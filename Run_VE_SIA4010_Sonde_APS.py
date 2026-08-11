# -*- coding: utf-8 -*-
u"""Results-variable probe -- run it from the Run button inside VE.

Run it on a VE project where **at least one ApacheSim simulation has already
finished**: the probe READS a `.aps` file, it does not produce one.

It records the variable names available at room, system and weather level, the
Apache systems, the energy end-uses and the units. That reading is what is
missing to bind the 20 quantities of SIA tests 2 to 6, all of which are
declared unresolved today. Those names are not API symbols -- they cannot be
looked up in documentation, only read off a real file.

It judges nothing and changes nothing. It writes `outputs/sonde_aps.json`.
"""

from __future__ import print_function

import os
import sys

_RACINE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Bootstrap -- MUST come before any project import
# ---------------------------------------------------------------------------
#
# VEScripts keeps the SAME interpreter from one click on Run to the next, so
# `sys.modules` persists. A `scripts` package imported from another repository
# stays cached there and shadows this one, whatever is done to `sys.path`
# afterwards: a module already loaded is never reloaded.
#
# Lived through on 2026-08-06:
#   ImportError: cannot import name 'sonde_aps' from 'scripts'
#   (...\SIA_Compliance_Scripts\scripts\__init__.py)
#
# That one at least announced itself. The dangerous case is a name that exists
# in BOTH repositories: it imports without error, and the wrong file gets
# debugged.
#
# This code cannot live in a project module -- it has to run before such a
# module is importable. Hence the duplication across launchers, which is
# deliberate.
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

from scripts import amorcage  # noqa: E402
from scripts import sonde_aps as sonde  # noqa: E402


if __name__ == '__main__':
    # No `sys.exit`: it raises SystemExit, which VEScripts reports as an
    # error in its script window even when everything went fine.
    if amorcage.controler(_RACINE):
        _code = sonde.main(tuple(getattr(sys, 'argv', ())[1:]))
    else:
        _code = 2
    print()
    print('--- finished (code %d) ---' % _code)
