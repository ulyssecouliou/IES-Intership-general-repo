"""Read-only qualification of the VE 2025 weekly-profile runtime contract."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import iesve


def _items(collection: Any) -> Iterable[Tuple[Any, Any]]:
    if isinstance(collection, dict):
        return collection.items()
    return enumerate(collection or ())


def _call_bool(profile: Any, name: str) -> Any:
    method = getattr(profile, name, None)
    if not callable(method):
        return None
    try:
        return bool(method())
    except Exception as exc:  # pragma: no cover - VE runtime diagnostic
        return "ERROR: {}".format(exc)


def _safe_text(value: Any) -> str:
    try:
        return str(value)
    except Exception as exc:  # pragma: no cover - VE runtime diagnostic
        return "<unreadable: {}>".format(exc)


def run() -> None:
    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("No active VE project")

    daily_profiles, group_profiles = project.profiles()
    weekly: List[Dict[str, Any]] = []
    for collection_key, profile in _items(group_profiles):
        if _call_bool(profile, "is_weekly") is not True:
            continue
        try:
            data = profile.get_data()
            data_error = None
        except Exception as exc:  # pragma: no cover - VE runtime diagnostic
            data = None
            data_error = str(exc)
        weekly.append(
            {
                "collection_key": _safe_text(collection_key),
                "id": _safe_text(getattr(profile, "id", "")),
                "reference": _safe_text(getattr(profile, "reference", "")),
                "python_type": _safe_text(type(profile)),
                "is_absolute": _call_bool(profile, "is_absolute"),
                "is_modulating": _call_bool(profile, "is_modulating"),
                "data_length": len(data) if isinstance(data, (list, tuple)) else None,
                "data": data,
                "data_error": data_error,
            }
        )

    project_path = Path(str(project.path))
    diagnostics = (
        project_path / "sia4010_artifacts" / "diagnostics"
    )
    diagnostics.mkdir(parents=True, exist_ok=True)
    report_path = diagnostics / "ve_weekly_profile_contract_probe.json"
    create_profile = getattr(project, "create_profile", None)
    report = {
        "status": "READ_ONLY_COMPLETE",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "project": {
            "name": _safe_text(getattr(project, "name", "")),
            "path": str(project_path),
        },
        "runtime": {
            "create_profile_doc": _safe_text(getattr(create_profile, "__doc__", "")),
            "daily_profile_count": len(daily_profiles),
            "group_profile_count": len(group_profiles),
            "weekly_profile_count": len(weekly),
        },
        "weekly_profiles": weekly,
        "mutation_performed": False,
    }
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )

    print("READ-ONLY VE WEEKLY-PROFILE CONTRACT PROBE: COMPLETE")
    print("Project: {}".format(project_path))
    print("create_profile doc: {}".format(report["runtime"]["create_profile_doc"]))
    print("Weekly profiles: {}".format(len(weekly)))
    for item in weekly:
        print(
            "- id={!r} ref={!r} type={} absolute={} modulating={} length={}".format(
                item["id"],
                item["reference"],
                item["python_type"],
                item["is_absolute"],
                item["is_modulating"],
                item["data_length"],
            )
        )
    print("Report: {}".format(report_path))
    print("No VE profile or project data was created, changed or saved.")


if __name__ == "__main__":
    run()
