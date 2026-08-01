"""Tests for the deterministic TMY1-to-EPW conversion helpers."""

import unittest

from swiss_sia.reference_model.sia4010.weather_conversion import (
    _RawTmy1,
    _relative_humidity,
    _solar_components,
)


class WeatherConversionTests(unittest.TestCase):
    def test_relative_humidity_is_bounded(self):
        self.assertEqual(_relative_humidity(20.0, 20.0), 100)
        self.assertGreater(_relative_humidity(20.0, 0.0), 0)
        self.assertLess(_relative_humidity(20.0, 0.0), 100)

    def test_solar_components_preserve_global_horizontal(self):
        record = _RawTmy1(
            station_id="23062",
            month=6,
            day=21,
            hour_ending=13,
            dry_bulb_c=25.0,
            dew_point_c=5.0,
            pressure_pa=83000,
            wind_direction_degrees=180,
            wind_speed_m_s=2.0,
            total_cloud_tenths=0,
            global_horizontal_w_m2=800.0,
            direct_normal_w_m2=700.0,
            diffuse_horizontal_w_m2=None,
        )
        ghi, dni, dhi = _solar_components(record)
        self.assertEqual(ghi, 800.0)
        self.assertGreaterEqual(dni, 0.0)
        self.assertGreaterEqual(dhi, 0.0)

    def test_nighttime_components_are_safe(self):
        record = _RawTmy1(
            station_id="23062",
            month=1,
            day=1,
            hour_ending=1,
            dry_bulb_c=0.0,
            dew_point_c=-6.6,
            pressure_pa=82780,
            wind_direction_degrees=203,
            wind_speed_m_s=2.8,
            total_cloud_tenths=7,
            global_horizontal_w_m2=0.0,
            direct_normal_w_m2=None,
            diffuse_horizontal_w_m2=None,
        )
        self.assertEqual(_solar_components(record), (0.0, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
