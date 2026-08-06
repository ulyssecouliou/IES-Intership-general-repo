# -*- coding: utf-8 -*-
u"""Fige les valeurs de référence d'un test SIA 4010, quel qu'il soit.

Généralise `build_test7_reference.py` et `build_test2_reference.py`. La
disposition des classeurs varie d'un test à l'autre — le Test 7 empile ses
grandeurs verticalement, le Test 2 les juxtapose en blocs horizontaux, le
Test 3 n'en a qu'une sur douze cas répartis en lignes non contiguës — mais le
CRITÈRE, lui, ne varie pas :

    moyenne = AVERAGE(programmes contributeurs)
    haut    = moyenne + MAX(ABS(programme − moyenne))
    bas     = moyenne − MAX(...)          parfois plancher à MAX(0, …)

Ce script ne suppose donc aucune position : il repère les bandes par leurs
FORMULES, ce qui reste vrai si le SIA réorganise une feuille.

LES TROIS PIÈGES, traités pour tous les tests.

1. **Le jeu contributeur varie ligne par ligne**, et les colonnes ne sont pas
   des programmes mais des VARIANTES de programme (IDA_ICE « Fe det Spec »,
   « Fe det noSpec », « Fe einf »…). Le SIA retient une variante par
   programme, pas la même d'un programme à l'autre. On lit la formule.
2. **Des cellules portent du TEXTE ressemblant à une formule**
   (`=Daten_TAS!E11`, `='Daten EnergyPlus'!G6`) : ce sont des chaînes
   partagées qu'Excel ignore dans un `AVERAGE`. On ne déréférence rien.
3. **Le plancher à zéro est ponctuel**, jamais une propriété du critère.

CONTRÔLE : chaque bande est recalculée par `engine.scatter_band` et confrontée
au trio du classeur, tolérance 1e-6. Un seul écart et le script échoue — c'est
ce contrôle qui donne sa valeur au fichier figé.

Usage :
    python scripts/build_sia_reference.py 2 [--ecrire]
    python scripts/build_sia_reference.py 3 [--ecrire]
"""

from __future__ import print_function

import io
import json
import os
import re
import sys

import openpyxl
from openpyxl.utils import column_index_from_string, get_column_letter

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

from engine import scatter_band  # noqa: E402

_DOSSIER_SIA = os.environ.get(
    'SIA_4010_DOSSIER', os.path.join(_RACINE, 'SIA_4010_geteilter_Link'))

TOLERANCE = 1e-6

_REFERENCE_CELLULE = re.compile(r'([A-Z]{1,3})(\d{1,5})')
_PLANCHER = re.compile(r'^=.*MAX\(\s*0\s*,', re.I)

#: Disposition propre à chaque test, LUE sur le classeur et non supposée.
#: `lignes` borne le balayage ; `meta` nomme les colonnes de contexte.
DISPOSITIONS = {
    2: {
        'fichier': os.path.join('Test2', 'Resultaterfassung_Test2.xlsx'),
        'feuille': u'Zusammenfassung',
        'lignes': (13, 25),
        'ligne_programmes': 9,
        'ligne_variantes': 10,
        'ligne_grandeur': 12,
        'ligne_unite': 13,
        'meta': {'cas': 1, 'remarque': 2},
        'classes': ['1A', '1B', '2A', '2B', '4A', '4B'],
    },
    3: {
        'fichier': os.path.join('Test3', 'Resultaterfassung_Test3.xlsx'),
        'feuille': u'Zusammenfassung',
        'lignes': (10, 27),
        'ligne_programmes': 8,
        'ligne_variantes': 10,
        'ligne_grandeur': 7,
        'ligne_unite': 7,
        'meta': {'cas': 1, 'protection_solaire': 2, 'regulation_eclairage': 3},
        'classes': ['2A', '2B', '4A', '4B'],
    },
}


class ExtractionRefusee(RuntimeError):
    u"""Levée dès qu'une valeur ne peut pas être établie avec certitude."""


def _valeur_numerique(feuille, ligne, colonne):
    u"""Valeur d'une cellule si et seulement si elle est numérique.

    Args:
        feuille: Feuille en mode valeurs.
        ligne: Numéro de ligne.
        colonne: Numéro de colonne.

    Returns:
        float | None: La valeur, ou `None` pour toute autre chose — texte
        compris, comme Excel la traite dans un `AVERAGE`.
    """
    brut = feuille.cell(row=ligne, column=colonne).value
    if isinstance(brut, bool) or not isinstance(brut, (int, float)):
        return None
    return float(brut)


def _colonnes_citees(formule):
    u"""Lettres de colonnes citées par une formule.

    Args:
        formule: Formule Excel, ou toute autre valeur.

    Returns:
        list[str]: Lettres, dans l'ordre d'apparition ; vide si non-formule.
    """
    if not isinstance(formule, str) or '(' not in formule:
        return []
    return [m.group(1)
            for m in _REFERENCE_CELLULE.finditer(formule[formule.find('(') + 1:])]


