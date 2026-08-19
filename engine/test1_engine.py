# -*- coding: utf-8 -*-
"""SIA 4010 validation engine -- Test 1 (ASHRAE 140 / EN ISO 52016-1 ch. 7).

Pure Python: no `import iesve`. Compatible with Python 3.4 (docs/ADR-001-architecture-
MSP.md §2 -- no f-strings, no `dataclasses`, no variable annotations;
only function annotations using native types are used, to stay
typed without depending on the `typing` module, absent in 3.4).

This module makes NO assumption about building physics: it compares the
IESVE candidate against reference values already frozen and audited in
`refs/reference-data/test-1.ref.json` (AUDIT.md, verdict "GARDER -- SIGNE", pass 3,
2026-07-30). It invents no value, no tolerance, no normative article.

Core rule (traceability/test-1.spec.md §6, confirmed word for word in
`Spezifikation_Test1.pdf`, section "Testkriterien"):

* Cases **600, 640, 900, 940, 600FF, 900FF**: "Es gibt dafuer kein
  Abweichungskriterium" -- NO deviation criterion. This engine therefore NEVER
  produces a pass/fail verdict for these cases: only an informative delta per
  reference program (`comparer_periode_informative`).
* Case **1E** (the only case with a criterion): "Resultate fuer den Test 1E muessen im
  Streubereich der enthaltenen Referenzprogramme liegen" -- the candidate must fall
  within the Streubereich of the 4 reference programs. This is the
  ONLY pass/fail verdict of Test 1 (`evaluer_periode_1e`).

Streubereich formula -- established by independent audit, NOT a simple min/max
(AUDIT.md, "What was VERIFIED AND CONFIRMED" pt 4, and re-audit pass 3,
26/26 periods):

    mean       = arithmetic mean of the 4 reference programs
    max_dev    = max( |program_i - mean| )
    upper      = mean + max_dev
    lower      = max(0, mean - max_dev)

In accordance with ADR-001 §4 pt 2 ("le moteur `engine/` recalcule les memes verdicts de
facon independante"), this module RECOMPUTES this band from the 4 program values
rather than trusting the `range_min`/`range_max` columns already computed
by the Excel workbook -- the two must agree (`coherence_reference`), which
provides an additional safeguard, separate from the static audit of
`engine/tests/test_ref_integrity.py`.

⚠ A VERIFIER -- candidate shape: `ve_adapter/` does not yet exist at this stage of the
pipeline (next step). The exact shape of the normalised JSON it will produce is
therefore NOT confirmed. This module adopts an explicit working convention (mirror of
the `reference_values` structure, cf. docstring of `evaluer_test1`) and remains
tolerant of the exact scalar form (`_valeur_candidate`); to be reconfirmed with
`ve-adapter-engineer` before real integration.
"""

import json
import os

from engine import scatter_band

# --------------------------------------------------------------------------
# Location of the frozen reference
# --------------------------------------------------------------------------

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
CHEMIN_REFERENCE_DEFAUT = os.path.join(
    _RACINE, 'refs', 'reference-data', 'test-1.ref.json')


# --------------------------------------------------------------------------
# Normative constants (all sourced -- no invented values)
# --------------------------------------------------------------------------

# Monthly keys as they appear in test-1.ref.json.
MOIS = (
    'month_01', 'month_02', 'month_03', 'month_04', 'month_05', 'month_06',
    'month_07', 'month_08', 'month_09', 'month_10', 'month_11', 'month_12',
)

# The 4 reference programs that define the Streubereich for case 1E.
# Case 1E has no ISO 52016-1 column (AUDIT.md pt 3; traceability/
# test-1.spec.md §6, identified in the Test 1 Anwenderberichte).
PROGRAMMES_REFERENCE_1E = (
    'ida_ice_5_0_beta_23',
    'excel_sia_380_2',
    'energyplus_openstudio_9_1_0',
    'tas_edsl_9_5_2',
)

# The only Test 1 case that carries a pass/fail criterion (traceability/test-1.spec.md §6).
CAS_AVEC_CRITERE = ('1E',)

