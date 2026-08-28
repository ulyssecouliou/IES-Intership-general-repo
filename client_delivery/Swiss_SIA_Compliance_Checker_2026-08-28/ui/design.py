# -*- coding: utf-8 -*-
"""IES design tokens -- single source for the navigator and the reports.

WHERE THE COLOURS COME FROM. They are not chosen, they are READ from the
public IES stylesheet `https://www.iesve.com/assets/css/styles.css` (692 KB,
read 2026-08-06), keeping the values carried by a named CSS variable and the
most frequent hex literals:

    --ha-accent      #0f54e8      26 occurrences
    --lightblue      #00abde      named variable
    --lightblue-fade #e8f1fb      named variable
    --light-grey     #f5f7f9      named variable
    navy             #1a2b4b      13 occurrences
    bright blue      #4162fd      31 occurrences
    body text        #384656       7 occurrences
    green            #11bb94      13 occurrences
    red              #de3f3f       5 occurrences

Anything below that is NOT in that list is derived arithmetically from one of
these -- tints and shades, never a new hue. The derivation is stated on each
token so it can be checked.

TYPOGRAPHY, AND ONE LICENCE RESERVATION. The site sets Camphor Pro, a
commercial face we may not embed in a PDF without a licence. Reports therefore
use Helvetica, which ships with ReportLab and is the closest geometric
sans-serif available. If IES holds a Camphor Pro licence for document
distribution, changing `REPORT_TITLE_FONT` and `REPORT_BODY_FONT` here is the
whole change.

HOW THE HOUSE STYLE DIVIDES SPACE. The site separates with whitespace, not
with heavy rules: full-width navy band, very light grey ground, white cards,
hairline rules, accent blue reserved for actions. Solid areas of bright colour
are rare and small. `SPACE` exists so that discipline survives contact with
layout code -- ad-hoc padding is what makes an interface look assembled rather
than designed.

ACCESSIBILITY. A verdict is NEVER carried by colour alone. Every status has a
symbol (`STATUS_SYMBOL`) and a word beside it. This is a `CLAUDE.md`
requirement, and the only way to stay readable on a ttk theme that ignores
`background`, or for a colour-blind reader.
"""

# ---------------------------------------------------------------------------
# Brand palette -- read from the stylesheet
# ---------------------------------------------------------------------------

NAVY = "#1a2b4b"  #: Bands, headings, table headers.
NAVY_DEEP = "#193054"  #: Darker variant: rules and footers.
NAVY_TINT = "#2c3f63"  #: Derived: NAVY lightened, for band sub-text.
ACCENT = "#0f54e8"  #: --ha-accent: links, emphasis, primary action.
ACCENT_BRIGHT = "#4162fd"  #: Secondary accent, hover state.
ACCENT_DEEP = "#0b3fb0"  #: Derived: ACCENT darkened, pressed state.
LIGHT_BLUE = "#00abde"  #: --lightblue.
BLUE_TINT = "#e8f1fb"  #: --lightblue-fade: table header ground.
BLUE_TINT_DEEP = "#d3e3f7"  #: Derived: BLUE_TINT darkened, selected row.
LIGHT_GREY = "#f5f7f9"  #: --light-grey: page ground, row striping.
BORDER_GREY = "#dce0eb"  #: Table hairlines, card edges.
BORDER_GREY_DEEP = "#c3cad9"  #: Derived: stronger edge where two cards meet.
TEXT = "#384656"  #: Body text.
TEXT_MUTED = "#6b7a8f"  #: Captions, table footnotes.
TEXT_ON_DARK = "#eef2f8"  #: Derived: body text on the navy band.
WHITE = "#ffffff"

GREEN = "#11bb94"  #: Pass.
RED = "#de3f3f"  #: Fail.
AMBER = "#ff973f"  #: Reservation, attention.
NEUTRAL_GREY = "#8b98aa"  #: Not evaluated.

# ---------------------------------------------------------------------------
# Status semantics
# ---------------------------------------------------------------------------
#
# The engines speak six states, not three. The previous token set had only
# green / red / grey, which forced WARNING and NOT_CHECKABLE to render as one
# of the three -- and NOT_CHECKABLE rendering as anything failure-like is a
# misreport: nothing was compared, so nothing failed.

PASS = "pass"
FAIL = "fail"
WARNING = "warning"
NOT_CHECKABLE = "not_checkable"
NOT_EVALUATED = "not_evaluated"
NOT_SIGNED = "not_signed"

STATUSES = (PASS, FAIL, WARNING, NOT_CHECKABLE, NOT_EVALUATED, NOT_SIGNED)

