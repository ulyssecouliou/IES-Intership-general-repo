"""Reversible SIA 4010 Test 1 run with the ISO 744-hour initialization.

The supplied ISO 52016-1 climate workbook identifies its first 744 hours as
initialization data copied from December.  ApacheSim expresses the equivalent
engine setup as 31 preconditioning days.  This script measures that mapping in
the active Test 1 project, records a diagnostic APS/evaluation, and restores
all ApacheSim options.  It never registers compliance evidence.
"""

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

ISO_INITIALIZATION_HOURS = 744
ISO_PRECONDITIONING_DAYS = ISO_INITIALIZATION_HOURS // 24


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


def _room_id(room):
    if isinstance(room, dict):
        return room.get("id") or room.get("room_id")
    if isinstance(room, (list, tuple)) and len(room) >= 2:
        return room[1]
    return None


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
    """Run and evaluate the 31-day A/B, restoring original Apache options."""

    from swiss_sia.reference_model.sia4010.active_case_evaluation import (
        evaluate_qualified_active_case,
    )
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.simulation_results import open_results_reader

    project = iesve.VEProject.get_current_project()
    project_root = Path(str(project.path)).resolve()
    scenario = ModelScenario.load(project_root / "sia_model_scenario.json")
    if scenario.variant != "test_1":
        raise RuntimeError(
            "Preconditioning A/B requires a Test 1 project; active is {}/{}"
            .format(scenario.variant, scenario.case_id)
        )

    simulator = iesve.ApacheSim()
    original_options = dict(simulator.get_options())
    writable_names = (
        "start_day",
        "start_month",
        "end_day",
        "end_month",
        "reporting_interval",
        "preconditioning_days",
        "results_filename",
    )
    missing = [name for name in writable_names if name not in original_options]
    if missing:
        raise RuntimeError(
            "ApacheSim options required for safe restoration are missing: {}"
            .format(missing)
        )
    restore_options = {
        name: original_options[name] for name in writable_names
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    aps_name = "SIA4010_test_1_{}_PRECONDITION_31D_AB_{}.aps".format(
        scenario.case_id, stamp
    )
    aps_path = project_root / "Vista" / aps_name
    diagnostics = project_root / "sia4010_artifacts" / "diagnostics"
    evaluation_path = diagnostics / (
        "SIA4010_test_1_{}_preconditioning_31d_ab_evaluation.json".format(
            scenario.case_id
        )
    )
    audit_path = diagnostics / (
        "SIA4010_test_1_{}_preconditioning_31d_ab.json".format(scenario.case_id)
    )
    applied_options = {
        "start_day": 1,
        "start_month": 1,
        "end_day": 31,
        "end_month": 12,
        "reporting_interval": 3,
        "preconditioning_days": ISO_PRECONDITIONING_DAYS,
        "results_filename": aps_name,
    }
    restored = False
    payload = None
    try:
        if simulator.set_options(dict(applied_options)) is not True:
            raise RuntimeError("ApacheSim.set_options() failed for 31-day A/B")
        readback = dict(simulator.get_options())
        mismatches = {
            key: {"expected": value, "actual": readback.get(key)}
            for key, value in applied_options.items()
            if readback.get(key) != value
        }
        if mismatches:
            raise RuntimeError(
                "ApacheSim 31-day option read-back mismatch: {}".format(mismatches)
            )
        if simulator.run_simulation(queue_to_tasks=False) is not True:
            status_path = project_root / "apache" / "status.json"
            detail = (
                status_path.read_text(encoding="utf-8")
                if status_path.is_file()
                else ""
            )
            raise RuntimeError(
                "ApacheSim 31-day A/B run failed: {}".format(detail)
            )
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
            raise RuntimeError(
                "Expected exactly one APS room, found {}".format(len(room_ids))
            )
        receipt = evaluate_qualified_active_case(
            variant=scenario.variant,
            case_id=scenario.case_id,
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
        payload = {
            "schema_version": "1.0",
            "status": "DIAGNOSTIC_RESULTS_RECORDED",
            "case": "{}/{}".format(scenario.variant, scenario.case_id),
            "normative_basis": {
                "source": "ISO 52016-1 BESTEST climate workbook",
                "initialization_hours": ISO_INITIALIZATION_HOURS,
                "apache_mapping_under_test": {
                    "preconditioning_days": ISO_PRECONDITIONING_DAYS
                },
            },
            "options": {
                "before": restore_options,
                "applied": applied_options,
                "verified_readback": {
                    name: readback.get(name) for name in applied_options
                },
            },
            "aps": {"path": str(aps_path), "sha256": _sha256(aps_path)},
            "evaluation": str(evaluation_path),
            "evaluation_status": receipt.status,
            "observed_metric_count": receipt.observed_metric_count,
            "key_metrics": {
                "annual_heating": _key_metric(comparisons, "heating", "Annual"),
                "annual_cooling": _key_metric(comparisons, "cooling", "Annual"),
                "peak_heating": _key_metric(
                    comparisons, "peak heating", "Heating"
                ),
                "peak_cooling": _key_metric(
                    comparisons, "peak heating", "Cooling"
                ),
            },
            "purpose": (
                "Reversible qualification of the ISO 744-hour initialization "
                "mapping; no model save or compliance registration is performed."
            ),
            "compliance_claim_allowed": False,
        }
    finally:
        restored = simulator.set_options(restore_options) is True
        if restored:
            restored_readback = dict(simulator.get_options())
            restored = all(
                restored_readback.get(key) == value
                for key, value in restore_options.items()
            )
    if not restored:
        raise RuntimeError("Original ApacheSim options were not restored")
    payload["restoration"] = {"apache_options_restored": True}
    _write_json(audit_path, payload)
    print("SIA 4010 TEST 1 PRECONDITIONING A/B: {}".format(payload["status"]))
    print("Case: {}".format(payload["case"]))
    print("Initialization: 744 h -> 31 ApacheSim preconditioning days")
    for name, metric in payload["key_metrics"].items():
        print("{}: {}".format(name, metric))
    print("Diagnostic APS: {}".format(aps_path))
    print("Evaluation: {}".format(evaluation_path))
    print("Audit: {}".format(audit_path))
    print("Original ApacheSim options were restored.")
    print("No compliance evidence was registered.")
    return payload


if __name__ == "__main__":
    run()
