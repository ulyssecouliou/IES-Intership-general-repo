"""Tests for the source-traced Test 2A fabric-awning control contract."""

import unittest

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.test2a_shading_control import (
    DYNAMIC_EQUIVALENCE_BLOCKERS,
    FIXED_CLOSED_OUTPUT_BLOCKERS,
    build_test2a_fabric_awning_control,
    build_test2a_optical_diagnostic_contract,
)


def _official_inputs():
    return {
        "external_shading_activation_w_m2": 150.0,
        "variant_2A_shade": "Soltis 92-2048-Alu fabric awning",
        "variant_2A_combined_g_total": 0.059,
        "variant_2A_direct_solar_transmittance": 0.04,
        "variant_2A_outside_solar_reflectance": 0.49,
        "variant_2A_inside_solar_reflectance": 0.456,
        "variant_2A_visible_transmittance": 0.058,
        "variant_2A_outside_visible_reflectance": 0.496,
        "variant_2A_inside_visible_reflectance": 0.395,
        "variant_2A_convection_factor": 0.006,
        "variant_2A_thermal_radiation_factor": 0.013,
        "variant_2A_ventilation_factor": 0.0,
        "variant_2A_secondary_internal_heat_transfer_factor": 0.019,
        "variant_2A_uv_transmittance": 0.012,
        "variant_2A_reference_combined_g_total": 0.056,
        "variant_2A_reference_u_w_m2k": 0.574,
        "variant_2A_iso15099_winter_u_w_m2k": 0.582,
        "variant_2A_peripheral_gap_m": 0.01,
        "variant_2A_screen_layer_thickness_m": 0.0005,
    }


