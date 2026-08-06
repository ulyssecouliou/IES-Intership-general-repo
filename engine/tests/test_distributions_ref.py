# -*- coding: utf-8 -*-
u"""Tests des distributions de fréquence de référence — tests SIA 2, 3 et 5.

Le second critère des spécifications 2, 3 et 5 — « Die Häufigkeitsverteilung
muss im Streubereich der Referenzprogramme liegen » — n'avait jamais été
extrait. Ces tests gardent le référentiel qui le porte.

Ils visent surtout ce qu'une extraction plausible mais fausse produirait :
compter une colonne de zéros comme une mesure, rater la ligne de totaux, ou
inventer une bande que le classeur ne calcule nulle part.
"""

import io
import json
import os

import pytest

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))
_DOSSIER = os.path.join(_RACINE, 'refs', 'reference-data')

TESTS = (2, 3, 5)

#: Tests dont la spécification ne comporte AUCUNE section « Testkriterien » et
#: dont le classeur n'a ni classes de fréquence ni feuille de distribution.
TESTS_SANS_DISTRIBUTION = (4, 6)


def _charger(numero):
    chemin = os.path.join(_DOSSIER, 'test-%d.distributions.ref.json' % numero)
    if not os.path.exists(chemin):
        pytest.skip(u'référentiel absent : '
                    u'scripts/build_sia_distribution_reference.py')
    with io.open(chemin, encoding='utf-8') as flux:
        return json.load(flux)


@pytest.fixture(scope='module', params=TESTS)
def reference(request):
    return _charger(request.param)


# --------------------------------------------------------------------------
# Le critère n'est pas inventé
# --------------------------------------------------------------------------

def test_le_critere_est_declare_non_calcule(reference):
    """Les feuilles « Verteilung » sont des GRAPHIQUES : aucune cellule du
    classeur ne définit la bande d'une distribution. Le déclarer, plutôt que
    de choisir une formule — ce serait inventer le critère."""
    assert reference['statut_critere'] == 'NON_CALCULE_PAR_LE_CLASSEUR'
    assert 'GRAPHIQUES' in reference['pourquoi_non_calcule']


def test_le_critere_cite_sa_source(reference):
    """Règle de traçabilité : chaque contrôle cite son article."""
    assert 'Streubereich' in reference['critere']
    assert 'Spezifikation_Test' in reference['critere']


def test_aucune_bande_nest_publiee(reference):
    """Si une clé de bande apparaissait, quelqu'un l'aurait calculée sans
    fondement. Le référentiel ne doit porter que des effectifs."""
    texte = json.dumps(reference, ensure_ascii=False).lower()
    for interdit in ('"borne_inf', '"borne_sup_bande', '"moyenne"',
                     '"ecart_max"', '"bande"'):
        assert interdit not in texte, interdit


# --------------------------------------------------------------------------
# Les effectifs sont réconciliés avec le classeur
# --------------------------------------------------------------------------

def test_chaque_contributeur_totalise_ce_que_le_classeur_annonce(reference):
    """Le garde-fou principal. Il valide DEUX choses d'un coup : la lecture
    des effectifs, et la détection de la ligne de totaux — qui n'est pas
    étiquetée dans le Test 3."""
    for bloc in reference['distributions']:
        for contributeur in bloc['contributeurs']:
            lettre = contributeur['colonne']
            somme = sum(e['par_colonne'][lettre] or 0
                        for e in bloc['effectifs'])
            assert somme == contributeur['total_heures'], (
                reference['test'], bloc['colonne_bloc'], lettre)


def test_aucune_colonne_de_zeros_nest_retenue(reference):
    """Une colonne pleine de zéros signale un programme qui n'a PAS soumis ce
    cas, pas un programme ayant compté zéro heure. La compter comme une mesure
    fausserait toute la dispersion."""
    for bloc in reference['distributions']:
        for contributeur in bloc['contributeurs']:
            assert contributeur['total_heures'] > 0


def test_les_effectifs_ne_sont_jamais_negatifs(reference):
    for bloc in reference['distributions']:
        for effectif in bloc['effectifs']:
            for valeur in effectif['par_colonne'].values():
                assert valeur is None or valeur >= 0


def test_tous_les_blocs_ont_le_meme_nombre_de_classes(reference):
    """Les classes viennent d'une feuille commune : un bloc qui en aurait un
    nombre différent signalerait une lecture décalée."""
    nombres = set(bloc['nb_classes'] for bloc in reference['distributions'])
    assert len(nombres) == 1, nombres


def test_les_bornes_sont_croissantes(reference):
    """Des bornes désordonnées signaleraient une colonne mal repérée."""
    for bloc in reference['distributions']:
        bornes = [e['borne_superieure'] for e in bloc['effectifs']
                  if e['borne_superieure'] is not None]
        assert bornes == sorted(bornes), bloc['colonne_bloc']


# --------------------------------------------------------------------------
# Ce que le relevé dit de lui-même
# --------------------------------------------------------------------------

def test_les_totaux_partiels_sont_conserves_pas_completes(reference):
    """Plusieurs programmes totalisent moins de 8760 heures. Les compléter
    fausserait la dispersion ; les taire la rendrait inexplicable."""
    totaux = set(c['total_heures'] for bloc in reference['distributions']
                 for c in bloc['contributeurs'])
    if any(t < 8760 for t in totaux):
        texte = u' '.join(reference['reserves'])
        assert u'8760' in texte


def test_un_bloc_sans_cas_est_signale(reference):
    """Le Test 5 porte un bloc que le classeur ne rattache à aucun cas. Le
    champ reste nul, et la réserve le dit."""
    sans_cas = [b for b in reference['distributions'] if not b['cas']]
    if sans_cas:
        assert any('identifiant de cas' in r for r in reference['reserves'])


def test_les_reserves_rappellent_que_la_bande_manque(reference):
    assert any('statut_critere' in r for r in reference['reserves'])


def test_chaque_bloc_nomme_sa_grandeur(reference):
    for bloc in reference['distributions']:
        assert bloc['grandeur'], bloc['colonne_bloc']


def test_la_source_est_tracable(reference):
    source = reference['source']
    assert source['fichier'].endswith('.xlsx')
    assert source['feuille']
    assert set(source['lignes_de_structure']) == {
        'cas', 'grandeur', 'programmes', 'classes'}


# --------------------------------------------------------------------------
# Portée
# --------------------------------------------------------------------------

@pytest.mark.parametrize('numero', TESTS_SANS_DISTRIBUTION)
def test_les_tests_4_et_6_nont_pas_de_distribution(numero):
    """Constat, pas oubli : leurs classeurs n'ont ni feuille
    « Haeufigkeitsklassen » ni feuille de distribution, et leurs
    spécifications ne fixent aucun Testkriterium."""
    chemin = os.path.join(_DOSSIER,
                          'test-%d.distributions.ref.json' % numero)
    assert not os.path.exists(chemin)


def test_lextracteur_refuse_un_test_hors_perimetre():
    from scripts import build_sia_distribution_reference as extracteur
    with pytest.raises(extracteur.ExtractionRefusee, match='seul critère'):
        extracteur.extraire(4)


@pytest.mark.parametrize('numero,attendu', [(2, 22), (3, 16), (5, 16)])
def test_le_nombre_de_distributions_est_fige(numero, attendu):
    """54 distributions au total. Si le compte changeait, ce serait soit un
    classeur différent, soit une lecture décalée — les deux méritent un
    échec."""
    assert _charger(numero)['nb_distributions'] == attendu
