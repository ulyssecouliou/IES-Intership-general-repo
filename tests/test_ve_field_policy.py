"""Unit tests for ``swiss_sia.reference_model.ve_field_policy``.

Each family of VE 2025 storage / API canonicalisation observed in the field is
reproduced with a small dict double so the policy module is proven against the
exact input shapes that trigger the bug in real launchers.
"""

import unittest

from swiss_sia.reference_model.ve_field_policy import (
    CODE_CONSTANT_ONE_PROFILE_CANONICALIZED_ON,
    CODE_CONSTRUCTION_SURFACE_RESISTANCE_ROUNDED_4DP,
    CODE_GLASS_OPTICAL_PROPERTY_ROUNDED_3DP,
    CODE_GLAZED_CONSTRUCTION_VLT_ROUNDED_4DP,
    CODE_GLAZED_LAYER_RESISTANCE_ROUNDED_5DP,
    CODE_GLAZED_LAYER_THICKNESS_NOT_PERSISTED,
    CODE_MATERIAL_ZERO_THERMAL_MASS_MINIMUM,
    CODE_OPTION_NOT_EXPOSED,
    CODE_OPTION_REQUIRED_MISSING,
    CODE_ROOM_CONDITION_AUDIT_ONLY,
    CODE_ZERO_AIR_FLOW_PROFILE_CANONICALIZED_ON,
    CODE_ZERO_GAIN_PROFILE_CANONICALIZED_ON,
    OptionFilterResult,
    ReadbackStatus,
    VE_THERMAL_MASS_MINIMUM,
    partition_options,
    verify_air_exchange,
    verify_construction,
    verify_gain,
    verify_layer,
    verify_material,
)


class MaterialZeroThermalMassTests(unittest.TestCase):
    """Zero density / specific_heat_capacity persisted at 1e-6."""

    def test_zero_density_persisted_at_ve_minimum_is_warning(self) -> None:
        expected = {"conductivity": 0.04, "density": 0.0, "specific_heat_capacity": 0.0}
        actual = {
            "conductivity": 0.04,
            "density": VE_THERMAL_MASS_MINIMUM,
            "specific_heat_capacity": VE_THERMAL_MASS_MINIMUM,
        }
        verdict = verify_material("insulation", expected, actual)
        self.assertEqual(verdict.status, ReadbackStatus.WARNING)
        self.assertEqual(verdict.mismatches, {})
        codes = [w["code"] for w in verdict.warnings]
        self.assertIn(CODE_MATERIAL_ZERO_THERMAL_MASS_MINIMUM, codes)

    def test_non_zero_density_off_by_one_is_fail(self) -> None:
        expected = {"conductivity": 0.04, "density": 30.0}
        actual = {"conductivity": 0.04, "density": 29.0}
        verdict = verify_material("insulation", expected, actual)
        self.assertEqual(verdict.status, ReadbackStatus.FAIL)
        self.assertIn("density", verdict.mismatches)

    def test_zero_density_persisted_at_wrong_minimum_is_fail(self) -> None:
        # VE returned an unexpected non-1e-6 value: not a documented
        # canonicalisation, so it must NOT be silently accepted.
        expected = {"density": 0.0}
        actual = {"density": 1.0e-3}
        verdict = verify_material("insulation", expected, actual)
        self.assertEqual(verdict.status, ReadbackStatus.FAIL)


class GlassOpticalRoundingTests(unittest.TestCase):
    """Glass ``transmittance`` / ``visible_transmittance`` rounded to 3dp."""

    def test_glass_transmittance_3dp_rounding_is_warning(self) -> None:
        expected = {"transmittance": 0.31456, "visible_transmittance": 0.71234}
        actual = {
            "transmittance": round(0.31456, 3),
            "visible_transmittance": round(0.71234, 3),
        }
        verdict = verify_material("glass", expected, actual)
        self.assertEqual(verdict.status, ReadbackStatus.WARNING)
        codes = [w["code"] for w in verdict.warnings]
        self.assertIn(CODE_GLASS_OPTICAL_PROPERTY_ROUNDED_3DP, codes)

    def test_non_glass_optical_rounding_is_fail(self) -> None:
        expected = {"transmittance": 0.31456}
        actual = {"transmittance": round(0.31456, 3)}
        verdict = verify_material("insulation", expected, actual)
        # For non-glass materials the 3dp rule does not apply so any diff fails.
        self.assertEqual(verdict.status, ReadbackStatus.FAIL)

    def test_glass_transmittance_off_by_two_decimals_is_fail(self) -> None:
        expected = {"transmittance": 0.42}
        actual = {"transmittance": 0.41}
        verdict = verify_material("glass", expected, actual)
        self.assertEqual(verdict.status, ReadbackStatus.FAIL)


