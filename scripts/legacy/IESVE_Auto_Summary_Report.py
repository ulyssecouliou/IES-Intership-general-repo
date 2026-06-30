"""
IESVE Auto Summary Report
=========================

Generate an Excel summary report from an IESVE Apache/Vista APS result file.

The report includes:
    - Project name and generation date
    - Zone peak heating and cooling loads
    - Annual heating/cooling load energy estimated from load result series
    - Comfort hours above 26 degC and 27 degC, annual and occupied

Run this script from the IESVE Python scripting environment after running an
Apache simulation.
"""

from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

import iesve
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
import xlsxwriter


DEFAULT_OUTPUT_NAME = "IESVE_Auto_Summary_Report"
COMFORT_THRESHOLDS = (26.0, 27.0)

COOLING_LOAD_ALIASES = (
    "Cooling load",
    "Cooling Load",
    "Cooling load (W)",
    "Cooling Load (W)",
    "Cooling load [W]",
    "Cooling Load [W]",
    "Cooling",
    "Sensible cooling",
    "Sensible cooling load",
    "Sensible Cooling Load",
    "Room cooling load",
    "Room Cooling Load",
    "Room sensible cooling load",
    "Room Sensible Cooling Load",
    "Cooling plant sensible load",
    "Cooling Plant Sensible Load",
)

HEATING_LOAD_ALIASES = (
    "Heating load",
    "Heating Load",
    "Heating load (W)",
    "Heating Load (W)",
    "Heating load [W]",
    "Heating Load [W]",
    "Heating",
    "Sensible heating",
    "Sensible heating load",
    "Sensible Heating Load",
    "Room heating load",
    "Room Heating Load",
    "Room sensible heating load",
    "Room Sensible Heating Load",
    "Heating plant sensible load",
    "Heating Plant Sensible Load",
)

TEMPERATURE_RESULT = (
    "Comfort temperature",
    "Dry resultant temperature",
    "z",
)

OCCUPANCY_RESULT = (
    "Number of people",
    "Number of people",
    "z",
)


class ReportError(Exception):
    """Raised when the report cannot be generated safely."""


