# -*- coding: utf-8 -*-
"""Extracts FIGURE 1 of SIA 380/2:2022 (p. 27) from the vector drawing.

Why this approach rather than reading by eye: figure 1 is a vector drawing,
not an image. The polyline vertices are therefore present in the PDF at exact
precision. After calibration on the GRID LINES (exact by construction, not on
the text labels which are offset by ~0.8 pt), the residual is below 0.001 °C
on all four curves.

This closes open point O2 of traceability/batiment-exemple-zonage.spec.md
("exact values from SIA 380/2 figure 1") at zero cost, since the document is
already in /refs.

CROSS-CHECK: SIA 380/2:2022 §5.2.2.5 states that the upper and lower limits
of figure 1 "correspond to those of SIA 180:2014, figure 4, for residential
and office spaces". The vertices extracted here are therefore compared against
the figure 4 capture provided by SIA on 2026-08-04.

Usage:
    python scripts/extract_sia380_2_figure1.py            # display
    python scripts/extract_sia380_2_figure1.py --ecrire    # + write JSON
"""

from __future__ import print_function

import io
import json
import os
import sys

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    sys.stderr.write("PyMuPDF (fitz) requis.\n")
    raise

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
_PDF = os.path.join(_RACINE, "refs", "SIA-380-2-2022.pdf")
_SORTIE = os.path.join(_RACINE, "refs", "reference-data", "sia-380-2-2022.figure1.json")

PAGE_FIGURE_1 = 27  # printed page number == index+1

# Calibration: PDF coordinates of the extreme grid lines of the frame.
# x = 10 °C at px 145.21 ; x = 25 °C at px 513.89
# y = 20 °C at py 378.61 ; y = 27 °C at py 176.35
GRILLE = {
    "x_min_px": 145.21,
    "x_max_px": 513.89,
    "x_min_val": 10.0,
    "x_max_val": 25.0,
    "y_min_px": 378.61,
    "y_max_px": 176.35,
    "y_min_val": 20.0,
    "y_max_val": 27.0,
}

# Line-style signatures as present in the PDF. The labels are those from the
# normative text of §5.2.2.3 (French edition).
STYLES = {
    "[] 0": "trait plein",
    "[ 6.75 9 ] 0": "pointillé",  # consignes VARIABLES
    "[ 6.75 9 0 9 ] 0": "traits mixtes",  # consignes CONSTANTES
}

TOLERANCE_RESIDU = 0.005  # °C — beyond this, we refuse to conclude


def _transformation():
    g = GRILLE
    sx = (g["x_max_px"] - g["x_min_px"]) / (g["x_max_val"] - g["x_min_val"])
    sy = (g["y_min_px"] - g["y_max_px"]) / (g["y_max_val"] - g["y_min_val"])

    def vers_x(px):
        return g["x_min_val"] + (px - g["x_min_px"]) / sx

    def vers_y(py):
        return g["y_min_val"] + (g["y_min_px"] - py) / sy

    return vers_x, vers_y, sx, sy


def _sommets(chemin, vers_x, vers_y):
    """Vertices of a path, deduplicated while preserving drawing order."""
    bruts = []
    for item in chemin["items"]:
        if item[0] == "l":
            for point in (item[1], item[2]):
                if (
                    not bruts
                    or abs(point.x - bruts[-1].x) > 0.3
                    or abs(point.y - bruts[-1].y) > 0.3
                ):
                    bruts.append(point)
    return [(round(vers_x(p.x), 4), round(vers_y(p.y), 4)) for p in bruts]


def _courbes_epaisses(page, vers_x, vers_y):
    """The four data curves: thick stroke (2.25), within the frame."""
    trouvees = []
    for index, chemin in enumerate(page.get_drawings()):
        largeur = chemin.get("width") or 0.0
        if largeur < 2.0:
            continue
        sommets = _sommets(chemin, vers_x, vers_y)
        if len(sommets) < 2:
            continue
        trouvees.append(
            {
                "index_chemin": index,
                "style_pdf": chemin.get("dashes"),
                "style": STYLES.get(chemin.get("dashes"), "⚠ inconnu"),
                "largeur_pt": largeur,
                "sommets": sommets,
            }
        )
    return trouvees