class GlazedLayerCanonicalisationTests(unittest.TestCase):
    """Glazed layers: thickness dropped to 0 and resistance rounded to 5dp."""

    def test_glazed_layer_thickness_lost_is_warning(self) -> None:
        expected = {"thickness": 0.006}
        actual = {"thickness": 0.0}
        verdict = verify_layer("glazed", expected, actual)
        self.assertEqual(verdict.status, ReadbackStatus.WARNING)
        codes = [w["code"] for w in verdict.warnings]
        self.assertIn(CODE_GLAZED_LAYER_THICKNESS_NOT_PERSISTED, codes)

    def test_opaque_layer_thickness_lost_is_fail(self) -> None:
        expected = {"thickness": 0.006}
        actual = {"thickness": 0.0}
        verdict = verify_layer("opaque", expected, actual)
        self.assertEqual(verdict.status, ReadbackStatus.FAIL)

    def test_glazed_layer_resistance_5dp_rounding_is_warning(self) -> None:
        expected = {"resistance": 0.123456789}
        actual = {"resistance": round(0.123456789, 5)}
        verdict = verify_layer("glazed", expected, actual)
        self.assertEqual(verdict.status, ReadbackStatus.WARNING)
        codes = [w["code"] for w in verdict.warnings]
        self.assertIn(CODE_GLAZED_LAYER_RESISTANCE_ROUNDED_5DP, codes)

    def test_glazed_layer_resistance_off_by_4dp_is_fail(self) -> None:
        # 4dp rounding is NOT a documented canonicalisation on layers.
        expected = {"resistance": 0.123456789}
        actual = {"resistance": round(0.123456789, 4)}
        verdict = verify_layer("glazed", expected, actual)
        self.assertEqual(verdict.status, ReadbackStatus.FAIL)


class GlazedConstructionVLTTests(unittest.TestCase):
    """Glazed constructions: ``visible_light_transmittance`` rounded to 4dp."""

    def test_glazed_construction_vlt_4dp_rounding_is_warning(self) -> None:
        expected = {"visible_light_transmittance": 0.712345}
        actual = {"visible_light_transmittance": round(0.712345, 4)}
        verdict = verify_construction("glazed", expected, actual)
        self.assertEqual(verdict.status, ReadbackStatus.WARNING)
        codes = [w["code"] for w in verdict.warnings]
        self.assertIn(CODE_GLAZED_CONSTRUCTION_VLT_ROUNDED_4DP, codes)

    def test_opaque_construction_vlt_diff_is_fail(self) -> None:
        expected = {"visible_light_transmittance": 0.712345}
        actual = {"visible_light_transmittance": round(0.712345, 4)}
        verdict = verify_construction("opaque", expected, actual)
        self.assertEqual(verdict.status, ReadbackStatus.FAIL)


class ConstructionSurfaceResistanceTests(unittest.TestCase):
    """VE construction surface resistances persist at four decimals."""

    def test_surface_resistance_4dp_rounding_is_warning(self) -> None:
        expected = {
            "inside_surface_resistance": 0.1310615989515072,
            "outside_surface_resistance": 0.041425020712510356,
        }
        actual = {
            "inside_surface_resistance": 0.13109999895095825,
            "outside_surface_resistance": 0.0414000004529953,
        }
        verdict = verify_construction("opaque", expected, actual)
        self.assertEqual(verdict.status, ReadbackStatus.WARNING)
        self.assertEqual(
            verdict.warnings[0]["code"],
            CODE_CONSTRUCTION_SURFACE_RESISTANCE_ROUNDED_4DP,
        )
        self.assertEqual(
            verdict.warnings[0]["fields"]["inside_surface_resistance"][
                "canonical_4dp"
            ],
            0.1311,
        )

    def test_surface_resistance_outside_4dp_canonical_value_is_fail(self) -> None:
        verdict = verify_construction(
            "opaque",
            {"inside_surface_resistance": 0.1310615989515072},
            {"inside_surface_resistance": 0.13},
        )
        self.assertEqual(verdict.status, ReadbackStatus.FAIL)


