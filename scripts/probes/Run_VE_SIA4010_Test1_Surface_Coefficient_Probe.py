"""Read-only Test 1 probe of ApacheSim surface convection coefficients."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import iesve


ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

VARIABLES = (
    "External convective surface coefficient",
    "Internal convective surface coefficient",
    "External radiative surface coefficient",
    "Internal radiative surface coefficient",
)
ISO_EXTERNAL_CONVECTIVE = 20.0
ISO_EXTERNAL_RADIATIVE = 4.14
ISO_INTERNAL_RADIATIVE = 5.13
ISO_INTERNAL_CONVECTIVE = {
    "wall": 2.5,
    "roof": 5.0,
    "ceiling": 5.0,
    "floor": 0.7,
    "ground": 0.7,
}


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _resolve_source_aps(project_root):
    """Return the most relevant qualified Test 1 APS and its audit record.

    The original diagnostic was written for case 640 only.  A qualified-template
    Test 1E run records the APS directly in its simulation audit, so support both
    evidence shapes without selecting an untracked ``Vista`` file by timestamp.
    """

    candidates = (
        project_root
        / "sia4010_artifacts"
        / "simulation"
        / "SIA4010_test_1_1E_template_apachesim.json",
        project_root
        / "sia4010_artifacts"
        / "diagnostics"
        / "SIA4010_test_1_640_iso_weather_ab.json",
    )
    for audit_path in candidates:
        if not audit_path.is_file():
            continue
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        aps_value = audit.get("results_path")
        if not aps_value:
            aps_value = (audit.get("aps") or {}).get("path")
        aps_path = Path(str(aps_value or ""))
        if not aps_path.is_file():
            raise RuntimeError(
                "Surface-coefficient source APS is missing: {}".format(aps_path)
            )
        variant = str(audit.get("variant") or "test_1")
        case_id = str(audit.get("case_id") or "640")
        return audit_path, aps_path, "{}/{}".format(variant, case_id)
    raise RuntimeError(
        "No qualified Test 1 APS audit is available for the active project"
    )


def _room_id(item):
    if isinstance(item, dict):
        return item.get("id") or item.get("room_id")
    if isinstance(item, (list, tuple)) and len(item) >= 2:
        return item[1]
    return None


def _iso_internal_target(surface_type):
    normalized = str(surface_type or "").lower()
    for token, target in ISO_INTERNAL_CONVECTIVE.items():
        if token in normalized:
            return target
    return None


def _summary(values):
    if not values:
        return {"count": 0, "minimum": None, "maximum": None, "mean": None}
    return {
        "count": len(values),
        "minimum": min(values),
        "maximum": max(values),
        "mean": sum(values) / len(values),
    }


def _coefficient_binding(variables, requested):
    """Resolve VE wording variants without guessing a non-coefficient series."""

    requested_lower = requested.lower()
    exact = [
        item
        for item in variables
        if str(item.get("aps_varname") or "").strip().lower()
        == requested_lower
        and str(item.get("model_level") or "").strip().lower() == "s"
    ]
    if exact:
        return exact[0]
    boundary = "external" if requested_lower.startswith("external") else "internal"
    transfer = "radiat" if "radiat" in requested_lower else "convect"
    semantic = []
    for item in variables:
        if str(item.get("model_level") or "").strip().lower() != "s":
            continue
        text = "{} {}".format(
            item.get("aps_varname") or "", item.get("display_name") or ""
        ).lower()
        if boundary in text and transfer in text and "coefficient" in text:
            semantic.append(item)
    return semantic[0] if len(semantic) == 1 else None


def run():
    from swiss_sia.reference_model.sia4010.aps_probe import (
        build_surface_inventory,
    )
    from swiss_sia.simulation_results import (
        convert_aps_series_to_metric,
        get_available_variables,
        open_results_reader,
        read_surface_result,
    )

    project = iesve.VEProject.get_current_project()
    project_root = Path(str(project.path)).resolve()
    source_audit, aps_path, case_label = _resolve_source_aps(project_root)

    results = open_results_reader(aps_path.name)
    variables = get_available_variables(results)
    bindings = {}
    for requested in VARIABLES:
        match = _coefficient_binding(variables, requested)
        if match is not None:
            bindings[requested] = match

    aps_room_ids = [
        value
        for value in (_room_id(item) for item in list(results.get_room_list() or []))
        if value is not None
    ]
    inventory = build_surface_inventory(project)
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
            resolved_room_id = None
            for room_id in candidates:
                raw = read_surface_result(results, room_id, handle, aps_var, display)
                if raw:
                    resolved_room_id = room_id
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
            observed = _summary(values)
            if requested == "External convective surface coefficient":
                target = ISO_EXTERNAL_CONVECTIVE
            elif requested == "External radiative surface coefficient":
                target = ISO_EXTERNAL_RADIATIVE
            elif requested == "Internal radiative surface coefficient":
                target = ISO_INTERNAL_RADIATIVE
            else:
                target = _iso_internal_target(surface.get("surface_type"))
            rows.append(
                {
                    "surface": surface,
                    "variable": requested,
                    "metric_unit": aps_tuple[3],
                    "resolved_results_room_id": resolved_room_id,
                    "observed": observed,
                    "iso_target_w_m2k": target,
                    "mean_minus_iso": (
                        observed["mean"] - target
                        if observed["mean"] is not None and target is not None
                        else None
                    ),
                }
            )

    populated = [row for row in rows if row["observed"]["count"]]
    combined_checks = []
    for surface in inventory:
        surface_id = surface.get("surface_id") or surface.get("id")
        same_surface = [
            row
            for row in populated
            if (row["surface"].get("surface_id") or row["surface"].get("id"))
            == surface_id
        ]
        for boundary in ("External", "Internal"):
            convective = next(
                (
                    row
                    for row in same_surface
                    if row["variable"]
                    == "{} convective surface coefficient".format(boundary)
                ),
                None,
            )
            radiative = next(
                (
                    row
                    for row in same_surface
                    if row["variable"]
                    == "{} radiative surface coefficient".format(boundary)
                ),
                None,
            )
            if convective is None or radiative is None:
                continue
            observed_total = (
                convective["observed"]["mean"]
                + radiative["observed"]["mean"]
            )
            target_total = (
                convective["iso_target_w_m2k"]
                + radiative["iso_target_w_m2k"]
            )
            combined_checks.append(
                {
                    "surface_id": surface_id,
                    "surface_type": surface.get("surface_type"),
                    "boundary": boundary.lower(),
                    "observed_total_w_m2k": observed_total,
                    "iso_total_w_m2k": target_total,
                    "difference_w_m2k": observed_total - target_total,
                }
            )
    coefficient_candidates = [
        {
            "aps_varname": item.get("aps_varname"),
            "display_name": item.get("display_name"),
            "model_level": item.get("model_level"),
            "metric_unit": item.get("resolved_metric_unit"),
        }
        for item in variables
        if "coefficient" in str(
            item.get("aps_varname") or item.get("display_name") or ""
        ).lower()
    ]
    status = (
        "READY_FOR_BOUNDARY_CONDITION_REVIEW"
        if populated
        else "APS_COEFFICIENT_SERIES_NOT_AVAILABLE"
    )
    payload = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "case": case_label,
        "source_aps": str(aps_path),
        "source_audit": str(source_audit),
        "available_bindings": sorted(bindings),
        "surface_count": len(inventory),
        "populated_series": len(populated),
        "iso_targets": {
            "external_convective_w_m2k": ISO_EXTERNAL_CONVECTIVE,
            "internal_wall_w_m2k": 2.5,
            "internal_roof_upwards_w_m2k": 5.0,
            "internal_floor_downwards_w_m2k": 0.7,
            "external_radiative_w_m2k": ISO_EXTERNAL_RADIATIVE,
            "internal_radiative_w_m2k": ISO_INTERNAL_RADIATIVE,
            "source": "BS EN ISO 52016-1:2017 Table 25",
        },
        "available_coefficient_candidates": coefficient_candidates,
        "combined_convective_plus_radiative_checks": combined_checks,
        "results": rows,
        "model_or_aps_changed": False,
        "compliance_claim_allowed": False,
    }
    output = (
        project_root
        / "sia4010_artifacts"
        / "diagnostics"
        / "sia4010_test1_surface_coefficient_probe.json"
    )
    _write_json(output, payload)

    print("SIA 4010 TEST 1 SURFACE-COEFFICIENT PROBE: {}".format(status))
    print("Case: {}".format(case_label))
    print("APS: {}".format(aps_path))
    print("Bindings: {}".format(sorted(bindings)))
    unresolved = [name for name in VARIABLES if name not in bindings]
    if unresolved:
        print("Unresolved coefficient bindings: {}".format(unresolved))
        print(
            "Available coefficient candidates: {}".format(
                [
                    item.get("aps_varname") or item.get("display_name")
                    for item in coefficient_candidates
                ]
            )
        )
    print("Populated surface series: {}".format(len(populated)))
    for row in populated:
        surface = row["surface"]
        print(
            "{} | {} | mean={} | ISO target={}".format(
                surface.get("surface_type"),
                row["variable"],
                row["observed"]["mean"],
                row["iso_target_w_m2k"],
            )
        )
    for check in combined_checks:
        print(
            "{} | {} combined | mean={} | ISO total={}".format(
                check["surface_type"],
                check["boundary"],
                check["observed_total_w_m2k"],
                check["iso_total_w_m2k"],
            )
        )
    print("Report: {}".format(output))
    print("No VE model, construction, weather, option or APS data was changed.")
    return payload


if __name__ == "__main__":
    run()
