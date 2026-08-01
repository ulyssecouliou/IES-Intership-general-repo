"""End-to-end completion tests for SIA 4010 Test 1 (BESTEST case 1E).

These exercise the whole pure-Python software side against the REAL official
evaluation workbook when it is present: parser -> observed extraction ->
comparator -> evaluation status -> class-matrix bridge, plus the fail-closed
binding placeholder and the official-bundle manifest wiring. Observed values are
CLEARLY SYNTHETIC fixtures derived from the official band; no candidate result
is fabricated and reaching the band is never SIA validation.
"""

import shutil
import unittest
from collections import Counter
from pathlib import Path

from swiss_sia.reference_model.sia4010.bundle_builder import build_manifest, write_manifest
from swiss_sia.reference_model.sia4010.compliance_comparator import (
    ComparisonStatus,
    Sia4010ComplianceComparator,
)
from swiss_sia.reference_model.sia4010.observed_extraction import (
    DictResultSource,
    VeApsResolver,
    build_observed_results,
)
from swiss_sia.reference_model.sia4010.test1_bindings import build_test1_bindings
from swiss_sia.reference_model.sia4010.test_runner import (
    Sia4010TestRunner,
    to_test_results_map,
)
from swiss_sia.reference_model.sia4010.workbook_loaders import parse_test1_reference_bands

REPO_ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_TEST1 = (
    REPO_ROOT / "SIA_4010_geteilter_Link" / "Test1" / "Resultaterfassung_Test1.xlsx"
)
TEST_OUTPUT_ROOT = REPO_ROOT / ".codex_tmp" / "sia4010_test1_completion"

HAS_OFFICIAL = OFFICIAL_TEST1.is_file()


def _midpoint_source(expected_results):
    """Return a synthetic within-band resolver (value = band midpoint)."""

    mapping = {
        e.key: ((e.lower_bound + e.upper_bound) / 2.0, e.unit) for e in expected_results
    }
    return DictResultSource(mapping)


@unittest.skipUnless(HAS_OFFICIAL, "official SIA 4010 Test 1 workbook not present")
class Test1ParserRegressionTests(unittest.TestCase):
    """Pin the parser against the shipped official Test 1 workbook."""

    def test_real_workbook_yields_the_expected_1e_bands(self):
        bands = parse_test1_reference_bands(OFFICIAL_TEST1)
        self.assertEqual(len(bands), 28)
        self.assertEqual({b.case_id for b in bands}, {"1E"})
        self.assertEqual(
            Counter(b.unit for b in bands),
            Counter({"kWh": 26, "kWh (peak)": 2}),
        )

    def test_peak_load_bands_are_labelled_and_united(self):
        peaks = [b for b in parse_test1_reference_bands(OFFICIAL_TEST1) if "peak" in b.metric.lower()]
        self.assertEqual(len(peaks), 2)
        for band in peaks:
            self.assertTrue(band.metric.lower().startswith("table 31"))
            self.assertEqual(band.unit, "kWh (peak)")
            self.assertTrue(band.has_band)

    def test_monthly_band_titles_and_row_labels_are_pinned(self):
        # Pin the 26 monthly/annual band titles so a fallback mislabel or a
        # title collision cannot pass silently as a regression.
        bands = parse_test1_reference_bands(OFFICIAL_TEST1)
        by_title = {}
        for band in bands:
            title = band.metric.rsplit("|", 1)[0].strip()
            by_title.setdefault(title, []).append(band.metric.rsplit("|", 1)[-1].strip())
        months = [str(m) for m in range(1, 13)] + ["Annual"]
        self.assertEqual(
            by_title.get("Table 28 — Test results sensible energy needs for heating"),
            months,
        )
        self.assertEqual(
            by_title.get("Table 29 — Test results sensible energy needs for cooling"),
            months,
        )
        self.assertEqual(
            by_title.get(
                "Table 31 — Test results Annual hourly integrated peak heating and cooling load"
            ),
            ["Heating", "Cooling"],
        )

    def test_known_month_one_heating_band_values(self):
        bands = parse_test1_reference_bands(OFFICIAL_TEST1)
        month_one = next(
            b for b in bands if "heating" in b.metric.lower() and b.metric.endswith("| 1")
        )
        self.assertAlmostEqual(month_one.lower_bound, 472.2871811677895, places=6)
        self.assertAlmostEqual(month_one.upper_bound, 588.8709790090021, places=6)
        self.assertEqual(month_one.unit, "kWh")


