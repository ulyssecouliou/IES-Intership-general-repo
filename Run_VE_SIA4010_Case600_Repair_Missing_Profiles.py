"""One-click repair for Case 600 models referencing missing DAY_* profiles.

Run from VEScripts with the affected, already-imported Case 600 project open.
"""

import importlib
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

MODULE = "Run_VE_SIA4010_Case600_Resume_After_Template_Fix"
if MODULE in sys.modules:
    del sys.modules[MODULE]
repair = importlib.import_module(MODULE)


def run():
    """Run the guarded portable-profile repair and controlled resume."""

    return repair.run()


if __name__ == "__main__":
    run()
