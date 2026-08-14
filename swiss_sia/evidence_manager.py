"""Evidence scanning helpers for reviewer-signed SIA justifications.

The checker must never turn a failed model value into a silent pass. This module
only detects reviewed justification records so the report can show
``JUSTIFIED_BY_EVIDENCE`` while keeping the original model value and limit
visible.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ACCEPTED_REVIEW_STATUSES = {
    "accepted",
    "approved",
    "justified",
    "reviewed",
    "signed",
    "signed_off",
    "signedoff",
    "validated",
}

ACCEPTED_DECISION_STATUSES = {
    "accepted",
    "approved",
    "justified",
    "justified_by_evidence",
    "reviewed",
}

JUSTIFICATION_FILE_PATTERNS = (
    "SIA3802_justification_*.csv",
    "SIA3802_justifications_*.csv",
    "sia3802_justification_*.csv",
    "sia3802_justifications_*.csv",
)

SIA2024_USAGE_MAPPING_FILE_PATTERNS = (
    "SIA2024_usage_mapping_*.csv",
    "sia2024_usage_mapping_*.csv",
)

SIA3874_LIGHTING_MAPPING_FILE_PATTERNS = (
    "SIA3874_lighting_control_mapping_*.csv",
    "sia3874_lighting_control_mapping_*.csv",
)

SIA3802_PROJECT_METADATA_FILE_PATTERNS = (
    "SIA3802_project_metadata_*.csv",
    "sia3802_project_metadata_*.csv",
)

SIA3802_GLOBAL_COMPARISON_FILE_PATTERNS = (
    "SIA3802_global_reference_comparison_*.csv",
    "sia3802_global_reference_comparison_*.csv",
)


def scan_sia3802_justifications(
    project_root: Path,
    evidence_dir_name: str = "sia4010_evidence",
    project_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Scan only reviewer justifications scoped to the active VE project."""
    evidence_dir = Path(project_root) / evidence_dir_name
    files, excluded_files = _matching_project_files(
        evidence_dir,
        JUSTIFICATION_FILE_PATTERNS,
        project_label,
    )
    records: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []

    for file_path in files:
        try:
            records.extend(_read_justification_csv(file_path))
        except Exception as exc:
            errors.append({"file": str(file_path), "error": str(exc)})

    accepted_records = [record for record in records if record.get("accepted")]
    return {
        "evidence_dir": str(evidence_dir),
        "project_label": project_label or "",
        "files": [str(path) for path in files],
        "excluded_files": [str(path) for path in excluded_files],
        "records": records,
        "accepted_records": accepted_records,
        "record_count": len(records),
        "accepted_count": len(accepted_records),
        "errors": errors,
        "status": "AVAILABLE" if accepted_records else ("PENDING_REVIEW" if records else "NOT_PROVIDED"),
    }


