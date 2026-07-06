"""
IESVE Model Intelligence Dashboard
==================================

Create a polished Excel dashboard for an open IESVE project.

Purpose
-------
This script audits the current VE model and generates a professional workbook
with executive dashboarding, room and area intelligence, envelope/opening
analysis, thermal template and construction summaries, QA recommendations, and
API diagnostics for traceability.

Run from inside the IESVE Python scripting environment.
"""

from __future__ import annotations

import os
from collections import Counter
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

import iesve
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
import xlsxwriter


DEFAULT_OUTPUT_NAME = "IESVE_Model_Intelligence_Dashboard"
MIN_ROOM_AREA_M2 = 0.5
HIGH_ROOM_AREA_M2 = 250.0
HIGH_WWR_PERCENT = 75.0


class DashboardError(Exception):
    """Raised when the dashboard cannot be created safely."""


def safe_float(value: Any) -> Optional[float]:
    """Convert a value to float when possible."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_text(value: Any, default: str = "") -> str:
    """Convert a value to clean text."""
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def compact(value: Any, max_length: int = 240) -> str:
    """Return compact text for worksheet cells."""
    text = safe_text(value)
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text


def normalize_key(value: Any) -> str:
    """Normalize names for matching dictionaries."""
    text = safe_text(value).lower()
    for token in (" ", "_", "-", ".", "/", "\\", "(", ")", "[", "]"):
        text = text.replace(token, "")
    return text


def safe_call(method: Any, patterns: Iterable[Tuple[Any, ...]]) -> Tuple[bool, Any, str]:
    """Try multiple call signatures for IESVE API compatibility."""
    if not callable(method):
        return False, None, "method not available"
    last_error = ""
    for args in patterns:
        try:
            return True, method(*args), ""
        except Exception as exc:
            last_error = str(exc)
    return False, None, last_error


def get_project_path(project: Any) -> str:
    """Return the current IESVE project path."""
    return safe_text(getattr(project, "path", None), os.getcwd())


def get_project_name(project: Any) -> str:
    """Return the current project name."""
    return safe_text(getattr(project, "name", None), "Unnamed IESVE Project")


def get_display_units(project: Any) -> Dict[str, Any]:
    """Read display units from VEProject when available."""
    method = getattr(project, "get_display_units", None)
    ok, value, _ = safe_call(method, ((),))
    return value if ok and isinstance(value, dict) else {}


def collect_api_diagnostics(project: Any) -> List[Dict[str, str]]:
    """Record which documented APIs are available in this IESVE project."""
    diagnostics = []
    project_methods = [
        "get_display_units",
        "get_version",
        "get_areas_list",
        "get_surfaces_list",
        "get_room_data",
        "get_assigned_constructions_list",
        "get_assigned_profiles_list",
        "get_bodies_list",
        "get_bodies_and_ids_list",
    ]
    for method_name in project_methods:
        method = getattr(project, method_name, None)
        ok, value, error = safe_call(method, ((), ("",), (None,)))
        diagnostics.append(
            {
                "API Object": "VEProject",
                "Method": method_name,
                "Available": "YES" if callable(method) else "NO",
                "Status": "OK" if ok else "NOT USED",
                "Return Type": describe_value(value) if ok else "",
                "Message": compact(error),
            }
        )

    try:
        room_groups = iesve.RoomGroups()
    except Exception:
        room_groups = None

    if room_groups is not None:
        for method_name in ("get_grouping_schemes", "get_room_groups"):
            method = getattr(room_groups, method_name, None)
            ok, value, error = safe_call(method, ((), ("",), (0,)))
            diagnostics.append(
                {
                    "API Object": "RoomGroups",
                    "Method": method_name,
                    "Available": "YES" if callable(method) else "NO",
                    "Status": "OK" if ok else "NOT USED",
                    "Return Type": describe_value(value) if ok else "",
                    "Message": compact(error),
                }
            )

    return diagnostics


def describe_value(value: Any) -> str:
    """Describe an API return value."""
    if value is None:
        return "None"
    if isinstance(value, dict):
        return f"dict ({len(value)} keys)"
    if isinstance(value, (list, tuple)):
        return f"{type(value).__name__} ({len(value)} items)"
    return type(value).__name__


def extract_room_rows_from_area_list(project: Any) -> List[Dict[str, Any]]:
    """Use get_areas_list() as the primary source for room-level area data."""
    method = getattr(project, "get_areas_list", None)
    ok, data, _ = safe_call(method, ((),))
    if not ok or not data:
        return []

    rows = []

    if isinstance(data, dict):
        iterable = data.items()
    else:
        iterable = enumerate(data if isinstance(data, list) else [])

    for key, item in iterable:
        if isinstance(item, dict):
            room_name = (
                item.get("name")
                or item.get("room_name")
                or item.get("space_name")
                or key
            )
            area = (
                item.get("floor_area")
                or item.get("area")
                or item.get("net_area")
                or item.get("value")
            )
            body = item.get("body") or item.get("body_name") or ""
            room_id = item.get("id") or item.get("room_id") or key
        elif isinstance(item, (list, tuple)):
            room_name = item[0] if len(item) > 0 else key
            area = item[1] if len(item) > 1 else None
            body = item[2] if len(item) > 2 else ""
            room_id = key
        else:
            room_name = key
            area = item
            body = ""
            room_id = key

        area_value = safe_float(area)
        rows.append(
            {
                "Room ID": safe_text(room_id),
                "Room Name": safe_text(room_name, "Unknown"),
                "Body": safe_text(body, "Unassigned"),
                "Floor Area (m2)": round(area_value or 0.0, 2),
                "Source": "get_areas_list",
            }
        )

    return rows


def extract_room_rows_from_room_data(project: Any) -> List[Dict[str, Any]]:
    """Fallback room extraction using get_room_data when available."""
    method = getattr(project, "get_room_data", None)
    ok, data, _ = safe_call(method, ((), ("",), (None,)))
    if not ok or not data:
        return []

    rows = []
    iterable = data if isinstance(data, list) else [data]
    for index, item in enumerate(iterable):
        if isinstance(item, dict):
            room_name = (
                item.get("name")
                or item.get("room_name")
                or item.get("space_name")
                or f"Room {index + 1}"
            )
            area = item.get("floor_area") or item.get("area") or item.get("net_area")
            body = item.get("body") or item.get("body_name") or ""
            room_id = item.get("id") or item.get("room_id") or index + 1
        else:
            continue

        rows.append(
            {
                "Room ID": safe_text(room_id),
                "Room Name": safe_text(room_name, "Unknown"),
                "Body": safe_text(body, "Unassigned"),
                "Floor Area (m2)": round(safe_float(area) or 0.0, 2),
                "Source": "get_room_data",
            }
        )
    return rows


def collect_room_rows(project: Any) -> List[Dict[str, Any]]:
    """Collect and de-duplicate room rows."""
    rows = extract_room_rows_from_area_list(project)
    if not rows:
        rows = extract_room_rows_from_room_data(project)

    deduped = []
    seen = set()
    for row in rows:
        key = normalize_key(row["Room ID"]) or normalize_key(row["Room Name"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def collect_surface_rows(project: Any) -> List[Dict[str, Any]]:
    """Collect surface and opening information when available."""
    method = getattr(project, "get_surfaces_list", None)
    ok, data, _ = safe_call(method, ((), ("",), (None,)))
    if not ok or not data:
        return []

    rows = []
    iterable = data if isinstance(data, list) else list(data.values()) if isinstance(data, dict) else []
    for index, item in enumerate(iterable):
        if isinstance(item, dict):
            surface_name = item.get("name") or item.get("surface_name") or f"Surface {index + 1}"
            room_name = item.get("room") or item.get("room_name") or item.get("space_name") or ""
            area = item.get("area") or item.get("gross_area") or item.get("net_area")
            surface_type = item.get("type") or item.get("surface_type") or ""
            construction = item.get("construction") or item.get("construction_name") or ""
            opening_area = (
                item.get("opening_area")
                or item.get("glazing_area")
                or item.get("window_area")
                or 0.0
            )
        elif isinstance(item, (list, tuple)):
            surface_name = item[0] if len(item) > 0 else f"Surface {index + 1}"
            room_name = item[1] if len(item) > 1 else ""
            area = item[2] if len(item) > 2 else None
            surface_type = item[3] if len(item) > 3 else ""
            construction = item[4] if len(item) > 4 else ""
            opening_area = item[5] if len(item) > 5 else 0.0
        else:
            continue

        area_value = safe_float(area) or 0.0
        opening_value = safe_float(opening_area) or 0.0
        wwr = round(opening_value / area_value * 100.0, 1) if area_value > 0 else 0.0
        rows.append(
            {
                "Surface Name": safe_text(surface_name, f"Surface {index + 1}"),
                "Room Name": safe_text(room_name, "Unknown"),
                "Surface Type": safe_text(surface_type, "Unknown"),
                "Construction": safe_text(construction, "Unknown"),
                "Area (m2)": round(area_value, 2),
                "Opening Area (m2)": round(opening_value, 2),
                "Opening Ratio (%)": wwr,
            }
        )
    return rows


def collect_assignment_rows(project: Any, method_name: str, label: str) -> List[Dict[str, str]]:
    """Collect assigned constructions or profiles/templates."""
    method = getattr(project, method_name, None)
    ok, data, _ = safe_call(method, ((), ("",), (None,)))
    if not ok or not data:
        return []

    rows = []
    iterable = data if isinstance(data, list) else list(data.items()) if isinstance(data, dict) else []
    for item in iterable:
        if isinstance(item, dict):
            target = item.get("room") or item.get("room_name") or item.get("surface") or item.get("name") or ""
            assignment = (
                item.get("construction")
                or item.get("construction_name")
                or item.get("profile")
                or item.get("profile_name")
                or item.get("template")
                or item.get("template_name")
                or item.get("value")
                or ""
            )
        elif isinstance(item, (list, tuple)):
            target = item[0] if len(item) > 0 else ""
            assignment = item[1] if len(item) > 1 else ""
        else:
            target = ""
            assignment = item

        rows.append(
            {
                "Assignment Type": label,
                "Target": compact(target),
                "Assigned Value": compact(assignment),
            }
        )
    return rows


def build_qa_rows(
    room_rows: List[Dict[str, Any]],
    surface_rows: List[Dict[str, Any]],
    assignment_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """Create actionable QA checks for the model."""
    qa_rows = []

    if not room_rows:
        qa_rows.append(
            {
                "Severity": "HIGH",
                "Category": "Rooms",
                "Issue": "No readable room/area data found.",
                "Recommendation": "Check whether get_areas_list or get_room_data is available in this VE version.",
            }
        )

    for row in room_rows:
        area = row["Floor Area (m2)"]
        if area <= 0:
            qa_rows.append(
                {
                    "Severity": "HIGH",
                    "Category": "Room Area",
                    "Issue": f"{row['Room Name']} has zero or missing floor area.",
                    "Recommendation": "Review room geometry and room inclusion in floor area calculations.",
                }
            )
        elif area < MIN_ROOM_AREA_M2:
            qa_rows.append(
                {
                    "Severity": "MEDIUM",
                    "Category": "Room Area",
                    "Issue": f"{row['Room Name']} has very small area ({area} m2).",
                    "Recommendation": "Check for sliver rooms, modelling fragments, or accidental spaces.",
                }
            )
        elif area > HIGH_ROOM_AREA_M2:
            qa_rows.append(
                {
                    "Severity": "LOW",
                    "Category": "Room Area",
                    "Issue": f"{row['Room Name']} is very large ({area} m2).",
                    "Recommendation": "Confirm zoning granularity is appropriate for simulation and HVAC analysis.",
                }
            )

    missing_construction = [
        row for row in surface_rows if row["Construction"] in ("", "Unknown", "None")
    ]
    if missing_construction:
        qa_rows.append(
            {
                "Severity": "HIGH",
                "Category": "Envelope",
                "Issue": f"{len(missing_construction)} surfaces have no readable construction assignment.",
                "Recommendation": "Review construction assignments before running compliance or energy simulations.",
            }
        )

    high_wwr = [row for row in surface_rows if row["Opening Ratio (%)"] > HIGH_WWR_PERCENT]
    if high_wwr:
        qa_rows.append(
            {
                "Severity": "MEDIUM",
                "Category": "Envelope",
                "Issue": f"{len(high_wwr)} surfaces have opening ratio above {HIGH_WWR_PERCENT:.0f}%.",
                "Recommendation": "Check glazing proportions, solar gains, daylighting assumptions, and overheating risk.",
            }
        )

    if not assignment_rows:
        qa_rows.append(
            {
                "Severity": "MEDIUM",
                "Category": "Assignments",
                "Issue": "No readable construction/profile assignment data was returned.",
                "Recommendation": "Use the API Diagnostics sheet to check available assignment methods.",
            }
        )

    if not qa_rows:
        qa_rows.append(
            {
                "Severity": "INFO",
                "Category": "Model QA",
                "Issue": "No major automated QA issues detected by this dashboard.",
                "Recommendation": "Continue with manual engineering review of templates, HVAC systems, schedules, and results.",
            }
        )

    return qa_rows


def make_formats(workbook: Any) -> Dict[str, Any]:
    """Create workbook formats."""
    navy = "#17365D"
    blue = "#D9EAF7"
    green = "#DDEBDA"
    amber = "#FCE4D6"
    red = "#F4CCCC"
    grey = "#E7E6E6"

    return {
        "title": workbook.add_format(
            {"bold": True, "font_size": 22, "font_color": navy}
        ),
        "subtitle": workbook.add_format(
            {"italic": True, "font_size": 10, "font_color": "#595959"}
        ),
        "section": workbook.add_format(
            {
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": navy,
                "align": "center",
                "valign": "vcenter",
                "border": 1,
            }
        ),
        "kpi_label": workbook.add_format(
            {"bold": True, "bg_color": blue, "border": 1, "align": "center"}
        ),
        "kpi_value": workbook.add_format(
            {"bold": True, "font_size": 16, "border": 1, "align": "center"}
        ),
        "header": workbook.add_format(
            {
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": navy,
                "border": 1,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
            }
        ),
        "text": workbook.add_format({"border": 1}),
        "num": workbook.add_format({"border": 1, "num_format": "0.00"}),
        "pct": workbook.add_format({"border": 1, "num_format": "0.0"}),
        "note": workbook.add_format(
            {"italic": True, "font_color": "#595959", "font_size": 9}
        ),
        "high": workbook.add_format({"bg_color": red, "border": 1, "bold": True}),
        "medium": workbook.add_format({"bg_color": amber, "border": 1, "bold": True}),
        "low": workbook.add_format({"bg_color": green, "border": 1, "bold": True}),
        "info": workbook.add_format({"bg_color": grey, "border": 1, "bold": True}),
    }


def write_metadata(ws: Any, formats: Dict[str, Any], project: Any) -> None:
    """Write dashboard title and metadata."""
    ws.merge_range("A1:H1", "IESVE Model Intelligence Dashboard", formats["title"])
    ws.merge_range(
        "A2:H2",
        "Automated model audit, geometry intelligence, and QA summary",
        formats["subtitle"],
    )
    ws.write("A4", "Project", formats["kpi_label"])
    ws.write("B4", get_project_name(project), formats["text"])
    ws.write("A5", "Generated", formats["kpi_label"])
    ws.write("B5", datetime.now().strftime("%Y-%m-%d %H:%M"), formats["text"])
    ws.write("A6", "Project Path", formats["kpi_label"])
    ws.write("B6", get_project_path(project), formats["text"])


def write_dashboard_sheet(
    workbook: Any,
    project: Any,
    room_rows: List[Dict[str, Any]],
    surface_rows: List[Dict[str, Any]],
    qa_rows: List[Dict[str, str]],
) -> None:
    """Write executive dashboard with KPI cards and charts."""
    formats = make_formats(workbook)
    ws = workbook.add_worksheet("Dashboard")
    write_metadata(ws, formats, project)

    total_area = sum(row["Floor Area (m2)"] for row in room_rows)
    total_surface_area = sum(row["Area (m2)"] for row in surface_rows)
    total_opening_area = sum(row["Opening Area (m2)"] for row in surface_rows)
    avg_room_area = total_area / len(room_rows) if room_rows else 0.0
    high_qa = sum(1 for row in qa_rows if row["Severity"] == "HIGH")

    kpis = [
        ("Rooms", len(room_rows)),
        ("Floor Area m2", round(total_area, 1)),
        ("Avg Room m2", round(avg_room_area, 1)),
        ("Surfaces", len(surface_rows)),
        ("Envelope m2", round(total_surface_area, 1)),
        ("Opening m2", round(total_opening_area, 1)),
        ("QA Issues", len(qa_rows)),
        ("High Risk", high_qa),
    ]

    start_col = 0
    for index, (label, value) in enumerate(kpis):
        col = start_col + index
        ws.write(8, col, label, formats["kpi_label"])
        ws.write(9, col, value, formats["kpi_value"])
        ws.set_column(col, col, 14)

    ws.merge_range("A12:D12", "Model Health Summary", formats["section"])
    ws.write("A14", "Automated interpretation", formats["header"])
    interpretation = build_interpretation(room_rows, surface_rows, qa_rows)
    ws.merge_range("A15:D20", interpretation, formats["text"])

    ws.merge_range("F12:H12", "Top QA Actions", formats["section"])
    ws.write_row("F14", ["Severity", "Issue", "Recommendation"], formats["header"])
    for index, row in enumerate(qa_rows[:6], start=14):
        severity_format = severity_format_for(formats, row["Severity"])
        ws.write(index, 5, row["Severity"], severity_format)
        ws.write(index, 6, row["Issue"], formats["text"])
        ws.write(index, 7, row["Recommendation"], formats["text"])

    write_dashboard_charts(workbook, ws, room_rows, surface_rows)
    ws.set_row(0, 30)
    ws.set_column("A:H", 18)
    ws.set_column("G:H", 42)


def build_interpretation(
    room_rows: List[Dict[str, Any]],
    surface_rows: List[Dict[str, Any]],
    qa_rows: List[Dict[str, str]],
) -> str:
    """Create a concise engineering interpretation."""
    total_area = sum(row["Floor Area (m2)"] for row in room_rows)
    high_qa = sum(1 for row in qa_rows if row["Severity"] == "HIGH")
    medium_qa = sum(1 for row in qa_rows if row["Severity"] == "MEDIUM")
    opening_area = sum(row["Opening Area (m2)"] for row in surface_rows)
    surface_area = sum(row["Area (m2)"] for row in surface_rows)
    wwr = opening_area / surface_area * 100.0 if surface_area > 0 else 0.0

    return (
        f"The model contains {len(room_rows)} readable rooms with "
        f"{total_area:.1f} m2 total floor area. The readable envelope dataset "
        f"contains {len(surface_rows)} surfaces with an aggregate opening ratio "
        f"of {wwr:.1f}%. The automated QA pass identified {high_qa} high-risk "
        f"items and {medium_qa} medium-risk items. Review high-risk items before "
        "using the model for compliance, sizing, or client-facing reporting."
    )


def write_dashboard_charts(
    workbook: Any,
    ws: Any,
    room_rows: List[Dict[str, Any]],
    surface_rows: List[Dict[str, Any]],
) -> None:
    """Create small chart data blocks and charts for dashboard rendering."""
    area_bands = Counter()
    for row in room_rows:
        area = row["Floor Area (m2)"]
        if area <= 0:
            area_bands["Missing/zero"] += 1
        elif area < 10:
            area_bands["0-10"] += 1
        elif area < 25:
            area_bands["10-25"] += 1
        elif area < 50:
            area_bands["25-50"] += 1
        elif area < 100:
            area_bands["50-100"] += 1
        else:
            area_bands[">100"] += 1

    ws.write_row("J2", ["Area Band", "Rooms"])
    for index, key in enumerate(["Missing/zero", "0-10", "10-25", "25-50", "50-100", ">100"], start=2):
        ws.write(index, 9, key)
        ws.write(index, 10, area_bands.get(key, 0))

    chart = workbook.add_chart({"type": "column"})
    chart.add_series(
        {
            "name": "Rooms by Area Band",
            "categories": ["Dashboard", 2, 9, 7, 9],
            "values": ["Dashboard", 2, 10, 7, 10],
            "fill": {"color": "#5B9BD5"},
        }
    )
    chart.set_title({"name": "Rooms by Area Band"})
    chart.set_legend({"none": True})
    chart.set_size({"width": 440, "height": 260})
    ws.insert_chart("A23", chart)

    surface_types = Counter(row["Surface Type"] for row in surface_rows)
    ws.write_row("M2", ["Surface Type", "Count"])
    for index, (key, count) in enumerate(surface_types.most_common(8), start=2):
        ws.write(index, 12, key)
        ws.write(index, 13, count)

    if surface_types:
        pie = workbook.add_chart({"type": "doughnut"})
        last_surface_row = 1 + min(len(surface_types), 8)
        pie.add_series(
            {
                "name": "Surface Types",
                "categories": ["Dashboard", 2, 12, last_surface_row, 12],
                "values": ["Dashboard", 2, 13, last_surface_row, 13],
            }
        )
        pie.set_title({"name": "Surface Type Mix"})
        pie.set_size({"width": 440, "height": 260})
        ws.insert_chart("F23", pie)

    ws.set_column("J:N", 14, None, {"hidden": True})


def severity_format_for(formats: Dict[str, Any], severity: str) -> Any:
    """Return a severity-specific format."""
    return {
        "HIGH": formats["high"],
        "MEDIUM": formats["medium"],
        "LOW": formats["low"],
        "INFO": formats["info"],
    }.get(severity, formats["text"])


def write_table_sheet(
    workbook: Any,
    sheet_name: str,
    columns: List[str],
    rows: List[Dict[str, Any]],
    numeric_columns: Optional[Iterable[str]] = None,
) -> None:
    """Write a formatted table-like worksheet."""
    formats = make_formats(workbook)
    numeric = set(numeric_columns or [])
    ws = workbook.add_worksheet(sheet_name)

    for col, header in enumerate(columns):
        ws.write(0, col, header, formats["header"])

    for row_index, row in enumerate(rows, start=1):
        for col, header in enumerate(columns):
            value = row.get(header, "")
            fmt = formats["num"] if header in numeric else formats["text"]
            ws.write(row_index, col, value, fmt)

    ws.freeze_panes(1, 0)
    ws.autofilter(0, 0, max(len(rows), 1), len(columns) - 1)
    for col, header in enumerate(columns):
        width = min(max(len(header) + 4, 16), 48)
        ws.set_column(col, col, width)


def write_qa_sheet(workbook: Any, qa_rows: List[Dict[str, str]]) -> None:
    """Write QA sheet with severity styling."""
    formats = make_formats(workbook)
    ws = workbook.add_worksheet("QA Action List")
    columns = ["Severity", "Category", "Issue", "Recommendation"]
    for col, header in enumerate(columns):
        ws.write(0, col, header, formats["header"])

    for row_index, row in enumerate(qa_rows, start=1):
        ws.write(row_index, 0, row["Severity"], severity_format_for(formats, row["Severity"]))
        ws.write(row_index, 1, row["Category"], formats["text"])
        ws.write(row_index, 2, row["Issue"], formats["text"])
        ws.write(row_index, 3, row["Recommendation"], formats["text"])

    ws.freeze_panes(1, 0)
    ws.autofilter(0, 0, max(len(qa_rows), 1), len(columns) - 1)
    ws.set_column("A:A", 14)
    ws.set_column("B:B", 20)
    ws.set_column("C:D", 70)


def write_report(
    output_path: str,
    project: Any,
    room_rows: List[Dict[str, Any]],
    surface_rows: List[Dict[str, Any]],
    assignment_rows: List[Dict[str, str]],
    qa_rows: List[Dict[str, str]],
    diagnostics: List[Dict[str, str]],
) -> None:
    """Write the full workbook."""
    workbook = xlsxwriter.Workbook(output_path)

    write_dashboard_sheet(workbook, project, room_rows, surface_rows, qa_rows)
    write_table_sheet(
        workbook,
        "Rooms",
        ["Room ID", "Room Name", "Body", "Floor Area (m2)", "Source"],
        room_rows,
        numeric_columns=["Floor Area (m2)"],
    )
    write_table_sheet(
        workbook,
        "Envelope",
        [
            "Surface Name",
            "Room Name",
            "Surface Type",
            "Construction",
            "Area (m2)",
            "Opening Area (m2)",
            "Opening Ratio (%)",
        ],
        surface_rows,
        numeric_columns=["Area (m2)", "Opening Area (m2)", "Opening Ratio (%)"],
    )
    write_table_sheet(
        workbook,
        "Assignments",
        ["Assignment Type", "Target", "Assigned Value"],
        assignment_rows,
    )
    write_qa_sheet(workbook, qa_rows)
    write_table_sheet(
        workbook,
        "API Diagnostics",
        ["API Object", "Method", "Available", "Status", "Return Type", "Message"],
        diagnostics,
    )

    workbook.close()


class DashboardWindow(tk.Frame):
    """Simple IESVE UI for generating the dashboard."""

    def __init__(self, master: tk.Tk, project: Any):
        """Initialize the dashboard window for the active VE project."""
        super().__init__(master)
        self.master = master
        self.project = project
        self.project_folder = get_project_path(project)
        self.master.title("IESVE Model Intelligence Dashboard")
        self.master.attributes("-topmost", True)
        self._init_window()

    def _init_window(self) -> None:
        """Create the Tkinter controls used by the dashboard UI."""
        self.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        ttk.Label(self, text="Create a model intelligence dashboard for the open VE project.").grid(
            row=0,
            column=0,
            columnspan=2,
            sticky=tk.W,
            pady=(0, 12),
        )

        ttk.Label(self, text="Save dashboard as:").grid(row=1, column=0, sticky=tk.W)
        self.output_entry = ttk.Entry(self, width=56)
        self.output_entry.insert(0, DEFAULT_OUTPUT_NAME)
        self.output_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 12))

        ttk.Button(self, text="Generate Dashboard", command=self.run).grid(
            row=3,
            column=0,
            sticky="e",
            padx=(0, 6),
        )
        ttk.Button(self, text="Cancel", command=self.master.destroy).grid(
            row=3,
            column=1,
            sticky="w",
        )

    def run(self) -> None:
        """Generate the legacy model-intelligence dashboard workbook."""
        output_name = self.output_entry.get().strip() or DEFAULT_OUTPUT_NAME
        if not output_name.lower().endswith(".xlsx"):
            output_name += ".xlsx"
        output_path = os.path.join(self.project_folder, output_name)

        try:
            room_rows = collect_room_rows(self.project)
            surface_rows = collect_surface_rows(self.project)
            assignment_rows = []
            assignment_rows.extend(
                collect_assignment_rows(
                    self.project,
                    "get_assigned_constructions_list",
                    "Construction",
                )
            )
            assignment_rows.extend(
                collect_assignment_rows(
                    self.project,
                    "get_assigned_profiles_list",
                    "Profile or Template",
                )
            )
            qa_rows = build_qa_rows(room_rows, surface_rows, assignment_rows)
            diagnostics = collect_api_diagnostics(self.project)

            write_report(
                output_path,
                self.project,
                room_rows,
                surface_rows,
                assignment_rows,
                qa_rows,
                diagnostics,
            )
        except PermissionError as exc:
            messagebox.showerror(
                "File error",
                f"Could not save the dashboard. Close the Excel file if it is open.\n\n{exc}",
            )
            return
        except Exception as exc:
            messagebox.showerror("Dashboard error", str(exc))
            return

        messagebox.showinfo("Dashboard created", f"Saved dashboard:\n{output_path}")
        try:
            os.startfile(output_path)
        except Exception:
            pass
        self.master.destroy()


def main() -> None:
    """Launch the dashboard tool from IESVE."""
    project = iesve.VEProject.get_current_project()
    if project is None:
        raise DashboardError("No IESVE project is currently open.")

    root = tk.Tk()
    DashboardWindow(root, project)
    root.mainloop()


if __name__ == "__main__":
    main()
