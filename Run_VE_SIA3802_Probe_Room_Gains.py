"""READ-ONLY probe: does VE expose template-inherited internal gains per room?

Run this file from the IESVE Scripts window with the Run button, on the active
project. It performs NO mutation: it only reads, for every room, its assigned
thermal template and both gain lists, then reports whether the room's
``get_internal_gains()`` reflects the gains defined on its assigned template.

This resolves the [TO VERIFY] question behind the gain-bridge read-back failure:
  - if some room's gains DO reflect its assigned template -> inheritance works,
    and the read-back should verify the template, not the room;
  - if no room ever reflects its template's gains -> room-level gains are
    independent of the template, and gains must be set in the VE room UI.

No value is written and no verdict is granted.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run() -> None:
    try:
        import iesve  # type: ignore
    except Exception as exc:
        raise RuntimeError("Run this launcher inside IESVE VEScripts.") from exc

    project = iesve.VEProject.get_current_project()
    if not project:
        raise RuntimeError("Open a project first.")
    try:
        model = project.models[0]
    except Exception as exc:
        raise RuntimeError("The active project has no usable real model.") from exc

    remediation = importlib.reload(
        importlib.import_module("swiss_sia.client_template_remediation")
    )
    gain_family = remediation._gain_family
    inventory = remediation.collect_inventory(project, model)

    templates_by_handle = {
        str(t.get("handle") or ""): t for t in inventory.get("templates", [])
    }

    def families(records):
        seen = []
        for record in records or []:
            fam = gain_family(record) if isinstance(record, dict) else None
            seen.append(fam if fam is not None else "<unknown>")
        return seen

    print("=" * 78)
    print("READ-ONLY ROOM-GAIN INHERITANCE PROBE (no mutation)")
    print("=" * 78)
    print("Templates in project:")
    for t in inventory.get("templates", []):
        print("  handle={} name={!r} template_gains={}".format(
            t.get("handle"), t.get("name"),
            families(t.get("casual_gains", [])),
        ))

    print("\nRooms:")
    any_inheritance = False
    for room in inventory.get("rooms", []):
        handle = str(room.get("current_template_handle") or "")
        template = templates_by_handle.get(handle, {})
        state = room.get("current_state") or {}
        room_fams = families(state.get("casual_gains", []))
        tmpl_fams = families(template.get("casual_gains", []))
        room_set = {f for f in room_fams if f != "<unknown>"}
        tmpl_set = {f for f in tmpl_fams if f != "<unknown>"}
        reflects = bool(tmpl_set) and tmpl_set.issubset(room_set)
        any_inheritance = any_inheritance or reflects
        print("  - {!r}".format(room.get("room_name")))
        print("      room_id (use this in the usage-mapping CSV) : {}".format(
            room.get("room_id")))
        print("      assigned template : handle={} name={!r}".format(
            handle, template.get("name")))
        print("      room get_internal_gains : {}".format(room_fams or "[]"))
        print("      template gains          : {}".format(tmpl_fams or "[]"))
        print("      room reflects template  : {}".format(
            "YES" if reflects else "NO"))

    any_template_has_gains = any(
        {f for f in families(t.get("casual_gains", [])) if f != "<unknown>"}
        for t in inventory.get("templates", [])
    )
    print("\n--- ROOM ID SOURCES (the usage-mapping CSV must use room.id) ---")
    print("  room.id = get_object_id(body): tries get_id() FIRST, then .id.")
    for body in model.get_bodies(False):
        bid = getattr(body, "id", None)
        getid = None
        try:
            member = getattr(body, "get_id", None)
            getid = member() if callable(member) else None
        except Exception as exc:  # noqa: BLE001 -- diagnostic only
            getid = "<error {}>".format(exc)
        print("  name={!r} | .id={!r} | get_id()={!r}  --> use the get_id() value "
              "if it differs".format(getattr(body, "name", ""), bid, getid))

    print("\n--- CONCLUSION ---")
    if any_inheritance:
        print("At least one room's get_internal_gains reflects its assigned")
        print("template -> template-inherited gains ARE readable. The bridge")
        print("read-back should verify the template, not the room.")
    elif not any_template_has_gains:
        print("INCONCLUSIVE: no template in this project defines any gains, so")
        print("inheritance could not be tested. The rooms return [] simply")
        print("because their assigned template is empty -- which is also why the")
        print("audit finds no gains. Assign a gain-bearing template first, then")
        print("re-run this probe to test inheritance.")
    else:
        print("A gain-bearing template exists but no room reflects it:")
        print("room-level gains appear independent of the template on this VE.")
    print("=" * 78)


if __name__ == "__main__":
    run()
