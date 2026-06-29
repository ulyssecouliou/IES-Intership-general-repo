"""
Lecture robuste des resultats Apache/Vista APS via l'API IESVE.

Ce module isole les patterns critiques de `iesve.ResultsReader` pour eviter
les erreurs classiques dans les scripts VE:
- ouvrir un APS par nom de fichier, pas par chemin complet;
- utiliser les `aps_varname` decouverts via `get_variables()`;
- convertir les tableaux numpy avec `.tolist()`;
- convertir les pas de temps en heures avec `results_per_day / 24`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple


@dataclass
class RoomDynamicResult:
    room_name: str
    room_id: Any
    area_m2: float
    heating_kwh: Optional[float] = None
    cooling_kwh: Optional[float] = None
    peak_heating_w: Optional[float] = None
    peak_cooling_w: Optional[float] = None
    occupied_hours_above_26: Optional[float] = None
    occupied_hours_above_27: Optional[float] = None
    source_notes: str = ""


def list_aps_files(project: Any) -> List[str]:
    """Retourne les fichiers APS disponibles dans le dossier Vista du projet."""
    vista_path = os.path.join(str(getattr(project, "path", "") or ""), "Vista")
    try:
        return sorted(name for name in os.listdir(vista_path) if name.lower().endswith(".aps"))
    except Exception:
        return []


def open_results_reader(aps_file_name: str) -> Any:
    """Ouvre un fichier APS avec le pattern documente IESVE."""
    import iesve

    return iesve.ResultsReader.open(aps_file_name)


def series_to_list(series: Any) -> List[float]:
    """Convertit les formes usuelles IESVE/numpy en liste numerique."""
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
    """Retourne le nombre de valeurs de resultat par heure."""
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
    """Lit une serie de resultats piece avec la signature documentee."""
    vista_var = vista_var or aps_var
    try:
        return series_to_list(results_file.get_room_results(room_id, aps_var, vista_var, level))
    except Exception:
        return []


def get_available_variables(results_file: Any) -> List[Dict[str, Any]]:
    """Retourne les variables APS disponibles, sous forme de dictionnaires."""
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
    """Trouve une variable APS par mots-cles dans `aps_varname` ou `display_name`."""
    tokens = [token.lower() for token in required_tokens]
    for variable in variables:
        aps_name = str(variable.get("aps_varname") or variable.get("name") or "")
        display_name = str(variable.get("display_name") or aps_name)
        model_level = str(variable.get("model_level") or variable.get("level") or "")
        haystack = f"{aps_name} {display_name}".lower()
        if level and model_level and model_level != level:
            continue
        if all(token in haystack for token in tokens):
            return aps_name, display_name, model_level or (level or "z")
    return None


def integrate_positive_watts_to_kwh(values: List[float], results_per_hour: float) -> float:
    """Integre uniquement les puissances positives en kWh."""
    if not values or results_per_hour <= 0:
        return 0.0
    return sum(value for value in values if value > 0) / results_per_hour / 1000.0


def peak_positive(values: List[float]) -> Optional[float]:
    positives = [value for value in values if value > 0]
    return max(positives) if positives else None


def count_occupied_hours_above(
    temperatures: List[float],
    occupancy: List[float],
    threshold: float,
    results_per_hour: float,
) -> float:
    """Compte les heures occupees au-dessus d'un seuil de temperature."""
    if not temperatures or results_per_hour <= 0:
        return 0.0
    count = 0
    for index, temperature in enumerate(temperatures):
        occupied = index < len(occupancy) and occupancy[index] > 0
        if occupied and temperature > threshold:
            count += 1
    return count / results_per_hour


def collect_room_dynamic_results(results_file: Any) -> List[RoomDynamicResult]:
    """Collecte des indicateurs dynamiques de base par piece depuis un APS."""
    variables = get_available_variables(results_file)
    rph = get_results_per_hour(results_file)

    heating_var = find_aps_variable(variables, ("heating", "load"), "z")
    cooling_var = find_aps_variable(variables, ("cooling", "load"), "z")
    temp_var = find_aps_variable(variables, ("dry", "resultant", "temperature"), "z")
    occ_var = find_aps_variable(variables, ("number", "people"), "z")

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

        result.source_notes = "; ".join(notes)
        rows.append(result)

    return rows

