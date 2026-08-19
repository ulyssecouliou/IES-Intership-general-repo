# -*- coding: utf-8 -*-
"""Garde de pureté GLOBALE de ``engine/`` — règle 4 de CLAUDE.md.

Les gardes existantes (``test_test7_engine.py``, ``test_setpoint_curves.py``) ne
couvrent qu'un fichier chacune. Un NOUVEAU module ``engine/`` important ``iesve``
passerait donc la suite locale et ne serait rattrapé qu'au push CI
(``.github/workflows/engine-tests.yml`` grep tout ``engine/``). Ce test ferme ce
trou en local : il parcourt TOUS les modules ``engine/*.py`` en une passe.
"""

import io
import os

import pytest

_ICI = os.path.dirname(os.path.abspath(__file__))
_ENGINE = os.path.abspath(os.path.join(_ICI, os.pardir))


def _modules_engine():
    """Chemins de tous les modules Python à la racine de ``engine/``."""
    for nom in sorted(os.listdir(_ENGINE)):
        if nom.endswith(".py"):
            yield os.path.join(_ENGINE, nom)


@pytest.mark.parametrize("chemin", list(_modules_engine()))
def test_aucun_module_engine_nimporte_iesve(chemin):
    """Aucun module de ``engine/`` ne doit importer ``iesve``.

    ``engine/`` est du Python pur, testable en CI sans licence VE. Un import
    ``iesve`` — même indirect via ``from iesve import ...`` — casserait cette
    garantie et doit faire échouer la suite localement, pas seulement en CI.
    """
    with io.open(chemin, encoding="utf-8") as flux:
        for numero, ligne in enumerate(flux, 1):
            nu = ligne.strip()
            assert not nu.startswith("import iesve"), (chemin, numero)
            assert not nu.startswith("from iesve"), (chemin, numero)


def test_la_garde_voit_bien_les_modules_engine():
    """Garde-fou de la garde : si le glob ne trouvait rien, le test ci-dessus
    passerait à vide. On exige donc de voir les modules cœur connus."""
    noms = {os.path.basename(chemin) for chemin in _modules_engine()}
    for attendu in ("test1_engine.py", "test7_engine.py", "scatter_band.py"):
        assert attendu in noms, attendu