# Validation classes that require Test 1 (traceability/test-1.spec.md §2,
# SIA 4010:2023 §4.5 tab. 63 -- confirmed: all classes EXCEPT class 5).
CLASSES_REQUERANT_TEST1 = ('1A', '1B', '2A', '2B', '3', '4A', '4B')

TOLERANCE_DEFAUT = 1e-6


# --------------------------------------------------------------------------
# Loading the frozen reference
# --------------------------------------------------------------------------

def charger_reference(chemin=None):
    """Load the frozen and signed reference values for Test 1.

    Source: `refs/reference-data/test-1.ref.json`, extracted from
    `SIA_4010_geteilter_Link/Test1/Resultaterfassung_Test1.xlsx` (sheet
    "Zusammenfassung Testfaelle") and independently audited (AUDIT.md, verdict
    "GARDER -- SIGNE", pass 3, 2026-07-30: 1336/1336 cells concordant, 0
    label<->column mismatch). This engine NEVER recomputes these values
    themselves: it loads them as-is. Extraction fidelity is
    verified separately by `engine/tests/test_ref_integrity.py`.
    """
    if chemin is None:
        chemin = CHEMIN_REFERENCE_DEFAUT
    with open(chemin, encoding='utf-8') as flux:
        return json.load(flux)


# --------------------------------------------------------------------------
# Scalar value extraction
# --------------------------------------------------------------------------

def _valeur_reelle(feuille):
    """Extract `value` from a reference cell `{value, unit, cell, [note]}`.

    A null value always corresponds to an Excel error documented by a
    `note` (AUDIT.md, check "documented null values", 80/80 verified): the
    engine propagates it as `None`, it never invents it as 0.
    """
    if not feuille:
        return None
    valeur = feuille.get('value')
    if isinstance(valeur, bool):
        return None
    return float(valeur) if isinstance(valeur, (int, float)) else None


def _valeur_candidate(valeur):
    """Normalise a candidate value supplied by the VE adapter.

    ⚠ A VERIFIER: the exact shape that `ve-adapter-engineer` will produce is not
    yet frozen (the adapter does not exist at this stage of the pipeline). As a
    precaution, this engine accepts two plausible forms and explicitly rejects
    the rest rather than guessing silently:
      - a raw number (`float`/`int`);
      - a dict `{"value": <number>, ...}`, in the same format as reference cells,
        if the adapter chooses to stay consistent with that format.
    """
    if valeur is None:
        return None
    if isinstance(valeur, bool):
        raise TypeError('Valeur candidate booleenne inattendue : ' + repr(valeur))
    if isinstance(valeur, (int, float)):
        return float(valeur)
    if isinstance(valeur, dict) and 'value' in valeur:
        return _valeur_candidate(valeur['value'])
    raise TypeError('Forme de valeur candidate non supportee : ' + repr(valeur))


# --------------------------------------------------------------------------
# Case 1E -- the only pass/fail criterion of Test 1
#
# traceability/test-1.spec.md §6: "Resultate fuer den Test 1E muessen im
# Streubereich der enthaltenen Referenzprogramme liegen" -- confirmed word for
# word in `Spezifikation_Test1.pdf`, section "Testkriterien".
# --------------------------------------------------------------------------

def calculer_plage_dispersion(valeurs_programmes):
    """Compute the Streubereich (dispersion band) of the reference programs.

    Article: `Spezifikation_Test1.pdf`, section "Testkriterien"
    (traceability/test-1.spec.md §6). Formula established by independent audit --
    NOT a simple min/max (AUDIT.md pt 4, 26/26 periods verified):

        mean      = arithmetic mean of the programs
        max_dev   = max( |program_i - mean| )
        upper     = mean + max_dev
        lower     = max(0, mean - max_dev)

    Returns a tuple `(mean, max_dev, lower, upper)`.

    ⚠ FLOOR AT ZERO: applied here because the Test 1 tables do so
    (`I16 = MAX(0, G16 - ...)`, likewise I82). This is NOT a property of the
    formula: Test 2 writes `O14 = M14 - MAX(...)`, without a floor. This
    function is therefore specific to Test 1 and must not be reused
    as-is for tests 2 to 5 -- call `scatter_band.build_band()`
    with an explicit `floor_at_zero`.

    The computation itself is delegated to `engine.scatter_band`, the single
    source of the formula (itself validated against the 48 bands tabulated by
    the SIA in `engine/tests/test_scatter_band.py`).
    """
    if not valeurs_programmes:
        raise ValueError('Aucune valeur de programme de reference fournie.')
    bande = scatter_band.build_band(valeurs_programmes, floor_at_zero=True)
    return (bande.mean, bande.max_deviation, bande.lower_bound, bande.upper_bound)


