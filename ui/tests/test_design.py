# -*- coding: utf-8 -*-
"""Tests for the IES design tokens (`ui/design.py`).

What these guard is not that the colours are pretty. It is two things that
have gone wrong in this repository before, and would again:

* **a status must never render as something it is not.** An unrecognised
  status resolving to green would report a success nobody measured. The
  engines speak six states; rendering NOT_CHECKABLE as a failure is equally
  wrong -- nothing was compared, so nothing failed;
* **colour must never be the only carrier.** On the ttk themes Windows starts
  with, backgrounds are ignored outright. An interface whose verdicts live in
  the row colour is blank on those machines.
"""

import io
import os
import re

import pytest

from ui import design

# --------------------------------------------------------------------------
# The palette is read, not invented
# --------------------------------------------------------------------------

#: The values carried by a named CSS variable or a frequent literal in the
#: public IES stylesheet, as recorded in the module note.
FROM_STYLESHEET = {
    "ACCENT": "#0f54e8",
    "LIGHT_BLUE": "#00abde",
    "BLUE_TINT": "#e8f1fb",
    "LIGHT_GREY": "#f5f7f9",
    "NAVY": "#1a2b4b",
    "ACCENT_BRIGHT": "#4162fd",
    "TEXT": "#384656",
    "GREEN": "#11bb94",
    "RED": "#de3f3f",
}


@pytest.mark.parametrize("name,value", sorted(FROM_STYLESHEET.items()))
def test_brand_colours_match_the_stylesheet(name, value):
    """These nine are quoted from iesve.com. Drifting from them silently is
    how a house style stops being one."""
    assert getattr(design, name) == value, name


def test_every_colour_is_a_six_digit_hex():
    """A three-digit hex or a named colour renders differently in tkinter and
    in ReportLab -- the dialog and the PDF would disagree."""
    motif = re.compile(r"^#[0-9a-f]{6}$")
    for name in dir(design):
        value = getattr(design, name)
        if isinstance(value, str) and value.startswith("#"):
            assert motif.match(value), (name, value)


def test_the_module_states_where_the_colours_come_from():
    """A palette without provenance cannot be checked, only believed."""
    chemin = os.path.abspath(design.__file__).replace(".pyc", ".py")
    with io.open(chemin, encoding="utf-8") as flux:
        entete = flux.read(3000)
    assert "iesve.com" in entete
    assert "--ha-accent" in entete


# --------------------------------------------------------------------------
# Status semantics: never read as something else
# --------------------------------------------------------------------------


def test_the_six_engine_states_all_have_tokens():
    """The engines speak six states. A view forced to pick among three would
    have to render WARNING or NOT_CHECKABLE as a pass or a failure."""
    assert len(design.STATUSES) == 6
    for status in design.STATUSES:
        assert status in design.STATUS_GROUND, status
        assert status in design.STATUS_STROKE, status
        assert status in design.STATUS_SYMBOL, status
        assert status in design.STATUS_SYMBOL_ASCII, status


def test_an_unknown_status_never_reads_as_success():
    """THE RULE THAT MATTERS. Defaulting to green would report a success
    nobody measured."""
    assert design.ground("no such status") == design.LIGHT_GREY
    assert design.stroke("no such status") == design.NEUTRAL_GREY
    assert design.ground("no such status") != design.STATUS_GROUND[design.PASS]
    assert design.stroke("no such status") != design.GREEN


def test_an_unknown_status_says_so_rather_than_guessing():
    """A question mark is the truthful symbol for "we do not know"."""
    assert design.symbol("no such status") == "?"
    assert design.symbol("no such status", ascii_only=True) == "?"


def test_not_checkable_is_not_dressed_as_a_failure():
    """Nothing was compared, so nothing failed. Rendering it in the failure
    red would misreport a missing input as a wrong answer."""
    assert design.ground(design.NOT_CHECKABLE) != design.STATUS_GROUND[design.FAIL]
    assert design.stroke(design.NOT_CHECKABLE) != design.RED


