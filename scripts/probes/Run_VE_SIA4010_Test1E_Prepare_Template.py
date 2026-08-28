"""Prepare the exact SIA 4010 Test 1E template project, without VE mutation.

Test 1E is the sole judged Test 1 case.  Its APS comparator is implemented,
but the fabric-awning model must be an independently reviewed exact VE
template because VE 2025 does not expose every required optical setter.  This
launcher installs the controlled external-input evidence, rebuilds the
source-traced 1E bundle and writes a PREPARE_ONLY scenario.  It never creates
geometry, assigns a construction, saves the project or claims a result.
"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

EXPECTED_PROJECT_FOLDER = "SIA4010_TEST1_1E_TEMPLATE"


def _reload_reference_model_package():
    for module_name in tuple(sys.modules):
        if module_name == "swiss_sia.reference_model" or module_name.startswith(
            "swiss_sia.reference_model."
        ):
            del sys.modules[module_name]


def _scenario_files(receipt):
    names = (
        ("case_manifest_path", "sia4010_all_classes.json"),
        ("config_path", "reference_model_config.json"),
        ("asset_manifest_path", "reference_model_assets.json"),
    )
    result = []
    for attribute, fallback in names:
        value = getattr(receipt, attribute, None)
        path = Path(str(value)) if value else PROJECT_ROOT / "config" / fallback
        if not path.is_file():
            raise RuntimeError("Prepared 1E input is missing: {}".format(path))
        result.append(str(path))
    return result


def run():
    """Write a checksum-traced PREPARE_ONLY scenario for test_1/1E."""

    try:
        import iesve  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Run this launcher inside IESVE VEScripts") from exc

    _reload_reference_model_package()
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.sia4010.native_ui import ModelBuilderController
    from swiss_sia.reference_model.sia4010.scenario_preflight import (
        is_temporary_ve_project,
    )

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("Open and save the dedicated Test 1E project first")
    project_path = Path(str(getattr(project, "path", "") or ""))
    if not project_path.is_dir() or is_temporary_ve_project(project_path):
        raise RuntimeError("Save the dedicated Test 1E project before preparation")
    if project_path.name.casefold() != EXPECTED_PROJECT_FOLDER.casefold():
        raise RuntimeError(
            "Wrong active project: expected folder {!r}, received {!r}. No "
            "scenario was written.".format(
                EXPECTED_PROJECT_FOLDER, project_path.name
            )
        )

    scenario_path = project_path / "sia_model_scenario.json"
    if scenario_path.is_file():
        existing = ModelScenario.load(scenario_path)
        if (existing.variant, existing.case_id) not in {
            ("test_1", "1D"),
            ("test_1", "1E"),
        }:
            raise RuntimeError(
                "Existing scenario belongs to {}/{}; expected the completed "
                "1D base or an existing 1E preparation".format(
                    existing.variant, existing.case_id
                )
            )
        if (existing.variant, existing.case_id) == ("test_1", "1D"):
            print(
                "Verified copied base scenario test_1/1D; replacing only its "
                "scenario identity with the source-traced 1E preparation."
            )

    controller = ModelBuilderController()
    manifest_path, created, authorizations = (
        controller.install_prepared_external_input_manifest(
            project_path, PROJECT_ROOT
        )
    )
    receipt = controller.prepare_case_bundle(
        project_path,
        PROJECT_ROOT,
        "SIA4010_OFFICIAL",
        "1A",
        "test_1",
        "1E",
    )
    if receipt is None:
        raise RuntimeError("No source-traced Test 1E bundle was produced")
    case_manifest, ve_config, ve_assets = _scenario_files(receipt)
    payload = controller.build_payload(
        "SIA4010_TEST1_1E_TEMPLATE",
        "SIA4010_OFFICIAL",
        "1A",
        "test_1",
        "1E",
        "PREPARE_ONLY",
        case_manifest,
        ve_config,
        ve_assets,
    )
    scenario = controller.write_and_validate(project_path, payload)

    print("SIA 4010 TEST 1E TEMPLATE PREPARATION")
    print("Project: {}".format(project_path))
    print("Scenario: {}/{}".format(scenario.variant, scenario.case_id))
    print("External-input manifest: {} (installed={})".format(
        manifest_path, created
    ))
    print("Authorized evidence records: {}".format(len(authorizations)))
    print("Preparation status: {}".format(getattr(receipt, "status", "UNKNOWN")))
    print("Preparation audit: {}".format(getattr(receipt, "audit_path", "")))
    print("Scenario file: {}".format(scenario_path))
    print("TEST 1E: PREPARED_FOR_EXACT_TEMPLATE_COMPLETION_AND_REVIEW")
    print(
        "No VE object was created, assigned or saved. Complete the exact 1E "
        "model, including the reviewed fabric-awning optics, before running "
        "Run_VE_SIA4010_Capture_Active_Template.py."
    )
    return scenario_path


if __name__ == "__main__":
    run()
