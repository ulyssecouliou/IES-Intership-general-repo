# -*- coding: utf-8 -*-
"""One reusable IES theme for every Tkinter window in the toolchain.

WHY THIS EXISTS. `ui/design.py` is a complete design system -- an IES-derived
palette, six measured status states, a type scale, a 4 px spacing scale. But
nothing applied it to Tk: each window rebuilt its own ttk styles by hand, and
three of them drifted into private palettes (a hub blue, a model-builder green)
that no longer matched the house style or each other. Consistency you have to
re-type in every window is consistency that decays.

This module is the single place that turns the tokens into a live ttk theme.
A window calls ``apply_ies_theme(root)`` once and every standard widget -- frame,
label, button, table, tab, entry, scrollbar -- inherits the house style. The
named ttk styles below are the vocabulary a window composes with; it should not
set a colour of its own, exactly as the report generators no longer do.

WHAT IT DELIBERATELY DOES NOT DO. It invents no colour and no font. Every value
resolves to a `ui/design.py` token. The screen face is Segoe UI because that is
what `design.py` records for the Windows host VE runs on; the real IES face,
Camphor Pro, is commercial and not ours to embed. A verdict is never carried by
colour alone -- ``status_badge`` always pairs the ground with a symbol and a
word, the same rule the reports follow.
"""

import tkinter.font as tkfont
from tkinter import ttk

from . import design


#: ttk base theme we extend. ``clam`` is the one cross-platform theme that
#: actually honours ``background``/``fieldbackground``, which the house style
#: needs -- ``vista``/``winnative`` ignore them and would drop us back to grey.
_BASE_THEME = "clam"

#: Named Font objects, created once per root and shared. Keyed by role so a
#: window asks for ``fonts["title"]`` rather than restating a family and size.
_FONT_ROLES = (
    ("display", design.SIZE_DISPLAY, "bold"),
    ("title", design.SIZE_TITLE, "bold"),
    ("subtitle", design.SIZE_SUBTITLE, "normal"),
    ("section", design.SIZE_SECTION, "bold"),
    ("body", design.SIZE_BODY, "normal"),
    ("body_bold", design.SIZE_BODY, "bold"),
    ("table", design.SIZE_TABLE, "normal"),
    ("caption", design.SIZE_CAPTION, "normal"),
)


def build_fonts(root):
    """Create the role-named screen fonts for one window.

    Args:
        root: The Tk root or toplevel the fonts belong to.

    Returns:
        dict[str, tkfont.Font]: One font per role in ``_FONT_ROLES`` plus a
        monospaced ``"mono"`` for evidence identifiers and checksums.
    """

    fonts = {}
    for role, size, weight in _FONT_ROLES:
        fonts[role] = tkfont.Font(
            root=root, family=design.UI_FONT, size=size, weight=weight
        )
    fonts["mono"] = tkfont.Font(
        root=root, family=design.UI_FONT_MONO, size=design.SIZE_BODY
    )
    return fonts


