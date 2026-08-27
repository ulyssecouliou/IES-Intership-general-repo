# -*- coding: utf-8 -*-
"""Tests de l assistant de preuves SIA 380/2.

Le danger vise est nomme : une FAUSSE DECLARATION DE CONFORMITE. Elle peut
naitre de six facons, et il y a un test pour chacune :

    - accepter un dossier incomplet ;
    - reprendre le statut demande sans le recalculer ;
    - pre-remplir une donnee que le logiciel ne peut pas demontrer ;
    - recopier la meteo detectee dans la meteo revue ;
    - convertir une sortie APS absente en zero ;
    - confondre NON_APPLICABLE, NOT_CHECKABLE et une donnee manquante.

S y ajoute la garde de liaison : « Room units heating load » doit l emporter
sur la serie steady state, defaut deja rencontre et corrige.
"""

from __future__ import annotations

import csv
import io
import json
import os
import unittest
from tempfile import TemporaryDirectory

from swiss_sia import evidence_wizard as w


def _dossier_complet(**surcharges):
    """Dossier minimal qui DOIT etre acceptable, avant surcharge."""
    reponses = {
        "project_id": "ZOER_32_C1_TEST",
        "building_status": "EXISTING_BUILDING",
        "weather_basis": "SIA 2028 DRY",
        "weather_file": "DRYCOLD_IESVE.epw",
        "weather_source_authority": "SIA 2028 C2:2023 project climate brief",
        "weather_use_case": "SIA3802_COOLING_NEED",
        "weather_scenario_period": "2035 RCP8.5 DRY",
        "location": "Zurich Kloten",
        "altitude_m": "426",
        "location_source": "Approved project climate brief, p. 2",
        "altitude_source": "Approved project survey, p. 3",
        "review_status": "accepted",
        "reviewer": "U. Couliou",
        "reviewer_role": "Responsible energy specialist",
        "reviewer_organisation": "IES",
        "reviewer_competence_basis": "Building simulation engineer",
        "reviewer_acceptance_scope": "Weather, model inputs and reported reserves",
        "review_date": "2026-08-10",
        "source_document": "Cahier des charges v3",
        "source_reference": "clause 4.2",
        "notes": "",
        "ventilation_strategy": "NATURAL_ONLY",
        "ventilation_justification": "Aucune CTA au projet, confirme MEP.",
        "ventilation_scope": "All conditioned rooms",
        "ventilation_flow_source": "",
        "lighting_scope": "OUT_OF_SCOPE",
        "lighting_power_source": "",
        "lighting_scope_justification": "Lighting excluded by the approved brief.",
        "aps_outputs_required": "NO",
        "aps_outputs_justification": "Aucun systeme aeraulique modelise.",
        "system_power_source": "Not applicable: no modelled fan/pump system.",
        "assumptions_status": "NO_UNRESOLVED_ASSUMPTIONS",
        "assumptions_register": "Climate brief v3, assumptions register section 7",
        "report_use_acknowledgement": "ENGINEERING_ASSESSMENT_ONLY",
    }
    reponses.update(surcharges)
    return reponses


class TestValidationDesChamps(unittest.TestCase):
    """Controle des valeurs saisies, champ par champ."""

    def test_un_choix_hors_liste_est_refuse(self):
        self.assertIsNotNone(w.valider_champ("building_status", "MAYBE"))

    def test_un_choix_valide_passe(self):
        self.assertIsNone(w.valider_champ("building_status", "NEW_BUILDING"))

    def test_une_altitude_non_numerique_est_refusee(self):
        self.assertIsNotNone(w.valider_champ("altitude_m", "environ 400"))

    def test_une_altitude_a_virgule_est_acceptee(self):
        self.assertIsNone(w.valider_champ("altitude_m", "426,5"))

    def test_une_date_mal_formee_est_refusee(self):
        self.assertIsNotNone(w.valider_champ("review_date", "10/08/2026"))

    def test_un_champ_vide_nest_pas_refuse_a_la_saisie(self):
        """L incompletude se traite au moment d accepter, pas a la frappe :
        sinon on ne peut pas enregistrer un dossier en cours."""
        for nom in w.noms_des_champs():
            self.assertIsNone(w.valider_champ(nom, ""))

    def test_un_champ_inconnu_leve(self):
        """Rendre un dict vide laisserait croire a un champ sans contrainte."""
        with self.assertRaises(KeyError):
            w.champ("champ_invente")


