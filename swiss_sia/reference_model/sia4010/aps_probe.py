"""Read-only APS capability inspection for SIA 4010 Tests 1 and 2."""

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping

from ...simulation_results import (
    convert_aps_series_to_metric,
    get_available_variables,
    get_results_per_hour,
    read_room_result,
    read_surface_result,
    result_label,
    series_to_list,
)


_RELEVANT_TOKENS = (
    "heat",
    "cool",
    "load",
    "solar",
    "radiation",
    "transmi",
    "gain",
    "window",
    "glazing",
    "temperature",
    "operative",
    "resultant",
    "radiant",
)


def is_sia4010_candidate_variable(variable: Mapping[str, Any]) -> bool:
    """Return whether variable metadata may contain a Test 1/2 quantity."""

    haystack = " ".join(
        str(variable.get(key) or "")
        for key in ("aps_varname", "name", "display_name")
    ).lower()
    return any(token in haystack for token in _RELEVANT_TOKENS)


def _room_identity(room: Any) -> Dict[str, Any]:
    """Normalize one ResultsReader room-list entry."""

    if isinstance(room, dict):
        return {
            "name": str(room.get("name") or room.get("room_name") or "Unknown"),
            "id": room.get("id") or room.get("room_id"),
            "area_m2": room.get("area") or room.get("floor_area"),
        }
    if isinstance(room, (list, tuple)) and len(room) >= 2:
        return {
            "name": str(room[0]),
            "id": room[1],
            "area_m2": room[2] if len(room) >= 3 else None,
        }
    return {"name": str(room), "id": None, "area_m2": None}


def _summary(values: Iterable[float]) -> Dict[str, Any]:
    """Return bounded numeric evidence without exporting a full annual series."""

    numeric = series_to_list(values)
    if not numeric:
        return {"count": 0}
    return {
        "count": len(numeric),
        "minimum": min(numeric),
        "maximum": max(numeric),
        "sum": sum(numeric),
        "first_values": numeric[:8],
    }


def _properties(value: Any) -> Dict[str, Any]:
    """Return proxy properties as a plain dictionary when available."""

    get_properties = getattr(value, "get_properties", None)
    if not callable(get_properties):
        return {}
    try:
        result = get_properties()
    except Exception:
        return {}
    if isinstance(result, dict):
        return dict(result)
    try:
        return dict(result)
    except Exception:
        return {}


def _attribute(value: Any, name: str, default: Any = None) -> Any:
    """Read a VE proxy attribute, calling it when the API exposes it as a method.

    Several VE proxy attributes are plain values on some objects and bound
    methods on others, and this changes between VE releases. Measured on
    VE 2025.2.0.0: ``VESurface.id`` and ``VESurface.name`` are METHODS, so a
    bare ``getattr`` yields the bound method and ``str()`` of it produces
    ``"<bound method id of <iesve.VESurface object at 0x...>>"``. That is what
    the 2026-07-31 probe run recorded for all 354 surfaces, which made the
    surface identity unusable -- while the probe still reported
    ``READY_FOR_SURFACE_BINDING_REVIEW``. A binding cannot be reviewed against a
    memory address.

    Returns ``default`` when the attribute is absent or the call raises, so the
    probe stays read-only and never fails on an API difference.
    """

    attribute = getattr(value, name, None)
    if attribute is None:
        return default
    if callable(attribute):
        try:
            return attribute()
        except Exception:
            return default
    return attribute


def _sequence(value: Any) -> List[Any]:
    """Return a safe list for VE proxy collections."""

    if value is None:
        return []
    if isinstance(value, list):
        return value
    try:
        return list(value)
    except Exception:
        return []


def build_surface_inventory(project: Any) -> List[Dict[str, Any]]:
    """Read exact room/surface APS handles from the active VE model."""

    inventory: List[Dict[str, Any]] = []
    for model in _sequence(getattr(project, "models", ())):
        get_bodies = getattr(model, "get_bodies", None)
        if not callable(get_bodies):
            continue
        try:
            bodies = _sequence(get_bodies(False))
        except Exception:
            continue
        for body in bodies:
            room_id = getattr(body, "id", None)
            room_name = str(
                getattr(body, "name", room_id if room_id is not None else "")
            )
            get_surfaces = getattr(body, "get_surfaces", None)
            if not callable(get_surfaces):
                continue
            try:
                surfaces = _sequence(get_surfaces())
            except Exception:
                continue
            for surface_index, surface in enumerate(surfaces):
                properties = _properties(surface)
                aps_handle = properties.get("aps_handle")
                if aps_handle is None:
                    aps_handle = getattr(surface, "aps_handle", None)
                get_openings = getattr(surface, "get_openings", None)
                try:
                    opening_count = (
                        len(_sequence(get_openings()))
                        if callable(get_openings)
                        else 0
                    )
                except Exception:
                    opening_count = 0
                inventory.append(
                    {
                        "room_name": room_name,
                        "room_id": room_id,
                        "surface_index": surface_index,
                        "surface_id": _attribute(surface, "id"),
                        "surface_name": str(
                            _attribute(
                                surface,
                                "name",
                                _attribute(surface, "id", surface_index),
                            )
                        ),
                        "surface_type": str(
                            properties.get("type", "")
                        ),
                        "orientation": properties.get("orientation"),
                        "tilt": properties.get("tilt"),
                        "aps_handle": aps_handle,
                        "opening_count": opening_count,
                    }
                )
    return inventory


