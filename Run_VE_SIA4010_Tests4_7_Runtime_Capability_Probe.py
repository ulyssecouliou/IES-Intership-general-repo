"""IESVE Run-button launcher for the read-only Tests 4-7 runtime probe."""

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run():
    """Inspect HVAC and plant API evidence without changing VE."""

    try:
        import iesve  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Run this script from the IESVE VEScripts editor."
        ) from exc

    from swiss_sia.reference_model.sia4010.hvac_plant_runtime_capability import (
        write_hvac_plant_runtime_capability_report,
    )

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("Open a saved disposable VE project first.")
    project_path = Path(str(project.path))
    if not project_path.is_dir():
        raise RuntimeError(
            "Save the disposable VE project before running this probe."
        )
    report_path = write_hvac_plant_runtime_capability_report(
        iesve, project, PROJECT_ROOT
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    observed = payload["observed_capabilities"]
    print(
        "READ-ONLY SIA 4010 TESTS 4-7 RUNTIME CAPABILITY: {}".format(
            payload["status"]
        )
    )
    print("Project: {}".format(payload["project"]["name"]))
    print(
        "Scenario: {}/{}".format(
            payload["scenario"]["selection"]["variant"],
            payload["scenario"]["selection"]["case_id"],
        )
    )
    print(
        "Apache system collection observed: {}".format(
            observed["apache_system_collection"]
        )
    )
    print(
        "Room system read-back observed: {}".format(
            observed["room_apache_system_readback"]
        )
    )
    print(
        "Plant-specific members observed: {}".format(
            len(observed["plant_specific_members"])
        )
    )
    print(
        "Exact Tests 4-7 cases audited: {}".format(
            len(payload["case_capability_matrix"])
        )
    )
    print("Report: {}".format(report_path))
    print("No VE model or project data was changed.")
    return str(report_path)


if __name__ == "__main__":
    run()
