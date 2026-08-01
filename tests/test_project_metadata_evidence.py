"""Tests for reviewer-controlled SIA 380/2 project metadata."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from swiss_sia import app
from swiss_sia.evidence_manager import (
    find_accepted_global_comparison,
    find_accepted_project_metadata,
    scan_sia3802_global_comparisons,
    scan_sia3802_project_metadata,
)


class ProjectMetadataEvidenceTests(unittest.TestCase):
    """Verify that building status is accepted only with auditable metadata."""

    def setUp(self) -> None:
        """Prepare a writable evidence path directly in the test directory."""
        self.project_root = Path(__file__).resolve().parents[1]
        self.csv_path = Path(__file__).with_name(
            "SIA3802_project_metadata_unit_test.csv"
        )
        self.comparison_path = Path(__file__).with_name(
            "SIA3802_global_reference_comparison_unit_test.csv"
        )
        self.active_metadata_path = Path(__file__).with_name(
            "SIA3802_project_metadata_Demo_Project.csv"
        )
        self.foreign_metadata_path = Path(__file__).with_name(
            "SIA3802_project_metadata_Demo_Project_10.csv"
        )

    def tearDown(self) -> None:
        """Remove the temporary metadata CSV after each test."""
        self.csv_path.unlink(missing_ok=True)
        self.comparison_path.unlink(missing_ok=True)
        self.active_metadata_path.unlink(missing_ok=True)
        self.foreign_metadata_path.unlink(missing_ok=True)

    def test_metadata_scan_excludes_files_for_other_projects(self) -> None:
        """Read only the helper file whose filename targets the active VE project."""
        header = (
            "project_id,building_status,weather_basis,weather_file,location,"
            "altitude_m,review_status,reviewer,review_date,source_document,"
            "source_reference,notes\n"
        )
        self.active_metadata_path.write_text(
            header
            + "Demo_Project,new building,SIA 2028 DRY,demo.epw,Zurich,408,"
            "accepted,Reviewer,2026-07-15,Project brief,Section 3,Reviewed\n",
            encoding="utf-8",
        )
        self.foreign_metadata_path.write_text(
            header
            + "Demo_Project_10,existing building,Other weather,other.epw,Bern,540,"
            "accepted,Other reviewer,2026-07-15,Other brief,Section 2,Reviewed\n",
            encoding="utf-8",
        )

        result = scan_sia3802_project_metadata(
            self.project_root,
            "tests",
            "Demo_Project",
        )

        self.assertEqual(result["record_count"], 1)
        self.assertEqual(len(result["excluded_files"]), 1)
        self.assertEqual(result["records"][0]["project_id"], "Demo_Project")

    def test_reviewed_metadata_is_normalized_and_matched(self) -> None:
        """Accept a complete reviewed row and normalize its building status."""
        self.csv_path.write_text(
            "project_id,building_status,weather_basis,weather_file,location,altitude_m,review_status,reviewer,review_date,source_document,source_reference,notes\n"
            "Demo_Project,new building,SIA 2028 DRY,demo.epw,Zurich,408,accepted,Reviewer,2026-07-15,Project brief,Section 3,Reviewed\n",
            encoding="utf-8",
        )

        result = scan_sia3802_project_metadata(self.project_root, "tests")
        record = find_accepted_project_metadata(result, "Demo Project")

        self.assertEqual(result["status"], "AVAILABLE")
        self.assertIsNotNone(record)
        self.assertEqual(record["building_status"], "NEW_BUILDING")
        self.assertEqual(record["weather_file"], "demo.epw")

    def test_incomplete_or_invalid_status_is_not_accepted(self) -> None:
        """Reject rows without review provenance or a supported status."""
        self.csv_path.write_text(
            "project_id,building_status,review_status,reviewer,review_date,source_document,source_reference\n"
            "Demo_Project,renovated,accepted,Reviewer,2026-07-15,Project brief,Section 3\n"
            "Demo_Project,existing building,pending,,,,\n",
            encoding="utf-8",
        )

        result = scan_sia3802_project_metadata(self.project_root, "tests")

        self.assertEqual(result["status"], "PENDING_REVIEW")
        self.assertEqual(result["accepted_count"], 0)
        self.assertIsNone(find_accepted_project_metadata(result, "Demo_Project"))

    def test_dynamic_summary_uses_reviewed_matching_metadata(self) -> None:
        """Propagate accepted project status and weather match into APS summary."""
        metadata = {
            "building_status": "EXISTING_BUILDING",
            "weather_basis": "SIA 2028 DRY",
            "weather_file": "demo.epw",
            "location": "Zurich",
            "altitude_m": "408",
            "file": "metadata.csv",
            "row": 2,
        }
        project = SimpleNamespace(path=r"C:\VE\Demo_Project")
        with (
            patch.object(app, "scan_sia3802_project_metadata", return_value={"status": "AVAILABLE"}),
            patch.object(app, "find_accepted_project_metadata", return_value=metadata),
            patch.object(app, "scan_sia3802_global_comparisons", return_value={"status": "NOT_PROVIDED"}),
            patch.object(app, "find_accepted_global_comparison", return_value=None),
            patch.object(app, "_current_project_weather_label", return_value="demo.epw"),
            patch.object(app.simulation_results_module, "list_aps_files", return_value=[]),
        ):
            summary = app._collect_dynamic_results(project)

        self.assertEqual(summary["building_status"], "EXISTING_BUILDING")
        self.assertEqual(summary["reviewed_weather_match_status"], "MATCH")
        self.assertEqual(summary["reviewed_weather_basis"], "SIA 2028 DRY")
        self.assertEqual(summary["status"], "NOT_CHECKABLE")

    def test_global_comparison_requires_complete_reviewed_scope(self) -> None:
        """Accept only a complete project-level result with audit provenance."""
        self.comparison_path.write_text(
            "project_id,comparison_scope,project_value,reference_value,unit,comparison_result,reviewer,review_date,review_status,source_document,source_reference,notes\n"
            "Demo_Project,complete_sia3802_project,42.0,45.0,kWh/m2,compliant,Reviewer,2026-07-15,accepted,Calculation workbook,Summary,Reviewed\n",
            encoding="utf-8",
        )

        result = scan_sia3802_global_comparisons(self.project_root, "tests")
        record = find_accepted_global_comparison(result, "Demo Project")

        self.assertEqual(result["status"], "AVAILABLE")
        self.assertIsNotNone(record)
        self.assertEqual(record["project_value_numeric"], 42.0)
        self.assertEqual(record["reference_value_numeric"], 45.0)


if __name__ == "__main__":
    unittest.main()
