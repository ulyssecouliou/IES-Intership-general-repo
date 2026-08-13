"""Fast, fail-closed Test 1 bootstrap plus one-click VE execution.

Open and save one blank project for one exact case.  This launcher selects the
next incomplete ISO case from the evidence ledger, copies the controlled
DRYCOLD transport and its derivation audit, writes the exact scenario, then
delegates to the existing create/resume/simulate/evaluate workflow.
"""

import importlib
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

#: The six ISO cases, then the four diagnostic cases of the Test 1 to Test 2
#: transition. 1E is absent on purpose: its fabric-awning dynamics is not
#: stated by the specification, so no generator may claim to reproduce it.
TEST1_ISO_CASES = ("600", "640", "600FF", "900", "940", "900FF")
TEST1_DIAGNOSTIC_CASES = ("1A", "1B", "1C", "1D")
TEST1_CASES = TEST1_ISO_CASES + TEST1_DIAGNOSTIC_CASES


def _reload_launcher(module_name):
    """Import or reload one launcher in VE's persistent Python process."""

    module = sys.modules.get(module_name)
    if module is None:
        return importlib.import_module(module_name)
    return importlib.reload(module)


def _reload_reference_model_package():
    """Drop cached project modules before rebuilding project-local inputs.

    VEScripts keeps one Python interpreter alive between runs.  Removing only
    this repository package ensures that corrected bundle builders and schema
    validators are imported from disk while leaving the native ``iesve``
    extension and the active VE project untouched.
    """

    for module_name in tuple(sys.modules):
        if module_name == "swiss_sia.reference_model" or module_name.startswith(
            "swiss_sia.reference_model."
        ):
            del sys.modules[module_name]


def _execution_mode(case_id):
    """Return the guarded mode registered for one exact Test 1 case."""

    from swiss_sia.reference_model.sia4010.case_registry import (
        get_case_capability,
    )

    capability = get_case_capability("test_1", str(case_id).upper())
    if capability.mutation_supported:
        return "CREATE_IN_ACTIVE_VE_PROJECT"
    if capability.runtime_qualification_supported:
        return "QUALIFY_IN_ACTIVE_VE_PROJECT"
    raise RuntimeError(
        "No guarded VE execution mode is registered for test_1/{}".format(
            case_id
        )
    )


