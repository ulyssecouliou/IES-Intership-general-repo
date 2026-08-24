"""Evidence-pack export for manager and reviewer handoff.

The pack is a convenience artifact generated after the Excel report. It does
not certify the model. It gathers the timestamped workbook, reviewer-provided
evidence files, templates, and a machine-readable manifest so the compliance
reviewer can see what was available for the run.
"""

from __future__ import annotations

import json
import re
import zipfile
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .config import (
    SIA4010_CLASS_MANIFEST_PREFIXES,
    SIA4010_EVIDENCE_MANIFEST_PREFIXES,
    SIA4010_EVIDENCE_REQUIREMENTS,
    SIA4010_OFFICIAL_TEST_RESULTS_PREFIXES,
)


BLOCKED_EVIDENCE_SUFFIXES = {
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".exe",
    ".msi",
    ".ps1",
    ".pyd",
    ".py",
    ".scr",
    ".vbs",
    ".zip",
}

HELPER_EVIDENCE_PATTERNS = [
    "readme.md",
    "sia3802_justification_*.csv",
    "sia3802_justifications_*.csv",
    "sia2024_usage_mapping_*.csv",
    "sia3802_global_reference_comparison_*.csv",
    "sia3802_project_metadata_*.csv",
    "sia3874_lighting_control_mapping_*.csv",
    "glazing_solar_protection_*.csv",
    "g_values_audit_*.csv",
]


