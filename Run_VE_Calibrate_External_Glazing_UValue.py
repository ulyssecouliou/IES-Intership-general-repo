"""Calibrate the existing reference glazing to its traced VE U-value target.

This controlled migration upgrades the assigned one-pane equivalent construction
to glass/cavity/glass without ever deleting its sole layer.  The cavity
resistance is solved against VE's own ISO U-factor read-back, then written back
to the project asset manifest with provenance so later resume runs are
reproducible.  No geometry, template, profile, gain, air exchange, or weather
data is changed.
"""

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

for module_name in tuple(sys.modules):
    if module_name == "swiss_sia.reference_model" or module_name.startswith(
        "swiss_sia.reference_model."
    ):
        del sys.modules[module_name]

from swiss_sia.reference_model.asset_manifest import load_asset_manifest
from swiss_sia.reference_model.config_loader import load_configuration
from swiss_sia.reference_model.exceptions import VeMutationError
from swiss_sia.reference_model.ve_api import IesVeGateway


GLAZING_KEY = "external_glazing"
GLASS_MATERIAL_KEY = "equivalent_glazing_layer"


def _material_id(layer):
    material = layer.get_material(False)
    if material is None:
        return ""
    value = getattr(material, "id", None)
    if value:
        return str(value)
    properties = dict(material.get_properties())
    return str(properties.get("id", properties.get("material_id", "")))


def _traceable_resistance(value):
    return {
        "value": value,
        "description": (
            "Equivalent sealed-cavity resistance numerically calibrated against "
            "the VE ISO whole-window U-factor read-back."
        ),
        "units": "m2 K/W",
        "source": "Runtime VE CDB ISO U-factor calibration",
        "source_locator": (
            "Run_VE_Calibrate_External_Glazing_UValue.py; replace with approved "
            "manufacturer glazing data before certification"
        ),
        "validation_range": {
            "expected_type": "number",
            "minimum": 0.000001,
            "maximum": 100.0,
            "allow_none": False,
        },
        "required": True,
    }


def _update_manifest(path, construction_id, target, actual, resistance, ve_version):
    original = path.read_bytes()
    payload = json.loads(original.decode("utf-8"))
    matches = [
        item
        for item in payload.get("constructions", [])
        if item.get("key") == GLAZING_KEY
    ]
    if len(matches) != 1:
        raise VeMutationError(
            "Expected exactly one external_glazing manifest definition"
        )
    matches[0]["layers"] = [
        {
            "material_key": GLASS_MATERIAL_KEY,
            "is_cavity": False,
            "properties": {},
        },
        {
            "material_key": GLASS_MATERIAL_KEY,
            "is_cavity": True,
            "properties": {"resistance": _traceable_resistance(resistance)},
        },
        {
            "material_key": GLASS_MATERIAL_KEY,
            "is_cavity": False,
            "properties": {},
        },
    ]
    payload.setdefault("metadata", {})["external_glazing_runtime_calibration"] = {
        "construction_id": construction_id,
        "target_u_w_m2k": target,
        "verified_u_w_m2k": actual,
        "cavity_resistance_m2k_w": resistance,
        "ve_version": ve_version,
        "status": "engineering-equivalent; manufacturer verification pending",
    }
    backup = path.with_name(path.stem + ".pre_glazing_calibration.json")
    if not backup.exists():
        backup.write_bytes(original)
    candidate = path.with_name(path.stem + ".calibration_candidate.json")
    candidate.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    try:
        # Validate the candidate before replacing the active manifest.
        load_asset_manifest(candidate)
        path.write_bytes(candidate.read_bytes())
    finally:
        if candidate.exists():
            candidate.unlink()
    return backup


