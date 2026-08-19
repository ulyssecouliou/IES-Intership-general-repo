# -*- coding: utf-8 -*-
u"""IESVE adapter for SIA 4010 band tests -- tests 2 to 6.

A single module for five tests: their references share the form
"quantity -> case" (cf. `engine/sia_bandes_engine.py`), and their extraction
shares the same mechanics -- open the `.aps`, read a series, aggregate it,
assemble the candidate.

WHAT IS VERIFIED, AND HOW. The `iesve` symbols used here are
present in `ve_adapter/ve_api_surface.json`, an introspection of a
real VE 2025 installation (309 symbols, Python 3.12.3). `verifier_api()`
checks this at runtime and fails loudly if a symbol has disappeared --
which has already happened: `element_categories` had been sought on
`VECdbProject` whereas it belongs to the MODULE `iesve`, and the Test 1
probe revealed it.

WHAT CANNOT BE VERIFIED HERE, AND IS THEREFORE NOT GUESSED. The
**`aps_varname`** -- result variable names -- are not API symbols: they are
runtime data, specific to the simulated model.
None can be established from the development workstation. The bindings in
`LIAISONS` are therefore declared **unresolved**, and the adapter REFUSES to
produce a value for an unresolved binding rather than inventing one.

    Procedure, in VE:
        1. `decouvrir_variables(results_file)` lists what the `.aps` contains.
        2. Identify the exact name corresponding to each SIA quantity.
        3. Declare it in `LIAISONS`, with its source.
        4. `extraire_candidat()` then becomes usable.

Pure Python at load time: `iesve` is only imported on call, so that
this module remains importable in continuous integration, without a VE licence.
"""

from __future__ import print_function

import io
import json
import os

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))

#: Introspection of a real VE 2025 installation. Acts as a guard: we write
#: against what exists, not against the documentation.
CHEMIN_SURFACE_API = os.path.join(_ICI, 've_api_surface.json')

#: `ResultsReader` methods used by this adapter. All present
#: in the recorded surface; `verifier_api()` confirms this at runtime.
METHODES_REQUISES = (
    'close',
    'get_all_room_results',
    'get_all_weather_results',
    'get_room_results',
    'get_results',
    'get_variables',
)

TESTS_COUVERTS = (2, 3, 4, 5, 6)

#: Result levels from the API, as named by `get_variables`.
NIVEAU_LOCAL = 'z'      # room / zone
NIVEAU_SYSTEME = 'v'    # apache system
NIVEAU_METEO = 'w'      # weather
NIVEAU_ENERGIE = 'e'    # consumption items, all energy vectors
NIVEAU_SURFACE = 's'    # envelope surface

#: Levels recorded on 2026-08-06 from `ZOER_C1.aps`, with their RAW count --
#: as `get_variables()` returned them, duplicates included. The frozen catalogue
#: `refs/reference-data/iesve-aps-variables-ve2025.json` removes 11 exact
#: duplicates and therefore counts slightly less (c=178, e=269): both figures are
#: correct, they just count different things.
#:
#: There are TWELVE levels, not three: `c` (carbon), `j`, `l`, `n`, `o`, `r` and
#: `t` also exist. No code must assume that the constants above
#: exhaust the list -- it was by believing it limited to z/v/w that lighting
#: (level `e`) and incident solar (level `s`) were missed.
NIVEAUX_RELEVES = {
    'c': 184, 'e': 274, 'j': 15, 'l': 88, 'n': 9, 'o': 6,
    'r': 15, 's': 22, 't': 6, 'v': 35, 'w': 14, 'z': 151,
}


class LiaisonNonResolue(RuntimeError):
    u"""Raised when a quantity has no established variable name.

    Intentionally an error: returning `None` silently would suggest
    the quantity was looked up and not found, whereas it was never
    looked up.
    """


class ApiIncompatible(RuntimeError):
    u"""Raised when the `iesve` API does not present the expected symbols."""