def apply_ies_theme(root):
    """Apply the IES house style to one Tk root, returning its fonts.

    Every colour and font below resolves to a ``ui/design.py`` token; this
    function adds none of its own. Call it once, immediately after creating the
    root, before building widgets.

    Args:
        root: The Tk root window.

    Returns:
        dict[str, tkfont.Font]: The role-named fonts, so the caller can set the
        same faces on the non-ttk widgets (``tk.Text``, ``tk.Canvas`` labels)
        that ttk styles do not reach.
    """

    fonts = build_fonts(root)
    root.configure(background=design.LIGHT_GREY)

    style = ttk.Style(root)
    if _BASE_THEME in style.theme_names():
        style.theme_use(_BASE_THEME)

    # --- Grounds -----------------------------------------------------------
    style.configure("TFrame", background=design.LIGHT_GREY)
    style.configure("Card.TFrame", background=design.WHITE)
    style.configure(
        "Band.TFrame", background=design.NAVY
    )  # full-width heading band
    style.configure(
        "Toolbar.TFrame", background=design.WHITE
    )
    style.configure(
        "TSeparator", background=design.BORDER_GREY
    )

    # --- Labels ------------------------------------------------------------
    style.configure(
        "TLabel",
        background=design.LIGHT_GREY,
        foreground=design.TEXT,
        font=fonts["body"],
    )
    style.configure("Card.TLabel", background=design.WHITE)
    style.configure(
        "Caption.TLabel",
        background=design.LIGHT_GREY,
        foreground=design.TEXT_MUTED,
        font=fonts["caption"],
    )
    style.configure(
        "CardCaption.TLabel",
        background=design.WHITE,
        foreground=design.TEXT_MUTED,
        font=fonts["caption"],
    )
    style.configure(
        "Section.TLabel",
        background=design.WHITE,
        foreground=design.NAVY,
        font=fonts["section"],
    )
    style.configure(
        "Title.TLabel",
        background=design.LIGHT_GREY,
        foreground=design.NAVY,
        font=fonts["title"],
    )
    # Labels that sit on the navy band.
    style.configure(
        "BandTitle.TLabel",
        background=design.NAVY,
        foreground=design.WHITE,
        font=fonts["title"],
    )
    style.configure(
        "BandSubtitle.TLabel",
        background=design.NAVY,
        foreground=design.TEXT_ON_DARK,
        font=fonts["subtitle"],
    )

    # --- Buttons -----------------------------------------------------------
    # Base: quiet, for secondary actions that are not the primary path.
    style.configure(
        "TButton",
        background=design.WHITE,
        foreground=design.TEXT,
        bordercolor=design.BORDER_GREY_DEEP,
        focuscolor=design.ACCENT,
        font=fonts["body"],
        padding=design.PAD_CONTROL,
        relief="flat",
    )
    style.map(
        "TButton",
        background=[
            ("pressed", design.BLUE_TINT_DEEP),
            ("active", design.BLUE_TINT),
            ("disabled", design.LIGHT_GREY),
        ],
        foreground=[("disabled", design.TEXT_MUTED)],
        bordercolor=[("focus", design.ACCENT)],
    )
    # Primary: the one action the house style paints -- accent blue, reserved.
    style.configure(
        "Primary.TButton",
        background=design.ACCENT,
        foreground=design.WHITE,
        bordercolor=design.ACCENT_DEEP,
        focuscolor=design.WHITE,
        font=fonts["body_bold"],
        padding=design.PAD_CONTROL,
        relief="flat",
    )
    style.map(
        "Primary.TButton",
        background=[
            ("pressed", design.ACCENT_DEEP),
            ("active", design.ACCENT_BRIGHT),
            ("disabled", design.BORDER_GREY_DEEP),
        ],
        foreground=[("disabled", design.WHITE)],
    )
    # Secondary: outlined, accent text on white.
    style.configure(
        "Secondary.TButton",
        background=design.WHITE,
        foreground=design.ACCENT,
        bordercolor=design.ACCENT,
        focuscolor=design.ACCENT,
        font=fonts["body_bold"],
        padding=design.PAD_CONTROL,
        relief="flat",
    )
    style.map(
        "Secondary.TButton",
        background=[
            ("pressed", design.BLUE_TINT_DEEP),
            ("active", design.BLUE_TINT),
            ("disabled", design.LIGHT_GREY),
        ],
        foreground=[("disabled", design.TEXT_MUTED)],
    )

    # --- Table -------------------------------------------------------------
    style.configure(
        "Treeview",
        background=design.WHITE,
        fieldbackground=design.WHITE,
        foreground=design.TEXT,
        rowheight=design.ROW_HEIGHT,
        font=fonts["table"],
        bordercolor=design.BORDER_GREY,
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", design.BLUE_TINT_DEEP)],
        foreground=[("selected", design.NAVY)],
    )
    style.configure(
        "Treeview.Heading",
        background=design.BLUE_TINT,
        foreground=design.NAVY,
        font=fonts["body_bold"],
        relief="flat",
        padding=design.PAD_CONTROL,
    )
    style.map(
        "Treeview.Heading",
        background=[("active", design.BLUE_TINT_DEEP)],
    )

    # --- Notebook ----------------------------------------------------------
    style.configure(
        "TNotebook", background=design.LIGHT_GREY, borderwidth=0
    )
    style.configure(
        "TNotebook.Tab",
        background=design.LIGHT_GREY,
        foreground=design.TEXT_MUTED,
        font=fonts["body"],
        padding=(design.SPACE["lg"], design.SPACE["sm"]),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", design.WHITE)],
        foreground=[("selected", design.NAVY)],
    )

    # --- Inputs ------------------------------------------------------------
    for entry_style in ("TEntry", "TCombobox", "TSpinbox"):
        style.configure(
            entry_style,
            fieldbackground=design.WHITE,
            background=design.WHITE,
            foreground=design.TEXT,
            bordercolor=design.BORDER_GREY_DEEP,
            insertcolor=design.TEXT,
            padding=design.SPACE["sm"],
        )
        style.map(
            entry_style,
            bordercolor=[("focus", design.ACCENT)],
            fieldbackground=[("disabled", design.LIGHT_GREY)],
        )

    style.configure(
        "TCheckbutton",
        background=design.WHITE,
        foreground=design.TEXT,
        font=fonts["body"],
        focuscolor=design.ACCENT,
    )
    style.configure(
        "TLabelframe",
        background=design.WHITE,
        bordercolor=design.BORDER_GREY,
    )
    style.configure(
        "TLabelframe.Label",
        background=design.WHITE,
        foreground=design.NAVY,
        font=fonts["section"],
    )

    # --- Scrollbars: subtle, the house divides by space not by chrome ------
    for scrollbar in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        style.configure(
            scrollbar,
            background=design.BORDER_GREY,
            troughcolor=design.LIGHT_GREY,
            bordercolor=design.LIGHT_GREY,
            arrowcolor=design.TEXT_MUTED,
            relief="flat",
        )
        style.map(
            scrollbar,
            background=[("active", design.BORDER_GREY_DEEP)],
        )

    style.configure(
        "TProgressbar",
        background=design.ACCENT,
        troughcolor=design.BLUE_TINT,
        bordercolor=design.BLUE_TINT,
    )

    return fonts


