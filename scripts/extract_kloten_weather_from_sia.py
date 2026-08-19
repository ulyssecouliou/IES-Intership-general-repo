# -*- coding: utf-8 -*-
u"""Extracts the Zürich-Kloten outdoor temperature from the OFFICIAL SIA workbooks.

DISCOVERY OF 2026-08-05. The official evaluation workbook for Test 4,
`Resultaterfassung Test4.xlsx`, contains a **`Wetterdaten`** sheet that
had gone unnoticed until now. It carries 8760 hourly values:

    column 1: "Site Outdoor Air Drybulb Temperature [C](Hourly)"
    column 2: "EMS Two Day Average OA Temp [C](Hourly)"

Column 1 is the **hourly outdoor air temperature for Zürich-Kloten** as
the reference program EnergyPlus read it from the original SIA 2028 file.
Column 2 is the **48-hour running mean**, already calculated — that is
exactly the x-axis of figure 1 of SIA 380/2.

SCOPE AND LIMITATIONS — read before using.

What this gives: a temperature series of official SIA origin, without
purchase. Sufficient for anything that depends only on air temperature —
in particular the dry cooler and the outdoor-air heat exchanger of Test 7.

What this does NOT give: solar radiation. The original SIA 2028 file
contains irradiance on vertical surfaces for the main orientations
(from the Test 2 EXCEL report); none of that is here. Tests 1E, 2, 3, 4,
5, 6 depend on it, and Test 7 depends on it for its mandatory quantity n° 14
"Elektrische Energie PV".

This is therefore NOT a substitute for the full SIA 2028 dataset. It is
an authentic and verifiable piece of the puzzle, from an official source.

Usage:
    python scripts/extract_kloten_weather_from_sia.py [--ecrire]
"""

from __future__ import print_function

import io
import json
import os
import sys

import openpyxl

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))

# The official folder lives in the other repository (118 MB, excluded by .gitignore).
_DOSSIER_SIA = os.environ.get(
    'SIA_4010_DOSSIER',
    os.path.join(os.path.expanduser('~'), 'Documents', 'IES Internship',
                 'IES-Intership-general-repo', 'SIA_4010_geteilter_Link'))

_CLASSEUR = os.path.join(_DOSSIER_SIA, 'Test4', 'Resultaterfassung Test4.xlsx')
_FEUILLE = u'Wetterdaten'

_SORTIE_JSON = os.path.join(_RACINE, 'refs', 'reference-data',
                            'sia-2028-kloten-temperature.json')
_SORTIE_CSV = os.path.join(_RACINE, 'refs', 'reference-data',
                           'sia-2028-kloten-temperature.csv')

HEURES = 8760

# Plausibility bounds for Zürich-Kloten (DRY reference year).
# They do not validate the exact value: they catch an extraction that
# picked the wrong column or the wrong sheet.
MOYENNE_ATTENDUE = (8.0, 11.0)
MIN_ATTENDU = (-25.0, -5.0)
MAX_ATTENDU = (28.0, 40.0)


class ExtractionRefusee(RuntimeError):
    pass


def extraire():
    if not os.path.exists(_CLASSEUR):
        raise ExtractionRefusee(
            u'classeur officiel introuvable : %s\n'
            u'Définir SIA_4010_DOSSIER si le dossier SIA est ailleurs.'
            % _CLASSEUR)

    classeur = openpyxl.load_workbook(_CLASSEUR, data_only=True, read_only=True)
    if _FEUILLE not in classeur.sheetnames:
        raise ExtractionRefusee(u'feuille %r absente de %s'
                                % (_FEUILLE, os.path.basename(_CLASSEUR)))
    feuille = classeur[_FEUILLE]

    lignes = [list(r) for r in feuille.iter_rows(values_only=True)]
    classeur.close()

    entete = [unicode(v) if str is bytes else str(v) for v in lignes[0][:2]]
    if u'Drybulb' not in entete[0]:
        raise ExtractionRefusee(
            u"colonne 1 inattendue : %r — l'extraction est refusée plutôt que "
            u"de figer une grandeur non identifiée" % entete[0])

    temperature, moyenne_48h = [], []
    for ligne in lignes[1:]:
        if isinstance(ligne[0], (int, float)):
            temperature.append(float(ligne[0]))
            moyenne_48h.append(
                float(ligne[1]) if isinstance(ligne[1], (int, float)) else None)

    if len(temperature) != HEURES:
        raise ExtractionRefusee(u'%d heures extraites, %d attendues'
                                % (len(temperature), HEURES))

    moyenne = sum(temperature) / len(temperature)
    mini, maxi = min(temperature), max(temperature)
    for valeur, (bas, haut), nom in (
            (moyenne, MOYENNE_ATTENDUE, u'moyenne'),
            (mini, MIN_ATTENDU, u'minimum'),
            (maxi, MAX_ATTENDU, u'maximum')):
        if not (bas <= valeur <= haut):
            raise ExtractionRefusee(
                u'%s = %.2f °C hors de la plage de vraisemblance [%.1f ; %.1f] '
                u'pour Zürich-Kloten' % (nom, valeur, bas, haut))

    return entete, temperature, moyenne_48h


