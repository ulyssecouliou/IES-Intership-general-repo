# -*- coding: utf-8 -*-
"""Tests of `engine/test7_engine.py` — Test 7, validation class 5.

Two families, as for Test 1:

1. **Reproduction of references.** The eleven bands of the engine must reproduce
   exactly the columns `Mittelwert / Obere Grenze / Untere Grenze` from the
   official workbook. This check also runs WITHOUT the workbook, against the
   frozen JSON, to remain executable in CI.

2. **Mutation resistance.** Each test fails if a plausible but wrong
   implementation were written: non-contributing programme counted as zero,
   floor-at-zero applied by default, missing quantity counted as passed,
   Diagnosegrössen entering the verdict.
"""

import io
import os

import pytest

from engine import scatter_band
from engine import test7_engine as moteur

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))


@pytest.fixture(scope="module")
def reference():
    if not os.path.exists(moteur.CHEMIN_REFERENCE_DEFAUT):
        pytest.skip("référence Test 7 absente : %s" % moteur.CHEMIN_REFERENCE_DEFAUT)
    return moteur.charger_reference()


# FICTIONAL irradiance provenance, only for positive controls: it
# lifts the PV lock without claiming to describe a real source. No test
# must use it to assert that an irradiance exists.
SOURCE_FICTIVE = "source fictive de test -- ne décrit aucune donnée réelle"


@pytest.fixture(scope="module")
def candidat_parfait(reference):
    """Fictional candidate placed exactly at the mean of each band.

    It MUST pass: it is the centre of the band. Used as a positive control.
    """
    return dict((g["libelle_de"], g["moyenne"]) for g in reference["grandeurs"])


# --------------------------------------------------------------------------
# 1. Reproduction of references
# --------------------------------------------------------------------------


def test_onze_grandeurs_a_bande(reference):
    """The workbook carries 11 banded lines: 5 cold, 5 hot, 1 PV."""
    assert len(reference["grandeurs"]) == 11


def test_les_bandes_du_json_sont_coherentes_avec_leurs_contributeurs(reference):
    """Full recomputation from per-programme values.

    If the frozen JSON had been edited by hand, this test would catch it.
    """
    for g in reference["grandeurs"]:
        contributions = moteur.valeurs_contributrices(g)
        bande = scatter_band.build_band(contributions, floor_at_zero=g["plancher_a_zero"])
        assert abs(bande.mean - g["moyenne"]) < 1e-9, g["libelle_de"]
        assert abs(bande.upper_bound - g["borne_haute"]) < 1e-9, g["libelle_de"]
        assert abs(bande.lower_bound - g["borne_basse"]) < 1e-9, g["libelle_de"]


def test_le_jeu_de_contributeurs_varie_reellement(reference):
    """GHJ, GHIJ, GHI — if everything were GHIJ, the workbook would have been misread."""
    jeux = set(tuple(g["contributeurs"]) for g in reference["grandeurs"])
    assert len(jeux) > 1, jeux
    assert ("G", "H", "J") in jeux
    assert ("G", "H", "I", "J") in jeux


def test_le_plancher_a_zero_est_ponctuel_pas_general(reference):
    """Only two quantities carry MAX(0,…) in the workbook."""
    avec = [g["libelle_de"] for g in reference["grandeurs"] if g["plancher_a_zero"]]
    assert len(avec) == 2, avec
    for g in reference["grandeurs"]:
        if g["plancher_a_zero"]:
            assert g["borne_basse"] >= 0.0


def test_le_pv_porte_une_bande_donc_il_est_obligatoire(reference):
    """'PV-Ertrag' is a Testgrösse: without irradiance, no class 5."""
    pv = [g for g in reference["grandeurs"] if "PV" in g["libelle_de"]]
    assert len(pv) == 1
    assert pv[0]["groupe"] == moteur.GROUPE_AVEC_CRITERE
    assert pv[0]["borne_haute"] > pv[0]["borne_basse"]


