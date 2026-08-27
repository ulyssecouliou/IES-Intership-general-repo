"""Tests for the company-letterhead SIA compliance report PDF."""

import struct
import unittest
import zlib
from pathlib import Path
from types import SimpleNamespace

from pypdf import PdfReader

from scripts.quality.fixtures import StaticModelAnalyzer, build_reference_room
from swiss_sia.company_profile import CompanyProfile, load_company_profile
from swiss_sia.config import SIA_COMPLIANCE_REQUIREMENT_MATRIX
from swiss_sia.compliance_report_pdf import (
    _criterion_for_alert,
    render_compliance_report_pdf,
    scoped_verdict_status,
    summarise_model,
)
from swiss_sia.compliance_verdict import (
    COMPLIANT,
    NOT_COMPLIANT,
    NOT_DETERMINED,
    build_compliance_verdict,
)
from swiss_sia.model_analyzer import OpeningData, RoomData, SurfaceData
from swiss_sia.pdf_writer import PdfDocument, _escape, wrap_to_width
from swiss_sia.reference_model.sia4010.ui_translations import LANGUAGES, translate
from swiss_sia.rule_engine import Alert, RuleEngine, Severity
from swiss_sia.sia380_checker import SIA3802Checker
from swiss_sia.sia4010_checker import SIA4010Checker

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = REPO_ROOT / ".codex_tmp" / "compliance_pdf_tests"


class PdfEncodingTests(unittest.TestCase):
    """Protect readable normative symbols in the WinAnsi-only PDF writer."""

    def test_greek_thermal_bridge_symbols_are_transliterated(self):
        self.assertEqual(
            _escape("Ponts thermiques (ψ/χ)"), b"Ponts thermiques \\(psi/chi\\)"
        )


def _write_test_png(path: Path, width: int = 12, height: int = 8) -> Path:
    """Write a small 8-bit RGB PNG without needing an imaging library.

    A synthetic gradient keeps the fixture free of any licensed material while
    still exercising the per-scanline PNG predictor that the writer relies on.
    """

    raw = bytearray()
    for row in range(height):
        raw.append(0)  # filter type 0 (None) for this scanline
        for column in range(width):
            raw += bytes((column * 20 % 256, row * 30 % 256, 128))

    def chunk(tag: bytes, body: bytes) -> bytes:
        """Return one length-prefixed, CRC-checked PNG chunk."""
        return (
            struct.pack(">I", len(body))
            + tag
            + body
            + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(bytes(raw)))
        + chunk(b"IEND", b"")
    )
    return path


class LogoEmbeddingTests(unittest.TestCase):
    """The company logo must embed and decode back to real pixels."""

    def test_contained_logo_keeps_its_original_aspect_ratio(self):
        wide = _write_test_png(OUTPUT_ROOT / "wide_logo.png", width=24, height=8)
        portrait = _write_test_png(OUTPUT_ROOT / "portrait_logo.png", width=8, height=24)
        document = PdfDocument(title="logo ratios")
        page = document.add_page()

        wide_box = page.image_contain(10.0, 10.0, 18.0, 18.0, wide)
        portrait_box = page.image_contain(40.0, 10.0, 18.0, 18.0, portrait)

        self.assertAlmostEqual(wide_box[2] / wide_box[3], 3.0)
        self.assertAlmostEqual(portrait_box[2] / portrait_box[3], 1.0 / 3.0)
        self.assertAlmostEqual(wide_box[0], 10.0)
        self.assertAlmostEqual(wide_box[1], 16.0)
        self.assertAlmostEqual(portrait_box[0], 46.0)
        self.assertAlmostEqual(portrait_box[1], 10.0)

    def test_png_logo_round_trips_through_the_pdf(self):
        from swiss_sia.pdf_writer import load_image

        logo = _write_test_png(OUTPUT_ROOT / "logo.png")
        parsed = load_image(logo)
        self.assertEqual((parsed["width"], parsed["height"]), (12, 8))
        self.assertEqual(parsed["colour_space"], "/DeviceRGB")

        path = OUTPUT_ROOT / "logo_embedded.pdf"
        document = PdfDocument(title="logo")
        page = document.add_page()
        page.image(16, 6, 17, 17, logo)
        document.save(path)

        image = PdfReader(str(path)).pages[0]["/Resources"]["/XObject"]["/Im1"]
        obj = image.get_object()
        self.assertEqual(int(obj["/Width"]), 12)
        # get_data() applies FlateDecode and the PNG predictor: a correct
        # DecodeParms yields exactly width * height * 3 bytes.
        self.assertEqual(len(obj.get_data()), 12 * 8 * 3)

    def test_palette_png_is_refused_rather_than_silently_flattened(self):
        from swiss_sia.pdf_writer import ImageError, load_image

        path = OUTPUT_ROOT / "palette.png"

        def chunk(tag, body):
            """Return one CRC-checked PNG chunk."""
            return (
                struct.pack(">I", len(body))
                + tag
                + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
            )

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 3, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\x00\x00"))
            + chunk(b"IEND", b"")
        )
        with self.assertRaises(ImageError):
            load_image(path)

    def test_unusable_logo_never_blocks_the_report(self):
        broken = OUTPUT_ROOT / "broken_logo.png"
        broken.parent.mkdir(parents=True, exist_ok=True)
        broken.write_bytes(b"not a real png")
        profile = CompanyProfile(name="Office", logo_path=broken)
        rooms = [build_reference_room()]
        path = render_compliance_report_pdf(
            OUTPUT_ROOT / "report_broken_logo.pdf",
            project_label="P",
            rooms_data=rooms,
            sia3802_results={},
            sia4010_results={},
            profile=profile,
            language="en",
        )
        self.assertIn("Office", PdfReader(str(path)).pages[0].extract_text())


