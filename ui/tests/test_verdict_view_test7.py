# -*- coding: utf-8 -*-
"""Tests de la vue du Test 7 — `ui/verdict_view.py::construire_vue_test7`.

Python pur, sans Tkinter : ces tests tournent en CI.

La règle testée en priorité est celle de `CLAUDE.md` sur la lisibilité du
verdict : **jamais de faux vert par donnée manquante.** Le cas réel du projet
est précisément celui-là — le PV du Test 7 restera non évaluable tant que nous
n'aurons pas d'irradiance, et l'interface ne doit pas laisser croire que la
classe 5 passe.
"""

import os

import pytest

from engine import test7_engine as moteur
from ui import verdict_view as vue


@pytest.fixture(scope='module')
def reference():
    if not os.path.exists(moteur.CHEMIN_REFERENCE_DEFAUT):
        pytest.skip(u'référence Test 7 absente')
    return moteur.charger_reference()


@pytest.fixture(scope='module')
def candidat_parfait(reference):
    return dict((g['libelle_de'], g['moyenne']) for g in reference['grandeurs'])


# Provenance FICTIVE, uniquement pour lever le verrou du PV dans les témoins
# positifs. Ne décrit aucune irradiance réelle.
SOURCE_FICTIVE = u'source fictive de test -- ne décrit aucune donnée réelle'


def _vue(reference, candidat, source_irradiance=None):
    return vue.construire_vue_test7(moteur.evaluer_test7(
        reference, candidat, source_irradiance=source_irradiance))


# --------------------------------------------------------------------------
# Contrat de vue
# --------------------------------------------------------------------------

def test_respecte_le_meme_contrat_que_le_test_1(reference):
    v = _vue(reference, None)
    for cle in ('test_id', 'verdict_global', 'classes', 'lignes'):
        assert cle in v, cle
    for cle in ('conforme', 'couleur', 'texte', 'article'):
        assert cle in v['verdict_global'], cle


def test_une_ligne_par_grandeur_dans_lordre_du_classeur(reference):
    v = _vue(reference, None)
    assert len(v['lignes']) == len(reference['grandeurs'])
    attendus = [g['libelle_de'] for g in reference['grandeurs']]
    assert [l['cas'] for l in v['lignes']] == attendus


def test_les_trois_classes_du_tableau_63_sont_presentes(reference):
    """Tab. 63 : le Test 7 est exigé par 4A (1, 2A, 3A-F, 4 à 7),
    4B (1 à 7) et 5 (7 seul). N'en lister qu'une sous-estimerait la portée
    d'un échec."""
    v = _vue(reference, None)
    assert [c['classe'] for c in v['classes']] == ['4A', '4B', '5']
    for ligne in v['classes']:
        assert 'tab. 63' in ligne['article']


def test_seule_la_classe_5_est_annoncee_comme_suffisante(reference):
    v = _vue(reference, None)
    par_classe = dict((c['classe'], c['article']) for c in v['classes'])
    assert u'n\'exige que le Test 7' in par_classe['5']
    for classe in ('4A', '4B'):
        assert u'NON suffisant' in par_classe[classe]


def test_larticle_ne_presente_jamais_le_critere_comme_enonce_par_le_test(
        reference):
    u"""Le mot « INFÉRÉ » a disparu de l'article, et c'est volontaire.

    Le classeur corrigé reçu le 2026-08-10 a été vérifié (XML et checksum
    consignés), donc le moteur porte désormais
    `CLASSEUR_CORRIGE_VERIFIE_2026-08-10` au lieu d'une inférence — statut
    verrouillé par `engine/tests/test_autotest_chaine.py`. Ce qui ne doit
    JAMAIS changer est l'aveu affiché : la spécification du Test 7 n'énonce
    aucun critère, c'est le §4.4 qui délègue la comparaison au classeur. Un
    article qui laisserait croire que le Test 7 porte son propre critère
    ferait passer une délégation pour une exigence.
    """

    v = _vue(reference, None)
    articles = [v['verdict_global']['article']]
    articles.extend(ligne['article'] for ligne in v['lignes'])
    assert articles
    for article in articles:
        assert u'aucun critère' in article
        assert u'délègue' in article
        assert u'4.4' in article


