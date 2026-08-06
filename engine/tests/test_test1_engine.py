# -*- coding: utf-8 -*-
"""Tests unitaires du moteur de validation SIA 4010 Test 1 (`engine/test1_engine.py`).

Developpement pilote par la reference (CLAUDE.md) : chaque controle charge une
valeur deja figee et auditee dans `refs/reference-data/test-1.ref.json` et exige
que le moteur la reproduise dans la tolerance, plutot que d'inventer des fixtures
synthetiques pour tout. Des cas synthetiques ne sont utilises que pour les
scenarios hors-bande ou de forme d'entree qu'aucune donnee reelle ne couvre
(candidat manquant, candidat clairement hors Streubereich, formes invalides).

Aucun `import iesve` ; compatible Python 3.4 (pas de f-string), cf.
`docs/ADR-001-architecture-MSP.md` §2 et `engine/tests/test_ref_integrity.py`.
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
# 1. Chargement de la reference figee
# --------------------------------------------------------------------------

def test_charger_reference_par_defaut_expose_les_cinq_grandeurs():
    """Cinq depuis la passe 4 : la Table 31 (charges de pointe horaires du cas
    1E) a ete ajoutee apres l'audit du loader existant, qui la lisait alors que
    la reference l'ignorait (AUDIT-swiss-sia-existant.md, element n 3)."""
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
# 2. `calculer_plage_dispersion` -- reproduit EXACTEMENT la formule auditee,
#    sur TOUTES les periodes reelles (1E, chauffage + refroidissement, 26
#    periodes comme dans AUDIT.md pt 4 / re-audit passe 3).
# --------------------------------------------------------------------------

def _enregistrements_1e(reference, grandeur):
    noeud = reference['reference_values'][grandeur]['1E']
    for mois in moteur.MOIS:
        yield mois, noeud['monthly'][mois]
    yield 'annual', noeud['annual']


def test_plage_dispersion_reproduit_la_reference_sur_toutes_les_periodes(reference):
    """Chaque `range_min`/`range_max` deja calcule par l'Excel officiel doit etre
    reproduit par `calculer_plage_dispersion` a partir des 4 programmes bruts."""
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
    # 12 mois + annuel, pour chauffage et refroidissement = 26 (AUDIT.md pt 4).
    assert verifiees == 26


def test_plage_dispersion_nest_pas_le_min_max_brut():
    """Garde-fou explicite contre l'idee recue corrigee par l'audit (AUDIT.md pt 4) :
    le Streubereich n'est PAS [min(valeurs), max(valeurs)]."""
    valeurs = [10.0, 12.0, 8.0, 50.0]
    moyenne, ecart_max, plage_min, plage_max = moteur.calculer_plage_dispersion(valeurs)
    assert moyenne == 20.0
    assert ecart_max == 30.0  # |50 - 20|
    assert plage_max == 50.0
    assert plage_min == 0.0  # plancher a 0 (moyenne - ecart_max = -10 < 0)
    # Le min/max brut des valeurs (8, 50) est different du Streubereich (0, 50) :
    assert (plage_min, plage_max) != (min(valeurs), max(valeurs))


def test_plage_dispersion_leve_si_aucune_valeur():
    with pytest.raises(ValueError):
        moteur.calculer_plage_dispersion([])


# --------------------------------------------------------------------------
# 3. `evaluer_periode_1e` -- le seul verdict pass/fail du Test 1
# --------------------------------------------------------------------------

def test_1e_candidat_egal_a_la_moyenne_est_conforme(reference):
    """La moyenne des programmes est, par construction, toujours dans sa propre
    plage (AUDIT.md pt 4 : verifie 26/26) : un candidat qui la reproduit doit
    donc passer le critere."""
    enregistrement = reference['reference_values'][
        'sensible_heating_demand_kwh']['1E']['annual']
    moyenne = moteur._valeur_reelle(enregistrement['mean_of_programs'])
    resultat = moteur.evaluer_periode_1e(enregistrement, moyenne)
    assert resultat['conforme'] is True
    assert resultat['coherence_reference'] is True
    assert resultat['marge_min'] >= 0
    assert resultat['marge_max'] >= 0


