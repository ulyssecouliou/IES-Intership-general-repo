# -*- coding: utf-8 -*-
"""Moteur de validation SIA 4010 -- Test n 1 (ASHRAE 140 / EN ISO 52016-1 ch. 7).

Python PUR : aucun `import iesve`. Compatible Python 3.4 (docs/ADR-001-architecture-
MSP.md §2 -- pas de f-string, pas de `dataclasses`, pas d'annotation de variable ;
seules des annotations de fonction utilisant des types natifs sont utilisees, pour
rester "type" sans deprendre du module `typing`, absent en 3.4).

Ce module ne fait AUCUNE hypothese sur la physique du batiment : il compare le
candidat IESVE aux valeurs de reference deja figees et auditees dans
`refs/reference-data/test-1.ref.json` (AUDIT.md, verdict "GARDER -- SIGNE", passe 3,
2026-07-30). Il n'invente ni valeur, ni tolerance, ni article de norme.

Regle de fond (traceability/test-1.spec.md §6, confirmee mot pour mot dans
`Spezifikation_Test1.pdf`, rubrique "Testkriterien") :

* Cas **600, 640, 900, 940, 600FF, 900FF** : "Es gibt dafuer kein
  Abweichungskriterium" -- AUCUN critere de deviation. Ce moteur ne produit donc
  JAMAIS de verdict pass/fail pour ces cas : uniquement un delta informatif par
  programme de reference (`comparer_periode_informative`).
* Cas **1E** (unique cas avec critere) : "Resultate fuer den Test 1E muessen im
  Streubereich der enthaltenen Referenzprogramme liegen" -- le candidat doit tomber
  dans la plage de dispersion (Streubereich) des 4 programmes de reference. C'est le
  SEUL verdict pass/fail du Test 1 (`evaluer_periode_1e`).

Formule du Streubereich -- etablie par audit independant, PAS un simple min/max
(AUDIT.md, "Ce qui a ete VERIFIE ET CONFIRME" pt 4, ainsi que le re-audit passe 3,
26/26 periodes) :

    moyenne    = moyenne arithmetique des 4 programmes de reference
    ecart_max  = max( |programme_i - moyenne| )
    plage_max  = moyenne + ecart_max
    plage_min  = max(0, moyenne - ecart_max)

Conformement a ADR-001 §4 pt 2 ("le moteur `engine/` recalcule les memes verdicts de
facon independante"), ce module RECALCULE cette plage a partir des 4 valeurs de
programme plutot que de se fier aux colonnes `range_min`/`range_max` deja calculees
par le classeur Excel -- les deux doivent concorder (`coherence_reference`), ce qui
constitue un garde-fou supplementaire, distinct de l'audit statique de
`engine/tests/test_ref_integrity.py`.

⚠ A VERIFIER -- forme du candidat : `ve_adapter/` n'existe pas encore a ce stade du
pipeline (etape suivante). La forme exacte du JSON normalise qu'il produira n'est
donc PAS confirmee. Ce module adopte une convention de travail explicite (miroir de
la structure de `reference_values`, cf. docstring de `evaluer_test1`) et reste
tolerant sur la forme scalaire exacte (`_valeur_candidate`) ; a reconfirmer avec
`ve-adapter-engineer` avant integration reelle.
"""

import json
import os

from engine import scatter_band

# --------------------------------------------------------------------------
# Localisation de la reference figee
# --------------------------------------------------------------------------

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
CHEMIN_REFERENCE_DEFAUT = os.path.join(
    _RACINE, 'refs', 'reference-data', 'test-1.ref.json')


# --------------------------------------------------------------------------
# Constantes normatives (toutes sourcees -- aucune valeur inventee)
# --------------------------------------------------------------------------

# Cles mensuelles telles qu'elles apparaissent dans test-1.ref.json.
MOIS = (
    'month_01', 'month_02', 'month_03', 'month_04', 'month_05', 'month_06',
    'month_07', 'month_08', 'month_09', 'month_10', 'month_11', 'month_12',
)

