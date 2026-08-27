# -*- coding: utf-8 -*-
"""Tests of the min/max distribution criterion confirmed on 2026-08-10."""

import pytest

from engine import sia_distributions_engine as moteur

# --------------------------------------------------------------------------
# Scope
# --------------------------------------------------------------------------


@pytest.mark.parametrize("numero", moteur.TESTS_SUPPORTES)
def test_les_trois_tests_concernes_ont_un_referentiel(numero):
    try:
        reference = moteur.charger_reference(numero)
    except moteur.ReferenceIntrouvable:
        pytest.skip("référentiel absent")
    assert reference["distributions"]


@pytest.mark.parametrize("numero", (4, 6))
def test_les_tests_4_6_attendent_encore_un_referentiel_executable(numero):
    """The workbooks have distributions, but their exact gate is still under review."""
    with pytest.raises(ValueError, match="gate exact reste en revue"):
        moteur.charger_reference(numero)


def test_un_referentiel_absent_est_une_erreur_franche(tmp_path):
    import os

    manquant = os.path.join(str(tmp_path), "absent.json")
    with pytest.raises(moteur.ReferenceIntrouvable, match="build_sia"):
        moteur.charger_reference(2, manquant)


# --------------------------------------------------------------------------
# Authority decision and verdict
# --------------------------------------------------------------------------


def test_le_statut_du_critere_est_confirme():
    assert moteur.STATUT_CRITERE == "CONFIRME_AUTORITE_2026-08-10"


def test_un_candidat_dans_enveloppe_passe():
    bloc = _bloc([{"A": 10, "B": 10, "C": 10}, {"A": 5, "B": 5, "C": 5}])
    resultat = moteur.evaluer_bloc(bloc, [10, 5])
    assert resultat["verdict"] == moteur.VERDICT_PASS
    assert resultat["nb_hors_lecture"] == {
        moteur.LECTURE_ENVELOPPE: 0,
        moteur.LECTURE_BANDE: 0,
    }


def test_le_verdict_densemble_passe_quand_tout_est_evaluable_dedans():
    reference = {
        "test": 2,
        "distributions": [
            _bloc([{"A": 1, "B": 1}]),
        ],
        "critere": "x",
    }
    assert moteur.evaluer(reference, {(None, "G"): [1]})["verdict"] == moteur.VERDICT_PASS


def test_la_justification_dit_pourquoi():
    assert "2026-08-10" in moteur.JUSTIFICATION_CRITERE
    assert "minimum/maximum" in moteur.JUSTIFICATION_CRITERE


# --------------------------------------------------------------------------
# The two readings of the Streubereich
# --------------------------------------------------------------------------


def test_les_deux_lectures_sont_calculees():
    """min/max envelope and mean ± max deviation do not coincide. Settling
    between them would amount to inventing the criterion."""
    lectures = moteur.bornes_des_lectures([2, 4, 12])
    assert lectures[moteur.LECTURE_ENVELOPPE] == (2.0, 12.0)
    # mean 6, max deviation |12-6| = 6 -> 0..12
    assert lectures[moteur.LECTURE_BANDE] == (0.0, 12.0)


def test_les_deux_lectures_peuvent_diverger():
    """A candidate may fall in one but not the other. That is precisely
    why both are reported."""
    lectures = moteur.bornes_des_lectures([10, 10, 10, 40])
    basse_env, haute_env = lectures[moteur.LECTURE_ENVELOPPE]
    basse_bande, haute_bande = lectures[moteur.LECTURE_BANDE]
    assert basse_env == 10.0 and haute_env == 40.0
    # mean 17.5, max deviation 22.5 -> 0..40: the band is WIDER at the bottom.
    assert basse_bande == 0.0
    assert basse_bande < basse_env


def test_le_plancher_a_zero_est_une_propriete_de_la_grandeur():
    """A count cannot be negative. The floor is not a criterion tolerance,
    it is a property of counting."""
    basse, _ = moteur.bornes_des_lectures([0, 0, 30])[moteur.LECTURE_BANDE]
    assert basse == 0.0


def test_les_bornes_sont_incluses():
    bloc = _bloc([{"A": 4, "B": 10}])
    resultat = moteur.evaluer_bloc(bloc, [10])
    assert resultat["classes"][0]["dans_la_lecture"][moteur.LECTURE_ENVELOPPE] is True


def test_sans_contributeur_aucune_lecture_nest_produite():
    assert moteur.bornes_des_lectures([]) == {}


# --------------------------------------------------------------------------
# Classification of an hourly series
# --------------------------------------------------------------------------


def test_les_bornes_sont_superieures_et_incluses():
    assert moteur.classer([10, 10.5, 100], [10, 100]) == [1, 2]


def test_la_derniere_classe_absorbe_les_depassements():
    """Otherwise hours would disappear from the total, making reconciliation with the
    workbook uninterpretable."""
    assert moteur.classer([5, 5000], [10, 100]) == [1, 0]
    detail = moteur.classer_avec_hors_classes([5, 5000], [10, 100])
    assert detail == {
        "effectifs": [1, 0],
        "hors_classes_superieur": 1,
        "total_numerique": 2,
    }


def test_les_valeurs_non_numeriques_sont_ecartees():
    assert moteur.classer([1, None, "x", True, 2], [10]) == [2]


