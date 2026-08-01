"""Placeholder VE/APS metric bindings for SIA 4010 Test 1 (BESTEST case 1E).

Test 1 compares the candidate program's sensible heating/cooling energy and
annual peak loads for the scored case 1E against the official reference band.
This module enumerates one :class:`MetricBinding` per official expected metric
so the VE Phase B qualification has a concrete, complete target list.

Every binding is ``confirmed=False`` on purpose: until the VE/APS variable and
aggregation are qualified inside the IESVE runtime, :class:`VeApsResolver`
refuses to use the binding and the metric stays ``NOT_CHECKABLE``. Nothing here
invents a VE variable name or a candidate value; the ``quantity`` and
``aggregation`` fields describe the physical target only, and the reference band
itself still comes solely from the official workbook parser.
"""

from typing import Dict, Iterable, Tuple

from .expected_results import ExpectedResult
from .observed_extraction import MetricBinding


def _row_label(metric: str) -> str:
    """Return the trailing row label of a parsed Test 1 metric (after ``|``)."""

    return metric.rsplit("|", 1)[-1].strip() if "|" in metric else ""


def classify_test1_metric(expected: ExpectedResult) -> MetricBinding:
    """Return a source-traced placeholder binding for one Test 1 metric.

    The physical quantity and aggregation are derived from the official metric
    label; the unit is taken verbatim from the parsed band so the observed
    extractor must match the exact official unit. The binding stays unconfirmed
    until qualified against the VE/APS result contract.
    """

    label = _row_label(expected.metric)
    low = expected.metric.lower()
    label_low = label.lower()
    if "peak" in low:
        side = "heating" if label_low == "heating" else (
            "cooling" if label_low == "cooling" else "load"
        )
        quantity = "annual peak {} load".format(side)
        aggregation = "annual_peak"
    else:
        if "heating" in low:
            side = "heating"
        elif "cooling" in low:
            side = "cooling"
        else:
            side = "sensible"
        if label_low == "annual":
            aggregation = "annual_sum"
            scope = "annual"
        else:
            aggregation = "monthly_sum"
            scope = "month {}".format(label) if label else "monthly"
        quantity = "sensible {} energy ({})".format(side, scope)
    return MetricBinding(
        quantity=quantity,
        unit=expected.unit,
        aggregation=aggregation,
        confirmed=False,
        source_locator=(
            "PLACEHOLDER - confirm the VE/APS variable and {} aggregation for "
            "case 1E metric '{}' (official band at {}) in the IESVE runtime".format(
                aggregation, expected.metric, expected.source_locator
            )
        ),
    )


def build_test1_bindings(
    expected_results: Iterable[ExpectedResult],
) -> Dict[Tuple[str, str], MetricBinding]:
    """Return the ``(test_id, metric) -> MetricBinding`` table for Test 1.

    Keyed exactly as :class:`VeApsResolver` looks bindings up, so every parsed
    case 1E metric has a placeholder target. All bindings are unconfirmed, so
    the resolver supplies nothing and every metric remains ``NOT_CHECKABLE``
    until VE qualification replaces these with confirmed bindings.
    """

    return {
        (expected.test_id, expected.metric): classify_test1_metric(expected)
        for expected in expected_results
    }
