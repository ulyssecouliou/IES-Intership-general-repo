"""Reversible Test 1 A/B using ISO surface-derived EPW solar components."""

import csv
import hashlib
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import iesve


ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

COMPONENTS = ROOT / "refs" / "reference-data" / "iso52016_epw_solar_components.csv"
COMPONENT_AUDIT = ROOT / "refs" / "reference-data" / "iso52016_epw_solar_components.audit.json"
ISO_SOUTH_KWH_M2 = 1547.1
ISO_SKY_AIR_DELTA_K = 11.0
STEFAN_BOLTZMANN_W_M2K4 = 5.6697e-8


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


def _remove_with_retry(path, timeout=2.0):
    """Remove a worker input after ApacheSim releases its transient file lock."""

    deadline = time.monotonic() + timeout
    while path.exists():
        try:
            path.unlink()
            return True
        except (PermissionError, OSError):
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.25)
    return True


def _room_id(item):
    if isinstance(item, dict):
        return item.get("id") or item.get("room_id")
    if isinstance(item, (list, tuple)) and len(item) >= 2:
        return item[1]
    return None


def _current_weather_reference():
    locate = iesve.VELocate()
    try:
        if locate.open_wea_data() < 0:
            raise RuntimeError("VELocate.open_wea_data() failed")
        reference = str(locate.get().get("weather_file", ""))
        locate.close_wea_data()
        return reference
    except Exception:
        try:
            locate.close_wea_data()
        except Exception:
            pass
        raise


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


def _build_candidate(base_epw, candidate_epw):
    component_audit = json.loads(COMPONENT_AUDIT.read_text(encoding="utf-8"))
    expected_hash = str(component_audit["output"]["sha256"]).upper()
    if _sha256(COMPONENTS) != expected_hash:
        raise RuntimeError("ISO component CSV checksum does not match its audit")
    with COMPONENTS.open("r", newline="", encoding="utf-8") as handle:
        components = list(csv.DictReader(handle))
    lines = base_epw.read_text(encoding="ascii").splitlines()
    if len(lines) < 8 or len(lines[8:]) != 8760 or len(components) != 8760:
        raise RuntimeError("Base EPW/component row count is not 8760")
    header = list(lines[:8])
    header[5] = "COMMENTS 1,ISO 52016 surface-derived EPW transport candidate"
    header[6] = (
        "COMMENTS 2,GHI from ISO H; DNI/DHI reconstructed and monthly-normalized; "
        "see project derivation audit"
    )
    output = []
    sky_air_delta_values = []
    for line, component in zip(lines[8:], components):
        fields = line.split(",")
        if len(fields) < 35:
            raise RuntimeError("Malformed base EPW data row")
        if (
            int(fields[1]) != int(component["month"])
            or int(fields[2]) != int(component["day"])
            or int(fields[3]) != int(component["hour_ending"])
        ):
            raise RuntimeError("EPW/component timestamp mismatch")
        dry_bulb_k = float(fields[6]) + 273.15
        horizontal_ir = float(fields[12])
        if horizontal_ir <= 0.0 or horizontal_ir == 9999.0:
            raise RuntimeError("Base EPW horizontal infrared value is unavailable")
        sky_temperature_k = (
            horizontal_ir / STEFAN_BOLTZMANN_W_M2K4
        ) ** 0.25
        sky_air_delta_values.append(dry_bulb_k - sky_temperature_k)
        fields[13] = str(int(round(float(component["ghi_w_m2"]))))
        fields[14] = str(int(round(float(component["dni_w_m2"]))))
        fields[15] = str(int(round(float(component["dhi_w_m2"]))))
        output.append(",".join(fields))
    temporary = candidate_epw.with_suffix(candidate_epw.suffix + ".tmp")
    temporary.write_text("\n".join(header + output) + "\n", encoding="ascii")
    temporary.replace(candidate_epw)
    return {
        "base_epw": {"path": str(base_epw), "sha256": _sha256(base_epw)},
        "components": {"path": str(COMPONENTS), "sha256": _sha256(COMPONENTS)},
        "component_audit": {"path": str(COMPONENT_AUDIT), "sha256": _sha256(COMPONENT_AUDIT)},
        "candidate_epw": {"path": str(candidate_epw), "sha256": _sha256(candidate_epw)},
        "records": len(output),
        "sky_temperature_transport": {
            "prescribed_delta_t_sky_air_k": ISO_SKY_AIR_DELTA_K,
            "horizontal_ir_formula": "T_sky_K = (horizontal_IR / sigma)^0.25",
            "stefan_boltzmann_w_m2k4": STEFAN_BOLTZMANN_W_M2K4,
            "observed_delta_t_sky_air_mean_k": (
                sum(sky_air_delta_values) / len(sky_air_delta_values)
            ),
            "observed_delta_t_sky_air_min_k": min(sky_air_delta_values),
            "observed_delta_t_sky_air_max_k": max(sky_air_delta_values),
            "maximum_absolute_difference_from_prescribed_k": max(
                abs(value - ISO_SKY_AIR_DELTA_K)
                for value in sky_air_delta_values
            ),
            "base_epw_already_matches_prescribed_condition": max(
                abs(value - ISO_SKY_AIR_DELTA_K)
                for value in sky_air_delta_values
            ) <= 0.02,
            "source": "BS EN ISO 52016-1:2017 clause 7.2.2.12",
        },
    }