class TestRefusDAcceptation(unittest.TestCase):
    """Le coeur : `accepted` ne s obtient pas a moitie."""

    def test_un_dossier_complet_et_confirme_est_accepte(self):
        resultat = w.evaluer_acceptation(_dossier_complet(), True)
        self.assertTrue(resultat["accepte"], resultat["motifs_de_refus"])
        self.assertEqual(resultat["statut_effectif"], w.ACCEPTE)

    def test_sans_confirmation_explicite_le_statut_retombe(self):
        resultat = w.evaluer_acceptation(_dossier_complet(), False)
        self.assertFalse(resultat["accepte"])
        self.assertEqual(resultat["statut_effectif"], w.EN_ATTENTE)

    def test_le_statut_demande_nest_jamais_repris_tel_quel(self):
        """Fail-closed : demander `accepted` sur un dossier vide ne l obtient
        pas. C est le recalcul qui decide, jamais la saisie."""
        resultat = w.evaluer_acceptation({"review_status": "accepted"}, True)
        self.assertEqual(resultat["statut_effectif"], w.EN_ATTENTE)

    def test_chaque_champ_obligatoire_bloque_a_lui_seul(self):
        for nom in [
            c["nom"]
            for c in w.CHAMPS
            if c["obligatoire_pour_accepter"] and c["nom"] != "review_status"
        ]:
            resultat = w.evaluer_acceptation(_dossier_complet(**{nom: ""}), True)
            self.assertFalse(resultat["accepte"], nom)
            self.assertIn(nom, resultat["manquants"])

    def test_un_eclairage_dans_le_perimetre_exige_sa_source(self):
        """Sans source, la puissance devrait etre deduite du gain
        Miscellaneous — c est-a-dire inventee."""
        resultat = w.evaluer_acceptation(
            _dossier_complet(lighting_scope="IN_SCOPE", lighting_power_source=""), True
        )
        self.assertFalse(resultat["accepte"])
        self.assertTrue(
            any("source de la puissance" in m for m in resultat["motifs_de_refus"])
        )

    def test_une_ventilation_mecanique_exige_la_source_des_debits(self):
        resultat = w.evaluer_acceptation(
            _dossier_complet(
                ventilation_strategy="MECHANICAL_PRESENT", ventilation_flow_source=""
            ),
            True,
        )
        self.assertFalse(resultat["accepte"])
        self.assertTrue(any("debits" in m for m in resultat["motifs_de_refus"]))

    def test_des_sorties_declarees_inutiles_exigent_leur_justification(self):
        resultat = w.evaluer_acceptation(
            _dossier_complet(aps_outputs_justification=""), True
        )
        self.assertFalse(resultat["accepte"])

    def test_under_review_bloque_lacceptation(self):
        for nom in ("ventilation_strategy", "lighting_scope", "aps_outputs_required"):
            resultat = w.evaluer_acceptation(
                _dossier_complet(**{nom: "UNDER_REVIEW"}), True
            )
            self.assertFalse(resultat["accepte"], nom)

    def test_une_valeur_invalide_bloque_meme_si_le_champ_est_rempli(self):
        resultat = w.evaluer_acceptation(_dossier_complet(review_date="10/08/2026"), True)
        self.assertFalse(resultat["accepte"])
        self.assertIn("review_date", resultat["erreurs"])


