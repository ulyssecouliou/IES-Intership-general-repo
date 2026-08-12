"""Source-traced client weather conversion to a complete EPW transport file.

The converter repairs structural transport defects without treating the result
as an official SIA weather dataset. Primary hourly variables come from the
client CSV, station pressure and uncertainty flags are inherited from the
adjacent client EPW, and every derived or missing field is recorded in JSON.
"""

from __future__ import annotations

import calendar
import csv
import hashlib
import io
import json
import math
import unicodedata
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple, Union

from .exceptions import ConfigurationError


PathLike = Union[str, Path]
EXPECTED_HOURS = 8760
EXPECTED_EPW_FIELDS = 35
SOURCE_CSV_NAME = "SMA_2035_RCP85_DRY.csv"
SOURCE_EPW_NAME = "SMA_2035_RCP85_DRY.epw"
OUTPUT_EPW_NAME = "SMA_2035_RCP85_DRY_IESVE_CANDIDATE.epw"
OUTPUT_AUDIT_NAME = "SMA_2035_RCP85_DRY_IESVE_DERIVATION.json"
CONVERSION_METHOD_VERSION = "swiss_sia.client_weather_epw.v1"

REQUIRED_CSV_COLUMNS = (
    "time.yy",
    "time.mm",
    "time.dd",
    "time.hh",
    "tre200h0",
    "ure200h0",
    "fkl010h0",
    "dkl010h0",
    "skycover",
    "gls",
    "str.diffus",
    "str.direkt",
)


@dataclass(frozen=True)
class WeatherLocation:
    """Client weather station identity parsed from the source EPW header."""

    city: str
    region: str
    country: str
    source: str
    station_id: str
    latitude_degrees: float
    longitude_degrees: float
    time_zone_hours: float
    elevation_m: float


@dataclass(frozen=True)
class ClientWeatherRecord:
    """One validated hourly source record and its inherited EPW metadata."""

    timestamp: datetime
    dry_bulb_c: float
    relative_humidity_percent: float
    wind_speed_m_s: float
    wind_direction_degrees: float
    total_sky_cover_percent: float
    global_horizontal_w_m2: float
    diffuse_horizontal_w_m2: float
    direct_normal_w_m2: float
    pressure_pa: float
    source_flags: str


def _sha256_bytes(content: bytes) -> str:
    """Return an uppercase SHA-256 checksum for immutable source bytes."""

    return hashlib.sha256(content).hexdigest().upper()


