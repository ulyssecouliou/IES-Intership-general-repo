"""Tests for the Test 1 diagnostic chain bundles 1A to 1E.

The chain feeds case 1E, the only pass/fail case of Test 1. A wrong value here
would not crash: it would produce a model that runs, compares against a real
reference band, and reports a credible false verdict. So these tests spend their
effort on two things.

First, that every applied value equals the frozen reference rather than a
constant retyped into the builder. Second, that what the published data does not
determine is reported as a blocker instead of filled in -- and that a case
needing one is never described as ready.
"""

import json
import unittest
from pathlib import Path

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.native_ui import ModelBuilderController
from swiss_sia.reference_model.sia4010.test1_diagnostic_bundle import (
    BLOCKER_AWNING,
    DIAGNOSTIC_CHAIN,
    INFILTRATION_M3_H_M2_TO_L_S_M2,
    KLOTEN_WEATHER_FILENAMES,
    build_test1_diagnostic_bundle,
    load_diagnostics_reference,
    resolve_kloten_weather,
)

ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = ROOT / ".codex_tmp"


class Test1DiagnosticBundleTests(unittest.TestCase):

    def setUp(self):
        self.project = TEMP_ROOT / self._testMethodName
        self.project.mkdir(parents=True, exist_ok=True)
        self.weather = self.project / "DRYCOLD.epw"
        self.weather.write_text("diagnostic chain baseline\n", encoding="utf-8")
        self.kloten = self.project / "KLOTEN.epw"
        self.kloten.write_text("SIA 2028 DRY normal Kloten\n", encoding="utf-8")
        self.reference = load_diagnostics_reference(ROOT)

    def _build(self, case_id, *, with_kloten=True):
        return build_test1_diagnostic_bundle(
            self.project,
            ROOT,
            case_id,
            weather_file=self.weather,
            kloten_weather_file=self.kloten if with_kloten else None,
        )

    @staticmethod
    def _read(path):
        with Path(path).open(encoding="utf-8") as handle:
            return json.load(handle)

    def _value(self, bloc, cle):
        return self.reference["parametres"][bloc][cle]["valeur"]

    # -- the chain itself ---------------------------------------------------

    def test_an_unknown_case_is_refused(self):
        with self.assertRaises(ConfigurationError):
            self._build("600")

    def test_the_chain_is_cumulative(self):
        """1D must apply 1A to 1C too, or it is not the case the spec defines."""

        receipt = self._build("1D")
        assets = self._read(receipt.asset_manifest_path)
        applied = assets["metadata"]["diagnostic_chain_applied"]
        self.assertEqual(applied, ["1A", "1B", "1C", "1D"])

    def test_1a_alone_touches_only_the_climate(self):
        receipt = self._build("1A")
        assets = self._read(receipt.asset_manifest_path)
        self.assertEqual(assets["metadata"]["diagnostic_chain_applied"], ["1A"])
        self.assertEqual(assets["metadata"]["diagnostic_chain_blocked"], [])
        self.assertEqual(receipt.status, "READY_FOR_PROVISIONAL_RUNTIME_QUALIFICATION")

    # -- link 1A ------------------------------------------------------------

    def test_the_kloten_climate_replaces_drycold(self):
        receipt = self._build("1A")
        parameters = self._read(receipt.config_path)["parameters"]
        self.assertEqual(parameters["weather_file"]["value"], str(self.kloten))
        self.assertIn("Kloten", parameters["weather_station"]["value"])

    def test_a_missing_kloten_file_blocks_instead_of_keeping_denver(self):
        """Silently keeping DRYCOLD would label a Denver result as Kloten."""

        receipt = self._build("1A", with_kloten=False)
        self.assertEqual(receipt.status, "BLOCKED_DIAGNOSTIC_CHAIN")
        audit = self._read(receipt.audit_path)
        blocked = {item["id"] for item in audit["chain_blocked"]}
        self.assertIn("TEST1_DIAGNOSTIC_KLOTEN_WEATHER_NOT_SUPPLIED", blocked)
        parameters = self._read(receipt.config_path)["parameters"]
        self.assertNotIn("Kloten", parameters["weather_station"]["value"])

    def test_a_kloten_path_that_does_not_exist_blocks(self):
        receipt = build_test1_diagnostic_bundle(
            self.project,
            ROOT,
            "1A",
            weather_file=self.weather,
            kloten_weather_file=self.project / "absent.epw",
        )
        audit = self._read(receipt.audit_path)
        blocked = {item["id"] for item in audit["chain_blocked"]}
        self.assertIn("TEST1_DIAGNOSTIC_KLOTEN_WEATHER_MISSING_FILE", blocked)

    # -- link 1B ------------------------------------------------------------

    def test_the_window_comes_from_the_frozen_reference(self):
        """Not from a constant retyped here: the values are read back from it."""

        receipt = self._build("1B")
        parameters = self._read(receipt.config_path)["parameters"]
        self.assertEqual(
            parameters["project_glazing_g_value"]["value"],
            self._value("vitrage", "g_total"),
        )
        self.assertEqual(
            parameters["project_visible_light_transmittance"]["value"],
            self._value("vitrage", "transmission_visible"),
        )
        self.assertEqual(
            parameters["project_window_u_w_m2k"]["value"],
            self._value("vitrage", "u_vitrage_w_m2k"),
        )

    def test_the_window_also_lands_on_the_construction(self):
        receipt = self._build("1B")
        assets = self._read(receipt.asset_manifest_path)
        glazing = next(
            item for item in assets["constructions"] if item["key"] == "external_glazing"
        )
        self.assertEqual(
            glazing["properties"]["g_value"]["value"],
            self._value("vitrage", "g_total"),
        )

    def test_the_u_value_matches_the_iso15099_winter_block(self):
        """The two official sources agree; an earlier claim of a typo was wrong.

        The documentation reports the same window under two standard families
        and the U differs between them. The specification quotes the ISO 15099
        winter figure. Comparing it against the EN ISO 52022-3 reference block
        is what made a difference of standard look like a contradiction.
        """

        receipt = self._build("1B")
        parameters = self._read(receipt.config_path)["parameters"]
        concordance = self.reference["concordance_du_u_vitrage"]
        self.assertEqual(concordance["norme_concordante"], "iso_15099_conditions_hiver")
        self.assertEqual(
            parameters["project_window_u_w_m2k"]["value"],
            concordance["valeur"],
        )

    # -- link 1C ------------------------------------------------------------

    def test_the_conversion_factor_is_proven_by_the_baseline(self):
        """The unit of the VE flow is derived, not assumed.

        The case-600 baseline carries the same infiltration twice: 1.107
        m3/(h m2) in the configuration and 0.3075 in the asset manifest. That
        the ratio is exactly 3.6 is what identifies the VE unit as litres per
        second per square metre. If this ever stops holding, the 1C conversion
        is wrong and must not be trusted.
        """

        baseline = build_test1_diagnostic_bundle(
            self.project,
            ROOT,
            "1A",
            weather_file=self.weather,
            kloten_weather_file=self.kloten,
        )
        parameters = self._read(baseline.config_path)["parameters"]
        assets = self._read(baseline.asset_manifest_path)
        exchange = next(
            item for item in assets["air_exchanges"] if item["key"] == "infiltration"
        )
        m3_h_m2 = parameters["infiltration_m3_h_m2"]["value"]
        l_s_m2 = exchange["properties"]["max_flow"]["value"]
        self.assertAlmostEqual(m3_h_m2 / INFILTRATION_M3_H_M2_TO_L_S_M2, l_s_m2, places=6)

    def test_the_adjusted_infiltration_is_converted_not_copied(self):
        receipt = self._build("1C")
        parameters = self._read(receipt.config_path)["parameters"]
        assets = self._read(receipt.asset_manifest_path)
        expected = self._value("infiltration", "debit_m3_h_m2")
        self.assertEqual(parameters["infiltration_m3_h_m2"]["value"], expected)
        exchange = next(
            item for item in assets["air_exchanges"] if item["key"] == "infiltration"
        )
        self.assertAlmostEqual(
            exchange["properties"]["max_flow"]["value"],
            expected / INFILTRATION_M3_H_M2_TO_L_S_M2,
            places=6,
        )

    def test_the_infiltration_object_is_renamed_with_its_value(self):
        """A name still saying 0P41ACH beside a new flow invites stale reuse."""

        receipt = self._build("1C")
        assets = self._read(receipt.asset_manifest_path)
        exchange = next(
            item for item in assets["air_exchanges"] if item["key"] == "infiltration"
        )
        name = exchange["properties"]["name"]["value"]
        self.assertNotIn("0P41ACH", name)
        self.assertIn("0P15", name)

    # -- link 1D ------------------------------------------------------------

    def test_the_stated_gain_densities_are_applied(self):
        receipt = self._build("1D")
        parameters = self._read(receipt.config_path)["parameters"]
        self.assertEqual(
            parameters["equipment_gain_w_m2"]["value"],
            self._value("apports", "appareils_w_m2"),
        )
        self.assertEqual(
            parameters["lighting_gain_w_m2"]["value"],
            self._value("apports", "eclairage_w_m2"),
        )
        self.assertEqual(
            parameters["occupancy_density_m2_person"]["value"],
            self._value("apports", "personnes_m2_par_personne"),
        )

    def test_the_occupant_gain_comes_from_the_authority_extract(self):
        """No met-to-watt convention is needed, and none is invented.

        This link was blocked at first on the grounds that 1.2 met becomes
        watts only through a body-area convention the specification omits. True
        of the specification, wrong as a conclusion: the SIA 2024 authority
        extract states the sensible gain directly in W/m2, so the per-person
        figure is arithmetic on two stated numbers.
        """

        receipt = self._build("1D")
        parameters = self._read(receipt.config_path)["parameters"]
        sensible = self._value("apports", "personnes_gain_sensible_w_m2")
        density = self._value("apports", "personnes_m2_par_personne")
        self.assertAlmostEqual(
            parameters["people_gain_w_person"]["value"],
            sensible * density,
            places=6,
        )
        self.assertNotEqual(parameters["people_gain_w_person"]["value"], 0.0)

    def test_1d_is_now_fully_applied(self):
        """Only the awning blocks the chain, so 1D itself is ready."""

        receipt = self._build("1D")
        assets = self._read(receipt.asset_manifest_path)
        self.assertEqual(
            assets["metadata"]["diagnostic_chain_applied"],
            ["1A", "1B", "1C", "1D"],
        )
        self.assertEqual(assets["metadata"]["diagnostic_chain_blocked"], [])
        self.assertEqual(receipt.status, "READY_FOR_PROVISIONAL_RUNTIME_QUALIFICATION")

    # -- link 1E ------------------------------------------------------------

    def test_the_awning_control_contract_is_built(self):
        """The device is settled, so the contract is produced, not skipped."""

        receipt = self._build("1E")
        assets = self._read(receipt.asset_manifest_path)
        control = assets["metadata"]["diagnostic_fabric_awning_control"]
        self.assertEqual(control["device"], "Soltis 92-2048-Alu")
        self.assertEqual(control["threshold_w_m2"], 150.0)

    def test_the_control_uses_the_deployed_state_properties(self):
        """Reading the retracted column would describe an unshaded window."""

        receipt = self._build("1E")
        assets = self._read(receipt.asset_manifest_path)
        control = assets["metadata"]["diagnostic_fabric_awning_control"]
        blocs = self.reference["fenetre_entiere"]["blocs"]
        ete = blocs["en_iso_52022_3_conditions_ete"]["grandeurs"]["g_total"]
        self.assertEqual(control["combined_g_total"], ete["store_deploye"])
        self.assertNotEqual(control["combined_g_total"], ete["store_rentre"])

    def test_the_unit_conversions_of_the_shade_geometry_are_right(self):
        """Millimetres and centimetres in the document, metres in the contract.

        A wrong factor gives a shade a thousand times too thick and changes
        nothing visible in the JSON.
        """

        receipt = self._build("1E")
        assets = self._read(receipt.asset_manifest_path)
        control = assets["metadata"]["diagnostic_fabric_awning_control"]
        self.assertAlmostEqual(
            control["peripheral_gap_m"],
            self._value("store", "lame_d_air_cm") / 100.0,
            places=9,
        )
        self.assertAlmostEqual(
            control["screen_layer_thickness_m"],
            self._value("store", "epaisseur_couche_mm") / 1000.0,
            places=9,
        )

    def test_1e_keeps_only_the_remaining_technical_optical_reserve(self):
        """Authority-resolved semantics must not remain as blockers."""

        receipt = self._build("1E")
        audit = self._read(receipt.audit_path)
        blocked = {item["id"]: item for item in audit["chain_blocked"]}
        self.assertIn(BLOCKER_AWNING, blocked)
        reserves = blocked[BLOCKER_AWNING]["unresolved_reserves"]
        self.assertNotIn(
            "SIA4010_TEST2A_THRESHOLD_COMPARISON_OPERATOR_NOT_CONFIRMED", reserves
        )
        self.assertNotIn("SIA4010_TEST2A_RELEASE_RULE_NOT_CONFIRMED", reserves)
        self.assertEqual(
            reserves,
            ["VE_TEST2A_COMBINED_G_TOTAL_OPTICAL_MAPPING_NOT_QUALIFIED"],
        )

    def test_the_reuse_of_the_test2a_contract_is_guarded(self):
        """The specification prescribes it; the code checks it still does."""

        definition = next(
            item for item in self.reference["chaine"] if item["cas"] == "1E"
        )
        self.assertIn("2 E1", definition["definition_verbatim_de"])

    def test_case_1e_is_never_reported_ready(self):
        """It carries the only pass/fail criterion; readiness must be earned."""

        receipt = self._build("1E")
        self.assertEqual(receipt.status, "BLOCKED_DIAGNOSTIC_CHAIN")

    # -- claims -------------------------------------------------------------

    def test_no_case_claims_compliance(self):
        for case_id in DIAGNOSTIC_CHAIN:
            with self.subTest(case=case_id):
                receipt = self._build(case_id)
                audit = self._read(receipt.audit_path)
                self.assertFalse(audit["compliance_claim_allowed"])
                self.assertTrue(audit["runtime_qualification_required"])
                assets = self._read(receipt.asset_manifest_path)
                self.assertFalse(assets["metadata"]["compliance_claim_allowed"])

    def test_the_absence_of_a_criterion_is_recorded_for_1a_to_1d(self):
        for case_id in ("1A", "1B", "1C", "1D"):
            with self.subTest(case=case_id):
                audit = self._read(self._build(case_id).audit_path)
                self.assertEqual(
                    audit["acceptance_criterion"],
                    "NONE_STATED_BY_SPECIFICATION",
                )

    def test_case_1e_declares_its_criterion(self):
        audit = self._read(self._build("1E").audit_path)
        self.assertEqual(audit["acceptance_criterion"], "PASS_FAIL_STREUBEREICH")

    def test_the_audit_pins_the_reference_it_used(self):
        """A bundle must say which frozen reference produced its values."""

        audit = self._read(self._build("1C").audit_path)
        self.assertIn("test-1.diagnostics.ref.json", audit["reference"]["path"])
        self.assertEqual(len(audit["reference"]["sha256"]), 64)

    def test_a_missing_frozen_reference_fails_closed(self):
        with self.assertRaises(ConfigurationError):
            build_test1_diagnostic_bundle(
                self.project,
                self.project,
                "1A",
                weather_file=self.weather,
            )


