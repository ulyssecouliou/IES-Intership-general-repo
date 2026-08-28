"""Format-specific loaders for official SIA 4010 evaluation workbooks.

These read reference acceptance data from the official ``Resultaterfassung``
workbooks and normalise it into :class:`ExpectedResult` records. They never
invent a criterion: a band is emitted only where the workbook itself provides
explicit lower/upper bounds (German ``untere Grenze`` / ``obere Grenze``).
Cases the specification declares to have no deviation criterion carry no such
bounds and are therefore skipped (diagnostic / comparison only), exactly as
``Spezifikation_Test1`` states for cases 600/640/900/940/600FF/900FF.
"""

import re
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from .expected_results import ExpectedResult


def deduplicate_expected_keys(
    results: Tuple[ExpectedResult, ...],
) -> Tuple[ExpectedResult, ...]:
    """Guarantee unique (test, case, metric) keys by suffixing repeats.

    Some official summaries reuse the same quantity label for physically
    distinct rows (Test 7: refrigeration vs heat pump both read ``Zugefuehrte
    elektrische Energie``). Suffixing the second and later occurrences keeps
    each metric one-to-one for the comparator; source_locator still records the
    exact originating cell.
    """

    seen: Dict[str, int] = {}
    unique: List[ExpectedResult] = []
    for result in results:
        key = result.key
        seen[key] = seen.get(key, 0) + 1
        if seen[key] > 1:
            result = replace(result, metric="{} ({})".format(result.metric, seen[key]))
        unique.append(result)
    return tuple(unique)


_UPPER = "obere grenze"
_LOWER = "untere grenze"
_MEAN = "mittelwert"
_ROW_LABEL_HEADERS = {"month", "monat", "fall", "case", "case id.", "case id"}
_CASE_ID_LABEL = "case id."
_UNIT_PATTERN = re.compile(
    r"^\s*(kwh|mwh|wh|kw|w|°c|c|k|%|m3|m³|m2|m²|l/s|ppm|lux|lx|h|-)\s*$",
    re.IGNORECASE,
)
# A base unit token followed by a parenthetical qualifier, e.g. "kWh (peak)"
# used by the Test 1 Table 31 annual peak-load block. The qualifier is kept
# verbatim so the observed extractor must match the exact official label.
_UNIT_WITH_QUALIFIER = re.compile(
    r"^\s*(kwh|mwh|wh|kw|w)\s*\([^)]*\)\s*$",
    re.IGNORECASE,
)


def _is_unit_token(value: Any) -> bool:
    """Return whether a cell holds a recognised unit token (with or without qualifier)."""

    if not isinstance(value, str):
        return False
    text = value.strip()
    return bool(_UNIT_PATTERN.match(text) or _UNIT_WITH_QUALIFIER.match(text))


def _norm(value: Any) -> str:
    """Return a trimmed lower-case string form of a cell value."""

    return str(value).strip().lower() if isinstance(value, str) else ""


def _is_number(value: Any) -> bool:
    """Return whether a cell value is a real numeric result."""

    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _read_sheet(worksheet: Any) -> Tuple[Dict[Tuple[int, int], Any], int, int]:
    """Return a (row, col) -> value grid plus the used row/column extents."""

    grid: Dict[Tuple[int, int], Any] = {}
    max_row = max_col = 0
    for row in worksheet.iter_rows():
        for cell in row:
            if cell.value is not None and str(cell.value).strip() != "":
                grid[(cell.row, cell.column)] = cell.value
                max_row = max(max_row, cell.row)
                max_col = max(max_col, cell.column)
    return grid, max_row, max_col


def _row_cells(
    grid: Dict[Tuple[int, int], Any], row: int, max_col: int
) -> List[Tuple[int, Any]]:
    """Return the populated (column, value) pairs of one row, left to right."""

    return [
        (col, grid[(row, col)]) for col in range(1, max_col + 1) if (row, col) in grid
    ]


