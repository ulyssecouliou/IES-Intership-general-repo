# -*- coding: utf-8 -*-
u"""Test 1 introspection probe -- run it from the Run button inside VE.

Kept at the repository root, like the other `Run_VE_*.py`: that is where
Scripts navigator de VE va chercher. Le code vit dans
`scripts/run_test1_dans_ve.py`; this file is only an entry point.

WHAT IT DOES. It walks a case step by step and records what the API ACTUALLY
returns. It is not trying to succeed, it is trying to learn: a step that fails
is a useful result, not a problem.

Outside VE the same file does an installation check and touches nothing.

It writes `outputs/sonde_test1_600.json`. That is the file to send back.
"""

from __future__ import print_function

import os
import sys

_RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Bootstrap -- MUST come before any project import
# ---------------------------------------------------------------------------
#
# VEScripts keeps the SAME interpreter from one click on Run to the next, so
# `sys.modules` persists. A `scripts` package imported from another repository
# stays cached there and shadows this one, whatever is done to `sys.path`
# afterwards: a module already loaded is never reloaded.
#
# Le danger est ici plus grand que pour la sonde APS : `run_test1_dans_ve`
# EXISTS in the old `SIA_Compliance_Scripts` repository. Without this purge
# the import SUCCEEDED -- loading the version from before the enum fixes, with
# nothing to say so. A failed import is a nuisance; a silent wrong one is a
# day of debugging the wrong file.
#
# Ce code ne peut pas vivre dans un module du projet : il faut qu'il tourne
# before such a module is importable. Hence the deliberate duplication
# les lanceurs.
_PAQUETS = ('scripts', 've_adapter', 'engine', 'ui', 'swiss_sia')
_PREFIXES = _PAQUETS + tuple(_nom + '.' for _nom in _PAQUETS)
for _nom_module in tuple(sys.modules):
    if _nom_module in _PAQUETS or _nom_module.startswith(_PREFIXES):
        del sys.modules[_nom_module]

# Our root goes FIRST, not last: another repository may already be on the
# path.
while _RACINE in sys.path:
    sys.path.remove(_RACINE)
sys.path.insert(0, _RACINE)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from scripts import bootstrap_check  # noqa: E402
from scripts import run_test1_dans_ve as sonde  # noqa: E402


if __name__ == '__main__':
    # No `sys.exit`: it raises SystemExit, which VEScripts reports as an
    # error in its script window even when everything went fine.
    if bootstrap_check.check(_RACINE):
        _code = sonde.main(tuple(getattr(sys, 'argv', ())[1:]))
    else:
        _code = 2
    print()
    print('--- finished (code %d) ---' % _code)
