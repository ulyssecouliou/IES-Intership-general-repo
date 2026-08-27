"""Tests for the SIA 4010 required-validation-class derivation."""

import unittest

from swiss_sia.config import SIA4010_TEST_CLASS_COVERAGE
from swiss_sia.model_analyzer import OpeningData, RoomData
from swiss_sia.validation_class_scope import (
    ABSENT,
    PRESENT,
    UNDETERMINED,
    derive_validation_class_scope,
)


def _opening(**kwargs):
    """Build an external opening with sensible defaults for the detectors."""
    payload = {"id": "w1", "name": "W1", "area": 1.0, "is_external": True}
    payload.update(kwargs)
    return OpeningData(**payload)


def _room(**kwargs):
    """Build a room with the minimum fields the detectors read."""
    payload = {"id": "r1", "name": "Room 1"}
    payload.update(kwargs)
    return RoomData(**payload)


def _state(scope, feature_id):
    """Return the detected state of one feature."""
    return next(f.state for f in scope.findings if f.feature_id == feature_id)


class NoModelTests(unittest.TestCase):
    def test_no_rooms_is_not_checkable(self):
        scope = derive_validation_class_scope([])
        self.assertEqual(scope.status, "NOT_CHECKABLE")
        self.assertIsNone(scope.required_class)
        self.assertEqual(scope.required_tests, ())


class EnvelopeOnlyTests(unittest.TestCase):
    """A bare envelope model with no detected devices relies on Test 1 only."""

    def setUp(self):
        # Natural ventilation only: no installation type, no fan, no rate.
        self.scope = derive_validation_class_scope(
            [
                _room(
                    openings=[_opening(shading_type="")],
                    internal_gains={"lighting": 8.0},
                    heat_recovery_type="",
                    hvac_systems=[{"id": "s1"}],
                )
            ]
        )

    def test_test_1_is_always_required(self):
        self.assertIn("test_1", self.scope.required_tests)

    def test_absent_devices_do_not_add_tests(self):
        self.assertEqual(_state(self.scope, "solar_protection"), ABSENT)
        self.assertEqual(_state(self.scope, "lighting_control"), ABSENT)
        self.assertEqual(_state(self.scope, "heat_recovery"), ABSENT)
        self.assertNotIn("test_2", self.scope.required_tests)
        self.assertNotIn("test_3", self.scope.required_tests)

    def test_required_class_is_the_least_demanding_covering_test_1(self):
        # Every class covering test_1 is acceptable; the least demanding wins.
        self.assertIn(self.scope.required_class, SIA4010_TEST_CLASS_COVERAGE["test_1"])
        self.assertEqual(self.scope.required_class, "1A")


class MechanicalVentilationTests(unittest.TestCase):
    """A declared ventilation installation pulls the class up to a Test 6 class."""

    def test_monozone_installation_requires_test_6(self):
        scope = derive_validation_class_scope(
            [
                _room(
                    openings=[_opening(shading_type="")],
                    internal_gains={"lighting": 8.0},
                    ventilation_installation_type="monozone",
                    hvac_systems=[{"id": "s1"}],
                )
            ]
        )
        self.assertEqual(_state(scope, "mechanical_ventilation"), PRESENT)
        self.assertIn("test_6", scope.required_tests)
        self.assertIn(scope.required_class, SIA4010_TEST_CLASS_COVERAGE["test_6"])
        self.assertEqual(scope.required_class, "3")


class FeatureDrivenClassTests(unittest.TestCase):
    def test_active_solar_protection_requires_test_2(self):
        scope = derive_validation_class_scope(
            [
                _room(
                    openings=[
                        _opening(
                            shading_type="blind",
                            shading_properties={"external_shade_active": True},
                        )
                    ],
                    internal_gains={"lighting": 8.0},
                    ventilation_installation_type="monozone",
                    hvac_systems=[{"id": "s1"}],
                )
            ]
        )
        self.assertEqual(_state(scope, "solar_protection"), PRESENT)
        self.assertIn("test_2", scope.required_tests)
        # Only classes covering both test_1 and test_2 remain.
        self.assertIn(scope.required_class, SIA4010_TEST_CLASS_COVERAGE["test_2"])

    def test_generation_plant_requires_test_7(self):
        scope = derive_validation_class_scope(
            [
                _room(
                    openings=[_opening(shading_type="")],
                    internal_gains={"lighting": 8.0},
                    ventilation_installation_type="monozone",
                    hvac_systems=[{"id": "s1", "cooling_generator_class": "air_cooled"}],
                )
            ]
        )
        self.assertEqual(_state(scope, "generation_plant"), PRESENT)
        self.assertIn("test_7", scope.required_tests)
        self.assertIn(scope.required_class, SIA4010_TEST_CLASS_COVERAGE["test_7"])

    def test_heat_recovery_requires_test_6(self):
        scope = derive_validation_class_scope(
            [
                _room(
                    openings=[_opening(shading_type="")],
                    internal_gains={"lighting": 8.0},
                    ventilation_installation_type="monozone",
                    heat_recovery_type="thermal_wheel",
                    hvac_systems=[{"id": "s1"}],
                )
            ]
        )
        self.assertEqual(_state(scope, "heat_recovery"), PRESENT)
        self.assertIn("test_6", scope.required_tests)


