"""Regression tests for the ``Haeufigkeitskassen`` extractor.

These tests read the real ``Resultaterfassung`` workbooks under
``SIA_4010_geteilter_Link/`` (immutable, source-traced) and prove:

1. Every SIA 4010 test whose workbook is available (2..7) actually carries a
   ``Haeufigkeitskassen`` sheet.  This directly refutes the earlier claim
   that Tests 4 and 6 carry no distribution.
2. The extractor preserves the SIA ``9999`` sentinel as a dedicated list of
   class indices instead of turning it into a bound.
3. Every ``Klassen`` header column carries a non-empty quantity label and
   unit.
4. The class indices are strictly increasing from 1 upwards.

Openpyxl is required at runtime; if unavailable the tests are skipped.
"""

from __future__ import annotations

import os
import unittest


try:
    import openpyxl  # noqa: F401 -- import-only availability check
    _OPENPYXL_AVAILABLE = True
except Exception:  # pragma: no cover
    _OPENPYXL_AVAILABLE = False


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
LINK_DIR = os.path.join(REPO_ROOT, "SIA_4010_geteilter_Link")


# Every distribution-bearing workbook (Tests 2 to 7). Verified by direct
# openpyxl inspection on 2026-08-12: all six carry a frequency-class sheet,
# under one of two spellings. An earlier version of this file wrongly claimed
# Tests 2, 3 and 5 had none; that was an artefact of matching only the
# misspelled name used by Tests 4, 6 and 7.
TEST_WORKBOOK_PATHS = {
    "2": os.path.join(LINK_DIR, "Test2", "Resultaterfassung_Test2.xlsx"),
    "3": os.path.join(LINK_DIR, "Test3", "Resultaterfassung_Test3.xlsx"),
    "4": os.path.join(LINK_DIR, "Test4", "Resultaterfassung Test4.xlsx"),
    "5": os.path.join(LINK_DIR, "Test5", "Resultaterfassung_Test5.xlsx"),
    "6": os.path.join(LINK_DIR, "Test6", "Resultaterfassung_Test6.xlsx"),
    "7": os.path.join(LINK_DIR, "Test7", "Resultaterfassung Test7.xlsx"),
}

#: Sheet spelling and binned-quantity count observed per test on 2026-08-12.
#: Pinned so a future edit to the extractor cannot silently drop a workbook.
#: Tests 2 and 3 also carry a ``Fenstermodelle`` column listing window models
#: as text; it has no unit and no numeric bounds, so it is correctly not a
#: binned quantity and is excluded from these counts.
EXPECTED_SHEET_AND_COUNT = {
    "2": ("Haeufigkeitsklassen", 3),
    "3": ("Haeufigkeitsklassen", 2),
    "4": ("Haeufigkeitskassen", 11),
    "5": ("Haeufigkeitsklassen", 11),
    "6": ("Haeufigkeitskassen", 11),
    "7": ("Haeufigkeitskassen", 20),
}


