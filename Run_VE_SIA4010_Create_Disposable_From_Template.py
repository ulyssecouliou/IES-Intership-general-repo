"""Copy a qualified SIA 4010 VE template to a new disposable project."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _request_inputs():
    import tkinter as tk
    from tkinter import filedialog, simpledialog

    root = tk.Tk()
    root.withdraw()
    try:
        case_key = simpledialog.askstring(
            "Projet jetable SIA 4010",
            "Cas exact (exemple: test_4/4)",
            parent=root,
        )
        if not case_key:
            return None, None
        destination = filedialog.askdirectory(
            title="Dossier parent du nouveau projet jetable",
            parent=root,
            mustexist=True,
        )
        return case_key, destination or None
    finally:
        root.destroy()


def run():
    """Create a verified copy; never overwrite an existing project."""

    from swiss_sia.reference_model.sia4010.template_strategy import (
        instantiate_qualified_case,
    )
    from swiss_sia.reference_model.ve_api import IesVeGateway

    gateway = IesVeGateway()
    case_key, destination = _request_inputs()
    if not case_key or not destination:
        print("SIA 4010 DISPOSABLE TEMPLATE COPY: CANCELLED")
        return None
    try:
        variant, case_id = (item.strip() for item in case_key.split("/", 1))
    except ValueError as exc:
        raise RuntimeError(
            "Use the exact form variant/case, for example test_4/4"
        ) from exc
    receipt = instantiate_qualified_case(
        gateway.project_path,
        PROJECT_ROOT,
        variant,
        case_id,
        destination,
    )
    print("SIA 4010 DISPOSABLE TEMPLATE COPY: {}".format(receipt.status))
    print("Case: {}/{}".format(receipt.variant, receipt.case_id))
    print("Template: {}".format(receipt.template_id))
    print("New VE project: {}".format(receipt.disposable_project))
    print("Audit: {}".format(receipt.report_path))
    print("Open the copied .mdl in VE before running any case mutation.")
    return receipt


if __name__ == "__main__":
    run()
