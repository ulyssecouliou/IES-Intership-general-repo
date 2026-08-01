"""IESVE Run-button launcher for the read-only SIA 4010 Test 2A probe."""

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run():
    """Inspect Test 2A profile/shading APIs without changing the VE project."""

    try:
        import iesve  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Run this script from the IESVE VEScripts editor."
        ) from exc

    from swiss_sia.reference_model.sia4010.test2a_runtime_capability import (
        write_test2a_runtime_capability_report,
    )

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("Open a saved disposable VE project first.")
    project_path = Path(str(project.path))
    if not project_path.is_dir():
        raise RuntimeError(
            "Save the disposable VE project before running this probe."
        )
    report_path = write_test2a_runtime_capability_report(iesve, project)
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    print(
        "READ-ONLY SIA 4010 TEST 2A RUNTIME CAPABILITY: {}".format(
            payload["status"]
        )
    )
    print("Project: {}".format(payload["project"]["name"]))
    print(
        "Profiles inspected: {}".format(
            len(payload["profile_api"]["profiles"])
        )
    )
    print(
        "Glazed constructions inspected: {}".format(
            len(
                payload["glazed_construction_api"]["constructions"]
            )
        )
    )
    print(
        "Openings inspected: {}".format(
            len(payload["opening_api"]["openings"])
        )
    )
    print("Report: {}".format(report_path))
    print("No VE model or project data was changed.")
    return str(report_path)


if __name__ == "__main__":
    run()
