# -*- coding: utf-8 -*-
"""Excel export -- fills the official SIA workbook over COM (Pywin32), in
`Handeingabe` mode (docs/ADR-001-architecture-MSP.md, 4).

--------------------------------------------------------------------------
EXECUTION STATUS -- READ BEFORE TRUSTING THIS MODULE
--------------------------------------------------------------------------
`pywin32` installs and **Excel (Office16) is genuinely present** on this
development machine (`reg query "HKLM\\SOFTWARE\\Microsoft\\Windows\\
CurrentVersion\\App Paths\\EXCEL.EXE"`). `ui/tests/test_excel_export.py`
therefore drives a **real** Excel process over COM against a throwaway workbook
created for the test -- never a file from `SIA_4010_geteilter_Link/`: open,
write cells, read back, save, close. That test is `pytest.mark.skipif`-ed when
`win32com` is unavailable, so collection never fails elsewhere.

**What that test does NOT prove:**

1. Behaviour against the REAL SIA workbook (`Resultaterfassung_Test1.xlsx`,
   sheet `Daten_Testprogramm`). Whether a sheet of that name, a cell `H3` and
   the `J:N` columns of the Handeingabe area really exist could not be checked
   here -- those files are not in this repository's `/refs` (130 MB, ADR-001
   7 bis). Tested only against a throwaway workbook that REPRODUCES the minimal
   structure the ADR describes.
2. Behaviour inside a real VEScripts environment (embedded Python, Pywin32 219
   -- ADR-001 2; that version is not what this Python 3.13 has).
3. **The cell map.** NO Handeingabe cell address is hard-coded here. ADR-001 5
   defers that map to a future descriptor (`refs/reference-data/testN.map.json`)
   which does not exist yet. This module REFUSES to guess an address:
   `cell_map` must come from the caller, or `fill_sia_workbook` raises a precise
   error rather than writing somewhere at random.

This module recalculates and invents nothing. It writes exactly
`ligne['valeur_candidate']`, as produced by
`engine/test1_engine.py::evaluer_test1()` and passed through unchanged by
`ui/verdict_view.py`.

TWO GUARD-RAILS WORTH KNOWING, both of which exist because of the same failure
mode -- a wrong number that looks like a measurement:

* every write is READ BACK, and a divergence raises. ADR-001 7 bis records an
  "Excel error silently converted to 0";
* a missing candidate value leaves the cell UNTOUCHED. Writing 0 there would
  fabricate a measured zero. The cells left untouched are REPORTED, not merely
  counted -- a workbook used to be able to leave with blank cells and nobody
  learning of it, which is exactly the Test 7 photovoltaic case.
"""

import shutil

# Cell confirmed by ADR-001 4 (cited proof: the formula
# `B16 = IF(Daten_Testprogramm!$H$3="Handeingabe"; ...)` on sheet
# `Zusammenfassung Testfälle`) -- THE ONLY cell address this module knows with
# certainty.
DATA_SHEET = "Daten_Testprogramm"
ENTRY_MODE_CELL = "H3"
HANDEINGABE_MODE_VALUE = "Handeingabe"


class MissingCellMap(RuntimeError):
    """Raised when the caller supplied no cell map.

    See the module note, reservation 3: no Handeingabe cell address is invented
    by this repository to date.
    """


class ExcelWriteDiverged(RuntimeError):
    """Raised when reading a cell back does not match what was written.

    Guard-rail against the risk ADR-001 7 bis records -- "Excel error silently
    converted to 0" -- on the same principle as
    `ve_adapter/test1_adapter.py::creer_materiau`: write, read back, fail hard
    on divergence.
    """


def _win32com():
    """Import `win32com.client`, with a message that says where it lives.

    Returns:
        module: `win32com.client`.

    Raises:
        ImportError: When Pywin32 is absent.
    """
    try:
        import win32com.client

        return win32com.client
    except ImportError as error:
        raise ImportError(
            "Module 'win32com' unavailable: the COM Excel export needs "
            "Pywin32, which ships inside VEScripts "
            "(docs/ADR-001-architecture-MSP.md 2) or installs with "
            "`pip install pywin32` in development. Original error: " + str(error)
        )


