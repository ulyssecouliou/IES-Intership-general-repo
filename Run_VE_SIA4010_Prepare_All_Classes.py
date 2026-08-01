"""Prepare all SIA 4010 validation classes without mutating the VE model.

This launcher is the non-graphical fallback for the native interface button
``Prepare all 8 classes``. It verifies the official package once, writes the
source-traced case/class indexes into the active project and reports every
unresolved input or generator capability fail-closed.
"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# VE Scripts persists Python imports between runs. Reload the current
# implementation so an operator never executes a stale preparation contract.
for module_name in tuple(sys.modules):
    if module_name == "swiss_sia.reference_model" or module_name.startswith(
        "swiss_sia.reference_model."
    ):
        del sys.modules[module_name]


def run():
    """Write the complete eight-class preparation index into the VE project."""

    from swiss_sia.reference_model.sia4010.preparation_bundle import (
        prepare_all_classes,
    )
    from swiss_sia.reference_model.ve_api import IesVeGateway

    gateway = IesVeGateway()
    receipt = prepare_all_classes(gateway.project_path, PROJECT_ROOT)
    print("SIA 4010 ALL-CLASSES PREPARATION: {}".format(receipt.status))
    print("Project: {}".format(gateway.project_name))
    print("Validation classes: {}".format(len(receipt.classes)))
    print("Unique exact cases: {}".format(receipt.unique_exact_cases))
    print(
        "Unique deterministic gbXML cases: {}".format(
            receipt.unique_geometry_artifact_cases
        )
    )
    print(
        "Blocked class-case occurrences: {}".format(
            receipt.blocked_occurrences
        )
    )
    print("Report: {}".format(receipt.audit_path))
    print("No VE model, workbook, APS or weather data was changed.")
    return receipt


if __name__ == "__main__":
    run()
