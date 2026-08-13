"""Evaluate one active one-zone SIA 4010 APS case with qualified bindings.

The installed runtime probe qualifies Test 1 sensible-load and Test 2
total-solar-gain variables.  Test 1 cases without official acceptance bounds
are recorded as reference-only results and are never presented as compliant.
Every case requiring an unqualified APS quantity is rejected.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from ..exceptions import ConfigurationError
from .case_registry import all_case_capabilities, get_case_capability
from .distribution_reference import (
    DISTRIBUTION_CRITERIA,
    build_distribution_bands,
    evaluate_distribution_criteria,
)
from .expected_results import ExpectedResult
from .qualified_aps import QualifiedApsBindings, Sia4010QualifiedApsExtractor
from .compliance_comparator import (
    ComparisonStatus,
    Sia4010ComplianceComparator,
)
from .test1_iso_reference import (
    CATALOG_RELATIVE_PATH,
    load_test1_iso_reference_results,
)
from .test_runner import Sia4010TestEvaluation, Sia4010TestRunner


REFERENCE_ONLY_RESULTS_RECORDED = (
    "REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION"
)

#: Cases 1A to 1D differ from 600/640/900/940 in a way that matters: those have
#: reference results to be shown against, these have none at all. The status
#: says both absences out loud so no reader supplies either from habit.
DIAGNOSTIC_DELIVERABLE_RECORDED = (
    "DIAGNOSTIC_DELIVERABLE_RECORDED_NO_CRITERION_NO_REFERENCE"
)

#: The APS evaluation scope that routes to the criterion-free deliverable path.
HOURLY_DELIVERABLE_SCOPE = "HOURLY_DELIVERABLE_ONLY_NO_REFERENCE"


QUALIFIED_ACTIVE_CASES = frozenset(
    (item.variant, item.case_id)
    for item in all_case_capabilities()
    if item.aps_evaluation_supported
)


def _sha256(path: Path) -> str:
    """Return one lowercase file checksum."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Atomically write one deterministic UTF-8 JSON artifact."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _reference_deviation_diagnostics(
    comparisons: Iterable[Any],
) -> List[Dict[str, Any]]:
    """Return non-normative signed deviations for reference-only results.

    ISO 52016-1 Clause 7.2 publishes comparison values but the supplied pages
    do not define an acceptance tolerance. These diagnostics therefore help
    locate modelling differences without turning them into a compliance
    verdict.
    """

    diagnostics = []
    for comparison in comparisons:
        expected = comparison.expected_value
        observed = comparison.observed_value
        if expected is None or observed is None:
            continue
        signed = float(observed) - float(expected)
        diagnostics.append(
            {
                "key": comparison.key,
                "expected_value": float(expected),
                "observed_value": float(observed),
                "unit": comparison.unit,
                "signed_difference": signed,
                "absolute_difference": abs(signed),
                "relative_difference_percent": (
                    None
                    if float(expected) == 0.0
                    else 100.0 * signed / abs(float(expected))
                ),
                "status": comparison.status.value,
                "normative_verdict_allowed": False,
                "source_locator": comparison.source_locator,
            }
        )
    return diagnostics


def _test2_case_label(case_id: str) -> str:
    """Return the official workbook label for one exact Test 2 case."""

    return "Test 2 {}".format(str(case_id)[-1].upper())


def _selected_expected(
    expected: Tuple[ExpectedResult, ...],
    test_id: str,
    case_id: str,
) -> Tuple[ExpectedResult, ...]:
    """Return only the official metrics belonging to the active exact case."""

    expected_case_id = "1E" if test_id == "1" else _test2_case_label(case_id)
    selected = tuple(
        item for item in expected if item.case_id == expected_case_id
    )
    if not selected:
        raise ConfigurationError(
            "Official workbook contains no expected metrics for {}/{}".format(
                test_id, case_id
            )
        )
    return selected


