"""Tests for probe-qualified SIA 4010 ResultsReader extraction."""

import unittest
from pathlib import Path

from swiss_sia.reference_model.sia4010.expected_results import ExpectedResult
from swiss_sia.reference_model.sia4010.qualified_aps import (
    QualifiedApsBindings,
    Sia4010QualifiedApsExtractor,
    _hourly_average_watts,
    _hourly_energy_kwh,
)

ROOT = Path(__file__).resolve().parents[1]
BINDINGS = ROOT / "config" / "sia4010_aps_bindings_ve_runtime.json"


class _Results:
    results_per_day = 48

    def __init__(self):
        self.values = {
            "Room units heating load": [1.0] * 17520,
            "Room units cooling load": [0.5] * 17520,
            "Window solar gains": [0.2] * 17520,
            "Room air temperature": [20.0] * 17520,
            "Comfort temperature": [22.0] * 17520,
        }

    def get_variables(self):
        variables = {
            "Room units heating load": (
                "Heating plant sensible load",
                "power",
            ),
            "Room units cooling load": (
                "Cooling plant sensible load",
                "power",
            ),
            "Window solar gains": ("Solar gain", "power"),
            "Room air temperature": ("Air temperature", "temperature"),
            "Comfort temperature": (
                "Dry resultant temperature",
                "temperature",
            ),
        }
        return [
            {
                "aps_varname": key,
                "display_name": metadata[0],
                "model_level": "z",
                "units_type": metadata[1],
            }
            for key, metadata in variables.items()
        ]

    def get_units(self):
        return {
            "power": {
                "units_metric": {
                    "display_name": "kW",
                    "divisor": 1000.0,
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
        }

    def get_room_results(self, room_id, aps_var, vista_var, level):
        values = self.values[aps_var]
        if aps_var in {
            "Room units heating load",
            "Room units cooling load",
            "Window solar gains",
        }:
            # Raw ResultsReader values are watts; helper divides by 1000.
            return [value * 1000.0 for value in values]
        return values


def _expected(test_id, case_id, metric, unit="kWh"):
    return ExpectedResult(
        test_id=test_id,
        case_id=case_id,
        metric=metric,
        expected_value=0.0,
        unit=unit,
        absolute_tolerance=None,
        relative_tolerance=None,
        source_locator="official workbook",
        source_checksum="x",
    )


class QualifiedApsTests(unittest.TestCase):
    def setUp(self):
        self.bindings = QualifiedApsBindings.load(BINDINGS)
        self.extractor = Sia4010QualifiedApsExtractor(
            _Results(), "R1", self.bindings, "case.aps"
        )

    def test_half_hour_power_aggregates_to_hourly_energy_and_mean_power(self):
        self.assertEqual(_hourly_energy_kwh([1.0, 3.0], 2.0), (2.0,))
        self.assertEqual(_hourly_average_watts([1.0, 3.0], 2.0), (2000.0,))
        hourly = self.extractor.hourly_power_watts("total_room_solar_heat_gain_power")
        self.assertEqual(len(hourly), 8760)
        self.assertEqual(hourly[0], 200.0)

    def test_test1_monthly_annual_and_peak_values(self):
        expected = [
            _expected(
                "1",
                "1E",
                "Table 28 — Test results sensible energy needs for heating | 1",
            ),
            _expected(
                "1",
                "1E",
                "Table 28 — Test results sensible energy needs for heating | Annual",
            ),
            _expected(
                "1",
                "1E",
                "Table 31 — Test results Annual hourly integrated peak heating and cooling load | Heating",
                "kWh (peak)",
            ),
        ]
        observed = self.extractor.test1_observed(expected)
        self.assertEqual(len(observed), 3)
        self.assertEqual(observed[0].value, 31 * 24.0)
        self.assertEqual(observed[1].value, 365 * 24.0)
        self.assertEqual(observed[2].value, 1.0)

    def test_test1_reference_only_case_records_results_without_bands(self):
        observed = self.extractor.test1_reference_only_observed("600")
        self.assertEqual(len(observed), 88)
        self.assertTrue(all(item.case_id == "600" for item in observed))
        self.assertEqual(observed[0].value, 31 * 24.0)
        self.assertEqual(observed[12].value, 365 * 24.0)
        self.assertEqual(observed[26].value, 1.0)
        self.assertEqual(observed[27].value, 0.5)
        self.assertEqual(observed[-1].value, 22.0)

    def test_test1_free_float_uses_qualified_temperature_series(self):
        observed = self.extractor.test1_reference_only_observed("600FF")
        self.assertEqual(len(observed), 39)
        self.assertTrue(all(item.case_id == "600FF" for item in observed))
        self.assertEqual(observed[12].value, 22.0)
        self.assertEqual(observed[13].value, 22.0)
        self.assertEqual(observed[14].value, 22.0)
        self.assertTrue(all(item.unit == "°C" for item in observed))

    def test_test2_uses_only_solar_heat_gain_alternative(self):
        expected = [
            _expected("2", "Test 2 A", "Jahresenergie solarer Wärmeeintrag"),
            _expected(
                "2",
                "Test 2 A",
                "Jahresenergie total transmittierte Solarstrahlung",
            ),
        ]
        observed = self.extractor.test2_observed(expected)
        self.assertEqual(len(observed), 1)
        self.assertIn("solarer Wärmeeintrag", observed[0].metric)
        self.assertAlmostEqual(observed[0].value, 0.2 * 8760)

    def test_series_evidence_is_compact_and_source_identified(self):
        evidence = self.extractor.series_evidence(
            ("room_air_temperature", "operative_temperature")
        )
        self.assertEqual(
            set(evidence),
            {
                "room_air_temperature",
                "operative_temperature",
            },
        )
        self.assertEqual(evidence["room_air_temperature"]["count"], 17520)
        self.assertEqual(evidence["room_air_temperature"]["unit"], "°C")
        self.assertEqual(evidence["operative_temperature"]["mean"], 22.0)

    def test_changed_runtime_metadata_fails_closed(self):
        results = _Results()
        original = results.get_units

        def wrong_units():
            payload = original()
            payload["power"]["units_metric"]["display_name"] = "W"
            return payload

        results.get_units = wrong_units
        extractor = Sia4010QualifiedApsExtractor(results, "R1", self.bindings, "case.aps")
        self.assertEqual(extractor.power_series("sensible_heating_power"), ())


if __name__ == "__main__":
    unittest.main()
