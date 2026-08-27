"""Regression tests for source-traced VE enums, conversions and thresholds."""

import inspect
from types import SimpleNamespace
import unittest

from swiss_sia.config import (
    SIA3802_U_VALUES,
    SIA_COMPLIANCE_VALUE_PROVENANCE,
)
from swiss_sia.data_extractor import VEDataExtractor
from swiss_sia.model_analyzer import ModelAnalyzer, OpeningData, RoomData
from swiss_sia.rule_engine import RuleEngine
from swiss_sia.sia380_checker import SIA3802Checker


class IESVELiteralTraceabilityTests(unittest.TestCase):
    """Ensure no observed VE ordinal or heuristic becomes hidden evidence."""

    def test_every_implementation_contract_has_trace_fields(self):
        keys = (
            "room_air_exchange_type_val",
            "room_air_exchange_units_val",
            "internal_gain_power_units_val",
            "surface_opening_type",
            "airflow_l_s_to_m3_h",
            "window_support_full_day_threshold",
            "generator_classification",
            "door_u_value_limit",
        )
        for key in keys:
            with self.subTest(key=key):
                contract = SIA_COMPLIANCE_VALUE_PROVENANCE[key]
                self.assertTrue(contract["locator"])
                self.assertTrue(contract["unit"])
                self.assertTrue(contract["rationale"])

    def test_air_exchange_enum_values_come_from_traced_contract(self):
        contract = SIA_COMPLIANCE_VALUE_PROVENANCE["room_air_exchange_type_val"]
        units_contract = SIA_COMPLIANCE_VALUE_PROVENANCE["room_air_exchange_units_val"]
        ach = units_contract["values"]["ach"]
        exchanges = [
            SimpleNamespace(
                get=lambda: {
                    "type_val": contract["values"]["auxiliary_ventilation"],
                    "units_val": ach,
                    "max_flows": {ach: 1.2},
                    "units_strs": {ach: "ach"},
                }
            ),
            SimpleNamespace(
                get=lambda: {
                    "type_val": contract["values"]["infiltration"],
                    "units_val": ach,
                    "max_flows": {ach: 0.15},
                    "units_strs": {ach: "ach"},
                }
            ),
        ]
        analyzer = ModelAnalyzer(
            SimpleNamespace(get_air_exchanges=lambda _room: exchanges)
        )

        summary = analyzer._analyze_air_exchanges(object())

        self.assertEqual(summary["air_exchange_classification_status"], "OK")
        self.assertEqual(summary["ventilation_rate"], 1.2)
        self.assertEqual(summary["infiltration_rate"], 0.15)

    def test_numeric_opening_ordinals_are_not_mapped(self):
        for raw in SIA_COMPLIANCE_VALUE_PROVENANCE["surface_opening_type"][
            "unverified_numeric_values"
        ]:
            with self.subTest(raw=raw):
                audit = VEDataExtractor._opening_type_audit(raw)
                self.assertEqual(audit["status"], "NOT_CHECKABLE")
                self.assertIsNone(audit["value"])
                self.assertIn("[TO VERIFY]", audit["note"])

        verified = VEDataExtractor._opening_type_audit("VESurface_type.ext_glazing")
        self.assertEqual(verified["status"], "OK")
        self.assertEqual(verified["value"], "window")

    def test_operable_profile_does_not_use_an_uncited_full_day_threshold(self):
        extractor = SimpleNamespace(
            get_macroflo_openings=lambda: {
                "MF-1": {"openable_area": 1.0, "profile": "DAY-1"}
            },
            get_profile_daily_equivalent_hours=lambda _profile: 24.0,
        )
        opening = OpeningData(
            id="O-1",
            opening_type="window",
            opening_type_status="OK",
            is_external=True,
            macroflo_id="MF-1",
        )

        result = ModelAnalyzer(extractor)._analyze_window_ventilation([opening])

        self.assertTrue(result["window_operable"])
        self.assertIsNone(result["window_ventilation_support"])
        self.assertEqual(result["window_ventilation_support_status"], "NOT_CHECKABLE")
        self.assertIn("[TO VERIFY]", result["window_ventilation_support_note"])

    def test_generator_classification_uses_exact_documented_enum_field_only(self):
        exact = ModelAnalyzer._classify_cooling_generator(
            {},
            {"type": "iesve.ncm_chiller_type.air_cooled"},
            "ignored free text",
        )
        inferred = ModelAnalyzer._classify_cooling_generator(
            {},
            {"description": "air cooled dry post cooler"},
            "air cooled dry post cooler",
        )
        heating = ModelAnalyzer._classify_heating_generator(
            {"Is_heat_pump": True},
            {"heat_source": "iesve.ncm_heat_source.heat_pump_ground_or_water_source"},
            "ground source",
        )

        self.assertEqual(exact, "air_cooled")
        self.assertIsNone(inferred)
        self.assertEqual(heating, "heat_pump_unclassified")

    def test_door_window_u_alias_is_removed_and_visible(self):
        self.assertIsNone(SIA3802_U_VALUES["door"])
        analyzer = ModelAnalyzer(SimpleNamespace())
        engine = RuleEngine()
        checker = SIA3802Checker(analyzer, engine)
        room = RoomData(
            id="R-1",
            openings=[
                OpeningData(
                    id="D-1",
                    opening_type="door",
                    opening_type_status="OK",
                    is_external=True,
                    u_value=1.0,
                )
            ],
        )

        checker._check_openings([room])

        alerts = [
            alert for alert in engine.alerts if alert.rule == "SIA3802_U_VALUE_DOOR"
        ]
        self.assertEqual(len(alerts), 1)
        self.assertIn("TO VERIFY", alerts[0].description)

    def test_listed_literals_are_absent_from_decision_code(self):
        opening_source = inspect.getsource(VEDataExtractor._normalize_opening_type)
        window_source = inspect.getsource(ModelAnalyzer._analyze_window_ventilation)
        airflow_source = inspect.getsource(ModelAnalyzer._derive_m3_h_m2_from_flow_table)
        selector_source = inspect.getsource(VEDataExtractor._select_best_model)
        extractor_source = inspect.getsource(VEDataExtractor)

        for ordinal in SIA_COMPLIANCE_VALUE_PROVENANCE["surface_opening_type"][
            "unverified_numeric_values"
        ]:
            self.assertNotIn(f"({ordinal},", opening_source)
        self.assertNotIn("23.5", window_source)
        self.assertNotIn("* 3.6", airflow_source)
        self.assertNotIn("return models[0]", selector_source)
        self.assertNotIn("ashae", extractor_source)


if __name__ == "__main__":
    unittest.main()
