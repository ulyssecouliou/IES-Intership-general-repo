# -*- coding: utf-8 -*-
"""Freezes the Test 7 reference values (validation class 5).

SOURCE: `SIA_4010_geteilter_Link/Test7/Resultaterfassung Test7.xlsx`,
sheet `Zusammenfassung`, as delivered by SIA.

LAYOUT READ, not assumed:
    row 6    : programme names — F = Testprogramm (us), then
               G = IDA ICE, H = Excel, I = Energy+/OpenStudio, J = EDSL Tas
    row 7    : versions; K = unit, L = Mittelwert, M = Obere Grenze,
               N = Untere Grenze
    rows 8-12  : quantities in COOLING mode
    rows 14-18 : quantities in HEATING mode
    row 20   : PV-Ertrag
    rows 21-26 : Diagnosegrössen — WITHOUT band (L/M/N empty)

TWO TRAPS, handled explicitly.

1. **The contributor set varies row by row.** `M8` excludes `I8`, `M14`
   excludes `J14`: a programme that has not delivered a quantity drops out of
   the band and is never counted as zero. The authoritative set is the one in
   the `MAX(ABS(...))` list, NOT the `AVERAGE` range — the `AVERAGE` covers a
   `G:J` range from which Excel drops blanks at evaluation, which is equivalent
   but not statically readable.

2. **Some cells contain TEXT that looks like a formula.**
   `I8`, `I10`, `I11`, `J14`, `J17`, `J18`, `J20` carry the string
   `='Daten EnergyPlus'!G6` — but in the XML they are marked `t="s"`,
   i.e. **shared string**, not a formula (`<f>` absent). Excel therefore
   treats them as text, and `AVERAGE` ignores them: that is exactly how
   SIA excluded those programmes.

   Correction applied on 2026-08-06 after independent audit: an earlier
   version of this script **dereferenced** those strings and wrote the
   resulting number into `par_programme`, creating the false impression that
   the programme had delivered a value when the workbook excludes it. The
   bands remained correct — contributors are read from the `MAX(ABS(...))` list,
   which does not mention them — but the JSON was misleading.
   **We no longer dereference anything: a string equals `None`, as in Excel.**

CHECK: each band is RECALCULATED by `engine.scatter_band` and compared against
the L/M/N triplet from the workbook. Any single discrepancy and the script fails.
This is proof that our engine reproduces the SIA acceptance criterion.

Usage:
    python scripts/build_test7_reference.py [--ecrire]
"""

from __future__ import print_function

import io
import hashlib
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
    "SIA_4010_DOSSIER", os.path.join(_RACINE, "SIA_4010_geteilter_Link")
)
_CLASSEUR = os.path.join(_DOSSIER_SIA, "Test7", "Resultaterfassung Test7.xlsx")
_SORTIE = os.path.join(_RACINE, "refs", "reference-data", "test-7.ref.json")

FEUILLE = "Zusammenfassung"
LIGNE_PROGRAMMES = 6
LIGNE_VERSIONS = 7
COL_LIBELLE = 2  # B
COL_GROUPE = 1  # A
COL_PROGRAMMES = (7, 8, 9, 10)  # G, H, I, J
COL_NOTRE = 6  # F — Testprogramm, empty until VE has run
COL_UNITE = 11  # K
COL_MOYENNE = 12  # L
COL_HAUT = 13  # M
COL_BAS = 14  # N

# Recalculation tolerance. Workbook values are at full precision;
# this threshold absorbs only binary rounding.
TOLERANCE = 1e-6

_CONTRIB = re.compile(r"ABS\(\s*([A-Z]+)(\d+)\s*-")
_PLANCHER = re.compile(r"^=\s*MAX\(\s*0\s*,", re.I)


def _sha256(chemin):
    h = hashlib.sha256()
    with open(chemin, "rb") as flux:
        for bloc in iter(lambda: flux.read(1024 * 1024), b""):
            h.update(bloc)
    return h.hexdigest()


class ExtractionRefusee(RuntimeError):
    pass