class TestPrefill(unittest.TestCase):
    """On ne pre-remplit que ce qui est techniquement demontre."""

    def test_seul_le_project_id_est_prerempli(self):
        valeurs = w.prefill(
            {
                "project_id": "ZOER_32_C1_TEST",
                "detected_weather_file": "DRYCOLD_IESVE.epw",
                "total_area_m2": 392.5,
            }
        )
        self.assertEqual(valeurs["project_id"], "ZOER_32_C1_TEST")
        for nom in (
            "location",
            "altitude_m",
            "weather_basis",
            "reviewer",
            "source_document",
            "ventilation_strategy",
        ):
            self.assertEqual(valeurs[nom], "", nom)

    def test_la_meteo_detectee_nest_pas_recopiee_dans_la_meteo_revue(self):
        """Les confondre reviendrait a faire valider par le logiciel ce que
        seul un humain peut declarer."""
        valeurs = w.prefill({"detected_weather_file": "DRYCOLD_IESVE.epw"})
        self.assertEqual(valeurs["weather_file"], "")

    def test_le_statut_initial_est_pending(self):
        self.assertEqual(w.prefill({})["review_status"], w.EN_ATTENTE)

    def test_un_fait_absent_est_non_verifiable_pas_zero(self):
        faits = w.faits_techniques({})
        self.assertEqual(faits["total_heating_kwh"]["valeur"], w.NON_FOURNI)
        self.assertEqual(faits["total_heating_kwh"]["statut"], w.NON_VERIFIABLE)

    def test_la_meteo_detectee_porte_sa_reserve(self):
        faits = w.faits_techniques({"detected_weather_file": "DRYCOLD_IESVE.epw"})
        self.assertIn("PAS", faits["detected_weather_file"]["note"])

    def test_le_chauffage_cite_sa_liaison(self):
        """La provenance de la grandeur doit rester lisible : c est elle qui
        distingue la bonne serie de la serie steady state."""
        faits = w.faits_techniques({"total_heating_kwh": 9586.63})
        self.assertIn("Room units heating load", faits["total_heating_kwh"]["note"])


class TestCorrespondanceMeteo(unittest.TestCase):
    """Une correspondance technique ne vaut pas approbation du climat."""

    def test_deux_fichiers_identiques_correspondent(self):
        resultat = w.correspondance_meteo("DRYCOLD_IESVE.epw", "DRYCOLD_IESVE.epw")
        self.assertEqual(resultat["statut"], w.PASS_TECHNIQUE)
        self.assertIn("RIEN", resultat["note"])

    def test_le_chemin_complet_est_reduit_au_nom(self):
        resultat = w.correspondance_meteo(
            r"C:\Weather\DRYCOLD_IESVE.epw", "DRYCOLD_IESVE.epw"
        )
        self.assertEqual(resultat["statut"], w.PASS_TECHNIQUE)

    def test_deux_fichiers_differents_sont_un_defaut_de_modele(self):
        resultat = w.correspondance_meteo("DRYCOLD_IESVE.epw", "KLO_dry.epw")
        self.assertEqual(resultat["statut"], w.DEFAUT_MODELE)

    def test_sans_meteo_revue_le_controle_est_non_verifiable(self):
        resultat = w.correspondance_meteo("DRYCOLD_IESVE.epw", "")
        self.assertEqual(resultat["statut"], w.NON_VERIFIABLE)
        self.assertEqual(resultat["revu"], w.NON_FOURNI)

    def test_sans_meteo_detectee_le_controle_est_non_verifiable(self):
        self.assertEqual(
            w.correspondance_meteo("", "KLO.epw")["statut"], w.NON_VERIFIABLE
        )


