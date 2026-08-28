"""Fresh EPW-enabled Case 600 launcher for the IESVE Scripts Run button."""

import runpy
import sys
from pathlib import Path


_SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = _SCRIPT_DIR.parent.parent
CURRENT_LAUNCHER = (
    _SCRIPT_DIR / "Run_VE_SIA4010_Case600_One_Click.py"
)
if not CURRENT_LAUNCHER.is_file():
    raise RuntimeError(
        "Current Case 600 launcher is missing: {}".format(CURRENT_LAUNCHER)
    )

# VEScripts retains imported modules between Run-button executions.  Purging
# only our project namespace ensures the updated EPW path and validation logic
# are loaded from disk without restarting VE.
for module_name in tuple(sys.modules):
    if (
        module_name
        in {
            "Run_VE_Verify_Case600_Weather",
            "Run_VE_SIA_Model_Builder",
        }
        or module_name == "swiss_sia.reference_model"
        or module_name.startswith("swiss_sia.reference_model.")
    ):
        sys.modules.pop(module_name, None)

runpy.run_path(str(CURRENT_LAUNCHER), run_name="__main__")
