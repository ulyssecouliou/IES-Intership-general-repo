"""Evidence scanning helpers for reviewer-signed SIA justifications.

The checker must never turn a failed model value into a silent pass. This module
only detects reviewed justification records so the report can show
``JUSTIFIED_BY_EVIDENCE`` while keeping the original model value and limit
visible.
"""

from __future__ import annotations

import csv
import os
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


def scan_sia3802_justifications(project_root: Path, evidence_dir_name: str = "sia4010_evidence") -> Dict[str, Any]:
    """Scan reviewer justification CSV files from the project evidence folder."""
    evidence_dir = Path(project_root) / evidence_dir_name
    files = _matching_files(evidence_dir, JUSTIFICATION_FILE_PATTERNS)
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
        "files": [str(path) for path in files],
        "records": records,
        "accepted_records": accepted_records,
        "record_count": len(records),
        "accepted_count": len(accepted_records),
        "errors": errors,
        "status": "AVAILABLE" if accepted_records else ("PENDING_REVIEW" if records else "NOT_PROVIDED"),
    }


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
    if not evidence_dir.is_dir():
        return []
    files: List[Path] = []
    for pattern in patterns:
        files.extend(evidence_dir.glob(pattern))
    return sorted({path.resolve() for path in files if path.is_file()})


def _read_justification_csv(file_path: Path) -> List[Dict[str, Any]]:
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
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _clean_value(value: Any) -> str:
    return str(value or "").strip()


def _status_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _key(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]+", "", str(value or "").upper())


def _scope_key(value: Any) -> str:
    tokens = [
        _key(token)
        for token in re.split(r"[,;|]+", str(value or ""))
        if token.strip()
    ]
    return "|".join(sorted(token for token in tokens if token))


def _field_matches(record_value: Any, requested_value: Any) -> bool:
    record_key = _key(record_value)
    requested_key = _key(requested_value)
    return bool(record_key and requested_key and (record_key == requested_key or requested_key in record_key or record_key in requested_key))


def _scope_matches(record_scope: Any, requested_scope: Any) -> bool:
    record_key = _scope_key(record_scope)
    requested_key = _scope_key(requested_scope)
    if not record_key or not requested_key:
        return False
    if record_key == requested_key:
        return True
    record_parts = set(record_key.split("|"))
    requested_parts = set(requested_key.split("|"))
    return bool(record_parts and requested_parts and (record_parts <= requested_parts or requested_parts <= record_parts))
