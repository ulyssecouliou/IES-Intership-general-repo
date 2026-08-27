"""Create an unassigned five-layer Test 1E equivalent glazing diagnostic.

Run only in a fresh Save-As disposable project named
``SIA4010_TEST1_1E_EQUIVALENT_GLAZING_DISPOSABLE``.  The construction is not
assigned to geometry and the script never saves the project.
"""

import json
import math
import shutil
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPECTED_PROJECT_PREFIX = "sia4010_test1_1e_equivalent_glazing_disposable"
MARKER = "SIA4010_XN_EQUIVALENT_4_14_4_14_4_DIAGNOSTIC"
TARGET_U = 0.654
TARGET_G = 0.545
TARGET_VT = 0.742
GLASS_THICKNESS_M = 0.004
CAVITY_THICKNESS_M = 0.014
U_TOLERANCE = 0.001


def _resolve_enum(iesve, nested, top_level, member):
    container = getattr(iesve.VECdbProject, nested, None) or getattr(
        iesve, top_level, None
    )
    if container is None or not hasattr(container, member):
        raise RuntimeError("VE enum is unavailable: {}.{}".format(nested, member))
    return getattr(container, member)


def _cdb_project(iesve):
    projects = iesve.VECdbDatabase.get_current_database().get_projects()
    candidates = projects.get(0, []) if isinstance(projects, dict) else []
    if not candidates:
        raise RuntimeError("Current CDB has no editable project database")
    return candidates[0]


def _construction(cdb, iesve, identifier):
    classes = getattr(iesve.VECdbProject, "construction_class", None) or getattr(
        iesve, "construction_class", None
    )
    none_class = getattr(classes, "none", None) if classes is not None else None
    attempts = [(identifier, none_class)] if none_class is not None else []
    attempts.append((identifier,))
    for arguments in attempts:
        try:
            value = cdb.get_construction(*arguments)
        except Exception:
            continue
        if value is not None:
            return value
    raise RuntimeError("Construction is unavailable: {}".format(identifier))


def _material_id_from_extw(cdb, iesve):
    extw = _construction(cdb, iesve, "EXTW")
    for layer in list(extw.get_layers()):
        for opaque in (False, True):
            try:
                material = layer.get_material(opaque)
            except Exception:
                continue
            if material is None:
                continue
            properties = dict(material.get_properties())
            identifier = str(
                properties.get("id")
                or properties.get("material_id")
                or getattr(material, "id", "")
            )
            if identifier:
                return identifier, properties
    raise RuntimeError("No reusable glass material was found in EXTW")


def _iso_u_type(iesve):
    values = getattr(iesve.VECdbProject, "uvalue_types", None) or getattr(
        iesve, "uvalue_types", None
    )
    if values is None or not hasattr(values, "iso"):
        raise RuntimeError("VE ISO U-value enum is unavailable")
    return getattr(values, "iso")


def _set_equal_cavity_resistance(cavities, resistance):
    for cavity in cavities:
        cavity.set_properties(
            {"thickness": CAVITY_THICKNESS_M, "resistance": float(resistance)}
        )
    persisted = [float(dict(item.get_properties())["resistance"]) for item in cavities]
    if not all(math.isclose(value, persisted[0], abs_tol=1.0e-7) for value in persisted):
        raise RuntimeError("The two cavity resistances did not persist equally")
    return persisted[0]


def _calibrate(construction, cavities, u_type):
    lower = 0.000001
    upper = 10.0

    def evaluate(value):
        persisted = _set_equal_cavity_resistance(cavities, value)
        return persisted, float(construction.get_u_factor(u_type))

    _, u_lower = evaluate(lower)
    _, u_upper = evaluate(upper)
    if not (u_lower > TARGET_U > u_upper):
        raise RuntimeError(
            "Target U is not bracketed: U({})={}, U({})={}".format(
                lower, u_lower, upper, u_upper
            )
        )
    final_resistance = lower
    final_u = u_lower
    for _ in range(64):
        midpoint = (lower + upper) / 2.0
        final_resistance, final_u = evaluate(midpoint)
        if abs(final_u - TARGET_U) <= U_TOLERANCE / 10.0:
            break
        if final_u > TARGET_U:
            lower = midpoint
        else:
            upper = midpoint
    if abs(final_u - TARGET_U) > U_TOLERANCE:
        raise RuntimeError("U calibration failed: {}".format(final_u))
    return final_resistance, final_u


def _load_or_install_scenario(project_path, scenario_class):
    """Restore the non-VE scenario sidecar omitted by VE Save As."""

    target = project_path / "sia_model_scenario.json"
    if target.is_file():
        return scenario_class.load(target), False, None
    candidates = (
        project_path.parent
        / "SIA4010_TEST_1_1E_DISPOSABLE"
        / "sia_model_scenario.json",
        project_path.parent
        / "SIA4010_TEST1_1E_TEMPLATE"
        / "sia_model_scenario.json",
    )
    for source in candidates:
        if not source.is_file():
            continue
        scenario = scenario_class.load(source)
        if (scenario.variant, scenario.case_id) != ("test_1", "1E"):
            continue
        shutil.copy2(str(source), str(target))
        installed = scenario_class.load(target)
        return installed, True, source
    raise RuntimeError(
        "VE Save As omitted sia_model_scenario.json and no validated sibling "
        "test_1/1E scenario was found"
    )


