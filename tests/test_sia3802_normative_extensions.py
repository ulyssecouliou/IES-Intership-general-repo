"""Unit tests for the pure-Python SIA 380/2 normative extensions."""

import unittest
from unittest.mock import Mock

from swiss_sia.config import (
    SIA3802_COOLING_EER_SEER_TARGETS,
    SIA3802_COOLING_NEED_SCREENING,
    SIA3802_HEATING_SCOP_TARGETS,
    SIA3802_LIMIT_VALUES,
    SIA3802_SOLAR_PROTECTION_CATEGORIES,
    SIA3802_SOURCE_REFERENCES,
    SIA3802_SUMMER_COMFORT_SIMULATION_CONDITIONS,
    SIA3802_TARGET_VALUES,
    SIA3802_WATER_COOLED_POST_COOLING_EERPLUS,
)
from swiss_sia.model_analyzer import RoomData
from swiss_sia.rule_engine import RuleEngine
from swiss_sia.sia380_checker import SIA3802Checker
from swiss_sia.simulation_results import (
    collect_room_dynamic_results,
    convert_aps_series_to_metric,
    count_occupied_hours_outside_limits,
    integrate_positive_result_to_kwh,
    integrate_positive_watts_to_kwh,
    is_complete_365_day_series,
    normalize_co2_series_to_ppm,
    peak_power_to_watts,
)


