"""Integrity tests for the licensed-evidence-derived ISO Test 1 catalog."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "config" / "iso52016_test1_verification_cases.json"


class Iso52016Test1VerificationCasesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(CATALOG.read_text(encoding="utf-8"))

    def test_exact_six_case_matrix_is_recorded(self):
        self.assertEqual(
            set(self.payload["cases"]),
            {"600", "640", "900", "940", "600FF", "900FF"},
        )

    def test_normative_common_inputs_are_preserved(self):
        common = self.payload["common_inputs"]
        self.assertEqual(common["infiltration"]["air_changes_per_hour"], 0.41)
        self.assertEqual(common["internal_gain"]["whole_zone_sensible_gain_w"], 200.0)
        self.assertEqual(common["thermostats"]["continuous"]["heating_setpoint_c"], 20.0)
        self.assertEqual(common["thermostats"]["continuous"]["cooling_setpoint_c"], 27.0)
        self.assertEqual(common["available_capacity"]["heating_w"], 1000000.0)
        self.assertEqual(common["available_capacity"]["cooling_w"], 1000000.0)

    def test_reference_annual_totals_match_published_tables(self):
        results = self.payload["reference_results"]
        self.assertEqual(results["monthly_heating_need_kwh"]["600"]["annual"], 5133)
        self.assertEqual(results["monthly_cooling_need_kwh"]["600"]["annual"], 7503)
        self.assertEqual(results["monthly_heating_need_kwh"]["940"]["annual"], 1303)
        self.assertEqual(results["monthly_cooling_need_kwh"]["900"]["annual"], 76)

    def test_reference_values_never_become_an_invented_verdict(self):
        policy = self.payload["reference_results"]["comparison_policy"]
        self.assertEqual(policy["mode"], "REFERENCE_ONLY")
        self.assertFalse(policy["official_acceptance_tolerance_available_in_captured_pages"])

    def test_apachesim_alternative_methods_are_declared_fail_closed(self):
        alternatives = self.payload["alternative_method_validation"]
        self.assertTrue(alternatives["annex_evidence_complete"])
        self.assertTrue(
            all(
                item["choice"] == "No"
                for item in alternatives["apachesim_a10_declaration"]["choices"].values()
            )
        )

    def test_hourly_tables_have_exactly_24_values(self):
        results = self.payload["reference_results"]
        for case in ("600", "640", "900", "940"):
            self.assertEqual(
                len(results["january_4_hourly_sensible_load"][case]["published_values"]),
                24,
            )
        for case in ("600FF", "900FF"):
            self.assertEqual(
                len(results["january_4_hourly_free_float_operative_temperature_c"][case]),
                24,
            )


if __name__ == "__main__":
    unittest.main()
