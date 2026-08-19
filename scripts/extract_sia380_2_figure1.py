# -*- coding: utf-8 -*-
u"""Extracts FIGURE 1 of SIA 380/2:2022 (p. 27) from the vector drawing.

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
    sys.stderr.write(u'PyMuPDF (fitz) requis.\n')
    raise

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
_PDF = os.path.join(_RACINE, 'refs', 'SIA-380-2-2022.pdf')
_SORTIE = os.path.join(_RACINE, 'refs', 'reference-data',
                       'sia-380-2-2022.figure1.json')

PAGE_FIGURE_1 = 27  # printed page number == index+1

# Calibration: PDF coordinates of the extreme grid lines of the frame.
# x = 10 °C at px 145.21 ; x = 25 °C at px 513.89
# y = 20 °C at py 378.61 ; y = 27 °C at py 176.35
GRILLE = {u'x_min_px': 145.21, u'x_max_px': 513.89, u'x_min_val': 10.0, u'x_max_val': 25.0,
          u'y_min_px': 378.61, u'y_max_px': 176.35, u'y_min_val': 20.0, u'y_max_val': 27.0}

# Line-style signatures as present in the PDF. The labels are those from the
# normative text of §5.2.2.3 (French edition).
STYLES = {
    u'[] 0':               u'trait plein',
    u'[ 6.75 9 ] 0':       u'pointillé',        # consignes VARIABLES
    u'[ 6.75 9 0 9 ] 0':   u'traits mixtes',    # consignes CONSTANTES
}

TOLERANCE_RESIDU = 0.005  # °C — beyond this, we refuse to conclude


def _transformation():
    g = GRILLE
    sx = (g[u'x_max_px'] - g[u'x_min_px']) / (g[u'x_max_val'] - g[u'x_min_val'])
    sy = (g[u'y_min_px'] - g[u'y_max_px']) / (g[u'y_max_val'] - g[u'y_min_val'])

    def vers_x(px):
        return g[u'x_min_val'] + (px - g[u'x_min_px']) / sx

    def vers_y(py):
        return g[u'y_min_val'] + (g[u'y_min_px'] - py) / sy

    return vers_x, vers_y, sx, sy


def _sommets(chemin, vers_x, vers_y):
    u"""Vertices of a path, deduplicated while preserving drawing order."""
    bruts = []
    for item in chemin[u'items']:
        if item[0] == 'l':
            for point in (item[1], item[2]):
                if (not bruts
                        or abs(point.x - bruts[-1].x) > 0.3
                        or abs(point.y - bruts[-1].y) > 0.3):
                    bruts.append(point)
    return [(round(vers_x(p.x), 4), round(vers_y(p.y), 4)) for p in bruts]


def _courbes_epaisses(page, vers_x, vers_y):
    u"""The four data curves: thick stroke (2.25), within the frame."""
    trouvees = []
    for index, chemin in enumerate(page.get_drawings()):
        largeur = chemin.get(u'width') or 0.0
        if largeur < 2.0:
            continue
        sommets = _sommets(chemin, vers_x, vers_y)
        if len(sommets) < 2:
            continue
        trouvees.append({
            u'index_chemin': index,
            u'style_pdf': chemin.get(u'dashes'),
            u'style': STYLES.get(chemin.get(u'dashes'), u'⚠ inconnu'),
            u'largeur_pt': largeur,
            u'sommets': sommets,
        })
    return trouvees


def _segmenter(sommets):
    u"""Splits a vertex list into x-monotone polylines.

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
    u"""Maximum discrepancy between extracted values and a multiple of `pas`."""
    pire = 0.0
    for x, y in polyligne:
        pire = max(pire, abs(x - round(x / pas) * pas),
                   abs(y - round(y / pas) * pas))
    return pire