# --------------------------------------------------------------------------
# 2. Engine behaviour
# --------------------------------------------------------------------------


def test_sans_candidat_rien_nest_conforme(reference):
    """State 'before first VE simulation': no success by default."""
    r = moteur.evaluer_test7(reference, None)
    assert r["verdict"] == scatter_band.VERDICT_NOT_CHECKABLE
    assert r["classe_5_validee"] is False
    assert all(g["conforme"] is None for g in r["grandeurs"])
    assert r["nb_echecs"] == 0


def test_candidat_au_centre_de_chaque_bande_passe(reference, candidat_parfait):
    """Positive control. The irradiance provenance must be declared:
    without it the PV is rejected, cf. the 'lock' section below."""
    r = moteur.evaluer_test7(
        reference, candidat_parfait, source_irradiance=SOURCE_FICTIVE
    )
    assert r["verdict"] == scatter_band.VERDICT_PASS
    assert r["classe_5_validee"] is True
    assert r["classe_5_provisoirement_conforme"] is True
    assert r["nb_echecs"] == 0
    assert r["nb_non_evaluables"] == 0


def test_une_seule_grandeur_manquante_suffit_a_bloquer(reference, candidat_parfait):
    """The real case: everything passes except the PV, for lack of irradiance.

    The verdict must be NOT_CHECKABLE, certainly not PASS.
    """
    partiel = dict(candidat_parfait)
    pv = [k for k in partiel if "PV" in k][0]
    del partiel[pv]

    r = moteur.evaluer_test7(reference, partiel)
    assert r["verdict"] == scatter_band.VERDICT_NOT_CHECKABLE
    assert r["classe_5_validee"] is False
    assert r["nb_non_evaluables"] == 1
    assert r["nb_echecs"] == 0
    ligne_pv = [g for g in r["grandeurs"] if g["libelle"] == pv][0]
    assert ligne_pv["statut"] == scatter_band.VERDICT_NOT_CHECKABLE
    assert ligne_pv["conforme"] is None


def test_une_valeur_hors_bande_fait_echouer(reference, candidat_parfait):
    faux = dict(candidat_parfait)
    cible = reference["grandeurs"][0]
    faux[cible["libelle_de"]] = cible["borne_haute"] + 1000.0

    r = moteur.evaluer_test7(reference, faux)
    assert r["verdict"] == scatter_band.VERDICT_FAIL
    assert r["classe_5_validee"] is False
    assert r["nb_echecs"] == 1


def test_les_bornes_sont_inclusives(reference, candidat_parfait):
    """The workbook defines no strict exclusion."""
    for borne in ("borne_basse", "borne_haute"):
        au_bord = dict(candidat_parfait)
        cible = reference["grandeurs"][1]
        au_bord[cible["libelle_de"]] = cible[borne]
        r = moteur.evaluer_test7(reference, au_bord)
        assert r["nb_echecs"] == 0, borne


def test_un_echec_prime_sur_une_non_evaluable(reference, candidat_parfait):
    """A FAIL must not be masked by a NOT_CHECKABLE."""
    melange = dict(candidat_parfait)
    pv = [k for k in melange if "PV" in k][0]
    del melange[pv]
    cible = reference["grandeurs"][0]
    melange[cible["libelle_de"]] = cible["borne_haute"] + 1000.0

    r = moteur.evaluer_test7(reference, melange)
    assert r["verdict"] == scatter_band.VERDICT_FAIL


def test_les_diagnosegroessen_nentrent_pas_dans_le_verdict(reference):
    """They carry no band in the workbook: they are excluded."""
    r = moteur.evaluer_test7(reference, None)
    assert r["grandeurs_soumises_au_critere"] == len(
        [g for g in reference["grandeurs"] if g["groupe"] == moteur.GROUPE_AVEC_CRITERE]
    )