class NormativeConstantTests(unittest.TestCase):
    """Pin the values transcribed from the normative SIA tables."""

    def test_table_1_cooling_need_screening_constants_are_exact(self):
        self.assertEqual(
            SIA3802_COOLING_NEED_SCREENING,
            {
                "day_and_night_window_support": {
                    "necessary_above_wh_m2_day": 200.0,
                    "desirable_min_wh_m2_day": 140.0,
                    "not_necessary_below_wh_m2_day": 140.0,
                },
                "occupied_hours_window_support": {
                    "necessary_above_wh_m2_day": 140.0,
                    "desirable_min_wh_m2_day": 100.0,
                    "not_necessary_below_wh_m2_day": 100.0,
                },
                "no_window_support": {
                    "necessary_above_wh_m2_day": 120.0,
                    "desirable_min_wh_m2_day": 80.0,
                    "not_necessary_below_wh_m2_day": 80.0,
                },
                "source": "SIA 380/2:2022 FR, tableau 1, page PDF 21",
                "assessment_only": True,
            },
        )

    def test_table_3_u_value_limit_and_target_constants_are_exact(self):
        table_3_keys = (
            "external_wall_u",
            "external_wall_against_ground_u",
            "internal_partition_non_bearing_u",
            "internal_partition_bearing_u",
            "internal_wall_unconditioned_u",
            "ground_floor_u",
            "intermediate_floor_u",
            "intermediate_floor_unconditioned_u",
            "flat_roof_u",
        )
        self.assertEqual(
            {key: SIA3802_LIMIT_VALUES[key] for key in table_3_keys},
            {
                "external_wall_u": 0.20,
                "external_wall_against_ground_u": 0.30,
                "internal_partition_non_bearing_u": 0.30,
                "internal_partition_bearing_u": 2.70,
                "internal_wall_unconditioned_u": 0.28,
                "ground_floor_u": 0.30,
                "intermediate_floor_u": 0.64,
                "intermediate_floor_unconditioned_u": 0.30,
                "flat_roof_u": 0.20,
            },
        )
        self.assertEqual(
            {key: SIA3802_TARGET_VALUES[key] for key in table_3_keys},
            {
                "external_wall_u": 0.14,
                "external_wall_against_ground_u": 0.20,
                "internal_partition_non_bearing_u": 0.30,
                "internal_partition_bearing_u": 2.70,
                "internal_wall_unconditioned_u": 0.20,
                "ground_floor_u": 0.20,
                "intermediate_floor_u": 0.64,
                "intermediate_floor_unconditioned_u": 0.20,
                "flat_roof_u": 0.14,
            },
        )
        self.assertEqual(
            SIA3802_SOURCE_REFERENCES["table_3"],
            "SIA 380/2:2022 FR, tableau 3, pages PDF 36-37",
        )

    def test_table_10_solar_protection_constants_are_exact(self):
        self.assertEqual(
            SIA3802_SOLAR_PROTECTION_CATEGORIES,
            {
                1: {
                    "lamellae": {
                        "solar_reflectance": 0.70,
                        "solar_transmittance": 0.00,
                    },
                    "fabric": {
                        "solar_reflectance": 0.50,
                        "solar_transmittance": 0.25,
                    },
                },
                2: {
                    "lamellae": {
                        "solar_reflectance": 0.70,
                        "solar_transmittance": 0.00,
                    }
                },
                3: {
                    "lamellae": {
                        "solar_reflectance": 0.50,
                        "solar_transmittance": 0.00,
                    },
                    "fabric": {
                        "solar_reflectance": 0.35,
                        "solar_transmittance": 0.25,
                    },
                },
                4: {
                    "lamellae": {
                        "solar_reflectance": 0.30,
                        "solar_transmittance": 0.00,
                    },
                    "fabric": {
                        "solar_reflectance": 0.25,
                        "solar_transmittance": 0.10,
                    },
                },
                5: {
                    "fabric": {
                        "solar_reflectance": 0.20,
                        "solar_transmittance": 0.05,
                    }
                },
            },
        )
        self.assertEqual(
            SIA3802_SOURCE_REFERENCES["table_10"],
            "SIA 380/2:2022 FR, tableau 10, page PDF 46",
        )

    def test_table_11_simulation_conditions_are_exact(self):
        self.assertEqual(
            SIA3802_SUMMER_COMFORT_SIMULATION_CONDITIONS,
            {
                "evaluated_quantity": (
                    "Operative temperature at room centre, 1.0 m above floor"
                ),
                "critical_radiative_zones_separate": True,
                "climate_source": (
                    "Normal DRY per SIA 2028 for the most representative station"
                ),
                "ch2018_scenario_data_available_from": 2022,
                "observation_period": {
                    "start": "2022-01-01",
                    "end": "2022-12-31",
                    "calendar_note": (
                        "1 January 2022 is Saturday; the calendar fixes working "
                        "days and holidays"
                    ),
                },
                "solar_protection": {
                    "planned_or_existing_characteristics_and_control": True,
                    "wind_resistance_considered": True,
                    "free_field_wind_at_one_metre_above_roof": True,
                    "summer_heat_protection_requirements_satisfied": True,
                },
                "internal_gains": {
                    "agreed_use_conditions_or_sia2024": True,
                    "people_activity_heat_gain_per_sia180": True,
                    "lighting_daylight_control_and_solar_protection_interaction": True,
                    "equipment_agreed_use_conditions_or_sia2024": True,
                },
                "occupied_fresh_air": (
                    "Normal-operation hygienic flow according to SIA 2024 and "
                    "system sizing"
                ),
                "unoccupied_fresh_air": {
                    "normal_flow_condition": (
                        "indoor_minus_outdoor_temperature_gt_4K_and_"
                        "indoor_temperature_gt_24C"
                    ),
                    "otherwise_m3_h_m2": 0.15,
                },
                "occupancy_time": (
                    "Planned use schedule or standard SIA 2024 schedule"
                ),
                "system_schedule": {
                    "start_before_occupancy_hours": 1,
                    "stop_after_occupancy_hours": 1,
                    "operate_through_lunch_break": True,
                },
                "source": (
                    "SIA 380/2:2022 FR, tableau 11, annexe C normative, "
                    "page PDF 59"
                ),
            },
        )

    def test_cooling_eer_and_seer_target_constants_are_exact(self):
        self.assertEqual(
            SIA3802_COOLING_EER_SEER_TARGETS,
            {
                "air_cooled": {
                    "<=12": {"eer": 3.10, "seer": 4.20},
                    "12-50": {"eer": 3.15, "seer": 4.35},
                    "50-150": {"eer": 3.20, "seer": 4.50},
                    "150-450": {"eer": 3.40, "seer": 4.80},
                    "450-1000": {"eer": 3.60, "seer": 5.00},
                },
                "water_cooled": {
                    "12-50": {"eer": 4.45, "seer": 5.90},
                    "50-150": {"eer": 4.65, "seer": 6.10},
                    "150-450": {"eer": 5.05, "seer": 6.90},
                    "450-1000": {"eer": 5.50, "seer": 7.40},
                    ">1000": {"eer": 6.00, "seer": 8.00},
                },
            },
        )

    def test_table_7_eer_plus_constants_are_exact(self):
        self.assertEqual(
            SIA3802_WATER_COOLED_POST_COOLING_EERPLUS,
            {
                "12-50": {
                    "limit": {"full_load": 3.15, "part_load_50": 4.55},
                    "target": {"full_load": 3.95, "part_load_50": 5.60},
                },
                "50-150": {
                    "limit": {"full_load": 3.20, "part_load_50": 4.70},
                    "target": {"full_load": 4.00, "part_load_50": 6.00},
                },
                "150-450": {
                    "limit": {"full_load": 3.30, "part_load_50": 5.30},
                    "target": {"full_load": 4.10, "part_load_50": 7.00},
                },
                "450-1000": {
                    "limit": {"full_load": 3.50, "part_load_50": 5.80},
                    "target": {"full_load": 4.30, "part_load_50": 7.60},
                },
                ">1000": {
                    "limit": {"full_load": 3.70, "part_load_50": 6.00},
                    "target": {"full_load": 4.50, "part_load_50": 8.00},
                },
                "auxiliary_power_assumptions": {
                    "post_cooling_fans_max_fraction": 0.036,
                    "post_cooling_pump_max_fraction": 0.012,
                    "chilled_water_pump_max_fraction": 0.015,
                },
            },
        )

    def test_scop_target_constants_are_exact(self):
        self.assertEqual(
            SIA3802_HEATING_SCOP_TARGETS,
            {
                "air_water_heat_pump": None,
                "ground_source_heat_pump": {
                    "12-50": 4.40,
                    "50-150": 4.60,
                    "150-450": 5.00,
                    "450-1000": 5.50,
                    ">1000": 6.00,
                },
            },
        )