def safe_float(value: Any) -> Optional[float]:
    """Convert a value to float, returning None for non-numeric values."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def series_to_list(series: Any) -> List[float]:
    """Convert common IESVE result return shapes into a numeric list."""
    if series is None:
        return []

    if hasattr(series, "tolist"):
        try:
            series = series.tolist()
        except Exception:
            pass

    if isinstance(series, dict):
        for key in ("values", "data", "series", "result"):
            if key in series:
                return series_to_list(series[key])
        series = list(series.values())

    if isinstance(series, (list, tuple)):
        values = []
        for item in series:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                item = item[1]
            number = safe_float(item)
            if number is not None:
                values.append(number)
        return values

    number = safe_float(series)
    return [number] if number is not None else []


def describe_value(value: Any) -> str:
    """Return a compact description of an API return value for diagnostics."""
    if value is None:
        return "None"
    if isinstance(value, dict):
        return f"dict ({len(value)} keys)"
    if isinstance(value, (list, tuple)):
        return f"{type(value).__name__} ({len(value)} items)"
    if hasattr(value, "shape"):
        return f"{type(value).__name__} shape={getattr(value, 'shape', '')}"
    return type(value).__name__


def compact_json(value: Any, max_length: int = 500) -> str:
    """Serialize API return data into a short worksheet-safe string."""
    try:
        text = json.dumps(value, default=str, ensure_ascii=True)
    except Exception:
        text = str(value)
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text


def safe_call(method: Any, arg_patterns: Iterable[Tuple[Any, ...]]) -> Tuple[bool, Any, str]:
    """Try multiple call signatures and return the first successful result."""
    if not callable(method):
        return False, None, "method not available"

    last_error = ""
    for args in arg_patterns:
        try:
            return True, method(*args), ""
        except Exception as exc:
            last_error = str(exc)
    return False, None, last_error


def normalize_token(value: Any) -> str:
    """Normalize a label for robust APS variable matching."""
    text = str(value or "").strip().lower()
    for token in (" ", "_", "-", ".", "/", "\\", "(", ")", "[", "]"):
        text = text.replace(token, "")
    return text


def iter_text_values(value: Any) -> Iterable[str]:
    """Yield nested text values from common IESVE API return structures."""
    if value is None:
        return
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            for nested in iter_text_values(item):
                yield nested
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            for nested in iter_text_values(item):
                yield nested


def get_available_variable_names(results_file: Any) -> List[str]:
    """Read variable names exposed by the APS file when available."""
    method = getattr(results_file, "get_variables", None)
    ok, variables, _ = safe_call(method, ((),))
    if not ok:
        return []

    names = []
    seen = set()
    for name in iter_text_values(variables):
        clean_name = str(name).strip()
        key = normalize_token(clean_name)
        if not clean_name or key in seen:
            continue
        seen.add(key)
        names.append(clean_name)
    return names


def looks_like_cooling_variable(name: str) -> bool:
    """Return True when a variable name looks like a cooling load result."""
    norm = normalize_token(name)
    return (
        "cool" in norm
        and any(token in norm for token in ("load", "sensible", "w", "kw", "watts"))
        and not any(token in norm for token in ("energy", "meter", "source"))
    )


def looks_like_heating_variable(name: str) -> bool:
    """Return True when a variable name looks like a heating load result."""
    norm = normalize_token(name)
    return (
        ("heat" in norm or "heating" in norm)
        and any(token in norm for token in ("load", "sensible", "w", "kw", "watts"))
        and not any(token in norm for token in ("energy", "meter", "source"))
    )


def open_results_file(results_reader: Any, aps_file_name: str, aps_full_path: str):
    """Open a Vista APS file using the ResultsReader API available in IESVE."""
    try:
        return results_reader.open(aps_file_name)
    except Exception:
        return results_reader.open(aps_full_path)


def get_room_records(results_file: Any) -> List[Dict[str, Any]]:
    """Read room id, name, and floor area from the APS result file."""
    records = []
    geometry_area_map = get_geometry_area_map(results_file)
    try:
        room_list = results_file.get_room_list()
    except Exception as exc:
        raise ReportError(f"Could not read room list from APS file: {exc}") from exc

    for room in room_list:
        if isinstance(room, dict):
            room_name = room.get("name") or room.get("room_name") or "Unknown"
            room_id = room.get("id") or room.get("room_id")
            floor_area = safe_float(room.get("area") or room.get("floor_area"))
        elif isinstance(room, (list, tuple)) and len(room) >= 2:
            room_name = room[0]
            room_id = room[1]
            floor_area = safe_float(room[2]) if len(room) >= 3 else None
        else:
            continue

        if room_id is None:
            continue

        records.append(
            {
                "room_name": str(room_name),
                "room_id": room_id,
                "floor_area_m2": round(
                    floor_area
                    or geometry_area_map.get(str(room_id), 0.0)
                    or geometry_area_map.get(str(room_name), 0.0),
                    2,
                ),
            }
        )

    if not records:
        raise ReportError("No rooms were found in the selected APS file.")

    return records


def get_geometry_area_map(results_file: Any) -> Dict[str, float]:
    """Use documented room geometry details as a fallback source for floor area."""
    method = getattr(results_file, "get_room_geometry_details_list", None)
    ok, details, _ = safe_call(method, ((),))
    if not ok or not isinstance(details, list):
        return {}

    area_map = {}
    for item in details:
        if not isinstance(item, dict):
            continue
        room_id = item.get("id") or item.get("room_id") or item.get("handle")
        room_name = item.get("name") or item.get("room_name")
        area = safe_float(
            item.get("floor_area")
            or item.get("area")
            or item.get("floor_area_m2")
            or item.get("net_area")
        )
        if area is None:
            continue
        if room_id is not None:
            area_map[str(room_id)] = area
        if room_name is not None:
            area_map[str(room_name)] = area
    return area_map


def read_room_result(
    results_file: Any,
    room_id: Any,
    category: str,
    variable: Optional[str] = None,
    level: str = "z",
) -> List[float]:
    """Read a room result series using several IESVE result-reader signatures."""
    variable = variable or category
    method_names = (
        "get_room_results",
        "get_results",
        "get_room_series",
        "get_room_profile",
    )
    attempts = (
        (room_id, category, variable, level),
        (room_id, category, variable),
        (room_id, category, level),
        (room_id, category),
        (room_id, variable, level),
        (room_id, variable),
        (variable, room_id, level),
        (variable, room_id),
        (category, variable, room_id, level),
        (category, variable, room_id),
    )

    for method_name in method_names:
        method = getattr(results_file, method_name, None)
        if not callable(method):
            continue
        for args in attempts:
            try:
                values = series_to_list(method(*args))
                if values:
                    return values
            except Exception:
                continue

    return []


def read_first_available_series(
    results_file: Any,
    room_id: Any,
    aliases: Iterable[str],
) -> Tuple[List[float], str, int]:
    """Try a list of result variable names and return the first valid series."""
    for alias in aliases:
        categories = (
            alias,
            "Loads",
            "Load",
            "Room loads",
            "Room Loads",
            "Apache loads",
            "Apache Loads",
        )
        for category in categories:
            values = read_room_result(results_file, room_id, category, alias, "z")
            if values:
                return values, f"{category} / {alias}", len(values)

            values = read_room_result(results_file, room_id, alias, category, "z")
            if values:
                return values, f"{alias} / {category}", len(values)

    return [], "", 0


def find_load_series(
    results_file: Any,
    room_id: Any,
    load_type: str,
    available_variables: List[str],
) -> Tuple[List[float], str, int]:
    """Find heating or cooling load results using aliases and APS variables."""
    if load_type == "cooling":
        aliases = list(COOLING_LOAD_ALIASES)
        discovered = [
            name for name in available_variables if looks_like_cooling_variable(name)
        ]
    else:
        aliases = list(HEATING_LOAD_ALIASES)
        discovered = [
            name for name in available_variables if looks_like_heating_variable(name)
        ]

    existing = {normalize_token(alias) for alias in aliases}
    for name in discovered:
        key = normalize_token(name)
        if key not in existing:
            aliases.append(name)
            existing.add(key)

    return read_first_available_series(results_file, room_id, aliases)


def get_results_per_hour(results_file: Any) -> float:
    """Return result timesteps per hour from the APS metadata."""
    results_per_day = safe_float(getattr(results_file, "results_per_day", None))
    if results_per_day and results_per_day > 0:
        return results_per_day / 24.0
    return 1.0


def integrate_watts_to_kwh(values: List[float], results_per_hour: float) -> float:
    """Convert a load time series in W to annual absolute kWh."""
    if not values or results_per_hour <= 0:
        return 0.0
    return round(sum(abs(value) for value in values) / results_per_hour / 1000.0, 2)


def peak_magnitude(values: List[float]) -> float:
    """Return the peak absolute value from a result series."""
    if not values:
        return 0.0
    return round(max(abs(value) for value in values), 2)


def collect_api_inventory(results_file: Any) -> Tuple[List[Dict[str, str]], List[str]]:
    """Collect documented ResultsReader metadata without depending on one signature."""
    diagnostics = []
    warnings = []
    documented_methods = [
        ("get_units", ((),)),
        ("get_variables", ((),)),
        ("get_energy_uses", ((), ("",), ("all",))),
        ("get_energy_sources", ((), ("",), ("all",))),
        ("get_energy_meters", ((), ("",), ("all",))),
        ("get_room_geometry_details_list", ((),)),
        ("get_room_ids", ((),)),
        ("get_apache_systems_list", ((),)),
        ("get_peak_results", ((), ("",), ("all",))),
    ]

    for method_name, arg_patterns in documented_methods:
        method = getattr(results_file, method_name, None)
        ok, value, error = safe_call(method, arg_patterns)
        diagnostics.append(
            {
                "API Method": method_name,
                "Available": "YES" if callable(method) else "NO",
                "Call Status": "OK" if ok else "NOT USED",
                "Return": describe_value(value) if ok else "",
                "Preview": compact_json(value) if ok else "",
                "Message": error,
            }
        )
        if callable(method) and not ok:
            warnings.append(
                f"Documented method {method_name} is available but needs a "
                "different call signature for this result set."
            )

    return diagnostics, warnings


def collect_energy_api_rows(results_file: Any) -> List[Dict[str, str]]:
    """Collect available documented energy dictionaries into table rows."""
    rows = []
    energy_methods = [
        "get_energy_uses",
        "get_energy_sources",
        "get_energy_meters",
    ]

    for method_name in energy_methods:
        method = getattr(results_file, method_name, None)
        ok, value, _ = safe_call(method, ((), ("",), ("all",)))
        if not ok:
            continue

        if isinstance(value, dict):
            for key, item in value.items():
                rows.append(
                    {
                        "Source Method": method_name,
                        "Key": str(key),
                        "Value Type": describe_value(item),
                        "Value Preview": compact_json(item, 900),
                    }
                )
        elif isinstance(value, list):
            for index, item in enumerate(value):
                rows.append(
                    {
                        "Source Method": method_name,
                        "Key": str(index),
                        "Value Type": describe_value(item),
                        "Value Preview": compact_json(item, 900),
                    }
                )
        else:
            rows.append(
                {
                    "Source Method": method_name,
                    "Key": "",
                    "Value Type": describe_value(value),
                    "Value Preview": compact_json(value, 900),
                }
            )

    return rows


def collect_available_variable_rows(results_file: Any) -> List[Dict[str, str]]:
    """Build rows listing APS variables exposed by get_variables()."""
    rows = []
    for name in get_available_variable_names(results_file):
        if looks_like_cooling_variable(name):
            classification = "Cooling candidate"
        elif looks_like_heating_variable(name):
            classification = "Heating candidate"
        else:
            classification = ""
        rows.append(
            {
                "Variable Name": name,
                "Classification": classification,
            }
        )
    return rows


def calculate_comfort_metrics(
    temperatures: List[float],
    occupancy: List[float],
    results_per_hour: float,
) -> Dict[str, float]:
    """Calculate annual and occupied comfort hours above each threshold."""
    metrics = {}
    total_occupied_steps = 0

    for index, temperature in enumerate(temperatures):
        occupied = index < len(occupancy) and occupancy[index] > 0
        if occupied:
            total_occupied_steps += 1

    metrics["occupied_hours"] = round(total_occupied_steps / results_per_hour, 1)
    metrics["peak_occupied_temp_degC"] = 0.0

    for threshold in COMFORT_THRESHOLDS:
        annual_steps = 0
        occupied_steps = 0
        excess_degree_hours = 0.0

        for index, temperature in enumerate(temperatures):
            occupied = index < len(occupancy) and occupancy[index] > 0

            if temperature > threshold:
                annual_steps += 1
                if occupied:
                    occupied_steps += 1
                    excess_degree_hours += temperature - threshold

            if occupied and temperature > metrics["peak_occupied_temp_degC"]:
                metrics["peak_occupied_temp_degC"] = temperature

        label = str(int(threshold))
        metrics[f"annual_hours_above_{label}"] = round(
            annual_steps / results_per_hour,
            1,
        )
        metrics[f"occupied_hours_above_{label}"] = round(
            occupied_steps / results_per_hour,
            1,
        )
        metrics[f"excess_degree_hours_above_{label}"] = round(
            excess_degree_hours / results_per_hour,
            1,
        )

    metrics["peak_occupied_temp_degC"] = round(
        metrics["peak_occupied_temp_degC"],
        2,
    )
    return metrics


def build_zone_rows(results_file: Any) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Collect load, energy, and comfort metrics for every room in the APS file."""
    rows = []
    warnings = []
    results_per_hour = get_results_per_hour(results_file)
    available_variables = get_available_variable_names(results_file)

    for room in get_room_records(results_file):
        room_id = room["room_id"]

        cooling_values, cooling_source, cooling_series_length = find_load_series(
            results_file,
            room_id,
            "cooling",
            available_variables,
        )
        heating_values, heating_source, heating_series_length = find_load_series(
            results_file,
            room_id,
            "heating",
            available_variables,
        )

        temperatures = read_room_result(results_file, room_id, *TEMPERATURE_RESULT)
        occupancy = read_room_result(results_file, room_id, *OCCUPANCY_RESULT)

        if not cooling_values:
            warnings.append(f"No cooling load series found for {room['room_name']}.")
        if not heating_values:
            warnings.append(f"No heating load series found for {room['room_name']}.")
        if not temperatures:
            warnings.append(f"No comfort temperature series found for {room['room_name']}.")
        if not occupancy:
            warnings.append(f"No occupancy series found for {room['room_name']}.")

        comfort = calculate_comfort_metrics(
            temperatures,
            occupancy,
            results_per_hour,
        )

        area = room["floor_area_m2"]
        cooling_peak = peak_magnitude(cooling_values)
        heating_peak = peak_magnitude(heating_values)
        annual_cooling_kwh = integrate_watts_to_kwh(cooling_values, results_per_hour)
        annual_heating_kwh = integrate_watts_to_kwh(heating_values, results_per_hour)

        rows.append(
            {
                "Room Name": room["room_name"],
                "Room ID": room_id,
                "Floor Area (m2)": area,
                "Peak Cooling Load (W)": cooling_peak,
                "Peak Heating Load (W)": heating_peak,
                "Cooling Load Density (W/m2)": round(cooling_peak / area, 2)
                if area > 0 else 0.0,
                "Heating Load Density (W/m2)": round(heating_peak / area, 2)
                if area > 0 else 0.0,
                "Annual Cooling Load Energy (kWh)": annual_cooling_kwh,
                "Annual Heating Load Energy (kWh)": annual_heating_kwh,
                "Annual Total Load Energy (kWh)": round(
                    annual_cooling_kwh + annual_heating_kwh,
                    2,
                ),
                "Total Occupied Hours (h)": comfort["occupied_hours"],
                "Annual Hours > 26 degC": comfort["annual_hours_above_26"],
                "Occupied Hours > 26 degC": comfort["occupied_hours_above_26"],
                "Excess Degree-Hours > 26 degC": comfort[
                    "excess_degree_hours_above_26"
                ],
                "Annual Hours > 27 degC": comfort["annual_hours_above_27"],
                "Occupied Hours > 27 degC": comfort["occupied_hours_above_27"],
                "Excess Degree-Hours > 27 degC": comfort[
                    "excess_degree_hours_above_27"
                ],
                "Peak Occupied Temp (degC)": comfort["peak_occupied_temp_degC"],
                "Cooling Source": cooling_source,
                "Heating Source": heating_source,
                "Cooling Series Length": cooling_series_length,
                "Heating Series Length": heating_series_length,
            }
        )

    if available_variables:
        cooling_candidates = [
            name for name in available_variables if looks_like_cooling_variable(name)
        ]
        heating_candidates = [
            name for name in available_variables if looks_like_heating_variable(name)
        ]
        if cooling_candidates:
            warnings.append(
                "Cooling-like APS variables found: "
                + ", ".join(cooling_candidates[:20])
            )
        if heating_candidates:
            warnings.append(
                "Heating-like APS variables found: "
                + ", ".join(heating_candidates[:20])
            )
    else:
        warnings.append("get_variables() did not expose APS variable names.")

    return rows, warnings


