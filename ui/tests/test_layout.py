# -*- coding: utf-8 -*-
"""Tests for the composable chrome (`ui/layout.py`).

These build REAL widgets. A layout module tested against doubles proves that
the code runs, which was never in doubt; what is in doubt is whether ttk
accepts the style names, honours the padding and renders the tags -- and only
a real Tk answers that.

Three things are guarded beyond "it does not crash":

* **an unrecognised status must not borrow another status's badge.** It would
  render as whatever that status means, which is a misreport with a confident
  face;
* **one primary button per window.** Two accent-blue buttons side by side stop
  meaning "this is the action";
* **an empty panel must say what to do.** A blank panel reads as "no problems
  found", which is the opposite of the truth when the real reason is that no
  simulation has run.
"""

import pytest

from ui import design
from ui import i18n
from ui import layout
from ui import theme


@pytest.fixture
def root():
    """A real Tk window with the house style applied."""
    tkinter = pytest.importorskip("tkinter")
    try:
        window = tkinter.Tk()
    except Exception:  # noqa: BLE001 -- no display is a skip, not a failure
        pytest.skip("no display available")
    window.withdraw()
    theme.apply(window)
    yield window
    window.destroy()


@pytest.fixture(autouse=True)
def restore_language():
    before = i18n.language()
    yield
    i18n.set_language(before)


# --------------------------------------------------------------------------
# Cards and rules
# --------------------------------------------------------------------------


def test_a_card_has_an_edge_behind_it(root):
    """ttk draws no border we can colour across themes, so the edge is a
    frame behind the card. Without it a white card on a light grey ground has
    no shape at all."""
    outer, inner = layout.card(root)
    assert str(outer.cget("style")) == theme.STYLE_CARD_EDGE
    assert str(inner.cget("style")) == theme.STYLE_CARD
    assert int(str(outer.cget("padding")[0])) == layout.EDGE


def test_card_padding_comes_from_the_scale(root):
    _, inner = layout.card(root)
    padding = [int(str(value)) for value in inner.cget("padding")]
    for value in padding:
        assert value in design.SPACE.values(), padding


def test_a_rule_is_one_pixel(root):
    for orientation, option in (("horizontal", "height"), ("vertical", "width")):
        separator = layout.rule(root, orientation)
        assert int(separator.cget(option)) == layout.EDGE


# --------------------------------------------------------------------------
# The header band
# --------------------------------------------------------------------------


def test_the_band_carries_titles_and_an_action_cluster(root):
    band = layout.header_band(root)
    assert sorted(band) == ["actions", "band", "titles"]
    assert str(band["band"].cget("style")) == theme.STYLE_BAND


def test_the_band_names_the_product(root):
    """VEScripts dialogs open with no chrome of their own: without the
    eyebrow, nothing on screen says which product this window belongs to."""
    band = layout.header_band(root)
    textes = [child.cget("text") for child in band["titles"].winfo_children()]
    assert any(i18n.t("app.product").upper() in str(t) for t in textes)


def test_the_band_follows_the_language_in_force(root):
    i18n.set_language(i18n.ENGLISH)
    band = layout.header_band(root)
    textes = [str(child.cget("text")) for child in band["titles"].winfo_children()]
    assert i18n.t("app.title") in textes


# --------------------------------------------------------------------------
# Buttons
# --------------------------------------------------------------------------


def test_a_primary_button_takes_the_accent_style(root):
    band = layout.header_band(root)
    button = layout.action_button(
        band["actions"], "action.export_excel", lambda: None, primary=True
    )
    assert str(button.cget("style")) == theme.STYLE_BUTTON_PRIMARY


def test_a_plain_button_does_not(root):
    band = layout.header_band(root)
    button = layout.action_button(band["actions"], "action.export_pdf", lambda: None)
    assert str(button.cget("style")) == theme.STYLE_BUTTON


def test_primary_and_quiet_together_are_refused(root):
    """Opposite intentions. Silently picking one would give the window two
    visual hierarchies."""
    band = layout.header_band(root)
    with pytest.raises(ValueError):
        layout.action_button(
            band["actions"], "action.close", lambda: None, primary=True, quiet=True
        )


def test_a_button_label_goes_through_the_table(root):
    band = layout.header_band(root)
    button = layout.action_button(band["actions"], "action.close", lambda: None)
    assert str(button.cget("text")) == i18n.t("action.close")


def test_an_unknown_label_key_raises_rather_than_rendering_blank(root):
    band = layout.header_band(root)
    with pytest.raises(i18n.MissingTranslation):
        layout.action_button(band["actions"], "action.no_such", lambda: None)


# --------------------------------------------------------------------------
# Status badges and the strip
# --------------------------------------------------------------------------


