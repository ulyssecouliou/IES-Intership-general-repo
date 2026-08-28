"""Read-only IESVE capability probe for the Swiss reference-model workflow.

Open this file in VE Scripts with the target project active and click Run.
The probe does not create or modify VE objects.  It inventories the installed
API surface, checks the configured weather file, detects naming collisions and
writes a JSON diagnostic beside the active VE project.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)


def _jsonable(value, depth=0):
    """Convert VE enums and containers to bounded JSON-safe values."""

    if depth > 4:
        return repr(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {
            str(key): _jsonable(item, depth + 1)
            for key, item in list(value.items())[:100]
        }
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item, depth + 1) for item in list(value)[:100]]
    enum_value = getattr(value, "value", None)
    if enum_value is not None and enum_value is not value:
        return {"name": str(value), "value": _jsonable(enum_value, depth + 1)}
    return str(value)


def _sha256(path):
    """Return the SHA-256 of a local file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _public_members(container):
    """Return non-callable public members from an API enum container."""

    if container is None:
        return {}
    result = {}
    for name in sorted(item for item in dir(container) if not item.startswith("_")):
        try:
            value = getattr(container, name)
            if not callable(value):
                result[name] = _jsonable(value)
        except Exception as exc:
            result[name] = {"error": str(exc)}
    return result


def _resolve_path(root, path):
    """Resolve a dotted attribute path from the iesve module."""

    current = root
    for part in path.split("."):
        if not hasattr(current, part):
            return None
        current = getattr(current, part)
    return current


def _resolve_enum_member(root, container_paths, member_names):
    """Resolve an enum member across nested and top-level VE layouts."""

    attempts = []
    for container_path in container_paths:
        container = _resolve_path(root, container_path)
        if container is None:
            attempts.append({"path": container_path, "available": False})
            continue
        for member_name in member_names:
            try:
                value = getattr(container, member_name)
                return {
                    "available": True,
                    "container_path": container_path,
                    "member": member_name,
                    "value": _jsonable(value),
                    "attempts": attempts,
                }
            except Exception as exc:
                attempts.append(
                    {
                        "path": container_path,
                        "member": member_name,
                        "available": True,
                        "error": str(exc),
                    }
                )
    return {"available": False, "attempts": attempts}


def _enum_resolution(iesve):
    """Resolve every enum member required by the mutation workflow."""

    definitions = {
        "element.wall": (("VECdbProject.element_categories", "element_categories"), ("wall",)),
        "element.roof": (("VECdbProject.element_categories", "element_categories"), ("roof",)),
        "element.ground_floor": (("VECdbProject.element_categories", "element_categories"), ("ground_floor",)),
        "element.partition": (("VECdbProject.element_categories", "element_categories"), ("partition",)),
        "element.door": (("VECdbProject.element_categories", "element_categories"), ("door",)),
        "element.ext_glazing": (("VECdbProject.element_categories", "element_categories"), ("ext_glazing",)),
        "material.other": (("VECdbProject.material_categories", "material_categories"), ("other",)),
        "material.glass": (("VECdbProject.material_categories", "material_categories"), ("glass",)),
        "material.all": (("VECdbProject.material_categories", "material_categories"), ("all",)),
        "class.opaque": (("VECdbProject.construction_class", "construction_class"), ("opaque",)),
        "class.glazed": (("VECdbProject.construction_class", "construction_class"), ("glazed",)),
        "class.none": (("VECdbProject.construction_class", "construction_class"), ("none",)),
        "uvalue.iso": (("VECdbProject.uvalue_types", "uvalue_types"), ("iso",)),
    }
    return {
        name: _resolve_enum_member(iesve, paths, members)
        for name, (paths, members) in definitions.items()
    }


def _method_matrix(obj, names):
    """Report whether required methods are exposed by one object."""

    return {name: bool(obj is not None and hasattr(obj, name)) for name in names}


def _thermal_templates(project, assigned=False, allow_ncm=False):
    """Call VEProject.thermal_templates across VE Boost.Python signatures."""

    errors = []
    for arguments in ((assigned, allow_ncm), (assigned,)):
        try:
            return project.thermal_templates(*arguments)
        except Exception as exc:
            errors.append("{}: {}".format(arguments, exc))
    raise RuntimeError(
        "VEProject.thermal_templates rejected supported positional signatures: {}".format(
            " | ".join(errors)
        )
    )


