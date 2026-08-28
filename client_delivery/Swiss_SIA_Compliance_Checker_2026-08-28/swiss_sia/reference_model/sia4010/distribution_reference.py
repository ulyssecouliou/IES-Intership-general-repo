"""Build SIA 4010 distribution reference envelopes from official Daten_* sheets.

The frequency-distribution second criterion needs the per-bin scatter band of
the reference programs. That band is not tabulated: each reference program ships
an hourly series (one ``Daten_<program>`` worksheet) per case and quantity, and
the acceptance band is the per-bin minimum/maximum of those series binned with
the official frequency legend. This follows the written clarification received
from Prof. Gerhard Zweifel on 2026-08-10.

This module locates the hourly column for each (case, quantity) in every
reference sheet, bins it, and builds a :class:`DistributionBand`. A reference
program contributes only when it actually provided the series (the column holds
numeric hours); a not-provided case is an empty column and is simply excluded,
never counted as zero. The candidate sheet (``Daten_Testprogramm``) is never
used as a reference. Nothing is invented: bins, values and the contributing set
all come from the workbook. The authority clarified on 2026-08-10 that displayed
class totals below 8,760 are caused by values outside the declared class
boundaries, not by missing reference hours. The source-hour total and excluded
overflow count are therefore carried separately in every band.
"""

import itertools
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

from openpyxl import load_workbook

from ..exceptions import ConfigurationError
from .frequency_distribution import (
    DistributionBand,
    DistributionOutcome,
    DistributionStatus,
    build_scatter_band,
    compare_distribution,
    histogram_counts,
    parse_frequency_classes,
)

# A case marker cell such as "2A".."2D" or "2 E1".."2 E5" (short, end-anchored,
# so a long quantity header is never mistaken for a case marker).
_CASE_MARKER = re.compile(r"^\d\s?[A-Z]\d*$")

# A scatter band needs more than one reference program: over a single program
# the maximum deviation is zero, so the band collapses to that program's exact
# counts and would reject almost any candidate.
MIN_REFERENCE_PROGRAMS = 2
EXPECTED_ANNUAL_HOURS = 8760


@dataclass(frozen=True)
class DistributionQuantity:
    """Maps a Daten_* column header to its Haeufigkeitsklassen legend bins."""

    header_label: str  # substring identifying the hourly column in Daten_* sheets
    legend_key: str  # exact key in the parsed Haeufigkeitsklassen legend


def _is_number(value) -> bool:
    """Return whether a cell value is a real number (not a bool)."""

    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _header_row_index(rows: Sequence[Sequence], labels: Sequence[str]) -> Optional[int]:
    """Return the first row index whose cells contain any target header label."""

    for index, row in enumerate(rows):
        if any(
            isinstance(cell, str) and any(label in cell for label in labels)
            for cell in row
        ):
            return index
    return None


def _case_marker_columns(header: Sequence) -> List[Tuple[int, str]]:
    """Return (column, marker) for every case marker on the header row, in order."""

    markers: List[Tuple[int, str]] = []
    for col, value in enumerate(header):
        if isinstance(value, str) and _CASE_MARKER.match(value.strip()):
            markers.append((col, value.strip()))
    return markers


def _quantity_column(
    header: Sequence, start: int, stop: int, header_label: str
) -> Optional[int]:
    """Return the column in [start, stop) whose header contains ``header_label``."""

    for col in range(start, min(stop, len(header))):
        value = header[col]
        if isinstance(value, str) and header_label in value:
            return col
    return None


def _collect_contiguous_series(data_rows, targets) -> Dict[int, List[float]]:
    """Collect each target column's hourly series, stopping at its first gap.

    The official data sheets place summary values (annual sums, minima, means)
    below the hourly block, separated by a blank row. An hourly series is
    contiguous, so a column is closed at its first blank cell once it has begun:
    that keeps aggregates out of the histogram, which would otherwise shift the
    bin counts and therefore the reference band.
    """

    series: Dict[int, List[float]] = {col: [] for col in targets}
    closed: Dict[int, bool] = {col: False for col in targets}
    for row in data_rows:
        for col in targets:
            if closed[col]:
                continue
            value = row[col] if col < len(row) else None
            if _is_number(value):
                series[col].append(value)
            elif series[col]:
                closed[col] = True  # the hourly block for this column ended
        if all(closed.values()):
            break
    return series


