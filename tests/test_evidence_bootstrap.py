"""Tests for safe project-specific evidence-template generation."""

from __future__ import annotations

import csv
import shutil
import unittest
from pathlib import Path

from swiss_sia.evidence_bootstrap import prepare_evidence_folder


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
            self.assertEqual(result["created_count"], 14)
            evidence_dir = Path(result["evidence_dir"])
            g_values_path = evidence_dir / "g_values_audit_SIA_compatible_model.csv"
            metadata_path = evidence_dir / "SIA3802_project_metadata_SIA_compatible_model.csv"

            with g_values_path.open(encoding="utf-8", newline="") as handle:
                g_values_row = next(csv.DictReader(handle))
            with metadata_path.open(encoding="utf-8", newline="") as handle:
                metadata_row = next(csv.DictReader(handle))

            self.assertEqual(g_values_row["project_name"], "SIA_compatible_model")
            self.assertEqual(g_values_row["review_status"], "pending")
            self.assertEqual(metadata_row["project_id"], "SIA_compatible_model")
            self.assertNotIn("ZOER_32_C1", g_values_path.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(temporary_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
