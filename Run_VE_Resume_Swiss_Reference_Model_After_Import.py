"""Resume the Swiss reference-model workflow after a successful gbXML import.

Use this launcher only when the earlier full run imported and validated the
generated rooms, then failed before completing construction/template/weather
assignments.  It validates and reuses the existing generated geometry and does
not import the gbXML again.
"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# VE retains imported Python modules between Run-button executions.  Clear this
# workflow's modules so this recovery launcher always uses the latest fixes.
for module_name in tuple(sys.modules):
    if module_name == "swiss_sia.reference_model" or module_name.startswith(
        "swiss_sia.reference_model."
    ):
        del sys.modules[module_name]

from swiss_sia.reference_model.config_loader import load_configuration
from swiss_sia.reference_model.ve_api import IesVeGateway
from swiss_sia.reference_model.workflow import ReferenceModelWorkflow


def run():
    """Continue assignments on the already imported deterministic geometry."""

    gateway = IesVeGateway()
    config_path = gateway.project_path / "reference_model_config.json"
    parameters = load_configuration(config_path if config_path.is_file() else None)
    outcome = ReferenceModelWorkflow(parameters, gateway).run(
        dry_run=False, resume_after_import=True
    )
    print(outcome.message)
    print("Status: {}".format(outcome.status.value))
    print("Audit report: {}".format(outcome.artifacts.report_json))
    return outcome


if __name__ == "__main__":
    run()
