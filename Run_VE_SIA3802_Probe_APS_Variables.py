"""READ-ONLY probe: which .aps is selected, and what room variables it exposes.

Run this file from the IESVE Scripts window with the Run button, on the active
project. It performs NO mutation and NO simulation: it lists the project's .aps
files (newest first), opens the newest readable one, and prints its weather,
timestep, and the full variable list. It then checks whether the variables the
compliance audit needs — room air temperature, occupancy, heating and cooling
loads — are actually present.

Use it to tell apart the two reasons SIA3802_HOURLY_TEMPERATURES /
SIA3802_HEATING_COOLING_DEMANDS stay NOT_CHECKABLE:
  - the .aps has no such series (the ApacheSim run did not output them / the rooms
    are not conditioned or occupied) -> re-run the simulation with those outputs;
  - the series exist under names the adapter does not match -> a binding fix.
"""

from __future__ import annotations

import importlib
import json
import math
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


DIAGNOSTIC_VARIABLES = (
    "Room units heating load",
    "Room units steady state htg load",
    "Room heating load",
    "Room units cooling load",
    "Room cooling load",
    "Convective plant load",
    "Plant profile",
    "System occupied and available",
    "System operation and available",
    "Heating set point",
    "Conduction gain",
    "Conduction gain - external wall",
    "Conduction gain - roof",
    "Conduction gain - ground floor",
    "Conduction gain - external glazed",
    "Conduction gain - internal wall",
    "Conduction gain - ceiling",
    "Conduction gain - floor",
    "External conduction gain (clear field)",
    "External conduction gain (bridge)",
    "Infiltration",
    "Infiltration gain",
    "Casual gains",
    "Lighting gain",
    "Equipment gain",
    "People gain",
    "Window solar gains",
    "System plant etc. gains",
    "Air & furniture dynamics gain",
    "External ventilation rate",
    "Ventilation gain from ext air",
    "Aux mech vent",
    "Aux mech vent gain",
    "Aux mech vent temp",
    "Conditioned ventilation rate",
    "Conditioned ventilation gains",
    "HVAC ventilation rate",
    "ApSys air supply",
    "Natural vent",
    "Cooling vent",
    "MacroFlo external vent",
    "MacroFlo internal vent",
    "MacroFlo ext vent gain",
    "MacroFlo int vent gain",
    "MacroFlo ext vent lat gain",
    "MacroFlo int vent lat gain",
    "Room CO2 concentration",
)


def _exact_variable(variables, aps_name, level="z"):
    """Return one exact APS variable tuple without guessing its identity."""
    expected = aps_name.strip().lower()
    for variable in variables:
        if str(variable.get("aps_varname") or "").strip().lower() != expected:
            continue
        model_level = str(variable.get("model_level") or "").strip().lower()
        if model_level and model_level != level:
            continue
        return (
            str(variable.get("aps_varname") or ""),
            str(variable.get("display_name") or aps_name),
            model_level or level,
            str(variable.get("resolved_metric_unit") or ""),
            float(variable.get("resolved_metric_divisor") or 1.0),
            float(variable.get("resolved_metric_offset") or 0.0),
        )
    return None


def _series_summary(values, results_per_hour):
    """Summarize one APS series without copying its 17,520 values."""
    numeric = [
        float(value)
        for value in values
        if isinstance(value, (int, float)) and math.isfinite(float(value))
    ]
    if not numeric:
        return {"points": 0}
    nonzero = [value for value in numeric if abs(value) > 1e-9]
    positive = [value for value in numeric if value > 1e-9]
    negative = [value for value in numeric if value < -1e-9]
    return {
        "points": len(numeric),
        "minimum": min(numeric),
        "maximum": max(numeric),
        "mean": sum(numeric) / len(numeric),
        "active_mean": sum(nonzero) / len(nonzero) if nonzero else 0.0,
        "nonzero_hours": len(nonzero) / results_per_hour,
        "positive_hours": len(positive) / results_per_hour,
        "negative_hours": len(negative) / results_per_hour,
        "positive_sum": sum(positive),
        "negative_sum": sum(negative),
    }


