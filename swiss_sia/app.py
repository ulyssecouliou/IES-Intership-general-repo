"""Main entry point for the Swiss SIA Compliance Checker.

This module orchestrates VE data extraction, SIA checks, scoring, preflight
checks, and Excel report generation.
"""

from __future__ import annotations

import importlib
import logging
import os
import re
import shutil
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import iesve  # type: ignore
except Exception:  # pragma: no cover - only available inside IESVE.
    iesve = None

from . import config as config_module


# VE can keep config.py cached between Run clicks. Reload it before importing
# dependent modules so updated SIA values and report matrices are used.
config_module = importlib.reload(config_module)
OUTPUT_DIR = config_module.OUTPUT_DIR
EXCEL_REPORT_NAME = config_module.EXCEL_REPORT_NAME
CREATE_LATEST_REPORT_ALIAS = config_module.CREATE_LATEST_REPORT_ALIAS
SIA4010_REQUIRED_EVIDENCE = config_module.SIA4010_REQUIRED_EVIDENCE
SIA4010_EVIDENCE_DIR = config_module.SIA4010_EVIDENCE_DIR

def _reload_local_module(module_name: str) -> Any:
    """Import and reload one package module retained by the VE interpreter."""
    module = importlib.import_module(f"{__package__}.{module_name}")
    return importlib.reload(module)


# VE Scripts keeps a Python interpreter alive between Run clicks. Reload every
# provider before modules that import symbols from it, preventing mixed APIs
# after the workspace code changes while VE remains open.
data_extractor_module = _reload_local_module("data_extractor")
model_analyzer_module = _reload_local_module("model_analyzer")
rule_engine_module = _reload_local_module("rule_engine")
evidence_manager_module = _reload_local_module("evidence_manager")
evidence_pack_module = _reload_local_module("evidence_pack")
simulation_results_module = _reload_local_module("simulation_results")
_reload_local_module("value_integrity")

health_score_module = _reload_local_module("health_score")
sia380_checker_module = _reload_local_module("sia380_checker")
sia4010_checker_module = _reload_local_module("sia4010_checker")
sia4010_prevalidation_module = _reload_local_module("sia4010_prevalidation")
validation_class_scope_module = _reload_local_module("validation_class_scope")
reference_project_module = _reload_local_module("reference_project")
company_profile_module = _reload_local_module("company_profile")
compliance_report_pdf_module = _reload_local_module("compliance_report_pdf")
excel_report_module = _reload_local_module("excel_report")

VEDataExtractor = data_extractor_module.VEDataExtractor
ModelAnalyzer = model_analyzer_module.ModelAnalyzer
RuleEngine = rule_engine_module.RuleEngine
SIA3802Checker = sia380_checker_module.SIA3802Checker
SIA4010Checker = sia4010_checker_module.SIA4010Checker
build_sia4010_pdf_prevalidation = sia4010_prevalidation_module.build_sia4010_pdf_prevalidation
derive_validation_class_scope = validation_class_scope_module.derive_validation_class_scope
build_reference_project_specification = (
    reference_project_module.build_reference_project_specification
)
load_company_profile = company_profile_module.load_company_profile
render_compliance_report_pdf = (
    compliance_report_pdf_module.render_compliance_report_pdf
)
# The client chooses the report language; Swiss work runs in DE/FR/IT plus EN.
REPORT_LANGUAGE_ENV_VAR = "SIA_REPORT_LANGUAGE"
HealthScoreCalculator = health_score_module.HealthScoreCalculator
ExcelReportGenerator = excel_report_module.ExcelReportGenerator
scan_sia3802_justifications = evidence_manager_module.scan_sia3802_justifications
scan_sia3802_project_metadata = evidence_manager_module.scan_sia3802_project_metadata
find_accepted_project_metadata = evidence_manager_module.find_accepted_project_metadata
scan_sia3802_global_comparisons = evidence_manager_module.scan_sia3802_global_comparisons
find_accepted_global_comparison = evidence_manager_module.find_accepted_global_comparison
create_evidence_pack = evidence_pack_module.create_evidence_pack

REPORTS_DIR = os.path.join(str(PROJECT_ROOT), OUTPUT_DIR)
os.makedirs(REPORTS_DIR, exist_ok=True)


def _configure_logging() -> None:
    """Configure console logging and add the report log when it is writable."""
    handlers: List[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    try:
        handlers.insert(
            0,
            logging.FileHandler(
                os.path.join(REPORTS_DIR, "swiss_compliance_checker.log"),
                encoding="utf-8",
            ),
        )
    except OSError:
        # Documentation builds and concurrent reviewers may hold the file lock.
        pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


_configure_logging()
logger = logging.getLogger(__name__)


def _safe_filename_part(value: object, fallback: str = "VE_Project") -> str:
    """Return a Windows-safe filename fragment for VE project names."""
    text = str(value or "").strip() or fallback
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r'[<>:"/\\|?*]+', "_", text)
    text = re.sub(r"\s+", "_", text)
    text = text.strip("._ ")
    return (text or fallback)[:80]


def _object_label(value: object, fallback: str) -> str:
    """Extract a readable label from a VE API object without assuming its shape."""
    for attr in ("name", "name_attr", "id"):
        try:
            candidate = getattr(value, attr, None)
            if callable(candidate):
                candidate = candidate()
            if candidate:
                return str(candidate)
        except Exception:
            continue
    return fallback