def _sequence(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return [value]


def _rooms(project):
    result = []
    for model in _sequence(getattr(project, "models", ())):
        getter = getattr(model, "get_bodies", None)
        if not callable(getter):
            continue
        result.extend(
            body
            for body in _sequence(getter(False))
            if hasattr(body, "get_room_data")
        )
    return result


def _next_campaign_case():
    from swiss_sia.reference_model.sia4010.evidence_registry import load_registry
    from swiss_sia.reference_model.sia4010.test1_campaign import (
        build_test1_campaign_status,
    )

    registry_path = (
        PROJECT_ROOT
        / "sia4010_evidence"
        / "autonomy"
        / "sia4010_case_evidence.json"
    )
    if not registry_path.is_file():
        return "600"
    status = build_test1_campaign_status(load_registry(registry_path))
    next_case = status.get("next_case")
    return str(next_case["case_id"]) if next_case else "600"


def _select_case(project_path):
    name = project_path.name.upper()
    # Prefer the longer free-floating identifiers so ``600`` is not selected
    # from a folder explicitly named ``...TEST1_600FF_DISPOSABLE``.
    for case_id in sorted(TEST1_CASES, key=len, reverse=True):
        if (
            "TEST1_{}".format(case_id) in name
            or "TEST_{}_TEST1".format(case_id) in name
        ):
            return case_id
    suggested = _next_campaign_case()
    import tkinter as tk
    from tkinter import simpledialog

    root = tk.Tk()
    root.withdraw()
    try:
        selected = simpledialog.askstring(
            "SIA 4010 Test 1",
            "Cas exact. ISO : 600, 640, 600FF, 900, 940, 900FF. "
            "Diagnostique : 1A, 1B, 1C, 1D (climat Kloten, livrable "
            "horaire, sans critere).",
            initialvalue=suggested,
            parent=root,
        )
    finally:
        root.destroy()
    if not selected:
        return None
    normalized = str(selected).strip().upper()
    if normalized not in TEST1_CASES:
        raise RuntimeError("Unsupported Test 1 case: {}".format(normalized))
    return normalized


def _prepare_scenario(project_path, case_id):
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.sia4010.native_ui import ModelBuilderController
    from swiss_sia.reference_model.sia4010.scenario_preflight import (
        evaluate_scenario,
    )

    scenario_path = project_path / "sia_model_scenario.json"
    execution_mode = _execution_mode(case_id)
    controller = ModelBuilderController()
    existing = None
    if scenario_path.is_file():
        existing = ModelScenario.load(scenario_path)
        if existing.variant != "test_1" or existing.case_id != case_id:
            raise RuntimeError(
                "Existing scenario belongs to {}/{} instead of test_1/{}".format(
                    existing.variant,
                    existing.case_id,
                    case_id,
                )
            )
    receipt = controller.prepare_case_bundle(
        project_path,
        PROJECT_ROOT,
        "SIA4010_OFFICIAL",
        "1A",
        "test_1",
        case_id,
    )
    if receipt is None:
        raise RuntimeError("No source-traced Test 1 bundle was produced")
    if existing is not None:
        if existing.execution_mode != execution_mode:
            payload = json.loads(scenario_path.read_text(encoding="utf-8"))
            payload["execution"]["mode"] = execution_mode
            existing = ModelBuilderController.write_and_validate(
                project_path, payload
            )
            preflight = evaluate_scenario(
                existing, project_path, PROJECT_ROOT
            )
            if not preflight.allows_mutation:
                raise RuntimeError(
                    "Corrected Test 1 execution mode failed preflight: {}".format(
                        "; ".join(preflight.blockers)
                    )
                )
            print(
                "Scenario execution mode corrected: {}".format(
                    execution_mode
                )
            )
        preflight = evaluate_scenario(existing, project_path, PROJECT_ROOT)
        if not preflight.allows_mutation:
            raise RuntimeError(
                "Refreshed Test 1 bundle failed preflight: {}".format(
                    "; ".join(preflight.blockers)
                )
            )
        print("Bundle: {}".format(getattr(receipt, "status", "PREPARED")))
        print("Preflight: {}".format(preflight.status))
        return existing
    payload = controller.build_payload(
        "SIA4010_TEST1_{}".format(case_id),
        "SIA4010_OFFICIAL",
        "1A",
        "test_1",
        case_id,
        execution_mode,
        "sia4010_case_manifest.json",
        "reference_model_config.json",
        "reference_model_assets.json",
    )
    scenario = controller.write_and_validate(project_path, payload)
    preflight = evaluate_scenario(scenario, project_path, PROJECT_ROOT)
    if not preflight.allows_mutation:
        raise RuntimeError(
            "Test 1 preflight blocked mutation: {}".format(
                "; ".join(preflight.blockers)
            )
        )
    print("Bundle: {}".format(getattr(receipt, "status", "PREPARED")))
    print("Preflight: {}".format(preflight.status))
    return scenario


def run():
    """Prepare and execute one exact case in the active saved project."""

    try:
        import iesve  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Run this launcher inside IESVE VEScripts") from exc

    _reload_reference_model_package()
    from swiss_sia.reference_model.sia4010.scenario_preflight import (
        is_temporary_ve_project,
    )

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("Open and save a blank disposable VE project first")
    project_path = Path(str(getattr(project, "path", "") or ""))
    if not project_path.is_dir() or is_temporary_ve_project(project_path):
        raise RuntimeError("Save the blank project before running Fast Start")
    case_id = _select_case(project_path)
    if case_id is None:
        print("SIA 4010 TEST 1 FAST START: CANCELLED")
        return None
    existing_scenario = project_path / "sia_model_scenario.json"
    if _rooms(project) and not existing_scenario.is_file():
        raise RuntimeError(
            "Safety gate: the project is not blank and contains no matching "
            "Test 1 scenario. Use a fresh disposable project."
        )
    print("SIA 4010 TEST 1 FAST START")
    print("Project: {}".format(project_path))
    print("Case: test_1/{}".format(case_id))
    print("Step 1/2 - controlled weather, bundle and scenario preparation")
    _prepare_scenario(project_path, case_id)
    print("Step 2/2 - create/resume, qualify, simulate and evaluate")
    active_case = _reload_launcher(
        "Run_VE_SIA4010_Test1_Active_Case_One_Click"
    )

    return active_case.run()


if __name__ == "__main__":
    run()
