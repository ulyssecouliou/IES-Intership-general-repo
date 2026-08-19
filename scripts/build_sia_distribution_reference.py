# -*- coding: utf-8 -*-
u"""Extracts the reference frequency distributions — SIA tests 2, 3 and 5.

WHY THIS FILE EXISTS. The specifications for tests 2, 3 and 5 state **two**
criteria, not one:

  1. « Jahressumme : Mittelwert +/- max. Abweichung der Referenzprogramme » —
     that is the annual band, already frozen by `build_sia_reference.py`;
  2. « Die Häufigkeitsverteilung muss im Streubereich der Referenzprogramme
     liegen » — the hourly distribution must stay within the dispersion of the
     reference programmes.

The second had never been extracted. Without it, a "compliant" verdict would
only cover half the test criteria.

THIS PARAGRAPH CLAIMED THE OPPOSITE, AND IT WAS WRONG. It stated that tests 4
and 6 have neither a class sheet nor a distribution sheet, "and that is an
observation, not an omission". It was an omission, and it came down to a
single letter: their workbooks name the sheet `Haeufigkeitskassen`, without
the « l » of `Haeufigkeitsklassen` that tests 2, 3 and 5 use. A typo in the
official files, mistaken for an absence.

WHAT WAS VERIFIED, on 2026-08-10, by opening the workbooks:

  * `Resultaterfassung Test4.xlsx` and `Resultaterfassung_Test6.xlsx` both
    carry a 23-row `Haeufigkeitskassen` sheet, structured like Test 2's: a
    class index, then one bound per quantity;
  * their `Zusammenfassung` carries a « Stündliche Häufigkeitsverteilung »
    section (Test 4: row 19) followed by blocks per quantity — name, unit and
    programmes, a `Klassen` row, then the counts for each reference programme.
    This is exactly the structure this script already knows how to read.

The authority clarification of 2026-08-10
(`traceability/sia4010-authority-clarification-2026-08-10.json`, decision
`SIA4010-TEST4-6-DISTRIBUTION-PRESENCE`) says the same.

These two tests are therefore WITHIN REACH and remain TO DO: their layout has
not yet been read in `DISPOSITIONS`, and this script never guesses a layout —
see the comment on that table. `TESTS_AVEC_DISTRIBUTION` still excludes them
for this reason, and for this reason only.

WHAT THE WORKBOOK DOES NOT DO, AND WHAT THIS SCRIPT WILL THEREFORE NOT DO
EITHER. The « Verteilung » sheets are **charts**, not tables: they plot the 8
reference variants plus the tested programme, and **no band is calculated
anywhere**. The judgement is visual in the official workbook. This script
therefore freezes COUNTS per class — facts — and leaves the criterion
explicitly undetermined. Choosing a band formula here would amount to
inventing the criterion.

Usage:
    python scripts/build_sia_distribution_reference.py [numero...] [--ecrire]
"""

from __future__ import print_function

import io
import json
import os
import sys

import openpyxl
from openpyxl.utils import column_index_from_string, get_column_letter

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))

_DOSSIER_SIA = os.environ.get(
    'SIA_4010_DOSSIER', os.path.join(_RACINE, 'SIA_4010_geteilter_Link'))

_SORTIE = os.path.join(_RACINE, 'refs', 'reference-data')

#: Tests whose layout has been READ in `DISPOSITIONS`, and whose counts are
#: therefore extractable. Tests 4, 6 and 7 joined this list on 2026-08-12,
#: when their layout was read.
#:
#: EXTRACTABLE IS NOT THE SAME AS ENFORCEABLE. This list says from where we
#: know how to read counts, not where a distribution criterion applies. The
#: specifications for tests 4, 6 and 7 contain no « Testkriterien » section —
#: zero occurrences of `Testkriterien`, `Streubereich`, `Abweichung` or
#: `Häufigkeitsverteilung`, verified on 2026-08-12 after confirming that the
#: text of all three PDFs extracts correctly. Whether the distribution
#: criterion is enforceable for them is a question put to the sub-commission
#: and has no answer yet. The `sia_distributions_engine` therefore keeps its
#: own list: freezing a fact does not authorise drawing a verdict from it.
TESTS_AVEC_DISTRIBUTION = (2, 3, 4, 5, 6, 7)