def create_evidence_pack(
    project_root: Path,
    report_path: Path,
    latest_report_path: Optional[Path],
    sia4010_results: Dict[str, Any],
    preflight_checks: List[Dict[str, Any]],
    evidence_dir_name: str = "sia4010_evidence",
    project_label: Optional[str] = None,
    evidence_project_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Create a ZIP evidence pack and return a report-ready status payload."""
    project_root = Path(project_root).resolve()
    evidence_project_root = Path(evidence_project_root or project_root).resolve()
    report_path = Path(report_path).resolve()
    latest_report_path = Path(latest_report_path).resolve() if latest_report_path else None
    output_path = _build_pack_path(report_path)

    manifest = _build_manifest(
        project_root=project_root,
        report_path=report_path,
        latest_report_path=latest_report_path,
        output_path=output_path,
        sia4010_results=sia4010_results,
        preflight_checks=preflight_checks,
        evidence_dir_name=evidence_dir_name,
        project_label=project_label,
        evidence_project_root=evidence_project_root,
    )

    file_entries: List[Dict[str, Any]] = []
    _collect_file_entry(project_root, report_path, file_entries, "reports")
    if latest_report_path and latest_report_path != report_path:
        _collect_file_entry(project_root, latest_report_path, file_entries, "reports")

    excluded_files: List[Dict[str, str]] = []
    evidence_root = evidence_project_root / evidence_dir_name
    for file_path in _iter_existing_files(evidence_root):
        if not matches_active_project_scope(file_path, project_label):
            excluded_files.append({
                "path": _relative_or_absolute(project_root, file_path),
                "reason": (
                    "Project-scoped helper/manifest file belongs to another VE project; "
                    f"active project is {project_label}."
                ),
            })
            continue
        include_file, exclusion_reason = _should_include_evidence_file(file_path, evidence_root)
        if include_file:
            _collect_file_entry(evidence_project_root, file_path, file_entries, evidence_dir_name)
        else:
            excluded_files.append({
                "path": _relative_or_absolute(project_root, file_path),
                "reason": exclusion_reason,
            })

    for file_path in _iter_existing_files(project_root / "templates" / "evidence"):
        _collect_file_entry(project_root, file_path, file_entries, "templates/evidence")

    for relative_doc in [
        "docs/project/CLIENT_RUN_GUIDE.md",
        "docs/project/RELEASE_ACCEPTANCE_CHECKLIST.md",
        "docs/project/SIA4010_TESTS_AND_CLASSES_IMPLEMENTATION.md",
        "docs/project/SIA_COMPLIANCE_EXECUTION_TRACKER.md",
        "docs/project/GLAZING_EVIDENCE_GUIDE.md",
    ]:
        _collect_file_entry(project_root, project_root / relative_doc, file_entries, "docs/project")

    included_files = [
        {
            "group": entry["group"],
            "path": entry["archive_name"],
            "size_bytes": entry["size_bytes"],
        }
        for entry in file_entries
    ]
    manifest["included_file_count"] = len(included_files)
    manifest["included_files"] = included_files
    manifest["excluded_file_count"] = len(excluded_files)
    manifest["excluded_files"] = excluded_files

    temporary_path = output_path.with_name(output_path.name + ".tmp")
    try:
        if temporary_path.exists():
            temporary_path.unlink()
        with zipfile.ZipFile(temporary_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
            _write_text(package, "README_EVIDENCE_PACK.md", _build_pack_readme(manifest))
            _write_text(package, "manifest/evidence_pack_manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
            for entry in file_entries:
                package.write(str(entry["source_path"]), entry["archive_name"])
        temporary_path.replace(output_path)
    except Exception:
        try:
            if temporary_path.exists():
                temporary_path.unlink()
        finally:
            raise

    return {
        "status": "CREATED",
        "path": str(output_path),
        "file_count": len(included_files),
        "included_files": included_files,
        "excluded_files": excluded_files,
        "manifest": manifest,
    }


def _build_pack_path(report_path: Path) -> Path:
    """Return the timestamped ZIP path associated with one report workbook."""
    stem = report_path.stem.replace("Swiss_Compliance_Report", "Swiss_Compliance_Evidence_Pack")
    output_path = report_path.with_name(f"{stem}.zip")
    suffix = 2
    while output_path.exists():
        output_path = report_path.with_name(f"{stem}_{suffix}.zip")
        suffix += 1
    return output_path


def _build_manifest(
    project_root: Path,
    report_path: Path,
    latest_report_path: Optional[Path],
    output_path: Path,
    sia4010_results: Dict[str, Any],
    preflight_checks: List[Dict[str, Any]],
    evidence_dir_name: str,
    project_label: Optional[str],
    evidence_project_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Build the JSON manifest embedded in the ZIP evidence pack."""
    evidence = sia4010_results.get("evidence", {}) if isinstance(sia4010_results, dict) else {}
    evidence_summary = evidence.get("summary", {}) if isinstance(evidence, dict) else {}
    official_summary = evidence_summary.get("official_test_result_summary", {}) if isinstance(evidence_summary, dict) else {}
    preflight_counts: Dict[str, int] = {}
    for check in preflight_checks or []:
        status = str(check.get("status", "UNKNOWN") or "UNKNOWN")
        preflight_counts[status] = preflight_counts.get(status, 0) + 1

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "Manager/reviewer handoff package; not an official SIA certificate.",
        "project_root": str(project_root),
        "evidence_project_root": str(evidence_project_root or project_root),
        "project_label": project_label or "",
        "report_path": _relative_or_absolute(project_root, report_path),
        "latest_report_alias": _relative_or_absolute(project_root, latest_report_path) if latest_report_path else "",
        "package_path": _relative_or_absolute(project_root, output_path),
        "evidence_directory": evidence_dir_name,
        "sia4010_status": evidence_summary.get("status", "NOT_CHECKABLE"),
        "sia4010_validation_class": evidence_summary.get("validation_class") or "",
        "sia4010_validation_class_status": evidence_summary.get("validation_class_selection_status", "NOT_SELECTED"),
        "sia4010_present_evidence_count": evidence_summary.get("present_count", 0),
        "sia4010_required_evidence_count": evidence_summary.get("required_count", 0),
        "sia4010_manifest_documented_count": evidence_summary.get("manifest_documented_count", 0),
        "sia4010_official_test_result_rows": official_summary.get("result_row_count", 0),
        "sia4010_recorded_pass_tests": official_summary.get("recorded_pass_tests", []),
        "sia4010_official_failed_tests": official_summary.get("failed_tests", []),
        "preflight_status_counts": preflight_counts,
        "copyright_note": (
            "Official SIA standard PDFs from references/standards are intentionally not included. "
            "Attach licensed standards separately only when redistribution is authorized."
        ),
    }


