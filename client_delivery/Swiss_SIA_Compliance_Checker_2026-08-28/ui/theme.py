# -*- coding: utf-8 -*-
"""Apply the IES house style to a ttk window.

`ui/design.py` holds the tokens, read from the public iesve.com stylesheet.
This module APPLIES them: without it the tokens exist and the dialog stays
default ttk, system grey.

THE ONE TECHNICAL FACT THAT DECIDES EVERYTHING. On Windows, ttk starts on the
`vista` (or `winnative`) theme, which hands rendering to the OS and **ignores
`background`, `foreground` and `fieldbackground` outright** on most widgets.
An earlier note in the dialog flagged this as unverified; it is now verified:
without changing theme, the brand colours simply do not appear.

`clam` honours them. That is why `apply` switches, and it is the only reason
-- not an aesthetic preference. If `clam` were missing (not observed, but
possible on a minimal install) the current theme is kept: an interface in
system colours is still usable, an exception is not.

WHAT THE HOUSE STYLE ASKS, AND WHAT IS DONE HERE. The site divides by space,
not by heavy rules: a full-width navy band, a very light grey ground, white
cards, hairlines, accent blue reserved for actions. Solid areas of bright
colour are rare and small. Every gap here comes from `design.SPACE`, so the
discipline survives contact with layout code.

ACCESSIBILITY. No verdict is carried by colour alone: the symbol and the word
always accompany it (`design.symbol`). That rule survives the theme switch,
and it is what keeps the interface readable for a colour-blind reader -- or on
a machine where the theme still refuses backgrounds.
"""

from __future__ import print_function

from ui import design

#: ttk theme that honours colours. See the module note: not a style choice,
#: the precondition for the house style to render at all.
REQUIRED_THEME = "clam"

#: Namespace for exposed style names. Prefixing avoids clobbering the styles
#: of another VEScripts dialog in the same interpreter -- which persists from
#: one click on Run to the next.
PREFIX = "IES."

STYLE_GROUND = PREFIX + "TFrame"
STYLE_CARD = PREFIX + "Card.TFrame"
STYLE_CARD_EDGE = PREFIX + "CardEdge.TFrame"
STYLE_BAND = PREFIX + "Band.TFrame"
STYLE_TOOLBAR = PREFIX + "Toolbar.TFrame"
STYLE_RULE = PREFIX + "Rule.TFrame"

STYLE_DISPLAY = PREFIX + "Display.TLabel"
STYLE_TITLE = PREFIX + "Title.TLabel"
STYLE_SUBTITLE = PREFIX + "Subtitle.TLabel"
STYLE_BODY = PREFIX + "TLabel"
STYLE_MUTED = PREFIX + "Muted.TLabel"
STYLE_SECTION = PREFIX + "Section.TLabel"
STYLE_CAPTION = PREFIX + "Caption.TLabel"
STYLE_MONO = PREFIX + "Mono.TLabel"
STYLE_BAND_TEXT = PREFIX + "BandText.TLabel"

STYLE_BUTTON = PREFIX + "TButton"
STYLE_BUTTON_PRIMARY = PREFIX + "Primary.TButton"
STYLE_BUTTON_QUIET = PREFIX + "Quiet.TButton"
STYLE_CHECK = PREFIX + "TCheckbutton"
STYLE_RADIO = PREFIX + "TRadiobutton"
STYLE_COMBO = PREFIX + "TCombobox"
STYLE_ENTRY = PREFIX + "TEntry"
STYLE_NOTEBOOK = PREFIX + "TNotebook"
STYLE_PROGRESS = PREFIX + "Horizontal.TProgressbar"
STYLE_SCROLLBAR = PREFIX + "Vertical.TScrollbar"
STYLE_TREE = PREFIX + "Treeview"
STYLE_LABELFRAME = PREFIX + "TLabelframe"

#: One style per status, for the badge that carries a verdict. Built rather
#: than written out so a status added to `design.STATUSES` cannot be forgotten
#: here -- a badge missing its style renders as default grey, which would make
#: a FAIL look like NOT EVALUATED.
STYLE_BADGE = dict(
    (status, PREFIX + "Badge%s.TLabel" % status.title().replace("_", ""))
    for status in design.STATUSES
)

