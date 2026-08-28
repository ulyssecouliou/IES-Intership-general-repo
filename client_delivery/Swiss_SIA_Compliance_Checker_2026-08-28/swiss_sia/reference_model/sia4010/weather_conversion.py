"""Deterministic NOAA TMY1 to EPW transport conversion for IESVE.

IESVE 2025 does not read the historical fixed-width DRYCOLD.TMY source
directly.  This module creates an EPW transport file while preserving the
hourly TMY1 meteorological values.  When TMY1 diffuse horizontal radiation is
missing, it is reconstructed from global horizontal and direct normal
radiation using documented solar geometry at the midpoint of the hour.  The
ISO 52016-1 verification-case boundary condition is also transported through
the EPW horizontal-infrared field: apparent sky temperature is exactly 11 K
below the hourly outdoor dry-bulb temperature.

The conversion is an interoperability step, not a normative SIA result.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union

from ..exceptions import ConfigurationError

PathLike = Union[str, Path]
DENVER_LATITUDE_DEGREES = 39.74
DENVER_LONGITUDE_DEGREES = -104.99
DENVER_TIME_ZONE_HOURS = -7.0
DENVER_ELEVATION_M = 1609.0
EXPECTED_HOURS = 8760
EPW_AUDIT_FILENAME = "DRYCOLD_IESVE_EPW_DERIVATION.json"
APPARENT_SKY_TEMPERATURE_OFFSET_K = 11.0
STEFAN_BOLTZMANN_W_M2_K4 = 5.670374419e-8


@dataclass(frozen=True)
class _RawTmy1:
    """One raw TMY1 hourly record as read from the BESTEST insert."""

    station_id: str
    month: int
    day: int
    hour_ending: int
    dry_bulb_c: float
    dew_point_c: float
    pressure_pa: int
    wind_direction_degrees: int
    wind_speed_m_s: float
    total_cloud_tenths: int
    global_horizontal_w_m2: float
    direct_normal_w_m2: Optional[float]
    diffuse_horizontal_w_m2: Optional[float]


def _sha256(path: Path) -> str:
    """Return the hexadecimal SHA-256 checksum of one file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _parse_tmy1(path: Path) -> List[_RawTmy1]:
    """Parse a TMY1 weather file into its raw hourly records."""

    try:
        lines = path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ConfigurationError(
            "Unable to read TMY1 weather file '{}': {}".format(path, exc)
        ) from exc
    records: List[_RawTmy1] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        if len(line) < 120:
            raise ConfigurationError("TMY1 line {} is too short".format(line_number))
        try:
            global_horizontal = (
                None if line[53] == "9" else max(0.0, float(line[54:58]) / 3.6)
            )
            if global_horizontal is None:
                raise ValueError("global horizontal radiation is missing")
            direct_normal = (
                None if line[23] == "9" else max(0.0, float(line[24:28]) / 3.6)
            )
            diffuse_horizontal = (
                None if line[28] == "9" else max(0.0, float(line[29:33]) / 3.6)
            )
            record = _RawTmy1(
                station_id=line[0:5],
                month=int(line[7:9]),
                day=int(line[9:11]),
                hour_ending=int(line[11:13]),
                dry_bulb_c=float(line[103:107]) / 10.0,
                dew_point_c=float(line[107:111]) / 10.0,
                pressure_pa=int(round(float(line[98:103]) * 10.0)),
                wind_direction_degrees=int(float(line[111:114])),
                wind_speed_m_s=float(line[114:118]) / 10.0,
                total_cloud_tenths=int(float(line[118:120])),
                global_horizontal_w_m2=global_horizontal,
                direct_normal_w_m2=direct_normal,
                diffuse_horizontal_w_m2=diffuse_horizontal,
            )
        except (TypeError, ValueError) as exc:
            raise ConfigurationError(
                "Malformed TMY1 data at line {}: {}".format(line_number, exc)
            ) from exc
        records.append(record)
    return records


