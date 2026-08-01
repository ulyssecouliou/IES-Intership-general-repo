"""Reusable placeholder VE/APS bindings for annual-sum SIA 4010 tests.

Tests 3, 4, 6 and 7 each compare one or more annual energy quantities (kWh)
against the official reference band. This builds one unconfirmed
:class:`MetricBinding` per ``(test_id, metric)`` so the VE Phase B qualification
has a concrete target list. Until a binding is confirmed against the installed
runtime, :class:`VeApsResolver` supplies nothing and the metric stays
``NOT_CHECKABLE``; no VE variable name or candidate value is invented here. The
``quantity`` is the official metric label read verbatim from the workbook, and
the reference band still comes solely from the workbook parser.
"""

from typing import Dict, Iterable, Tuple

from .expected_results import ExpectedResult
from .observed_extraction import MetricBinding


def build_annual_sum_bindings(
    expected_results: Iterable[ExpectedResult],
) -> Dict[Tuple[str, str], MetricBinding]:
    """Return the ``(test_id, metric) -> MetricBinding`` table for annual-sum tests.

    Keyed exactly as :class:`VeApsResolver` looks bindings up. Every binding is
    unconfirmed, so the resolver supplies nothing and every metric remains
    ``NOT_CHECKABLE`` until VE qualification replaces these with confirmed
    bindings (the per-case value is then selected by the accessor using the
    expected result's case id).
    """

    bindings: Dict[Tuple[str, str], MetricBinding] = {}
    for expected in expected_results:
        bindings[(expected.test_id, expected.metric)] = MetricBinding(
            quantity=expected.metric,
            unit=expected.unit,
            aggregation="annual_sum",
            confirmed=False,
            source_locator=(
                "PLACEHOLDER - confirm the VE/APS variable and annual-sum "
                "aggregation for '{}' (official band at {}) in the IESVE "
                "runtime".format(expected.metric, expected.source_locator)
            ),
        )
    return bindings
