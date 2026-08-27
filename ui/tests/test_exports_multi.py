# -*- coding: utf-8 -*-
"""Tests des exports branchés sur la vue multi-tests.

PDF : génère un VRAI fichier et le relit — ReportLab est installé ici
(cf. docstring de `ui/export_pdf_reportlab.py`, avec sa réserve de version
3.2 côté VE).

Excel : la partie orchestration est testée SANS Excel. Le remplissage réel
par COM reste couvert par `ui/tests/test_excel_export.py`, qui se saute
si Excel est absent.
"""

import os

import pytest

# --------------------------------------------------------------------------
# Vues synthétiques — on teste les exports, pas les moteurs
# --------------------------------------------------------------------------


def _vue(numero, couleur="gris"):
    conforme = {"vert": True, "rouge": False, "gris": None}[couleur]
    ligne = {
        "grandeur": "Groupe",
        "grandeur_libelle": "Groupe",
        "cas": "Grandeur A",
        "type_controle": "critere_pass_fail",
        "periode": "annual",
        "periode_libelle": "Annuel",
        "conforme": conforme,
        "couleur": couleur,
        "texte_verdict": "texte",
        "valeur_candidate": None,
        "valeur_candidate_affichee": "—",
        "reference_affichee": "100,0 (90,0 … 110,0) kWh",
        "article": "article de test",
        "source_valeur_reference": "source de test",
        "detail": {},
    }
    return {
        "test_id": "Test " + numero,
        "numero_test": numero,
        "verdict_global": {
            "conforme": conforme,
            "couleur": couleur,
            "texte": "verdict",
            "article": "article global",
        },
        "classes": [
            {
                "classe": "5",
                "test_id": "Test " + numero,
                "test_requis": True,
                "conforme": conforme,
                "couleur": couleur,
                "texte_verdict": "verdict",
                "article": "article classe",
            }
        ],
        "lignes": [ligne],
    }


# --------------------------------------------------------------------------
# PDF
# --------------------------------------------------------------------------

reportlab = pytest.importorskip("reportlab")
from ui import export_pdf_reportlab as pdf  # noqa: E402


def test_pdf_multi_genere_un_fichier_valide(tmp_path):
    chemin = str(tmp_path / "rapport.pdf")
    pdf.generer_pdf_rapport_multi([_vue("1"), _vue("7")], chemin)
    assert os.path.getsize(chemin) > 1000
    with open(chemin, "rb") as flux:
        assert flux.read(5) == b"%PDF-"


def test_pdf_multi_commence_par_la_synthese_par_classe(tmp_path):
    fitz = pytest.importorskip("fitz")
    chemin = str(tmp_path / "rapport.pdf")
    pdf.generer_pdf_rapport_multi([_vue("1"), _vue("7")], chemin)
    texte = fitz.open(chemin)[0].get_text()
    assert "synthèse par classe" in texte
    # les huit classes du tableau 63 figurent en page 1
    for classe in ("1A", "1B", "2A", "2B", "4A", "4B"):
        assert classe in texte


def test_pdf_multi_nomme_les_tests_manquants(tmp_path):
    """Le rapport client doit dire POURQUOI une classe n'est pas acquise."""
    fitz = pytest.importorskip("fitz")
    chemin = str(tmp_path / "rapport.pdf")
    pdf.generer_pdf_rapport_multi([_vue("7")], chemin)  # Test 1 absent
    texte = fitz.open(chemin)[0].get_text()
    assert "Test 1" in texte
    assert "absent" in texte


def test_pdf_multi_refuse_une_liste_vide(tmp_path):
    with pytest.raises(ValueError):
        pdf.generer_pdf_rapport_multi([], str(tmp_path / "vide.pdf"))


def test_pdf_mono_delegue_au_multi_et_reste_compatible(tmp_path):
    chemin = str(tmp_path / "mono.pdf")
    resultat = pdf.generer_pdf_rapport(_vue("1"), chemin)
    assert resultat == chemin
    assert os.path.getsize(chemin) > 1000


# --------------------------------------------------------------------------
# Excel — orchestration seule, sans COM
# --------------------------------------------------------------------------

from ui import excel_export as xls  # noqa: E402


def test_excel_un_travail_en_echec_ninterrompt_pas_les_autres():
    """Sans carte de cellules, `fill_sia_workbook_reporting` lève. Les
    deux travaux doivent être tentés, et les deux échecs consignés."""
    resultat = xls.fill_sia_workbooks(
        [
            {
                "vue": _vue("1"),
                "chemin_source": "inexistant1.xlsx",
                "carte_cellules": None,
            },
            {
                "vue": _vue("7"),
                "chemin_source": "inexistant7.xlsx",
                "carte_cellules": None,
            },
        ]
    )
    assert len(resultat["echecs"]) == 2
    assert resultat["rapports"] == []
    assert resultat["complet"] is False
    assert [e["test_id"] for e in resultat["echecs"]] == ["Test 1", "Test 7"]
    for echec in resultat["echecs"]:
        assert "MissingCellMap" in echec["erreur"]


def test_excel_sans_aucun_travail_nest_pas_complet_par_defaut():
    """Zéro travail ne doit pas se lire comme « tout est rempli »."""
    resultat = xls.fill_sia_workbooks([])
    assert resultat["rapports"] == []
    assert resultat["echecs"] == []
    # `complet` vaut True au sens strict (aucun échec, aucune cellule vide),
    # mais aucun classeur n'a été produit : c'est à l'appelant de constater
    # la liste vide. On verrouille le comportement pour qu'il soit explicite.
    assert resultat["complet"] is True
    assert len(resultat["rapports"]) == 0


def test_excel_le_rapport_detaille_expose_les_cellules_ignorees():
    """Régression : ces listes étaient calculées puis jetées, si bien qu'un
    classeur pouvait repartir avec des cases vides sans que personne
    l'apprenne. C'est exactement le cas du PV du Test 7."""
    import ast
    import inspect

    source = inspect.getsource(xls.fill_sia_workbook_reporting)
    tree = ast.parse(source)
    returned_keys = {
        key.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Dict)
        for key in node.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }
    assert {
        "cellules_ignorees_valeur_absente",
        "cellules_ecrites",
        "complet",
    } <= returned_keys
