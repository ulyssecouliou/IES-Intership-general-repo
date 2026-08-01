# -*- coding: utf-8 -*-
"""Extrait le texte d'un PDF en respectant la STRUCTURE des tableaux.

POURQUOI CET OUTIL EXISTE
-------------------------
`pdftotext -layout` devine la mise en page a partir d'espaces, et il se trompe
sur les tableaux denses. Ce projet en a deja subi les consequences deux fois :

  * ASHRAE 140:2023, Informative Table 7-11 : valeurs decalees d'une ligne par
    rapport a leurs libelles. Il a fallu reconstruire la table par l'arithmetique
    que la norme donnait en note pour lever le doute (U = 2.10 W/(m2K)).
  * `Spezifikation_Test4.pdf` / `_Test5.pdf`, rubrique `Sollwerte` : la valeur de
    consigne de temperature n'apparait NULLE PART dans les deux extractions
    texte, alors que le libelle `Raumlufttemperatur` est bien present. Une
    valeur normative qui disparait silencieusement est exactement le genre de
    defaut que ce projet doit rendre impossible.

Sur un tableau de proprietes de materiaux ou de consignes, une colonne mal
attribuee produit un modele faux ET plausible, invisible en aval.

COMMENT
-------
PyMuPDF rend chaque mot avec sa boite englobante. On regroupe donc les mots en
lignes par leur ordonnee, puis on les ordonne par abscisse, et on signale les
sauts horizontaux importants par un separateur de colonne. Rien n'est devine :
la position vient du fichier.

Usage :
    python scripts/pdf_table_cells.py <fichier.pdf> [page] [--motif REGEX]

    page   : numero de page 1-based ; toutes si omis
    --motif: ne montre que les lignes contenant ce motif (insensible a la casse),
             avec deux lignes de contexte de part et d'autre
"""

import re
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.stderr.write('PyMuPDF absent : python -m pip install pymupdf\n')
    raise SystemExit(1)

# Deux mots dont les bases verticales different de moins de cela appartiennent a
# la meme ligne. 3 points typographiques tolerent les petits decalages de rendu
# sans fusionner deux lignes distinctes.
TOLERANCE_LIGNE_PT = 3.0
# Un blanc horizontal superieur a cela separe deux cellules plutot que deux mots.
ECART_COLONNE_PT = 12.0


def lignes_de_page(page):
    """Rend [[(x, texte), ...], ...] : les mots groupes en lignes, ordonnes."""
    mots = page.get_text('words')  # (x0, y0, x1, y1, mot, bloc, ligne, n)
    groupes = []
    for x0, y0, x1, _y1, mot, _b, _l, _n in sorted(mots, key=lambda m: (m[1], m[0])):
        for groupe in groupes:
            if abs(groupe['y'] - y0) <= TOLERANCE_LIGNE_PT:
                groupe['mots'].append((x0, x1, mot))
                break
        else:
            groupes.append({'y': y0, 'mots': [(x0, x1, mot)]})
    lignes = []
    for groupe in sorted(groupes, key=lambda g: g['y']):
        lignes.append(sorted(groupe['mots'], key=lambda m: m[0]))
    return lignes


def rendre_ligne(mots):
    """Assemble une ligne en inserant ' | ' aux ruptures de colonne."""
    morceaux, precedent_fin = [], None
    for x0, x1, mot in mots:
        if precedent_fin is not None and (x0 - precedent_fin) > ECART_COLONNE_PT:
            morceaux.append('|')
        morceaux.append(mot)
        precedent_fin = x1
    return ' '.join(morceaux)


def main():
    if len(sys.argv) < 2:
        sys.stderr.write(__doc__.split('Usage :')[-1] + '\n')
        return 1
    chemin = sys.argv[1]
    page_demandee = None
    motif = None
    reste = sys.argv[2:]
    while reste:
        argument = reste.pop(0)
        if argument == '--motif' and reste:
            motif = re.compile(reste.pop(0), re.IGNORECASE)
        elif argument.isdigit():
            page_demandee = int(argument)

    document = fitz.open(chemin)
    print('%s : %d page(s)' % (chemin.split('\\')[-1], document.page_count))
    for numero in range(document.page_count):
        if page_demandee is not None and numero + 1 != page_demandee:
            continue
        lignes = [rendre_ligne(mots) for mots in lignes_de_page(document[numero])]
        print('')
        print('=== page %d : %d ligne(s) ===' % (numero + 1, len(lignes)))
        if motif is None:
            for index, texte in enumerate(lignes, 1):
                print('%4d  %s' % (index, texte))
            continue
        retenues = set()
        for index, texte in enumerate(lignes):
            if motif.search(texte):
                retenues.update(range(max(0, index - 2),
                                      min(len(lignes), index + 3)))
        precedent = None
        for index in sorted(retenues):
            if precedent is not None and index != precedent + 1:
                print('      ...')
            marque = '>>' if motif.search(lignes[index]) else '  '
            print('%s%4d  %s' % (marque, index + 1, lignes[index]))
            precedent = index
    document.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
