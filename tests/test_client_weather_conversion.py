"""Tests for source-traced client weather EPW reconstruction."""

import unittest
from datetime import datetime

from swiss_sia.reference_model.client_weather_conversion import (
    _standard_pressure_pa,
    ClientWeatherRecord,
    _combine_records,
    _dew_point_c,
    _epw_record,
    _parse_client_epw_transport,
)
from swiss_sia.reference_model.exceptions import ConfigurationError


class ClientWeatherConversionTests(unittest.TestCase):
    def _record(self):
        return ClientWeatherRecord(
            timestamp=datetime(2035, 6, 21, 11),
            dry_bulb_c=19.3,
            relative_humidity_percent=78.6,
            wind_speed_m_s=3.7,
            wind_direction_degrees=180.0,
            total_sky_cover_percent=88.0,
            global_horizontal_w_m2=376.0,
            diffuse_horizontal_w_m2=353.0,
            direct_normal_w_m2=25.0,
            pressure_pa=95260.0,
            source_flags="CLIENT",
        )

    def test_noaa_dew_point_is_physical(self):
        dew_point = _dew_point_c(20.0, 50.0)
        self.assertAlmostEqual(dew_point, 9.27, places=1)
        self.assertLessEqual(dew_point, 20.0)

    def test_standard_pressure_uses_station_elevation(self):
        pressure = _standard_pressure_pa(411.0)
        self.assertGreater(pressure, 90000.0)
        self.assertLess(pressure, 101325.0)

    def test_epw_record_has_complete_standard_mapping(self):
        fields = _epw_record(self._record())
        self.assertEqual(len(fields), 35)
        self.assertEqual(fields[3:5], [12, 60])
        self.assertEqual(fields[13:16], [376, 25, 353])
        self.assertEqual(fields[22:24], [9, 9])
        self.assertGreater(fields[12], 0)

    def test_client_epw_defects_are_recorded_not_silently_accepted(self):
        header = ["HEADER"] * 8
        fields = [
            "2035", "1", "1", "1", "0", "FLAGS", "3.3", "0",
            "92.8", "95290", "0", "0", "0", "0", "0", "0",
            "0", "0", "0", "0", "89.1", "2.5", "0.93", "0",
            "0", "0", "0", "0", "0", "0", "0", "0", "",
        ]
        inherited, defects = _parse_client_epw_transport(
            "\n".join(header + [",".join(fields)])
        )
        self.assertEqual(len(inherited), 1)
        self.assertEqual(defects["field_count_distribution"], {"33": 1})
        self.assertEqual(defects["expected_field_count"], 35)

    def test_csv_and_epw_hour_mismatch_is_rejected(self):
        row = {
            "time.yy": "2035",
            "time.mm": "1",
            "time.dd": "1",
            "time.hh": "0",
            "tre200h0": "3.3",
            "ure200h0": "92.8",
            "fkl010h0": "2.5",
            "dkl010h0": "89.1",
            "skycover": "93",
            "gls": "0",
            "str.diffus": "0",
            "str.direkt": "0",
        }
        with self.assertRaises(ConfigurationError):
            _combine_records(
                [row],
                [(datetime(2035, 1, 1, 1), 95290.0, "FLAGS")],
            )


if __name__ == "__main__":
    unittest.main()
