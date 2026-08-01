"""Tests for IESVE Boost.Python signature compatibility adapters."""

import unittest

from swiss_sia.reference_model.ve_compat import thermal_templates


class _TwoArgumentProject:
    def thermal_templates(self, assigned, allow_ncm):
        return {"signature": (assigned, allow_ncm)}


class _OneArgumentProject:
    def thermal_templates(self, assigned):
        return {"signature": (assigned,)}


class ThermalTemplateCompatibilityTests(unittest.TestCase):
    def test_two_argument_boost_signature(self):
        self.assertEqual(
            thermal_templates(_TwoArgumentProject(), False, False),
            {"signature": (False, False)},
        )

    def test_one_argument_legacy_signature(self):
        self.assertEqual(
            thermal_templates(_OneArgumentProject(), False, False),
            {"signature": (False,)},
        )


if __name__ == "__main__":
    unittest.main()
