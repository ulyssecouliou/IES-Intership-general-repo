"""
Client launcher for the SIA 380/2-only compliance report.

Use this file from the IESVE Scripts window with the Run button. It runs the
same VE analysis as Run_VE_Swiss_Compliance.py but produces the client
SIA 380/2-only deliverable: the workbook omits every SIA 4010 sheet, card and
label (only the protective disclaimers and provenance citations remain), so the
software's SIA 4010 validation state can never be misread as a statement about
the client building.

For the full internal report (SIA 380/2 + SIA 4010 readiness), use
Run_VE_Swiss_Compliance.py instead.
"""

import os
import sys
import importlib

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


if __name__ == "__main__":
    # VE can keep the Python interpreter alive between Run clicks. Reload the
    # package app so every Run uses the latest workspace code.
    module_name = "swiss_sia.app"
    if module_name in sys.modules:
        app = importlib.reload(sys.modules[module_name])
    else:
        app = importlib.import_module(module_name)
    # Force the client SIA 380/2-only scope regardless of SIA_REPORT_SCOPE.
    app.main(include_sia4010=False)