def _row_value(test1_view, period_key):
    """Find `valeur_candidate` for one (quantity, case, period) key.

    Args:
        test1_view: What `ui/verdict_view.py::construire_vue_test1` builds.
        period_key: `(quantity, case, period)`.

    Returns:
        The candidate value, or `None`. NEVER `0` by default when the row is
        absent or its value is `None` -- the caller decides, and this module
        then writes nothing into the corresponding cell.
    """
    quantity, case, period = period_key
    for row in test1_view["lignes"]:
        if (row["grandeur"], row["cas"], row["periode"]) == (quantity, case, period):
            return row["valeur_candidate"]
    return None


def fill_sia_workbook_reporting(
    source_path,
    test1_view,
    cell_map=None,
    output_path=None,
    sheet=DATA_SHEET,
    keep_excel_visible=False,
):
    """Fill a COPY of the official SIA workbook in `Handeingabe` mode.

    Args:
        source_path: An EXISTING workbook -- preferably already a working copy,
            never a file from `SIA_4010_geteilter_Link/` (ADR-001 4: "run on a
            copy, never on the files that are the frozen source"). This module
            makes a further copy to `output_path` as defence in depth and NEVER
            opens `source_path` for writing.
        test1_view: What `construire_vue_test1` builds.
        cell_map: Mandatory `{(quantity, case, period): cell address}`, for
            example `{('sensible_heating_demand_kwh', '1E', 'annual'): 'N28'}`,
            on `sheet`. No default is supplied here -- see the module note.
        output_path: Where the filled workbook goes. Defaults to
            `<source_path>` with `_rempli` inserted before the extension.
        sheet: Sheet name to write into.
        keep_excel_visible: Show the Excel window, for debugging.

    Returns:
        dict: A full report, including the cells left blank for want of a
        candidate value.

    Raises:
        MissingCellMap: If `cell_map` is empty. Guessing a Handeingabe address
            would write a real number into the wrong box.

    Note:
        ⚠ À VÉRIFIER -- behaviour against the REAL SIA workbook is unproven
        (module note, reservations 1 and 2).
    """
    if not cell_map:
        raise MissingCellMap(
            "No (quantity, case, period) -> cell map supplied. ADR-001 5 "
            "defers that map to a future descriptor "
            "(refs/reference-data/testN.map.json), absent to date. Pass "
            "`cell_map` explicitly rather than guessing a Handeingabe cell "
            "address."
        )

    if output_path is None:
        stem, extension = _split_extension(source_path)
        output_path = stem + "_rempli" + extension

    # Defence in depth: never open source_path for writing, even when the
    # caller has already copied it themselves (ADR-001 4).
    shutil.copyfile(source_path, output_path)

    win32com_client = _win32com()
    excel = win32com_client.Dispatch("Excel.Application")
    excel.Visible = bool(keep_excel_visible)
    excel.DisplayAlerts = False
    workbook = None
    try:
        workbook = excel.Workbooks.Open(output_path)
        data_sheet = workbook.Worksheets(sheet)

        # Turn on Handeingabe mode -- the ONLY address ADR-001 4 confirms.
        _write_and_verify_cell(data_sheet, ENTRY_MODE_CELL, HANDEINGABE_MODE_VALUE)

        written, skipped_no_value = [], []
        for period_key, cell_address in cell_map.items():
            value = _row_value(test1_view, period_key)
            if value is None:
                # NEVER write 0 in place of a missing value (a candidate that
                # was not simulated). Leave the Excel cell untouched rather
                # than fabricate a false zero that could pass for a genuine
                # measured nought.
                skipped_no_value.append((period_key, cell_address))
                continue
            _write_and_verify_cell(data_sheet, cell_address, value)
            written.append((period_key, cell_address))

        # Force a full recalculation -- required for the `Testprogramm`
        # columns (computed, never entered -- ADR-001 4) to reflect the new
        # Handeingabe values before saving.
        excel.CalculateFullRebuild()

        workbook.Save()
    finally:
        if workbook is not None:
            # Already saved explicitly above.
            workbook.Close(SaveChanges=False)
        excel.Quit()

    return {
        "chemin_sortie": output_path,
        "test_id": test1_view.get("test_id"),
        "feuille": sheet,
        "cellules_ecrites": written,
        # Cells left INTACT for want of a candidate value. These used to be
        # counted and then discarded: a workbook could leave with blank cells
        # and nobody learning of it. That is exactly the Test 7 photovoltaic
        # case.
        "cellules_ignorees_valeur_absente": skipped_no_value,
        "complet": not skipped_no_value,
    }


