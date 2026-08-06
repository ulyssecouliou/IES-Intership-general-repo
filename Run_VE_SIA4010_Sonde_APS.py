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

# ---------------------------------------------------------------------------
# Amorçage — DOIT précéder tout import du projet
# ---------------------------------------------------------------------------
#
# VEScripts garde le MÊME interpréteur d'un clic sur Run au suivant :
# `sys.modules` persiste. Un paquet `scripts` importé depuis un autre dépôt y
# reste en cache et masque celui-ci, quoi qu'on fasse ensuite à `sys.path` —
# un module déjà chargé n'est jamais rechargé.
#
# Vécu le 2026-08-06 :
#   ImportError: cannot import name 'sonde_aps' from 'scripts'
#   (...\SIA_Compliance_Scripts\scripts\__init__.py)
#
# Ce code ne peut pas vivre dans un module du projet : il faut qu'il tourne
# avant qu'un tel module soit importable. D'où la duplication assumée entre
# les lanceurs.
_PAQUETS = ('scripts', 've_adapter', 'engine', 'ui', 'swiss_sia')
_PREFIXES = _PAQUETS + tuple(_nom + '.' for _nom in _PAQUETS)
for _nom_module in tuple(sys.modules):
    if _nom_module in _PAQUETS or _nom_module.startswith(_PREFIXES):
        del sys.modules[_nom_module]

# Notre racine passe DEVANT, pas derrière : un autre dépôt peut déjà être sur
# le chemin.
while _RACINE in sys.path:
    sys.path.remove(_RACINE)
sys.path.insert(0, _RACINE)

from scripts import amorcage  # noqa: E402
from scripts import sonde_aps as sonde  # noqa: E402


if __name__ == '__main__':
    # Pas de `sys.exit` : il leve SystemExit, que VEScripts remonte comme une
    # erreur dans sa fenetre de script alors que tout s est bien passe.
    if amorcage.controler(_RACINE):
        _code = sonde.main(tuple(getattr(sys, 'argv', ())[1:]))
    else:
        _code = 2
    print()
    print('--- termine (code %d) ---' % _code)
