"""Create project-specific evidence templates for the VE Run-button workflow."""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import PROJECT_ROOT, SIA4010_EVIDENCE_DIR

TEMPLATE_TARGETS = [
    ("sia4010_evidence_index_template.csv", "SIA4010_evidence_index_{project}.csv"),
    ("sia4010_class_validation_template.csv", "SIA4010_class_validation_{project}.csv"),
    (
        "sia4010_official_test_results_template.csv",
        "SIA4010_official_test_results_{project}.csv",
    ),
    (
        "sia4010_software_register_review_template.csv",
        "SIA4010_software_register_review_{project}.csv",
    ),
    ("sia3802_justifications_template.csv", "SIA3802_justifications_{project}.csv"),
    ("sia2024_usage_mapping_template.csv", "SIA2024_usage_mapping_{project}.csv"),
    (
        "sia3874_lighting_control_mapping_template.csv",
        "SIA3874_lighting_control_mapping_{project}.csv",
    ),
    ("sia3802_project_metadata_template.csv", "SIA3802_project_metadata_{project}.csv"),
    (
        "sia3802_global_reference_comparison_template.csv",
        "SIA3802_global_reference_comparison_{project}.csv",
    ),
    ("sia3802_thermal_bridges_template.csv", "SIA3802_thermal_bridges_{project}.csv"),
    (
        "sia3802_cooling_generators_template.csv",
        "SIA3802_cooling_generators_{project}.csv",
    ),
    ("sia3802_ahu_heat_recovery_template.csv", "SIA3802_ahu_heat_recovery_{project}.csv"),
    (
        "sia3802_ventilation_control_template.csv",
        "SIA3802_ventilation_control_{project}.csv",
    ),
    ("sia3802_electrical_power_template.csv", "SIA3802_electrical_power_{project}.csv"),
    ("glazing_solar_protection_template.csv", "glazing_solar_protection_{project}.csv"),
    ("g_values_audit_template.csv", "g_values_audit_{project}.csv"),
]

PROJECT_LABEL_TOKENS = (
    "VE_PROJECT_FOLDER_NAME",
    "PROJECT_FOLDER_NAME",
)


