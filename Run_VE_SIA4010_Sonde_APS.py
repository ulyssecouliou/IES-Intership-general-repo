# -*- coding: utf-8 -*-
u"""Sonde des variables de résultats — à lancer au bouton Run depuis VE.

À lancer sur un projet VE **dont au moins une simulation ApacheSim a déjà
tourné** : la sonde lit un fichier `.aps`, elle n'en produit pas.

Elle relève les noms de variables disponibles aux niveaux local, système et
météo, les systèmes Apache, les postes d'énergie et les unités. C'est ce
relevé qui manque pour lier les 20 grandeurs des tests SIA 2 à 6 — aujourd'hui
toutes déclarées non résolues.

Elle ne juge rien et ne modifie rien. Elle écrit `outputs/sonde_aps.json`.
"""

from __future__ import print_function

import os
import sys

_RACINE = os.path.dirname(os.path.abspath(__file__))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

from scripts import sonde_aps as sonde  # noqa: E402


if __name__ == '__main__':
    # Pas de `sys.exit` : il leve SystemExit, que VEScripts remonte comme une
    # erreur dans sa fenetre de script alors que tout s est bien passe.
    _code = sonde.main(tuple(getattr(sys, 'argv', ())[1:]))
    print()
    print('--- termine (code %d) ---' % _code)