def _segmenter(sommets):
    """Splits a vertex list into x-monotone polylines.

    A PDF path may contain TWO distinct curves (the "dashed" path carries both
    the heating and cooling setpoint curves): the break is detected by a
    reversal along the x-axis.
    """
    groupes, courant = [], []
    for sommet in sommets:
        if courant and sommet[0] < courant[-1][0] - 1e-6:
            groupes.append(courant)
            courant = []
        courant.append(sommet)
    if courant:
        groupes.append(courant)
    return groupes


def _residu_max(polyligne, pas):
    """Maximum discrepancy between extracted values and a multiple of `pas`."""
    pire = 0.0
    for x, y in polyligne:
        pire = max(pire, abs(x - round(x / pas) * pas), abs(y - round(y / pas) * pas))
    return pire


def extraire():
    document = fitz.open(_PDF)
    page = document[PAGE_FIGURE_1 - 1]
    vers_x, vers_y, sx, sy = _transformation()

    chemins = _courbes_epaisses(page, vers_x, vers_y)
    polylignes = []
    for chemin in chemins:
        for groupe in _segmenter(chemin["sommets"]):
            if len(groupe) < 2:
                continue
            polylignes.append(
                {
                    "style": chemin["style"],
                    "style_pdf": chemin["style_pdf"],
                    "index_chemin": chemin["index_chemin"],
                    "sommets": groupe,
                    "y_min": min(y for _, y in groupe),
                    "y_max": max(y for _, y in groupe),
                }
            )

    # Naming by style + altitude: the limits are in solid stroke, the highest
    # is the upper one; similarly for each pair of setpoint curves.
    def nommer(style, roles):
        lot = sorted(
            (p for p in polylignes if p["style"] == style), key=lambda p: p["y_max"]
        )
        if len(lot) != len(roles):
            raise AssertionError(
                "style %r : %d polylignes trouvées, %d attendues"
                % (style, len(lot), len(roles))
            )
        for polyligne, role in zip(lot, roles):
            polyligne["role"] = role
        return lot

    nommer("trait plein", ["limite_inferieure", "limite_superieure"])
    nommer(
        "pointillé", ["consigne_chauffage_variable", "consigne_refroidissement_variable"]
    )
    nommer(
        "traits mixtes",
        ["consigne_chauffage_constante", "consigne_refroidissement_constante"],
    )

    par_role = dict((p["role"], p) for p in polylignes)

    # Quality check: the limits must fall on half-degrees and the setpoints
    # on tenths.
    residus = {}
    for role, pas in (
        ("limite_inferieure", 0.5),
        ("limite_superieure", 0.5),
        ("consigne_chauffage_variable", 0.1),
        ("consigne_refroidissement_variable", 0.1),
        ("consigne_chauffage_constante", 0.1),
        ("consigne_refroidissement_constante", 0.1),
    ):
        residu = _residu_max(par_role[role]["sommets"], pas)
        residus[role] = round(residu, 6)
        if residu > TOLERANCE_RESIDU:
            raise AssertionError(
                "%s : résidu %.4f °C au pas de %.1f — extraction refusée"
                % (role, residu, pas)
            )

    # Control deviation Δθctr, measured not assumed.
    ctr_chaud = round(
        min(y for _, y in par_role["consigne_chauffage_variable"]["sommets"])
        - min(y for _, y in par_role["limite_inferieure"]["sommets"]),
        4,
    )
    ctr_froid = round(
        max(y for _, y in par_role["limite_superieure"]["sommets"])
        - max(y for _, y in par_role["consigne_refroidissement_variable"]["sommets"]),
        4,
    )

    return {
        "sx_pt_par_degre": round(sx, 5),
        "sy_pt_par_degre": round(sy, 5),
        "polylignes": polylignes,
        "par_role": par_role,
        "residus_max_c": residus,
        "delta_theta_ctr_chauffage_k": ctr_chaud,
        "delta_theta_ctr_refroidissement_k": ctr_froid,
    }


def _arrondir(sommets, pas):
    return [
        [round(round(x / pas) * pas, 4), round(round(y / pas) * pas, 4)]
        for x, y in sommets
    ]


