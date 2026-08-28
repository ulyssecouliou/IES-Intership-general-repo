"""Reversible ApacheSim diagnostic of Test 1 south-surface irradiation.

The ISO climate workbook supplies surface irradiance directly, whereas EPW
supplies horizontal/direct/diffuse components.  This run enables the detailed
external-solar output, reads the façade carrying the two windows, and restores
all changed ApacheSim options.  It does not register compliance evidence.
"""

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import iesve


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

ISO_SOUTH_MONTHLY_KWH_M2 = (
    159.9,
    132.7,
    151.4,
    114.4,
    97.1,
    82.8,
    91.9,
    109.0,
    138.6,
    165.6,
    146.6,
    157.2,
)
ISO_SOUTH_ANNUAL_KWH_M2 = 1547.1
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _wait_for_aps(path, timeout=30.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_file() and path.stat().st_size > 0:
            return
        time.sleep(0.1)
    raise RuntimeError("Detailed-solar APS was not created: {}".format(path))


def _monthly_irradiation(values_w_m2, results_per_hour):
    values_per_day = int(round(24.0 * results_per_hour))
    cursor = 0
    monthly = []
    for days in MONTH_DAYS:
        count = days * values_per_day
        monthly.append(
            sum(values_w_m2[cursor : cursor + count])
            / results_per_hour
            / 1000.0
        )
        cursor += count
    return monthly


def _room_id(item):
    if isinstance(item, dict):
        return item.get("id") or item.get("room_id")
    if isinstance(item, (list, tuple)) and len(item) >= 2:
        return item[1]
    return None


def run():
    from swiss_sia.reference_model.sia4010.aps_probe import build_surface_inventory
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.simulation_results import (
        convert_aps_series_to_metric,
        get_available_variables,
        get_results_per_hour,
        open_results_reader,
        read_surface_result,
    )

    project = iesve.VEProject.get_current_project()
    project_root = Path(str(project.path)).resolve()
    scenario = ModelScenario.load(project_root / "sia_model_scenario.json")
    if scenario.variant != "test_1":
        raise RuntimeError("Surface-solar diagnostic requires a Test 1 project")

    inventory = build_surface_inventory(project)
    façade_candidates = [
        item
        for item in inventory
        if int(item.get("opening_count") or 0) >= 2
        and item.get("aps_handle") is not None
    ]
    if len(façade_candidates) != 1:
        raise RuntimeError(
            "Expected one façade carrying the two Test 1 windows; found {}. "
            "Run the read-only APS probe to inspect surface identities."
            .format(len(façade_candidates))
        )
    façade = façade_candidates[0]

    simulator = iesve.ApacheSim()
    original = dict(simulator.get_options())
    names = (
        "start_day",
        "start_month",
        "end_day",
        "end_month",
        "reporting_interval",
        "results_filename",
        "detailed_rooms",
        "detailed_external_solar",
    )
    missing = [name for name in names if name not in original]
    if missing:
        raise RuntimeError(
            "ApacheSim options required for safe restoration are missing: {}"
            .format(missing)
        )
    restore = {name: original[name] for name in names}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    aps_name = "SIA4010_test_1_{}_SURFACE_SOLAR_{}.aps".format(
        scenario.case_id, stamp
    )
    aps_path = project_root / "Vista" / aps_name
    applied = {
        "start_day": 1,
        "start_month": 1,
        "end_day": 31,
        "end_month": 12,
        "reporting_interval": 3,
        "results_filename": aps_name,
        # Detailed surface outputs are emitted only for rooms explicitly
        # listed here.  An empty list silently produced a valid APS without
        # the requested surface series in the first two runtime attempts.
        "detailed_rooms": [façade["room_id"]],
        "detailed_external_solar": True,
    }
    restored = False
    payload = None
    try:
        if simulator.set_options(applied) is not True:
            raise RuntimeError("ApacheSim rejected the detailed-solar options")
        readback = dict(simulator.get_options())
        mismatches = {
            key: {"expected": value, "actual": readback.get(key)}
            for key, value in applied.items()
            if readback.get(key) != value
        }
        if mismatches:
            raise RuntimeError(
                "Detailed-solar option read-back mismatch: {}".format(mismatches)
            )
        if simulator.run_simulation(queue_to_tasks=False) is not True:
            status_path = project_root / "apache" / "status.json"
            detail = (
                status_path.read_text(encoding="utf-8")
                if status_path.is_file()
                else ""
            )
            raise RuntimeError("Detailed-solar ApacheSim failed: {}".format(detail))
        _wait_for_aps(aps_path)
        results = open_results_reader(aps_name)
        room_ids = [
            value
            for value in (_room_id(item) for item in list(results.get_room_list() or []))
            if value is not None
        ]
        if len(room_ids) != 1:
            raise RuntimeError("Expected one APS room; found {}".format(len(room_ids)))

        variable = None
        for item in get_available_variables(results):
            if (
                str(item.get("aps_varname") or "").strip().lower()
                == "ext surface incident solar flux"
                and str(item.get("model_level") or "").strip().lower() == "s"
                and "flux" in str(item.get("display_name") or "").lower()
            ):
                variable = item
                break
        if variable is None:
            raise RuntimeError(
                "APS variable 'Ext surface incident solar flux' was not exposed"
            )
        aps_var = str(variable.get("aps_varname"))
        display = str(variable.get("display_name") or aps_var)
        # ResultsReader's surface overload is keyed by the VE body identity,
        # not necessarily by the normalized id returned by get_room_list().
        # They happened to match in the original binding probe but differ in
        # generated gbXML projects, so try both explicit identities and record
        # which one resolves.
        raw = []
        resolved_room_id = None
        attempted_room_ids = []
        for candidate_room_id in (façade.get("room_id"), room_ids[0]):
            if candidate_room_id is None or candidate_room_id in attempted_room_ids:
                continue
            attempted_room_ids.append(candidate_room_id)
            raw = read_surface_result(
                results,
                candidate_room_id,
                façade["aps_handle"],
                aps_var,
                display,
            )
            if raw:
                resolved_room_id = candidate_room_id
                break
        if not raw:
            raise RuntimeError(
                "The south facade returned no external incident-solar series; "
                "attempted room ids {} with surface handle {}"
                .format(attempted_room_ids, façade["aps_handle"])
            )
        aps_tuple = (
            aps_var,
            display,
            "s",
            str(variable.get("resolved_metric_unit") or ""),
            float(variable.get("resolved_metric_divisor") or 1.0),
            float(variable.get("resolved_metric_offset") or 0.0),
        )
        values = convert_aps_series_to_metric(raw, aps_tuple)
        results_per_hour = get_results_per_hour(results)
        expected_count = int(round(8760 * results_per_hour))
        if len(values) != expected_count:
            raise RuntimeError(
                "Surface solar series has {} values; expected {}".format(
                    len(values), expected_count
                )
            )
        observed_monthly = _monthly_irradiation(values, results_per_hour)
        observed_annual = sum(observed_monthly)
        relative = (
            observed_annual - ISO_SOUTH_ANNUAL_KWH_M2
        ) / ISO_SOUTH_ANNUAL_KWH_M2
        payload = {
            "schema_version": "1.0",
            "status": (
                "SURFACE_IRRADIATION_WITHIN_2_PERCENT"
                if abs(relative) <= 0.02
                else "SURFACE_IRRADIATION_MISMATCH_IDENTIFIED"
            ),
            "case": "{}/{}".format(scenario.variant, scenario.case_id),
            "surface": façade,
            "resolved_results_room_id": resolved_room_id,
            "variable": {
                "aps_varname": aps_var,
                "display_name": display,
                "metric_unit": aps_tuple[3],
            },
            "iso": {
                "source": "BS EN ISO 52016-1:2017 Table 26",
                "south_monthly_kwh_m2": ISO_SOUTH_MONTHLY_KWH_M2,
                "south_annual_kwh_m2": ISO_SOUTH_ANNUAL_KWH_M2,
                "rounded_monthly_sum_kwh_m2": sum(ISO_SOUTH_MONTHLY_KWH_M2),
            },
            "ve": {
                "south_monthly_kwh_m2": observed_monthly,
                "south_annual_kwh_m2": observed_annual,
                "value_count": len(values),
                "results_per_hour": results_per_hour,
            },
            "comparison": {
                "difference_kwh_m2": observed_annual - ISO_SOUTH_ANNUAL_KWH_M2,
                "relative_difference": relative,
                "monthly": [
                    {
                        "month": index,
                        "iso_kwh_m2": expected,
                        "ve_kwh_m2": observed,
                        "difference_kwh_m2": observed - expected,
                        "relative_difference": (observed - expected) / expected,
                    }
                    for index, (expected, observed) in enumerate(
                        zip(ISO_SOUTH_MONTHLY_KWH_M2, observed_monthly), start=1
                    )
                ],
            },
            "aps": {"path": str(aps_path), "sha256": _sha256(aps_path)},
            "options": {"before": restore, "applied": applied},
            "purpose": (
                "Separate EPW/VE sky-model surface transport from glazing "
                "optical treatment. No compliance evidence is registered."
            ),
            "compliance_claim_allowed": False,
        }
    finally:
        restored = simulator.set_options(restore) is True
        if restored:
            current = dict(simulator.get_options())
            restored = all(current.get(key) == value for key, value in restore.items())
    if not restored:
        raise RuntimeError("Original ApacheSim options were not restored")

    payload["restoration"] = {"apache_options_restored": True}
    output_dir = project_root / "sia4010_artifacts" / "diagnostics"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / (
        "SIA4010_test_1_{}_surface_solar_diagnostic.json".format(
            scenario.case_id
        )
    )
    temporary = output_path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output_path)

    print("SIA 4010 TEST 1 SURFACE-SOLAR DIAGNOSTIC: {}".format(payload["status"]))
    print("Case: {}".format(payload["case"]))
    print("ISO south surface: {:.3f} kWh/m2".format(ISO_SOUTH_ANNUAL_KWH_M2))
    print("VE south surface: {:.3f} kWh/m2".format(observed_annual))
    print("Relative difference: {:+.2%}".format(relative))
    print("Diagnostic APS: {}".format(aps_path))
    print("Audit: {}".format(output_path))
    print("Original ApacheSim options were restored.")
    print("No compliance evidence was registered.")
    return payload


if __name__ == "__main__":
    run()
