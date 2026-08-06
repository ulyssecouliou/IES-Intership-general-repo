# -*- coding: utf-8 -*-
"""Tests des jetons de design IES.

Deux exigences, et la seconde compte plus que la premiere :

* les couleurs viennent bien de la feuille de style d IES, pas d un gout
  personnel ;
* **un verdict n est jamais porte par la seule couleur** -- symbole et texte
  l accompagnent toujours, faute de quoi le rapport devient illisible sur un
  theme ttk qui ignore `background`, ou pour un lecteur daltonien.
"""

import re

import pytest

from ui import design_ies as design

_HEX = re.compile(r'^#[0-9a-f]{6}$')


def test_toutes_les_couleurs_sont_des_hex_valides():
    for nom in dir(design):
        valeur = getattr(design, nom)
        if nom.isupper() and isinstance(valeur, str) and valeur.startswith('#'):
            assert _HEX.match(valeur), (nom, valeur)


def test_les_couleurs_de_marque_sont_celles_du_site():
    """Relevees sur iesve.com/assets/css/styles.css le 2026-08-06.

    Si quelqu un les 'ajuste', ce test le signale : ce ne sont pas des
    preferences, ce sont des valeurs de marque.
    """
    assert design.ACCENT == '#0f54e8'      # --ha-accent
    assert design.TEINTE_BLEUE == '#e8f1fb'  # --lightblue-fade
    assert design.GRIS_CLAIR == '#f5f7f9'  # --light-grey
    assert design.BLEU_CLAIR == '#00abde'  # --lightblue
    assert design.NAVY == '#1a2b4b'


@pytest.mark.parametrize('couleur', ['vert', 'rouge', 'gris'])
def test_chaque_verdict_a_fond_trait_et_symbole(couleur):
    assert _HEX.match(design.fond_verdict(couleur))
    assert _HEX.match(design.trait_verdict(couleur))
    assert design.symbole(couleur) not in ('', '?')
    assert design.symbole(couleur, ascii_seulement=True) not in ('', '?')


def test_les_trois_symboles_sont_distincts():
    """Deux verdicts au meme symbole seraient indistinguables en niveaux de
    gris."""
    valeurs = [design.symbole(c) for c in ('vert', 'rouge', 'gris')]
    assert len(set(valeurs)) == 3
    ascii_ = [design.symbole(c, True) for c in ('vert', 'rouge', 'gris')]
    assert len(set(ascii_)) == 3


def test_les_trois_fonds_sont_distincts():
    fonds = [design.fond_verdict(c) for c in ('vert', 'rouge', 'gris')]
    assert len(set(fonds)) == 3


def test_une_couleur_inconnue_ne_donne_jamais_du_vert():
    """Le repli doit etre neutre : une couleur inattendue ne doit pas se lire
    comme un succes."""
    assert design.fond_verdict('turquoise') == design.GRIS_CLAIR
    assert design.trait_verdict('turquoise') == design.GRIS_NEUTRE
    assert design.symbole('turquoise') == '?'


def test_les_symboles_ascii_evitent_les_glyphes_absents():
    """Helvetica n a ni coche ni croix : ReportLab afficherait un carre noir.
    La variante ASCII existe pour ca, et pour la console de VEScripts."""
    for valeur in design.SYMBOLE_ASCII_PAR_VERDICT.values():
        assert all(ord(c) < 128 for c in valeur), valeur


def test_la_police_est_embarquable():
    """Camphor Pro est commerciale et non embarquable sans licence ; le
    rapport doit rester sur une police fournie par ReportLab."""
    assert design.POLICE_TITRE.startswith('Helvetica')
    assert design.POLICE_TEXTE.startswith('Helvetica')


def test_le_navigateur_et_le_pdf_partagent_la_meme_source():
    """Deux palettes divergeraient au premier ajustement."""
    from ui import dialog_tkinter as dlg
    assert dlg.COULEUR_FOND_PAR_VERDICT == design.FOND_PAR_VERDICT
    assert dlg.SYMBOLE_PAR_VERDICT == design.SYMBOLE_PAR_VERDICT
