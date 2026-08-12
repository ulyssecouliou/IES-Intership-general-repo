# -*- coding: utf-8 -*-
"""Tests de la vue des tests a bandes et de la subsomption de couverture."""

import pytest

from engine import sia_bandes_engine as moteur
from ui import verdict_view as vue


def _ref(numero):
    try:
        return moteur.charger_reference(numero)
    except IOError:
        pytest.skip(u'reference Test %d absente' % numero)


def _vue(numero, candidat=None):
    return vue.construire_vue_bandes(moteur.evaluer(_ref(numero), candidat))


def _centre(reference):
    return dict(
        (g['libelle_de'], dict((c['cas'], c['moyenne']) for c in g['cas']))
        for g in reference['grandeurs'])


# --------------------------------------------------------------------------
# Contrat de vue
# --------------------------------------------------------------------------

@pytest.mark.parametrize('numero,lignes', [(2, 8), (3, 12)])
def test_une_ligne_par_bande(numero, lignes):
    assert len(_vue(numero)['lignes']) == lignes


@pytest.mark.parametrize('numero', [2, 3])
def test_respecte_le_contrat_commun(numero):
    v = _vue(numero)
    for cle in ('test_id', 'numero_test', 'verdict_global', 'classes', 'lignes'):
        assert cle in v, cle
    assert v['numero_test'] == str(numero)


@pytest.mark.parametrize('numero', [2, 3])
def test_sans_candidat_tout_est_gris(numero):
    v = _vue(numero)
    assert v['verdict_global']['couleur'] == 'gris'
    assert all(l['couleur'] == 'gris' for l in v['lignes'])
    assert all(l['valeur_candidate_affichee'] == u'—' for l in v['lignes'])


def test_candidat_au_centre_tout_est_vert():
    reference = _ref(2)
    v = vue.construire_vue_bandes(moteur.evaluer(reference, _centre(reference)))
    assert v['verdict_global']['couleur'] == 'vert'
    assert all(l['couleur'] == 'vert' for l in v['lignes'])


@pytest.mark.parametrize('numero', [2, 3])
def test_larticle_annonce_le_critere_comme_enonce_dans_la_spec(numero):
    u"""L'article citait « Critère INFÉRÉ » pour tous les tests à bandes.

    Faux pour les tests 2, 3 et 5 : leurs spécifications comportent une section
    « Testkriterien » qui énonce la bande annuelle mot pour mot — vérifié dans
    les PDF officiels. L'interface sous-estimait donc notre propre preuve, et
    devant la sous-commission une preuve affaiblie sans raison se défend mal.

    Ce qui est testé n'est pas le mot, mais que l'article cite la section de la
    spécification qui porte le critère.
    """
    v = _vue(numero)
    articles = [v['verdict_global']['article']]
    articles.extend(l['article'] for l in v['lignes'])
    assert articles
    for article in articles:
        assert u'ÉNONCÉ' in article
        assert u'Testkriterien' in article
        assert u'Spezifikation_Test%d.pdf' % numero in article
        assert u'INFÉRÉ' not in article


def test_la_note_sur_les_variantes_est_portee(numero=2):
    """Sans elle, personne ne sait que les colonnes sont des variantes."""
    assert 'VARIANTES' in _vue(numero)['note_variantes']


def test_le_resume_de_bande_montre_moyenne_et_bornes():
    v = _vue(2)
    for ligne in v['lignes']:
        detail = ligne['detail']
        assert vue.formater_nombre(detail['moyenne'], 1) in ligne['reference_affichee']


# --------------------------------------------------------------------------
# Subsomption : un test complet couvre ses sous-ensembles
# --------------------------------------------------------------------------

def _vue_minimale(numero, couleur='gris'):
    conforme = {'vert': True, 'rouge': False, 'gris': None}[couleur]
    return {
        'test_id': u'Test ' + numero, 'numero_test': numero,
        'verdict_global': {'conforme': conforme, 'couleur': couleur,
                           'texte': u'x', 'article': u''},
        'classes': [], 'lignes': [],
    }


def test_le_test_2_complet_couvre_lexigence_2a():
    """Tab. 63 exige « Test 2A » pour la classe 1A : le Test 2 entier
    l'englobe. L'ignorer laisserait la classe marquee incomplete alors que
    tout ce qu'elle reclame est present."""
    lignes = dict((l['classe'], l) for l in vue.construire_synthese_classes(
        [_vue_minimale('1', 'vert'), _vue_minimale('2', 'vert')]))
    assert lignes['1A']['tests_manquants'] == []
    assert lignes['1A']['conforme'] is True


def test_le_test_3_complet_couvre_lexigence_3a_f():
    lignes = dict((l['classe'], l) for l in vue.construire_synthese_classes(
        [_vue_minimale('1', 'vert'), _vue_minimale('2', 'vert'),
         _vue_minimale('3', 'vert')]))
    assert lignes['2A']['tests_manquants'] == []
    assert lignes['2B']['tests_manquants'] == []


def test_la_subsomption_ne_marche_pas_a_lenvers():
    """Couvrir 2A ne couvre PAS le Test 2 : la classe 1B doit rester
    incomplete."""
    lignes = dict((l['classe'], l) for l in vue.construire_synthese_classes(
        [_vue_minimale('1', 'vert'), _vue_minimale('2A', 'vert')]))
    assert lignes['1B']['tests_manquants'] == ['2']


def test_les_huit_classes_ont_tous_leurs_tests_couverts():
    """Etat reel du depot depuis que les sept tests ont leurs references.

    Les huit classes sont completement couvertes ; elles restent GRISES faute
    de simulation VE, plus faute de tests. C est un changement de nature : le
    rapport ne dit plus « il manque des tests » mais « il manque des
    resultats »."""
    from ui import dialog_tkinter as dlg
    lignes = vue.construire_synthese_classes(dlg.construire_vues_disponibles()[0])
    assert [l['classe'] for l in lignes if not l['tests_manquants']] == [
        '1A', '1B', '2A', '2B', '3', '4A', '4B', '5']
    # ...et aucune n est verte, faute de candidat.
    assert all(l['couleur'] == 'gris' for l in lignes)
