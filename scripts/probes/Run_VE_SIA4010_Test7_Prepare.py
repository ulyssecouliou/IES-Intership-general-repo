"""Prepare the exact official SIA 4010 Test 7 scenario, read-only for VE.

The launcher fixes the case to ``test_7/7`` under validation class 5 and opts
into the reviewed repository evidence manifest.  It writes project-local
scenario/evidence JSON only; it does not create, assign, mutate or save VE
model objects.
"""

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
    """Delegate to the guarded generic preparer with fixed Test 7 inputs."""

    import Run_VE_SIA4010_Prepare_Case_Scenario as preparation

    preparation.CASE = "7"
    preparation.TARGET_CLASS = "5"
    preparation.ALLOW_SCENARIO_REPLACEMENT = True
    preparation.INSTALL_PREPARED_EXTERNAL_INPUTS = True
    preparation.EXPECTED_PROJECT_FOLDER = "SIA4010_TEST7_DISPOSABLE"
    return preparation.run()


if __name__ == "__main__":
    # Do not raise SystemExit: VEScripts displays it as an execution error.
    run()
