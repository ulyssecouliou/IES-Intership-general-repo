"""Tests for safe project-specific evidence-template generation."""

from __future__ import annotations

import csv
import shutil
import unittest
from pathlib import Path

from swiss_sia.evidence_bootstrap import (
    TEMPLATE_TARGETS,
    prepare_evidence_folder,
    prefill_cooling_generator_evidence,
    prefill_lighting_control_evidence,
    prefill_sia2024_usage_evidence,
    prefill_ventilation_control_evidence,
)
from swiss_sia.model_analyzer import RoomData

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class EvidenceBootstrapTests(unittest.TestCase):
    """Prevent example-project values from entering a new evidence folder."""

    def test_templates_receive_the_safe_active_project_label(self) -> None:
        """Inject the project label into CSV content and preserve pending review state."""
        temporary_root = PROJECT_ROOT / "tests" / "_evidence_bootstrap_workspace"
        shutil.rmtree(temporary_root, ignore_errors=True)
        try:
            shutil.copytree(
                PROJECT_ROOT / "templates" / "evidence",
                temporary_root / "templates" / "evidence",
            )

            result = prepare_evidence_folder(
                project_root=temporary_root,
                project_label="SIA compatible model",
            )

            self.assertEqual(result["status"], "READY")
            self.assertEqual(result["created_count"], 16)
            evidence_dir = Path(result["evidence_dir"])
            g_values_path = evidence_dir / "g_values_audit_SIA_compatible_model.csv"
            metadata_path = (
                evidence_dir / "SIA3802_project_metadata_SIA_compatible_model.csv"
            )

            with g_values_path.open(encoding="utf-8", newline="") as handle:
                g_values_row = next(csv.DictReader(handle))
            with metadata_path.open(encoding="utf-8", newline="") as handle:
                metadata_row = next(csv.DictReader(handle))

            self.assertEqual(g_values_row["project_name"], "SIA_compatible_model")
            self.assertEqual(g_values_row["review_status"], "pending")
            self.assertEqual(metadata_row["project_id"], "SIA_compatible_model")
            self.assertNotIn("ZOER_32_C1", g_values_path.read_text(encoding="utf-8"))

            software_register = evidence_dir / (
                "SIA4010_software_register_review_SIA_compatible_model.csv"
            )
            self.assertTrue(software_register.is_file())

            room = RoomData(
                id="ROOM-1",
                mechanical_ventilation_present=True,
                ventilation_m3_h_m2=4.0,
                ventilation_installation_type="monozone",
                ventilation_control_level=1,
                ventilation_control_evidence_note="explicit VE identifiers",
                hvac_systems=[
                    {
                        "id": "SYS-1",
                        "air_flow_control": "MULTI_STAGE",
                        "fan_control": "DIRECT",
                        "cooling_capacity_kw": 18.5,
                        "eer": 3.2,
                        "seer": 4.1,
                    }
                ],
            )
            prefill = prefill_ventilation_control_evidence(
                [room], temporary_root, "SIA compatible model"
            )
            self.assertEqual(prefill["status"], "PREFILLED")
            with Path(prefill["file"]).open(encoding="utf-8", newline="") as handle:
                ventilation_row = next(csv.DictReader(handle))
            self.assertEqual(ventilation_row["system_id"], "SYS-1")
            self.assertEqual(ventilation_row["control_class"], "two_speeds_time_schedule")
            self.assertEqual(ventilation_row["airflow_band"], "3_TO_6")
            self.assertEqual(ventilation_row["review_status"], "pending")

            room.thermal_template_id = "SIA2024_4.01_CLASSROOM_REFERENCE"
            room.daylight_dimming_profile = "ON"
            cooling = prefill_cooling_generator_evidence(
                [room], temporary_root, "SIA compatible model"
            )
            usage = prefill_sia2024_usage_evidence(
                [room], temporary_root, "SIA compatible model"
            )
            lighting = prefill_lighting_control_evidence(
                [room], temporary_root, "SIA compatible model"
            )
            self.assertEqual(cooling["status"], "PREFILLED")
            self.assertEqual(usage["status"], "PREFILLED")
            self.assertEqual(lighting["status"], "PREFILLED")
            with Path(usage["file"]).open(encoding="utf-8", newline="") as handle:
                usage_row = next(csv.DictReader(handle))
            with Path(lighting["file"]).open(encoding="utf-8", newline="") as handle:
                lighting_row = next(csv.DictReader(handle))
            with Path(cooling["file"]).open(encoding="utf-8", newline="") as handle:
                cooling_row = next(csv.DictReader(handle))
            self.assertEqual(cooling_row["generator_class"], "")
            self.assertEqual(cooling_row["capacity_kw"], "18.5")
            self.assertEqual(cooling_row["nominal_eer"], "3.2")
            self.assertEqual(cooling_row["seer"], "4.1")
            self.assertEqual(cooling_row["review_status"], "pending")
            self.assertEqual(usage_row["sia2024_category"], "4.01")
            self.assertEqual(usage_row["review_status"], "pending")
            self.assertEqual(lighting_row["daylight_control"], "ON")
            self.assertEqual(lighting_row["sia3874_control_type"], "")
            self.assertEqual(lighting_row["review_status"], "pending")
        finally:
            shutil.rmtree(temporary_root, ignore_errors=True)

    def test_every_csv_template_is_registered_and_auditable(self) -> None:
        """Keep the evidence directory, bootstrap and reviewer fields in sync."""
        template_dir = PROJECT_ROOT / "templates" / "evidence"
        disk_templates = {path.name for path in template_dir.glob("*_template.csv")}
        registered_templates = {source for source, _target in TEMPLATE_TARGETS}
        self.assertEqual(disk_templates, registered_templates)

        target_patterns = [target for _source, target in TEMPLATE_TARGETS]
        self.assertEqual(len(target_patterns), len(set(target_patterns)))
        for template_name in sorted(disk_templates):
            with (template_dir / template_name).open(
                encoding="utf-8-sig", newline=""
            ) as handle:
                rows = list(csv.reader(handle))
            self.assertGreaterEqual(len(rows), 2, template_name)
            header = rows[0]
            self.assertTrue(all(header), template_name)
            self.assertEqual(len(header), len(set(header)), template_name)
            self.assertTrue(
                "review_status" in header or "status" in header,
                template_name,
            )
            self.assertTrue(
                "source_document" in header or "source_authority" in header,
                template_name,
            )

    def test_templates_can_come_from_repository_while_target_is_ve_project(self) -> None:
        """Keep product templates separate from project-local reviewer evidence."""
        temporary_root = PROJECT_ROOT / "tests" / "_external_ve_project"
        shutil.rmtree(temporary_root, ignore_errors=True)
        try:
            result = prepare_evidence_folder(
                project_root=temporary_root,
                project_label="Client model",
                template_root=PROJECT_ROOT,
            )
            self.assertEqual(result["status"], "READY")
            self.assertEqual(result["created_count"], len(TEMPLATE_TARGETS))
            self.assertTrue(
                (
                    temporary_root
                    / "sia4010_evidence"
                    / "SIA3802_project_metadata_Client_model.csv"
                ).is_file()
            )
            self.assertFalse((temporary_root / "templates").exists())
        finally:
            shutil.rmtree(temporary_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