def write_metadata(
    worksheet: Any,
    formats: Dict[str, Any],
    project: Any,
    aps_file_name: str,
    weather_file: str,
) -> None:
    """Write report title and project metadata."""
    worksheet.write(0, 0, "IESVE Summary Report", formats["title"])
    worksheet.write(
        1,
        0,
        "Zone loads, annual load energy, and comfort hours",
        formats["subtitle"],
    )
    worksheet.write(3, 0, "Project:", formats["label"])
    worksheet.write(3, 1, getattr(project, "name", "Unknown"))
    worksheet.write(4, 0, "Generated:", formats["label"])
    worksheet.write(4, 1, datetime.now().strftime("%Y-%m-%d %H:%M"))
    worksheet.write(5, 0, "Results file:", formats["label"])
    worksheet.write(5, 1, aps_file_name)
    worksheet.write(6, 0, "Weather file:", formats["label"])
    worksheet.write(6, 1, weather_file or "Not available")


def create_formats(workbook: Any) -> Dict[str, Any]:
    """Create workbook cell formats."""
    return {
        "title": workbook.add_format({"bold": True, "font_size": 16}),
        "subtitle": workbook.add_format(
            {"italic": True, "font_color": "#595959"}
        ),
        "label": workbook.add_format({"bold": True}),
        "header": workbook.add_format(
            {
                "bold": True,
                "bg_color": "#1F4E78",
                "font_color": "#FFFFFF",
                "border": 1,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
            }
        ),
        "section": workbook.add_format(
            {
                "bold": True,
                "bg_color": "#D9EAF7",
                "border": 1,
                "align": "center",
            }
        ),
        "text": workbook.add_format({"border": 1}),
        "number": workbook.add_format({"border": 1, "num_format": "0.00"}),
        "integer": workbook.add_format({"border": 1, "num_format": "0"}),
        "note": workbook.add_format(
            {"italic": True, "font_color": "#595959", "font_size": 9}
        ),
    }