def build_distribution_bands(
    workbook_path: Union[str, Path],
    case_ids: Sequence[str],
    quantities: Sequence[DistributionQuantity],
    candidate_sheet: str = "Daten_Testprogramm",
    data_prefix: str = "Daten_",
) -> Dict[Tuple[str, str], DistributionBand]:
    """Return ``{(case_id, header_label): DistributionBand}`` from the reference sheets.

    For each reference ``Daten_*`` sheet (excluding the candidate), the hourly
    column of every requested (case, quantity) is located and binned; the bands
    are the per-bin minimum/maximum across the contributing programs (see
    :func:`build_scatter_band`). A (case, quantity) with no
    contributing program is omitted, so an empty band is never invented.
    """

    path = Path(workbook_path)
    legend = parse_frequency_classes(path)
    for quantity in quantities:
        if quantity.legend_key not in legend:
            raise ConfigurationError(
                "No Haeufigkeitsklassen legend entry for '{}'".format(quantity.legend_key)
            )
    labels = [quantity.header_label for quantity in quantities]

    workbook = load_workbook(path, data_only=True, read_only=True)
    try:
        reference_names = [
            name
            for name in workbook.sheetnames
            if name.startswith(data_prefix) and name != candidate_sheet
        ]
        # (case, header_label) -> list of (program_name, per-bin counts)
        contributions: Dict[
            Tuple[str, str], List[Tuple[str, Tuple[int, ...], int, int]]
        ] = {}
        for name in reference_names:
            row_iter = workbook[name].iter_rows(values_only=True)
            # Consume rows until the header row; data rows then follow in row_iter.
            header = None
            for scanned, row in enumerate(row_iter):
                if any(
                    isinstance(cell, str) and any(label in cell for label in labels)
                    for cell in row
                ):
                    header = row
                    break
                if scanned >= 8:  # header sits near the top; give up early otherwise
                    break
            if header is None:
                continue
            markers = _case_marker_columns(header)
            # Map only the requested (case, quantity) hourly columns for this sheet.
            targets: Dict[int, Tuple[str, str, str]] = {}
            for marker_pos, (marker_col, marker) in enumerate(markers):
                if marker not in case_ids:
                    continue
                stop = (
                    markers[marker_pos + 1][0]
                    if marker_pos + 1 < len(markers)
                    else len(header)
                )
                for quantity in quantities:
                    col = _quantity_column(
                        header, marker_col, stop, quantity.header_label
                    )
                    if col is not None:
                        targets[col] = (
                            marker,
                            quantity.header_label,
                            quantity.legend_key,
                        )
            if not targets:
                continue
            # Stream the remaining rows, keeping only the target columns' hourly
            # values and stopping each column before any trailing aggregates.
            series = _collect_contiguous_series(row_iter, targets)
            for col, (marker, header_label, legend_key) in targets.items():
                numeric = series[col]
                if not numeric:
                    continue  # program did not provide this case (empty column)
                full_counts = histogram_counts(
                    numeric,
                    legend[legend_key].upper_edges,
                    include_overflow=True,
                )
                counts = full_counts[:-1]
                contributions.setdefault((marker, header_label), []).append(
                    (name, counts, len(numeric), full_counts[-1])
                )
    finally:
        workbook.close()

    bands: Dict[Tuple[str, str], DistributionBand] = {}
    for (case_id, header_label), program_counts in contributions.items():
        quantity = next(q for q in quantities if q.header_label == header_label)
        legend_entry = legend[quantity.legend_key]
        band = build_scatter_band(
            [counts for _name, counts, _hours, _outside in program_counts],
            quantity=header_label,
            unit=legend_entry.unit,
            upper_edges=legend_entry.upper_edges,
            source_locator="{}!Daten_* [{}] refs={}".format(
                path.name,
                case_id,
                ",".join(
                    sorted(name for name, _counts, _hours, _outside in program_counts)
                ),
            ),
            include_overflow=False,
        )
        if band is not None:
            hour_totals = tuple(
                sorted((name, hours) for name, _counts, hours, _outside in program_counts)
            )
            outside_counts = tuple(
                sorted(
                    (name, outside) for name, _counts, _hours, outside in program_counts
                )
            )
            bands[(case_id, header_label)] = replace(
                band,
                reference_hour_totals=hour_totals,
                outside_class_counts=outside_counts,
                incomplete_reference_programs=tuple(
                    name for name, hours in hour_totals if hours != EXPECTED_ANNUAL_HOURS
                ),
            )
    return bands


