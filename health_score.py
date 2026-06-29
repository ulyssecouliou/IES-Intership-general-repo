"""
Calculateur des scores de conformité (Compliance Score et Health Score).
Ce module calcule les scores globaux et détaillés pour le Swiss Compliance Checker.
"""

import logging
from typing import Dict, List, Any
from dataclasses import dataclass, field

from config import CATEGORY_WEIGHTS, SIA4010_TEST_WEIGHTS, PENALTIES
from rule_engine import Alert, Severity

logger = logging.getLogger(__name__)


@dataclass
class ScoreResult:
    """Résultat d'un score de conformité."""
    compliance_score: float  # Score global de conformité (0-100)
    health_score: float      # Score de santé du modèle (0-100)
    detailed_scores: Dict[str, float]  # Scores détaillés par catégorie
    alerts: List[Alert]      # Liste de toutes les alertes


class HealthScoreCalculator:
    """
    Calcule les scores de conformité (Compliance Score et Health Score).
    """

    def __init__(self):
        """Initialise le calculateur de scores."""
        self.compliance_score = 0.0
        self.health_score = 0.0
        self.detailed_scores = {}
        self.alerts = []

    def calculate_scores(
        self,
        sia3801_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
    ) -> ScoreResult:
        """
        Calcule le Compliance Score et le Health Score à partir des résultats SIA 380/2 et SIA 4010.
        
        Args:
            sia3801_results: Résultats des vérifications SIA 380/2.
            sia4010_results: Résultats des vérifications SIA 4010.
        
        Returns:
            Objet ScoreResult contenant tous les scores et alertes.
        """
        # Calculer le Compliance Score (SIA 380/2 + SIA 4010)
        compliance_score = self._calculate_compliance_score(sia3801_results, sia4010_results)

        # Calculer le Health Score (qualité du modèle)
        health_score = self._calculate_health_score(sia3801_results, sia4010_results)

        # Calculer les scores détaillés par catégorie
        detailed_scores = self._calculate_detailed_scores(sia3801_results, sia4010_results)

        # Collecter toutes les alertes
        alerts = sia3801_results.get("alerts", []) + sia4010_results.get("alerts", [])

        return ScoreResult(
            compliance_score=compliance_score,
            health_score=health_score,
            detailed_scores=detailed_scores,
            alerts=alerts,
        )

    def _calculate_compliance_score(
        self,
        sia3801_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
    ) -> float:
        """
        Calcule le Compliance Score global (0-100).
        
        Args:
            sia3801_results: Résultats des vérifications SIA 380/2.
            sia4010_results: Résultats des vérifications SIA 4010.
        
        Returns:
            Score global de conformité (0-100).
        """
        # Score SIA 380/2 (poids = 70%)
        sia3801_score = self._calculate_sia3801_score(sia3801_results)

        # Score SIA 4010 (poids = 30%)
        sia4010_score = sia4010_results.get("score", 0.0)

        # Score global = 70% SIA 380/2 + 30% SIA 4010
        return sia3801_score * 0.7 + sia4010_score * 0.3

    def _calculate_sia3801_score(self, sia3801_results: Dict[str, Any]) -> float:
        """
        Calcule le score SIA 380/2 (0-100).
        
        Args:
            sia3801_results: Résultats des vérifications SIA 380/2.
        
        Returns:
            Score SIA 380/2 (0-100).
        """
        category_scores = []
        for category, weight in CATEGORY_WEIGHTS.items():
            if category in ["envelope", "openings", "ventilation", "gains", "hvac"]:
                category_score = sia3801_results.get(category, {}).get("score", 0.0)
                category_scores.append(category_score * weight)

        total_weight = sum(
            weight for category, weight in CATEGORY_WEIGHTS.items()
            if category in ["envelope", "openings", "ventilation", "gains", "hvac"]
        )
        return sum(category_scores) / total_weight if category_scores else 0.0

    def _calculate_health_score(
        self,
        sia3801_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
    ) -> float:
        """
        Calcule le Health Score (0-100) basé sur la qualité du modèle.
        
        Args:
            sia3801_results: Résultats des vérifications SIA 380/2.
            sia4010_results: Résultats des vérifications SIA 4010.
        
        Returns:
            Score de santé du modèle (0-100).
        """
        # Le Health Score dépend de :
        # 1. Complétude des données (40%)
        # 2. Cohérence des données (30%)
        # 3. Absence d'erreurs critiques (30%)

        completeness_score = self._calculate_completeness_score(sia3801_results)
        consistency_score = self._calculate_consistency_score(sia3801_results)
        critical_errors_score = self._calculate_critical_errors_score(sia3801_results, sia4010_results)

        return (
            completeness_score * 0.4 +
            consistency_score * 0.3 +
            critical_errors_score * 0.3
        )

    def _calculate_completeness_score(self, sia3801_results: Dict[str, Any]) -> float:
        """
        Calcule le score de complétude des données (0-100).
        
        Args:
            sia3801_results: Résultats des vérifications SIA 380/2.
        
        Returns:
            Score de complétude (0-100).
        """
        alerts = sia3801_results.get("alerts", [])
        missing_alerts = [
            alert for alert in alerts
            if self._is_missing_data_alert(alert)
        ]
        return self._score_from_alerts(missing_alerts)

    def _calculate_consistency_score(self, sia3801_results: Dict[str, Any]) -> float:
        """
        Calcule le score de cohérence des données (0-100).
        
        Args:
            sia3801_results: Résultats des vérifications SIA 380/2.
        
        Returns:
            Score de cohérence (0-100).
        """
        category_scores = [
            sia3801_results.get(category, {}).get("score")
            for category in ["envelope", "openings", "ventilation", "gains", "hvac"]
        ]
        numeric_scores = [
            float(score)
            for score in category_scores
            if isinstance(score, (int, float))
        ]
        if not numeric_scores:
            return 0.0
        return sum(numeric_scores) / len(numeric_scores)

    def _calculate_critical_errors_score(
        self,
        sia3801_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
    ) -> float:
        """
        Calcule le score basé sur l'absence d'erreurs critiques (0-100).
        
        Args:
            sia3801_results: Résultats des vérifications SIA 380/2.
            sia4010_results: Résultats des vérifications SIA 4010.
        
        Returns:
            Score basé sur l'absence d'erreurs critiques (0-100).
        """
        alerts = sia3801_results.get("alerts", []) + sia4010_results.get("alerts", [])
        critical_errors = [alert for alert in alerts if alert.severity == Severity.CRITICAL]
        if not critical_errors:
            return 100.0
        # Chaque erreur critique réduit le score de 10%
        return max(0.0, 100.0 - len(critical_errors) * 10)

    @staticmethod
    def _is_missing_data_alert(alert: Alert) -> bool:
        """Identifie les alertes qui signalent une donnée absente ou non vérifiable."""
        rule = str(alert.rule or "").upper()
        text = " ".join([
            str(alert.description or ""),
            str(alert.recommendation or ""),
        ]).lower()
        markers = (
            "MISSING",
            "UNAVAILABLE",
            "NOT_CHECKABLE",
            "non disponible",
            "non verifiable",
            "non vérifiable",
            "manquant",
            "introuvable",
        )
        return any(marker in rule or marker in text for marker in markers)

    @staticmethod
    def _score_from_alerts(alerts: List[Alert]) -> float:
        """Transforme une liste d'alertes en score qualité 0-100."""
        score = 100.0
        penalties = {
            Severity.CRITICAL: 15.0,
            Severity.HIGH: 10.0,
            Severity.MEDIUM: 6.0,
            Severity.LOW: 3.0,
        }
        for alert in alerts:
            score -= penalties.get(alert.severity, 3.0)
        return max(0.0, min(100.0, score))

    def _calculate_detailed_scores(
        self,
        sia3801_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
    ) -> Dict[str, float]:
        """
        Calcule les scores détaillés par catégorie.
        
        Args:
            sia3801_results: Résultats des vérifications SIA 380/2.
            sia4010_results: Résultats des vérifications SIA 4010.
        
        Returns:
            Dictionnaire des scores détaillés par catégorie.
        """
        detailed_scores = {}

        # Scores SIA 380/2
        for category in ["envelope", "openings", "ventilation", "gains", "hvac"]:
            detailed_scores[f"SIA3801_{category.upper()}"] = sia3801_results.get(category, {}).get("score", 0.0)

        # Scores SIA 4010
        detailed_scores["SIA4010_ENERGY"] = sia4010_results.get("score", 0.0)

        # Scores des tests SIA 4010
        for test_name, test_data in sia4010_results.get("tests", {}).items():
            detailed_scores[f"SIA4010_{test_name.upper()}"] = test_data.get("score", 0.0)

        return detailed_scores