def evaluer_periode_1e(enregistrement_reference, valeur_candidate,
                        tolerance=TOLERANCE_DEFAUT):
    """Pass/fail verdict for case 1E for ONE period (a month or the annual) of ONE
    quantity (heating OR cooling).

    Article: `Spezifikation_Test1.pdf`, section "Testkriterien"
    (traceability/test-1.spec.md §6) -- only case 1E carries a criterion. The band
    is recomputed independently of the columns already calculated by Excel
    (ADR-001 §4 pt 2), with a consistency safeguard (`coherence_reference`).

    `enregistrement_reference` is the raw node from `test-1.ref.json` for this
    period (dict of cells `{value, unit, cell}` per program, plus
    `mean_of_programs`/`range_max`/`range_min`).
    """
    valeurs_programmes = []
    for programme in PROGRAMMES_REFERENCE_1E:
        valeur = _valeur_reelle(enregistrement_reference.get(programme))
        if valeur is None:
            raise ValueError(
                'Programme de reference manquant ou non numerique (' + programme +
                ') dans un enregistrement du cas 1E : ' + repr(enregistrement_reference))
        valeurs_programmes.append(valeur)

    moyenne, ecart_max, plage_min, plage_max = calculer_plage_dispersion(
        valeurs_programmes)

    plage_max_stockee = _valeur_reelle(enregistrement_reference.get('range_max'))
    plage_min_stockee = _valeur_reelle(enregistrement_reference.get('range_min'))
    coherence_reference = (
        plage_max_stockee is not None and plage_min_stockee is not None and
        abs(plage_max_stockee - plage_max) <= tolerance and
        abs(plage_min_stockee - plage_min) <= tolerance)

    valeur = _valeur_candidate(valeur_candidate)

    resultat = {
        'valeur_candidate': valeur,
        'moyenne_programmes': moyenne,
        'ecart_max': ecart_max,
        'plage_min': plage_min,
        'plage_max': plage_max,
        'coherence_reference': coherence_reference,
    }

    if valeur is None:
        resultat['conforme'] = None
        resultat['motif'] = 'Candidat non fourni (VE Script pas encore execute).'
        return resultat

    resultat['conforme'] = (plage_min - tolerance) <= valeur <= (plage_max + tolerance)
    resultat['marge_min'] = valeur - plage_min
    resultat['marge_max'] = plage_max - valeur
    return resultat


# --------------------------------------------------------------------------
# Informative cases -- NO verdict (traceability/test-1.spec.md §6)
# --------------------------------------------------------------------------

def comparer_periode_informative(enregistrement_reference, valeur_candidate):
    """Comparison WITHOUT pass/fail verdict (cases 600/640/900/940/600FF/900FF).

    Article: `Spezifikation_Test1.pdf`, section "Testkriterien": "Es gibt
    dafuer kein Abweichungskriterium" -- no deviation criterion for these cases
    (traceability/test-1.spec.md §6, confirmed word for word). This function
    therefore NEVER produces a `conforme` boolean other than `None`: only an
    informative delta of the candidate vs each of the reference programs available
    in the record (which vary by quantity: 5 programs for the
    energy/temperature tables -- ISO 52016-1, IDA ICE, EXCEL SIA 380/2,
    Energy+/OpenStudio, EDSL-Tas).
    """
    valeur = _valeur_candidate(valeur_candidate)
    noms_programmes = [cle for cle in enregistrement_reference
                        if cle != 'testprogramm_candidate']

    comparaisons = {}
    for nom in noms_programmes:
        valeur_reference = _valeur_reelle(enregistrement_reference[nom])
        if valeur is None or valeur_reference is None:
            comparaisons[nom] = {
                'reference': valeur_reference,
                'delta_absolu': None,
                'delta_relatif_pct': None,
            }
            continue
        delta = valeur - valeur_reference
        delta_relatif = (delta / valeur_reference * 100.0) if valeur_reference != 0 else None
        comparaisons[nom] = {
            'reference': valeur_reference,
            'delta_absolu': delta,
            'delta_relatif_pct': delta_relatif,
        }

    return {
        'valeur_candidate': valeur,
        'comparaisons': comparaisons,
        'type_controle': 'informatif',
        'conforme': None,  # explicit: NO criterion for this case (spec §6)
    }


