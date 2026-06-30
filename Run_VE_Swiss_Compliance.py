"""
Client launcher for the Swiss SIA compliance checker.

Use this file from the IESVE Scripts window with the Run button.
It delegates to main.py so the production workflow has one clear entry point
without requiring PowerShell or command-line arguments.
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
