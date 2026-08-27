"""Regression tests for guarded Test 1 one-click recovery decisions."""

import inspect
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import Run_VE_SIA_Model_Builder as model_builder
from Run_VE_SIA4010_Test1_Active_Case_One_Click import (
    _exact_floor_insulation_mismatch,
    _exact_stale_construction_key,
    _failed_control_ids,
    _outcome_failed,
    _requires_operator_checkpoint,
)


class ActiveCaseRecoveryTests(unittest.TestCase):
    def test_fresh_generation_requires_rfcont_operator_checkpoint(self):
        self.assertTrue(_requires_operator_checkpoint(0, "900"))
        self.assertFalse(_requires_operator_checkpoint(1, "900"))
        self.assertFalse(_requires_operator_checkpoint(0, "600FF"))
        self.assertFalse(_requires_operator_checkpoint(0, "900FF"))

    def test_only_explicit_failed_controls_are_returned(self):
        outcome = SimpleNamespace(
            status=SimpleNamespace(value="FAIL"),
            validation_results=(
                SimpleNamespace(
                    control_id="VE-THERM-004",
                    status=SimpleNamespace(value="FAIL"),
                ),
                SimpleNamespace(
                    control_id="CFG-004",
                    status=SimpleNamespace(value="WARNING"),
                ),
            ),
        )
        self.assertTrue(_outcome_failed(outcome))
        self.assertEqual(_failed_control_ids(outcome), {"VE-THERM-004"})

    def test_builder_exposes_explicit_geometry_resume_flag(self):
        signature = inspect.signature(model_builder.run)
        self.assertIn("resume_after_import", signature.parameters)
        self.assertFalse(signature.parameters["resume_after_import"].default)

    def test_floor_recovery_requires_one_exact_failure(self):
        payload = {
            "validation_results": [
                {
                    "status": "FAIL",
                    "message": (
                        "Controlled workflow failure: existing material "
                        "xps_ground (CDB id PYOP5, matched on description "
                        "'SIA600_FLOOR_INSULATION') cannot be reused read-back "
                        "mismatch: {'density': {'expected': 0.0, 'actual': "
                        "10.0}, 'specific_heat_capacity': {'expected': 0.0, "
                        "'actual': 1400.0}}"
                    ),
                }
            ]
        }
        with patch("pathlib.Path.read_text", return_value=json.dumps(payload)):
            self.assertTrue(_exact_floor_insulation_mismatch("C:/project"))
        payload["validation_results"].append(
            {"status": "FAIL", "message": "another failure"}
        )
        with patch("pathlib.Path.read_text", return_value=json.dumps(payload)):
            self.assertFalse(_exact_floor_insulation_mismatch("C:/project"))

    def test_exact_stale_construction_key_is_parsed_fail_closed(self):
        payload = {
            "validation_results": [
                {
                    "status": "FAIL",
                    "message": (
                        "Controlled workflow failure: existing construction "
                        "external_wall read-back mismatch: {'x': {'expected': "
                        "1, 'actual': 2}}"
                    ),
                }
            ]
        }
        with patch("pathlib.Path.read_text", return_value=json.dumps(payload)):
            self.assertEqual(_exact_stale_construction_key("C:/project"), "external_wall")
        payload["validation_results"].append(
            {"status": "FAIL", "message": "unrelated failure"}
        )
        with patch("pathlib.Path.read_text", return_value=json.dumps(payload)):
            self.assertEqual(_exact_stale_construction_key("C:/project"), "")


if __name__ == "__main__":
    unittest.main()
