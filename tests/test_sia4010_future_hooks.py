"""Tests for conservative future SIA 4010 integration contracts."""

import unittest

from swiss_sia.reference_model.sia4010.compliance_comparator import (
    ComparisonStatus,
    Sia4010ComplianceComparator,
)
from swiss_sia.reference_model.sia4010.expected_results import (
    ExpectedResult,
    ObservedResult,
)


def _expected(absolute=None, relative=None):
    return ExpectedResult(
        test_id="1",
        case_id="CASE-01",
        metric="annual_energy",
        expected_value=100.0,
        unit="kWh",
        absolute_tolerance=absolute,
        relative_tolerance=relative,
        source_locator="Official workbook cell X",
        source_checksum="abc123",
    )


def _expected_band(lower, upper, mean=100.0, absolute=None):
    return ExpectedResult(
        test_id="1",
        case_id="CASE-01",
        metric="annual_energy",
        expected_value=mean,
        unit="kWh",
        absolute_tolerance=absolute,
        relative_tolerance=None,
        source_locator="Official workbook Zusammenfassung",
        source_checksum="abc123",
        lower_bound=lower,
        upper_bound=upper,
    )


def _observed(value=100.0, unit="kWh"):
    return ObservedResult(
        test_id="1",
        case_id="CASE-01",
        metric="annual_energy",
        value=value,
        unit=unit,
        evidence_locator="VE APS extract row 1",
    )


class Sia4010FutureHookTests(unittest.TestCase):
    def setUp(self):
        self.comparator = Sia4010ComplianceComparator()

    def test_missing_official_tolerance_is_not_checkable(self):
        outcome = self.comparator.compare_one(_expected(), _observed())
        self.assertEqual(outcome.status, ComparisonStatus.NOT_CHECKABLE)
        self.assertIn("no tolerance was invented", outcome.message)

    def test_source_provided_absolute_tolerance_controls_pass_fail(self):
        self.assertEqual(
            self.comparator.compare_one(_expected(absolute=1.0), _observed(100.5)).status,
            ComparisonStatus.PASS,
        )
        self.assertEqual(
            self.comparator.compare_one(
                _expected(absolute=1.0), _observed(101.01)
            ).status,
            ComparisonStatus.FAIL,
        )

    def test_unit_mismatch_is_not_implicitly_converted(self):
        outcome = self.comparator.compare_one(
            _expected(absolute=1.0), _observed(0.1, "MWh")
        )
        self.assertEqual(outcome.status, ComparisonStatus.NOT_CHECKABLE)

    def test_official_band_accepts_value_within_bounds(self):
        outcome = self.comparator.compare_one(
            _expected_band(90.0, 110.0), _observed(100.0)
        )
        self.assertEqual(outcome.status, ComparisonStatus.PASS)
        self.assertEqual(outcome.lower_bound, 90.0)
        self.assertEqual(outcome.upper_bound, 110.0)
        self.assertIn("within the official reference band", outcome.message)

    def test_official_band_rejects_value_below_and_above_bounds(self):
        self.assertEqual(
            self.comparator.compare_one(
                _expected_band(90.0, 110.0), _observed(89.9)
            ).status,
            ComparisonStatus.FAIL,
        )
        self.assertEqual(
            self.comparator.compare_one(
                _expected_band(90.0, 110.0), _observed(110.1)
            ).status,
            ComparisonStatus.FAIL,
        )

    def test_band_takes_precedence_over_tolerance(self):
        # Observed is within the band but far outside a (tighter) tolerance:
        # the official band must decide, so the outcome is PASS.
        outcome = self.comparator.compare_one(
            _expected_band(90.0, 110.0, absolute=0.5), _observed(108.0)
        )
        self.assertEqual(outcome.status, ComparisonStatus.PASS)

    def test_band_still_requires_matching_units(self):
        outcome = self.comparator.compare_one(
            _expected_band(90.0, 110.0), _observed(100.0, "MWh")
        )
        self.assertEqual(outcome.status, ComparisonStatus.NOT_CHECKABLE)


if __name__ == "__main__":
    unittest.main()