class CheckerBehaviorTests(unittest.TestCase):
    """Exercise checker behavior with normalized Python data only."""

    @staticmethod
    def _new_checker():
        engine = RuleEngine()
        return SIA3802Checker(model_analyzer=object(), rule_engine=engine), engine

    def test_hvac_eer_seer_and_scop_pass_fail_and_missing(self):
        cases = (
            {
                "metric": "eer",
                "rule": "SIA3802_COOLING_EER_MIN",
                "label": "nominal EER",
                "capacity_key": "cooling_capacity_kw",
                "base": {
                    "cooling_generator_class": "air_cooled",
                    "cooling_capacity_kw": 25.0,
                },
                "pass_value": 3.00,
                "fail_value": 2.99,
            },
            {
                "metric": "seer",
                "rule": "SIA3802_COOLING_SEER_MIN",
                "label": "seasonal SEER",
                "capacity_key": "cooling_capacity_kw",
                "base": {
                    "cooling_generator_class": "air_cooled",
                    "cooling_capacity_kw": 25.0,
                },
                "pass_value": 3.90,
                "fail_value": 3.89,
            },
            {
                "metric": "scop",
                "rule": "SIA3802_HEATING_SCOP_MIN",
                "label": "seasonal SCoP",
                "capacity_key": "heating_capacity_kw",
                "base": {
                    "heating_generator_class": "ground_source_heat_pump",
                    "heating_capacity_kw": 25.0,
                },
                "pass_value": 4.00,
                "fail_value": 3.99,
            },
        )

        for case in cases:
            with self.subTest(metric=case["metric"], status="pass"):
                checker, engine = self._new_checker()
                hvac = dict(case["base"], id="pass-system")
                hvac[case["metric"]] = case["pass_value"]
                checker._check_hvac_metric(
                    hvac,
                    case["metric"],
                    case["rule"],
                    case["label"],
                    case["capacity_key"],
                )
                self.assertTrue(
                    checker._hvac_metric_meets_limit(hvac, case["metric"])
                )
                self.assertEqual(engine.get_alerts_by_category("HVAC"), [])

            with self.subTest(metric=case["metric"], status="fail"):
                checker, engine = self._new_checker()
                hvac = dict(case["base"], id="fail-system")
                hvac[case["metric"]] = case["fail_value"]
                checker._check_hvac_metric(
                    hvac,
                    case["metric"],
                    case["rule"],
                    case["label"],
                    case["capacity_key"],
                )
                self.assertFalse(
                    checker._hvac_metric_meets_limit(hvac, case["metric"])
                )
                self.assertEqual(
                    [
                        alert.rule
                        for alert in engine.get_alerts_by_category(
                            "Reference Project Diagnostics"
                        )
                    ],
                    [case["rule"]],
                )

            with self.subTest(metric=case["metric"], status="missing"):
                checker, engine = self._new_checker()
                hvac = dict(case["base"], id="missing-system")
                checker._check_hvac_metric(
                    hvac,
                    case["metric"],
                    case["rule"],
                    case["label"],
                    case["capacity_key"],
                )
                self.assertFalse(
                    checker._hvac_metric_meets_limit(hvac, case["metric"])
                )
                self.assertEqual(
                    [alert.rule for alert in engine.get_alerts_by_category("HVAC")],
                    [case["rule"] + "_VALUE_MISSING"],
                )

    def test_hvac_project_system_is_checked_once_across_room_assignments(self):
        checker, engine = self._new_checker()
        shared_system = {"id": "SYST0000", "seer": 2.5}
        rooms = [
            RoomData(id="room-1", hvac_systems=[dict(shared_system)]),
            RoomData(id="room-2", hvac_systems=[dict(shared_system)]),
            RoomData(id="room-3", hvac_systems=[dict(shared_system)]),
        ]

        checker._check_hvac(rooms)

        matching_alerts = [
            alert
            for alert in engine.get_alerts_by_category("HVAC")
            if alert.rule == "SIA3802_COOLING_GENERATOR_CLASS_MISSING"
        ]
        self.assertEqual(len(matching_alerts), 1)

    def test_table_4_ventilation_control_pass_fail_and_missing(self):
        common = {
            "ventilation_rate": 1.0,
            "ventilation_m3_h_m2": 4.0,
            "ventilation_installation_type": "monozone",
            "infiltration_m3_h_m2": 0.15,
            "air_exchange_classification_status": "OK",
        }

        checker, engine = self._new_checker()
        passing_room = RoomData(
            id="pass-room",
            ventilation_control_level=1,
            **common,
        )
        checker._check_ventilation([passing_room])
        self.assertTrue(checker._ventilation_control_meets_limit(passing_room))
        self.assertEqual(engine.get_alerts_by_category("Ventilation"), [])

        checker, engine = self._new_checker()
        failing_room = RoomData(
            id="fail-room",
            ventilation_control_level=0,
            **common,
        )
        checker._check_ventilation([failing_room])
        self.assertFalse(checker._ventilation_control_meets_limit(failing_room))
        self.assertEqual(
            [
                alert.rule
                for alert in engine.get_alerts_by_category(
                    "Reference Project Diagnostics"
                )
            ],
            ["SIA3802_VENTILATION_CONTROL_CLASS"],
        )

        checker, engine = self._new_checker()
        missing_room = RoomData(
            id="missing-room",
            ventilation_control_level=None,
            **common,
        )
        checker._check_ventilation([missing_room])
        self.assertFalse(checker._ventilation_control_meets_limit(missing_room))
        self.assertEqual(
            [
                alert.rule
                for alert in engine.get_alerts_by_category("Ventilation")
            ],
            ["SIA3802_VENTILATION_CONTROL_EVIDENCE_MISSING"],
        )

    def test_reviewed_ventilation_record_is_applied_only_when_band_matches(self):
        checker, _ = self._new_checker()
        checker._reviewer_ventilation_controls = [{
            "system_id": "SYS-1",
            "room_or_zone": "",
            "system_type_normalized": "monozone",
            "control_class": "two_speeds_time_schedule",
            "control_level_numeric": 1,
            "airflow_band_normalized": "3-6",
            "specific_airflow_m3_h_m2_numeric": 4.0,
            "source_document": "ventilation_design.pdf",
        }]
        room = RoomData(
            id="R1",
            ventilation_rate=4.0,
            ventilation_m3_h_m2=4.0,
            mechanical_ventilation_present=True,
            hvac_systems=[{"id": "SYS-1"}],
        )

        applied = checker._apply_reviewed_ventilation_controls([room])

        self.assertEqual(applied, 1)
        self.assertEqual(room.ventilation_installation_type, "monozone")
        self.assertEqual(room.ventilation_control_level, 1)
        self.assertEqual(room.ventilation_control_level_status, "REVIEWER_ACCEPTED")

    def test_natural_ventilation_does_not_raise_mechanical_rate_missing(self):
        checker, engine = self._new_checker()
        room = RoomData(
            id="R1",
            mechanical_ventilation_present=False,
            air_exchange_classification_status="OK",
            infiltration_m3_h_m2=0.15,
        )

        checker._check_ventilation([room])

        self.assertNotIn(
            "SIA3802_VENTILATION_RATE_MISSING",
            [alert.rule for alert in engine.get_alerts_by_category("Ventilation")],
        )

    def test_room_scope_disambiguates_records_on_the_same_system(self):
        checker, _ = self._new_checker()
        base = {
            "system_id": "SYS-1",
            "system_type_normalized": "monozone",
            "control_class": "one_speed_time_schedule",
            "control_level_numeric": 0,
            "airflow_band_normalized": "<=3",
            "specific_airflow_m3_h_m2_numeric": 2.0,
            "source_document": "ventilation_design.pdf",
        }
        checker._reviewer_ventilation_controls = [
            dict(base, room_or_zone="R1"),
            dict(base, room_or_zone="R2"),
        ]
        rooms = [
            RoomData(
                id=room_id,
                ventilation_rate=2.0,
                ventilation_m3_h_m2=2.0,
                mechanical_ventilation_present=True,
                hvac_systems=[{"id": "SYS-1"}],
            )
            for room_id in ("R1", "R2")
        ]

        self.assertEqual(checker._apply_reviewed_ventilation_controls(rooms), 2)

    def test_cooling_need_screening_statuses(self):
        cases = (
            (121.0, "no_window_support", "NECESSARY"),
            (120.0, "no_window_support", "DESIRABLE"),
            (79.0, "no_window_support", "NOT_NECESSARY"),
            (None, "no_window_support", "NOT_CHECKABLE"),
            (100.0, None, "DESIRABLE"),
        )
        for gains, support, expected_status in cases:
            with self.subTest(
                gains=gains,
                support=support,
                expected_status=expected_status,
            ):
                row = SIA3802Checker._cooling_need_screening_row(
                    RoomData(
                        id="screening-room",
                        internal_gains_wh_m2_day=gains,
                        window_ventilation_support=support,
                    )
                )
                self.assertEqual(row["status"], expected_status)
                self.assertFalse(row["hard_pass_fail"])

    def test_dynamic_comfort_requires_reviewed_climate_match(self):
        """Block comfort checking until reviewed and active weather files match."""
        checker, _engine = self._new_checker()
        result = checker._check_dynamic_method({
            "status": "AVAILABLE",
            "building_status": "NEW_BUILDING",
            "reviewed_weather_match_status": "MISMATCH",
            "max_occupied_hours_above_sia180_upper": 10.0,
            "max_occupied_hours_below_sia180_lower": 0.0,
            "rooms": [{
                "room_id": "room-1",
                "room_name": "Room 1",
                "annual_comfort_period_complete": True,
                "occupied_hours_above_sia180_upper": 10.0,
                "occupied_hours_below_sia180_lower": 0.0,
                "window_operable": False,
            }],
            "design_power_status": "NOT_CHECKABLE",
        })
        rules = {alert.rule for alert in result["alerts"]}

        self.assertEqual(result["status"], "NOT_CHECKABLE")
        self.assertIn("SIA3802_REVIEWED_CLIMATE_PROVENANCE_MISSING", rules)

    def test_dynamic_comfort_checks_with_reviewed_climate_match(self):
        """Run the annual comfort rule when all conservative gates are present."""
        checker, _engine = self._new_checker()
        result = checker._check_dynamic_method({
            "status": "AVAILABLE",
            "building_status": "NEW_BUILDING",
            "reviewed_weather_match_status": "MATCH",
            "max_occupied_hours_above_sia180_upper": 10.0,
            "max_occupied_hours_below_sia180_lower": 0.0,
            "rooms": [{
                "room_id": "room-1",
                "room_name": "Room 1",
                "annual_comfort_period_complete": True,
                "occupied_hours_above_sia180_upper": 10.0,
                "occupied_hours_below_sia180_lower": 0.0,
                "window_operable": False,
            }],
            "design_power_status": "NOT_CHECKABLE",
        })
        rules = {alert.rule for alert in result["alerts"]}

        self.assertEqual(result["status"], "CHECKED")
        self.assertNotIn("SIA3802_SUMMER_COMFORT_DYNAMIC", rules)

    def test_unverified_comfort_method_never_emits_determined_noncompliance(self):
        """Keep computed exceedance hours as screening until the method is qualified."""
        checker, _engine = self._new_checker()
        result = checker._check_dynamic_method({
            "status": "AVAILABLE",
            "building_status": "NEW_BUILDING",
            "reviewed_weather_match_status": "MATCH",
            "rooms": [{
                "room_id": "room-1",
                "room_name": "Room 1",
                "annual_comfort_period_complete": True,
                "occupied_hours_above_sia180_upper": 1462.0,
                "occupied_hours_below_sia180_lower": 1.0,
                "window_operable": True,
                "comfort_method_status": "NOT_CHECKABLE",
                "comfort_method_note": "PENDING norm-analyst",
            }],
            "design_power_status": "NOT_CHECKABLE",
        })
        rules = {alert.rule for alert in result["alerts"]}

        self.assertEqual(result["status"], "NOT_CHECKABLE")
        self.assertIn("SIA3802_COMFORT_METHOD_NOT_VERIFIED", rules)
        self.assertNotIn("SIA3802_SUMMER_COMFORT_DYNAMIC", rules)
        self.assertEqual(result["comfort"]["unverified_method_room_count"], 1)

    def test_unknown_operability_uses_zero_hour_screening_without_passing(self):
        """Screen unknown operability strictly while preserving the evidence gap."""
        checker, _engine = self._new_checker()
        result = checker._check_dynamic_method({
            "status": "AVAILABLE",
            "building_status": "NEW_BUILDING",
            "reviewed_weather_match_status": "MATCH",
            "rooms": [{
                "room_id": "room-1",
                "room_name": "Room 1",
                "annual_comfort_period_complete": True,
                "occupied_hours_above_sia180_upper": 0.0,
                "occupied_hours_below_sia180_lower": 0.0,
                "window_operable": None,
            }],
            "design_power_status": "NOT_CHECKABLE",
        })

        self.assertEqual(result["status"], "NOT_CHECKABLE")
        room_result = result["comfort"]["room_results"][0]
        self.assertEqual(room_result["upper_limit_hours"], 0.0)
        self.assertEqual(
            room_result["method"],
            "CONSERVATIVE_ZERO_HOUR_SCREENING_OPERABILITY_UNKNOWN",
        )
        self.assertIn(
            "SIA3802_WINDOW_OPERABILITY_EVIDENCE_MISSING",
            {alert.rule for alert in result["alerts"]},
        )

    def test_unknown_building_status_is_screened_as_new_without_passing(self):
        """Use the stricter new-building allowance but retain missing evidence."""
        checker, _engine = self._new_checker()
        result = checker._check_dynamic_method({
            "status": "AVAILABLE",
            "reviewed_weather_match_status": "MATCH",
            "rooms": [{
                "room_id": "room-1",
                "room_name": "Room 1",
                "annual_comfort_period_complete": True,
                "occupied_hours_above_sia180_upper": 0.0,
                "occupied_hours_below_sia180_lower": 0.0,
                "window_operable": False,
            }],
            "design_power_status": "NOT_CHECKABLE",
        })

        self.assertEqual(result["status"], "NOT_CHECKABLE")
        self.assertEqual(result["comfort"]["upper_limit_hours"], 100.0)
        self.assertIn(
            "SIA3802_BUILDING_STATUS_MISSING_ASSUMED_NEW",
            {alert.rule for alert in result["alerts"]},
        )

    def test_user_operable_room_uses_zero_hour_upper_limit(self):
        """Apply clause 3.2.4.2 without the 100/400-hour allowance."""
        checker, _engine = self._new_checker()
        result = checker._check_dynamic_method({
            "status": "AVAILABLE",
            "building_status": "NEW_BUILDING",
            "reviewed_weather_match_status": "MATCH",
            "rooms": [{
                "room_id": "room-1",
                "room_name": "Room 1",
                "annual_comfort_period_complete": True,
                "occupied_hours_above_sia180_upper": 1.0,
                "occupied_hours_below_sia180_lower": 0.0,
                "window_operable": True,
            }],
            "design_power_status": "NOT_CHECKABLE",
        })

        self.assertEqual(result["status"], "CHECKED")
        self.assertEqual(
            result["comfort"]["room_results"][0]["upper_limit_hours"],
            0.0,
        )
        self.assertIn(
            "SIA3802_SUMMER_COMFORT_DYNAMIC",
            {alert.rule for alert in result["alerts"]},
        )
        comfort_alert = next(
            alert
            for alert in result["alerts"]
            if alert.rule == "SIA3802_SUMMER_COMFORT_DYNAMIC"
        )
        self.assertIn("temperatures exceed", comfort_alert.description)
        self.assertNotIn("temperatures satisfy", comfort_alert.description)

    def test_incomplete_room_blocks_annual_comfort(self):
        """Reject an aggregate conclusion when one applicable room is incomplete."""
        checker, _engine = self._new_checker()
        result = checker._check_dynamic_method({
            "status": "AVAILABLE",
            "building_status": "NEW_BUILDING",
            "reviewed_weather_match_status": "MATCH",
            "rooms": [
                {
                    "room_id": "complete",
                    "annual_comfort_period_complete": True,
                    "occupied_hours_above_sia180_upper": 0.0,
                    "occupied_hours_below_sia180_lower": 0.0,
                    "window_operable": False,
                },
                {
                    "room_id": "incomplete",
                    "annual_comfort_period_complete": False,
                    "window_operable": False,
                },
            ],
            "design_power_status": "NOT_CHECKABLE",
        })

        self.assertEqual(result["status"], "NOT_CHECKABLE")
        self.assertIn(
            "SIA3802_ANNUAL_COMFORT_ROOM_COVERAGE_INCOMPLETE",
            {alert.rule for alert in result["alerts"]},
        )