def _build_unique_report_path(project_path: object, model: object = None) -> str:
    """Build a timestamped report path so VE runs do not overwrite each other."""
    project_name = os.path.basename(os.path.normpath(str(project_path or ""))) or "VE_Project"
    project_name = _safe_filename_part(project_name)
    model_name = _safe_filename_part(_object_label(model, "Model_01"), "Model_01")
    base_name, extension = os.path.splitext(EXCEL_REPORT_NAME)
    extension = extension or ".xlsx"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{base_name}__{project_name}__{model_name}__{timestamp}{extension}"
    candidate = os.path.join(REPORTS_DIR, filename)

    suffix = 2
    while os.path.exists(candidate):
        filename = f"{base_name}__{project_name}__{model_name}__{timestamp}_{suffix}{extension}"
        candidate = os.path.join(REPORTS_DIR, filename)
        suffix += 1
    return candidate


def _copy_latest_report_alias(source_path: str) -> Optional[str]:
    """Keep Swiss_Compliance_Report.xlsx as a convenience alias when possible."""
    latest_path = os.path.join(REPORTS_DIR, EXCEL_REPORT_NAME)
    if os.path.abspath(source_path) == os.path.abspath(latest_path):
        return latest_path

    temp_path = latest_path + ".tmp"
    try:
        shutil.copy2(source_path, temp_path)
        os.replace(temp_path, latest_path)
        return latest_path
    except PermissionError:
        logger.warning(
            "Could not update %s because the file is probably open. "
            "The timestamped report remains available: %s",
            latest_path,
            source_path,
        )
    except Exception as exc:
        logger.warning("Could not copy latest report alias %s: %s", latest_path, exc)

    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except Exception:
        pass
    return None


def _select_latest_aps_file(project: Any, aps_files: List[str]) -> Optional[str]:
    """Return the most recent APS file name from the active VE project's Vista folder."""
    if not aps_files:
        return None

    vista_dir = os.path.join(str(getattr(project, "path", "") or ""), "Vista")
    dated_files = []
    for file_name in aps_files:
        path = os.path.join(vista_dir, file_name)
        try:
            dated_files.append((os.path.getmtime(path), file_name))
        except Exception:
            dated_files.append((0.0, file_name))
    dated_files.sort(reverse=True)
    return dated_files[0][1]


def _rank_aps_files_by_mtime(project: Any, aps_files: List[str]) -> List[str]:
    """Return APS file names ordered from newest to oldest."""
    vista_dir = os.path.join(str(getattr(project, "path", "") or ""), "Vista")
    dated_files = []
    for file_name in aps_files:
        path = os.path.join(vista_dir, file_name)
        try:
            dated_files.append((os.path.getmtime(path), file_name))
        except Exception:
            dated_files.append((0.0, file_name))
    dated_files.sort(reverse=True)
    return [file_name for _mtime, file_name in dated_files]


def _weather_reference_label(value: Any) -> str:
    """Return a readable weather-file label from VE strings or proxy objects."""
    if value in (None, ""):
        return ""
    if isinstance(value, (str, bytes, os.PathLike)):
        return os.path.basename(os.fspath(value)) or str(value)
    for attr in ("path", "filename", "file_name", "name", "weather_file"):
        try:
            candidate = getattr(value, attr, None)
            if callable(candidate):
                candidate = candidate()
            if candidate not in (None, ""):
                return os.path.basename(os.fspath(candidate)) if isinstance(candidate, (str, bytes, os.PathLike)) else str(candidate)
        except Exception:
            continue
    return str(value)


def _current_project_weather_label(project: Any) -> str:
    """Return the current project weather file through documented VE APIs."""
    if iesve is not None:
        locator = None
        try:
            locator = iesve.VELocate()
            if locator.open_wea_data() != -1:
                location = locator.get() or {}
                label = _weather_reference_label(location.get("weather_file"))
                if label:
                    return label
        except Exception:
            pass
        finally:
            if locator is not None:
                try:
                    locator.close_wea_data()
                except Exception:
                    pass
    for attr in ("weather_file", "weather", "climate_file"):
        try:
            candidate = getattr(project, attr, None)
            if callable(candidate):
                candidate = candidate()
            label = _weather_reference_label(candidate)
            if label:
                return label
        except Exception:
            continue
    return ""


def _aps_matches_project_weather(aps_references: List[str], project_weather: str) -> bool:
    """Return true only when both weather references are known and match."""
    if not aps_references or not project_weather:
        return False
    project_weather_name = os.path.basename(project_weather).lower()
    return any(os.path.basename(reference).lower() == project_weather_name for reference in aps_references)


def _sum_numeric_rows(rows: List[Dict[str, Any]], key: str) -> Optional[float]:
    """Return the sum of numeric row values, or ``None`` when no value exists."""
    values = [float(row[key]) for row in rows if isinstance(row.get(key), (int, float))]
    return sum(values) if values else None


def _max_numeric_rows(rows: List[Dict[str, Any]], key: str) -> Optional[float]:
    """Return the maximum numeric row value, or ``None`` when no value exists."""
    values = [float(row[key]) for row in rows if isinstance(row.get(key), (int, float))]
    return max(values) if values else None


def _average_numeric_rows(rows: List[Dict[str, Any]], key: str) -> Optional[float]:
    """Return the arithmetic average of numeric row values, or ``None`` when absent."""
    values = [float(row[key]) for row in rows if isinstance(row.get(key), (int, float))]
    return sum(values) / len(values) if values else None


