"""Read-only live-room and APS verification of Test 1 infiltration."""

import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

EXPECTED_ACH = 0.41
EXPECTED_VOLUME_M3 = 129.6
EXPECTED_AREA_M2 = 48.0
EXPECTED_L_S = EXPECTED_ACH * EXPECTED_VOLUME_M3 / 3.6


def _room_id(item):
    if isinstance(item, dict):
        return item.get("id") or item.get("room_id")
    if isinstance(item, (list, tuple)) and len(item) >= 2:
        return item[1]
    return None


def _to_l_s(value, unit):
    label = str(unit or "").lower().replace(" ", "")
    if "l/s" in label:
        return value
    if "m³/s" in label or "m3/s" in label:
        return value * 1000.0
    if "m³/h" in label or "m3/h" in label:
        return value * 1000.0 / 3600.0
    return None


def _selected_flow(data):
    value = data.get("max_flow")
    if value is not None:
        try:
            return float(value)
        except (TypeError, ValueError):
            pass
    values = data.get("max_flows")
    if isinstance(values, dict):
        selected = data.get("units_val", 0)
        for key in (selected, str(selected)):
            if key in values:
                try:
                    return float(values[key])
                except (TypeError, ValueError):
                    pass
    return None


def _total_flow_l_s(data):
    """Resolve the canonical total flow from VE's parallel unit values.

    ``RoomAirExchange.get()`` exposes the same flow in five units.  ``units_val``
    only records the unit last displayed by the UI; a per-person value must not
    be interpreted as an already-total l/s value merely because its label also
    contains ``l/s``.  Unit index 1 is VE's canonical total-l/s representation.
    """
    values = data.get("max_flows")
    labels = data.get("units_strs")
    if isinstance(values, dict) and isinstance(labels, dict):
        for key in (1, "1"):
            label = str(labels.get(key, "")).lower().replace(" ", "")
            if key in values and label == "l/s":
                try:
                    return float(values[key])
                except (TypeError, ValueError):
                    return None
    value = _selected_flow(data)
    unit = str(data.get("units_str") or "")
    return _to_l_s(value, unit) if value is not None else None


def _active_case(project_path):
    """Return the active Test 1 case without assuming the historical 640 case."""
    scenario_path = Path(project_path) / "sia_model_scenario.json"
    if not scenario_path.is_file():
        raise RuntimeError("Missing active-case scenario: {}".format(scenario_path))
    with scenario_path.open("r", encoding="utf-8") as handle:
        scenario = json.load(handle)
    selection = scenario.get("selection") or {}
    variant = str(selection.get("variant") or scenario.get("variant") or "")
    case_id = str(
        selection.get("case_id")
        or scenario.get("case_id")
        or scenario.get("case")
        or ""
    )
    if variant != "test_1" or not case_id:
        raise RuntimeError(
            "Expected an active Test 1 scenario; received {!r}/{!r}".format(
                variant, case_id
            )
        )
    return variant, case_id


def _latest_aps_audit(project_path, variant, case_id):
    """Find the newest simulation receipt that points to an existing APS file."""
    simulation_dir = Path(project_path) / "sia4010_artifacts" / "simulation"
    if not simulation_dir.is_dir():
        return None, None
    candidates = []
    case_token = "{}_{}_".format(variant, case_id).lower()
    for audit_path in simulation_dir.glob("*.json"):
        try:
            with audit_path.open("r", encoding="utf-8") as handle:
                audit = json.load(handle)
        except (OSError, ValueError):
            continue
        aps_path = str(
            audit.get("results_path")
            or audit.get("aps_path")
            or audit.get("aps")
            or ""
        )
        if not aps_path or not os.path.isfile(aps_path):
            continue
        name_matches = case_token in audit_path.name.lower()
        candidates.append((name_matches, audit_path.stat().st_mtime, audit_path, aps_path))
    if not candidates:
        return None, None
    _, _, audit_path, aps_path = max(candidates, key=lambda item: (item[0], item[1]))
    return str(audit_path), aps_path


