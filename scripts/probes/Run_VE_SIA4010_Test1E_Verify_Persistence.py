"""Verify the saved and reopened Test 1E awning read-back."""

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

    from swiss_sia.reference_model.sia4010.test1e_awning_qualification import (
        verify_test1e_awning_persistence,
    )

    project = iesve.VEProject.get_current_project()
    report = verify_test1e_awning_persistence(iesve, project)
    print("SIA 4010 TEST 1E AWNING: PERSISTED_AWNING_READBACK_VERIFIED")
    print("Project: {}".format(getattr(project, "path", "")))
    print("Openings verified: 2; construction: EXTW")
    print("Report: {}".format(report))
    print("No VE object was changed and the project was not saved by the script.")
    print("NEXT: send this output before template capture and APS simulation.")
    return report


if __name__ == "__main__":
    run()
