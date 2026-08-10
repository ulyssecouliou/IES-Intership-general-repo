# -*- coding: utf-8 -*-
u"""Import de la géométrie du Test 1 — bouton Run depuis VE.

ATTENTION : ce script MODIFIE le modèle VE. À lancer sur un projet JETABLE,
jamais sur un modèle client.

POURQUOI UN SCRIPT SÉPARÉ DE LA SONDE. Un import **modifie le modèle**. La
sonde du Test 1 est un relevé : elle crée des matériaux d'essai et les
supprime. Y glisser un import ferait qu'un simple relevé muterait le modèle
sans qu'on l'ait demandé — exactement le genre d'effet de bord qu'on ne
remarque qu'une fois le mal fait. Cet import se lance donc **explicitement**,
sur un projet jetable.

CE QUE FAIT CE SCRIPT, DANS L'ORDRE :

    1. écrit le gbXML depuis `ve_adapter/gbxml_test1.py` — qui refuse déjà
       d'écrire une géométrie incohérente ;
    2. l'importe par `ImportGBXML.import_file`, dont la signature n'est pas
       introspectable : plusieurs formes d'appel sont essayées, et celle qui
       répond est CONSIGNÉE ;
    3. **relit `get_bodies()` puis `get_areas()`** et confronte les surfaces
       à celles de la source.

L'ÉTAPE 3 EST LA SEULE QUI PROUVE QUELQUE CHOSE. Un import qui ne lève pas ne
dit rien : les épaisseurs de couche à 1 mm ont été créées sans la moindre
erreur, et valaient un R quarante-sept fois trop faible. Une géométrie
importée de travers se comporterait pareil.

Il écrit `outputs/import_geometrie_test1.json`.
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
from scripts import importer_geometrie_test1 as sonde  # noqa: E402


if __name__ == '__main__':
    # Pas de `sys.exit` : il leve SystemExit, que VEScripts remonte comme une
    # erreur dans sa fenetre de script alors que tout s est bien passe.
    if amorcage.controler(_RACINE):
        _code = sonde.main(tuple(getattr(sys, 'argv', ())[1:]))
    else:
        _code = 2
    print()
    print('--- termine (code %d) ---' % _code)