# ---------------------------------------------------------------------------
# Quantity -> result variable bindings
# ---------------------------------------------------------------------------
#
# `None` means UNRESOLVED, not "absent". Each entry carries the EXACT label
# from the SIA workbook, which serves as the matching key against the frozen
# reference: it is in German and must remain so, otherwise matching breaks.
#
# The `piste` field says where to look in the `.aps`. It is a search hint,
# NOT a value: it must never be used as a variable name.
# Generated from frozen references by a script, NEVER retyped by
# hand: German labels are the matching keys, and a single extra space
# is enough to make a binding unfindable once resolved.
LIAISONS = {
    2: {
        u'Jahresenergie solarer Wärmeeintrag': {
            'aps_varname': None, 'niveau': NIVEAU_LOCAL,
            'agregation': 'somme_annuelle',
            'piste': u'apport solaire et rayonnement transmis, au niveau du local',
        },
        u'Jahresenergie total transmittierte Solarstrahlung': {
            'aps_varname': None, 'niveau': NIVEAU_LOCAL,
            'agregation': 'somme_annuelle',
            'piste': u'apport solaire et rayonnement transmis, au niveau du local',
        },
    },
    3: {
        u'Beleuchtungsenergie': {
            'aps_varname': None, 'niveau': NIVEAU_LOCAL,
            'agregation': 'somme_annuelle',
            'piste': u"puissance d'eclairage du local",
        },
    },
    4: {
        u'Energiebedarf Ventilatoren': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'centrale de traitement d air du Hoersaal',
        },
        u'Wärmeabfuhr Luftkühler total': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'centrale de traitement d air du Hoersaal',
        },
        u'Wärmezufuhr Lufterwärmer': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'centrale de traitement d air du Hoersaal',
        },
    },
    5: {
        u'Befeuchtungsenergie': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation du batiment exemple',
        },
        u'Energiebedarf Ventilatoren': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation du batiment exemple',
        },
        u'Hilfsenergie WRG': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation du batiment exemple',
        },
        u'Wärmeabfuhr Luftkühler latent': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation du batiment exemple',
        },
        u'Wärmeabfuhr Luftkühler total': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation du batiment exemple',
        },
        u'Wärmezufuhr Lufterwärmer': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation du batiment exemple',
        },
        u'Wärmezufuhr WRG': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation du batiment exemple',
        },
        u'Wärmezufuhr WRG latent': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation du batiment exemple',
        },
    },
    6: {
        u'Energiebedarf Ventilatoren': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation, restaurant et cuisine',
        },
        u'Hilfsenergie WRG': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation, restaurant et cuisine',
        },
        u'Wärmeabfuhr Luftkühler total': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation, restaurant et cuisine',
        },
        u'Wärmeabfuhr WRG': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation, restaurant et cuisine',
        },
        u'Wärmezufuhr Lufterwärmer': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation, restaurant et cuisine',
        },
        u'Wärmezufuhr WRG': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation, restaurant et cuisine',
        },
    },
}


