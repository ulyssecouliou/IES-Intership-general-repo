"""
Validateur des règles SIA 4010.
Ce module vérifie la conformité du modèle VE aux exigences de la norme suisse SIA 4010.
"""

import logging
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from config import (
    SIA4010_EVIDENCE_DIR,
    SIA4010_EVIDENCE_FILE_PATTERNS,
    SIA4010_REQUIRED_EVIDENCE,
    SIA4010_THRESHOLDS,
    SIA4010_TEST_WEIGHTS,
    SIA4010_VALIDATION_TESTS,
    EMISSION_FACTORS,
)
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
        # SIA 4010 ne fournit pas de limites bâtiment autonomes dans le PDF.
        # Ces règles restent des emplacements pour indicateurs client futurs.
        self.rule_engine.add_rule(Rule(
            name="SIA4010_HEATING_DEMAND",
            description="Besoin en chauffage disponible; SIA 4010 exige une validation par tests/fichiers officiels, pas un seuil kWh/m².an autonome.",
            check=lambda data: True,
            severity=Severity.LOW,
            category="Energy",
            recommendation="Comparer uniquement via le fichier d'évaluation SIA 4010 officiel ou via les exigences SIA 380 applicables au projet.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA4010_COOLING_DEMAND",
            description="Besoin en refroidissement disponible; SIA 4010 exige une validation par tests/fichiers officiels, pas un seuil kWh/m².an autonome.",
            check=lambda data: True,
            severity=Severity.LOW,
            category="Energy",
            recommendation="Comparer uniquement via le fichier d'évaluation SIA 4010 officiel ou via les exigences SIA 380 applicables au projet.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA4010_PRIMARY_ENERGY",
            description="Énergie primaire disponible; SIA 4010 ne donne pas de seuil autonome dans le PDF.",
            check=lambda data: True,
            severity=Severity.LOW,
            category="Energy",
            recommendation="Pondérer et juger l'énergie primaire selon SIA 380 / exigences projet, puis joindre la validation SIA 4010 si le moteur de calcul est revendiqué.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA4010_CO2_EMISSIONS",
            description="Émissions CO2 disponibles; SIA 4010 ne donne pas de seuil autonome dans le PDF.",
            check=lambda data: True,
            severity=Severity.LOW,
            category="Energy",
            recommendation="Traiter le CO2 comme indicateur client/cantonal séparé, pas comme verdict SIA 4010.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA4010_RENEWABLE_ENERGY",
            description="Part renouvelable disponible; SIA 4010 ne donne pas de seuil autonome dans le PDF.",
            check=lambda data: True,
            severity=Severity.LOW,
            category="Energy",
            recommendation="Traiter la part renouvelable selon les exigences projet/cantonales; ne pas l'utiliser comme validation SIA 4010.",
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
        evidence = self._scan_sia4010_evidence()

        # Vérifier uniquement les indicateurs réellement disponibles comme
        # informations projet. Ils ne remplacent jamais les fichiers SIA 4010.
        self.rule_engine.clear_alerts()
        rule_by_metric = {
            "heating_demand": "SIA4010_HEATING_DEMAND",
            "cooling_demand": "SIA4010_COOLING_DEMAND",
            "primary_energy": "SIA4010_PRIMARY_ENERGY",
            "co2_emissions": "SIA4010_CO2_EMISSIONS",
            "renewable_energy_share": "SIA4010_RENEWABLE_ENERGY",
        }
        for metric, rule_name in rule_by_metric.items():
            if energy_data.get(metric) is None:
                continue
            self.rule_engine.check_rules([rule_name], energy_data)

        self.rule_engine.add_alert(
            rule="SIA4010_VALIDATION_EVIDENCE_MISSING",
            description="Validation SIA 4010 non vérifiable sans spécifications de tests, fichiers Excel d'évaluation et résultats de référence officiels.",
            severity=Severity.HIGH,
            category="SIA4010 Validation",
            recommendation="Joindre les fichiers SIA 4010 officiels remplis, les comparaisons aux références et la classe de validation visée avant tout verdict PASS.",
            data=energy_data,
        )

        # Exécuter les 7 tests SIA 4010
        test_results = self._run_sia4010_tests(energy_data)

        return {
            "energy": energy_data,
            "alerts": self.rule_engine.alerts,
            "tests": test_results,
            "score": self._calculate_sia4010_score(test_results),
            "evidence": evidence,
            "validation_class": evidence.get("validation_class"),
        }

    def _scan_sia4010_evidence(self) -> Dict[str, Any]:
        """Scan local SIA 4010 evidence files without granting official validation."""
        repo_dir = os.path.dirname(os.path.abspath(__file__))
        evidence_dir = os.path.join(repo_dir, SIA4010_EVIDENCE_DIR)
        files: List[Dict[str, Any]] = []
        if os.path.isdir(evidence_dir):
            for root, _dirs, filenames in os.walk(evidence_dir):
                for filename in filenames:
                    path = os.path.join(root, filename)
                    rel_path = os.path.relpath(path, repo_dir)
                    try:
                        size_bytes = os.path.getsize(path)
                    except Exception:
                        size_bytes = None
                    files.append({
                        "name": filename,
                        "path": rel_path,
                        "size_bytes": size_bytes,
                    })

        evidence: Dict[str, Any] = {
            "evidence_dir": evidence_dir,
            "files": files,
            "validation_class": None,
        }
        filenames_blob = " ".join(file_data["name"].lower() for file_data in files)
        for key, patterns in SIA4010_EVIDENCE_FILE_PATTERNS.items():
            matched = [
                file_data
                for file_data in files
                if any(pattern.lower() in file_data["name"].lower() for pattern in patterns)
            ]
            evidence[key] = {
                "present": bool(matched),
                "files": matched,
            }

        class_markers = ["4b", "4a", "3", "2b", "2a", "1b", "1a", "5"]
        for marker in class_markers:
            if f"class_{marker}" in filenames_blob or f"classe_{marker}" in filenames_blob or f"class{marker}" in filenames_blob:
                evidence["validation_class"] = marker.upper()
                break

        item_key_map = {
            SIA4010_REQUIRED_EVIDENCE[0]: "official_test_specifications",
            SIA4010_REQUIRED_EVIDENCE[1]: "official_evaluation_workbooks",
            SIA4010_REQUIRED_EVIDENCE[2]: "candidate_results",
            SIA4010_REQUIRED_EVIDENCE[3]: "reference_comparisons",
            SIA4010_REQUIRED_EVIDENCE[4]: "validation_class_confirmation",
        }
        for item, key in item_key_map.items():
            evidence[item] = bool(evidence.get(key, {}).get("present"))
        return evidence

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
        # SIA 4010:2023, tableau 62. Ces tests valident le logiciel ou la
        # méthode de calcul, pas directement un modèle client isolé.
        return {
            test_name: {
                "status": "NOT_CHECKABLE",
                "score": 0,
                "description": description,
            }
            for test_name, description in SIA4010_VALIDATION_TESTS.items()
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
