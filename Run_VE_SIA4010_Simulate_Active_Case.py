"""One-click guarded ApacheSim run followed by qualified APS evaluation."""

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
    """Run the exact active Test 1 case, then evaluate its new APS evidence."""

    import iesve

    from swiss_sia.reference_model.sia4010.apachesim_qualification import (
        run_qualified_apachesim,
    )
    from swiss_sia.reference_model.sia4010.evidence_registry import (
        register_case_simulation,
    )
    from swiss_sia.reference_model.ve_api import IesVeGateway

    project = iesve.VEProject.get_current_project()
    print("Active VE project: {}".format(str(getattr(project, "path", "") or "")))
    gateway = IesVeGateway(iesve_module=iesve)
    weather_before, weather_after = (
        gateway.normalize_weather_reference_for_apachesim()
    )
    if weather_after != weather_before:
        print(
            "ApacheSim weather reference repaired: {} -> {}".format(
                weather_before, weather_after
            )
        )
    else:
        print("ApacheSim weather reference verified: {}".format(weather_after))
    simulation = run_qualified_apachesim(
        project=project,
        apachesim_factory=iesve.ApacheSim,
        repository_root=PROJECT_ROOT,
    )
    print("SIA 4010 GUARDED APACHESIM: {}".format(simulation.status))
    print("Case: {}/{}".format(simulation.variant, simulation.case_id))
    print("APS: {}".format(simulation.results_path))
    print("Simulation audit: {}".format(simulation.audit_path))
    registry = (
        PROJECT_ROOT
        / "sia4010_evidence"
        / "autonomy"
        / "sia4010_case_evidence.json"
    )
    register_case_simulation(
        registry,
        simulation,
        project_path=Path(simulation.project_path),
    )
    print("Evidence ledger: {}".format(registry))
    print("Step 2/2 - qualified APS extraction and comparison")

    # Import after the simulation package reload so the evaluator uses the same
    # current source tree and the newest, uniquely named APS just created.
    import Run_VE_SIA4010_Evaluate_Active_Case as evaluator

    evaluation = evaluator.run()
    print(
        "ONE-CLICK SIMULATION + APS WORKFLOW: {}".format(
            getattr(evaluation, "status", "NOT_CHECKABLE")
        )
    )
    return evaluation


if __name__ == "__main__":
    run()
