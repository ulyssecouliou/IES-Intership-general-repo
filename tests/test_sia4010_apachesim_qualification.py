"""Fail-closed tests for one-click ApacheSim runtime qualification."""

import hashlib
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from swiss_sia.reference_model.sia4010.apachesim_qualification import (
    ApacheSimQualificationError,
    run_qualified_apachesim,
)
from swiss_sia.reference_model.sia4010.native_ui import ModelBuilderController


ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = ROOT / ".codex_tmp"


#: ISO 52016-1 clause 7.2.2.14 infiltration expressed in VE ``l/s/m2``
#: (``units_val == 2``), as written by the source-traced asset manifest.
ISO_INFILTRATION_L_S_M2 = 0.3075


class _AirExchange:
    """Minimal ``RoomAirExchange`` double (API reference section 11)."""

    def __init__(self, type_val, max_flow, units_val=2, name="SIA600_INFILTRATION_0P41ACH"):
        self._data = {
            "name": name,
            "type_val": type_val,
            "units_val": units_val,
            # VE returns room-level flows as a dict indexed by unit selector.
            "max_flows": {units_val: max_flow},
            "max_flow_from_template": False,
            "variation_profile": "ON",
        }

    def get(self):
        return dict(self._data)


class _RoomData:
    def __init__(
        self,
        factor=2.0710644309317603,
        conditioned=True,
        infiltration_flow=ISO_INFILTRATION_L_S_M2,
    ):
        self.factor = factor
        self.conditioned = conditioned
        self.infiltration_flow = infiltration_flow

    def get_air_exchanges(self):
        if self.infiltration_flow is None:
            return []
        return [_AirExchange(0, self.infiltration_flow)]

    def get_room_conditions(self):
        return {
            "furniture_mass_factor": self.factor,
            "heating_profile": "ON" if self.conditioned else "OFF",
            "cooling_profile": "ON" if self.conditioned else "OFF",
        }

    def get_apache_systems(self):
        return {
            "conditioned": (
                True
                if self.conditioned
                else "iesve.conditioned_flag.no_free_floating"
            ),
            "heating_capacity_unlimited": True,
            "cooling_capacity_unlimited": True,
            "heating_plant_radiant_fraction": 0.0,
            "cooling_plant_radiant_fraction": 0.0,
            "system_air_minimum_flowrate": 0.0,
        }


class _Body:
    def __init__(
        self,
        name,
        factor=2.0710644309317603,
        conditioned=True,
        infiltration_flow=ISO_INFILTRATION_L_S_M2,
    ):
        self.name = name
        self.room_data = _RoomData(factor, conditioned, infiltration_flow)

    def get_room_data(self):
        return self.room_data


class _Model:
    def __init__(
        self,
        case_id,
        factor=2.0710644309317603,
        conditioned=True,
        infiltration_flow=ISO_INFILTRATION_L_S_M2,
    ):
        self.body = _Body(
            "SIA4010_TEST_1_{}_ZONE".format(case_id),
            factor,
            conditioned,
            infiltration_flow,
        )

    def get_bodies(self, assigned):
        return [self.body]


class _Project:
    """Minimal saved VE project identity."""

    def __init__(
        self,
        path,
        *,
        case_id="600",
        factor=2.0710644309317603,
        conditioned=True,
        infiltration_flow=ISO_INFILTRATION_L_S_M2,
    ):
        self.path = str(path)
        self.models = [_Model(case_id, factor, conditioned, infiltration_flow)]
        self.name = Path(path).name


class _FakeApacheSim:
    """Deterministic synchronous ApacheSim stand-in."""

    def __init__(
        self,
        project_path,
        *,
        mismatch=False,
        run_result=True,
        rfcont=0.5,
    ):
        self.project_path = Path(project_path)
        self.options = {
            "simulation_timestep": 2,
            "preconditioning_days": 14,
            "reporting_interval": 1,
        }
        self.mismatch = mismatch
        self.run_result = run_result
        self.rfcont = rfcont

    def get_options(self):
        options = dict(self.options)
        if self.mismatch and "reporting_interval" in options:
            options["reporting_interval"] = 2
        return options

    def set_options(self, options):
        self.options.update(options)
        return True

    def run_simulation(self, queue_to_tasks=False):
        if self.run_result:
            vista = self.project_path / "Vista"
            vista.mkdir(parents=True, exist_ok=True)
            (vista / self.options["results_filename"]).write_bytes(
                b"qualified fake APS"
            )
            if self.rfcont is not None:
                apache = self.project_path / "apache"
                apache.mkdir(parents=True, exist_ok=True)
                (apache / "{}.der".format(self.project_path.name)).write_text(
                    "VERSION, 8\nRFCONT,  {:.4f},\nEND\n".format(self.rfcont),
                    encoding="latin-1",
                )
        return self.run_result


