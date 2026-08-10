# -*- coding: utf-8 -*-
"""Composable chrome for the SIA 4010 navigator: band, cards, strip, footer.

WHY THESE ARE COMPONENTS AND NOT INLINE CODE. The dialog used to build its
header, its toolbar and its panels inline, which had two costs. Padding was
chosen per call site, so the layout drifted from the house style one widget at
a time. And `swiss_sia`'s evidence wizard built its own, slightly different
version of the same header -- two windows from one product that do not look
alike.

WHAT THE HOUSE STYLE ASKS. iesve.com divides by space, not by rules: a
full-width navy band, a very light grey ground, white cards floating on it,
hairlines, and accent blue reserved for the one action that matters. Solid
areas of bright colour are rare and small. Every gap here comes from
`design.SPACE`; nothing takes a number.

THE ONE RULE THAT IS NOT DECORATION. A verdict is never carried by colour
alone -- `status_strip` renders symbol, word and ground together, and the
symbol comes first, because it is what survives a ttk theme that ignores
backgrounds. That is a `CLAUDE.md` requirement, not a preference.

ttk has no drop shadow and no border radius. A card reads as a card because of
a one-pixel edge, done here by nesting a frame in a frame -- faking a shadow
with stippled greys looks worse than not trying.
"""

from __future__ import print_function

from ui import design
from ui import i18n
from ui import theme

#: Width in pixels of the accent bar down the left of a status card. Thin
#: enough to read as an edge rather than a block of colour.
ACCENT_BAR = 3

#: Where a card's one-pixel edge comes from. ttk draws no border we can
#: colour reliably across themes, so the edge is a frame behind the card.
EDGE = 1


def _ttk():
    """Import ttk, with a message that says what is actually wrong.

    Returns:
        module: `tkinter.ttk`.

    Raises:
        ImportError: Outside VEScripts, where there is no display.
    """
    try:
        from tkinter import ttk
    except ImportError as error:
        raise ImportError(
            'tkinter unavailable: ui/layout.py builds real widgets and only '
            'means anything inside VEScripts (%s)' % error)
    return ttk


def card(parent, padding=None):
    """A white card on the grey ground, with a hairline edge.

    Args:
        parent: Parent widget.
        padding: Inner padding; `design.PAD_CARD` by default.

    Returns:
        tuple: `(outer, inner)`. Pack or grid the OUTER frame; put content in
        the INNER one. Two frames because the edge is a frame behind the card
        -- see the module note.
    """
    ttk = _ttk()
    outer = ttk.Frame(parent, style=theme.STYLE_CARD_EDGE, padding=EDGE)
    inner = ttk.Frame(outer, style=theme.STYLE_CARD,
                      padding=design.PAD_CARD if padding is None else padding)
    inner.pack(fill='both', expand=True)
    return outer, inner


def rule(parent, orientation='horizontal'):
    """A hairline separator.

    Args:
        parent: Parent widget.
        orientation: `'horizontal'` or `'vertical'`.

    Returns:
        ttk.Frame: The rule, not yet packed.
    """
    ttk = _ttk()
    thickness = {'height': EDGE} if orientation == 'horizontal' \
        else {'width': EDGE}
    frame = ttk.Frame(parent, style=theme.STYLE_RULE)
    frame.configure(**thickness)
    return frame


def header_band(parent, title_key='app.title', subtitle_key='app.subtitle'):
    """The full-width navy band: the product's visual signature.

    Args:
        parent: Parent widget, usually the window.
        title_key: i18n key for the title.
        subtitle_key: i18n key for the line under it.

    Returns:
        dict: `{'band', 'titles', 'actions'}`. `actions` is a right-aligned
        frame for buttons; `titles` is where a caller may add more lines.
    """
    ttk = _ttk()
    band = ttk.Frame(parent, style=theme.STYLE_BAND, padding=design.PAD_BAND)
    band.pack(side='top', fill='x')

    # ACTIONS D'ABORD. Tk sert les enfants dans l'ordre d'empaquetage : les
    # titres empaquetés en premier réclamaient toute la largeur et le second
    # bouton d'export sortait de la fenêtre. Un bouton hors champ n'est pas
    # une imperfection : l'action est inatteignable et rien ne le signale.
    actions = ttk.Frame(band, style=theme.STYLE_BAND)
    actions.pack(side='right', anchor='ne')

    titles = ttk.Frame(band, style=theme.STYLE_BAND)
    titles.pack(side='left', anchor='w', fill='x', expand=True)

    # An eyebrow above the title: it says which product this window belongs
    # to, which matters because VEScripts dialogs open with no chrome of
    # their own.
    ttk.Label(titles, style=theme.STYLE_SUBTITLE,
              text=i18n.t('app.product').upper()).pack(anchor='w')
    ttk.Label(titles, style=theme.STYLE_TITLE,
              text=i18n.t(title_key)).pack(anchor='w',
                                           pady=(design.SPACE['xs'], 0))
    ttk.Label(titles, style=theme.STYLE_BAND_TEXT, wraplength=720,
              text=i18n.t(subtitle_key)).pack(anchor='w',
                                              pady=(design.SPACE['xs'], 0))

    return {'band': band, 'titles': titles, 'actions': actions}


