"""Reapply the 1E shade subset and explicitly assign EXTW to both windows."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))


def run():
    for module_name in tuple(sys.modules):
        if module_name == "swiss_sia.reference_model" or module_name.startswith(
            "swiss_sia.reference_model."
        ):
            del sys.modules[module_name]
    import iesve  # type: ignore

    project = iesve.VEProject.get_current_project()
    project_path = Path(str(getattr(project, "path", "") or ""))
    if project_path.name.casefold().startswith(
        "sia4010_test1_1e_equivalent_glazing_disposable"
    ):
        # The equivalent-glazing workflow needs a second-session shade write
        # on the already-persisted EXTW1 construction.  Route the familiar
        # legacy launcher to that guarded operation so the two similarly named
        # scripts cannot accidentally target the wrong receipt family.
        from Run_VE_SIA4010_Test1E_Reapply_Equivalent_Shade_After_Reload import (
            run as run_equivalent_reapplication,
        )

        return run_equivalent_reapplication()

    from swiss_sia.reference_model.sia4010.test1e_awning_qualification import (
        reapply_test1e_awning_with_opening_assignment,
    )

    report = reapply_test1e_awning_with_opening_assignment(iesve, project)
    print("SIA 4010 TEST 1E AWNING: PROVISIONAL_AWNING_REASSIGNED_AND_READBACK_VERIFIED")
    print("Construction EXTW reapplied to both source-identified south windows.")
    print("Report: {}".format(report))
    print("Project saved by script: NO")
    print("NEXT: Ctrl+S, close the project, reopen it, then rerun persistence verification.")
    print("This is not yet a Test 1 PASS.")
    return report


if __name__ == "__main__":
    run()
