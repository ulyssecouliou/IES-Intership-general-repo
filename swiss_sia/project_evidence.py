"""Safe project-local storage for the client evidence editor.

The UI is intentionally a thin layer.  This module owns paths, CSV schemas,
backups and fail-closed review-state validation so it can be tested without VE
or Tkinter.
"""

from __future__ import annotations

import csv
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from .config import SIA4010_EVIDENCE_DIR
from .evidence_manager import normalize_reviewer_evidence


@dataclass(frozen=True)
class EvidenceFamily:
    key: str
    title: str
    filename: str
    fields: Tuple[str, ...]
    help_text: str


FAMILIES: Tuple[EvidenceFamily, ...] = (
    EvidenceFamily(
        "project_metadata", "Projet et climat", "SIA3802_project_metadata_{project}.csv",
        (
            "project_id", "building_status", "weather_basis", "weather_file",
            "location", "altitude_m", "review_status", "reviewer",
            "review_date", "source_document", "source_reference", "notes",
            "ventilation_strategy", "ventilation_justification",
            "ventilation_flow_source", "lighting_scope",
            "lighting_power_source", "aps_outputs_required",
            "aps_outputs_justification",
        ),
        "Statut du bâtiment et base climatique approuvés par le responsable énergie.",
    ),
    EvidenceFamily(
        "global_comparison", "Comparaison globale", "SIA3802_global_reference_comparison_{project}.csv",
        ("project_id", "comparison_scope", "comparison_metric", "project_value", "reference_value", "unit", "comparison_result", "reviewer", "review_date", "review_status", "source_document", "source_reference", "notes"),
        "Comparaison du projet complet avec la référence SIA, issue du calcul signé.",
    ),
    EvidenceFamily(
        "ventilation_control", "Commande ventilation", "SIA3802_ventilation_control_{project}.csv",
        ("project_id", "system_id", "room_or_zone", "system_type", "control_class", "airflow_band", "specific_airflow_m3_h_m2", "unit", "air_flow_control", "fan_control", "demand_sensor", "control_scope", "minimum_airflow_percent", "time_schedule", "review_status", "reviewer", "review_date", "source_document", "source_reference", "notes"),
        "Une ligne par système ou zone. Les valeurs préremplies depuis VE restent à confirmer.",
    ),
    EvidenceFamily(
        "cooling_generator", "Générateur froid", "SIA3802_cooling_generators_{project}.csv",
        ("project_id", "generator_class", "capacity_kw", "nominal_eer", "seer", "unit", "review_status", "reviewer", "review_date", "source_document", "source_reference", "notes"),
        "Classe, puissance et EER/SEER d'après la fiche fabricant approuvée.",
    ),
    EvidenceFamily(
        "lighting_mapping", "Commande éclairage", "SIA3874_lighting_control_mapping_{project}.csv",
        ("room_id", "thermal_template_id", "sia3874_control_type", "daylight_control", "review_status", "reviewer", "source_document", "source_reference", "notes"),
        "Correspondance pièce ou template avec le type de commande SIA 387/4.",
    ),
    EvidenceFamily(
        "electrical_power", "Puissance électrique", "SIA3802_electrical_power_{project}.csv",
        ("project_id", "building_status", "required_electrical_power_w_m2", "conditioned_area_m2", "cooling_present", "cooling_category", "unit", "review_status", "reviewer", "review_date", "source_document", "source_reference", "notes"),
        "Puissance de dimensionnement en W/m² et catégorie de nécessité du froid.",
    ),
)
FAMILY_BY_KEY = {item.key: item for item in FAMILIES}


