"""Conservative adapters for transferring results to official SIA 4010 workbooks.

The official workbook layouts are not distributed with this repository. These
adapters therefore remain explicit integration boundaries rather than guessing
worksheet names, cell locations, units, or formulas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, NoReturn, Optional


def transfer_test_1_results(
    results: Mapping[str, Any],
    evidence_dir: Optional[Path] = None,
) -> NoReturn:
    """Require ``sia4010_evidence/SIA4010_official_evaluation_workbook_test_1_*.xlsx`` or ``.xlsm``."""
    raise NotImplementedError(
        "Missing official SIA 4010 evaluation workbook for test 1. Place "
        "sia4010_evidence/SIA4010_official_evaluation_workbook_test_1_*.xlsx "
        "or .xlsm in sia4010_evidence before implementing result transfer."
    )


def transfer_test_2_results(
    results: Mapping[str, Any],
    evidence_dir: Optional[Path] = None,
) -> NoReturn:
    """Require ``sia4010_evidence/SIA4010_official_evaluation_workbook_test_2_*.xlsx`` or ``.xlsm``."""
    raise NotImplementedError(
        "Missing official SIA 4010 evaluation workbook for test 2. Place "
        "sia4010_evidence/SIA4010_official_evaluation_workbook_test_2_*.xlsx "
        "or .xlsm in sia4010_evidence before implementing result transfer."
    )


def transfer_test_3_results(
    results: Mapping[str, Any],
    evidence_dir: Optional[Path] = None,
) -> NoReturn:
    """Require ``sia4010_evidence/SIA4010_official_evaluation_workbook_test_3_*.xlsx`` or ``.xlsm``."""
    raise NotImplementedError(
        "Missing official SIA 4010 evaluation workbook for test 3. Place "
        "sia4010_evidence/SIA4010_official_evaluation_workbook_test_3_*.xlsx "
        "or .xlsm in sia4010_evidence before implementing result transfer."
    )


def transfer_test_4_results(
    results: Mapping[str, Any],
    evidence_dir: Optional[Path] = None,
) -> NoReturn:
    """Require ``sia4010_evidence/SIA4010_official_evaluation_workbook_test_4_*.xlsx`` or ``.xlsm``."""
    raise NotImplementedError(
        "Missing official SIA 4010 evaluation workbook for test 4. Place "
        "sia4010_evidence/SIA4010_official_evaluation_workbook_test_4_*.xlsx "
        "or .xlsm in sia4010_evidence before implementing result transfer."
    )


def transfer_test_5_results(
    results: Mapping[str, Any],
    evidence_dir: Optional[Path] = None,
) -> NoReturn:
    """Require ``sia4010_evidence/SIA4010_official_evaluation_workbook_test_5_*.xlsx`` or ``.xlsm``."""
    raise NotImplementedError(
        "Missing official SIA 4010 evaluation workbook for test 5. Place "
        "sia4010_evidence/SIA4010_official_evaluation_workbook_test_5_*.xlsx "
        "or .xlsm in sia4010_evidence before implementing result transfer."
    )


def transfer_test_6_results(
    results: Mapping[str, Any],
    evidence_dir: Optional[Path] = None,
) -> NoReturn:
    """Require ``sia4010_evidence/SIA4010_official_evaluation_workbook_test_6_*.xlsx`` or ``.xlsm``."""
    raise NotImplementedError(
        "Missing official SIA 4010 evaluation workbook for test 6. Place "
        "sia4010_evidence/SIA4010_official_evaluation_workbook_test_6_*.xlsx "
        "or .xlsm in sia4010_evidence before implementing result transfer."
    )


def transfer_test_7_results(
    results: Mapping[str, Any],
    evidence_dir: Optional[Path] = None,
) -> NoReturn:
    """Require ``sia4010_evidence/SIA4010_official_evaluation_workbook_test_7_*.xlsx`` or ``.xlsm``."""
    raise NotImplementedError(
        "Missing official SIA 4010 evaluation workbook for test 7. Place "
        "sia4010_evidence/SIA4010_official_evaluation_workbook_test_7_*.xlsx "
        "or .xlsm in sia4010_evidence before implementing result transfer."
    )
