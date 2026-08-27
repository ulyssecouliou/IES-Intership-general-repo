# -*- coding: utf-8 -*-
"""Freezes in JSON the reference data transmitted by SIA on 2026-08-04.

SOURCES (screenshots provided by Yiqiao Yang, SIA, 2026-08-04):
  - SIA 2024:2021, tableau 11 (p. 54-55) — design values
  - SIA 2024:2021, annex B (normative), tableau 13 (p. 58-59)
  - SIA 180:2014, chiffre 2.3.1 — comfort requirements
  - SIA 180:2014, chiffre 2.3.2 and figure 4 — perceived-temperature range
  - SIA 387/4:2017, tableau 9 and chiffre 3.4.3.5 — slat blind control

These screenshots « reflect the originally published versions and may not
include subsequent corrigenda » (Yiqiao Yang, 2026-08-04). Corrigenda
DO EXIST for SIA 2024 and SIA 180 → see the `corrigenda` field of each
produced file. **No value in this script is confirmed post-corrigendum.**

The script does not merely copy: it VERIFIES the setpoint-curve offset rule
of SIA 380/2:2022 §5.2.2.5 against the seven offsets enumerated by
SIA 4010:2023 §3.1.4. If any one fails to reproduce, it exits with an error.
"""

from __future__ import print_function

import io
import json
import os

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
_SORTIE = os.path.join(_RACINE, "refs", "reference-data")

# --------------------------------------------------------------------------
# SIA 2024:2021, tableau 11 — « Auslegungswerte für Heizungs-, Kälte- und
# lufttechnische Anlagen », p. 54-55.
#
# Columns, in table order:
#   0 theta_h  Raumtemperatur-Auslegungswert, Heizfall (Auslegung Norm-Heizlast), °C
#   1 theta_c  Raumtemperatur-Auslegungswert, Kühlfall (Auslegung Klimakälteleistung), °C
#   2 hr_h     Relative Raumluftfeuchte, Heizfall (Auslegung Befeuchtung), %
#   3 hr_c     Relative Raumluftfeuchte, Kühlfall (Auslegung Entfeuchtung), %
#   4 va_hyg   Hygienebedingter Aussenluft-Volumenstrom, m3/h per person (day)
#   5 va_nuit  idem, reduced-flow night operation (value in parentheses)
#   6 va_proc  Prozessbedingter Aussenluft-Volumenstrom, m3/(h.m2)
#   7 notes    table footnote references
#
# `None` = « – » (nicht relevant) in the table.
# --------------------------------------------------------------------------
TABLEAU_11 = [
    ("1.01", "Wohnen MFH", 21, 26, 30, 60, 29, 15, None, [1, 2]),
    ("1.02", "Wohnen EFH", 21, 26, 30, 60, 29, 15, None, [1, 2]),
    ("2.01", "Hotelzimmer", 21, 26, 30, 60, 29, 15, None, [1]),
    ("2.02", "Empfang, Lobby", 21, 26, 30, 60, 29, None, None, []),
    ("3.01", "Einzel-, Gruppenbüro", 21, 26, 30, 60, 29, None, None, []),
    ("3.02", "Grossraumbüro", 21, 26, 30, 60, 29, None, None, []),
    ("3.03", "Sitzungszimmer", 21, 26, 30, 60, 29, None, None, []),
    ("3.04", "Schalterhalle, Empfang", 20, 26, 30, 60, 29, None, None, []),
    ("4.01", "Schulzimmer", 21, 26, 30, 60, 29, None, None, []),
    ("4.02", "Lehrerzimmer, Aufenthaltsraum", 21, 26, 30, 60, 29, None, None, []),
    ("4.03", "Bibliothek", 21, 26, 30, 60, 29, None, None, []),
    ("4.04", "Hörsaal", 21, 26, 30, 60, 29, None, None, []),
    ("4.05", "Schulfachraum", 21, 26, 30, 60, 29, None, None, []),
    ("5.01", "Lebensmittelverkauf", 20, 26, 30, 60, 29, None, None, []),
    ("5.02", "Fachgeschäft", 20, 26, 30, 60, 29, None, None, []),
    ("5.03", "Verkauf Möbel, Bau, Garten", 20, 26, 30, 60, 29, None, None, []),
    ("6.01", "Restaurant", 21, 26, 30, 70, 29, None, None, []),
    ("6.02", "Selbstbedienungsrestaurant", 21, 26, 30, 70, 29, None, None, []),
    ("6.03", "Küche zu 6.1", 20, 28, None, None, 48, None, 80, [3]),
    ("6.04", "Küche zu 6.2", 20, 28, None, None, 48, None, 80, [3]),
    ("7.01", "Vorstellungsraum", 21, 26, 30, 60, 29, None, None, []),
    ("7.02", "Mehrzweckhalle", 21, 26, 30, 60, 29, None, None, []),
    ("7.03", "Ausstellungshalle", 21, 26, 30, 60, 29, None, None, []),
    ("8.01", "Bettenzimmer", 22, 26, 30, 60, 29, None, None, []),
    ("8.02", "Stationszimmer", 21, 26, 30, 60, 29, None, None, []),
    ("8.03", "Behandlungsraum", 22, 26, 30, 60, 29, None, None, []),
    ("9.01", "Produktion (grobe Arbeit)", 18, 30, 30, 70, 48, None, 10, []),
    ("9.02", "Produktion (feine Arbeit)", 21, 26, 30, 70, 29, None, 5, []),
    ("9.03", "Laborraum", 21, 26, 30, 70, 29, None, 12, []),
    ("10.01", "Lagerraum", 18, None, 30, 70, 29, None, None, []),
    ("11.01", "Turnhalle", 18, None, 30, 70, 73, None, None, []),
    ("11.02", "Fitnessraum", 21, 26, 30, 70, 73, None, None, []),
    ("11.03", "Schwimmhalle", 24, None, 55, 65, 29, None, 20, [4, 5]),
    ("12.01", "Verkehrsfläche", 21, None, None, None, None, None, None, []),
    ("12.02", "Verkehrsfläche 24 h", 21, 26, None, None, None, None, None, []),
    ("12.03", "Treppenhaus", 18, None, None, None, None, None, None, []),
    ("12.04", "Nebenraum", 18, None, None, None, None, None, None, []),
    ("12.05", "Küche, Teeküche", 21, None, None, None, 29, None, None, []),
    ("12.06", "WC, Bad, Dusche", 21, None, None, None, None, None, None, [6]),
    ("12.07", "WC", 21, None, None, None, None, None, None, []),
    ("12.08", "Garderobe, Dusche", 21, None, None, None, None, None, None, [6]),
    ("12.09", "Parkhaus", None, None, None, None, None, None, 2, [8]),
    ("12.10", "Wasch- und Trockenraum", None, None, None, None, None, None, None, []),
    ("12.11", "Kühlraum", None, None, None, None, None, None, None, []),
    ("12.12", "Serverraum", None, 26, None, None, None, None, None, []),
]