class _Alert:
    """Minimal alert double carrying only what the verdict engine reads."""

    def __init__(self, category, severity, rule=""):
        """Record the alert category and severity name."""
        self.category = category
        self.severity = type("Severity", (), {"name": severity})()
        self.rule = rule


class PdfWriterTests(unittest.TestCase):
    """The dependency-free writer must produce a readable, valid PDF."""

    def test_pages_and_accented_text_survive_a_round_trip(self):
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        path = OUTPUT_ROOT / "writer.pdf"
        document = PdfDocument(title="T")
        first = document.add_page()
        first.text(15, 20, "Zürich Genève Lugano éàçöäÉÀ", size_pt=11)
        second = document.add_page()
        second.text(15, 20, "Second page", size_pt=11, bold=True)
        document.save(path)
        reader = PdfReader(str(path))
        self.assertEqual(len(reader.pages), 2)
        self.assertIn("Zürich Genève Lugano", reader.pages[0].extract_text())
        self.assertIn("Second page", reader.pages[1].extract_text())

    def test_wrap_never_drops_words(self):
        sentence = "A limitation clause must stay readable in full at all times."
        lines = wrap_to_width(sentence, 8.0, 40.0)
        self.assertGreater(len(lines), 1)
        self.assertEqual(" ".join(lines).split(), sentence.split())