#: Tests whose workbooks carry distributions, whether the layout has been read
#: or not. Used to distinguish "no distribution" from "not yet extracted" —
#: confusing the two is what led to weeks of writing that tests 4 and 6 had
#: none, and to writing to the SIA on 2026-08-07, who flagged it.
TESTS_PORTANT_DES_DISTRIBUTIONS = (2, 3, 4, 5, 6, 7)

#: Hours in a year. The workbook totals by column; the discrepancies of one or
#: two hours observed (8759, 8732) are REAL and preserved as-is.
HEURES_ANNEE = 8760

#: Layout READ from each workbook, never assumed. They all differ —
#: believing them to be alike is what caused four errors on annual sums.
#:
#:   ligne_cas        : row carrying the case identifier, at the top of a block
#:   ligne_grandeur   : row carrying « quantity, unit »
#:   ligne_unite      : row carrying the unit ALONE, when the workbook does not
#:                      include it in the quantity cell. Absent for tests 2, 3
#:                      and 5, where the unit follows the comma.
#:   ligne_programmes : row carrying programme names
#:   ligne_classes    : row carrying the word « Klassen »
#:   colonne_index    : class index column common to all blocks, or None if
#:                      each block carries its own bounds
#:
#: THREE LAYOUT FAMILIES, identified on 2026-08-12:
#:
#:   tests 2, 3, 5 : « Quantity, unit » in ONE cell, and a case row carrying
#:                   an identifier (« Alle », « Test 3 A »...);
#:   tests 4, 6    : quantity and unit on TWO rows, the unit row also carrying
#:                   programme names. No case identifier: these tests have
#:                   only one case;
#:   test 7        : like 4 and 6, but the quantity cell repeats the unit after
#:                   a comma. Both sources are read and must agree — a
#:                   disagreement causes the extraction to be refused.
DISPOSITIONS = {
    2: {
        'fichier': os.path.join('Test2', 'Resultaterfassung_Test2.xlsx'),
        'feuille': u'Zusammenfassung',
        'ligne_cas': 28,
        'ligne_grandeur': 29,
        'ligne_programmes': 30,
        'ligne_classes': 31,
        'colonne_index': None,
        'classes_sia': ['2A', '2B', '4A', '4B'],
    },
    3: {
        'fichier': os.path.join('Test3', 'Resultaterfassung_Test3.xlsx'),
        'feuille': u'Zusammenfassung',
        'ligne_cas': 30,
        'ligne_grandeur': 31,
        'ligne_programmes': 32,
        'ligne_classes': 33,
        'colonne_index': None,
        'classes_sia': ['2A', '2B', '4A', '4B'],
    },
    5: {
        'fichier': os.path.join('Test5', 'Resultaterfassung_Test5.xlsx'),
        'feuille': u'Zusammenfassung',
        'ligne_cas': 20,
        'ligne_grandeur': 21,
        'ligne_programmes': 22,
        'ligne_classes': 23,
        # Test 5 carries the class index in column A, common to all blocks,
        # and the bound in the 1st column of each block.
        'colonne_index': 1,
        'classes_sia': ['3', '4A', '4B'],
    },
    # Identified on 2026-08-12 by opening the workbooks. The section carries
    # the title « Stündliche Häufigkeitsverteilung » in column A: Test 4 row
    # 19, Test 6 row 22, Test 7 row 31. No case row: these three tests have
    # only one case, and `_reserves` will say so rather than inferring it.
    4: {
        'fichier': os.path.join('Test4', 'Resultaterfassung Test4.xlsx'),
        'feuille': u'Zusammenfassung',
        'ligne_cas': 20,
        'ligne_grandeur': 21,
        'ligne_unite': 22,
        'ligne_programmes': 22,
        'ligne_classes': 23,
        'colonne_index': 1,
        'classes_sia': ['3', '4A', '4B'],
    },
    6: {
        'fichier': os.path.join('Test6', 'Resultaterfassung_Test6.xlsx'),
        'feuille': u'Zusammenfassung',
        'ligne_cas': 23,
        'ligne_grandeur': 24,
        'ligne_unite': 25,
        'ligne_programmes': 25,
        'ligne_classes': 26,
        'colonne_index': 1,
        'classes_sia': ['3', '4A', '4B'],
    },
    7: {
        'fichier': os.path.join('Test7', 'Resultaterfassung Test7.xlsx'),
        'feuille': u'Zusammenfassung',
        'ligne_cas': 31,
        'ligne_grandeur': 32,
        'ligne_unite': 33,
        'ligne_programmes': 33,
        'ligne_classes': 34,
        'colonne_index': 1,
        'classes_sia': ['4A', '4B', '5'],
    },
}

