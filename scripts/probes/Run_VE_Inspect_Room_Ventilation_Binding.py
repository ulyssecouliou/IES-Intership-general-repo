"""Read-only inspection of room/template ventilation and Apache system data."""

from __future__ import annotations

import pprint
import sys
from pathlib import Path

import iesve


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from swiss_sia.reference_model.ve_compat import thermal_templates  # noqa: E402


def run():
    project = iesve.VEProject.get_current_project()
    model = project.models[0]
    rooms = [
        body
        for body in model.get_bodies(False)
        if str(getattr(body, "name", "")).startswith("SIA_REF_ZONE_")
    ]
    print("READ-ONLY ROOM VENTILATION-BINDING INSPECTION")
    print("Project: {}".format(project.name))
    print("Generated rooms: {}".format(len(rooms)))
    if not rooms:
        raise RuntimeError("No SIA_REF_ZONE_ room exists in the active project.")

    room = rooms[0]
    room_data = room.get_room_data()
    general = dict(room_data.get_general())
    print("--- room ---")
    print("name: {!r}".format(room.name))
    print("floor_area_m2: {!r}".format(room.get_areas().get("int_floor_area")))
    print("general:")
    pprint.pprint(general, width=190)
    print("apache_systems:")
    pprint.pprint(dict(room_data.get_apache_systems()), width=190)
    print("room_conditions:")
    pprint.pprint(dict(room_data.get_room_conditions()), width=190)
    print("room_air_exchanges:")
    room_exchanges = list(room_data.get_air_exchanges())
    print("count: {}".format(len(room_exchanges)))
    for exchange in room_exchanges:
        print("python_type: {!r}".format(type(exchange)))
        print(
            "set_doc: {!r}".format(
                getattr(getattr(exchange, "set", None), "__doc__", None)
            )
        )
        pprint.pprint(dict(exchange.get()), width=190)

    print("--- matching thermal template ---")
    template_name = str(general.get("thermal_template_name", ""))
    matches = [
        (handle, template)
        for handle, template in thermal_templates(project, assigned=False).items()
        if str(getattr(template, "name", "")) == template_name
    ]
    print("template_name: {!r}".format(template_name))
    print("template_matches: {}".format(len(matches)))
    for handle, template in matches:
        print("template_handle: {!r}".format(handle))
        print("template_apache_systems:")
        pprint.pprint(dict(template.get_apache_systems()), width=190)
        print("template_air_exchanges:")
        for exchange in template.get_air_exchanges():
            print("python_type: {!r}".format(type(exchange)))
            pprint.pprint(dict(exchange.get()), width=190)

    print("Inspection complete; no VE model, template or system data was changed.")


if __name__ == "__main__":
    run()