# --------------------------------------------------------------------------
# Period iteration by quantity -- handles the structural differences
# in the reference JSON (AUDIT.md, "Non-blocking remarks" pt 1):
#   - Tables 28/29 (heating/cooling): `annual` at the case root level.
#   - Table 30 (monthly temperature): `annual` nested under `monthly.annual`.
#   - Table 32 (annual extremes, 600FF/900FF only): `extremes` node.
# --------------------------------------------------------------------------

def _perioder_energie(noeud_cas, candidat_cas):
    """Sensible heating/cooling (Tables 28/29): monthly + `annual`
    at the case root level."""
    candidat_cas = candidat_cas or {}
    candidat_mensuel = candidat_cas.get('monthly') or {}
    for mois in MOIS:
        yield mois, noeud_cas['monthly'][mois], candidat_mensuel.get(mois)
    yield 'annual', noeud_cas['annual'], candidat_cas.get('annual')


def _perioder_temperature_mensuelle(noeud_cas, candidat_cas):
    """Monthly mean operative temperature (Table 30): `annual` nested
    under `monthly.annual` -- NOT at the case root level (cf. AUDIT.md)."""
    candidat_cas = candidat_cas or {}
    candidat_mensuel = candidat_cas.get('monthly') or {}
    for mois in MOIS:
        yield mois, noeud_cas['monthly'][mois], candidat_mensuel.get(mois)
    yield 'annual', noeud_cas['monthly']['annual'], candidat_mensuel.get('annual')


def _perioder_extremes(noeud_cas, candidat_cas):
    """Annual operative temperature extremes (Table 32, 600FF/900FF
    only): `extremes.{max,min,average}` node."""
    candidat_cas = candidat_cas or {}
    candidat_extremes = candidat_cas.get('extremes') or {}
    for cle in ('max', 'min', 'average'):
        yield cle, noeud_cas['extremes'][cle], candidat_extremes.get(cle)


def _perioder_pointe(noeud_cas, candidat_cas):
    """Annual hourly peak loads (Table 31, case 1E only).

    Node `peak.{heating,cooling}`. This is the THIRD pass/fail criterion of
    case 1E, in addition to the monthly demands (Table 28/29): Table 31 tabulates
    a triplet Mittelwert / obere Grenze / untere Grenze in G/H/I, header row
    L81. Gap revealed by the audit of the existing loader
    (AUDIT-swiss-sia-existant.md, item 3).
    """
    candidat_cas = candidat_cas or {}
    candidat_pointe = candidat_cas.get('peak') or {}
    for cle in ('heating', 'cooling'):
        yield cle, noeud_cas['peak'][cle], candidat_pointe.get(cle)


_ITERATEURS_PAR_GRANDEUR = {
    'sensible_heating_demand_kwh': _perioder_energie,
    'sensible_cooling_demand_kwh': _perioder_energie,
    'operative_temperature_monthly_celsius': _perioder_temperature_mensuelle,
    'operative_temperature_annual_extremes_celsius': _perioder_extremes,
    'annual_hourly_peak_load_kwh': _perioder_pointe,
}


# --------------------------------------------------------------------------
# Orchestration -- one case, then the full Test 1
# --------------------------------------------------------------------------