def _collect_dynamic_results(project: Any) -> Dict[str, Any]:
    """Read available APS/Vista room results when the VE ResultsReader is available."""
    summary: Dict[str, Any] = {
        "status": "NOT_CHECKABLE",
        "aps_files": [],
        "selected_aps_file": None,
        "project_weather_file": "",
        "selected_aps_weather_references": [],
        "skipped_aps_files": [],
        "rooms": [],
        "total_area_m2": 0.0,
        "total_heating_kwh": None,
        "total_cooling_kwh": None,
        "total_lighting_kwh": None,
        "total_fan_kwh": None,
        "total_pump_kwh": None,
        "total_auxiliary_kwh": None,
        "total_coil_heating_kwh": None,
        "total_coil_cooling_kwh": None,
        "heating_kwh_m2": None,
        "cooling_kwh_m2": None,
        "lighting_kwh_m2": None,
        "fan_kwh_m2": None,
        "pump_kwh_m2": None,
        "auxiliary_kwh_m2": None,
        "peak_co2_ppm": None,
        "average_co2_ppm": None,
        "peak_relative_humidity_percent": None,
        "average_relative_humidity_percent": None,
        "occupied_hours_above_26": None,
        "occupied_hours_above_27": None,
        "max_occupied_hours_above_sia180_upper": None,
        "max_occupied_hours_below_sia180_lower": None,
        "sia180_curve_room_count": 0,
        "annual_comfort_room_count": 0,
        "building_status": config_module.SIA3802_DYNAMIC_COMFORT.get(
            "building_status", "UNSPECIFIED"
        ),
        "building_status_source": "config fallback",
        "project_metadata_status": "NOT_PROVIDED",
        "global_reference_comparison_status": "NOT_PROVIDED",
        "global_reference_comparison": {},
        "reviewed_weather_basis": "",
        "reviewed_weather_file": "",
        "reviewed_weather_match_status": "NOT_CHECKABLE",
        "reviewed_location": "",
        "reviewed_altitude_m": "",
        "design_power_status": "NOT_CHECKABLE",
        "heating_design_power_w": None,
        "cooling_design_power_w": None,
        "notes": "",
    }

    try:
        project_label = os.path.basename(
            os.path.normpath(str(getattr(project, "path", "") or ""))
        ) or "VE_Project"
        metadata_scan = scan_sia3802_project_metadata(
            PROJECT_ROOT,
            SIA4010_EVIDENCE_DIR,
            project_label,
        )
        summary["project_metadata_status"] = metadata_scan.get("status", "NOT_PROVIDED")
        metadata = find_accepted_project_metadata(metadata_scan, project_label)
        if metadata:
            summary["building_status"] = metadata.get("building_status", "UNSPECIFIED")
            summary["building_status_source"] = (
                f"reviewed project metadata: {metadata.get('file', '')} row {metadata.get('row', '')}"
            )
            summary["reviewed_weather_basis"] = metadata.get("weather_basis", "")
            summary["reviewed_weather_file"] = metadata.get("weather_file", "")
            summary["reviewed_location"] = metadata.get("location", "")
            summary["reviewed_altitude_m"] = metadata.get("altitude_m", "")

        comparison_scan = scan_sia3802_global_comparisons(
            PROJECT_ROOT,
            SIA4010_EVIDENCE_DIR,
            project_label,
        )
        summary["global_reference_comparison_status"] = comparison_scan.get(
            "status", "NOT_PROVIDED"
        )
        comparison = find_accepted_global_comparison(
            comparison_scan,
            project_label,
        )
        if comparison:
            summary["global_reference_comparison"] = dict(comparison)

        project_weather = _current_project_weather_label(project)
        summary["project_weather_file"] = project_weather
        reviewed_weather = str(summary.get("reviewed_weather_file") or "")
        if reviewed_weather and project_weather:
            summary["reviewed_weather_match_status"] = (
                "MATCH"
                if _aps_matches_project_weather([reviewed_weather], project_weather)
                else "MISMATCH"
            )
        aps_files = simulation_results_module.list_aps_files(project)
        summary["aps_files"] = aps_files
        selected_aps = None
        selected_refs: List[str] = []
        results_file = None
        fallback_reader = None
        fallback_data = None
        ranked_aps = _rank_aps_files_by_mtime(project, aps_files)
        for candidate_aps in ranked_aps:
            aps_path = simulation_results_module.get_aps_path(project, candidate_aps)
            binary_refs = simulation_results_module.extract_epw_references_from_aps(aps_path)
            try:
                candidate_reader = simulation_results_module.open_results_reader(candidate_aps)
            except Exception as exc:
                summary["skipped_aps_files"].append({
                    "aps_file": candidate_aps,
                    "weather_references": binary_refs,
                    "reason": f"ResultsReader could not open the APS file: {exc}",
                })
                continue

            reader_weather = _weather_reference_label(
                getattr(candidate_reader, "weather_file", "")
            )
            authoritative_refs = [reader_weather] if reader_weather else binary_refs
            weather_matches = _aps_matches_project_weather(
                authoritative_refs,
                project_weather,
            )
            if not project_weather or weather_matches:
                if fallback_reader is not None:
                    try:
                        fallback_reader.close()
                    except Exception:
                        pass
                    fallback_reader = None
                selected_aps = candidate_aps
                selected_refs = authoritative_refs
                results_file = candidate_reader
                break

            if not authoritative_refs and fallback_reader is None:
                fallback_reader = candidate_reader
                fallback_data = (candidate_aps, authoritative_refs)
                continue

            try:
                candidate_reader.close()
            except Exception:
                pass
            summary["skipped_aps_files"].append({
                "aps_file": candidate_aps,
                "weather_references": authoritative_refs,
                "reason": f"ResultsReader weather does not match current project weather file {project_weather}.",
            })

        if results_file is None and fallback_reader is not None and fallback_data:
            selected_aps, selected_refs = fallback_data
            results_file = fallback_reader

        summary["selected_aps_file"] = selected_aps
        summary["selected_aps_weather_references"] = selected_refs
        if not selected_aps or results_file is None:
            summary["notes"] = "No APS file found in the project Vista folder."
            return summary
        try:
            room_results = simulation_results_module.collect_room_dynamic_results(results_file)
        finally:
            try:
                results_file.close()
            except Exception:
                pass
        rows = []
        for item in room_results:
            rows.append({
                "room_name": item.room_name,
                "room_id": item.room_id,
                "area_m2": item.area_m2,
                "heating_kwh": item.heating_kwh,
                "cooling_kwh": item.cooling_kwh,
                "lighting_kwh": item.lighting_kwh,
                "fan_kwh": item.fan_kwh,
                "pump_kwh": item.pump_kwh,
                "auxiliary_kwh": item.auxiliary_kwh,
                "coil_heating_kwh": item.coil_heating_kwh,
                "coil_cooling_kwh": item.coil_cooling_kwh,
                "peak_heating_w": item.peak_heating_w,
                "peak_cooling_w": item.peak_cooling_w,
                "peak_co2_ppm": item.peak_co2_ppm,
                "average_co2_ppm": item.average_co2_ppm,
                "peak_relative_humidity_percent": item.peak_relative_humidity_percent,
                "average_relative_humidity_percent": item.average_relative_humidity_percent,
                "occupied_hours_above_26": item.occupied_hours_above_26,
                "occupied_hours_above_27": item.occupied_hours_above_27,
                "occupied_hours_above_sia180_upper": item.occupied_hours_above_sia180_upper,
                "occupied_hours_below_sia180_lower": item.occupied_hours_below_sia180_lower,
                "annual_comfort_period_complete": item.annual_comfort_period_complete,
                "comfort_curve_source": item.comfort_curve_source,
                "source_notes": item.source_notes,
            })

        total_area = sum(float(row.get("area_m2") or 0.0) for row in rows)
        over_26_values = [
            float(row["occupied_hours_above_26"])
            for row in rows
            if isinstance(row.get("occupied_hours_above_26"), (int, float))
        ]
        over_27_values = [
            float(row["occupied_hours_above_27"])
            for row in rows
            if isinstance(row.get("occupied_hours_above_27"), (int, float))
        ]
        over_sia180_upper_values = [
            float(row["occupied_hours_above_sia180_upper"])
            for row in rows
            if isinstance(row.get("occupied_hours_above_sia180_upper"), (int, float))
        ]
        below_sia180_lower_values = [
            float(row["occupied_hours_below_sia180_lower"])
            for row in rows
            if isinstance(row.get("occupied_hours_below_sia180_lower"), (int, float))
        ]

        total_heating = _sum_numeric_rows(rows, "heating_kwh")
        total_cooling = _sum_numeric_rows(rows, "cooling_kwh")
        total_lighting = _sum_numeric_rows(rows, "lighting_kwh")
        total_fan = _sum_numeric_rows(rows, "fan_kwh")
        total_pump = _sum_numeric_rows(rows, "pump_kwh")
        total_auxiliary = _sum_numeric_rows(rows, "auxiliary_kwh")
        total_coil_heating = _sum_numeric_rows(rows, "coil_heating_kwh")
        total_coil_cooling = _sum_numeric_rows(rows, "coil_cooling_kwh")
        meaningful_fields = (
            "heating_kwh",
            "cooling_kwh",
            "lighting_kwh",
            "fan_kwh",
            "pump_kwh",
            "auxiliary_kwh",
            "peak_co2_ppm",
            "occupied_hours_above_26",
        )
        meaningful_result_count = sum(
            1
            for row in rows
            if any(row.get(field) is not None for field in meaningful_fields)
        )
        weather_confirmed = bool(
            project_weather
            and selected_refs
            and _aps_matches_project_weather(selected_refs, project_weather)
        )
        summary.update({
            "status": (
                "AVAILABLE"
                if rows and meaningful_result_count and weather_confirmed
                else ("PARTIAL" if rows and meaningful_result_count else "NOT_CHECKABLE")
            ),
            "rooms": rows,
            "total_area_m2": total_area,
            "total_heating_kwh": total_heating,
            "total_cooling_kwh": total_cooling,
            "total_lighting_kwh": total_lighting,
            "total_fan_kwh": total_fan,
            "total_pump_kwh": total_pump,
            "total_auxiliary_kwh": total_auxiliary,
            "total_coil_heating_kwh": total_coil_heating,
            "total_coil_cooling_kwh": total_coil_cooling,
            "heating_kwh_m2": total_heating / total_area if total_heating is not None and total_area > 0 else None,
            "cooling_kwh_m2": total_cooling / total_area if total_cooling is not None and total_area > 0 else None,
            "lighting_kwh_m2": total_lighting / total_area if total_lighting is not None and total_area > 0 else None,
            "fan_kwh_m2": total_fan / total_area if total_fan is not None and total_area > 0 else None,
            "pump_kwh_m2": total_pump / total_area if total_pump is not None and total_area > 0 else None,
            "auxiliary_kwh_m2": total_auxiliary / total_area if total_auxiliary is not None and total_area > 0 else None,
            "peak_co2_ppm": _max_numeric_rows(rows, "peak_co2_ppm"),
            "average_co2_ppm": _average_numeric_rows(rows, "average_co2_ppm"),
            "peak_relative_humidity_percent": _max_numeric_rows(rows, "peak_relative_humidity_percent"),
            "average_relative_humidity_percent": _average_numeric_rows(rows, "average_relative_humidity_percent"),
            "occupied_hours_above_26": sum(over_26_values) if over_26_values else None,
            "occupied_hours_above_27": sum(over_27_values) if over_27_values else None,
            "max_occupied_hours_above_sia180_upper": max(over_sia180_upper_values) if over_sia180_upper_values else None,
            "max_occupied_hours_below_sia180_lower": max(below_sia180_lower_values) if below_sia180_lower_values else None,
            "sia180_curve_room_count": len(over_sia180_upper_values),
            "annual_comfort_room_count": sum(1 for row in rows if row.get("annual_comfort_period_complete")),
            "notes": (
                "Read from IESVE ResultsReader with APS/project weather match."
                if weather_confirmed
                else "Results were read, but project/APS weather provenance is incomplete; dynamic compliance remains partial."
            ),
        })
    except Exception as exc:
        summary["status"] = "NOT_CHECKABLE"
        summary["notes"] = (
            "APS/Vista results could not be read by the current VE Python environment: "
            f"{exc}. If this mentions an EPW file, rerun the APS simulation after "
            "confirming the project weather file."
        )

    return summary