def _find_band_headers(
    grid: Dict[Tuple[int, int], Any], max_row: int, max_col: int
) -> List[Dict[str, int]]:
    """Locate every header row/columns exposing an explicit lower/upper band."""

    headers: List[Dict[str, int]] = []
    for row in range(1, max_row + 1):
        cells = _row_cells(grid, row, max_col)
        upper_col = lower_col = mean_col = None
        for col, value in cells:
            norm = _norm(value)
            if norm == _UPPER:
                upper_col = col
            elif norm == _LOWER:
                lower_col = col
            elif norm == _MEAN:
                mean_col = col
        if upper_col is not None and lower_col is not None:
            label_col = None
            for col, value in cells:
                if col < upper_col and _norm(value) in _ROW_LABEL_HEADERS:
                    label_col = col  # nearest label header to the left of the band
            if label_col is not None:
                headers.append(
                    {
                        "row": row,
                        "label_col": label_col,
                        "upper_col": upper_col,
                        "lower_col": lower_col,
                        "mean_col": mean_col if mean_col is not None else -1,
                    }
                )
    return headers


def _block_case_and_unit(
    grid: Dict[Tuple[int, int], Any], header: Dict[str, int]
) -> Tuple[str, str]:
    """Resolve the case id and unit from the ``Case id.`` row above a band header.

    The unit may sit on the case-id row to the right of the case value (Table
    28/29 monthly blocks: ``kWh``) or directly below the case value (Table 31
    peak-load block: ``kWh (peak)``). Both placements are read verbatim from the
    workbook; no unit is invented and a parenthetical qualifier is preserved.
    """

    label_col, upper_col, header_row = (
        header["label_col"],
        header["upper_col"],
        header["row"],
    )
    span = range(label_col, upper_col + 2)
    for row in range(header_row - 1, max(header_row - 10, 0), -1):
        label_cols = [
            col for col in span if _norm(grid.get((row, col))) == _CASE_ID_LABEL
        ]
        if not label_cols:
            continue
        case_label_col = min(label_cols)
        # The case identifier is the first populated cell right of the label.
        value_col = None
        for col in range(case_label_col + 1, upper_col + 2):
            if (row, col) in grid:
                value_col = col
                break
        if value_col is None:
            return "", ""
        case_id = str(grid[(row, value_col)]).strip()
        unit = ""
        # Prefer a unit token on the same row, right of the case value.
        for col in range(value_col + 1, upper_col + 2):
            value = grid.get((row, col))
            if _is_unit_token(value):
                unit = str(value).strip()
                break
        # Otherwise take the unit directly below the case value (peak-load block).
        if not unit and _is_unit_token(grid.get((row + 1, value_col))):
            unit = str(grid[(row + 1, value_col)]).strip()
        return case_id, unit
    return "", ""


def _block_title(
    grid: Dict[Tuple[int, int], Any], header: Dict[str, int], max_col: int
) -> str:
    """Resolve the nearest table title above a band header, for metric naming.

    Primary search stays inside the block's own column span. Fallback: the
    workbook repeats a quantity across adjacent column blocks, and the leftmost
    copy can carry a plain heading while a repeat carries the ``Table N`` heading
    (Test 1 Table 31 peak-load block). The fallback then picks the ``Table N``
    heading in the nearest adjacent columns, not the first one globally, so a
    distant block's title cannot leak in.
    """

    label_col, upper_col, header_row = (
        header["label_col"],
        header["upper_col"],
        header["row"],
    )
    span = range(label_col, upper_col + 2)
    for row in range(header_row - 1, max(header_row - 12, 0), -1):
        for col in span:
            value = grid.get((row, col))
            if isinstance(value, str) and value.strip().lower().startswith("table"):
                return value.strip()
    candidates: List[Tuple[int, int, str]] = []
    for row in range(header_row - 1, max(header_row - 6, 0), -1):
        for col in range(1, max_col + 1):
            value = grid.get((row, col))
            if isinstance(value, str) and value.strip().lower().startswith("table"):
                candidates.append((row, col, value.strip()))
    if candidates:

        def _column_distance(item: Tuple[int, int, str]) -> int:
            """Return how far a candidate column sits from this block's own columns."""

            _row, col, _text = item
            if col < label_col:
                return label_col - col
            if col > upper_col:
                return col - upper_col
            return 0

        # Nearest columns first, then the topmost row (the block heading row).
        candidates.sort(key=lambda item: (_column_distance(item), -item[0]))
        return candidates[0][2]
    return "table"


