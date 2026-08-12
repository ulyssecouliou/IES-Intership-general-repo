# -*- coding: utf-8 -*-
"""Read-only extractor for the SIA frequency-class definition sheet.

**All six** SIA 4010 evaluation workbooks that carry distributions (Tests 2
to 7) define, per output quantity, the upper bounds of the frequency-class
bins used by the distribution criterion.  The sheet name is spelled
inconsistently across the official files:

===========  ==============================  ==================
Test         Sheet name                      Binned quantities
===========  ==============================  ==================
2            ``Haeufigkeitsklassen``          4
3            ``Haeufigkeitsklassen``          3
4            ``Haeufigkeitskassen``          11
5            ``Haeufigkeitsklassen``         11
6            ``Haeufigkeitskassen``          11
7            ``Haeufigkeitskassen``          20
===========  ==============================  ==================

Tests 4, 6 and 7 drop the ``l`` of ``Klassen``.  Both spellings are therefore
accepted; matching only one silently excluded three workbooks, which is how an
earlier version of this module concluded that Tests 2, 3 and 5 had no
frequency classes.  Verified by direct openpyxl inspection on 2026-08-12.

Two earlier repository claims are refuted by that same inspection and must not
be reintroduced:

* "Tests 4 and 6 carry no frequency classes" — they carry 11 quantities each,
  more than Test 2 (4) and Test 3 (3).
* "Tests 2, 3 and 5 use one ``Verteilung_*`` sheet per distribution instead of
  a frequency-class sheet" — they use both, exactly like the others.

This module extracts the bins strictly from the observed layout: row 1 = the
section header ``Klassen``; row 2 = per-column quantity labels (German), row 3
= units, rows 4..N = one row per class index, column A = class index, columns
B..end = per-quantity upper bound of the class.

Cells set to ``9999`` are kept apart from the numeric bounds. What that value
means is an inference, not an authority statement, and it is worth stating
carefully: in this definition sheet it repeats over many trailing classes of a
quantity, which reads as "this class is not used here". In the distribution
tables of the ``Zusammenfassung`` sheets, however, the first such class carries
real hour counts — it collects whatever exceeds the last real bound. The value
therefore behaves as "no upper limit", and only the classes after the first one
are genuinely unused. Downstream code should treat it as a bound it cannot
compare numerically, never as a measurement, and never assume it is empty.

The extractor is pure Python (openpyxl is the only external dependency, as
elsewhere in the repository).  It never mutates the workbook and never
follows formulas; it reads with ``data_only=True`` so display values are
recovered even when the workbook was cached without a recalculation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


#: Accepted spellings of the frequency-class sheet, in lookup order. The
#: misspelled form is real and appears in the official Tests 4, 6 and 7 files.
SHEET_NAME_CANDIDATES: Tuple[str, ...] = (
    "Haeufigkeitsklassen",
    "Haeufigkeitskassen",
)

#: Retained for callers that only need a label to show a user.
SHEET_NAME = SHEET_NAME_CANDIDATES[0]

SIA_NOT_USED_SENTINEL = 9999


@dataclass(frozen=True)
class QuantityBins:
    """One quantity column extracted from ``Haeufigkeitskassen``."""

    column_letter: str
    quantity_label: str
    unit: str
    class_indices: Tuple[int, ...]
    upper_bounds: Tuple[float, ...]
    sentinel_9999_class_indices: Tuple[int, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class HaeufigkeitskassenTable:
    """Structured extract of one workbook's frequency-class sheet."""

    workbook_path: str
    test_id: str
    row_range: Tuple[int, int]
    quantities: Tuple[QuantityBins, ...]
    #: The spelling actually found in this workbook. Recorded because the
    #: official files disagree and provenance must stay auditable.
    sheet_name: str = SHEET_NAME_CANDIDATES[0]

    def quantity_by_label(self, label: str) -> Optional[QuantityBins]:
        for q in self.quantities:
            if q.quantity_label == label:
                return q
        return None


def _cell(ws: Any, row: int, col: int) -> Any:
    return ws.cell(row=row, column=col).value


