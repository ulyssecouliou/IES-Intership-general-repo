# -*- coding: utf-8 -*-
"""Tests des références figées des Tests 2 à 6.

Ces tests tournent SANS les classeurs SIA (118 Mo, hors dépôt) : ils
confrontent le JSON figé à lui-même, en recalculant chaque bande depuis les
valeurs par programme qu'il contient. Si quelqu'un éditait un JSON à la main,
ils le verraient.

Le contrôle contre le classeur, lui, est fait par
`scripts/build_sia_reference.py` au moment de l'extraction.
"""

import io
import json
import os

import pytest

from engine import scatter_band

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))
_REFS = os.path.join(_RACINE, 'refs', 'reference-data')


def _charger(numero):
    chemin = os.path.join(_REFS, 'test-%d.ref.json' % numero)
    if not os.path.exists(chemin):
        pytest.skip(u'référence Test %d absente' % numero)
    with io.open(chemin, encoding='utf-8') as flux:
        return json.load(flux)


@pytest.fixture(scope='module')
def test2():
    return _charger(2)


@pytest.fixture(scope='module')
def test3():
    return _charger(3)


def _toutes_les_bandes(reference):
    for grandeur in reference['grandeurs']:
        for cas in grandeur['cas']:
            yield grandeur, cas


@pytest.mark.parametrize('numero,nb_grandeurs,nb_bandes',
                         [(2, 2, 8), (3, 1, 12), (4, 3, 3), (5, 8, 16), (6, 6, 6)])
def test_le_nombre_de_bandes_est_celui_du_classeur(numero, nb_grandeurs, nb_bandes):
    reference = _charger(numero)
    assert len(reference['grandeurs']) == nb_grandeurs
    assert sum(len(g['cas']) for g in reference['grandeurs']) == nb_bandes


@pytest.mark.parametrize('numero', [2, 3, 4, 5, 6])
def test_chaque_bande_se_recalcule_depuis_ses_contributeurs(numero):
    """Preuve que le JSON n'a pas été édité à la main."""
    reference = _charger(numero)
    for grandeur, cas in _toutes_les_bandes(reference):
        valeurs = [cas['par_colonne'][l]['valeur'] for l in cas['contributeurs']]
        bande = scatter_band.build_band(valeurs,
                                        floor_at_zero=cas['plancher_a_zero'])
        for attendu, obtenu, nom in ((cas['moyenne'], bande.mean, 'moyenne'),
                                     (cas['borne_haute'], bande.upper_bound, 'haut'),
                                     (cas['borne_basse'], bande.lower_bound, 'bas')):
            assert abs(attendu - obtenu) < 1e-9, (numero, cas['cas'], nom)


def test_test2_a_bien_quatre_cas_2a_a_2d(test2):
    for grandeur in test2['grandeurs']:
        cas = [c['cas'] for c in grandeur['cas']]
        assert cas == ['Test 2 A', 'Test 2 B', 'Test 2 C', 'Test 2 D']


def test_test3_a_bien_douze_cas_3a_a_3l(test3):
    cas = [c['cas'] for c in test3['grandeurs'][0]['cas']]
    attendus = ['Test 3 %s' % lettre for lettre in 'ABCDEFGHIJKL']
    assert cas == attendus


def test_le_jeu_contributeur_varie_reellement(test2):
    """« ohne EDSL-Tas » : le cas 2A a quatre programmes, les autres trois.

    Si tous les jeux étaient identiques, c'est qu'on aurait lu la position au
    lieu de la formule.
    """
    premiere = test2['grandeurs'][0]['cas']
    jeux = [tuple(c['contributeurs']) for c in premiere]
    assert len(set(jeux)) > 1, jeux
    assert len(jeux[0]) == 4 and len(jeux[1]) == 3


def test_les_variantes_de_programme_sont_conservees(test2):
    """Les colonnes sont des variantes, pas des programmes : la variante
    retenue doit rester lisible dans le référentiel."""
    cas = test2['grandeurs'][0]['cas'][0]
    variantes = {c['programme']: c['variante'] for c in cas['par_colonne'].values()}
    assert any(v for v in variantes.values()), variantes


@pytest.mark.parametrize('numero', [2, 3, 5])
def test_le_critere_enonce_dans_la_spec_est_annonce_comme_tel(numero):
    """Les specs des tests 2, 3 et 5 ont bien une section « Testkriterien ».

    Ce test affirmait l'inverse : « seul le Test 1 énonce ses critères ». C'est
    faux, et la recherche plein texte dans les PDF officiels le montre — la
    section existe dans les trois, et elle énonce la bande annuelle dans la
    formule même que le moteur applique. Marquer ces trois tests INFERE
    affaiblissait à tort notre propre preuve.
    """
    reference = _charger(numero)
    assert reference['critere']['statut'] == 'ENONCE_DANS_LA_SPEC'
    origine = reference['critere']['origine']
    assert 'Testkriterien' in origine
    assert 'Spezifikation_Test%d.pdf' % numero in origine


@pytest.mark.parametrize('numero', [4, 6])
def test_le_critere_absent_de_la_spec_reste_infere(numero):
    """Les specs des tests 4 et 6 n'ont aucune section « Testkriterien ».

    Zéro occurrence en recherche plein texte, donc §4.4 délègue et le statut
    INFERE est exact. Ne pas le confondre avec la réponse d'autorité du
    2026-08-10, qui définit ce que veut dire « Streubereich » sans créer un
    critère là où la spécification n'en énonce pas.
    """
    reference = _charger(numero)
    assert reference['critere']['statut'] == 'INFERE'
    assert '4.4' in reference['critere']['origine']


@pytest.mark.parametrize('numero', [2, 3, 4, 5, 6])
def test_la_reference_et_le_moteur_saccordent_sur_le_critere(numero):
    """Le garde-fou contre la dérive qui a produit cette incohérence.

    La référence figée et le moteur tiennent chacun leur table du statut du
    critère, et c'est voulu : la référence est la preuve contre laquelle le
    moteur est jugé, elle ne peut pas dériver de lui. Le prix de cette
    indépendance est qu'ils peuvent diverger, comme ils l'ont fait entre le
    2026-08-07 et aujourd'hui. Ce test rend la divergence impossible à ignorer.
    """
    from engine import sia_bandes_engine as moteur

    reference = _charger(numero)
    statut_moteur, _justification = moteur.critere_du_test(numero)
    assert reference['critere']['statut'] == statut_moteur


@pytest.mark.parametrize('numero', [2, 3, 4, 5, 6])
def test_les_bornes_encadrent_la_moyenne(numero):
    reference = _charger(numero)
    for _, cas in _toutes_les_bandes(reference):
        assert cas['borne_basse'] <= cas['moyenne'] <= cas['borne_haute']


@pytest.mark.parametrize('numero', [2, 3, 4, 5, 6])
def test_chaque_grandeur_porte_un_libelle_et_une_unite(numero):
    """Un libellé « Testprogramm » ou une unité « Mittelwert » signalerait
    qu'on lit la mauvaise cellule -- erreur déjà commise et corrigée."""
    reference = _charger(numero)
    for grandeur in reference['grandeurs']:
        assert grandeur['libelle_de'], grandeur
        assert grandeur['libelle_de'] != 'Testprogramm'
        assert grandeur['unite'] == 'kWh', grandeur['unite']
