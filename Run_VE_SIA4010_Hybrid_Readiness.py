"""VEScripts launcher: report direct and template-backed case readiness."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run():
    """Write a fail-closed readiness report for the active saved project."""

    from swiss_sia.reference_model.sia4010.template_strategy import (
        write_hybrid_readiness,
    )
    from swiss_sia.reference_model.ve_api import IesVeGateway

    gateway = IesVeGateway()
    receipt = write_hybrid_readiness(gateway.project_path, PROJECT_ROOT)
    print("SIA 4010 HYBRID EXECUTION READINESS: {}".format(receipt.status))
    print("Project: {}".format(gateway.project_name))
    print("Direct VEScripts cases: {}".format(receipt.direct_cases))
    print("Qualified-template cases: {}".format(receipt.template_cases))
    print("Blocked template cases: {}".format(receipt.blocked_cases))
    print("Report: {}".format(receipt.report_path))
    print("No VE model, template, system, weather or APS data was changed.")
    return receipt


if __name__ == "__main__":
    run()
