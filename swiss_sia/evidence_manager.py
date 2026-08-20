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

SIA3802_THERMAL_BRIDGE_FILE_PATTERNS = (
    "SIA3802_thermal_bridges_*.csv",
    "sia3802_thermal_bridges_*.csv",
)

SIA3802_COOLING_GENERATOR_FILE_PATTERNS = (
    "SIA3802_cooling_generators_*.csv",
    "sia3802_cooling_generators_*.csv",
)

SIA3802_AHU_HEAT_RECOVERY_FILE_PATTERNS = (
    "SIA3802_ahu_heat_recovery_*.csv",
    "sia3802_ahu_heat_recovery_*.csv",
)

SIA3802_VENTILATION_CONTROL_FILE_PATTERNS = (
    "SIA3802_ventilation_control_*.csv",
    "sia3802_ventilation_control_*.csv",
)

GLAZING_SOLAR_PROTECTION_FILE_PATTERNS = (
    "glazing_solar_protection_*.csv",
    "GLAZING_solar_protection_*.csv",
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


def _scan_reviewer_records(
    project_root: Path,
    evidence_dir_name: str,
    file_patterns: Any,
    project_label: Optional[str],
    normalizer: Any,
) -> Dict[str, Any]:
    """Scan project-scoped reviewer CSVs and normalize each row.

    Shared body for every reviewer-owned SIA 380/2 evidence family (thermal
    bridges, cooling generators, AHU/heat recovery, ventilation control). Only
    the file patterns and the per-row normalizer differ; acceptance is decided by
    the normalizer, never inferred here.
    """
    evidence_dir = Path(project_root) / evidence_dir_name
    files, excluded_files = _matching_project_files(
        evidence_dir, file_patterns, project_label
    )
    records: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    for file_path in files:
        try:
            with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
                for row_number, raw_row in enumerate(csv.DictReader(handle), start=2):
                    record = normalizer(raw_row)
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


def _find_accepted_for_project(
    scan_results: Dict[str, Any],
    project_label: str,
) -> Optional[Dict[str, Any]]:
    """Return the accepted reviewer record matching the active VE project."""
    if not isinstance(scan_results, dict):
        return None
    accepted = scan_results.get("accepted_records", []) or []
    if not isinstance(accepted, list):
        return None
    for record in accepted:
        if isinstance(record, dict) and _field_matches(record.get("project_id"), project_label):
            return record
    return None


def scan_sia3802_thermal_bridges(
    project_root: Path,
    evidence_dir_name: str = "sia4010_evidence",
    project_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Scan reviewer-owned SIA 380/2 thermal-bridge (psi/chi) records.

    VE exposes no psi/chi quantity, so the project's thermal-bridge treatment is
    supplied as reviewed external evidence rather than read from the model.
    """
    return _scan_reviewer_records(
        project_root,
        evidence_dir_name,
        SIA3802_THERMAL_BRIDGE_FILE_PATTERNS,
        project_label,
        _normalize_thermal_bridge_record,
    )


def find_accepted_thermal_bridges(
    thermal_bridge_results: Dict[str, Any],
    project_label: str,
) -> Optional[Dict[str, Any]]:
    """Return the accepted thermal-bridge record for the active VE project."""
    return _find_accepted_for_project(thermal_bridge_results, project_label)


def scan_sia3802_cooling_generators(
    project_root: Path,
    evidence_dir_name: str = "sia4010_evidence",
    project_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Scan reviewer-owned cooling-generator EER/SEER records.

    An autosized VE cooling generator leaves its capacity greyed out, so the
    SIA 380/2 Tables 5-7 EER power band cannot be resolved from the model. The
    reviewer then supplies the generator class, the nominal capacity (kW) and the
    nominal EER (with SEER optional) from the manufacturer data sheet. Nothing is
    inferred from an empty field.
    """
    return _scan_reviewer_records(
        project_root,
        evidence_dir_name,
        SIA3802_COOLING_GENERATOR_FILE_PATTERNS,
        project_label,
        _normalize_cooling_generator_record,
    )


def find_accepted_cooling_generators(
    cooling_generator_results: Dict[str, Any],
    project_label: str,
) -> Optional[Dict[str, Any]]:
    """Return the accepted cooling-generator record for the active VE project."""
    return _find_accepted_for_project(cooling_generator_results, project_label)


def scan_sia3802_ahu_heat_recovery(
    project_root: Path,
    evidence_dir_name: str = "sia4010_evidence",
    project_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Scan reviewer-owned AHU / heat-recovery records (SIA 380/2 Table 4).

    VE exposes recovery/control identifiers but not verified leakage class,
    seasonal recovery efficiency, pressure drops or SFP. The reviewer supplies
    them from the AHU data sheet; nothing is inferred from an empty field.
    """
    return _scan_reviewer_records(
        project_root,
        evidence_dir_name,
        SIA3802_AHU_HEAT_RECOVERY_FILE_PATTERNS,
        project_label,
        _normalize_ahu_heat_recovery_record,
    )


def find_accepted_ahu_heat_recovery(
    ahu_results: Dict[str, Any],
    project_label: str,
) -> Optional[Dict[str, Any]]:
    """Return the accepted AHU / heat-recovery record for the active VE project."""
    return _find_accepted_for_project(ahu_results, project_label)


def scan_sia3802_ventilation_control(
    project_root: Path,
    evidence_dir_name: str = "sia4010_evidence",
    project_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Scan reviewer-owned ventilation-control records (SIA 380/2 Table 4).

    The Table 4 control band depends on the system type (monozone/multizone) and
    the specific airflow (<=3 / 3-6 / >6 m3/(h.m2)); the reviewer classifies the
    installed control strategy against it. Nothing is inferred from the model.
    """
    return _scan_reviewer_records(
        project_root,
        evidence_dir_name,
        SIA3802_VENTILATION_CONTROL_FILE_PATTERNS,
        project_label,
        _normalize_ventilation_control_record,
    )


def find_accepted_ventilation_control(
    ventilation_results: Dict[str, Any],
    project_label: str,
) -> Optional[Dict[str, Any]]:
    """Return the accepted ventilation-control record for the active VE project."""
    return _find_accepted_for_project(ventilation_results, project_label)


def scan_glazing_solar_protection(
    project_root: Path,
    evidence_dir_name: str = "sia4010_evidence",
    project_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Scan reviewer-owned solar-protection records (SIA 380/2 Table 10).

    One row per facade/construction: solar-protection type + g_total with shading
    are the Table 10 quantum. Used when the shading is documented outside VE (not
    modelled on the openings). Nothing is inferred from an empty field.
    """
    return _scan_reviewer_records(
        project_root,
        evidence_dir_name,
        GLAZING_SOLAR_PROTECTION_FILE_PATTERNS,
        project_label,
        _normalize_solar_protection_record,
    )


def accepted_solar_protection_windows(
    solar_protection_results: Dict[str, Any],
    project_label: str,
) -> int:
    """Sum the reviewed window count across accepted solar-protection rows.

    Returns how many external windows the reviewer has documented with a Table 10
    solar-protection treatment for this project, so the coverage check can compare
    it against the external windows VE actually sees (never a silent full pass).
    """
    if not isinstance(solar_protection_results, dict):
        return 0
    accepted = solar_protection_results.get("accepted_records", []) or []
    if not isinstance(accepted, list):
        return 0
    total = 0
    for record in accepted:
        if not isinstance(record, dict):
            continue
        if not _field_matches(record.get("project_id"), project_label):
            continue
        count = record.get("window_count_numeric")
        total += int(count) if count is not None else 1
    return total


def _normalize_solar_protection_record(raw_row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize one reviewer-owned solar-protection record (SIA 380/2 Table 10).

    Accepted only when a reviewer has signed off a solar-protection type and a
    numeric g_total with shading (the Table 10 quantum), with a traceable source.
    The reviewed window count feeds the coverage reconciliation. Nothing is
    inferred from an empty field.
    """
    record = {
        _normalize_header(key): _clean_value(value)
        for key, value in (raw_row or {}).items()
        if key is not None
    }
    record.setdefault("project_id", record.get("project_name", record.get("project", "")))
    record.setdefault("facade_or_zone", "")
    record.setdefault("window_count", "")
    record.setdefault("solar_protection_type", "")
    record.setdefault("solar_protection_category", "")
    record.setdefault("shading_control_strategy", "")
    record.setdefault("g_total_with_shading", "")
    record.setdefault("review_status", "")
    record.setdefault("reviewer", "")
    record.setdefault("source_document", record.get("source_file", ""))
    record.setdefault("source_page_or_sheet", "")
    record.setdefault("notes", "")
    for numeric_field in ("window_count", "g_total_with_shading"):
        try:
            record[numeric_field + "_numeric"] = float(record.get(numeric_field))
        except (TypeError, ValueError):
            record[numeric_field + "_numeric"] = None
    record["accepted"] = (
        _status_key(record.get("review_status")) in ACCEPTED_REVIEW_STATUSES
        and bool(record.get("project_id"))
        and bool(record.get("solar_protection_type"))
        and record.get("g_total_with_shading_numeric") is not None
        and bool(record.get("reviewer"))
        and bool(record.get("source_document") or record.get("source_page_or_sheet"))
    )
    return record


def _normalize_cooling_generator_record(raw_row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize one reviewer-owned cooling-generator EER/SEER record.

    Accepted only when a reviewer has signed off a generator class, a numeric
    nominal capacity (kW) and a numeric nominal EER (the SIA 380/2 Tables 5-7
    quantum), with a traceable manufacturer source. SEER is optional and stays
    conditional on SN EN 14825 (absent from the verified sources).
    """
    record = {
        _normalize_header(key): _clean_value(value)
        for key, value in (raw_row or {}).items()
        if key is not None
    }
    record.setdefault("project_id", record.get("project", ""))
    record.setdefault("generator_class", "")
    record.setdefault("capacity_kw", "")
    record.setdefault("nominal_eer", "")
    record.setdefault("seer", "")
    record.setdefault("unit", "")
    record.setdefault("review_status", "")
    record.setdefault("reviewer", "")
    record.setdefault("review_date", "")
    record.setdefault("source_document", record.get("source_file", ""))
    record.setdefault("source_reference", "")
    record.setdefault("notes", "")
    for numeric_field in ("capacity_kw", "nominal_eer", "seer"):
        try:
            record[numeric_field + "_numeric"] = float(record.get(numeric_field))
        except (TypeError, ValueError):
            record[numeric_field + "_numeric"] = None
    record["accepted"] = (
        _status_key(record.get("review_status")) in ACCEPTED_REVIEW_STATUSES
        and bool(record.get("project_id"))
        and bool(record.get("generator_class"))
        and record.get("capacity_kw_numeric") is not None
        and record.get("nominal_eer_numeric") is not None
        and bool(record.get("reviewer"))
        and bool(record.get("review_date"))
        and bool(record.get("source_document") or record.get("source_reference"))
    )
    return record


def _normalize_ahu_heat_recovery_record(raw_row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize one reviewer-owned AHU / heat-recovery record (SIA 380/2 Table 4).

    Accepted only when a reviewer has signed off the leakage/air-tightness class
    and a numeric heat-recovery temperature efficiency (the Table 4 quantum),
    with a traceable AHU data-sheet source. Pressure drop and SFP are optional
    supplementary fields. Nothing is inferred from an empty field.
    """
    record = {
        _normalize_header(key): _clean_value(value)
        for key, value in (raw_row or {}).items()
        if key is not None
    }
    record.setdefault("project_id", record.get("project", ""))
    record.setdefault("leakage_class", "")
    record.setdefault("heat_recovery_type", "")
    record.setdefault("heat_recovery_temperature_efficiency", "")
    record.setdefault("supply_pressure_drop_pa", "")
    record.setdefault("extract_pressure_drop_pa", "")
    record.setdefault("sfp_w_per_m3_s", "")
    record.setdefault("unit", "")
    record.setdefault("review_status", "")
    record.setdefault("reviewer", "")
    record.setdefault("review_date", "")
    record.setdefault("source_document", record.get("source_file", ""))
    record.setdefault("source_reference", "")
    record.setdefault("notes", "")
    for numeric_field in (
        "heat_recovery_temperature_efficiency",
        "supply_pressure_drop_pa",
        "extract_pressure_drop_pa",
        "sfp_w_per_m3_s",
    ):
        try:
            record[numeric_field + "_numeric"] = float(record.get(numeric_field))
        except (TypeError, ValueError):
            record[numeric_field + "_numeric"] = None
    record["accepted"] = (
        _status_key(record.get("review_status")) in ACCEPTED_REVIEW_STATUSES
        and bool(record.get("project_id"))
        and bool(record.get("leakage_class"))
        and record.get("heat_recovery_temperature_efficiency_numeric") is not None
        and bool(record.get("reviewer"))
        and bool(record.get("review_date"))
        and bool(record.get("source_document") or record.get("source_reference"))
    )
    return record


def _normalize_ventilation_control_record(raw_row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize one reviewer-owned ventilation-control record (SIA 380/2 Table 4).

    Accepted only when a reviewer has signed off the system type
    (monozone/multizone), the installed control class and the specific airflow
    band it was judged against, with a traceable source. Nothing is inferred.
    """
    record = {
        _normalize_header(key): _clean_value(value)
        for key, value in (raw_row or {}).items()
        if key is not None
    }
    record.setdefault("project_id", record.get("project", ""))
    record.setdefault("system_type", "")
    record.setdefault("control_class", "")
    record.setdefault("airflow_band", "")
    record.setdefault("specific_airflow_m3_h_m2", "")
    record.setdefault("unit", "")
    record.setdefault("review_status", "")
    record.setdefault("reviewer", "")
    record.setdefault("review_date", "")
    record.setdefault("source_document", record.get("source_file", ""))
    record.setdefault("source_reference", "")
    record.setdefault("notes", "")
    try:
        record["specific_airflow_m3_h_m2_numeric"] = float(
            record.get("specific_airflow_m3_h_m2")
        )
    except (TypeError, ValueError):
        record["specific_airflow_m3_h_m2_numeric"] = None
    has_band = (
        bool(record.get("airflow_band"))
        or record.get("specific_airflow_m3_h_m2_numeric") is not None
    )
    record["accepted"] = (
        _status_key(record.get("review_status")) in ACCEPTED_REVIEW_STATUSES
        and bool(record.get("project_id"))
        and bool(record.get("system_type"))
        and bool(record.get("control_class"))
        and has_band
        and bool(record.get("reviewer"))
        and bool(record.get("review_date"))
        and bool(record.get("source_document") or record.get("source_reference"))
    )
    return record


def _normalize_thermal_bridge_record(raw_row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize one reviewer-owned thermal-bridge (psi/chi) record.

    Accepted only when a reviewer has signed off a stated assessment method and
    either a numeric total psi.L + chi (W/K) or a referenced junction schedule,
    with a traceable source. The tool never derives the value from an empty VE
    field, and zero is only valid when explicitly stated and reviewed.
    """
    record = {
        _normalize_header(key): _clean_value(value)
        for key, value in (raw_row or {}).items()
        if key is not None
    }
    record.setdefault("project_id", record.get("project", ""))
    record.setdefault("assessment_method", "")
    record.setdefault("total_psi_chi_w_per_k", "")
    record.setdefault("schedule_reference", "")
    record.setdefault("unit", "")
    record.setdefault("review_status", "")
    record.setdefault("reviewer", "")
    record.setdefault("review_date", "")
    record.setdefault("source_document", record.get("source_file", ""))
    record.setdefault("source_reference", "")
    record.setdefault("notes", "")
    try:
        record["total_psi_chi_w_per_k_numeric"] = float(record.get("total_psi_chi_w_per_k"))
    except (TypeError, ValueError):
        record["total_psi_chi_w_per_k_numeric"] = None
    has_quantum = (
        record.get("total_psi_chi_w_per_k_numeric") is not None
        or bool(record.get("schedule_reference"))
    )
    record["accepted"] = (
        _status_key(record.get("review_status")) in ACCEPTED_REVIEW_STATUSES
        and bool(record.get("project_id"))
        and bool(record.get("assessment_method"))
        and has_quantum
        and bool(record.get("reviewer"))
        and bool(record.get("review_date"))
        and bool(record.get("source_document") or record.get("source_reference"))
    )
    return record


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
