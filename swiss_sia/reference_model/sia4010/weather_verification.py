"""Traceable verification of the BESTEST DRYCOLD TMY1 weather source.

The SIA 4010 Test 1 climate workbook contains an ISO 52010-1 conversion of
DRYCOLD.TMY.  It is therefore useful for identifying the source weather file,
but its converted surface irradiances must not be mistaken for raw TMY1 solar
fields.  This module verifies the lossless hourly fields (calendar, dry-bulb
temperature and wind speed) and records the solar comparison as informative.
It never turns that source-identity check into a normative compliance claim.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Union

from ..exceptions import ConfigurationError


PathLike = Union[str, Path]
EXPECTED_ANNUAL_HOURS = 8760
ISO_INITIALIZATION_HOURS = 744
ISO_DATA_START_ROW_ZERO_BASED = 749


@dataclass(frozen=True)
class Tmy1Record:
    """Subset of one fixed-width NOAA TMY1 record needed for traceability."""

    station_id: str
    source_year: int
    month: int
    day: int
    hour_ending: int
    dry_bulb_c: float
    wind_speed_m_s: float
    global_horizontal_w_m2: float | None


def sha256_file(path: PathLike) -> str:
    """Return an uppercase SHA-256 digest."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def parse_tmy1(path: PathLike) -> List[Tmy1Record]:
    """Parse the auditable TMY1 fields used by the ISO workbook comparison."""

    source = Path(path)
    try:
        lines = source.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ConfigurationError(
            "Unable to read TMY1 weather file '{}': {}".format(source, exc)
        ) from exc

    records: List[Tmy1Record] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        if len(line) < 120:
            raise ConfigurationError(
                "TMY1 line {} is too short ({} characters)".format(
                    line_number, len(line)
                )
            )
        try:
            source_year_two_digits = int(line[5:7])
            source_year = (
                2000 + source_year_two_digits
                if source_year_two_digits < 20
                else 1900 + source_year_two_digits
            )
            ghi = (
                None
                if line[53] == "9"
                else max(0.0, float(line[54:58]) / 3.6)
            )
            record = Tmy1Record(
                station_id=line[0:5],
                source_year=source_year,
                month=int(line[7:9]),
                day=int(line[9:11]),
                hour_ending=int(line[11:13]),
                dry_bulb_c=float(line[103:107]) / 10.0,
                wind_speed_m_s=float(line[114:118]) / 10.0,
                global_horizontal_w_m2=ghi,
            )
        except (TypeError, ValueError) as exc:
            raise ConfigurationError(
                "Malformed TMY1 data at line {}: {}".format(line_number, exc)
            ) from exc
        if not 1 <= record.month <= 12:
            raise ConfigurationError(
                "TMY1 line {} has invalid month {}".format(
                    line_number, record.month
                )
            )
        if not 1 <= record.hour_ending <= 24:
            raise ConfigurationError(
                "TMY1 line {} has invalid hour {}".format(
                    line_number, record.hour_ending
                )
            )
        records.append(record)
    return records