def _build_pack_readme(manifest: Dict[str, Any]) -> str:
    """Return the README text stored in the generated evidence pack."""
    recorded_pass_tests = manifest.get("sia4010_recorded_pass_tests") or []
    failed_tests = manifest.get("sia4010_official_failed_tests") or []
    return "\n".join([
        "# Swiss SIA Evidence Pack",
        "",
        "This ZIP was generated by the IESVE Run-button workflow.",
        "",
        "It is a reviewer handoff package, not an official SIA certificate.",
        "",
        "## Included Scope",
        "",
        "- Timestamped Swiss compliance Excel report.",
        "- Allowed evidence files currently present in `sia4010_evidence/`.",
        "- Evidence templates and key project guidance documents.",
        "- Machine-readable manifest at `manifest/evidence_pack_manifest.json`.",
        "- Excluded evidence-folder files are listed in the manifest.",
        "",
        "## Current SIA 4010 State",
        "",
        f"- Evidence status: `{manifest.get('sia4010_status', 'NOT_CHECKABLE')}`.",
        f"- Selected validation class: `{manifest.get('sia4010_validation_class') or 'not selected'}`.",
        f"- Class selection status: `{manifest.get('sia4010_validation_class_status', 'NOT_SELECTED')}`.",
        f"- Evidence families present: `{manifest.get('sia4010_present_evidence_count', 0)}/{manifest.get('sia4010_required_evidence_count', 0)}`.",
        f"- Manifest-documented evidence families: `{manifest.get('sia4010_manifest_documented_count', 0)}`.",
        f"- Official result rows: `{manifest.get('sia4010_official_test_result_rows', 0)}`.",
        f"- Tests with recorded PASS result rows: `{', '.join(recorded_pass_tests) if recorded_pass_tests else 'none'}`.",
        f"- Official failed tests: `{', '.join(failed_tests) if failed_tests else 'none'}`.",
        "",
        "## Important Guardrail",
        "",
        manifest.get("copyright_note", ""),
        "",
        "Before making any official SIA 4010 validation claim, the responsible",
        "authority/reviewer must confirm the official evidence files, class scope,",
        "candidate results, reference comparisons, and PASS/FAIL outcomes.",
        "",
    ])


def _iter_existing_files(root: Path) -> Iterable[Path]:
    """Yield existing files under root in deterministic order."""
    if not root.exists() or not root.is_dir():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file())


def matches_active_project_scope(file_path: Path, project_label: Optional[str]) -> bool:
    """Exclude project helper/manifests whose filename targets another VE project."""
    file_path = Path(file_path)
    if not project_label:
        return True
    normalized_name = file_path.name.lower()
    if normalized_name == "readme.md":
        return True
    matched_prefix = ""
    for pattern in HELPER_EVIDENCE_PATTERNS:
        if pattern != "readme.md" and fnmatch(normalized_name, pattern):
            matched_prefix = pattern.split("*", 1)[0]
            break
    if not matched_prefix:
        for prefix in (
            *SIA4010_EVIDENCE_MANIFEST_PREFIXES,
            *SIA4010_CLASS_MANIFEST_PREFIXES,
            *SIA4010_OFFICIAL_TEST_RESULTS_PREFIXES,
        ):
            if normalized_name.startswith(prefix.lower()):
                matched_prefix = prefix
                break
    if not matched_prefix:
        return True
    scope_key = re.sub(r"[^a-z0-9]+", "", str(project_label).lower())
    file_key = re.sub(r"[^a-z0-9]+", "", file_path.stem.lower())
    prefix_key = re.sub(r"[^a-z0-9]+", "", Path(matched_prefix).stem.lower())
    return bool(
        scope_key
        and prefix_key
        and file_key.startswith(prefix_key)
        and file_key[len(prefix_key):] == scope_key
    )