def extract_reference_bands(
    worksheet: Any,
    test_id: str,
    source_locator_prefix: str,
    source_checksum: str = "",
) -> Tuple[ExpectedResult, ...]:
    """Extract every explicit reference band from one summary worksheet."""

    grid, max_row, max_col = _read_sheet(worksheet)
    results: List[ExpectedResult] = []
    for header in _find_band_headers(grid, max_row, max_col):
        case_id, unit = _block_case_and_unit(grid, header)
        title = _block_title(grid, header, max_col)
        label_col = header["label_col"]
        upper_col, lower_col, mean_col = (
            header["upper_col"],
            header["lower_col"],
            header["mean_col"],
        )
        for row in range(header["row"] + 1, max_row + 1):
            row_label = grid.get((row, label_col))
            upper = grid.get((row, upper_col))
            lower = grid.get((row, lower_col))
            if row_label is None or not (_is_number(upper) and _is_number(lower)):
                # Stop at the first row that no longer holds band data.
                if row_label is None:
                    break
                continue
            mean = grid.get((row, mean_col)) if mean_col > 0 else None
            expected_value = float(mean) if _is_number(mean) else float(upper)
            metric = "{} | {}".format(title, str(row_label).strip())
            results.append(
                ExpectedResult(
                    test_id=test_id,
                    case_id=case_id,
                    metric=metric,
                    expected_value=expected_value,
                    unit=unit,
                    absolute_tolerance=None,
                    relative_tolerance=None,
                    source_locator="{}!{}{}".format(
                        source_locator_prefix, get_column_letter(upper_col), row
                    ),
                    source_checksum=source_checksum,
                    lower_bound=float(lower),
                    upper_bound=float(upper),
                )
            )
    return tuple(results)


def _mean_band_blocks(
    grid: Dict[Tuple[int, int], Any], header_row: int, max_col: int
) -> List[Tuple[int, int, int]]:
    """Return (mean, upper, lower) column triples on a band header row.

    The official workbooks lay the band out as three consecutive columns
    ``Mittelwert`` / ``obere Grenze`` / ``untere Grenze``.
    """

    blocks: List[Tuple[int, int, int]] = []
    for col in range(1, max_col + 1):
        if _norm(grid.get((header_row, col))) == _MEAN:
            upper, lower = col + 1, col + 2
            if (
                _norm(grid.get((header_row, upper))) == _UPPER
                and _norm(grid.get((header_row, lower))) == _LOWER
            ):
                blocks.append((col, upper, lower))
    return blocks


def _nearest_left_header(
    grid: Dict[Tuple[int, int], Any], row: int, before_col: int, label: str
) -> Optional[int]:
    """Return the nearest column left of ``before_col`` whose header equals ``label``."""

    found = None
    for col in range(1, before_col):
        if _norm(grid.get((row, col))) == label:
            found = col
    return found


def parse_case_per_row_bands(
    worksheet: Any,
    test_id: str,
    source_locator_prefix: str,
    row_label_header: str,
    source_checksum: str = "",
) -> Tuple[ExpectedResult, ...]:
    """Extract bands where each data row is a case (Test 2 style layout).

    The row-label column (e.g. ``Fall``) holds the case id, each band block
    (``Mittelwert`` / ``obere Grenze`` / ``untere Grenze``) is one quantity whose
    title sits on the row-label header row and whose unit sits on the next row.
    """

    grid, max_row, max_col = _read_sheet(worksheet)
    label_cell = next(
        ((r, c) for (r, c), value in grid.items() if _norm(value) == row_label_header),
        None,
    )
    if label_cell is None:
        return ()
    label_row, label_col = label_cell
    header_rows = sorted({r for (r, _c), value in grid.items() if _norm(value) == _MEAN})
    results: List[ExpectedResult] = []
    for header_row in header_rows:
        for mean_col, upper_col, lower_col in _mean_band_blocks(
            grid, header_row, max_col
        ):
            title_col = _nearest_left_header(grid, header_row, mean_col, "testprogramm")
            title = (
                str(grid.get((label_row, title_col), "quantity")).strip()
                if title_col
                else "quantity"
            )
            unit = str(grid.get((label_row + 1, upper_col), "")).strip()
            started = False
            for row in range(label_row + 1, max_row + 1):
                case = grid.get((row, label_col))
                upper = grid.get((row, upper_col))
                lower = grid.get((row, lower_col))
                if case is None and upper is None and lower is None:
                    continue  # blank gap between case sub-groups
                if case is not None and _is_number(upper) and _is_number(lower):
                    started = True
                    mean = grid.get((row, mean_col))
                    results.append(
                        ExpectedResult(
                            test_id=test_id,
                            case_id=str(case).strip(),
                            metric=title,
                            expected_value=(
                                float(mean) if _is_number(mean) else float(upper)
                            ),
                            unit=unit,
                            absolute_tolerance=None,
                            relative_tolerance=None,
                            source_locator="{}!{}{}".format(
                                source_locator_prefix, get_column_letter(upper_col), row
                            ),
                            source_checksum=source_checksum,
                            lower_bound=float(lower),
                            upper_bound=float(upper),
                        )
                    )
                elif started:
                    break  # a populated non-band row ends the case block
    return tuple(results)