# Les 4 programmes de reference qui fondent le Streubereich du cas 1E.
# Le cas 1E n'a pas de colonne ISO 52016-1 (AUDIT.md pt 3 ; traceability/
# test-1.spec.md §6, identifies par les Anwenderberichte Test 1).
PROGRAMMES_REFERENCE_1E = (
    'ida_ice_5_0_beta_23',
    'excel_sia_380_2',
    'energyplus_openstudio_9_1_0',
    'tas_edsl_9_5_2',
)

# Seul cas du Test 1 porte un critere pass/fail (traceability/test-1.spec.md §6).
CAS_AVEC_CRITERE = ('1E',)

# Classes de validation qui requierent le Test 1 (traceability/test-1.spec.md §2,
# SIA 4010:2023 §4.5 tab. 63 -- confirme : toutes les classes SAUF la classe 5).
CLASSES_REQUERANT_TEST1 = ('1A', '1B', '2A', '2B', '3', '4A', '4B')

TOLERANCE_DEFAUT = 1e-6


# --------------------------------------------------------------------------
# Chargement de la reference figee
# --------------------------------------------------------------------------

def charger_reference(chemin=None):
    """Charge les valeurs de reference figees et signees du Test 1.

    Source : `refs/reference-data/test-1.ref.json`, extrait de
    `SIA_4010_geteilter_Link/Test1/Resultaterfassung_Test1.xlsx` (feuille
    "Zusammenfassung Testfaelle") et audite independamment (AUDIT.md, verdict
    "GARDER -- SIGNE", passe 3, 2026-07-30 : 1336/1336 cellules concordantes, 0
    incoherence libelle<->colonne). Ce moteur ne recalcule JAMAIS ces valeurs
    elles-memes : il les charge telles quelles. La fidelite de l'extraction est
    controlee separement par `engine/tests/test_ref_integrity.py`.
    """
    if chemin is None:
        chemin = CHEMIN_REFERENCE_DEFAUT
    with open(chemin, encoding='utf-8') as flux:
        return json.load(flux)


# --------------------------------------------------------------------------
# Extraction de valeurs scalaires
# --------------------------------------------------------------------------

def _valeur_reelle(feuille):
    """Extrait `value` d'une feuille de reference `{value, unit, cell, [note]}`.

    Une valeur nulle correspond toujours a une erreur Excel documentee par une
    `note` (AUDIT.md, controle "valeurs nulles documentees", 80/80 verifiees) : le
    moteur la propage en `None`, il ne l'invente jamais a 0.
    """
    if not feuille:
        return None
    valeur = feuille.get('value')
    if isinstance(valeur, bool):
        return None
    return float(valeur) if isinstance(valeur, (int, float)) else None


