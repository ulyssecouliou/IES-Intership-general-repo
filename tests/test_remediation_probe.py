"""Tests for the pure-Python read-only remediation diagnosis."""

from __future__ import annotations

import unittest

from swiss_sia.model_analyzer import OpeningData, RoomData, SurfaceData
from swiss_sia.remediation_probe import build_remediation_diagnosis


class RemediationProbeTests(unittest.TestCase):
    """Verify conservative status and exact affected-object reporting."""

    def test_reports_exact_model_failures_and_missing_outputs(self) -> None:
        """Unclassified surfaces and incomplete windows must fail closed."""
        room = RoomData(
            id="ROOM-1",
            name="Test room",
            area=48.0,
            surfaces=[
                SurfaceData(
                    id="SURF-1",
                    area=12.0,
                    is_external=True,
                    surface_type="unclassified",
                    construction_ids=["WALL-X"],
                )
            ],
            openings=[
                OpeningData(
                    id="WIN-1",
                    area=3.0,
                    is_external=True,
                    opening_type="window",
                    construction_id="GLZ-X",
                )
            ],
            internal_gains={"lighting": None, "people": None, "equipment": 5.0},
        )
        diagnosis = build_remediation_diagnosis(
            [room],
            {"status": "AVAILABLE", "selected_aps_file": "test.aps"},
            r"C:\Models\DEMO_TEST",
        )

        self.assertEqual(diagnosis.status, "FAIL")
        controls = {control.control_id: control for control in diagnosis.controls}
        self.assertEqual(controls["RUN-001"].status, "PASS")
        self.assertEqual(controls["MODEL-001"].status, "FAIL")
        self.assertEqual(controls["MODEL-001"].affected_objects[0]["id"], "SURF-1")
        self.assertEqual(controls["MODEL-002"].status, "FAIL")
        self.assertEqual(controls["MODEL-002"].affected_objects[0]["id"], "WIN-1")
        self.assertEqual(controls["MODEL-003"].status, "WARNING")
        self.assertEqual(controls["SIM-002"].status, "WARNING")

    def test_complete_readback_returns_pass(self) -> None:
        """Complete model, APS and reviewed metadata inputs should pass the probe."""
        room = RoomData(
            id="ROOM-1",
            name="Complete room",
            area=48.0,
            surfaces=[
                SurfaceData(
                    id="SURF-1",
                    area=12.0,
                    is_external=True,
                    surface_type="external wall",
                    u_value=0.2,
                )
            ],
            openings=[
                OpeningData(
                    id="WIN-1",
                    area=3.0,
                    is_external=True,
                    opening_type="window",
                    construction_id="GLZ-1",
                    u_value=1.1,
                    frame_fraction=0.25,
                )
            ],
            internal_gains={"lighting": 6.0, "people": 4.0, "equipment": 5.0},
            internal_gains_wh_m2_day=120.0,
            ventilation_m3_h_m2=2.0,
        )
        dynamic = {
            "status": "AVAILABLE",
            "selected_aps_file": "complete.aps",
            "total_heating_kwh": 100.0,
            "total_lighting_kwh": 20.0,
            "total_fan_kwh": 10.0,
            "total_pump_kwh": 5.0,
            "total_auxiliary_kwh": 1.0,
            "total_coil_heating_kwh": 80.0,
            "total_coil_cooling_kwh": 60.0,
            "project_metadata_status": "AVAILABLE",
            "reviewed_weather_match_status": "MATCH",
        }

        diagnosis = build_remediation_diagnosis(
            [room], dynamic, r"C:\Models\COMPLETE_TEST"
        )

        self.assertEqual(diagnosis.status, "PASS")
        self.assertTrue(all(control.status == "PASS" for control in diagnosis.controls))
        self.assertEqual(diagnosis.next_actions, [])

    def test_numerical_surface_residue_does_not_fail_the_model(self) -> None:
        """A near-zero external partition must be audited but not remediated."""
        room = RoomData(
            id="ROOM-1",
            name="Room with topology residue",
            surfaces=[
                SurfaceData(
                    id="SLIVER-1",
                    area=7.8e-14,
                    net_area=7.8e-14,
                    is_external=True,
                    surface_type="partition",
                )
            ],
            internal_gains={"lighting": 1.0},
            internal_gains_wh_m2_day=1.0,
            ventilation_m3_h_m2=1.0,
        )
        dynamic = {
            "status": "AVAILABLE",
            "selected_aps_file": "test.aps",
            "total_heating_kwh": 1.0,
            "total_lighting_kwh": 1.0,
            "total_fan_kwh": 1.0,
            "total_pump_kwh": 1.0,
            "total_auxiliary_kwh": 1.0,
            "total_coil_heating_kwh": 1.0,
            "total_coil_cooling_kwh": 1.0,
            "project_metadata_status": "AVAILABLE",
            "reviewed_weather_match_status": "MATCH",
        }

        diagnosis = build_remediation_diagnosis(
            [room], dynamic, r"C:\Models\SLIVER_TEST"
        )

        controls = {control.control_id: control for control in diagnosis.controls}
        self.assertEqual(controls["MODEL-001"].status, "PASS")
        self.assertIn("1 numerical residue(s) ignored", controls["MODEL-001"].observed)

    def test_runtime_evidence_classifies_missing_inputs_and_inactive_heating(self) -> None:
        """Raw VE/APS evidence must replace generic extraction warnings."""
        room = RoomData(
            id="ROOM-1",
            name="Runtime room",
            internal_gains={"lighting": None, "equipment": 5.0},
            internal_gains_wh_m2_day=120.0,
        )
        dynamic = {"status": "AVAILABLE", "selected_aps_file": "test.aps"}
        runtime = {
            "rooms": [{
                "room_id": "ROOM-1",
                "room_conditions": {"heating_profile": "OFF"},
                "internal_gains": [{"name": "Miscellaneous", "type_str": "Miscellaneous"}],
                "air_exchanges": [{"name": "Infiltration"}],
            }]
        }
        aps = {
            "production_bindings": {"heating_load": {"aps_varname": "Heating load"}},
            "unresolved_bindings": ["lighting", "fan"],
        }

        diagnosis = build_remediation_diagnosis(
            [room], dynamic, r"C:\Models\RUNTIME_TEST", runtime, aps
        )
        controls = {control.control_id: control for control in diagnosis.controls}

        self.assertEqual(controls["MODEL-003"].category, "VE_MODEL_EVIDENCE")
        self.assertIn("infiltration", controls["MODEL-003"].observed)
        self.assertEqual(controls["MODEL-004"].category, "VE_MODEL_EVIDENCE")
        self.assertIn("no VE Lighting gain", controls["MODEL-004"].observed)
        self.assertIn("heating profiles", controls["SIM-002"].observed)
        self.assertIn("lighting, fan", controls["SIM-003"].observed)


if __name__ == "__main__":
    unittest.main()
