"""Tests for the checksum-qualified official Test 2 diagnostic binding."""

import unittest
from pathlib import Path

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.test2a_diagnostic_workbook import (
    EXPECTED_TEST2_WORKBOOK_SHA256,
    load_test2a_diagnostic_workbook_binding,
)

ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "SIA_4010_geteilter_Link" / "Test2" / "Resultaterfassung_Test2.xlsx"


@unittest.skipUnless(WORKBOOK.is_file(), "official Test 2 workbook unavailable")
class Test2ADiagnosticWorkbookTests(unittest.TestCase):
    """The official 2E1 transfer columns are explicit and checksum-bound."""

    def test_binds_all_eight_candidate_series_to_exact_ranges(self):
        binding = load_test2a_diagnostic_workbook_binding(WORKBOOK)
        self.assertEqual(
            binding.workbook_sha256,
            EXPECTED_TEST2_WORKBOOK_SHA256,
        )
        self.assertEqual(binding.status, "OFFICIAL_2E1_SCHEMA_BOUND")
        self.assertEqual(binding.hour_count, 8760)
        self.assertEqual(binding.candidate_timestamp_range, "X5:X8764")
        self.assertEqual(binding.reference_timestamp_range, "X4:X8763")
        by_id = {item.series_id: item for item in binding.series}
        self.assertEqual(len(by_id), 8)
        self.assertEqual(
            by_id[
                "hourly_incident_solar_irradiance_total_on_window_plane"
            ].candidate_data_range,
            "Y5:Y8764",
        )
        self.assertEqual(
            by_id["hourly_room_solar_heat_gain_total"].candidate_data_range,
            "BD5:BD8764",
        )
        self.assertEqual(
            by_id[
                "hourly_transmitted_solar_radiation_excluding_secondary"
            ].reference_data_range,
            "BH4:BH8763",
        )

    def test_rejects_an_unexpected_workbook_identity(self):
        with self.assertRaisesRegex(ConfigurationError, "SHA-256 mismatch"):
            load_test2a_diagnostic_workbook_binding(
                WORKBOOK,
                expected_sha256="0" * 64,
            )


if __name__ == "__main__":
    unittest.main()