NOTES_TABLEAU_11 = {
    1: "Angabe gilt für Tagbetrieb; Angabe in Klammern gilt für den Nachtbetrieb "
    "mit reduziertem Aussenluft-Volumenstrom",
    2: "Massgebend für die Auslegung raumlufttechnischer Anlagen in Wohngebäuden "
    "ist SIA 382/5",
    3: "Massgebend für die Auslegung raumlufttechnischer Anlagen in "
    "Gastwirtschaftsbetrieben ist SWKI VA102-01:2009",
    4: "Mindestens Wassertemperatur, maximal 32 °C",
    5: "Massgebend für die Auslegung raumlufttechnischer Anlagen in Hallenbädern "
    "ist SWKI 2004-1:2005",
    6: "Die Angabe gilt, sofern die angrenzende Hauptnutzung keine höheren "
    "Raumtemperaturen für die Auslegung der Heizsysteme vorschreibt",
    7: "Entspricht der Kategorie der Raumluftqualität II; «unterstützende "
    "Fensterlüftung» bedeutet, dass bei Bedarf der Aussenluft-Volumenstrom über "
    "eine Lüftungsöffnung kurzzeitig erhöht werden kann",
    8: "Massgebend für die Auslegung von Lüftungsanlagen in Parkhäusern ist "
    "SWKI VA103-01:2017",
}

# --------------------------------------------------------------------------
# SIA 2024:2021, annex B (NORMATIVE), tableau 13 — « Mittlere Raumtemperaturen
# für die Berechnung des jährlichen Klimakälte- und Heizwärmebedarfs », p. 58-59.
# (usage, theta_h_moy, theta_c_moy)
# --------------------------------------------------------------------------
TABLEAU_13 = [
    ("1.01", 22, 25),
    ("1.02", 22, 25),
    ("2.01", 22, 25),
    ("2.02", 22, 25),
    ("3.01", 22, 25),
    ("3.02", 22, 25),
    ("3.03", 22, 25),
    ("3.04", 22, 25),
    ("4.01", 22, 25),
    ("4.02", 22, 25),
    ("4.03", 22, 25),
    ("4.04", 22, 25),
    ("4.05", 22, 25),
    ("5.01", 22, 25),
    ("5.02", 22, 25),
    ("5.03", 22, 25),
    ("6.01", 22, 25),
    ("6.02", 22, 25),
    ("6.03", 22, 25),
    ("6.04", 22, 25),
    ("7.01", 22, 25),
    ("7.02", 22, 25),
    ("7.03", 22, 25),
    ("8.01", 22, 25),
    ("8.02", 22, 25),
    ("8.03", 22, 25),
    ("9.01", 20, 25),
    ("9.02", 20, 25),
    ("9.03", 20, 25),
    ("10.01", 18, None),
    ("11.01", 18, None),
    ("11.02", 22, 25),
    ("11.03", 28, None),
    ("12.01", 22, None),
    ("12.02", 22, 25),
    ("12.03", 20, None),
    ("12.04", 20, None),
    ("12.05", 22, None),
    ("12.06", 22, None),
    ("12.07", 22, None),
    ("12.08", 22, None),
    ("12.09", None, None),
    ("12.10", None, None),
    ("12.11", None, None),
    ("12.12", None, 25),
]

