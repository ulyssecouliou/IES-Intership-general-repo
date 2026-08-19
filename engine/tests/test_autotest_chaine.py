# -*- coding: utf-8 -*-
u"""Tests of the chain self-test (`scripts/autotest_chaine.py`).

This script has a property that must be locked: it must **fail** if the
chain breaks, and must **never** make anyone believe it validates anything.
A self-test that always passed would be useless; a self-test taken for a
validation would be worse than useless.
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
# The chain holds
# --------------------------------------------------------------------------

def test_les_sept_tests_passent_la_chaine(rendus):
    assert len(rendus) == len(auto.TESTS)
    assert [r['bandes']['test'] for r in rendus] == list(range(1, 8))


def test_chaque_test_rejoue_au_moins_un_cas(rendus):
    """Zero replayed cases would read as 'chain green' while nothing
    would have been evaluated."""
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
def test_les_tests_sans_referentiel_distribution_executable_le_declarent(numero):
    """Their presence is confirmed, but the exact gate is still under review."""
    assert auto.verifier_distributions(numero) is None


def test_tests_1_et_7_passent_par_leurs_moteurs_dedies(rendus):
    par_test = dict((r['bandes']['test'], r) for r in rendus)
    assert par_test[1]['bandes']['nb_cas_rejoues'] == 28
    assert par_test[1]['bandes']['critere'] == 'ENONCE_DANS_LA_SPEC'
    assert par_test[7]['bandes']['nb_cas_rejoues'] == 11
    assert par_test[7]['bandes']['critere'] == (
        'CLASSEUR_CORRIGE_VERIFIE_2026-08-10'
    )
    assert par_test[1]['vue']['nb_lignes'] > 0
    assert par_test[7]['vue']['nb_lignes'] == 11


# --------------------------------------------------------------------------
# It claims to validate nothing
# --------------------------------------------------------------------------

def test_le_module_dit_ce_quil_ne_prouve_pas():
    assert 'proves **nothing** about IESVE' in auto.__doc__


def test_les_distributions_rejouees_passent_enveloppe_confirmee(rendus):
    """A reference programme must remain within its own min/max envelope."""
    for rendu in rendus:
        if rendu['distributions']:
            assert rendu['distributions']['verdict'] == 'PASS'
            assert rendu['distributions']['critere'] == (
                'CONFIRME_AUTORITE_2026-08-10'
            )


def test_le_statut_du_critere_remonte_tel_quel(rendus):
    """ENONCE_DANS_LA_SPEC for 2, 3 and 5; INFERE for 4 and 6. The self-test
    must not flatten what the norm distinguishes."""
    par_test = dict((r['bandes']['test'], r['bandes']['critere'])
                    for r in rendus)
    assert par_test[2] == moteur.STATUT_CRITERE_ENONCE
    assert par_test[5] == moteur.STATUT_CRITERE_ENONCE
    assert par_test[4] == moteur.STATUT_CRITERE
    assert par_test[6] == moteur.STATUT_CRITERE


# --------------------------------------------------------------------------
# It fails when the chain breaks
# --------------------------------------------------------------------------

def test_un_candidat_hors_bande_fait_echouer(monkeypatch):
    """The only way to get there is to break the chain: a contributor
    falls within its own band by construction."""
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
# Choice of the replayed programme
# --------------------------------------------------------------------------

def test_le_programme_retenu_est_le_plus_present():
    reference = {'grandeurs': [{'cas': [
        {'contributeurs': ['A', 'B']}, {'contributeurs': ['B']}]}]}
    assert auto.choisir_contributeur(reference) == 'B'


def test_a_egalite_le_choix_est_deterministe():
    """An unstable choice would make two runs incomparable."""
    reference = {'grandeurs': [{'cas': [{'contributeurs': ['Z', 'A']}]}]}
    assert auto.choisir_contributeur(reference) == 'A'


def test_sans_contributeur_aucun_programme_nest_choisi():
    assert auto.choisir_contributeur({'grandeurs': []}) is None


def test_les_cas_ou_le_programme_est_absent_sont_ecartes():
    """Counting it as zero would shift the mean, hence the band."""
    reference = {'grandeurs': [{'libelle_de': 'G', 'cas': [
        {'cas': 'avec', 'contributeurs': ['A'],
         'par_colonne': {'A': {'valeur': 1.0}}},
        {'cas': 'sans', 'contributeurs': ['B'],
         'par_colonne': {'B': {'valeur': 2.0}}}]}]}
    assert auto.candidat_depuis_contributeur(reference, 'A') == {
        'G': {'avec': 1.0}}
