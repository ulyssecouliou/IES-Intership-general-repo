# -*- coding: utf-8 -*-
"""Tests du moteur generique des tests a bandes (2 et 3)."""

import pytest

from engine import scatter_band
from engine import sia_bandes_engine as moteur


def _ref(numero):
    try:
        return moteur.charger_reference(numero)
    except IOError:
        pytest.skip(u'reference Test %d absente' % numero)


def _candidat_au_centre(reference):
    return dict(
        (g['libelle_de'], dict((c['cas'], c['moyenne']) for c in g['cas']))
        for g in reference['grandeurs'])


@pytest.fixture(scope='module')
def ref2():
    return _ref(2)


@pytest.fixture(scope='module')
def ref3():
    return _ref(3)


@pytest.mark.parametrize('numero,bandes', [(2, 8), (3, 12)])
def test_nombre_de_bandes(numero, bandes):
    assert moteur.evaluer(_ref(numero), None)['nb_bandes'] == bandes


@pytest.mark.parametrize('numero', [2, 3])
def test_sans_candidat_rien_nest_conforme(numero):
    r = moteur.evaluer(_ref(numero), None)
    assert r['verdict'] == scatter_band.VERDICT_NOT_CHECKABLE
    assert r['nb_echecs'] == 0
    assert all(c['conforme'] is None
               for g in r['grandeurs'] for c in g['cas'])


@pytest.mark.parametrize('numero', [2, 3])
def test_candidat_au_centre_passe(numero):
    reference = _ref(numero)
    r = moteur.evaluer(reference, _candidat_au_centre(reference))
    assert r['verdict'] == scatter_band.VERDICT_PASS
    assert r['nb_non_evaluables'] == 0


def test_une_valeur_hors_bande_fait_echouer(ref2):
    candidat = _candidat_au_centre(ref2)
    grandeur = ref2['grandeurs'][0]
    cible = grandeur['cas'][0]
    candidat[grandeur['libelle_de']][cible['cas']] = cible['borne_haute'] + 500.0
    r = moteur.evaluer(ref2, candidat)
    assert r['verdict'] == scatter_band.VERDICT_FAIL
    assert r['nb_echecs'] == 1


def test_un_cas_manquant_bloque_sans_faire_echouer(ref2):
    """Le cas reel : tout passe sauf une bande non simulee."""
    candidat = _candidat_au_centre(ref2)
    grandeur = ref2['grandeurs'][0]
    del candidat[grandeur['libelle_de']][grandeur['cas'][0]['cas']]
    r = moteur.evaluer(ref2, candidat)
    assert r['verdict'] == scatter_band.VERDICT_NOT_CHECKABLE
    assert r['nb_non_evaluables'] == 1
    assert r['nb_echecs'] == 0


def test_un_echec_prime_sur_une_absence(ref2):
    candidat = _candidat_au_centre(ref2)
    grandeur = ref2['grandeurs'][0]
    del candidat[grandeur['libelle_de']][grandeur['cas'][0]['cas']]
    cible = grandeur['cas'][1]
    candidat[grandeur['libelle_de']][cible['cas']] = cible['borne_haute'] + 500.0
    assert moteur.evaluer(ref2, candidat)['verdict'] == scatter_band.VERDICT_FAIL


def test_les_bornes_sont_inclusives(ref2):
    candidat = _candidat_au_centre(ref2)
    grandeur = ref2['grandeurs'][0]
    for borne in ('borne_basse', 'borne_haute'):
        cible = grandeur['cas'][0]
        candidat[grandeur['libelle_de']][cible['cas']] = cible[borne]
        assert moteur.evaluer(ref2, candidat)['nb_echecs'] == 0, borne


def test_une_cle_non_appariee_est_signalee(ref2):
    """Une faute de frappe cote adaptateur ne doit pas passer inapercue."""
    candidat = _candidat_au_centre(ref2)
    candidat['Grandeur Inexistante'] = {'Test 2 A': 1.0}
    assert moteur.evaluer(ref2, candidat)['cles_candidat_ignorees']


def test_appariement_insensible_a_la_casse(ref2):
    candidat = dict(
        (g['libelle_de'].upper(), dict((c['cas'].lower(), c['moyenne'])
                                       for c in g['cas']))
        for g in ref2['grandeurs'])
    r = moteur.evaluer(ref2, candidat)
    assert r['nb_non_evaluables'] == 0
    assert r['cles_candidat_ignorees'] == []


