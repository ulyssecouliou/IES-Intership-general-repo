"""Guarded, reversible Test 1/640 surface-coefficient mechanism probe.

This diagnostic tests whether the boundary layers' documented
``convection_coefficient`` field controls ApacheSim surface-film coefficients.
It is deliberately fail-closed: runtime layer order must match the source
manifest, U-factors must remain unchanged, and all CDB fields and ApacheSim
options must be restored.  It never registers compliance evidence.
"""

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import iesve


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ISO_EXTERNAL_CONVECTIVE = 20.0
ISO_INTERNAL_CONVECTIVE = {
    "external_wall": 2.5,
    "roof": 5.0,
    "ground_floor": 0.7,
}
CONSTRUCTION_PARAMETER = {
    "external_wall": "external_wall_construction_id",
    "roof": "roof_construction_id",
    "ground_floor": "ground_floor_construction_id",
}
U_FACTOR_ABORT_TOLERANCE = 1.0e-5


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _wait_for_aps(path, timeout=30.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_file() and path.stat().st_size > 0:
            return
        time.sleep(0.1)
    raise RuntimeError("Diagnostic APS was not created: {}".format(path))


def _sequence(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return [value]


def _room_id(item):
    if isinstance(item, dict):
        return item.get("id") or item.get("room_id")
    if isinstance(item, (list, tuple)) and len(item) >= 2:
        return item[1]
    return None


def _cdb_project():
    projects = iesve.VECdbDatabase.get_current_database().get_projects()
    candidates = projects.get(0, []) if isinstance(projects, dict) else []
    if not candidates:
        raise RuntimeError("Current CDB has no editable project database")
    return candidates[0]


def _enum_container(nested, top_level):
    return getattr(iesve.VECdbProject, nested, None) or getattr(
        iesve, top_level, None
    )


def _construction(cdb_project, identifier):
    classes = _enum_container("construction_class", "construction_class")
    attempts = []
    if classes is not None and hasattr(classes, "opaque"):
        attempts.append((identifier, getattr(classes, "opaque")))
    attempts.append((identifier,))
    last_error = None
    for arguments in attempts:
        try:
            value = cdb_project.get_construction(*arguments)
        except Exception as exc:
            last_error = exc
            continue
        if value is not None:
            return value
    raise RuntimeError(
        "Unable to resolve construction {!r}: {}".format(identifier, last_error)
    )


def _iso_u_factor(construction):
    types = _enum_container("uvalue_types", "uvalue_types")
    if types is None or not hasattr(types, "iso"):
        raise RuntimeError("VE ISO U-factor enum is unavailable")
    return float(construction.get_u_factor(getattr(types, "iso")))


def _key_metric(comparisons, title_fragment, suffix):
    for comparison in comparisons:
        key = str(comparison.get("key", ""))
        if title_fragment in key and key.endswith("| " + suffix):
            return {
                "key": key,
                "expected": comparison.get("expected_value"),
                "observed": comparison.get("observed_value"),
                "absolute_difference": comparison.get("absolute_difference"),
                "unit": comparison.get("unit"),
            }
    return None


def _surface_coefficient_rows(results, inventory):
    from swiss_sia.simulation_results import (
        convert_aps_series_to_metric,
        get_available_variables,
        read_surface_result,
    )

    requested_names = (
        "External convective surface coefficient",
        "Internal convective surface coefficient",
    )
    variables = get_available_variables(results)
    bindings = {}
    for requested in requested_names:
        matches = [
            item
            for item in variables
            if str(item.get("aps_varname") or "").strip().lower()
            == requested.lower()
            and str(item.get("model_level") or "").strip().lower() == "s"
        ]
        if len(matches) == 1:
            bindings[requested] = matches[0]
    if len(bindings) != len(requested_names):
        raise RuntimeError(
            "Diagnostic APS did not expose both surface coefficient variables"
        )
    aps_room_ids = [
        value
        for value in (_room_id(item) for item in _sequence(results.get_room_list()))
        if value is not None
    ]
    rows = []
    for surface in inventory:
        handle = surface.get("aps_handle")
        if handle is None:
            continue
        candidates = []
        for value in [surface.get("room_id")] + aps_room_ids:
            if value is not None and value not in candidates:
                candidates.append(value)
        for requested, variable in bindings.items():
            aps_var = str(variable.get("aps_varname") or requested)
            display = str(variable.get("display_name") or aps_var)
            raw = []
            for room_id in candidates:
                raw = read_surface_result(results, room_id, handle, aps_var, display)
                if raw:
                    break
            aps_tuple = (
                aps_var,
                display,
                "s",
                str(variable.get("resolved_metric_unit") or ""),
                float(variable.get("resolved_metric_divisor") or 1.0),
                float(variable.get("resolved_metric_offset") or 0.0),
            )
            values = convert_aps_series_to_metric(raw, aps_tuple) if raw else []
            rows.append(
                {
                    "surface_id": surface.get("surface_id"),
                    "surface_type": surface.get("surface_type"),
                    "variable": requested,
                    "count": len(values),
                    "minimum": min(values) if values else None,
                    "maximum": max(values) if values else None,
                    "mean": sum(values) / len(values) if values else None,
                }
            )
    return rows


def run():
    from swiss_sia.reference_model.sia4010.active_case_evaluation import (
        evaluate_qualified_active_case,
    )
    from swiss_sia.reference_model.sia4010.aps_probe import build_surface_inventory
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.simulation_results import open_results_reader

    project = iesve.VEProject.get_current_project()
    project_root = Path(str(project.path)).resolve()
    scenario = ModelScenario.load(project_root / "sia_model_scenario.json")
    if (scenario.variant, scenario.case_id) != ("test_1", "640"):
        raise RuntimeError(
            "Surface-coefficient A/B is guarded for test_1/640; active is {}/{}"
            .format(scenario.variant, scenario.case_id)
        )

    report_path = (
        project_root
        / "reference_model_artifacts"
        / "reports"
        / "reference_model_report.json"
    )
    manifest_path = project_root / "reference_model_assets.json"
    if not report_path.is_file() or not manifest_path.is_file():
        raise RuntimeError("Reference-model report or asset manifest is missing")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_constructions = {
        item["key"]: item for item in manifest.get("constructions", [])
    }

    cdb = _cdb_project()
    targets = {}
    for key, parameter_name in CONSTRUCTION_PARAMETER.items():
        parameter = report.get("parameters", {}).get(parameter_name, {})
        identifier = str(parameter.get("value") or "")
        if not identifier:
            raise RuntimeError("Missing construction parameter: {}".format(parameter_name))
        definition = manifest_constructions.get(key)
        if definition is None:
            raise RuntimeError("Manifest construction is missing: {}".format(key))
        construction = _construction(cdb, identifier)
        layers = list(construction.get_layers())
        expected_thicknesses = [
            float(layer["properties"]["thickness"]["value"])
            for layer in definition.get("layers", [])
        ]
        actual_thicknesses = [
            float(dict(layer.get_properties()).get("thickness")) for layer in layers
        ]
        if len(layers) < 2 or len(actual_thicknesses) != len(expected_thicknesses):
            raise RuntimeError("Unexpected layer count for {}".format(key))
        if any(
            abs(actual - expected) > 1.0e-5
            for actual, expected in zip(actual_thicknesses, expected_thicknesses)
        ):
            raise RuntimeError(
                "Runtime layer order does not match manifest for {}: expected={}, "
                "actual={}".format(key, expected_thicknesses, actual_thicknesses)
            )
        targets[key] = {
            "identifier": identifier,
            "construction": construction,
            "layers": layers,
            "expected_thicknesses_m": expected_thicknesses,
            "original_external": dict(layers[0].get_properties()),
            "original_internal": dict(layers[-1].get_properties()),
            "u_factor_before": _iso_u_factor(construction),
        }

    simulator = iesve.ApacheSim()
    original_options = dict(simulator.get_options())
    option_names = (
        "start_day",
        "start_month",
        "end_day",
        "end_month",
        "reporting_interval",
        "results_filename",
        "detailed_rooms",
        "detailed_external_solar",
    )
    missing_options = [name for name in option_names if name not in original_options]
    if missing_options:
        raise RuntimeError(
            "ApacheSim options required for restoration are missing: {}".format(
                missing_options
            )
        )
    restore_options = {name: original_options[name] for name in option_names}
    inventory = build_surface_inventory(project)
    room_ids = sorted(
        {item.get("room_id") for item in inventory if item.get("room_id") is not None}
    )
    if len(room_ids) != 1:
        raise RuntimeError("Expected exactly one model room; found {}".format(room_ids))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    aps_name = "SIA4010_test_1_640_SURFACE_COEFFICIENT_AB_{}.aps".format(stamp)
    aps_path = project_root / "Vista" / aps_name
    diagnostics = project_root / "sia4010_artifacts" / "diagnostics"
    evaluation_path = diagnostics / (
        "SIA4010_test_1_640_surface_coefficient_ab_evaluation.json"
    )
    audit_path = diagnostics / "SIA4010_test_1_640_surface_coefficient_ab.json"
    recovery_path = diagnostics / (
        "SIA4010_test_1_640_surface_coefficient_ab_recovery.json"
    )
    applied_options = {
        "start_day": 1,
        "start_month": 1,
        "end_day": 31,
        "end_month": 12,
        "reporting_interval": 3,
        "results_filename": aps_name,
        "detailed_rooms": room_ids,
        "detailed_external_solar": True,
    }

    payload = None
    options_restored = False
    cdb_restored = False
    _write_json(
        recovery_path,
        {
            "schema_version": "1.0",
            "status": "ORIGINAL_VALUES_CAPTURED_BEFORE_MUTATION",
            "case": "test_1/640",
            "constructions": {
                key: {
                    "identifier": item["identifier"],
                    "external_layer_index": 0,
                    "external_convection_coefficient": item[
                        "original_external"
                    ].get("convection_coefficient", 0.0),
                    "internal_layer_index": len(item["layers"]) - 1,
                    "internal_convection_coefficient": item[
                        "original_internal"
                    ].get("convection_coefficient", 0.0),
                    "expected_thicknesses_m": item["expected_thicknesses_m"],
                    "u_factor_before": item["u_factor_before"],
                }
                for key, item in targets.items()
            },
            "purpose": "Crash-recovery receipt; not compliance evidence.",
        },
    )
    try:
        for key, item in targets.items():
            item["layers"][0].set_properties(
                {"convection_coefficient": ISO_EXTERNAL_CONVECTIVE}
            )
            item["layers"][-1].set_properties(
                {"convection_coefficient": ISO_INTERNAL_CONVECTIVE[key]}
            )
            external_readback = float(
                dict(item["layers"][0].get_properties()).get(
                    "convection_coefficient"
                )
            )
            internal_readback = float(
                dict(item["layers"][-1].get_properties()).get(
                    "convection_coefficient"
                )
            )
            if abs(external_readback - ISO_EXTERNAL_CONVECTIVE) > 1.0e-6:
                raise RuntimeError("External coefficient did not persist for {}".format(key))
            if abs(internal_readback - ISO_INTERNAL_CONVECTIVE[key]) > 1.0e-6:
                raise RuntimeError("Internal coefficient did not persist for {}".format(key))
            item["applied_external"] = external_readback
            item["applied_internal"] = internal_readback
            item["u_factor_after"] = _iso_u_factor(item["construction"])
            if (
                abs(item["u_factor_after"] - item["u_factor_before"])
                > U_FACTOR_ABORT_TOLERANCE
            ):
                raise RuntimeError(
                    "Coefficient setter changed {} U-factor from {} to {}; "
                    "simulation aborted".format(
                        key, item["u_factor_before"], item["u_factor_after"]
                    )
                )

        if simulator.set_options(applied_options) is not True:
            raise RuntimeError("ApacheSim rejected surface-coefficient A/B options")
        if simulator.run_simulation(queue_to_tasks=False) is not True:
            status_path = project_root / "apache" / "status.json"
            detail = (
                status_path.read_text(encoding="utf-8")
                if status_path.is_file()
                else ""
            )
            raise RuntimeError(
                "Surface-coefficient A/B simulation failed: {}".format(detail)
            )
        _wait_for_aps(aps_path)
        results = open_results_reader(aps_name)
        aps_room_ids = [
            value
            for value in (_room_id(item) for item in _sequence(results.get_room_list()))
            if value is not None
        ]
        if len(aps_room_ids) != 1:
            raise RuntimeError(
                "Expected exactly one APS room; found {}".format(aps_room_ids)
            )
        receipt = evaluate_qualified_active_case(
            variant="test_1",
            case_id="640",
            results_file=results,
            room_id=aps_room_ids[0],
            aps_path=aps_path,
            bundle_root=ROOT / "SIA_4010_geteilter_Link",
            bindings_path=ROOT / "config" / "sia4010_aps_bindings_ve_runtime.json",
            output_path=evaluation_path,
        )
        evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
        comparisons = evaluation["evaluation"]["comparisons"]
        payload = {
            "schema_version": "1.0",
            "status": "DIAGNOSTIC_RESULTS_RECORDED",
            "case": "test_1/640",
            "mechanism_under_test": (
                "VECdbLayer.convection_coefficient on manifest-verified outer "
                "and inner boundary layers"
            ),
            "constructions": {
                key: {
                    name: value
                    for name, value in item.items()
                    if name
                    in {
                        "identifier",
                        "expected_thicknesses_m",
                        "u_factor_before",
                        "u_factor_after",
                        "applied_external",
                        "applied_internal",
                    }
                }
                for key, item in targets.items()
            },
            "surface_coefficients": _surface_coefficient_rows(results, inventory),
            "thermal_key_metrics": {
                "annual_heating": _key_metric(comparisons, "heating", "Annual"),
                "annual_cooling": _key_metric(comparisons, "cooling", "Annual"),
                "peak_heating": _key_metric(
                    comparisons, "peak heating", "Heating"
                ),
                "peak_cooling": _key_metric(
                    comparisons, "peak heating", "Cooling"
                ),
            },
            "aps": {"path": str(aps_path), "sha256": _sha256(aps_path)},
            "evaluation": str(evaluation_path),
            "evaluation_status": receipt.status,
            "observed_metric_count": receipt.observed_metric_count,
            "compliance_claim_allowed": False,
        }
    finally:
        try:
            options_restored = simulator.set_options(restore_options) is True
        finally:
            restoration_errors = []
            for key, item in targets.items():
                try:
                    item["layers"][0].set_properties(
                        {
                            "convection_coefficient": item["original_external"].get(
                                "convection_coefficient", 0.0
                            )
                        }
                    )
                    item["layers"][-1].set_properties(
                        {
                            "convection_coefficient": item["original_internal"].get(
                                "convection_coefficient", 0.0
                            )
                        }
                    )
                    restored_external = float(
                        dict(item["layers"][0].get_properties()).get(
                            "convection_coefficient"
                        )
                    )
                    restored_internal = float(
                        dict(item["layers"][-1].get_properties()).get(
                            "convection_coefficient"
                        )
                    )
                    if abs(
                        restored_external
                        - float(
                            item["original_external"].get(
                                "convection_coefficient", 0.0
                            )
                        )
                    ) > 1.0e-6 or abs(
                        restored_internal
                        - float(
                            item["original_internal"].get(
                                "convection_coefficient", 0.0
                            )
                        )
                    ) > 1.0e-6:
                        restoration_errors.append(key)
                except Exception as exc:
                    restoration_errors.append("{}: {}".format(key, exc))
            cdb_restored = not restoration_errors
    if not options_restored or not cdb_restored:
        raise RuntimeError(
            "A/B restoration failed: options={}, cdb={}".format(
                options_restored, cdb_restored
            )
        )
    payload["restoration"] = {
        "apache_options_restored": True,
        "cdb_layer_coefficients_restored": True,
        "recovery_receipt": str(recovery_path),
    }
    _write_json(audit_path, payload)
    print("SIA 4010 TEST 1 SURFACE-COEFFICIENT A/B: {}".format(payload["status"]))
    print("Case: test_1/640")
    for row in payload["surface_coefficients"]:
        if row["count"]:
            print(
                "{} | {} | mean={}".format(
                    row["surface_type"], row["variable"], row["mean"]
                )
            )
    for name, metric in payload["thermal_key_metrics"].items():
        print("{}: {}".format(name, metric))
    print("Diagnostic APS: {}".format(aps_path))
    print("Audit: {}".format(audit_path))
    print("Original CDB layer fields and ApacheSim options were restored.")
    print("No compliance evidence was registered.")
    return payload


if __name__ == "__main__":
    run()
