"""Tests for the guarded Test 2A external-shade CDB setter probe."""

import hashlib
import json
import shutil
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from swiss_sia.reference_model.exceptions import (
    ConfigurationError,
    VeMutationError,
)
from swiss_sia.reference_model.sia4010.test2a_shading_qualification import (
    FIXED_CLOSED_PROBE_MARKER,
    PROBE_MARKER,
    qualify_test2a_2e1_optical_setters,
    qualify_test2a_shading_setters,
)


ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / ".codex_tmp" / "test2a_shading_qualification"


class _Construction:
    def __init__(
        self,
        identifier,
        *,
        marker="",
        broken_readback=False,
        broken_optical_readback=False,
    ):
        self.id = identifier
        self._broken_readback = broken_readback
        self._broken_optical_readback = broken_optical_readback
        self._properties = {
            "description": marker,
            "external_shade_active": False,
            "external_shade_profile": "NONE",
            "external_shade_radiation_to_lower": 0.0,
            "external_shade_radiation_to_raise": 0.0,
            "external_shade_transmittance_0": 0.0,
            "external_shade_solar_reflectance": 0.1,
            "external_shade_visible_reflectance": 0.1,
        }
        self._layers = [object()]

    def set_const_class(self, value):
        self.construction_class = value

    def get_properties(self):
        return dict(self._properties)

    def set_properties(self, values):
        for key, value in values.items():
            if (
                self._broken_readback
                and key == "external_shade_radiation_to_lower"
            ):
                continue
            if (
                self._broken_optical_readback
                and key == "external_shade_transmittance_0"
            ):
                continue
            self._properties[key] = value

    def get_layers(self):
        return list(self._layers)


class _CdbProject:
    def __init__(
        self,
        *,
        existing_marker=False,
        broken_readback=False,
        broken_optical_readback=False,
    ):
        self._broken_readback = broken_readback
        self._broken_optical_readback = broken_optical_readback
        self._constructions = {
            "BASE": _Construction(
                "BASE",
                marker=PROBE_MARKER if existing_marker else "",
            )
        }

    def get_construction_ids(self, _construction_class):
        return list(self._constructions)

    def get_construction(self, identifier, *_arguments):
        return self._constructions.get(str(identifier))

    def create_construction(self, _category):
        identifier = "PROBE-{}".format(len(self._constructions))
        construction = _Construction(
            identifier,
            broken_readback=self._broken_readback,
            broken_optical_readback=self._broken_optical_readback,
        )
        self._constructions[identifier] = construction
        return construction


def _iesve(cdb):
    class _Database:
        @staticmethod
        def get_projects():
            return {0: [cdb]}

    class _DatabaseType:
        @staticmethod
        def get_current_database():
            return _Database()

    return SimpleNamespace(
        VECdbDatabase=_DatabaseType,
        VECdbProject=SimpleNamespace(
            construction_class=SimpleNamespace(glazed="glazed"),
            element_categories=SimpleNamespace(ext_glazing="ext_glazing"),
        ),
    )


def _scenario():
    return SimpleNamespace(
        is_official=True,
        variant="test_2A",
        case_id="2A",
        to_dict=lambda: {
            "profile": "SIA4010_OFFICIAL",
            "variant": "test_2A",
            "case_id": "2A",
        },
    )


