"""Apply the guarded writable fabric-awning subset to the exact 1E windows."""

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
        qualify_test1e_awning,
    )

    project = iesve.VEProject.get_current_project()
    report = qualify_test1e_awning(iesve, project, PROJECT_ROOT)
    print("SIA 4010 TEST 1E AWNING: PROVISIONAL_AWNING_APPLIED_AND_READBACK_VERIFIED")
    print("Project: {}".format(getattr(project, "path", "")))
    print("Target: two source-identified south windows, 6.0 m2 each")
    print("Writable fields: active, OFF/NONE profile, transmittance 0.04, 150/150 W/m2")
    print("Report: {}".format(report))
    print("Project saved by script: NO")
    print("NEXT: save the project manually, then send this complete output.")
    print(
        "This is not yet a Test 1 PASS: unavailable reflectance setters, APS "
        "equivalence and independent template review remain fail-closed."
    )
    return report


if __name__ == "__main__":
    run()
