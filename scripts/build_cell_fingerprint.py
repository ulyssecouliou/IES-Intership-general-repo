# -*- coding: utf-8 -*-
"""Generates the raw-cell fingerprint of the Test 1 evaluation workbook.

WHY THIS FILE EXISTS
--------------------
The two strongest checks in `engine/tests/test_ref_integrity.py` --
value<->cell fidelity and label<->column matching -- require the official
workbook. It weighs 14 MB (130 MB for all seven) and is kept out of the
repository. In CI it is therefore absent, and mutation testing proved it:

    injected mutation                              with workbook   without workbook
    column shift (+1), Table 30                      detected      NOT DETECTED
    phantom case "600" in Table 32                   detected        detected
    Excel error converted to 0                       detected      NOT DETECTED
    wrong Streubereich formula (min/max)             detected        detected

In other words, CI could not catch the class of bug that actually occurred
(see AUDIT.md, defects no. 1 and no. 3).

WHAT THE FINGERPRINT SOLVES
----------------------------
It freezes the RAW cells (address -> value as-is, Excel errors included)
plus the header rows, in a few dozen KB that can be versioned.
The test uses it as a substitute for the workbook when the latter is absent.

This is NOT circular: the fingerprint contains the raw values, while
`test-1.ref.json` contains their INTERPRETATION (which programme, which
quantity, which column). The interpretation is what was wrong in defects no. 1
and no. 2, not the values. And when the workbook is present, the test checks
the fingerprint AGAINST it, so it cannot silently drift.

USAGE
-----
    python scripts/build_cell_fingerprint.py

Re-run after any regeneration of `test-1.ref.json`. The test fails pointing
to this file if the fingerprint no longer covers all the cells it cites.
"""

import collections
import hashlib
import json
import os
import sys

import openpyxl

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_JSON = os.path.join(RACINE, "refs", "reference-data", "test-1.ref.json")
EMPREINTE = os.path.join(RACINE, "refs", "reference-data", "test-1.cells.json")
CLASSEUR = os.path.join(
    RACINE, "SIA_4010_geteilter_Link", "Test1", "Resultaterfassung_Test1.xlsx"
)
FEUILLE = "Zusammenfassung Testf\xe4lle"

# Header rows of the extracted tables, reconstructed against the source and
# confirmed by the independent audit (AUDIT.md).
LIGNES_ENTETE = (15, 36, 57, 81, 104)


def _cellules_citees(reference):
    """Return every source-cell address cited by the reference JSON."""
    adresses = set()

    def parcourir(noeud):
        """Recursively collect cited cell addresses from one JSON node."""

        if isinstance(noeud, dict):
            if "value" in noeud and "cell" in noeud:
                adresses.add(noeud["cell"])
                return
            for valeur in noeud.values():
                parcourir(valeur)

    parcourir(reference["reference_values"])
    return adresses


def main():
    """Generate the immutable Test 1 workbook-cell fingerprint."""

    if not os.path.exists(CLASSEUR):
        sys.stderr.write(
            "Classeur source absent : " + CLASSEUR + "\n"
            "L'empreinte ne peut etre generee que depuis la source figee.\n"
        )
        return 1

    with open(REF_JSON, encoding="utf-8") as flux:
        reference = json.load(flux)
    adresses = _cellules_citees(reference)

    with open(CLASSEUR, "rb") as flux:
        somme = hashlib.sha256(flux.read()).hexdigest()

    classeur = openpyxl.load_workbook(CLASSEUR, data_only=True)
    feuille = classeur[FEUILLE]

    cellules = collections.OrderedDict()
    for adresse in sorted(adresses, key=lambda a: (len(a), a)):
        valeur = feuille[adresse].value
        # Excel errors are kept as-is ('#DIV/0!'): that is exactly what
        # distinguishes a real error from an invented zero.
        cellules[adresse] = valeur

    entetes = collections.OrderedDict()
    for ligne in LIGNES_ENTETE:
        colonnes = collections.OrderedDict()
        for cellule in feuille[ligne]:
            if cellule.value is not None:
                colonnes[cellule.column_letter] = str(cellule.value)
        entetes[str(ligne)] = colonnes
    classeur.close()

    empreinte = collections.OrderedDict(
        [
            (
                "_comment",
                "Cellules BRUTES du classeur officiel, figees pour que la CI puisse "
                "verifier test-1.ref.json sans les 14 Mo du .xlsx. Genere par "
                "scripts/build_cell_fingerprint.py -- ne pas editer a la main.",
            ),
            (
                "source",
                collections.OrderedDict(
                    [
                        (
                            "file",
                            "SIA_4010_geteilter_Link/Test1/Resultaterfassung_Test1.xlsx",
                        ),
                        ("sheet", FEUILLE),
                        ("sha256", somme),
                    ]
                ),
            ),
            ("reference_status", reference.get("status")),
            ("header_rows", entetes),
            ("cells", cellules),
        ]
    )

    with open(EMPREINTE, "w", encoding="utf-8") as flux:
        json.dump(empreinte, flux, ensure_ascii=False, indent=1, sort_keys=False)

    taille = os.path.getsize(EMPREINTE)
    erreurs = sum(1 for v in cellules.values() if isinstance(v, str))
    print("Empreinte ecrite : {0}".format(EMPREINTE))
    print("  cellules      : {0}".format(len(cellules)))
    print("  dont erreurs Excel conservees : {0}".format(erreurs))
    print(
        "  lignes d en-tete : {0}".format(
            ", ".join(str(line_number) for line_number in LIGNES_ENTETE)
        )
    )
    print("  taille        : {0} Ko".format(taille // 1024))
    print("  sha256 source : {0}".format(somme[:16] + "..."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
