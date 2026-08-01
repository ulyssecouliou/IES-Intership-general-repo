"""Fresh-entry launcher that bypasses the IESVE VEScripts module cache."""

import runpy
import sys
from pathlib import Path


CURRENT_LAUNCHER = (
    Path(__file__).resolve().parent
    / "Run_VE_SIA4010_Case600_One_Click.py"
)

if not CURRENT_LAUNCHER.is_file():
    raise RuntimeError(
        "Current Case 600 launcher is missing: {}".format(CURRENT_LAUNCHER)
    )

for module_name in (
    "Run_VE_Verify_Case600_Weather",
    "Run_VE_SIA_Model_Builder",
):
    sys.modules.pop(module_name, None)

runpy.run_path(str(CURRENT_LAUNCHER), run_name="__main__")