def _sha256_path(path: Path) -> str:
    """Return an uppercase SHA-256 checksum for one generated file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _decode_text(content: bytes, context: str) -> str:
    """Decode client text deterministically with one documented fallback."""

    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ConfigurationError("Unable to decode {} as UTF-8 or CP1252".format(context))


def _single_zip_entry(archive: zipfile.ZipFile, basename: str) -> bytes:
    """Return one exact-basename ZIP entry and reject ambiguous matches."""

    matches = [
        info
        for info in archive.infolist()
        if not info.is_dir() and Path(info.filename).name == basename
    ]
    if len(matches) != 1:
        raise ConfigurationError(
            "Expected exactly one ZIP entry named '{}', found {}".format(
                basename, len(matches)
            )
        )
    return archive.read(matches[0])


def _float(row: Mapping[str, str], key: str, line_number: int) -> float:
    """Read one finite source number with a field-specific error."""

    try:
        value = float(row[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise ConfigurationError(
            "Invalid {} at client CSV line {}".format(key, line_number)
        ) from exc
    if not math.isfinite(value):
        raise ConfigurationError(
            "Non-finite {} at client CSV line {}".format(key, line_number)
        )
    return value


def _parse_location(epw_text: str) -> WeatherLocation:
    """Parse and validate the EPW LOCATION header supplied by the client."""

    lines = epw_text.splitlines()
    if not lines:
        raise ConfigurationError("Client EPW is empty")
    fields = lines[0].rstrip(",").split(",")
    if len(fields) != 10 or fields[0].strip().upper() != "LOCATION":
        raise ConfigurationError("Client EPW LOCATION header is malformed")
    try:
        location = WeatherLocation(
            city=fields[1].strip(),
            region=fields[2].strip(),
            country=fields[3].strip(),
            source=fields[4].strip(),
            station_id=fields[5].strip(),
            latitude_degrees=float(fields[6]),
            longitude_degrees=float(fields[7]),
            time_zone_hours=float(fields[8]),
            elevation_m=float(fields[9]),
        )
    except ValueError as exc:
        raise ConfigurationError("Client EPW LOCATION numbers are malformed") from exc
    if not -90.0 <= location.latitude_degrees <= 90.0:
        raise ConfigurationError("Client weather latitude is outside -90..90")
    if not -180.0 <= location.longitude_degrees <= 180.0:
        raise ConfigurationError("Client weather longitude is outside -180..180")
    if not -12.0 <= location.time_zone_hours <= 12.0:
        raise ConfigurationError("Client weather time zone is outside -12..12")
    return location


def _parse_client_epw_transport(
    epw_text: str,
) -> Tuple[List[Tuple[datetime, float, str]], Dict[str, Any]]:
    """Read pressure and flags while auditing structural EPW defects."""

    lines = [line for line in epw_text.splitlines()[8:] if line.strip()]
    inherited: List[Tuple[datetime, float, str]] = []
    field_counts: Dict[int, int] = {}
    ghi_values = set()
    dew_point_values = set()
    for offset, line in enumerate(lines, start=9):
        fields = line.split(",")
        field_counts[len(fields)] = field_counts.get(len(fields), 0) + 1
        if len(fields) < 10:
            raise ConfigurationError(
                "Client EPW line {} has fewer than 10 fields".format(offset)
            )
        try:
            timestamp = datetime(
                int(fields[0]),
                int(fields[1]),
                int(fields[2]),
            ) + timedelta(hours=int(fields[3]) - 1)
            pressure = float(fields[9])
        except (TypeError, ValueError) as exc:
            raise ConfigurationError(
                "Client EPW timestamp/pressure is malformed at line {}".format(offset)
            ) from exc
        if not 31000.0 < pressure < 120000.0:
            raise ConfigurationError(
                "Client EPW pressure is outside the EPW range at line {}".format(offset)
            )
        inherited.append((timestamp, pressure, fields[5].strip() or "?"))
        if len(fields) > 13:
            ghi_values.add(fields[13])
        if len(fields) > 7:
            dew_point_values.add(fields[7])
    defect_summary = {
        "record_count": len(lines),
        "field_count_distribution": {
            str(key): value for key, value in sorted(field_counts.items())
        },
        "expected_field_count": EXPECTED_EPW_FIELDS,
        "all_global_horizontal_values_identical": len(ghi_values) == 1,
        "global_horizontal_sample": sorted(ghi_values)[:3],
        "all_dew_point_values_identical": len(dew_point_values) == 1,
        "dew_point_sample": sorted(dew_point_values)[:3],
    }
    return inherited, defect_summary


def _parse_client_csv(csv_text: str) -> List[Dict[str, str]]:
    """Parse the client CSV and enforce its documented source schema."""

    reader = csv.DictReader(io.StringIO(csv_text))
    fieldnames = tuple(reader.fieldnames or ())
    missing = sorted(set(REQUIRED_CSV_COLUMNS) - set(fieldnames))
    if missing:
        raise ConfigurationError(
            "Client CSV is missing required columns: {}".format(missing)
        )
    rows = [dict(row) for row in reader if any(str(value).strip() for value in row.values())]
    if len(rows) != EXPECTED_HOURS:
        raise ConfigurationError(
            "Client CSV contains {} hours; expected {}".format(
                len(rows), EXPECTED_HOURS
            )
        )
    return rows


def _validate_range(
    value: float,
    minimum: float,
    maximum: float,
    field: str,
    line_number: int,
) -> None:
    """Reject an hourly source value outside its physical/EPW bounds."""

    if not minimum <= value <= maximum:
        raise ConfigurationError(
            "{}={} outside {}..{} at client CSV line {}".format(
                field, value, minimum, maximum, line_number
            )
        )


def _combine_records(
    csv_rows: Sequence[Mapping[str, str]],
    inherited_epw: Sequence[Tuple[datetime, float, str]],
) -> List[ClientWeatherRecord]:
    """Bind CSV variables to same-hour pressure and flags from the client EPW."""

    if len(csv_rows) != len(inherited_epw):
        raise ConfigurationError("Client CSV and EPW hourly counts differ")
    records: List[ClientWeatherRecord] = []
    first_year = int(_float(csv_rows[0], "time.yy", 2))
    expected_timestamp = datetime(first_year, 1, 1)
    for index, (row, inherited) in enumerate(zip(csv_rows, inherited_epw)):
        line_number = index + 2
        try:
            timestamp = datetime(
                int(_float(row, "time.yy", line_number)),
                int(_float(row, "time.mm", line_number)),
                int(_float(row, "time.dd", line_number)),
                int(_float(row, "time.hh", line_number)),
            )
        except ValueError as exc:
            raise ConfigurationError(
                "Invalid client CSV date at line {}".format(line_number)
            ) from exc
        if timestamp != expected_timestamp:
            raise ConfigurationError(
                "Client CSV is not a continuous hourly year at line {}: "
                "expected {}, observed {}".format(
                    line_number, expected_timestamp.isoformat(), timestamp.isoformat()
                )
            )
        inherited_timestamp, pressure, source_flags = inherited
        if inherited_timestamp != timestamp:
            raise ConfigurationError(
                "Client CSV/EPW timestamp mismatch at {}".format(
                    timestamp.isoformat()
                )
            )
        dry_bulb = _float(row, "tre200h0", line_number)
        relative_humidity = _float(row, "ure200h0", line_number)
        wind_speed = _float(row, "fkl010h0", line_number)
        wind_direction = _float(row, "dkl010h0", line_number)
        sky_cover = _float(row, "skycover", line_number)
        ghi = _float(row, "gls", line_number)
        dhi = _float(row, "str.diffus", line_number)
        dni = _float(row, "str.direkt", line_number)
        for value, bounds, field in (
            (dry_bulb, (-70.0, 70.0), "tre200h0"),
            (relative_humidity, (0.0, 100.0), "ure200h0"),
            (wind_speed, (0.0, 40.0), "fkl010h0"),
            (wind_direction, (0.0, 360.0), "dkl010h0"),
            (sky_cover, (0.0, 100.0), "skycover"),
            (ghi, (0.0, 2000.0), "gls"),
            (dhi, (0.0, 2000.0), "str.diffus"),
            (dni, (0.0, 2000.0), "str.direkt"),
        ):
            _validate_range(value, bounds[0], bounds[1], field, line_number)
        if dhi > ghi + 0.01:
            raise ConfigurationError(
                "Diffuse horizontal exceeds global horizontal at line {}".format(
                    line_number
                )
            )
        records.append(
            ClientWeatherRecord(
                timestamp=timestamp,
                dry_bulb_c=dry_bulb,
                relative_humidity_percent=relative_humidity,
                wind_speed_m_s=wind_speed,
                wind_direction_degrees=wind_direction,
                total_sky_cover_percent=sky_cover,
                global_horizontal_w_m2=ghi,
                diffuse_horizontal_w_m2=dhi,
                direct_normal_w_m2=dni,
                pressure_pa=pressure,
                source_flags=source_flags,
            )
        )
        expected_timestamp += timedelta(hours=1)
    return records


def _dew_point_c(dry_bulb_c: float, relative_humidity_percent: float) -> float:
    """Return dew point using the NOAA MADIS temperature/RH equations."""

    if relative_humidity_percent <= 0.0:
        raise ConfigurationError("Dew point cannot be derived from zero RH")
    saturation = 6.1365 * math.exp(
        17.502 * dry_bulb_c / (240.97 + dry_bulb_c)
    )
    vapour_pressure = relative_humidity_percent / 100.0 * saturation
    ratio = math.log(vapour_pressure / 6.1365)
    dew_point = 240.97 * ratio / (17.502 - ratio)
    return min(dry_bulb_c, dew_point)


def _sky_cover_tenths(percent: float) -> int:
    """Convert source percent cloud cover to nearest EPW tenth."""

    return max(0, min(10, int(math.floor(percent / 10.0 + 0.5))))


def _horizontal_infrared_w_m2(record: ClientWeatherRecord) -> float:
    """Derive horizontal infrared using the EnergyPlus EPW equation."""

    dew_point_k = _dew_point_c(
        record.dry_bulb_c, record.relative_humidity_percent
    ) + 273.15
    dry_bulb_k = record.dry_bulb_c + 273.15
    opaque_proxy = float(_sky_cover_tenths(record.total_sky_cover_percent))
    emissivity = (
        0.787 + 0.764 * math.log(dew_point_k / 273.0)
    ) * (
        1.0
        + 0.0224 * opaque_proxy
        - 0.0035 * opaque_proxy**2
        + 0.00028 * opaque_proxy**3
    )
    return emissivity * 5.6697e-8 * dry_bulb_k**4


def _ascii(value: str) -> str:
    """Return an IESVE-safe ASCII station label without changing audit identity."""

    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")


def _epw_record(record: ClientWeatherRecord) -> List[Union[str, int, float]]:
    """Map one source record to the complete 35-field EPW data contract."""

    cloud_tenths = _sky_cover_tenths(record.total_sky_cover_percent)
    fields: List[Union[str, int, float]] = [
        record.timestamp.year,
        record.timestamp.month,
        record.timestamp.day,
        record.timestamp.hour + 1,
        60,
        record.source_flags,
        "{:.1f}".format(record.dry_bulb_c),
        "{:.1f}".format(
            _dew_point_c(record.dry_bulb_c, record.relative_humidity_percent)
        ),
        int(round(record.relative_humidity_percent)),
        int(round(record.pressure_pa)),
        9999,
        9999,
        int(round(_horizontal_infrared_w_m2(record))),
        int(round(record.global_horizontal_w_m2)),
        int(round(record.direct_normal_w_m2)),
        int(round(record.diffuse_horizontal_w_m2)),
        999999,
        999999,
        999999,
        9999,
        int(round(record.wind_direction_degrees)),
        "{:.1f}".format(record.wind_speed_m_s),
        cloud_tenths,
        cloud_tenths,
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
    if len(fields) != EXPECTED_EPW_FIELDS:
        raise AssertionError("Internal EPW mapping does not contain 35 fields")
    return fields


def _write_atomic(path: Path, content: str, encoding: str) -> None:
    """Write a generated artifact atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding=encoding, newline="\n")
    temporary.replace(path)


