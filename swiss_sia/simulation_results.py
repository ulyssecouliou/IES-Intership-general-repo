"""Robust Apache/Vista APS result access through the IESVE API.

This module isolates the critical ``iesve.ResultsReader`` patterns needed by
the production VE Run-button workflow:

- open APS files by filename, not by full path;
- use ``aps_varname`` values discovered through ``get_variables()``;
- convert NumPy-like arrays with ``tolist()`` before iteration;
- convert timesteps to hours with ``results_per_day / 24``.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple


@dataclass
class RoomDynamicResult:
    """Normalized dynamic indicators extracted for one APS room."""

    room_name: str
    room_id: Any
    area_m2: float
    heating_kwh: Optional[float] = None
    cooling_kwh: Optional[float] = None
    lighting_kwh: Optional[float] = None
    fan_kwh: Optional[float] = None
    pump_kwh: Optional[float] = None
    auxiliary_kwh: Optional[float] = None
    coil_heating_kwh: Optional[float] = None
    coil_cooling_kwh: Optional[float] = None
    peak_heating_w: Optional[float] = None
    peak_cooling_w: Optional[float] = None
    peak_co2_ppm: Optional[float] = None
    average_co2_ppm: Optional[float] = None
    peak_relative_humidity_percent: Optional[float] = None
    average_relative_humidity_percent: Optional[float] = None
    occupied_hours_above_26: Optional[float] = None
    occupied_hours_above_27: Optional[float] = None
    source_notes: str = ""


def list_aps_files(project: Any) -> List[str]:
    """Return APS files available in the active project's Vista folder."""
    vista_path = os.path.join(str(getattr(project, "path", "") or ""), "Vista")
    try:
        return sorted(name for name in os.listdir(vista_path) if name.lower().endswith(".aps"))
    except Exception:
        return []


def get_aps_path(project: Any, aps_file_name: str) -> str:
    """Return the expected full path for an APS file in the project Vista folder."""
    return os.path.join(str(getattr(project, "path", "") or ""), "Vista", str(aps_file_name or ""))


def extract_epw_references_from_aps(aps_path: str, max_bytes: int = 8_000_000) -> List[str]:
    """Extract visible EPW filename references from an APS file without opening ResultsReader."""
    try:
        with open(aps_path, "rb") as handle:
            payload = handle.read(max_bytes)
    except Exception:
        return []

    text = payload.decode("latin-1", errors="ignore")
    matches = re.findall(r"[A-Za-z0-9_. ()\\/\-:]+\.epw", text, flags=re.IGNORECASE)
    references = []
    seen = set()
    for match in matches:
        cleaned = match.strip().strip("\x00\r\n\t ")
        # Keep the filename when binary noise precedes the path.
        basename = os.path.basename(cleaned.replace("\\", os.sep).replace("/", os.sep))
        value = basename or cleaned
        key = value.lower()
        if value and key not in seen:
            references.append(value)
            seen.add(key)
    return references


def open_results_reader(aps_file_name: str) -> Any:
    """Open an APS file using the documented IESVE filename-only pattern."""
    import iesve

    return iesve.ResultsReader.open(aps_file_name)


def series_to_list(series: Any) -> List[float]:
    """Convert common IESVE/NumPy result shapes to a numeric list."""
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
        values: List[float] = []
        for item in series:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                item = item[1]
            try:
                values.append(float(item))
            except (TypeError, ValueError):
                continue
        return values
    try:
        return [float(series)]
    except (TypeError, ValueError):
        return []


def get_results_per_hour(results_file: Any) -> float:
    """Return the number of result values per simulated hour."""
    try:
        results_per_day = float(getattr(results_file, "results_per_day", 24) or 24)
    except (TypeError, ValueError):
        results_per_day = 24.0
    return results_per_day / 24.0 if results_per_day > 0 else 1.0


def read_room_result(
    results_file: Any,
    room_id: Any,
    aps_var: str,
    vista_var: Optional[str] = None,
    level: str = "z",
) -> List[float]:
    """Read one room result series using the documented ResultsReader call."""
    vista_var = vista_var or aps_var
    try:
        return series_to_list(results_file.get_room_results(room_id, aps_var, vista_var, level))
    except Exception:
        return []


