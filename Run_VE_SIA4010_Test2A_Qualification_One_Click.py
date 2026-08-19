"""One-click, fail-closed VEScript for the existing Test 2A probes.

Run this only in a fresh saved disposable project containing at least one
opening proxy.  The terminal result qualifies storage plus one transient,
restored opening assignment; it is not a generated test model and does not
authorize a compliance claim.
"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run():
    """Prepare Test 2A and execute its guarded qualification chain."""

    try:
        import iesve  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Run this script from the IESVE VEScripts editor."
        ) from exc

    import Run_VE_SIA4010_Prepare_Case_Scenario as preparation
    from swiss_sia.reference_model.sia4010.test2a_optical_workflow import (
        run_test2a_2e1_optical_workflow,
    )
    from swiss_sia.reference_model.sia4010.test2a_opening_assignment_qualification import (
        qualify_test2a_opening_assignment,
    )
    from swiss_sia.reference_model.sia4010.test2a_profile_qualification import (
        qualify_test2a_profile_graph,
    )
    from swiss_sia.reference_model.sia4010.test2a_qualification_chain import (
        run_test2a_qualification_chain,
    )
    from swiss_sia.reference_model.sia4010.test2a_runtime_capability import (
        write_test2a_runtime_capability_report,
    )
    from swiss_sia.reference_model.sia4010.test2a_shading_qualification import (
        qualify_test2a_shading_setters,
    )
    from swiss_sia.reference_model.sia4010.test2a_thermal_glazing_qualification import (
        qualify_test2a_base_glazing_thermal_storage,
    )

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("Open a fresh saved disposable VE project first.")
    project_path = Path(str(getattr(project, "path", "") or ""))

    def prepare():
        preparation.CASE = "2A"
        preparation.TARGET_CLASS = "1A"
        preparation.ALLOW_SCENARIO_REPLACEMENT = False
        preparation.INSTALL_PREPARED_EXTERNAL_INPUTS = True
        return preparation.run()

    print("SIA 4010 TEST 2A QUALIFICATION CHAIN")
    print("Project: {}".format(project_path))
    print(
        "Scope: profiles, two glazed CDB probes, equivalent base-glazing U-value, "
        "then one transient opening assignment with verified restoration; no "
        "simulation or compliance claim."
    )
    receipt = run_test2a_qualification_chain(
        project,
        prepare=prepare,
        runtime_probe=lambda: write_test2a_runtime_capability_report(
            iesve, project
        ),
        profile_qualification=lambda: qualify_test2a_profile_graph(
            iesve, project
        ),
        shading_qualification=lambda: qualify_test2a_shading_setters(
            iesve, project, repository_root=PROJECT_ROOT
        ),
        optical_qualification=lambda: run_test2a_2e1_optical_workflow(
            iesve, project, project_path, PROJECT_ROOT
        ).to_dict(),
        thermal_glazing_qualification=lambda: (
            qualify_test2a_base_glazing_thermal_storage(
                iesve, project, repository_root=PROJECT_ROOT
            )
        ),
        opening_assignment_qualification=lambda: (
            qualify_test2a_opening_assignment(iesve, project)
        ),
    )
    print("TEST 2A QUALIFICATION CHAIN: {}".format(receipt.status))
    print("Audit: {}".format(receipt.report_path))
    print("Test 2A model mutation supported: NO")
    print("Compliance claim allowed: NO")
    return receipt.to_dict()


if __name__ == "__main__":
    run()