def test_1e_candidat_egal_a_un_programme_de_reference_est_conforme(reference):
    """Un candidat identique a UN des 4 programmes de reference doit tomber dans
    la plage, puisque cette plage encadre justement l'ecart maximal observe entre
    les programmes et leur moyenne."""
    enregistrement = reference['reference_values'][
        'sensible_cooling_demand_kwh']['1E']['monthly']['month_07']
    valeur_ida = moteur._valeur_reelle(enregistrement['ida_ice_5_0_beta_23'])
    resultat = moteur.evaluer_periode_1e(enregistrement, valeur_ida)
    assert resultat['conforme'] is True


def test_1e_candidat_sur_la_borne_exacte_est_conforme(reference):
    """`range_min <= candidat <= range_max` : la borne elle-meme est incluse
    (AUDIT.md : "range_min <= candidat <= range_max"), pas une inegalite stricte."""
    enregistrement = reference['reference_values'][
        'sensible_heating_demand_kwh']['1E']['annual']
    plage_max = moteur._valeur_reelle(enregistrement['range_max'])
    plage_min = moteur._valeur_reelle(enregistrement['range_min'])
    assert moteur.evaluer_periode_1e(enregistrement, plage_max)['conforme'] is True
    assert moteur.evaluer_periode_1e(enregistrement, plage_min)['conforme'] is True


def test_1e_candidat_nettement_hors_bande_est_rejete(reference):
    """Cas synthetique hors-bande : aucune donnee reelle ne peut couvrir un
    candidat aberrant puisque le candidat IESVE n'a pas encore ete calcule."""
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
        # Le plancher de la plage est 0 (cf. formule) : verifier qu'on rejette
        # bien un candidat negatif hors plage, pas seulement "en dessous de la
        # moyenne".
        resultat_bas = moteur.evaluer_periode_1e(enregistrement, candidat_trop_bas)
        assert resultat_bas['conforme'] is False
        assert resultat_bas['marge_min'] < 0


def test_1e_candidat_absent_ne_produit_aucun_verdict(reference):
    """Un candidat non fourni (VE Script pas encore execute) doit rester
    `conforme=None` avec un motif explicite -- jamais un `False` invente."""
    enregistrement = reference['reference_values'][
        'sensible_heating_demand_kwh']['1E']['annual']
    resultat = moteur.evaluer_periode_1e(enregistrement, None)
    assert resultat['conforme'] is None
    assert 'motif' in resultat
    assert 'marge_min' not in resultat
    assert 'marge_max' not in resultat


def test_1e_leve_si_un_programme_de_reference_manque():
    """Un enregistrement 1E incomplet (programme manquant) doit lever une erreur
    explicite plutot que de calculer une plage fausse en silence."""
    enregistrement_incomplet = {
        'ida_ice_5_0_beta_23': {'value': 100.0, 'unit': 'kWh', 'cell': 'C1'},
        'excel_sia_380_2': {'value': 110.0, 'unit': 'kWh', 'cell': 'D1'},
        'energyplus_openstudio_9_1_0': {'value': 90.0, 'unit': 'kWh', 'cell': 'E1'},
        # tas_edsl_9_5_2 manquant
        'range_max': {'value': 120.0, 'unit': 'kWh', 'cell': 'H1'},
        'range_min': {'value': 80.0, 'unit': 'kWh', 'cell': 'I1'},
    }
    with pytest.raises(ValueError):
        moteur.evaluer_periode_1e(enregistrement_incomplet, 100.0)


def test_1e_coherence_reference_detecte_une_plage_stockee_divergente(reference):
    """Si les colonnes deja calculees par l'Excel divergeaient du recalcul
    independant du moteur, `coherence_reference` doit passer a False (garde-fou
    ADR-001 §4 pt 2). Simule sur une copie modifiee d'un enregistrement reel."""
    import copy
    enregistrement = copy.deepcopy(reference['reference_values'][
        'sensible_heating_demand_kwh']['1E']['annual'])
    enregistrement['range_max']['value'] += 500.0  # divergence volontaire
    resultat = moteur.evaluer_periode_1e(enregistrement, 0.0)
    assert resultat['coherence_reference'] is False


