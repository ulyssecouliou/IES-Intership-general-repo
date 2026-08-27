# -*- coding: utf-8 -*-
"""Probe of result variables from a `.aps` file.

WHAT IT UNLOCKS. SIA tests 2 to 6 compare 20 quantities
("Wärmezufuhr Lufterwärmer", "Energiebedarf Ventilatoren", "Hilfsenergie
WRG"...) for which **none has an established VE variable name**:
`ve_adapter/bandes_adapter.py` declares all of them `aps_varname: None`. As
long as this reading does not exist, extraction refuses to run — rightly so:
guessing a name would produce a plausible but false number.

This probe lists what the file actually contains, at all useful levels. It
binds nothing: the matching of German label → VE variable is done afterwards,
by hand, by confronting the reading against the SIA workbook.

WHAT IT IS NOT. No value produced here is a validation result. The probe reads
names, units and series sizes; it judges no discrepancy.

HOW IT DIFFERS FROM `Run_VE_SIA4010_APS_Probe.py`, which already existed.
That one filters variables on eleven tokens chosen for Tests 1 and 2
(`load`, `solar`, `radiation`, `gain`, `window`, `temperature`...) and writes
its report to the VE project folder. **None of those tokens names a fan, a
humidifier or a heat-recovery unit**: it filters out exactly what tests 4 to 6
need. This one filters nothing, additionally queries Apache systems, energy
metering and units, and writes under `outputs/`. Both are read-only and can
coexist.

It writes `outputs/sonde_aps.json`. That is the file to send back.
"""

from __future__ import print_function

import io
import json
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

from scripts.run_test1_dans_ve import (  # noqa: E402
    LIMITE_ELEMENTS,
    _dans_ve,
    _membres,
    _serialisable,
    dire,
)

#: Ceiling that `_serialisable` applies to any sequence recorded in a step.
#: It truncated the 2026-08-06 reading to 500 variables, none of level "z".
#: Re-exported so that tests can target this threshold: it is precisely what
#: the complete list must work around.
LIMITE_ELEMENTS_ETAPE = LIMITE_ELEMENTS

CHEMIN_RAPPORT = os.path.join(_RACINE, "outputs", "sonde_aps.json")

#: Result levels queried by `get_variables`. The SIA labels for tests 4 to 6
#: (Lufterwärmer, Luftkühler, WRG, Ventilatoren) name air-handling components:
#: they live at the system level, not the room level. All three are queried to
#: avoid any assumption.
NIVEAUX = (
    ("z", "local / zone"),
    ("v", "systeme Apache"),
    ("w", "meteo"),
)

#: VE project sub-folders in which a `.aps` is searched. The list is indicative
#: and the search descends recursively: the directory tree is not assumed.
PROFONDEUR_RECHERCHE = 3

#: Beyond this, enumeration stops: a large project would produce an unreadable
#: report without conveying anything more.
LIMITE_FICHIERS = 40


def trouver_aps(racine_projet):
    """Searches for `.aps` files under a VE project folder.

    Args:
        racine_projet: VE project folder.

    Returns:
        list[str]: Paths found, most recent first. Empty if none.
    """
    # `VEProject.path` is not guaranteed to be a string: `os.path.isdir(3)`
    # would interpret an integer as a file descriptor.
    if not isinstance(racine_projet, str) or not os.path.isdir(racine_projet):
        return []
    trouves = []
    base = racine_projet.rstrip(os.sep)
    for dossier, sous_dossiers, fichiers in os.walk(base):
        profondeur = dossier[len(base) :].count(os.sep)
        if profondeur >= PROFONDEUR_RECHERCHE:
            del sous_dossiers[:]
            continue
        for nom in fichiers:
            if nom.lower().endswith(".aps"):
                trouves.append(os.path.join(dossier, nom))
        if len(trouves) >= LIMITE_FICHIERS:
            break
    trouves.sort(key=lambda c: os.path.getmtime(c), reverse=True)
    return trouves[:LIMITE_FICHIERS]


def _resume_serie(serie):
    """Describes a series without copying it.

    An hourly series has 8760 points: including it in full would make the
    report unreadable. Its range and first values are enough to recognise a
    quantity and spot an erroneous unit.

    Args:
        serie: Sequence of numbers, or anything else.

    Returns:
        dict: Summary, or a description of what prevented it.
    """
    try:
        valeurs = [v for v in serie if isinstance(v, (int, float))]
    except TypeError:
        return {"non_iterable": repr(serie)[:200]}
    if not valeurs:
        return {"nb_points": 0, "remarque": "aucune valeur numerique"}
    return {
        "nb_points": len(valeurs),
        "minimum": min(valeurs),
        "maximum": max(valeurs),
        "somme": sum(valeurs),
        "premieres_valeurs": valeurs[:6],
    }