@unittest.skipUnless(HAS_OFFICIAL, "official SIA 4010 Test 1 workbook not present")
class Test1BandMechanicsTests(unittest.TestCase):
    """Prove PASS/FAIL/NOT_CHECKABLE on the real bands without fabrication."""

    def setUp(self):
        self.bands = parse_test1_reference_bands(OFFICIAL_TEST1)
        self.comparator = Sia4010ComplianceComparator()

    def test_within_band_synthetic_results_all_pass(self):
        observed = build_observed_results(self.bands, _midpoint_source(self.bands))
        outcomes = self.comparator.compare_all(self.bands, observed)
        statuses = Counter(o.status for o in outcomes)
        self.assertEqual(statuses[ComparisonStatus.PASS], 28)
        self.assertEqual(statuses[ComparisonStatus.FAIL], 0)
        self.assertEqual(statuses[ComparisonStatus.NOT_CHECKABLE], 0)

    def test_outside_band_synthetic_result_fails(self):
        mapping = {b.key: (b.upper_bound + 1000.0, b.unit) for b in self.bands}
        observed = build_observed_results(self.bands, DictResultSource(mapping))
        outcomes = self.comparator.compare_all(self.bands, observed)
        self.assertTrue(all(o.status == ComparisonStatus.FAIL for o in outcomes))

    def test_placeholder_bindings_keep_everything_not_checkable(self):
        # Bindings are unconfirmed, so the resolver must never call the accessor
        # or supply a value: every metric stays NOT_CHECKABLE (never a false pass).
        bindings = build_test1_bindings(self.bands)
        self.assertEqual(len(bindings), 28)
        self.assertTrue(all(not b.confirmed for b in bindings.values()))
        self.assertEqual(
            {b.aggregation for b in bindings.values()},
            {"monthly_sum", "annual_sum", "annual_peak"},
        )

        def _accessor(binding, expected):
            """A stub accessor that would leak a value if ever wrongly called."""
            return 999.0

        resolver = VeApsResolver(accessor=_accessor, bindings=bindings)
        observed = build_observed_results(self.bands, resolver)
        self.assertEqual(observed, ())
        outcomes = self.comparator.compare_all(self.bands, observed)
        self.assertTrue(all(o.status == ComparisonStatus.NOT_CHECKABLE for o in outcomes))


@unittest.skipUnless(HAS_OFFICIAL, "official SIA 4010 Test 1 workbook not present")
class Test1BundleWiringTests(unittest.TestCase):
    """Prove the manifest/checksum wiring and the runner status on real data."""

    def test_manifest_builder_classifies_the_workbook(self):
        # Read-only: build the manifest dict, do not write into the licensed dir.
        manifest = build_manifest(OFFICIAL_TEST1.parent)
        workbook_entries = [
            item for item in manifest["files"] if item["role"] == "evaluation_workbook"
        ]
        self.assertEqual(len(workbook_entries), 1)
        entry = workbook_entries[0]
        self.assertIn("1", entry["test_ids"])
        self.assertTrue(entry["sha256"])
        self.assertTrue("SIA" in manifest["issued_by"].upper())

    def _scratch_bundle(self) -> Path:
        """Copy the real workbook into a temp bundle and write its manifest."""
        bundle = TEST_OUTPUT_ROOT / "bundle"
        test1_dir = bundle / "Test1"
        test1_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(OFFICIAL_TEST1, test1_dir / OFFICIAL_TEST1.name)
        write_manifest(bundle)
        return bundle

    def test_runner_records_official_results_within_band(self):
        bundle = self._scratch_bundle()
        runner = Sia4010TestRunner()
        bands = runner.expected_bands(bundle, "1")
        self.assertEqual(len(bands), 28)
        observed = build_observed_results(bands, _midpoint_source(bands))
        evaluation = runner.evaluate_test(bundle, "1", observed)
        self.assertEqual(evaluation.status, "OFFICIAL_RESULTS_RECORDED")
        self.assertEqual(evaluation.counts["PASS"], 28)
        self.assertEqual(evaluation.counts["FAIL"], 0)
        class_input = to_test_results_map({"1": evaluation})
        self.assertEqual(class_input["test_1"]["status"], "OFFICIAL_RESULTS_RECORDED")

    def test_runner_flags_a_value_outside_the_band(self):
        bundle = self._scratch_bundle()
        runner = Sia4010TestRunner()
        bands = runner.expected_bands(bundle, "1")
        mapping = {b.key: (b.upper_bound + 1000.0, b.unit) for b in bands}
        observed = build_observed_results(bands, DictResultSource(mapping))
        evaluation = runner.evaluate_test(bundle, "1", observed)
        self.assertEqual(evaluation.status, "FAILED")
        self.assertGreater(evaluation.counts["FAIL"], 0)

    def test_partial_coverage_keeps_uncovered_metrics_not_checkable(self):
        # Only a subset of metrics is observed; the uncovered ones must stay
        # NOT_CHECKABLE and remain visible in the counts, so incompleteness is
        # never hidden or promoted to a positive aggregate status.
        bundle = self._scratch_bundle()
        runner = Sia4010TestRunner()
        bands = runner.expected_bands(bundle, "1")
        covered = bands[:5]
        mapping = {b.key: ((b.lower_bound + b.upper_bound) / 2.0, b.unit) for b in covered}
        observed = build_observed_results(bands, DictResultSource(mapping))
        evaluation = runner.evaluate_test(bundle, "1", observed)
        self.assertEqual(evaluation.counts["PASS"], 5)
        self.assertEqual(evaluation.counts["FAIL"], 0)
        self.assertEqual(evaluation.counts["NOT_CHECKABLE"], len(bands) - 5)
        self.assertGreater(evaluation.counts["NOT_CHECKABLE"], 0)
        self.assertEqual(evaluation.status, "NOT_CHECKABLE")


if __name__ == "__main__":
    unittest.main()
