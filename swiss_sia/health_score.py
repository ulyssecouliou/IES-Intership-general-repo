"""Score calculation for the Swiss SIA compliance checker.

The module separates the automated SIA 380/2 indicator from the model health
score. SIA 4010 is intentionally kept as an evidence-readiness status rather
than a building performance score.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .config import CATEGORY_WEIGHTS
from .rule_engine import Alert, Severity


@dataclass
class ScoreResult:
    """Computed score package passed to the Excel report generator."""

    compliance_score: float
    health_score: float
    detailed_scores: Dict[str, float]
    alerts: List[Alert]


class HealthScoreCalculator:
    """Calculate compliance and model-quality scores from checker results."""

    def calculate_scores(
        self,
        sia3802_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
    ) -> ScoreResult:
        """Calculate all report scores and aggregate alerts."""
        compliance_score = self._calculate_compliance_score(sia3802_results)
        health_score = self._calculate_health_score(sia3802_results, sia4010_results)
        detailed_scores = self._calculate_detailed_scores(sia3802_results, sia4010_results)
        alerts = sia3802_results.get("alerts", []) + sia4010_results.get("alerts", [])

        return ScoreResult(
            compliance_score=compliance_score,
            health_score=health_score,
            detailed_scores=detailed_scores,
            alerts=alerts,
        )

    def _calculate_compliance_score(self, sia3802_results: Dict[str, Any]) -> float:
        """Return the weighted automated SIA 380/2 indicator."""
        return self._calculate_sia3802_score(sia3802_results)

    def _calculate_sia3802_score(self, sia3802_results: Dict[str, Any]) -> float:
        """Calculate the weighted SIA 380/2 score from implemented categories."""
        category_scores = []
        score_categories = ["envelope", "openings", "ventilation", "gains", "hvac"]
        for category, weight in CATEGORY_WEIGHTS.items():
            if category in score_categories:
                category_score = sia3802_results.get(category, {}).get("score", 0.0)
                category_scores.append(category_score * weight)

        total_weight = sum(
            weight for category, weight in CATEGORY_WEIGHTS.items()
            if category in score_categories
        )
        return sum(category_scores) / total_weight if category_scores else 0.0

    def _calculate_health_score(
        self,
        sia3802_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
    ) -> float:
        """Calculate the model health score from completeness and consistency."""
        completeness_score = self._calculate_completeness_score(sia3802_results)
        consistency_score = self._calculate_consistency_score(sia3802_results)
        critical_errors_score = self._calculate_critical_errors_score(
            sia3802_results,
            sia4010_results,
        )

        return (
            completeness_score * 0.4
            + consistency_score * 0.3
            + critical_errors_score * 0.3
        )

    def _calculate_completeness_score(self, sia3802_results: Dict[str, Any]) -> float:
        """Score missing or non-checkable data alerts."""
        alerts = sia3802_results.get("alerts", [])
        missing_alerts = [
            alert for alert in alerts
            if self._is_missing_data_alert(alert)
        ]
        return self._score_from_alerts(missing_alerts)

    def _calculate_consistency_score(self, sia3802_results: Dict[str, Any]) -> float:
        """Average available category scores as a model consistency proxy."""
        category_scores = [
            sia3802_results.get(category, {}).get("score")
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
        sia3802_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
    ) -> float:
        """Score the absence of critical alerts."""
        alerts = sia3802_results.get("alerts", []) + sia4010_results.get("alerts", [])
        critical_errors = [alert for alert in alerts if alert.severity == Severity.CRITICAL]
        if not critical_errors:
            return 100.0
        return max(0.0, 100.0 - len(critical_errors) * 10)

    @staticmethod
    def _is_missing_data_alert(alert: Alert) -> bool:
        """Return true when an alert indicates missing or non-checkable data."""
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
        """Convert a list of alerts into a 0-100 quality score."""
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
        sia3802_results: Dict[str, Any],
        sia4010_results: Dict[str, Any],
    ) -> Dict[str, float]:
        """Build detailed score rows for the report workbook."""
        detailed_scores: Dict[str, float] = {}

        for category in ["envelope", "openings", "ventilation", "gains", "hvac"]:
            detailed_scores[f"SIA3802_{category.upper()}"] = sia3802_results.get(
                category,
                {},
            ).get("score", 0.0)

        detailed_scores["SIA4010_ENERGY"] = sia4010_results.get("score", 0.0)
        detailed_scores["SIA4010_EVIDENCE_READINESS"] = sia4010_results.get("readiness_score", 0.0)

        for test_name, test_data in sia4010_results.get("tests", {}).items():
            detailed_scores[f"SIA4010_{test_name.upper()}"] = test_data.get("score", 0.0)

        return detailed_scores
