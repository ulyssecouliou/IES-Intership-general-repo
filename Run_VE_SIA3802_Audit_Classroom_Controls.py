"""Read-only audit of the three rooms using the SIA 2024 classroom template.

Run this launcher from the IESVE 2025 VEScripts window while the client model
copy is open.  It calls getters only: no VE setter, project save or simulation
method is invoked.  The resulting JSON contains the exact native values needed
to prepare a read-back-verified repair without guessing a profile or capacity.
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
TARGET_ROOMS = ("Office_01", "Corridor", "Office_02")
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "sia3802_classroom_controls_audit.json"


def _native(value: Any) -> Any:
    """Convert Boost.Python values to deterministic JSON-compatible values."""

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


def _record(record: Any) -> dict[str, Any]:
    getter = getattr(record, "get", None)
    if not callable(getter):
        return {"python_type": str(type(record)), "value": _native(record)}
    try:
        payload = dict(getter())
    except Exception as exc:  # diagnostic boundary
        return {
            "python_type": str(type(record)),
            "read_error": "{}: {}".format(type(exc).__name__, exc),
        }
    return {"python_type": str(type(record)), "data": _native(payload)}


def _template_collection(project: Any) -> dict[Any, Any]:
    errors = []
    for arguments in ((False, False), (False,)):
        try:
            return dict(project.thermal_templates(*arguments))
        except Exception as exc:
            errors.append("{}: {}".format(arguments, exc))
    raise RuntimeError("Cannot read VE thermal templates: {}".format(" | ".join(errors)))


def _profile_identity(profile_id: Any, profile: Any) -> str:
    return str(
        getattr(profile, "reference", None)
        or getattr(profile, "name", None)
        or profile_id
    )


def _profile_inventory(project: Any) -> list[dict[str, Any]]:
    inventory = []
    try:
        collections = list(project.profiles())
    except Exception as exc:
        return [{"read_error": "{}: {}".format(type(exc).__name__, exc)}]
    for collection_index, collection in enumerate(collections):
        for profile_id, profile in dict(collection).items():
            identity = _profile_identity(profile_id, profile)
            if not (
                identity.startswith("SIA2024_4P01")
                or identity in {"ON", "OFF"}
            ):
                continue
            item = {
                "collection_index": collection_index,
                "profile_id": str(profile_id),
                "identity": identity,
                "python_type": str(type(profile)),
            }
            try:
                item["data"] = _native(profile.get_data())
            except Exception as exc:
                item["read_error"] = "{}: {}".format(type(exc).__name__, exc)
            inventory.append(item)
    return inventory


def _template_snapshot(handle: Any, template: Any) -> dict[str, Any]:
    snapshot = {
        "handle": str(handle),
        "name": str(getattr(template, "name", "")),
        "python_type": str(type(template)),
    }
    for key, getter_name in (
        ("room_conditions", "get_room_conditions"),
        ("apache_systems", "get_apache_systems"),
    ):
        getter = getattr(template, getter_name, None)
        try:
            snapshot[key] = _native(dict(getter())) if callable(getter) else None
        except Exception as exc:
            snapshot[key + "_read_error"] = "{}: {}".format(type(exc).__name__, exc)
    try:
        snapshot["air_exchanges"] = [
            _record(item) for item in list(template.get_air_exchanges())
        ]
    except Exception as exc:
        snapshot["air_exchanges_read_error"] = "{}: {}".format(type(exc).__name__, exc)
    return snapshot


def _room_snapshot(body: Any) -> dict[str, Any]:
    room = {
        "name": str(getattr(body, "name", "")),
        "id": str(getattr(body, "id", "")),
        "python_type": str(type(body)),
    }
    try:
        room["areas"] = _native(dict(body.get_areas()))
    except Exception as exc:
        room["areas_read_error"] = "{}: {}".format(type(exc).__name__, exc)
    data = body.get_room_data()
    room["room_data_python_type"] = str(type(data))
    for key, getter_name in (
        ("general", "get_general"),
        ("room_conditions", "get_room_conditions"),
        ("apache_systems", "get_apache_systems"),
    ):
        getter = getattr(data, getter_name, None)
        try:
            room[key] = _native(dict(getter())) if callable(getter) else None
        except Exception as exc:
            room[key + "_read_error"] = "{}: {}".format(type(exc).__name__, exc)
    try:
        room["air_exchanges"] = [_record(item) for item in data.get_air_exchanges()]
    except Exception as exc:
        room["air_exchanges_read_error"] = "{}: {}".format(type(exc).__name__, exc)
    room["setter_capabilities"] = {
        "set_room_conditions": callable(getattr(data, "set_room_conditions", None)),
        "set_apache_systems": callable(getattr(data, "set_apache_systems", None)),
    }
    return room


def _summary(template: dict[str, Any], rooms: list[dict[str, Any]]) -> dict[str, Any]:
    conditions = template.get("room_conditions") or {}
    systems = template.get("apache_systems") or {}
    room_names = {item.get("name") for item in rooms}
    profile = conditions.get("heating_profile")
    return {
        "all_target_rooms_found": room_names == set(TARGET_ROOMS),
        "missing_target_rooms": sorted(set(TARGET_ROOMS) - room_names),
        "template_heating_profile": _native(profile),
        "continuous_heating_fallback_detected": str(profile).strip().upper() == "ON",
        "template_heating_setpoint": _native(conditions.get("heating_setpoint")),
        "template_heating_capacity_unlimited": _native(
            systems.get("heating_capacity_unlimited")
        ),
        "template_heating_capacity_value": _native(
            systems.get("heating_capacity_value")
        ),
        "template_system_air_minimum_flowrate": _native(
            systems.get("system_air_minimum_flowrate")
        ),
        "repair_applied": False,
        "next_action": (
            "Use this exact read-back to prepare a separate reviewed repair; "
            "do not guess a heating schedule or design capacity."
        ),
    }


def run() -> None:
    try:
        import iesve  # type: ignore
    except Exception as exc:
        raise RuntimeError("Run this file inside IESVE 2025 VEScripts.") from exc

    project = iesve.VEProject.get_current_project()
    if not project:
        raise RuntimeError("Open the SIA_compatible_model_TEST project first.")
    if not getattr(project, "models", None):
        raise RuntimeError("The active VE project has no real model.")
    model = project.models[0]
    matches = [
        (handle, template)
        for handle, template in _template_collection(project).items()
        if str(getattr(template, "name", "")) == TEMPLATE_NAME
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "Expected exactly one {!r} template; found {}.".format(
                TEMPLATE_NAME, len(matches)
            )
        )

    template = _template_snapshot(*matches[0])
    room_index = {
        str(getattr(body, "name", "")): body for body in model.get_bodies(False)
    }
    rooms = [
        _room_snapshot(room_index[name]) for name in TARGET_ROOMS if name in room_index
    ]
    report = {
        "schema_version": "1.0",
        "audit": "sia3802_classroom_controls",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_name": str(getattr(project, "name", "")),
        "project_path": str(getattr(project, "path", "")),
        "read_only": True,
        "no_mutation_performed": True,
        "target_template": TEMPLATE_NAME,
        "target_rooms": list(TARGET_ROOMS),
        "template": template,
        "rooms": rooms,
        "matching_profiles": _profile_inventory(project),
    }
    report["summary"] = _summary(template, rooms)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT_PATH.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(OUTPUT_PATH)

    print("=" * 78)
    print("SIA 380/2 CLASSROOM CONTROLS AUDIT — READ ONLY")
    print("Project: {}".format(report["project_path"] or report["project_name"]))
    print("Template: {}".format(TEMPLATE_NAME))
    print("Rooms found: {} / {}".format(len(rooms), len(TARGET_ROOMS)))
    print("Heating profile: {!r}".format(report["summary"]["template_heating_profile"]))
    print("Heating setpoint: {!r}".format(report["summary"]["template_heating_setpoint"]))
    print(
        "Heating capacity unlimited: {!r}".format(
            report["summary"]["template_heating_capacity_unlimited"]
        )
    )
    print("No VE value was changed and the project was not saved.")
    print("JSON: {}".format(OUTPUT_PATH))
    print("=" * 78)


if __name__ == "__main__":
    run()
