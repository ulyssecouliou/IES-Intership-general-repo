"""Tests for audit exports, post-import validation, and fail-closed workflow."""

import json
import hashlib
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from swiss_sia.reference_model.compliance_config import build_default_registry
from swiss_sia.reference_model.domain import (
    ConstructionSnapshot,
    MaterialSnapshot,
    ModelSnapshot,
    OpeningSnapshot,
    RoomSnapshot,
    SurfaceSnapshot,
    TemplateSnapshot,
)
from swiss_sia.reference_model.geometry import ReferenceGeometryGenerator
from swiss_sia.reference_model.report_generator import ReportGenerator
from swiss_sia.reference_model.results import AuditEvent, ValidationStatus
from swiss_sia.reference_model.validator import ReferenceModelValidator
from swiss_sia.reference_model.ve_api import VeGateway
from swiss_sia.reference_model.workflow import ReferenceModelWorkflow

TEST_ROOT = Path(__file__).resolve().parents[1]
TEST_OUTPUT_ROOT = TEST_ROOT / ".codex_tmp" / "reference_model_tests"


def _test_dir(name):
    path = TEST_OUTPUT_ROOT / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _source(value):
    return {
        "value": value,
        "source": "Approved unit-test project evidence",
        "source_locator": "TEST-EVIDENCE-001",
    }


def _fully_configured_registry():
    return build_default_registry().with_overrides(
        {
            "external_wall_construction_id": _source("C-WALL"),
            "roof_construction_id": _source("C-ROOF"),
            "ground_floor_construction_id": _source("C-FLOOR"),
            "internal_wall_construction_id": _source("C-PARTITION"),
            "door_construction_id": _source("C-DOOR"),
            "glazing_construction_id": _source("C-GLAZING"),
            "project_external_wall_u_w_m2k": _source(0.18),
            "project_roof_u_w_m2k": _source(0.16),
            "project_ground_floor_u_w_m2k": _source(0.25),
            "project_window_u_w_m2k": _source(1.0),
            "project_glazing_g_value": _source(0.45),
            "project_visible_light_transmittance": _source(0.65),
            "weather_file": _source("approved_weather.fwt"),
            "thermal_template_name": _source("Approved SIA Template"),
            "thermal_template_source_record": _source("sha256:template-test"),
            "hvac_system_id": _source("APSYS-TEST"),
        }
    )


def _valid_snapshot(parameters, geometry, project_path):
    construction_values = {
        "C-WALL": (0.18, {}),
        "C-ROOF": (0.16, {}),
        "C-FLOOR": (0.25, {}),
        "C-PARTITION": (None, {}),
        "C-DOOR": (None, {}),
        "C-GLAZING": (
            1.0,
            {"g_value": 0.45, "visible_light_transmittance": 0.65},
        ),
    }
    constructions = tuple(
        ConstructionSnapshot(
            identifier=identifier,
            reference=identifier,
            category="test",
            layer_count=1,
            material_ids=("MAT-{}".format(identifier),),
            properties=properties,
            u_value_w_m2k=u_value,
            valid=True,
        )
        for identifier, (u_value, properties) in construction_values.items()
    )
    rooms = []
    for space in geometry.spaces:
        surfaces = []
        for surface in geometry.surfaces:
            if space.identifier not in surface.adjacent_space_ids:
                continue
            construction_id = str(parameters.value(surface.construction_parameter))
            openings = tuple(
                OpeningSnapshot(
                    identifier=opening.identifier,
                    opening_type=opening.opening_type.value,
                    area_m2=opening.polygon.area,
                    construction_id=str(
                        parameters.value(opening.construction_parameter)
                    ),
                )
                for opening in surface.openings
            )
            surfaces.append(
                SurfaceSnapshot(
                    identifier=surface.identifier,
                    surface_type=surface.surface_type.value,
                    area_m2=surface.polygon.area,
                    construction_ids=(construction_id,),
                    adjacent_room_ids=surface.adjacent_space_ids,
                    openings=openings,
                )
            )
        rooms.append(
            RoomSnapshot(
                identifier=space.identifier,
                name=space.name,
                area_m2=space.floor_area_m2,
                volume_m3=space.volume_m3,
                thermal_template_name="Approved SIA Template",
                surfaces=tuple(surfaces),
                hvac_system_id="APSYS-TEST",
            )
        )
    template = TemplateSnapshot(
        handle="T-1",
        name="Approved SIA Template",
        standard="generic",
        room_conditions={"heating_setpoint": 20.0},
        system_data={"HVAC_system": "APSYS-TEST"},
        gains=({"type_str": "People"},),
        air_exchanges=({"type_str": "Infiltration"},),
    )
    return ModelSnapshot(
        project_name="Unit Test Project",
        project_path=str(project_path),
        ve_version="2023.test",
        weather_file="approved_weather.fwt",
        weather_readable=True,
        rooms=tuple(rooms),
        constructions=constructions,
        materials=(MaterialSnapshot("MAT", "test", {}, True),),
        templates=(template,),
    )


