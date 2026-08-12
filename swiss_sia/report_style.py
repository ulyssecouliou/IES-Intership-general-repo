# -*- coding: utf-8 -*-
"""Bridge the IES house style to the two report engines.

``ui/design.py`` holds the palette, read from the public IES stylesheet, and
declares itself the single source for the navigator *and the reports*. The
reports did not use it: the client PDF carried its own teal-green constants and
the Excel generator carried 285 colour literals, none of them from the IES
palette. This module is the adapter that lets both adopt the tokens without
scattering conversions.

WHAT IT CONVERTS

fpdf wants floats in 0..1. openpyxl wants ``FFRRGGBB`` or ``RRGGBB`` without a
leading hash. Neither accepts the ``#rrggbb`` strings the token module holds, so
every consumer was writing its own conversion — which is how a palette drifts.

WHAT IT ENFORCES

A verdict is never carried by colour alone. :func:`status_presentation` returns
the colour, the ground, the symbol and the word together, so a caller cannot
take the colour and forget the rest. That rule comes from ``CLAUDE.md`` and from
``ui/design.py``; this module makes the compliant path the easy one.

Text colours come from ``STATUS_TEXT``, never from ``STATUS_STROKE``: the four
stroke hues measure between 2.15:1 and 4.30:1 on white, all below WCAG AA for
body text. :func:`contrast_ratio` is exposed so a test can re-measure rather
than trust this note.

No ``iesve`` import, no openpyxl or fpdf import at module level: the two
factory helpers take the class they need, so this module stays importable in
any environment and testable without either library.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from ui import design


__all__ = [
    "PDF",
    "XL",
    "StatusPresentation",
    "contrast_ratio",
    "meets_aa",
    "rgb_unit",
    "xl_hex",
    "status_presentation",
    "excel_fill",
    "excel_font",
    "excel_side",
    "excel_thin_border",
    "xw_hex",
    "xw_format",
    "xw_title",
    "xw_subtitle",
    "xw_band",
    "xw_section",
    "xw_label",
    "xw_value",
    "xw_kpi_label",
    "xw_kpi_value",
    "xw_table_header",
    "xw_disclaimer",
    "xw_link",
    "xw_table_link",
    "xw_status",
    "XW_TAB_COLOR",
    "XW_SECTION_TAB_COLORS",
    "XW_CHART_FILL",
    "XW_CHART_FILL_NORMATIVE",
    "XW_SEVERITY_FILLS",
    "REPORT_DISCLAIMER_KEY",
]


# ---------------------------------------------------------------------------
# Conversions
# ---------------------------------------------------------------------------


def _channels(token: str) -> Tuple[int, int, int]:
    """Return the 0..255 channels of a ``#rrggbb`` token."""

    text = token.lstrip("#")
    if len(text) != 6:
        raise ValueError("Expected a #rrggbb colour token, got {!r}".format(token))
    return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))


def rgb_unit(token: str) -> Tuple[float, float, float]:
    """Return an fpdf-ready 0..1 triple for one design token."""

    return tuple(channel / 255.0 for channel in _channels(token))


def xl_hex(token: str, *, alpha: bool = True) -> str:
    """Return an openpyxl-ready hex string, uppercase and without the hash.

    openpyxl accepts both ``RRGGBB`` and ``FFRRGGBB``; the alpha-prefixed form
    is the one it writes back, so passing it keeps a workbook diff quiet.
    """

    red, green, blue = _channels(token)
    body = "{:02X}{:02X}{:02X}".format(red, green, blue)
    return ("FF" + body) if alpha else body


# ---------------------------------------------------------------------------
# Contrast, measured rather than asserted
# ---------------------------------------------------------------------------

#: WCAG 2.1 minimum contrast for body text.
AA_BODY = 4.5

#: WCAG 2.1 minimum for large text and for non-text such as a rule or an icon.
AA_LARGE = 3.0


