"""Tests for the fail-closed, read-only Test 2A runtime capability probe."""

from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import json

from swiss_sia.reference_model.sia4010 import test2a_runtime_capability as probe


WORK_ROOT = (
    Path(__file__).resolve().parents[1]
    / ".codex_tmp"
    / "test2a_runtime_capability"
)
WORK_ROOT.mkdir(parents=True, exist_ok=True)


class _Profile:
    def __init__(self, reference="OFFICE"):
        self.reference = reference

    @staticmethod
    def get_data():
        return [[0.0, 0.0, "-"], [24.0, 0.0, "-"]]

    @staticmethod
    def is_weekly():
        return False

    @staticmethod
    def is_yearly():
        return False

    @staticmethod
    def is_compact():
        return False

    @staticmethod
    def is_freeform():
        return False

    @staticmethod
    def is_modulating():
        return True


class _Construction:
    def __init__(self, properties):
        self._properties = properties

    def get_properties(self):
        return dict(self._properties)

    def set_properties(self, _properties):
        raise AssertionError("read-only probe must not call set_properties")


class _CdbProject:
    def __init__(self, properties):
        self._construction = _Construction(properties)

    @staticmethod
    def get_construction_ids(_construction_class):
        return ["GLZ-1"]

    def get_construction(self, *_arguments):
        return self._construction


class _Opening:
    id = "WIN-1"

    def assign_construction(self, _value):
        raise AssertionError("read-only probe must not assign constructions")


class _Surface:
    id = "SURF-1"

    @staticmethod
    def get_openings():
        return [_Opening()]


class _Body:
    name = "ROOM-1"

    @staticmethod
    def get_surfaces():
        return [_Surface()]


class _Model:
    @staticmethod
    def get_bodies(selected_only):
        if selected_only:
            raise AssertionError("probe must request the whole read-only model")
        return [_Body()]


class _Project:
    def __init__(self, path):
        self.path = str(path)
        self.name = "TEST2A_PROBE"
        self.models = [_Model()]

    @staticmethod
    def profiles():
        return ({"DAY_1": _Profile()}, {})

    @staticmethod
    def create_profile(*_arguments):
        raise AssertionError("read-only probe must not create profiles")

    @staticmethod
    def save_profiles():
        raise AssertionError("read-only probe must not save profiles")

    @staticmethod
    def get_version():
        return "2025.2-test"


def _iesve(properties):
    cdb = _CdbProject(properties)

    class _Database:
        @staticmethod
        def get_projects():
            return {0: [cdb]}

    class _DatabaseType:
        @staticmethod
        def get_current_database():
            return _Database()

    construction_class = SimpleNamespace(glazed="glazed")
    cdb_project_type = SimpleNamespace(
        construction_class=construction_class
    )
    return SimpleNamespace(
        VECdbDatabase=_DatabaseType,
        VECdbProject=cdb_project_type,
    )


def _readiness(ready):
    return SimpleNamespace(
        ready_for_binding=ready,
        status="READY_FOR_BINDING" if ready else "MISSING",
        to_dict=lambda: {
            "status": "READY_FOR_BINDING" if ready else "MISSING"
        },
    )


def _bindings(with_profile_graph=True):
    graph = None
    if with_profile_graph:
        graph = SimpleNamespace(
            required_profile_types=("daily", "weekly", "yearly"),
            outputs=(
                ("occupancy_profile", "occupancy_yearly"),
                ("equipment_profile", "equipment_yearly"),
                ("lighting_profile", "lighting_yearly"),
            ),
        )
    return SimpleNamespace(
        office_profiles=SimpleNamespace(ve_profile_graph=graph)
    )


class Test2ARuntimeCapabilityTests(TestCase):
    """Prove that the probe only promotes complete read-only evidence."""

    def test_complete_runtime_evidence_is_ready_for_disposable_probe(self):
        properties = {
            field: 1 for field in probe.REQUIRED_EXTERNAL_SHADE_FIELDS
        }
        project = WORK_ROOT / "complete"
        project.mkdir(parents=True, exist_ok=True)
        with patch.object(
            probe,
            "external_input_readiness",
            return_value=_readiness(True),
        ), patch.object(
            probe,
            "load_test2a_external_bindings",
            return_value=_bindings(),
        ):
            payload = probe.build_test2a_runtime_capability_report(
                _iesve(properties),
                _Project(project),
            )

        self.assertEqual(
            payload["status"],
            "READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION",
        )
        self.assertEqual(payload["technical_blockers"], [])
        self.assertFalse(payload["mutation_performed"])
        self.assertFalse(payload["mutation_authorized"])
        self.assertEqual(len(payload["profile_api"]["profiles"]), 1)
        self.assertEqual(len(payload["opening_api"]["openings"]), 1)
        aps_binding = payload["official_shading_control"][
            "aps_diagnostic_binding"
        ]
        self.assertTrue(aps_binding["available"])
        self.assertEqual(aps_binding["bound_count"], 1)
        self.assertEqual(aps_binding["required_count"], 8)
        self.assertFalse(aps_binding["complete"])

    def test_ready_sources_without_native_profile_graph_remain_closed(self):
        properties = {
            field: 1 for field in probe.REQUIRED_EXTERNAL_SHADE_FIELDS
        }
        project = WORK_ROOT / "profile_graph_missing"
        project.mkdir(parents=True, exist_ok=True)
        with patch.object(
            probe,
            "external_input_readiness",
            return_value=_readiness(True),
        ), patch.object(
            probe,
            "load_test2a_external_bindings",
            return_value=_bindings(False),
        ):
            payload = probe.build_test2a_runtime_capability_report(
                _iesve(properties),
                _Project(project),
            )

        self.assertEqual(payload["status"], "NATIVE_PROFILE_GRAPH_REQUIRED")
        self.assertIn(
            "SIA2024_NATIVE_VE_PROFILE_GRAPH_NOT_SUPPLIED",
            payload["technical_blockers"],
        )

    def test_missing_source_and_shading_fields_remain_fail_closed(self):
        project = WORK_ROOT / "missing"
        project.mkdir(parents=True, exist_ok=True)
        with patch.object(
            probe,
            "external_input_readiness",
            return_value=_readiness(False),
        ):
            payload = probe.build_test2a_runtime_capability_report(
                _iesve({"solar_factor": 0.5}),
                _Project(project),
            )

        self.assertEqual(payload["status"], "SOURCE_BINDINGS_REQUIRED")
        self.assertIn(
            "TEST2A_SOURCE_BINDINGS_NOT_READY",
            payload["technical_blockers"],
        )
        self.assertTrue(
            any(
                item.startswith("MISSING_EXTERNAL_SHADE_FIELDS:")
                for item in payload["technical_blockers"]
            )
        )

    def test_report_and_checksum_are_written_without_mutation(self):
        properties = {
            field: 1 for field in probe.REQUIRED_EXTERNAL_SHADE_FIELDS
        }
        project = WORK_ROOT / "write"
        project.mkdir(parents=True, exist_ok=True)
        with patch.object(
            probe,
            "external_input_readiness",
            return_value=_readiness(True),
        ), patch.object(
            probe,
            "load_test2a_external_bindings",
            return_value=_bindings(),
        ):
            output = probe.write_test2a_runtime_capability_report(
                _iesve(properties),
                _Project(project),
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            checksum = output.with_suffix(output.suffix + ".sha256")
            self.assertEqual(
                payload["status"],
                "READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION",
            )
            self.assertTrue(checksum.is_file())
            self.assertIn(output.name, checksum.read_text(encoding="ascii"))
