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

from . import data_extractor as data_extractor_module
from . import excel_report as excel_report_module
from . import health_score as health_score_module
from . import model_analyzer as model_analyzer_module
from . import rule_engine as rule_engine_module
from . import sia380_checker as sia380_checker_module
from . import sia4010_checker as sia4010_checker_module
from . import simulation_results as simulation_results_module


# VE Scripts can keep a Python interpreter alive between Run clicks. Force local
# modules to reload so the button always uses the latest workspace code.
data_extractor_module = importlib.reload(data_extractor_module)
model_analyzer_module = importlib.reload(model_analyzer_module)
rule_engine_module = importlib.reload(rule_engine_module)
sia380_checker_module = importlib.reload(sia380_checker_module)
sia4010_checker_module = importlib.reload(sia4010_checker_module)
health_score_module = importlib.reload(health_score_module)
excel_report_module = importlib.reload(excel_report_module)
simulation_results_module = importlib.reload(simulation_results_module)

VEDataExtractor = data_extractor_module.VEDataExtractor
ModelAnalyzer = model_analyzer_module.ModelAnalyzer
RuleEngine = rule_engine_module.RuleEngine
SIA3802Checker = sia380_checker_module.SIA3802Checker
SIA4010Checker = sia4010_checker_module.SIA4010Checker
HealthScoreCalculator = health_score_module.HealthScoreCalculator
ExcelReportGenerator = excel_report_module.ExcelReportGenerator

REPORTS_DIR = os.path.join(str(PROJECT_ROOT), OUTPUT_DIR)
os.makedirs(REPORTS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(REPORTS_DIR, "swiss_compliance_checker.log"),
            encoding="utf-8",
        ),
        logging.StreamHandler(sys.stdout),
    ],
)
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


def _collect_dynamic_results(project: Any) -> Dict[str, Any]:
    """Read available APS/Vista room results when the VE ResultsReader is available."""
    summary: Dict[str, Any] = {
        "status": "NOT_CHECKABLE",
        "aps_files": [],
        "selected_aps_file": None,
        "rooms": [],
        "total_area_m2": 0.0,
        "total_heating_kwh": None,
        "total_cooling_kwh": None,
        "heating_kwh_m2": None,
        "cooling_kwh_m2": None,
        "occupied_hours_above_26": None,
        "occupied_hours_above_27": None,
        "notes": "",
    }

    try:
        aps_files = simulation_results_module.list_aps_files(project)
        summary["aps_files"] = aps_files
        selected_aps = _select_latest_aps_file(project, aps_files)
        summary["selected_aps_file"] = selected_aps
        if not selected_aps:
            summary["notes"] = "No APS file found in the project Vista folder."
            return summary

        results_file = simulation_results_module.open_results_reader(selected_aps)
        room_results = simulation_results_module.collect_room_dynamic_results(results_file)
        rows = []
        for item in room_results:
            rows.append({
                "room_name": item.room_name,
                "room_id": item.room_id,
                "area_m2": item.area_m2,
                "heating_kwh": item.heating_kwh,
                "cooling_kwh": item.cooling_kwh,
                "peak_heating_w": item.peak_heating_w,
                "peak_cooling_w": item.peak_cooling_w,
                "occupied_hours_above_26": item.occupied_hours_above_26,
                "occupied_hours_above_27": item.occupied_hours_above_27,
                "source_notes": item.source_notes,
            })

        total_area = sum(float(row.get("area_m2") or 0.0) for row in rows)
        heating_values = [
            float(row["heating_kwh"])
            for row in rows
            if isinstance(row.get("heating_kwh"), (int, float))
        ]
        cooling_values = [
            float(row["cooling_kwh"])
            for row in rows
            if isinstance(row.get("cooling_kwh"), (int, float))
        ]
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

        total_heating = sum(heating_values) if heating_values else None
        total_cooling = sum(cooling_values) if cooling_values else None
        summary.update({
            "status": "AVAILABLE" if rows else "PARTIAL",
            "rooms": rows,
            "total_area_m2": total_area,
            "total_heating_kwh": total_heating,
            "total_cooling_kwh": total_cooling,
            "heating_kwh_m2": total_heating / total_area if total_heating is not None and total_area > 0 else None,
            "cooling_kwh_m2": total_cooling / total_area if total_cooling is not None and total_area > 0 else None,
            "occupied_hours_above_26": sum(over_26_values) if over_26_values else None,
            "occupied_hours_above_27": sum(over_27_values) if over_27_values else None,
            "notes": "Read from IESVE ResultsReader.",
        })
    except Exception as exc:
        summary["status"] = "NOT_CHECKABLE"
        summary["notes"] = f"APS/Vista results could not be read by the current VE Python environment: {exc}"

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


