"""Render the company-letterhead SIA compliance report as a PDF.

The document states, on the office's own letterhead, what the analysis of one
VE model found against SIA 380/2 and, for internal combined reports, what
validation state the toolchain holds under SIA 4010. It is an engineering
assessment report, not an official SIA certificate. The verdict engine in
:mod:`swiss_sia.compliance_verdict` keeps every undetermined item visible
instead of reading as compliant.

When the client interface supplies a Model Viewer capture, that image is used
as the report thumbnail. Otherwise the report falls back to a schematic drawn
from extracted opaque and glazed areas; it never invents surface geometry.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from .company_profile import CompanyProfile, load_company_profile
from .compliance_criteria import CLIENT_LIMITATIONS
from .config import SIA_COMPLIANCE_REQUIREMENT_MATRIX
from .compliance_verdict import (
    COMPLIANT,
    NOT_COMPLIANT,
    NOT_DETERMINED,
    _INDETERMINATE_RULE_MARKERS,
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
REPORT_SCOPES = frozenset(("sia3802", "both"))


def normalize_report_scope(scope: str = "both") -> str:
    """Return a supported report scope or fail closed on an unknown value."""

    normalized = str(scope or "").strip().lower()
    if normalized not in REPORT_SCOPES:
        raise ValueError(
            "Unsupported compliance report scope {!r}; expected one of {}".format(
                scope, sorted(REPORT_SCOPES)
            )
        )
    return normalized


def scoped_verdict_status(verdict: ComplianceVerdict, scope: str = "both") -> str:
    """Return the headline status for the explicitly selected report scope."""

    normalized = normalize_report_scope(scope)
    if normalized == "sia3802":
        return verdict.sia3802_status
    return verdict.overall_status


def _scoped_outstanding(verdict: ComplianceVerdict, scope: str) -> Tuple[str, ...]:
    """Return only reserves that belong to the selected report scope."""

    if normalize_report_scope(scope) == "sia3802":
        return tuple(
            item for item in verdict.outstanding if not item.startswith("sia4010_")
        )
    return verdict.outstanding


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

    if not profile.is_configured:
        # No invented issuer and no shipped placeholder logo.  A compact,
        # factual report identity is preferable to a large warning-like
        # "engineering office not configured" banner on a client document.
        page.rect(0, 0, A4_MM[0], 20.0, fill=BRAND_DEEP)
        page.rect(0, 20.0, A4_MM[0], 1.4, fill=ACCENT)
        page.text(MARGIN, 12.5, "SIA 380/2", size_pt=13.0, bold=True, colour=WHITE)
        page.text(
            A4_MM[0] - MARGIN - 70.0,
            12.5,
            translate("report_neutral_header", language),
            size_pt=8.5,
            colour=(0.741, 0.882, 0.831),
            align="right",
            width_mm=70.0,
        )
        return 30.0

    page.rect(0, 0, A4_MM[0], 30.0, fill=BRAND_DEEP)
    page.rect(0, 30.0, A4_MM[0], 1.4, fill=ACCENT)
    text_left = MARGIN
    if profile.logo_path is not None:
        try:
            page.image_contain(MARGIN, 6.5, 17.0, 17.0, profile.logo_path)
            text_left = MARGIN + 21.0
        except Exception:
            # A logo that cannot be embedded must never block the report.
            text_left = MARGIN
    page.text(
        text_left,
        13.5,
        truncate_to_width(profile.name, 15.0, 120.0, bold=True),
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
    page: PdfPage,
    top: float,
    verdict: ComplianceVerdict,
    language: str,
    scope: str = "both",
) -> float:
    """Draw the headline verdict block and return the y position below it."""

    normalized_scope = normalize_report_scope(scope)
    status = scoped_verdict_status(verdict, normalized_scope)
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
    counts = "{} / {} / {}".format(
        verdict.blocking_total,
        verdict.missing_total,
        verdict.advisory_total,
    )
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
    # Two-column card: fits the client/project identification (client, address,
    # mandate, author, checker, index, framework...) without pushing the rest of
    # the one-page report off the sheet.
    column_width = CONTENT_WIDTH / 2.0
    label_width = 34.0
    value_width = column_width - label_width - 4.0
    row_height = 5.0
    for index, (label, value) in enumerate(rows):
        column = index % 2
        line_index = index // 2
        x = MARGIN + column * column_width
        y = top + line_index * row_height
        page.text(x, y, label, size_pt=7.5, colour=MUTED)
        page.text(
            x + label_width,
            y,
            truncate_to_width(value, 7.5, value_width),
            size_pt=7.5,
            colour=INK,
        )
    line_count = (len(rows) + 1) // 2
    return top + line_count * row_height + 3.0


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
    columns = (0.0, 62.0, 108.0, 132.0, 156.0)
    headers = (
        translate("column_domain", language),
        translate("column_status", language),
        translate("column_blocking", language),
        translate("column_missing", language),
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
            str(domain.missing_count),
            size_pt=8.0,
            colour=WARN,
        )
        page.text(
            MARGIN + columns[4],
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
    image_path: Optional[Union[str, Path]] = None,
) -> float:
    """Draw the selected Model Viewer image or the extracted-data schematic."""

    height = 46.0
    page.rect(x, top, width, height, fill=PANEL, stroke=LINE, width_pt=0.4)
    thumbnail_title = "client_ui_viewer" if image_path else "section_model"
    page.text(
        x + 4.0,
        top + 6.0,
        translate(thumbnail_title, language).upper(),
        size_pt=7.0,
        bold=True,
        colour=BRAND,
    )
    if image_path:
        try:
            page.image_contain(
                x + 4.0, top + 9.0, width - 8.0, height - 13.0, image_path
            )
            return top + height + 3.0
        except Exception:
            # A broken optional presentation image cannot block the report.
            pass
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
    page: PdfPage,
    top: float,
    verdict: ComplianceVerdict,
    language: str,
    scope: str = "both",
) -> float:
    """Draw the mandatory scope and limitation statement."""

    normalized_scope = normalize_report_scope(scope)
    suffix = "_sia3802" if normalized_scope == "sia3802" else ""
    statements = [
        translate("scope_line_1" + suffix, language),
        translate("scope_line_2" + suffix, language),
    ]
    outstanding = _scoped_outstanding(verdict, normalized_scope)
    if outstanding:
        statements.append(
            translate("scope_outstanding", language).format(
                items=", ".join(
                    translate("outstanding_" + item, language)
                    for item in outstanding
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


def _draw_footer(
    page: PdfPage,
    page_number: int,
    total: int,
    language: str,
    ies_logo_path: Optional[Path] = None,
) -> None:
    """Draw the page footer: non-certification reminder, IES brand mark, page no.

    ``ies_logo_path`` embeds the real IES logo when the asset is present; when it
    is absent the footer falls back to the "Powered by IES Virtual Environment"
    wordmark so the report always carries the product provenance without ever
    reproducing a logo the project does not ship.
    """

    y = A4_MM[1] - 10.0
    page.line(MARGIN, y - 4.0, A4_MM[0] - MARGIN, y - 4.0, width_pt=0.4, colour=LINE)
    page.text(MARGIN, y, translate("footer_not_certificate", language), size_pt=6.5, colour=MUTED)

    powered_by = translate("footer_powered_by", language)
    centre = A4_MM[0] / 2.0
    logo_drawn = False
    if ies_logo_path is not None:
        try:
            page.image_contain(centre - 26.0, y - 4.2, 6.0, 6.0, ies_logo_path)
            logo_drawn = True
        except Exception:
            # A logo that cannot be embedded must never block the report.
            logo_drawn = False
    page.text(
        centre - (18.0 if logo_drawn else 30.0),
        y,
        powered_by,
        size_pt=6.5,
        colour=BRAND,
    )
    page.text(
        A4_MM[0] - MARGIN - 30.0,
        y,
        translate("footer_page", language).format(page=page_number, total=total),
        size_pt=6.5,
        colour=MUTED,
        align="right",
        width_mm=30.0,
    )


def _resolve_ies_logo(project_root: Optional[Union[str, Path]]) -> Optional[Path]:
    """Return the IES brand logo asset path when the user has supplied one.

    Looked up at ``assets/ies_logo.png`` (or .jpg) under the project root. The
    project does not ship the IES logo; drop the real asset there to embed it.
    """

    root = Path(project_root) if project_root else Path.cwd()
    for name in ("assets/ies_logo.png", "assets/ies_logo.jpg", "assets/ies_logo.jpeg"):
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def _alert_value(alert: Any, key: str, default: Any = "") -> Any:
    """Read one alert field from either the real dataclass or a test mapping."""

    if isinstance(alert, dict):
        return alert.get(key, default)
    return getattr(alert, key, default)


def _alert_severity(alert: Any) -> str:
    """Return a stable upper-case severity name."""

    severity = _alert_value(alert, "severity", "")
    name = getattr(severity, "name", None) or getattr(severity, "value", None)
    return str(name or severity or "").upper()


def _alert_is_indeterminate(alert: Any) -> bool:
    """Return whether an alert represents absent/uncheckable evidence."""

    rule = str(_alert_value(alert, "rule", "") or "").upper()
    return any(marker in rule for marker in _INDETERMINATE_RULE_MARKERS) or any(
        marker in rule for marker in ("NOT_COMPARABLE", "SOURCE_NOT_COMPARABLE")
    )


def _alert_kind(alert: Any) -> str:
    """Classify a finding consistently with the fail-closed verdict engine."""

    if _alert_is_indeterminate(alert):
        return "missing"
    if _alert_severity(alert) in {"CRITICAL", "HIGH"}:
        return "blocking"
    return "advisory"


def _criterion_for_alert(alert: Any) -> Dict[str, Any]:
    """Find the closest configured SIA criterion without inventing a limit."""

    rule = str(_alert_value(alert, "rule", "") or "").upper()
    if not rule:
        return {}
    for entry in SIA_COMPLIANCE_REQUIREMENT_MATRIX:
        candidates = [
            item.strip().upper()
            for item in str(entry.get("implemented_rule") or "").split("/")
            if item.strip()
        ]
        if any(rule == item or rule.startswith(item + "_") or item in rule for item in candidates):
            return entry

    # Missing-data alerts often permute the same tokens as the evaluated rule
    # (e.g. WINDOW_U_VALUE_MISSING vs U_VALUE_WINDOW). Token overlap gives the
    # report its configured reference only when the match is unambiguous enough.
    ignored = {
        "SIA3802", "SIA4010", "MISSING", "NOT", "CHECKABLE", "UNAVAILABLE",
        "SOURCE", "COMPARABLE", "ERROR", "RULE", "MODEL",
    }
    rule_tokens = {part for part in rule.split("_") if part and part not in ignored}
    category = str(_alert_value(alert, "category", "") or "")
    compatible_domains = {
        "Envelope": {"Envelope"},
        "Openings": {"Openings", "Solar protection"},
        "Ventilation": {"Ventilation"},
        "HVAC": {"Cooling", "Heating"},
    }.get(category, set())
    if not compatible_domains:
        return {}
    scored: List[Tuple[int, Dict[str, Any]]] = []
    for entry in SIA_COMPLIANCE_REQUIREMENT_MATRIX:
        if str(entry.get("domain") or "") not in compatible_domains:
            continue
        implemented = str(entry.get("implemented_rule") or "").upper()
        tokens = {part for part in implemented.replace(" / ", "_").split("_") if part and part not in ignored}
        score = len(rule_tokens.intersection(tokens))
        if score >= 2:
            scored.append((score, entry))
    if not scored:
        return {}
    scored.sort(key=lambda item: item[0], reverse=True)
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return {}
    return scored[0][1]


def _format_reference_value(value: Any, unit: Any, language: str) -> str:
    """Format a configured limit/target exactly as stored in the matrix."""

    if value is None or value == "":
        return translate("report_value_not_available", language)
    if isinstance(value, float):
        text = ("{:.4g}".format(value)).rstrip("0").rstrip(".")
    else:
        text = str(value)
    unit_text = str(unit or "").strip()
    if unit_text and unit_text not in {"-", "minimum"}:
        text = "{} {}".format(text, unit_text)
    return text


def _model_data_text(alert: Any, language: str) -> str:
    """Summarise only scalar model evidence carried by the real alert."""

    data = _alert_value(alert, "data", None)
    if data is None:
        return translate("report_value_not_available", language)
    if isinstance(data, dict):
        values = data
    else:
        try:
            values = vars(data)
        except TypeError:
            values = {}
    preferred = (
        "name", "id", "room_name", "surface_name", "opening_name",
        "value", "actual", "u_value", "solar_factor", "g_total",
        "visible_transmittance", "frame_fraction", "air_exchange_rate",
        "infiltration_rate", "area", "orientation", "heating_setpoint",
        "cooling_setpoint", "power_density", "efficiency", "eer", "seer", "scop",
        "upper_hours", "upper_limit_hours", "lower_hours", "window_operable",
        "method",
    )
    parts: List[str] = []
    for key in preferred:
        value = values.get(key)
        if value is None or value == "" or isinstance(value, (dict, list, tuple, set)):
            continue
        label = key.replace("_", " ")
        parts.append("{}: {}".format(label, value))
        if len(parts) == 6:
            break
    return "; ".join(parts) or translate("report_value_not_available", language)


def _decision_reason(verdict: ComplianceVerdict, language: str) -> str:
    """Return the translated, explicit reason for the SIA 380/2 decision."""

    return translate("report_reason_" + verdict.sia3802_reason, language)


def _decision_action(verdict: ComplianceVerdict, language: str) -> str:
    """Return the concrete next step associated with the overall decision."""

    return translate("report_action_" + verdict.sia3802_reason, language)


def _detail_section_header(page: PdfPage, top: float, key: str, language: str) -> float:
    """Draw a reusable detailed-report section heading."""

    page.text(MARGIN, top, translate(key, language).upper(), size_pt=8.0, bold=True, colour=BRAND)
    top += 3.0
    page.line(MARGIN, top, A4_MM[0] - MARGIN, top, width_pt=0.5, colour=LINE)
    return top + 5.5


def _draw_detailed_pages(
    document: PdfDocument,
    office: CompanyProfile,
    verdict: ComplianceVerdict,
    sia3802_results: Optional[Dict[str, Any]],
    language: str,
    rooms_data: Optional[Sequence[Any]] = None,
) -> List[PdfPage]:
    """Add a paginated decision rationale and every SIA 380/2 finding."""

    results = dict(sia3802_results or {})
    alerts = list(results.get("alerts", []) or [])
    pages: List[PdfPage] = []
    page: PdfPage
    cursor: float

    def new_page(continued: bool = False) -> Tuple[PdfPage, float]:
        detail_page = document.add_page()
        pages.append(detail_page)
        top = _draw_letterhead(detail_page, office, language)
        detail_page.text(
            MARGIN,
            top,
            translate("report_details_continued" if continued else "report_details_title", language),
            size_pt=15.0,
            bold=True,
            colour=INK,
        )
        top += 6.5
        if not continued:
            detail_page.text(
                MARGIN,
                top,
                translate("report_details_subtitle", language),
                size_pt=8.2,
                colour=MUTED,
            )
            top += 8.0
        else:
            top += 4.0
        return detail_page, top

    page, cursor = new_page()

    # Explicit decision rationale and decisive project/reference figures.
    cursor = _detail_section_header(page, cursor, "report_decision_basis", language)
    status_colour, status_bg = _STATUS_COLOURS.get(verdict.sia3802_status, (WARN, WARN_BG))
    reason_lines = wrap_to_width(_decision_reason(verdict, language), 8.1, CONTENT_WIDTH - 12.0)
    action_lines = wrap_to_width(_decision_action(verdict, language), 7.6, CONTENT_WIDTH - 44.0)
    decision_height = 19.0 + len(reason_lines) * 4.2 + max(1, len(action_lines)) * 3.9
    page.rect(MARGIN, cursor, CONTENT_WIDTH, decision_height, fill=status_bg)
    page.rect(MARGIN, cursor, 2.2, decision_height, fill=status_colour)
    page.text(
        MARGIN + 6.0, cursor + 6.0, _status_label(verdict.sia3802_status, language),
        size_pt=11.0, bold=True, colour=status_colour,
    )
    y = cursor + 12.0
    for line in reason_lines:
        page.text(MARGIN + 6.0, y, line, size_pt=8.1, colour=INK)
        y += 4.2
    y += 1.0
    page.text(MARGIN + 6.0, y, translate("report_finding_action", language), size_pt=6.8, bold=True, colour=status_colour)
    for line_index, line in enumerate(action_lines):
        page.text(MARGIN + 40.0, y + line_index * 3.9, line, size_pt=7.6, colour=INK)
    cursor += decision_height + 6.0

    comparison = results.get("global_reference_comparison", {}) or {}
    if not isinstance(comparison, dict):
        comparison = {}
    page.text(MARGIN, cursor, translate("report_global_comparison", language), size_pt=9.0, bold=True, colour=INK)
    cursor += 5.0
    comparison_rows = (
        ("report_comparison_status", comparison.get("status")),
        ("report_comparison_project_value", comparison.get("project_value")),
        ("report_comparison_reference_value", comparison.get("reference_value")),
        ("report_comparison_source", comparison.get("source")),
    )
    cell_width = CONTENT_WIDTH / 2.0
    for index, (label_key, value) in enumerate(comparison_rows):
        x = MARGIN + (index % 2) * cell_width
        y = cursor + (index // 2) * 10.0
        page.rect(x, y, cell_width - 2.0, 8.0, fill=PANEL)
        page.text(x + 3.0, y + 3.4, translate(label_key, language), size_pt=6.5, colour=MUTED)
        page.text(
            x + 3.0, y + 6.6,
            truncate_to_width(
                str(value) if value not in (None, "") else translate("report_value_not_available", language),
                7.3,
                cell_width - 8.0,
            ),
            size_pt=7.3, bold=True, colour=INK,
        )
    cursor += 24.0

    # Six domain decisions, including the internal reason rather than only a colour.
    cursor = _detail_section_header(page, cursor, "report_domains_detailed", language)
    for domain in verdict.domains:
        colour, background = _STATUS_COLOURS.get(domain.status, (WARN, WARN_BG))
        page.rect(MARGIN, cursor, CONTENT_WIDTH, 8.0, fill=PANEL)
        page.rect(MARGIN, cursor, 2.0, 8.0, fill=colour)
        page.text(MARGIN + 5.0, cursor + 5.0, translate("domain_" + domain.domain, language), size_pt=8.0, bold=True, colour=INK)
        page.text(
            MARGIN + 54.0, cursor + 5.0,
            translate("report_domain_reason_" + domain.reason, language),
            size_pt=7.2, colour=MUTED,
        )
        page.text(
            A4_MM[0] - MARGIN - 53.0, cursor + 5.0,
            "{}  |  B:{} M:{} A:{}".format(
                _status_label(domain.status, language),
                domain.blocking_count,
                domain.missing_count,
                domain.advisory_count,
            ),
            size_pt=7.1, bold=True, colour=colour, align="right", width_mm=53.0,
        )
        cursor += 9.5
    cursor += 4.0

    # Ventilation is an essential evidence gate.  Show what VE actually proved,
    # even when no alert exists because every applicable room passed.
    rooms = list(rooms_data or [])
    mechanical_rooms = [
        room for room in rooms
        if getattr(room, "mechanical_ventilation_present", None) is True
    ]
    normalized_rooms = [
        room for room in mechanical_rooms
        if _float_or_none(getattr(room, "ventilation_m3_h_m2", None)) is not None
    ]
    controlled_rooms = [
        room for room in mechanical_rooms
        if getattr(room, "ventilation_installation_type", None)
        and getattr(room, "ventilation_control_level", None) is not None
    ]
    reviewed_rooms = [
        room for room in controlled_rooms
        if str(getattr(room, "ventilation_control_level_status", "") or "")
        == "REVIEWER_ACCEPTED"
    ]
    airflow_values = [
        _float_or_none(getattr(room, "ventilation_m3_h_m2", None))
        for room in normalized_rooms
    ]
    airflow_values = [value for value in airflow_values if value is not None]
    cursor = _detail_section_header(
        page, cursor, "report_ventilation_evidence_title", language
    )
    airflow_range = translate("report_value_not_available", language)
    if airflow_values:
        airflow_range = "{:.3g} - {:.3g} m3/(h.m2)".format(
            min(airflow_values), max(airflow_values)
        )
    ventilation_rows = (
        (
            "report_ventilation_rooms",
            "{} / {} (unknown: {})".format(
                len(mechanical_rooms),
                len(rooms),
                sum(
                    1
                    for room in rooms
                    if getattr(room, "mechanical_ventilation_present", None) is None
                ),
            ),
        ),
        (
            "report_ventilation_airflow",
            "{} / {}".format(len(normalized_rooms), len(mechanical_rooms)),
        ),
        (
            "report_ventilation_control",
            "{} / {} (reviewed: {})".format(
                len(controlled_rooms), len(mechanical_rooms), len(reviewed_rooms)
            ),
        ),
        ("report_ventilation_range", airflow_range),
    )
    cell_width = CONTENT_WIDTH / 2.0
    for index, (label_key, value) in enumerate(ventilation_rows):
        x = MARGIN + (index % 2) * cell_width
        y = cursor + (index // 2) * 10.0
        page.rect(x, y, cell_width - 2.0, 8.0, fill=PANEL)
        page.text(x + 3.0, y + 3.2, translate(label_key, language), size_pt=6.3, colour=MUTED)
        page.text(
            x + 3.0,
            y + 6.5,
            truncate_to_width(str(value), 7.2, cell_width - 8.0),
            size_pt=7.2,
            bold=True,
            colour=INK,
        )
    cursor += 24.0

    cursor = _detail_section_header(page, cursor, "report_findings_title", language)
    if not alerts:
        for line in wrap_to_width(translate("report_findings_none", language), 8.0, CONTENT_WIDTH - 4.0):
            page.text(MARGIN + 2.0, cursor, line, size_pt=8.0, colour=MUTED)
            cursor += 4.2
        return pages

    priority = {"blocking": 0, "missing": 1, "advisory": 2}
    alerts.sort(key=lambda item: (priority[_alert_kind(item)], str(_alert_value(item, "category", "")), str(_alert_value(item, "rule", ""))))
    for number, alert in enumerate(alerts, 1):
        kind = _alert_kind(alert)
        criterion = _criterion_for_alert(alert)
        unit = criterion.get("unit")
        title = str(criterion.get("criterion") or _alert_value(alert, "category", "") or _alert_value(alert, "rule", ""))
        fields = [
            (
                "report_finding_observation",
                str(_alert_value(alert, "description", "") or translate("report_value_not_available", language)),
            ),
            ("report_finding_why", translate("report_finding_why_" + kind, language)),
            (
                "report_finding_limit",
                _format_reference_value(criterion.get("limit"), unit, language),
            ),
        ]
        if criterion.get("target") not in (None, ""):
            fields.append(("report_finding_target", _format_reference_value(criterion.get("target"), unit, language)))
        fields.extend(
            [
                ("report_finding_model_data", _model_data_text(alert, language)),
                (
                    "report_finding_source",
                    str(criterion.get("source") or translate("report_value_not_available", language)),
                ),
                (
                    "report_finding_action",
                    str(_alert_value(alert, "recommendation", "") or criterion.get("next_action") or translate("report_value_not_available", language)),
                ),
            ]
        )
        wrapped = [
            (label, wrap_to_width(value, 7.2, CONTENT_WIDTH - 45.0))
            for label, value in fields
        ]
        card_height = 13.0 + sum(max(1, len(lines)) * 3.7 + 1.3 for _, lines in wrapped)
        if cursor + card_height > A4_MM[1] - 24.0:
            page, cursor = new_page(continued=True)
            cursor = _detail_section_header(page, cursor, "report_findings_title", language)

        if kind == "blocking":
            tone, ground = BAD, BAD_BG
        elif kind == "missing":
            tone, ground = WARN, WARN_BG
        else:
            tone, ground = BRAND, PANEL
        page.rect(MARGIN, cursor, CONTENT_WIDTH, card_height, fill=WHITE, stroke=LINE, width_pt=0.5)
        page.rect(MARGIN, cursor, CONTENT_WIDTH, 10.0, fill=ground)
        page.rect(MARGIN, cursor, 2.2, card_height, fill=tone)
        page.text(MARGIN + 6.0, cursor + 6.2, "{:02d}  {}".format(number, title), size_pt=8.7, bold=True, colour=INK)
        page.text(
            A4_MM[0] - MARGIN - 62.0,
            cursor + 6.2,
            translate("report_finding_" + kind, language),
            size_pt=7.0,
            bold=True,
            colour=tone,
            align="right",
            width_mm=59.0,
        )
        rule = str(_alert_value(alert, "rule", "") or "")
        page.text(MARGIN + 6.0, cursor + 10.8, "{}: {}".format(translate("report_finding_rule", language), rule), size_pt=6.2, colour=MUTED)
        y = cursor + 15.0
        for label_key, lines in wrapped:
            page.text(MARGIN + 6.0, y, translate(label_key, language), size_pt=6.8, bold=True, colour=BRAND)
            for line_index, line in enumerate(lines or [""]):
                page.text(MARGIN + 40.0, y + line_index * 3.7, line, size_pt=7.2, colour=INK)
            y += max(1, len(lines)) * 3.7 + 1.3
        cursor += card_height + 5.0
    return pages


def _draw_annex_page(
    document: PdfDocument,
    office: CompanyProfile,
    verdict: ComplianceVerdict,
    language: str,
    scope: str = "both",
) -> PdfPage:
    """Draw the second-page annex: limitations, reserves and methodology."""

    page = document.add_page()
    cursor = _draw_letterhead(page, office, language)
    page.text(
        MARGIN, cursor, translate("annex_title", language),
        size_pt=15.0, bold=True, colour=INK,
    )
    cursor += 9.0

    def _section_header(top: float, key: str) -> float:
        page.text(MARGIN, top, translate(key, language).upper(),
                  size_pt=8.0, bold=True, colour=BRAND)
        top += 3.0
        page.line(MARGIN, top, A4_MM[0] - MARGIN, top, width_pt=0.5, colour=LINE)
        return top + 5.5

    # 1. Structural limitations, each with its justification.
    cursor = _section_header(cursor, "annex_limitations_title")
    for item in CLIENT_LIMITATIONS.get(language, CLIENT_LIMITATIONS["en"]):
        page.rect(MARGIN, cursor - 2.6, 1.6, 1.6, fill=MUTED)
        page.text(MARGIN + 4.0, cursor, item["title"], size_pt=8.5, bold=True, colour=INK)
        cursor += 4.6
        for line in wrap_to_width(item["why"], 7.5, CONTENT_WIDTH - 4.0):
            page.text(MARGIN + 4.0, cursor, line, size_pt=7.5, colour=MUTED)
            cursor += 3.8
        cursor += 2.0
    cursor += 3.0

    # 2. Outstanding model reserves for this run (dynamic).
    cursor = _section_header(cursor, "annex_reserves_title")
    outstanding = _scoped_outstanding(verdict, scope)
    if outstanding:
        for item in outstanding:
            text = "• " + translate("outstanding_" + item, language)
            for line in wrap_to_width(text, 7.8, CONTENT_WIDTH - 4.0):
                page.text(MARGIN + 2.0, cursor, line, size_pt=7.8, colour=INK)
                cursor += 4.2
            cursor += 1.0
    else:
        page.text(MARGIN + 2.0, cursor, translate("annex_reserves_none", language),
                  size_pt=7.8, colour=OK)
        cursor += 5.0
    cursor += 4.0

    # 3. Methodology and data sources.
    cursor = _section_header(cursor, "annex_method_title")
    for line in wrap_to_width(translate("annex_method_body", language), 7.8, CONTENT_WIDTH - 4.0):
        page.text(MARGIN + 2.0, cursor, line, size_pt=7.8, colour=INK)
        cursor += 4.2
    return page


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
    scope: str = "both",
    report_context: Any = None,
) -> Path:
    """Render the company SIA compliance report and return the written path.

    ``scope="both"`` retains the combined SIA 380/2 and SIA 4010 headline.
    ``scope="sia3802"`` reports only the SIA 380/2 status, reserves and scope;
    the client report contains no SIA 4010 readiness indicator.
    """

    code = normalize_language(language)
    report_scope = normalize_report_scope(scope)
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
    context_value = (
        (lambda key, default="": report_context.get(key, default))
        if isinstance(report_context, dict)
        else (lambda key, default="": getattr(report_context, key, default))
    )
    client_logo = str(context_value("client_logo_path", "") or "").strip()
    if client_logo and Path(client_logo).is_file():
        try:
            page.image_contain(
                A4_MM[0] - MARGIN - 19.0,
                cursor - 5.0,
                19.0,
                13.0,
                client_logo,
            )
        except Exception:
            pass
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
        translate(
            "report_subtitle_sia3802" if report_scope == "sia3802" else "report_subtitle",
            code,
        ),
        size_pt=9.0,
        colour=MUTED,
    )
    cursor += 8.0
    cursor = _draw_verdict_banner(page, cursor, verdict, code, report_scope)

    to_complete = translate("value_to_complete", code)
    identification = [
        (translate("field_client", code), str(context_value("client_name", "") or to_complete)),
        (translate("field_project", code), str(context_value("project_name", "") or project_label or translate("value_unavailable", code))),
        (translate("field_project_address", code), str(context_value("project_address", "") or to_complete)),
        (translate("field_model", code), model_name or translate("value_unavailable", code)),
        (translate("field_mandate", code), str(context_value("report_reference", "") or office.report_reference or to_complete)),
        (
            translate("field_generated", code),
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ),
        (translate("field_prepared_by", code), str(context_value("prepared_by", "") or office.author_name or to_complete)),
        (translate("client_ui_weather", code), str(context_value("weather_file", "") or translate("value_unavailable", code))),
        (translate("field_framework", code), "SIA 380/2:2022" if report_scope == "sia3802" else "SIA 380/2:2022 + SIA 4010:2023"),
        (translate("field_solar_shading", code), str(context_value("solar_shading", "TO_CONFIRM") or "TO_CONFIRM")),
    ]
    cursor = _draw_identification(page, cursor, identification, code)
    cursor = _draw_domain_table(page, cursor, verdict, code)

    column_width = (CONTENT_WIDTH - 6.0) / 2.0
    thumbnail_bottom = _draw_model_thumbnail(
        page,
        MARGIN,
        cursor,
        column_width,
        summary,
        code,
        image_path=str(context_value("model_viewer_image_path", "") or "") or None,
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
    cursor = _draw_scope_block(page, cursor, verdict, code, report_scope)
    _draw_signature(page, cursor, office, code)
    ies_logo = _resolve_ies_logo(project_root)

    _draw_detailed_pages(
        document, office, verdict, sia3802_results, code, rooms_data=rooms
    )
    _draw_annex_page(document, office, verdict, code, report_scope)
    total_pages = len(document.pages)
    for page_number, report_page in enumerate(document.pages, 1):
        _draw_footer(
            report_page,
            page_number,
            total_pages,
            code,
            ies_logo_path=ies_logo,
        )
    return document.save(output_path)
