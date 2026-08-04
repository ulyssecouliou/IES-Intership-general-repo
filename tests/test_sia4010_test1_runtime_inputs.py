"""Tests for the guarded ISO Test 1 to IESVE runtime mappings."""

import unittest

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.test1_runtime_inputs import (
    build_furniture_condition_payload,
    calculate_furniture_mass_factor,
    validate_capacity_semantics,
)


class Test1RuntimeInputMappingTests(unittest.TestCase):
    def test_case600_mapping_reconstructs_exact_target_capacity(self):
        mapping = calculate_furniture_mass_factor(
            floor_area_m2=48.0,
            room_volume_m3=129.6,
            reference_air_density_kg_m3=1.2,
        )
        reconstructed = (
            (1.0 + mapping.furniture_mass_factor)
            * mapping.ve_air_capacity_j_k
        )
        self.assertAlmostEqual(reconstructed, 480000.0, places=8)
        self.assertAlmostEqual(
            mapping.furniture_mass_factor, 2.071064430932006, places=12
        )
        self.assertFalse(mapping.compliance_claim_allowed)

    def test_unlimited_capacities_are_accepted_for_conditioned_case(self):
        receipt = validate_capacity_semantics(
            {
                "heating_capacity_unlimited": True,
                "cooling_capacity_unlimited": True,
            },
            conditioned=True,
        )
        self.assertTrue(receipt["verified"])

    def test_finite_or_missing_capacity_is_rejected(self):
        with self.assertRaises(ConfigurationError):
            validate_capacity_semantics(
                {
                    "heating_capacity_unlimited": True,
                    "cooling_capacity_unlimited": False,
                },
                conditioned=True,
            )

    def test_invalid_air_density_is_rejected(self):
        with self.assertRaises(ConfigurationError):
            calculate_furniture_mass_factor(
                floor_area_m2=48.0,
                room_volume_m3=129.6,
                reference_air_density_kg_m3=0.0,
            )

    def test_setter_payload_never_echoes_read_only_getter_fields(self):
        payload = build_furniture_condition_payload(
            {
                "furniture_mass_factor": 1.0,
                "furniture_mass_factor_from_template": True,
                "dhw_unit": "read-only getter value",
                "plant_profile_type_str": "read-only getter value",
            },
            2.071064430932006,
        )
        self.assertEqual(
            set(payload),
            {"furniture_mass_factor", "furniture_mass_factor_from_template"},
        )
        self.assertFalse(payload["furniture_mass_factor_from_template"])


if __name__ == "__main__":
    unittest.main()