class ConservativeHandlingTests(unittest.TestCase):
    """An undetermined feature must never be treated as absent."""

    def test_explicitly_inactive_shading_is_absent(self):
        # An explicit zero activation field means inactive product-wide.
        scope = derive_validation_class_scope(
            [
                _room(
                    openings=[
                        _opening(
                            shading_type="blind",
                            shading_properties={"external_shade_active": False},
                        )
                    ],
                    internal_gains={"lighting": 8.0},
                    hvac_systems=[{"id": "s1"}],
                )
            ]
        )
        self.assertEqual(_state(scope, "solar_protection"), ABSENT)
        self.assertNotIn("test_2", scope.required_tests)

    def test_no_external_opening_leaves_shading_undetermined(self):
        scope = derive_validation_class_scope(
            [
                _room(
                    openings=[],
                    internal_gains={"lighting": 8.0},
                    hvac_systems=[{"id": "s1"}],
                )
            ]
        )
        self.assertEqual(_state(scope, "solar_protection"), UNDETERMINED)
        self.assertNotIn("test_2", scope.required_tests)
        self.assertIn("test_2", scope.undetermined_tests)

    def test_conservative_class_covers_undetermined_features(self):
        # No ventilation data at all -> test_6 undetermined, not assumed absent.
        scope = derive_validation_class_scope(
            [
                _room(
                    openings=[_opening(shading_type="")],
                    internal_gains={"lighting": 8.0},
                    hvac_systems=[{"id": "s1"}],
                )
            ]
        )
        self.assertIn("test_6", scope.undetermined_tests)
        self.assertNotIn("test_6", scope.required_tests)
        self.assertIn(scope.conservative_class, SIA4010_TEST_CLASS_COVERAGE["test_6"])
        self.assertNotEqual(scope.required_class, scope.conservative_class)

    def test_missing_lighting_gain_leaves_control_undetermined(self):
        scope = derive_validation_class_scope(
            [
                _room(
                    openings=[_opening(shading_type="")],
                    internal_gains={},
                    ventilation_installation_type="monozone",
                    hvac_systems=[{"id": "s1"}],
                )
            ]
        )
        self.assertEqual(_state(scope, "lighting_control"), UNDETERMINED)
        self.assertIn("test_3", scope.undetermined_tests)

    def test_no_ventilation_data_is_undetermined(self):
        scope = derive_validation_class_scope(
            [
                _room(
                    openings=[_opening(shading_type="")], internal_gains={"lighting": 8.0}
                )
            ]
        )
        self.assertEqual(_state(scope, "mechanical_ventilation"), UNDETERMINED)

    def test_notes_never_claim_the_tool_holds_the_class(self):
        scope = derive_validation_class_scope(
            [_room(openings=[_opening()], internal_gains={"lighting": 8.0})]
        )
        joined = " ".join(scope.notes).lower()
        self.assertIn("does not assert that the tool holds", joined)
        self.assertIn("sub-commission attestation", joined)


class SerializationTests(unittest.TestCase):
    def test_to_dict_is_serializable_and_complete(self):
        scope = derive_validation_class_scope(
            [_room(openings=[_opening()], internal_gains={"lighting": 8.0})]
        )
        payload = scope.to_dict()
        self.assertEqual(
            set(payload),
            {
                "status",
                "required_class",
                "conservative_class",
                "required_tests",
                "undetermined_tests",
                "findings",
                "notes",
            },
        )
        self.assertTrue(payload["findings"])
        self.assertIn("test_family", payload["findings"][0])
        self.assertTrue(payload["findings"][0]["test_scope"])


if __name__ == "__main__":
    unittest.main()
