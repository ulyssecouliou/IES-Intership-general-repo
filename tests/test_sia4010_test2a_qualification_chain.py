"""Tests for the fail-closed Test 2A one-click qualification chain."""

import json
import hashlib
import shutil
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from swiss_sia.reference_model.sia4010.model_scenario import (
    ModelScenario,
    ScenarioFiles,
    official_features,
)
from swiss_sia.reference_model.sia4010.test2a_qualification_chain import (
    FINAL_STATUS,
    MUTATION_SCOPE,
    READY_STATUS,
    Test2AQualificationBlocked,
    _report_evidence,
    run_test2a_qualification_chain,
)

ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / ".codex_tmp" / "t2a_chain"
SCENARIO_FILENAME = "sia_model_scenario.json"


class Test2AQualificationChainTests(unittest.TestCase):
    """Only verified narrow probe reports may advance the chain."""

    def setUp(self):
        short_name = hashlib.sha256(self._testMethodName.encode("utf-8")).hexdigest()[:10]
        self.project_path = WORK_ROOT / short_name
        if self.project_path.exists():
            shutil.rmtree(self.project_path)
        self.project_path.mkdir(parents=True)
        self.project = SimpleNamespace(
            name="SIA4010_TEST2A_DISPOSABLE",
            path=str(self.project_path),
        )
        self.calls = []

    def tearDown(self):
        if self.project_path.exists():
            shutil.rmtree(self.project_path)

    def _write_report(self, name, status, scope="", claim=False, **extra):
        path = self.project_path / "reports" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "status": status,
            "compliance_claim_allowed": claim,
        }
        if scope:
            payload["mutation_scope"] = scope
        payload.update(extra)
        path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        path.with_suffix(path.suffix + ".sha256").write_text(
            "{}  {}\n".format(digest, path.name),
            encoding="ascii",
        )
        return path

    def _prepare(self):
        self.calls.append("prepare")
        scenario = ModelScenario(
            scenario_id="test2a_chain",
            profile="SIA4010_OFFICIAL",
            target_class="1A",
            variant="test_2A",
            case_id="2A",
            features=official_features("test_2A", "2A"),
            files=ScenarioFiles("case.json", "config.json", "assets.json"),
            execution_mode="PREPARE_ONLY",
        )
        (self.project_path / SCENARIO_FILENAME).write_text(
            json.dumps(scenario.to_dict()) + "\n",
            encoding="utf-8",
        )
        return 0

    def _runtime(self, status=READY_STATUS):
        self.calls.append("runtime")
        return self._write_report("runtime.json", status)

    def _profiles(self):
        self.calls.append("profiles")
        return self._write_report("profiles.json", "PASS", "PROJECT_PROFILES_ONLY")

    def _shading(self):
        self.calls.append("shading")
        return self._write_report(
            "shading.json",
            "PASS",
            "ONE_UNASSIGNED_GLAZED_CDB_CONSTRUCTION",
        )

    def _optical(self):
        self.calls.append("optical")
        report = self._write_report(
            "optical.json",
            "PASS",
            "ONE_UNASSIGNED_GLAZED_CDB_CONSTRUCTION",
        )
        audit = self.project_path / "reports" / "bundle.json"
        audit.write_text(
            json.dumps(
                {
                    "status": "RUNTIME_STORAGE_QUALIFIED_MODEL_BINDING_REQUIRED",
                    "mutation_supported": False,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        digest = hashlib.sha256(audit.read_bytes()).hexdigest()
        audit.with_suffix(audit.suffix + ".sha256").write_text(
            "{}  {}\n".format(digest, audit.name),
            encoding="ascii",
        )
        return {
            "report_path": str(report),
            "bundle_status": "RUNTIME_STORAGE_QUALIFIED_MODEL_BINDING_REQUIRED",
            "bundle_audit_path": str(audit),
            "mutation_supported": False,
        }

    def _assignment(self):
        self.calls.append("assignment")
        path = self.project_path / "reports" / "assignment.json"
        path.write_text(
            json.dumps(
                {
                    "status": "PASS",
                    "compliance_claim_allowed": False,
                    "mutation_scope": (
                        "ONE_OPENING_TRANSIENT_ASSIGNMENT_WITH_VERIFIED_" "RESTORATION"
                    ),
                    "candidate_assignment_readback_verified": True,
                    "original_assignment_restored": True,
                    "opening_assignment_persisted": False,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        path.with_suffix(path.suffix + ".sha256").write_text(
            "{}  {}\n".format(digest, path.name), encoding="ascii"
        )
        return path

    def _thermal(self):
        self.calls.append("thermal")
        path = self.project_path / "reports" / "thermal.json"
        path.write_text(
            json.dumps(
                {
                    "status": "PASS",
                    "compliance_claim_allowed": False,
                    "mutation_scope": ("ONE_UNASSIGNED_GLAZED_CDB_LAYER_RESISTANCE"),
                    "base_glazing_thermal_storage_qualified": True,
                    "manufacturer_layer_build_up_qualified": False,
                    "combined_glazing_awning_u_qualified": False,
                    "calibration_result": {
                        "absolute_difference_w_m2k": 0.0002,
                        "qa_tolerance_w_m2k": 0.001,
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        path.with_suffix(path.suffix + ".sha256").write_text(
            "{}  {}\n".format(digest, path.name), encoding="ascii"
        )
        return path

    def test_complete_chain_preserves_fail_closed_terminal_claim(self):
        receipt = run_test2a_qualification_chain(
            self.project,
            self._prepare,
            self._runtime,
            self._profiles,
            self._shading,
            self._optical,
            self._thermal,
            self._assignment,
        )
        self.assertEqual(receipt.status, FINAL_STATUS)
        self.assertFalse(receipt.mutation_supported)
        self.assertFalse(receipt.compliance_claim_allowed)
        self.assertEqual(
            self.calls,
            [
                "prepare",
                "runtime",
                "profiles",
                "shading",
                "optical",
                "thermal",
                "assignment",
            ],
        )
        audit = json.loads(receipt.report_path.read_text(encoding="utf-8"))
        self.assertEqual(audit["status"], FINAL_STATUS)
        self.assertEqual(audit["mutation_scope"], MUTATION_SCOPE)
        self.assertFalse(audit["model_generated"])
        self.assertFalse(audit["simulation_performed"])
        self.assertTrue(audit["opening_assignment_performed"])
        self.assertTrue(audit["opening_assignment_restored"])
        self.assertEqual(len(audit["stages"]), 7)

    def test_runtime_not_ready_blocks_before_first_mutation(self):
        profiles = mock.Mock(side_effect=AssertionError("must not mutate"))
        with self.assertRaisesRegex(
            Test2AQualificationBlocked,
            "expected.*READY_FOR_DISPOSABLE",
        ):
            run_test2a_qualification_chain(
                self.project,
                self._prepare,
                lambda: self._runtime("READ_ONLY_EVIDENCE_INCOMPLETE"),
                profiles,
                self._shading,
                self._optical,
                self._thermal,
                self._assignment,
            )
        profiles.assert_not_called()
        reports = list(
            (self.project_path / "sia4010_artifacts" / "diagnostics").glob(
                "sia4010_test2a_qualification_chain_*.json"
            )
        )
        self.assertEqual(len(reports), 1)
        audit = json.loads(reports[0].read_text(encoding="utf-8"))
        self.assertEqual(audit["status"], "BLOCKED")
        self.assertFalse(audit["mutation_boundary_entered"])

    def test_stage_report_cannot_authorize_compliance_claim(self):
        report = self._write_report("unsafe.json", "PASS", claim=True)
        with self.assertRaisesRegex(
            Test2AQualificationBlocked,
            "incorrectly authorizes",
        ):
            _report_evidence(
                report,
                label="unsafe stage",
                expected_status="PASS",
            )

    def test_status_failure_exposes_all_runtime_blockers_and_next_action(self):
        report = self._write_report(
            "blocked.json",
            "NATIVE_PROFILE_GRAPH_REQUIRED",
            technical_blockers=[
                "NO_OPENING_PROXY_AVAILABLE_FOR_READBACK",
                "SIA2024_NATIVE_VE_PROFILE_GRAPH_NOT_SUPPLIED",
            ],
            next_action="Import the prepared geometry and bind the calendar.",
        )
        with self.assertRaises(Test2AQualificationBlocked) as captured:
            _report_evidence(
                report,
                label="read_only_runtime_capability",
                expected_status=READY_STATUS,
            )
        message = str(captured.exception)
        self.assertIn("NO_OPENING_PROXY_AVAILABLE_FOR_READBACK", message)
        self.assertIn("SIA2024_NATIVE_VE_PROFILE_GRAPH_NOT_SUPPLIED", message)
        self.assertIn("Import the prepared geometry", message)

    def test_second_chain_in_same_project_is_rejected(self):
        run_test2a_qualification_chain(
            self.project,
            self._prepare,
            self._runtime,
            self._profiles,
            self._shading,
            self._optical,
            self._thermal,
            self._assignment,
        )
        with self.assertRaisesRegex(
            Test2AQualificationBlocked,
            "fresh disposable copy",
        ):
            run_test2a_qualification_chain(
                self.project,
                self._prepare,
                self._runtime,
                self._profiles,
                self._shading,
                self._optical,
                self._thermal,
                self._assignment,
            )


if __name__ == "__main__":
    unittest.main()
