"""Apply the guarded, explicitly provisional Test 1E angular diagnostic."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))


def _purge_cached_reference_model_modules():
    for module_name in tuple(sys.modules):
        if module_name == "swiss_sia.reference_model" or module_name.startswith(
            "swiss_sia.reference_model."
        ):
            del sys.modules[module_name]


def run():
    """Write and verify only the VE-documented angular transmission fields."""

    _purge_cached_reference_model_modules()
    import iesve  # type: ignore

    from swiss_sia.reference_model.sia4010.test1e_awning_qualification import (
        apply_test1e_provisional_angular_diagnostic,
    )

    project = iesve.VEProject.get_current_project()
    report = apply_test1e_provisional_angular_diagnostic(iesve, project)
    print(
        "SIA 4010 TEST 1E ANGULAR OPTICS: "
        "PROVISIONAL_ANGULAR_DIAGNOSTIC_APPLIED_AND_READBACK_VERIFIED"
    )
    print("Project: {}".format(getattr(project, "path", "")))
    print("Direct transmittance: 0.04 at 0/15/30/45/60/75 degrees; 0 at 90 degrees")
    print("Report: {}".format(report))
    print("Project saved by script: NO")
    print("This is a diagnostic assumption, not an authority-confirmed Test 1 PASS.")
    print("NEXT: set solar reflectance 0.490 and visible reflectance 0.496 in APcdb.")
    print("Then save, close, reopen, and run Test1E Optical Readback.")
    return report


if __name__ == "__main__":
    run()