def _resolve_apache_weather_folders(base_weather_name):
    """Find all VE weather folders that supply the active base EPW."""

    getter = getattr(iesve, "get_weather_file_paths", None)
    if not callable(getter):
        raise RuntimeError("IESVE does not expose get_weather_file_paths()")
    matches = []
    for value in getter() or []:
        folder = Path(str(value))
        if (folder / base_weather_name).is_file():
            matches.append(folder.resolve())
    unique = []
    for folder in matches:
        if folder not in unique:
            unique.append(folder)
    if not unique:
        raise RuntimeError(
            "No Apache weather folder contains {!r}; VE reported: {}"
            .format(base_weather_name, [str(item) for item in unique])
        )
    return unique


def run():
    from swiss_sia.reference_model.sia4010.active_case_evaluation import (
        evaluate_qualified_active_case,
    )
    from swiss_sia.reference_model.sia4010.aps_probe import build_surface_inventory
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.ve_api import IesVeGateway
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
    if (scenario.variant, scenario.case_id) != ("test_1", "640"):
        raise RuntimeError(
            "ISO weather A/B is guarded for test_1/640; active is {}/{}"
            .format(scenario.variant, scenario.case_id)
        )
    base_epw = project_root / "DRYCOLD_IESVE.epw"
    if not base_epw.is_file():
        raise RuntimeError("Base project EPW is missing: {}".format(base_epw))
    candidate_epw = project_root / "DRYCOLD_IESVE_ISO_SURFACE_DERIVED.epw"
    derivation = _build_candidate(base_epw, candidate_epw)
    reader = iesve.WeatherFileReader()
    try:
        if int(reader.open_weather_file(str(candidate_epw))) <= 0:
            raise RuntimeError("IESVE rejected the ISO surface-derived EPW")
        num_days = 366 if int(reader.feb29) else 365
        if len(reader.get_results(3, 1, num_days)) != 8760:
            raise RuntimeError("IESVE did not read 8760 candidate weather records")
    finally:
        try:
            reader.close()
        except Exception:
            pass

    inventory = build_surface_inventory(project)
    facade_rows = [
        item for item in inventory
        if int(item.get("opening_count") or 0) >= 2
        and item.get("aps_handle") is not None
    ]
    if len(facade_rows) != 1:
        raise RuntimeError("Expected one two-window facade; found {}".format(len(facade_rows)))
    facade = facade_rows[0]
    gateway = IesVeGateway(iesve_module=iesve)
    original_weather = _current_weather_reference()
    simulator = iesve.ApacheSim()
    original_options = dict(simulator.get_options())
    option_names = (
        "start_day", "start_month", "end_day", "end_month",
        "reporting_interval", "results_filename", "detailed_rooms",
        "detailed_external_solar",
    )
    missing = [name for name in option_names if name not in original_options]
    if missing:
        raise RuntimeError("Required ApacheSim options are missing: {}".format(missing))
    restore_options = {name: original_options[name] for name in option_names}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    aps_name = "SIA4010_test_1_640_ISO_WEATHER_AB_{}.aps".format(stamp)
    aps_path = project_root / "Vista" / aps_name
    apache_weather_folders = _resolve_apache_weather_folders(base_epw.name)
    installed_candidate_name = "DRYCOLD_IESVE_ISO_SURFACE_DERIVED_AB.epw"
    installed_candidates = [
        folder / installed_candidate_name for folder in apache_weather_folders
    ]
    diagnostics = project_root / "sia4010_artifacts" / "diagnostics"
    evaluation_path = diagnostics / "SIA4010_test_1_640_iso_weather_ab_evaluation.json"
    audit_path = diagnostics / "SIA4010_test_1_640_iso_weather_ab.json"
    applied_options = {
        "start_day": 1,
        "start_month": 1,
        "end_day": 31,
        "end_month": 12,
        "reporting_interval": 3,
        "results_filename": aps_name,
        "detailed_rooms": [facade["room_id"]],
        "detailed_external_solar": True,
    }
    payload = None
    options_restored = False
    weather_restored = False
    installed_candidates_removed = False
    pending_cleanup = []
    try:
        candidate_digest = _sha256(candidate_epw)
        for installed_candidate in installed_candidates:
            if installed_candidate.exists():
                if _sha256(installed_candidate) != candidate_digest:
                    raise RuntimeError(
                        "Refusing to overwrite a different Apache weather candidate: {}"
                        .format(installed_candidate)
                    )
            else:
                shutil.copy2(candidate_epw, installed_candidate)
            if _sha256(installed_candidate) != candidate_digest:
                raise RuntimeError(
                    "Temporary Apache weather copy checksum mismatch: {}"
                    .format(installed_candidate)
                )
        gateway.assign_weather(str(installed_candidates[0]))
        assigned_candidate = _current_weather_reference()
        if Path(assigned_candidate).name.lower() != installed_candidate_name.lower():
            raise RuntimeError(
                "Candidate weather assignment did not persist: expected={!r}, "
                "read_back={!r}".format(installed_candidate_name, assigned_candidate)
            )
        if simulator.set_options(applied_options) is not True:
            raise RuntimeError("ApacheSim rejected ISO weather A/B options")
        if simulator.run_simulation(queue_to_tasks=False) is not True:
            status_path = project_root / "apache" / "status.json"
            detail = status_path.read_text(encoding="utf-8") if status_path.is_file() else ""
            raise RuntimeError("ISO weather A/B simulation failed: {}".format(detail))
        _wait_for_aps(aps_path)
        results = open_results_reader(aps_name)
        aps_rooms = list(results.get_room_list() or [])
        room_ids = [value for value in (_room_id(item) for item in aps_rooms) if value is not None]
        if len(room_ids) != 1:
            raise RuntimeError("Expected one APS room; found {}".format(len(room_ids)))
        receipt = evaluate_qualified_active_case(
            variant="test_1",
            case_id="640",
            results_file=results,
            room_id=room_ids[0],
            aps_path=aps_path,
            bundle_root=ROOT / "SIA_4010_geteilter_Link",
            bindings_path=ROOT / "config" / "sia4010_aps_bindings_ve_runtime.json",
            output_path=evaluation_path,
        )
        evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
        comparisons = evaluation["evaluation"]["comparisons"]

        solar_variable = None
        for item in get_available_variables(results):
            if (
                str(item.get("aps_varname") or "").lower()
                == "ext surface incident solar flux"
                and str(item.get("model_level") or "").lower() == "s"
                and "flux" in str(item.get("display_name") or "").lower()
            ):
                solar_variable = item
                break
        if solar_variable is None:
            raise RuntimeError("Detailed surface-solar APS variable is missing")
        aps_var = str(solar_variable["aps_varname"])
        display = str(solar_variable.get("display_name") or aps_var)
        raw_solar = read_surface_result(
            results, facade["room_id"], facade["aps_handle"], aps_var, display
        )
        if not raw_solar:
            raise RuntimeError("Candidate APS returned no south-surface solar series")
        solar_tuple = (
            aps_var, display, "s",
            str(solar_variable.get("resolved_metric_unit") or ""),
            float(solar_variable.get("resolved_metric_divisor") or 1.0),
            float(solar_variable.get("resolved_metric_offset") or 0.0),
        )
        solar_values = convert_aps_series_to_metric(raw_solar, solar_tuple)
        results_per_hour = get_results_per_hour(results)
        south_kwh_m2 = sum(solar_values) / results_per_hour / 1000.0
        payload = {
            "schema_version": "1.0",
            "status": "DIAGNOSTIC_RESULTS_RECORDED",
            "case": "test_1/640",
            "derivation": derivation,
            "weather": {
                "original": original_weather,
                "candidate": candidate_epw.name,
                "temporary_apache_copies": [
                    str(path) for path in installed_candidates
                ],
                "assigned_readback": assigned_candidate,
            },
            "surface_solar": {
                "iso_south_kwh_m2": ISO_SOUTH_KWH_M2,
                "ve_south_kwh_m2": south_kwh_m2,
                "difference_kwh_m2": south_kwh_m2 - ISO_SOUTH_KWH_M2,
                "relative_difference": (south_kwh_m2 - ISO_SOUTH_KWH_M2) / ISO_SOUTH_KWH_M2,
            },
            "thermal_key_metrics": {
                "annual_heating": _key_metric(comparisons, "heating", "Annual"),
                "annual_cooling": _key_metric(comparisons, "cooling", "Annual"),
                "peak_heating": _key_metric(comparisons, "peak heating", "Heating"),
                "peak_cooling": _key_metric(comparisons, "peak heating", "Cooling"),
            },
            "aps": {"path": str(aps_path), "sha256": _sha256(aps_path)},
            "evaluation": str(evaluation_path),
            "evaluation_status": receipt.status,
            "observed_metric_count": receipt.observed_metric_count,
            "purpose": "Source-derived weather transport A/B; no thermal-result calibration.",
            "compliance_claim_allowed": False,
        }
    finally:
        try:
            options_restored = simulator.set_options(restore_options) is True
        finally:
            try:
                gateway.assign_weather(original_weather)
                weather_restored = _current_weather_reference() == original_weather
            finally:
                for installed_candidate in installed_candidates:
                    _remove_with_retry(installed_candidate)
                installed_candidates_removed = all(
                    not path.exists() for path in installed_candidates
                )
                pending_cleanup = [
                    str(path) for path in installed_candidates if path.exists()
                ]
    if not options_restored or not weather_restored:
        raise RuntimeError(
            "A/B restoration failed: options={}, weather={}"
            .format(
                options_restored,
                weather_restored,
            )
        )
    if pending_cleanup:
        payload["status"] = "DIAGNOSTIC_RESULTS_RECORDED_CLEANUP_DEFERRED"
    payload["restoration"] = {
        "apache_options_restored": True,
        "weather_restored": True,
        "temporary_apache_weather_removed": installed_candidates_removed,
        "pending_cleanup_after_ve_closes": pending_cleanup,
    }
    _write_json(audit_path, payload)
    print("SIA 4010 TEST 1 ISO WEATHER TRANSPORT A/B: {}".format(payload["status"]))
    print("Case: test_1/640")
    print(
        "South surface: ISO={:.3f}, VE={:.3f} kWh/m2 ({:+.2%})".format(
            ISO_SOUTH_KWH_M2,
            payload["surface_solar"]["ve_south_kwh_m2"],
            payload["surface_solar"]["relative_difference"],
        )
    )
    for name, metric in payload["thermal_key_metrics"].items():
        print("{}: {}".format(name, metric))
    print("Candidate EPW: {}".format(candidate_epw))
    print("Diagnostic APS: {}".format(aps_path))
    print("Audit: {}".format(audit_path))
    print("Original weather and ApacheSim options were restored.")
    print("No compliance evidence was registered.")
    return payload


if __name__ == "__main__":
    run()