@pytest.mark.parametrize("status", design.STATUSES)
def test_a_badge_takes_the_style_of_its_status(root, status):
    badge = layout.status_badge(root, status, "X")
    assert str(badge.cget("style")) == theme.STYLE_BADGE[status]


@pytest.mark.parametrize("status", design.STATUSES)
def test_a_badge_always_shows_its_symbol(root, status):
    """Colour is never the only carrier -- on the ttk themes Windows starts
    with, the ground may not render at all."""
    badge = layout.status_badge(root, status, "WORD")
    texte = str(badge.cget("text"))
    assert design.STATUS_SYMBOL[status] in texte
    assert "WORD" in texte


def test_an_unknown_status_does_not_borrow_another_badge(root):
    """It would render as whatever that status means: a misreport with a
    confident face."""
    badge = layout.status_badge(root, "no such status", "X")
    assert str(badge.cget("style")) == theme.STYLE_BADGE[design.NOT_EVALUATED]
    assert str(badge.cget("style")) != theme.STYLE_BADGE[design.PASS]


def test_a_legacy_colour_name_still_finds_its_badge(root):
    badge = layout.status_badge(root, "rouge", "X")
    assert str(badge.cget("style")) == theme.STYLE_BADGE[design.FAIL]


def test_the_strip_shows_one_badge_per_test(root):
    """One verdict per test, never an aggregate: an aggregate hides WHICH
    test fails, and that is the only thing this row is for."""
    band = layout.header_band(root)
    strip = layout.status_strip(
        band["titles"],
        [
            {"label": "Test 1", "status": design.NOT_EVALUATED, "text": "A"},
            {"label": "Test 7", "status": design.FAIL, "text": "B"},
        ],
    )
    assert len(strip.winfo_children()) == 2


def test_the_strip_survives_an_empty_list(root):
    band = layout.header_band(root)
    strip = layout.status_strip(band["titles"], [])
    assert strip.winfo_children() == []


# --------------------------------------------------------------------------
# Toolbar, headings, empty state, footer
# --------------------------------------------------------------------------


def test_the_toolbar_splits_left_right_and_caption(root):
    bar = layout.toolbar(root)
    assert sorted(bar) == ["caption", "inner", "left", "outer", "right", "row"]


def test_the_caption_row_sits_below_the_controls(root):
    """A state line packed after the buttons on the SAME row was truncated as
    soon as they took their width -- and a truncated state hides the list of
    missing tests, which is exactly what has to be read."""
    bar = layout.toolbar(root)
    children = bar["inner"].winfo_children()
    assert children.index(bar["row"]) < children.index(bar["caption"])


def test_a_section_heading_can_carry_a_note(root):
    _, inner = layout.card(root)
    layout.section_heading(inner, "section.results", "note.pass_is_not_compliance")
    textes = [str(child.cget("text")) for child in inner.winfo_children()]
    assert i18n.t("section.results") in textes
    assert i18n.t("note.pass_is_not_compliance") in textes


def test_an_empty_state_says_what_to_do(root):
    """A blank panel reads as "no problems found" -- the opposite of the truth
    when the real reason is that no simulation has run."""
    _, inner = layout.card(root)
    label = layout.empty_state(inner, "state.no_results")
    texte = str(label.cget("text"))
    assert texte == i18n.t("state.no_results")
    assert texte.strip()


def test_the_footer_carries_the_standing_reminder(root):
    """The confusion it guards against happens while someone is looking at
    the screen, not only when they read the report."""
    outer = layout.footer(root)
    inner = outer.winfo_children()[0]
    textes = [str(child.cget("text")) for child in inner.winfo_children()]
    assert any(i18n.t("note.pass_is_not_compliance") in t for t in textes)


def test_the_footer_reminder_carries_a_symbol_too(root):
    outer = layout.footer(root)
    inner = outer.winfo_children()[0]
    texte = str(inner.winfo_children()[0].cget("text"))
    assert design.STATUS_SYMBOL[design.WARNING] in texte


# --------------------------------------------------------------------------
# Language switch
# --------------------------------------------------------------------------


def test_the_language_switch_offers_every_language(root):
    bar = layout.toolbar(root)
    box = layout.language_switch(bar["right"], lambda code: None)
    assert len(box.cget("values")) == len(i18n.LANGUAGES)


def test_switching_language_calls_back_with_the_code(root):
    bar = layout.toolbar(root)
    seen = []
    box = layout.language_switch(bar["right"], seen.append)
    box.set(i18n.t("language.en"))
    box.event_generate("<<ComboboxSelected>>")
    assert seen == [i18n.ENGLISH]
    assert i18n.language() == i18n.ENGLISH


# --------------------------------------------------------------------------
# Results table
# --------------------------------------------------------------------------

