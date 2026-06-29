"""
Moteur de règles pour appliquer les exigences SIA 380/2 et SIA 4010.
Ce module génère des alertes en cas de non-conformité.
"""

import logging
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Niveaux de sévérité pour les alertes."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class Alert:
    """Représente une alerte générée par le moteur de règles."""
    rule: str
    description: str
    severity: Severity
    category: str
    recommendation: str
    data: Optional[Any] = None


@dataclass
class Rule:
    """Représente une règle de conformité."""
    name: str
    description: str
    check: Callable[[Any], bool]  # Fonction qui retourne True si conforme
    severity: Severity
    category: str
    recommendation: str


class RuleEngine:
    """
    Moteur de règles pour appliquer des règles de conformité aux données VE.
    """

    def __init__(self):
        """Initialise le moteur de règles."""
        self.rules: List[Rule] = []
        self.alerts: List[Alert] = []

    def add_rule(self, rule: Rule):
        """
        Ajoute une règle au moteur.
        
        Args:
            rule: Objet Rule à ajouter.
        """
        self.rules.append(rule)

    def add_rules(self, rules: List[Rule]):
        """
        Ajoute plusieurs règles au moteur.
        
        Args:
            rules: Liste d'objets Rule à ajouter.
        """
        self.rules.extend(rules)

    def add_alert(
        self,
        rule: str,
        description: str,
        severity: Severity,
        category: str,
        recommendation: str,
        data: Optional[Any] = None,
    ) -> Alert:
        """Ajoute une alerte manuelle pour les cas non vérifiables ou incomplets."""
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
        """
        Applique toutes les règles à une donnée et retourne les alertes.
        
        Args:
            data: Donnée à vérifier.
        
        Returns:
            Liste des alertes générées.
        """
        if reset:
            self.alerts = []
        new_alerts: List[Alert] = []
        for rule in self.rules:
            try:
                if not rule.check(data):
                    alert = Alert(
                        rule=rule.name,
                        description=rule.description,
                        severity=rule.severity,
                        category=rule.category,
                        recommendation=rule.recommendation,
                        data=data,
                    )
                    self.alerts.append(alert)
                    new_alerts.append(alert)
            except Exception as e:
                logger.error(f"Erreur lors de l'application de la règle {rule.name}: {e}")
        return new_alerts

    def check_rules(self, rule_names: List[str], data: Any) -> List[Alert]:
        """Applique uniquement les règles nommées et conserve les alertes déjà collectées."""
        alerts: List[Alert] = []
        rule_name_set = set(rule_names)
        for rule in self.rules:
            if rule.name not in rule_name_set:
                continue
            try:
                if not rule.check(data):
                    alert = Alert(
                        rule=rule.name,
                        description=rule.description,
                        severity=rule.severity,
                        category=rule.category,
                        recommendation=rule.recommendation,
                        data=data,
                    )
                    self.alerts.append(alert)
                    alerts.append(alert)
            except Exception as e:
                logger.error(f"Erreur lors de l'application de la règle {rule.name}: {e}")
        return alerts

    def check_rule(self, rule_name: str, data: Any) -> Optional[Alert]:
        """
        Applique une règle spécifique à une donnée.
        
        Args:
            rule_name: Nom de la règle à appliquer.
            data: Donnée à vérifier.
        
        Returns:
            Alerte générée ou None si la règle est respectée.
        """
        for rule in self.rules:
            if rule.name == rule_name:
                try:
                    if not rule.check(data):
                        return Alert(
                            rule=rule.name,
                            description=rule.description,
                            severity=rule.severity,
                            category=rule.category,
                            recommendation=rule.recommendation,
                            data=data,
                        )
                except Exception as e:
                    logger.error(f"Erreur lors de l'application de la règle {rule.name}: {e}")
        return None

    def clear_alerts(self):
        """Efface toutes les alertes."""
        self.alerts = []

    def get_alerts_by_severity(self, severity: Severity) -> List[Alert]:
        """
        Retourne les alertes d'un niveau de sévérité donné.
        
        Args:
            severity: Niveau de sévérité (Critical, High, Medium, Low).
        
        Returns:
            Liste des alertes correspondantes.
        """
        return [alert for alert in self.alerts if alert.severity == severity]

    def get_alerts_by_category(self, category: str) -> List[Alert]:
        """
        Retourne les alertes d'une catégorie donnée.
        
        Args:
            category: Catégorie des alertes (ex: "Envelope", "HVAC").
        
        Returns:
            Liste des alertes correspondantes.
        """
        return [alert for alert in self.alerts if alert.category == category]

    def get_critical_alerts(self) -> List[Alert]:
        """Retourne les alertes critiques."""
        return self.get_alerts_by_severity(Severity.CRITICAL)

    def get_high_alerts(self) -> List[Alert]:
        """Retourne les alertes de niveau élevé."""
        return self.get_alerts_by_severity(Severity.HIGH)

    def get_medium_alerts(self) -> List[Alert]:
        """Retourne les alertes de niveau moyen."""
        return self.get_alerts_by_severity(Severity.MEDIUM)

    def get_low_alerts(self) -> List[Alert]:
        """Retourne les alertes de niveau faible."""
        return self.get_alerts_by_severity(Severity.LOW)

    def count_alerts_by_severity(self) -> Dict[str, int]:
        """
        Compte le nombre d'alertes par niveau de sévérité.
        
        Returns:
            Dictionnaire avec les comptes par sévérité.
        """
        return {
            "Critical": len(self.get_critical_alerts()),
            "High": len(self.get_high_alerts()),
            "Medium": len(self.get_medium_alerts()),
            "Low": len(self.get_low_alerts()),
        }

    def count_alerts_by_category(self) -> Dict[str, int]:
        """
        Compte le nombre d'alertes par catégorie.
        
        Returns:
            Dictionnaire avec les comptes par catégorie.
        """
        categories = {}
        for alert in self.alerts:
            if alert.category not in categories:
                categories[alert.category] = 0
            categories[alert.category] += 1
        return categories
