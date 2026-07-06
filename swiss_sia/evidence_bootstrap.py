"""Create project-specific evidence templates for the VE Run-button workflow."""

from __future__ import annotations

import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import PROJECT_ROOT, SIA4010_EVIDENCE_DIR


TEMPLATE_TARGETS = [
    ("sia4010_evidence_index_template.csv", "SIA4010_evidence_index_{project}.csv"),
    ("sia4010_class_validation_template.csv", "SIA4010_class_validation_{project}.csv"),
    ("sia4010_official_test_results_template.csv", "SIA4010_official_test_results_{project}.csv"),
    ("sia3802_justifications_template.csv", "SIA3802_justifications_{project}.csv"),
    ("glazing_solar_protection_template.csv", "glazing_solar_protection_{project}.csv"),
    ("g_values_audit_template.csv", "g_values_audit_{project}.csv"),
]


def prepare_evidence_folder(
    project_root: Path = PROJECT_ROOT,
    project_label: Optional[str] = None,
    overwrite: bool = False,
) -> Dict[str, Any]:
    """Copy evidence templates into the project evidence folder with safe names."""
    project_root = Path(project_root).resolve()
    project_label = _safe_filename_part(project_label or _detect_ve_project_label() or "VE_Project")
    template_dir = project_root / "templates" / "evidence"
    evidence_dir = project_root / SIA4010_EVIDENCE_DIR
    evidence_dir.mkdir(parents=True, exist_ok=True)

    results: List[Dict[str, Any]] = []
    for template_name, target_pattern in TEMPLATE_TARGETS:
        source = template_dir / template_name
        target = evidence_dir / target_pattern.format(project=project_label)
        if not source.exists():
            results.append({
                "template": template_name,
                "target": str(target),
                "status": "MISSING_TEMPLATE",
                "message": f"Template not found: {source}",
            })
            continue
        if target.exists() and not overwrite:
            results.append({
                "template": template_name,
                "target": str(target),
                "status": "EXISTS",
                "message": "Kept existing file. Use overwrite=True only if a reset is intentional.",
            })
            continue

        shutil.copy2(source, target)
        results.append({
            "template": template_name,
            "target": str(target),
            "status": "CREATED" if not overwrite else "OVERWRITTEN",
            "message": "Project evidence template is ready.",
        })

    created = sum(1 for item in results if item["status"] in {"CREATED", "OVERWRITTEN"})
    existing = sum(1 for item in results if item["status"] == "EXISTS")
    missing = sum(1 for item in results if item["status"] == "MISSING_TEMPLATE")
    return {
        "status": "READY" if missing == 0 else "PARTIAL",
        "project_label": project_label,
        "evidence_dir": str(evidence_dir),
        "created_count": created,
        "existing_count": existing,
        "missing_template_count": missing,
        "files": results,
    }


def print_preparation_summary(result: Dict[str, Any]) -> None:
    """Print a concise summary suitable for the IESVE script console."""
    print("SIA evidence folder preparation")
    print(f"Status: {result.get('status')}")
    print(f"Project label: {result.get('project_label')}")
    print(f"Evidence folder: {result.get('evidence_dir')}")
    print(
        "Files: "
        f"{result.get('created_count', 0)} created, "
        f"{result.get('existing_count', 0)} existing, "
        f"{result.get('missing_template_count', 0)} missing template(s)"
    )
    for item in result.get("files", []):
        print(f"- {item.get('status')}: {item.get('target')}")


def _detect_ve_project_label() -> str:
    """Return the current VE project folder name when the IESVE API is present."""
    try:
        import iesve  # type: ignore

        project = iesve.VEProject.get_current_project()
        project_path = str(getattr(project, "path", "") or "")
        if project_path:
            return Path(project_path).name
    except Exception:
        return ""
    return ""


def _safe_filename_part(value: object, fallback: str = "VE_Project") -> str:
    """Return a Windows-safe ASCII filename fragment."""
    text = str(value or "").strip() or fallback
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r'[<>:"/\\|?*]+', "_", text)
    text = re.sub(r"\s+", "_", text)
    text = text.strip("._ ")
    return (text or fallback)[:80]
