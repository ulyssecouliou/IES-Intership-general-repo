# -*- coding: utf-8 -*-
"""Unit tests for the SIA 4010 Test 1 validation engine (`engine/test1_engine.py`).

Reference-driven development (CLAUDE.md): each check loads a value already
frozen and audited in `refs/reference-data/test-1.ref.json` and requires
the engine to reproduce it within tolerance, rather than inventing synthetic
fixtures for everything. Synthetic cases are only used for out-of-band
scenarios or input shapes that no real data covers
(missing candidate, candidate clearly outside Streubereich, invalid shapes).

No `import iesve`; compatible with Python 3.4 (no f-strings), cf.
`docs/ADR-001-architecture-MSP.md` §2 and `engine/tests/test_ref_integrity.py`.
"""

import os
import sys

import pytest

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

from engine import test1_engine as moteur  # noqa: E402


TOLERANCE = 1e-6


@pytest.fixture(scope='module')
def reference():
    return moteur.charger_reference()


def _proche(gauche, droite, tolerance=TOLERANCE):
    return abs(gauche - droite) <= tolerance


# --------------------------------------------------------------------------
# 1. Loading the frozen reference
# --------------------------------------------------------------------------

def test_charger_reference_par_defaut_expose_les_cinq_grandeurs():
    """Five since pass 4: Table 31 (hourly peak loads for case
    1E) was added after the audit of the existing loader, which was reading it
    while the reference ignored it (AUDIT-swiss-sia-existant.md, item 3)."""
    ref = moteur.charger_reference()
    assert set(ref['reference_values'].keys()) == {
        'sensible_heating_demand_kwh',
        'sensible_cooling_demand_kwh',
        'operative_temperature_monthly_celsius',
        'operative_temperature_annual_extremes_celsius',
        'annual_hourly_peak_load_kwh',
    }


def test_charger_reference_chemin_explicite_equivaut_au_defaut(reference):
    ref_explicite = moteur.charger_reference(moteur.CHEMIN_REFERENCE_DEFAUT)
    assert ref_explicite['test_id'] == reference['test_id']


# --------------------------------------------------------------------------
# 2. `calculer_plage_dispersion` -- reproduces EXACTLY the audited formula,
#    on ALL real periods (1E, heating + cooling, 26
#    periods as in AUDIT.md pt 4 / re-audit pass 3).
# --------------------------------------------------------------------------

def _enregistrements_1e(reference, grandeur):
    noeud = reference['reference_values'][grandeur]['1E']
    for mois in moteur.MOIS:
        yield mois, noeud['monthly'][mois]
    yield 'annual', noeud['annual']


def test_plage_dispersion_reproduit_la_reference_sur_toutes_les_periodes(reference):
    """Each `range_min`/`range_max` already computed by the official Excel must be
    reproduced by `calculer_plage_dispersion` from the 4 raw programmes."""
    verifiees = 0
    for grandeur in ('sensible_heating_demand_kwh', 'sensible_cooling_demand_kwh'):
        for _label, enregistrement in _enregistrements_1e(reference, grandeur):
            valeurs = [moteur._valeur_reelle(enregistrement[p])
                       for p in moteur.PROGRAMMES_REFERENCE_1E]
            moyenne, _ecart, plage_min, plage_max = moteur.calculer_plage_dispersion(
                valeurs)
            attendu_max = moteur._valeur_reelle(enregistrement['range_max'])
            attendu_min = moteur._valeur_reelle(enregistrement['range_min'])
            attendu_moyenne = moteur._valeur_reelle(enregistrement['mean_of_programs'])
            assert _proche(plage_max, attendu_max)
            assert _proche(plage_min, attendu_min)
            assert _proche(moyenne, attendu_moyenne)
            verifiees += 1
    # 12 months + annual, for heating and cooling = 26 (AUDIT.md pt 4).
    assert verifiees == 26


