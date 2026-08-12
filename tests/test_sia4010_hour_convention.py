"""Tests for fail-closed APS/EPW hour-convention diagnostics."""

import unittest
from pathlib import Path

from swiss_sia.reference_model.sia4010.hour_convention import (
    aggregate_hourly_means,
    build_hour_convention_diagnostic,
    compare_hour_alignments,
    read_epw_dry_bulb_c,
)


class HourConventionTests(unittest.TestCase):
    def test_aggregate_hourly_means(self):
        values = []
        for hour in range(8760):
            values.extend((float(hour), float(hour + 2)))
        hourly = aggregate_hourly_means(values, 2.0)
        self.assertEqual(len(hourly), 8760)
        self.assertEqual(hourly[0], 1.0)
        self.assertEqual(hourly[-1], 8760.0)

    def test_alignment_reports_positive_aps_index_offset(self):
        epw = tuple(float(index % 97) for index in range(8760))
        aps = (999.0,) + epw[:-1]
        alignments = compare_hour_alignments(epw, aps)
        self.assertEqual(alignments[0].aps_index_offset_hours, 1)
        self.assertEqual(alignments[0].root_mean_square_difference_c, 0.0)
        diagnostic = build_hour_convention_diagnostic(epw, aps, 1.0)
        self.assertEqual(
            diagnostic["status"],
            "NONZERO_APS_INDEX_OFFSET_REQUIRES_BINDING_REVIEW",
        )
        self.assertFalse(diagnostic["compliance_claim_allowed"])

    def test_zero_offset_is_reported_without_reindexing(self):
        epw = tuple(float(index % 31) for index in range(8760))
        diagnostic = build_hour_convention_diagnostic(epw, epw, 1.0)
        self.assertEqual(
            diagnostic["status"],
            "APS_INDEX_ALIGNS_WITH_EPW_FILE_ORDER",
        )
        self.assertEqual(
            diagnostic["best_alignment"]["aps_index_offset_hours"], 0
        )

    def test_epw_reader_requires_complete_year(self):
        directory = (
            Path(__file__).resolve().parents[1]
            / ".codex_tmp"
            / "hour_convention"
        )
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "incomplete_weather.epw"
        header = ["header"] * 8
        rows = ["2011,1,1,1,60,0,12.5"]
        path.write_text("\n".join(header + rows), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Expected 8760"):
            read_epw_dry_bulb_c(path)


if __name__ == "__main__":
    unittest.main()