class SetpointCheckTests(unittest.TestCase):
    """Exercise the conservative operating-setpoint diagnostic."""

    @staticmethod
    def _new_checker():
        """Return a checker and its rule engine with no VE dependency."""
        engine = RuleEngine()
        return SIA3802Checker(model_analyzer=object(), rule_engine=engine), engine

    def test_constant_setpoints_are_reported_without_alert(self):
        checker, engine = self._new_checker()
        room = RoomData(
            id="room-1",
            name="Office",
            room_conditions={
                "heating_setpoint": 21.0,
                "heating_setpoint_type": "constant",
                "cooling_setpoint": 26.0,
                "cooling_setpoint_type": "constant",
            },
        )
        result = checker._check_setpoints([room])
        self.assertEqual(result["status"], "DIAGNOSTIC_ONLY")
        self.assertEqual(result["observations"][0]["status"], "REPORTED")
        self.assertEqual(result["observations"][0]["heating_setpoint_c"], 21.0)
        self.assertEqual(result["observations"][0]["cooling_setpoint_c"], 26.0)
        self.assertEqual(engine.get_alerts_by_category("Setpoints"), [])

    def test_variable_setpoint_via_profile_is_reported(self):
        checker, engine = self._new_checker()
        room = RoomData(
            id="room-2",
            name="Variable",
            room_conditions={
                "heating_setpoint_type": "variable",
                "heating_setpoint_profile": "SIA_HEATING_PROFILE",
            },
        )
        result = checker._check_setpoints([room])
        self.assertEqual(result["observations"][0]["status"], "REPORTED")
        self.assertEqual(engine.get_alerts_by_category("Setpoints"), [])

    def test_missing_setpoints_are_not_checkable_never_pass(self):
        checker, engine = self._new_checker()
        room = RoomData(id="room-3", name="Empty", room_conditions={})
        result = checker._check_setpoints([room])
        self.assertEqual(result["observations"][0]["status"], "NOT_CHECKABLE")
        self.assertEqual(
            [alert.rule for alert in engine.get_alerts_by_category("Setpoints")],
            ["SIA3802_SETPOINTS_NOT_CHECKABLE"],
        )

    def test_no_rooms_flag_model_not_checkable(self):
        checker, engine = self._new_checker()
        result = checker._check_setpoints([])
        self.assertEqual(result["observations"], [])
        self.assertEqual(
            [alert.rule for alert in engine.get_alerts_by_category("Setpoints")],
            ["SIA3802_MODEL_NOT_CHECKABLE_SETPOINTS"],
        )


