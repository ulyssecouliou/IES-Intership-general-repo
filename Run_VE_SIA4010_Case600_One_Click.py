"""One-click guarded bootstrap and creation of SIA 4010 Case 600."""

import shutil
import sys
from pathlib import Path

import iesve


REPOSITORY_ROOT = Path(__file__).resolve().parent
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

import Run_VE_Verify_Case600_Weather as weather_probe
import Run_VE_SIA_Model_Builder as model_builder


def _is_room(body):
    try:
        return body.type == iesve.VEBody.VEBody_type.room
    except Exception:
        return str(getattr(body, "type", "")).casefold().endswith("room")


def _copy_verified_input(source, destination):
    """Copy one controlled input, refusing to replace different content."""

    from swiss_sia.reference_model.sia4010.weather_verification import (
        sha256_file,
    )

    if destination.is_file():
        if sha256_file(source) != sha256_file(destination):
            raise RuntimeError(
                "A different file already exists and was not overwritten: "
                "{}".format(destination)
            )
        return
    shutil.copy2(source, destination)


def _bootstrap_blank_project():
    """Populate a saved blank VE project with the verified Case 600 bundle."""

    from swiss_sia.reference_model.sia4010.mvp_bundle import (
        build_case600_mvp_bundle,
    )
    from swiss_sia.reference_model.sia4010.native_ui import (
        ModelBuilderController,
    )
    from swiss_sia.reference_model.sia4010.scenario_preflight import (
        evaluate_scenario,
        is_temporary_ve_project,
    )

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("Open and save a blank VE project first.")
    project_path = Path(str(project.path))
    if is_temporary_ve_project(project_path):
        raise RuntimeError(
            "The active VE project is still temporary. Use File > Save Project "
            "As, then run this script again."
        )
    if not project_path.is_dir():
        raise RuntimeError(
            "The active VE project folder does not exist: {}".format(
                project_path
            )
        )
    models = list(getattr(project, "models", []) or [])
    if not models:
        raise RuntimeError("The active VE project exposes no real model.")
    rooms = [
        body
        for body in models[0].get_bodies(False)
        if _is_room(body)
    ]
    if rooms:
        raise RuntimeError(
            "Safety gate: the active project is not blank ({} room(s)). "
            "Create and save a new blank project; SWISSG must not be used."
            .format(len(rooms))
        )

    source_directory = (
        REPOSITORY_ROOT / "references" / "standards" / "bestest"
    )
    weather_source = source_directory / "DRYCOLD_IESVE.epw"
    verification_source = (
        source_directory / "DRYCOLD_IESVE_EPW_DERIVATION.json"
    )
    if not weather_source.is_file() or not verification_source.is_file():
        raise RuntimeError(
            "Controlled DRYCOLD inputs are missing from {}".format(
                source_directory
            )
        )
    weather_destination = project_path / weather_source.name
    verification_destination = project_path / verification_source.name
    _copy_verified_input(weather_source, weather_destination)
    _copy_verified_input(verification_source, verification_destination)

    receipt = build_case600_mvp_bundle(
        project_path,
        REPOSITORY_ROOT,
        weather_destination,
    )
    controller = ModelBuilderController()
    payload = controller.build_payload(
        "SIA4010_1A_600",
        "SIA4010_OFFICIAL",
        "1A",
        "test_1",
        "600",
        "CREATE_IN_ACTIVE_VE_PROJECT",
        "sia4010_case_manifest.json",
        "reference_model_config.json",
        "reference_model_assets.json",
    )
    scenario = controller.write_and_validate(project_path, payload)
    preflight = evaluate_scenario(
        scenario, project_path, REPOSITORY_ROOT
    )
    if not preflight.allows_mutation:
        raise RuntimeError(
            "Case 600 preflight blocked mutation: {}".format(
                "; ".join(preflight.blockers)
            )
        )
    print("Bootstrap: {}".format(receipt.status))
    print("Project: {}".format(project_path))
    print("Preflight: {}".format(preflight.status))
    return project_path


def run():
    """Verify the active project's TMY, then run the strict model workflow."""

    print("SIA 4010 CASE 600 ONE-CLICK WORKFLOW")
    print("Step 1/3 - bootstrap the saved blank VE project")
    _bootstrap_blank_project()
    print("Step 2/3 - read-only weather verification")
    weather_probe.run()
    print("Step 3/3 - guarded Case 600 model creation")
    return model_builder.run()


if __name__ == "__main__":
    run()
