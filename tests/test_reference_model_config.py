"""Tests for strict, source-traced reference-model configuration."""

import json
import unittest
from pathlib import Path

from swiss_sia.reference_model.compliance_config import (
    SIA3802_TABLE2,
    SIA3802_TABLE3,
    build_default_registry,
)
from swiss_sia.reference_model.config_loader import load_configuration
from swiss_sia.reference_model.exceptions import ConfigurationError

TEST_ROOT = Path(__file__).resolve().parents[1]
TEST_OUTPUT_ROOT = TEST_ROOT / ".codex_tmp" / "reference_model_tests"


def _test_dir(name):
    path = TEST_OUTPUT_ROOT / name
    path.mkdir(parents=True, exist_ok=True)
    return path


class ReferenceModelConfigurationTests(unittest.TestCase):
    def test_every_parameter_has_required_metadata(self):
        registry = build_default_registry()
        self.assertGreater(len(list(registry)), 40)
        for parameter in registry:
            self.assertTrue(parameter.name)
            self.assertTrue(parameter.description)
            self.assertTrue(parameter.units)
            self.assertTrue(parameter.source)
            self.assertTrue(parameter.source_locator)
            self.assertTrue(parameter.validation_range.expected_type)

    def test_default_registry_is_fail_closed_for_ve_mutation(self):
        unresolved = {
            parameter.name for parameter in build_default_registry().unresolved_required()
        }
        self.assertEqual(
            unresolved,
            {
                "external_wall_construction_id",
                "roof_construction_id",
                "ground_floor_construction_id",
                "internal_wall_construction_id",
                "door_construction_id",
                "glazing_construction_id",
                "weather_file",
                "thermal_template_name",
                "thermal_template_source_record",
            },
        )

    def test_compliance_value_override_requires_provenance(self):
        registry = build_default_registry()
        with self.assertRaises(ConfigurationError):
            registry.with_overrides({"project_external_wall_u_w_m2k": 0.2})
        configured = registry.with_overrides(
            {
                "project_external_wall_u_w_m2k": {
                    "value": 0.2,
                    "source": "Approved project construction calculation",
                    "source_locator": "Envelope schedule W-01",
                }
            }
        )
        parameter = configured.get_parameter("project_external_wall_u_w_m2k")
        self.assertEqual(parameter.value, 0.2)
        self.assertFalse(parameter.is_placeholder)

    def test_unknown_parameter_and_out_of_range_values_are_rejected(self):
        registry = build_default_registry()
        with self.assertRaises(ConfigurationError):
            registry.with_overrides({"invented_threshold": 1})
        with self.assertRaises(ConfigurationError):
            registry.with_overrides({"building_width_m": -5})

    def test_example_configuration_is_parseable_and_keeps_placeholders(self):
        example = Path(__file__).resolve().parents[1] / "config" / "reference_model.example.json"
        registry = load_configuration(example)
        self.assertIsNone(registry.value("weather_file"))
        self.assertTrue(registry.get_parameter("weather_file").is_placeholder)

    def test_sia3802_reference_constants_are_pinned_to_source(self):
        """Pin value + source table + PDF locator for every SIA 380/2 reference constant.

        Verified against SIA 380/2:2022 FR: opaque construction U-values are in
        Table 3 (PDF p. 36); window U-value, glazing g-value and light
        transmittance are in Table 2 (PDF p. 32). This guards the audit trail
        against silent value drift or a re-introduced table/page mis-citation.
        """
        registry = build_default_registry()
        expected = {
            "sia3802_reference_external_wall_u_w_m2k": (0.20, SIA3802_TABLE3, "SIA 380/2:2022 FR, PDF pp. 36-37"),
            "sia3802_reference_roof_u_w_m2k": (0.20, SIA3802_TABLE3, "SIA 380/2:2022 FR, PDF pp. 36-37"),
            "sia3802_reference_ground_floor_u_w_m2k": (0.30, SIA3802_TABLE3, "SIA 380/2:2022 FR, PDF pp. 36-37"),
            "sia3802_reference_window_u_w_m2k": (1.10, SIA3802_TABLE2, "SIA 380/2:2022 FR, Table 2, PDF p. 32"),
            "sia3802_reference_glazing_g_value": (0.50, SIA3802_TABLE2, "SIA 380/2:2022 FR, Table 2, PDF p. 32"),
            "sia3802_reference_light_transmittance": (0.70, SIA3802_TABLE2, "SIA 380/2:2022 FR, Table 2, PDF p. 32"),
        }
        for name, (value, source, locator) in expected.items():
            parameter = registry.get_parameter(name)
            self.assertEqual(parameter.value, value, name)
            self.assertEqual(parameter.source, source, name)
            self.assertEqual(parameter.source_locator, locator, name)
            self.assertTrue(parameter.comparison_only, name)

    def test_sia4010_target_validation_class_allows_only_official_classes(self):
        registry = build_default_registry()
        parameter = registry.get_parameter("sia4010_target_validation_class")
        self.assertEqual(
            tuple(parameter.validation_range.allowed_values),
            ("1A", "1B", "2A", "2B", "3", "4A", "4B", "5"),
        )
        self.assertTrue(parameter.is_placeholder)

    def test_loader_rejects_unknown_top_level_fields(self):
        path = _test_dir("config_unknown_field") / "bad.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "parameters": {},
                    "silent_compliance_assumption": True,
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaises(ConfigurationError):
            load_configuration(path)


if __name__ == "__main__":
    unittest.main()
