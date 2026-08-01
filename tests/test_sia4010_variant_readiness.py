"""Unit tests for SIA 4010 variant readiness and workbook adapters."""

from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from swiss_sia import sia4010_test_adapters
from swiss_sia.config import (
    SIA4010_CLASS_TEST_MATRIX,
    SIA4010_TEST_VARIANT_REQUIREMENTS,
)
from swiss_sia.model_analyzer import RoomData
from swiss_sia.sia4010_checker import SIA4010Checker


EXPECTED_CLASS_TEST_MATRIX = {
    "1A": ["test_1", "test_2A"],
    "1B": ["test_1", "test_2B", "test_2C", "test_2D"],
    "2B": [
        "test_1",
        "test_2B",
        "test_2C",
        "test_2D",
        "test_3A",
        "test_3B",
        "test_3C",
        "test_3D",
        "test_3E",
        "test_3F",
        "test_3G",
        "test_3H",
        "test_3I",
        "test_3J",
        "test_3K",
        "test_3L",
    ],
    "4B": [
        "test_1",
        "test_2B",
        "test_2C",
        "test_2D",
        "test_3A",
        "test_3B",
        "test_3C",
        "test_3D",
        "test_3E",
        "test_3F",
        "test_3G",
        "test_3H",
        "test_3I",
        "test_3J",
        "test_3K",
        "test_3L",
        "test_4",
        "test_5A",
        "test_5B",
        "test_5C",
        "test_5D",
        "test_6",
        "test_7",
    ],
    "5": ["test_7"],
}


