# -*- coding: utf-8 -*-
"""Scatter band of the SIA 4010 reference programs.

This is the central acceptance criterion of SIA 4010: the candidate program must
fall inside the band formed by the reference programs.

FORMULA -- read directly from the official SIA workbooks, not inferred:

    mean        = AVERAGE(contributing programs)
    upper bound = mean + MAX(ABS(program - mean))
    lower bound = mean - MAX(ABS(program - mean))

Sources (read with openpyxl, data_only=False):
  - Resultaterfassung_Test1.xlsx, sheet "Zusammenfassung Testfaelle":
        H16 = =G16+MAX(ABS(C16-G16),ABS(D16-G16),ABS(E16-G16),ABS(F16-G16))
        I16 = =MAX(0,G16-MAX(ABS(C16-G16),...))          <- Table 28, floored at 0
        H82/I82 likewise                                  <- Table 31
  - Resultaterfassung_Test2.xlsx, sheet "Zusammenfassung":
        N14 = =M14+MAX(ABS(E14-M14),ABS(H14-M14),ABS(K14-M14),ABS(L14-M14))
        O14 = =M14-MAX(...)                               <- NO zero floor

The German labels quoted above ("Mittelwert", "obere Grenze", "untere Grenze",
"Streubereich") are kept verbatim wherever they are source data -- workbook
header text or normative wording. They are lookup keys, not prose: translating
them would break the match against the official files.

ZERO FLOOR: present in Test 1 (MAX(0, ...)), absent in Test 2. It is therefore a
property of the table, not of the formula. Never apply it by default;
`floor_at_zero` must be passed explicitly based on the workbook at hand.

FREQUENCY-DISTRIBUTION CRITERION (Tests 2 to 5): the same band applies bin by
bin. The workbook tabulates no band for that criterion, so it must be derived.
Arbitration recorded in `traceability/streubereich-distributions.spec.md`
(~92% confidence). The competing "min/max envelope" reading was set aside but
not refuted, hence `verdict()` returns an intermediate PASS_WITH_RESERVATION
state where the two readings disagree: the decision stays reversible without
rewriting the engine.

CONTRIBUTING SET: not guessable. The SIA keeps ONE variant per program, and not
the same variant across programs (Test 2: IDA_ICE "Fe det Spec", Excel, Energy+
"Fe einf", TAS "Fe det nonSpect"; the other columns are excluded). A program
that did not deliver a case drops out of the mean and is never counted as zero.
The only safe rule is to READ that set from the workbook's own AVERAGE formula
-- see `contributors_from_formula()`.

Pure Python, no dependencies, no `import iesve`: testable in CI without a VE
licence and runnable as-is inside VEScripts.
"""

import re

VERDICT_PASS = "PASS"
VERDICT_PASS_WITH_RESERVATION = "PASS_WITH_RESERVATION"
VERDICT_FAIL = "FAIL"
VERDICT_NOT_CHECKABLE = "NOT_CHECKABLE"


class ScatterBand(object):
    """Scatter band of a set of reference-program values."""

    __slots__ = (
        "mean",
        "max_deviation",
        "lower_bound",
        "upper_bound",
        "contributors",
        "floored_at_zero",
    )

    def __init__(
        self, mean, max_deviation, lower_bound, upper_bound, contributors, floored_at_zero
    ):
        self.mean = mean
        self.max_deviation = max_deviation
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.contributors = contributors
        self.floored_at_zero = floored_at_zero

    def contains(self, value, tolerance=0.0):
        """Bounds are INCLUSIVE: the workbook defines no strict exclusion."""
        return (self.lower_bound - tolerance) <= value <= (self.upper_bound + tolerance)

    def __repr__(self):
        return "ScatterBand(mean={0!r}, [{1!r}, {2!r}], n={3})".format(
            self.mean, self.lower_bound, self.upper_bound, self.contributors
        )


def build_band(values, floor_at_zero=False):
    """Return the ScatterBand of a set of reference-program values.

    `values` must hold only the CONTRIBUTING programs. Programs that did not
    deliver the case must have been removed beforehand -- passing them as zero
    would skew the mean and therefore the band.

    `floor_at_zero` applies `max(0, ...)` to the lower bound, as Test 1 does.
    Pass it only when the workbook at hand actually does so.
    """
    kept = [float(v) for v in values if v is not None]
    if not kept:
        return None
    mean = sum(kept) / float(len(kept))
    max_deviation = max(abs(v - mean) for v in kept)
    upper_bound = mean + max_deviation
    lower_bound = mean - max_deviation
    if floor_at_zero:
        lower_bound = max(0.0, lower_bound)
    return ScatterBand(
        mean, max_deviation, lower_bound, upper_bound, len(kept), floor_at_zero
    )


