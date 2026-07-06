"""Run-button helper that prepares project-specific SIA evidence CSV files.

Use this from the IESVE Scripts window when the reviewer needs the CSV
templates in ``sia4010_evidence/`` but cannot use PowerShell.
"""

import importlib
import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


if __name__ == "__main__":
    module_name = "swiss_sia.evidence_bootstrap"
    if module_name in sys.modules:
        evidence_bootstrap = importlib.reload(sys.modules[module_name])
    else:
        evidence_bootstrap = importlib.import_module(module_name)

    result = evidence_bootstrap.prepare_evidence_folder()
    evidence_bootstrap.print_preparation_summary(result)