def _has_evidence_item(evidence: Dict[str, Any], evidence_item: str) -> bool:
    """Return whether an evidence item is present in the SIA 4010 scan result."""
    if not isinstance(evidence, dict) or not evidence:
        return False

    def normalize(value: str) -> str:
        return "".join(ch.lower() for ch in str(value) if ch.isalnum())

    target = normalize(evidence_item)
    for key, value in evidence.items():
        key_norm = normalize(key)
        if target in key_norm or key_norm in target:
            return bool(value)
    return False


def _build_preflight_checks(
    project: Any,
    rooms_data: List[Any],
    report_path: str,
    sia4010_results: Dict[str, Any],
    extraction_diagnostics: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Create auditable execution checks for the VE Run-button workflow."""
    surfaces = [surface for room in rooms_data for surface in getattr(room, "surfaces", [])]
    openings = [opening for room in rooms_data for opening in getattr(room, "openings", [])]
    external_surfaces = [surface for surface in surfaces if getattr(surface, "is_external", False)]
    external_openings = [opening for opening in openings if getattr(opening, "is_external", False)]
    evidence = sia4010_results.get("evidence", {}) or {}
    evidence_files = evidence.get("files", []) or []
    classified_evidence_count = int(evidence.get("classified_file_count", 0) or 0)
    evidence_present = sum(
        1 for item in SIA4010_REQUIRED_EVIDENCE
        if _has_evidence_item(evidence, item)
    )
    dynamic_results = sia4010_results.get("dynamic_results", {}) or {}
    dynamic_status = str(dynamic_results.get("status", "NOT_CHECKABLE") or "NOT_CHECKABLE")
    dynamic_preflight_status = "PASS" if dynamic_status == "AVAILABLE" else ("WARNING" if dynamic_status == "PARTIAL" else "NOT_CHECKABLE")
    report_dir = os.path.dirname(os.path.abspath(report_path))
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
            "observed": str(getattr(project, "path", "") or "No active project"),
            "why": "The script must run from the correct open VE project.",
            "action": "Open the target client VE project before pressing Run.",
            "owner": "Model reviewer",
            "source": "iesve.VEProject.get_current_project",
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
                f"{len(dynamic_results.get('aps_files', []) or [])} APS file(s) detected"
            ),
            "why": "SIA 380/2 dynamic checks and SIA 4010 tests need hourly/sub-hourly simulation outputs.",
            "action": "Run the APS simulation in VE and keep the APS/Vista result file in the project Vista folder.",
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

        logger.info("Extracting VE model data.")
        data_extractor = VEDataExtractor(project)
        model_analyzer = ModelAnalyzer(data_extractor)
        logger.info("Loaded model_analyzer from: %s", model_analyzer_module.__file__)

        logger.info("Running SIA 380/2 checks.")
        sia3802_checker = SIA3802Checker(model_analyzer, RuleEngine())
        sia3802_results = sia3802_checker.check_all()

        logger.info("Running SIA 4010 readiness checks.")
        sia4010_checker = SIA4010Checker(model_analyzer, RuleEngine())
        sia4010_results = sia4010_checker.check_all()

        logger.info("Collecting APS/Vista dynamic results where available.")
        dynamic_results = _collect_dynamic_results(project)
        _apply_dynamic_results_to_sia4010(sia4010_results, dynamic_results)
        logger.info(
            "APS/Vista dynamic result status: %s (%s)",
            dynamic_results.get("status"),
            dynamic_results.get("selected_aps_file") or "no APS selected",
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
        rooms_data = model_analyzer.analyze_all_rooms()
        extraction_diagnostics = data_extractor.get_body_extraction_diagnostics()
        preflight_checks = _build_preflight_checks(
            project,
            rooms_data,
            unique_report_path,
            sia4010_results,
            extraction_diagnostics,
        )
        report_generator.generate_report(
            score_result,
            sia3802_results,
            sia4010_results,
            rooms_data,
            preflight_checks,
            dynamic_results,
        )
        latest_report_path = (
            _copy_latest_report_alias(report_generator.output_path)
            if CREATE_LATEST_REPORT_ALIAS
            else None
        )

        logger.info("Analysis completed successfully.")
        logger.info(
            "SIA 380/2 automated compliance indicator: %.1f/100",
            score_result.compliance_score,
        )
        logger.info("Health Score: %.1f/100", score_result.health_score)
        logger.info("Generated Excel report: %s", report_generator.output_path)
        if latest_report_path:
            logger.info("Updated latest report alias: %s", latest_report_path)
        else:
            logger.info("Latest report alias disabled; only the timestamped workbook was generated.")

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
