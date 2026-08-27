"""Tests for the SIA 4010 official-bundle manifest builder."""

import unittest
from pathlib import Path

from swiss_sia.reference_model.sia4010.bundle_builder import (
    build_manifest,
    write_manifest,
)
from swiss_sia.reference_model.sia4010.test_loader import Sia4010TestLoader

TEST_ROOT = Path(__file__).resolve().parents[1]
TEST_OUTPUT_ROOT = TEST_ROOT / ".codex_tmp" / "sia4010_bundle_tests"


def _make_bundle(name: str) -> Path:
    """Create a small fake official bundle mirroring the real folder layout."""

    root = TEST_OUTPUT_ROOT / name
    (root / "Test1" / "Anwenderberichte").mkdir(parents=True, exist_ok=True)
    (root / "Beispielgebaeude").mkdir(parents=True, exist_ok=True)
    (root / "Test1" / "Resultaterfassung_Test1.xlsx").write_bytes(b"workbook-1")
    (root / "Test1" / "Spezifikation_Test1.pdf").write_bytes(b"spec-1")
    (root / "Test1" / "Anwenderberichte" / "EnergyPlus_Test1.pdf").write_bytes(b"ref-1")
    (root / "Beispielgebaeude" / "model.ifc").write_bytes(b"ifc-bytes")
    return root


class Sia4010BundleBuilderTests(unittest.TestCase):
    def test_manifest_assigns_roles_and_test_ids(self):
        root = _make_bundle("roles")
        manifest = build_manifest(root)
        self.assertEqual(manifest["schema_version"], "1.0")
        self.assertIn("SIA", manifest["issued_by"])
        by_path = {item["path"]: item for item in manifest["files"]}
        self.assertEqual(
            by_path["Test1/Resultaterfassung_Test1.xlsx"]["role"],
            "evaluation_workbook",
        )
        self.assertEqual(by_path["Test1/Resultaterfassung_Test1.xlsx"]["test_ids"], ["1"])
        self.assertEqual(
            by_path["Test1/Spezifikation_Test1.pdf"]["role"], "test_specification"
        )
        self.assertEqual(
            by_path["Test1/Anwenderberichte/EnergyPlus_Test1.pdf"]["role"],
            "reference_report",
        )
        self.assertEqual(
            by_path["Beispielgebaeude/model.ifc"]["role"], "example_building_ifc"
        )
        self.assertEqual(
            by_path["Beispielgebaeude/model.ifc"]["test_ids"], ["4", "5", "6", "7"]
        )

    def test_written_manifest_round_trips_through_loader(self):
        root = _make_bundle("roundtrip")
        write_manifest(root)
        bundle = Sia4010TestLoader().load_bundle(root)
        self.assertIn("SIA", bundle.issued_by)
        self.assertEqual(len(bundle.files), 4)  # loader re-verifies every checksum

    def test_tampered_file_fails_checksum_verification(self):
        from swiss_sia.reference_model.exceptions import ConfigurationError

        root = _make_bundle("tampered")
        write_manifest(root)
        # Mutate a file after the manifest was written -> checksum must mismatch.
        (root / "Test1" / "Resultaterfassung_Test1.xlsx").write_bytes(b"tampered")
        with self.assertRaises(ConfigurationError):
            Sia4010TestLoader().load_bundle(root)


if __name__ == "__main__":
    unittest.main()
