"""Dry-run tests for the SIA 4010 Phase B executor (run_all_tests)."""

import unittest
from pathlib import Path

from openpyxl import Workbook

from swiss_sia.reference_model.sia4010.bundle_builder import write_manifest
from swiss_sia.reference_model.sia4010.execution import run_all_tests

TEST_ROOT = Path(__file__).resolve().parents[1]
TEST_OUTPUT_ROOT = TEST_ROOT / ".codex_tmp" / "sia4010_execution_tests"


def _build_bundle(name: str) -> Path:
    """Create a bundle with Test 1 and Test 2 evaluation workbooks."""

    root = TEST_OUTPUT_ROOT / name
    (root / "Test1").mkdir(parents=True, exist_ok=True)
    (root / "Test2").mkdir(parents=True, exist_ok=True)
    wb1 = Workbook()
    ws1 = wb1.active
    ws1.title = "Zusammenfassung Testfälle"
    ws1["A1"] = "Table 28 — Test results sensible energy"
    ws1["A3"], ws1["B3"], ws1["D3"] = "Case id.", "1E", "kWh"
    for col, label in {
        "A": "Month",
        "B": "Testprogramm",
        "G": "Mittelwert",
        "H": "obere Grenze",
        "I": "untere Grenze",
    }.items():
        ws1["{}5".format(col)] = label
    ws1["A6"], ws1["G6"], ws1["H6"], ws1["I6"] = 1, 530.6, 588.9, 472.3
    wb1.save(root / "Test1" / "Resultaterfassung_Test1.xlsx")
    wb2 = Workbook()
    ws2 = wb2.active
    ws2.title = "Zusammenfassung"
    for col, label in {
        "D": "Testprogramm",
        "M": "Mittelwert",
        "N": "obere Grenze",
        "O": "untere Grenze",
    }.items():
        ws2["{}9".format(col)] = label
    ws2["A12"], ws2["D12"] = "Fall", "Jahresenergie solar"
    ws2["A13"], ws2["N13"] = "Testfaelle", "kWh"
    ws2["A14"], ws2["M14"], ws2["N14"], ws2["O14"] = "Test 2 A", 1048.9, 1202.3, 895.5
    wb2.save(root / "Test2" / "Resultaterfassung_Test2.xlsx")
    write_manifest(root)
    return root


class Sia4010ExecutionTests(unittest.TestCase):
    def test_run_all_tests_evaluates_registered_present_tests(self):
        root = _build_bundle("exec")

        # Resolver supplies within-band values for Test 1 only; Test 2 gets none.
        def resolver(expected):
            if expected.test_id == "1":
                return (expected.lower_bound + expected.upper_bound) / 2.0, expected.unit
            return None

        summary = run_all_tests(root, resolver)
        self.assertEqual(set(summary.evaluations), {"1", "2"})
        self.assertEqual(summary.statuses["1"], "OFFICIAL_RESULTS_RECORDED")
        self.assertEqual(summary.statuses["2"], "NOT_CHECKABLE")
        self.assertIn("test_1", summary.test_results_map)
        self.assertIn("statuses", summary.to_dict())
        # Test 1 carries no distribution criterion; Test 2 does, and with no
        # reference data / candidate here it resolves fail-closed to NOT_CHECKABLE.
        self.assertEqual(summary.evaluations["1"].distribution_outcomes, ())
        test2_dist = summary.evaluations["2"].distribution_outcomes
        self.assertTrue(test2_dist)
        self.assertTrue(all(o.status == "NOT_CHECKABLE" for o in test2_dist))

    def test_empty_resolver_keeps_everything_not_checkable(self):
        root = _build_bundle("empty")
        summary = run_all_tests(root, lambda expected: None)
        self.assertTrue(summary.evaluations)
        self.assertTrue(all(s == "NOT_CHECKABLE" for s in summary.statuses.values()))


if __name__ == "__main__":
    unittest.main()