def test_pass_and_fail_never_share_a_ground_or_a_symbol():
    for table in (
        design.STATUS_GROUND,
        design.STATUS_SYMBOL,
        design.STATUS_SYMBOL_ASCII,
        design.STATUS_STROKE,
    ):
        assert table[design.PASS] != table[design.FAIL]


def test_every_symbol_is_distinct():
    """Two states sharing a glyph is the same defect as sharing a colour."""
    assert len(set(design.STATUS_SYMBOL.values())) == len(design.STATUS_SYMBOL)


def test_the_ascii_variant_stays_ascii():
    """The VEScripts console is not UTF-8; a glyph there prints as mojibake
    or raises."""
    for status, texte in sorted(design.STATUS_SYMBOL_ASCII.items()):
        texte.encode("ascii")  # raises if it is not


# --------------------------------------------------------------------------
# Legacy colour names, during the conversion
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "legacy,status",
    [
        ("vert", design.PASS),
        ("rouge", design.FAIL),
        ("gris", design.NOT_EVALUATED),
    ],
)
def test_a_legacy_colour_name_resolves_to_its_status(legacy, status):
    """Callers not yet converted must keep rendering correctly -- a silent
    change of meaning mid-conversion is worse than a crash."""
    assert design.ground(legacy) == design.STATUS_GROUND[status]
    assert design.symbol(legacy) == design.STATUS_SYMBOL[status]


def test_the_legacy_map_is_input_only():
    """Nothing renders from it. It exists to be deleted."""
    for status in design.LEGACY_COLOUR_TO_STATUS.values():
        assert status in design.STATUSES


# --------------------------------------------------------------------------
# The space scale
# --------------------------------------------------------------------------


def test_every_gap_is_a_multiple_of_the_base():
    """A scale with an odd member is not a scale."""
    for name, value in sorted(design.SPACE.items()):
        assert value % 4 == 0, (name, value)


def test_the_scale_is_strictly_increasing():
    ordre = ["xs", "sm", "md", "lg", "xl", "xxl"]
    valeurs = [design.SPACE[nom] for nom in ordre]
    assert valeurs == sorted(valeurs)
    assert len(set(valeurs)) == len(valeurs)


def test_a_gap_outside_the_scale_is_refused():
    """Refusing is the point: a one-off gap is how a scale stops being one."""
    with pytest.raises(KeyError):
        design.space("enormous")


def test_space_returns_a_tuple_for_several_names():
    assert design.space("sm", "lg") == (design.SPACE["sm"], design.SPACE["lg"])


# --------------------------------------------------------------------------
# Typography
# --------------------------------------------------------------------------


def test_report_fonts_stay_embeddable():
    """Camphor Pro is commercial. Setting it here would produce PDFs we may
    not distribute -- and the failure would be legal, not technical."""
    for police in (
        design.REPORT_TITLE_FONT,
        design.REPORT_BODY_FONT,
        design.REPORT_BODY_BOLD_FONT,
    ):
        assert police.startswith("Helvetica"), police


def test_the_type_scale_is_strictly_decreasing():
    tailles = [
        design.SIZE_DISPLAY,
        design.SIZE_TITLE,
        design.SIZE_SUBTITLE,
        design.SIZE_SECTION,
        design.SIZE_BODY,
        design.SIZE_CAPTION,
    ]
    assert tailles == sorted(tailles, reverse=True)


def test_the_window_has_a_floor():
    """Without a minimum the results table collapses to unreadable column
    widths, and the reader silently loses the reference band."""
    assert design.WINDOW_MIN_WIDTH < design.WINDOW_WIDTH
    assert design.WINDOW_MIN_HEIGHT < design.WINDOW_HEIGHT
    assert design.WINDOW_MIN_WIDTH >= 900
