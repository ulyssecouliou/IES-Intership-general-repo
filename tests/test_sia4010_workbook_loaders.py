"""Tests for the SIA 4010 evaluation-workbook reference-band loader."""

import unittest
from pathlib import Path

from openpyxl import Workbook

from swiss_sia.reference_model.sia4010.compliance_comparator import (
    ComparisonStatus,
    Sia4010ComplianceComparator,
)
from swiss_sia.reference_model.sia4010.expected_results import ObservedResult
from swiss_sia.reference_model.sia4010.workbook_loaders import (
    deduplicate_expected_keys,
    parse_test1_reference_bands,
    parse_test2_reference_bands,
    parse_test3_reference_bands,
    parse_test4_reference_bands,
    parse_test5_reference_bands,
    parse_test6_reference_bands,
    parse_test7_reference_bands,
)

TEST_ROOT = Path(__file__).resolve().parents[1]
TEST_OUTPUT_ROOT = TEST_ROOT / ".codex_tmp" / "sia4010_parser_tests"
SHEET = "Zusammenfassung Testfälle"


def _build_fixture(name: str) -> Path:
    """Build a workbook mirroring the real grid: a band block plus a bandless one."""

    TEST_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET
    # Block A (case 1E) WITH explicit band columns G/H/I.
    ws["A1"] = "Table 28 — Test results sensible energy"
    ws["A3"] = "Case id."
    ws["B3"] = "1E"
    ws["D3"] = "kWh"
    for col, label in {
        "A": "Month", "B": "Testprogramm", "C": "IDA ICE", "D": "EXCEL SIA 380/2",
        "E": "Energy+/OpenStudio", "F": "EDSL-Tas", "G": "Mittelwert",
        "H": "obere Grenze", "I": "untere Grenze",
    }.items():
        ws["{}5".format(col)] = label
    ws.append([])  # spacer not used; explicit rows below
    ws["A6"], ws["G6"], ws["H6"], ws["I6"] = 1, 530.6, 588.9, 472.3
    ws["A7"], ws["G7"], ws["H7"], ws["I7"] = 2, 404.2, 452.7, 355.7
    # Block K (case 600) WITHOUT any band columns -> must be ignored.
    ws["K1"] = "Table 28 — Test results sensible energy"
    ws["K3"] = "Case id."
    ws["L3"] = 600
    ws["N3"] = "kWh"
    for col, label in {
        "K": "Month", "L": "Testprogramm", "M": "Daten Norm EN ISO",
        "N": "IDA ICE", "O": "EXCEL SIA 380/2", "P": "Energy+/OpenStudio",
    }.items():
        ws["{}5".format(col)] = label
    ws["K6"], ws["M6"] = 1, 1005.0
    path = TEST_OUTPUT_ROOT / name
    wb.save(path)
    return path


class Sia4010WorkbookLoaderTests(unittest.TestCase):
    def test_extracts_band_only_for_case_with_explicit_bounds(self):
        results = parse_test1_reference_bands(_build_fixture("t1.xlsx"))
        # Only case 1E (with obere/untere Grenze) yields bands; case 600 does not.
        self.assertTrue(results)
        self.assertEqual({r.case_id for r in results}, {"1E"})
        for r in results:
            self.assertTrue(r.has_band)
            self.assertEqual(r.unit, "kWh")
            self.assertIn("Table 28", r.metric)

    def test_band_values_and_mean_are_read_correctly(self):
        results = parse_test1_reference_bands(_build_fixture("t1b.xlsx"))
        month1 = [r for r in results if r.metric.endswith("| 1")][0]
        self.assertEqual(month1.upper_bound, 588.9)
        self.assertEqual(month1.lower_bound, 472.3)
        self.assertEqual(month1.expected_value, 530.6)  # Mittelwert

    def test_parsed_band_drives_comparator_pass_fail(self):
        results = parse_test1_reference_bands(_build_fixture("t1c.xlsx"))
        month1 = [r for r in results if r.metric.endswith("| 1")][0]
        comparator = Sia4010ComplianceComparator()

        def observe(value):
            return ObservedResult(
                test_id=month1.test_id, case_id=month1.case_id, metric=month1.metric,
                value=value, unit="kWh", evidence_locator="VE APS",
            )

        self.assertEqual(comparator.compare_one(month1, observe(500.0)).status, ComparisonStatus.PASS)
        self.assertEqual(comparator.compare_one(month1, observe(600.0)).status, ComparisonStatus.FAIL)


def _build_test2_fixture(name: str) -> Path:
    """Build a Test 2 style 'case-per-row' summary (Fall rows, band blocks)."""

    TEST_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Zusammenfassung"
    for col, label in {
        "D": "Testprogramm", "E": "IDA_ICE", "M": "Mittelwert",
        "N": "obere Grenze", "O": "untere Grenze",
    }.items():
        ws["{}9".format(col)] = label
    ws["A12"], ws["D12"] = "Fall", "Jahresenergie solarer Waermeeintrag"
    ws["A13"], ws["N13"], ws["O13"], ws["M13"] = "Testfaelle", "kWh", "kWh", "kWh"
    ws["A14"], ws["M14"], ws["N14"], ws["O14"] = "Test 2 A", 1048.9, 1202.3, 895.5
    ws["A15"], ws["M15"], ws["N15"], ws["O15"] = "Test 2 B", 1522.8, 1878.3, 1167.3
    path = TEST_OUTPUT_ROOT / name
    wb.save(path)
    return path


