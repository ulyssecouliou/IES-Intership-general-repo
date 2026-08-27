"""Tests for the report style bridge.

The contrast figures quoted in ``report_style`` and in ``ui/design.py`` are
re-measured here rather than trusted. A palette note goes stale silently; a
failing test does not.
"""

from __future__ import annotations

import unittest

from swiss_sia import report_style
from swiss_sia.report_style import (
    AA_BODY,
    PDF,
    XL,
    contrast_ratio,
    excel_fill,
    excel_font,
    excel_side,
    excel_thin_border,
    meets_aa,
    rgb_unit,
    status_presentation,
    xl_hex,
)
from ui import design


class ConversionTests(unittest.TestCase):

    def test_rgb_unit_maps_a_token_to_fpdf_range(self) -> None:
        self.assertEqual(rgb_unit("#000000"), (0.0, 0.0, 0.0))
        self.assertEqual(rgb_unit("#ffffff"), (1.0, 1.0, 1.0))
        red, green, blue = rgb_unit(design.NAVY)
        self.assertAlmostEqual(red, 0x1A / 255.0)
        self.assertAlmostEqual(green, 0x2B / 255.0)
        self.assertAlmostEqual(blue, 0x4B / 255.0)

    def test_xl_hex_is_uppercase_alpha_prefixed_and_hashless(self) -> None:
        self.assertEqual(xl_hex(design.NAVY), "FF1A2B4B")
        self.assertEqual(xl_hex(design.NAVY, alpha=False), "1A2B4B")

    def test_a_malformed_token_is_refused(self) -> None:
        for bad in ("#12345", "navy", "#1a2b4b4b"):
            with self.assertRaises(ValueError):
                rgb_unit(bad)


class PaletteRoleTests(unittest.TestCase):

    def test_both_engines_expose_the_same_roles(self) -> None:
        for role in report_style._Palette.ROLES:
            self.assertIsInstance(getattr(XL, role), str)
            triple = getattr(PDF, role)
            self.assertEqual(len(triple), 3)
            self.assertTrue(all(0.0 <= channel <= 1.0 for channel in triple))

    def test_every_role_resolves_to_a_design_token(self) -> None:
        tokens = {
            value
            for name, value in vars(design).items()
            if isinstance(value, str) and value.startswith("#") and len(value) == 7
        }
        for role, token in report_style._Palette.ROLES.items():
            self.assertIn(token, tokens, msg="role {} is off-palette".format(role))

    def test_an_unknown_role_is_refused(self) -> None:
        with self.assertRaises(KeyError):
            XL.token("chartreuse")
        with self.assertRaises(AttributeError):
            _ = XL.chartreuse


class StatusPresentationTests(unittest.TestCase):

    def test_every_status_carries_colour_symbol_and_ascii_symbol(self) -> None:
        """A verdict is never information by colour alone."""

        for status in design.STATUSES:
            presented = status_presentation(status)
            self.assertTrue(presented.text.startswith("#"))
            self.assertTrue(presented.ground.startswith("#"))
            self.assertTrue(presented.symbol.strip())
            self.assertTrue(presented.symbol_ascii.strip())

    def test_every_verdict_word_clears_aa_on_its_own_ground(self) -> None:
        for status in design.STATUSES:
            presented = status_presentation(status)
            ratio = presented.contrast_on_ground()
            self.assertGreaterEqual(
                ratio,
                AA_BODY,
                msg="{}: {:.2f}:1 on {}".format(status, ratio, presented.ground),
            )

    def test_every_verdict_word_clears_aa_on_white(self) -> None:
        """A verdict also appears on plain white, outside a status card."""

        for status in design.STATUSES:
            presented = status_presentation(status)
            self.assertTrue(
                meets_aa(presented.text, design.WHITE),
                msg="{}: {:.2f}:1 on white".format(
                    status, contrast_ratio(presented.text, design.WHITE)
                ),
            )

    def test_stroke_hues_would_not_have_cleared_aa(self) -> None:
        """Why STATUS_TEXT exists at all.

        If a future edit points verdict text at STATUS_STROKE, this test
        documents what that costs. It also guards the derivation: should the
        stroke hues ever become AA-safe, the separate text tokens can go.
        """

        offenders = [
            status
            for status in (design.PASS, design.FAIL, design.WARNING)
            if not meets_aa(design.STATUS_STROKE[status], design.WHITE)
        ]
        self.assertEqual(
            offenders,
            [design.PASS, design.FAIL, design.WARNING],
            msg="stroke hues changed; revisit STATUS_TEXT",
        )

    def test_derived_text_shades_are_shades_of_their_base(self) -> None:
        """A derived token is a shade, never a new hue.

        Scaling RGB uniformly preserves the ratios between channels, so each
        derived value must keep the channel ordering of its base.
        """

        pairs = (
            (design.GREEN, design.GREEN_TEXT),
            (design.RED, design.RED_TEXT),
            (design.AMBER, design.AMBER_TEXT),
            (design.NEUTRAL_GREY, design.NEUTRAL_TEXT),
        )
        for base, derived in pairs:
            base_channels = report_style._channels(base)
            derived_channels = report_style._channels(derived)
            self.assertEqual(
                [sorted(base_channels).index(c) for c in base_channels],
                [sorted(derived_channels).index(c) for c in derived_channels],
                msg="{} -> {} changed hue order".format(base, derived),
            )
            for channel_base, channel_derived in zip(base_channels, derived_channels):
                self.assertLessEqual(channel_derived, channel_base)

    def test_legacy_colour_words_still_resolve(self) -> None:
        self.assertEqual(status_presentation("vert").status, design.PASS)
        self.assertEqual(status_presentation("rouge").status, design.FAIL)
        self.assertEqual(status_presentation("gris").status, design.NOT_EVALUATED)

    def test_an_unknown_status_is_refused(self) -> None:
        with self.assertRaises(KeyError):
            status_presentation("probably_fine")


