"""Excel report generator for the Swiss Compliance Checker.

This module uses xlsxwriter to create a professional Excel workbook inside the
IESVE Python scripting environment.
"""

import logging
import os
from collections import Counter
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import xlsxwriter

    USE_XLSXWRITER = True
except ImportError:
    USE_XLSXWRITER = False
    logging.warning("xlsxwriter is not available.")

from ui import design
from . import report_style
from .config import (
    OUTPUT_DIR,
    EXCEL_REPORT_NAME,
    SIA_DATA_COVERAGE_MATRIX,
    SIA_COMPLIANCE_REQUIREMENT_MATRIX,
    SIA3802_LIMIT_VALUES,
    SIA4010_EVIDENCE_REQUIREMENTS,
    SIA4010_REQUIRED_EVIDENCE,
    SIA4010_SYSTEM_REQUIREMENT_SOURCES,
    SIA4010_TEST_ALIAS_LABELS,
    SIA4010_TEST_ALIAS_ORDER,
    SIA4010_TEST_ALIAS_TO_BASE_TEST,
    SIA4010_TEST_CLASS_COVERAGE,
    SIA4010_TEST_READINESS_REQUIREMENTS,
    SIA4010_VALIDATED_SOFTWARE_REGISTER,
    SIA4010_VALIDATION_CLASS_DETAILS,
    SIA4010_VALIDATION_CLASSES,
    SIA4010_IESVE_REGISTER_STATUS,
    SIA3802_NAVIGATOR_BACKLOG,
)
from .health_score import ScoreResult
from .rule_engine import Alert, Severity
from .evidence_manager import describe_justification, find_accepted_justification
from .model_analyzer import has_active_solar_protection
from .compliance_verdict import build_compliance_verdict
from .client_report_context import building_strategy_summary, building_strategy_text
from .compliance_criteria import CLIENT_CAPABILITY_GUIDE
from .assessment_governance import (
    BLOCKED as GOVERNANCE_BLOCKED,
    DOCUMENTED as GOVERNANCE_DOCUMENTED,
    RESERVE as GOVERNANCE_RESERVE,
    evaluate_assessment_governance,
    governance_summary,
    legal_wording,
    report_text,
    status_label as governance_status_label,
)
from .reference_model.sia4010.ui_translations import normalize_language, translate

#: The seven formats shared across the workbook, in the IES house style.
# They lived in config.EXCEL_FORMATS, which put presentation inside the
# normative configuration module and shipped a blue from no IES palette.
SHARED_FORMATS = report_style.xw_shared_roles()

logger = logging.getLogger(__name__)


class ExcelReportGenerator:
    """Generate the professional Swiss compliance Excel workbook."""

    def __init__(
        self,
        output_path: str = None,
        model_analyzer: Any = None,
        report_context: Any = None,
    ):
        """Initialize the Excel report generator."""
        self.output_path = output_path or os.path.join(OUTPUT_DIR, EXCEL_REPORT_NAME)
        self.model_analyzer = model_analyzer
        self.report_context = report_context
        self.report_language = normalize_language(self._context_value("language", "en"))
        self.workbook = None
        self.use_xlsxwriter = USE_XLSXWRITER
        self.sia3802_justifications: Dict[str, Any] = {}
        # Whether the workbook carries the SIA 4010 toolchain-validation
        # material. The client SIA 380/2 report sets this False: SIA 4010
        # validates the software, not the client building, so its sheets and
        # cards on a client report can only be misread. See set at report time.
        self.include_sia4010 = True
        self._active_sections = self._REPORT_SECTIONS

        if not self.use_xlsxwriter:
            raise RuntimeError(
                "xlsxwriter is not available. The Excel report cannot be generated inside the VE environment."
            )

        self._init_workbook()

    def _init_workbook(self):
        """Initialize the Excel workbook."""
        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            output_dir = os.path.dirname(os.path.abspath(self.output_path))
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            self.workbook = xlsxwriter.Workbook(self.output_path)
            logger.info(f"Excel workbook created: {self.output_path}")
        except Exception as e:
            logger.error(f"Error while creating the Excel workbook: {e}")
            raise

    def generate_report(
        self,
        score_result: ScoreResult,
        sia3802_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
        rooms_data: Optional[List[Any]] = None,
        preflight_checks: Optional[List[Dict[str, Any]]] = None,
        dynamic_results: Optional[Dict[str, Any]] = None,
        justification_results: Optional[Dict[str, Any]] = None,
        include_sia4010: bool = True,
    ):
        """Generate the Excel report.

        Args:
            include_sia4010: When False, the workbook is a SIA 380/2-only client
                report: the four dedicated SIA 4010 sheets are omitted and the
                SIA 4010 fragments woven into shared sheets are suppressed, so
                nothing about the software's validation state can be misread as
                a statement about the client building. A single credential line
                on the cover points to the separate Anwenderbericht. Defaults to
                True so existing callers keep the full combined workbook.
        """
        try:
            self._generate_report_xlsxwriter(
                score_result,
                sia3802_results,
                sia4010_results,
                rooms_data,
                preflight_checks,
                dynamic_results,
                justification_results,
                include_sia4010,
            )
            logger.info(f"Excel report generated successfully: {self.output_path}")
        except Exception as e:
            logger.error(f"Error while generating the Excel report: {e}")
            if self.workbook:
                self.workbook.close()
            raise

    def _generate_report_xlsxwriter(
        self,
        score_result: ScoreResult,
        sia3802_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
        rooms_data: Optional[List[Any]] = None,
        preflight_checks: Optional[List[Dict[str, Any]]] = None,
        dynamic_results: Optional[Dict[str, Any]] = None,
        justification_results: Optional[Dict[str, Any]] = None,
        include_sia4010: bool = True,
    ):
        """Generate the workbook with xlsxwriter."""
        self.include_sia4010 = include_sia4010
        # The index and the tab-colour finalize both iterate this; dropping the
        # SIA 4010 section here keeps them from linking to or colouring sheets
        # that were never written.
        self._active_sections = [
            (
                (
                    "Compliance & priority"
                    if not include_sia4010 and section_name == "Readiness & priority"
                    else section_name
                ),
                colour,
                [
                    sheet
                    for sheet in sheets
                    if include_sia4010 or sheet != "DETAILED SCORES"
                ],
            )
            for section_name, colour, sheets in self._REPORT_SECTIONS
            if include_sia4010 or section_name != "SIA 4010"
        ]
        self.sia3802_justifications = (
            justification_results or sia3802_results.get("justifications", {}) or {}
        )
        # Round all displayed scores once, at the source, so no sheet renders
        # raw floating-point noise (e.g. 73.6842105263158 -> 73.7).
        score_result = self._display_score_result(score_result)
        if not self.include_sia4010:
            # Drop the SIA 4010 alerts before anything aggregates them, so no
            # shared view (alerts sheet, action matrix, dashboards, P1) carries
            # a validation-evidence finding onto a client 380/2 report.
            score_result = self._without_sia4010_alerts(score_result)
        alert_groups = self._build_alert_groups(score_result.alerts)
        self._write_cover_xlsxwriter(
            score_result, sia3802_results, sia4010_results, rooms_data or []
        )
        self._write_model_viewer_xlsxwriter()
        self._write_index_xlsxwriter(bool(rooms_data))
        self._write_manager_dashboard_xlsxwriter(
            score_result, sia3802_results, sia4010_results, rooms_data or [], alert_groups
        )
        self._write_action_dashboard_xlsxwriter(
            score_result,
            sia3802_results,
            sia4010_results,
            rooms_data or [],
            alert_groups,
            dynamic_results or {},
        )
        self._write_client_summary_xlsxwriter(
            score_result,
            sia3802_results,
            sia4010_results,
            rooms_data or [],
            alert_groups,
        )
        self._write_preflight_xlsxwriter(
            preflight_checks or [], rooms_data or [], sia4010_results
        )
        self._write_p1_remediation_xlsxwriter(alert_groups, sia4010_results)
        self._write_facade_glazing_review_xlsxwriter(alert_groups, rooms_data or [])
        self._write_frame_fraction_audit_xlsxwriter(rooms_data or [])
        self._write_envelope_u_review_xlsxwriter(rooms_data or [])
        self._write_ve_g_values_audit_xlsxwriter(rooms_data or [])
        self._write_assumptions_limits_xlsxwriter(
            score_result, sia4010_results, rooms_data or []
        )
        self._write_review_governance_xlsxwriter(dynamic_results or {})
        self._write_capability_guide_xlsxwriter()
        self._write_audit_log_xlsxwriter(
            score_result,
            sia4010_results,
            rooms_data or [],
            preflight_checks or [],
            dynamic_results or {},
        )
        # The legacy SUMMARY and ACTION PLAN sheet builders were deleted: their
        # content is fully covered by the newer CLIENT SUMMARY, ACTION DASHBOARD /
        # P1 REMEDIATION and the domain scores on the dashboards.
        self._write_compliance_results_xlsxwriter(sia3802_results, sia4010_results)
        self._write_reference_project_xlsxwriter(sia3802_results)
        self._write_sia_requirements_xlsxwriter(sia3802_results, sia4010_results)
        self._write_sia_data_coverage_xlsxwriter(
            sia3802_results,
            sia4010_results,
            rooms_data or [],
            preflight_checks or [],
            dynamic_results or {},
        )
        self._write_input_request_xlsxwriter(
            sia3802_results,
            sia4010_results,
            rooms_data or [],
            preflight_checks or [],
            dynamic_results or {},
        )
        self._write_sia3802_justifications_xlsxwriter(self.sia3802_justifications)
        self._write_open_items_backlog_xlsxwriter(
            alert_groups,
            sia3802_results,
            sia4010_results,
            rooms_data or [],
            preflight_checks or [],
            dynamic_results or {},
        )
        if self.include_sia4010:
            self._write_sia4010_readiness_xlsxwriter(sia4010_results, rooms_data or [])
            self._write_sia4010_prevalidation_xlsxwriter(sia4010_results)
            self._write_sia4010_class_matrix_xlsxwriter(sia4010_results, rooms_data or [])
            self._write_sia4010_software_register_xlsxwriter()
        self._write_sia_navigator_backlog_xlsxwriter()
        self._write_dynamic_results_xlsxwriter(dynamic_results or {})
        self._write_alert_summary_xlsxwriter(alert_groups)
        self._write_alerts_xlsxwriter(score_result.alerts)
        self._write_data_quality_xlsxwriter(score_result.alerts, rooms_data or [])
        if self.include_sia4010:
            self._write_detailed_scores_xlsxwriter(score_result.detailed_scores)
        if rooms_data:
            self._write_rooms_xlsxwriter(rooms_data)
        self._finalize_workbook_xlsxwriter()
        self.workbook.close()

    # =============================================================================
    # Report identity, cover, index and finalize (shared presentation layer)
    # =============================================================================

    # Ordered section -> (tab colour, member sheets). Drives both the clickable
    # index grouping and the uniform tab colours applied at finalize. The
    # colours resolve through report_style so the workbook, the PDF and the
    # in-VE interface cannot drift into separate visual identities.
    _REPORT_SECTIONS = [
        (
            "Executive",
            report_style.XW_SECTION_TAB_COLORS["Executive"],
            [
                "MANAGER DASHBOARD",
                "ACTION DASHBOARD",
                "CLIENT SUMMARY",
                "MODEL VIEWER",
            ],
        ),
        (
            "Readiness & priority",
            report_style.XW_SECTION_TAB_COLORS["Readiness & priority"],
            [
                "PREFLIGHT",
                "P1 REMEDIATION",
            ],
        ),
        (
            "Envelope & glazing",
            report_style.XW_SECTION_TAB_COLORS["Envelope & glazing"],
            [
                "FACADE GLAZING REVIEW",
                "FRAME FRACTION AUDIT",
                "ENVELOPE U REVIEW",
                "VE G-VALUES AUDIT",
            ],
        ),
        (
            "SIA 380/2",
            report_style.XW_SECTION_TAB_COLORS["SIA 380/2"],
            [
                "COMPLIANCE RESULTS",
                "REFERENCE PROJECT",
                "SIA REQUIREMENTS",
                "SIA DATA COVERAGE",
                "SIA3802 JUSTIFICATIONS",
                "CAPABILITY GUIDE",
                "ASSUMPTIONS LIMITS",
                "REVIEW GOVERNANCE",
            ],
        ),
        (
            "SIA 4010",
            report_style.XW_SECTION_TAB_COLORS["SIA 4010"],
            [
                "SIA4010 READINESS",
                "SIA4010 PREVALIDATION",
                "SIA4010 CLASS MATRIX",
                "SIA4010 SOFTWARE REGISTER",
            ],
        ),
        (
            "Actions & inputs",
            report_style.XW_SECTION_TAB_COLORS["Actions & inputs"],
            [
                "INPUT REQUEST",
                "OPEN ITEMS BACKLOG",
                "NAVIGATOR BACKLOG",
                "AUDIT LOG",
            ],
        ),
        (
            "Data & detail",
            report_style.XW_SECTION_TAB_COLORS["Data & detail"],
            [
                "DYNAMIC RESULTS",
                "ALERT SUMMARY",
                "ALERTS",
                "DATA QUALITY",
                "DETAILED SCORES",
                "ROOMS",
            ],
        ),
    ]
    _COVER_TAB_COLOR = report_style.XW_TAB_COLOR

    @staticmethod
    def _is_sia4010_alert(alert: Any) -> bool:
        """Return whether an alert belongs to the SIA 4010 validation family.

        Same rule the action matrix uses to label a row's standard: SIA 4010
        alerts carry ``SIA4010`` in the rule or category. Used only to keep them
        off a client SIA 380/2 report.
        """

        rule = str(getattr(alert, "rule", "") or "").upper()
        category = str(getattr(alert, "category", "") or "").upper()
        return "SIA4010" in rule or "4010" in category

    def _without_sia4010_alerts(self, score_result: "ScoreResult") -> "ScoreResult":
        """Return a copy of the score with all SIA 4010 material removed.

        The SIA 380/2 score and health score are unchanged. Both the alert list
        and the per-domain detailed scores are filtered, so the client report's
        aggregated views (alerts, action matrix, P1, dashboards) and the detailed
        scores sheet show SIA 380/2 findings only, never a SIA4010_TEST_* row.
        """

        return ScoreResult(
            compliance_score=getattr(score_result, "compliance_score", 0.0),
            health_score=getattr(score_result, "health_score", 0.0),
            detailed_scores={
                key: value
                for key, value in (
                    getattr(score_result, "detailed_scores", {}) or {}
                ).items()
                if "4010" not in str(key).upper()
            },
            alerts=[
                alert
                for alert in getattr(score_result, "alerts", []) or []
                if not self._is_sia4010_alert(alert)
            ],
        )

    @staticmethod
    def _display_score_result(score_result: "ScoreResult") -> "ScoreResult":
        """Return a display copy with scores rounded to one decimal.

        Rounding once at the source keeps every downstream sheet, KPI card and
        chart free of raw floating-point noise, independent of each cell's
        number format. The alert list is preserved unchanged.
        """

        def _r(value: Any) -> Any:
            """Round one value to a single decimal, leaving non-numerics as-is."""

            try:
                return round(float(value), 1)
            except (TypeError, ValueError):
                return value

        return ScoreResult(
            compliance_score=_r(getattr(score_result, "compliance_score", 0.0)),
            health_score=_r(getattr(score_result, "health_score", 0.0)),
            detailed_scores={
                key: _r(value)
                for key, value in (
                    getattr(score_result, "detailed_scores", {}) or {}
                ).items()
            },
            alerts=getattr(score_result, "alerts", []),
        )

    def _project_label(self) -> str:
        """Derive a human project label from the output filename."""

        base = os.path.splitext(os.path.basename(self.output_path or ""))[0]
        parts = base.split("__")
        if len(parts) >= 2 and parts[1]:
            return parts[1].replace("_", " ").strip()
        return "Swiss SIA project"

    def _context_value(self, key: str, default: Any = "") -> Any:
        """Read one optional client-interface value from a dataclass or dict."""

        context = self.report_context
        if context is None:
            return default
        if isinstance(context, dict):
            return context.get(key, default)
        return getattr(context, key, default)

    def _tr(self, key: str) -> str:
        """Translate one client-facing workbook label."""

        return translate(key, self.report_language)

    def _context_image(self, key: str) -> Optional[str]:
        """Return one existing report-context image path."""

        value = str(self._context_value(key, "") or "").strip()
        return value if value and os.path.isfile(value) else None

    def _client_evidence_destination(self, text: str) -> str:
        """Return a destination hint safe for a client SIA 380/2-only report.

        The coverage matrix routes several genuine SIA 380/2 inputs into the
        tool's ``sia4010_evidence/`` intake folder. On a client 380/2-only
        report that internal folder name must not surface, so this keeps any
        real location (the VE Vista folder, an Excel sheet) and neutralises the
        bare folder token. In the default mode the text is returned unchanged.
        """

        if self.include_sia4010:
            return text
        cleaned = str(text or "")
        for connector in (" or ", " plus "):
            cleaned = cleaned.replace(f"{connector}sia4010_evidence/", "")
        if cleaned.strip() == "sia4010_evidence/" or not cleaned.strip():
            return "Project evidence folder"
        return cleaned.replace("sia4010_evidence/", "project evidence folder")

    @staticmethod
    def _resolve_cover_logo():
        """Return the real cover logo path when one has been supplied.

        The assets directory is resolved from this module's location, not from
        the workbook output path -- the workbook can be written anywhere, and the
        previous relative lookup never found the file.  The placeholder square
        is deliberately excluded from client-facing workbooks.

        Returns:
            str | None: An existing logo file path, or None when neither the
            real logo nor the placeholder is present.
        """

        assets = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets"
        )
        path = os.path.join(assets, "ies_logo.png")
        if os.path.isfile(path):
            return path
        return None

    def _write_cover_xlsxwriter(
        self, score_result, sia3802_results, sia4010_results, rooms_data
    ):
        """Write the branded cover landing page with rounded headline KPIs."""

        worksheet = self.workbook.add_worksheet("COVER")
        worksheet.hide_gridlines(2)
        worksheet.set_column("A:A", 2)
        worksheet.set_column("B:E", 22)
        worksheet.set_column("F:F", 2)

        # Every format below resolves through report_style, so this sheet
        # carries no colour of its own. See that module for why the status
        # colours are the derived text shades and not the stroke hues.
        title_format = self.workbook.add_format(report_style.xw_title())
        subtitle_format = self.workbook.add_format(report_style.xw_subtitle())
        logo_format = self.workbook.add_format(
            report_style.xw_format(
                "muted", size=design.SIZE_BODY, align="center", valign="vcenter"
            )
        )
        label_format = self.workbook.add_format(report_style.xw_label())
        value_format = self.workbook.add_format(report_style.xw_value())
        kpi_label_format = self.workbook.add_format(report_style.xw_kpi_label())
        kpi_value_format = self.workbook.add_format(report_style.xw_kpi_value())
        kpi_int_format = self.workbook.add_format(
            report_style.xw_kpi_value(num_format="#,##0")
        )
        # The disclaimer was set in a dark red, which reads as a failure state.
        # It is a scope statement, not a verdict: muted, like every other note.
        disclaimer_format = self.workbook.add_format(
            {**report_style.xw_disclaimer(), "valign": "top"}
        )

        # Cover logo. Only a real supplied IES asset is accepted; the generic
        # placeholder square is never printed on a client report.
        worksheet.merge_range("B2:C4", "", logo_format)
        worksheet.merge_range("D2:E4", "", logo_format)
        worksheet.set_row(1, 22)
        worksheet.set_row(2, 22)
        worksheet.set_row(3, 22)
        logo_path = self._resolve_cover_logo()
        if logo_path is not None:
            try:
                # Fit the square IES asset into the three-row logo block without
                # distorting it or allowing it to dominate the client identity.
                worksheet.insert_image(
                    "B2",
                    logo_path,
                    {
                        "x_scale": 0.23,
                        "y_scale": 0.23,
                        "object_position": 1,
                        "x_offset": 4,
                        "y_offset": 4,
                    },
                )
            except Exception:
                worksheet.write("B2", "SIA 380/2", logo_format)
        else:
            worksheet.write("B2", "SIA 380/2", logo_format)
        client_logo = self._context_image("client_logo_path")
        if client_logo:
            try:
                worksheet.insert_image(
                    "D2",
                    client_logo,
                    {
                        "x_scale": 0.30,
                        "y_scale": 0.30,
                        "object_position": 1,
                        "x_offset": 8,
                        "y_offset": 4,
                    },
                )
            except Exception:
                worksheet.write(
                    "D2", str(self._context_value("client_name", "")), logo_format
                )

        report_title = self._tr("report_title")
        worksheet.merge_range("B6:E6", report_title, title_format)
        worksheet.set_row(5, 32)
        worksheet.merge_range(
            "B7:E7",
            (
                "Automated SIA 380/2 readiness review and SIA 4010 evidence status"
                if self.include_sia4010
                else self._tr("report_subtitle_sia3802")
            ),
            subtitle_format,
        )

        unavailable = self._tr("value_unavailable")
        worksheet.write("B9", self._tr("field_client"), label_format)
        worksheet.merge_range(
            "C9:E9", self._context_value("client_name", unavailable), value_format
        )
        worksheet.write("B10", self._tr("field_project"), label_format)
        worksheet.merge_range(
            "C10:E10",
            self._context_value("project_name", "") or self._project_label(),
            value_format,
        )
        worksheet.write("B11", self._tr("field_project_address"), label_format)
        worksheet.merge_range(
            "C11:E11", self._context_value("project_address", unavailable), value_format
        )
        worksheet.write("B12", self._tr("client_ui_weather"), label_format)
        worksheet.merge_range(
            "C12:E12", self._context_value("weather_file", unavailable), value_format
        )
        worksheet.write(
            "B13",
            building_strategy_text("field_building_strategy", self.report_language),
            label_format,
        )
        worksheet.merge_range(
            "C13:E13",
            building_strategy_summary(self.report_context or {}, self.report_language),
            value_format,
        )
        worksheet.write("B14", self._tr("field_generated"), label_format)
        worksheet.merge_range(
            "C14:E14", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), value_format
        )
        # Regulatory framework is fixed for the whole assessment (constrained
        # navigator): stating the editions on the cover keeps the scope explicit
        # and immutable from the first sheet, per the SIA 380/2 navigator brief.
        worksheet.write("B15", self._tr("field_framework"), label_format)
        worksheet.merge_range(
            "C15:E15",
            (
                "SIA 380/2:2022 (FR) + SIA 4010:2023 (FR) - editions fixed for this assessment"
                if self.include_sia4010
                else "SIA 380/2:2022 (FR) - edition fixed for this assessment"
            ),
            value_format,
        )

        verdict = build_compliance_verdict(
            sia3802_results, sia4010_results, len(rooms_data)
        )
        if self.include_sia4010:
            worksheet.write(
                "B17", "SIA 380/2 coverage (diagnostic, not compliance)", kpi_label_format
            )
            worksheet.write_number(
                "C17",
                round(float(getattr(score_result, "compliance_score", 0.0) or 0.0), 1),
                kpi_value_format,
            )
            worksheet.write("B18", "Model health score", kpi_label_format)
            worksheet.write_number(
                "C18",
                round(float(getattr(score_result, "health_score", 0.0) or 0.0), 1),
                kpi_value_format,
            )
            worksheet.write("B19", "Rooms analysed", kpi_label_format)
            worksheet.write_number("C19", len(rooms_data), kpi_int_format)
        else:
            worksheet.write("B17", self._tr("client_ui_decision"), kpi_label_format)
            status_key = {
                "COMPLIANT": "verdict_compliant",
                "NOT_COMPLIANT": "verdict_not_compliant",
            }.get(verdict.sia3802_status, "verdict_not_determined")
            worksheet.merge_range("C17:E17", self._tr(status_key), kpi_value_format)
            worksheet.write("B18", self._tr("figure_rooms"), kpi_label_format)
            worksheet.write_number("C18", len(rooms_data), kpi_int_format)

        worksheet.merge_range(
            "B20:E23",
            (
                "This workbook is an automated readiness and evidence review. It is "
                "NOT an SIA certificate and does not constitute SIA 4010 validation. "
                "Scores are indicators computed from the directly extracted VE model; "
                "missing official evidence is reported as WARNING or NOT_CHECKABLE, "
                "never as a pass. See the INDEX sheet to navigate all sections."
                if self.include_sia4010
                else self._tr("excel_scope_statement")
            ),
            disclaimer_format,
        )

    def _write_model_viewer_xlsxwriter(self) -> None:
        """Embed the user-selected Model Viewer capture in the workbook."""

        worksheet = self.workbook.add_worksheet("MODEL VIEWER")
        worksheet.hide_gridlines(2)
        worksheet.set_column("A:A", 2)
        worksheet.set_column("B:M", 13)
        title_format = self.workbook.add_format(report_style.xw_title())
        note_format = self.workbook.add_format(
            report_style.xw_format("muted", text_wrap=True, valign="top")
        )
        worksheet.merge_range("B2:M2", self._tr("excel_model_viewer_title"), title_format)
        worksheet.merge_range(
            "B4:M5",
            self._tr("excel_model_viewer_note"),
            note_format,
        )
        image_path = self._context_image("model_viewer_image_path")
        if image_path:
            try:
                worksheet.insert_image(
                    "B7",
                    image_path,
                    {"x_scale": 0.70, "y_scale": 0.70, "object_position": 1},
                )
            except Exception:
                worksheet.merge_range(
                    "B7:M10", self._tr("excel_image_unavailable"), note_format
                )
        else:
            worksheet.merge_range(
                "B7:M10", self._tr("excel_no_viewer_image"), note_format
            )

    def _write_index_xlsxwriter(self, has_rooms: bool):
        """Write a clickable index grouped by report section."""

        worksheet = self.workbook.add_worksheet("INDEX")
        worksheet.hide_gridlines(2)
        worksheet.set_column("A:A", 2)
        worksheet.set_column("B:B", 40)
        worksheet.set_column("C:C", 60)

        # Resolved through report_style, like the cover. The section bar was a
        # solid teal; the house style bands in navy and reserves saturated
        # colour for small areas, so the band carries light type on navy.
        title_format = self.workbook.add_format(
            report_style.xw_format("band", size=design.SIZE_TITLE, bold=True, border=None)
        )
        section_format = self.workbook.add_format(report_style.xw_band())
        link_format = self.workbook.add_format({**report_style.xw_link(), "underline": 1})

        worksheet.write("B2", self._tr("excel_report_index"), title_format)
        row = 3
        for section, color, sheets in self._active_sections:
            visible = [s for s in sheets if s != "ROOMS" or has_rooms]
            if not visible:
                continue
            worksheet.merge_range(row, 1, row, 2, section, section_format)
            row += 1
            for sheet in visible:
                worksheet.write_url(
                    row, 1, "internal:'{}'!A1".format(sheet), link_format, sheet
                )
                row += 1
            row += 1

    def _finalize_workbook_xlsxwriter(self):
        """Apply uniform print setup, tab colours and header/footer to all sheets.

        This is the only place that colours a tab. Fifteen sheet builders used
        to set their own first, all of them silently overwritten here a moment
        later, which is how nine off-palette literals survived unnoticed.
        """

        color_by_sheet = {}
        for _section, color, sheets in self._active_sections:
            for sheet in sheets:
                color_by_sheet[sheet] = color

        project = self._project_label()
        generated = datetime.now().strftime("%Y-%m-%d %H:%M")
        header = "&LIES | {}&C{}&R&D".format(project, self._tr("report_title"))
        footer = (
            "&LNot a certificate - automated SIA readiness review"
            if self.include_sia4010
            else "&L" + self._tr("footer_not_certificate")
        ) + "&C&P / &N&R{} {}".format(self._tr("field_generated"), generated)
        for worksheet in self.workbook.worksheets():
            name = getattr(worksheet, "name", "")
            worksheet.hide_gridlines(2)
            if name in ("COVER", "INDEX"):
                worksheet.set_tab_color(self._COVER_TAB_COLOR)
            elif name in color_by_sheet:
                worksheet.set_tab_color(color_by_sheet[name])
            worksheet.set_paper(9)  # A4
            worksheet.set_margins(left=0.5, right=0.5, top=0.75, bottom=0.75)
            worksheet.center_horizontally()
            if name not in ("COVER", "INDEX"):
                worksheet.set_landscape()
                worksheet.fit_to_pages(1, 0)
            worksheet.set_header(header)
            worksheet.set_footer(footer)

    # =============================================================================
    # xlsxwriter methods
    # =============================================================================

    def _write_manager_dashboard_xlsxwriter(
        self,
        score_result: ScoreResult,
        sia3802_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
        rooms_data: List[Any],
        alert_groups: List[Dict[str, Any]],
    ):
        """Write the executive visual dashboard shown first in the workbook."""
        worksheet = self.workbook.add_worksheet("MANAGER DASHBOARD")
        worksheet.hide_gridlines(2)

        # The dashboard used to carry its own teal-and-slate palette. Every
        # format below now resolves through report_style, so this sheet reads as
        # the same document as the cover, the index and the PDF.
        title_format = self.workbook.add_format(
            report_style.xw_format(
                "on_dark",
                size=20,
                bold=True,
                background="band_deep",
                border=None,
                align="left",
                valign="vcenter",
            )
        )
        subtitle_format = self.workbook.add_format(
            report_style.xw_format(
                "on_dark",
                size=10,
                background="band_deep",
                border=None,
                align="left",
                valign="vcenter",
            )
        )
        card_title_format = self.workbook.add_format(
            report_style.xw_format(
                "band",
                size=9,
                bold=True,
                background="table_header",
                align="center",
                valign="vcenter",
            )
        )
        card_value_format = self.workbook.add_format(
            report_style.xw_format(
                "band_deep",
                size=18,
                bold=True,
                background="white",
                align="center",
                valign="vcenter",
            )
        )
        card_note_format = self.workbook.add_format(
            report_style.xw_format(
                "muted",
                size=8,
                background="white",
                align="center",
                valign="vcenter",
                text_wrap=True,
            )
        )
        section_format = self.workbook.add_format(
            report_style.xw_format(
                "on_dark",
                size=12,
                bold=True,
                background="band",
                border=None,
                align="left",
                valign="vcenter",
            )
        )
        # The reading note is an aside, not a warning: the amber box read as an
        # alert on a sheet whose alerts carry meaning. Panel grey instead.
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                size=10,
                background="panel",
                valign="top",
                text_wrap=True,
            )
        )
        header_format = self.workbook.add_format(
            report_style.xw_format(
                "on_dark",
                bold=True,
                background="band",
            )
        )
        cell_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                text_wrap=True,
                valign="top",
            )
        )
        # Priority is a fail-severity marker, so it takes the audited status
        # presentation rather than a locally chosen red.
        priority_format = self.workbook.add_format(report_style.xw_status("fail"))
        number_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                num_format="#,##0",
            )
        )
        nav_format = self.workbook.add_format(
            report_style.xw_format(
                "accent",
                bold=True,
                background="table_header",
                align="center",
            )
        )

        worksheet.set_column("A:A", 14)
        worksheet.set_column("B:B", 18)
        worksheet.set_column("C:C", 14)
        worksheet.set_column("D:D", 18)
        worksheet.set_column("E:E", 14)
        worksheet.set_column("F:F", 18)
        worksheet.set_column("G:G", 14)
        worksheet.set_column("H:H", 18)
        worksheet.set_column("I:I", 14)
        worksheet.set_column("J:J", 18)
        worksheet.set_column("K:L", 18)
        worksheet.set_column("N:U", 16, None, {"hidden": True})

        worksheet.set_row(0, 34)
        worksheet.set_row(1, 26)
        worksheet.merge_range("A1:L1", "Swiss SIA Compliance Dashboard", title_format)
        worksheet.merge_range(
            "A2:L2",
            (
                "Executive view - VE model, automated SIA 380/2 checks, SIA 4010 readiness and action priorities."
                if self.include_sia4010
                else "Executive view - client VE model, SIA 380/2 compliance verdict and action priorities."
            ),
            subtitle_format,
        )
        # Build the target list first, then drop it into the fixed slots, so the
        # SIA 4010 button vanishes in 380/2-only mode (its sheet is never
        # written) and the remaining buttons reflow with no dead link or gap.
        nav_links = [
            ("Action Page", "ACTION DASHBOARD"),
            ("P1 Actions", "P1 REMEDIATION"),
            ("Input Request", "INPUT REQUEST"),
            ("SIA Coverage", "SIA DATA COVERAGE"),
        ]
        if self.include_sia4010:
            nav_links.append(("SIA4010", "SIA4010 READINESS"))
        nav_links.append(("Audit Log", "AUDIT LOG"))
        nav_slots = ["A3:B3", "C3:D3", "E3:F3", "G3:H3", "I3:J3", "K3:L3"]
        for cell_range, (label, sheet_name) in zip(nav_slots, nav_links):
            first_cell = cell_range.split(":")[0]
            worksheet.merge_range(cell_range, "", nav_format)
            worksheet.write_url(
                first_cell, f"internal:'{sheet_name}'!A1", nav_format, string=label
            )

        alerts_count = self._count_alerts_by_severity(score_result.alerts)
        critical_high = alerts_count.get("Critical", 0) + alerts_count.get("High", 0)
        room_count = len(rooms_data)
        total_area = sum(
            self._safe_float(getattr(room, "area", 0.0)) for room in rooms_data
        )
        evidence = sia4010_results.get("evidence", {}) or {}
        evidence_present = sum(
            1
            for item in SIA4010_REQUIRED_EVIDENCE
            if self._has_sia4010_evidence(evidence, item)
        )
        compliance_verdict = build_compliance_verdict(
            sia3802_results, sia4010_results, room_count
        )

        # Cards are placed left to right into fixed two-column slots. Building
        # the list first means dropping the SIA 4010 card in 380/2-only mode
        # reflows the rest with no empty slot, rather than leaving a hole.
        cards = []
        if self.include_sia4010:
            cards.extend(
                [
                    (
                        "MODEL QA",
                        f"{score_result.health_score:.1f}",
                        "Health score from data completeness and model quality.",
                    ),
                    (
                        "SIA 380/2 COVERAGE (diag.)",
                        f"{score_result.compliance_score:.1f}",
                        "Component-coverage diagnostic only, NOT a compliance score: it excludes the decisive §7.2.5.2 gate. See the COMPLIANCE VERDICT.",
                    ),
                ]
            )
        else:
            cards.extend(
                [
                    (
                        "COMPLIANCE VERDICT",
                        compliance_verdict.sia3802_status.replace("_", " "),
                        "Decisive SIA 380/2 building conclusion; missing evidence remains visible.",
                    ),
                    (
                        "BLOCKING FINDINGS",
                        str(compliance_verdict.blocking_total),
                        "Determined findings that prevent a compliant conclusion.",
                    ),
                    (
                        "MISSING / ADVISORY",
                        "{} / {}".format(
                            compliance_verdict.missing_total,
                            compliance_verdict.advisory_total,
                        ),
                        "Incomplete evidence / review items that remain visible.",
                    ),
                ]
            )
        if self.include_sia4010:
            cards.append(
                (
                    "SIA 4010 EVIDENCE",
                    f"{evidence_present}/{len(SIA4010_REQUIRED_EVIDENCE)}",
                    "Official evidence items detected locally.",
                )
            )
        cards.extend(
            [
                ("ROOMS", f"{room_count}", "Thermal rooms extracted from VE."),
                ("FLOOR AREA", f"{total_area:,.1f}", "m2 extracted from room areas."),
                (
                    "P1 RISKS",
                    f"{critical_high}",
                    "Critical + high alerts requiring attention.",
                ),
            ]
        )
        card_slots = ["A4:B7", "C4:D7", "E4:F7", "G4:H7", "I4:J7", "K4:L7"]
        for slot, (title, value, note) in zip(card_slots, cards):
            self._write_dashboard_card(
                worksheet,
                slot,
                title,
                value,
                note,
                card_title_format,
                card_value_format,
                card_note_format,
            )

        worksheet.merge_range("A9:L9", "Executive Interpretation", section_format)
        worksheet.merge_range(
            "A10:L12",
            self._dashboard_verdict(
                score_result,
                sia4010_results,
                rooms_data,
                self.include_sia4010,
                sia3802_results,
            ),
            note_format,
        )

        score_rows = (
            self._dashboard_score_rows(score_result) if self.include_sia4010 else []
        )
        severity_rows = [
            ["Severity", "Count"],
            ["Critical", alerts_count.get("Critical", 0)],
            ["High", alerts_count.get("High", 0)],
            ["Medium", alerts_count.get("Medium", 0)],
            ["Low", alerts_count.get("Low", 0)],
        ]
        requirement_rows = self._dashboard_requirement_status_rows(
            sia3802_results, sia4010_results
        )

        if self.include_sia4010:
            worksheet.write_row("N3", ["Category", "Score"], header_format)
            for row_index, row_values in enumerate(score_rows, start=3):
                worksheet.write_row(row_index, 13, row_values, cell_format)
        worksheet.write_row("Q3", severity_rows[0], header_format)
        for row_index, row_values in enumerate(severity_rows[1:], start=4):
            worksheet.write(row_index, 16, row_values[0], cell_format)
            worksheet.write(row_index, 17, row_values[1], number_format)
        worksheet.write_row("T3", ["Status", "Count"], header_format)
        for row_index, row_values in enumerate(requirement_rows, start=4):
            worksheet.write(row_index, 19, row_values[0], cell_format)
            worksheet.write(row_index, 20, row_values[1], number_format)

        if self.include_sia4010:
            worksheet.merge_range("A14:F14", "Scores by Domain", section_format)
            score_chart = self.workbook.add_chart({"type": "bar"})
            score_last_row = 3 + len(score_rows)
            score_chart.add_series(
                {
                    "name": "Score",
                    "categories": f"='MANAGER DASHBOARD'!$N$4:$N${score_last_row}",
                    "values": f"='MANAGER DASHBOARD'!$O$4:$O${score_last_row}",
                    "fill": {"color": report_style.XW_CHART_FILL},
                    "border": {"none": True},
                    "data_labels": {"value": True, "num_format": "0"},
                }
            )
            score_chart.set_title({"name": "Score overview (0-100)"})
            score_chart.set_x_axis(
                {
                    "name": "Score",
                    "min": 0,
                    "max": 100,
                    "major_gridlines": {"visible": False},
                }
            )
            score_chart.set_y_axis({"major_gridlines": {"visible": False}})
            score_chart.set_legend({"none": True})
            score_chart.set_style(10)
            self._show_hidden_chart_data(score_chart)
            worksheet.insert_chart("A15", score_chart, {"x_scale": 1.25, "y_scale": 1.25})
        else:
            worksheet.merge_range("A14:F14", "Compliance by Domain", section_format)
            worksheet.write_row(
                "A15",
                ["Domain", "Verdict", "Blocking", "Missing", "Advisory"],
                header_format,
            )
            for row_index, domain in enumerate(compliance_verdict.domains, start=15):
                worksheet.write(row_index, 0, domain.domain.title(), cell_format)
                worksheet.write(
                    row_index, 1, domain.status.replace("_", " "), cell_format
                )
                worksheet.write(row_index, 2, domain.blocking_count, number_format)
                worksheet.write(row_index, 3, domain.missing_count, number_format)
                worksheet.write(row_index, 4, domain.advisory_count, number_format)

        worksheet.merge_range("G14:L14", "Risk Distribution", section_format)
        alert_chart = self.workbook.add_chart({"type": "doughnut"})
        alert_chart.add_series(
            {
                "name": "Alerts",
                "categories": "='MANAGER DASHBOARD'!$Q$5:$Q$8",
                "values": "='MANAGER DASHBOARD'!$R$5:$R$8",
                # One slice per severity, in the order severity_rows writes them, so
                # the fills cannot drift out of step with the categories.
                "points": [
                    {"fill": {"color": report_style.XW_SEVERITY_FILLS[severity]}}
                    for severity, _ in severity_rows[1:]
                ],
                "data_labels": {"percentage": True},
            }
        )
        alert_chart.set_title({"name": "Alerts by severity"})
        alert_chart.set_style(10)
        self._show_hidden_chart_data(alert_chart)
        worksheet.insert_chart("G15", alert_chart, {"x_scale": 1.22, "y_scale": 1.22})

        worksheet.merge_range("A32:F32", "SIA Requirement Coverage", section_format)
        requirement_chart = self.workbook.add_chart({"type": "column"})
        req_last_row = 4 + len(requirement_rows)
        requirement_chart.add_series(
            {
                "name": "Requirements",
                "categories": f"='MANAGER DASHBOARD'!$T$5:$T${req_last_row}",
                "values": f"='MANAGER DASHBOARD'!$U$5:$U${req_last_row}",
                "fill": {"color": report_style.XW_CHART_FILL_NORMATIVE},
                "border": {"none": True},
                "data_labels": {"value": True},
            }
        )
        requirement_chart.set_title({"name": "Coverage by status"})
        requirement_chart.set_legend({"none": True})
        requirement_chart.set_y_axis({"major_gridlines": {"visible": False}})
        requirement_chart.set_style(10)
        self._show_hidden_chart_data(requirement_chart)
        worksheet.insert_chart(
            "A33", requirement_chart, {"x_scale": 1.25, "y_scale": 1.05}
        )

        worksheet.merge_range("G32:L32", "Top Priority Actions", section_format)
        worksheet.write_row(
            "G33",
            ["Priority", "Category", "Issue count", "Action", "Evidence"],
            header_format,
        )
        row = 33
        for group in alert_groups[:6]:
            worksheet.write(
                row,
                6,
                group.get("priority", ""),
                priority_format if group.get("priority") == "P1" else cell_format,
            )
            worksheet.write(row, 7, group.get("category", ""), cell_format)
            worksheet.write(row, 8, group.get("count", 0), number_format)
            worksheet.write(row, 9, self._action_for_alert_group(group), cell_format)
            worksheet.write(
                row, 10, "; ".join(group.get("evidence_samples", [])[:2]), cell_format
            )
            worksheet.set_row(row, 44)
            row += 1
        if not alert_groups:
            worksheet.merge_range(
                "G34:K34", "No priority action generated from alerts.", cell_format
            )

        worksheet.freeze_panes(3, 0)

    def _write_action_dashboard_xlsxwriter(
        self,
        score_result: ScoreResult,
        sia3802_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
        rooms_data: List[Any],
        alert_groups: List[Dict[str, Any]],
        dynamic_results: Dict[str, Any],
    ):
        """Write a single-page action view focused on compliance findings."""
        worksheet = self.workbook.add_worksheet("ACTION DASHBOARD")
        worksheet.hide_gridlines(2)
        worksheet.set_landscape()
        worksheet.fit_to_pages(1, 0)
        worksheet.freeze_panes(22, 0)

        # This sheet used to be entirely orange -- bands, headers, hairlines and
        # cards -- which made "everything on it is urgent" the first impression
        # and left its three real severity markers no contrast to work with.
        # House style now, with urgency carried only by the verdict cells.
        title_format = self.workbook.add_format(
            report_style.xw_format(
                "on_dark",
                size=20,
                bold=True,
                background="band_deep",
                border=None,
                align="left",
                valign="vcenter",
            )
        )
        subtitle_format = self.workbook.add_format(
            report_style.xw_format(
                "on_dark",
                size=10,
                background="band_deep",
                border=None,
                align="left",
                valign="vcenter",
            )
        )
        section_format = self.workbook.add_format(
            report_style.xw_format(
                "on_dark",
                bold=True,
                background="band",
                align="left",
                valign="vcenter",
            )
        )
        header_format = self.workbook.add_format(
            report_style.xw_format(
                "on_dark",
                bold=True,
                background="band",
                align="center",
                valign="vcenter",
                text_wrap=True,
            )
        )
        cell_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                text_wrap=True,
                valign="top",
            )
        )
        muted_format = self.workbook.add_format(
            report_style.xw_format(
                "muted",
                text_wrap=True,
                valign="top",
            )
        )
        card_title_format = self.workbook.add_format(
            report_style.xw_format(
                "band",
                size=9,
                bold=True,
                background="table_header",
                align="center",
                valign="vcenter",
            )
        )
        card_value_format = self.workbook.add_format(
            report_style.xw_format(
                "band_deep",
                size=18,
                bold=True,
                background="white",
                align="center",
                valign="vcenter",
            )
        )
        card_note_format = self.workbook.add_format(
            report_style.xw_format(
                "muted",
                size=8,
                background="white",
                align="center",
                valign="vcenter",
                text_wrap=True,
            )
        )
        score_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                num_format="0",
                align="center",
                valign="vcenter",
            )
        )
        number_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                num_format="#,##0",
                align="center",
            )
        )
        decimal_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                num_format="0.000",
                align="center",
            )
        )
        gap_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                num_format="+0.000;-0.000;0.000",
                align="center",
            )
        )
        # The three priorities map onto the audited verdict presentations: P1 is
        # what fails compliance, P2 what carries a reservation, P3 what is not
        # evaluated yet. Reusing them keeps one severity language in the report.
        p1_format = self.workbook.add_format(report_style.xw_status("fail"))
        p2_format = self.workbook.add_format(report_style.xw_status("warning"))
        p3_format = self.workbook.add_format(report_style.xw_status("not_evaluated"))
        link_format = self.workbook.add_format(report_style.xw_table_link())
        ok_format = self.workbook.add_format(report_style.xw_status("pass"))
        warn_format = self.workbook.add_format(report_style.xw_status("warning"))
        fail_format = self.workbook.add_format(report_style.xw_status("fail"))

        worksheet.set_column("A:A", 11)
        worksheet.set_column("B:B", 13)
        worksheet.set_column("C:C", 16)
        worksheet.set_column("D:D", 24)
        worksheet.set_column("E:E", 30)
        worksheet.set_column("F:F", 10)
        worksheet.set_column("G:I", 12)
        worksheet.set_column("J:J", 17)
        worksheet.set_column("K:K", 42)
        worksheet.set_column("L:L", 40)
        worksheet.set_column("M:M", 18)
        worksheet.set_column("N:N", 18)
        worksheet.set_column("O:O", 18)
        worksheet.set_column("P:P", 18)

        worksheet.merge_range(
            "A1:P1", "Action Dashboard - What To Change Next", title_format
        )
        worksheet.merge_range(
            "A2:P2",
            (
                "Single-page operational view: separated SIA 380/2 and SIA 4010 scores, current blockers, VE actions, evidence and owners."
                if self.include_sia4010
                else "Single-page operational view of the client model: SIA 380/2 verdict, current blockers, VE actions and owners."
            ),
            subtitle_format,
        )

        evidence = sia4010_results.get("evidence", {}) or {}
        evidence_summary = (
            evidence.get("summary", {}) if isinstance(evidence, dict) else {}
        )
        evidence_present = sum(
            1
            for item in SIA4010_REQUIRED_EVIDENCE
            if self._has_sia4010_evidence(evidence, item)
        )
        alerts_count = self._count_alerts_by_severity(score_result.alerts)
        priority_counts = Counter(
            str(group.get("priority", "")) for group in alert_groups
        )
        blocked_tests = self._count_blocked_sia4010_tests(sia4010_results)
        total_area = sum(
            self._safe_float(getattr(room, "area", 0.0), 0.0) or 0.0
            for room in rooms_data
        )

        # Left-to-right cards. The three SIA 4010 cards drop in 380/2-only mode
        # and the rest reflow into the freed slots, so there is no empty card.
        compliance_verdict = build_compliance_verdict(
            sia3802_results, sia4010_results, len(rooms_data)
        )
        cards = []
        if self.include_sia4010:
            cards.append(
                (
                    "SIA 380/2 COVERAGE (diag.)",
                    f"{float(score_result.compliance_score or 0.0):.1f}",
                    "Component-coverage diagnostic only, NOT a compliance score: it excludes the decisive §7.2.5.2 gate. See the COMPLIANCE VERDICT.",
                )
            )
        else:
            cards.extend(
                [
                    (
                        "COMPLIANCE VERDICT",
                        compliance_verdict.sia3802_status.replace("_", " "),
                        "Actual SIA 380/2 conclusion supported by the available evidence.",
                    ),
                    (
                        "BLOCKING / MISSING / ADVISORY",
                        "{} / {} / {}".format(
                            compliance_verdict.blocking_total,
                            compliance_verdict.missing_total,
                            compliance_verdict.advisory_total,
                        ),
                        "Findings carried by the compliance verdict.",
                    ),
                ]
            )
        if self.include_sia4010:
            cards.append(
                (
                    "SIA 4010 OFFICIAL",
                    f"{float(sia4010_results.get('score', 0.0) or 0.0):.1f}",
                    "Official validation score remains zero until reviewed test evidence is present.",
                )
            )
            cards.append(
                (
                    "4010 EVIDENCE",
                    f"{evidence_present}/{len(SIA4010_REQUIRED_EVIDENCE)}",
                    "Detected official evidence families in sia4010_evidence/.",
                )
            )
        if self.include_sia4010:
            cards.append(
                (
                    "MODEL HEALTH",
                    f"{float(score_result.health_score or 0.0):.1f}",
                    "Data completeness and consistency indicator.",
                )
            )
        cards.append(
            (
                "P1 / P2 / P3",
                f"{priority_counts.get('P1', 0)} / {priority_counts.get('P2', 0)} / {priority_counts.get('P3', 0)}",
                "Grouped actions by priority.",
            )
        )
        if self.include_sia4010:
            cards.append(
                (
                    "SIA 4010 TESTS",
                    f"{blocked_tests} blocked",
                    "Tests blocked until official evidence and reviewer acceptance are complete.",
                )
            )
        cards.append(
            (
                "ROOMS / AREA",
                f"{len(rooms_data)} / {total_area:,.1f}",
                "Thermal rooms and m2 extracted from VE.",
            )
        )
        cards.append(
            (
                "HIGH + CRITICAL",
                f"{alerts_count.get('Critical', 0) + alerts_count.get('High', 0)}",
                "Blocking or near-blocking findings.",
            )
        )
        card_slots = [
            "A4:B7",
            "C4:D7",
            "E4:F7",
            "G4:H7",
            "I4:J7",
            "K4:L7",
            "M4:N7",
            "O4:P7",
        ]
        for slot, (title, value, note) in zip(card_slots, cards):
            self._write_dashboard_card(
                worksheet,
                slot,
                title,
                value,
                note,
                card_title_format,
                card_value_format,
                card_note_format,
            )

        worksheet.merge_range(
            "A9:P10",
            self._dashboard_verdict(
                score_result,
                sia4010_results,
                rooms_data,
                self.include_sia4010,
                sia3802_results,
            ),
            muted_format,
        )

        worksheet.merge_range(
            "A12:G12",
            (
                "SIA 380/2 Model Scores"
                if self.include_sia4010
                else "SIA 380/2 Compliance by Domain"
            ),
            section_format,
        )
        sia3802_rows = (
            self._action_dashboard_sia3802_score_rows(score_result)
            if self.include_sia4010
            else []
        )
        if self.include_sia4010:
            worksheet.write_row("A13", ["Domain", "Score", "Meaning"], header_format)
            for row_index, row_values in enumerate(sia3802_rows, start=13):
                worksheet.write(row_index, 0, row_values[0], cell_format)
                worksheet.write(row_index, 1, row_values[1], score_format)
                worksheet.write(row_index, 2, row_values[2], cell_format)
            worksheet.conditional_format(
                13,
                1,
                12 + len(sia3802_rows),
                1,
                {
                    # Accent blue, not green: a data bar shows magnitude, and a
                    # green bar behind a score of 20 reads as a pass it is not.
                    "type": "data_bar",
                    "bar_color": report_style.XW_CHART_FILL,
                    "min_type": "num",
                    "min_value": 0,
                    "max_type": "num",
                    "max_value": 100,
                },
            )
        else:
            worksheet.write_row(
                "A13",
                ["Domain", "Verdict", "Blocking", "Missing", "Advisory"],
                header_format,
            )
            for row_index, domain in enumerate(compliance_verdict.domains, start=13):
                worksheet.write(row_index, 0, domain.domain.title(), cell_format)
                worksheet.write(
                    row_index, 1, domain.status.replace("_", " "), cell_format
                )
                worksheet.write(row_index, 2, domain.blocking_count, number_format)
                worksheet.write(row_index, 3, domain.missing_count, number_format)
                worksheet.write(row_index, 4, domain.advisory_count, number_format)

        if self.include_sia4010:
            worksheet.merge_range(
                "I12:P12", "SIA 4010 Official Validation Scores", section_format
            )
            worksheet.write_row(
                "I13", ["Area / test", "Score", "Status / evidence"], header_format
            )
            sia4010_rows = self._action_dashboard_sia4010_score_rows(
                score_result, sia4010_results
            )
            for row_index, row_values in enumerate(sia4010_rows, start=13):
                worksheet.write(row_index, 8, row_values[0], cell_format)
                worksheet.write(row_index, 9, row_values[1], score_format)
                worksheet.write(row_index, 10, row_values[2], cell_format)
            if sia4010_rows:
                worksheet.conditional_format(
                    13,
                    9,
                    12 + len(sia4010_rows),
                    9,
                    {
                        # Navy, matching the normative series in the dashboard charts:
                        # SIA 4010 readiness is not the same axis as a 380/2 score.
                        "type": "data_bar",
                        "bar_color": report_style.XW_CHART_FILL_NORMATIVE,
                        "min_type": "num",
                        "min_value": 0,
                        "max_type": "num",
                        "max_value": 100,
                    },
                )

        worksheet.merge_range(
            "A22:P22",
            "Detailed Action Matrix - Change In VE Or Provide Evidence",
            section_format,
        )
        headers = [
            "Priority",
            "Standard",
            "Domain",
            "Construction / scope",
            "Rule",
            "Item score",
            "Current",
            "Limit",
            "Gap",
            "Status",
            "What to change / do",
            "Evidence needed",
            "Owner",
            "Issue count",
            "Detail sheet",
            "Evidence sample",
        ]
        start_row = 22
        worksheet.write_row(start_row, 0, headers, header_format)

        row = start_row + 1
        for group in alert_groups[:24]:
            rule = str(group.get("rule", "") or "")
            current_value, limit_value, gap_value = (
                self._action_dashboard_values_for_group(group, sia4010_results)
            )
            item_score = self._action_item_score_for_group(group, sia4010_results)
            priority = str(group.get("priority", "") or "")
            detail_sheet = self._detail_sheet_for_alert_group(group)

            priority_format = (
                p1_format
                if priority == "P1"
                else (p2_format if priority == "P2" else p3_format)
            )
            status_text = self._status_for_alert_group(group)
            status_format = self._action_status_format(
                item_score, ok_format, warn_format, fail_format
            )

            worksheet.write(row, 0, priority, priority_format)
            worksheet.write(row, 1, self._standard_for_alert_group(group), cell_format)
            worksheet.write(row, 2, group.get("category", ""), cell_format)
            worksheet.write(row, 3, group.get("construction", ""), cell_format)
            worksheet.write(row, 4, rule, cell_format)
            worksheet.write(row, 5, item_score, score_format)
            self._write_optional_number(
                worksheet, row, 6, current_value, decimal_format, cell_format
            )
            self._write_optional_number(
                worksheet, row, 7, limit_value, decimal_format, cell_format
            )
            self._write_optional_number(
                worksheet, row, 8, gap_value, gap_format, cell_format
            )
            worksheet.write(row, 9, status_text, status_format)
            worksheet.write(row, 10, self._action_for_alert_group(group), cell_format)
            worksheet.write(
                row, 11, self._p1_evidence_needed_for_group(group), cell_format
            )
            worksheet.write(row, 12, self._p1_owner_for_group(group), cell_format)
            worksheet.write(row, 13, int(group.get("count", 0) or 0), number_format)
            if detail_sheet:
                worksheet.write_url(
                    row,
                    14,
                    f"internal:'{detail_sheet}'!A1",
                    link_format,
                    string=detail_sheet,
                )
            else:
                worksheet.write(row, 14, "", cell_format)
            worksheet.write(
                row, 15, "; ".join(group.get("evidence_samples", [])[:2]), cell_format
            )
            worksheet.set_row(row, 48)
            row += 1

        if not alert_groups:
            worksheet.merge_range(
                row,
                0,
                row,
                len(headers) - 1,
                "No action item generated from current alerts.",
                cell_format,
            )
            row += 1

        if row > start_row + 1:
            worksheet.conditional_format(
                start_row + 1,
                5,
                row - 1,
                5,
                {
                    "type": "data_bar",
                    "bar_color": report_style.XW_CHART_FILL,
                    "min_type": "num",
                    "min_value": 0,
                    "max_type": "num",
                    "max_value": 100,
                },
            )
            worksheet.autofilter(start_row, 0, row - 1, len(headers) - 1)

        next_row = row + 1
        worksheet.merge_range(
            next_row, 0, next_row, 7, "Most important next step", section_format
        )
        worksheet.merge_range(
            next_row + 1,
            0,
            next_row + 3,
            7,
            self._action_dashboard_next_step(
                alert_groups, evidence_summary, dynamic_results
            ),
            muted_format,
        )
        worksheet.merge_range(next_row, 8, next_row, 15, "Safe wording", section_format)
        worksheet.merge_range(
            next_row + 1,
            8,
            next_row + 3,
            15,
            (
                "Use this workbook as a professional SIA 380/2 and SIA 4010 readiness report. Do not claim final SIA compliance or SIA 4010 validation until model blockers, evidence files and reviewer acceptance are complete."
                if self.include_sia4010
                else "Use the displayed SIA 380/2 verdict together with its blocking, advisory and outstanding-evidence details. This engineering assessment is not an official SIA certificate."
            ),
            muted_format,
        )

    def _write_client_summary_xlsxwriter(
        self,
        score_result: ScoreResult,
        sia3802_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
        rooms_data: List[Any],
        alert_groups: List[Dict[str, Any]],
    ):
        """Write a concise client/manager summary with safe claim wording."""
        worksheet = self.workbook.add_worksheet("CLIENT SUMMARY")
        worksheet.hide_gridlines(2)

        title_format = self.workbook.add_format(
            report_style.xw_format(
                "on_dark",
                size=18,
                bold=True,
                background="band_deep",
                border=None,
                align="left",
                valign="vcenter",
            )
        )
        section_format = self.workbook.add_format(
            report_style.xw_format(
                "on_dark",
                bold=True,
                background="band",
            )
        )
        cell_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                text_wrap=True,
                valign="top",
            )
        )
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                background="panel",
                text_wrap=True,
                valign="top",
            )
        )
        number_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                num_format="#,##0.0",
            )
        )
        count_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                num_format="#,##0",
            )
        )
        # The decision statement is a wrapped paragraph, not a verdict chip, so
        # it takes the status colours through xw_format rather than xw_status:
        # the latter centres its text, which would centre a sentence.
        _fail = report_style.status_presentation("fail")
        _pass = report_style.status_presentation("pass")
        _warning = report_style.status_presentation("warning")
        fail_format = self.workbook.add_format(
            report_style.xw_format(
                _fail.text,
                background=_fail.ground,
                text_wrap=True,
                valign="top",
            )
        )
        pass_format = self.workbook.add_format(
            report_style.xw_format(
                _pass.text,
                background=_pass.ground,
                text_wrap=True,
                valign="top",
            )
        )
        warning_format = self.workbook.add_format(
            report_style.xw_format(
                _warning.text,
                background=_warning.ground,
                text_wrap=True,
                valign="top",
            )
        )

        alerts_count = self._count_alerts_by_severity(score_result.alerts)
        evidence = sia4010_results.get("evidence", {}) or {}
        evidence_present = sum(
            1
            for item in SIA4010_REQUIRED_EVIDENCE
            if self._has_sia4010_evidence(evidence, item)
        )
        p1_groups = [group for group in alert_groups if group.get("priority") == "P1"]
        total_area = sum(
            self._safe_float(getattr(room, "area", 0.0)) for room in rooms_data
        )
        blocked_sia4010_tests = (
            self._count_blocked_sia4010_tests(sia4010_results)
            if self.include_sia4010
            else 0
        )

        worksheet.merge_range(
            "A1:H1",
            (
                "Client / Manager Summary"
                if self.include_sia4010
                else self._tr("excel_client_summary_title")
            ),
            title_format,
        )
        worksheet.merge_range(
            "A2:H3",
            (
                "Professional readiness statement for the active VE model. This page is intentionally conservative: it separates automated SIA 380/2 checks from official SIA 4010 validation evidence."
                if self.include_sia4010
                else self._tr("excel_client_summary_intro")
            ),
            note_format,
        )

        worksheet.write(
            "A5",
            (
                "Current decision"
                if self.include_sia4010
                else self._tr("excel_current_decision")
            ),
            section_format,
        )
        client_verdict = build_compliance_verdict(
            sia3802_results, sia4010_results, len(rooms_data)
        )
        if self.include_sia4010:
            decision_format = (
                fail_format if p1_groups or blocked_sia4010_tests else pass_format
            )
        elif client_verdict.sia3802_status == "COMPLIANT":
            decision_format = pass_format
        elif client_verdict.sia3802_status == "NOT_COMPLIANT":
            decision_format = fail_format
        else:
            decision_format = warning_format
        worksheet.merge_range(
            "B5:H6",
            self._dashboard_verdict(
                score_result,
                sia4010_results,
                rooms_data,
                self.include_sia4010,
                sia3802_results,
            ),
            decision_format,
        )

        worksheet.write("A8", "KPI", section_format)
        worksheet.write("B8", self._tr("excel_value"), section_format)
        worksheet.write("C8", self._tr("excel_interpretation"), section_format)
        kpis = [
            (
                self._tr("excel_rooms_analysed"),
                len(rooms_data),
                self._tr("excel_rooms_interpretation"),
                count_format,
            ),
            (
                self._tr("excel_floor_area_analysed"),
                total_area,
                self._tr("excel_floor_area_interpretation"),
                number_format,
            ),
            (
                self._tr("excel_p1_groups"),
                len(p1_groups),
                self._tr("excel_p1_interpretation"),
                count_format,
            ),
        ]
        if self.include_sia4010:
            kpis[0:0] = [
                (
                    "SIA 380/2 automated score",
                    float(score_result.compliance_score or 0.0),
                    "Weighted automated indicator only; it is not a full certificate.",
                    number_format,
                ),
                (
                    "Model health score",
                    float(score_result.health_score or 0.0),
                    "Data completeness and model quality indicator.",
                    number_format,
                ),
            ]
        if self.include_sia4010:
            kpis.append(
                (
                    "SIA 4010 evidence",
                    evidence_present,
                    f"Official evidence families detected out of {len(SIA4010_REQUIRED_EVIDENCE)}.",
                    count_format,
                )
            )
            kpis.append(
                (
                    "SIA 4010 blocked tests",
                    blocked_sia4010_tests,
                    "Tests remain blocked until official evidence is complete and reviewed.",
                    count_format,
                )
            )
        kpis.append(
            (
                self._tr("excel_high_critical"),
                alerts_count.get("Critical", 0) + alerts_count.get("High", 0),
                self._tr("excel_high_critical_interpretation"),
                count_format,
            )
        )
        row = 8
        for label, value, interpretation, value_format in kpis:
            row += 1
            worksheet.write(row, 0, label, cell_format)
            worksheet.write(row, 1, value, value_format)
            worksheet.write(row, 2, interpretation, cell_format)

        worksheet.write("A19", self._tr("excel_safe_claim"), section_format)
        worksheet.write("B19", self._tr("excel_use_avoid"), section_format)
        worksheet.write("C19", self._tr("excel_reason"), section_format)
        claim_rows = [
            (
                "Use",
                (
                    "Automated SIA 380/2 readiness review for directly extracted VE data."
                    if self.include_sia4010
                    else self._tr("excel_claim_supported")
                ),
                self._tr("excel_claim_supported_reason"),
            ),
            (
                "Avoid" if self.include_sia4010 else self._tr("excel_avoid"),
                (
                    "This model is fully SIA compliant."
                    if self.include_sia4010
                    else self._tr("excel_claim_avoid_full")
                ),
                (
                    "Current P1 items remain open and several MSP checks are not implemented yet."
                    if self.include_sia4010
                    else self._tr("excel_claim_open_items")
                ),
            ),
        ]
        if not self.include_sia4010:
            claim_rows[0] = (
                self._tr("excel_use"),
                claim_rows[0][1],
                claim_rows[0][2],
            )
        if self.include_sia4010:
            claim_rows.insert(
                1,
                (
                    "Use",
                    "SIA 4010 evidence readiness matrix.",
                    "The script scans evidence presence and keeps official tests NOT_CHECKABLE without proof.",
                ),
            )
            claim_rows.append(
                (
                    "Avoid",
                    "The software/model is SIA 4010 validated.",
                    "Official SIA test files, candidate outputs, reference comparisons and validation class confirmation are missing.",
                )
            )
        for offset, claim in enumerate(claim_rows, start=20):
            worksheet.write_row(offset, 0, claim, cell_format)

        worksheet.write("A27", self._tr("excel_immediate_decision"), section_format)
        worksheet.write("B27", self._tr("excel_owner"), section_format)
        worksheet.write("C27", self._tr("excel_evidence_expected"), section_format)
        next_rows = self._client_next_decision_rows(p1_groups, sia4010_results)
        for offset, item in enumerate(next_rows, start=28):
            worksheet.write_row(offset, 0, item, cell_format)

        worksheet.set_column("A:A", 28)
        worksheet.set_column("B:B", 20)
        worksheet.set_column("C:H", 32)
        worksheet.freeze_panes(8, 0)

    def _write_preflight_xlsxwriter(
        self,
        preflight_checks: List[Dict[str, Any]],
        rooms_data: List[Any],
        sia4010_results: Dict[str, Any],
    ):
        """Write execution readiness checks for the VE Run-button workflow."""
        worksheet = self.workbook.add_worksheet("PREFLIGHT")
        worksheet.hide_gridlines(2)

        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        subheader_format = self.workbook.add_format(SHARED_FORMATS["subheader"])
        cell_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                text_wrap=True,
                valign="top",
            )
        )
        # The three verdicts come from the shared roles rather than being
        # redefined here, so PREFLIGHT cannot drift from the rest of the report.
        pass_format = self.workbook.add_format(SHARED_FORMATS["pass"])
        warning_format = self.workbook.add_format(SHARED_FORMATS["warning"])
        fail_format = self.workbook.add_format(SHARED_FORMATS["fail"])
        # INFO and NOT_CHECKABLE are not verdicts: absent evidence must never
        # read as a pass, so they take the not_checkable presentation.
        info_format = self.workbook.add_format(report_style.xw_status("not_checkable"))
        number_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                num_format="#,##0",
            )
        )

        checks = preflight_checks or self._fallback_preflight_checks(
            rooms_data, sia4010_results
        )
        if not self.include_sia4010:
            checks = [
                check
                for check in checks
                if not any(
                    "4010" in str(check.get(field, "")).upper()
                    for field in ("check", "why", "action", "source", "observed", "id")
                )
            ]
        status_counts = Counter(str(check.get("status", "UNKNOWN")) for check in checks)

        worksheet.merge_range(
            "A1:G1",
            (
                "VE Run Preflight - Execution Readiness"
                if self.include_sia4010
                else "VE Run Preflight - Report Inputs"
            ),
            header_format,
        )
        worksheet.merge_range(
            "A2:G2",
            "These checks indicate whether the report can be interpreted with confidence. "
            "A FAIL here does not necessarily mean SIA non-compliance: it can indicate missing extraction data or missing evidence.",
            cell_format,
        )

        worksheet.write("A4", "KPI", header_format)
        kpis = [
            ("Checks", len(checks)),
            ("PASS", status_counts.get("PASS", 0)),
            ("WARNING", status_counts.get("WARNING", 0)),
            ("FAIL", status_counts.get("FAIL", 0)),
            (
                "INFO/NOT_CHECKABLE",
                status_counts.get("INFO", 0) + status_counts.get("NOT_CHECKABLE", 0),
            ),
        ]
        for offset, (label, value) in enumerate(kpis, start=5):
            worksheet.write(offset, 0, label, subheader_format)
            worksheet.write(offset, 1, value, number_format)

        start_row = 11
        worksheet.write_row(
            start_row,
            0,
            [
                "Status",
                "Check",
                "Observed",
                "Why it matters",
                "Action",
                "Owner",
                "Source",
            ],
            header_format,
        )
        row = start_row + 1
        for check in checks:
            status = str(check.get("status", "UNKNOWN"))
            status_format = self._preflight_status_format(
                status, pass_format, warning_format, fail_format, info_format, cell_format
            )
            worksheet.write(row, 0, status, status_format)
            worksheet.write(row, 1, check.get("check", ""), cell_format)
            worksheet.write(row, 2, check.get("observed", ""), cell_format)
            worksheet.write(row, 3, check.get("why", ""), cell_format)
            worksheet.write(row, 4, check.get("action", ""), cell_format)
            worksheet.write(row, 5, check.get("owner", "Model reviewer"), cell_format)
            worksheet.write(row, 6, check.get("source", "VE script"), cell_format)
            worksheet.set_row(row, 44)
            row += 1

        worksheet.autofilter(start_row, 0, max(start_row, row - 1), 6)
        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:A", 16)
        worksheet.set_column("B:B", 28)
        worksheet.set_column("C:E", 42)
        worksheet.set_column("F:F", 20)
        worksheet.set_column("G:G", 28)

    @staticmethod
    def _fallback_preflight_checks(
        rooms_data: List[Any], sia4010_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Return minimal preflight checks when the application layer did not supply them."""
        evidence = sia4010_results.get("evidence", {}) or {}
        classified_evidence_count = int(evidence.get("classified_file_count", 0) or 0)
        return [
            {
                "status": "PASS" if rooms_data else "FAIL",
                "check": "VE rooms extracted",
                "observed": f"{len(rooms_data)} room(s)",
                "why": "A compliance report is not meaningful if no thermal room was extracted.",
                "action": "Open the correct VE project/model and rerun from the VE Run button.",
                "source": "ModelAnalyzer.analyze_all_rooms",
            },
            {
                "status": "PASS" if classified_evidence_count else "NOT_CHECKABLE",
                "check": "SIA 4010 classified evidence files",
                "observed": f"{classified_evidence_count} classified evidence file(s), {len(evidence.get('files', []) or [])} total file(s) detected",
                "why": "SIA 4010 official validation cannot be claimed without official evidence files.",
                "action": "Place official files in sia4010_evidence and rerun.",
                "source": "SIA 4010 evidence folder",
            },
        ]

    @staticmethod
    def _preflight_status_format(
        status: str,
        pass_format: Any,
        warning_format: Any,
        fail_format: Any,
        info_format: Any,
        cell_format: Any,
    ) -> Any:
        """Return the Excel cell format for a preflight status."""
        status_upper = str(status or "").upper()
        if status_upper == "PASS":
            return pass_format
        if status_upper == "WARNING":
            return warning_format
        if status_upper == "FAIL":
            return fail_format
        if status_upper in {"INFO", "NOT_CHECKABLE", "UNKNOWN"}:
            return info_format
        return cell_format

    def _write_p1_remediation_xlsxwriter(
        self, alert_groups: List[Dict[str, Any]], sia4010_results: Dict[str, Any]
    ):
        """Write an actionable remediation table for manager-critical P1 items."""
        worksheet = self.workbook.add_worksheet("P1 REMEDIATION")
        worksheet.hide_gridlines(2)

        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        subheader_format = self.workbook.add_format(SHARED_FORMATS["subheader"])
        cell_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                text_wrap=True,
                valign="top",
            )
        )
        # P1 is the top severity on this board, so it takes the escalated
        # presentation: light type on the solid fail colour, not another red.
        p1_format = self.workbook.add_format(SHARED_FORMATS["critical"])
        number_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                num_format="#,##0",
            )
        )
        area_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                num_format="#,##0.0",
            )
        )
        decimal_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                num_format="0.000",
            )
        )
        gap_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                num_format="+0.000;-0.000;0.000",
            )
        )
        # A justified deviation is neither a pass nor a failure: it is a
        # documented decision, so it reads in the neutral accent, not in green.
        justified_format = self.workbook.add_format(
            report_style.xw_format(
                "accent",
                bold=True,
                background="table_header",
                align="center",
                text_wrap=True,
            )
        )

        p1_groups = [group for group in alert_groups if group.get("priority") == "P1"]
        evidence = sia4010_results.get("evidence", {}) or {}
        evidence_present = sum(
            1
            for item in SIA4010_REQUIRED_EVIDENCE
            if self._has_sia4010_evidence(evidence, item)
        )

        worksheet.merge_range("A1:N1", "P1 Remediation Board", header_format)
        worksheet.merge_range(
            "A2:N3",
            "This board converts the highest priority findings into owner-ready actions. It does not change the compliance score; it explains what must be treated or documented before a client compliance claim.",
            cell_format,
        )
        worksheet.write("A5", "KPI", header_format)
        worksheet.write("A6", "P1 groups", subheader_format)
        worksheet.write("B6", len(p1_groups), number_format)
        worksheet.write("A7", "P1 raw alerts", subheader_format)
        worksheet.write(
            "B7",
            sum(int(group.get("count", 0) or 0) for group in p1_groups),
            number_format,
        )
        # The SIA 4010 evidence tally has no place on a client 380/2 board.
        if self.include_sia4010:
            worksheet.write("A8", "SIA 4010 evidence families", subheader_format)
            worksheet.write(
                "B8", f"{evidence_present}/{len(SIA4010_REQUIRED_EVIDENCE)}", cell_format
            )

        headers = [
            "Priority",
            "Category",
            "Construction / scope",
            "Rule",
            "Issue count",
            "Affected area (m2)",
            "Current value",
            "Limit / required",
            "Gap",
            "Decision needed",
            "Recommended VE action",
            "Evidence needed",
            "Owner",
            "Status",
        ]
        start_row = 11
        worksheet.write_row(start_row, 0, headers, header_format)

        row = start_row + 1
        for group in p1_groups:
            current_value = self._p1_current_value_for_group(group)
            limit_value = self._p1_limit_for_group(group)
            rule = str(group.get("rule", "")).upper()
            justification = self._accepted_justification_for_group(group)
            if "SIA4010" in rule:
                current_value = float(evidence_present)
            gap_value = self._p1_gap_for_values(rule, current_value, limit_value)
            status_text = (
                "Justified by evidence"
                if justification
                else self._status_for_alert_group(group)
            )
            decision_text = (
                "Reviewer evidence is attached. Keep the model value, limit and justification visible in the audit pack."
                if justification
                else self._p1_decision_for_group(group)
            )
            action_text = (
                "No silent PASS: maintain the finding as justified and verify the evidence remains applicable after model changes."
                if justification
                else self._action_for_alert_group(group)
            )
            evidence_text = (
                describe_justification(justification)
                if justification
                else self._p1_evidence_needed_for_group(group)
            )

            worksheet.write(row, 0, group.get("priority", "P1"), p1_format)
            worksheet.write(row, 1, group.get("category", ""), cell_format)
            worksheet.write(row, 2, group.get("construction", ""), cell_format)
            worksheet.write(row, 3, group.get("rule", ""), cell_format)
            worksheet.write(row, 4, group.get("count", 0), number_format)
            worksheet.write(row, 5, group.get("affected_area", 0.0), area_format)
            self._write_optional_number(
                worksheet, row, 6, current_value, decimal_format, cell_format
            )
            self._write_optional_number(
                worksheet, row, 7, limit_value, decimal_format, cell_format
            )
            self._write_optional_number(
                worksheet, row, 8, gap_value, gap_format, cell_format
            )
            worksheet.write(row, 9, decision_text, cell_format)
            worksheet.write(row, 10, action_text, cell_format)
            worksheet.write(row, 11, evidence_text, cell_format)
            worksheet.write(row, 12, self._p1_owner_for_group(group), cell_format)
            worksheet.write(
                row, 13, status_text, justified_format if justification else cell_format
            )
            worksheet.set_row(row, 52)
            row += 1

        if not p1_groups:
            worksheet.merge_range(
                start_row + 1,
                0,
                start_row + 1,
                len(headers) - 1,
                "No P1 group detected in the current run.",
                cell_format,
            )
            row = start_row + 2

        worksheet.autofilter(start_row, 0, max(start_row, row - 1), len(headers) - 1)
        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:A", 12)
        worksheet.set_column("B:B", 16)
        worksheet.set_column("C:C", 28)
        worksheet.set_column("D:D", 30)
        worksheet.set_column("E:I", 15)
        worksheet.set_column("J:L", 46)
        worksheet.set_column("M:N", 18)

    def _write_facade_glazing_review_xlsxwriter(
        self,
        alert_groups: List[Dict[str, Any]],
        rooms_data: List[Any],
    ):
        """Write a construction-level facade/glazing action sheet."""
        worksheet = self.workbook.add_worksheet("FACADE GLAZING REVIEW")
        worksheet.hide_gridlines(2)
        worksheet.freeze_panes(8, 0)
        worksheet.set_column("A:A", 18)
        worksheet.set_column("B:B", 11)
        worksheet.set_column("C:C", 13)
        worksheet.set_column("D:G", 12)
        worksheet.set_column("H:J", 14)
        worksheet.set_column("K:K", 42)
        worksheet.set_column("L:M", 58)
        worksheet.set_column("N:N", 20)

        # This sheet carried a third palette of its own, an orange one. The
        # verdict cells keep their top alignment, which reads better beside the
        # wrapped justification columns.
        title_format = self.workbook.add_format(
            report_style.xw_format(
                "on_dark",
                size=16,
                bold=True,
                background="band_deep",
                border=None,
                align="left",
                valign="vcenter",
            )
        )
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                background="panel",
                border=None,
                text_wrap=True,
                valign="top",
            )
        )
        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        cell_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                valign="top",
                text_wrap=True,
            )
        )
        number_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                num_format="0.000",
                valign="top",
            )
        )
        area_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                num_format="0.0",
                valign="top",
            )
        )
        pass_format = self.workbook.add_format(
            report_style.xw_status("pass", valign="top")
        )
        # "Partial" is a reservation, not a failure: the warning presentation.
        partial_format = self.workbook.add_format(
            report_style.xw_status("warning", valign="top")
        )

        rows = self._build_facade_glazing_rows(alert_groups, rooms_data)
        reference_deviation_rows = sum(
            1
            for row in rows
            if "REFERENCE_DEVIATION" in {row["uw_status"], row["g_status"]}
        )
        missing_rows = sum(
            1 for row in rows if row.get("missing_evidence") not in (None, "", "None")
        )

        worksheet.merge_range(
            "A1:N1", "Facade Glazing Review - SIA 380/2 Action Sheet", title_format
        )
        worksheet.merge_range(
            "A2:N4",
            (
                "Construction-level view for facade/glazing review. Table 2 values are reference-project inputs, "
                "not standalone component compliance limits. The sheet therefore separates reference deviations "
                "from genuinely missing EN 410, shading-control or active g_total evidence."
            ),
            note_format,
        )
        worksheet.write("A6", "Constructions", header_format)
        worksheet.write("B6", len(rows), cell_format)
        worksheet.write("C6", "Reference-deviation rows", header_format)
        worksheet.write("D6", reference_deviation_rows, cell_format)
        worksheet.write("E6", "Rows missing evidence", header_format)
        worksheet.write("F6", missing_rows, cell_format)
        worksheet.write("G6", "SIA source", header_format)
        worksheet.merge_range(
            "H6:N6",
            "SIA 380/2:2022 FR, table 2 pages PDF 32-35 and table 10 page PDF 46",
            cell_format,
        )

        headers = [
            "Construction",
            "Windows",
            "Area m2",
            "Avg Uw",
            "Avg g",
            "Max g",
            "g gap",
            "Uw reference status",
            "g reference status",
            "Evidence status",
            "Missing evidence",
            "Recommended action",
            "Evidence to collect",
            "Owner",
        ]
        for col, header in enumerate(headers):
            worksheet.write(7, col, header, header_format)

        if not rows:
            worksheet.merge_range(
                "A9:N9",
                "No external window/opening data was available in this run.",
                cell_format,
            )
            return

        for row_index, row_data in enumerate(rows, start=8):
            status_format = (
                partial_format
                if row_data["status"] in {"MISSING_EVIDENCE", "REFERENCE_DEVIATION"}
                else pass_format
            )
            worksheet.write(row_index, 0, row_data["construction"], cell_format)
            worksheet.write(row_index, 1, row_data["window_count"], cell_format)
            worksheet.write(row_index, 2, row_data["area"], area_format)
            self._write_optional_number(
                worksheet, row_index, 3, row_data["avg_u"], number_format, cell_format
            )
            self._write_optional_number(
                worksheet, row_index, 4, row_data["avg_g"], number_format, cell_format
            )
            self._write_optional_number(
                worksheet, row_index, 5, row_data["max_g"], number_format, cell_format
            )
            self._write_optional_number(
                worksheet, row_index, 6, row_data["g_gap"], number_format, cell_format
            )
            uw_format = (
                partial_format
                if row_data["uw_status"] in {"MISSING", "REFERENCE_DEVIATION"}
                else pass_format
            )
            g_format = (
                partial_format
                if row_data["g_status"] in {"MISSING", "REFERENCE_DEVIATION"}
                else pass_format
            )
            worksheet.write(row_index, 7, row_data["uw_status"], uw_format)
            worksheet.write(row_index, 8, row_data["g_status"], g_format)
            worksheet.write(row_index, 9, row_data["status"], status_format)
            worksheet.write(row_index, 10, row_data["missing_evidence"], cell_format)
            worksheet.write(row_index, 11, row_data["recommended_action"], cell_format)
            worksheet.write(row_index, 12, row_data["evidence_needed"], cell_format)
            worksheet.write(row_index, 13, row_data["owner"], cell_format)

    def _write_frame_fraction_audit_xlsxwriter(self, rooms_data: List[Any]):
        """Write construction-level frame-fraction evidence and actions."""
        worksheet = self.workbook.add_worksheet("FRAME FRACTION AUDIT")
        worksheet.hide_gridlines(2)
        worksheet.freeze_panes(8, 0)
        worksheet.set_column("A:A", 18)
        worksheet.set_column("B:C", 12)
        worksheet.set_column("D:H", 14)
        worksheet.set_column("I:I", 16)
        worksheet.set_column("J:L", 44)

        title_format = self.workbook.add_format(
            report_style.xw_format(
                "on_dark",
                size=16,
                bold=True,
                background="band_deep",
                border=None,
                align="left",
                valign="vcenter",
            )
        )
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                background="panel",
                border=None,
                text_wrap=True,
                valign="top",
            )
        )
        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        cell_format = self.workbook.add_format(
            report_style.xw_format("ink", text_wrap=True, valign="top")
        )
        number_format = self.workbook.add_format(
            report_style.xw_format("ink", num_format="0.000", valign="top")
        )
        area_format = self.workbook.add_format(
            report_style.xw_format("ink", num_format="0.0", valign="top")
        )
        pass_format = self.workbook.add_format(SHARED_FORMATS["pass"])
        # A partial result is a reservation, not a failure.
        partial_format = self.workbook.add_format(SHARED_FORMATS["warning"])
        # A justified deviation is a documented decision: neutral accent, not
        # green, so it is never mistaken for a pass.
        justified_format = self.workbook.add_format(
            report_style.xw_format(
                "accent",
                bold=True,
                background="table_header",
                align="center",
                text_wrap=True,
            )
        )

        rows = self._build_frame_fraction_rows(rooms_data)
        failing_rows = sum(1 for row in rows if row["status"] == "REFERENCE_DEVIATION")
        missing_rows = sum(1 for row in rows if row["status"] == "MISSING")

        worksheet.merge_range(
            "A1:L1", "Frame Fraction Audit - SIA 380/2 Table 2", title_format
        )
        worksheet.merge_range(
            "A2:L4",
            (
                "Construction-level comparison of window frame fraction ff with the SIA 380/2 table 2 "
                "reference-project value. A deviation remains visible for the global project/reference calculation; "
                "it is not a standalone component-compliance failure."
            ),
            note_format,
        )
        worksheet.write("A6", "Constructions", header_format)
        worksheet.write("B6", len(rows), cell_format)
        worksheet.write("C6", "Reference deviations", header_format)
        worksheet.write("D6", failing_rows, cell_format)
        worksheet.write("E6", "Missing rows", header_format)
        worksheet.write("F6", missing_rows, cell_format)
        worksheet.write("G6", "Reference value", header_format)
        worksheet.write(
            "H6", SIA3802_LIMIT_VALUES["window_frame_fraction"], number_format
        )

        headers = [
            "Construction",
            "Windows",
            "Area m2",
            "Avg frame fraction",
            "Max frame fraction",
            "Reference value",
            "Deviation windows",
            "Missing values",
            "Status",
            "Action",
            "Evidence to collect",
            "Owner",
        ]
        worksheet.write_row(7, 0, headers, header_format)

        if not rows:
            worksheet.merge_range(
                "A9:L9",
                "No external window frame-fraction data was available in this run.",
                cell_format,
            )
            return

        for row_index, row_data in enumerate(rows, start=8):
            status_format = (
                justified_format
                if row_data["status"] == "JUSTIFIED_BY_EVIDENCE"
                else (
                    partial_format
                    if row_data["status"] == "REFERENCE_DEVIATION"
                    else (
                        partial_format if row_data["status"] == "MISSING" else pass_format
                    )
                )
            )
            worksheet.write(row_index, 0, row_data["construction"], cell_format)
            worksheet.write(row_index, 1, row_data["window_count"], cell_format)
            worksheet.write(row_index, 2, row_data["area"], area_format)
            self._write_optional_number(
                worksheet,
                row_index,
                3,
                row_data["avg_frame_fraction"],
                number_format,
                cell_format,
            )
            self._write_optional_number(
                worksheet,
                row_index,
                4,
                row_data["max_frame_fraction"],
                number_format,
                cell_format,
            )
            worksheet.write(row_index, 5, row_data["limit"], number_format)
            worksheet.write(row_index, 6, row_data["fail_count"], cell_format)
            worksheet.write(row_index, 7, row_data["missing_count"], cell_format)
            worksheet.write(row_index, 8, row_data["status"], status_format)
            worksheet.write(row_index, 9, row_data["action"], cell_format)
            worksheet.write(row_index, 10, row_data["evidence"], cell_format)
            worksheet.write(row_index, 11, row_data["owner"], cell_format)
            worksheet.set_row(row_index, 46)

        worksheet.autofilter(7, 0, max(7, 7 + len(rows)), len(headers) - 1)

    def _write_envelope_u_review_xlsxwriter(self, rooms_data: List[Any]):
        """Write envelope U-value remediation rows by construction."""
        worksheet = self.workbook.add_worksheet("ENVELOPE U REVIEW")
        worksheet.hide_gridlines(2)
        worksheet.freeze_panes(8, 0)
        worksheet.set_column("A:A", 13)
        worksheet.set_column("B:B", 30)
        worksheet.set_column("C:D", 12)
        worksheet.set_column("E:H", 14)
        worksheet.set_column("I:I", 16)
        worksheet.set_column("J:L", 46)

        title_format = self.workbook.add_format(
            report_style.xw_format(
                "on_dark",
                size=16,
                bold=True,
                background="band_deep",
                border=None,
                align="left",
                valign="vcenter",
            )
        )
        # This sheet was red throughout -- bands, hairlines and the reading note
        # alike -- so an envelope review of a compliant model still looked like
        # a failure, and its own fail cells had nothing left to stand out
        # against.
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                background="panel",
                border=None,
                text_wrap=True,
                valign="top",
            )
        )
        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        cell_format = self.workbook.add_format(
            report_style.xw_format("ink", text_wrap=True, valign="top")
        )
        number_format = self.workbook.add_format(
            report_style.xw_format("ink", num_format="0.000", valign="top")
        )
        area_format = self.workbook.add_format(
            report_style.xw_format("ink", num_format="0.0", valign="top")
        )
        pass_format = self.workbook.add_format(SHARED_FORMATS["pass"])
        partial_format = self.workbook.add_format(SHARED_FORMATS["warning"])
        justified_format = self.workbook.add_format(
            report_style.xw_format(
                "accent",
                bold=True,
                background="table_header",
                align="center",
                text_wrap=True,
            )
        )

        rows = self._build_envelope_u_rows(rooms_data)
        failing_rows = sum(1 for row in rows if row["status"] == "REFERENCE_DEVIATION")
        missing_rows = sum(1 for row in rows if row["status"] == "MISSING")

        worksheet.merge_range(
            "A1:L1", "Envelope U-Value Review - SIA 380/2 Table 3", title_format
        )
        worksheet.merge_range(
            "A2:L4",
            (
                "Construction-level comparison for external walls, roofs and ground floors. Table 3 values are "
                "reference-project inputs; deviations remain visible for the global comparison and are not "
                "standalone component-compliance failures."
            ),
            note_format,
        )
        worksheet.write("A6", "Rows", header_format)
        worksheet.write("B6", len(rows), cell_format)
        worksheet.write("C6", "Reference deviations", header_format)
        worksheet.write("D6", failing_rows, cell_format)
        worksheet.write("E6", "Missing rows", header_format)
        worksheet.write("F6", missing_rows, cell_format)
        worksheet.write("G6", "Source", header_format)
        worksheet.merge_range(
            "H6:L6", "SIA 380/2:2022 FR, table 3 reference-project U-values", cell_format
        )

        headers = [
            "Type",
            "Construction(s)",
            "Surfaces",
            "Net area m2",
            "Avg U",
            "Max U",
            "Reference value",
            "Gap",
            "Status",
            "Action",
            "Evidence to collect",
            "Owner",
        ]
        worksheet.write_row(7, 0, headers, header_format)

        if not rows:
            worksheet.merge_range(
                "A9:L9",
                "No external opaque envelope surfaces were available in this run.",
                cell_format,
            )
            return

        for row_index, row_data in enumerate(rows, start=8):
            status_format = (
                justified_format
                if row_data["status"] == "JUSTIFIED_BY_EVIDENCE"
                else (
                    partial_format
                    if row_data["status"] == "REFERENCE_DEVIATION"
                    else (
                        partial_format if row_data["status"] == "MISSING" else pass_format
                    )
                )
            )
            worksheet.write(row_index, 0, row_data["surface_type"], cell_format)
            worksheet.write(row_index, 1, row_data["construction"], cell_format)
            worksheet.write(row_index, 2, row_data["surface_count"], cell_format)
            worksheet.write(row_index, 3, row_data["net_area"], area_format)
            self._write_optional_number(
                worksheet, row_index, 4, row_data["avg_u"], number_format, cell_format
            )
            self._write_optional_number(
                worksheet, row_index, 5, row_data["max_u"], number_format, cell_format
            )
            self._write_optional_number(
                worksheet, row_index, 6, row_data["limit"], number_format, cell_format
            )
            self._write_optional_number(
                worksheet, row_index, 7, row_data["gap"], number_format, cell_format
            )
            worksheet.write(row_index, 8, row_data["status"], status_format)
            worksheet.write(row_index, 9, row_data["action"], cell_format)
            worksheet.write(row_index, 10, row_data["evidence"], cell_format)
            worksheet.write(row_index, 11, row_data["owner"], cell_format)
            worksheet.set_row(row_index, 46)

        worksheet.autofilter(7, 0, max(7, 7 + len(rows)), len(headers) - 1)

    def _write_ve_g_values_audit_xlsxwriter(self, rooms_data: List[Any]):
        """Write a VE/API audit sheet for glazing g-value traceability."""
        worksheet = self.workbook.add_worksheet("VE G-VALUES AUDIT")
        worksheet.hide_gridlines(2)
        worksheet.freeze_panes(8, 0)
        worksheet.set_column("A:A", 18)
        worksheet.set_column("B:C", 11)
        worksheet.set_column("D:I", 14)
        worksheet.set_column("J:K", 22)
        worksheet.set_column("L:L", 14)
        worksheet.set_column("M:O", 34)
        worksheet.set_column("P:R", 48)

        title_format = self.workbook.add_format(
            report_style.xw_format(
                "on_dark",
                size=16,
                bold=True,
                background="band_deep",
                border=None,
                align="left",
                valign="vcenter",
            )
        )
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                background="panel",
                border=None,
                text_wrap=True,
                valign="top",
            )
        )
        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        cell_format = self.workbook.add_format(
            report_style.xw_format("ink", valign="top", text_wrap=True)
        )
        number_format = self.workbook.add_format(
            report_style.xw_format("ink", num_format="0.000", valign="top")
        )
        area_format = self.workbook.add_format(
            report_style.xw_format("ink", num_format="0.0", valign="top")
        )
        pass_format = self.workbook.add_format(
            report_style.xw_status("pass", valign="top")
        )
        fail_format = self.workbook.add_format(
            report_style.xw_status("fail", valign="top")
        )
        partial_format = self.workbook.add_format(
            report_style.xw_status("warning", valign="top")
        )
        info_format = self.workbook.add_format(
            report_style.xw_status("not_checkable", valign="top")
        )

        rows = self._build_ve_g_values_audit_rows(rooms_data)
        proven_rows = sum(
            1 for row in rows if row["g_proof_status"] == "PROVES_CDB_G_IS_NOT_EN410"
        )
        action_rows = sum(
            1
            for row in rows
            if row["g_total_status"]
            in {
                "CALCULATION_REQUIRED",
                "BASE_G_ABOVE_REFERENCE_NO_ACTIVE_SHADING",
            }
        )

        worksheet.merge_range(
            "A1:R1", "VE G-Values Audit - VEScripts Traceability", title_format
        )
        worksheet.merge_range(
            "A2:R4",
            (
                "This sheet uses the documented IESVE API route VECdbConstruction.get_g_values() "
                "and VECdbConstruction.get_properties() to prove which g-value is being used. "
                "VEScripts documents bs_en_410, building_regulations and bfrc, plus CDB shading fields; "
                "it does not document a direct g_total_with_shading field, so shaded g-total values need "
                "a direct exposed value, manufacturer evidence or a reviewed ISO 52022-3 / ISO 15099 calculation."
            ),
            note_format,
        )
        worksheet.write("A6", "Constructions", header_format)
        worksheet.write("B6", len(rows), cell_format)
        worksheet.write("C6", "CDB g != EN 410", header_format)
        worksheet.write("D6", proven_rows, cell_format)
        worksheet.write("E6", "Glazing / g_total actions", header_format)
        worksheet.write("F6", action_rows, cell_format)
        worksheet.write("G6", "VEScripts source", header_format)
        worksheet.merge_range(
            "H6:R6",
            "VEScripts.pdf pages 198-200: get_g_values() and documented CDB glazing/shade fields",
            cell_format,
        )

        headers = [
            "Construction",
            "Windows",
            "Area m2",
            "Selected SIA g",
            "Selected source",
            "CDB g_value",
            "bs_en_410",
            "building_regulations",
            "bfrc",
            "g proof status",
            "Delta CDB-EN410",
            "Shading fields",
            "Shading active/type",
            "Shading control",
            "Shading optical evidence",
            "g_total with shading",
            "g_total status",
            "Recommended action",
        ]
        for col, header in enumerate(headers):
            worksheet.write(7, col, header, header_format)

        if not rows:
            worksheet.merge_range(
                "A9:R9",
                "No external glazing constructions were available in this run.",
                cell_format,
            )
            return

        for row_index, row_data in enumerate(rows, start=8):
            proof_format = self._ve_g_proof_format(
                row_data["g_proof_status"],
                pass_format,
                partial_format,
                fail_format,
                info_format,
            )
            g_total_format = self._ve_g_total_format(
                row_data["g_total_status"],
                pass_format,
                partial_format,
                fail_format,
                info_format,
            )
            worksheet.write(row_index, 0, row_data["construction"], cell_format)
            worksheet.write(row_index, 1, row_data["window_count"], cell_format)
            worksheet.write(row_index, 2, row_data["area"], area_format)
            self._write_optional_number(
                worksheet,
                row_index,
                3,
                row_data["selected_sia_g"],
                number_format,
                cell_format,
            )
            worksheet.write(row_index, 4, row_data["selected_source"], cell_format)
            self._write_optional_number(
                worksheet,
                row_index,
                5,
                row_data["cdb_g_value"],
                number_format,
                cell_format,
            )
            self._write_optional_number(
                worksheet, row_index, 6, row_data["bs_en_410"], number_format, cell_format
            )
            self._write_optional_number(
                worksheet,
                row_index,
                7,
                row_data["building_regulations"],
                number_format,
                cell_format,
            )
            self._write_optional_number(
                worksheet, row_index, 8, row_data["bfrc"], number_format, cell_format
            )
            worksheet.write(row_index, 9, row_data["g_proof_status"], proof_format)
            self._write_optional_number(
                worksheet,
                row_index,
                10,
                row_data["delta_cdb_en410"],
                number_format,
                cell_format,
            )
            worksheet.write(row_index, 11, row_data["shading_field_count"], cell_format)
            worksheet.write(row_index, 12, row_data["shading_type"], cell_format)
            worksheet.write(row_index, 13, row_data["shading_control"], cell_format)
            worksheet.write(
                row_index, 14, row_data["shading_optical_evidence"], cell_format
            )
            self._write_optional_number(
                worksheet, row_index, 15, row_data["g_total"], number_format, cell_format
            )
            worksheet.write(row_index, 16, row_data["g_total_status"], g_total_format)
            worksheet.write(row_index, 17, row_data["recommended_action"], cell_format)
            worksheet.set_row(row_index, 48)

        worksheet.autofilter(7, 0, max(7, 7 + len(rows)), len(headers) - 1)

    def _write_assumptions_limits_xlsxwriter(
        self,
        score_result: ScoreResult,
        sia4010_results: Dict[str, Any],
        rooms_data: List[Any],
    ):
        """Write explicit assumptions and limitations for audit-safe delivery."""
        worksheet = self.workbook.add_worksheet("ASSUMPTIONS LIMITS")
        worksheet.hide_gridlines(2)

        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        subheader_format = self.workbook.add_format(SHARED_FORMATS["subheader"])
        cell_format = self.workbook.add_format(
            report_style.xw_format("ink", text_wrap=True, valign="top")
        )
        warning_format = self.workbook.add_format(
            report_style.xw_status("warning", valign="top")
        )
        blocker_format = self.workbook.add_format(SHARED_FORMATS["critical"])
        number_format = self.workbook.add_format(
            report_style.xw_format("ink", num_format="#,##0.0")
        )

        evidence = sia4010_results.get("evidence", {}) or {}
        classified_evidence_count = int(evidence.get("classified_file_count", 0) or 0)
        blocked_sia4010_tests = self._count_blocked_sia4010_tests(sia4010_results)

        worksheet.merge_range(
            "A1:F1", "Assumptions, Limits and Certification Guardrails", header_format
        )
        worksheet.merge_range(
            "A2:F3",
            "This sheet is part of the professional QA layer. It explains what the report can support today and which claims must remain blocked until missing VE data or official SIA evidence is provided.",
            cell_format,
        )

        worksheet.write("A5", "KPI", header_format)
        worksheet.write("B5", "Value", header_format)
        worksheet.write("C5", "Meaning", header_format)
        kpis = [
            (
                "SIA 380/2 automated score",
                float(score_result.compliance_score or 0.0),
                "Automated/partial checks only.",
            ),
            (
                "Model health score",
                float(score_result.health_score or 0.0),
                "Data quality and completeness indicator.",
            ),
            ("Rooms analysed", len(rooms_data), "Extracted from the active VE model."),
            (
                "SIA 4010 classified evidence files",
                classified_evidence_count,
                "Official-looking files detected and classified by evidence family.",
            ),
            (
                "SIA 4010 blocked tests",
                blocked_sia4010_tests,
                "Tests still blocked until official evaluation evidence is complete and reviewed.",
            ),
        ]
        if not self.include_sia4010:
            kpis = [
                kpi
                for kpi in kpis
                if "4010" not in str(kpi[0]).upper()
                and "SCORE" not in str(kpi[0]).upper()
            ]
        for row, (label, value, meaning) in enumerate(kpis, start=6):
            worksheet.write(row, 0, label, subheader_format)
            worksheet.write(row, 1, value, number_format)
            worksheet.write(row, 2, meaning, cell_format)

        # -- Per-category compliance coverage summary --
        cat_header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        cat_pass_format = self.workbook.add_format(
            report_style.xw_status("pass", valign="top")
        )
        cat_partial_format = self.workbook.add_format(
            report_style.xw_status("warning", valign="top")
        )
        cat_nc_format = self.workbook.add_format(
            report_style.xw_status("not_checkable", valign="top")
        )

        worksheet.merge_range(
            "A12:F12", "Per-Category SIA 380/2 Coverage Summary", cat_header_format
        )
        cat_headers = [
            "Domain",
            "VE-testable criteria",
            "Reserves (external evidence)",
            "Category verdict",
            "VE coverage",
            "SIA article",
        ]
        cat_start = 13
        worksheet.write_row(cat_start, 0, cat_headers, cat_header_format)
        category_rows = [
            (
                "Envelope",
                "U-values walls, roof, floor — extracted and compared to table 3",
                "Thermal bridges: VE reads psi/chi but all-zero must be reviewed",
                "TESTABLE",
                "Automated",
                "SIA 380/2:2022 table 3",
            ),
            (
                "Openings",
                "Uw, g_perp, tau_v, frame fraction, WWR — extracted from CDB",
                "g-value EN 410 mapping; active g_total with shading",
                "TESTABLE",
                "Automated + review",
                "SIA 380/2:2022 table 2",
            ),
            (
                "Ventilation",
                "Infiltration rate, mechanical ventilation rate, control class",
                "AHU heat recovery, duct leakage class, control strategy evidence",
                "TESTABLE WITH RESERVES",
                "Partial + evidence",
                "SIA 380/2:2022 tables 2 and 4",
            ),
            (
                "Internal gains",
                "Lighting power, equipment power presence",
                "SIA 2024 use-category mapping, weekly schedules",
                "TESTABLE WITH RESERVES",
                "Partial + evidence",
                "SIA 380/2:2022 ch. 4; SIA 2024",
            ),
            (
                "HVAC efficiency",
                "EER/SEER by capacity band, SCOP indicative",
                "Generator class, EN 14825 SEER/SCoP verification; EER+ is documented reserve (VE cannot decompose)",
                "TESTABLE WITH RESERVES",
                "Partial + evidence",
                "SIA 380/2:2022 tables 5-9",
            ),
            (
                "Solar protection",
                "Shading device type detection",
                "Control strategy, active g_total, table 10 category",
                "BLOCKED UNTIL EVIDENCE",
                "VE partial",
                "SIA 380/2:2022 table 10; §7.1.2",
            ),
            (
                "Summer comfort",
                "SIA 180 upper/lower occupied-hour check from APS",
                "Weather provenance; unknown window operability uses 0 h screening but remains NOT_DETERMINED; unknown building status uses NEW (100 h) screening",
                "TESTABLE WITH RESERVES",
                "APS + conservative screening",
                "SIA 380/2:2022 §7.1.2.1; SIA 180",
            ),
            (
                "Electrical power §7.2.4",
                "Comparison to 7/12 W/m2 limit",
                "Required power figure is external evidence (design sizing)",
                "TESTABLE WITH EVIDENCE",
                "Evidence scan",
                "SIA 380/2:2022 §7.2.4",
            ),
            (
                "Design-day power",
                "Not implemented — documented reserve",
                "Dedicated design-day simulation workflow; does not block domain verdict",
                "RESERVE (NOT TESTABLE)",
                "Not implemented",
                "SIA 380/2:2022 §5.3.4-5",
            ),
            (
                "Global comparison §7.2.5.2",
                "Comparison logic implemented",
                "Project/reference index is external (reviewer)",
                "DECISIVE GATE — EXTERNAL",
                "Evidence scan",
                "SIA 380/2:2022 §7.2.5.2",
            ),
        ]
        for offset, (domain, testable, reserves, verdict, coverage, article) in enumerate(
            category_rows, start=cat_start + 1
        ):
            if verdict in ("TESTABLE", "TESTABLE WITH EVIDENCE"):
                fmt = cat_pass_format
            elif verdict in ("TESTABLE WITH RESERVES",):
                fmt = cat_partial_format
            else:
                fmt = cat_nc_format
            worksheet.write(offset, 0, domain, subheader_format)
            worksheet.write(offset, 1, testable, cell_format)
            worksheet.write(offset, 2, reserves, cell_format)
            worksheet.write(offset, 3, verdict, fmt)
            worksheet.write(offset, 4, coverage, cell_format)
            worksheet.write(offset, 5, article, cell_format)
            worksheet.set_row(offset, 42)

        headers = [
            "Status",
            "Assumption / limitation",
            "Why it matters",
            "Impact on claim",
            "Mitigation",
            "Source",
        ]
        start_row = cat_start + len(category_rows) + 3
        worksheet.write_row(start_row, 0, headers, header_format)
        rows = [
            (
                "BLOCKER",
                "SIA 4010 validation is evidence-based, not a building threshold check.",
                "The official validation needs test specifications, evaluation workbooks, candidate outputs, reference comparisons and validation class confirmation.",
                "No official SIA 4010 validation claim can be made.",
                "Populate sia4010_evidence with the official pack and rerun.",
                "SIA 4010:2023, table 62 and table 63.",
            ),
            (
                "CONTROLLED",
                "SIA 380/2 score covers direct/partial automated checks only.",
                "Dynamic method, SIA 2024, SIA 387/4 and APS/Vista result checks are not fully automated yet.",
                "Use as readiness indicator, not final certificate wording.",
                "Implement MSP dynamic result extraction and external evidence import.",
                "SIA 380/2:2022, chapters 4-7 and annex A.",
            ),
            (
                "REVIEW",
                "VE solar_factor is treated as the value to compare against g_perp until mapping is confirmed.",
                "SIA requires the correct normal solar factor / documented glazing-plus-shading method.",
                "Failing g-value alerts must be reviewed before remediation decisions are final.",
                "Confirm EN 410 g_perp, SHGC mapping and active shading g_total treatment.",
                "SIA 380/2:2022, table 2; SIA 4010 clause 3.1.5.",
            ),
            (
                "REVIEW",
                "WWR is used as a design risk indicator, not a direct SIA 380/2 pass/fail threshold.",
                "SIA 380/2 refers glazing ratios/use assumptions to other SIA references.",
                "WWR warnings guide review but should not be sold as direct non-compliance.",
                "Document SIA 2024 use category and reference calculation context.",
                "SIA 380/2:2022, table 2 note / SIA 2024 dependency.",
            ),
            (
                "REVIEW",
                "Infiltration is checked only when the VE unit is comparable to m3/(h.m2).",
                "Wrong unit conversion could create false pass/fail.",
                "Infiltration alerts require unit evidence.",
                "Store raw VE unit, conversion formula and reviewer approval.",
                "SIA 380/2:2022, table 2.",
            ),
            (
                "MSP GAP",
                "Ventilation, lighting, HVAC efficiencies, PV and hourly results need deeper API/result extraction.",
                "These criteria require system controls, SIA 2024/SIA 387/4 mapping and APS/Vista outputs.",
                "MSP required for sale-grade complete compliance workflow.",
                "Add dynamic result readers and system mapping worksheets.",
                "SIA 380/2 tables 4-10; SIA 4010 system tables.",
            ),
            (
                "REVIEW",
                "Summer comfort (SIA 180) requires complete APS, weather provenance, building status and window operability.",
                "Missing any element makes the overheating verdict NOT_CHECKABLE, never a silent pass.",
                "Summer comfort cannot be confirmed without a full annual simulation and reviewed metadata.",
                "Run an annual ApacheSim simulation; supply project metadata CSV with building status and weather provenance.",
                "SIA 380/2:2022 §7.1.2.1; SIA 180:2014 fig. 4.",
            ),
            (
                "REVIEW",
                "Solar protection control strategy (SIA 380/2 table 10) is not exposed by VE.",
                "The autonomous gate §7.1.2 blocks the overall verdict when the control category is missing.",
                "Overall verdict stays NOT_DETERMINED until control evidence is supplied.",
                "Provide SIA3802_solar_protection_<project>.csv with table 10 categories and active g_total.",
                "SIA 380/2:2022 tables 2 and 10; §7.1.2.2-5.",
            ),
            (
                "REVIEW",
                "SIA 2024 use-category mapping requires reviewer confirmation per thermal zone.",
                "Without it, internal gains, schedules and glazing assumptions are not comparable to normative references.",
                "Gains and schedules diagnostics remain informational, not verdict-bearing.",
                "Provide SIA2024_usage_mapping_<project>.csv reviewed and accepted.",
                "SIA 380/2:2022 chapter 4; SIA 2024:2021.",
            ),
            (
                "REVIEW",
                "AHU heat recovery, duct leakage class and pressure drops are only partially exposed by VE.",
                "Full evidence (L1/L2 class, recovery efficiency, pressure drops) must be supplied externally.",
                "Ventilation control comparison is incomplete without AHU technical data.",
                "Provide SIA3802_ahu_heat_recovery_<project>.csv with leakage class and recovery data.",
                "SIA 380/2:2022 table 4; SN EN 16798-3.",
            ),
            (
                "CONTROLLED",
                "Design-day power (heating/cooling) workflow is not implemented.",
                "SIA 380/2 prescribes dedicated design-day sequences; annual room peaks are not a substitute.",
                "Design power claims cannot be made until the dedicated workflow exists.",
                "Use annual peak loads as informational only; do not claim design-day compliance.",
                "SIA 380/2:2022 §5.3.4 and §5.3.5.",
            ),
            (
                "CONTROLLED",
                "Weekly schedules and exceptions are extracted as daily-equivalent profiles only.",
                "Full weekly/exception schedules are needed for normative traceability.",
                "Schedule compliance is informational until full profiles are exported and reviewed.",
                "Export complete weekly schedules from VE templates or supply reviewer confirmation.",
                "SIA 380/2:2022 chapter 4; SIA 2024:2021.",
            ),
        ]
        if not self.include_sia4010:
            # The client workbook is strictly scoped to the building assessment:
            # remove the software-validation row and its cross-references.
            rows = [
                tuple(
                    str(value)
                    .replace("Use as readiness indicator", "Use as supporting evidence")
                    .replace("; SIA 4010 clause 3.1.5", "")
                    .replace("; SIA 4010 system tables", "")
                    for value in row_values
                )
                for row_values in rows
                if "SIA 4010 validation is evidence-based" not in row_values[1]
            ]
        for offset, row_values in enumerate(rows, start=start_row + 1):
            status_format = (
                blocker_format
                if row_values[0] == "BLOCKER"
                else (
                    warning_format
                    if row_values[0] in {"REVIEW", "MSP GAP"}
                    else cell_format
                )
            )
            worksheet.write(offset, 0, row_values[0], status_format)
            for col, value in enumerate(row_values[1:], start=1):
                worksheet.write(offset, col, value, cell_format)
            worksheet.set_row(offset, 48)

        worksheet.autofilter(start_row, 0, start_row + len(rows), len(headers) - 1)
        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:A", 16)
        worksheet.set_column("B:E", 42)
        worksheet.set_column("F:F", 36)

    def _write_review_governance_xlsxwriter(
        self, dynamic_results: Dict[str, Any]
    ) -> None:
        """Write the seven reviewer-owned domains and every unresolved reserve."""

        worksheet = self.workbook.add_worksheet("REVIEW GOVERNANCE")
        worksheet.hide_gridlines(2)
        metadata = dynamic_results.get("reviewed_project_metadata", {}) or {}
        findings = evaluate_assessment_governance(
            metadata,
            dynamic_results,
            self.report_language,
        )
        summary = governance_summary(findings)

        title_format = self.workbook.add_format(report_style.xw_title())
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink", background="panel", text_wrap=True, valign="top"
            )
        )
        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        cell_format = self.workbook.add_format(
            report_style.xw_format("ink", text_wrap=True, valign="top")
        )
        status_formats = {
            GOVERNANCE_DOCUMENTED: self.workbook.add_format(
                report_style.xw_status("pass", valign="top")
            ),
            GOVERNANCE_RESERVE: self.workbook.add_format(
                report_style.xw_status("warning", valign="top")
            ),
            GOVERNANCE_BLOCKED: self.workbook.add_format(
                report_style.xw_status("fail", valign="top")
            ),
        }

        worksheet.merge_range(
            "A1:F1",
            report_text("section_title", self.report_language).upper(),
            title_format,
        )
        worksheet.merge_range(
            "A2:F4",
            (
                legal_wording(self.report_language)
                + " Overall governance status: "
                + governance_status_label(
                    str(summary.get("overall_status") or GOVERNANCE_BLOCKED),
                    self.report_language,
                )
                + ". "
                + report_text("traceability_note", self.report_language)
            ),
            note_format,
        )
        headers = (
            report_text("domain", self.report_language),
            report_text("status", self.report_language),
            report_text("evidence", self.report_language),
            report_text("uncertainty", self.report_language),
            report_text("action", self.report_language),
            report_text("responsible", self.report_language),
        )
        for column, label in enumerate(headers):
            worksheet.write(5, column, label, header_format)

        for row, finding in enumerate(findings, start=6):
            worksheet.write(row, 0, finding.title, cell_format)
            worksheet.write(
                row,
                1,
                governance_status_label(finding.status, self.report_language),
                status_formats.get(finding.status, status_formats[GOVERNANCE_BLOCKED]),
            )
            worksheet.write(row, 2, finding.evidence, cell_format)
            worksheet.write(row, 3, finding.uncertainty, cell_format)
            worksheet.write(row, 4, finding.required_action, cell_format)
            worksheet.write(row, 5, finding.responsible_party, cell_format)
            worksheet.set_row(row, 72)

        worksheet.freeze_panes(6, 0)
        worksheet.autofilter(5, 0, 5 + len(findings), 5)
        worksheet.set_column("A:A", 30)
        worksheet.set_column("B:B", 16)
        worksheet.set_column("C:C", 45)
        worksheet.set_column("D:E", 58)
        worksheet.set_column("F:F", 34)

    def _write_capability_guide_xlsxwriter(self):
        """Explain automation boundaries, evidence needs and ownership."""

        worksheet = self.workbook.add_worksheet("CAPABILITY GUIDE")
        worksheet.hide_gridlines(2)
        copy = {
            "en": {
                "title": "Capability boundaries - what is automated, what remains external, and why",
                "intro": "A missing item is not a software error and is never treated as a pass. Each row states the available automation, the technical boundary, the exact evidence needed, its owner and its effect on the verdict.",
                "headers": [
                    "Topic",
                    "What the tool reads or checks",
                    "What it cannot establish",
                    "Technical reason",
                    "Evidence required",
                    "Responsible party",
                    "Effect on verdict",
                ],
            },
            "fr": {
                "title": "Limites fonctionnelles - ce qui est automatisé, ce qui reste externe et pourquoi",
                "intro": "Une donnée manquante n'est pas une erreur du logiciel et n'est jamais considérée comme conforme. Chaque ligne indique l'automatisation disponible, la limite technique, la preuve exacte attendue, son responsable et l'effet sur le verdict.",
                "headers": [
                    "Sujet",
                    "Ce que le logiciel lit ou contrôle",
                    "Ce qu'il ne peut pas établir",
                    "Raison technique",
                    "Preuve requise",
                    "Responsable",
                    "Effet sur le verdict",
                ],
            },
        }.get(self.report_language)
        copy = copy or {
            "title": "Technical capability guide (English)",
            "intro": "This technical sheet is provided in English. A missing item is never treated as a pass; each row identifies the evidence and responsible party.",
            "headers": [
                "Topic",
                "What the tool reads or checks",
                "What it cannot establish",
                "Technical reason",
                "Evidence required",
                "Responsible party",
                "Effect on verdict",
            ],
        }
        title_format = self.workbook.add_format(
            report_style.xw_format("band", size=design.SIZE_TITLE, bold=True, border=None)
        )
        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        cell_format = self.workbook.add_format(
            report_style.xw_format("ink", text_wrap=True, valign="top")
        )
        topic_format = self.workbook.add_format(
            report_style.xw_format(
                "ink", background="panel", bold=True, text_wrap=True, valign="top"
            )
        )
        impact_style = report_style.xw_status("not_checkable", valign="top")
        impact_style["text_wrap"] = True
        impact_format = self.workbook.add_format(impact_style)
        worksheet.merge_range(
            "A1:G1",
            copy["title"],
            title_format,
        )
        worksheet.merge_range(
            "A2:G3",
            copy["intro"],
            cell_format,
        )
        headers = copy["headers"]
        worksheet.write_row(4, 0, headers, header_format)
        rows = CLIENT_CAPABILITY_GUIDE.get(
            self.report_language, CLIENT_CAPABILITY_GUIDE["en"]
        )
        if not self.include_sia4010:
            rows = [
                item
                for item in rows
                if "4010" not in " ".join(str(value) for value in item.values())
            ]
        for row_index, item in enumerate(rows, start=5):
            worksheet.write(row_index, 0, item["topic"], topic_format)
            worksheet.write(row_index, 1, item["available"], cell_format)
            worksheet.write(row_index, 2, item["missing"], cell_format)
            worksheet.write(row_index, 3, item["why"], cell_format)
            worksheet.write(row_index, 4, item["evidence"], cell_format)
            worksheet.write(row_index, 5, item["owner"], cell_format)
            worksheet.write(row_index, 6, item["effect"], impact_format)
            worksheet.set_row(row_index, 76)
        worksheet.freeze_panes(5, 1)
        worksheet.autofilter(4, 0, max(4, 4 + len(rows)), 6)
        worksheet.set_column("A:A", 28)
        worksheet.set_column("B:D", 38)
        worksheet.set_column("E:E", 42)
        worksheet.set_column("F:F", 28)
        worksheet.set_column("G:G", 38)

    def _write_audit_log_xlsxwriter(
        self,
        score_result: ScoreResult,
        sia4010_results: Dict[str, Any],
        rooms_data: List[Any],
        preflight_checks: List[Dict[str, Any]],
        dynamic_results: Dict[str, Any],
    ):
        """Write run metadata and evidence traceability for audit review."""
        worksheet = self.workbook.add_worksheet("AUDIT LOG")
        worksheet.hide_gridlines(2)

        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        subheader_format = self.workbook.add_format(SHARED_FORMATS["subheader"])
        cell_format = self.workbook.add_format(
            report_style.xw_format("ink", text_wrap=True, valign="top")
        )
        info_format = self.workbook.add_format(
            report_style.xw_format(
                "ink", background="panel", text_wrap=True, valign="top"
            )
        )
        number_format = self.workbook.add_format(
            report_style.xw_format("ink", num_format="#,##0.0")
        )

        evidence = sia4010_results.get("evidence", {}) or {}
        evidence_summary = (
            evidence.get("summary", {}) if isinstance(evidence, dict) else {}
        )
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_area = sum(
            self._safe_float(getattr(room, "area", 0.0)) for room in rooms_data
        )
        preflight_counts = Counter(
            str(item.get("status", "UNKNOWN")) for item in preflight_checks
        )
        template_remediation = dynamic_results.get("template_remediation", {}) or {}

        worksheet.merge_range("A1:F1", "Audit Log and Traceability", header_format)
        worksheet.merge_range(
            "A2:F3",
            "This sheet records run metadata, evidence state and guardrails used by the workbook. It supports audit review but does not create an official SIA certificate.",
            info_format,
        )

        metadata_rows = [
            ("Generated at", timestamp),
            ("Report path", self.output_path),
            ("Workbook generator", "swiss_sia.excel_report.ExcelReportGenerator"),
            (
                "Standards scope",
                (
                    "SIA 380/2:2022 FR; SIA 4010:2023 FR"
                    if self.include_sia4010
                    else "SIA 380/2:2022 FR"
                ),
            ),
            ("Rooms analysed", len(rooms_data)),
            ("Floor area analysed (m2)", total_area),
            ("SIA 380/2 automated score", float(score_result.compliance_score or 0.0)),
            ("Model health score", float(score_result.health_score or 0.0)),
            (
                "SIA 4010 official validation score",
                float(sia4010_results.get("score", 0.0) or 0.0),
            ),
            (
                "SIA 4010 evidence readiness score",
                float(sia4010_results.get("readiness_score", 0.0) or 0.0),
            ),
            ("SIA 4010 evidence status", evidence_summary.get("status", "UNKNOWN")),
            (
                "SIA 4010 validation class",
                evidence_summary.get("validation_class") or "Not confirmed",
            ),
            (
                "SIA 4010 validation class source",
                evidence_summary.get("validation_class_source", "not_selected"),
            ),
            (
                "SIA 4010 class manifest status",
                evidence_summary.get("validation_class_selection_status", "NOT_SELECTED"),
            ),
            (
                "SIA 4010 evidence families",
                f"{evidence_summary.get('present_count', 0)}/{evidence_summary.get('required_count', len(SIA4010_REQUIRED_EVIDENCE))}",
            ),
            ("APS/Vista status", dynamic_results.get("status", "NOT_CHECKABLE")),
            ("Selected APS file", dynamic_results.get("selected_aps_file") or "None"),
            (
                "Project weather file",
                dynamic_results.get("project_weather_file") or "Not exposed by VE",
            ),
            (
                "Selected APS weather references",
                self._compact_join(
                    dynamic_results.get("selected_aps_weather_references", []) or [],
                    empty="No EPW reference detected in APS",
                    max_chars=500,
                ),
            ),
            (
                "Skipped stale APS files",
                len(dynamic_results.get("skipped_aps_files", []) or []),
            ),
            ("APS files detected", len(dynamic_results.get("aps_files", []) or [])),
            (
                "Preflight PASS/WARNING/FAIL/NOT_CHECKABLE",
                f"{preflight_counts.get('PASS', 0)}/{preflight_counts.get('WARNING', 0)}/{preflight_counts.get('FAIL', 0)}/{preflight_counts.get('NOT_CHECKABLE', 0)}",
            ),
            (
                "Client template remediation status",
                template_remediation.get("status", "NOT RUN"),
            ),
            (
                "Template remediation integrity",
                template_remediation.get("integrity_status", "NOT_CHECKABLE"),
            ),
            (
                "Post-remediation audit",
                template_remediation.get("post_remediation_audit", "NOT_APPLICABLE"),
            ),
            ("Reviewed template", template_remediation.get("template_name") or "None"),
            ("Template target rooms", template_remediation.get("room_count", 0)),
            ("Template reviewer", template_remediation.get("reviewer") or "Not provided"),
            (
                "Template review date",
                template_remediation.get("review_date") or "Not provided",
            ),
            (
                "Template source",
                template_remediation.get("source_document") or "Not provided",
            ),
            (
                "Template source reference",
                template_remediation.get("source_reference") or "Not provided",
            ),
            ("Template preview plan", template_remediation.get("plan_path") or "None"),
            (
                "Template mutation receipt",
                template_remediation.get("receipt_path") or "None",
            ),
            (
                "Template operation compliance claim",
                template_remediation.get("compliance_claim", "NOT_GRANTED"),
            ),
        ]
        if not self.include_sia4010:
            metadata_rows = [
                (label, value)
                for (label, value) in metadata_rows
                if "4010" not in str(label).upper() and "SCORE" not in str(label).upper()
            ]
        metadata_rows.extend(
            [
                ("Client", self._context_value("client_name", "Not specified")),
                ("Project", self._context_value("project_name", self._project_label())),
                (
                    "Project address",
                    self._context_value("project_address", "Not specified"),
                ),
                (
                    "Client contact",
                    self._context_value("client_contact", "Not specified"),
                ),
                (
                    "Report reference",
                    self._context_value("report_reference", "Not specified"),
                ),
                ("Prepared by", self._context_value("prepared_by", "Not specified")),
                (
                    "Client-declared solar shading",
                    self._context_value("solar_shading", "TO_CONFIRM"),
                ),
                (
                    "Client-declared window operability",
                    self._context_value("window_operability", "TO_CONFIRM"),
                ),
                (
                    "Client-declared mechanical cooling",
                    self._context_value("mechanical_cooling", "TO_CONFIRM"),
                ),
                (
                    "Client building-strategy notes",
                    self._context_value("building_strategy_notes", "Not specified"),
                ),
                (
                    "Model Viewer image",
                    self._context_value("model_viewer_image_path", "Not provided"),
                ),
            ]
        )

        worksheet.write("A5", "Field", subheader_format)
        worksheet.write("B5", "Value", subheader_format)
        for row_index, (label, value) in enumerate(metadata_rows, start=6):
            worksheet.write(row_index, 0, label, cell_format)
            if isinstance(value, float):
                worksheet.write(row_index, 1, value, number_format)
            else:
                worksheet.write(row_index, 1, value, cell_format)

        # Start the evidence section after the complete metadata block. This is
        # deliberately dynamic because guarded remediation adds traceability
        # fields and must never overwrite earlier audit rows.
        row = 6 + len(metadata_rows) + 2
        if self.include_sia4010:
            worksheet.write(row, 0, "Official Evidence Family", subheader_format)
            worksheet.write(row, 1, "Status", subheader_format)
            worksheet.write(row, 2, "Detected Files", subheader_format)
            row += 1
            for item in SIA4010_REQUIRED_EVIDENCE:
                key = self._evidence_key_for_required_item(item)
                files = (
                    evidence.get(key, {}).get("files", [])
                    if isinstance(evidence.get(key), dict)
                    else []
                )
                worksheet.write(row, 0, item, cell_format)
                worksheet.write(
                    row,
                    1,
                    (
                        "PRESENT"
                        if self._has_sia4010_evidence(evidence, item)
                        else "MISSING"
                    ),
                    cell_format,
                )
                worksheet.write(
                    row,
                    2,
                    self._compact_join(
                        [
                            file_data.get("path") or file_data.get("name", "")
                            for file_data in files
                        ],
                        empty="No file detected",
                        max_chars=500,
                    ),
                    cell_format,
                )
                row += 1

        row += 2
        worksheet.write(row, 0, "Guardrail", subheader_format)
        worksheet.write(row, 1, "Required interpretation", subheader_format)
        guardrails = [
            (
                "SIA 380/2",
                "Only implemented direct checks can be read as automated findings; partial and missing evidence remain reviewer items.",
            ),
        ]
        if self.include_sia4010:
            guardrails.append(
                (
                    "SIA 4010",
                    "Official validation requires SIA test specifications, official evaluation workbooks, candidate results, reference comparisons and class confirmation.",
                )
            )
        guardrails.extend(
            [
                (
                    "Missing data",
                    "Missing or non-comparable data must never be treated as PASS.",
                ),
                (
                    "Report wording",
                    (
                        "Use readiness/audit wording until every blocker and official evidence requirement is reviewed."
                        if self.include_sia4010
                        else "Use the assessed compliance verdict together with its visible blockers, advisory findings and evidence reserves."
                    ),
                ),
            ]
        )
        for label, text in guardrails:
            row += 1
            worksheet.write(row, 0, label, cell_format)
            worksheet.write(row, 1, text, cell_format)

        worksheet.set_column("A:A", 34)
        worksheet.set_column("B:B", 48)
        worksheet.set_column("C:F", 40)
        worksheet.freeze_panes(5, 0)

    def _write_compliance_results_xlsxwriter(
        self, sia3802_results: Dict[str, Any], sia4010_results: Dict[str, Any]
    ):
        """Write the COMPLIANCE RESULTS sheet with xlsxwriter."""
        worksheet = self.workbook.add_worksheet("COMPLIANCE RESULTS")

        # Styles
        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        pass_format = self.workbook.add_format(SHARED_FORMATS["pass"])
        warning_format = self.workbook.add_format(SHARED_FORMATS["warning"])
        fail_format = self.workbook.add_format(SHARED_FORMATS["fail"])
        cell_format = self.workbook.add_format({"border": 1})
        not_checkable_format = self.workbook.add_format(
            report_style.xw_status("not_checkable")
        )

        # Titre
        worksheet.merge_range("A1:F1", "SIA Compliance Results", header_format)

        # SIA 380/2 results
        worksheet.write("A3", "SIA 380/2", header_format)
        row = 4
        for category, data in sia3802_results.items():
            if category != "alerts":
                worksheet.write(row, 0, category, header_format)
                worksheet.write(row, 1, data.get("score", 0), cell_format)
                row += 1

        # SIA 4010 results. A client 380/2 report carries no validation block.
        if self.include_sia4010:
            worksheet.write(row + 1, 0, "SIA 4010", header_format)
            worksheet.write(row + 2, 0, "Overall score", header_format)
            worksheet.write(row + 2, 1, sia4010_results.get("score", 0), cell_format)

            row += 3
            worksheet.write(row, 0, "SIA 4010 tests", header_format)
            for test_name, test_data in sia4010_results.get("tests", {}).items():
                row += 1
                worksheet.write(row, 0, test_name, cell_format)
                worksheet.write(row, 1, test_data.get("status", "N/A"), cell_format)
                status = test_data.get("status")
                if status == "PASS":
                    worksheet.write(row, 1, status, pass_format)
                elif status == "WARNING":
                    worksheet.write(row, 1, status, warning_format)
                elif status == "NOT_CHECKABLE":
                    worksheet.write(row, 1, status, not_checkable_format)
                else:
                    worksheet.write(row, 1, status, fail_format)

        # Set readable column widths.
        worksheet.set_column("A:A", 30)
        worksheet.set_column("B:B", 20)

    def _write_reference_project_xlsxwriter(self, sia3802_results: Dict[str, Any]):
        """Write the SIA 380/2 reference-project input specification.

        The decisive SIA 380/2 conclusion compares the project demand with the
        reference-project demand. This sheet is the deterministic build
        instruction for that reference variant: per construction, the project
        value, the normative reference value and its SIA locator.
        """
        worksheet = self.workbook.add_worksheet("REFERENCE PROJECT")

        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        subheader_format = self.workbook.add_format(SHARED_FORMATS["subheader"])
        cell_format = self.workbook.add_format(
            {"border": 1, "text_wrap": True, "valign": "top"}
        )
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink", background="panel", text_wrap=True, valign="top"
            )
        )
        number_format = self.workbook.add_format(
            {"border": 1, "num_format": "0.000", "valign": "top"}
        )
        integer_format = self.workbook.add_format(
            {"border": 1, "num_format": "#,##0", "valign": "top"}
        )
        ok_format = self.workbook.add_format(report_style.xw_status("pass"))
        blocked_format = self.workbook.add_format(report_style.xw_status("fail"))
        warn_format = self.workbook.add_format(report_style.xw_status("warning"))

        specification = sia3802_results.get("reference_project", {}) or {}
        substitutions = specification.get("substitutions", []) or []
        status = str(specification.get("status") or "NOT_CHECKABLE")

        worksheet.merge_range(
            "A1:J1", "SIA 380/2 Reference-Project Input Specification", header_format
        )
        worksheet.merge_range(
            "A2:J3",
            (
                "The decisive SIA 380/2 conclusion compares the project demand with the reference-project "
                "demand. This sheet lists, per construction, the substitution required to build that "
                "reference variant. It is NOT a compliance conclusion: the reference demand still requires "
                "a VE/ApacheSim run and the project/reference comparison still requires reviewer acceptance."
            ),
            note_format,
        )

        status_format = {
            "READY_FOR_REFERENCE_RUN": ok_format,
            "BLOCKED_INCOMPLETE_INPUTS": blocked_format,
        }.get(status, warn_format)
        worksheet.write("A5", "Specification status", subheader_format)
        worksheet.write("B5", status, status_format)
        worksheet.write("A6", "Substitutions listed", subheader_format)
        worksheet.write("B6", len(substitutions), integer_format)
        worksheet.write("A7", "Blockers", subheader_format)
        worksheet.write(
            "B7", len(specification.get("blockers", []) or []), integer_format
        )
        worksheet.write("D5", "Implemented Table 2 families", subheader_format)
        worksheet.write(
            "E5",
            len(specification.get("implemented_input_families", []) or []),
            integer_format,
        )
        worksheet.write("D6", "Missing Table 2 / SIA 380 families", subheader_format)
        worksheet.write(
            "E6",
            len(specification.get("missing_input_families", []) or []),
            integer_format,
        )

        headers = [
            "Parameter",
            "Construction / scope",
            "Element type",
            "Project value",
            "Reference value (limit)",
            "Reference target",
            "Unit",
            "Elements",
            "Status",
            "SIA source",
        ]
        last_col = len(headers) - 1
        start_row = 9
        worksheet.write_row(start_row, 0, headers, header_format)
        row = start_row + 1
        for item in substitutions:
            item_status = str(item.get("status") or "")
            worksheet.write(row, 0, item.get("parameter", ""), cell_format)
            worksheet.write(row, 1, item.get("scope", ""), cell_format)
            worksheet.write(row, 2, item.get("element_type", ""), cell_format)
            self._write_optional_number(
                worksheet, row, 3, item.get("project_value"), number_format, cell_format
            )
            self._write_optional_number(
                worksheet, row, 4, item.get("reference_value"), number_format, cell_format
            )
            # SIA 380/2:2022 7.2.5.2 compares the project value against the limit
            # OR the target; identity/directive rows have no target.
            self._write_optional_number(
                worksheet,
                row,
                5,
                item.get("reference_target_value"),
                number_format,
                cell_format,
            )
            worksheet.write(row, 6, item.get("unit", ""), cell_format)
            worksheet.write(row, 7, item.get("affected_elements", 0), integer_format)
            worksheet.write(
                row,
                8,
                item_status,
                ok_format if item_status == "SUBSTITUTABLE" else blocked_format,
            )
            worksheet.write(row, 9, item.get("source", ""), cell_format)
            row += 1
        if not substitutions:
            worksheet.merge_range(
                row,
                0,
                row,
                last_col,
                "No external construction was available for substitution.",
                cell_format,
            )
            row += 1

        worksheet.autofilter(start_row, 0, max(start_row, row - 1), last_col)
        worksheet.freeze_panes(start_row + 1, 0)

        blockers_start = row + 2
        worksheet.write(
            blockers_start, 0, "Blockers before the reference run", header_format
        )
        blocker_row = blockers_start + 1
        for blocker in specification.get("blockers", []) or []:
            worksheet.merge_range(
                blocker_row, 0, blocker_row, last_col, blocker, cell_format
            )
            blocker_row += 1
        if not (specification.get("blockers") or []):
            worksheet.merge_range(
                blocker_row,
                0,
                blocker_row,
                last_col,
                "No blocker among the implemented substitutions; the missing families below still block a complete reference run.",
                warn_format,
            )
            blocker_row += 1

        family_row = blocker_row + 2
        worksheet.write(
            family_row,
            0,
            "Reference-input families not yet automated",
            header_format,
        )
        family_row += 1
        for family in specification.get("missing_input_families", []) or []:
            worksheet.merge_range(
                family_row,
                0,
                family_row,
                last_col,
                str(family),
                warn_format,
            )
            family_row += 1

        notes_start = family_row + 1
        for note in specification.get("notes", []) or []:
            worksheet.merge_range(
                notes_start, 0, notes_start, last_col, note, note_format
            )
            notes_start += 1

        worksheet.set_column("A:A", 32)
        worksheet.set_column("B:B", 34)
        worksheet.set_column("C:C", 16)
        worksheet.set_column(
            "D:F", 16
        )  # project value, reference limit, reference target
        worksheet.set_column("G:G", 12)  # unit
        worksheet.set_column("H:H", 11)  # elements
        worksheet.set_column("I:I", 24)  # status
        worksheet.set_column("J:J", 46)  # SIA source

    def _write_sia_requirements_xlsxwriter(
        self, sia3802_results: Dict[str, Any], sia4010_results: Dict[str, Any]
    ):
        """Write the auditable SIA requirement matrix used by the checker."""
        worksheet = self.workbook.add_worksheet("SIA REQUIREMENTS")

        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        subheader_format = self.workbook.add_format(SHARED_FORMATS["subheader"])
        cell_format = self.workbook.add_format(
            {"border": 1, "text_wrap": True, "valign": "top"}
        )
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink", background="panel", text_wrap=True, valign="top"
            )
        )
        pass_format = self.workbook.add_format(report_style.xw_status("pass"))
        fail_format = self.workbook.add_format(report_style.xw_status("fail"))
        partial_format = self.workbook.add_format(report_style.xw_status("warning"))
        not_checkable_format = self.workbook.add_format(
            report_style.xw_status("not_checkable")
        )

        worksheet.merge_range(
            "A1:M1",
            (
                "SIA 380/2 + SIA 4010 Requirement Matrix"
                if self.include_sia4010
                else "SIA 380/2 Requirement Matrix"
            ),
            header_format,
        )
        worksheet.merge_range(
            "A2:M2",
            "This matrix lists criteria from the PDF/config sources, their automation status and the next action. "
            "It prevents non-verifiable data from being converted into a false PASS.",
            note_format,
        )

        all_alerts = list(sia3802_results.get("alerts", []) or []) + list(
            sia4010_results.get("alerts", []) or []
        )
        rule_evaluations = sia3802_results.get("rule_evaluations", {}) or {}
        rows = [
            self._build_requirement_matrix_row(requirement, all_alerts, rule_evaluations)
            for requirement in SIA_COMPLIANCE_REQUIREMENT_MATRIX
        ]
        if not self.include_sia4010:
            rows = [
                row for row in rows if "4010" not in str(row.get("standard", "")).upper()
            ]
        status_counts = Counter(row["status"] for row in rows)

        worksheet.write("A4", "KPI", header_format)
        kpis = [
            ("Requirements listed", len(rows)),
            (
                "Automated PASS/CHECK",
                status_counts.get("PASS", 0) + status_counts.get("PARTIAL_CHECK", 0),
            ),
            (
                "Failing or missing",
                status_counts.get("FAIL", 0) + status_counts.get("MISSING", 0),
            ),
            (
                "Not checkable / not implemented",
                status_counts.get("NOT_CHECKABLE", 0)
                + status_counts.get("NOT_IMPLEMENTED", 0),
            ),
        ]
        number_format = self.workbook.add_format({"border": 1, "num_format": "#,##0"})
        for offset, (label, value) in enumerate(kpis, start=5):
            worksheet.write(offset, 0, label, subheader_format)
            worksheet.write(offset, 1, value, number_format)

        headers = [
            "Status",
            "Automation",
            "MVP/MSP",
            "Standard",
            "Domain",
            "Requirement ID",
            "Evaluated objects",
            "Criterion",
            "Limit",
            "Unit",
            "Target",
            "PDF source",
            "Next action / blockers",
        ]
        start_row = 10
        worksheet.write_row(start_row, 0, headers, header_format)

        row = start_row + 1
        for item in rows:
            status_format = self._requirement_status_format(
                item["status"],
                pass_format,
                fail_format,
                partial_format,
                not_checkable_format,
                cell_format,
            )
            worksheet.write(row, 0, item["status"], status_format)
            worksheet.write(row, 1, item["automation"], cell_format)
            worksheet.write(row, 2, item["mvp_status"], cell_format)
            worksheet.write(row, 3, item["standard"], cell_format)
            worksheet.write(row, 4, item["domain"], cell_format)
            worksheet.write(row, 5, item["id"], cell_format)
            worksheet.write(row, 6, item["evaluated_count"], number_format)
            worksheet.write(row, 7, item["criterion"], cell_format)
            worksheet.write(row, 8, item["limit"], cell_format)
            worksheet.write(row, 9, item["unit"], cell_format)
            worksheet.write(row, 10, item["target"], cell_format)
            worksheet.write(row, 11, item["source"], cell_format)
            worksheet.write(row, 12, item["next_action"], cell_format)
            worksheet.set_row(row, 52)
            row += 1

        worksheet.autofilter(start_row, 0, max(start_row, row - 1), len(headers) - 1)
        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:A", 18)
        worksheet.set_column("B:C", 16)
        worksheet.set_column("D:F", 20)
        worksheet.set_column("G:G", 16)
        worksheet.set_column("H:H", 42)
        worksheet.set_column("I:K", 18)
        worksheet.set_column("L:L", 42)
        worksheet.set_column("M:M", 54)

    def _write_sia_data_coverage_xlsxwriter(
        self,
        sia3802_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
        rooms_data: List[Any],
        preflight_checks: List[Dict[str, Any]],
        dynamic_results: Dict[str, Any],
    ):
        """Write the full data coverage matrix for SIA 380/2 and all SIA 4010 classes."""
        worksheet = self.workbook.add_worksheet("SIA DATA COVERAGE")

        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        subheader_format = self.workbook.add_format(SHARED_FORMATS["subheader"])
        cell_format = self.workbook.add_format(
            {"border": 1, "text_wrap": True, "valign": "top"}
        )
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink", background="panel", text_wrap=True, valign="top"
            )
        )
        number_format = self.workbook.add_format({"border": 1, "num_format": "#,##0"})
        available_format = self.workbook.add_format(report_style.xw_status("pass"))
        partial_format = self.workbook.add_format(report_style.xw_status("warning"))
        missing_format = self.workbook.add_format(report_style.xw_status("fail"))
        not_checkable_format = self.workbook.add_format(
            report_style.xw_status("not_checkable")
        )

        rows = self._build_sia_data_coverage_rows(
            sia3802_results,
            sia4010_results,
            rooms_data,
            preflight_checks,
            dynamic_results,
        )
        if not self.include_sia4010:
            rows = [
                row
                for row in rows
                if "4010" not in str(row.get("standard", "")).upper()
                and "4010" not in str(row.get("validation_scope", "")).upper()
            ]
        status_counts = Counter(row["coverage_status"] for row in rows)

        worksheet.merge_range(
            "A1:N1",
            (
                "SIA 380/2 + SIA 4010 Data Coverage Matrix"
                if self.include_sia4010
                else "SIA 380/2 Data Coverage Matrix"
            ),
            header_format,
        )
        worksheet.merge_range(
            "A2:N2",
            (
                "This sheet explains what is currently evidenced by the VE model/API, what requires APS/Vista outputs, "
                "and what must remain external official SIA 4010 evidence before any final compliance claim."
                if self.include_sia4010
                else "This sheet explains what is currently evidenced by the VE model/API and what still requires "
                "APS/Vista outputs before a SIA 380/2 conclusion."
            ),
            note_format,
        )

        worksheet.write("A4", "KPI", header_format)
        kpis = [
            ("Coverage rows", len(rows)),
            ("Available", status_counts.get("AVAILABLE", 0)),
            ("Partial", status_counts.get("PARTIAL", 0)),
            ("Missing", status_counts.get("MISSING", 0)),
            ("Not checkable", status_counts.get("NOT_CHECKABLE", 0)),
        ]
        for offset, (label, value) in enumerate(kpis, start=5):
            worksheet.write(offset, 0, label, subheader_format)
            worksheet.write(offset, 1, value, number_format)

        headers = [
            "Status",
            "Automation",
            "Standard",
            "SIA scope / class",
            "Domain",
            "Coverage ID",
            "Criterion",
            "Expected value / rule",
            "Data needed",
            "Expected source",
            "Current evidence",
            "PDF source",
            "Owner",
            "Next action",
        ]
        start_row = 12
        worksheet.write_row(start_row, 0, headers, header_format)

        row = start_row + 1
        for item in rows:
            status_format = self._coverage_status_format(
                item["coverage_status"],
                available_format,
                partial_format,
                missing_format,
                not_checkable_format,
                cell_format,
            )
            worksheet.write(row, 0, item["coverage_status"], status_format)
            worksheet.write(row, 1, item["automation"], cell_format)
            worksheet.write(row, 2, item["standard"], cell_format)
            worksheet.write(row, 3, item["validation_scope"], cell_format)
            worksheet.write(row, 4, item["domain"], cell_format)
            worksheet.write(row, 5, item["id"], cell_format)
            worksheet.write(row, 6, item["criterion"], cell_format)
            worksheet.write(row, 7, item["expected_value"], cell_format)
            worksheet.write(row, 8, item["data_needed"], cell_format)
            worksheet.write(row, 9, item["expected_source"], cell_format)
            worksheet.write(row, 10, item["current_evidence"], cell_format)
            worksheet.write(row, 11, item["source"], cell_format)
            worksheet.write(row, 12, item["owner"], cell_format)
            worksheet.write(row, 13, item["next_action"], cell_format)
            worksheet.set_row(row, 58)
            row += 1

        worksheet.autofilter(start_row, 0, max(start_row, row - 1), len(headers) - 1)
        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:B", 16)
        worksheet.set_column("C:D", 24)
        worksheet.set_column("E:F", 22)
        worksheet.set_column("G:G", 42)
        worksheet.set_column("H:J", 46)
        worksheet.set_column("K:K", 46)
        worksheet.set_column("L:L", 42)
        worksheet.set_column("M:M", 20)
        worksheet.set_column("N:N", 54)

    def _write_input_request_xlsxwriter(
        self,
        sia3802_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
        rooms_data: List[Any],
        preflight_checks: List[Dict[str, Any]],
        dynamic_results: Dict[str, Any],
    ):
        """Write a client/model-reviewer input checklist generated from missing coverage."""
        worksheet = self.workbook.add_worksheet("INPUT REQUEST")

        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        cell_format = self.workbook.add_format(
            {"border": 1, "text_wrap": True, "valign": "top"}
        )
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink", background="panel", text_wrap=True, valign="top"
            )
        )
        p1_format = self.workbook.add_format(report_style.xw_status("fail"))
        p2_format = self.workbook.add_format(report_style.xw_status("warning"))
        p3_format = self.workbook.add_format(report_style.xw_status("not_evaluated"))

        coverage_rows = self._build_sia_data_coverage_rows(
            sia3802_results,
            sia4010_results,
            rooms_data,
            preflight_checks,
            dynamic_results,
        )
        request_rows = [
            row
            for row in coverage_rows
            if row["coverage_status"] in {"PARTIAL", "MISSING", "NOT_CHECKABLE"}
        ]
        if not self.include_sia4010:
            request_rows = [
                row
                for row in request_rows
                if "4010" not in str(row.get("standard", "")).upper()
                and "4010" not in str(row.get("validation_scope", "")).upper()
            ]

        worksheet.merge_range(
            "A1:J1", "Input Request - Data and Evidence Needed", header_format
        )
        worksheet.merge_range(
            "A2:J2",
            "Use this sheet as the practical handoff list for the model reviewer/client. "
            "It is generated from the coverage matrix and focuses on what is still needed.",
            note_format,
        )

        headers = [
            "Priority",
            "Status",
            "Standard",
            "SIA scope / class",
            "What to provide",
            "Preferred format",
            "Where to put it",
            "Why it matters",
            "Owner",
            "Source",
        ]
        start_row = 4
        worksheet.write_row(start_row, 0, headers, header_format)

        row = start_row + 1
        for item in request_rows:
            priority = self._input_request_priority(item)
            priority_format = (
                p1_format
                if priority == "P1"
                else (p2_format if priority == "P2" else p3_format)
            )
            worksheet.write(row, 0, priority, priority_format)
            worksheet.write(row, 1, item["coverage_status"], cell_format)
            worksheet.write(row, 2, item["standard"], cell_format)
            worksheet.write(row, 3, item["validation_scope"], cell_format)
            worksheet.write(row, 4, item["data_needed"], cell_format)
            worksheet.write(row, 5, item["preferred_format"], cell_format)
            worksheet.write(
                row,
                6,
                self._client_evidence_destination(item["destination"]),
                cell_format,
            )
            worksheet.write(row, 7, item["criterion"], cell_format)
            worksheet.write(row, 8, item["owner"], cell_format)
            worksheet.write(row, 9, item["source"], cell_format)
            worksheet.set_row(row, 58)
            row += 1

        if not request_rows:
            worksheet.write(
                row,
                0,
                "No missing input detected by the current automated coverage matrix.",
                cell_format,
            )

        worksheet.autofilter(start_row, 0, max(start_row, row - 1), len(headers) - 1)
        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:B", 14)
        worksheet.set_column("C:D", 24)
        worksheet.set_column("E:H", 44)
        worksheet.set_column("I:I", 22)
        worksheet.set_column("J:J", 42)

    def _write_sia3802_justifications_xlsxwriter(
        self, justification_results: Dict[str, Any]
    ):
        """Write reviewer-provided SIA 380/2 justification records."""
        worksheet = self.workbook.add_worksheet("SIA3802 JUSTIFICATIONS")
        worksheet.hide_gridlines(2)
        worksheet.freeze_panes(8, 0)
        worksheet.set_column("A:B", 14)
        worksheet.set_column("C:F", 24)
        worksheet.set_column("G:I", 20)
        worksheet.set_column("J:L", 42)
        worksheet.set_column("M:N", 18)

        title_format = self.workbook.add_format(
            report_style.xw_format(
                "on_dark",
                size=16,
                bold=True,
                background="band_deep",
                border=None,
                align="left",
                valign="vcenter",
            )
        )
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                background="panel",
                border=None,
                text_wrap=True,
                valign="top",
            )
        )
        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        cell_format = self.workbook.add_format(
            report_style.xw_format("ink", text_wrap=True, valign="top")
        )
        number_format = self.workbook.add_format(
            report_style.xw_format("ink", num_format="#,##0", valign="top")
        )
        accepted_format = self.workbook.add_format(
            report_style.xw_format(
                "accent",
                bold=True,
                background="table_header",
                align="center",
                text_wrap=True,
            )
        )
        pending_format = self.workbook.add_format(
            report_style.xw_status("warning", valign="top")
        )

        records = (
            justification_results.get("records", [])
            if isinstance(justification_results, dict)
            else []
        )
        accepted_count = (
            int(justification_results.get("accepted_count", 0) or 0)
            if isinstance(justification_results, dict)
            else 0
        )
        record_count = (
            int(justification_results.get("record_count", 0) or 0)
            if isinstance(justification_results, dict)
            else 0
        )
        evidence_dir = (
            justification_results.get("evidence_dir", "sia4010_evidence/")
            if isinstance(justification_results, dict)
            else "sia4010_evidence/"
        )

        worksheet.merge_range(
            "A1:N1",
            "SIA 380/2 Justifications - Reviewed Evidence Exceptions",
            title_format,
        )
        worksheet.merge_range(
            "A2:N4",
            (
                "This sheet shows reviewer-signed justifications that can explain a retained model value without hiding the original check result. "
                "A row is accepted only when it has reviewer, source evidence and an accepted/reviewed/signed status. "
                "Accepted justifications can be displayed as JUSTIFIED_BY_EVIDENCE in the technical audit sheets."
            ),
            note_format,
        )
        worksheet.write("A6", "Records", header_format)
        worksheet.write("B6", record_count, number_format)
        worksheet.write("C6", "Accepted", header_format)
        worksheet.write("D6", accepted_count, number_format)
        worksheet.write("E6", "Evidence folder", header_format)
        worksheet.merge_range(
            "F6:N6", self._client_evidence_destination(evidence_dir), cell_format
        )

        headers = [
            "Status",
            "Accepted",
            "Standard",
            "Domain",
            "Rule",
            "Construction / scope",
            "Reviewer",
            "Review status",
            "Decision status",
            "Source document",
            "Source reference",
            "Justification summary",
            "File",
            "Row",
        ]
        worksheet.write_row(7, 0, headers, header_format)

        if not records:
            worksheet.merge_range(
                "A9:N12",
                (
                    "No SIA 380/2 justification CSV was detected. To add one, fill "
                    "templates/evidence/sia3802_justifications_template.csv and place it in the evidence folder "
                    "with a filename such as SIA3802_justification_ZOER_32_C1.csv."
                ),
                cell_format,
            )
            return

        for row_index, record in enumerate(records, start=8):
            accepted = bool(record.get("accepted"))
            status_text = "JUSTIFIED_BY_EVIDENCE" if accepted else "PENDING_REVIEW"
            status_format = accepted_format if accepted else pending_format
            worksheet.write(row_index, 0, status_text, status_format)
            worksheet.write(row_index, 1, "YES" if accepted else "NO", status_format)
            worksheet.write(row_index, 2, record.get("standard", ""), cell_format)
            worksheet.write(row_index, 3, record.get("domain", ""), cell_format)
            worksheet.write(row_index, 4, record.get("rule", ""), cell_format)
            worksheet.write(
                row_index, 5, record.get("construction_or_scope", ""), cell_format
            )
            worksheet.write(row_index, 6, record.get("reviewer", ""), cell_format)
            worksheet.write(row_index, 7, record.get("review_status", ""), cell_format)
            worksheet.write(row_index, 8, record.get("decision_status", ""), cell_format)
            worksheet.write(row_index, 9, record.get("source_document", ""), cell_format)
            worksheet.write(
                row_index, 10, record.get("source_reference", ""), cell_format
            )
            worksheet.write(
                row_index,
                11,
                record.get("justification_summary", "") or record.get("notes", ""),
                cell_format,
            )
            worksheet.write(row_index, 12, record.get("file", ""), cell_format)
            worksheet.write(row_index, 13, record.get("row", ""), number_format)
            worksheet.set_row(row_index, 50)

        worksheet.autofilter(7, 0, max(7, 7 + len(records)), len(headers) - 1)

    def _write_open_items_backlog_xlsxwriter(
        self,
        alert_groups: List[Dict[str, Any]],
        sia3802_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
        rooms_data: List[Any],
        preflight_checks: List[Dict[str, Any]],
        dynamic_results: Dict[str, Any],
    ):
        """Write a persistent backlog of current gaps and deferred work."""
        worksheet = self.workbook.add_worksheet("OPEN ITEMS BACKLOG")
        worksheet.hide_gridlines(2)
        worksheet.freeze_panes(8, 0)
        worksheet.set_column("A:A", 11)
        worksheet.set_column("B:B", 20)
        worksheet.set_column("C:E", 24)
        worksheet.set_column("F:H", 46)
        worksheet.set_column("I:I", 20)
        worksheet.set_column("J:J", 18)

        title_format = self.workbook.add_format(
            report_style.xw_format(
                "on_dark",
                size=16,
                bold=True,
                background="band_deep",
                border=None,
                align="left",
                valign="vcenter",
            )
        )
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink",
                background="panel",
                border=None,
                text_wrap=True,
                valign="top",
            )
        )
        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        cell_format = self.workbook.add_format(
            report_style.xw_format("ink", text_wrap=True, valign="top")
        )
        number_format = self.workbook.add_format(
            report_style.xw_format("ink", num_format="#,##0")
        )
        p1_format = self.workbook.add_format(report_style.xw_status("fail"))
        p2_format = self.workbook.add_format(report_style.xw_status("warning"))
        p3_format = self.workbook.add_format(report_style.xw_status("not_evaluated"))

        rows = self._build_open_items_backlog_rows(
            alert_groups,
            sia3802_results,
            sia4010_results,
            rooms_data,
            preflight_checks,
            dynamic_results,
        )
        if not self.include_sia4010:
            rows = [
                row
                for row in rows
                if not any(
                    "4010" in str(row.get(field, "")).upper()
                    for field in (
                        "source",
                        "domain",
                        "item",
                        "reason",
                        "next_action",
                        "expected_output",
                    )
                )
            ]
        priority_counts = Counter(row["priority"] for row in rows)

        worksheet.merge_range(
            "A1:J1", "Open Items Backlog - Current Gaps and Deferred Work", title_format
        )
        worksheet.merge_range(
            "A2:J4",
            (
                "This backlog is generated at each VE Run so unfinished items stay visible. "
                "It combines current model alerts, missing data/evidence coverage and manager navigator gaps. "
                "Use it as the running memory of what remains outside the current automated pass."
            ),
            note_format,
        )
        worksheet.write("A6", "Items", header_format)
        worksheet.write("B6", len(rows), number_format)
        worksheet.write("C6", "P1", header_format)
        worksheet.write("D6", priority_counts.get("P1", 0), number_format)
        worksheet.write("E6", "P2", header_format)
        worksheet.write("F6", priority_counts.get("P2", 0), number_format)
        worksheet.write("G6", "P3", header_format)
        worksheet.write("H6", priority_counts.get("P3", 0), number_format)

        headers = [
            "Priority",
            "Source",
            "Domain",
            "Item",
            "Status",
            "Why it remains open",
            "Next action",
            "Evidence / output expected",
            "Owner",
            "Keep until",
        ]
        worksheet.write_row(7, 0, headers, header_format)

        if not rows:
            worksheet.merge_range(
                "A9:J9",
                "No open item detected by the current backlog builder.",
                cell_format,
            )
            return

        for row_index, row_data in enumerate(rows, start=8):
            priority_format = (
                p1_format
                if row_data["priority"] == "P1"
                else p2_format if row_data["priority"] == "P2" else p3_format
            )
            worksheet.write(row_index, 0, row_data["priority"], priority_format)
            worksheet.write(row_index, 1, row_data["source"], cell_format)
            worksheet.write(row_index, 2, row_data["domain"], cell_format)
            worksheet.write(row_index, 3, row_data["item"], cell_format)
            worksheet.write(row_index, 4, row_data["status"], cell_format)
            worksheet.write(row_index, 5, row_data["reason"], cell_format)
            worksheet.write(row_index, 6, row_data["next_action"], cell_format)
            worksheet.write(row_index, 7, row_data["expected_output"], cell_format)
            worksheet.write(row_index, 8, row_data["owner"], cell_format)
            worksheet.write(row_index, 9, row_data["keep_until"], cell_format)
            worksheet.set_row(row_index, 54)

        worksheet.autofilter(7, 0, max(7, 7 + len(rows)), len(headers) - 1)

    def _write_dynamic_results_xlsxwriter(self, dynamic_results: Dict[str, Any]):
        """Write APS/Vista dynamic result indicators when IESVE exposes them."""
        worksheet = self.workbook.add_worksheet("DYNAMIC RESULTS")

        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        subheader_format = self.workbook.add_format(SHARED_FORMATS["subheader"])
        cell_format = self.workbook.add_format(
            {"border": 1, "text_wrap": True, "valign": "top"}
        )
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink", background="panel", text_wrap=True, valign="top"
            )
        )
        number_format = self.workbook.add_format({"border": 1, "num_format": "#,##0.00"})
        integer_format = self.workbook.add_format({"border": 1, "num_format": "#,##0"})
        status_format = self.workbook.add_format(report_style.xw_status("not_checkable"))

        worksheet.merge_range("A1:T1", "APS/Vista Dynamic Results", header_format)
        worksheet.merge_range(
            "A2:T2",
            (
                "These values are readiness indicators extracted from APS/Vista when IESVE ResultsReader is available. "
                "They support SIA 380/2 and SIA 4010 checks but do not replace official SIA 4010 comparison workbooks."
                if self.include_sia4010
                else "These values are extracted from APS/Vista when IESVE ResultsReader is available. "
                "They support the SIA 380/2 compliance assessment of the client model."
            ),
            note_format,
        )

        # A non-dict global_reference_comparison payload must not raise on the
        # .get() reads below; coerce it once so the overview degrades to blank
        # values instead of aborting the workbook.
        global_reference_comparison = (
            dynamic_results.get("global_reference_comparison", {}) or {}
        )
        if not isinstance(global_reference_comparison, dict):
            global_reference_comparison = {}

        overview = [
            ("Status", dynamic_results.get("status", "NOT_CHECKABLE")),
            ("Selected APS file", dynamic_results.get("selected_aps_file") or "None"),
            (
                "Project weather file",
                dynamic_results.get("project_weather_file") or "Not exposed by VE",
            ),
            (
                "Selected APS weather references",
                self._compact_join(
                    dynamic_results.get("selected_aps_weather_references", []) or [],
                    empty="No EPW reference detected in APS",
                    max_chars=500,
                ),
            ),
            (
                "Skipped stale APS files",
                len(dynamic_results.get("skipped_aps_files", []) or []),
            ),
            ("APS files detected", len(dynamic_results.get("aps_files", []) or [])),
            ("Total area used by APS results (m2)", dynamic_results.get("total_area_m2")),
            ("Heating demand (kWh/m2)", dynamic_results.get("heating_kwh_m2")),
            ("Cooling demand (kWh/m2)", dynamic_results.get("cooling_kwh_m2")),
            ("Lighting energy (kWh/m2)", dynamic_results.get("lighting_kwh_m2")),
            ("Fan energy (kWh/m2)", dynamic_results.get("fan_kwh_m2")),
            ("Pump energy (kWh/m2)", dynamic_results.get("pump_kwh_m2")),
            ("Auxiliary energy (kWh/m2)", dynamic_results.get("auxiliary_kwh_m2")),
            ("Total lighting energy (kWh)", dynamic_results.get("total_lighting_kwh")),
            ("Total fan energy (kWh)", dynamic_results.get("total_fan_kwh")),
            ("Total pump energy (kWh)", dynamic_results.get("total_pump_kwh")),
            ("Total auxiliary energy (kWh)", dynamic_results.get("total_auxiliary_kwh")),
            (
                "Total heating coil energy (kWh)",
                dynamic_results.get("total_coil_heating_kwh"),
            ),
            (
                "Total cooling coil energy (kWh)",
                dynamic_results.get("total_coil_cooling_kwh"),
            ),
            ("Peak CO2 (ppm)", dynamic_results.get("peak_co2_ppm")),
            ("Average CO2 (ppm)", dynamic_results.get("average_co2_ppm")),
            (
                "Peak relative humidity (%)",
                dynamic_results.get("peak_relative_humidity_percent"),
            ),
            (
                "Average relative humidity (%)",
                dynamic_results.get("average_relative_humidity_percent"),
            ),
            ("Occupied hours > 26 C", dynamic_results.get("occupied_hours_above_26")),
            ("Occupied hours > 27 C", dynamic_results.get("occupied_hours_above_27")),
            (
                "Maximum occupied hours above SIA 180 upper curve",
                dynamic_results.get("max_occupied_hours_above_sia180_upper"),
            ),
            (
                "Maximum occupied hours below SIA 180 lower curve",
                dynamic_results.get("max_occupied_hours_below_sia180_lower"),
            ),
            (
                "Rooms with a complete annual comfort series",
                dynamic_results.get("annual_comfort_room_count"),
            ),
            (
                "Reviewed building status",
                dynamic_results.get("building_status") or "UNSPECIFIED",
            ),
            (
                "Building-status evidence",
                dynamic_results.get("building_status_source") or "Not provided",
            ),
            (
                "Project metadata status",
                dynamic_results.get("project_metadata_status") or "NOT_PROVIDED",
            ),
            (
                "Reviewed weather basis",
                dynamic_results.get("reviewed_weather_basis") or "Not provided",
            ),
            (
                "Reviewed weather file",
                dynamic_results.get("reviewed_weather_file") or "Not provided",
            ),
            (
                "Reviewed weather match",
                dynamic_results.get("reviewed_weather_match_status") or "NOT_CHECKABLE",
            ),
            (
                "Reviewed location",
                dynamic_results.get("reviewed_location") or "Not provided",
            ),
            (
                "Reviewed altitude (m)",
                dynamic_results.get("reviewed_altitude_m") or "Not provided",
            ),
            (
                "Global project/reference evidence",
                dynamic_results.get("global_reference_comparison_status")
                or "NOT_PROVIDED",
            ),
            (
                "Reviewed global project value",
                global_reference_comparison.get("project_value_numeric"),
            ),
            (
                "Reviewed global reference value",
                global_reference_comparison.get("reference_value_numeric"),
            ),
            (
                "Reviewed global comparison unit",
                global_reference_comparison.get("unit") or "Not provided",
            ),
            ("Design-power result status", dynamic_results.get("design_power_status")),
            ("Notes", dynamic_results.get("notes") or "None"),
        ]
        worksheet.write("A4", "Metric", header_format)
        worksheet.write("B4", "Value", header_format)
        for offset, (label, value) in enumerate(overview, start=5):
            worksheet.write(offset, 0, label, subheader_format)
            if isinstance(value, (int, float)):
                worksheet.write(offset, 1, value, number_format)
            else:
                worksheet.write(
                    offset,
                    1,
                    str(value or ""),
                    status_format if label == "Status" else cell_format,
                )

        overview_start = 5
        overview_end = overview_start + len(overview) - 1
        section_start = overview_end + 2

        # Drop any malformed (None/non-dict) skipped-file entry so one bad row
        # cannot raise and abort the whole workbook; each entry below is read
        # with .get().
        skipped_rows = [
            row
            for row in (dynamic_results.get("skipped_aps_files", []) or [])
            if isinstance(row, dict)
        ]
        skipped_start = section_start
        if skipped_rows:
            worksheet.write(skipped_start, 0, "Skipped APS file", header_format)
            worksheet.write(skipped_start, 1, "Weather references", header_format)
            worksheet.write(skipped_start, 2, "Reason", header_format)
            for row_offset, skipped in enumerate(skipped_rows, start=skipped_start + 1):
                worksheet.write(row_offset, 0, skipped.get("aps_file", ""), cell_format)
                worksheet.write(
                    row_offset,
                    1,
                    self._compact_join(
                        skipped.get("weather_references", []) or [],
                        empty="No EPW reference detected",
                        max_chars=500,
                    ),
                    cell_format,
                )
                worksheet.write(row_offset, 2, skipped.get("reason", ""), cell_format)

        start_row = (
            skipped_start + len(skipped_rows) + 3 if skipped_rows else section_start
        )
        headers = [
            "Room",
            "Room ID",
            "Area m2",
            "Heating kWh",
            "Cooling kWh",
            "Lighting kWh",
            "Fan kWh",
            "Pump kWh",
            "Auxiliary kWh",
            "Heating coil kWh",
            "Cooling coil kWh",
            "Peak heating W",
            "Peak cooling W",
            "Peak CO2 ppm",
            "Average CO2 ppm",
            "Peak RH %",
            "Average RH %",
            "Hours > 26 C",
            "Hours > 27 C",
            "Hours above SIA 180 upper",
            "Hours below SIA 180 lower",
            "Annual comfort period complete",
            "Comfort curve source",
            "Source notes",
        ]
        worksheet.write_row(start_row, 0, headers, header_format)

        row = start_row + 1
        # Match the checker's own guard (SIA3802Checker._check_dynamic_method):
        # keep only dict rows so a None/malformed APS room entry cannot raise
        # here and abort the whole workbook. A dropped row is rendered as the
        # "no readable result" fallback, never a silent success.
        room_rows = [
            item
            for item in (dynamic_results.get("rooms", []) or [])
            if isinstance(item, dict)
        ]
        if room_rows:
            for item in room_rows:
                worksheet.write(row, 0, item.get("room_name", ""), cell_format)
                worksheet.write(row, 1, str(item.get("room_id", "") or ""), cell_format)
                self._write_optional_number(
                    worksheet, row, 2, item.get("area_m2"), number_format, cell_format
                )
                self._write_optional_number(
                    worksheet, row, 3, item.get("heating_kwh"), number_format, cell_format
                )
                self._write_optional_number(
                    worksheet, row, 4, item.get("cooling_kwh"), number_format, cell_format
                )
                self._write_optional_number(
                    worksheet,
                    row,
                    5,
                    item.get("lighting_kwh"),
                    number_format,
                    cell_format,
                )
                self._write_optional_number(
                    worksheet, row, 6, item.get("fan_kwh"), number_format, cell_format
                )
                self._write_optional_number(
                    worksheet, row, 7, item.get("pump_kwh"), number_format, cell_format
                )
                self._write_optional_number(
                    worksheet,
                    row,
                    8,
                    item.get("auxiliary_kwh"),
                    number_format,
                    cell_format,
                )
                self._write_optional_number(
                    worksheet,
                    row,
                    9,
                    item.get("coil_heating_kwh"),
                    number_format,
                    cell_format,
                )
                self._write_optional_number(
                    worksheet,
                    row,
                    10,
                    item.get("coil_cooling_kwh"),
                    number_format,
                    cell_format,
                )
                self._write_optional_number(
                    worksheet,
                    row,
                    11,
                    item.get("peak_heating_w"),
                    integer_format,
                    cell_format,
                )
                self._write_optional_number(
                    worksheet,
                    row,
                    12,
                    item.get("peak_cooling_w"),
                    integer_format,
                    cell_format,
                )
                self._write_optional_number(
                    worksheet,
                    row,
                    13,
                    item.get("peak_co2_ppm"),
                    integer_format,
                    cell_format,
                )
                self._write_optional_number(
                    worksheet,
                    row,
                    14,
                    item.get("average_co2_ppm"),
                    number_format,
                    cell_format,
                )
                self._write_optional_number(
                    worksheet,
                    row,
                    15,
                    item.get("peak_relative_humidity_percent"),
                    number_format,
                    cell_format,
                )
                self._write_optional_number(
                    worksheet,
                    row,
                    16,
                    item.get("average_relative_humidity_percent"),
                    number_format,
                    cell_format,
                )
                self._write_optional_number(
                    worksheet,
                    row,
                    17,
                    item.get("occupied_hours_above_26"),
                    number_format,
                    cell_format,
                )
                self._write_optional_number(
                    worksheet,
                    row,
                    18,
                    item.get("occupied_hours_above_27"),
                    number_format,
                    cell_format,
                )
                self._write_optional_number(
                    worksheet,
                    row,
                    19,
                    item.get("occupied_hours_above_sia180_upper"),
                    number_format,
                    cell_format,
                )
                self._write_optional_number(
                    worksheet,
                    row,
                    20,
                    item.get("occupied_hours_below_sia180_lower"),
                    number_format,
                    cell_format,
                )
                worksheet.write(
                    row,
                    21,
                    "YES" if item.get("annual_comfort_period_complete") else "NO",
                    cell_format,
                )
                worksheet.write(
                    row, 22, item.get("comfort_curve_source", ""), cell_format
                )
                worksheet.write(row, 23, item.get("source_notes", ""), cell_format)
                row += 1
        else:
            worksheet.write(
                row,
                0,
                "No room-level dynamic result was readable in this run.",
                cell_format,
            )

        worksheet.autofilter(start_row, 0, max(start_row, row - 1), len(headers) - 1)
        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:B", 24)
        worksheet.set_column("C:V", 16)
        worksheet.set_column("W:X", 72)

    def _write_sia4010_readiness_xlsxwriter(
        self, sia4010_results: Dict[str, Any], rooms_data: List[Any]
    ):
        """Write a SIA 4010 readiness matrix backed by the PDF traceability."""
        worksheet = self.workbook.add_worksheet("SIA4010 READINESS")

        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        subheader_format = self.workbook.add_format(SHARED_FORMATS["subheader"])
        cell_format = self.workbook.add_format(
            {"border": 1, "text_wrap": True, "valign": "top"}
        )
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink", background="panel", text_wrap=True, valign="top"
            )
        )
        percent_format = self.workbook.add_format(
            {"border": 1, "num_format": "0.0%", "valign": "top"}
        )
        number_format = self.workbook.add_format(
            {"border": 1, "num_format": "#,##0", "valign": "top"}
        )
        ready_format = self.workbook.add_format(report_style.xw_status("pass"))
        partial_format = self.workbook.add_format(report_style.xw_status("warning"))
        missing_format = self.workbook.add_format(report_style.xw_status("fail"))
        not_checkable_format = self.workbook.add_format(
            report_style.xw_status("not_checkable")
        )

        rows = self._build_sia4010_readiness_rows(sia4010_results, rooms_data)
        avg_readiness = (
            sum(row["readiness_ratio"] for row in rows) / len(rows) if rows else 0.0
        )
        not_checkable_count = sum(
            1 for row in rows if row["official_status"] == "NOT_CHECKABLE"
        )
        validation_class = sia4010_results.get("validation_class") or "Not selected"
        evidence = sia4010_results.get("evidence", {}) or {}
        evidence_present_count = sum(
            1
            for item in SIA4010_REQUIRED_EVIDENCE
            if self._has_sia4010_evidence(evidence, item)
        )
        official_test_summary = (
            evidence.get("official_test_result_summary", {})
            if isinstance(evidence, dict)
            else {}
        )

        worksheet.merge_range(
            "A1:K1", "SIA 4010 Readiness - Validation Evidence Matrix", header_format
        )
        worksheet.merge_range(
            "A2:K2",
            "This sheet separates VE model readiness from official SIA 4010 validation. "
            "Without the official SIA evidence files, tests remain NOT_CHECKABLE.",
            note_format,
        )

        worksheet.write("A4", "KPI", header_format)
        kpis = [
            ("Validation class selected", validation_class),
            ("Tests listed", len(rows)),
            ("Average VE data readiness", avg_readiness),
            ("NOT_CHECKABLE tests", not_checkable_count),
            ("Official evidence items present", evidence_present_count),
            ("Official evidence items required", len(SIA4010_REQUIRED_EVIDENCE)),
            (
                "Official test-result files",
                official_test_summary.get("result_file_count", 0),
            ),
            (
                "Official test-result rows",
                official_test_summary.get("result_row_count", 0),
            ),
            (
                "Tests with recorded PASS rows",
                len(official_test_summary.get("recorded_pass_tests", []) or []),
            ),
            (
                "Official failed tests",
                len(official_test_summary.get("failed_tests", []) or []),
            ),
        ]
        for offset, (label, value) in enumerate(kpis, start=5):
            worksheet.write(offset, 0, label, subheader_format)
            if isinstance(value, float):
                worksheet.write(offset, 1, value, percent_format)
            elif isinstance(value, int):
                worksheet.write(offset, 1, value, number_format)
            else:
                worksheet.write(offset, 1, value, cell_format)

        worksheet.write("D4", "Validation classes from SIA 4010 table 63", header_format)
        worksheet.write_row("D5", ["Class", "Required tests"], subheader_format)
        class_row = 6
        for class_name, tests in SIA4010_VALIDATION_CLASSES.items():
            worksheet.write(class_row, 3, class_name, cell_format)
            worksheet.write(class_row, 4, tests, cell_format)
            class_row += 1

        start_row = max(class_row + 2, 16)
        headers = [
            "Test",
            "Classes concerned",
            "Domain",
            "VE data readiness",
            "VE data status",
            "Official status",
            "Data currently evidenced",
            "Missing / blockers",
            "Official evidence required",
            "PDF source",
            "Next action",
        ]
        worksheet.write_row(start_row, 0, headers, header_format)

        row = start_row + 1
        for item in rows:
            worksheet.write(row, 0, item["test"], cell_format)
            worksheet.write(row, 1, item["classes"], cell_format)
            worksheet.write(row, 2, item["domain"], cell_format)
            worksheet.write(row, 3, item["readiness_ratio"], percent_format)
            worksheet.write(
                row,
                4,
                item["ve_status"],
                self._sia4010_status_format(
                    item["ve_status"],
                    ready_format,
                    partial_format,
                    missing_format,
                    not_checkable_format,
                    cell_format,
                ),
            )
            worksheet.write(
                row,
                5,
                item["official_status"],
                self._sia4010_status_format(
                    item["official_status"],
                    ready_format,
                    partial_format,
                    missing_format,
                    not_checkable_format,
                    cell_format,
                ),
            )
            worksheet.write(row, 6, item["present"], cell_format)
            worksheet.write(row, 7, item["missing"], cell_format)
            worksheet.write(row, 8, item["official_evidence"], cell_format)
            worksheet.write(row, 9, item["source"], cell_format)
            worksheet.write(row, 10, item["next_action"], cell_format)
            worksheet.set_row(row, 62)
            row += 1

        worksheet.autofilter(start_row, 0, max(start_row, row - 1), len(headers) - 1)

        evidence_start = row + 2
        worksheet.write(
            evidence_start, 0, "Official SIA 4010 evidence checklist", header_format
        )
        worksheet.write_row(
            evidence_start + 1,
            0,
            [
                "Evidence item",
                "File status",
                "Manifest status",
                "Required filename prefix",
                "Example filename",
                "Source authority",
                "Tests covered",
                "Reviewer / review status",
                "Comment",
            ],
            subheader_format,
        )
        evidence_row = evidence_start + 2
        for item in SIA4010_REQUIRED_EVIDENCE:
            status = (
                "PRESENT" if self._has_sia4010_evidence(evidence, item) else "MISSING"
            )
            evidence_key = self._evidence_key_for_required_item(item)
            requirement = SIA4010_EVIDENCE_REQUIREMENTS.get(evidence_key, {})
            manifest_rows = (
                evidence.get(evidence_key, {}).get("manifest_rows", [])
                if isinstance(evidence, dict)
                else []
            )
            manifest_row = manifest_rows[0] if manifest_rows else {}
            manifest_status = (
                manifest_row.get("row_status", "NOT_DOCUMENTED")
                if manifest_row
                else "NOT_DOCUMENTED"
            )
            manifest_note = manifest_row.get(
                "row_status_reason", "No manifest row detected for this evidence family."
            )
            reviewer_status = " / ".join(
                value
                for value in [
                    manifest_row.get("reviewer", ""),
                    manifest_row.get("review_status", ""),
                ]
                if value
            )
            worksheet.write(evidence_row, 0, item, cell_format)
            worksheet.write(
                evidence_row,
                1,
                status,
                ready_format if status == "PRESENT" else missing_format,
            )
            worksheet.write(
                evidence_row,
                2,
                manifest_status,
                ready_format if manifest_status == "DOCUMENTED" else missing_format,
            )
            worksheet.write(
                evidence_row,
                3,
                self._compact_join(
                    requirement.get("required_prefixes", []) or [],
                    empty="See evidence template.",
                ),
                cell_format,
            )
            worksheet.write(
                evidence_row, 4, requirement.get("example_filename", ""), cell_format
            )
            worksheet.write(
                evidence_row, 5, manifest_row.get("source_authority", ""), cell_format
            )
            worksheet.write(
                evidence_row, 6, manifest_row.get("tests_covered", ""), cell_format
            )
            worksheet.write(evidence_row, 7, reviewer_status, cell_format)
            worksheet.write(
                evidence_row,
                8,
                (
                    manifest_note
                    if manifest_status != "DOCUMENTED"
                    else "Evidence file is referenced by a documented manifest row."
                ),
                cell_format,
            )
            evidence_row += 1

        files_start = evidence_row + 2
        worksheet.write(files_start, 0, "Detected evidence files", header_format)
        worksheet.write_row(
            files_start + 1,
            0,
            [
                "File",
                "Relative path",
                "Size (KB)",
                "Detected family",
                "Classification note",
            ],
            subheader_format,
        )
        files_row = files_start + 2
        evidence_files = evidence.get("files", []) if isinstance(evidence, dict) else []
        ignored_file_reasons = {
            str(item.get("path") or item.get("name") or ""): item.get("reason", "")
            for item in (
                evidence.get("ignored_files", []) if isinstance(evidence, dict) else []
            )
            if isinstance(item, dict)
        }
        if evidence_files:
            for file_data in evidence_files:
                detected_families = self._sia4010_detected_families_for_file(
                    evidence, file_data
                )
                worksheet.write(files_row, 0, file_data.get("name", ""), cell_format)
                worksheet.write(files_row, 1, file_data.get("path", ""), cell_format)
                size_bytes = file_data.get("size_bytes")
                size_kb = (
                    float(size_bytes) / 1024.0
                    if isinstance(size_bytes, (int, float))
                    else None
                )
                self._write_optional_number(
                    worksheet, files_row, 2, size_kb, number_format, cell_format
                )
                worksheet.write(files_row, 3, detected_families, cell_format)
                reason_key = str(file_data.get("path") or file_data.get("name") or "")
                worksheet.write(
                    files_row,
                    4,
                    ignored_file_reasons.get(
                        reason_key,
                        "Counted only if listed under a detected official evidence family.",
                    ),
                    cell_format,
                )
                files_row += 1
        else:
            worksheet.write(
                files_row, 0, "No file detected in sia4010_evidence.", cell_format
            )
            worksheet.write(
                files_row,
                1,
                (
                    evidence.get("evidence_dir", "sia4010_evidence")
                    if isinstance(evidence, dict)
                    else "sia4010_evidence"
                ),
                cell_format,
            )
            worksheet.write(files_row, 2, "", cell_format)
            worksheet.write(files_row, 3, "NOT_CHECKABLE", not_checkable_format)
            worksheet.write(
                files_row,
                4,
                "Add official files using the documented prefixes shown above.",
                cell_format,
            )
            files_row += 1

        official_start = files_row + 2
        worksheet.write(
            official_start, 0, "Official SIA 4010 test results", header_format
        )
        missing_result_columns = (
            official_test_summary.get("missing_columns", {})
            if isinstance(official_test_summary, dict)
            else {}
        )
        if missing_result_columns:
            missing_column_note = "; ".join(
                f"{path}: {', '.join(columns)}"
                for path, columns in missing_result_columns.items()
            )
            worksheet.write(
                official_start,
                1,
                f"Missing CSV columns: {missing_column_note}",
                missing_format,
            )
        else:
            worksheet.write(
                official_start,
                1,
                "CSV column structure: OK when a result file is provided.",
                note_format,
            )
        worksheet.write_row(
            official_start + 2,
            0,
            [
                "Raw test ID",
                "Normalized test",
                "Input status",
                "Parsed row status",
                "Source CSV",
                "CSV row",
                "Reference file",
                "Reference found",
                "Candidate file",
                "Candidate found",
                "Deviation",
                "Tolerance",
                "Reviewer",
                "Review date",
                "Source authority",
                "Source reference",
                "Notes",
            ],
            subheader_format,
        )
        official_row = official_start + 3
        official_result_rows = (
            evidence.get("official_test_result_rows", [])
            if isinstance(evidence, dict)
            else []
        )
        if official_result_rows:
            for result_row in official_result_rows:
                parsed_status = result_row.get("row_status", "")
                if parsed_status == "OFFICIAL_PASS":
                    status_format = ready_format
                elif parsed_status == "OFFICIAL_FAIL":
                    status_format = missing_format
                elif parsed_status in {"PASS_METADATA_INCOMPLETE", "NOT_REVIEWED"}:
                    status_format = partial_format
                else:
                    status_format = not_checkable_format

                reference_found = (
                    "YES" if result_row.get("reference_file_exists") else "NO"
                )
                candidate_found = (
                    "YES" if result_row.get("candidate_file_exists") else "NO"
                )
                worksheet.write(
                    official_row, 0, result_row.get("test_id", ""), cell_format
                )
                worksheet.write(
                    official_row, 1, result_row.get("test_key", ""), cell_format
                )
                worksheet.write(
                    official_row, 2, result_row.get("status", ""), cell_format
                )
                worksheet.write(official_row, 3, parsed_status, status_format)
                worksheet.write(
                    official_row,
                    4,
                    result_row.get("result_path") or result_row.get("result_file", ""),
                    cell_format,
                )
                self._write_optional_number(
                    worksheet,
                    official_row,
                    5,
                    result_row.get("row_index"),
                    number_format,
                    cell_format,
                )
                worksheet.write(
                    official_row, 6, result_row.get("reference_file", ""), cell_format
                )
                worksheet.write(
                    official_row,
                    7,
                    reference_found,
                    ready_format if reference_found == "YES" else missing_format,
                )
                worksheet.write(
                    official_row, 8, result_row.get("candidate_file", ""), cell_format
                )
                worksheet.write(
                    official_row,
                    9,
                    candidate_found,
                    ready_format if candidate_found == "YES" else missing_format,
                )
                worksheet.write(
                    official_row, 10, result_row.get("deviation", ""), cell_format
                )
                worksheet.write(
                    official_row, 11, result_row.get("tolerance", ""), cell_format
                )
                worksheet.write(
                    official_row, 12, result_row.get("reviewer", ""), cell_format
                )
                worksheet.write(
                    official_row, 13, result_row.get("review_date", ""), cell_format
                )
                worksheet.write(
                    official_row, 14, result_row.get("source_authority", ""), cell_format
                )
                worksheet.write(
                    official_row, 15, result_row.get("source_reference", ""), cell_format
                )
                worksheet.write(
                    official_row, 16, result_row.get("row_status_reason", ""), cell_format
                )
                worksheet.set_row(official_row, 54)
                official_row += 1
        else:
            worksheet.write(
                official_row, 0, "No official test-result CSV detected.", cell_format
            )
            worksheet.write(official_row, 1, "NOT_CHECKABLE", not_checkable_format)
            worksheet.write(
                official_row,
                2,
                "Add SIA4010_official_test_results_<project>.csv to sia4010_evidence/.",
                cell_format,
            )
            for column in range(3, 16):
                worksheet.write(official_row, column, "", cell_format)
            worksheet.write(
                official_row,
                16,
                "Tests can be READY_FOR_OFFICIAL_REVIEW, but not VALIDATED, until explicit official PASS rows are provided.",
                cell_format,
            )
            official_row += 1

        system_start = official_row + 2
        worksheet.write(
            system_start, 0, "System data families required by SIA 4010", header_format
        )
        worksheet.write_row(
            system_start + 1,
            0,
            [
                "System family",
                "Required data",
                "PDF / table source",
                "Current extraction status",
            ],
            subheader_format,
        )
        system_row = system_start + 2
        for family, data in SIA4010_SYSTEM_REQUIREMENT_SOURCES.items():
            worksheet.write(system_row, 0, family, cell_format)
            worksheet.write(
                system_row, 1, "; ".join(data.get("requires", [])), cell_format
            )
            worksheet.write(
                system_row,
                2,
                f"{data.get('pages', '')}; {data.get('table_range', '')}",
                cell_format,
            )
            worksheet.write(
                system_row,
                3,
                self._sia4010_system_status(family, rooms_data, sia4010_results),
                cell_format,
            )
            worksheet.set_row(system_row, 48)
            system_row += 1

        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:A", 24)
        worksheet.set_column("B:B", 18)
        worksheet.set_column("C:C", 32)
        worksheet.set_column("D:D", 30)
        worksheet.set_column("E:E", 40)
        worksheet.set_column("F:F", 26)
        worksheet.set_column("G:H", 34)
        worksheet.set_column("I:I", 46)
        worksheet.set_column("J:J", 34)
        worksheet.set_column("K:K", 52)
        worksheet.set_column("L:Q", 28)

    def _write_sia4010_prevalidation_xlsxwriter(self, sia4010_results: Dict[str, Any]):
        """Write PDF-based SIA 4010 prevalidation tests and classes."""
        worksheet = self.workbook.add_worksheet("SIA4010 PREVALIDATION")

        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        subheader_format = self.workbook.add_format(SHARED_FORMATS["subheader"])
        cell_format = self.workbook.add_format(
            {"border": 1, "text_wrap": True, "valign": "top"}
        )
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink", background="panel", text_wrap=True, valign="top"
            )
        )
        number_format = self.workbook.add_format(
            {"border": 1, "num_format": "#,##0.0", "valign": "top"}
        )
        pass_format = self.workbook.add_format(
            report_style.xw_status("pass", valign="top")
        )
        partial_format = self.workbook.add_format(
            report_style.xw_status("warning", valign="top")
        )
        fail_format = self.workbook.add_format(
            report_style.xw_status("fail", valign="top")
        )
        missing_format = self.workbook.add_format(
            report_style.xw_status("not_checkable", valign="top")
        )

        prevalidation = sia4010_results.get("prevalidation", {}) or {}
        summary = prevalidation.get("summary", {}) or {}
        tests = prevalidation.get("tests", {}) or {}
        classes = prevalidation.get("classes", {}) or {}

        worksheet.merge_range(
            "A1:L1", "SIA 4010 PDF-Based Prevalidation - Tests 1 to 7", header_format
        )
        worksheet.merge_range(
            "A2:L3",
            (
                "This sheet uses the published SIA 380/2:2022 and SIA 4010:2023 PDFs to perform the closest possible "
                "prevalidation from the active VE model. It is not official SIA 4010 software validation and it does not "
                "replace the paid SIA execution package or sub-commission review."
            ),
            note_format,
        )

        worksheet.write("A5", "KPI", header_format)
        kpis = [
            ("Overall PDF precheck status", summary.get("overall_status", "NOT_RUN")),
            ("Tests evaluated", summary.get("test_count", len(tests))),
            ("Classes evaluated", summary.get("class_count", len(classes))),
            ("Average test score", float(summary.get("average_test_score", 0.0) or 0.0)),
            (
                "Average class score",
                float(summary.get("average_class_score", 0.0) or 0.0),
            ),
            (
                "Official validation required",
                "YES" if summary.get("official_validation_required", True) else "NO",
            ),
        ]
        for row_offset, (label, value) in enumerate(kpis, start=6):
            worksheet.write(row_offset, 0, label, subheader_format)
            if isinstance(value, float):
                worksheet.write(row_offset, 1, value, number_format)
            else:
                worksheet.write(row_offset, 1, value, cell_format)

        worksheet.write("D5", "Status counts", header_format)
        worksheet.write_row("D6", ["Scope", "Status", "Count"], subheader_format)
        status_row = 7
        for scope, counts in [
            ("Tests", summary.get("test_status_counts", {}) or {}),
            ("Classes", summary.get("class_status_counts", {}) or {}),
        ]:
            for status, count in sorted(counts.items()):
                worksheet.write(status_row, 3, scope, cell_format)
                worksheet.write(
                    status_row,
                    4,
                    status,
                    self._sia4010_prevalidation_status_format(
                        status,
                        pass_format,
                        partial_format,
                        fail_format,
                        missing_format,
                        cell_format,
                    ),
                )
                worksheet.write(status_row, 5, count, cell_format)
                status_row += 1

        start_row = max(status_row + 2, 16)
        headers = [
            "Test",
            "PDF precheck status",
            "Score",
            "PDF scope",
            "SIA 380/2 link",
            "Passed checks",
            "Missing data",
            "Blocking risks",
            "Close-to-official scope",
            "Official gap",
            "Source",
            "Next action",
        ]
        worksheet.write_row(start_row, 0, headers, header_format)

        row = start_row + 1
        for test_name in sorted(tests):
            item = tests[test_name]
            status = item.get("status", "")
            worksheet.write(row, 0, test_name, cell_format)
            worksheet.write(
                row,
                1,
                status,
                self._sia4010_prevalidation_status_format(
                    status,
                    pass_format,
                    partial_format,
                    fail_format,
                    missing_format,
                    cell_format,
                ),
            )
            worksheet.write(row, 2, float(item.get("score", 0.0) or 0.0), number_format)
            worksheet.write(row, 3, item.get("pdf_scope", ""), cell_format)
            worksheet.write(row, 4, item.get("sia3802_link", ""), cell_format)
            worksheet.write(
                row,
                5,
                self._compact_join(item.get("passed_checks", []) or [], max_chars=340),
                cell_format,
            )
            worksheet.write(
                row,
                6,
                self._compact_join(
                    item.get("missing_checks", []) or [],
                    empty="No missing data recorded.",
                    max_chars=340,
                ),
                cell_format,
            )
            worksheet.write(
                row,
                7,
                self._compact_join(
                    item.get("blocking_risks", []) or [],
                    empty="No blocking SIA 380/2 risk detected.",
                    max_chars=340,
                ),
                cell_format,
            )
            worksheet.write(row, 8, item.get("close_to_official_scope", ""), cell_format)
            worksheet.write(row, 9, item.get("official_gap", ""), cell_format)
            worksheet.write(row, 10, item.get("source", ""), cell_format)
            worksheet.write(row, 11, item.get("next_action", ""), cell_format)
            worksheet.set_row(row, 84)
            row += 1

        class_start = row + 2
        worksheet.write(class_start, 0, "PDF-Based Class Prevalidation", header_format)
        class_headers = [
            "Class",
            "Status",
            "Score",
            "Required tests",
            "Application",
            "Solar protection",
            "Missing / failed tests",
            "Official validation required",
            "Source",
        ]
        worksheet.write_row(class_start + 1, 0, class_headers, subheader_format)
        class_row = class_start + 2
        for class_name in sorted(classes):
            item = classes[class_name]
            status = item.get("status", "")
            worksheet.write(class_row, 0, class_name, cell_format)
            worksheet.write(
                class_row,
                1,
                status,
                self._sia4010_prevalidation_status_format(
                    status,
                    pass_format,
                    partial_format,
                    fail_format,
                    missing_format,
                    cell_format,
                ),
            )
            worksheet.write(
                class_row, 2, float(item.get("score", 0.0) or 0.0), number_format
            )
            worksheet.write(
                class_row, 3, item.get("required_tests_label", ""), cell_format
            )
            worksheet.write(class_row, 4, item.get("application", ""), cell_format)
            worksheet.write(class_row, 5, item.get("solar_protection", ""), cell_format)
            worksheet.write(
                class_row,
                6,
                self._compact_join(
                    item.get("missing_or_failed_tests", []) or [],
                    empty="No missing/failed PDF precheck.",
                    max_chars=260,
                ),
                cell_format,
            )
            worksheet.write(
                class_row,
                7,
                "YES" if item.get("official_validation_required", True) else "NO",
                cell_format,
            )
            worksheet.write(class_row, 8, item.get("source", ""), cell_format)
            worksheet.set_row(class_row, 60)
            class_row += 1

        worksheet.autofilter(start_row, 0, max(start_row, row - 1), len(headers) - 1)
        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:A", 12)
        worksheet.set_column("B:B", 24)
        worksheet.set_column("C:C", 10)
        worksheet.set_column("D:E", 42)
        worksheet.set_column("F:H", 42)
        worksheet.set_column("I:J", 46)
        worksheet.set_column("K:L", 46)

    def _write_sia4010_class_matrix_xlsxwriter(
        self, sia4010_results: Dict[str, Any], rooms_data: List[Any]
    ):
        """Write the SIA 4010 validation-class matrix for classes 1A to 5."""
        worksheet = self.workbook.add_worksheet("SIA4010 CLASS MATRIX")

        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        subheader_format = self.workbook.add_format(SHARED_FORMATS["subheader"])
        cell_format = self.workbook.add_format(
            {"border": 1, "text_wrap": True, "valign": "top"}
        )
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink", background="panel", text_wrap=True, valign="top"
            )
        )
        percent_format = self.workbook.add_format(
            {"border": 1, "num_format": "0.0%", "valign": "top"}
        )
        integer_format = self.workbook.add_format(
            {"border": 1, "num_format": "#,##0", "valign": "top"}
        )
        ready_format = self.workbook.add_format(
            report_style.xw_status("pass", valign="top")
        )
        partial_format = self.workbook.add_format(
            report_style.xw_status("warning", valign="top")
        )
        missing_format = self.workbook.add_format(
            report_style.xw_status("fail", valign="top")
        )
        not_checkable_format = self.workbook.add_format(
            report_style.xw_status("not_checkable", valign="top")
        )

        rows = self._build_sia4010_class_matrix_rows(sia4010_results, rooms_data)
        evidence = sia4010_results.get("evidence", {}) or {}
        evidence_summary = (
            evidence.get("summary", {}) if isinstance(evidence, dict) else {}
        )
        selected_class = str(
            sia4010_results.get("validation_class")
            or evidence_summary.get("validation_class")
            or "Not selected"
        )
        class_manifest_summary = (
            evidence.get("class_manifest_summary", {})
            if isinstance(evidence, dict)
            else {}
        )
        status_counts = Counter(row["class_status"] for row in rows)
        avg_ve_readiness = (
            sum(row["ve_readiness_ratio"] for row in rows) / len(rows) if rows else 0.0
        )

        worksheet.merge_range(
            "A1:L1", "SIA 4010 Validation-Class Matrix - Classes 1A to 5", header_format
        )
        worksheet.merge_range(
            "A2:L3",
            (
                "This matrix maps every SIA 4010 validation class to its required tests and official evidence state. "
                "It supports all classes 1A, 1B, 2A, 2B, 3, 4A, 4B and 5, but it does not claim certification "
                "unless official SIA evidence and reviewer confirmation are available."
            ),
            note_format,
        )

        # Which class does THIS model's analysis actually rely on? Derived from
        # the extracted model features; an undetermined feature is kept in the
        # conservative class rather than assumed absent.
        class_scope = sia4010_results.get("required_class_scope", {}) or {}

        worksheet.write("A5", "KPI", header_format)
        kpis = [
            (
                "Class required by this model",
                class_scope.get("required_class") or "Not derived",
            ),
            (
                "Conservative class (incl. undetermined)",
                class_scope.get("conservative_class") or "Not derived",
            ),
            ("Selected / detected class", selected_class),
            ("Classes covered by matrix", len(rows)),
            ("Average VE data readiness", avg_ve_readiness),
            ("Official evidence status", evidence_summary.get("status", "NOT_CHECKABLE")),
            ("Evidence families present", evidence_summary.get("present_count", 0)),
            (
                "Evidence families required",
                evidence_summary.get("required_count", len(SIA4010_REQUIRED_EVIDENCE)),
            ),
            (
                "Class selection source",
                evidence_summary.get("validation_class_source", "not_selected"),
            ),
            (
                "Class manifest status",
                class_manifest_summary.get("selection_status", "NOT_SELECTED"),
            ),
        ]
        for offset, (label, value) in enumerate(kpis, start=6):
            worksheet.write(offset, 0, label, subheader_format)
            if isinstance(value, float):
                worksheet.write(offset, 1, value, percent_format)
            elif isinstance(value, int):
                worksheet.write(offset, 1, value, integer_format)
            else:
                worksheet.write(offset, 1, value, cell_format)

        worksheet.write("D5", "Class status summary", header_format)
        worksheet.write_row("D6", ["Status", "Class count"], subheader_format)
        summary_row = 7
        for status, count in sorted(status_counts.items()):
            worksheet.write(
                summary_row,
                3,
                status,
                self._sia4010_status_format(
                    status,
                    ready_format,
                    partial_format,
                    missing_format,
                    not_checkable_format,
                    cell_format,
                ),
            )
            worksheet.write(summary_row, 4, count, integer_format)
            summary_row += 1

        # Side panel: why this model requires that class (feature -> official test).
        worksheet.write("G5", "Why this model requires that class", header_format)
        worksheet.write_row(
            "G6",
            ["Model feature", "Detected", "Relies on official test", "Evidence"],
            subheader_format,
        )
        scope_row = 6
        for finding in class_scope.get("findings", []) or []:
            state = str(finding.get("state", ""))
            state_format = {
                "PRESENT": ready_format,
                "ABSENT": cell_format,
                "UNDETERMINED": partial_format,
            }.get(state, cell_format)
            worksheet.write(scope_row, 6, finding.get("label", ""), cell_format)
            worksheet.write(scope_row, 7, state, state_format)
            worksheet.write(
                scope_row,
                8,
                "{} - {}".format(
                    finding.get("test_family", ""), finding.get("test_scope", "")
                ),
                cell_format,
            )
            worksheet.write(scope_row, 9, finding.get("evidence", ""), cell_format)
            scope_row += 1
        for note in class_scope.get("notes", []) or []:
            worksheet.merge_range(scope_row, 6, scope_row, 9, note, note_format)
            scope_row += 1
        summary_row = max(summary_row, scope_row)

        start_row = max(summary_row + 2, 16)
        headers = [
            "Class",
            "Selected",
            "Class status",
            "Application",
            "Solar protection condition",
            "Required tests",
            "VE data readiness",
            "Official test/evidence state",
            "Missing official evidence",
            "Status reason",
            "Next action",
            "Source",
            "Automated band cross-check",
        ]
        worksheet.write_row(start_row, 0, headers, header_format)

        row = start_row + 1
        for item in rows:
            worksheet.write(row, 0, item["class"], cell_format)
            worksheet.write(
                row,
                1,
                "YES" if item["selected"] else "NO",
                ready_format if item["selected"] else cell_format,
            )
            worksheet.write(
                row,
                2,
                item["class_status"],
                self._sia4010_status_format(
                    item["class_status"],
                    ready_format,
                    partial_format,
                    missing_format,
                    not_checkable_format,
                    cell_format,
                ),
            )
            worksheet.write(row, 3, item["application"], cell_format)
            worksheet.write(row, 4, item["solar_protection"], cell_format)
            worksheet.write(row, 5, item["required_tests_label"], cell_format)
            worksheet.write(row, 6, item["ve_readiness_ratio"], percent_format)
            worksheet.write(row, 7, item["official_test_state"], cell_format)
            worksheet.write(row, 8, item["missing_official_evidence"], cell_format)
            worksheet.write(row, 9, item["status_reason"], cell_format)
            worksheet.write(row, 10, item["next_action"], cell_format)
            worksheet.write(row, 11, item["source"], cell_format)
            worksheet.write(row, 12, item.get("band_crosscheck", "NOT_RUN"), cell_format)
            worksheet.set_row(row, 70)
            row += 1

        worksheet.autofilter(start_row, 0, max(start_row, row - 1), len(headers) - 1)

        class_manifest_rows = (
            evidence.get("class_manifest_rows", []) if isinstance(evidence, dict) else []
        )
        manifest_start = row + 2
        worksheet.write(manifest_start, 0, "Class Selection Manifest", header_format)
        worksheet.write_row(
            manifest_start + 1,
            0,
            [
                "Class",
                "Selected",
                "Row status",
                "Required tests",
                "Reviewer",
                "Review status",
                "Source authority",
                "Source reference",
                "Notes",
            ],
            subheader_format,
        )
        manifest_row_index = manifest_start + 2
        if class_manifest_rows:
            for manifest_row in class_manifest_rows:
                row_status = manifest_row.get("row_status", "")
                worksheet.write(
                    manifest_row_index,
                    0,
                    manifest_row.get("validation_class", ""),
                    cell_format,
                )
                worksheet.write(
                    manifest_row_index,
                    1,
                    "YES" if manifest_row.get("selected_bool") else "NO",
                    ready_format if manifest_row.get("selected_bool") else cell_format,
                )
                worksheet.write(
                    manifest_row_index,
                    2,
                    row_status,
                    (
                        ready_format
                        if row_status == "SELECTED_DOCUMENTED"
                        else (
                            missing_format
                            if manifest_row.get("selected_bool")
                            else cell_format
                        )
                    ),
                )
                worksheet.write(
                    manifest_row_index,
                    3,
                    manifest_row.get("required_tests", ""),
                    cell_format,
                )
                worksheet.write(
                    manifest_row_index, 4, manifest_row.get("reviewer", ""), cell_format
                )
                worksheet.write(
                    manifest_row_index,
                    5,
                    manifest_row.get("review_status", ""),
                    cell_format,
                )
                worksheet.write(
                    manifest_row_index,
                    6,
                    manifest_row.get("source_authority", ""),
                    cell_format,
                )
                worksheet.write(
                    manifest_row_index,
                    7,
                    manifest_row.get("source_reference", ""),
                    cell_format,
                )
                worksheet.write(
                    manifest_row_index,
                    8,
                    manifest_row.get("row_status_reason", "")
                    or manifest_row.get("notes", ""),
                    cell_format,
                )
                worksheet.set_row(manifest_row_index, 46)
                manifest_row_index += 1
        else:
            worksheet.write(
                manifest_row_index,
                0,
                "No SIA4010_class_validation_<project>.csv manifest detected.",
                cell_format,
            )
            worksheet.write(manifest_row_index, 1, "NO", missing_format)
            worksheet.write(manifest_row_index, 2, "NOT_SELECTED", missing_format)
            worksheet.write(
                manifest_row_index,
                8,
                "Copy templates/evidence/sia4010_class_validation_template.csv into sia4010_evidence/ and rename it for the project.",
                cell_format,
            )
            manifest_row_index += 1

        readiness_start = manifest_row_index + 2
        worksheet.write(
            readiness_start, 0, "Variant-Level Class Readiness", header_format
        )
        worksheet.write(
            readiness_start,
            1,
            "VE-data readiness and official evidence are separate; neither column grants certification.",
            note_format,
        )
        variant_headers = [
            "Class",
            "Variant",
            "VE readiness",
            "VE status",
            "Official evidence status",
            "Required identifiers",
            "Identifier matches",
            "Identifier mismatches",
            "Present VE data",
            "Missing VE data",
            "Test object",
            "Source",
        ]
        worksheet.write_row(readiness_start + 2, 0, variant_headers, subheader_format)
        readiness_row = readiness_start + 3
        class_readiness = sia4010_results.get("class_readiness", {}) or {}
        for class_name, class_data in class_readiness.items():
            for variant in class_data.get("variant_rows", []) or []:
                ve_status = str(variant.get("ve_status") or "MISSING")
                official_status = str(variant.get("official_status") or "NOT_CHECKABLE")
                identifiers = ", ".join(
                    f"{key}={value}"
                    for key, value in (
                        variant.get("system_identifiers", {}) or {}
                    ).items()
                )
                worksheet.write(readiness_row, 0, class_name, cell_format)
                worksheet.write(readiness_row, 1, variant.get("variant", ""), cell_format)
                worksheet.write(
                    readiness_row, 2, variant.get("readiness_ratio", 0.0), percent_format
                )
                worksheet.write(
                    readiness_row,
                    3,
                    ve_status,
                    self._sia4010_status_format(
                        ve_status,
                        ready_format,
                        partial_format,
                        missing_format,
                        not_checkable_format,
                        cell_format,
                    ),
                )
                worksheet.write(
                    readiness_row,
                    4,
                    official_status,
                    self._sia4010_status_format(
                        official_status,
                        ready_format,
                        partial_format,
                        missing_format,
                        not_checkable_format,
                        cell_format,
                    ),
                )
                worksheet.write(readiness_row, 5, identifiers, cell_format)
                worksheet.write(
                    readiness_row,
                    6,
                    self._compact_join(
                        variant.get("matching_identifiers", []) or [], empty="None"
                    ),
                    cell_format,
                )
                worksheet.write(
                    readiness_row,
                    7,
                    self._compact_join(
                        variant.get("mismatching_identifiers", []) or [], empty="None"
                    ),
                    (
                        missing_format
                        if variant.get("mismatching_identifiers")
                        else ready_format
                    ),
                )
                worksheet.write(
                    readiness_row,
                    8,
                    self._compact_join(
                        variant.get("present_labels", []) or [], empty="None"
                    ),
                    cell_format,
                )
                worksheet.write(
                    readiness_row,
                    9,
                    self._compact_join(
                        variant.get("missing_labels", []) or [], empty="None"
                    ),
                    cell_format,
                )
                worksheet.write(readiness_row, 10, variant.get("object", ""), cell_format)
                worksheet.write(readiness_row, 11, variant.get("source", ""), cell_format)
                worksheet.set_row(readiness_row, 58)
                readiness_row += 1
        if readiness_row == readiness_start + 3:
            worksheet.write(
                readiness_row,
                0,
                "Variant readiness was not generated in this run.",
                cell_format,
            )
            worksheet.write(readiness_row, 4, "NOT_CHECKABLE", not_checkable_format)

        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:A", 10)
        worksheet.set_column("B:C", 18)
        worksheet.set_column("D:E", 42)
        worksheet.set_column("F:F", 20)
        worksheet.set_column("G:G", 18)
        worksheet.set_column("H:L", 44)
        worksheet.set_column("L:L", 44)

    def _write_sia4010_software_register_xlsxwriter(self):
        """Write manager-provided SIA 4010 validated-software register guardrails."""
        worksheet = self.workbook.add_worksheet("SIA4010 SOFTWARE REGISTER")

        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        subheader_format = self.workbook.add_format(SHARED_FORMATS["subheader"])
        cell_format = self.workbook.add_format(
            {"border": 1, "text_wrap": True, "valign": "top"}
        )
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink", background="panel", text_wrap=True, valign="top"
            )
        )
        warning_format = self.workbook.add_format(
            report_style.xw_status("warning", valign="top")
        )
        pass_format = self.workbook.add_format(
            report_style.xw_status("pass", valign="top")
        )

        worksheet.merge_range(
            "A1:H1", "SIA 4010 Software Register - Manager Reference", header_format
        )
        worksheet.merge_range(
            "A2:H3",
            (
                "This sheet is based on the manager-provided SIA 4010 validated-software register dated 2024-09-17. "
                "It is a guardrail only: it does not validate the active IESVE model or this script. "
                "If IESVE is not listed, the report must not claim software-level SIA 4010 validation without separate official evidence."
            ),
            note_format,
        )

        status = SIA4010_IESVE_REGISTER_STATUS
        worksheet.write("A5", "Software checked", subheader_format)
        worksheet.write("B5", status["software"], cell_format)
        worksheet.write("C5", "Listed in register", subheader_format)
        worksheet.write(
            "D5",
            "YES" if status["listed_in_manager_register"] else "NO",
            pass_format if status["listed_in_manager_register"] else warning_format,
        )
        worksheet.write("E5", "Register date", subheader_format)
        worksheet.write("F5", status["register_date"], cell_format)
        worksheet.write("G5", "Guardrail", subheader_format)
        worksheet.write("H5", status["guardrail"], warning_format)

        start_row = 7
        headers = [
            "Institution",
            "Software",
            "Validated classes",
            "Valid until",
            "Source",
        ]
        worksheet.write_row(start_row, 0, headers, header_format)
        row = start_row + 1
        for item in SIA4010_VALIDATED_SOFTWARE_REGISTER:
            worksheet.write(row, 0, item["institution"], cell_format)
            worksheet.write(row, 1, item["software"], cell_format)
            worksheet.write(row, 2, ", ".join(item["validation_classes"]), cell_format)
            worksheet.write(row, 3, item["valid_until"], cell_format)
            worksheet.write(row, 4, item["source"], cell_format)
            worksheet.set_row(row, 44)
            row += 1

        class_start = row + 2
        worksheet.write(
            class_start, 0, "Validation classes from manager register", header_format
        )
        worksheet.write_row(
            class_start + 1,
            0,
            ["Class", "Applications", "Solar protection", "Tests", "Source"],
            subheader_format,
        )
        class_row = class_start + 2
        for class_name, details in SIA4010_VALIDATION_CLASS_DETAILS.items():
            worksheet.write(class_row, 0, class_name, cell_format)
            worksheet.write(class_row, 1, details["applications"], cell_format)
            worksheet.write(class_row, 2, details["solar_protection"], cell_format)
            worksheet.write(class_row, 3, details["tests"], cell_format)
            worksheet.write(class_row, 4, details["source"], cell_format)
            worksheet.set_row(class_row, 56)
            class_row += 1

        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:A", 32)
        worksheet.set_column("B:B", 28)
        worksheet.set_column("C:D", 20)
        worksheet.set_column("E:E", 58)
        worksheet.set_column("F:F", 18)
        worksheet.set_column("G:G", 20)
        worksheet.set_column("H:H", 62)

    def _write_sia_navigator_backlog_xlsxwriter(self):
        """Write the manager-provided SIA 380/2 navigator product backlog."""
        worksheet = self.workbook.add_worksheet("NAVIGATOR BACKLOG")

        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        cell_format = self.workbook.add_format(
            {"border": 1, "text_wrap": True, "valign": "top"}
        )
        note_format = self.workbook.add_format(
            report_style.xw_format(
                "ink", background="panel", text_wrap=True, valign="top"
            )
        )
        partial_format = self.workbook.add_format(
            report_style.xw_status("warning", valign="top")
        )
        missing_format = self.workbook.add_format(
            report_style.xw_status("fail", valign="top")
        )
        readiness_format = self.workbook.add_format(
            report_style.xw_status("not_checkable", valign="top")
        )

        worksheet.merge_range(
            "A1:G1", "SIA 380/2 Navigator - Product Backlog Integration", header_format
        )
        worksheet.merge_range(
            "A2:G3",
            (
                "This backlog is extracted from the manager-provided navigator document. "
                "It distinguishes the current readiness/reporting MVP from the future constrained-input navigator: closed lists, locked templates, justified overrides and full audit trail."
            ),
            note_format,
        )

        headers = [
            "Epic",
            "Name",
            "User story",
            "Acceptance criteria",
            "Current status",
            "Next action",
            "Source",
        ]
        start_row = 5
        worksheet.write_row(start_row, 0, headers, header_format)
        row = start_row + 1
        for item in SIA3802_NAVIGATOR_BACKLOG:
            status_text = item["current_project_status"]
            status_upper = status_text.upper()
            status_format = (
                missing_format
                if status_upper.startswith("MISSING")
                else (
                    readiness_format
                    if status_upper.startswith("READINESS")
                    else partial_format
                )
            )
            worksheet.write(row, 0, item["epic"], cell_format)
            worksheet.write(row, 1, item["name"], cell_format)
            worksheet.write(row, 2, item["user_story"], cell_format)
            worksheet.write(row, 3, item["acceptance_criteria"], cell_format)
            worksheet.write(row, 4, status_text, status_format)
            worksheet.write(row, 5, item["next_action"], cell_format)
            worksheet.write(
                row,
                6,
                "Sia 380_2 Navigator - Executive Summary & Product Backlog.docx",
                cell_format,
            )
            worksheet.set_row(row, 64)
            row += 1

        worksheet.autofilter(start_row, 0, max(start_row, row - 1), len(headers) - 1)
        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:A", 12)
        worksheet.set_column("B:B", 30)
        worksheet.set_column("C:D", 42)
        worksheet.set_column("E:E", 32)
        worksheet.set_column("F:F", 46)
        worksheet.set_column("G:G", 42)

    def _write_alert_summary_xlsxwriter(self, alert_groups: List[Dict[str, Any]]):
        """Write grouped alerts to reduce repetitive raw alert rows."""
        worksheet = self.workbook.add_worksheet("ALERT SUMMARY")

        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        cell_format = self.workbook.add_format(
            {"border": 1, "text_wrap": True, "valign": "top"}
        )
        number_format = self.workbook.add_format({"border": 1, "num_format": "#,##0"})
        area_format = self.workbook.add_format({"border": 1, "num_format": "#,##0.0"})
        decimal_format = self.workbook.add_format({"border": 1, "num_format": "0.000"})

        worksheet.merge_range(
            "A1:O1", "Alert Summary - Grouped Technical Findings", header_format
        )
        worksheet.merge_range(
            "A2:O2",
            "Repetitive alerts are grouped by category, construction, type and rule.",
            cell_format,
        )

        headers = [
            "Category",
            "Construction",
            "Type",
            "Rule",
            "Max severity",
            "Critical",
            "High",
            "Medium",
            "Low",
            "Count",
            "Affected area (m2)",
            "Avg U",
            "Avg g",
            "Evidence samples",
            "Recommendation",
        ]
        worksheet.write_row(4, 0, headers, header_format)

        row = 5
        for group in alert_groups:
            worksheet.write(row, 0, group["category"], cell_format)
            worksheet.write(row, 1, group["construction"], cell_format)
            worksheet.write(row, 2, group["object_type"], cell_format)
            worksheet.write(row, 3, group["rule"], cell_format)
            worksheet.write(row, 4, group["max_severity"], cell_format)
            worksheet.write(
                row, 5, group["severity_counts"].get("Critical", 0), number_format
            )
            worksheet.write(
                row, 6, group["severity_counts"].get("High", 0), number_format
            )
            worksheet.write(
                row, 7, group["severity_counts"].get("Medium", 0), number_format
            )
            worksheet.write(row, 8, group["severity_counts"].get("Low", 0), number_format)
            worksheet.write(row, 9, group["count"], number_format)
            worksheet.write(row, 10, group["affected_area"], area_format)
            self._write_optional_number(
                worksheet, row, 11, group.get("avg_u"), decimal_format, cell_format
            )
            self._write_optional_number(
                worksheet, row, 12, group.get("avg_g"), decimal_format, cell_format
            )
            worksheet.write(row, 13, "; ".join(group["evidence_samples"]), cell_format)
            worksheet.write(row, 14, group["recommendation"], cell_format)
            row += 1

        worksheet.autofilter(4, 0, max(4, row - 1), len(headers) - 1)
        worksheet.freeze_panes(5, 0)
        worksheet.set_column("A:A", 16)
        worksheet.set_column("B:B", 24)
        worksheet.set_column("C:C", 16)
        worksheet.set_column("D:D", 30)
        worksheet.set_column("E:J", 12)
        worksheet.set_column("K:K", 18)
        worksheet.set_column("L:M", 12)
        worksheet.set_column("N:N", 58)
        worksheet.set_column("O:O", 52)

    def _write_alerts_xlsxwriter(self, alerts: List[Alert]):
        """Write the ALERTS sheet with xlsxwriter."""
        worksheet = self.workbook.add_worksheet("ALERTS")

        # Styles
        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        critical_format = self.workbook.add_format(SHARED_FORMATS["critical"])
        high_format = self.workbook.add_format(SHARED_FORMATS["fail"])
        medium_format = self.workbook.add_format(SHARED_FORMATS["warning"])
        low_format = self.workbook.add_format(
            report_style.xw_format("ink", background="panel")
        )
        cell_format = self.workbook.add_format(report_style.xw_format("ink"))

        note_format = self.workbook.add_format(
            report_style.xw_format(
                "muted",
                italic=True,
                text_wrap=True,
            )
        )

        # Title
        worksheet.merge_range("A1:F1", "Alert List", header_format)
        worksheet.merge_range(
            "A2:F2",
            "All CRITICAL and HIGH alerts are listed individually. Repetitive "
            "lower-severity alerts of the same rule are capped for readability, "
            "with a summary row for the remainder (see DATA QUALITY for full counts).",
            note_format,
        )

        # Header
        headers = [
            "Category",
            "Rule",
            "Description",
            "Severity",
            "Value / evidence",
            "Recommendation",
        ]
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, header_format)
        worksheet.freeze_panes(4, 0)

        # Show blocking alerts in full; cap repetitive lower-severity rules so a
        # single rule (e.g. SIA3802_FRAME_FRACTION x126) cannot drown the list.
        cap_per_rule = 5
        severity_rank = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
        }
        ordered = sorted(alerts, key=lambda a: severity_rank.get(a.severity, 4))
        rule_totals = Counter(alert.rule for alert in alerts)
        written_per_rule: Dict[str, int] = {}
        row = 4
        for alert in ordered:
            always = alert.severity in (Severity.CRITICAL, Severity.HIGH)
            written = written_per_rule.get(alert.rule, 0)
            if not always and written >= cap_per_rule:
                continue
            worksheet.write(row, 0, alert.category, cell_format)
            worksheet.write(row, 1, alert.rule, cell_format)
            worksheet.write(row, 2, alert.description, cell_format)
            worksheet.write(row, 4, self._format_alert_data(alert), cell_format)
            worksheet.write(row, 5, alert.recommendation, cell_format)
            if alert.severity == Severity.CRITICAL:
                worksheet.write(row, 3, alert.severity.value, critical_format)
            elif alert.severity == Severity.HIGH:
                worksheet.write(row, 3, alert.severity.value, high_format)
            elif alert.severity == Severity.MEDIUM:
                worksheet.write(row, 3, alert.severity.value, medium_format)
            else:
                worksheet.write(row, 3, alert.severity.value, low_format)
            written_per_rule[alert.rule] = written + 1
            row += 1
            if (
                not always
                and written_per_rule[alert.rule] == cap_per_rule
                and rule_totals[alert.rule] > cap_per_rule
            ):
                remaining = rule_totals[alert.rule] - cap_per_rule
                worksheet.merge_range(
                    row,
                    0,
                    row,
                    5,
                    "... +{} more '{}' alerts of the same type (capped for readability)".format(
                        remaining, alert.rule
                    ),
                    note_format,
                )
                row += 1

        # Set readable column widths.
        worksheet.set_column("A:A", 15)
        worksheet.set_column("B:B", 20)
        worksheet.set_column("C:C", 40)
        worksheet.set_column("D:D", 15)
        worksheet.set_column("E:E", 38)
        worksheet.set_column("F:F", 40)

    def _write_data_quality_xlsxwriter(self, alerts: List[Alert], rooms_data: List[Any]):
        """Write a data-quality and API-coverage summary sheet."""
        worksheet = self.workbook.add_worksheet("DATA QUALITY")

        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        subheader_format = self.workbook.add_format(SHARED_FORMATS["subheader"])
        cell_format = self.workbook.add_format({"border": 1})
        warning_format = self.workbook.add_format(SHARED_FORMATS["warning"])
        fail_format = self.workbook.add_format(SHARED_FORMATS["fail"])
        percent_format = self.workbook.add_format({"border": 1, "num_format": "0.0%"})
        uvalue_format = self.workbook.add_format({"border": 1, "num_format": "0.000"})

        severity_counts = self._count_alerts_by_severity(alerts)
        category_counts = Counter(alert.category for alert in alerts)
        rule_counts = Counter(alert.rule for alert in alerts)
        missing_alerts = [
            alert
            for alert in alerts
            if "MISSING" in str(alert.rule).upper()
            or "NOT_CHECKABLE" in str(alert.rule).upper()
            or "non disponible" in str(alert.description).lower()
        ]
        total_area = sum(
            self._safe_float(getattr(room, "area", 0.0)) for room in rooms_data
        )
        total_volume = sum(
            self._safe_float(getattr(room, "volume", 0.0)) for room in rooms_data
        )

        worksheet.merge_range("A1:F1", "Data Quality & API Coverage", header_format)
        worksheet.write("A3", "KPI", header_format)
        kpis = [
            ("Rooms analysed", len(rooms_data)),
            ("Total area (m2)", total_area),
            ("Total volume (m3)", total_volume),
            ("Total alerts", len(alerts)),
            ("Critical alerts", severity_counts.get("Critical", 0)),
            (
                "Warnings",
                severity_counts.get("High", 0) + severity_counts.get("Medium", 0),
            ),
            ("Information", severity_counts.get("Low", 0)),
            ("Missing / not checkable data", len(missing_alerts)),
        ]
        for row, (label, value) in enumerate(kpis, start=3):
            worksheet.write(row, 0, label, subheader_format)
            worksheet.write(row, 1, value, cell_format)

        worksheet.write("D3", "Interpretation", header_format)
        interpretation = (
            "Read the score carefully when many alerts are MISSING or NOT_CHECKABLE: "
            "this usually indicates missing evidence/extraction first, not necessarily "
            "a physical building non-compliance."
        )
        worksheet.write(
            "D4", interpretation, warning_format if missing_alerts else cell_format
        )
        worksheet.set_row(3, 45)

        worksheet.write("A13", "Alerts by category", header_format)
        worksheet.write_row("A14", ["Category", "Count"], subheader_format)
        row = 14
        for category, count in category_counts.most_common():
            worksheet.write(row, 0, category, cell_format)
            worksheet.write(row, 1, count, cell_format)
            row += 1

        worksheet.write("D13", "Most frequent rules", header_format)
        worksheet.write_row("D14", ["Rule", "Count", "Share"], subheader_format)
        row = 14
        for rule, count in rule_counts.most_common(12):
            worksheet.write(row, 3, rule, cell_format)
            worksheet.write(row, 4, count, cell_format)
            worksheet.write(row, 5, count / len(alerts) if alerts else 0, percent_format)
            row += 1

        start_row = max(row + 2, 24)
        worksheet.write(start_row, 0, "Rooms requiring review", header_format)
        worksheet.write_row(
            start_row + 1,
            0,
            ["Room ID", "Name", "Area (m2)", "WWR", "Average wall U-value", "Comment"],
            subheader_format,
        )
        row = start_row + 2
        for room in rooms_data:
            wwr = self._calculate_wwr(room)
            avg_u = self._calculate_average_u_value(room, "wall")
            if wwr <= 0.3 and avg_u not in (0, None):
                continue
            comment = []
            if wwr > 0.3:
                comment.append("WWR above current threshold")
            if avg_u == 0:
                comment.append("U-value not extracted")
            worksheet.write(row, 0, getattr(room, "id", ""), cell_format)
            worksheet.write(row, 1, getattr(room, "name", ""), cell_format)
            worksheet.write(row, 2, float(getattr(room, "area", 0.0) or 0.0), cell_format)
            worksheet.write(row, 3, wwr, percent_format)
            worksheet.write(row, 4, avg_u, uvalue_format)
            worksheet.write(
                row, 5, "; ".join(comment), fail_format if comment else cell_format
            )
            row += 1

        worksheet.set_column("A:A", 22)
        worksheet.set_column("B:B", 16)
        worksheet.set_column("C:C", 14)
        worksheet.set_column("D:D", 34)
        worksheet.set_column("E:E", 12)
        worksheet.set_column("F:F", 42)

    def _write_detailed_scores_xlsxwriter(self, detailed_scores: Dict[str, float]):
        """Write the DETAILED SCORES sheet with xlsxwriter."""
        worksheet = self.workbook.add_worksheet("DETAILED SCORES")

        # Styles
        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        cell_format = self.workbook.add_format({"border": 1})

        # Title
        worksheet.merge_range("A1:B1", "Detailed Scores", header_format)

        # Header
        worksheet.write("A2", "Category", header_format)
        worksheet.write("B2", "Score (0-100)", header_format)

        # Data
        row = 3
        for category, score in detailed_scores.items():
            worksheet.write(row, 0, category, cell_format)
            worksheet.write(row, 1, score, cell_format)
            row += 1

        # Set readable column widths.
        worksheet.set_column("A:A", 30)
        worksheet.set_column("B:B", 20)

    def _write_rooms_xlsxwriter(self, rooms_data: List[Any]):
        """Write the ROOMS sheet with xlsxwriter."""
        worksheet = self.workbook.add_worksheet("ROOMS")

        # Styles
        header_format = self.workbook.add_format(SHARED_FORMATS["header"])
        cell_format = self.workbook.add_format({"border": 1})
        number_format = self.workbook.add_format({"border": 1, "num_format": "#,##0.0"})
        percent_format = self.workbook.add_format({"border": 1, "num_format": "0.0%"})
        uvalue_format = self.workbook.add_format({"border": 1, "num_format": "0.000"})

        # Title
        worksheet.merge_range("A1:F1", "Room Data", header_format)

        # Header
        headers = [
            "ID",
            "Name",
            "Area (m2)",
            "Volume (m3)",
            "WWR",
            "Average U-value (W/m2K)",
        ]
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, header_format)

        # Data
        row = 3
        for room in rooms_data:
            worksheet.write(row, 0, room.id, cell_format)
            worksheet.write(row, 1, room.name, cell_format)
            worksheet.write(row, 2, room.area, number_format)
            worksheet.write(row, 3, room.volume, number_format)
            worksheet.write(row, 4, self._calculate_wwr(room), percent_format)
            worksheet.write(
                row, 5, self._calculate_average_u_value(room, "wall"), uvalue_format
            )
            row += 1

        # Set readable column widths.
        worksheet.set_column("A:A", 10)
        worksheet.set_column("B:B", 20)
        worksheet.set_column("C:C", 15)
        worksheet.set_column("D:D", 15)
        worksheet.set_column("E:E", 10)
        worksheet.set_column("F:F", 25)

    # =============================================================================
    # Utility methods
    # =============================================================================

    @staticmethod
    def _count_alerts_by_severity(alerts: List[Alert]) -> Dict[str, int]:
        """
        Count alerts by severity.
        """
        counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for alert in alerts:
            counts[alert.severity.value] += 1
        return counts

    def _build_sia_data_coverage_rows(
        self,
        sia3802_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
        rooms_data: List[Any],
        preflight_checks: List[Dict[str, Any]],
        dynamic_results: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Build data coverage rows for automated checks, APS/Vista data and external evidence."""
        stats = dict(self._build_sia4010_model_stats(rooms_data, sia4010_results))
        # Reviewed thermal-bridge (psi/chi) evidence is a SIA 380/2 result, so it
        # rides on sia3802_results, not the model stats. Surface it to the
        # coverage check for the thermal_bridges key.
        thermal_bridges = (sia3802_results or {}).get("thermal_bridges", {}) or {}
        stats["thermal_bridge_accepted"] = bool(thermal_bridges.get("accepted"))
        record = thermal_bridges.get("record") or {}
        if isinstance(record, dict) and thermal_bridges.get("accepted"):
            method = str(record.get("assessment_method") or "").strip()
            total = record.get("total_psi_chi_w_per_k_numeric")
            detail = "method={}".format(method) if method else "reviewed schedule"
            if total is not None:
                detail += ", total psi.L+chi={} W/K".format(total)
            stats["thermal_bridge_evidence"] = (
                "Reviewer-accepted thermal-bridge evidence ({}).".format(detail)
            )
        # VE 2025.2 reads psi/chi directly (VESurface thermal bridges): the model
        # thermal-bridge conductance H_tb (W/K) is the primary evidence.
        stats["thermal_bridge_ve_available"] = bool(thermal_bridges.get("ve_available"))
        if thermal_bridges.get("ve_available"):
            total_htb = thermal_bridges.get("total_w_per_k")
            nonzero = thermal_bridges.get("nonzero_count")
            zero_psi = thermal_bridges.get("zero_psi_linear_count")
            detail = "H_tb={} W/K from {} non-zero junction(s)".format(
                round(total_htb, 3) if isinstance(total_htb, (int, float)) else total_htb,
                nonzero,
            )
            if zero_psi:
                detail += (
                    "; {} junction(s) at psi=0 (verify not un-entered defaults)".format(
                        zero_psi
                    )
                )
            stats["thermal_bridge_ve_evidence"] = "VE-read thermal bridges ({}).".format(
                detail
            )
        # Reviewed cooling-generator EER/SEER evidence (autosize workaround) also
        # rides on sia3802_results. Surface it to the cooling_efficiency key.
        cooling_generators = (sia3802_results or {}).get("cooling_generators", {}) or {}
        stats["cooling_generator_accepted"] = bool(cooling_generators.get("accepted"))
        cooling_record = cooling_generators.get("record") or {}
        if isinstance(cooling_record, dict) and cooling_generators.get("accepted"):
            gen_class = str(cooling_record.get("generator_class") or "").strip()
            capacity = cooling_record.get("capacity_kw_numeric")
            eer = cooling_record.get("nominal_eer_numeric")
            seer = cooling_record.get("seer_numeric")
            detail = "class={}".format(gen_class) if gen_class else "reviewed generator"
            if capacity is not None:
                detail += ", capacity={} kW".format(capacity)
            if eer is not None:
                detail += ", nominal EER={}".format(eer)
            if seer is not None:
                detail += ", SEER={} [conditional on SN EN 14825]".format(seer)
            stats["cooling_generator_evidence"] = (
                "Reviewer-accepted cooling-generator evidence ({}).".format(detail)
            )
        # Reviewed AHU / heat-recovery (Table 4) evidence rides on sia3802_results.
        ahu = (sia3802_results or {}).get("ahu_heat_recovery", {}) or {}
        stats["ahu_reviewed_accepted"] = bool(ahu.get("accepted"))
        ahu_record = ahu.get("record") or {}
        if isinstance(ahu_record, dict) and ahu.get("accepted"):
            leakage = str(ahu_record.get("leakage_class") or "").strip()
            eta = ahu_record.get("heat_recovery_temperature_efficiency_numeric")
            detail = "leakage class={}".format(leakage) if leakage else "reviewed AHU"
            if eta is not None:
                detail += ", heat-recovery temperature efficiency={}".format(eta)
            stats["ahu_reviewed_evidence"] = (
                "Reviewer-accepted AHU/heat-recovery evidence ({}).".format(detail)
            )
        # Reviewed ventilation-control (Table 4) evidence rides on sia3802_results.
        vent = (sia3802_results or {}).get("ventilation_control_evidence", {}) or {}
        stats["ventilation_control_reviewed_accepted"] = bool(vent.get("accepted"))
        vent_record = vent.get("record") or {}
        if isinstance(vent_record, dict) and vent.get("accepted"):
            system_type = str(vent_record.get("system_type") or "").strip()
            control_class = str(vent_record.get("control_class") or "").strip()
            band = str(vent_record.get("airflow_band") or "").strip()
            detail = (
                "system={}".format(system_type) if system_type else "reviewed control"
            )
            if control_class:
                detail += ", control class={}".format(control_class)
            if band:
                detail += ", airflow band={}".format(band)
            stats["ventilation_control_reviewed_evidence"] = (
                "Reviewer-accepted ventilation-control evidence ({}).".format(detail)
            )
        # Reviewed solar-protection (Table 10) windows documented outside VE.
        solar_evidence = (sia3802_results or {}).get(
            "solar_protection_evidence", {}
        ) or {}
        stats["solar_protection_reviewed_windows"] = int(
            solar_evidence.get("accepted_window_count", 0) or 0
        )
        # Reviewed §7.2.4 required electrical power (W/m2) documented outside VE.
        electrical_power = (sia3802_results or {}).get("electrical_power", {}) or {}
        stats["electrical_power_accepted"] = bool(electrical_power.get("accepted"))
        ep_record = electrical_power.get("record") or {}
        if isinstance(ep_record, dict) and electrical_power.get("accepted"):
            value = ep_record.get("required_electrical_power_w_m2_numeric")
            limit = electrical_power.get("limit_w_m2")
            meets = electrical_power.get("meets_limit")
            verdict = "meets" if meets else ("exceeds" if meets is False else "vs")
            stats["electrical_power_evidence"] = (
                "Reviewer §7.2.4 required electrical power {} W/m2 ({} the {} W/m2 "
                "limit for {}).".format(
                    value, verdict, limit, ep_record.get("building_status_key") or "?"
                )
            )
        evidence = sia4010_results.get("evidence", {}) or {}
        dynamic_payload = (
            dynamic_results or sia4010_results.get("dynamic_results", {}) or {}
        )
        preflight_status_by_check = {
            str(item.get("check", "")): str(item.get("status", ""))
            for item in preflight_checks or []
            if isinstance(item, dict)
        }

        rows: List[Dict[str, Any]] = []
        for item in SIA_DATA_COVERAGE_MATRIX:
            coverage_status, current_evidence = self._coverage_status_for_key(
                str(item.get("coverage_key", "")),
                stats,
                evidence,
                dynamic_payload,
                preflight_status_by_check,
            )
            rows.append(
                {
                    "coverage_status": coverage_status,
                    "current_evidence": current_evidence,
                    "id": item.get("id", ""),
                    "standard": item.get("standard", ""),
                    "validation_scope": item.get("validation_scope", ""),
                    "domain": item.get("domain", ""),
                    "criterion": item.get("criterion", ""),
                    "expected_value": item.get("expected_value", ""),
                    "data_needed": item.get("data_needed", ""),
                    "expected_source": item.get("expected_source", ""),
                    "automation": item.get("automation", ""),
                    "preferred_format": item.get("preferred_format", ""),
                    "destination": item.get("destination", ""),
                    "source": item.get("source", ""),
                    "owner": item.get("owner", ""),
                    "next_action": item.get("next_action", ""),
                }
            )

        selected_class = str(evidence.get("validation_class") or "").upper()
        all_evidence_present = all(
            self._has_sia4010_evidence(evidence, item)
            for item in SIA4010_REQUIRED_EVIDENCE
        )
        for class_name, required_tests in SIA4010_VALIDATION_CLASSES.items():
            if selected_class == class_name and all_evidence_present:
                status = "AVAILABLE"
                current = "Selected class and all required evidence families detected."
            elif selected_class == class_name:
                status = "PARTIAL"
                current = "Selected class detected, but official evidence is incomplete."
            else:
                status = "MISSING"
                current = f"Selected class detected: {selected_class or 'none'}."

            rows.append(
                {
                    "coverage_status": status,
                    "current_evidence": current,
                    "id": f"SIA4010_CLASS_{class_name}",
                    "standard": "SIA 4010:2023",
                    "validation_scope": f"Class {class_name}",
                    "domain": "Validation class",
                    "criterion": f"SIA 4010 validation class {class_name}",
                    "expected_value": f"Required tests: {required_tests}",
                    "data_needed": "Official class selection/confirmation and required test evidence.",
                    "expected_source": "Official SIA evidence package / responsible validation authority.",
                    "automation": "EVIDENCE_SCAN",
                    "preferred_format": f"File name should include class_{class_name} or classe_{class_name}.",
                    "destination": "sia4010_evidence/",
                    "source": "SIA 4010:2023 FR, tableau 63, page PDF 48",
                    "owner": "Compliance reviewer",
                    "next_action": "Confirm the intended class and attach the official evidence for its required tests.",
                }
            )

        return rows

    def _coverage_status_for_key(
        self,
        key: str,
        stats: Dict[str, Any],
        evidence: Dict[str, Any],
        dynamic_results: Dict[str, Any],
        preflight_status_by_check: Dict[str, str],
    ) -> Any:
        """Return status and observed evidence text for one coverage key."""

        def availability(count: int, total: int, label: str) -> Any:
            """Return coverage status text for count/total evidence pairs."""
            if total <= 0:
                return "MISSING", f"No {label} detected."
            if count >= total:
                return "AVAILABLE", f"{count}/{total} {label} available."
            if count > 0:
                return "PARTIAL", f"{count}/{total} {label} available."
            return "MISSING", f"0/{total} {label} available."

        if key == "project_climate":
            metadata_status = str(
                dynamic_results.get("project_metadata_status") or "NOT_PROVIDED"
            ).upper()
            weather_match = str(
                dynamic_results.get("reviewed_weather_match_status") or "NOT_CHECKABLE"
            ).upper()
            if metadata_status == "AVAILABLE" and weather_match == "MATCH":
                return (
                    "AVAILABLE",
                    "Reviewer-approved project metadata is available and its weather file matches the active VE project weather.",
                )
            active_project_status = preflight_status_by_check.get("Active VE project", "")
            if active_project_status == "PASS":
                return (
                    "PARTIAL",
                    f"Active project detected; metadata={metadata_status}, reviewed weather match={weather_match}.",
                )
            return "MISSING", "No active project evidence in preflight checks."
        if key == "rooms":
            count = int(stats.get("rooms", 0) or 0)
            return (
                ("AVAILABLE", f"{count} thermal room(s) extracted.")
                if count
                else ("MISSING", "No thermal room extracted.")
            )
        if key == "use_category":
            count = int(stats.get("rooms", 0) or 0)
            mapped = int(stats.get("rooms_with_use_category", 0) or 0)
            if not count:
                return "MISSING", "No room data available for SIA 2024 mapping."
            if mapped >= count:
                return (
                    "AVAILABLE",
                    f"{mapped}/{count} room(s) carry a reviewer-accepted SIA 2024 use category.",
                )
            if mapped:
                return (
                    "PARTIAL",
                    f"{mapped}/{count} room(s) carry a reviewer-accepted SIA 2024 use category; confirm the rest.",
                )
            return (
                "PARTIAL",
                f"{count} room(s) extracted; SIA 2024 category mapping still needs confirmation.",
            )
        if key == "external_surfaces":
            count = int(stats.get("external_surfaces", 0) or 0)
            return (
                ("AVAILABLE", f"{count} external surface(s) extracted.")
                if count
                else ("MISSING", "No external surface extracted.")
            )
        if key == "surface_u_values":
            return availability(
                int(stats.get("surface_u_values", 0) or 0),
                int(stats.get("external_surfaces", 0) or 0),
                "external surface U-values",
            )
        if key == "thermal_bridges":
            # VE 2025.2 reads psi/chi per surface, so the model's H_tb (W/K) is
            # the primary evidence. A reviewer schedule is the fallback. An
            # all-zero VE read (possible un-entered defaults) is not complete
            # evidence, so it does not credit AVAILABLE on its own.
            if stats.get("thermal_bridge_ve_available"):
                return (
                    "AVAILABLE",
                    stats.get("thermal_bridge_ve_evidence")
                    or "VE-read thermal-bridge conductance (psi.L + chi) available.",
                )
            if stats.get("thermal_bridge_accepted"):
                return (
                    "AVAILABLE",
                    stats.get("thermal_bridge_evidence")
                    or "Reviewer-accepted thermal-bridge (psi/chi) schedule ingested.",
                )
            return (
                "MISSING",
                "No VE-read psi/chi thermal bridges and no reviewed schedule; the configured zero remains a placeholder, not evidence.",
            )
        if key == "window_u_values":
            return availability(
                int(stats.get("window_u_values", 0) or 0),
                int(stats.get("external_windows", 0) or 0),
                "external window U-values",
            )
        if key == "window_g_values":
            total_windows = int(stats.get("external_windows", 0) or 0)
            en410_count = int(
                stats.get("en410_g_values", stats.get("window_g_values", 0)) or 0
            )
            raw_cdb_count = int(stats.get("raw_cdb_g_values", 0) or 0)
            if total_windows <= 0:
                return (
                    "MISSING",
                    "No external window data available for g-value evidence.",
                )
            if en410_count >= total_windows:
                return (
                    "AVAILABLE",
                    f"{en410_count}/{total_windows} external window EN 410 g_perp values available.",
                )
            if en410_count or raw_cdb_count:
                return (
                    "PARTIAL",
                    (
                        f"{en410_count}/{total_windows} EN 410 g_perp values available; "
                        f"{raw_cdb_count}/{total_windows} raw CDB g_value entries available but not automatically SIA-comparable."
                    ),
                )
            return "MISSING", "No EN 410 g_perp or raw CDB g-value evidence extracted."
        if key == "visible_transmittance":
            return availability(
                int(stats.get("visible_transmittance_values", 0) or 0),
                int(stats.get("external_windows", 0) or 0),
                "external window visible transmittance values",
            )
        if key == "frame_fraction":
            return availability(
                int(stats.get("frame_fraction_values", 0) or 0),
                int(stats.get("external_windows", 0) or 0),
                "external window frame-fraction values",
            )
        if key == "solar_protection":
            total_windows = int(stats.get("external_windows", 0) or 0)
            if total_windows <= 0:
                return (
                    "MISSING",
                    "No external window data available for solar-protection evidence.",
                )
            type_count = int(stats.get("solar_protection_types", 0) or 0)
            control_count = int(stats.get("solar_protection_controls", 0) or 0)
            g_total_count = int(stats.get("g_total_values", 0) or 0)
            g_total_not_required = int(
                stats.get("g_total_not_required_for_g_limit", 0) or 0
            )
            g_total_coverage = min(total_windows, g_total_count + g_total_not_required)
            reviewed_windows = int(stats.get("solar_protection_reviewed_windows", 0) or 0)
            evidence_text = (
                f"type/category {type_count}/{total_windows}; "
                f"control/profile {control_count}/{total_windows}; "
                f"active g_total {g_total_count}/{total_windows}; "
                f"EN 410 g already <= SIA limit {g_total_not_required}/{total_windows}."
            )
            if reviewed_windows:
                evidence_text += f" reviewer-documented shading windows {reviewed_windows}/{total_windows}."
            # Reviewer-documented shading (Table 10) covers windows VE does not
            # model. Credit AVAILABLE only when the VE-derived coverage plus the
            # reviewed windows reach every external window; never a silent pass.
            ve_type_covered = min(total_windows, type_count)
            combined_covered = min(
                total_windows,
                max(ve_type_covered, g_total_coverage) + reviewed_windows,
            )
            if (
                type_count >= total_windows
                and control_count >= total_windows
                and g_total_coverage >= total_windows
            ):
                return "AVAILABLE", evidence_text
            if reviewed_windows and combined_covered >= total_windows:
                return "AVAILABLE", evidence_text
            if (
                type_count
                or control_count
                or g_total_count
                or g_total_not_required
                or reviewed_windows
            ):
                return "PARTIAL", evidence_text
            return "MISSING", evidence_text
        if key == "schedules":
            return availability(
                int(stats.get("rooms_with_daily_profile_hours", 0) or 0),
                int(stats.get("rooms", 0) or 0),
                "rooms with resolved representative daily profile hours",
            )
        if key == "ventilation_control":
            if stats.get("ventilation_control_reviewed_accepted"):
                return "AVAILABLE", stats.get(
                    "ventilation_control_reviewed_evidence",
                    "Reviewer-accepted ventilation-control class (SIA 380/2 Table 4).",
                )
            return availability(
                int(stats.get("rooms_with_ventilation_control", 0) or 0),
                int(stats.get("rooms_with_ventilation", 0) or 0),
                "ventilated rooms with system/control classification",
            )
        if key == "ahu_heat_recovery":
            if stats.get("ahu_reviewed_accepted"):
                return "AVAILABLE", stats.get(
                    "ahu_reviewed_evidence",
                    "Reviewer-accepted AHU leakage class and heat-recovery efficiency (SIA 380/2 Table 4).",
                )
            count = int(stats.get("rooms_with_ahu_identifiers", 0) or 0)
            if count:
                return (
                    "PARTIAL",
                    f"{count} room(s) expose fan/recovery/humidification identifiers; pressure-drop, leakage and verified efficiency evidence remains external. Attach reviewed evidence via SIA3802_ahu_heat_recovery_<project>.csv.",
                )
            return (
                "MISSING",
                "No AHU fan/recovery/humidification identifier was extracted. Provide reviewed evidence via SIA3802_ahu_heat_recovery_<project>.csv.",
            )
        if key == "electrical_power":
            if stats.get("electrical_power_accepted"):
                return "AVAILABLE", stats.get(
                    "electrical_power_evidence",
                    "Reviewer-accepted §7.2.4 required electrical power (W/m2).",
                )
            return (
                "MISSING",
                "No reviewed §7.2.4 required electrical power (W/m2) provided; it is a design "
                "sizing figure VE does not expose. Attach SIA3802_electrical_power_<project>.csv.",
            )
        if key == "cooling_efficiency":
            if stats.get("cooling_generator_accepted"):
                return "AVAILABLE", stats.get(
                    "cooling_generator_evidence",
                    "Reviewer-accepted cooling-generator class/capacity/EER evidence.",
                )
            count = int(stats.get("cooling_systems_with_efficiency", 0) or 0)
            if count:
                return (
                    "PARTIAL",
                    f"{count} cooling system(s) expose class, capacity and EER/SEER; Table 7 EER+ and part-load evidence remains conditional.",
                )
            return (
                "MISSING",
                "No cooling system exposes a complete class/capacity/EER-or-SEER tuple. Provide reviewed manufacturer EER via SIA3802_cooling_generators_<project>.csv when the generator is autosized.",
            )
        if key == "heating_efficiency":
            count = int(stats.get("heating_systems_with_efficiency", 0) or 0)
            if count:
                return (
                    "PARTIAL",
                    f"{count} heating system(s) expose heat-pump class, capacity and SCOP; delegated evidence remains conditional.",
                )
            heat_pumps = int(stats.get("heat_pump_heating_systems", 0) or 0)
            non_heat_pumps = int(stats.get("non_heat_pump_heating_systems", 0) or 0)
            if heat_pumps:
                return (
                    "MISSING",
                    f"{heat_pumps} heat-pump heating system(s) present without a complete class/capacity/SCOP tuple; SCOP evidence required.",
                )
            if non_heat_pumps:
                return (
                    "NON_APPLICABLE",
                    f"{non_heat_pumps} heating generator(s) are not heat pumps; SCOP does not apply (SIA 380/2). Non-heat-pump generation efficiency runs through the global project/reference comparison.",
                )
            return (
                "MISSING",
                "No heating system exposes a complete heat-pump class/capacity/SCOP tuple.",
            )
        if key == "infiltration":
            rooms = int(stats.get("rooms", 0) or 0)
            converted = int(stats.get("rooms_with_infiltration_m3_h_m2", 0) or 0)
            raw = int(stats.get("rooms_with_infiltration", 0) or 0)
            if converted:
                return availability(converted, rooms, "rooms with converted infiltration")
            if raw:
                return (
                    "PARTIAL",
                    f"{raw}/{rooms} room(s) expose raw infiltration; unit conversion still needs confirmation.",
                )
            return "MISSING", "No room infiltration value extracted."
        if key == "internal_gains":
            rooms = int(stats.get("rooms", 0) or 0)
            gain_rooms = max(
                int(stats.get("rooms_with_lighting", 0) or 0),
                int(stats.get("rooms_with_equipment", 0) or 0),
            )
            return availability(gain_rooms, rooms, "rooms with internal gain data")
        if key == "ventilation_rates":
            return availability(
                int(stats.get("rooms_with_ventilation", 0) or 0),
                int(stats.get("rooms", 0) or 0),
                "rooms with ventilation rate data",
            )
        if key == "lighting_control":
            lighting_rooms = int(stats.get("rooms_with_lighting", 0) or 0)
            dynamic_lighting_rows = int(stats.get("dynamic_lighting_rows", 0) or 0)
            control_mappings = int(stats.get("lighting_control_mappings", 0) or 0)
            # Best effort while SIA 387/4 (lighting-control reference) is absent:
            # a reviewer-confirmed SIA 387/4 control-type mapping covering the lit
            # rooms is credited AVAILABLE, but explicitly UNDER RESERVE -- the tool
            # cannot itself verify the control type against SIA 387/4 (the numeric
            # control tables are not in refs/). It is a reviewer attestation, not a
            # proven pass. See docs/project/RESERVES_NORMATIVES.md.
            if control_mappings and lighting_rooms and control_mappings >= lighting_rooms:
                return (
                    "AVAILABLE",
                    (
                        f"{control_mappings}/{lighting_rooms} lit room(s) carry a "
                        "reviewer-confirmed SIA 387/4 control-type mapping "
                        "[UNDER RESERVE: SIA 387/4 lighting-control tables absent; "
                        "reviewer attestation, not an independently verified pass]."
                    ),
                )
            if lighting_rooms or dynamic_lighting_rows or control_mappings:
                return (
                    "PARTIAL",
                    (
                        f"{lighting_rooms} room(s) expose lighting gains; "
                        f"{control_mappings} room(s) carry a reviewer control mapping; "
                        f"{dynamic_lighting_rows} APS room row(s) expose lighting energy; "
                        "daylight/presence control strategy still needs the SIA 387/4 mapping."
                    ),
                )
            return (
                "MISSING",
                "No lighting power, lighting energy or control evidence extracted.",
            )
        if key == "dynamic_aps":
            status = str(
                dynamic_results.get("status", "NOT_CHECKABLE") or "NOT_CHECKABLE"
            ).upper()
            aps_count = len(dynamic_results.get("aps_files", []) or [])
            selected = dynamic_results.get("selected_aps_file") or "none"
            if status == "AVAILABLE":
                return (
                    "AVAILABLE",
                    f"{aps_count} APS file(s) detected; selected {selected}; room results readable.",
                )
            if status == "PARTIAL":
                return (
                    "PARTIAL",
                    f"{aps_count} APS file(s) detected; selected {selected}; room results incomplete.",
                )
            return (
                "NOT_CHECKABLE",
                dynamic_results.get("notes")
                or f"{aps_count} APS file(s) detected; ResultsReader did not provide room results.",
            )
        if key == "hourly_temperatures":
            room_rows = int(stats.get("dynamic_room_rows", 0) or 0)
            temperature_rows = int(stats.get("dynamic_temperature_rows", 0) or 0)
            complete_rows = int(stats.get("dynamic_annual_comfort_rows", 0) or 0)
            if room_rows > 0 and complete_rows == room_rows:
                return (
                    "AVAILABLE",
                    f"{complete_rows}/{room_rows} room(s) have complete annual temperature, occupancy and SIA 180 limit-curve series.",
                )
            if temperature_rows > 0:
                return (
                    "PARTIAL",
                    f"{temperature_rows}/{room_rows} room(s) expose temperature/occupancy indicators, but only {complete_rows}/{room_rows} have complete annual SIA 180 comfort series.",
                )
            return (
                "MISSING",
                "No usable APS room temperature/occupancy series was extracted.",
            )
        if key == "heating_cooling_demands":
            room_rows = int(stats.get("dynamic_room_rows", 0) or 0)
            heating_rows = int(stats.get("dynamic_heating_rows", 0) or 0)
            cooling_rows = int(stats.get("dynamic_cooling_rows", 0) or 0)
            if room_rows > 0 and heating_rows == room_rows and cooling_rows == room_rows:
                return (
                    "AVAILABLE",
                    f"Heating and cooling demand series are available for all {room_rows} APS room(s).",
                )
            if heating_rows or cooling_rows:
                return (
                    "PARTIAL",
                    f"Heating demand is available for {heating_rows}/{room_rows} room(s); cooling demand is available for {cooling_rows}/{room_rows} room(s).",
                )
            return (
                "MISSING",
                "No usable APS room heating or cooling demand series was extracted.",
            )

        evidence_prefix = "evidence_"
        if key.startswith(evidence_prefix):
            family = key[len(evidence_prefix) :]
            family_data = evidence.get(family, {}) if isinstance(evidence, dict) else {}
            present = (
                bool(family_data.get("present"))
                if isinstance(family_data, dict)
                else bool(family_data)
            )
            files = family_data.get("files", []) if isinstance(family_data, dict) else []
            if present:
                return (
                    "AVAILABLE",
                    f"{len(files)} matching evidence file(s) detected for {family}.",
                )
            return "MISSING", f"No matching evidence file detected for {family}."

        return "NOT_CHECKABLE", "No coverage rule is implemented for this key yet."

    @staticmethod
    def _coverage_status_format(
        status: str,
        available_format: Any,
        partial_format: Any,
        missing_format: Any,
        not_checkable_format: Any,
        cell_format: Any,
    ) -> Any:
        """Return the Excel cell format for a data-coverage status."""
        status_upper = str(status or "").upper()
        if status_upper == "AVAILABLE":
            return available_format
        if status_upper == "PARTIAL":
            return partial_format
        if status_upper == "MISSING":
            return missing_format
        if status_upper == "NOT_CHECKABLE":
            return not_checkable_format
        return cell_format

    @staticmethod
    def _input_request_priority(item: Dict[str, Any]) -> str:
        """Rank missing inputs so the handoff sheet starts with true blockers."""
        status = str(item.get("coverage_status", "") or "").upper()
        standard = str(item.get("standard", "") or "").upper()
        domain = str(item.get("domain", "") or "").lower()
        if status in {"MISSING", "NOT_CHECKABLE"} and "SIA 4010" in standard:
            return "P1"
        if status in {"MISSING", "NOT_CHECKABLE"} and domain in {
            "dynamic results",
            "ventilation",
            "cooling",
            "heating",
        }:
            return "P1"
        if status == "PARTIAL" and domain in {"solar protection", "dynamic results"}:
            return "P1"
        if status == "MISSING":
            return "P2"
        return "P3"

    @staticmethod
    def _show_hidden_chart_data(chart: Any) -> None:
        """Keep charts visible even when their helper source columns are hidden."""
        show_hidden_data = getattr(chart, "show_hidden_data", None)
        if callable(show_hidden_data):
            show_hidden_data()

    def _build_sia4010_class_matrix_rows(
        self, sia4010_results: Dict[str, Any], rooms_data: List[Any]
    ) -> List[Dict[str, Any]]:
        """Build one report row per SIA 4010 validation class."""
        class_results = sia4010_results.get("classes", {}) or {}
        test_rows = {
            row["test"]: row
            for row in self._build_sia4010_readiness_rows(sia4010_results, rooms_data)
        }
        evidence = sia4010_results.get("evidence", {}) or {}
        evidence_summary = (
            evidence.get("summary", {}) if isinstance(evidence, dict) else {}
        )
        missing_evidence = evidence_summary.get("missing_items", []) or [
            item
            for item in SIA4010_REQUIRED_EVIDENCE
            if not self._has_sia4010_evidence(evidence, item)
        ]
        selected_class = str(
            sia4010_results.get("validation_class")
            or evidence_summary.get("validation_class")
            or ""
        ).upper()

        rows: List[Dict[str, Any]] = []
        for class_name, tests_label in SIA4010_VALIDATION_CLASSES.items():
            class_data = (
                class_results.get(class_name, {})
                if isinstance(class_results, dict)
                else {}
            )
            aliases = class_data.get(
                "required_test_aliases"
            ) or self._required_sia4010_aliases_for_class(class_name)
            base_tests = []
            for alias in aliases:
                base_test = SIA4010_TEST_ALIAS_TO_BASE_TEST.get(alias, alias)
                if base_test not in base_tests:
                    base_tests.append(base_test)

            readiness_values = [
                float(test_rows.get(base_test, {}).get("readiness_ratio", 0.0) or 0.0)
                for base_test in base_tests
            ]
            ve_readiness_ratio = (
                sum(readiness_values) / len(readiness_values) if readiness_values else 0.0
            )
            official_states = [
                f"{SIA4010_TEST_ALIAS_LABELS.get(alias, alias)}={class_data.get('required_test_statuses', {}).get(alias, test_rows.get(SIA4010_TEST_ALIAS_TO_BASE_TEST.get(alias, alias), {}).get('official_status', 'NOT_CHECKABLE'))}"
                for alias in aliases
            ]
            missing_text = self._compact_join(
                class_data.get("missing_official_evidence", missing_evidence) or [],
                empty="No missing evidence recorded.",
                max_chars=320,
            )
            class_status = class_data.get("class_status")
            if not class_status:
                if selected_class and selected_class != class_name:
                    class_status = "NOT_REQUESTED"
                elif not selected_class:
                    class_status = "CLASS_NOT_SELECTED"
                elif missing_text and missing_text != "No missing evidence recorded.":
                    class_status = "EVIDENCE_INCOMPLETE"
                else:
                    class_status = "READY_FOR_OFFICIAL_REVIEW"

            if class_status == "READY_FOR_OFFICIAL_REVIEW":
                next_action = "Submit the official evidence package for reviewer/sub-commission acceptance."
            elif class_status == "OFFICIAL_RESULTS_RECORDED":
                next_action = "Obtain and archive the SIA sub-commission attestation before using any validated or certified claim."
            elif class_status == "NOT_REQUESTED":
                next_action = f"Select class {class_name} only if this class is intended for the project claim."
            elif class_status == "CLASS_NOT_SELECTED":
                next_action = "Attach validation class confirmation naming the intended class before claiming SIA 4010 validation."
            else:
                next_action = "Complete the missing official SIA 4010 evidence families and rerun the report."

            details = SIA4010_VALIDATION_CLASS_DETAILS.get(class_name, {})
            rows.append(
                {
                    "class": class_name,
                    "selected": bool(
                        class_data.get("selected", selected_class == class_name)
                    ),
                    "class_status": class_status,
                    "application": class_data.get("application")
                    or details.get("applications", ""),
                    "solar_protection": class_data.get("solar_protection")
                    or details.get("solar_protection", ""),
                    "required_tests_label": class_data.get("required_tests_label")
                    or tests_label,
                    "ve_readiness_ratio": ve_readiness_ratio,
                    "official_test_state": self._compact_join(
                        official_states, max_chars=320
                    ),
                    "missing_official_evidence": missing_text,
                    "status_reason": class_data.get("status_reason", ""),
                    "next_action": next_action,
                    "source": class_data.get("source") or details.get("source", ""),
                    "band_crosscheck": (class_data.get("band_crosscheck", {}) or {}).get(
                        "summary", "NOT_RUN"
                    ),
                }
            )
        return rows

    def _build_sia4010_readiness_rows(
        self, sia4010_results: Dict[str, Any], rooms_data: List[Any]
    ) -> List[Dict[str, Any]]:
        """Build one readiness row per SIA 4010 validation test."""
        stats = self._build_sia4010_model_stats(rooms_data, sia4010_results)
        tests = sia4010_results.get("tests", {}) or {}
        required_evidence = self._compact_join(SIA4010_REQUIRED_EVIDENCE, max_chars=300)

        checks_by_test = {
            "test_1": [
                ("zones/rooms extracted", stats["rooms"] > 0),
                ("external envelope surfaces extracted", stats["external_surfaces"] > 0),
                ("surface U-values extracted", stats["surface_u_values"] > 0),
                (
                    "surface tilt/adjacency metadata extracted",
                    stats["surface_tilt_values"] > 0
                    or stats["surface_adjacency_values"] > 0,
                ),
                (
                    "external window/opening data extracted",
                    stats["external_openings"] > 0,
                ),
                ("official test model/reference outputs attached", False),
            ],
            "test_2": [
                ("external glazing extracted", stats["external_windows"] > 0),
                (
                    "EN 410/SIA-comparable g_perp values extracted",
                    stats["en410_g_values"] > 0,
                ),
                (
                    "solar protection type/category documented",
                    stats["solar_protection_types"] > 0,
                ),
                (
                    "solar protection control strategy documented",
                    stats["solar_protection_controls"] > 0,
                ),
                (
                    "active glazing-plus-shading g_total documented when needed for the table 2 reference-input comparison",
                    stats["external_windows"] > 0
                    and (
                        stats["g_total_values"] > 0
                        or stats["g_total_not_required_for_g_limit"]
                        >= stats["external_windows"]
                    ),
                ),
                ("official CH climate/use/infiltration diagnostic attached", False),
            ],
            "test_3": [
                ("lighting power extracted", stats["rooms_with_lighting"] > 0),
                (
                    "daylight control strategy documented",
                    stats["daylight_control_evidence"] > 0,
                ),
                (
                    "SIA 387/4 lighting control type documented",
                    stats["lighting_control_mappings"] > 0,
                ),
                (
                    "lighting energy outputs available",
                    stats["dynamic_lighting_rows"] > 0
                    or stats["lighting_energy_available"],
                ),
                ("official test 3 evaluation file attached", False),
            ],
            "test_4": [
                ("HVAC systems extracted", stats["rooms_with_hvac"] > 0),
                (
                    "ventilation/airflow data extracted",
                    stats["rooms_with_ventilation"] > 0,
                ),
                (
                    "cooling/heating coil outputs available",
                    stats["dynamic_coil_rows"] > 0
                    or stats["dynamic_demand_rows"] > 0
                    or stats["cooling_demand_available"]
                    or stats["heating_demand_available"],
                ),
                (
                    "temperature hourly outputs available",
                    stats["dynamic_temperature_rows"] > 0,
                ),
                (
                    "CO2 hourly outputs available or manually evidenced",
                    stats["dynamic_co2_rows"] > 0,
                ),
                ("official amphitheatre test/evaluation attached", False),
            ],
            "test_5": [
                ("HVAC/AHU systems extracted", stats["rooms_with_hvac"] > 0),
                ("ventilation data extracted", stats["rooms_with_ventilation"] > 0),
                ("fan control identifier documented", stats["fan_controls"] > 0),
                (
                    "heat/moisture recovery type documented",
                    stats["heat_recovery_types"] > 0,
                ),
                ("humidifier type/control documented", stats["humidifier_controls"] > 0),
                ("official test 5 variant/evaluation attached", False),
            ],
            "test_6": [
                ("ventilation systems extracted", stats["rooms_with_ventilation"] > 0),
                (
                    "constant airflow/stage data documented",
                    stats["ventilation_stages"] > 0,
                ),
                ("heat recovery data documented", stats["heat_recovery_types"] > 0),
                ("restaurant/kitchen overflow represented", stats["overflow_paths"] > 0),
                ("official test 6 evaluation file attached", False),
            ],
            "test_7": [
                ("HVAC systems extracted", stats["rooms_with_hvac"] > 0),
                (
                    "heating and cooling demand outputs available",
                    (
                        stats["dynamic_heating_rows"] > 0
                        and stats["dynamic_cooling_rows"] > 0
                    )
                    or (
                        stats["heating_demand_available"]
                        and stats["cooling_demand_available"]
                    ),
                ),
                (
                    "final energy by system/carrier available",
                    stats["final_energy_available"],
                ),
                (
                    "pump/fan/auxiliary energy available",
                    stats["dynamic_auxiliary_energy_rows"] > 0
                    or stats["auxiliary_energy_available"],
                ),
                (
                    "emission/distribution/storage/generation chain documented",
                    stats["storage_generation_data"] > 0,
                ),
                ("official test 7 loads/evaluation attached", False),
            ],
        }

        rows = []
        for test_name, requirement in SIA4010_TEST_READINESS_REQUIREMENTS.items():
            checks = checks_by_test.get(test_name, [])
            present = [label for label, ok in checks if ok]
            missing = [label for label, ok in checks if not ok]
            readiness_ratio = len(present) / len(checks) if checks else 0.0
            if readiness_ratio >= 0.85:
                ve_status = "READY"
            elif readiness_ratio > 0:
                ve_status = "PARTIAL"
            else:
                ve_status = "MISSING"

            test_status = tests.get(test_name, {}).get("status") or "NOT_CHECKABLE"
            official_status = (
                test_status
                if test_status
                in {
                    "PASS",
                    "VALIDATED",
                    "OFFICIAL_RESULTS_RECORDED",
                    "FAIL",
                    "WARNING",
                    "EVIDENCE_INCOMPLETE",
                    "READY_FOR_OFFICIAL_REVIEW",
                }
                else "NOT_CHECKABLE"
            )
            rows.append(
                {
                    "test": test_name,
                    "classes": self._classes_for_sia4010_test(test_name),
                    "domain": requirement.get(
                        "domain", tests.get(test_name, {}).get("description", "")
                    ),
                    "readiness_ratio": readiness_ratio,
                    "ve_status": ve_status,
                    "official_status": official_status,
                    "present": self._compact_join(
                        present, empty="No key data currently evidenced"
                    ),
                    "missing": self._compact_join(
                        missing, empty="No blocker detected in the current matrix"
                    ),
                    "official_evidence": required_evidence,
                    "source": requirement.get("source", ""),
                    "next_action": requirement.get("next_action", ""),
                }
            )
        return rows

    @staticmethod
    def _build_sia4010_model_stats(
        rooms_data: List[Any], sia4010_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Summarize currently extracted VE data relevant to SIA 4010 readiness."""
        surfaces = [
            surface for room in rooms_data for surface in getattr(room, "surfaces", [])
        ]
        openings = [
            opening for room in rooms_data for opening in getattr(room, "openings", [])
        ]
        external_surfaces = [
            surface for surface in surfaces if getattr(surface, "is_external", False)
        ]
        external_openings = [
            opening for opening in openings if getattr(opening, "is_external", False)
        ]
        external_windows = [
            opening
            for opening in external_openings
            if str(getattr(opening, "opening_type", "") or "").lower()
            in {"window", "glazing", "ext_glazing", "4"}
        ]
        rooms_with_lighting = [
            room
            for room in rooms_data
            if (getattr(room, "internal_gains", {}) or {}).get("lighting") is not None
        ]
        rooms_with_equipment = [
            room
            for room in rooms_data
            if (getattr(room, "internal_gains", {}) or {}).get("equipment") is not None
        ]
        rooms_with_ventilation = [
            room
            for room in rooms_data
            if getattr(room, "ventilation_rate", None) is not None
        ]
        rooms_with_infiltration = [
            room
            for room in rooms_data
            if getattr(room, "infiltration_rate", None) is not None
        ]
        rooms_with_infiltration_m3_h_m2 = [
            room
            for room in rooms_data
            if getattr(room, "infiltration_m3_h_m2", None) is not None
        ]
        rooms_with_hvac = [
            room for room in rooms_data if getattr(room, "hvac_systems", None)
        ]
        hvac_systems = [
            system
            for room in rooms_with_hvac
            for system in (getattr(room, "hvac_systems", []) or [])
            if isinstance(system, dict)
        ]
        rooms_with_daily_profile_hours = [
            room
            for room in rooms_data
            if getattr(room, "internal_gains_wh_m2_day", None) is not None
        ]
        rooms_with_ventilation_control = [
            room
            for room in rooms_with_ventilation
            if getattr(room, "ventilation_installation_type", None)
            and getattr(room, "ventilation_control_level", None) is not None
        ]
        rooms_with_ahu_identifiers = [
            room
            for room in rooms_with_hvac
            if getattr(room, "fan_control", None)
            or getattr(room, "heat_recovery_type", None)
            or getattr(room, "ventilation_control", None)
        ]
        cooling_systems_with_efficiency = [
            system
            for system in hvac_systems
            if system.get("cooling_generator_class")
            and system.get("cooling_capacity_kw") is not None
            and (system.get("nominal_eer") is not None or system.get("seer") is not None)
        ]
        heating_systems_with_efficiency = [
            system
            for system in hvac_systems
            if system.get("heating_generator_class")
            and system.get("heating_capacity_kw") is not None
            and system.get("scop") is not None
        ]
        # SCOP is a heat-pump seasonal index (SIA 380/2). A heat pump is present
        # when the generator classifier resolved a heat-pump class. A sized
        # heating generator that VE did NOT classify as a heat pump is a
        # non-heat-pump source (e.g. a boiler): SCOP does not apply to it, so the
        # SCOP criterion is NON_APPLICABLE rather than NOT_CHECKABLE.
        heat_pump_heating_systems = [
            system for system in hvac_systems if system.get("heating_generator_class")
        ]
        non_heat_pump_heating_systems = [
            system
            for system in hvac_systems
            if not system.get("heating_generator_class")
            and system.get("heating_capacity_kw") is not None
        ]
        daylight_control_evidence = [
            room
            for room in rooms_data
            if getattr(room, "daylight_dimming_profile", "")
            or getattr(room, "lighting_control_type", "")
        ]
        lighting_control_mappings = [
            room for room in rooms_data if getattr(room, "lighting_control_type", "")
        ]
        fan_controls = [system for system in hvac_systems if system.get("fan_control")]
        heat_recovery_types = [
            room
            for room in rooms_data
            if getattr(room, "heat_recovery_type", None)
            or any(
                system.get("heat_recovery_type")
                for system in (getattr(room, "hvac_systems", []) or [])
                if isinstance(system, dict)
            )
        ]
        humidifier_controls = [
            system
            for system in hvac_systems
            if system.get("humidifier_control") or system.get("humidifier_type")
        ]
        ventilation_stages = [
            room
            for room in rooms_data
            if getattr(room, "ventilation_control_level", None) is not None
        ]
        overflow_paths = [
            system for system in hvac_systems if system.get("overflow_paths")
        ]
        storage_generation_data = [
            system for system in hvac_systems if system.get("storage_generation_data")
        ]
        energy = sia4010_results.get("energy", {}) or {}
        dynamic_results = sia4010_results.get("dynamic_results", {}) or {}
        dynamic_room_rows = dynamic_results.get("rooms", []) or []
        dynamic_demand_rows = [
            row
            for row in dynamic_room_rows
            if row.get("heating_kwh") is not None or row.get("cooling_kwh") is not None
        ]
        dynamic_heating_rows = [
            row for row in dynamic_room_rows if row.get("heating_kwh") is not None
        ]
        dynamic_cooling_rows = [
            row for row in dynamic_room_rows if row.get("cooling_kwh") is not None
        ]
        dynamic_temperature_rows = [
            row
            for row in dynamic_room_rows
            if row.get("occupied_hours_above_26") is not None
            or row.get("occupied_hours_above_27") is not None
        ]
        dynamic_annual_comfort_rows = [
            row
            for row in dynamic_room_rows
            if row.get("annual_comfort_period_complete") is True
            and row.get("occupied_hours_above_sia180_upper") is not None
            and row.get("occupied_hours_below_sia180_lower") is not None
        ]
        dynamic_lighting_rows = [
            row for row in dynamic_room_rows if row.get("lighting_kwh") is not None
        ]
        dynamic_fan_rows = [
            row for row in dynamic_room_rows if row.get("fan_kwh") is not None
        ]
        dynamic_pump_rows = [
            row for row in dynamic_room_rows if row.get("pump_kwh") is not None
        ]
        dynamic_auxiliary_rows = [
            row for row in dynamic_room_rows if row.get("auxiliary_kwh") is not None
        ]
        dynamic_coil_rows = [
            row
            for row in dynamic_room_rows
            if row.get("coil_heating_kwh") is not None
            or row.get("coil_cooling_kwh") is not None
        ]
        dynamic_co2_rows = [
            row
            for row in dynamic_room_rows
            if row.get("peak_co2_ppm") is not None
            or row.get("average_co2_ppm") is not None
        ]
        dynamic_humidity_rows = [
            row
            for row in dynamic_room_rows
            if row.get("peak_relative_humidity_percent") is not None
            or row.get("average_relative_humidity_percent") is not None
        ]
        g_total_not_required_for_g_limit = 0
        for opening in external_windows:
            try:
                g_value = float(getattr(opening, "solar_factor", None))
            except (TypeError, ValueError):
                continue
            if g_value <= SIA3802_LIMIT_VALUES["glazing_g_value"]:
                g_total_not_required_for_g_limit += 1
        return {
            "rooms": len(rooms_data),
            "rooms_with_use_category": sum(
                1
                for room in rooms_data
                if str(getattr(room, "sia2024_category", "") or "").strip()
            ),
            "external_surfaces": len(external_surfaces),
            "surface_u_values": sum(
                1
                for surface in external_surfaces
                if getattr(surface, "u_value", None) is not None
            ),
            "surface_tilt_values": sum(
                1
                for surface in external_surfaces
                if getattr(surface, "tilt", None) is not None
            ),
            "surface_adjacency_values": sum(
                1
                for surface in external_surfaces
                if getattr(surface, "adjacency_room_ids", None)
            ),
            "external_openings": len(external_openings),
            "external_windows": len(external_windows),
            "window_u_values": sum(
                1
                for opening in external_windows
                if getattr(opening, "u_value", None) is not None
            ),
            "window_g_values": sum(
                1
                for opening in external_windows
                if getattr(opening, "solar_factor", None) is not None
            ),
            "en410_g_values": sum(
                1
                for opening in external_windows
                if getattr(opening, "g_value_bs_en_410", None) is not None
            ),
            "raw_cdb_g_values": sum(
                1
                for opening in external_windows
                if getattr(opening, "cdb_g_value", None) is not None
            ),
            "visible_transmittance_values": sum(
                1
                for opening in external_windows
                if getattr(opening, "visible_transmittance", None) is not None
            ),
            "frame_fraction_values": sum(
                1
                for opening in external_windows
                if getattr(opening, "frame_fraction", None) is not None
            ),
            "solar_protection_types": sum(
                1
                for opening in external_windows
                if has_active_solar_protection(opening)
                and getattr(opening, "shading_type", None)
            ),
            "solar_protection_controls": sum(
                1
                for opening in external_windows
                if has_active_solar_protection(opening)
                and getattr(opening, "shading_control", None)
            ),
            "g_total_values": sum(
                1
                for opening in external_windows
                if getattr(opening, "g_total", None) is not None
            ),
            "g_total_not_required_for_g_limit": g_total_not_required_for_g_limit,
            "rooms_with_lighting": len(rooms_with_lighting),
            "rooms_with_equipment": len(rooms_with_equipment),
            "rooms_with_ventilation": len(rooms_with_ventilation),
            "rooms_with_infiltration": len(rooms_with_infiltration),
            "rooms_with_infiltration_m3_h_m2": len(rooms_with_infiltration_m3_h_m2),
            "rooms_with_hvac": len(rooms_with_hvac),
            "rooms_with_daily_profile_hours": len(rooms_with_daily_profile_hours),
            "rooms_with_ventilation_control": len(rooms_with_ventilation_control),
            "rooms_with_ahu_identifiers": len(rooms_with_ahu_identifiers),
            "cooling_systems_with_efficiency": len(cooling_systems_with_efficiency),
            "heating_systems_with_efficiency": len(heating_systems_with_efficiency),
            "heat_pump_heating_systems": len(heat_pump_heating_systems),
            "non_heat_pump_heating_systems": len(non_heat_pump_heating_systems),
            "daylight_control_evidence": len(daylight_control_evidence),
            "lighting_control_mappings": len(lighting_control_mappings),
            "fan_controls": len(fan_controls),
            "heat_recovery_types": len(heat_recovery_types),
            "humidifier_controls": len(humidifier_controls),
            "ventilation_stages": len(ventilation_stages),
            "overflow_paths": len(overflow_paths),
            "storage_generation_data": len(storage_generation_data),
            "dynamic_room_rows": len(dynamic_room_rows),
            "dynamic_demand_rows": len(dynamic_demand_rows),
            "dynamic_heating_rows": len(dynamic_heating_rows),
            "dynamic_cooling_rows": len(dynamic_cooling_rows),
            "dynamic_temperature_rows": len(dynamic_temperature_rows),
            "dynamic_annual_comfort_rows": len(dynamic_annual_comfort_rows),
            "dynamic_lighting_rows": len(dynamic_lighting_rows),
            "dynamic_fan_rows": len(dynamic_fan_rows),
            "dynamic_pump_rows": len(dynamic_pump_rows),
            "dynamic_auxiliary_rows": len(dynamic_auxiliary_rows),
            "dynamic_auxiliary_energy_rows": max(
                len(dynamic_fan_rows), len(dynamic_pump_rows), len(dynamic_auxiliary_rows)
            ),
            "dynamic_coil_rows": len(dynamic_coil_rows),
            "dynamic_co2_rows": len(dynamic_co2_rows),
            "dynamic_humidity_rows": len(dynamic_humidity_rows),
            "heating_demand_available": energy.get("heating_demand") is not None,
            "cooling_demand_available": energy.get("cooling_demand") is not None,
            "lighting_energy_available": energy.get("lighting_energy") is not None,
            "auxiliary_energy_available": any(
                energy.get(key) is not None
                for key in ("fan_energy", "pump_energy", "auxiliary_energy")
            ),
            "final_energy_available": any(
                energy.get(key) is not None
                for key in ("primary_energy", "co2_emissions", "renewable_energy_share")
            )
            or any(system.get("final_energy") is not None for system in hvac_systems),
        }

    def _classes_for_sia4010_test(self, test_name: str) -> str:
        """Return validation classes concerned by a test, including SIA sub-variants."""
        aliases = {
            "test_2": ["test_2", "test_2A"],
            "test_3": ["test_3", "test_3A_to_3F"],
        }.get(test_name, [test_name])
        classes = []
        for alias in aliases:
            classes.extend(SIA4010_TEST_CLASS_COVERAGE.get(alias, []))
        unique_classes = []
        for class_name in classes:
            if class_name not in unique_classes:
                unique_classes.append(class_name)
        return ", ".join(unique_classes) if unique_classes else "To be confirmed"

    @staticmethod
    def _required_sia4010_aliases_for_class(class_name: str) -> List[str]:
        """Return SIA 4010 test aliases required by one validation class."""
        return [
            alias
            for alias in SIA4010_TEST_ALIAS_ORDER
            if class_name in SIA4010_TEST_CLASS_COVERAGE.get(alias, [])
        ]

    @staticmethod
    def _compact_join(items: List[str], empty: str = "", max_chars: int = 260) -> str:
        """Join text fragments and truncate them for readable report cells."""
        text = "; ".join(str(item) for item in items if item)
        if not text:
            return empty
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3].rstrip() + "..."

    @staticmethod
    def _sia4010_status_format(
        status: str,
        ready_format: Any,
        partial_format: Any,
        missing_format: Any,
        not_checkable_format: Any,
        cell_format: Any,
    ) -> Any:
        """Return the Excel cell format for SIA 4010 readiness statuses."""
        status_upper = str(status or "").upper()
        if status_upper in {"READY", "PASS", "VALIDATED", "PRESENT"}:
            return ready_format
        if status_upper in {
            "PARTIAL",
            "WARNING",
            "READY_FOR_OFFICIAL_REVIEW",
            "OFFICIAL_RESULTS_RECORDED",
            "OFFICIAL_RESULT_RECORDED",
        }:
            return partial_format
        if status_upper in {"NOT_REQUESTED", "CLASS_NOT_SELECTED"}:
            return not_checkable_format
        if status_upper in {"NOT_CHECKABLE"}:
            return not_checkable_format
        if status_upper in {"MISSING", "FAIL", "EVIDENCE_INCOMPLETE"}:
            return missing_format
        return cell_format

    @staticmethod
    def _sia4010_prevalidation_status_format(
        status: str,
        pass_format: Any,
        partial_format: Any,
        fail_format: Any,
        missing_format: Any,
        cell_format: Any,
    ) -> Any:
        """Return a color format for PDF-based prevalidation statuses."""
        status_upper = str(status or "").upper()
        if status_upper == "PDF_PRECHECK_PASS":
            return pass_format
        if status_upper == "PDF_PRECHECK_PARTIAL":
            return partial_format
        if status_upper == "PDF_PRECHECK_FAIL":
            return fail_format
        if status_upper in {
            "MISSING_VE_DATA",
            "NEEDS_SIA_EXECUTION_PACKAGE",
            "OFFICIAL_VALIDATION_REQUIRED",
        }:
            return missing_format
        return cell_format

    @staticmethod
    def _has_sia4010_evidence(evidence: Dict[str, Any], evidence_item: str) -> bool:
        """Return true only when an official evidence family has detected files."""
        if not isinstance(evidence, dict) or not evidence:
            return False

        structured_key = ExcelReportGenerator._evidence_key_for_required_item(
            evidence_item
        )
        structured_value = evidence.get(structured_key)
        if isinstance(structured_value, dict):
            files = structured_value.get("files", []) or []
            return bool(structured_value.get("present") and files)

        exact_value = evidence.get(evidence_item)
        if isinstance(exact_value, dict):
            files = exact_value.get("files", []) or []
            return bool(exact_value.get("present") and files)
        if isinstance(exact_value, bool):
            return False

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
                if isinstance(value, (list, tuple)):
                    return bool(value)
                return False
        return False

    @staticmethod
    def _evidence_key_for_required_item(evidence_item: str) -> str:
        """Map a required SIA 4010 evidence label to the scan payload key."""
        item = str(evidence_item or "")
        known = {
            SIA4010_REQUIRED_EVIDENCE[0]: "official_test_specifications",
            SIA4010_REQUIRED_EVIDENCE[1]: "official_evaluation_workbooks",
            SIA4010_REQUIRED_EVIDENCE[2]: "candidate_results",
            SIA4010_REQUIRED_EVIDENCE[3]: "reference_comparisons",
            SIA4010_REQUIRED_EVIDENCE[4]: "validation_class_confirmation",
        }
        return known.get(item, item)

    @staticmethod
    def _sia4010_detected_families_for_file(
        evidence: Dict[str, Any], file_data: Dict[str, Any]
    ) -> str:
        """Return evidence family labels that reference a detected file."""
        if not isinstance(evidence, dict) or not isinstance(file_data, dict):
            return ""
        filename = str(file_data.get("name", "") or "")
        families = []
        for key, value in evidence.items():
            if not isinstance(value, dict):
                continue
            for matched_file in value.get("files", []) or []:
                if str(matched_file.get("name", "") or "") == filename:
                    families.append(str(key))
                    break
        return ", ".join(families) if families else "Unclassified"

    def _sia4010_system_status(
        self, family: str, rooms_data: List[Any], sia4010_results: Dict[str, Any]
    ) -> str:
        """Describe current extraction coverage for a SIA 4010 system family."""
        stats = self._build_sia4010_model_stats(rooms_data, sia4010_results)
        if family == "ventilation":
            if stats["rooms_with_ventilation"]:
                return f"PARTIAL: {stats['rooms_with_ventilation']} rooms expose ventilation_rate; detailed AHU SIA 4010 fields still missing."
            return "MISSING: no ventilation_rate / AHU controls extracted yet."
        if family == "cooling":
            if stats["cooling_demand_available"]:
                return "PARTIAL: cooling demand exists; detailed generation/distribution/storage fields still required."
            return "MISSING: no cooling dynamic result, EER/SEER or cooling system breakdown extracted yet."
        if family == "heating":
            if stats["rooms_with_hvac"] or stats["heating_demand_available"]:
                return "PARTIAL: HVAC/heating evidence exists; generator, distribution, storage and auxiliary details still required."
            return "MISSING: no heating demand/generator detail extracted yet."
        if family == "domestic_hot_water":
            return "MISSING: DHW coupling/load cycles are not extracted yet."
        if family == "general_building_electricity":
            if stats["rooms_with_lighting"] or stats["rooms_with_equipment"]:
                return "PARTIAL: lighting/equipment gains are partially extracted; SIA 2056/SIA 387/4 evidence still required."
            return "MISSING: no electricity/lighting evidence extracted yet."
        if family == "photovoltaics":
            return "MISSING: PV modules/orientation/performance are not extracted yet."
        return "TO_CONFIRM"

    @staticmethod
    def _write_dashboard_card(
        worksheet: Any,
        cell_range: str,
        title: str,
        value: str,
        note: str,
        title_format: Any,
        value_format: Any,
        note_format: Any,
    ):
        """Write a compact KPI card in a merged cell range."""
        start, end = cell_range.split(":")
        start_col_letters = "".join(ch for ch in start if ch.isalpha())
        start_row = int("".join(ch for ch in start if ch.isdigit()))
        end_col_letters = "".join(ch for ch in end if ch.isalpha())
        end_row = int("".join(ch for ch in end if ch.isdigit()))
        worksheet.merge_range(
            f"{start_col_letters}{start_row}:{end_col_letters}{start_row}",
            title,
            title_format,
        )
        worksheet.merge_range(
            f"{start_col_letters}{start_row + 1}:{end_col_letters}{start_row + 2}",
            value,
            value_format,
        )
        worksheet.merge_range(
            f"{start_col_letters}{start_row + 3}:{end_col_letters}{end_row}",
            note,
            note_format,
        )

    @staticmethod
    def _dashboard_score_rows(score_result: ScoreResult) -> List[List[Any]]:
        """Return chart-ready dashboard rows for score metrics."""
        rows = [
            ["Automated precheck", float(score_result.compliance_score or 0.0)],
            ["Model health", float(score_result.health_score or 0.0)],
        ]
        for key, value in list(score_result.detailed_scores.items())[:10]:
            if isinstance(value, (int, float)):
                label = (
                    str(key)
                    .replace("SIA3802_", "380/2 ")
                    .replace("SIA3801_", "380/2 ")
                    .replace("SIA4010_", "4010 ")
                    .replace("_", " ")
                    .title()
                )
                rows.append([label[:34], float(value)])
        return rows

    @staticmethod
    def _action_dashboard_sia3802_score_rows(
        score_result: ScoreResult,
    ) -> List[List[Any]]:
        """Return the SIA 380/2 score rows shown on the action dashboard."""
        detailed_scores = score_result.detailed_scores or {}
        return [
            [
                "Overall SIA 380/2",
                float(score_result.compliance_score or 0.0),
                "Weighted automated indicator from model-facing SIA 380/2 checks.",
            ],
            [
                "Envelope",
                float(detailed_scores.get("SIA3802_ENVELOPE", 0.0) or 0.0),
                "Opaque external surfaces, U-values and boundary classification.",
            ],
            [
                "Openings",
                float(detailed_scores.get("SIA3802_OPENINGS", 0.0) or 0.0),
                "Window Uw, g_perp, tau_v, frame fraction and shading evidence.",
            ],
            [
                "Ventilation",
                float(detailed_scores.get("SIA3802_VENTILATION", 0.0) or 0.0),
                "Infiltration, airflow rates and ventilation control evidence.",
            ],
            [
                "Gains",
                float(detailed_scores.get("SIA3802_GAINS", 0.0) or 0.0),
                "Occupancy, lighting, equipment gains and schedules.",
            ],
            [
                "HVAC",
                float(detailed_scores.get("SIA3802_HVAC", 0.0) or 0.0),
                "System type, efficiency evidence and plant readiness.",
            ],
            [
                "Value integrity",
                float(detailed_scores.get("SIA3802_VALUE_INTEGRITY", 0.0) or 0.0),
                "Guards against non-comparable values such as raw CDB g-values.",
            ],
        ]

    @staticmethod
    def _action_dashboard_sia4010_score_rows(
        score_result: ScoreResult,
        sia4010_results: Dict[str, Any],
    ) -> List[List[Any]]:
        """Return the SIA 4010 score rows shown on the action dashboard."""
        detailed_scores = score_result.detailed_scores or {}
        evidence = sia4010_results.get("evidence", {}) or {}
        evidence_summary = (
            evidence.get("summary", {}) if isinstance(evidence, dict) else {}
        )
        tests = sia4010_results.get("tests", {}) or {}
        rows = [
            [
                "Official validation",
                float(sia4010_results.get("score", 0.0) or 0.0),
                "Reserved for explicit official PASS/VALIDATED rows and accepted evidence.",
            ],
            [
                "Evidence readiness",
                float(sia4010_results.get("readiness_score", 0.0) or 0.0),
                f"{evidence_summary.get('status', 'UNKNOWN')} - {evidence_summary.get('present_count', 0)}/{evidence_summary.get('required_count', len(SIA4010_REQUIRED_EVIDENCE))} evidence families.",
            ],
        ]
        for index in range(1, 8):
            test_key = f"test_{index}"
            test_data = tests.get(test_key, {}) or {}
            rows.append(
                [
                    f"Test {index}",
                    float(
                        detailed_scores.get(f"SIA4010_TEST_{index}", 0.0)
                        or test_data.get("score", 0.0)
                        or 0.0
                    ),
                    str(
                        test_data.get("status")
                        or test_data.get("official_status")
                        or "NOT_CHECKABLE"
                    ),
                ]
            )
        return rows

    def _action_dashboard_values_for_group(
        self,
        group: Dict[str, Any],
        sia4010_results: Dict[str, Any],
    ) -> tuple:
        """Return current, limit and gap values for one action-dashboard row."""
        rule = str(group.get("rule", "") or "").upper()
        current_value = self._p1_current_value_for_group(group)
        limit_value = self._p1_limit_for_group(group)
        if "SIA4010" in rule:
            evidence = sia4010_results.get("evidence", {}) or {}
            current_value = float(
                sum(
                    1
                    for item in SIA4010_REQUIRED_EVIDENCE
                    if self._has_sia4010_evidence(evidence, item)
                )
            )
            limit_value = float(len(SIA4010_REQUIRED_EVIDENCE))
        gap_value = self._p1_gap_for_values(rule, current_value, limit_value)
        return current_value, limit_value, gap_value

    def _action_item_score_for_group(
        self,
        group: Dict[str, Any],
        sia4010_results: Dict[str, Any],
    ) -> float:
        """Return a 0-100 closure score for one action item."""
        rule = str(group.get("rule", "") or "").upper()
        current_value, limit_value, _gap_value = self._action_dashboard_values_for_group(
            group, sia4010_results
        )

        if "SIA4010" in rule:
            if not limit_value:
                return 0.0
            return max(
                0.0,
                min(100.0, (float(current_value or 0.0) / float(limit_value)) * 100.0),
            )

        if "MISSING" in rule or "NOT_CHECKABLE" in rule:
            return 0.0

        if current_value is not None and limit_value is not None:
            current = float(current_value)
            limit = float(limit_value)
            if current <= limit:
                return 100.0
            if current > 0:
                return max(0.0, min(99.0, (limit / current) * 100.0))

        fallback_by_severity = {
            "Critical": 0.0,
            "High": 25.0,
            "Medium": 55.0,
            "Low": 75.0,
        }
        return fallback_by_severity.get(str(group.get("max_severity", "")), 50.0)

    @staticmethod
    def _standard_for_alert_group(group: Dict[str, Any]) -> str:
        """Return the standard family affected by an action group."""
        rule = str(group.get("rule", "") or "").upper()
        category = str(group.get("category", "") or "").upper()
        if "SIA4010" in rule or "SIA4010" in category:
            return "SIA 4010"
        if "SIA3802" in rule or "SIA3801" in rule:
            return "SIA 380/2"
        return "Model data"

    @staticmethod
    def _detail_sheet_for_alert_group(group: Dict[str, Any]) -> str:
        """Return the best workbook sheet for detailed evidence behind an action row."""
        rule = str(group.get("rule", "") or "").upper()
        if "SIA4010" in rule:
            return "SIA4010 READINESS"
        if "SOLAR_FACTOR" in rule or "G_TOTAL" in rule:
            return "FACADE GLAZING REVIEW"
        if "FRAME_FRACTION" in rule:
            return "FRAME FRACTION AUDIT"
        if "U_VALUE" in rule or "OPAQUE" in rule:
            return "ENVELOPE U REVIEW"
        if any(
            token in rule
            for token in ("VENTILATION", "INFILTRATION", "LIGHTING", "EQUIPMENT", "HVAC")
        ):
            return "INPUT REQUEST"
        if "MISSING" in rule or "NOT_CHECKABLE" in rule:
            return "DATA QUALITY"
        return "ALERT SUMMARY"

    @staticmethod
    def _action_status_format(
        item_score: float, ok_format: Any, warn_format: Any, fail_format: Any
    ) -> Any:
        """Return a visual status format for one action row."""
        if item_score >= 100.0:
            return ok_format
        if item_score >= 50.0:
            return warn_format
        return fail_format

    def _action_dashboard_next_step(
        self,
        alert_groups: List[Dict[str, Any]],
        evidence_summary: Dict[str, Any],
        dynamic_results: Dict[str, Any],
    ) -> str:
        """Return the strongest next-step sentence for the action dashboard."""
        model_groups = [
            group
            for group in alert_groups
            if self._standard_for_alert_group(group) != "SIA 4010"
        ]
        if model_groups:
            group = model_groups[0]
            return (
                f"Next VE model action: {self._action_for_alert_group(group)} "
                f"Scope: {group.get('construction', 'model')}; rule: {group.get('rule', '')}; "
                f"owner: {self._p1_owner_for_group(group)}."
            )

        if evidence_summary.get("status") != "READY_FOR_OFFICIAL_REVIEW":
            return (
                "Next compliance action: complete the SIA 4010 evidence pack and class/test manifests. "
                f"Current official evidence: {evidence_summary.get('present_count', 0)}/"
                f"{evidence_summary.get('required_count', len(SIA4010_REQUIRED_EVIDENCE))} families."
            )

        dynamic_status = str(
            dynamic_results.get("status", "UNKNOWN")
            if isinstance(dynamic_results, dict)
            else "UNKNOWN"
        )
        return (
            "Next review action: submit the complete SIA 4010 package for responsible reviewer/sub-commission acceptance. "
            f"APS/Vista dynamic result status: {dynamic_status}."
        )

    def _dashboard_requirement_status_rows(
        self, sia3802_results: Dict[str, Any], sia4010_results: Dict[str, Any]
    ) -> List[List[Any]]:
        """Return chart-ready dashboard rows for requirement-matrix statuses."""
        all_alerts = list(sia3802_results.get("alerts", []) or []) + list(
            sia4010_results.get("alerts", []) or []
        )
        rule_evaluations = sia3802_results.get("rule_evaluations", {}) or {}
        rows = [
            self._build_requirement_matrix_row(requirement, all_alerts, rule_evaluations)
            for requirement in SIA_COMPLIANCE_REQUIREMENT_MATRIX
        ]
        counts = Counter(row["status"] for row in rows)
        order = [
            "PASS",
            "PARTIAL_CHECK",
            "REFERENCE_DIAGNOSTIC",
            "REFERENCE_DEVIATION",
            "READINESS_ONLY",
            "FAIL",
            "MISSING",
            "NOT_CHECKABLE",
            "NOT_IMPLEMENTED",
        ]
        return [
            [status, counts.get(status, 0)] for status in order if counts.get(status, 0)
        ]

    @staticmethod
    def _count_blocked_sia4010_tests(sia4010_results: Dict[str, Any]) -> int:
        """Count SIA 4010 tests that still cannot support an official claim."""
        blocked_statuses = {"NOT_CHECKABLE", "EVIDENCE_INCOMPLETE"}
        return sum(
            1
            for test in sia4010_results.get("tests", {}).values()
            if str(test.get("status", "") or "").upper() in blocked_statuses
        )

    def _dashboard_verdict(
        self,
        score_result: ScoreResult,
        sia4010_results: Dict[str, Any],
        rooms_data: List[Any],
        include_sia4010: bool = True,
        sia3802_results: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Return the executive dashboard verdict from scores and blockers.

        When include_sia4010 is False the verdict is SIA 380/2-only: the SIA
        4010 validation-evidence branches are not reachable, so a client 380/2
        report never states a fact about the software's validation.
        """
        if not include_sia4010 and sia3802_results is not None:
            verdict = build_compliance_verdict(
                sia3802_results, sia4010_results, len(rooms_data)
            )
            status_key = {
                "COMPLIANT": "verdict_compliant",
                "NOT_COMPLIANT": "verdict_not_compliant",
            }.get(verdict.sia3802_status, "verdict_not_determined")
            return "{}: {}".format(
                self._tr(status_key),
                self._tr("report_reason_" + verdict.sia3802_reason),
            )

        critical_count = sum(
            1 for alert in score_result.alerts if alert.severity == Severity.CRITICAL
        )
        high_count = sum(
            1 for alert in score_result.alerts if alert.severity == Severity.HIGH
        )
        blocked_tests = (
            self._count_blocked_sia4010_tests(sia4010_results) if include_sia4010 else 0
        )
        if not rooms_data:
            return (
                "BLOCKER: no VE thermal room was extracted. The model cannot be assessed yet. "
                "Open the correct VE project/model and rerun the script from the VE Run button."
            )
        if critical_count or high_count:
            return (
                f"NOT READY FOR CLIENT COMPLIANCE CLAIM: {critical_count} critical and {high_count} high alerts require action. "
                "The workbook is suitable as a professional readiness report, not as a final SIA compliance certificate."
            )
        if blocked_tests:
            return (
                f"READINESS ONLY: SIA 380/2 direct checks can be reviewed, but {blocked_tests} SIA 4010 validation tests remain blocked "
                "until official SIA evidence files, reference comparisons and reviewer acceptance are complete."
            )
        if not include_sia4010:
            return "READY FOR DETAILED REVIEW: no critical or high alert detected on the SIA 380/2 checks of this model."
        return "READY FOR DETAILED REVIEW: no critical/high alert detected and SIA 4010 tests are no longer blocked by missing evidence."

    def _build_requirement_matrix_row(
        self,
        requirement: Dict[str, Any],
        alerts: List[Alert],
        rule_evaluations: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """Build a report row for one SIA requirement without inventing verdicts."""
        automation = str(requirement.get("automation", "") or "")
        implemented_rule = str(requirement.get("implemented_rule", "") or "")
        related_alerts = self._find_requirement_alerts(requirement, alerts)
        rule_names = self._implemented_rule_names(implemented_rule)
        evaluated_count = sum(
            int((rule_evaluations or {}).get(rule_name, 0) or 0)
            for rule_name in rule_names
        )

        if automation in {"NOT_IMPLEMENTED", ""}:
            status = "NOT_IMPLEMENTED"
        elif automation == "REFERENCE_DIAGNOSTIC":
            status = "REFERENCE_DEVIATION" if related_alerts else "REFERENCE_DIAGNOSTIC"
        elif automation == "READINESS_ONLY":
            status = "NOT_CHECKABLE" if related_alerts else "READINESS_ONLY"
        elif related_alerts:
            if any(
                "MISSING" in str(alert.rule or "").upper() for alert in related_alerts
            ):
                status = "MISSING"
            elif any(
                "NOT_CHECKABLE" in str(alert.rule or "").upper()
                for alert in related_alerts
            ):
                status = "NOT_CHECKABLE"
            else:
                status = "FAIL"
        elif automation == "AUTOMATED" and evaluated_count <= 0:
            status = "NOT_CHECKABLE"
        elif automation == "PARTIAL":
            status = "PARTIAL_CHECK"
        elif implemented_rule:
            status = "PASS"
        else:
            status = "NOT_CHECKABLE"

        blockers = [str(alert.description or "") for alert in related_alerts[:3]]
        next_action = str(requirement.get("next_action", "") or "")
        if blockers:
            next_action = next_action + " | Current blockers: " + " ; ".join(blockers)

        return {
            "status": status,
            "automation": automation,
            "mvp_status": requirement.get("mvp_status", ""),
            "standard": requirement.get("standard", ""),
            "domain": requirement.get("domain", ""),
            "id": requirement.get("id", ""),
            "evaluated_count": evaluated_count,
            "criterion": requirement.get("criterion", ""),
            "limit": requirement.get("limit", ""),
            "unit": requirement.get("unit", ""),
            "target": requirement.get("target", ""),
            "source": requirement.get("source", ""),
            "next_action": next_action,
        }

    @staticmethod
    def _find_requirement_alerts(
        requirement: Dict[str, Any], alerts: List[Alert]
    ) -> List[Alert]:
        """Return alerts that map to one requirement-matrix row."""
        rule_name = str(requirement.get("implemented_rule", "") or "").upper()
        rule_names = set(ExcelReportGenerator._implemented_rule_names(rule_name))
        requirement_id = str(requirement.get("id", "") or "").upper()
        if not rule_name and not requirement_id:
            return []

        matches = []
        for alert in alerts:
            alert_rule = str(alert.rule or "").upper()
            if rule_names and alert_rule in rule_names:
                matches.append(alert)
                continue
            if requirement_id.startswith(
                "SIA3802_AIRTIGHTNESS"
            ) and alert_rule.startswith("SIA3802_INFILTRATION"):
                matches.append(alert)
                continue
            if requirement_id.startswith("SIA4010") and alert_rule.startswith("SIA4010"):
                matches.append(alert)
        return matches

    @staticmethod
    def _implemented_rule_names(value: str) -> List[str]:
        """Split a requirement rule field into exact registered rule names."""
        return [
            token.strip().upper()
            for token in str(value or "").split("/")
            if token.strip()
        ]

    @staticmethod
    def _requirement_status_format(
        status: str,
        pass_format: Any,
        fail_format: Any,
        partial_format: Any,
        not_checkable_format: Any,
        cell_format: Any,
    ) -> Any:
        """Return the Excel cell format for a requirement-matrix status."""
        status_upper = str(status or "").upper()
        if status_upper in {"PASS"}:
            return pass_format
        if status_upper in {
            "PARTIAL_CHECK",
            "REFERENCE_DIAGNOSTIC",
            "REFERENCE_DEVIATION",
            "READINESS_ONLY",
        }:
            return partial_format
        if status_upper in {"NOT_CHECKABLE", "NOT_IMPLEMENTED"}:
            return not_checkable_format
        if status_upper in {"FAIL", "MISSING"}:
            return fail_format
        return cell_format

    def _build_facade_glazing_rows(
        self,
        alert_groups: List[Dict[str, Any]],
        rooms_data: List[Any],
    ) -> List[Dict[str, Any]]:
        """Aggregate external window data by construction for facade decisions."""
        del alert_groups  # The row is intentionally based on actual openings, not alert duplication.
        grouped: Dict[str, Dict[str, Any]] = {}
        for room in rooms_data:
            room_name = str(getattr(room, "name", "") or getattr(room, "id", "") or "")
            for opening in getattr(room, "openings", []) or []:
                if not getattr(opening, "is_external", False):
                    continue
                opening_type = str(getattr(opening, "opening_type", "") or "").lower()
                if (
                    opening_type
                    and "window" not in opening_type
                    and "glaz" not in opening_type
                ):
                    continue

                construction = str(
                    getattr(opening, "construction_id", "") or "NO_CONSTRUCTION"
                )
                area = self._safe_float(getattr(opening, "area", 0.0), 0.0) or 0.0
                u_value = self._safe_float(getattr(opening, "u_value", None), None)
                g_value = self._safe_float(getattr(opening, "solar_factor", None), None)
                visible_transmittance = self._safe_float(
                    getattr(opening, "visible_transmittance", None), None
                )
                frame_fraction = self._safe_float(
                    getattr(opening, "frame_fraction", None), None
                )
                shading_type = getattr(opening, "shading_type", None)
                shading_control = getattr(opening, "shading_control", None)
                g_total = self._safe_float(getattr(opening, "g_total", None), None)
                active_solar_protection = has_active_solar_protection(opening)

                row = grouped.setdefault(
                    construction,
                    {
                        "construction": construction,
                        "window_count": 0,
                        "area": 0.0,
                        "u_weighted": 0.0,
                        "u_area": 0.0,
                        "g_weighted": 0.0,
                        "g_area": 0.0,
                        "max_g": None,
                        "rooms": set(),
                        "missing_visible_transmittance": 0,
                        "missing_frame_fraction": 0,
                        "missing_shading_type": 0,
                        "missing_shading_control": 0,
                        "active_solar_protection": 0,
                        "g_total_required": 0,
                        "missing_g_total": 0,
                        "missing_u": 0,
                        "missing_g": 0,
                        "fail_u": 0,
                        "fail_g": 0,
                    },
                )
                row["window_count"] += 1
                row["area"] += area
                g_total_required_for_limit = False
                if room_name:
                    row["rooms"].add(room_name)
                if u_value is None:
                    row["missing_u"] += 1
                else:
                    weight = area if area > 0 else 1.0
                    row["u_weighted"] += u_value * weight
                    row["u_area"] += weight
                    if u_value > SIA3802_LIMIT_VALUES["window_u"]:
                        row["fail_u"] += 1
                if g_value is None:
                    row["missing_g"] += 1
                else:
                    weight = area if area > 0 else 1.0
                    row["g_weighted"] += g_value * weight
                    row["g_area"] += weight
                    row["max_g"] = (
                        g_value if row["max_g"] is None else max(row["max_g"], g_value)
                    )
                    if g_value > SIA3802_LIMIT_VALUES["glazing_g_value"]:
                        row["fail_g"] += 1
                        g_total_required_for_limit = active_solar_protection
                if visible_transmittance is None:
                    row["missing_visible_transmittance"] += 1
                if frame_fraction is None:
                    row["missing_frame_fraction"] += 1
                if active_solar_protection:
                    row["active_solar_protection"] += 1
                    if not shading_type:
                        row["missing_shading_type"] += 1
                    if not shading_control:
                        row["missing_shading_control"] += 1
                if g_total_required_for_limit:
                    row["g_total_required"] += 1
                    if g_total is None:
                        row["missing_g_total"] += 1

        rows: List[Dict[str, Any]] = []
        for item in grouped.values():
            avg_u = item["u_weighted"] / item["u_area"] if item["u_area"] else None
            avg_g = item["g_weighted"] / item["g_area"] if item["g_area"] else None
            max_g = item["max_g"]
            g_gap = (
                max_g - SIA3802_LIMIT_VALUES["glazing_g_value"]
                if max_g is not None
                else None
            )
            uw_status = (
                "MISSING"
                if item["missing_u"]
                else ("REFERENCE_DEVIATION" if item["fail_u"] else "REFERENCE_MATCH")
            )
            g_status = (
                "MISSING"
                if item["missing_g"]
                else ("REFERENCE_DEVIATION" if item["fail_g"] else "REFERENCE_MATCH")
            )
            missing_evidence_items = []
            if item["missing_visible_transmittance"]:
                missing_evidence_items.append("tau_v visible transmittance")
            if item["missing_frame_fraction"]:
                missing_evidence_items.append("frame fraction")
            if item["missing_shading_type"]:
                missing_evidence_items.append("solar protection type")
            if item["missing_shading_control"]:
                missing_evidence_items.append("solar protection control")
            if item["missing_g_total"]:
                missing_evidence_items.append(
                    "active g_total with shading for glazing above the table 2 reference input"
                )

            if missing_evidence_items or g_status == "MISSING" or uw_status == "MISSING":
                status = "MISSING_EVIDENCE"
            elif "REFERENCE_DEVIATION" in {g_status, uw_status}:
                status = "REFERENCE_DEVIATION"
            else:
                status = "REFERENCE_MATCH"

            evidence_items = [
                "CDB glazing export",
                "EN 410 g_perp or SHGC mapping note",
                "visible transmittance tau_v",
                "frame/glass split",
            ]
            if item["active_solar_protection"]:
                evidence_items.append(
                    "shading device type, optical properties and control thresholds"
                )
            else:
                evidence_items.append(
                    "confirmation that no active solar-protection device is modelled"
                )
            if item["g_total_required"]:
                evidence_items.append(
                    "active g_total with shading for glazing rows above the table 2 reference input"
                )
            else:
                evidence_items.append(
                    "actual EN 410 g_perp retained for the global project/reference comparison"
                )

            rows.append(
                {
                    "construction": item["construction"],
                    "window_count": item["window_count"],
                    "area": item["area"],
                    "avg_u": avg_u,
                    "avg_g": avg_g,
                    "max_g": max_g,
                    "g_gap": g_gap,
                    "uw_status": uw_status,
                    "g_status": g_status,
                    "status": status,
                    "missing_evidence": self._compact_join(
                        missing_evidence_items, empty="None", max_chars=220
                    ),
                    "recommended_action": self._facade_glazing_action(
                        status, g_status, uw_status
                    ),
                    "evidence_needed": self._compact_join(evidence_items, max_chars=360),
                    "owner": (
                        "Facade/glazing lead"
                        if status in {"MISSING_EVIDENCE", "REFERENCE_DEVIATION"}
                        else "Model reviewer / compliance reviewer"
                    ),
                }
            )

        return sorted(
            rows,
            key=lambda row: (
                (
                    0
                    if row["status"] == "MISSING_EVIDENCE"
                    else 1 if row["status"] == "REFERENCE_DEVIATION" else 2
                ),
                -(row["g_gap"] or 0.0),
                -row["area"],
                row["construction"],
            ),
        )

    def _build_frame_fraction_rows(self, rooms_data: List[Any]) -> List[Dict[str, Any]]:
        """Aggregate external-window frame fraction by construction."""
        limit = SIA3802_LIMIT_VALUES["window_frame_fraction"]
        grouped: Dict[str, Dict[str, Any]] = {}
        for room in rooms_data:
            for opening in getattr(room, "openings", []) or []:
                if not getattr(opening, "is_external", False):
                    continue
                opening_type = str(getattr(opening, "opening_type", "") or "").lower()
                if (
                    opening_type
                    and "window" not in opening_type
                    and "glaz" not in opening_type
                ):
                    continue

                construction = str(
                    getattr(opening, "construction_id", "") or "NO_CONSTRUCTION"
                )
                area = self._safe_float(getattr(opening, "area", 0.0), 0.0) or 0.0
                weight = area if area > 0 else 1.0
                frame_fraction = self._safe_float(
                    getattr(opening, "frame_fraction", None), None
                )
                row = grouped.setdefault(
                    construction,
                    {
                        "construction": construction,
                        "window_count": 0,
                        "area": 0.0,
                        "values": [],
                        "max_frame_fraction": None,
                        "fail_count": 0,
                        "missing_count": 0,
                    },
                )
                row["window_count"] += 1
                row["area"] += area
                if frame_fraction is None:
                    row["missing_count"] += 1
                    continue
                row["values"].append((frame_fraction, weight))
                row["max_frame_fraction"] = (
                    frame_fraction
                    if row["max_frame_fraction"] is None
                    else max(row["max_frame_fraction"], frame_fraction)
                )
                if frame_fraction > limit:
                    row["fail_count"] += 1

        rows: List[Dict[str, Any]] = []
        for item in grouped.values():
            avg_frame_fraction = self._weighted_average(item["values"])
            if item["fail_count"]:
                justification = self._accepted_justification(
                    rule="SIA3802_FRAME_FRACTION",
                    construction=item["construction"],
                    domain="Openings",
                )
                if justification:
                    status = "JUSTIFIED_BY_EVIDENCE"
                    action = "Keep the extracted frame fraction visible and retain the reviewer-signed facade justification in the audit pack."
                    evidence = describe_justification(justification)
                else:
                    status = "REFERENCE_DEVIATION"
                    action = "Keep the actual frame/glass split and evaluate the deviation in the global SIA project/reference calculation; correct it only if the model is intended to reproduce the reference input."
                    evidence = "CDB glazing/frame export; manufacturer frame/glass schedule; global project/reference calculation evidence."
            elif item["missing_count"]:
                status = "MISSING"
                action = "Provide frame fraction ff for every external window construction before final SIA 380/2 wording."
                evidence = "CDB construction properties, manufacturer schedule or facade take-off with frame/glass split."
            else:
                status = "REFERENCE_MATCH"
                action = "Keep frame-fraction evidence in the audit pack and monitor if window constructions change."
                evidence = "CDB export or reviewed glazing schedule proving the retained frame fraction."

            rows.append(
                {
                    "construction": item["construction"],
                    "window_count": item["window_count"],
                    "area": item["area"],
                    "avg_frame_fraction": avg_frame_fraction,
                    "max_frame_fraction": item["max_frame_fraction"],
                    "limit": limit,
                    "fail_count": item["fail_count"],
                    "missing_count": item["missing_count"],
                    "status": status,
                    "action": action,
                    "evidence": evidence,
                    "owner": (
                        "Facade/glazing lead"
                        if status == "REFERENCE_DEVIATION"
                        else "Model reviewer / compliance reviewer"
                    ),
                }
            )

        return sorted(
            rows,
            key=lambda row: (
                (
                    0
                    if row["status"] == "REFERENCE_DEVIATION"
                    else 1 if row["status"] == "MISSING" else 2
                ),
                -row["fail_count"],
                -(row["max_frame_fraction"] or 0.0),
                -row["area"],
                row["construction"],
            ),
        )

    def _build_envelope_u_rows(self, rooms_data: List[Any]) -> List[Dict[str, Any]]:
        """Aggregate external opaque envelope U-values by type and construction."""
        grouped: Dict[tuple, Dict[str, Any]] = {}
        for room in rooms_data:
            for surface in getattr(room, "surfaces", []) or []:
                if not getattr(surface, "is_external", False):
                    continue
                surface_type = self._surface_review_type(
                    getattr(surface, "surface_type", None)
                )
                limit = self._surface_u_limit(surface_type)
                if limit is None:
                    continue
                net_area = (
                    self._safe_float(
                        getattr(surface, "net_area", getattr(surface, "area", 0.0)), 0.0
                    )
                    or 0.0
                )
                if net_area <= 1e-6:
                    continue
                construction_ids = getattr(surface, "construction_ids", None) or []
                construction = (
                    ", ".join(str(item) for item in construction_ids)
                    if construction_ids
                    else "NO_CONSTRUCTION"
                )
                u_value = self._safe_float(getattr(surface, "u_value", None), None)
                key = (surface_type, construction)
                row = grouped.setdefault(
                    key,
                    {
                        "surface_type": surface_type,
                        "construction": construction,
                        "surface_count": 0,
                        "net_area": 0.0,
                        "values": [],
                        "max_u": None,
                        "limit": limit,
                        "fail_count": 0,
                        "missing_count": 0,
                    },
                )
                row["surface_count"] += 1
                row["net_area"] += net_area
                if u_value is None:
                    row["missing_count"] += 1
                    continue
                row["values"].append((u_value, net_area))
                row["max_u"] = (
                    u_value if row["max_u"] is None else max(row["max_u"], u_value)
                )
                if u_value > limit:
                    row["fail_count"] += 1

        rows: List[Dict[str, Any]] = []
        for item in grouped.values():
            avg_u = self._weighted_average(item["values"])
            gap = avg_u - item["limit"] if avg_u is not None else None
            if item["fail_count"]:
                justification = self._accepted_justification(
                    rule=self._surface_u_rule(item["surface_type"]),
                    construction=item["construction"],
                    domain="Envelope",
                )
                if justification:
                    status = "JUSTIFIED_BY_EVIDENCE"
                    action = "Keep the extracted U-value visible and retain the reviewer-signed SIA reference-calculation justification in the audit pack."
                    evidence = describe_justification(justification)
                else:
                    status = "REFERENCE_DEVIATION"
                    action = "Keep the actual construction value and evaluate it in the global SIA project/reference calculation; change it only if reproducing the table 3 reference input."
                    evidence = "Construction build-up, CDB U-value source and global project/reference calculation evidence."
            elif item["missing_count"]:
                status = "MISSING"
                action = "Provide U-value/construction evidence for every external opaque surface in this construction group."
                evidence = "CDB construction export or audited U-value calculation."
            else:
                status = "REFERENCE_MATCH"
                action = "Keep construction evidence in the audit pack."
                evidence = "CDB construction export and U-value source."

            rows.append(
                {
                    "surface_type": item["surface_type"],
                    "construction": item["construction"],
                    "surface_count": item["surface_count"],
                    "net_area": item["net_area"],
                    "avg_u": avg_u,
                    "max_u": item["max_u"],
                    "limit": item["limit"],
                    "gap": gap,
                    "status": status,
                    "action": action,
                    "evidence": evidence,
                    "owner": (
                        "Envelope lead"
                        if status == "REFERENCE_DEVIATION"
                        else "Model reviewer / compliance reviewer"
                    ),
                }
            )

        return sorted(
            rows,
            key=lambda row: (
                (
                    0
                    if row["status"] == "REFERENCE_DEVIATION"
                    else 1 if row["status"] == "MISSING" else 2
                ),
                -(row["gap"] or 0.0),
                -row["net_area"],
                row["surface_type"],
                row["construction"],
            ),
        )

    def _build_open_items_backlog_rows(
        self,
        alert_groups: List[Dict[str, Any]],
        sia3802_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
        rooms_data: List[Any],
        preflight_checks: List[Dict[str, Any]],
        dynamic_results: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """Build a combined backlog from alerts, coverage gaps and navigator gaps."""
        rows: List[Dict[str, str]] = []
        for group in alert_groups:
            rows.append(
                {
                    "priority": str(group.get("priority") or "P3"),
                    "source": "Current model alerts",
                    "domain": str(group.get("category") or "Model"),
                    "item": str(group.get("rule") or "Grouped issue"),
                    "status": self._status_for_alert_group(group),
                    "reason": (
                        f"{group.get('count', 0)} issue(s), max severity {group.get('max_severity', '')}, "
                        f"scope {group.get('construction', '')}."
                    ),
                    "next_action": self._action_for_alert_group(group),
                    "expected_output": self._p1_evidence_needed_for_group(group),
                    "owner": self._p1_owner_for_group(group),
                    "keep_until": "Alert disappears or reviewer signs off evidence.",
                }
            )

        coverage_rows = self._build_sia_data_coverage_rows(
            sia3802_results,
            sia4010_results,
            rooms_data,
            preflight_checks,
            dynamic_results,
        )
        for item in coverage_rows:
            if item.get("coverage_status") not in {"PARTIAL", "MISSING", "NOT_CHECKABLE"}:
                continue
            rows.append(
                {
                    "priority": self._input_request_priority(item),
                    "source": "Coverage matrix",
                    "domain": str(
                        item.get("domain") or item.get("standard") or "Coverage"
                    ),
                    "item": str(
                        item.get("id") or item.get("criterion") or "Coverage item"
                    ),
                    "status": str(item.get("coverage_status") or "OPEN"),
                    "reason": str(
                        item.get("current_evidence") or item.get("criterion") or ""
                    ),
                    "next_action": str(item.get("next_action") or ""),
                    "expected_output": str(
                        item.get("data_needed") or item.get("preferred_format") or ""
                    ),
                    "owner": str(item.get("owner") or "Model reviewer"),
                    "keep_until": "Coverage status becomes AVAILABLE or reviewer accepts the limitation.",
                }
            )

        for item in SIA3802_NAVIGATOR_BACKLOG:
            current_status = str(item.get("current_project_status") or "")
            upper_status = current_status.upper()
            if upper_status.startswith("COMPLETE"):
                continue
            priority = "P2" if "MISSING" in upper_status else "P3"
            rows.append(
                {
                    "priority": priority,
                    "source": "Manager navigator backlog",
                    "domain": str(item.get("name") or "Navigator"),
                    "item": str(item.get("epic") or "Navigator epic"),
                    "status": current_status or "OPEN",
                    "reason": str(item.get("acceptance_criteria") or ""),
                    "next_action": str(item.get("next_action") or ""),
                    "expected_output": str(item.get("user_story") or ""),
                    "owner": "Developer / compliance reviewer",
                    "keep_until": "Navigator capability is implemented or explicitly deferred.",
                }
            )

        priority_rank = {"P1": 0, "P2": 1, "P3": 2}
        return sorted(
            rows,
            key=lambda row: (
                priority_rank.get(row["priority"], 3),
                row["source"],
                row["domain"],
                row["item"],
            ),
        )

    @staticmethod
    def _surface_review_type(surface_type: Any) -> str:
        """Normalize VE surface type into the envelope review buckets."""
        raw = str(surface_type or "").strip().lower()
        if "." in raw:
            raw = raw.split(".")[-1]
        raw = raw.replace(" ", "_").replace("-", "_")
        if raw in {"ext_wall", "external_wall", "wall"}:
            return "wall"
        if raw in {"roof", "flat_roof", "ext_roof", "external_roof"}:
            return "roof"
        if raw in {"floor", "ground_floor", "external_floor", "ext_floor"}:
            return "floor"
        return raw

    @staticmethod
    def _surface_u_limit(surface_type: str) -> Optional[float]:
        """Return the SIA 380/2 readiness U-value limit for an envelope type."""
        if surface_type == "wall":
            return SIA3802_LIMIT_VALUES["external_wall_u"]
        if surface_type == "roof":
            return SIA3802_LIMIT_VALUES["flat_roof_u"]
        if surface_type == "floor":
            return SIA3802_LIMIT_VALUES["ground_floor_u"]
        return None

    @staticmethod
    def _surface_u_rule(surface_type: str) -> str:
        """Return the alert/justification rule expected for an envelope U-value row."""
        if surface_type == "wall":
            return "SIA3802_U_VALUE_EXTERNAL_WALL"
        if surface_type == "roof":
            return "SIA3802_U_VALUE_ROOF"
        if surface_type == "floor":
            return "SIA3802_U_VALUE_GROUND_FLOOR"
        return "SIA3802_OPAQUE_U_VALUES"

    def _accepted_justification(
        self,
        *,
        rule: str,
        construction: str,
        domain: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Find a reviewed justification that matches the rule and construction scope."""
        return find_accepted_justification(
            self.sia3802_justifications,
            rule=rule,
            construction=construction,
            domain=domain,
            standard="SIA 380/2",
        )

    def _accepted_justification_for_group(
        self, group: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find a reviewed justification matching an alert group."""
        return self._accepted_justification(
            rule=str(group.get("rule") or ""),
            construction=str(group.get("construction") or ""),
            domain=str(group.get("category") or ""),
        )

    @staticmethod
    def _facade_glazing_action(status: str, g_status: str, uw_status: str) -> str:
        """Return a concise action for a facade/glazing construction row."""
        if status == "REFERENCE_DEVIATION" and g_status == "REFERENCE_DEVIATION":
            return (
                "Confirm whether VE solar_factor is EN 410 g_perp, SHGC or another CDB value. "
                "Retain the actual value for the global project/reference calculation, or reproduce 0.50 when building a reference-input model."
            )
        if status == "REFERENCE_DEVIATION" and uw_status == "REFERENCE_DEVIATION":
            return "Retain the actual Uw for the global comparison, or reproduce the table 2 value when building a reference-input model."
        if status == "MISSING_EVIDENCE":
            return "Complete the missing facade evidence before any final SIA 380/2 claim for openings."
        return "Keep construction evidence in the audit pack and monitor if glazing/shading assumptions change."

    def _build_ve_g_values_audit_rows(
        self, rooms_data: List[Any]
    ) -> List[Dict[str, Any]]:
        """Aggregate external glazing g-value evidence by construction."""
        grouped: Dict[str, Dict[str, Any]] = {}
        for room in rooms_data:
            for opening in getattr(room, "openings", []) or []:
                if not getattr(opening, "is_external", False):
                    continue
                opening_type = str(getattr(opening, "opening_type", "") or "").lower()
                if (
                    opening_type
                    and "window" not in opening_type
                    and "glaz" not in opening_type
                ):
                    continue

                construction = str(
                    getattr(opening, "construction_id", "") or "NO_CONSTRUCTION"
                )
                area = self._safe_float(getattr(opening, "area", 0.0), 0.0) or 0.0
                weight = area if area > 0 else 1.0
                row = grouped.setdefault(
                    construction,
                    {
                        "construction": construction,
                        "window_count": 0,
                        "area": 0.0,
                        "selected_sia_g": [],
                        "selected_source": set(),
                        "cdb_g_value": [],
                        "bs_en_410": [],
                        "building_regulations": [],
                        "bfrc": [],
                        "g_total": [],
                        "shading_field_names": set(),
                        "shading_type": set(),
                        "shading_control": set(),
                        "shading_optical": set(),
                        "active_shading_count": 0,
                        "weight": [],
                    },
                )
                row["window_count"] += 1
                row["area"] += area
                row["weight"].append(weight)
                for key, attr in (
                    ("selected_sia_g", "solar_factor"),
                    ("cdb_g_value", "cdb_g_value"),
                    ("bs_en_410", "g_value_bs_en_410"),
                    ("building_regulations", "g_value_building_regulations"),
                    ("bfrc", "g_value_bfrc"),
                    ("g_total", "g_total"),
                ):
                    value = self._safe_float(getattr(opening, attr, None), None)
                    row[key].append((value, weight))
                source = str(getattr(opening, "solar_factor_source", "") or "")
                if source:
                    row["selected_source"].add(source)
                active_solar_protection = has_active_solar_protection(opening)
                if active_solar_protection:
                    row["active_shading_count"] += 1
                    shading_type = str(getattr(opening, "shading_type", "") or "")
                    if shading_type:
                        row["shading_type"].add(shading_type)
                    shading_control = str(getattr(opening, "shading_control", "") or "")
                    if shading_control:
                        row["shading_control"].add(shading_control)

                shading_properties = getattr(opening, "shading_properties", {}) or {}
                if isinstance(shading_properties, dict):
                    for key, value in shading_properties.items():
                        if value in (None, ""):
                            continue
                        row["shading_field_names"].add(str(key))
                        if self._is_shading_optical_field(str(key)):
                            row["shading_optical"].add(f"{key}={value}")

        rows: List[Dict[str, Any]] = []
        for item in grouped.values():
            selected_sia_g = self._weighted_average(item["selected_sia_g"])
            cdb_g_value = self._weighted_average(item["cdb_g_value"])
            bs_en_410 = self._weighted_average(item["bs_en_410"])
            building_regulations = self._weighted_average(item["building_regulations"])
            bfrc = self._weighted_average(item["bfrc"])
            g_total = self._weighted_average(item["g_total"])
            delta_cdb_en410 = (
                cdb_g_value - bs_en_410
                if cdb_g_value is not None and bs_en_410 is not None
                else None
            )
            g_proof_status = self._g_proof_status(cdb_g_value, bs_en_410, selected_sia_g)
            g_total_status = self._g_total_status(
                selected_sia_g,
                g_total,
                item["active_shading_count"],
                g_proof_status,
            )
            rows.append(
                {
                    "construction": item["construction"],
                    "window_count": item["window_count"],
                    "area": item["area"],
                    "selected_sia_g": selected_sia_g,
                    "selected_source": self._compact_join(
                        sorted(item["selected_source"]), empty="No source", max_chars=180
                    ),
                    "cdb_g_value": cdb_g_value,
                    "bs_en_410": bs_en_410,
                    "building_regulations": building_regulations,
                    "bfrc": bfrc,
                    "g_proof_status": g_proof_status,
                    "delta_cdb_en410": delta_cdb_en410,
                    "shading_field_count": len(item["shading_field_names"]),
                    "shading_type": self._compact_join(
                        sorted(item["shading_type"]),
                        empty="No active shading type detected",
                        max_chars=220,
                    ),
                    "shading_control": self._compact_join(
                        sorted(item["shading_control"]),
                        empty="No control detected",
                        max_chars=220,
                    ),
                    "shading_optical_evidence": self._compact_join(
                        sorted(item["shading_optical"]),
                        empty="No optical shade fields detected",
                        max_chars=240,
                    ),
                    "g_total": g_total,
                    "g_total_status": g_total_status,
                    "recommended_action": self._ve_g_values_action(
                        g_proof_status,
                        g_total_status,
                        selected_sia_g,
                        cdb_g_value,
                        bs_en_410,
                    ),
                }
            )

        return sorted(
            rows,
            key=lambda row: (
                (
                    0
                    if row["g_total_status"]
                    in {
                        "CALCULATION_REQUIRED",
                        "BASE_G_ABOVE_REFERENCE_NO_ACTIVE_SHADING",
                    }
                    else 1
                ),
                (
                    0
                    if row["g_proof_status"]
                    in {"MISSING_G_VALUE", "SIA_MAPPING_REQUIRED"}
                    else 1
                ),
                -(row["area"] or 0.0),
                row["construction"],
            ),
        )

    @staticmethod
    def _weighted_average(values: List[Any]) -> Optional[float]:
        """Return a weighted average from ``(value, weight)`` tuples."""
        total = 0.0
        total_weight = 0.0
        for item in values:
            if not isinstance(item, tuple) or len(item) != 2:
                continue
            value, weight = item
            if value is None:
                continue
            total += value * weight
            total_weight += weight
        return total / total_weight if total_weight else None

    @staticmethod
    def _is_shading_optical_field(key: str) -> bool:
        """Return true when a CDB field looks like shading optical evidence."""
        lowered = key.lower()
        return any(
            token in lowered
            for token in (
                "transmittance",
                "transmitance",
                "coefficient",
                "radiant_fraction",
                "sky",
                "ground",
            )
        )

    @staticmethod
    def _has_active_shading_from_properties(properties: Dict[str, Any]) -> bool:
        """Return true when VE properties indicate an active shading device."""
        for key in (
            "external_shade_active",
            "internal_shade_active",
            "local_shade_active",
        ):
            value = properties.get(key)
            if isinstance(value, bool):
                if value:
                    return True
            elif isinstance(value, (int, float)):
                if value != 0:
                    return True
            elif isinstance(value, str) and value.strip().lower() in {
                "1",
                "true",
                "yes",
                "y",
                "on",
                "active",
                "enabled",
            }:
                return True
        return False

    @staticmethod
    def _g_proof_status(
        cdb_g_value: Optional[float],
        bs_en_410: Optional[float],
        selected_sia_g: Optional[float],
    ) -> str:
        """Classify whether glazing data proves a SIA-comparable g-value."""
        if (
            bs_en_410 is not None
            and cdb_g_value is not None
            and abs(cdb_g_value - bs_en_410) > 0.005
        ):
            return "PROVES_CDB_G_IS_NOT_EN410"
        if bs_en_410 is not None:
            return "EN410_AVAILABLE"
        if selected_sia_g is not None:
            return "SIA_MAPPING_REQUIRED"
        return "MISSING_G_VALUE"

    @staticmethod
    def _g_total_status(
        selected_sia_g: Optional[float],
        g_total: Optional[float],
        active_shading_count: int,
        g_proof_status: str = "",
    ) -> str:
        """Classify whether shaded total solar factor evidence is available."""
        if g_total is not None:
            return "DIRECT_OR_IMPORTED_VALUE"
        comparable_base_g = g_proof_status in {
            "EN410_AVAILABLE",
            "PROVES_CDB_G_IS_NOT_EN410",
        }
        if active_shading_count:
            if (
                comparable_base_g
                and selected_sia_g is not None
                and selected_sia_g <= SIA3802_LIMIT_VALUES["glazing_g_value"]
            ):
                return "NOT_REQUIRED_FOR_G_LIMIT"
            return "CALCULATION_REQUIRED"
        if (
            comparable_base_g
            and selected_sia_g is not None
            and selected_sia_g <= SIA3802_LIMIT_VALUES["glazing_g_value"]
        ):
            return "NOT_REQUIRED_FOR_G_LIMIT"
        if selected_sia_g is not None:
            if (
                comparable_base_g
                and selected_sia_g > SIA3802_LIMIT_VALUES["glazing_g_value"]
            ):
                return "BASE_G_ABOVE_REFERENCE_NO_ACTIVE_SHADING"
            return "NOT_APPLICABLE_NO_ACTIVE_SHADING"
        return "NOT_APPLICABLE_NO_ACTIVE_SHADING"

    @staticmethod
    def _ve_g_values_action(
        g_proof_status: str,
        g_total_status: str,
        selected_sia_g: Optional[float],
        cdb_g_value: Optional[float],
        bs_en_410: Optional[float],
    ) -> str:
        """Return the recommended reviewer action for one glazing construction."""
        if g_total_status == "BASE_G_ABOVE_REFERENCE_NO_ACTIVE_SHADING":
            return (
                "No active solar protection is modelled, so g_total is not applicable. Retain the actual base g_perp in the "
                "global comparison, or select glazing at/below 0.50 when reproducing the table 2 reference-input model."
            )
        if g_total_status == "CALCULATION_REQUIRED":
            return (
                "An active solar-protection device is modelled. Extract its optical/control fields and provide a reviewed "
                "ISO 52022-3 / ISO 15099 calculation or manufacturer g_total evidence."
            )
        if g_proof_status == "PROVES_CDB_G_IS_NOT_EN410":
            return (
                "Use bs_en_410 as the SIA g_perp candidate and keep the CDB export/review summary proving "
                f"that cdb g_value {cdb_g_value:.3f} differs from EN 410 {bs_en_410:.3f}."
            )
        if g_proof_status == "SIA_MAPPING_REQUIRED":
            return "Attach a reviewer note mapping the selected VE g-value to the SIA comparable g_perp before claiming compliance."
        if g_proof_status == "MISSING_G_VALUE":
            return "Fix CDB glazing extraction or attach a manufacturer glazing schedule with EN 410 g_perp."
        if (
            selected_sia_g is not None
            and selected_sia_g <= SIA3802_LIMIT_VALUES["glazing_g_value"]
        ):
            return "Keep EN 410/CDB proof in the audit pack; no shaded g_total is needed for the g-value limit."
        return "Keep evidence and reviewer sign-off with the project compliance pack."

    @staticmethod
    def _ve_g_proof_format(
        status: str,
        pass_format: Any,
        partial_format: Any,
        fail_format: Any,
        info_format: Any,
    ) -> Any:
        """Return the Excel cell format for g-value proof status."""
        if status in {"EN410_AVAILABLE", "PROVES_CDB_G_IS_NOT_EN410"}:
            return pass_format if status == "EN410_AVAILABLE" else info_format
        if status == "SIA_MAPPING_REQUIRED":
            return partial_format
        return fail_format

    @staticmethod
    def _ve_g_total_format(
        status: str,
        pass_format: Any,
        partial_format: Any,
        fail_format: Any,
        info_format: Any,
    ) -> Any:
        """Return the Excel cell format for shaded g-total status."""
        if status in {"DIRECT_OR_IMPORTED_VALUE", "NOT_REQUIRED_FOR_G_LIMIT"}:
            return pass_format
        if status == "CALCULATION_REQUIRED":
            return partial_format
        if status == "BASE_G_ABOVE_REFERENCE_NO_ACTIVE_SHADING":
            return partial_format
        if status == "MISSING_SHADING_OR_CALCULATION":
            return fail_format
        return info_format

    def _build_alert_groups(self, alerts: List[Alert]) -> List[Dict[str, Any]]:
        """Build stable technical groups from raw alerts."""
        groups: Dict[Any, Dict[str, Any]] = {}
        for alert in alerts:
            construction = self._get_alert_construction_key(alert)
            object_type = self._get_alert_object_type(alert)
            key = (alert.category, construction, object_type, alert.rule)
            if key not in groups:
                groups[key] = {
                    "category": alert.category,
                    "construction": construction,
                    "object_type": object_type,
                    "rule": alert.rule,
                    "description": alert.description,
                    "recommendation": alert.recommendation,
                    "severity_counts": Counter(),
                    "max_severity": alert.severity.value,
                    "count": 0,
                    "affected_area": 0.0,
                    "u_sum": 0.0,
                    "u_count": 0,
                    "g_sum": 0.0,
                    "g_count": 0,
                    "evidence_samples": [],
                }

            group = groups[key]
            group["count"] += 1
            group["affected_area"] += self._get_alert_area(alert)
            group["severity_counts"][alert.severity.value] += 1
            u_value = self._get_alert_numeric(alert, "u_value")
            if u_value is not None:
                group["u_sum"] += u_value
                group["u_count"] += 1
            g_value = self._get_alert_numeric(alert, "solar_factor")
            if g_value is not None:
                group["g_sum"] += g_value
                group["g_count"] += 1
            if self._severity_rank(alert.severity.value) < self._severity_rank(
                group["max_severity"]
            ):
                group["max_severity"] = alert.severity.value

            evidence = self._format_alert_data(alert)
            if evidence and len(group["evidence_samples"]) < 3:
                group["evidence_samples"].append(evidence)

        for group in groups.values():
            group["avg_u"] = (
                group["u_sum"] / group["u_count"] if group["u_count"] else None
            )
            group["avg_g"] = (
                group["g_sum"] / group["g_count"] if group["g_count"] else None
            )
            group["priority"] = self._get_priority(group)
            group["priority_score"] = self._get_priority_score(group)

        return sorted(
            groups.values(),
            key=lambda group: (
                group["priority_score"],
                -group["count"],
                -group["affected_area"],
                group["category"],
                group["construction"],
                group["rule"],
            ),
        )

    def _get_alert_construction_key(self, alert: Alert) -> str:
        """Return the best grouping key for an alert's construction scope."""
        data = getattr(alert, "data", None)
        if isinstance(data, dict):
            value = data.get("construction_id") or data.get("construction")
            if value:
                return str(value)

        construction_id = getattr(data, "construction_id", None)
        if construction_id:
            return str(construction_id)

        construction_ids = getattr(data, "construction_ids", None)
        if construction_ids:
            return ", ".join(str(item) for item in construction_ids)

        rule = str(alert.rule or "").upper()
        if "SIA4010" in rule or str(alert.category or "").upper().startswith("SIA4010"):
            return "VALIDATION"
        if (
            rule in {"SIA3802_WWR", "SIA3801_WWR"}
            or hasattr(data, "surfaces")
            or hasattr(data, "openings")
        ):
            return "ROOM_LEVEL"
        return "NO_CONSTRUCTION"

    @staticmethod
    def _get_alert_object_type(alert: Alert) -> str:
        """Return a compact object type label for alert grouping."""
        data = getattr(alert, "data", None)
        if isinstance(data, dict):
            value = data.get("type") or data.get("system_type")
            return str(value) if value else "dict"

        for attr in ("opening_type", "surface_type"):
            value = getattr(data, attr, None)
            if value:
                return str(value)

        if hasattr(data, "surfaces") or hasattr(data, "openings"):
            return "room"

        rule = str(alert.rule or "").upper()
        if "SIA4010" in rule:
            return "validation"

        return data.__class__.__name__ if data is not None else "building"

    @staticmethod
    def _safe_float(value: Any, default: Optional[float] = 0.0) -> Optional[float]:
        """Convert VE/API values to float without failing report generation."""
        if value in (None, ""):
            return default
        try:
            if isinstance(value, str):
                normalized = value.strip().replace(" ", "")
                if "," in normalized and "." not in normalized:
                    normalized = normalized.replace(",", ".")
                return float(normalized)
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _get_alert_area(alert: Alert) -> float:
        """Return the affected area attached to an alert when available."""
        data = getattr(alert, "data", None)
        if isinstance(data, dict):
            value = data.get("area")
        else:
            value = getattr(data, "area", None)
        return ExcelReportGenerator._safe_float(value, 0.0) or 0.0

    @staticmethod
    def _get_alert_numeric(alert: Alert, key: str) -> Optional[float]:
        """Return a numeric value from alert data by attribute or dictionary key."""
        data = getattr(alert, "data", None)
        if isinstance(data, dict):
            value = data.get(key)
        else:
            value = getattr(data, key, None)
        if value in (None, ""):
            return None
        return ExcelReportGenerator._safe_float(value, None)

    @staticmethod
    def _write_optional_number(
        worksheet: Any,
        row: int,
        col: int,
        value: Optional[float],
        number_format: Any,
        cell_format: Any,
    ):
        """Write a number when available or an empty formatted cell otherwise."""
        if value is None:
            worksheet.write(row, col, "", cell_format)
        else:
            worksheet.write(row, col, value, number_format)

    @staticmethod
    def _severity_rank(severity_value: str) -> int:
        """Return an ordering rank for alert severities."""
        order = {
            "Critical": 0,
            "High": 1,
            "Medium": 2,
            "Low": 3,
        }
        return order.get(str(severity_value), 4)

    @staticmethod
    def _get_priority(group: Dict[str, Any]) -> str:
        """Assign a remediation priority to an alert group."""
        severity = group.get("max_severity", "")
        count = int(group.get("count", 0) or 0)
        rule = str(group.get("rule", "")).upper()
        if severity in {"Critical", "High"}:
            return "P1"
        if severity == "Medium" or "MISSING" in rule or "NOT_CHECKABLE" in rule:
            return "P2"
        if count >= 20:
            return "P2"
        return "P3"

    def _get_priority_score(self, group: Dict[str, Any]) -> int:
        """Return a stable sort score for remediation priority groups."""
        base = {
            "P1": 100,
            "P2": 200,
            "P3": 300,
        }.get(group.get("priority"), 400)
        severity_weight = self._severity_rank(group.get("max_severity", "")) * 10
        count_scope = min(int(group.get("count", 0) or 0), 99)
        area_scope = min(int(float(group.get("affected_area", 0.0) or 0.0) / 10), 99)
        scope_weight = max(0, 99 - min(count_scope + area_scope, 99))
        return base + severity_weight + scope_weight

    @staticmethod
    def _action_for_alert_group(group: Dict[str, Any]) -> str:
        """Return a practical remediation action for an alert group."""
        rule = str(group.get("rule", "")).upper()
        recommendation = str(group.get("recommendation", "") or "")
        if rule in {"SIA3802_SOLAR_FACTOR", "SIA3801_SOLAR_FACTOR"}:
            return (
                "Confirm which solar value must be retained for the SIA method "
                "(g-value, SHGC, EN 410, shading effect), then resolve by construction. "
                + recommendation
            )
        if rule in {"SIA3802_WWR", "SIA3801_WWR"}:
            return "Review the window-to-wall ratio by zone and document the accepted WWR threshold or reference-calculation basis."
        if "SIA4010" in rule:
            return "Collect SIA 4010 validation evidence: official test cases, APS/reference outputs and acceptable deviations."
        if "MISSING" in rule or "NOT_CHECKABLE" in rule:
            return (
                "Complete the missing value in VE or attach auditable external evidence."
            )
        return recommendation or "Review this item with the model owner."

    def _client_next_decision_rows(
        self,
        p1_groups: List[Dict[str, Any]],
        sia4010_results: Dict[str, Any],
    ) -> List[tuple]:
        """Build client summary next decisions from actual P1 groups."""
        rows = []
        for group in p1_groups[:3]:
            category = str(group.get("category", "") or "Model")
            rule = str(group.get("rule", "") or "Priority issue")
            action = self._action_for_alert_group(group)
            owner = self._p1_owner_for_group(group)
            evidence = self._p1_evidence_needed_for_group(group)
            rows.append((f"{category}: {rule} - {action}", owner, evidence))

        if rows:
            return rows

        evidence = sia4010_results.get("evidence", {}) or {}
        summary = evidence.get("summary", {}) if isinstance(evidence, dict) else {}
        if summary.get("status") != "READY_FOR_OFFICIAL_REVIEW":
            return [
                (
                    "Complete the SIA 4010 official evidence pack before any validation wording.",
                    "Compliance reviewer",
                    "Official test specs, Excel evaluation workbooks, candidate outputs, reference comparison plots and validation class confirmation.",
                )
            ]

        return [
            (
                "Submit the completed SIA 4010 evidence pack for official review/sign-off.",
                "Compliance reviewer",
                "Reviewer/sub-commission acceptance or documented validation decision.",
            )
        ]

    def _status_for_alert_group(self, group: Dict[str, Any]) -> str:
        """Return the report status for an alert group, including evidence overrides."""
        if self._accepted_justification_for_group(group):
            return "Justified by evidence"
        rule = str(group.get("rule", "")).upper()
        if "MISSING" in rule or "NOT_CHECKABLE" in rule or "SIA4010" in rule:
            return "To document"
        return "To resolve"

    @staticmethod
    def _p1_current_value_for_group(group: Dict[str, Any]) -> Optional[float]:
        """Return the representative current value for a P1 alert group."""
        rule = str(group.get("rule", "")).upper()
        if rule in {"SIA3802_SOLAR_FACTOR", "SIA3801_SOLAR_FACTOR"}:
            return group.get("avg_g")
        if rule in {
            "SIA3802_U_VALUE_EXTERNAL_WALL",
            "SIA3802_U_VALUE_ROOF",
            "SIA3802_U_VALUE_FLOOR",
            "SIA3801_U_VALUE_EXTERNAL_WALL",
            "SIA3801_U_VALUE_ROOF",
            "SIA3801_U_VALUE_FLOOR",
        }:
            return group.get("avg_u")
        if "SIA4010" in rule:
            return None
        return None

    @staticmethod
    def _p1_limit_for_group(group: Dict[str, Any]) -> Optional[float]:
        """Return the applicable limit for a P1 alert group when available."""
        rule = str(group.get("rule", "")).upper()
        if rule in {"SIA3802_SOLAR_FACTOR", "SIA3801_SOLAR_FACTOR"}:
            return SIA3802_LIMIT_VALUES["glazing_g_value"]
        if rule in {"SIA3802_U_VALUE_EXTERNAL_WALL", "SIA3801_U_VALUE_EXTERNAL_WALL"}:
            return SIA3802_LIMIT_VALUES["external_wall_u"]
        if rule in {"SIA3802_U_VALUE_ROOF", "SIA3801_U_VALUE_ROOF"}:
            return SIA3802_LIMIT_VALUES["flat_roof_u"]
        if rule in {"SIA3802_U_VALUE_FLOOR", "SIA3801_U_VALUE_FLOOR"}:
            return SIA3802_LIMIT_VALUES["ground_floor_u"]
        if "SIA4010" in rule:
            return float(len(SIA4010_REQUIRED_EVIDENCE))
        return None

    def _p1_gap_for_group(self, group: Dict[str, Any]) -> Optional[float]:
        """Return the numerical gap between current value and limit for a P1 group."""
        current_value = self._p1_current_value_for_group(group)
        limit_value = self._p1_limit_for_group(group)
        return self._p1_gap_for_values(
            str(group.get("rule", "")).upper(), current_value, limit_value
        )

    @staticmethod
    def _p1_gap_for_values(
        rule: str, current_value: Optional[float], limit_value: Optional[float]
    ) -> Optional[float]:
        """Return the signed compliance gap for one P1 value/limit pair."""
        if current_value is None or limit_value is None:
            return None
        if "SIA4010" in str(rule).upper():
            return limit_value - current_value
        return current_value - limit_value

    @staticmethod
    def _p1_decision_for_group(group: Dict[str, Any]) -> str:
        """Return the decision needed to close one P1 group."""
        rule = str(group.get("rule", "")).upper()
        if rule in {"SIA3802_SOLAR_FACTOR", "SIA3801_SOLAR_FACTOR"}:
            return "Confirm whether VE solar_factor is EN 410 g_perp/SHGC/g_total, then replace or document glazing/shading so the retained value is <= 0.50."
        if rule in {"SIA3802_U_VALUE_EXTERNAL_WALL", "SIA3801_U_VALUE_EXTERNAL_WALL"}:
            return "Either improve the external wall construction to U <= 0.20 W/m2K or provide a justified full SIA reference calculation."
        if "SIA4010" in rule:
            return "Decide the target validation class and collect the official SIA evidence pack before any SIA 4010 validation claim."
        if "MISSING" in rule or "NOT_CHECKABLE" in rule:
            return "Decide whether the missing value can be extracted from VE or must be provided as external auditable evidence."
        return "Review the grouped issue and document the accepted remediation path."

    @staticmethod
    def _p1_evidence_needed_for_group(group: Dict[str, Any]) -> str:
        """Return the evidence package expected for one P1 group."""
        rule = str(group.get("rule", "")).upper()
        if rule in {"SIA3802_SOLAR_FACTOR", "SIA3801_SOLAR_FACTOR"}:
            return "CDB glazing construction export; EN 410 g_perp or SHGC mapping note; shading device/control evidence if g_total is used; before/after VE screenshot or export."
        if rule in {"SIA3802_U_VALUE_EXTERNAL_WALL", "SIA3801_U_VALUE_EXTERNAL_WALL"}:
            return "Construction build-up; CDB U-value source; changed construction assignment or full SIA 380/2 reference calculation note."
        if "SIA4010" in rule:
            return "Official SIA test specs; official Excel evaluation workbooks; candidate APS/Vista outputs; reference comparison plots; validation class confirmation."
        if "VENTILATION" in rule:
            return "VE airflow/ventilation export; unit conversion; SIA 2024 use category; control class mapping."
        if "LIGHTING" in rule:
            return "Lighting power density; daylight/control strategy; SIA 387/4 mapping; relevant VE template export."
        if "HVAC" in rule:
            return "System type, capacity band, EER/SEER/SCOP or manufacturer evidence; APS/Vista outputs where applicable."
        return "Model export, calculation note and reviewer sign-off."

    @staticmethod
    def _p1_owner_for_group(group: Dict[str, Any]) -> str:
        """Return the recommended owner for resolving one P1 group."""
        rule = str(group.get("rule", "")).upper()
        category = str(group.get("category", "")).upper()
        if rule in {"SIA3802_SOLAR_FACTOR", "SIA3801_SOLAR_FACTOR"}:
            return "Facade/glazing lead"
        if "U_VALUE" in rule or category == "ENVELOPE":
            return "Envelope lead"
        if "SIA4010" in rule:
            return "Compliance reviewer"
        if "VENTILATION" in rule:
            return "HVAC engineer"
        if "LIGHTING" in rule:
            return "Lighting engineer"
        if "HVAC" in rule:
            return "HVAC engineer"
        return "Model reviewer"

    def _calculate_wwr(self, room: Any) -> float:
        """Calculate window-to-wall ratio directly when no analyzer is available."""
        if self.model_analyzer is not None:
            try:
                return self.model_analyzer.calculate_wwr(room)
            except Exception:
                pass
        external_walls = [
            surface
            for surface in getattr(room, "surfaces", [])
            if getattr(surface, "is_external", False)
            and str(getattr(surface, "surface_type", "") or "").lower()
            in {"wall", "ext_wall"}
        ]
        wall_area = sum(
            float(getattr(surface, "area", 0.0) or 0.0) for surface in external_walls
        )
        window_area = sum(
            float(getattr(opening, "area", 0.0) or 0.0)
            for opening in getattr(room, "openings", [])
            if getattr(opening, "is_external", False)
            and str(getattr(opening, "opening_type", "") or "").lower()
            in {"window", "glazing", "ext_glazing"}
        )
        return window_area / wall_area if wall_area > 0 else 0.0

    def _calculate_average_u_value(self, room: Any, surface_type: str) -> float:
        """Calculate area-weighted U-value directly when no analyzer is available."""
        if self.model_analyzer is not None:
            try:
                return self.model_analyzer.calculate_average_u_value(room, surface_type)
            except Exception:
                pass
        target = surface_type.lower()
        values = [
            (
                float(getattr(surface, "u_value", 0.0)),
                float(getattr(surface, "net_area", getattr(surface, "area", 0.0)) or 0.0),
            )
            for surface in getattr(room, "surfaces", [])
            if str(getattr(surface, "surface_type", "") or "").lower()
            in {target, f"ext_{target}"}
            and getattr(surface, "u_value", None) is not None
            and float(getattr(surface, "net_area", getattr(surface, "area", 0.0)) or 0.0)
            > 1e-6
        ]
        total_area = sum(area for _value, area in values)
        return (
            sum(value * area for value, area in values) / total_area
            if total_area > 0
            else 0.0
        )

    @staticmethod
    def _append_alert_identity(parts: List[str], data: Any) -> None:
        """Append stable object and construction identifiers."""

        object_id = getattr(data, "id", None)
        name = getattr(data, "name", None)
        if name and str(name) != str(object_id):
            parts.append(f"name={name}")
        if object_id:
            parts.append(f"id={object_id}")
        construction_id = getattr(data, "construction_id", None)
        if construction_id:
            parts.append(f"construction={construction_id}")
        construction_ids = getattr(data, "construction_ids", None)
        if construction_ids:
            parts.append(
                f"constructions={','.join(str(item) for item in construction_ids)}"
            )

    def _append_alert_envelope_values(self, parts: List[str], data: Any) -> None:
        """Append numeric envelope evidence without duplicating conversion logic."""

        numeric_fields = (
            ("u_value", "U", " W/m2K"),
            ("solar_factor", "g", ""),
            ("visible_transmittance", "tau_v", ""),
            ("frame_fraction", "frame_fraction", ""),
            ("g_total", "g_total", ""),
        )
        for attribute, label, unit in numeric_fields:
            raw_value = getattr(data, attribute, None)
            if raw_value is None:
                continue
            value = self._safe_float(raw_value, None)
            if value is not None:
                parts.append(f"{label}={value:.3f}{unit}")

        solar_factor_source = getattr(data, "solar_factor_source", None)
        if solar_factor_source:
            parts.append(f"g_source={solar_factor_source}")

    @staticmethod
    def _append_not_checkable_evidence(parts: List[str], data: Any) -> None:
        """Append explicit placeholders for evidence unavailable from VE."""

        for evidence_name in (
            "visible_transmittance",
            "frame_fraction",
            "g_total",
            "internal_gains_daily",
            "ventilation_installation_type",
            "ventilation_control_level",
        ):
            status = str(getattr(data, f"{evidence_name}_status", "") or "")
            placeholder = str(getattr(data, f"{evidence_name}_placeholder", "") or "")
            if status == "NOT_CHECKABLE":
                parts.append(
                    f"{evidence_name}=NOT_CHECKABLE"
                    + (f" [{placeholder}]" if placeholder else "")
                )

    def _append_alert_geometry(self, parts: List[str], data: Any) -> None:
        """Append surface, opening and adjacency evidence."""

        if hasattr(data, "area"):
            parts.append(f"area={self._safe_float(getattr(data, 'area'), 0.0):.2f} m2")
        if hasattr(data, "net_area"):
            parts.append(
                f"net_area={self._safe_float(getattr(data, 'net_area'), 0.0):.2f} m2"
            )
        if hasattr(data, "tilt") and getattr(data, "tilt") is not None:
            tilt = self._safe_float(getattr(data, "tilt"), None)
            if tilt is not None:
                parts.append(f"tilt={tilt:.1f} deg")
        if hasattr(data, "surface_type") and getattr(data, "surface_type"):
            parts.append(f"type={getattr(data, 'surface_type')}")
        if hasattr(data, "adjacency_room_ids") and getattr(data, "adjacency_room_ids"):
            parts.append(
                "adjacent_room_ids="
                + ",".join(
                    str(item) for item in getattr(data, "adjacency_room_ids") if item
                )
            )
        if hasattr(data, "opening_type") and getattr(data, "opening_type"):
            parts.append(f"type={getattr(data, 'opening_type')}")

    def _append_alert_ventilation_and_gains(self, parts: List[str], data: Any) -> None:
        """Append room ventilation, controls and internal-gain evidence."""

        if (
            hasattr(data, "ventilation_rate")
            and getattr(data, "ventilation_rate") is not None
        ):
            ventilation_rate = self._safe_float(getattr(data, "ventilation_rate"), None)
            if ventilation_rate is not None:
                ventilation_unit = str(
                    getattr(data, "ventilation_unit", None) or "VE active unit"
                )
                parts.append(f"ventilation={ventilation_rate:.3f} {ventilation_unit}")
        if (
            hasattr(data, "ventilation_m3_h_m2")
            and getattr(data, "ventilation_m3_h_m2") is not None
        ):
            normalized = self._safe_float(getattr(data, "ventilation_m3_h_m2"), None)
            if normalized is not None:
                parts.append(f"ventilation_normalized={normalized:.3f} m3/(h.m2)")
        if getattr(data, "ventilation_normalization_method", ""):
            parts.append(
                "ventilation_method="
                + str(getattr(data, "ventilation_normalization_method"))
            )
        if getattr(data, "ventilation_source", ""):
            parts.append("ventilation_source=" + str(getattr(data, "ventilation_source")))
        if getattr(data, "ventilation_control_evidence_note", ""):
            parts.append(
                "ventilation_control_context="
                + str(getattr(data, "ventilation_control_evidence_note"))
            )
        if hasattr(data, "internal_gains"):
            gains = getattr(data, "internal_gains") or {}
            if gains:
                parts.append(
                    "gains="
                    + ",".join(
                        f"{key}:{value:.2f}"
                        for key, value in gains.items()
                        if isinstance(value, (int, float))
                    )
                )

    @staticmethod
    def _append_mapping_alert_data(parts: List[str], data: Dict[str, Any]) -> None:
        """Append the supported keys from mapping-based alert payloads."""

        hour_fields = {"upper_hours", "upper_limit_hours", "lower_hours"}
        for key in (
            "id",
            "room_id",
            "room_name",
            "type",
            "efficiency",
            "energy_consumption",
            "upper_hours",
            "upper_limit_hours",
            "lower_hours",
            "window_operable",
            "method",
        ):
            value = data.get(key)
            if value not in (None, ""):
                suffix = " h" if key in hour_fields else ""
                parts.append(f"{key}={value}{suffix}")

    def _format_alert_data(self, alert: Alert) -> str:
        """Build a compact evidence string for the alert row."""

        data = getattr(alert, "data", None)
        if data is None:
            return ""

        parts: List[str] = []
        self._append_alert_identity(parts, data)
        self._append_alert_envelope_values(parts, data)
        self._append_not_checkable_evidence(parts, data)
        self._append_alert_geometry(parts, data)
        self._append_alert_ventilation_and_gains(parts, data)
        if isinstance(data, dict):
            self._append_mapping_alert_data(parts, data)

        if (
            str(alert.rule).upper() in {"SIA3802_WWR", "SIA3801_WWR"}
            and self.model_analyzer is not None
        ):
            try:
                parts.append(f"WWR={self.model_analyzer.calculate_wwr(data):.1%}")
            except (AttributeError, TypeError, ValueError, ZeroDivisionError):
                pass

        return "; ".join(part for part in parts if part)