def _cosine_solar_zenith(record: _RawTmy1) -> float:
    """Return midpoint-of-hour solar zenith cosine using NOAA equations."""

    hour_start = record.hour_ending - 1
    local_midpoint = datetime(2001, record.month, record.day, hour_start, 30)
    day_of_year = local_midpoint.timetuple().tm_yday
    fractional_hour = local_midpoint.hour + local_midpoint.minute / 60.0
    gamma = 2.0 * math.pi / 365.0 * (day_of_year - 1 + (fractional_hour - 12.0) / 24.0)
    equation_of_time = 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2.0 * gamma)
        - 0.040849 * math.sin(2.0 * gamma)
    )
    declination = (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2.0 * gamma)
        + 0.000907 * math.sin(2.0 * gamma)
        - 0.002697 * math.cos(3.0 * gamma)
        + 0.00148 * math.sin(3.0 * gamma)
    )
    minutes = local_midpoint.hour * 60.0 + local_midpoint.minute
    time_offset = (
        equation_of_time + 4.0 * DENVER_LONGITUDE_DEGREES - 60.0 * DENVER_TIME_ZONE_HOURS
    )
    true_solar_minutes = (minutes + time_offset) % 1440.0
    hour_angle = math.radians(true_solar_minutes / 4.0 - 180.0)
    latitude = math.radians(DENVER_LATITUDE_DEGREES)
    cosine = math.sin(latitude) * math.sin(declination) + math.cos(latitude) * math.cos(
        declination
    ) * math.cos(hour_angle)
    return max(0.0, min(1.0, cosine))


def _relative_humidity(dry_bulb_c: float, dew_point_c: float) -> int:
    """Return clamped integer RH from dry bulb and dew point."""

    def saturation_pressure(temperature_c: float) -> float:
        """Return the saturation vapour pressure in hPa for a temperature in C."""

        return 6.112 * math.exp(17.67 * temperature_c / (temperature_c + 243.5))

    relative = 100.0 * saturation_pressure(dew_point_c) / saturation_pressure(dry_bulb_c)
    return int(round(max(0.0, min(100.0, relative))))


def _solar_components(record: _RawTmy1) -> Tuple[float, float, float]:
    """Return EPW GHI, DNI and DHI without changing the source GHI."""

    ghi = record.global_horizontal_w_m2
    cosine_zenith = _cosine_solar_zenith(record)
    dni = record.direct_normal_w_m2 or 0.0
    if cosine_zenith <= 0.0 or ghi <= 0.0:
        return ghi, 0.0, max(0.0, ghi)
    if record.diffuse_horizontal_w_m2 is not None:
        dhi = record.diffuse_horizontal_w_m2
    else:
        # Energy-balance reconstruction from the two measured TMY1 fields.
        dhi = max(0.0, ghi - dni * cosine_zenith)
    # Measurement/time-convention differences can make DNI*cos(z) exceed GHI.
    # Cap DNI so the EPW components preserve the measured horizontal total.
    maximum_dni = ghi / cosine_zenith if cosine_zenith > 0.0 else 0.0
    dni = min(dni, maximum_dni)
    dhi = max(0.0, ghi - dni * cosine_zenith)
    return ghi, dni, dhi


def _horizontal_infrared_radiation_w_m2(dry_bulb_c: float) -> float:
    """Return long-wave sky radiation for the ISO fixed 11 K sky offset.

    EPW field 13 is the horizontal infrared radiation intensity from the sky.
    Encoding the prescribed apparent sky temperature in that field avoids
    delegating this normative boundary condition to an engine default.
    """

    apparent_sky_temperature_k = (
        float(dry_bulb_c) + 273.15 - APPARENT_SKY_TEMPERATURE_OFFSET_K
    )
    if apparent_sky_temperature_k <= 0.0:
        raise ConfigurationError(
            "Invalid apparent sky temperature derived from dry bulb: "
            "{} degC".format(dry_bulb_c)
        )
    return STEFAN_BOLTZMANN_W_M2_K4 * apparent_sky_temperature_k**4