# --------------------------------------------------------------------------
# CHECK — the offset rule of SIA 380/2:2022 §5.2.2.5:
#   « the limits shall be offset by the difference between the design values
#     of the corresponding usage and usages 1.01 to 3.03 per SIA 2024:2021,
#     tableau 11 »
# compared against the seven EXPLICIT offsets of SIA 4010:2023 §3.1.4 (p. 10).
# --------------------------------------------------------------------------
GROUPE_REFERENCE = ["1.01", "1.02", "2.01", "2.02", "3.01", "3.02", "3.03"]

# (usage, expected offset of the LOWER curve, downwards, in K)
DECALAGES_4010_INFERIEURE = [
    ("3.04", 1),
    ("5.01", 1),
    ("5.02", 1),
    ("5.03", 1),
    ("6.03", 1),
    ("6.04", 1),
    ("9.01", 3),
]
# (usage, expected offset of the UPPER curve, upwards, in K)
DECALAGES_4010_SUPERIEURE = [
    ("6.03", 2),
    ("6.04", 2),
    ("9.01", 4),
]


def _par_usage():
    """Index the SIA 2024 design-value rows by usage code."""

    return dict((row[0], row) for row in TABLEAU_11)


def verifier_regle_de_decalage():
    """Reproduces the seven offsets of SIA 4010 §3.1.4 from tableau 11.

    Raises `AssertionError` on the first discrepancy: this check is the only
    proof that our transcription of tableau 11 is correct AND that our reading
    of rule §5.2.2.5 is correct.
    """
    t11 = _par_usage()

    # The reference group must be unanimous, otherwise "the difference from
    # usages 1.01 to 3.03" would not make sense as a scalar.
    th = set(t11[u][2] for u in GROUPE_REFERENCE)
    tc = set(t11[u][3] for u in GROUPE_REFERENCE)
    assert th == set([21]), "groupe de référence non unanime en chauffage : %r" % th
    assert tc == set([26]), "groupe de référence non unanime en refroidissement : %r" % tc
    ref_h, ref_c = 21, 26

    controles = []
    for usage, attendu in DECALAGES_4010_INFERIEURE:
        calcule = ref_h - t11[usage][2]
        assert calcule == attendu, (
            "décalage inférieur %s : SIA 4010 annonce %d K, "
            "le tableau 11 donne %d K" % (usage, attendu, calcule)
        )
        controles.append(("inférieure", usage, attendu, calcule))

    for usage, attendu in DECALAGES_4010_SUPERIEURE:
        calcule = t11[usage][3] - ref_c
        assert calcule == attendu, (
            "décalage supérieur %s : SIA 4010 annonce %d K, "
            "le tableau 11 donne %d K" % (usage, attendu, calcule)
        )
        controles.append(("supérieure", usage, attendu, calcule))

    return controles


