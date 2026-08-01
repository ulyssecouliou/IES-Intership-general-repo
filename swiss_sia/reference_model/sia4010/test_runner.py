"""Orchestration hook for official SIA 4010 test execution."""

from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Tuple, Union

from ..exceptions import ConfigurationError
from .compliance_comparator import (
    ComparisonOutcome,
    ComparisonStatus,
    Sia4010ComplianceComparator,
)
from .expected_results import ExpectedResult, ObservedResult
from .frequency_distribution import DistributionOutcome
from .test_loader import BundleFile, OfficialTestBundle, Sia4010TestLoader
from .workbook_loaders import (
    deduplicate_expected_keys,
    parse_test1_reference_bands,
    parse_test2_reference_bands,
    parse_test3_reference_bands,
    parse_test4_reference_bands,
    parse_test5_reference_bands,
    parse_test6_reference_bands,
    parse_test7_reference_bands,
)


@dataclass(frozen=True)
class Sia4010RunResult:
    """Verified source bundle and all resulting metric comparisons."""

    bundle: OfficialTestBundle
    comparisons: Tuple[ComparisonOutcome, ...]

    def to_dict(self) -> Dict[str, Any]:
        """Return bundle provenance and comparisons as serializable data."""

        return {
            "bundle": {
                "root": str(self.bundle.root),
                "schema_version": self.bundle.schema_version,
                "issued_by": self.bundle.issued_by,
                "source_url": self.bundle.source_url,
                "manifest_path": str(self.bundle.manifest_path),
                "files": [
                    {
                        "path": str(item.path),
                        "role": item.role,
                        "sha256": item.sha256,
                        "test_ids": list(item.test_ids),
                    }
                    for item in self.bundle.files
                ],
            },
            "comparisons": [comparison.to_dict() for comparison in self.comparisons],
        }