COLUMNS = (
    ("value", "column.simulated", 110, "e"),
    ("band", "column.band", 180, "e"),
    ("verdict", "column.verdict", 130, "center"),
)


def test_the_table_heads_every_column_from_the_table(root):
    built = layout.results_table(root, COLUMNS)
    for identifier, key, _, _ in COLUMNS:
        assert built["tree"].heading(identifier, "text") == i18n.t(key)


def test_the_table_returns_one_tag_per_status(root):
    """Returning them stops a caller inventing its own tag and getting a FAIL
    that renders like a NOT EVALUATED."""
    built = layout.results_table(root, COLUMNS)
    assert sorted(built["tags"]) == sorted(design.STATUSES)


def test_numeric_columns_are_right_aligned(root):
    """Digits that do not line up are measurably harder to scan for an
    outlier, and scanning for the outlier is what this table is for."""
    built = layout.results_table(root, COLUMNS)
    for identifier in ("value", "band"):
        assert str(built["tree"].column(identifier, "anchor")) == "e"


def test_the_table_sits_in_a_card(root):
    built = layout.results_table(root, COLUMNS)
    assert str(built["outer"].cget("style")) == theme.STYLE_CARD_EDGE


# --------------------------------------------------------------------------
# Packing order -- the silent defect, met three times
# --------------------------------------------------------------------------


def collapsed_widgets(window, floor=40):
    """Widgets that asked for real width and were given none.

    Tk allocates to its children in packing order. A child packed with
    `expand=True` BEFORE its siblings takes the whole cavity, and the ones
    after it are allocated one pixel -- with no error, no warning, and no
    exception. They simply are not there.

    Args:
        window: Root or container to walk.
        floor: Requested width above which being allocated nothing is a bug.

    Returns:
        list: `(class, requested, allocated)` for each collapsed widget.
    """
    found = []
    for child in window.winfo_children():
        if child.winfo_reqwidth() > floor and child.winfo_width() <= 2:
            found.append(
                (child.winfo_class(), child.winfo_reqwidth(), child.winfo_width())
            )
        found.extend(collapsed_widgets(child, floor))
    return found


def _mapped(window, height=design.WINDOW_HEIGHT):
    """Give a window a real size and map it, then settle the geometry.

    Without this every widget measures one pixel wide, because an unmapped
    window has no cavity to allocate -- so a collapse test on a withdrawn
    window PASSES for the wrong reason: it "detects" a collapse that is only
    the window not being on screen. This helper exists because that exact
    mistake was made here first.

    Args:
        window: The root window.
        height: Window height. Pass a small value to reproduce a cavity too
            short for the content, which is what actually starves siblings.
    """
    window.geometry("%dx%d" % (design.WINDOW_WIDTH, height))
    window.deiconify()
    for _ in range(5):
        window.update_idletasks()
        window.update()


#: A cavity deliberately shorter than a table plus a detail panel plus a
#: footer. The real dialog hits the same condition at full size, because the
#: table alone asks for more than the window has.
CRAMPED_HEIGHT = 240


def test_content_taller_than_the_window_starves_whatever_is_packed_last(root):
    """THE DEFECT, reproduced. It is NOT that `expand` steals from
    siblings --
    `expand` only shares out what is left over. It is that when the requested
    sizes exceed the cavity, Tk satisfies them in PACKING ORDER and the last
    ones get nothing: no error, no warning, they simply are not there.

    In the dialog this cost the footer and then the detail panel, so the
    reminder "a technical PASS is not compliance" left the screen -- exactly
    where the confusion it prevents happens."""
    built = layout.results_table(root, COLUMNS)
    built["outer"].pack(side="top", fill="both", expand=True)
    layout.footer(root)
    _mapped(root, CRAMPED_HEIGHT)
    assert collapsed_widgets(
        root
    ), "expected the footer to be starved when packed after the table"


def test_the_shrinkable_widget_packed_last_absorbs_the_shortfall(root):
    """THE FIX. The table is the only widget that can give ground -- it
    scrolls. Packing it last makes it absorb the shortfall instead of the
    fixed-height cards."""
    layout.footer(root)
    built = layout.results_table(root, COLUMNS)
    built["outer"].pack(side="top", fill="both", expand=True)
    _mapped(root, CRAMPED_HEIGHT)
    assert collapsed_widgets(root) == []


def test_the_toolbar_serves_its_right_cluster_first(root):
    """A left cluster with `expand=True` packed first pushed the export
    buttons out of the window -- an unreachable action, with nothing to say
    so."""
    bar = layout.toolbar(root)
    children = bar["row"].winfo_children()
    assert (
        children[0] is bar["right"]
    ), "the right cluster must be packed before the expanding left one"


def test_the_band_serves_its_actions_first(root):
    band = layout.header_band(root)
    children = band["band"].winfo_children()
    assert children[0] is band["actions"]
