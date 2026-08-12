"""Tests for guarded lightweight Test 1 runtime-qualification bundles."""

import json
import unittest
from pathlib import Path

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
from swiss_sia.reference_model.sia4010.native_ui import ModelBuilderController
from swiss_sia.reference_model.sia4010.scenario_preflight import (
    evaluate_scenario,
)
from swiss_sia.reference_model.sia4010.test1_variant_bundle import (
    build_test1_heavyweight_probe_bundle,
    build_test1_lightweight_probe_bundle,
    build_test1_runtime_probe_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = ROOT / ".codex_tmp"


class Test1VariantBundleTests(unittest.TestCase):
    """Probe bundles must be exact, traceable and remain non-compliance claims."""

    def setUp(self):
        self.project = TEMP_ROOT / self._testMethodName
        self.project.mkdir(parents=True, exist_ok=True)
        self.weather = self.project / "DRYCOLD.epw"
        self.weather.write_text("runtime qualification weather\n", encoding="utf-8")

    def _build(self, case_id):
        return build_test1_lightweight_probe_bundle(
            self.project,
            ROOT,
            case_id,
            weather_file=self.weather,
        )

    def _build_heavy(self, case_id):
        return build_test1_heavyweight_probe_bundle(
            self.project,
            ROOT,
            case_id,
            weather_file=self.weather,
        )

    @staticmethod
    def _read(path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_rejects_heavyweight_and_diagnostic_cases(self):
        for case_id in ("600", "900", "940", "900FF", "1E"):
            with self.subTest(case_id=case_id):
                with self.assertRaises(ConfigurationError):
                    self._build(case_id)

    def test_heavy_wrapper_rejects_lightweight_and_diagnostic_cases(self):
        for case_id in ("600", "640", "600FF", "1E"):
            with self.subTest(case_id=case_id):
                with self.assertRaises(ConfigurationError):
                    self._build_heavy(case_id)

    def test_case640_writes_exact_two_level_setpoint_contract(self):
        receipt = self._build("640")
        self.assertEqual(
            receipt.status,
            "READY_FOR_PROVISIONAL_RUNTIME_QUALIFICATION",
        )
        assets = self._read(receipt.asset_manifest_path)
        self.assertEqual(assets["metadata"]["sia4010_case_id"], "640")
        profiles = {item["key"]: item for item in assets["profiles"]}
        self.assertEqual(
            profiles["heating_setpoint_daily_profile"]["data"]["value"],
            [
                [0.0, 10.0, ""],
                [7.0, 10.0, ""],
                [7.0, 20.0, ""],
                [23.0, 20.0, ""],
                [23.0, 10.0, ""],
                [24.0, 10.0, ""],
            ],
        )
        self.assertEqual(
            profiles["heating_setpoint_daily_profile"]["data"]["source"],
            "SIA 4010 Test 1 specification",
        )
        self.assertFalse(
            profiles["heating_setpoint_daily_profile"]["modulating"]
        )
        self.assertEqual(profiles["heating_setpoint_daily_profile"]["units"], 0)
        self.assertEqual(
            profiles["heating_setpoint_weekly_profile"]["data"]["value"],
            [{"profile_ref": "heating_setpoint_daily_profile"}] * 12,
        )
        self.assertNotIn("heating_setpoint_profile", profiles)
        conditions = assets["thermal_template"]["room_conditions"]
        self.assertEqual(
            assets["thermal_template"]["name"],
            "SIA4010_TEST1_CASE640_VARIABLE_SETPOINT_V7",
        )
        self.assertEqual(
            conditions["heating_profile"]["value"],
            "ON",
        )
        self.assertEqual(
            conditions["heating_setpoint_type"]["value"],
            "variable",
        )
        self.assertEqual(
            conditions["heating_setpoint_profile"]["value"],
            {"profile_ref": "heating_setpoint_weekly_profile"},
        )
        self.assertEqual(
            conditions["heating_setpoint_profile"]["source"],
            "SIA 4010 Test 1 specification",
        )
        self.assertTrue(
            assets["thermal_template"]["system_data"]["conditioned"]["value"]
        )

    def test_case600ff_disables_conditioning_without_fabricating_controls(self):
        receipt = self._build("600FF")
        assets = self._read(receipt.asset_manifest_path)
        self.assertEqual(assets["metadata"]["sia4010_case_id"], "600FF")
        self.assertFalse(
            assets["thermal_template"]["system_data"]["conditioned"]["value"]
        )
        conditions = assets["thermal_template"]["room_conditions"]
        self.assertEqual(conditions["heating_profile"]["value"], "OFF")
        self.assertEqual(conditions["cooling_profile"]["value"], "OFF")
        self.assertEqual(
            conditions["heating_profile"]["source"],
            "SIA 4010 Test 1 specification",
        )
        self.assertNotIn(
            "heating_setpoint_profile",
            {item["key"] for item in assets["profiles"]},
        )
        audit = self._read(receipt.audit_path)
        self.assertFalse(audit["compliance_claim_allowed"])
        self.assertTrue(audit["runtime_qualification_required"])
        self.assertEqual(audit["case_id"], "600FF")

    def test_case900_uses_exact_public_high_mass_layer_contract(self):
        receipt = self._build_heavy("900")
        self.assertEqual(
            receipt.status,
            "READY_FOR_PROVISIONAL_RUNTIME_QUALIFICATION",
        )
        assets = self._read(receipt.asset_manifest_path)
        self.assertEqual(assets["metadata"]["envelope_mass"], "HIGH_MASS")
        self.assertFalse(assets["metadata"]["compliance_claim_allowed"])
        materials = {item["key"]: item for item in assets["materials"]}
        constructions = {
            item["key"]: item for item in assets["constructions"]
        }
        self.assertEqual(
            [layer["material_key"] for layer in constructions["external_wall"]["layers"]],
            ["external_plaster", "eps_wall", "modular_brick"],
        )
        self.assertEqual(
            [layer["properties"]["thickness"]["value"] for layer in constructions["external_wall"]["layers"]],
            [0.009, 0.0615, 0.1],
        )
        self.assertEqual(
            [layer["material_key"] for layer in constructions["roof"]["layers"]],
            ["external_plaster", "eps_roof", "internal_plaster"],
        )
        self.assertEqual(
            [layer["material_key"] for layer in constructions["ground_floor"]["layers"]],
            ["xps_ground", "reinforced_concrete"],
        )
        ideal = materials["xps_ground"]["properties"]
        self.assertEqual(ideal["conductivity"]["value"], 0.04)
        self.assertEqual(ideal["density"]["value"], 0.0)
        self.assertEqual(ideal["specific_heat_capacity"]["value"], 0.0)
        self.assertEqual(
            ideal["density"]["validation_range"]["minimum"], 0.0
        )
        concrete_block = materials["modular_brick"]["properties"]
        self.assertEqual(concrete_block["conductivity"]["value"], 0.51)
        self.assertEqual(concrete_block["density"]["value"], 1400.0)
        self.assertEqual(
            concrete_block["specific_heat_capacity"]["value"], 1000.0
        )
        audit = self._read(receipt.audit_path)
        self.assertTrue(audit["runtime_qualification_required"])
        self.assertTrue(
            any(
                item["id"] == "VE_HIGH_MASS_ENVELOPE_RUNTIME_QUALIFICATION"
                for item in audit["known_uncertainties"]
            )
        )

    def test_case940_combines_high_mass_envelope_and_night_setback(self):
        receipt = self._build_heavy("940")
        assets = self._read(receipt.asset_manifest_path)
        profiles = {item["key"]: item for item in assets["profiles"]}
        self.assertEqual(
            profiles["heating_setpoint_daily_profile"]["reference"],
            "SIA940_HEATING_SETPOINT_ABSOLUTE_DAY",
        )
        self.assertEqual(
            profiles["heating_setpoint_daily_profile"]["data"]["value"],
            [
                [0.0, 10.0, ""],
                [7.0, 10.0, ""],
                [7.0, 20.0, ""],
                [23.0, 20.0, ""],
                [23.0, 10.0, ""],
                [24.0, 10.0, ""],
            ],
        )
        self.assertTrue(
            assets["thermal_template"]["system_data"]["conditioned"]["value"]
        )

    def test_case900ff_is_high_mass_and_free_floating(self):
        receipt = build_test1_runtime_probe_bundle(
            self.project,
            ROOT,
            "900FF",
            weather_file=self.weather,
        )
        assets = self._read(receipt.asset_manifest_path)
        self.assertEqual(assets["metadata"]["envelope_mass"], "HIGH_MASS")
        self.assertFalse(
            assets["thermal_template"]["system_data"]["conditioned"]["value"]
        )
        conditions = assets["thermal_template"]["room_conditions"]
        self.assertEqual(conditions["heating_profile"]["value"], "OFF")
        self.assertEqual(conditions["cooling_profile"]["value"], "OFF")
        self.assertNotIn(
            "heating_setpoint_profile",
            {item["key"] for item in assets["profiles"]},
        )

    def test_qualification_mode_passes_preflight_but_never_allows_claim(self):
        receipt = self._build("640")
        payload = ModelBuilderController().build_payload(
            "SIA4010_1A_640",
            "SIA4010_OFFICIAL",
            "1A",
            "test_1",
            "640",
            "QUALIFY_IN_ACTIVE_VE_PROJECT",
            str(receipt.case_manifest_path),
            str(receipt.config_path),
            str(receipt.asset_manifest_path),
        )
        scenario_path = self.project / "sia_model_scenario.json"
        scenario_path.write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )
        scenario = ModelScenario.load(scenario_path)
        preflight = evaluate_scenario(scenario, self.project, ROOT)
        self.assertEqual(
            preflight.status,
            "READY_FOR_PROVISIONAL_VE_MUTATION",
        )
        self.assertTrue(preflight.allows_mutation)
        self.assertFalse(
            preflight.scenario["input_readiness"]["compliance_claim_allowed"]
        )

    def test_rebuild_is_deterministic_for_runtime_inputs(self):
        first = self._build("600FF")
        first_assets = first.asset_manifest_path.read_bytes()
        first_config = first.config_path.read_bytes()
        second = self._build("600FF")
        self.assertEqual(second.asset_manifest_path.read_bytes(), first_assets)
        self.assertEqual(second.config_path.read_bytes(), first_config)

    def test_every_runtime_case_forces_zero_mechanical_outdoor_air(self):
        for case_id in ("640", "600FF", "900", "940", "900FF"):
            with self.subTest(case_id=case_id):
                receipt = build_test1_runtime_probe_bundle(
                    self.project,
                    ROOT,
                    case_id,
                    weather_file=self.weather,
                )
                assets = json.loads(
                    receipt.asset_manifest_path.read_text(encoding="utf-8")
                )
                system = assets["thermal_template"]["system_data"]
                self.assertEqual(
                    system["system_air_minimum_flowrate"]["value"], 0.0
                )
                self.assertEqual(
                    system["system_air_minimum_flowrate_units"]["value"], 3
                )


if __name__ == "__main__":
    unittest.main()
