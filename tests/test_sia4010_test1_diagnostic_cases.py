# -*- coding: utf-8 -*-
u"""Les cas diagnostiques 1A à 1D du Test 1, une fois enregistrés.

Ils étaient absents du registre alors que 1E y était, ce qui laissait le seul cas
du Test 1 à porter un critère pass/fail sans la base que sa propre définition
exige : « Diagnosefall 1D, jedoch mit Stoffmarkisen-Sonnenschutz ».

Ce que ces tests protègent n'est pas leur présence, mais deux choses qu'un ajout
ultérieur pourrait défaire sans bruit :

* la spécification n'énonce **aucun** critère de comparaison pour 1A à 1D — elle
  demande de livrer des jeux annuels de puissance horaire. Leur donner un champ
  d'évaluation APS reviendrait à inventer une bande, donc à fabriquer un verdict ;
* ils dépendent chacun d'une donnée déléguée. Les déclarer sans exigence les
  ferait paraître prêts alors que le climat de Kloten leur manque.
"""

from __future__ import annotations

import unittest

from swiss_sia.reference_model.sia4010.case_registry import (
    TEST1_DIAGNOSTIC_CASES,
    all_case_capabilities,
    get_case_capability,
)
from swiss_sia.reference_model.sia4010.external_input_manifest import (
    required_external_input_ids,
)
from swiss_sia.reference_model.sia4010.model_scenario import (
    TEST_CASES,
    official_features,
)


#: Les six cas ISO du Test 1, qui ne sont PAS des diagnostics.
CAS_ISO = ("600", "640", "600FF", "900", "940", "900FF")


