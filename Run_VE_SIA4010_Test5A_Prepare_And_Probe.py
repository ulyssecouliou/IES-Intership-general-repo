"""One-click source preparation and read-only runtime probe for SIA Test 5A."""

from __future__ import print_function

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run():
    """Prepare official test_5A/5A under class 3, then probe VE read-only."""

    import Run_VE_SIA4010_Prepare_Case_Scenario as preparation

    preparation.CASE = "5A"
    preparation.TARGET_CLASS = "3"
    preparation.ALLOW_SCENARIO_REPLACEMENT = True
    preparation.INSTALL_PREPARED_EXTERNAL_INPUTS = True
    preparation.EXPECTED_PROJECT_FOLDER = "SIA4010_TEST5A_DISPOSABLE"
    result = preparation.run()
    if result not in (None, 0):
        raise RuntimeError(
            "Test 5A preparation did not complete; capability probe was not run"
        )

    import Run_VE_SIA4010_Tests4_7_Runtime_Capability_Probe as probe

    return probe.run()


if __name__ == "__main__":
    run()
