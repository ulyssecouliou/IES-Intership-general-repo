"""PDF-based SIA 4010 prevalidation.

This module builds the strongest possible prevalidation from the published
SIA 380/2:2022 and SIA 4010:2023 PDFs, without claiming official SIA software
validation. Official validation still requires the paid SIA execution package
and sub-commission review referenced by SIA 4010 clauses 4.6.1-4.6.2.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence

from .config import (
    SIA3802_LIMIT_VALUES,
    SIA4010_PDF_PREVALIDATION_TESTS,
    SIA4010_PREVALIDATION_STATUSES,
    SIA4010_SOURCE_REFERENCES,
    SIA4010_TEST_ALIAS_LABELS,
    SIA4010_TEST_ALIAS_ORDER,
    SIA4010_TEST_ALIAS_TO_BASE_TEST,
    SIA4010_TEST_CLASS_COVERAGE,
    SIA4010_VALIDATION_CLASS_DETAILS,
    SIA4010_VALIDATION_CLASSES,
)
from .model_analyzer import has_active_solar_protection


BLOCKING_SIA3802_RULES_BY_TEST = {
    "test_1": {
        "SIA_VALUE_SURFACE_U_IMPLAUSIBLE",
        "SIA_VALUE_WINDOW_U_IMPLAUSIBLE",
        "SIA_VALUE_SURFACE_AREA_INVALID",
        "SIA_VALUE_OPENING_AREA_INVALID",
    },
    "test_2": {
        "SIA_VALUE_G_FRACTION_OUT_OF_RANGE",
        "SIA_VALUE_TAU_FRACTION_OUT_OF_RANGE",
        "SIA_VALUE_FRAME_FRACTION_OUT_OF_RANGE",
        "SIA_VALUE_G_TOTAL_FRACTION_OUT_OF_RANGE",
        "SIA_VALUE_G_TOTAL_GT_G_PERP",
    },
}


def build_sia4010_pdf_prevalidation(
    rooms_data: Sequence[Any],
    sia3802_results: Dict[str, Any],
    sia4010_results: Dict[str, Any],
    dynamic_results: Dict[str, Any],
) -> Dict[str, Any]:
    """Return SIA 4010 PDF-based prevalidation tests and classes."""
    stats = _build_stats(rooms_data, sia4010_results, dynamic_results)
    alerts_by_rule = _alerts_by_rule(sia3802_results.get("alerts", []) if isinstance(sia3802_results, dict) else [])

    tests = {
        test_name: _evaluate_test(test_name, stats, alerts_by_rule)
        for test_name in SIA4010_PDF_PREVALIDATION_TESTS
    }
    classes = _evaluate_classes(tests)
    summary = _build_summary(tests, classes)
    return {
        "status": summary["overall_status"],
        "summary": summary,
        "tests": tests,
        "classes": classes,
        "stats": stats,
        "official_validation_note": (
            "PDF-based prevalidation only. This is not official SIA 4010 software "
            "validation and does not replace the SIA execution package or the "
            "responsible SIA sub-commission review."
        ),
        "sources": [
            "SIA 4010:2023 FR, table 62 page PDF 46",
            "SIA 4010:2023 FR, table 63 page PDF 48",
            "SIA 4010:2023 FR, annex A table 64 pages PDF 50-51",
            "SIA 4010:2023 FR, tables 65-66 page PDF 52",
            "SIA 380/2:2022 FR, tables 2-4 and annex A",
        ],
    }


def _evaluate_test(
    test_name: str,
    stats: Dict[str, Any],
    alerts_by_rule: Dict[str, List[Any]],
) -> Dict[str, Any]:
    """Evaluate one SIA 4010 PDF-based prevalidation test."""
    definition = SIA4010_PDF_PREVALIDATION_TESTS[test_name]
    checks = _checks_for_test(test_name, stats)
    passed = [label for label, ok in checks if ok]
    missing = [label for label, ok in checks if not ok]
    blocking_rules = BLOCKING_SIA3802_RULES_BY_TEST.get(test_name, set())
    blocking_alerts = [
        alert for rule in blocking_rules for alert in alerts_by_rule.get(rule, [])
    ]
    risk_text = _risk_text(blocking_alerts)

    readiness_ratio = len(passed) / len(checks) if checks else 0.0
    if blocking_alerts:
        status = SIA4010_PREVALIDATION_STATUSES["fail"]
    elif readiness_ratio >= 1.0:
        status = SIA4010_PREVALIDATION_STATUSES["pass"]
    elif readiness_ratio > 0:
        status = SIA4010_PREVALIDATION_STATUSES["partial"]
    else:
        status = SIA4010_PREVALIDATION_STATUSES["missing"]

    return {
        "test": test_name,
        "title": definition["title"],
        "status": status,
        "readiness_ratio": readiness_ratio,
        "score": round(readiness_ratio * 100.0, 1),
        "passed_checks": passed,
        "missing_checks": missing,
        "blocking_risks": risk_text,
        "blocking_alert_count": len(blocking_alerts),
        "pdf_scope": definition["pdf_scope"],
        "sia3802_link": definition["sia3802_link"],
        "close_to_official_scope": definition["close_to_official_scope"],
        "official_gap": definition["official_gap"],
        "source": definition["source"],
        "next_action": _next_action_for_test(test_name, status, missing, blocking_alerts),
    }


def _checks_for_test(test_name: str, stats: Dict[str, Any]) -> List[Any]:
    """Return evidence checks required for one base SIA 4010 test."""
    if test_name == "test_1":
        return [
            ("rooms/zones extracted", stats["rooms"] > 0),
            ("external envelope surfaces extracted", stats["external_surfaces"] > 0),
            ("opaque external U-values extracted", stats["surface_u_values"] > 0),
            ("external windows/openings extracted", stats["external_windows"] > 0),
            ("external window U-values extracted", stats["window_u_values"] > 0),
            ("dynamic APS/Vista file readable", stats["dynamic_available"]),
        ]
    if test_name == "test_2":
        g_total_coverage = stats["g_total_values"] + stats["g_total_not_required_for_g_limit"]
        return [
            ("external glazing extracted", stats["external_windows"] > 0),
            ("EN 410/SIA comparable g_perp values extracted", stats["en410_g_values"] > 0),
            ("visible transmittance extracted", stats["visible_transmittance_values"] > 0),
            ("solar-protection type/category documented", stats["solar_protection_types"] > 0),
            ("solar-protection control/profile documented", stats["solar_protection_controls"] > 0),
            ("active g_total available or EN 410 g already at/below the table 2 reference input", g_total_coverage >= stats["external_windows"] > 0),
            ("infiltration evidence available for diagnostic transition", stats["rooms_with_infiltration_m3_h_m2"] > 0),
        ]
    if test_name == "test_3":
        return [
            ("lighting power/internal gain extracted", stats["rooms_with_lighting"] > 0),
            ("daylight control strategy documented", stats["lighting_control_evidence"] > 0),
            ("lighting energy results available", stats["lighting_energy_available"]),
            ("SIA 387/4 control variant mapped", stats["lighting_control_evidence"] > 0),
        ]
    if test_name == "test_4":
        return [
            ("HVAC system data extracted", stats["rooms_with_hvac"] > 0),
            ("ventilation/airflow data extracted", stats["rooms_with_ventilation"] > 0),
            ("dynamic heating/cooling demand available", stats["dynamic_demand_rows"] > 0),
            ("dynamic temperature indicators available", stats["dynamic_temperature_rows"] > 0),
            ("CO2 output or manual evidence available", stats["co2_available"]),
            ("coil/supply-air output evidence available", stats["coil_or_supply_air_available"]),
        ]
    if test_name == "test_5":
        return [
            ("HVAC/AHU system data extracted", stats["rooms_with_hvac"] > 0),
            ("multizone or AHU grouping evidence available", stats["multizone_hvac_evidence"] > 0),
            ("fan control identifier documented", stats["fan_control_evidence"] > 0),
            ("heat/moisture recovery type documented", stats["heat_recovery_evidence"] > 0),
            ("humidifier type/control documented", stats["humidifier_evidence"] > 0),
        ]
    if test_name == "test_6":
        return [
            ("ventilation system data extracted", stats["rooms_with_ventilation"] > 0),
            ("constant airflow or staged airflow documented", stats["staged_airflow_evidence"] > 0),
            ("heat recovery documented", stats["heat_recovery_evidence"] > 0),
            ("restaurant/kitchen overflow logic documented", stats["overflow_evidence"] > 0),
        ]
    if test_name == "test_7":
        return [
            (
                "dynamic heating and cooling demand available",
                stats["dynamic_heating_rows"] > 0 and stats["dynamic_cooling_rows"] > 0,
            ),
            ("final energy by system/carrier available", stats["final_energy_available"]),
            ("emission/distribution/storage/generation evidence available", stats["system_chain_evidence"] > 0),
            ("pump/fan/auxiliary energy available", stats["auxiliary_energy_available"]),
            ("heating/cooling generation data available", stats["generation_evidence"] > 0),
        ]
    return []


def _evaluate_classes(tests: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Evaluate validation-class readiness from the base-test results."""
    classes: Dict[str, Dict[str, Any]] = {}
    for class_name, tests_label in SIA4010_VALIDATION_CLASSES.items():
        aliases = _required_aliases_for_class(class_name)
        statuses = {
            alias: tests.get(SIA4010_TEST_ALIAS_TO_BASE_TEST.get(alias, alias), {}).get(
                "status",
                SIA4010_PREVALIDATION_STATUSES["missing"],
            )
            for alias in aliases
        }
        scores = [
            tests.get(SIA4010_TEST_ALIAS_TO_BASE_TEST.get(alias, alias), {}).get("score", 0.0)
            for alias in aliases
        ]
        status_values = set(statuses.values())
        if SIA4010_PREVALIDATION_STATUSES["fail"] in status_values:
            class_status = SIA4010_PREVALIDATION_STATUSES["fail"]
        elif SIA4010_PREVALIDATION_STATUSES["missing"] in status_values:
            class_status = SIA4010_PREVALIDATION_STATUSES["missing"]
        elif status_values == {SIA4010_PREVALIDATION_STATUSES["pass"]}:
            class_status = SIA4010_PREVALIDATION_STATUSES["pass"]
        else:
            class_status = SIA4010_PREVALIDATION_STATUSES["partial"]

        missing_or_failed = [
            SIA4010_TEST_ALIAS_LABELS.get(alias, alias)
            for alias, status in statuses.items()
            if status != SIA4010_PREVALIDATION_STATUSES["pass"]
        ]
        details = SIA4010_VALIDATION_CLASS_DETAILS.get(class_name, {})
        classes[class_name] = {
            "class": class_name,
            "status": class_status,
            "score": round(sum(float(score or 0.0) for score in scores) / len(scores), 1) if scores else 0.0,
            "required_tests_label": tests_label,
            "required_test_aliases": aliases,
            "required_test_statuses": statuses,
            "missing_or_failed_tests": missing_or_failed,
            "application": details.get("applications", ""),
            "solar_protection": details.get("solar_protection", ""),
            "source": SIA4010_SOURCE_REFERENCES["classes"],
            "official_validation_required": True,
        }
    return classes


