"""SIA 180:2014 figure-4 comfort band + 48h running mean (production module)."""

from __future__ import annotations

import io
import json
import os
import unittest

from swiss_sia.reference_model import sia180_comfort as sc


class Sia180ComfortTests(unittest.TestCase):
    def test_vertices_come_from_the_frozen_source(self):
        with io.open(sc._FIGURE1_PATH, encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual(
            sc._UPPER_VERTICES,
            [tuple(map(float, v)) for v in data["courbes"]["limite_superieure"]["sommets"]],
        )
        self.assertEqual(
            sc._LOWER_VERTICES,
            [tuple(map(float, v)) for v in data["courbes"]["limite_inferieure"]["sommets"]],
        )
        self.assertEqual(sc.DOMAIN, (10.0, 25.0))

    def test_upper_curve_matches_known_points(self):
        self.assertAlmostEqual(sc.upper_limit(12.0), 24.5)
        self.assertAlmostEqual(sc.upper_limit(17.5), 26.5)
        self.assertAlmostEqual(sc.upper_limit(14.75), 25.5)   # segment midpoint
        self.assertAlmostEqual(sc.upper_limit(5.0), 24.5)     # clamp below domain
        self.assertAlmostEqual(sc.upper_limit(30.0), 26.5)    # clamp above domain

    def test_lower_curve_matches_known_points(self):
        self.assertAlmostEqual(sc.lower_limit(19.0), 20.5)
        self.assertAlmostEqual(sc.lower_limit(23.5), 22.0)
        self.assertAlmostEqual(sc.lower_limit(21.25), 21.25)  # segment midpoint
        self.assertAlmostEqual(sc.lower_limit(5.0), 20.5)     # clamp below domain

    def test_rolling_mean_uses_a_48h_window_in_timesteps(self):
        # 96 half-hourly steps of 20 °C then a jump; the running mean lags.
        exterior = [20.0] * 96 + [30.0]
        theta = sc.rolling_mean(exterior, results_per_hour=2.0)
        self.assertAlmostEqual(theta[0], 20.0)
        self.assertAlmostEqual(theta[95], 20.0)
        # step 96 averages 95x20 + 1x30 over the 96-step window
        self.assertAlmostEqual(theta[96], (95 * 20.0 + 30.0) / 96.0)

    def test_missing_values_do_not_break_the_mean(self):
        theta = sc.rolling_mean([None, None, 22.0], results_per_hour=1.0)
        self.assertIsNone(theta[0])
        self.assertAlmostEqual(theta[2], 22.0)

    def test_comfort_limit_series_aligns_and_fails_closed(self):
        exterior = [None] + [22.0] * 96
        upper, lower = sc.comfort_limit_series(exterior, results_per_hour=2.0)
        self.assertEqual(len(upper), len(exterior))
        self.assertIsNone(upper[0])
        # theta_rm ~22 -> upper between the 17.5 and 25 plateau (26.5)
        self.assertAlmostEqual(upper[-1], 26.5)
        self.assertAlmostEqual(lower[-1], sc.lower_limit(22.0))


if __name__ == "__main__":
    unittest.main()