def write_summary_sheet(
    workbook: Any,
    project: Any,
    aps_file_name: str,
    weather_file: str,
    rows: List[Dict[str, Any]],
) -> None:
    """Write the executive summary worksheet."""
    formats = create_formats(workbook)
    worksheet = workbook.add_worksheet("Summary")
    write_metadata(worksheet, formats, project, aps_file_name, weather_file)

    total_area = sum(row["Floor Area (m2)"] for row in rows)
    total_cooling = sum(row["Annual Cooling Load Energy (kWh)"] for row in rows)
    total_heating = sum(row["Annual Heating Load Energy (kWh)"] for row in rows)
    max_cooling = max((row["Peak Cooling Load (W)"] for row in rows), default=0.0)
    max_heating = max((row["Peak Heating Load (W)"] for row in rows), default=0.0)
    max_hours_26 = max((row["Occupied Hours > 26 degC"] for row in rows), default=0.0)
    max_hours_27 = max((row["Occupied Hours > 27 degC"] for row in rows), default=0.0)

    worksheet.merge_range("A9:C9", "Key Performance Indicators", formats["section"])
    headers = ("Metric", "Value", "Unit")
    for col, header in enumerate(headers):
        worksheet.write(9, col, header, formats["header"])

    summary_rows = (
        ("Zones analysed", len(rows), "count"),
        ("Total floor area", total_area, "m2"),
        ("Max cooling peak", max_cooling, "W"),
        ("Max heating peak", max_heating, "W"),
        ("Annual cooling load energy", total_cooling, "kWh"),
        ("Annual heating load energy", total_heating, "kWh"),
        ("Annual total load energy", total_cooling + total_heating, "kWh"),
        ("Highest occupied hours > 26 degC", max_hours_26, "h"),
        ("Highest occupied hours > 27 degC", max_hours_27, "h"),
    )

    for row_index, row_data in enumerate(summary_rows, start=10):
        worksheet.write(row_index, 0, row_data[0], formats["text"])
        worksheet.write(row_index, 1, row_data[1], formats["number"])
        worksheet.write(row_index, 2, row_data[2], formats["text"])

    worksheet.set_column("A:A", 34)
    worksheet.set_column("B:C", 18)


