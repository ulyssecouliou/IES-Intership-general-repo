"""Tests for the runnable-case Test 1 campaign state machine."""

import hashlib
import json
import shutil
import unittest
from pathlib import Path

from swiss_sia.reference_model.sia4010.test1_campaign import (
    TEST1_CAMPAIGN_CASES,
    TEST1_DIAGNOSTIC_CASES,
    TEST1_ISO_CASES,
    TEST1_JUDGED_CASES,
    build_test1_campaign_status,
)


class Test1CampaignTests(unittest.TestCase):
    def setUp(self):
        self.root = (
            Path(__file__).resolve().parents[1]
            / ".codex_tmp"
            / ("campaign_" + self._testMethodName)
        )
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir(parents=True)

    def tearDown(self):
        if self.root.exists():
            shutil.rmtree(self.root)

    def _artifact(self, name):
        path = self.root / name
        path.write_text(json.dumps({"name": name}) + "\n", encoding="utf-8")
        return str(path), hashlib.sha256(path.read_bytes()).hexdigest()

    def _current_simulation(self, suffix=""):
        evidence = {
            "status": "SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION",
            "model_evidence_link_status": "VERIFIED",
            "project_path": str(self.root),
        }
        for prefix in ("artifact", "results", "model_report", "scenario"):
            path, digest = self._artifact(prefix + suffix + ".json")
            evidence[prefix + "_path"] = path
            evidence[prefix + "_sha256"] = digest
        return evidence

    def test_next_case_follows_official_campaign_order(self):
        registry = {"cases": {}}
        report = build_test1_campaign_status(registry)
        self.assertEqual(report["next_case"]["case_id"], "600")
        self.assertTrue(report["next_case"]["next_action"]["requires_fresh_project"])
        self.assertEqual(
            report["next_case"]["next_action"]["script"],
            "Run_VE_SIA4010_Test1_Fast_Start.py",
        )
        self.assertEqual(report["case_count"], 11)
        self.assertEqual(report["reference_case_count"], 10)
        self.assertEqual(report["iso_case_count"], 6)
        self.assertEqual(report["iso_reference_results_complete_count"], 0)
        self.assertEqual(report["next_iso_case"]["case_id"], "600")
        self.assertEqual(report["diagnostic_case_count"], 4)
        self.assertEqual(report["diagnostic_deliverables_complete_count"], 0)
        self.assertEqual(report["next_diagnostic_case"]["case_id"], "1A")
        self.assertEqual(
            report["formal_test1_status"],
            "BLOCKED_DIAGNOSTIC_1E_VE_QUALIFICATION_REQUIRED",
        )
        self.assertEqual(report["judged_case"]["case_id"], "1E")
        self.assertEqual(
            report["next_case"]["next_action"]["script"],
            "Run_VE_SIA4010_Test1_Fast_Start.py",
        )

    def test_completed_600_advances_to_640(self):
        registry = {
            "cases": {
                "test_1/600": {
                    "case_id": "600",
                    "simulation_evidence": self._current_simulation("_600"),
                    "result_evidence": {
                        "status": "REFERENCE_RESULTS_RECORDED",
                        "required_output_scope_complete": True,
                        "simulation_link_status": "VERIFIED",
                        "observed_metric_count": 88,
                    },
                }
            }
        }
        report = build_test1_campaign_status(registry)
        self.assertEqual(report["reference_results_complete_count"], 1)
        self.assertEqual(report["iso_reference_results_complete_count"], 1)
        self.assertEqual(report["next_case"]["case_id"], "640")

    def test_existing_simulation_routes_to_existing_project_evaluation(self):
        simulation = self._current_simulation()
        registry = {
            "cases": {
                "test_1/600": {
                    "case_id": "600",
                    "simulation_evidence": simulation,
                    "result_evidence": {
                        "required_output_scope_complete": True,
                        "simulation_link_status": "NOT_LINKED",
                        "observed_metric_count": 88,
                    },
                }
            }
        }
        action = build_test1_campaign_status(registry)["next_case"]["next_action"]
        self.assertFalse(action["requires_fresh_project"])
        self.assertEqual(action["project_path"], str(self.root))
        self.assertEqual(action["script"], "Run_VE_SIA4010_Evaluate_Active_Case.py")

    def test_stale_simulation_routes_to_guarded_resimulation(self):
        simulation = self._current_simulation()
        Path(simulation["scenario_path"]).write_text(
            '{"changed": true}\n', encoding="utf-8"
        )
        registry = {
            "cases": {
                "test_1/600": {
                    "case_id": "600",
                    "simulation_evidence": simulation,
                    "result_evidence": {
                        "required_output_scope_complete": True,
                        "simulation_link_status": "NOT_LINKED",
                        "observed_metric_count": 88,
                    },
                }
            }
        }
        item = build_test1_campaign_status(registry)["next_case"]
        self.assertEqual(item["stage"], "REQUALIFY_SIMULATION_EVIDENCE")
        self.assertEqual(
            item["next_action"]["script"],
            "Run_VE_SIA4010_Simulate_Active_Case.py",
        )
        self.assertFalse(item["next_action"]["requires_fresh_project"])

    def test_known_floor_material_failure_routes_to_narrow_repair(self):
        simulation = self._current_simulation()
        model_report = Path(simulation["model_report_path"])
        model_report.write_text(
            json.dumps(
                {
                    "overall_status": "FAIL",
                    "validation_results": [
                        {
                            "status": "FAIL",
                            "message": (
                                "existing material xps_ground read-back mismatch: "
                                "density and specific_heat_capacity"
                            ),
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        registry = {
            "cases": {
                "test_1/600": {
                    "case_id": "600",
                    "simulation_evidence": simulation,
                }
            }
        }
        item = build_test1_campaign_status(registry)["next_case"]
        self.assertEqual(item["stage"], "RECONCILE_FLOOR_INSULATION")
        self.assertEqual(
            item["next_action"]["script"],
            "Run_VE_SIA4010_Test1_Reconcile_Floor_Insulation.py",
        )
        self.assertEqual(
            item["next_action"]["follow_up_script"],
            "Run_VE_SIA4010_Test1_Active_Case_One_Click.py",
        )

    def test_all_reference_cases_and_judged_case_complete(self):
        registry = {
            "cases": {
                "test_1/{}".format(case_id): {
                    "case_id": case_id,
                    "simulation_evidence": self._current_simulation(
                        "_{}".format(case_id)
                    ),
                    "result_evidence": {
                        "status": (
                            "OFFICIAL_RESULTS_RECORDED"
                            if case_id == "1E"
                            else "REFERENCE_RESULTS_RECORDED"
                        ),
                        "required_output_scope_complete": True,
                        "simulation_link_status": "VERIFIED",
                        "observed_metric_count": 39 if case_id.endswith("FF") else 88,
                    },
                }
                for case_id in TEST1_CAMPAIGN_CASES
            }
        }
        report = build_test1_campaign_status(registry)
        self.assertEqual(report["status"], "TEST1_REFERENCE_CAMPAIGN_COMPLETE")
        self.assertIsNone(report["next_case"])
        reference_rows = [item for item in report["cases"] if item["case_id"] != "1E"]
        self.assertTrue(
            all(
                item["formal_compliance_verdict"].startswith("NOT_AVAILABLE")
                for item in reference_rows
            )
        )
        self.assertEqual(
            report["judged_case"]["formal_compliance_verdict"],
            "OFFICIAL_RESULTS_RECORDED",
        )
        self.assertEqual(report["formal_test1_status"], "TEST1_JUDGED_RESULT_RECORDED")
        self.assertEqual(report["iso_status"], "TEST1_ISO_REFERENCE_CAMPAIGN_COMPLETE")
        self.assertEqual(
            report["diagnostic_status"],
            "TEST1_DIAGNOSTIC_DELIVERABLES_COMPLETE",
        )

    def test_iso_completion_is_reported_separately_from_diagnostics(self):
        registry = {
            "cases": {
                "test_1/{}".format(case_id): {
                    "case_id": case_id,
                    "simulation_evidence": self._current_simulation(
                        "_iso_{}".format(case_id)
                    ),
                    "result_evidence": {
                        "required_output_scope_complete": True,
                        "simulation_link_status": "VERIFIED",
                        "observed_metric_count": 39 if case_id.endswith("FF") else 88,
                    },
                }
                for case_id in TEST1_ISO_CASES
            }
        }
        report = build_test1_campaign_status(registry)
        self.assertEqual(report["iso_status"], "TEST1_ISO_REFERENCE_CAMPAIGN_COMPLETE")
        self.assertEqual(report["iso_reference_results_complete_count"], 6)
        self.assertIsNone(report["next_iso_case"])
        self.assertEqual(
            report["diagnostic_status"],
            "TEST1_DIAGNOSTIC_DELIVERABLES_IN_PROGRESS",
        )
        self.assertEqual(report["next_diagnostic_case"]["case_id"], "1A")
        self.assertEqual(
            tuple(
                item["case_id"]
                for item in report["cases"]
                if item["case_id"] in TEST1_DIAGNOSTIC_CASES
            ),
            TEST1_DIAGNOSTIC_CASES,
        )

    def test_complete_reference_campaign_routes_next_to_judged_1e(self):
        registry = {
            "cases": {
                "test_1/{}".format(case_id): {
                    "case_id": case_id,
                    "simulation_evidence": self._current_simulation(
                        "_reference_{}".format(case_id)
                    ),
                    "result_evidence": {
                        "required_output_scope_complete": True,
                        "simulation_link_status": "VERIFIED",
                        "observed_metric_count": 39 if case_id.endswith("FF") else 88,
                    },
                }
                for case_id in TEST1_ISO_CASES + TEST1_DIAGNOSTIC_CASES
            }
        }
        report = build_test1_campaign_status(registry)
        self.assertEqual(report["reference_results_complete_count"], 10)
        self.assertEqual(report["next_case"]["case_id"], TEST1_JUDGED_CASES[0])
        self.assertEqual(
            report["next_case"]["next_action"]["script"],
            "scripts/probes/Run_VE_SIA4010_Test1E_Prepare_Template.py",
        )


if __name__ == "__main__":
    unittest.main()
