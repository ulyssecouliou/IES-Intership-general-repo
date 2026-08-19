"""VEScripts launcher for controlled SIA 380/2 thermal-template remediation."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _reload(name: str):
    module = importlib.import_module(name)
    return importlib.reload(module)


def run() -> None:
    """Open the preview/apply UI for the active saved client-model copy."""

    try:
        import iesve  # type: ignore
    except Exception as exc:
        raise RuntimeError("Run this launcher inside IESVE VEScripts.") from exc

    project = iesve.VEProject.get_current_project()
    if not project:
        raise RuntimeError("Open a saved disposable project copy first.")
    project_path = str(getattr(project, "path", "") or "")
    if not project_path:
        raise RuntimeError("Save the active VE project copy before continuing.")
    try:
        model = project.models[0]
    except Exception as exc:
        raise RuntimeError("The active project has no usable real model.") from exc

    remediation = _reload("swiss_sia.client_template_remediation")
    interface = _reload("swiss_sia.client_template_remediation_ui")
    inventory = remediation.collect_inventory(project, model)
    print("SIA 380/2 APPROVED TEMPLATE REMEDIATION")
    print("Project copy: {}".format(project_path))
    print("Rooms available: {}".format(len(inventory["rooms"])))
    print("Thermal templates available: {}".format(len(inventory["templates"])))
    for template in inventory["templates"]:
        observations = template["review_observations"]
        print(
            "- {!r} | handle={} | gains={} | air exchanges={} | "
            "lighting={} | non-infiltration air={} | missing profiles={}".format(
                template["name"],
                template["handle"],
                len(template["casual_gains"]),
                len(template["air_exchanges"]),
                observations["lighting_gain_detected"],
                observations["non_infiltration_air_exchange_detected"],
                template["missing_profile_references"],
            )
        )
    print("No VE data changes until an immutable preview is explicitly applied.")
    interface.launch_client_template_remediation(
        iesve, project, model, project_path
    )
    print("Template-remediation window closed.")


if __name__ == "__main__":
    run()