def get_available_variables(results_file: Any) -> List[Dict[str, Any]]:
    """Return available APS variables as dictionaries."""
    try:
        raw = results_file.get_variables()
    except Exception:
        return []
    variables: List[Dict[str, Any]] = []
    for item in raw or []:
        if isinstance(item, dict):
            variables.append(item)
    return variables


def find_aps_variable(
    variables: Iterable[Dict[str, Any]],
    required_tokens: Iterable[str],
    level: Optional[str] = None,
) -> Optional[Tuple[str, str, str]]:
    """Find an APS variable by tokens in ``aps_varname`` or ``display_name``."""
    matches = find_aps_variables(variables, required_tokens, level, max_matches=1)
    return matches[0] if matches else None


def find_aps_variables(
    variables: Iterable[Dict[str, Any]],
    required_tokens: Iterable[str],
    level: Optional[str] = None,
    max_matches: int = 8,
) -> List[Tuple[str, str, str]]:
    """Find APS variables by tokens in ``aps_varname`` or ``display_name``."""
    tokens = [token.lower() for token in required_tokens]
    expected_level = str(level or "").strip().lower()
    matches: List[Tuple[str, str, str]] = []
    seen = set()
    for variable in variables:
        aps_name = str(variable.get("aps_varname") or variable.get("name") or "")
        display_name = str(variable.get("display_name") or aps_name)
        model_level = str(variable.get("model_level") or variable.get("level") or "").strip().lower()
        haystack = f"{aps_name} {display_name}".lower()
        if expected_level and model_level and model_level != expected_level:
            continue
        if all(token in haystack for token in tokens):
            key = (aps_name, display_name, model_level or (expected_level or "z"))
            if key not in seen:
                matches.append(key)
                seen.add(key)
            if len(matches) >= max_matches:
                break
    return matches


def find_first_aps_variable(
    variables: Iterable[Dict[str, Any]],
    token_sets: Iterable[Iterable[str]],
    level: Optional[str] = None,
) -> Optional[Tuple[str, str, str]]:
    """Return the first APS variable matching one of several token sets."""
    for tokens in token_sets:
        match = find_aps_variable(variables, tokens, level)
        if match:
            return match
    return None


def result_label(aps_variable: Tuple[str, str, str]) -> str:
    """Return a readable label for a discovered APS variable."""
    aps_name, display_name, level = aps_variable
    label = display_name or aps_name
    return f"{label} [{aps_name}; level={level}]"


def integrate_positive_watts_to_kwh(values: List[float], results_per_hour: float) -> float:
    """Integrate positive power values from W timesteps to kWh."""
    if not values or results_per_hour <= 0:
        return 0.0
    return sum(value for value in values if value > 0) / results_per_hour / 1000.0


def integrate_positive_result_to_kwh(
    values: List[float],
    variable_label: str,
    results_per_hour: float,
) -> Optional[float]:
    """Integrate a positive APS result series to kWh with conservative unit handling."""
    positives = [value for value in values if value > 0]
    if not positives:
        return None

    label = variable_label.lower()
    if "kwh" in label:
        # Some APS channels are cumulative kWh, while others are timestep kWh.
        # Use the cumulative endpoint when the sequence is monotonic, otherwise
        # sum positive timestep values.
        is_monotonic = all(
            positives[index] >= positives[index - 1]
            for index in range(1, len(positives))
        )
        return max(positives) if is_monotonic else sum(positives)
    if re.search(r"\bwh\b", label):
        return sum(positives) / 1000.0
    return integrate_positive_watts_to_kwh(positives, results_per_hour)


def peak_positive(values: List[float]) -> Optional[float]:
    """Return the peak positive value, or ``None`` when no positive value exists."""

    positives = [value for value in values if value > 0]
    return max(positives) if positives else None


def average_positive(values: List[float]) -> Optional[float]:
    """Return the average of positive values, or ``None`` when none exists."""
    positives = [value for value in values if value > 0]
    return sum(positives) / len(positives) if positives else None