def sonder(chemin_aps=None):
    """Reads the content of a `.aps`: variables, systems, energy metering.

    Args:
        chemin_aps: File to open. If `None`, searches in the current VE
            project and takes the most recent.

    Returns:
        dict: Report, also written to disk.
    """
    rapport = {
        "dans_ve": _dans_ve(),
        "etapes": [],
        "avertissement": (
            "Rapport de SONDE. Aucune valeur ici n'est un résultat de "
            "validation : ce fichier relève des noms de variables, des "
            "unités et des tailles de séries, rien d'autre."
        ),
    }

    def etape(nom, fonction):
        """Executes a step recording its outcome.

        Args:
            nom: Step label.
            fonction: Callable taking no argument.

        Returns:
            Any: The result, or `None` on failure.
        """
        try:
            valeur = fonction()
        except Exception as erreur:  # noqa: BLE001 -- on consigne, on ne masque pas
            rapport["etapes"].append(
                {
                    "nom": nom,
                    "statut": "ECHEC",
                    "type_erreur": type(erreur).__name__,
                    "erreur": "%s" % erreur,
                }
            )
            dire("  [ECHEC] %-42s %s" % (nom, type(erreur).__name__))
            return None
        rapport["etapes"].append(
            {
                "nom": nom,
                "statut": "OK",
                "type": type(valeur).__name__,
                "valeur": _serialisable(valeur),
            }
        )
        dire("  [OK]    %-42s %s" % (nom, repr(valeur)[:48]))
        return valeur

    dire("=== SONDE APS : variables de resultats ===")
    if not rapport["dans_ve"]:
        dire("  hors VEScripts : la sonde ne peut rien apprendre ici.")
        dire("  a lancer au bouton Run, depuis une VE ouverte sur un projet")
        dire("  dont AU MOINS UNE simulation a deja tourne.")
        return rapport

    import iesve

    # --- Locate the file -------------------------------------------
    if chemin_aps is None:
        projet = etape("projet courant", lambda: iesve.VEProject.get_current_project())
        dossier = etape("dossier du projet", lambda: getattr(projet, "path", None))
        candidats = etape("fichiers .aps trouves", lambda: trouver_aps(dossier)) or []
        if not candidats:
            etape("ouverture du .aps", lambda: _sans_aps())
            _ecrire(rapport)
            return rapport
        chemin_aps = candidats[0]
        dire("  -> retenu (le plus recent) : %s" % os.path.basename(chemin_aps))

    lecteur = etape("ResultsReader.open", lambda: iesve.ResultsReader.open(chemin_aps))
    if lecteur is None:
        _ecrire(rapport)
        return rapport
    rapport["aps"] = {
        "chemin": chemin_aps,
        "nom": os.path.basename(chemin_aps),
    }

    try:
        _relever(etape, lecteur, rapport)
    finally:
        etape("fermeture", lambda: lecteur.close())

    _ecrire(rapport)
    return rapport


def _sans_aps():
    """Signals the absence of a results file.

    Raises:
        RuntimeError: Always. An explicit failure step is better than a
            silently empty report.
    """
    raise RuntimeError(
        "aucun .aps sous le dossier du projet. Lancer une simulation "
        "ApacheSim dans VE, puis relancer cette sonde."
    )


