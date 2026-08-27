# -*- coding: utf-8 -*-
"""Freeze the Test 4 temperature setpoint, read off the specification chart.

POURQUOI CE FICHIER EXISTE. Dans `Spezifikation_Test4.pdf`, la ligne
"Sollwerte / Raumlufttemperatur" is **empty in the text layer**. The
setpoint is not written there: it is drawn, in an image occupying the
rectangle (307, 74)–(581, 182) de la page 2.

The practical consequence: any automatic extraction from the PDF -- ours
comprise, jusqu'au 2026-08-07 — conclut que le Test 4 n'a pas de consigne de
temperature. That is wrong, and it would be a silent error: a model
construit sans elle tournerait, produirait des nombres, et serait faux.

CE QUE LE GRAPHIQUE MONTRE. Une consigne GLISSANTE, fonction de la moyenne
48-hour rolling mean of the outdoor temperature -- not a fixed value. Four
break points are **annotated in plain text on the plot** ("12;23", "17;25",
"19;22", "23.5;23.5"): those are chart data labels, not pixels read by eye.

WHAT REMAINS UNVERIFIED. Which curve is which -- blue for cooling, red for
heating -- is INFERRED from their relative position (the heating setpoint is
the lower one), not from a legend: the chart carries none. The cross-check is
consistent, the dead band widening from 1.0 K to 1.5 K, but it is still an
inference and is recorded as one.

Usage :
    python scripts/freeze_test4_consignes.py [--ecrire]
"""

from __future__ import print_function

import io
import json
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))

_SORTIE = os.path.join(_RACINE, "refs", "reference-data", "test-4.consignes.json")

_SPEC = os.path.join("SIA_4010_geteilter_Link", "Test4", "Spezifikation_Test4.pdf")

#: Bounding box of the image that carries it, page 2 (index 1). Recorded so
#: the reading can be reproduced exactly.
_RECTANGLE_IMAGE = {"page": 2, "x0": 307.35, "y0": 74.55, "x1": 581.10, "y1": 182.55}

#: Break points, as ANNOTATED on the plot. Each pair is
#: `(48-hour rolling mean of outdoor temperature, setpoint)`, in degrees C.
#: Hors de ces bornes, les deux courbes sont horizontales.
CONSIGNES = {
    "chauffage": {
        "couleur_du_trace": "rouge (la plus basse)",
        "points": [[19.0, 22.0], [23.5, 23.5]],
        "etiquettes_lues": ["19;22", "23.5;23.5"],
    },
    "refroidissement": {
        "couleur_du_trace": "bleu (la plus haute)",
        "points": [[12.0, 23.0], [17.0, 25.0]],
        "etiquettes_lues": ["12;23", "17;25"],
    },
}

RESERVES = [
    "La consigne est ABSENTE de la couche texte du PDF : elle n'existe que "
    "sous forme d'image. Une extraction textuelle conclut à tort qu'il n'y "
    "a pas de consigne.",
    "L'attribution chauffage/refroidissement est DÉDUITE de la position "
    "relative des courbes, faute de légende sur le graphique. Cohérente (la "
    "bande morte passe de 1,0 K à 1,5 K) mais non certifiée.",
    "Les quatre points viennent des étiquettes portées sur le tracé, pas "
    "d'une lecture de pixels. Entre deux points, l'interpolation linéaire "
    "est supposée d'après l'allure du tracé.",
    "Hors des bornes, les deux courbes sont horizontales — palier bas avant "
    "le premier point, palier haut après le second.",
]


def consigne(role, moyenne_48h):
    """Setpoint temperature for a given outdoor rolling mean.

    Args:
        role: `'chauffage'` ou `'refroidissement'`.
        moyenne_48h: 48-hour rolling mean of outdoor temperature, in
            degrees C.

    Returns:
        float: Consigne en °C.

    Raises:
        KeyError: If the role is unknown. Returning a default setpoint
            would put an unmeasured number into a validation chain.
    """
    points = CONSIGNES[role]["points"]
    (x1, y1), (x2, y2) = points[0], points[1]
    if moyenne_48h <= x1:
        return y1
    if moyenne_48h >= x2:
        return y2
    return y1 + (y2 - y1) * (moyenne_48h - x1) / (x2 - x1)


def construire():
    """The structure to freeze.

    Returns:
        dict: Reference ready to write. Its French strings are DATA: they
        are copied into `docs/FICHE-APACHEHVAC-TEST4.md`, a French document,
        so they stay French exactly as the `ui/i18n.py` table does.
    """
    return {
        "grandeur": "Consigne de température de l'air du local — Test SIA "
        "4010 n° 4 (Hörsaal)",
        "statut": "FIGÉ — lu sur le graphique de la spécification",
        "type": "consigne glissante sur la moyenne mobile 48 h de la "
        "température extérieure",
        "unite": "°C",
        "source": {
            "fichier": _SPEC,
            "emplacement": "ligne « Sollwerte / Raumlufttemperatur »",
            "image": _RECTANGLE_IMAGE,
            "pourquoi": "La cellule est VIDE dans la couche texte du PDF. "
            "La consigne n'existe que sous forme d'image.",
        },
        "abscisse": "Gleitender 48-h Mittelwert Aussenlufttemperatur, °C",
        "consignes": CONSIGNES,
        "reserves": RESERVES,
    }


def main(arguments):
    """Command-line entry point.

    Args:
        arguments: Arguments sans le nom du script.

    Returns:
        int: 0 when everything went well.
    """
    donnees = construire()
    for role in sorted(donnees["consignes"]):
        points = donnees["consignes"][role]["points"]
        print(
            "%-16s %s  (paliers hors bornes)"
            % (role, " -> ".join("%.1f °C ext = %.1f °C" % tuple(p) for p in points))
        )
    print()
    for exterieure in (-10.0, 12.0, 15.0, 19.0, 21.0, 30.0):
        print(
            "  ext %6.1f °C : chauffage %.2f  refroidissement %.2f"
            % (
                exterieure,
                consigne("chauffage", exterieure),
                consigne("refroidissement", exterieure),
            )
        )
    if "--ecrire" in arguments:
        with io.open(_SORTIE, "w", encoding="utf-8") as flux:
            flux.write(json.dumps(donnees, ensure_ascii=False, indent=1))
            flux.write("\n")
        print()
        print("written: %s" % os.path.relpath(_SORTIE, _RACINE))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