def _control(status: bool, expected: Any, observed: Any) -> Dict[str, Any]:
    """Return one machine-readable PASS/FAIL control."""

    return {
        "status": "PASS" if status else "FAIL",
        "expected": expected,
        "observed": observed,
    }


def convert_client_weather_archive(
    archive_path: PathLike,
    output_directory: PathLike,
) -> Dict[str, Any]:
    """Create a complete, audited EPW candidate from the supplied client ZIP."""

    archive_source = Path(archive_path).resolve()
    output_root = Path(output_directory).resolve()
    if not archive_source.is_file():
        raise ConfigurationError("Client archive does not exist: {}".format(archive_source))
    archive_bytes = archive_source.read_bytes()
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as archive:
            csv_bytes = _single_zip_entry(archive, SOURCE_CSV_NAME)
            client_epw_bytes = _single_zip_entry(archive, SOURCE_EPW_NAME)
    except (OSError, zipfile.BadZipFile) as exc:
        raise ConfigurationError("Unable to read client weather archive") from exc

    csv_text = _decode_text(csv_bytes, SOURCE_CSV_NAME)
    client_epw_text = _decode_text(client_epw_bytes, SOURCE_EPW_NAME)
    location = _parse_location(client_epw_text)
    csv_rows = _parse_client_csv(csv_text)
    inherited, original_defects = _parse_client_epw_transport(client_epw_text)
    records = _combine_records(csv_rows, inherited)

    output_root.mkdir(parents=True, exist_ok=True)
    epw_path = output_root / OUTPUT_EPW_NAME
    audit_path = output_root / OUTPUT_AUDIT_NAME
    first_weekday = calendar.day_name[records[0].timestamp.weekday()]
    header = [
        "LOCATION,{},{},{},{},{},{:.6f},{:.6f},{:g},{:g}".format(
            _ascii(location.city),
            _ascii(location.region),
            _ascii(location.country),
            _ascii(location.source) or "CLIENT_DRY",
            _ascii(location.station_id),
            location.latitude_degrees,
            location.longitude_degrees,
            location.time_zone_hours,
            location.elevation_m,
        ),
        "DESIGN CONDITIONS,0",
        "TYPICAL/EXTREME PERIODS,0",
        "GROUND TEMPERATURES,0",
        "HOLIDAYS/DAYLIGHT SAVINGS,No,0,0,0",
        "COMMENTS 1,Client SMA 2035 RCP85 DRY repaired transport candidate",
        "COMMENTS 2,See {} for source mapping limitations and hashes".format(
            OUTPUT_AUDIT_NAME
        ),
        "DATA PERIODS,1,1,Data,{},1/1,12/31".format(first_weekday),
    ]
    epw_rows = [
        ",".join(str(value) for value in _epw_record(record))
        for record in records
    ]
    _write_atomic(epw_path, "\n".join(header + epw_rows) + "\n", "ascii")

    generated_lines = epw_path.read_text(encoding="ascii").splitlines()[8:]
    generated_fields = [line.split(",") for line in generated_lines]
    field_count_ok = all(
        len(fields) == EXPECTED_EPW_FIELDS for fields in generated_fields
    )
    ghi_difference = max(
        abs(float(fields[13]) - record.global_horizontal_w_m2)
        for fields, record in zip(generated_fields, records)
    )
    dry_bulb_difference = max(
        abs(float(fields[6]) - record.dry_bulb_c)
        for fields, record in zip(generated_fields, records)
    )
    wind_difference = max(
        abs(float(fields[21]) - record.wind_speed_m_s)
        for fields, record in zip(generated_fields, records)
    )
    controls = {
        "source_hour_count": _control(
            len(records) == EXPECTED_HOURS, EXPECTED_HOURS, len(records)
        ),
        "generated_hour_count": _control(
            len(generated_fields) == EXPECTED_HOURS,
            EXPECTED_HOURS,
            len(generated_fields),
        ),
        "epw_field_count": _control(
            field_count_ok,
            EXPECTED_EPW_FIELDS,
            sorted({len(fields) for fields in generated_fields}),
        ),
        "dry_bulb_preserved": _control(
            dry_bulb_difference == 0.0, 0.0, dry_bulb_difference
        ),
        "wind_speed_preserved": _control(
            wind_difference == 0.0, 0.0, wind_difference
        ),
        "ghi_preserved_with_integer_rounding": _control(
            ghi_difference <= 0.5, "<=0.5 W/m2", ghi_difference
        ),
        "nonzero_global_radiation_present": _control(
            max(record.global_horizontal_w_m2 for record in records) > 0.0,
            ">0 W/m2",
            max(record.global_horizontal_w_m2 for record in records),
        ),
        "dew_point_not_above_dry_bulb": _control(
            all(
                float(fields[7]) <= float(fields[6]) + 0.1
                for fields in generated_fields
            ),
            True,
            True,
        ),
    }
    status = (
        "READY_FOR_IESVE_READ_ONLY_PROBE"
        if all(control["status"] == "PASS" for control in controls.values())
        else "FAIL"
    )
    audit: Dict[str, Any] = {
        "schema_version": "1.0",
        "method": CONVERSION_METHOD_VERSION,
        "status": status,
        "purpose": "IESVE transport candidate from client climate data",
        "compliance_claim_allowed": False,
        "official_sia_weather_identity_confirmed": False,
        "source": {
            "archive_path": str(archive_source),
            "archive_sha256": _sha256_bytes(archive_bytes),
            "csv_entry": SOURCE_CSV_NAME,
            "csv_sha256": _sha256_bytes(csv_bytes),
            "client_epw_entry": SOURCE_EPW_NAME,
            "client_epw_sha256": _sha256_bytes(client_epw_bytes),
            "original_epw_defects": original_defects,
        },
        "weather": {
            "path": str(epw_path),
            "sha256": _sha256_path(epw_path),
            "format": "EPW",
            "record_count": len(generated_fields),
            "location_original": location.__dict__,
            "location_epw_ascii": _ascii(location.city),
        },
        "field_mapping": {
            "dry_bulb_c": "CSV tre200h0",
            "relative_humidity_percent": "CSV ure200h0",
            "wind_speed_m_s": "CSV fkl010h0",
            "wind_direction_degrees": "CSV dkl010h0",
            "global_horizontal": "CSV gls hourly mean; numeric Wh/m2 equivalence for one-hour records",
            "diffuse_horizontal": "CSV str.diffus hourly mean",
            "direct_normal": "CSV str.direkt hourly mean",
            "station_pressure": "Inherited same-hour client EPW field 9",
            "dew_point": "Derived from dry bulb and RH using NOAA MADIS equations",
            "horizontal_infrared": "Derived using EnergyPlus EPW equation",
            "total_sky_cover": "CSV percent converted to nearest tenth",
            "opaque_sky_cover": "Total sky cover used as explicit proxy",
            "unsupported_fields": "EPW documented missing-value sentinels",
        },
        "controls": controls,
        "warnings": [
            "The supplied EPW is structurally defective and is not modified.",
            "Pressure provenance is limited to the supplied client EPW.",
            "Opaque sky cover is unavailable; total sky cover is used as a proxy.",
            "Precipitation snow illuminance and ground-temperature inputs are unavailable and remain missing.",
            "IESVE WeatherFileReader read-back is mandatory before assignment.",
            "Certification use requires confirmation of SIA/MeteoSwiss source authorization and intended standard/test scope.",
        ],
        "model_or_weather_assignment_changed": False,
    }
    _write_atomic(
        audit_path,
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n",
        "utf-8",
    )
    if status == "FAIL":
        raise ConfigurationError(
            "Generated client EPW failed controls; see {}".format(audit_path)
        )
    return audit


