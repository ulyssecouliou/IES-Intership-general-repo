"""Read-only VE runtime inventory used to qualify remediation warnings.

The functions in this module do not mutate VE objects.  They preserve the raw
read-back needed to distinguish a missing model input from an unsupported
normalization or an APS variable-binding gap.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


def json_safe(value: Any, *, depth: int = 0) -> Any:
    """Return a bounded JSON-safe representation of a VE API value."""
    if depth > 6:
        return str(value)
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return {
            str(key): json_safe(item, depth=depth + 1)
            for key, item in list(value.items())[:200]
        }
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item, depth=depth + 1) for item in list(value)[:200]]
    try:
        return json_safe(dict(value), depth=depth + 1)
    except Exception:
        return str(value)


def _child_data(item: Any) -> Dict[str, Any]:
    """Return the dictionary exposed by a VERoomData child object."""
    if isinstance(item, dict):
        return dict(item)
    try:
        data = item.get()
    except Exception as exc:
        return {"read_error": str(exc), "python_type": str(type(item))}
    if isinstance(data, dict):
        return data
    try:
        return dict(data)
    except Exception:
        return {"raw_value": str(data), "python_type": str(type(item))}


def collect_model_runtime_inventory(extractor: Any) -> Dict[str, Any]:
    """Collect raw gains, air exchanges, conditions and systems per room."""
    rooms: List[Dict[str, Any]] = []
    referenced_system_ids = set()
    for body in extractor.get_bodies():
        room_id = str(extractor.get_object_id(body) or "")
        room_name = ""
        try:
            properties = extractor._as_dict(body.get_properties())
            room_name = str(properties.get("name") or properties.get("id") or "")
        except Exception:
            room_name = room_id
        room_data = extractor.get_room_data(body)
        if room_data is None:
            rooms.append(
                {
                    "room_id": room_id,
                    "room_name": room_name,
                    "room_data_status": "UNAVAILABLE",
                }
            )
            continue
        general = extractor.get_room_general(room_data)
        conditions = extractor.get_room_conditions(room_data)
        apache_systems = extractor.get_apache_systems(room_data)
        system_id = str(apache_systems.get("HVAC_system") or "")
        if system_id:
            referenced_system_ids.add(system_id)
        gains = [
            json_safe(_child_data(item))
            for item in extractor.get_internal_gains(room_data)
        ]
        exchanges = [
            json_safe(_child_data(item))
            for item in extractor.get_air_exchanges(room_data)
        ]
        rooms.append(
            {
                "room_id": room_id,
                "room_name": room_name,
                "room_data_status": "AVAILABLE",
                "general": json_safe(general),
                "room_conditions": json_safe(conditions),
                "apache_system_assignment": json_safe(apache_systems),
                "internal_gain_count": len(gains),
                "internal_gains": gains,
                "air_exchange_count": len(exchanges),
                "air_exchanges": exchanges,
            }
        )

    systems = {
        system_id: json_safe(extractor.get_apache_system_data(system_id))
        for system_id in sorted(referenced_system_ids)
    }
    return {
        "room_count": len(rooms),
        "rooms": rooms,
        "referenced_apache_systems": systems,
        "claim_guardrail": (
            "Raw VEScripts read-back only; presence does not establish SIA compliance."
        ),
    }


_APS_BINDING_TOKEN_SETS: Dict[str, Sequence[Sequence[str]]] = {
    "heating_load": (("heating", "load"),),
    "cooling_load": (("cooling", "load"),),
    "lighting": (
        ("lighting", "power"),
        ("lights", "power"),
        ("lighting", "electric"),
        ("lighting", "energy"),
    ),
    "fan": (
        ("fan", "power"),
        ("fans", "power"),
        ("fan", "electric"),
        ("fan", "energy"),
    ),
    "pump": (
        ("pump", "power"),
        ("pumps", "power"),
        ("pump", "electric"),
        ("pump", "energy"),
    ),
    "auxiliary": (
        ("auxiliary", "power"),
        ("auxiliary", "energy"),
        ("aux", "power"),
        ("aux", "energy"),
    ),
    "heating_coil": (
        ("heating", "coil"),
        ("reheat", "coil"),
        ("heater", "coil"),
        ("supply", "heating"),
    ),
    "cooling_coil": (
        ("cooling", "coil"),
        ("cooler", "coil"),
        ("supply", "cooling"),
    ),
}


def _binding_record(variable: Optional[Sequence[Any]]) -> Optional[Dict[str, Any]]:
    """Return a readable APS variable-binding record."""
    if not variable:
        return None
    return {
        "aps_varname": str(variable[0] or ""),
        "display_name": str(variable[1] or ""),
        "model_level": str(variable[2] or ""),
        "metric_unit": str(variable[3] or "") if len(variable) > 3 else "",
        "metric_divisor": variable[4] if len(variable) > 4 else 1.0,
        "metric_offset": variable[5] if len(variable) > 5 else 0.0,
    }


def build_aps_variable_inventory(
    variables: Iterable[Dict[str, Any]],
    simulation_results_module: Any,
) -> Dict[str, Any]:
    """Report exact production bindings and nearby unbound APS variables."""
    variable_rows = list(variables)
    bindings: Dict[str, Optional[Dict[str, Any]]] = {}
    for key, token_sets in _APS_BINDING_TOKEN_SETS.items():
        if key in {"heating_load", "cooling_load"}:
            variable = simulation_results_module.find_room_sensible_load_variable(
                variable_rows, key.split("_", 1)[0]
            )
        else:
            variable = simulation_results_module.find_first_aps_variable(
                variable_rows, token_sets, "z"
            )
        bindings[key] = _binding_record(variable)

    keywords = {
        token
        for token_sets in _APS_BINDING_TOKEN_SETS.values()
        for token_set in token_sets
        for token in token_set
    }
    candidates = []
    for variable in variable_rows:
        aps_name = str(variable.get("aps_varname") or variable.get("name") or "")
        display_name = str(variable.get("display_name") or aps_name)
        haystack = "{} {}".format(aps_name, display_name).lower()
        if any(keyword in haystack for keyword in keywords):
            candidates.append(
                {
                    "aps_varname": aps_name,
                    "display_name": display_name,
                    "model_level": str(
                        variable.get("model_level") or variable.get("level") or ""
                    ),
                    "metric_unit": str(variable.get("resolved_metric_unit") or ""),
                    "units_type": json_safe(variable.get("units_type")),
                }
            )
    return {
        "available_variable_count": len(variable_rows),
        "production_bindings": bindings,
        "unresolved_bindings": [key for key, value in bindings.items() if value is None],
        "related_variable_count": len(candidates),
        "related_variables": candidates,
        "claim_guardrail": (
            "Variable-name discovery only; units, sign and physical meaning require review."
        ),
    }


def collect_aps_runtime_inventory(
    aps_file_name: str,
    simulation_results_module: Any,
) -> Dict[str, Any]:
    """Open the selected APS read-only and collect its variable inventory."""
    if not aps_file_name:
        return {"status": "NOT_AVAILABLE", "reason": "No selected APS file."}
    results_file = None
    try:
        results_file = simulation_results_module.open_results_reader(aps_file_name)
        variables = simulation_results_module.get_available_variables(results_file)
        report = build_aps_variable_inventory(variables, simulation_results_module)
        report.update({"status": "AVAILABLE", "aps_file": aps_file_name})
        return report
    except Exception as exc:
        return {
            "status": "NOT_CHECKABLE",
            "aps_file": aps_file_name,
            "reason": str(exc),
        }
    finally:
        if results_file is not None:
            try:
                results_file.close()
            except Exception:
                pass
