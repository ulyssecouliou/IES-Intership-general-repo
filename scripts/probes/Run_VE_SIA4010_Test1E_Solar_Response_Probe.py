"""Read-only solar-response diagnostic for the latest Test 1E APS."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import iesve


ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)


def _summary(values):
    if not values:
        return {"count": 0, "minimum": None, "maximum": None, "mean": None, "sum": None}
    return {
        "count": len(values),
        "minimum": min(values),
        "maximum": max(values),
        "mean": sum(values) / len(values),
        "sum": sum(values),
    }


def _variable(variables, aps_name, level):
    rows = [
        item for item in variables
        if str(item.get("aps_varname") or "").strip().casefold() == aps_name.casefold()
        and str(item.get("model_level") or "").strip().casefold() == level.casefold()
    ]
    if not rows:
        return None
    # Prefer the physical flux rather than the alternative heat-flow metadata.
    rows.sort(key=lambda item: "flux" not in str(item.get("display_name") or "").casefold())
    return rows[0]


def _aps_tuple(item):
    return (
        str(item.get("aps_varname") or ""),
        str(item.get("display_name") or item.get("aps_varname") or ""),
        str(item.get("model_level") or ""),
        str(item.get("resolved_metric_unit") or ""),
        float(item.get("resolved_metric_divisor") or 1.0),
        float(item.get("resolved_metric_offset") or 0.0),
    )


def run():
    from swiss_sia.reference_model.sia4010.aps_probe import build_surface_inventory
    from swiss_sia.simulation_results import (
        convert_aps_series_to_metric,
        get_available_variables,
        get_results_per_hour,
        open_results_reader,
        read_room_result,
        read_surface_result,
    )

    project = iesve.VEProject.get_current_project()
    project_path = Path(str(project.path)).resolve()
    audit_path = (
        project_path / "sia4010_artifacts" / "simulation"
        / "SIA4010_test_1_1E_template_apachesim.json"
    )
    if not audit_path.is_file():
        raise RuntimeError("No guarded Test 1E simulation audit is available")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    aps_path = Path(str(audit.get("results_path") or ""))
    if not aps_path.is_file():
        raise RuntimeError("The guarded Test 1E APS is missing")

    results = open_results_reader(aps_path.name)
    variables = get_available_variables(results)
    solar_gain_variable = _variable(variables, "Window solar gains", "z")
    incident_variable = _variable(variables, "Ext surface incident solar flux", "s")
    if solar_gain_variable is None:
        raise RuntimeError("Window solar gains is unavailable in the APS")
    room_rows = list(results.get_room_list() or [])
    room_id = room_rows[0][1] if room_rows and isinstance(room_rows[0], (list, tuple)) else None
    if room_id is None and room_rows and isinstance(room_rows[0], dict):
        room_id = room_rows[0].get("id") or room_rows[0].get("room_id")
    gain_tuple = _aps_tuple(solar_gain_variable)
    gains = convert_aps_series_to_metric(
        read_room_result(results, room_id, gain_tuple[0], gain_tuple[1], "z"),
        gain_tuple,
    )

    target_surfaces = [
        item for item in build_surface_inventory(project)
        if int(item.get("opening_count") or 0) == 2
        and abs(float(item.get("orientation") or 0.0) - 180.0) <= 1.0e-6
    ]
    incident = []
    incident_surface = None
    if incident_variable is not None and len(target_surfaces) == 1:
        incident_surface = target_surfaces[0]
        incident_tuple = _aps_tuple(incident_variable)
        room_candidates = [incident_surface.get("room_id"), room_id]
        for candidate in room_candidates:
            if candidate is None:
                continue
            raw = read_surface_result(
                results,
                candidate,
                incident_surface.get("aps_handle"),
                incident_tuple[0],
                incident_tuple[1],
            )
            incident = convert_aps_series_to_metric(raw, incident_tuple) if raw else []
            if incident:
                break

    paired_count = min(len(incident), len(gains))
    above = [index for index in range(paired_count) if incident[index] >= 150.0]
    below = [index for index in range(paired_count) if incident[index] < 150.0]
    payload = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "SOLAR_RESPONSE_RECORDED" if gains else "SOLAR_GAIN_SERIES_UNAVAILABLE",
        "project": str(project_path),
        "aps": str(aps_path),
        "results_per_hour": get_results_per_hour(results),
        "threshold_w_m2": 150.0,
        "window_solar_gain": {"variable": gain_tuple, "series": _summary(gains)},
        "exterior_plane_incident_solar": {
            "variable": _aps_tuple(incident_variable) if incident_variable else None,
            "surface": incident_surface,
            "series": _summary(incident),
        },
        "paired_response": {
            "count": paired_count,
            "samples_at_or_above_threshold": len(above),
            "samples_below_threshold": len(below),
            "solar_gain_at_or_above_threshold": _summary([gains[index] for index in above]),
            "solar_gain_below_threshold": _summary([gains[index] for index in below]),
        },
        "claim_guardrail": (
            "Read-only response evidence. APS exposes no qualified shade-state "
            "series, so threshold exposure must not be called proof of device state."
        ),
    }
    output = (
        project_path / "sia4010_artifacts" / "diagnostics"
        / "sia4010_test1e_solar_response_probe.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print("SIA 4010 TEST 1E SOLAR RESPONSE: {}".format(payload["status"]))
    print("APS: {}".format(aps_path))
    print("Window solar gain samples: {}; annual integrated value at native step: {}".format(len(gains), payload["window_solar_gain"]["series"]["sum"]))
    print("Exterior-plane incident samples: {}; >=150 W/m2: {}".format(len(incident), len(above)))
    if paired_count:
        print("Mean window gain when incident >=150: {}".format(payload["paired_response"]["solar_gain_at_or_above_threshold"]["mean"]))
        print("Mean window gain when incident <150: {}".format(payload["paired_response"]["solar_gain_below_threshold"]["mean"]))
    print("Report: {}".format(output))
    print("No VE model, construction, option or APS data was changed.")
    return output


if __name__ == "__main__":
    run()