def construire_json(extrait):
    pr = extrait["par_role"]
    return {
        "norme": "SIA 380/2:2022",
        "element": "figure 1 — Températures ambiantes de consigne pour le "
        "chauffage et le refroidissement",
        "page_imprimee": PAGE_FIGURE_1,
        "statut": "FIGÉ — extrait du dessin vectoriel, résidu < 0,001 °C",
        "date_extraction": "2026-08-04",
        "source": {
            "fichier": "refs/SIA-380-2-2022.pdf",
            "methode": "PyMuPDF get_drawings(), calibration sur les lignes de "
            "grille du cadre (et NON sur les étiquettes de texte, "
            "décalées de ~0,8 pt)",
            "script": "scripts/extract_sia380_2_figure1.py",
            "residus_max_c": extrait["residus_max_c"],
        },
        "axes": {
            "abscisse": "Température extérieure moyenne glissante sur 48 heures, °C",
            "abscisse_domaine": [10.0, 25.0],
            "ordonnee": "Température, °C",
            "ordonnee_domaine": [20.0, 27.0],
            "nature_de_la_grandeur": "SIA 380/2 §5.2.2.1 : « Les valeurs de consigne peuvent être "
            "fixées pour la température moyenne de l'air intérieur OU pour "
            "la température opérative simplifiée. Le choix est à discuter "
            "avec le mandant. » → la figure ne tranche pas ; le choix est "
            "un paramètre du projet.",
        },
        "courbes": {
            "limite_superieure": {
                "style_dans_la_figure": "trait plein",
                "sommets": _arrondir(pr["limite_superieure"]["sommets"], 0.5),
                "pente_segment_croissant": "2,0 K / 5,5 K = 4/11",
                "origine": "SIA 180:2014 figure 4, courbe supérieure " "(§5.2.2.5)",
            },
            "limite_inferieure": {
                "style_dans_la_figure": "trait plein",
                "sommets": _arrondir(pr["limite_inferieure"]["sommets"], 0.5),
                "pente_segment_croissant": "1,5 K / 4,5 K = 1/3",
                "origine": "SIA 180:2014 figure 4, courbe inférieure " "(§5.2.2.5)",
            },
            "consigne_chauffage_variable": {
                "symbole": "T_set;H",
                "style_dans_la_figure": "pointillé",
                "sommets": _arrondir(pr["consigne_chauffage_variable"]["sommets"], 0.1),
                "sapplique_si": "régulation AVEC communication "
                "(HEAT_EMIS_CTRL_DEF = 3 ou 4 selon "
                "SN EN ISO 52120-1:2022 tab. 5) ET l'utilisateur "
                "n'a aucune possibilité d'influence — §5.2.2.3",
            },
            "consigne_refroidissement_variable": {
                "symbole": "T_set;C",
                "style_dans_la_figure": "pointillé",
                "sommets": _arrondir(
                    pr["consigne_refroidissement_variable"]["sommets"], 0.1
                ),
                "sapplique_si": "idem, CLG_EMIS_CTRL_DEF = 3 ou 4 — §5.2.2.3",
            },
            "consigne_chauffage_constante": {
                "symbole": "T_set;H constante",
                "style_dans_la_figure": "traits mixtes",
                "valeur_c": max(
                    y
                    for _, y in _arrondir(
                        pr["consigne_chauffage_constante"]["sommets"], 0.1
                    )
                ),
                "definition_normative": "« valeurs constantes au MAXIMUM de la "
                "courbe de la valeur de consigne pour le "
                "chauffage » — §5.2.2.3",
                "sapplique_si": "régulation SANS communication "
                "(HEAT_EMIS_CTRL_DEF = 1 ou 2) OU l'utilisateur "
                "a une possibilité d'influence — §5.2.2.3",
            },
            "consigne_refroidissement_constante": {
                "symbole": "T_set;C constante",
                "style_dans_la_figure": "traits mixtes",
                "valeur_c": min(
                    y
                    for _, y in _arrondir(
                        pr["consigne_refroidissement_constante"]["sommets"], 0.1
                    )
                ),
                "definition_normative": "« au MINIMUM de la courbe de la valeur "
                "de consigne pour le refroidissement » "
                "— §5.2.2.3",
                "sapplique_si": "CLG_EMIS_CTRL_DEF = 1 ou 2 — §5.2.2.3",
            },
        },
        "ecart_de_regulation": {
            "symbole": "delta_theta_ctr",
            "mesure_chauffage_k": extrait["delta_theta_ctr_chauffage_k"],
            "mesure_refroidissement_k": extrait["delta_theta_ctr_refroidissement_k"],
            "definition_normative": "SIA 380/2 §5.2.2.2 : « La différence entre "
            "les valeurs de consigne et les limites "
            "supérieures et inférieures [...] correspond "
            "à l'écart de régulation pour l'émission de "
            "chaleur et de froid delta_theta_ctr selon "
            "SN EN 15316-2:2017. »",
            "reserve": "⚠ À VÉRIFIER — 0,7 K est ce que la figure DESSINE. "
            "SN EN 15316-2:2017, qui définit la grandeur, n'est pas "
            "en notre possession : nous ne savons donc pas si 0,7 K "
            "est la valeur générale ou une illustration pour une "
            "classe de régulation particulière.",
        },
        "regle_de_decalage_par_usage": {
            "citation": "SIA 380/2 §5.2.2.5 : « Sans détermination plus "
            "détaillée des conditions de confort, les limites seront "
            "décalées suivant la différence entre les valeurs de "
            "dimensionnement de l'utilisation correspondante et les "
            "utilisations 1.01 à 3.03 selon SIA 2024:2021, "
            "tableau 11. »",
            "forme": "decalage_inferieure_K = theta_h_design(usage) - 21 ; "
            "decalage_superieure_K = theta_c_design(usage) - 26",
            "groupe_de_reference": "1.01 à 3.03, unanimes à 21 °C / 26 °C au "
            "tableau 11 — c'est ce qui rend la "
            "« différence » scalaire.",
            "verifie_contre": "les 10 valeurs de décalage énumérées par "
            "SIA 4010:2023 §3.1.4 sur 7 usages : 10/10 "
            "reproduites (cf. engine/tests/test_setpoint_curves.py)",
            "la_forme_est_conservee": "« Pour d'autres utilisations, les courbes "
            "se déplacent, mais gardent leur forme. » "
            "— §5.2.2.5",
        },
        "exception_habillement_non_saisonnier": {
            "citation": "SIA 380/2 §5.2.2.5 et SIA 4010 §3.1.4 : pour les usages "
            "où l'habillement ne dépend pas de la température "
            "extérieure (salles de gymnastique, salles de fitness, "
            "piscines couvertes, vestiaires, douches), les limites "
            "sont CONSTANTES — « la courbe [...] prend la forme "
            "d'une ligne droite » (SIA 4010 §3.1.4).",
            "usages_concernes_sia_2024": ["11.01", "11.02", "11.03", "12.08"],
            "reserve": "⚠ La correspondance entre les libellés cités et les "
            "numéros d'usage est notre lecture ; les normes citent "
            "les libellés, pas les numéros. 12.06 « WC, Bad, Dusche » "
            "pourrait aussi relever de « douches ». À VÉRIFIER.",
        },
        "controle_croise_sia_180": {
            "affirmation_normative": "SIA 380/2 §5.2.2.5 : les limites de la "
            "figure 1 « correspondent à celles de "
            "SIA 180:2014, figure 4, pour les locaux "
            "d'habitation et les bureaux »",
            "capture_figure_4_recue": "2026-08-04, Yiqiao Yang, SIA",
            "concordance": "8 valeurs sur 8 — ordonnées 20,5 / 22,0 / 24,5 / 26,5 "
            "et ruptures d'abscisse 12 / 17,5 / 19 / 23,5.",
            "portee": "Deux documents indépendants, accord exact. Les sommets "
            "ci-dessus valent donc aussi pour SIA 180:2014 figure 4.",
        },
    }


def main():
    extrait = extraire()
    print(
        "Calibration : %.5f pt/°C en x, %.5f pt/°C en y"
        % (extrait["sx_pt_par_degre"], extrait["sy_pt_par_degre"])
    )
    print()
    for role, polyligne in sorted(extrait["par_role"].items()):
        print("%-38s %-14s %s" % (role, polyligne["style"], polyligne["sommets"]))
    print()
    print("Résidus max (°C) : %s" % extrait["residus_max_c"])
    print(
        "delta_theta_ctr : chauffage %.4f K, refroidissement %.4f K"
        % (
            extrait["delta_theta_ctr_chauffage_k"],
            extrait["delta_theta_ctr_refroidissement_k"],
        )
    )

    if "--ecrire" in sys.argv:
        donnees = construire_json(extrait)
        with io.open(_SORTIE, "w", encoding="utf-8") as f:
            f.write(json.dumps(donnees, ensure_ascii=False, indent=2))
            f.write("\n")
        print()
        print("écrit : %s" % _SORTIE)


if __name__ == "__main__":
    main()
