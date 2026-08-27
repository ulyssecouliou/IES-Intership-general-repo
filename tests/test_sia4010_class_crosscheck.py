"""Tests for the non-gating automated band cross-check on SIA 4010 classes."""

import unittest

from swiss_sia.sia4010_checker import SIA4010Checker


class Sia4010ClassCrosscheckTests(unittest.TestCase):
    def _class_results(self):
        return {
            "5": {
                "class": "5",
                "class_status": "NOT_CHECKABLE",
                "required_tests": ["test_7"],
            },
            "1A": {
                "class": "1A",
                "class_status": "NOT_CHECKABLE",
                "required_tests": ["test_1", "test_2"],
                "required_test_aliases": ["test_1", "test_2A"],
            },
        }

    def test_crosscheck_annotates_without_changing_class_status(self):
        band_map = {
            "test_7": {"status": "FAILED"},
            "test_1": {"status": "OFFICIAL_RESULTS_RECORDED"},
            "test_2A": {"status": "OFFICIAL_RESULTS_RECORDED"},
        }
        annotated = SIA4010Checker._annotate_classes_with_band_crosscheck(
            self._class_results(), band_map
        )
        self.assertEqual(annotated["5"]["band_crosscheck"]["summary"], "BAND_FAILED")
        self.assertEqual(
            annotated["1A"]["band_crosscheck"]["summary"], "BAND_WITHIN_RANGE"
        )
        # Crucial: the official class status is untouched (no overclaim).
        self.assertEqual(annotated["5"]["class_status"], "NOT_CHECKABLE")
        self.assertEqual(annotated["1A"]["class_status"], "NOT_CHECKABLE")

    def test_crosscheck_not_checkable_when_tests_unevaluated(self):
        annotated = SIA4010Checker._annotate_classes_with_band_crosscheck(
            self._class_results(), {}
        )
        self.assertEqual(
            annotated["5"]["band_crosscheck"]["summary"], "BAND_NOT_CHECKABLE"
        )
        self.assertEqual(
            annotated["5"]["band_crosscheck"]["per_test"]["test_7"], "NOT_EVALUATED"
        )


if __name__ == "__main__":
    unittest.main()