# --------------------------------------------------------------------------
# Couleurs — jamais de faux vert
# --------------------------------------------------------------------------

def test_sans_candidat_tout_est_gris(reference):
    v = _vue(reference, None)
    assert v['verdict_global']['couleur'] == 'gris'
    assert v['verdict_global']['conforme'] is None
    for ligne in v['lignes']:
        assert ligne['couleur'] == 'gris'
        assert ligne['valeur_candidate_affichee'] == u'—'


def test_candidat_au_centre_tout_est_vert(reference, candidat_parfait):
    """Témoin positif : provenance d'irradiance déclarée, sinon le PV est
    refusé par le verrou du moteur."""
    v = _vue(reference, candidat_parfait, source_irradiance=SOURCE_FICTIVE)
    assert v['verdict_global']['couleur'] == 'vert'
    assert all(l['couleur'] == 'vert' for l in v['lignes'])


def test_un_pv_sans_provenance_laisse_la_classe_5_grise(reference,
                                                         candidat_parfait):
    """Vue du scénario que l'audit avait montré ouvert : toutes les valeurs
    sont fournies, PV compris, mais sans dire d'où vient l'irradiance."""
    v = _vue(reference, candidat_parfait)  # aucune provenance déclarée
    assert v['verdict_global']['couleur'] == 'gris'
    ligne_pv = [l for l in v['lignes'] if 'PV' in l['cas']][0]
    assert ligne_pv['couleur'] == 'gris'
    assert ligne_pv['valeur_candidate'] is None


def test_le_pv_manquant_ne_donne_jamais_un_vert_global(reference,
                                                       candidat_parfait):
    """Le cas réel du projet : tout tombe dans la bande sauf le PV."""
    partiel = dict(candidat_parfait)
    libelle_pv = [k for k in partiel if 'PV' in k][0]
    del partiel[libelle_pv]

    v = _vue(reference, partiel)
    assert v['verdict_global']['couleur'] == 'gris'
    assert v['verdict_global']['conforme'] is None
    assert v['classes'][0]['couleur'] == 'gris'

    ligne_pv = [l for l in v['lignes'] if l['cas'] == libelle_pv][0]
    assert ligne_pv['couleur'] == 'gris'
    autres = [l for l in v['lignes'] if l['cas'] != libelle_pv]
    assert all(l['couleur'] == 'vert' for l in autres)


def test_une_valeur_hors_bande_donne_du_rouge(reference, candidat_parfait):
    faux = dict(candidat_parfait)
    cible = reference['grandeurs'][0]
    faux[cible['libelle_de']] = cible['borne_haute'] + 1000.0

    v = _vue(reference, faux)
    assert v['verdict_global']['couleur'] == 'rouge'
    assert v['verdict_global']['conforme'] is False
    rouge = [l for l in v['lignes'] if l['couleur'] == 'rouge']
    assert len(rouge) == 1
    assert rouge[0]['cas'] == cible['libelle_de']


# --------------------------------------------------------------------------
# Présentation
# --------------------------------------------------------------------------

def test_le_resume_de_bande_montre_moyenne_et_bornes(reference):
    v = _vue(reference, None)
    for ligne, grandeur in zip(v['lignes'], reference['grandeurs']):
        resume = ligne['reference_affichee']
        assert vue.formater_nombre(grandeur['moyenne'], 1) in resume
        assert vue.formater_nombre(grandeur['borne_basse'], 1) in resume
        assert vue.formater_nombre(grandeur['borne_haute'], 1) in resume


def test_le_groupe_du_classeur_sert_de_niveau_de_regroupement(reference):
    v = _vue(reference, None)
    groupes = set(l['grandeur'] for l in v['lignes'])
    assert moteur.GROUPE_AVEC_CRITERE in groupes


def test_la_vue_ne_mute_pas_le_resultat_du_moteur(reference, candidat_parfait):
    resultat = moteur.evaluer_test7(reference, candidat_parfait)
    avant = resultat['grandeurs'][0]['moyenne']
    v = vue.construire_vue_test7(resultat)
    v['lignes'][0]['detail']['moyenne'] = -12345.0
    assert resultat['grandeurs'][0]['moyenne'] == avant
