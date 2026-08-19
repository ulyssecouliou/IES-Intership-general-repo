"""Regression tests for conservative SIA claim and evidence handling."""

from pathlib import Path
from types import SimpleNamespace
import unittest

from swiss_sia.excel_report import ExcelReportGenerator
from swiss_sia.evidence_pack import (
    matches_active_project_scope,
    _should_include_evidence_file,
)
from swiss_sia.model_analyzer import ModelAnalyzer, OpeningData, RoomData
from swiss_sia.rule_engine import Alert, Rule, RuleEngine, Severity
from swiss_sia.sia380_checker import SIA3802Checker
from swiss_sia.sia4010_checker import SIA4010Checker
from swiss_sia.sia4010_prevalidation import _build_stats


class ClaimSafetyExtensionTests(unittest.TestCase):
    """Prevent schema presence or unreviewed files from creating positive claims."""

    def test_empty_mapping_keys_do_not_create_classifier_text(self):
        """Ignore API schema keys whose nested values are entirely empty."""
        text = ModelAnalyzer._mapping_text({
            "water_cooled": None,
            "fan_ctrl": "",
            "co2": {"sensor": None},
            "gas_sensor": False,
            "real_value": "available",
        })

        self.assertNotIn("water_cooled", text)
        self.assertNotIn("fan_ctrl", text)
        self.assertNotIn("co2", text)
        self.assertNotIn("gas_sensor", text)
        self.assertIn("real_value available", text)

    def test_undocumented_generator_flags_do_not_create_a_classification(self):
        """Do not derive a generator class from undocumented key-name tokens."""
        cooling_ncm = {"water_cooled": False, "air_cooled": True}
        text = ModelAnalyzer._mapping_text(cooling_ncm)

        result = ModelAnalyzer._classify_cooling_generator({}, cooling_ncm, text)

        self.assertIsNone(result)

    def test_adjacency_uses_documented_body_id_property(self):
        """Ignore invented adjacency labels and preserve documented room IDs."""
        analyzer = ModelAnalyzer.__new__(ModelAnalyzer)
        analyzer.data_extractor = SimpleNamespace(_as_dict=lambda value: dict(value))
        adjacency = SimpleNamespace(
            type="external_air",
            name="Outside",
            get_properties=lambda: {"body_id": "ROOM-ADJACENT"},
        )

        self.assertEqual(
            analyzer._get_adjacency_body_id(adjacency),
            "ROOM-ADJACENT",
        )
        self.assertEqual(
            analyzer._get_adjacency_body_id({"body_id": "ROOM-DICT"}),
            "ROOM-DICT",
        )

    def test_zero_final_energy_is_explicit_evidence(self):
        """Accept a numeric zero without accepting unrelated empty HVAC keys."""
        room = RoomData(
            id="room-1",
            hvac_systems=[{
                "final_energy": 0.0,
                "fan_control": None,
                "heat_recovery_type": None,
            }],
        )
        stats = _build_stats(
            [room],
            {"energy": {}},
            {"status": "NOT_CHECKABLE", "rooms": []},
        )

        self.assertTrue(stats["final_energy_available"])
        self.assertFalse(stats["fan_control_evidence"])
        self.assertFalse(stats["heat_recovery_evidence"])

    def test_zero_rule_evaluations_never_render_pass(self):
        """Require an actual rule execution before an automated PASS is possible."""
        generator = ExcelReportGenerator.__new__(ExcelReportGenerator)
        requirement = {
            "automation": "AUTOMATED",
            "implemented_rule": "EXAMPLE_RULE",
            "id": "EXAMPLE_REQUIREMENT",
        }

        row = generator._build_requirement_matrix_row(
            requirement,
            alerts=[],
            rule_evaluations={},
        )

        self.assertEqual(row["status"], "NOT_CHECKABLE")
        self.assertEqual(row["evaluated_count"], 0)

    def test_rule_exception_is_critical_and_never_counted_as_evaluated(self):
        """Turn an implementation error into explicit fail-closed evidence."""

        engine = RuleEngine()
        engine.add_rule(
            Rule(
                name="BROKEN_RULE",
                description="Broken rule used by the regression test.",
                check=lambda _data: 1 / 0,
                severity=Severity.LOW,
                category="Envelope",
                recommendation="Repair the rule.",
            )
        )

        alerts = engine.check_rules(["BROKEN_RULE"], object())

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].severity.name, "CRITICAL")
        self.assertEqual(alerts[0].rule, "RULE_EXECUTION_ERROR:BROKEN_RULE")
        self.assertEqual(engine.evaluated_counts.get("BROKEN_RULE", 0), 0)
        self.assertEqual(engine.evaluation_error_counts["BROKEN_RULE"], 1)

    def test_rule_exception_forces_zero_sia3802_category_score(self):
        """Prevent a broken compliance rule from producing a 100 percent score."""

        engine = RuleEngine()
        checker = SIA3802Checker(SimpleNamespace(), engine)
        engine.add_rule(
            Rule(
                name="BROKEN_ENVELOPE_RULE",
                description="Broken rule used by the regression test.",
                check=lambda _data: (_ for _ in ()).throw(RuntimeError("broken")),
                severity=Severity.LOW,
                category="Envelope",
                recommendation="Repair the rule.",
            )
        )

        engine.check_rules(["BROKEN_ENVELOPE_RULE"], object())

        self.assertEqual(checker._calculate_category_score("Envelope"), 0.0)

    def test_seasonal_seer_scop_rules_carry_the_sn_en_14825_caveat(self):
        """SEER/SCoP rest on the unverified SN EN 14825 index equivalence, so a
        signed report must never state 'meets the SIA limit' for them without the
        [TO VERIFY] caveat. The full-load EER rule compares the directly named
        Table 5 value and must stay caveat-free."""
        engine = RuleEngine()
        SIA3802Checker(SimpleNamespace(), engine)
        rules = {rule.name: rule for rule in engine.rules}

        for name in ("SIA3802_COOLING_SEER_MIN", "SIA3802_HEATING_SCOP_MIN"):
            rule = rules[name]
            self.assertIn("SN EN 14825", rule.description, name)
            self.assertIn("TO VERIFY", rule.description, name)
            self.assertIn("SN EN 14825", rule.recommendation, name)

        eer = rules["SIA3802_COOLING_EER_MIN"]
        self.assertNotIn("SN EN 14825", eer.description)

    def test_reference_input_deviation_is_not_a_compliance_failure(self):
        """Keep reference-project deviations in their dedicated report state."""
        generator = ExcelReportGenerator.__new__(ExcelReportGenerator)
        requirement = {
            "automation": "REFERENCE_DIAGNOSTIC",
            "implemented_rule": "SIA3802_U_VALUE_EXTERNAL_WALL",
            "id": "SIA3802_ENV_EXT_WALL_U",
        }
        alert = Alert(
            rule="SIA3802_U_VALUE_EXTERNAL_WALL",
            description="Reference-project input deviation.",
            severity=Severity.LOW,
            category="Reference Project Diagnostics",
            recommendation="Complete the global comparison.",
        )

        row = generator._build_requirement_matrix_row(
            requirement,
            alerts=[alert],
            rule_evaluations={"SIA3802_U_VALUE_EXTERNAL_WALL": 1},
        )

        self.assertEqual(row["status"], "REFERENCE_DEVIATION")
        self.assertNotEqual(row["status"], "FAIL")

    def test_window_reference_check_absorbs_only_float_serialization_noise(self):
        """Accept VE float noise but retain a real reference-input deviation."""
        rule_engine = RuleEngine()
        SIA3802Checker(SimpleNamespace(), rule_engine)

        rule_engine.check_rules(
            ["SIA3802_U_VALUE_WINDOW"],
            OpeningData(id="near", u_value=1.100028395652771),
        )
        self.assertEqual(rule_engine.alerts, [])

        rule_engine.check_rules(
            ["SIA3802_U_VALUE_WINDOW"],
            OpeningData(id="outside", u_value=1.1002),
        )
        self.assertEqual(rule_engine.alerts[-1].rule, "SIA3802_U_VALUE_WINDOW")

    def test_official_result_requires_candidate_and_reference_families(self):
        """Reject existing files that do not belong to the configured evidence families."""
        row = {
            "test_id": "test_1",
            "status": "pass",
            "reference_file": "random_reference.xlsx",
            "candidate_file": "random_candidate.xlsx",
            "deviation": "0.0",
            "tolerance": "0.1",
            "reviewer": "Reviewer",
            "review_date": "2026-07-15",
            "source_authority": "SIA sub-commission",
            "source_reference": "Decision reference",
        }
        files = [
            {"name": "random_reference.xlsx", "path": "sia4010_evidence/random_reference.xlsx"},
            {"name": "random_candidate.xlsx", "path": "sia4010_evidence/random_candidate.xlsx"},
        ]

        SIA4010Checker._annotate_official_test_result_row(row, files)

        self.assertEqual(row["row_status"], "REFERENCE_FILE_FAMILY_MISMATCH")

    def test_documented_litres_per_second_per_m2_unit_is_converted(self):
        """Recognize the exact l/s/m2 label documented by the VEScripts API."""
        result = ModelAnalyzer._derive_m3_h_m2_from_flow_table(
            {2: 1.0},
            {2: "l/s/m²"},
        )

        self.assertEqual(result, 3.6)

    def test_person_ventilation_is_normalized_only_with_occupancy_evidence(self):
        """Convert l/s/person only when m2/person is explicit and positive."""
        result = ModelAnalyzer._derive_m3_h_m2_from_person_flow(
            {3: 10.0},
            {3: "l/s/person"},
            15.0,
        )

        self.assertAlmostEqual(result, 2.4)
        self.assertIsNone(
            ModelAnalyzer._derive_m3_h_m2_from_person_flow(
                {3: 10.0},
                {3: "l/s/person"},
                None,
            )
        )

    def test_energy_source_metadata_never_returns_plausible_zero_consumption(self):
        """Require ResultsReader consumption data instead of source metadata dictionaries."""
        analyzer = ModelAnalyzer.__new__(ModelAnalyzer)

        result = analyzer.calculate_total_energy_consumption({
            "electricity": {"id": 1, "name": "Electricity", "cef": 1.0}
        })

        self.assertIsNone(result)

    def test_low_severity_volume_never_becomes_p1(self):
        """Keep repeated reference diagnostics below the manager-blocking P1 tier."""
        priority = ExcelReportGenerator._get_priority({
            "max_severity": "Low",
            "count": 126,
            "rule": "SIA3802_FRAME_FRACTION",
        })

        self.assertEqual(priority, "P2")

    def test_dynamic_coverage_requires_complete_annual_comfort_series(self):
        """Do not call fixed-temperature indicators complete annual SIA comfort evidence."""
        generator = ExcelReportGenerator.__new__(ExcelReportGenerator)
        status, evidence = generator._coverage_status_for_key(
            "hourly_temperatures",
            {
                "dynamic_room_rows": 3,
                "dynamic_temperature_rows": 3,
                "dynamic_annual_comfort_rows": 0,
            },
            {},
            {},
            {},
        )

        self.assertEqual(status, "PARTIAL")
        self.assertIn("0/3", evidence)

    def test_thermal_bridge_coverage_never_accepts_placeholder_zero_as_evidence(self):
        """Keep the zero reference placeholder separate from project evidence."""
        generator = ExcelReportGenerator.__new__(ExcelReportGenerator)
        status, evidence = generator._coverage_status_for_key(
            "thermal_bridges",
            {},
            {},
            {},
            {},
        )

        self.assertEqual(status, "MISSING")
        self.assertIn("placeholder", evidence)

    def test_project_helper_files_are_included_only_for_active_project(self):
        """Include generated helper CSVs but prevent cross-project pack contamination."""
        active = Path(
            "sia4010_evidence/SIA3802_project_metadata_Demo_Project.csv"
        )
        colliding = Path(
            "sia4010_evidence/SIA3802_project_metadata_Demo_Project_10.csv"
        )
        include, reason = _should_include_evidence_file(
            active,
            Path("sia4010_evidence"),
        )

        self.assertTrue(include, reason)
        self.assertTrue(matches_active_project_scope(active, "Demo_Project"))
        self.assertFalse(matches_active_project_scope(colliding, "Demo_Project"))
        self.assertFalse(matches_active_project_scope(str(colliding), "Demo_Project"))


if __name__ == "__main__":
    unittest.main()
