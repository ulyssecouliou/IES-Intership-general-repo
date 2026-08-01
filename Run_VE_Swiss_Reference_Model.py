"""IESVE Run-button launcher for the Swiss reference-model workflow.

Place a ``reference_model_config.json`` file in the active VE project folder.
No command-line arguments or manual model-editing steps are required.
"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# VE retains imported Python modules between Run-button executions.  Clear this
# workflow's modules so a compatibility fix is picked up without restarting VE.
for module_name in tuple(sys.modules):
    if module_name == "swiss_sia.reference_model" or module_name.startswith(
        "swiss_sia.reference_model."
    ):
        del sys.modules[module_name]

from swiss_sia.reference_model.config_loader import load_configuration
from swiss_sia.reference_model.ve_api import IesVeGateway
from swiss_sia.reference_model.workflow import ReferenceModelWorkflow


def run():
    """Execute the reference-model workflow in the active VE project."""

    gateway = IesVeGateway()
    config_path = gateway.project_path / "reference_model_config.json"
    parameters = load_configuration(config_path if config_path.is_file() else None)
    outcome = ReferenceModelWorkflow(parameters, gateway).run(dry_run=False)
    print(outcome.message)
    print("Status: {}".format(outcome.status.value))
    print("Audit report: {}".format(outcome.artifacts.report_json))
    return outcome


if __name__ == "__main__":
    run()