class Sia4010Test2LoaderTests(unittest.TestCase):
    def test_case_per_row_bands_are_extracted(self):
        results = parse_test2_reference_bands(_build_test2_fixture("t2.xlsx"))
        self.assertEqual({r.case_id for r in results}, {"Test 2 A", "Test 2 B"})
        for r in results:
            self.assertTrue(r.has_band)
            self.assertEqual(r.unit, "kWh")
            self.assertIn("Jahresenergie", r.metric)
        case_a = [r for r in results if r.case_id == "Test 2 A"][0]
        self.assertEqual(case_a.upper_bound, 1202.3)
        self.assertEqual(case_a.lower_bound, 895.5)
        self.assertEqual(case_a.expected_value, 1048.9)


def _build_test3_fixture(name: str) -> Path:
    """Build a Test 3 style inline-header summary (Testfaelle row = band row, gaps)."""

    TEST_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Zusammenfassung"
    ws["A8"], ws["F8"] = "Jahreswerte", "kWh"
    ws["A10"], ws["O10"], ws["P10"], ws["Q10"] = (
        "Testfaelle", "Mittelwert", "Obere Grenze", "Untere Grenze",
    )
    ws["A11"], ws["O11"], ws["P11"], ws["Q11"] = "Test 3 A", 665.4, 678.2, 652.6
    ws["A12"], ws["O12"], ws["P12"], ws["Q12"] = "Test 3 B", 1008.2, 1033.7, 982.7
    # row 13 is a blank gap between sub-groups
    ws["A14"], ws["O14"], ws["P14"], ws["Q14"] = "Test 3 C", 806.1, 816.4, 795.9
    ws["A15"] = "Stuendliche Haeufigkeit"  # a new section -> stops collection
    ws["A16"], ws["O16"], ws["P16"], ws["Q16"] = "Test 3 Z", 1.0, 2.0, 0.5
    path = TEST_OUTPUT_ROOT / name
    wb.save(path)
    return path


class Sia4010Test3LoaderTests(unittest.TestCase):
    def test_inline_header_bands_span_gaps_and_stop_at_new_section(self):
        results = parse_test3_reference_bands(_build_test3_fixture("t3.xlsx"))
        cases = {r.case_id for r in results}
        # Collects across the blank gap (A,B,C) but stops at the new section (not Z).
        self.assertEqual(cases, {"Test 3 A", "Test 3 B", "Test 3 C"})
        self.assertNotIn("Test 3 Z", cases)
        for r in results:
            self.assertEqual(r.unit, "kWh")
            self.assertEqual(r.metric, "Jahreswerte")
            self.assertTrue(r.has_band)


def _build_test4_fixture(name: str) -> Path:
    """Build a Test 4 style metric-per-row summary (Testgroessen band, then junk)."""

    TEST_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Zusammenfassung"
    ws["A8"], ws["T8"], ws["U8"], ws["V8"] = (
        "Jahreswerte", "Mittelwert", "obere Grenze", "untere Grenze",
    )
    ws["A9"] = "Testgroessen"  # section header, no band
    ws["A10"], ws["I10"], ws["T10"], ws["U10"], ws["V10"] = (
        "Energiebedarf Ventilatoren", "kWh", 829.5, 970.5, 688.5,
    )
    ws["A11"], ws["I11"], ws["T11"], ws["U11"], ws["V11"] = (
        "Waermezufuhr Lufterwaermer", "kWh", 2847.0, 3252.0, 2442.0,
    )
    ws["A13"] = "Diagnosegroessen"  # section header -> stops collection
    ws["A14"], ws["I14"] = "Energiebedarf Zuluft", "kWh"  # diagnostic, no band
    # reused columns lower down with inverted junk must be rejected
    ws["A19"], ws["T19"], ws["U19"], ws["V19"] = "Winterwoche", 20.0, 19.0, 21.0
    path = TEST_OUTPUT_ROOT / name
    wb.save(path)
    return path


class Sia4010Test4LoaderTests(unittest.TestCase):
    def test_metric_per_row_bands_stop_at_diagnostics_and_reject_junk(self):
        results = parse_test4_reference_bands(_build_test4_fixture("t4.xlsx"))
        metrics = {r.metric for r in results}
        self.assertEqual(
            metrics,
            {"Energiebedarf Ventilatoren", "Waermezufuhr Lufterwaermer"},
        )
        self.assertNotIn("Winterwoche", metrics)  # inverted/reused columns rejected
        for r in results:
            self.assertEqual(r.unit, "kWh")
            self.assertEqual(r.case_id, "Test 4")
            self.assertLessEqual(r.lower_bound, r.upper_bound)