def action_button(parent, label_key, command, primary=False, quiet=False):
    """One button in an action cluster.

    Only ONE button in a window should be primary. Two accent-blue buttons
    side by side stop meaning "this is the action" and start meaning nothing.

    Args:
        parent: Parent widget.
        label_key: i18n key for the label.
        command: Callback.
        primary: True for the single accent action.
        quiet: True for a borderless text button.

    Returns:
        ttk.Button: Packed to the left of its parent.

    Raises:
        ValueError: If both `primary` and `quiet` are asked for -- they are
            opposite intentions, and silently picking one would give the
            window two visual hierarchies.
    """
    ttk = _ttk()
    if primary and quiet:
        raise ValueError('a button is primary or quiet, not both')
    style = theme.STYLE_BUTTON
    if primary:
        style = theme.STYLE_BUTTON_PRIMARY
    elif quiet:
        style = theme.STYLE_BUTTON_QUIET
    button = ttk.Button(parent, style=style, text=i18n.t(label_key),
                        command=command)
    button.pack(side='left', padx=(design.SPACE['sm'], 0))
    return button


def status_badge(parent, status, text):
    """A verdict badge: symbol, then word, on the status ground.

    Args:
        parent: Parent widget.
        status: One of `design.STATUSES`, or a legacy colour name.
        text: The verdict wording, already translated.

    Returns:
        ttk.Label: The badge, not yet packed.
    """
    ttk = _ttk()
    # An unrecognised status must not borrow another status's style: it would
    # render as whatever that status means. Fall back to the neutral one.
    style = theme.STYLE_BADGE.get(status)
    if style is None:
        resolved = design.LEGACY_COLOUR_TO_STATUS.get(status)
        style = theme.STYLE_BADGE.get(resolved,
                                      theme.STYLE_BADGE[design.NOT_EVALUATED])
    return ttk.Label(parent, style=style,
                     text=theme.verdict_label(status, text))


def status_strip(parent, entries):
    """A row of badges, one per test.

    One verdict per test, never an aggregate. An aggregate would hide WHICH
    test fails, which is the only thing a reader needs from this row.

    Args:
        parent: Parent widget.
        entries: Sequence of `{'label': str, 'status': str, 'text': str}`.

    Returns:
        ttk.Frame: The strip, packed into `parent`.
    """
    ttk = _ttk()
    strip = ttk.Frame(parent, style=theme.STYLE_BAND)
    strip.pack(side='top', fill='x', pady=(design.SPACE['md'], 0))
    for entry in entries:
        holder = ttk.Frame(strip, style=theme.STYLE_BAND)
        holder.pack(side='left', padx=(0, design.SPACE['sm']))
        ttk.Label(holder, style=theme.STYLE_SUBTITLE,
                  text=entry['label']).pack(anchor='w')
        status_badge(holder, entry['status'], entry['text']).pack(
            anchor='w', pady=(design.SPACE['xs'], 0))
    return strip


def toolbar(parent):
    """A white toolbar card: controls left, state right.

    Args:
        parent: Parent widget.

    Returns:
        dict: `{'outer', 'inner', 'left', 'right'}`.
    """
    ttk = _ttk()
    outer, inner = card(parent, padding=design.PAD_CONTROL)
    outer.pack(side='top', fill='x', pady=(0, design.SPACE['sm']))

    row = ttk.Frame(inner, style=theme.STYLE_CARD)
    row.pack(side='top', fill='x')

    # DROITE D'ABORD, pour la même raison que dans `header_band` : Tk sert les
    # enfants dans l'ordre d'empaquetage, et un côté gauche en `expand=True`
    # raflait toute la largeur. Les boutons d'export sortaient de la fenêtre
    # — inatteignables, sans aucun signal.
    right = ttk.Frame(row, style=theme.STYLE_CARD)
    right.pack(side='right')
    left = ttk.Frame(row, style=theme.STYLE_CARD)
    left.pack(side='left', fill='x', expand=True)

    # Ligne d'état, pleine largeur, SOUS les contrôles. Placée à leur suite
    # sur la même ligne, elle était tronquée dès que les boutons prenaient
    # leur place — et un état tronqué (« 2/7 test(s) prés… ») cache la liste
    # des tests manquants, qui est justement ce qu'il faut lire.
    caption = ttk.Frame(inner, style=theme.STYLE_CARD)
    caption.pack(side='top', fill='x', pady=(design.SPACE['sm'], 0))

    return {'outer': outer, 'inner': inner, 'row': row, 'left': left,
            'right': right, 'caption': caption}


