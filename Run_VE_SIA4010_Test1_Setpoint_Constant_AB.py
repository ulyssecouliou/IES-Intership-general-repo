"""Reversible behavioural check of the Test 1 intermittent setpoint binding.

The active 640/940 room is simulated once with a temporary constant 20 degC
heating setpoint.  Comparing this result with the qualified variable-profile
run establishes whether ApacheSim is actually applying the 10/20 degC profile,
not merely whether VE reads its identifier back.  Room conditions and Apache
options are restored and no compliance evidence is registered.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import iesve


REPOSITORY_ROOT = Path(__file__).resolve().parent
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


def _sequence(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return [value]


def _mode(value):
    try:
        return {0: "constant", 1: "variable", 2: "two_value"}.get(
            int(value), ""
        )
    except (TypeError, ValueError):
        text = str(value).lower().replace("_", "")
        if "twovalue" in text:
            return "two_value"
        if "variable" in text:
            return "variable"
        if "constant" in text:
            return "constant"
        return ""


def _constant_setpoint_enum():
    """Resolve the VE-version-specific constant-setpoint enum member."""

    owners = [
        getattr(iesve, "setpoint_type", None),
        getattr(getattr(iesve, "VERoomData", None), "setpoint_type", None),
        getattr(
            getattr(iesve, "VEThermalTemplate", None), "setpoint_type", None
        ),
    ]
    for owner in owners:
        if owner is not None and hasattr(owner, "constant"):
            return getattr(owner, "constant")
    raise RuntimeError("VE constant-setpoint enum is unavailable")


def run():
    """Run constant-20 A/B and restore the exact original room controls."""

    from Run_VE_SIA4010_Test1_Preconditioning_AB import (
        _key_metric,
        _room_id,
        _sha256,
        _wait_for_aps,
        _write_json,
    )
    from swiss_sia.reference_model.sia4010.active_case_evaluation import (
        evaluate_qualified_active_case,
    )
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.simulation_results import open_results_reader

    project = iesve.VEProject.get_current_project()
    project_root = Path(str(project.path)).resolve()
    scenario = ModelScenario.load(project_root / "sia_model_scenario.json")
    if scenario.variant != "test_1" or scenario.case_id not in {"640", "940"}:
        raise RuntimeError(
            "Setpoint A/B requires test_1/640 or test_1/940; active is {}/{}"
            .format(scenario.variant, scenario.case_id)
        )

    expected_name = "SIA4010_TEST_1_{}_ZONE".format(scenario.case_id)
    rooms = [
        body
        for model in _sequence(project.models)
        for body in _sequence(model.get_bodies(False))
        if str(getattr(body, "name", "")) == expected_name
    ]
    if len(rooms) != 1:
        raise RuntimeError(
            "Expected one room named {!r}; found {}".format(
                expected_name, len(rooms)
            )
        )
    room_data = rooms[0].get_room_data()
    original_conditions = dict(room_data.get_room_conditions())
    if _mode(original_conditions.get("heating_setpoint_type")) != "variable":
        raise RuntimeError(
            "Active room is not using a variable heating setpoint: {!r}".format(
                original_conditions.get("heating_setpoint_type")
            )
        )
    original_profile = str(
        original_conditions.get("heating_setpoint_profile", "") or ""
    )
    if not original_profile or original_profile == "0":
        raise RuntimeError("Active room has no variable heating-setpoint profile")

    original_inheritance = original_conditions.get(
        "heating_setpoint_from_template", False
    )
    restore_conditions = {
        "heating_setpoint_type": original_conditions["heating_setpoint_type"],
        "heating_setpoint_profile": original_conditions[
            "heating_setpoint_profile"
        ],
        "heating_setpoint_from_template": original_inheritance,
    }
    constant_type = _constant_setpoint_enum()
    applied_conditions = {
        "heating_setpoint_type": constant_type,
        "heating_setpoint": 20.0,
        "heating_setpoint_from_template": False,
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
    )
    missing_options = [
        name for name in option_names if name not in original_options
    ]
    if missing_options:
        raise RuntimeError(
            "ApacheSim options required for restoration are missing: {}".format(
                missing_options
            )
        )
    restore_options = {name: original_options[name] for name in option_names}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    aps_name = "SIA4010_test_1_{}_CONSTANT20_AB_{}.aps".format(
        scenario.case_id, stamp
    )
    aps_path = project_root / "Vista" / aps_name
    diagnostics = project_root / "sia4010_artifacts" / "diagnostics"
    evaluation_path = diagnostics / (
        "SIA4010_test_1_{}_constant20_ab_evaluation.json".format(
            scenario.case_id
        )
    )
    audit_path = diagnostics / (
        "SIA4010_test_1_{}_constant20_ab.json".format(scenario.case_id)
    )
    applied_options = {
        "start_day": 1,
        "start_month": 1,
        "end_day": 31,
        "end_month": 12,
        "reporting_interval": 3,
        "results_filename": aps_name,
    }
    payload = None
    room_restored = False
    options_restored = False
    try:
        room_data.set_room_conditions(applied_conditions)
        applied_readback = dict(room_data.get_room_conditions())
        if _mode(applied_readback.get("heating_setpoint_type")) != "constant":
            raise RuntimeError(
                "Constant setpoint mode did not persist: {!r}".format(
                    applied_readback.get("heating_setpoint_type")
                )
            )
        if abs(float(applied_readback.get("heating_setpoint")) - 20.0) > 1e-6:
            raise RuntimeError("Constant 20 degC setpoint did not persist")
        if simulator.set_options(applied_options) is not True:
            raise RuntimeError("ApacheSim.set_options() failed for setpoint A/B")
        if simulator.run_simulation(queue_to_tasks=False) is not True:
            status_path = project_root / "apache" / "status.json"
            detail = (
                status_path.read_text(encoding="utf-8")
                if status_path.is_file()
                else ""
            )
            raise RuntimeError("ApacheSim setpoint A/B failed: {}".format(detail))
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
            "setpoint_ab": {
                "original_mode": "variable",
                "original_profile": original_profile,
                "temporary_mode": "constant",
                "temporary_setpoint_c": 20.0,
                "verified_readback": {
                    "mode": _mode(
                        applied_readback.get("heating_setpoint_type")
                    ),
                    "setpoint_c": applied_readback.get("heating_setpoint"),
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
                "Behavioural A/B only: determine whether ApacheSim applies the "
                "linked 10/20 degC absolute profile."
            ),
            "compliance_claim_allowed": False,
        }
    finally:
        try:
            options_restored = simulator.set_options(restore_options) is True
        finally:
            room_data.set_room_conditions(restore_conditions)
            restored = dict(room_data.get_room_conditions())
            room_restored = (
                _mode(restored.get("heating_setpoint_type")) == "variable"
                and str(restored.get("heating_setpoint_profile", ""))
                == original_profile
                and restored.get("heating_setpoint_from_template", False)
                == original_inheritance
            )
    if not room_restored or not options_restored:
        raise RuntimeError(
            "Setpoint A/B restoration failed: room={}, options={}".format(
                room_restored, options_restored
            )
        )
    payload["restoration"] = {
        "room_conditions_restored": True,
        "apache_options_restored": True,
    }
    _write_json(audit_path, payload)
    print("SIA 4010 TEST 1 SETPOINT CONSTANT A/B: {}".format(payload["status"]))
    print("Case: {}".format(payload["case"]))
    print("Original profile: {}".format(original_profile))
    for name, metric in payload["key_metrics"].items():
        print("{}: {}".format(name, metric))
    print("Diagnostic APS: {}".format(aps_path))
    print("Evaluation: {}".format(evaluation_path))
    print("Audit: {}".format(audit_path))
    print("Original variable setpoint and ApacheSim options were restored.")
    print("No compliance evidence was registered.")
    return payload


if __name__ == "__main__":
    run()