@dataclass(frozen=True)
class Sia4010TestEvaluation:
    """Aggregate outcome of one SIA 4010 test against the official reference band.

    ``status`` is the conservative combination of the annual-band result
    (``band_status``) and any frequency-distribution outcomes: any FAIL makes it
    ``FAILED``; only when every present criterion is positive is it
    ``OFFICIAL_RESULTS_RECORDED``; otherwise ``NOT_CHECKABLE``.
    """

    test_id: str
    bundle: OfficialTestBundle
    workbook: str
    comparisons: Tuple[ComparisonOutcome, ...]
    counts: Dict[str, int]
    status: str
    band_status: str = ""
    distribution_outcomes: Tuple[DistributionOutcome, ...] = ()
    variant_statuses: Dict[str, str] = field(default_factory=dict)
    variant_band_statuses: Dict[str, str] = field(default_factory=dict)
    variant_counts: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return the evaluation as serializable data."""

        return {
            "test_id": self.test_id,
            "workbook": self.workbook,
            "issued_by": self.bundle.issued_by,
            "counts": dict(self.counts),
            "status": self.status,
            "band_status": self.band_status or self.status,
            "comparisons": [comparison.to_dict() for comparison in self.comparisons],
            "distribution": [asdict(outcome) for outcome in self.distribution_outcomes],
            "variant_statuses": dict(self.variant_statuses or {}),
            "variant_band_statuses": dict(self.variant_band_statuses or {}),
            "variant_counts": {
                key: dict(value)
                for key, value in (self.variant_counts or {}).items()
            },
        }


# Per-test parser for the official evaluation workbook. Each returns the
# explicit reference bands the workbook supplies; tests are added one by one.
_TEST_PARSERS: Dict[str, Callable[..., Tuple[ExpectedResult, ...]]] = {
    "1": parse_test1_reference_bands,
    "2": parse_test2_reference_bands,
    "3": parse_test3_reference_bands,
    "4": parse_test4_reference_bands,
    "5": parse_test5_reference_bands,
    "6": parse_test6_reference_bands,
    "7": parse_test7_reference_bands,
}

# Tests 2, 3 and 5 have two inseparable acceptance criteria in their official
# specifications: the annual result band and an hourly frequency-distribution
# band.  A missing distribution must therefore never be promoted to a pass.
_DISTRIBUTION_REQUIRED_TESTS = frozenset({"2", "3", "5"})


class Sia4010TestRunner:
    """Loads official inputs and compares externally extracted VE results."""

    def __init__(
        self,
        loader: Sia4010TestLoader = None,
        comparator: Sia4010ComplianceComparator = None,
    ):
        """Initialize the runner with replaceable loader and comparator services."""

        self.loader = loader or Sia4010TestLoader()
        self.comparator = comparator or Sia4010ComplianceComparator()

    @staticmethod
    def _evaluation_workbook(bundle: OfficialTestBundle, test_id: str) -> BundleFile:
        """Return the checksum-verified evaluation workbook for one test id."""

        candidates = [
            item
            for item in bundle.files
            if item.role == "evaluation_workbook" and test_id in item.test_ids
        ]
        if len(candidates) != 1:
            raise ConfigurationError(
                "Expected exactly one evaluation workbook for SIA 4010 test {}; found {}".format(
                    test_id, len(candidates)
                )
            )
        return candidates[0]

    def expected_bands(
        self, bundle_path: Union[str, Path], test_id: Union[str, int]
    ) -> Tuple[ExpectedResult, ...]:
        """Return the deduped official reference bands for one test.

        Used by the Phase B executor to drive an observed-result resolver with
        the exact expected metrics, so observed keys align one-to-one.
        """

        test_id = str(test_id)
        parser = _TEST_PARSERS.get(test_id)
        if parser is None:
            raise ConfigurationError(
                "No official-workbook parser is registered for SIA 4010 test {}".format(test_id)
            )
        bundle = self.loader.load_bundle(bundle_path)
        workbook_file = self._evaluation_workbook(bundle, test_id)
        return deduplicate_expected_keys(
            parser(
                workbook_file.path, test_id=test_id, source_checksum=workbook_file.sha256
            )
        )

    @staticmethod
    def _strict_band_status(comparisons: Iterable[ComparisonOutcome]) -> str:
        """Return a positive band status only when every expected metric passes."""

        comparisons = tuple(comparisons)
        if not comparisons:
            return "NO_REFERENCE_BANDS"
        statuses = {comparison.status for comparison in comparisons}
        if ComparisonStatus.FAIL in statuses:
            return "FAILED"
        if statuses == {ComparisonStatus.PASS}:
            return "OFFICIAL_RESULTS_RECORDED"
        return "NOT_CHECKABLE"

    @staticmethod
    def _variant_key(test_id: str, case_id: str) -> str:
        """Return the exact class-matrix key for a scored official case."""

        normalized_test = str(test_id)
        if normalized_test == "1":
            return "test_1"
        compact = "".join(
            character
            for character in str(case_id or "").upper()
            if character.isalnum()
        )
        exact_suffixes = {
            "2": tuple("2{}".format(letter) for letter in "ABCD"),
            "3": tuple("3{}".format(letter) for letter in "ABCDEFGHIJKL"),
            "5": tuple("5{}".format(letter) for letter in "ABCD"),
        }
        if normalized_test in exact_suffixes:
            match = next(
                (
                    suffix
                    for suffix in exact_suffixes[normalized_test]
                    if compact.endswith(suffix)
                ),
                "",
            )
            return "test_{}".format(match) if match else ""
        if normalized_test in {"4", "6", "7"}:
            return "test_{}".format(normalized_test)
        return ""

    @classmethod
    def _variant_outcomes(
        cls,
        test_id: str,
        comparisons: Tuple[ComparisonOutcome, ...],
        distribution_outcomes: Tuple[DistributionOutcome, ...],
    ) -> Tuple[
        Dict[str, str],
        Dict[str, str],
        Dict[str, Dict[str, int]],
    ]:
        """Aggregate comparisons by exact SIA 4010 variant."""

        comparisons_by_variant: Dict[str, list] = {}
        for comparison in comparisons:
            key_parts = str(comparison.key).split("|", 2)
            case_id = key_parts[1] if len(key_parts) >= 2 else ""
            variant = cls._variant_key(test_id, case_id)
            if variant:
                comparisons_by_variant.setdefault(variant, []).append(comparison)

        distributions_by_variant: Dict[str, list] = {}
        for outcome in distribution_outcomes:
            variant = cls._variant_key(test_id, getattr(outcome, "case_id", ""))
            if variant:
                distributions_by_variant.setdefault(variant, []).append(outcome)

        variants = sorted(set(comparisons_by_variant) | set(distributions_by_variant))
        statuses: Dict[str, str] = {}
        band_statuses: Dict[str, str] = {}
        counts: Dict[str, Dict[str, int]] = {}
        for variant in variants:
            variant_comparisons = tuple(comparisons_by_variant.get(variant, ()))
            if str(test_id) == "2":
                comparison_statuses = {
                    comparison.status for comparison in variant_comparisons
                }
                # The Test 2 specification accepts the annual sum of either
                # total solar heat gain OR total transmitted solar radiation.
                # One supplied, passing quantity is therefore sufficient. A
                # supplied value outside its band still fails conservatively.
                if ComparisonStatus.FAIL in comparison_statuses:
                    band_status = "FAILED"
                elif ComparisonStatus.PASS in comparison_statuses:
                    band_status = "OFFICIAL_RESULTS_RECORDED"
                else:
                    band_status = "NOT_CHECKABLE"
            else:
                band_status = cls._strict_band_status(variant_comparisons)
            band_statuses[variant] = band_status
            variant_distributions = tuple(distributions_by_variant.get(variant, ()))
            statuses[variant] = cls._combine_status(band_status, variant_distributions)
            # Tests 2, 3 and 5 have two mandatory acceptance criteria. A passing
            # annual band alone can never make an exact variant positive.
            if (
                str(test_id) in _DISTRIBUTION_REQUIRED_TESTS
                and not variant_distributions
            ):
                statuses[variant] = (
                    "FAILED" if band_status == "FAILED" else "NOT_CHECKABLE"
                )
            counter = Counter(item.status.value for item in variant_comparisons)
            counts[variant] = {
                status.value: counter.get(status.value, 0)
                for status in ComparisonStatus
            }
        return statuses, band_statuses, counts

    @staticmethod
    def _combine_status(
        band_status: str, distribution_outcomes: Tuple[DistributionOutcome, ...]
    ) -> str:
        """Combine the annual-band status with distribution outcomes, conservatively.

        Any FAIL/FAILED wins (``FAILED``); only when every present criterion is
        positive (band ``OFFICIAL_RESULTS_RECORDED`` / distribution ``PASS``) is
        it ``OFFICIAL_RESULTS_RECORDED``; a bundle with no reference band and no
        distribution stays ``NO_REFERENCE_BANDS``; anything else (a missing or
        not-checkable criterion) is ``NOT_CHECKABLE`` - a missing criterion never
        upgrades to a pass.
        """

        statuses = [band_status] + [outcome.status for outcome in distribution_outcomes]
        if any(status in ("FAILED", "FAIL") for status in statuses):
            return "FAILED"
        positive = {"OFFICIAL_RESULTS_RECORDED", "PASS"}
        if statuses and all(status in positive for status in statuses):
            return "OFFICIAL_RESULTS_RECORDED"
        if band_status == "NO_REFERENCE_BANDS" and not distribution_outcomes:
            return "NO_REFERENCE_BANDS"
        return "NOT_CHECKABLE"

    def evaluate_test(
        self,
        bundle_path: Union[str, Path],
        test_id: Union[str, int],
        observed_results: Iterable[ObservedResult],
        distribution_outcomes: Iterable[DistributionOutcome] = (),
    ) -> Sia4010TestEvaluation:
        """Verify a bundle and compare one test's official band to observed results.

        The status is deliberately conservative: reaching every band never reads
        as SIA validation. Results inside the annual band are
        ``OFFICIAL_RESULTS_RECORDED`` (a separate SIA sub-commission attestation
        remains required); any value outside the band is ``FAILED``; a band with
        no comparable observed result stays ``NOT_CHECKABLE``. When a test also
        carries a frequency-distribution criterion, its outcomes are combined in
        (see :meth:`_combine_status`) so an unmet or not-checkable distribution
        can only lower the verdict, never raise it.
        """

        test_id = str(test_id)
        parser = _TEST_PARSERS.get(test_id)
        if parser is None:
            raise ConfigurationError(
                "No official-workbook parser is registered for SIA 4010 test {}".format(test_id)
            )
        bundle = self.loader.load_bundle(bundle_path)
        workbook_file = self._evaluation_workbook(bundle, test_id)
        expected = deduplicate_expected_keys(
            parser(
                workbook_file.path, test_id=test_id, source_checksum=workbook_file.sha256
            )
        )
        comparisons = self.comparator.compare_all(expected, observed_results)
        counts = Counter(comparison.status.value for comparison in comparisons)
        count_map = {status.value: counts.get(status.value, 0) for status in ComparisonStatus}
        band_status = self._strict_band_status(comparisons)
        distribution_outcomes = tuple(distribution_outcomes)
        status = self._combine_status(band_status, distribution_outcomes)
        variant_statuses, variant_band_statuses, variant_counts = self._variant_outcomes(
            test_id,
            comparisons,
            distribution_outcomes,
        )
        if test_id == "2" and variant_statuses:
            exact_band_statuses = set(variant_band_statuses.values())
            if "FAILED" in exact_band_statuses:
                band_status = "FAILED"
            elif exact_band_statuses == {"OFFICIAL_RESULTS_RECORDED"}:
                band_status = "OFFICIAL_RESULTS_RECORDED"
            else:
                band_status = "NOT_CHECKABLE"
            exact_statuses = set(variant_statuses.values())
            if "FAILED" in exact_statuses:
                status = "FAILED"
            elif exact_statuses == {"OFFICIAL_RESULTS_RECORDED"}:
                status = "OFFICIAL_RESULTS_RECORDED"
            else:
                status = "NOT_CHECKABLE"
        return Sia4010TestEvaluation(
            test_id=test_id,
            bundle=bundle,
            workbook=workbook_file.path.name,
            comparisons=comparisons,
            counts=count_map,
            status=status,
            band_status=band_status,
            distribution_outcomes=distribution_outcomes,
            variant_statuses=variant_statuses,
            variant_band_statuses=variant_band_statuses,
            variant_counts=variant_counts,
        )

    def evaluate_all(
        self,
        bundle_path: Union[str, Path],
        observed_by_test: Dict[str, Iterable[ObservedResult]],
        distribution_outcomes_by_test: Dict[
            str, Iterable[DistributionOutcome]
        ] = None,
    ) -> Dict[str, Sia4010TestEvaluation]:
        """Evaluate every registered test whose workbook is present in the bundle."""

        distribution_outcomes_by_test = distribution_outcomes_by_test or {}
        bundle = self.loader.load_bundle(bundle_path)
        present = {
            test_id
            for item in bundle.files
            if item.role == "evaluation_workbook"
            for test_id in item.test_ids
        }
        evaluations: Dict[str, Sia4010TestEvaluation] = {}
        for test_id in sorted(present):
            if test_id in _TEST_PARSERS:
                evaluations[test_id] = self.evaluate_test(
                    bundle_path,
                    test_id,
                    observed_by_test.get(test_id, []),
                    distribution_outcomes=distribution_outcomes_by_test.get(
                        test_id, ()
                    ),
                )
        return evaluations

    def run(
        self,
        bundle_path: Union[str, Path],
        observed_results: Iterable[ObservedResult],
    ) -> "Sia4010RunResult":
        """Compare a bundle's CSV-declared expected results to observed results.

        Legacy path for bundles that ship a normalized ``expected_results_csv``;
        the primary Phase B path is ``evaluate_test`` / ``evaluate_all`` over the
        official workbooks.
        """

        bundle = self.loader.load_bundle(bundle_path)
        expected_results = self.loader.load_expected_results(bundle)
        comparisons = self.comparator.compare_all(expected_results, observed_results)
        return Sia4010RunResult(bundle=bundle, comparisons=comparisons)


def to_test_results_map(
    evaluations: Dict[str, "Sia4010TestEvaluation"]
) -> Dict[str, Dict[str, Any]]:
    """Shape runner evaluations as the ``{test_<id>: {status}}`` map consumed by
    :meth:`SIA4010Checker._evaluate_validation_classes`.

    This is the bridge from the automated official-band comparison to the
    existing class-matrix aggregation (SIA 4010 Table 63); it does not
    re-implement the class logic.
    """

    results = {
        "test_{}".format(test_id): {
            "status": evaluation.status,
            "band_status": evaluation.band_status or evaluation.status,
            "counts": dict(evaluation.counts),
            "workbook": evaluation.workbook,
            "distribution": {
                "criteria": len(evaluation.distribution_outcomes),
                "statuses": dict(
                    Counter(o.status for o in evaluation.distribution_outcomes)
                ),
            },
        }
        for test_id, evaluation in evaluations.items()
    }
    for evaluation in evaluations.values():
        for variant, status in (evaluation.variant_statuses or {}).items():
            base_key = "test_{}".format(evaluation.test_id)
            if variant == base_key:
                # Test 1 is both the base test and the exact class-matrix key;
                # retain its separate annual-band and combined statuses.
                continue
            results[variant] = {
                "status": status,
                "band_status": (evaluation.variant_band_statuses or {}).get(
                    variant, status
                ),
                "counts": dict(
                    (evaluation.variant_counts or {}).get(variant, {})
                ),
                "workbook": evaluation.workbook,
                "distribution": {
                    "criteria": sum(
                        1
                        for outcome in evaluation.distribution_outcomes
                        if Sia4010TestRunner._variant_key(
                            evaluation.test_id,
                            getattr(outcome, "case_id", ""),
                        )
                        == variant
                    ),
                    "statuses": dict(
                        Counter(
                            outcome.status
                            for outcome in evaluation.distribution_outcomes
                            if Sia4010TestRunner._variant_key(
                                evaluation.test_id,
                                getattr(outcome, "case_id", ""),
                            )
                            == variant
                        )
                    ),
                },
            }
    return results