class _PreflightOnlyGateway(VeGateway):
    def __init__(self, path):
        self._path = Path(path)
        self.mutation_calls = 0

    @property
    def project_path(self):
        return self._path

    @property
    def project_name(self):
        return "Preflight Test"

    def check_capabilities(self):
        self.mutation_calls += 1
        return {}

    def assert_no_existing_generated_rooms(self, expected_names):
        self.mutation_calls += 1

    def import_geometry(self, gbxml_path):
        self.mutation_calls += 1

    def rebuild_adjacencies(self):
        self.mutation_calls += 1

    def assign_constructions(self, expected_geometry, parameters):
        self.mutation_calls += 1

    def assign_thermal_template(self, expected_geometry, parameters):
        self.mutation_calls += 1

    def assign_hvac_if_configured(self, expected_geometry, parameters):
        self.mutation_calls += 1

    def assign_weather(self, weather_file):
        self.mutation_calls += 1

    def snapshot(self, expected_geometry, parameters):
        self.mutation_calls += 1
        raise AssertionError("snapshot must not run during blocked preflight")


class _HappyPathGateway(VeGateway):
    """Records the mutation sequence and returns a valid snapshot."""

    def __init__(self, path):
        self._path = Path(path)
        self.calls = []

    @property
    def project_path(self):
        return self._path

    @property
    def project_name(self):
        return "Happy Path Test"

    def check_capabilities(self):
        self.calls.append("check")
        return {}

    def assert_no_existing_generated_rooms(self, expected_names):
        self.calls.append("no_existing")

    def import_geometry(self, gbxml_path):
        self.calls.append("import")

    def rebuild_adjacencies(self):
        self.calls.append("rebuild")

    def assign_constructions(self, expected_geometry, parameters):
        self.calls.append("assign_constructions")

    def verify_construction_assignments(self, expected_geometry, parameters):
        self.calls.append("verify_constructions")

    def assign_thermal_template(self, expected_geometry, parameters):
        self.calls.append("assign_template")

    def assign_hvac_if_configured(self, expected_geometry, parameters):
        self.calls.append("assign_hvac")

    def assign_weather(self, weather_file):
        self.calls.append("assign_weather")

    def snapshot(self, expected_geometry, parameters):
        self.calls.append("snapshot")
        return _valid_snapshot(parameters, expected_geometry, self._path)