def read_optional_energy_result(
    results_file: Any,
    room_id: Any,
    aps_variable: Optional[Tuple[str, str, str]],
    results_per_hour: float,
) -> Tuple[Optional[float], str]:
    """Read and integrate one optional room energy or power result."""
    if not aps_variable:
        return None, ""
    values = read_room_result(results_file, room_id, *aps_variable)
    if not values:
        return None, f"{result_label(aps_variable)} found but returned no data"
    energy = integrate_positive_result_to_kwh(values, result_label(aps_variable), results_per_hour)
    return energy, result_label(aps_variable)


def read_optional_point_result(
    results_file: Any,
    room_id: Any,
    aps_variable: Optional[Tuple[str, str, str]],
) -> Tuple[Optional[float], Optional[float], str]:
    """Read peak and average positive values for an optional room result."""
    if not aps_variable:
        return None, None, ""
    values = read_room_result(results_file, room_id, *aps_variable)
    if not values:
        return None, None, f"{result_label(aps_variable)} found but returned no data"
    return peak_positive(values), average_positive(values), result_label(aps_variable)


def normalize_co2_series_to_ppm(values: List[float], variable_label: str) -> Tuple[List[float], str]:
    """Normalize common APS CO2 result units to ppm for report readability."""
    positives = [value for value in values if value > 0]
    if not positives:
        return [], ""

    label = variable_label.lower()
    peak_value = max(positives)
    if "ppm" in label:
        return positives, "ppm"
    if "%" in label or "percent" in label:
        return [value * 10_000.0 for value in positives], "converted from percent to ppm"
    if peak_value <= 0.02:
        return [value * 1_000_000.0 for value in positives], "converted from fraction to ppm"
    return positives, "assumed ppm"


def read_optional_co2_result(
    results_file: Any,
    room_id: Any,
    aps_variable: Optional[Tuple[str, str, str]],
) -> Tuple[Optional[float], Optional[float], str]:
    """Read an optional CO2 result and normalize it to ppm when units are inferable."""
    if not aps_variable:
        return None, None, ""
    label = result_label(aps_variable)
    values = read_room_result(results_file, room_id, *aps_variable)
    if not values:
        return None, None, f"{label} found but returned no data"
    normalized_values, unit_note = normalize_co2_series_to_ppm(values, label)
    if not normalized_values:
        return None, None, f"{label} found but returned no positive CO2 values"
    readable_label = f"{label}; {unit_note}" if unit_note else label
    return peak_positive(normalized_values), average_positive(normalized_values), readable_label


def count_occupied_hours_above(
    temperatures: List[float],
    occupancy: List[float],
    threshold: float,
    results_per_hour: float,
) -> float:
    """Count occupied hours above a temperature threshold."""
    if not temperatures or results_per_hour <= 0:
        return 0.0
    count = 0
    for index, temperature in enumerate(temperatures):
        occupied = index < len(occupancy) and occupancy[index] > 0
        if occupied and temperature > threshold:
            count += 1
    return count / results_per_hour


