"""Controlled Test 1 weather A/B run using VE's native Denver TMY transport."""

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import iesve


REPOSITORY_ROOT = Path(__file__).resolve().parent
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

NATIVE_REFERENCE = "DenverStapletonTMY.fwt"


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


def _room_id(room):
    if isinstance(room, dict):
        return room.get("id") or room.get("room_id")
    if isinstance(room, (list, tuple)) and len(room) >= 2:
        return room[1]
    return None


def _wait_for_aps(path, timeout=15.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_file() and path.stat().st_size > 0:
            return
        time.sleep(0.1)
    raise RuntimeError("Diagnostic APS was not created: {}".format(path))


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


def run():
    """Run a reversible diagnostic without registering compliance evidence."""

    from swiss_sia.reference_model.sia4010.active_case_evaluation import (
        evaluate_qualified_active_case,
    )
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.ve_api import IesVeGateway
    from swiss_sia.simulation_results import open_results_reader

    project = iesve.VEProject.get_current_project()
    project_root = Path(str(project.path)).resolve()
    scenario = ModelScenario.load(project_root / "sia_model_scenario.json")
    if (scenario.variant, scenario.case_id) != ("test_1", "600"):
        raise RuntimeError(
            "Weather A/B is currently guarded for test_1/600 only; active is {}/{}"
            .format(scenario.variant, scenario.case_id)
        )
    original_weather = _current_weather_reference()
    gateway = IesVeGateway(iesve_module=iesve)
    simulator = iesve.ApacheSim()
    original_options = dict(simulator.get_options())
    writable_option_names = (
        "start_day",
        "start_month",
        "end_day",
        "end_month",
        "reporting_interval",
        "results_filename",
    )
    restore_options = {
        name: original_options[name]
        for name in writable_option_names
        if name in original_options
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    aps_name = "SIA4010_test_1_600_WEATHER_AB_FWT_{}.aps".format(stamp)
    aps_path = project_root / "Vista" / aps_name
    evaluation_path = (
        project_root
        / "sia4010_artifacts"
        / "diagnostics"
        / "SIA4010_test_1_600_weather_ab_fwt_evaluation.json"
    )
    audit_path = (
        project_root
        / "sia4010_artifacts"
        / "diagnostics"
        / "SIA4010_test_1_600_weather_ab_fwt.json"
    )
    restored_weather = None
    restored_options = False
    try:
        gateway.assign_weather(NATIVE_REFERENCE)
        assigned_candidate = _current_weather_reference()
        options = {
            "start_day": 1,
            "start_month": 1,
            "end_day": 31,
            "end_month": 12,
            "reporting_interval": 3,
            "results_filename": aps_name,
        }
        if simulator.set_options(options) is not True:
            raise RuntimeError("ApacheSim.set_options() failed for A/B run")
        if simulator.run_simulation(queue_to_tasks=False) is not True:
            status_path = project_root / "apache" / "status.json"
            detail = status_path.read_text(encoding="utf-8") if status_path.is_file() else ""
            raise RuntimeError("ApacheSim A/B run failed: {}".format(detail))
        _wait_for_aps(aps_path)
        results = open_results_reader(aps_name)
        rooms = list(results.get_room_list() or [])
        room_ids = [identifier for identifier in (_room_id(item) for item in rooms) if identifier is not None]
        if len(room_ids) != 1:
            raise RuntimeError("Expected one APS room, found {}".format(len(room_ids)))
        receipt = evaluate_qualified_active_case(
            variant="test_1",
            case_id="600",
            results_file=results,
            room_id=room_ids[0],
            aps_path=aps_path,
            bundle_root=REPOSITORY_ROOT / "SIA_4010_geteilter_Link",
            bindings_path=REPOSITORY_ROOT / "config" / "sia4010_aps_bindings_ve_runtime.json",
            output_path=evaluation_path,
        )
        evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
        comparisons = evaluation["evaluation"]["comparisons"]
        key_metrics = {
            "annual_heating": _key_metric(comparisons, "heating", "Annual"),
            "annual_cooling": _key_metric(comparisons, "cooling", "Annual"),
            "peak_heating": _key_metric(comparisons, "peak heating", "Heating"),
            "peak_cooling": _key_metric(comparisons, "peak heating", "Cooling"),
        }
        payload = {
            "schema_version": "1.0",
            "status": "DIAGNOSTIC_RESULTS_RECORDED",
            "case": "test_1/600",
            "original_weather": original_weather,
            "diagnostic_weather": assigned_candidate,
            "aps": {
                "path": str(aps_path),
                "sha256": _sha256(aps_path),
            },
            "evaluation": str(evaluation_path),
            "evaluation_status": receipt.status,
            "observed_metric_count": receipt.observed_metric_count,
            "key_metrics": key_metrics,
            "purpose": (
                "A/B diagnosis only. DenverStapletonTMY.fwt has not yet been "
                "established as the normative transport of the supplied DRYCOLD.TMY."
            ),
            "compliance_claim_allowed": False,
        }
    finally:
        try:
            restored_options = simulator.set_options(restore_options) is True
        finally:
            gateway.assign_weather(original_weather)
            restored_weather = _current_weather_reference()
    payload["restoration"] = {
        "weather_reference": restored_weather,
        "weather_matches_original": restored_weather == original_weather,
        "apache_options_restored": restored_options,
    }
    if not payload["restoration"]["weather_matches_original"]:
        raise RuntimeError("Original weather reference was not restored")
    if not restored_options:
        raise RuntimeError("Original writable ApacheSim options were not restored")
    _write_json(audit_path, payload)
    print("SIA 4010 TEST 1 WEATHER A/B: {}".format(payload["status"]))
    for name, metric in payload["key_metrics"].items():
        print("{}: {}".format(name, metric))
    print("Diagnostic APS: {}".format(aps_path))
    print("Evaluation: {}".format(evaluation_path))
    print("Audit: {}".format(audit_path))
    print("Restored weather: {}".format(restored_weather))
    print("No compliance evidence was registered.")
    return payload


if __name__ == "__main__":
    run()
