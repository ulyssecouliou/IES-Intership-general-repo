"""Read-only IESVE probe for the prepared SIA 4010 Case 600 weather file."""

import hashlib
import json
import sys
from pathlib import Path

import iesve


REPOSITORY_ROOT = Path(__file__).resolve().parent
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def run():
    """Open the TMY through VE and emit evidence without changing the model."""

    project = iesve.VEProject.get_current_project()
    project_root = Path(project.path)
    candidates = sorted(
        path
        for path in project_root.iterdir()
        if path.is_file() and path.suffix.casefold() in {".epw", ".fwt"}
    )
    if len(candidates) != 1:
        raise RuntimeError(
            "Expected exactly one VE-readable .epw or .fwt in {}, found {}"
            .format(
                project_root, len(candidates)
            )
        )
    weather_path = candidates[0].resolve()
    reader = iesve.WeatherFileReader()
    try:
        open_result = int(reader.open_weather_file(str(weather_path)))
        if open_result <= 0:
            raise RuntimeError(
                "IESVE WeatherFileReader rejected {}".format(weather_path)
            )
        num_days = 366 if int(reader.feb29) else 365
        # The documented WeatherFileReader identifiers are stable across the
        # VE versions relevant to this project: 3=dry bulb, 10=wind speed.
        dry_bulb = reader.get_results(3, 1, num_days)
        wind_speed = reader.get_results(10, 1, num_days)
        record_count = len(dry_bulb)
        payload = {
            "schema_version": "1.0",
            "status": (
                "PASS"
                if record_count == 8760 and len(wind_speed) == 8760
                else "FAIL"
            ),
            "purpose": (
                "Read-only IESVE weather readability check; not a compliance "
                "result and not a weather assignment."
            ),
            "project": project.name,
            "weather_file": str(weather_path),
            "weather_sha256": _sha256(weather_path),
            "iesve_open_result": open_result,
            "site": str(reader.site),
            "latitude": float(reader.lat),
            "longitude": float(reader.long),
            "time_zone": float(reader.time_zone),
            "year": int(reader.year),
            "feb29": int(reader.feb29),
            "record_count": record_count,
            "dry_bulb_c": {
                "minimum": float(min(dry_bulb)),
                "maximum": float(max(dry_bulb)),
            },
            "wind_speed_m_s": {
                "minimum": float(min(wind_speed)),
                "maximum": float(max(wind_speed)),
            },
            "model_or_weather_assignment_changed": False,
        }
    finally:
        try:
            reader.close()
        except Exception:
            pass

    report_path = (
        project_root
        / "sia4010_artifacts"
        / "diagnostics"
        / "case600_weather_iesve_probe.json"
    )
    _write_json(report_path, payload)
    print("READ-ONLY CASE 600 WEATHER PROBE: {}".format(payload["status"]))
    print("Project: {}".format(project.name))
    print("Weather: {}".format(weather_path))
    print("Records: {}".format(payload["record_count"]))
    print("Report: {}".format(report_path))
    print("No VE model or weather assignment was changed.")


if __name__ == "__main__":
    run()
