"""Prepare the exact fresh disposable VE project used by Test 2A probes."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

for module_name in tuple(sys.modules):
    if module_name == "swiss_sia.reference_model" or module_name.startswith(
        "swiss_sia.reference_model."
    ):
        del sys.modules[module_name]


def run():
    """Install the controlled Test 2A scenario and prepared evidence contract."""

    import Run_VE_SIA4010_Prepare_Case_Scenario as preparation

    preparation.CASE = "2A"
    preparation.TARGET_CLASS = "1A"
    preparation.ALLOW_SCENARIO_REPLACEMENT = False
    preparation.INSTALL_PREPARED_EXTERNAL_INPUTS = True
    preparation.EXPECTED_PROJECT_FOLDER = "SIA4010_TEST2A_DISPOSABLE_V3"
    return preparation.run()


if __name__ == "__main__":
    run()
