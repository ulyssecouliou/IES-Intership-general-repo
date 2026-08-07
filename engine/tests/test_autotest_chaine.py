# -*- coding: utf-8 -*-
u"""Tests de l'auto-test de chaîne (`scripts/autotest_chaine.py`).

Ce script a une propriété qu'il faut verrouiller : il doit **échouer** si la
chaîne se casse, et ne **jamais** laisser croire qu'il valide quoi que ce soit.
Un auto-test qui passerait toujours ne servirait à rien ; un auto-test qu'on
prendrait pour une validation serait pire qu'inutile.
"""

import pytest

from engine import sia_bandes_engine as moteur
from scripts import autotest_chaine as auto


@pytest.fixture(scope='module')
def rendus():
    try:
        return auto.executer()
    except IOError:
        pytest.skip(u'références absentes')


# --------------------------------------------------------------------------
# La chaîne tient
# --------------------------------------------------------------------------

def test_les_cinq_tests_a_bandes_passent_la_chaine(rendus):
    assert len(rendus) == len(auto.TESTS)


def test_chaque_test_rejoue_au_moins_un_cas(rendus):
    """Zéro cas rejoué se lirait comme « chaîne verte » alors que rien
    n'aurait été évalué."""
    for rendu in rendus:
        assert rendu['bandes']['nb_cas_rejoues'] > 0, rendu['bandes']['test']


def test_chaque_test_produit_une_vue_non_vide(rendus):
    for rendu in rendus:
        assert rendu['vue']['nb_lignes'] > 0, rendu['vue']['test_id']


def test_les_distributions_sont_evaluees_quand_elles_existent(rendus):
    for rendu in rendus:
        distributions = rendu['distributions']
        if distributions is None:
            continue
        assert distributions['nb_evaluees'] == distributions['nb_distributions']


@pytest.mark.parametrize('numero', (4, 6))
def test_les_tests_sans_distribution_le_declarent(numero):
    assert auto.verifier_distributions(numero) is None


# --------------------------------------------------------------------------
# Il ne prétend rien valider
# --------------------------------------------------------------------------

def test_le_module_dit_ce_quil_ne_prouve_pas():
    assert 'ne prouve **rien** sur IESVE' in auto.__doc__


def test_les_distributions_restent_non_etablies(rendus):
    """Même rejouées à l'identique, elles ne concluent pas : le classeur
    officiel ne définit aucune bande de distribution."""
    for rendu in rendus:
        if rendu['distributions']:
            assert rendu['distributions']['verdict'] == 'NON_ETABLI'


def test_le_statut_du_critere_remonte_tel_quel(rendus):
    """ENONCE_DANS_LA_SPEC pour 2, 3 et 5 ; INFERE pour 4 et 6. L'auto-test ne
    doit pas uniformiser ce que la norme distingue."""
    par_test = dict((r['bandes']['test'], r['bandes']['critere'])
                    for r in rendus)
    assert par_test[2] == moteur.STATUT_CRITERE_ENONCE
    assert par_test[5] == moteur.STATUT_CRITERE_ENONCE
    assert par_test[4] == moteur.STATUT_CRITERE
    assert par_test[6] == moteur.STATUT_CRITERE


# --------------------------------------------------------------------------
# Il échoue quand la chaîne se casse
# --------------------------------------------------------------------------

def test_un_candidat_hors_bande_fait_echouer(monkeypatch):
    """Le seul moyen d'y arriver est de casser la chaîne : un contributeur
    tombe dans sa propre bande par construction."""
    vrai = auto.candidat_depuis_contributeur

    def fausse(reference, lettre):
        candidat = vrai(reference, lettre)
        for par_cas in candidat.values():
            for cas in par_cas:
                par_cas[cas] = par_cas[cas] * 1000.0 + 1.0
            break
        return candidat

    monkeypatch.setattr(auto, 'candidat_depuis_contributeur', fausse)
    with pytest.raises(auto.ChaineDefaillante, match='impossible'):
        auto.verifier_bandes(3)


def test_un_referentiel_sans_contributeur_est_refuse(monkeypatch):
    monkeypatch.setattr(
        auto.moteur_bandes, 'charger_reference',
        lambda numero, chemin=None: {'test': numero, 'grandeurs': []})
    with pytest.raises(auto.ChaineDefaillante, match='aucun contributeur'):
        auto.verifier_bandes(3)


def test_main_rend_zero_quand_la_chaine_tient():
    assert auto.main(('3',)) == 0


def test_main_rend_un_quand_elle_casse(monkeypatch):
    def casse(numero):
        raise auto.ChaineDefaillante(u'defaut simule')
    monkeypatch.setattr(auto, 'verifier_bandes', casse)
    assert auto.main(('3',)) == 1


# --------------------------------------------------------------------------
# Choix du programme rejoué
# --------------------------------------------------------------------------

def test_le_programme_retenu_est_le_plus_present():
    reference = {'grandeurs': [{'cas': [
        {'contributeurs': ['A', 'B']}, {'contributeurs': ['B']}]}]}
    assert auto.choisir_contributeur(reference) == 'B'


def test_a_egalite_le_choix_est_deterministe():
    """Un choix instable rendrait deux exécutions incomparables."""
    reference = {'grandeurs': [{'cas': [{'contributeurs': ['Z', 'A']}]}]}
    assert auto.choisir_contributeur(reference) == 'A'


def test_sans_contributeur_aucun_programme_nest_choisi():
    assert auto.choisir_contributeur({'grandeurs': []}) is None


def test_les_cas_ou_le_programme_est_absent_sont_ecartes():
    """Le compter à zéro déplacerait la moyenne, donc la bande."""
    reference = {'grandeurs': [{'libelle_de': 'G', 'cas': [
        {'cas': 'avec', 'contributeurs': ['A'],
         'par_colonne': {'A': {'valeur': 1.0}}},
        {'cas': 'sans', 'contributeurs': ['B'],
         'par_colonne': {'B': {'valeur': 2.0}}}]}]}
    assert auto.candidat_depuis_contributeur(reference, 'A') == {
        'G': {'avec': 1.0}}
