"""Read-only probe for ISO 52016 hourly air-and-furniture capacity in IESVE.

Run this file from the VEScripts editor with a saved disposable Test 1 model
open. The probe never calls a VE setter. It records the current room value of
``furniture_mass_factor`` and the API members that may expose the ApLocate air
properties needed for an exact conversion.
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


def _sequence(value):
    """Return one VE collection as a normal Python list."""

    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return [value]


def _members(value):
    """Return non-private member names without invoking any member."""

    return sorted(
        name
        for name in dir(value)
        if not name.startswith("_")
        and any(token in name.casefold() for token in (
            "air", "density", "locate", "weather", "specific", "heat"
        ))
    )


def run():
    """Inspect the active Test 1 room and write a read-only diagnostic."""

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
    room_records = []
    for body in bodies:
        if not hasattr(body, "get_room_data"):
            continue
        try:
            room_data = body.get_room_data()
            general = dict(room_data.get_general())
            conditions = dict(room_data.get_room_conditions())
        except Exception as exc:
            room_records.append({
                "name": str(getattr(body, "name", "")),
                "read_error": str(exc),
            })
            continue
        area = general.get("floor_area", general.get("floor_area_m2"))
        volume = general.get("volume", general.get("room_volume"))
        room_records.append({
            "name": str(getattr(body, "name", "")),
            "id": str(getattr(body, "id", "")),
            "floor_area_readback_m2": area,
            "volume_readback_m3": volume,
            "furniture_mass_factor": conditions.get("furniture_mass_factor"),
            "room_condition_keys": sorted(str(key) for key in conditions),
        })

    rooms_with_factor = [
        room for room in room_records
        if room.get("furniture_mass_factor") is not None
    ]
    status = (
        "READY_FOR_EXACT_FACTOR_CALCULATION"
        if rooms_with_factor
        else "BLOCKED_FURNITURE_MASS_FACTOR_NOT_EXPOSED"
    )
    report = {
        "schema_version": "1.0",
        "status": status,
        "read_only": True,
        "project": {
            "name": str(getattr(project, "name", "") or ""),
            "path": project_path,
        },
        "iso_requirement": {
            "source": "BS EN ISO 52016-1:2017",
            "source_locator": "Clause 7.2.2.5, licensed evidence page 126",
            "air_and_furniture_areal_capacity_j_m2k": ISO_AREAL_CAPACITY_J_M2K,
            "test_cell_floor_area_m2": ISO_FLOOR_AREA_M2,
            "test_cell_volume_m3": ISO_VOLUME_M3,
            "total_target_capacity_j_k": (
                ISO_AREAL_CAPACITY_J_M2K * ISO_FLOOR_AREA_M2
            ),
        },
        "ies_mapping": {
            "definition": (
                "IES defines furniture_mass_factor as furniture thermal "
                "capacity divided by the thermal capacity of the room air."
            ),
            "required_formula": (
                "furniture_mass_factor = "
                "(10000 * floor_area) / (rho_air * cp_air * volume) - 1"
            ),
            "missing_exact_inputs": [
                "ApLocate reference air density rho_air in kg/m3",
                "ApacheSim air specific heat cp_air in J/(kg K)",
            ],
            "guardrail": (
                "Do not set a factor until both air properties are confirmed "
                "for the active VE/ApacheSim configuration."
            ),
        },
        "rooms": room_records,
        "candidate_api_members": {
            "iesve": _members(iesve),
            "project": _members(project),
            "model": _members(models[0]),
        },
    }

    output_dir = os.path.join(project_path, "sia4010_artifacts", "diagnostics")
    os.makedirs(output_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(
        output_dir,
        "sia4010_test1_internal_capacity_probe_{}.json".format(stamp),
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False, default=str)

    print("READ-ONLY SIA 4010 TEST 1 INTERNAL-CAPACITY PROBE: {}".format(status))
    print("Project: {}".format(report["project"]["name"]))
    print("Rooms inspected: {}".format(len(room_records)))
    for room in rooms_with_factor:
        print(
            "{} furniture_mass_factor: {}".format(
                room["name"], room["furniture_mass_factor"]
            )
        )
    print("Report: {}".format(output_path))
    print("No VE model or project data was changed.")
    return output_path


if __name__ == "__main__":
    run()