def _valeur_numerique(valeurs, feuille, ligne, colonne):
    """Value of a cell if and only if it is numeric.

    Anything else — text, blank cell, string resembling a formula —
    returns `None`, exactly as Excel treats it in an `AVERAGE`. We dereference
    NOTHING: a string `='Daten EnergyPlus'!G6` marked `t="s"` is text, not a
    reference, and converting it to a number would invent a value the workbook
    deliberately excludes (see trap 2 in the module header).
    """
    brut = valeurs[feuille].cell(row=ligne, column=colonne).value
    if isinstance(brut, bool):
        return None
    if isinstance(brut, (int, float)):
        return float(brut)
    return None


def _contributeurs(formule_haut):
    """Contributing columns, read from the MAX(ABS(...)) list of the upper bound."""
    if not isinstance(formule_haut, str):
        return []
    return [m.group(1) for m in _CONTRIB.finditer(formule_haut)]


def extraire():
    if not os.path.exists(_CLASSEUR):
        raise ExtractionRefusee("classeur introuvable : %s" % _CLASSEUR)

    formules = openpyxl.load_workbook(_CLASSEUR, data_only=False)
    caches = openpyxl.load_workbook(_CLASSEUR, data_only=True)
    valeurs = dict(
        (n, caches[n]) for n in caches.sheetnames if hasattr(caches[n], "cell")
    )

    sf = formules[FEUILLE]
    sv = caches[FEUILLE]

    programmes = [sv.cell(row=LIGNE_PROGRAMMES, column=c).value for c in COL_PROGRAMMES]
    versions = [sv.cell(row=LIGNE_VERSIONS, column=c).value for c in COL_PROGRAMMES]

    from openpyxl.utils import get_column_letter

    lettre_de = dict((get_column_letter(c), c) for c in COL_PROGRAMMES)

    grandeurs, groupe_courant = [], None
    for ligne in range(8, 31):
        etiquette_groupe = sv.cell(row=ligne, column=COL_GROUPE).value
        if isinstance(etiquette_groupe, str) and etiquette_groupe.strip():
            groupe_courant = etiquette_groupe.strip()

        formule_moyenne = sf.cell(row=ligne, column=COL_MOYENNE).value
        if not (
            isinstance(formule_moyenne, str) and "AVERAGE" in formule_moyenne.upper()
        ):
            continue  # pas de bande sur cette ligne (Diagnosegrössen)

        libelle = sv.cell(row=ligne, column=COL_LIBELLE).value
        if not libelle:
            continue

        formule_haut = sf.cell(row=ligne, column=COL_HAUT).value
        formule_bas = sf.cell(row=ligne, column=COL_BAS).value
        lettres = _contributeurs(formule_haut)
        if not lettres:
            raise ExtractionRefusee(
                "ligne %d : contributeurs illisibles dans %r" % (ligne, formule_haut)
            )

        par_programme, contributions = {}, []
        for lettre in lettres:
            colonne = lettre_de.get(lettre)
            if colonne is None:
                raise ExtractionRefusee(
                    "ligne %d : colonne contributrice %s hors G-J" % (ligne, lettre)
                )
            v = _valeur_numerique(valeurs, FEUILLE, ligne, colonne)
            if v is None:
                raise ExtractionRefusee(
                    "ligne %d colonne %s : contributeur déclaré mais valeur "
                    "non numérique — extraction refusée plutôt que devinée"
                    % (ligne, lettre)
                )
            contributions.append(v)

        for indice, colonne in enumerate(COL_PROGRAMMES):
            par_programme[programmes[indice]] = _valeur_numerique(
                valeurs, FEUILLE, ligne, colonne
            )

        plancher = bool(_PLANCHER.match(str(formule_bas or "")))
        bande = scatter_band.build_band(contributions, floor_at_zero=plancher)

        attendu = dict(
            (nom, sv.cell(row=ligne, column=col).value)
            for nom, col in (
                ("moyenne", COL_MOYENNE),
                ("haut", COL_HAUT),
                ("bas", COL_BAS),
            )
        )
        for nom, obtenu in (
            ("moyenne", bande.mean),
            ("haut", bande.upper_bound),
            ("bas", bande.lower_bound),
        ):
            reference = attendu[nom]
            if not isinstance(reference, (int, float)):
                raise ExtractionRefusee(
                    "ligne %d : %s non mis en cache par le classeur" % (ligne, nom)
                )
            if abs(float(reference) - obtenu) > TOLERANCE:
                raise ExtractionRefusee(
                    "ligne %d, %s : classeur %.10f, recalcul %.10f"
                    % (ligne, nom, reference, obtenu)
                )

        grandeurs.append(
            {
                "ligne_classeur": ligne,
                "groupe": groupe_courant,
                "libelle_de": str(libelle).strip(),
                "unite": sv.cell(row=ligne, column=COL_UNITE).value,
                "par_programme": par_programme,
                "contributeurs": lettres,
                "contributeurs_noms": [
                    programmes[COL_PROGRAMMES.index(lettre_de[column_letter])]
                    for column_letter in lettres
                ],
                "moyenne": bande.mean,
                "borne_haute": bande.upper_bound,
                "borne_basse": bande.lower_bound,
                "ecart_max": bande.max_deviation,
                "plancher_a_zero": plancher,
            }
        )

    return {
        "test": 7,
        "classe_de_validation": "5 — SIA 4010:2023 tableau 63 : le Test 7 est "
        "le seul test exigé par la classe 5",
        "statut": "FIGÉ — bandes recalculées et confrontées au classeur",
        "date_extraction": "2026-08-10",
        "source": {
            "fichier": "SIA_4010_geteilter_Link/Test7/Resultaterfassung Test7.xlsx",
            "sha256": _sha256(_CLASSEUR),
            "correction": "Règle conditionnelle N (borne basse) à M (borne haute)",
            "feuille": FEUILLE,
            "programmes": programmes,
            "versions": versions,
        },
        "critere": {
            "formule": "moyenne ± MAX(ABS(programme − moyenne)), bornes incluses",
            "origine": "formules L/M/N du classeur, lues verbatim",
            "plancher_a_zero": "présent ligne par ligne (MAX(0,…)), jamais par défaut",
            "contributeurs": "lus sur la liste MAX(ABS(...)) de la borne haute ; "
            "le jeu VARIE d'une grandeur à l'autre",
        },
        "grandeurs": grandeurs,
        "reserve_pv": "La grandeur « PV-Ertrag » porte une bande : c'est une "
        "Testgrösse obligatoire. Elle exige l'irradiance sur le "
        "plan des modules, absente de toute source officielle à "
        "ce jour. Cf. traceability/classes-de-validation.spec.md.",
    }


def main():
    donnees = extraire()
    print("Test 7 — %d grandeurs à bande extraites" % len(donnees["grandeurs"]))
    print("programmes : %s" % ", ".join(str(p) for p in donnees["source"]["programmes"]))
    print()
    print("%-46s %10s %10s %10s  %s" % ("grandeur", "moyenne", "bas", "haut", "contrib."))
    print("-" * 100)
    for g in donnees["grandeurs"]:
        print(
            "%-46s %10.1f %10.1f %10.1f  %s%s"
            % (
                g["libelle_de"][:46],
                g["moyenne"],
                g["borne_basse"],
                g["borne_haute"],
                "".join(g["contributeurs"]),
                "  [plancher 0]" if g["plancher_a_zero"] else "",
            )
        )
    print()
    print(
        "toutes les bandes recalculées concordent avec le classeur (tol. %g)" % TOLERANCE
    )

    if "--ecrire" in sys.argv:
        with io.open(_SORTIE, "w", encoding="utf-8") as f:
            f.write(json.dumps(donnees, ensure_ascii=False, indent=2))
            f.write("\n")
        print("écrit : %s" % os.path.relpath(_SORTIE, _RACINE))


if __name__ == "__main__":
    main()
