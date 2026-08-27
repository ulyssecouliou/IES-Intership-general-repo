# -*- coding: utf-8 -*-
"""Test d'intégration RÉEL de `ui/export_pdf_reportlab.py`.

Contrairement à la majorité de `ui/dialog_tkinter.py` et
`ui/excel_export.py`, ce test S'EXÉCUTE réellement ici : `reportlab` a pu
être installé dans cet environnement de développement (`pip install
reportlab`, version 5.0.0). Il ne prouve PAS la compatibilité avec ReportLab
3.2 (version réellement embarquée dans VEScripts, ADR-001 §2) -- seulement
que la logique d'assemblage du rapport (lecture de `ui/verdict_view.py`,
construction des tableaux) produit un PDF syntaxiquement valide, sans
exception, à partir de données réelles (fixture de développement).

`pytest.importorskip` : si `reportlab` finit par être absent d'un autre poste
d'exécution de la suite de tests, ce fichier est ignoré plutôt que de faire
échouer toute la collecte -- cohérent avec le fait que `reportlab` ne fait
PAS partie des dépendances obligatoires de `engine/` (Python pur, CI sans
VE) ; il ne l'est que pour cette partie optionnelle de `ui/`.
"""

import os
import sys

import pytest

reportlab = pytest.importorskip("reportlab")

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

from engine import test1_engine as moteur  # noqa: E402
from ve_adapter import test1_adapter as adapter  # noqa: E402
from ui import verdict_view as vue  # noqa: E402
from ui import export_pdf_reportlab  # noqa: E402


@pytest.fixture(scope="module")
def vue_test1():
    reference = moteur.charger_reference()
    candidat = adapter.charger_fixture_test1()
    resultat = moteur.evaluer_test1(reference, candidat)
    return vue.construire_vue_test1(resultat)


def test_generer_pdf_rapport_produit_un_fichier_pdf_valide(tmp_path, vue_test1):
    chemin_pdf = str(tmp_path / "rapport_test1.pdf")
    resultat = export_pdf_reportlab.generer_pdf_rapport(vue_test1, chemin_pdf)

    assert resultat == chemin_pdf
    assert os.path.isfile(chemin_pdf)
    assert os.path.getsize(chemin_pdf) > 1000  # rapport non trivial

    with open(chemin_pdf, "rb") as flux:
        entete = flux.read(5)
    assert entete == b"%PDF-"


def test_generer_pdf_rapport_fonctionne_sans_aucun_candidat(tmp_path):
    """Etat "avant simulation" : le rapport doit se generer meme si toutes
    les lignes sont grises, sans exception."""
    reference = moteur.charger_reference()
    resultat = moteur.evaluer_test1(reference, None)
    vue_sans_candidat = vue.construire_vue_test1(resultat)

    chemin_pdf = str(tmp_path / "rapport_sans_candidat.pdf")
    export_pdf_reportlab.generer_pdf_rapport(vue_sans_candidat, chemin_pdf)

    assert os.path.isfile(chemin_pdf)
    with open(chemin_pdf, "rb") as flux:
        assert flux.read(5) == b"%PDF-"
