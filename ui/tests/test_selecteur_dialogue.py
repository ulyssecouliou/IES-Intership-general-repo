# -*- coding: utf-8 -*-
"""Tests du sélecteur de classe du dialogue, SANS ouvrir de fenêtre.

Les méthodes de filtrage n'ont besoin ni d'affichage ni de widget : elles ne
lisent que `self._vues` et la valeur du sélecteur. On les exerce donc sur un
objet minimal, ce qui les rend testables en intégration continue — là où
`tkinter.Tk()` échouerait.

Le danger visé est précis : que l'écran et le rapport disent deux choses
différentes. Si le filtre s'applique à l'arbre mais pas aux exports, le client
verrait sa classe et recevrait un PDF couvrant tout — ou l'inverse.
"""

import io
import os

import pytest

from ui import dialog_tkinter as dialogue
from ui import class_selection as selection


class FauxSelecteur(object):
    """Tient lieu de `tkinter.StringVar`."""

    def __init__(self, valeur):
        self._valeur = valeur

    def get(self):
        return self._valeur


class NavigateurSansEcran(object):
    """Objet minimal portant les méthodes de filtrage du dialogue.

    Les méthodes sont empruntées telles quelles à `NavigateurSIA4010` : c'est
    bien le code de production qui est exercé, pas une copie.
    """

    _classe_active = dialogue.NavigateurSIA4010._classe_active
    _vues_affichees = dialogue.NavigateurSIA4010._vues_affichees
    _texte_diagnostic = dialogue.NavigateurSIA4010._texte_diagnostic

    def __init__(self, vues, choix=None):
        self._vues = list(vues)
        if choix is not None:
            self._classe_choisie = FauxSelecteur(choix)


def _vue(test_id, couleur="vert"):
    return {
        "test_id": test_id,
        "classes": [],
        "verdict_global": {"couleur": couleur, "texte": "x", "article": "y"},
    }


# --------------------------------------------------------------------------
# Lecture du sélecteur
# --------------------------------------------------------------------------


def test_sans_selecteur_aucune_classe_nest_active():
    """Avant construction de l'interface, le filtre ne doit pas s'appliquer."""
    assert NavigateurSansEcran([_vue("SIA-4010-Test-1")])._classe_active() is None


def test_toutes_les_classes_ne_filtre_rien():
    navigateur = NavigateurSansEcran(
        [_vue("SIA-4010-Test-1"), _vue("5")], dialogue.TOUTES_LES_CLASSES
    )
    assert navigateur._classe_active() is None
    assert len(navigateur._vues_affichees()) == 2


def test_lidentifiant_est_extrait_du_libelle():
    """Le sélecteur affiche « 2A — Besoins de chaleur… » ; seul « 2A » compte."""
    navigateur = NavigateurSansEcran([], "2A — %s" % selection.description("2A"))
    assert navigateur._classe_active() == "2A"


def test_un_choix_vide_ne_filtre_pas():
    assert NavigateurSansEcran([_vue("SIA-4010-Test-1")], "")._classe_active() is None


# --------------------------------------------------------------------------
# Le filtre, et sa cohérence avec les exports
# --------------------------------------------------------------------------


def test_la_classe_5_ne_retient_que_le_test_7():
    navigateur = NavigateurSansEcran(
        [_vue("SIA-4010-Test-1"), _vue("Test 7")], "5 — %s" % selection.description("5")
    )
    assert [v["test_id"] for v in navigateur._vues_affichees()] == ["Test 7"]


def test_une_classe_sans_test_present_donne_une_liste_vide():
    """Vide est la vérité : mieux vaut un rapport vide qu'un rapport qui
    couvrirait des tests étrangers à la classe."""
    navigateur = NavigateurSansEcran(
        [_vue("SIA-4010-Test-1")], "5 — %s" % selection.description("5")
    )
    assert navigateur._vues_affichees() == []


def test_lexport_pdf_utilise_la_selection_pas_la_liste_complete():
    """Si le PDF lisait `self._vues`, l'écran et le rapport diraient deux
    choses différentes — et c'est le rapport qui part au client."""
    chemin = os.path.abspath(dialogue.__file__).replace(".pyc", ".py")
    with io.open(chemin, encoding="utf-8") as flux:
        source = flux.read()
    debut = source.index("def _exporter_pdf")
    corps = source[debut : debut + 1400]
    assert "self._vues_affichees()" in corps
    assert "generer_pdf_rapport_multi(\n                self._vues," not in corps


def test_larbre_est_rempli_depuis_la_selection():
    """Même exigence pour l'affichage : l'arbre montre ce que le rapport
    contiendra."""
    chemin = os.path.abspath(dialogue.__file__).replace(".pyc", ".py")
    with io.open(chemin, encoding="utf-8") as flux:
        source = flux.read()
    assert "for une_vue in self._vues_affichees():" in source


# --------------------------------------------------------------------------
# Le diagnostic interne
# --------------------------------------------------------------------------


def test_sans_classe_choisie_le_diagnostic_couvre_les_huit():
    texte = NavigateurSansEcran(
        [_vue("SIA-4010-Test-1")], dialogue.TOUTES_LES_CLASSES
    )._texte_diagnostic()
    for classe in selection.CLASSES:
        assert "Class %s" % classe in texte


def test_avec_une_classe_choisie_le_diagnostic_sy_limite():
    texte = NavigateurSansEcran([_vue("SIA-4010-Test-1")], "1A — x")._texte_diagnostic()
    assert "Class 1A" in texte
    assert "Class 4B" not in texte


def test_le_diagnostic_nomme_les_liaisons_non_resolues():
    """Il doit dire la CAUSE, pas seulement le symptôme."""
    texte = NavigateurSansEcran([_vue("SIA-4010-Test-1")], "2A — x")._texte_diagnostic()
    assert "LIAISONS_NON_RESOLUES" in texte
    assert "decouvrir_variables" in texte or "Sonde_APS" in texte


def test_letat_des_liaisons_est_lu_dans_ladaptateur():
    """Recopié, il se périmerait à la première liaison résolue."""
    etat = dialogue._etat_des_liaisons()
    if not etat:
        pytest.skip("adaptateur non importable")
    from ve_adapter import bandes_adapter

    for numero, (resolues, declarees) in etat.items():
        assert declarees == len(bandes_adapter.LIAISONS[numero])
        assert resolues == len(bandes_adapter.liaisons_resolues(numero))


def test_un_adaptateur_absent_ne_fait_pas_echouer(monkeypatch):
    """Le diagnostic doit rester produisible même sans l'adaptateur."""
    import builtins

    vrai_import = builtins.__import__

    def refuser(nom, *args, **kwargs):
        if nom.startswith("ve_adapter"):
            raise ImportError(nom)
        return vrai_import(nom, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", refuser)
    assert dialogue._etat_des_liaisons() == {}
