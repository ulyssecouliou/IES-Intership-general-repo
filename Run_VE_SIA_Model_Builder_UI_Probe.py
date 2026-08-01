"""Read-only Tk/ttk compatibility probe for the embedded IESVE Python."""

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run():
    """Verify native UI availability without starting a mainloop or changing VE."""

    import iesve

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("No active IESVE project")
    project_path = Path(project.path)
    checks = {}
    error = None
    root = None
    try:
        import tkinter as tk
        from tkinter import messagebox, ttk

        checks["tkinter_import"] = True
        checks["ttk_import"] = ttk is not None
        checks["messagebox_import"] = messagebox is not None
        root = tk.Tk()
        root.withdraw()
        checks["tk_root"] = True
        checks["tk_version"] = str(root.tk.call("info", "patchlevel"))
        style = ttk.Style(root)
        checks["ttk_themes"] = list(style.theme_names())
        checks["topmost_supported"] = True
        try:
            root.attributes("-topmost", True)
        except tk.TclError:
            checks["topmost_supported"] = False
    except Exception as exc:
        error = "{}: {}".format(type(exc).__name__, exc)
    finally:
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass

    ready = bool(
        checks.get("tkinter_import")
        and checks.get("ttk_import")
        and checks.get("tk_root")
    )
    from swiss_sia.reference_model.sia4010.case_registry import (
        all_case_capabilities,
    )

    capabilities = all_case_capabilities()
    checks["registered_exact_cases"] = len(capabilities)
    checks["runtime_generator_probe_cases"] = [
        "{}/{}".format(item.variant, item.case_id)
        for item in capabilities
        if item.runtime_qualification_supported
    ]
    checks["guarded_apachesim_cases"] = [
        "{}/{}".format(item.variant, item.case_id)
        for item in capabilities
        if item.apachesim_qualification_supported
    ]
    apachesim_methods = {}
    try:
        simulator = iesve.ApacheSim()
        apachesim_methods = {
            method: callable(getattr(simulator, method, None))
            for method in ("get_options", "set_options", "run_simulation")
        }
    except Exception as exc:
        apachesim_methods = {
            "construction_error": "{}: {}".format(type(exc).__name__, exc)
        }
    checks["apachesim_methods"] = apachesim_methods
    checks["apachesim_api_ready"] = bool(
        apachesim_methods
        and all(
            apachesim_methods.get(method) is True
            for method in ("get_options", "set_options", "run_simulation")
        )
    )
    report = {
        "status": "READY" if ready else "BLOCKED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": getattr(project, "name", project_path.name),
        "project_path": str(project_path),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "checks": checks,
        "error": error,
        "mutation": "NONE",
    }
    output = project_path / "sia4010_artifacts" / "diagnostics"
    output.mkdir(parents=True, exist_ok=True)
    path = output / "sia_model_builder_ui_probe.json"
    path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("SIA MODEL BUILDER UI PROBE: {}".format(report["status"]))
    print("Project: {}".format(report["project"]))
    print("Python: {}".format(report["python_version"]))
    print(
        "Runtime generator probes: {}".format(
            len(checks["runtime_generator_probe_cases"])
        )
    )
    print(
        "Guarded ApacheSim cases: {}".format(
            len(checks["guarded_apachesim_cases"])
        )
    )
    print(
        "ApacheSim API: {}".format(
            "READY" if checks["apachesim_api_ready"] else "BLOCKED"
        )
    )
    print("Report: {}".format(path))
    print("No VE model data was changed.")
    return report


if __name__ == "__main__":
    run()
