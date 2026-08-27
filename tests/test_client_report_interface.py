"""Tests for the project-local client report interface contract."""

from __future__ import annotations

import struct
import re
import unittest
import zlib
from pathlib import Path

from pypdf import PdfReader

from swiss_sia.client_compliance_ui import (
    ClientComplianceWindow,
    LANGUAGE_CODES,
    LANGUAGE_LABELS,
    compliance_palette,
    initial_client_language,
    validate_client_context,
)
from swiss_sia.client_report_context import (
    BUILDING_STRATEGY_TEXT,
    ClientReportContext,
    building_strategy_summary,
    load_client_report_context,
    report_directory,
    save_client_report_context,
)
from swiss_sia.reference_model.sia4010.ui_translations import TRANSLATIONS
from swiss_sia.company_profile import CompanyProfile
from swiss_sia.compliance_report_pdf import render_compliance_report_pdf

ROOT = Path(__file__).resolve().parents[1]
TMP_ROOT = ROOT / ".codex_tmp" / "client_report_interface_tests"


def _write_rgb_png(path: Path, width: int = 10, height: int = 6) -> Path:
    """Write a tiny RGB PNG accepted by the dependency-free PDF writer."""

    raw = bytearray()
    for row in range(height):
        raw.append(0)
        for column in range(width):
            raw += bytes((column * 20 % 256, row * 30 % 256, 120))

    def chunk(tag: bytes, body: bytes) -> bytes:
        return (
            struct.pack(">I", len(body))
            + tag
            + body
            + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw)))
        + chunk(b"IEND", b"")
    )
    return path


