"""Read-only IESVE probe for the remaining ISO Test 1 runtime bindings.

Run from VEScripts with a saved disposable Test 1 project containing exactly
one generated room.  No VE setter, simulation or save operation is called.
"""

import json
import os
import sys
from datetime import datetime


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

ISO_AREAL_CAPACITY_J_M2K = 10000.0
ISO_FLOOR_AREA_M2 = 48.0
ISO_VOLUME_M3 = 129.6
ISO_HEATING_CAPACITY_W = 1000000.0
ISO_COOLING_CAPACITY_W = 1000000.0


def _sequence(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return [value]


def _candidate_members(value):
    tokens = (
        "air", "density", "locate", "weather", "specific", "heat",
        "capacity", "furniture", "system", "condition",
    )
    return sorted(
        name for name in dir(value)
        if not name.startswith("_")
        and any(token in name.casefold() for token in tokens)
    )


def _selected(mapping, keys):
    return {key: mapping.get(key) for key in keys if key in mapping}


def run():
    try:
        import iesve  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Run this script from the IESVE VEScripts editor.") from exc

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("Open a saved disposable VE project first.")
    project_path = str(getattr(project, "path", "") or "")
    if not os.path.isdir(project_path):
        raise RuntimeError("Save the disposable VE project before running this probe.")

    models = _sequence(getattr(project, "models", []))
    if not models:
        raise RuntimeError("The active project exposes no VE model.")
    bodies = _sequence(models[0].get_bodies(False))
    rooms = []
    for body in bodies:
        if not hasattr(body, "get_room_data"):
            continue
        try:
            room_data = body.get_room_data()
            general = dict(room_data.get_general())
            conditions = dict(room_data.get_room_conditions())
            systems = dict(room_data.get_apache_systems())
        except Exception as exc:
            rooms.append({
                "name": str(getattr(body, "name", "")),
                "read_error": str(exc),
            })
            continue
        rooms.append({
            "name": str(getattr(body, "name", "")),
            "id": str(getattr(body, "id", "")),
            "floor_area_readback_m2": general.get(
                "floor_area", general.get("floor_area_m2")
            ),
            "volume_readback_m3": general.get(
                "volume", general.get("room_volume")
            ),
            "room_conditions": _selected(
                conditions,
                (
                    "furniture_mass_factor", "heating_setpoint",
                    "cooling_setpoint", "heating_profile", "cooling_profile",
                    "solar_reflected_fraction",
                ),
            ),
            "apache_systems": _selected(
                systems,
                (
                    "conditioned", "HVAC_system", "HVAC_methodology",
                    "heating_capacity_unlimited", "heating_capacity_unit",
                    "heating_capacity_value", "cooling_capacity_unlimited",
                    "cooling_capacity_unit", "cooling_capacity_value",
                ),
            ),
            "room_condition_keys": sorted(str(key) for key in conditions),
            "apache_system_keys": sorted(str(key) for key in systems),
            "candidate_room_data_members": _candidate_members(room_data),
            "candidate_body_members": _candidate_members(body),
        })

    usable = [room for room in rooms if "read_error" not in room]
    furniture_exposed = bool(usable) and all(
        "furniture_mass_factor" in room["room_conditions"] for room in usable
    )
    capacity_keys = {
        "heating_capacity_unlimited", "heating_capacity_unit",
        "heating_capacity_value", "cooling_capacity_unlimited",
        "cooling_capacity_unit", "cooling_capacity_value",
    }
    capacities_exposed = bool(usable) and all(
        capacity_keys <= set(room["apache_systems"]) for room in usable
    )
    status = (
        "READY_FOR_CONTROLLED_BINDING_REVIEW"
        if furniture_exposed and capacities_exposed
        else "PARTIAL_RUNTIME_BINDINGS"
        if usable
        else "BLOCKED_NO_READABLE_ROOM"
    )

    report = {
        "schema_version": "1.0",
        "status": status,
        "read_only": True,
        "project": {
            "name": str(getattr(project, "name", "") or ""),
            "path": project_path,
        },
        "iso_contract": {
            "source": "BS EN ISO 52016-1:2017",
            "air_and_furniture_areal_capacity_j_m2k": ISO_AREAL_CAPACITY_J_M2K,
            "floor_area_m2": ISO_FLOOR_AREA_M2,
            "volume_m3": ISO_VOLUME_M3,
            "total_air_and_furniture_capacity_j_k": (
                ISO_AREAL_CAPACITY_J_M2K * ISO_FLOOR_AREA_M2
            ),
            "heating_capacity_w": ISO_HEATING_CAPACITY_W,
            "cooling_capacity_w": ISO_COOLING_CAPACITY_W,
            "source_locators": [
                "Clause 7.2.2.5, page 126",
                "Clause 7.2.2.16, page 130",
            ],
        },
        "mapping_contract": {
            "furniture_formula": (
                "furniture_mass_factor = "
                "(10000 * floor_area) / (rho_air * cp_air * volume) - 1"
            ),
            "important_runtime_difference": (
                "ApacheSim evaluates air capacity at room conditions; one "
                "constant furniture factor can match the ISO capacity only "
                "at a declared reference air state. Clause 7.2 result "
                "comparison therefore remains mandatory."
            ),
            "setter_guardrail": (
                "Do not set capacity units, values or furniture factor until "
                "the exact read-back types in this report are reviewed."
            ),
        },
        "bindings_exposed": {
            "furniture_mass_factor": furniture_exposed,
            "heating_and_cooling_capacity_fields": capacities_exposed,
        },
        "rooms": rooms,
        "candidate_api_members": {
            "iesve": _candidate_members(iesve),
            "project": _candidate_members(project),
            "model": _candidate_members(models[0]),
        },
    }

    output_dir = os.path.join(project_path, "sia4010_artifacts", "diagnostics")
    os.makedirs(output_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(
        output_dir,
        "sia4010_test1_runtime_input_probe_{}.json".format(stamp),
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False, default=str)

    print("READ-ONLY SIA 4010 TEST 1 RUNTIME-INPUT PROBE: {}".format(status))
    print("Project: {}".format(report["project"]["name"]))
    print("Rooms inspected: {}".format(len(rooms)))
    print("Furniture field exposed: {}".format(furniture_exposed))
    print("Capacity fields exposed: {}".format(capacities_exposed))
    print("Report: {}".format(output_path))
    print("No VE model, template, system, weather or APS data was changed.")
    return output_path


if __name__ == "__main__":
    run()