def _correlation(left, right):
    """Return Pearson correlation for aligned finite APS values."""
    pairs = []
    for left_value, right_value in zip(left, right):
        try:
            x = float(left_value)
            y = float(right_value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(x) and math.isfinite(y):
            pairs.append((x, y))
    if len(pairs) < 2:
        return None
    mean_x = sum(item[0] for item in pairs) / len(pairs)
    mean_y = sum(item[1] for item in pairs) / len(pairs)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    denominator_x = sum((x - mean_x) ** 2 for x, _ in pairs)
    denominator_y = sum((y - mean_y) ** 2 for _, y in pairs)
    denominator = math.sqrt(denominator_x * denominator_y)
    return numerator / denominator if denominator > 0 else None


def _write_ventilation_diagnostic(sim, reader, variables, rooms, aps_name):
    """Read exact room ventilation/load series and write a compact JSON audit."""
    results_per_hour = sim.get_results_per_hour(reader)
    matches = {
        name: _exact_variable(variables, name)
        for name in DIAGNOSTIC_VARIABLES
    }
    report = {
        "schema_version": 1,
        "purpose": "Read-only APS ventilation/heating diagnostic",
        "aps_file": aps_name,
        "results_per_hour": results_per_hour,
        "variables": {},
        "rooms": [],
    }
    for name, variable in matches.items():
        report["variables"][name] = {
            "available": variable is not None,
            "display_name": variable[1] if variable else "",
            "model_level": variable[2] if variable else "",
            "metric_unit": variable[3] if variable else "",
        }

    for room in rooms:
        if isinstance(room, dict):
            room_name = room.get("name") or room.get("room_name") or "Unknown"
            room_id = room.get("id") or room.get("room_id")
        elif isinstance(room, (list, tuple)) and len(room) >= 2:
            room_name, room_id = room[0], room[1]
        else:
            continue
        series = {}
        summaries = {}
        for name, variable in matches.items():
            values = sim.read_metric_room_result(reader, room_id, variable)
            series[name] = values
            summaries[name] = _series_summary(values, results_per_hour)

        heating = series.get("Room units heating load", [])
        correlations = {}
        for name in DIAGNOSTIC_VARIABLES:
            if name in {"Room units heating load", "Heating set point"}:
                continue
            value = _correlation(heating, series.get(name, []))
            if value is not None:
                correlations[name] = value
        report["rooms"].append({
            "room_name": str(room_name),
            "room_id": str(room_id),
            "series": summaries,
            "heating_correlations": correlations,
        })

    output_dir = os.path.join(PROJECT_ROOT, "outputs")
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    output_path = os.path.join(output_dir, "sia3802_ventilation_aps_diagnostic.json")
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print("\n--- TARGETED VENTILATION / HEATING DIAGNOSTIC ---")
    print("  report:", output_path)
    for room in report["rooms"]:
        print("  room:", room["room_name"])
        for name in (
            "Room units heating load",
            "External ventilation rate",
            "Aux mech vent",
            "Conditioned ventilation rate",
            "HVAC ventilation rate",
            "MacroFlo external vent",
        ):
            summary = room["series"].get(name, {})
            print("    {:30s} points={} active_h={} max={}".format(
                name,
                summary.get("points", 0),
                summary.get("nonzero_hours", 0),
                summary.get("maximum"),
            ))
    return output_path

def run() -> None:
    try:
        import iesve  # type: ignore  # noqa: F401
    except Exception as exc:
        raise RuntimeError("Run this launcher inside IESVE VEScripts.") from exc

    sim = importlib.reload(importlib.import_module("swiss_sia.simulation_results"))

    project = __import__("iesve").VEProject.get_current_project()
    if not project:
        raise RuntimeError("Open a project first.")

    aps_files = sim.list_aps_files(project)
    print("=" * 78)
    print("READ-ONLY APS VARIABLE PROBE (no mutation, no simulation)")
    print("=" * 78)
    print("Project weather label:", getattr(project, "path", ""))
    print("APS files in Vista folder:", aps_files or "[]")
    if not aps_files:
        print("No .aps file found. Run ApacheSim on THIS project first.")
        print("=" * 78)
        return

    # Newest by modification time.
    def _mtime(name):
        try:
            return os.path.getmtime(sim.get_aps_path(project, name))
        except Exception:
            return 0.0
    newest = sorted(aps_files, key=_mtime, reverse=True)[0]
    path = sim.get_aps_path(project, newest)
    print("Newest .aps:", newest)
    print("  path:", path)
    print("  EPW references in bytes:", sim.extract_epw_references_from_aps(path))

    reader = sim.open_results_reader(newest)
    try:
        print("  reader weather_file:", getattr(reader, "weather_file", ""))
        try:
            print("  results_per_hour:", sim.get_results_per_hour(reader))
        except Exception as exc:
            print("  results_per_hour: <error>", exc)
        variables = sim.get_available_variables(reader)
        print("  variable count:", len(variables))
        print("\n--- ALL VARIABLES (aps_varname | display_name | units) ---")
        for v in variables:
            print("   {} | {} | {}".format(
                v.get("aps_varname"), v.get("display_name"),
                v.get("resolved_metric_unit") or v.get("units_type")))
        print("\n--- WHAT THE AUDIT NEEDS (find_aps_variable returns a tuple) ---")
        # The variables the real extractor looks up, with the exact tokens/levels
        # it uses in collect_room_dynamic_results.
        needed = {
            "temperature (dry resultant, z)": (("dry", "resultant", "temperature"), "z"),
            "occupancy (number people, z)": (("number", "people"), "z"),
            "heating load (room, heating)": None,   # via find_room_sensible_load_variable
            "cooling load (room, cooling)": None,
        }
        found = {}
        for label, spec in needed.items():
            if spec is None:
                mode = "heating" if "heating" in label else "cooling"
                m = sim.find_room_sensible_load_variable(variables, mode)
            else:
                tokens, level = spec
                m = sim.find_aps_variable(variables, tokens, level)
            found[label] = m
            if m:
                print("  {:34s}: FOUND -> aps={!r} display={!r} level={!r}".format(
                    label, m[0], m[1], m[2]))
            else:
                print("  {:34s}: NOT FOUND".format(label))

        print("\n--- ROOM LIST + SAMPLE READ (the real failure point) ---")
        try:
            room_list = reader.get_room_list()
            print("  get_room_list(): OK, {} room(s)".format(len(list(room_list))))
        except Exception as exc:
            room_list = []
            print("  get_room_list(): FAILED ->", exc)
        rooms = list(room_list)
        temp_var = found.get("temperature (dry resultant, z)")
        if rooms and temp_var:
            first = rooms[0]
            rid = first.get("id") if isinstance(first, dict) else (
                first[1] if isinstance(first, (list, tuple)) and len(first) >= 2 else first)
            print("  first room id:", rid)
            try:
                series = sim.read_metric_room_result(reader, rid, temp_var)
                series = list(series)
                print("  read temperature series length:", len(series),
                      "| sample:", series[:3])
            except Exception as exc:
                print("  read_metric_room_result FAILED ->", exc)

        _write_ventilation_diagnostic(
            sim,
            reader,
            variables,
            rooms,
            newest,
        )
    finally:
        try:
            reader.close()
        except Exception:
            pass
    print("=" * 78)


if __name__ == "__main__":
    run()
