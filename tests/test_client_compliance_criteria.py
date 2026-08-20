"""Contract tests for the client SIA 380/2 compliance-criteria manifest + evaluator.

Guards that the manifest stays faithful to the live config (regulatory values
come from config, every criterion states its data source and VE capability, the
.aps-driven criteria name the quantities the .aps must yield, and the two
criteria VE cannot produce stay flagged), and that the runtime evaluator fills a
fail-closed per-criterion verdict against a model + its .aps results.
"""

from __future__ import annotations

import unittest

from swiss_sia import config
from swiss_sia.compliance_criteria import CAPABILITY_LEGEND, build_manifest
from swiss_sia.compliance_criteria_evaluator import evaluate_client_compliance


class _Room:
    surfaces = []
    openings = []


class ManifestContractTests(unittest.TestCase):
    def setUp(self):
        self.manifest = build_manifest()
        self.by_id = {c["id"]: c for c in self.manifest["criteria"]}

    def test_every_criterion_has_the_analysable_fields(self):
        required = {
            "id", "domain", "criterion", "data_source", "ve_capability",
            "aps_quantities", "runtime_status", "article_source", "coverage_key",
        }
        self.assertTrue(self.manifest["criteria"])
        for crit in self.manifest["criteria"]:
            self.assertTrue(required.issubset(crit), crit["id"])
            self.assertEqual(crit["runtime_status"], "TO_BE_EVALUATED")
            self.assertIn(crit["ve_capability"], CAPABILITY_LEGEND, crit["id"])
            self.assertTrue(crit["data_source"], crit["id"])

    def test_regulatory_thresholds_come_from_config_not_the_builder(self):
        opaque = self.by_id["SIA3802_OPAQUE_U_VALUES"]
        self.assertEqual(
            opaque["thresholds"]["limit"],
            config.SIA3802_LIMIT_VALUES["external_wall_u"],
        )
        self.assertEqual(
            opaque["thresholds"]["target"],
            config.SIA3802_TARGET_VALUES["external_wall_u"],
        )

    def test_decisive_gate_is_reviewer_evidence_not_computed_by_ve(self):
        gate = self.manifest["decisive_gate"]
        self.assertEqual(gate["article"], "SIA 380/2:2022 §7.2.5.2")
        self.assertEqual(gate["data_source"], ["reviewer_or_external_evidence"])
        self.assertEqual(gate["ve_capability"], "EXTERNAL_EVIDENCE")

    def test_aps_driven_criteria_name_the_required_aps_quantities(self):
        for cid in (
            "SIA3802_DYNAMIC_APS_RESULTS",
            "SIA3802_HOURLY_TEMPERATURES",
            "SIA3802_HEATING_COOLING_DEMANDS",
        ):
            crit = self.by_id[cid]
            self.assertIn("aps_simulation_results", crit["data_source"], cid)
            self.assertTrue(crit["aps_quantities"], cid)

    def test_design_power_stays_not_available_in_ve(self):
        self.assertEqual(
            self.by_id["SIA3802_DESIGN_POWER_DAYS"]["ve_capability"], "NOT_AVAILABLE")

    def test_thermal_bridges_are_reviewer_evidence_not_unavailable(self):
        # VE still can't read psi/chi, but a reviewed schedule can now be ingested.
        self.assertEqual(
            self.by_id["SIA3802_THERMAL_BRIDGES"]["ve_capability"], "EXTERNAL_EVIDENCE")

    def test_seasonal_efficiency_criteria_carry_the_sn_en_14825_caveat(self):
        for cid in ("SIA3802_COOLING_EER_SEER", "SIA3802_HEATING_SCOP"):
            self.assertIn("SN EN 14825", self.by_id[cid]["ve_capability_note"], cid)