class SimulationHelperTests(unittest.TestCase):
    def test_count_occupied_hours_outside_limits_above_and_below(self):
        temperatures = [25.0, 29.0, 17.0, 15.0, 30.0]
        occupancy = [1.0, 1.0, 1.0, 1.0, 0.0]
        limits = [26.0, 28.0, 18.0, 16.0, 29.0]

        self.assertEqual(
            count_occupied_hours_outside_limits(
                temperatures,
                occupancy,
                limits,
                2.0,
                direction="above",
            ),
            0.5,
        )
        self.assertEqual(
            count_occupied_hours_outside_limits(
                temperatures,
                occupancy,
                limits,
                2.0,
                direction="below",
            ),
            1.5,
        )

    def test_count_occupied_hours_outside_limits_rejects_missing_inputs(self):
        self.assertIsNone(
            count_occupied_hours_outside_limits(
                [],
                [1.0],
                [26.0],
                1.0,
                direction="above",
            )
        )

    def test_empty_watt_integration_returns_none(self):
        self.assertIsNone(integrate_positive_watts_to_kwh([], 1.0))

    def test_complete_year_requires_exact_aligned_length(self):
        """Accept exactly 365 days and reject partial or overlong series."""
        hourly_year = [0.0] * (365 * 24)
        self.assertTrue(is_complete_365_day_series(hourly_year, 1.0))
        self.assertFalse(is_complete_365_day_series(hourly_year[:-1], 1.0))
        self.assertFalse(is_complete_365_day_series(hourly_year + [0.0], 1.0))
        self.assertFalse(is_complete_365_day_series(hourly_year, 0.0))

    def test_declared_aps_power_units_are_converted(self):
        """Integrate kW as kWh and normalize kW peaks to watts."""
        values = [1.0, 2.0]
        self.assertEqual(
            integrate_positive_result_to_kwh(values, "Heating load [kW]", 1.0),
            3.0,
        )
        self.assertEqual(peak_power_to_watts(values, "Heating load [kW]"), 2000.0)
        self.assertIsNone(peak_power_to_watts(values, "Heating energy [kWh]"))

    def test_units_type_is_resolved_without_unit_in_variable_name(self):
        """Use the ResultsReader unit catalog instead of guessing from names."""
        reader = Mock()
        reader.get_variables.return_value = [{
            "aps_varname": "HEAT_LOAD",
            "display_name": "Heating load",
            "model_level": "z",
            "units_type": 7,
        }]
        reader.get_units.return_value = {
            7: {"units_metric": {"display_name": "kW"}}
        }
        reader.get_room_list.return_value = []
        from swiss_sia.simulation_results import (
            find_aps_variable,
            get_available_variables,
            result_label,
        )

        variable = find_aps_variable(
            get_available_variables(reader),
            ("heating", "load"),
            "z",
        )

        self.assertIsNotNone(variable)
        label = result_label(variable)
        self.assertIn("kW", label)
        self.assertEqual(
            integrate_positive_result_to_kwh([1.0, 2.0], label, 1.0),
            3.0,
        )

    def test_resultsreader_metric_divisor_is_applied_before_reporting(self):
        """Convert raw APS power and CO2 values with the documented unit divisor."""
        power_variable = ("COOL", "Cooling load", "z", "W", 1000.0, 0.0)
        co2_variable = ("CO2", "Room CO2 concentration", "z", "ppm", 0.000001, 0.0)

        self.assertEqual(
            convert_aps_series_to_metric([3_406_347.65625], power_variable),
            [3406.34765625],
        )
        converted_co2 = convert_aps_series_to_metric([0.0004], co2_variable)
        normalized_co2, note = normalize_co2_series_to_ppm(
            converted_co2,
            "Room CO2 concentration [unit=ppm]",
        )
        self.assertEqual(len(normalized_co2), 1)
        self.assertAlmostEqual(normalized_co2[0], 400.0)
        self.assertEqual(note, "ppm")

    def test_tiny_co2_values_are_corrected_even_when_label_claims_ppm(self):
        """Reject physically implausible 0.0004 ppm when unit metadata lacks a divisor."""
        values, note = normalize_co2_series_to_ppm(
            [0.0004, 0.0008],
            "Room CO2 concentration [unit=ppm]",
        )

        self.assertEqual(values, [400.0, 800.0])
        self.assertEqual(note, "converted from fraction to ppm")

    def test_timestep_and_cumulative_kwh_are_distinguished_by_label(self):
        """Sum timestep kWh and use the endpoint only for explicit cumulative data."""
        self.assertEqual(
            integrate_positive_result_to_kwh([1.0, 1.0, 1.0], "Energy [kWh]", 1.0),
            3.0,
        )
        self.assertEqual(
            integrate_positive_result_to_kwh([1.0, 2.0, 3.0], "Cumulative energy [kWh]", 1.0),
            3.0,
        )

    def test_failed_comfort_reads_remain_missing(self):
        """Never convert result-read exceptions into zero overheating hours."""
        reader = Mock()
        reader.results_per_day = 24
        reader.get_units.return_value = {}
        reader.get_variables.return_value = [
            {"aps_varname": "TEMP", "display_name": "Dry resultant temperature", "model_level": "z"},
            {"aps_varname": "OCC", "display_name": "Number people", "model_level": "z"},
            {"aps_varname": "UPPER", "display_name": "Upper comfort temperature", "model_level": "w"},
            {"aps_varname": "LOWER", "display_name": "Lower comfort temperature", "model_level": "w"},
        ]
        reader.get_room_list.return_value = [("Room 1", "room-1", 10.0)]
        reader.get_room_results.side_effect = RuntimeError("read failed")
        reader.get_weather_results.side_effect = RuntimeError("read failed")

        rows = collect_room_dynamic_results(reader)

        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0].occupied_hours_above_26)
        self.assertIsNone(rows[0].occupied_hours_above_27)
        self.assertFalse(rows[0].annual_comfort_period_complete)


if __name__ == "__main__":
    unittest.main()