class VerdictEngineTests(unittest.TestCase):
    """The verdict must never read as compliant on missing evidence."""

    def _sia3802(self, alerts=(), comparison_status=""):
        """Build a minimal checker-shaped result for the verdict engine."""
        return {
            "envelope": {},
            "openings": {},
            "ventilation": {},
            "gains": {},
            "setpoints": {},
            "hvac": {},
            "alerts": list(alerts),
            "global_reference_comparison": {"status": comparison_status},
        }

    def test_no_room_is_not_determined(self):
        verdict = build_compliance_verdict(self._sia3802(), {}, rooms_analysed=0)
        self.assertEqual(verdict.sia3802_status, NOT_DETERMINED)
        self.assertEqual(verdict.overall_status, NOT_DETERMINED)

    def test_alert_never_borrows_a_limit_from_an_unrelated_domain(self):
        alert = Alert(
            rule="SIA3802_LIGHTING_CONTROL_TYPE_MISSING",
            description="Lighting control evidence is missing.",
            severity=Severity.MEDIUM,
            category="Gains",
            recommendation="Provide the lighting-control evidence.",
        )
        self.assertEqual(_criterion_for_alert(alert), {})

    def test_missing_global_comparison_blocks_a_compliant_statement(self):
        verdict = build_compliance_verdict(self._sia3802(), {}, rooms_analysed=3)
        self.assertEqual(verdict.sia3802_status, NOT_DETERMINED)
        self.assertEqual(verdict.sia3802_reason, "global_comparison_missing")
        self.assertIn("global_reference_comparison", verdict.outstanding)

    def test_blocking_finding_makes_the_domain_and_overall_not_compliant(self):
        verdict = build_compliance_verdict(
            self._sia3802(
                alerts=[_Alert("Envelope", "CRITICAL")],
                comparison_status="REVIEWED_RESULT_AVAILABLE",
            ),
            {},
            rooms_analysed=3,
        )
        envelope = next(d for d in verdict.domains if d.domain == "envelope")
        self.assertEqual(envelope.status, NOT_COMPLIANT)
        self.assertEqual(verdict.sia3802_status, NOT_COMPLIANT)
        self.assertEqual(verdict.overall_status, NOT_COMPLIANT)

    def test_advisory_findings_do_not_block_a_domain(self):
        verdict = build_compliance_verdict(
            self._sia3802(
                alerts=[_Alert("Gains", "LOW"), _Alert("Gains", "MEDIUM")],
                comparison_status="REVIEWED_RESULT_AVAILABLE",
            ),
            {},
            rooms_analysed=3,
        )
        gains = next(d for d in verdict.domains if d.domain == "gains")
        self.assertEqual(gains.status, COMPLIANT)
        self.assertEqual(gains.advisory_count, 2)

    def test_missing_component_evidence_is_a_reserve_not_a_downgrade(self):
        """A domain with missing evidence is a per-domain NOT_DETERMINED, but once
        the decisive §7.2.5.2 comparison is reviewed and no determined failure
        exists the overall statement is COMPLIANT with the reserve surfaced in
        `outstanding` (product decision 2026-08-19, pending norm-analyst)."""

        verdict = build_compliance_verdict(
            self._sia3802(
                alerts=[
                    _Alert(
                        "Gains",
                        "MEDIUM",
                        rule="SIA3802_LIGHTING_POWER_MISSING",
                    )
                ],
                comparison_status="REVIEWED_RESULT_AVAILABLE",
            ),
            {},
            rooms_analysed=3,
        )
        gains = next(d for d in verdict.domains if d.domain == "gains")
        self.assertEqual(gains.status, NOT_DETERMINED)
        self.assertEqual(gains.missing_count, 1)
        self.assertEqual(verdict.missing_total, 1)
        self.assertEqual(verdict.sia3802_status, COMPLIANT)
        self.assertEqual(
            verdict.sia3802_reason, "comparison_reviewed_no_blocker_with_reserves"
        )
        self.assertIn("sia3802_domain_evidence", verdict.outstanding)

    def test_missing_essential_ventilation_evidence_downgrades_to_not_determined(self):
        verdict = build_compliance_verdict(
            self._sia3802(
                alerts=[
                    _Alert(
                        "Ventilation",
                        "MEDIUM",
                        rule="SIA3802_VENTILATION_RATE_MISSING",
                    )
                ],
                comparison_status="REVIEWED_RESULT_AVAILABLE",
            ),
            {},
            rooms_analysed=3,
        )

        self.assertEqual(verdict.sia3802_status, NOT_DETERMINED)
        self.assertEqual(verdict.sia3802_reason, "ventilation_evidence_incomplete")
        self.assertIn("sia3802_ventilation_evidence", verdict.outstanding)

    def test_determined_failure_still_fails_closed_despite_reviewed_comparison(self):
        """A determined (non-indeterminate) blocking finding must still make the
        overall NOT_COMPLIANT even with the decisive comparison reviewed."""

        verdict = build_compliance_verdict(
            self._sia3802(
                alerts=[_Alert("Openings", "CRITICAL", rule="SIA3802_U_VALUE_WINDOW")],
                comparison_status="REVIEWED_RESULT_AVAILABLE",
            ),
            {},
            rooms_analysed=3,
        )
        self.assertEqual(verdict.sia3802_status, NOT_COMPLIANT)

    def test_sia3802_compliant_only_with_reviewed_comparison_and_no_blocker(self):
        verdict = build_compliance_verdict(
            self._sia3802(comparison_status="REVIEWED_RESULT_AVAILABLE"),
            {},
            rooms_analysed=3,
        )
        self.assertEqual(verdict.sia3802_status, COMPLIANT)

    def test_contradicting_comparison_is_not_compliant_despite_acceptance(self):
        """A reviewed comparison whose figures contradict the reviewer's
        acceptance (project value above the reference) must yield NOT_COMPLIANT,
        never a compliant statement, even with no other blocker."""
        verdict = build_compliance_verdict(
            self._sia3802(comparison_status="REVIEWED_RESULT_CONTRADICTS_ACCEPTANCE"),
            {},
            rooms_analysed=3,
        )
        self.assertEqual(verdict.sia3802_status, NOT_COMPLIANT)
        self.assertEqual(
            verdict.sia3802_reason, "global_comparison_contradicts_acceptance"
        )
        self.assertEqual(verdict.overall_status, NOT_COMPLIANT)

    def test_sia4010_never_reports_compliant_without_attestation(self):
        # Even with every official test recorded, the strongest SIA 4010 status
        # this report may carry is NOT_DETERMINED: attestation is external.
        verdict = build_compliance_verdict(
            self._sia3802(comparison_status="REVIEWED_RESULT_AVAILABLE"),
            {
                "tests": {"test_1": {"status": "OFFICIAL_RESULTS_RECORDED"}},
                "validation_class": "1A",
                "class_readiness": {"1A": {}},
            },
            rooms_analysed=3,
        )
        self.assertEqual(verdict.sia4010_status, NOT_DETERMINED)
        self.assertEqual(verdict.sia4010_reason, "attestation_required")
        self.assertEqual(verdict.overall_status, NOT_DETERMINED)

    def test_failed_official_test_is_not_compliant(self):
        verdict = build_compliance_verdict(
            self._sia3802(comparison_status="REVIEWED_RESULT_AVAILABLE"),
            {"tests": {"test_1": {"status": "FAILED"}}, "validation_class": "1A"},
            rooms_analysed=3,
        )
        self.assertEqual(verdict.sia4010_status, NOT_COMPLIANT)


