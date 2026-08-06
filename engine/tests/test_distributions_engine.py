# -*- coding: utf-8 -*-
u"""Tests du moteur de distributions (second critère des tests 2, 3 et 5).

Ce moteur a une propriété inhabituelle qu'il faut verrouiller : **il ne doit
jamais conclure**. Le classeur officiel ne calcule aucune bande pour les
distributions, donc rendre un verdict conforme transformerait une preuve
manquante en conformité — exactement ce que le projet existe pour empêcher.

La moitié des tests ci-dessous vise ce refus de conclure ; l'autre moitié
vise le classement d'une série horaire, où une erreur de borne passerait
inaperçue.
"""

import pytest

from engine import sia_distributions_engine as moteur


# --------------------------------------------------------------------------
# Portée
# --------------------------------------------------------------------------

@pytest.mark.parametrize('numero', moteur.TESTS_SUPPORTES)
def test_les_trois_tests_concernes_ont_un_referentiel(numero):
    try:
        reference = moteur.charger_reference(numero)
    except moteur.ReferenceIntrouvable:
        pytest.skip(u'référentiel absent')
    assert reference['distributions']


@pytest.mark.parametrize('numero', (4, 6))
def test_les_tests_sans_distribution_sont_refuses(numero):
    """Leurs spécifications ne fixent aucun Testkriterium et leurs classeurs
    n'ont pas de classes de fréquence. Rendre un résultat vide se lirait comme
    « rien ne passe » au lieu de « ce critère n'existe pas »."""
    with pytest.raises(ValueError, match='pas de critère de distribution'):
        moteur.charger_reference(numero)


def test_un_referentiel_absent_est_une_erreur_franche(tmp_path):
    import os
    manquant = os.path.join(str(tmp_path), 'absent.json')
    with pytest.raises(moteur.ReferenceIntrouvable, match='build_sia'):
        moteur.charger_reference(2, manquant)


# --------------------------------------------------------------------------
# Le refus de conclure
# --------------------------------------------------------------------------

def test_le_statut_du_critere_est_non_etabli():
    """Plus faible qu'`INFERE` des sommes annuelles : là une formule existait
    dans le classeur. Ici il n'y en a aucune."""
    assert moteur.STATUT_CRITERE == 'NON_ETABLI'


def test_un_candidat_parfait_ne_donne_pas_conforme():
    """LE test central. Même un candidat au centre de toutes les classes ne
    doit pas produire de verdict conforme."""
    bloc = _bloc([{'A': 10, 'B': 10, 'C': 10}, {'A': 5, 'B': 5, 'C': 5}])
    resultat = moteur.evaluer_bloc(bloc, [10, 5])
    assert resultat['verdict'] == moteur.VERDICT_NON_ETABLI
    # ... alors meme qu'aucune classe n'est hors des deux lectures.
    assert resultat['nb_hors_lecture'] == {
        moteur.LECTURE_ENVELOPPE: 0, moteur.LECTURE_BANDE: 0}


def test_le_verdict_densemble_reste_non_etabli():
    reference = {'test': 2, 'distributions': [
        _bloc([{'A': 1, 'B': 1}]),
    ], 'critere': 'x'}
    assert moteur.evaluer(reference, {(None, 'G'): [1]})[
        'verdict'] == moteur.VERDICT_NON_ETABLI


def test_la_justification_dit_pourquoi():
    assert 'graphiques' in moteur.JUSTIFICATION_CRITERE


# --------------------------------------------------------------------------
# Les deux lectures du Streubereich
# --------------------------------------------------------------------------

def test_les_deux_lectures_sont_calculees():
    """Enveloppe min/max et moyenne ± écart max ne coïncident pas. Trancher
    entre elles reviendrait à inventer le critère."""
    lectures = moteur.bornes_des_lectures([2, 4, 12])
    assert lectures[moteur.LECTURE_ENVELOPPE] == (2.0, 12.0)
    # moyenne 6, ecart max |12-6| = 6 -> 0..12
    assert lectures[moteur.LECTURE_BANDE] == (0.0, 12.0)


def test_les_deux_lectures_peuvent_diverger():
    """Un candidat peut tomber dans l'une et pas dans l'autre. C'est
    précisément pourquoi les deux sont rapportées."""
    lectures = moteur.bornes_des_lectures([10, 10, 10, 40])
    basse_env, haute_env = lectures[moteur.LECTURE_ENVELOPPE]
    basse_bande, haute_bande = lectures[moteur.LECTURE_BANDE]
    assert basse_env == 10.0 and haute_env == 40.0
    # moyenne 17.5, ecart max 22.5 -> 0..40 : la bande est PLUS large en bas.
    assert basse_bande == 0.0
    assert basse_bande < basse_env


def test_le_plancher_a_zero_est_une_propriete_de_la_grandeur():
    """Un effectif ne peut pas être négatif. Le plancher n'est pas une
    tolérance du critère, c'est une propriété du comptage."""
    basse, _ = moteur.bornes_des_lectures([0, 0, 30])[moteur.LECTURE_BANDE]
    assert basse == 0.0


def test_les_bornes_sont_incluses():
    bloc = _bloc([{'A': 4, 'B': 10}])
    resultat = moteur.evaluer_bloc(bloc, [10])
    assert resultat['classes'][0]['dans_la_lecture'][
        moteur.LECTURE_ENVELOPPE] is True


def test_sans_contributeur_aucune_lecture_nest_produite():
    assert moteur.bornes_des_lectures([]) == {}


# --------------------------------------------------------------------------
# Classement d'une série horaire
# --------------------------------------------------------------------------

def test_les_bornes_sont_superieures_et_incluses():
    assert moteur.classer([10, 10.5, 100], [10, 100]) == [1, 2]


