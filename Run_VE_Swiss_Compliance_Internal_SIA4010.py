"""
Internal launcher for the full SIA 380/2 + SIA 4010 report.

Use this file from the IESVE Scripts window with the Run button ONLY for the
internal deliverable that also carries the SIA 4010 validation-class readiness
of the toolchain. This report is NOT for a client: the SIA 4010 volet reports
the software's own validation state, never a statement about the client
building.

For the default client SIA 380/2-only deliverable, use
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
    # Force the full internal SIA 380/2 + SIA 4010 scope regardless of
    # SIA_REPORT_SCOPE.
    app.main(include_sia4010=True)