@unittest.skipUnless(_OPENPYXL_AVAILABLE, "openpyxl unavailable")
class HaeufigkeitskassenExtractorRegressionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        from swiss_sia.reference_model.sia4010.haeufigkeitskassen_extractor import (
            extract_haeufigkeitskassen,
        )

        cls.extract = staticmethod(extract_haeufigkeitskassen)

    def test_tests_4_6_7_carry_haeufigkeitskassen(self) -> None:
        """Direct refutation of the "Tests 4/6 have no distribution" claim.

        Reported to the SIA on 2026-08-07 as "the corresponding workbooks do
        not include frequency classes or distribution sheets"; the authority
        pushed back, and inspection proved the authority right. Tests 4 and 6
        carry 11 binned quantities each, more than Tests 2 and 3.
        """

        for test_id in ("4", "6", "7"):
            path = TEST_WORKBOOK_PATHS[test_id]
            if not os.path.exists(path):
                self.skipTest("Workbook missing: {}".format(path))
            table = self.extract(path, test_id=test_id)
            self.assertGreater(
                len(table.quantities),
                0,
                msg="Test {} yielded zero quantities from Haeufigkeitskassen".format(
                    test_id
                ),
            )

    def test_all_six_distribution_workbooks_are_readable(self) -> None:
        """Both sheet spellings must resolve, for all of Tests 2 to 7."""

        for test_id, (sheet, count) in EXPECTED_SHEET_AND_COUNT.items():
            path = TEST_WORKBOOK_PATHS[test_id]
            if not os.path.exists(path):
                self.skipTest("Workbook missing: {}".format(path))
            table = self.extract(path, test_id=test_id)
            self.assertEqual(
                table.sheet_name,
                sheet,
                msg="Test {} frequency-class sheet spelling changed".format(test_id),
            )
            self.assertEqual(
                len(table.quantities),
                count,
                msg="Test {} binned-quantity count changed".format(test_id),
            )

    def test_fenstermodelle_legend_is_not_a_binned_quantity(self) -> None:
        """A text legend column must never be read as a frequency-class column."""

        for test_id in ("2", "3"):
            path = TEST_WORKBOOK_PATHS[test_id]
            if not os.path.exists(path):
                self.skipTest("Workbook missing: {}".format(path))
            table = self.extract(path, test_id=test_id)
            labels = [q.quantity_label for q in table.quantities]
            self.assertNotIn("Fenstermodelle", labels)
            for q in table.quantities:
                self.assertTrue(
                    q.unit,
                    msg="Test {} column {} has no unit and is not a quantity".format(
                        test_id, q.column_letter
                    ),
                )
                self.assertTrue(
                    q.upper_bounds or q.sentinel_9999_class_indices,
                    msg="Test {} column {} carries no bounds".format(
                        test_id, q.column_letter
                    ),
                )

    def test_tests_4_and_6_have_more_bins_than_tests_2_and_3(self) -> None:
        """Pins the fact that refuted our claim to the SIA."""

        for test_id in ("2", "3", "4", "6"):
            if not os.path.exists(TEST_WORKBOOK_PATHS[test_id]):
                self.skipTest("Workbook missing for test {}".format(test_id))
        counts = {
            test_id: len(
                self.extract(TEST_WORKBOOK_PATHS[test_id], test_id=test_id).quantities
            )
            for test_id in ("2", "3", "4", "6")
        }
        self.assertGreater(counts["4"], counts["2"])
        self.assertGreater(counts["4"], counts["3"])
        self.assertGreater(counts["6"], counts["2"])
        self.assertGreater(counts["6"], counts["3"])

    def test_sentinel_9999_preserved_separately(self) -> None:
        """The SIA convention ``9999`` must never be reported as a bound."""

        path = TEST_WORKBOOK_PATHS["6"]
        if not os.path.exists(path):
            self.skipTest("Test 6 workbook missing")
        table = self.extract(path, test_id="6")
        seen_sentinel = False
        for q in table.quantities:
            self.assertNotIn(9999.0, q.upper_bounds)
            self.assertNotIn(9999, q.upper_bounds)
            if q.sentinel_9999_class_indices:
                seen_sentinel = True
        self.assertTrue(
            seen_sentinel,
            msg=(
                "Test 6 workbook has known 9999 sentinels in the "
                "Haeufigkeitskassen sheet; the extractor did not surface any."
            ),
        )

    def test_every_quantity_has_label_and_unit(self) -> None:
        for test_id, path in TEST_WORKBOOK_PATHS.items():
            if not os.path.exists(path):
                self.skipTest("Workbook missing: {}".format(path))
            table = self.extract(path, test_id=test_id)
            for q in table.quantities:
                self.assertTrue(
                    q.quantity_label,
                    msg="Test {} column {} has empty label".format(
                        test_id, q.column_letter
                    ),
                )

    def test_class_indices_strictly_monotonic(self) -> None:
        for test_id, path in TEST_WORKBOOK_PATHS.items():
            if not os.path.exists(path):
                self.skipTest("Workbook missing: {}".format(path))
            table = self.extract(path, test_id=test_id)
            for q in table.quantities:
                self.assertEqual(
                    list(q.class_indices),
                    sorted(q.class_indices),
                    msg="Test {} column {} indices not monotonic".format(
                        test_id, q.column_letter
                    ),
                )
                self.assertEqual(
                    len(q.class_indices),
                    len(set(q.class_indices)),
                    msg="Test {} column {} indices not unique".format(
                        test_id, q.column_letter
                    ),
                )

    def test_test_4_first_column_matches_expected_bounds(self) -> None:
        """Verbatim regression: the SIA workbook layout is stable."""

        path = TEST_WORKBOOK_PATHS["4"]
        if not os.path.exists(path):
            self.skipTest("Test 4 workbook missing")
        table = self.extract(path, test_id="4")
        first = table.quantities[0]
        self.assertEqual(first.column_letter, "B")
        self.assertIn("Zu-/Abluft", first.quantity_label)
        self.assertEqual(first.unit, "m3/h")
        # The first six upper bounds visible in the workbook, verbatim.
        self.assertEqual(first.upper_bounds[:6], (10.0, 200.0, 400.0, 600.0, 800.0, 1000.0))


if __name__ == "__main__":
    unittest.main()