def construire_sia2024():
    """Build the source-traced SIA 2024 reference payload."""

    lignes_11 = []
    for usage, libelle, th, tc, hrh, hrc, vah, van, vap, notes in TABLEAU_11:
        lignes_11.append(
            {
                "usage": usage,
                "libelle_de": libelle,
                "theta_h_design_c": th,
                "theta_c_design_c": tc,
                "humidite_relative_h_pct": hrh,
                "humidite_relative_c_pct": hrc,
                "air_neuf_hygiene_m3_h_pers": vah,
                "air_neuf_hygiene_nuit_m3_h_pers": van,
                "air_neuf_process_m3_h_m2": vap,
                "renvois": notes,
            }
        )
    lignes_13 = [
        {"usage": u, "theta_h_moyenne_c": h, "theta_c_moyenne_c": c}
        for (u, h, c) in TABLEAU_13
    ]

    return {
        "norme": "SIA 2024:2021",
        "titre": "Données d'utilisation des locaux pour l'énergie et les "
        "installations du bâtiment",
        "statut": "FIGÉ — sous réserve des rectificatifs (cf. corrigenda)",
        "date_extraction": "2026-08-04",
        "source": {
            "nature": "captures d'écran des pages du document publié",
            "fournisseur": "Yiqiao Yang, SIA",
            "date_reception": "2026-08-04",
            "pages": [54, 55, 58, 59],
            "reserve_du_fournisseur": "« they reflect the originally published versions of the "
            "standards/merkblätter and may not include any subsequent "
            "corrigenda »",
        },
        "corrigenda": {
            "existent": True,
            "source_declaree": "Yiqiao Yang, SIA, 2026-08-04 : "
            "« corrigenda are available for SIA 2024 and SIA 180 »",
            "gratuits": True,
            "ou": "SIA Shop",
            "controle_effectue": False,
            "consequence": "⚠ À VÉRIFIER — aucune valeur de ce fichier n'est "
            "confirmée post-rectificatif.",
        },
        "tableau_11": {
            "titre_de": "Auslegungswerte für Heizungs-, Kälte- und "
            "lufttechnische Anlagen",
            "pages": [54, 55],
            "niveau_de_valeur": {
                "distingue_standard_ziel_grenz": False,
                "constat": "Le tableau 11 ne comporte QU'UNE colonne par "
                "grandeur : aucune distinction Standardwert / "
                "Zielwert / Grenzwert. La température ambiante de "
                "dimensionnement ne dépend donc PAS du niveau de "
                "valeur demandé par une spécification de test.",
                "portee": "Ferme la seconde moitié du point ouvert O1 de "
                "traceability/batiment-exemple-zonage.spec.md §8.3.",
            },
            "unites": {
                "theta_h_design_c": "°C — Auslegung Norm-Heizlast",
                "theta_c_design_c": "°C — Auslegung Klimakälteleistung",
                "humidite_relative_h_pct": "% — Auslegung Befeuchtung",
                "humidite_relative_c_pct": "% — Auslegung Entfeuchtung",
                "air_neuf_hygiene_m3_h_pers": "m3/h par personne, exploitation de jour",
                "air_neuf_hygiene_nuit_m3_h_pers": "m3/h par personne, exploitation de nuit à débit réduit "
                "(valeur entre parenthèses au tableau) — renvoi 1",
                "air_neuf_process_m3_h_m2": "m3/(h.m2)",
            },
            "convention_null": "null = « – » (nicht relevant) au tableau",
            "renvois": dict((str(k), v) for k, v in NOTES_TABLEAU_11.items()),
            "lignes": lignes_11,
        },
        "tableau_13": {
            "titre_de": "Mittlere Raumtemperaturen für die Berechnung des "
            "jährlichen Klimakälte- und Heizwärmebedarfs gemäss SIA 2024",
            "annexe": "B (normative)",
            "pages": [58, 59],
            "avertissement_de_lannexe": "« Die angegebenen mittleren Raumtemperaturen gelten nur in "
            "SIA 2024 und sind für andere Normen, insbesondere für "
            "SIA 380/1, nicht massgebend. »",
            "lecture_de_lavertissement": "L'exclusion nomme SIA 380/**1**, pas SIA 380/2. Et SIA 380/2:2022 "
            "§5.2.2.6 autorise EXPLICITEMENT cette voie simplifiée « surtout "
            "dans les phases de planification précoce ». Pas de contradiction : "
            "pour SIA 380/2 la voie normale reste la figure 1.",
            "convention_null": "null = « – » (nicht relevant) au tableau",
            "lignes": lignes_13,
        },
        "usages_requis_par_les_tests_sia_4010": {
            "commentaire": "Usages cités par les spécifications des tests 4, 5 et 6 "
            "et par la documentation du bâtiment exemple.",
            "test_4": ["4.04"],
            "test_5": ["3.01", "3.02", "3.03"],
            "test_6": ["6.02", "6.04"],
        },
        "ce_qui_reste_manquant": [
            "Les FICHES D'UTILISATION (Merkblatt-Nutzungsdaten) 3.1, 3.2, 3.3, "
            "4.4, 6.2, 6.4 : apports internes (personnes, appareils, éclairage), "
            "horaires, simultanéités, surface par personne. NON contenues dans "
            "les tableaux 11 et 13. Disponibles GRATUITEMENT en ligne — cf. "
            "champ `fiches_utilisation_en_ligne`.",
            "Les niveaux Standardwert / Zielwert / Grenzwert de ces fiches "
            "(le test 4 demande les Zielwerte, les tests 5 et 6 les Standardwerte).",
        ],
        "fiches_utilisation_en_ligne": {
            "url": "https://www.sia.ch/de/cms/dienstleistungen/"
            "normenundordnungen?item=15143#15152",
            "gratuit": True,
            "source": "Yiqiao Yang, SIA, 2026-08-04",
            "note_du_fournisseur": "« The data sheet is updated and includes all changes regarding "
            "data sheet in the two corrigenda of SIA 2024. » → la version en "
            "ligne des FICHES est post-rectificatif ; les tableaux 11 et 13 "
            "ci-dessus ne le sont pas.",
            "telecharge": False,
        },
    }


# SIA 180:2014 figure 3 -- adaptive comfort band for rooms with NATURAL
# ventilation while neither heated nor cooled, vs the 48 h running mean of the
# outdoor temperature (theta_rm). Read from the published figure 3 provided by
# Yiqiao Yang (SIA) on 2026-08-20. The two limit lines carry their own equations
# on the chart: upper 0.33*theta_rm + 21.8, lower 0.33*theta_rm + 14.3, with an
# upper floor (25.0 degC), a lower floor (20.5 degC) and a lower cap (22.0 degC).
FIG3_PENTE = 0.33
FIG3_SUP_OFFSET = 21.8
FIG3_INF_OFFSET = 14.3
FIG3_SUP_PLANCHER = 25.0
FIG3_INF_PLANCHER = 20.5
FIG3_INF_PLAFOND = 22.0


