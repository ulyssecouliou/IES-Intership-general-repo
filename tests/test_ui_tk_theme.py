# -*- coding: utf-8 -*-
"""Guards for the shared IES Tkinter theme.

The house design system existed but nothing applied it to Tk, so windows drifted
into private palettes. `ui/tk_theme.py` is the single place that turns the tokens
into a live ttk theme. These tests pin two things: it invents no colour of its
own (every value is a design token), and the styles it configures resolve to the
exact IES tokens -- so a window that adopts the theme cannot drift.

Note on Tk in tests: creating and destroying several Tk roots inside one pytest
process makes Tcl font operations flaky on some builds, so the live-theme tests
share ONE cached root and skip cleanly when no display is available. The
strongest guarantee -- that the module holds no colour literal -- needs no Tk.
"""

import re
import unittest
from pathlib import Path

from ui import design, tk_theme

try:
    import tkinter as tk
    from tkinter import ttk

    _TK_IMPORTABLE = True
except Exception:  # pragma: no cover - headless CI without tkinter
    _TK_IMPORTABLE = False


ROOT = Path(__file__).resolve().parents[1]
_HEX = re.compile(r"#[0-9a-fA-F]{6}\b")

#: One cached root for the whole module, created on first use and never
#: destroyed during the run -- see the module note.
_ROOT = None


def _shared_root():
    """Return the one cached withdrawn Tk root, or skip if Tk cannot start."""

    global _ROOT
    if not _TK_IMPORTABLE:
        raise unittest.SkipTest("tkinter is not importable")
    if _ROOT is None:
        try:
            _ROOT = tk.Tk()
            _ROOT.withdraw()
        except Exception as exc:  # pragma: no cover - headless
            raise unittest.SkipTest("Tk has no display: {}".format(exc))
    return _ROOT


def tearDownModule():
    """Destroy the cached root so it cannot leak Tcl state into other modules.

    The root is shared within this module (creating and destroying one per test
    makes Tcl font ops flaky), but leaving it alive contaminated another Tk test
    file's default-root resolution. Destroying it here, and clearing tkinter's
    default-root pointer, keeps the next module's Tk session clean.
    """

    global _ROOT
    if _ROOT is not None:
        try:
            _ROOT.destroy()
        finally:
            _ROOT = None
            if _TK_IMPORTABLE:
                tk._default_root = None


class TkThemeNoLiteralTests(unittest.TestCase):
    def test_theme_module_holds_no_colour_literal(self):
        """Every colour must come from a ui/design.py token, never a hex here.

        This is the same ratchet the Excel generator carries: the moment a raw
        colour appears in the theme, the single-source guarantee is broken.
        """

        source = (ROOT / "ui" / "tk_theme.py").read_text(encoding="utf-8")
        literals = _HEX.findall(source)
        self.assertEqual(
            literals,
            [],
            "tk_theme.py must hold no colour literal; found {}".format(literals),
        )


class TkThemeApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = _shared_root()
        cls.fonts = tk_theme.apply_ies_theme(cls.root)
        cls.style = ttk.Style(cls.root)

    def test_theme_uses_clam_and_the_house_ground(self):
        self.assertEqual(self.style.theme_use(), "clam")
        self.assertEqual(self.root.cget("background"), design.LIGHT_GREY)

    def test_named_styles_resolve_to_ies_tokens(self):
        cases = (
            ("Primary.TButton", "background", design.ACCENT),
            ("Band.TFrame", "background", design.NAVY),
            ("Treeview.Heading", "background", design.BLUE_TINT),
            ("Card.TFrame", "background", design.WHITE),
            ("Section.TLabel", "foreground", design.NAVY),
        )
        for style_name, option, expected in cases:
            with self.subTest(style=style_name, option=option):
                self.assertEqual(
                    self.style.lookup(style_name, option), expected
                )

    def test_table_row_height_is_the_house_token(self):
        self.assertEqual(
            self.style.lookup("Treeview", "rowheight"),
            design.ROW_HEIGHT,
        )

    def test_fonts_cover_every_role(self):
        for role in (
            "display",
            "title",
            "subtitle",
            "section",
            "body",
            "body_bold",
            "table",
            "caption",
            "mono",
        ):
            self.assertIn(role, self.fonts)


class TkThemeStatusBadgeTests(unittest.TestCase):
    """Pure logic, no Tk: the accessibility contract of a status chip."""

    def test_badge_pairs_colour_with_symbol_and_word(self):
        badge = tk_theme.status_badge(design.FAIL)
        self.assertEqual(badge["ground"], design.STATUS_GROUND[design.FAIL])
        self.assertEqual(badge["text"], design.STATUS_TEXT[design.FAIL])
        self.assertEqual(badge["symbol"], design.STATUS_SYMBOL[design.FAIL])
        self.assertEqual(badge["word"], "fail")

    def test_unknown_status_never_reads_as_pass(self):
        """An unexpected value must fall to neutral, never to a success hue."""

        badge = tk_theme.status_badge("something_unmapped")
        self.assertNotEqual(badge["ground"], design.STATUS_GROUND[design.PASS])
        self.assertEqual(badge["text"], design.NEUTRAL_TEXT)


class SetupDialogStyleTests(unittest.TestCase):
    """The reference-model setup dialog no longer carries an ad-hoc style."""

    def test_setup_dialog_source_is_on_the_shared_theme(self):
        source = (
            ROOT / "swiss_sia" / "reference_model_setup_ui.py"
        ).read_text(encoding="utf-8")
        # It adopts the shared theme...
        self.assertIn("tk_theme.apply_ies_theme", source)
        # ...and carries no hardcoded face or colour of its own.
        self.assertNotIn("Segoe UI", source)
        self.assertEqual(_HEX.findall(source), [])


if __name__ == "__main__":
    unittest.main()
