"""Read-only IESVE qualification probe for a derived client EPW candidate."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import iesve


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from swiss_sia.reference_model.client_weather_conversion import (  # noqa: E402
    OUTPUT_AUDIT_NAME,
)


def _sha256(path):
    """Return an uppercase SHA-256 checksum for one local artifact."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _write_json(path, payload):
    """Write one diagnostic atomically without changing the VE model."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def run():
    """Read the derived EPW through VE and emit fail-closed evidence."""

    project = iesve.VEProject.get_current_project()
    project_root = Path(project.path).resolve()
    candidates = sorted(project_root.glob("*_IESVE_CANDIDATE.epw"))
    if len(candidates) != 1:
        raise RuntimeError(
            "Expected exactly one *_IESVE_CANDIDATE.epw in {}, found {}".format(
                project_root, len(candidates)
            )
        )
    weather_path = candidates[0].resolve()
    audit_path = project_root / OUTPUT_AUDIT_NAME
    if not audit_path.is_file():
        raise RuntimeError("Adjacent derivation audit is missing: {}".format(audit_path))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    expected_sha = str(audit.get("weather", {}).get("sha256", "")).upper()
    actual_sha = _sha256(weather_path)
    if not expected_sha or expected_sha != actual_sha:
        raise RuntimeError("Derived EPW checksum does not match its audit JSON")
    if audit.get("status") != "READY_FOR_IESVE_READ_ONLY_PROBE":
        raise RuntimeError("Derivation audit is not ready for an IESVE probe")

    reader = iesve.WeatherFileReader()
    try:
        open_result = int(reader.open_weather_file(str(weather_path)))
        if open_result <= 0:
            raise RuntimeError("IESVE WeatherFileReader rejected {}".format(weather_path))
        number_of_days = 366 if int(reader.feb29) else 365
        dry_bulb = reader.get_results(3, 1, number_of_days)
        wind_speed = reader.get_results(10, 1, number_of_days)
        record_count = len(dry_bulb)
        passed = record_count == 8760 and len(wind_speed) == 8760
        payload = {
            "schema_version": "1.0",
            "status": "READY_FOR_CONTROLLED_MODEL_ASSIGNMENT" if passed else "FAIL",
            "purpose": "Read-only IESVE qualification of derived client weather",
            "compliance_claim_allowed": False,
            "project": project.name,
            "weather_file": str(weather_path),
            "weather_sha256": actual_sha,
            "derivation_audit": str(audit_path),
            "derivation_method": audit.get("method"),
            "iesve_open_result": open_result,
            "site": str(reader.site),
            "latitude": float(reader.lat),
            "longitude": float(reader.long),
            "time_zone": float(reader.time_zone),
            "year": int(reader.year),
            "feb29": int(reader.feb29),
            "record_count": record_count,
            "dry_bulb_c": {"minimum": float(min(dry_bulb)), "maximum": float(max(dry_bulb))},
            "wind_speed_m_s": {"minimum": float(min(wind_speed)), "maximum": float(max(wind_speed))},
            "limitations": audit.get("warnings", []),
            "model_or_weather_assignment_changed": False,
        }
    finally:
        try:
            reader.close()
        except Exception:
            pass

    report_path = project_root / "weather_artifacts" / "diagnostics" / "client_weather_iesve_probe.json"
    _write_json(report_path, payload)
    print("READ-ONLY CLIENT WEATHER PROBE: {}".format(payload["status"]))
    print("Project: {}".format(project.name))
    print("Weather: {}".format(weather_path))
    print("Records: {}".format(payload["record_count"]))
    print("Report: {}".format(report_path))
    print("Compliance claim allowed: NO")
    print("No VE model or weather assignment was changed.")


if __name__ == "__main__":
    run()