#: Treeview row tags, one per status. Same reasoning as `STYLE_BADGE`.
ROW_TAG = dict((status, "ies_row_%s" % status) for status in design.STATUSES)


def apply(root):
    """Apply the house style to a window and return the configured style.

    Args:
        root: A `tkinter.Tk` or `Toplevel`.

    Returns:
        ttk.Style: The configured style, for any further tuning.

    Raises:
        ImportError: If tkinter is unavailable -- this module only means
            anything inside VEScripts.
    """
    try:
        from tkinter import ttk
    except ImportError as error:
        raise ImportError(
            "tkinter unavailable: the house style can only be applied to a "
            "real interface (%s)" % error
        )

    style = ttk.Style(root)
    _force_theme(style)
    root.configure(background=design.LIGHT_GREY)
    for configure in (
        _ground_styles,
        _text_styles,
        _button_styles,
        _input_styles,
        _table_style,
        _badge_styles,
        _chrome_styles,
    ):
        configure(style)
    return style


def _force_theme(style):
    """Switch to a theme that honours colours.

    Args:
        style: A `ttk.Style`.

    Returns:
        str: The theme actually in force.
    """
    if REQUIRED_THEME in style.theme_names():
        style.theme_use(REQUIRED_THEME)
    return style.theme_use()


def _ground_styles(style):
    """Frames: page ground, white cards, navy band, hairline rule.

    Args:
        style: A `ttk.Style`.
    """
    style.configure(STYLE_GROUND, background=design.LIGHT_GREY)
    style.configure(STYLE_CARD, background=design.WHITE, relief="flat", borderwidth=0)
    # A card reads as a card because of its edge, not because of a shadow --
    # ttk has no shadow, and a faked one looks worse than none.
    style.configure(
        STYLE_CARD_EDGE, background=design.BORDER_GREY, relief="flat", borderwidth=0
    )
    style.configure(STYLE_BAND, background=design.NAVY)
    style.configure(STYLE_TOOLBAR, background=design.WHITE)
    style.configure(STYLE_RULE, background=design.BORDER_GREY)
    style.configure(
        STYLE_LABELFRAME,
        background=design.WHITE,
        bordercolor=design.BORDER_GREY,
        relief="solid",
        borderwidth=1,
    )
    style.configure(
        STYLE_LABELFRAME + ".Label",
        background=design.WHITE,
        foreground=design.NAVY,
        font=(design.UI_FONT, design.SIZE_BODY, "bold"),
    )


def _text_styles(style):
    """Labels: band headings, body, muted, captions, monospace.

    Args:
        style: A `ttk.Style`.
    """
    style.configure(
        STYLE_DISPLAY,
        background=design.NAVY,
        foreground=design.WHITE,
        font=(design.UI_FONT, design.SIZE_DISPLAY, "bold"),
    )
    style.configure(
        STYLE_TITLE,
        background=design.NAVY,
        foreground=design.WHITE,
        font=(design.UI_FONT, design.SIZE_TITLE, "bold"),
    )
    style.configure(
        STYLE_SUBTITLE,
        background=design.NAVY,
        foreground=design.BLUE_TINT,
        font=(design.UI_FONT, design.SIZE_SUBTITLE),
    )
    style.configure(
        STYLE_BAND_TEXT,
        background=design.NAVY,
        foreground=design.TEXT_ON_DARK,
        font=(design.UI_FONT, design.SIZE_BODY),
    )
    style.configure(
        STYLE_BODY,
        background=design.WHITE,
        foreground=design.TEXT,
        font=(design.UI_FONT, design.SIZE_BODY),
    )
    style.configure(
        STYLE_MUTED,
        background=design.WHITE,
        foreground=design.TEXT_MUTED,
        font=(design.UI_FONT, design.SIZE_BODY),
    )
    style.configure(
        STYLE_SECTION,
        background=design.WHITE,
        foreground=design.NAVY,
        font=(design.UI_FONT, design.SIZE_SECTION, "bold"),
    )
    style.configure(
        STYLE_CAPTION,
        background=design.WHITE,
        foreground=design.TEXT_MUTED,
        font=(design.UI_FONT, design.SIZE_CAPTION),
    )
    # Numbers line up only in a monospaced face. A results table where the
    # digits do not align is measurably harder to scan for an outlier.
    style.configure(
        STYLE_MONO,
        background=design.WHITE,
        foreground=design.TEXT,
        font=(design.UI_FONT_MONO, design.SIZE_BODY),
    )


