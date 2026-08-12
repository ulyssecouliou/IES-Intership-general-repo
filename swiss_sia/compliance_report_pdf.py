"""Render the company-letterhead SIA compliance report as a PDF.

The document states, on the office's own letterhead, what the analysis of one
VE model found against SIA 380/2 and what validation state the toolchain holds
under SIA 4010. It is an engineering assessment report, not an official SIA
certificate and not an SIA 4010 validation attestation: the scope block says so
explicitly, and the verdict engine in :mod:`swiss_sia.compliance_verdict` keeps
every undetermined item visible instead of reading as compliant.

The model thumbnail is a schematic drawn from the extracted data (external
opaque and glazed area per orientation). The analysed model does not expose
surface polygons, so no attempt is made to draw a geometric view that could
misrepresent the building.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from .company_profile import CompanyProfile, load_company_profile
from .compliance_verdict import (
    COMPLIANT,
    NOT_COMPLIANT,
    NOT_DETERMINED,
    ComplianceVerdict,
    build_compliance_verdict,
)
from .pdf_writer import (
    A4_MM,
    PdfDocument,
    PdfPage,
    truncate_to_width,
    wrap_to_width,
)
from .reference_model.sia4010.ui_translations import normalize_language, translate

# Palette. Every value below is the IES house style, resolved through
# ``report_style`` from the tokens in ``ui/design.py``, which reads them from the
# public IES stylesheet.
#
# WHAT CHANGED, AND WHY. These constants used to hold a teal-green identity of
# their own: BRAND was (0.071, 0.443, 0.353). The token module declares itself
# the single source for the navigator *and the reports*, so a client-facing
# report in a second palette was a drift, not a choice. The names are kept so
# the 625 lines below are untouched; only what they resolve to has moved.
#
# The status colours come from STATUS_TEXT, not STATUS_STROKE. The four stroke
# hues measure 2.15:1 to 4.30:1 on white and would have put verdict words below
# WCAG AA; the derived text shades clear it on white and on their own ground.
# ``tests/test_report_style.py`` re-measures rather than trusting this note.
from .report_style import PDF as _PDF, status_presentation as _status

INK = _PDF.ink
MUTED = _PDF.muted
LINE = _PDF.rule
BRAND = _PDF.band
BRAND_DEEP = _PDF.band_deep
ACCENT = _PDF.accent
PANEL = _PDF.panel
WHITE = _PDF.white
OK = _status("pass").pdf_text
OK_BG = _status("pass").pdf_ground
BAD = _status("fail").pdf_text
BAD_BG = _status("fail").pdf_ground
WARN = _status("warning").pdf_text
WARN_BG = _status("warning").pdf_ground

MARGIN = 16.0
CONTENT_WIDTH = A4_MM[0] - 2 * MARGIN

_STATUS_COLOURS = {
    COMPLIANT: (OK, OK_BG),
    NOT_COMPLIANT: (BAD, BAD_BG),
    NOT_DETERMINED: (WARN, WARN_BG),
}

_ORIENTATION_ORDER = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def _status_label(status: str, language: str) -> str:
    """Return the translated label of one verdict status."""

    return translate(
        {
            COMPLIANT: "verdict_compliant",
            NOT_COMPLIANT: "verdict_not_compliant",
            NOT_DETERMINED: "verdict_not_determined",
        }.get(status, "verdict_not_determined"),
        language,
    )


def _float_or_none(value: Any) -> Optional[float]:
    """Return a float when the value is numeric, otherwise None."""

    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compass_sector(orientation: Any) -> Optional[str]:
    """Return the eight-point compass sector for a VE orientation in degrees.

    A textual orientation already expressed as a sector is accepted as-is; an
    unusable value returns None so it is reported as unspecified rather than
    charted in the wrong direction.
    """

    text = str(orientation or "").strip().upper()
    if text in _ORIENTATION_ORDER:
        return text
    degrees = _float_or_none(orientation)
    if degrees is None:
        return None
    index = int((degrees % 360.0) / 45.0 + 0.5) % 8
    return _ORIENTATION_ORDER[index]


def summarise_model(rooms_data: Optional[Sequence[Any]]) -> Dict[str, Any]:
    """Return the schematic figures the thumbnail and key-figure block need."""

    rooms = list(rooms_data or [])
    opaque: Dict[str, float] = {sector: 0.0 for sector in _ORIENTATION_ORDER}
    glazed: Dict[str, float] = {sector: 0.0 for sector in _ORIENTATION_ORDER}
    floor_area = 0.0
    volume = 0.0
    unplaced_opaque = 0.0
    unplaced_glazed = 0.0
    for room in rooms:
        floor_area += _float_or_none(getattr(room, "area", None)) or 0.0
        volume += _float_or_none(getattr(room, "volume", None)) or 0.0
        for surface in getattr(room, "surfaces", None) or ():
            if not getattr(surface, "is_external", False):
                continue
            area = _float_or_none(
                getattr(surface, "net_area", None)
            ) or _float_or_none(getattr(surface, "area", None)) or 0.0
            sector = _compass_sector(getattr(surface, "orientation", None))
            if sector is None:
                unplaced_opaque += area
            else:
                opaque[sector] += area
        for opening in getattr(room, "openings", None) or ():
            if not getattr(opening, "is_external", False):
                continue
            area = _float_or_none(getattr(opening, "area", None)) or 0.0
            sector = _compass_sector(getattr(opening, "orientation", None))
            if sector is None:
                unplaced_glazed += area
            else:
                glazed[sector] += area
    total_opaque = sum(opaque.values()) + unplaced_opaque
    total_glazed = sum(glazed.values()) + unplaced_glazed
    return {
        "rooms": len(rooms),
        "floor_area_m2": floor_area,
        "volume_m3": volume,
        "opaque_by_sector": opaque,
        "glazed_by_sector": glazed,
        "total_opaque_m2": total_opaque,
        "total_glazed_m2": total_glazed,
        "unplaced_opaque_m2": unplaced_opaque,
        "unplaced_glazed_m2": unplaced_glazed,
        "window_wall_ratio": (total_glazed / total_opaque) if total_opaque else None,
    }


def _draw_letterhead(
    page: PdfPage, profile: CompanyProfile, language: str
) -> float:
    """Draw the company letterhead and return the y position below it."""

    page.rect(0, 0, A4_MM[0], 30.0, fill=BRAND_DEEP)
    page.rect(0, 30.0, A4_MM[0], 1.4, fill=ACCENT)
    text_left = MARGIN
    if profile.logo_path is not None:
        try:
            page.image(MARGIN, 6.5, 17.0, 17.0, profile.logo_path)
            text_left = MARGIN + 21.0
        except Exception:
            # A logo that cannot be embedded must never block the report.
            text_left = MARGIN
    name = profile.name or translate("company_unspecified", language)
    page.text(
        text_left,
        13.5,
        truncate_to_width(name, 15.0, 120.0, bold=True),
        size_pt=15.0,
        bold=True,
        colour=WHITE,
    )
    if profile.tagline:
        page.text(
            text_left,
            19.5,
            truncate_to_width(profile.tagline, 8.5, 120.0),
            size_pt=8.5,
            colour=(0.741, 0.882, 0.831),
        )
    right_lines = list(profile.address_lines) + list(profile.contact_lines)
    for index, line in enumerate(right_lines[:4]):
        page.text(
            A4_MM[0] - MARGIN - 62.0,
            9.0 + index * 4.2,
            truncate_to_width(line, 7.5, 62.0),
            size_pt=7.5,
            colour=(0.741, 0.882, 0.831),
            align="right",
            width_mm=62.0,
        )
    return 40.0


def _draw_verdict_banner(
    page: PdfPage, top: float, verdict: ComplianceVerdict, language: str
) -> float:
    """Draw the headline verdict block and return the y position below it."""

    status = verdict.overall_status
    colour, background = _STATUS_COLOURS[status]
    height = 24.0
    page.rect(MARGIN, top, CONTENT_WIDTH, height, fill=background)
    page.rect(MARGIN, top, 2.2, height, fill=colour)
    page.text(
        MARGIN + 7.0,
        top + 9.0,
        translate("verdict_heading", language).upper(),
        size_pt=7.5,
        bold=True,
        colour=MUTED,
    )
    page.text(
        MARGIN + 7.0,
        top + 18.0,
        _status_label(status, language),
        size_pt=16.0,
        bold=True,
        colour=colour,
    )
    counts = "{} / {}".format(verdict.blocking_total, verdict.advisory_total)
    page.text(
        A4_MM[0] - MARGIN - 62.0,
        top + 10.0,
        translate("findings_blocking_advisory", language),
        size_pt=7.5,
        colour=MUTED,
        align="right",
        width_mm=62.0,
    )
    page.text(
        A4_MM[0] - MARGIN - 62.0,
        top + 18.0,
        counts,
        size_pt=13.0,
        bold=True,
        colour=INK,
        align="right",
        width_mm=62.0,
    )
    return top + height + 7.0


def _draw_identification(
    page: PdfPage,
    top: float,
    rows: Sequence[Tuple[str, str]],
    language: str,
) -> float:
    """Draw the project identification table and return the y below it."""

    page.text(
        MARGIN,
        top,
        translate("section_identification", language).upper(),
        size_pt=7.5,
        bold=True,
        colour=BRAND,
    )
    top += 3.0
    page.line(MARGIN, top, A4_MM[0] - MARGIN, top, width_pt=0.5, colour=LINE)
    top += 5.0
    for label, value in rows:
        page.text(MARGIN, top, label, size_pt=8.0, colour=MUTED)
        page.text(
            MARGIN + 46.0,
            top,
            truncate_to_width(value, 8.0, CONTENT_WIDTH - 48.0),
            size_pt=8.0,
            colour=INK,
        )
        top += 5.0
    return top + 2.0


def _draw_domain_table(
    page: PdfPage, top: float, verdict: ComplianceVerdict, language: str
) -> float:
    """Draw the per-domain verdict table and return the y below it."""

    page.text(
        MARGIN,
        top,
        translate("section_domains", language).upper(),
        size_pt=7.5,
        bold=True,
        colour=BRAND,
    )
    top += 3.0
    page.line(MARGIN, top, A4_MM[0] - MARGIN, top, width_pt=0.5, colour=LINE)
    top += 5.5
    columns = (0.0, 62.0, 112.0, 142.0)
    headers = (
        translate("column_domain", language),
        translate("column_status", language),
        translate("column_blocking", language),
        translate("column_advisory", language),
    )
    for offset, header in zip(columns, headers):
        page.text(MARGIN + offset, top, header, size_pt=7.0, bold=True, colour=MUTED)
    top += 4.5
    for domain in verdict.domains:
        colour, background = _STATUS_COLOURS[domain.status]
        page.rect(MARGIN, top - 3.4, CONTENT_WIDTH, 5.6, fill=PANEL)
        page.text(
            MARGIN + 2.0,
            top,
            translate("domain_" + domain.domain, language),
            size_pt=8.0,
            colour=INK,
        )
        page.rect(MARGIN + columns[1], top - 3.0, 3.0, 3.0, fill=colour)
        page.text(
            MARGIN + columns[1] + 4.5,
            top,
            _status_label(domain.status, language),
            size_pt=7.5,
            bold=True,
            colour=colour,
        )
        page.text(
            MARGIN + columns[2],
            top,
            str(domain.blocking_count),
            size_pt=8.0,
            colour=INK,
        )
        page.text(
            MARGIN + columns[3],
            top,
            str(domain.advisory_count),
            size_pt=8.0,
            colour=MUTED,
        )
        top += 6.4
    return top + 2.0


def _draw_model_thumbnail(
    page: PdfPage,
    x: float,
    top: float,
    width: float,
    summary: Dict[str, Any],
    language: str,
) -> float:
    """Draw the schematic facade rose of the analysed model."""

    height = 46.0
    page.rect(x, top, width, height, fill=PANEL, stroke=LINE, width_pt=0.4)
    page.text(
        x + 4.0,
        top + 6.0,
        translate("section_model", language).upper(),
        size_pt=7.0,
        bold=True,
        colour=BRAND,
    )
    opaque = summary["opaque_by_sector"]
    glazed = summary["glazed_by_sector"]
    peak = max(list(opaque.values()) + list(glazed.values()) + [0.0])
    base = top + height - 8.0
    chart_height = 25.0
    slot = (width - 12.0) / len(_ORIENTATION_ORDER)
    for index, sector in enumerate(_ORIENTATION_ORDER):
        left = x + 6.0 + index * slot
        if peak > 0:
            opaque_height = chart_height * (opaque[sector] / peak)
            glazed_height = chart_height * (glazed[sector] / peak)
        else:
            opaque_height = glazed_height = 0.0
        bar = slot * 0.34
        if opaque_height > 0.15:
            page.rect(left, base - opaque_height, bar, opaque_height, fill=BRAND)
        if glazed_height > 0.15:
            page.rect(left + bar + 0.7, base - glazed_height, bar, glazed_height, fill=ACCENT)
        page.text(
            left,
            base + 3.4,
            sector,
            size_pt=6.0,
            colour=MUTED,
            align="center",
            width_mm=bar * 2 + 0.7,
        )
    page.line(x + 5.0, base, x + width - 5.0, base, width_pt=0.4, colour=LINE)
    page.rect(x + 4.0, top + 8.6, 2.4, 2.4, fill=BRAND)
    page.text(x + 8.0, top + 11.0, translate("legend_opaque", language), size_pt=6.0, colour=MUTED)
    page.rect(x + 34.0, top + 8.6, 2.4, 2.4, fill=ACCENT)
    page.text(x + 38.0, top + 11.0, translate("legend_glazed", language), size_pt=6.0, colour=MUTED)
    return top + height + 3.0


def _draw_key_figures(
    page: PdfPage,
    x: float,
    top: float,
    width: float,
    summary: Dict[str, Any],
    scores: Dict[str, Any],
    language: str,
) -> float:
    """Draw the key-figure list beside the thumbnail."""

    page.text(
        x,
        top + 6.0,
        translate("section_key_figures", language).upper(),
        size_pt=7.0,
        bold=True,
        colour=BRAND,
    )
    ratio = summary["window_wall_ratio"]
    rows = [
        (translate("figure_rooms", language), "{:,.0f}".format(summary["rooms"])),
        (
            translate("figure_floor_area", language),
            "{:,.1f} m2".format(summary["floor_area_m2"]),
        ),
        (
            translate("figure_volume", language),
            "{:,.1f} m3".format(summary["volume_m3"]),
        ),
        (
            translate("figure_opaque", language),
            "{:,.1f} m2".format(summary["total_opaque_m2"]),
        ),
        (
            translate("figure_glazed", language),
            "{:,.1f} m2".format(summary["total_glazed_m2"]),
        ),
        (
            translate("figure_wwr", language),
            "{:.1%}".format(ratio) if ratio is not None else translate("value_unavailable", language),
        ),
    ]
    for label, value in rows:
        top += 6.0
        page.text(x, top + 6.0, label, size_pt=7.5, colour=MUTED)
        page.text(
            x,
            top + 6.0,
            value,
            size_pt=7.5,
            bold=True,
            colour=INK,
            align="right",
            width_mm=width,
        )
    return top + 10.0


def _draw_scope_block(
    page: PdfPage, top: float, verdict: ComplianceVerdict, language: str
) -> float:
    """Draw the mandatory scope and limitation statement."""

    statements = [
        translate("scope_line_1", language),
        translate("scope_line_2", language),
    ]
    if verdict.outstanding:
        statements.append(
            translate("scope_outstanding", language).format(
                items=", ".join(
                    translate("outstanding_" + item, language)
                    for item in verdict.outstanding
                )
            )
        )
    # A scope or limitation statement is wrapped, never truncated: cutting its
    # end would change what the report claims.
    size = 7.2
    usable = CONTENT_WIDTH - 10.0
    lines: List[str] = []
    for statement in statements:
        lines.extend(wrap_to_width(statement, size, usable))
    height = 6.0 + 4.0 * len(lines)
    page.rect(MARGIN, top, CONTENT_WIDTH, height, fill=WARN_BG)
    page.rect(MARGIN, top, 2.0, height, fill=WARN)
    inner = top + 5.4
    for line in lines:
        page.text(MARGIN + 6.0, inner, line, size_pt=size, colour=(0.36, 0.26, 0.05))
        inner += 4.0
    return top + height + 5.0


def _draw_signature(
    page: PdfPage, top: float, profile: CompanyProfile, language: str
) -> None:
    """Draw the signature block; unset office details stay visibly empty."""

    page.text(
        MARGIN,
        top,
        translate("section_signature", language).upper(),
        size_pt=7.5,
        bold=True,
        colour=BRAND,
    )
    top += 3.0
    page.line(MARGIN, top, A4_MM[0] - MARGIN, top, width_pt=0.5, colour=LINE)
    top += 12.0
    for column, (label, value) in enumerate(
        (
            (translate("signature_name", language), profile.author_name),
            (translate("signature_role", language), profile.author_role),
            (translate("signature_date", language), ""),
        )
    ):
        left = MARGIN + column * (CONTENT_WIDTH / 3.0)
        page.line(left, top, left + CONTENT_WIDTH / 3.0 - 8.0, top, width_pt=0.5, colour=MUTED)
        page.text(left, top + 4.2, label, size_pt=7.0, colour=MUTED)
        if value:
            page.text(left, top - 1.6, value, size_pt=8.0, colour=INK)


def _draw_footer(page: PdfPage, page_number: int, total: int, language: str) -> None:
    """Draw the page footer with the non-certification reminder."""

    y = A4_MM[1] - 10.0
    page.line(MARGIN, y - 4.0, A4_MM[0] - MARGIN, y - 4.0, width_pt=0.4, colour=LINE)
    page.text(MARGIN, y, translate("footer_not_certificate", language), size_pt=6.5, colour=MUTED)
    page.text(
        A4_MM[0] - MARGIN - 30.0,
        y,
        translate("footer_page", language).format(page=page_number, total=total),
        size_pt=6.5,
        colour=MUTED,
        align="right",
        width_mm=30.0,
    )


def render_compliance_report_pdf(
    output_path: Union[str, Path],
    project_label: str,
    rooms_data: Optional[Sequence[Any]],
    sia3802_results: Optional[Dict[str, Any]],
    sia4010_results: Optional[Dict[str, Any]],
    score_result: Any = None,
    profile: Optional[CompanyProfile] = None,
    project_root: Optional[Union[str, Path]] = None,
    language: str = "en",
    model_name: str = "",
) -> Path:
    """Render the company SIA compliance report and return the written path."""

    code = normalize_language(language)
    office = profile
    if office is None:
        office = load_company_profile(project_root or Path.cwd())
    rooms = list(rooms_data or [])
    verdict = build_compliance_verdict(sia3802_results, sia4010_results, len(rooms))
    summary = summarise_model(rooms)
    scores = {
        "compliance": getattr(score_result, "compliance_score", None),
        "health": getattr(score_result, "health_score", None),
    }

    document = PdfDocument(
        title="{} - {}".format(translate("report_title", code), project_label)
    )
    page = document.add_page()
    cursor = _draw_letterhead(page, office, code)
    page.text(
        MARGIN,
        cursor,
        translate("report_title", code),
        size_pt=17.0,
        bold=True,
        colour=INK,
    )
    cursor += 6.0
    page.text(
        MARGIN,
        cursor,
        translate("report_subtitle", code),
        size_pt=9.0,
        colour=MUTED,
    )
    cursor += 8.0
    cursor = _draw_verdict_banner(page, cursor, verdict, code)

    identification = [
        (translate("field_project", code), project_label or translate("value_unavailable", code)),
        (translate("field_model", code), model_name or translate("value_unavailable", code)),
        (
            translate("field_generated", code),
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ),
        (translate("field_framework", code), "SIA 380/2:2022 + SIA 4010:2023"),
        (
            translate("field_reference", code),
            office.report_reference or translate("value_unavailable", code),
        ),
    ]
    cursor = _draw_identification(page, cursor, identification, code)
    cursor = _draw_domain_table(page, cursor, verdict, code)

    column_width = (CONTENT_WIDTH - 6.0) / 2.0
    thumbnail_bottom = _draw_model_thumbnail(
        page, MARGIN, cursor, column_width, summary, code
    )
    figures_bottom = _draw_key_figures(
        page,
        MARGIN + column_width + 6.0,
        cursor - 6.0,
        column_width,
        summary,
        scores,
        code,
    )
    cursor = max(thumbnail_bottom, figures_bottom) + 2.0
    cursor = _draw_scope_block(page, cursor, verdict, code)
    _draw_signature(page, cursor, office, code)
    _draw_footer(page, 1, 1, code)
    return document.save(output_path)
