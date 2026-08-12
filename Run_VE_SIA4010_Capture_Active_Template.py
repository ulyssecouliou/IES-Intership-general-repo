"""Capture a checksum candidate for the active VE project template."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _ask(prompt, title):
    import tkinter as tk
    from tkinter import simpledialog

    root = tk.Tk()
    root.withdraw()
    try:
        return simpledialog.askstring(title, prompt, parent=root)
    finally:
        root.destroy()


def run():
    """Capture the saved project; never mark it qualified automatically."""

    import iesve  # type: ignore

    from swiss_sia.reference_model.sia4010.template_strategy import (
        capture_template_candidate,
    )
    from swiss_sia.reference_model.ve_api import IesVeGateway

    gateway = IesVeGateway()
    cases_text = _ask(
        "Cas couverts, separes par des virgules (exemple: test_4/4)",
        "Capture template SIA 4010",
    )
    if not cases_text:
        print("SIA 4010 TEMPLATE CAPTURE: CANCELLED")
        return None
    operator = _ask("Nom de l'operateur", "Capture template SIA 4010")
    if not operator:
        print("SIA 4010 TEMPLATE CAPTURE: CANCELLED")
        return None
    version_getter = getattr(iesve, "get_version", None)
    ve_version = str(version_getter()) if callable(version_getter) else "VE_VERSION_NOT_EXPOSED"
    path = capture_template_candidate(
        gateway.project_path,
        (item.strip() for item in cases_text.split(",") if item.strip()),
        ve_version=ve_version,
        operator=operator,
    )
    print("SIA 4010 TEMPLATE CAPTURE: CANDIDATE_REQUIRES_INDEPENDENT_REVIEW")
    print("Project: {}".format(gateway.project_name))
    print("Candidate: {}".format(path))
    print("No VE model, system, weather or APS data was changed.")
    return path


if __name__ == "__main__":
    run()