class ApacheSimQualificationTests(unittest.TestCase):
    """Only source-confirmed temporal options may reach ApacheSim."""

    def setUp(self):
        self.project = TEMP_ROOT / self._testMethodName
        self.project.mkdir(parents=True, exist_ok=True)
        vista = self.project / "Vista"
        if vista.is_dir():
            for prior_result in vista.glob(
                "SIA4010_test_1_*_20260729_020304.aps"
            ):
                prior_result.unlink()
        self._write_scenario("600")
        self._write_model_report("600")
        self._write_runtime_input_report("600")

    def _write_scenario(self, case_id):
        payload = ModelBuilderController().build_payload(
            "SIA4010_1A_{}".format(case_id),
            "SIA4010_OFFICIAL",
            "1A",
            "test_1",
            case_id,
            (
                "CREATE_IN_ACTIVE_VE_PROJECT"
                if case_id == "600"
                else "QUALIFY_IN_ACTIVE_VE_PROJECT"
            ),
            "sia4010_case_manifest.json",
            "reference_model_config.json",
            "reference_model_assets.json",
        )
        (self.project / "sia_model_scenario.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    def _write_model_report(self, case_id, *, overall="WARNING"):
        path = (
            self.project
            / "reference_model_artifacts"
            / "reports"
            / "reference_model_report.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "overall_status": overall,
                    "run_metadata": {"mode": "VE_MUTATION"},
                    "validation_results": [
                        {
                            "control_id": "VE-WEA-001",
                            "status": "PASS",
                        }
                    ],
                    "additional_data": {
                        "asset_manifest": {
                            "metadata": {
                                "sia4010_variant": "test_1",
                                "sia4010_case_id": case_id,
                            }
                        }
                    },
                    "ve_model_snapshot": {
                        "spaces": [{"identifier": "SIA4010_TEST_1_ZONE"}]
                    },
                }
            ),
            encoding="utf-8",
        )

    def _write_runtime_input_report(
        self,
        case_id,
        *,
        conditioned=True,
        infiltration_receipt=None,
    ):
        scenario_path = self.project / "sia_model_scenario.json"
        scenario_payload = json.loads(scenario_path.read_text(encoding="utf-8"))
        report_path = (
            self.project
            / "sia4010_artifacts"
            / "diagnostics"
            / "sia4010_test1_runtime_input_qualification_20260729_010203.json"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        factor = 2.0710644309317603
        report_path.write_text(
            json.dumps(
                {
                    "status": "PROVISIONAL_ENGINE_MAPPING_APPLIED_READY_FOR_SIMULATION",
                    "project": {"name": self.project.name, "path": str(self.project)},
                    "scenario": scenario_payload,
                    "scenario_sha256": hashlib.sha256(
                        scenario_path.read_bytes()
                    ).hexdigest(),
                    "room": {"name": "SIA4010_TEST_1_{}_ZONE".format(case_id)},
                    "mutation": {
                        "intended_fields": (
                            [
                                "furniture_mass_factor",
                                "system_air_minimum_flowrate",
                                "heating_plant_radiant_fraction",
                                "cooling_plant_radiant_fraction",
                            ]
                            if conditioned
                            else [
                                "furniture_mass_factor",
                                "system_air_minimum_flowrate",
                            ]
                        ),
                        "before": 1.0,
                        "requested": factor,
                        "verified_after": factor,
                        "system_verified_after": (
                            {
                                "ve_heating_radiant_fraction": 0.0,
                                "ve_cooling_radiant_fraction": 0.0,
                                "verified": True,
                            }
                            if conditioned
                            else {"applicable": False, "verified": True}
                        ),
                        "mechanical_ventilation_verified_after": {
                            "ve_system_air_minimum_flowrate": 0.0,
                            "verified": True,
                        },
                        "prescribed_infiltration_verified_after": (
                            infiltration_receipt
                            if infiltration_receipt is not None
                            else {
                                "ve_infiltration_max_flow": (
                                    ISO_INFILTRATION_L_S_M2
                                ),
                                "ve_infiltration_units_val": 2,
                                "verified": True,
                            }
                        ),
                    },
                    "mapping": {"furniture_mass_factor": factor},
                    "capacity_semantics": {
                        "conditioned": conditioned,
                        "verified": True,
                    },
                    "free_floating_controls": (
                        {"applicable": False, "verified": True}
                        if conditioned
                        else {
                            "applicable": True,
                            "verified": True,
                            "verified_after": {
                                "heating_profile": "OFF",
                                "cooling_profile": "OFF",
                            },
                        }
                    ),
                    "guardrails": {
                        "capacity_fields_mutated": False,
                        "compliance_claim_allowed": False,
                    },
                }
            ),
            encoding="utf-8",
        )


    def _run(self, factory, *, project=None):
        return run_qualified_apachesim(
            project=project or _Project(self.project),
            apachesim_factory=factory,
            repository_root=ROOT,
            now=datetime(2026, 7, 29, 2, 3, 4, tzinfo=timezone.utc),
            file_wait_seconds=0.0,
        )

    def test_sets_only_confirmed_annual_hourly_options_and_writes_evidence(self):
        sim = _FakeApacheSim(self.project)
        receipt = self._run(lambda: sim)
        self.assertEqual(
            receipt.status,
            "SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION",
        )
        self.assertEqual(
            receipt.requested_options,
            {
                "start_day": 1,
                "start_month": 1,
                "end_day": 31,
                "end_month": 12,
                "reporting_interval": 3,
                "preconditioning_days": 31,
                "results_filename": (
                    "SIA4010_test_1_600_20260729_020304.aps"
                ),
            },
        )
        self.assertEqual(receipt.options_after["simulation_timestep"], 2)
        self.assertEqual(receipt.options_after["preconditioning_days"], 31)
        self.assertGreater(receipt.results_size_bytes, 0)
        self.assertTrue(Path(receipt.results_path).is_file())
        audit = json.loads(Path(receipt.audit_path).read_text(encoding="utf-8"))
        self.assertFalse(audit["compliance_claim_allowed"])
        self.assertTrue(audit["aps_evaluation_required"])
        self.assertIn("simulation_timestep", audit["deliberately_unset_engine_options"])
        self.assertNotIn(
            "preconditioning_days", audit["deliberately_unset_engine_options"]
        )
        self.assertEqual(
            audit["initialization_source_file"]["initialization_hours"], 744
        )
        self.assertTrue(audit["source_file"]["sha256"])
        self.assertEqual(
            audit["control_temperature_evidence"]["rfcont"], 0.5
        )

    def test_rejects_air_temperature_control_after_simulation(self):
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "RFCONT=0.*requires RFCONT=0.5",
        ):
            self._run(lambda: _FakeApacheSim(self.project, rfcont=0.0))
        audit_path = (
            self.project
            / "sia4010_artifacts"
            / "simulation"
            / "SIA4010_test_1_600_apachesim_qualification.json"
        )
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        self.assertEqual(audit["status"], "FAIL")
        self.assertFalse(audit["compliance_claim_allowed"])

    def test_rejects_missing_engine_control_readback(self):
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "expected one generated .der file",
        ):
            self._run(lambda: _FakeApacheSim(self.project, rfcont=None))

    def test_rejects_model_report_for_another_case_before_calling_engine(self):
        self._write_model_report("640")
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "instead of test_1/600",
        ):
            self._run(lambda: self.fail("ApacheSim must not be constructed"))

    def test_rejects_failed_weather_validation(self):
        report_path = (
            self.project
            / "reference_model_artifacts"
            / "reports"
            / "reference_model_report.json"
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["validation_results"][0]["status"] = "FAIL"
        report_path.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "VE-WEA-001 must PASS",
        ):
            self._run(lambda: _FakeApacheSim(self.project))
    def test_rejects_missing_runtime_input_qualification(self):
        report = next(
            (self.project / "sia4010_artifacts" / "diagnostics").glob(
                "sia4010_test1_runtime_input_qualification_*.json"
            )
        )
        report.unlink()
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "no qualification report was found",
        ):
            self._run(lambda: self.fail("ApacheSim must not be constructed"))

    def test_rejects_live_furniture_factor_mismatch(self):
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "Live VE furniture factor does not match",
        ):
            self._run(
                lambda: self.fail("ApacheSim must not be constructed"),
                project=_Project(self.project, factor=1.0),
            )

    def test_rejects_live_non_zero_mechanical_ventilation(self):
        """The zero-ventilation correction must be re-proven on the live room.

        A saved project can re-inherit the generic office template's
        ``10 L/(s person)`` outdoor-air default on reopen. The qualification
        report would still read zero, so only the live read-back catches it.
        """

        project = _Project(self.project)
        project.models[0].body.room_data.get_apache_systems = lambda: {
            "conditioned": True,
            "heating_capacity_unlimited": True,
            "cooling_capacity_unlimited": True,
            "heating_plant_radiant_fraction": 0.0,
            "cooling_plant_radiant_fraction": 0.0,
            "system_air_minimum_flowrate": 10.0,
        }
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "no longer has zero mechanical ventilation",
        ):
            self._run(
                lambda: self.fail("ApacheSim must not be constructed"),
                project=project,
            )

    def test_rejects_runtime_qualification_without_infiltration_evidence(self):
        """A report predating the infiltration read-back is stale, not valid."""

        report = next(
            (self.project / "sia4010_artifacts" / "diagnostics").glob(
                "sia4010_test1_runtime_input_qualification_*.json"
            )
        )
        payload = json.loads(report.read_text(encoding="utf-8"))
        del payload["mutation"]["prescribed_infiltration_verified_after"]
        report.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "no prescribed-infiltration read-back evidence",
        ):
            self._run(lambda: self.fail("ApacheSim must not be constructed"))

    def test_rejects_live_room_with_infiltration_removed(self):
        """Zeroing mechanical ventilation must not leave the room airtight."""

        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "no longer retains the prescribed",
        ):
            self._run(
                lambda: self.fail("ApacheSim must not be constructed"),
                project=_Project(self.project, infiltration_flow=None),
            )

    def test_rejects_live_infiltration_flow_drift(self):
        """The live infiltration must match the qualified magnitude."""

        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "infiltration flow does not match",
        ):
            self._run(
                lambda: self.fail("ApacheSim must not be constructed"),
                project=_Project(self.project, infiltration_flow=0.9),
            )

    def test_rejects_stale_single_field_runtime_qualification(self):
        report = next(
            (self.project / "sia4010_artifacts" / "diagnostics").glob(
                "sia4010_test1_runtime_input_qualification_*.json"
            )
        )
        payload = json.loads(report.read_text(encoding="utf-8"))
        payload["mutation"] = {
            "only_intended_field": "furniture_mass_factor",
            "requested": 2.0710644309317603,
            "verified_after": 2.0710644309317603,
        }
        report.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "wrong mutation scope",
        ):
            self._run(lambda: self.fail("ApacheSim must not be constructed"))

    def test_free_floating_case_requires_only_furniture_runtime_mutation(self):
        self._write_scenario("600FF")
        self._write_model_report("600FF")
        self._write_runtime_input_report("600FF", conditioned=False)
        project = _Project(
            self.project,
            case_id="600FF",
            conditioned=False,
        )
        receipt = self._run(
            lambda: _FakeApacheSim(self.project, rfcont=0.0),
            project=project,
        )
        self.assertEqual(receipt.case_id, "600FF")
        self.assertEqual(
            receipt.status,
            "SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION",
        )
        audit = json.loads(Path(receipt.audit_path).read_text(encoding="utf-8"))
        control = audit["control_temperature_evidence"]
        self.assertEqual(control["rfcont"], 0.0)
        self.assertFalse(control["requirement_applicable"])
        self.assertIsNone(control["required_rfcont"])
        self.assertEqual(
            control["verification_status"],
            "NOT_APPLICABLE_FREE_FLOATING",
        )

    def test_free_floating_case_rejects_live_on_profiles(self):
        self._write_scenario("600FF")
        self._write_model_report("600FF")
        self._write_runtime_input_report("600FF", conditioned=False)
        project = _Project(
            self.project,
            case_id="600FF",
            conditioned=True,
        )
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "no longer has OFF heating and cooling profiles",
        ):
            self._run(
                lambda: self.fail("ApacheSim must not be constructed"),
                project=project,
            )



    def test_option_readback_mismatch_fails_and_keeps_audit(self):
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "read-back mismatch",
        ):
            self._run(lambda: _FakeApacheSim(self.project, mismatch=True))
        audit_path = (
            self.project
            / "sia4010_artifacts"
            / "simulation"
            / "SIA4010_test_1_600_apachesim_qualification.json"
        )
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        self.assertEqual(audit["status"], "FAIL")
        self.assertFalse(audit["compliance_claim_allowed"])

    def test_run_failure_does_not_create_false_success(self):
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "did not return True",
        ):
            self._run(
                lambda: _FakeApacheSim(self.project, run_result=False)
            )

    def test_unsupported_case_1e_is_blocked(self):
        self._write_scenario("1E")
        self._write_model_report("1E")
        with self.assertRaisesRegex(
            ApacheSimQualificationError,
            "unavailable for test_1/1E",
        ):
            self._run(lambda: _FakeApacheSim(self.project))


if __name__ == "__main__":
    unittest.main()
