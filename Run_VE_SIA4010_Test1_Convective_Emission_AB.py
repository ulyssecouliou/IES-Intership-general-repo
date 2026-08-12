"""Reversible Test 1 A/B run for fully convective ideal heating and cooling."""

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


def _sequence(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return [value]


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
    """Simulate the corrected emission split, then restore every changed field."""

    from swiss_sia.reference_model.sia4010.active_case_evaluation import (
        evaluate_qualified_active_case,
    )
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.sia4010.test1_runtime_inputs import (
        build_ideal_load_system_payload,
        validate_ideal_load_emission_semantics,
    )
    from swiss_sia.simulation_results import open_results_reader

    project = iesve.VEProject.get_current_project()
    project_root = Path(str(project.path)).resolve()
    scenario = ModelScenario.load(project_root / "sia_model_scenario.json")
    if (scenario.variant, scenario.case_id) != ("test_1", "600"):
        raise RuntimeError(
            "Convective-emission A/B is guarded for test_1/600 only; active is "
            "{}/{}".format(scenario.variant, scenario.case_id)
        )
    expected_room = "SIA4010_TEST_1_600_ZONE"
    bodies = [
        body
        for model in _sequence(project.models)
        for body in _sequence(model.get_bodies(False))
        if str(getattr(body, "name", "")) == expected_room
    ]
    if len(bodies) != 1:
        raise RuntimeError(
            "Expected exactly one room named {!r}; found {}".format(
                expected_room, len(bodies)
            )
        )
    room_data = bodies[0].get_room_data()
    original_system = dict(room_data.get_apache_systems())
    mutation = build_ideal_load_system_payload(original_system)
    rollback = {
        key: original_system[key] for key in mutation if key in original_system
    }
    if len(rollback) != len(mutation):
        missing = sorted(set(mutation) - set(rollback))
        raise RuntimeError(
            "VE cannot safely restore absent system fields: {}".format(missing)
        )

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
    aps_name = "SIA4010_test_1_600_CONVECTIVE_AB_{}.aps".format(stamp)
    aps_path = project_root / "Vista" / aps_name
    diagnostics = project_root / "sia4010_artifacts" / "diagnostics"
    evaluation_path = diagnostics / "SIA4010_test_1_600_convective_ab_evaluation.json"
    audit_path = diagnostics / "SIA4010_test_1_600_convective_ab.json"
    restored_system = False
    restored_options = False
    try:
        room_data.set_apache_systems(mutation)
        applied_system = dict(room_data.get_apache_systems())
        emission = validate_ideal_load_emission_semantics(applied_system)
        options = {
            "start_day": 1,
            "start_month": 1,
            "end_day": 31,
            "end_month": 12,
            "reporting_interval": 3,
            "results_filename": aps_name,
        }
        if simulator.set_options(options) is not True:
            raise RuntimeError("ApacheSim.set_options() failed for emission A/B")
        if simulator.run_simulation(queue_to_tasks=False) is not True:
            status_path = project_root / "apache" / "status.json"
            detail = (
                status_path.read_text(encoding="utf-8")
                if status_path.is_file()
                else ""
            )
            raise RuntimeError("ApacheSim emission A/B run failed: {}".format(detail))
        _wait_for_aps(aps_path)
        results = open_results_reader(aps_name)
        room_ids = [
            identifier
            for identifier in (
                _room_id(item) for item in list(results.get_room_list() or [])
            )
            if identifier is not None
        ]
        if len(room_ids) != 1:
            raise RuntimeError("Expected one APS room, found {}".format(len(room_ids)))
        receipt = evaluate_qualified_active_case(
            variant="test_1",
            case_id="600",
            results_file=results,
            room_id=room_ids[0],
            aps_path=aps_path,
            bundle_root=REPOSITORY_ROOT / "SIA_4010_geteilter_Link",
            bindings_path=(
                REPOSITORY_ROOT
                / "config"
                / "sia4010_aps_bindings_ve_runtime.json"
            ),
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
            "mutation": {
                "before": {
                    key: original_system.get(key)
                    for key in (
                        "heating_plant_radiant_fraction",
                        "cooling_plant_radiant_fraction",
                    )
                },
                "applied": emission,
            },
            "aps": {"path": str(aps_path), "sha256": _sha256(aps_path)},
            "evaluation": str(evaluation_path),
            "evaluation_status": receipt.status,
            "observed_metric_count": receipt.observed_metric_count,
            "key_metrics": key_metrics,
            "purpose": (
                "A/B diagnosis of the normative fully convective ideal-load "
                "mapping. No project save or compliance registration is performed."
            ),
            "compliance_claim_allowed": False,
        }
    finally:
        try:
            restored_options = simulator.set_options(restore_options) is True
        finally:
            room_data.set_apache_systems(rollback)
            after_restore = dict(room_data.get_apache_systems())
            restored_system = all(
                after_restore.get(key) == value for key, value in rollback.items()
            )
    payload["restoration"] = {
        "system_fields_restored": restored_system,
        "apache_options_restored": restored_options,
    }
    if not restored_system or not restored_options:
        raise RuntimeError("Emission A/B restoration did not verify")
    _write_json(audit_path, payload)
    print("SIA 4010 TEST 1 CONVECTIVE EMISSION A/B: {}".format(payload["status"]))
    for name, metric in payload["key_metrics"].items():
        print("{}: {}".format(name, metric))
    print("Diagnostic APS: {}".format(aps_path))
    print("Evaluation: {}".format(evaluation_path))
    print("Audit: {}".format(audit_path))
    print("Original room system fields and Apache options were restored.")
    print("No compliance evidence was registered.")
    return payload


if __name__ == "__main__":
    run()
