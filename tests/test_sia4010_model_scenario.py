"""Tests for the feature-safe SIA 4010 model-scenario contract."""

import json
import unittest
from pathlib import Path

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.case_manifest import Sia4010CaseManifest
from swiss_sia.reference_model.sia4010.model_scenario import (
    ModelScenario,
    build_feature_catalog,
    official_features,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".codex_tmp" / "model_scenario_tests"


class Sia4010ModelScenarioTests(unittest.TestCase):
    def setUp(self):
        OUTPUT.mkdir(parents=True, exist_ok=True)

    def _write(self, payload, name="scenario.json"):
        path = OUTPUT / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _payload(self, variant="test_2A", case_id="2A"):
        return {
            "schema_version": "1.0",
            "scenario_id": "SCENARIO",
            "profile": "SIA4010_OFFICIAL",
            "selection": {
                "target_class": "1A",
                "variant": variant,
                "case_id": case_id,
            },
            "features": official_features(variant, case_id),
            "files": {
                "case_manifest_file": "config/sia4010_classes_1a_1b.json",
                "ve_config_file": "reference_model_config.json",
                "ve_asset_manifest_file": "reference_model_assets.json",
            },
            "execution": {"mode": "PREPARE_ONLY"},
        }

    def test_official_features_are_case_specific(self):
        self.assertTrue(official_features("test_1", "600")["ideal_heating"])
        self.assertFalse(official_features("test_1", "600FF")["ideal_heating"])
        self.assertFalse(official_features("test_1", "600")["solar_protection"])
        self.assertTrue(official_features("test_1", "1E")["solar_protection"])
        self.assertTrue(official_features("test_2A", "2A")["solar_protection"])

    def test_loads_valid_official_scenario(self):
        scenario = ModelScenario.load(self._write(self._payload()))
        self.assertTrue(scenario.is_official)
        self.assertEqual(scenario.case_id, "2A")

    def test_official_feature_cannot_be_disabled(self):
        payload = self._payload()
        payload["features"]["weather"] = False
        with self.assertRaises(ConfigurationError):
            ModelScenario.load(self._write(payload, "invalid_feature.json"))

    def test_class_variant_mapping_is_strict(self):
        payload = self._payload("test_2B", "2B")
        with self.assertRaises(ConfigurationError):
            ModelScenario.load(self._write(payload, "invalid_class.json"))

    def test_readiness_is_fail_closed_on_missing_inputs(self):
        scenario = ModelScenario.load(self._write(self._payload()))
        manifest = Sia4010CaseManifest.load(
            ROOT / "config" / "sia4010_classes_1a_1b.json"
        )
        readiness = scenario.readiness(manifest)
        self.assertEqual(readiness["decision"], "READY_FOR_PREPARATION")
        self.assertTrue(readiness["missing_parameters"])
        self.assertFalse(readiness["compliance_claim_allowed"])

    def test_catalog_and_python_rules_have_same_cases(self):
        catalog = build_feature_catalog()
        self.assertEqual(catalog["classes"]["1A"], ["test_1", "test_2A"])
        self.assertEqual(
            set(catalog["classes"]),
            {"1A", "1B", "2A", "2B", "3", "4A", "4B", "5"},
        )
        self.assertIn("test_3L", catalog["official_feature_matrix"])
        self.assertIn("test_5D", catalog["official_feature_matrix"])
        self.assertIn("test_7", catalog["official_feature_matrix"])
        self.assertEqual(
            catalog["official_feature_matrix"]["test_1"]["600FF"],
            official_features("test_1", "600FF"),
        )

    def test_loads_scenario_from_every_validation_domain(self):
        examples = (
            ("2B", "test_3L", "3L"),
            ("3", "test_5D", "5D"),
            ("4A", "test_7", "7"),
            ("5", "test_7", "7"),
        )
        for class_id, variant, case_id in examples:
            with self.subTest(class_id=class_id, variant=variant):
                payload = self._payload(variant, case_id)
                payload["selection"]["target_class"] = class_id
                scenario = ModelScenario.load(
                    self._write(payload, "{}_{}.json".format(class_id, variant))
                )
                self.assertEqual(scenario.target_class, class_id)

    def test_custom_scenario_cannot_mutate_ve(self):
        payload = self._payload()
        payload["profile"] = "CUSTOM_REFERENCE"
        payload["execution"]["mode"] = "CREATE_IN_ACTIVE_VE_PROJECT"
        with self.assertRaises(ConfigurationError):
            ModelScenario.load(self._write(payload, "custom_mutation.json"))


if __name__ == "__main__":
    unittest.main()