def _parse_meteoswiss_station_metadata(
    metadata_path: Path,
    time_zone_hours: float,
) -> Tuple[WeatherLocation, Dict[str, Any]]:
    """Read the station row from the multilingual MeteoSwiss metadata CSV."""

    if not metadata_path.is_file():
        raise ConfigurationError(
            "Adjacent MeteoSwiss metadata file is missing: {}".format(metadata_path)
        )
    content = metadata_path.read_bytes()
    text = _decode_text(content, metadata_path.name)
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    if len(rows) < 2 or len(rows[1]) < 20:
        raise ConfigurationError("MeteoSwiss station metadata is malformed")
    station = rows[1]
    try:
        location = WeatherLocation(
            city=station[0].strip(),
            region=station[19].strip(),
            country="CHE",
            source=station[13].strip() or "MeteoSwiss",
            station_id=station[1].strip(),
            latitude_degrees=float(station[17]),
            longitude_degrees=float(station[18]),
            time_zone_hours=float(time_zone_hours),
            elevation_m=float(station[14]),
        )
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            "MeteoSwiss station metadata contains invalid coordinates"
        ) from exc
    if not -12.0 <= location.time_zone_hours <= 12.0:
        raise ConfigurationError("Explicit EPW time zone is outside -12..12")
    return location, {
        "path": str(metadata_path.resolve()),
        "sha256": _sha256_bytes(content),
        "station_row": {
            "station": location.city,
            "abbreviation": location.station_id,
            "owner": location.source,
            "elevation_m": location.elevation_m,
            "latitude_degrees": location.latitude_degrees,
            "longitude_degrees": location.longitude_degrees,
        },
    }


