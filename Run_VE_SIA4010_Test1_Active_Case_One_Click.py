"""State-aware one-click execution of one prepared ISO Test 1 project.

The native Model Builder must first prepare ``sia_model_scenario.json`` in a
saved disposable project.  This launcher then creates the case when the
expected room is absent, safely resumes when exactly that room already exists,
applies the qualified runtime inputs, runs ApacheSim, evaluates the new APS and
updates the central evidence ledger.

One VE project remains one exact official case.  The launcher never deletes or
replaces rooms and never switches an active project to a different case.
"""

import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TEST1_CASES = {"600", "640", "600FF", "900", "940", "900FF"}


def _reload_reference_model_package():
    """Drop the cached repository package so corrected modules reload from disk.

    VEScripts reuses one Python interpreter between Run-button presses, so a
    module imported by an earlier run survives a source change.  Pressing this
    launcher directly instead of through Fast Start would otherwise keep the
    stale package.  The native ``iesve`` extension and the active VE project
    are untouched.

    Called from ``run()`` rather than at import time so that importing this
    module from a test never invalidates classes another module already holds.
    """

    for module_name in tuple(sys.modules):
        if module_name == "swiss_sia.reference_model" or module_name.startswith(
            "swiss_sia.reference_model."
        ):
            del sys.modules[module_name]


def _reload_launcher(module_name):
    """Import or reload one launcher in VE's persistent Python process."""

    module = sys.modules.get(module_name)
    if module is None:
        return importlib.import_module(module_name)
    return importlib.reload(module)


def _sequence(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return [value]


def _room_names(project):
    names = []
    for model in _sequence(getattr(project, "models", ())):
        get_bodies = getattr(model, "get_bodies", None)
        if not callable(get_bodies):
            continue
        for body in _sequence(get_bodies(False)):
            if hasattr(body, "get_room_data"):
                names.append(str(getattr(body, "name", "") or ""))
    return names


def _failed_control_ids(outcome):
    """Return the exact failed validation controls from a workflow outcome."""

    failed = set()
    for result in getattr(outcome, "validation_results", ()) or ():
        status = str(getattr(getattr(result, "status", ""), "value", ""))
        if not status:
            status = str(getattr(result, "status", ""))
        if "FAIL" in status.upper():
            failed.add(str(getattr(result, "control_id", "") or ""))
    return {control_id for control_id in failed if control_id}


def _outcome_failed(outcome):
    status = str(getattr(getattr(outcome, "status", ""), "value", ""))
    if not status:
        status = str(getattr(outcome, "status", ""))
    return "FAIL" in status.upper()


def _build_resume_and_calibrate_if_required(resume_after_import):
    """Run the guarded builder and repair only the proven glazing-U failure."""

    model_builder = _reload_launcher("Run_VE_SIA_Model_Builder")
    outcome = model_builder.run(resume_after_import=resume_after_import)
    if not _outcome_failed(outcome):
        return outcome

    failed_controls = _failed_control_ids(outcome)
    if failed_controls != {"VE-THERM-004"}:
        return outcome

    print(
        "Automatic recovery - calibrate VE whole-window U-value and resume "
        "without importing geometry"
    )
    calibrator = _reload_launcher(
        "Run_VE_Calibrate_External_Glazing_UValue"
    )
    calibrator.run()
    model_builder = _reload_launcher("Run_VE_SIA_Model_Builder")
    return model_builder.run(resume_after_import=True)


def run():
    """Create/resume, qualify, simulate and evaluate the active Test 1 case."""

    _reload_reference_model_package()
    try:
        import iesve  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Run this script from the IESVE VEScripts editor") from exc

    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.sia4010.scenario_preflight import (
        is_temporary_ve_project,
    )

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("Open and save one disposable Test 1 project first")
    project_path = Path(str(getattr(project, "path", "") or ""))
    if not project_path.is_dir() or is_temporary_ve_project(project_path):
        raise RuntimeError("Save the disposable VE project before execution")
    scenario_path = project_path / "sia_model_scenario.json"
    scenario = ModelScenario.load(scenario_path)
    if scenario.variant != "test_1" or scenario.case_id not in TEST1_CASES:
        raise RuntimeError(
            "This launcher supports Test 1 cases {} only; active case is {}/{}"
            .format(
                ", ".join(sorted(TEST1_CASES)),
                scenario.variant,
                scenario.case_id,
            )
        )

    expected_room = "SIA4010_TEST_1_{}_ZONE".format(scenario.case_id)
    rooms_before = _room_names(project)
    wrong_rooms = [name for name in rooms_before if name != expected_room]
    expected_count = rooms_before.count(expected_room)
    if wrong_rooms or expected_count > 1:
        raise RuntimeError(
            "Fail-closed project identity gate: expected only {!r}; found {}"
            .format(expected_room, rooms_before)
        )

    print("SIA 4010 TEST 1 ACTIVE-CASE ONE-CLICK")
    print("Project: {}".format(project_path))
    print("Case: test_1/{}".format(scenario.case_id))
    if expected_count == 0:
        print("Step 1/3 - guarded model generation/runtime qualification")
        outcome = _build_resume_and_calibrate_if_required(False)
    else:
        print(
            "Step 1/3 - expected generated room already exists; validate and "
            "resume without geometry import"
        )
        outcome = _build_resume_and_calibrate_if_required(True)

    if _outcome_failed(outcome):
        raise RuntimeError(
            "Model workflow failed controls={}; see its audit report before "
            "retrying".format(sorted(_failed_control_ids(outcome)))
        )
    rooms_after = _room_names(project)
    if rooms_after.count(expected_room) != 1 or any(
        name != expected_room for name in rooms_after
    ):
        raise RuntimeError(
            "Post-generation room identity mismatch: {}".format(rooms_after)
        )

    print("Step 2/3 - qualify Test 1 runtime capacity and emission inputs")
    runtime_qualifier = _reload_launcher(
        "Run_VE_SIA4010_Test1_Qualify_Runtime_Inputs"
    )

    runtime_report = runtime_qualifier.run()
    if not Path(runtime_report).is_file():
        raise RuntimeError("Runtime-input qualification report was not created")

    print("Step 3/3 - guarded ApacheSim plus qualified APS evaluation")
    simulator = _reload_launcher("Run_VE_SIA4010_Simulate_Active_Case")

    evaluation = simulator.run()
    print(
        "TEST 1 ACTIVE-CASE ONE-CLICK COMPLETE: {}".format(
            getattr(evaluation, "status", "NOT_CHECKABLE")
        )
    )
    print("Save the VE project now to persist the qualified room inputs.")
    return evaluation


if __name__ == "__main__":
    run()
