"""READ-ONLY probe: read the model's thermal bridges (psi / chi) via the
surface-level iesve API and compute the building thermal-bridge conductance.

An official IES 2025.2 script (thermal_bridging_report.py) revealed that thermal
bridges are exposed on SURFACES, not constructions:

  surface.get_thermal_bridges_non_repeating() -> linear/opening junctions:
      bd.type (iesve.ThermalBridge_NonRepType), bd.length [m],
      bd.psi [W/(m.K)], bd.flux_factor
  surface.get_thermal_bridges_random() -> point/random bridges:
      bd.type (iesve.ThermalBridge_RandomType, incl. .point),
      bd.dimension (length [m] for linear, count for point),
      bd.transmittance (psi [W/(m.K)] for linear, chi [W/K] for point)

These are exactly the SIA 380/2 quantities (psi.L + chi, in W/K). This probe
performs NO mutation and NO simulation. It:
  1. capability-checks the two surface members on THIS VE version,
  2. lists every non-none thermal bridge per room/surface with its psi/chi,
  3. computes the building thermal-bridge conductance
        H_tb = sum(psi * length * flux_factor) + sum(chi * count)   [W/K]

Run it from the IESVE Scripts window with the Run button on the active project.
Send me the output: if the members are present and return data, I wire a direct
VE read of the SIA thermal-bridge term (no reviewer CSV needed).
"""

from __future__ import annotations

import importlib
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def run() -> None:
    try:
        import iesve  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("Run this launcher inside IESVE VEScripts.") from exc

    project = iesve.VEProject.get_current_project()
    if not project:
        raise RuntimeError("Open a project first.")
    models = project.models
    if not models:
        raise RuntimeError("The active project has no model.")
    model = models[0]

    print("=" * 78)
    print("READ-ONLY THERMAL-BRIDGE PROBE (surface API; no mutation, no simulation)")
    print("=" * 78)

    # 1. Capability check on the documented surface members.
    bodies = model.get_bodies_and_ids(False)
    sample_surface = None
    for body in bodies.values():
        if getattr(body, "type", None) != iesve.VEBody_type.room:
            continue
        surfaces = body.get_surfaces()
        if surfaces:
            sample_surface = surfaces[0]
            break
    has_nonrep = bool(sample_surface is not None and hasattr(sample_surface, "get_thermal_bridges_non_repeating"))
    has_random = bool(sample_surface is not None and hasattr(sample_surface, "get_thermal_bridges_random"))
    print("Capability check (VESurface):")
    print("  get_thermal_bridges_non_repeating:", "PRESENT" if has_nonrep else "ABSENT")
    print("  get_thermal_bridges_random       :", "PRESENT" if has_random else "ABSENT")
    if not (has_nonrep or has_random):
        print("-" * 78)
        print("RESULT: neither thermal-bridge member exists on this VE version.")
        print("Keep the reviewer-CSV path. Tell me your IESVE version.")
        print("=" * 78)
        return

    units = "metric" if project.get_display_units() == iesve.DisplayUnits.metric else "ip"
    print("Display units:", units, "(psi expected in W/(m.K), chi in W/K when metric)")

    # 2 + 3. Enumerate every thermal bridge and accumulate the W/K conductance.
    linear_conductance = 0.0   # sum(psi * length * flux_factor)
    point_conductance = 0.0    # sum(chi * count)
    linear_count = 0
    point_count = 0
    rooms_seen = 0

    for body in bodies.values():
        if getattr(body, "type", None) != iesve.VEBody_type.room:
            continue
        rooms_seen += 1
        for surface in body.get_surfaces():
            # Non-repeating (linear + opening) bridges.
            if has_nonrep:
                try:
                    nonrep = surface.get_thermal_bridges_non_repeating()
                except Exception as exc:  # noqa: BLE001
                    nonrep = []
                    print("  [warn] non_repeating read failed:", exc)
                for bd in nonrep:
                    if getattr(bd, "type", None) == iesve.ThermalBridge_NonRepType.none:
                        continue
                    psi = _num(getattr(bd, "psi", None))
                    length = _num(getattr(bd, "length", None))
                    flux = _num(getattr(bd, "flux_factor", None))
                    flux = 1.0 if flux is None else flux
                    contrib = None
                    if psi is not None and length is not None:
                        contrib = psi * length * flux
                        linear_conductance += contrib
                        linear_count += 1
                    print("  [{}] {} | {} : psi={} W/mK, L={} m, flux={} -> {} W/K".format(
                        body.name, str(getattr(surface, "type", "")), str(getattr(bd, "type", "")),
                        psi, length, flux,
                        round(contrib, 4) if contrib is not None else "?"))
            # Random (point + random-linear) bridges.
            if has_random:
                try:
                    randoms = surface.get_thermal_bridges_random()
                except Exception as exc:  # noqa: BLE001
                    randoms = []
                    print("  [warn] random read failed:", exc)
                for bd in randoms:
                    btype = getattr(bd, "type", None)
                    transmittance = _num(getattr(bd, "transmittance", None))
                    dimension = _num(getattr(bd, "dimension", None))
                    is_point = (btype == iesve.ThermalBridge_RandomType.point)
                    contrib = None
                    if transmittance is not None and dimension is not None:
                        contrib = transmittance * dimension
                        if is_point:
                            point_conductance += contrib
                            point_count += 1
                        else:
                            linear_conductance += contrib
                            linear_count += 1
                    kind = "chi(point)" if is_point else "psi(random-linear)"
                    print("  [{}] {} | {} : {}={}, dim={} -> {} W/K".format(
                        body.name, str(getattr(surface, "type", "")), str(btype),
                        kind, transmittance, dimension,
                        round(contrib, 4) if contrib is not None else "?"))

    total = linear_conductance + point_conductance
    print("-" * 78)
    print("Rooms scanned:", rooms_seen)
    print("Linear/opening bridges:", linear_count,
          "-> sum(psi.L.flux) =", round(linear_conductance, 4), "W/K")
    print("Point bridges:", point_count,
          "-> sum(chi.count) =", round(point_conductance, 4), "W/K")
    print("BUILDING THERMAL-BRIDGE CONDUCTANCE H_tb =", round(total, 4), "W/K")
    print("=" * 78)
    if linear_count == 0 and point_count == 0:
        print("RESULT: the members exist but the model carries NO thermal bridge")
        print("(all zero / none). Enter junctions in VE, or supply the reviewer CSV.")
    else:
        print("RESULT: VE exposes real psi/chi thermal bridges. Send me this output;")
        print("I will wire a direct VE read of H_tb (W/K) for SIA3802_THERMAL_BRIDGES.")
    print("=" * 78)


run()