@dataclass(frozen=True)
class ActiveCaseEvaluationReceipt:
    """Source-traced result of one qualified active-case APS comparison."""

    status: str
    variant: str
    case_id: str
    test_id: str
    observed_metric_count: int
    distribution_criterion_count: int
    acceptance_criterion_available: bool
    required_output_scope_complete: bool
    artifact_path: Optional[Path]
    #: Absent for the diagnostic cases 1A to 1D. They have no criterion and no
    #: reference, so nothing is evaluated; carrying an empty evaluation object
    #: here would read as "evaluated, found nothing".
    evaluation: Optional[Sia4010TestEvaluation] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe receipt."""

        return {
            "status": self.status,
            "variant": self.variant,
            "case_id": self.case_id,
            "test_id": self.test_id,
            "observed_metric_count": self.observed_metric_count,
            "distribution_criterion_count": self.distribution_criterion_count,
            "acceptance_criterion_available": (
                self.acceptance_criterion_available
            ),
            "required_output_scope_complete": (
                self.required_output_scope_complete
            ),
            "artifact_path": (
                str(self.artifact_path) if self.artifact_path else None
            ),
            "evaluation": (
                self.evaluation.to_dict()
                if self.evaluation is not None
                else None
            ),
        }


def _record_test1_diagnostic_deliverable(
    *,
    variant: str,
    case_id: str,
    extractor: "Sia4010QualifiedApsExtractor",
    aps: Path,
    bindings_path: Path,
    output_path: Optional[Union[str, Path]],
) -> ActiveCaseEvaluationReceipt:
    """Record the annual hourly deliverable of one diagnostic case 1A to 1D.

    These four cases take a separate path on purpose. The ISO reference-only
    path compares the run against ISO 52016-1 chapter 7 reference results, and
    that comparison is impossible here for two independent reasons: the
    diagnostic cases run under the Zurich-Kloten climate rather than DRYCOLD, so
    they are not ISO cases; and `test-1.ref.json` carries no reference for them
    at all. Routing them through that path would have produced a deviation
    against the wrong object, which is the one failure mode this pipeline exists
    to prevent.

    Args:
        variant: Official variant, always ``test_1`` here.
        case_id: One of 1A, 1B, 1C, 1D.
        extractor: Runtime-qualified APS extractor.
        aps: APS evidence file.
        bindings_path: Qualified APS binding file.
        output_path: Where to write the deliverable artifact, if anywhere.

    Returns:
        ActiveCaseEvaluationReceipt: Receipt with no evaluation attached, whose
        status is the deliverable status when both annual series are complete
        and ``NOT_CHECKABLE`` when either is not.
    """

    deliverable = extractor.test1_diagnostic_hourly_deliverable(case_id)
    complete = deliverable is not None and deliverable.hour_count == 8760
    status = (
        DIAGNOSTIC_DELIVERABLE_RECORDED if complete else "NOT_CHECKABLE"
    )
    artifact = Path(output_path) if output_path is not None else None
    if artifact is not None:
        payload = {
            "schema_version": "1.0",
            "status": status,
            "variant": variant,
            "case_id": str(case_id).upper(),
            "test_id": "1",
            "acceptance_criterion_available": False,
            "reference_results_available": False,
            "compliance_claim_allowed": False,
            "source_evidence": {
                "aps_path": str(aps),
                "aps_sha256": _sha256(aps),
                "bindings_path": str(bindings_path),
                "bindings_sha256": _sha256(bindings_path),
            },
            "deliverable": (
                deliverable.to_dict() if deliverable is not None else None
            ),
            "incompleteness": (
                None
                if complete
                else (
                    "One or both annual power series is absent or is not "
                    "exactly one 365-day year, so no deliverable is recorded. "
                    "A partial year is not delivered as if it were whole."
                )
            ),
        }
        _write_json(artifact, payload)
    return ActiveCaseEvaluationReceipt(
        status=status,
        variant=variant,
        case_id=str(case_id).upper(),
        test_id="1",
        observed_metric_count=(
            2 * deliverable.hour_count if deliverable is not None else 0
        ),
        distribution_criterion_count=0,
        acceptance_criterion_available=False,
        required_output_scope_complete=complete,
        artifact_path=artifact,
        evaluation=None,
    )


def evaluate_qualified_active_case(
    *,
    variant: str,
    case_id: str,
    results_file: Any,
    room_id: Any,
    aps_path: Union[str, Path],
    bundle_root: Union[str, Path],
    bindings_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
) -> ActiveCaseEvaluationReceipt:
    """Extract and compare one active APS case, rejecting unqualified families."""

    pair = (str(variant), str(case_id))
    if pair not in QUALIFIED_ACTIVE_CASES:
        raise ConfigurationError(
            "Qualified active APS evaluation is unavailable for {}/{}; "
            "supported cases are {}".format(
                pair[0],
                pair[1],
                sorted("{}/{}".format(*item) for item in QUALIFIED_ACTIVE_CASES),
            )
        )
    capability = get_case_capability(*pair)
    test_id = capability.base_test_id
    aps = Path(aps_path)
    if not aps.is_file():
        raise ConfigurationError(
            "Active-case APS evidence does not exist: {}".format(aps)
        )
    reference_catalog_path = None
    reference_diagnostics = []
    bindings = QualifiedApsBindings.load(bindings_path)
    runner = Sia4010TestRunner()
    extractor = Sia4010QualifiedApsExtractor(
        results_file,
        room_id,
        bindings,
        "{}#sha256={}".format(aps, _sha256(aps)),
    )

    if capability.aps_evaluation_scope == HOURLY_DELIVERABLE_SCOPE:
        return _record_test1_diagnostic_deliverable(
            variant=pair[0],
            case_id=pair[1],
            extractor=extractor,
            aps=aps,
            bindings_path=Path(bindings_path),
            output_path=output_path,
        )

    distributions = ()
    if test_id == "1":
        required_quantity_ids = (
            (
                "sensible_heating_power",
                "sensible_cooling_power",
            )
            if pair[1] == "1E"
            else (
                "room_air_temperature",
                "operative_temperature",
            )
            if pair[1] in {"600FF", "900FF"}
            else (
                "sensible_heating_power",
                "sensible_cooling_power",
                "room_air_temperature",
                "operative_temperature",
            )
        )
    else:
        required_quantity_ids = ("total_room_solar_heat_gain_power",)
    acceptance_criterion_available = not (
        test_id == "1" and pair[1] != "1E"
    )
    if test_id == "1" and not acceptance_criterion_available:
        observed = extractor.test1_reference_only_observed(pair[1])
        bundle = runner.loader.load_bundle(bundle_root)
        workbook = runner._evaluation_workbook(bundle, "1")
        expected_reference = load_test1_iso_reference_results(
            Path(bundle_root).parent, pair[1]
        )
        reference_catalog_path = (
            Path(bundle_root).parent / CATALOG_RELATIVE_PATH
        )
        reference_comparisons = Sia4010ComplianceComparator().compare_all(
            expected_reference, observed
        )
        reference_diagnostics = _reference_deviation_diagnostics(
            reference_comparisons
        )
        reference_counts = {
            status.value: 0 for status in ComparisonStatus
        }
        for comparison in reference_comparisons:
            reference_counts[comparison.status.value] += 1
        required_metric_count = (
            39 if pair[1] in {"600FF", "900FF"} else 88
        )
        reference_status = (
            REFERENCE_ONLY_RESULTS_RECORDED
            if len(observed) == required_metric_count
            else "NOT_CHECKABLE"
        )
        evaluation = Sia4010TestEvaluation(
            test_id="1",
            bundle=bundle,
            workbook=str(workbook.path),
            comparisons=reference_comparisons,
            counts=reference_counts,
            status=reference_status,
            band_status="NO_ACCEPTANCE_CRITERION",
            variant_statuses={"test_1": reference_status},
            variant_band_statuses={
                "test_1": "NO_ACCEPTANCE_CRITERION"
            },
            variant_counts={"test_1": dict(reference_counts)},
        )
    else:
        expected_all = runner.expected_bands(bundle_root, test_id)
        expected = _selected_expected(expected_all, test_id, pair[1])
    if test_id == "1" and acceptance_criterion_available:
        observed = extractor.test1_observed(expected)
    elif test_id == "2":
        observed = extractor.test2_observed(expected)
        criterion = DISTRIBUTION_CRITERIA["2"]
        bundle = runner.loader.load_bundle(bundle_root)
        workbook = runner._evaluation_workbook(bundle, "2")
        quantities = criterion["quantities"]
        bands = build_distribution_bands(
            workbook.path,
            (pair[1],),
            quantities,
            candidate_sheet=criterion["candidate_sheet"],
            data_prefix=criterion["data_prefix"],
        )
        candidate = {}
        for quantity in quantities:
            band = bands.get((pair[1], quantity.header_label))
            if band is not None:
                counts = extractor.test2_solar_distribution(
                    band.upper_edges,
                    include_overflow=band.include_overflow,
                )
                if counts:
                    candidate[(pair[1], quantity.header_label)] = counts
        distributions = evaluate_distribution_criteria(
            workbook.path,
            (pair[1],),
            quantities,
            candidate_distributions=candidate,
            candidate_sheet=criterion["candidate_sheet"],
            data_prefix=criterion["data_prefix"],
        )

    if acceptance_criterion_available:
        evaluation = runner.evaluate_test(
            bundle_root,
            test_id,
            observed,
            distribution_outcomes=distributions,
        )
    if test_id == "1":
        selected_status = evaluation.status
    else:
        selected_status = evaluation.variant_statuses.get(
            pair[0], "NOT_CHECKABLE"
        )
    series_evidence = extractor.series_evidence(required_quantity_ids)
    runtime_scope_complete = (
        len(series_evidence) == len(required_quantity_ids)
    )
    artifact = Path(output_path) if output_path is not None else None
    receipt = ActiveCaseEvaluationReceipt(
        status=selected_status,
        variant=pair[0],
        case_id=pair[1],
        test_id=test_id,
        observed_metric_count=len(observed),
        distribution_criterion_count=len(distributions),
        acceptance_criterion_available=acceptance_criterion_available,
        required_output_scope_complete=(
            capability.aps_full_evaluation_supported
            and runtime_scope_complete
        ),
        artifact_path=artifact,
        evaluation=evaluation,
    )
    if artifact is not None:
        source_evidence = {
            "aps_path": str(aps),
            "aps_sha256": _sha256(aps),
            "bindings_path": str(Path(bindings_path)),
            "bindings_sha256": _sha256(Path(bindings_path)),
            "official_bundle": str(Path(bundle_root)),
        }
        if reference_catalog_path is not None:
            source_evidence["iso52016_test1_reference_catalog"] = {
                "path": str(reference_catalog_path),
                "sha256": _sha256(reference_catalog_path),
                "acceptance_tolerance_available": False,
            }
        payload = {
            "schema_version": "1.0",
            **receipt.to_dict(),
            "source_evidence": source_evidence,
            "observed_results": [item.to_dict() for item in observed],
            "reference_only_deviation_diagnostics": reference_diagnostics,
            "qualified_series_evidence": series_evidence,
            "claim_guardrail": (
                "A reference-only result has no compliance verdict when the "
                "official source supplies no acceptance criterion. An "
                "official-band result is a technical comparison only; it is "
                "not an SIA attestation and does not qualify unbound APS metrics."
            ),
        }
        _write_json(artifact, payload)
    return receipt
