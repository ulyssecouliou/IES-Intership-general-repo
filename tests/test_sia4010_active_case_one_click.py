"""Regression tests for guarded Test 1 one-click recovery decisions."""

import inspect
import unittest
from types import SimpleNamespace

import Run_VE_SIA_Model_Builder as model_builder
from Run_VE_SIA4010_Test1_Active_Case_One_Click import (
    _failed_control_ids,
    _outcome_failed,
)


class ActiveCaseRecoveryTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
