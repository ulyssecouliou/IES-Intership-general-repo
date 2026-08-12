"""Run-button launcher for the read-only Swiss remediation probe.

Open the saved disposable VE project, select this file in VEScripts and press
Run.  The script writes diagnostic JSON/TXT artifacts but never mutates model
geometry, constructions, templates, systems, profiles or weather assignment.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _reload(module_name: str) -> Any:
    """Import and reload a module retained by the VE interpreter."""
    module = importlib.import_module(module_name)
    return importlib.reload(module)


def _atomic_write(path: Path, text: str) -> None:
    """Write one UTF-8 diagnostic artifact atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(str(temporary), str(path))


def _text_report(report: Dict[str, Any]) -> str:
    """Return a compact human-readable diagnosis."""
    lines = [
        "SWISS SIA READ-ONLY REMEDIATION PROBE",
        "Status: {}".format(report.get("status", "UNKNOWN")),
        "Project: {}".format(report.get("project_path", "")),
        "Rooms: {}".format(report.get("room_count", 0)),
        "",
        "CONTROLS",
    ]
    for control in report.get("controls", []):
        lines.append(
            "[{status}] {control_id} - {title}: {observed}".format(**control)
        )
        if control.get("status") != "PASS":
            lines.append("  Action: {}".format(control.get("action", "")))
            for item in control.get("affected_objects", []):
                lines.append("  Object: {}".format(json.dumps(item, ensure_ascii=False)))
    lines.extend(["", "NEXT ACTIONS"])
    for index, action in enumerate(report.get("next_actions", []), start=1):
        lines.append("{}. {}".format(index, action))
    lines.extend([
        "",
        str(report.get("guardrail", "")),
        "No VE model, construction, template, system, profile or weather data was changed.",
    ])
    return "\n".join(lines) + "\n"


def run() -> None:
    """Inspect the active saved VE project and emit deterministic diagnostics."""
    try:
        import iesve  # type: ignore
    except Exception as exc:
        raise RuntimeError("This script must be run inside IESVE VEScripts.") from exc

    data_extractor_module = _reload("swiss_sia.data_extractor")
    model_analyzer_module = _reload("swiss_sia.model_analyzer")
    app_module = _reload("swiss_sia.app")
    remediation_module = _reload("swiss_sia.remediation_probe")
    runtime_inventory_module = _reload("swiss_sia.runtime_inventory")
    simulation_results_module = _reload("swiss_sia.simulation_results")

    project = iesve.VEProject.get_current_project()
    if not project:
        raise RuntimeError("No active VE project found. Open the disposable project first.")
    project_path = str(getattr(project, "path", "") or "")
    if not project_path:
        raise RuntimeError("The active VE project must be saved before running the probe.")

    extractor = data_extractor_module.VEDataExtractor(project)
    analyzer = model_analyzer_module.ModelAnalyzer(extractor)
    rooms = analyzer.analyze_all_rooms()
    dynamic_results = app_module._collect_dynamic_results(project)
    app_module._attach_dynamic_results_to_rooms(rooms, dynamic_results)
    ve_runtime_inventory = (
        runtime_inventory_module.collect_model_runtime_inventory(extractor)
    )
    aps_runtime_inventory = (
        runtime_inventory_module.collect_aps_runtime_inventory(
            str(dynamic_results.get("selected_aps_file") or ""),
            simulation_results_module,
        )
    )
    diagnosis = remediation_module.build_remediation_diagnosis(
        rooms,
        dynamic_results,
        project_path,
        ve_runtime_inventory,
        aps_runtime_inventory,
    )
    report = diagnosis.to_dict()
    report["normalized_dynamic_results"] = runtime_inventory_module.json_safe(
        dynamic_results
    )
    report["ve_runtime_inventory"] = ve_runtime_inventory
    report["aps_runtime_inventory"] = aps_runtime_inventory

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(project_path) / "sia_compliance_artifacts" / "diagnostics"
    json_path = output_dir / "swiss_sia_remediation_probe_{}.json".format(timestamp)
    text_path = output_dir / "swiss_sia_remediation_probe_{}.txt".format(timestamp)
    _atomic_write(json_path, json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    _atomic_write(text_path, _text_report(report))

    print("SWISS SIA READ-ONLY REMEDIATION PROBE: {}".format(diagnosis.status))
    print("Project: {}".format(project_path))
    print("Rooms: {}".format(diagnosis.room_count))
    for control in diagnosis.controls:
        print("[{}] {} - {}".format(control.status, control.control_id, control.observed))
    print("JSON report: {}".format(json_path))
    print("Text report: {}".format(text_path))
    print("No VE model, construction, template, system, profile or weather data was changed.")


if __name__ == "__main__":
    run()