def _relative_luminance(token: str) -> float:
    """Return the WCAG relative luminance of one token."""

    def channel(value: int) -> float:
        srgb = value / 255.0
        if srgb <= 0.04045:
            return srgb / 12.92
        return ((srgb + 0.055) / 1.055) ** 2.4

    red, green, blue = (channel(c) for c in _channels(token))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground: str, background: str) -> float:
    """Return the WCAG contrast ratio between two tokens."""

    first = _relative_luminance(foreground)
    second = _relative_luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def meets_aa(foreground: str, background: str, *, large: bool = False) -> bool:
    """Whether a pairing clears WCAG AA for its text size."""

    threshold = AA_LARGE if large else AA_BODY
    return contrast_ratio(foreground, background) >= threshold


# ---------------------------------------------------------------------------
# Named roles, so callers ask for a role and not for a colour
# ---------------------------------------------------------------------------


class _Palette:
    """Base class holding the role-to-token mapping shared by both engines."""

    #: Role name -> design token. Roles are named for what they do in a
    #: document, so a caller never has to know which hue is current.
    ROLES: Dict[str, str] = {
        "ink": design.TEXT,
        "muted": design.TEXT_MUTED,
        "on_dark": design.TEXT_ON_DARK,
        "rule": design.BORDER_GREY,
        "rule_strong": design.BORDER_GREY_DEEP,
        "band": design.NAVY,
        "band_deep": design.NAVY_DEEP,
        "band_tint": design.NAVY_TINT,
        "accent": design.ACCENT,
        "accent_bright": design.ACCENT_BRIGHT,
        "panel": design.LIGHT_GREY,
        "table_header": design.BLUE_TINT,
        "table_selected": design.BLUE_TINT_DEEP,
        "white": design.WHITE,
    }

    def token(self, role: str) -> str:
        """Return the design token behind one role."""

        try:
            return self.ROLES[role]
        except KeyError:
            raise KeyError(
                "Unknown report style role {!r}. Known roles: {}".format(
                    role, ", ".join(sorted(self.ROLES))
                )
            ) from None

    def __getattr__(self, name: str) -> Any:
        if name in self.ROLES:
            return self._convert(self.ROLES[name])
        raise AttributeError(name)

    def _convert(self, token: str) -> Any:  # pragma: no cover - overridden
        raise NotImplementedError


class _PdfPalette(_Palette):
    """Roles as fpdf 0..1 triples."""

    def _convert(self, token: str) -> Tuple[float, float, float]:
        return rgb_unit(token)


class _ExcelPalette(_Palette):
    """Roles as openpyxl hex strings."""

    def _convert(self, token: str) -> str:
        return xl_hex(token)


#: Role palette for the PDF engine.
PDF = _PdfPalette()

#: Role palette for the Excel engine.
XL = _ExcelPalette()


# ---------------------------------------------------------------------------
# Status presentation: colour, ground, symbol and word travel together
# ---------------------------------------------------------------------------


class StatusPresentation:
    """Everything needed to render one status, so none of it can be dropped.

    ``text`` and ``ground`` are design tokens. ``symbol`` and ``word`` satisfy
    the rule that a verdict is never carried by colour alone: a colour-blind
    reader, a greyscale print and the VEScripts console each get the meaning.
    """

    __slots__ = ("status", "text", "ground", "stroke", "symbol", "symbol_ascii")

    def __init__(
        self,
        status: str,
        text: str,
        ground: str,
        stroke: str,
        symbol: str,
        symbol_ascii: str,
    ) -> None:
        self.status = status
        self.text = text
        self.ground = ground
        self.stroke = stroke
        self.symbol = symbol
        self.symbol_ascii = symbol_ascii

    @property
    def pdf_text(self) -> Tuple[float, float, float]:
        return rgb_unit(self.text)

    @property
    def pdf_ground(self) -> Tuple[float, float, float]:
        return rgb_unit(self.ground)

    @property
    def pdf_stroke(self) -> Tuple[float, float, float]:
        return rgb_unit(self.stroke)

    @property
    def xl_text(self) -> str:
        return xl_hex(self.text)

    @property
    def xl_ground(self) -> str:
        return xl_hex(self.ground)

    def contrast_on_ground(self) -> float:
        """Measured contrast of the verdict word on its own ground."""

        return contrast_ratio(self.text, self.ground)

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return "StatusPresentation({!r}, {:.2f}:1)".format(
            self.status, self.contrast_on_ground()
        )


