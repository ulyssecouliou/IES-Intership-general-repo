"""Tests for the project-local evidence editor backend."""

from __future__ import annotations

import csv
import shutil
import unittest
from pathlib import Path
from unittest.mock import Mock

from swiss_sia.project_evidence import evidence_path, load_records, save_records
from swiss_sia.rule_engine import RuleEngine
from swiss_sia.sia4010_checker import SIA4010Checker


class ProjectEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parent / "_project_evidence_workspace"
        shutil.rmtree(self.root, ignore_errors=True)
        self.root.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_invalid_requested_acceptance_is_forced_pending(self) -> None:
        result = save_records(
                self.root, "project_metadata", "My VE Project",
                [{
                    "building_status": "NEW_BUILDING",
                    "review_status": "accepted",
                    "reviewer": "",
                    "review_date": "",
                    "source_document": "",
                }],
            )
        self.assertEqual(result["forced_pending_count"], 1)
        with Path(result["path"]).open(encoding="utf-8", newline="") as handle:
            row = next(csv.DictReader(handle))
        self.assertEqual(row["project_id"], "My_VE_Project")
        self.assertEqual(row["review_status"], "pending")

    def test_complete_metadata_is_accepted_and_backup_is_created(self) -> None:
        record = {
                "building_status": "EXISTING_BUILDING", "weather_basis": "SIA 2028 DRY",
                "weather_file": "reviewed.epw", "location": "Geneva", "altitude_m": "420",
                "review_status": "accepted", "reviewer": "Energy engineer",
                "review_date": "2026-08-24", "source_document": "Climate brief",
                "source_reference": "p. 4", "notes": "Reviewed",
        }
        first = save_records(self.root, "project_metadata", "Project A", [record])
        second = save_records(self.root, "project_metadata", "Project A", [record])
        self.assertEqual(first["accepted_count"], 1)
        self.assertEqual(second["accepted_count"], 1)
        self.assertTrue(Path(second["backup"]).is_file())
        loaded = load_records(self.root, "project_metadata", "Project A")
        self.assertEqual(loaded[0]["reviewer"], "Energy engineer")
        self.assertEqual(
            evidence_path(self.root, "project_metadata", "Project A"), Path(first["path"])
        )

    def test_multiple_ventilation_rows_are_preserved(self) -> None:
        base = {
                "system_type": "monozone", "control_class": "two_speeds_time_schedule",
                "airflow_band": "3_TO_6", "specific_airflow_m3_h_m2": "4",
                "review_status": "accepted", "reviewer": "HVAC engineer",
                "review_date": "2026-08-24", "source_document": "Ventilation design",
        }
        rows = [dict(base, system_id="SYS-1"), dict(base, system_id="SYS-2")]
        result = save_records(self.root, "ventilation_control", "P", rows)
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["accepted_count"], 2)
        self.assertEqual(len(load_records(self.root, "ventilation_control", "P")), 2)

    def test_sia4010_checker_reads_the_explicit_active_project_root(self) -> None:
        evidence = self.root / "sia4010_evidence"
        evidence.mkdir()
        active = evidence / "SIA3802_project_metadata_P.csv"
        other = evidence / "SIA3802_project_metadata_Other.csv"
        active.write_text("project_id\nP\n", encoding="utf-8")
        other.write_text("project_id\nOther\n", encoding="utf-8")
        checker = SIA4010Checker(
            Mock(), RuleEngine(), project_label="P", project_root=self.root
        )
        result = checker._scan_sia4010_evidence()
        self.assertEqual(Path(result["evidence_dir"]), evidence)
        self.assertIn(active.name, {item["name"] for item in result["files"]})
        self.assertNotIn(other.name, {item["name"] for item in result["files"]})


if __name__ == "__main__":
    unittest.main()
