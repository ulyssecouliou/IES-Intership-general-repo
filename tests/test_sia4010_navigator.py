"""Tests for the fail-closed SIA 4010 class navigator."""

import json
import unittest
from pathlib import Path

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.navigator import Sia4010ValidationNavigator
from swiss_sia.reference_model.sia4010.navigator_report import (
    write_navigator_artifacts,
)

TEST_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = TEST_ROOT / ".codex_tmp" / "sia4010_navigator"


def _ready_models(*variants):
    return {variant: "VERIFIED" for variant in variants}


def _results(*variants):
    return {variant: {"status": "OFFICIAL_RESULTS_RECORDED"} for variant in variants}


def _locators(*variants):
    return {variant: "aps/{}.csv".format(variant) for variant in variants}


class Sia4010NavigatorTests(unittest.TestCase):
    def test_class_1a_requires_exact_2a_not_generic_test2(self):
        evaluation = Sia4010ValidationNavigator.evaluate(
            "1A",
            bundle_verified=True,
            model_case_statuses=_ready_models("test_1", "test_2A"),
            candidate_result_locators=_locators("test_1", "test_2A"),
            test_results_map={
                "test_1": {"status": "OFFICIAL_RESULTS_RECORDED"},
                "test_2": {"status": "OFFICIAL_RESULTS_RECORDED"},
            },
        )
        self.assertEqual(evaluation.overall_status, "RESULTS_INCOMPLETE")
        comparison = next(
            gate for gate in evaluation.gates if gate.gate_id == "official_comparison"
        )
        self.assertEqual(comparison.missing_variants, ("test_2A",))

    def test_class_1b_requires_2b_2c_and_2d(self):
        required = ("test_1", "test_2B", "test_2C", "test_2D")
        evaluation = Sia4010ValidationNavigator.evaluate(
            "1B",
            bundle_verified=True,
            model_case_statuses=_ready_models(*required),
            candidate_result_locators=_locators(*required),
            test_results_map=_results("test_1", "test_2B"),
        )
        self.assertEqual(evaluation.overall_status, "RESULTS_INCOMPLETE")
        comparison = next(
            gate for gate in evaluation.gates if gate.gate_id == "official_comparison"
        )
        self.assertEqual(comparison.missing_variants, ("test_2C", "test_2D"))

    def test_failed_band_wins(self):
        required = ("test_1", "test_2A")
        results = _results(*required)
        results["test_2A"] = {"status": "FAILED"}
        evaluation = Sia4010ValidationNavigator.evaluate(
            "1A",
            bundle_verified=True,
            model_case_statuses=_ready_models(*required),
            candidate_result_locators=_locators(*required),
            test_results_map=results,
        )
        self.assertEqual(evaluation.overall_status, "OFFICIAL_BAND_FAILED")

    def test_technical_success_still_requires_attestation(self):
        required = ("test_1", "test_2A")
        evaluation = Sia4010ValidationNavigator.evaluate(
            "1A",
            bundle_verified=True,
            model_case_statuses=_ready_models(*required),
            candidate_result_locators=_locators(*required),
            test_results_map=_results(*required),
        )
        self.assertEqual(evaluation.technical_status, "TECHNICALLY_WITHIN_OFFICIAL_BANDS")
        self.assertEqual(evaluation.overall_status, "READY_FOR_OFFICIAL_REVIEW")

    def test_attestation_is_recorded_without_claiming_certification(self):
        required = ("test_1", "test_2A")
        evaluation = Sia4010ValidationNavigator.evaluate(
            "1A",
            bundle_verified=True,
            model_case_statuses=_ready_models(*required),
            candidate_result_locators=_locators(*required),
            test_results_map=_results(*required),
            attestation_locator="evidence/SIA_attestation.pdf",
        )
        self.assertEqual(evaluation.overall_status, "OFFICIAL_ATTESTATION_RECORDED")
        self.assertNotIn("certified", evaluation.overall_status.lower())

    def test_every_official_class_is_supported(self):
        for class_id in ("1A", "1B", "2A", "2B", "3", "4A", "4B", "5"):
            with self.subTest(class_id=class_id):
                evaluation = Sia4010ValidationNavigator.evaluate(
                    class_id,
                    bundle_verified=False,
                    model_case_statuses={},
                    candidate_result_locators={},
                    test_results_map={},
                )
                self.assertEqual(evaluation.target_class, class_id)
                self.assertTrue(evaluation.required_variants)

    def test_unknown_class_is_rejected(self):
        with self.assertRaises(ConfigurationError):
            Sia4010ValidationNavigator.evaluate(
                "9",
                bundle_verified=False,
                model_case_statuses={},
                candidate_result_locators={},
                test_results_map={},
            )

    def test_report_writes_json_and_html(self):
        evaluation = Sia4010ValidationNavigator.evaluate(
            "1A",
            bundle_verified=False,
            model_case_statuses={},
            candidate_result_locators={},
            test_results_map={},
        )
        paths = write_navigator_artifacts(evaluation, OUTPUT)
        payload = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
        html = Path(paths["html"]).read_text(encoding="utf-8")
        self.assertEqual(payload["target_class"], "1A")
        self.assertIn("SIA 4010 validation navigator", html)
        self.assertIn("BLOCKED_OFFICIAL_BUNDLE", html)


if __name__ == "__main__":
    unittest.main()
