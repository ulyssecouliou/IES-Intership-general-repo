"""Read-only comparison of the derived DRYCOLD EPW and native VE Denver FWT."""

import hashlib
import json
import math
import sys
from pathlib import Path

import iesve


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

NATIVE_CANDIDATE = "DenverStapletonTMY.fwt"
VARIABLES = {
    1: "cloud_cover_oktas",
    2: "wind_direction_degrees",
    3: "dry_bulb_c",
    4: "wet_bulb_c",
    5: "direct_normal_radiation_w_m2",
    6: "diffuse_horizontal_radiation_w_m2",
    9: "atmospheric_pressure_pa",
    10: "wind_speed_m_s",
    11: "relative_humidity_percent",
    12: "humidity_ratio_kg_kg",
}


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


def _weather_paths():
    getter = getattr(iesve, "get_weather_file_paths", None)
    return [Path(str(item)) for item in getter()] if callable(getter) else []


def _resolve(reference, project_root):
    supplied = Path(str(reference))
    candidates = [supplied, project_root / supplied.name]
    candidates.extend(folder / supplied.name for folder in _weather_paths())
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise RuntimeError("Weather file cannot be resolved: {}".format(reference))


def _read(reference):
    reader = iesve.WeatherFileReader()
    try:
        if int(reader.open_weather_file(str(reference))) <= 0:
            raise RuntimeError("WeatherFileReader rejected {}".format(reference))
        days = 366 if int(reader.feb29) else 365
        values = {
            name: [float(item) for item in reader.get_results(index, 1, days)]
            for index, name in VARIABLES.items()
        }
        metadata = {
            "site": str(reader.site),
            "latitude": float(reader.lat),
            "longitude": float(reader.long),
            "time_zone": float(reader.time_zone),
            "year": int(reader.year),
            "feb29": int(reader.feb29),
        }
    finally:
        try:
            reader.close()
        except Exception:
            pass
    return values, metadata


def _comparison(left, right):
    if len(left) != len(right):
        return {"status": "FAIL", "left_count": len(left), "right_count": len(right)}
    differences = [abs(a - b) for a, b in zip(left, right)]
    return {
        "status": "PASS",
        "record_count": len(left),
        "maximum_absolute_difference": max(differences),
        "mean_absolute_difference": sum(differences) / len(differences),
        "left_annual_sum": sum(left),
        "right_annual_sum": sum(right),
        "identical_record_count": sum(value == 0.0 for value in differences),
    }


def _lag_diagnostic(left, right):
    outcomes = []
    for lag in range(-3, 4):
        if lag < 0:
            first, second = left[-lag:], right[:lag]
        elif lag > 0:
            first, second = left[:-lag], right[lag:]
        else:
            first, second = left, right
        rmse = math.sqrt(
            sum((a - b) ** 2 for a, b in zip(first, second)) / len(first)
        )
        outcomes.append({"lag_hours": lag, "rmse": rmse})
    return {
        "outcomes": outcomes,
        "lowest_rmse_lag_hours": min(outcomes, key=lambda item: item["rmse"])[
            "lag_hours"
        ],
    }


def run():
    """Compare both transports without assigning weather or changing the model."""

    project = iesve.VEProject.get_current_project()
    project_root = Path(project.path).resolve()
    locate = iesve.VELocate()
    try:
        if locate.open_wea_data() < 0:
            raise RuntimeError("VELocate.open_wea_data() failed")
        assigned_reference = str(locate.get().get("weather_file", ""))
        locate.close_wea_data()
    except Exception:
        try:
            locate.close_wea_data()
        except Exception:
            pass
        raise
    assigned_path = _resolve(assigned_reference, project_root)
    native_path = _resolve(NATIVE_CANDIDATE, project_root)
    assigned_values, assigned_metadata = _read(assigned_path)
    native_values, native_metadata = _read(native_path)
    comparisons = {
        name: _comparison(assigned_values[name], native_values[name])
        for name in VARIABLES.values()
    }
    payload = {
        "schema_version": "1.0",
        "status": "READY_FOR_WEATHER_IDENTITY_REVIEW",
        "purpose": (
            "Read-only transport comparison. It does not establish that the "
            "native FWT is the normative SIA/ISO weather file."
        ),
        "project": str(project_root),
        "assigned_weather": {
            "reference": assigned_reference,
            "path": str(assigned_path),
            "sha256": _sha256(assigned_path),
            "metadata": assigned_metadata,
        },
        "native_candidate": {
            "reference": NATIVE_CANDIDATE,
            "path": str(native_path),
            "sha256": _sha256(native_path),
            "metadata": native_metadata,
        },
        "comparisons": comparisons,
        "solar_lag_diagnostics": {
            name: _lag_diagnostic(assigned_values[name], native_values[name])
            for name in (
                "direct_normal_radiation_w_m2",
                "diffuse_horizontal_radiation_w_m2",
            )
        },
        "model_or_weather_assignment_changed": False,
        "compliance_claim_allowed": False,
    }
    report_path = (
        project_root
        / "sia4010_artifacts"
        / "diagnostics"
        / "sia4010_weather_transport_comparison.json"
    )
    _write_json(report_path, payload)
    print("SIA 4010 WEATHER TRANSPORT COMPARISON: {}".format(payload["status"]))
    print("Assigned: {}".format(assigned_path))
    print("Native candidate: {}".format(native_path))
    for name in (
        "dry_bulb_c",
        "wind_speed_m_s",
        "direct_normal_radiation_w_m2",
        "diffuse_horizontal_radiation_w_m2",
    ):
        item = comparisons[name]
        print(
            "{}: max_abs={}, mean_abs={}, identical={}/{}".format(
                name,
                item["maximum_absolute_difference"],
                item["mean_absolute_difference"],
                item["identical_record_count"],
                item["record_count"],
            )
        )
    print("Report: {}".format(report_path))
    print("No VE model or weather assignment was changed.")
    return payload


if __name__ == "__main__":
    run()