def build_split_header_distribution_bands(
    workbook_path: Union[str, Path],
    case_ids: Sequence[str],
    quantities: Sequence[DistributionQuantity],
    scored_section: str,
    diagnostic_section: str,
    candidate_sheet: str,
    data_prefix: str,
) -> Dict[Tuple[str, str], DistributionBand]:
    """Return distribution bands for a workbook whose header spans two rows.

    Test 5 lays its data sheets out differently from Tests 2 and 3: the case
    markers (``Test 5A`` ...) and the section labels (``Testgroessen`` /
    ``Diagnosegroessen``) sit on the first row, while the quantity labels sit a
    few rows below. Only the columns between a case's scored-section label and
    its diagnostic-section label carry the acceptance criterion, so the
    diagnostic columns must never reach the band.

    A quantity whose label is not found inside a case's scored span is simply
    absent from the result: the criterion for that (case, quantity) then stays
    NOT_CHECKABLE rather than being binned against a guessed column.

    Two safeguards matter here. Some reference sheets omit the diagnostic-section
    marker, so their span would run on into the diagnostic columns; the scored
    label set per case is therefore agreed from the sheets that *do* declare the
    boundary, and sheets without it are restricted to that set. And a band is
    only emitted when at least two reference programs contributed, because a
    min/max envelope over a single program is not a scatter band of the
    reference programs and would be far too tight.
    """

    path = Path(workbook_path)
    legend = parse_frequency_classes(path)
    for quantity in quantities:
        if quantity.legend_key not in legend:
            raise ConfigurationError(
                "No Haeufigkeitsklassen legend entry for '{}'".format(quantity.legend_key)
            )

    labels = [quantity.header_label for quantity in quantities]

    def read_head(sheet_name):
        """Return the sheet's header rows and a live iterator over its data."""

        row_iter = workbook[sheet_name].iter_rows(values_only=True)
        head: List[Sequence] = []
        for index, row in enumerate(row_iter):
            head.append(row)
            if index >= 5:  # the two header rows and the unit row live here
                break
        return head, row_iter

    def case_spans(head):
        """Return the case-row index and {case: (start, end, has_boundary)}."""

        case_index = next(
            (
                index
                for index, row in enumerate(head)
                if any(isinstance(cell, str) and cell.strip() in case_ids for cell in row)
            ),
            None,
        )
        if case_index is None:
            return None, {}
        case_row = head[case_index]
        markers = [
            (col, str(value).strip())
            for col, value in enumerate(case_row)
            if isinstance(value, str) and str(value).strip() in case_ids
        ]
        spans = {}
        for position, (marker_col, marker) in enumerate(markers):
            block_end = (
                markers[position + 1][0] if position + 1 < len(markers) else len(case_row)
            )
            scored_start = next(
                (
                    col
                    for col in range(marker_col, block_end)
                    if isinstance(case_row[col], str)
                    and case_row[col].strip() == scored_section
                ),
                None,
            )
            if scored_start is None:
                continue
            boundary = next(
                (
                    col
                    for col in range(scored_start + 1, block_end)
                    if isinstance(case_row[col], str)
                    and case_row[col].strip() == diagnostic_section
                ),
                None,
            )
            spans[marker] = (
                scored_start,
                boundary if boundary is not None else block_end,
                boundary is not None,
            )
        return case_index, spans

    workbook = load_workbook(path, data_only=True, read_only=True)
    try:
        reference_names = [
            name
            for name in workbook.sheetnames
            if name.startswith(data_prefix) and name != candidate_sheet
        ]

        # Pass 1: agree the scored label set per case, using only the sheets that
        # declare an explicit diagnostic boundary.
        agreed: Dict[str, set] = {}
        for name in reference_names:
            head, _iter = read_head(name)
            case_index, spans = case_spans(head)
            if case_index is None:
                continue
            quantity_row = _header_row_index(head[case_index + 1 :], labels)
            if quantity_row is None:
                continue
            cells = head[case_index + 1 + quantity_row]
            for case_id, (start, end, has_boundary) in spans.items():
                if not has_boundary:
                    continue
                for col in range(start, min(end, len(cells))):
                    cell = cells[col]
                    if isinstance(cell, str) and cell.strip() in labels:
                        agreed.setdefault(case_id, set()).add(cell.strip())

        # Pass 2: extract, restricted to the agreed label set for that case.
        contributions: Dict[
            Tuple[str, str], List[Tuple[str, Tuple[int, ...], int, int]]
        ] = {}
        for name in reference_names:
            head, row_iter = read_head(name)
            case_index, spans = case_spans(head)
            if case_index is None:
                continue
            quantity_row = _header_row_index(head[case_index + 1 :], labels)
            if quantity_row is None:
                continue
            quantity_cells = head[case_index + 1 + quantity_row]
            targets: Dict[int, Tuple[str, str, str]] = {}
            for case_id, (start, end, _has_boundary) in spans.items():
                allowed = agreed.get(case_id)
                for quantity in quantities:
                    if allowed is not None and quantity.header_label not in allowed:
                        continue
                    for col in range(start, min(end, len(quantity_cells))):
                        cell = quantity_cells[col]
                        if (
                            isinstance(cell, str)
                            and cell.strip() == quantity.header_label
                        ):
                            targets[col] = (
                                case_id,
                                quantity.header_label,
                                quantity.legend_key,
                            )
                            break
            if not targets:
                continue
            # Rows already pulled into the header window may hold the first data
            # hours, so scan them too before continuing with the stream. Header
            # and unit cells are non-numeric and are ignored by _is_number.
            data_rows = itertools.chain(
                head[case_index + 1 + quantity_row + 1 :], row_iter
            )
            series = _collect_contiguous_series(data_rows, targets)
            for col, (case_id, header_label, legend_key) in targets.items():
                if not series[col]:
                    continue  # program did not provide this case/quantity
                full_counts = histogram_counts(
                    series[col],
                    legend[legend_key].upper_edges,
                    include_overflow=True,
                )
                contributions.setdefault((case_id, header_label), []).append(
                    (name, full_counts[:-1], len(series[col]), full_counts[-1])
                )
    finally:
        workbook.close()

    bands: Dict[Tuple[str, str], DistributionBand] = {}
    for (case_id, header_label), program_counts in contributions.items():
        if len(program_counts) < MIN_REFERENCE_PROGRAMS:
            continue  # not a scatter band of the reference programs
        quantity = next(q for q in quantities if q.header_label == header_label)
        legend_entry = legend[quantity.legend_key]
        band = build_scatter_band(
            [counts for _name, counts, _hours, _outside in program_counts],
            quantity=header_label,
            unit=legend_entry.unit,
            upper_edges=legend_entry.upper_edges,
            source_locator="{}!{}* [{}] refs={}".format(
                path.name,
                data_prefix,
                case_id,
                ",".join(
                    sorted(name for name, _counts, _hours, _outside in program_counts)
                ),
            ),
            include_overflow=False,
        )
        if band is not None:
            hour_totals = tuple(
                sorted((name, hours) for name, _counts, hours, _outside in program_counts)
            )
            outside_counts = tuple(
                sorted(
                    (name, outside) for name, _counts, _hours, outside in program_counts
                )
            )
            bands[(case_id, header_label)] = replace(
                band,
                reference_hour_totals=hour_totals,
                outside_class_counts=outside_counts,
                incomplete_reference_programs=tuple(
                    name for name, hours in hour_totals if hours != EXPECTED_ANNUAL_HOURS
                ),
            )
    return bands