def run():
    import iesve

    from swiss_sia.simulation_results import (
        convert_aps_series_to_metric,
        get_available_variables,
        get_results_per_hour,
        open_results_reader,
        read_room_result,
    )

    project = iesve.VEProject.get_current_project()
    project_path = str(project.path)
    variant, case_id = _active_case(project_path)
    case_label = "{}/{}".format(variant, case_id)
    bodies = []
    for model in list(project.models):
        bodies.extend(list(model.get_bodies(False)))
    rooms = [body for body in bodies if "SIA4010_TEST_1_" in str(body.name)]
    if len(rooms) != 1:
        raise RuntimeError("Expected one generated Test 1 room; found {}".format(len(rooms)))
    body = rooms[0]
    room_data = body.get_room_data()
    general = dict(room_data.get_general())
    floor_area = float(general.get("floor_area") or 0.0)
    live_rows = []
    infiltration_rows = []
    for record in list(room_data.get_air_exchanges()):
        data = dict(record.get())
        row = {"python_type": str(type(record)), "data": data}
        live_rows.append(row)
        text = "{} {}".format(data.get("name", ""), data.get("type_str", "")).lower()
        if "infiltration" in text:
            infiltration_rows.append(row)
    live_l_s = None
    if len(infiltration_rows) == 1:
        data = infiltration_rows[0]["data"]
        live_l_s = _total_flow_l_s(data)
        live_profile = str(data.get("variation_profile") or "")
    else:
        live_profile = ""
    live_pass = (
        len(infiltration_rows) == 1
        and live_l_s is not None
        and math.isclose(live_l_s, EXPECTED_L_S, rel_tol=0.001, abs_tol=0.01)
        and live_profile.upper() == "ON"
    )

    audit_path, aps_path = _latest_aps_audit(
        project_path, variant, case_id
    )
    if aps_path is None:
        status = "LIVE_INPUT_VERIFIED_AWAITING_APS" if live_pass else "FAIL"
        report = {
            "schema_version": "1.1",
            "status": status,
            "case": case_label,
            "prescribed": {
                "air_changes_per_hour": EXPECTED_ACH,
                "room_volume_m3": EXPECTED_VOLUME_M3,
                "flow_l_s": EXPECTED_L_S,
                "source": "BS EN ISO 52016-1:2017 Clause 7.2.2.14",
            },
            "live_room": {
                "status": "PASS" if live_pass else "FAIL",
                "floor_area_m2": floor_area,
                "resolved_flow_l_s": live_l_s,
                "profile": live_profile,
                "air_exchanges": live_rows,
            },
            "aps": {
                "status": "NOT_RUN",
                "path": None,
                "reason": "No active-case APS simulation receipt is available yet",
            },
            "model_or_aps_changed": False,
        }
        output_dir = os.path.join(project_path, "sia4010_artifacts", "diagnostics")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(
            output_dir,
            "sia4010_test1_infiltration_probe_{}.json".format(
                datetime.now().strftime("%Y%m%d_%H%M%S")
            ),
        )
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False, default=str)
        print("SIA 4010 TEST 1 INFILTRATION PROBE: {}".format(status))
        print("Case: {}".format(case_label))
        print("Expected: {:.3f} l/s (0.41 ACH)".format(EXPECTED_L_S))
        print("Live room: {} l/s; profile={}".format(live_l_s, live_profile))
        print("APS: not run for this active case")
        print("Report: {}".format(output_path))
        print("No VE model or APS data was changed.")
        return output_path

    results = open_results_reader(os.path.basename(aps_path))
    aps_rooms = list(results.get_room_list() or [])
    if len(aps_rooms) != 1:
        raise RuntimeError("Expected one APS room; found {}".format(len(aps_rooms)))
    aps_room_id = _room_id(aps_rooms[0])
    variable = None
    for item in get_available_variables(results):
        if (
            str(item.get("aps_varname") or item.get("name") or "").strip().lower()
            == "infiltration"
            and str(item.get("model_level") or item.get("level") or "z").lower()
            in ("", "z")
        ):
            variable = item
            break
    if variable is None:
        raise RuntimeError("APS room variable 'Infiltration' was not found")
    aps_name = str(variable.get("aps_varname") or variable.get("name"))
    display = str(variable.get("display_name") or aps_name)
    level = str(variable.get("model_level") or variable.get("level") or "z")
    aps_tuple = (
        aps_name,
        display,
        level,
        str(variable.get("resolved_metric_unit") or ""),
        float(variable.get("resolved_metric_divisor") or 1.0),
        float(variable.get("resolved_metric_offset") or 0.0),
    )
    raw = read_room_result(results, aps_room_id, aps_name, display, level)
    values = convert_aps_series_to_metric(raw, aps_tuple)
    results_per_hour = get_results_per_hour(results)
    expected_count = int(round(8760 * results_per_hour))
    values_l_s = [_to_l_s(value, aps_tuple[3]) for value in values]
    unit_supported = bool(values_l_s) and all(value is not None for value in values_l_s)
    aps_pass = (
        len(values_l_s) == expected_count
        and unit_supported
        and math.isclose(min(values_l_s), EXPECTED_L_S, rel_tol=0.001, abs_tol=0.01)
        and math.isclose(max(values_l_s), EXPECTED_L_S, rel_tol=0.001, abs_tol=0.01)
    )
    status = "PASS" if live_pass and aps_pass else "FAIL"
    report = {
        "schema_version": "1.1",
        "status": status,
        "case": case_label,
        "prescribed": {
            "air_changes_per_hour": EXPECTED_ACH,
            "room_volume_m3": EXPECTED_VOLUME_M3,
            "flow_l_s": EXPECTED_L_S,
            "source": "BS EN ISO 52016-1:2017 Clause 7.2.2.14",
        },
        "live_room": {
            "status": "PASS" if live_pass else "FAIL",
            "floor_area_m2": floor_area,
            "resolved_flow_l_s": live_l_s,
            "profile": live_profile,
            "air_exchanges": live_rows,
        },
        "aps": {
            "status": "PASS" if aps_pass else "FAIL",
            "path": aps_path,
            "audit_path": audit_path,
            "variable": {
                "aps_varname": aps_name,
                "display_name": display,
                "metric_unit": aps_tuple[3],
            },
            "count": len(values_l_s),
            "expected_count": expected_count,
            "minimum_l_s": min(values_l_s) if unit_supported else None,
            "maximum_l_s": max(values_l_s) if unit_supported else None,
            "mean_l_s": (
                sum(values_l_s) / len(values_l_s) if unit_supported else None
            ),
        },
        "model_or_aps_changed": False,
    }
    output_dir = os.path.join(project_path, "sia4010_artifacts", "diagnostics")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(
        output_dir,
        "sia4010_test1_infiltration_probe_{}.json".format(
            datetime.now().strftime("%Y%m%d_%H%M%S")
        ),
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False, default=str)

    print("SIA 4010 TEST 1 INFILTRATION PROBE: {}".format(status))
    print("Case: {}".format(case_label))
    print("Expected: {:.3f} l/s (0.41 ACH)".format(EXPECTED_L_S))
    print("Live room: {} l/s; profile={}".format(live_l_s, live_profile))
    print(
        "APS: min={} l/s; max={} l/s; values={}".format(
            report["aps"]["minimum_l_s"],
            report["aps"]["maximum_l_s"],
            report["aps"]["count"],
        )
    )
    print("Report: {}".format(output_path))
    print("No VE model or APS data was changed.")
    return output_path


if __name__ == "__main__":
    run()
