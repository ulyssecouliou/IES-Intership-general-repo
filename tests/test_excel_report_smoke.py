"""Smoke tests for the integrated professional Excel report."""

from __future__ import annotations

import unittest
import zipfile
from pathlib import Path

from scripts.quality.fixtures import StaticModelAnalyzer, build_reference_room
from swiss_sia.excel_report import ExcelReportGenerator
from swiss_sia.health_score import HealthScoreCalculator
from swiss_sia.rule_engine import RuleEngine
from swiss_sia.sia380_checker import SIA3802Checker
from swiss_sia.sia4010_checker import SIA4010Checker
from swiss_sia.reference_project import build_reference_project_specification
from swiss_sia.validation_class_scope import derive_validation_class_scope


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
    """Guard the SIA 380/2-only client workbook against SIA 4010 leakage."""

    # The only places a client 380/2-only workbook may still mention SIA 4010:
    # two protective disclaimers that tell the reader not to over-claim, a single
    # credential line pointing at the tool's separate Anwenderbericht, and two
    # provenance citations that name the exact SIA article behind a value. Every
    # other SIA 4010 sheet, card, KPI and label must be gone. Each entry is a
    # distinctive fragment; a leaked string must contain one of them to pass.
    _ALLOWLIST_MARKERS = (
        "does not constitute SIA 4010 validation",          # cover disclaimer
        "Tool undergoing SIA 4010 validation",              # cover credential line
        "Do not claim final SIA compliance or SIA 4010",    # action-dashboard disclaimer
        "table 2; SIA 4010 clause 3.1.5.",                  # provenance citation
        "SIA 4010 system tables.",                          # provenance citation
    )

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
            workbook_xml = workbook.read("xl/workbook.xml").decode("utf-8", "ignore")
            shared_strings = workbook.read("xl/sharedStrings.xml").decode("utf-8", "ignore")
        return workbook_xml + shared_strings

    def test_client_workbook_has_no_sia4010_outside_allowlist(self) -> None:
        """A 380/2-only workbook mentions SIA 4010 only in the allowlisted cells."""
        import re

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

            # Every shared string carrying "4010" must be one of the allowlisted
            # disclaimers, the credential line or a provenance citation.
            strings = re.findall(r"<t[^>]*>(.*?)</t>", report_text, re.S)
            leaked = [
                text
                for text in strings
                if "4010" in text
                and not any(marker in text for marker in self._ALLOWLIST_MARKERS)
            ]
            self.assertEqual(
                leaked,
                [],
                msg=f"Unexpected SIA 4010 content in the client workbook: {leaked}",
            )

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


if __name__ == "__main__":
    unittest.main()
