"""Regression tests pinning the indicative CO2 emission factors.

These factors are not source-traced to an authoritative reference. The tests
pin their values and their INDICATIVE/UNVERIFIED provenance so the numbers
cannot drift silently, and so they cannot be quietly promoted to authoritative
status without an explicit, reviewed change to the marked provenance.
"""

import unittest

from swiss_sia import config


class EmissionFactorProvenanceTests(unittest.TestCase):
    def test_status_is_marked_indicative_and_unverified(self):
        """Provenance markers must flag the factors as non-authoritative."""

        self.assertEqual(config.EMISSION_FACTORS_STATUS, "INDICATIVE_UNVERIFIED")
        self.assertTrue(config.EMISSION_FACTORS_SOURCE.upper().startswith("PLACEHOLDER"))
        self.assertEqual(config.EMISSION_FACTORS_UNITS, "kg CO2/kWh")

    def test_factor_values_are_pinned(self):
        """Pin exact values so any change is a deliberate, reviewed edit."""

        self.assertEqual(
            config.EMISSION_FACTORS,
            {
                "electricity": 0.05,
                "gas": 0.20,
                "oil": 0.25,
                "wood": 0.02,
                "solar": 0.0,
                "wind": 0.0,
                "district_heating": 0.1,
            },
        )


if __name__ == "__main__":
    unittest.main()
