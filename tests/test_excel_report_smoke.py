"""Smoke tests for the integrated professional Excel report."""

from __future__ import annotations

import struct
import unittest
import zipfile
import zlib
from pathlib import Path

from scripts.quality.fixtures import StaticModelAnalyzer, build_reference_room
from swiss_sia.excel_report import ExcelReportGenerator
from swiss_sia.health_score import HealthScoreCalculator
from swiss_sia.rule_engine import Alert, RuleEngine, Severity
from swiss_sia.sia380_checker import SIA3802Checker
from swiss_sia.sia4010_checker import SIA4010Checker
from swiss_sia.reference_project import build_reference_project_specification
from swiss_sia.validation_class_scope import derive_validation_class_scope
from swiss_sia.client_report_context import (
    ClientReportContext,
    building_strategy_text,
)
from swiss_sia.reference_model.sia4010.ui_translations import translate


def _write_rgb_png(path: Path, width: int = 20, height: int = 12) -> Path:
    """Write a small dependency-free RGB image for workbook embedding tests."""

    raw = bytearray()
    for row in range(height):
        raw.append(0)
        for column in range(width):
            raw += bytes((column * 11 % 256, row * 19 % 256, 120))

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


def _build_report_inputs():
    """Return deterministic (analyzer, score, sia3802, sia4010, rooms, dynamic).

    Mirrors the production path closely enough to exercise every shared sheet:
    external mappings accepted, a derived validation-class scope and a
    reference-project specification are all attached before scoring.
    """

    room = build_reference_room()
    rooms = [room]
    analyzer = StaticModelAnalyzer(rooms)
    external_mappings = {
        "sia2024_usage": {
            "accepted": [{"room_id": room.id, "sia2024_category": "QUALITY_FIXTURE"}]
        },
        "sia3874_lighting": {
            "accepted": [{"room_id": room.id, "sia3874_control_type": "QUALITY_FIXTURE"}]
        },
    }
    dynamic_results = {
        "status": "NOT_CHECKABLE",
        "building_status": "NEW_BUILDING",
        "rooms": [],
        "design_power_status": "NOT_CHECKABLE",
        "notes": "Deterministic workbook smoke fixture.",
    }
    sia3802_results = SIA3802Checker(analyzer, RuleEngine()).check_all(
        rooms_data=rooms,
        dynamic_results=dynamic_results,
        external_mappings=external_mappings,
    )
    sia4010_results = SIA4010Checker(analyzer, RuleEngine()).check_all(rooms_data=rooms)
    sia4010_results["required_class_scope"] = derive_validation_class_scope(rooms).to_dict()
    sia3802_results["reference_project"] = build_reference_project_specification(
        rooms, analyzer
    ).to_dict()
    score_result = HealthScoreCalculator().calculate_scores(sia3802_results, sia4010_results)
    return analyzer, score_result, sia3802_results, sia4010_results, rooms, dynamic_results