class Test2AShadingQualificationTests(unittest.TestCase):
    """Only the one-object setter scope can receive a PASS."""

    def setUp(self):
        self.project = WORK_ROOT / hashlib.sha256(
            self._testMethodName.encode("utf-8")
        ).hexdigest()[:12]
        if self.project.exists():
            shutil.rmtree(self.project)
        self.project.mkdir(parents=True)
        (self.project / "sia_model_scenario.json").write_text(
            "{}\n", encoding="utf-8"
        )
        self.ve_project = SimpleNamespace(
            path=str(self.project),
            name="TEST2A_SHADE_PROBE",
        )

    def tearDown(self):
        if self.project.exists():
            shutil.rmtree(self.project)

    def _run(self, cdb):
        bindings = SimpleNamespace(
            evidence_sha256=(
                ("iso52016_2017_chapter7_test_cell", "1" * 64),
                ("sia2028_dry_normal_zurich_kloten", "2" * 64),
                ("sia2024_office_3_1_standard_profiles", "3" * 64),
            )
        )
        with mock.patch(
            "swiss_sia.reference_model.sia4010."
            "test2a_shading_qualification.ModelScenario.load",
            return_value=_scenario(),
        ), mock.patch(
            "swiss_sia.reference_model.sia4010."
            "test2a_shading_qualification.external_input_readiness",
            return_value=SimpleNamespace(ready_for_binding=True),
        ), mock.patch(
            "swiss_sia.reference_model.sia4010."
            "test2a_shading_qualification.load_test2a_external_bindings",
            return_value=bindings,
        ):
            return qualify_test2a_shading_setters(
                _iesve(cdb),
                self.ve_project,
                repository_root=ROOT,
            )

    def _run_optical(self, cdb):
        bindings = SimpleNamespace(
            evidence_sha256=(
                ("iso52016_2017_chapter7_test_cell", "1" * 64),
                ("sia2028_dry_normal_zurich_kloten", "2" * 64),
                ("sia2024_office_3_1_standard_profiles", "3" * 64),
            )
        )
        with mock.patch(
            "swiss_sia.reference_model.sia4010."
            "test2a_shading_qualification.ModelScenario.load",
            return_value=_scenario(),
        ), mock.patch(
            "swiss_sia.reference_model.sia4010."
            "test2a_shading_qualification.external_input_readiness",
            return_value=SimpleNamespace(ready_for_binding=True),
        ), mock.patch(
            "swiss_sia.reference_model.sia4010."
            "test2a_shading_qualification.load_test2a_external_bindings",
            return_value=bindings,
        ):
            return qualify_test2a_2e1_optical_setters(
                _iesve(cdb),
                self.ve_project,
                repository_root=ROOT,
            )

    def test_pass_is_strictly_limited_to_cdb_setter_storage(self):
        report_path = self._run(_CdbProject())
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "PASS")
        self.assertTrue(payload["cdb_setter_qualified"])
        self.assertFalse(payload["dynamic_equivalence_qualified"])
        self.assertFalse(payload["full_test2a_mutation_authorized"])
        self.assertFalse(payload["optical_mapping_performed"])
        self.assertFalse(payload["opening_assignment_performed"])
        self.assertEqual(
            payload["setter_result"]["written_properties"][
                "external_shade_radiation_to_lower"
            ],
            150.0,
        )
        self.assertTrue(
            report_path.with_suffix(report_path.suffix + ".sha256").is_file()
        )

    def test_existing_probe_fails_before_second_creation(self):
        cdb = _CdbProject(existing_marker=True)
        with self.assertRaisesRegex(VeMutationError, "already exists"):
            self._run(cdb)
        self.assertEqual(list(cdb._constructions), ["BASE"])

    def test_readback_mismatch_remains_a_failed_qualification(self):
        cdb = _CdbProject(broken_readback=True)
        with self.assertRaisesRegex(VeMutationError, "read-back mismatch"):
            self._run(cdb)
        reports = list(
            (self.project / "sia4010_artifacts" / "diagnostics").glob(
                "sia2a_external_shade_setter_*.json"
            )
        )
        self.assertEqual(len(reports), 1)
        payload = json.loads(reports[0].read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "FAIL")
        self.assertFalse(payload["cdb_setter_qualified"])

    def test_temporary_project_is_rejected_before_mutation(self):
        with mock.patch(
            "swiss_sia.reference_model.sia4010."
            "test2a_shading_qualification.is_temporary_ve_project",
            return_value=True,
        ):
            with self.assertRaisesRegex(ConfigurationError, "temporary VEPROJ"):
                qualify_test2a_shading_setters(
                    _iesve(_CdbProject()),
                    self.ve_project,
                    repository_root=ROOT,
                )

    def test_2e1_optical_storage_pass_keeps_output_equivalence_blocked(self):
        cdb = _CdbProject()
        self._run(cdb)
        report_path = self._run_optical(cdb)
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "PASS")
        self.assertTrue(payload["fixed_closed_storage_qualified"])
        self.assertFalse(payload["fixed_closed_optical_mapping_qualified"])
        self.assertFalse(
            payload["diagnostic_candidate_generation_authorized"]
        )
        written = payload["setter_result"]["written_properties"]
        self.assertEqual(written["external_shade_profile"], "ON")
        self.assertAlmostEqual(
            written["external_shade_transmittance_0"],
            0.04,
        )
        self.assertAlmostEqual(
            written["external_shade_solar_reflectance"],
            0.49,
        )
        self.assertAlmostEqual(
            written["external_shade_visible_reflectance"],
            0.496,
        )
        self.assertEqual(
            cdb._constructions[
                payload["setter_result"]["construction_id"]
            ].get_properties()["description"],
            FIXED_CLOSED_PROBE_MARKER,
        )
        self.assertTrue(
            report_path.with_suffix(
                report_path.suffix + ".sha256"
            ).is_file()
        )

    def test_2e1_optical_probe_requires_threshold_setter_pass(self):
        cdb = _CdbProject()
        with self.assertRaisesRegex(
            ConfigurationError,
            "exactly one prior threshold",
        ):
            self._run_optical(cdb)
        self.assertEqual(list(cdb._constructions), ["BASE"])

    def test_2e1_optical_readback_mismatch_is_fail_closed(self):
        cdb = _CdbProject(broken_optical_readback=True)
        self._run(cdb)
        with self.assertRaisesRegex(VeMutationError, "read-back mismatch"):
            self._run_optical(cdb)
        reports = list(
            (self.project / "sia4010_artifacts" / "diagnostics").glob(
                "sia2a_2e1_optical_setter_*.json"
            )
        )
        self.assertEqual(len(reports), 1)
        payload = json.loads(reports[0].read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "FAIL")
        self.assertFalse(payload["fixed_closed_storage_qualified"])


if __name__ == "__main__":
    unittest.main()
