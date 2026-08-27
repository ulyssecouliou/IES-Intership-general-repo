"""Read the exact live Test 1E envelope and construction layers."""

import json
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))


def _purge_cached_reference_model_modules():
    for module_name in tuple(sys.modules):
        if module_name == "swiss_sia.reference_model" or module_name.startswith(
            "swiss_sia.reference_model."
        ):
            del sys.modules[module_name]


def _plain(value):
    try:
        return json.loads(json.dumps(value, default=str))
    except (TypeError, ValueError):
        return str(value)


def run():
    """Capture surface assignments, CDB properties, layers and materials."""

    _purge_cached_reference_model_modules()
    import iesve  # type: ignore

    from swiss_sia.reference_model.sia4010.test1e_awning_qualification import (
        _live_targets,
    )
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.ve_api import IesVeGateway

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("Open the saved Test 1E project first")
    project_path = Path(str(getattr(project, "path", "") or "")).resolve()
    if not project_path.is_dir():
        raise RuntimeError("Save the active Test 1E project before read-back")
    scenario_path = project_path / "sia_model_scenario.json"
    if not scenario_path.is_file():
        raise RuntimeError(
            "Prepare the active Test 1E scenario before envelope read-back"
        )
    scenario = ModelScenario.load(scenario_path)
    if (scenario.variant, scenario.case_id) != ("test_1", "1E"):
        raise RuntimeError(
            "Envelope read-back requires scenario test_1/1E; active scenario is "
            "{}/{}".format(scenario.variant, scenario.case_id)
        )
    gateway = IesVeGateway(iesve)
    _live_targets(gateway)
    surfaces = []
    constructions = {}
    for body in gateway.model.get_bodies(False):
        for surface in body.get_surfaces():
            surface_properties = _plain(dict(surface.get_properties()))
            assigned = []
            for item in surface.get_constructions():
                identifier = gateway._construction_identifier(item)
                assigned.append(identifier)
                construction = (
                    item
                    if hasattr(item, "get_properties")
                    else gateway._get_construction(identifier)
                )
                if identifier in constructions:
                    continue
                layers = []
                for index, layer in enumerate(construction.get_layers()):
                    properties = _plain(dict(layer.get_properties()))
                    materials = []
                    for opaque in (True, False):
                        try:
                            material = layer.get_material(is_opaque=opaque)
                        except TypeError:
                            try:
                                material = layer.get_material(opaque)
                            except Exception:
                                continue
                        except Exception:
                            continue
                        if material is not None:
                            material_properties = {}
                            if hasattr(material, "get_properties"):
                                try:
                                    material_properties = _plain(
                                        dict(material.get_properties())
                                    )
                                except Exception:
                                    material_properties = {}
                            materials.append(
                                {
                                    "identifier": str(
                                        getattr(material, "id", material)
                                    ),
                                    "reference": str(
                                        getattr(material, "reference", "")
                                    ),
                                    "properties": material_properties,
                                }
                            )
                    layers.append(
                        {
                            "index": index,
                            "properties": properties,
                            "materials": materials,
                        }
                    )
                constructions[identifier] = {
                    "properties": _plain(dict(construction.get_properties())),
                    "reference": str(getattr(construction, "reference", "")),
                    "category": str(getattr(construction, "category", "")),
                    "opaque": _plain(getattr(construction, "opaque", None)),
                    "layers": layers,
                }
            surfaces.append(
                {
                    "properties": surface_properties,
                    "assigned_construction_ids": assigned,
                    "opening_count": len(list(surface.get_openings())),
                }
            )
    output = (
        project_path
        / "sia4010_artifacts"
        / "diagnostics"
        / "sia4010_test1e_envelope_readback.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "status": "ENVELOPE_AND_LAYER_READBACK_RECORDED",
                "project_path": str(project_path),
                "scenario": {
                    "variant": scenario.variant,
                    "case_id": scenario.case_id,
                },
                "surfaces": surfaces,
                "constructions": constructions,
                "mutation_performed": False,
                "project_saved_by_script": False,
                "claim_guardrail": (
                    "Read-back evidence only; comparison and acceptance remain separate."
                ),
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print("SIA 4010 TEST 1E ENVELOPE READBACK: RECORDED")
    print("Project: {}".format(project_path))
    print("Surfaces: {}; constructions: {}".format(len(surfaces), len(constructions)))
    for identifier, construction in sorted(constructions.items()):
        print(
            "- {}: layers={}, reference={!r}, opaque={!r}".format(
                identifier,
                len(construction["layers"]),
                construction["reference"],
                construction["opaque"],
            )
        )
        for layer in construction["layers"]:
            print(
                "    layer {} materials={} properties={}".format(
                    layer["index"],
                    layer["materials"],
                    layer["properties"],
                )
            )
    print("Report: {}".format(output))
    print("No VE object was changed and the project was not saved by the script.")
    return output


if __name__ == "__main__":
    run()
