"""Apply the single bracketed Test 1E optical sensitivity point."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
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
    """Apply and read back the 0.21 bracketed sensitivity point."""

    _purge_cached_reference_model_modules()
    import iesve  # type: ignore

    from swiss_sia.reference_model.sia4010.test1e_awning_qualification import (
        apply_test1e_provisional_angular_diagnostic,
    )

    project = iesve.VEProject.get_current_project()
    report = apply_test1e_provisional_angular_diagnostic(
        iesve,
        project,
        angular_transmittance=0.21,
        diagnostic_label="BRACKETED_EQUIVALENT_OPTICS_SENSITIVITY_NOT_SOURCE_INPUT",
    )
    print(
        "SIA 4010 TEST 1E OPTICAL SENSITIVITY: "
        "BRACKETED_0P21_APPLIED_AND_READBACK_VERIFIED"
    )
    print("Project: {}".format(getattr(project, "path", "")))
    print("Direct transmittance: 0.21 at 0/15/30/45/60/75 degrees; 0 at 90 degrees")
    print("Report: {}".format(report))
    print("Project saved by script: NO")
    print("This is a bounded sensitivity test, not a source input or SIA PASS.")
    print("NEXT: Ctrl+S, close, reopen, then run Test1E Optical Readback.")
    return report


if __name__ == "__main__":
    run()