def write_zone_sheet(workbook: Any, rows: List[Dict[str, Any]]) -> None:
    """Write detailed zone results."""
    formats = create_formats(workbook)
    worksheet = workbook.add_worksheet("Zone Results")

    columns = [
        "Room Name",
        "Floor Area (m2)",
        "Peak Cooling Load (W)",
        "Peak Heating Load (W)",
        "Cooling Load Density (W/m2)",
        "Heating Load Density (W/m2)",
        "Annual Cooling Load Energy (kWh)",
        "Annual Heating Load Energy (kWh)",
        "Annual Total Load Energy (kWh)",
        "Total Occupied Hours (h)",
        "Annual Hours > 26 degC",
        "Occupied Hours > 26 degC",
        "Excess Degree-Hours > 26 degC",
        "Annual Hours > 27 degC",
        "Occupied Hours > 27 degC",
        "Excess Degree-Hours > 27 degC",
        "Peak Occupied Temp (degC)",
        "Cooling Source",
        "Heating Source",
        "Cooling Series Length",
        "Heating Series Length",
    ]

    for col, header in enumerate(columns):
        worksheet.write(0, col, header, formats["header"])

    for row_index, data in enumerate(rows, start=1):
        for col, header in enumerate(columns):
            value = data.get(header, "")
            cell_format = formats["text"] if isinstance(value, str) else formats["number"]
            worksheet.write(row_index, col, value, cell_format)

    worksheet.freeze_panes(1, 1)
    worksheet.autofilter(0, 0, len(rows), len(columns) - 1)
    worksheet.set_column("A:A", 38)
    worksheet.set_column("B:Q", 15)
    worksheet.set_column("R:S", 30)
    worksheet.set_column("T:U", 16)