def _standard_pressure_pa(elevation_m: float) -> float:
    """Return standard barometric pressure at station elevation.

    The equation is the standard-atmosphere replacement used for missing EPW
    station pressure. It is a documented transport derivation, not a measured
    MeteoSwiss variable.
    """

    base = 1.0 - 2.25577e-5 * elevation_m
    if base <= 0.0:
        raise ConfigurationError("Station elevation cannot produce EPW pressure")
    return 101325.0 * base**5.2559


def _combine_meteoswiss_csv_records(
    csv_rows: Sequence[Mapping[str, str]],
    elevation_m: float,
) -> List[ClientWeatherRecord]:
    """Validate one 365-day MeteoSwiss climate year and derive EPW transport fields."""

    records: List[ClientWeatherRecord] = []
    source_year = int(_float(csv_rows[0], "time.yy", 2))
    pressure = _standard_pressure_pa(elevation_m)
    common_year_start = datetime(2001, 1, 1)
    for index, row in enumerate(csv_rows):
        line_number = index + 2
        expected = common_year_start + timedelta(hours=index)
        year = int(_float(row, "time.yy", line_number))
        month = int(_float(row, "time.mm", line_number))
        day = int(_float(row, "time.dd", line_number))
        hour = int(_float(row, "time.hh", line_number))
        if year != source_year or (month, day, hour) != (
            expected.month,
            expected.day,
            expected.hour,
        ):
            raise ConfigurationError(
                "MeteoSwiss CSV is not a continuous 365-day hourly climate year "
                "at line {}".format(line_number)
            )
        try:
            timestamp = datetime(year, month, day, hour)
        except ValueError as exc:
            raise ConfigurationError(
                "Invalid MeteoSwiss date at line {}".format(line_number)
            ) from exc

        values = {
            "dry_bulb": _float(row, "tre200h0", line_number),
            "relative_humidity": _float(row, "ure200h0", line_number),
            "wind_speed": _float(row, "fkl010h0", line_number),
            "wind_direction": _float(row, "dkl010h0", line_number),
            "sky_cover": _float(row, "skycover", line_number),
            "ghi": _float(row, "gls", line_number),
            "dhi": _float(row, "str.diffus", line_number),
            "dni": _float(row, "str.direkt", line_number),
        }
        for key, bounds in (
            ("dry_bulb", (-70.0, 70.0)),
            ("relative_humidity", (0.01, 100.0)),
            ("wind_speed", (0.0, 40.0)),
            ("wind_direction", (0.0, 360.0)),
            ("sky_cover", (0.0, 100.0)),
            ("ghi", (0.0, 2000.0)),
            ("dhi", (0.0, 2000.0)),
            ("dni", (0.0, 2000.0)),
        ):
            _validate_range(values[key], bounds[0], bounds[1], key, line_number)
        if values["dhi"] > values["ghi"] + 0.01:
            raise ConfigurationError(
                "Diffuse horizontal exceeds global horizontal at line {}".format(
                    line_number
                )
            )
        records.append(
            ClientWeatherRecord(
                timestamp=timestamp,
                dry_bulb_c=values["dry_bulb"],
                relative_humidity_percent=values["relative_humidity"],
                wind_speed_m_s=values["wind_speed"],
                wind_direction_degrees=values["wind_direction"],
                total_sky_cover_percent=values["sky_cover"],
                global_horizontal_w_m2=values["ghi"],
                diffuse_horizontal_w_m2=values["dhi"],
                direct_normal_w_m2=values["dni"],
                pressure_pa=pressure,
                source_flags="?",
            )
        )
    return records