class ClientContextTests(unittest.TestCase):
    def test_every_static_client_ui_key_has_four_reviewed_translations(self) -> None:
        source = (ROOT / "swiss_sia" / "client_compliance_ui.py").read_text(
            encoding="utf-8"
        )
        keys = {
            key
            for key in re.findall(r'self\.t\("([^"]+)"', source)
            if not key.endswith("_")
        }
        missing = keys - set(TRANSLATIONS) - set(BUILDING_STRATEGY_TEXT)
        self.assertEqual(missing, set())
        for key in keys & set(TRANSLATIONS):
            with self.subTest(key=key):
                self.assertEqual(set(TRANSLATIONS[key]), {"en", "de", "fr", "it"})

    def test_language_selector_exposes_exactly_four_languages(self) -> None:
        self.assertEqual(set(LANGUAGE_LABELS), {"en", "de", "fr", "it"})
        self.assertEqual(
            {LANGUAGE_CODES[label] for label in LANGUAGE_LABELS.values()},
            {"en", "de", "fr", "it"},
        )

    def test_english_is_the_default_for_new_and_legacy_contexts(self) -> None:
        self.assertEqual(ClientReportContext().language, "en")
        self.assertEqual(initial_client_language(ClientReportContext()), "en")
        # Contexts saved before explicit language selection used French as an
        # implicit default. They migrate to the new English default.
        self.assertEqual(
            initial_client_language(ClientReportContext(language="fr")),
            "en",
        )

    def test_an_explicit_language_choice_is_restored(self) -> None:
        self.assertEqual(
            initial_client_language(
                ClientReportContext(language="it", language_selected=True)
            ),
            "it",
        )

    def test_missing_translation_key_is_humanised_for_the_business_ui(self) -> None:
        window = ClientComplianceWindow.__new__(ClientComplianceWindow)
        window.language = "fr"
        self.assertEqual(
            window.t("client_ui_strategy_windows"),
            "Fenêtres prévues ouvrables",
        )
        self.assertEqual(
            window.t("client_ui_example_business_label"),
            "Example business label",
        )

    def test_required_fields_are_explicit(self) -> None:
        self.assertEqual(
            validate_client_context(ClientReportContext()),
            "client_and_project_required",
        )
        self.assertIsNone(
            validate_client_context(
                ClientReportContext(client_name="Client", project_name="Project")
            )
        )

    def test_context_reads_the_text_visible_in_focused_entries(self) -> None:
        """IESVE-hosted Tk entries are synchronised before form validation."""

        class Value:
            def __init__(self, value: str = "") -> None:
                self.value = value

            def get(self) -> str:
                return self.value

            def set(self, value: str) -> None:
                self.value = value

        class Entry:
            def __init__(self, value: str) -> None:
                self.value = value

            def get(self) -> str:
                return self.value

        window = ClientComplianceWindow.__new__(ClientComplianceWindow)
        window.vars = {
            key: Value(default)
            for key, default in {
                "client_name": "",
                "project_name": "",
                "project_address": "",
                "client_contact": "",
                "report_reference": "",
                "prepared_by": "",
                "language": "en",
                "weather_file": "weather.fwt",
                "solar_shading": "TO_CONFIRM",
                "window_operability": "TO_CONFIRM",
                "mechanical_cooling": "TO_CONFIRM",
                "building_strategy_notes": "",
                "client_logo_path": "",
                "model_viewer_image_path": "",
            }.items()
        }
        window.field_entries = {
            "client_name": Entry("Client visible in the form"),
            "project_name": Entry("Project visible in the form"),
        }

        context = window._context()

        self.assertEqual(context.client_name, "Client visible in the form")
        self.assertEqual(context.project_name, "Project visible in the form")
        self.assertIsNone(validate_client_context(context))

    def test_unusable_report_image_is_rejected_before_generation(self) -> None:
        self.assertEqual(
            validate_client_context(
                ClientReportContext(
                    client_name="Client",
                    project_name="Project",
                    client_logo_path=str(TMP_ROOT / "missing-logo.png"),
                )
            ),
            "client_ui_image_error",
        )

    def test_context_and_selected_images_are_saved_inside_the_project(self) -> None:
        root = TMP_ROOT / "context_case"
        project = root / "VE Project"
        project.mkdir(parents=True, exist_ok=True)
        source_logo = _write_rgb_png(root / "logo.png")
        source_view = _write_rgb_png(root / "viewer.png", 20, 12)
        stored = save_client_report_context(
            project,
            ClientReportContext(
                client_name="Client",
                project_name="Project",
                weather_file="weather.fwt",
                solar_shading="YES",
                window_operability="NO",
                mechanical_cooling="YES",
                building_strategy_notes="External blinds; cooling at 26 C.",
                client_logo_path=str(source_logo),
                model_viewer_image_path=str(source_view),
            ),
        )
        loaded = load_client_report_context(project)
        self.assertEqual(loaded.client_name, "Client")
        self.assertEqual(loaded.weather_file, "weather.fwt")
        self.assertEqual(loaded.solar_shading, "YES")
        self.assertEqual(loaded.window_operability, "NO")
        self.assertEqual(loaded.mechanical_cooling, "YES")
        self.assertEqual(
            loaded.building_strategy_notes,
            "External blinds; cooling at 26 C.",
        )
        self.assertEqual(loaded.language, "en")
        self.assertTrue(Path(stored.client_logo_path).is_file())
        self.assertTrue(Path(stored.model_viewer_image_path).is_file())
        self.assertTrue(Path(stored.client_logo_path).is_relative_to(project))
        self.assertEqual(report_directory(project), project / "SIA Compliance Reports")

    def test_invalid_strategy_declarations_fail_closed_per_project(self) -> None:
        context = ClientReportContext(
            solar_shading="unknown",
            window_operability="sometimes",
            mechanical_cooling="",
        ).normalized()

        self.assertEqual(context.solar_shading, "TO_CONFIRM")
        self.assertEqual(context.window_operability, "TO_CONFIRM")
        self.assertEqual(context.mechanical_cooling, "TO_CONFIRM")
        self.assertEqual(
            building_strategy_summary(context, "fr"),
            "Stores: TO_CONFIRM | Fenêtres: TO_CONFIRM | Froid: TO_CONFIRM",
        )

    def test_building_strategy_is_isolated_between_ve_projects(self) -> None:
        project_a = TMP_ROOT / "strategy_isolation" / "Model A"
        project_b = TMP_ROOT / "strategy_isolation" / "Model B"
        project_a.mkdir(parents=True, exist_ok=True)
        project_b.mkdir(parents=True, exist_ok=True)

        save_client_report_context(
            project_a,
            ClientReportContext(
                solar_shading="YES",
                window_operability="YES",
                mechanical_cooling="NO",
            ),
        )
        save_client_report_context(
            project_b,
            ClientReportContext(
                solar_shading="NO",
                window_operability="NO",
                mechanical_cooling="YES",
            ),
        )

        self.assertEqual(
            building_strategy_summary(load_client_report_context(project_a), "en"),
            "Shading: YES | Windows: YES | Cooling: NO",
        )
        self.assertEqual(
            building_strategy_summary(load_client_report_context(project_b), "en"),
            "Shading: NO | Windows: NO | Cooling: YES",
        )

    def test_palette_exposes_only_compliance_statuses(self) -> None:
        self.assertEqual(compliance_palette("COMPLIANT")[2], "verdict_compliant")
        self.assertEqual(compliance_palette("NOT_COMPLIANT")[2], "verdict_not_compliant")
        self.assertEqual(compliance_palette("anything")[2], "verdict_not_determined")

    def test_current_excel_and_pdf_are_opened_in_that_order(self) -> None:
        window = ClientComplianceWindow.__new__(ClientComplianceWindow)
        window.result = {
            "excel_path": "current-report.xlsx",
            "pdf_path": "current-report.pdf",
        }
        opened = []
        window._open_path = opened.append

        window._open_current_reports()

        self.assertEqual(
            opened,
            ["current-report.xlsx", "current-report.pdf"],
        )

    def test_automatic_model_viewer_capture_selects_the_created_image(self) -> None:
        class Value:
            def __init__(self) -> None:
                self.value = ""

            def set(self, value: str) -> None:
                self.value = value

        class Root:
            def __init__(self) -> None:
                self.foreground_requested = False

            def update_idletasks(self) -> None:
                pass

            def after_idle(self, _callback) -> None:
                self.foreground_requested = True

        window = ClientComplianceWindow.__new__(ClientComplianceWindow)
        window.project_path = Path("project")
        window.capture_model_viewer = lambda project: project / "captured.png"
        window.vars = {"model_viewer_image_path": Value()}
        window.status_text = Value()
        window.root = Root()
        window.t = lambda key: key

        window._capture_viewer()

        self.assertEqual(
            window.vars["model_viewer_image_path"].value,
            str(Path("project") / "captured.png"),
        )
        self.assertEqual(window.status_text.value, "client_ui_capture_done")
        self.assertTrue(window.root.foreground_requested)