class ExcelFactoryTests(unittest.TestCase):
    """The factories take their classes, so no openpyxl import is needed."""

    def test_fill_font_side_and_border_use_house_colours(self) -> None:
        class _Fill:
            def __init__(self, start_color, end_color, fill_type):
                self.start_color = start_color
                self.end_color = end_color
                self.fill_type = fill_type

        class _Font:
            def __init__(self, name, size, bold, italic, color):
                self.name = name
                self.size = size
                self.bold = bold
                self.italic = italic
                self.color = color

        class _Side:
            def __init__(self, style, color):
                self.style = style
                self.color = color

        class _Border:
            def __init__(self, left, right, top, bottom):
                self.left, self.right = left, right
                self.top, self.bottom = top, bottom

        fill = excel_fill(_Fill, "band")
        self.assertEqual(fill.start_color, "FF1A2B4B")
        self.assertEqual(fill.fill_type, "solid")

        font = excel_font(_Font, "on_dark", size=11, bold=True)
        self.assertEqual(font.color, xl_hex(design.TEXT_ON_DARK))
        self.assertTrue(font.bold)
        self.assertEqual(font.size, 11)
        self.assertEqual(font.name, design.UI_FONT)

        default_font = excel_font(_Font)
        self.assertEqual(default_font.color, xl_hex(design.TEXT))
        self.assertEqual(default_font.size, design.SIZE_TABLE)

        side = excel_side(_Side)
        self.assertEqual(side.color, xl_hex(design.BORDER_GREY))

        border = excel_thin_border(_Border, _Side)
        for edge in (border.left, border.right, border.top, border.bottom):
            self.assertEqual(edge.color, xl_hex(design.BORDER_GREY))

    def test_a_raw_token_is_accepted_as_well_as_a_role(self) -> None:
        class _Fill:
            def __init__(self, start_color, end_color, fill_type):
                self.start_color = start_color

        self.assertEqual(excel_fill(_Fill, "#1a2b4b").start_color, "FF1A2B4B")

    def test_an_unknown_role_is_refused_by_the_factories(self) -> None:
        class _Fill:
            def __init__(self, start_color, end_color, fill_type):
                pass

        with self.assertRaises(KeyError):
            excel_fill(_Fill, "chartreuse")


class ClientPdfAdoptionTests(unittest.TestCase):
    """The client report must resolve to the house style, not its own."""

    def test_the_client_pdf_palette_comes_from_the_tokens(self) -> None:
        from swiss_sia import compliance_report_pdf as report

        self.assertEqual(report.BRAND, rgb_unit(design.NAVY))
        self.assertEqual(report.INK, rgb_unit(design.TEXT))
        self.assertEqual(report.MUTED, rgb_unit(design.TEXT_MUTED))
        self.assertEqual(report.LINE, rgb_unit(design.BORDER_GREY))
        self.assertEqual(report.PANEL, rgb_unit(design.LIGHT_GREY))
        self.assertEqual(report.ACCENT, rgb_unit(design.ACCENT))

    def test_the_client_pdf_verdict_colours_are_text_safe(self) -> None:
        from swiss_sia import compliance_report_pdf as report

        self.assertEqual(report.OK, rgb_unit(design.GREEN_TEXT))
        self.assertEqual(report.BAD, rgb_unit(design.RED_TEXT))
        self.assertEqual(report.WARN, rgb_unit(design.AMBER_TEXT))

    def test_the_client_pdf_no_longer_carries_a_second_palette(self) -> None:
        """The teal-green identity is gone, not merely unused."""

        from swiss_sia import compliance_report_pdf as report

        # (0.071, 0.443, 0.353) was the old BRAND.
        self.assertNotAlmostEqual(report.BRAND[1], 0.443, places=3)


if __name__ == "__main__":
    unittest.main()
