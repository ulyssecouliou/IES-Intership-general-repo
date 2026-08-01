"""Tests for fail-closed scenario model-builder preflight."""

import json
import unittest
from pathlib import Path

from swiss_sia.reference_model.sia4010.model_scenario import (
    ModelScenario,
    official_features,
)
from swiss_sia.reference_model.sia4010.scenario_preflight import (
    evaluate_scenario,
    is_temporary_ve_project,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".codex_tmp" / "scenario_preflight_tests"


class Sia4010ScenarioPreflightTests(unittest.TestCase):
    def setUp(self):
        OUTPUT.mkdir(parents=True, exist_ok=True)

    def _scenario(self, execution_mode="PREPARE_ONLY"):
        scenario = {
            "schema_version": "1.0",
            "scenario_id": "TEST2A",
            "profile": "SIA4010_OFFICIAL",
            "selection": {
                "target_class": "1A",
                "variant": "test_2A",
                "case_id": "2A",
            },
            "features": official_features("test_2A", "2A"),
            "files": {
                "case_manifest_file": "config/sia4010_classes_1a_1b.json",
                "ve_config_file": "missing_config.json",
                "ve_asset_manifest_file": "missing_assets.json",
            },
            "execution": {"mode": execution_mode},
        }
        path = OUTPUT / "scenario.json"
        path.write_text(json.dumps(scenario), encoding="utf-8")
        return ModelScenario.load(path)

    def test_prepare_only_creates_reviewable_decision(self):
        result = evaluate_scenario(self._scenario(), OUTPUT, ROOT)
        self.assertEqual(result.status, "READY_FOR_PREPARATION")
        self.assertFalse(result.allows_mutation)
        self.assertTrue(result.blockers)
        self.assertTrue(result.warnings)

    def test_mutation_is_blocked_without_official_inputs_and_assets(self):
        result = evaluate_scenario(
            self._scenario("CREATE_IN_ACTIVE_VE_PROJECT"), OUTPUT, ROOT
        )
        self.assertEqual(result.status, "BLOCKED_CONFIGURATION")
        self.assertFalse(result.allows_mutation)
        self.assertGreaterEqual(len(result.blockers), 3)

    def test_unsaved_ve_temp_project_is_detected(self):
        self.assertTrue(
            is_temporary_ve_project(
                Path.home()
                / "AppData"
                / "Local"
                / "Temp"
                / "VEPROJ"
                / "2025200"
            )
        )


if __name__ == "__main__":
    unittest.main()