class Test1DiagnosticDispatchTests(unittest.TestCase):
    """The chain must be reachable from VE, not only from a unit test.

    A generator nothing routes to is a generator nobody can run. The controller
    used to return None for these five cases, so preparing 1A produced the
    generic fallback bundle instead of the chain, silently.
    """

    def setUp(self):
        self.project = TEMP_ROOT / self._testMethodName
        self.project.mkdir(parents=True, exist_ok=True)

    def _prepare(self, case_id):
        return ModelBuilderController.prepare_supported_mvp_bundle(
            self.project, ROOT, "SIA4010_OFFICIAL", "test_1", case_id
        )

    def test_every_diagnostic_case_is_dispatched(self):
        for case_id in DIAGNOSTIC_CHAIN:
            with self.subTest(case=case_id):
                receipt = self._prepare(case_id)
                self.assertIsNotNone(receipt, case_id)

    def test_the_six_iso_cases_still_route_to_their_own_builders(self):
        """Widening the guard must not capture the cases it did not own."""

        for case_id in ("600", "640", "600FF", "900", "940", "900FF"):
            with self.subTest(case=case_id):
                receipt = self._prepare(case_id)
                self.assertIsNotNone(receipt)
                self.assertNotIn("DIAGNOSTIC", str(receipt.status))

    def test_an_unrelated_case_is_still_declined(self):
        self.assertIsNone(
            ModelBuilderController.prepare_supported_mvp_bundle(
                self.project, ROOT, "SIA4010_OFFICIAL", "test_2A", "2A"
            )
        )

    def test_the_kloten_resolver_prefers_the_project_folder(self):
        """An operator who dropped a file in the project meant it."""

        local = self.project / KLOTEN_WEATHER_FILENAMES[0]
        local.write_text("operator supplied\n", encoding="utf-8")
        found, searched = resolve_kloten_weather(self.project, ROOT)
        self.assertEqual(found, local)
        self.assertEqual(searched[0], str(local))

    def test_the_resolver_names_where_it_looked(self):
        """A failure that cannot say where it searched is hard to act on."""

        empty = self.project / "nowhere"
        empty.mkdir(exist_ok=True)
        _found, searched = resolve_kloten_weather(empty, empty)
        self.assertTrue(searched)
        self.assertTrue(all(isinstance(item, str) for item in searched))


if __name__ == "__main__":
    unittest.main()