class TestEcritureCsv(unittest.TestCase):
    """Sauvegarde, colonnes, et statut recalcule."""

    def test_le_csv_porte_les_colonnes_du_gabarit_en_tete(self):
        with TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "preuves.csv")
            w.ecrire_csv(chemin, _dossier_complet(), w.ACCEPTE)
            with io.open(chemin, encoding="utf-8") as flux:
                entetes = next(csv.reader(flux))
            self.assertEqual(entetes[: len(w.COLONNES_GABARIT)], list(w.COLONNES_GABARIT))

    def test_un_fichier_existant_est_sauvegarde_avant_ecrasement(self):
        with TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "preuves.csv")
            with io.open(chemin, "w", encoding="utf-8") as flux:
                flux.write("ancien contenu")
            ecriture = w.ecrire_csv(
                chemin, _dossier_complet(), w.ACCEPTE, "20260810_120000"
            )
            self.assertIsNotNone(ecriture["sauvegarde"])
            self.assertTrue(os.path.exists(ecriture["sauvegarde"]))
            with io.open(ecriture["sauvegarde"], encoding="utf-8") as flux:
                self.assertEqual(flux.read(), "ancien contenu")

    def test_sans_fichier_existant_aucune_sauvegarde_nest_creee(self):
        with TemporaryDirectory() as dossier:
            ecriture = w.ecrire_csv(
                os.path.join(dossier, "neuf.csv"), _dossier_complet(), w.EN_ATTENTE
            )
            self.assertIsNone(ecriture["sauvegarde"])

    def test_le_statut_ecrit_est_le_statut_recalcule(self):
        """Meme si la saisie dit `accepted`, c est le statut recalcule qui
        part dans le fichier."""
        with TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "preuves.csv")
            w.ecrire_csv(chemin, _dossier_complet(), w.EN_ATTENTE)
            with io.open(chemin, encoding="utf-8") as flux:
                ligne = next(csv.DictReader(flux))
            self.assertEqual(ligne["review_status"], w.EN_ATTENTE)

    def test_le_dossier_est_cree_au_besoin(self):
        with TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "sia4010_evidence", "p.csv")
            w.ecrire_csv(chemin, _dossier_complet(), w.EN_ATTENTE)
            self.assertTrue(os.path.exists(chemin))


class TestAudit(unittest.TestCase):
    """Le JSON d audit doit dire ce qui manque, et ce qui n a pas ete fait."""

    def _audit(self, **surcharges):
        reponses = _dossier_complet(**surcharges)
        acceptation = w.evaluer_acceptation(reponses, True)
        detecte = {"detected_weather_file": "DRYCOLD_IESVE.epw", "total_area_m2": 392.5}
        return w.construire_audit(
            reponses,
            detecte,
            acceptation,
            w.actions_restantes(reponses, detecte, acceptation),
            "C:/x/preuves.csv",
            None,
            "20260810_120000",
        )

    def test_laudit_declare_quaucune_donnee_ve_na_ete_modifiee(self):
        audit = self._audit()
        self.assertFalse(audit["ve_data_modified"])
        self.assertIn("ne mute rien", audit["ve_data_modified_note"])

    def test_laudit_ne_prononce_ni_conformite_ni_validation(self):
        audit = self._audit()
        self.assertIn("NE constitue ni", audit["purpose"])
        self.assertIn("distinctes", audit["guardrail"])

    def test_laudit_porte_les_champs_manquants(self):
        audit = self._audit(location="")
        self.assertIn("location", audit["missing_fields"])

    def test_laudit_porte_les_deux_meteos_et_leur_correspondance(self):
        audit = self._audit()
        self.assertEqual(audit["weather"]["detected_in_ve"], "DRYCOLD_IESVE.epw")
        self.assertEqual(audit["weather"]["match_status"], w.PASS_TECHNIQUE)

    def test_laudit_distingue_statut_demande_et_statut_effectif(self):
        audit = self._audit(location="")
        self.assertEqual(audit["review"]["requested_status"], w.ACCEPTE)
        self.assertEqual(audit["review"]["effective_status"], w.EN_ATTENTE)

    def test_une_source_absente_est_marquee_non_fournie_pas_vide(self):
        audit = self._audit(ventilation_flow_source="")
        self.assertEqual(audit["sources"]["ventilation_flow_source"], w.NON_FOURNI)

    def test_laudit_secrit_sans_ecraser(self):
        with TemporaryDirectory() as dossier:
            premier = w.ecrire_audit(dossier, self._audit(), "P", "20260810_1")
            second = w.ecrire_audit(dossier, self._audit(), "P", "20260810_2")
            self.assertNotEqual(premier, second)
            self.assertTrue(os.path.exists(premier))
            with io.open(premier, encoding="utf-8") as flux:
                self.assertFalse(json.load(flux)["ve_data_modified"])


