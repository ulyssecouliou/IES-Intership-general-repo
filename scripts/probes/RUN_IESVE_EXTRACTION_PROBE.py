"""
Run-button launcher for IESVE.

Open this file in VE Scripts and click Run. No PowerShell or arguments needed.
The diagnostic JSON will be written to the local reports folder.
"""

import importlib
import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from scripts.probes import iesve_extraction_probe


def main() -> str:
    """Run the IESVE extraction probe with default limits and print the output path."""
    probe_module = importlib.reload(iesve_extraction_probe)
    output_path = probe_module.run_with_defaults()
    print(f"IESVE extraction probe written to: {output_path}")
    print(f"Probe schema version: {probe_module.PROBE_SCHEMA_VERSION}")
    return str(output_path)


if __name__ == "__main__":
    main()
