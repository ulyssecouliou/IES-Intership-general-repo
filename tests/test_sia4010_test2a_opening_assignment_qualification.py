"""Tests for transient, restored Test 2A opening assignment."""

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
from swiss_sia.reference_model.sia4010.test2a_opening_assignment_qualification import (
    MUTATION_SCOPE,
    qualify_test2a_opening_assignment,
)


ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / ".codex_tmp" / "test2a_opening_assignment"


class _Construction:
    def __init__(self, identifier):
        self.id = identifier

    def get_layers(self):
        return [object()]


class _Opening:
    def __init__(self, construction):
        self._construction = construction

    def get_id(self):
        return "OPENING-1"

    def get_construction(self):
        return self._construction

    def get_properties(self):
        return {"type": "Window", "area": 12.0}


class _Body:
    id = "ROOM-1"

    def __init__(self, opening, *, break_restore=False):
        self.opening = opening
        self.break_restore = break_restore

    def get_surfaces(self):
        return [_Surface(self.opening)]

    def assign_construction_to_opening(self, construction, _surface, _opening_id):
        if self.break_restore and construction.id == "ORIGINAL":
            return
        self.opening._construction = construction


class _Surface:
    index = 1

    def __init__(self, opening):
        self.opening = opening

    def get_openings(self):
        return [self.opening]


class _Gateway:
    def __init__(self, project_path, *, break_restore=False):
        self.project_path = project_path
        self.project = SimpleNamespace(path=str(project_path))
        self.original = _Construction("ORIGINAL")
        self.candidate = _Construction("CANDIDATE")
        opening = _Opening(self.original)
        self.body = _Body(opening, break_restore=break_restore)
        self.model = SimpleNamespace(
            get_bodies=lambda _include: [self.body]
        )

    def _get_construction(self, identifier):
        if identifier != "CANDIDATE":
            raise AssertionError(identifier)
        return self.candidate

    @staticmethod
    def _construction_layer_is_resolved(_construction, _layer):
        return True

    @staticmethod
    def _construction_identifier(construction):
        return construction.id


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


class Test2AOpeningAssignmentQualificationTests(unittest.TestCase):
    def setUp(self):
        name = hashlib.sha256(
            self._testMethodName.encode("utf-8")
        ).hexdigest()[:12]
        self.project_path = WORK_ROOT / name
        if self.project_path.exists():
            shutil.rmtree(self.project_path)
        self.project_path.mkdir(parents=True)
        (self.project_path / "sia_model_scenario.json").write_text(
            "{}\n", encoding="utf-8"
        )
        self.project = SimpleNamespace(
            path=str(self.project_path), name="TEST2A_ASSIGNMENT"
        )

    def tearDown(self):
        if self.project_path.exists():
            shutil.rmtree(self.project_path)

    def _write_optical_report(self, *, combined=True):
        path = (
            self.project_path
            / "sia4010_artifacts"
            / "diagnostics"
            / "sia2a_2e1_optical_setter_test.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "status": "PASS",
                    "fixed_closed_storage_qualified": True,
                    "combined_threshold_optical_storage_qualified": combined,
                    "compliance_claim_allowed": False,
                    "setter_result": {"construction_id": "CANDIDATE"},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        path.with_suffix(path.suffix + ".sha256").write_text(
            "{}  {}\n".format(digest, path.name), encoding="ascii"
        )

    def _run(self, gateway):
        with mock.patch(
            "swiss_sia.reference_model.sia4010."
            "test2a_opening_assignment_qualification.ModelScenario.load",
            return_value=_scenario(),
        ), mock.patch(
            "swiss_sia.reference_model.sia4010."
            "test2a_opening_assignment_qualification.IesVeGateway",
            return_value=gateway,
        ):
            return qualify_test2a_opening_assignment(object(), self.project)

    def test_assignment_is_read_back_and_original_is_restored(self):
        self._write_optical_report()
        gateway = _Gateway(self.project_path)
        report_path = self._run(gateway)
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["mutation_scope"], MUTATION_SCOPE)
        self.assertTrue(payload["candidate_assignment_readback_verified"])
        self.assertTrue(payload["original_assignment_restored"])
        self.assertFalse(payload["opening_assignment_persisted"])
        self.assertEqual(
            gateway.body.opening.get_construction().id, "ORIGINAL"
        )
        self.assertFalse(payload["compliance_claim_allowed"])
        self.assertTrue(
            report_path.with_suffix(report_path.suffix + ".sha256").is_file()
        )

    def test_non_combined_optical_probe_is_rejected_before_assignment(self):
        self._write_optical_report(combined=False)
        gateway = _Gateway(self.project_path)
        with self.assertRaisesRegex(ConfigurationError, "combined"):
            self._run(gateway)
        self.assertEqual(
            gateway.body.opening.get_construction().id, "ORIGINAL"
        )

    def test_failed_restoration_is_fail_closed(self):
        self._write_optical_report()
        gateway = _Gateway(self.project_path, break_restore=True)
        with self.assertRaisesRegex(VeMutationError, "not restored"):
            self._run(gateway)
        reports = list(
            (self.project_path / "sia4010_artifacts" / "diagnostics").glob(
                "sia2a_opening_assignment_*.json"
            )
        )
        self.assertEqual(len(reports), 1)
        payload = json.loads(reports[0].read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "FAIL")
        self.assertTrue(payload["opening_assignment_persisted"])


if __name__ == "__main__":
    unittest.main()