class ReferenceModelReportingAndWorkflowTests(unittest.TestCase):
    def test_post_import_snapshot_can_pass_all_object_controls(self):
        temporary = _test_dir("valid_snapshot")
        parameters = _fully_configured_registry()
        geometry = ReferenceGeometryGenerator(parameters).generate()
        snapshot = _valid_snapshot(parameters, geometry, temporary)
        results = ReferenceModelValidator().validate_model_snapshot(
            snapshot, parameters, geometry
        )
        failures = [result for result in results if result.status == ValidationStatus.FAIL]
        self.assertEqual(failures, [], [(item.control_id, item.message) for item in failures])

    def test_converted_weather_candidate_reports_claim_guardrail(self):
        temporary = _test_dir("converted_weather_claim_guardrail")
        weather = temporary / "GVE_TEST_IESVE_CANDIDATE.epw"
        weather.write_text("test weather evidence\n", encoding="ascii")
        digest = hashlib.sha256(weather.read_bytes()).hexdigest()
        evidence_dir = temporary / "reference_model_artifacts" / "weather"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        audit = evidence_dir / "GVE_TEST_IESVE_DERIVATION.json"
        audit.write_text(
            json.dumps(
                {
                    "status": "READY_FOR_IESVE_READ_ONLY_PROBE",
                    "compliance_claim_allowed": False,
                    "official_sia_weather_identity_confirmed": False,
                    "weather": {"sha256": digest},
                }
            ),
            encoding="utf-8",
        )
        parameters = _fully_configured_registry().with_overrides(
            {"weather_file": _source(str(weather))}
        )
        geometry = ReferenceGeometryGenerator(parameters).generate()
        snapshot = replace(
            _valid_snapshot(parameters, geometry, temporary),
            weather_file=weather.name,
        )
        results = ReferenceModelValidator().validate_model_snapshot(
            snapshot, parameters, geometry
        )
        provenance = next(
            item for item in results if item.control_id == "VE-WEA-002"
        )
        self.assertEqual(provenance.status, ValidationStatus.WARNING)
        self.assertFalse(provenance.evidence["compliance_claim_allowed"])
        self.assertTrue(provenance.evidence["checksum_matches"])

    def test_report_exports_json_csv_and_jsonl(self):
        temporary = _test_dir("report_exports")
        parameters = build_default_registry()
        geometry = ReferenceGeometryGenerator(parameters).generate()
        validations = ReferenceModelValidator().validate_geometry(
            geometry, parameters
        )
        artifacts = ReportGenerator(temporary).generate(
            run_metadata={"mode": "TEST"},
            parameters=parameters,
            validations=validations,
            audit_events=[
                AuditEvent(1, "2026-01-01T00:00:00+00:00", "test", "emit", "PASS")
            ],
            geometry=geometry,
        )
        for path in artifacts.__dict__.values():
            self.assertTrue(Path(path).is_file(), path)
        payload = json.loads(artifacts.report_json.read_text(encoding="utf-8"))
        self.assertEqual(payload["overall_status"], "PASS")
        self.assertTrue(payload["placeholders"])
        self.assertEqual(len(artifacts.audit_jsonl.read_text(encoding="utf-8").splitlines()), 1)

    def test_full_existing_mode_workflow_runs_and_verifies_constructions(self):
        temporary = _test_dir("happy_path_workflow")
        parameters = _fully_configured_registry()
        gateway = _HappyPathGateway(temporary)
        fixed_time = lambda: datetime(2026, 1, 1, tzinfo=timezone.utc)
        outcome = ReferenceModelWorkflow(
            parameters, gateway, now=fixed_time
        ).run()
        self.assertNotEqual(outcome.status, ValidationStatus.FAIL)
        # The full mutation sequence ran, including the post-adjacency guard.
        self.assertIn("verify_constructions", gateway.calls)
        self.assertLess(
            gateway.calls.index("assign_constructions"),
            gateway.calls.index("rebuild"),
        )
        self.assertLess(
            gateway.calls.index("rebuild"),
            gateway.calls.index("verify_constructions"),
        )
        self.assertLess(
            gateway.calls.index("verify_constructions"),
            gateway.calls.index("assign_template"),
        )
        self.assertTrue(outcome.artifacts.report_json.is_file())

    def test_resume_after_import_reuses_rooms_without_duplicate_gate_or_import(self):
        temporary = _test_dir("resume_after_import_workflow")
        parameters = _fully_configured_registry()
        gateway = _HappyPathGateway(temporary)
        fixed_time = lambda: datetime(2026, 1, 1, tzinfo=timezone.utc)

        outcome = ReferenceModelWorkflow(
            parameters, gateway, now=fixed_time
        ).run(resume_after_import=True)

        self.assertNotEqual(outcome.status, ValidationStatus.FAIL)
        self.assertNotIn("no_existing", gateway.calls)
        self.assertNotIn("import", gateway.calls)
        self.assertIn("assign_constructions", gateway.calls)
        self.assertIn("assign_weather", gateway.calls)
        payload = json.loads(outcome.artifacts.report_json.read_text(encoding="utf-8"))
        self.assertEqual(payload["run_metadata"]["mode"], "VE_RESUME_AFTER_IMPORT")

    def test_dry_run_and_resume_are_mutually_exclusive(self):
        temporary = _test_dir("invalid_resume_mode")
        workflow = ReferenceModelWorkflow(
            _fully_configured_registry(), _HappyPathGateway(temporary)
        )

        with self.assertRaises(ValueError):
            workflow.run(dry_run=True, resume_after_import=True)

    def test_unresolved_required_inputs_block_all_ve_calls(self):
        temporary = _test_dir("blocked_workflow")
        gateway = _PreflightOnlyGateway(temporary)
        fixed_time = lambda: datetime(2026, 1, 1, tzinfo=timezone.utc)
        outcome = ReferenceModelWorkflow(
            build_default_registry(), gateway, now=fixed_time
        ).run()
        self.assertEqual(outcome.status, ValidationStatus.FAIL)
        self.assertEqual(gateway.mutation_calls, 0)
        self.assertTrue(outcome.artifacts.report_json.is_file())


if __name__ == "__main__":
    unittest.main()
