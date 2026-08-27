"""Read-only diagnostics for APS versus EPW hourly indexing.

The ISO Test 1 tables number hours from 1 to 24, while result-file APIs may
expose samples at the beginning or the end of a reporting interval.  This
module does not change or relabel results.  It compares an APS weather series
with the project EPW and reports every tested integer-hour alignment so that a
time convention can be qualified from engine evidence rather than selected to
improve agreement with the ISO reference outputs.
"""

import csv
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Sequence, Tuple, Union


@dataclass(frozen=True)
class HourAlignment:
    """One candidate alignment between EPW hours and APS result indices."""

    aps_index_offset_hours: int
    sample_count: int
    mean_absolute_difference_c: float
    root_mean_square_difference_c: float
    maximum_absolute_difference_c: float

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe diagnostic record."""

        return asdict(self)


def read_epw_dry_bulb_c(path: Union[str, Path]) -> Tuple[float, ...]:
    """Read the 8760 EPW dry-bulb values in file order.

    EPW column 7 (zero-based index 6) is dry-bulb temperature.  The function
    deliberately requires a non-leap complete year because the qualified
    Test 1 APS extraction uses the same 8760-hour contract.
    """

    weather_path = Path(path)
    values = []
    with weather_path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.reader(handle)
        for line_number, row in enumerate(reader, start=1):
            if line_number <= 8:
                continue
            if len(row) <= 6:
                raise ValueError(
                    "EPW data row {} has fewer than seven columns".format(line_number)
                )
            try:
                values.append(float(row[6]))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "Invalid EPW dry-bulb value at row {}: {!r}".format(
                        line_number, row[6]
                    )
                ) from exc
    if len(values) != 8760:
        raise ValueError(
            "Expected 8760 EPW records, found {} in {}".format(len(values), weather_path)
        )
    return tuple(values)


def aggregate_hourly_means(
    values: Sequence[float], results_per_hour: float
) -> Tuple[float, ...]:
    """Return hourly means from a complete integer-frequency APS series."""

    steps = int(round(float(results_per_hour)))
    if steps <= 0 or not math.isclose(
        float(results_per_hour), float(steps), rel_tol=0.0, abs_tol=1.0e-9
    ):
        raise ValueError(
            "APS results_per_hour must be a positive integer, found {!r}".format(
                results_per_hour
            )
        )
    expected = 8760 * steps
    if len(values) != expected:
        raise ValueError(
            "Expected {} APS weather samples, found {}".format(expected, len(values))
        )
    return tuple(
        sum(float(value) for value in values[index : index + steps]) / steps
        for index in range(0, len(values), steps)
    )


def compare_hour_alignments(
    epw_hour_ending: Sequence[float],
    aps_hourly: Sequence[float],
    offsets: Iterable[int] = range(-3, 4),
) -> Tuple[HourAlignment, ...]:
    """Compare APS indices ``i + offset`` with EPW hour-ending record ``i``."""

    if len(epw_hour_ending) != 8760 or len(aps_hourly) != 8760:
        raise ValueError("Hourly alignment requires two complete 8760-value years")
    diagnostics = []
    for offset_value in offsets:
        offset = int(offset_value)
        differences = [
            abs(float(epw_hour_ending[index]) - float(aps_hourly[index + offset]))
            for index in range(8760)
            if 0 <= index + offset < 8760
        ]
        if not differences:
            continue
        diagnostics.append(
            HourAlignment(
                aps_index_offset_hours=offset,
                sample_count=len(differences),
                mean_absolute_difference_c=sum(differences) / len(differences),
                root_mean_square_difference_c=math.sqrt(
                    sum(value * value for value in differences) / len(differences)
                ),
                maximum_absolute_difference_c=max(differences),
            )
        )
    return tuple(
        sorted(
            diagnostics,
            key=lambda item: (
                item.root_mean_square_difference_c,
                item.mean_absolute_difference_c,
                abs(item.aps_index_offset_hours),
            ),
        )
    )


def build_hour_convention_diagnostic(
    epw_hour_ending: Sequence[float],
    aps_values: Sequence[float],
    results_per_hour: float,
) -> Dict[str, Any]:
    """Build a fail-closed, non-compliance APS/EPW alignment diagnostic."""

    aps_hourly = aggregate_hourly_means(aps_values, results_per_hour)
    alignments = compare_hour_alignments(epw_hour_ending, aps_hourly)
    if not alignments:
        raise ValueError("No APS/EPW hourly alignment could be evaluated")
    best = alignments[0]
    zero = next(item for item in alignments if item.aps_index_offset_hours == 0)
    improvement = (
        0.0
        if zero.root_mean_square_difference_c == 0.0
        else 1.0 - best.root_mean_square_difference_c / zero.root_mean_square_difference_c
    )
    if best.aps_index_offset_hours == 0:
        status = "APS_INDEX_ALIGNS_WITH_EPW_FILE_ORDER"
    elif improvement >= 0.25:
        status = "NONZERO_APS_INDEX_OFFSET_REQUIRES_BINDING_REVIEW"
    else:
        status = "HOUR_CONVENTION_INCONCLUSIVE"
    return {
        "schema_version": "1.0",
        "status": status,
        "results_per_hour": float(results_per_hour),
        "best_alignment": best.to_dict(),
        "zero_offset_alignment": zero.to_dict(),
        "rmse_improvement_over_zero_fraction": improvement,
        "alignments": [item.to_dict() for item in alignments],
        "interpretation": (
            "aps_index_offset_hours means APS[i + offset] was compared with "
            "EPW hour-ending record i. This diagnostic does not authorize "
            "re-indexing ISO outputs without a reviewed engine-time binding."
        ),
        "compliance_claim_allowed": False,
    }