#: Word that marks, on `ligne_classes`, the first column of a block.
MARQUEUR_BLOC = u'Klassen'

#: Label for the control row, below the classes.
MARQUEUR_TOTAL = u'Total'


class ExtractionRefusee(RuntimeError):
    u"""Raised as soon as a value cannot be established with certainty."""


def _texte(feuille, ligne, colonne):
    u"""Text value of a cell, cleaned.

    Args:
        feuille: openpyxl sheet.
        ligne: Row number.
        colonne: Column index.

    Returns:
        str | None: Cleaned text, or `None` if the cell carries none.
    """
    valeur = feuille.cell(ligne, colonne).value
    if isinstance(valeur, str) and valeur.strip():
        return valeur.strip()
    return None


def _entier(feuille, ligne, colonne):
    u"""Integer value of a cell, or `None`.

    Args:
        feuille: openpyxl sheet.
        ligne: Row number.
        colonne: Column index.

    Returns:
        int | None: Count, or `None` if the cell is not numeric.
    """
    valeur = feuille.cell(ligne, colonne).value
    if isinstance(valeur, bool) or valeur is None:
        return None
    if isinstance(valeur, int):
        return valeur
    if isinstance(valeur, float) and valeur == int(valeur):
        return int(valeur)
    return None


def _colonnes_de_bloc(feuille, disposition):
    u"""Locates the columns that open a distribution block.

    Args:
        feuille: `Zusammenfassung` sheet.
        disposition: Entry from `DISPOSITIONS`.

    Returns:
        list[int]: Indices of columns carrying « Klassen », in order.

    Raises:
        ExtractionRefusee: If no block is found — the declared layout does
            not match the workbook, and continuing would produce an empty
            reference dataset that reads as "no distribution".
    """
    ligne = disposition['ligne_classes']
    blocs = [c for c in range(1, feuille.max_column + 1)
             if _texte(feuille, ligne, c) == MARQUEUR_BLOC]
    if not blocs:
        raise ExtractionRefusee(
            u'aucun bloc « %s » sur la ligne %d : la disposition déclarée ne '
            u'correspond pas au classeur.' % (MARQUEUR_BLOC, ligne))
    return blocs


def _bornes_du_bloc(feuille, disposition, colonne_bloc):
    u"""Reads the class bounds of a block, and the control row.

    Args:
        feuille: `Zusammenfassung` sheet.
        disposition: Entry from `DISPOSITIONS`.
        colonne_bloc: Column carrying « Klassen ».

    THE CONTROL ROW IS NOT ALWAYS LABELLED. Test 2 writes « Total » in
    column A; Test 3 leaves the cell empty and simply places totals below the
    last class. It is therefore located by position — the row following the
    last class — and the **sum check** (`_controler_totaux`) validates this
    detection: if the retained row is wrong, the sums will not add up and
    extraction will be refused. No detection is taken on faith.

    Returns:
        tuple: `(lignes_de_classe, bornes, ligne_total)`.

    Raises:
        ExtractionRefusee: If no class is found below the block.
    """
    depart = disposition['ligne_classes'] + 1
    colonne_libelle = disposition.get('colonne_index') or colonne_bloc
    lignes, bornes = [], []
    ligne_total = None
    for ligne in range(depart, feuille.max_row + 1):
        if _texte(feuille, ligne, 1) == MARQUEUR_TOTAL:
            ligne_total = ligne
            break
        borne = _entier(feuille, ligne, colonne_bloc)
        if borne is None and _entier(feuille, ligne, colonne_libelle) is None:
            break
        lignes.append(ligne)
        bornes.append(borne)
    if not lignes:
        raise ExtractionRefusee(
            u'aucune classe sous le bloc %s : la disposition déclarée ne '
            u'correspond pas au classeur.' % get_column_letter(colonne_bloc))
    if ligne_total is None:
        ligne_total = lignes[-1] + 1
    return lignes, bornes, ligne_total


