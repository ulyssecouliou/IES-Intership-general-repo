"""
Générateur de rapports Excel pour le Swiss Compliance Checker.
Ce module utilise xlsxwriter pour créer un fichier Excel professionnel dans VEScripts.
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
    logging.warning("xlsxwriter non disponible.")

from .config import (
    OUTPUT_DIR,
    EXCEL_REPORT_NAME,
    EXCEL_FORMATS,
    SIA_DATA_COVERAGE_MATRIX,
    SIA_COMPLIANCE_REQUIREMENT_MATRIX,
    SIA3802_LIMIT_VALUES,
    SIA4010_REQUIRED_EVIDENCE,
    SIA4010_SYSTEM_REQUIREMENT_SOURCES,
    SIA4010_TEST_CLASS_COVERAGE,
    SIA4010_TEST_READINESS_REQUIREMENTS,
    SIA4010_VALIDATION_CLASSES,
)
from .health_score import ScoreResult
from .rule_engine import Alert, Severity

logger = logging.getLogger(__name__)


class ExcelReportGenerator:
    """
    Génère un rapport Excel professionnel avec :
    - Onglets dédiés (SUMMARY, COMPLIANCE RESULTS, ROOMS, etc.).
    - Mise en forme conditionnelle (couleurs pour PASS/WARNING/FAIL).
    - Graphiques (scores par catégorie).
    """

    def __init__(self, output_path: str = None, model_analyzer: Any = None):
        """
        Initialise le générateur de rapports Excel.
        
        Args:
            output_path: Chemin du fichier Excel de sortie.
        """
        self.output_path = output_path or os.path.join(OUTPUT_DIR, EXCEL_REPORT_NAME)
        self.model_analyzer = model_analyzer
        self.workbook = None
        self.use_xlsxwriter = USE_XLSXWRITER

        if not self.use_xlsxwriter:
            raise RuntimeError("xlsxwriter n'est pas disponible. Impossible de générer le rapport Excel dans l'environnement VE.")

        self._init_workbook()

    def _init_workbook(self):
        """Initialise le classeur Excel."""
        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            output_dir = os.path.dirname(os.path.abspath(self.output_path))
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            self.workbook = xlsxwriter.Workbook(self.output_path)
            logger.info(f"Classeur Excel créé: {self.output_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la création du classeur Excel: {e}")
            raise

    def generate_report(
        self,
        score_result: ScoreResult,
        sia3802_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
        rooms_data: Optional[List[Any]] = None,
        preflight_checks: Optional[List[Dict[str, Any]]] = None,
        dynamic_results: Optional[Dict[str, Any]] = None,
    ):
        """
        Génère le rapport Excel complet.
        
        Args:
            score_result: Résultat des scores (Compliance Score, Health Score, etc.).
            sia3802_results: Résultats des vérifications SIA 380/2.
            sia4010_results: Résultats des vérifications SIA 4010.
            rooms_data: Données des pièces (optionnel).
        """
        try:
            self._generate_report_xlsxwriter(score_result, sia3802_results, sia4010_results, rooms_data, preflight_checks, dynamic_results)
            logger.info(f"Rapport Excel généré avec succès: {self.output_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport Excel: {e}")
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
    ):
        """Génère le rapport avec xlsxwriter."""
        alert_groups = self._build_alert_groups(score_result.alerts)
        self._write_manager_dashboard_xlsxwriter(score_result, sia3802_results, sia4010_results, rooms_data or [], alert_groups)
        self._write_client_summary_xlsxwriter(score_result, sia4010_results, rooms_data or [], alert_groups)
        self._write_preflight_xlsxwriter(preflight_checks or [], rooms_data or [], sia4010_results)
        self._write_p1_remediation_xlsxwriter(alert_groups, sia4010_results)
        self._write_assumptions_limits_xlsxwriter(score_result, sia4010_results, rooms_data or [])
        self._write_audit_log_xlsxwriter(score_result, sia4010_results, rooms_data or [], preflight_checks or [], dynamic_results or {})
        self._write_summary_xlsxwriter(score_result)
        self._write_action_plan_xlsxwriter(alert_groups)
        self._write_compliance_results_xlsxwriter(sia3802_results, sia4010_results)
        self._write_sia_requirements_xlsxwriter(sia3802_results, sia4010_results)
        self._write_sia_data_coverage_xlsxwriter(sia3802_results, sia4010_results, rooms_data or [], preflight_checks or [], dynamic_results or {})
        self._write_input_request_xlsxwriter(sia3802_results, sia4010_results, rooms_data or [], preflight_checks or [], dynamic_results or {})
        self._write_sia4010_readiness_xlsxwriter(sia4010_results, rooms_data or [])
        self._write_dynamic_results_xlsxwriter(dynamic_results or {})
        self._write_alert_summary_xlsxwriter(alert_groups)
        self._write_alerts_xlsxwriter(score_result.alerts)
        self._write_data_quality_xlsxwriter(score_result.alerts, rooms_data or [])
        self._write_detailed_scores_xlsxwriter(score_result.detailed_scores)
        if rooms_data:
            self._write_rooms_xlsxwriter(rooms_data)
        self.workbook.close()

    # =============================================================================
    # Méthodes pour xlsxwriter
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
        worksheet.set_tab_color("#0F766E")

        title_format = self.workbook.add_format({
            "bold": True,
            "font_size": 20,
            "font_color": "#FFFFFF",
            "bg_color": "#0B1F2A",
            "align": "left",
            "valign": "vcenter",
        })
        subtitle_format = self.workbook.add_format({
            "font_size": 10,
            "font_color": "#DCE8E8",
            "bg_color": "#0B1F2A",
            "align": "left",
            "valign": "vcenter",
        })
        card_title_format = self.workbook.add_format({
            "bold": True,
            "font_size": 9,
            "font_color": "#335C67",
            "bg_color": "#F2F7F6",
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "border_color": "#C8D8D6",
        })
        card_value_format = self.workbook.add_format({
            "bold": True,
            "font_size": 18,
            "font_color": "#0B1F2A",
            "bg_color": "#FFFFFF",
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "border_color": "#C8D8D6",
        })
        card_note_format = self.workbook.add_format({
            "font_size": 8,
            "font_color": "#4B5563",
            "bg_color": "#FFFFFF",
            "align": "center",
            "valign": "vcenter",
            "text_wrap": True,
            "border": 1,
            "border_color": "#C8D8D6",
        })
        section_format = self.workbook.add_format({
            "bold": True,
            "font_size": 12,
            "font_color": "#FFFFFF",
            "bg_color": "#335C67",
            "align": "left",
            "valign": "vcenter",
        })
        note_format = self.workbook.add_format({
            "font_size": 10,
            "font_color": "#334155",
            "bg_color": "#FFF7E6",
            "text_wrap": True,
            "valign": "top",
            "border": 1,
            "border_color": "#E8C66A",
        })
        header_format = self.workbook.add_format({
            "bold": True,
            "font_color": "#FFFFFF",
            "bg_color": "#0F766E",
            "border": 1,
            "border_color": "#D7E5E2",
        })
        cell_format = self.workbook.add_format({
            "border": 1,
            "border_color": "#D7E5E2",
            "text_wrap": True,
            "valign": "top",
        })
        priority_format = self.workbook.add_format({
            "bold": True,
            "font_color": "#7F1D1D",
            "bg_color": "#FEE2E2",
            "border": 1,
            "border_color": "#FCA5A5",
            "align": "center",
        })
        number_format = self.workbook.add_format({"border": 1, "border_color": "#D7E5E2", "num_format": "#,##0"})
        nav_format = self.workbook.add_format({
            "bold": True,
            "font_color": "#0F766E",
            "bg_color": "#EAF7F4",
            "border": 1,
            "border_color": "#9CCFC7",
            "align": "center",
        })

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
            "Executive view - modele VE, controles SIA 380/2 automatises, readiness SIA 4010 et priorites d'action.",
            subtitle_format,
        )
        nav_links = [
            ("A3:B3", "P1 Actions", "P1 REMEDIATION"),
            ("C3:D3", "Input Request", "INPUT REQUEST"),
            ("E3:F3", "SIA Coverage", "SIA DATA COVERAGE"),
            ("G3:H3", "Dynamic Results", "DYNAMIC RESULTS"),
            ("I3:J3", "SIA4010", "SIA4010 READINESS"),
            ("K3:L3", "Audit Log", "AUDIT LOG"),
        ]
        for cell_range, label, sheet_name in nav_links:
            first_cell = cell_range.split(":")[0]
            worksheet.merge_range(cell_range, "", nav_format)
            worksheet.write_url(first_cell, f"internal:'{sheet_name}'!A1", nav_format, string=label)

        alerts_count = self._count_alerts_by_severity(score_result.alerts)
        critical_high = alerts_count.get("Critical", 0) + alerts_count.get("High", 0)
        room_count = len(rooms_data)
        total_area = sum(self._safe_float(getattr(room, "area", 0.0)) for room in rooms_data)
        evidence = sia4010_results.get("evidence", {}) or {}
        evidence_present = sum(1 for item in SIA4010_REQUIRED_EVIDENCE if self._has_sia4010_evidence(evidence, item))

        self._write_dashboard_card(worksheet, "A4:B7", "MODEL QA", f"{score_result.health_score:.1f}", "Health score from data completeness and model quality.", card_title_format, card_value_format, card_note_format)
        self._write_dashboard_card(worksheet, "C4:D7", "SIA 380/2 SCORE", f"{score_result.compliance_score:.1f}", "Weighted automated indicator; non-checkable SIA 4010 evidence is kept separate.", card_title_format, card_value_format, card_note_format)
        self._write_dashboard_card(worksheet, "E4:F7", "SIA 4010 EVIDENCE", f"{evidence_present}/{len(SIA4010_REQUIRED_EVIDENCE)}", "Official evidence items detected locally.", card_title_format, card_value_format, card_note_format)
        self._write_dashboard_card(worksheet, "G4:H7", "ROOMS", f"{room_count}", "Thermal rooms extracted from VE.", card_title_format, card_value_format, card_note_format)
        self._write_dashboard_card(worksheet, "I4:J7", "FLOOR AREA", f"{total_area:,.1f}", "m2 extracted from room areas.", card_title_format, card_value_format, card_note_format)
        self._write_dashboard_card(worksheet, "K4:L7", "P1 RISKS", f"{critical_high}", "Critical + high alerts requiring attention.", card_title_format, card_value_format, card_note_format)

        worksheet.merge_range("A9:L9", "Executive Interpretation", section_format)
        worksheet.merge_range("A10:L12", self._dashboard_verdict(score_result, sia4010_results, rooms_data), note_format)

        score_rows = self._dashboard_score_rows(score_result)
        severity_rows = [
            ["Severity", "Count"],
            ["Critical", alerts_count.get("Critical", 0)],
            ["High", alerts_count.get("High", 0)],
            ["Medium", alerts_count.get("Medium", 0)],
            ["Low", alerts_count.get("Low", 0)],
        ]
        requirement_rows = self._dashboard_requirement_status_rows(sia3802_results, sia4010_results)

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

        worksheet.merge_range("A14:F14", "Scores by Domain", section_format)
        score_chart = self.workbook.add_chart({"type": "bar"})
        score_last_row = 3 + len(score_rows)
        score_chart.add_series({
            "name": "Score",
            "categories": f"='MANAGER DASHBOARD'!$N$4:$N${score_last_row}",
            "values": f"='MANAGER DASHBOARD'!$O$4:$O${score_last_row}",
            "fill": {"color": "#0F766E"},
            "border": {"none": True},
            "data_labels": {"value": True, "num_format": "0"},
        })
        score_chart.set_title({"name": "Score overview (0-100)"})
        score_chart.set_x_axis({"name": "Score", "min": 0, "max": 100, "major_gridlines": {"visible": False}})
        score_chart.set_y_axis({"major_gridlines": {"visible": False}})
        score_chart.set_legend({"none": True})
        score_chart.set_style(10)
        self._show_hidden_chart_data(score_chart)
        worksheet.insert_chart("A15", score_chart, {"x_scale": 1.25, "y_scale": 1.25})

        worksheet.merge_range("G14:L14", "Risk Distribution", section_format)
        alert_chart = self.workbook.add_chart({"type": "doughnut"})
        alert_chart.add_series({
            "name": "Alerts",
            "categories": "='MANAGER DASHBOARD'!$Q$5:$Q$8",
            "values": "='MANAGER DASHBOARD'!$R$5:$R$8",
            "points": [
                {"fill": {"color": "#7F1D1D"}},
                {"fill": {"color": "#DC2626"}},
                {"fill": {"color": "#F59E0B"}},
                {"fill": {"color": "#0EA5E9"}},
            ],
            "data_labels": {"percentage": True},
        })
        alert_chart.set_title({"name": "Alerts by severity"})
        alert_chart.set_style(10)
        self._show_hidden_chart_data(alert_chart)
        worksheet.insert_chart("G15", alert_chart, {"x_scale": 1.22, "y_scale": 1.22})

        worksheet.merge_range("A32:F32", "SIA Requirement Coverage", section_format)
        requirement_chart = self.workbook.add_chart({"type": "column"})
        req_last_row = 4 + len(requirement_rows)
        requirement_chart.add_series({
            "name": "Requirements",
            "categories": f"='MANAGER DASHBOARD'!$T$5:$T${req_last_row}",
            "values": f"='MANAGER DASHBOARD'!$U$5:$U${req_last_row}",
            "fill": {"color": "#335C67"},
            "border": {"none": True},
            "data_labels": {"value": True},
        })
        requirement_chart.set_title({"name": "Coverage by status"})
        requirement_chart.set_legend({"none": True})
        requirement_chart.set_y_axis({"major_gridlines": {"visible": False}})
        requirement_chart.set_style(10)
        self._show_hidden_chart_data(requirement_chart)
        worksheet.insert_chart("A33", requirement_chart, {"x_scale": 1.25, "y_scale": 1.05})

        worksheet.merge_range("G32:L32", "Top Priority Actions", section_format)
        worksheet.write_row("G33", ["Priority", "Category", "Issue count", "Action", "Evidence"], header_format)
        row = 33
        for group in alert_groups[:6]:
            worksheet.write(row, 6, group.get("priority", ""), priority_format if group.get("priority") == "P1" else cell_format)
            worksheet.write(row, 7, group.get("category", ""), cell_format)
            worksheet.write(row, 8, group.get("count", 0), number_format)
            worksheet.write(row, 9, self._action_for_alert_group(group), cell_format)
            worksheet.write(row, 10, "; ".join(group.get("evidence_samples", [])[:2]), cell_format)
            worksheet.set_row(row, 44)
            row += 1
        if not alert_groups:
            worksheet.merge_range("G34:K34", "No priority action generated from alerts.", cell_format)

        worksheet.freeze_panes(3, 0)

    def _write_client_summary_xlsxwriter(
        self,
        score_result: ScoreResult,
        sia4010_results: Dict[str, Any],
        rooms_data: List[Any],
        alert_groups: List[Dict[str, Any]],
    ):
        """Write a concise client/manager summary with safe claim wording."""
        worksheet = self.workbook.add_worksheet("CLIENT SUMMARY")
        worksheet.hide_gridlines(2)
        worksheet.set_tab_color("#1F4E78")

        title_format = self.workbook.add_format({
            "bold": True,
            "font_size": 18,
            "font_color": "#FFFFFF",
            "bg_color": "#1F2937",
            "align": "left",
            "valign": "vcenter",
        })
        section_format = self.workbook.add_format({
            "bold": True,
            "font_color": "#FFFFFF",
            "bg_color": "#1F4E78",
            "border": 1,
            "border_color": "#D7E5E2",
        })
        cell_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top", "border_color": "#D7E5E2"})
        note_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top", "bg_color": "#FFF7E6", "border_color": "#E8C66A"})
        number_format = self.workbook.add_format({"border": 1, "num_format": "#,##0.0", "border_color": "#D7E5E2"})
        count_format = self.workbook.add_format({"border": 1, "num_format": "#,##0", "border_color": "#D7E5E2"})
        fail_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top", "bg_color": "#FDECEA", "font_color": "#9C0006"})
        pass_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top", "bg_color": "#E2EFDA", "font_color": "#375623"})

        alerts_count = self._count_alerts_by_severity(score_result.alerts)
        evidence = sia4010_results.get("evidence", {}) or {}
        evidence_present = sum(1 for item in SIA4010_REQUIRED_EVIDENCE if self._has_sia4010_evidence(evidence, item))
        p1_groups = [group for group in alert_groups if group.get("priority") == "P1"]
        total_area = sum(self._safe_float(getattr(room, "area", 0.0)) for room in rooms_data)
        blocked_sia4010_tests = self._count_blocked_sia4010_tests(sia4010_results)

        worksheet.merge_range("A1:H1", "Client / Manager Summary", title_format)
        worksheet.merge_range(
            "A2:H3",
            "Professional readiness statement for the active VE model. This page is intentionally conservative: it separates automated SIA 380/2 checks from official SIA 4010 validation evidence.",
            note_format,
        )

        worksheet.write("A5", "Current decision", section_format)
        worksheet.merge_range("B5:H6", self._dashboard_verdict(score_result, sia4010_results, rooms_data), fail_format if p1_groups or blocked_sia4010_tests else pass_format)

        worksheet.write("A8", "KPI", section_format)
        worksheet.write("B8", "Value", section_format)
        worksheet.write("C8", "Interpretation", section_format)
        kpis = [
            ("SIA 380/2 automated score", float(score_result.compliance_score or 0.0), "Weighted automated indicator only; it is not a full certificate.", number_format),
            ("Model health score", float(score_result.health_score or 0.0), "Data completeness and model quality indicator.", number_format),
            ("Rooms analysed", len(rooms_data), "Thermal rooms/zones extracted from VE.", count_format),
            ("Floor area analysed (m2)", total_area, "Sum of extracted room areas.", number_format),
            ("P1 action groups", len(p1_groups), "Priority groups to treat before client compliance wording.", count_format),
            ("SIA 4010 evidence", evidence_present, f"Official evidence families detected out of {len(SIA4010_REQUIRED_EVIDENCE)}.", count_format),
            ("SIA 4010 blocked tests", blocked_sia4010_tests, "Tests remain blocked until official evidence is complete and reviewed.", count_format),
            ("High + critical alerts", alerts_count.get("Critical", 0) + alerts_count.get("High", 0), "Blocking or near-blocking review items.", count_format),
        ]
        row = 8
        for label, value, interpretation, value_format in kpis:
            row += 1
            worksheet.write(row, 0, label, cell_format)
            worksheet.write(row, 1, value, value_format)
            worksheet.write(row, 2, interpretation, cell_format)

        worksheet.write("A19", "Safe claim", section_format)
        worksheet.write("B19", "Use / avoid", section_format)
        worksheet.write("C19", "Reason", section_format)
        claim_rows = [
            ("Use", "Automated SIA 380/2 readiness review for directly extracted VE data.", "Supported by the implemented checks and requirement matrix."),
            ("Use", "SIA 4010 evidence readiness matrix.", "The script scans evidence presence and keeps official tests NOT_CHECKABLE without proof."),
            ("Avoid", "This model is fully SIA compliant.", "Current P1 items remain open and several MSP checks are not implemented yet."),
            ("Avoid", "The software/model is SIA 4010 validated.", "Official SIA test files, candidate outputs, reference comparisons and validation class confirmation are missing."),
        ]
        for offset, claim in enumerate(claim_rows, start=20):
            worksheet.write_row(offset, 0, claim, cell_format)

        worksheet.write("A27", "Immediate next decision", section_format)
        worksheet.write("B27", "Owner", section_format)
        worksheet.write("C27", "Evidence expected", section_format)
        next_rows = self._client_next_decision_rows(p1_groups, sia4010_results)
        for offset, item in enumerate(next_rows, start=28):
            worksheet.write_row(offset, 0, item, cell_format)

        worksheet.set_column("A:A", 28)
        worksheet.set_column("B:B", 20)
        worksheet.set_column("C:H", 32)
        worksheet.freeze_panes(8, 0)

    def _write_preflight_xlsxwriter(self, preflight_checks: List[Dict[str, Any]], rooms_data: List[Any], sia4010_results: Dict[str, Any]):
        """Write execution readiness checks for the VE Run-button workflow."""
        worksheet = self.workbook.add_worksheet("PREFLIGHT")
        worksheet.hide_gridlines(2)
        worksheet.set_tab_color("#F59E0B")

        header_format = self.workbook.add_format(EXCEL_FORMATS["header"])
        subheader_format = self.workbook.add_format(EXCEL_FORMATS["subheader"])
        cell_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top", "border_color": "#D7E5E2"})
        pass_format = self.workbook.add_format({"bg_color": "#E2EFDA", "font_color": "#375623", "border": 1, "bold": True, "align": "center"})
        warning_format = self.workbook.add_format({"bg_color": "#FFF2CC", "font_color": "#7F6000", "border": 1, "bold": True, "align": "center"})
        fail_format = self.workbook.add_format({"bg_color": "#FDECEA", "font_color": "#C00000", "border": 1, "bold": True, "align": "center"})
        info_format = self.workbook.add_format({"bg_color": "#D9EAF7", "font_color": "#1F4E78", "border": 1, "bold": True, "align": "center"})
        number_format = self.workbook.add_format({"border": 1, "num_format": "#,##0", "border_color": "#D7E5E2"})

        checks = preflight_checks or self._fallback_preflight_checks(rooms_data, sia4010_results)
        status_counts = Counter(str(check.get("status", "UNKNOWN")) for check in checks)

        worksheet.merge_range("A1:G1", "VE Run Preflight - Execution Readiness", header_format)
        worksheet.merge_range(
            "A2:G2",
            "Ces controles indiquent si le rapport peut etre interprete avec confiance. "
            "Un FAIL ici ne signifie pas forcement non-conformite SIA: cela peut indiquer une extraction ou une preuve manquante.",
            cell_format,
        )

        worksheet.write("A4", "KPI", header_format)
        kpis = [
            ("Checks", len(checks)),
            ("PASS", status_counts.get("PASS", 0)),
            ("WARNING", status_counts.get("WARNING", 0)),
            ("FAIL", status_counts.get("FAIL", 0)),
            ("INFO/NOT_CHECKABLE", status_counts.get("INFO", 0) + status_counts.get("NOT_CHECKABLE", 0)),
        ]
        for offset, (label, value) in enumerate(kpis, start=5):
            worksheet.write(offset, 0, label, subheader_format)
            worksheet.write(offset, 1, value, number_format)

        start_row = 11
        worksheet.write_row(start_row, 0, ["Status", "Check", "Observed", "Why it matters", "Action", "Owner", "Source"], header_format)
        row = start_row + 1
        for check in checks:
            status = str(check.get("status", "UNKNOWN"))
            status_format = self._preflight_status_format(status, pass_format, warning_format, fail_format, info_format, cell_format)
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
    def _fallback_preflight_checks(rooms_data: List[Any], sia4010_results: Dict[str, Any]) -> List[Dict[str, Any]]:
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
    def _preflight_status_format(status: str, pass_format: Any, warning_format: Any, fail_format: Any, info_format: Any, cell_format: Any) -> Any:
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

    def _write_p1_remediation_xlsxwriter(self, alert_groups: List[Dict[str, Any]], sia4010_results: Dict[str, Any]):
        """Write an actionable remediation table for manager-critical P1 items."""
        worksheet = self.workbook.add_worksheet("P1 REMEDIATION")
        worksheet.hide_gridlines(2)
        worksheet.set_tab_color("#C00000")

        header_format = self.workbook.add_format(EXCEL_FORMATS["header"])
        subheader_format = self.workbook.add_format(EXCEL_FORMATS["subheader"])
        cell_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top", "border_color": "#D7E5E2"})
        p1_format = self.workbook.add_format({"bg_color": "#F4CCCC", "font_color": "#9C0006", "border": 1, "bold": True, "align": "center"})
        number_format = self.workbook.add_format({"border": 1, "num_format": "#,##0", "border_color": "#D7E5E2"})
        area_format = self.workbook.add_format({"border": 1, "num_format": "#,##0.0", "border_color": "#D7E5E2"})
        decimal_format = self.workbook.add_format({"border": 1, "num_format": "0.000", "border_color": "#D7E5E2"})
        gap_format = self.workbook.add_format({"border": 1, "num_format": "+0.000;-0.000;0.000", "border_color": "#D7E5E2"})

        p1_groups = [group for group in alert_groups if group.get("priority") == "P1"]
        evidence = sia4010_results.get("evidence", {}) or {}
        evidence_present = sum(1 for item in SIA4010_REQUIRED_EVIDENCE if self._has_sia4010_evidence(evidence, item))

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
        worksheet.write("B7", sum(int(group.get("count", 0) or 0) for group in p1_groups), number_format)
        worksheet.write("A8", "SIA 4010 evidence families", subheader_format)
        worksheet.write("B8", f"{evidence_present}/{len(SIA4010_REQUIRED_EVIDENCE)}", cell_format)

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
            if "SIA4010" in rule:
                current_value = float(evidence_present)
            gap_value = self._p1_gap_for_values(rule, current_value, limit_value)

            worksheet.write(row, 0, group.get("priority", "P1"), p1_format)
            worksheet.write(row, 1, group.get("category", ""), cell_format)
            worksheet.write(row, 2, group.get("construction", ""), cell_format)
            worksheet.write(row, 3, group.get("rule", ""), cell_format)
            worksheet.write(row, 4, group.get("count", 0), number_format)
            worksheet.write(row, 5, group.get("affected_area", 0.0), area_format)
            self._write_optional_number(worksheet, row, 6, current_value, decimal_format, cell_format)
            self._write_optional_number(worksheet, row, 7, limit_value, decimal_format, cell_format)
            self._write_optional_number(worksheet, row, 8, gap_value, gap_format, cell_format)
            worksheet.write(row, 9, self._p1_decision_for_group(group), cell_format)
            worksheet.write(row, 10, self._action_for_alert_group(group), cell_format)
            worksheet.write(row, 11, self._p1_evidence_needed_for_group(group), cell_format)
            worksheet.write(row, 12, self._p1_owner_for_group(group), cell_format)
            worksheet.write(row, 13, self._status_for_alert_group(group), cell_format)
            worksheet.set_row(row, 52)
            row += 1

        if not p1_groups:
            worksheet.merge_range(start_row + 1, 0, start_row + 1, len(headers) - 1, "No P1 group detected in the current run.", cell_format)
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

    def _write_assumptions_limits_xlsxwriter(
        self,
        score_result: ScoreResult,
        sia4010_results: Dict[str, Any],
        rooms_data: List[Any],
    ):
        """Write explicit assumptions and limitations for audit-safe delivery."""
        worksheet = self.workbook.add_worksheet("ASSUMPTIONS LIMITS")
        worksheet.hide_gridlines(2)
        worksheet.set_tab_color("#7F6000")

        header_format = self.workbook.add_format(EXCEL_FORMATS["header"])
        subheader_format = self.workbook.add_format(EXCEL_FORMATS["subheader"])
        cell_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top", "border_color": "#D7E5E2"})
        warning_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top", "bg_color": "#FFF2CC", "font_color": "#7F6000"})
        blocker_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top", "bg_color": "#FDECEA", "font_color": "#9C0006", "bold": True})
        number_format = self.workbook.add_format({"border": 1, "num_format": "#,##0.0", "border_color": "#D7E5E2"})

        evidence = sia4010_results.get("evidence", {}) or {}
        classified_evidence_count = int(evidence.get("classified_file_count", 0) or 0)
        blocked_sia4010_tests = self._count_blocked_sia4010_tests(sia4010_results)

        worksheet.merge_range("A1:F1", "Assumptions, Limits and Certification Guardrails", header_format)
        worksheet.merge_range(
            "A2:F3",
            "This sheet is part of the professional QA layer. It explains what the report can support today and which claims must remain blocked until missing VE data or official SIA evidence is provided.",
            cell_format,
        )

        worksheet.write("A5", "KPI", header_format)
        worksheet.write("B5", "Value", header_format)
        worksheet.write("C5", "Meaning", header_format)
        kpis = [
            ("SIA 380/2 automated score", float(score_result.compliance_score or 0.0), "Automated/partial checks only."),
            ("Model health score", float(score_result.health_score or 0.0), "Data quality and completeness indicator."),
            ("Rooms analysed", len(rooms_data), "Extracted from the active VE model."),
            ("SIA 4010 classified evidence files", classified_evidence_count, "Official-looking files detected and classified by evidence family."),
            ("SIA 4010 blocked tests", blocked_sia4010_tests, "Tests still blocked until official evaluation evidence is complete and reviewed."),
        ]
        for row, (label, value, meaning) in enumerate(kpis, start=6):
            worksheet.write(row, 0, label, subheader_format)
            worksheet.write(row, 1, value, number_format)
            worksheet.write(row, 2, meaning, cell_format)

        headers = ["Status", "Assumption / limitation", "Why it matters", "Impact on claim", "Mitigation", "Source"]
        start_row = 14
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
        ]
        for offset, row_values in enumerate(rows, start=start_row + 1):
            status_format = blocker_format if row_values[0] == "BLOCKER" else warning_format if row_values[0] in {"REVIEW", "MSP GAP"} else cell_format
            worksheet.write(offset, 0, row_values[0], status_format)
            for col, value in enumerate(row_values[1:], start=1):
                worksheet.write(offset, col, value, cell_format)
            worksheet.set_row(offset, 48)

        worksheet.autofilter(start_row, 0, start_row + len(rows), len(headers) - 1)
        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:A", 16)
        worksheet.set_column("B:E", 42)
        worksheet.set_column("F:F", 36)

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
        worksheet.set_tab_color("#64748B")

        header_format = self.workbook.add_format(EXCEL_FORMATS["header"])
        subheader_format = self.workbook.add_format(EXCEL_FORMATS["subheader"])
        cell_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top", "border_color": "#D7E5E2"})
        info_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top", "bg_color": "#EAF3F8", "border_color": "#9CC2E5"})
        number_format = self.workbook.add_format({"border": 1, "num_format": "#,##0.0", "border_color": "#D7E5E2"})

        evidence = sia4010_results.get("evidence", {}) or {}
        evidence_summary = evidence.get("summary", {}) if isinstance(evidence, dict) else {}
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_area = sum(self._safe_float(getattr(room, "area", 0.0)) for room in rooms_data)
        preflight_counts = Counter(str(item.get("status", "UNKNOWN")) for item in preflight_checks)

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
            ("Standards scope", "SIA 380/2:2022 FR; SIA 4010:2023 FR"),
            ("Rooms analysed", len(rooms_data)),
            ("Floor area analysed (m2)", total_area),
            ("SIA 380/2 automated score", float(score_result.compliance_score or 0.0)),
            ("Model health score", float(score_result.health_score or 0.0)),
            ("SIA 4010 official validation score", float(sia4010_results.get("score", 0.0) or 0.0)),
            ("SIA 4010 evidence readiness score", float(sia4010_results.get("readiness_score", 0.0) or 0.0)),
            ("SIA 4010 evidence status", evidence_summary.get("status", "UNKNOWN")),
            ("SIA 4010 validation class", evidence_summary.get("validation_class") or "Not confirmed"),
            ("SIA 4010 evidence families", f"{evidence_summary.get('present_count', 0)}/{evidence_summary.get('required_count', len(SIA4010_REQUIRED_EVIDENCE))}"),
            ("APS/Vista status", dynamic_results.get("status", "NOT_CHECKABLE")),
            ("Selected APS file", dynamic_results.get("selected_aps_file") or "None"),
            ("APS files detected", len(dynamic_results.get("aps_files", []) or [])),
            ("Preflight PASS/WARNING/FAIL/NOT_CHECKABLE", f"{preflight_counts.get('PASS', 0)}/{preflight_counts.get('WARNING', 0)}/{preflight_counts.get('FAIL', 0)}/{preflight_counts.get('NOT_CHECKABLE', 0)}"),
        ]

        worksheet.write("A5", "Field", subheader_format)
        worksheet.write("B5", "Value", subheader_format)
        for row_index, (label, value) in enumerate(metadata_rows, start=6):
            worksheet.write(row_index, 0, label, cell_format)
            if isinstance(value, float):
                worksheet.write(row_index, 1, value, number_format)
            else:
                worksheet.write(row_index, 1, value, cell_format)

        row = 25
        worksheet.write(row, 0, "Official Evidence Family", subheader_format)
        worksheet.write(row, 1, "Status", subheader_format)
        worksheet.write(row, 2, "Detected Files", subheader_format)
        row += 1
        for item in SIA4010_REQUIRED_EVIDENCE:
            key = self._evidence_key_for_required_item(item)
            files = evidence.get(key, {}).get("files", []) if isinstance(evidence.get(key), dict) else []
            worksheet.write(row, 0, item, cell_format)
            worksheet.write(row, 1, "PRESENT" if self._has_sia4010_evidence(evidence, item) else "MISSING", cell_format)
            worksheet.write(
                row,
                2,
                self._compact_join(
                    [file_data.get("path") or file_data.get("name", "") for file_data in files],
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
            ("SIA 380/2", "Only implemented direct checks can be read as automated findings; partial and missing evidence remain reviewer items."),
            ("SIA 4010", "Official validation requires SIA test specifications, official evaluation workbooks, candidate results, reference comparisons and class confirmation."),
            ("Missing data", "Missing or non-comparable data must never be treated as PASS."),
            ("Report wording", "Use readiness/audit wording until every blocker and official evidence requirement is reviewed."),
        ]
        for label, text in guardrails:
            row += 1
            worksheet.write(row, 0, label, cell_format)
            worksheet.write(row, 1, text, cell_format)

        worksheet.set_column("A:A", 34)
        worksheet.set_column("B:B", 48)
        worksheet.set_column("C:F", 40)
        worksheet.freeze_panes(5, 0)

    def _write_summary_xlsxwriter(self, score_result: ScoreResult):
        """Écrit l'onglet SUMMARY avec xlsxwriter."""
        worksheet = self.workbook.add_worksheet("SUMMARY")

        # Styles
        header_format = self.workbook.add_format(EXCEL_FORMATS["header"])
        subheader_format = self.workbook.add_format(EXCEL_FORMATS["subheader"])
        score_format = self.workbook.add_format(EXCEL_FORMATS["score"])
        cell_format = self.workbook.add_format({"border": 1})

        # Titre
        worksheet.merge_range("A1:F1", "Swiss Compliance Checker - Rapport de Conformité", header_format)
        worksheet.merge_range("A2:F2", f"Généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subheader_format)

        # KPI
        worksheet.write("A4", "KPI", header_format)
        worksheet.write("A5", "SIA 380/2 Automated Compliance Indicator:", subheader_format)
        worksheet.write("B5", score_result.compliance_score, score_format)
        worksheet.write("A6", "Health Score (Qualité du Modèle):", subheader_format)
        worksheet.write("B6", score_result.health_score, score_format)

        # Scores détaillés
        worksheet.write("A8", "Scores Détaillés par Catégorie", header_format)
        row = 9
        for category, score in score_result.detailed_scores.items():
            worksheet.write(row, 0, category, subheader_format)
            worksheet.write(row, 1, score, cell_format)
            row += 1

        # Nombre d'alertes
        alerts_count = self._count_alerts_by_severity(score_result.alerts)
        row += 1
        worksheet.write(row, 0, "Nombre d'erreurs critiques:", subheader_format)
        worksheet.write(row, 1, alerts_count.get("Critical", 0), cell_format)
        worksheet.write(row + 1, 0, "Nombre d'avertissements:", subheader_format)
        worksheet.write(row + 1, 1, alerts_count.get("High", 0) + alerts_count.get("Medium", 0), cell_format)
        worksheet.write(row + 2, 0, "Nombre d'informations:", subheader_format)
        worksheet.write(row + 2, 1, alerts_count.get("Low", 0), cell_format)

        # Ajuster la largeur des colonnes
        worksheet.set_column("A:A", 30)
        worksheet.set_column("B:B", 20)

    def _write_compliance_results_xlsxwriter(self, sia3802_results: Dict[str, Any], sia4010_results: Dict[str, Any]):
        """Écrit l'onglet COMPLIANCE RESULTS avec xlsxwriter."""
        worksheet = self.workbook.add_worksheet("COMPLIANCE RESULTS")

        # Styles
        header_format = self.workbook.add_format(EXCEL_FORMATS["header"])
        pass_format = self.workbook.add_format(EXCEL_FORMATS["pass"])
        warning_format = self.workbook.add_format(EXCEL_FORMATS["warning"])
        fail_format = self.workbook.add_format(EXCEL_FORMATS["fail"])
        cell_format = self.workbook.add_format({"border": 1})
        not_checkable_format = self.workbook.add_format({"bg_color": "#D9EAF7", "font_color": "#1F4E78", "border": 1, "bold": True})

        # Titre
        worksheet.merge_range("A1:F1", "Résultats de Conformité SIA", header_format)

        # Résultats SIA 380/2
        worksheet.write("A3", "SIA 380/2", header_format)
        row = 4
        for category, data in sia3802_results.items():
            if category != "alerts":
                worksheet.write(row, 0, category, header_format)
                worksheet.write(row, 1, data.get("score", 0), cell_format)
                row += 1

        # Résultats SIA 4010
        worksheet.write(row + 1, 0, "SIA 4010", header_format)
        worksheet.write(row + 2, 0, "Score Global", header_format)
        worksheet.write(row + 2, 1, sia4010_results.get("score", 0), cell_format)

        row += 3
        worksheet.write(row, 0, "Tests SIA 4010", header_format)
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

        # Ajuster la largeur des colonnes
        worksheet.set_column("A:A", 30)
        worksheet.set_column("B:B", 20)

    def _write_sia_requirements_xlsxwriter(self, sia3802_results: Dict[str, Any], sia4010_results: Dict[str, Any]):
        """Write the auditable SIA requirement matrix used by the checker."""
        worksheet = self.workbook.add_worksheet("SIA REQUIREMENTS")

        header_format = self.workbook.add_format(EXCEL_FORMATS["header"])
        subheader_format = self.workbook.add_format(EXCEL_FORMATS["subheader"])
        cell_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top"})
        note_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top", "bg_color": "#EAF3F8"})
        pass_format = self.workbook.add_format({"bg_color": "#E2EFDA", "font_color": "#375623", "border": 1, "bold": True})
        fail_format = self.workbook.add_format({"bg_color": "#FDECEA", "font_color": "#C00000", "border": 1, "bold": True})
        partial_format = self.workbook.add_format({"bg_color": "#FFF2CC", "font_color": "#7F6000", "border": 1, "bold": True})
        not_checkable_format = self.workbook.add_format({"bg_color": "#D9EAF7", "font_color": "#1F4E78", "border": 1, "bold": True})

        worksheet.merge_range("A1:L1", "SIA 380/2 + SIA 4010 Requirement Matrix", header_format)
        worksheet.merge_range(
            "A2:L2",
            "Cette matrice liste les criteres issus des PDF/config, leur statut d'automatisation et la prochaine action. "
            "Elle evite de transformer une donnee non verifiable en faux PASS.",
            note_format,
        )

        all_alerts = list(sia3802_results.get("alerts", []) or []) + list(sia4010_results.get("alerts", []) or [])
        rows = [
            self._build_requirement_matrix_row(requirement, all_alerts)
            for requirement in SIA_COMPLIANCE_REQUIREMENT_MATRIX
        ]
        status_counts = Counter(row["status"] for row in rows)

        worksheet.write("A4", "KPI", header_format)
        kpis = [
            ("Requirements listed", len(rows)),
            ("Automated PASS/CHECK", status_counts.get("PASS", 0) + status_counts.get("PARTIAL_CHECK", 0)),
            ("Failing or missing", status_counts.get("FAIL", 0) + status_counts.get("MISSING", 0)),
            ("Not checkable / not implemented", status_counts.get("NOT_CHECKABLE", 0) + status_counts.get("NOT_IMPLEMENTED", 0)),
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
            worksheet.write(row, 6, item["criterion"], cell_format)
            worksheet.write(row, 7, item["limit"], cell_format)
            worksheet.write(row, 8, item["unit"], cell_format)
            worksheet.write(row, 9, item["target"], cell_format)
            worksheet.write(row, 10, item["source"], cell_format)
            worksheet.write(row, 11, item["next_action"], cell_format)
            worksheet.set_row(row, 52)
            row += 1

        worksheet.autofilter(start_row, 0, max(start_row, row - 1), len(headers) - 1)
        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:A", 18)
        worksheet.set_column("B:C", 16)
        worksheet.set_column("D:F", 20)
        worksheet.set_column("G:G", 42)
        worksheet.set_column("H:J", 18)
        worksheet.set_column("K:K", 42)
        worksheet.set_column("L:L", 54)

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

        header_format = self.workbook.add_format(EXCEL_FORMATS["header"])
        subheader_format = self.workbook.add_format(EXCEL_FORMATS["subheader"])
        cell_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top"})
        note_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top", "bg_color": "#EAF3F8"})
        number_format = self.workbook.add_format({"border": 1, "num_format": "#,##0"})
        available_format = self.workbook.add_format({"bg_color": "#E2EFDA", "font_color": "#375623", "border": 1, "bold": True})
        partial_format = self.workbook.add_format({"bg_color": "#FFF2CC", "font_color": "#7F6000", "border": 1, "bold": True})
        missing_format = self.workbook.add_format({"bg_color": "#FDECEA", "font_color": "#C00000", "border": 1, "bold": True})
        not_checkable_format = self.workbook.add_format({"bg_color": "#D9EAF7", "font_color": "#1F4E78", "border": 1, "bold": True})

        rows = self._build_sia_data_coverage_rows(
            sia3802_results,
            sia4010_results,
            rooms_data,
            preflight_checks,
            dynamic_results,
        )
        status_counts = Counter(row["coverage_status"] for row in rows)

        worksheet.merge_range("A1:N1", "SIA 380/2 + SIA 4010 Data Coverage Matrix", header_format)
        worksheet.merge_range(
            "A2:N2",
            "This sheet explains what is currently evidenced by the VE model/API, what requires APS/Vista outputs, "
            "and what must remain external official SIA 4010 evidence before any final compliance claim.",
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

        header_format = self.workbook.add_format(EXCEL_FORMATS["header"])
        subheader_format = self.workbook.add_format(EXCEL_FORMATS["subheader"])
        cell_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top"})
        note_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top", "bg_color": "#EAF3F8"})
        p1_format = self.workbook.add_format({"bg_color": "#FDECEA", "font_color": "#C00000", "border": 1, "bold": True})
        p2_format = self.workbook.add_format({"bg_color": "#FFF2CC", "font_color": "#7F6000", "border": 1, "bold": True})
        p3_format = self.workbook.add_format({"bg_color": "#E2EFDA", "font_color": "#375623", "border": 1, "bold": True})

        coverage_rows = self._build_sia_data_coverage_rows(
            sia3802_results,
            sia4010_results,
            rooms_data,
            preflight_checks,
            dynamic_results,
        )
        request_rows = [
            row for row in coverage_rows
            if row["coverage_status"] in {"PARTIAL", "MISSING", "NOT_CHECKABLE"}
        ]

        worksheet.merge_range("A1:J1", "Input Request - Data and Evidence Needed", header_format)
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
            priority_format = p1_format if priority == "P1" else (p2_format if priority == "P2" else p3_format)
            worksheet.write(row, 0, priority, priority_format)
            worksheet.write(row, 1, item["coverage_status"], cell_format)
            worksheet.write(row, 2, item["standard"], cell_format)
            worksheet.write(row, 3, item["validation_scope"], cell_format)
            worksheet.write(row, 4, item["data_needed"], cell_format)
            worksheet.write(row, 5, item["preferred_format"], cell_format)
            worksheet.write(row, 6, item["destination"], cell_format)
            worksheet.write(row, 7, item["criterion"], cell_format)
            worksheet.write(row, 8, item["owner"], cell_format)
            worksheet.write(row, 9, item["source"], cell_format)
            worksheet.set_row(row, 58)
            row += 1

        if not request_rows:
            worksheet.write(row, 0, "No missing input detected by the current automated coverage matrix.", cell_format)

        worksheet.autofilter(start_row, 0, max(start_row, row - 1), len(headers) - 1)
        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:B", 14)
        worksheet.set_column("C:D", 24)
        worksheet.set_column("E:H", 44)
        worksheet.set_column("I:I", 22)
        worksheet.set_column("J:J", 42)

    def _write_dynamic_results_xlsxwriter(self, dynamic_results: Dict[str, Any]):
        """Write APS/Vista dynamic result indicators when IESVE exposes them."""
        worksheet = self.workbook.add_worksheet("DYNAMIC RESULTS")

        header_format = self.workbook.add_format(EXCEL_FORMATS["header"])
        subheader_format = self.workbook.add_format(EXCEL_FORMATS["subheader"])
        cell_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top"})
        note_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top", "bg_color": "#EAF3F8"})
        number_format = self.workbook.add_format({"border": 1, "num_format": "#,##0.00"})
        integer_format = self.workbook.add_format({"border": 1, "num_format": "#,##0"})
        status_format = self.workbook.add_format({"bg_color": "#D9EAF7", "font_color": "#1F4E78", "border": 1, "bold": True})

        worksheet.merge_range("A1:J1", "APS/Vista Dynamic Results", header_format)
        worksheet.merge_range(
            "A2:J2",
            "These values are readiness indicators extracted from APS/Vista when IESVE ResultsReader is available. "
            "They support SIA 380/2 and SIA 4010 checks but do not replace official SIA 4010 comparison workbooks.",
            note_format,
        )

        overview = [
            ("Status", dynamic_results.get("status", "NOT_CHECKABLE")),
            ("Selected APS file", dynamic_results.get("selected_aps_file", "")),
            ("APS files detected", len(dynamic_results.get("aps_files", []) or [])),
            ("Total area used by APS results (m2)", dynamic_results.get("total_area_m2")),
            ("Heating demand (kWh/m2)", dynamic_results.get("heating_kwh_m2")),
            ("Cooling demand (kWh/m2)", dynamic_results.get("cooling_kwh_m2")),
            ("Occupied hours > 26 C", dynamic_results.get("occupied_hours_above_26")),
            ("Occupied hours > 27 C", dynamic_results.get("occupied_hours_above_27")),
            ("Notes", dynamic_results.get("notes", "")),
        ]
        worksheet.write("A4", "Metric", header_format)
        worksheet.write("B4", "Value", header_format)
        for offset, (label, value) in enumerate(overview, start=5):
            worksheet.write(offset, 0, label, subheader_format)
            if isinstance(value, (int, float)):
                worksheet.write(offset, 1, value, number_format)
            else:
                worksheet.write(offset, 1, str(value or ""), status_format if label == "Status" else cell_format)

        start_row = 16
        headers = [
            "Room",
            "Room ID",
            "Area m2",
            "Heating kWh",
            "Cooling kWh",
            "Peak heating W",
            "Peak cooling W",
            "Hours > 26 C",
            "Hours > 27 C",
            "Source notes",
        ]
        worksheet.write_row(start_row, 0, headers, header_format)

        row = start_row + 1
        room_rows = dynamic_results.get("rooms", []) or []
        if room_rows:
            for item in room_rows:
                worksheet.write(row, 0, item.get("room_name", ""), cell_format)
                worksheet.write(row, 1, str(item.get("room_id", "") or ""), cell_format)
                self._write_optional_number(worksheet, row, 2, item.get("area_m2"), number_format, cell_format)
                self._write_optional_number(worksheet, row, 3, item.get("heating_kwh"), number_format, cell_format)
                self._write_optional_number(worksheet, row, 4, item.get("cooling_kwh"), number_format, cell_format)
                self._write_optional_number(worksheet, row, 5, item.get("peak_heating_w"), integer_format, cell_format)
                self._write_optional_number(worksheet, row, 6, item.get("peak_cooling_w"), integer_format, cell_format)
                self._write_optional_number(worksheet, row, 7, item.get("occupied_hours_above_26"), number_format, cell_format)
                self._write_optional_number(worksheet, row, 8, item.get("occupied_hours_above_27"), number_format, cell_format)
                worksheet.write(row, 9, item.get("source_notes", ""), cell_format)
                row += 1
        else:
            worksheet.write(row, 0, "No room-level dynamic result was readable in this run.", cell_format)

        worksheet.autofilter(start_row, 0, max(start_row, row - 1), len(headers) - 1)
        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:B", 24)
        worksheet.set_column("C:I", 16)
        worksheet.set_column("J:J", 52)

    def _write_sia4010_readiness_xlsxwriter(self, sia4010_results: Dict[str, Any], rooms_data: List[Any]):
        """Write a SIA 4010 readiness matrix backed by the PDF traceability."""
        worksheet = self.workbook.add_worksheet("SIA4010 READINESS")

        header_format = self.workbook.add_format(EXCEL_FORMATS["header"])
        subheader_format = self.workbook.add_format(EXCEL_FORMATS["subheader"])
        cell_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top"})
        note_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top", "bg_color": "#EAF3F8"})
        percent_format = self.workbook.add_format({"border": 1, "num_format": "0.0%", "valign": "top"})
        number_format = self.workbook.add_format({"border": 1, "num_format": "#,##0", "valign": "top"})
        ready_format = self.workbook.add_format({"bg_color": "#E2EFDA", "font_color": "#375623", "border": 1, "bold": True})
        partial_format = self.workbook.add_format({"bg_color": "#FFF2CC", "font_color": "#7F6000", "border": 1, "bold": True})
        missing_format = self.workbook.add_format({"bg_color": "#FDECEA", "font_color": "#C00000", "border": 1, "bold": True})
        not_checkable_format = self.workbook.add_format({"bg_color": "#D9EAF7", "font_color": "#1F4E78", "border": 1, "bold": True})

        rows = self._build_sia4010_readiness_rows(sia4010_results, rooms_data)
        avg_readiness = sum(row["readiness_ratio"] for row in rows) / len(rows) if rows else 0.0
        not_checkable_count = sum(1 for row in rows if row["official_status"] == "NOT_CHECKABLE")
        validation_class = sia4010_results.get("validation_class") or "Non selectionnee"
        evidence = sia4010_results.get("evidence", {}) or {}
        evidence_present_count = sum(1 for item in SIA4010_REQUIRED_EVIDENCE if self._has_sia4010_evidence(evidence, item))

        worksheet.merge_range("A1:K1", "SIA 4010 Readiness - Validation Evidence Matrix", header_format)
        worksheet.merge_range(
            "A2:K2",
            "Cet onglet separe la readiness du modele VE et la validation officielle SIA 4010. "
            "Sans fichiers officiels SIA, les tests restent NOT_CHECKABLE.",
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
            worksheet.write(row, 4, item["ve_status"], self._sia4010_status_format(item["ve_status"], ready_format, partial_format, missing_format, not_checkable_format, cell_format))
            worksheet.write(row, 5, item["official_status"], self._sia4010_status_format(item["official_status"], ready_format, partial_format, missing_format, not_checkable_format, cell_format))
            worksheet.write(row, 6, item["present"], cell_format)
            worksheet.write(row, 7, item["missing"], cell_format)
            worksheet.write(row, 8, item["official_evidence"], cell_format)
            worksheet.write(row, 9, item["source"], cell_format)
            worksheet.write(row, 10, item["next_action"], cell_format)
            worksheet.set_row(row, 62)
            row += 1

        worksheet.autofilter(start_row, 0, max(start_row, row - 1), len(headers) - 1)

        evidence_start = row + 2
        worksheet.write(evidence_start, 0, "Official SIA 4010 evidence checklist", header_format)
        worksheet.write_row(evidence_start + 1, 0, ["Evidence item", "Status", "Comment"], subheader_format)
        evidence_row = evidence_start + 2
        for item in SIA4010_REQUIRED_EVIDENCE:
            status = "PRESENT" if self._has_sia4010_evidence(evidence, item) else "MISSING"
            worksheet.write(evidence_row, 0, item, cell_format)
            worksheet.write(evidence_row, 1, status, ready_format if status == "PRESENT" else missing_format)
            worksheet.write(
                evidence_row,
                2,
                "A fournir depuis les documents/fichiers officiels SIA 4010." if status == "MISSING" else "Preuve referencee dans sia4010_results.",
                cell_format,
            )
            evidence_row += 1

        files_start = evidence_row + 2
        worksheet.write(files_start, 0, "Detected evidence files", header_format)
        worksheet.write_row(files_start + 1, 0, ["File", "Relative path", "Size (KB)", "Detected family"], subheader_format)
        files_row = files_start + 2
        evidence_files = evidence.get("files", []) if isinstance(evidence, dict) else []
        if evidence_files:
            for file_data in evidence_files:
                detected_families = self._sia4010_detected_families_for_file(evidence, file_data)
                worksheet.write(files_row, 0, file_data.get("name", ""), cell_format)
                worksheet.write(files_row, 1, file_data.get("path", ""), cell_format)
                size_bytes = file_data.get("size_bytes")
                size_kb = float(size_bytes) / 1024.0 if isinstance(size_bytes, (int, float)) else None
                self._write_optional_number(worksheet, files_row, 2, size_kb, number_format, cell_format)
                worksheet.write(files_row, 3, detected_families, cell_format)
                files_row += 1
        else:
            worksheet.write(files_row, 0, "No file detected in sia4010_evidence.", cell_format)
            worksheet.write(files_row, 1, evidence.get("evidence_dir", "sia4010_evidence") if isinstance(evidence, dict) else "sia4010_evidence", cell_format)
            worksheet.write(files_row, 2, "", cell_format)
            worksheet.write(files_row, 3, "NOT_CHECKABLE", not_checkable_format)
            files_row += 1

        system_start = files_row + 2
        worksheet.write(system_start, 0, "System data families required by SIA 4010", header_format)
        worksheet.write_row(system_start + 1, 0, ["System family", "Required data", "PDF / table source", "Current extraction status"], subheader_format)
        system_row = system_start + 2
        for family, data in SIA4010_SYSTEM_REQUIREMENT_SOURCES.items():
            worksheet.write(system_row, 0, family, cell_format)
            worksheet.write(system_row, 1, "; ".join(data.get("requires", [])), cell_format)
            worksheet.write(system_row, 2, f"{data.get('pages', '')}; {data.get('table_range', '')}", cell_format)
            worksheet.write(system_row, 3, self._sia4010_system_status(family, rooms_data, sia4010_results), cell_format)
            worksheet.set_row(system_row, 48)
            system_row += 1

        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:A", 12)
        worksheet.set_column("B:B", 18)
        worksheet.set_column("C:C", 36)
        worksheet.set_column("D:D", 16)
        worksheet.set_column("E:F", 18)
        worksheet.set_column("G:H", 44)
        worksheet.set_column("I:I", 46)
        worksheet.set_column("J:J", 34)
        worksheet.set_column("K:K", 52)

    def _write_action_plan_xlsxwriter(self, alert_groups: List[Dict[str, Any]]):
        """Write a prioritized action plan based on grouped alerts."""
        worksheet = self.workbook.add_worksheet("ACTION PLAN")

        header_format = self.workbook.add_format(EXCEL_FORMATS["header"])
        subheader_format = self.workbook.add_format(EXCEL_FORMATS["subheader"])
        cell_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top"})
        p1_format = self.workbook.add_format({"bg_color": "#F4CCCC", "font_color": "#9C0006", "border": 1, "bold": True})
        p2_format = self.workbook.add_format({"bg_color": "#FFF2CC", "font_color": "#7F6000", "border": 1, "bold": True})
        p3_format = self.workbook.add_format({"bg_color": "#DEEAF1", "font_color": "#1F4E78", "border": 1, "bold": True})
        area_format = self.workbook.add_format({"border": 1, "num_format": "#,##0.0"})
        number_format = self.workbook.add_format({"border": 1, "num_format": "#,##0"})

        worksheet.merge_range("A1:L1", "Action Plan - Prioritised Compliance Follow-up", header_format)
        worksheet.merge_range(
            "A2:L2",
            "Cet onglet transforme les alertes en actions auditables. Les scores restent inchanges.",
            cell_format,
        )

        worksheet.write("A4", "KPI", header_format)
        worksheet.write("A5", "Action groups", subheader_format)
        worksheet.write("B5", len(alert_groups), number_format)
        worksheet.write("A6", "Raw alerts represented", subheader_format)
        worksheet.write("B6", sum(group["count"] for group in alert_groups), number_format)
        worksheet.write("A7", "P1 groups", subheader_format)
        worksheet.write("B7", sum(1 for group in alert_groups if group["priority"] == "P1"), number_format)

        headers = [
            "Priority",
            "Priority score",
            "Category",
            "Construction",
            "Type",
            "Rule",
            "Issue count",
            "Max severity",
            "Affected area (m2)",
            "Action",
            "Evidence samples",
            "Status",
        ]
        start_row = 10
        worksheet.write_row(start_row, 0, headers, header_format)

        row = start_row + 1
        for group in alert_groups:
            priority_format = p1_format if group["priority"] == "P1" else p2_format if group["priority"] == "P2" else p3_format
            worksheet.write(row, 0, group["priority"], priority_format)
            worksheet.write(row, 1, group["priority_score"], number_format)
            worksheet.write(row, 2, group["category"], cell_format)
            worksheet.write(row, 3, group["construction"], cell_format)
            worksheet.write(row, 4, group["object_type"], cell_format)
            worksheet.write(row, 5, group["rule"], cell_format)
            worksheet.write(row, 6, group["count"], number_format)
            worksheet.write(row, 7, group["max_severity"], cell_format)
            worksheet.write(row, 8, group["affected_area"], area_format)
            worksheet.write(row, 9, self._action_for_alert_group(group), cell_format)
            worksheet.write(row, 10, "; ".join(group["evidence_samples"]), cell_format)
            worksheet.write(row, 11, self._status_for_alert_group(group), cell_format)
            row += 1

        worksheet.autofilter(start_row, 0, max(start_row, row - 1), len(headers) - 1)
        worksheet.freeze_panes(start_row + 1, 0)
        worksheet.set_column("A:A", 12)
        worksheet.set_column("B:B", 14)
        worksheet.set_column("C:C", 16)
        worksheet.set_column("D:D", 24)
        worksheet.set_column("E:E", 16)
        worksheet.set_column("F:F", 30)
        worksheet.set_column("G:I", 16)
        worksheet.set_column("J:J", 52)
        worksheet.set_column("K:K", 58)
        worksheet.set_column("L:L", 18)

    def _write_alert_summary_xlsxwriter(self, alert_groups: List[Dict[str, Any]]):
        """Write grouped alerts to reduce repetitive raw alert rows."""
        worksheet = self.workbook.add_worksheet("ALERT SUMMARY")

        header_format = self.workbook.add_format(EXCEL_FORMATS["header"])
        cell_format = self.workbook.add_format({"border": 1, "text_wrap": True, "valign": "top"})
        number_format = self.workbook.add_format({"border": 1, "num_format": "#,##0"})
        area_format = self.workbook.add_format({"border": 1, "num_format": "#,##0.0"})
        decimal_format = self.workbook.add_format({"border": 1, "num_format": "0.000"})

        worksheet.merge_range("A1:O1", "Alert Summary - Grouped Technical Findings", header_format)
        worksheet.merge_range(
            "A2:O2",
            "Les alertes repetitives sont regroupees par categorie, construction, type et regle.",
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
            worksheet.write(row, 5, group["severity_counts"].get("Critical", 0), number_format)
            worksheet.write(row, 6, group["severity_counts"].get("High", 0), number_format)
            worksheet.write(row, 7, group["severity_counts"].get("Medium", 0), number_format)
            worksheet.write(row, 8, group["severity_counts"].get("Low", 0), number_format)
            worksheet.write(row, 9, group["count"], number_format)
            worksheet.write(row, 10, group["affected_area"], area_format)
            self._write_optional_number(worksheet, row, 11, group.get("avg_u"), decimal_format, cell_format)
            self._write_optional_number(worksheet, row, 12, group.get("avg_g"), decimal_format, cell_format)
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
        """Écrit l'onglet ALERTS avec xlsxwriter."""
        worksheet = self.workbook.add_worksheet("ALERTS")

        # Styles
        header_format = self.workbook.add_format(EXCEL_FORMATS["header"])
        critical_format = self.workbook.add_format(EXCEL_FORMATS["critical"])
        high_format = self.workbook.add_format(EXCEL_FORMATS["fail"])
        medium_format = self.workbook.add_format(EXCEL_FORMATS["warning"])
        low_format = self.workbook.add_format({"bg_color": "#DEEAF1", "border": 1})
        cell_format = self.workbook.add_format({"border": 1})

        # Titre
        worksheet.merge_range("A1:F1", "Liste des Alertes", header_format)

        # En-tête
        headers = ["Catégorie", "Règle", "Description", "Sévérité", "Valeur / preuve", "Recommandation"]
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, header_format)

        # Données
        row = 3
        for alert in alerts:
            worksheet.write(row, 0, alert.category, cell_format)
            worksheet.write(row, 1, alert.rule, cell_format)
            worksheet.write(row, 2, alert.description, cell_format)
            worksheet.write(row, 3, alert.severity.value, cell_format)
            worksheet.write(row, 4, self._format_alert_data(alert), cell_format)
            worksheet.write(row, 5, alert.recommendation, cell_format)

            # Appliquer le format de couleur en fonction de la sévérité
            if alert.severity == Severity.CRITICAL:
                worksheet.write(row, 3, alert.severity.value, critical_format)
            elif alert.severity == Severity.HIGH:
                worksheet.write(row, 3, alert.severity.value, high_format)
            elif alert.severity == Severity.MEDIUM:
                worksheet.write(row, 3, alert.severity.value, medium_format)
            else:
                worksheet.write(row, 3, alert.severity.value, low_format)
            row += 1

        # Ajuster la largeur des colonnes
        worksheet.set_column("A:A", 15)
        worksheet.set_column("B:B", 20)
        worksheet.set_column("C:C", 40)
        worksheet.set_column("D:D", 15)
        worksheet.set_column("E:E", 38)
        worksheet.set_column("F:F", 40)

    def _write_data_quality_xlsxwriter(self, alerts: List[Alert], rooms_data: List[Any]):
        """Ecrit un onglet de synthese qualite des donnees et couverture API."""
        worksheet = self.workbook.add_worksheet("DATA QUALITY")

        header_format = self.workbook.add_format(EXCEL_FORMATS["header"])
        subheader_format = self.workbook.add_format(EXCEL_FORMATS["subheader"])
        cell_format = self.workbook.add_format({"border": 1})
        warning_format = self.workbook.add_format(EXCEL_FORMATS["warning"])
        fail_format = self.workbook.add_format(EXCEL_FORMATS["fail"])
        percent_format = self.workbook.add_format({"border": 1, "num_format": "0.0%"})

        severity_counts = self._count_alerts_by_severity(alerts)
        category_counts = Counter(alert.category for alert in alerts)
        rule_counts = Counter(alert.rule for alert in alerts)
        missing_alerts = [
            alert for alert in alerts
            if "MISSING" in str(alert.rule).upper()
            or "NOT_CHECKABLE" in str(alert.rule).upper()
            or "non disponible" in str(alert.description).lower()
        ]
        total_area = sum(self._safe_float(getattr(room, "area", 0.0)) for room in rooms_data)
        total_volume = sum(self._safe_float(getattr(room, "volume", 0.0)) for room in rooms_data)

        worksheet.merge_range("A1:F1", "Data Quality & API Coverage", header_format)
        worksheet.write("A3", "KPI", header_format)
        kpis = [
            ("Rooms analysed", len(rooms_data)),
            ("Total area (m2)", total_area),
            ("Total volume (m3)", total_volume),
            ("Total alerts", len(alerts)),
            ("Critical alerts", severity_counts.get("Critical", 0)),
            ("Warnings", severity_counts.get("High", 0) + severity_counts.get("Medium", 0)),
            ("Information", severity_counts.get("Low", 0)),
            ("Missing / not checkable data", len(missing_alerts)),
        ]
        for row, (label, value) in enumerate(kpis, start=3):
            worksheet.write(row, 0, label, subheader_format)
            worksheet.write(row, 1, value, cell_format)

        worksheet.write("D3", "Interpretation", header_format)
        interpretation = (
            "Le score doit etre lu avec prudence si beaucoup d'alertes sont MISSING "
            "ou NOT_CHECKABLE: cela indique d'abord un manque de preuve/extraction, "
            "pas necessairement une non-conformite physique du batiment."
        )
        worksheet.write("D4", interpretation, warning_format if missing_alerts else cell_format)
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
        worksheet.write_row(start_row + 1, 0, ["Room ID", "Name", "Area (m2)", "WWR", "Average wall U-value", "Comment"], subheader_format)
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
            worksheet.write(row, 4, avg_u, cell_format)
            worksheet.write(row, 5, "; ".join(comment), fail_format if comment else cell_format)
            row += 1

        worksheet.set_column("A:A", 22)
        worksheet.set_column("B:B", 16)
        worksheet.set_column("C:C", 14)
        worksheet.set_column("D:D", 34)
        worksheet.set_column("E:E", 12)
        worksheet.set_column("F:F", 42)

    def _write_detailed_scores_xlsxwriter(self, detailed_scores: Dict[str, float]):
        """Écrit l'onglet DETAILED SCORES avec xlsxwriter."""
        worksheet = self.workbook.add_worksheet("DETAILED SCORES")

        # Styles
        header_format = self.workbook.add_format(EXCEL_FORMATS["header"])
        cell_format = self.workbook.add_format({"border": 1})

        # Titre
        worksheet.merge_range("A1:B1", "Scores Détaillés", header_format)

        # En-tête
        worksheet.write("A2", "Catégorie", header_format)
        worksheet.write("B2", "Score (0-100)", header_format)

        # Données
        row = 3
        for category, score in detailed_scores.items():
            worksheet.write(row, 0, category, cell_format)
            worksheet.write(row, 1, score, cell_format)
            row += 1

        # Ajuster la largeur des colonnes
        worksheet.set_column("A:A", 30)
        worksheet.set_column("B:B", 20)

    def _write_rooms_xlsxwriter(self, rooms_data: List[Any]):
        """Écrit l'onglet ROOMS avec xlsxwriter."""
        worksheet = self.workbook.add_worksheet("ROOMS")

        # Styles
        header_format = self.workbook.add_format(EXCEL_FORMATS["header"])
        cell_format = self.workbook.add_format({"border": 1})

        # Titre
        worksheet.merge_range("A1:F1", "Données des Pièces", header_format)

        # En-tête
        headers = ["ID", "Nom", "Surface (m²)", "Volume (m³)", "WWR", "U-value Moyenne (W/m²K)"]
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, header_format)

        # Données
        row = 3
        for room in rooms_data:
            worksheet.write(row, 0, room.id, cell_format)
            worksheet.write(row, 1, room.name, cell_format)
            worksheet.write(row, 2, room.area, cell_format)
            worksheet.write(row, 3, room.volume, cell_format)
            worksheet.write(row, 4, self._calculate_wwr(room), cell_format)
            worksheet.write(row, 5, self._calculate_average_u_value(room, "wall"), cell_format)
            row += 1

        # Ajuster la largeur des colonnes
        worksheet.set_column("A:A", 10)
        worksheet.set_column("B:B", 20)
        worksheet.set_column("C:C", 15)
        worksheet.set_column("D:D", 15)
        worksheet.set_column("E:E", 10)
        worksheet.set_column("F:F", 25)

    # =============================================================================
    # Méthodes utilitaires
    # =============================================================================

    @staticmethod
    def _count_alerts_by_severity(alerts: List[Alert]) -> Dict[str, int]:
        """
        Compte le nombre d'alertes par niveau de sévérité.
        
        Args:
            alerts: Liste des alertes.
        
        Returns:
            Dictionnaire avec les comptes par sévérité.
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
        stats = self._build_sia4010_model_stats(rooms_data, sia4010_results)
        evidence = sia4010_results.get("evidence", {}) or {}
        dynamic_payload = dynamic_results or sia4010_results.get("dynamic_results", {}) or {}
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
            rows.append({
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
            })

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

            rows.append({
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
            })

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
            if total <= 0:
                return "MISSING", f"No {label} detected."
            if count >= total:
                return "AVAILABLE", f"{count}/{total} {label} available."
            if count > 0:
                return "PARTIAL", f"{count}/{total} {label} available."
            return "MISSING", f"0/{total} {label} available."

        if key == "project_climate":
            active_project_status = preflight_status_by_check.get("Active VE project", "")
            if active_project_status == "PASS":
                return "PARTIAL", "Active project detected; weather/climate basis still needs explicit confirmation."
            return "MISSING", "No active project evidence in preflight checks."
        if key == "rooms":
            count = int(stats.get("rooms", 0) or 0)
            return ("AVAILABLE", f"{count} thermal room(s) extracted.") if count else ("MISSING", "No thermal room extracted.")
        if key == "use_category":
            count = int(stats.get("rooms", 0) or 0)
            if count:
                return "PARTIAL", f"{count} room(s) extracted; SIA 2024 category mapping still needs confirmation."
            return "MISSING", "No room data available for SIA 2024 mapping."
        if key == "external_surfaces":
            count = int(stats.get("external_surfaces", 0) or 0)
            return ("AVAILABLE", f"{count} external surface(s) extracted.") if count else ("MISSING", "No external surface extracted.")
        if key == "surface_u_values":
            return availability(
                int(stats.get("surface_u_values", 0) or 0),
                int(stats.get("external_surfaces", 0) or 0),
                "external surface U-values",
            )
        if key == "window_u_values":
            return availability(
                int(stats.get("window_u_values", 0) or 0),
                int(stats.get("external_windows", 0) or 0),
                "external window U-values",
            )
        if key == "window_g_values":
            return availability(
                int(stats.get("window_g_values", 0) or 0),
                int(stats.get("external_windows", 0) or 0),
                "external window g-values",
            )
        if key in {"visible_transmittance", "frame_fraction", "solar_protection", "schedules", "ventilation_control", "ahu_heat_recovery", "cooling_efficiency", "heating_efficiency"}:
            return "MISSING", "Not extracted by the current IESVE API mapping; external evidence or a new extractor is required."
        if key == "infiltration":
            rooms = int(stats.get("rooms", 0) or 0)
            converted = int(stats.get("rooms_with_infiltration_m3_h_m2", 0) or 0)
            raw = int(stats.get("rooms_with_infiltration", 0) or 0)
            if converted:
                return availability(converted, rooms, "rooms with converted infiltration")
            if raw:
                return "PARTIAL", f"{raw}/{rooms} room(s) expose raw infiltration; unit conversion still needs confirmation."
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
            if lighting_rooms:
                return "PARTIAL", f"{lighting_rooms} room(s) expose lighting gains; control strategy still missing."
            return "MISSING", "No lighting power/control evidence extracted."
        if key == "dynamic_aps":
            status = str(dynamic_results.get("status", "NOT_CHECKABLE") or "NOT_CHECKABLE").upper()
            aps_count = len(dynamic_results.get("aps_files", []) or [])
            selected = dynamic_results.get("selected_aps_file") or "none"
            if status == "AVAILABLE":
                return "AVAILABLE", f"{aps_count} APS file(s) detected; selected {selected}; room results readable."
            if status == "PARTIAL":
                return "PARTIAL", f"{aps_count} APS file(s) detected; selected {selected}; room results incomplete."
            return "NOT_CHECKABLE", dynamic_results.get("notes") or f"{aps_count} APS file(s) detected; ResultsReader did not provide room results."
        if key == "hourly_temperatures":
            return availability(
                int(stats.get("dynamic_temperature_rows", 0) or 0),
                int(stats.get("dynamic_room_rows", 0) or 0),
                "dynamic room temperature/occupancy indicators",
            )
        if key == "heating_cooling_demands":
            return availability(
                int(stats.get("dynamic_demand_rows", 0) or 0),
                int(stats.get("dynamic_room_rows", 0) or 0),
                "dynamic heating/cooling demand indicators",
            )

        evidence_prefix = "evidence_"
        if key.startswith(evidence_prefix):
            family = key[len(evidence_prefix):]
            family_data = evidence.get(family, {}) if isinstance(evidence, dict) else {}
            present = bool(family_data.get("present")) if isinstance(family_data, dict) else bool(family_data)
            files = family_data.get("files", []) if isinstance(family_data, dict) else []
            if present:
                return "AVAILABLE", f"{len(files)} matching evidence file(s) detected for {family}."
            return "MISSING", f"No matching evidence file detected for {family}."

        return "NOT_CHECKABLE", "No coverage rule is implemented for this key yet."

    @staticmethod
    def _coverage_status_format(status: str, available_format: Any, partial_format: Any, missing_format: Any, not_checkable_format: Any, cell_format: Any) -> Any:
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
        if status in {"MISSING", "NOT_CHECKABLE"} and domain in {"dynamic results", "ventilation", "cooling", "heating"}:
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

    def _build_sia4010_readiness_rows(self, sia4010_results: Dict[str, Any], rooms_data: List[Any]) -> List[Dict[str, Any]]:
        """Build one readiness row per SIA 4010 validation test."""
        stats = self._build_sia4010_model_stats(rooms_data, sia4010_results)
        tests = sia4010_results.get("tests", {}) or {}
        required_evidence = self._compact_join(SIA4010_REQUIRED_EVIDENCE, max_chars=300)

        checks_by_test = {
            "test_1": [
                ("zones/rooms extracted", stats["rooms"] > 0),
                ("external envelope surfaces extracted", stats["external_surfaces"] > 0),
                ("surface U-values extracted", stats["surface_u_values"] > 0),
                ("external window/opening data extracted", stats["external_openings"] > 0),
                ("official test model/reference outputs attached", False),
            ],
            "test_2": [
                ("external glazing extracted", stats["external_windows"] > 0),
                ("window g-values extracted", stats["window_g_values"] > 0),
                ("solar protection type/category documented", False),
                ("solar protection control strategy documented", False),
                ("official CH climate/use/infiltration diagnostic attached", False),
            ],
            "test_3": [
                ("lighting power extracted", stats["rooms_with_lighting"] > 0),
                ("daylight control strategy documented", False),
                ("SIA 387/4 lighting control type documented", False),
                ("lighting energy outputs available", False),
                ("official test 3 evaluation file attached", False),
            ],
            "test_4": [
                ("HVAC systems extracted", stats["rooms_with_hvac"] > 0),
                ("ventilation/airflow data extracted", stats["rooms_with_ventilation"] > 0),
                ("cooling/heating coil outputs available", stats["dynamic_demand_rows"] > 0 or stats["cooling_demand_available"] or stats["heating_demand_available"]),
                ("temperature hourly outputs available", stats["dynamic_temperature_rows"] > 0),
                ("CO2 hourly outputs available or manually evidenced", False),
                ("official amphitheatre test/evaluation attached", False),
            ],
            "test_5": [
                ("HVAC/AHU systems extracted", stats["rooms_with_hvac"] > 0),
                ("ventilation data extracted", stats["rooms_with_ventilation"] > 0),
                ("fan control identifier documented", False),
                ("heat/moisture recovery type documented", False),
                ("humidifier type/control documented", False),
                ("official test 5 variant/evaluation attached", False),
            ],
            "test_6": [
                ("ventilation systems extracted", stats["rooms_with_ventilation"] > 0),
                ("constant airflow/stage data documented", False),
                ("heat recovery data documented", False),
                ("restaurant/kitchen overflow represented", False),
                ("official test 6 evaluation file attached", False),
            ],
            "test_7": [
                ("HVAC systems extracted", stats["rooms_with_hvac"] > 0),
                ("heating/cooling demand outputs available", stats["dynamic_demand_rows"] > 0 or stats["heating_demand_available"] or stats["cooling_demand_available"]),
                ("final energy by system/carrier available", stats["final_energy_available"]),
                ("pump/fan/auxiliary energy available", False),
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
                if test_status in {"PASS", "VALIDATED", "WARNING", "EVIDENCE_INCOMPLETE", "READY_FOR_OFFICIAL_REVIEW"}
                else "NOT_CHECKABLE"
            )
            rows.append({
                "test": test_name,
                "classes": self._classes_for_sia4010_test(test_name),
                "domain": requirement.get("domain", tests.get(test_name, {}).get("description", "")),
                "readiness_ratio": readiness_ratio,
                "ve_status": ve_status,
                "official_status": official_status,
                "present": self._compact_join(present, empty="Aucune donnee cle actuellement prouvee"),
                "missing": self._compact_join(missing, empty="Aucun blocker detecte dans la matrice actuelle"),
                "official_evidence": required_evidence,
                "source": requirement.get("source", ""),
                "next_action": requirement.get("next_action", ""),
            })
        return rows

    @staticmethod
    def _build_sia4010_model_stats(rooms_data: List[Any], sia4010_results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize currently extracted VE data relevant to SIA 4010 readiness."""
        surfaces = [surface for room in rooms_data for surface in getattr(room, "surfaces", [])]
        openings = [opening for room in rooms_data for opening in getattr(room, "openings", [])]
        external_surfaces = [surface for surface in surfaces if getattr(surface, "is_external", False)]
        external_openings = [opening for opening in openings if getattr(opening, "is_external", False)]
        external_windows = [
            opening for opening in external_openings
            if str(getattr(opening, "opening_type", "") or "").lower() in {"window", "glazing", "ext_glazing", "4"}
        ]
        rooms_with_lighting = [
            room for room in rooms_data
            if (getattr(room, "internal_gains", {}) or {}).get("lighting") is not None
        ]
        rooms_with_equipment = [
            room for room in rooms_data
            if (getattr(room, "internal_gains", {}) or {}).get("equipment") is not None
        ]
        rooms_with_ventilation = [
            room for room in rooms_data
            if getattr(room, "ventilation_rate", None) is not None
        ]
        rooms_with_infiltration = [
            room for room in rooms_data
            if getattr(room, "infiltration_rate", None) is not None
        ]
        rooms_with_infiltration_m3_h_m2 = [
            room for room in rooms_data
            if getattr(room, "infiltration_m3_h_m2", None) is not None
        ]
        rooms_with_hvac = [
            room for room in rooms_data
            if getattr(room, "hvac_systems", None)
        ]
        energy = sia4010_results.get("energy", {}) or {}
        dynamic_results = sia4010_results.get("dynamic_results", {}) or {}
        dynamic_room_rows = dynamic_results.get("rooms", []) or []
        dynamic_demand_rows = [
            row for row in dynamic_room_rows
            if row.get("heating_kwh") is not None or row.get("cooling_kwh") is not None
        ]
        dynamic_temperature_rows = [
            row for row in dynamic_room_rows
            if row.get("occupied_hours_above_26") is not None or row.get("occupied_hours_above_27") is not None
        ]
        return {
            "rooms": len(rooms_data),
            "external_surfaces": len(external_surfaces),
            "surface_u_values": sum(1 for surface in external_surfaces if getattr(surface, "u_value", None) is not None),
            "external_openings": len(external_openings),
            "external_windows": len(external_windows),
            "window_u_values": sum(1 for opening in external_windows if getattr(opening, "u_value", None) is not None),
            "window_g_values": sum(1 for opening in external_windows if getattr(opening, "solar_factor", None) is not None),
            "rooms_with_lighting": len(rooms_with_lighting),
            "rooms_with_equipment": len(rooms_with_equipment),
            "rooms_with_ventilation": len(rooms_with_ventilation),
            "rooms_with_infiltration": len(rooms_with_infiltration),
            "rooms_with_infiltration_m3_h_m2": len(rooms_with_infiltration_m3_h_m2),
            "rooms_with_hvac": len(rooms_with_hvac),
            "dynamic_room_rows": len(dynamic_room_rows),
            "dynamic_demand_rows": len(dynamic_demand_rows),
            "dynamic_temperature_rows": len(dynamic_temperature_rows),
            "heating_demand_available": energy.get("heating_demand") is not None,
            "cooling_demand_available": energy.get("cooling_demand") is not None,
            "final_energy_available": any(
                energy.get(key) is not None
                for key in ("primary_energy", "co2_emissions", "renewable_energy_share")
            ),
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
        return ", ".join(unique_classes) if unique_classes else "A confirmer"

    @staticmethod
    def _compact_join(items: List[str], empty: str = "", max_chars: int = 260) -> str:
        text = "; ".join(str(item) for item in items if item)
        if not text:
            return empty
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3].rstrip() + "..."

    @staticmethod
    def _sia4010_status_format(status: str, ready_format: Any, partial_format: Any, missing_format: Any, not_checkable_format: Any, cell_format: Any) -> Any:
        status_upper = str(status or "").upper()
        if status_upper in {"READY", "PASS", "VALIDATED", "PRESENT"}:
            return ready_format
        if status_upper in {"PARTIAL", "WARNING", "READY_FOR_OFFICIAL_REVIEW"}:
            return partial_format
        if status_upper in {"NOT_CHECKABLE"}:
            return not_checkable_format
        if status_upper in {"MISSING", "FAIL", "EVIDENCE_INCOMPLETE"}:
            return missing_format
        return cell_format

    @staticmethod
    def _has_sia4010_evidence(evidence: Dict[str, Any], evidence_item: str) -> bool:
        """Best-effort check for future evidence payloads without requiring a strict schema."""
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
    def _sia4010_detected_families_for_file(evidence: Dict[str, Any], file_data: Dict[str, Any]) -> str:
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

    def _sia4010_system_status(self, family: str, rooms_data: List[Any], sia4010_results: Dict[str, Any]) -> str:
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
        worksheet.merge_range(f"{start_col_letters}{start_row}:{end_col_letters}{start_row}", title, title_format)
        worksheet.merge_range(f"{start_col_letters}{start_row + 1}:{end_col_letters}{start_row + 2}", value, value_format)
        worksheet.merge_range(f"{start_col_letters}{start_row + 3}:{end_col_letters}{end_row}", note, note_format)

    @staticmethod
    def _dashboard_score_rows(score_result: ScoreResult) -> List[List[Any]]:
        rows = [
            ["Compliance indicator", float(score_result.compliance_score or 0.0)],
            ["Model health", float(score_result.health_score or 0.0)],
        ]
        for key, value in list(score_result.detailed_scores.items())[:10]:
            if isinstance(value, (int, float)):
                label = str(key).replace("SIA3802_", "380/2 ").replace("SIA3801_", "380/2 ").replace("SIA4010_", "4010 ").replace("_", " ").title()
                rows.append([label[:34], float(value)])
        return rows

    def _dashboard_requirement_status_rows(self, sia3802_results: Dict[str, Any], sia4010_results: Dict[str, Any]) -> List[List[Any]]:
        all_alerts = list(sia3802_results.get("alerts", []) or []) + list(sia4010_results.get("alerts", []) or [])
        rows = [
            self._build_requirement_matrix_row(requirement, all_alerts)
            for requirement in SIA_COMPLIANCE_REQUIREMENT_MATRIX
        ]
        counts = Counter(row["status"] for row in rows)
        order = ["PASS", "PARTIAL_CHECK", "READINESS_ONLY", "FAIL", "MISSING", "NOT_CHECKABLE", "NOT_IMPLEMENTED"]
        return [[status, counts.get(status, 0)] for status in order if counts.get(status, 0)]

    @staticmethod
    def _count_blocked_sia4010_tests(sia4010_results: Dict[str, Any]) -> int:
        """Count SIA 4010 tests that still cannot support an official claim."""
        blocked_statuses = {"NOT_CHECKABLE", "EVIDENCE_INCOMPLETE"}
        return sum(
            1 for test in sia4010_results.get("tests", {}).values()
            if str(test.get("status", "") or "").upper() in blocked_statuses
        )

    @staticmethod
    def _dashboard_verdict(score_result: ScoreResult, sia4010_results: Dict[str, Any], rooms_data: List[Any]) -> str:
        critical_count = sum(1 for alert in score_result.alerts if alert.severity == Severity.CRITICAL)
        high_count = sum(1 for alert in score_result.alerts if alert.severity == Severity.HIGH)
        blocked_tests = ExcelReportGenerator._count_blocked_sia4010_tests(sia4010_results)
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
        return "READY FOR DETAILED REVIEW: no critical/high alert detected and SIA 4010 tests are no longer blocked by missing evidence."

    def _build_requirement_matrix_row(self, requirement: Dict[str, Any], alerts: List[Alert]) -> Dict[str, Any]:
        """Build a report row for one SIA requirement without inventing verdicts."""
        automation = str(requirement.get("automation", "") or "")
        implemented_rule = str(requirement.get("implemented_rule", "") or "")
        related_alerts = self._find_requirement_alerts(requirement, alerts)

        if automation in {"NOT_IMPLEMENTED", ""}:
            status = "NOT_IMPLEMENTED"
        elif automation == "READINESS_ONLY":
            status = "NOT_CHECKABLE" if related_alerts else "READINESS_ONLY"
        elif related_alerts:
            if any("MISSING" in str(alert.rule or "").upper() for alert in related_alerts):
                status = "MISSING"
            elif any("NOT_CHECKABLE" in str(alert.rule or "").upper() for alert in related_alerts):
                status = "NOT_CHECKABLE"
            else:
                status = "FAIL"
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
            "criterion": requirement.get("criterion", ""),
            "limit": requirement.get("limit", ""),
            "unit": requirement.get("unit", ""),
            "target": requirement.get("target", ""),
            "source": requirement.get("source", ""),
            "next_action": next_action,
        }

    @staticmethod
    def _find_requirement_alerts(requirement: Dict[str, Any], alerts: List[Alert]) -> List[Alert]:
        rule_name = str(requirement.get("implemented_rule", "") or "").upper()
        requirement_id = str(requirement.get("id", "") or "").upper()
        if not rule_name and not requirement_id:
            return []

        matches = []
        for alert in alerts:
            alert_rule = str(alert.rule or "").upper()
            if rule_name and alert_rule == rule_name:
                matches.append(alert)
                continue
            if requirement_id.startswith("SIA3802_AIRTIGHTNESS") and alert_rule.startswith("SIA3802_INFILTRATION"):
                matches.append(alert)
                continue
            if requirement_id.startswith("SIA4010") and alert_rule.startswith("SIA4010"):
                matches.append(alert)
        return matches

    @staticmethod
    def _requirement_status_format(status: str, pass_format: Any, fail_format: Any, partial_format: Any, not_checkable_format: Any, cell_format: Any) -> Any:
        status_upper = str(status or "").upper()
        if status_upper in {"PASS"}:
            return pass_format
        if status_upper in {"PARTIAL_CHECK", "READINESS_ONLY"}:
            return partial_format
        if status_upper in {"NOT_CHECKABLE", "NOT_IMPLEMENTED"}:
            return not_checkable_format
        if status_upper in {"FAIL", "MISSING"}:
            return fail_format
        return cell_format

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
            if self._severity_rank(alert.severity.value) < self._severity_rank(group["max_severity"]):
                group["max_severity"] = alert.severity.value

            evidence = self._format_alert_data(alert)
            if evidence and len(group["evidence_samples"]) < 3:
                group["evidence_samples"].append(evidence)

        for group in groups.values():
            group["avg_u"] = group["u_sum"] / group["u_count"] if group["u_count"] else None
            group["avg_g"] = group["g_sum"] / group["g_count"] if group["g_count"] else None
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
        if rule in {"SIA3802_WWR", "SIA3801_WWR"} or hasattr(data, "surfaces") or hasattr(data, "openings"):
            return "ROOM_LEVEL"
        return "NO_CONSTRUCTION"

    @staticmethod
    def _get_alert_object_type(alert: Alert) -> str:
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
        data = getattr(alert, "data", None)
        if isinstance(data, dict):
            value = data.get("area")
        else:
            value = getattr(data, "area", None)
        return ExcelReportGenerator._safe_float(value, 0.0) or 0.0

    @staticmethod
    def _get_alert_numeric(alert: Alert, key: str) -> Optional[float]:
        data = getattr(alert, "data", None)
        if isinstance(data, dict):
            value = data.get(key)
        else:
            value = getattr(data, key, None)
        if value in (None, ""):
            return None
        return ExcelReportGenerator._safe_float(value, None)

    @staticmethod
    def _write_optional_number(worksheet: Any, row: int, col: int, value: Optional[float], number_format: Any, cell_format: Any):
        if value is None:
            worksheet.write(row, col, "", cell_format)
        else:
            worksheet.write(row, col, value, number_format)

    @staticmethod
    def _severity_rank(severity_value: str) -> int:
        order = {
            "Critical": 0,
            "High": 1,
            "Medium": 2,
            "Low": 3,
        }
        return order.get(str(severity_value), 4)

    @staticmethod
    def _get_priority(group: Dict[str, Any]) -> str:
        severity = group.get("max_severity", "")
        count = int(group.get("count", 0) or 0)
        rule = str(group.get("rule", "")).upper()
        if severity in {"Critical", "High"} or count >= 20:
            return "P1"
        if severity == "Medium" or "MISSING" in rule or "NOT_CHECKABLE" in rule:
            return "P2"
        return "P3"

    def _get_priority_score(self, group: Dict[str, Any]) -> int:
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
        rule = str(group.get("rule", "")).upper()
        recommendation = str(group.get("recommendation", "") or "")
        if rule in {"SIA3802_SOLAR_FACTOR", "SIA3801_SOLAR_FACTOR"}:
            return (
                "Verifier quelle valeur solaire doit etre retenue pour la methode SIA "
                "(g-value, SHGC, EN 410, effet des protections), puis traiter par construction. "
                + recommendation
            )
        if rule in {"SIA3802_WWR", "SIA3801_WWR"}:
            return "Revoir le ratio vitrage/facade par zone et documenter l'acceptabilite du seuil WWR utilise."
        if "SIA4010" in rule:
            return "Collecter les preuves de validation SIA 4010: cas tests, sorties APS/reference et ecarts acceptables."
        if "MISSING" in rule or "NOT_CHECKABLE" in rule:
            return "Completer la donnee manquante dans VE ou joindre une justification externe auditable."
        return recommendation or "Revoir cet element avec le responsable du modele."

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
            return [(
                "Complete the SIA 4010 official evidence pack before any validation wording.",
                "Compliance reviewer",
                "Official test specs, Excel evaluation workbooks, candidate outputs, reference comparison plots and validation class confirmation.",
            )]

        return [(
            "Submit the completed SIA 4010 evidence pack for official review/sign-off.",
            "Compliance reviewer",
            "Reviewer/sub-commission acceptance or documented validation decision.",
        )]

    @staticmethod
    def _status_for_alert_group(group: Dict[str, Any]) -> str:
        rule = str(group.get("rule", "")).upper()
        if "MISSING" in rule or "NOT_CHECKABLE" in rule or "SIA4010" in rule:
            return "A documenter"
        return "A traiter"

    @staticmethod
    def _p1_current_value_for_group(group: Dict[str, Any]) -> Optional[float]:
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
        current_value = self._p1_current_value_for_group(group)
        limit_value = self._p1_limit_for_group(group)
        return self._p1_gap_for_values(str(group.get("rule", "")).upper(), current_value, limit_value)

    @staticmethod
    def _p1_gap_for_values(rule: str, current_value: Optional[float], limit_value: Optional[float]) -> Optional[float]:
        if current_value is None or limit_value is None:
            return None
        if "SIA4010" in str(rule).upper():
            return limit_value - current_value
        return current_value - limit_value

    @staticmethod
    def _p1_decision_for_group(group: Dict[str, Any]) -> str:
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
        if self.model_analyzer is not None:
            try:
                return self.model_analyzer.calculate_wwr(room)
            except Exception:
                pass
        external_walls = [
            surface for surface in getattr(room, "surfaces", [])
            if getattr(surface, "is_external", False)
            and str(getattr(surface, "surface_type", "") or "").lower() in {"wall", "ext_wall"}
        ]
        wall_area = sum(float(getattr(surface, "area", 0.0) or 0.0) for surface in external_walls)
        window_area = sum(
            float(getattr(opening, "area", 0.0) or 0.0)
            for opening in getattr(room, "openings", [])
            if getattr(opening, "is_external", False)
            and str(getattr(opening, "opening_type", "") or "").lower() in {"window", "glazing", "ext_glazing"}
        )
        return window_area / wall_area if wall_area > 0 else 0.0

    def _calculate_average_u_value(self, room: Any, surface_type: str) -> float:
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
            if str(getattr(surface, "surface_type", "") or "").lower() in {target, f"ext_{target}"}
            and getattr(surface, "u_value", None) is not None
            and float(getattr(surface, "net_area", getattr(surface, "area", 0.0)) or 0.0) > 1e-6
        ]
        total_area = sum(area for _value, area in values)
        return sum(value * area for value, area in values) / total_area if total_area > 0 else 0.0

    def _format_alert_data(self, alert: Alert) -> str:
        """Build a compact evidence string for the alert row."""
        data = getattr(alert, "data", None)
        if data is None:
            return ""

        parts = []
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
            parts.append(f"constructions={','.join(str(item) for item in construction_ids)}")

        if hasattr(data, "u_value") and getattr(data, "u_value") is not None:
            u_value = self._safe_float(getattr(data, "u_value"), None)
            if u_value is not None:
                parts.append(f"U={u_value:.3f} W/m2K")
        if hasattr(data, "solar_factor") and getattr(data, "solar_factor") is not None:
            solar_factor = self._safe_float(getattr(data, "solar_factor"), None)
            if solar_factor is not None:
                parts.append(f"g={solar_factor:.3f}")
        if hasattr(data, "area"):
            parts.append(f"area={self._safe_float(getattr(data, 'area'), 0.0):.2f} m2")
        if hasattr(data, "net_area"):
            parts.append(f"net_area={self._safe_float(getattr(data, 'net_area'), 0.0):.2f} m2")
        if hasattr(data, "surface_type") and getattr(data, "surface_type"):
            parts.append(f"type={getattr(data, 'surface_type')}")
        if hasattr(data, "opening_type") and getattr(data, "opening_type"):
            parts.append(f"type={getattr(data, 'opening_type')}")
        if hasattr(data, "ventilation_rate") and getattr(data, "ventilation_rate") is not None:
            ventilation_rate = self._safe_float(getattr(data, "ventilation_rate"), None)
            if ventilation_rate is not None:
                parts.append(f"ventilation={ventilation_rate:.3f} ach")
        if hasattr(data, "internal_gains"):
            gains = getattr(data, "internal_gains") or {}
            if gains:
                parts.append(
                    "gains="
                    + ",".join(
                        f"{key}:{value:.2f}" for key, value in gains.items()
                        if isinstance(value, (int, float))
                    )
                )
        if isinstance(data, dict):
            for key in ("id", "type", "efficiency", "energy_consumption"):
                value = data.get(key)
                if value not in (None, ""):
                    parts.append(f"{key}={value}")

        if str(alert.rule).upper() in {"SIA3802_WWR", "SIA3801_WWR"} and self.model_analyzer is not None:
            try:
                parts.append(f"WWR={self.model_analyzer.calculate_wwr(data):.1%}")
            except Exception:
                pass

        return "; ".join(part for part in parts if part)