def _bandes_du_classeur(feuille_formules, plage_lignes):
    u"""Repère les bandes par leur formule AVERAGE.

    Args:
        feuille_formules: Feuille en mode formules.
        plage_lignes: Couple (première, dernière) ligne à balayer.

    Returns:
        list[tuple[int, int]]: Couples (ligne, colonne de la moyenne).
    """
    debut, fin = plage_lignes
    trouvees = []
    for rangee in feuille_formules.iter_rows(min_row=debut, max_row=fin):
        for cellule in rangee:
            valeur = cellule.value
            if isinstance(valeur, str) and 'AVERAGE' in valeur.upper():
                trouvees.append((cellule.row, cellule.column))
    return sorted(trouvees)


def _controler_coherence(ligne, lettres_moyenne, lettres_haut, colonne_moyenne):
    u"""Vérifie que le MAX porte sur les mêmes colonnes que l'AVERAGE.

    Une divergence signalerait que le classeur pondère la moyenne et la
    déviation sur des jeux différents — cas qu'on refuse d'interpréter.

    Args:
        ligne: Numéro de ligne, pour le message.
        lettres_moyenne: Colonnes citées par l'AVERAGE.
        lettres_haut: Colonnes citées par la borne haute.
        colonne_moyenne: Indice de la colonne de moyenne, à écarter.

    Raises:
        ExtractionRefusee: Si les deux jeux diffèrent.
    """
    attendues = set(lettres_moyenne)
    observees = set(lettres_haut) - {get_column_letter(colonne_moyenne)}
    if observees and observees != attendues:
        raise ExtractionRefusee(
            u'ligne %d : AVERAGE porte sur %s mais MAX sur %s'
            % (ligne, sorted(attendues), sorted(observees)))


def _unite_apres(feuille, ligne, col_libelle, col_moyenne):
    u"""Unité d'une grandeur, cherchée À DROITE de son libellé.

    Les classeurs ne la placent pas au même endroit : le Test 2 la met sur la
    ligne suivant le libellé, le Test 3 sur la MÊME ligne, deux colonnes plus
    loin. Une colonne fixe donnerait « Mittelwert » comme unité — erreur
    silencieuse dans un référentiel figé.

    Args:
        feuille: Feuille en mode valeurs.
        ligne: Ligne où chercher.
        col_libelle: Colonne du libellé ; la recherche commence juste après.
        col_moyenne: Colonne de la moyenne, borne de la recherche.

    Returns:
        str | None: Première valeur texte non vide trouvée.
    """
    for colonne in range(col_libelle + 1, max(col_libelle + 2, col_moyenne) + 1):
        valeur = feuille.cell(row=ligne, column=colonne).value
        if isinstance(valeur, str) and valeur.strip():
            return valeur.strip()
    return None