#: Row grounds. Pale enough to stay legible under dark text -- these sit
#: behind body copy, not beside it.
STATUS_GROUND = {
    PASS: "#e6f7f1",
    FAIL: "#fdeaea",
    WARNING: "#fff4e8",
    NOT_CHECKABLE: "#eef1f6",
    NOT_EVALUATED: LIGHT_GREY,
    NOT_SIGNED: "#eef1f6",
}

#: Stroke colour, for hairlines, dots and the left edge of a status card.
STATUS_STROKE = {
    PASS: GREEN,
    FAIL: RED,
    WARNING: AMBER,
    NOT_CHECKABLE: NEUTRAL_GREY,
    NOT_EVALUATED: NEUTRAL_GREY,
    NOT_SIGNED: NEUTRAL_GREY,
}

# ---------------------------------------------------------------------------
# Status colours for TEXT, derived
# ---------------------------------------------------------------------------
#
# WHY THESE EXIST. The four hues above are stroke colours and none of them is
# legible as text. Measured against white: GREEN 2.45:1, RED 4.30:1,
# AMBER 2.15:1, NEUTRAL_GREY 2.93:1 — all below the 4.5:1 that WCAG AA asks of
# body text. Setting a verdict word in STATUS_STROKE would put the report below
# the threshold its own accessibility rule implies.
#
# Each value below is its base hue scaled uniformly in RGB by the stated
# factor: a shade, never a new hue, as this module requires. The two ratios are
# measured, not asserted — on white, and on the STATUS_GROUND the word sits on.
#
#   status    base            factor  derived   /white  /ground
#   PASS      GREEN           0.60    #0a7059   6.04    5.45
#   FAIL      RED             0.70    #9b2c2c   7.53    6.50
#   WARNING   AMBER           0.58    #945825   5.70    5.26
#   neutral   NEUTRAL_GREY    0.72    #646d7a   5.24    4.63
#
# One observation, left as such rather than silently changed: TEXT_MUTED
# reaches 4.37:1 on white, marginally under AA for the 7 pt note size. It is a
# long-standing token used by the navigator too, so raising it is a decision
# for the house style, not a side effect of this table.

GREEN_TEXT = "#0a7059"  #: Derived: GREEN x0.60. 6.04:1 on white.
RED_TEXT = "#9b2c2c"  #: Derived: RED x0.70. 7.53:1 on white.
AMBER_TEXT = "#945825"  #: Derived: AMBER x0.58. 5.70:1 on white.
NEUTRAL_TEXT = "#646d7a"  #: Derived: NEUTRAL_GREY x0.72. 5.24:1 on white.

#: Colour for a verdict WORD, or any status-carrying text. Never use
#: STATUS_STROKE for type.
STATUS_TEXT = {
    PASS: GREEN_TEXT,
    FAIL: RED_TEXT,
    WARNING: AMBER_TEXT,
    NOT_CHECKABLE: NEUTRAL_TEXT,
    NOT_EVALUATED: NEUTRAL_TEXT,
    NOT_SIGNED: NEUTRAL_TEXT,
}

#: Deliberate redundancy with colour -- never information by colour alone.
#: Taken verbatim by the navigator and by the PDF, so they cannot drift.
STATUS_SYMBOL = {
    PASS: "✔",  # heavy check
    FAIL: "✘",  # heavy ballot X
    WARNING: "⚠",  # warning sign
    NOT_CHECKABLE: "—",  # em dash
    NOT_EVALUATED: "·",  # middle dot
    NOT_SIGNED: "○",  # open circle
}

#: ASCII variant, for the VEScripts console, which is not UTF-8.
STATUS_SYMBOL_ASCII = {
    PASS: "OK",
    FAIL: "NO",
    WARNING: "!",
    NOT_CHECKABLE: "--",
    NOT_EVALUATED: ".",
    NOT_SIGNED: "o",
}

#: Legacy colour names, kept ONLY as an input mapping for callers that still
#: pass 'vert' / 'rouge' / 'gris'. Nothing renders from these; they resolve to
#: a status above. Delete when the last caller is converted.
LEGACY_COLOUR_TO_STATUS = {
    "vert": PASS,
    "rouge": FAIL,
    "gris": NOT_EVALUATED,
    "green": PASS,
    "red": FAIL,
    "grey": NOT_EVALUATED,
}

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

#: Face for the generated workbook. Calibri, not because it is the house face
#: but because it is the one present on every Office install: a workbook that
#: falls back to a substitute face re-flows its own column widths. Camphor Pro
#: cannot be embedded (see the module note) and Segoe UI is a Windows-only
#: assumption for a file a client may open anywhere. Recorded here so the choice
#: has one home rather than 285 scattered format dictionaries.
EXCEL_FONT = "Calibri"

