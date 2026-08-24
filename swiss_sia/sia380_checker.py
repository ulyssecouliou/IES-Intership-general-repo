"""SIA 380/2 checker for extracted IESVE model data.

This module evaluates the available VE data against the automated/readiness
checks implemented for SIA 380/2:2022. It deliberately keeps some topics as
evidence/readiness checks when the standard requires a reference calculation,
SIA 2024 mapping or official SIA 4010 validation evidence.
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .config import (
    PROJECT_ROOT,
    SIA3802_COOLING_EER_SEER_LIMITS,
    SIA3802_ELECTRICAL_POWER_LIMITS_W_M2,
    SIA3802_COOLING_EER_SEER_TARGETS,
    SIA3802_COOLING_NEED_SCREENING,
    SIA_COMPLIANCE_VALUE_PROVENANCE,
    SIA3802_DYNAMIC_COMFORT,
    SIA3802_HEATING_SCOP_LIMITS,
    SIA3802_HEATING_SCOP_TARGETS,
    SIA3802_LIMIT_VALUES,
    SIA3802_THRESHOLDS,
    SIA3802_U_VALUES,
    SIA3802_VENTILATION_CONTROL_TABLE,
    SIA3802_WATER_COOLED_POST_COOLING_EERPLUS,
    SIA4010_EVIDENCE_DIR,
)
from .evidence_manager import (
    accepted_solar_protection_windows,
    find_accepted_ahu_heat_recovery,
    find_accepted_cooling_generators,
    find_accepted_electrical_power,
    find_accepted_mapping,
    find_accepted_thermal_bridges,
    find_accepted_ventilation_control,
    scan_glazing_solar_protection,
    scan_sia2024_usage_mappings,
    scan_sia3802_ahu_heat_recovery,
    scan_sia3802_cooling_generators,
    scan_sia3802_electrical_power,
    scan_sia3802_thermal_bridges,
    scan_sia3802_ventilation_control,
    scan_sia3874_lighting_mappings,
)
from .model_analyzer import ModelAnalyzer, RoomData, has_active_solar_protection
from .rule_engine import Alert, Rule, RuleEngine, Severity
from .value_integrity import add_value_integrity_alerts


# Engineering epsilon used only to absorb floating-point/CDB serialization
# noise.  It is deliberately far smaller than a regulatory tolerance and does
# not turn meaningful reference-input deviations (for example 0.3033 vs 0.30)
# into a match.
REFERENCE_INPUT_NUMERICAL_EPSILON_W_M2K = 1.0e-4

# A category carrying any unverifiable ("cannot check") input is capped below the
# pass band so the number reads "incomplete", not "good". QA heuristic, not a
# regulatory value. Kept in sync with the verdict's indeterminate definition.
INCOMPLETE_EVIDENCE_SCORE_CEILING = 60.0
_INDETERMINATE_ALERT_MARKERS = (
    "MISSING",
    "NOT_CHECKABLE",
    "PLACEHOLDER",
    "UNAVAILABLE",
    "RULE_EXECUTION_ERROR",
)


_LOGGER = logging.getLogger(__name__)


class SIA3802Checker:
    """Check VE model data against the implemented SIA 380/2 rules."""

    def __init__(self, model_analyzer: ModelAnalyzer, rule_engine: RuleEngine):
        """Initialize the SIA 380/2 checker."""
        self.model_analyzer = model_analyzer
        self.rule_engine = rule_engine
        self._setup_rules()

    def _setup_rules(self):
        """Register SIA 380/2 rules in the shared rule engine."""
        reference_category = "Reference Project Diagnostics"
        reference_note = (
            "This is a deviation from a SIA 380/2 reference-project input, "
            "not a standalone component-compliance failure."
        )
        # SEER (cooling) and SCoP (heating) are seasonal indices defined per
        # SN EN 14825:2018 (now a verified reference:
        # refs/reference-data/sn-en-14825-2018.cooling-seer.json). SIA 380/2:2022
        # table 5 (page PDF 38) states the SEER minima "selon SN EN 14825", so a
        # DECLARED SEER (manufacturer ErP/Ecodesign figure, EN 14825 by
        # construction) is directly comparable to the SIA band -- handled by the
        # dedicated SIA3802_COOLING_SEER_MIN_DECLARED rule below, no caveat.
        # This VE-internal caveat remains ONLY for a seasonal index read from the
        # VE model itself, whose computation method is not confirmed to follow
        # EN 14825. The heating SCoP calculation clause is not yet verified, so
        # SCoP keeps the caveat too. The full-load EER rule compares the
        # directly-named table 5 EER and is exempt.
        sn_en_14825_caveat = (
            " [seasonal index read from the VE model - its EN 14825 computation "
            "is not confirmed; indicative, not a proven pass. Provide a declared "
            "SEER/SCoP (manufacturer, EN 14825) for a clean comparison. TO VERIFY]"
        )
        self.rule_engine.add_rule(Rule(
            name="SIA3802_U_VALUE_EXTERNAL_WALL",
            description=f"External wall U-value differs from the table 3 reference-project limit input of {SIA3802_U_VALUES['external_wall']} W/m2K. {reference_note}",
            check=lambda surface: surface.u_value <= SIA3802_U_VALUES["external_wall"] + REFERENCE_INPUT_NUMERICAL_EPSILON_W_M2K if surface.u_value is not None else False,
            severity=Severity.LOW,
            category=reference_category,
            recommendation="Retain the actual project value and complete the global project/reference calculation before drawing a compliance conclusion.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_U_VALUE_ROOF",
            description=f"Flat roof U-value differs from the table 3 reference-project limit input of {SIA3802_U_VALUES['roof']} W/m2K. {reference_note}",
            check=lambda surface: surface.u_value <= SIA3802_U_VALUES["roof"] + REFERENCE_INPUT_NUMERICAL_EPSILON_W_M2K if surface.u_value is not None else False,
            severity=Severity.LOW,
            category=reference_category,
            recommendation="Retain the actual project value and complete the global project/reference calculation before drawing a compliance conclusion.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_U_VALUE_FLOOR",
            description=f"Floor U-value differs from the table 3 reference-project limit input of {SIA3802_U_VALUES['floor']} W/m2K. {reference_note}",
            check=lambda surface: surface.u_value <= SIA3802_U_VALUES["floor"] + REFERENCE_INPUT_NUMERICAL_EPSILON_W_M2K if surface.u_value is not None else False,
            severity=Severity.LOW,
            category=reference_category,
            recommendation="Confirm the boundary classification and complete the global project/reference calculation.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_U_VALUE_WINDOW",
            description=f"Window Uw differs from the table 2 reference-project limit input of {SIA3802_U_VALUES['window']} W/m2K. {reference_note}",
            check=lambda opening: opening.u_value <= SIA3802_U_VALUES["window"] + REFERENCE_INPUT_NUMERICAL_EPSILON_W_M2K if opening.u_value is not None else False,
            severity=Severity.LOW,
            category=reference_category,
            recommendation="Confirm that the extracted value is Uw and complete the global project/reference calculation.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_U_VALUE_DOOR",
            description=(
                "[TO VERIFY] No door-specific U-value is published in SIA 380/2:2022 "
                "7.2.5.3, table 2, PDF page 32; the former window-U-value alias is unsupported."
            ),
            check=lambda _opening: False,
            severity=Severity.MEDIUM,
            category="Openings",
            recommendation=(
                "Provide a reviewer-approved source and applicability rule for the door U-value; "
                "do not substitute the table-2 window Uw."
            ),
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_SOLAR_FACTOR",
            description=f"Glazing g_perp differs from the table 2 reference-project limit input of {SIA3802_THRESHOLDS['solar_factor_max']}. {reference_note}",
            check=lambda opening: opening.solar_factor <= SIA3802_THRESHOLDS["solar_factor_max"] if opening.solar_factor is not None else False,
            severity=Severity.LOW,
            category=reference_category,
            recommendation="Keep EN 410 provenance and evaluate the value through the global project/reference calculation.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_VISIBLE_TRANSMITTANCE",
            description=f"Glazing visible transmittance tau_v >= {SIA3802_THRESHOLDS['light_transmittance_min']} (SIA 380/2:2022, table 2, reference value).",
            check=lambda opening: opening.visible_transmittance >= SIA3802_THRESHOLDS["light_transmittance_min"] if opening.visible_transmittance is not None else False,
            severity=Severity.LOW,
            category=reference_category,
            recommendation="Retain the extracted tau_v in the global project/reference calculation, or use tau_v >= 0.70 when reproducing the table 2 reference input.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_FRAME_FRACTION",
            description=f"Window frame fraction ff <= {SIA3802_THRESHOLDS['window_frame_fraction']} (SIA 380/2:2022, table 2, reference value).",
            check=lambda opening: opening.frame_fraction <= SIA3802_THRESHOLDS["window_frame_fraction"] if opening.frame_fraction is not None else False,
            severity=Severity.LOW,
            category=reference_category,
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
            severity=Severity.LOW,
            category=reference_category,
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
            name="SIA3802_VENTILATION_CONTROL_CLASS",
            description="Extracted ventilation control meets the SIA 380/2 table 4 reference-project limit for its installation type and airflow band.",
            check=lambda room: self._ventilation_control_meets_limit(room),
            severity=Severity.LOW,
            category=reference_category,
            recommendation="Update or document fan staging, schedule/demand sensors and zone/room control scope for the applicable table 4 cell.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_COOLING_EER_MIN",
            description=f"Cooling EER meets the capacity-banded SIA 380/2 table 5 or 6 limit. {reference_note}",
            check=lambda hvac: self._hvac_metric_meets_limit(hvac, "eer"),
            severity=Severity.LOW,
            category=reference_category,
            recommendation="Check generator classification, rated capacity and nominal EER against the applicable reference-project row.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_COOLING_SEER_MIN",
            description=f"Cooling SEER meets the capacity-banded SIA 380/2 table 5 or 6 limit. {reference_note}{sn_en_14825_caveat}",
            check=lambda hvac: self._hvac_metric_meets_limit(hvac, "seer"),
            severity=Severity.LOW,
            category=reference_category,
            recommendation=f"Check generator classification, rated capacity and seasonal SEER against the applicable reference-project row.{sn_en_14825_caveat}",
        ))

        # Declared SEER (manufacturer ErP/Ecodesign figure) is EN 14825 by
        # construction, and SIA 380/2 table 5 defines its minima "selon SN EN
        # 14825" -- so this comparison is clean, no seasonal-equivalence caveat.
        self.rule_engine.add_rule(Rule(
            name="SIA3802_COOLING_SEER_MIN_DECLARED",
            description=(
                "Declared cooling SEER (manufacturer, SN EN 14825:2018) meets the "
                "capacity-banded SIA 380/2 table 5 (air-cooled) or table 6 "
                f"(water-cooled) SEER limit. {reference_note}"
            ),
            check=lambda hvac: self._hvac_metric_meets_limit(hvac, "seer"),
            severity=Severity.LOW,
            category=reference_category,
            recommendation="Confirm the declared SEER, generator class and rated capacity against the SIA 380/2 table 5 SEER band.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_HEATING_SCOP_MIN",
            description=f"Heat-pump SCOP meets the capacity-banded SIA 380/2 table 8 or 9 limit. {reference_note}{sn_en_14825_caveat}",
            check=lambda hvac: self._hvac_metric_meets_limit(hvac, "scop"),
            severity=Severity.LOW,
            category=reference_category,
            recommendation=f"Check heat-source classification, rated capacity and SCoP against the applicable reference-project row.{sn_en_14825_caveat}",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA3802_SUMMER_COMFORT_DYNAMIC",
            description="Annual occupied-hour temperatures exceed the applicable SIA 180 upper-hour allowance or undercut the lower limit curve.",
            check=lambda data: (
                data.get("upper_hours") is not None
                and data.get("lower_hours") is not None
                and data.get("upper_limit_hours") is not None
                and data["upper_hours"] <= data["upper_limit_hours"]
                and data["lower_hours"] <= 0.0
            ),
            severity=Severity.HIGH,
            category="Dynamic Method",
            recommendation="Review the critical rooms, shading, ventilation and system operation, then rerun a full-year SIA-compatible dynamic simulation.",
        ))

    def check_all(
        self,
        rooms_data: Optional[List[RoomData]] = None,
        dynamic_results: Optional[Dict[str, Any]] = None,
        external_mappings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run all implemented SIA 380/2 checks and return category results."""
        rooms_data = rooms_data if rooms_data is not None else self.model_analyzer.analyze_all_rooms()
        self.rule_engine.clear_alerts()

        project = getattr(
            getattr(self.model_analyzer, "data_extractor", None),
            "project",
            None,
        )
        project_path = str(getattr(project, "path", "") or "")
        project_label = Path(project_path).name if project_path else None

        if external_mappings is None:
            external_mappings = {
                "sia2024_usage": scan_sia2024_usage_mappings(
                    PROJECT_ROOT,
                    SIA4010_EVIDENCE_DIR,
                    project_label,
                ),
                "sia3874_lighting": scan_sia3874_lighting_mappings(
                    PROJECT_ROOT,
                    SIA4010_EVIDENCE_DIR,
                    project_label,
                ),
            }

        # Thermal bridges (psi/chi): VE 2025.2 exposes them per surface
        # (VESurface.get_thermal_bridges_non_repeating/_random), so the model's
        # thermal-bridge conductance H_tb (W/K) is read directly. A reviewer
        # schedule stays as a fallback for older VE versions / unset data.
        thermal_bridge_scan = scan_sia3802_thermal_bridges(
            PROJECT_ROOT, SIA4010_EVIDENCE_DIR, project_label
        )
        thermal_bridge_record = find_accepted_thermal_bridges(
            thermal_bridge_scan, project_label or ""
        )
        ve_thermal_bridges = self._read_ve_thermal_bridges()

        # Cooling-generator EER/SEER can be supplied as reviewed manufacturer
        # evidence when the VE generator is autosized (capacity greyed out), so
        # the SIA 380/2 Tables 5-7 power band cannot be resolved from the model.
        cooling_generator_scan = scan_sia3802_cooling_generators(
            PROJECT_ROOT, SIA4010_EVIDENCE_DIR, project_label
        )
        cooling_generator_record = find_accepted_cooling_generators(
            cooling_generator_scan, project_label or ""
        )
        # Make the accepted reviewer cooling-generator record available to the
        # HVAC check, so a declared SEER (EN 14825) can be compared to the SIA
        # band even when the VE generator is autosized (capacity greyed out).
        self._reviewer_cooling_generator = cooling_generator_record

        # AHU / heat-recovery (Table 4) and ventilation-control (Table 4) verified
        # characteristics are supplied as reviewed evidence: VE exposes only the
        # identifiers, not the leakage class, seasonal efficiency or control band.
        ahu_scan = scan_sia3802_ahu_heat_recovery(
            PROJECT_ROOT, SIA4010_EVIDENCE_DIR, project_label
        )
        ahu_record = find_accepted_ahu_heat_recovery(ahu_scan, project_label or "")
        ventilation_control_scan = scan_sia3802_ventilation_control(
            PROJECT_ROOT, SIA4010_EVIDENCE_DIR, project_label
        )
        ventilation_control_record = find_accepted_ventilation_control(
            ventilation_control_scan, project_label or ""
        )
        self._reviewer_ventilation_controls = list(
            ventilation_control_scan.get("accepted_records", []) or []
        )
        applied_ventilation_evidence = self._apply_reviewed_ventilation_controls(
            rooms_data
        )

        # Solar protection (Table 10) documented outside VE: reviewed rows carry
        # the shading type + g_total with shading. The reviewed window count is
        # reconciled against the external windows VE sees, never a silent pass.
        solar_protection_scan = scan_glazing_solar_protection(
            PROJECT_ROOT, SIA4010_EVIDENCE_DIR, project_label
        )
        solar_protection_windows = accepted_solar_protection_windows(
            solar_protection_scan, project_label or ""
        )

        # SIA 380/2:2022 §7.2.4 required electrical power (W/m2): a design sizing
        # figure VE does not expose, supplied as reviewed evidence.
        electrical_power_scan = scan_sia3802_electrical_power(
            PROJECT_ROOT, SIA4010_EVIDENCE_DIR, project_label
        )
        electrical_power_record = find_accepted_electrical_power(
            electrical_power_scan, project_label or ""
        )
        has_fluid_installation = any(
            getattr(room, "hvac_systems", None)
            or getattr(room, "mechanical_ventilation_present", None) is True
            or getattr(room, "ventilation_rate", None) is not None
            for room in (rooms_data or [])
        )
        electrical_power = self._evaluate_electrical_power(
            electrical_power_record, has_fluid_installation
        )
        electrical_power["status"] = electrical_power_scan.get("status")

        envelope = self._run_category(
            "Envelope", self._check_envelope, rooms_data
        )
        openings = self._run_category(
            "Openings", self._check_openings, rooms_data
        )
        ventilation = self._run_category(
            "Ventilation", self._check_ventilation, rooms_data
        )
        gains = self._run_category(
            "Gains", self._check_gains, rooms_data, external_mappings
        )
        setpoints = self._run_category(
            "Setpoints", self._check_setpoints, rooms_data
        )
        hvac = self._run_category("HVAC", self._check_hvac, rooms_data)
        dynamic = self._run_category(
            "Dynamic Method", self._check_dynamic_method, dynamic_results or {}
        )
        value_integrity = add_value_integrity_alerts(self.rule_engine, rooms_data)
        global_reference_comparison = self._check_global_reference_comparison(
            dynamic_results or {}
        )

        results = {
            "envelope": envelope,
            "openings": openings,
            "ventilation": ventilation,
            "gains": gains,
            "setpoints": setpoints,
            "hvac": hvac,
            "dynamic": dynamic,
            "value_integrity": value_integrity,
            "global_reference_comparison": global_reference_comparison,
            "reference_project_diagnostics": {
                "status": "DIAGNOSTIC_ONLY",
                "alerts": self.rule_engine.get_alerts_by_category(
                    "Reference Project Diagnostics"
                ),
                "note": (
                    "Tables 2 to 9 define inputs for reference-project comparisons. "
                    "Their component-level deviations are not standalone compliance failures."
                ),
            },
            "external_mappings": external_mappings,
            "thermal_bridges": self._build_thermal_bridge_result(
                thermal_bridge_scan, thermal_bridge_record, ve_thermal_bridges
            ),
            "cooling_generators": {
                "status": cooling_generator_scan.get("status"),
                "accepted": bool(cooling_generator_record),
                "record": cooling_generator_record,
            },
            "ahu_heat_recovery": {
                "status": ahu_scan.get("status"),
                "accepted": bool(ahu_record),
                "record": ahu_record,
            },
            "ventilation_control_evidence": {
                "status": ventilation_control_scan.get("status"),
                "accepted": bool(ventilation_control_record),
                "record": ventilation_control_record,
                "records": list(
                    ventilation_control_scan.get("accepted_records", []) or []
                ),
                "applied_room_count": applied_ventilation_evidence,
            },
            "solar_protection_evidence": {
                "status": solar_protection_scan.get("status"),
                "accepted_window_count": solar_protection_windows,
                "records": solar_protection_scan.get("accepted_records", []),
            },
            "electrical_power": electrical_power,
            "rule_evaluations": dict(self.rule_engine.evaluated_counts),
            "alerts": list(self.rule_engine.alerts),
        }
        return results

    def _run_category(
        self,
        category: str,
        check: Callable[..., Dict[str, Any]],
        *args: Any,
    ) -> Dict[str, Any]:
        """Run one category check, failing that category closed on any error.

        The seven category checks read VE-extracted data whose shape can vary:
        the extractor degrades to empty or ``None`` rather than raising, so a
        real client model can present a room, surface or system this checker did
        not anticipate.  Without this guard, one unexpected value in a single
        category would raise and take down the entire analysis, leaving the user
        with no report at all.

        On error the category is recorded as a blocking
        ``RULE_EXECUTION_ERROR`` alert -- which the category score already treats
        as a hard zero and the reported verdict treats as ``NOT_DETERMINED`` --
        so the run continues, every other category still produces its diagnostic,
        and the failure can never read as a pass.  The exception is logged with
        its stage and category, never with model data.

        Args:
            category: Human-readable SIA category, e.g. ``"Envelope"``.
            check: The bound category-check method.
            *args: Positional arguments forwarded to ``check``.

        Returns:
            dict: The check result, or a fail-closed ``RULE_EXECUTION_ERROR``
            record when the check raised.
        """

        try:
            return check(*args)
        except Exception as exc:  # noqa: BLE001 -- fail closed, never crash the run
            rule = "SIA3802_{}_RULE_EXECUTION_ERROR".format(
                category.upper().replace(" ", "_")
            )
            _LOGGER.exception(
                "SIA 380/2 category check failed; stage=check_all "
                "category=%s outcome=NOT_CHECKABLE",
                category,
            )
            self.rule_engine.add_alert(
                rule=rule,
                description=(
                    "The {} check could not run to completion on this model, "
                    "so this category cannot be evaluated. This is a "
                    "fail-closed result, not a pass.".format(category)
                ),
                severity=Severity.CRITICAL,
                category=category,
                recommendation=(
                    "Report the model to the tool maintainer with the logged "
                    "error; the extracted data shape was not anticipated by "
                    "the {} check.".format(category)
                ),
                data=None,
            )
            return {
                "status": "RULE_EXECUTION_ERROR",
                "error_type": type(exc).__name__,
            }

    def _check_global_reference_comparison(
        self,
        dynamic_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Require an explicit reviewed project/reference result for compliance."""
        # This method runs outside the per-category fail-closed guard, so a
        # degenerate dynamic_results payload (a non-dict, or a non-dict
        # global_reference_comparison value) must not raise and take down the
        # whole analysis. Coerce both to empty dicts so the checks below fall
        # through to the explicit NOT_CHECKABLE result rather than an exception.
        if not isinstance(dynamic_results, dict):
            dynamic_results = {}
        comparison = dynamic_results.get("global_reference_comparison", {}) or {}
        if not isinstance(comparison, dict):
            comparison = {}
        accepted = bool(comparison.get("accepted"))
        project_value = self._float_or_none(
            comparison.get("project_value_numeric", comparison.get("project_value"))
        )
        reference_value = self._float_or_none(
            comparison.get("reference_value_numeric", comparison.get("reference_value"))
        )
        source = str(
            comparison.get("source_document")
            or comparison.get("source_reference")
            or ""
        ).strip()
        if accepted and project_value is not None and reference_value is not None and source:
            # SIA 380/2:2022 7.2.5.2 -- the global performance requirement is met
            # only when the project value is LOWER THAN OR EQUAL TO the reference
            # value. The reviewer's `accepted` flag must not override the figures:
            # if the two numbers contradict that sense (inverted columns, wrong
            # unit, or a genuine exceedance), the report must never read COMPLIANT.
            # `float_eps` is a pure floating-point guard, NOT a normative margin:
            # it only keeps an exact project == reference equality from being
            # rejected by rounding noise.
            float_eps = 1e-9
            within_reference = (
                project_value
                <= reference_value + abs(reference_value) * float_eps
            )
            if within_reference:
                return {
                    "status": "REVIEWED_RESULT_AVAILABLE",
                    "project_value": project_value,
                    "reference_value": reference_value,
                    "source": source,
                }
            self.rule_engine.add_alert(
                rule="SIA3802_GLOBAL_REFERENCE_DISCREPANCY",
                description=(
                    "The reviewed global comparison is marked accepted, but the "
                    "project value ({0:.4g}) exceeds the reference value "
                    "({1:.4g}). Per SIA 380/2:2022 7.2.5.2 the project value must "
                    "be lower than or equal to the reference; reviewer acceptance "
                    "cannot override the reported figures.".format(
                        project_value, reference_value
                    )
                ),
                severity=Severity.CRITICAL,
                category="Global Reference Comparison",
                recommendation=(
                    "Reconcile the acceptance with the figures: correct the "
                    "project/reference values, their column order or units, or "
                    "withdraw acceptance. 'accepted' must attest that the project "
                    "meets the reference, not merely that values were entered."
                ),
                data=None,
            )
            return {
                "status": "REVIEWED_RESULT_CONTRADICTS_ACCEPTANCE",
                "project_value": project_value,
                "reference_value": reference_value,
                "source": source,
            }

        self.rule_engine.add_alert(
            rule="SIA3802_GLOBAL_REFERENCE_COMPARISON_NOT_CHECKABLE",
            description=(
                "No reviewed global SIA 380/2 project/reference comparison was "
                "provided; component diagnostics cannot establish compliance."
            ),
            severity=Severity.CRITICAL,
            category="Global Reference Comparison",
            recommendation=(
                "Provide the auditable project and reference calculation results, "
                "their common metric/unit, calculation source and reviewer acceptance."
            ),
            data=None,
        )
        return {
            "status": "NOT_CHECKABLE",
            "project_value": project_value,
            "reference_value": reference_value,
            "source": source,
        }

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
                    active_solar_protection = has_active_solar_protection(opening)
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

                    if active_solar_protection and not getattr(opening, "shading_type", None):
                        self.rule_engine.add_alert(
                            rule="SIA3802_SOLAR_PROTECTION_TYPE_MISSING",
                            description=f"Solar-protection type is not available for external window {opening.name or opening.id}.",
                            severity=Severity.LOW,
                            category="Openings",
                            recommendation="Document the solar-protection type according to SIA 380/2 table 10 and the applicable SIA 4010 test 2/2A variant.",
                            data=opening,
                        )

                    if active_solar_protection and not getattr(opening, "shading_control", None):
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
                        and active_solar_protection
                        and solar_factor is not None
                        and solar_factor > SIA3802_THRESHOLDS["solar_factor_max"]
                    ):
                        self.rule_engine.add_alert(
                            rule="SIA3802_G_TOTAL_WITH_SHADING_MISSING",
                            description=f"Active glazing-plus-shading g_total is not available for external window {opening.name or opening.id}, while g_perp is above the table 2 reference input.",
                            severity=Severity.LOW,
                            category="Openings",
                            recommendation="Provide active g_total for the modelled protection, retain the actual value in the global comparison, or use EN 410 g_perp <= 0.50 when reproducing the table 2 reference-input model.",
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
                else:
                    self.rule_engine.add_alert(
                        rule="SIA3802_OPENING_TYPE_NOT_CHECKABLE",
                        description=(
                            f"External opening {opening.name or opening.id} has no source-traced "
                            "VESurface_type classification. "
                            f"{getattr(opening, 'opening_type_note', '') or '[TO VERIFY] opening type'}"
                        ),
                        severity=Severity.CRITICAL,
                        category="Openings",
                        recommendation=(
                            "Expose a documented symbolic VESurface_type enum member; numeric "
                            "ordinals 4/5/6/11 are not published in the checked IESVE sources."
                        ),
                        data=opening,
                    )
            self.rule_engine.check_rules(["SIA3802_WWR"], room)

        return {
            "alerts": self.rule_engine.get_alerts_by_category("Openings"),
            "score": self._calculate_category_score("Openings"),
        }

    def _apply_reviewed_ventilation_controls(
        self,
        rooms_data: List[RoomData],
    ) -> int:
        """Apply accepted Table-4 records only when their scope and band reconcile."""
        records = list(getattr(self, "_reviewer_ventilation_controls", []) or [])
        if not records:
            return 0
        system_ids = {
            str(system.get("id") or "").strip().lower()
            for room in rooms_data
            for system in (getattr(room, "hvac_systems", []) or [])
            if isinstance(system, dict) and system.get("id")
        }
        applied = 0
        for room in rooms_data:
            room_system_ids = {
                str(system.get("id") or "").strip().lower()
                for system in (getattr(room, "hvac_systems", []) or [])
                if isinstance(system, dict) and system.get("id")
            }
            room_scope_keys = {
                str(getattr(room, "id", "") or "").strip().lower(),
                str(getattr(room, "name", "") or "").strip().lower(),
                str((getattr(room, "hvac_zone", {}) or {}).get("id") or "").strip().lower(),
                str((getattr(room, "hvac_zone", {}) or {}).get("name") or "").strip().lower(),
            }
            room_scope_keys.discard("")
            matches = []
            for record in records:
                record_system = str(record.get("system_id") or "").strip().lower()
                record_scope = str(record.get("room_or_zone") or "").strip().lower()
                if record_scope:
                    if record_scope in room_scope_keys and (
                        not record_system or record_system in room_system_ids
                    ):
                        matches.append(record)
                elif record_system and record_system in room_system_ids:
                    matches.append(record)
                elif (
                    not record_system
                    and not record_scope
                    and len(records) == 1
                    and len(system_ids) <= 1
                ):
                    matches.append(record)

            if len(matches) != 1:
                if len(matches) > 1:
                    self.rule_engine.add_alert(
                        rule="SIA3802_VENTILATION_EVIDENCE_SCOPE_AMBIGUOUS",
                        description=(
                            f"Room {room.name or room.id} matches more than one accepted "
                            "ventilation-control record."
                        ),
                        severity=Severity.MEDIUM,
                        category="Ventilation",
                        recommendation=(
                            "Use unique system_id or room_or_zone values in the ventilation evidence CSV."
                        ),
                        data=room,
                    )
                continue

            record = matches[0]
            ve_airflow = self._float_or_none(
                getattr(room, "ventilation_m3_h_m2", None)
            )
            evidence_airflow = self._float_or_none(
                record.get("specific_airflow_m3_h_m2_numeric")
            )
            record_band = str(record.get("airflow_band_normalized") or "")
            ve_band = self._ventilation_band(ve_airflow) if ve_airflow is not None else ""
            if ve_band and record_band and ve_band != record_band:
                self.rule_engine.add_alert(
                    rule="SIA3802_VENTILATION_EVIDENCE_AIRFLOW_MISMATCH",
                    description=(
                        f"Room {room.name or room.id} is in VE airflow band {ve_band} "
                        f"({ve_airflow:.3g} m3/(h.m2)), while the accepted ventilation "
                        f"record states band {record_band}."
                    ),
                    severity=Severity.MEDIUM,
                    category="Ventilation",
                    recommendation=(
                        "Reconcile the VE design airflow and reviewed Table-4 record before validation."
                    ),
                    data=room,
                )
                continue
            if ve_airflow is None:
                if evidence_airflow is None:
                    continue
                room.ventilation_m3_h_m2 = evidence_airflow
                room.ventilation_rate = evidence_airflow
                room.ventilation_unit = "m3/(h.m2)"
                room.ventilation_normalization_method = "reviewer-accepted design airflow"
                room.ventilation_source = str(
                    record.get("source_document")
                    or record.get("source_reference")
                    or "reviewed ventilation evidence"
                )
                room.mechanical_ventilation_present = True

            room.ventilation_installation_type = str(
                record.get("system_type_normalized") or ""
            )
            room.ventilation_installation_type_status = "REVIEWER_ACCEPTED"
            room.ventilation_installation_type_placeholder = ""
            room.ventilation_control = str(record.get("control_class") or "")
            room.ventilation_control_level = int(record["control_level_numeric"])
            room.ventilation_control_level_status = "REVIEWER_ACCEPTED"
            room.ventilation_control_level_placeholder = ""
            room.ventilation_control_evidence_note = (
                "Reviewer-accepted SIA 380/2 Table 4 evidence: "
                f"{record.get('file', record.get('source_document', ''))}"
            )
            applied += 1
        return applied

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
            if getattr(room, "air_exchange_classification_status", "NOT_CHECKABLE") != "OK":
                self.rule_engine.add_alert(
                    rule="SIA3802_AIR_EXCHANGE_TYPE_NOT_CHECKABLE",
                    description=(
                        f"Room {room.name or room.id} contains no completely source-traced "
                        "RoomAirExchange.type_val classification. "
                        f"{getattr(room, 'air_exchange_classification_note', '')}"
                    ),
                    severity=Severity.MEDIUM,
                    category="Ventilation",
                    recommendation=(
                        "Read type_val using the documented VEScript 6.1.15.1 contract "
                        "(0 infiltration, 1 natural ventilation, 2 auxiliary ventilation)."
                    ),
                    data=room,
                )
            mechanical_present = getattr(room, "mechanical_ventilation_present", None)
            if mechanical_present is False:
                # Source-traced air exchanges contain no auxiliary ventilation;
                # Table 4 mechanical-control classification is not applicable.
                pass
            elif room.ventilation_rate is not None:
                self.rule_engine.check_rules(["SIA3802_VENTILATION_RATE"], room)
                ventilation_m3_h_m2 = getattr(room, "ventilation_m3_h_m2", None)
                if ventilation_m3_h_m2 is None:
                    raw_evidence = list(
                        getattr(room, "air_exchange_evidence", []) or []
                    )
                    self.rule_engine.add_alert(
                        rule="SIA3802_VENTILATION_UNIT_NOT_COMPARABLE",
                        description=(
                            f"Ventilation rate is present for room {room.name or room.id}, "
                            "but it is not normalized to m3/(h.m2). "
                            f"VE evidence: {raw_evidence!r}"
                        ),
                        severity=Severity.LOW,
                        category="Ventilation",
                        recommendation="Export or convert outdoor airflow per floor area to select the applicable SIA 380/2 table 4 band.",
                        data=room,
                    )
                else:
                    band = self._ventilation_band(ventilation_m3_h_m2)
                    if (
                        getattr(room, "ventilation_installation_type", None)
                        and getattr(room, "ventilation_control_level", None) is not None
                    ):
                        self.rule_engine.check_rules(
                            ["SIA3802_VENTILATION_CONTROL_CLASS"],
                            room,
                        )
                    else:
                        self.rule_engine.add_alert(
                            rule="SIA3802_VENTILATION_CONTROL_EVIDENCE_MISSING",
                            description=(
                                f"Ventilation rate {ventilation_m3_h_m2:.3g} m3/(h.m2) "
                                f"for room {room.name or room.id}; table 4 band: {band}. "
                                "The installation type or comparable control strategy could not be proven. "
                                f"Available VE control context: "
                                f"{getattr(room, 'ventilation_control_evidence_note', '') or 'none'}"
                            ),
                            severity=Severity.LOW,
                            category="Ventilation",
                            recommendation="Document system type, FAN_CTRL, occupancy/gas sensors and airflow reduction to validate the applicable SIA 380/2 table 4 cell.",
                            data=room,
                        )
            else:
                self.rule_engine.add_alert(
                    rule="SIA3802_VENTILATION_RATE_MISSING",
                    description=(
                        f"Mechanical ventilation for room {room.name or room.id} cannot be "
                        "excluded or quantified from a usable room design rate. "
                        f"VE air/system evidence: "
                        f"{getattr(room, 'air_exchange_evidence', [])!r}"
                    ),
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

    def _check_gains(
        self,
        rooms_data: List[RoomData],
        external_mappings: Dict[str, Any],
    ) -> Dict[str, Any]:
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

        screening_rows: List[Dict[str, Any]] = []
        sia2024_mappings = external_mappings.get("sia2024_usage", {}) or {}
        lighting_mappings = external_mappings.get("sia3874_lighting", {}) or {}
        for room in rooms_data:
            usage_mapping = find_accepted_mapping(
                sia2024_mappings,
                room_id=room.id,
                thermal_template_id=getattr(room, "thermal_template_id", ""),
            )
            if not usage_mapping:
                self.rule_engine.add_alert(
                    rule="SIA3802_SIA2024_MAPPING_MISSING",
                    description=f"No reviewer-confirmed SIA 2024 use category is mapped to room {room.name or room.id} or its thermal template.",
                    severity=Severity.MEDIUM,
                    category="Gains",
                    recommendation="Complete SIA2024_usage_mapping_*.csv with room/template, SIA category, reviewer, source and accepted review status.",
                    data=room,
                )
            else:
                setattr(room, "sia2024_category", usage_mapping.get("sia2024_category", ""))

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

            lighting_mapping = find_accepted_mapping(
                lighting_mappings,
                room_id=room.id,
                thermal_template_id=getattr(room, "thermal_template_id", ""),
            )
            if not lighting_mapping:
                dimming = getattr(room, "daylight_dimming_profile", "")
                self.rule_engine.add_alert(
                    rule="SIA3802_LIGHTING_CONTROL_TYPE_MISSING",
                    description=(
                        f"No reviewer-confirmed SIA 387/4 lighting-control mapping is available for room {room.name or room.id}. "
                        f"VE daylight-dimming profile: {dimming or 'not extracted'}."
                    ),
                    severity=Severity.LOW,
                    category="Gains",
                    recommendation="Complete SIA3874_lighting_control_mapping_*.csv; the two current standards do not contain the missing SIA 387/4 numeric/control tables.",
                    data=room,
                )
            else:
                setattr(
                    room,
                    "lighting_control_type",
                    lighting_mapping.get("sia3874_control_type", ""),
                )

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

            screening = self._cooling_need_screening_row(room)
            screening_rows.append(screening)
            if screening["status"] == "NOT_CHECKABLE":
                self.rule_engine.add_alert(
                    rule="SIA3802_COOLING_NEED_SCREENING_NOT_CHECKABLE",
                    description=f"Table 1 cooling-need screening is not checkable for room {room.name or room.id}: {screening['reason']}",
                    severity=Severity.LOW,
                    category="Gains",
                    recommendation="Provide resolvable daily gain profiles and explicit window-operability/support evidence.",
                    data=room,
                )

        return {
            "alerts": self.rule_engine.get_alerts_by_category("Gains"),
            "score": self._calculate_category_score("Gains"),
            "cooling_need_screening": screening_rows,
        }

    def _check_setpoints(self, rooms_data: List[RoomData]) -> Dict[str, Any]:
        """Report heating/cooling operating setpoints and flag missing ones.

        SIA 380/2 operating setpoints are fixed by the normative VE template
        for each SIA 2024 use category. This check does not invent a numeric
        limit or derive a project requirement from a target: it surfaces each
        room's extracted setpoint value, type and profile for reviewer
        confirmation and records ``NOT_CHECKABLE`` when no setpoint can be
        extracted, so a missing operating condition is never silently treated
        as compliant.
        """
        if not rooms_data:
            self.rule_engine.add_alert(
                rule="SIA3802_MODEL_NOT_CHECKABLE_SETPOINTS",
                description="No usable VE room was analysed for operating-setpoint checks.",
                severity=Severity.CRITICAL,
                category="Setpoints",
                recommendation="Confirm the active VE model contains thermal rooms with assigned SIA operating conditions.",
                data=None,
            )

        observations: List[Dict[str, Any]] = []
        for room in rooms_data:
            conditions = getattr(room, "room_conditions", {}) or {}
            heating = self._float_or_none(conditions.get("heating_setpoint"))
            cooling = self._float_or_none(conditions.get("cooling_setpoint"))
            heating_type = str(conditions.get("heating_setpoint_type") or "").strip()
            cooling_type = str(conditions.get("cooling_setpoint_type") or "").strip()
            heating_profile = str(
                conditions.get("heating_setpoint_profile")
                or conditions.get("heating_profile")
                or ""
            ).strip()
            cooling_profile = str(
                conditions.get("cooling_setpoint_profile")
                or conditions.get("cooling_profile")
                or ""
            ).strip()
            # A variable/two-value setpoint is still present through its profile.
            heating_present = (
                heating is not None
                or bool(heating_profile)
                or heating_type in {"variable", "two_value"}
            )
            cooling_present = (
                cooling is not None
                or bool(cooling_profile)
                or cooling_type in {"variable", "two_value"}
            )
            status = "REPORTED" if (heating_present or cooling_present) else "NOT_CHECKABLE"
            observations.append(
                {
                    "room": room.name or room.id,
                    "status": status,
                    "heating_setpoint_c": heating,
                    "heating_setpoint_type": heating_type,
                    "heating_setpoint_profile": heating_profile,
                    "cooling_setpoint_c": cooling,
                    "cooling_setpoint_type": cooling_type,
                    "cooling_setpoint_profile": cooling_profile,
                }
            )
            if status == "NOT_CHECKABLE":
                self.rule_engine.add_alert(
                    rule="SIA3802_SETPOINTS_NOT_CHECKABLE",
                    description=(
                        "No heating or cooling operating setpoint could be extracted for "
                        f"room {room.name or room.id}."
                    ),
                    severity=Severity.MEDIUM,
                    category="Setpoints",
                    recommendation=(
                        "Confirm the SIA operating conditions (heating/cooling setpoint or "
                        "profile) are assigned in the VE thermal template."
                    ),
                    data=room,
                )

        return {
            "status": "DIAGNOSTIC_ONLY",
            "alerts": self.rule_engine.get_alerts_by_category("Setpoints"),
            "observations": observations,
            "note": (
                "Operating setpoints are fixed by the normative VE template (SIA 2024 "
                "usage). Values are reported for reviewer confirmation; this check does "
                "not assign a numeric pass/fail against an invented limit."
            ),
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

        checked_hvac_system_ids = set()
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
                # Apache Systems are project-level objects referenced by every
                # served room. Check a named system once so its evidence and
                # reservations are not repeated for each room assignment.
                system_id = str(hvac.get("id") or "").strip().casefold()
                if system_id:
                    if system_id in checked_hvac_system_ids:
                        continue
                    checked_hvac_system_ids.add(system_id)

                cooling_class = hvac.get("cooling_generator_class")
                heating_class = hvac.get("heating_generator_class")
                if cooling_class in {"air_cooled", "water_cooled"}:
                    self._check_hvac_metric(
                        hvac,
                        "eer",
                        "SIA3802_COOLING_EER_MIN",
                        "nominal EER",
                        "cooling_capacity_kw",
                    )
                    self._check_hvac_metric(
                        hvac,
                        "seer",
                        "SIA3802_COOLING_SEER_MIN",
                        "seasonal SEER",
                        "cooling_capacity_kw",
                    )
                    self._annotate_hvac_targets(hvac)
                elif cooling_class == "water_cooled_post_cooling":
                    self.rule_engine.add_alert(
                        rule="SIA3802_COOLING_EERPLUS_NOT_CHECKABLE",
                        description=f"System {hvac.get('id', 'unknown')} is classified as water-cooled with dry post-cooling, but system-level EER+ at full and 50% load is not exposed by the current VE extraction.",
                        severity=Severity.LOW,
                        category="HVAC",
                        recommendation="Provide Table 7-comparable EER+ including post-cooling fan/pump and chilled-water pump shares; do not substitute nominal EER or SSEER.",
                        data=hvac,
                    )
                elif any(hvac.get(metric) is not None for metric in ("eer", "seer", "sseer")):
                    self.rule_engine.add_alert(
                        rule="SIA3802_COOLING_GENERATOR_CLASS_MISSING",
                        description=f"Cooling efficiency is available for system {hvac.get('id', 'unknown')}, but air-cooled, water-cooled or dry-post-cooling classification is not proven.",
                        severity=Severity.LOW,
                        category="HVAC",
                        recommendation="Expose/document condenser and heat-rejection type before selecting a SIA 380/2 table 5-7 row.",
                        data=hvac,
                    )

                if heating_class in {"air_water_heat_pump", "ground_source_heat_pump"}:
                    self._check_hvac_metric(
                        hvac,
                        "scop",
                        "SIA3802_HEATING_SCOP_MIN",
                        "seasonal SCoP",
                        "heating_capacity_kw",
                    )
                    self._annotate_hvac_targets(hvac)
                elif heating_class == "heat_pump_unclassified":
                    self.rule_engine.add_alert(
                        rule="SIA3802_HEAT_PUMP_CLASS_MISSING",
                        description=f"System {hvac.get('id', 'unknown')} is a heat pump, but its air-water or ground/brine-water class is not proven.",
                        severity=Severity.LOW,
                        category="HVAC",
                        recommendation="Document the heat source/sink before selecting SIA 380/2 table 8 or table 9.",
                        data=hvac,
                    )

                if (
                    cooling_class is None
                    and heating_class is None
                    and not any(hvac.get(metric) is not None for metric in ("eer", "seer", "sseer", "scop"))
                ):
                    self.rule_engine.add_alert(
                        rule="SIA3802_HVAC_EFFICIENCY_MISSING",
                        description=f"No table-comparable HVAC generator efficiency is available for system {hvac.get('id', 'unknown')}.",
                        severity=Severity.LOW,
                        category="HVAC",
                        recommendation="Read EER/SEER/SCoP and generator type/capacity from Apache Systems or attach reviewed system evidence.",
                        data=hvac,
                    )

        self._check_declared_cooling_seer()

        return {
            "alerts": self.rule_engine.get_alerts_by_category("HVAC"),
            "score": self._calculate_category_score("HVAC"),
        }

    def _read_ve_thermal_bridges(self) -> Dict[str, Any]:
        """Read the model's thermal-bridge conductance from VE, if available.

        Guarded: the data extractor is absent in pure-Python tests, and the VE
        members are absent on older versions. Returns an empty dict when the
        read cannot be performed, so the reviewer schedule remains the fallback.
        """
        extractor = getattr(self.model_analyzer, "data_extractor", None)
        if extractor is None or not hasattr(extractor, "get_model_thermal_bridges"):
            return {}
        try:
            return extractor.get_model_thermal_bridges() or {}
        except Exception as exc:  # noqa: BLE001 - never let a read break the audit
            _LOGGER.warning("VE thermal-bridge read failed: %s", exc)
            return {}

    @staticmethod
    def _build_thermal_bridge_result(
        thermal_bridge_scan: Dict[str, Any],
        thermal_bridge_record: Optional[Dict[str, Any]],
        ve_thermal_bridges: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Merge the VE-read thermal-bridge conductance with the reviewer schedule.

        VE-read is primary when the surface members are present and returned data;
        the reviewer schedule is the fallback (older VE / unset model). A VE read
        made only of zero-psi junctions is surfaced but NOT treated as complete
        evidence, so an un-entered default never silently reads as a pass.
        """
        result: Dict[str, Any] = {
            "status": thermal_bridge_scan.get("status"),
            "accepted": bool(thermal_bridge_record),
            "record": thermal_bridge_record,
            "ve_read": ve_thermal_bridges or {},
        }
        ve = ve_thermal_bridges or {}
        if ve.get("readable"):
            result["source"] = "ve_model"
            result["total_w_per_k"] = ve.get("total_w_per_k")
            result["nonzero_count"] = int(ve.get("nonzero_count", 0) or 0)
            result["zero_psi_linear_count"] = int(ve.get("zero_psi_linear_count", 0) or 0)
            # Available as evidence once at least one non-zero junction is read.
            # An all-zero read is transparent but not complete evidence.
            result["ve_available"] = result["nonzero_count"] > 0
        elif thermal_bridge_record:
            result["source"] = "reviewer_csv"
            result["ve_available"] = False
        else:
            result["source"] = "none"
            result["ve_available"] = False
        return result

    def _evaluate_electrical_power(
        self, record: Optional[Dict[str, Any]], has_fluid_installation: bool
    ) -> Dict[str, Any]:
        """Evaluate the reviewed §7.2.4 required electrical power against its limit.

        norm-analyst A5 (traceability/audit-A5-...): §7.2.4 is an AUTONOMOUS,
        conditionally-blocking requirement (not subsumed by §7.2.5.2). The power
        lock (7 W/m2 new / 12 W/m2 existing, §7.2.4.2) only makes a building NON
        compliant when cooling is DESIRABLE/superfluous (§3.2.3.1 n.1, §3.2.5.2);
        when cooling is NECESSARY the norm does not restrict the power. Fail-closed:

          - no fluid installation             -> NOT_APPLICABLE  (§7.2.4.1)
          - installation present, power missing -> NOT_DETERMINED (reserve)
          - power <= limit                     -> OK
          - power > limit, cooling desirable   -> NOT_COMPLIANT
          - power > limit, cooling necessary   -> OK (power unrestricted; §3.2.1.1
                                                  still forces §7.1, gated elsewhere)
          - power > limit, category unknown    -> NOT_DETERMINED (SIA 180/2024 for
                                                  the necessity class are absent)
        """
        result: Dict[str, Any] = {
            "accepted": bool(record and record.get("accepted")),
            "record": record if isinstance(record, dict) else None,
            "meets_limit": None,
            "limit_w_m2": None,
            "verdict_status": None,
        }
        if not isinstance(record, dict) or not record.get("accepted"):
            result["verdict_status"] = (
                "NOT_DETERMINED" if has_fluid_installation else "NOT_APPLICABLE"
            )
            return result
        status_key = record.get("building_status_key")
        limit = SIA3802_ELECTRICAL_POWER_LIMITS_W_M2.get(str(status_key))
        value = self._float_or_none(record.get("required_electrical_power_w_m2_numeric"))
        if limit is None or value is None:
            result["verdict_status"] = "NOT_DETERMINED"
            return result
        result["limit_w_m2"] = limit
        result["meets_limit"] = value <= limit
        if result["meets_limit"]:
            result["verdict_status"] = "OK"
            return result
        category = str(record.get("cooling_category_key") or "")
        if category == "desirable":
            result["verdict_status"] = "NOT_COMPLIANT"
            self.rule_engine.add_alert(
                rule="SIA3802_ELECTRICAL_POWER_EXCEEDS_LIMIT",
                description=(
                    "Reviewed §7.2.4 required electrical power {:.2f} W/m2 exceeds the "
                    "{} limit {:.0f} W/m2, and cooling is desirable/superfluous: per "
                    "SIA 380/2:2022 §3.2.3.1 note 1 / §3.2.5.2 cooling is then admitted "
                    "ONLY with a low-power installation.".format(value, status_key, limit)
                ),
                severity=Severity.HIGH,
                category="Electrical Power",
                recommendation=(
                    "Reduce the required electrical power to <= the §7.2.4 limit, or "
                    "renounce mechanical cooling."
                ),
                data=record,
            )
        elif category == "necessary":
            # Cooling necessary: the power is not restricted by §7.2.4; §3.2.1.1
            # still forces the §7.1 constructive requirements (gated separately).
            result["verdict_status"] = "OK"
        else:
            result["verdict_status"] = "NOT_DETERMINED"
            self.rule_engine.add_alert(
                rule="SIA3802_ELECTRICAL_POWER_CATEGORY_NOT_CHECKABLE",
                description=(
                    "Reviewed §7.2.4 required electrical power {:.2f} W/m2 exceeds the "
                    "{} limit {:.0f} W/m2, but whether the §7.2.4 power lock applies "
                    "depends on the cooling-necessity category (§3.2), which is not "
                    "stated. The building status cannot be concluded.".format(
                        value, status_key, limit
                    )
                ),
                severity=Severity.MEDIUM,
                category="Electrical Power",
                recommendation=(
                    "State the cooling category (necessary / desirable) so §7.2.4 can "
                    "be concluded; necessity classing needs SIA 180 / SIA 2024."
                ),
                data=record,
            )
        return result

    def _check_declared_cooling_seer(self) -> None:
        """Compare a reviewer-declared SEER (EN 14825) to the SIA table 5 band.

        Runs only when an accepted cooling-generator evidence record exists. This
        is the autosize workaround: VE leaves the capacity greyed out, so the
        band cannot be resolved from the model; the reviewer supplies the SIA
        class, the rated capacity and the declared SEER. A declared SEER is
        EN 14825 by construction, so no seasonal-equivalence caveat applies.

        The clean declared comparison covers the SIA 380/2 tables whose minima are
        stated as a SEER "selon SN EN 14825": table 5 (air-cooled) and table 6
        (water-cooled), both across their full power ranges (verified on the
        SIA 380/2:2022 PDF page 38). Only a water-cooled unit with dry post-cooling
        (table 7, an EER+ metric, not a SEER) or an unclassified generator is out
        of scope; those stay NOT_CHECKABLE here. Band resolution itself is left to
        _hvac_metric (a capacity outside the encoded bands -> BAND_NOT_CHECKABLE).
        """
        record = getattr(self, "_reviewer_cooling_generator", None)
        if not isinstance(record, dict):
            return
        sia_class = record.get("sia_cooling_class")
        capacity = self._float_or_none(record.get("capacity_kw_numeric"))
        seer = self._float_or_none(record.get("seer_numeric"))
        if not sia_class or capacity is None or seer is None:
            return
        if sia_class not in ("air_cooled", "water_cooled"):
            self.rule_engine.add_alert(
                rule="SIA3802_COOLING_SEER_DECLARED_OUT_OF_TABLE_SCOPE",
                description=(
                    f"Declared SEER for the reviewer cooling generator "
                    f"({sia_class or 'unclassified'}, {capacity} kW) is outside the "
                    "SIA 380/2 table 5/6 SEER scope. A water-cooled unit with dry "
                    "post-cooling uses table 7's EER+ (not a SEER), and an "
                    "unclassified generator cannot select a table row, so a clean "
                    "SEER comparison cannot be made here."
                ),
                severity=Severity.LOW,
                category="Reference Project Diagnostics",
                recommendation=(
                    "Provide the table-appropriate metric (e.g. table 7 EER+ for "
                    "water-cooled with dry post-cooling); do not compare a declared "
                    "SEER to a non-table-5/6 band."
                ),
                data=record,
            )
            return
        declared_hvac = {
            "id": "reviewer_cooling_generator",
            "cooling_generator_class": sia_class,
            "cooling_capacity_kw": capacity,
            "seer": seer,
            "reviewer_declared": True,
        }
        self._check_hvac_metric(
            declared_hvac,
            "seer",
            "SIA3802_COOLING_SEER_MIN_DECLARED",
            "declared seasonal SEER",
            "cooling_capacity_kw",
        )

    def _check_dynamic_method(self, dynamic_results: Dict[str, Any]) -> Dict[str, Any]:
        """Check full-year comfort evidence and design-power result availability."""
        status = str(dynamic_results.get("status") or "NOT_CHECKABLE").upper()
        building_status = str(
            dynamic_results.get("building_status")
            or SIA3802_DYNAMIC_COMFORT.get("building_status")
            or "UNSPECIFIED"
        ).upper()
        climate_provenance_status = str(
            dynamic_results.get("reviewed_weather_match_status") or "NOT_CHECKABLE"
        ).upper()
        room_rows = [
            row for row in (dynamic_results.get("rooms", []) or [])
            if isinstance(row, dict)
        ]
        series_complete_room_rows = [
            row for row in room_rows
            if row.get("annual_comfort_period_complete")
            and row.get("occupied_hours_above_sia180_upper") is not None
            and row.get("occupied_hours_below_sia180_lower") is not None
        ]
        incomplete_room_rows = [
            row for row in room_rows if row not in series_complete_room_rows
        ]
        unverified_method_rows = [
            row for row in series_complete_room_rows
            if str(row.get("comfort_method_status") or "VERIFIED").upper()
            != "VERIFIED"
        ]
        complete_room_rows = [
            row for row in series_complete_room_rows
            if row not in unverified_method_rows
        ]
        unknown_operability_rows = [
            row for row in complete_room_rows
            if row.get("window_operable") is None
        ]
        non_operable_rows = [
            row for row in complete_room_rows
            if row.get("window_operable") is False
        ]
        upper_hours = dynamic_results.get("max_occupied_hours_above_sia180_upper")
        lower_hours = dynamic_results.get("max_occupied_hours_below_sia180_lower")
        upper_limit_hours = None
        if building_status in {"NEW", "NEW_BUILDING", "NEW_CONSTRUCTION"}:
            upper_limit_hours = SIA3802_DYNAMIC_COMFORT["new_building_upper_exceedance_hours"]
        elif building_status in {"EXISTING", "EXISTING_BUILDING"}:
            upper_limit_hours = SIA3802_DYNAMIC_COMFORT["existing_building_upper_exceedance_hours"]
        building_status_missing_for_non_operable = bool(
            non_operable_rows and upper_limit_hours is None
        )

        comfort_data = {
            "status": status,
            "building_status": building_status,
            "upper_hours": upper_hours,
            "lower_hours": lower_hours,
            "upper_limit_hours": upper_limit_hours,
            "climate_provenance_status": climate_provenance_status,
            "expected_room_count": len(room_rows),
            "complete_room_count": len(complete_room_rows),
            "incomplete_room_count": len(incomplete_room_rows),
            "unverified_method_room_count": len(unverified_method_rows),
            "unknown_operability_room_count": len(unknown_operability_rows),
            "room_results": [],
        }
        if status != "AVAILABLE":
            self.rule_engine.add_alert(
                rule="SIA3802_SUMMER_COMFORT_NOT_CHECKABLE",
                description="SIA 380/2 full-year dynamic comfort is not checkable because APS results or weather provenance are incomplete.",
                severity=Severity.MEDIUM,
                category="Dynamic Method",
                recommendation="Run a full 2022-calendar DRY simulation and ensure the APS weather matches the active VE project weather.",
                data=dynamic_results,
            )
        elif climate_provenance_status != "MATCH":
            self.rule_engine.add_alert(
                rule="SIA3802_REVIEWED_CLIMATE_PROVENANCE_MISSING",
                description="The active VE weather file is not matched to an accepted reviewer-owned SIA climate metadata record.",
                severity=Severity.MEDIUM,
                category="Dynamic Method",
                recommendation="Complete SIA3802_project_metadata_<project>.csv with the reviewed SIA 2028 weather file and confirm it matches the active VE project weather.",
                data=dynamic_results,
            )
        elif not room_rows or incomplete_room_rows:
            self.rule_engine.add_alert(
                rule="SIA3802_ANNUAL_COMFORT_ROOM_COVERAGE_INCOMPLETE",
                description=(
                    f"Annual SIA comfort evidence is complete for {len(complete_room_rows)} "
                    f"of {len(room_rows)} dynamic rooms; every applicable room must be complete."
                ),
                severity=Severity.MEDIUM,
                category="Dynamic Method",
                recommendation="Export aligned annual temperature, occupancy and both SIA 180 limit series for every applicable room.",
                data=incomplete_room_rows,
            )
        elif unverified_method_rows:
            self.rule_engine.add_alert(
                rule="SIA3802_COMFORT_METHOD_NOT_VERIFIED",
                description=(
                    "Annual comfort series are available, but the exact SIA 180 "
                    "operative-temperature quantity and running-mean convention "
                    "have not yet been normatively verified. Reported exceedance "
                    "hours remain screening values, not a determined verdict."
                ),
                severity=Severity.MEDIUM,
                category="Dynamic Method",
                recommendation=(
                    "Validate the operative-temperature and theta_rm conventions "
                    "against SIA 180, then qualify the calculation method before "
                    "issuing a pass/fail comfort conclusion."
                ),
                data=unverified_method_rows,
            )
        else:
            if unknown_operability_rows:
                self.rule_engine.add_alert(
                    rule="SIA3802_WINDOW_OPERABILITY_EVIDENCE_MISSING",
                    description=(
                        f"Window operability is unknown for {len(unknown_operability_rows)} room(s); "
                        "using the 0 h upper-limit allowance as a conservative screening value. "
                        "The comfort domain remains not determined until reviewed "
                        "MacroFlo/window-opening evidence is supplied."
                    ),
                    severity=Severity.MEDIUM,
                    category="Dynamic Method",
                    recommendation="Provide reviewed MacroFlo/window-opening evidence for every applicable room.",
                    data=unknown_operability_rows,
                )
                comfort_data["conservative_zero_hour_screening_count"] = len(
                    unknown_operability_rows
                )
            if non_operable_rows and upper_limit_hours is None:
                building_status = "NEW_BUILDING"
                upper_limit_hours = SIA3802_DYNAMIC_COMFORT["new_building_upper_exceedance_hours"]
                comfort_data["building_status"] = building_status
                comfort_data["upper_limit_hours"] = upper_limit_hours
                comfort_data["building_status_assumed"] = True
                self.rule_engine.add_alert(
                    rule="SIA3802_BUILDING_STATUS_MISSING_ASSUMED_NEW",
                    description=(
                        "Building status is not set; using the NEW_BUILDING 100 h/year "
                        "allowance as a conservative screening value. The comfort domain "
                        "remains not determined until reviewed project metadata is supplied."
                    ),
                    severity=Severity.MEDIUM,
                    category="Dynamic Method",
                    recommendation="Set dynamic_results['building_status'] to NEW_BUILDING or EXISTING_BUILDING from reviewed project metadata.",
                    data=dynamic_results,
                )
            for row in complete_room_rows:
                is_user_operable = row.get("window_operable") is True
                operability_unknown = row.get("window_operable") is None
                room_limit = (
                    0.0
                    if is_user_operable or operability_unknown
                    else upper_limit_hours
                )
                room_data = {
                    "room_id": row.get("room_id"),
                    "room_name": row.get("room_name"),
                    "window_operable": row.get("window_operable"),
                    "method": (
                        "SIA3802_3.2.4.2_USER_OPERABLE"
                        if is_user_operable
                        else (
                            "CONSERVATIVE_ZERO_HOUR_SCREENING_OPERABILITY_UNKNOWN"
                            if operability_unknown
                            else "SIA3802_3.2.4.3_TO_3.2.4.5_ANNUAL_ALLOWANCE"
                        )
                    ),
                    "upper_hours": row.get("occupied_hours_above_sia180_upper"),
                    "lower_hours": row.get("occupied_hours_below_sia180_lower"),
                    "upper_limit_hours": room_limit,
                }
                comfort_data["room_results"].append(room_data)
                self.rule_engine.check_rules(
                    ["SIA3802_SUMMER_COMFORT_DYNAMIC"],
                    room_data,
                )

        design_power_status = str(dynamic_results.get("design_power_status") or "NOT_CHECKABLE").upper()
        if design_power_status != "AVAILABLE":
            for rule, label in (
                ("SIA3802_HEATING_DESIGN_POWER_NOT_CHECKABLE", "four-day January heating design-power"),
                ("SIA3802_COOLING_DESIGN_POWER_NOT_CHECKABLE", "three-day cooling design-power"),
            ):
                self.rule_engine.add_alert(
                    rule=rule,
                    description=f"The SIA 380/2 {label} result is not checkable from the selected annual APS file.",
                    severity=Severity.LOW,
                    category="Dynamic Method",
                    recommendation="Provide documented design-day/sizing results with the required 14-day preconditioning; annual simulated peaks are not equivalent.",
                    data=dynamic_results,
                )

        return {
            "status": (
                "CHECKED"
                if status == "AVAILABLE"
                and climate_provenance_status == "MATCH"
                and bool(room_rows)
                and not incomplete_room_rows
                and not unverified_method_rows
                and not unknown_operability_rows
                and not building_status_missing_for_non_operable
                else "NOT_CHECKABLE"
            ),
            "comfort": comfort_data,
            "design_power_status": design_power_status,
            "score": self._calculate_category_score("Dynamic Method"),
            "alerts": self.rule_engine.get_alerts_by_category("Dynamic Method"),
        }

    def _check_hvac_metric(
        self,
        hvac: Dict[str, Any],
        metric: str,
        rule_name: str,
        metric_label: str,
        capacity_key: str,
    ) -> None:
        """Run one capacity-banded HVAC rule or emit an explicit missing alert."""
        if hvac.get(capacity_key) is None:
            self.rule_engine.add_alert(
                rule=f"{rule_name}_CAPACITY_MISSING",
                description=f"{metric_label} cannot be compared for system {hvac.get('id', 'unknown')} because rated capacity is missing.",
                severity=Severity.LOW,
                category="HVAC",
                recommendation="Expose generator gen_size in kW or provide reviewed capacity evidence.",
                data=hvac,
            )
            return
        if hvac.get(metric) is None:
            self.rule_engine.add_alert(
                rule=f"{rule_name}_VALUE_MISSING",
                description=f"{metric_label} is missing for system {hvac.get('id', 'unknown')}.",
                severity=Severity.LOW,
                category="HVAC",
                recommendation=f"Expose the documented VE {metric} value before comparing the SIA reference-project row.",
                data=hvac,
            )
            return
        if self._hvac_limit(hvac, metric) is None:
            self.rule_engine.add_alert(
                rule=f"{rule_name}_BAND_NOT_CHECKABLE",
                description=f"No SIA 380/2 table row covers the extracted class/capacity for system {hvac.get('id', 'unknown')}.",
                severity=Severity.LOW,
                category="HVAC",
                recommendation="Verify generator class, units and capacity-band boundary; do not extrapolate beyond the published table.",
                data=hvac,
            )
            return
        self.rule_engine.check_rules([rule_name], hvac)

    @classmethod
    def _hvac_metric_meets_limit(cls, hvac: Dict[str, Any], metric: str) -> bool:
        """Compare one HVAC metric with its exact capacity-banded limit."""
        value = cls._float_or_none(hvac.get(metric))
        limit = cls._hvac_limit(hvac, metric)
        return value is not None and limit is not None and value >= limit

    @classmethod
    def _hvac_limit(cls, hvac: Dict[str, Any], metric: str) -> Optional[float]:
        """Return the applicable table 5, 6, 8 or 9 limit without extrapolation."""
        if metric in {"eer", "seer"}:
            generator_class = hvac.get("cooling_generator_class")
            table = SIA3802_COOLING_EER_SEER_LIMITS.get(str(generator_class), {})
            capacity = cls._float_or_none(hvac.get("cooling_capacity_kw"))
            band = cls._capacity_band(capacity, table)
            return cls._float_or_none((table.get(band, {}) or {}).get(metric)) if band else None
        if metric == "scop":
            generator_class = hvac.get("heating_generator_class")
            table = SIA3802_HEATING_SCOP_LIMITS.get(str(generator_class), {})
            capacity = cls._float_or_none(hvac.get("heating_capacity_kw"))
            band = cls._capacity_band(capacity, table)
            return cls._float_or_none(table.get(band)) if band else None
        return None

    @classmethod
    def _annotate_hvac_targets(cls, hvac: Dict[str, Any]) -> None:
        """Attach secondary target indicators without changing pass/fail status."""
        cooling_class = str(hvac.get("cooling_generator_class") or "")
        cooling_targets = SIA3802_COOLING_EER_SEER_TARGETS.get(cooling_class, {})
        cooling_band = cls._capacity_band(
            cls._float_or_none(hvac.get("cooling_capacity_kw")),
            cooling_targets,
        )
        if cooling_band:
            hvac["eer_target"] = cls._float_or_none(cooling_targets[cooling_band].get("eer"))
            hvac["seer_target"] = cls._float_or_none(cooling_targets[cooling_band].get("seer"))

        heating_class = str(hvac.get("heating_generator_class") or "")
        heating_targets = SIA3802_HEATING_SCOP_TARGETS.get(heating_class)
        heating_band = cls._capacity_band(
            cls._float_or_none(hvac.get("heating_capacity_kw")),
            heating_targets if isinstance(heating_targets, dict) else {},
        )
        hvac["scop_target"] = (
            cls._float_or_none(heating_targets.get(heating_band))
            if isinstance(heating_targets, dict) and heating_band
            else None
        )
        hvac["table_8_target_exists"] = heating_class != "air_water_heat_pump"

    @staticmethod
    def _capacity_band(capacity_kw: Optional[float], table: Dict[str, Any]) -> Optional[str]:
        """Select a published capacity band with deterministic boundary handling."""
        if capacity_kw is None or capacity_kw < 0 or not isinstance(table, dict):
            return None
        ordered_bands = ("<=12", "12-50", "50-150", "150-450", "450-1000", ">1000")
        for band in ordered_bands:
            if band not in table:
                continue
            if band == "<=12" and capacity_kw <= 12:
                return band
            if band == "12-50" and (
                (12 < capacity_kw <= 50)
                or ("<=12" not in table and 12 <= capacity_kw <= 50)
            ):
                return band
            if band == "50-150" and 50 < capacity_kw <= 150:
                return band
            if band == "150-450" and 150 < capacity_kw <= 450:
                return band
            if band == "450-1000" and 450 < capacity_kw <= 1000:
                return band
            if band == ">1000" and capacity_kw > 1000:
                return band
        return None

    @classmethod
    def _cooling_need_screening_row(cls, room: RoomData) -> Dict[str, Any]:
        """Evaluate the informational SIA 380/2 table 1 cooling screening."""
        gains = cls._float_or_none(getattr(room, "internal_gains_wh_m2_day", None))
        support = str(getattr(room, "window_ventilation_support", "") or "")
        row = {
            "rule": "SIA3802_COOLING_NEED_SCREENING_RESULT",
            "room_id": room.id,
            "room_name": room.name,
            "internal_gains_wh_m2_day": gains,
            "window_ventilation_support": support,
            "status": "NOT_CHECKABLE",
            "hard_pass_fail": False,
            "reason": "",
            "source": SIA3802_COOLING_NEED_SCREENING.get("source", ""),
        }
        thresholds = SIA3802_COOLING_NEED_SCREENING.get(support)
        if gains is None:
            row["reason"] = "daily internal gains could not be integrated from VE profiles"
            return row
        if not isinstance(thresholds, dict):
            thresholds = SIA3802_COOLING_NEED_SCREENING.get("no_window_support")
            if not isinstance(thresholds, dict):
                row["reason"] = "no_window_support threshold missing from config"
                return row
            row["window_ventilation_support"] = "no_window_support"
            row["window_ventilation_support_assumed"] = True
            support = "no_window_support"
        necessary_above = float(thresholds["necessary_above_wh_m2_day"])
        desirable_min = float(thresholds["desirable_min_wh_m2_day"])
        if gains > necessary_above:
            row["status"] = "NECESSARY"
        elif gains >= desirable_min:
            row["status"] = "DESIRABLE"
        else:
            row["status"] = "NOT_NECESSARY"
        row["reason"] = "Informational table 1 screening; not an autonomous compliance verdict"
        return row

    @classmethod
    def _ventilation_control_meets_limit(cls, room: RoomData) -> bool:
        """Compare extracted control strategy rank with the applicable table-4 limit."""
        installation_type = str(getattr(room, "ventilation_installation_type", "") or "").lower()
        airflow = cls._float_or_none(getattr(room, "ventilation_m3_h_m2", None))
        actual_level = getattr(room, "ventilation_control_level", None)
        if not installation_type or airflow is None or actual_level is None:
            return False
        band = cls._ventilation_band(airflow)
        cell = SIA3802_VENTILATION_CONTROL_TABLE.get((installation_type, band), {})
        required_level = cls._ventilation_control_rank(cell.get("limit"))
        return required_level is not None and int(actual_level) >= required_level

    @staticmethod
    def _ventilation_control_rank(label: Any) -> Optional[int]:
        """Map exact table-4 control descriptions to ordered capability levels."""
        text = str(label or "").lower()
        if "variable speed" in text and "gas sensor" in text:
            return 4
        if "variable speed" in text and "occupancy" in text:
            return 3
        if "two speeds" in text and "occupancy" in text:
            return 2
        if "two speeds" in text:
            return 1
        if "one speed" in text:
            return 0
        return None

    @staticmethod
    def _float_or_none(value: Any) -> Optional[float]:
        """Convert a candidate numeric value without accepting invalid data."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _calculate_category_score(self, category: str) -> float:
        """Calculate a category score from 0 to 100.

        The score must not read as "good" when a category's inputs are not
        verifiable. An indeterminate alert (missing / not-checkable evidence,
        same definition the verdict uses) therefore carries a heavy penalty --
        far above a determined advisory -- and the score is capped below the pass
        band while any indeterminate alert remains. This aligns the number with
        the verdict, which marks such a domain NOT_DETERMINED: a category riddled
        with unverifiable inputs can no longer report ~85 (audit A2, 2026-08-20).
        It is never forced to 0 for merely-missing evidence, which would be a
        false failure; only a genuinely blocking alert scores 0.
        """
        alerts = self.rule_engine.get_alerts_by_category(category)
        if not alerts:
            return 100.0

        if any(self._is_blocking_not_checkable_alert(alert) for alert in alerts):
            return 0.0

        score = 100.0
        has_indeterminate = False
        for alert in alerts:
            if self._is_indeterminate_alert(alert):
                # Unverifiable input: much heavier than a determined advisory,
                # so a category cannot look verified when it is not.
                score -= 20.0
                has_indeterminate = True
            elif alert.severity == Severity.CRITICAL:
                score -= 25.0
            elif alert.severity == Severity.HIGH:
                score -= 15.0
            elif alert.severity == Severity.MEDIUM:
                score -= 10.0
            elif alert.severity == Severity.LOW:
                score -= 5.0
        if has_indeterminate:
            # Cap below the pass band: "incomplete", not "good".
            score = min(score, INCOMPLETE_EVIDENCE_SCORE_CEILING)
        return max(0.0, min(100.0, score))

    @staticmethod
    def _is_blocking_not_checkable_alert(alert: Alert) -> bool:
        """Return true when a category cannot produce a meaningful SIA 380/2 score."""
        rule = str(alert.rule or "").upper()
        return alert.severity == Severity.CRITICAL and (
            "MODEL_NOT_CHECKABLE" in rule
            or "EXTERNAL_ENVELOPE_MISSING" in rule
            or "RULE_EXECUTION_ERROR" in rule
        )

    @staticmethod
    def _is_indeterminate_alert(alert: Alert) -> bool:
        """Return true when an alert marks missing / not-checkable evidence.

        Same "cannot check" markers the verdict uses (compliance_verdict.py),
        so the score and the verdict agree on what counts as undetermined.
        """
        rule = str(alert.rule or "").upper()
        return any(marker in rule for marker in _INDETERMINATE_ALERT_MARKERS)

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
