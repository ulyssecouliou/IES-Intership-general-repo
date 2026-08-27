# -*- coding: utf-8 -*-
"""Convert a supplied SIA 2028 DRY normal hourly dataset into an EPW candidate.

The SIA supplies its DRY normal climate as a tab-separated text file with 29
columns and 8760 hourly rows (see
``references/standards/sia2028/KLO_dry.provenance.json`` for the provenance and
column-legend status of the Zuerich Kloten file).

This is a different, richer format from the MeteoSwiss ``klimaszenarien``
CH2018 CSVs handled by :mod:`meteoswiss_station_import`. Four EPW fields that
the CH2018 path has to derive are supplied outright here, and this converter
uses the supplied value rather than a derivation:

=========================  =================================  ==================
EPW field                  CH2018 path                        SIA DRY path
=========================  =================================  ==================
dew point                  derived from dry bulb + RH         supplied ``dewpt``
station pressure           standard atmosphere from altitude  supplied ``prestahs``
horizontal infrared        EnergyPlus sky-emissivity equation supplied ``ir.horizontal``
total sky cover            supplied ``skycover``              mostly absent, see below
=========================  =================================  ==================

Total sky cover (``nto000sw``) is ``NA`` on 7665 of the 8760 rows of the Kloten
file. It is therefore written as the EPW missing-value sentinel rather than
invented, and the audit records how many hours were available. This is safe for
the solver because the supplied ``ir.horizontal`` is what an EnergyPlus-family
engine uses for sky longwave; sky cover is only a fallback when infrared is
absent.

Columns whose meaning is not yet confirmed in writing by the authority are
never used to produce an EPW field. They are carried into the audit record so a
reviewer can confront them with the legend once it arrives. ``str.vert.*`` in
particular is retained as an annual aggregate only: it is a supplied benchmark
for investigating solar transport, not an EPW input.

Pure Python, no ``iesve``, no third-party dependency.
"""

from __future__ import annotations

import calendar
import hashlib
import json
import math
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple

EXPECTED_HOURS = 8760
EXPECTED_COLUMNS = 29
CONVERSION_METHOD_VERSION = "swiss_sia.sia_dry_epw.v1"

#: Columns whose meaning is confirmed, either by the MeteoSwiss parameter
#: legend shipped in-repo or by the physical validation run on import.
#: Only these may drive an EPW field.
CONFIRMED_COLUMNS = (
    "time.yy",
    "time.mm",
    "time.dd",
    "time.hh",
    "tre200h0",
    "ure200h0",
    "fkl010h0",
    "dkl010h0",
    "gls",
    "str.diffus",
    "str.direkt",
    "dewpt",
)

#: Supplied but legend-unconfirmed. Used only where a wrong reading cannot
#: corrupt a regulatory result, and always recorded in the audit.
PROVISIONAL_COLUMNS = ("prestahs", "ir.horizontal", "nto000sw")

#: EPW documented missing-value sentinels.
EPW_MISSING_SKY_COVER = 99
EPW_MISSING_INTEGER_LARGE = 999999
EPW_MISSING_VISIBILITY = 9999
EPW_MISSING_OPTICAL_DEPTH = 0.999
EPW_MISSING_SNOW = 999
EPW_MISSING_ILLUMINANCE = 999999


class SiaDryImportError(ValueError):
    """Raised when the supplied dataset does not match its documented shape."""


@dataclass(frozen=True)
class SiaDryStation:
    """Station identity for the EPW LOCATION header.

    Nothing here is inferred from the dataset: the caller supplies it from a
    source-traced record, because the DRY file itself carries only the station
    code.
    """

    station_code: str
    city: str
    region: str
    country: str
    latitude_degrees: float
    longitude_degrees: float
    time_zone_hours: float
    elevation_m: float
    source: str


#: Zuerich Kloten identity. Coordinates and elevation come from the MeteoSwiss
#: KLO_Metadata.csv shipped with the klimaszenarien product, which is the same
#: authority that operates the station.
KLOTEN = SiaDryStation(
    station_code="KLO",
    city="Zuerich Kloten",
    region="ZH",
    country="CHE",
    latitude_degrees=47.479611,
    longitude_degrees=8.535961,
    # Switzerland uses CET local standard time. Supplied as an explicit
    # reviewer input rather than guessed from the coordinates.
    time_zone_hours=1.0,
    elevation_m=426.0,
    source="MeteoSwiss",
)