def _figure3_limites(theta_rm):
    """Return (lower, upper) figure-3 comfort limits at one theta_rm."""
    upper = max(FIG3_SUP_PLANCHER, FIG3_PENTE * theta_rm + FIG3_SUP_OFFSET)
    lower = min(
        FIG3_INF_PLAFOND,
        max(FIG3_INF_PLANCHER, FIG3_PENTE * theta_rm + FIG3_INF_OFFSET),
    )
    return lower, upper


def verifier_figure_3():
    """Recompute the figure-3 break points and confront the graph's key points.

    Raises AssertionError on the first discrepancy: the only proof that the
    transcribed equations and plateaus reproduce the published figure 3.
    """
    rupture_sup = (FIG3_SUP_PLANCHER - FIG3_SUP_OFFSET) / FIG3_PENTE
    rupture_inf_bas = (FIG3_INF_PLANCHER - FIG3_INF_OFFSET) / FIG3_PENTE
    rupture_inf_haut = (FIG3_INF_PLAFOND - FIG3_INF_OFFSET) / FIG3_PENTE
    # (theta_rm, lower_expected, upper_expected) read on the published chart.
    controles = [
        (5, 20.5, 25.0),
        (10, 20.5, 25.1),
        (19, 20.57, 28.07),
        (23.33, 22.0, 29.5),
        (27, 22.0, 30.71),
    ]
    for theta, lo_att, up_att in controles:
        lo, up = _figure3_limites(theta)
        assert (
            abs(lo - lo_att) < 0.15
        ), "figure 3 limite inférieure à theta_rm=%s : %.2f attendu %.2f" % (
            theta,
            lo,
            lo_att,
        )
        assert (
            abs(up - up_att) < 0.15
        ), "figure 3 limite supérieure à theta_rm=%s : %.2f attendu %.2f" % (
            theta,
            up,
            up_att,
        )
    return {
        "rupture_superieure_theta_rm_C": round(rupture_sup, 2),
        "rupture_inferieure_basse_theta_rm_C": round(rupture_inf_bas, 2),
        "rupture_inferieure_haute_theta_rm_C": round(rupture_inf_haut, 2),
    }


