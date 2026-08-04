"""Tests for the project-local SIA 4010 Case 600 MVP bundle."""

import json
import unittest
from pathlib import Path

from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
from swiss_sia.reference_model.sia4010.mvp_bundle import (
    build_case600_mvp_bundle,
)
from swiss_sia.reference_model.sia4010.weather_verification import sha256_file
from swiss_sia.reference_model.sia4010.native_ui import ModelBuilderController
from swiss_sia.reference_model.sia4010.scenario_preflight import (
    evaluate_scenario,
)


ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = ROOT / ".codex_tmp"


class Sia4010MvpBundleTests(unittest.TestCase):
    def setUp(self):
        self.project = TEMP_ROOT / self._testMethodName
        self.project.mkdir(parents=True, exist_ok=True)

    def test_missing_weather_is_explicitly_blocking(self):
        receipt = build_case600_mvp_bundle(self.project, ROOT)
        self.assertEqual(receipt.status, "BLOCKED_WEATHER")
        audit = json.loads(receipt.audit_path.read_text(encoding="utf-8"))
        self.assertFalse(audit["compliance_claim_allowed"])
        self.assertEqual(
            audit["evidence_summary"]["unresolved"],
            ["denver_drycold_weather_file"],
        )
        self.assertTrue(receipt.config_path.is_file())
        self.assertTrue(receipt.asset_manifest_path.is_file())

    def test_client_weather_enables_provisional_creation_preflight(self):
        weather = self.project / "DRYCOLD.epw"
        weather.write_text("provisional test weather\n", encoding="utf-8")
        receipt = build_case600_mvp_bundle(self.project, ROOT)
        self.assertEqual(
            receipt.status, "READY_FOR_PROVISIONAL_DEMONSTRATION"
        )
        controller = ModelBuilderController()
        payload = controller.build_payload(
            "SIA4010_1A_600",
            "SIA4010_OFFICIAL",
            "1A",
            "test_1",
            "600",
            "CREATE_IN_ACTIVE_VE_PROJECT",
            str(receipt.case_manifest_path),
            str(receipt.config_path),
            str(receipt.asset_manifest_path),
        )
        scenario_path = self.project / "scenario.json"
        scenario_path.write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
        preflight = evaluate_scenario(
            ModelScenario.load(scenario_path), self.project, ROOT
        )
        self.assertEqual(
            preflight.status, "READY_FOR_PROVISIONAL_VE_MUTATION"
        )
        self.assertTrue(preflight.allows_mutation)
        self.assertFalse(
            preflight.scenario["input_readiness"]["compliance_claim_allowed"]
        )

    def test_ui_controller_prepares_verified_and_runtime_probe_cases(self):
        controller = ModelBuilderController()
        probe = controller.prepare_supported_mvp_bundle(
            self.project, ROOT, "SIA4010_OFFICIAL", "test_1", "600FF"
        )
        self.assertEqual(
            probe.status,
            "READY_FOR_PROVISIONAL_RUNTIME_QUALIFICATION",
        )
        supported = controller.prepare_supported_mvp_bundle(
            self.project, ROOT, "SIA4010_OFFICIAL", "test_1", "600"
        )
        self.assertEqual(
            supported.status,
            "READY_FOR_PROVISIONAL_DEMONSTRATION",
        )
        heavyweight = controller.prepare_supported_mvp_bundle(
            self.project, ROOT, "SIA4010_OFFICIAL", "test_1", "900"
        )
        self.assertEqual(
            heavyweight.status,
            "READY_FOR_PROVISIONAL_RUNTIME_QUALIFICATION",
        )
        unsupported = controller.prepare_supported_mvp_bundle(
            self.project, ROOT, "SIA4010_OFFICIAL", "test_1", "1E"
        )
        self.assertIsNone(unsupported)

    def test_checksum_bound_weather_verification_is_preserved(self):
        weather = self.project / "DRYCOLD.TMY"
        weather.write_text("provisional TMY test weather\n", encoding="ascii")
        verification = self.project / (
            "DRYCOLD_TMY_ISO_SOURCE_VERIFICATION.json"
        )
        verification.write_text(
            json.dumps(
                {
                    "status": "PASS",
                    "source_identity_supported": True,
                    "weather": {"sha256": sha256_file(weather)},
                }
            ),
            encoding="utf-8",
        )
        receipt = build_case600_mvp_bundle(self.project, ROOT)
        audit = json.loads(receipt.audit_path.read_text(encoding="utf-8"))
        self.assertEqual(
            audit["weather_source_identity_verification"]["status"], "PASS"
        )
        self.assertFalse(
            audit["weather"]["identity_confirmation_required"]
        )
        self.assertTrue(
            audit["weather"]["acquisition_provenance_approval_required"]
        )

    def test_case600_glass_uses_ve2025_supported_material_properties(self):
        receipt = build_case600_mvp_bundle(self.project, ROOT)
        assets = json.loads(
            receipt.asset_manifest_path.read_text(encoding="utf-8")
        )
        glass = next(
            material
            for material in assets["materials"]
            if material["key"] == "equivalent_glazing_layer"
        )
        properties = glass["properties"]
        self.assertNotIn("density", properties)
        self.assertNotIn("specific_heat_capacity", properties)
        self.assertEqual(properties["conductivity"]["value"], 1.06)
        self.assertIn("transmittance", properties)
        self.assertIn("visible_transmittance", properties)

    def test_case600_uses_generic_ve_template_with_traced_evidence(self):
        receipt = build_case600_mvp_bundle(self.project, ROOT)
        assets = json.loads(
            receipt.asset_manifest_path.read_text(encoding="utf-8")
        )
        template = assets["thermal_template"]
        self.assertEqual(template["standard"], "generic")
        self.assertEqual(template["name"], "SIA4010_TEST1_CASE600")
        self.assertIn("ISO Test 1", template["description"])
        self.assertIn("ISO 52016-1:2017", template["source"])

    def test_case600_internal_gain_is_constant_sensible_200w_with_60_40_split(self):
        receipt = build_case600_mvp_bundle(self.project, ROOT)
        assets = json.loads(
            receipt.asset_manifest_path.read_text(encoding="utf-8")
        )
        config = json.loads(receipt.config_path.read_text(encoding="utf-8"))
        self.assertEqual(
            config["parameters"]["occupancy_profile_id"]["value"], "ON"
        )
        gains = {item["key"]: item for item in assets["gains"]}
        equipment = gains["equipment_gain"]["properties"]

        self.assertEqual(assets["profiles"], [])
        self.assertTrue(
            all(
                gain["properties"]["variation_profile"]["value"] == "ON"
                for gain in gains.values()
            )
        )
        self.assertTrue(
            all(
                exchange["properties"]["variation_profile"]["value"] == "ON"
                for exchange in assets["air_exchanges"]
            )
        )
        self.assertAlmostEqual(
            equipment["max_power_consumption"]["value"] * 48.0, 200.0
        )
        self.assertAlmostEqual(
            equipment["max_sensible_gain"]["value"] * 48.0, 200.0
        )
        self.assertEqual(equipment["max_latent_gain"]["value"], 0.0)
        self.assertEqual(equipment["radiant_fraction"]["value"], 0.6)
        self.assertIn("ISO 52016-1:2017", equipment["radiant_fraction"]["source"])

    def test_verified_runtime_glazing_calibration_survives_bundle_rebuild(self):
        receipt = build_case600_mvp_bundle(self.project, ROOT)
        assets = json.loads(
            receipt.asset_manifest_path.read_text(encoding="utf-8")
        )
        glazing = next(
            item
            for item in assets["constructions"]
            if item["key"] == "external_glazing"
        )
        cavity = next(
            layer for layer in glazing["layers"] if layer["is_cavity"]
        )
        cavity["properties"]["resistance"] = {
            "value": 0.14933,
            "description": "Runtime calibrated resistance.",
            "units": "m2 K/W",
            "source": "Runtime VE CDB ISO U-factor calibration",
            "source_locator": "controlled test calibration",
            "validation_range": {
                "expected_type": "number",
                "minimum": 0.000001,
                "maximum": 100.0,
                "allow_none": False,
            },
            "required": True,
        }
        assets["metadata"]["external_glazing_runtime_calibration"] = {
            "construction_id": "EXTW",
            "target_u_w_m2k": 2.984,
            "verified_u_w_m2k": 2.9841,
            "cavity_resistance_m2k_w": 0.14933,
            "ve_version": "2025.2.0.0",
            "status": "engineering-equivalent",
        }
        receipt.asset_manifest_path.write_text(
            json.dumps(assets, indent=2) + "\n", encoding="utf-8"
        )

        rebuilt = build_case600_mvp_bundle(self.project, ROOT)
        rebuilt_assets = json.loads(
            rebuilt.asset_manifest_path.read_text(encoding="utf-8")
        )
        rebuilt_glazing = next(
            item
            for item in rebuilt_assets["constructions"]
            if item["key"] == "external_glazing"
        )
        rebuilt_cavity = next(
            layer
            for layer in rebuilt_glazing["layers"]
            if layer["is_cavity"]
        )
        self.assertEqual(
            rebuilt_cavity["properties"]["resistance"]["value"], 0.14933
        )
        self.assertTrue(
            rebuilt_assets["metadata"][
                "external_glazing_runtime_calibration"
            ]["preserved_by_bundle_rebuild"]
        )


if __name__ == "__main__":
    unittest.main()