# ---------------------------------------------------------------------------
# Candidates from a prior APS probe -- TO CONFIRM, never used
# ---------------------------------------------------------------------------
#
# `config/sia4010_aps_bindings_ve_runtime.json` carries five bindings recorded
# on 2026-07-28 from a real `.aps` file (project "test", 8760 hourly steps).
# They are NOT included in `LIAISONS`: these are VE variable names recorded
# for Test 1, and nothing establishes that they carry the quantity the SIA
# workbook designates. Conflating the two is exactly how a plausible but wrong
# number gets produced.
#
# Two levels of evidence, which must not be mixed:
#
#   * `room_air_temperature` and `operative_temperature` are supported by
#     `references/iesve/probes/sia4010_aps_temperature_binding_evidence.json`,
#     which contains the full series. Their authenticity is cross-checked: min
#     19.999998 °C / max 27.000002 °C on case 600, exactly the
#     ASHRAE 140 setpoints of 20/27. Neither is used for tests 2 to 6.
#   * the three others are backed only by a
#     `RUNTIME_METADATA_CONFIRMED` metadata. **The original probe report
#     (`sia4010_aps_probe_20260728_154627.json`, sha256 F3E1338C…) is ABSENT
#     from the repository**: the trace cannot be replayed. Status: allegation.
#
# SINCE THE 2026-08-06 RECORDING on `ZOER_C1.aps` (819 variables, cf.
# `outputs/sonde_aps.json`), most of the hints below are backed by a variable
# ACTUALLY PRESENT in a `.aps` -- name, level, display label and unit family
# verified against the recording by a test.
#
# What remains to be established is therefore no longer "does this name exist"
# but "does it designate the quantity the SIA workbook designates". This second
# question cannot be settled in VE: it requires the SIA definition. That is
# why nothing is bound.
#
#   RELEVE     -- the variable exists, cross-checked against the probe report.
#   ALLEGATION -- announced by a configuration file whose original trace
#                 is absent from the repository.
#
# Table indexed by QUANTITY, not by test: "Wärmezufuhr Lufterwärmer"
# appears in tests 4, 5 and 6 and designates the same thing there. Indexing by
# test would force repeating the hint three times, hence letting them diverge.
CANDIDATS_PAR_GRANDEUR = {
    u'Jahresenergie solarer Wärmeeintrag': {
        'aps_varname_candidat': u'Window solar gains',
        'display_name': u'Solar gain',
        'niveau': NIVEAU_LOCAL,
        'units_type': u'Gain',
        'preuve': u'outputs/sonde_aps.json, variables[model_level=z] ; '
                  u'corrobore config/sia4010_aps_bindings_ve_runtime.json '
                  u'-> bindings.total_room_solar_heat_gain_power',
        'niveau_de_preuve': u'RELEVE',
        'a_confirmer': u'Que « solarer Wärmeeintrag » au sens du classeur SIA '
                       u'désigne le gain solaire transmis par les vitrages au '
                       u'local, et non le rayonnement incident. Le Test 2 '
                       u'distingue les deux : sa seconde grandeur est '
                       u'« total transmittierte Solarstrahlung ».',
    },
    u'Beleuchtungsenergie': {
        'aps_varname_candidat': u'Total lights energy',
        'display_name': u'Total lights energy',
        'niveau': NIVEAU_ENERGIE,
        'units_type': u'Power',
        'preuve': u'outputs/sonde_aps.json, variables[model_level=e]',
        'niveau_de_preuve': u'RELEVE',
        'a_confirmer': u'Que le classeur compte l\'énergie FINALE de '
                       u'l\'éclairage, tous vecteurs confondus. VE expose '
                       u'aussi « Lights electricity » (électricité seule) et, '
                       u'au niveau du local, « Lighting gain » — qui est un '
                       u'APPORT thermique, pas une consommation.',
    },
    u'Wärmezufuhr Lufterwärmer': {
        'aps_varname_candidat': u'Sys Mech vent heating load',
        'display_name': u'System air heating load',
        'niveau': NIVEAU_SYSTEME,
        'units_type': u'Sys Load',
        'preuve': u'outputs/sonde_aps.json, variables[model_level=v]',
        'niveau_de_preuve': u'RELEVE',
        'a_confirmer': u'Que la batterie chaude du classeur corresponde au '
                       u'poste ApacheSystems « System air », et non à un '
                       u'composant d\'un réseau ApacheHVAC.',
    },
    u'Wärmeabfuhr Luftkühler latent': {
        'aps_varname_candidat': u'Sys Mech vent dehum load',
        'display_name': u'System air lat. clg. load',
        'niveau': NIVEAU_SYSTEME,
        'units_type': u'Sys Load',
        'preuve': u'outputs/sonde_aps.json, variables[model_level=v]',
        'niveau_de_preuve': u'RELEVE',
        'a_confirmer': u'Que la charge de déshumidification de VE et la part '
                       u'latente du classeur recouvrent la même grandeur.',
    },
    u'Wärmeabfuhr Luftkühler total': {
        'aps_varname_candidat': None,
        'display_name': None,
        'niveau': NIVEAU_SYSTEME,
        'units_type': u'Sys Load',
        'preuve': u'outputs/sonde_aps.json, variables[model_level=v]',
        'niveau_de_preuve': u'RELEVE — mais AUCUNE variable unique',
        'a_confirmer': u'« total » suppose sensible + latent. VE les sépare en '
                       u'« Sys Mech vent cooling load » (sensible) et '
                       u'« Sys Mech vent dehum load » (latent). Une liaison ne '
                       u'peut donc pas être un simple nom de variable : il '
                       u'faut une SOMME, que LIAISONS ne sait pas exprimer '
                       u'aujourd\'hui.',
    },
    u'Befeuchtungsenergie': {
        'aps_varname_candidat': u'Sys Room humidification load',
        'display_name': u'Room hum. plant load',
        'niveau': NIVEAU_SYSTEME,
        'units_type': u'Sys Load',
        'preuve': u'outputs/sonde_aps.json, variables[model_level=v]',
        'niveau_de_preuve': u'RELEVE',
        'a_confirmer': u'VE porte cette charge au LOCAL (« Room hum. plant '
                       u'load »), pas à la centrale. Si le classeur vise '
                       u'l\'humidification de l\'air neuf, ce n\'est pas la '
                       u'même grandeur. « Ideal humidification » existe au '
                       u'niveau énergie, mais VE le marque [obs].',
    },
}

