# -*- coding: utf-8 -*-
"""Extracts text from a PDF while respecting the STRUCTURE of its tables.

WHY THIS TOOL EXISTS
--------------------
`pdftotext -layout` guesses the layout from whitespace, and it fails on dense
tables. This project has already suffered the consequences twice:

  * ASHRAE 140:2023, Informative Table 7-11: values offset by one row relative
    to their labels. The table had to be rebuilt from the arithmetic the
    standard gave in a note to resolve the ambiguity (U = 2.10 W/(m2K)).
  * `Spezifikation_Test4.pdf` / `_Test5.pdf`, section `Sollwerte`: the
    set-point temperature value does not appear ANYWHERE in either text
    extraction, even though the label `Raumlufttemperatur` is present. A
    normative value that disappears silently is exactly the kind of defect
    this project must make impossible.

On a table of material properties or set-points, a misattributed column
produces a model that is wrong AND plausible, invisible downstream.

HOW
---
PyMuPDF returns each word with its bounding box. Words are grouped into lines
by their y-coordinate, then sorted by x-coordinate, and significant horizontal
gaps are flagged with a column separator. Nothing is guessed: the position
comes from the file.

Usage :
    python scripts/pdf_table_cells.py <fichier.pdf> [page] [--motif REGEX]

    page   : 1-based page number; all if omitted
    --motif: show only lines matching this pattern (case-insensitive),
             with two context lines on each side
"""

import re
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.stderr.write("PyMuPDF absent : python -m pip install pymupdf\n")
    raise SystemExit(1)

# Two words whose vertical baselines differ by less than this belong to the
# same line. 3 typographic points tolerate small rendering offsets without
# merging distinct lines.
TOLERANCE_LIGNE_PT = 3.0
# A horizontal gap wider than this separates two cells rather than two words.
ECART_COLONNE_PT = 12.0


def lignes_de_page(page):
    """Returns [[(x, text), ...], ...]: words grouped into lines, sorted."""
    mots = page.get_text("words")  # (x0, y0, x1, y1, mot, bloc, ligne, n)
    groupes = []
    for x0, y0, x1, _y1, mot, _b, _l, _n in sorted(mots, key=lambda m: (m[1], m[0])):
        for groupe in groupes:
            if abs(groupe["y"] - y0) <= TOLERANCE_LIGNE_PT:
                groupe["mots"].append((x0, x1, mot))
                break
        else:
            groupes.append({"y": y0, "mots": [(x0, x1, mot)]})
    lignes = []
    for groupe in sorted(groupes, key=lambda g: g["y"]):
        lignes.append(sorted(groupe["mots"], key=lambda m: m[0]))
    return lignes


def rendre_ligne(mots):
    """Assembles a line by inserting ' | ' at column breaks."""
    morceaux, precedent_fin = [], None
    for x0, x1, mot in mots:
        if precedent_fin is not None and (x0 - precedent_fin) > ECART_COLONNE_PT:
            morceaux.append("|")
        morceaux.append(mot)
        precedent_fin = x1
    return " ".join(morceaux)


def main():
    if len(sys.argv) < 2:
        sys.stderr.write(__doc__.split("Usage :")[-1] + "\n")
        return 1
    chemin = sys.argv[1]
    page_demandee = None
    motif = None
    reste = sys.argv[2:]
    while reste:
        argument = reste.pop(0)
        if argument == "--motif" and reste:
            motif = re.compile(reste.pop(0), re.IGNORECASE)
        elif argument.isdigit():
            page_demandee = int(argument)

    document = fitz.open(chemin)
    print("%s : %d page(s)" % (chemin.split("\\")[-1], document.page_count))
    for numero in range(document.page_count):
        if page_demandee is not None and numero + 1 != page_demandee:
            continue
        lignes = [rendre_ligne(mots) for mots in lignes_de_page(document[numero])]
        print("")
        print("=== page %d : %d ligne(s) ===" % (numero + 1, len(lignes)))
        if motif is None:
            for index, texte in enumerate(lignes, 1):
                print("%4d  %s" % (index, texte))
            continue
        retenues = set()
        for index, texte in enumerate(lignes):
            if motif.search(texte):
                retenues.update(range(max(0, index - 2), min(len(lignes), index + 3)))
        precedent = None
        for index in sorted(retenues):
            if precedent is not None and index != precedent + 1:
                print("      ...")
            marque = ">>" if motif.search(lignes[index]) else "  "
            print("%s%4d  %s" % (marque, index + 1, lignes[index]))
            precedent = index
    document.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