def test_plage_dispersion_nest_pas_le_min_max_brut():
    """Explicit safeguard against the misconception corrected by the audit (AUDIT.md pt 4):
    the Streubereich is NOT [min(values), max(values)]."""
    valeurs = [10.0, 12.0, 8.0, 50.0]
    moyenne, ecart_max, plage_min, plage_max = moteur.calculer_plage_dispersion(valeurs)
    assert moyenne == 20.0
    assert ecart_max == 30.0  # |50 - 20|
    assert plage_max == 50.0
    assert plage_min == 0.0  # floor at 0 (mean - ecart_max = -10 < 0)
    # The raw min/max of the values (8, 50) differs from the Streubereich (0, 50):
    assert (plage_min, plage_max) != (min(valeurs), max(valeurs))


def test_plage_dispersion_leve_si_aucune_valeur():
    with pytest.raises(ValueError):
        moteur.calculer_plage_dispersion([])


# --------------------------------------------------------------------------
# 3. `evaluer_periode_1e` -- the only pass/fail verdict of Test 1
# --------------------------------------------------------------------------

def test_1e_candidat_egal_a_la_moyenne_est_conforme(reference):
    """The programme mean is, by construction, always within its own
    band (AUDIT.md pt 4: verified 26/26): a candidate that reproduces it must
    therefore pass the criterion."""
    enregistrement = reference['reference_values'][
        'sensible_heating_demand_kwh']['1E']['annual']
    moyenne = moteur._valeur_reelle(enregistrement['mean_of_programs'])
    resultat = moteur.evaluer_periode_1e(enregistrement, moyenne)
    assert resultat['conforme'] is True
    assert resultat['coherence_reference'] is True
    assert resultat['marge_min'] >= 0
    assert resultat['marge_max'] >= 0


def test_1e_candidat_egal_a_un_programme_de_reference_est_conforme(reference):
    """A candidate identical to ONE of the 4 reference programmes must fall within
    the band, since this band brackets the maximum deviation observed between
    the programmes and their mean."""
    enregistrement = reference['reference_values'][
        'sensible_cooling_demand_kwh']['1E']['monthly']['month_07']
    valeur_ida = moteur._valeur_reelle(enregistrement['ida_ice_5_0_beta_23'])
    resultat = moteur.evaluer_periode_1e(enregistrement, valeur_ida)
    assert resultat['conforme'] is True


def test_1e_candidat_sur_la_borne_exacte_est_conforme(reference):
    """`range_min <= candidat <= range_max`: the bound itself is included
    (AUDIT.md: "range_min <= candidat <= range_max"), not a strict inequality."""
    enregistrement = reference['reference_values'][
        'sensible_heating_demand_kwh']['1E']['annual']
    plage_max = moteur._valeur_reelle(enregistrement['range_max'])
    plage_min = moteur._valeur_reelle(enregistrement['range_min'])
    assert moteur.evaluer_periode_1e(enregistrement, plage_max)['conforme'] is True
    assert moteur.evaluer_periode_1e(enregistrement, plage_min)['conforme'] is True


def test_1e_candidat_nettement_hors_bande_est_rejete(reference):
    """Synthetic out-of-band case: no real data can cover an
    aberrant candidate since the IESVE candidate has not yet been computed."""
    enregistrement = reference['reference_values'][
        'sensible_heating_demand_kwh']['1E']['annual']
    plage_max = moteur._valeur_reelle(enregistrement['range_max'])
    candidat_trop_haut = plage_max + 1000.0
    resultat = moteur.evaluer_periode_1e(enregistrement, candidat_trop_haut)
    assert resultat['conforme'] is False
    assert resultat['marge_max'] < 0
    assert resultat['marge_min'] > 0

    plage_min = moteur._valeur_reelle(enregistrement['range_min'])
    candidat_trop_bas = plage_min - 1000.0
    if candidat_trop_bas < 0:
        # The band floor is 0 (cf. formula): verify that a negative candidate
        # outside the band is indeed rejected, not just "below the mean".
        resultat_bas = moteur.evaluer_periode_1e(enregistrement, candidat_trop_bas)
        assert resultat_bas['conforme'] is False
        assert resultat_bas['marge_min'] < 0