def _valeur_candidate(valeur):
    """Normalise une valeur candidate fournie par l'adaptateur VE.

    ⚠ A VERIFIER : la forme exacte que produira `ve-adapter-engineer` n'est pas
    encore figee (l'adaptateur n'existe pas a ce stade du pipeline). Par prudence,
    ce moteur accepte deux formes plausibles et rejette explicitement le reste
    plutot que de deviner en silence :
      - un nombre brut (`float`/`int`) ;
      - un dict `{"value": <nombre>, ...}`, au meme format que les feuilles de
        reference, si l'adaptateur choisit de rester coherent avec ce format.
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
# Cas 1E -- le seul critere pass/fail du Test 1
#
# traceability/test-1.spec.md §6 : "Resultate fuer den Test 1E muessen im
# Streubereich der enthaltenen Referenzprogramme liegen" -- confirme mot pour mot
# dans `Spezifikation_Test1.pdf`, rubrique "Testkriterien".
# --------------------------------------------------------------------------

def calculer_plage_dispersion(valeurs_programmes):
    """Calcule le Streubereich (plage de dispersion) des programmes de reference.

    Article : `Spezifikation_Test1.pdf`, rubrique "Testkriterien"
    (traceability/test-1.spec.md §6). Formule etablie par audit independant --
    PAS un simple min/max (AUDIT.md pt 4, 26/26 periodes verifiees) :

        moyenne   = moyenne arithmetique des programmes
        ecart_max = max( |programme_i - moyenne| )
        plage_max = moyenne + ecart_max
        plage_min = max(0, moyenne - ecart_max)

    Retourne un tuple `(moyenne, ecart_max, plage_min, plage_max)`.

    ⚠ PLANCHER A ZERO : applique ici parce que les tables du Test 1 le font
    (`I16 = MAX(0, G16 - ...)`, idem I82). Ce n'est PAS une propriete de la
    formule : le Test 2 ecrit `O14 = M14 - MAX(...)`, sans plancher. Cette
    fonction est donc specifique au Test 1 et ne doit pas etre reutilisee
    telle quelle pour les tests 2 a 5 -- appeler `scatter_band.build_band()`
    avec `floor_at_zero` explicite.

    Le calcul lui-meme est delegue a `engine.scatter_band`, source unique de la
    formule (elle-meme prouvee contre les 48 bandes tabulees par le SIA dans
    `engine/tests/test_scatter_band.py`).
    """
    if not valeurs_programmes:
        raise ValueError('Aucune valeur de programme de reference fournie.')
    bande = scatter_band.build_band(valeurs_programmes, floor_at_zero=True)
    return (bande.mean, bande.max_deviation, bande.lower_bound, bande.upper_bound)


def evaluer_periode_1e(enregistrement_reference, valeur_candidate,
                        tolerance=TOLERANCE_DEFAUT):
    """Verdict pass/fail du cas 1E pour UNE periode (un mois ou l'annuel) d'UNE
    grandeur (chauffage OU refroidissement).

    Article : `Spezifikation_Test1.pdf`, rubrique "Testkriterien"
    (traceability/test-1.spec.md §6) -- seul le cas 1E porte un critere. La plage
    est recalculee independamment des colonnes deja calculees par l'Excel
    (ADR-001 §4 pt 2), avec un garde-fou de coherence (`coherence_reference`).

    `enregistrement_reference` est le noeud brut de `test-1.ref.json` pour cette
    periode (dict de feuilles `{value, unit, cell}` par programme, plus
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
# Cas informatifs -- AUCUN verdict (traceability/test-1.spec.md §6)
# --------------------------------------------------------------------------

def comparer_periode_informative(enregistrement_reference, valeur_candidate):
    """Comparaison SANS verdict pass/fail (cas 600/640/900/940/600FF/900FF).

    Article : `Spezifikation_Test1.pdf`, rubrique "Testkriterien" : "Es gibt
    dafuer kein Abweichungskriterium" -- pas de critere de deviation pour ces cas
    (traceability/test-1.spec.md §6, confirme mot pour mot). Cette fonction ne
    produit donc JAMAIS de booleen `conforme` autre que `None` : uniquement un
    delta informatif candidat vs chacun des programmes de reference disponibles
    dans l'enregistrement (qui varient selon la grandeur : 5 programmes pour les
    tables energie/temperature -- ISO 52016-1, IDA ICE, EXCEL SIA 380/2,
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
        'conforme': None,  # explicite : AUCUN critere pour ce cas (spec §6)
    }


# --------------------------------------------------------------------------
# Parcours des periodes par grandeur -- gere les differences structurelles
# du JSON de reference (AUDIT.md, "Remarques NON bloquantes" pt 1) :
#   - Tables 28/29 (chauffage/refroidissement) : `annual` au niveau racine du cas.
#   - Table 30 (temperature mensuelle) : `annual` imbrique sous `monthly.annual`.
#   - Table 32 (extremes annuels, 600FF/900FF seulement) : noeud `extremes`.
# --------------------------------------------------------------------------

def _perioder_energie(noeud_cas, candidat_cas):
    """Chauffage/refroidissement sensible (Tables 28/29) : mensuel + `annual`
    au niveau racine du cas."""
    candidat_cas = candidat_cas or {}
    candidat_mensuel = candidat_cas.get('monthly') or {}
    for mois in MOIS:
        yield mois, noeud_cas['monthly'][mois], candidat_mensuel.get(mois)
    yield 'annual', noeud_cas['annual'], candidat_cas.get('annual')


def _perioder_temperature_mensuelle(noeud_cas, candidat_cas):
    """Temperature operative moyenne mensuelle (Table 30) : `annual` imbrique
    sous `monthly.annual` -- PAS au niveau racine du cas (cf. AUDIT.md)."""
    candidat_cas = candidat_cas or {}
    candidat_mensuel = candidat_cas.get('monthly') or {}
    for mois in MOIS:
        yield mois, noeud_cas['monthly'][mois], candidat_mensuel.get(mois)
    yield 'annual', noeud_cas['monthly']['annual'], candidat_mensuel.get('annual')


def _perioder_extremes(noeud_cas, candidat_cas):
    """Extremes annuels de temperature operative (Table 32, 600FF/900FF
    uniquement) : noeud `extremes.{max,min,average}`."""
    candidat_cas = candidat_cas or {}
    candidat_extremes = candidat_cas.get('extremes') or {}
    for cle in ('max', 'min', 'average'):
        yield cle, noeud_cas['extremes'][cle], candidat_extremes.get(cle)


def _perioder_pointe(noeud_cas, candidat_cas):
    """Charges de pointe horaires annuelles (Table 31, cas 1E uniquement).

    Noeud `peak.{heating,cooling}`. C'est le TROISIEME critere pass/fail du cas
    1E, en plus des besoins mensuels (Table 28/29) : la Table 31 tabule bien un
    triplet Mittelwert / obere Grenze / untere Grenze en G/H/I, ligne d'en-tete
    L81. Lacune revelee par l'audit du loader existant
    (AUDIT-swiss-sia-existant.md, element n 3).
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
# Orchestration -- un cas, puis le Test 1 complet
# --------------------------------------------------------------------------

def evaluer_cas(reference, grandeur, cas, candidat_cas):
    """Evalue toutes les periodes d'un cas pour une grandeur donnee.

    Dispatch normatif (traceability/test-1.spec.md §6) :
      - `cas == '1E'` -> critere pass/fail (Streubereich, `evaluer_periode_1e`).
      - tout autre cas -> comparaison informative uniquement, sans verdict
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
    """Verdict global du Test 1 = agregation du SEUL critere existant (cas 1E).

    traceability/test-1.spec.md §6 : le cas 1E est le seul a porter un critere
    pass/fail. Les autres cas restent purement informatifs et n'ont donc aucune
    incidence sur ce verdict.
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
    """Point d'entree principal : evalue l'ensemble du Test SIA 4010 n 1.

    `reference` : dict charge par `charger_reference()` (ou compatible).

    `candidat` : dict normalise produit par l'adaptateur VE, de forme MIROIR de
    `reference['reference_values']` (meme grandeurs, memes cas, meme
    imbrication mensuel/annuel/extremes -- cf. `_perioder_energie`,
    `_perioder_temperature_mensuelle`, `_perioder_extremes`), mais dont les
    feuilles terminales sont des scalaires (ou `None`) au lieu de dicts par
    programme :

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

    ⚠ A VERIFIER : cette forme est une convention de travail de ce module, PAS un
    contrat confirme par `ve-adapter-engineer` (l'adaptateur n'existe pas encore).
    Si `candidat` est `None` ou incomplet, chaque periode manquante est evaluee
    avec `valeur_candidate=None` (`conforme=None`, motif explicite) plutot que
    d'echouer silencieusement.
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
