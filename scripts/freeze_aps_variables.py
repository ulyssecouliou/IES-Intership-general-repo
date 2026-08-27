# -*- coding: utf-8 -*-
"""Freezes the result-variable catalogue read from a real VE instance.

WHY THIS FILE EXISTS. `outputs/` is ignored by Git. The probe report
`outputs/sonde_aps.json` is therefore absent from a fresh clone — and with it,
the evidence against which `ve_adapter/tests/test_bandes_adapter.py` checks
every candidate variable name. Those tests would have **silently ignored
themselves**, giving the impression that the candidates were verified while
nothing controlled them any longer.

WHAT THIS FILE IS, AND IS NOT. It is a **name catalogue**: what VE 2025 can
produce. It is neither a SIA reference value, nor a binding, nor a simulation
result. No series appears in it.

Usage:
    python scripts/freeze_aps_variables.py [chemin_du_rapport] [--ecrire]

The report is produced by `Run_VE_SIA4010_Sonde_APS.py`, via the Run button
from VE, on a project that has already been simulated.
"""

from __future__ import print_function

import io
import json
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))

_SORTIE = os.path.join(
    _RACINE, "refs", "reference-data", "iesve-aps-variables-ve2025.json"
)

RAPPORT_PAR_DEFAUT = os.path.join(_RACINE, "outputs", "sonde_aps.json")

#: Fields retained. Everything needed to recognise a quantity and convert its
#: unit, nothing more.
CHAMPS = ("aps_varname", "display_name", "model_level", "units_type")

RESERVES = [
    "Catalogue de NOMS, pas de valeurs. Il dit ce que VE sait produire, pas "
    "ce que vaut une grandeur.",
    "Relevé sur UN modèle (ZOER_C1). Un modèle doté d'un réseau ApacheHVAC "
    "exposerait vraisemblablement d'autres variables : l'absence d'un nom "
    "ici ne prouve pas que VE ne sait pas le produire.",
    "Plusieurs entrées partagent un même aps_varname avec des display_name "
    "ou des units_type différents (ainsi « Ext surface incident solar flux », "
    "en Radiation flux et en Heat flow). Le couple (aps_varname, "
    "model_level) n'est donc PAS une clé unique.",
    "Les libellés marqués [obs] sont signalés obsolètes par VE elle-même.",
]


class RapportInexploitable(RuntimeError):
    """Raised when the probe report does not carry the complete reading."""


def _lire_rapport(chemin):
    """Loads an APS probe report.

    Args:
        chemin: Explicit path, or `None` for the default location.

    Returns:
        dict: Report content.

    Raises:
        RapportInexploitable: If the file is missing or does not carry the
            `variables` key — in which case it comes from a probe predating the
            complete reading, and freezing its truncated list would be worse
            than freezing nothing.
    """
    chemin = chemin or RAPPORT_PAR_DEFAUT
    if not os.path.isfile(chemin):
        raise RapportInexploitable(
            "rapport introuvable : %s. Lancer Run_VE_SIA4010_Sonde_APS.py "
            "depuis VE, sur un projet dont une simulation a tourné." % chemin
        )
    with io.open(chemin, encoding="utf-8") as flux:
        rapport = json.load(flux)
    if not rapport.get("variables"):
        raise RapportInexploitable(
            "le rapport ne porte pas la clé « variables ». Il vient d'une "
            "sonde antérieure, dont le relevé était tronqué à 500 entrées : "
            "le figer donnerait un catalogue incomplet qui se lirait comme "
            "complet."
        )
    return rapport


def _normaliser(variables):
    """Reduces and orders the recorded entries.

    Args:
        variables: Entries from the report.

    Returns:
        list[dict]: Entries reduced to useful fields, sorted by level then
            name, exact duplicates removed.
    """
    vues = set()
    retenues = []
    for variable in variables:
        if not isinstance(variable, dict):
            continue
        reduite = dict((champ, variable.get(champ)) for champ in CHAMPS)
        signature = tuple(reduite[champ] for champ in CHAMPS)
        if signature in vues:
            continue
        vues.add(signature)
        retenues.append(reduite)
    return sorted(
        retenues,
        key=lambda v: (
            "%s" % v["model_level"],
            "%s" % v["aps_varname"],
            "%s" % v["display_name"],
        ),
    )


def _compter_par_niveau(variables):
    """Counts entries by model level.

    Args:
        variables: Normalised entries.

    Returns:
        dict: `{level: count}`, sorted.
    """
    comptes = {}
    for variable in variables:
        niveau = "%s" % variable["model_level"]
        comptes[niveau] = comptes.get(niveau, 0) + 1
    return dict(sorted(comptes.items()))


def construire(chemin_rapport=None):
    """Builds the structure to freeze.

    Args:
        chemin_rapport: Explicit report path.

    Returns:
        dict: Structure ready to write.
    """
    rapport = _lire_rapport(chemin_rapport)
    brutes = rapport["variables"]
    variables = _normaliser(brutes)
    return {
        "grandeur": "Catalogue des variables de résultats exposées par une "
        "VE 2025, relevé dans un .aps réel",
        "statut": "FIGÉ — introspection runtime, pas une lecture de doc",
        "source": {
            "rapport": os.path.basename(chemin_rapport or RAPPORT_PAR_DEFAUT),
            "aps": (rapport.get("aps") or {}).get("nom"),
            "methode": "Run_VE_SIA4010_Sonde_APS.py, ResultsReader."
            "get_variables() sans argument",
            "pourquoi": "outputs/ est ignoré par Git : sans ce fichier, les "
            "tests qui confrontent chaque nom candidat à la "
            "réalité s'ignorent en silence sur un clone neuf.",
        },
        "nombre": len(variables),
        "nombre_brut": len(brutes),
        "doublons_exacts_ecartes": len(brutes) - len(variables),
        "par_niveau": _compter_par_niveau(variables),
        "reserves": RESERVES,
        "variables": variables,
    }


def main(arguments):
    """Command-line entry point.

    Args:
        arguments: Arguments without the script name.

    Returns:
        int: 0 if everything went well.
    """
    chemins = [a for a in arguments if not a.startswith("--")]
    donnees = construire(chemins[0] if chemins else None)

    print("relevé  : %s (%s)" % (donnees["source"]["rapport"], donnees["source"]["aps"]))
    print(
        "variables : %d retenues sur %d relevées (%d doublons exacts "
        "écartés)"
        % (donnees["nombre"], donnees["nombre_brut"], donnees["doublons_exacts_ecartes"])
    )
    print(
        "par niveau : %s"
        % ", ".join("%s=%d" % couple for couple in donnees["par_niveau"].items())
    )

    if "--ecrire" in arguments:
        with io.open(_SORTIE, "w", encoding="utf-8") as flux:
            flux.write(json.dumps(donnees, ensure_ascii=False, indent=1))
            flux.write("\n")
        print()
        print("écrit : %s" % os.path.relpath(_SORTIE, _RACINE))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