def _first_unit_in_row_range(
    grid: Dict[Tuple[int, int], Any], rows: range, cols: range
) -> str:
    """Return the first cell in a region whose value is a recognised unit token."""

    for row in rows:
        for col in cols:
            value = grid.get((row, col))
            if isinstance(value, str) and _UNIT_PATTERN.match(value):
                return value.strip()
    return ""


def parse_inline_header_bands(
    worksheet: Any,
    test_id: str,
    source_locator_prefix: str,
    row_label_headers: Tuple[str, ...],
    source_checksum: str = "",
) -> Tuple[ExpectedResult, ...]:
    """Extract bands where the band header row is also the case-column header row.

    Test 3 lays the summary out with the case-column header (``Testfaelle``) on
    the same row as ``Mittelwert`` / ``Obere Grenze`` / ``Untere Grenze``, cases
    beginning on the next row, and the quantity named by a section header above.
    """

    grid, max_row, max_col = _read_sheet(worksheet)
    label_cell = next(
        ((r, c) for (r, c), value in grid.items() if _norm(value) in row_label_headers),
        None,
    )
    if label_cell is None:
        return ()
    label_row, label_col = label_cell
    title = "annual values"
    for row in range(label_row - 1, max(label_row - 6, 0), -1):
        value = grid.get((row, label_col))
        if isinstance(value, str) and value.strip():
            title = value.strip()
            break
    results: List[ExpectedResult] = []
    for mean_col, upper_col, lower_col in _mean_band_blocks(grid, label_row, max_col):
        unit = _first_unit_in_row_range(
            grid, range(max(label_row - 3, 1), label_row + 1), range(1, max_col + 1)
        )
        started = False
        for row in range(label_row + 1, max_row + 1):
            case = grid.get((row, label_col))
            upper = grid.get((row, upper_col))
            lower = grid.get((row, lower_col))
            if case is None and upper is None and lower is None:
                continue  # blank gap between case sub-groups
            if case is not None and _is_number(upper) and _is_number(lower):
                started = True
                mean = grid.get((row, mean_col))
                results.append(
                    ExpectedResult(
                        test_id=test_id,
                        case_id=str(case).strip(),
                        metric=title,
                        expected_value=float(mean) if _is_number(mean) else float(upper),
                        unit=unit,
                        absolute_tolerance=None,
                        relative_tolerance=None,
                        source_locator="{}!{}{}".format(
                            source_locator_prefix, get_column_letter(upper_col), row
                        ),
                        source_checksum=source_checksum,
                        lower_bound=float(lower),
                        upper_bound=float(upper),
                    )
                )
            elif started:
                break  # a populated non-band row ends the case block (new section)
    return tuple(results)


def parse_test3_reference_bands(
    workbook_path: Union[str, Path],
    sheet_names: Tuple[str, ...] = ("Zusammenfassung",),
    test_id: str = "3",
    source_checksum: str = "",
) -> Tuple[ExpectedResult, ...]:
    """Parse the explicit reference bands from the Test 3 evaluation workbook."""

    path = Path(workbook_path)
    workbook = load_workbook(path, data_only=True, read_only=True)
    try:
        results: List[ExpectedResult] = []
        for sheet_name in sheet_names:
            if sheet_name not in workbook.sheetnames:
                continue
            worksheet = workbook[sheet_name]
            if not hasattr(worksheet, "iter_rows"):
                continue
            results.extend(
                parse_inline_header_bands(
                    worksheet,
                    test_id=test_id,
                    source_locator_prefix="{}!{}".format(path.name, sheet_name),
                    row_label_headers=("testfälle", "testfaelle", "testfall"),
                    source_checksum=source_checksum,
                )
            )
        return tuple(results)
    finally:
        workbook.close()


