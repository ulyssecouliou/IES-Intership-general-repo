"""IESVE Run-button launcher for the guarded Test 2A shade setter probe."""

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
    """Run the one-object setter probe against the active saved VE project."""

    from swiss_sia.reference_model.sia4010.test2a_shading_qualification import (
        qualify_test2a_shading_setters,
    )
    from swiss_sia.reference_model.ve_api import IesVeGateway

    gateway = IesVeGateway()
    report = qualify_test2a_shading_setters(
        gateway.iesve,
        gateway.project,
        repository_root=PROJECT_ROOT,
    )
    print("CONTROLLED TEST 2A SHADING SETTER QUALIFICATION: PASS")
    print("Project: {}".format(gateway.project.name))
    print("Report: {}".format(report))
    print(
        "No geometry, opening assignment, layer, optical mapping, template, "
        "weather or simulation was changed."
    )
    print(
        "Dynamic equality/timestep/optical equivalence remains fail-closed."
    )
    return report


if __name__ == "__main__":
    run()