def _apply_dynamic_results_to_sia4010(
    sia4010_results: Dict[str, Any],
    dynamic_results: Dict[str, Any],
) -> None:
    """Expose APS/Vista indicators to readiness sheets without granting official validation."""
    sia4010_results["dynamic_results"] = dynamic_results
    if not isinstance(dynamic_results, dict):
        return

    energy = sia4010_results.setdefault("energy", {})
    if dynamic_results.get("heating_kwh_m2") is not None:
        energy["heating_demand"] = dynamic_results.get("heating_kwh_m2")
    if dynamic_results.get("cooling_kwh_m2") is not None:
        energy["cooling_demand"] = dynamic_results.get("cooling_kwh_m2")
    if dynamic_results.get("lighting_kwh_m2") is not None:
        energy["lighting_energy"] = dynamic_results.get("lighting_kwh_m2")
    if dynamic_results.get("fan_kwh_m2") is not None:
        energy["fan_energy"] = dynamic_results.get("fan_kwh_m2")
    if dynamic_results.get("pump_kwh_m2") is not None:
        energy["pump_energy"] = dynamic_results.get("pump_kwh_m2")
    if dynamic_results.get("auxiliary_kwh_m2") is not None:
        energy["auxiliary_energy"] = dynamic_results.get("auxiliary_kwh_m2")