@pytest.mark.parametrize('numero', [4, 6])
def test_le_critere_est_annonce_comme_infere(numero):
    """CORRIGE le 2026-08-07. Ce test portait sur les tests 2 et 3, sur la
    croyance que seul le Test 1 enoncait ses criteres. Relecture faite, les
    specifications 2, 3 et 5 enoncent la bande annuelle mot pour mot : leur
    statut est desormais ENONCE_DANS_LA_SPEC (voir plus bas). Seuls 4 et 6
    n'ont aucune section « Testkriterien », et pour eux INFERE reste exact."""
    r = moteur.evaluer(_ref(numero), None)
    assert r['critere']['statut'] == 'INFERE'
    assert all(c['critere_statut'] == 'INFERE'
               for g in r['grandeurs'] for c in g['cas'])


def test_les_variantes_de_programme_remontent(ref2):
    """Les colonnes sont des variantes : la variante retenue doit rester
    lisible dans le resultat, sinon on ne sait plus quoi comparer."""
    r = moteur.evaluer(ref2, None)
    cas = r['grandeurs'][0]['cas'][0]
    assert cas['programmes']
    assert len(cas['programmes']) == len(cas['contributeurs'])


def test_un_contributeur_absent_nest_pas_compte_comme_zero(ref2):
    for grandeur in ref2['grandeurs']:
        for cas in grandeur['cas']:
            valeurs = moteur.valeurs_contributrices(cas)
            assert len(valeurs) == len(cas['contributeurs'])
            assert all(v is not None for v in valeurs)


def test_le_test_7_est_refuse_par_ce_moteur():
    """Sa reference a une autre forme ; le message doit le dire."""
    with pytest.raises(ValueError, match='Test 7'):
        moteur.charger_reference(7)


def test_resume_mentionne_chaque_cas(ref3):
    texte = moteur.resumer(moteur.evaluer(ref3, None))
    for cas in ref3['grandeurs'][0]['cas']:
        assert cas['cas'] in texte



# --------------------------------------------------------------------------
# Statut du critere : enonce ou infere, selon le test
# --------------------------------------------------------------------------

import pytest as _pytest  # noqa: E402

from engine import sia_bandes_engine as _moteur  # noqa: E402


@_pytest.mark.parametrize('numero', (2, 3, 5))
def test_les_specs_2_3_et_5_enoncent_leur_critere(numero):
    """CORRIGE le 2026-08-07. On avait cru que seul le Test 1 enoncait ses
    criteres. Les specifications 2, 3 et 5 portent chacune une section
    « Testkriterien » qui enonce la bande annuelle mot pour mot. Les marquer
    INFERE affaiblissait a tort trois tests."""
    statut, justification = _moteur.critere_du_test(numero)
    assert statut == _moteur.STATUT_CRITERE_ENONCE
    assert 'Testkriterien' in justification
    assert 'Spezifikation_Test%d.pdf' % numero in justification


@_pytest.mark.parametrize('numero', (4, 6))
def test_les_specs_4_et_6_ne_fixent_aucun_critere(numero):
    """Elles n'ont aucune section « Testkriterien » : SIA 4010 §4.4 delegue au
    classeur. Le statut INFERE reste exact pour elles."""
    statut, justification = _moteur.critere_du_test(numero)
    assert statut == _moteur.STATUT_CRITERE
    assert '4.4' in justification


def test_un_test_inconnu_retombe_sur_le_statut_le_plus_faible():
    """Mieux vaut sous-estimer la force d'un critere que la surestimer."""
    assert _moteur.critere_du_test(99)[0] == _moteur.STATUT_CRITERE


@_pytest.mark.parametrize('numero', (2, 3, 4, 5, 6))
def test_le_resultat_porte_le_statut_du_test(numero):
    try:
        reference = _moteur.charger_reference(numero)
    except IOError:
        _pytest.skip(u'reference absente')
    resultat = _moteur.evaluer(reference)
    attendu, _ = _moteur.critere_du_test(numero)
    assert resultat['critere']['statut'] == attendu
    for grandeur in resultat['grandeurs']:
        for ligne in grandeur['cas']:
            assert ligne['critere_statut'] == attendu


def test_la_docstring_ne_dit_plus_que_seul_le_test_1_enonce_ses_criteres():
    """Elle l'affirmait, et c'etait faux. Une docstring fausse est une
    affirmation fausse de plus dans un dossier de validation."""
    assert 'only Test 1 states its criteria' not in _moteur.__doc__
    assert 'ENONCE_DANS_LA_SPEC' in _moteur.__doc__