#: Quantities for which the 2026-08-06 recording showed NO hint.
#: Recording them is better than letting it seem they were never looked for:
#: silence reads as "not yet checked", which would be false.
SANS_CANDIDAT = {
    u'Jahresenergie total transmittierte Solarstrahlung':
        u'Au niveau surface, VE expose « Total short wave transmittance » (un '
        u'COEFFICIENT, sans unité) et « Ext/Int surface incident solar flux » '
        u'(un rayonnement INCIDENT, pas transmis). Aucune série d\'énergie '
        u'transmise. Constat identique à celui de '
        u'config/sia4010_aps_bindings_ve_runtime.json -> explicitly_unbound, '
        u'atteint ici indépendamment.',
    u'Energiebedarf Ventilatoren':
        u'Aucune variable de ventilateurs SEULS. « ApSys aux energy » agrège '
        u'fans + pumps + ctrls (libellé VE : « Ap Sys fans/pumps/ctrls '
        u'energy ») ; « Fans energy » relève d\'ApacheHVAC et VE le marque '
        u'[obs]. Les postes get_energy_uses() prm_fans_interior_central et '
        u'prm_fans_interior_local sont une piste, mais ce sont des POSTES, pas '
        u'des variables de série.',
    u'Wärmezufuhr WRG':
        u'ApacheSystems n\'expose de la récupération sur l\'air neuf qu\'une '
        u'TEMPÉRATURE (« Sys Mech vent heat recovery temp »). Les deux '
        u'variables de récupération en Power du même niveau — « Sys Process '
        u'heat recovered » et « Sys Process heat recovery heat pump » — '
        u'portent sur les PROCESS, pas sur la ventilation.',
    u'Wärmeabfuhr WRG': u'Même motif que « Wärmezufuhr WRG ».',
    u'Wärmezufuhr WRG latent': u'Même motif que « Wärmezufuhr WRG ».',
    u'Hilfsenergie WRG':
        u'« HR & spray pumps energy » (niveau énergie) est la seule piste, '
        u'mais elle agrège la récupération et les humidificateurs à '
        u'pulvérisation.',
}


def candidats_a_confirmer(numero_test):
    u"""Hints recorded from a real `.aps`, to confirm against the standard.

    These are NOT bindings. `extraire_candidat` ignores them entirely.
    They exist only so that an operator in front of an open VE knows what to
    check first, instead of browsing 819 variables.

    Args:
        numero_test: SIA test number.

    Returns:
        dict: `{German label: hint}` for the quantities of this test,
            empty if none.
    """
    return _projeter(CANDIDATS_PAR_GRANDEUR, numero_test)


