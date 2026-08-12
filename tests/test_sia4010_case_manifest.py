"""Tests for the source-traced SIA 4010 class 1A/1B input manifest."""

import json
import unittest
from pathlib import Path

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.case_manifest import Sia4010CaseManifest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "sia4010_classes_1a_1b.json"
OUTPUT = ROOT / ".codex_tmp" / "sia4010_case_manifest"


class Sia4010CaseManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = Sia4010CaseManifest.load(MANIFEST)

    def test_exact_class_variants_are_pinned(self):
        self.assertEqual(
            list(self.manifest.class_readiness("1A")),
            ["test_1", "test_2A"],
        )
        self.assertEqual(
            list(self.manifest.class_readiness("1B")),
            ["test_1", "test_2B", "test_2C", "test_2D"],
        )

    def test_missing_controlled_sources_block_generation(self):
        readiness = self.manifest.variant_readiness("test_1")
        self.assertEqual(readiness.status, "BLOCKED_MISSING_INPUTS")
        self.assertIn("denver_drycold_weather_file", readiness.missing_parameters)
        self.assertNotIn(
            "iso_lightweight_construction", readiness.provisional_parameters
        )
        self.assertNotIn("iso_test1_glazing", readiness.provisional_parameters)
        self.assertNotIn("iso_test1_infiltration", readiness.provisional_parameters)

    def test_test1_readiness_is_case_specific(self):
        case_600 = self.manifest.case_readiness("test_1", "600")
        case_600ff = self.manifest.case_readiness("test_1", "600FF")
        case_1e = self.manifest.case_readiness("test_1", "1E")
        self.assertEqual(
            case_600.missing_parameters, ("denver_drycold_weather_file",)
        )
        self.assertNotIn(
            "iso_lightweight_construction", case_600.provisional_parameters
        )
        self.assertNotIn(
            "test1_night_setback_schedule", case_600.missing_parameters
        )
        self.assertNotIn(
            "test1_heating_setpoint_c", case_600ff.missing_parameters
        )
        self.assertNotIn("sia2024_office_profiles", case_1e.missing_parameters)
        self.assertIn(
            "zurich_kloten_dry_weather_file", case_1e.missing_parameters
        )
        self.assertNotIn("iso_test1_glazing", case_1e.missing_parameters)
        self.assertNotIn("denver_drycold_weather_file", case_1e.missing_parameters)

    def test_confirmed_values_are_available(self):
        self.assertEqual(self.manifest.value("cell_width_m"), 8.0)
        self.assertEqual(self.manifest.value("shading_activation_w_m2"), 150.0)

    def test_iso_values_are_normative(self):
        envelope = self.manifest.value("iso_lightweight_construction")
        self.assertIn("raised floor", envelope["boundary_condition"])
        self.assertEqual(
            envelope["floor_layers_outside_to_inside"][0]["density_kg_m3"], 0.0
        )
        glazing = self.manifest.value("iso_test1_glazing")
        self.assertEqual(glazing["whole_window_u_w_m2k"], 2.984)
        self.assertEqual(glazing["corrected_solar_energy_transmittance"], 0.71)
        readiness = self.manifest.case_readiness("test_1", "600")
        self.assertEqual(readiness.provisional_parameters, ())
        infiltration = self.manifest.value("iso_test1_infiltration")
        self.assertEqual(infiltration["air_changes_per_hour"], 0.41)

    def test_authority_supplied_office_profiles_are_source_traced(self):
        profiles = self.manifest.value("sia2024_office_profiles")
        self.assertEqual(profiles["use_category"], "3.1 Einzel-/Gruppenbüro")
        self.assertEqual(profiles["value_set"], "standard values")
        self.assertAlmostEqual(
            sum(profiles["source_hour_bins"]["occupancy"]), 7.2
        )
        self.assertAlmostEqual(
            sum(profiles["source_hour_bins"]["equipment"]), 11.1
        )
        self.assertAlmostEqual(
            sum(profiles["source_hour_bins"]["lighting"]), 11.1
        )
        self.assertEqual(profiles["rest_days_per_week"], 2)
        self.assertEqual(profiles["use_days_per_year"], 261)
        self.assertEqual(profiles["people_annual_simultaneity"], 0.8)
        self.assertEqual(
            profiles["native_ve_calendar_mapping_status"],
            "PENDING_EXACT_WEEKDAY_DATE_AND_HOUR_BOUNDARY_BINDING",
        )

    def test_every_parameter_has_required_metadata(self):
        for parameter in self.manifest.parameters.values():
            self.assertTrue(
                Sia4010CaseManifest.REQUIRED_PARAMETER_FIELDS <= set(parameter)
            )

    def test_class_matrix_mismatch_is_rejected(self):
        OUTPUT.mkdir(parents=True, exist_ok=True)
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        payload["classes"]["1A"] = ["test_1", "test_2"]
        path = OUTPUT / "bad_matrix.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(ConfigurationError):
            Sia4010CaseManifest.load(path)


if __name__ == "__main__":
    unittest.main()
