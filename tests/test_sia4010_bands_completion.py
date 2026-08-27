"""Band-path completion tests for annual-sum SIA 4010 tests (2, 3, 4, 5, 6, 7).

Each of these tests compares annual energy quantities (kWh) against the official
reference band. This exercises the whole pure-Python software side against the
REAL official evaluation workbooks: parser -> observed extraction -> comparator
-> evaluation status -> class-matrix bridge, plus the fail-closed placeholder
bindings and the official-bundle manifest/checksum wiring. Observed values are
CLEARLY SYNTHETIC fixtures derived from the official band; no candidate result
is fabricated and reaching the band is never SIA validation.

Each official workbook is parsed once and cached (some ship dozens of sheets),
so the suite stays fast. Out of scope here (still remaining work): the second
acceptance criterion of Tests 2, 3 and 5 (the hourly frequency-distribution
scatter band) and every real VE/APS run.
"""

import glob
import shutil
import unittest
from functools import lru_cache
from pathlib import Path

from swiss_sia.reference_model.sia4010.bundle_builder import write_manifest
from swiss_sia.reference_model.sia4010.compliance_comparator import (
    ComparisonStatus,
    Sia4010ComplianceComparator,
)
from swiss_sia.reference_model.sia4010.observed_extraction import (
    DictResultSource,
    VeApsResolver,
    build_observed_results,
)
from swiss_sia.reference_model.sia4010.placeholder_bindings import (
    build_annual_sum_bindings,
)
from swiss_sia.reference_model.sia4010.test_runner import (
    Sia4010TestRunner,
    to_test_results_map,
)
from swiss_sia.reference_model.sia4010.workbook_loaders import (
    parse_test2_reference_bands,
    parse_test3_reference_bands,
    parse_test4_reference_bands,
    parse_test5_reference_bands,
    parse_test6_reference_bands,
    parse_test7_reference_bands,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PKG = REPO_ROOT / "SIA_4010_geteilter_Link"
TEST_OUTPUT_ROOT = REPO_ROOT / ".codex_tmp" / "sia4010_bands_completion"

# One config per annual-sum test. "pin" is a (lower, upper) band that must exist
# in the parsed set, pinning values without depending on the exact German label.
CONFIGS = [
    {"id": "2", "parse": parse_test2_reference_bands, "bands": 8, "pin": (895.5, 1202.3)},
    {"id": "3", "parse": parse_test3_reference_bands, "bands": 12, "pin": (652.6, 678.2)},
    {"id": "4", "parse": parse_test4_reference_bands, "bands": 3, "pin": (688.5, 970.5)},
    {"id": "5", "parse": parse_test5_reference_bands, "bands": 16, "pin": (426.0, 592.8)},
    {
        "id": "6",
        "parse": parse_test6_reference_bands,
        "bands": 6,
        "pin": (3320.8, 4386.5),
    },
    {
        "id": "7",
        "parse": parse_test7_reference_bands,
        "bands": 11,
        "pin": (3373.8, 4483.8),
    },
]
CONFIGS_BY_ID = {config["id"]: config for config in CONFIGS}
# A small, fast workbook that represents the runner/manifest path for all tests.
REPRESENTATIVE_ID = "4"


def _workbook(test_id):
    """Return the official evaluation workbook path for one test, or None."""
    matches = glob.glob(str(PKG / "Test{}".format(test_id) / "Resultaterfassung*"))
    return Path(matches[0]) if matches else None


HAS_PKG = PKG.is_dir() and all(_workbook(c["id"]) for c in CONFIGS)


@lru_cache(maxsize=None)
def _bands(test_id):
    """Parse one official workbook once and cache the result for the whole run."""
    config = CONFIGS_BY_ID[test_id]
    return config["parse"](_workbook(test_id))


def _has_pin(bands, pin):
    """Return whether a band with the pinned (lower, upper) values is present."""
    lo, hi = pin
    return any(
        round(b.lower_bound, 1) == lo and round(b.upper_bound, 1) == hi for b in bands
    )


@unittest.skipUnless(HAS_PKG, "official SIA 4010 package not present")
class AnnualSumBandsTests(unittest.TestCase):
    """Prove the band path on the real official workbooks (Tests 2-7)."""

    def setUp(self):
        self.comparator = Sia4010ComplianceComparator()

    def test_parsers_yield_expected_official_bands(self):
        for config in CONFIGS:
            with self.subTest(test=config["id"]):
                bands = _bands(config["id"])
                self.assertEqual(len(bands), config["bands"])
                self.assertEqual({b.unit for b in bands}, {"kWh"})
                self.assertTrue(all(b.has_band for b in bands))
                self.assertTrue(all(b.case_id and b.metric for b in bands))
                self.assertTrue(
                    _has_pin(bands, config["pin"]),
                    "pinned band {} missing for Test {}".format(
                        config["pin"], config["id"]
                    ),
                )

    def test_within_band_passes_and_outside_fails(self):
        for config in CONFIGS:
            with self.subTest(test=config["id"]):
                bands = _bands(config["id"])
                within = DictResultSource(
                    {
                        b.key: ((b.lower_bound + b.upper_bound) / 2.0, b.unit)
                        for b in bands
                    }
                )
                outcomes = self.comparator.compare_all(
                    bands, build_observed_results(bands, within)
                )
                self.assertTrue(all(o.status == ComparisonStatus.PASS for o in outcomes))

                outside = DictResultSource(
                    {b.key: (b.upper_bound + 1_000_000.0, b.unit) for b in bands}
                )
                outcomes = self.comparator.compare_all(
                    bands, build_observed_results(bands, outside)
                )
                self.assertTrue(all(o.status == ComparisonStatus.FAIL for o in outcomes))

    def test_placeholder_bindings_keep_everything_not_checkable(self):
        for config in CONFIGS:
            with self.subTest(test=config["id"]):
                bands = _bands(config["id"])
                bindings = build_annual_sum_bindings(bands)
                self.assertTrue(bindings)
                self.assertTrue(all(not b.confirmed for b in bindings.values()))
                self.assertEqual(
                    {b.aggregation for b in bindings.values()}, {"annual_sum"}
                )

                def _accessor(binding, expected):
                    """Stub accessor that would leak a value if wrongly called."""
                    return 12345.0

                resolver = VeApsResolver(accessor=_accessor, bindings=bindings)
                observed = build_observed_results(bands, resolver)
                self.assertEqual(observed, ())
                outcomes = self.comparator.compare_all(bands, observed)
                self.assertTrue(
                    all(o.status == ComparisonStatus.NOT_CHECKABLE for o in outcomes)
                )


@unittest.skipUnless(HAS_PKG, "official SIA 4010 package not present")
class AnnualSumBundleWiringTests(unittest.TestCase):
    """Prove manifest/checksum loading and the runner status on real data."""

    @classmethod
    def setUpClass(cls):
        """Assemble one scratch bundle holding the real annual-sum workbooks."""
        cls.bundle = TEST_OUTPUT_ROOT / "bundle"
        for config in CONFIGS:
            workbook = _workbook(config["id"])
            target_dir = cls.bundle / "Test{}".format(config["id"])
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(workbook, target_dir / workbook.name)
        write_manifest(cls.bundle)

    def test_manifest_resolves_every_workbook(self):
        # load_bundle only checksums files (no workbook parse), so this proves
        # multi-test manifest resolution for all six tests cheaply.
        bundle = Sia4010TestRunner().loader.load_bundle(self.bundle)
        resolved = {
            test_id
            for item in bundle.files
            if item.role == "evaluation_workbook"
            for test_id in item.test_ids
        }
        self.assertTrue({c["id"] for c in CONFIGS}.issubset(resolved))

    def test_runner_records_official_results_within_band(self):
        runner = Sia4010TestRunner()
        bands = runner.expected_bands(self.bundle, REPRESENTATIVE_ID)
        self.assertEqual(len(bands), CONFIGS_BY_ID[REPRESENTATIVE_ID]["bands"])
        observed = build_observed_results(
            bands,
            DictResultSource(
                {b.key: ((b.lower_bound + b.upper_bound) / 2.0, b.unit) for b in bands}
            ),
        )
        evaluation = runner.evaluate_test(self.bundle, REPRESENTATIVE_ID, observed)
        self.assertEqual(evaluation.status, "OFFICIAL_RESULTS_RECORDED")
        self.assertEqual(evaluation.counts["PASS"], len(bands))
        self.assertEqual(evaluation.counts["FAIL"], 0)
        class_input = to_test_results_map({REPRESENTATIVE_ID: evaluation})
        self.assertEqual(
            class_input["test_{}".format(REPRESENTATIVE_ID)]["status"],
            "OFFICIAL_RESULTS_RECORDED",
        )

    def test_missing_observed_results_stay_not_checkable(self):
        runner = Sia4010TestRunner()
        evaluation = runner.evaluate_test(self.bundle, REPRESENTATIVE_ID, [])
        self.assertEqual(evaluation.status, "NOT_CHECKABLE")
        self.assertEqual(evaluation.counts["PASS"], 0)
        self.assertEqual(evaluation.counts["FAIL"], 0)

    def test_test7_uses_verified_corrected_workbook(self):
        runner = Sia4010TestRunner()
        bands = runner.expected_bands(self.bundle, "7")
        observed = build_observed_results(
            bands,
            DictResultSource(
                {
                    band.key: (
                        (band.lower_bound + band.upper_bound) / 2.0,
                        band.unit,
                    )
                    for band in bands
                }
            ),
        )
        evaluation = runner.evaluate_test(self.bundle, "7", observed)
        self.assertEqual(evaluation.status, "OFFICIAL_RESULTS_RECORDED")
        self.assertEqual(
            evaluation.criterion_status,
            "CORRECTED_WORKBOOK_VERIFIED_2026-08-10",
        )
        self.assertEqual(
            evaluation.band_status,
            "OFFICIAL_RESULTS_RECORDED",
        )
        self.assertTrue(
            all(c.status == ComparisonStatus.PASS for c in evaluation.comparisons)
        )


if __name__ == "__main__":
    unittest.main()