def evaluate_distribution_criteria(
    workbook_path: Union[str, Path],
    case_ids: Sequence[str],
    quantities: Sequence[DistributionQuantity],
    candidate_distributions: Optional[Dict[Tuple[str, str], Sequence[int]]] = None,
    candidate_sheet: str = "Daten_Testprogramm",
    data_prefix: str = "Daten_",
    layout: str = "inline_header",
    scored_section: str = "",
    diagnostic_section: str = "",
) -> Tuple[DistributionOutcome, ...]:
    """Return one distribution outcome per (case, quantity), fail-closed.

    The reference bands come from the workbook; the candidate per-bin counts come
    from ``candidate_distributions`` (keyed by ``(case_id, header_label)``), which
    is populated from the VE hourly APS output during Phase B. A (case, quantity)
    with no candidate resolves to ``NOT_CHECKABLE`` - never a pass.
    """

    try:
        if layout == "split_header":
            bands = build_split_header_distribution_bands(
                workbook_path,
                case_ids,
                quantities,
                scored_section=scored_section,
                diagnostic_section=diagnostic_section,
                candidate_sheet=candidate_sheet,
                data_prefix=data_prefix,
            )
        else:
            bands = build_distribution_bands(
                workbook_path,
                case_ids,
                quantities,
                candidate_sheet=candidate_sheet,
                data_prefix=data_prefix,
            )
    except ConfigurationError:
        bands = {}
    if not bands:
        # The criterion applies but its reference data is unavailable: report one
        # NOT_CHECKABLE per requested (case, quantity) so a test carrying a
        # distribution criterion can never pass on the annual band alone.
        return tuple(
            DistributionOutcome(
                quantity=quantity.header_label,
                unit="",
                status=DistributionStatus.NOT_CHECKABLE,
                message="Reference distribution band unavailable",
                out_of_band_bins=(),
                program_count=0,
                source_locator="",
                case_id=case_id,
            )
            for case_id in case_ids
            for quantity in quantities
        )
    outcomes: List[DistributionOutcome] = []
    # Emit one auditable outcome for every required case/quantity pair.  A
    # partially parsed workbook must not silently drop a mandatory criterion.
    required_keys = [
        (case_id, quantity.header_label)
        for case_id in case_ids
        for quantity in quantities
    ]
    for key in required_keys:
        band = bands.get(key)
        if band is None:
            outcomes.append(
                DistributionOutcome(
                    quantity=key[1],
                    unit="",
                    status=DistributionStatus.NOT_CHECKABLE,
                    message="Reference distribution band unavailable",
                    out_of_band_bins=(),
                    program_count=0,
                    source_locator="",
                    case_id=key[0],
                )
            )
            continue
        candidate = None
        if candidate_distributions is not None:
            candidate = candidate_distributions.get(key)
        outcomes.append(replace(compare_distribution(candidate, band), case_id=key[0]))
    return tuple(outcomes)


