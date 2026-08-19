"""Fail-closed tests for delegated SIA 4010 input evidence."""

import hashlib
import json
import shutil
import unittest
from pathlib import Path

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.external_input_manifest import (
    EXTERNAL_INPUT_CATALOG,
    EXTERNAL_INPUT_BINDING_SCHEMAS,
    EXTERNAL_INPUT_FILENAME,
    Sia4010ExternalInputManifest,
    build_external_input_matrix,
    external_input_readiness,
    required_external_input_ids,
)


ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / ".codex_tmp" / "external_inputs"


def _sha256(path: Path) -> str:
    """Return the lowercase SHA-256 digest of one test fixture."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


class Sia4010ExternalInputManifestTests(unittest.TestCase):
    """External normative inputs never become ready from filenames alone."""

    def setUp(self):
        self.project = WORK_ROOT / self._testMethodName
        if self.project.exists():
            shutil.rmtree(self.project)
        self.project.mkdir(parents=True)

    def tearDown(self):
        if self.project.exists():
            shutil.rmtree(self.project)

    def _write_manifest(self, inputs, schema_version="1.0"):
        path = self.project / EXTERNAL_INPUT_FILENAME
        path.write_text(
            json.dumps(
                {"schema_version": schema_version, "inputs": inputs},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return path

    def _ready_entry(self, input_id):
        source = self.project / "{}.json".format(input_id)
        binding = self.project / "{}_binding.json".format(input_id)
        report = self.project / "{}_validation.json".format(input_id)
        source.write_text(
            json.dumps({"input_id": input_id, "values": [1.0]}) + "\n",
            encoding="utf-8",
        )
        source_sha256 = _sha256(source)
        binding.write_text(
            json.dumps(
                {
                    "schema_id": EXTERNAL_INPUT_BINDING_SCHEMAS[input_id],
                    "normalized_values": [1.0],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        report.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "input_id": input_id,
                    "source_sha256": source_sha256,
                    "status": "PASS",
                    "validated_by": "independent test validator",
                    "validation_method": "schema and semantic fixture checks",
                    "binding_artifact": {
                        "path": binding.name,
                        "sha256": _sha256(binding),
                        "schema_id": EXTERNAL_INPUT_BINDING_SCHEMAS[input_id],
                    },
                    "checks": [
                        {
                            "id": "TEST-CHECK-001",
                            "status": "PASS",
                            "detail": "fixture is complete",
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return {
            "source_path": source.name,
            "source_sha256": source_sha256,
            "provenance_status": "SIA_SUPPLIED",
            "normative_authorization_status": "CONFIRMED",
            "source_authority": "SIA",
            "license_reference": "documented-test-license",
            "dataset_identity": input_id,
            "machine_readable_format": "JSON",
            "semantic_scope": ["complete delegated input"],
            "technical_validation": {
                "status": "PASS",
                "report_path": report.name,
                "report_sha256": _sha256(report),
            },
        }

    def test_exact_requirement_mapping_covers_each_test_family(self):
        self.assertEqual(required_external_input_ids("test_1", "600"), ())
        self.assertEqual(len(required_external_input_ids("test_1", "1E")), 3)
        self.assertEqual(len(required_external_input_ids("test_2A", "2A")), 3)
        self.assertIn(
            "sia3874_2017_table9_controls",
            required_external_input_ids("test_2D", "2D"),
        )
        self.assertIn(
            "sia_authority_test3_3k_3l_device_clarification",
            required_external_input_ids("test_3K", "3K"),
        )
        self.assertIn(
            "sia_example_building_fabric_awning_detail",
            required_external_input_ids("test_3A", "3A"),
        )
        self.assertNotIn(
            "sia_authority_test3_3k_3l_device_clarification",
            required_external_input_ids("test_3J", "3J"),
        )
        for variant, case_id, expected_count in (
            ("test_4", "4", 3),
            ("test_5A", "5A", 4),
            ("test_6", "6", 4),
            ("test_7", "7", 3),
        ):
            with self.subTest(variant=variant):
                self.assertEqual(
                    len(required_external_input_ids(variant, case_id)),
                    expected_count,
                )

    def test_invalid_exact_variant_case_pair_is_rejected(self):
        with self.assertRaisesRegex(
            ConfigurationError, "Unknown SIA 4010 variant/case combination"
        ):
            required_external_input_ids("test_2A", "2D")

    def test_case_without_delegated_inputs_is_not_blocked_by_manifest(self):
        readiness = external_input_readiness(
            self.project, "test_1", "600"
        )
        self.assertEqual(readiness.status, "NOT_REQUIRED")
        self.assertTrue(readiness.ready_for_binding)
        self.assertEqual(readiness.required_input_ids, ())

    def test_missing_manifest_lists_every_required_input(self):
        readiness = external_input_readiness(
            self.project, "test_2A", "2A"
        )
        self.assertEqual(readiness.status, "MISSING_MANIFEST")
        self.assertFalse(readiness.ready_for_binding)
        self.assertEqual(
            readiness.blocked_input_ids, readiness.required_input_ids
        )
        self.assertTrue(
            all(item.status == "MISSING" for item in readiness.evidence)
        )

    def test_matrix_accounts_for_all_34_exact_cases(self):
        """34 since the registration of diagnostic cases 1A through 1D of Test 1.

        They are not without delegated input: 1A and 1B require the ISO cell
        and the Zurich-Kloten climate, 1C and 1D additionally require SIA 2024,
        from which 1C's adjusted infiltration is drawn.
        """
        matrix = build_external_input_matrix(self.project)
        self.assertEqual(matrix["exact_case_count"], 34)
        self.assertEqual(
            matrix["catalog_input_count"], len(EXTERNAL_INPUT_CATALOG)
        )
        # NOT_REQUIRED stays exactly 6: the six ISO cases of Test 1, which
        # run on the supplied DRYCOLD weather. That this count did not change
        # after adding 1A through 1D proves the four new cases properly received
        # their requirements, rather than silently falling into "nothing to
        # supply" -- which would have been the discreet way to be wrong.
        self.assertEqual(matrix["status_counts"]["NOT_REQUIRED"], 6)
        self.assertEqual(matrix["status_counts"]["MISSING_MANIFEST"], 28)
        weather = next(
            item
            for item in matrix["inputs"]
            if item["input_id"] == "sia2028_dry_normal_zurich_kloten"
        )
        # 28 not 24: the Zurich-Kloten climate is exactly what
        # link 1A adds to case 600, so all four diagnostic cases
        # depend on it.
        self.assertEqual(len(weather["affected_cases"]), 28)

    def test_example_manifest_has_exact_catalog_and_stays_blocked(self):
        example = Sia4010ExternalInputManifest.load(
            ROOT / "config" / "sia4010_external_inputs.example.json"
        )
        self.assertEqual(set(example.entries), set(EXTERNAL_INPUT_CATALOG))
        readiness = example.readiness("test_2A", "2A")
        self.assertEqual(readiness.status, "BLOCKED")
        self.assertFalse(readiness.ready_for_binding)

    def test_complete_authorized_checksum_evidence_is_ready(self):
        input_ids = required_external_input_ids("test_2A", "2A")
        path = self._write_manifest(
            {
                input_id: self._ready_entry(input_id)
                for input_id in input_ids
            }
        )
        readiness = external_input_readiness(
            self.project,
            "test_2A",
            "2A",
            manifest=Sia4010ExternalInputManifest.load(path),
        )
        self.assertEqual(readiness.status, "READY_FOR_BINDING")
        self.assertTrue(readiness.ready_for_binding)
        self.assertEqual(readiness.ready_input_ids, input_ids)
        self.assertEqual(readiness.blocked_input_ids, ())
        self.assertTrue(
            all(
                item.binding_artifact_path is not None
                for item in readiness.evidence
            )
        )

    def test_unconfirmed_authorization_remains_blocked(self):
        input_id = "iso52016_2017_chapter7_test_cell"
        entry = self._ready_entry(input_id)
        entry["normative_authorization_status"] = "UNCONFIRMED"
        manifest = Sia4010ExternalInputManifest.load(
            self._write_manifest({input_id: entry})
        )
        evidence = manifest.evidence(input_id)
        self.assertEqual(evidence.status, "BLOCKED")
        self.assertIn(
            "normative authorization is unconfirmed", evidence.issues
        )

    def test_source_checksum_tampering_is_rejected(self):
        input_id = "iso52016_2017_chapter7_test_cell"
        entry = self._ready_entry(input_id)
        path = self._write_manifest({input_id: entry})
        (self.project / "{}.json".format(input_id)).write_text(
            '{"tampered": true}\n', encoding="utf-8"
        )
        manifest = Sia4010ExternalInputManifest.load(path)
        with self.assertRaisesRegex(ConfigurationError, "source checksum"):
            manifest.evidence(input_id)

    def test_validation_report_checksum_tampering_is_rejected(self):
        input_id = "iso52016_2017_chapter7_test_cell"
        entry = self._ready_entry(input_id)
        path = self._write_manifest({input_id: entry})
        (
            self.project / "{}_validation.json".format(input_id)
        ).write_text('{"status": "FAIL"}\n', encoding="utf-8")
        manifest = Sia4010ExternalInputManifest.load(path)
        with self.assertRaisesRegex(
            ConfigurationError, "validation-report checksum"
        ):
            manifest.evidence(input_id)

    def test_validation_report_must_bind_exact_source_and_checks(self):
        input_id = "iso52016_2017_chapter7_test_cell"
        entry = self._ready_entry(input_id)
        report_path = (
            self.project / "{}_validation.json".format(input_id)
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["source_sha256"] = "0" * 64
        report_path.write_text(
            json.dumps(report) + "\n", encoding="utf-8"
        )
        entry["technical_validation"]["report_sha256"] = _sha256(report_path)
        manifest = Sia4010ExternalInputManifest.load(
            self._write_manifest({input_id: entry})
        )
        with self.assertRaisesRegex(ConfigurationError, "exact source SHA-256"):
            manifest.evidence(input_id)

        report["source_sha256"] = entry["source_sha256"]
        report["checks"] = []
        report_path.write_text(
            json.dumps(report) + "\n", encoding="utf-8"
        )
        entry["technical_validation"]["report_sha256"] = _sha256(report_path)
        manifest = Sia4010ExternalInputManifest.load(
            self._write_manifest({input_id: entry})
        )
        with self.assertRaisesRegex(ConfigurationError, "non-empty checks"):
            manifest.evidence(input_id)

    def test_binding_artifact_schema_and_checksum_are_enforced(self):
        input_id = "iso52016_2017_chapter7_test_cell"
        entry = self._ready_entry(input_id)
        report_path = (
            self.project / "{}_validation.json".format(input_id)
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["binding_artifact"]["schema_id"] = "wrong.schema"
        report_path.write_text(
            json.dumps(report) + "\n", encoding="utf-8"
        )
        entry["technical_validation"]["report_sha256"] = _sha256(report_path)
        manifest = Sia4010ExternalInputManifest.load(
            self._write_manifest({input_id: entry})
        )
        with self.assertRaisesRegex(ConfigurationError, "requires binding schema"):
            manifest.evidence(input_id)

        report["binding_artifact"]["schema_id"] = (
            EXTERNAL_INPUT_BINDING_SCHEMAS[input_id]
        )
        report["binding_artifact"]["sha256"] = "0" * 64
        report_path.write_text(
            json.dumps(report) + "\n", encoding="utf-8"
        )
        entry["technical_validation"]["report_sha256"] = _sha256(report_path)
        manifest = Sia4010ExternalInputManifest.load(
            self._write_manifest({input_id: entry})
        )
        with self.assertRaisesRegex(
            ConfigurationError, "binding artifact checksum"
        ):
            manifest.evidence(input_id)

    def test_unknown_input_and_schema_are_rejected(self):
        with self.assertRaisesRegex(ConfigurationError, "Unknown"):
            Sia4010ExternalInputManifest.load(
                self._write_manifest({"misspelled": {}})
            )
        with self.assertRaisesRegex(ConfigurationError, "Unsupported"):
            Sia4010ExternalInputManifest.load(
                self._write_manifest({}, schema_version="99")
            )

    def test_cached_manifest_must_belong_to_active_project(self):
        input_ids = required_external_input_ids("test_2A", "2A")
        manifest = Sia4010ExternalInputManifest.load(
            self._write_manifest(
                {
                    input_id: self._ready_entry(input_id)
                    for input_id in input_ids
                }
            )
        )
        other_project = self.project / "other"
        other_project.mkdir()
        with self.assertRaisesRegex(ConfigurationError, "active project"):
            external_input_readiness(
                other_project,
                "test_2A",
                "2A",
                manifest=manifest,
            )


if __name__ == "__main__":
    unittest.main()