def write_notes_sheet(workbook: Any, warnings: List[str]) -> None:
    """Write assumptions, API notes, and warnings."""
    formats = create_formats(workbook)
    worksheet = workbook.add_worksheet("Notes")

    notes = [
        "API method used: ResultsReader.open(...) and get_room_results(...).",
        "Room list source: APS get_room_list().",
        "Comfort temperature source: Comfort temperature / Dry resultant temperature / z.",
        "Occupancy source: Number of people / Number of people / z.",
        "Load energy is calculated by integrating load series in W to kWh.",
        "If a source result is unavailable in the APS file, the corresponding value is set to zero.",
        "Check result variable names if heating or cooling loads appear as zero.",
    ]

    worksheet.write(0, 0, "Report Notes", formats["title"])
    for row_index, note in enumerate(notes, start=2):
        worksheet.write(row_index, 0, note, formats["note"])

    if warnings:
        start_row = len(notes) + 4
        worksheet.write(start_row, 0, "Warnings", formats["label"])
        for row_index, warning in enumerate(warnings, start=start_row + 1):
            worksheet.write(row_index, 0, warning, formats["note"])

    worksheet.set_column("A:A", 120)


def write_api_inventory_sheet(
    workbook: Any,
    diagnostics: List[Dict[str, str]],
) -> None:
    """Write documented API method diagnostics and previews."""
    formats = create_formats(workbook)
    worksheet = workbook.add_worksheet("API Inventory")
    columns = ["API Method", "Available", "Call Status", "Return", "Preview", "Message"]

    for col, header in enumerate(columns):
        worksheet.write(0, col, header, formats["header"])

    for row_index, row in enumerate(diagnostics, start=1):
        for col, header in enumerate(columns):
            worksheet.write(row_index, col, row.get(header, ""), formats["text"])

    worksheet.freeze_panes(1, 0)
    worksheet.autofilter(0, 0, len(diagnostics), len(columns) - 1)
    worksheet.set_column("A:A", 28)
    worksheet.set_column("B:D", 16)
    worksheet.set_column("E:E", 80)
    worksheet.set_column("F:F", 50)


