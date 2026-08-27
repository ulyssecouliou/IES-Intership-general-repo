# -*- coding: utf-8 -*-
"""Generates the ApacheHVAC data entry sheets for SIA tests 5 and 6.

SAME REASON AS FOR TEST 4. `HVACNetwork` exposes no creation method:
the network must be entered manually, once, in the ApacheHVAC editor.
Afterwards the `.asp` is versioned and reloaded via `load_network`.

WHAT IS DIFFERENT HERE. The Test 4 sheet is drawn from a Python module where
parameters had been captured one by one. These are drawn from
`refs/reference-data/test-{5,6}.reseau.json`, produced by an extractor that
reads the PDF — so **gaps in the specification bubble up to the sheet**,
named, at the top, instead of being silently filled in.

That is the key point: in Test 5, five parameters depend on the variant
(5A to 5D) and the PDF table has four columns for two cells. A sheet that
resolved them would build two wrong variants out of four, with nothing
flagging it before the final comparison.

Usage:
    python scripts/build_fiche_apachehvac_56.py [--ecrire]
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

from scripts.build_reseau_ventilation_reference import (  # noqa: E402
    A_CONFIRMER,
    RELEVE,
    SUR_GRAPHIQUE,
)

_REFS = os.path.join(_RACINE, "refs", "reference-data")
_DOCS = os.path.join(_RACINE, "docs")

TESTS = (5, 6)

#: Sections of the sheet, in airflow order, with the expected `iesve` class
#: at survey time. The class name is used to COMPARE the entered network against
#: this sheet after the fact, via `HVACNetwork.components` — it is not an
#: object name to enter.
BLOCS = [
    ("reseau", "Réseau et conditions générales", None),
    ("ventilateurs", "Ventilateurs", "HVACFan"),
    ("recuperateur", "Récupérateur de chaleur", "HVACAirToAirHeatEnthalpyExchanger"),
    ("batterie_chaude", "Batterie chaude", "HVACHeatingCoil"),
    ("batterie_froide", "Batterie froide", "HVACCoolingCoil"),
    ("humidificateur", "Humidificateur", None),
]

#: What each sheet enables, and what it does not.
PORTEE = {
    5: (
        "Quatre variantes (5A à 5D) : type de récupérateur, taux d'échange, "
        "part de pression constante et type d'humidificateur en dépendent.",
        "Test 5 — classes de validation 2B, 4A et 4B",
    ),
    6: (
        "Une seule configuration : récupération par boucle à eau glycolée "
        "(« Kreislaufverbund »), ventilation à trois étages.",
        "Test 6 — classes de validation 3, 4A et 4B",
    ),
}


def charger(numero_test):
    """Loads the frozen network reference data.

    Args:
        numero_test: 5 or 6.

    Returns:
        dict: Reference data.

    Raises:
        IOError: If the reference data has not been frozen.
    """
    chemin = os.path.join(_REFS, "test-%d.reseau.json" % numero_test)
    if not os.path.exists(chemin):
        raise IOError(
            "référentiel absent : %s. Le produire par "
            "`python scripts/build_reseau_ventilation_reference.py "
            "--ecrire`." % os.path.relpath(chemin, _RACINE)
        )
    with io.open(chemin, encoding="utf-8") as flux:
        return json.load(flux)


def _valeur_lisible(champ):
    """Formats the value of a field.

    Args:
        champ: Entry from the reference data.

    Returns:
        str: Markdown cell. A field to be resolved NEVER shows a value:
        showing a dash would suggest zero, showing a value would suggest a
        confirmed reading.
    """
    if champ["statut"] == A_CONFIRMER:
        return "**À TRANCHER**"
    valeur = champ["valeur"]
    if isinstance(valeur, (list, tuple)):
        return "**%s**" % " – ".join("%s" % v for v in valeur)
    return "**%s**" % valeur


def _tableau(bloc):
    """Table rows for a component section.

    Args:
        bloc: Sub-dictionary from the reference data.

    Returns:
        list[str]: Markdown rows.
    """
    lignes = ["| Paramètre | Valeur | Source (section du PDF) |", "|---|---|---|"]
    for cle in sorted(bloc):
        champ = bloc[cle]
        if not isinstance(champ, dict) or "statut" not in champ:
            continue
        lignes.append(
            "| `%s` | %s | %s |" % (cle, _valeur_lisible(champ), champ["source"])
        )
    return lignes


def _tableau_courbes(courbes):
    """Table rows for the sliding setpoints.

    Args:
        courbes: `courbes` block from the reference data.

    Returns:
        list[str]: Markdown rows.
    """
    lignes = [
        "| Consigne | Points (θ extérieure → consigne) | Lecture |",
        "|---|---|---|",
    ]
    for cle in sorted(courbes):
        courbe = courbes[cle]
        if courbe["statut"] == A_CONFIRMER:
            lignes.append("| `%s` | **À TRANCHER** | relevé refusé |" % cle)
            continue
        points = " ; ".join("%g °C → %g °C" % (x, y) for x, y in courbe["points"])
        lignes.append("| `%s` | %s | étiquettes du graphique |" % (cle, points))
    return lignes


def _a_trancher(reference):
    """Collects everything the specification does not allow to resolve.

    Args:
        reference: Loaded reference data.

    Returns:
        list[tuple]: `(field path, source, reason)`.
    """
    trous = []
    for nom_bloc in sorted(reference):
        bloc = reference[nom_bloc]
        if nom_bloc.startswith("_") or not isinstance(bloc, dict):
            continue
        for cle in sorted(bloc):
            champ = bloc[cle]
            if not isinstance(champ, dict):
                continue
            if champ.get("statut") != A_CONFIRMER:
                continue
            trous.append(
                (
                    "%s.%s" % (nom_bloc, cle),
                    champ.get("source") or "—",
                    champ.get("a_confirmer") or "—",
                )
            )
    return trous


def construire(numero_test):
    """Writes the data entry sheet for one test.

    Args:
        numero_test: 5 or 6.

    Returns:
        str: Markdown document.
    """
    reference = charger(numero_test)
    portee, classes = PORTEE[numero_test]
    trous = _a_trancher(reference)
    compte = reference["_bilan"]["effectifs"]

    lignes = [
        "# Fiche de saisie — réseau ApacheHVAC du Test SIA 4010 n° %d" % numero_test,
        "",
        "> **Document généré** par `scripts/build_fiche_apachehvac_56.py`, "
        "depuis `refs/reference-data/test-%d.reseau.json` — lui-même extrait "
        "de `%s`. Ne rien corriger ici : corriger l'extracteur et "
        "régénérer." % (numero_test, reference["_source"]),
        "",
        "> **%d paramètres relevés, %d lus sur un graphique, %d À TRANCHER "
        "avant toute saisie.**"
        % (
            compte.get(RELEVE, 0),
            compte.get(SUR_GRAPHIQUE, 0),
            compte.get(A_CONFIRMER, 0),
        ),
        "",
        "- Portée : %s" % portee,
        "- Classes visées : %s" % classes,
        "",
        "## Pourquoi cette saisie est manuelle",
        "",
        "`HVACNetwork` n'expose que `components`, `systems`, `controllers`, "
        "`get_component_by_id`, `load_network` et `path` — **aucune méthode "
        "de création**. Le réseau ne peut pas être construit par script. Une "
        "fois saisi, le `.asp` se versionne et se recharge par "
        "`load_network` ; tout le reste redevient scriptable.",
        "",
        "---",
        "",
    ]

    if trous:
        lignes.extend(
            [
                "## ⚠ À trancher AVANT de saisir quoi que ce soit",
                "",
                "Ces %d points ne sont pas dans la couche texte du PDF. Les "
                "combler au jugé produirait un réseau plausible et faux — le "
                "genre d'erreur qui ne se voit qu'à la comparaison finale, "
                "après une simulation annuelle." % len(trous),
                "",
                "| Champ | Où regarder dans le PDF | Pourquoi il manque |",
                "|---|---|---|",
            ]
        )
        for chemin, source, raison in trous:
            lignes.append("| `%s` | %s | %s |" % (chemin, source, raison))
        lignes.append("")
        lignes.append("---")
        lignes.append("")

    lignes.append("## Composants")
    lignes.append("")
    for nom_bloc, titre, classe in BLOCS:
        bloc = reference.get(nom_bloc)
        if not bloc:
            continue
        lignes.append("### %s" % titre)
        lignes.append("")
        if classe:
            lignes.append("*Classe `iesve` attendue au relevé : `%s`*" % classe)
            lignes.append("")
        lignes.extend(_tableau(bloc))
        lignes.append("")

    lignes.append("## Consignes glissantes")
    lignes.append("")
    lignes.append(
        "Elles sont **dessinées** dans la spécification. Les points "
        "ci-dessous viennent des étiquettes de données du "
        "graphique. **Les paliers au-delà de ces points ne sont pas "
        "étiquetés** : le tracé les suggère constants, la "
        "spécification ne l'écrit pas."
    )
    lignes.append("")
    lignes.extend(_tableau_courbes(reference["courbes"]))
    lignes.append("")

    lignes.extend(
        [
            "## Après la saisie",
            "",
            "1. Enregistrer le réseau ; noter le chemin du `.asp` et le " "versionner.",
            "2. Lancer ApacheSim sur **l'année complète** — un `.aps` partiel "
            "rend toute somme annuelle inexploitable.",
            "3. Lancer `Run_VE_SIA4010_Sonde_APS.py` et renvoyer "
            "`outputs/sonde_aps.json`.",
            "4. Le relevé donnera les noms de variables des batteries, du "
            "récupérateur, des ventilateurs et de l'humidificateur — les "
            "liaisons encore manquantes du Test %d." % numero_test,
            "",
            "## Ce que cette fiche ne dit pas",
            "",
            "- Elle ne déclare rien conforme. Elle décrit une SAISIE ; le verdict "
            "vient de la comparaison aux valeurs de référence publiées.",
            "- Les charges internes et l'occupation renvoient à SIA 2024:2021, "
            "absent du dépôt sous forme exploitable.",
            "- Le climat SIA 2028 DRY Zürich-Kloten reste absent : sans lui, "
            "aucune simulation de ce test n'est un cas de validation SIA.",
            "",
        ]
    )
    return "\n".join(lignes) + "\n"


def main(arguments=()):
    """Entry point.

    Args:
        arguments: `--ecrire` to write the sheets.

    Returns:
        int: 0 if both sheets were built successfully.
    """
    for numero in TESTS:
        try:
            document = construire(numero)
        except IOError as erreur:
            print("Test %d : %s" % (numero, erreur))
            return 1
        trous = len(_a_trancher(charger(numero)))
        print(
            "Test %d : %d lignes, %d point(s) à trancher"
            % (numero, document.count("\n"), trous)
        )
        if "--ecrire" in arguments:
            chemin = os.path.join(_DOCS, "FICHE-APACHEHVAC-TEST%d.md" % numero)
            with io.open(chemin, "w", encoding="utf-8") as flux:
                flux.write(document)
            print("    écrit : %s" % os.path.relpath(chemin, _RACINE))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