class TestVentilationInfiltrationSeule(unittest.TestCase):
    """MODEL-003 : ne jamais creer de ventilation automatiquement."""

    def test_infiltration_seule_est_un_pass_technique_pas_un_defaut(self):
        actions = w.actions_ventilation(
            {
                "ventilation_strategy": "NATURAL_ONLY",
                "ventilation_justification": "Confirme MEP.",
            },
            {"infiltration_only": True, "oa_max_flow": 0.0},
        )
        categories = [a["categorie"] for a in actions]
        self.assertNotIn(w.DEFAUT_MODELE, categories)
        self.assertIn(w.PASS_TECHNIQUE, categories)

    def test_un_debit_nul_est_coherent_avec_linfiltration_seule(self):
        actions = w.actions_ventilation(
            {"ventilation_strategy": "NATURAL_ONLY", "ventilation_justification": "x"},
            {"infiltration_only": True, "oa_max_flow": 0.0},
        )
        self.assertTrue(any("OA_max_flow = 0" in a["constat"] for a in actions))

    def test_un_debit_non_expose_est_une_limite_vescripts(self):
        """Ni un defaut du modele, ni une donnee manquante du client."""
        actions = w.actions_ventilation(
            {"ventilation_strategy": "NATURAL_ONLY"},
            {"infiltration_only": True, "oa_max_flow": None},
        )
        self.assertIn(w.LIMITE_VESCRIPTS, [a["categorie"] for a in actions])

    def test_une_ventilation_mecanique_attendue_est_un_defaut_de_modele(self):
        actions = w.actions_ventilation(
            {"ventilation_strategy": "MECHANICAL_EXPECTED"},
            {"infiltration_only": True, "oa_max_flow": 0.0},
        )
        defauts = [a for a in actions if a["categorie"] == w.DEFAUT_MODELE]
        self.assertEqual(len(defauts), 1)
        self.assertIn("NE PAS creer cet echange", defauts[0]["action"])

    def test_laction_nomme_lendroit_exact_dans_ve(self):
        actions = w.actions_ventilation(
            {"ventilation_strategy": "MECHANICAL_EXPECTED"}, {}
        )
        self.assertTrue(any("Air Exchanges" in a["action"] for a in actions))

    def test_une_strategie_non_tranchee_est_une_donnee_client_manquante(self):
        actions = w.actions_ventilation({}, {"infiltration_only": True})
        self.assertIn(w.DONNEE_CLIENT_MANQUANTE, [a["categorie"] for a in actions])