def test_le_classeur_corrige_est_annonce_comme_verifie(reference):
    """The result identifies the corrected source now active."""
    r = moteur.evaluer_test7(reference, None)
    assert r["critere"]["statut"] == "CLASSEUR_CORRIGE_VERIFIE_2026-08-10"
    assert "4.4" in r["critere"]["justification"]
    assert "2026-08-10" in r["critere"]["justification"]


def test_appariement_insensible_a_la_casse_et_aux_espaces(reference):
    brut = dict(
        (g["libelle_de"].upper() + "  ", g["moyenne"]) for g in reference["grandeurs"]
    )
    r = moteur.evaluer_test7(reference, brut, source_irradiance=SOURCE_FICTIVE)
    assert r["nb_non_evaluables"] == 0
    assert r["cles_candidat_ignorees"] == []


def test_un_programme_non_contributeur_nest_pas_compte_comme_zero(reference):
    """Classic mutation: replacing None with 0.0 would overwrite the mean."""
    for g in reference["grandeurs"]:
        contributions = moteur.valeurs_contributrices(g)
        assert len(contributions) == len(g["contributeurs_noms"])
        assert all(v is not None for v in contributions)
        if len(g["contributeurs_noms"]) < 4:
            avec_zero = contributions + [0.0]
            faussee = sum(avec_zero) / len(avec_zero)
            assert abs(faussee - g["moyenne"]) > 1e-6, g["libelle_de"]


def test_une_cle_candidate_non_appariee_est_signalee(reference, candidat_parfait):
    """A typo in the adapter must not go unnoticed.

    Without this signal, the targeted quantity would appear NOT_CHECKABLE without
    anything indicating that a value had nonetheless been supplied under a different name.
    """
    avec_faute = dict(candidat_parfait)
    cible = reference["grandeurs"][0]["libelle_de"]
    avec_faute["Zugefuehrte elektrische Enrgie Kaeltemaschine"] = avec_faute.pop(cible)

    r = moteur.evaluer_test7(reference, avec_faute)
    assert "Zugefuehrte elektrische Enrgie Kaeltemaschine" in r["cles_candidat_ignorees"]
    # and the targeted quantity remained non-evaluable
    ligne = [g for g in r["grandeurs"] if g["libelle"] == cible][0]
    assert ligne["statut"] == scatter_band.VERDICT_NOT_CHECKABLE


def test_les_metadonnees_prefixees_ne_sont_pas_signalees(reference, candidat_parfait):
    """`_provenance` is an assumed block from fixtures, not an error."""
    avec_meta = dict(candidat_parfait)
    avec_meta["_provenance"] = {"source": "fixture de développement"}
    r = moteur.evaluer_test7(reference, avec_meta)
    assert r["cles_candidat_ignorees"] == []


def test_un_candidat_propre_ne_signale_rien(reference, candidat_parfait):
    r = moteur.evaluer_test7(reference, candidat_parfait)
    assert r["cles_candidat_ignorees"] == []


# --------------------------------------------------------------------------
# 3. Irradiance lock — the scenario the audit showed was open
# --------------------------------------------------------------------------


def test_une_valeur_de_pv_sans_provenance_declaree_est_refusee(
    reference, candidat_parfait
):
    """The dangerous scenario: a PV calculated on a substitute climate.

    Before this lock, providing the value was sufficient to obtain PASS and
    `classe_5_validee = True`.
    """
    r = moteur.evaluer_test7(reference, candidat_parfait)  # PV provided, no source
    assert r["verdict"] == scatter_band.VERDICT_NOT_CHECKABLE
    assert r["classe_5_validee"] is False
    assert r["grandeurs_verrouillees"] == ["PV-Ertrag"]

    pv = [g for g in r["grandeurs"] if g["libelle"] == "PV-Ertrag"][0]
    assert pv["statut"] == scatter_band.VERDICT_NOT_CHECKABLE
    assert pv["candidat"] is None  # the value is DISCARDED, not kept
    assert pv["verrou"] == moteur.MOTIF_VERROU_IRRADIANCE


