"""Input-value integrity checks for SIA 380/2 and SIA 4010 workflows.

These checks do not add new SIA limits. They protect the compliance engine from
using non-comparable or physically implausible VE values, which is essential
before applying SIA 380/2 limits or SIA 4010 test prevalidation.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .config import SIA3802_SOURCE_REFERENCES, SIA4010_SOURCE_REFERENCES
from .rule_engine import RuleEngine, Severity

VALUE_INTEGRITY_CATEGORY = "Value Integrity"


def add_value_integrity_alerts(
    rule_engine: RuleEngine, rooms_data: Iterable[Any]
) -> Dict[str, Any]:
    """Add value-integrity alerts and return an audit summary.

    The ranges below are plausibility and comparability guardrails. Numeric
    compliance still remains in the dedicated SIA 380/2 rules.
    """
    rooms = list(rooms_data or [])
    before = len(rule_engine.alerts)

    for room in rooms:
        _check_room_geometry(rule_engine, room)
        _check_room_air_and_gains(rule_engine, room)
        for surface in getattr(room, "surfaces", []) or []:
            _check_surface(rule_engine, surface)
        for opening in getattr(room, "openings", []) or []:
            _check_opening(rule_engine, opening)

    added_alerts = rule_engine.alerts[before:]
    return {
        "score": _score_from_alerts(added_alerts),
        "alerts": added_alerts,
        "alert_count": len(added_alerts),
        "checked_rooms": len(rooms),
        "source": (
            f"{SIA3802_SOURCE_REFERENCES['method']}; "
            f"{SIA4010_SOURCE_REFERENCES['tests']}; VEScripts documented metric API units"
        ),
    }


def _check_room_geometry(rule_engine: RuleEngine, room: Any) -> None:
    """Validate that room geometry values are present and physically plausible."""
    area = _as_float(getattr(room, "area", None))
    volume = _as_float(getattr(room, "volume", None))
    label = _label(room)
    if area is None or area <= 0:
        _add_alert(
            rule_engine,
            "SIA_VALUE_ROOM_AREA_INVALID",
            f"Room {label} has no positive floor area from VEBody.get_areas().",
            Severity.HIGH,
            "Confirm the active thermal room set and VEBody.get_areas()['int_floor_area'/'ext_floor_area'].",
            room,
        )
    elif area > 50000:
        _add_alert(
            rule_engine,
            "SIA_VALUE_ROOM_AREA_IMPLAUSIBLE",
            f"Room {label} area is {area:.3g} m2, which is unusually high for one thermal room.",
            Severity.MEDIUM,
            "Check whether VE returned an aggregated body or whether the room units are wrong.",
            room,
        )

    if volume is None or volume <= 0:
        _add_alert(
            rule_engine,
            "SIA_VALUE_ROOM_VOLUME_INVALID",
            f"Room {label} has no positive volume from VEBody.get_areas().",
            Severity.MEDIUM,
            "Confirm VE room geometry before relying on heating/cooling or ventilation checks.",
            room,
        )


def _check_room_air_and_gains(rule_engine: RuleEngine, room: Any) -> None:
    """Validate room airflow and internal-gain values before SIA checks."""
    label = _label(room)
    infiltration = _as_float(getattr(room, "infiltration_m3_h_m2", None))
    if infiltration is not None and (infiltration < 0 or infiltration > 20):
        _add_alert(
            rule_engine,
            "SIA_VALUE_INFILTRATION_IMPLAUSIBLE",
            f"Room {label} infiltration is {infiltration:.3g} m3/(h.m2), outside a plausible comparable range.",
            Severity.MEDIUM,
            "Check RoomAirExchange.get() units and conversion before applying the SIA 380/2 table 2 value.",
            room,
        )

    ventilation = _as_float(getattr(room, "ventilation_m3_h_m2", None))
    if ventilation is not None and (ventilation < 0 or ventilation > 100):
        _add_alert(
            rule_engine,
            "SIA_VALUE_VENTILATION_IMPLAUSIBLE",
            f"Room {label} ventilation is {ventilation:.3g} m3/(h.m2), outside a plausible design-airflow range.",
            Severity.MEDIUM,
            "Check RoomAirExchange.get() units and table 4 airflow-band mapping.",
            room,
        )

    for gain_name, value in (getattr(room, "internal_gains", {}) or {}).items():
        numeric = _as_float(value)
        if numeric is not None and numeric < 0:
            _add_alert(
                rule_engine,
                "SIA_VALUE_INTERNAL_GAIN_NEGATIVE",
                f"Room {label} has negative {gain_name} gain value {numeric:.3g}.",
                Severity.MEDIUM,
                "Check RoomInternalGain.get() data before using gains for SIA 380/2/SIA 4010 tests.",
                room,
            )


def _check_surface(rule_engine: RuleEngine, surface: Any) -> None:
    """Validate surface area and U-value inputs before envelope checks."""
    label = _label(surface)
    area = _as_float(getattr(surface, "area", None))
    net_area = _as_float(getattr(surface, "net_area", None))
    u_value = _as_float(getattr(surface, "u_value", None))

    if area is not None and area < 0:
        _add_alert(
            rule_engine,
            "SIA_VALUE_SURFACE_AREA_INVALID",
            f"Surface {label} has negative area {area:.3g} m2 from VESurface.get_areas().",
            Severity.HIGH,
            "Check VESurface.get_areas() output and surface classification.",
            surface,
        )
    if area is not None and net_area is not None and area > 0 and net_area > area * 1.05:
        _add_alert(
            rule_engine,
            "SIA_VALUE_SURFACE_NET_GT_GROSS",
            f"Surface {label} net area {net_area:.3g} m2 exceeds gross area {area:.3g} m2.",
            Severity.MEDIUM,
            "Check external_net/total_net extraction and opening subtraction before weighted U-value calculations.",
            surface,
        )
    if u_value is not None and (u_value <= 0 or u_value > 10):
        _add_alert(
            rule_engine,
            "SIA_VALUE_SURFACE_U_IMPLAUSIBLE",
            f"Surface {label} U-value is {u_value:.3g} W/(m2K), outside the accepted physical audit range.",
            Severity.HIGH,
            "Check VECdbConstruction.get_u_factor()/get_properties() and units before applying SIA 380/2 table 3.",
            surface,
        )


def _check_opening(rule_engine: RuleEngine, opening: Any) -> None:
    """Validate opening geometry, U-values, g-values, and shading values."""
    label = _label(opening)
    area = _as_float(getattr(opening, "area", None))
    u_value = _as_float(getattr(opening, "u_value", None))
    g_value = _as_float(getattr(opening, "solar_factor", None))
    tau_v = _as_float(getattr(opening, "visible_transmittance", None))
    frame_fraction = _as_float(getattr(opening, "frame_fraction", None))
    g_total = _as_float(getattr(opening, "g_total", None))
    bs_en_410 = _as_float(getattr(opening, "g_value_bs_en_410", None))
    cdb_g = _as_float(getattr(opening, "cdb_g_value", None))
    source = str(getattr(opening, "solar_factor_source", "") or "")

    if area is not None and area <= 0:
        _add_alert(
            rule_engine,
            "SIA_VALUE_OPENING_AREA_INVALID",
            f"Opening {label} has non-positive area {area:.3g} m2 from VEGeometry.get_properties().",
            Severity.MEDIUM,
            "Check VEGeometry.get_properties()['area'] and opening type before using glazing checks.",
            opening,
        )
    if u_value is not None and (u_value <= 0 or u_value > 10):
        _add_alert(
            rule_engine,
            "SIA_VALUE_WINDOW_U_IMPLAUSIBLE",
            f"Opening {label} U-value is {u_value:.3g} W/(m2K), outside the accepted physical audit range.",
            Severity.HIGH,
            "Check whether the value is window Uw, glass-centre Ug, or a CDB unit issue before applying table 2.",
            opening,
        )

    for rule, value, field_name in [
        ("SIA_VALUE_G_FRACTION_OUT_OF_RANGE", g_value, "EN 410 g_perp"),
        ("SIA_VALUE_TAU_FRACTION_OUT_OF_RANGE", tau_v, "visible transmittance tau_v"),
        ("SIA_VALUE_FRAME_FRACTION_OUT_OF_RANGE", frame_fraction, "frame fraction"),
        ("SIA_VALUE_G_TOTAL_FRACTION_OUT_OF_RANGE", g_total, "g_total with shading"),
    ]:
        if value is not None and not 0 <= value <= 1:
            _add_alert(
                rule_engine,
                rule,
                f"Opening {label} {field_name} is {value:.3g}; expected a fraction between 0 and 1.",
                Severity.HIGH,
                "Check whether VE/CDB returned a percentage and whether normalization was applied correctly.",
                opening,
            )

    if cdb_g is not None and bs_en_410 is None and not source:
        _add_alert(
            rule_engine,
            "SIA_VALUE_G_SOURCE_NOT_EN410",
            (
                f"Opening {label} exposes CDB g_value {cdb_g:.3g}, but no "
                "VECdbConstruction.get_g_values().bs_en_410 value was found."
            ),
            Severity.MEDIUM,
            "Treat this as audit evidence only. Provide EN 410 g_perp/manufacturer proof before a SIA 380/2 g-value PASS.",
            opening,
        )
    if g_total is not None and g_value is not None and g_total > g_value + 0.02:
        _add_alert(
            rule_engine,
            "SIA_VALUE_G_TOTAL_GT_G_PERP",
            f"Opening {label} g_total {g_total:.3g} is greater than EN 410 g_perp {g_value:.3g}.",
            Severity.MEDIUM,
            "Review the shading calculation/evidence because an effective shaded g-value is normally not expected to exceed bare glazing g_perp.",
            opening,
        )


def _add_alert(
    rule_engine: RuleEngine,
    rule: str,
    description: str,
    severity: Severity,
    recommendation: str,
    data: Any,
) -> None:
    """Add a normalized value-integrity alert to the shared rule engine."""
    rule_engine.add_alert(
        rule=rule,
        description=description,
        severity=severity,
        category=VALUE_INTEGRITY_CATEGORY,
        recommendation=recommendation,
        data=data,
    )


def _score_from_alerts(alerts: List[Any]) -> float:
    """Calculate a conservative integrity score from alert severities."""
    score = 100.0
    penalties = {
        Severity.CRITICAL: 25.0,
        Severity.HIGH: 15.0,
        Severity.MEDIUM: 8.0,
        Severity.LOW: 3.0,
    }
    for alert in alerts:
        score -= penalties.get(getattr(alert, "severity", Severity.LOW), 3.0)
    return max(0.0, min(100.0, score))


def _as_float(value: Any) -> Optional[float]:
    """Convert a value to float while preserving missing/invalid values as ``None``."""
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _label(item: Any) -> str:
    """Return the most readable identifier available for an audited object."""
    return str(getattr(item, "name", None) or getattr(item, "id", None) or "unknown")
