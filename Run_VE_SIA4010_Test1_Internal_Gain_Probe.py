"""Read-only verification of the ISO 52016 Test 1 internal sensible gain.

Run from the VE Scripts window with the generated Test 1 project open.  The
probe checks both the live room-level VE record and, when exposed, the
corresponding series in the qualified APS.  It never writes to the model or
the APS file.
"""

import json
import math
import os
import sys
from datetime import datetime


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

EXPECTED_POWER_W = 200.0
EXPECTED_HOURS = 8760
EXPECTED_ENERGY_KWH = EXPECTED_POWER_W * EXPECTED_HOURS / 1000.0
RELATIVE_TOLERANCE = 0.01


def _plain(value):
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _record_data(record):
    try:
        return dict(record.get())
    except Exception as exc:
        return {"read_error": str(exc), "python_type": str(type(record))}


def _indexed_number(data, plural_key, scalar_key):
    """Resolve VE's selected scalar from its dual-unit read-back dictionary."""

    values = data.get(plural_key)
    if isinstance(values, dict):
        selected = data.get("units_val", 0)
        for key in (selected, str(selected)):
            if key in values:
                try:
                    return float(values[key])
                except (TypeError, ValueError):
                    pass
    try:
        return float(data.get(scalar_key))
    except (TypeError, ValueError):
        return None


def _whole_room_sensible_w(data, floor_area_m2):
    value = _indexed_number(data, "max_sensible_gains", "max_sensible_gain")
    if value is None:
        return None
    unit = str(data.get("units_str") or "")
    unit_values = data.get("power_units") or data.get("units_strs")
    if isinstance(unit_values, dict):
        selected = data.get("units_val", 0)
        unit = str(unit_values.get(selected, unit_values.get(str(selected), unit)))
    normalized = unit.lower().replace(" ", "")
    if "/m" in normalized or "m²" in normalized or "m2" in normalized:
        return value * floor_area_m2
    return value


def _is_equipment_gain(data):
    text = " ".join(
        str(data.get(key) or "")
        for key in ("name", "type_str", "type_val")
    ).lower()
    return any(token in text for token in ("equipment", "power", "appliance"))


def _room_identity(item):
    if isinstance(item, dict):
        return item.get("id") or item.get("room_id"), str(
            item.get("name") or item.get("room_name") or ""
        )
    if isinstance(item, (list, tuple)):
        return (item[1] if len(item) > 1 else None), str(item[0] if item else "")
    return None, str(item)


def _metric_energy_kwh(values, unit, results_per_hour):
    if not values or results_per_hour <= 0:
        return None
    label = str(unit or "").lower()
    if "kwh" in label:
        return sum(values)
    if "wh" in label:
        return sum(values) / 1000.0
    if "kw" in label:
        return sum(values) / results_per_hour
    if "w" in label:
        return sum(values) / results_per_hour / 1000.0
    return None


def _candidate_score(variable):
    text = " ".join(
        str(variable.get(key) or "")
        for key in ("aps_varname", "name", "display_name")
    ).lower()
    score = 0
    for token, points in (
        ("internal", 8),
        ("casual", 8),
        ("equipment", 7),
        ("sensible", 5),
        ("gain", 4),
        ("power", 2),
    ):
        if token in text:
            score += points
    # Reject solar, ventilation and plant gain series even though they contain
    # the generic word "gain".
    if any(token in text for token in ("solar", "ventilation", "latent", "system")):
        score -= 12
    return score