class Test2AShadingControlTests(unittest.TestCase):
    """The normative rule and the VE setter candidate remain distinct."""

    def test_uses_authority_confirmed_control_semantics(self):
        control = build_test2a_fabric_awning_control(_official_inputs())
        self.assertEqual(control.threshold_w_m2, 150.0)
        self.assertEqual(
            control.signal,
            "total_solar_irradiance_incident_on_exterior_glazing_plane",
        )
        self.assertEqual(control.active_operator, ">=")
        self.assertEqual(control.inactive_operator, "<")
        self.assertFalse(control.hysteresis_required)
        self.assertEqual(
            control.setter_plan,
            {
                "external_shade_active": True,
                "external_shade_radiation_to_lower": 150.0,
                "external_shade_radiation_to_raise": 150.0,
            },
        )
        self.assertFalse(control.dynamic_equivalence_qualified)
        self.assertEqual(
            control.fixed_closed_candidate_setter_plan,
            {
                "external_shade_active": True,
                "external_shade_profile": "ON",
                "external_shade_transmittance_0": 0.04,
            },
        )
        self.assertAlmostEqual(
            control.direct_solar_transmittance
            + control.secondary_internal_heat_transfer_factor,
            control.combined_g_total,
        )
        self.assertAlmostEqual(
            control.convection_factor
            + control.thermal_radiation_factor
            + control.ventilation_factor,
            control.secondary_internal_heat_transfer_factor,
        )
        self.assertEqual(
            control.dynamic_equivalence_blockers, DYNAMIC_EQUIVALENCE_BLOCKERS
        )
        self.assertNotIn(
            "SIA4010_TEST2A_THRESHOLD_COMPARISON_OPERATOR_NOT_CONFIRMED",
            control.dynamic_equivalence_blockers,
        )

    def test_payload_never_upgrades_setter_plan_to_dynamic_equivalence(self):
        payload = build_test2a_fabric_awning_control(_official_inputs()).to_dict()
        self.assertFalse(payload["dynamic_equivalence_qualified"])
        self.assertEqual(
            payload["setter_plan_scope"], "AUTHORITY_CONFIRMED_IESVE_MAPPING"
        )
        self.assertEqual(
            payload["confirmed_normative_control"]["threshold_w_m2"],
            150.0,
        )
        self.assertEqual(payload["unresolved_normative_semantics"], {})
        self.assertEqual(
            payload["confirmed_normative_control"]["activation_operator"],
            ">=",
        )
        self.assertIn("authority confirmed", payload["claim_guardrail"].lower())
        self.assertEqual(
            payload["fixed_closed_setter_plan_scope"],
            "VE2025_DOCUMENTED_WRITABLE_SUBSET_STORAGE_AND_READBACK_ONLY",
        )
        self.assertIn(
            "VE2025_CDB_EXTERNAL_SHADE_SOLAR_REFLECTANCE_SETTER_UNAVAILABLE",
            payload["fixed_closed_output_blockers"],
        )
        self.assertEqual(
            tuple(payload["fixed_closed_output_blockers"]),
            FIXED_CLOSED_OUTPUT_BLOCKERS,
        )

    def test_missing_source_value_fails_closed(self):
        values = _official_inputs()
        del values["variant_2A_combined_g_total"]
        with self.assertRaisesRegex(ConfigurationError, "missing"):
            build_test2a_fabric_awning_control(values)

    def test_unphysical_fraction_fails_closed(self):
        values = _official_inputs()
        values["variant_2A_visible_transmittance"] = 1.2
        with self.assertRaisesRegex(ConfigurationError, "outside"):
            build_test2a_fabric_awning_control(values)

    def test_inconsistent_summer_g_identity_fails_closed(self):
        values = _official_inputs()
        values["variant_2A_secondary_internal_heat_transfer_factor"] = 0.02
        with self.assertRaisesRegex(ConfigurationError, "optical identity"):
            build_test2a_fabric_awning_control(values)

    def test_2e1_contract_requires_output_evidence_not_a_ratio_guess(self):
        control = build_test2a_fabric_awning_control(_official_inputs())
        diagnostic = build_test2a_optical_diagnostic_contract(control)
        payload = diagnostic.to_dict()
        self.assertEqual(payload["diagnostic_case_id"], "2E1")
        self.assertEqual(payload["protection_state"], "ALWAYS_CLOSED")
        self.assertFalse(payload["qualification_ready"])
        self.assertFalse(payload["dynamic_control_qualified"])
        self.assertIsNone(payload["candidate_transmission_factor"])
        self.assertEqual(
            payload["summer_optical_identities"]["g_total"],
            0.059,
        )
        self.assertIn(
            "hourly_room_solar_heat_gain_secondary",
            payload["result_series"],
        )

    def test_2e1_bound_schema_closes_only_the_workbook_blocker(self):
        control = build_test2a_fabric_awning_control(_official_inputs())
        binding = {
            "status": "OFFICIAL_2E1_SCHEMA_BOUND",
            "workbook_sha256": "a" * 64,
            "series": [],
        }
        diagnostic = build_test2a_optical_diagnostic_contract(
            control,
            binding,
        )
        payload = diagnostic.to_dict()
        self.assertEqual(
            payload["workbook_binding_status"],
            "OFFICIAL_2E1_SCHEMA_BOUND",
        )
        self.assertEqual(payload["official_workbook_binding"], binding)
        self.assertEqual(
            payload["technical_reference_comparison"]["status"],
            "AVAILABLE_NO_ACCEPTANCE_CRITERION",
        )
        self.assertFalse(
            payload["technical_reference_comparison"]["acceptance_criterion_available"]
        )
        self.assertNotIn(
            "OFFICIAL_TEST2_DIAGNOSTIC_2E1_SERIES_NOT_BOUND",
            payload["blockers"],
        )
        self.assertIn(
            "VE_TEST2A_FIXED_CLOSED_OPTICAL_MAPPING_NOT_QUALIFIED",
            payload["blockers"],
        )
        self.assertFalse(payload["qualification_ready"])


if __name__ == "__main__":
    unittest.main()
