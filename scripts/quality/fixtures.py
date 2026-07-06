"""Reusable in-memory fixtures for release-quality validation.

These fixtures let the project validate SIA 380/2 and SIA 4010 guardrails
without relying on client models, official SIA workbooks, or an active IESVE
session. They intentionally mirror the normalized objects produced by
``ModelAnalyzer`` so the production checkers are exercised directly.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Set

from swiss_sia.model_analyzer import OpeningData, RoomData, SurfaceData
from swiss_sia.rule_engine import Alert, Severity


class StaticModelAnalyzer:
    """In-memory analyzer exposing the subset required by the SIA checkers."""

    def __init__(self, rooms: Iterable[RoomData]) -> None:
        """Store deterministic rooms for checker validation."""
        self._rooms = list(rooms)

    def analyze_all_rooms(self) -> List[RoomData]:
        """Return the fixture rooms as the production analyzer would."""
        return list(self._rooms)

    def calculate_wwr(self, room_data: RoomData) -> float:
        """Calculate the window-to-wall ratio for one fixture room."""
        external_wall_area = sum(
            surface.area
            for surface in room_data.surfaces
            if surface.is_external and self._normalize_surface_type(surface.surface_type) == "wall"
        )
        window_area = sum(
            opening.area
            for opening in room_data.openings
            if opening.is_external and self._normalize_opening_type(opening.opening_type) == "window"
        )
        return window_area / external_wall_area if external_wall_area > 0 else 0.0

    @staticmethod
    def _normalize_surface_type(surface_type: Any) -> str:
        """Normalize surface labels in the same spirit as ``ModelAnalyzer``."""
        raw = str(surface_type or "").strip().lower()
        if "." in raw:
            raw = raw.split(".")[-1]
        raw = raw.replace(" ", "_").replace("-", "_")
        if raw.startswith(("ext_", "int_")):
            raw = raw[4:]
        if raw.startswith("ground_"):
            raw = raw[7:]
        return raw

    def _normalize_opening_type(self, opening_type: Any) -> str:
        """Normalize opening labels in the same spirit as ``ModelAnalyzer``."""
        normalized = self._normalize_surface_type(opening_type)
        if normalized in {"glazing", "window", "win"}:
            return "window"
        if normalized in {"door", "doors"}:
            return "door"
        return normalized


def build_reference_room() -> RoomData:
    """Return a room with clean SIA 380/2-ready envelope and opening data."""
    return RoomData(
        id="fixture-reference-room",
        name="Reference compliant room",
        volume=150.0,
        area=50.0,
        surfaces=[
            SurfaceData(
                id="fixture-reference-wall",
                name="External wall",
                area=50.0,
                net_area=42.0,
                u_value=0.18,
                orientation="South",
                tilt=90.0,
                is_external=True,
                surface_type="wall",
                construction_ids=["REF_EXT_WALL"],
                adjacency_types=["external_air"],
            ),
            SurfaceData(
                id="fixture-reference-roof",
                name="Flat roof",
                area=50.0,
                net_area=50.0,
                u_value=0.18,
                tilt=0.0,
                is_external=True,
                surface_type="roof",
                construction_ids=["REF_ROOF"],
                adjacency_types=["external_air"],
            ),
            SurfaceData(
                id="fixture-reference-floor",
                name="Ground floor",
                area=50.0,
                net_area=50.0,
                u_value=0.25,
                tilt=180.0,
                is_external=True,
                surface_type="floor",
                construction_ids=["REF_GROUND_FLOOR"],
                adjacency_types=["ground"],
            ),
        ],
        openings=[
            OpeningData(
                id="fixture-reference-window",
                name="EN 410 window",
                area=8.0,
                u_value=1.0,
                solar_factor=0.45,
                solar_factor_source="VECdbConstruction.get_g_values().bs_en_410",
                cdb_g_value=0.60,
                g_value_bs_en_410=0.45,
                visible_transmittance=0.72,
                frame_fraction=0.20,
                shading_type="external venetian blind",
                shading_control="solar irradiance control",
                shading_properties={"active": True},
                g_total=0.28,
                g_total_source="reviewer documented shading calculation",
                orientation="South",
                opening_type="window",
                is_external=True,
                construction_id="REF_WINDOW",
            )
        ],
        internal_gains={"lighting": 6.0, "people": 4.0, "equipment": 8.0},
        ventilation_rate=100.0,
        ventilation_m3_h_m2=2.0,
        infiltration_rate=0.10,
        infiltration_unit="m3/(h.m2)",
        infiltration_m3_h_m2=0.10,
        hvac_systems=[{"id": "REF_HVAC", "type": "heat_pump", "efficiency": 4.0}],
        room_conditions={"heating_setpoint": 21.0, "cooling_setpoint": 26.0},
    )


def build_problem_room() -> RoomData:
    """Return a room that should trigger the high-value SIA guardrails."""
    return RoomData(
        id="fixture-problem-room",
        name="Problematic audit room",
        volume=150.0,
        area=50.0,
        surfaces=[
            SurfaceData(
                id="fixture-problem-wall",
                name="Weak external wall",
                area=40.0,
                net_area=28.0,
                u_value=0.35,
                orientation="South",
                tilt=90.0,
                is_external=True,
                surface_type="wall",
                construction_ids=["BAD_EXT_WALL"],
                adjacency_types=["external_air"],
            ),
            SurfaceData(
                id="fixture-problem-roof",
                name="Weak flat roof",
                area=50.0,
                net_area=50.0,
                u_value=0.28,
                tilt=0.0,
                is_external=True,
                surface_type="roof",
                construction_ids=["BAD_ROOF"],
                adjacency_types=["external_air"],
            ),
        ],
        openings=[
            OpeningData(
                id="fixture-problem-window",
                name="Raw CDB window",
                area=18.0,
                u_value=1.45,
                solar_factor=0.75,
                solar_factor_source="",
                cdb_g_value=0.75,
                g_value_bs_en_410=None,
                visible_transmittance=0.55,
                frame_fraction=0.38,
                shading_type=None,
                shading_control=None,
                g_total=None,
                orientation="South",
                opening_type="window",
                is_external=True,
                construction_id="BAD_WINDOW",
            )
        ],
        internal_gains={"lighting": None, "people": 4.0, "equipment": None},
        ventilation_rate=100.0,
        ventilation_m3_h_m2=8.0,
        infiltration_rate=0.30,
        infiltration_unit="m3/(h.m2)",
        infiltration_m3_h_m2=0.30,
        hvac_systems=[{"id": "BAD_HVAC", "type": "generic", "efficiency": None}],
        room_conditions={},
    )


def build_reference_analyzer() -> StaticModelAnalyzer:
    """Return an analyzer containing one clean reference room."""
    return StaticModelAnalyzer([build_reference_room()])


def build_problem_analyzer() -> StaticModelAnalyzer:
    """Return an analyzer containing one intentionally problematic room."""
    return StaticModelAnalyzer([build_problem_room()])


def collect_alert_rules(results: Dict[str, Any]) -> Set[str]:
    """Return all alert rule names from checker results."""
    return {str(alert.rule) for alert in results.get("alerts", [])}


def collect_high_or_critical_alert_rules(results: Dict[str, Any]) -> Set[str]:
    """Return high and critical alert rule names from checker results."""
    return {
        str(alert.rule)
        for alert in results.get("alerts", [])
        if isinstance(alert, Alert) and alert.severity in {Severity.HIGH, Severity.CRITICAL}
    }