def evaluer_cas(reference, grandeur, cas, candidat_cas):
    """Evaluate all periods of a case for a given quantity.

    Normative dispatch (traceability/test-1.spec.md §6):
      - `cas == '1E'` -> pass/fail criterion (Streubereich, `evaluer_periode_1e`).
      - any other case -> informative comparison only, no verdict
        (`comparer_periode_informative`).
    """
    noeud_cas = reference['reference_values'][grandeur][cas]
    iterateur = _ITERATEURS_PAR_GRANDEUR[grandeur]
    resultats = {}
    for label, enregistrement_reference, valeur_candidate in iterateur(
            noeud_cas, candidat_cas):
        if cas in CAS_AVEC_CRITERE:
            resultats[label] = evaluer_periode_1e(
                enregistrement_reference, valeur_candidate)
        else:
            resultats[label] = comparer_periode_informative(
                enregistrement_reference, valeur_candidate)
    return resultats


def _verdict_global_1e(cas_resultats):
    """Overall Test 1 verdict = aggregation of the ONLY existing criterion (case 1E).

    traceability/test-1.spec.md §6: case 1E is the only one carrying a
    pass/fail criterion. All other cases remain purely informative and therefore
    have no impact on this verdict.
    """
    periodes_1e = []
    for bloc in cas_resultats.values():
        if bloc['cas'] not in CAS_AVEC_CRITERE:
            continue
        for label, verdict in bloc['periodes'].items():
            periodes_1e.append((bloc['grandeur'], label, verdict))

    if not periodes_1e:
        return {'conforme': None, 'motif': 'Cas 1E absent de la reference ou du candidat.'}

    echecs = [p for p in periodes_1e if p[2]['conforme'] is False]
    non_evaluees = [p for p in periodes_1e if p[2]['conforme'] is None]

    if echecs:
        conforme = False
    elif non_evaluees:
        conforme = None
    else:
        conforme = True

    return {
        'conforme': conforme,
        'nb_periodes_totales': len(periodes_1e),
        'nb_periodes_non_evaluees': len(non_evaluees),
        'echecs': [{'grandeur': g, 'periode': p} for g, p, _v in echecs],
    }


def evaluer_test1(reference, candidat=None):
    """Main entry point: evaluate the full SIA 4010 Test 1.

    `reference`: dict loaded by `charger_reference()` (or compatible).

    `candidat`: normalised dict produced by the VE adapter, MIRRORING the shape of
    `reference['reference_values']` (same quantities, same cases, same
    monthly/annual/extremes nesting -- cf. `_perioder_energie`,
    `_perioder_temperature_mensuelle`, `_perioder_extremes`), but whose
    terminal leaves are scalars (or `None`) instead of per-program dicts:

        {
          "sensible_heating_demand_kwh": {
            "1E":  {"monthly": {"month_01": 512.3, ...}, "annual": 2700.0},
            "600": {"monthly": {...}, "annual": ...},
            ...
          },
          "sensible_cooling_demand_kwh": {...},
          "operative_temperature_monthly_celsius": {
            "600": {"monthly": {"month_01": 22.1, ..., "annual": 23.4}},
            ...
          },
          "operative_temperature_annual_extremes_celsius": {
            "600FF": {"extremes": {"max": 61.2, "min": -15.0, "average": 25.8}},
            ...
          }
        }

    ⚠ A VERIFIER: this shape is a working convention of this module, NOT a
    contract confirmed by `ve-adapter-engineer` (the adapter does not yet exist).
    If `candidat` is `None` or incomplete, each missing period is evaluated
    with `valeur_candidate=None` (`conforme=None`, explicit reason) rather than
    failing silently.
    """
    candidat = candidat or {}
    resultat = {
        'test_id': reference.get('test_id', 'SIA-4010-Test-1'),
        'cas': {},
    }
    for grandeur, cas_disponibles in reference['reference_values'].items():
        candidat_grandeur = candidat.get(grandeur) or {}
        for cas in cas_disponibles:
            candidat_cas = candidat_grandeur.get(cas)
            cle = grandeur + '/' + cas
            resultat['cas'][cle] = {
                'grandeur': grandeur,
                'cas': cas,
                'type_controle': ('critere_pass_fail' if cas in CAS_AVEC_CRITERE
                                   else 'informatif'),
                'periodes': evaluer_cas(reference, grandeur, cas, candidat_cas),
            }

    resultat['verdict_test1'] = _verdict_global_1e(resultat['cas'])
    resultat['classes_concernees'] = list(CLASSES_REQUERANT_TEST1)
    return resultat