def _column_letter(idx: int) -> str:
    letters = ""
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def _coerce_class_index(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        s = value.strip()
        if s.isdigit():
            return int(s)
    return None


def _coerce_upper_bound(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip().replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _detect_last_row(ws: Any) -> int:
    """Return the last row whose column A is a class index (int)."""

    last = 3  # header rows 1..3
    row = 4
    while row <= ws.max_row:
        idx = _coerce_class_index(_cell(ws, row, 1))
        if idx is None:
            break
        last = row
        row += 1
    return last


def _is_quantity_column(ws: Any, col: int, last_row: int) -> bool:
    """Return whether one column is a binned quantity rather than a legend.

    The Tests 2 and 3 sheets carry a ``Fenstermodelle`` column listing window
    models as text, with no unit and no numeric bounds. It sits past a gap of
    empty columns, so an earlier version excluded it only by stopping at the
    first empty header. That was luck, not a rule: a legend placed adjacent to
    the quantities would have been read as a bin column, and a quantity placed
    past a gap would have been silently dropped.

    A binned quantity is therefore required to carry all three of: a label in
    row 2, a unit in row 3, and at least one numeric bound in rows 4..N.
    """

    label = _cell(ws, 2, col)
    if label is None or not str(label).strip():
        return False
    unit = _cell(ws, 3, col)
    if unit is None or not str(unit).strip():
        return False
    for row in range(4, last_row + 1):
        if _coerce_upper_bound(_cell(ws, row, col)) is not None:
            return True
    return False


def extract_haeufigkeitskassen(
    workbook_path: str,
    *,
    test_id: str,
    openpyxl_module: Any = None,
) -> HaeufigkeitskassenTable:
    """Extract the frequency-class bins of one Test evaluation workbook.

    Args:
        workbook_path: absolute path to the official ``Resultaterfassung``
            workbook of one SIA 4010 test.
        test_id: SIA test identifier ("4", "6", "7", ...), used in the returned
            structure for traceability.
        openpyxl_module: the ``openpyxl`` module (injected for testability).
            When ``None`` the module is imported locally.

    Returns:
        ``HaeufigkeitskassenTable`` with one ``QuantityBins`` entry per
        quantity column.

    Raises:
        FileNotFoundError: when ``workbook_path`` does not exist.
        KeyError: when the workbook carries none of ``SHEET_NAME_CANDIDATES``.
            Direct inspection on 2026-08-12 confirms every distribution-bearing
            workbook (Tests 2 to 7) carries one, under one of the two spellings.
            A workbook with neither is a source-integrity problem, not a layout
            variant.
    """

    if openpyxl_module is None:
        import openpyxl as openpyxl_module  # local import; io-only dependency
    wb = openpyxl_module.load_workbook(workbook_path, data_only=True)
    sheet_name = next(
        (name for name in SHEET_NAME_CANDIDATES if name in wb.sheetnames),
        None,
    )
    if sheet_name is None:
        raise KeyError(
            "Workbook {} carries none of the frequency-class sheets {}".format(
                workbook_path, SHEET_NAME_CANDIDATES
            )
        )
    ws = wb[sheet_name]

    last_row = _detect_last_row(ws)
    quantities: List[QuantityBins] = []
    # Scan every column: a binned quantity is identified by its own shape, not
    # by sitting before the first empty header.
    for col in range(2, ws.max_column + 1):
        if not _is_quantity_column(ws, col, last_row):
            continue
        label = _cell(ws, 2, col)
        unit = _cell(ws, 3, col)
        class_indices: List[int] = []
        upper_bounds: List[float] = []
        sentinels: List[int] = []
        for row in range(4, last_row + 1):
            idx = _coerce_class_index(_cell(ws, row, 1))
            if idx is None:
                continue
            bound = _coerce_upper_bound(_cell(ws, row, col))
            if bound is None:
                continue
            if bound == SIA_NOT_USED_SENTINEL:
                sentinels.append(idx)
                continue
            class_indices.append(idx)
            upper_bounds.append(bound)
        quantities.append(
            QuantityBins(
                column_letter=_column_letter(col),
                quantity_label=str(label).strip(),
                unit="" if unit is None else str(unit).strip(),
                class_indices=tuple(class_indices),
                upper_bounds=tuple(upper_bounds),
                sentinel_9999_class_indices=tuple(sentinels),
            )
        )
    return HaeufigkeitskassenTable(
        workbook_path=workbook_path,
        test_id=str(test_id),
        row_range=(4, last_row),
        quantities=tuple(quantities),
        sheet_name=sheet_name,
    )


def summarise(table: HaeufigkeitskassenTable) -> Dict[str, Any]:
    """Machine-readable summary of one extracted table (audit-friendly)."""

    return {
        "workbook_path": table.workbook_path,
        "test_id": table.test_id,
        "sheet_name": table.sheet_name,
        "row_range": list(table.row_range),
        "quantity_count": len(table.quantities),
        "quantities": [
            {
                "column_letter": q.column_letter,
                "quantity_label": q.quantity_label,
                "unit": q.unit,
                "class_count": len(q.class_indices),
                "class_indices": list(q.class_indices),
                "upper_bounds": list(q.upper_bounds),
                "sentinel_9999_class_indices": list(q.sentinel_9999_class_indices),
            }
            for q in table.quantities
        ],
    }


__all__ = [
    "SHEET_NAME",
    "SHEET_NAME_CANDIDATES",
    "SIA_NOT_USED_SENTINEL",
    "QuantityBins",
    "HaeufigkeitskassenTable",
    "extract_haeufigkeitskassen",
    "summarise",
]