def _maximum_absolute_difference(
    left: Iterable[float], right: Iterable[float]
) -> float:
    """Return the largest absolute difference between two aligned series."""

    differences = [abs(a - b) for a, b in zip(left, right)]
    return max(differences) if differences else 0.0


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write one JSON payload atomically through a temporary file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def verify_tmy1_against_iso_workbook(
    tmy_path: PathLike,
    workbook_path: PathLike,
    report_path: PathLike | None = None,
    *,
    tolerance: float = 1.0e-9,
) -> Dict[str, Any]:
    """Verify DRYCOLD source identity against the supplied ISO climate sheet.

    ``xlrd`` is imported lazily because it is bundled with IESVE Python but is
    not needed by the runtime model builder after the evidence report exists.
    """

    try:
        import xlrd  # type: ignore
    except ImportError as exc:
        raise ConfigurationError(
            "xlrd is required to verify the legacy ISO .xls climate workbook"
        ) from exc

    tmy = Path(tmy_path).resolve()
    workbook = Path(workbook_path).resolve()
    records = parse_tmy1(tmy)
    try:
        sheet = xlrd.open_workbook(str(workbook)).sheet_by_index(0)
    except (OSError, IndexError, xlrd.biffh.XLRDError) as exc:
        raise ConfigurationError(
            "Unable to read ISO climate workbook '{}': {}".format(
                workbook, exc
            )
        ) from exc

    header = str(sheet.cell_value(1, 5))
    required_rows = ISO_DATA_START_ROW_ZERO_BASED + EXPECTED_ANNUAL_HOURS
    if sheet.nrows < required_rows or sheet.ncols < 16:
        raise ConfigurationError(
            "ISO climate workbook has unexpected dimensions {}x{}".format(
                sheet.nrows, sheet.ncols
            )
        )

    iso_rows: Sequence[Sequence[float]] = [
        [float(sheet.cell_value(row, column)) for column in range(16)]
        for row in range(
            ISO_DATA_START_ROW_ZERO_BASED,
            ISO_DATA_START_ROW_ZERO_BASED + EXPECTED_ANNUAL_HOURS,
        )
    ]
    paired_count = min(len(records), len(iso_rows))
    timestamp_mismatches = [
        index + 1
        for index, (record, row) in enumerate(
            zip(records[:paired_count], iso_rows[:paired_count])
        )
        if (
            record.month != int(row[1])
            or record.hour_ending != int(row[4])
        )
    ]
    dry_bulb_max_difference = _maximum_absolute_difference(
        (record.dry_bulb_c for record in records[:paired_count]),
        (row[5] for row in iso_rows[:paired_count]),
    )
    wind_max_difference = _maximum_absolute_difference(
        (record.wind_speed_m_s for record in records[:paired_count]),
        (row[14] for row in iso_rows[:paired_count]),
    )

    raw_ghi_pairs = [
        (record.global_horizontal_w_m2, row[13])
        for record, row in zip(records[:paired_count], iso_rows[:paired_count])
        if record.global_horizontal_w_m2 is not None
    ]
    ghi_max_difference = _maximum_absolute_difference(
        (float(pair[0]) for pair in raw_ghi_pairs),
        (float(pair[1]) for pair in raw_ghi_pairs),
    )
    ghi_mean_difference = (
        sum(abs(float(left) - float(right)) for left, right in raw_ghi_pairs)
        / len(raw_ghi_pairs)
        if raw_ghi_pairs
        else None
    )

    controls = {
        "workbook_declares_drycold_tmy_source": {
            "status": "PASS" if "DRYCOLD.TMY" in header.upper() else "FAIL",
            "observed": header,
        },
        "annual_record_count": {
            "status": (
                "PASS"
                if len(records) == EXPECTED_ANNUAL_HOURS
                else "FAIL"
            ),
            "expected": EXPECTED_ANNUAL_HOURS,
            "observed": len(records),
        },
        "calendar_alignment": {
            "status": "PASS" if not timestamp_mismatches else "FAIL",
            "mismatch_count": len(timestamp_mismatches),
            "first_mismatch_hours": timestamp_mismatches[:10],
        },
        "dry_bulb_identity": {
            "status": (
                "PASS"
                if dry_bulb_max_difference <= tolerance
                else "FAIL"
            ),
            "maximum_absolute_difference_c": dry_bulb_max_difference,
        },
        "wind_speed_identity": {
            "status": (
                "PASS" if wind_max_difference <= tolerance else "FAIL"
            ),
            "maximum_absolute_difference_m_s": wind_max_difference,
        },
        "solar_series_relationship": {
            "status": "INFORMATION",
            "raw_tmy1_vs_iso_converted_ghi_maximum_absolute_difference_w_m2": (
                ghi_max_difference
            ),
            "raw_tmy1_vs_iso_converted_ghi_mean_absolute_difference_w_m2": (
                ghi_mean_difference
            ),
            "interpretation": (
                "No raw-value identity is expected: the workbook header says "
                "the climate was converted according to draft ISO/FDIS "
                "52010-1. The converted directional irradiances remain the "
                "authoritative inputs for calculation paths that require them."
            ),
        },
    }
    identity_passed = all(
        control["status"] == "PASS"
        for control_id, control in controls.items()
        if control_id != "solar_series_relationship"
    )
    payload: Dict[str, Any] = {
        "schema_version": "1.0",
        "status": "PASS" if identity_passed else "FAIL",
        "purpose": (
            "Source-identity verification only; this is not a SIA 4010 "
            "compliance result."
        ),
        "source_identity_supported": identity_passed,
        "compliance_claim_allowed": False,
        "weather": {
            "path": str(tmy),
            "sha256": sha256_file(tmy),
            "format": "NOAA_TMY1_FIXED_WIDTH",
            "station_ids": sorted(
                {record.station_id for record in records}
            ),
        },
        "iso_climate_workbook": {
            "path": str(workbook),
            "sha256": sha256_file(workbook),
            "sheet_name": sheet.name,
            "header": header,
            "initialization_hours_excluded": ISO_INITIALIZATION_HOURS,
            "annual_data_start_excel_row": (
                ISO_DATA_START_ROW_ZERO_BASED + 1
            ),
        },
        "controls": controls,
        "limitations": [
            (
                "The public TMY1 file is retained as reference evidence; "
                "acquisition provenance must be approved before certification."
            ),
            (
                "IESVE readability and the weather actually recorded in the "
                "APS file require separate runtime verification."
            ),
            (
                "This audit does not establish the normative identity of all "
                "Case 600 construction or simulation settings."
            ),
        ],
    }
    if report_path is not None:
        _write_json(Path(report_path), payload)
    return payload

