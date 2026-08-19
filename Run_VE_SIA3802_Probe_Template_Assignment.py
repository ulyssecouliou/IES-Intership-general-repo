"""MUTATION PROBE (disposable copy only): does raw template assignment give a
room the template's internal gains, WITHOUT the gain-structure bridge?

This resolves the [TO VERIFY] question behind the bridge read-back failure. It:
  1. requires a disposable project copy (_TEST / _COPY / _DISPOSABLE);
  2. creates the source-traced SIA 2024 4.01 template (which HAS gains);
  3. reads one room's gains BEFORE;
  4. calls the RAW VEModel.assign_thermal_template_to_rooms (NO bridge, no
     room-gain synchronisation);
  5. reads the same room's gains AFTER;
  6. reports whether the template's gains propagated to the room.

It writes to VE but never saves. Close VE WITHOUT saving and discard the copy
afterwards, whatever the result. No compliance verdict is granted.

  - Gains appear after a plain assignment -> inheritance works; the apply path
    can be simplified to a plain assignment (drop the failing bridge).
  - Gains do NOT appear -> the documented API cannot materialise room gains;
    the write feature is dropped and gains are set in the VE room UI.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MAX_ROOMS = 2


def run() -> None:
    try:
        import iesve  # type: ignore
    except Exception as exc:
        raise RuntimeError("Run this launcher inside IESVE VEScripts.") from exc

    source_module = importlib.reload(
        importlib.import_module("swiss_sia.sia3802_classroom_template")
    )
    importlib.reload(
        importlib.import_module("swiss_sia.reference_model.ve_asset_provisioner")
    )
    gateway_module = importlib.reload(
        importlib.import_module("swiss_sia.reference_model.ve_api")
    )
    hub_module = importlib.reload(importlib.import_module("swiss_sia.compliance_hub"))
    gain_family = gateway_module._gain_family

    gateway = gateway_module.IesVeGateway(iesve)
    project_path = gateway.project_path.resolve()
    if not hub_module.is_disposable_project(str(project_path)):
        raise RuntimeError(
            "Open a saved project copy ending in _TEST, _COPY or _DISPOSABLE first."
        )

    def families(snapshot):
        out = []
        for record in snapshot.get("gains", []) or []:
            try:
                fam = gain_family(record)
            except Exception:
                fam = None
            out.append(fam if fam is not None else "<unknown>")
        return out

    print("=" * 78)
    print("MUTATION PROBE: raw template assignment -> room gains (disposable copy)")
    print("=" * 78)
    print("Project copy:", project_path)

    plan, summary = source_module.build_classroom_operational_plan(PROJECT_ROOT)
    receipt = gateway.provision_operational_template(plan)
    print("Template created:", summary["template_name"], "->", receipt.get("status"))

    template_handle, template = gateway._find_template(summary["template_name"])
    template_families = families(
        {"gains": [
            gateway._record_data(r, "template gain")
            for r in list(template.get_casual_gains())
        ]}
    )
    print("Template gain families:", template_families)

    bodies = list(gateway.model.get_bodies(False))[:MAX_ROOMS]
    if not bodies:
        raise RuntimeError("No rooms in the active model.")

    for body in bodies:
        room_id = str(getattr(body, "id", "") or "")
        before = gateway._client_room_template_snapshot(body)
        print("\nRoom:", before.get("room_name"))
        print("  gains BEFORE:", families(before) or "[]")

        if hasattr(template, "apply_changes"):
            template.apply_changes()
        gateway.model.assign_thermal_template_to_rooms(template, [room_id])

        fresh = {
            str(getattr(b, "id", "") or ""): b
            for b in gateway.model.get_bodies(False)
        }
        after = gateway._client_room_template_snapshot(fresh.get(room_id, body))
        after_fams = families(after)
        print("  assigned template handle:",
              dict(after.get("general", {})).get("thermal_template"))
        print("  gains AFTER :", after_fams or "[]")
        propagated = {f for f in template_families if f != "<unknown>"} <= {
            f for f in after_fams if f != "<unknown>"
        } and bool(template_families)
        print("  template gains propagated to room:", "YES" if propagated else "NO")

    print("\n--- CONCLUSION ---")
    print("If AFTER shows the template gains -> plain assignment inherits gains;")
    print("the failing bridge can be removed and the apply simplified.")
    print("If AFTER is still [] -> the documented API cannot materialise room")
    print("gains; set gains in the VE room UI instead.")
    print("\nClose VE WITHOUT saving and discard this disposable copy.")
    print("=" * 78)


if __name__ == "__main__":
    run()
