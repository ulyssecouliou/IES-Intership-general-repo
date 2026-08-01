"""Cross-project SIA 4010 evidence-ledger tests."""

import json
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from swiss_sia.reference_model.sia4010.apachesim_qualification import (
    ApacheSimQualificationReceipt,
    TEST1_SIMULATION_SOURCE,
)
from swiss_sia.reference_model.sia4010.evidence_registry import (
    _artifact_is_valid,
    _sha256,
    _simulation_evidence_is_valid,
    _variant_model_status,
    _variant_result_record,
    load_registry,
    new_registry_payload,
    register_case_evaluation,
    register_case_simulation,
    register_model_outcome,
)
from swiss_sia.reference_model.sia4010.model_scenario import (
    ModelScenario,
    TEST_CASES,
    official_features,
)


EVIDENCE = Path(__file__).resolve()
ROOT = EVIDENCE.parents[1]
TEMP_ROOT = ROOT / ".codex_tmp"


class Sia4010EvidenceRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.payload = new_registry_payload()
        self.cases = self.payload["cases"]
        self.test_root = (
            TEMP_ROOT / "evidence_registry" / self._testMethodName
        )
        self.test_root.mkdir(parents=True, exist_ok=True)

    def test_empty_ledger_contains_every_exact_case_and_no_claim(self):
        self.assertEqual(len(self.cases), 30)
        self.assertTrue(
            all(
                record["model_evidence"]["status"] == "MISSING"
                for record in self.cases.values()
            )
        )
        self.assertTrue(
            all(
                record["simulation_evidence"]["status"] == "NOT_RUN"
                for record in self.cases.values()
            )
        )
        self.assertTrue(
            all(
                record["result_evidence"]["status"] == "NOT_CHECKABLE"
                for record in self.cases.values()
            )
        )

    def test_variant_model_gate_requires_every_exact_case(self):
        digest = _sha256(EVIDENCE)
        first = TEST_CASES["test_1"][0]
        self.cases["test_1/{}".format(first)]["model_evidence"] = {
            "status": "VERIFIED",
            "artifact_path": str(EVIDENCE),
            "artifact_sha256": digest,
        }
        self.assertEqual(
            _variant_model_status(self.cases, "test_1"), "BLOCKED"
        )
        for case_id in TEST_CASES["test_1"]:
            self.cases["test_1/{}".format(case_id)]["model_evidence"] = {
                "status": "VERIFIED",
                "artifact_path": str(EVIDENCE),
                "artifact_sha256": digest,
            }
        self.assertEqual(_variant_model_status(self.cases, "test_1"), "PASS")

    def test_test1_result_gate_uses_the_official_1e_result(self):
        digest = _sha256(EVIDENCE)
        record = self.cases["test_1/1E"]
        record["simulation_evidence"] = {
            "status": "SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION",
            "artifact_path": str(EVIDENCE),
            "artifact_sha256": digest,
            "scenario_path": str(EVIDENCE),
            "scenario_sha256": digest,
            "model_report_path": str(EVIDENCE),
            "model_report_sha256": digest,
            "results_path": str(EVIDENCE),
            "results_sha256": digest,
            "results_size_bytes": EVIDENCE.stat().st_size,
            "aps_evaluation_required": True,
            "compliance_claim_allowed": False,
        }
        record["result_evidence"] = {
            "status": "OFFICIAL_RESULTS_RECORDED",
            "artifact_path": str(EVIDENCE),
            "artifact_sha256": digest,
            "aps_path": str(EVIDENCE),
            "aps_sha256": digest,
            "simulation_link_status": "VERIFIED",
        }
        result = _variant_result_record(self.cases, "test_1")
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "OFFICIAL_RESULTS_RECORDED")

    def test_result_gate_rejects_unlinked_aps_evidence(self):
        digest = _sha256(EVIDENCE)
        self.cases["test_1/1E"]["result_evidence"] = {
            "status": "OFFICIAL_RESULTS_RECORDED",
            "artifact_path": str(EVIDENCE),
            "artifact_sha256": digest,
            "aps_path": str(EVIDENCE),
            "aps_sha256": digest,
            "simulation_link_status": "NOT_LINKED",
        }
        self.assertIsNone(_variant_result_record(self.cases, "test_1"))

    def test_checksum_mismatch_invalidates_evidence(self):
        evidence = {
            "artifact_path": str(EVIDENCE),
            "artifact_sha256": "0" * 64,
        }
        self.assertFalse(_artifact_is_valid(evidence))

    def test_v1_registry_is_migrated_without_erasing_evidence(self):
        path = self.test_root / "registry.json"
        payload = new_registry_payload()
        payload["schema_version"] = "1.0"
        for record in payload["cases"].values():
            record.pop("simulation_evidence")
            record["result_evidence"].pop("aps_path")
            record["result_evidence"].pop("aps_sha256")
            record["result_evidence"].pop("simulation_link_status")
        payload["cases"]["test_1/600"]["model_evidence"]["status"] = (
            "VERIFIED"
        )
        path.write_text(json.dumps(payload), encoding="utf-8")

        migrated = load_registry(path)

        self.assertEqual(migrated["schema_version"], "1.1")
        self.assertEqual(migrated["migrated_from_schema_version"], "1.0")
        self.assertEqual(
            migrated["cases"]["test_1/600"]["model_evidence"]["status"],
            "VERIFIED",
        )
        self.assertEqual(
            migrated["cases"]["test_1/600"]["simulation_evidence"]["status"],
            "NOT_RUN",
        )

    def test_next_registration_persists_v1_to_v11_migration(self):
        registry = self.test_root / "registry.json"
        legacy = new_registry_payload()
        legacy["schema_version"] = "1.0"
        for record in legacy["cases"].values():
            record.pop("simulation_evidence")
            record["result_evidence"].pop("aps_path")
            record["result_evidence"].pop("aps_sha256")
            record["result_evidence"].pop("simulation_link_status")
        legacy["cases"]["test_2A/2A"]["model_evidence"]["status"] = "FAILED"
        registry.write_text(json.dumps(legacy), encoding="utf-8")

        self._create_registered_simulation(self.test_root)

        persisted = json.loads(registry.read_text(encoding="utf-8"))
        self.assertEqual(persisted["schema_version"], "1.1")
        self.assertEqual(
            persisted["cases"]["test_2A/2A"]["model_evidence"]["status"],
            "FAILED",
        )
        self.assertEqual(
            persisted["cases"]["test_1/600"]["simulation_evidence"]["status"],
            "SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION",
        )

    def _create_registered_simulation(self, root):
        project = Path(root) / "project"
        project.mkdir(parents=True, exist_ok=True)
        registry = Path(root) / "registry.json"
        scenario_path = project / "sia_model_scenario.json"
        scenario_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "scenario_id": "TEST_600",
                    "profile": "SIA4010_OFFICIAL",
                    "selection": {
                        "target_class": "1A",
                        "variant": "test_1",
                        "case_id": "600",
                    },
                    "features": official_features("test_1", "600"),
                    "files": {
                        "case_manifest_file": "case.json",
                        "ve_config_file": "config.json",
                        "ve_asset_manifest_file": "assets.json",
                    },
                    "execution": {"mode": "CREATE_IN_ACTIVE_VE_PROJECT"},
                }
            ),
            encoding="utf-8",
        )
        scenario = ModelScenario.load(scenario_path)
        model_report = project / "reference_model_report.json"
        model_report.write_text(
            json.dumps({"overall_status": "PASS"}), encoding="utf-8"
        )
        aps = project / "SIA4010_test_1_600.aps"
        aps.write_bytes(b"qualified APS evidence")
        audit = project / "simulation.json"
        requested_options = {
            "start_day": 1,
            "start_month": 1,
            "end_day": 31,
            "end_month": 12,
            "reporting_interval": 3,
            "results_filename": aps.name,
        }
        receipt = ApacheSimQualificationReceipt(
            status="SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION",
            variant="test_1",
            case_id="600",
            project_path=str(project),
            model_report_path=str(model_report),
            model_report_sha256=_sha256(model_report),
            scenario_path=str(scenario_path),
            scenario_sha256=_sha256(scenario_path),
            requested_options=requested_options,
            options_before={"simulation_timestep": 2},
            options_after={
                "simulation_timestep": 2,
                **requested_options,
            },
            results_path=str(aps),
            results_sha256=_sha256(aps),
            results_size_bytes=aps.stat().st_size,
            audit_path=str(audit),
        )
        audit_payload = receipt.to_dict()
        audit_payload.update(
            {
                "source": TEST1_SIMULATION_SOURCE,
                "source_file": {
                    "path": str(EVIDENCE),
                    "sha256": _sha256(EVIDENCE),
                },
                "confirmed_contract": {
                    "simulation_period": (
                        "2011-01-01 through 2011-12-31"
                    ),
                    "required_result_frequency": "hourly",
                    "requested_apachesim_options": requested_options,
                },
            }
        )
        audit.write_text(json.dumps(audit_payload), encoding="utf-8")
        register_model_outcome(
            registry,
            scenario,
            workflow_status="PASS",
            report_path=model_report,
            project_path=project,
        )
        payload = register_case_simulation(
            registry,
            receipt,
            project_path=project,
        )
        return project, registry, receipt, payload

    def test_register_case_simulation_records_complete_verified_chain(self):
        _project, _registry, _receipt, payload = (
            self._create_registered_simulation(self.test_root)
        )
        evidence = payload["cases"]["test_1/600"]["simulation_evidence"]
        self.assertEqual(evidence["model_evidence_link_status"], "VERIFIED")
        self.assertTrue(_simulation_evidence_is_valid(evidence))

    def test_register_case_simulation_rejects_tampered_aps(self):
        project, registry, receipt, _payload = (
            self._create_registered_simulation(self.test_root)
        )
        Path(receipt.results_path).write_bytes(b"tampered")
        with self.assertRaisesRegex(
            Exception, "ApacheSim APS checksum mismatch"
        ):
            register_case_simulation(
                registry,
                receipt,
                project_path=project,
            )

    def test_register_case_simulation_rejects_wrong_temporal_contract(self):
        project, registry, receipt, _payload = (
            self._create_registered_simulation(self.test_root)
        )
        bad_options = dict(receipt.requested_options)
        bad_options["start_day"] = 2
        altered = replace(receipt, requested_options=bad_options)
        with self.assertRaisesRegex(
            Exception, "receipt option start_day mismatch"
        ):
            register_case_simulation(
                registry,
                altered,
                project_path=project,
            )

    def test_register_case_simulation_rejects_untraced_source(self):
        project, registry, receipt, _payload = (
            self._create_registered_simulation(self.test_root)
        )
        audit_path = Path(receipt.audit_path)
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        audit["source"] = "unverified source"
        audit_path.write_text(json.dumps(audit), encoding="utf-8")
        with self.assertRaisesRegex(
            Exception, "does not cite the qualified Test 1 source"
        ):
            register_case_simulation(
                registry,
                receipt,
                project_path=project,
            )

    def test_register_case_evaluation_records_checksummed_artifact(self):
        project, registry, simulation, _payload = (
            self._create_registered_simulation(self.test_root)
        )
        artifact = self.test_root / "evaluation.json"
        artifact.write_text(
            json.dumps(
                {
                    "variant": "test_1",
                    "case_id": "600",
                    "status": (
                        "REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION"
                    ),
                    "source_evidence": {
                        "aps_path": simulation.results_path,
                        "aps_sha256": simulation.results_sha256,
                    }
                }
            ),
            encoding="utf-8",
        )
        receipt = SimpleNamespace(
            variant="test_1",
            case_id="600",
            status="REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION",
            artifact_path=artifact,
            observed_metric_count=88,
            distribution_criterion_count=0,
        )
        with mock.patch(
            "swiss_sia.reference_model.sia4010.evidence_registry._write_json"
        ) as writer:
            payload = register_case_evaluation(
                registry,
                receipt,
                project_path=project,
            )
        artifact_digest = _sha256(artifact)
        evidence = payload["cases"]["test_1/600"]["result_evidence"]
        self.assertEqual(
            evidence["status"],
            "REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION",
        )
        self.assertEqual(evidence["artifact_sha256"], artifact_digest)
        self.assertEqual(evidence["simulation_link_status"], "VERIFIED")
        writer.assert_called_once()

    def test_register_case_evaluation_marks_foreign_aps_unlinked(self):
        project, registry, _simulation, _payload = (
            self._create_registered_simulation(self.test_root)
        )
        foreign_aps = self.test_root / "foreign.aps"
        foreign_aps.write_bytes(b"other APS")
        artifact = self.test_root / "evaluation.json"
        artifact.write_text(
            json.dumps(
                {
                    "variant": "test_1",
                    "case_id": "600",
                    "status": (
                        "REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION"
                    ),
                    "source_evidence": {
                        "aps_path": str(foreign_aps),
                        "aps_sha256": _sha256(foreign_aps),
                    }
                }
            ),
            encoding="utf-8",
        )
        receipt = SimpleNamespace(
            variant="test_1",
            case_id="600",
            status="REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION",
            artifact_path=artifact,
            observed_metric_count=88,
            distribution_criterion_count=0,
        )
        payload = register_case_evaluation(
            registry,
            receipt,
            project_path=project,
        )
        evidence = payload["cases"]["test_1/600"]["result_evidence"]
        self.assertEqual(evidence["simulation_link_status"], "NOT_LINKED")


if __name__ == "__main__":
    unittest.main()