def _contributeurs(feuille, disposition, colonne_bloc, colonne_fin,
                   ligne_total):
    u"""Locates programme columns that actually submitted this case.

    THE PITFALL. A column may be full of zeros because the programme did not
    submit this case, not because it counted zero hours. The « Total » row
    resolves this: it is ~8760 for a real contributor, 0 otherwise. Counting
    zeros as measurements would skew the entire dispersion.

    Args:
        feuille: `Zusammenfassung` sheet.
        disposition: Entry from `DISPOSITIONS`.
        colonne_bloc: Column carrying « Klassen ».
        colonne_fin: First column of the next block (excluded).
        ligne_total: Control row.

    Returns:
        list[dict]: One descriptor per contributing column.
    """
    ligne_programmes = disposition['ligne_programmes']
    retenus = []
    for colonne in range(colonne_bloc + 1, colonne_fin):
        total = _entier(feuille, ligne_total, colonne)
        if not total:
            continue
        retenus.append({
            'colonne': get_column_letter(colonne),
            'programme': _texte(feuille, ligne_programmes, colonne),
            # Backward-compatible name: this is the sum of the displayed
            # classes, not the size of the underlying annual source series.
            'total_heures': total,
            'heures_dans_classes': total,
            'heures_hors_classes': max(0, HEURES_ANNEE - total),
            'heures_source_attendues': HEURES_ANNEE,
        })
    return retenus


def _grandeur_et_unite(libelle):
    u"""Splits « Quantity, unit » into two parts.

    Args:
        libelle: Text of the quantity row.

    Returns:
        tuple[str, str | None]: Quantity and unit, where the unit may be absent.
    """
    if libelle and ',' in libelle:
        grandeur, unite = libelle.rsplit(',', 1)
        return grandeur.strip(), unite.strip()
    return (libelle or u'').strip(), None


def extraire(numero_test):
    u"""Extracts the reference distributions for a test.

    Args:
        numero_test: 2, 3 or 5.

    Returns:
        dict: Structure ready to freeze.

    Raises:
        ExtractionRefusee: On any inconsistency between the extraction and the
            workbook checks.
    """
    if numero_test not in DISPOSITIONS:
        raise ExtractionRefusee(
            u'test %r : aucune disposition relevée. Tests dont la disposition '
            u'est lue : %s. Ne jamais en ajouter un sans avoir ouvert son '
            u'classeur : une disposition supposée extrait au hasard.'
            % (numero_test, sorted(DISPOSITIONS)))

    disposition = DISPOSITIONS[numero_test]
    chemin = os.path.join(_DOSSIER_SIA, disposition['fichier'])
    if not os.path.isfile(chemin):
        raise ExtractionRefusee(u'classeur introuvable : %s' % chemin)

    classeur = openpyxl.load_workbook(chemin, data_only=True)
    feuille = classeur[disposition['feuille']]

    colonnes = _colonnes_de_bloc(feuille, disposition)
    distributions = []
    for rang, colonne_bloc in enumerate(colonnes):
        suivante = (colonnes[rang + 1] if rang + 1 < len(colonnes)
                    else feuille.max_column + 1)
        distributions.append(
            _extraire_bloc(feuille, disposition, colonne_bloc, suivante))

    return {
        u'test': numero_test,
        u'critere': u'Häufigkeitsverteilung : « muss im Streubereich der '
                    u'Referenzprogramme liegen » (Spezifikation_Test%d.pdf, '
                    u'Testkriterien)' % numero_test,
        u'statut_critere': u'CONFIRME_AUTORITE_2026-08-10',
        u'pourquoi_non_calcule':
            u'Les feuilles « Verteilung » sont des GRAPHIQUES : elles tracent '
            u'les variantes de référence et le programme testé, sans calculer '
            u'aucune bande. Aucune cellule du classeur ne définit le '
            u'Streubereich d\'une distribution. La clarification écrite du '
            u'2026-08-10 définit la règle : enveloppe min/max des programmes '
            u'de référence, classe par classe.',
        u'classes_concernees': disposition['classes_sia'],
        u'source': {
            u'fichier': disposition['fichier'],
            u'feuille': disposition['feuille'],
            u'lignes_de_structure': _lignes_de_structure(disposition),
        },
        u'nb_distributions': len(distributions),
        u'reserves': _reserves(distributions),
        u'distributions': distributions,
    }


def _lignes_de_structure(disposition):
    u"""Records the rows actually read, so the source is reproducible.

    `unite` only appears for layouts that have one: the absent key means
    "the unit follows the comma in the quantity cell", not "unknown".

    Args:
        disposition: Entry from `DISPOSITIONS`.

    Returns:
        dict: Row numbers, by role.
    """
    lignes = {
        u'cas': disposition['ligne_cas'],
        u'grandeur': disposition['ligne_grandeur'],
        u'programmes': disposition['ligne_programmes'],
        u'classes': disposition['ligne_classes'],
    }
    if disposition.get('ligne_unite') is not None:
        lignes[u'unite'] = disposition['ligne_unite']
    return lignes