# Registry of tests that carry a frequency-distribution criterion, with the
# quantities it applies to and that workbook's structural details. Only entries
# whose layout is confirmed against the official workbook are registered; an
# unregistered test simply has no distribution outcome (never a silent pass).
#
# Not registered on purpose:
# - Test 2 "Total transmittierte Solarstrahlung": the Haeufigkeitsklassen legend
#   has no dedicated bin column for it, so its bin set is not defined by the
#   workbook and is not guessed here.
# - Test 5 "Leistung Befeuchter" (case 5D): the legend defines bins for
#   "Leistung Hilfsenergie Befeuchter" but not for the humidifier power itself,
#   so that one scored quantity stays NOT_CHECKABLE instead of borrowing bins.

# Workbook evidence discovered after the authority reply of 2026-08-10. These
# entries deliberately do NOT enter ``DISTRIBUTION_CRITERIA`` yet: Prof. Zweifel
# confirmed that the sheets exist. Yiqiao subsequently confirmed in writing
# that the results to be delivered for Tests 4, 6 and 7 are those listed in the
# Excel sheets. This establishes the output contract, but not that every plotted
# diagnostic is a pass gate. Recording the exact workbook labels removes the
# former false claim without inventing the remaining acceptance scope.
DISTRIBUTION_WORKBOOK_EVIDENCE: Dict[str, Dict[str, object]] = {
    "4": {
        "legend_sheet": "Haeufigkeitskassen",
        "summary_heading": "Stündliche Häufigkeitsverteilung",
        "status": "REQUIRED_OUTPUT_SCOPE_CONFIRMED_ACCEPTANCE_GATE_PENDING",
        "legend_quantities": (
            "Zu-/Abluft-Volumenstrom",
            "Zulufttemperatur",
            "Mittlere Raumlufttemperatur",
            "Operative Temperatur",
            "CO2 Konzentration",
            "Leistung Zuluftventilator",
            "Leistung Abluftventilator",
            "Leistung Zu- und Abluftventilator",
            "Lufterwärmerleistung",
            "Luftkühlerleistung total",
            "Luftkühlerleistung latent",
        ),
    },
    "6": {
        "legend_sheet": "Haeufigkeitskassen",
        "summary_heading": "Stündliche Häufigkeitsverteilung",
        "status": "REQUIRED_OUTPUT_SCOPE_CONFIRMED_ACCEPTANCE_GATE_PENDING",
        "legend_quantities": (
            "Zu-/Abluft-Volumenstrom",
            "Zulufttemperatur",
            "Ablufttemperatur",
            "Leistung Zu- und Abluftventilator",
            "Leistung Lufterwärmer",
            "Leistung Luftkühler total",
            "Leistung Luftkühler latent",
            "Wärmeverluste Verteilung",
            "Leistung Hilfsenergie WRG",
            "Wärmezufuhr WRG",
            "Wärmeabfuhr WRG",
        ),
    },
}