def test_la_derniere_classe_absorbe_les_depassements():
    """Sinon des heures disparaîtraient du total, et la réconciliation avec le
    classeur deviendrait ininterprétable."""
    assert moteur.classer([5, 5000], [10, 100]) == [1, 1]
    assert sum(moteur.classer([5, 5000], [10, 100])) == 2


def test_les_valeurs_non_numeriques_sont_ecartees():
    assert moteur.classer([1, None, 'x', True, 2], [10]) == [2]


def test_une_serie_vide_donne_des_classes_vides():
    assert moteur.classer([], [10, 100]) == [0, 0]
    assert moteur.classer(None, [10]) == [0]


def test_des_bornes_desordonnees_sont_refusees():
    """Tout classement serait arbitraire, et l'erreur invisible."""
    with pytest.raises(ValueError, match='croissantes'):
        moteur.classer([1], [100, 10])


def test_sans_borne_le_classement_est_refuse():
    with pytest.raises(ValueError, match='aucune borne'):
        moteur.classer([1], [])


# --------------------------------------------------------------------------
# Absence de candidat
# --------------------------------------------------------------------------

def test_sans_candidat_la_distribution_est_non_evaluable():
    """Ni conforme, ni en échec : rien n'a été mesuré."""
    resultat = moteur.evaluer_bloc(_bloc([{'A': 1}]), None)
    assert resultat['verdict'] == moteur.VERDICT_NON_EVALUABLE
    assert resultat['classes'][0]['candidat'] is None
    assert resultat['classes'][0]['dans_la_lecture'][
        moteur.LECTURE_ENVELOPPE] is None


def test_une_cle_candidate_inconnue_est_signalee():
    """Silencieusement ignorée, elle laisserait croire qu'elle a été prise en
    compte."""
    reference = {'test': 2, 'critere': 'x',
                 'distributions': [_bloc([{'A': 1}])]}
    resultat = moteur.evaluer(reference, {('inexistant', 'X'): [1]})
    assert resultat['cles_candidat_ignorees'] == [['inexistant', 'X']]
    assert resultat['nb_non_evaluables'] == 1


def test_les_contributeurs_partiels_sont_signales():
    """Un programme qui ne totalise que 3380 heures ne couvre pas la même
    période que les autres : le taire rendrait la dispersion inexplicable."""
    bloc = _bloc([{'A': 1, 'B': 1}])
    bloc['contributeurs'][0]['total_heures'] = 3380   # partiel, comme le Test 5
    bloc['contributeurs'][1]['total_heures'] = 8760   # annee complete
    assert moteur.evaluer_bloc(bloc, [1])['contributeurs_partiels'] == ['A']


# --------------------------------------------------------------------------
# Sur les vraies références
# --------------------------------------------------------------------------

@pytest.mark.parametrize('numero', moteur.TESTS_SUPPORTES)
def test_sans_candidat_tout_est_non_evaluable(numero):
    try:
        reference = moteur.charger_reference(numero)
    except moteur.ReferenceIntrouvable:
        pytest.skip(u'référentiel absent')
    resultat = moteur.evaluer(reference)
    assert resultat['nb_evaluees'] == 0
    assert resultat['nb_non_evaluables'] == resultat['nb_distributions']
    assert resultat['verdict'] == moteur.VERDICT_NON_ETABLI


def test_un_candidat_reel_reste_non_conclusif():
    """Sur le Test 3, en resoumettant la distribution d'un programme de
    référence comme candidat : toutes les classes tombent dans l'enveloppe,
    et le verdict reste malgré tout NON_ETABLI."""
    try:
        reference = moteur.charger_reference(3)
    except moteur.ReferenceIntrouvable:
        pytest.skip(u'référentiel absent')
    bloc = reference['distributions'][0]
    lettre = bloc['contributeurs'][0]['colonne']
    effectifs = [e['par_colonne'][lettre] for e in bloc['effectifs']]

    resultat = moteur.evaluer(
        reference, {(bloc['cas'], bloc['grandeur']): effectifs})
    premier = resultat['distributions'][0]
    assert premier['nb_hors_lecture'][moteur.LECTURE_ENVELOPPE] == 0
    assert premier['total_candidat'] == bloc['contributeurs'][0]['total_heures']
    assert resultat['verdict'] == moteur.VERDICT_NON_ETABLI


def test_le_resume_dit_que_rien_nest_conclu():
    try:
        reference = moteur.charger_reference(2)
    except moteur.ReferenceIntrouvable:
        pytest.skip(u'référentiel absent')
    texte = moteur.resumer(moteur.evaluer(reference))
    assert 'NON_ETABLI' in texte
    assert 'aucune bande' in texte


# --------------------------------------------------------------------------
# Outillage
# --------------------------------------------------------------------------

def _bloc(classes_par_colonne):
    """Fabrique un bloc de distribution minimal.

    Args:
        classes_par_colonne: Une entrée par classe, `{colonne: effectif}`.

    Returns:
        dict: Bloc au format du référentiel.
    """
    colonnes = sorted(classes_par_colonne[0])
    return {
        'cas': None,
        'grandeur': 'G',
        'unite': 'W',
        'colonne_bloc': 'A',
        'nb_classes': len(classes_par_colonne),
        'ligne_total': 99,
        'contributeurs': [
            {'colonne': c, 'programme': c,
             'total_heures': sum(e[c] for e in classes_par_colonne)}
            for c in colonnes],
        'effectifs': [
            {'ligne_classeur': 10 + rang, 'borne_superieure': 10 * (rang + 1),
             'par_colonne': dict(entree)}
            for rang, entree in enumerate(classes_par_colonne)],
    }