def prepare_evidence_folder(
    project_root: Path = PROJECT_ROOT,
    project_label: Optional[str] = None,
    overwrite: bool = False,
    template_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Copy evidence templates into the project evidence folder with safe names."""
    project_root = Path(project_root).resolve()
    source_root = Path(template_root or PROJECT_ROOT).resolve()
    project_label = _safe_filename_part(
        project_label or _detect_ve_project_label() or "VE_Project"
    )
    template_dir = source_root / "templates" / "evidence"
    evidence_dir = project_root / SIA4010_EVIDENCE_DIR
    evidence_dir.mkdir(parents=True, exist_ok=True)

    results: List[Dict[str, Any]] = []
    for template_name, target_pattern in TEMPLATE_TARGETS:
        source = template_dir / template_name
        target = evidence_dir / target_pattern.format(project=project_label)
        if not source.exists():
            results.append(
                {
                    "template": template_name,
                    "target": str(target),
                    "status": "MISSING_TEMPLATE",
                    "message": f"Template not found: {source}",
                }
            )
            continue
        if target.exists() and not overwrite:
            results.append(
                {
                    "template": template_name,
                    "target": str(target),
                    "status": "EXISTS",
                    "message": "Kept existing file. Use overwrite=True only if a reset is intentional.",
                }
            )
            continue

        target_existed = target.exists()
        _copy_project_template(source, target, project_label)
        results.append(
            {
                "template": template_name,
                "target": str(target),
                "status": "OVERWRITTEN" if target_existed else "CREATED",
                "message": "Project evidence template is ready.",
            }
        )

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


def prefill_ventilation_control_evidence(
    rooms_data: Any,
    project_root: Path = PROJECT_ROOT,
    project_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Replace only the untouched ventilation placeholder with VE inventory rows.

    The generated rows remain ``pending`` and cannot validate compliance until a
    reviewer supplies their name/date and confirms the canonical Table-4 class.
    Existing user-edited evidence is never overwritten.
    """
    root = Path(project_root).resolve()
    label = _safe_filename_part(project_label or "VE_Project")
    target = (
        root / SIA4010_EVIDENCE_DIR / ("SIA3802_ventilation_control_{}.csv".format(label))
    )
    if not target.is_file():
        return {"status": "MISSING", "file": str(target), "row_count": 0}
    try:
        with target.open("r", encoding="utf-8-sig", newline="") as handle:
            existing = list(csv.DictReader(handle))
    except Exception as exc:
        return {"status": "ERROR", "file": str(target), "error": str(exc), "row_count": 0}
    if not existing:
        return {"status": "EMPTY", "file": str(target), "row_count": 0}
    placeholder = existing[0]
    untouched = (
        len(existing) == 1
        and str(placeholder.get("review_status") or "").strip().lower() == "pending"
        and (
            "VE_APACHE_SYSTEM_ID" in str(placeholder.get("system_id") or "")
            or "REVIEWER_NAME" in str(placeholder.get("reviewer") or "")
        )
    )
    if not untouched:
        return {"status": "PRESERVED", "file": str(target), "row_count": len(existing)}

    fieldnames = list(placeholder.keys())
    generated: List[Dict[str, Any]] = []
    control_class_by_level = {
        0: "one_speed_time_schedule",
        1: "two_speeds_time_schedule",
    }
    for room in list(rooms_data or []):
        if getattr(room, "mechanical_ventilation_present", None) is not True:
            continue
        systems = [
            system
            for system in (getattr(room, "hvac_systems", []) or [])
            if isinstance(system, dict)
        ] or [{}]
        for system in systems:
            airflow = getattr(room, "ventilation_m3_h_m2", None)
            try:
                airflow_number = float(airflow) if airflow is not None else None
            except (TypeError, ValueError):
                airflow_number = None
            band = ""
            if airflow_number is not None:
                band = (
                    "LE_3"
                    if airflow_number <= 3
                    else ("3_TO_6" if airflow_number <= 6 else "GT_6")
                )
            profiles = sorted(
                {
                    str(item.get("variation_profile") or "")
                    for item in (getattr(room, "air_exchange_evidence", []) or [])
                    if isinstance(item, dict) and item.get("variation_profile")
                }
            )
            level = getattr(room, "ventilation_control_level", None)
            row = {name: "" for name in fieldnames}
            row.update(
                {
                    "project_id": label,
                    "system_id": str(system.get("id") or ""),
                    "room_or_zone": str(
                        getattr(room, "id", "") or getattr(room, "name", "") or ""
                    ),
                    "system_type": str(
                        getattr(room, "ventilation_installation_type", "") or ""
                    ),
                    "control_class": control_class_by_level.get(level, ""),
                    "airflow_band": band,
                    "specific_airflow_m3_h_m2": (
                        "" if airflow_number is None else "{:.6g}".format(airflow_number)
                    ),
                    "unit": "m3/(h.m2)",
                    "air_flow_control": str(system.get("air_flow_control") or ""),
                    "fan_control": str(system.get("fan_control") or ""),
                    "demand_sensor": str(
                        system.get("demand_controlled_ventilation") or ""
                    ),
                    "control_scope": (
                        "room" if getattr(room, "hvac_zone", None) else "system"
                    ),
                    "time_schedule": " | ".join(profiles),
                    "review_status": "pending",
                    "source_document": "IESVE model readback; reviewer confirmation required",
                    "source_reference": (
                        "VERoomData.get_air_exchanges/get_apache_systems; "
                        "VEApacheSystem ventilation_ncm/system_controls_ncm"
                    ),
                    "notes": str(
                        getattr(room, "ventilation_control_evidence_note", "") or ""
                    ),
                }
            )
            generated.append(row)
    if not generated:
        return {"status": "NO_MECHANICAL_ROOMS", "file": str(target), "row_count": 0}
    try:
        with target.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(generated)
    except Exception as exc:
        return {"status": "ERROR", "file": str(target), "error": str(exc), "row_count": 0}
    return {"status": "PREFILLED", "file": str(target), "row_count": len(generated)}


def _untouched_placeholder(
    target: Path, placeholder_tokens: tuple[str, ...]
) -> tuple[List[Dict[str, Any]], Optional[Dict[str, Any]], Optional[str]]:
    """Read one evidence CSV and identify its untouched generated placeholder."""

    if not target.is_file():
        return [], None, "MISSING"
    try:
        with target.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except Exception:
        return [], None, "ERROR"
    if not rows:
        return [], None, "EMPTY"
    first = rows[0]
    payload = " ".join(str(value or "") for value in first.values())
    untouched = (
        len(rows) == 1
        and str(first.get("review_status") or "").strip().lower() == "pending"
        and any(token in payload for token in placeholder_tokens)
    )
    return rows, first if untouched else None, None if untouched else "PRESERVED"


def _write_pending_rows(
    target: Path, fieldnames: List[str], rows: List[Dict[str, Any]]
) -> Dict[str, Any]:
    try:
        with target.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    except Exception as exc:
        return {"status": "ERROR", "file": str(target), "error": str(exc), "row_count": 0}
    return {"status": "PREFILLED", "file": str(target), "row_count": len(rows)}


def _sia2024_category_from_template(template_id: str) -> str:
    """Extract only an explicit SIA 2024 category encoded in a template name."""

    match = re.search(
        r"SIA\s*2024[_ -]*(\d{1,2}(?:[._Pp]\d{1,2})?)",
        str(template_id or ""),
        flags=re.IGNORECASE,
    )
    if not match:
        return ""
    return match.group(1).replace("P", ".").replace("p", ".").replace("_", ".")


def prefill_cooling_generator_evidence(
    rooms_data: Any,
    project_root: Path = PROJECT_ROOT,
    project_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Prefill cooling-generator values explicitly exposed by VE, never inferred ones.

    The rows remain pending because the reviewer must confirm the generator class,
    manufacturer basis and applicability of the SIA table. Existing edited rows
    are preserved.
    """

    root = Path(project_root).resolve()
    label = _safe_filename_part(project_label or "VE_Project")
    target = (
        root / SIA4010_EVIDENCE_DIR / ("SIA3802_cooling_generators_{}.csv".format(label))
    )
    rows, placeholder, status = _untouched_placeholder(
        target,
        (
            "air_cooled_OR_water_cooled",
            "NOMINAL_CAPACITY_KW",
            "REVIEWER_NAME",
        ),
    )
    if placeholder is None:
        return {"status": status, "file": str(target), "row_count": len(rows)}

    fieldnames = list(placeholder.keys())
    generated: List[Dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for room in list(rooms_data or []):
        for system in getattr(room, "hvac_systems", []) or []:
            if not isinstance(system, dict):
                continue
            generator_class = str(system.get("cooling_generator_class") or "").strip()
            capacity = system.get("cooling_capacity_kw")
            eer = system.get("eer")
            seer = system.get("seer")
            if not any(
                value not in (None, "")
                for value in (generator_class, capacity, eer, seer)
            ):
                continue
            identity = tuple(
                str(value or "")
                for value in (
                    system.get("id"),
                    generator_class,
                    capacity,
                    eer,
                    seer,
                )
            )
            if identity in seen:
                continue
            seen.add(identity)
            row = {name: "" for name in fieldnames}
            row.update(
                {
                    "project_id": label,
                    "generator_class": generator_class,
                    "capacity_kw": "" if capacity is None else str(capacity),
                    "nominal_eer": "" if eer is None else str(eer),
                    "seer": "" if seer is None else str(seer),
                    "unit": "EER/SEER=W/W;kW",
                    "review_status": "pending",
                    "source_document": "IESVE Apache system readback; manufacturer confirmation required",
                    "source_reference": "VEApacheSystem cooling/cooling_ncm",
                    "notes": (
                        "VE system {}. Values are copied without inference; blank class or "
                        "performance fields remain unresolved until reviewer confirmation."
                    ).format(system.get("id") or system.get("name") or "not identified"),
                }
            )
            generated.append(row)
    if not generated:
        return {"status": "NO_EXPOSED_COOLING_DATA", "file": str(target), "row_count": 0}
    return _write_pending_rows(target, fieldnames, generated)


def prefill_sia2024_usage_evidence(
    rooms_data: Any,
    project_root: Path = PROJECT_ROOT,
    project_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Prefill explicit template-encoded SIA 2024 categories as pending evidence."""

    root = Path(project_root).resolve()
    label = _safe_filename_part(project_label or "VE_Project")
    target = root / SIA4010_EVIDENCE_DIR / ("SIA2024_usage_mapping_{}.csv".format(label))
    rows, placeholder, status = _untouched_placeholder(
        target, ("ROOM_ID_OR_BLANK", "TEMPLATE_ID_OR_BLANK", "REVIEWER_TO_COMPLETE")
    )
    if placeholder is None:
        return {"status": status, "file": str(target), "row_count": len(rows)}
    fieldnames = list(placeholder.keys())
    generated: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for room in list(rooms_data or []):
        template_id = str(getattr(room, "thermal_template_id", "") or "").strip()
        category = _sia2024_category_from_template(template_id)
        if not template_id or not category or template_id in seen:
            continue
        seen.add(template_id)
        row = {name: "" for name in fieldnames}
        row.update(
            {
                "thermal_template_id": template_id,
                "sia2024_category": category,
                "review_status": "pending",
                "source_document": "IESVE thermal-template name readback",
                "source_reference": "VERoomData thermal_template_id",
                "notes": (
                    "Category was explicitly encoded in the VE template name; "
                    "reviewer must confirm the intended room use before acceptance."
                ),
            }
        )
        generated.append(row)
    if not generated:
        return {"status": "NO_EXPLICIT_CATEGORY", "file": str(target), "row_count": 0}
    return _write_pending_rows(target, fieldnames, generated)


def prefill_lighting_control_evidence(
    rooms_data: Any,
    project_root: Path = PROJECT_ROOT,
    project_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Prefill VE lighting-control facts while leaving the SIA 387/4 class pending."""

    root = Path(project_root).resolve()
    label = _safe_filename_part(project_label or "VE_Project")
    target = (
        root
        / SIA4010_EVIDENCE_DIR
        / ("SIA3874_lighting_control_mapping_{}.csv".format(label))
    )
    rows, placeholder, status = _untouched_placeholder(
        target, ("ROOM_ID_OR_BLANK", "TEMPLATE_ID_OR_BLANK", "REVIEWER_TO_COMPLETE")
    )
    if placeholder is None:
        return {"status": status, "file": str(target), "row_count": len(rows)}
    fieldnames = list(placeholder.keys())
    generated: List[Dict[str, Any]] = []
    for room in list(rooms_data or []):
        profile = str(getattr(room, "daylight_dimming_profile", "") or "").strip()
        template_id = str(getattr(room, "thermal_template_id", "") or "").strip()
        room_id = str(getattr(room, "id", "") or "").strip()
        if not profile and not template_id:
            continue
        row = {name: "" for name in fieldnames}
        row.update(
            {
                "room_id": room_id,
                "thermal_template_id": template_id,
                "sia3874_control_type": "",
                "daylight_control": profile,
                "review_status": "pending",
                "source_document": "IESVE lighting-control readback",
                "source_reference": "VERoomData daylight_dimming_profile",
                "notes": (
                    "VE facts were prefilled; the SIA 387/4 control type remains "
                    "blank until confirmed from the controlled source."
                ),
            }
        )
        generated.append(row)
    if not generated:
        return {
            "status": "NO_LIGHTING_CONTROL_FACTS",
            "file": str(target),
            "row_count": 0,
        }
    return _write_pending_rows(target, fieldnames, generated)


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


def _copy_project_template(source: Path, target: Path, project_label: str) -> None:
    """Copy a UTF-8 CSV template while replacing controlled project tokens."""
    content = source.read_text(encoding="utf-8-sig")
    for token in PROJECT_LABEL_TOKENS:
        content = content.replace(token, project_label)
    target.write_text(content, encoding="utf-8", newline="")


def _safe_filename_part(value: object, fallback: str = "VE_Project") -> str:
    """Return a Windows-safe ASCII filename fragment."""
    text = str(value or "").strip() or fallback
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r'[<>:"/\\|?*]+', "_", text)
    text = re.sub(r"\s+", "_", text)
    text = text.strip("._ ")
    return (text or fallback)[:80]
