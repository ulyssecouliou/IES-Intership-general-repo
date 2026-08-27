# -*- coding: utf-8 -*-
"""Inventories the actual surface of the installed `iesve` module.

To be run from the IESVE Scripts window (Run button). **Read-only**:
opens no project, creates nothing, simulates nothing, modifies no VE object.
The script only introspects the already-loaded module.

WHY
--------
The measured installation is **VE 2025** (probe `Run_VE_Probe_Runtime.py`,
2026-07-31), whereas the only documentation in our possession is
`refs/VEScripts-API-VE2023.pdf`. All API statements in
`docs/ADR-001-architecture-MSP.md` §3 are drawn from it and have therefore
never been confronted with the actually installed version. An API rarely
shrinks, but it extends and renames: until this check is done, the adapter
layer rests on documentation two major versions old.

This probe replaces the documentation: it produces the exact list of classes
and methods available here and now.

OUTPUT
------
`ve_api_surface.json` beside this script, plus a console summary that directly
checks the symbols the MSP depends on.
"""

import inspect
import json
import os
import sys

# Symbols on which the chosen architecture rests (ADR-001 §3). Each is
# checked explicitly: these are the ones that must exist, not "the API in general".
SYMBOLES_CRITIQUES = [
    (
        "ApacheSim",
        ["save_options", "run_simulation", "get_options"],
        "lancer une simulation sans interface",
    ),
    (
        "ResultsReader",
        ["open", "get_results", "get_room_results", "get_variables"],
        "lire les series horaires des .aps",
    ),
    (
        "VECdbMaterial",
        ["get_properties", "set_properties"],
        "proprietes materiaux (ASHRAE 140 tab. 7-2 / 7-27)",
    ),
    (
        "VECdbConstruction",
        ["add_layer", "insert_layer", "delete_layer", "get_layers", "set_properties"],
        "composition des constructions",
    ),
    (
        "VECdbLayer",
        ["get_properties", "set_properties"],
        "coefficient de surface externe (spec Test 1 §8 pt 6)",
    ),
    ("VECdbProject", [], "acces a la base de constructions du projet"),
    ("VEProject", [], "projet actif"),
    ("VERoomData", [], "donnees de local"),
    ("VEThermalTemplate", [], "consignes et gabarits thermiques"),
    ("VEProfile", [], "profils horaires"),
    ("VEApacheSystem", [], "systemes ApacheHVAC (tests 4-5)"),
    ("VESuncast", [], "protection solaire (test 2)"),
    ("VEBody", [], "geometrie"),
    ("VESurface", [], "surfaces et ouvertures"),
    ("WeatherFileReader", [], "fichier meteo de reference (DRYCOLD.TMY)"),
]


def _membres_publics(objet):
    """Public names of an object, sorted, excluding private attributes."""
    try:
        return sorted(nom for nom in dir(objet) if not nom.startswith("_"))
    except Exception:
        return []


def _resume_doc(objet):
    doc = getattr(objet, "__doc__", None)
    if not doc:
        return ""
    return doc.strip().splitlines()[0][:120]


def main():
    try:
        import iesve
    except ImportError as erreur:
        print("ECHEC : impossible d'importer `iesve` (" + str(erreur) + ").")
        print("Ce script doit tourner DANS la fenetre Scripts d'IESVE.")
        return 1

    print("=== SURFACE DE L API iesve (VE reellement installe) ===")
    print("python        : " + sys.version.split()[0])
    print("executable    : " + str(sys.executable))
    version = getattr(iesve, "__version__", None) or getattr(iesve, "version", None)
    print("iesve.version : " + str(version))
    print("")

    noms = _membres_publics(iesve)
    print("Symboles publics exposes par `iesve` : " + str(len(noms)))
    print("")

    surface = {}
    for nom in noms:
        try:
            objet = getattr(iesve, nom)
        except Exception as erreur:
            surface[nom] = {"kind": "inaccessible", "error": str(erreur)}
            continue
        genre = (
            "class"
            if inspect.isclass(objet)
            else "function" if callable(objet) else "value"
        )
        entree = {"kind": genre, "doc": _resume_doc(objet)}
        if genre == "class":
            entree["members"] = _membres_publics(objet)
        surface[nom] = entree

    # --- Targeted check of the symbols the MSP depends on ---
    print("--- symboles critiques (ADR-001 §3) ---")
    manquants = []
    for nom, methodes, usage in SYMBOLES_CRITIQUES:
        if nom not in surface:
            print("  ABSENT   {0:22s} {1}".format(nom, usage))
            manquants.append(nom)
            continue
        membres = set(surface[nom].get("members", []))
        absentes = [m for m in methodes if m not in membres]
        if absentes:
            print("  PARTIEL  {0:22s} manque {1}".format(nom, ", ".join(absentes)))
            manquants.append(nom + "." + ",".join(absentes))
        else:
            detail = "{0} methodes".format(len(membres)) if membres else "present"
            print("  OK       {0:22s} {1:14s} {2}".format(nom, detail, usage))

    print("")
    print("--- nouveautes eventuelles (symboles absents du guide VE 2023) ---")
    connus_2023 = set(
        [
            "AirExchange",
            "ApacheSim",
            "BpfCustom",
            "CasualGain",
            "EnergySources",
            "IECC",
            "ImportGBXML",
            "NECB",
            "PRM",
            "ProjectInfo",
            "ResultsReader",
            "RoomAirExchange",
            "RoomInternalGain",
            "RoomGroups",
            "TariffsEngine",
            "TDVCalculator",
            "TransformerLosses",
            "UMLH",
            "VEAdjacency",
            "VEApacheSystem",
            "VEBody",
            "VECdbConstruction",
            "VECdbDatabase",
            "VECdbLayer",
            "VECdbMaterial",
            "VECdbProject",
            "VEComponentProcess",
            "VEEnergyMeter",
            "VEGeometry",
            "VELocate",
            "VEMacroFlo",
            "VEModel",
            "VEProfile",
            "VEProject",
            "VERenewables",
            "VERoomData",
            "VESankey",
            "VESuncast",
            "VESurface",
            "VEThermalTemplate",
            "WeatherFileReader",
            "RefModelUserEdits",
        ]
    )
    nouveaux = [n for n in noms if n not in connus_2023 and n[0].isupper()]
    print("  " + (", ".join(nouveaux) if nouveaux else "(aucun)"))
    disparus = sorted(connus_2023 - set(noms))
    print("")
    print("--- documentes en 2023 mais ABSENTS ici ---")
    print("  " + (", ".join(disparus) if disparus else "(aucun)"))

    chemin = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "ve_api_surface.json"
    )
    try:
        with open(chemin, "w", encoding="utf-8") as flux:
            json.dump(
                {
                    "python": sys.version,
                    "executable": str(sys.executable),
                    "iesve_version": str(version),
                    "symbols": surface,
                },
                flux,
                ensure_ascii=False,
                indent=1,
                sort_keys=True,
            )
        print("")
        print("Inventaire complet ecrit dans : " + chemin)
    except Exception as erreur:
        print("Ecriture impossible (" + str(erreur) + ").")

    print("")
    if manquants:
        print(
            "ATTENTION : " + str(len(manquants)) + " symbole(s) critique(s) "
            "absent(s) ou incomplet(s) — voir ci-dessus."
        )
    else:
        print("Tous les symboles critiques de l architecture sont presents.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