class ModelSummaryTests(unittest.TestCase):
    """The schematic must chart only orientations it can actually resolve."""

    def test_areas_are_grouped_by_compass_sector(self):
        room = RoomData(
            id="r",
            name="R",
            area=50.0,
            volume=150.0,
            surfaces=[
                SurfaceData(
                    id="s",
                    name="S",
                    area=10.0,
                    net_area=10.0,
                    is_external=True,
                    orientation=180.0,
                ),
                SurfaceData(
                    id="n",
                    name="N",
                    area=6.0,
                    net_area=6.0,
                    is_external=True,
                    orientation=0.0,
                ),
            ],
            openings=[
                OpeningData(
                    id="w", name="W", area=2.0, is_external=True, orientation=180.0
                )
            ],
        )
        summary = summarise_model([room])
        self.assertEqual(summary["opaque_by_sector"]["S"], 10.0)
        self.assertEqual(summary["opaque_by_sector"]["N"], 6.0)
        self.assertEqual(summary["glazed_by_sector"]["S"], 2.0)
        self.assertAlmostEqual(summary["window_wall_ratio"], 2.0 / 16.0)

    def test_unresolvable_orientation_is_not_charted_in_a_wrong_sector(self):
        room = RoomData(
            id="r",
            name="R",
            surfaces=[
                SurfaceData(
                    id="s",
                    name="S",
                    area=9.0,
                    net_area=9.0,
                    is_external=True,
                    orientation="unknown",
                )
            ],
        )
        summary = summarise_model([room])
        self.assertEqual(sum(summary["opaque_by_sector"].values()), 0.0)
        self.assertEqual(summary["unplaced_opaque_m2"], 9.0)
        self.assertEqual(summary["total_opaque_m2"], 9.0)

    def test_empty_model_is_safe(self):
        summary = summarise_model([])
        self.assertEqual(summary["rooms"], 0)
        self.assertIsNone(summary["window_wall_ratio"])


