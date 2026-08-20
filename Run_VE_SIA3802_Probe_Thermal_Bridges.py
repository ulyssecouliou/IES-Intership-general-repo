"""READ-ONLY probe: does the iesve API expose the per-construction thermal-bridge
coefficient shown in Apache Construction Database Manager -> Project Constructions
-> Thermal Bridges (W/m2.K)?

Run this file from the IESVE Scripts window with the Run button, on the active
project. It performs NO mutation and NO simulation. It:
  1. collects every construction assigned to the model's surfaces and openings,
  2. for each unique construction, dumps the raw VECdbConstruction.get_properties()
     dict, the U-factors, and every non-callable attribute / zero-arg accessor,
  3. highlights any key whose name looks like a thermal-bridge / psi / chi /
     linear / y-value quantity, and prints its value + unit hint.

Purpose: decide, from the REAL API on this VE (not an assumption), whether the
thermal-bridge coefficient is machine-readable. If a readable member is found, we
switch SIA3802_THERMAL_BRIDGES from reviewer-CSV evidence to a direct VE read
(sum of coefficient x area, in W/K). If nothing is exposed, the reviewer CSV path
stays -- populated from the values visible in this dialog.

Nothing here is written back. It only reads and prints.
"""

from __future__ import annotations

import importlib
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Name fragments that would indicate a thermal-bridge quantity. Use the STEM
# "bridg" so both "bridge" and "bridging" match (the VE glazing key is
# thermal_bridging_coefficient).
_BRIDGE_HINTS = (
    "bridg", "psi", "linear", "y_value", "yvalue", "y-value",
    "junction", "tb_", "_tb", "point_transmit",
)


def _looks_like_bridge(name: str) -> bool:
    lowered = str(name or "").lower()
    return any(hint in lowered for hint in _BRIDGE_HINTS)


def _safe(callable_or_value):
    """Return a value, calling a zero-arg accessor defensively."""
    try:
        if callable(callable_or_value):
            return callable_or_value()
        return callable_or_value
    except Exception as exc:  # noqa: BLE001 - probe: report, never raise
        return f"<error: {exc}>"


def _dump_object(obj, label):
    print(f"  --- raw dump of {label} ---")
    # get_properties() dict is the most likely home of the coefficient.
    if hasattr(obj, "get_properties"):
        try:
            props = obj.get_properties()
            props = dict(props) if hasattr(props, "items") else props
            print(f"  get_properties() -> {type(props).__name__}")
            if isinstance(props, dict):
                for key in sorted(props):
                    marker = "  <-- BRIDGE?" if _looks_like_bridge(key) else ""
                    print(f"      {key} = {props[key]!r}{marker}")
        except Exception as exc:  # noqa: BLE001
            print(f"  get_properties() failed: {exc}")
    # Every non-dunder attribute / zero-arg accessor, flagged when name matches.
    print("  attributes / accessors matching a thermal-bridge name:")
    found_any = False
    for name in sorted(dir(obj)):
        if name.startswith("_"):
            continue
        if not _looks_like_bridge(name):
            continue
        found_any = True
        print(f"      {name} -> {_safe(getattr(obj, name, None))!r}")
    if not found_any:
        print("      (none)")

    # Try documented-looking candidate getters for an opaque thermal-bridge
    # coefficient (the glazing key is thermal_bridging_coefficient; opaque may
    # expose it under a method or a differently-named property).
    candidates = (
        "thermal_bridging_coefficient", "thermal_bridge_coefficient",
        "get_thermal_bridging_coefficient", "get_thermal_bridge_coefficient",
        "thermal_bridging", "thermal_bridges", "get_thermal_bridges",
        "psi_value", "get_psi", "linear_thermal_transmittance",
    )
    printed_candidate = False
    for name in candidates:
        if hasattr(obj, name):
            if not printed_candidate:
                print("  candidate thermal-bridge members present:")
                printed_candidate = True
            print(f"      {name} -> {_safe(getattr(obj, name))!r}")
    if not printed_candidate:
        print("  candidate thermal-bridge members: (none present)")