def section_heading(parent, text_key, note_key=None):
    """A section title, optionally with a muted note beneath it.

    Args:
        parent: Parent widget.
        text_key: i18n key for the heading.
        note_key: i18n key for the note, or `None`.

    Returns:
        ttk.Label: The heading label, packed.
    """
    ttk = _ttk()
    heading = ttk.Label(parent, style=theme.STYLE_SECTION,
                        text=i18n.t(text_key))
    heading.pack(anchor='w')
    if note_key is not None:
        ttk.Label(parent, style=theme.STYLE_CAPTION, wraplength=680,
                  text=i18n.t(note_key)).pack(anchor='w',
                                              pady=(design.SPACE['xs'], 0))
    return heading


def empty_state(parent, message_key):
    """What a panel shows when it has nothing to show.

    A blank panel reads as a broken one. Worse, in this tool it reads as "no
    problems found", which is the opposite of the truth when the real reason
    is that no simulation has run.

    Args:
        parent: Parent widget.
        message_key: i18n key for a message that says what to DO.

    Returns:
        ttk.Label: The message, packed.
    """
    ttk = _ttk()
    label = ttk.Label(parent, style=theme.STYLE_MUTED, wraplength=560,
                      justify='left', text=i18n.t(message_key))
    label.pack(anchor='w', padx=design.SPACE['lg'], pady=design.SPACE['xl'])
    return label


def footer(parent, notes=('note.pass_is_not_compliance',)):
    """A quiet footer carrying the standing reminders.

    These live in the window, not only in the report, because the confusion
    they guard against -- technical PASS read as SIA 380/2 compliance, or as
    SIA 4010 validation -- happens while someone is looking at the screen.

    Args:
        parent: Parent widget.
        notes: i18n keys to display, in order.

    Returns:
        ttk.Frame: The footer, packed at the bottom.
    """
    ttk = _ttk()
    outer, inner = card(parent, padding=design.PAD_CONTROL)
    outer.pack(side='bottom', fill='x', pady=(design.SPACE['sm'], 0))
    for key in notes:
        ttk.Label(inner, style=theme.STYLE_CAPTION, wraplength=900,
                  justify='left',
                  text=u'%s  %s' % (design.STATUS_SYMBOL[design.WARNING],
                                    i18n.t(key))).pack(anchor='w')
    return outer


def language_switch(parent, on_change):
    """A combobox that switches the interface language.

    Args:
        parent: Parent widget.
        on_change: Called with the new language code after the switch. The
            caller rebuilds -- ttk cannot retranslate widgets in place.

    Returns:
        ttk.Combobox: The control, packed.
    """
    ttk = _ttk()
    import tkinter as tk

    labels = {i18n.FRENCH: i18n.t('language.fr'),
              i18n.ENGLISH: i18n.t('language.en')}
    reverse = dict((text, code) for code, text in labels.items())

    ttk.Label(parent, style=theme.STYLE_MUTED,
              text=i18n.t('language.label')).pack(
                  side='left', padx=(0, design.SPACE['sm']))
    chosen = tk.StringVar(value=labels[i18n.language()])
    box = ttk.Combobox(parent, textvariable=chosen, state='readonly',
                       style=theme.STYLE_COMBO, width=12,
                       values=[labels[code] for code in i18n.LANGUAGES])
    box.pack(side='left')

    def _switch(_event=None):
        code = reverse.get(chosen.get())
        if code is None:
            return
        i18n.set_language(code)
        on_change(code)

    box.bind('<<ComboboxSelected>>', _switch)
    return box


def results_table(parent, columns, tree_heading_key='column.quantity'):
    """A results table in a card, with a scrollbar and status row tags.

    Args:
        parent: Parent widget.
        columns: Sequence of `(column id, i18n key, width, anchor)`.
        tree_heading_key: i18n key for the tree column's own heading.

    Returns:
        dict: `{'outer', 'inner', 'tree', 'tags'}`. `tags` maps each status to
        its row tag, so callers cannot invent their own and get a FAIL that
        looks like a NOT EVALUATED.
    """
    ttk = _ttk()
    outer, inner = card(parent, padding=design.PAD_CARD)

    ids = tuple(column[0] for column in columns)
    tree = ttk.Treeview(inner, columns=ids, show='tree headings',
                        style=theme.STYLE_TREE)
    tree.heading('#0', text=i18n.t(tree_heading_key))
    tree.column('#0', width=340, stretch=True)
    for identifier, key, width, anchor in columns:
        tree.heading(identifier, text=i18n.t(key))
        tree.column(identifier, width=width, anchor=anchor,
                    stretch=(anchor == 'w'))
    tree.pack(side='left', fill='both', expand=True)

    bar = ttk.Scrollbar(inner, orient='vertical', style=theme.STYLE_SCROLLBAR,
                        command=tree.yview)
    bar.pack(side='left', fill='y')
    tree.configure(yscrollcommand=bar.set)

    return {'outer': outer, 'inner': inner, 'tree': tree,
            'tags': theme.configure_row_tags(tree)}