class GainProfileCanonicalisationTests(unittest.TestCase):
    """Two documented ``variation_profile -> ON`` acceptances on gains."""

    def test_zero_lighting_gain_profile_canonicalised_to_on_is_warning(self) -> None:
        expected = {
            "max_power_consumption": 0.0,
            "variation_profile": "DAY_0042",
        }
        actual = {
            "max_power_consumption": 0.0,
            "variation_profile": "ON",
        }
        verdict = verify_gain("lighting", expected, actual)
        self.assertEqual(verdict.status, ReadbackStatus.WARNING)
        codes = [w["code"] for w in verdict.warnings]
        self.assertIn(CODE_ZERO_GAIN_PROFILE_CANONICALIZED_ON, codes)

    def test_non_zero_lighting_gain_profile_canonicalised_to_on_is_fail(self) -> None:
        expected = {
            "max_power_consumption": 5.5,
            "variation_profile": "DAY_0042",
        }
        actual = {
            "max_power_consumption": 5.5,
            "variation_profile": "ON",
        }
        verdict = verify_gain("lighting", expected, actual)
        self.assertEqual(verdict.status, ReadbackStatus.FAIL)

    def test_constant_one_profile_declared_is_accepted_as_on(self) -> None:
        expected = {
            "max_power_consumption": 5.5,
            "variation_profile": "DAY_0100",
        }
        actual = {
            "max_power_consumption": 5.5,
            "variation_profile": "ON",
        }
        verdict = verify_gain(
            "lighting",
            expected,
            actual,
            constant_on_profile_ids=frozenset({"DAY_0100"}),
        )
        self.assertEqual(verdict.status, ReadbackStatus.WARNING)
        codes = [w["code"] for w in verdict.warnings]
        self.assertIn(CODE_CONSTANT_ONE_PROFILE_CANONICALIZED_ON, codes)


class AirExchangeProfileCanonicalisationTests(unittest.TestCase):

    def test_zero_flow_profile_canonicalised_to_on_is_warning(self) -> None:
        expected = {"max_flow": 0.0, "variation_profile": "DAY_0007"}
        actual = {"max_flow": 0.0, "variation_profile": "ON"}
        verdict = verify_air_exchange(expected, actual)
        self.assertEqual(verdict.status, ReadbackStatus.WARNING)
        codes = [w["code"] for w in verdict.warnings]
        self.assertIn(CODE_ZERO_AIR_FLOW_PROFILE_CANONICALIZED_ON, codes)

    def test_non_zero_flow_profile_canonicalised_to_on_is_fail(self) -> None:
        expected = {"max_flow": 0.6, "variation_profile": "DAY_0007"}
        actual = {"max_flow": 0.6, "variation_profile": "ON"}
        verdict = verify_air_exchange(expected, actual)
        self.assertEqual(verdict.status, ReadbackStatus.FAIL)


class OptionFilterTests(unittest.TestCase):
    """``partition_options`` covers each unknown-option scenario."""

    def test_solar_reflected_fraction_is_audit_only(self) -> None:
        payload = {"heating_setpoint": 20.0, "solar_reflected_fraction": 0.2}
        result = partition_options(
            payload,
            audit_only_keys={"solar_reflected_fraction"},
        )
        self.assertNotIn("solar_reflected_fraction", result.writable)
        self.assertIn("solar_reflected_fraction", result.audit_only)
        self.assertEqual(result.status, ReadbackStatus.WARNING)
        codes = [w["code"] for w in result.warnings]
        self.assertIn(CODE_ROOM_CONDITION_AUDIT_ONLY, codes)

    def test_dhw_unit_dropped_when_not_in_known_writable_keys(self) -> None:
        payload = {"heating_setpoint": 20.0, "dhw_unit": 3}
        result = partition_options(
            payload,
            known_writable_keys={"heating_setpoint"},
        )
        self.assertNotIn("dhw_unit", result.writable)
        self.assertIn("dhw_unit", result.dropped_unknown)
        self.assertEqual(result.status, ReadbackStatus.WARNING)
        codes = [w["code"] for w in result.warnings]
        self.assertIn(CODE_OPTION_NOT_EXPOSED, codes)

    def test_output_hvac_controllers_dropped_when_runtime_probe_denies_it(self) -> None:
        # Emulate a capability probe: a Mapping keyed by attribute name.
        probe = {"heating_setpoint": True, "output_HVAC_controllers": False}
        payload = {"heating_setpoint": 20.0, "output_HVAC_controllers": True}
        result = partition_options(payload, capability_probe=probe)
        self.assertNotIn("output_HVAC_controllers", result.writable)
        self.assertIn("output_HVAC_controllers", result.dropped_unknown)
        self.assertEqual(result.status, ReadbackStatus.WARNING)

    def test_missing_required_option_forces_fail_closed(self) -> None:
        payload = {"heating_setpoint": 20.0}
        result = partition_options(
            payload,
            required_keys={"heating_setpoint", "cooling_setpoint"},
        )
        self.assertEqual(result.status, ReadbackStatus.FAIL)
        self.assertEqual(result.missing_required, ("cooling_setpoint",))
        codes = [w["code"] for w in result.warnings]
        self.assertIn(CODE_OPTION_REQUIRED_MISSING, codes)

    def test_clean_payload_passes(self) -> None:
        payload = {"heating_setpoint": 20.0, "cooling_setpoint": 26.0}
        result = partition_options(
            payload,
            required_keys={"heating_setpoint", "cooling_setpoint"},
        )
        self.assertEqual(result.status, ReadbackStatus.PASS)
        self.assertEqual(result.writable, payload)
        self.assertEqual(result.warnings, ())


if __name__ == "__main__":
    unittest.main()