def run() -> None:
    try:
        import iesve  # type: ignore  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("Run this launcher inside IESVE VEScripts.") from exc

    de_module = importlib.reload(importlib.import_module("swiss_sia.data_extractor"))
    project = importlib.import_module("iesve").VEProject.get_current_project()
    if not project:
        raise RuntimeError("Open a project first.")

    extractor = de_module.VEDataExtractor(project)

    print("=" * 78)
    print("READ-ONLY THERMAL-BRIDGE API PROBE (no mutation, no simulation)")
    print("=" * 78)

    # 1. Collect every construction id assigned in the model.
    construction_ids = []
    seen = set()
    for body in extractor.get_bodies():
        for surface in extractor.get_surfaces(body):
            for cid in extractor.get_constructions(surface) or []:
                if cid and cid not in seen:
                    seen.add(cid)
                    construction_ids.append(cid)
            for opening in extractor.get_openings(surface) or []:
                cid = extractor.get_opening_construction(opening)
                if cid and cid not in seen:
                    seen.add(cid)
                    construction_ids.append(cid)

    print(f"Unique constructions assigned in the model: {len(construction_ids)}")
    if not construction_ids:
        print("No construction found. Open the client model first.")
        print("=" * 78)
        return

    # 2. Resolve the raw CDB construction object for each id and dump it.
    iesve = importlib.import_module("iesve")
    classes = extractor._get_cdb_construction_classes(iesve)
    classes.append(None)
    cdb_projects = extractor._get_cdb_projects()
    print(f"CDB projects available: {len(cdb_projects)}")

    any_bridge_key = False
    for cid in construction_ids:
        print("-" * 78)
        print(f"Construction id: {cid}")
        raw_obj = None
        for cdb_project in cdb_projects:
            for cls in classes:
                raw_obj = extractor._safe_get_cdb_construction(cdb_project, cid, cls)
                if raw_obj is not None:
                    break
            if raw_obj is not None:
                break
        if raw_obj is None:
            print("  (could not resolve the raw CDB construction object)")
            continue

        # U-factors for context (so we can compare with any bridge uplift).
        try:
            uvalue_types = extractor._get_cdb_uvalue_types(iesve)
            u_factors = {}
            for name, value in uvalue_types:
                try:
                    u_factors[name] = raw_obj.get_u_factor(value)
                except Exception:
                    pass
            print(f"  u_factors = {u_factors}")
        except Exception as exc:  # noqa: BLE001
            print(f"  u_factors read failed: {exc}")

        _dump_object(raw_obj, f"VECdbConstruction {cid}")

        # Did this construction expose any bridge-looking key?
        try:
            props = raw_obj.get_properties()
            props = dict(props) if hasattr(props, "items") else {}
        except Exception:
            props = {}
        if any(_looks_like_bridge(k) for k in props) or any(
            _looks_like_bridge(n) for n in dir(raw_obj) if not n.startswith("_")
        ):
            any_bridge_key = True

    # Full member list of the first OPAQUE construction, so a thermal-bridge
    # method that does not match the hints is still visible for eyeballing.
    print("-" * 78)
    print("FULL member list of the first opaque construction (names only):")
    first_opaque = None
    for cid in construction_ids:
        for cdb_project in cdb_projects:
            for cls in classes:
                obj = extractor._safe_get_cdb_construction(cdb_project, cid, cls)
                if obj is None:
                    continue
                try:
                    props = obj.get_properties()
                    cat = str((dict(props) if hasattr(props, "items") else {}).get("category", ""))
                except Exception:
                    cat = ""
                if "glazing" not in cat.lower() and "window" not in cat.lower():
                    first_opaque = obj
                    break
            if first_opaque is not None:
                break
        if first_opaque is not None:
            break
    if first_opaque is not None:
        names = [n for n in sorted(dir(first_opaque)) if not n.startswith("_")]
        print("  ", names)
    else:
        print("  (no opaque construction resolved)")

    # Project-level thermal-bridge collections (some VE versions keep junction
    # psi lists on the CDB project / model, not on the construction).
    print("-" * 78)
    print("Project/model members matching a thermal-bridge name:")
    project_hits = False
    for holder_label, holder in (
        ("VEProject", project),
        ("VEModel", getattr(extractor, "model", None)),
    ):
        if holder is None:
            continue
        for name in sorted(dir(holder)):
            if not name.startswith("_") and _looks_like_bridge(name):
                project_hits = True
                print(f"      {holder_label}.{name} -> {_safe(getattr(holder, name, None))!r}")
    for cdb_project in cdb_projects[:1]:
        for name in sorted(dir(cdb_project)):
            if not name.startswith("_") and _looks_like_bridge(name):
                project_hits = True
                print(f"      VECdbProject.{name} -> {_safe(getattr(cdb_project, name, None))!r}")
    if not project_hits:
        print("      (none)")

    print("=" * 78)
    if any_bridge_key:
        print("RESULT: a thermal-bridge member IS exposed by the API (see flagged")
        print("keys above, e.g. thermal_bridging_coefficient on glazing).")
        print("Send me: (1) is the Thermal Bridges tab on GLAZING or on OPAQUE walls?")
        print("(2) the value shown there, and (3) whether it appears above. If opaque")
        print("thermal bridges are NOT exposed, we keep the reviewer-CSV for those.")
    else:
        print("RESULT: NO thermal-bridge member exposed by the documented API here.")
        print("The reviewer-CSV path stays; populate it from the Thermal Bridges tab.")
    print("=" * 78)


run()
