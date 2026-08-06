# -*- coding: utf-8 -*-
"""Tests de `verdict_view.construire_synthese_classes` — la page de tête du
rapport client.

C'est la seule vue qui réponde à « quelles classes ce logiciel a-t-il ? », et
donc celle où un faux vert coûterait le plus cher. La règle testée sans
exception : **une classe n'est verte que si TOUS les tests que le tableau 63
lui impose sont présents dans le dossier ET verts.**

Python pur, sans Tkinter ni Excel : tourne en CI.

Les vues sont fabriquées à la main plutôt que dérivées des moteurs — on teste
ici la logique d'agrégation, pas les moteurs, et une vue synthétique permet de
provoquer des combinaisons qu'aucun jeu de données réel ne produit encore.
"""

import pytest

from ui import verdict_view as vue


def _vue(numero, couleur, texte=u'peu importe'):
    """Vue minimale : seules les clés lues par la synthèse sont fournies."""
    conforme = {'vert': True, 'rouge': False, 'gris': None}[couleur]
    return {
        'test_id': u'Test ' + numero,
        'numero_test': numero,
        'verdict_global': {'conforme': conforme, 'couleur': couleur,
                           'texte': texte, 'article': u''},
        'classes': [],
        'lignes': [],
    }


def _par_classe(lignes):
    return dict((l['classe'], l) for l in lignes)


# --------------------------------------------------------------------------
# Le tableau 63 lui-même
# --------------------------------------------------------------------------

def test_les_huit_classes_du_tableau_63_sont_couvertes():
    lignes = vue.construire_synthese_classes([])
    assert [l['classe'] for l in lignes] == [
        '1A', '1B', '2A', '2B', '3', '4A', '4B', '5']


def test_la_classe_5_nexige_que_le_test_7():
    assert vue.TESTS_PAR_CLASSE['5'] == ('7',)


def test_la_classe_4b_exige_les_sept_tests():
    assert vue.TESTS_PAR_CLASSE['4B'] == ('1', '2', '3', '4', '5', '6', '7')


def test_le_test_7_est_exige_par_4a_4b_et_5():
    """Erreur déjà commise une fois : n'attribuer le Test 7 qu'à la classe 5
    sous-estime la portée d'un échec — une classe au lieu de trois."""
    concernees = [c for c, t in vue.TESTS_PAR_CLASSE.items() if '7' in t]
    assert sorted(concernees) == ['4A', '4B', '5']


def test_le_test_1_est_exige_partout_sauf_classe_5():
    sans_test1 = [c for c, t in vue.TESTS_PAR_CLASSE.items() if '1' not in t]
    assert sans_test1 == ['5']


# --------------------------------------------------------------------------
# Jamais de faux vert
# --------------------------------------------------------------------------

def test_sans_aucune_vue_rien_nest_conforme():
    for ligne in vue.construire_synthese_classes([]):
        assert ligne['conforme'] is None
        assert ligne['couleur'] == 'gris'
        assert ligne['tests_couverts'] == []
        assert ligne['tests_manquants'] == ligne['tests_exiges']


def test_un_test_vert_ne_suffit_pas_si_un_autre_manque():
    """Cœur du sujet : le Test 1 vert ne donne PAS la classe 1A, qui exige
    aussi le Test 2A."""
    lignes = _par_classe(vue.construire_synthese_classes([_vue('1', 'vert')]))
    assert lignes['1A']['conforme'] is None
    assert lignes['1A']['couleur'] == 'gris'
    assert lignes['1A']['tests_manquants'] == ['2A']
    assert u'Test 2A' in lignes['1A']['texte_verdict']


def test_la_classe_5_devient_verte_avec_le_seul_test_7():
    """Miroir du précédent : la classe 5 n'exige que le Test 7."""
    lignes = _par_classe(vue.construire_synthese_classes([_vue('7', 'vert')]))
    assert lignes['5']['conforme'] is True
    assert lignes['5']['couleur'] == 'vert'
    assert lignes['5']['tests_manquants'] == []
    # ...mais 4A et 4B, qui exigent aussi le Test 7, restent incomplètes.
    assert lignes['4A']['conforme'] is None
    assert lignes['4B']['conforme'] is None


def test_un_test_gris_empeche_le_vert_meme_si_tout_est_couvert():
    lignes = _par_classe(vue.construire_synthese_classes([_vue('7', 'gris')]))
    assert lignes['5']['tests_manquants'] == []
    assert lignes['5']['conforme'] is None
    assert u'non évalué' in lignes['5']['texte_verdict'].lower()


def test_un_echec_rend_la_classe_rouge():
    lignes = _par_classe(vue.construire_synthese_classes([_vue('7', 'rouge')]))
    assert lignes['5']['conforme'] is False
    assert lignes['5']['couleur'] == 'rouge'


def test_un_echec_reste_visible_meme_avec_des_tests_manquants():
    """Un échec avéré est plus grave qu'une absence : il ne doit pas être
    ravalé au rang de « non concluante » et disparaître du rapport."""
    lignes = _par_classe(vue.construire_synthese_classes([_vue('1', 'rouge')]))
    assert lignes['1A']['conforme'] is False
    assert lignes['1A']['couleur'] == 'rouge'
    assert lignes['1A']['tests_manquants'] == ['2A']
    # le texte dit les deux choses
    assert u'Non conforme' in lignes['1A']['texte_verdict']
    assert u'Test 2A' in lignes['1A']['texte_verdict']


def test_tous_les_tests_verts_donne_toutes_les_classes_vertes():
    toutes = [_vue(n, 'vert')
              for n in ('1', '2', '2A', '3', '3A-F', '4', '5', '6', '7')]
    for ligne in vue.construire_synthese_classes(toutes):
        assert ligne['conforme'] is True, ligne['classe']
        assert ligne['tests_manquants'] == []


# --------------------------------------------------------------------------
# Traçabilité et robustesse
# --------------------------------------------------------------------------

def test_chaque_ligne_cite_le_tableau_63():
    for ligne in vue.construire_synthese_classes([_vue('1', 'vert')]):
        assert 'tab' in ligne['article'].lower()
        assert '63' in ligne['article']


def test_les_tests_manquants_sont_nommes_pas_seulement_comptes():
    """Le lecteur doit pouvoir vérifier lui-même, sans nous croire."""
    ligne = _par_classe(vue.construire_synthese_classes([_vue('1', 'vert')]))['4B']
    for numero in ('2', '3', '4', '5', '6', '7'):
        assert u'Test ' + numero in ligne['texte_verdict']


def test_une_vue_sans_numero_de_test_est_ignoree_sans_planter():
    """Une vue d'un test futur, pas encore rattachée au tableau 63, ne doit
    ni faire échouer la synthèse ni compter comme couverture."""
    anonyme = _vue('1', 'vert')
    del anonyme['numero_test']
    lignes = _par_classe(vue.construire_synthese_classes([anonyme]))
    assert lignes['1A']['tests_couverts'] == []


def test_les_vues_reelles_declarent_leur_numero():
    """Si un constructeur de vue oubliait `numero_test`, la synthèse
    afficherait silencieusement zéro couverture."""
    import inspect
    for nom in ('construire_vue_test1', 'construire_vue_test7'):
        source = inspect.getsource(getattr(vue, nom))
        assert "'numero_test'" in source, nom