def test_une_serie_vide_donne_des_classes_vides():
    assert moteur.classer([], [10, 100]) == [0, 0]
    assert moteur.classer(None, [10]) == [0]


def test_des_bornes_desordonnees_sont_refusees():
    """Any classification would be arbitrary, and the error invisible."""
    with pytest.raises(ValueError, match="croissantes"):
        moteur.classer([1], [100, 10])


def test_sans_borne_le_classement_est_refuse():
    with pytest.raises(ValueError, match="aucune borne"):
        moteur.classer([1], [])


# --------------------------------------------------------------------------
# Absence of candidate
# --------------------------------------------------------------------------


def test_sans_candidat_la_distribution_est_non_evaluable():
    """Neither conforming, nor failing: nothing has been measured."""
    resultat = moteur.evaluer_bloc(_bloc([{"A": 1}]), None)
    assert resultat["verdict"] == moteur.VERDICT_NON_EVALUABLE
    assert resultat["classes"][0]["candidat"] is None
    assert resultat["classes"][0]["dans_la_lecture"][moteur.LECTURE_ENVELOPPE] is None


def test_une_cle_candidate_inconnue_est_signalee():
    """Silently ignored, it would make one believe it was taken into
    account."""
    reference = {"test": 2, "critere": "x", "distributions": [_bloc([{"A": 1}])]}
    resultat = moteur.evaluer(reference, {("inexistant", "X"): [1]})
    assert resultat["cles_candidat_ignorees"] == [["inexistant", "X"]]
    assert resultat["nb_non_evaluables"] == 1


def test_les_heures_hors_classes_sont_signalees():
    """3380 hours displayed does not imply an incomplete annual series."""
    bloc = _bloc([{"A": 1, "B": 1}])
    bloc["contributeurs"][0]["total_heures"] = 3380
    bloc["contributeurs"][0]["heures_hors_classes"] = 5380
    bloc["contributeurs"][1]["total_heures"] = 8760
    bloc["contributeurs"][1]["heures_hors_classes"] = 0
    resultat = moteur.evaluer_bloc(bloc, [1])
    assert resultat["contributeurs_partiels"] == []
    assert resultat["contributeurs_hors_classes"] == [
        {"colonne": "A", "heures_hors_classes": 5380}
    ]


# --------------------------------------------------------------------------
# Against real references
# --------------------------------------------------------------------------


@pytest.mark.parametrize("numero", moteur.TESTS_SUPPORTES)
def test_sans_candidat_tout_est_non_evaluable(numero):
    try:
        reference = moteur.charger_reference(numero)
    except moteur.ReferenceIntrouvable:
        pytest.skip("référentiel absent")
    resultat = moteur.evaluer(reference)
    assert resultat["nb_evaluees"] == 0
    assert resultat["nb_non_evaluables"] == resultat["nb_distributions"]
    assert resultat["verdict"] == moteur.VERDICT_NON_EVALUABLE


def test_un_candidat_reel_passe_son_bloc_mais_pas_les_blocs_absents():
    """On Test 3, resubmitting a reference programme's distribution as candidate:
    all classes fall within the envelope, and the verdict remains NON_ETABLI."""
    try:
        reference = moteur.charger_reference(3)
    except moteur.ReferenceIntrouvable:
        pytest.skip("référentiel absent")
    bloc = reference["distributions"][0]
    lettre = bloc["contributeurs"][0]["colonne"]
    effectifs = [e["par_colonne"][lettre] for e in bloc["effectifs"]]

    resultat = moteur.evaluer(reference, {(bloc["cas"], bloc["grandeur"]): effectifs})
    premier = resultat["distributions"][0]
    assert premier["nb_hors_lecture"][moteur.LECTURE_ENVELOPPE] == 0
    assert premier["total_candidat"] == bloc["contributeurs"][0]["total_heures"]
    assert premier["verdict"] == moteur.VERDICT_PASS
    assert resultat["verdict"] == moteur.VERDICT_NON_EVALUABLE


def test_le_resume_indique_le_critere_confirme_et_levidence_absente():
    try:
        reference = moteur.charger_reference(2)
    except moteur.ReferenceIntrouvable:
        pytest.skip("référentiel absent")
    texte = moteur.resumer(moteur.evaluer(reference))
    assert "NOT_CHECKABLE" in texte
    assert "min/max confirmé" in texte


# --------------------------------------------------------------------------
# Tooling
# --------------------------------------------------------------------------


def _bloc(classes_par_colonne):
    """Builds a minimal distribution block.

    Args:
        classes_par_colonne: One entry per class, `{column: count}`.

    Returns:
        dict: Block in the reference format.
    """
    colonnes = sorted(classes_par_colonne[0])
    return {
        "cas": None,
        "grandeur": "G",
        "unite": "W",
        "colonne_bloc": "A",
        "nb_classes": len(classes_par_colonne),
        "ligne_total": 99,
        "contributeurs": [
            {
                "colonne": c,
                "programme": c,
                "total_heures": sum(e[c] for e in classes_par_colonne),
            }
            for c in colonnes
        ],
        "effectifs": [
            {
                "ligne_classeur": 10 + rang,
                "borne_superieure": 10 * (rang + 1),
                "par_colonne": dict(entree),
            }
            for rang, entree in enumerate(classes_par_colonne)
        ],
    }
