"""READ-ONLY probe: which .aps is selected, and what room variables it exposes.

Run this file from the IESVE Scripts window with the Run button, on the active
project. It performs NO mutation and NO simulation: it lists the project's .aps
files (newest first), opens the newest readable one, and prints its weather,
timestep, and the full variable list. It then checks whether the variables the
compliance audit needs — room air temperature, occupancy, heating and cooling
loads — are actually present.

Use it to tell apart the two reasons SIA3802_HOURLY_TEMPERATURES /
SIA3802_HEATING_COOLING_DEMANDS stay NOT_CHECKABLE:
  - the .aps has no such series (the ApacheSim run did not output them / the rooms
    are not conditioned or occupied) -> re-run the simulation with those outputs;
  - the series exist under names the adapter does not match -> a binding fix.
"""

from __future__ import annotations

import importlib
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# What the audit looks for, as lower-case token groups (any group present = ok).
_WANTED = {
    "room air temperature": [["dry", "resultant", "temperature"], ["air", "temperature"], ["resultant", "temperature"]],
    "occupancy": [["occupancy"], ["people"], ["occupied"]],
    "heating load": [["heating", "load"], ["sensible", "heating"], ["heating"]],
    "cooling load": [["cooling", "load"], ["sensible", "cooling"], ["cooling"]],
}


def run() -> None:
    try:
        import iesve  # type: ignore  # noqa: F401
    except Exception as exc:
        raise RuntimeError("Run this launcher inside IESVE VEScripts.") from exc

    sim = importlib.reload(importlib.import_module("swiss_sia.simulation_results"))

    project = __import__("iesve").VEProject.get_current_project()
    if not project:
        raise RuntimeError("Open a project first.")

    aps_files = sim.list_aps_files(project)
    print("=" * 78)
    print("READ-ONLY APS VARIABLE PROBE (no mutation, no simulation)")
    print("=" * 78)
    print("Project weather label:", getattr(project, "path", ""))
    print("APS files in Vista folder:", aps_files or "[]")
    if not aps_files:
        print("No .aps file found. Run ApacheSim on THIS project first.")
        print("=" * 78)
        return

    # Newest by modification time.
    def _mtime(name):
        try:
            return os.path.getmtime(sim.get_aps_path(project, name))
        except Exception:
            return 0.0
    newest = sorted(aps_files, key=_mtime, reverse=True)[0]
    path = sim.get_aps_path(project, newest)
    print("Newest .aps:", newest)
    print("  path:", path)
    print("  EPW references in bytes:", sim.extract_epw_references_from_aps(path))

    reader = sim.open_results_reader(newest)
    try:
        print("  reader weather_file:", getattr(reader, "weather_file", ""))
        try:
            print("  results_per_hour:", sim.get_results_per_hour(reader))
        except Exception as exc:
            print("  results_per_hour: <error>", exc)
        variables = sim.get_available_variables(reader)
        print("  variable count:", len(variables))
        print("\n--- ALL VARIABLES (aps_varname | display_name | units) ---")
        for v in variables:
            print("   {} | {} | {}".format(
                v.get("aps_varname"), v.get("display_name"),
                v.get("resolved_metric_unit") or v.get("units_type")))
        print("\n--- WHAT THE AUDIT NEEDS ---")
        for label, groups in _WANTED.items():
            hit = None
            for tokens in groups:
                m = sim.find_aps_variable(variables, tokens)
                if m:
                    hit = (tokens, m.get("aps_varname") or m.get("display_name"))
                    break
            print("  {:24s}: {}".format(
                label, ("FOUND via {} -> {}".format(hit[0], hit[1]) if hit else "NOT FOUND")))
    finally:
        try:
            reader.close()
        except Exception:
            pass
    print("=" * 78)


if __name__ == "__main__":
    run()
