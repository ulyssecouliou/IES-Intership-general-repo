"""One-click simulation and APS comparison for a qualified SIA 4010 template."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

for module_name in tuple(sys.modules):
    if (
        module_name == "Run_VE_SIA4010_Evaluate_Active_Case"
        or module_name == "swiss_sia.reference_model"
        or module_name.startswith("swiss_sia.reference_model.")
    ):
        del sys.modules[module_name]


def run():
    """Run a verified exact Test 1E or Test 2A-2D template end to end."""

    import iesve

    from swiss_sia.reference_model.sia4010.evidence_registry import (
        register_template_case_simulation,
    )
    from swiss_sia.reference_model.sia4010.template_apachesim import (
        run_qualified_template_apachesim,
    )

    project = iesve.VEProject.get_current_project()
    simulation = run_qualified_template_apachesim(
        project=project,
        apachesim_factory=iesve.ApacheSim,
        repository_root=PROJECT_ROOT,
    )
    registry = (
        PROJECT_ROOT
        / "sia4010_evidence"
        / "autonomy"
        / "sia4010_case_evidence.json"
    )
    register_template_case_simulation(
        registry,
        simulation,
        project_path=Path(simulation.project_path),
    )
    print("SIA 4010 QUALIFIED-TEMPLATE APACHESIM: {}".format(simulation.status))
    print("Case: {}/{}".format(simulation.variant, simulation.case_id))
    print("APS: {}".format(simulation.results_path))
    print("Simulation audit: {}".format(simulation.audit_path))
    print("Step 2/2 - qualified APS extraction and official comparison")

    import Run_VE_SIA4010_Evaluate_Active_Case as evaluator

    evaluation = evaluator.run()
    print(
        "QUALIFIED TEMPLATE + APS WORKFLOW: {}".format(
            getattr(evaluation, "status", "NOT_CHECKABLE")
        )
    )
    return evaluation


if __name__ == "__main__":
    run()
