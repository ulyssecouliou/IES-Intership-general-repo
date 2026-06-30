"""
Diagnostic IESVE API probe for Swiss Compliance Checker.

Run this script inside IESVE/VEScripts with a project open. It writes a JSON
snapshot of the real objects/properties exposed by the current model so the
compliance extractor can be mapped to the client's VE data without guessing.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
from datetime import datetime
from typing import Any, Dict, List

try:
    import iesve  # type: ignore
except Exception:  # pragma: no cover - only available inside IESVE.
    iesve = None

from swiss_sia.config import OUTPUT_DIR
from swiss_sia import data_extractor


data_extractor = importlib.reload(data_extractor)
VEDataExtractor = data_extractor.VEDataExtractor

DEFAULT_BODY_LIMIT = 6
DEFAULT_SURFACE_LIMIT = 40
DEFAULT_OPENING_LIMIT = 20
PROBE_SCHEMA_VERSION = "2026-06-29-cdb-diagnostics-v2"
DATA_EXTRACTOR_MODULE_PATH = getattr(data_extractor, "__file__", "")


def jsonable(value: Any, depth: int = 0) -> Any:
    """Convert VE/Python objects to JSON-safe diagnostic values."""
    if depth > 4:
        return repr(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {
            str(key): jsonable(val, depth + 1)
            for key, val in list(value.items())[:80]
        }
    if isinstance(value, (list, tuple, set)):
        return [jsonable(item, depth + 1) for item in list(value)[:80]]
    try:
        return dict(value)
    except Exception:
        pass
    try:
        return str(value)
    except Exception:
        return repr(value)


def safe_attr(obj: Any, name: str) -> Any:
    try:
        value = getattr(obj, name)
        if callable(value):
            try:
                return value()
            except TypeError:
                return f"<callable {name}>"
        return value
    except Exception as exc:
        return f"<error: {exc}>"


def safe_call(obj: Any, method_name: str, *args: Any) -> Any:
    try:
        method = getattr(obj, method_name)
        return method(*args)
    except Exception as exc:
        return {"__error__": str(exc), "__method__": method_name}


def object_header(extractor: VEDataExtractor, obj: Any) -> Dict[str, Any]:
    return {
        "id": extractor.get_object_id(obj),
        "class": obj.__class__.__name__ if obj is not None else None,
        "type_attr": jsonable(safe_attr(obj, "type")),
        "subtype_attr": jsonable(safe_attr(obj, "subtype")),
        "name_attr": jsonable(safe_attr(obj, "name")),
    }


def child_get_values(children: List[Any]) -> List[Any]:
    values = []
    for child in children[:30]:
        if isinstance(child, dict):
            values.append(jsonable(child))
            continue
        try:
            if hasattr(child, "get"):
                values.append(jsonable(child.get()))
            else:
                values.append(jsonable(child))
        except Exception as exc:
            values.append({"__error__": str(exc), "__class__": child.__class__.__name__})
    return values


def collect_construction_ids(payload: Dict[str, Any]) -> List[str]:
    """Collect construction IDs discovered on sampled surfaces/openings."""
    construction_ids = []
    seen = set()
    for body in payload.get("bodies", []):
        for surface in body.get("surfaces", []):
            for construction_id in surface.get("constructions") or []:
                key = str(construction_id or "").strip()
                if key and key not in seen:
                    seen.add(key)
                    construction_ids.append(key)
            for opening in surface.get("openings", []):
                key = str(opening.get("construction") or "").strip()
                if key and key not in seen:
                    seen.add(key)
                    construction_ids.append(key)
    return construction_ids


def probe_cdb(extractor: VEDataExtractor, construction_ids: List[str]) -> Dict[str, Any]:
    """Capture enough CDB diagnostics to debug construction property resolution."""
    diagnostics: Dict[str, Any] = {
        "construction_ids_tested": construction_ids[:30],
        "projects": [],
        "resolved_properties": {},
    }

    try:
        import iesve
        classes = extractor._get_cdb_construction_classes(iesve)
    except Exception as exc:
        diagnostics["class_error"] = str(exc)
        classes = []

    diagnostics["construction_class_count"] = len(classes)
    diagnostics["construction_classes"] = [str(item) for item in classes]

    try:
        projects = extractor._get_cdb_projects()
    except Exception as exc:
        diagnostics["project_error"] = str(exc)
        projects = []

    diagnostics["project_count"] = len(projects)
    for project_index, cdb_project in enumerate(projects[:10]):
        project_info = {
            "index": project_index,
            "class": cdb_project.__class__.__name__,
            "reference": jsonable(safe_attr(cdb_project, "reference")),
            "id": jsonable(safe_attr(cdb_project, "id")),
            "construction_id_samples": [],
            "target_resolution": {},
        }

        for construction_class in classes[:8] + [None]:
            class_label = str(construction_class)
            try:
                if construction_class is None:
                    ids = cdb_project.get_construction_ids()
                else:
                    ids = cdb_project.get_construction_ids(construction_class)
                ids_list = [str(item) for item in list(ids)[:20]]
                project_info["construction_id_samples"].append({
                    "class": class_label,
                    "count_or_sample_size": len(ids_list),
                    "sample": ids_list,
                })
            except Exception as exc:
                project_info["construction_id_samples"].append({
                    "class": class_label,
                    "error": str(exc),
                })

            for construction_id in construction_ids[:12]:
                if construction_id in project_info["target_resolution"]:
                    continue
                construction = extractor._safe_get_cdb_construction(cdb_project, construction_id, construction_class)
                if construction is not None:
                    project_info["target_resolution"][construction_id] = {
                        "class": class_label,
                        "construction_object_class": construction.__class__.__name__,
                    }

        diagnostics["projects"].append(project_info)

    for construction_id in construction_ids[:30]:
        diagnostics["resolved_properties"][construction_id] = jsonable(
            extractor.get_construction_properties(construction_id)
        )

    return diagnostics


def probe_project(body_limit: int, surface_limit: int, opening_limit: int) -> Dict[str, Any]:
    if iesve is None:
        raise RuntimeError("The iesve Python module is only available inside IESVE.")
    project = iesve.VEProject.get_current_project()
    if not project:
        raise RuntimeError("No active VE project found. Open a project in IESVE first.")

    extractor = VEDataExtractor(project)
    bodies = extractor.get_bodies()

    payload: Dict[str, Any] = {
        "probe_schema_version": PROBE_SCHEMA_VERSION,
        "data_extractor_path": DATA_EXTRACTOR_MODULE_PATH,
        "data_extractor_has_cdb_helper": hasattr(VEDataExtractor, "_get_cdb_construction_classes"),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_path": jsonable(safe_attr(project, "path")),
        "body_count": len(bodies),
        "body_limit": body_limit,
        "surface_limit": surface_limit,
        "opening_limit": opening_limit,
        "bodies": [],
    }

    for body in bodies[:body_limit]:
        body_info = object_header(extractor, body)
        body_info["areas"] = jsonable(extractor.get_body_areas(body))

        room_data = extractor.get_room_data(body)
        body_info["room_data"] = {
            "class": room_data.__class__.__name__ if room_data is not None else None,
            "conditions": jsonable(extractor.get_room_conditions(room_data)) if room_data else {},
            "apache_systems": jsonable(extractor.get_apache_systems(room_data)) if room_data else {},
            "internal_gains": child_get_values(extractor.get_internal_gains(room_data)) if room_data else [],
            "air_exchanges": child_get_values(extractor.get_air_exchanges(room_data)) if room_data else [],
        }

        surfaces = extractor.get_surfaces(body)
        body_info["surface_count"] = len(surfaces)
        body_info["surfaces"] = []

        for surface in surfaces[:surface_limit]:
            surface_info = object_header(extractor, surface)
            raw_properties = safe_call(surface, "get_properties")
            raw_areas = safe_call(surface, "get_areas")
            surface_info.update({
                "normalized_properties": jsonable(extractor.get_surface_properties(surface)),
                "raw_properties": jsonable(raw_properties),
                "areas": jsonable(raw_areas),
                "constructions": jsonable(extractor.get_constructions(surface)),
                "resolved_constructions": jsonable([
                    extractor.get_construction_properties(construction_id)
                    for construction_id in extractor.get_constructions(surface)
                ]),
                "adjacencies": jsonable(extractor.get_adjacencies(surface)),
            })

            openings = extractor.get_openings(surface)
            surface_info["opening_count"] = len(openings)
            surface_info["openings"] = []
            for opening in openings[:opening_limit]:
                opening_info = object_header(extractor, opening)
                opening_info.update({
                    "normalized_properties": jsonable(extractor.get_opening_properties(opening)),
                    "raw_properties": jsonable(safe_call(opening, "get_properties")),
                    "areas": jsonable(safe_call(opening, "get_areas")),
                    "construction": jsonable(safe_call(opening, "get_construction")),
                    "resolved_construction": jsonable(
                        extractor.get_construction_properties(extractor.get_opening_construction(opening))
                    ),
                })
                surface_info["openings"].append(opening_info)

            body_info["surfaces"].append(surface_info)

        payload["bodies"].append(body_info)

    payload["cdb_diagnostics"] = probe_cdb(extractor, collect_construction_ids(payload))

    return payload


def write_probe(body_limit: int, surface_limit: int, opening_limit: int) -> str:
    """Run the probe and write the JSON diagnostic file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    payload = probe_project(body_limit, surface_limit, opening_limit)
    output_path = os.path.join(
        OUTPUT_DIR,
        f"iesve_extraction_probe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return output_path


def run_with_defaults() -> str:
    """Button-friendly entry point for the VE Scripts Run button."""
    return write_probe(DEFAULT_BODY_LIMIT, DEFAULT_SURFACE_LIMIT, DEFAULT_OPENING_LIMIT)


def main() -> None:
    parser = argparse.ArgumentParser(description="Dump a small diagnostic snapshot of the active IESVE model.")
    parser.add_argument("--body-limit", type=int, default=DEFAULT_BODY_LIMIT)
    parser.add_argument("--surface-limit", type=int, default=DEFAULT_SURFACE_LIMIT)
    parser.add_argument("--opening-limit", type=int, default=DEFAULT_OPENING_LIMIT)
    args, _unknown = parser.parse_known_args()

    output_path = write_probe(args.body_limit, args.surface_limit, args.opening_limit)
    print(f"IESVE extraction probe written to: {output_path}")


if __name__ == "__main__":
    main()