def status_badge(status):
    """Return the three things a status chip needs, colour never alone.

    Args:
        status: One of ``design.STATUSES`` or a legacy colour name.

    Returns:
        dict: ``{"ground", "text", "symbol", "word"}`` -- the ground colour,
        the WCAG-safe text colour, the redundant symbol and the status word.
        The pairing is the accessibility contract: a reader who cannot see the
        colour still reads the symbol and the word.
    """

    resolved = design._resolve(status) or design.NOT_EVALUATED
    return {
        "ground": design.ground(resolved),
        "text": design.STATUS_TEXT.get(resolved, design.NEUTRAL_TEXT),
        "symbol": design.symbol(resolved),
        "word": resolved.replace("_", " "),
    }


def centre_on_screen(window, width, height):
    """Place a window centred on its screen, clamped to stay fully visible.

    A dialog that opens partly off a small laptop screen hides its own action
    buttons. This keeps the whole window on the visible desktop.

    Args:
        window: The Tk root or toplevel.
        width: Desired width in pixels.
        height: Desired height in pixels.

    Returns:
        str: The geometry string applied, e.g. ``"1240x760+120+80"``.
    """

    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    width = min(width, screen_w)
    height = min(height, screen_h)
    x = max(0, (screen_w - width) // 2)
    y = max(0, (screen_h - height) // 3)  # a third down reads better than half
    geometry = "{}x{}+{}+{}".format(width, height, x, y)
    window.geometry(geometry)
    return geometry