def write_energy_api_sheet(workbook: Any, rows: List[Dict[str, str]]) -> None:
    """Write raw documented energy API data when available."""
    formats = create_formats(workbook)
    worksheet = workbook.add_worksheet("Energy API Data")
    columns = ["Source Method", "Key", "Value Type", "Value Preview"]

    for col, header in enumerate(columns):
        worksheet.write(0, col, header, formats["header"])

    if not rows:
        worksheet.write(
            1,
            0,
            "No energy API dictionary could be read with the generic signatures.",
            formats["note"],
        )
    else:
        for row_index, row in enumerate(rows, start=1):
            for col, header in enumerate(columns):
                worksheet.write(row_index, col, row.get(header, ""), formats["text"])

    worksheet.freeze_panes(1, 0)
    worksheet.autofilter(0, 0, max(len(rows), 1), len(columns) - 1)
    worksheet.set_column("A:A", 24)
    worksheet.set_column("B:B", 28)
    worksheet.set_column("C:C", 18)
    worksheet.set_column("D:D", 110)


def write_available_variables_sheet(
    workbook: Any,
    rows: List[Dict[str, str]],
) -> None:
    """Write APS variable names found via get_variables()."""
    formats = create_formats(workbook)
    worksheet = workbook.add_worksheet("Available Variables")
    columns = ["Variable Name", "Classification"]

    for col, header in enumerate(columns):
        worksheet.write(0, col, header, formats["header"])

    if not rows:
        worksheet.write(
            1,
            0,
            "get_variables() did not return a readable variable list.",
            formats["note"],
        )
    else:
        for row_index, row in enumerate(rows, start=1):
            for col, header in enumerate(columns):
                worksheet.write(row_index, col, row.get(header, ""), formats["text"])

    worksheet.freeze_panes(1, 0)
    worksheet.autofilter(0, 0, max(len(rows), 1), len(columns) - 1)
    worksheet.set_column("A:A", 70)
    worksheet.set_column("B:B", 24)


