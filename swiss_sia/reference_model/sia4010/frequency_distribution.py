"""Frequency-distribution criterion for the SIA 4010 evaluation workbooks.

Besides the annual-sum band, these tests require the candidate's hourly
frequency distribution of a quantity (e.g. solar heat gain) to lie "im
Streubereich der Referenzprogramme" - within the scatter band of the reference
programs, bin by bin (Spezifikation_Test2, Testkriterien).

This module is the pure-Python core:

- ``parse_frequency_classes`` reads the official ``Haeufigkeitsklassen`` legend
  (per-quantity class upper edges) verbatim - it invents no bins.
- ``histogram_counts`` bins an hourly series with Excel ``FREQUENCY`` semantics.
  Its optional overflow result is kept separate from the official displayed
  classes, so hours outside the class limits are audited rather than mistaken
  for missing data or silently merged into the last class.
- ``build_scatter_band`` derives the acceptance interval as the per-bin
  ``min(reference programs) .. max(reference programs)`` envelope.
- ``compare_distribution`` reports PASS only when every candidate bin lies in
  that envelope, FAIL outside it, and NOT_CHECKABLE when evidence is missing.

AUTHORITY CLARIFICATION
-----------------------
The workbooks draw the reference histograms but do not calculate a numerical
distribution band. A written clarification from Prof. Gerhard Zweifel received
on 2026-08-10 confirms that ``Streubereich`` is interpretation #1: the envelope
of the reference programs for every frequency class (minimum to maximum).
The same authority clarified that apparent totals below 8,760 in the displayed
histograms do not mean that the reference series are incomplete: some hourly
values fall outside the class boundaries. Those hours remain part of the source
series and are reported separately as overflow; they are not an invented scored
class.

The formerly inferred symmetric band ``mean +/- max deviation`` is retained as
diagnostic metadata only, to preserve auditability of results produced before
the clarification. It is no longer an acceptance criterion.

NOTE ON THE CONTRIBUTING SET
----------------------------
This module bands whatever programs it is handed. Which programs those should be
is not derivable from a general rule: for the Test 2 annual band the SIA averages
one variant per program, and not the same variant across programs (IDA_ICE "Fe
det Spec", Excel, Energy+ "Fe einf", TAS "Fe det nonSpect" - the other variant
columns are excluded). A program that did not deliver a case drops out of the
average and is never counted as zero. The safe rule is to read the contributing
set from the workbook's own annual-band ``AVERAGE`` formula and apply the same
set to the bins. ``build_distribution_bands`` currently contributes every
``Daten_*`` sheet that supplied a series, which is NOT the same selection - see
the open point in the arbitration document.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from openpyxl import load_workbook


@dataclass(frozen=True)
class FrequencyClasses:
    """Official histogram class definition for one quantity (verbatim edges)."""

    quantity: str
    unit: str
    upper_edges: Tuple[float, ...]
    source_locator: str


@dataclass(frozen=True)
class DistributionBand:
    """Per-bin scatter band built from the reference programs.

    ``lower_counts`` / ``upper_counts`` are the ACCEPTANCE band: the per-bin
    minimum and maximum across the contributing reference programs.

    ``envelope_lower_counts`` / ``envelope_upper_counts`` repeat that accepted
    envelope for backward-compatible reports. ``symmetric_*`` contains the old
    inferred mean-plus-deviation diagnostic and is never used for a verdict.

    ``include_overflow`` records whether the final Excel ``FREQUENCY`` overflow
    result is scored. Official workbook bands set it to ``False`` because the
    workbook charts only the declared classes; generic callers may retain the
    full Excel result. ``outside_class_counts`` preserves the excluded overflow
    count per reference program for the audit trail.
    """

    quantity: str
    unit: str
    upper_edges: Tuple[float, ...]
    lower_counts: Tuple[float, ...]
    upper_counts: Tuple[float, ...]
    program_count: int
    source_locator: str
    envelope_lower_counts: Tuple[float, ...] = ()
    envelope_upper_counts: Tuple[float, ...] = ()
    symmetric_lower_counts: Tuple[float, ...] = ()
    symmetric_upper_counts: Tuple[float, ...] = ()
    include_overflow: bool = True
    reference_hour_totals: Tuple[Tuple[str, int], ...] = ()
    outside_class_counts: Tuple[Tuple[str, int], ...] = ()
    incomplete_reference_programs: Tuple[str, ...] = ()


class DistributionStatus:
    """String outcomes for a distribution comparison (mirrors ComparisonStatus)."""

    PASS = "PASS"
    # Retained only for backward-compatible deserialization of historical
    # reports. New comparisons never emit this status after the clarification.
    PASS_WITH_RESERVATION = "PASS_WITH_RESERVATION"
    FAIL = "FAIL"
    NOT_CHECKABLE = "NOT_CHECKABLE"

    @staticmethod
    def is_passing(status: str) -> bool:
        """Whether a status counts as meeting the criterion.

        Historical reserved passes remain passing when old reports are read.
        """

        return status in (DistributionStatus.PASS,
                          DistributionStatus.PASS_WITH_RESERVATION)


@dataclass(frozen=True)
class DistributionOutcome:
    """Auditable result of one candidate distribution against a reference band."""

    quantity: str
    unit: str
    status: str
    message: str
    out_of_band_bins: Tuple[int, ...]
    program_count: int
    source_locator: str
    case_id: str = ""


def _is_number(value: Any) -> bool:
    """Return whether a cell value is a real number (not a bool)."""

    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _dedupe_trailing_padding(edges: Sequence[float]) -> Tuple[float, ...]:
    """Collapse repeated trailing catch-all edges (e.g. 9999, 9999, ...) to one."""

    cleaned: List[float] = []
    for edge in edges:
        if cleaned and edge == cleaned[-1]:
            continue  # drop a repeated edge (padding rows in the legend)
        cleaned.append(edge)
    return tuple(cleaned)


def parse_frequency_classes(
    workbook_path: Union[str, Path],
    sheet_name: str = "Haeufigkeitsklassen",
) -> Dict[str, FrequencyClasses]:
    """Parse the official class legend into ``{quantity_label: FrequencyClasses}``.

    The legend lists a class index in the first column and one column per
    quantity, whose header row carries the quantity label and the next row its
    unit; the class upper edges follow downward. Edges are read verbatim.
    """

    path = Path(workbook_path)
    workbook = load_workbook(path, data_only=True, read_only=True)
    try:
        if sheet_name not in workbook.sheetnames:
            return {}
        worksheet = workbook[sheet_name]
        rows = [list(row) for row in worksheet.iter_rows(values_only=True)]
    finally:
        workbook.close()
    if len(rows) < 4:
        return {}

    # Row layout: label row, unit row, then edges. The first column is the class
    # index; quantity columns start at the first column carrying a label.
    label_row = rows[1]
    unit_row = rows[2] if len(rows) > 2 else []
    result: Dict[str, FrequencyClasses] = {}
    for col in range(1, len(label_row)):
        label = label_row[col]
        if not isinstance(label, str) or not label.strip():
            continue
        unit = ""
        if col < len(unit_row) and isinstance(unit_row[col], str):
            unit = unit_row[col].strip()
        edges: List[float] = []
        for row in rows[3:]:
            if col >= len(row):
                continue
            value = row[col]
            if _is_number(value):
                edges.append(float(value))
        if not edges:
            continue
        result[label.strip()] = FrequencyClasses(
            quantity=label.strip(),
            unit=unit,
            upper_edges=_dedupe_trailing_padding(edges),
            source_locator="{}!{}".format(path.name, sheet_name),
        )
    return result


def histogram_counts(
    values: Iterable[Any],
    upper_edges: Sequence[float],
    include_overflow: bool = True,
) -> Tuple[int, ...]:
    """Bin numeric ``values`` into classes with Excel ``FREQUENCY`` semantics.

    Class ``i`` counts
    ``edge[i-1] < v <= edge[i]`` (class 0 is ``v <= edge[0]``), and the final
    Excel result counts the overflow ``v > edge[-1]``. When
    ``include_overflow`` is false, that last result is omitted to reproduce the
    classes displayed in the SIA workbooks. Non-numeric values are ignored, so
    a missing hour never fabricates a count.
    """

    edges = list(upper_edges)
    counts = [0] * (len(edges) + 1)
    for value in values:
        if not _is_number(value):
            continue
        placed = False
        for index, edge in enumerate(edges):
            if float(value) <= edge:
                counts[index] += 1
                placed = True
                break
        if not placed:
            counts[-1] += 1
    return tuple(counts if include_overflow else counts[:-1])


def build_scatter_band(
    program_counts: Iterable[Sequence[int]],
    quantity: str,
    unit: str,
    upper_edges: Sequence[float],
    source_locator: str,
    include_overflow: bool = True,
) -> Optional[DistributionBand]:
    """Return the per-bin acceptance band across the reference programs' counts.

    The acceptance band is the per-bin min/max envelope of the contributing
    programs, following the written authority clarification received on
    2026-08-10. The former symmetric interpretation is diagnostic only.

    No zero floor is applied. The SIA floors the lower bound only in the Test 1
    tables (``MAX(0, ...)``), not in the Test 2 family from which this criterion
    comes; and for hour counts the floor changes nothing, since a count is never
    negative.

    Every contributing program must share the same bin length; a program with a
    different length is rejected (mismatched binning is never silently merged).
    Returns ``None`` when no reference program contributed, so no band is
    invented from nothing.
    """

    matrix = [tuple(counts) for counts in program_counts]
    expected_len = len(upper_edges) + (1 if include_overflow else 0)
    matrix = [row for row in matrix if len(row) == expected_len]
    if not matrix:
        return None

    symmetric_lower: List[float] = []
    symmetric_upper: List[float] = []
    for index in range(expected_len):
        column = [float(row[index]) for row in matrix]
        mean = sum(column) / float(len(column))
        deviation = max(abs(value - mean) for value in column)
        symmetric_lower.append(mean - deviation)
        symmetric_upper.append(mean + deviation)

    envelope_lower = tuple(
        float(min(row[i] for row in matrix)) for i in range(expected_len)
    )
    envelope_upper = tuple(
        float(max(row[i] for row in matrix)) for i in range(expected_len)
    )
    return DistributionBand(
        quantity=quantity,
        unit=unit,
        upper_edges=tuple(float(edge) for edge in upper_edges),
        lower_counts=envelope_lower,
        upper_counts=envelope_upper,
        program_count=len(matrix),
        source_locator=source_locator,
        envelope_lower_counts=envelope_lower,
        envelope_upper_counts=envelope_upper,
        symmetric_lower_counts=tuple(symmetric_lower),
        symmetric_upper_counts=tuple(symmetric_upper),
        include_overflow=include_overflow,
    )


def compare_distribution(
    candidate_counts: Optional[Sequence[int]],
    band: Optional[DistributionBand],
) -> DistributionOutcome:
    """Compare a candidate distribution to the reference scatter band, fail-closed.

    PASS only if every candidate bin lies within ``[lower, upper]``; FAIL if any
    bin is outside; NOT_CHECKABLE when the candidate distribution or the band is
    absent, or when their bin lengths differ (never an implicit re-bin).
    """

    if band is None:
        return DistributionOutcome(
            quantity="", unit="", status=DistributionStatus.NOT_CHECKABLE,
            message="No reference scatter band was available",
            out_of_band_bins=(), program_count=0, source_locator="",
        )
    if candidate_counts is None:
        return DistributionOutcome(
            quantity=band.quantity, unit=band.unit,
            status=DistributionStatus.NOT_CHECKABLE,
            message="Candidate distribution is missing",
            out_of_band_bins=(), program_count=band.program_count,
            source_locator=band.source_locator,
        )
    if len(candidate_counts) != len(band.lower_counts):
        return DistributionOutcome(
            quantity=band.quantity, unit=band.unit,
            status=DistributionStatus.NOT_CHECKABLE,
            message="Candidate and reference bin counts differ; no implicit re-bin",
            out_of_band_bins=(), program_count=band.program_count,
            source_locator=band.source_locator,
        )
    quality_suffix = ""
    if band.outside_class_counts:
        outside = [
            "{}={}".format(name, count)
            for name, count in band.outside_class_counts
            if count
        ]
        if outside:
            quality_suffix += (
                "; reference hours outside the declared class boundaries "
                "are audited separately: " + ", ".join(outside)
            )
    if band.incomplete_reference_programs:
        quality_suffix += (
            "; WARNING: incomplete official reference series retained unchanged: "
            + ", ".join(band.incomplete_reference_programs)
        )

    out_of_band = tuple(
        index
        for index, count in enumerate(candidate_counts)
        if not (band.lower_counts[index] <= count <= band.upper_counts[index])
    )
    if out_of_band:
        return DistributionOutcome(
            quantity=band.quantity,
            unit=band.unit,
            status=DistributionStatus.FAIL,
            message=(
                "Candidate distribution leaves the per-bin reference min/max envelope"
                + quality_suffix
            ),
            out_of_band_bins=out_of_band,
            program_count=band.program_count,
            source_locator=band.source_locator,
        )

    return DistributionOutcome(
        quantity=band.quantity,
        unit=band.unit,
        status=DistributionStatus.PASS,
        message=(
            "Candidate distribution lies within the per-bin reference min/max envelope"
            + quality_suffix
        ),
        out_of_band_bins=(),
        program_count=band.program_count,
        source_locator=band.source_locator,
    )