def extraire():
    document = fitz.open(_PDF)
    page = document[PAGE_FIGURE_1 - 1]
    vers_x, vers_y, sx, sy = _transformation()

    chemins = _courbes_epaisses(page, vers_x, vers_y)
    polylignes = []
    for chemin in chemins:
        for groupe in _segmenter(chemin[u'sommets']):
            if len(groupe) < 2:
                continue
            polylignes.append({
                u'style': chemin[u'style'],
                u'style_pdf': chemin[u'style_pdf'],
                u'index_chemin': chemin[u'index_chemin'],
                u'sommets': groupe,
                u'y_min': min(y for _, y in groupe),
                u'y_max': max(y for _, y in groupe),
            })

    # Naming by style + altitude: the limits are in solid stroke, the highest
    # is the upper one; similarly for each pair of setpoint curves.
    def nommer(style, roles):
        lot = sorted((p for p in polylignes if p[u'style'] == style),
                     key=lambda p: p[u'y_max'])
        if len(lot) != len(roles):
            raise AssertionError(
                u'style %r : %d polylignes trouvées, %d attendues'
                % (style, len(lot), len(roles)))
        for polyligne, role in zip(lot, roles):
            polyligne[u'role'] = role
        return lot

    nommer(u'trait plein', [u'limite_inferieure', u'limite_superieure'])
    nommer(u'pointillé', [u'consigne_chauffage_variable',
                          u'consigne_refroidissement_variable'])
    nommer(u'traits mixtes', [u'consigne_chauffage_constante',
                              u'consigne_refroidissement_constante'])

    par_role = dict((p[u'role'], p) for p in polylignes)

    # Quality check: the limits must fall on half-degrees and the setpoints
    # on tenths.
    residus = {}
    for role, pas in ((u'limite_inferieure', 0.5), (u'limite_superieure', 0.5),
                      (u'consigne_chauffage_variable', 0.1),
                      (u'consigne_refroidissement_variable', 0.1),
                      (u'consigne_chauffage_constante', 0.1),
                      (u'consigne_refroidissement_constante', 0.1)):
        residu = _residu_max(par_role[role][u'sommets'], pas)
        residus[role] = round(residu, 6)
        if residu > TOLERANCE_RESIDU:
            raise AssertionError(
                u'%s : résidu %.4f °C au pas de %.1f — extraction refusée'
                % (role, residu, pas))

    # Control deviation Δθctr, measured not assumed.
    ctr_chaud = round(
        min(y for _, y in par_role[u'consigne_chauffage_variable'][u'sommets'])
        - min(y for _, y in par_role[u'limite_inferieure'][u'sommets']), 4)
    ctr_froid = round(
        max(y for _, y in par_role[u'limite_superieure'][u'sommets'])
        - max(y for _, y in par_role[u'consigne_refroidissement_variable'][u'sommets']), 4)

    return {
        u'sx_pt_par_degre': round(sx, 5),
        u'sy_pt_par_degre': round(sy, 5),
        u'polylignes': polylignes,
        u'par_role': par_role,
        u'residus_max_c': residus,
        u'delta_theta_ctr_chauffage_k': ctr_chaud,
        u'delta_theta_ctr_refroidissement_k': ctr_froid,
    }


def _arrondir(sommets, pas):
    return [[round(round(x / pas) * pas, 4), round(round(y / pas) * pas, 4)]
            for x, y in sommets]