class SIA4010VariantReadinessTests(unittest.TestCase):
    """Verify class matrices and conservative readiness payloads."""

    def assert_no_official_verdict(self, payload):
        """Recursively reject exact PASS or VALIDATED scalar values."""
        if isinstance(payload, dict):
            for key, value in payload.items():
                self.assert_no_official_verdict(key)
                self.assert_no_official_verdict(value)
        elif isinstance(payload, (list, tuple, set)):
            for value in payload:
                self.assert_no_official_verdict(value)
        elif isinstance(payload, str):
            self.assertNotIn(payload, {"PASS", "VALIDATED"})

    @staticmethod
    def make_checker():
        """Build a checker without ModelAnalyzer, RuleEngine, or IESVE."""
        checker = SIA4010Checker.__new__(SIA4010Checker)
        checker._scan_sia4010_evidence = Mock(return_value={"files": []})
        checker._summarize_evidence = Mock(return_value={
            "status": "READY_FOR_OFFICIAL_REVIEW",
            "missing_items": [],
        })
        return checker

    @staticmethod
    def make_fully_populated_room():
        """Return one simple room that satisfies every readiness fact."""
        room = RoomData(
            id="room-1",
            surfaces=[SimpleNamespace(is_external=True, u_value=0.25)],
            openings=[SimpleNamespace(
                is_external=True,
                opening_type="window",
                g_value_bs_en_410=0.5,
                shading_type="fabric",
                shading_control="solar",
            )],
            internal_gains={"lighting": 7.5},
            daylight_dimming_profile="daylight-profile",
            window_operable=True,
            ventilation_m3_h_m2=3.6,
            hvac_systems=[{
                "fan_control": "DIRECT",
                "humidifier_control": "STEAM",
                "overflow_paths": ["kitchen"],
                "final_energy": 0.0,
                "storage_generation_data": {"boiler": "present"},
            }],
            heat_recovery_type="PLATE",
            ventilation_control_level=1,
            dynamic_results={
                "lighting_kwh": 0.0,
                "coil_heating_kwh": 0.0,
                "occupied_hours_above_26": 0.0,
                "peak_co2_ppm": 0.0,
                "heating_kwh": 0.0,
                "fan_kwh": 0.0,
            },
        )
        room.lighting_control_type = "DAYLIGHT_LINKED"
        return room

    def test_requested_class_matrix_and_24_variants_are_exact(self):
        for class_name, expected_variants in EXPECTED_CLASS_TEST_MATRIX.items():
            with self.subTest(validation_class=class_name):
                self.assertEqual(
                    SIA4010_CLASS_TEST_MATRIX[class_name],
                    expected_variants,
                )

        expected_variants = {
            variant
            for variants in EXPECTED_CLASS_TEST_MATRIX.values()
            for variant in variants
        }
        self.assertEqual(len(expected_variants), 24)
        self.assertSetEqual(
            set(SIA4010_TEST_VARIANT_REQUIREMENTS),
            expected_variants,
        )

    def test_model_data_presence_does_not_bypass_exact_identifiers(self):
        room = self.make_fully_populated_room()

        for class_name, expected_variants in EXPECTED_CLASS_TEST_MATRIX.items():
            with self.subTest(validation_class=class_name):
                checker = self.make_checker()
                payload = checker.resolve_class_readiness(
                    f" {class_name.lower()} ",
                    [room],
                )

                self.assertEqual(payload["validation_class"], class_name)
                self.assertEqual(payload["required_variants"], expected_variants)
                self.assertEqual(
                    [row["variant"] for row in payload["variant_rows"]],
                    expected_variants,
                )
                identifier_variants = [
                    row for row in payload["variant_rows"]
                    if row["system_identifiers"]
                ]
                self.assertTrue(identifier_variants)
                self.assertTrue(payload["blocking_variants"])
                self.assertEqual(
                    payload["evidence_status"],
                    "READY_FOR_OFFICIAL_REVIEW",
                )
                self.assertEqual(
                    payload["official_status"],
                    "EVIDENCE_INCOMPLETE",
                )
                for row in payload["variant_rows"]:
                    self.assertEqual(
                        row["present_requirements"],
                        row["model_requirements"],
                    )
                    self.assertEqual(row["missing_requirements"], [])
                    if row["mismatching_identifiers"]:
                        self.assertNotEqual(row["ve_status"], "READY")
                self.assert_no_official_verdict(payload)
                checker._scan_sia4010_evidence.assert_called_once_with()
                checker._summarize_evidence.assert_called_once_with({"files": []})

    def test_resolve_class_readiness_with_all_model_requirements_missing(self):
        for class_name, expected_variants in EXPECTED_CLASS_TEST_MATRIX.items():
            with self.subTest(validation_class=class_name):
                checker = self.make_checker()
                payload = checker.resolve_class_readiness(class_name, [])

                self.assertEqual(payload["required_variants"], expected_variants)
                self.assertEqual(payload["blocking_variants"], expected_variants)
                self.assertEqual(payload["overall_ve_readiness_ratio"], 0.0)
                self.assertEqual(
                    payload["evidence_status"],
                    "READY_FOR_OFFICIAL_REVIEW",
                )
                self.assertEqual(
                    payload["official_status"],
                    "EVIDENCE_INCOMPLETE",
                )
                for row in payload["variant_rows"]:
                    self.assertEqual(row["ve_status"], "MISSING")
                    self.assertEqual(row["present_requirements"], [])
                    self.assertEqual(
                        row["missing_requirements"],
                        row["model_requirements"],
                    )
                    self.assertEqual(row["readiness_ratio"], 0.0)
                self.assert_no_official_verdict(payload)

    def test_generic_official_rows_cannot_validate_full_class_variants(self):
        """Require exact 2B, 3A-3L and 5A-5D result identifiers for class 4B."""
        checker = SIA4010Checker.__new__(SIA4010Checker)
        generic_rows = {
            f"test_{number}": [{"test_id": f"test_{number}", "row_status": "OFFICIAL_PASS"}]
            for number in range(1, 8)
        }
        generic_summary = {
            "status": "READY_FOR_OFFICIAL_REVIEW",
            "validation_class": "4B",
            "missing_items": [],
            "official_test_result_summary": {
                "recorded_pass_by_test": generic_rows,
                "failed_by_test": {},
            },
        }

        generic_tests = checker._run_sia4010_tests(generic_summary)
        generic_classes = checker._evaluate_validation_classes(
            generic_tests,
            generic_summary,
        )

        self.assertNotEqual(generic_tests["test_2"]["status"], "VALIDATED")
        self.assertNotEqual(generic_tests["test_3"]["status"], "VALIDATED")
        self.assertNotEqual(generic_tests["test_5"]["status"], "VALIDATED")
        self.assertEqual(
            generic_classes["4B"]["class_status"],
            "READY_FOR_OFFICIAL_REVIEW",
        )

        exact_rows = {
            variant: [{"test_id": variant, "row_status": "OFFICIAL_PASS"}]
            for variant in SIA4010_CLASS_TEST_MATRIX["4B"]
        }
        exact_summary = {
            **generic_summary,
            "official_test_result_summary": {
                "recorded_pass_by_test": exact_rows,
                "failed_by_test": {},
            },
        }
        exact_tests = checker._run_sia4010_tests(exact_summary)
        exact_classes = checker._evaluate_validation_classes(
            exact_tests,
            exact_summary,
        )

        self.assertTrue(
            all(
                result["status"] == "OFFICIAL_RESULTS_RECORDED"
                for result in exact_tests.values()
            )
        )
        self.assertEqual(
            exact_classes["4B"]["class_status"],
            "OFFICIAL_RESULTS_RECORDED",
        )

    def test_variant_identifiers_reject_mutually_exclusive_test_2_controls(self):
        """Ready only the lamellae variant matching the explicit control value."""
        checker = self.make_checker()
        room = RoomData(
            id="room-1",
            surfaces=[SimpleNamespace(is_external=True, u_value=0.25)],
            openings=[SimpleNamespace(
                is_external=True,
                opening_type="window",
                g_value_bs_en_410=0.5,
                shading_type="lamellae",
                shading_control="1",
            )],
            window_operable=True,
        )

        payload = checker.resolve_class_readiness("1B", [room])
        rows = {row["variant"]: row for row in payload["variant_rows"]}

        self.assertEqual(rows["test_2B"]["mismatching_identifiers"], [])
        self.assertEqual(rows["test_2B"]["ve_status"], "READY")
        self.assertIn("SHADING_CONTROL_VARIANT", rows["test_2C"]["mismatching_identifiers"])
        self.assertIn("SHADING_CONTROL_VARIANT", rows["test_2D"]["mismatching_identifiers"])

    def test_test_id_normalization_preserves_exact_variants(self):
        """Normalize spelling while keeping reduced and full variants distinct."""
        self.assertEqual(SIA4010Checker._normalize_test_id("Test 2A"), "test_2A")
        self.assertEqual(SIA4010Checker._normalize_test_id("test-2B"), "test_2B")
        self.assertEqual(SIA4010Checker._normalize_test_id("test-2C"), "test_2C")
        self.assertEqual(SIA4010Checker._normalize_test_id("test-2D"), "test_2D")
        self.assertEqual(SIA4010Checker._normalize_test_id("3L"), "test_3L")
        self.assertNotEqual(
            SIA4010Checker._normalize_test_id("Test 2A"),
            SIA4010Checker._normalize_test_id("Test 2B"),
        )


class SIA4010WorkbookAdapterTests(unittest.TestCase):
    """Keep all workbook integrations explicit until official files exist."""

    def test_transfer_adapters_raise_with_test_specific_workbook_pattern(self):
        for test_number in range(1, 8):
            with self.subTest(test_number=test_number):
                adapter = getattr(
                    sia4010_test_adapters,
                    f"transfer_test_{test_number}_results",
                )
                with self.assertRaises(NotImplementedError) as raised:
                    adapter({}, evidence_dir=Path("unused-evidence-dir"))

                message = str(raised.exception)
                self.assertIn(
                    "sia4010_evidence/"
                    f"SIA4010_official_evaluation_workbook_test_{test_number}_*.xlsx",
                    message,
                )
                self.assertIn(".xlsm", message)


if __name__ == "__main__":
    unittest.main()
