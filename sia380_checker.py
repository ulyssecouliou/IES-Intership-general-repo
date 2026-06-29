"""
Validateur des règles SIA 380/2.
Ce module vérifie la conformité du modèle VE aux exigences de la norme suisse SIA 380/2.
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from config import SIA3801_U_VALUES, SIA3801_THRESHOLDS
from rule_engine import RuleEngine, Rule, Severity, Alert
from model_analyzer import ModelAnalyzer, RoomData, SurfaceData, OpeningData

logger = logging.getLogger(__name__)


class SIA3801Checker:
    """
    Vérifie la conformité du modèle VE aux exigences SIA 380/2.
    """

    def __init__(self, model_analyzer: ModelAnalyzer, rule_engine: RuleEngine):
        """
        Initialise le validateur SIA 380/2.
        
        Args:
            model_analyzer: Instance de ModelAnalyzer.
            rule_engine: Instance de RuleEngine.
        """
        self.model_analyzer = model_analyzer
        self.rule_engine = rule_engine
        self._setup_rules()

    def _setup_rules(self):
        """Configure les règles SIA 380/2 dans le moteur de règles."""
        # Règles pour les U-values des surfaces
        self.rule_engine.add_rule(Rule(
            name="SIA3801_U_VALUE_EXTERNAL_WALL",
            description=f"U-value des murs extérieurs ≤ {SIA3801_U_VALUES['external_wall']} W/m²K",
            check=lambda surface: surface.u_value <= SIA3801_U_VALUES["external_wall"] if surface.u_value is not None else False,
            severity=Severity.HIGH,
            category="Envelope",
            recommendation=f"Réduire la U-value à ≤ {SIA3801_U_VALUES['external_wall']} W/m²K en améliorant l'isolation.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3801_U_VALUE_ROOF",
            description=f"U-value des toitures ≤ {SIA3801_U_VALUES['roof']} W/m²K",
            check=lambda surface: surface.u_value <= SIA3801_U_VALUES["roof"] if surface.u_value is not None else False,
            severity=Severity.HIGH,
            category="Envelope",
            recommendation=f"Réduire la U-value à ≤ {SIA3801_U_VALUES['roof']} W/m²K en améliorant l'isolation.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3801_U_VALUE_FLOOR",
            description=f"U-value des planchers ≤ {SIA3801_U_VALUES['floor']} W/m²K",
            check=lambda surface: surface.u_value <= SIA3801_U_VALUES["floor"] if surface.u_value is not None else False,
            severity=Severity.HIGH,
            category="Envelope",
            recommendation=f"Réduire la U-value à ≤ {SIA3801_U_VALUES['floor']} W/m²K en améliorant l'isolation.",
        ))

        # Règles pour les U-values des ouvertures
        self.rule_engine.add_rule(Rule(
            name="SIA3801_U_VALUE_WINDOW",
            description=f"U-value des fenêtres ≤ {SIA3801_U_VALUES['window']} W/m²K",
            check=lambda opening: opening.u_value <= SIA3801_U_VALUES["window"] if opening.u_value is not None else False,
            severity=Severity.HIGH,
            category="Openings",
            recommendation=f"Remplacer les fenêtres pour atteindre une U-value ≤ {SIA3801_U_VALUES['window']} W/m²K.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3801_U_VALUE_DOOR",
            description=f"U-value des portes ≤ {SIA3801_U_VALUES['door']} W/m²K",
            check=lambda opening: opening.u_value <= SIA3801_U_VALUES["door"] if opening.u_value is not None else False,
            severity=Severity.MEDIUM,
            category="Openings",
            recommendation=f"Remplacer les portes pour atteindre une U-value ≤ {SIA3801_U_VALUES['door']} W/m²K.",
        ))

        # Règles pour le facteur solaire
        self.rule_engine.add_rule(Rule(
            name="SIA3801_SOLAR_FACTOR",
            description=f"Facteur solaire (g-value) des fenêtres ≤ {SIA3801_THRESHOLDS['solar_factor_max']}",
            check=lambda opening: opening.solar_factor <= SIA3801_THRESHOLDS["solar_factor_max"] if opening.solar_factor is not None else False,
            severity=Severity.MEDIUM,
            category="Openings",
            recommendation=f"Utiliser des vitrages avec un facteur solaire ≤ {SIA3801_THRESHOLDS['solar_factor_max']}.",
        ))

        # Règles pour le WWR (Window-to-Wall Ratio)
        self.rule_engine.add_rule(Rule(
            name="SIA3801_WWR",
            description=f"Window-to-Wall Ratio (WWR) ≤ {SIA3801_THRESHOLDS['wwr_max'] * 100}%",
            check=lambda room: self.model_analyzer.calculate_wwr(room) <= SIA3801_THRESHOLDS["wwr_max"],
            severity=Severity.MEDIUM,
            category="Openings",
            recommendation=f"Réduire le WWR à ≤ {SIA3801_THRESHOLDS['wwr_max'] * 100}% en réduisant la surface des fenêtres.",
        ))

        # Règles pour la ventilation
        self.rule_engine.add_rule(Rule(
            name="SIA3801_VENTILATION_RATE",
            description=f"Débit de ventilation ≥ {SIA3801_THRESHOLDS['ventilation_rate_min']} h⁻¹",
            check=lambda room: room.ventilation_rate >= SIA3801_THRESHOLDS["ventilation_rate_min"] if room.ventilation_rate is not None else False,
            severity=Severity.HIGH,
            category="Ventilation",
            recommendation=f"Augmenter le débit de ventilation à ≥ {SIA3801_THRESHOLDS['ventilation_rate_min']} h⁻¹.",
        ))

        # Règles pour les gains internes (éclairage)
        self.rule_engine.add_rule(Rule(
            name="SIA3801_LIGHTING_POWER",
            description=f"Puissance d'éclairage ≤ {SIA3801_THRESHOLDS['lighting_power_max']} W/m²",
            check=lambda room: room.internal_gains.get("lighting") is not None and room.internal_gains.get("lighting") <= SIA3801_THRESHOLDS["lighting_power_max"],
            severity=Severity.MEDIUM,
            category="Gains",
            recommendation=f"Réduire la puissance d'éclairage à ≤ {SIA3801_THRESHOLDS['lighting_power_max']} W/m².",
        ))

        # Règles pour les gains internes (équipements)
        self.rule_engine.add_rule(Rule(
            name="SIA3801_EQUIPMENT_POWER",
            description=f"Puissance des équipements ≤ {SIA3801_THRESHOLDS['equipment_power_max']} W/m²",
            check=lambda room: room.internal_gains.get("equipment") is not None and room.internal_gains.get("equipment") <= SIA3801_THRESHOLDS["equipment_power_max"],
            severity=Severity.MEDIUM,
            category="Gains",
            recommendation=f"Réduire la puissance des équipements à ≤ {SIA3801_THRESHOLDS['equipment_power_max']} W/m².",
        ))

        # Règles pour les systèmes CVC (efficacité)
        self.rule_engine.add_rule(Rule(
            name="SIA3801_HVAC_EFFICIENCY",
            description=f"Rendement des systèmes CVC ≥ {SIA3801_THRESHOLDS['hvac_efficiency_min'] * 100}%",
            check=lambda hvac: hvac.get("efficiency", 0) >= SIA3801_THRESHOLDS["hvac_efficiency_min"] if hvac.get("efficiency") is not None else False,
            severity=Severity.HIGH,
            category="HVAC",
            recommendation=f"Améliorer le rendement des systèmes CVC à ≥ {SIA3801_THRESHOLDS['hvac_efficiency_min'] * 100}%.",
        ))

    def check_all(self) -> Dict[str, Any]:
        """
        Exécute toutes les vérifications SIA 380/2 et retourne les résultats.
        
        Returns:
            Dictionnaire des résultats par catégorie.
        """
        rooms_data = self.model_analyzer.analyze_all_rooms()
        self.rule_engine.clear_alerts()
        
        results = {
            "envelope": self._check_envelope(rooms_data),
            "openings": self._check_openings(rooms_data),
            "ventilation": self._check_ventilation(rooms_data),
            "gains": self._check_gains(rooms_data),
            "hvac": self._check_hvac(rooms_data),
            "alerts": list(self.rule_engine.alerts),
        }
        return results

    def _check_envelope(self, rooms_data: List[RoomData]) -> Dict[str, Any]:
        """
        Vérifie la conformité de l'enveloppe (murs, toitures, planchers).
        
        Args:
            rooms_data: Liste des objets RoomData.
        
        Returns:
            Dictionnaire avec les alertes et le score de la catégorie.
        """
        for room in rooms_data:
            for surface in room.surfaces:
                if not surface.is_external:
                    continue
                if getattr(surface, "net_area", surface.area) <= 1e-6:
                    continue
                if surface.u_value is None:
                    self.rule_engine.add_alert(
                        rule="SIA3801_U_VALUE_MISSING",
                        description=f"U-value non disponible pour la surface externe {surface.name or surface.id}.",
                        severity=Severity.MEDIUM,
                        category="Envelope",
                        recommendation="Vérifier que la construction VE est assignée et expose une U-value exploitable.",
                        data=surface,
                    )
                    continue
                surface_type = self.model_analyzer._normalize_surface_type(surface.surface_type)
                if surface_type == "wall":
                    self.rule_engine.check_rules(["SIA3801_U_VALUE_EXTERNAL_WALL"], surface)
                elif surface_type == "roof":
                    self.rule_engine.check_rules(["SIA3801_U_VALUE_ROOF"], surface)
                elif surface_type in {"floor", "ground_floor"}:
                    self.rule_engine.check_rules(["SIA3801_U_VALUE_FLOOR"], surface)
        
        return {
            "alerts": self.rule_engine.get_alerts_by_category("Envelope"),
            "score": self._calculate_category_score("Envelope"),
        }

    def _check_openings(self, rooms_data: List[RoomData]) -> Dict[str, Any]:
        """
        Vérifie la conformité des ouvertures (fenêtres, portes).
        
        Args:
            rooms_data: Liste des objets RoomData.
        
        Returns:
            Dictionnaire avec les alertes et le score de la catégorie.
        """
        for room in rooms_data:
            for opening in room.openings:
                if not opening.is_external:
                    continue
                opening_type = self.model_analyzer._normalize_opening_type(opening.opening_type)
                if opening_type == "window":
                    if opening.u_value is not None:
                        self.rule_engine.check_rules(["SIA3801_U_VALUE_WINDOW"], opening)
                    else:
                        self.rule_engine.add_alert(
                            rule="SIA3801_WINDOW_U_VALUE_MISSING",
                            description=f"U-value non disponible pour la fenêtre externe {opening.name or opening.id}.",
                            severity=Severity.MEDIUM,
                            category="Openings",
                            recommendation="Vérifier le vitrage/la construction VE et renseigner la U-value de la fenêtre.",
                            data=opening,
                        )
                    if opening.solar_factor is not None:
                        self.rule_engine.check_rules(["SIA3801_SOLAR_FACTOR"], opening)
                    else:
                        self.rule_engine.add_alert(
                            rule="SIA3801_SOLAR_FACTOR_MISSING",
                            description=f"Facteur solaire non disponible pour la fenêtre externe {opening.name or opening.id}.",
                            severity=Severity.MEDIUM,
                            category="Openings",
                            recommendation="Vérifier les propriétés du vitrage et le facteur solaire utilisé pour les apports solaires.",
                            data=opening,
                        )
                elif opening_type == "door" and opening.u_value is not None:
                    self.rule_engine.check_rules(["SIA3801_U_VALUE_DOOR"], opening)
                elif opening_type == "door":
                    self.rule_engine.add_alert(
                        rule="SIA3801_DOOR_U_VALUE_MISSING",
                        description=f"U-value non disponible pour la porte externe {opening.name or opening.id}.",
                        severity=Severity.LOW,
                        category="Openings",
                        recommendation="Vérifier que la construction de porte expose une U-value exploitable.",
                        data=opening,
                    )
            self.rule_engine.check_rules(["SIA3801_WWR"], room)
        
        return {
            "alerts": self.rule_engine.get_alerts_by_category("Openings"),
            "score": self._calculate_category_score("Openings"),
        }

    def _check_ventilation(self, rooms_data: List[RoomData]) -> Dict[str, Any]:
        """
        Vérifie la conformité des systèmes de ventilation.
        
        Args:
            rooms_data: Liste des objets RoomData.
        
        Returns:
            Dictionnaire avec les alertes et le score de la catégorie.
        """
        for room in rooms_data:
            if room.ventilation_rate is not None:
                self.rule_engine.check_rules(["SIA3801_VENTILATION_RATE"], room)
            else:
                self.rule_engine.add_alert(
                    rule="SIA3801_VENTILATION_RATE_MISSING",
                    description=f"Débit de ventilation non disponible pour la pièce {room.name or room.id}.",
                    severity=Severity.MEDIUM,
                    category="Ventilation",
                    recommendation="Vérifier les échanges d'air VE et leurs unités afin de documenter le débit de ventilation.",
                    data=room,
                )
        
        return {
            "alerts": self.rule_engine.get_alerts_by_category("Ventilation"),
            "score": self._calculate_category_score("Ventilation"),
        }

    def _check_gains(self, rooms_data: List[RoomData]) -> Dict[str, Any]:
        """
        Vérifie la conformité des gains internes (éclairage, équipements).
        
        Args:
            rooms_data: Liste des objets RoomData.
        
        Returns:
            Dictionnaire avec les alertes et le score de la catégorie.
        """
        for room in rooms_data:
            if room.internal_gains.get("lighting") is None:
                self.rule_engine.add_alert(
                    rule="SIA3801_LIGHTING_POWER_MISSING",
                    description=f"Puissance d'éclairage non disponible pour la pièce {room.name or room.id}.",
                    severity=Severity.LOW,
                    category="Gains",
                    recommendation="Vérifier les gains internes d'éclairage du template thermique VE.",
                    data=room,
                )
            else:
                self.rule_engine.check_rules(["SIA3801_LIGHTING_POWER"], room)

            if room.internal_gains.get("equipment") is None:
                self.rule_engine.add_alert(
                    rule="SIA3801_EQUIPMENT_POWER_MISSING",
                    description=f"Puissance d'équipements non disponible pour la pièce {room.name or room.id}.",
                    severity=Severity.LOW,
                    category="Gains",
                    recommendation="Vérifier les gains internes d'équipements du template thermique VE.",
                    data=room,
                )
            else:
                self.rule_engine.check_rules(["SIA3801_EQUIPMENT_POWER"], room)
        
        return {
            "alerts": self.rule_engine.get_alerts_by_category("Gains"),
            "score": self._calculate_category_score("Gains"),
        }

    def _check_hvac(self, rooms_data: List[RoomData]) -> Dict[str, Any]:
        """
        Vérifie la conformité des systèmes CVC.
        
        Args:
            rooms_data: Liste des objets RoomData.
        
        Returns:
            Dictionnaire avec les alertes et le score de la catégorie.
        """
        for room in rooms_data:
            for hvac in room.hvac_systems:
                if hvac.get("efficiency") is not None:
                    self.rule_engine.check_rules(["SIA3801_HVAC_EFFICIENCY"], hvac)
                else:
                    self.rule_engine.add_alert(
                        rule="SIA3801_HVAC_EFFICIENCY_MISSING",
                        description=f"Rendement CVC non disponible pour le système {hvac.get('id', 'inconnu')}.",
                        severity=Severity.LOW,
                        category="HVAC",
                        recommendation="Lire les rendements depuis les systèmes Apache/ApacheHVAC ou documenter l'hypothèse utilisée.",
                        data=hvac,
                    )
        
        return {
            "alerts": self.rule_engine.get_alerts_by_category("HVAC"),
            "score": self._calculate_category_score("HVAC"),
        }

    def _calculate_category_score(self, category: str) -> float:
        """
        Calcule le score pour une catégorie donnée (0-100).
        
        Args:
            category: Catégorie à évaluer.
        
        Returns:
            Score de la catégorie (0-100).
        """
        alerts = self.rule_engine.get_alerts_by_category(category)
        if not alerts:
            return 100.0

        # Calculer le score en fonction de la sévérité des alertes
        score = 100.0
        for alert in alerts:
            if alert.severity == Severity.CRITICAL:
                score -= 25.0
            elif alert.severity == Severity.HIGH:
                score -= 15.0
            elif alert.severity == Severity.MEDIUM:
                score -= 10.0
            elif alert.severity == Severity.LOW:
                score -= 5.0
        return max(0.0, min(100.0, score))
