"""Comparison engine that refuses to invent SIA 4010 tolerances."""

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, Iterable, Optional, Tuple

from .expected_results import ExpectedResult, ObservedResult


class ComparisonStatus(str, Enum):
    """Possible outcomes for one future SIA 4010 comparison."""

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_CHECKABLE = "NOT_CHECKABLE"


@dataclass(frozen=True)
class ComparisonOutcome:
    """Auditable comparison of one expected and observed metric."""

    key: str
    status: ComparisonStatus
    message: str
    expected_value: Optional[float]
    observed_value: Optional[float]
    unit: str
    absolute_difference: Optional[float]
    allowed_absolute_difference: Optional[float]
    source_locator: str
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return this comparison outcome as serializable data."""

        data = asdict(self)
        data["status"] = self.status.value
        return data


class Sia4010ComplianceComparator:
    """Compare only where the official bundle supplies an acceptance tolerance."""

    @staticmethod
    def _allowed_difference(expected: ExpectedResult) -> Optional[float]:
        """Derive allowed difference solely from source-provided tolerances."""

        candidates = []
        if expected.absolute_tolerance is not None:
            candidates.append(abs(expected.absolute_tolerance))
        if expected.relative_tolerance is not None:
            candidates.append(
                abs(expected.expected_value) * abs(expected.relative_tolerance)
            )
        return max(candidates) if candidates else None

    def compare_one(
        self, expected: ExpectedResult, observed: Optional[ObservedResult]
    ) -> ComparisonOutcome:
        """Compare one metric without conversions or invented tolerances."""

        if observed is None:
            return ComparisonOutcome(
                key=expected.key,
                status=ComparisonStatus.NOT_CHECKABLE,
                message="Observed result is missing",
                expected_value=expected.expected_value,
                observed_value=None,
                unit=expected.unit,
                absolute_difference=None,
                allowed_absolute_difference=self._allowed_difference(expected),
                source_locator=expected.source_locator,
            )
        if observed.unit != expected.unit:
            return ComparisonOutcome(
                key=expected.key,
                status=ComparisonStatus.NOT_CHECKABLE,
                message="Unit mismatch; no implicit conversion is permitted",
                expected_value=expected.expected_value,
                observed_value=observed.value,
                unit=expected.unit,
                absolute_difference=None,
                allowed_absolute_difference=self._allowed_difference(expected),
                source_locator=expected.source_locator,
            )
        # Prefer the official reference band when the workbook supplies explicit
        # lower/upper acceptance bounds; the candidate must fall within them.
        if expected.has_band:
            within = expected.lower_bound <= observed.value <= expected.upper_bound
            return ComparisonOutcome(
                key=expected.key,
                status=ComparisonStatus.PASS if within else ComparisonStatus.FAIL,
                message=(
                    "Observed result is within the official reference band"
                    if within
                    else "Observed result is outside the official reference band"
                ),
                expected_value=expected.expected_value,
                observed_value=observed.value,
                unit=expected.unit,
                absolute_difference=None,
                allowed_absolute_difference=None,
                source_locator=expected.source_locator,
                lower_bound=expected.lower_bound,
                upper_bound=expected.upper_bound,
            )
        allowed = self._allowed_difference(expected)
        difference = abs(observed.value - expected.expected_value)
        if allowed is None:
            return ComparisonOutcome(
                key=expected.key,
                status=ComparisonStatus.NOT_CHECKABLE,
                message="Official acceptance tolerance is absent; no tolerance was invented",
                expected_value=expected.expected_value,
                observed_value=observed.value,
                unit=expected.unit,
                absolute_difference=difference,
                allowed_absolute_difference=None,
                source_locator=expected.source_locator,
            )
        passed = difference <= allowed
        return ComparisonOutcome(
            key=expected.key,
            status=ComparisonStatus.PASS if passed else ComparisonStatus.FAIL,
            message=(
                "Observed result is within the source-provided tolerance"
                if passed
                else "Observed result exceeds the source-provided tolerance"
            ),
            expected_value=expected.expected_value,
            observed_value=observed.value,
            unit=expected.unit,
            absolute_difference=difference,
            allowed_absolute_difference=allowed,
            source_locator=expected.source_locator,
        )

    def compare_all(
        self,
        expected_results: Iterable[ExpectedResult],
        observed_results: Iterable[ObservedResult],
    ) -> Tuple[ComparisonOutcome, ...]:
        """Compare all expected metrics against observed results by key."""

        observed_by_key = {result.key: result for result in observed_results}
        return tuple(
            self.compare_one(expected, observed_by_key.get(expected.key))
            for expected in expected_results
        )
