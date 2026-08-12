"""Tests for the six-case Test 1 campaign state machine."""

import unittest

from swiss_sia.reference_model.sia4010.test1_campaign import (
    TEST1_CAMPAIGN_CASES,
    build_test1_campaign_status,
)


class Test1CampaignTests(unittest.TestCase):
    def test_next_case_follows_official_campaign_order(self):
        registry = {"cases": {}}
        report = build_test1_campaign_status(registry)
        self.assertEqual(report["next_case"]["case_id"], "600")
        self.assertEqual(report["case_count"], 6)

    def test_completed_600_advances_to_640(self):
        registry = {
            "cases": {
                "test_1/600": {
                    "case_id": "600",
                    "result_evidence": {
                        "required_output_scope_complete": True,
                        "simulation_link_status": "VERIFIED",
                        "observed_metric_count": 88,
                    },
                }
            }
        }
        report = build_test1_campaign_status(registry)
        self.assertEqual(report["reference_results_complete_count"], 1)
        self.assertEqual(report["next_case"]["case_id"], "640")

    def test_all_cases_complete_without_formal_verdict(self):
        registry = {
            "cases": {
                "test_1/{}".format(case_id): {
                    "case_id": case_id,
                    "result_evidence": {
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
        self.assertTrue(
            all(
                item["formal_compliance_verdict"].startswith("NOT_AVAILABLE")
                for item in report["cases"]
            )
        )


if __name__ == "__main__":
    unittest.main()
