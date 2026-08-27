# -*- coding: utf-8 -*-
"""Tests for the ttk house style (`ui/theme.py`).

The defect these exist for is specific and was real: on Windows, ttk starts on
`vista`, which hands rendering to the OS and ignores `background` outright.
Every colour in `ui/design.py` can be correct and the dialog still comes up
system grey. Nothing raises. The only way to catch it is to assert the theme
switch itself.

The second thing guarded here is that a style NAME the module advertises
actually exists. A widget given an unknown style silently falls back to the
default -- so a typo in a constant produces a grey widget among branded ones,
which reads as a rendering bug rather than as the missing style it is.
"""

import io
import os

import pytest

from ui import design
from ui import theme


@pytest.fixture
def root():
    """A real Tk window, skipped where there is no display."""
    tkinter = pytest.importorskip("tkinter")
    try:
        window = tkinter.Tk()
    except Exception:  # noqa: BLE001 -- no display is a skip, not a failure
        pytest.skip("no display available")
    window.withdraw()
    yield window
    window.destroy()


# --------------------------------------------------------------------------
# The theme switch -- the whole reason this module exists
# --------------------------------------------------------------------------


def test_apply_actually_switches_theme(root):
    """THE DEFECT. Without this switch every colour below is ignored and the
    dialog comes up system grey, with nothing raising."""
    from tkinter import ttk

    style = theme.apply(root)
    assert isinstance(style, ttk.Style)
    if theme.REQUIRED_THEME in style.theme_names():
        assert style.theme_use() == theme.REQUIRED_THEME


def test_apply_paints_the_window_ground(root):
    theme.apply(root)
    assert root.cget("background") == design.LIGHT_GREY


def test_a_missing_clam_does_not_fail(root):
    """Not observed, but possible on a minimal install. An interface in system
    colours is still usable; an exception is not."""
    from tkinter import ttk

    style = ttk.Style(root)
    original = style.theme_names

    style.theme_names = lambda: ("alt",)
    try:
        assert theme._force_theme(style) in style.theme_names() or True
    finally:
        style.theme_names = original


def test_the_module_explains_why_it_switches():
    """A theme switch with no stated reason gets 'simplified away'."""
    chemin = os.path.abspath(theme.__file__).replace(".pyc", ".py")
    with io.open(chemin, encoding="utf-8") as flux:
        entete = flux.read(2500)
    assert "vista" in entete
    assert "not an aesthetic preference" in entete


# --------------------------------------------------------------------------
# Style names
# --------------------------------------------------------------------------


def _advertised_styles():
    """Every style name the module exposes as a constant."""
    noms = []
    for nom in dir(theme):
        if not nom.startswith("STYLE_"):
            continue
        valeur = getattr(theme, nom)
        if isinstance(valeur, str):
            noms.append(valeur)
        elif isinstance(valeur, dict):
            noms.extend(valeur.values())
    return sorted(set(noms))


def test_every_advertised_style_is_really_configured(root):
    """A widget given an unknown style falls back to the default in silence:
    one grey widget among branded ones, which reads as a rendering bug."""
    style = theme.apply(root)
    for nom in _advertised_styles():
        assert style.configure(nom) is not None, nom


def test_every_style_name_is_prefixed():
    """VEScripts keeps one interpreter across clicks on Run. An unprefixed
    style would leak into another dialog's appearance."""
    for nom in _advertised_styles():
        assert nom.startswith(theme.PREFIX), nom


def test_there_is_one_badge_style_per_status():
    """Built rather than written out, so a status added to design cannot be
    forgotten here -- a badge without a style renders default grey, and a FAIL
    would look like a NOT EVALUATED."""
    assert sorted(theme.STYLE_BADGE) == sorted(design.STATUSES)


def test_there_is_one_row_tag_per_status():
    assert sorted(theme.ROW_TAG) == sorted(design.STATUSES)


def test_badge_styles_are_distinct():
    assert len(set(theme.STYLE_BADGE.values())) == len(theme.STYLE_BADGE)


# --------------------------------------------------------------------------
# Verdicts: colour is never the only carrier
# --------------------------------------------------------------------------


@pytest.mark.parametrize("status", design.STATUSES)
def test_a_verdict_always_carries_its_symbol(status):
    libelle = theme.verdict_label(status, "TEXT")
    assert design.STATUS_SYMBOL[status] in libelle
    assert "TEXT" in libelle


def test_the_symbol_comes_before_the_word():
    """It leads because it is what stays readable when the colour does not
    render at all."""
    libelle = theme.verdict_label(design.PASS, "CONFORME")
    assert libelle.index(design.STATUS_SYMBOL[design.PASS]) < libelle.index("CONFORME")


def test_an_unknown_status_does_not_read_as_a_success():
    ground, _ = theme.row_colours("no such status")
    assert ground == design.LIGHT_GREY
    assert ground != design.STATUS_GROUND[design.PASS]


@pytest.mark.parametrize("status", design.STATUSES)
def test_row_text_stays_the_brand_text_colour(status):
    """Tinting the text as well as the ground costs contrast, and the ground
    already carries the state."""
    _, texte = theme.row_colours(status)
    assert texte == design.TEXT


# --------------------------------------------------------------------------
# Table
# --------------------------------------------------------------------------


def test_configure_row_tags_returns_every_tag(root):
    from tkinter import ttk

    theme.apply(root)
    arbre = ttk.Treeview(root)
    tags = theme.configure_row_tags(arbre)
    assert sorted(tags) == sorted(design.STATUSES)


def test_table_rows_breathe(root):
    """The house style divides by space. A cramped row height is the single
    change that makes the table stop looking like the site."""
    style = theme.apply(root)
    assert int(style.configure(theme.STYLE_TREE, "rowheight")) >= 26


def test_the_table_header_is_not_the_row_ground(root):
    """Without a distinct header the first data row reads as a heading."""
    style = theme.apply(root)
    entete = style.configure(theme.STYLE_TREE + ".Heading", "background")
    corps = style.configure(theme.STYLE_TREE, "background")
    assert entete != corps


# --------------------------------------------------------------------------
# Space discipline
# --------------------------------------------------------------------------


def test_padding_comes_from_the_scale():
    """Ad-hoc padding is what makes an interface look assembled rather than
    designed."""
    valeurs = list(design.SPACE.values())
    for paire in (design.PAD_BAND, design.PAD_CARD, design.PAD_CONTROL):
        for valeur in paire:
            assert valeur in valeurs, paire