def parse_grouped_case_column_bands(
    worksheet: Any,
    test_id: str,
    source_locator_prefix: str,
    source_checksum: str = "",
) -> Tuple[ExpectedResult, ...]:
    """Extract bands where rows are quantities and cases are grouped columns.

    Test 5 layout: the ``Mittelwert`` / ``Obere Grenze`` / ``Untere Grenze``
    headers each span one column per case (5A..5D). For quantity row ``r`` and
    case index ``i`` the band is (mean[start_mean+i], upper[start_upper+i],
    lower[start_lower+i]). Case labels are read from the case-label row.
    """

    grid, max_row, max_col = _read_sheet(worksheet)

    def _group_start(label: str) -> Optional[Tuple[int, int]]:
        """Return the (row, col) of the first cell whose header equals label."""

        for (r, c), value in grid.items():
            if _norm(value) == label:
                return r, c
        return None

    mean = _group_start(_MEAN)
    upper = _group_start(_UPPER)
    lower = _group_start(_LOWER)
    if not (mean and upper and lower):
        return ()
    header_row, mean_start = mean
    upper_start, lower_start = upper[1], lower[1]
    width = upper_start - mean_start
    if width < 1 or (lower_start - upper_start) != width:
        return ()
    # Case labels: the row with the most "Test <id>" tokens, first `width` distinct.
    token = "test {}".format(test_id)
    label_row_counts: Dict[int, int] = {}
    for (r, _c), value in grid.items():
        if isinstance(value, str) and token in value.strip().lower():
            label_row_counts[r] = label_row_counts.get(r, 0) + 1
    if not label_row_counts:
        return ()
    case_row = max(label_row_counts, key=label_row_counts.get)
    ordered: List[str] = []
    for col in range(1, max_col + 1):
        value = grid.get((case_row, col))
        if isinstance(value, str) and token in value.strip().lower():
            label = value.strip()
            if label not in ordered:
                ordered.append(label)
    case_labels = ordered[:width]
    if len(case_labels) < width:
        return ()

    results: List[ExpectedResult] = []
    started = False
    for row in range(header_row + 1, max_row + 1):
        metric = grid.get((row, 1))
        row_bands = []
        for i in range(width):
            m = grid.get((row, mean_start + i))
            u = grid.get((row, upper_start + i))
            lower = grid.get((row, lower_start + i))
            if _is_number(u) and _is_number(lower) and float(lower) <= float(u):
                row_bands.append((i, m, u, lower))
        if isinstance(metric, str) and row_bands:
            started = True
            unit = _first_unit_in_row(grid, row, max_col)
            for i, m, u, lower in row_bands:
                results.append(
                    ExpectedResult(
                        test_id=test_id,
                        case_id=case_labels[i],
                        metric=metric.strip(),
                        expected_value=float(m) if _is_number(m) else float(u),
                        unit=unit,
                        absolute_tolerance=None,
                        relative_tolerance=None,
                        source_locator="{}!{}{}".format(
                            source_locator_prefix,
                            get_column_letter(upper_start + i),
                            row,
                        ),
                        source_checksum=source_checksum,
                        lower_bound=float(lower),
                        upper_bound=float(u),
                    )
                )
        elif started and isinstance(metric, str) and not row_bands:
            break  # a labelled non-band row ends the obligatory block
    return tuple(results)


def parse_test5_reference_bands(
    workbook_path: Union[str, Path],
    sheet_names: Tuple[str, ...] = ("Zusammenfassung",),
    test_id: str = "5",
    source_checksum: str = "",
) -> Tuple[ExpectedResult, ...]:
    """Parse the explicit reference bands from the Test 5 evaluation workbook."""

    path = Path(workbook_path)
    workbook = load_workbook(path, data_only=True, read_only=True)
    try:
        results: List[ExpectedResult] = []
        for sheet_name in sheet_names:
            if sheet_name not in workbook.sheetnames:
                continue
            worksheet = workbook[sheet_name]
            if not hasattr(worksheet, "iter_rows"):
                continue
            results.extend(
                parse_grouped_case_column_bands(
                    worksheet,
                    test_id=test_id,
                    source_locator_prefix="{}!{}".format(path.name, sheet_name),
                    source_checksum=source_checksum,
                )
            )
        return tuple(results)
    finally:
        workbook.close()


