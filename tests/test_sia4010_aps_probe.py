"""Pure-Python tests for the read-only APS binding probe."""

import unittest

from swiss_sia.reference_model.sia4010.aps_probe import (
    build_surface_inventory,
    inspect_results_reader,
    is_sia4010_candidate_variable,
)


class _Results:
    results_per_day = 24

    def get_variables(self):
        return [
            {
                "aps_varname": "QHEAT",
                "display_name": "Heating load",
                "model_level": "z",
                "units_type": "power",
            },
            {
                "aps_varname": "AIR_TEMP",
                "display_name": "Air temperature",
                "model_level": "z",
                "units_type": "temperature",
            },
            {
                "aps_varname": "SURFACE_SOLAR",
                "display_name": "External surface incident solar flux",
                "model_level": "s",
                "units_type": "irradiance",
            },
        ]

    def get_units(self):
        return {
            "power": {
                "units_metric": {
                    "display_name": "W",
                    "divisor": 1.0,
                    "offset": 0.0,
                }
            },
            "temperature": {
                "units_metric": {
                    "display_name": "°C",
                    "divisor": 1.0,
                    "offset": 0.0,
                }
            },
            "irradiance": {
                "units_metric": {
                    "display_name": "W/m²",
                    "divisor": 1.0,
                    "offset": 0.0,
                }
            },
        }

    def get_room_list(self):
        return [{"name": "CELL", "id": "R1", "area": 48.0}]

    def get_room_results(self, room_id, aps_var, vista_var, level):
        if aps_var == "QHEAT":
            return [0.0, 100.0, 200.0]
        if aps_var == "AIR_TEMP":
            return [20.0, 20.5, 21.0]
        return []

    def get_surface_results(
        self,
        room_id,
        aps_handle,
        aps_var,
        vista_var,
    ):
        if room_id == "R1" and aps_handle == 77 and aps_var == "SURFACE_SOLAR":
            return [0.0, 300.0, 500.0]
        return []


class _Surface:
    id = "S1"
    name = "SOUTH_WALL"

    @staticmethod
    def get_properties():
        return {
            "aps_handle": 77,
            "type": "ExternalWall",
            "orientation": 180.0,
            "tilt": 90.0,
        }

    @staticmethod
    def get_openings():
        return [object()]


class _Body:
    id = "R1"
    name = "CELL"

    @staticmethod
    def get_surfaces():
        return [_Surface()]


class _Model:
    @staticmethod
    def get_bodies(selected_only):
        if selected_only:
            raise AssertionError("whole model required")
        return [_Body()]


class _Project:
    models = [_Model()]


class Sia4010ApsProbeTests(unittest.TestCase):
    def test_candidate_filter_includes_required_load_and_temperature_physics(self):
        self.assertTrue(
            is_sia4010_candidate_variable(
                {"aps_varname": "QHEAT", "display_name": "Heating load"}
            )
        )
        self.assertTrue(
            is_sia4010_candidate_variable(
                {"aps_varname": "AIR_TEMP", "display_name": "Air temperature"}
            )
        )
        self.assertFalse(
            is_sia4010_candidate_variable(
                {"aps_varname": "FAN_SPEED", "display_name": "Fan speed"}
            )
        )

    def test_probe_reports_metadata_and_series_summary(self):
        report = inspect_results_reader(_Results(), "case.aps")
        self.assertEqual(report["status"], "READY_FOR_BINDING_REVIEW")
        self.assertEqual(report["candidate_variable_count"], 3)
        rows = {row["aps_varname"]: row for row in report["candidate_variables"]}
        self.assertEqual(rows["QHEAT"]["metric_unit"], "W")
        self.assertEqual(rows["QHEAT"]["room_series"][0]["series"]["maximum"], 200.0)
        self.assertEqual(rows["AIR_TEMP"]["metric_unit"], "°C")
        self.assertEqual(rows["AIR_TEMP"]["room_series"][0]["series"]["maximum"], 21.0)
        self.assertNotIn("full_series", rows["QHEAT"])
        self.assertEqual(
            report["surface_binding_status"],
            "SURFACE_SERIES_NOT_DEMONSTRATED",
        )

    def test_probe_reads_surface_series_only_from_exact_aps_handle(self):
        inventory = build_surface_inventory(_Project())
        self.assertEqual(len(inventory), 1)
        self.assertEqual(inventory[0]["aps_handle"], 77)
        report = inspect_results_reader(
            _Results(),
            "case.aps",
            surface_inventory=inventory,
        )
        self.assertEqual(
            report["surface_binding_status"],
            "READY_FOR_SURFACE_BINDING_REVIEW",
        )
        self.assertEqual(report["surface_series_count"], 1)
        rows = {row["aps_varname"]: row for row in report["candidate_variables"]}
        evidence = rows["SURFACE_SOLAR"]["surface_series"][0]
        self.assertEqual(evidence["surface_name"], "SOUTH_WALL")
        self.assertEqual(evidence["opening_count"], 1)
        self.assertEqual(evidence["series"]["maximum"], 500.0)


if __name__ == "__main__":
    unittest.main()
