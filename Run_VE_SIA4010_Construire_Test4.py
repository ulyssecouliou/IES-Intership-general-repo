# -*- coding: utf-8 -*-
u"""Reconnaissance du systeme de ventilation du Test 4 — bouton Run depuis VE.

CE QU IL FAIT. Il cree un systeme ApacheSystems et releve ce que l API attend
reellement : signature des setters, valeurs par defaut, structures acceptees.
Il ne configure RIEN — c est un releve, pas une construction.

POURQUOI EN DEUX TEMPS. `VEProject.create_apache_system()` existe, mais la
signature de `set_heating`, `set_cooling` et `set_air_supply` n est documentee
nulle part et n a jamais ete observee. Les deviner reproduirait les trois
defauts deja rencontres ce mois-ci : bon symbole, mauvais usage.

    1. ce lanceur releve ce que l API attend ;
    2. la construction est cablee ensuite, sur des signatures constatees.

Le reseau ApacheHVAC, lui, n est PAS scriptable : `HVACNetwork` n expose que
`components`, `systems`, `controllers`, `get_component_by_id`, `load_network`
et `path`. Aucune methode de creation. Un reseau se construit a la main dans
VE, puis son fichier `.asp` se charge par `load_network`.

CE MODELE N EST PAS UN CAS DE VALIDATION SIA. Il sert a lever les 18 liaisons
manquantes des tests 4 a 6. Trois entrees obligatoires manquent au depot pour
une validation : le climat SIA 2028 Kloten, les constructions SIA 380/2
tableau 3, et les fiches d usage SIA 2024.

Il ecrit `outputs/reconnaissance_test4.json`.
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

from scripts import bootstrap_check  # noqa: E402
from scripts import construire_test4_dans_ve as sonde  # noqa: E402


if __name__ == '__main__':
    # No `sys.exit`: it raises SystemExit, which VEScripts reports as an
    # error in its script window even when everything went fine.
    if bootstrap_check.check(_RACINE):
        _code = sonde.main(tuple(getattr(sys, 'argv', ())[1:]))
    else:
        _code = 2
    print()
    print('--- finished (code %d) ---' % _code)