def _build_summary(
    tests: Dict[str, Dict[str, Any]],
    classes: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Build aggregate prevalidation scores and status counters."""
    test_status_counts = _count_statuses(item["status"] for item in tests.values())
    class_status_counts = _count_statuses(item["status"] for item in classes.values())
    test_scores = [float(item.get("score", 0.0) or 0.0) for item in tests.values()]
    class_scores = [float(item.get("score", 0.0) or 0.0) for item in classes.values()]
    overall_status = _overall_status([item["status"] for item in tests.values()])
    return {
        "overall_status": overall_status,
        "test_count": len(tests),
        "class_count": len(classes),
        "average_test_score": round(sum(test_scores) / len(test_scores), 1) if test_scores else 0.0,
        "average_class_score": round(sum(class_scores) / len(class_scores), 1) if class_scores else 0.0,
        "test_status_counts": test_status_counts,
        "class_status_counts": class_status_counts,
        "official_validation_required": True,
    }


def _overall_status(statuses: Iterable[str]) -> str:
    """Return the conservative aggregate status for a set of statuses."""
    status_set = set(statuses)
    if SIA4010_PREVALIDATION_STATUSES["fail"] in status_set:
        return SIA4010_PREVALIDATION_STATUSES["fail"]
    if SIA4010_PREVALIDATION_STATUSES["missing"] in status_set:
        return SIA4010_PREVALIDATION_STATUSES["missing"]
    if status_set == {SIA4010_PREVALIDATION_STATUSES["pass"]}:
        return SIA4010_PREVALIDATION_STATUSES["pass"]
    return SIA4010_PREVALIDATION_STATUSES["partial"]


def _build_stats(
    rooms_data: Sequence[Any],
    sia4010_results: Dict[str, Any],
    dynamic_results: Dict[str, Any],
) -> Dict[str, Any]:
    """Build model, evidence, and dynamic-result counters for prevalidation."""
    rooms = list(rooms_data or [])
    surfaces = [surface for room in rooms for surface in getattr(room, "surfaces", [])]
    openings = [opening for room in rooms for opening in getattr(room, "openings", [])]
    external_surfaces = [surface for surface in surfaces if getattr(surface, "is_external", False)]
    external_openings = [opening for opening in openings if getattr(opening, "is_external", False)]
    external_windows = [
        opening for opening in external_openings
        if str(getattr(opening, "opening_type", "") or "").lower() in {"window", "glazing", "ext_glazing", "4"}
    ]
    dynamic_payload = dynamic_results or sia4010_results.get("dynamic_results", {}) or {}
    dynamic_room_rows = dynamic_payload.get("rooms", []) or []
    dynamic_demand_rows = [
        row for row in dynamic_room_rows
        if row.get("heating_kwh") is not None or row.get("cooling_kwh") is not None
    ]
    dynamic_heating_rows = [
        row for row in dynamic_room_rows
        if row.get("heating_kwh") is not None
    ]
    dynamic_cooling_rows = [
        row for row in dynamic_room_rows
        if row.get("cooling_kwh") is not None
    ]
    dynamic_temperature_rows = [
        row for row in dynamic_room_rows
        if row.get("occupied_hours_above_26") is not None or row.get("occupied_hours_above_27") is not None
    ]
    dynamic_lighting_rows = [
        row for row in dynamic_room_rows
        if row.get("lighting_kwh") is not None
    ]
    dynamic_fan_rows = [
        row for row in dynamic_room_rows
        if row.get("fan_kwh") is not None
    ]
    dynamic_pump_rows = [
        row for row in dynamic_room_rows
        if row.get("pump_kwh") is not None
    ]
    dynamic_auxiliary_rows = [
        row for row in dynamic_room_rows
        if row.get("auxiliary_kwh") is not None
    ]
    dynamic_coil_rows = [
        row for row in dynamic_room_rows
        if row.get("coil_heating_kwh") is not None or row.get("coil_cooling_kwh") is not None
    ]
    dynamic_co2_rows = [
        row for row in dynamic_room_rows
        if row.get("peak_co2_ppm") is not None or row.get("average_co2_ppm") is not None
    ]
    dynamic_humidity_rows = [
        row for row in dynamic_room_rows
        if row.get("peak_relative_humidity_percent") is not None
        or row.get("average_relative_humidity_percent") is not None
    ]
    g_total_not_required_for_g_limit = 0
    for opening in external_windows:
        try:
            g_value = float(getattr(opening, "solar_factor", None))
        except (TypeError, ValueError):
            continue
        if g_value <= SIA3802_LIMIT_VALUES["glazing_g_value"]:
            g_total_not_required_for_g_limit += 1

    rooms_with_lighting = [
        room for room in rooms
        if (getattr(room, "internal_gains", {}) or {}).get("lighting") is not None
    ]
    rooms_with_ventilation = [
        room for room in rooms
        if getattr(room, "ventilation_rate", None) is not None
    ]
    rooms_with_infiltration_m3_h_m2 = [
        room for room in rooms
        if getattr(room, "infiltration_m3_h_m2", None) is not None
    ]
    rooms_with_hvac = [room for room in rooms if getattr(room, "hvac_systems", None)]
    hvac_systems = [
        item
        for room in rooms
        for item in (getattr(room, "hvac_systems", []) or [])
        if isinstance(item, dict)
    ]
    energy = sia4010_results.get("energy", {}) or {}

    def has_system_value(*keys: str) -> bool:
        """Return true when an explicit non-empty HVAC field is available."""
        return any(
            system.get(key) not in (None, "", False, [], {})
            for system in hvac_systems
            for key in keys
        )

    def has_final_energy() -> bool:
        """Treat zero final energy as an explicit and therefore available result."""
        return any(system.get("final_energy") is not None for system in hvac_systems)

    return {
        "rooms": len(rooms),
        "external_surfaces": len(external_surfaces),
        "surface_u_values": sum(1 for surface in external_surfaces if getattr(surface, "u_value", None) is not None),
        "external_openings": len(external_openings),
        "external_windows": len(external_windows),
        "window_u_values": sum(1 for opening in external_windows if getattr(opening, "u_value", None) is not None),
        "window_g_values": sum(1 for opening in external_windows if getattr(opening, "solar_factor", None) is not None),
        "en410_g_values": sum(1 for opening in external_windows if getattr(opening, "g_value_bs_en_410", None) is not None),
        "raw_cdb_g_values": sum(1 for opening in external_windows if getattr(opening, "cdb_g_value", None) is not None),
        "visible_transmittance_values": sum(1 for opening in external_windows if getattr(opening, "visible_transmittance", None) is not None),
        "solar_protection_types": sum(
            1 for opening in external_windows if has_active_solar_protection(opening)
        ),
        "solar_protection_controls": sum(
            1
            for opening in external_windows
            if has_active_solar_protection(opening)
            and getattr(opening, "shading_control", None)
        ),
        "g_total_values": sum(1 for opening in external_windows if getattr(opening, "g_total", None) is not None),
        "g_total_not_required_for_g_limit": g_total_not_required_for_g_limit,
        "rooms_with_lighting": len(rooms_with_lighting),
        "rooms_with_ventilation": len(rooms_with_ventilation),
        "rooms_with_infiltration_m3_h_m2": len(rooms_with_infiltration_m3_h_m2),
        "rooms_with_hvac": len(rooms_with_hvac),
        "dynamic_available": str(dynamic_payload.get("status", "")).upper() == "AVAILABLE",
        "dynamic_demand_rows": len(dynamic_demand_rows),
        "dynamic_heating_rows": len(dynamic_heating_rows),
        "dynamic_cooling_rows": len(dynamic_cooling_rows),
        "dynamic_temperature_rows": len(dynamic_temperature_rows),
        "dynamic_lighting_rows": len(dynamic_lighting_rows),
        "dynamic_fan_rows": len(dynamic_fan_rows),
        "dynamic_pump_rows": len(dynamic_pump_rows),
        "dynamic_auxiliary_rows": len(dynamic_auxiliary_rows),
        "dynamic_auxiliary_energy_rows": max(len(dynamic_fan_rows), len(dynamic_pump_rows), len(dynamic_auxiliary_rows)),
        "dynamic_coil_rows": len(dynamic_coil_rows),
        "dynamic_co2_rows": len(dynamic_co2_rows),
        "dynamic_humidity_rows": len(dynamic_humidity_rows),
        "lighting_control_evidence": any(
            getattr(room, "daylight_dimming_profile", "")
            or getattr(room, "lighting_control_type", "")
            for room in rooms
        ),
        "lighting_energy_available": (
            len(dynamic_lighting_rows) > 0
            or energy.get("lighting_energy") is not None
        ),
        "co2_available": has_system_value("co2_control", "co2_sensor") or len(dynamic_co2_rows) > 0,
        "coil_or_supply_air_available": (
            len(dynamic_coil_rows) > 0
            or has_system_value("supply_air_temperature", "coil_heating", "coil_cooling")
        ),
        "multizone_hvac_evidence": any(
            "MULTIZONE" in "".join(character for character in str(system.get("system_type") or "").upper() if character.isalnum())
            for system in hvac_systems
        ),
        "fan_control_evidence": has_system_value("fan_control"),
        "heat_recovery_evidence": (
            has_system_value("heat_recovery_type", "heat_recovery_characteristic")
            or any(getattr(room, "heat_recovery_type", None) for room in rooms)
        ),
        "humidifier_evidence": has_system_value("humidifier_type", "humidifier_control") or len(dynamic_humidity_rows) > 0,
        "staged_airflow_evidence": (
            has_system_value("ventilation_stages")
            or any(getattr(room, "ventilation_control_level", None) is not None for room in rooms)
        ),
        "overflow_evidence": has_system_value("overflow_paths"),
        "final_energy_available": has_final_energy() or any(
            energy.get(key) is not None
            for key in ("primary_energy", "co2_emissions", "renewable_energy_share")
        ),
        "system_chain_evidence": has_system_value("storage_generation_data", "distribution_data", "emission_data"),
        "auxiliary_energy_available": (
            len(dynamic_fan_rows) > 0
            or len(dynamic_pump_rows) > 0
            or len(dynamic_auxiliary_rows) > 0
            or energy.get("fan_energy") is not None
            or energy.get("pump_energy") is not None
            or energy.get("auxiliary_energy") is not None
        ),
        "generation_evidence": has_system_value(
            "cooling_generator_class",
            "heating_generator_class",
            "storage_generation_data",
        ),
    }


def _alerts_by_rule(alerts: Sequence[Any]) -> Dict[str, List[Any]]:
    """Group rule-engine alerts by rule identifier."""
    grouped: Dict[str, List[Any]] = {}
    for alert in alerts or []:
        rule = str(getattr(alert, "rule", "") or "")
        if not rule:
            continue
        grouped.setdefault(rule, []).append(alert)
    return grouped


def _risk_text(alerts: Sequence[Any]) -> List[str]:
    """Return compact risk descriptions for blocking alerts."""
    risks = []
    for alert in alerts:
        description = str(getattr(alert, "description", "") or "").strip()
        rule = str(getattr(alert, "rule", "") or "").strip()
        risks.append(f"{rule}: {description}" if description else rule)
    return risks


def _next_action_for_test(
    test_name: str,
    status: str,
    missing: Sequence[str],
    blocking_alerts: Sequence[Any],
) -> str:
    """Return the next recommended action for one prevalidation test."""
    if status == SIA4010_PREVALIDATION_STATUSES["pass"]:
        return "Keep the extracted data and prepare the official SIA execution-package comparison if formal validation is required."
    if status == SIA4010_PREVALIDATION_STATUSES["fail"]:
        rules = sorted({str(getattr(alert, "rule", "") or "") for alert in blocking_alerts})
        return "Resolve the blocking SIA 380/2 issue(s) before claiming this precheck: " + ", ".join(rules)
    if missing:
        return "Add or document missing VE data: " + "; ".join(missing[:5])
    return f"Review {test_name} manually and document the assumptions before official validation."


def _required_aliases_for_class(class_name: str) -> List[str]:
    """Return SIA 4010 test aliases required by one validation class."""
    return [
        alias for alias in SIA4010_TEST_ALIAS_ORDER
        if class_name in SIA4010_TEST_CLASS_COVERAGE.get(alias, [])
    ]


def _contains_any(text: str, terms: Sequence[str]) -> int:
    """Return ``1`` when any term appears in the text, otherwise ``0``."""
    normalized = str(text or "").lower()
    return 1 if any(term.lower() in normalized for term in terms) else 0


def _count_statuses(statuses: Iterable[str]) -> Dict[str, int]:
    """Count status values for compact summaries."""
    counts: Dict[str, int] = {}
    for status in statuses:
        counts[status] = counts.get(status, 0) + 1
    return counts
