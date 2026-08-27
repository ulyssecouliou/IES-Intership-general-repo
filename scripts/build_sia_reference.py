# -*- coding: utf-8 -*-
"""Freezes the reference values for any SIA 4010 test.

Generalises `build_test7_reference.py` and `build_test2_reference.py`. The
workbook layout varies from test to test — Test 7 stacks its quantities
vertically, Test 2 juxtaposes them in horizontal blocks, Test 3 has only one
over twelve non-contiguous rows — but the CRITERION itself does not vary:

    mean  = AVERAGE(contributing programmes)
    upper = mean + MAX(ABS(programme − mean))
    lower = mean − MAX(...)          sometimes floored at MAX(0, …)

This script therefore assumes no fixed position: it locates bands by their
FORMULAE, which remains correct even if the SIA reorganises a sheet.

THE THREE PITFALLS, handled for all tests.

1. **The contributing set varies row by row**, and columns are not programmes
   but PROGRAMME VARIANTS (IDA_ICE « Fe det Spec », « Fe det noSpec »,
   « Fe einf »…). The SIA retains one variant per programme, not the same one
   across programmes. We read the formula.
2. **Some cells carry TEXT that looks like a formula**
   (`=Daten_TAS!E11`, `='Daten EnergyPlus'!G6`): these are shared strings
   that Excel ignores in an `AVERAGE`. We dereference nothing.
3. **The zero floor is punctual**, never a property of the criterion.

CHECK: each band is recalculated by `engine.scatter_band` and compared to the
workbook trio, tolerance 1e-6. A single discrepancy causes the script to fail
— this check is what gives the frozen file its value.

Usage:
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
    "SIA_4010_DOSSIER", os.path.join(_RACINE, "SIA_4010_geteilter_Link")
)

TOLERANCE = 1e-6

_REFERENCE_CELLULE = re.compile(r"([A-Z]{1,3})(\d{1,5})")
_PLAGE = re.compile(r"([A-Z]{1,3})(\d{1,5})\s*:\s*([A-Z]{1,3})(\d{1,5})")
_PLANCHER = re.compile(r"^=\s*MAX\(\s*0\s*,", re.I)

#: Layout specific to each test, READ from the workbook and never assumed.
#: `lignes` bounds the scan; `meta` names the context columns.
#
# `libelle`, `cas` and `unite` say WHERE to read each label:
#     ('ligne', n)   -> column n of the band row
#     ('bloc', n)    -> row n, in the 1st column of the contributor block
#     ('colonne', n) -> row n, in the mean column
#     ('contributeur', n) -> row n, above the 1st contributor
#     ('cellule', (r, c)) -> fixed cell, when the label follows no relative
#                            rule (Test 3: unit in H7, label in F7)
#     None           -> not applicable
#
# Three semantics coexist in the official workbooks, and they must be
# distinguished to avoid labelling bands incorrectly:
#   tests 2 and 3: one quantity per BLOCK, one case per row;
#   tests 4 and 6: one quantity per ROW, no cases;
#   test 5:        a MATRIX, quantity in row and case in column.
DISPOSITIONS = {
    2: {
        "fichier": os.path.join("Test2", "Resultaterfassung_Test2.xlsx"),
        "feuille": "Zusammenfassung",
        "lignes": (13, 25),
        "ligne_programmes": 9,
        "ligne_variantes": 10,
        "libelle": ("bloc", 12),
        "cas": ("ligne", 1),
        "unite": ("bloc", 13),
        "meta": {"remarque": 2},
        "classes": ["1A", "1B", "2A", "2B", "4A", "4B"],
    },
    3: {
        "fichier": os.path.join("Test3", "Resultaterfassung_Test3.xlsx"),
        "feuille": "Zusammenfassung",
        "lignes": (10, 27),
        "ligne_programmes": 8,
        "ligne_variantes": 10,
        "libelle": ("bloc", 7),
        "cas": ("ligne", 1),
        # F7 carries the label, H7 the unit: two columns further, with no
        # usable relative rule. It is therefore designated explicitly.
        "unite": ("cellule", (7, 8)),
        "meta": {"protection_solaire": 2, "regulation_eclairage": 3},
        "classes": ["2A", "2B", "4A", "4B"],
    },
    4: {
        "fichier": os.path.join("Test4", "Resultaterfassung Test4.xlsx"),
        "feuille": "Zusammenfassung",
        "lignes": (9, 13),
        "ligne_programmes": 8,
        "ligne_variantes": 9,
        "libelle": ("ligne", 1),
        "cas": None,
        "unite": ("ligne", 9),
        "meta": {},
        "classes": ["3", "4A", "4B"],
    },
    5: {
        "fichier": os.path.join("Test5", "Resultaterfassung_Test5.xlsx"),
        "feuille": "Zusammenfassung",
        "lignes": (9, 17),
        "ligne_programmes": 6,
        "ligne_variantes": 7,
        "libelle": ("ligne", 1),
        "cas": ("contributeur", 8),
        "unite": ("ligne", 5),
        "meta": {},
        "classes": ["3", "4A", "4B"],
    },
    6: {
        "fichier": os.path.join("Test6", "Resultaterfassung_Test6.xlsx"),
        "feuille": "Zusammenfassung",
        "lignes": (10, 16),
        "ligne_programmes": 8,
        "ligne_variantes": 9,
        "libelle": ("ligne", 2),
        "cas": None,
        "unite": ("ligne", 10),
        "meta": {},
        "classes": ["3", "4A", "4B"],
    },
}


class ExtractionRefusee(RuntimeError):
    """Raised as soon as a value cannot be established with certainty."""


def _valeur_numerique(feuille, ligne, colonne):
    """Value of a cell if and only if it is numeric.

    Args:
        feuille: Sheet in values mode.
        ligne: Row number.
        colonne: Column number.

    Returns:
        float | None: The value, or `None` for anything else — including text,
        as Excel handles it in an `AVERAGE`.
    """
    brut = feuille.cell(row=ligne, column=colonne).value
    if isinstance(brut, bool) or not isinstance(brut, (int, float)):
        return None
    return float(brut)


def _colonnes_citees(formule):
    """Column letters referenced by a formula.

    Args:
        formule: Excel formula, or any other value.

    Returns:
        list[str]: Letters in order of appearance; empty if not a formula.
    """
    if not isinstance(formule, str) or "(" not in formule:
        return []
    return [
        m.group(1) for m in _REFERENCE_CELLULE.finditer(formule[formule.find("(") + 1 :])
    ]


def _colonnes_dune_plage(formule):
    """Expands ranges in a formula into individual columns.

    `AVERAGE(E10:H10)` references E and H; the actual contributors are E, F,
    G, H. Not expanding would cause the consistency check to fail on tests
    where AVERAGE covers a range (4 and 6) rather than a list (2, 3).

    Args:
        formule: Excel formula.

    Returns:
        list[str] | None: Expanded columns, `None` if no range.
    """
    if not isinstance(formule, str):
        return None
    trouvee = _PLAGE.search(formule)
    if not trouvee:
        return None
    debut = column_index_from_string(trouvee.group(1))
    fin = column_index_from_string(trouvee.group(3))
    return [get_column_letter(c) for c in range(min(debut, fin), max(debut, fin) + 1)]


def _bornes_de_la_moyenne(feuille_formules, ligne, colonne_moyenne):
    """Finds the bound columns by reading the row's formulae.

    Workbooks do NOT place bounds at the same offset: Test 2 puts them at
    mean+1 and +2, Test 5 at +4 and +8, with four interleaved quantities.
    Assuming an offset would give wrong bounds, and for Test 5 the "upper
    bound" would actually be the mean of another quantity.

    The upper bound is therefore identified by its formula `<mean>+MAX(` and
    the lower bound by `<mean>-MAX(`, floor included.

    Args:
        feuille_formules: Sheet in formulas mode.
        ligne: Band row.
        colonne_moyenne: Mean column index.

    Returns:
        tuple[int | None, int | None]: Columns (upper, lower).
    """
    reference = "%s%d" % (get_column_letter(colonne_moyenne), ligne)
    haut = bas = None
    for cellule in feuille_formules[ligne]:
        valeur = cellule.value
        if not isinstance(valeur, str) or "MAX" not in valeur.upper():
            continue
        compact = valeur.replace(" ", "")
        if reference + "+MAX(" in compact:
            haut = cellule.column
        elif reference + "-MAX(" in compact:
            bas = cellule.column
    return haut, bas


def _bandes_du_classeur(feuille_formules, plage_lignes):
    """Locates bands by their AVERAGE formula.

    Args:
        feuille_formules: Sheet in formulas mode.
        plage_lignes: (first, last) row pair to scan.

    Returns:
        list[tuple[int, int]]: (row, mean column) pairs.
    """
    debut, fin = plage_lignes
    trouvees = []
    for rangee in feuille_formules.iter_rows(min_row=debut, max_row=fin):
        for cellule in rangee:
            valeur = cellule.value
            if isinstance(valeur, str) and "AVERAGE" in valeur.upper():
                trouvees.append((cellule.row, cellule.column))
    return sorted(trouvees)


def _controler_coherence(ligne, lettres_moyenne, lettres_haut, colonne_moyenne):
    """Verifies that the MAX covers the same columns as the AVERAGE.

    A discrepancy would mean that the workbook weights the mean and the
    deviation on different sets — a case we refuse to interpret.

    Args:
        ligne: Row number, for the error message.
        lettres_moyenne: Columns referenced by AVERAGE.
        lettres_haut: Columns referenced by the upper bound.
        colonne_moyenne: Mean column index, to exclude.

    Raises:
        ExtractionRefusee: If the two sets differ.
    """
    attendues = set(lettres_moyenne)
    observees = set(lettres_haut) - {get_column_letter(colonne_moyenne)}
    if observees and observees != attendues:
        raise ExtractionRefusee(
            "ligne %d : AVERAGE porte sur %s mais MAX sur %s"
            % (ligne, sorted(attendues), sorted(observees))
        )


def _unite_apres(feuille, ligne, col_libelle, col_moyenne):
    """Unit of a quantity, searched TO THE RIGHT of its label.

    Workbooks do not place it at the same position: Test 2 puts it on the row
    following the label, Test 3 on the SAME row, two columns further. A fixed
    column would give « Mittelwert » as the unit — a silent error in a frozen
    reference dataset.

    Args:
        feuille: Sheet in values mode.
        ligne: Row to search.
        col_libelle: Label column; search starts just after.
        col_moyenne: Mean column, upper bound of the search.

    Returns:
        str | None: First non-empty text value found.
    """
    for colonne in range(col_libelle + 1, max(col_libelle + 2, col_moyenne) + 1):
        valeur = feuille.cell(row=ligne, column=colonne).value
        if isinstance(valeur, str) and valeur.strip():
            return valeur.strip()
    return None


def _etiquette(feuille, origine, ligne, col_moyenne, col_bloc, col_contributeur=None):
    """Reads a label according to the origin declared by the layout.

    Args:
        feuille: Sheet in values mode.
        origine: Pair `('ligne'|'bloc'|'colonne', n)`, or `None`.
        ligne: Band row.
        col_moyenne: Mean column.
        col_bloc: First column of the contributor block.
        col_contributeur: Column of the first contributor. Test 5 carries the
            case name there -- « Test 5A » heads column J, and the
            corresponding mean is in Z, eight columns further, with no header.

    Returns:
        str | None: The label, stripped, or `None`.
    """
    if not origine:
        return None
    genre, indice = origine
    if genre == "ligne":
        valeur = feuille.cell(row=ligne, column=indice).value
    elif genre == "bloc":
        valeur = feuille.cell(row=indice, column=col_bloc).value
    elif genre == "colonne":
        valeur = feuille.cell(row=indice, column=col_moyenne).value
    elif genre == "contributeur" and col_contributeur is not None:
        valeur = feuille.cell(row=indice, column=col_contributeur).value
    elif genre == "cellule":
        valeur = feuille.cell(row=indice[0], column=indice[1]).value
    else:
        return None
    return valeur.strip() if isinstance(valeur, str) else valeur


#: Annual-sum criterion status, per test, **read from the specification**.
#
# This block formerly carried a uniform `INFERE` and this phrase: "only Test 1
# states its criteria in its specification". That is false, and the official
# PDFs say so: the specifications for tests 2, 3 and 5 contain a
# `Testkriterien` section that states the annual band word for word, in the
# same formula the engine applies. The specifications for tests 4 and 6
# contain none — verified by full-text search, zero occurrences — so for them
# `INFERE` remains correct.
#
# This table is deliberately independent of `engine/sia_bandes_engine.py`:
# the frozen reference is the evidence against which the engine is judged; it
# cannot derive from the engine. The two are compared by
# `engine/tests/test_references_bandes.py`, which fails if they diverge.
_CRITERE_ENONCE = "ENONCE_DANS_LA_SPEC"
_CRITERE_INFERE = "INFERE"
_CRITERE_PAR_TEST = {
    2: (
        _CRITERE_ENONCE,
        "Spezifikation_Test2.pdf page 2/2, section « Testkriterien » : "
        "« Jahressumme der solaren Wärmeeinträge oder der total "
        "transmittierten Strahlung: Mittelwert der Referenzprogramme +/- "
        "maximale Abweichung ». La même section énonce aussi le critère de "
        "distribution : « Häufigkeitsverteilung … muss im Streubereich der "
        "Referenzprogramme liegen ».",
    ),
    3: (
        _CRITERE_ENONCE,
        "Spezifikation_Test3.pdf page 3/3, section « Testkriterien » : "
        "« Jahressumme: Mittelwert +/- max. Abweichung der "
        "Referenzprogramme », suivie de « Häufigkeitsverteilung innerhalb des "
        "Streubereichs der Referenzprogramme ».",
    ),
    5: (
        _CRITERE_ENONCE,
        "Spezifikation_Test5.pdf page 5/5, section « Testkriterien » : "
        "« Zulässiger Bereich für Jahressummen: Mittelwerte der "
        "Referenzprogramme +/- maximale Abweichung. Die "
        "Häufigkeitsverteilungen müssen im Streubereich der "
        "Referenzprogramme liegen. »",
    ),
}
_CRITERE_DELEGUE = (
    "La spécification de ce test ne comporte aucune section « Testkriterien » "
    "(recherche plein texte : zéro occurrence). SIA 4010:2023 §4.4 délègue "
    "alors la comparaison au classeur d'évaluation, qui porte les bandes. À "
    "confirmer par la sous-commission (§4.6.2)."
)


def _critere_du_test(numero_test):
    """Returns the `critere` block for a test, including status and origin.

    Args:
        numero_test: SIA test number.

    Returns:
        dict: Formula, status and sourced origin.
    """

    statut, origine = _CRITERE_PAR_TEST.get(
        numero_test, (_CRITERE_INFERE, _CRITERE_DELEGUE)
    )
    return {
        "formule": "moyenne ± MAX(ABS(programme − moyenne)), bornes incluses",
        "statut": statut,
        "origine": origine,
    }


def extraire(numero_test):
    """Extracts and verifies all bands for a test.

    Args:
        numero_test: SIA test number, e.g. 2.

    Returns:
        dict: Frozen structure, ready to write.

    Raises:
        ExtractionRefusee: On the first discrepancy with the workbook.
    """
    if numero_test not in DISPOSITIONS:
        raise ExtractionRefusee(
            "disposition inconnue pour le test %s ; connues : %s"
            % (numero_test, sorted(DISPOSITIONS))
        )
    plan = DISPOSITIONS[numero_test]
    chemin = os.path.join(_DOSSIER_SIA, plan["fichier"])
    if not os.path.exists(chemin):
        raise ExtractionRefusee("classeur introuvable : %s" % chemin)

    sf = openpyxl.load_workbook(chemin, data_only=False)[plan["feuille"]]
    sv = openpyxl.load_workbook(chemin, data_only=True)[plan["feuille"]]

    par_bloc = {}
    for ligne, col_moy in _bandes_du_classeur(sf, plan["lignes"]):
        col_haut, col_bas = _bornes_de_la_moyenne(sf, ligne, col_moy)
        if col_haut is None or col_bas is None:
            raise ExtractionRefusee(
                "ligne %d col %s : bornes introuvables -- aucune formule ne "
                "reference cette moyenne avec un MAX"
                % (ligne, get_column_letter(col_moy))
            )

        formule_moy = sf.cell(row=ligne, column=col_moy).value
        citees = _colonnes_dune_plage(formule_moy) or _colonnes_citees(formule_moy)
        # Range OR list, Excel ignores non-numeric cells in an AVERAGE --
        # typically a string like « ='Daten EnergyPlus'!G11 » left there by
        # the SIA to flag a programme that did not submit. The actual
        # contributors are therefore the NUMERIC cells referenced, which is
        # exactly what the MAX list enumerates on its side.
        lettres = [
            column_letter
            for column_letter in citees
            if _valeur_numerique(sv, ligne, column_index_from_string(column_letter))
            is not None
        ]
        if not lettres:
            raise ExtractionRefusee(
                "ligne %d col %s : contributeurs illisibles"
                % (ligne, get_column_letter(col_moy))
            )
        _controler_coherence(
            ligne,
            lettres,
            _colonnes_citees(sf.cell(row=ligne, column=col_haut).value),
            col_moy,
        )

        contributions, par_colonne = [], {}
        for lettre in lettres:
            colonne = column_index_from_string(lettre)
            valeur = _valeur_numerique(sv, ligne, colonne)
            if valeur is None:
                raise ExtractionRefusee(
                    "ligne %d colonne %s : contributeur déclaré mais valeur "
                    "non numérique" % (ligne, lettre)
                )
            contributions.append(valeur)
            par_colonne[lettre] = {
                "valeur": valeur,
                "programme": sv.cell(row=plan["ligne_programmes"], column=colonne).value,
                "variante": sv.cell(row=plan["ligne_variantes"], column=colonne).value,
            }

        plancher = bool(
            _PLANCHER.match(str(sf.cell(row=ligne, column=col_bas).value or ""))
        )
        bande = scatter_band.build_band(contributions, floor_at_zero=plancher)

        for nom, colonne, obtenu in (
            ("moyenne", col_moy, bande.mean),
            ("haut", col_haut, bande.upper_bound),
            ("bas", col_bas, bande.lower_bound),
        ):
            reference = sv.cell(row=ligne, column=colonne).value
            if not isinstance(reference, (int, float)):
                raise ExtractionRefusee(
                    "ligne %d : %s non mis en cache par le classeur" % (ligne, nom)
                )
            if abs(float(reference) - obtenu) > TOLERANCE:
                raise ExtractionRefusee(
                    "ligne %d, %s : classeur %.10f, recalcul %.10f"
                    % (ligne, nom, reference, obtenu)
                )

        col_premier = min(
            column_index_from_string(column_letter) for column_letter in lettres
        )
        col_bloc = col_premier - 1
        libelle = _etiquette(sv, plan["libelle"], ligne, col_moy, col_bloc, col_premier)
        nom_cas = _etiquette(sv, plan["cas"], ligne, col_moy, col_bloc, col_premier)
        unite = _etiquette(sv, plan["unite"], ligne, col_moy, col_bloc, col_premier)

        entree = {
            "ligne_classeur": ligne,
            "colonne_moyenne": get_column_letter(col_moy),
            "cas": nom_cas if nom_cas else "(ensemble)",
            "contributeurs": lettres,
            "par_colonne": par_colonne,
            "moyenne": bande.mean,
            "borne_haute": bande.upper_bound,
            "borne_basse": bande.lower_bound,
            "ecart_max": bande.max_deviation,
            "plancher_a_zero": plancher,
        }
        for nom_meta, colonne_meta in plan["meta"].items():
            valeur = sv.cell(row=ligne, column=colonne_meta).value
            entree[nom_meta] = valeur.strip() if isinstance(valeur, str) else valeur
        par_bloc.setdefault((libelle, unite), []).append(entree)

    # Grouping by (label, unit): that is the quantity, regardless of how the
    # workbook presents it -- as a column block or as a row.
    grandeurs = []
    for cle in sorted(par_bloc, key=lambda c: ("%s" % c[0], "%s" % c[1])):
        libelle, unite = cle
        grandeurs.append(
            {
                "libelle_de": libelle,
                "unite": unite,
                "cas": par_bloc[cle],
            }
        )

    return {
        "test": numero_test,
        "classes_concernees": plan["classes"],
        "statut": "FIGÉ — bandes recalculées et confrontées au classeur",
        "date_extraction": "2026-08-06",
        "source": {
            "fichier": "SIA_4010_geteilter_Link/" + plan["fichier"].replace("\\", "/"),
            "feuille": plan["feuille"],
        },
        "critere": _critere_du_test(numero_test),
        "piege_variantes": (
            "Les colonnes sont des VARIANTES de programme, pas des programmes. "
            "Le SIA retient une variante par programme, et pas la même d'un "
            "programme à l'autre : le jeu contributeur est lu sur la formule."
        ),
        "grandeurs": grandeurs,
    }


def main(arguments):
    """Command-line entry point.

    Args:
        arguments: Arguments excluding the script name.

    Returns:
        int: 0 if everything went well.
    """
    numeros = [int(a) for a in arguments if a.isdigit()]
    if not numeros:
        print("usage : python scripts/build_sia_reference.py <N> [--ecrire]")
        print("  tests disponibles : %s" % sorted(DISPOSITIONS))
        return 1

    for numero in numeros:
        donnees = extraire(numero)
        total = sum(len(g["cas"]) for g in donnees["grandeurs"])
        print(
            "Test %d — %d grandeur(s), %d bande(s)"
            % (numero, len(donnees["grandeurs"]), total)
        )
        for grandeur in donnees["grandeurs"]:
            print()
            print("  %s [%s]" % (grandeur["libelle_de"], grandeur["unite"]))
            for entree in grandeur["cas"]:
                print(
                    "    %-12s %10.1f  (%10.1f … %10.1f)  %s%s"
                    % (
                        entree.get("cas") or "?",
                        entree["moyenne"],
                        entree["borne_basse"],
                        entree["borne_haute"],
                        "".join(entree["contributeurs"]),
                        "  [plancher 0]" if entree["plancher_a_zero"] else "",
                    )
                )
        print()
        print("  toutes les bandes concordent (tol. %g)" % TOLERANCE)

        if "--ecrire" in arguments:
            sortie = os.path.join(
                _RACINE, "refs", "reference-data", "test-%d.ref.json" % numero
            )
            with io.open(sortie, "w", encoding="utf-8") as flux:
                flux.write(json.dumps(donnees, ensure_ascii=False, indent=2))
                flux.write("\n")
            print("  écrit : %s" % os.path.relpath(sortie, _RACINE))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