def construire_sia180():
    """Build the source-traced SIA 180 reference payload."""
    ruptures = verifier_figure_3()

    return {
        "norme": "SIA 180:2014",
        "titre": "Protection thermique, protection contre l'humidité et climat "
        "intérieur dans les bâtiments",
        "statut": "FIGÉ — sous réserve des rectificatifs",
        "date_extraction": "2026-08-04",
        "source": {
            "nature": "captures d'écran du document publié",
            "fournisseur": "Yiqiao Yang, SIA",
            "date_reception": "2026-08-04",
            "chiffres": ["2.3.1", "2.3.2 (avec figure 4)"],
            "complement": "Figure 3 fournie par Yiqiao Yang (SIA) le 2026-08-20 "
            "(sans rectificatif applicable).",
        },
        "corrigenda": {
            "existent": True,
            "source_declaree": "Yiqiao Yang, SIA, 2026-08-04",
            "gratuits": True,
            "ou": "SIA Shop",
            "controle_effectue": False,
        },
        "chiffre_2_3_1": {
            "titre_de": "Anforderungen an Räume, während diese beheizt, "
            "gekühlt oder mechanisch belüftet sind — Allgemein",
            "renvoi": "Ces conditions correspondent pour l'essentiel à la "
            "CATÉGORIE B de SN EN ISO 7730, annexe A.",
            "portee": "À respecter pendant TOUTE la durée d'utilisation "
            "(« während der ganzen Nutzungszeit »).",
            "criteres": [
                {
                    "grandeur": "PPD",
                    "libelle_de": "erwarteter Anteil mit der thermischen "
                    "Behaglichkeit unzufriedener Personen",
                    "operateur": "<",
                    "valeur": 10,
                    "unite": "%",
                },
                {
                    "grandeur": "PMV",
                    "libelle_de": "erwartete durchschnittliche Bewertung der "
                    "thermischen Behaglichkeit",
                    "operateur": "dans",
                    "valeur": [-0.5, 0.5],
                    "unite": "-",
                },
                {
                    "grandeur": "insatisfaits_courant_dair_ventilation_naturelle",
                    "libelle_de": "prozentualer Anteil zusätzlicher Unzufriedener "
                    "wegen Zugluft, natürliche Lüftung",
                    "operateur": "<",
                    "valeur": 20,
                    "unite": "%",
                },
                {
                    "grandeur": "insatisfaits_courant_dair_ventilation_mecanique",
                    "libelle_de": "prozentualer Anteil zusätzlicher Unzufriedener "
                    "wegen Zugluft, mechanische Lüftung",
                    "operateur": "<",
                    "valeur": 15,
                    "unite": "%",
                },
                {
                    "grandeur": "insatisfaits_gradient_tete_chevilles",
                    "libelle_de": "prozentualer Anteil zusätzlicher Unzufriedener "
                    "wegen Temperaturdifferenz zwischen Kopf und Knöcheln",
                    "operateur": "<",
                    "valeur": 5,
                    "unite": "%",
                },
                {
                    "grandeur": "insatisfaits_temperature_du_sol",
                    "libelle_de": "prozentualer Anteil zusätzlicher Unzufriedener "
                    "wegen Fussbodentemperatur",
                    "operateur": "<",
                    "valeur": 10,
                    "unite": "%",
                },
                {
                    "grandeur": "insatisfaits_asymetrie_de_rayonnement",
                    "libelle_de": "prozentualer Anteil zusätzlicher Unzufriedener "
                    "wegen Asymmetrie der Strahlungstemperatur",
                    "operateur": "<",
                    "valeur": 5,
                    "unite": "%",
                },
            ],
        },
        "chiffre_2_3_2_figure_4": {
            "titre_de": "Zulässiger Bereich der empfundenen Temperatur in Wohn- "
            "und Büroräumen, während diese beheizt, gekühlt oder "
            "mechanisch belüftet sind, je nach gleitendem Mittelwert "
            "der Aussentemperatur",
            "grandeur_ordonnee": "empfundene Temperatur (température ressentie), °C",
            "grandeur_abscisse": "gleitender Mittelwert der Aussentemperatur über "
            "48 Stunden, °C",
            "condition_prealable": "Avec la variation saisonnière de l'habillement "
            "selon la figure 2 (§2.3.2).",
            "domaine_dapplication": "locaux d'habitation et bureaux "
            "(Wohn- und Büroräume)",
            "identite_avec_sia_380_2": {
                "etablie": True,
                "citation": "SIA 380/2:2022 §5.2.2.5 : « La limite supérieure et "
                "la limite inférieure de la figure 1 découlent des "
                "exigences de SIA 180:2014, chiffre 2.3.1. Elles "
                "CORRESPONDENT À CELLES DE SIA 180:2014, FIGURE 4, "
                "pour les locaux d'habitation et les bureaux. »",
                "consequence": "Les sommets ci-dessous ne sont PAS lus à l'œil sur "
                "la capture : ils sont extraits du dessin VECTORIEL "
                "de la figure 1 de refs/SIA-380-2-2022.pdf p. 27 "
                "(résidu < 0,001 °C), puis confrontés à la capture "
                "de la figure 4. Concordance sur les 8 valeurs.",
                "fichier": "sia-380-2-2022.figure1.json",
            },
        },
        "chiffre_2_3_3_figure_3": {
            "titre_de": "Zulässiger Bereich der empfundenen Temperatur in Räumen "
            "mit natürlicher Lüftung, während diese weder beheizt noch "
            "gekühlt sind, je nach dem gleitenden Mittelwert der "
            "Aussentemperatur",
            "grandeur_ordonnee": "empfundene Temperatur (température ressentie), °C",
            "grandeur_abscisse": "gleitender Mittelwert der Aussentemperatur über "
            "48 Stunden (θrm), °C",
            "domaine_dapplication": "locaux à ventilation naturelle, ni chauffés "
            "ni refroidis (modèle de confort adaptatif)",
            "source": {
                "nature": "capture d'écran du document publié",
                "fournisseur": "Yiqiao Yang, SIA",
                "date_reception": "2026-08-20",
                "rectificatif_applicable": False,
            },
            "axes": {
                "abscisse_theta_rm_C": [5, 27],
                "ordonnee_C": [20, 31],
            },
            "limite_superieure": {
                "equation_tracee": "0,33·θrm + 21,8",
                "pente": FIG3_PENTE,
                "ordonnee_origine_C": FIG3_SUP_OFFSET,
                "plancher_plateau_C": FIG3_SUP_PLANCHER,
                "formule_effective": "max(25.0, 0.33*theta_rm + 21.8)",
                "point_de_rupture_theta_rm_C": ruptures["rupture_superieure_theta_rm_C"],
            },
            "limite_inferieure": {
                "equation_tracee": "0,33·θrm + 14,3",
                "pente": FIG3_PENTE,
                "ordonnee_origine_C": FIG3_INF_OFFSET,
                "plancher_plateau_C": FIG3_INF_PLANCHER,
                "plafond_plateau_C": FIG3_INF_PLAFOND,
                "formule_effective": "min(22.0, max(20.5, 0.33*theta_rm + 14.3))",
                "point_de_rupture_bas_theta_rm_C": ruptures[
                    "rupture_inferieure_basse_theta_rm_C"
                ],
                "point_de_rupture_haut_theta_rm_C": ruptures[
                    "rupture_inferieure_haute_theta_rm_C"
                ],
            },
            "controle_croise": {
                "methode": "points de rupture recalculés depuis les "
                "intersections plateau/pente et valeurs confrontées "
                "à la figure 3 publiée (verifier_figure_3).",
                "exemples_theta_rm_inf_sup": {
                    "5": list(_figure3_limites(5)),
                    "19": [round(v, 2) for v in _figure3_limites(19)],
                    "27": [round(v, 2) for v in _figure3_limites(27)],
                },
            },
            "distinction_figure_4": "Figure 3 (ventilation naturelle, ni chauffé "
            "ni refroidi = modèle adaptatif) ≠ figure 4 "
            "(chauffé/refroidi/ventilé mécaniquement). Ne "
            "pas confondre : la figure 4 est celle "
            "reprise par SIA 380/2 figure 1.",
        },
    }


