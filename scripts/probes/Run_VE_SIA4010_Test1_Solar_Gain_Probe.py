"""Read-only Test 1 solar transport diagnostic for the active Case 640 APS."""

import json
import os
import sys
from datetime import datetime


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

SOUTH_IRRADIATION_KWH_M2 = (
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
SOUTH_ANNUAL_IRRADIATION_KWH_M2 = 1547.1
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
WINDOW_AREA_M2 = 12.0
SOLAR_ENERGY_TRANSMITTANCE = 0.71


def _room_identity(item):
    if isinstance(item, dict):
        return item.get("id") or item.get("room_id"), str(
            item.get("name") or item.get("room_name") or ""
        )
    if isinstance(item, (list, tuple)):
        return (item[1] if len(item) > 1 else None), str(item[0] if item else "")
    return None, str(item)


def _monthly_energy_kwh(power_kw, results_per_hour):
    values_per_day = int(round(24.0 * results_per_hour))
    rows = []
    cursor = 0
    for days in MONTH_DAYS:
        count = days * values_per_day
        rows.append(sum(power_kw[cursor : cursor + count]) / results_per_hour)
        cursor += count
    return rows


def run():
    import iesve

    from swiss_sia.simulation_results import (
        convert_aps_series_to_metric,
        get_available_variables,
        get_results_per_hour,
        open_results_reader,
        read_room_result,
    )

    project = iesve.VEProject.get_current_project()
    project_path = str(project.path)
    audit_path = os.path.join(
        project_path,
        "sia4010_artifacts",
        "simulation",
        "SIA4010_test_1_640_apachesim_qualification.json",
    )
    if not os.path.isfile(audit_path):
        raise RuntimeError("Qualified Case 640 ApacheSim audit not found: {}".format(audit_path))
    with open(audit_path, "r", encoding="utf-8") as handle:
        audit = json.load(handle)
    aps_path = str(audit.get("results_path") or "")
    if not os.path.isfile(aps_path):
        raise RuntimeError("Qualified Case 640 APS not found: {}".format(aps_path))

    results = open_results_reader(os.path.basename(aps_path))
    results_per_hour = get_results_per_hour(results)
    rooms = list(results.get_room_list() or [])
    if len(rooms) != 1:
        raise RuntimeError("Expected one APS room; found {}".format(len(rooms)))
    room_id, room_name = _room_identity(rooms[0])

    variable = None
    for item in get_available_variables(results):
        if (
            str(item.get("aps_varname") or item.get("name") or "").strip().lower()
            == "window solar gains"
            and str(item.get("model_level") or item.get("level") or "z").lower()
            in ("", "z")
        ):
            variable = item
            break
    if variable is None:
        raise RuntimeError("Qualified APS variable 'Window solar gains' was not found")
    aps_name = str(variable.get("aps_varname") or variable.get("name"))
    display = str(variable.get("display_name") or aps_name)
    level = str(variable.get("model_level") or variable.get("level") or "z")
    aps_tuple = (
        aps_name,
        display,
        level,
        str(variable.get("resolved_metric_unit") or ""),
        float(variable.get("resolved_metric_divisor") or 1.0),
        float(variable.get("resolved_metric_offset") or 0.0),
    )
    raw = read_room_result(results, room_id, aps_name, display, level)
    power_kw = convert_aps_series_to_metric(raw, aps_tuple)
    expected_count = int(round(8760 * results_per_hour))
    if len(power_kw) != expected_count:
        raise RuntimeError(
            "Window solar gain series has {} values; expected {}".format(
                len(power_kw), expected_count
            )
        )

    observed_monthly = _monthly_energy_kwh(power_kw, results_per_hour)
    expected_monthly = [
        value * WINDOW_AREA_M2 * SOLAR_ENERGY_TRANSMITTANCE
        for value in SOUTH_IRRADIATION_KWH_M2
    ]
    observed_annual = sum(observed_monthly)
    # The published annual value is authoritative.  The rounded monthly
    # entries add to 1547.2 kWh/m2, a 0.1 kWh/m2 table-rounding artefact.
    expected_annual = (
        SOUTH_ANNUAL_IRRADIATION_KWH_M2
        * WINDOW_AREA_M2
        * SOLAR_ENERGY_TRANSMITTANCE
    )
    implied_incident = observed_annual / (
        WINDOW_AREA_M2 * SOLAR_ENERGY_TRANSMITTANCE
    )
    deviation = observed_annual - expected_annual
    relative = deviation / expected_annual
    monthly = []
    for month, (incident, expected, observed) in enumerate(
        zip(SOUTH_IRRADIATION_KWH_M2, expected_monthly, observed_monthly), start=1
    ):
        monthly.append(
            {
                "month": month,
                "iso_south_incident_kwh_m2": incident,
                "iso_constant_g_window_gain_kwh": expected,
                "ve_window_solar_gain_kwh": observed,
                "difference_kwh": observed - expected,
                "relative_difference": (observed - expected) / expected,
            }
        )

    if abs(relative) <= 0.02:
        status = "SOLAR_GAIN_WITHIN_2_PERCENT_DIAGNOSTIC"
    else:
        status = "SOLAR_TRANSPORT_MISMATCH_IDENTIFIED"
    report = {
        "schema_version": "1.0",
        "status": status,
        "project": {"name": str(project.name), "path": project_path},
        "case": "test_1/640",
        "aps": {
            "path": aps_path,
            "room_id": room_id,
            "room_name": room_name,
            "variable": {
                "aps_varname": aps_name,
                "display_name": display,
                "metric_unit": aps_tuple[3],
            },
            "results_per_hour": results_per_hour,
            "value_count": len(power_kw),
        },
        "iso_reference": {
            "source": "BS EN ISO 52016-1:2017, Table 26 and Clause 7.2.2.6",
            "south_incident_irradiation_kwh_m2": SOUTH_ANNUAL_IRRADIATION_KWH_M2,
            "rounded_monthly_sum_kwh_m2": sum(SOUTH_IRRADIATION_KWH_M2),
            "window_area_m2": WINDOW_AREA_M2,
            "solar_energy_transmittance": SOLAR_ENERGY_TRANSMITTANCE,
            "constant_g_annual_window_gain_kwh": expected_annual,
        },
        "observed": {
            "annual_window_solar_gain_kwh": observed_annual,
            "implied_south_incident_irradiation_kwh_m2": implied_incident,
        },
        "comparison": {
            "difference_kwh": deviation,
            "relative_difference": relative,
            "monthly": monthly,
        },
        "qualification": (
            "This diagnostic compares the qualified VE Window solar gains APS "
            "series with the ISO surface-irradiation input multiplied by the "
            "prescribed 12 m2 and g=0.71. A mismatch can include both EPW sky "
            "transport and VE incidence-angle glazing treatment; it is not by "
            "itself a compliance verdict."
        ),
        "model_or_aps_changed": False,
    }
    output_dir = os.path.join(project_path, "sia4010_artifacts", "diagnostics")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(
        output_dir,
        "sia4010_test1_solar_gain_probe_{}.json".format(
            datetime.now().strftime("%Y%m%d_%H%M%S")
        ),
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False, default=str)

    print("SIA 4010 TEST 1 SOLAR-GAIN PROBE: {}".format(status))
    print("Case: test_1/640")
    print(
        "ISO south irradiation: {:.3f} kWh/m2".format(
            SOUTH_ANNUAL_IRRADIATION_KWH_M2
        )
    )
    print("ISO constant-g window gain: {:.3f} kWh".format(expected_annual))
    print("VE APS window solar gain: {:.3f} kWh".format(observed_annual))
    print("Implied south irradiation: {:.3f} kWh/m2".format(implied_incident))
    print("Relative difference: {:+.2%}".format(relative))
    print("Report: {}".format(output_path))
    print("No VE model or APS data was changed.")
    return output_path


if __name__ == "__main__":
    run()
