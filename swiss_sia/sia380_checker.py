"""
Validateur des règles SIA 380/2.
Ce module vérifie la conformité du modèle VE aux exigences de la norme suisse SIA 380/2.
"""

from typing import Any, Dict, List

from .config import SIA3802_LIMIT_VALUES, SIA3802_THRESHOLDS, SIA3802_U_VALUES
from .model_analyzer import ModelAnalyzer, RoomData
from .rule_engine import Alert, Rule, RuleEngine, Severity


class SIA3802Checker:
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
            name="SIA3802_U_VALUE_EXTERNAL_WALL",
            description=f"U-value des murs extérieurs <= {SIA3802_U_VALUES['external_wall']} W/m²K (SIA 380/2:2022, tableau 3, valeur limite)",
            check=lambda surface: surface.u_value <= SIA3802_U_VALUES["external_wall"] if surface.u_value is not None else False,
            severity=Severity.HIGH,
            category="Envelope",
            recommendation=f"Réduire la U-value à <= {SIA3802_U_VALUES['external_wall']} W/m²K ou justifier le calcul de référence complet SIA 380/2.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_U_VALUE_ROOF",
            description=f"U-value des toitures plates <= {SIA3802_U_VALUES['roof']} W/m²K (SIA 380/2:2022, tableau 3, valeur limite)",
            check=lambda surface: surface.u_value <= SIA3802_U_VALUES["roof"] if surface.u_value is not None else False,
            severity=Severity.HIGH,
            category="Envelope",
            recommendation=f"Réduire la U-value à <= {SIA3802_U_VALUES['roof']} W/m²K ou documenter le type de toiture si le seuil générique ne s'applique pas.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_U_VALUE_FLOOR",
            description=f"U-value des sols/planchers contre terrain ou non conditionné <= {SIA3802_U_VALUES['floor']} W/m²K (SIA 380/2:2022, tableau 3, valeur limite générique)",
            check=lambda surface: surface.u_value <= SIA3802_U_VALUES["floor"] if surface.u_value is not None else False,
            severity=Severity.HIGH,
            category="Envelope",
            recommendation=f"Réduire la U-value à <= {SIA3802_U_VALUES['floor']} W/m²K ou classifier plus finement le plancher (terrain, cave non conditionnée, intermédiaire).",
        ))

        # Règles pour les U-values des ouvertures
        self.rule_engine.add_rule(Rule(
            name="SIA3802_U_VALUE_WINDOW",
            description=f"U-value des fenêtres Uw <= {SIA3802_U_VALUES['window']} W/m²K (SIA 380/2:2022, tableau 2, valeur limite)",
            check=lambda opening: opening.u_value <= SIA3802_U_VALUES["window"] if opening.u_value is not None else False,
            severity=Severity.HIGH,
            category="Openings",
            recommendation=f"Vérifier vitrage/cadre et atteindre Uw <= {SIA3802_U_VALUES['window']} W/m²K, ou produire le calcul de référence complet.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_U_VALUE_DOOR",
            description=f"U-value des portes traitées avec le seuil Uw <= {SIA3802_U_VALUES['door']} W/m²K par prudence (SIA 380/2 définit les portes avec les fenêtres pour la surface)",
            check=lambda opening: opening.u_value <= SIA3802_U_VALUES["door"] if opening.u_value is not None else False,
            severity=Severity.MEDIUM,
            category="Openings",
            recommendation=f"Vérifier si la porte doit être traitée comme fenêtre/élément opaque et viser <= {SIA3802_U_VALUES['door']} W/m²K si ce regroupement s'applique.",
        ))

        # Règles pour le facteur solaire
        self.rule_engine.add_rule(Rule(
            name="SIA3802_SOLAR_FACTOR",
            description=f"Facteur solaire du vitrage g_perp <= {SIA3802_THRESHOLDS['solar_factor_max']} (SIA 380/2:2022, tableau 2, valeur limite)",
            check=lambda opening: opening.solar_factor <= SIA3802_THRESHOLDS["solar_factor_max"] if opening.solar_factor is not None else False,
            severity=Severity.MEDIUM,
            category="Openings",
            recommendation=f"Utiliser/documenter des vitrages avec g_perp <= {SIA3802_THRESHOLDS['solar_factor_max']} et vérifier que la valeur VE correspond bien au g SIA.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_VISIBLE_TRANSMITTANCE",
            description=f"Transmission lumineuse du vitrage tau >= {SIA3802_THRESHOLDS['light_transmittance_min']} (SIA 380/2:2022, tableau 2, valeur de référence).",
            check=lambda opening: opening.visible_transmittance >= SIA3802_THRESHOLDS["light_transmittance_min"] if opening.visible_transmittance is not None else False,
            severity=Severity.LOW,
            category="Openings",
            recommendation="Extraire ou documenter la transmission lumineuse du vitrage; si la valeur VE n'est pas comparable, joindre une fiche vitrage auditable.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_FRAME_FRACTION",
            description=f"Fraction de cadre de fenêtre ff <= {SIA3802_THRESHOLDS['window_frame_fraction']} (SIA 380/2:2022, tableau 2, valeur de référence).",
            check=lambda opening: opening.frame_fraction <= SIA3802_THRESHOLDS["window_frame_fraction"] if opening.frame_fraction is not None else False,
            severity=Severity.LOW,
            category="Openings",
            recommendation="Extraire ou documenter la fraction de cadre de fenêtre; si VE ne l'expose pas, joindre une justification façade/vitrage.",
        ))

        # Règles pour le WWR (Window-to-Wall Ratio)
        self.rule_engine.add_rule(Rule(
            name="SIA3802_WWR",
            description=f"Indicateur de revue WWR > {SIA3802_THRESHOLDS['wwr_max'] * 100}% (SIA 380/2 renvoie le taux de surfaces vitrées à SIA 2024, pas à un seuil fixe)",
            check=lambda room: self.model_analyzer.calculate_wwr(room) <= SIA3802_THRESHOLDS["wwr_max"],
            severity=Severity.LOW,
            category="Design Review",
            recommendation="Traiter le WWR comme un indicateur de risque solaire: confirmer le taux de surfaces vitrées applicable via SIA 2024 et le calcul de référence.",
        ))

        # Règles pour la ventilation
        self.rule_engine.add_rule(Rule(
            name="SIA3802_VENTILATION_RATE",
            description="Débit de ventilation présent; le contrôle SIA 380/2 exige SIA 2024 et le tableau 4, pas un seuil h-1 unique.",
            check=lambda room: True,
            severity=Severity.LOW,
            category="Data Completeness",
            recommendation="Comparer les débits fournis/extraits aux exigences SIA 2024 et qualifier le type de régulation selon SIA 380/2 tableau 4.",
        ))

        # Règles pour les gains internes (éclairage)
        self.rule_engine.add_rule(Rule(
            name="SIA3802_INFILTRATION_M3_H_M2",
            description=f"Infiltration <= {SIA3802_LIMIT_VALUES['infiltration_m3_h_m2']} m3/(h.m2) quand la valeur VE est comparable (SIA 380/2:2022, tableau 2).",
            check=lambda room: room.infiltration_m3_h_m2 <= SIA3802_LIMIT_VALUES["infiltration_m3_h_m2"] if room.infiltration_m3_h_m2 is not None else False,
            severity=Severity.MEDIUM,
            category="Ventilation",
            recommendation="Verifier l'unite d'infiltration VE et documenter la conversion retenue vers m3/(h.m2).",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_LIGHTING_POWER",
            description="Puissance d'éclairage présente; SIA 380/2 renvoie à SIA 387/4 et SIA 2024, pas à un seuil W/m² unique.",
            check=lambda room: True,
            severity=Severity.LOW,
            category="Data Completeness",
            recommendation="Vérifier la puissance et la commande de l'éclairage avec SIA 387/4, tableau 10, et les usages SIA 2024.",
        ))

        # Règles pour les gains internes (équipements)
        self.rule_engine.add_rule(Rule(
            name="SIA3802_EQUIPMENT_POWER",
            description="Puissance d'équipements présente; SIA 380/2 renvoie aux usages SIA 2024, pas à un seuil W/m² unique.",
            check=lambda room: True,
            severity=Severity.LOW,
            category="Data Completeness",
            recommendation="Comparer les appareils, profils et apports internes aux valeurs SIA 2024 applicables à l'usage du local.",
        ))

        # Règles pour les systèmes CVC (efficacité)
        self.rule_engine.add_rule(Rule(
            name="SIA3802_HVAC_EFFICIENCY",
            description="Efficacité CVC présente; SIA 380/2 utilise des tableaux EER/SEER/SCOP et la validation SIA 4010, pas un rendement unique.",
            check=lambda hvac: True,
            severity=Severity.LOW,
            category="Data Completeness",
            recommendation="Qualifier le système, sa puissance et son type pour comparer aux tableaux SIA 380/2 5 à 9 et fournir la preuve SIA 4010 applicable.",
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
        if not rooms_data:
            self.rule_engine.add_alert(
                rule="SIA3802_MODEL_NOT_CHECKABLE_ENVELOPE",
                description="Aucune piece VE exploitable n'a ete analysee pour controler l'enveloppe.",
                severity=Severity.CRITICAL,
                category="Envelope",
                recommendation="Verifier que le modele VE actif contient des rooms thermiques et que le script est lance depuis le bon projet.",
                data=None,
            )
        elif not any(
            surface.is_external and getattr(surface, "net_area", surface.area) > 1e-6
            for room in rooms_data
            for surface in room.surfaces
        ):
            self.rule_engine.add_alert(
                rule="SIA3802_EXTERNAL_ENVELOPE_MISSING",
                description="Aucune surface externe exploitable n'a ete extraite pour le controle SIA 380/2.",
                severity=Severity.CRITICAL,
                category="Envelope",
                recommendation="Verifier les types de surfaces, adjacences et constructions VE avant de conclure sur l'enveloppe.",
                data=None,
            )

        for room in rooms_data:
            for surface in room.surfaces:
                if not surface.is_external:
                    continue
                if getattr(surface, "net_area", surface.area) <= 1e-6:
                    continue
                if surface.u_value is None:
                    self.rule_engine.add_alert(
                        rule="SIA3802_U_VALUE_MISSING",
                        description=f"U-value non disponible pour la surface externe {surface.name or surface.id}.",
                        severity=Severity.MEDIUM,
                        category="Envelope",
                        recommendation="Vérifier que la construction VE est assignée et expose une U-value exploitable.",
                        data=surface,
                    )
                    continue
                surface_type = self.model_analyzer._normalize_surface_type(surface.surface_type)
                if surface_type == "wall":
                    self.rule_engine.check_rules(["SIA3802_U_VALUE_EXTERNAL_WALL"], surface)
                elif surface_type == "roof":
                    self.rule_engine.check_rules(["SIA3802_U_VALUE_ROOF"], surface)
                elif surface_type in {"floor", "ground_floor"}:
                    self.rule_engine.check_rules(["SIA3802_U_VALUE_FLOOR"], surface)
        
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
        if not rooms_data:
            self.rule_engine.add_alert(
                rule="SIA3802_MODEL_NOT_CHECKABLE_OPENINGS",
                description="Aucune piece VE exploitable n'a ete analysee pour controler les ouvertures.",
                severity=Severity.CRITICAL,
                category="Openings",
                recommendation="Verifier que le modele VE actif contient des rooms thermiques et des surfaces externes.",
                data=None,
            )

        for room in rooms_data:
            for opening in room.openings:
                if not opening.is_external:
                    continue
                opening_type = self.model_analyzer._normalize_opening_type(opening.opening_type)
                if opening_type == "window":
                    if opening.u_value is not None:
                        self.rule_engine.check_rules(["SIA3802_U_VALUE_WINDOW"], opening)
                    else:
                        self.rule_engine.add_alert(
                            rule="SIA3802_WINDOW_U_VALUE_MISSING",
                            description=f"U-value non disponible pour la fenêtre externe {opening.name or opening.id}.",
                            severity=Severity.MEDIUM,
                            category="Openings",
                            recommendation="Vérifier le vitrage/la construction VE et renseigner la U-value de la fenêtre.",
                            data=opening,
                        )
                    if opening.solar_factor is not None:
                        self.rule_engine.check_rules(["SIA3802_SOLAR_FACTOR"], opening)
                    else:
                        self.rule_engine.add_alert(
                            rule="SIA3802_SOLAR_FACTOR_MISSING",
                            description=f"Facteur solaire non disponible pour la fenêtre externe {opening.name or opening.id}.",
                            severity=Severity.MEDIUM,
                            category="Openings",
                            recommendation="Vérifier les propriétés du vitrage et le facteur solaire utilisé pour les apports solaires.",
                            data=opening,
                        )
                    if getattr(opening, "visible_transmittance", None) is not None:
                        self.rule_engine.check_rules(["SIA3802_VISIBLE_TRANSMITTANCE"], opening)
                    else:
                        self.rule_engine.add_alert(
                            rule="SIA3802_VISIBLE_TRANSMITTANCE_MISSING",
                            description=f"Transmission lumineuse non disponible pour la fenêtre externe {opening.name or opening.id}.",
                            severity=Severity.LOW,
                            category="Openings",
                            recommendation="Fournir tau/visible transmittance du vitrage depuis VE/CDB ou via fiche technique vitrage.",
                            data=opening,
                        )
                    if getattr(opening, "frame_fraction", None) is not None:
                        self.rule_engine.check_rules(["SIA3802_FRAME_FRACTION"], opening)
                    else:
                        self.rule_engine.add_alert(
                            rule="SIA3802_FRAME_FRACTION_MISSING",
                            description=f"Fraction de cadre non disponible pour la fenêtre externe {opening.name or opening.id}.",
                            severity=Severity.LOW,
                            category="Openings",
                            recommendation="Fournir la fraction de cadre ff ou confirmer que le calcul de référence SIA utilise une valeur externe documentée.",
                            data=opening,
                        )
                    if not getattr(opening, "shading_type", None):
                        self.rule_engine.add_alert(
                            rule="SIA3802_SOLAR_PROTECTION_TYPE_MISSING",
                            description=f"Type de protection solaire non disponible pour la fenêtre externe {opening.name or opening.id}.",
                            severity=Severity.LOW,
                            category="Openings",
                            recommendation="Documenter le type de protection solaire selon SIA 380/2 tableau 10 et la variante SIA 4010 test 2/2A applicable.",
                            data=opening,
                        )
                    if not getattr(opening, "shading_control", None):
                        self.rule_engine.add_alert(
                            rule="SIA3802_SOLAR_PROTECTION_CONTROL_MISSING",
                            description=f"Commande de protection solaire non disponible pour la fenêtre externe {opening.name or opening.id}.",
                            severity=Severity.LOW,
                            category="Openings",
                            recommendation="Documenter la stratégie de commande des protections solaires et sa correspondance SIA 387/4/SIA 4010.",
                            data=opening,
                        )
                    if getattr(opening, "g_total", None) is None:
                        self.rule_engine.add_alert(
                            rule="SIA3802_G_TOTAL_WITH_SHADING_MISSING",
                            description=f"g_total vitrage + protection solaire non disponible pour la fenêtre externe {opening.name or opening.id}.",
                            severity=Severity.LOW,
                            category="Openings",
                            recommendation="Fournir le g_total actif si la protection solaire est prise en compte, ou documenter pourquoi seul g_perp est utilisé.",
                            data=opening,
                        )
                elif opening_type == "door" and opening.u_value is not None:
                    self.rule_engine.check_rules(["SIA3802_U_VALUE_DOOR"], opening)
                elif opening_type == "door":
                    self.rule_engine.add_alert(
                        rule="SIA3802_DOOR_U_VALUE_MISSING",
                        description=f"U-value non disponible pour la porte externe {opening.name or opening.id}.",
                        severity=Severity.LOW,
                        category="Openings",
                        recommendation="Vérifier que la construction de porte expose une U-value exploitable.",
                        data=opening,
                    )
            self.rule_engine.check_rules(["SIA3802_WWR"], room)
        
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
        if not rooms_data:
            self.rule_engine.add_alert(
                rule="SIA3802_MODEL_NOT_CHECKABLE_VENTILATION",
                description="Aucune piece VE exploitable n'a ete analysee pour controler la ventilation et l'infiltration.",
                severity=Severity.CRITICAL,
                category="Ventilation",
                recommendation="Verifier que le modele VE actif contient des rooms thermiques avec donnees d'echanges d'air.",
                data=None,
            )

        for room in rooms_data:
            if room.ventilation_rate is not None:
                self.rule_engine.check_rules(["SIA3802_VENTILATION_RATE"], room)
                ventilation_m3_h_m2 = getattr(room, "ventilation_m3_h_m2", None)
                if ventilation_m3_h_m2 is None:
                    self.rule_engine.add_alert(
                        rule="SIA3802_VENTILATION_UNIT_NOT_COMPARABLE",
                        description=f"Débit de ventilation présent pour la pièce {room.name or room.id}, mais pas normalisé en m3/(h.m2).",
                        severity=Severity.LOW,
                        category="Ventilation",
                        recommendation="Exporter ou convertir le débit d'air neuf par surface pour sélectionner la bande du tableau 4 SIA 380/2.",
                        data=room,
                    )
                else:
                    band = self._ventilation_band(ventilation_m3_h_m2)
                    self.rule_engine.add_alert(
                        rule="SIA3802_VENTILATION_CONTROL_EVIDENCE_MISSING",
                        description=(
                            f"Débit de ventilation {ventilation_m3_h_m2:.3g} m3/(h.m2) "
                            f"pour la pièce {room.name or room.id}; bande tableau 4: {band}. "
                            "La stratégie monozone/multizone et commande ventilateur n'est pas encore prouvée."
                        ),
                        severity=Severity.LOW,
                        category="Ventilation",
                        recommendation="Documenter type système, FAN_CTRL, capteurs/occupation/gaz et réduction de débit pour valider la commande SIA 380/2 tableau 4.",
                        data=room,
                    )
            else:
                self.rule_engine.add_alert(
                    rule="SIA3802_VENTILATION_RATE_MISSING",
                    description=f"Débit de ventilation non disponible pour la pièce {room.name or room.id}.",
                    severity=Severity.MEDIUM,
                    category="Ventilation",
                    recommendation="Vérifier les échanges d'air VE et leurs unités afin de documenter le débit de ventilation.",
                    data=room,
                )
        
            if getattr(room, "infiltration_m3_h_m2", None) is not None:
                self.rule_engine.check_rules(["SIA3802_INFILTRATION_M3_H_M2"], room)
            elif getattr(room, "infiltration_rate", None) is not None:
                self.rule_engine.add_alert(
                    rule="SIA3802_INFILTRATION_UNIT_NOT_COMPARABLE",
                    description=f"Infiltration presente pour la piece {room.name or room.id}, mais pas dans une unite directement comparable a m3/(h.m2).",
                    severity=Severity.LOW,
                    category="Ventilation",
                    recommendation="Documenter l'unite VE et fournir la conversion vers m3/(h.m2) avant verdict SIA 380/2 sur l'infiltration.",
                    data=room,
                )
            else:
                self.rule_engine.add_alert(
                    rule="SIA3802_INFILTRATION_MISSING",
                    description=f"Infiltration non disponible pour la piece {room.name or room.id}.",
                    severity=Severity.MEDIUM,
                    category="Ventilation",
                    recommendation="Verifier les echanges d'air VE de type infiltration et la valeur du tableau 2 SIA 380/2.",
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
        if not rooms_data:
            self.rule_engine.add_alert(
                rule="SIA3802_MODEL_NOT_CHECKABLE_GAINS",
                description="Aucune piece VE exploitable n'a ete analysee pour controler les gains internes.",
                severity=Severity.CRITICAL,
                category="Gains",
                recommendation="Verifier que le modele VE actif contient des rooms thermiques avec templates d'occupation, eclairage et equipements.",
                data=None,
            )

        for room in rooms_data:
            if room.internal_gains.get("lighting") is None:
                self.rule_engine.add_alert(
                    rule="SIA3802_LIGHTING_POWER_MISSING",
                    description=f"Puissance d'éclairage non disponible pour la pièce {room.name or room.id}.",
                    severity=Severity.LOW,
                    category="Gains",
                    recommendation="Vérifier les gains internes d'éclairage du template thermique VE.",
                    data=room,
                )
            else:
                self.rule_engine.check_rules(["SIA3802_LIGHTING_POWER"], room)

            if room.internal_gains.get("equipment") is None:
                self.rule_engine.add_alert(
                    rule="SIA3802_EQUIPMENT_POWER_MISSING",
                    description=f"Puissance d'équipements non disponible pour la pièce {room.name or room.id}.",
                    severity=Severity.LOW,
                    category="Gains",
                    recommendation="Vérifier les gains internes d'équipements du template thermique VE.",
                    data=room,
                )
            else:
                self.rule_engine.check_rules(["SIA3802_EQUIPMENT_POWER"], room)
        
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
        if not rooms_data:
            self.rule_engine.add_alert(
                rule="SIA3802_MODEL_NOT_CHECKABLE_HVAC",
                description="Aucune piece VE exploitable n'a ete analysee pour controler les systemes CVC.",
                severity=Severity.CRITICAL,
                category="HVAC",
                recommendation="Verifier que le modele VE actif contient des rooms thermiques avec donnees Apache Systems.",
                data=None,
            )

        for room in rooms_data:
            if not room.hvac_systems:
                self.rule_engine.add_alert(
                    rule="SIA3802_HVAC_SYSTEM_MISSING",
                    description=f"Aucun systeme CVC extrait pour la piece {room.name or room.id}.",
                    severity=Severity.LOW,
                    category="HVAC",
                    recommendation="Verifier Apache Systems/ApacheHVAC et documenter si la piece est volontairement non conditionnee.",
                    data=room,
                )
            for hvac in room.hvac_systems:
                if hvac.get("efficiency") is not None:
                    self.rule_engine.check_rules(["SIA3802_HVAC_EFFICIENCY"], hvac)
                else:
                    self.rule_engine.add_alert(
                        rule="SIA3802_HVAC_EFFICIENCY_MISSING",
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

        if any(self._is_blocking_not_checkable_alert(alert) for alert in alerts):
            return 0.0

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

    @staticmethod
    def _is_blocking_not_checkable_alert(alert: Alert) -> bool:
        """Return true when a category cannot produce a meaningful SIA 380/2 score."""
        rule = str(alert.rule or "").upper()
        return alert.severity == Severity.CRITICAL and (
            "MODEL_NOT_CHECKABLE" in rule
            or "EXTERNAL_ENVELOPE_MISSING" in rule
        )

    @staticmethod
    def _ventilation_band(value_m3_h_m2: float) -> str:
        """Return the SIA 380/2 table 4 airflow band for normalized airflow."""
        if value_m3_h_m2 <= 3:
            return "<=3"
        if value_m3_h_m2 <= 6:
            return "3-6"
        return ">6"


# Backward-compatible alias for older launchers or notebooks.
SIA3801Checker = SIA3802Checker