def test_1e_candidat_absent_ne_produit_aucun_verdict(reference):
    """A candidate not yet provided (VE Script not yet run) must stay
    `conforme=None` with an explicit reason -- never an invented `False`."""
    enregistrement = reference['reference_values'][
        'sensible_heating_demand_kwh']['1E']['annual']
    resultat = moteur.evaluer_periode_1e(enregistrement, None)
    assert resultat['conforme'] is None
    assert 'motif' in resultat
    assert 'marge_min' not in resultat
    assert 'marge_max' not in resultat


def test_1e_leve_si_un_programme_de_reference_manque():
    """An incomplete 1E record (missing programme) must raise an explicit error
    rather than silently computing a wrong band."""
    enregistrement_incomplet = {
        'ida_ice_5_0_beta_23': {'value': 100.0, 'unit': 'kWh', 'cell': 'C1'},
        'excel_sia_380_2': {'value': 110.0, 'unit': 'kWh', 'cell': 'D1'},
        'energyplus_openstudio_9_1_0': {'value': 90.0, 'unit': 'kWh', 'cell': 'E1'},
        # tas_edsl_9_5_2 missing
        'range_max': {'value': 120.0, 'unit': 'kWh', 'cell': 'H1'},
        'range_min': {'value': 80.0, 'unit': 'kWh', 'cell': 'I1'},
    }
    with pytest.raises(ValueError):
        moteur.evaluer_periode_1e(enregistrement_incomplet, 100.0)


def test_1e_coherence_reference_detecte_une_plage_stockee_divergente(reference):
    """If the columns already computed by the Excel diverged from the independent
    recomputation of the engine, `coherence_reference` must switch to False (safeguard
    ADR-001 §4 pt 2). Simulated on a modified copy of a real record."""
    import copy
    enregistrement = copy.deepcopy(reference['reference_values'][
        'sensible_heating_demand_kwh']['1E']['annual'])
    enregistrement['range_max']['value'] += 500.0  # intentional divergence
    resultat = moteur.evaluer_periode_1e(enregistrement, 0.0)
    assert resultat['coherence_reference'] is False


# --------------------------------------------------------------------------
# 4. `comparer_periode_informative` -- NO verdict, for all other cases
# --------------------------------------------------------------------------

def test_informatif_ne_produit_jamais_de_verdict(reference):
    enregistrement = reference['reference_values'][
        'sensible_heating_demand_kwh']['600']['annual']
    resultat = moteur.comparer_periode_informative(enregistrement, 5000.0)
    assert resultat['conforme'] is None
    assert resultat['type_controle'] == 'informatif'


def test_informatif_delta_nul_si_candidat_egal_a_un_programme(reference):
    enregistrement = reference['reference_values'][
        'sensible_heating_demand_kwh']['600']['annual']
    valeur_iso = moteur._valeur_reelle(enregistrement['iso_52016_1_2017_reference'])
    resultat = moteur.comparer_periode_informative(enregistrement, valeur_iso)
    comparaison_iso = resultat['comparaisons']['iso_52016_1_2017_reference']
    assert _proche(comparaison_iso['delta_absolu'], 0.0)
    assert _proche(comparaison_iso['delta_relatif_pct'], 0.0)
    # The other programmes must show a non-zero delta (distinct real data
    # -- verifies we are not comparing everything to the same number).
    comparaison_tas = resultat['comparaisons']['tas_edsl_9_5_2']
    assert comparaison_tas['delta_absolu'] != 0.0