def write_excel_report(
    output_path: str,
    project: Any,
    aps_file_name: str,
    weather_file: str,
    rows: List[Dict[str, Any]],
    warnings: List[str],
    diagnostics: List[Dict[str, str]],
    energy_api_rows: List[Dict[str, str]],
    variable_rows: List[Dict[str, str]],
) -> None:
    """Create the final Excel workbook."""
    workbook = xlsxwriter.Workbook(output_path)
    write_summary_sheet(workbook, project, aps_file_name, weather_file, rows)
    write_zone_sheet(workbook, rows)
    write_api_inventory_sheet(workbook, diagnostics)
    write_energy_api_sheet(workbook, energy_api_rows)
    write_available_variables_sheet(workbook, variable_rows)
    write_notes_sheet(workbook, warnings)
    workbook.close()


class SummaryReportWindow(tk.Frame):
    """Small IESVE UI for selecting an APS file and creating the report."""

    def __init__(self, master: tk.Tk, project: Any, results_reader: Any):
        super().__init__(master)
        self.master = master
        self.project = project
        self.results_reader = results_reader
        self.project_folder = project.path
        self.vista_folder = os.path.join(project.path, "Vista")
        self.master.title("IESVE Auto Summary Report")
        self.master.attributes("-topmost", True)
        self._init_window()

    def _init_window(self) -> None:
        self.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ttk.Label(self, text="Select a Vista Results File (.aps):").grid(
            row=0,
            column=0,
            sticky=tk.W,
        )

        aps_files = self._get_aps_files()
        self.listbox = tk.Listbox(self, height=8, width=60)
        for aps_file in aps_files:
            self.listbox.insert(tk.END, aps_file)
        if aps_files:
            self.listbox.select_set(0)
        self.listbox.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(5, 15))

        ttk.Label(self, text="Save report as:").grid(row=2, column=0, sticky=tk.W)
        self.output_entry = ttk.Entry(self, width=60)
        self.output_entry.insert(0, DEFAULT_OUTPUT_NAME)
        self.output_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 15))

        ttk.Button(self, text="Generate Report", command=self.run_report).grid(
            row=4,
            column=0,
            sticky="e",
            padx=(0, 5),
        )
        ttk.Button(self, text="Cancel", command=self.master.destroy).grid(
            row=4,
            column=1,
            sticky="w",
        )

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

    def _get_aps_files(self) -> List[str]:
        try:
            files = os.listdir(self.vista_folder)
        except FileNotFoundError:
            messagebox.showerror(
                "Vista folder not found",
                f"Could not find Vista folder:\n{self.vista_folder}",
            )
            return []
        return sorted(file_name for file_name in files if file_name.lower().endswith(".aps"))

    def run_report(self) -> None:
        aps_file_name = self.listbox.get(tk.ACTIVE)
        if not aps_file_name:
            messagebox.showerror("No APS file", "Select an APS file first.")
            return

        output_name = self.output_entry.get().strip() or DEFAULT_OUTPUT_NAME
        if not output_name.lower().endswith(".xlsx"):
            output_name += ".xlsx"

        output_path = os.path.join(self.project_folder, output_name)
        aps_full_path = os.path.join(self.vista_folder, aps_file_name)

        try:
            results_file = open_results_file(
                self.results_reader,
                aps_file_name,
                aps_full_path,
            )
            weather_file = getattr(results_file, "weather_file", "")
            rows, warnings = build_zone_rows(results_file)
            diagnostics, api_warnings = collect_api_inventory(results_file)
            energy_api_rows = collect_energy_api_rows(results_file)
            variable_rows = collect_available_variable_rows(results_file)
            warnings.extend(api_warnings)
            write_excel_report(
                output_path,
                self.project,
                aps_file_name,
                weather_file,
                rows,
                warnings,
                diagnostics,
                energy_api_rows,
                variable_rows,
            )
        except PermissionError as exc:
            messagebox.showerror(
                "File error",
                f"Could not save the workbook. Close it if it is open.\n\n{exc}",
            )
            return
        except Exception as exc:
            messagebox.showerror("Report error", str(exc))
            return

        messagebox.showinfo("Report created", f"Saved report:\n{output_path}")
        try:
            os.startfile(output_path)
        except Exception:
            pass
        self.master.destroy()


def main() -> None:
    """Launch the summary report UI inside IESVE."""
    project = iesve.VEProject.get_current_project()
    if project is None:
        raise ReportError("No IESVE project is currently open.")

    root = tk.Tk()
    SummaryReportWindow(root, project, iesve.ResultsReader)
    root.mainloop()


if __name__ == "__main__":
    main()
