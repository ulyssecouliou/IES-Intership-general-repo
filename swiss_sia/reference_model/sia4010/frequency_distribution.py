"""Frequency-distribution second criterion for SIA 4010 (Tests 2, 3, 5).

Besides the annual-sum band, these tests require the candidate's hourly
frequency distribution of a quantity (e.g. solar heat gain) to lie "im
Streubereich der Referenzprogramme" - within the scatter band of the reference
programs, bin by bin (Spezifikation_Test2, Testkriterien).

This module is the pure-Python core:

- ``parse_frequency_classes`` reads the official ``Haeufigkeitsklassen`` legend
  (per-quantity class upper edges) verbatim - it invents no bins.
- ``histogram_counts`` bins an hourly series with Excel ``FREQUENCY`` semantics
  (class ``i`` counts ``edge[i-1] < v <= edge[i]``; a final overflow class
  counts ``v > edge[-1]``), so candidate and reference are binned identically.
- ``build_scatter_band`` derives the per-bin band as ``mean +/- max|count -
  mean|`` across the reference programs' per-bin counts, computed only from the
  reference programs' own data (nothing invented).
- ``compare_distribution`` reports PASS when every candidate bin lies within the
  band, PASS_WITH_RESERVATION when it does but leaves the narrower min/max
  envelope, FAIL if any bin is outside the band, and NOT_CHECKABLE when the
  candidate distribution is absent (fail-closed; a missing candidate is never a
  pass).

WHY THE SYMMETRIC BAND AND NOT THE MIN/MAX ENVELOPE
---------------------------------------------------
The workbook tabulates no band for this criterion (verified: zero
``Mittelwert`` / ``obere Grenze`` / ``untere Grenze`` label anywhere in the
frequency zone of Resultaterfassung_Test2, rows 26-308 x 239 columns, and its 50
charts merely superimpose the programs' histograms - no envelope series). The
band therefore has to be derived, which makes the choice of formula a normative
reading rather than a lookup.

Wherever the SIA does tabulate a scatter band, it computes it as the symmetric
band. Read directly from the official workbooks:

    Resultaterfassung_Test1, "Zusammenfassung Testfaelle"
        H16 = G16+MAX(ABS(C16-G16),ABS(D16-G16),ABS(E16-G16),ABS(F16-G16))
        I16 = MAX(0,G16-MAX(ABS(C16-G16),...))
    Resultaterfassung_Test2, "Zusammenfassung"
        N14 = M14+MAX(ABS(E14-M14),ABS(H14-M14),ABS(K14-M14),ABS(L14-M14))
        O14 = M14-MAX(...)

Spezifikation_Test1 applies the same word to the criterion those tables encode:
"Resultate fuer den Test 1E muessen im Streubereich der enthaltenen
Referenzprogramme liegen". So when the SIA had to turn this word into numbers,
it wrote the symmetric band.

Since ``max|count - mean| >= max - mean`` and ``>= mean - min``, the min/max
envelope is always contained in the symmetric band: reading the criterion as the
envelope is strictly stricter and risks failing a candidate that the official
criterion accepts. That is why the envelope is reported, never enforced.

Full arbitration, including the counter-argument and what would overturn it:
``traceability/streubereich-distributions.spec.md`` in the SIA_Compliance_Scripts
repository (confidence ~92%, not certain). The decision is reversible: switching
the enforced criterion means swapping which pair of tuples ``compare_distribution``
tests against.

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

    ``lower_counts`` / ``upper_counts`` are the ACCEPTANCE band: per bin, the
    symmetric band ``mean +/- max|count - mean|`` across the contributing
    reference programs. This is the construction the SIA itself applies wherever
    it tabulates a scatter band; see the module docstring for the evidence.

    ``envelope_lower_counts`` / ``envelope_upper_counts`` are the per-bin
    min/max span of the same programs. This is the competing reading of the
    criterion, kept only to flag the cases where the two readings disagree
    (``PASS_WITH_RESERVATION``). It is never the acceptance criterion. Empty
    tuples mean "envelope unknown", and no reservation is ever raised.

    ``bin_count`` is ``len(upper_edges) + 1`` (the final entry is the overflow
    class). ``program_count`` records how many reference programs contributed,
    for the audit trail.
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


class DistributionStatus:
    """String outcomes for a distribution comparison (mirrors ComparisonStatus)."""

    PASS = "PASS"
    # Inside the acceptance band, but outside the narrower min/max envelope.
    # A pass under the retained reading of the criterion, carrying a flag for
    # the sub-commission (SIA 4010 clause 4.6.2). Treat as passing; report it.
    PASS_WITH_RESERVATION = "PASS_WITH_RESERVATION"
    FAIL = "FAIL"
    NOT_CHECKABLE = "NOT_CHECKABLE"

    @staticmethod
    def is_passing(status: str) -> bool:
        """Whether a status counts as meeting the criterion.

        Use this instead of ``== DistributionStatus.PASS``: a reserved pass IS a
        pass under the retained reading, and comparing against PASS alone would
        silently turn it into a failure.
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
    values: Iterable[Any], upper_edges: Sequence[float]
) -> Tuple[int, ...]:
    """Bin numeric ``values`` into classes with Excel ``FREQUENCY`` semantics.

    Returns ``len(upper_edges) + 1`` counts: class ``i`` counts
    ``edge[i-1] < v <= edge[i]`` (class 0 is ``v <= edge[0]``), and the final
    entry counts the overflow ``v > edge[-1]``. Non-numeric values are ignored,
    so a missing hour never fabricates a count.
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
    return tuple(counts)


def build_scatter_band(
    program_counts: Iterable[Sequence[int]],
    quantity: str,
    unit: str,
    upper_edges: Sequence[float],
    source_locator: str,
) -> Optional[DistributionBand]:
    """Return the per-bin acceptance band across the reference programs' counts.

    The acceptance band is, per bin, ``mean +/- max|count - mean|`` over the
    contributing programs -- the construction the SIA applies wherever it
    tabulates a scatter band. The min/max envelope is computed alongside and
    stored separately; since it is always contained in the symmetric band, it
    only serves to flag disagreement between the two readings.

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
    expected_len = len(upper_edges) + 1
    matrix = [row for row in matrix if len(row) == expected_len]
    if not matrix:
        return None

    lower: List[float] = []
    upper: List[float] = []
    for index in range(expected_len):
        column = [float(row[index]) for row in matrix]
        mean = sum(column) / float(len(column))
        deviation = max(abs(value - mean) for value in column)
        lower.append(mean - deviation)
        upper.append(mean + deviation)

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
        lower_counts=tuple(lower),
        upper_counts=tuple(upper),
        program_count=len(matrix),
        source_locator=source_locator,
        envelope_lower_counts=envelope_lower,
        envelope_upper_counts=envelope_upper,
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
            message="Candidate distribution leaves the reference scatter band",
            out_of_band_bins=out_of_band,
            program_count=band.program_count,
            source_locator=band.source_locator,
        )

    # Inside the acceptance band. Check the narrower min/max envelope only to
    # surface where the two readings of the criterion disagree; leaving the
    # envelope is never on its own a failure.
    outside_envelope: Tuple[int, ...] = ()
    if (len(band.envelope_lower_counts) == len(candidate_counts)
            and len(band.envelope_upper_counts) == len(candidate_counts)):
        outside_envelope = tuple(
            index
            for index, count in enumerate(candidate_counts)
            if not (band.envelope_lower_counts[index]
                    <= count
                    <= band.envelope_upper_counts[index])
        )
    if outside_envelope:
        return DistributionOutcome(
            quantity=band.quantity,
            unit=band.unit,
            status=DistributionStatus.PASS_WITH_RESERVATION,
            message=(
                "Candidate distribution lies within the reference scatter band "
                "but outside the min/max envelope of the reference programs in "
                "{} bin(s); flag for the sub-commission".format(
                    len(outside_envelope)
                )
            ),
            out_of_band_bins=outside_envelope,
            program_count=band.program_count,
            source_locator=band.source_locator,
        )
    return DistributionOutcome(
        quantity=band.quantity,
        unit=band.unit,
        status=DistributionStatus.PASS,
        message="Candidate distribution lies within the reference scatter band",
        out_of_band_bins=(),
        program_count=band.program_count,
        source_locator=band.source_locator,
    )
