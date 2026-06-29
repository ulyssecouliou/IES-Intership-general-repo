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

from config import OUTPUT_DIR, EXCEL_REPORT_NAME, EXCEL_FORMATS
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
            if test_data.get("status") == "PASS":
                worksheet.write(row, 1, test_data.get("status"), pass_format)
            elif test_data.get("status") == "WARNING":
                worksheet.write(row, 1, test_data.get("status"), warning_format)
            else:
                worksheet.write(row, 1, test_data.get("status"), fail_format)

        # Ajuster la largeur des colonnes
        worksheet.set_column("A:A", 30)
        worksheet.set_column("B:B", 20)

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
