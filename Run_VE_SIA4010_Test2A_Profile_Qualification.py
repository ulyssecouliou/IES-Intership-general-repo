"""Qualify the source-bound Test 2A VE profile graph in a disposable project.

Run only after the read-only Test 2A runtime probe reports
``READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION``.  This script creates project
profiles and therefore must never be run in a production VE project.
"""

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

for module_name in tuple(sys.modules):
    if module_name == "swiss_sia.reference_model" or module_name.startswith(
        "swiss_sia.reference_model."
    ):
        del sys.modules[module_name]


def run():
    """Create and strictly read back only the Test 2A native profile graph."""

    from swiss_sia.reference_model.sia4010.test2a_profile_qualification import (
        qualify_test2a_profile_graph,
    )
    from swiss_sia.reference_model.ve_api import IesVeGateway

    gateway = IesVeGateway()
    report = qualify_test2a_profile_graph(
        gateway.iesve,
        gateway.project,
    )
    payload = json.loads(report.read_text(encoding="utf-8"))
    print("SIA 4010 TEST 2A PROFILE QUALIFICATION: {}".format(
        payload["status"]
    ))
    print("Project: {}".format(gateway.project.name))
    print("Created profiles: {}".format(
        payload.get("created_profile_count", 0)
    ))
    print("Output profile IDs: {}".format(
        payload.get("output_profile_ids", {})
    ))
    print("Report: {}".format(report))
    print(
        "No geometry, material, construction, template, gain, shading, "
        "weather or simulation data was changed."
    )
    return report


if __name__ == "__main__":
    run()