def _button_styles(style):
    """Buttons: bordered neutral, accent primary, and a quiet text button.

    Args:
        style: A `ttk.Style`.
    """
    padding = design.PAD_CONTROL
    style.configure(
        STYLE_BUTTON,
        background=design.WHITE,
        foreground=design.NAVY,
        bordercolor=design.BORDER_GREY,
        focuscolor=design.ACCENT,
        relief="flat",
        borderwidth=1,
        padding=padding,
        font=(design.UI_FONT, design.SIZE_BODY),
    )
    style.map(
        STYLE_BUTTON,
        background=[
            ("pressed", design.BLUE_TINT_DEEP),
            ("active", design.BLUE_TINT),
            ("disabled", design.LIGHT_GREY),
        ],
        foreground=[("disabled", design.NEUTRAL_GREY)],
        bordercolor=[("active", design.ACCENT)],
    )

    style.configure(
        STYLE_BUTTON_PRIMARY,
        background=design.ACCENT,
        foreground=design.WHITE,
        bordercolor=design.ACCENT,
        focuscolor=design.WHITE,
        relief="flat",
        borderwidth=0,
        padding=padding,
        font=(design.UI_FONT, design.SIZE_BODY, "bold"),
    )
    style.map(
        STYLE_BUTTON_PRIMARY,
        background=[
            ("pressed", design.ACCENT_DEEP),
            ("active", design.ACCENT_BRIGHT),
            ("disabled", design.NEUTRAL_GREY),
        ],
    )

    style.configure(
        STYLE_BUTTON_QUIET,
        background=design.WHITE,
        foreground=design.ACCENT,
        bordercolor=design.WHITE,
        relief="flat",
        borderwidth=0,
        padding=padding,
        font=(design.UI_FONT, design.SIZE_BODY),
    )
    style.map(
        STYLE_BUTTON_QUIET,
        background=[("active", design.BLUE_TINT)],
        foreground=[("disabled", design.NEUTRAL_GREY)],
    )


def _input_styles(style):
    """Checkbuttons, radios, combobox, entry.

    Args:
        style: A `ttk.Style`.
    """
    for name in (STYLE_CHECK, STYLE_RADIO):
        style.configure(
            name,
            background=design.WHITE,
            foreground=design.TEXT,
            focuscolor=design.ACCENT,
            indicatorcolor=design.WHITE,
            bordercolor=design.BORDER_GREY_DEEP,
            padding=(design.SPACE["xs"], design.SPACE["xs"]),
            font=(design.UI_FONT, design.SIZE_BODY),
        )
        style.map(
            name,
            background=[("active", design.WHITE)],
            indicatorcolor=[("selected", design.ACCENT), ("disabled", design.LIGHT_GREY)],
            foreground=[("disabled", design.NEUTRAL_GREY)],
        )

    style.configure(
        STYLE_ENTRY,
        fieldbackground=design.WHITE,
        foreground=design.TEXT,
        bordercolor=design.BORDER_GREY_DEEP,
        insertcolor=design.ACCENT,
        relief="flat",
        borderwidth=1,
        padding=design.SPACE["sm"],
    )
    style.map(STYLE_ENTRY, bordercolor=[("focus", design.ACCENT)])

    style.configure(
        STYLE_COMBO,
        fieldbackground=design.WHITE,
        background=design.WHITE,
        foreground=design.TEXT,
        bordercolor=design.BORDER_GREY_DEEP,
        arrowcolor=design.NAVY,
        relief="flat",
        padding=design.SPACE["sm"],
    )
    style.map(
        STYLE_COMBO,
        fieldbackground=[("readonly", design.WHITE)],
        bordercolor=[("focus", design.ACCENT)],
        arrowcolor=[("disabled", design.NEUTRAL_GREY)],
    )


