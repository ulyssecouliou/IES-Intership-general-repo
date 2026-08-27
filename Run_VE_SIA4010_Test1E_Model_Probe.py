"""Read-only inventory of the prepared SIA 4010 Test 1E VE model.

The next operation will assign the reviewed fabric-awning construction.  This
probe first records every body, surface and opening with its current
construction so the mutating launcher can target exact opening IDs rather than
guessing.  It changes no VE object and does not save the project.
"""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

EXPECTED_PROJECT_FOLDER = "SIA4010_TEST1_1E_TEMPLATE"
REPORT_DIRECTORY = Path("sia4010_artifacts") / "diagnostics"


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sequence(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return [value]


def _safe_call(obj, method, default=None):
    function = getattr(obj, method, None)
    if not callable(function):
        return default
    try:
        return function()
    except Exception as exc:  # native VE boundary
        return {"error": "{}: {}".format(type(exc).__name__, exc)}


def _properties(obj):
    value = _safe_call(obj, "get_properties", {})
    return dict(value) if isinstance(value, dict) else {"readback": str(value)}


def _construction_record(construction):
    if construction is None:
        return {"id": "", "properties": {}}
    identifier = str(getattr(construction, "id", "") or "")
    properties = _properties(construction)
    shade_keys = (
        "external_shade_active",
        "external_shade_profile",
        "external_shade_radiation_to_lower",
        "external_shade_radiation_to_raise",
        "external_shade_transmittance_0",
        "external_shade_solar_reflectance",
        "external_shade_visible_reflectance",
    )
    return {
        "id": identifier,
        "description": str(properties.get("description", "") or ""),
        "shade_properties": {
            key: properties.get(key) for key in shade_keys if key in properties
        },
    }


def run():
    try:
        import iesve  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Run this probe inside IESVE VEScripts") from exc

    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.sia4010.scenario_preflight import (
        is_temporary_ve_project,
    )

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("Open the prepared Test 1E template project first")
    project_path = Path(str(getattr(project, "path", "") or ""))
    if not project_path.is_dir() or is_temporary_ve_project(project_path):
        raise RuntimeError("Save the Test 1E template project before probing")
    if project_path.name.casefold() != EXPECTED_PROJECT_FOLDER.casefold():
        raise RuntimeError(
            "Wrong active project: expected {!r}, received {!r}".format(
                EXPECTED_PROJECT_FOLDER, project_path.name
            )
        )
    scenario_path = project_path / "sia_model_scenario.json"
    scenario = ModelScenario.load(scenario_path)
    if (scenario.variant, scenario.case_id) != ("test_1", "1E"):
        raise RuntimeError(
            "Active scenario is {}/{}; expected test_1/1E".format(
                scenario.variant, scenario.case_id
            )
        )

    bodies = []
    opening_count = 0
    errors = []
    for model_index, model in enumerate(_sequence(getattr(project, "models", ()))):
        get_bodies = getattr(model, "get_bodies", None)
        if not callable(get_bodies):
            continue
        try:
            model_bodies = _sequence(get_bodies(False))
        except Exception as exc:
            errors.append("model {} bodies: {}: {}".format(
                model_index, type(exc).__name__, exc
            ))
            continue
        for body in model_bodies:
            body_row = {
                "id": str(getattr(body, "id", "") or ""),
                "name": str(getattr(body, "name", "") or ""),
                "surfaces": [],
            }
            try:
                surfaces = _sequence(body.get_surfaces())
            except Exception as exc:
                errors.append("body {} surfaces: {}: {}".format(
                    body_row["name"], type(exc).__name__, exc
                ))
                surfaces = []
            for surface_index, surface in enumerate(surfaces):
                surface_row = {
                    "index": surface_index,
                    "properties": _properties(surface),
                    "openings": [],
                }
                getter = getattr(surface, "get_openings", None)
                if callable(getter):
                    try:
                        openings = _sequence(getter())
                    except Exception as exc:
                        errors.append("surface {} openings: {}: {}".format(
                            surface_index, type(exc).__name__, exc
                        ))
                        openings = []
                    for opening in openings:
                        opening_count += 1
                        construction = _safe_call(
                            opening, "get_construction", None
                        )
                        surface_row["openings"].append(
                            {
                                "id": str(_safe_call(opening, "get_id", "") or ""),
                                "properties": _properties(opening),
                                "construction": _construction_record(construction),
                            }
                        )
                body_row["surfaces"].append(surface_row)
            bodies.append(body_row)

    status = (
        "OPENINGS_DISCOVERED_READY_FOR_EXACT_TARGET_REVIEW"
        if opening_count and not errors
        else "MODEL_READBACK_INCOMPLETE"
    )
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "project": {
            "name": str(getattr(project, "name", "") or ""),
            "path": str(project_path),
        },
        "scenario": {"variant": scenario.variant, "case_id": scenario.case_id},
        "scenario_path": str(scenario_path),
        "scenario_sha256": _sha256(scenario_path),
        "body_count": len(bodies),
        "opening_count": opening_count,
        "bodies": bodies,
        "readback_errors": errors,
        "mutation_performed": False,
        "project_saved_by_script": False,
        "compliance_claim_allowed": False,
        "next_action": (
            "Use the exact opening IDs and current construction IDs to build "
            "the guarded 1E awning assignment."
        ),
    }
    report_directory = project_path / REPORT_DIRECTORY
    report_directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    report_path = report_directory / "sia4010_test1e_model_probe_{}.json".format(
        stamp
    )
    report_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    report_path.with_suffix(report_path.suffix + ".sha256").write_text(
        "{}  {}\n".format(_sha256(report_path), report_path.name),
        encoding="ascii",
    )
    print("SIA 4010 TEST 1E MODEL PROBE: {}".format(status))
    print("Project: {}".format(project_path))
    print("Bodies: {}; openings: {}".format(len(bodies), opening_count))
    print("Read-back errors: {}".format(len(errors)))
    print("Report: {}".format(report_path))
    print("No VE object was changed and the project was not saved.")
    return report_path


if __name__ == "__main__":
    run()
