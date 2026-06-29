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

from config import (
    OUTPUT_DIR,
    EXCEL_REPORT_NAME,
    EXCEL_FORMATS,
    SIA_COMPLIANCE_REQUIREMENT_MATRIX,
    SIA4010_REQUIRED_EVIDENCE,
    SIA4010_SYSTEM_REQUIREMENT_SOURCES,
    SIA4010_TEST_CLASS_COVERAGE,
    SIA4010_TEST_READINESS_REQUIREMENTS,
    SIA4010_VALIDATION_CLASSES,
)
from health_score import ScoreResult
from rule_engine import Alert, Severity

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
        sia3801_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
        rooms_data: Optional[List[Any]] = None,
    ):
        """
        Génère le rapport Excel complet.
        
        Args:
            score_result: Résultat des scores (Compliance Score, Health Score, etc.).
            sia3801_results: Résultats des vérifications SIA 380/2.
            sia4010_results: Résultats des vérifications SIA 4010.
            rooms_data: Données des pièces (optionnel).
        """
        try:
            self._generate_report_xlsxwriter(score_result, sia3801_results, sia4010_results, rooms_data)
            logger.info(f"Rapport Excel généré avec succès: {self.output_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport Excel: {e}")
            if self.workbook:
                self.workbook.close()
            raise

    def _generate_report_xlsxwriter(
        self,
        score_result: ScoreResult,
        sia3801_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
        rooms_data: Optional[List[Any]] = None,
    ):
        """Génère le rapport avec xlsxwriter."""
        alert_groups = self._build_alert_groups(score_result.alerts)
        self._write_summary_xlsxwriter(score_result)
        self._write_action_plan_xlsxwriter(alert_groups)
        self._write_compliance_results_xlsxwriter(sia3801_results, sia4010_results)
        self._write_sia_requirements_xlsxwriter(sia3801_results, sia4010_results)
        self._write_sia4010_readiness_xlsxwriter(sia4010_results, rooms_data or [])
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
        worksheet.write("A5", "Compliance Score (SIA 380/2 + SIA 4010):", subheader_format)
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

    def _write_compliance_results_xlsxwriter(self, sia3801_results: Dict[str, Any], sia4010_results: Dict[str, Any]):
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
        for category, data in sia3801_results.items():
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

    def _write_sia_requirements_xlsxwriter(self, sia3801_results: Dict[str, Any], sia4010_results: Dict[str, Any]):
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

        all_alerts = list(sia3801_results.get("alerts", []) or []) + list(sia4010_results.get("alerts", []) or [])
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

        system_start = evidence_row + 2
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
        total_area = sum(float(getattr(room, "area", 0.0) or 0.0) for room in rooms_data)
        total_volume = sum(float(getattr(room, "volume", 0.0) or 0.0) for room in rooms_data)

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
                ("cooling/heating coil outputs available", stats["cooling_demand_available"] or stats["heating_demand_available"]),
                ("CO2/temperature hourly outputs available", False),
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
                ("heating/cooling demand outputs available", stats["heating_demand_available"] or stats["cooling_demand_available"]),
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
            official_status = test_status if test_status in {"PASS", "VALIDATED", "WARNING"} else "NOT_CHECKABLE"
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
        rooms_with_hvac = [
            room for room in rooms_data
            if getattr(room, "hvac_systems", None)
        ]
        energy = sia4010_results.get("energy", {}) or {}
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
            "rooms_with_hvac": len(rooms_with_hvac),
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
        if status_upper in {"PARTIAL", "WARNING"}:
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
        if rule == "SIA3801_WWR" or hasattr(data, "surfaces") or hasattr(data, "openings"):
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
    def _get_alert_area(alert: Alert) -> float:
        data = getattr(alert, "data", None)
        if isinstance(data, dict):
            value = data.get("area")
        else:
            value = getattr(data, "area", None)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _get_alert_numeric(alert: Alert, key: str) -> Optional[float]:
        data = getattr(alert, "data", None)
        if isinstance(data, dict):
            value = data.get(key)
        else:
            value = getattr(data, key, None)
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

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
        if rule == "SIA3801_SOLAR_FACTOR":
            return (
                "Verifier quelle valeur solaire doit etre retenue pour la methode SIA "
                "(g-value, SHGC, EN 410, effet des protections), puis traiter par construction. "
                + recommendation
            )
        if rule == "SIA3801_WWR":
            return "Revoir le ratio vitrage/facade par zone et documenter l'acceptabilite du seuil WWR utilise."
        if "SIA4010" in rule:
            return "Collecter les preuves de validation SIA 4010: cas tests, sorties APS/reference et ecarts acceptables."
        if "MISSING" in rule or "NOT_CHECKABLE" in rule:
            return "Completer la donnee manquante dans VE ou joindre une justification externe auditable."
        return recommendation or "Revoir cet element avec le responsable du modele."

    @staticmethod
    def _status_for_alert_group(group: Dict[str, Any]) -> str:
        rule = str(group.get("rule", "")).upper()
        if "MISSING" in rule or "NOT_CHECKABLE" in rule or "SIA4010" in rule:
            return "A documenter"
        return "A traiter"

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
            parts.append(f"U={float(getattr(data, 'u_value')):.3f} W/m2K")
        if hasattr(data, "solar_factor") and getattr(data, "solar_factor") is not None:
            parts.append(f"g={float(getattr(data, 'solar_factor')):.3f}")
        if hasattr(data, "area"):
            parts.append(f"area={float(getattr(data, 'area') or 0.0):.2f} m2")
        if hasattr(data, "net_area"):
            parts.append(f"net_area={float(getattr(data, 'net_area') or 0.0):.2f} m2")
        if hasattr(data, "surface_type") and getattr(data, "surface_type"):
            parts.append(f"type={getattr(data, 'surface_type')}")
        if hasattr(data, "opening_type") and getattr(data, "opening_type"):
            parts.append(f"type={getattr(data, 'opening_type')}")
        if hasattr(data, "ventilation_rate") and getattr(data, "ventilation_rate") is not None:
            parts.append(f"ventilation={float(getattr(data, 'ventilation_rate')):.3f} ach")
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

        if str(alert.rule).upper() == "SIA3801_WWR" and self.model_analyzer is not None:
            try:
                parts.append(f"WWR={self.model_analyzer.calculate_wwr(data):.1%}")
            except Exception:
                pass

        return "; ".join(part for part in parts if part)
