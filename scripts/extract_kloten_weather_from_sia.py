# -*- coding: utf-8 -*-
u"""Extrait la température extérieure de Zürich-Kloten des classeurs OFFICIELS SIA.

DÉCOUVERTE DU 2026-08-05. Le classeur d'évaluation officiel du Test 4,
`Resultaterfassung Test4.xlsx`, contient une feuille **`Wetterdaten`** restée
inaperçue jusqu'ici. Elle porte 8760 valeurs horaires :

    colonne 1 : « Site Outdoor Air Drybulb Temperature [C](Hourly) »
    colonne 2 : « EMS Two Day Average OA Temp [C](Hourly) »

La colonne 1 est la **température d'air extérieur horaire de Zürich-Kloten**
telle que le programme de référence EnergyPlus l'a lue dans le fichier SIA 2028
d'origine. La colonne 2 est la **moyenne glissante sur 48 heures**, déjà
calculée — c'est-à-dire exactement l'abscisse de la figure 1 de SIA 380/2.

PORTÉE ET LIMITES — à lire avant de s'en servir.

Ce que cela donne : une série de températures d'origine officielle SIA, sans
achat. Suffisant pour tout ce qui ne dépend que de la température d'air —
notamment le refroidisseur sec et l'échangeur sur air extérieur du Test 7.

Ce que cela ne donne PAS : le rayonnement solaire. Le fichier SIA 2028 d'origine
contient l'irradiance sur les surfaces verticales des orientations principales
(rapport EXCEL du Test 2) ; rien de tout cela n'est ici. Les tests 1E, 2, 3, 4,
5, 6 en dépendent, et le Test 7 en dépend pour sa grandeur obligatoire n° 14
« Elektrische Energie PV ».

Ce n'est donc PAS un substitut au jeu SIA 2028 complet. C'est une pièce
authentique et vérifiable du puzzle, et elle vient d'une source officielle.

Usage :
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

# Le dossier officiel vit dans l'autre dépôt (118 Mo, hors dépôt par .gitignore).
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

# Bornes de vraisemblance pour Zürich-Kloten (année de référence DRY).
# Elles ne valident pas la valeur exacte : elles interceptent une extraction
# qui aurait attrapé la mauvaise colonne ou la mauvaise feuille.
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