def _reserves(distributions):
    u"""Drafts reservations from the extracted data, not from memory.

    A hand-written reservation becomes stale as soon as the workbook changes.
    These are recalculated at each extraction: if the pattern disappears, the
    reservation disappears with it.

    Args:
        distributions: Extracted blocks.

    Returns:
        list[str]: Reservations, possibly empty.
    """
    reserves = []

    sans_cas = [b['colonne_bloc'] for b in distributions if not b['cas']]
    if sans_cas:
        reserves.append(
            u'Bloc(s) %s : le classeur ne porte AUCUN identifiant de cas sur '
            u'la ligne prévue. La spécification range ces grandeurs sous un '
            u'cas précis, mais le classeur ne le dit pas : le champ reste nul '
            u'plutôt que d\'être comblé par déduction.'
            % u', '.join(sans_cas))

    conflits = [b['conflit_unite'] for b in distributions
                if b.get('conflit_unite')]
    for conflit in conflits:
        reserves.append(
            u'Bloc %s : le classeur écrit deux unités contradictoires pour la '
            u'même grandeur — « %s » dans la cellule de grandeur, « %s » sur la '
            u'ligne d\'unité %d. Les effectifs sont conservés car ils ne '
            u'dépendent pas de cette étiquette ; l\'unité reste nulle. Trancher '
            u'ici corrigerait un défaut du classeur officiel à la place de son '
            u'auteur. À signaler à la sous-commission.'
            % (conflit['colonne_bloc'], conflit['unite_cellule_grandeur'],
               conflit['unite_ligne_unite'], conflit['ligne_unite']))

    totaux = sorted(set(c['total_heures'] for b in distributions
                        for c in b['contributeurs']))
    hors_classes = [t for t in totaux if t < HEURES_ANNEE]
    if hors_classes:
        reserves.append(
            u'Totaux affichés dans les classes : %s. La SIA a confirmé le '
            u'2026-08-10 que les écarts à %d ne sont pas des heures manquantes : '
            u'les autres valeurs sont hors des bornes définies par les classes. '
            u'Elles sont conservées comme compte hors classes et ne sont pas '
            u'ajoutées à la dernière classe.'
            % (u', '.join(str(t) for t in totaux), HEURES_ANNEE))

    reserves.append(
        u'Les effectifs sont des FAITS relevés cellule par cellule et '
        u'réconciliés avec la ligne de totaux du classeur. La bande '
        u'd\'acceptation min/max par classe est confirmée par la réponse '
        u'écrite du 2026-08-10.')
    return reserves


def _extraire_bloc(feuille, disposition, colonne_bloc, colonne_fin):
    u"""Extracts one distribution block.

    Args:
        feuille: `Zusammenfassung` sheet.
        disposition: Entry from `DISPOSITIONS`.
        colonne_bloc: Column carrying « Klassen ».
        colonne_fin: First column of the next block (excluded).

    Returns:
        dict: Distribution for one (case, quantity) pair.

    Raises:
        ExtractionRefusee: If the sum of counts for a contributor does not
            reproduce its declared total. This is the safeguard: it has already
            caught four false assumptions about annual sums.
    """
    lignes, bornes, ligne_total = _bornes_du_bloc(
        feuille, disposition, colonne_bloc)
    contributeurs = _contributeurs(
        feuille, disposition, colonne_bloc, colonne_fin, ligne_total)

    grandeur, unite = _grandeur_et_unite(
        _texte(feuille, disposition['ligne_grandeur'], colonne_bloc))
    ligne_unite = disposition.get('ligne_unite')
    conflit_unite = None
    if ligne_unite is not None:
        unite_propre = _texte(feuille, ligne_unite, colonne_bloc)
        if unite is None:
            # Tests 4 and 6: the quantity cell does not carry the unit.
            unite = unite_propre
        elif unite_propre and unite_propre != unite:
            # Test 7, block W on 2026-08-12: the quantity cell announces
            # « kW » and the unit row « °C ». Only one block out of seventeen.
            #
            # The COUNTS do not depend on this label: refusing the block would
            # lose facts over a metadata disagreement. Choosing one of the two
            # sources would mean correcting a defect in the official workbook
            # in place of its author. The unit therefore remains null and the
            # conflict surfaces as a named reservation.
            conflit_unite = {
                'colonne_bloc': get_column_letter(colonne_bloc),
                'unite_cellule_grandeur': unite,
                'unite_ligne_unite': unite_propre,
                'ligne_unite': ligne_unite,
            }
            unite = None

    effectifs = []
    for rang, ligne in enumerate(lignes):
        par_colonne = {}
        for contributeur in contributeurs:
            colonne = column_index_from_string(contributeur['colonne'])
            par_colonne[contributeur['colonne']] = _entier(
                feuille, ligne, colonne)
        effectifs.append({
            'ligne_classeur': ligne,
            'borne_superieure': bornes[rang],
            'par_colonne': par_colonne,
        })

    _controler_totaux(contributeurs, effectifs, colonne_bloc)

    bloc = {
        'cas': _texte(feuille, disposition['ligne_cas'], colonne_bloc),
        'grandeur': grandeur,
        'unite': unite,
        'colonne_bloc': get_column_letter(colonne_bloc),
        'nb_classes': len(lignes),
        'ligne_total': ligne_total,
        'contributeurs': contributeurs,
        'effectifs': effectifs,
    }
    # Key added only when there is a conflict: the reference datasets for
    # tests 2, 3 and 5 thus remain bit-for-bit identical, none of them having
    # a unit row. A frozen proof is not rewritten for a null key.
    if conflit_unite is not None:
        bloc['conflit_unite'] = conflit_unite
    return bloc