def construire_sia387_4():
    """Build the source-traced SIA 387/4 solar-control payload."""

    return {
        "norme": "SIA 387/4:2023",
        "titre": "Éclairage — Calcul et exigences (partie protection solaire)",
        "statut": "FIGÉ — tableau 9 et équations 18-20 confirmés sur l'édition "
        "2023 (réserve d'édition levée le 2026-08-21).",
        "date_extraction": "2026-08-04",
        "source": {
            "nature": "captures d'écran du document publié",
            "fournisseur": "Yiqiao Yang, SIA",
            "date_reception": "2026-08-04",
            "elements": ["chiffre 3.4.3.5", "tableau 9"],
            "complement_2023": {
                "date_reception": "2026-08-21",
                "elements": ["chiffre 3.4.3.7", "tableau 9 (équations 18, 19, 20)"],
                "note": "Capture SIA 387/4:2023 fournie par Yiqiao Yang : "
                "confirme verbatim les formules encodées ci-dessous.",
            },
        },
        "reserve_dedition": {
            "edition_recue": "SIA 387/4:2017 puis SIA 387/4:2023 (tableau 9)",
            "edition_citee_par_les_normes": "SIA 387/4:2023",
            "citation": "SIA 4010:2023 §3.1.5 (p. 10) : « les commandes de "
            "protection solaire de type X = 1 ou 2 selon le "
            "tableau 9 de SIA 387/4:2023 »",
            "indice_de_stabilite": "La TYPOLOGIE X = 1 / 2 / 3, le NUMÉRO de "
            "tableau (9) ET les équations (18)(19)(20) "
            "concordent entre l'encodage et la capture "
            "SIA 387/4:2023 reçue.",
            "statut": "✅ LEVÉE le 2026-08-21 — équations (18), (19), (20) de "
            "l'édition 2023 reçues et identiques aux formules encodées.",
        },
        "chiffre_3_4_3_7": {
            "enonce_de": "Der Lamellen-Anstellwinkel in (16) und (17) wird für "
            "die drei Funktionstypen der Sonnenschutzsteuerung "
            "gemäss Tabelle 9 berechnet.",
            "renvoi": "introduit le tableau 9 (angle β utilisé dans les "
            "équations (16) et (17)).",
        },
        "tableau_9": {
            "titre_de": "Berechnung des Lamellen-Anstellwinkels für die drei "
            "Funktionstypen der Sonnenschutzsteuerung",
            "grandeur_calculee": "beta — Lamellen-Anstellwinkel (angle "
            "d'inclinaison des lamelles), en degrés",
            "symbole_hauteur_solaire": "delta_s_n — hauteur solaire",
            "types": [
                {
                    "x": 1,
                    "type_sia_411": 1,
                    "libelle_de": "Motorbetrieben mit manueller Betätigung",
                    "description_de": "Die Lamellen gehen in Arbeitsposition 45° "
                    "und werden mehr geschlossen, wenn "
                    "Direktstrahlung eindringen würde. Sie werden "
                    "nicht mehr zurückgestellt, wenn sie mehr "
                    "geschlossen sind.",
                    "equation_numero": 18,
                    "formule": "beta = max(45 ; 90 - 2*delta_s_n ; beta_{h-1})",
                    "a_memoire": True,
                    "symbole_memoire": "beta_{h-1} = Lamellen-Anstellwinkel der "
                    "vorangehenden Stunde",
                },
                {
                    "x": 2,
                    "type_sia_411": 2,
                    "libelle_de": "Motorbetrieben mit automatischer Steuerung "
                    "(mit oder ohne Berücksichtigung der Verschattung)",
                    "description_de": "Die Lamellen gehen in Arbeitsposition 45° "
                    "und werden mehr geschlossen, wenn "
                    "Direktstrahlung eindringen würde.",
                    "equation_numero": 19,
                    "formule": "beta = max(45 ; 90 - 2*delta_s_n)",
                    "a_memoire": False,
                },
                {
                    "x": 3,
                    "type_sia_411": 3,
                    "libelle_de": "Motorbetrieben mit automatischer Steuerung "
                    "und Lamellennachführung",
                    "description_de": "Die Lamellen gehen in die optimale Position, "
                    "so dass keine Direktstrahlung eindringt.",
                    "equation_numero": 20,
                    "formule": "beta = max(0 ; min(90 ; 90 - 2*delta_s_n))",
                    "a_memoire": False,
                },
            ],
        },
        "chiffre_3_4_3_5": {
            "enonce_de": "Bei Lamellenstoren sind tau_v_sp_B = tau_v_B_45, "
            "rho_v_sp_B = rho_v_B_45 sowie tau_v_sp_D = tau_v_D_45 "
            "und rho_v_sp_D = rho_v_B_D einzusetzen.",
            "symboles": {
                "tau_v_B_45": "Lichttransmissionsgrad des Sonnenschutzes für "
                "direkte Strahlung in Arbeitsstellung (45°) bei "
                "Sonnenhöhe 45° gemäss SN EN 14500",
                "rho_v_B_45": "Lichtreflexionsgrad, direkte Strahlung, "
                "Arbeitsstellung 45°, Sonnenhöhe 45°, SN EN 14500",
                "tau_v_D_45": "Lichttransmissionsgrad, diffuse Strahlung, "
                "Arbeitsstellung 45°, Sonnenhöhe 45°, SN EN 14500",
                "rho_v_D_45": "Lichtreflexionsgrad, diffuse Strahlung, "
                "Arbeitsstellung 45°, Sonnenhöhe 45°, SN EN 14500",
            },
            "source_des_valeurs": "Herstellerangaben. À défaut, les valeurs du "
            "TABLEAU 8 selon le type de protection solaire "
            "du §3.3.2.9.",
            "tableau_8_en_notre_possession": False,
            "anomalie_de_lenonce": "L'énoncé imprimé écrit "
            "« rho_v_sp_D = rho_v_B_D » alors que la liste "
            "de symboles définit rho_v_D_45 et non "
            "rho_v_B_D. Coquille probable pour "
            "rho_v_sp_D = rho_v_D_45. ⚠ À VÉRIFIER.",
        },
        "pertinence_pour_les_tests": {
            "commentaire": "Le bâtiment exemple porte un STORE EN TISSU "
            "(Stoffmarkise Soltis), pas des lamelles : le "
            "tableau 9 ne s'applique donc pas aux tests 4 à 6. "
            "Il s'applique au TEST 2 (cas à lamelles) — c'est "
            "précisément le modèle que TAS ne possède pas "
            "(« Kein Lamellenmodell », anwender_test2_3).",
            "voie_alternative_pour_le_tissu": "SIA 4010:2023 §3.1.5 : pour les "
            "stores en tissu, remplacer g_g du "
            "vitrage par g_tot (vitrage + "
            "protection) selon SN EN ISO 52022-3 "
            "ou ISO 15099 lorsque la protection "
            "est actionnée — « plus simple et "
            "donne des résultats plus précis ».",
        },
    }