def _first_unit_in_row(grid: Dict[Tuple[int, int], Any], row: int, max_col: int) -> str:
    """Return the first recognised unit token found in a single row."""

    for col in range(1, max_col + 1):
        value = grid.get((row, col))
        if isinstance(value, str) and _UNIT_PATTERN.match(value):
            return value.strip()
    return ""


def parse_metric_per_row_bands(
    worksheet: Any,
    test_id: str,
    case_id: str,
    source_locator_prefix: str,
    source_checksum: str = "",
) -> Tuple[ExpectedResult, ...]:
    """Extract bands where each data row is a quantity of one example-building case.

    Test 4 layout: a single case whose rows are named quantities (``Testgroessen``
    carry a band; ``Diagnosegroessen`` do not), the unit sits in a per-row cell,
    and the band columns are fixed for the block. Only rows that actually hold a
    numeric band (the obligatory quantities) are emitted.
    """

    grid, max_row, max_col = _read_sheet(worksheet)
    header_rows = sorted({r for (r, _c), value in grid.items() if _norm(value) == _MEAN})
    if not header_rows:
        return ()
    header_row = header_rows[0]
    blocks = _mean_band_blocks(grid, header_row, max_col)
    if not blocks:
        return ()
    mean_col, upper_col, lower_col = blocks[0]

    # Pass 1: collect the contiguous block of rows that actually carry a band.
    banded_rows: List[int] = []
    started = False
    for row in range(header_row + 1, max_row + 1):
        upper = grid.get((row, upper_col))
        lower = grid.get((row, lower_col))
        has_text = any(isinstance(grid.get((row, c)), str) for c in range(1, upper_col))
        is_band = (
            _is_number(upper)
            and _is_number(lower)
            and float(lower) <= float(upper)  # reject reused columns / inverted junk
        )
        if is_band:
            started = True
            banded_rows.append(row)
        elif not has_text and upper is None and lower is None:
            continue  # blank gap row between sub-groups
        elif started and has_text:
            break  # a labelled non-band row ends the obligatory block
    if not banded_rows:
        return ()

    # Pass 2: the metric-label column is the one carrying text in the most
    # banded rows (col A for Test 4, col B for Test 6 where col A is a section).
    label_col, best = 1, -1
    for col in range(1, upper_col):
        count = sum(1 for r in banded_rows if isinstance(grid.get((r, col)), str))
        if count > best:
            best, label_col = count, col

    results: List[ExpectedResult] = []
    for row in banded_rows:
        metric = grid.get((row, label_col))
        if not isinstance(metric, str):
            continue
        mean = grid.get((row, mean_col))
        results.append(
            ExpectedResult(
                test_id=test_id,
                case_id=case_id,
                metric=metric.strip(),
                expected_value=(
                    float(mean) if _is_number(mean) else float(grid.get((row, upper_col)))
                ),
                unit=_first_unit_in_row(grid, row, max_col),
                absolute_tolerance=None,
                relative_tolerance=None,
                source_locator="{}!{}{}".format(
                    source_locator_prefix, get_column_letter(upper_col), row
                ),
                source_checksum=source_checksum,
                lower_bound=float(grid.get((row, lower_col))),
                upper_bound=float(grid.get((row, upper_col))),
            )
        )
    return tuple(results)


def parse_test4_reference_bands(
    workbook_path: Union[str, Path],
    sheet_names: Tuple[str, ...] = ("Zusammenfassung",),
    test_id: str = "4",
    source_checksum: str = "",
) -> Tuple[ExpectedResult, ...]:
    """Parse the explicit reference bands from the Test 4 evaluation workbook."""

    path = Path(workbook_path)
    workbook = load_workbook(path, data_only=True, read_only=True)
    try:
        results: List[ExpectedResult] = []
        for sheet_name in sheet_names:
            if sheet_name not in workbook.sheetnames:
                continue
            worksheet = workbook[sheet_name]
            if not hasattr(worksheet, "iter_rows"):
                continue
            results.extend(
                parse_metric_per_row_bands(
                    worksheet,
                    test_id=test_id,
                    case_id="Test {}".format(test_id),
                    source_locator_prefix="{}!{}".format(path.name, sheet_name),
                    source_checksum=source_checksum,
                )
            )
        return tuple(results)
    finally:
        workbook.close()