class ClientPdfContextTests(unittest.TestCase):
    def test_pdf_contains_client_weather_shading_logo_and_viewer_image(self) -> None:
        root = TMP_ROOT / "pdf_case"
        root.mkdir(parents=True, exist_ok=True)
        logo = _write_rgb_png(root / "client.png")
        viewer = _write_rgb_png(root / "viewer.png", 20, 12)
        output = root / "client_report.pdf"
        context = ClientReportContext(
            client_name="Client Alpine SA",
            project_name="School North",
            project_address="1 Test Street, Lausanne",
            report_reference="SIA-26-014",
            prepared_by="U. Engineer",
            weather_file="CHE_GVE_2060_RCP85_DRY.fwt",
            solar_shading="YES",
            window_operability="NO",
            mechanical_cooling="YES",
            building_strategy_notes="External blinds and mechanical cooling.",
            client_logo_path=str(logo),
            model_viewer_image_path=str(viewer),
        )
        render_compliance_report_pdf(
            output,
            project_label="fallback",
            rooms_data=[],
            sia3802_results={},
            sia4010_results={},
            profile=CompanyProfile(name="IES"),
            language="en",
            scope="sia3802",
            report_context=context,
        )
        reader = PdfReader(str(output))
        text = reader.pages[1].extract_text()
        full_text = "\n".join(page.extract_text() for page in reader.pages)
        self.assertIn("Client Alpine SA", text)
        self.assertIn("School North", text)
        self.assertIn("CHE_GVE_2060_RCP85_DRY.fwt", text)
        self.assertIn("Solar shading YES", text)
        self.assertIn("Operable windows NO", text)
        self.assertIn("Mechanical cooling YES", text)
        self.assertNotIn("SIA 4010", full_text)
        images = reader.pages[1]["/Resources"]["/XObject"]
        self.assertGreaterEqual(len(images), 2)


if __name__ == "__main__":
    unittest.main()