class EvaluatorTests(unittest.TestCase):
    def _base_sia3802(self, comparison_status):
        return {
            "envelope": {}, "openings": {}, "ventilation": {}, "gains": {},
            "setpoints": {}, "hvac": {}, "alerts": [],
            "global_reference_comparison": {"status": comparison_status},
        }

    def test_missing_evidence_never_becomes_ok(self):
        """Empty rooms -> criteria are NOT_CHECKABLE, never OK."""
        manifest = evaluate_client_compliance(
            self._base_sia3802("NOT_CHECKABLE"), {}, {}, [_Room()], [],
        )
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertEqual(by_id["SIA3802_OPAQUE_U_VALUES"]["runtime_status"], "NOT_CHECKABLE")
        # Rooms are extracted, so geometry is OK; nothing is silently PASS.
        self.assertEqual(by_id["SIA3802_ROOM_GEOMETRY"]["runtime_status"], "OK")

    def test_things_ve_cannot_do_are_reported_as_such(self):
        manifest = evaluate_client_compliance(
            self._base_sia3802("NOT_CHECKABLE"), {}, {}, [_Room()], [],
        )
        by_id = {c["id"]: c for c in manifest["criteria"]}
        # Thermal bridges are now reviewer-evidence: without a schedule they read
        # NEEDS_REVIEWER_EVIDENCE (VE still cannot read psi/chi itself).
        self.assertEqual(
            by_id["SIA3802_THERMAL_BRIDGES"]["runtime_status"], "NEEDS_REVIEWER_EVIDENCE"
        )
        self.assertEqual(
            by_id["SIA3802_DESIGN_POWER_DAYS"]["runtime_status"], "NOT_AVAILABLE_IN_VE"
        )

    def test_decisive_gate_reflects_the_global_comparison(self):
        missing = evaluate_client_compliance(
            self._base_sia3802("NOT_CHECKABLE"), {}, {}, [_Room()], [],
        )
        self.assertEqual(
            missing["decisive_gate"]["runtime_status"], "NEEDS_REVIEWER_EVIDENCE"
        )
        available = evaluate_client_compliance(
            self._base_sia3802("REVIEWED_RESULT_AVAILABLE"), {}, {}, [_Room()], [],
        )
        self.assertEqual(available["decisive_gate"]["runtime_status"], "OK")
        contradiction = evaluate_client_compliance(
            self._base_sia3802("REVIEWED_RESULT_CONTRADICTS_ACCEPTANCE"),
            {}, {}, [_Room()], [],
        )
        self.assertEqual(contradiction["decisive_gate"]["runtime_status"], "NOT_OK")

    def test_client_scope_drops_sia4010_criteria(self):
        manifest = evaluate_client_compliance(
            self._base_sia3802("NOT_CHECKABLE"), {}, {}, [_Room()], [],
            scope="sia3802",
        )
        self.assertFalse([
            c for c in manifest["criteria"]
            if str(c.get("standard") or "").startswith("SIA 4010")
        ])

    def test_aps_dynamic_results_unblock_the_aps_criteria(self):
        """Room .aps results (temperatures, demands) must reach the coverage stats
        even in the client scope where the SIA 4010 checks are skipped."""
        dynamic = {"rooms": [{
            "room_id": "SP000000", "room_name": "Office_01", "area_m2": 20.0,
            "heating_kwh": 120.0, "cooling_kwh": 40.0,
            "occupied_hours_above_26": 3.0, "occupied_hours_above_27": 1.0,
        }]}
        manifest = evaluate_client_compliance(
            self._base_sia3802("REVIEWED_RESULT_AVAILABLE"), {}, dynamic, [_Room()], [],
            scope="sia3802",
        )
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertNotEqual(
            by_id["SIA3802_HEATING_COOLING_DEMANDS"]["runtime_status"], "NOT_CHECKABLE")
        self.assertNotEqual(
            by_id["SIA3802_HOURLY_TEMPERATURES"]["runtime_status"], "NOT_CHECKABLE")

    def test_accepted_use_category_credits_the_criterion(self):
        """A room carrying a reviewer-accepted SIA 2024 category makes
        USE_CATEGORY OK, instead of staying forever PARTIAL."""
        class _MappedRoom:
            surfaces = []
            openings = []
            sia2024_category = "3.01"

        manifest = evaluate_client_compliance(
            self._base_sia3802("REVIEWED_RESULT_AVAILABLE"), {}, {},
            [_MappedRoom(), _MappedRoom()], [], scope="sia3802",
        )
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertEqual(by_id["SIA3802_USE_CATEGORY_SIA2024"]["runtime_status"], "OK")

    def test_unmapped_rooms_keep_use_category_partial(self):
        manifest = evaluate_client_compliance(
            self._base_sia3802("REVIEWED_RESULT_AVAILABLE"), {}, {}, [_Room()], [],
            scope="sia3802",
        )
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertEqual(by_id["SIA3802_USE_CATEGORY_SIA2024"]["runtime_status"], "PARTIAL")

    def test_thermal_bridge_reviewed_evidence_credits_the_criterion(self):
        sia3802 = self._base_sia3802("REVIEWED_RESULT_AVAILABLE")
        sia3802["thermal_bridges"] = {
            "status": "AVAILABLE",
            "accepted": True,
            "record": {
                "assessment_method": "detailed_psi_chi",
                "total_psi_chi_w_per_k_numeric": 12.4,
            },
        }
        manifest = evaluate_client_compliance(
            sia3802, {}, {}, [_Room()], [], scope="sia3802")
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertEqual(by_id["SIA3802_THERMAL_BRIDGES"]["runtime_status"], "OK")

    def test_thermal_bridge_without_evidence_needs_reviewer(self):
        manifest = evaluate_client_compliance(
            self._base_sia3802("REVIEWED_RESULT_AVAILABLE"), {}, {}, [_Room()], [],
            scope="sia3802")
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertEqual(
            by_id["SIA3802_THERMAL_BRIDGES"]["runtime_status"], "NEEDS_REVIEWER_EVIDENCE")

    def test_evaluation_block_matches_the_authoritative_verdict(self):
        manifest = evaluate_client_compliance(
            self._base_sia3802("NOT_CHECKABLE"), {}, {}, [_Room()], [],
        )
        evaluation = manifest["evaluation"]
        self.assertEqual(evaluation["overall_sia3802_status"], "NOT_DETERMINED")
        self.assertIn("global_reference_comparison", evaluation["outstanding"])
        self.assertEqual(evaluation["rooms_analysed"], 1)