def status_presentation(status: str) -> StatusPresentation:
    """Return the full presentation of one engine status.

    Accepts the six statuses of ``ui/design.py`` and, for callers not yet
    converted, the legacy colour words it still maps.
    """

    key = design.LEGACY_COLOUR_TO_STATUS.get(status, status)
    if key not in design.STATUSES:
        raise KeyError(
            "Unknown status {!r}. Known: {}".format(
                status, ", ".join(design.STATUSES)
            )
        )
    return StatusPresentation(
        status=key,
        text=design.STATUS_TEXT[key],
        ground=design.STATUS_GROUND[key],
        stroke=design.STATUS_STROKE[key],
        symbol=design.STATUS_SYMBOL[key],
        symbol_ascii=design.STATUS_SYMBOL_ASCII[key],
    )


# ---------------------------------------------------------------------------
# openpyxl factories
# ---------------------------------------------------------------------------
#
# The openpyxl classes are passed in rather than imported, so this module has
# no hard dependency and a test can exercise it with a stub.


def excel_fill(pattern_fill_cls: Any, role_or_token: str) -> Any:
    """Return a solid ``PatternFill`` for one role name or design token."""

    token = _resolve(role_or_token)
    return pattern_fill_cls(
        start_color=xl_hex(token), end_color=xl_hex(token), fill_type="solid"
    )


def excel_font(
    font_cls: Any,
    role_or_token: str = "ink",
    *,
    size: Optional[float] = None,
    bold: bool = False,
    italic: bool = False,
    name: Optional[str] = None,
) -> Any:
    """Return a ``Font`` in the house style.

    The default size and family come from the report scale in
    ``ui/design.py`` so a workbook cannot drift from the PDF.
    """

    return font_cls(
        name=name or design.UI_FONT,
        size=size if size is not None else design.SIZE_TABLE,
        bold=bold,
        italic=italic,
        color=xl_hex(_resolve(role_or_token)),
    )


def excel_side(side_cls: Any, role_or_token: str = "rule", style: str = "thin") -> Any:
    """Return one ``Side`` in a house rule colour."""

    return side_cls(style=style, color=xl_hex(_resolve(role_or_token)))


def excel_thin_border(border_cls: Any, side_cls: Any, role_or_token: str = "rule") -> Any:
    """Return a hairline ``Border`` on all four edges."""

    side = excel_side(side_cls, role_or_token)
    return border_cls(left=side, right=side, top=side, bottom=side)


def _resolve(role_or_token: str) -> str:
    """Accept either a role name or a raw ``#rrggbb`` design token."""

    if role_or_token.startswith("#"):
        return role_or_token
    if role_or_token in _Palette.ROLES:
        return _Palette.ROLES[role_or_token]
    raise KeyError(
        "Unknown role or token {!r}. Pass a role name or a #rrggbb token.".format(
            role_or_token
        )
    )


# ---------------------------------------------------------------------------
# xlsxwriter formats
# ---------------------------------------------------------------------------
#
# The workbook is written with xlsxwriter, not openpyxl, and the two differ in
# ways that matter here: xlsxwriter wants ``#RRGGBB`` *with* the hash, and a
# format is a plain property dict handed to ``workbook.add_format``. So these
# helpers return dicts and this module still imports neither library.
#
# The named builders below exist so a sheet asks for "a KPI value" rather than
# assembling eight properties, which is how a workbook ends up with 285 colour
# literals and no two cards alike.


def xw_hex(token: str) -> str:
    """Return an xlsxwriter-ready ``#rrggbb`` string for one token."""

    red, green, blue = _channels(token)
    return "#{:02X}{:02X}{:02X}".format(red, green, blue)