def run():
    gateway = IesVeGateway()
    config_path = gateway.project_path / "reference_model_config.json"
    parameters = load_configuration(config_path if config_path.is_file() else None)
    manifest_setting = parameters.value("asset_manifest_file")
    if not manifest_setting:
        raise VeMutationError("asset_manifest_file is unresolved")
    manifest_path = Path(str(manifest_setting))
    if not manifest_path.is_absolute():
        manifest_path = gateway.project_path / manifest_path
    manifest = load_asset_manifest(manifest_path)

    # This call strictly reuses and verifies the existing assets before the
    # controlled glazing migration; it does not create duplicates.
    receipt = gateway.provision_assets(manifest)
    construction_id = receipt.construction_ids[GLAZING_KEY]
    glass_material_id = receipt.material_ids[GLASS_MATERIAL_KEY]
    construction = gateway._get_construction(construction_id)
    layers = list(construction.get_layers())
    if len(layers) not in (1, 2, 3):
        raise VeMutationError(
            "Glazing calibration requires 1-3 known layers; found {}".format(
                len(layers)
            )
        )
    if _material_id(layers[0]) != glass_material_id:
        raise VeMutationError("Unexpected external glazing outer-pane material")

    if len(layers) == 1:
        construction.add_layer(glass_material_id, True)
        layers = list(construction.get_layers())
    if len(layers) == 2:
        # Establish a positive cavity property before appending the inner pane.
        layers[1].set_properties({"resistance": 1.0})
        construction.add_layer(glass_material_id, False)
        layers = list(construction.get_layers())
    if len(layers) != 3:
        raise VeMutationError("Glass/cavity/glass layer creation did not persist")
    if _material_id(layers[0]) != glass_material_id:
        raise VeMutationError("Outer-pane material changed during calibration")
    if _material_id(layers[1]):
        raise VeMutationError("Middle glazing layer is not a native VE cavity")
    if _material_id(layers[2]) != glass_material_id:
        raise VeMutationError("Inner-pane material did not persist")

    target = float(parameters.value("project_window_u_w_m2k"))
    qa_tolerance = float(
        parameters.value("construction_u_value_tolerance_w_m2k")
    )
    solve_tolerance = max(qa_tolerance / 10.0, 0.000001)
    cavity = layers[1]
    uvalue_type = gateway._uvalue_type_iso()

    def evaluate(requested_resistance):
        cavity.set_properties({"resistance": requested_resistance})
        actual_resistance = float(cavity.get_properties()["resistance"])
        actual_u = float(construction.get_u_factor(uvalue_type))
        return actual_resistance, actual_u

    lower = 0.000001
    upper = 10.0
    _, u_lower = evaluate(lower)
    _, u_upper = evaluate(upper)
    if not (u_lower > target > u_upper):
        raise VeMutationError(
            "VE U-factor target is not bracketed: target={}, U({})={}, U({})={}".format(
                target, lower, u_lower, upper, u_upper
            )
        )

    final_resistance = None
    final_u = None
    for _ in range(60):
        midpoint = (lower + upper) / 2.0
        actual_resistance, actual_u = evaluate(midpoint)
        final_resistance, final_u = actual_resistance, actual_u
        if abs(actual_u - target) <= solve_tolerance:
            break
        if actual_u > target:
            lower = midpoint
        else:
            upper = midpoint
    if final_u is None or abs(final_u - target) > qa_tolerance:
        raise VeMutationError(
            "VE glazing calibration failed: target={}, actual={}".format(
                target, final_u
            )
        )

    backup = _update_manifest(
        manifest_path,
        construction_id,
        target,
        final_u,
        final_resistance,
        gateway._safe_version(),
    )
    print("CONTROLLED EXTERNAL-GLAZING U-VALUE CALIBRATION: PASS")
    print("Project: {}".format(gateway.project_name))
    print("Construction ID: {}".format(construction_id))
    print("Target U-value: {:.9f} W/(m2 K)".format(target))
    print("VE verified U-value: {:.9f} W/(m2 K)".format(final_u))
    print("Calibrated cavity resistance: {:.9f} m2 K/W".format(final_resistance))
    print("Updated manifest: {}".format(manifest_path))
    print("Manifest backup: {}".format(backup))
    print(
        "No geometry, template, profile, gain, air exchange, HVAC, or weather data was changed."
    )


if __name__ == "__main__":
    run()
