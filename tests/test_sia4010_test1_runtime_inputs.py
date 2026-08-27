"""Tests for the guarded ISO Test 1 to IESVE runtime mappings."""

import unittest

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.test1_runtime_inputs import (
    build_furniture_condition_payload,
    build_ideal_load_system_payload,
    build_zero_mechanical_ventilation_payload,
    calculate_furniture_mass_factor,
    is_conditioned_state,
    is_off_profile,
    validate_capacity_semantics,
    validate_ideal_load_emission_semantics,
    validate_prescribed_infiltration_preserved,
    validate_zero_mechanical_ventilation_semantics,
)


class Test1RuntimeInputMappingTests(unittest.TestCase):
    def test_off_profile_binding_is_exact_but_case_insensitive(self):
        self.assertTrue(is_off_profile("OFF"))
        self.assertTrue(is_off_profile("off"))
        self.assertFalse(is_off_profile("ON"))
        self.assertFalse(is_off_profile(None))

    def test_conditioned_enum_is_interpreted_by_name_not_truthiness(self):
        self.assertTrue(is_conditioned_state("iesve.conditioned_flag.yes"))
        self.assertFalse(is_conditioned_state("iesve.conditioned_flag.no_free_floating"))
        with self.assertRaises(ConfigurationError):
            is_conditioned_state("iesve.conditioned_flag.unknown")

    def test_case600_mapping_reconstructs_exact_target_capacity(self):
        mapping = calculate_furniture_mass_factor(
            floor_area_m2=48.0,
            room_volume_m3=129.6,
            reference_air_density_kg_m3=1.2,
        )
        reconstructed = (
            1.0 + mapping.furniture_mass_factor
        ) * mapping.ve_air_capacity_j_k
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

    def test_ideal_load_payload_maps_iso_convective_fraction_to_ve(self):
        payload = build_ideal_load_system_payload(
            {
                "heating_plant_radiant_fraction": 0.2,
                "cooling_plant_radiant_fraction": 0.1,
                "heating_plant_radiant_fraction_from_template": True,
                "read_only_label": "ignored",
            }
        )
        self.assertEqual(payload["heating_plant_radiant_fraction"], 0.0)
        self.assertEqual(payload["cooling_plant_radiant_fraction"], 0.0)
        self.assertFalse(payload["heating_plant_radiant_fraction_from_template"])
        self.assertNotIn("read_only_label", payload)

    def test_ideal_load_emission_readback_must_be_fully_convective(self):
        receipt = validate_ideal_load_emission_semantics(
            {
                "heating_plant_radiant_fraction": 0.0,
                "cooling_plant_radiant_fraction": 0.0,
            }
        )
        self.assertTrue(receipt["verified"])
        with self.assertRaises(ConfigurationError):
            validate_ideal_load_emission_semantics(
                {
                    "heating_plant_radiant_fraction": 0.2,
                    "cooling_plant_radiant_fraction": 0.0,
                }
            )

    def test_ideal_load_emission_missing_fraction_is_fail_closed(self):
        # A missing radiant fraction must fail closed to a ConfigurationError,
        # not a raw TypeError from float(None). Degenerate VE read-back is a
        # controlled failure here, mirroring the mechanical-ventilation validator.
        with self.assertRaises(ConfigurationError):
            validate_ideal_load_emission_semantics(
                {"cooling_plant_radiant_fraction": 0.0}
            )

    def test_mechanical_ventilation_payload_and_readback_are_zero(self):
        payload = build_zero_mechanical_ventilation_payload(
            {
                "system_air_minimum_flowrate": 10.0,
                "system_air_minimum_flowrate_units": 3,
                "system_air_minimum_flowrate_from_template": True,
            }
        )
        self.assertEqual(payload["system_air_minimum_flowrate"], 0.0)
        self.assertFalse(payload["system_air_minimum_flowrate_from_template"])
        self.assertNotIn("system_air_minimum_flowrate_units", payload)
        receipt = validate_zero_mechanical_ventilation_semantics(
            {"system_air_minimum_flowrate": 0.0, "system_air_minimum_flowrate_units": 3}
        )
        self.assertTrue(receipt["verified"])
        with self.assertRaises(ConfigurationError):
            validate_zero_mechanical_ventilation_semantics(
                {"system_air_minimum_flowrate": 10.0}
            )

    def test_prescribed_infiltration_readback_accepts_room_max_flows_dict(self):
        """VE returns room-level flows as a dict indexed by the unit selector."""

        receipt = validate_prescribed_infiltration_preserved(
            [
                {
                    "name": "SIA600_INFILTRATION_0P41ACH",
                    "type_val": 0,
                    "units_val": 2,
                    "max_flows": {2: 0.3075},
                    "max_flow_from_template": False,
                }
            ]
        )
        self.assertTrue(receipt["verified"])
        self.assertAlmostEqual(receipt["ve_infiltration_max_flow"], 0.3075)
        self.assertEqual(receipt["ve_infiltration_units_val"], 2)
        self.assertEqual(receipt["ve_air_exchange_count"], 1)

    def test_prescribed_infiltration_readback_accepts_get_objects(self):
        """Real VE hands back objects exposing get(), not plain mappings."""

        class _Exchange:
            def __init__(self, data):
                self._data = data

            def get(self):
                return dict(self._data)

        receipt = validate_prescribed_infiltration_preserved(
            [
                _Exchange(
                    {
                        "name": "SIA600_INFILTRATION_0P41ACH",
                        "type_val": 0,
                        "units_val": 2,
                        "max_flows": {2: 0.3075},
                    }
                )
            ]
        )
        self.assertTrue(receipt["verified"])

    def test_prescribed_infiltration_rejects_missing_exchange(self):
        with self.assertRaises(ConfigurationError):
            validate_prescribed_infiltration_preserved([])

    def test_prescribed_infiltration_rejects_zero_flow(self):
        with self.assertRaises(ConfigurationError):
            validate_prescribed_infiltration_preserved(
                [{"type_val": 0, "units_val": 2, "max_flows": {2: 0.0}}]
            )

    def test_prescribed_infiltration_ignores_mechanical_ventilation_records(self):
        """type_val 2 is Auxiliary Ventilation and must never satisfy the check."""

        with self.assertRaises(ConfigurationError):
            validate_prescribed_infiltration_preserved(
                [{"type_val": 2, "units_val": 3, "max_flows": {3: 10.0}}]
            )

    def test_prescribed_infiltration_accepts_zero_outdoor_air_companion(self):
        """The asset manifest deliberately creates outdoor_air at exactly zero."""

        receipt = validate_prescribed_infiltration_preserved(
            [
                {
                    "name": "SIA600FF_INFILTRATION_0P41ACH",
                    "type_val": 0,
                    "units_val": 2,
                    "max_flows": {2: 0.3075},
                },
                {
                    "name": "SIA600FF_OUTDOOR_AIR_ZERO",
                    "type_val": 2,
                    "units_val": 3,
                    "max_flows": {3: 0.0},
                },
            ]
        )
        self.assertTrue(receipt["verified"])
        self.assertEqual(receipt["ve_air_exchange_count"], 2)
        self.assertTrue(receipt["ve_other_air_exchanges_all_zero"])
        self.assertEqual(len(receipt["ve_other_air_exchanges"]), 1)
        self.assertEqual(
            receipt["ve_other_air_exchanges"][0]["name"],
            "SIA600FF_OUTDOOR_AIR_ZERO",
        )

    def test_prescribed_infiltration_rejects_second_exchange_carrying_flow(self):
        """A non-zero second path defeats the whole zero-ventilation correction."""

        with self.assertRaisesRegex(ConfigurationError, "prescribes infiltration only"):
            validate_prescribed_infiltration_preserved(
                [
                    {
                        "name": "SIA600FF_INFILTRATION_0P41ACH",
                        "type_val": 0,
                        "units_val": 2,
                        "max_flows": {2: 0.3075},
                    },
                    {
                        "name": "LEFTOVER_MECH_VENT",
                        "type_val": 2,
                        "units_val": 3,
                        "max_flows": {3: 10.0},
                    },
                ]
            )

    def test_prescribed_infiltration_rejects_natural_ventilation_flow(self):
        """type_val 1 is Natural Ventilation and is equally out of scope."""

        with self.assertRaisesRegex(ConfigurationError, "prescribes infiltration only"):
            validate_prescribed_infiltration_preserved(
                [
                    {"type_val": 0, "units_val": 2, "max_flows": {2: 0.3075}},
                    {"type_val": 1, "units_val": 0, "max_flows": {0: 2.0}},
                ]
            )

    def test_prescribed_infiltration_rejects_duplicate_infiltration(self):
        with self.assertRaises(ConfigurationError):
            validate_prescribed_infiltration_preserved(
                [
                    {"type_val": 0, "units_val": 2, "max_flows": {2: 0.3075}},
                    {"type_val": 0, "units_val": 2, "max_flows": {2: 0.3075}},
                ]
            )


if __name__ == "__main__":
    unittest.main()
