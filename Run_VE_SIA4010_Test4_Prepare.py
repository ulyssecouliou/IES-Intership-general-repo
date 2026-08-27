"""Prepare the exact official SIA 4010 Test 4 scenario, read-only for VE.

This dedicated launcher avoids relying on the editable ``CASE`` default in
the reusable scenario-preparation script.  It deliberately replaces a stale
scenario in the active disposable project, prepares ``test_4/4`` under class
3, and writes only the project-local evidence and scenario JSON files.  It
does not create, assign, mutate or save VE model objects.
"""

from __future__ import print_function

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run():
    """Delegate to the guarded generic preparer with fixed Test 4 inputs."""

    import Run_VE_SIA4010_Prepare_Case_Scenario as preparation

    preparation.CASE = "4"
    preparation.TARGET_CLASS = "3"
    preparation.ALLOW_SCENARIO_REPLACEMENT = True
    # Explicitly install the already reviewed project evidence (notably the
    # SIA 2028 Kloten weather).  The controller upgrades only an untouched
    # empty template and never overwrites a locally edited manifest.
    preparation.INSTALL_PREPARED_EXTERNAL_INPUTS = True
    preparation.EXPECTED_PROJECT_FOLDER = "SIA4010_TEST4_DISPOSABLE"
    return preparation.run()


if __name__ == "__main__":
    # Do not raise SystemExit: VEScripts displays it as an execution error.
    run()