def sans_candidat(numero_test):
    u"""Quantities of this test for which the recording showed no hint.

    Args:
        numero_test: SIA test number.

    Returns:
        dict: `{German label: reason}`, empty if none.
    """
    return _projeter(SANS_CANDIDAT, numero_test)


def _projeter(table_par_grandeur, numero_test):
    u"""Restrict a table indexed by quantity to the quantities of a test.

    Args:
        table_par_grandeur: `{label: value}`.
        numero_test: SIA test number.

    Returns:
        dict: Subset corresponding to the declared quantities of the test.
    """
    grandeurs = LIAISONS.get(numero_test, {})
    return dict((libelle, valeur)
                for libelle, valeur in table_par_grandeur.items()
                if libelle in grandeurs)


def verifier_api(symboles=None):
    u"""Check that the `iesve` API presents the symbols used here.

    Args:
        symboles: API surface already loaded; otherwise read from disk.

    Returns:
        dict: `{method: True}` for each required and present method.

    Raises:
        ApiIncompatible: If the surface is unreadable or a method is missing.
            Better to fail at load time than mid-extraction, on an open model.
    """
    if symboles is None:
        if not os.path.isfile(CHEMIN_SURFACE_API):
            raise ApiIncompatible(
                u'surface d\'API introuvable : %s. La régénérer avec '
                u've_adapter/Run_VE_Probe_API_Surface.py depuis VE.'
                % CHEMIN_SURFACE_API)
        with io.open(CHEMIN_SURFACE_API, encoding='utf-8') as flux:
            symboles = json.load(flux).get('symbols', {})

    lecteur = symboles.get('ResultsReader') or {}
    membres = set(lecteur.get('members') or ())
    manquantes = [m for m in METHODES_REQUISES if m not in membres]
    if manquantes:
        raise ApiIncompatible(
            u'ResultsReader ne présente pas : %s. L\'API a changé depuis la '
            u'surface relevée ; relancer la sonde avant d\'aller plus loin.'
            % u', '.join(manquantes))
    return dict((m, True) for m in METHODES_REQUISES)


#: Fields of a `get_variables()` entry where to search for a pattern. `name`
#: does not exist: that was an assumption, corrected on 2026-08-06.
CHAMPS_NOMMANTS = ('aps_varname', 'display_name')


def decouvrir_variables(results_file, niveau=None, motif=None):
    u"""List the variables available in a `.aps`, to establish bindings.

    This is the tool that replaces guesswork: read what the file actually
    contains, then populate `LIAISONS`.

    CORRECTED on 2026-08-06, against a real VE (`ZOER_C1.aps`). This
    function was calling `get_variables(niveau)`; VE responds `ArgumentError`.
    **`get_variables()` takes no argument** and returns ALL variables,
    each carrying its level in `model_level`. Filtering is therefore done
    here, not by the API.

    Args:
        results_file: Already-open `ResultsReader` object.
        niveau: Level to retain (`'z'` room, `'v'` system, `'w'` weather).
            `None` returns all.
        motif: Filtering substring on the name, case-insensitive.

    Returns:
        list[dict]: Variables, as described by the API.
    """
    variables = list(results_file.get_variables() or [])
    if niveau is not None:
        variables = [v for v in variables if _niveau_de(v) == niveau]
    if not motif:
        return variables
    cible = motif.lower()
    return [v for v in variables if cible in _nom_de(v).lower()]


def _niveau_de(variable):
    u"""Model level carried by a `get_variables()` entry.

    Args:
        variable: API entry.

    Returns:
        str | None: Value of `model_level`, or `None` if absent.
    """
    if not isinstance(variable, dict):
        return None
    return variable.get('model_level')


def _nom_de(variable):
    u"""Text to search for a pattern, for a `get_variables()` entry.

    Args:
        variable: API entry.

    Returns:
        str: APS name and display label concatenated.
    """
    if not isinstance(variable, dict):
        return u'%s' % (variable,)
    return u' '.join(u'%s' % variable.get(champ, u'')
                     for champ in CHAMPS_NOMMANTS)


