# -*- coding: utf-8 -*-
u"""Fige les valeurs de référence du Test 7 (classe de validation 5).

SOURCE : `SIA_4010_geteilter_Link/Test7/Resultaterfassung Test7.xlsx`,
feuille `Zusammenfassung`, telle que livrée par le SIA.

DISPOSITION LUE, non supposée :
    ligne 6   : noms des programmes — F = Testprogramm (à nous), puis
                G = IDA ICE, H = Excel, I = Energy+/OpenStudio, J = EDSL Tas
    ligne 7   : versions ; K = unité, L = Mittelwert, M = Obere Grenze,
                N = Untere Grenze
    lignes 8-12  : grandeurs du mode FROID
    lignes 14-18 : grandeurs du mode CHAUD
    ligne 20  : PV-Ertrag
    lignes 21-26 : Diagnosegrössen — SANS bande (L/M/N vides)

DEUX PIÈGES, traités explicitement.

1. **Le jeu de contributeurs varie ligne par ligne.** `M8` exclut `I8`, `M14`
   exclut `J14` : un programme qui n'a pas livré une grandeur sort de la bande
   et n'est jamais compté comme zéro. Le jeu qui fait foi est celui de la liste
   `MAX(ABS(...))`, PAS la plage de l'`AVERAGE` — l'`AVERAGE` porte sur une
   plage `G:J` dont Excel écarte les vides à l'évaluation, ce qui est
   équivalent mais illisible statiquement.

2. **Des cellules contiennent du TEXTE qui ressemble à une formule.**
   `I8`, `I10`, `I11`, `J14`, `J17`, `J18`, `J20` portent la chaîne
   `='Daten EnergyPlus'!G6` — mais dans le XML elles sont marquées `t="s"`,
   c'est-à-dire **chaîne partagée**, pas formule (`<f>` absent). Excel les
   traite donc comme du texte, et `AVERAGE` les ignore : c'est bien ainsi que
   le SIA a exclu ces programmes.

   Correction apportée le 2026-08-06 après audit indépendant : une version
   antérieure de ce script **déréférençait** ces chaînes et inscrivait le
   nombre obtenu dans `par_programme`, laissant croire que le programme avait
   livré une valeur alors que le classeur l'exclut. Les bandes restaient
   justes — les contributeurs sont lus sur la liste `MAX(ABS(...))`, qui ne
   les mentionne pas — mais le JSON était trompeur à la lecture.
   **On ne déréférence plus rien : une chaîne vaut `None`, comme pour Excel.**

CONTRÔLE : chaque bande est RECALCULÉE par `engine.scatter_band` et confrontée
au trio L/M/N du classeur. Un seul écart et le script échoue. C'est la preuve
que notre moteur reproduit le critère d'acceptation du SIA.

Usage :
    python scripts/build_test7_reference.py [--ecrire]
"""

from __future__ import print_function

import io
import json
import os
import re
import sys

import openpyxl

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

from engine import scatter_band  # noqa: E402

_DOSSIER_SIA = os.environ.get(
    'SIA_4010_DOSSIER',
    os.path.join(os.path.expanduser('~'), 'Documents', 'IES Internship',
                 'IES-Intership-general-repo', 'SIA_4010_geteilter_Link'))
_CLASSEUR = os.path.join(_DOSSIER_SIA, 'Test7', 'Resultaterfassung Test7.xlsx')
_SORTIE = os.path.join(_RACINE, 'refs', 'reference-data', 'test-7.ref.json')

FEUILLE = u'Zusammenfassung'
LIGNE_PROGRAMMES = 6
LIGNE_VERSIONS = 7
COL_LIBELLE = 2      # B
COL_GROUPE = 1       # A
COL_PROGRAMMES = (7, 8, 9, 10)   # G, H, I, J
COL_NOTRE = 6        # F — Testprogramm, vide tant que VE n'a pas tourné
COL_UNITE = 11       # K
COL_MOYENNE = 12     # L
COL_HAUT = 13        # M
COL_BAS = 14         # N

# Tolérance de recalcul. Les valeurs du classeur sont en pleine précision ;
# ce seuil n'absorbe qu'un arrondi binaire.
TOLERANCE = 1e-6