def _collect_file_entry(
    project_root: Path,
    file_path: Path,
    file_entries: List[Dict[str, Any]],
    archive_group: str,
) -> None:
    """Collect one package file when it exists and is under the project root."""
    file_path = Path(file_path).resolve()
    if not file_path.exists() or not file_path.is_file():
        return
    if project_root not in file_path.parents and file_path != project_root:
        return

    relative = file_path.relative_to(project_root).as_posix()
    if any(entry.get("archive_name") == relative for entry in file_entries):
        return
    file_entries.append({
        "source_path": file_path,
        "archive_name": relative,
        "group": archive_group,
        "size_bytes": file_path.stat().st_size,
    })


def _should_include_evidence_file(file_path: Path, evidence_root: Path) -> Tuple[bool, str]:
    """Return whether one evidence-folder file is safe and relevant for export."""
    if file_path.is_symlink():
        return False, "Symbolic links are not included in evidence packs."

    name = file_path.name
    normalized_name = name.lower()
    suffix = file_path.suffix.lower()
    if suffix in BLOCKED_EVIDENCE_SUFFIXES:
        return False, f"Blocked evidence-pack file type: {suffix}."

    if _looks_like_licensed_sia_standard(normalized_name):
        return False, "Licensed SIA standard/reference PDFs are intentionally not redistributed in evidence packs."

    if any(fnmatch(normalized_name, pattern) for pattern in HELPER_EVIDENCE_PATTERNS):
        return True, ""

    for prefix in SIA4010_EVIDENCE_MANIFEST_PREFIXES:
        if normalized_name.startswith(prefix.lower()) and suffix == ".csv":
            return True, ""

    for prefix in SIA4010_CLASS_MANIFEST_PREFIXES:
        if normalized_name.startswith(prefix.lower()) and suffix == ".csv":
            return True, ""

    for prefix in SIA4010_OFFICIAL_TEST_RESULTS_PREFIXES:
        if normalized_name.startswith(prefix.lower()) and suffix == ".csv":
            return True, ""

    for requirement in SIA4010_EVIDENCE_REQUIREMENTS.values():
        accepted_extensions = {
            str(extension).lower()
            for extension in requirement.get("accepted_extensions", []) or []
        }
        required_prefixes = [
            str(prefix).lower()
            for prefix in requirement.get("required_prefixes", []) or []
        ]
        if suffix in accepted_extensions and any(normalized_name.startswith(prefix) for prefix in required_prefixes):
            return True, ""

    try:
        relative = file_path.relative_to(evidence_root).as_posix()
    except ValueError:
        relative = name
    return False, f"File does not match an allowed evidence-pack naming rule: {relative}."


def _looks_like_licensed_sia_standard(normalized_name: str) -> bool:
    """Return true for obvious copied standard/reference PDF names."""
    if not normalized_name.endswith(".pdf"):
        return False
    standard_markers = [
        "sia 380-2",
        "sia 380_2",
        "sia 4010",
        "380-2-2022",
        "4010-2023",
        "r223",
        "4010_form",
    ]
    return any(marker in normalized_name for marker in standard_markers)


def _write_text(package: zipfile.ZipFile, archive_name: str, text: str) -> None:
    """Write UTF-8 text content into the package."""
    package.writestr(archive_name, text.encode("utf-8"))


def _relative_or_absolute(project_root: Path, path: Optional[Path]) -> str:
    """Return a stable relative path when possible."""
    if not path:
        return ""
    path = Path(path).resolve()
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return str(path)
