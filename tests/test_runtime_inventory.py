"""Tests for the read-only VE/APS runtime inventory."""

from __future__ import annotations

import unittest

from swiss_sia.runtime_inventory import build_aps_variable_inventory, json_safe
from swiss_sia.simulation_results import find_room_sensible_load_variable


class _SimulationResults:
    """Minimal finder implementation matching production token semantics."""

    @staticmethod
    def find_first_aps_variable(variables, token_sets, level):
        for token_set in token_sets:
            for variable in variables:
                model_level = str(variable.get("model_level") or "").lower()
                text = "{} {}".format(
                    variable.get("aps_varname", ""),
                    variable.get("display_name", ""),
                ).lower()
                if model_level == level and all(token in text for token in token_set):
                    return (
                        variable.get("aps_varname", ""),
                        variable.get("display_name", ""),
                        model_level,
                        variable.get("resolved_metric_unit", ""),
                        1.0,
                        0.0,
                    )
        return None

    @staticmethod
    def find_room_sensible_load_variable(variables, mode):
        """Delegate preferred sensible-load selection to production code."""
        return find_room_sensible_load_variable(variables, mode)


class RuntimeInventoryTests(unittest.TestCase):
    """Verify bounded serialization and exact APS binding evidence."""

    def test_json_safe_normalizes_mapping_keys_and_unknown_values(self) -> None:
        """VE enums and indexed dictionaries must remain reportable."""
        value = json_safe({0: object(), "rows": (1, 2)})
        self.assertEqual(value["rows"], [1, 2])
        self.assertIsInstance(value["0"], str)

    def test_aps_inventory_separates_bound_and_related_variables(self) -> None:
        """Nearby variables must be visible even when production cannot bind them."""
        variables = [
            {
                "aps_varname": "QCL",
                "display_name": "Room cooling load",
                "model_level": "z",
                "resolved_metric_unit": "kW",
            },
            {
                "aps_varname": "FAN_SYS",
                "display_name": "System fan power",
                "model_level": "s",
                "resolved_metric_unit": "kW",
            },
        ]
        report = build_aps_variable_inventory(variables, _SimulationResults)

        self.assertIsNotNone(report["production_bindings"]["cooling_load"])
        self.assertIsNone(report["production_bindings"]["heating_load"])
        self.assertIn("fan", report["unresolved_bindings"])
        self.assertEqual(report["related_variable_count"], 2)

    def test_sensible_heating_load_wins_over_steady_state_series(self) -> None:
        """Catalog ordering must not bind the steady-state heating series."""
        variables = [
            {
                "aps_varname": "Room units steady state htg load",
                "display_name": "Steady state heating plant load",
                "model_level": "z",
                "resolved_metric_unit": "kW",
            },
            {
                "aps_varname": "Room units heating load",
                "display_name": "Heating plant sensible load",
                "model_level": "z",
                "resolved_metric_unit": "kW",
            },
        ]

        binding = find_room_sensible_load_variable(variables, "heating")

        self.assertIsNotNone(binding)
        self.assertEqual(binding[0], "Room units heating load")


if __name__ == "__main__":
    unittest.main()