def parse_test6_reference_bands(
    workbook_path: Union[str, Path],
    sheet_names: Tuple[str, ...] = ("Zusammenfassung",),
    test_id: str = "6",
    source_checksum: str = "",
) -> Tuple[ExpectedResult, ...]:
    """Parse the explicit reference bands from the Test 6 evaluation workbook.

    Test 6 shares Test 4's metric-per-row layout (single example-building case),
    so it reuses the same extractor; the metric labels sit in a column detected
    at runtime (col B here, col A for Test 4).
    """

    path = Path(workbook_path)
    workbook = load_workbook(path, data_only=True, read_only=True)
    try:
        results: List[ExpectedResult] = []
        for sheet_name in sheet_names:
            if sheet_name not in workbook.sheetnames:
                continue
            worksheet = workbook[sheet_name]
            if not hasattr(worksheet, "iter_rows"):
                continue
            results.extend(
                parse_metric_per_row_bands(
                    worksheet,
                    test_id=test_id,
                    case_id="Test {}".format(test_id),
                    source_locator_prefix="{}!{}".format(path.name, sheet_name),
                    source_checksum=source_checksum,
                )
            )
        return tuple(results)
    finally:
        workbook.close()


def parse_test7_reference_bands(
    workbook_path: Union[str, Path],
    sheet_names: Tuple[str, ...] = ("Zusammenfassung",),
    test_id: str = "7",
    source_checksum: str = "",
) -> Tuple[ExpectedResult, ...]:
    """Parse the explicit reference bands from the Test 7 evaluation workbook.

    Test 7 (total energy: refrigeration, heat pump, PV) shares the Test 4/6
    metric-per-row layout for its obligatory annual quantities.
    """

    path = Path(workbook_path)
    workbook = load_workbook(path, data_only=True, read_only=True)
    try:
        results: List[ExpectedResult] = []
        for sheet_name in sheet_names:
            if sheet_name not in workbook.sheetnames:
                continue
            worksheet = workbook[sheet_name]
            if not hasattr(worksheet, "iter_rows"):
                continue
            results.extend(
                parse_metric_per_row_bands(
                    worksheet,
                    test_id=test_id,
                    case_id="Test {}".format(test_id),
                    source_locator_prefix="{}!{}".format(path.name, sheet_name),
                    source_checksum=source_checksum,
                )
            )
        return tuple(results)
    finally:
        workbook.close()


def parse_test2_reference_bands(
    workbook_path: Union[str, Path],
    sheet_names: Tuple[str, ...] = ("Zusammenfassung",),
    test_id: str = "2",
    source_checksum: str = "",
) -> Tuple[ExpectedResult, ...]:
    """Parse the explicit reference bands from the Test 2 evaluation workbook."""

    path = Path(workbook_path)
    workbook = load_workbook(path, data_only=True, read_only=True)
    try:
        results: List[ExpectedResult] = []
        for sheet_name in sheet_names:
            if sheet_name not in workbook.sheetnames:
                continue
            worksheet = workbook[sheet_name]
            if not hasattr(worksheet, "iter_rows"):
                continue
            results.extend(
                parse_case_per_row_bands(
                    worksheet,
                    test_id=test_id,
                    source_locator_prefix="{}!{}".format(path.name, sheet_name),
                    row_label_header="fall",
                    source_checksum=source_checksum,
                )
            )
        return tuple(results)
    finally:
        workbook.close()


def parse_test1_reference_bands(
    workbook_path: Union[str, Path],
    sheet_names: Tuple[str, ...] = ("Zusammenfassung Testfälle",),
    test_id: str = "1",
    source_checksum: str = "",
) -> Tuple[ExpectedResult, ...]:
    """Parse the explicit reference bands from the Test 1 evaluation workbook."""

    path = Path(workbook_path)
    workbook = load_workbook(path, data_only=True, read_only=True)
    try:
        results: List[ExpectedResult] = []
        for sheet_name in sheet_names:
            if sheet_name not in workbook.sheetnames:
                continue
            worksheet = workbook[sheet_name]
            if not hasattr(worksheet, "iter_rows"):
                continue  # skip chartsheets
            results.extend(
                extract_reference_bands(
                    worksheet,
                    test_id=test_id,
                    source_locator_prefix="{}!{}".format(path.name, sheet_name),
                    source_checksum=source_checksum,
                )
            )
        return tuple(results)
    finally:
        workbook.close()