class CompanyProfileTests(unittest.TestCase):
    """A missing or malformed profile must never break the report."""

    def test_absent_config_yields_an_unconfigured_profile(self):
        profile = load_company_profile(OUTPUT_ROOT / "does-not-exist")
        self.assertFalse(profile.is_configured)
        self.assertIsNone(profile.logo_path)

    def test_malformed_config_is_tolerated(self):
        root = OUTPUT_ROOT / "bad"
        (root / "config").mkdir(parents=True, exist_ok=True)
        (root / "config" / "company_profile.json").write_text(
            "{ not json", encoding="utf-8"
        )
        self.assertFalse(load_company_profile(root).is_configured)

    def test_missing_logo_file_is_ignored(self):
        root = OUTPUT_ROOT / "nologo"
        (root / "config").mkdir(parents=True, exist_ok=True)
        (root / "config" / "company_profile.json").write_text(
            '{"name": "Office", "logo_path": "assets/absent.png"}', encoding="utf-8"
        )
        profile = load_company_profile(root)
        self.assertTrue(profile.is_configured)
        self.assertIsNone(profile.logo_path)

    def test_placeholder_logo_is_ignored_when_office_name_is_empty(self):
        root = OUTPUT_ROOT / "placeholder_only"
        (root / "config").mkdir(parents=True, exist_ok=True)
        _write_test_png(root / "placeholder.png")
        (root / "config" / "company_profile.json").write_text(
            '{"name": "", "logo_path": "placeholder.png"}',
            encoding="utf-8",
        )
        profile = load_company_profile(root)
        self.assertFalse(profile.is_configured)
        self.assertIsNone(profile.logo_path)

    def test_repository_profile_identifies_ies_as_report_issuer(self):
        profile = load_company_profile(REPO_ROOT)
        self.assertEqual(profile.name, "IES")
        self.assertEqual(profile.logo_path, REPO_ROOT / "assets" / "ies_logo.png")
        self.assertTrue(profile.logo_path.is_file())


