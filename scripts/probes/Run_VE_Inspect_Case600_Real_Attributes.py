"""Read-only comparison of default and explicit real-building room data."""

import pprint

import iesve


ROOM_NAME = "SIA4010_TEST_1_600_ZONE"


def _record_payloads(records):
    payloads = []
    for record in records:
        try:
            payloads.append(dict(record.get()))
        except Exception as exc:
            payloads.append({"read_error": repr(exc)})
    return payloads


def _print_room_data(label, room_data):
    print("--- {} ---".format(label))
    print("python_type={!r}".format(type(room_data)))
    print("general:")
    pprint.pprint(dict(room_data.get_general()), width=180)
    print("gains:")
    pprint.pprint(
        _record_payloads(room_data.get_internal_gains()), width=220
    )
    print("air_exchanges:")
    pprint.pprint(
        _record_payloads(room_data.get_air_exchanges()), width=220
    )


def run():
    """Inspect getters only; never call setters or save."""

    project = iesve.VEProject.get_current_project()
    rooms = [
        body
        for body in project.models[0].get_bodies(False)
        if str(getattr(body, "name", "")) == ROOM_NAME
    ]
    print("READ-ONLY CASE 600 ATTRIBUTE-TYPE INSPECTION")
    print("Project: {}".format(project.name))
    print("Room matches: {}".format(len(rooms)))
    for body in rooms:
        _print_room_data("DEFAULT get_room_data()", body.get_room_data())
        _print_room_data(
            "REAL get_room_data(real_attributes)",
            body.get_room_data(iesve.attribute_type.real_attributes),
        )
    print("Inspection complete; no project data was changed or saved.")


if __name__ == "__main__":
    run()
