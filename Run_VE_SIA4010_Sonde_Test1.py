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
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

from scripts import run_test1_dans_ve as sonde  # noqa: E402


if __name__ == '__main__':
    # Pas de `sys.exit` : il leve SystemExit, que VEScripts remonte comme une
    # erreur dans sa fenetre de script alors que tout s est bien passe.
    _code = sonde.main(tuple(getattr(sys, 'argv', ())[1:]))
    print()
    print('--- termine (code %d) ---' % _code)
