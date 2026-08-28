"""One-click source synchronization and read-only capability probe for Test 7."""

from __future__ import print_function

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)


def run():
    """Prepare test_7/7 first, then run the read-only Tests 4-7 probe."""

    import Run_VE_SIA4010_Test7_Prepare as preparation

    result = preparation.run()
    if result not in (None, 0):
        raise RuntimeError(
            "Test 7 preparation did not complete; capability probe was not run"
        )

    # VEScripts keeps modules cached between runs.  Import only after the
    # preparer has synchronized the project-local manifest and scenario.
    import Run_VE_SIA4010_Tests4_7_Runtime_Capability_Probe as probe

    return probe.run()


if __name__ == "__main__":
    run()