def construire(entete, temperature, moyenne_48h):
    moyenne = sum(temperature) / len(temperature)
    return {
        u'grandeur': u"température d'air extérieur horaire, Zürich-Kloten",
        u'statut': u'FIGÉ — source officielle SIA, extrait le 2026-08-05',
        u'source': {
            u'fichier': u'SIA_4010_geteilter_Link/Test4/Resultaterfassung Test4.xlsx',
            u'feuille': _FEUILLE,
            u'colonnes': entete,
            u'nature': u"sortie du programme de référence EnergyPlus, telle que "
                       u"livrée par le SIA dans son classeur d'évaluation officiel",
            u'origine_amont': u'fichier SIA 2028 DRY normal, station Kloten '
                              u'(« Original-SIA-Datei » des rapports d\'application)',
        },
        u'heures': len(temperature),
        u'agregats': {
            u'min_c': round(min(temperature), 4),
            u'max_c': round(max(temperature), 4),
            u'moyenne_c': round(moyenne, 4),
        },
        u'moyenne_glissante_48h': {
            u'presente': any(v is not None for v in moyenne_48h),
            u'colonne': entete[1] if len(entete) > 1 else None,
            u'usage': u"abscisse de la figure 1 de SIA 380/2 — permet de "
                      u"contrôler `engine.setpoint_curves.running_mean_48h` "
                      u"contre une série calculée par un programme de référence, "
                      u"y compris sur les 47 premières heures où la norme ne dit "
                      u"rien.",
        },
        u'ce_que_cela_debloque': [
            u"Tout ce qui ne dépend que de la température d'air extérieur : "
            u"refroidisseur sec et échangeur sur air extérieur du Test 7, donc "
            u"le point de fonctionnement de la pompe à chaleur.",
            u"La validation de notre moyenne glissante sur 48 h.",
        ],
        u'ce_que_cela_ne_debloque_pas': [
            u"Le RAYONNEMENT SOLAIRE, absent de cette feuille. Le fichier "
            u"SIA 2028 d'origine contient l'irradiance sur les surfaces "
            u"verticales des orientations principales ; rien de cela n'est ici.",
            u"Test 7 grandeur obligatoire n° 14 « Elektrische Energie PV » : "
            u"exige l'irradiance sur le plan des modules.",
            u"Tests 1E, 2, 3, 4, 5, 6 : tous solaires.",
            u"L'humidité de l'air extérieur.",
        ],
        u'avertissement': u"Ce n'est PAS un substitut au jeu SIA 2028 complet. "
                          u"C'est une pièce authentique du puzzle, d'origine "
                          u"officielle, qui couvre la seule température.",
    }


def main():
    entete, temperature, moyenne_48h = extraire()
    donnees = construire(entete, temperature, moyenne_48h)

    print(u'feuille  : %s' % _FEUILLE)
    print(u'colonnes : %s' % u' | '.join(entete))
    print(u'heures   : %d' % donnees[u'heures'])
    agregats = donnees[u'agregats']
    print(u'min %.2f   max %.2f   moyenne %.3f °C'
          % (agregats[u'min_c'], agregats[u'max_c'], agregats[u'moyenne_c']))
    print(u'moyenne glissante 48 h présente : %s'
          % donnees[u'moyenne_glissante_48h'][u'presente'])

    if '--ecrire' in sys.argv:
        with io.open(_SORTIE_JSON, 'w', encoding='utf-8') as f:
            f.write(json.dumps(donnees, ensure_ascii=False, indent=2))
            f.write(u'\n')
        with io.open(_SORTIE_CSV, 'w', encoding='utf-8') as f:
            f.write(u'heure,theta_e_air_c,moyenne_glissante_48h_c\n')
            for i, (t, m) in enumerate(zip(temperature, moyenne_48h), start=1):
                f.write(u'%d,%.6f,%s\n'
                        % (i, t, u'' if m is None else u'%.6f' % m))
        print()
        print(u'écrit : %s' % os.path.relpath(_SORTIE_JSON, _RACINE))
        print(u'écrit : %s' % os.path.relpath(_SORTIE_CSV, _RACINE))


if __name__ == '__main__':
    main()
