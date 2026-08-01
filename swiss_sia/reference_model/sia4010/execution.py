"""Orchestrate SIA 4010 official test execution (Phase B) end to end.

Loads a checksum-verified official bundle, extracts candidate (VE/APS) results
for each registered test via a resolver, evaluates every test against its
official reference band, and produces a conservative summary. Fail-closed
throughout: a resolver that cannot supply a metric leaves it NOT_CHECKABLE;
nothing is fabricated, and reaching a band is never SIA validation.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple, Union

from .distribution_reference import DISTRIBUTION_CRITERIA, evaluate_distribution_criteria
from .observed_extraction import Resolver, build_observed_results
from .test_runner import (
    Sia4010TestEvaluation,
    Sia4010TestRunner,
    _TEST_PARSERS,
    to_test_results_map,
)


@dataclass(frozen=True)
class Sia4010ExecutionSummary:
    """Result of running every registered SIA 4010 test in one bundle."""

    bundle_root: str
    issued_by: str
    evaluations: Dict[str, Sia4010TestEvaluation]
    test_results_map: Dict[str, Any]

    @property
    def statuses(self) -> Dict[str, str]:
        """Return the per-test status map (test id -> conservative status)."""

        return {test_id: ev.status for test_id, ev in self.evaluations.items()}

    def to_dict(self) -> Dict[str, Any]:
        """Return the execution summary as serializable data."""

        return {
            "bundle_root": self.bundle_root,
            "issued_by": self.issued_by,
            "statuses": self.statuses,
            "test_results_map": self.test_results_map,
            "tests": {
                test_id: ev.to_dict() for test_id, ev in self.evaluations.items()
            },
        }


def run_all_tests(
    bundle_path: Union[str, Path],
    resolver: Resolver,
    runner: Optional[Sia4010TestRunner] = None,
    candidate_distributions_by_test: Optional[
        Mapping[str, Mapping[Tuple[str, str], Sequence[int]]]
    ] = None,
) -> Sia4010ExecutionSummary:
    """Evaluate every registered test present in the bundle against its band.

    For each test the official expected bands drive the resolver (so observed
    keys align), observed results are built fail-closed, and the test is
    evaluated. The resulting per-test status map is ready for the class matrix
    cross-check; it never upgrades a class on its own.
    """

    runner = runner or Sia4010TestRunner()
    candidate_distributions_by_test = candidate_distributions_by_test or {}
    bundle = runner.loader.load_bundle(bundle_path)
    present = sorted(
        {
            test_id
            for item in bundle.files
            if item.role == "evaluation_workbook"
            for test_id in item.test_ids
        }
        & set(_TEST_PARSERS)
    )
    evaluations: Dict[str, Sia4010TestEvaluation] = {}
    for test_id in present:
        expected = runner.expected_bands(bundle_path, test_id)
        observed = build_observed_results(expected, resolver)
        distribution_outcomes = ()
        criteria = DISTRIBUTION_CRITERIA.get(test_id)
        if criteria is not None:
            # The candidate distribution needs VE hourly APS output, absent here,
            # so it resolves fail-closed to NOT_CHECKABLE and only lowers the
            # verdict; the reference band still comes from the official workbook.
            workbook_file = runner._evaluation_workbook(bundle, test_id)
            distribution_outcomes = evaluate_distribution_criteria(
                workbook_file.path,
                criteria["case_ids"],
                criteria["quantities"],
                candidate_distributions=candidate_distributions_by_test.get(
                    test_id
                ),
                candidate_sheet=criteria.get("candidate_sheet", "Daten_Testprogramm"),
                data_prefix=criteria.get("data_prefix", "Daten_"),
                layout=criteria.get("layout", "inline_header"),
                scored_section=criteria.get("scored_section", ""),
                diagnostic_section=criteria.get("diagnostic_section", ""),
            )
        evaluations[test_id] = runner.evaluate_test(
            bundle_path, test_id, observed, distribution_outcomes=distribution_outcomes
        )
    return Sia4010ExecutionSummary(
        bundle_root=str(bundle.root),
        issued_by=bundle.issued_by,
        evaluations=evaluations,
        test_results_map=to_test_results_map(evaluations),
    )
