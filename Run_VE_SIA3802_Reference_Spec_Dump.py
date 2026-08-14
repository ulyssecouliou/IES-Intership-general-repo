"""Build and dump the SIA 380/2 reference-project spec for the active VE project.

Open this file in the IESVE Scripts window with the target project active and
click Run. It runs the real extraction path (VEDataExtractor -> ModelAnalyzer),
builds the reference-project input specification and writes it as JSON beside the
active VE project, plus a readable per-substitution summary to the console. It
reads the model only; it creates and modifies nothing.

This is the reference-project specification on a real client model: every
substitution with its project value, reference limit and target, status and SIA
source -- so the reference-model builder (Phase B) knows exactly what to apply
and what still blocks a runnable reference run.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    """Extract the model, build the reference-project spec and dump it."""
    import importlib

    try:
        iesve = importlib.import_module("iesve")
    except Exception as exc:  # noqa: BLE001
        print("This script must run inside IESVE (iesve unavailable): %s" % exc)
        return

    from swiss_sia.data_extractor import VEDataExtractor
    from swiss_sia.model_analyzer import ModelAnalyzer
    from swiss_sia.reference_project import build_reference_project_specification

    project = iesve.VEProject.get_current_project()
    project_path = str(getattr(project, "path", "") or "")

    extractor = VEDataExtractor(project)
    analyzer = ModelAnalyzer(extractor)
    rooms = analyzer.analyze_all_rooms()
    spec = build_reference_project_specification(rooms, analyzer)
    payload = spec.to_dict()
    payload["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload["project_path"] = project_path
    payload["rooms_analysed"] = len(rooms)

    out_dir = Path(project_path).parent if project_path else PROJECT_ROOT
    out_path = out_dir / "sia3802_reference_spec.json"
    try:
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Wrote reference spec: %s" % out_path)
    except Exception as exc:  # noqa: BLE001
        print("Could not write JSON (%s); dumping to console:" % exc)
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    print("\n=== Reference-project specification (real model) ===")
    print("Status: %s | rooms: %s | substitutions: %s | blockers: %s"
          % (payload.get("status"), len(rooms),
             len(payload.get("substitutions", [])), len(payload.get("blockers", []))))
    print("\n%-34s %-12s %-10s %-10s %s" % ("parameter", "project", "ref(limit)", "target", "status"))
    for item in payload.get("substitutions", []):
        print("%-34s %-12s %-10s %-10s %s" % (
            str(item.get("parameter"))[:34],
            item.get("project_value"),
            item.get("reference_value"),
            item.get("reference_target_value"),
            item.get("status"),
        ))
    blockers = payload.get("blockers", [])
    if blockers:
        print("\n--- Blockers (%s) ---" % len(blockers))
        for blocker in blockers:
            print("  - %s" % blocker)


if __name__ == "__main__":
    main()
