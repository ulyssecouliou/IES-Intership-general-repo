"""Unit tests for ``ve_mutation_policy_probe``.

The probe is proven with a fake ``iesve`` / project / cdb_project surface so
CI covers the three global status paths (PASS, WARNING, FAIL) without any
VEScripts runtime.
"""

import json
import os
import unittest
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from swiss_sia.reference_model.ve_mutation_policy_probe import (
    ProbeStatus,
    run_probe,
    write_probe_report,
)


def _fully_capable_project():
    """Mirror the shape VE 2025 really exposes, as the 2026-08-12 run showed.

    Two members this fake used to carry do not exist on the real runtime, and
    the fake hid it: there is no ``project.rooms`` -- rooms come from
    ``project.models[0].get_bodies(False)`` -- and ``uvalue_types`` lives on the
    ``VECdbProject`` class, not on a CDB project instance. A fake that is more
    generous than the runtime turns a probe green in CI and red in VE.
    """

    model = SimpleNamespace(get_bodies=lambda assigned_only: [])
    project = SimpleNamespace(
        models=[model],
        save_profiles=lambda: True,
        create_profile=lambda *a, **k: None,
        create_casual_gain=lambda *a, **k: None,
        create_air_exchange=lambda *a, **k: None,
        create_apache_system=lambda *a, **k: None,
        create_thermal_template=lambda *a, **k: None,
    )
    cdb = SimpleNamespace(
        create_material=lambda *a, **k: None,
        create_construction=lambda *a, **k: None,
        get_construction=lambda *a, **k: None,
    )
    iesve = SimpleNamespace(
        VECdbProject=SimpleNamespace(uvalue_types=SimpleNamespace(iso=object())),
        construction_class=SimpleNamespace(none=object()),
        element_categories=SimpleNamespace(),
        material_categories=SimpleNamespace(),
    )
    return iesve, project, cdb


def _fake_clock():
    return lambda: "2026-08-11T10-00-00+00:00"


class VeMutationPolicyProbeTests(unittest.TestCase):

    def test_fully_capable_runtime_reports_pass(self) -> None:
        iesve, project, cdb = _fully_capable_project()
        report = run_probe(iesve, project, cdb, project_id="proj_X", clock=_fake_clock())
        self.assertEqual(report.overall, ProbeStatus.PASS)
        self.assertTrue(all(f.status is ProbeStatus.PASS for f in report.findings))

    def test_missing_optional_enum_yields_warning(self) -> None:
        iesve, project, cdb = _fully_capable_project()
        # Optional enum removed -> WARNING not FAIL.
        del iesve.construction_class
        report = run_probe(iesve, project, cdb, project_id="proj_X", clock=_fake_clock())
        self.assertEqual(report.overall, ProbeStatus.WARNING)
        warning_ids = {
            f.capability_id for f in report.findings if f.status is ProbeStatus.WARNING
        }
        self.assertIn("IESVE_CONSTRUCTION_CLASS_ENUM", warning_ids)

    def test_rooms_are_probed_through_the_model_not_the_project(self) -> None:
        """The real run failed on an invented ``project.rooms``.

        Guarding the member names keeps the probe honest: a probe that reports
        FAIL because it asked for something the API never had would block a
        policy claim for no reason at all.
        """

        iesve, project, cdb = _fully_capable_project()
        self.assertFalse(hasattr(project, "rooms"))
        report = run_probe(iesve, project, cdb, project_id="proj_X", clock=_fake_clock())
        ids = {finding.capability_id for finding in report.findings}
        self.assertIn("PROJECT_MODELS", ids)
        self.assertIn("MODEL_GET_BODIES", ids)
        self.assertNotIn("PROJECT_ROOMS", ids)

    def test_a_project_without_models_fails_closed(self) -> None:
        iesve, project, cdb = _fully_capable_project()
        project.models = []
        report = run_probe(iesve, project, cdb, project_id="proj_X", clock=_fake_clock())
        self.assertEqual(report.overall, ProbeStatus.FAIL)

    def test_uvalue_types_is_probed_on_the_class_not_the_instance(self) -> None:
        iesve, project, cdb = _fully_capable_project()
        self.assertFalse(hasattr(cdb, "uvalue_types"))
        report = run_probe(iesve, project, cdb, project_id="proj_X", clock=_fake_clock())
        finding = next(
            f for f in report.findings if f.capability_id == "CDB_UVALUE_TYPES"
        )
        self.assertIs(finding.status, ProbeStatus.PASS)

    def test_missing_required_setter_yields_fail(self) -> None:
        iesve, project, cdb = _fully_capable_project()
        # Required capability removed -> FAIL.
        del project.create_thermal_template
        report = run_probe(iesve, project, cdb, project_id="proj_X", clock=_fake_clock())
        self.assertEqual(report.overall, ProbeStatus.FAIL)
        fail_ids = {
            f.capability_id for f in report.findings if f.status is ProbeStatus.FAIL
        }
        self.assertIn("PROJECT_CREATE_THERMAL_TEMPLATE", fail_ids)

    def test_missing_get_construction_yields_fail(self) -> None:
        iesve, project, cdb = _fully_capable_project()
        del cdb.get_construction
        report = run_probe(iesve, project, cdb, project_id="proj_X", clock=_fake_clock())
        self.assertEqual(report.overall, ProbeStatus.FAIL)
        fail_ids = {
            f.capability_id for f in report.findings if f.status is ProbeStatus.FAIL
        }
        self.assertIn("CDB_CONSTRUCTION_LOOKUP", fail_ids)

    def test_none_project_yields_multiple_fails(self) -> None:
        iesve, _, cdb = _fully_capable_project()
        report = run_probe(iesve, None, cdb, project_id="proj_X", clock=_fake_clock())
        self.assertEqual(report.overall, ProbeStatus.FAIL)

    def test_write_probe_report_produces_valid_json(self) -> None:
        iesve, project, cdb = _fully_capable_project()
        report = run_probe(iesve, project, cdb, project_id="proj_X", clock=_fake_clock())
        with TemporaryDirectory() as tmp:
            path = write_probe_report(report, tmp)
            self.assertTrue(os.path.exists(path))
            with open(path, "r", encoding="utf-8") as handle:
                content = json.load(handle)
            self.assertEqual(content["schema_version"], "1.0")
            self.assertEqual(content["overall"], "PASS")
            self.assertEqual(content["project_id"], "proj_X")
            self.assertTrue(content["findings"])


if __name__ == "__main__":
    unittest.main()