def _controler_totaux(contributeurs, effectifs, colonne_bloc):
    u"""Compares the sum of counts to the total declared by the workbook.

    Args:
        contributeurs: Column descriptors.
        effectifs: Counts per class.
        colonne_bloc: Block column, for the error message.

    Raises:
        ExtractionRefusee: On the slightest discrepancy. A misread count would
            yield a plausible but incorrect distribution.
    """
    for contributeur in contributeurs:
        lettre = contributeur['colonne']
        somme = sum(e['par_colonne'][lettre] or 0 for e in effectifs)
        if somme != contributeur['total_heures']:
            raise ExtractionRefusee(
                u'bloc %s, colonne %s : somme des classes = %d, total déclaré '
                u'par le classeur = %d. Écart de %d.'
                % (get_column_letter(colonne_bloc), lettre, somme,
                   contributeur['total_heures'],
                   somme - contributeur['total_heures']))


def _chemin_sortie(numero_test):
    u"""Path for the frozen reference dataset of a test.

    Args:
        numero_test: SIA test number.

    Returns:
        str: Absolute path.
    """
    return os.path.join(_SORTIE, 'test-%d.distributions.ref.json' % numero_test)


def main(arguments):
    u"""Command-line entry point.

    Args:
        arguments: Test numbers, and `--ecrire`.

    Returns:
        int: 0 if everything went well, 1 otherwise.
    """
    demandes = [int(a) for a in arguments if a.isdigit()]
    tests = demandes or list(TESTS_AVEC_DISTRIBUTION)
    code = 0
    for numero in tests:
        try:
            donnees = extraire(numero)
        except ExtractionRefusee as erreur:
            print(u'Test %d : REFUSE — %s' % (numero, erreur))
            code = 1
            continue
        heures = set()
        for bloc in donnees['distributions']:
            for contributeur in bloc['contributeurs']:
                heures.add(contributeur['total_heures'])
        print(u'Test %d : %d distributions, %d classes, totaux horaires %s'
              % (numero, donnees['nb_distributions'],
                 donnees['distributions'][0]['nb_classes'] if
                 donnees['distributions'] else 0,
                 sorted(heures)))
        for bloc in donnees['distributions'][:4]:
            print(u'    %-12s %-42s %d contributeur(s)'
                  % (bloc['cas'], (bloc['grandeur'] or u'')[:42],
                     len(bloc['contributeurs'])))
        if len(donnees['distributions']) > 4:
            print(u'    ... et %d autres'
                  % (len(donnees['distributions']) - 4))
        if '--ecrire' in arguments:
            chemin = _chemin_sortie(numero)
            with io.open(chemin, 'w', encoding='utf-8') as flux:
                flux.write(json.dumps(donnees, ensure_ascii=False, indent=1))
                flux.write(u'\n')
            print(u'    écrit : %s' % os.path.relpath(chemin, _RACINE))
        print()
    return code


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
