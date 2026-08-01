"""Fail-closed tests for one-click ApacheSim runtime qualification."""

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from swiss_sia.reference_model.sia4010.apachesim_qualification import (
    ApacheSimQualificationError,
    run_qualified_apachesim,
)
from swiss_sia.reference_model.sia4010.native_ui import ModelBuilderController


ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = ROOT / ".codex_tmp"


class _Project:
    """Minimal saved VE project identity."""

    def __init__(self, path):
        self.path = str(path)
        self.name = Path(path).name


class _FakeApacheSim:
    """Deterministic synchronous ApacheSim stand-in."""

    def __init__(self, project_path, *, mismatch=False, run_result=True):
        self.project_path = Path(project_path)
        self.options = {
            "simulation_timestep": 2,
            "preconditioning_days": 14,
            "reporting_interval": 1,
        }
        self.mismatch = mismatch
        self.run_result = run_result

    def get_options(self):
        options = dict(self.options)
        if self.mismatch and "reporting_interval" in options:
            options["reporting_interval"] = 2
        return options

    def set_options(self, options):
        self.options.update(options)
        return True

    def run_simulation(self, queue_to_tasks=False):
        if self.run_result:
            vista = self.project_path / "Vista"
            vista.mkdir(parents=True, exist_ok=True)
            (vista / self.options["results_filename"]).write_bytes(
                b"qualified fake APS"
            )
        return self.run_result


class ApacheSimQualificationTests(unittest.TestCase):
    """Only source-confirmed temporal options may reach ApacheSim."""

    def setUp(self):
        self.project = TEMP_ROOT / self._testMethodName
        self.project.mkdir(parents=True, exist_ok=True)
        prior_result = (
            self.project
            / "Vista"
            / "SIA4010_test_1_600_20260729_020304.aps"
        )
        if prior_result.is_file():
            prior_result.unlink()
        self._write_scenario("600")
        self._write_model_report("600")

    def _write_scenario(self, case_id):
        payload = ModelBuilderController().build_payload(
            "SIA4010_1A_{}".format(case_id),
            "SIA4010_OFFICIAL",
            "1A",
            "test_1",
            case_id,
            (
                "CREATE_IN_ACTIVE_VE_PROJECT"
                if case_id == "600"
                else "QUALIFY_IN_ACTIVE_VE_PROJECT"
            ),
            "sia4010_case_manifest.json",
            "reference_model_config.json",
            "reference_model_assets.json",
        )
        (self.project / "sia_model_scenario.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    def _write_model_report(self, case_id, *, overall="WARNING"):
        path = (
            self.project
            / "reference_model_artifacts"
            / "reports"
            / "reference_model_report.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "overall_status": overall,
                    "run_metadata": {"mode": "VE_MUTATION"},
                    "validation_results": [
                        {
                            "control_id": "VE-WEA-001",
                            "status": "PASS",
                        }
                    ],
                    "additional_data": {
                        "asset_manifest": {
                            "metadata": {
                                "sia4010_variant": "test_1",
                                "sia4010_case_id": case_id,
                            }
                        }
                    },
                    "ve_model_snapshot": {
                        "spaces": [{"identifier": "SIA4010_TEST_1_ZONE"}]
                    },
                }
            ),
            encoding="utf-8",
        )

    def _run(self, factory):
        return run_qualified_apachesim(
            project=_Project(self.project),
            apachesim_factory=factory,
            repository_root=ROOT,
            now=datetime(2026, 7, 29, 2, 3, 4, tzinfo=timezone.utc),
            file_wait_seconds=0.0,
        )

    def test_sets_only_confirmed_annual_hourly_options_and_writes_evidence(self):
        sim = _FakeApacheSim(self.project)
        receipt = self._run(lambda: sim)
        self.assertEqual(
            receipt.status,
            "SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION",
        )
        self.assertEqual(
            receipt.requested_options,
            {
                "start_day": 1,
                "start_month": 1,
                "end_day": 31,
                "end_month": 12,
                "reporting_interval": 3,
                "results_filename": (
                    "SIA4010_test_1_600_20260729_020304.aps"
                ),
            },
        )
        self.assertEqual(receipt.options_after["simulation_timestep"], 2)
        self.assertEqual(receipt.options_after["preconditioning_days"], 14)
        self.assertGreater(receipt.results_size_bytes, 0)
        self.assertTrue(Path(receipt.results_path).is_file())
        audit = json.loads(Path(receipt.audit_path).read_text(encoding="utf-8"))
        self.assertFalse(audit["compliance_claim_allowed"])
        self.assertTrue(audit["aps_evaluation_required"])
        self.assertIn("simulation_timestep", audit["deliberately_unset_engine_options"])
        self.assertTrue(audit["source_file"]["sha256"])

    def test_rejects_model_report_for_another_case_before_calling_engine(self):
        self._write_model_report("640")
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "instead of test_1/600",
        ):
            self._run(lambda: self.fail("ApacheSim must not be constructed"))

    def test_rejects_failed_weather_validation(self):
        report_path = (
            self.project
            / "reference_model_artifacts"
            / "reports"
            / "reference_model_report.json"
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["validation_results"][0]["status"] = "FAIL"
        report_path.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "VE-WEA-001 must PASS",
        ):
            self._run(lambda: _FakeApacheSim(self.project))

    def test_option_readback_mismatch_fails_and_keeps_audit(self):
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "read-back mismatch",
        ):
            self._run(lambda: _FakeApacheSim(self.project, mismatch=True))
        audit_path = (
            self.project
            / "sia4010_artifacts"
            / "simulation"
            / "SIA4010_test_1_600_apachesim_qualification.json"
        )
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        self.assertEqual(audit["status"], "FAIL")
        self.assertFalse(audit["compliance_claim_allowed"])

    def test_run_failure_does_not_create_false_success(self):
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "did not return True",
        ):
            self._run(
                lambda: _FakeApacheSim(self.project, run_result=False)
            )

    def test_unsupported_case_1e_is_blocked(self):
        self._write_scenario("1E")
        self._write_model_report("1E")
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "unavailable for test_1/1E",
        ):
            self._run(lambda: _FakeApacheSim(self.project))


if __name__ == "__main__":
    unittest.main()