class ExcelReportSmokeTests(unittest.TestCase):
    """Exercise the report generator with deterministic normalized VE data."""

    def test_dynamic_alert_data_includes_observed_hours_and_limit(self) -> None:
        """Keep the Excel alert row auditable for summer-comfort failures."""
        helper = ExcelReportGenerator.__new__(ExcelReportGenerator)
        alert = Alert(
            rule="SIA3802_SUMMER_COMFORT_DYNAMIC",
            description="Occupied hours exceed the applicable allowance.",
            severity=Severity.HIGH,
            category="Dynamic Method",
            recommendation="Review the room.",
            data={
                "room_name": "Office_01",
                "upper_hours": 1445.5,
                "upper_limit_hours": 0.0,
                "lower_hours": 0.0,
                "method": "CONSERVATIVE_ZERO_HOUR_SCREENING_OPERABILITY_UNKNOWN",
            },
        )

        evidence = helper._format_alert_data(alert)
        self.assertIn("room_name=Office_01", evidence)
        self.assertIn("upper_hours=1445.5 h", evidence)
        self.assertIn("upper_limit_hours=0.0 h", evidence)
        self.assertIn("lower_hours=0.0 h", evidence)

    def test_report_contains_readiness_dynamic_and_chart_parts(self) -> None:
        """Generate a workbook and verify its critical professional artifacts."""
        room = build_reference_room()
        rooms = [room]
        analyzer = StaticModelAnalyzer(rooms)
        external_mappings = {
            "sia2024_usage": {
                "accepted": [{"room_id": room.id, "sia2024_category": "QUALITY_FIXTURE"}]
            },
            "sia3874_lighting": {
                "accepted": [
                    {
                        "room_id": room.id,
                        "sia3874_control_type": "QUALITY_FIXTURE",
                    }
                ]
            },
        }
        dynamic_results = {
            "status": "NOT_CHECKABLE",
            "building_status": "NEW_BUILDING",
            "rooms": [],
            "design_power_status": "NOT_CHECKABLE",
            "notes": "Deterministic workbook smoke fixture.",
        }

        sia3802_results = SIA3802Checker(analyzer, RuleEngine()).check_all(
            rooms_data=rooms,
            dynamic_results=dynamic_results,
            external_mappings=external_mappings,
        )
        sia4010_results = SIA4010Checker(analyzer, RuleEngine()).check_all(
            rooms_data=rooms
        )
        # Mirror the production path: the model's required validation-class scope
        # is derived and rendered in the SIA4010 CLASS MATRIX sheet.
        class_scope = derive_validation_class_scope(rooms)
        sia4010_results["required_class_scope"] = class_scope.to_dict()
        self.assertTrue(class_scope.findings)
        reference_specification = build_reference_project_specification(rooms, analyzer)
        sia3802_results["reference_project"] = reference_specification.to_dict()
        self.assertTrue(reference_specification.substitutions)
        score_result = HealthScoreCalculator().calculate_scores(
            sia3802_results,
            sia4010_results,
        )
        helper = ExcelReportGenerator.__new__(ExcelReportGenerator)
        coverage_stats = helper._build_sia4010_model_stats(
            rooms,
            {**sia4010_results, "dynamic_results": dynamic_results},
        )
        climate_status, _climate_text = helper._coverage_status_for_key(
            "project_climate",
            coverage_stats,
            {},
            {
                **dynamic_results,
                "project_metadata_status": "AVAILABLE",
                "reviewed_weather_match_status": "MATCH",
            },
            {"Active VE project": "PASS"},
        )

        self.assertGreater(coverage_stats["rooms_with_daily_profile_hours"], 0)
        self.assertGreater(coverage_stats["rooms_with_ventilation_control"], 0)
        self.assertGreater(coverage_stats["cooling_systems_with_efficiency"], 0)
        self.assertGreater(coverage_stats["heating_systems_with_efficiency"], 0)
        self.assertEqual(climate_status, "AVAILABLE")

        output_path = Path(__file__).with_name("_excel_report_smoke.xlsx")
        try:
            ExcelReportGenerator(str(output_path), analyzer).generate_report(
                score_result,
                sia3802_results,
                sia4010_results,
                rooms_data=rooms,
                dynamic_results=dynamic_results,
            )

            self.assertTrue(output_path.exists())
            with zipfile.ZipFile(output_path) as workbook:
                names = set(workbook.namelist())
                workbook_xml = workbook.read("xl/workbook.xml").decode(
                    "utf-8", errors="ignore"
                )
                shared_strings = workbook.read("xl/sharedStrings.xml").decode(
                    "utf-8", errors="ignore"
                )

            report_text = workbook_xml + shared_strings
            self.assertIn("SIA4010 CLASS MATRIX", report_text)
            self.assertIn("Variant-Level Class Readiness", report_text)
            # The required-class scope reaches the reader, with its justification
            # and its anti-overclaim note.
            self.assertIn("Class required by this model", report_text)
            self.assertIn("Why this model requires that class", report_text)
            self.assertIn("does not assert that the tool holds", report_text)
            self.assertIn("REFERENCE PROJECT", report_text)
            self.assertIn("Reference-Project Input Specification", report_text)
            self.assertIn("DYNAMIC RESULTS", report_text)
            self.assertIn("Reviewed building status", report_text)
            self.assertTrue(any(name.startswith("xl/charts/chart") for name in names))
            self.assertTrue(any(name.startswith("xl/drawings/drawing") for name in names))
        finally:
            output_path.unlink(missing_ok=True)


