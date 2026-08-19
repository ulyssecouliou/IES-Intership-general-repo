"""Regression tests for the Test 1 floor-insulation recovery launcher."""

import importlib
import json
import unittest
from pathlib import Path
from unittest.mock import Mock


launcher = importlib.import_module(
    "Run_VE_SIA4010_Test1_Reconcile_Floor_Insulation"
)


class FloorInsulationLauncherTests(unittest.TestCase):
    def test_resolves_project_relative_asset_manifest(self):
        project = Path("C:/projects/test1_600")
        self.assertEqual(
            launcher._resolve_scenario_file(project, "reference_model_assets.json"),
            project / "reference_model_assets.json",
        )

    def test_preserves_absolute_asset_manifest(self):
        project = Path("C:/projects/test1_600")
        absolute = Path("C:/controlled/reference_model_assets.json")
        self.assertEqual(
            launcher._resolve_scenario_file(project, str(absolute)), absolute
        )

    def test_only_known_cached_gateway_failure_is_safe_to_retry(self):
        payload = {
            "status": "FAIL",
            "error": (
                "AttributeError: IesVeGateway has no attribute "
                "reconcile_existing_material"
            ),
        }
        path = Mock()
        path.read_text.return_value = json.dumps(payload)
        self.assertTrue(launcher._safe_predispatch_failure(path))
        payload["receipt"] = {"changed": True}
        path.read_text.return_value = json.dumps(payload)
        self.assertFalse(launcher._safe_predispatch_failure(path))

    def test_completed_verified_repair_is_safe_to_retry_idempotently(self):
        path = Mock()
        path.read_text.return_value = json.dumps(
            {"status": "PASS", "receipt": {"status": "RECONCILED_AND_VERIFIED"}}
        )
        self.assertTrue(launcher._safe_retryable_report(path))


if __name__ == "__main__":
    unittest.main()