DISTRIBUTION_CRITERIA: Dict[str, Dict[str, object]] = {
    "2": {
        "case_ids": ("2A", "2B", "2C", "2D"),
        "quantities": (
            DistributionQuantity(
                header_label="Solarer Wärmeeintrag gesamt",
                legend_key="Solarer Wärmeeintrag gesamt",
            ),
        ),
        "data_prefix": "Daten_",
        "candidate_sheet": "Daten_Testprogramm",
    },
    # Test 3: Spezifikation_Test3 names total room lighting power as the single
    # Testgroesse and requires both the annual-sum band and the hourly
    # frequency distribution within the reference programs' scatter band.
    # Illuminance ("Beleuchtungsstaerke", lux) is a Diagnosegroesse and is
    # therefore intentionally excluded even though the legend defines its bins.
    "3": {
        "case_ids": (
            "3A",
            "3B",
            "3C",
            "3D",
            "3E",
            "3F",
            "3G",
            "3H",
            "3I",
            "3J",
            "3K",
            "3L",
        ),
        "quantities": (
            DistributionQuantity(
                header_label="Beleuchtungsleistung",
                legend_key="Beleuchtungsleistung",
            ),
        ),
        "data_prefix": "Daten_",
        "candidate_sheet": "Daten_Testprogramm",
    },
    # Test 5: Spezifikation_Test5 requires "Die Haeufigkeitsverteilungen muessen
    # im Streubereich der Referenzprogramme liegen". Its data sheets use the
    # split-header layout, and each case scores a different quantity set, so the
    # union is registered and per-case span filtering selects the right columns.
    # Each legend_key below is the legend column that defines that quantity's
    # bins; where the wording differs it is the same physical quantity with the
    # words reordered, and the two WRG transfer quantities map one-to-one onto
    # the legend's two WRG columns. The 5C spellings repeat a word in the source
    # workbook, so both spellings are registered verbatim.
    "5": {
        "case_ids": ("Test 5A", "Test 5B", "Test 5C", "Test 5D"),
        "quantities": (
            DistributionQuantity(
                header_label="Zu-/Abluft-Volumenstrom",
                legend_key="Zu-/Abluft-Volumenstrom",
            ),
            DistributionQuantity(
                header_label="Leistung Zu- und Abluftventilator",
                legend_key="Leistung Zu- und Abluftventilator",
            ),
            DistributionQuantity(
                header_label="Leistung Lufterwärmer",
                legend_key="Leistung Lufterwärmer",
            ),
            DistributionQuantity(
                header_label="Leistung Luftkühler total",
                legend_key="Leistung\ntotal Luftkühler",
            ),
            DistributionQuantity(
                header_label="Leistung Luftkühler latent",
                legend_key="Leistung latent Luftkühler",
            ),
            DistributionQuantity(
                header_label="WRG Übertragungsleistung gesamt",
                legend_key="Leistung WRG",
            ),
            DistributionQuantity(
                header_label="WRG Übertragungsleistung latent",
                legend_key="Leistung WRG latent",
            ),
            DistributionQuantity(
                header_label="WRG Übertragungsleistungleistung gesamt",
                legend_key="Leistung WRG",
            ),
            DistributionQuantity(
                header_label="WRG Übertragungsleistungleistung latent",
                legend_key="Leistung WRG latent",
            ),
            DistributionQuantity(
                header_label="Leistung Hilfsenergie WRG",
                legend_key="Leistung Hilfsenergie WRG",
            ),
        ),
        "data_prefix": "Daten ",
        "candidate_sheet": "Daten Testprogramm",
        "layout": "split_header",
        "scored_section": "Testgrössen",
        "diagnostic_section": "Diagnosegrössen",
    },
}