def _relever(etape, lecteur, rapport=None):
    """Queries all useful entry points of the `ResultsReader`.

    Args:
        etape: Recorded execution function.
        lecteur: Open `ResultsReader`.
        rapport: Report where the COMPLETE variable list is deposited, outside
            the ceiling applied to steps.
    """
    # --- Time frame: without it, an annual sum has no meaning.
    for nom in (
        "results_per_day",
        "first_day",
        "last_day",
        "year",
        "weather_file",
        "hvac_file",
    ):
        etape("%s" % nom, lambda n=nom: getattr(lecteur, n))

    # --- Variables: the core of the reading.
    #
    # CONFIRMED BY EXECUTION on 2026-08-06 on ZOER_C1.aps:
    # `get_variables()` WITHOUT argument responds; `get_variables('z')` raises
    # ArgumentError. `swiss_sia` was right, `bandes_adapter` was wrong.
    # The level is read from `model_level`, entry by entry.
    #
    # The argument forms are still read: if a VE version accepted them, the
    # report would say so rather than letting the opposite be assumed.
    variables = etape("get_variables()  [sans argument]", lambda: lecteur.get_variables())
    for niveau, libelle in NIVEAUX:
        etape(
            "get_variables(%r)  [%s]" % (niveau, libelle),
            lambda n=niveau: lecteur.get_variables(n),
        )

    # The complete list is deposited OUTSIDE the steps: the 500-element ceiling
    # had truncated the 2026-08-06 reading to 500 entries, none of level "z".
    # A guard intended for readability had cut exactly what the probe exists to
    # report.
    if rapport is not None and variables:
        rapport["variables"] = [_variable_lisible(v) for v in variables]
        rapport["variables_par_niveau"] = _compter_par_niveau(variables)
        dire(
            "  -> %d variables, par niveau : %s"
            % (len(variables), _en_clair(rapport["variables_par_niveau"]))
        )

    # --- Rooms: level-z quantities are read per room.
    etape("get_room_list", lambda: lecteur.get_room_list())
    etape("get_room_ids", lambda: lecteur.get_room_ids())

    # --- Apache systems: this is where Luftkühler, Lufterwärmer and
    # --- WRG live, if they exist in the model.
    systemes = etape("get_apache_systems", lambda: lecteur.get_apache_systems())
    if systemes:
        etape(
            "get_all_apache_system_results (1er systeme)",
            lambda: _apercu_resultats(lecteur.get_all_apache_system_results(systemes[0])),
        )

    # --- Energy metering: the most likely path for "Energiebedarf
    # --- Ventilatoren" and "Befeuchtungsenergie".
    etape("get_energy_uses", lambda: lecteur.get_energy_uses())
    etape("get_energy_meters", lambda: lecteur.get_energy_meters())
    etape("get_energy_sources", lambda: lecteur.get_energy_sources())

    # --- HVAC components, if an ApacheHVAC network exists.
    etape("get_component_objects", lambda: lecteur.get_component_objects())

    # `get_process_variables()` without argument raises ArgumentError: it
    # expects a process, which `get_process_list()` provides. Observed 2026-08-06.
    processus = etape("get_process_list", lambda: lecteur.get_process_list())
    for nom_processus in list(processus or [])[:6]:
        etape(
            "get_process_variables(%r)" % nom_processus,
            lambda p=nom_processus: lecteur.get_process_variables(p),
        )

    # --- Units: without them, it is unknown whether a series is in W or kW.
    etape("get_units", lambda: lecteur.get_units())

    # --- Complete surface, for comparison with ve_api_surface.json.
    etape("attributs du ResultsReader", lambda: _membres(lecteur))


#: Fields kept from a `get_variables()` entry. Everything needed to recognise
#: a quantity and convert its unit, nothing more.
CHAMPS_VARIABLE = (
    "aps_varname",
    "display_name",
    "model_level",
    "units_type",
    "subtype",
    "custom_type",
    "source",
)


def _variable_lisible(variable):
    """Reduces a `get_variables()` entry to what is useful.

    Args:
        variable: Entry as returned by the API.

    Returns:
        dict: Retained fields, or the `repr` if the form is unexpected.
    """
    if not isinstance(variable, dict):
        return {"forme_inattendue": repr(variable)[:200]}
    return dict(
        (champ, variable[champ]) for champ in CHAMPS_VARIABLE if champ in variable
    )


def _compter_par_niveau(variables):
    """Counts variables by `model_level`.

    Args:
        variables: List of `get_variables()` entries.

    Returns:
        dict: `{level: count}`, sorted by level.
    """
    comptes = {}
    for variable in variables:
        niveau = "%s" % (
            variable.get("model_level") if isinstance(variable, dict) else "?"
        )
        comptes[niveau] = comptes.get(niveau, 0) + 1
    return dict(sorted(comptes.items()))


def _en_clair(comptes):
    """Puts the counts by level on a single console line.

    Args:
        comptes: `{level: count}`.

    Returns:
        str: For example "e=274, c=184, z=61".
    """
    return ", ".join("%s=%d" % couple for couple in comptes.items())


def _apercu_resultats(resultats):
    """Summarises a result set without copying the series.

    Args:
        resultats: What a `get_all_*_results` returns.

    Returns:
        dict | Any: Summary per variable, or the value as-is if its form is
            not recognised — in which case the `repr` is informative.
    """
    if not isinstance(resultats, dict):
        return resultats
    return dict(
        ("%s" % cle, _resume_serie(serie)) for cle, serie in list(resultats.items())[:60]
    )


def _ecrire(rapport):
    """Writes the report to disk and says where to find it.

    Args:
        rapport: Probe report.
    """
    dossier = os.path.dirname(CHEMIN_RAPPORT)
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    with io.open(CHEMIN_RAPPORT, "w", encoding="utf-8") as flux:
        flux.write(json.dumps(rapport, ensure_ascii=False, indent=2))
    dire()
    dire("rapport de sonde : %s" % CHEMIN_RAPPORT)
    dire(
        "-> me renvoyer ce fichier : il contient les 20 noms de variables "
        "qui manquent aux tests 2 a 6."
    )


def main(arguments=()):
    """Entry point.

    Args:
        arguments: Explicit `.aps` path, optional.

    Returns:
        int: 0 if the report could be written, 1 otherwise.
    """
    chemins = [a for a in arguments if not a.startswith("--")]
    rapport = sonder(chemins[0] if chemins else None)
    return 0 if rapport.get("etapes") else 1