def collect_room_dynamic_results(results_file: Any) -> List[RoomDynamicResult]:
    """Collect basic room-level dynamic indicators from an APS results file."""
    variables = get_available_variables(results_file)
    rph = get_results_per_hour(results_file)

    heating_var = find_aps_variable(variables, ("heating", "load"), "z")
    cooling_var = find_aps_variable(variables, ("cooling", "load"), "z")
    temp_var = find_aps_variable(variables, ("dry", "resultant", "temperature"), "z")
    occ_var = find_aps_variable(variables, ("number", "people"), "z")
    lighting_var = find_first_aps_variable(
        variables,
        (
            ("lighting", "power"),
            ("lights", "power"),
            ("lighting", "electric"),
            ("lighting", "energy"),
        ),
        "z",
    )
    fan_var = find_first_aps_variable(
        variables,
        (
            ("fan", "power"),
            ("fans", "power"),
            ("fan", "electric"),
            ("fan", "energy"),
        ),
        "z",
    )
    pump_var = find_first_aps_variable(
        variables,
        (
            ("pump", "power"),
            ("pumps", "power"),
            ("pump", "electric"),
            ("pump", "energy"),
        ),
        "z",
    )
    auxiliary_var = find_first_aps_variable(
        variables,
        (
            ("auxiliary", "power"),
            ("auxiliary", "energy"),
            ("aux", "power"),
            ("aux", "energy"),
        ),
        "z",
    )
    heating_coil_var = find_first_aps_variable(
        variables,
        (
            ("heating", "coil"),
            ("reheat", "coil"),
            ("heater", "coil"),
            ("supply", "heating"),
        ),
        "z",
    )
    cooling_coil_var = find_first_aps_variable(
        variables,
        (
            ("cooling", "coil"),
            ("cooler", "coil"),
            ("supply", "cooling"),
        ),
        "z",
    )
    co2_var = find_first_aps_variable(
        variables,
        (
            ("co2",),
            ("carbon", "dioxide"),
        ),
        "z",
    )
    relative_humidity_var = find_first_aps_variable(
        variables,
        (
            ("relative", "humidity"),
            ("room", "humidity"),
        ),
        "z",
    )

    try:
        room_list = results_file.get_room_list()
    except Exception:
        return []

    rows: List[RoomDynamicResult] = []
    for room in room_list:
        if isinstance(room, dict):
            room_name = room.get("name") or room.get("room_name") or "Unknown"
            room_id = room.get("id") or room.get("room_id")
            area = float(room.get("area") or room.get("floor_area") or 0.0)
        elif isinstance(room, (list, tuple)) and len(room) >= 2:
            room_name = room[0]
            room_id = room[1]
            area = float(room[2]) if len(room) >= 3 and room[2] is not None else 0.0
        else:
            continue

        result = RoomDynamicResult(str(room_name), room_id, area)
        notes: List[str] = []

        if heating_var:
            values = read_room_result(results_file, room_id, *heating_var)
            result.heating_kwh = integrate_positive_watts_to_kwh(values, rph)
            result.peak_heating_w = peak_positive(values)
        else:
            notes.append("heating load variable not found")

        if cooling_var:
            values = read_room_result(results_file, room_id, *cooling_var)
            result.cooling_kwh = integrate_positive_watts_to_kwh(values, rph)
            result.peak_cooling_w = peak_positive(values)
        else:
            notes.append("cooling load variable not found")

        if temp_var and occ_var:
            temperatures = read_room_result(results_file, room_id, *temp_var)
            occupancy = read_room_result(results_file, room_id, *occ_var)
            result.occupied_hours_above_26 = count_occupied_hours_above(temperatures, occupancy, 26.0, rph)
            result.occupied_hours_above_27 = count_occupied_hours_above(temperatures, occupancy, 27.0, rph)
        else:
            notes.append("comfort or occupancy variable not found")

        optional_energy_vars = (
            ("lighting", lighting_var, "lighting result variable not found"),
            ("fan", fan_var, "fan result variable not found"),
            ("pump", pump_var, "pump result variable not found"),
            ("auxiliary", auxiliary_var, "auxiliary result variable not found"),
            ("heating coil", heating_coil_var, "heating coil result variable not found"),
            ("cooling coil", cooling_coil_var, "cooling coil result variable not found"),
        )
        for category, variable, missing_note in optional_energy_vars:
            energy, label = read_optional_energy_result(results_file, room_id, variable, rph)
            if category == "lighting":
                result.lighting_kwh = energy
            elif category == "fan":
                result.fan_kwh = energy
            elif category == "pump":
                result.pump_kwh = energy
            elif category == "auxiliary":
                result.auxiliary_kwh = energy
            elif category == "heating coil":
                result.coil_heating_kwh = energy
            elif category == "cooling coil":
                result.coil_cooling_kwh = energy
            if label and energy is not None:
                notes.append(f"{category}: {label}")
            elif label:
                notes.append(label)
            else:
                notes.append(missing_note)

        co2_peak, co2_average, co2_label = read_optional_co2_result(results_file, room_id, co2_var)
        result.peak_co2_ppm = co2_peak
        result.average_co2_ppm = co2_average
        if co2_label:
            notes.append(f"CO2: {co2_label}")
        else:
            notes.append("CO2 result variable not found")

        humidity_peak, humidity_average, humidity_label = read_optional_point_result(results_file, room_id, relative_humidity_var)
        result.peak_relative_humidity_percent = humidity_peak
        result.average_relative_humidity_percent = humidity_average
        if humidity_label:
            notes.append(f"relative humidity: {humidity_label}")
        else:
            notes.append("relative humidity result variable not found")

        result.source_notes = "; ".join(notes)
        rows.append(result)

    return rows