def _load_json(path):
    """Load one JSON file and return its payload plus evidence metadata."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload, {
        "path": str(path),
        "exists": True,
        "sha256": _sha256(path),
    }


def _cdb_project(iesve):
    """Resolve the current editable project CDB without mutation."""

    database = iesve.VECdbDatabase.get_current_database()
    projects = database.get_projects()
    candidates = projects.get(0, []) if isinstance(projects, dict) else []
    return candidates[0] if candidates else None


def _existing_profile_references(project):
    """Return current profile references for collision checking."""

    references = []
    for collection in project.profiles():
        for identifier, profile in collection.items():
            reference = getattr(profile, "reference", getattr(profile, "name", ""))
            references.append({"id": str(identifier), "reference": str(reference)})
    return references


def _sample_cdb(iesve, project_cdb, enum_resolution):
    """Read a small representative CDB sample and exposed property keys."""

    diagnostics = {"available": project_cdb is not None, "materials": [], "constructions": []}
    if project_cdb is None:
        return diagnostics

    all_materials = enum_resolution.get("material.all", {}).get("value")
    all_materials_runtime = _resolve_enum_member(
        iesve,
        ("VECdbProject.material_categories", "material_categories"),
        ("all",),
    )
    if all_materials_runtime.get("available"):
        container = _resolve_path(iesve, all_materials_runtime["container_path"])
        all_materials = getattr(container, all_materials_runtime["member"])
    try:
        material_ids = list(project_cdb.get_material_ids(all_materials))[:12]
    except Exception as exc:
        diagnostics["material_error"] = str(exc)
        material_ids = []
    for identifier in material_ids:
        try:
            material = project_cdb.get_material(identifier)
            properties = dict(material.get_properties())
            diagnostics["materials"].append(
                {
                    "id": str(identifier),
                    "property_keys": sorted(str(key) for key in properties),
                    "properties": _jsonable(properties),
                }
            )
        except Exception as exc:
            diagnostics["materials"].append({"id": str(identifier), "error": str(exc)})

    category_by_value = {
        str(result.get("value")): name.split(".", 1)[1]
        for name, result in enum_resolution.items()
        if name.startswith("element.") and result.get("available")
    }
    for class_name in ("opaque", "glazed"):
        class_info = enum_resolution.get("class.{}".format(class_name), {})
        if not class_info.get("available"):
            diagnostics["constructions"].append(
                {"class": class_name, "error": "construction-class enum unavailable"}
            )
            continue
        container = _resolve_path(iesve, class_info["container_path"])
        construction_class = getattr(container, class_info["member"])
        try:
            identifiers = list(
                project_cdb.get_construction_ids(construction_class)
            )[:12]
        except Exception as exc:
            diagnostics["constructions"].append(
                {"class": class_name, "error": str(exc)}
            )
            continue
        for identifier in identifiers:
            construction = None
            for arguments in ((identifier, construction_class), (identifier,)):
                try:
                    construction = project_cdb.get_construction(*arguments)
                    if construction is not None:
                        break
                except Exception:
                    continue
            if construction is None:
                diagnostics["constructions"].append(
                    {"class": class_name, "id": str(identifier), "error": "unresolved"}
                )
                continue
            try:
                properties = dict(construction.get_properties())
                category_value = _jsonable(getattr(construction, "category", None))
                diagnostics["constructions"].append(
                    {
                        "class": class_name,
                        "category": category_by_value.get(
                            str(category_value), str(category_value)
                        ),
                        "id": str(identifier),
                        "property_keys": sorted(str(key) for key in properties),
                        "properties": _jsonable(properties),
                        "g_values": _jsonable(construction.get_g_values())
                        if hasattr(construction, "get_g_values")
                        else None,
                    }
                )
            except Exception as exc:
                diagnostics["constructions"].append(
                    {"class": class_name, "id": str(identifier), "error": str(exc)}
                )
    return diagnostics


def run():
    """Run the read-only probe and return the generated report path."""

    try:
        import iesve  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Run this script from the IESVE VEScripts editor.") from exc

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("Open the target VE project before running the probe.")
    model = project.models[0] if getattr(project, "models", None) else None
    project_path = Path(str(project.path))
    config_path = project_path / "reference_model_config.json"
    assets_path = project_path / "reference_model_assets.json"
    if not config_path.is_file() or not assets_path.is_file():
        raise RuntimeError(
            "reference_model_config.json and reference_model_assets.json must be in {}".format(
                project_path
            )
        )

    config, config_evidence = _load_json(config_path)
    assets, assets_evidence = _load_json(assets_path)
    project_cdb = _cdb_project(iesve)
    enum_resolution = _enum_resolution(iesve)

    capability_groups = {
        "project": _method_matrix(
            project,
            (
                "create_profile", "save_profiles", "create_casual_gain",
                "casual_gains", "create_air_exchange", "air_exchanges",
                "create_thermal_template", "profiles",
                "thermal_templates", "apache_systems", "get_version",
            ),
        ),
        "model": _method_matrix(
            model, ("get_bodies", "rebuild_adjacencies", "assign_thermal_template_to_rooms")
        ),
        "cdb_project": _method_matrix(
            project_cdb,
            (
                "create_material", "create_construction", "get_material_ids",
                "get_material", "get_construction_ids", "get_construction",
            ),
        ),
        "modules": {
            "ImportGBXML": hasattr(iesve, "ImportGBXML"),
            "VELocate": hasattr(iesve, "VELocate"),
            "WeatherFileReader": hasattr(iesve, "WeatherFileReader"),
            "VECdbDatabase": hasattr(iesve, "VECdbDatabase"),
            "VECdbProject": hasattr(iesve, "VECdbProject"),
        },
    }
    missing = sorted(
        "{}.{}".format(group_name, name)
        for group_name, group in capability_groups.items()
        for name, present in group.items()
        if not present
    )
    missing_enums = sorted(
        name for name, result in enum_resolution.items() if not result.get("available")
    )

    weather_value = config.get("parameters", {}).get("weather_file", {}).get("value")
    weather_path = Path(str(weather_value)) if weather_value else None
    weather = {
        "configured": str(weather_value or ""),
        "exists": bool(weather_path and weather_path.is_file()),
        "open_result": None,
        "readable": False,
    }
    if weather["exists"] and hasattr(iesve, "WeatherFileReader"):
        try:
            weather["sha256"] = _sha256(weather_path)
            reader = iesve.WeatherFileReader()
            weather["open_result"] = reader.open_weather_file(str(weather_path))
            weather["readable"] = bool(weather["open_result"] > 0)
        except Exception as exc:
            weather["error"] = str(exc)

    profiles = _existing_profile_references(project)
    existing_profile_names = {item["reference"] for item in profiles}
    requested_profile_names = {
        str(item.get("reference", "")) for item in assets.get("profiles", [])
    }
    templates = _thermal_templates(project, assigned=False)
    existing_template_names = {
        str(getattr(template, "name", "")) for template in templates.values()
    }
    requested_template = str(assets.get("thermal_template", {}).get("name", ""))
    collisions = {
        "profiles": sorted(existing_profile_names & requested_profile_names),
        "thermal_template": requested_template
        if requested_template in existing_template_names
        else "",
    }
    reuse_verified = assets.get("on_existing") == "reuse_verified"
    blocking_collisions = {
        "profiles": [] if reuse_verified else collisions["profiles"],
        "thermal_template": "" if reuse_verified else collisions["thermal_template"],
    }

    ready = (
        not missing
        and not missing_enums
        and weather["readable"]
        and not blocking_collisions["profiles"]
        and not blocking_collisions["thermal_template"]
    )
    payload = {
        "probe_schema_version": "1.1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "READY" if ready else "BLOCKED",
        "project": {
            "name": str(getattr(project, "name", "")),
            "path": str(project_path),
            "version": str(project.get_version()) if hasattr(project, "get_version") else "unavailable",
        },
        "inputs": {"config": config_evidence, "assets": assets_evidence},
        "capabilities": capability_groups,
        "missing_capabilities": missing,
        "enum_resolution": enum_resolution,
        "missing_enums": missing_enums,
        "enums": {
            "element_categories": _public_members(getattr(iesve.VECdbProject, "element_categories", None)),
            "material_categories": _public_members(getattr(iesve.VECdbProject, "material_categories", None)),
            "construction_class": _public_members(getattr(iesve.VECdbProject, "construction_class", None)),
            "uvalue_types": _public_members(getattr(iesve.VECdbProject, "uvalue_types", None)),
        },
        "weather": weather,
        "existing_profiles": profiles,
        "existing_thermal_templates": sorted(existing_template_names),
        "collisions": collisions,
        "existing_asset_policy": {
            "mode": str(assets.get("on_existing", "")),
            "collisions_are_blocking": not reuse_verified,
            "verification_stage": "Generator read-back before reuse",
            "blocking_collisions": blocking_collisions,
        },
        "cdb_sample": _sample_cdb(iesve, project_cdb, enum_resolution),
        "next_action": "Run Run_VE_Swiss_Reference_Model.py in this disposable project."
        if ready
        else "Resolve every missing capability, weather error or blocking name collision before model generation.",
    }

    output_dir = project_path / "reference_model_artifacts" / "diagnostics"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "reference_model_capability_probe_{}.json".format(
        datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Reference-model capability probe status: {}".format(payload["status"]))
    print("Report: {}".format(output_path))
    return str(output_path)


if __name__ == "__main__":
    run()
