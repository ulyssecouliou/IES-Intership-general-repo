"""IESVE Run-button launcher for the read-only SIA 4010 Test 3 probe."""

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run():
    """Inspect lighting, template and sensor APIs without changing VE."""

    try:
        import iesve  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Run this script from the IESVE VEScripts editor."
        ) from exc

    from swiss_sia.reference_model.sia4010.test3_runtime_capability import (
        write_test3_runtime_capability_report,
    )

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("Open a saved disposable VE project first.")
    project_path = Path(str(project.path))
    if not project_path.is_dir():
        raise RuntimeError(
            "Save the disposable VE project before running this probe."
        )
    report_path = write_test3_runtime_capability_report(
        iesve,
        project,
        PROJECT_ROOT,
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    print(
        "READ-ONLY SIA 4010 TEST 3 RUNTIME CAPABILITY: {}".format(
            payload["status"]
        )
    )
    print("Project: {}".format(payload["project"]["name"]))
    print(
        "Scenario: {}/{}".format(
            payload["scenario"]["variant"],
            payload["scenario"]["case_id"],
        )
    )
    print(
        "Lighting fields observed: {}".format(
            len(payload["observed_lighting_fields"])
        )
    )
    print(
        "Sensor-related members observed: {}".format(
            len(payload["sensor_related_members"])
        )
    )
    print(
        "Exact Test 3 variants audited: {}".format(
            len(payload["variant_capability_matrix"])
        )
    )
    print("Report: {}".format(report_path))
    print("No VE model or project data was changed.")
    return str(report_path)


if __name__ == "__main__":
    run()
