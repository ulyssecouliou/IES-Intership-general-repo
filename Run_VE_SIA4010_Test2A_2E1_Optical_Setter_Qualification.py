"""IESVE launcher for the guarded Test 2A diagnostic 2E1 optical probe."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

for module_name in tuple(sys.modules):
    if module_name == "swiss_sia.reference_model" or module_name.startswith(
        "swiss_sia.reference_model."
    ):
        del sys.modules[module_name]


def run():
    """Qualify fixed-shade fields and rebuild the immutable Test 2A bundle."""

    from swiss_sia.reference_model.sia4010.test2a_optical_workflow import (
        run_test2a_2e1_optical_workflow,
    )
    from swiss_sia.reference_model.ve_api import IesVeGateway

    gateway = IesVeGateway()
    receipt = run_test2a_2e1_optical_workflow(
        gateway.iesve,
        gateway.project,
        gateway.project_path,
        PROJECT_ROOT,
    )
    print("CONTROLLED TEST 2A 2E1 WRITABLE OPTICAL SUBSET: PASS")
    print("Project: {}".format(gateway.project.name))
    print("Report: {}".format(receipt.report_path))
    print(
        "Rebuilt Test 2A bundle status: {}".format(
            receipt.bundle_status
        )
    )
    print("Bundle audit: {}".format(receipt.bundle_audit_path))
    print(
        "Only the VE 2025 documented writable fixed-closed CDB subset was "
        "qualified: active state, ON profile, normal-incidence transmittance "
        "and the two threshold expressions."
    )
    print(
        "The threshold control and IESVE field mapping are authority-confirmed. "
        "External-shade solar/visible reflectance setters are unavailable; "
        "angular optics, secondary heat transfer and APS equivalence also "
        "remain fail-closed."
    )
    return receipt.to_dict()


if __name__ == "__main__":
    run()