def _attach_dynamic_results_to_rooms(
    rooms_data: List[Any],
    dynamic_results: Dict[str, Any],
) -> None:
    """Attach APS rows to normalized rooms for variant-readiness checks."""
    by_id = {
        str(row.get("room_id") or "").strip().lower(): row
        for row in (dynamic_results.get("rooms", []) or [])
        if isinstance(row, dict) and row.get("room_id") not in (None, "")
    }
    by_name = {
        str(row.get("room_name") or "").strip().lower(): row
        for row in (dynamic_results.get("rooms", []) or [])
        if isinstance(row, dict) and row.get("room_name")
    }
    for room in rooms_data:
        room_id = str(getattr(room, "id", "") or "").strip().lower()
        room_name = str(getattr(room, "name", "") or "").strip().lower()
        row = by_id.get(room_id) or by_name.get(room_name) or {}
        if row:
            row["window_operable"] = getattr(room, "window_operable", None)
        setattr(room, "dynamic_results", dict(row))


def _has_evidence_item(evidence: Dict[str, Any], evidence_item: str) -> bool:
    """Return whether an official evidence item has detected files."""
    if not isinstance(evidence, dict) or not evidence:
        return False

    known_keys = {
        SIA4010_REQUIRED_EVIDENCE[0]: "official_test_specifications",
        SIA4010_REQUIRED_EVIDENCE[1]: "official_evaluation_workbooks",
        SIA4010_REQUIRED_EVIDENCE[2]: "candidate_results",
        SIA4010_REQUIRED_EVIDENCE[3]: "reference_comparisons",
        SIA4010_REQUIRED_EVIDENCE[4]: "validation_class_confirmation",
    }
    structured_value = evidence.get(known_keys.get(evidence_item, evidence_item))
    if isinstance(structured_value, dict):
        files = structured_value.get("files", []) or []
        return bool(structured_value.get("present") and files)

    exact_value = evidence.get(evidence_item)
    if isinstance(exact_value, dict):
        files = exact_value.get("files", []) or []
        return bool(exact_value.get("present") and files)
    if isinstance(exact_value, bool):
        return exact_value

    def normalize(value: str) -> str:
        """Normalize evidence labels to alphanumeric lowercase keys."""
        return "".join(ch.lower() for ch in str(value) if ch.isalnum())

    target = normalize(evidence_item)
    for key, value in evidence.items():
        key_norm = normalize(key)
        if target in key_norm or key_norm in target:
            if isinstance(value, dict):
                files = value.get("files", []) or []
                return bool(value.get("present") and files)
            return bool(value)
    return False


