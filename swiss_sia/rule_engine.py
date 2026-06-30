"""Rule engine used by the Swiss SIA compliance checker.

The engine stores named compliance rules, applies them to normalized VE data,
and returns structured alerts when a rule is not satisfied.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


logger = logging.getLogger(__name__)


class Severity(Enum):
    """Alert severity levels."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class Alert:
    """Structured alert raised by a rule or by a manual completeness check."""

    rule: str
    description: str
    severity: Severity
    category: str
    recommendation: str
    data: Optional[Any] = None


@dataclass
class Rule:
    """Compliance rule applied to one VE-derived object."""

    name: str
    description: str
    check: Callable[[Any], bool]
    severity: Severity
    category: str
    recommendation: str


class RuleEngine:
    """Apply named rules to VE-derived data and collect alerts."""

    def __init__(self):
        """Initialize an empty rule engine."""
        self.rules: List[Rule] = []
        self._rules_by_name: Dict[str, Rule] = {}
        self.alerts: List[Alert] = []

    def add_rule(self, rule: Rule):
        """Register a single rule."""
        self.rules.append(rule)
        self._rules_by_name[rule.name] = rule

    def add_rules(self, rules: List[Rule]):
        """Register multiple rules while keeping the name index in sync."""
        for rule in rules:
            self.add_rule(rule)

    @staticmethod
    def _make_alert(rule: Rule, data: Any) -> Alert:
        """Build a rule alert in one place to keep all rule paths consistent."""
        return Alert(
            rule=rule.name,
            description=rule.description,
            severity=rule.severity,
            category=rule.category,
            recommendation=rule.recommendation,
            data=data,
        )

    def add_alert(
        self,
        rule: str,
        description: str,
        severity: Severity,
        category: str,
        recommendation: str,
        data: Optional[Any] = None,
    ) -> Alert:
        """Add a manual alert for non-checkable or incomplete situations."""
        alert = Alert(
            rule=rule,
            description=description,
            severity=severity,
            category=category,
            recommendation=recommendation,
            data=data,
        )
        self.alerts.append(alert)
        return alert

    def check_all(self, data: Any, reset: bool = False) -> List[Alert]:
        """Apply every registered rule to one data object."""
        if reset:
            self.alerts = []

        new_alerts: List[Alert] = []
        for rule in self.rules:
            try:
                if not rule.check(data):
                    alert = self._make_alert(rule, data)
                    self.alerts.append(alert)
                    new_alerts.append(alert)
            except Exception as exc:
                logger.error("Error while applying rule %s: %s", rule.name, exc)
        return new_alerts

    def check_rules(self, rule_names: List[str], data: Any) -> List[Alert]:
        """Apply only the requested named rules to one data object."""
        alerts: List[Alert] = []
        for rule_name in rule_names:
            rule = self._rules_by_name.get(rule_name)
            if rule is None:
                continue
            try:
                if not rule.check(data):
                    alert = self._make_alert(rule, data)
                    self.alerts.append(alert)
                    alerts.append(alert)
            except Exception as exc:
                logger.error("Error while applying rule %s: %s", rule.name, exc)
        return alerts

    def check_rule(self, rule_name: str, data: Any) -> Optional[Alert]:
        """Apply one named rule and return an alert if it fails."""
        rule = self._rules_by_name.get(rule_name)
        if rule is None:
            return None
        try:
            if not rule.check(data):
                return self._make_alert(rule, data)
        except Exception as exc:
            logger.error("Error while applying rule %s: %s", rule.name, exc)
        return None

    def clear_alerts(self):
        """Clear all collected alerts."""
        self.alerts = []

    def get_alerts_by_severity(self, severity: Severity) -> List[Alert]:
        """Return collected alerts for one severity level."""
        return [alert for alert in self.alerts if alert.severity == severity]

    def get_alerts_by_category(self, category: str) -> List[Alert]:
        """Return collected alerts for one category."""
        return [alert for alert in self.alerts if alert.category == category]

    def get_critical_alerts(self) -> List[Alert]:
        """Return critical alerts."""
        return self.get_alerts_by_severity(Severity.CRITICAL)

    def get_high_alerts(self) -> List[Alert]:
        """Return high-severity alerts."""
        return self.get_alerts_by_severity(Severity.HIGH)

    def get_medium_alerts(self) -> List[Alert]:
        """Return medium-severity alerts."""
        return self.get_alerts_by_severity(Severity.MEDIUM)

    def get_low_alerts(self) -> List[Alert]:
        """Return low-severity alerts."""
        return self.get_alerts_by_severity(Severity.LOW)

    def count_alerts_by_severity(self) -> Dict[str, int]:
        """Count collected alerts by severity level."""
        return {
            "Critical": len(self.get_critical_alerts()),
            "High": len(self.get_high_alerts()),
            "Medium": len(self.get_medium_alerts()),
            "Low": len(self.get_low_alerts()),
        }

    def count_alerts_by_category(self) -> Dict[str, int]:
        """Count collected alerts by category."""
        categories: Dict[str, int] = {}
        for alert in self.alerts:
            categories[alert.category] = categories.get(alert.category, 0) + 1
        return categories