def extraire(numero_test):
    u"""Extrait et vérifie toutes les bandes d'un test.

    Args:
        numero_test: Numéro du test SIA, ex. 2.

    Returns:
        dict: Structure figée, prête à écrire.

    Raises:
        ExtractionRefusee: Au premier écart avec le classeur.
    """
    if numero_test not in DISPOSITIONS:
        raise ExtractionRefusee(
            u'disposition inconnue pour le test %s ; connues : %s'
            % (numero_test, sorted(DISPOSITIONS)))
    plan = DISPOSITIONS[numero_test]
    chemin = os.path.join(_DOSSIER_SIA, plan['fichier'])
    if not os.path.exists(chemin):
        raise ExtractionRefusee(u'classeur introuvable : %s' % chemin)

    sf = openpyxl.load_workbook(chemin, data_only=False)[plan['feuille']]
    sv = openpyxl.load_workbook(chemin, data_only=True)[plan['feuille']]

    par_bloc = {}
    for ligne, col_moy in _bandes_du_classeur(sf, plan['lignes']):
        col_haut, col_bas = col_moy + 1, col_moy + 2
        lettres = _colonnes_citees(sf.cell(row=ligne, column=col_moy).value)
        if not lettres:
            raise ExtractionRefusee(
                u'ligne %d col %s : contributeurs illisibles'
                % (ligne, get_column_letter(col_moy)))
        _controler_coherence(
            ligne, lettres,
            _colonnes_citees(sf.cell(row=ligne, column=col_haut).value), col_moy)

        contributions, par_colonne = [], {}
        for lettre in lettres:
            colonne = column_index_from_string(lettre)
            valeur = _valeur_numerique(sv, ligne, colonne)
            if valeur is None:
                raise ExtractionRefusee(
                    u'ligne %d colonne %s : contributeur déclaré mais valeur '
                    u'non numérique' % (ligne, lettre))
            contributions.append(valeur)
            par_colonne[lettre] = {
                'valeur': valeur,
                'programme': sv.cell(row=plan['ligne_programmes'],
                                     column=colonne).value,
                'variante': sv.cell(row=plan['ligne_variantes'],
                                    column=colonne).value,
            }

        plancher = bool(_PLANCHER.match(
            str(sf.cell(row=ligne, column=col_bas).value or '')))
        bande = scatter_band.build_band(contributions, floor_at_zero=plancher)

        for nom, colonne, obtenu in ((u'moyenne', col_moy, bande.mean),
                                     (u'haut', col_haut, bande.upper_bound),
                                     (u'bas', col_bas, bande.lower_bound)):
            reference = sv.cell(row=ligne, column=colonne).value
            if not isinstance(reference, (int, float)):
                raise ExtractionRefusee(
                    u'ligne %d : %s non mis en cache par le classeur'
                    % (ligne, nom))
            if abs(float(reference) - obtenu) > TOLERANCE:
                raise ExtractionRefusee(
                    u'ligne %d, %s : classeur %.10f, recalcul %.10f'
                    % (ligne, nom, reference, obtenu))

        entree = {
            'ligne_classeur': ligne,
            'contributeurs': lettres,
            'par_colonne': par_colonne,
            'moyenne': bande.mean,
            'borne_haute': bande.upper_bound,
            'borne_basse': bande.lower_bound,
            'ecart_max': bande.max_deviation,
            'plancher_a_zero': plancher,
        }
        for nom_meta, colonne_meta in plan['meta'].items():
            valeur = sv.cell(row=ligne, column=colonne_meta).value
            entree[nom_meta] = valeur.strip() if isinstance(valeur, str) else valeur
        par_bloc.setdefault(col_moy, []).append(entree)

    grandeurs = []
    for col_moy in sorted(par_bloc):
        entrees = par_bloc[col_moy]
        col_libelle = min(column_index_from_string(l)
                          for l in entrees[0]['contributeurs']) - 1
        grandeurs.append({
            'colonne_moyenne': get_column_letter(col_moy),
            'libelle_de': sv.cell(row=plan['ligne_grandeur'],
                                  column=col_libelle).value,
            'unite': _unite_apres(sv, plan['ligne_unite'], col_libelle, col_moy),
            'cas': entrees,
        })

    return {
        'test': numero_test,
        'classes_concernees': plan['classes'],
        'statut': u'FIGÉ — bandes recalculées et confrontées au classeur',
        'date_extraction': u'2026-08-06',
        'source': {
            'fichier': u'SIA_4010_geteilter_Link/' + plan['fichier'].replace('\\', '/'),
            'feuille': plan['feuille'],
        },
        'critere': {
            'formule': u'moyenne ± MAX(ABS(programme − moyenne)), bornes incluses',
            'statut': u'INFERE',
            'origine': u"SIA 4010:2023 §4.4 délègue la comparaison au classeur ; "
                       u"seul le Test 1 énonce ses critères dans sa spécification.",
        },
        'piege_variantes': (
            u"Les colonnes sont des VARIANTES de programme, pas des programmes. "
            u"Le SIA retient une variante par programme, et pas la même d'un "
            u"programme à l'autre : le jeu contributeur est lu sur la formule."
        ),
        'grandeurs': grandeurs,
    }


def main(arguments):
    u"""Point d'entrée en ligne de commande.

    Args:
        arguments: Arguments sans le nom du script.

    Returns:
        int: 0 si tout s'est bien passé.
    """
    numeros = [int(a) for a in arguments if a.isdigit()]
    if not numeros:
        print(u'usage : python scripts/build_sia_reference.py <N> [--ecrire]')
        print(u'  tests disponibles : %s' % sorted(DISPOSITIONS))
        return 1

    for numero in numeros:
        donnees = extraire(numero)
        total = sum(len(g['cas']) for g in donnees['grandeurs'])
        print(u'Test %d — %d grandeur(s), %d bande(s)'
              % (numero, len(donnees['grandeurs']), total))
        for grandeur in donnees['grandeurs']:
            print()
            print(u'  %s [%s]' % (grandeur['libelle_de'], grandeur['unite']))
            for entree in grandeur['cas']:
                print(u'    %-12s %10.1f  (%10.1f … %10.1f)  %s%s'
                      % (entree.get('cas') or u'?', entree['moyenne'],
                         entree['borne_basse'], entree['borne_haute'],
                         u''.join(entree['contributeurs']),
                         u'  [plancher 0]' if entree['plancher_a_zero'] else u''))
        print()
        print(u'  toutes les bandes concordent (tol. %g)' % TOLERANCE)

        if '--ecrire' in arguments:
            sortie = os.path.join(_RACINE, 'refs', 'reference-data',
                                  'test-%d.ref.json' % numero)
            with io.open(sortie, 'w', encoding='utf-8') as flux:
                flux.write(json.dumps(donnees, ensure_ascii=False, indent=2))
                flux.write(u'\n')
            print(u'  écrit : %s' % os.path.relpath(sortie, _RACINE))
        print()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