def _build_preflight_checks(
    project: Any,
    rooms_data: List[Any],
    report_path: str,
    sia4010_results: Dict[str, Any],
    justification_results: Optional[Dict[str, Any]] = None,
    extraction_diagnostics: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Create auditable execution checks for the VE Run-button workflow."""
    surfaces = [surface for room in rooms_data for surface in getattr(room, "surfaces", [])]
    openings = [opening for room in rooms_data for opening in getattr(room, "openings", [])]
    external_surfaces = [surface for surface in surfaces if getattr(surface, "is_external", False)]
    external_openings = [opening for opening in openings if getattr(opening, "is_external", False)]
    evidence = sia4010_results.get("evidence", {}) or {}
    justification_results = justification_results or {}
    evidence_files = evidence.get("files", []) or []
    classified_evidence_count = int(evidence.get("classified_file_count", 0) or 0)
    evidence_present = sum(
        1 for item in SIA4010_REQUIRED_EVIDENCE
        if _has_evidence_item(evidence, item)
    )
    dynamic_results = sia4010_results.get("dynamic_results", {}) or {}
    dynamic_status = str(dynamic_results.get("status", "NOT_CHECKABLE") or "NOT_CHECKABLE")
    dynamic_preflight_status = "PASS" if dynamic_status == "AVAILABLE" else ("WARNING" if dynamic_status == "PARTIAL" else "NOT_CHECKABLE")
    project_weather = dynamic_results.get("project_weather_file") or "Not exposed by VE"
    selected_aps_weather = ", ".join(dynamic_results.get("selected_aps_weather_references", []) or []) or "No EPW reference detected in APS"
    skipped_aps_count = len(dynamic_results.get("skipped_aps_files", []) or [])
    report_dir = os.path.dirname(os.path.abspath(report_path))
    project_path = str(getattr(project, "path", "") or "")
    project_path_norm = project_path.replace("/", "\\").lower()
    is_temp_veproj = "\\appdata\\local\\temp\\veproj\\" in project_path_norm
    temp_project_status = (
        "FAIL"
        if is_temp_veproj and not rooms_data
        else ("WARNING" if is_temp_veproj else "PASS")
    )
    body_diagnostics = extraction_diagnostics or {}
    raw_body_count = int(body_diagnostics.get("raw_body_count", 0) or 0)
    relevant_body_count = int(body_diagnostics.get("relevant_body_count", 0) or 0)
    discarded_body_count = int(body_diagnostics.get("discarded_body_count", 0) or 0)
    discarded_sample = body_diagnostics.get("discarded_sample", []) or []
    model_count = int(body_diagnostics.get("model_count", 0) or 0)
    selected_model_index = int(body_diagnostics.get("selected_model_index", 0) or 0)
    model_summaries = body_diagnostics.get("model_summaries", []) or []
    model_summary = "; ".join(
        (
            f"m{item.get('index', '')}"
            f":{item.get('model_type', '') or 'unknown'}"
            f" raw={item.get('raw_body_count', 0)}"
            f" retained={item.get('relevant_body_count', 0)}"
        )
        for item in model_summaries[:5]
        if isinstance(item, dict)
    )
    discarded_summary = "; ".join(
        f"{item.get('id', '')}:{item.get('type', '')}/{item.get('subtype', '')}"
        for item in discarded_sample
        if isinstance(item, dict)
    )
    body_diagnostic_status = (
        "PASS"
        if relevant_body_count > 0
        else ("WARNING" if raw_body_count > 0 else "FAIL")
    )

    return [
        {
            "status": "PASS" if project else "FAIL",
            "check": "Active VE project",
            "observed": project_path or "No active project",
            "why": "The script must run from the correct open VE project.",
            "action": "Open the target client VE project before pressing Run.",
            "owner": "Model reviewer",
            "source": "iesve.VEProject.get_current_project",
        },
        {
            "status": temp_project_status,
            "check": "Saved project path, not temporary VE copy",
            "observed": project_path or "No active project",
            "why": "Temporary VEPROJ copies may not expose rooms, surfaces or Vista files reliably through the IESVE API.",
            "action": "Open the saved client project folder in VE, for example the ZOER_32_C1 project folder, then rerun from the VE Run button.",
            "owner": "Model reviewer",
            "source": "VEProject.path",
        },
        {
            "status": body_diagnostic_status,
            "check": "VE body extraction diagnostic",
            "observed": (
                f"models={model_count}, selected={selected_model_index}; "
                f"{raw_body_count} raw body(s), {relevant_body_count} retained, "
                f"{discarded_body_count} filtered"
                + (f"; model scan: {model_summary}" if model_summary else "")
                + (f"; sample filtered: {discarded_summary}" if discarded_summary else "")
            ),
            "why": "Separates an empty VE model/API response from an over-restrictive body filter.",
            "action": "If raw bodies exist but none are retained, inspect body type/subtype mappings; if raw bodies are zero, open the correct model/project.",
            "owner": "Developer / model reviewer",
            "source": "VEModel.get_bodies raw diagnostics",
        },
        {
            "status": "PASS" if rooms_data else "FAIL",
            "check": "Thermal rooms extracted",
            "observed": f"{len(rooms_data)} room(s)",
            "why": "No SIA model check is meaningful without rooms/zones.",
            "action": "Check room type/subtype and rerun the script.",
            "owner": "Model reviewer",
            "source": "VEModel.get_bodies",
        },
        {
            "status": "PASS" if external_surfaces else "FAIL",
            "check": "External envelope extracted",
            "observed": f"{len(external_surfaces)} external surface(s)",
            "why": "SIA 380/2 envelope checks depend on external surfaces and constructions.",
            "action": "Check surface types, adjacencies and CDB construction assignments.",
            "owner": "Model reviewer",
            "source": "VESurface.get_areas / get_constructions",
        },
        {
            "status": "PASS" if external_openings else "WARNING",
            "check": "External openings extracted",
            "observed": f"{len(external_openings)} external opening(s)",
            "why": "Window Uw and g-value checks need external glazing/openings.",
            "action": "Confirm whether the model should contain external windows; if yes, check openings.",
            "owner": "Model reviewer",
            "source": "VESurface.get_openings",
        },
        {
            "status": "PASS" if os.path.isdir(report_dir) and os.access(report_dir, os.W_OK) else "FAIL",
            "check": "Report folder writable",
            "observed": report_dir,
            "why": "VE must be able to write the timestamped Excel report.",
            "action": "Close open Excel files or fix folder permissions.",
            "owner": "Model reviewer",
            "source": "reports directory",
        },
        {
            "status": "PASS" if getattr(excel_report_module, "USE_XLSXWRITER", False) else "FAIL",
            "check": "Excel writer available",
            "observed": f"xlsxwriter available={getattr(excel_report_module, 'USE_XLSXWRITER', False)}",
            "why": "The VE Run workflow needs xlsxwriter to generate the client report.",
            "action": "Install/use the VE Python environment that exposes xlsxwriter.",
            "owner": "Developer",
            "source": "excel_report.py",
        },
        {
            "status": dynamic_preflight_status,
            "check": "APS/Vista dynamic results",
            "observed": (
                f"status={dynamic_status}; selected APS="
                f"{dynamic_results.get('selected_aps_file') or 'not selected'}; "
                f"{len(dynamic_results.get('aps_files', []) or [])} APS file(s) detected; "
                f"project weather={project_weather}; APS weather={selected_aps_weather}; "
                f"skipped stale APS={skipped_aps_count}"
            ),
            "why": "SIA 380/2 dynamic checks and SIA 4010 tests need hourly/sub-hourly simulation outputs.",
            "action": "If the APS references an old EPW, rerun the APS simulation after saving the current VE project weather file.",
            "owner": "Model reviewer",
            "source": "IESVE ResultsReader / Vista APS",
        },
        {
            "status": "PASS" if classified_evidence_count else "NOT_CHECKABLE",
            "check": "SIA 4010 classified evidence files",
            "observed": (
                f"{classified_evidence_count} classified evidence file(s), "
                f"{len(evidence_files)} total file(s) in "
                f"{evidence.get('evidence_dir', 'sia4010_evidence')}"
            ),
            "why": "SIA 4010 is not a building threshold; it requires official validation evidence.",
            "action": "Place official SIA test specs, Excel evaluation files and candidate results in sia4010_evidence.",
            "owner": "Compliance reviewer",
            "source": "sia4010_evidence",
        },
        {
            "status": "PASS" if evidence_present == len(SIA4010_REQUIRED_EVIDENCE) else "NOT_CHECKABLE",
            "check": "SIA 4010 official evidence completeness",
            "observed": f"{evidence_present}/{len(SIA4010_REQUIRED_EVIDENCE)} evidence families detected",
            "why": "The report must not claim SIA 4010 validation until official evidence is complete.",
            "action": "Complete all evidence families before any official PASS claim.",
            "owner": "Compliance reviewer",
            "source": "SIA 4010 evidence scan",
        },
        {
            "status": (
                "PASS"
                if int(justification_results.get("accepted_count", 0) or 0)
                else ("WARNING" if int(justification_results.get("record_count", 0) or 0) else "INFO")
            ),
            "check": "SIA 380/2 reviewer justifications",
            "observed": (
                f"{int(justification_results.get('accepted_count', 0) or 0)} accepted / "
                f"{int(justification_results.get('record_count', 0) or 0)} provided record(s) in "
                f"{justification_results.get('evidence_dir', SIA4010_EVIDENCE_DIR)}"
            ),
            "why": "Reviewer-signed evidence can justify a retained model value without hiding the original fail condition.",
            "action": "Use SIA3802_justification_*.csv records with reviewer, source and accepted review status for auditable exceptions.",
            "owner": "Compliance reviewer",
            "source": "SIA 380/2 justification scan",
        },
    ]


def main():
    """Run the VE extraction, SIA checks, scoring, and Excel report generation."""
    try:
        logger.info("Starting VE model analysis.")

        if iesve is None:
            raise RuntimeError("The iesve Python module is only available inside IESVE.")

        project = iesve.VEProject.get_current_project()
        if not project:
            raise RuntimeError("No active VE project found. Please open a project in IESVE.")

        logger.info("Loaded VE project: %s", project.path)
        project_label = os.path.basename(
            os.path.normpath(str(getattr(project, "path", "") or ""))
        ) or "VE_Project"

        logger.info("Extracting VE model data.")
        data_extractor = VEDataExtractor(project)
        model_analyzer = ModelAnalyzer(data_extractor)
        logger.info("Loaded model_analyzer from: %s", model_analyzer_module.__file__)

        rooms_data = model_analyzer.analyze_all_rooms()

        logger.info("Collecting APS/Vista dynamic results where available.")
        dynamic_results = _collect_dynamic_results(project)
        _attach_dynamic_results_to_rooms(rooms_data, dynamic_results)
        logger.info(
            "APS/Vista dynamic result status: %s (%s)",
            dynamic_results.get("status"),
            dynamic_results.get("selected_aps_file") or "no APS selected",
        )

        logger.info("Running SIA 380/2 checks.")
        sia3802_checker = SIA3802Checker(model_analyzer, RuleEngine())
        sia3802_results = sia3802_checker.check_all(
            rooms_data=rooms_data,
            dynamic_results=dynamic_results,
        )

        logger.info("Preparing the SIA 380/2 reference-project input specification.")
        reference_specification = build_reference_project_specification(
            rooms_data,
            model_analyzer,
        )
        sia3802_results["reference_project"] = reference_specification.to_dict()
        logger.info(
            "Reference-project specification: %s (%s substitutions, %s blockers)",
            reference_specification.status,
            len(reference_specification.substitutions),
            len(reference_specification.blockers),
        )

        logger.info("Running SIA 4010 readiness checks.")
        sia4010_checker = SIA4010Checker(
            model_analyzer,
            RuleEngine(),
            project_label=project_label,
        )
        sia4010_results = sia4010_checker.check_all(rooms_data=rooms_data)
        _apply_dynamic_results_to_sia4010(sia4010_results, dynamic_results)

        logger.info("Deriving the SIA 4010 validation-class scope of this model.")
        class_scope = derive_validation_class_scope(rooms_data)
        sia4010_results["required_class_scope"] = class_scope.to_dict()
        logger.info(
            "Required validation class: %s (conservative: %s, status %s)",
            class_scope.required_class or "not derived",
            class_scope.conservative_class or "not derived",
            class_scope.status,
        )

        logger.info("Scanning SIA 380/2 reviewer justifications.")
        justification_results = scan_sia3802_justifications(
            PROJECT_ROOT,
            SIA4010_EVIDENCE_DIR,
            project_label,
        )
        sia3802_results["justifications"] = justification_results
        logger.info(
            "SIA 380/2 justification status: %s (%s accepted / %s provided)",
            justification_results.get("status"),
            justification_results.get("accepted_count"),
            justification_results.get("record_count"),
        )

        logger.info("Calculating scores.")
        score_calculator = HealthScoreCalculator()
        score_result = score_calculator.calculate_scores(sia3802_results, sia4010_results)

        logger.info("Generating Excel report.")
        unique_report_path = _build_unique_report_path(project.path, data_extractor.model)
        report_generator = ExcelReportGenerator(
            output_path=unique_report_path,
            model_analyzer=model_analyzer,
        )
        logger.info("Running SIA 4010 PDF-based prevalidation.")
        sia4010_results["prevalidation"] = build_sia4010_pdf_prevalidation(
            rooms_data,
            sia3802_results,
            sia4010_results,
            dynamic_results,
        )
        extraction_diagnostics = data_extractor.get_body_extraction_diagnostics()
        preflight_checks = _build_preflight_checks(
            project,
            rooms_data,
            unique_report_path,
            sia4010_results,
            justification_results,
            extraction_diagnostics,
        )
        report_generator.generate_report(
            score_result,
            sia3802_results,
            sia4010_results,
            rooms_data,
            preflight_checks,
            dynamic_results,
            justification_results,
        )
        latest_report_path = (
            _copy_latest_report_alias(report_generator.output_path)
            if CREATE_LATEST_REPORT_ALIAS
            else None
        )

        logger.info("Rendering the company SIA compliance report (PDF).")
        compliance_pdf_path = None
        try:
            company_profile = load_company_profile(PROJECT_ROOT)
            compliance_pdf_path = render_compliance_report_pdf(
                os.path.splitext(unique_report_path)[0] + ".pdf",
                project_label=project_label,
                rooms_data=rooms_data,
                sia3802_results=sia3802_results,
                sia4010_results=sia4010_results,
                score_result=score_result,
                profile=company_profile,
                project_root=PROJECT_ROOT,
                language=os.environ.get(REPORT_LANGUAGE_ENV_VAR, "") or "en",
                model_name=_object_label(data_extractor.model, ""),
            )
            logger.info("Compliance report PDF: %s", compliance_pdf_path)
            if not company_profile.is_configured:
                logger.warning(
                    "No config/company_profile.json found: the PDF letterhead and "
                    "signature block are printed as not specified."
                )
        except Exception as exc:
            # The PDF is an additional deliverable; never lose the workbook run.
            logger.error("Could not render the compliance report PDF: %s", exc)

        evidence_pack_result = None
        try:
            evidence_pack_result = create_evidence_pack(
                project_root=PROJECT_ROOT,
                report_path=Path(report_generator.output_path),
                latest_report_path=Path(latest_report_path) if latest_report_path else None,
                sia4010_results=sia4010_results,
                preflight_checks=preflight_checks,
                evidence_dir_name=SIA4010_EVIDENCE_DIR,
                project_label=project_label,
            )
            logger.info(
                "Generated evidence pack ZIP: %s (%s included file(s))",
                evidence_pack_result.get("path"),
                evidence_pack_result.get("file_count"),
            )
        except Exception as exc:
            logger.warning(
                "Excel report was generated, but the optional evidence pack ZIP could not be created: %s",
                exc,
            )

        logger.info("Analysis completed successfully.")
        logger.info(
            "SIA 380/2 automated precheck indicator: %.1f/100",
            score_result.compliance_score,
        )
        logger.info("Health Score: %.1f/100", score_result.health_score)
        logger.info("Generated Excel report: %s", report_generator.output_path)
        if latest_report_path:
            logger.info("Updated latest report alias: %s", latest_report_path)
        else:
            logger.info("Latest report alias disabled; only the timestamped workbook was generated.")
        if evidence_pack_result:
            logger.info("Generated evidence pack: %s", evidence_pack_result.get("path"))

        critical_alerts = [
            alert for alert in score_result.alerts
            if alert.severity.value == "Critical"
        ]
        if critical_alerts:
            logger.warning("%s critical issue(s) detected:", len(critical_alerts))
            for alert in critical_alerts:
                logger.warning(" - %s (Recommendation: %s)", alert.description, alert.recommendation)

        logger.info("Detailed scores by category:")
        for category, score in score_result.detailed_scores.items():
            logger.info(" - %s: %.1f/100", category, score)

    except Exception as exc:
        logger.error("Critical error during analysis: %s", exc)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
