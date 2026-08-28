"""Read-only VE probe: what does the API expose for the blocked SIA 380/2 families?

Open this file in the IESVE Scripts window with the target client project active
and click Run. The probe creates and modifies NOTHING. It reads, per assigned
Apache system, the members that the four not-yet-automated reference-project
families need, and writes a JSON diagnostic beside the active VE project plus a
per-family availability verdict to the console.

Families probed (reference values already frozen in config; only the PROJECT
value extraction is unknown):
  - ventilation systems : heat-recovery efficiency (eps_V), duct/AHU leakage
    class, specific fan power, U_ahu;
  - emission / capacity : heating/cooling radiant fraction, unlimited-capacity
    flags;
  - photovoltaic        : installed PV area and conversion efficiency;
  - thermal bridges     : any linear-transmittance (psi/chi) member on
    constructions (the API doc suggests none -> this confirms it).

The probe is deliberately defensive: every member is read through getattr/try so
a missing member is reported as "not exposed", never a crash. Nothing here
asserts an API member exists -- it discovers what this VE build actually offers.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

_ABSENT = "<not exposed>"


def _jsonable(value, depth=0):
    """Convert VE enums/containers to bounded JSON-safe values."""
    if depth > 4:
        return repr(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v, depth + 1) for k, v in list(value.items())[:100]}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v, depth + 1) for v in list(value)[:100]]
    enum_value = getattr(value, "value", None)
    if enum_value is not None and enum_value is not value:
        return {"name": str(value), "value": _jsonable(enum_value, depth + 1)}
    return str(value)


def _call_dict(obj, method_name):
    """Call a zero-argument method and coerce the result to a plain dict."""
    try:
        result = getattr(obj, method_name)()
    except Exception as exc:  # noqa: BLE001 - probe: report, never fail
        return {"__error__": f"{type(exc).__name__}: {exc}"}
    if isinstance(result, dict):
        return {str(k): _jsonable(v) for k, v in result.items()}
    if hasattr(result, "items"):
        try:
            return {str(k): _jsonable(v) for k, v in result.items()}
        except Exception:  # noqa: BLE001
            pass
    return {"__value__": _jsonable(result)}


def _pick(source, *keys):
    """Return the first present, non-None key from a dict, else the absent marker."""
    for key in keys:
        if isinstance(source, dict) and key in source and source[key] is not None:
            return source[key]
    return _ABSENT


def _probe_systems(iesve):
    """Read the ventilation/emission members per assigned Apache system."""
    systems_report = []
    try:
        raw = iesve.VEProject.get_current_project().apache_systems()
    except Exception as exc:  # noqa: BLE001
        return {"__error__": f"apache_systems() failed: {type(exc).__name__}: {exc}"}
    for system in list(raw or [])[:50]:
        vent = _call_dict(system, "ventilation_ncm")
        adjust = _call_dict(system, "system_adjustment_ncm")
        aux = _call_dict(system, "auxiliary_energy")
        # Radiant fraction / unlimited capacity live on the thermal-template view;
        # try the system's own accessor first, then the template method.
        systems_report.append({
            "id": str(getattr(system, "id", "") or getattr(system, "name", "") or "system"),
            "name": str(getattr(system, "name", "") or ""),
            "ventilation": {
                "heat_recovery_efficiency": _pick(vent, "heat_recovery_efficiency"),
                "heat_recovery_type": _pick(vent, "heat_recovery_type"),
                "variable_heat_recovery": _pick(vent, "variable_heat_recovery"),
            },
            "system_adjustment": {
                "ductwork_leakage_test": _pick(adjust, "ductwork_leakage_test"),
                "cen_class": _pick(adjust, "cen_class"),
                "specific_fan_power": _pick(adjust, "specific_fan_power"),
                "u_ahu_candidates": {
                    k: adjust.get(k)
                    for k in ("U_ahu", "ahu_heat_transfer", "thermal_transmittance_ahu")
                    if isinstance(adjust, dict) and k in adjust
                } or _ABSENT,
            },
            "auxiliary_energy": {"SFP": _pick(aux, "SFP", "sfp")},
            "emission": {
                "heating_plant_radiant_fraction": _pick(
                    _call_dict(system, "heating"), "heating_plant_radiant_fraction"),
                "cooling_plant_radiant_fraction": _pick(
                    _call_dict(system, "cooling"), "cooling_plant_radiant_fraction"),
            },
            "raw_ncm_keys": sorted(vent.keys()) if isinstance(vent, dict) else _ABSENT,
            "raw_adjustment_keys": sorted(adjust.keys()) if isinstance(adjust, dict) else _ABSENT,
        })
    return systems_report


def _probe_pv(iesve):
    """Read installed PV data via VERenewables, defensively."""
    try:
        renewables = iesve.VERenewables()
    except Exception as exc:  # noqa: BLE001
        return {"__error__": f"VERenewables() not instantiable: {type(exc).__name__}: {exc}"}
    try:
        pv_list = renewables.get_pv_data()
    except Exception as exc:  # noqa: BLE001
        return {"__error__": f"get_pv_data() failed: {type(exc).__name__}: {exc}"}
    out = []
    for pv in list(pv_list or [])[:50]:
        entry = {k: _jsonable(getattr(pv, k, None)) for k in ("id", "type_id", "area", "cell_efficiency")}
        type_id = getattr(pv, "type_id", None)
        if type_id is not None:
            try:
                pv_type = renewables.get_pv_type_by_id(type_id)
                entry["electrical_conversion_efficiency"] = _jsonable(
                    getattr(pv_type, "electrical_conversion_efficiency", None))
            except Exception as exc:  # noqa: BLE001
                entry["__type_error__"] = f"{type(exc).__name__}: {exc}"
        out.append(entry)
    return out or _ABSENT


def _probe_emission_capacity(project):
    """Read radiant fraction / unlimited-capacity flags from body thermal templates.

    The apache-system heating()/cooling() dicts do not carry the radiant fraction;
    per the API contract it lives on the body's thermal-template apache systems
    (VEBody.get_apache_systems). Probe a sample of bodies and report the target
    keys plus the full key list of the first system for discovery.
    """
    try:
        from swiss_sia.data_extractor import VEDataExtractor

        bodies = VEDataExtractor(project).get_bodies()
    except Exception as exc:  # noqa: BLE001
        return {"__error__": f"body access failed: {type(exc).__name__}: {exc}"}
    out = []
    discovered_keys = None
    for body in list(bodies or [])[:30]:
        systems = _call_dict(body, "get_apache_systems")
        # get_apache_systems may return a dict keyed by system, or a value dict.
        candidates = list(systems.values()) if isinstance(systems, dict) else [systems]
        for entry in candidates[:5]:
            if isinstance(entry, dict):
                if discovered_keys is None and entry:
                    discovered_keys = sorted(entry.keys())
                radiant_h = _pick(entry, "heating_plant_radiant_fraction")
                radiant_c = _pick(entry, "cooling_plant_radiant_fraction")
                if radiant_h is not _ABSENT or radiant_c is not _ABSENT:
                    out.append({
                        "body": str(getattr(body, "id", "?")),
                        "heating_plant_radiant_fraction": radiant_h,
                        "cooling_plant_radiant_fraction": radiant_c,
                        "heating_capacity_unlimited": _pick(entry, "heating_capacity_unlimited"),
                        "cooling_capacity_unlimited": _pick(entry, "cooling_capacity_unlimited"),
                    })
    return {"found": out or _ABSENT, "first_system_keys": discovered_keys or _ABSENT}


def _probe_enums(iesve):
    """Introspect the leakage/CEN enums so the observed ints can be named.

    The NCM dicts return integer codes (e.g. cen_class=3, ductwork_leakage_test=0);
    this dumps any iesve attribute whose name relates to leakage/CEN so the exact
    enum mapping to the SIA duct/AHU class can be confirmed, never guessed.
    """
    result = {}
    for name in dir(iesve):
        low = name.lower()
        if any(token in low for token in ("leakage", "cen_", "cenclass", "leakage_standard")):
            member = getattr(iesve, name, None)
            try:
                members = {k: _jsonable(getattr(member, k)) for k in dir(member) if not k.startswith("_")}
                result[name] = members
            except Exception:  # noqa: BLE001
                result[name] = str(member)
    # Common name-helper functions (e.g. aux_energy_method_names) may exist.
    for helper in ("ncm_leakage_standard_names", "ncm_leakage_test_names", "cen_class_names"):
        fn = getattr(iesve, helper, None)
        if callable(fn):
            try:
                result[helper] = _jsonable(fn())
            except Exception as exc:  # noqa: BLE001
                result[helper] = f"<call failed: {exc}>"
    return result or "<no leakage/CEN enum found on iesve; observed ints must be mapped from VE docs>"


def main():
    """Run the read-only extraction probe and write a JSON diagnostic."""
    import importlib

    try:
        iesve = importlib.import_module("iesve")
    except Exception as exc:  # noqa: BLE001
        print("This probe must run inside IESVE (iesve module unavailable): %s" % exc)
        return

    project = iesve.VEProject.get_current_project()
    project_path = str(getattr(project, "path", "") or "")

    emission_capacity = _probe_emission_capacity(project)
    photovoltaic = _probe_pv(iesve)
    report = {
        "probe": "sia3802_reference_extraction",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project_path": project_path,
        "apache_systems": _probe_systems(iesve),
        "emission_capacity": emission_capacity,
        "photovoltaic": photovoltaic,
        "leakage_enums": _probe_enums(iesve),
        "thermal_bridges": "NOT EXPOSED per API contract (no psi/chi member); reviewer evidence only",
    }

    # Per-family verdict from what the probe actually found.
    systems = report["apache_systems"] if isinstance(report["apache_systems"], list) else []

    def _any(path_a, path_b):
        return any(
            isinstance(s.get(path_a), dict) and s[path_a].get(path_b) not in (None, _ABSENT)
            for s in systems
        )

    emission_found = (
        isinstance(emission_capacity, dict)
        and isinstance(emission_capacity.get("found"), list)
        and bool(emission_capacity["found"])
    )
    if isinstance(photovoltaic, list) and photovoltaic:
        pv_verdict = "EXTRACTABLE (PV present)"
    elif isinstance(photovoltaic, dict) and "__error__" in photovoltaic:
        pv_verdict = "API ERROR: " + str(photovoltaic["__error__"])
    else:
        pv_verdict = "API OK, no PV in this project (extractable when present)"

    report["verdict"] = {
        "ventilation_efficiency (eps_V)": "EXTRACTABLE" if _any("ventilation", "heat_recovery_efficiency") else "NOT EXPOSED",
        "duct/AHU leakage class": "EXTRACTABLE (int enum, see leakage_enums)" if _any("system_adjustment", "cen_class") else "NOT EXPOSED",
        "emission radiant fraction": "EXTRACTABLE" if emission_found else "NOT EXPOSED via body templates",
        "photovoltaic": pv_verdict,
        "thermal_bridges (psi/chi)": "NOT EXPOSED (reviewer evidence only)",
    }

    out_dir = Path(project_path).parent if project_path else PROJECT_ROOT
    out_path = out_dir / "sia3802_reference_extraction_probe.json"
    try:
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Wrote extraction probe: %s" % out_path)
    except Exception as exc:  # noqa: BLE001
        print("Could not write JSON (%s); dumping to console:" % exc)
        print(json.dumps(report, ensure_ascii=False, indent=2))

    print("\n=== Per-family extraction verdict ===")
    for family, status in report["verdict"].items():
        print("  %-32s %s" % (family, status))


if __name__ == "__main__":
    main()