#: See the licence reservation in the module note: Camphor Pro is not
#: embeddable, so reports set Helvetica.
REPORT_TITLE_FONT = "Helvetica-Bold"
REPORT_BODY_FONT = "Helvetica"
REPORT_BODY_BOLD_FONT = "Helvetica-Bold"

#: Screen face. Camphor Pro is commercial; Segoe UI is the closest thing
#: present out of the box on Windows, where VE runs.
UI_FONT = "Segoe UI"
UI_FONT_MONO = "Consolas"

#: A modular scale, ratio 1.2 rounded to whole points. Sizes chosen ad hoc are
#: what makes a hierarchy read as noise.
SIZE_DISPLAY = 22
SIZE_TITLE = 18
SIZE_SUBTITLE = 13
SIZE_SECTION = 11
SIZE_BODY = 9
SIZE_TABLE = 9
SIZE_CAPTION = 8

#: Report sizes, in points. Print takes a tighter scale than screen.
REPORT_SIZE_TITLE = 20
REPORT_SIZE_SUBTITLE = 13
REPORT_SIZE_SECTION = 11
REPORT_SIZE_BODY = 9
REPORT_SIZE_TABLE = 7.5
REPORT_SIZE_NOTE = 7

#: Leading, as a multiple of the font size.
LINE_HEIGHT = 1.35

# ---------------------------------------------------------------------------
# Space
# ---------------------------------------------------------------------------

#: One scale, 4 px base. Every gap in the interface is a member of this scale
#: -- that is what makes the layout look deliberate rather than assembled.
SPACE = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "xxl": 32,
}

#: Card and band padding, as (horizontal, vertical).
PAD_BAND = (SPACE["xl"], SPACE["lg"])
PAD_CARD = (SPACE["lg"], SPACE["md"])
PAD_CONTROL = (SPACE["md"], SPACE["sm"])

#: Table row height. Generous: the house style divides by space.
ROW_HEIGHT = 28
HEADER_ROW_HEIGHT = 32

#: Window geometry. The minimum stops the results table from collapsing to
#: unreadable column widths. The default width is set from a MEASUREMENT, not
#: a guess: at 1180 the composed dialog requested 1189 and the last export
#: button was clipped -- an unreachable action, with nothing to say so.
WINDOW_WIDTH = 1240
WINDOW_HEIGHT = 760
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 600

# ---------------------------------------------------------------------------
# Report page layout
# ---------------------------------------------------------------------------

MARGIN_CM = 1.6
SECTION_SPACE_CM = 0.55
PARAGRAPH_SPACE_CM = 0.25

#: Table hairline weight, in points. Thin: the house style divides by space,
#: not by heavy rules.
RULE_PT = 0.4
HEADER_RULE_PT = 0.8

#: Accent bar down the left of a status card, in points.
STATUS_BAR_PT = 2.5


def _resolve(status):
    """Accept a status or a legacy colour name, return a status.

    Args:
        status: One of `STATUSES`, or a legacy `'vert'`/`'rouge'`/`'gris'`.

    Returns:
        str | None: A member of `STATUSES`, or `None` if unrecognised.
    """
    if status in STATUS_GROUND:
        return status
    return LEGACY_COLOUR_TO_STATUS.get(status)


def ground(status):
    """Row ground for a status.

    Args:
        status: One of `STATUSES`, or a legacy colour name.

    Returns:
        str: Hex colour. Neutral grey for an unrecognised status -- never
        green: an unexpected value must not read as success.
    """
    resolved = _resolve(status)
    return STATUS_GROUND[resolved] if resolved else LIGHT_GREY


def stroke(status):
    """Stroke colour for a status.

    Args:
        status: One of `STATUSES`, or a legacy colour name.

    Returns:
        str: Hex colour; neutral grey for an unrecognised status.
    """
    resolved = _resolve(status)
    return STATUS_STROKE[resolved] if resolved else NEUTRAL_GREY


def symbol(status, ascii_only=False):
    """Symbol for a status.

    Args:
        status: One of `STATUSES`, or a legacy colour name.
        ascii_only: True for the VEScripts console.

    Returns:
        str: Symbol; `'?'` for an unrecognised status. A question mark is
        correct here: it says "we do not know", which is the truth.
    """
    table = STATUS_SYMBOL_ASCII if ascii_only else STATUS_SYMBOL
    resolved = _resolve(status)
    return table[resolved] if resolved else "?"


def space(*names):
    """Look up one or more gaps from the scale.

    Args:
        *names: Keys of `SPACE`.

    Returns:
        int | tuple: The value, or a tuple of them.

    Raises:
        KeyError: For a name outside the scale. Refusing is the point: a
            one-off gap is how a scale stops being one.
    """
    if len(names) == 1:
        return SPACE[names[0]]
    return tuple(SPACE[name] for name in names)