def scan_sia2024_usage_mappings(
    project_root: Path,
    evidence_dir_name: str = "sia4010_evidence",
    project_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Scan reviewer-confirmed room/template mappings to SIA 2024 use categories."""
    return _scan_reviewer_mapping_files(
        project_root,
        evidence_dir_name,
        SIA2024_USAGE_MAPPING_FILE_PATTERNS,
        project_label,
        mapping_field="sia2024_category",
        mapping_kind="SIA 2024 usage category",
    )


def scan_sia3874_lighting_mappings(
    project_root: Path,
    evidence_dir_name: str = "sia4010_evidence",
    project_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Scan reviewer-confirmed mappings to SIA 387/4 lighting controls."""
    return _scan_reviewer_mapping_files(
        project_root,
        evidence_dir_name,
        SIA3874_LIGHTING_MAPPING_FILE_PATTERNS,
        project_label,
        mapping_field="sia3874_control_type",
        mapping_kind="SIA 387/4 lighting control",
    )


def scan_sia3802_project_metadata(
    project_root: Path,
    evidence_dir_name: str = "sia4010_evidence",
    project_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Scan reviewer-approved project status and climate metadata records."""
    evidence_dir = Path(project_root) / evidence_dir_name
    files, excluded_files = _matching_project_files(
        evidence_dir,
        SIA3802_PROJECT_METADATA_FILE_PATTERNS,
        project_label,
    )
    records: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    for file_path in files:
        try:
            with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
                for row_number, raw_row in enumerate(csv.DictReader(handle), start=2):
                    record = _normalize_project_metadata_record(raw_row)
                    record["file"] = str(file_path)
                    record["row"] = row_number
                    records.append(record)
        except Exception as exc:
            errors.append({"file": str(file_path), "error": str(exc)})
    accepted_records = [record for record in records if record.get("accepted")]
    return {
        "evidence_dir": str(evidence_dir),
        "project_label": project_label or "",
        "files": [str(path) for path in files],
        "excluded_files": [str(path) for path in excluded_files],
        "records": records,
        "accepted_records": accepted_records,
        "record_count": len(records),
        "accepted_count": len(accepted_records),
        "errors": errors,
        "status": "AVAILABLE" if accepted_records else ("PENDING_REVIEW" if records else "NOT_PROVIDED"),
    }


def find_accepted_project_metadata(
    metadata_results: Dict[str, Any],
    project_label: str,
) -> Optional[Dict[str, Any]]:
    """Return accepted metadata matching the active VE project label."""
    if not isinstance(metadata_results, dict):
        return None
    accepted = metadata_results.get("accepted_records", []) or []
    if not isinstance(accepted, list):
        return None
    for record in accepted:
        if isinstance(record, dict) and _field_matches(record.get("project_id"), project_label):
            return record
    return None


def scan_sia3802_global_comparisons(
    project_root: Path,
    evidence_dir_name: str = "sia4010_evidence",
    project_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Scan reviewer-approved global project/reference comparison records."""
    evidence_dir = Path(project_root) / evidence_dir_name
    files, excluded_files = _matching_project_files(
        evidence_dir,
        SIA3802_GLOBAL_COMPARISON_FILE_PATTERNS,
        project_label,
    )
    records: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    for file_path in files:
        try:
            with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
                for row_number, raw_row in enumerate(csv.DictReader(handle), start=2):
                    record = _normalize_global_comparison_record(raw_row)
                    record["file"] = str(file_path)
                    record["row"] = row_number
                    records.append(record)
        except Exception as exc:
            errors.append({"file": str(file_path), "error": str(exc)})
    accepted_records = [record for record in records if record.get("accepted")]
    return {
        "evidence_dir": str(evidence_dir),
        "project_label": project_label or "",
        "files": [str(path) for path in files],
        "excluded_files": [str(path) for path in excluded_files],
        "records": records,
        "accepted_records": accepted_records,
        "record_count": len(records),
        "accepted_count": len(accepted_records),
        "errors": errors,
        "status": "AVAILABLE" if accepted_records else ("PENDING_REVIEW" if records else "NOT_PROVIDED"),
    }


def find_accepted_global_comparison(
    comparison_results: Dict[str, Any],
    project_label: str,
) -> Optional[Dict[str, Any]]:
    """Return the accepted complete comparison for the active VE project."""
    if not isinstance(comparison_results, dict):
        return None
    accepted = comparison_results.get("accepted_records", []) or []
    if not isinstance(accepted, list):
        return None
    for record in accepted:
        if isinstance(record, dict) and _field_matches(record.get("project_id"), project_label):
            return record
    return None


def find_accepted_mapping(
    mapping_results: Dict[str, Any],
    *,
    room_id: Optional[str] = None,
    thermal_template_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Return an accepted external-standard mapping for a room or template."""
    if not isinstance(mapping_results, dict):
        return None
    accepted = mapping_results.get("accepted_records", []) or []
    if not isinstance(accepted, list):
        return None
    for record in accepted:
        if not isinstance(record, dict):
            continue
        mapped_room = record.get("room_id") or record.get("room")
        mapped_template = record.get("thermal_template_id") or record.get("template_id")
        if room_id and mapped_room and _field_matches(mapped_room, room_id):
            return record
        if thermal_template_id and mapped_template and _field_matches(mapped_template, thermal_template_id):
            return record
    return None


def find_accepted_justification(
    justification_results: Dict[str, Any],
    *,
    rule: Optional[str] = None,
    construction: Optional[str] = None,
    domain: Optional[str] = None,
    standard: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Return the strongest accepted justification matching a rule/scope."""
    if not isinstance(justification_results, dict):
        return None

    candidates = justification_results.get("accepted_records", []) or []
    if not isinstance(candidates, list):
        return None

    for record in candidates:
        if not isinstance(record, dict):
            continue
        if rule and not _field_matches(record.get("rule"), rule):
            continue
        if construction and not _scope_matches(record.get("construction_or_scope"), construction):
            continue
        if domain and record.get("domain") and not _field_matches(record.get("domain"), domain):
            continue
        if standard and record.get("standard") and not _field_matches(record.get("standard"), standard):
            continue
        return record
    return None


def describe_justification(record: Optional[Dict[str, Any]]) -> str:
    """Build a compact user-facing description for a justification record."""
    if not record:
        return ""
    bits = []
    reviewer = str(record.get("reviewer") or "").strip()
    source = str(record.get("source_document") or record.get("source_file") or "").strip()
    reference = str(record.get("source_reference") or "").strip()
    summary = str(record.get("justification_summary") or record.get("notes") or "").strip()
    if reviewer:
        bits.append(f"reviewer={reviewer}")
    if source:
        bits.append(f"source={source}")
    if reference:
        bits.append(f"ref={reference}")
    if summary:
        bits.append(summary)
    return "; ".join(bits) or "Reviewed justification attached."


def _matching_files(evidence_dir: Path, patterns: Iterable[str]) -> List[Path]:
    """Return evidence files matching any accepted justification pattern."""
    if not evidence_dir.is_dir():
        return []
    files: List[Path] = []
    for pattern in patterns:
        files.extend(evidence_dir.glob(pattern))
    return sorted({path.resolve() for path in files if path.is_file()})


def _matching_project_files(
    evidence_dir: Path,
    patterns: Iterable[str],
    project_label: Optional[str],
) -> tuple[List[Path], List[Path]]:
    """Return matching evidence files split into active-project and excluded scopes."""
    pattern_list = tuple(patterns)
    files = _matching_files(evidence_dir, pattern_list)
    if not project_label:
        return files, []
    included = [
        path
        for path in files
        if _matches_project_scoped_filename(path, pattern_list, project_label)
    ]
    excluded = [path for path in files if path not in included]
    return included, excluded


def _matches_project_scoped_filename(
    file_path: Path,
    patterns: Iterable[str],
    project_label: str,
) -> bool:
    """Match the exact project suffix after a recognized evidence-file prefix."""
    project_key = _key(project_label)
    stem_key = _key(file_path.stem)
    if not project_key or not stem_key:
        return False
    for pattern in patterns:
        prefix = str(pattern).split("*", 1)[0]
        prefix_key = _key(Path(prefix).stem)
        if prefix_key and stem_key.startswith(prefix_key):
            return stem_key[len(prefix_key):] == project_key
    return False


def _scan_reviewer_mapping_files(
    project_root: Path,
    evidence_dir_name: str,
    patterns: Iterable[str],
    project_label: Optional[str],
    *,
    mapping_field: str,
    mapping_kind: str,
) -> Dict[str, Any]:
    """Scan one family of reviewer-owned external-standard mapping CSV files."""
    evidence_dir = Path(project_root) / evidence_dir_name
    files, excluded_files = _matching_project_files(
        evidence_dir,
        patterns,
        project_label,
    )
    records: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    for file_path in files:
        try:
            with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
                for row_number, raw_row in enumerate(csv.DictReader(handle), start=2):
                    record = _normalize_mapping_record(raw_row, mapping_field)
                    record["file"] = str(file_path)
                    record["row"] = row_number
                    records.append(record)
        except Exception as exc:
            errors.append({"file": str(file_path), "error": str(exc)})
    accepted_records = [record for record in records if record.get("accepted")]
    return {
        "mapping_kind": mapping_kind,
        "mapping_field": mapping_field,
        "evidence_dir": str(evidence_dir),
        "project_label": project_label or "",
        "files": [str(path) for path in files],
        "excluded_files": [str(path) for path in excluded_files],
        "records": records,
        "accepted_records": accepted_records,
        "record_count": len(records),
        "accepted_count": len(accepted_records),
        "errors": errors,
        "status": "AVAILABLE" if accepted_records else ("PENDING_REVIEW" if records else "NOT_PROVIDED"),
    }


def _normalize_mapping_record(raw_row: Dict[str, Any], mapping_field: str) -> Dict[str, Any]:
    """Normalize and validate one reviewer-owned mapping record."""
    record = {
        _normalize_header(key): _clean_value(value)
        for key, value in (raw_row or {}).items()
        if key is not None
    }
    record.setdefault("room_id", record.get("room", ""))
    record.setdefault("thermal_template_id", record.get("template_id", ""))
    record.setdefault(mapping_field, "")
    record.setdefault("review_status", "")
    record.setdefault("reviewer", "")
    record.setdefault("source_document", record.get("source_file", ""))
    record.setdefault("source_reference", "")
    record.setdefault("notes", "")
    record["accepted"] = (
        _status_key(record.get("review_status")) in ACCEPTED_REVIEW_STATUSES
        and bool(record.get("room_id") or record.get("thermal_template_id"))
        and bool(record.get(mapping_field))
        and bool(record.get("reviewer"))
        and bool(record.get("source_document") or record.get("source_reference"))
    )
    return record


def _normalize_project_metadata_record(raw_row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize one reviewer-owned project metadata record."""
    record = {
        _normalize_header(key): _clean_value(value)
        for key, value in (raw_row or {}).items()
        if key is not None
    }
    status_key = _status_key(record.get("building_status"))
    status_aliases = {
        "new": "NEW_BUILDING",
        "new_building": "NEW_BUILDING",
        "new_construction": "NEW_BUILDING",
        "existing": "EXISTING_BUILDING",
        "existing_building": "EXISTING_BUILDING",
    }
    record["building_status"] = status_aliases.get(status_key, "")
    record.setdefault("project_id", record.get("project", ""))
    record.setdefault("weather_basis", "")
    record.setdefault("weather_file", "")
    record.setdefault("location", "")
    record.setdefault("altitude_m", "")
    record.setdefault("review_status", "")
    record.setdefault("reviewer", "")
    record.setdefault("review_date", "")
    record.setdefault("source_document", record.get("source_file", ""))
    record.setdefault("source_reference", "")
    record.setdefault("notes", "")
    record["accepted"] = (
        _status_key(record.get("review_status")) in ACCEPTED_REVIEW_STATUSES
        and bool(record.get("project_id"))
        and bool(record.get("building_status"))
        and bool(record.get("reviewer"))
        and bool(record.get("review_date"))
        and bool(record.get("source_document") or record.get("source_reference"))
    )
    return record


def _normalize_global_comparison_record(raw_row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize one reviewer-owned global SIA 380/2 comparison record."""
    record = {
        _normalize_header(key): _clean_value(value)
        for key, value in (raw_row or {}).items()
        if key is not None
    }
    record.setdefault("project_id", record.get("project", ""))
    record.setdefault("comparison_scope", "")
    record.setdefault("comparison_metric", "")
    record.setdefault("project_value", "")
    record.setdefault("reference_value", "")
    record.setdefault("unit", "")
    record.setdefault("comparison_result", "")
    record.setdefault("review_status", "")
    record.setdefault("reviewer", "")
    record.setdefault("review_date", "")
    record.setdefault("source_document", record.get("source_file", ""))
    record.setdefault("source_reference", "")
    record.setdefault("notes", "")
    try:
        record["project_value_numeric"] = float(record.get("project_value"))
        record["reference_value_numeric"] = float(record.get("reference_value"))
    except (TypeError, ValueError):
        record["project_value_numeric"] = None
        record["reference_value_numeric"] = None
    result_key = _status_key(record.get("comparison_result"))
    metric_key = _status_key(record.get("comparison_metric"))
    record["accepted"] = (
        _status_key(record.get("review_status")) in ACCEPTED_REVIEW_STATUSES
        and _status_key(record.get("comparison_scope")) == "complete_sia3802_project"
        and metric_key == "global_energy_expenditure_index_sia380"
        and result_key in {"pass", "passed", "compliant", "accepted"}
        and bool(record.get("project_id"))
        and record.get("project_value_numeric") is not None
        and record.get("reference_value_numeric") is not None
        and record["project_value_numeric"] <= record["reference_value_numeric"]
        and bool(record.get("unit"))
        and bool(record.get("reviewer"))
        and bool(record.get("review_date"))
        and bool(record.get("source_document") or record.get("source_reference"))
    )
    return record


def _read_justification_csv(file_path: Path) -> List[Dict[str, Any]]:
    """Read one reviewer justification CSV and normalize every row."""
    with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row_number, raw_row in enumerate(reader, start=2):
            record = _normalize_record(raw_row)
            record["file"] = str(file_path)
            record["row"] = row_number
            rows.append(record)
        return rows


def _normalize_record(raw_row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize reviewer justification fields and compute acceptance status."""
    record = {
        _normalize_header(key): _clean_value(value)
        for key, value in (raw_row or {}).items()
        if key is not None
    }
    record.setdefault("standard", "")
    record.setdefault("domain", "")
    record.setdefault("rule", "")
    record.setdefault("construction_or_scope", "")
    record.setdefault("decision_status", record.get("status", ""))
    record.setdefault("review_status", "")
    record.setdefault("reviewer", "")
    record.setdefault("source_document", record.get("source_file", ""))
    record.setdefault("source_reference", "")
    record.setdefault("justification_summary", record.get("summary", ""))
    record.setdefault("notes", "")

    review_status = _status_key(record.get("review_status"))
    decision_status = _status_key(record.get("decision_status"))
    record["accepted"] = (
        review_status in ACCEPTED_REVIEW_STATUSES
        and (not decision_status or decision_status in ACCEPTED_DECISION_STATUSES)
        and bool(record.get("reviewer"))
        and bool(record.get("source_document") or record.get("source_reference"))
    )
    record["normalized_rule"] = _key(record.get("rule"))
    record["normalized_scope"] = _scope_key(record.get("construction_or_scope"))
    return record


def _normalize_header(value: Any) -> str:
    """Normalize a CSV header to a stable snake_case key."""
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _clean_value(value: Any) -> str:
    """Return a stripped string for a CSV field value."""
    return str(value or "").strip()


def _status_key(value: Any) -> str:
    """Normalize review/decision statuses for comparisons."""
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _key(value: Any) -> str:
    """Normalize a value to an uppercase alphanumeric comparison key."""
    return re.sub(r"[^A-Z0-9]+", "", str(value or "").upper())


def _scope_key(value: Any) -> str:
    """Normalize comma/semicolon separated scope labels for matching."""
    tokens = [
        _key(token)
        for token in re.split(r"[,;|]+", str(value or ""))
        if token.strip()
    ]
    return "|".join(sorted(token for token in tokens if token))


def _field_matches(record_value: Any, requested_value: Any) -> bool:
    """Return true when a record field matches the requested value fuzzily."""
    record_key = _key(record_value)
    requested_key = _key(requested_value)
    return bool(record_key and requested_key and (record_key == requested_key or requested_key in record_key or record_key in requested_key))


def _scope_matches(record_scope: Any, requested_scope: Any) -> bool:
    """Return true when a justification scope covers the requested scope."""
    record_key = _scope_key(record_scope)
    requested_key = _scope_key(requested_scope)
    if not record_key or not requested_key:
        return False
    if record_key == requested_key:
        return True
    record_parts = set(record_key.split("|"))
    requested_parts = set(requested_key.split("|"))
    return bool(record_parts and requested_parts and (record_parts <= requested_parts or requested_parts <= record_parts))