class TestEclairageAbsent(unittest.TestCase):
    """MODEL-004 : ne jamais transformer Miscellaneous en Lighting."""

    def test_labsence_de_lighting_est_constatee_avec_le_gain_miscellaneous(self):
        actions = w.actions_eclairage(
            {"lighting_scope": "OUT_OF_SCOPE"},
            {"lighting_gain_present": False, "misc_gain_w_m2": 5.0},
        )
        self.assertTrue(any("5.0 W/m2" in a["constat"] for a in actions))

    def test_la_conversion_automatique_est_explicitement_interdite(self):
        actions = w.actions_eclairage(
            {"lighting_scope": "OUT_OF_SCOPE"},
            {"lighting_gain_present": False, "misc_gain_w_m2": 5.0},
        )
        self.assertTrue(any("NE PAS convertir" in a["action"] for a in actions))

    def test_hors_perimetre_le_controle_est_non_applicable(self):
        actions = w.actions_eclairage(
            {"lighting_scope": "OUT_OF_SCOPE"}, {"lighting_gain_present": False}
        )
        self.assertIn(w.NON_APPLICABLE, [a["categorie"] for a in actions])

    def test_dans_le_perimetre_cest_une_donnee_client_manquante(self):
        """Pas un defaut du modele : le client n a pas fourni la puissance."""
        actions = w.actions_eclairage(
            {"lighting_scope": "IN_SCOPE"}, {"lighting_gain_present": False}
        )
        self.assertIn(w.DONNEE_CLIENT_MANQUANTE, [a["categorie"] for a in actions])
        self.assertTrue(any("NE PAS deduire" in a["action"] for a in actions))


class TestSortiesApsManquantes(unittest.TestCase):
    """SIM-003 : une sortie absente ne vaut jamais zero."""

    ABSENTES = ("lighting", "fan", "pump", "auxiliary", "heating_coil", "cooling_coil")

    def test_non_applicable_quand_le_systeme_nen_produit_pas(self):
        actions = w.actions_sorties_aps({"aps_outputs_required": "NO"}, self.ABSENTES)
        self.assertEqual([a["categorie"] for a in actions], [w.NON_APPLICABLE])
        self.assertIn("ne valent pas zero", actions[0]["action"])

    def test_sortie_non_activee_quand_elles_sont_necessaires(self):
        actions = w.actions_sorties_aps({"aps_outputs_required": "YES"}, self.ABSENTES)
        categories = set(a["categorie"] for a in actions)
        self.assertEqual(categories, {w.SORTIE_NON_ACTIVEE})
        self.assertNotIn(w.NON_APPLICABLE, categories)

    def test_chaque_sortie_recoit_son_emplacement_dans_apachesim(self):
        actions = w.actions_sorties_aps({"aps_outputs_required": "YES"}, self.ABSENTES)
        for grandeur in self.ABSENTES:
            self.assertTrue(any(grandeur in a["constat"] for a in actions), grandeur)
        self.assertTrue(any("ApacheSim > Results" in a["action"] for a in actions))

    def test_non_tranche_reste_non_verifiable(self):
        """Different de NON_APPLICABLE : on n a pas decide, on n a pas su."""
        actions = w.actions_sorties_aps({}, self.ABSENTES)
        self.assertEqual([a["categorie"] for a in actions], [w.NON_VERIFIABLE])

    def test_aucune_action_ne_propose_de_combler_par_zero(self):
        for besoin in ("YES", "NO", ""):
            for action in w.actions_sorties_aps(
                {"aps_outputs_required": besoin}, self.ABSENTES
            ):
                self.assertNotIn("= 0", action["action"])

    def test_sans_sortie_absente_le_controle_passe(self):
        actions = w.actions_sorties_aps({"aps_outputs_required": "YES"}, ())
        self.assertEqual([a["categorie"] for a in actions], [w.PASS_TECHNIQUE])


