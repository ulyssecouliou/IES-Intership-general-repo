"""Read-only inspection of template and room-level PeopleGain representations."""

from __future__ import annotations

import pprint
import sys
from pathlib import Path

import iesve


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from swiss_sia.reference_model.ve_compat import thermal_templates  # noqa: E402


def _is_people(data):
    label = str(data.get("type_str", "")).casefold()
    return "people" in label


def run():
    project = iesve.VEProject.get_current_project()
    model = project.models[0]
    rooms = [
        body
        for body in model.get_bodies(False)
        if str(getattr(body, "name", "")).startswith("SIA_REF_ZONE_")
    ]
    print("READ-ONLY ROOM PEOPLE-GAIN INSPECTION")
    print("Project: {}".format(project.name))
    print("Generated rooms: {}".format(len(rooms)))
    if not rooms:
        raise RuntimeError("No SIA_REF_ZONE_ room exists in the active project.")

    room = rooms[0]
    room_data = room.get_room_data()
    print("--- room ---")
    print("name: {!r}".format(room.name))
    pprint.pprint(dict(room_data.get_general()), width=180)
    room_people = []
    for gain in room_data.get_internal_gains():
        data = dict(gain.get())
        if _is_people(data):
            room_people.append((gain, data))
    print("room_people_count: {}".format(len(room_people)))
    for gain, data in room_people:
        print("python_type: {!r}".format(type(gain)))
        print("set_doc: {!r}".format(getattr(getattr(gain, "set", None), "__doc__", None)))
        pprint.pprint(data, width=180)

    print("--- matching thermal template ---")
    general = dict(room_data.get_general())
    expected_name = str(general.get("thermal_template_name", ""))
    matches = []
    for handle, template in thermal_templates(project, assigned=False).items():
        if str(getattr(template, "name", "")) == expected_name:
            matches.append((handle, template))
    print("template_name: {!r}".format(expected_name))
    print("template_matches: {}".format(len(matches)))
    for handle, template in matches:
        print("template_handle: {!r}".format(handle))
        for gain in template.get_casual_gains():
            data = dict(gain.get())
            if _is_people(data):
                print("template_people_python_type: {!r}".format(type(gain)))
                pprint.pprint(data, width=180)

    print("Inspection complete; no VE model or template data was changed.")


if __name__ == "__main__":
    run()