def _write_meteoswiss_epw_candidate(
    source_csv: Path,
    csv_bytes: bytes,
    records: Sequence[ClientWeatherRecord],
    location: WeatherLocation,
    metadata_evidence: Mapping[str, Any],
    output_directory: Path,
) -> Dict[str, Any]:
    """Write one complete EPW candidate and its adjacent derivation audit."""

    stem = source_csv.stem
    epw_path = output_directory / "{}_IESVE_CANDIDATE.epw".format(stem)
    audit_path = output_directory / "{}_IESVE_DERIVATION.json".format(stem)
    first_weekday = calendar.day_name[records[0].timestamp.weekday()]
    header = [
        "LOCATION,{},{},{},{},{},{:.6f},{:.6f},{:g},{:g}".format(
            _ascii(location.city),
            _ascii(location.region),
            _ascii(location.country),
            _ascii(location.source),
            _ascii(location.station_id),
            location.latitude_degrees,
            location.longitude_degrees,
            location.time_zone_hours,
            location.elevation_m,
        ),
        "DESIGN CONDITIONS,0",
        "TYPICAL/EXTREME PERIODS,0",
        "GROUND TEMPERATURES,0",
        "HOLIDAYS/DAYLIGHT SAVINGS,No,0,0,0",
        "COMMENTS 1,MeteoSwiss future indoor-climate CSV transport candidate: {}".format(
            stem
        ),
        "COMMENTS 2,See {} for derivations limitations and source hashes".format(
            audit_path.name
        ),
        "DATA PERIODS,1,1,Data,{},1/1,12/31".format(first_weekday),
    ]
    epw_rows = [
        ",".join(str(value) for value in _epw_record(record)) for record in records
    ]
    _write_atomic(epw_path, "\n".join(header + epw_rows) + "\n", "ascii")

    generated = [
        line.split(",")
        for line in epw_path.read_text(encoding="ascii").splitlines()[8:]
        if line.strip()
    ]
    controls = {
        "source_hour_count": _control(
            len(records) == EXPECTED_HOURS, EXPECTED_HOURS, len(records)
        ),
        "generated_hour_count": _control(
            len(generated) == EXPECTED_HOURS, EXPECTED_HOURS, len(generated)
        ),
        "epw_field_count": _control(
            all(len(row) == EXPECTED_EPW_FIELDS for row in generated),
            EXPECTED_EPW_FIELDS,
            sorted({len(row) for row in generated}),
        ),
        "direct_diffuse_radiation_present": _control(
            max(record.direct_normal_w_m2 for record in records) > 0.0
            and max(record.diffuse_horizontal_w_m2 for record in records) > 0.0,
            True,
            True,
        ),
        "dew_point_not_above_dry_bulb": _control(
            all(float(row[7]) <= float(row[6]) + 0.1 for row in generated),
            True,
            True,
        ),
    }
    passed = all(item["status"] == "PASS" for item in controls.values())
    audit: Dict[str, Any] = {
        "schema_version": "1.0",
        "method": "swiss_sia.meteoswiss_csv_epw.v1",
        "status": "READY_FOR_IESVE_READ_ONLY_PROBE" if passed else "FAIL",
        "purpose": "IESVE transport candidate from MeteoSwiss hourly climate CSV",
        "compliance_claim_allowed": False,
        "official_sia_weather_identity_confirmed": False,
        "source": {
            "csv_path": str(source_csv.resolve()),
            "csv_sha256": _sha256_bytes(csv_bytes),
            "metadata": dict(metadata_evidence),
            "license": "CC BY 4.0; attribution required by GVE_Metadata.csv",
        },
        "weather": {
            "path": str(epw_path.resolve()),
            "sha256": _sha256_path(epw_path),
            "format": "EPW",
            "record_count": len(generated),
            "location": location.__dict__,
        },
        "field_mapping": {
            "dry_bulb_c": "CSV tre200h0",
            "relative_humidity_percent": "CSV ure200h0",
            "wind_speed_m_s": "CSV fkl010h0",
            "wind_direction_degrees": "CSV dkl010h0",
            "global_horizontal": "CSV gls hourly mean -> hourly Wh/m2",
            "diffuse_horizontal": "CSV str.diffus hourly mean -> hourly Wh/m2",
            "direct_normal": "CSV str.direkt hourly mean -> hourly Wh/m2",
            "total_sky_cover": "CSV skycover percent -> nearest tenth",
            "opaque_sky_cover": "Total sky cover used as explicit proxy",
            "dew_point": "Derived from dry bulb and RH using NOAA MADIS equations",
            "horizontal_infrared": "Derived using EnergyPlus EPW equation",
            "station_pressure": (
                "Standard atmosphere derived from MeteoSwiss station elevation"
            ),
            "unsupported_fields": "EPW documented missing-value sentinels",
        },
        "controls": controls,
        "warnings": [
            "This is a transport conversion, not an official MeteoSwiss/SIA EPW.",
            "The CSV contains no measured station pressure; standard elevation pressure is used.",
            "Opaque sky cover is unavailable; total sky cover is used as a proxy.",
            "Precipitation snow illuminance and ground temperatures are unavailable.",
            "The source is a 365-day climate year; 2060 omits leap day by source design.",
            "IESVE WeatherFileReader read-back is mandatory before assignment.",
            "Regulatory suitability and scenario selection require reviewer confirmation.",
        ],
        "model_or_weather_assignment_changed": False,
    }
    _write_atomic(
        audit_path,
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n",
        "utf-8",
    )
    if not passed:
        raise ConfigurationError(
            "Generated MeteoSwiss EPW failed controls: {}".format(audit_path)
        )
    return audit