FIELD_CHOICES: Dict[str, Tuple[str, ...]] = {
    "building_status": ("", "NEW_BUILDING", "EXISTING_BUILDING"),
    "review_status": ("pending", "accepted"),
    "comparison_scope": ("complete_sia3802_project",),
    "comparison_metric": ("global_energy_expenditure_index_sia380",),
    "comparison_result": ("", "pass", "fail"),
    "system_type": ("", "monozone", "multizone"),
    "control_class": ("", "one_speed_time_schedule", "two_speeds_time_schedule", "two_speeds_occupancy", "variable_occupancy", "variable_gas_sensor"),
    "airflow_band": ("", "LE_3", "3_TO_6", "GT_6"),
    "generator_class": ("", "air_cooled", "water_cooled"),
    "cooling_present": ("", "YES", "NO"),
    "cooling_category": ("", "necessary", "desirable", "none"),
    "control_scope": ("", "system", "zone", "room"),
}

DEFAULTS = {
    "review_status": "pending",
    "comparison_scope": "complete_sia3802_project",
    "comparison_metric": "global_energy_expenditure_index_sia380",
    "unit": "",
}
UNIT_DEFAULTS = {
    "global_comparison": "kWh/m2a",
    "ventilation_control": "m3/(h.m2)",
    "cooling_generator": "EER/SEER=W/W;kW",
    "electrical_power": "W/m2",
}


def safe_project_label(value: object) -> str:
    text = str(value or "VE_Project").strip() or "VE_Project"
    return (re.sub(r'[^A-Za-z0-9_.-]+', "_", text).strip("._") or "VE_Project")[:80]


def evidence_path(project_root: Path, family: str, project_label: str) -> Path:
    spec = FAMILY_BY_KEY[family]
    return Path(project_root).resolve() / SIA4010_EVIDENCE_DIR / spec.filename.format(
        project=safe_project_label(project_label)
    )


def empty_record(family: str, project_label: str, weather_file: str = "") -> Dict[str, str]:
    spec = FAMILY_BY_KEY[family]
    row = {field: DEFAULTS.get(field, "") for field in spec.fields}
    if "project_id" in row:
        row["project_id"] = safe_project_label(project_label)
    if family == "project_metadata":
        row["weather_file"] = str(weather_file or "")
    if family in UNIT_DEFAULTS:
        row["unit"] = UNIT_DEFAULTS[family]
    return row


def load_records(project_root: Path, family: str, project_label: str, weather_file: str = "") -> List[Dict[str, str]]:
    path = evidence_path(project_root, family, project_label)
    if not path.is_file():
        return [empty_record(family, project_label, weather_file)]
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    return rows or [empty_record(family, project_label, weather_file)]


def save_records(project_root: Path, family: str, project_label: str, records: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    """Validate and atomically save rows; invalid acceptance is forced pending."""

    spec = FAMILY_BY_KEY[family]
    target = evidence_path(project_root, family, project_label)
    target.parent.mkdir(parents=True, exist_ok=True)
    cleaned: List[Dict[str, str]] = []
    forced_pending = 0
    accepted_count = 0
    for incoming in records:
        row = {field: str(incoming.get(field, "") or "").strip() for field in spec.fields}
        if "project_id" in row:
            row["project_id"] = safe_project_label(project_label)
        normalized = normalize_reviewer_evidence(family, row)
        requested = row.get("review_status", "").lower() in {"accepted", "approved", "validated"}
        if requested and not normalized.get("accepted"):
            row["review_status"] = "pending"
            forced_pending += 1
        elif normalized.get("accepted"):
            accepted_count += 1
        cleaned.append(row)
    if not cleaned:
        cleaned = [empty_record(family, project_label)]

    backup = None
    if target.exists():
        backup = target.with_suffix(target.suffix + ".bak")
        backup.write_bytes(target.read_bytes())
    fd, temporary_name = tempfile.mkstemp(prefix=target.stem + "_", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(spec.fields), extrasaction="ignore")
            writer.writeheader()
            writer.writerows(cleaned)
        os.replace(temporary_name, target)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise
    return {
        "path": str(target), "row_count": len(cleaned),
        "accepted_count": accepted_count, "forced_pending_count": forced_pending,
        "backup": str(backup) if backup else "",
    }