_CONTRIB = re.compile(r'ABS\(\s*([A-Z]+)(\d+)\s*-')
_PLANCHER = re.compile(r'^=\s*MAX\(\s*0\s*,', re.I)


class ExtractionRefusee(RuntimeError):
    pass


def _valeur_numerique(valeurs, feuille, ligne, colonne):
    u"""Valeur d'une cellule si et seulement si elle est numérique.

    Toute autre chose — texte, cellule vide, chaîne ressemblant à une formule —
    vaut `None`, exactement comme Excel la traite dans un `AVERAGE`. On ne
    déréférence RIEN : une chaîne `='Daten EnergyPlus'!G6` marquée `t="s"` est
    du texte, pas une référence, et la transformer en nombre inventerait une
    valeur que le classeur exclut délibérément (cf. piège 2 de l'en-tête).
    """
    brut = valeurs[feuille].cell(row=ligne, column=colonne).value
    if isinstance(brut, bool):
        return None
    if isinstance(brut, (int, float)):
        return float(brut)
    return None


def _contributeurs(formule_haut):
    u"""Colonnes contributrices, lues sur la liste MAX(ABS(...)) de la borne."""
    if not isinstance(formule_haut, str):
        return []
    return [m.group(1) for m in _CONTRIB.finditer(formule_haut)]