def fill_sia_workbook(
    source_path,
    test1_view,
    cell_map=None,
    output_path=None,
    sheet=DATA_SHEET,
    keep_excel_visible=False,
):
    """Fill a copy of the SIA workbook and return the PATH of the result.

    Kept for existing callers. To learn which cells were left blank for want of
    a candidate value -- information you need as soon as a test is only
    partially simulated -- use `fill_sia_workbook_reporting`, which returns the
    full report.

    Args:
        source_path: See `fill_sia_workbook_reporting`.
        test1_view: See `fill_sia_workbook_reporting`.
        cell_map: See `fill_sia_workbook_reporting`.
        output_path: See `fill_sia_workbook_reporting`.
        sheet: See `fill_sia_workbook_reporting`.
        keep_excel_visible: See `fill_sia_workbook_reporting`.

    Returns:
        str: Path of the filled workbook.
    """
    return fill_sia_workbook_reporting(
        source_path,
        test1_view,
        cell_map=cell_map,
        output_path=output_path,
        sheet=sheet,
        keep_excel_visible=keep_excel_visible,
    )["chemin_sortie"]


def fill_sia_workbooks(jobs, keep_excel_visible=False):
    """Fill ONE SIA workbook PER TEST.

    Each SIA test has its own evaluation workbook
    (`Resultaterfassung_Test1.xlsx`, `Resultaterfassung Test7.xlsx`, ...):
    there is no single workbook to fill for several tests. This orchestrates a
    series of independent fills.

    A job that fails DOES NOT STOP the others: its error is recorded and
    processing continues. Reporting one failure while hiding three successes --
    or the reverse -- would be worse than either.

    Args:
        jobs: A list of `{'vue': ..., 'chemin_source': ..., 'carte_cellules':
            ...}`, optionally with `chemin_sortie` and `feuille`.
        keep_excel_visible: Show the Excel window, for debugging.

    Returns:
        dict: `{'rapports': [...], 'echecs': [...], 'complet': bool}`.
        `complet` is true only when EVERY job succeeded AND no cell was left
        blank.
    """
    reports, failures = [], []
    for job in jobs:
        view = job["vue"]
        try:
            reports.append(
                fill_sia_workbook_reporting(
                    job["chemin_source"],
                    view,
                    cell_map=job.get("carte_cellules"),
                    output_path=job.get("chemin_sortie"),
                    sheet=job.get("feuille", DATA_SHEET),
                    keep_excel_visible=keep_excel_visible,
                )
            )
        except Exception as error:  # noqa: BLE001 -- one failure must not stop
            failures.append(
                {
                    "test_id": view.get("test_id"),
                    "chemin_source": job.get("chemin_source"),
                    "erreur": "%s: %s" % (type(error).__name__, error),
                }
            )

    return {
        "rapports": reports,
        "echecs": failures,
        "complet": ((not failures) and all(report["complet"] for report in reports)),
    }


def _split_extension(path):
    """Split a path into stem and extension.

    Args:
        path: A file path.

    Returns:
        tuple[str, str]: `(stem, extension)`; the extension is `''` when there
        is no dot.
    """
    dot = path.rfind(".")
    if dot == -1:
        return path, ""
    return path[:dot], path[dot:]


def _write_and_verify_cell(com_sheet, cell_address, value, tolerance=1e-9):
    """Write a value into a cell, then read it back to check it persisted.

    Direct guard-rail against ADR-001 7 bis ("Excel error silently converted to
    0"), on the write/read-back pattern already established by
    `ve_adapter/test1_adapter.py`.

    Args:
        com_sheet: A COM worksheet.
        cell_address: For example `'N28'`.
        value: What to write.
        tolerance: Numeric comparison tolerance on read-back.

    Raises:
        ExcelWriteDiverged: When the read-back does not match.
    """
    cell = com_sheet.Range(cell_address)
    cell.Value = value
    read_back = cell.Value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if read_back is None or abs(float(read_back) - float(value)) > tolerance:
            raise ExcelWriteDiverged(
                "Cell {0}: written={1!r}, read back={2!r} -- divergence, do "
                "not continue.".format(cell_address, value, read_back)
            )
    elif read_back != value:
        raise ExcelWriteDiverged(
            "Cell {0}: written={1!r}, read back={2!r} -- divergence, do not "
            "continue.".format(cell_address, value, read_back)
        )