class ClientSia3802OnlyReportTests(unittest.TestCase):
    """Keep the client workbook strictly on real SIA 380/2 compliance."""

    def _generate(self, output_path: Path, *, include_sia4010: bool) -> str:
        analyzer, score, s3802, s4010, rooms, dynamic = _build_report_inputs()
        ExcelReportGenerator(str(output_path), analyzer).generate_report(
            score,
            s3802,
            s4010,
            rooms_data=rooms,
            dynamic_results=dynamic,
            include_sia4010=include_sia4010,
        )
        with zipfile.ZipFile(output_path) as workbook:
            return "\n".join(
                workbook.read(name).decode("utf-8", "ignore")
                for name in workbook.namelist()
                if name.endswith(".xml")
            )

    def test_client_workbook_has_no_sia4010_or_development_indicators(self) -> None:
        """The client workbook contains compliance, not software/readiness KPIs."""

        output_path = Path(__file__).with_name("_excel_report_3802_only.xlsx")
        try:
            report_text = self._generate(output_path, include_sia4010=False)

            # No dedicated SIA 4010 sheet survives, and no dashboard nav button
            # links to one.
            for sheet_name in (
                "SIA4010 READINESS",
                "SIA4010 PREVALIDATION",
                "SIA4010 CLASS MATRIX",
                "SIA4010 SOFTWARE REGISTER",
            ):
                self.assertNotIn(sheet_name, report_text)

            self.assertNotIn("4010", report_text)
            self.assertNotIn("Model health score", report_text)
            self.assertNotIn("SIA 380/2 automated score", report_text)
            self.assertNotIn("DETAILED SCORES", report_text)

            # The 380/2 client deliverable still carries its own content.
            self.assertIn("SIA 380/2", report_text)
            self.assertIn("CLIENT SUMMARY", report_text)
            self.assertIn("REFERENCE PROJECT", report_text)
        finally:
            output_path.unlink(missing_ok=True)

    def test_default_workbook_keeps_full_sia4010_sections(self) -> None:
        """The default report is unchanged: the SIA 4010 sheets are present."""
        output_path = Path(__file__).with_name("_excel_report_full.xlsx")
        try:
            report_text = self._generate(output_path, include_sia4010=True)
            for sheet_name in (
                "SIA4010 READINESS",
                "SIA4010 CLASS MATRIX",
                "SIA4010 SOFTWARE REGISTER",
            ):
                self.assertIn(sheet_name, report_text)
        finally:
            output_path.unlink(missing_ok=True)

    def test_client_workbook_uses_real_verdict_and_project_information(self) -> None:
        """The client headlines contain compliance, not development scores."""

        output_path = Path(__file__).with_name("_excel_report_client_ui.xlsx")
        viewer_image = _write_rgb_png(
            Path(__file__).resolve().parents[1]
            / ".codex_tmp"
            / "excel_client_model_viewer.png"
        )
        analyzer, score, s3802, s4010, rooms, dynamic = _build_report_inputs()
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
            building_strategy_notes="External blinds; cooling at 26 C.",
            model_viewer_image_path=str(viewer_image),
        )
        try:
            ExcelReportGenerator(
                str(output_path), analyzer, report_context=context
            ).generate_report(
                score,
                s3802,
                s4010,
                rooms_data=rooms,
                dynamic_results=dynamic,
                include_sia4010=False,
            )
            with zipfile.ZipFile(output_path) as workbook:
                workbook_xml = workbook.read("xl/workbook.xml").decode("utf-8", "ignore")
                strings = workbook.read("xl/sharedStrings.xml").decode("utf-8", "ignore")
                sheet_xml = "".join(
                    workbook.read(name).decode("utf-8", "ignore")
                    for name in workbook.namelist()
                    if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
                )
                embedded_images = [
                    workbook.read(name)
                    for name in workbook.namelist()
                    if name.startswith("xl/media/")
                ]
            report_text = workbook_xml + strings + sheet_xml
            self.assertIn("MODEL VIEWER", report_text)
            self.assertIn("Client Alpine SA", report_text)
            self.assertIn("School North", report_text)
            self.assertIn("CHE_GVE_2060_RCP85_DRY.fwt", report_text)
            self.assertIn(building_strategy_text("field_building_strategy", "en"), report_text)
            self.assertIn("Windows: NO", report_text)
            self.assertIn("Client building-strategy notes", report_text)
            self.assertIn(translate("excel_client_summary_title", "en"), report_text)
            self.assertIn("IES |", report_text)
            self.assertNotIn("Model health score", report_text)
            self.assertNotIn("SIA 380/2 automated score", report_text)
            self.assertIn(viewer_image.read_bytes(), embedded_images)
            self.assertIn(
                (Path(__file__).resolve().parents[1] / "assets" / "ies_logo.png").read_bytes(),
                embedded_images,
            )
        finally:
            output_path.unlink(missing_ok=True)
            viewer_image.unlink(missing_ok=True)

    def test_client_workbook_uses_selected_report_language(self) -> None:
        """The client-facing Excel pages follow the language selected in the UI."""

        analyzer, score, s3802, s4010, rooms, dynamic = _build_report_inputs()
        for language in ("en", "de", "fr", "it"):
            with self.subTest(language=language):
                output_path = Path(__file__).with_name(
                    f"_excel_report_language_{language}.xlsx"
                )
                context = ClientReportContext(
                    client_name="International Client",
                    project_name="Multilingual Project",
                    language=language,
                    language_selected=True,
                )
                try:
                    ExcelReportGenerator(
                        str(output_path), analyzer, report_context=context
                    ).generate_report(
                        score,
                        s3802,
                        s4010,
                        rooms_data=rooms,
                        dynamic_results=dynamic,
                        include_sia4010=False,
                    )
                    with zipfile.ZipFile(output_path) as workbook:
                        strings = workbook.read("xl/sharedStrings.xml").decode(
                            "utf-8", "ignore"
                        )
                    self.assertIn(translate("report_title", language), strings)
                    self.assertIn(
                        translate("excel_client_summary_title", language), strings
                    )
                    self.assertIn(
                        translate("excel_model_viewer_title", language), strings
                    )
                finally:
                    output_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