def _close(actual, expected):
    return actual is not None and math.isclose(
        float(actual), float(expected), rel_tol=RELATIVE_TOLERANCE, abs_tol=0.2
    )


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
    bodies = []
    for model in list(project.models):
        try:
            bodies.extend(list(model.get_bodies(False)))
        except Exception:
            continue
    matching = [body for body in bodies if "SIA4010_TEST_1_" in str(body.name)]
    if len(matching) != 1:
        raise RuntimeError(
            "Expected exactly one generated SIA 4010 Test 1 room; found {}".format(
                len(matching)
            )
        )
    body = matching[0]
    room_data = body.get_room_data()
    general = dict(room_data.get_general())
    floor_area = float(general.get("floor_area") or 0.0)
    gain_rows = []
    equipment_rows = []
    for gain in list(room_data.get_internal_gains()):
        data = _record_data(gain)
        row = {
            "python_type": str(type(gain)),
            "data": _plain(data),
            "whole_room_sensible_w": _whole_room_sensible_w(data, floor_area),
        }
        gain_rows.append(row)
        if _is_equipment_gain(data):
            equipment_rows.append(row)

    live_power = None
    live_profile = None
    if len(equipment_rows) == 1:
        live_power = equipment_rows[0]["whole_room_sensible_w"]
        live_profile = str(equipment_rows[0]["data"].get("variation_profile") or "")
    live_pass = (
        len(equipment_rows) == 1
        and _close(live_power, EXPECTED_POWER_W)
        and live_profile.upper() == "ON"
    )

    audit_path = os.path.join(
        project_path,
        "sia4010_artifacts",
        "simulation",
        "SIA4010_test_1_640_apachesim_qualification.json",
    )
    audit = {}
    if os.path.isfile(audit_path):
        with open(audit_path, "r", encoding="utf-8") as handle:
            audit = json.load(handle)
    results_path = str(audit.get("results_path") or "")
    aps_name = os.path.basename(results_path)
    aps_candidates = []
    behavioral_matches = []
    if aps_name and os.path.isfile(results_path):
        results = open_results_reader(aps_name)
        results_per_hour = get_results_per_hour(results)
        try:
            aps_rooms = list(results.get_room_list() or [])
        except Exception:
            aps_rooms = []
        aps_room_id = None
        for item in aps_rooms:
            candidate_id, candidate_name = _room_identity(item)
            if candidate_name == str(body.name) or len(aps_rooms) == 1:
                aps_room_id = candidate_id
                break
        variables = sorted(
            get_available_variables(results), key=_candidate_score, reverse=True
        )
        for variable in variables:
            score = _candidate_score(variable)
            if score < 8 or aps_room_id is None:
                continue
            aps_var = str(variable.get("aps_varname") or variable.get("name") or "")
            display = str(variable.get("display_name") or aps_var)
            level = str(variable.get("model_level") or variable.get("level") or "z")
            raw = read_room_result(results, aps_room_id, aps_var, display, level)
            if not raw:
                continue
            aps_tuple = (
                aps_var,
                display,
                level,
                str(variable.get("resolved_metric_unit") or ""),
                float(variable.get("resolved_metric_divisor") or 1.0),
                float(variable.get("resolved_metric_offset") or 0.0),
            )
            values = convert_aps_series_to_metric(raw, aps_tuple)
            unit = aps_tuple[3]
            energy = _metric_energy_kwh(values, unit, results_per_hour)
            row = {
                "score": score,
                "aps_varname": aps_var,
                "display_name": display,
                "model_level": level,
                "metric_unit": unit,
                "count": len(values),
                "minimum": min(values),
                "maximum": max(values),
                "mean": sum(values) / len(values),
                "annual_energy_kwh": energy,
                "first_values": values[:8],
            }
            aps_candidates.append(row)
            if len(values) == EXPECTED_HOURS and _close(energy, EXPECTED_ENERGY_KWH):
                behavioral_matches.append(row)
            if len(aps_candidates) >= 30:
                break

    aps_pass = bool(behavioral_matches)
    if not live_pass:
        status = "FAIL"
    elif aps_pass:
        status = "PASS"
    else:
        status = "WARNING_APS_INTERNAL_GAIN_SERIES_NOT_CONFIRMED"

    report = {
        "schema_version": "1.0",
        "status": status,
        "project": {"name": str(project.name), "path": project_path},
        "room": {
            "id": str(body.id),
            "name": str(body.name),
            "floor_area_m2": floor_area,
        },
        "prescribed": {
            "sensible_internal_gain_w": EXPECTED_POWER_W,
            "schedule": "continuous 24 h/day for the full year",
            "annual_energy_kwh": EXPECTED_ENERGY_KWH,
            "source": "BS EN ISO 52016-1:2017, 7.2.2.13",
        },
        "live_room_check": {
            "status": "PASS" if live_pass else "FAIL",
            "equipment_gain_count": len(equipment_rows),
            "resolved_sensible_power_w": live_power,
            "variation_profile": live_profile,
            "all_internal_gains": gain_rows,
        },
        "aps_check": {
            "status": "PASS" if aps_pass else "NOT_CONFIRMED",
            "audit_path": audit_path,
            "aps_path": results_path,
            "behavioral_matches": behavioral_matches,
            "candidate_series": aps_candidates,
        },
        "interpretation": (
            "The prescribed 200 W continuous internal sensible gain is present "
            "in both the live room and APS behavior."
            if aps_pass and live_pass
            else "The live room is correct, but ResultsReader did not expose a "
            "qualified 1752 kWh internal-gain series; this is not proof that the "
            "solver omitted it."
            if live_pass
            else "The room-level equipment gain is absent, duplicated, not 200 W, "
            "or not assigned to the continuous ON profile."
        ),
        "model_or_aps_changed": False,
    }
    output_dir = os.path.join(project_path, "sia4010_artifacts", "diagnostics")
    os.makedirs(output_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(
        output_dir, "sia4010_test1_internal_gain_probe_{}.json".format(stamp)
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False, default=str)

    print("SIA 4010 TEST 1 INTERNAL-GAIN PROBE: {}".format(status))
    print("Case: test_1/640")
    print("Live room equipment gains: {}".format(len(equipment_rows)))
    print("Live resolved sensible power: {} W".format(live_power))
    print("Live profile: {}".format(live_profile or "<missing>"))
    print("Expected annual sensible gain: {} kWh".format(EXPECTED_ENERGY_KWH))
    print("APS behavioral matches: {}".format(len(behavioral_matches)))
    for item in behavioral_matches:
        print(
            "  {}: {} kWh ({})".format(
                item["display_name"], item["annual_energy_kwh"], item["metric_unit"]
            )
        )
    print("Report: {}".format(output_path))
    print("No VE model or APS data was changed.")
    return output_path


if __name__ == "__main__":
    run()
