"""Run-button, read-only APS probe for SIA 4010 Tests 1 and 2."""

import json
import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# The VE Scripts process persists imported modules between Run-button
# executions. Purge the project package so probe-filter and ResultsReader
# contract updates are always loaded from the current source files.
for module_name in tuple(sys.modules):
    if module_name == "swiss_sia.reference_model" or module_name.startswith(
        "swiss_sia.reference_model."
    ):
        del sys.modules[module_name]


def run():
    """Inspect the newest APS file and write a source-review report."""

    import iesve

    from swiss_sia.reference_model.sia4010.aps_probe import (
        build_surface_inventory,
        inspect_results_reader,
    )
    from swiss_sia.simulation_results import list_aps_files, open_results_reader

    project = iesve.VEProject.get_current_project()
    aps_files = list_aps_files(project)
    if not aps_files:
        print("SIA 4010 APS PROBE: BLOCKED")
        print("No APS file was found in the active project's Vista folder.")
        return None

    vista = os.path.join(str(project.path), "Vista")
    aps_file = max(
        aps_files,
        key=lambda name: os.path.getmtime(os.path.join(vista, name)),
    )
    results_file = open_results_reader(aps_file)
    surface_inventory = build_surface_inventory(project)
    report = inspect_results_reader(
        results_file,
        aps_file,
        surface_inventory=surface_inventory,
    )
    report["project_name"] = str(getattr(project, "name", "") or "")
    report["project_path"] = str(getattr(project, "path", "") or "")

    output_dir = os.path.join(
        str(project.path), "sia4010_artifacts", "diagnostics"
    )
    os.makedirs(output_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(
        output_dir, "sia4010_aps_probe_{}.json".format(stamp)
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False, default=str)

    print("READ-ONLY SIA 4010 APS PROBE: {}".format(report["status"]))
    print("Project: {}".format(report["project_name"]))
    print("APS file: {}".format(aps_file))
    print("Rooms: {}".format(report["room_count"]))
    print("Candidate variables: {}".format(report["candidate_variable_count"]))
    print(
        "Surface series: {} ({})".format(
            report["surface_series_count"],
            report["surface_binding_status"],
        )
    )
    print("Report: {}".format(output_path))
    print("No VE model or APS data was changed.")
    return output_path


if __name__ == "__main__":
    run()