def run():
    import iesve  # type: ignore

    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario

    project = iesve.VEProject.get_current_project()
    project_path = Path(str(getattr(project, "path", "") or "")).resolve()
    if not project_path.name.casefold().startswith(EXPECTED_PROJECT_PREFIX):
        raise RuntimeError(
            "Use Save As to create SIA4010_TEST1_1E_EQUIVALENT_GLAZING_DISPOSABLE, "
            "open that fresh copy, then rerun. Active folder: {}".format(
                project_path.name
            )
        )
    scenario, scenario_installed, scenario_source = _load_or_install_scenario(
        project_path, ModelScenario
    )
    if (scenario.variant, scenario.case_id) != ("test_1", "1E"):
        raise RuntimeError("The fresh copy must retain official test_1/1E")

    output = (
        project_path
        / "sia4010_artifacts"
        / "diagnostics"
        / "sia4010_test1e_equivalent_5layer_glazing.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_file():
        try:
            previous = json.loads(output.read_text(encoding="utf-8"))
        except Exception:
            previous = {}
        if previous.get("status") != "UNASSIGNED_EQUIVALENT_5LAYER_CREATED_AND_VERIFIED":
            raise RuntimeError(
                "A previous attempt crossed the CDB mutation boundary in this "
                "copy. Close it without saving, create a fresh V2 copy, and rerun."
            )
        raise RuntimeError(
            "A verified equivalent construction already exists in this copy"
        )
    report = {
        "schema_version": "1.0",
        "status": "STARTED",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project": str(project_path),
        "scenario_sidecar_installed": scenario_installed,
        "scenario_sidecar_source": str(scenario_source or ""),
        "construction_marker": MARKER,
        "assigned_to_openings": False,
        "project_saved_by_script": False,
        "manufacturer_product_claim": False,
        "compliance_claim_allowed": False,
    }
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    cdb = _cdb_project(iesve)
    glazed_class = _resolve_enum(
        iesve, "construction_class", "construction_class", "glazed"
    )
    category = _resolve_enum(
        iesve, "element_categories", "element_categories", "ext_glazing"
    )
    existing = []
    for identifier in list(cdb.get_construction_ids(glazed_class)):
        item = _construction(cdb, iesve, str(identifier))
        text = "{} {}".format(identifier, getattr(item, "reference", ""))
        try:
            text += " " + json.dumps(dict(item.get_properties()), default=str)
        except Exception:
            pass
        if MARKER.casefold() in text.casefold():
            existing.append(str(identifier))
    if existing:
        raise RuntimeError(
            "Equivalent diagnostic construction already exists: {}".format(existing)
        )

    glass_id, glass_properties = _material_id_from_extw(cdb, iesve)
    construction = cdb.create_construction(category)
    construction.set_const_class(glazed_class)
    initial_layers = list(construction.get_layers())
    initial_ids = [layer.get_id() for layer in initial_layers]
    before = dict(construction.get_properties())
    requested_properties = {
        "g_value": TARGET_G,
        "visible_light_transmittance": TARGET_VT,
        "frame_percent": 0.0,
    }
    if "description" in before:
        requested_properties["description"] = MARKER
    construction.set_properties(requested_properties)

    for is_cavity in (False, True, False, True, False):
        construction.add_layer(glass_id, is_cavity)
    for initial_id in initial_ids:
        construction.delete_layer(initial_id)
    layers = list(construction.get_layers())
    if len(layers) != 5:
        raise RuntimeError("Expected five layers; found {}".format(len(layers)))
    glass_layers = [layers[index] for index in (0, 2, 4)]
    cavities = [layers[index] for index in (1, 3)]
    for layer in glass_layers:
        layer.set_properties({"thickness": GLASS_THICKNESS_M})
    cavity_resistance, verified_u = _calibrate(
        construction, cavities, _iso_u_type(iesve)
    )
    after = dict(construction.get_properties())
    verified_g = float(after["g_value"])
    verified_vt = float(after["visible_light_transmittance"])
    if abs(verified_g - TARGET_G) > 1.0e-6 or abs(verified_vt - TARGET_VT) > 1.0e-6:
        raise RuntimeError("Construction optical read-back mismatch")
    layer_readback = [dict(layer.get_properties()) for layer in layers]
    expected_thicknesses = [0.004, 0.014, 0.004, 0.014, 0.004]
    for expected, actual in zip(expected_thicknesses, layer_readback):
        if abs(float(actual["thickness"]) - expected) > 1.0e-6:
            raise RuntimeError("Layer thickness read-back mismatch")

    report.update(
        {
            "status": "UNASSIGNED_EQUIVALENT_5LAYER_CREATED_AND_VERIFIED",
            "construction_id": str(getattr(construction, "id", "")),
            "source_glass_material_id": glass_id,
            "source_glass_material_properties": glass_properties,
            "targets": {
                "layer_thicknesses_m": expected_thicknesses,
                "u_w_m2k": TARGET_U,
                "g_value": TARGET_G,
                "visible_light_transmittance": TARGET_VT,
            },
            "readback": {
                "layers": layer_readback,
                "equal_cavity_resistance_m2k_w": cavity_resistance,
                "u_w_m2k": verified_u,
                "g_value": verified_g,
                "visible_light_transmittance": verified_vt,
            },
            "limitations": [
                "Existing VE glass material is a proxy, not manufacturer Planitherm XN layer data.",
                "Gas composition, coating placement, emissivities and layer-resolved optics are unconfirmed.",
                "Construction is deliberately unassigned and cannot establish a Test 1 PASS.",
            ],
            "next_action": "Send this output for review before any opening assignment.",
        }
    )
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    print("SIA 4010 TEST 1E EQUIVALENT 5-LAYER GLAZING: {}".format(report["status"]))
    print("Construction: {}".format(report["construction_id"]))
    print("Layers: 4/14/4/14/4 mm")
    print("U: {}; g: {}; VT: {}".format(verified_u, verified_g, verified_vt))
    print("Assigned to openings: NO")
    print("Project saved by script: NO")
    print("Report: {}".format(output))
    print("NEXT: send this complete output before assignment.")
    return output


if __name__ == "__main__":
    run()
