"""Tests for the narrow Test 2A base-glazing thermal qualifier."""

import hashlib
import json
import shutil
import unittest
from pathlib import Path
from types import SimpleNamespace

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.model_scenario import (
    ModelScenario,
    ScenarioFiles,
    official_features,
)
from swiss_sia.reference_model.sia4010.test2a_thermal_glazing_qualification import (
    MUTATION_SCOPE,
    qualify_test2a_base_glazing_thermal_storage,
)

ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / ".codex_tmp" / "t2a_thermal"


class _Layer:
    def __init__(self):
        self.resistance = 0.1

    def set_properties(self, values):
        self.resistance = float(values["resistance"])

    def get_properties(self):
        return {"resistance": self.resistance}


class _Construction:
    def __init__(self, layer):
        self.layer = layer

    def get_layers(self):
        return [self.layer]

    def get_u_factor(self, _kind):
        return 1.0 / (0.15 + self.layer.resistance)


class _Gateway:
    construction = None

    def __init__(self, _iesve):
        pass

    def _get_construction(self, identifier):
        if identifier != "EXT_TEST2A":
            raise AssertionError(identifier)
        return self.construction

    def _uvalue_type_iso(self):
        return "ISO"


class Test2AThermalGlazingQualificationTests(unittest.TestCase):
    def setUp(self):
        self.project_path = WORK_ROOT / self._testMethodName
        if self.project_path.exists():
            shutil.rmtree(self.project_path)
        self.project_path.mkdir(parents=True)
        self.project = SimpleNamespace(name="T2A", path=str(self.project_path))
        scenario = ModelScenario(
            scenario_id="t2a",
            profile="SIA4010_OFFICIAL",
            target_class="1A",
            variant="test_2A",
            case_id="2A",
            features=official_features("test_2A", "2A"),
            files=ScenarioFiles("case.json", "config.json", "assets.json"),
            execution_mode="PREPARE_ONLY",
        )
        (self.project_path / "sia_model_scenario.json").write_text(
            json.dumps(scenario.to_dict()) + "\n", encoding="utf-8"
        )
        self.report_dir = self.project_path / "sia4010_artifacts" / "diagnostics"
        self.report_dir.mkdir(parents=True)
        self.optical = self.report_dir / "sia2a_2e1_optical_setter_fixture.json"
        self._write_optical(combined=True)
        _Gateway.construction = _Construction(_Layer())

    def tearDown(self):
        if self.project_path.exists():
            shutil.rmtree(self.project_path)

    def _write_optical(self, combined):
        payload = {
            "status": "PASS",
            "fixed_closed_storage_qualified": True,
            "combined_threshold_optical_storage_qualified": combined,
            "setter_result": {
                "construction_id": "EXT_TEST2A",
                "threshold_and_optical_fields_co_stored": combined,
            },
        }
        self.optical.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        digest = hashlib.sha256(self.optical.read_bytes()).hexdigest()
        self.optical.with_suffix(self.optical.suffix + ".sha256").write_text(
            "{}  {}\n".format(digest, self.optical.name), encoding="ascii"
        )

    def test_calibrates_base_u_without_widening_claim(self):
        report_path = qualify_test2a_base_glazing_thermal_storage(
            object(),
            self.project,
            repository_root=ROOT,
            gateway_factory=_Gateway,
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["mutation_scope"], MUTATION_SCOPE)
        self.assertTrue(report["base_glazing_thermal_storage_qualified"])
        self.assertFalse(report["manufacturer_layer_build_up_qualified"])
        self.assertFalse(report["combined_glazing_awning_u_qualified"])
        self.assertFalse(report["compliance_claim_allowed"])
        self.assertAlmostEqual(
            report["calibration_result"]["verified_iso_u_w_m2k"],
            0.654,
            delta=0.001,
        )
        self.assertTrue(report_path.with_suffix(report_path.suffix + ".sha256").is_file())

    def test_rejects_non_combined_optical_prerequisite_before_mutation(self):
        self._write_optical(combined=False)
        original = _Gateway.construction.layer.resistance
        with self.assertRaisesRegex(ConfigurationError, "combined"):
            qualify_test2a_base_glazing_thermal_storage(
                object(),
                self.project,
                repository_root=ROOT,
                gateway_factory=_Gateway,
            )
        self.assertEqual(_Gateway.construction.layer.resistance, original)


if __name__ == "__main__":
    unittest.main()