def test_informatif_candidat_absent_laisse_les_references_visibles(reference):
    """Even without a candidate, the reference values (informative comparison)
    remain exposed -- only the delta becomes None."""
    enregistrement = reference['reference_values'][
        'operative_temperature_monthly_celsius']['600']['monthly']['month_01']
    resultat = moteur.comparer_periode_informative(enregistrement, None)
    assert resultat['valeur_candidate'] is None
    for comparaison in resultat['comparaisons'].values():
        assert comparaison['reference'] is not None
        assert comparaison['delta_absolu'] is None


def test_informatif_gere_les_cas_600ff_900ff_temperature(reference):
    """Cases 600FF/900FF (free float): only controlled output = operative
    temperature, always without verdict (spec §6)."""
    enregistrement = reference['reference_values'][
        'operative_temperature_monthly_celsius']['600FF']['monthly']['annual']
    resultat = moteur.comparer_periode_informative(enregistrement, 24.0)
    assert resultat['conforme'] is None
    assert 'ida_ice_5_0_beta_23' in resultat['comparaisons']


def test_informatif_gere_les_extremes_table_32(reference):
    enregistrement = reference['reference_values'][
        'operative_temperature_annual_extremes_celsius']['600FF']['extremes']['max']
    resultat = moteur.comparer_periode_informative(enregistrement, 65.0)
    assert resultat['conforme'] is None
    assert resultat['comparaisons']['ida_ice_5_0_beta_23']['reference'] is not None


# --------------------------------------------------------------------------
# 5. `_valeur_candidate` -- explicit shape tolerance, rejection of the rest
# --------------------------------------------------------------------------

@pytest.mark.parametrize('entree,attendu', [
    (None, None),
    (42, 42.0),
    (42.5, 42.5),
    ({'value': 42.5}, 42.5),
    ({'value': 42.5, 'unit': 'kWh', 'cell': 'B1'}, 42.5),
])
def test_valeur_candidate_formes_acceptees(entree, attendu):
    assert moteur._valeur_candidate(entree) == attendu


@pytest.mark.parametrize('entree', ['42', [42.0], True, False])
def test_valeur_candidate_formes_rejetees(entree):
    with pytest.raises(TypeError):
        moteur._valeur_candidate(entree)


# --------------------------------------------------------------------------
# 6. Orchestration -- `evaluer_cas` / `evaluer_test1`
# --------------------------------------------------------------------------

def test_evaluer_cas_1e_toutes_periodes_conformes_si_candidat_egal_a_la_moyenne(
        reference):
    """Builds a 1E candidate entirely equal to `mean_of_programs` (monthly +
    annual): the case must come out fully conforming."""
    noeud_1e = reference['reference_values']['sensible_heating_demand_kwh']['1E']
    candidat_mensuel = {}
    for mois in moteur.MOIS:
        candidat_mensuel[mois] = moteur._valeur_reelle(
            noeud_1e['monthly'][mois]['mean_of_programs'])
    candidat_cas = {
        'monthly': candidat_mensuel,
        'annual': moteur._valeur_reelle(noeud_1e['annual']['mean_of_programs']),
    }
    resultats = moteur.evaluer_cas(
        reference, 'sensible_heating_demand_kwh', '1E', candidat_cas)
    assert len(resultats) == 13  # 12 months + annual
    assert all(v['conforme'] is True for v in resultats.values())


def test_evaluer_cas_informatif_ne_leve_jamais_meme_sans_candidat(reference):
    resultats = moteur.evaluer_cas(
        reference, 'sensible_heating_demand_kwh', '600', None)
    assert len(resultats) == 13
    assert all(v['conforme'] is None for v in resultats.values())


