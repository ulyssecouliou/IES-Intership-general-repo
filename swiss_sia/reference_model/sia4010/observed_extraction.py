"""Build SIA 4010 observed results from a VE result source (Phase B boundary).

The extractor is EXPECTED-DRIVEN: it iterates the official expected metrics and
asks a resolver for each one's VE/APS value, so observed keys always align with
the expected keys produced by the workbook parsers. A missing value yields no
observed result (the comparator then reports NOT_CHECKABLE); nothing is
fabricated and no unit is converted implicitly.

The real resolver wraps the VE runtime and ApacheSim/APS results and must be
qualified inside VE (Phase B). A dict-backed resolver supports pure-Python dry
runs of the full ingestion -> comparison -> verdict pipeline.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Tuple

from .expected_results import ExpectedResult, ObservedResult

# A resolver maps one expected metric to its (value, unit) from VE, or None when
# the VE/APS quantity is not (yet) available for that metric.
Resolver = Callable[[ExpectedResult], Optional[Tuple[float, str]]]


def build_observed_results(
    expected_results: Iterable[ExpectedResult],
    resolver: Resolver,
    evidence_locator: str = "VE/APS extraction",
) -> Tuple[ObservedResult, ...]:
    """Return observed results for every expected metric the resolver supplies.

    Fail-closed: a metric the resolver cannot supply is simply omitted, so the
    comparator reports it NOT_CHECKABLE rather than inventing a value.
    """

    observed: List[ObservedResult] = []
    for expected in expected_results:
        resolved = resolver(expected)
        if resolved is None:
            continue
        value, unit = resolved
        observed.append(
            ObservedResult(
                test_id=expected.test_id,
                case_id=expected.case_id,
                metric=expected.metric,
                value=float(value),
                unit=str(unit),
                evidence_locator=evidence_locator,
            )
        )
    return tuple(observed)


class DictResultSource:
    """A dry-run resolver keyed by ``ExpectedResult.key`` -> ``(value, unit)``.

    Used to exercise the full Phase B pipeline in pure Python. The real VE/APS
    resolver is a drop-in replacement qualified inside the VE runtime.
    """

    def __init__(self, mapping: Mapping[str, Tuple[float, str]]):
        """Bind the source to a mapping of expected key to (value, unit)."""

        self._mapping: Dict[str, Tuple[float, str]] = dict(mapping)

    def __call__(self, expected: ExpectedResult) -> Optional[Tuple[float, str]]:
        """Resolve one expected metric to its (value, unit), or None if absent."""

        return self._mapping.get(expected.key)


@dataclass(frozen=True)
class MetricBinding:
    """Source-traced binding of one expected metric to a VE/APS quantity.

    ``confirmed`` is True only once the mapping is qualified against the
    installed VE runtime and the APS result contract. Until then the binding is
    a placeholder and the resolver refuses to use it (the metric stays
    NOT_CHECKABLE), so no VE variable name or value is ever invented.
    """

    quantity: str
    unit: str
    aggregation: str = "value"
    confirmed: bool = False
    source_locator: str = "PLACEHOLDER - VE/APS binding to confirm in the runtime"


# Accessor: given a confirmed binding and the expected metric, return the value
# (already in the binding's unit) from the VE/APS results, or None if absent.
ResultAccessor = Callable[[MetricBinding, ExpectedResult], Optional[float]]


class VeApsResolver:
    """Resolve expected metrics from VE/APS results via source-traced bindings.

    Fail-closed on every axis: a metric with no binding, an unconfirmed
    (placeholder) binding, or a value the accessor cannot supply resolves to
    None, so the comparator reports NOT_CHECKABLE rather than inventing a value.
    Units are taken from the binding and never converted implicitly.

    The accessor wraps the VE runtime / APS results and is injected so the
    resolver stays pure-Python testable; the default bindings are empty so the
    resolver invents nothing until real VE-qualified bindings are supplied.
    """

    def __init__(
        self,
        accessor: ResultAccessor,
        bindings: Optional[Mapping[Tuple[str, str], MetricBinding]] = None,
    ):
        """Bind the resolver to a VE/APS accessor and a metric-binding table."""

        self._accessor = accessor
        self._bindings: Dict[Tuple[str, str], MetricBinding] = dict(bindings or {})

    def __call__(self, expected: ExpectedResult) -> Optional[Tuple[float, str]]:
        """Resolve one expected metric to (value, unit), or None (fail-closed)."""

        binding = self._bindings.get((expected.test_id, expected.metric))
        if binding is None or not binding.confirmed:
            return None
        value = self._accessor(binding, expected)
        if value is None:
            return None
        return float(value), binding.unit


# A per-quantity extractor reads one value from the VE/APS results for a binding.
QuantityExtractor = Callable[[Any, MetricBinding, ExpectedResult], Optional[float]]


class VeApsResultAccessor:
    """A ``ResultAccessor`` that reads candidate values from VE/APS results.

    It delegates each quantity to a registered extractor. The extractors are the
    VE-runtime-specific code (using e.g. ``simulation_results.find_aps_variable``
    over an APS ``ResultsReader``) and are qualified during Phase B; this class
    only wires them and enforces fail-closed behaviour:

    - an unregistered quantity -> None (metric stays NOT_CHECKABLE);
    - an extractor that returns None or raises -> None.

    No APS variable name is guessed here, so nothing is fabricated. The APS
    results object is injected, keeping the accessor pure-Python testable.
    """

    def __init__(
        self,
        aps_results: Any,
        quantity_extractors: Optional[Mapping[str, QuantityExtractor]] = None,
    ):
        """Bind the accessor to an APS results object and per-quantity extractors."""

        self._aps = aps_results
        self._extractors: Dict[str, QuantityExtractor] = dict(quantity_extractors or {})

    def register(self, quantity: str, extractor: QuantityExtractor) -> None:
        """Register a confirmed per-quantity extractor (added during VE qualification)."""

        self._extractors[quantity] = extractor

    def __call__(
        self, binding: MetricBinding, expected: ExpectedResult
    ) -> Optional[float]:
        """Return the candidate value for one binding, or None (fail-closed)."""

        extractor = self._extractors.get(binding.quantity)
        if extractor is None:
            return None
        try:
            value = extractor(self._aps, binding, expected)
        except Exception:
            return None  # fail-closed on any extraction error inside the runtime
        return None if value is None else float(value)
