"""READ-ONLY probe for the per-project operable-window strategy.

Run this file from the IESVE VEScripts window while the target client model is
open.  It reads the saved building strategy, MacroFlo definitions and external
window assignments.  It never calls ``VEMacroFlo.set`` or any project-saving
method.  The JSON result is the evidence needed to design a guarded setter
without guessing the Boost.Python payload accepted by VE 2025.
"""

from __future__ import annotations

import importlib
import inspect
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

OUTPUT_PATH = PROJECT_ROOT / "outputs" / "sia3802_macroflo_strategy_probe.json"


def _native(value: Any) -> Any:
    """Convert Boost.Python containers and enums to JSON-compatible values."""

    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(key): _native(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_native(item) for item in value]
    try:
        return [_native(item) for item in list(value)]
    except Exception:
        return str(value)


def _callable_contract(value: Any) -> Dict[str, Any]:
    """Return all introspection VE exposes for one callable, without invoking it."""

    result = {
        "callable": callable(value),
        "python_type": str(type(value)),
        "doc": str(getattr(value, "__doc__", "") or ""),
    }
    try:
        result["signature"] = str(inspect.signature(value))
    except Exception as exc:
        result["signature_error"] = "{}: {}".format(type(exc).__name__, exc)
    return result


def _strategy_status(
    window_declaration: str,
    external_windows: Iterable[Dict[str, Any]],
    definitions: Any,
) -> str:
    """Classify readiness without interpreting an unknown MacroFlo payload."""

    windows = list(external_windows)
    assigned = [item for item in windows if str(item.get("macroflo_id") or "")]
    if str(window_declaration or "").upper() != "YES":
        return "OPERABLE_WINDOWS_NOT_DECLARED"
    if not windows:
        return "NO_EXTERNAL_WINDOWS_FOUND"
    if not assigned:
        return "MISSING_MACROFLO_ASSIGNMENTS"
    if not definitions:
        return "ASSIGNMENTS_PRESENT_DEFINITIONS_UNREADABLE"
    return "MACROFLO_ASSIGNMENTS_PRESENT_REVIEW_PAYLOAD"


def main() -> None:
    """Read the active model and write a mutation-free MacroFlo diagnostic."""

    import iesve  # type: ignore

    context_module = importlib.import_module("swiss_sia.client_report_context")
    context_module = importlib.reload(context_module)
    extractor_module = importlib.import_module("swiss_sia.data_extractor")
    extractor_module = importlib.reload(extractor_module)
    analyzer_module = importlib.import_module("swiss_sia.model_analyzer")
    analyzer_module = importlib.reload(analyzer_module)

    project = iesve.VEProject.get_current_project()
    if project is None or not str(getattr(project, "path", "") or ""):
        raise RuntimeError("Open and save the target VE project before running this probe.")

    project_path = Path(str(project.path))
    context = context_module.load_client_report_context(project_path)
    macroflo_class = getattr(iesve, "VEMacroFlo", None)
    project_getter = getattr(project, "get_macro_flo_opening_types", None)
    definitions_error = ""
    try:
        opening_types = list(project_getter()) if callable(project_getter) else []
    except Exception as exc:
        opening_types = []
        definitions_error = "{}: {}".format(type(exc).__name__, exc)

    definitions = []
    for index, opening_type in enumerate(opening_types):
        get_method = getattr(opening_type, "get", None)
        set_method = getattr(opening_type, "set", None)
        read_error = ""
        try:
            data = _native(get_method()) if callable(get_method) else None
        except Exception as exc:
            data = None
            read_error = "{}: {}".format(type(exc).__name__, exc)
        definitions.append({
            "index": index,
            "python_type": str(type(opening_type)),
            "public_members": sorted(
                name for name in dir(opening_type) if not name.startswith("_")
            ),
            "get": _callable_contract(get_method),
            "set": _callable_contract(set_method),
            "data": data,
            "read_error": read_error,
        })

    extractor = extractor_module.VEDataExtractor(project)
    rooms = analyzer_module.ModelAnalyzer(extractor).analyze_all_rooms()
    window_rows: List[Dict[str, Any]] = []
    for room in rooms:
        for opening in list(getattr(room, "openings", []) or []):
            if not bool(getattr(opening, "is_external", False)):
                continue
            opening_type = str(getattr(opening, "opening_type", "") or "").lower()
            if "window" not in opening_type and "glaz" not in opening_type:
                continue
            window_rows.append({
                "room_id": str(getattr(room, "id", "") or ""),
                "room_name": str(getattr(room, "name", "") or ""),
                "opening_id": str(getattr(opening, "id", "") or ""),
                "opening_name": str(getattr(opening, "name", "") or ""),
                "opening_type": str(getattr(opening, "opening_type", "") or ""),
                "area_m2": getattr(opening, "area", None),
                "macroflo_id": str(getattr(opening, "macroflo_id", "") or ""),
            })

    report = {
        "schema_version": 1,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "Read-only MacroFlo strategy and API contract probe",
        "project_path": str(project_path),
        "building_strategy": context.to_dict(),
        "api": {
            "vemacroflo_class_type": str(type(macroflo_class)),
            "vemacroflo_public_members": sorted(
                name for name in dir(macroflo_class) if not name.startswith("_")
            ),
            "project_get_macro_flo_opening_types": _callable_contract(
                project_getter
            ),
            "official_installed_example": str(
                Path(iesve.__file__).resolve().parents[2]
                / "apps"
                / "Scripts"
                / "api_examples"
                / "vemacroflo"
                / "macroflo.py"
            ) if getattr(iesve, "__file__", None) else "",
        },
        "definitions": definitions,
        "definitions_read_error": definitions_error,
        "external_windows": window_rows,
        "summary": {
            "strategy_status": _strategy_status(
                context.window_operability, window_rows, definitions
            ),
            "external_window_count": len(window_rows),
            "assigned_macroflo_count": sum(
                1 for item in window_rows if item.get("macroflo_id")
            ),
            "mutation_performed": False,
            "project_saved": False,
        },
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    print("=" * 78)
    print("SIA 380/2 MACROFLO STRATEGY PROBE - READ ONLY")
    print("Project:", project_path)
    print("Declared operable windows:", context.window_operability)
    print("External windows:", len(window_rows))
    print("MacroFlo opening types:", len(definitions))
    print("MacroFlo assignments:", report["summary"]["assigned_macroflo_count"])
    print("Status:", report["summary"]["strategy_status"])
    print("No VE value was changed and the project was not saved.")
    print("JSON:", OUTPUT_PATH)
    print("=" * 78)


if __name__ == "__main__":
    main()