def test_evaluer_test1_structure_et_verdict_global_conforme(reference):
    """Builds a COMPLETE candidate (heating + cooling, 1E =
    programme mean everywhere): global verdict of Test 1 = conforming."""
    candidat = {}
    for grandeur in ('sensible_heating_demand_kwh', 'sensible_cooling_demand_kwh'):
        noeud_1e = reference['reference_values'][grandeur]['1E']
        candidat_mensuel = {}
        for mois in moteur.MOIS:
            candidat_mensuel[mois] = moteur._valeur_reelle(
                noeud_1e['monthly'][mois]['mean_of_programs'])
        candidat[grandeur] = {
            '1E': {
                'monthly': candidat_mensuel,
                'annual': moteur._valeur_reelle(noeud_1e['annual']['mean_of_programs']),
            }
        }

    # Table 31: third pass/fail criterion for case 1E. Without it, the global
    # verdict remains `None` -- which is the intended behaviour (an unevaluated
    # period is never a success), but prevents testing the conforming case.
    noeud_pointe = reference['reference_values']['annual_hourly_peak_load_kwh']['1E']
    candidat['annual_hourly_peak_load_kwh'] = {
        '1E': {
            'peak': dict(
                (cle, moteur._valeur_reelle(noeud_pointe['peak'][cle]['mean_of_programs']))
                for cle in ('heating', 'cooling')
            )
        }
    }

    resultat = moteur.evaluer_test1(reference, candidat)

    # All quantities/cases from the reference must appear.
    cles_attendues = set()
    for grandeur, cas_tous in reference['reference_values'].items():
        for cas in cas_tous:
            cles_attendues.add(grandeur + '/' + cas)
    assert set(resultat['cas'].keys()) == cles_attendues

    # Non-1E cases remain "informatif", 1E is "critere_pass_fail".
    assert resultat['cas']['sensible_heating_demand_kwh/1E']['type_controle'] == \
        'critere_pass_fail'
    assert resultat['cas']['sensible_heating_demand_kwh/600']['type_controle'] == \
        'informatif'

    assert resultat['verdict_test1']['conforme'] is True
    assert resultat['classes_concernees'] == list(moteur.CLASSES_REQUERANT_TEST1)
    assert '5' not in resultat['classes_concernees']  # tab. 63: class 5 excluded


def test_evaluer_test1_sans_candidat_ne_leve_pas_et_verdict_est_none(reference):
    """Full pipeline callable BEFORE ve-adapter provides anything:
    no exception, global verdict `None` (nothing is yet evaluated)."""
    resultat = moteur.evaluer_test1(reference, None)
    assert resultat['verdict_test1']['conforme'] is None
    # All 1E periods must be non-evaluated, not faulty.
    bloc_1e = resultat['cas']['sensible_heating_demand_kwh/1E']
    assert all(p['conforme'] is None for p in bloc_1e['periodes'].values())


def test_evaluer_test1_un_seul_echec_1e_suffit_a_faire_echouer_le_verdict_global(
        reference):
    """A single out-of-band 1E period must flip the global verdict,
    even if all other 1E periods are conforming."""
    candidat = {}
    for grandeur in ('sensible_heating_demand_kwh', 'sensible_cooling_demand_kwh'):
        noeud_1e = reference['reference_values'][grandeur]['1E']
        candidat_mensuel = {}
        for mois in moteur.MOIS:
            candidat_mensuel[mois] = moteur._valeur_reelle(
                noeud_1e['monthly'][mois]['mean_of_programs'])
        candidat[grandeur] = {
            '1E': {
                'monthly': candidat_mensuel,
                'annual': moteur._valeur_reelle(noeud_1e['annual']['mean_of_programs']),
            }
        }
    # Sabotage one single period (January, heating) well beyond the band.
    plage_max_janvier = moteur._valeur_reelle(
        reference['reference_values']['sensible_heating_demand_kwh']['1E']
        ['monthly']['month_01']['range_max'])
    candidat['sensible_heating_demand_kwh']['1E']['monthly']['month_01'] = \
        plage_max_janvier + 10000.0

    resultat = moteur.evaluer_test1(reference, candidat)
    assert resultat['verdict_test1']['conforme'] is False
    echecs = resultat['verdict_test1']['echecs']
    assert {'grandeur': 'sensible_heating_demand_kwh', 'periode': 'month_01'} in echecs
    assert len(echecs) == 1