def _apparent_sky_temperature_c(horizontal_infrared_w_m2: float) -> float:
    """Return apparent sky temperature decoded from EPW field 13."""

    if horizontal_infrared_w_m2 <= 0.0:
        raise ConfigurationError("Horizontal infrared radiation must be positive")
    return (horizontal_infrared_w_m2 / STEFAN_BOLTZMANN_W_M2_K4) ** 0.25 - 273.15


def _epw_line(record: _RawTmy1) -> str:
    """Return one EPW-formatted hourly line for a raw TMY1 record."""

    ghi, dni, dhi = _solar_components(record)
    relative_humidity = _relative_humidity(record.dry_bulb_c, record.dew_point_c)
    horizontal_infrared = _horizontal_infrared_radiation_w_m2(record.dry_bulb_c)
    fields = [
        2001,
        record.month,
        record.day,
        record.hour_ending,
        60,
        "?0?0?0?0?0?0?0?0?0?0?0?0?0?0?0?0?0?0?0?0?0?0",
        "{:.1f}".format(record.dry_bulb_c),
        "{:.1f}".format(record.dew_point_c),
        relative_humidity,
        record.pressure_pa,
        9999,
        9999,
        "{:.3f}".format(horizontal_infrared),
        int(round(ghi)),
        int(round(dni)),
        int(round(dhi)),
        999999,
        999999,
        999999,
        9999,
        (
            record.wind_direction_degrees
            if 0 <= record.wind_direction_degrees <= 360
            else 999
        ),
        "{:.1f}".format(record.wind_speed_m_s),
        record.total_cloud_tenths if 0 <= record.total_cloud_tenths <= 10 else 99,
        99,
        9999,
        99999,
        9,
        999999999,
        999,
        0.999,
        999,
        99,
        999,
        999,
        99,
    ]
    return ",".join(str(field) for field in fields)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write one JSON payload atomically through a temporary file."""

    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def convert_tmy1_to_iesve_epw(
    tmy_path: PathLike,
    epw_path: PathLike,
    audit_path: PathLike,
) -> Dict[str, Any]:
    """Convert, validate and source-trace one DRYCOLD TMY1 file."""

    source = Path(tmy_path).resolve()
    destination = Path(epw_path).resolve()
    audit_destination = Path(audit_path).resolve()
    records = _parse_tmy1(source)
    if len(records) != EXPECTED_HOURS:
        raise ConfigurationError(
            "Expected {} TMY1 hours, found {}".format(EXPECTED_HOURS, len(records))
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    header = [
        ("LOCATION,Denver,Colorado,USA,TMY1-23062,23062," "39.740,-104.990,-7.0,1609.0"),
        "DESIGN CONDITIONS,0",
        "TYPICAL/EXTREME PERIODS,0",
        "GROUND TEMPERATURES,0",
        "HOLIDAYS/DAYLIGHT SAVINGS,No,0,0,0",
        "COMMENTS 1,Derived losslessly where available from DRYCOLD.TMY",
        (
            "COMMENTS 2,DHI reconstructed by hourly solar energy balance; "
            "see DRYCOLD_IESVE_EPW_DERIVATION.json"
        ),
        "DATA PERIODS,1,1,Data,Monday,1/1,12/31",
    ]
    content = "\n".join(header + [_epw_line(record) for record in records])
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(content + "\n", encoding="ascii")
    temporary.replace(destination)

    epw_lines = destination.read_text(encoding="ascii").splitlines()[8:]
    parsed = [line.split(",") for line in epw_lines]
    dry_bulb_difference = max(
        abs(float(fields[6]) - record.dry_bulb_c)
        for fields, record in zip(parsed, records)
    )
    wind_difference = max(
        abs(float(fields[21]) - record.wind_speed_m_s)
        for fields, record in zip(parsed, records)
    )
    ghi_rounding_difference = max(
        abs(float(fields[13]) - record.global_horizontal_w_m2)
        for fields, record in zip(parsed, records)
    )
    apparent_sky_offset_difference = max(
        abs(
            (float(fields[6]) - _apparent_sky_temperature_c(float(fields[12])))
            - APPARENT_SKY_TEMPERATURE_OFFSET_K
        )
        for fields in parsed
    )
    audit: Dict[str, Any] = {
        "schema_version": "1.0",
        "status": "PASS",
        "purpose": (
            "IESVE-compatible transport conversion; not a normative SIA "
            "compliance result."
        ),
        "source_identity_supported": True,
        "compliance_claim_allowed": False,
        "weather": {
            "path": str(destination),
            "sha256": _sha256(destination),
            "format": "EPW",
            "record_count": len(parsed),
        },
        "source_tmy1": {
            "path": str(source),
            "sha256": _sha256(source),
            "format": "NOAA_TMY1_FIXED_WIDTH",
        },
        "conversion": {
            "location": {
                "latitude_degrees": DENVER_LATITUDE_DEGREES,
                "longitude_degrees": DENVER_LONGITUDE_DEGREES,
                "time_zone_hours": DENVER_TIME_ZONE_HOURS,
                "elevation_m": DENVER_ELEVATION_M,
            },
            "hour_interpretation": "TMY1 hour-ending; solar geometry at midpoint",
            "diffuse_radiation_method": (
                "DHI=max(0,GHI-DNI*cos(zenith)); DNI capped to preserve GHI"
            ),
            "apparent_sky_temperature": {
                "method": (
                    "EPW horizontal infrared = Stefan-Boltzmann radiation "
                    "at outdoor dry bulb minus 11 K"
                ),
                "external_air_minus_apparent_sky_temperature_k": (
                    APPARENT_SKY_TEMPERATURE_OFFSET_K
                ),
                "source": "BS EN ISO 52016-1:2017 clause 7.2.2.12",
            },
        },
        "controls": {
            "record_count": {
                "status": "PASS" if len(parsed) == EXPECTED_HOURS else "FAIL",
                "expected": EXPECTED_HOURS,
                "observed": len(parsed),
            },
            "dry_bulb_preserved": {
                "status": "PASS" if dry_bulb_difference == 0.0 else "FAIL",
                "maximum_absolute_difference_c": dry_bulb_difference,
            },
            "wind_speed_preserved": {
                "status": "PASS" if wind_difference == 0.0 else "FAIL",
                "maximum_absolute_difference_m_s": wind_difference,
            },
            "global_horizontal_preserved_with_integer_epw_rounding": {
                "status": "PASS" if ghi_rounding_difference <= 0.5 else "FAIL",
                "maximum_absolute_difference_w_m2": ghi_rounding_difference,
            },
            "fixed_apparent_sky_temperature_offset": {
                "status": ("PASS" if apparent_sky_offset_difference <= 0.1 else "FAIL"),
                "expected_offset_k": APPARENT_SKY_TEMPERATURE_OFFSET_K,
                "maximum_absolute_difference_k": (apparent_sky_offset_difference),
            },
        },
        "limitations": [
            (
                "The TMY1 source lacks diffuse horizontal radiation for this "
                "dataset; DHI is reconstructed for EPW interoperability."
            ),
            (
                "The generated EPW must be opened and read back through "
                "IESVE WeatherFileReader before model mutation."
            ),
            (
                "Official/certification use still requires approval of source "
                "provenance and the SIA-authorized test procedure."
            ),
        ],
    }
    if any(control["status"] != "PASS" for control in audit["controls"].values()):
        audit["status"] = "FAIL"
    audit_destination.parent.mkdir(parents=True, exist_ok=True)
    _write_json(audit_destination, audit)
    if audit["status"] != "PASS":
        raise ConfigurationError(
            "Generated EPW failed validation; see {}".format(audit_destination)
        )
    return audit