# --------------------------------------------------------------------------
# 4. `comparer_periode_informative` -- AUCUN verdict, pour tous les autres cas
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
    # Les autres programmes, eux, doivent presenter un delta non nul (donnees
    # reelles distinctes -- verifie qu'on ne compare pas tout au meme nombre).
    comparaison_tas = resultat['comparaisons']['tas_edsl_9_5_2']
    assert comparaison_tas['delta_absolu'] != 0.0


def test_informatif_candidat_absent_laisse_les_references_visibles(reference):
    """Meme sans candidat, les valeurs de reference (comparatif informatif)
    restent exposees -- seul le delta devient None."""
    enregistrement = reference['reference_values'][
        'operative_temperature_monthly_celsius']['600']['monthly']['month_01']
    resultat = moteur.comparer_periode_informative(enregistrement, None)
    assert resultat['valeur_candidate'] is None
    for comparaison in resultat['comparaisons'].values():
        assert comparaison['reference'] is not None
        assert comparaison['delta_absolu'] is None


def test_informatif_gere_les_cas_600ff_900ff_temperature(reference):
    """Cas 600FF/900FF (flottement libre) : seule sortie contrôlée = temperature
    operative, toujours sans verdict (spec §6)."""
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
# 5. `_valeur_candidate` -- tolerance de forme explicite, rejet du reste
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
    """Construit un candidat 1E entierement egal a `mean_of_programs` (mois +
    annuel) : le cas doit ressortir integralement conforme."""
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
    assert len(resultats) == 13  # 12 mois + annuel
    assert all(v['conforme'] is True for v in resultats.values())


def test_evaluer_cas_informatif_ne_leve_jamais_meme_sans_candidat(reference):
    resultats = moteur.evaluer_cas(
        reference, 'sensible_heating_demand_kwh', '600', None)
    assert len(resultats) == 13
    assert all(v['conforme'] is None for v in resultats.values())


def test_evaluer_test1_structure_et_verdict_global_conforme(reference):
    """Construit un candidat COMPLET (chauffage + refroidissement, 1E =
    moyenne des programmes partout) : verdict global du Test 1 = conforme."""
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

    # Table 31 : troisieme critere pass/fail du cas 1E. Sans lui, le verdict
    # global reste `None` -- ce qui est le comportement voulu (une periode non
    # evaluee n'est jamais un succes), mais empeche de tester le cas conforme.
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

    # Toutes les grandeurs/cas de la reference doivent apparaitre.
    cles_attendues = set()
    for grandeur, cas_tous in reference['reference_values'].items():
        for cas in cas_tous:
            cles_attendues.add(grandeur + '/' + cas)
    assert set(resultat['cas'].keys()) == cles_attendues

    # Les cas non-1E restent "informatif", 1E est "critere_pass_fail".
    assert resultat['cas']['sensible_heating_demand_kwh/1E']['type_controle'] == \
        'critere_pass_fail'
    assert resultat['cas']['sensible_heating_demand_kwh/600']['type_controle'] == \
        'informatif'

    assert resultat['verdict_test1']['conforme'] is True
    assert resultat['classes_concernees'] == list(moteur.CLASSES_REQUERANT_TEST1)
    assert '5' not in resultat['classes_concernees']  # tab. 63 : classe 5 exclue


def test_evaluer_test1_sans_candidat_ne_leve_pas_et_verdict_est_none(reference):
    """Pipeline complet appelable AVANT que ve-adapter ne fournisse quoi que ce
    soit : aucune exception, verdict global `None` (rien n'est encore evalue)."""
    resultat = moteur.evaluer_test1(reference, None)
    assert resultat['verdict_test1']['conforme'] is None
    # Toutes les periodes 1E doivent etre non-evaluees, pas fautives.
    bloc_1e = resultat['cas']['sensible_heating_demand_kwh/1E']
    assert all(p['conforme'] is None for p in bloc_1e['periodes'].values())


def test_evaluer_test1_un_seul_echec_1e_suffit_a_faire_echouer_le_verdict_global(
        reference):
    """Une seule periode 1E hors bande doit faire basculer le verdict global,
    meme si toutes les autres periodes 1E sont conformes."""
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
    # Sabote une seule periode (janvier, chauffage) tres au-dela de la plage.
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
