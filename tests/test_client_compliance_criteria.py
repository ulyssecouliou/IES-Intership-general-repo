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

    def test_thermal_bridges_are_read_from_ve(self):
        # VE 2025.2 reads psi/chi per surface; a reviewed schedule is the fallback.
        self.assertEqual(
            self.by_id["SIA3802_THERMAL_BRIDGES"]["ve_capability"], "VE_AVAILABLE")

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
        # Thermal bridges are read from VE (VE_AVAILABLE): with no VE read and no
        # reviewer schedule they read NOT_CHECKABLE, never a silent pass.
        self.assertEqual(
            by_id["SIA3802_THERMAL_BRIDGES"]["runtime_status"], "NOT_CHECKABLE"
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

    def test_thermal_bridge_without_evidence_is_not_checkable(self):
        manifest = evaluate_client_compliance(
            self._base_sia3802("REVIEWED_RESULT_AVAILABLE"), {}, {}, [_Room()], [],
            scope="sia3802")
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertEqual(
            by_id["SIA3802_THERMAL_BRIDGES"]["runtime_status"], "NOT_CHECKABLE")

    def test_ve_read_thermal_bridges_credit_the_criterion(self):
        """A VE-read H_tb with non-zero junctions credits the criterion (VE primary)."""
        sia3802 = self._base_sia3802("REVIEWED_RESULT_AVAILABLE")
        sia3802["thermal_bridges"] = {
            "status": "NOT_PROVIDED",
            "accepted": False,
            "record": None,
            "source": "ve_model",
            "ve_available": True,
            "total_w_per_k": 24.66,
            "nonzero_count": 8,
            "zero_psi_linear_count": 60,
        }
        manifest = evaluate_client_compliance(
            sia3802, {}, {}, [_Room()], [], scope="sia3802")
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertEqual(by_id["SIA3802_THERMAL_BRIDGES"]["runtime_status"], "OK")

    def test_boiler_only_heating_makes_scop_non_applicable(self):
        """A sized non-heat-pump heating generator -> SCOP is out of scope, not a gap."""
        class _BoilerRoom:
            surfaces = []
            openings = []
            hvac_systems = [{
                "heating_capacity_kw": 12.0,
                "heating_generator_class": None,  # VE did not classify a heat pump
                "scop": None,
            }]

        manifest = evaluate_client_compliance(
            self._base_sia3802("REVIEWED_RESULT_AVAILABLE"), {}, {},
            [_BoilerRoom()], [], scope="sia3802",
        )
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertEqual(
            by_id["SIA3802_HEATING_SCOP"]["runtime_status"], "NON_APPLICABLE")

    def test_heat_pump_without_scop_stays_not_checkable(self):
        """A heat pump lacking SCOP is a real gap, never NON_APPLICABLE."""
        class _HeatPumpRoom:
            surfaces = []
            openings = []
            hvac_systems = [{
                "heating_capacity_kw": 8.0,
                "heating_generator_class": "heat_pump_air_water",
                "scop": None,
            }]

        manifest = evaluate_client_compliance(
            self._base_sia3802("REVIEWED_RESULT_AVAILABLE"), {}, {},
            [_HeatPumpRoom()], [], scope="sia3802",
        )
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertEqual(
            by_id["SIA3802_HEATING_SCOP"]["runtime_status"], "NOT_CHECKABLE")

    def test_reviewed_cooling_generator_credits_the_eer_criterion(self):
        """Reviewed manufacturer EER (autosize workaround) makes EER/SEER OK."""
        sia3802 = self._base_sia3802("REVIEWED_RESULT_AVAILABLE")
        sia3802["cooling_generators"] = {
            "status": "AVAILABLE",
            "accepted": True,
            "record": {
                "generator_class": "air_cooled_chiller",
                "capacity_kw_numeric": 45.0,
                "nominal_eer_numeric": 3.2,
                "seer_numeric": None,
            },
        }
        manifest = evaluate_client_compliance(
            sia3802, {}, {}, [_Room()], [], scope="sia3802")
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertEqual(by_id["SIA3802_COOLING_EER_SEER"]["runtime_status"], "OK")

    def test_cooling_eer_without_evidence_stays_not_checkable(self):
        manifest = evaluate_client_compliance(
            self._base_sia3802("REVIEWED_RESULT_AVAILABLE"), {}, {}, [_Room()], [],
            scope="sia3802")
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertEqual(
            by_id["SIA3802_COOLING_EER_SEER"]["runtime_status"], "NOT_CHECKABLE")

    def test_reviewed_electrical_power_credits_the_724_criterion(self):
        sia3802 = self._base_sia3802("REVIEWED_RESULT_AVAILABLE")
        sia3802["electrical_power"] = {
            "accepted": True,
            "meets_limit": True,
            "limit_w_m2": 7.0,
            "record": {
                "building_status_key": "new",
                "required_electrical_power_w_m2_numeric": 6.0,
            },
        }
        manifest = evaluate_client_compliance(
            sia3802, {}, {}, [_Room()], [], scope="sia3802")
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertEqual(by_id["SIA3802_ELECTRICAL_POWER"]["runtime_status"], "OK")

    def test_electrical_power_without_evidence_needs_reviewer(self):
        manifest = evaluate_client_compliance(
            self._base_sia3802("REVIEWED_RESULT_AVAILABLE"), {}, {}, [_Room()], [],
            scope="sia3802")
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertEqual(
            by_id["SIA3802_ELECTRICAL_POWER"]["runtime_status"], "NEEDS_REVIEWER_EVIDENCE")

    def test_reviewed_ahu_evidence_credits_the_ahu_criterion(self):
        sia3802 = self._base_sia3802("REVIEWED_RESULT_AVAILABLE")
        sia3802["ahu_heat_recovery"] = {
            "status": "AVAILABLE",
            "accepted": True,
            "record": {
                "leakage_class": "B",
                "heat_recovery_temperature_efficiency_numeric": 0.78,
            },
        }
        manifest = evaluate_client_compliance(
            sia3802, {}, {}, [_Room()], [], scope="sia3802")
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertEqual(by_id["SIA3802_AHU_HEAT_RECOVERY"]["runtime_status"], "OK")

    def test_reviewed_solar_protection_windows_credit_the_criterion(self):
        """Reviewer-documented shading covering every external window -> OK."""
        class _Window:
            is_external = True
            opening_type = "window"

        class _WindowedRoom:
            surfaces = []
            openings = [_Window()]

        sia3802 = self._base_sia3802("REVIEWED_RESULT_AVAILABLE")
        sia3802["solar_protection_evidence"] = {
            "status": "AVAILABLE",
            "accepted_window_count": 1,
            "records": [],
        }
        manifest = evaluate_client_compliance(
            sia3802, {}, {}, [_WindowedRoom()], [], scope="sia3802")
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertEqual(
            by_id["SIA3802_SOLAR_PROTECTION_CONTROL"]["runtime_status"], "OK")

    def test_partial_reviewed_solar_protection_stays_partial(self):
        """Reviewed shading covering only some windows must not read AVAILABLE."""
        class _Window:
            is_external = True
            opening_type = "window"

        class _TwoWindowRoom:
            surfaces = []
            openings = [_Window(), _Window()]

        sia3802 = self._base_sia3802("REVIEWED_RESULT_AVAILABLE")
        sia3802["solar_protection_evidence"] = {
            "status": "AVAILABLE",
            "accepted_window_count": 1,
            "records": [],
        }
        manifest = evaluate_client_compliance(
            sia3802, {}, {}, [_TwoWindowRoom()], [], scope="sia3802")
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertEqual(
            by_id["SIA3802_SOLAR_PROTECTION_CONTROL"]["runtime_status"], "PARTIAL")

    def test_reviewed_ventilation_control_credits_the_criterion(self):
        sia3802 = self._base_sia3802("REVIEWED_RESULT_AVAILABLE")
        sia3802["ventilation_control_evidence"] = {
            "status": "AVAILABLE",
            "accepted": True,
            "record": {
                "system_type": "multizone",
                "control_class": "demand_controlled",
                "airflow_band": "3_to_6",
            },
        }
        manifest = evaluate_client_compliance(
            sia3802, {}, {}, [_Room()], [], scope="sia3802")
        by_id = {c["id"]: c for c in manifest["criteria"]}
        self.assertEqual(by_id["SIA3802_VENTILATION_CONTROL"]["runtime_status"], "OK")

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


class CoolingGeneratorEvidenceTests(unittest.TestCase):
    """The reviewer cooling-generator record is accepted only when complete."""

    def _row(self, **overrides):
        row = {
            "project_id": "Demo",
            "generator_class": "air_cooled_chiller",
            "capacity_kw": "45.0",
            "nominal_eer": "3.2",
            "seer": "",
            "unit": "kW",
            "review_status": "accepted",
            "reviewer": "Reviewer",
            "review_date": "2026-08-20",
            "source_document": "manufacturer_datasheet.pdf",
        }
        row.update(overrides)
        return row

    def test_complete_record_is_accepted(self):
        from swiss_sia.evidence_manager import _normalize_cooling_generator_record
        self.assertTrue(_normalize_cooling_generator_record(self._row())["accepted"])

    def test_declared_seer_only_is_accepted(self):
        """A declared SEER (no nominal EER) is a valid EN 14825 quantum (voie A)."""
        from swiss_sia.evidence_manager import _normalize_cooling_generator_record
        record = _normalize_cooling_generator_record(
            self._row(nominal_eer="", seer="3.9", generator_class="air_cooled"))
        self.assertTrue(record["accepted"])
        self.assertEqual(record["sia_cooling_class"], "air_cooled")
        self.assertEqual(record["seer_numeric"], 3.9)

    def test_water_cooled_class_is_mapped(self):
        from swiss_sia.evidence_manager import _normalize_cooling_generator_record
        record = _normalize_cooling_generator_record(
            self._row(generator_class="water_cooled_chiller"))
        self.assertEqual(record["sia_cooling_class"], "water_cooled")

    def test_no_eer_and_no_seer_is_rejected(self):
        from swiss_sia.evidence_manager import _normalize_cooling_generator_record
        self.assertFalse(
            _normalize_cooling_generator_record(
                self._row(nominal_eer="", seer=""))["accepted"])

    def test_missing_capacity_is_rejected(self):
        from swiss_sia.evidence_manager import _normalize_cooling_generator_record
        self.assertFalse(
            _normalize_cooling_generator_record(self._row(capacity_kw=""))["accepted"])

    def test_pending_review_is_rejected(self):
        from swiss_sia.evidence_manager import _normalize_cooling_generator_record
        self.assertFalse(
            _normalize_cooling_generator_record(self._row(review_status="pending"))["accepted"])


class ElectricalPowerEvidenceTests(unittest.TestCase):
    """The reviewer §7.2.4 electrical-power record is accepted only when complete."""

    def _row(self, **overrides):
        row = {
            "project_id": "Demo",
            "building_status": "new",
            "required_electrical_power_w_m2": "6.5",
            "review_status": "accepted",
            "reviewer": "Reviewer",
            "review_date": "2026-08-20",
            "source_document": "sizing_calc.pdf",
        }
        row.update(overrides)
        return row

    def test_complete_record_is_accepted(self):
        from swiss_sia.evidence_manager import _normalize_electrical_power_record
        rec = _normalize_electrical_power_record(self._row())
        self.assertTrue(rec["accepted"])
        self.assertEqual(rec["building_status_key"], "new")
        self.assertEqual(rec["required_electrical_power_w_m2_numeric"], 6.5)

    def test_existing_status_is_mapped(self):
        from swiss_sia.evidence_manager import _normalize_electrical_power_record
        self.assertEqual(
            _normalize_electrical_power_record(
                self._row(building_status="renovated"))["building_status_key"],
            "existing")

    def test_missing_power_is_rejected(self):
        from swiss_sia.evidence_manager import _normalize_electrical_power_record
        self.assertFalse(
            _normalize_electrical_power_record(
                self._row(required_electrical_power_w_m2=""))["accepted"])

    def test_unknown_status_is_rejected(self):
        from swiss_sia.evidence_manager import _normalize_electrical_power_record
        self.assertFalse(
            _normalize_electrical_power_record(
                self._row(building_status="mixed"))["accepted"])

    def test_negative_power_is_rejected(self):
        """Audit A5 R1: a negative required power is invalid, never accepted."""
        from swiss_sia.evidence_manager import _normalize_electrical_power_record
        self.assertFalse(
            _normalize_electrical_power_record(
                self._row(required_electrical_power_w_m2="-5"))["accepted"])

    def test_wrong_unit_is_rejected(self):
        """Audit A5 R2: a non-W/m2 unit (e.g. kW) must not be silently compared."""
        from swiss_sia.evidence_manager import _normalize_electrical_power_record
        rec = _normalize_electrical_power_record(self._row(unit="kW"))
        self.assertFalse(rec["accepted"])
        self.assertFalse(rec["unit_is_w_per_m2"])

    def test_blank_unit_is_accepted(self):
        from swiss_sia.evidence_manager import _normalize_electrical_power_record
        self.assertTrue(_normalize_electrical_power_record(self._row(unit=""))["accepted"])


class AhuHeatRecoveryEvidenceTests(unittest.TestCase):
    """The reviewer AHU / heat-recovery record is accepted only when complete."""

    def _row(self, **overrides):
        row = {
            "project_id": "Demo",
            "leakage_class": "B",
            "heat_recovery_type": "plate",
            "heat_recovery_temperature_efficiency": "0.78",
            "review_status": "accepted",
            "reviewer": "Reviewer",
            "review_date": "2026-08-20",
            "source_document": "ahu_datasheet.pdf",
        }
        row.update(overrides)
        return row

    def test_complete_record_is_accepted(self):
        from swiss_sia.evidence_manager import _normalize_ahu_heat_recovery_record
        self.assertTrue(_normalize_ahu_heat_recovery_record(self._row())["accepted"])

    def test_missing_efficiency_is_rejected(self):
        from swiss_sia.evidence_manager import _normalize_ahu_heat_recovery_record
        self.assertFalse(
            _normalize_ahu_heat_recovery_record(
                self._row(heat_recovery_temperature_efficiency=""))["accepted"])

    def test_missing_leakage_class_is_rejected(self):
        from swiss_sia.evidence_manager import _normalize_ahu_heat_recovery_record
        self.assertFalse(
            _normalize_ahu_heat_recovery_record(self._row(leakage_class=""))["accepted"])


class VentilationControlEvidenceTests(unittest.TestCase):
    """The reviewer ventilation-control record is accepted only when complete."""

    def _row(self, **overrides):
        row = {
            "project_id": "Demo",
            "system_type": "multizone",
            "control_class": "variable_occupancy",
            "airflow_band": "3_to_6",
            "review_status": "accepted",
            "reviewer": "Reviewer",
            "review_date": "2026-08-20",
            "source_document": "ventilation_design.pdf",
        }
        row.update(overrides)
        return row

    def test_complete_record_is_accepted(self):
        from swiss_sia.evidence_manager import _normalize_ventilation_control_record
        self.assertTrue(_normalize_ventilation_control_record(self._row())["accepted"])

    def test_numeric_airflow_satisfies_the_band(self):
        from swiss_sia.evidence_manager import _normalize_ventilation_control_record
        row = self._row(airflow_band="", specific_airflow_m3_h_m2="4.5")
        self.assertTrue(_normalize_ventilation_control_record(row)["accepted"])

    def test_missing_band_and_airflow_is_rejected(self):
        from swiss_sia.evidence_manager import _normalize_ventilation_control_record
        row = self._row(airflow_band="", specific_airflow_m3_h_m2="")
        self.assertFalse(_normalize_ventilation_control_record(row)["accepted"])

    def test_missing_control_class_is_rejected(self):
        from swiss_sia.evidence_manager import _normalize_ventilation_control_record
        self.assertFalse(
            _normalize_ventilation_control_record(self._row(control_class=""))["accepted"])

    def test_ambiguous_demand_control_is_rejected(self):
        """Table 4 distinguishes occupancy and gas-sensor demand control."""
        from swiss_sia.evidence_manager import _normalize_ventilation_control_record
        self.assertFalse(
            _normalize_ventilation_control_record(
                self._row(control_class="demand_controlled")
            )["accepted"]
        )


class SolarProtectionEvidenceTests(unittest.TestCase):
    """The reviewer solar-protection record is accepted only when complete."""

    def _row(self, **overrides):
        row = {
            "project_name": "Demo",
            "facade_or_zone": "South",
            "window_count": "4",
            "solar_protection_type": "venetian_blind",
            "g_total_with_shading": "0.10",
            "reviewer": "Reviewer",
            "review_status": "accepted",
            "source_document": "facade_shading.pdf",
        }
        row.update(overrides)
        return row

    def test_complete_record_is_accepted(self):
        from swiss_sia.evidence_manager import _normalize_solar_protection_record
        record = _normalize_solar_protection_record(self._row())
        self.assertTrue(record["accepted"])
        self.assertEqual(record["window_count_numeric"], 4.0)

    def test_missing_g_total_is_rejected(self):
        from swiss_sia.evidence_manager import _normalize_solar_protection_record
        self.assertFalse(
            _normalize_solar_protection_record(self._row(g_total_with_shading=""))["accepted"])

    def test_missing_type_is_rejected(self):
        from swiss_sia.evidence_manager import _normalize_solar_protection_record
        self.assertFalse(
            _normalize_solar_protection_record(self._row(solar_protection_type=""))["accepted"])

    def test_accepted_windows_are_summed_for_the_project(self):
        from swiss_sia.evidence_manager import accepted_solar_protection_windows
        scan = {"accepted_records": [
            {"project_id": "Demo", "window_count_numeric": 4.0},
            {"project_id": "Demo", "window_count_numeric": 3.0},
            {"project_id": "Other", "window_count_numeric": 9.0},
        ]}
        self.assertEqual(accepted_solar_protection_windows(scan, "Demo"), 7)


if __name__ == "__main__":
    unittest.main()