def _table_style(style):
    """Table: blue-tint header, airy rows, hairlines, brand selection.

    Args:
        style: A `ttk.Style`.
    """
    style.configure(
        STYLE_TREE,
        background=design.WHITE,
        fieldbackground=design.WHITE,
        foreground=design.TEXT,
        bordercolor=design.BORDER_GREY,
        borderwidth=0,
        rowheight=design.ROW_HEIGHT,
        font=(design.UI_FONT, design.SIZE_TABLE),
    )
    style.configure(
        STYLE_TREE + ".Heading",
        background=design.BLUE_TINT,
        foreground=design.NAVY,
        relief="flat",
        borderwidth=0,
        padding=(design.SPACE["sm"], design.SPACE["sm"]),
        font=(design.UI_FONT, design.SIZE_TABLE, "bold"),
    )
    style.map(STYLE_TREE + ".Heading", background=[("active", design.BLUE_TINT_DEEP)])
    # Selection takes the brand accent rather than the system blue.
    style.map(
        STYLE_TREE,
        background=[("selected", design.ACCENT)],
        foreground=[("selected", design.WHITE)],
    )
    # Layout without the default sunken border: the card edge already frames
    # the table, and two frames around one object read as a mistake.
    try:
        style.layout(STYLE_TREE, style.layout("Treeview"))
    except Exception:  # noqa: BLE001 -- a missing layout is not fatal here
        pass


def _badge_styles(style):
    """One label style per status, for the verdict badge.

    Args:
        style: A `ttk.Style`.
    """
    for status in design.STATUSES:
        style.configure(
            STYLE_BADGE[status],
            background=design.ground(status),
            foreground=design.NAVY,
            padding=(design.SPACE["sm"], design.SPACE["xs"]),
            font=(design.UI_FONT, design.SIZE_CAPTION, "bold"),
        )


def _chrome_styles(style):
    """Notebook, progress bar, scrollbar.

    Args:
        style: A `ttk.Style`.
    """
    style.configure(
        STYLE_NOTEBOOK,
        background=design.LIGHT_GREY,
        bordercolor=design.BORDER_GREY,
        borderwidth=0,
        tabmargins=(0, 0, 0, 0),
    )
    style.configure(
        STYLE_NOTEBOOK + ".Tab",
        background=design.LIGHT_GREY,
        foreground=design.TEXT_MUTED,
        borderwidth=0,
        padding=(design.SPACE["lg"], design.SPACE["sm"]),
        font=(design.UI_FONT, design.SIZE_BODY),
    )
    style.map(
        STYLE_NOTEBOOK + ".Tab",
        background=[("selected", design.WHITE)],
        foreground=[("selected", design.NAVY)],
        font=[("selected", (design.UI_FONT, design.SIZE_BODY, "bold"))],
    )

    style.configure(
        STYLE_PROGRESS,
        background=design.ACCENT,
        troughcolor=design.BLUE_TINT,
        bordercolor=design.BLUE_TINT,
        lightcolor=design.ACCENT,
        darkcolor=design.ACCENT,
        thickness=design.SPACE["sm"],
        borderwidth=0,
    )

    style.configure(
        STYLE_SCROLLBAR,
        background=design.LIGHT_GREY,
        troughcolor=design.WHITE,
        bordercolor=design.WHITE,
        arrowcolor=design.TEXT_MUTED,
        relief="flat",
        borderwidth=0,
    )
    style.map(STYLE_SCROLLBAR, background=[("active", design.BORDER_GREY_DEEP)])


def configure_row_tags(tree):
    """Attach one row tag per status to a Treeview.

    Doing this in one place is what keeps a FAIL from rendering like a
    NOT EVALUATED because one view forgot a tag.

    Args:
        tree: A `ttk.Treeview`.

    Returns:
        dict: `{status: tag name}`, for use in `tree.insert(tags=...)`.
    """
    for status in design.STATUSES:
        tree.tag_configure(
            ROW_TAG[status], background=design.ground(status), foreground=design.TEXT
        )
    return dict(ROW_TAG)


def verdict_label(status, text):
    """Compose a verdict label: symbol FIRST, then the word.

    The symbol leads, always: it is what stays readable when the colour does
    not render.

    Args:
        status: One of `design.STATUSES`, or a legacy colour name.
        text: The verdict wording, already translated.

    Returns:
        str: The composed label.
    """
    return "%s  %s" % (design.symbol(status), text)


def row_colours(status):
    """Ground and text colour for one table row.

    Args:
        status: One of `design.STATUSES`, or a legacy colour name.

    Returns:
        tuple[str, str]: `(ground, text)`.
    """
    return design.ground(status), design.TEXT
