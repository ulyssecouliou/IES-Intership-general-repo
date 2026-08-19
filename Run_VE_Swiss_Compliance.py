"""
Client launcher for the Swiss SIA 380/2 compliance checker.

Use this file from the IESVE Scripts window with the Run button. It is the
default client deliverable: an SIA 380/2-only report. SIA 4010 validation
classes qualify the toolchain, not a client building, so they never appear
here (only the protective disclaimers and provenance citations remain).

For the full internal report (SIA 380/2 + SIA 4010 readiness), use
Run_VE_Swiss_Compliance_Internal_SIA4010.py instead.
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
    app.main()
