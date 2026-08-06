# -*- coding: utf-8 -*-
u"""Sonde d'introspection du Test 1 — à lancer au bouton Run depuis VE.

Placé à la racine, comme les autres `Run_VE_*.py` : c'est là que le Python
Scripts navigator de VE va chercher. Le code vit dans
`scripts/run_test1_dans_ve.py` ; ce fichier n'est qu'un point d'entrée.

CE QU'IL FAIT. Il déroule un cas pas à pas et consigne ce que l'API renvoie
RÉELLEMENT. Il n'essaie pas de réussir, il essaie d'apprendre : une étape en
échec est un résultat utile, pas un problème.

Hors de VE, le même fichier se contente d'un contrôle d'installation et ne
touche à rien.

Il écrit `outputs/sonde_test1_600.json`. C'est ce fichier qu'il faut renvoyer.
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
# Le danger est ici plus grand que pour la sonde APS : `run_test1_dans_ve`
# EXISTE dans l'ancien dépôt `SIA_Compliance_Scripts`. Sans cette purge,
# l'import réussissait — en chargeant la version antérieure aux corrections
# d'énumérés, sans rien signaler.
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
from scripts import run_test1_dans_ve as sonde  # noqa: E402


if __name__ == '__main__':
    # Pas de `sys.exit` : il leve SystemExit, que VEScripts remonte comme une
    # erreur dans sa fenetre de script alors que tout s est bien passe.
    if amorcage.controler(_RACINE):
        _code = sonde.main(tuple(getattr(sys, 'argv', ())[1:]))
    else:
        _code = 2
    print()
    print('--- termine (code %d) ---' % _code)
