"""Tests for executable ISO 52016-1 Test 1 reference metrics."""

import unittest
from pathlib import Path

from swiss_sia.reference_model.sia4010.test1_iso_reference import (
    load_test1_iso_reference_results,
)


ROOT = Path(__file__).resolve().parents[1]


class Test1IsoReferenceTests(unittest.TestCase):
    def test_conditioned_cases_expose_all_available_iso_comparisons(self):
        for case_id in ("600", "640", "900", "940"):
            expected = load_test1_iso_reference_results(ROOT, case_id)
            self.assertEqual(len(expected), 64)
            self.assertTrue(all(item.case_id == case_id for item in expected))
            self.assertTrue(all(item.absolute_tolerance is None for item in expected))
            self.assertTrue(all(item.relative_tolerance is None for item in expected))

    def test_free_float_cases_expose_complete_reference_scope(self):
        for case_id in ("600FF", "900FF"):
            expected = load_test1_iso_reference_results(ROOT, case_id)
            self.assertEqual(len(expected), 39)

    def test_table_33_published_integer_scale_is_applied(self):
        expected = load_test1_iso_reference_results(ROOT, "600")
        hour_one = next(
            item
            for item in expected
            if item.metric.endswith("January 4 | 1")
        )
        self.assertEqual(hour_one.expected_value, 4.189)
        self.assertEqual(hour_one.unit, "kWh")

    def test_reference_annual_values_match_iso_table(self):
        expected = load_test1_iso_reference_results(ROOT, "600")
        by_metric = {item.metric: item for item in expected}
        self.assertEqual(
            by_metric[
                "Table 28 — Test results sensible energy needs for heating | Annual"
            ].expected_value,
            5133.0,
        )
        self.assertEqual(
            by_metric[
                "Table 29 — Test results sensible energy needs for cooling | Annual"
            ].expected_value,
            7503.0,
        )


if __name__ == "__main__":
    unittest.main()