def build_envelope(values):
    """Competing reading set aside by the arbitration: the min..max span.

    Kept in order to produce the PASS_WITH_RESERVATION state. Arithmetically
    [min, max] is ALWAYS contained in the symmetric band, so the envelope is a
    strictly stricter criterion.
    """
    kept = [float(v) for v in values if v is not None]
    if not kept:
        return None
    return (min(kept), max(kept))


def verdict(candidate_value, reference_values, floor_at_zero=False, tolerance=0.0):
    """Return the three-state verdict of the arbitration.

    - PASS                    : inside the band AND the envelope -- both
                                readings agree, no arbitration risk.
    - PASS_WITH_RESERVATION   : inside the retained band but outside the
                                envelope. Report it and prepare the point for
                                the sub-commission (SIA 4010 clause 4.6.2).
    - FAIL                    : outside both -- a failure under either reading.
    - NOT_CHECKABLE           : candidate or references missing. Never a pass by
                                default.
    """
    if candidate_value is None:
        return VERDICT_NOT_CHECKABLE
    band = build_band(reference_values, floor_at_zero=floor_at_zero)
    if band is None:
        return VERDICT_NOT_CHECKABLE
    if not band.contains(candidate_value, tolerance):
        return VERDICT_FAIL
    low, high = build_envelope(reference_values)
    if (low - tolerance) <= candidate_value <= (high + tolerance):
        return VERDICT_PASS
    return VERDICT_PASS_WITH_RESERVATION


def is_passing(status):
    """Whether a verdict counts as meeting the criterion.

    Use this instead of `== VERDICT_PASS`: a reserved pass IS a pass under the
    retained reading, and comparing against PASS alone would silently turn it
    into a failure.
    """
    return status in (VERDICT_PASS, VERDICT_PASS_WITH_RESERVATION)


# ---------------------------------------------------------------------------
# Reading the contributing set from the workbook formula
# ---------------------------------------------------------------------------

_AVERAGE_PATTERN = re.compile(r"^=\s*AVERAGE\s*\((.+)\)\s*$", re.IGNORECASE)
_RANGE_PATTERN = re.compile(r"^\$?([A-Z]{1,3})\$?(\d{1,5}):\$?([A-Z]{1,3})\$?(\d{1,5})$")
_CELL_PATTERN = re.compile(r"^\$?([A-Z]{1,3})\$?(\d{1,5})$")


def _column_index(letters):
    index = 0
    for char in letters:
        index = index * 26 + (ord(char) - 64)
    return index


def _column_letters(index):
    letters = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def contributors_from_formula(formula):
    """Return the cells averaged by an `=AVERAGE(...)` formula.

    This is the only reliable way to know the contributing set: the SIA selects
    one variant per program with no derivable general rule. Handles the two
    shapes found in the official workbooks: `=AVERAGE(C16:F16)` (range) and
    `=AVERAGE(E14,H14,K14,L14)` (list).

    Returns `[]` when the formula is not a plain AVERAGE -- a nested or
    cross-sheet call must be handled explicitly, never guessed.
    """
    if not isinstance(formula, str):
        return []
    match = _AVERAGE_PATTERN.match(formula.strip())
    if match is None:
        return []
    body = match.group(1)
    if "(" in body or "!" in body:
        return []  # nested or cross-sheet: out of scope, do not guess
    cells = []
    for term in body.split(","):
        term = term.strip()
        span = _RANGE_PATTERN.match(term)
        if span is not None:
            col1, row1, col2, row2 = span.groups()
            if row1 != row2:
                return []  # multi-row range: unsupported, do not guess
            start, end = _column_index(col1), _column_index(col2)
            if end < start:
                start, end = end, start
            for i in range(start, end + 1):
                cells.append(_column_letters(i) + row1)
            continue
        cell = _CELL_PATTERN.match(term)
        if cell is None:
            return []  # unrecognised term: refuse rather than approximate
        cells.append(cell.group(1) + cell.group(2))
    return cells