class ThermalBridgeEvidenceTests(unittest.TestCase):
    """The reviewer thermal-bridge record is accepted only when complete."""

    def _row(self, **overrides):
        row = {
            "project_id": "Demo",
            "assessment_method": "detailed_psi_chi",
            "total_psi_chi_w_per_k": "12.4",
            "unit": "W/K",
            "review_status": "accepted",
            "reviewer": "Reviewer",
            "review_date": "2026-08-20",
            "source_document": "thermal_bridge_calc.pdf",
        }
        row.update(overrides)
        return row

    def test_complete_record_is_accepted(self):
        from swiss_sia.evidence_manager import _normalize_thermal_bridge_record
        self.assertTrue(_normalize_thermal_bridge_record(self._row())["accepted"])

    def test_schedule_reference_satisfies_the_quantum(self):
        from swiss_sia.evidence_manager import _normalize_thermal_bridge_record
        row = self._row(total_psi_chi_w_per_k="", schedule_reference="Junction schedule §4")
        self.assertTrue(_normalize_thermal_bridge_record(row)["accepted"])

    def test_missing_value_and_schedule_is_rejected(self):
        from swiss_sia.evidence_manager import _normalize_thermal_bridge_record
        row = self._row(total_psi_chi_w_per_k="", schedule_reference="")
        self.assertFalse(_normalize_thermal_bridge_record(row)["accepted"])

    def test_pending_review_is_rejected(self):
        from swiss_sia.evidence_manager import _normalize_thermal_bridge_record
        self.assertFalse(
            _normalize_thermal_bridge_record(self._row(review_status="pending"))["accepted"])


if __name__ == "__main__":
    unittest.main()
