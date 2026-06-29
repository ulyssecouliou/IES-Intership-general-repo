"""
Validateur des règles SIA 4010.
Ce module vérifie la conformité du modèle VE aux exigences de la norme suisse SIA 4010.
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from config import SIA4010_THRESHOLDS, SIA4010_TEST_WEIGHTS, EMISSION_FACTORS
from rule_engine import RuleEngine, Rule, Severity, Alert
from model_analyzer import ModelAnalyzer, RoomData

logger = logging.getLogger(__name__)


class SIA4010Checker:
    """
    Vérifie la conformité du modèle VE aux exigences SIA 4010.
    """

    def __init__(self, model_analyzer: ModelAnalyzer, rule_engine: RuleEngine):
        """
        Initialise le validateur SIA 4010.
        
        Args:
            model_analyzer: Instance de ModelAnalyzer.
            rule_engine: Instance de RuleEngine.
        """
        self.model_analyzer = model_analyzer
        self.rule_engine = rule_engine
        self._setup_rules()

    def _setup_rules(self):
        """Configure les règles SIA 4010 dans le moteur de règles."""
        # Règles pour les besoins énergétiques
        self.rule_engine.add_rule(Rule(
            name="SIA4010_HEATING_DEMAND",
            description=f"Besoin en chauffage ≤ {SIA4010_THRESHOLDS['heating_demand_max']} kWh/m²/an",
            check=lambda data: data.get("heating_demand") is not None and data.get("heating_demand") <= SIA4010_THRESHOLDS["heating_demand_max"],
            severity=Severity.CRITICAL,
            category="Energy",
            recommendation=f"Réduire le besoin en chauffage à ≤ {SIA4010_THRESHOLDS['heating_demand_max']} kWh/m²/an en améliorant l'isolation ou les systèmes CVC.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA4010_COOLING_DEMAND",
            description=f"Besoin en refroidissement ≤ {SIA4010_THRESHOLDS['cooling_demand_max']} kWh/m²/an",
            check=lambda data: data.get("cooling_demand") is not None and data.get("cooling_demand") <= SIA4010_THRESHOLDS["cooling_demand_max"],
            severity=Severity.HIGH,
            category="Energy",
            recommendation=f"Réduire le besoin en refroidissement à ≤ {SIA4010_THRESHOLDS['cooling_demand_max']} kWh/m²/an en améliorant l'isolation ou les systèmes CVC.",
        ))

        # Règles pour l'énergie primaire
        self.rule_engine.add_rule(Rule(
            name="SIA4010_PRIMARY_ENERGY",
            description=f"Énergie primaire ≤ {SIA4010_THRESHOLDS['primary_energy_max']} kWh/m²/an",
            check=lambda data: data.get("primary_energy") is not None and data.get("primary_energy") <= SIA4010_THRESHOLDS["primary_energy_max"],
            severity=Severity.CRITICAL,
            category="Energy",
            recommendation=f"Réduire l'énergie primaire à ≤ {SIA4010_THRESHOLDS['primary_energy_max']} kWh/m²/an en optimisant les systèmes énergétiques.",
        ))

        # Règles pour les émissions CO₂
        self.rule_engine.add_rule(Rule(
            name="SIA4010_CO2_EMISSIONS",
            description=f"Émissions CO₂ ≤ {SIA4010_THRESHOLDS['co2_emissions_max']} kg CO₂/m²/an",
            check=lambda data: data.get("co2_emissions") is not None and data.get("co2_emissions") <= SIA4010_THRESHOLDS["co2_emissions_max"],
            severity=Severity.HIGH,
            category="Energy",
            recommendation=f"Réduire les émissions CO₂ à ≤ {SIA4010_THRESHOLDS['co2_emissions_max']} kg CO₂/m²/an en utilisant des énergies moins polluantes.",
        ))

        # Règles pour les énergies renouvelables
        self.rule_engine.add_rule(Rule(
            name="SIA4010_RENEWABLE_ENERGY",
            description=f"Part des énergies renouvelables ≥ {SIA4010_THRESHOLDS['renewable_energy_min'] * 100}%",
            check=lambda data: data.get("renewable_energy_share") is not None and data.get("renewable_energy_share") >= SIA4010_THRESHOLDS["renewable_energy_min"],
            severity=Severity.MEDIUM,
            category="Energy",
            recommendation=f"Augmenter la part des énergies renouvelables à ≥ {SIA4010_THRESHOLDS['renewable_energy_min'] * 100}%.",
        ))

    def check_all(self) -> Dict[str, Any]:
        """
        Exécute toutes les vérifications SIA 4010 et retourne les résultats.
        
        Returns:
            Dictionnaire des résultats (énergie, alertes, tests, score).
        """
        rooms_data = self.model_analyzer.analyze_all_rooms()

        # SIA 4010 valide une méthode/un logiciel via 7 tests officiels.
        # Sans fichier APS de test SIA ou fichier d'évaluation importé, on ne doit
        # jamais annoncer une réussite; les indicateurs restent non vérifiables.
        energy_data = {
            "heating_demand": self._calculate_heating_demand(rooms_data),
            "cooling_demand": self._calculate_cooling_demand(rooms_data),
            "primary_energy": None,
            "co2_emissions": None,
            "renewable_energy_share": None,
        }

        # Vérifier uniquement les indicateurs réellement disponibles.
        self.rule_engine.clear_alerts()
        rule_by_metric = {
            "heating_demand": "SIA4010_HEATING_DEMAND",
            "cooling_demand": "SIA4010_COOLING_DEMAND",
            "primary_energy": "SIA4010_PRIMARY_ENERGY",
            "co2_emissions": "SIA4010_CO2_EMISSIONS",
            "renewable_energy_share": "SIA4010_RENEWABLE_ENERGY",
        }
        checked_metrics = []
        for metric, rule_name in rule_by_metric.items():
            if energy_data.get(metric) is None:
                continue
            self.rule_engine.check_rules([rule_name], energy_data)
            checked_metrics.append(metric)
        if not checked_metrics:
            self.rule_engine.add_alert(
                rule="SIA4010_VALIDATION_EVIDENCE_MISSING",
                description="Aucun résultat dynamique ou fichier de validation SIA 4010 n'est disponible pour vérifier les indicateurs énergétiques.",
                severity=Severity.HIGH,
                category="SIA4010 Validation",
                recommendation="Importer ou générer les résultats APS correspondant aux tests SIA 4010, puis joindre la matrice de validation au rapport.",
                data=energy_data,
            )

        # Exécuter les 7 tests SIA 4010
        test_results = self._run_sia4010_tests(energy_data)

        return {
            "energy": energy_data,
            "alerts": self.rule_engine.alerts,
            "tests": test_results,
            "score": self._calculate_sia4010_score(test_results),
        }

    def _calculate_heating_demand(self, rooms_data: List[RoomData]) -> Optional[float]:
        """
        Calcule le besoin annuel en chauffage (kWh/m²/an).
        
        Args:
            rooms_data: Liste des objets RoomData.
        
        Returns:
            Besoin en chauffage (kWh/m²/an).
        """
        return None

    def _calculate_cooling_demand(self, rooms_data: List[RoomData]) -> Optional[float]:
        """
        Calcule le besoin annuel en refroidissement (kWh/m²/an).
        
        Args:
            rooms_data: Liste des objets RoomData.
        
        Returns:
            Besoin en refroidissement (kWh/m²/an).
        """
        return None

    def _calculate_co2_emissions(self, energy_sources: Dict[str, Any], total_area: float) -> float:
        """
        Calcule les émissions CO₂ totales (kg CO₂/m²/an).
        
        Args:
            energy_sources: Dictionnaire des sources d'énergie.
            total_area: Surface totale du bâtiment (m²).
        
        Returns:
            Émissions CO₂ (kg CO₂/m²/an).
        """
        total_co2 = 0.0
        for source in energy_sources.values():
            try:
                consumption = source.get_annual_consumption()
                emission_factor = EMISSION_FACTORS.get(source.type, 0.0)
                total_co2 += consumption * emission_factor
            except Exception as e:
                logger.error(f"Erreur lors du calcul des émissions CO₂: {e}")
        return total_co2 / total_area if total_area > 0 else 0.0

    def _calculate_renewable_energy_share(self, energy_sources: Dict[str, Any], total_energy: float) -> float:
        """
        Calcule la part des énergies renouvelables.
        
        Args:
            energy_sources: Dictionnaire des sources d'énergie.
            total_energy: Consommation énergétique totale (kWh/an).
        
        Returns:
            Part des énergies renouvelables (0-1).
        """
        renewable_energy = 0.0
        for source in energy_sources.values():
            try:
                if source.type in ["solar", "wind", "biomass"]:
                    renewable_energy += source.get_annual_consumption()
            except Exception as e:
                logger.error(f"Erreur lors du calcul de l'énergie renouvelable: {e}")
        return renewable_energy / total_energy if total_energy > 0 else 0.0

    def _run_sia4010_tests(self, energy_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Exécute les 7 tests SIA 4010.
        
        Args:
            energy_data: Dictionnaire des données énergétiques.
        
        Returns:
            Dictionnaire des résultats des tests.
        """
        # SIA 4010:2023, tableau 62/64. Ces tests valident le logiciel ou la
        # méthode de calcul, pas directement un modèle client isolé.
        return {
            "test_1": {"status": "NOT_CHECKABLE", "score": 0, "description": "Tests de base enveloppe selon EN ISO 52016-1 / ASHRAE 140"},
            "test_2": {"status": "NOT_CHECKABLE", "score": 0, "description": "Type et régulation de la protection solaire selon SIA 387/4 et SIA 380/2"},
            "test_3": {"status": "NOT_CHECKABLE", "score": 0, "description": "Régulation de l'éclairage selon SIA 387/4"},
            "test_4": {"status": "NOT_CHECKABLE", "score": 0, "description": "Climatisation d'une seule pièce, système à air seul"},
            "test_5": {"status": "NOT_CHECKABLE", "score": 0, "description": "Unité de traitement d'air multizone avec récupération et humidification"},
            "test_6": {"status": "NOT_CHECKABLE", "score": 0, "description": "Ventilation à trois niveaux avec récupération de chaleur"},
            "test_7": {"status": "NOT_CHECKABLE", "score": 0, "description": "Émission, distribution, stockage et production de chaleur/froid"},
        }

    def _calculate_sia4010_score(self, test_results: Dict[str, Any]) -> float:
        """
        Calcule le score SIA 4010 (0-100) basé sur les résultats des tests.
        
        Args:
            test_results: Dictionnaire des résultats des tests.
        
        Returns:
            Score SIA 4010 (0-100).
        """
        total_score = 0.0
        total_weight = 0.0
        for test_name, test_data in test_results.items():
            weight = SIA4010_TEST_WEIGHTS.get(test_name, 0.0)
            total_score += test_data["score"] * weight
            total_weight += weight
        return total_score / total_weight if total_weight > 0 else 0.0