class TestDistinctionDesCategories(unittest.TestCase):
    """NON_APPLICABLE, NOT_CHECKABLE et donnee manquante sont distincts."""

    def test_les_neuf_categories_sont_distinctes(self):
        self.assertEqual(len(set(w.CATEGORIES)), len(w.CATEGORIES))

    def test_chaque_categorie_est_expliquee(self):
        for categorie in w.CATEGORIES:
            self.assertIn(categorie, w.EXPLICATION_DES_CATEGORIES)
            self.assertTrue(w.EXPLICATION_DES_CATEGORIES[categorie])

    def test_non_applicable_et_non_verifiable_ne_sont_pas_synonymes(self):
        self.assertNotEqual(w.NON_APPLICABLE, w.NON_VERIFIABLE)
        self.assertNotEqual(
            w.EXPLICATION_DES_CATEGORIES[w.NON_APPLICABLE],
            w.EXPLICATION_DES_CATEGORIES[w.NON_VERIFIABLE],
        )

    def test_un_pass_technique_ne_vaut_ni_conformite_ni_validation(self):
        explication = w.EXPLICATION_DES_CATEGORIES[w.PASS_TECHNIQUE]
        self.assertIn("380/2", explication)
        self.assertIn("4010", explication)

    def test_un_dossier_incomplet_rend_le_verdict_sia_impossible(self):
        reponses = _dossier_complet(location="")
        acceptation = w.evaluer_acceptation(reponses, True)
        actions = w.actions_restantes(reponses, {}, acceptation)
        self.assertEqual(actions[-1]["categorie"], w.VERDICT_SIA_IMPOSSIBLE)

    def test_le_verdict_nest_jamais_prononce_meme_dossier_complet(self):
        """L assistant ne conclut pas a la conformite : il constate qu il n a
        rien de bloquant, et laisse la decision a un ingenieur."""
        reponses = _dossier_complet()
        acceptation = w.evaluer_acceptation(reponses, True)
        actions = w.actions_restantes(
            reponses,
            {
                "detected_weather_file": "DRYCOLD_IESVE.epw",
                "ventilation": {"infiltration_only": True, "oa_max_flow": 0.0},
                "lighting": {"lighting_gain_present": False},
            },
            acceptation,
        )
        conclusion = actions[-1]
        self.assertNotEqual(conclusion["categorie"], w.PASS_TECHNIQUE)
        self.assertIn("ne le prononce pas", conclusion["action"])


class TestAbsenceDeMutationVE(unittest.TestCase):
    """Rien dans ce noyau ne doit pouvoir ecrire dans VE."""

    def test_le_noyau_nimporte_pas_iesve(self):
        chemin = os.path.abspath(w.__file__).replace(".pyc", ".py")
        with io.open(chemin, encoding="utf-8") as flux:
            for numero, ligne in enumerate(flux, 1):
                nu = ligne.strip()
                self.assertFalse(nu.startswith(("import iesve", "from iesve")), numero)

    def test_le_noyau_nappelle_aucun_setter_ve(self):
        chemin = os.path.abspath(w.__file__).replace(".pyc", ".py")
        with io.open(chemin, encoding="utf-8") as flux:
            source = flux.read()
        for interdit in (
            "set_properties",
            "create_material",
            "add_layer",
            "create_apache_system",
            "assign_construction",
        ):
            self.assertNotIn(interdit, source, interdit)


class TestPrioriteDeLaLiaisonChauffage(unittest.TestCase):
    """« Room units heating load » doit l emporter sur la serie steady state.

    Le defaut a deja ete rencontre : la serie steady state precede la bonne
    dans le catalogue APS, et un choix par ordre d apparition la retenait.
    """

    def test_la_serie_steady_state_ne_gagne_pas(self):
        from swiss_sia.simulation_results import find_room_sensible_load_variable

        variables = [
            {
                "aps_varname": "Room units steady state htg load",
                "display_name": "Steady state heating plant load",
                "model_level": "z",
                "resolved_metric_unit": "kW",
            },
            {
                "aps_varname": "Room units heating load",
                "display_name": "Heating plant sensible load",
                "model_level": "z",
                "resolved_metric_unit": "kW",
            },
        ]
        binding = find_room_sensible_load_variable(variables, "heating")
        self.assertIsNotNone(binding)
        self.assertEqual(binding[0], "Room units heating load")

    def test_la_provenance_du_chauffage_est_citee_dans_les_faits(self):
        note = w.faits_techniques({"total_heating_kwh": 1.0})["total_heating_kwh"]["note"]
        self.assertIn("Room units heating load", note)
        self.assertIn("steady state", note)


if __name__ == "__main__":
    unittest.main()