def _ecrire(nom, donnees):
    """Write one generated reference payload as formatted UTF-8 JSON."""

    chemin = os.path.join(_SORTIE, nom)
    with io.open(chemin, "w", encoding="utf-8") as f:
        f.write(json.dumps(donnees, ensure_ascii=False, indent=2, sort_keys=False))
        f.write("\n")
    return chemin


def main():
    """Validate cross-standard offsets and write all reference payloads."""

    controles = verifier_regle_de_decalage()
    print("Règle de décalage SIA 380/2 §5.2.2.5 vs SIA 4010 §3.1.4 :")
    for courbe, usage, attendu, calcule in controles:
        print(
            "  courbe %-11s usage %-5s  annoncé %d K  calculé %d K  OK"
            % (courbe, usage, attendu, calcule)
        )
    print("  -> %d/%d décalages reproduits." % (len(controles), len(controles)))

    ruptures = verifier_figure_3()
    print()
    print("SIA 180:2014 figure 3 (ventilation naturelle, ni chauffe ni refroidi) :")
    print(
        "  limite sup 0.33*theta_rm+21.8 (plancher 25) ; inf 0.33*theta_rm+14.3 "
        "(plancher 20.5 ; plafond 22)"
    )
    print(
        "  ruptures theta_rm : sup %.2f ; inf basse %.2f ; inf haute %.2f  OK"
        % (
            ruptures["rupture_superieure_theta_rm_C"],
            ruptures["rupture_inferieure_basse_theta_rm_C"],
            ruptures["rupture_inferieure_haute_theta_rm_C"],
        )
    )

    t11 = _par_usage()
    print()
    print("Usage 4.04 Hörsaal (consigne du test 4, point ouvert O1) :")
    print(
        "  tableau 11 : chauffage %s °C, refroidissement %s °C"
        % (t11["4.04"][2], t11["4.04"][3])
    )
    print("  groupe 1.01-3.03 : 21 / 26  ->  décalage 0 K / 0 K")

    for nom, donnees in (
        ("sia-2024-2021.tables.json", construire_sia2024()),
        ("sia-180-2014.comfort.json", construire_sia180()),
        ("sia-387-4-2017.blinds.json", construire_sia387_4()),
    ):
        print("écrit : %s" % _ecrire(nom, donnees))


if __name__ == "__main__":
    main()