def agreger(serie, methode):
    u"""Aggregate an hourly series according to the requested method.

    Args:
        serie: Hourly values.
        methode: `'somme_annuelle'`, `'moyenne'`, `'maximum'` or `'minimum'`.

    Returns:
        float | None: Aggregated value, `None` if the series is empty.

    Raises:
        ValueError: If the method is unknown -- never a silent fallback
            to sum, which would give a plausible but wrong number.
    """
    valeurs = [float(v) for v in (serie or []) if v is not None]
    if not valeurs:
        return None
    if methode == 'somme_annuelle':
        # VE powers are in W at the hourly step: the sum of W over
        # 8760 h equals Wh, which SIA expects in kWh.
        return sum(valeurs) / 1000.0
    if methode == 'moyenne':
        return sum(valeurs) / len(valeurs)
    if methode == 'maximum':
        return max(valeurs)
    if methode == 'minimum':
        return min(valeurs)
    raise ValueError(u'méthode d\'agrégation inconnue : %r' % (methode,))


def liaisons_resolues(numero_test):
    u"""Quantities whose variable name is established.

    Args:
        numero_test: SIA test number.

    Returns:
        dict: Subset of `LIAISONS[numero_test]`.
    """
    return dict((libelle, liaison)
                for libelle, liaison in LIAISONS.get(numero_test, {}).items()
                if liaison.get('aps_varname'))


def liaisons_manquantes(numero_test, reference=None):
    u"""Quantities of the test whose binding remains to be established.

    Args:
        numero_test: SIA test number.
        reference: Frozen reference, to compare the list of quantities with
            that of the bindings. Without it, only the declared bindings are
            examined.

    Returns:
        list[str]: Unresolved labels, sorted.
    """
    declarees = LIAISONS.get(numero_test, {})
    attendues = set(declarees)
    if reference is not None:
        attendues |= set(g['libelle_de'] for g in reference['grandeurs'])
    return sorted(libelle for libelle in attendues
                  if not declarees.get(libelle, {}).get('aps_varname'))


def extraire_candidat(numero_test, results_file, reference,
                      resolveur_local=None):
    u"""Assemble the candidate of a test, in the format expected by the engine.

    Args:
        numero_test: SIA test number, between 2 and 6.
        results_file: `ResultsReader` open on the case `.aps`.
        reference: Frozen reference of the test.
        resolveur_local: Callable `(cas) -> room_id`, when the test covers
            several rooms. `None` if only one room is involved.

    Returns:
        dict: `{quantity label: {case: value}}`, containing ONLY the
        quantities whose binding is resolved and whose reading succeeded.

    Raises:
        ValueError: If the test is not covered by this adapter.
        LiaisonNonResolue: If NO binding is resolved -- returning an
            empty candidate would read as "nothing passes", whereas nothing
            was looked up.
    """
    if numero_test not in TESTS_COUVERTS:
        raise ValueError(
            u'test %r hors de portée ; couverts : %s'
            % (numero_test, list(TESTS_COUVERTS)))

    resolues = liaisons_resolues(numero_test)
    if not resolues:
        raise LiaisonNonResolue(
            u'aucune liaison résolue pour le test %d. Les noms de variables '
            u'ne sont pas des symboles de l\'API : ils se relèvent sur un '
            u'.aps réel avec `decouvrir_variables()`, puis se déclarent dans '
            u'`LIAISONS`. Grandeurs concernées : %s'
            % (numero_test, u', '.join(liaisons_manquantes(numero_test, reference))))

    candidat = {}
    for grandeur in reference['grandeurs']:
        libelle = grandeur['libelle_de']
        liaison = resolues.get(libelle)
        if liaison is None:
            continue
        par_cas = {}
        for cas in grandeur['cas']:
            valeur = _lire_un_cas(results_file, liaison, cas, resolveur_local)
            if valeur is not None:
                par_cas[cas['cas']] = valeur
        if par_cas:
            candidat[libelle] = par_cas
    return candidat


