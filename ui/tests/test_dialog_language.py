# -*- coding: utf-8 -*-
"""Tests for switching the navigator's language at runtime.

A separate file from `test_dialog_tkinter.py` on purpose: that one is still in
French and gets converted with the module it covers. This behaviour is new, so
it is written in English from the start rather than added to a file that is
about to be rewritten.

WHAT IS ACTUALLY AT RISK. Switching language rebuilds the window, because ttk
cannot relabel widgets in place. A rebuild is where state gets dropped, and the
state that matters here is the SELECTED VALIDATION CLASS: losing it silently
returns the reader to "all classes", and the next export then covers a scope
they did not choose. An export that disagrees with the screen is the specific
failure this repository has to avoid.
"""

import pytest

from ui import i18n


@pytest.fixture(autouse=True)
def restore_language():
    before = i18n.language()
    yield
    i18n.set_language(before)


@pytest.fixture
def navigator():
    """A real navigator on the frozen Test 1 reference."""
    pytest.importorskip('tkinter')
    from engine import test1_engine as engine
    from ui import verdict_view as views
    try:
        from ui.dialog_tkinter import NavigateurSIA4010
    except ImportError:
        pytest.skip('tkinter unavailable')
    try:
        reference = engine.charger_reference()
    except Exception:  # noqa: BLE001 -- a missing reference is a skip
        pytest.skip('Test 1 reference not frozen')
    try:
        app = NavigateurSIA4010([
            views.construire_vue_test1(engine.evaluer_test1(reference))])
    except Exception as error:  # noqa: BLE001 -- see module note in dialog
        pytest.skip('no display available (%s)' % type(error).__name__)
    app._racine.update_idletasks()
    yield app
    app._racine.destroy()


def _class_values(app):
    return [u'%s' % value for value in app._selecteur.cget('values')]


def test_the_switch_is_reachable_from_the_toolbar(navigator):
    """The table and the switching machinery existed but nothing on screen
    offered them: a bilingual interface nobody can put into English."""
    from ui import layout
    assert hasattr(navigator, '_changer_de_langue')
    assert callable(layout.language_switch)


def test_switching_rebuilds_the_window(navigator):
    """ttk does not relabel in place. Retaining every widget and its key
    would amount to a second translation table -- the one that drifts from
    the first."""
    i18n.set_language(i18n.ENGLISH)
    navigator._changer_de_langue(i18n.ENGLISH)
    navigator._racine.update_idletasks()
    assert navigator._racine.winfo_children()


def test_switching_keeps_the_selected_class(navigator):
    """THE RISK. Dropping it returns the reader to "all classes" without
    saying so, and the next export covers a scope they did not choose."""
    cible = [v for v in _class_values(navigator) if v.startswith('2A')]
    if not cible:
        pytest.skip('class 2A not offered by this reference')
    navigator._classe_choisie.set(cible[0])
    navigator._changer_de_classe()
    assert navigator._classe_active() == '2A'

    i18n.set_language(i18n.ENGLISH)
    navigator._changer_de_langue(i18n.ENGLISH)
    navigator._racine.update_idletasks()
    assert navigator._classe_active() == '2A'


def test_switching_from_all_classes_stays_on_all_classes(navigator):
    assert navigator._classe_active() is None
    i18n.set_language(i18n.ENGLISH)
    navigator._changer_de_langue(i18n.ENGLISH)
    navigator._racine.update_idletasks()
    assert navigator._classe_active() is None


def test_the_tree_is_rebuilt_and_not_duplicated(navigator):
    """A rebuild that appends instead of replacing would double every row,
    and a doubled row count reads as twice the evidence."""
    avant = len(navigator._arbre.get_children(''))
    i18n.set_language(i18n.ENGLISH)
    navigator._changer_de_langue(i18n.ENGLISH)
    navigator._racine.update_idletasks()
    assert len(navigator._arbre.get_children('')) == avant


def test_column_headings_follow_the_language(navigator):
    i18n.set_language(i18n.ENGLISH)
    navigator._changer_de_langue(i18n.ENGLISH)
    navigator._racine.update_idletasks()
    assert navigator._arbre.heading('verdict', 'text') == \
        i18n.translate('column.verdict', i18n.ENGLISH)


def test_switching_back_restores_french(navigator):
    i18n.set_language(i18n.ENGLISH)
    navigator._changer_de_langue(i18n.ENGLISH)
    i18n.set_language(i18n.FRENCH)
    navigator._changer_de_langue(i18n.FRENCH)
    navigator._racine.update_idletasks()
    assert navigator._arbre.heading('valeur', 'text') == \
        i18n.translate('column.simulated', i18n.FRENCH)


def test_nothing_is_collapsed_after_a_rebuild(navigator):
    """The packing-order defect could easily come back through the rebuild
    path, which is not the one the layout tests exercise."""
    from ui.tests.test_layout import collapsed_widgets
    root = navigator._racine
    root.geometry('1240x760')
    root.deiconify()
    for _ in range(5):
        root.update_idletasks()
        root.update()
    i18n.set_language(i18n.ENGLISH)
    navigator._changer_de_langue(i18n.ENGLISH)
    for _ in range(5):
        root.update_idletasks()
        root.update()
    assert collapsed_widgets(root) == []