def inspect_results_reader(
    results_file: Any,
    aps_file_name: str,
    surface_inventory: Iterable[Mapping[str, Any]] = (),
) -> Dict[str, Any]:
    """Inspect candidate variables and series without changing VE or APS data."""

    variables = get_available_variables(results_file)
    candidates = [
        variable for variable in variables if is_sia4010_candidate_variable(variable)
    ]
    try:
        raw_rooms = list(results_file.get_room_list() or [])
    except Exception:
        raw_rooms = []
    rooms = [_room_identity(room) for room in raw_rooms]
    surfaces = [dict(item) for item in surface_inventory]
    result_rows: List[Dict[str, Any]] = []
    for variable in candidates:
        aps_name = str(variable.get("aps_varname") or variable.get("name") or "")
        display_name = str(variable.get("display_name") or aps_name)
        level = str(variable.get("model_level") or variable.get("level") or "z")
        aps_variable = (
            aps_name,
            display_name,
            level,
            str(variable.get("resolved_metric_unit") or ""),
            variable.get("resolved_metric_divisor", 1.0),
            variable.get("resolved_metric_offset", 0.0),
        )
        room_summaries = []
        surface_summaries = []
        if level.lower() in {"z", "r", "room", "zone", ""}:
            for room in rooms:
                if room["id"] is None:
                    continue
                raw = read_room_result(
                    results_file,
                    room["id"],
                    aps_name,
                    display_name,
                    level or "z",
                )
                metric = convert_aps_series_to_metric(raw, aps_variable)
                summary = _summary(metric)
                if summary["count"]:
                    room_summaries.append(
                        {
                            "room_name": room["name"],
                            "room_id": room["id"],
                            "series": summary,
                        }
                    )
        elif level.lower() in {"s", "surface"}:
            for surface in surfaces:
                room_id = surface.get("room_id")
                aps_handle = surface.get("aps_handle")
                if room_id is None or aps_handle is None:
                    continue
                raw = read_surface_result(
                    results_file,
                    room_id,
                    aps_handle,
                    aps_name,
                    display_name,
                )
                metric = convert_aps_series_to_metric(raw, aps_variable)
                summary = _summary(metric)
                if summary["count"]:
                    surface_summaries.append(
                        {
                            "room_name": surface.get("room_name"),
                            "room_id": room_id,
                            "surface_name": surface.get("surface_name"),
                            "surface_id": surface.get("surface_id"),
                            "surface_index": surface.get("surface_index"),
                            "surface_type": surface.get("surface_type"),
                            "orientation": surface.get("orientation"),
                            "tilt": surface.get("tilt"),
                            "aps_handle": aps_handle,
                            "opening_count": surface.get("opening_count", 0),
                            "series": summary,
                        }
                    )
        result_rows.append(
            {
                "aps_varname": aps_name,
                "display_name": display_name,
                "model_level": level,
                "metric_unit": aps_variable[3],
                "metric_divisor": aps_variable[4],
                "metric_offset": aps_variable[5],
                "label": result_label(aps_variable),
                "room_series": room_summaries,
                "surface_series": surface_summaries,
            }
        )
    surface_series_count = sum(
        len(row["surface_series"]) for row in result_rows
    )
    return {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "READY_FOR_BINDING_REVIEW" if candidates and rooms else "BLOCKED",
        "aps_file": aps_file_name,
        "results_per_hour": get_results_per_hour(results_file),
        "room_count": len(rooms),
        "rooms": rooms,
        "surface_inventory_count": len(surfaces),
        "surface_inventory": surfaces,
        "surface_series_count": surface_series_count,
        "surface_binding_status": (
            "READY_FOR_SURFACE_BINDING_REVIEW"
            if surface_series_count
            else "SURFACE_SERIES_NOT_DEMONSTRATED"
        ),
        "available_variable_count": len(variables),
        "candidate_variable_count": len(candidates),
        "candidate_variables": result_rows,
        "claim_guardrail": (
            "Read-only discovery only. A variable binding remains unconfirmed "
            "until its sign, unit, timestep, exact surface identity and "
            "physical meaning are reviewed."
        ),
    }