def _lire_un_cas(results_file, liaison, cas, resolveur_local):
    u"""Read and aggregate the series of a case.

    Args:
        results_file: Open `ResultsReader`.
        liaison: `LIAISONS` entry.
        cas: Case entry from the reference.
        resolveur_local: Callable `(cas) -> room_id`, or `None`.

    Returns:
        float | None: Aggregated value, `None` if the series is absent.
    """
    room_id = resolveur_local(cas) if resolveur_local else None
    try:
        if room_id is None:
            serie = results_file.get_results(
                liaison['aps_varname'], liaison.get('niveau', NIVEAU_LOCAL))
        else:
            serie = results_file.get_room_results(
                room_id, liaison['aps_varname'],
                liaison.get('niveau', NIVEAU_LOCAL))
    except Exception:  # noqa: BLE001 -- an absent series is not a crash
        return None
    return agreger(serie, liaison.get('agregation', 'somme_annuelle'))


def etat_des_liaisons():
    u"""Summary of what is ready and what is not.

    Returns:
        str: Text table, readable in the VEScripts console.
    """
    lignes = [u'Liaisons grandeur -> variable de resultat', u'']
    for numero in TESTS_COUVERTS:
        declarees = LIAISONS.get(numero, {})
        resolues = liaisons_resolues(numero)
        lignes.append(u'  Test %d : %d/%d resolue(s)'
                      % (numero, len(resolues), len(declarees)))
        candidats = candidats_a_confirmer(numero)
        muettes = sans_candidat(numero)
        for libelle in sorted(set(declarees) - set(resolues)):
            lignes.append(u'      non resolue : %s%s'
                          % (libelle, _mention(libelle, candidats, muettes)))
    lignes.append(u'')
    lignes.append(u'Les noms de variables se relevent sur un .aps reel avec '
                  u'decouvrir_variables(), jamais par supposition.')
    lignes.append(u'Un candidat n est PAS une liaison : il indique quoi '
                  u'controler en premier, rien de plus.')
    return u'\n'.join(lignes)


def _mention(libelle, candidats, muettes):
    u"""Suffix line describing the state of an unresolved quantity.

    Three states, distinct and not to be confused: a hint exists; we looked
    and nothing matches; we have not looked yet. The third must never read
    as the second.

    Args:
        libelle: German label of the quantity.
        candidats: Hints for the test.
        muettes: Quantities of the test with no hint, and their reason.

    Returns:
        str: Text to concatenate, possibly empty.
    """
    piste = candidats.get(libelle)
    if piste:
        nom = piste['aps_varname_candidat']
        if nom is None:
            return u'  [pas de variable unique -- cf. a_confirmer]'
        return u'  [candidat a confirmer : %s]' % nom
    if libelle in muettes:
        return u'  [cherche, aucune variable ne correspond]'
    return u'  [pas encore cherche]'


# ---------------------------------------------------------------------------
# Second criterion: the hourly series, and its distribution
# ---------------------------------------------------------------------------
#
# The specifications of tests 2, 3 and 5 require "Jahresdatensätze in
# stündlicher Auflösung": the workbook calculates ITSELF the annual sum and
# the distribution from the 8760 values. Delivering an aggregate only satisfies
# half the criteria.
#
# THE TWO CRITERIA DO NOT NAME THE QUANTITIES THE SAME WAY. The annual block
# talks about ENERGY ("Jahresenergie solarer Wärmeeintrag", kWh); the
# distribution block talks about POWER ("Solarer Wärmeeintrag gesamt", W).
# It is the same physical quantity at two stages: the workbook sums the hourly
# power to obtain the annual energy. The correspondence is therefore established
# here, explicitly, rather than guessed by string similarity.
#
# `None` signals a DIAGNOSTIC quantity: it has a distribution in the
# workbook but no annual counterpart, and the specifications classify it
# under "Diagnoseresultate" / "Diagnosegrössen". It is not a criterion.
CORRESPONDANCE_DISTRIBUTIONS = {
    2: {
        u'Solarer Wärmeeintrag gesamt':
            u'Jahresenergie solarer Wärmeeintrag',
        u'Total transmittierte Solarstrahlung':
            u'Jahresenergie total transmittierte Solarstrahlung',
        u'Einstrahlung auf Fensterebene gesamt': None,
        u'Lamellenwinkel der Storen': None,
    },
    3: {
        u'Beleuchtungsleistung': u'Beleuchtungsenergie',
        u'Beleuchtungsstärke': None,
    },
    5: {
        u'Leistung Lufterwärmer': u'Wärmezufuhr Lufterwärmer',
        u'Leistung Luftkühler total': u'Wärmeabfuhr Luftkühler total',
        u'Leistung Luftkühler latent': u'Wärmeabfuhr Luftkühler latent',
        u'Leistung WRG': u'Wärmezufuhr WRG',
        u'Leistung WRG latent': u'Wärmezufuhr WRG latent',
        u'Leistung Zu- und Abluftventilator': u'Energiebedarf Ventilatoren',
        u'Zu-/Abluft-Volumenstrom': None,
        u'Zulufttemperatur im Betrieb': None,
    },
}