def _build_test5_fixture(name: str) -> Path:
    """Build a Test 5 style grouped-column layout (cases across columns, one row)."""

    TEST_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Zusammenfassung"
    ws["Z6"], ws["AD6"], ws["AH6"] = "Mittelwert", "Obere Grenze", "Untere Grenze"
    ws["F8"], ws["G8"], ws["H8"], ws["I8"] = "Test 5A", "Test 5B", "Test 5C", "Test 5D"
    ws["A10"], ws["I10"] = "Energiebedarf Ventilatoren", "kWh"
    ws["Z10"], ws["AA10"], ws["AB10"], ws["AC10"] = 509.0, 665.0, 700.0, 720.0  # means
    ws["AD10"], ws["AE10"], ws["AF10"], ws["AG10"] = 593.0, 739.0, 780.0, 800.0  # uppers
    ws["AH10"], ws["AI10"], ws["AJ10"], ws["AK10"] = 426.0, 591.0, 620.0, 640.0  # lowers
    path = TEST_OUTPUT_ROOT / name
    wb.save(path)
    return path


class Sia4010Test5LoaderTests(unittest.TestCase):
    def test_grouped_case_column_bands_are_extracted(self):
        results = parse_test5_reference_bands(_build_test5_fixture("t5.xlsx"))
        self.assertEqual(
            {r.case_id for r in results},
            {"Test 5A", "Test 5B", "Test 5C", "Test 5D"},
        )
        for r in results:
            self.assertEqual(r.unit, "kWh")
            self.assertEqual(r.metric, "Energiebedarf Ventilatoren")
            self.assertTrue(r.has_band)
        case_a = [r for r in results if r.case_id == "Test 5A"][0]
        self.assertEqual(case_a.lower_bound, 426.0)
        self.assertEqual(case_a.upper_bound, 593.0)
        self.assertEqual(case_a.expected_value, 509.0)


def _build_test6_fixture(name: str) -> Path:
    """Build a Test 6 style metric-per-row layout with metric labels in col B."""

    TEST_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Zusammenfassung"
    ws["E8"], ws["K8"], ws["L8"], ws["M8"] = (
        "Testprogramm", "Mittelwert", "obere Grenze", "untere Grenze",
    )
    ws["A9"] = "Jahreswerte"
    ws["A10"], ws["B10"], ws["J10"], ws["K10"], ws["L10"], ws["M10"] = (
        "Testgroessen", "Energiebedarf Ventilatoren", "kWh", 3854.0, 4387.0, 3321.0,
    )
    ws["B11"], ws["J11"], ws["K11"], ws["L11"], ws["M11"] = (
        "Waermezufuhr Lufterwaermer", "kWh", 1789.0, 2180.0, 1398.0,
    )
    ws["A12"] = "Diagnosegroessen"  # section -> stops
    ws["B13"], ws["J13"] = "Energiebedarf Zuluft", "kWh"  # diagnostic, no band
    path = TEST_OUTPUT_ROOT / name
    wb.save(path)
    return path


class Sia4010Test6LoaderTests(unittest.TestCase):
    def test_metric_label_column_is_detected_as_col_b(self):
        results = parse_test6_reference_bands(_build_test6_fixture("t6.xlsx"))
        metrics = {r.metric for r in results}
        # Metric labels come from col B, not the col-A section header "Testgroessen".
        self.assertEqual(
            metrics,
            {"Energiebedarf Ventilatoren", "Waermezufuhr Lufterwaermer"},
        )
        self.assertNotIn("Testgroessen", metrics)
        for r in results:
            self.assertEqual(r.unit, "kWh")
            self.assertEqual(r.case_id, "Test 6")


def _build_test7_fixture(name: str) -> Path:
    """Build a Test 7 style metric-per-row layout with a duplicated quantity label."""

    TEST_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Zusammenfassung"
    ws["E7"], ws["L7"], ws["M7"], ws["N7"] = (
        "Testprogramm", "Mittelwert", "Obere Grenze", "Untere Grenze",
    )
    ws["A8"], ws["B8"], ws["K8"], ws["L8"], ws["M8"], ws["N8"] = (
        "Testgroessen", "Zugefuehrte elektrische Energie", "kWh", 3929.0, 4484.0, 3374.0,
    )
    # row 9 blank gap (sub-section separator); row 10 repeats the label
    ws["B10"], ws["K10"], ws["L10"], ws["M10"], ws["N10"] = (
        "Zugefuehrte elektrische Energie", "kWh", 8081.0, 9374.0, 8081.0,
    )
    path = TEST_OUTPUT_ROOT / name
    wb.save(path)
    return path


class Sia4010Test7LoaderTests(unittest.TestCase):
    def test_duplicate_labels_are_disambiguated_to_unique_keys(self):
        raw = parse_test7_reference_bands(_build_test7_fixture("t7.xlsx"))
        # Both rows share the same metric label before de-duplication.
        self.assertEqual(len(raw), 2)
        self.assertEqual(len({r.metric for r in raw}), 1)
        # De-duplication makes the comparator keys one-to-one.
        unique = deduplicate_expected_keys(raw)
        self.assertEqual(len({r.key for r in unique}), 2)
        self.assertTrue(any(r.metric.endswith("(2)") for r in unique))


if __name__ == "__main__":
    unittest.main()
