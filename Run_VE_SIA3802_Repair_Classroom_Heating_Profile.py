"""Repair the reviewed classroom heating availability profile in IESVE 2025.

The active disposable project must contain exactly one
``SIA2024_4.01_CLASSROOM_REFERENCE`` template assigned to exactly three rooms.
The script changes only the template heating availability profile from the
continuous ``ON`` fallback to the existing native ``HVSS0001`` System extended
hours profile.  It does not change setpoints, heating/cooling capacities,
ventilation, infiltration, gains, Apache systems or the APS file.

The operation is guarded by exact preconditions, user confirmation, native
read-back and automatic rollback to ``ON`` if verification fails.  The project
is deliberately not saved by the script.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TEMPLATE_NAME = "SIA2024_4.01_CLASSROOM_REFERENCE"
EXPECTED_ROOM_IDS = {"SP000000", "SP000001", "SP000002"}
SOURCE_PROFILE = "ON"
TARGET_PROFILE = "HVSS0001"
TARGET_PROFILE_REFERENCE = "System extended hours"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "sia3802_classroom_heating_repair.json"


def _native(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(key): _native(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_native(item) for item in value]
    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, (bool, int, float, str)):
        return {"value": enum_value, "display": str(value)}
    return str(value)


def _write(payload: dict[str, Any]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT_PATH.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(OUTPUT_PATH)


def _templates(project: Any) -> dict[Any, Any]:
    errors = []
    for arguments in ((False, False), (False,)):
        try:
            return dict(project.thermal_templates(*arguments))
        except Exception as exc:
            errors.append("{}: {}".format(arguments, exc))
    raise RuntimeError("Cannot read thermal templates: {}".format(" | ".join(errors)))


def _find_template(project: Any) -> tuple[Any, Any]:
    matches = [
        (handle, template)
        for handle, template in _templates(project).items()
        if str(getattr(template, "name", "")) == TEMPLATE_NAME
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "Expected exactly one {!r} template; found {}.".format(
                TEMPLATE_NAME, len(matches)
            )
        )
    return matches[0]


def _assigned_rooms(model: Any) -> list[Any]:
    rooms = []
    for body in model.get_bodies(False):
        try:
            general = dict(body.get_room_data().get_general())
        except Exception:
            continue
        if str(general.get("thermal_template_name") or "") == TEMPLATE_NAME:
            rooms.append(body)
    return rooms


def _profile(project: Any, profile_id: str) -> dict[str, Any]:
    matches = []
    for collection_index, collection in enumerate(project.profiles()):
        for native_id, profile in dict(collection).items():
            if str(native_id) != profile_id:
                continue
            matches.append((collection_index, native_id, profile))
    if len(matches) != 1:
        raise RuntimeError(
            "Expected exactly one native profile {!r}; found {}.".format(
                profile_id, len(matches)
            )
        )
    collection_index, native_id, profile = matches[0]
    reference = str(getattr(profile, "reference", None) or "")
    data = _native(profile.get_data())
    if reference != TARGET_PROFILE_REFERENCE:
        raise RuntimeError(
            "Profile {!r} is {!r}, not the audited {!r}.".format(
                profile_id, reference, TARGET_PROFILE_REFERENCE
            )
        )
    return {
        "collection_index": collection_index,
        "profile_id": str(native_id),
        "reference": reference,
        "python_type": str(type(profile)),
        "data": data,
    }


def _snapshot(template: Any, rooms: list[Any]) -> dict[str, Any]:
    template_conditions = dict(template.get_room_conditions())
    template_systems = dict(template.get_apache_systems())
    room_records = []
    for body in rooms:
        room_data = body.get_room_data()
        general = dict(room_data.get_general())
        conditions = dict(room_data.get_room_conditions())
        systems = dict(room_data.get_apache_systems())
        room_records.append(
            {
                "name": str(getattr(body, "name", "")),
                "id": str(general.get("id") or getattr(body, "id", "")),
                "thermal_template_name": str(
                    general.get("thermal_template_name") or ""
                ),
                "heating_profile": _native(conditions.get("heating_profile")),
                "heating_profile_from_template": _native(
                    conditions.get("heating_profile_from_template")
                ),
                "heating_setpoint": _native(conditions.get("heating_setpoint")),
                "plant_profile_type": _native(conditions.get("plant_profile_type")),
                "heating_capacity_unlimited": _native(
                    systems.get("heating_capacity_unlimited")
                ),
                "heating_capacity_value": _native(
                    systems.get("heating_capacity_value")
                ),
                "system_air_minimum_flowrate": _native(
                    systems.get("system_air_minimum_flowrate")
                ),
            }
        )
    return {
        "template": {
            "heating_profile": _native(template_conditions.get("heating_profile")),
            "heating_setpoint": _native(template_conditions.get("heating_setpoint")),
            "cooling_profile": _native(template_conditions.get("cooling_profile")),
            "plant_profile_type": _native(
                template_conditions.get("plant_profile_type")
            ),
            "heating_capacity_unlimited": _native(
                template_systems.get("heating_capacity_unlimited")
            ),
            "heating_capacity_value": _native(
                template_systems.get("heating_capacity_value")
            ),
            "system_air_minimum_flowrate": _native(
                template_systems.get("system_air_minimum_flowrate")
            ),
        },
        "rooms": room_records,
    }


def _assert_preconditions(before: dict[str, Any]) -> None:
    rooms = before["rooms"]
    room_ids = {str(room["id"]) for room in rooms}
    if len(rooms) != 3 or room_ids != EXPECTED_ROOM_IDS:
        raise RuntimeError(
            "Repair scope mismatch: expected room IDs {}, found {}.".format(
                sorted(EXPECTED_ROOM_IDS), sorted(room_ids)
            )
        )
    if before["template"]["heating_profile"] != SOURCE_PROFILE:
        raise RuntimeError(
            "Template heating profile is {!r}, expected {!r}; no change made.".format(
                before["template"]["heating_profile"], SOURCE_PROFILE
            )
        )
    if before["template"]["heating_setpoint"] != 21.0:
        raise RuntimeError("Template heating setpoint is no longer the audited 21 C.")
    if before["template"]["system_air_minimum_flowrate"] != 0.0:
        raise RuntimeError("System outdoor-air flow is no longer zero; audit first.")
    for room in rooms:
        if room["heating_profile"] != SOURCE_PROFILE:
            raise RuntimeError(
                "Room {!r} no longer inherits the audited ON profile.".format(
                    room["name"]
                )
            )
        if room["heating_profile_from_template"] is not True:
            raise RuntimeError(
                "Room {!r} has a direct heating-profile override.".format(room["name"])
            )


def _verify(before: dict[str, Any], after: dict[str, Any]) -> None:
    if after["template"]["heating_profile"] != TARGET_PROFILE:
        raise RuntimeError("Template did not retain the reviewed heating profile.")
    for room in after["rooms"]:
        if room["heating_profile"] != TARGET_PROFILE:
            raise RuntimeError(
                "Room {!r} did not inherit the reviewed heating profile.".format(
                    room["name"]
                )
            )
        if room["heating_profile_from_template"] is not True:
            raise RuntimeError(
                "Room {!r} lost template inheritance.".format(room["name"])
            )
    unchanged_template_fields = (
        "heating_setpoint",
        "cooling_profile",
        "plant_profile_type",
        "heating_capacity_unlimited",
        "heating_capacity_value",
        "system_air_minimum_flowrate",
    )
    drift = {
        key: {"before": before["template"][key], "after": after["template"][key]}
        for key in unchanged_template_fields
        if before["template"][key] != after["template"][key]
    }
    if drift:
        raise RuntimeError("Unrequested template-field drift: {}".format(drift))


def _confirm() -> bool:
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    approved = messagebox.askyesno(
        "Repair classroom heating availability",
        (
            "Exactly one VE value will change:\n\n"
            "SIA2024_4.01_CLASSROOM_REFERENCE\n"
            "Heating Profile: ON -> HVSS0001 (System extended hours)\n\n"
            "The 21 C setpoint, unlimited capacities, cooling, ventilation, "
            "infiltration, gains and Apache system will remain unchanged.\n\n"
            "The project will NOT be saved automatically. Apply now?"
        ),
        parent=root,
    )
    root.destroy()
    return bool(approved)


def run() -> None:
    try:
        import iesve  # type: ignore
    except Exception as exc:
        raise RuntimeError("Run this file inside IESVE 2025 VEScripts.") from exc

    project = iesve.VEProject.get_current_project()
    if not project or not getattr(project, "models", None):
        raise RuntimeError("Open SIA_compatible_model_TEST first.")
    project_path = Path(str(getattr(project, "path", "") or ""))
    project_identity = "{} {}".format(
        str(getattr(project, "name", "")), str(project_path)
    ).upper()
    if "_TEST" not in project_identity:
        raise RuntimeError("Open a disposable project copy containing _TEST first.")

    model = project.models[0]
    _, template = _find_template(project)
    rooms = _assigned_rooms(model)
    target_profile = _profile(project, TARGET_PROFILE)
    before = _snapshot(template, rooms)
    _assert_preconditions(before)
    report = {
        "schema_version": "1.0",
        "operation": "sia3802_classroom_heating_profile_repair",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_name": str(getattr(project, "name", "")),
        "project_path": str(getattr(project, "path", "")),
        "template_name": TEMPLATE_NAME,
        "requested_change": {
            "field": "heating_profile",
            "before": SOURCE_PROFILE,
            "after": TARGET_PROFILE,
        },
        "target_profile": target_profile,
        "before": before,
        "status": "READY_FOR_CONFIRMATION",
        "project_saved_by_script": False,
        "simulation_run_by_script": False,
        "compliance_claim": "NOT_GRANTED",
    }
    _write(report)

    if not _confirm():
        report["status"] = "CANCELLED_NO_VE_CHANGE"
        _write(report)
        print("SIA 380/2 HEATING PROFILE REPAIR: CANCELLED — NO VE CHANGE")
        print("JSON: {}".format(OUTPUT_PATH))
        return

    try:
        template.set_room_conditions({"heating_profile": TARGET_PROFILE})
        if hasattr(template, "apply_changes"):
            template.apply_changes()
        _, refreshed_template = _find_template(project)
        refreshed_rooms = _assigned_rooms(model)
        after = _snapshot(refreshed_template, refreshed_rooms)
        _verify(before, after)
    except Exception as exc:
        rollback_error = None
        try:
            _, rollback_template = _find_template(project)
            rollback_template.set_room_conditions({"heating_profile": SOURCE_PROFILE})
            if hasattr(rollback_template, "apply_changes"):
                rollback_template.apply_changes()
        except Exception as rollback_exc:
            rollback_error = "{}: {}".format(type(rollback_exc).__name__, rollback_exc)
        report["status"] = "FAILED_ROLLBACK_ATTEMPTED"
        report["error"] = "{}: {}".format(type(exc).__name__, exc)
        report["rollback_error"] = rollback_error
        _write(report)
        raise RuntimeError(
            "Repair verification failed; rollback attempted. Close VE without "
            "saving and inspect {}.".format(OUTPUT_PATH)
        ) from exc

    report["status"] = "APPLIED_AND_READBACK_VERIFIED"
    report["after"] = after
    report["verified_change_count"] = 1
    report["unchanged_families"] = [
        "heating_setpoint",
        "heating_capacity",
        "cooling",
        "ventilation",
        "infiltration",
        "internal_gains",
        "apache_system_assignment",
    ]
    report["next_action"] = (
        "Save the VE project copy, run annual ApacheSim with the existing weather "
        "and 30-minute timestep, then run the APS diagnostic and compliance hub."
    )
    _write(report)
    print("=" * 78)
    print("SIA 380/2 HEATING PROFILE REPAIR: APPLIED_AND_READBACK_VERIFIED")
    print("Template: {}".format(TEMPLATE_NAME))
    print("Heating Profile: {} -> {} ({})".format(
        SOURCE_PROFILE, TARGET_PROFILE, TARGET_PROFILE_REFERENCE
    ))
    print("Verified inherited rooms: {}".format(
        ", ".join(room["name"] for room in after["rooms"])
    ))
    print("Capacities, setpoints and ventilation: UNCHANGED")
    print("Project saved by script: NO")
    print("JSON: {}".format(OUTPUT_PATH))
    print("=" * 78)


if __name__ == "__main__":
    run()