class RenderedReportTests(unittest.TestCase):
    """Render the real report and pin its compliance-critical wording."""

    @classmethod
    def setUpClass(cls):
        """Run the checkers on the deterministic fixture room once."""
        rooms = [build_reference_room()]
        analyzer = StaticModelAnalyzer(rooms)
        dynamic = {
            "status": "NOT_CHECKABLE",
            "building_status": "NEW_BUILDING",
            "rooms": [],
            "design_power_status": "NOT_CHECKABLE",
        }
        cls.rooms = rooms
        cls.sia3802 = SIA3802Checker(analyzer, RuleEngine()).check_all(
            rooms_data=rooms, dynamic_results=dynamic
        )
        cls.sia4010 = SIA4010Checker(analyzer, RuleEngine()).check_all(rooms_data=rooms)
        cls.profile = CompanyProfile(
            name="Bureau Technique Alpin SA",
            tagline="Ingénieurs conseils",
            address_lines=("Rue du Simplon 12", "1950 Sion"),
            contact_lines=("+41 27 000 00 00",),
            author_name="A. Rossi",
            author_role="Ingénieur SIA",
            report_reference="BTA-2026-0142",
        )
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    def _render(self, language):
        """Render the report in one language and return its extracted text."""
        path = render_compliance_report_pdf(
            OUTPUT_ROOT / "report_{}.pdf".format(language),
            project_label="ZOER_32_C1",
            rooms_data=self.rooms,
            sia3802_results=self.sia3802,
            sia4010_results=self.sia4010,
            profile=self.profile,
            language=language,
            model_name="ZOER_32_C1.mit",
        )
        return PdfReader(str(path)).pages[1].extract_text()

    def test_cover_matches_the_sibling_ies_report_hierarchy(self):
        path = render_compliance_report_pdf(
            OUTPUT_ROOT / "report_cover.pdf",
            project_label="ZOER_32_C1",
            rooms_data=self.rooms,
            sia3802_results=self.sia3802,
            sia4010_results=self.sia4010,
            profile=self.profile,
            language="en",
            model_name="ZOER_32_C1.mit",
        )
        cover = PdfReader(str(path)).pages[0].extract_text()
        self.assertIn("ENGINEERING ASSESSMENT REPORT", cover)
        self.assertIn("SIA 380/2 compliance assessment", cover)
        self.assertIn("ZOER_32_C1", cover)
        self.assertNotIn("CERTIFICATION REPORT", cover)

    def test_company_identity_reaches_the_letterhead(self):
        text = self._render("fr")
        self.assertIn("Bureau Technique Alpin SA", text)
        self.assertIn("1950 Sion", text)
        self.assertIn("BTA-2026-0142", text)
        self.assertIn("A. Rossi", text)

    def test_project_and_model_are_identified(self):
        text = self._render("en")
        self.assertIn("ZOER_32_C1", text)
        self.assertIn("ZOER_32_C1.mit", text)
        self.assertIn("SIA 380/2:2022 + SIA 4010:2023", text)

    def test_model_schematic_and_key_figures_are_present(self):
        text = self._render("en")
        for sector in ("N", "NE", "E", "SE", "S", "SW", "W", "NW"):
            self.assertIn(sector, text)
        self.assertIn(translate("figure_wwr", "en"), text)
        self.assertIn(translate("legend_glazed", "en"), text)

    def test_every_language_renders_its_own_wording(self):
        for code in LANGUAGES:
            with self.subTest(language=code):
                text = self._render(code)
                self.assertIn(translate("report_title", code), text)
                self.assertIn(translate("section_signature", code).upper(), text)

    def test_report_never_claims_to_be_a_certificate(self):
        for code in LANGUAGES:
            with self.subTest(language=code):
                text = self._render(code)
                # The scope statements must appear in full, not truncated.
                for key in ("scope_line_1", "scope_line_2"):
                    statement = translate(key, code)
                    tail = statement.split()[-1].strip(".")
                    self.assertIn(tail, text)
                self.assertIn(translate("scope_line_1", code)[:40], text)

    def test_header_and_footer_follow_the_ies_compliance_report_pattern(self):
        text = self._render("en")
        self.assertIn("SIA Compliance Report", text)
        self.assertIn("ZOER_32_C1", text)
        self.assertIn("IES  ·  www.iesve.com", text)
        self.assertRegex(text, r"\d{2}/\d{2}/\d{4}\s+2$")

    def test_undetermined_verdict_is_reported_not_hidden(self):
        # The fixture supplies no reviewed global comparison, so the headline
        # verdict must be NOT DETERMINED rather than compliant.
        text = self._render("en")
        self.assertIn(translate("verdict_not_determined", "en"), text)
        self.assertNotIn(translate("verdict_compliant", "en") + "\n" + "SIA", text)

    def test_detailed_pages_explain_the_decision_and_each_action(self):
        path = render_compliance_report_pdf(
            OUTPUT_ROOT / "report_detailed_findings.pdf",
            project_label="ZOER_32_C1",
            rooms_data=self.rooms,
            sia3802_results=self.sia3802,
            sia4010_results={},
            profile=self.profile,
            language="fr",
            scope="sia3802",
        )
        reader = PdfReader(str(path))
        full_text = "\n".join(page.extract_text() for page in reader.pages)
        self.assertGreaterEqual(len(reader.pages), 3)
        self.assertIn(translate("report_details_title", "fr"), full_text)
        self.assertIn(translate("report_decision_basis", "fr").upper(), full_text)
        self.assertIn(translate("report_finding_action", "fr"), full_text)
        self.assertIn(
            translate("report_reason_global_comparison_missing", "fr"),
            full_text,
        )

    def test_long_annex_moves_methodology_clear_of_the_footer(self):
        path = render_compliance_report_pdf(
            OUTPUT_ROOT / "report_long_annex.pdf",
            project_label="ZOER_32_C1",
            rooms_data=self.rooms,
            sia3802_results=self.sia3802,
            sia4010_results=self.sia4010,
            profile=self.profile,
            language="en",
            scope="both",
        )
        page_text = [page.extract_text() for page in PdfReader(str(path)).pages]
        reserves_page = next(
            index
            for index, text in enumerate(page_text)
            if translate("annex_reserves_title", "en").upper() in text
        )
        methodology_page = next(
            index
            for index, text in enumerate(page_text)
            if translate("annex_method_title", "en").upper() in text
        )
        self.assertGreater(methodology_page, reserves_page)
        self.assertIn(translate("annex_title", "en"), page_text[methodology_page])

    def test_configured_limit_and_model_value_are_printed_for_a_blocker(self):
        wall_entry = next(
            item
            for item in SIA_COMPLIANCE_REQUIREMENT_MATRIX
            if item.get("implemented_rule") == "SIA3802_U_VALUE_EXTERNAL_WALL"
        )
        sia3802 = {
            "envelope": {},
            "openings": {},
            "ventilation": {},
            "gains": {},
            "setpoints": {},
            "hvac": {},
            "global_reference_comparison": {"status": "REVIEWED_RESULT_AVAILABLE"},
            "alerts": [
                Alert(
                    rule="SIA3802_U_VALUE_EXTERNAL_WALL",
                    description="External wall U-value exceeds the configured reference input.",
                    severity=Severity.CRITICAL,
                    category="Envelope",
                    recommendation="Review the wall construction and rerun the assessment.",
                    data=SimpleNamespace(name="Wall A", u_value=0.41),
                )
            ],
        }
        path = render_compliance_report_pdf(
            OUTPUT_ROOT / "report_detailed_limit.pdf",
            project_label="P",
            rooms_data=self.rooms,
            sia3802_results=sia3802,
            sia4010_results={},
            profile=self.profile,
            language="en",
            scope="sia3802",
        )
        full_text = "\n".join(page.extract_text() for page in PdfReader(str(path)).pages)
        self.assertIn(str(wall_entry["limit"]), full_text)
        self.assertIn("u value: 0.41", full_text)
        self.assertIn("Review the wall construction", full_text)

    def test_repetitive_findings_are_grouped_with_all_object_ids(self):
        alerts = [
            Alert(
                rule="SIA3802_VISIBLE_TRANSMITTANCE",
                description="Glazing visible transmittance requires review.",
                severity=Severity.LOW,
                category="Openings",
                recommendation="Retain the value in the global comparison.",
                data=SimpleNamespace(
                    name="Window-{}".format(index),
                    visible_transmittance=0.65,
                ),
            )
            for index in range(1, 9)
        ]
        sia3802 = {
            "envelope": {},
            "openings": {},
            "ventilation": {},
            "gains": {},
            "setpoints": {},
            "hvac": {},
            "alerts": alerts,
            "global_reference_comparison": {"status": "NOT_CHECKABLE"},
        }
        path = render_compliance_report_pdf(
            OUTPUT_ROOT / "report_grouped_findings.pdf",
            project_label="P",
            rooms_data=self.rooms,
            sia3802_results=sia3802,
            sia4010_results={},
            profile=self.profile,
            language="en",
            scope="sia3802",
        )
        full_text = "\n".join(page.extract_text() for page in PdfReader(str(path)).pages)
        self.assertIn("8 occurrences share this rule", full_text)
        for index in range(1, 9):
            self.assertIn("Window-{}".format(index), full_text)
        self.assertEqual(full_text.count("SIA3802_VISIBLE_TRANSMITTANCE"), 1)

    def test_summer_comfort_blocker_prints_failure_values_and_source(self):
        """The client card must explain the exceedance instead of describing a pass."""
        alert = Alert(
            rule="SIA3802_SUMMER_COMFORT_DYNAMIC",
            description=(
                "Annual occupied-hour temperatures exceed the applicable SIA 180 "
                "upper-hour allowance or undercut the lower limit curve."
            ),
            severity=Severity.HIGH,
            category="Dynamic Method",
            recommendation="Review the critical room and rerun the simulation.",
            data={
                "room_name": "Office_01",
                "upper_hours": 1445.5,
                "upper_limit_hours": 0.0,
                "lower_hours": 0.0,
                "window_operable": None,
                "method": "CONSERVATIVE_ZERO_HOUR_SCREENING_OPERABILITY_UNKNOWN",
            },
        )
        criterion = _criterion_for_alert(alert)
        self.assertEqual(criterion["id"], "SIA3802_SUMMER_COMFORT")

        sia3802 = {
            "envelope": {},
            "openings": {},
            "ventilation": {},
            "gains": {},
            "setpoints": {},
            "hvac": {},
            "dynamic": {"status": "CHECKED"},
            "global_reference_comparison": {"status": "REVIEWED_RESULT_AVAILABLE"},
            "alerts": [alert],
        }
        path = render_compliance_report_pdf(
            OUTPUT_ROOT / "report_summer_comfort_evidence.pdf",
            project_label="P",
            rooms_data=self.rooms,
            sia3802_results=sia3802,
            sia4010_results={},
            profile=self.profile,
            language="en",
            scope="sia3802",
        )
        full_text = "\n".join(page.extract_text() for page in PdfReader(str(path)).pages)
        self.assertIn("temperatures exceed", full_text)
        self.assertNotIn("temperatures satisfy", full_text)
        self.assertIn("upper hours: 1445.5", full_text)
        self.assertIn("upper limit hours: 0.0", full_text)
        self.assertIn(str(criterion["source"]), full_text)

    def test_sia3802_scope_omits_sia4010_readiness_from_client_banner(self):
        sia3802 = {
            "envelope": {},
            "openings": {},
            "ventilation": {},
            "gains": {},
            "setpoints": {},
            "hvac": {},
            "alerts": [],
            "global_reference_comparison": {"status": "REVIEWED_RESULT_AVAILABLE"},
        }
        sia4010 = {
            "tests": {"test_1": {"status": "OFFICIAL_RESULTS_RECORDED"}},
            "validation_class": "1A",
            "class_readiness": {"1A": {}},
        }
        verdict = build_compliance_verdict(sia3802, sia4010, len(self.rooms))
        self.assertEqual(verdict.sia3802_status, COMPLIANT)
        self.assertEqual(verdict.sia4010_status, NOT_DETERMINED)
        self.assertEqual(verdict.overall_status, NOT_DETERMINED)
        self.assertEqual(scoped_verdict_status(verdict, "sia3802"), COMPLIANT)

        path = render_compliance_report_pdf(
            OUTPUT_ROOT / "report_sia3802_scope.pdf",
            project_label="ZOER_32_C1",
            rooms_data=self.rooms,
            sia3802_results=sia3802,
            sia4010_results=sia4010,
            profile=self.profile,
            language="fr",
            model_name="ZOER_32_C1.mit",
            scope="sia3802",
        )
        text = PdfReader(str(path)).pages[1].extract_text()
        heading = text.index(translate("verdict_heading", "fr").upper())
        compliant = text.index(translate("verdict_compliant", "fr"), heading)
        undetermined = text.find(translate("verdict_not_determined", "fr"), heading)
        self.assertTrue(undetermined < 0 or compliant < undetermined)
        self.assertNotIn(translate("sia4010_readiness_attestation_required", "fr"), text)

    def test_unknown_report_scope_is_rejected(self):
        with self.assertRaises(ValueError):
            render_compliance_report_pdf(
                OUTPUT_ROOT / "report_invalid_scope.pdf",
                project_label="P",
                rooms_data=self.rooms,
                sia3802_results=self.sia3802,
                sia4010_results=self.sia4010,
                profile=self.profile,
                scope="automatic",
            )

    def test_report_renders_without_any_company_profile(self):
        for code in LANGUAGES:
            with self.subTest(language=code):
                path = render_compliance_report_pdf(
                    OUTPUT_ROOT / "report_noprofile_{}.pdf".format(code),
                    project_label="P",
                    rooms_data=self.rooms,
                    sia3802_results=self.sia3802,
                    sia4010_results=self.sia4010,
                    profile=CompanyProfile(),
                    language=code,
                )
                text = PdfReader(str(path)).pages[1].extract_text()
                self.assertIn(translate("report_neutral_header", code), text)
                self.assertNotIn(translate("company_unspecified", code), text)

    def test_report_language_defaults_to_english(self):
        path = render_compliance_report_pdf(
            OUTPUT_ROOT / "report_default_language.pdf",
            project_label="P",
            rooms_data=self.rooms,
            sia3802_results=self.sia3802,
            sia4010_results=self.sia4010,
            profile=CompanyProfile(),
        )
        text = PdfReader(str(path)).pages[1].extract_text()
        self.assertIn(translate("report_title", "en"), text)
        self.assertIn(translate("report_neutral_header", "en"), text)


if __name__ == "__main__":
    unittest.main()
