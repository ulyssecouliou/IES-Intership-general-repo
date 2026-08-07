# -*- coding: utf-8 -*-
u"""Tests de la charte appliquée (`ui/theme_ies.py`).

L'affichage réel demande un écran, donc les tests qui instancient une fenêtre
s'ignorent sans affichage. Ce qui est testable sans écran est justement ce qui
peut tromper : que les couleurs viennent bien des jetons relevés sur le site,
que le thème soit changé (sans quoi rien ne s'affiche), et qu'aucun verdict ne
repose sur la seule couleur.
"""

import io
import os

import pytest

from ui import design_ies as design
from ui import theme_ies as charte


def _fenetre():
    """Ouvre une fenêtre, ou ignore le test faute d'affichage.

    Returns:
        tkinter.Tk: Fenêtre à détruire par l'appelant.
    """
    tk = pytest.importorskip('tkinter', reason=u'tkinter absent')
    try:
        return tk.Tk()
    except Exception:  # noqa: BLE001 -- pas d'affichage : rien à tester ici
        pytest.skip(u'aucun affichage disponible')


# --------------------------------------------------------------------------
# Le point qui décide de tout : le thème
# --------------------------------------------------------------------------

def test_le_theme_requis_honore_les_couleurs():
    """Sur Windows, ttk démarre sur `vista`, qui délègue au système et ignore
    `background`. Sans bascule, la charte ne s'affiche tout simplement pas —
    c'est ce que signalait la réserve « À VÉRIFIER » du dialogue."""
    assert charte.THEME_REQUIS == 'clam'


def test_appliquer_bascule_effectivement_le_theme():
    racine = _fenetre()
    try:
        style = charte.appliquer(racine)
        assert style.theme_use() == charte.THEME_REQUIS
    finally:
        racine.destroy()


def test_appliquer_peint_le_fond_de_la_fenetre():
    racine = _fenetre()
    try:
        charte.appliquer(racine)
        assert racine.cget('background') == design.GRIS_CLAIR
    finally:
        racine.destroy()


def test_les_styles_annonces_existent_reellement():
    """Un nom de style inexistant ne lève pas dans ttk : le widget retombe
    silencieusement sur le style par défaut. L'erreur serait invisible."""
    racine = _fenetre()
    try:
        style = charte.appliquer(racine)
        for nom in (charte.STYLE_FOND, charte.STYLE_CARTE,
                    charte.STYLE_BANDEAU, charte.STYLE_TITRE,
                    charte.STYLE_BOUTON, charte.STYLE_BOUTON_ACCENT,
                    charte.STYLE_ARBRE):
            assert style.configure(nom) is not None, nom
    finally:
        racine.destroy()


def test_les_styles_sont_prefixes():
    """VEScripts garde le même interpréteur d'un Run à l'autre : un style non
    préfixé écraserait celui d'un autre dialogue."""
    for nom in (charte.STYLE_FOND, charte.STYLE_CARTE, charte.STYLE_BANDEAU,
                charte.STYLE_TITRE, charte.STYLE_SOUS_TITRE,
                charte.STYLE_TEXTE, charte.STYLE_BOUTON,
                charte.STYLE_BOUTON_ACCENT, charte.STYLE_ARBRE):
        assert nom.startswith(charte.PREFIXE), nom


def test_labsence_de_clam_ne_fait_pas_echouer(monkeypatch):
    """Une interface aux couleurs du système reste utilisable ; une exception
    au lancement, non."""
    class FauxStyle(object):
        def theme_names(self):
            return ('alt', 'default')

        def theme_use(self, nom=None):
            return 'default'

    assert charte._forcer_le_theme(FauxStyle()) == 'default'


# --------------------------------------------------------------------------
# Les couleurs viennent des jetons, pas d'un choix
# --------------------------------------------------------------------------

def test_aucune_couleur_nest_ecrite_en_dur():
    """Toute couleur du thème doit venir de `design_ies`, qui les tient de la
    feuille de style publique d'IES. Une valeur écrite ici serait un choix
    esthétique déguisé en charte."""
    chemin = os.path.abspath(charte.__file__).replace('.pyc', '.py')
    with io.open(chemin, encoding='utf-8') as flux:
        for numero, ligne in enumerate(flux, 1):
            nu = ligne.split('#')[0]
            assert '#0' not in nu and '#1' not in nu, (numero, ligne.strip())


def test_les_couleurs_de_marque_sont_celles_du_site():
    """Relevées sur `iesve.com/assets/css/styles.css`."""
    assert design.NAVY == '#1a2b4b'
    assert design.ACCENT == '#0f54e8'
    assert design.TEINTE_BLEUE == '#e8f1fb'
    assert design.GRIS_CLAIR == '#f5f7f9'


# --------------------------------------------------------------------------
# Accessibilité : jamais l'information par la seule couleur
# --------------------------------------------------------------------------

@pytest.mark.parametrize('couleur', ['vert', 'rouge', 'gris'])
def test_un_verdict_porte_toujours_son_symbole(couleur):
    libelle = charte.libelle_de_verdict(couleur, u'Conforme')
    assert libelle.startswith(design.symbole(couleur))
    assert u'Conforme' in libelle


def test_le_symbole_precede_le_texte():
    """C'est le symbole qui reste lisible quand la couleur ne s'affiche pas :
    il doit venir en premier."""
    libelle = charte.libelle_de_verdict('rouge', u'Non conforme')
    assert libelle.index(design.symbole('rouge')) == 0


def test_une_couleur_inconnue_ne_se_lit_pas_comme_un_succes():
    fond, _ = charte.couleurs_de_ligne('couleur inventee')
    assert fond == design.GRIS_CLAIR
    assert fond != design.FOND_PAR_VERDICT['vert']


@pytest.mark.parametrize('couleur', ['vert', 'rouge', 'gris'])
def test_le_texte_des_lignes_reste_le_texte_de_marque(couleur):
    _, texte = charte.couleurs_de_ligne(couleur)
    assert texte == design.TEXTE


# --------------------------------------------------------------------------
# Mise en page
# --------------------------------------------------------------------------

def test_les_lignes_du_tableau_respirent():
    """Le site divise par l'espace, pas par des traits épais. Une ligne serrée
    trahirait la charte plus sûrement qu'une couleur approximative."""
    assert charte.HAUTEUR_LIGNE >= 24


def test_le_dialogue_applique_la_charte_avant_de_creer_ses_widgets():
    """Le changement de thème ttk ne se propage pas rétroactivement : appliqué
    trop tard, il laisserait les widgets déjà créés en gris système."""
    chemin = os.path.join(os.path.dirname(os.path.abspath(charte.__file__)),
                          'dialog_tkinter.py')
    with io.open(chemin, encoding='utf-8') as flux:
        source = flux.read()
    debut = source.index('def _construire_widgets')
    corps = source[debut:debut + 1200]
    assert corps.index('charte.appliquer') < corps.index('ttk.Frame')
