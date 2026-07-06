"""SIA 380/2 checker for extracted IESVE model data.

This module evaluates the available VE data against the automated/readiness
checks implemented for SIA 380/2:2022. It deliberately keeps some topics as
evidence/readiness checks when the standard requires a reference calculation,
SIA 2024 mapping or official SIA 4010 validation evidence.
"""

from typing import Any, Dict, List

from .config import SIA3802_LIMIT_VALUES, SIA3802_THRESHOLDS, SIA3802_U_VALUES
from .model_analyzer import ModelAnalyzer, RoomData
from .rule_engine import Alert, Rule, RuleEngine, Severity
from .value_integrity import add_value_integrity_alerts


class SIA3802Checker:
    """Check VE model data against the implemented SIA 380/2 rules."""

    def __init__(self, model_analyzer: ModelAnalyzer, rule_engine: RuleEngine):
        """Initialize the SIA 380/2 checker."""
        self.model_analyzer = model_analyzer
        self.rule_engine = rule_engine
        self._setup_rules()

    def _setup_rules(self):
        """Register SIA 380/2 rules in the shared rule engine."""
        self.rule_engine.add_rule(Rule(
            name="SIA3802_U_VALUE_EXTERNAL_WALL",
            description=f"External wall U-value <= {SIA3802_U_VALUES['external_wall']} W/m2K (SIA 380/2:2022, table 3, limit value).",
            check=lambda surface: surface.u_value <= SIA3802_U_VALUES["external_wall"] if surface.u_value is not None else False,
            severity=Severity.HIGH,
            category="Envelope",
            recommendation=f"Reduce/document the wall construction to U <= {SIA3802_U_VALUES['external_wall']} W/m2K or provide the complete SIA 380/2 reference-calculation justification.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_U_VALUE_ROOF",
            description=f"Flat roof U-value <= {SIA3802_U_VALUES['roof']} W/m2K (SIA 380/2:2022, table 3, limit value).",
            check=lambda surface: surface.u_value <= SIA3802_U_VALUES["roof"] if surface.u_value is not None else False,
            severity=Severity.HIGH,
            category="Envelope",
            recommendation=f"Reduce/document the roof construction to U <= {SIA3802_U_VALUES['roof']} W/m2K or justify why the generic roof threshold does not apply.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_U_VALUE_FLOOR",
            description=f"Ground or unconditioned-floor U-value <= {SIA3802_U_VALUES['floor']} W/m2K (SIA 380/2:2022, table 3, generic limit value).",
            check=lambda surface: surface.u_value <= SIA3802_U_VALUES["floor"] if surface.u_value is not None else False,
            severity=Severity.HIGH,
            category="Envelope",
            recommendation=f"Reduce/document the floor construction to U <= {SIA3802_U_VALUES['floor']} W/m2K or classify the floor boundary condition more precisely.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_U_VALUE_WINDOW",
            description=f"Window Uw <= {SIA3802_U_VALUES['window']} W/m2K (SIA 380/2:2022, table 2, limit value).",
            check=lambda opening: opening.u_value <= SIA3802_U_VALUES["window"] if opening.u_value is not None else False,
            severity=Severity.HIGH,
            category="Openings",
            recommendation=f"Check glazing/frame data and reach Uw <= {SIA3802_U_VALUES['window']} W/m2K, or provide the complete reference calculation.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_U_VALUE_DOOR",
            description=f"Door U-value checked conservatively against Uw <= {SIA3802_U_VALUES['door']} W/m2K where the opening is treated like a window/opening.",
            check=lambda opening: opening.u_value <= SIA3802_U_VALUES["door"] if opening.u_value is not None else False,
            severity=Severity.MEDIUM,
            category="Openings",
            recommendation=f"Confirm whether the door must be treated as a window/opening or opaque element, then target <= {SIA3802_U_VALUES['door']} W/m2K if this grouping applies.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_SOLAR_FACTOR",
            description=f"Glazing solar factor g_perp <= {SIA3802_THRESHOLDS['solar_factor_max']} (SIA 380/2:2022, table 2, limit value).",
            check=lambda opening: opening.solar_factor <= SIA3802_THRESHOLDS["solar_factor_max"] if opening.solar_factor is not None else False,
            severity=Severity.MEDIUM,
            category="Openings",
            recommendation=f"Use/document glazing with EN 410 g_perp <= {SIA3802_THRESHOLDS['solar_factor_max']} and keep the VE value mapping evidence.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_VISIBLE_TRANSMITTANCE",
            description=f"Glazing visible transmittance tau_v >= {SIA3802_THRESHOLDS['light_transmittance_min']} (SIA 380/2:2022, table 2, reference value).",
            check=lambda opening: opening.visible_transmittance >= SIA3802_THRESHOLDS["light_transmittance_min"] if opening.visible_transmittance is not None else False,
            severity=Severity.LOW,
            category="Openings",
            recommendation="Extract or document glazing visible transmittance; if the VE value is not comparable, attach an auditable glazing datasheet.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_FRAME_FRACTION",
            description=f"Window frame fraction ff <= {SIA3802_THRESHOLDS['window_frame_fraction']} (SIA 380/2:2022, table 2, reference value).",
            check=lambda opening: opening.frame_fraction <= SIA3802_THRESHOLDS["window_frame_fraction"] if opening.frame_fraction is not None else False,
            severity=Severity.LOW,
            category="Openings",
            recommendation="Check the extracted frame fraction; if it exceeds 0.25, correct the window construction or attach facade/glazing justification.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_WWR",
            description=f"Design-review indicator: WWR > {SIA3802_THRESHOLDS['wwr_max'] * 100}% (SIA 380/2 refers glazed-area ratios to SIA 2024/reference calculation, not a standalone fixed limit).",
            check=lambda room: self.model_analyzer.calculate_wwr(room) <= SIA3802_THRESHOLDS["wwr_max"],
            severity=Severity.LOW,
            category="Design Review",
            recommendation="Treat WWR as a solar-risk indicator: confirm the applicable glazed-area ratio through SIA 2024 and the reference calculation.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_VENTILATION_RATE",
            description="Ventilation rate is present; SIA 380/2 control requires SIA 2024 and table 4, not a single h-1 threshold.",
            check=lambda room: True,
            severity=Severity.LOW,
            category="Data Completeness",
            recommendation="Compare supplied/extracted airflow rates with SIA 2024 requirements and qualify the control type according to SIA 380/2 table 4.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_INFILTRATION_M3_H_M2",
            description=f"Infiltration <= {SIA3802_LIMIT_VALUES['infiltration_m3_h_m2']} m3/(h.m2) when the VE value is comparable (SIA 380/2:2022, table 2).",
            check=lambda room: room.infiltration_m3_h_m2 <= SIA3802_LIMIT_VALUES["infiltration_m3_h_m2"] if room.infiltration_m3_h_m2 is not None else False,
            severity=Severity.MEDIUM,
            category="Ventilation",
            recommendation="Confirm the VE infiltration unit and document the retained conversion to m3/(h.m2).",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_LIGHTING_POWER",
            description="Lighting power is present; SIA 380/2 refers to SIA 387/4 and SIA 2024, not a single W/m2 threshold.",
            check=lambda room: True,
            severity=Severity.LOW,
            category="Data Completeness",
            recommendation="Check lighting power and control strategy against SIA 387/4 table 10 and the applicable SIA 2024 use profile.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_EQUIPMENT_POWER",
            description="Equipment power is present; SIA 380/2 refers to SIA 2024 use profiles, not a single W/m2 threshold.",
            check=lambda room: True,
            severity=Severity.LOW,
            category="Data Completeness",
            recommendation="Compare appliances, profiles and internal gains with the applicable SIA 2024 room-use values.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_HVAC_EFFICIENCY",
            description="HVAC efficiency is present; SIA 380/2 uses EER/SEER/SCOP tables and SIA 4010 validation, not one generic efficiency.",
            check=lambda hvac: True,
            severity=Severity.LOW,
            category="Data Completeness",
            recommendation="Classify system type, capacity band and performance value to compare against SIA 380/2 tables 5 to 9 and provide the applicable SIA 4010 evidence.",
        ))

    def check_all(self) -> Dict[str, Any]:
        """Run all implemented SIA 380/2 checks and return category results."""
        rooms_data = self.model_analyzer.analyze_all_rooms()
        self.rule_engine.clear_alerts()

        envelope = self._check_envelope(rooms_data)
        openings = self._check_openings(rooms_data)
        ventilation = self._check_ventilation(rooms_data)
        gains = self._check_gains(rooms_data)
        hvac = self._check_hvac(rooms_data)
        value_integrity = add_value_integrity_alerts(self.rule_engine, rooms_data)

        results = {
            "envelope": envelope,
            "openings": openings,
            "ventilation": ventilation,
            "gains": gains,
            "hvac": hvac,
            "value_integrity": value_integrity,
            "alerts": list(self.rule_engine.alerts),
        }
        return results

    def _check_envelope(self, rooms_data: List[RoomData]) -> Dict[str, Any]:
        """Check external envelope surfaces: walls, roofs and floors."""
        if not rooms_data:
            self.rule_engine.add_alert(
                rule="SIA3802_MODEL_NOT_CHECKABLE_ENVELOPE",
                description="No usable VE room was analysed for the envelope checks.",
                severity=Severity.CRITICAL,
                category="Envelope",
                recommendation="Confirm the active VE model contains thermal rooms and rerun the script from the correct project.",
                data=None,
            )
        elif not any(
            surface.is_external and getattr(surface, "net_area", surface.area) > 1e-6
            for room in rooms_data
            for surface in room.surfaces
        ):
            self.rule_engine.add_alert(
                rule="SIA3802_EXTERNAL_ENVELOPE_MISSING",
                description="No usable external surface was extracted for the SIA 380/2 envelope checks.",
                severity=Severity.CRITICAL,
                category="Envelope",
                recommendation="Check VE surface types, adjacencies and constructions before drawing any envelope conclusion.",
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
                        description=f"U-value is not available for external surface {surface.name or surface.id}.",
                        severity=Severity.MEDIUM,
                        category="Envelope",
                        recommendation="Check that the VE construction is assigned and exposes a usable U-value.",
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
        """Check external openings: windows, glazing and doors."""
        if not rooms_data:
            self.rule_engine.add_alert(
                rule="SIA3802_MODEL_NOT_CHECKABLE_OPENINGS",
                description="No usable VE room was analysed for the opening checks.",
                severity=Severity.CRITICAL,
                category="Openings",
                recommendation="Confirm the active VE model contains thermal rooms and external surfaces.",
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
                            description=f"U-value is not available for external window {opening.name or opening.id}.",
                            severity=Severity.MEDIUM,
                            category="Openings",
                            recommendation="Check glazing/frame construction data and provide the window U-value.",
                            data=opening,
                        )

                    if opening.solar_factor is not None and self._is_sia_comparable_g_value(opening):
                        self.rule_engine.check_rules(["SIA3802_SOLAR_FACTOR"], opening)
                    elif opening.solar_factor is not None:
                        self.rule_engine.add_alert(
                            rule="SIA3802_G_VALUE_SOURCE_NOT_COMPARABLE",
                            description=f"Solar factor is present for external window {opening.name or opening.id}, but its source is not proven as EN 410 g_perp.",
                            severity=Severity.MEDIUM,
                            category="Openings",
                            recommendation="Use VECdbConstruction.get_g_values().bs_en_410 or manufacturer evidence before comparing to the SIA 380/2 g-value limit.",
                            data=opening,
                        )
                    else:
                        self.rule_engine.add_alert(
                            rule="SIA3802_SOLAR_FACTOR_MISSING",
                            description=f"Solar factor is not available for external window {opening.name or opening.id}.",
                            severity=Severity.MEDIUM,
                            category="Openings",
                            recommendation="Check glazing properties and the solar-factor value used for solar gains.",
                            data=opening,
                        )

                    if getattr(opening, "visible_transmittance", None) is not None:
                        self.rule_engine.check_rules(["SIA3802_VISIBLE_TRANSMITTANCE"], opening)
                    else:
                        self.rule_engine.add_alert(
                            rule="SIA3802_VISIBLE_TRANSMITTANCE_MISSING",
                            description=f"Visible transmittance is not available for external window {opening.name or opening.id}.",
                            severity=Severity.LOW,
                            category="Openings",
                            recommendation="Provide glazing tau_v from VE/CDB or from an auditable glazing datasheet.",
                            data=opening,
                        )

                    if getattr(opening, "frame_fraction", None) is not None:
                        self.rule_engine.check_rules(["SIA3802_FRAME_FRACTION"], opening)
                    else:
                        self.rule_engine.add_alert(
                            rule="SIA3802_FRAME_FRACTION_MISSING",
                            description=f"Frame fraction is not available for external window {opening.name or opening.id}.",
                            severity=Severity.LOW,
                            category="Openings",
                            recommendation="Provide frame fraction ff or confirm that the SIA reference calculation uses an external documented value.",
                            data=opening,
                        )

                    if not getattr(opening, "shading_type", None):
                        self.rule_engine.add_alert(
                            rule="SIA3802_SOLAR_PROTECTION_TYPE_MISSING",
                            description=f"Solar-protection type is not available for external window {opening.name or opening.id}.",
                            severity=Severity.LOW,
                            category="Openings",
                            recommendation="Document the solar-protection type according to SIA 380/2 table 10 and the applicable SIA 4010 test 2/2A variant.",
                            data=opening,
                        )

                    if not getattr(opening, "shading_control", None):
                        self.rule_engine.add_alert(
                            rule="SIA3802_SOLAR_PROTECTION_CONTROL_MISSING",
                            description=f"Solar-protection control is not available for external window {opening.name or opening.id}.",
                            severity=Severity.LOW,
                            category="Openings",
                            recommendation="Document the solar-protection control strategy and its SIA 387/4 / SIA 4010 mapping.",
                            data=opening,
                        )

                    solar_factor = getattr(opening, "solar_factor", None)
                    if (
                        getattr(opening, "g_total", None) is None
                        and solar_factor is not None
                        and solar_factor > SIA3802_THRESHOLDS["solar_factor_max"]
                    ):
                        self.rule_engine.add_alert(
                            rule="SIA3802_G_TOTAL_WITH_SHADING_MISSING",
                            description=f"Active glazing-plus-shading g_total is not available for external window {opening.name or opening.id}, while g_perp is above the SIA g-limit.",
                            severity=Severity.LOW,
                            category="Openings",
                            recommendation="Provide active g_total if solar protection is used for compliance, or replace/document glazing with EN 410 g_perp <= the SIA limit.",
                            data=opening,
                        )
                elif opening_type == "door" and opening.u_value is not None:
                    self.rule_engine.check_rules(["SIA3802_U_VALUE_DOOR"], opening)
                elif opening_type == "door":
                    self.rule_engine.add_alert(
                        rule="SIA3802_DOOR_U_VALUE_MISSING",
                        description=f"U-value is not available for external door {opening.name or opening.id}.",
                        severity=Severity.LOW,
                        category="Openings",
                        recommendation="Check that the door construction exposes a usable U-value.",
                        data=opening,
                    )
            self.rule_engine.check_rules(["SIA3802_WWR"], room)

        return {
            "alerts": self.rule_engine.get_alerts_by_category("Openings"),
            "score": self._calculate_category_score("Openings"),
        }

    def _check_ventilation(self, rooms_data: List[RoomData]) -> Dict[str, Any]:
        """Check ventilation and infiltration evidence."""
        if not rooms_data:
            self.rule_engine.add_alert(
                rule="SIA3802_MODEL_NOT_CHECKABLE_VENTILATION",
                description="No usable VE room was analysed for ventilation and infiltration checks.",
                severity=Severity.CRITICAL,
                category="Ventilation",
                recommendation="Confirm the active VE model contains thermal rooms with air-exchange data.",
                data=None,
            )

        for room in rooms_data:
            if room.ventilation_rate is not None:
                self.rule_engine.check_rules(["SIA3802_VENTILATION_RATE"], room)
                ventilation_m3_h_m2 = getattr(room, "ventilation_m3_h_m2", None)
                if ventilation_m3_h_m2 is None:
                    self.rule_engine.add_alert(
                        rule="SIA3802_VENTILATION_UNIT_NOT_COMPARABLE",
                        description=f"Ventilation rate is present for room {room.name or room.id}, but it is not normalized to m3/(h.m2).",
                        severity=Severity.LOW,
                        category="Ventilation",
                        recommendation="Export or convert outdoor airflow per floor area to select the applicable SIA 380/2 table 4 band.",
                        data=room,
                    )
                else:
                    band = self._ventilation_band(ventilation_m3_h_m2)
                    self.rule_engine.add_alert(
                        rule="SIA3802_VENTILATION_CONTROL_EVIDENCE_MISSING",
                        description=(
                            f"Ventilation rate {ventilation_m3_h_m2:.3g} m3/(h.m2) "
                            f"for room {room.name or room.id}; table 4 band: {band}. "
                            "Single-zone/multizone strategy and fan-control evidence are not proven yet."
                        ),
                        severity=Severity.LOW,
                        category="Ventilation",
                        recommendation="Document system type, FAN_CTRL, occupancy/gas sensors and airflow reduction to validate SIA 380/2 table 4 control.",
                        data=room,
                    )
            else:
                self.rule_engine.add_alert(
                    rule="SIA3802_VENTILATION_RATE_MISSING",
                    description=f"Ventilation rate is not available for room {room.name or room.id}.",
                    severity=Severity.MEDIUM,
                    category="Ventilation",
                    recommendation="Check VE air exchanges and units to document the ventilation rate.",
                    data=room,
                )

            if getattr(room, "infiltration_m3_h_m2", None) is not None:
                self.rule_engine.check_rules(["SIA3802_INFILTRATION_M3_H_M2"], room)
            elif getattr(room, "infiltration_rate", None) is not None:
                self.rule_engine.add_alert(
                    rule="SIA3802_INFILTRATION_UNIT_NOT_COMPARABLE",
                    description=f"Infiltration is present for room {room.name or room.id}, but not in a directly comparable m3/(h.m2) unit.",
                    severity=Severity.LOW,
                    category="Ventilation",
                    recommendation="Document the VE unit and provide the conversion to m3/(h.m2) before any SIA 380/2 infiltration verdict.",
                    data=room,
                )
            else:
                self.rule_engine.add_alert(
                    rule="SIA3802_INFILTRATION_MISSING",
                    description=f"Infiltration is not available for room {room.name or room.id}.",
                    severity=Severity.MEDIUM,
                    category="Ventilation",
                    recommendation="Check VE infiltration-type air exchanges and the SIA 380/2 table 2 value.",
                    data=room,
                )

        return {
            "alerts": self.rule_engine.get_alerts_by_category("Ventilation"),
            "score": self._calculate_category_score("Ventilation"),
        }

    def _check_gains(self, rooms_data: List[RoomData]) -> Dict[str, Any]:
        """Check internal-gain evidence for lighting and equipment."""
        if not rooms_data:
            self.rule_engine.add_alert(
                rule="SIA3802_MODEL_NOT_CHECKABLE_GAINS",
                description="No usable VE room was analysed for internal-gain checks.",
                severity=Severity.CRITICAL,
                category="Gains",
                recommendation="Confirm the active VE model contains thermal rooms with occupancy, lighting and equipment templates.",
                data=None,
            )

        for room in rooms_data:
            if room.internal_gains.get("lighting") is None:
                self.rule_engine.add_alert(
                    rule="SIA3802_LIGHTING_POWER_MISSING",
                    description=f"Lighting power is not available for room {room.name or room.id}.",
                    severity=Severity.LOW,
                    category="Gains",
                    recommendation="Check lighting internal gains in the VE thermal template.",
                    data=room,
                )
            else:
                self.rule_engine.check_rules(["SIA3802_LIGHTING_POWER"], room)

            if room.internal_gains.get("equipment") is None:
                self.rule_engine.add_alert(
                    rule="SIA3802_EQUIPMENT_POWER_MISSING",
                    description=f"Equipment power is not available for room {room.name or room.id}.",
                    severity=Severity.LOW,
                    category="Gains",
                    recommendation="Check equipment internal gains in the VE thermal template.",
                    data=room,
                )
            else:
                self.rule_engine.check_rules(["SIA3802_EQUIPMENT_POWER"], room)

        return {
            "alerts": self.rule_engine.get_alerts_by_category("Gains"),
            "score": self._calculate_category_score("Gains"),
        }

    def _check_hvac(self, rooms_data: List[RoomData]) -> Dict[str, Any]:
        """Check HVAC system evidence."""
        if not rooms_data:
            self.rule_engine.add_alert(
                rule="SIA3802_MODEL_NOT_CHECKABLE_HVAC",
                description="No usable VE room was analysed for HVAC system checks.",
                severity=Severity.CRITICAL,
                category="HVAC",
                recommendation="Confirm the active VE model contains thermal rooms with Apache Systems data.",
                data=None,
            )

        for room in rooms_data:
            if not room.hvac_systems:
                self.rule_engine.add_alert(
                    rule="SIA3802_HVAC_SYSTEM_MISSING",
                    description=f"No HVAC system was extracted for room {room.name or room.id}.",
                    severity=Severity.LOW,
                    category="HVAC",
                    recommendation="Check Apache Systems/ApacheHVAC and document whether the room is intentionally unconditioned.",
                    data=room,
                )
            for hvac in room.hvac_systems:
                if hvac.get("efficiency") is not None:
                    self.rule_engine.check_rules(["SIA3802_HVAC_EFFICIENCY"], hvac)
                else:
                    self.rule_engine.add_alert(
                        rule="SIA3802_HVAC_EFFICIENCY_MISSING",
                        description=f"HVAC efficiency is not available for system {hvac.get('id', 'unknown')}.",
                        severity=Severity.LOW,
                        category="HVAC",
                        recommendation="Read efficiencies from Apache Systems/ApacheHVAC or document the retained assumption.",
                        data=hvac,
                    )

        return {
            "alerts": self.rule_engine.get_alerts_by_category("HVAC"),
            "score": self._calculate_category_score("HVAC"),
        }

    def _calculate_category_score(self, category: str) -> float:
        """Calculate a category score from 0 to 100."""
        alerts = self.rule_engine.get_alerts_by_category(category)
        if not alerts:
            return 100.0

        if any(self._is_blocking_not_checkable_alert(alert) for alert in alerts):
            return 0.0

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

    @staticmethod
    def _is_sia_comparable_g_value(opening: Any) -> bool:
        """Return true when the glazing g-value is proven as EN 410 g_perp."""
        source = str(getattr(opening, "solar_factor_source", "") or "").lower()
        return "bs_en_410" in source or getattr(opening, "g_value_bs_en_410", None) is not None


# Backward-compatible alias for older launchers or notebooks.
SIA3801Checker = SIA3802Checker