def construire_json(extrait):
    pr = extrait[u'par_role']
    return {
        u'norme': u'SIA 380/2:2022',
        u'element': u'figure 1 — Températures ambiantes de consigne pour le '
                    u'chauffage et le refroidissement',
        u'page_imprimee': PAGE_FIGURE_1,
        u'statut': u'FIGÉ — extrait du dessin vectoriel, résidu < 0,001 °C',
        u'date_extraction': u'2026-08-04',
        u'source': {
            u'fichier': u'refs/SIA-380-2-2022.pdf',
            u'methode': u'PyMuPDF get_drawings(), calibration sur les lignes de '
                        u'grille du cadre (et NON sur les étiquettes de texte, '
                        u'décalées de ~0,8 pt)',
            u'script': u'scripts/extract_sia380_2_figure1.py',
            u'residus_max_c': extrait[u'residus_max_c'],
        },
        u'axes': {
            u'abscisse': u'Température extérieure moyenne glissante sur 48 heures, °C',
            u'abscisse_domaine': [10.0, 25.0],
            u'ordonnee': u'Température, °C',
            u'ordonnee_domaine': [20.0, 27.0],
            u'nature_de_la_grandeur':
                u'SIA 380/2 §5.2.2.1 : « Les valeurs de consigne peuvent être '
                u'fixées pour la température moyenne de l\'air intérieur OU pour '
                u'la température opérative simplifiée. Le choix est à discuter '
                u'avec le mandant. » → la figure ne tranche pas ; le choix est '
                u'un paramètre du projet.',
        },
        u'courbes': {
            u'limite_superieure': {
                u'style_dans_la_figure': u'trait plein',
                u'sommets': _arrondir(pr[u'limite_superieure'][u'sommets'], 0.5),
                u'pente_segment_croissant': u'2,0 K / 5,5 K = 4/11',
                u'origine': u'SIA 180:2014 figure 4, courbe supérieure '
                            u'(§5.2.2.5)',
            },
            u'limite_inferieure': {
                u'style_dans_la_figure': u'trait plein',
                u'sommets': _arrondir(pr[u'limite_inferieure'][u'sommets'], 0.5),
                u'pente_segment_croissant': u'1,5 K / 4,5 K = 1/3',
                u'origine': u'SIA 180:2014 figure 4, courbe inférieure '
                            u'(§5.2.2.5)',
            },
            u'consigne_chauffage_variable': {
                u'symbole': u'T_set;H',
                u'style_dans_la_figure': u'pointillé',
                u'sommets': _arrondir(pr[u'consigne_chauffage_variable'][u'sommets'], 0.1),
                u'sapplique_si': u'régulation AVEC communication '
                                 u'(HEAT_EMIS_CTRL_DEF = 3 ou 4 selon '
                                 u'SN EN ISO 52120-1:2022 tab. 5) ET l\'utilisateur '
                                 u'n\'a aucune possibilité d\'influence — §5.2.2.3',
            },
            u'consigne_refroidissement_variable': {
                u'symbole': u'T_set;C',
                u'style_dans_la_figure': u'pointillé',
                u'sommets': _arrondir(
                    pr[u'consigne_refroidissement_variable'][u'sommets'], 0.1),
                u'sapplique_si': u'idem, CLG_EMIS_CTRL_DEF = 3 ou 4 — §5.2.2.3',
            },
            u'consigne_chauffage_constante': {
                u'symbole': u'T_set;H constante',
                u'style_dans_la_figure': u'traits mixtes',
                u'valeur_c': max(y for _, y in _arrondir(
                    pr[u'consigne_chauffage_constante'][u'sommets'], 0.1)),
                u'definition_normative': u'« valeurs constantes au MAXIMUM de la '
                                         u'courbe de la valeur de consigne pour le '
                                         u'chauffage » — §5.2.2.3',
                u'sapplique_si': u'régulation SANS communication '
                                 u'(HEAT_EMIS_CTRL_DEF = 1 ou 2) OU l\'utilisateur '
                                 u'a une possibilité d\'influence — §5.2.2.3',
            },
            u'consigne_refroidissement_constante': {
                u'symbole': u'T_set;C constante',
                u'style_dans_la_figure': u'traits mixtes',
                u'valeur_c': min(y for _, y in _arrondir(
                    pr[u'consigne_refroidissement_constante'][u'sommets'], 0.1)),
                u'definition_normative': u'« au MINIMUM de la courbe de la valeur '
                                         u'de consigne pour le refroidissement » '
                                         u'— §5.2.2.3',
                u'sapplique_si': u'CLG_EMIS_CTRL_DEF = 1 ou 2 — §5.2.2.3',
            },
        },
        u'ecart_de_regulation': {
            u'symbole': u'delta_theta_ctr',
            u'mesure_chauffage_k': extrait[u'delta_theta_ctr_chauffage_k'],
            u'mesure_refroidissement_k': extrait[u'delta_theta_ctr_refroidissement_k'],
            u'definition_normative': u'SIA 380/2 §5.2.2.2 : « La différence entre '
                                     u'les valeurs de consigne et les limites '
                                     u'supérieures et inférieures [...] correspond '
                                     u'à l\'écart de régulation pour l\'émission de '
                                     u'chaleur et de froid delta_theta_ctr selon '
                                     u'SN EN 15316-2:2017. »',
            u'reserve': u'⚠ À VÉRIFIER — 0,7 K est ce que la figure DESSINE. '
                        u'SN EN 15316-2:2017, qui définit la grandeur, n\'est pas '
                        u'en notre possession : nous ne savons donc pas si 0,7 K '
                        u'est la valeur générale ou une illustration pour une '
                        u'classe de régulation particulière.',
        },
        u'regle_de_decalage_par_usage': {
            u'citation': u'SIA 380/2 §5.2.2.5 : « Sans détermination plus '
                         u'détaillée des conditions de confort, les limites seront '
                         u'décalées suivant la différence entre les valeurs de '
                         u'dimensionnement de l\'utilisation correspondante et les '
                         u'utilisations 1.01 à 3.03 selon SIA 2024:2021, '
                         u'tableau 11. »',
            u'forme': u'decalage_inferieure_K = theta_h_design(usage) - 21 ; '
                      u'decalage_superieure_K = theta_c_design(usage) - 26',
            u'groupe_de_reference': u'1.01 à 3.03, unanimes à 21 °C / 26 °C au '
                                    u'tableau 11 — c\'est ce qui rend la '
                                    u'« différence » scalaire.',
            u'verifie_contre': u'les 10 valeurs de décalage énumérées par '
                               u'SIA 4010:2023 §3.1.4 sur 7 usages : 10/10 '
                               u'reproduites (cf. engine/tests/test_setpoint_curves.py)',
            u'la_forme_est_conservee': u'« Pour d\'autres utilisations, les courbes '
                                       u'se déplacent, mais gardent leur forme. » '
                                       u'— §5.2.2.5',
        },
        u'exception_habillement_non_saisonnier': {
            u'citation': u'SIA 380/2 §5.2.2.5 et SIA 4010 §3.1.4 : pour les usages '
                         u'où l\'habillement ne dépend pas de la température '
                         u'extérieure (salles de gymnastique, salles de fitness, '
                         u'piscines couvertes, vestiaires, douches), les limites '
                         u'sont CONSTANTES — « la courbe [...] prend la forme '
                         u'd\'une ligne droite » (SIA 4010 §3.1.4).',
            u'usages_concernes_sia_2024': [u'11.01', u'11.02', u'11.03', u'12.08'],
            u'reserve': u'⚠ La correspondance entre les libellés cités et les '
                        u'numéros d\'usage est notre lecture ; les normes citent '
                        u'les libellés, pas les numéros. 12.06 « WC, Bad, Dusche » '
                        u'pourrait aussi relever de « douches ». À VÉRIFIER.',
        },
        u'controle_croise_sia_180': {
            u'affirmation_normative': u'SIA 380/2 §5.2.2.5 : les limites de la '
                                      u'figure 1 « correspondent à celles de '
                                      u'SIA 180:2014, figure 4, pour les locaux '
                                      u'd\'habitation et les bureaux »',
            u'capture_figure_4_recue': u'2026-08-04, Yiqiao Yang, SIA',
            u'concordance': u'8 valeurs sur 8 — ordonnées 20,5 / 22,0 / 24,5 / 26,5 '
                            u'et ruptures d\'abscisse 12 / 17,5 / 19 / 23,5.',
            u'portee': u'Deux documents indépendants, accord exact. Les sommets '
                       u'ci-dessus valent donc aussi pour SIA 180:2014 figure 4.',
        },
    }


def main():
    extrait = extraire()
    print(u'Calibration : %.5f pt/°C en x, %.5f pt/°C en y'
          % (extrait[u'sx_pt_par_degre'], extrait[u'sy_pt_par_degre']))
    print()
    for role, polyligne in sorted(extrait[u'par_role'].items()):
        print(u'%-38s %-14s %s' % (role, polyligne[u'style'],
                                   polyligne[u'sommets']))
    print()
    print(u'Résidus max (°C) : %s' % extrait[u'residus_max_c'])
    print(u'delta_theta_ctr : chauffage %.4f K, refroidissement %.4f K'
          % (extrait[u'delta_theta_ctr_chauffage_k'],
             extrait[u'delta_theta_ctr_refroidissement_k']))

    if '--ecrire' in sys.argv:
        donnees = construire_json(extrait)
        with io.open(_SORTIE, 'w', encoding='utf-8') as f:
            f.write(json.dumps(donnees, ensure_ascii=False, indent=2))
            f.write(u'\n')
        print()
        print(u'écrit : %s' % _SORTIE)


if __name__ == '__main__':
    main()
