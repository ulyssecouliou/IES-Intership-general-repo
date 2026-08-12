"""Station-generic import of MeteoSwiss ``klimaszenarien-raumklima`` archives.

The pre-existing :mod:`client_weather_conversion` module exposes
``convert_meteoswiss_csv_directory`` which is bound to the ``GVE_...`` file
naming convention.  MeteoSwiss publishes the same product for every scaled-
observation station (BAS, BKLI, GVE, KLO, REH, ...) under a matching
``<STATION>_Metadata.csv`` / ``<STATION>_<scenario>.csv`` layout.

This module re-uses the private, already-tested helpers of
``client_weather_conversion`` and adds one thin public entry point which takes
the station code explicitly and writes:

* one EPW candidate per scenario CSV, plus its audit JSON, under
  ``<output_root>/<STATION>/``;
* one ``<STATION>_IESVE_CONVERSION_SUMMARY.json`` naming every input file,
  every output file, the SHA-256 of the station-metadata source and the
  explicit time-zone reviewer input.

No SIA validation claim is made by this module: the outputs are labelled
``READY_FOR_IESVE_READ_ONLY_PROBE`` so downstream consumers know they must
be qualified inside VE before any compliance use.

Pure Python; the only new dependency is ``zipfile`` from the standard library
for the unpack helper.  Openpyxl is not required.
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .client_weather_conversion import (
    _combine_meteoswiss_csv_records,
    _decode_text,
    _parse_client_csv,
    _parse_meteoswiss_station_metadata,
    _write_atomic,
    _write_meteoswiss_epw_candidate,
)
from .exceptions import ConfigurationError


__all__ = [
    "STATION_CODE_ALLOWED_CHARACTERS",
    "unpack_meteoswiss_archive",
    "convert_meteoswiss_station_directory",
    "convert_meteoswiss_station_archive",
]


STATION_CODE_ALLOWED_CHARACTERS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")


def _validate_station_code(station_code: str) -> str:
    """Refuse anything that would not match the MeteoSwiss naming convention."""

    if not isinstance(station_code, str):
        raise ConfigurationError("station_code must be a string")
    upper = station_code.strip().upper()
    if not upper:
        raise ConfigurationError("station_code must not be empty")
    if not set(upper).issubset(STATION_CODE_ALLOWED_CHARACTERS):
        raise ConfigurationError(
            "station_code {!r} contains characters outside A-Z0-9".format(upper)
        )
    return upper


def unpack_meteoswiss_archive(
    archive_path: Path,
    unpack_root: Path,
) -> Path:
    """Extract one ``klimaszenarien-raumklima-<STATION>.zip`` to a sibling folder.

    Args:
        archive_path: Path to the ZIP archive as downloaded from the
            MeteoSwiss product page.
        unpack_root: Directory under which the extraction folder is created.
            The extracted folder is named ``klimaszenarien-raumklima-<STATION>``
            to mirror the archive's own naming, so a re-run finds and reuses
            the same directory.

    Returns:
        Path to the extracted directory.  The path is guaranteed to contain
        both ``<STATION>_Metadata.csv`` and at least one scenario CSV; the
        function raises otherwise.
    """

    archive_path = Path(archive_path).resolve()
    if not archive_path.is_file():
        raise ConfigurationError(
            "MeteoSwiss archive is not a file: {}".format(archive_path)
        )
    name = archive_path.stem
    marker = "klimaszenarien-raumklima-"
    if not name.startswith(marker):
        raise ConfigurationError(
            "Unexpected archive name {!r}; expected prefix {!r}".format(
                archive_path.name, marker
            )
        )
    station_code = _validate_station_code(name[len(marker):])
    destination = Path(unpack_root).resolve() / name
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        expected_metadata = "{}_Metadata.csv".format(station_code)
        metadata_present = any(
            member.filename == expected_metadata for member in archive.infolist()
        )
        if not metadata_present:
            raise ConfigurationError(
                "Archive {} does not contain {}".format(archive_path, expected_metadata)
            )
        for member in archive.infolist():
            if member.is_dir():
                continue
            # Reject absolute paths or traversal attempts.
            if member.filename.startswith(("/", "\\")) or ".." in Path(
                member.filename
            ).parts:
                raise ConfigurationError(
                    "Archive {} contains suspicious path {}".format(
                        archive_path, member.filename
                    )
                )
            archive.extract(member, destination)
    # Post-extract sanity check: at least one scenario CSV alongside metadata.
    scenarios = [
        p
        for p in destination.glob("{}_*.csv".format(station_code))
        if p.name != "{}_Metadata.csv".format(station_code)
    ]
    if not scenarios:
        raise ConfigurationError(
            "Extracted archive {} carries no scenario CSVs beside {}".format(
                archive_path, expected_metadata
            )
        )
    return destination


def convert_meteoswiss_station_directory(
    station_code: str,
    input_directory: Path,
    output_directory: Path,
    time_zone_hours: float,
) -> Dict[str, Any]:
    """Convert every ``<STATION>_*.csv`` in ``input_directory`` to an EPW candidate.

    Args:
        station_code: Uppercase MeteoSwiss station abbreviation (e.g. ``KLO``).
        input_directory: Directory holding ``<STATION>_Metadata.csv`` plus one
            or more scenario CSV files.
        output_directory: Root under which a subdirectory named
            ``<STATION>`` will be created; every output file lives there.
        time_zone_hours: Explicit EPW local-standard-time offset from UTC.
            MeteoSwiss publishes timestamps in local standard time (CET =
            ``+1.0`` for Switzerland).  This value is written verbatim into
            the summary as reviewer input.

    Returns:
        A dict mirroring the summary written to
        ``<output_directory>/<STATION>/<STATION>_IESVE_CONVERSION_SUMMARY.json``.
    """

    station_code = _validate_station_code(station_code)
    source_root = Path(input_directory).resolve()
    if not source_root.is_dir():
        raise ConfigurationError(
            "MeteoSwiss source directory does not exist: {}".format(source_root)
        )
    metadata_path = source_root / "{}_Metadata.csv".format(station_code)
    location, metadata = _parse_meteoswiss_station_metadata(
        metadata_path, time_zone_hours
    )
    candidates = sorted(
        path
        for path in source_root.glob("{}_*.csv".format(station_code))
        if path.name.casefold() != "{}_metadata.csv".format(station_code.lower())
    )
    if not candidates:
        raise ConfigurationError(
            "No {} scenario CSV files were found under {}".format(
                station_code, source_root
            )
        )
    output_root = Path(output_directory).resolve() / station_code
    output_root.mkdir(parents=True, exist_ok=True)
    outputs: List[Dict[str, Any]] = []
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
        "station_code": station_code,
        "input_directory": str(source_root),
        "output_directory": str(output_root),
        "time_zone_hours_explicit_input": float(time_zone_hours),
        "station": location.__dict__,
        "metadata_source": metadata,
        "outputs": outputs,
        "compliance_claim_allowed": False,
    }
    _write_atomic(
        output_root / "{}_IESVE_CONVERSION_SUMMARY.json".format(station_code),
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        "utf-8",
    )
    return summary


def convert_meteoswiss_station_archive(
    archive_path: Path,
    unpack_root: Path,
    output_directory: Path,
    time_zone_hours: float,
) -> Dict[str, Any]:
    """One-shot: unpack a ``klimaszenarien-raumklima-<STATION>.zip`` then convert."""

    extracted = unpack_meteoswiss_archive(archive_path, unpack_root)
    marker = "klimaszenarien-raumklima-"
    station_code = _validate_station_code(extracted.name[len(marker):])
    return convert_meteoswiss_station_directory(
        station_code=station_code,
        input_directory=extracted,
        output_directory=output_directory,
        time_zone_hours=time_zone_hours,
    )
