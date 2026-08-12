"""IESVE Run-button launcher for the unified Swiss Compliance Hub."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# VEScripts keeps one Python interpreter alive between Run clicks. Reload the
# hub registry so launcher changes are effective without restarting VE.
for module_name in tuple(sys.modules):
    if module_name in {
        "swiss_sia.compliance_hub",
        "swiss_sia.compliance_hub_ui",
    }:
        del sys.modules[module_name]


def _execute_launcher(filename: str) -> None:
    """Execute one existing Run-button launcher in the current VE interpreter."""
    path = (PROJECT_ROOT / filename).resolve()
    if path.parent != PROJECT_ROOT or not path.is_file():
        raise RuntimeError("Hub launcher is missing or outside the repository: {}".format(path))
    runpy.run_path(str(path), run_name="__main__")


def run() -> None:
    """Open the hub for the active saved VE project."""
    try:
        import iesve  # type: ignore
    except Exception as exc:
        raise RuntimeError("Run this launcher inside IESVE VEScripts.") from exc

    project = iesve.VEProject.get_current_project()
    project_path = str(getattr(project, "path", "") or "") if project else ""
    if not project_path:
        raise RuntimeError("Open and save a VE project before launching the hub.")

    from swiss_sia.compliance_hub import build_capability_summary
    from swiss_sia.compliance_hub_ui import launch_hub
    from swiss_sia.reference_model.sia4010.case_registry import all_case_capabilities

    capabilities = build_capability_summary(all_case_capabilities())
    launch_hub(project_path, capabilities, _execute_launcher)


if __name__ == "__main__":
    run()