def extraire():
    if not os.path.exists(_CLASSEUR):
        raise ExtractionRefusee(u'classeur introuvable : %s' % _CLASSEUR)

    formules = openpyxl.load_workbook(_CLASSEUR, data_only=False)
    caches = openpyxl.load_workbook(_CLASSEUR, data_only=True)
    valeurs = dict((n, caches[n]) for n in caches.sheetnames
                   if hasattr(caches[n], 'cell'))

    sf = formules[FEUILLE]
    sv = caches[FEUILLE]

    programmes = [sv.cell(row=LIGNE_PROGRAMMES, column=c).value
                  for c in COL_PROGRAMMES]
    versions = [sv.cell(row=LIGNE_VERSIONS, column=c).value
                for c in COL_PROGRAMMES]

    from openpyxl.utils import get_column_letter
    lettre_de = dict((get_column_letter(c), c) for c in COL_PROGRAMMES)

    grandeurs, groupe_courant = [], None
    for ligne in range(8, 31):
        etiquette_groupe = sv.cell(row=ligne, column=COL_GROUPE).value
        if isinstance(etiquette_groupe, str) and etiquette_groupe.strip():
            groupe_courant = etiquette_groupe.strip()

        formule_moyenne = sf.cell(row=ligne, column=COL_MOYENNE).value
        if not (isinstance(formule_moyenne, str)
                and 'AVERAGE' in formule_moyenne.upper()):
            continue  # pas de bande sur cette ligne (Diagnosegrössen)

        libelle = sv.cell(row=ligne, column=COL_LIBELLE).value
        if not libelle:
            continue

        formule_haut = sf.cell(row=ligne, column=COL_HAUT).value
        formule_bas = sf.cell(row=ligne, column=COL_BAS).value
        lettres = _contributeurs(formule_haut)
        if not lettres:
            raise ExtractionRefusee(
                u'ligne %d : contributeurs illisibles dans %r'
                % (ligne, formule_haut))

        par_programme, contributions = {}, []
        for lettre in lettres:
            colonne = lettre_de.get(lettre)
            if colonne is None:
                raise ExtractionRefusee(
                    u'ligne %d : colonne contributrice %s hors G-J'
                    % (ligne, lettre))
            v = _valeur_numerique(valeurs, FEUILLE, ligne, colonne)
            if v is None:
                raise ExtractionRefusee(
                    u'ligne %d colonne %s : contributeur déclaré mais valeur '
                    u'non numérique — extraction refusée plutôt que devinée'
                    % (ligne, lettre))
            contributions.append(v)

        for indice, colonne in enumerate(COL_PROGRAMMES):
            par_programme[programmes[indice]] = _valeur_numerique(
                valeurs, FEUILLE, ligne, colonne)

        plancher = bool(_PLANCHER.match(str(formule_bas or '')))
        bande = scatter_band.build_band(contributions, floor_at_zero=plancher)

        attendu = dict(
            (nom, sv.cell(row=ligne, column=col).value)
            for nom, col in ((u'moyenne', COL_MOYENNE), (u'haut', COL_HAUT),
                             (u'bas', COL_BAS)))
        for nom, obtenu in ((u'moyenne', bande.mean),
                            (u'haut', bande.upper_bound),
                            (u'bas', bande.lower_bound)):
            reference = attendu[nom]
            if not isinstance(reference, (int, float)):
                raise ExtractionRefusee(
                    u'ligne %d : %s non mis en cache par le classeur' % (ligne, nom))
            if abs(float(reference) - obtenu) > TOLERANCE:
                raise ExtractionRefusee(
                    u'ligne %d, %s : classeur %.10f, recalcul %.10f'
                    % (ligne, nom, reference, obtenu))

        grandeurs.append({
            u'ligne_classeur': ligne,
            u'groupe': groupe_courant,
            u'libelle_de': str(libelle).strip(),
            u'unite': sv.cell(row=ligne, column=COL_UNITE).value,
            u'par_programme': par_programme,
            u'contributeurs': lettres,
            u'contributeurs_noms': [programmes[COL_PROGRAMMES.index(lettre_de[l])]
                                    for l in lettres],
            u'moyenne': bande.mean,
            u'borne_haute': bande.upper_bound,
            u'borne_basse': bande.lower_bound,
            u'ecart_max': bande.max_deviation,
            u'plancher_a_zero': plancher,
        })

    return {
        u'test': 7,
        u'classe_de_validation': u'5 — SIA 4010:2023 tableau 63 : le Test 7 est '
                                 u'le seul test exigé par la classe 5',
        u'statut': u'FIGÉ — bandes recalculées et confrontées au classeur',
        u'date_extraction': u'2026-08-05',
        u'source': {
            u'fichier': u'SIA_4010_geteilter_Link/Test7/Resultaterfassung Test7.xlsx',
            u'feuille': FEUILLE,
            u'programmes': programmes,
            u'versions': versions,
        },
        u'critere': {
            u'formule': u'moyenne ± MAX(ABS(programme − moyenne)), bornes incluses',
            u'origine': u'formules L/M/N du classeur, lues verbatim',
            u'plancher_a_zero': u'présent ligne par ligne (MAX(0,…)), jamais par défaut',
            u'contributeurs': u"lus sur la liste MAX(ABS(...)) de la borne haute ; "
                              u"le jeu VARIE d'une grandeur à l'autre",
        },
        u'grandeurs': grandeurs,
        u'reserve_pv': u"La grandeur « PV-Ertrag » porte une bande : c'est une "
                       u"Testgrösse obligatoire. Elle exige l'irradiance sur le "
                       u"plan des modules, absente de toute source officielle à "
                       u"ce jour. Cf. traceability/classes-de-validation.spec.md.",
    }


def main():
    donnees = extraire()
    print(u'Test 7 — %d grandeurs à bande extraites' % len(donnees[u'grandeurs']))
    print(u'programmes : %s' % u', '.join(str(p) for p in donnees[u'source'][u'programmes']))
    print()
    print(u'%-46s %10s %10s %10s  %s' % (u'grandeur', u'moyenne', u'bas', u'haut', u'contrib.'))
    print(u'-' * 100)
    for g in donnees[u'grandeurs']:
        print(u'%-46s %10.1f %10.1f %10.1f  %s%s'
              % (g[u'libelle_de'][:46], g[u'moyenne'], g[u'borne_basse'],
                 g[u'borne_haute'], u''.join(g[u'contributeurs']),
                 u'  [plancher 0]' if g[u'plancher_a_zero'] else u''))
    print()
    print(u'toutes les bandes recalculées concordent avec le classeur (tol. %g)'
          % TOLERANCE)

    if '--ecrire' in sys.argv:
        with io.open(_SORTIE, 'w', encoding='utf-8') as f:
            f.write(json.dumps(donnees, ensure_ascii=False, indent=2))
            f.write(u'\n')
        print(u'écrit : %s' % os.path.relpath(_SORTIE, _RACINE))


if __name__ == '__main__':
    main()