#: Annual quantities WITHOUT a corresponding distribution. Their only criterion
#: is the annual sum -- not because the workbook forgot, but because it carries
#: no distribution sheet for them.
SANS_DISTRIBUTION = {
    5: (u'Befeuchtungsenergie', u'Hilfsenergie WRG'),
}


def libelle_annuel(numero_test, grandeur_distribution):
    u"""Annual quantity corresponding to a distribution quantity.

    Args:
        numero_test: SIA test number.
        grandeur_distribution: Label as it appears in the distribution reference.

    Returns:
        str | None: Label from `LIAISONS`, or `None` if the quantity is a
            diagnostic.

    Raises:
        KeyError: If the quantity is not declared. Returning `None` silently
            would confuse it with a diagnostic, and would drop a criterion
            without saying so.
    """
    correspondance = CORRESPONDANCE_DISTRIBUTIONS.get(numero_test, {})
    if grandeur_distribution not in correspondance:
        raise KeyError(
            u'grandeur de distribution non déclarée pour le test %r : %r. '
            u'La déclarer dans CORRESPONDANCE_DISTRIBUTIONS, en diagnostic '
            u'(None) ou en grandeur de LIAISONS.'
            % (numero_test, grandeur_distribution))
    return correspondance[grandeur_distribution]


def extraire_serie(numero_test, results_file, libelle, room_id=None):
    u"""Read the RAW hourly series of a quantity, without aggregating it.

    This is what the specifications require: the workbook wants the 8760
    values and calculates the annual sum and distribution itself.

    Args:
        numero_test: SIA test number.
        results_file: Open `ResultsReader`.
        libelle: German label of the quantity, key of `LIAISONS`.
        room_id: Room, for a room-level quantity.

    Returns:
        list | None: Hourly series, or `None` if reading fails.

    Raises:
        LiaisonNonResolue: If the quantity has no established variable name.
            Returning an empty series would read as "the quantity equals zero".
    """
    liaison = LIAISONS.get(numero_test, {}).get(libelle)
    if liaison is None:
        raise LiaisonNonResolue(
            u'grandeur inconnue du test %d : %r' % (numero_test, libelle))
    if not liaison.get('aps_varname'):
        raise LiaisonNonResolue(
            u'liaison non résolue pour %r. Les noms de variables se relèvent '
            u'sur un .aps réel avec `decouvrir_variables()`.' % libelle)
    return _lire_serie(results_file, liaison, room_id)


def _lire_serie(results_file, liaison, room_id):
    u"""Read a series, at room or global level according to the binding.

    Args:
        results_file: Open `ResultsReader`.
        liaison: Resolved `LIAISONS` entry.
        room_id: Room, if the quantity is room-level.

    Returns:
        list | None: Series, or `None` if the API refuses.
    """
    varname, niveau = liaison['aps_varname'], liaison['niveau']
    try:
        if room_id is not None and niveau == NIVEAU_LOCAL:
            return results_file.get_room_results(room_id, varname, niveau)
        return results_file.get_results(varname, niveau)
    except Exception:  # noqa: BLE001 -- absence is a result, not a crash
        return None
