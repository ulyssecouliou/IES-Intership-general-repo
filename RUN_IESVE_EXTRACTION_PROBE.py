"""
Run-button launcher for IESVE.

Open this file in VE Scripts and click Run. No PowerShell or arguments needed.
The diagnostic JSON will be written to the local reports folder.
"""

import importlib

import iesve_extraction_probe


iesve_extraction_probe = importlib.reload(iesve_extraction_probe)


output_path = iesve_extraction_probe.run_with_defaults()
print(f"IESVE extraction probe written to: {output_path}")
print(f"Probe schema version: {iesve_extraction_probe.PROBE_SCHEMA_VERSION}")