def xw_format(
    role_or_token: str = "ink",
    *,
    size: Optional[float] = None,
    bold: bool = False,
    italic: bool = False,
    background: Optional[str] = None,
    border: Optional[str] = "rule",
    align: Optional[str] = None,
    valign: Optional[str] = None,
    num_format: Optional[str] = None,
    text_wrap: bool = False,
    underline: bool = False,
) -> Dict[str, Any]:
    """Return one xlsxwriter format dict in the house style.

    ``border`` names the rule colour and is dropped entirely when ``None``, so
    a caller gets a hairline by default and has to ask for a borderless cell.
    """

    spec: Dict[str, Any] = {
        "font_name": design.EXCEL_FONT,
        "font_size": size if size is not None else design.SIZE_TABLE,
        "font_color": xw_hex(_resolve(role_or_token)),
    }
    if bold:
        spec["bold"] = True
    if italic:
        spec["italic"] = True
    if underline:
        spec["underline"] = True
    if background is not None:
        spec["bg_color"] = xw_hex(_resolve(background))
    if border is not None:
        spec["border"] = 1
        spec["border_color"] = xw_hex(_resolve(border))
    if align:
        spec["align"] = align
    if valign:
        spec["valign"] = valign
    if num_format:
        spec["num_format"] = num_format
    if text_wrap:
        spec["text_wrap"] = True
    return spec


def xw_title() -> Dict[str, Any]:
    """Cover title: navy, large, no box around it."""

    return xw_format(
        "band",
        size=design.SIZE_DISPLAY,
        bold=True,
        border=None,
        valign="vcenter",
    )


def xw_subtitle() -> Dict[str, Any]:
    """One line under the title, muted and unboxed."""

    return xw_format("muted", size=design.SIZE_SUBTITLE, border=None)


def xw_band() -> Dict[str, Any]:
    """Full-width navy band with light type on it, as on the site."""

    return xw_format(
        "on_dark",
        size=design.SIZE_SECTION,
        bold=True,
        background="band",
        border=None,
        valign="vcenter",
    )


def xw_section() -> Dict[str, Any]:
    """Section heading inside a sheet."""

    return xw_format("band", size=design.SIZE_SECTION, bold=True, border=None)


def xw_label() -> Dict[str, Any]:
    """Field label in an identification block."""

    return xw_format("muted", size=design.SIZE_BODY, bold=True, border=None)


def xw_value() -> Dict[str, Any]:
    """Field value beside a label."""

    return xw_format("ink", size=design.SIZE_BODY, border=None)


def xw_kpi_label() -> Dict[str, Any]:
    """Caption of a headline figure, on the pale blue table ground."""

    return xw_format(
        "band",
        size=design.SIZE_BODY,
        bold=True,
        background="table_header",
        align="center",
    )


def xw_kpi_value(num_format: str = "0.0") -> Dict[str, Any]:
    """A headline figure. Accent blue, because a number is not a verdict."""

    return xw_format(
        "accent",
        size=design.SIZE_TITLE,
        bold=True,
        background="white",
        align="center",
        num_format=num_format,
    )


def xw_table_header() -> Dict[str, Any]:
    """Table header row: navy type on the pale blue ground."""

    return xw_format(
        "band",
        size=design.SIZE_TABLE,
        bold=True,
        background="table_header",
        align="left",
        text_wrap=True,
    )


def xw_disclaimer() -> Dict[str, Any]:
    """The non-certification sentence. Muted, wrapped, never truncated."""

    return xw_format(
        "muted", size=design.SIZE_CAPTION, italic=True, border=None, text_wrap=True
    )


def xw_link() -> Dict[str, Any]:
    """An internal link on the index sheet."""

    return xw_format("accent", size=design.SIZE_BODY, border=None)


def xw_table_link() -> Dict[str, Any]:
    """An internal link inside a bordered table cell.

    Underlined, unlike :func:`xw_link`: on the index the link sits alone on a
    line and its colour is enough, but in a table row a link marked by colour
    alone is indistinguishable for a reader who cannot separate the two hues,
    and it would also lose the hairline its neighbours have.
    """

    return xw_format(
        "accent",
        underline=True,
        align="center",
    )


def xw_status(status: str, *, size: Optional[float] = None) -> Dict[str, Any]:
    """Return the format for a verdict cell.

    Colour comes from ``STATUS_TEXT``, so the word clears WCAG AA on its own
    ground. The caller still owes the symbol and the word: see
    :func:`status_presentation`.
    """

    presented = status_presentation(status)
    return xw_format(
        presented.text,
        size=size if size is not None else design.SIZE_TABLE,
        bold=True,
        background=presented.ground,
        align="center",
    )


#: Tab colour for the two landing sheets. Navy, matching the band.
XW_TAB_COLOR = xw_hex(design.NAVY)

