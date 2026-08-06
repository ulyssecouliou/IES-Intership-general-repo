# -*- coding: utf-8 -*-
"""Genere l'empreinte de cellules brutes du classeur d'evaluation du Test 1.

POURQUOI CE FICHIER EXISTE
--------------------------
Les deux controles les plus forts de `engine/tests/test_ref_integrity.py` --
fidelite valeur<->cellule et correspondance libelle<->colonne -- exigent le
classeur officiel. Celui-ci pese 14 Mo (130 Mo pour les sept) et reste hors
depot. En CI il est donc absent, et la mesure par mutation l'a prouve :

    mutation injectee                          avec classeur   sans classeur
    decalage de colonnes (+1), Table 30            detectee      NON DETECTEE
    cas fantome "600" en Table 32                  detectee        detectee
    erreur Excel convertie en 0                    detectee      NON DETECTEE
    fausse formule Streubereich (min/max)          detectee        detectee

Autrement dit, la CI ne pouvait pas attraper la classe de bug qui s'est
reellement produite (cf. AUDIT.md, defauts n 1 et n 3).

CE QUE L'EMPREINTE RESOUT
-------------------------
Elle fige les cellules BRUTES (adresse -> valeur telle quelle, erreurs Excel
comprises) plus les lignes d'en-tete, en quelques dizaines de Ko versionnables.
Le test s'en sert comme substitut du classeur quand celui-ci est absent.

Ce n'est PAS circulaire : l'empreinte contient les valeurs brutes, le
`test-1.ref.json` contient leur INTERPRETATION (quel programme, quelle grandeur,
quelle colonne). C'est l'interpretation qui etait fausse dans les defauts n 1
et n 2, pas les valeurs. Et quand le classeur est present, le test verifie
l'empreinte CONTRE lui, donc elle ne peut pas deriver en silence.

USAGE
-----
    python scripts/build_cell_fingerprint.py

A relancer apres toute regeneration de `test-1.ref.json`. Le test echoue en
signalant ce fichier si l'empreinte ne couvre plus toutes les cellules citees.
"""

import collections
import hashlib
import json
import os
import sys

import openpyxl

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_JSON = os.path.join(RACINE, 'refs', 'reference-data', 'test-1.ref.json')
EMPREINTE = os.path.join(RACINE, 'refs', 'reference-data', 'test-1.cells.json')
CLASSEUR = os.path.join(RACINE, 'SIA_4010_geteilter_Link', 'Test1',
                        'Resultaterfassung_Test1.xlsx')
FEUILLE = u'Zusammenfassung Testf\xe4lle'

# Lignes d'en-tete des tables extraites, reconstruites contre la source et
# confirmees par l'audit independant (AUDIT.md).
LIGNES_ENTETE = (15, 36, 57, 81, 104)


def _cellules_citees(reference):
    """Toutes les adresses {value, cell} presentes dans le JSON de reference."""
    adresses = set()

    def parcourir(noeud):
        if isinstance(noeud, dict):
            if 'value' in noeud and 'cell' in noeud:
                adresses.add(noeud['cell'])
                return
            for valeur in noeud.values():
                parcourir(valeur)

    parcourir(reference['reference_values'])
    return adresses


def main():
    if not os.path.exists(CLASSEUR):
        sys.stderr.write('Classeur source absent : ' + CLASSEUR + '\n'
                         "L'empreinte ne peut etre generee que depuis la source figee.\n")
        return 1

    with open(REF_JSON, encoding='utf-8') as flux:
        reference = json.load(flux)
    adresses = _cellules_citees(reference)

    with open(CLASSEUR, 'rb') as flux:
        somme = hashlib.sha256(flux.read()).hexdigest()

    classeur = openpyxl.load_workbook(CLASSEUR, data_only=True)
    feuille = classeur[FEUILLE]

    cellules = collections.OrderedDict()
    for adresse in sorted(adresses, key=lambda a: (len(a), a)):
        valeur = feuille[adresse].value
        # Les erreurs Excel sont conservees telles quelles ('#DIV/0!') : c'est
        # exactement ce qui distingue une erreur d'un zero invente.
        cellules[adresse] = valeur

    entetes = collections.OrderedDict()
    for ligne in LIGNES_ENTETE:
        colonnes = collections.OrderedDict()
        for cellule in feuille[ligne]:
            if cellule.value is not None:
                colonnes[cellule.column_letter] = str(cellule.value)
        entetes[str(ligne)] = colonnes
    classeur.close()

    empreinte = collections.OrderedDict([
        ('_comment',
         "Cellules BRUTES du classeur officiel, figees pour que la CI puisse "
         "verifier test-1.ref.json sans les 14 Mo du .xlsx. Genere par "
         "scripts/build_cell_fingerprint.py -- ne pas editer a la main."),
        ('source', collections.OrderedDict([
            ('file', 'SIA_4010_geteilter_Link/Test1/Resultaterfassung_Test1.xlsx'),
            ('sheet', FEUILLE),
            ('sha256', somme),
        ])),
        ('reference_status', reference.get('status')),
        ('header_rows', entetes),
        ('cells', cellules),
    ])

    with open(EMPREINTE, 'w', encoding='utf-8') as flux:
        json.dump(empreinte, flux, ensure_ascii=False, indent=1, sort_keys=False)

    taille = os.path.getsize(EMPREINTE)
    erreurs = sum(1 for v in cellules.values() if isinstance(v, str))
    print('Empreinte ecrite : {0}'.format(EMPREINTE))
    print('  cellules      : {0}'.format(len(cellules)))
    print("  dont erreurs Excel conservees : {0}".format(erreurs))
    print('  lignes d en-tete : {0}'.format(', '.join(str(l) for l in LIGNES_ENTETE)))
    print('  taille        : {0} Ko'.format(taille // 1024))
    print('  sha256 source : {0}'.format(somme[:16] + '...'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
