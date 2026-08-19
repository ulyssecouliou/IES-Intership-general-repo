"""VEScripts launcher for the source-traced SIA 2024 usage 4.01 template."""

from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _write(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return path


def run() -> None:
    """Review, create and read back the operational template in a VE copy."""

    try:
        import iesve  # type: ignore
        import tkinter as tk
        from tkinter import messagebox
    except Exception as exc:
        raise RuntimeError("Run this launcher inside IESVE VEScripts.") from exc

    source_module = importlib.reload(
        importlib.import_module("swiss_sia.sia3802_classroom_template")
    )
    # VE keeps imported Python modules alive for the whole application
    # session. Reload the version-sensitive provisioner before ve_api so the
    # gateway binds the current class rather than a stale pre-launch instance.
    importlib.reload(
        importlib.import_module("swiss_sia.reference_model.ve_asset_provisioner")
    )
    gateway_module = importlib.reload(
        importlib.import_module("swiss_sia.reference_model.ve_api")
    )
    hub_module = importlib.reload(importlib.import_module("swiss_sia.compliance_hub"))
    gateway = gateway_module.IesVeGateway(iesve)
    project_path = gateway.project_path.resolve()
    if not hub_module.is_disposable_project(str(project_path)):
        raise RuntimeError(
            "Open a saved project copy ending in _TEST, _COPY or _DISPOSABLE first."
        )

    plan, summary = source_module.build_classroom_operational_plan(PROJECT_ROOT)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = project_path / "sia_compliance_artifacts" / "template_provisioning"
    review_path = _write(
        folder / "sia2024_classroom_template_review_{}.json".format(stamp), summary
    )
    print("SIA 380/2 CLASSROOM REFERENCE TEMPLATE: READY_FOR_REVIEW")
    print("Project copy: {}".format(project_path))
    print("Template: {}".format(summary["template_name"]))
    print("SIA usage category: 4.01 Classroom")
    print("Profiles to create/verify: {}".format(summary["profile_count"]))
    print("Review artifact: {}".format(review_path))
    print("Automatic compliance claim: NO")

    root = tk.Tk()
    root.withdraw()
    approved = messagebox.askyesno(
        "Create SIA 2024 classroom reference template",
        (
            "This will create or strictly verify profiles, gains, air exchanges "
            "and one thermal template in the active disposable copy.\n\n"
            "Direct SIA values are source-traced. The people latent conversion, "
            "lighting schedule, ventilation schedule and constant design setpoint "
            "mapping remain REVIEW REQUIRED and actual project data take priority.\n\n"
            "No room will be changed and no compliance verdict will be granted.\n\n"
            "Create/verify the template now?"
        ),
        parent=root,
    )
    root.destroy()
    if not approved:
        print("SIA 380/2 CLASSROOM REFERENCE TEMPLATE: CANCELLED_NO_VE_CHANGE")
        return

    receipt = gateway.provision_operational_template(plan)
    result = {
        **summary,
        "status": receipt["status"],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project_path": str(project_path),
        "ve_receipt": receipt,
        "room_assignments_changed": False,
        "project_saved_by_script": False,
        "compliance_claim": "NOT_GRANTED",
        "next_action": (
            "Open Run_VE_SIA3802_Approved_Template_Remediation.py, select the "
            "new template and the intended classroom rooms, create a read-only "
            "preview, obtain independent project approval, then apply and rerun "
            "the read-only SIA 380/2 audit."
        ),
    }
    receipt_path = _write(
        folder / "sia2024_classroom_template_receipt_{}.json".format(stamp), result
    )
    print("SIA 380/2 CLASSROOM REFERENCE TEMPLATE: {}".format(receipt["status"]))
    print("Template handle: {}".format(receipt["template_handle"]))
    print("Receipt: {}".format(receipt_path))
    print("No room assignment was changed. Review before saving the VE copy.")


if __name__ == "__main__":
    run()