def xw_shared_roles() -> Dict[str, Dict[str, Any]]:
    """Return the seven formats the workbook shares across its many sheets.

    These used to live in ``swiss_sia/config.py`` as ``EXCEL_FORMATS``, which
    put presentation inside the normative configuration module and gave the
    workbook a blue that belongs to no IES palette. Forty-eight call sites read
    them, so this is the single highest-leverage conversion in the generator.

    ``critical`` is the inverse of ``fail`` rather than a second red: light type
    on the solid fail colour, where ``fail`` is dark type on a tint of it. Both
    mean non-compliant, so inventing another hue would claim a distinction the
    palette does not make, and inverting reads as an escalation even in
    greyscale -- which two reds side by side do not.
    """

    failed = status_presentation("fail")
    return {
        "header": xw_format(
            "on_dark",
            size=14,
            bold=True,
            background="band",
            valign="top",
            text_wrap=True,
        ),
        "subheader": xw_format(
            "on_dark",
            size=12,
            bold=True,
            background="band_tint",
        ),
        "pass": xw_status("pass"),
        "warning": xw_status("warning"),
        "fail": xw_status("fail"),
        "critical": xw_format(
            "on_dark",
            bold=True,
            background=failed.text,
            align="center",
        ),
        "score": xw_format("band_deep", size=16, bold=True, border=None),
    }


#: Chart series fill for a plain quantity bar or column, in house accent blue.
XW_CHART_FILL = xw_hex(design.ACCENT)

#: Chart series fill for a normative-coverage series, in the brand navy.
XW_CHART_FILL_NORMATIVE = xw_hex(design.NAVY)

#: Doughnut slice fill per alert severity, darkest first.
#
# The four levels need four distinguishable fills, and the ramp has to read as
# a severity ordering rather than four unrelated hues. Critical and High take
# the darkened and plain fail red, Medium the warning amber, and Low the house
# light blue: informational, deliberately not a warning colour. These are chart
# areas, not text, so the WCAG text-contrast rule that governs STATUS_TEXT does
# not apply -- the ordering and the labels carry the meaning.
XW_SEVERITY_FILLS = {
    "Critical": xw_hex(design.RED_TEXT),
    "High": xw_hex(design.RED),
    "Medium": xw_hex(design.AMBER),
    "Low": xw_hex(design.LIGHT_BLUE),
}

#: Tab colour per report section, keyed by the section name the index prints.
#
# Thirty-odd tabs need to be told apart at a glance, which is why the workbook
# had seven colours to begin with. The ones it had -- teal ``#0F766E``, violet
# ``#6D28D9``, two oranges -- belong to no IES palette; a client opening the
# file saw a second visual identity. These stay seven distinguishable colours,
# but every one is a house token, and the choice carries the section's meaning
# rather than decorating it: the brand navy family for the normative work, the
# semantic amber where the section is about what to fix first, and the muted
# slates for supporting data.
XW_SECTION_TAB_COLORS = {
    # The brand anchor, for what a manager opens first.
    "Executive": xw_hex(design.NAVY_DEEP),
    # Priority is attention, so it takes the semantic amber, darkened for
    # legibility exactly as AMBER_TEXT is.
    "Readiness & priority": xw_hex(design.AMBER_TEXT),
    # Fabric and glazing: the house light blue, distinct from both navies.
    "Envelope & glazing": xw_hex(design.LIGHT_BLUE),
    # The primary normative section takes the primary brand colour.
    "SIA 380/2": xw_hex(design.NAVY),
    # The second normative section, separated by the accent blue darkened.
    "SIA 4010": xw_hex(design.ACCENT_DEEP),
    # Working sheets, in body-text slate.
    "Actions & inputs": xw_hex(design.TEXT),
    # Supporting detail, deliberately the quietest tab.
    "Data & detail": xw_hex(design.TEXT_MUTED),
}


# ---------------------------------------------------------------------------
# Wording
# ---------------------------------------------------------------------------

#: i18n key of the sentence every client-facing report must carry. The report
#: states readiness and evidence; it is not a certificate. Kept here so both
#: engines cite the same key rather than each phrasing its own disclaimer.
REPORT_DISCLAIMER_KEY = "report_non_certification"
