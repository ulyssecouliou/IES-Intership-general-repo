"""Verify and register the active disposable SIA 4010 template model."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))


def _purge_cached_reference_model_modules():
    """Ensure VE uses the current repository code on every Run press."""

    for module_name in tuple(sys.modules):
        if module_name == "swiss_sia.reference_model" or module_name.startswith(
            "swiss_sia.reference_model."
        ):
            del sys.modules[module_name]


def run():
    """Recheck the exact template copy and add its model proof to the ledger."""

    _purge_cached_reference_model_modules()

    import iesve

    from swiss_sia.reference_model.sia4010.evidence_registry import (
        register_model_outcome,
    )
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.sia4010.template_strategy import (
        qualify_instantiated_template_model,
    )

    project = iesve.VEProject.get_current_project()
    project_path = Path(str(getattr(project, "path", "") or "")).resolve()
    instantiation = (
        project_path
        / "sia4010_artifacts"
        / "templates"
        / "template_instantiation.json"
    )
    print("Active VE project: {}".format(project_path))
    if not instantiation.is_file():
        expected = (
            project_path.parent
            / "SIA4010_TEST_1_1E_DISPOSABLE"
            / "SIA4010_TEST1_1E_TEMPLATE.mdl"
        )
        raise RuntimeError(
            "The active project is not an instantiated disposable template. "
            "Close the source template, then open '{}' and rerun.".format(expected)
        )
    receipt = qualify_instantiated_template_model(project_path, PROJECT_ROOT)
    scenario = ModelScenario.load(receipt.scenario_path)
    registry = (
        PROJECT_ROOT
        / "sia4010_evidence"
        / "autonomy"
        / "sia4010_case_evidence.json"
    )
    register_model_outcome(
        registry,
        scenario,
        workflow_status="PASS",
        report_path=receipt.report_path,
        project_path=project_path,
    )
    print("SIA 4010 TEMPLATE MODEL: {}".format(receipt.status))
    print("Case: {}/{}".format(receipt.variant, receipt.case_id))
    print("Template: {}".format(receipt.template_id))
    print("Model proof: {}".format(receipt.report_path))
    print("Evidence ledger: {}".format(registry))
    print("Next: run the guarded ApacheSim launcher for this test family.")
    return receipt


if __name__ == "__main__":
    run()
