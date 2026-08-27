"""Tests for the getter-only SIA 4010 Tests 4-7 runtime probe."""

import hashlib
import json
import shutil
import unittest
from pathlib import Path
from unittest import mock

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.hvac_plant_runtime_capability import (
    build_hvac_plant_runtime_capability_report,
    write_hvac_plant_runtime_capability_report,
)
from swiss_sia.reference_model.sia4010.model_scenario import (
    ModelScenario,
    ScenarioFiles,
    official_features,
)

ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / ".codex_tmp" / "hvac_plant_runtime_capability"


class _ApacheSystem:
    id = "SYS_1"
    name = "READ_ONLY_SYSTEM"

    def get(self):
        return {"name": self.name, "airflow": 1700.0}

    def set(self, _payload):
        raise AssertionError("The read-only probe must never call set()")


class _RoomData:
    def get_apache_systems(self):
        return {"HVAC_system": "SYS_1"}

    def get_room_conditions(self):
        return {"heating_setpoint": 22.0}

    def set_apache_systems(self, _payload):
        raise AssertionError("The read-only probe must never call a setter")


class _Body:
    name = "ROOM_101"

    def get_room_data(self):
        return _RoomData()


class _Model:
    def get_bodies(self, include_voids):
        if include_voids is not False:
            raise AssertionError("Unexpected body traversal argument")
        return [_Body()]


class _Project:
    name = "CONTROLLED_HVAC_PLANT"

    def __init__(self, path):
        self.path = str(path)
        self.models = [_Model()]

    def get_version(self):
        return "2025.2"

    def apache_systems(self):
        return [_ApacheSystem()]

    def create_apache_system(self):
        raise AssertionError("The read-only probe must never create a system")


class _Iesve:
    ApacheHVACNetwork = type("ApacheHVACNetwork", (), {})
    HeatPump = type("HeatPump", (), {})
    PVSystem = type("PVSystem", (), {})


class _Readiness:
    def __init__(self, ready):
        self.ready_for_binding = ready
        self.status = "READY_FOR_BINDING" if ready else "BLOCKED"

    def to_dict(self):
        return {
            "status": self.status,
            "ready_for_binding": self.ready_for_binding,
        }


class HvacPlantRuntimeCapabilityTests(unittest.TestCase):
    """The probe covers seven exact cases and remains strictly read-only."""

    def setUp(self):
        self.project_path = WORK_ROOT / self._testMethodName
        if self.project_path.exists():
            shutil.rmtree(self.project_path)
        self.project_path.mkdir(parents=True)
        self.project = _Project(self.project_path)
        self._write_scenario("test_4", "4")

    def tearDown(self):
        if self.project_path.exists():
            shutil.rmtree(self.project_path)

    def _write_scenario(self, variant, case_id):
        scenario = ModelScenario(
            scenario_id="SIA4010_{}_{}".format(variant.upper(), case_id),
            profile="SIA4010_OFFICIAL",
            target_class="4A",
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
        "swiss_sia.reference_model.sia4010.hvac_plant_runtime_capability."
        "external_input_readiness",
        return_value=_Readiness(True),
    )
    def test_complete_inventory_audits_all_seven_cases(self, _readiness):
        payload = build_hvac_plant_runtime_capability_report(_Iesve, self.project, ROOT)
        self.assertEqual(
            payload["status"],
            "READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION",
        )
        self.assertEqual(len(payload["case_capability_matrix"]), 7)
        self.assertEqual(
            {row["case_id"] for row in payload["case_capability_matrix"]},
            {"4", "5A", "5B", "5C", "5D", "6", "7"},
        )
        self.assertTrue(payload["observed_capabilities"]["apache_system_collection"])
        self.assertTrue(payload["observed_capabilities"]["room_apache_system_readback"])
        self.assertFalse(payload["mutation_performed"])
        self.assertFalse(payload["mutation_authorized"])
        self.assertIn(
            "APACHEHVAC_TOPOLOGY_SETTERS_NOT_QUALIFIED",
            payload["technical_blockers"],
        )

    @mock.patch(
        "swiss_sia.reference_model.sia4010.hvac_plant_runtime_capability."
        "external_input_readiness",
        return_value=_Readiness(False),
    )
    def test_missing_source_bindings_fail_closed(self, _readiness):
        payload = build_hvac_plant_runtime_capability_report(_Iesve, self.project, ROOT)
        self.assertEqual(payload["status"], "SOURCE_BINDINGS_REQUIRED")
        self.assertIn(
            "TEST4_EXTERNAL_SOURCE_BINDINGS_NOT_READY",
            payload["technical_blockers"],
        )

    def test_wrong_scenario_is_rejected(self):
        self._write_scenario("test_3A", "3A")
        with self.assertRaisesRegex(ConfigurationError, "Test 4"):
            build_hvac_plant_runtime_capability_report(_Iesve, self.project, ROOT)

    @mock.patch(
        "swiss_sia.reference_model.sia4010.hvac_plant_runtime_capability."
        "external_input_readiness",
        return_value=_Readiness(True),
    )
    def test_test7_records_plant_evidence_and_checksum(self, _readiness):
        self._write_scenario("test_7", "7")
        report = write_hvac_plant_runtime_capability_report(_Iesve, self.project, ROOT)
        payload = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(payload["scenario"]["selection"]["case_id"], "7")
        self.assertTrue(payload["observed_capabilities"]["plant_specific_members"])
        checksum = report.with_suffix(report.suffix + ".sha256")
        expected = checksum.read_text(encoding="ascii").split()[0]
        self.assertEqual(expected, hashlib.sha256(report.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
