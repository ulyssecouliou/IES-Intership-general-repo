"""Unpack and convert one or more MeteoSwiss klimaszenarien-raumklima archives.

This launcher is station-generic: pass a list of ZIP archives (or the
containing directory) and it will unpack each one, convert every scenario CSV
to an EPW candidate under ``--output <output>/<STATION>/`` and emit a
per-station audit JSON plus a per-station SUMMARY.

Usage examples (from the repo root, no VE required):

    python Convert_MeteoSwiss_Station_Weather.py \
        --archive "%USERPROFILE%\\Downloads\\klimaszenarien-raumklima-KLO.zip" \
        --archive "%USERPROFILE%\\Downloads\\klimaszenarien-raumklima-BAS.zip" \
        --output generated_weather --time-zone 1.0

    python Convert_MeteoSwiss_Station_Weather.py \
        --archive-glob "%USERPROFILE%\\Downloads\\klimaszenarien-raumklima-*.zip" \
        --output generated_weather --time-zone 1.0

Switzerland uses CET local standard time (UTC+1) without DST for the MeteoSwiss
climate scenarios, so ``--time-zone 1.0`` is the reviewer-approved value.  The
launcher passes it through verbatim; it is not defaulted silently.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from swiss_sia.reference_model.meteoswiss_station_import import (
    convert_meteoswiss_station_archive,
)


def _iter_archive_paths(args: argparse.Namespace) -> list[Path]:
    paths: list[Path] = []
    for entry in args.archive:
        paths.append(Path(entry).resolve())
    for pattern in args.archive_glob:
        for hit in sorted(glob.glob(pattern)):
            paths.append(Path(hit).resolve())
    deduped: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path).casefold()
        if key not in seen:
            seen.add(key)
            deduped.append(path)
    return deduped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument(
        "--archive",
        action="append",
        default=[],
        help=(
            "Path to a klimaszenarien-raumklima-<STATION>.zip archive. "
            "Repeat for multiple stations."
        ),
    )
    parser.add_argument(
        "--archive-glob",
        action="append",
        default=[],
        help=(
            "Glob pattern matching one or more archives (e.g. "
            "'~/Downloads/klimaszenarien-raumklima-*.zip')."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help=(
            "Root output directory. A subdirectory <STATION>/ is created "
            "for each archive."
        ),
    )
    parser.add_argument(
        "--unpack-root",
        type=Path,
        default=None,
        help=(
            "Where to extract archives; default is the parent of each archive."
        ),
    )
    parser.add_argument(
        "--time-zone",
        type=float,
        required=True,
        help="EPW local standard-time offset from UTC; explicit reviewer input.",
    )
    args = parser.parse_args()

    archive_paths = _iter_archive_paths(args)
    if not archive_paths:
        print(
            "No archives supplied; pass --archive and/or --archive-glob.",
            file=sys.stderr,
        )
        return 2

    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    summaries = []
    failures = []
    for archive_path in archive_paths:
        unpack_root = args.unpack_root or archive_path.parent
        try:
            summary = convert_meteoswiss_station_archive(
                archive_path=archive_path,
                unpack_root=unpack_root,
                output_directory=output_dir,
                time_zone_hours=args.time_zone,
            )
        except Exception as exc:  # noqa: BLE001 - per-archive failure isolation
            failures.append(
                {
                    "archive": str(archive_path),
                    "status": "FAILED",
                    "error": "{}: {}".format(type(exc).__name__, exc),
                }
            )
            print(
                "FAILED {} -- {}: {}".format(
                    archive_path.name, type(exc).__name__, exc
                ),
                file=sys.stderr,
            )
            continue
        summaries.append(summary)
        print(
            "Converted {} -> {} ({} scenarios)".format(
                archive_path.name,
                summary["output_directory"],
                len(summary["outputs"]),
            )
        )
    aggregate = {
        "schema_version": "1.0",
        "status": (
            "READY_FOR_IESVE_READ_ONLY_PROBE"
            if summaries and not failures
            else "PARTIAL"
            if summaries
            else "FAILED"
        ),
        "station_count": len(summaries),
        "stations": [s["station_code"] for s in summaries],
        "failed_archives": failures,
        "output_directory": str(output_dir),
        "time_zone_hours_explicit_input": args.time_zone,
        "per_station_summaries": [
            str(
                Path(s["output_directory"])
                / "{}_IESVE_CONVERSION_SUMMARY.json".format(s["station_code"])
            )
            for s in summaries
        ],
        "compliance_claim_allowed": False,
    }
    aggregate_path = (
        output_dir / "MeteoSwiss_STATION_IMPORT_SUMMARY.json"
    )
    aggregate_path.write_text(
        json.dumps(aggregate, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("Aggregate summary: {}".format(aggregate_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