def test_le_verrou_ne_touche_que_le_pv(reference, candidat_parfait):
    r = moteur.evaluer_test7(reference, candidat_parfait)
    autres = [g for g in r["grandeurs"] if g["libelle"] != "PV-Ertrag"]
    assert all(g["verrou"] is None for g in autres)
    assert all(g["conforme"] is True for g in autres)


def test_une_provenance_declaree_leve_le_verrou(reference, candidat_parfait):
    """The lock requires a declaration, it does not forbid the value.

    A hard block would be wrong the day we have the irradiance.
    """
    source = "SIA 2028 DRY normal, Kloten, colonnes verticales — hypothétique"
    r = moteur.evaluer_test7(reference, candidat_parfait, source_irradiance=source)
    assert r["verdict"] == scatter_band.VERDICT_PASS
    assert r["classe_5_validee"] is True
    assert r["classe_5_provisoirement_conforme"] is True
    assert r["grandeurs_verrouillees"] == []
    assert r["source_irradiance"] == source


def test_meme_un_pass_complet_exige_encore_l_attestation(reference, candidat_parfait):
    """A software PASS is NOT an official validation.

    `classe_5_validee` may be True (corrected workbook bands
    reproduced), but the criterion has never been confirmed by the SIA
    sub-commission (art. 4.6.2): the attestation flag remains raised so that a
    consumer reading only the boolean does not present software compliance
    as an official validation.
    """
    r = moteur.evaluer_test7(
        reference, candidat_parfait, source_irradiance=SOURCE_FICTIVE
    )
    assert r["classe_5_validee"] is True
    assert r["attestation_sous_commission_requise"] is True


def test_la_provenance_declaree_remonte_sur_la_ligne_pv(reference, candidat_parfait):
    """Without this, the declaration would be lost when writing the report."""
    source = "irradiance mesurée, station X"
    r = moteur.evaluer_test7(reference, candidat_parfait, source_irradiance=source)
    pv = [g for g in r["grandeurs"] if g["libelle"] == "PV-Ertrag"][0]
    assert pv["source_irradiance"] == source
    assert pv["exige_irradiance"] is True


def test_le_resume_affiche_le_verrou(reference, candidat_parfait):
    texte = moteur.resumer(moteur.evaluer_test7(reference, candidat_parfait))
    assert "VERROU" in texte
    assert "PV-Ertrag" in texte


def test_chaque_ligne_porte_le_statut_du_classeur_corrige(reference, candidat_parfait):
    """`evaluer_grandeur` is public: the marker must not depend
    on a pass through `evaluer_test7`."""
    grandeur = reference["grandeurs"][0]
    ligne = moteur.evaluer_grandeur(grandeur, grandeur["moyenne"])
    assert ligne["critere_statut"] == "CLASSEUR_CORRIGE_VERIFIE_2026-08-10"


def test_la_liste_des_grandeurs_a_irradiance_correspond_a_la_reference(reference):
    """If the workbook label changed, the lock would become inoperative
    silently. This test would catch it."""
    libelles = set(g["libelle_de"].strip() for g in reference["grandeurs"])
    for nom in moteur.GRANDEURS_EXIGEANT_IRRADIANCE:
        assert nom in libelles, nom


def test_resume_mentionne_chaque_grandeur(reference, candidat_parfait):
    texte = moteur.resumer(moteur.evaluer_test7(reference, candidat_parfait))
    for g in reference["grandeurs"]:
        assert g["libelle_de"][:40] in texte


def test_no_iesve_import():
    """Rule 4 of CLAUDE.md: engine/ is pure Python."""
    chemin = os.path.join(_RACINE, "engine", "test7_engine.py")
    with io.open(chemin, encoding="utf-8") as f:
        for numero, ligne in enumerate(f, 1):
            nu = ligne.strip()
            assert not nu.startswith("import iesve"), numero
            assert not nu.startswith("from iesve"), numero
