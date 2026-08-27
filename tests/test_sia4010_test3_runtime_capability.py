"""Tests for the read-only SIA 4010 Test 3 VE capability probe."""

import hashlib
import json
import shutil
import unittest
from pathlib import Path
from unittest import mock

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.model_scenario import (
    ModelScenario,
    ScenarioFiles,
    official_features,
)
from swiss_sia.reference_model.sia4010.test3_runtime_capability import (
    build_test3_runtime_capability_report,
    write_test3_runtime_capability_report,
)

ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / ".codex_tmp" / "test3_runtime_capability"


class LightingGain:
    """Lighting proxy exposing the observed gain read/write fields."""

    id = 7

    def get(self):
        return {
            "name": "CONTROLLED_LIGHTING",
            "type_str": "Lighting",
            "variation_profile": "YEAR_PROFILE",
            "dimming_profile": "DIM_PROFILE",
            "max_illuminance": 500.0,
            "installed_power_density": 12.5,
            "max_power_consumption": 12.5,
        }

    def set(self, _payload):
        raise AssertionError("The read-only probe must never call set()")


class _Template:
    name = "CONTROLLED_TEMPLATE"

    def get_casual_gains(self):
        return [LightingGain()]


class _RoomData:
    daylight_sensor = object()

    def get_internal_gains(self):
        return [LightingGain()]


class _Body:
    name = "CONTROLLED_ROOM"

    def get_room_data(self):
        return _RoomData()


class _Model:
    def get_bodies(self, include_voids):
        if include_voids is not False:
            raise AssertionError("Unexpected body traversal argument")
        return [_Body()]


class _Project:
    name = "CONTROLLED_TEST3"

    def __init__(self, path):
        self.path = str(path)
        self.models = [_Model()]

    def get_version(self):
        return "2025.2"

    def casual_gains(self):
        return [LightingGain()]

    def create_casual_gain(self):
        raise AssertionError("The read-only probe must never create a gain")

    def thermal_templates(self, assigned=True, allow_ncm=False):
        if assigned is not False or allow_ncm is not False:
            raise AssertionError("Unexpected thermal template arguments")
        return {5: _Template()}


class _Iesve:
    DaylightSensor = type("DaylightSensor", (), {})
    LightingGain = LightingGain


class _Readiness:
    def __init__(self, ready):
        self.ready_for_binding = ready
        self.status = "READY_FOR_BINDING" if ready else "BLOCKED"

    def to_dict(self):
        return {
            "status": self.status,
            "ready_for_binding": self.ready_for_binding,
        }


class Test3RuntimeCapabilityTests(unittest.TestCase):
    """The probe inventories all variants and never authorizes mutation."""

    def setUp(self):
        self.project_path = WORK_ROOT / self._testMethodName
        if self.project_path.exists():
            shutil.rmtree(self.project_path)
        self.project_path.mkdir(parents=True)
        self.project = _Project(self.project_path)
        self._write_scenario("test_3A", "3A")

    def tearDown(self):
        if self.project_path.exists():
            shutil.rmtree(self.project_path)

    def _write_scenario(self, variant, case_id):
        target_class = "2B"
        scenario = ModelScenario(
            scenario_id="SIA4010_{}_{}".format(variant.upper(), case_id),
            profile="SIA4010_OFFICIAL",
            target_class=target_class,
            variant=variant,
            case_id=case_id,
            features=official_features(variant, case_id),
            files=ScenarioFiles("case.json", "config.json", "assets.json"),
            execution_mode="PREPARE_ONLY",
        )
        (self.project_path / "sia_model_scenario.json").write_text(
            json.dumps(scenario.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )

    @mock.patch(
        "swiss_sia.reference_model.sia4010.test3_runtime_capability."
        "external_input_readiness",
        return_value=_Readiness(True),
    )
    def test_complete_read_only_inventory_covers_twelve_variants(
        self,
        _readiness,
    ):
        payload = build_test3_runtime_capability_report(
            _Iesve,
            self.project,
            ROOT,
        )
        self.assertEqual(
            payload["status"],
            "READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION",
        )
        self.assertEqual(len(payload["variant_capability_matrix"]), 12)
        self.assertEqual(
            {row["case_id"] for row in payload["variant_capability_matrix"]},
            {"3{}".format(letter) for letter in "ABCDEFGHIJKL"},
        )
        self.assertEqual(payload["missing_lighting_fields"], [])
        self.assertTrue(payload["sensor_related_members"])
        self.assertIn(
            "TEST3_APS_BINDINGS_NOT_QUALIFIED",
            payload["technical_blockers"],
        )
        self.assertEqual(payload["setter_qualification_blockers"], [])
        self.assertFalse(payload["mutation_performed"])
        self.assertFalse(payload["mutation_authorized"])

    @mock.patch(
        "swiss_sia.reference_model.sia4010.test3_runtime_capability."
        "external_input_readiness",
        return_value=_Readiness(False),
    )
    def test_missing_source_bindings_fail_closed(self, _readiness):
        payload = build_test3_runtime_capability_report(
            _Iesve,
            self.project,
            ROOT,
        )
        self.assertEqual(payload["status"], "SOURCE_BINDINGS_REQUIRED")
        selected = payload["selected_variant_capability"]
        self.assertIn(
            "TEST3_EXTERNAL_SOURCE_BINDINGS_NOT_READY",
            selected["technical_blockers"],
        )

    @mock.patch(
        "swiss_sia.reference_model.sia4010.test3_runtime_capability."
        "external_input_readiness"
    )
    def test_3k_3l_source_readiness_is_audited_independently(
        self,
        readiness,
    ):
        readiness.side_effect = lambda _path, _variant, case_id: _Readiness(
            case_id not in {"3K", "3L"}
        )
        payload = build_test3_runtime_capability_report(
            _Iesve,
            self.project,
            ROOT,
        )
        self.assertEqual(
            payload["status"],
            "READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION",
        )
        by_case = {row["case_id"]: row for row in payload["variant_capability_matrix"]}
        self.assertNotIn(
            "TEST3_3K_3L_DEVICE_IDENTITY_CLARIFICATION_REQUIRED",
            by_case["3A"]["technical_blockers"],
        )
        for case_id in ("3K", "3L"):
            self.assertIn(
                "TEST3_3K_3L_DEVICE_IDENTITY_CLARIFICATION_REQUIRED",
                by_case[case_id]["technical_blockers"],
            )

    def test_missing_exact_scenario_is_rejected(self):
        (self.project_path / "sia_model_scenario.json").unlink()
        with self.assertRaisesRegex(
            ConfigurationError,
            "Prepare one official Test 3",
        ):
            build_test3_runtime_capability_report(
                _Iesve,
                self.project,
                ROOT,
            )

    @mock.patch(
        "swiss_sia.reference_model.sia4010.test3_runtime_capability."
        "external_input_readiness",
        return_value=_Readiness(True),
    )
    def test_writer_emits_checksum_sidecar(self, _readiness):
        report = write_test3_runtime_capability_report(
            _Iesve,
            self.project,
            ROOT,
        )
        checksum = report.with_suffix(report.suffix + ".sha256")
        self.assertTrue(checksum.is_file())
        expected = checksum.read_text(encoding="ascii").split()[0]
        actual = hashlib.sha256(report.read_bytes()).hexdigest()
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