class Test1DiagnosticCaseRegistrationTests(unittest.TestCase):

    def test_les_quatre_cas_sont_enregistres(self) -> None:
        for case_id in TEST1_DIAGNOSTIC_CASES:
            with self.subTest(case=case_id):
                self.assertIn(case_id, TEST_CASES["test_1"])
                capability = get_case_capability("test_1", case_id)
                self.assertEqual(capability.base_test_id, "1")

    def test_la_chaine_precede_le_cas_quelle_fonde(self) -> None:
        u"""1E dépend de 1D, donc 1D doit être lisible avant lui."""
        cases = TEST_CASES["test_1"]
        for case_id in TEST1_DIAGNOSTIC_CASES:
            self.assertLess(cases.index(case_id), cases.index("1E"), case_id)

    def test_les_six_cas_iso_restent_intacts(self) -> None:
        u"""Ajouter des cas ne doit pas déplacer ni altérer les six normatifs."""
        self.assertEqual(TEST_CASES["test_1"][:6], CAS_ISO)

    def test_aucun_diagnostic_ne_porte_de_champ_devaluation_aps(self) -> None:
        u"""La spécification n'énonce aucun critère pour eux : pas de bande.

        `refs/reference-data/test-1.ref.json` ne porte de valeurs de référence
        que pour les six cas ISO et pour 1E. Un champ d'évaluation sur 1A à 1D
        impliquerait une bande qui n'existe pas.
        """
        for case_id in TEST1_DIAGNOSTIC_CASES:
            with self.subTest(case=case_id):
                capability = get_case_capability("test_1", case_id)
                self.assertEqual(capability.aps_evaluation_scope, "UNAVAILABLE")
                self.assertFalse(capability.aps_evaluation_supported)

    def test_le_cas_1e_garde_son_critere(self) -> None:
        u"""Le contre-exemple : 1E est jugé, lui, et doit le rester."""
        capability = get_case_capability("test_1", "1E")
        self.assertEqual(
            capability.aps_evaluation_scope, "OFFICIAL_CRITERIA_IMPLEMENTED"
        )

    def test_aucun_diagnostic_nest_declare_generable(self) -> None:
        u"""Aucun générateur VE ne les lie ; le registre ne doit pas le suggérer."""
        for case_id in TEST1_DIAGNOSTIC_CASES:
            with self.subTest(case=case_id):
                capability = get_case_capability("test_1", case_id)
                self.assertEqual(capability.generation_status, "NOT_IMPLEMENTED")
                self.assertFalse(capability.mutation_supported)
                self.assertFalse(capability.runtime_qualification_supported)

    def test_le_blocage_nomme_la_chaine_et_son_referentiel(self) -> None:
        for case_id in TEST1_DIAGNOSTIC_CASES:
            with self.subTest(case=case_id):
                capability = get_case_capability("test_1", case_id)
                self.assertEqual(
                    capability.blocker_code,
                    "TEST1_DIAGNOSTIC_CHAIN_GENERATOR_NOT_IMPLEMENTED",
                )
                self.assertIn(
                    "test-1.diagnostics.ref.json", capability.blocker_detail
                )
                self.assertIn("NO comparison criterion",
                              capability.blocker_detail)

    def test_chaque_diagnostic_exige_ses_donnees_deleguees(self) -> None:
        u"""Rendre un tuple vide les ferait paraître autonomes.

        Le climat de Zürich-Kloten est précisément ce que le maillon 1A ajoute
        au cas 600 ; aucun des quatre ne peut s'en passer.
        """
        for case_id in TEST1_DIAGNOSTIC_CASES:
            with self.subTest(case=case_id):
                requis = required_external_input_ids("test_1", case_id)
                self.assertIn("sia2028_dry_normal_zurich_kloten", requis)
                self.assertIn("iso52016_2017_chapter7_test_cell", requis)

    def test_sia_2024_apparait_au_maillon_qui_lintroduit(self) -> None:
        u"""1C tire son infiltration de SIA 2024:2021, 1A et 1B non.

        « Infiltration 0.15 m3/(h*m2) gemäss SIA 2024:2021 » : l'exigence naît
        en 1C et se propage. La déclarer dès 1A marquerait deux cas bloqués sur
        une donnée dont ils ne dépendent pas.
        """
        for case_id in ("1A", "1B"):
            with self.subTest(case=case_id):
                self.assertNotIn(
                    "sia2024_office_3_1_standard_profiles",
                    required_external_input_ids("test_1", case_id),
                )
        for case_id in ("1C", "1D", "1E"):
            with self.subTest(case=case_id):
                self.assertIn(
                    "sia2024_office_3_1_standard_profiles",
                    required_external_input_ids("test_1", case_id),
                )

    def test_les_six_cas_iso_nexigent_toujours_rien(self) -> None:
        u"""Ils tournent sur la météo DRYCOLD fournie avec le Test 1."""
        for case_id in CAS_ISO:
            with self.subTest(case=case_id):
                self.assertEqual(
                    required_external_input_ids("test_1", case_id), ()
                )

    def test_seul_1e_active_la_protection_solaire(self) -> None:
        u"""Le store est ce que 1E ajoute à 1D, et rien d'autre ne l'a."""
        for case_id in TEST1_DIAGNOSTIC_CASES + CAS_ISO:
            with self.subTest(case=case_id):
                features = official_features("test_1", case_id)
                self.assertFalse(features["solar_protection"], case_id)
        self.assertTrue(
            official_features("test_1", "1E")["solar_protection"]
        )

    def test_les_diagnostics_sont_des_cas_pilotes_pas_en_flottement(
        self,
    ) -> None:
        u"""La chaîne part du cas 600, qui porte des consignes 20/27 °C."""
        for case_id in TEST1_DIAGNOSTIC_CASES:
            with self.subTest(case=case_id):
                features = official_features("test_1", case_id)
                self.assertTrue(features["ideal_heating"])
                self.assertTrue(features["ideal_cooling"])
                self.assertTrue(features["infiltration"])

    def test_le_nombre_total_de_cas_enregistres(self) -> None:
        u"""34, et non 30 : quatre maillons ajoutés à `test_1`."""
        self.assertEqual(len(all_case_capabilities()), 34)

    def test_le_nombre_de_variantes_est_inchange(self) -> None:
        u"""Ce sont des cas de `test_1`, pas de nouvelles variantes.

        Si ce compte bougeait, la matrice des huit classes de validation aurait
        changé — ce qui serait une décision normative, pas un ajout de cas.
        """
        self.assertEqual(len(TEST_CASES), 24)


if __name__ == "__main__":
    unittest.main()
