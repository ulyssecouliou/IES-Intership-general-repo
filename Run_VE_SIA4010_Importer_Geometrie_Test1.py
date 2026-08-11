# -*- coding: utf-8 -*-
u"""Test 1 geometry import -- Run button inside VE.

WARNING: this script MODIFIES the VE model. Run it on a THROWAWAY project,
never on a client model.

WHY THIS IS SEPARATE FROM THE PROBE. An import **modifies the model**. The
Test 1 probe is a reading: it creates trial materials and deletes them.
Folding an import into it would make a mere reading mutate the model without
anyone asking -- exactly the kind of side effect nobody
remarque qu'une fois le mal fait. Cet import se lance donc **explicitement**,
sur un projet jetable.

CE QUE FAIT CE SCRIPT, DANS L'ORDRE :

    1. writes the gbXML from `ve_adapter/gbxml_test1.py`, which already
       refuses to write an incoherent geometry;
    2. l'importe par `ImportGBXML.import_file`, dont la signature n'est pas
       introspectable: several call shapes are tried, and the one that
       answers is RECORDED;
    3. **relit `get_bodies()` puis `get_areas()`** et confronte les surfaces
       against those of the source.

STEP 3 IS THE ONLY ONE THAT PROVES ANYTHING. An import that does not raise
says nothing: the 1 mm layer thicknesses were created without a single error,
and were worth a resistance forty-seven times too low. A geometry imported
crooked would behave the same way.

It writes `outputs/import_geometrie_test1.json`.
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
from scripts import importer_geometrie_test1 as sonde  # noqa: E402


if __name__ == '__main__':
    # No `sys.exit`: it raises SystemExit, which VEScripts reports as an
    # error in its script window even when everything went fine.
    if amorcage.controler(_RACINE):
        _code = sonde.main(tuple(getattr(sys, 'argv', ())[1:]))
    else:
        _code = 2
    print()
    print('--- finished (code %d) ---' % _code)