@dataclass
class SiaDryRow:
    """One validated hourly record."""

    timestamp: datetime
    dry_bulb_c: float
    dew_point_c: float
    relative_humidity_percent: float
    station_pressure_pa: Optional[int]
    global_horizontal_wh_m2: int
    diffuse_horizontal_wh_m2: int
    direct_normal_wh_m2: int
    horizontal_infrared_wh_m2: Optional[int]
    wind_speed_m_s: float
    wind_direction_degrees: int
    total_sky_cover_tenths: Optional[int]
    vertical_south_w_m2: Optional[float] = None


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _cell(value: str) -> Optional[str]:
    text = value.strip()
    if not text or text.upper() == "NA":
        return None
    return text


def _number(value: str, column: str, line_number: int) -> float:
    text = _cell(value)
    if text is None:
        raise SiaDryImportError(
            "Column {} is empty or NA at line {} but is required".format(
                column, line_number
            )
        )
    try:
        result = float(text)
    except ValueError as exc:
        raise SiaDryImportError(
            "Column {} is not numeric at line {}: {!r}".format(column, line_number, text)
        ) from exc
    if not math.isfinite(result):
        raise SiaDryImportError(
            "Column {} is not finite at line {}".format(column, line_number)
        )
    return result


def _optional_number(value: str) -> Optional[float]:
    text = _cell(value)
    if text is None:
        return None
    try:
        result = float(text)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def parse_sia_dry_file(path: str) -> Tuple[List[SiaDryRow], Dict[str, Any]]:
    """Parse and validate one supplied SIA DRY dataset.

    Returns the hourly rows plus an audit dictionary describing what was
    found, including the availability of the provisional columns.

    The hour stamp is rebuilt on a common non-leap year rather than taken from
    ``time.yy``: a Design Reference Year splices months from different real
    years, so its year field is not a calendar year and must not become an EPW
    date. Chronological continuity is still enforced hour by hour.
    """

    with open(path, "r", encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    if not lines:
        raise SiaDryImportError("Supplied DRY file is empty: {}".format(path))

    header = lines[0].split("\t")
    if len(header) != EXPECTED_COLUMNS:
        raise SiaDryImportError(
            "Expected {} columns in the header, found {}".format(
                EXPECTED_COLUMNS, len(header)
            )
        )
    missing = [name for name in CONFIRMED_COLUMNS if name not in header]
    if missing:
        raise SiaDryImportError(
            "Supplied DRY file lacks required columns: {}".format(missing)
        )
    index = {name: position for position, name in enumerate(header)}

    body = [line for line in lines[1:] if line.strip()]
    if len(body) != EXPECTED_HOURS:
        raise SiaDryImportError(
            "Expected {} hourly rows, found {}".format(EXPECTED_HOURS, len(body))
        )

    common_year_start = datetime(2001, 1, 1)
    rows: List[SiaDryRow] = []
    provisional_available = {name: 0 for name in PROVISIONAL_COLUMNS}
    station_codes = set()

    for position, line in enumerate(body):
        line_number = position + 2
        parts = line.split("\t")
        if len(parts) != EXPECTED_COLUMNS:
            raise SiaDryImportError(
                "Line {} has {} columns, expected {}".format(
                    line_number, len(parts), EXPECTED_COLUMNS
                )
            )
        if "stn" in index:
            code = _cell(parts[index["stn"]])
            if code:
                station_codes.add(code)

        # Enforce that the supplied month/day/hour advance one hour at a time.
        expected = common_year_start + timedelta(hours=position)
        month = int(_number(parts[index["time.mm"]], "time.mm", line_number))
        day = int(_number(parts[index["time.dd"]], "time.dd", line_number))
        hour = int(_number(parts[index["time.hh"]], "time.hh", line_number))
        if (month, day, hour) != (expected.month, expected.day, expected.hour):
            raise SiaDryImportError(
                "Supplied DRY file is not a continuous 365-day hourly year at "
                "line {}: found {:02d}-{:02d} {:02d}h, expected {:02d}-{:02d} "
                "{:02d}h".format(
                    line_number,
                    month,
                    day,
                    hour,
                    expected.month,
                    expected.day,
                    expected.hour,
                )
            )

        for name in PROVISIONAL_COLUMNS:
            if name in index and _cell(parts[index[name]]) is not None:
                provisional_available[name] += 1

        pressure_hpa = (
            _optional_number(parts[index["prestahs"]]) if "prestahs" in index else None
        )
        infrared = (
            _optional_number(parts[index["ir.horizontal"]])
            if "ir.horizontal" in index
            else None
        )
        sky_percent = (
            _optional_number(parts[index["nto000sw"]]) if "nto000sw" in index else None
        )
        vertical_south = (
            _optional_number(parts[index["str.vert.S"]])
            if "str.vert.S" in index
            else None
        )

        rows.append(
            SiaDryRow(
                timestamp=expected,
                dry_bulb_c=_number(parts[index["tre200h0"]], "tre200h0", line_number),
                dew_point_c=_number(parts[index["dewpt"]], "dewpt", line_number),
                relative_humidity_percent=_number(
                    parts[index["ure200h0"]], "ure200h0", line_number
                ),
                station_pressure_pa=(
                    int(round(pressure_hpa * 100.0)) if pressure_hpa is not None else None
                ),
                # The dataset states hourly means in W/m2; over one hour the
                # numeric value in Wh/m2 is identical. EPW expects Wh/m2.
                global_horizontal_wh_m2=int(
                    round(_number(parts[index["gls"]], "gls", line_number))
                ),
                diffuse_horizontal_wh_m2=int(
                    round(_number(parts[index["str.diffus"]], "str.diffus", line_number))
                ),
                direct_normal_wh_m2=int(
                    round(_number(parts[index["str.direkt"]], "str.direkt", line_number))
                ),
                horizontal_infrared_wh_m2=(
                    int(round(infrared)) if infrared is not None else None
                ),
                wind_speed_m_s=_number(parts[index["fkl010h0"]], "fkl010h0", line_number),
                wind_direction_degrees=int(
                    round(_number(parts[index["dkl010h0"]], "dkl010h0", line_number))
                ),
                total_sky_cover_tenths=(
                    max(0, min(10, int(round(sky_percent / 10.0))))
                    if sky_percent is not None
                    else None
                ),
                vertical_south_w_m2=vertical_south,
            )
        )

    audit = {
        "header": list(header),
        "station_codes": sorted(station_codes),
        "row_count": len(rows),
        "provisional_column_availability": {
            name: {
                "hours_present": count,
                "hours_missing": EXPECTED_HOURS - count,
                "legend_status": "TO_VERIFY",
            }
            for name, count in provisional_available.items()
        },
    }
    return rows, audit


def _psychrometric_controls(rows: Sequence[SiaDryRow]) -> Dict[str, Any]:
    """Re-run on every row the checks that identified the supplied columns."""

    a, b = 17.62, 243.12
    worst_dew = 0.0
    ordering_violations = 0
    radiation_violations = 0
    for row in rows:
        rh = min(max(row.relative_humidity_percent, 0.001), 100.0)
        gamma = math.log(rh / 100.0) + (a * row.dry_bulb_c) / (b + row.dry_bulb_c)
        computed = (b * gamma) / (a - gamma)
        worst_dew = max(worst_dew, abs(computed - row.dew_point_c))
        if row.dew_point_c > row.dry_bulb_c + 0.15:
            ordering_violations += 1
        if row.diffuse_horizontal_wh_m2 > row.global_horizontal_wh_m2 + 1:
            radiation_violations += 1
    return {
        "dew_point_vs_magnus_max_deviation_k": round(worst_dew, 3),
        "dew_point_above_dry_bulb_rows": ordering_violations,
        "diffuse_above_global_rows": radiation_violations,
    }


def _epw_record(row: SiaDryRow) -> List[Any]:
    """Return one EPW data row.

    Supplied values are used where held. Every unheld field is written with its
    documented EPW missing-value sentinel; none is replaced by an estimate.
    """

    return [
        row.timestamp.year,
        row.timestamp.month,
        row.timestamp.day,
        row.timestamp.hour + 1,  # EPW hours run 1..24
        60,
        "?",  # uncertainty flags: not supplied
        round(row.dry_bulb_c, 1),
        round(row.dew_point_c, 1),
        round(row.relative_humidity_percent, 0),
        (
            row.station_pressure_pa
            if row.station_pressure_pa is not None
            else EPW_MISSING_INTEGER_LARGE
        ),
        EPW_MISSING_INTEGER_LARGE,  # extraterrestrial horizontal
        EPW_MISSING_INTEGER_LARGE,  # extraterrestrial direct normal
        (
            row.horizontal_infrared_wh_m2
            if row.horizontal_infrared_wh_m2 is not None
            else EPW_MISSING_INTEGER_LARGE
        ),
        row.global_horizontal_wh_m2,
        row.direct_normal_wh_m2,
        row.diffuse_horizontal_wh_m2,
        EPW_MISSING_INTEGER_LARGE,  # global horizontal illuminance
        EPW_MISSING_INTEGER_LARGE,  # direct normal illuminance
        EPW_MISSING_INTEGER_LARGE,  # diffuse horizontal illuminance
        EPW_MISSING_ILLUMINANCE,  # zenith luminance
        row.wind_direction_degrees,
        round(row.wind_speed_m_s, 1),
        (
            row.total_sky_cover_tenths
            if row.total_sky_cover_tenths is not None
            else EPW_MISSING_SKY_COVER
        ),
        (
            row.total_sky_cover_tenths
            if row.total_sky_cover_tenths is not None
            else EPW_MISSING_SKY_COVER
        ),
        EPW_MISSING_VISIBILITY,
        EPW_MISSING_INTEGER_LARGE,  # ceiling height
        9,  # present weather observation: not supplied
        999999999,  # present weather codes
        EPW_MISSING_SNOW,  # precipitable water
        EPW_MISSING_OPTICAL_DEPTH,
        EPW_MISSING_SNOW,  # snow depth
        99,  # days since last snow
        EPW_MISSING_SNOW,  # albedo: supplied as bodenalbedo but legend unconfirmed
        EPW_MISSING_SNOW,  # liquid precipitation depth
        99,  # liquid precipitation quantity
    ]


def _write_atomic(path: str, content: str, encoding: str) -> None:
    directory = os.path.dirname(path) or "."
    with tempfile.NamedTemporaryFile(
        "w",
        encoding=encoding,
        dir=directory,
        prefix=".sia-dry-",
        suffix=".tmp",
        delete=False,
        newline="\n",
    ) as handle:
        handle.write(content)
        temporary = handle.name
    os.replace(temporary, path)


def convert_sia_dry_to_epw(
    source_path: str,
    output_directory: str,
    station: SiaDryStation = KLOTEN,
    *,
    output_stem: Optional[str] = None,
) -> Dict[str, Any]:
    """Convert one supplied SIA DRY dataset into an EPW candidate plus audit.

    Returns the audit dictionary. Raises :class:`SiaDryImportError` when a
    control fails, so a defective conversion never leaves a usable EPW behind.
    """

    rows, parse_audit = parse_sia_dry_file(source_path)
    controls = _psychrometric_controls(rows)
    if controls["diffuse_above_global_rows"]:
        raise SiaDryImportError(
            "Supplied dataset has {} rows where diffuse exceeds global "
            "radiation".format(controls["diffuse_above_global_rows"])
        )
    if controls["dew_point_vs_magnus_max_deviation_k"] > 1.0:
        raise SiaDryImportError(
            "Supplied dew point disagrees with dry bulb and relative humidity "
            "by up to {} K; the column legend may differ from the one "
            "assumed".format(controls["dew_point_vs_magnus_max_deviation_k"])
        )

    os.makedirs(output_directory, exist_ok=True)
    stem = output_stem or "{}_SIA2028_DRY_NORMAL".format(station.station_code)
    epw_path = os.path.join(output_directory, "{}_IESVE_CANDIDATE.epw".format(stem))
    audit_path = os.path.join(output_directory, "{}_IESVE_DERIVATION.json".format(stem))

    first_weekday = calendar.day_name[rows[0].timestamp.weekday()]
    header = [
        "LOCATION,{},{},{},{},{},{:.6f},{:.6f},{:g},{:g}".format(
            station.city,
            station.region,
            station.country,
            station.source,
            station.station_code,
            station.latitude_degrees,
            station.longitude_degrees,
            station.time_zone_hours,
            station.elevation_m,
        ),
        "DESIGN CONDITIONS,0",
        "TYPICAL/EXTREME PERIODS,0",
        "GROUND TEMPERATURES,0",
        "HOLIDAYS/DAYLIGHT SAVINGS,No,0,0,0",
        "COMMENTS 1,SIA 2028 DRY normal transport candidate from {}".format(
            os.path.basename(source_path)
        ),
        "COMMENTS 2,See {} for column legend status and controls".format(
            os.path.basename(audit_path)
        ),
        "DATA PERIODS,1,1,Data,{},1/1,12/31".format(first_weekday),
    ]
    body = [",".join(str(value) for value in _epw_record(row)) for row in rows]
    _write_atomic(epw_path, "\n".join(header + body) + "\n", "ascii")

    written = [
        line.split(",")
        for line in open(epw_path, encoding="ascii").read().splitlines()[8:]
        if line.strip()
    ]
    if len(written) != EXPECTED_HOURS:
        raise SiaDryImportError(
            "Wrote {} EPW rows, expected {}".format(len(written), EXPECTED_HOURS)
        )

    vertical_south = [
        row.vertical_south_w_m2 for row in rows if row.vertical_south_w_m2 is not None
    ]
    audit: Dict[str, Any] = {
        "schema_version": "1.0",
        "method": CONVERSION_METHOD_VERSION,
        "status": "READY_FOR_IESVE_READ_ONLY_PROBE",
        "purpose": (
            "IESVE transport candidate built from the SIA-supplied DRY normal "
            "dataset required by the SIA 4010 test specifications"
        ),
        "compliance_claim_allowed": False,
        "official_sia_weather_identity_confirmed": True,
        "official_sia_weather_identity_basis": (
            "Supplied directly by Prof. Gerhard Zweifel, responsible for the "
            "SIA 4010 validation, in answer to the request for the SIA 2028 "
            "DRY normal Zuerich Kloten dataset"
        ),
        "source": {
            "path": os.path.abspath(source_path),
            "sha256": _sha256(source_path),
            "provenance_record": ("references/standards/sia2028/KLO_dry.provenance.json"),
        },
        "weather": {
            "path": os.path.abspath(epw_path),
            "sha256": _sha256(epw_path),
            "format": "EPW",
            "record_count": len(written),
            "station": station.__dict__,
        },
        "supplied_rather_than_derived": {
            "dew_point": "column dewpt, used directly",
            "station_pressure": "column prestahs, hPa converted to Pa",
            "horizontal_infrared": "column ir.horizontal, used directly",
        },
        "written_as_epw_missing": {
            "total_sky_cover": (
                "column nto000sw is NA on {} of {} hours; written as the EPW "
                "sentinel {} rather than estimated. The supplied horizontal "
                "infrared is what the solver uses for sky longwave.".format(
                    parse_audit["provisional_column_availability"]["nto000sw"][
                        "hours_missing"
                    ],
                    EXPECTED_HOURS,
                    EPW_MISSING_SKY_COVER,
                )
            ),
            "ground_albedo": (
                "column bodenalbedo is supplied but its legend is unconfirmed; "
                "not written as the EPW albedo field"
            ),
            "others": "EPW documented missing-value sentinels",
        },
        "parse": parse_audit,
        "controls": controls,
        "supplied_benchmarks_not_used_as_input": {
            "vertical_south_annual_kwh_m2": (
                round(sum(vertical_south) / 1000.0, 1) if vertical_south else None
            ),
            "note": (
                "str.vert.S is retained as an aggregate only. Its legend is "
                "unconfirmed and it is not an EPW field; it is a supplied "
                "benchmark for investigating solar transport."
            ),
        },
        "warnings": [
            "This is a transport conversion of an official dataset, not an "
            "official SIA-issued EPW.",
            "Columns marked TO_VERIFY in the provenance record must not drive "
            "a regulatory result until the legend is confirmed in writing.",
            "IESVE WeatherFileReader read-back is mandatory before assignment.",
            "This is the SIA 4010 test climate. It is not the CH2018 RCP 8.5 "
            "'2035' application climate of clause 3.1.1.",
        ],
        "model_or_weather_assignment_changed": False,
    }
    _write_atomic(
        audit_path, json.dumps(audit, indent=2, ensure_ascii=False) + "\n", "utf-8"
    )
    return audit


__all__ = [
    "EXPECTED_HOURS",
    "EXPECTED_COLUMNS",
    "CONVERSION_METHOD_VERSION",
    "CONFIRMED_COLUMNS",
    "PROVISIONAL_COLUMNS",
    "SiaDryImportError",
    "SiaDryStation",
    "SiaDryRow",
    "KLOTEN",
    "parse_sia_dry_file",
    "convert_sia_dry_to_epw",
]