def convert_meteoswiss_csv_directory(
    input_directory: PathLike,
    output_directory: PathLike,
    time_zone_hours: float,
) -> Dict[str, Any]:
    """Convert every scenario CSV beside one GVE_Metadata.csv, fail closed."""

    source_root = Path(input_directory).resolve()
    output_root = Path(output_directory).resolve()
    if not source_root.is_dir():
        raise ConfigurationError(
            "MeteoSwiss source directory does not exist: {}".format(source_root)
        )
    location, metadata = _parse_meteoswiss_station_metadata(
        source_root / "GVE_Metadata.csv", time_zone_hours
    )
    candidates = sorted(
        path
        for path in source_root.glob("GVE_*.csv")
        if path.name.casefold() != "gve_metadata.csv"
    )
    if not candidates:
        raise ConfigurationError("No GVE scenario CSV files were found")
    output_root.mkdir(parents=True, exist_ok=True)
    outputs = []
    for source_csv in candidates:
        csv_bytes = source_csv.read_bytes()
        csv_rows = _parse_client_csv(_decode_text(csv_bytes, source_csv.name))
        records = _combine_meteoswiss_csv_records(csv_rows, location.elevation_m)
        audit = _write_meteoswiss_epw_candidate(
            source_csv,
            csv_bytes,
            records,
            location,
            metadata,
            output_root,
        )
        outputs.append(
            {
                "source": str(source_csv),
                "epw": audit["weather"]["path"],
                "audit": str(
                    output_root / "{}_IESVE_DERIVATION.json".format(source_csv.stem)
                ),
                "status": audit["status"],
            }
        )
    summary = {
        "schema_version": "1.0",
        "status": "READY_FOR_IESVE_READ_ONLY_PROBE",
        "input_directory": str(source_root),
        "output_directory": str(output_root),
        "time_zone_hours_explicit_input": float(time_zone_hours),
        "station": location.__dict__,
        "outputs": outputs,
        "compliance_claim_allowed": False,
    }
    _write_atomic(
        output_root / "GVE_IESVE_CONVERSION_SUMMARY.json",
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        "utf-8",
    )
    return summary


__all__ = [
    "CONVERSION_METHOD_VERSION",
    "OUTPUT_AUDIT_NAME",
    "OUTPUT_EPW_NAME",
    "ClientWeatherRecord",
    "WeatherLocation",
    "convert_client_weather_archive",
    "convert_meteoswiss_csv_directory",
]
