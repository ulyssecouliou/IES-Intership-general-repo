"""Install converted MeteoSwiss / SIA EPW candidates into the IES VE weather folder.

Target folder: ``C:\\Program Files\\IES\\Shared Content\\Weather``.  Writing there
requires either an administrator process or an existing folder ACL that grants
the current user write access.  The launcher probes the folder first and fails
closed with a clear message if write access is denied.

Source scan strategy (deterministic):

* every ``.epw`` under ``generated_weather/<STATION>/`` produced by
  ``Convert_MeteoSwiss_Station_Weather.py`` is treated as a
  ``MeteoSwiss-transport-candidate`` — labelled explicitly in the audit;
* every ``.epw`` under ``generated_weather/<STATION>/`` whose stem ends in
  ``_SIA_OFFICIAL`` is treated as a ``SIA-official`` file (byte-for-byte copy
  from the SIA distribution package, e.g. ``SIA 380_2 and SIA 4010.zip``).

Target naming: ``CHE_<STATION>_<scenario>[_source-tag].epw`` so the new files
sort under the existing IES country-prefixed layout.  Any name collision with
a different SHA-256 aborts installation for that file unless ``--force`` is
passed.

An audit JSON is written under ``sia4010_evidence/weather_install/<UTC-date>.json``
with the source path, target path, SHA-256, size and label for every
installed file.  ``sia4010_evidence/`` is git-ignored by convention, so the
audit stays local.

No compliance claim is made by this launcher; each EPW carries its own
provenance and every installed file remains a candidate for IESVE
``WeatherFileReader`` read-back qualification before assignment.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE_ROOT = REPO_ROOT / "generated_weather"
DEFAULT_TARGET = Path(r"C:\Program Files\IES\Shared Content\Weather")
DEFAULT_AUDIT_ROOT = REPO_ROOT / "sia4010_evidence" / "weather_install"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _probe_write_access(target: Path) -> tuple[bool, str]:
    try:
        target.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return False, "cannot create {}: {}".format(target, exc)
    try:
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        marker = target / "._ies_weather_install_probe_{}.tmp".format(stamp)
        marker.write_bytes(b"probe")
        marker.unlink()
    except PermissionError as exc:
        return False, "PermissionError while probing {}: {}".format(target, exc)
    except Exception as exc:
        return False, "{}: {}".format(type(exc).__name__, exc)
    return True, "ok"


def _label_for(source: Path) -> str:
    """Classify one EPW by the provenance encoded in its filename.

    The distinction matters for the audit trail: a CH2018 future-scenario
    transport, a SIA-supplied DRY normal transport and a byte-for-byte copy of
    an EPW issued inside the SIA package are three different kinds of evidence
    and must not share one label.
    """

    stem = source.stem
    if stem.endswith("_SIA_OFFICIAL"):
        return "SIA-official"
    if "_SIA2028_DRY_NORMAL" in stem:
        # Transport of the DRY normal dataset supplied by the authority
        # responsible for the SIA 4010 validation. This is the test climate the
        # specifications require, not a CH2018 application-climate scenario.
        return "SIA2028-DRY-normal-transport-candidate"
    if stem.endswith("_IESVE_CANDIDATE"):
        return "MeteoSwiss-CH2018-transport-candidate"
    return "unlabelled"


def _target_name(source: Path, station: str) -> str:
    stem = source.stem
    if stem.endswith("_IESVE_CANDIDATE"):
        base = stem[: -len("_IESVE_CANDIDATE")]
        return "CHE_{}.epw".format(base) if base.startswith(station) else \
               "CHE_{}_{}.epw".format(station, base)
    if stem.endswith("_SIA_OFFICIAL"):
        return "CHE_{}_{}.epw".format(station, stem[: -len("_SIA_OFFICIAL")]) \
               if not stem.startswith(station) else \
               "CHE_{}_SIA-official.epw".format(stem[: -len("_SIA_OFFICIAL")])
    return "CHE_{}_{}.epw".format(station, stem)


def _collect(source_root: Path) -> list[dict]:
    files: list[dict] = []
    for station_dir in sorted(p for p in source_root.iterdir() if p.is_dir()):
        station = station_dir.name
        for epw in sorted(station_dir.glob("*.epw")):
            files.append(
                {
                    "station": station,
                    "source": epw,
                    "sha256": _sha256(epw),
                    "size": epw.stat().st_size,
                    "label": _label_for(epw),
                    "target_name": _target_name(epw, station),
                }
            )
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument(
        "--source-root",
        type=Path,
        default=DEFAULT_SOURCE_ROOT,
        help="Root that contains one <STATION>/ folder per station (default: generated_weather/).",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help="Destination folder (default: IES 'Shared Content/Weather').",
    )
    parser.add_argument(
        "--audit-root",
        type=Path,
        default=DEFAULT_AUDIT_ROOT,
        help="Where to write the install audit JSON (default: sia4010_evidence/weather_install/).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing target file whose SHA-256 differs from the source.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be done; do not copy anything.",
    )
    args = parser.parse_args()

    source_root: Path = args.source_root.resolve()
    target: Path = args.target.resolve()
    audit_root: Path = args.audit_root.resolve()

    if not source_root.is_dir():
        print("Source root does not exist: {}".format(source_root), file=sys.stderr)
        return 2

    ok, detail = _probe_write_access(target)
    if not ok:
        print(
            "Cannot write to {}: {}\nRun this launcher from an elevated shell, "
            "or grant the current user write access to the folder.".format(target, detail),
            file=sys.stderr,
        )
        return 1

    files = _collect(source_root)
    if not files:
        print("No .epw files found under {}".format(source_root), file=sys.stderr)
        return 2

    audit_entries = []
    installed = 0
    skipped = 0
    conflicts = 0
    for entry in files:
        source: Path = entry["source"]
        dest = target / entry["target_name"]
        record = {
            "station": entry["station"],
            "label": entry["label"],
            "source_path": str(source),
            "source_sha256": entry["sha256"],
            "source_size_bytes": entry["size"],
            "target_path": str(dest),
            "target_name": entry["target_name"],
        }
        if dest.exists():
            existing = _sha256(dest)
            if existing == entry["sha256"]:
                record["action"] = "SKIPPED_ALREADY_INSTALLED"
                skipped += 1
                audit_entries.append(record)
                continue
            record["existing_sha256"] = existing
            if not args.force:
                record["action"] = "CONFLICT_ABORTED"
                conflicts += 1
                audit_entries.append(record)
                continue
            record["action"] = "OVERWRITTEN_WITH_FORCE"
        else:
            record["action"] = "INSTALLED"

        if not args.dry_run:
            shutil.copy2(source, dest)
            record["installed_sha256"] = _sha256(dest)
            if record["installed_sha256"] != entry["sha256"]:
                record["action"] = "FAIL_READBACK_MISMATCH"
                conflicts += 1
                audit_entries.append(record)
                continue
        installed += 1
        audit_entries.append(record)

    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    audit_root.mkdir(parents=True, exist_ok=True)
    audit_path = audit_root / "sia_weather_install_{}.json".format(stamp)
    audit_body = {
        "schema_version": "1.0",
        "generated_at_utc": stamp,
        "source_root": str(source_root),
        "target": str(target),
        "counts": {
            "installed": installed,
            "skipped": skipped,
            "conflicts": conflicts,
            "total": len(files),
        },
        "dry_run": args.dry_run,
        "force": args.force,
        "entries": audit_entries,
        "compliance_claim_allowed": False,
        "note": (
            "Every installed EPW remains a candidate; VE WeatherFileReader "
            "read-back is required before assignment. SIA-official files are "
            "byte-for-byte copies from the SIA distribution package."
        ),
    }
    audit_path.write_text(
        json.dumps(audit_body, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("Installed: {}  Skipped (already present): {}  Conflicts: {}".format(
        installed, skipped, conflicts
    ))
    for e in audit_entries:
        print(" - [{action}] {label}: {name}".format(
            action=e["action"], label=e["label"], name=e["target_name"]
        ))
    print("Audit: {}".format(audit_path))
    return 0 if conflicts == 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())
