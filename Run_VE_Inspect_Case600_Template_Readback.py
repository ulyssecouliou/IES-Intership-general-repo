"""Read-only inspection of Case 600 template versus room-content read-back."""

import pprint

import iesve


ROOM_NAME = "SIA4010_TEST_1_600_ZONE"
TEMPLATE_NAME = "SIA4010_TEST1_CASE600"


def _records(records):
    result = []
    for record in records:
        try:
            data = dict(record.get())
        except Exception as exc:
            data = {"read_error": repr(exc)}
        result.append(
            {
                "python_type": str(type(record)),
                "object_name": str(getattr(record, "name", "")),
                "object_id": str(getattr(record, "id", "")),
                "data": data,
            }
        )
    return result


def run():
    """Print all relevant getters without assigning or saving anything."""

    project = iesve.VEProject.get_current_project()
    model = project.models[0]
    templates = project.thermal_templates(False)
    template_matches = [
        (handle, template)
        for handle, template in templates.items()
        if str(getattr(template, "name", "")) == TEMPLATE_NAME
    ]
    rooms = [
        body
        for body in model.get_bodies(False)
        if str(getattr(body, "name", "")) == ROOM_NAME
    ]
    print("READ-ONLY CASE 600 TEMPLATE READ-BACK INSPECTION")
    print("Project: {}".format(project.name))
    print("Template matches: {}".format(len(template_matches)))
    print("Room matches: {}".format(len(rooms)))
    for handle, template in template_matches:
        print("--- TEMPLATE handle={} ---".format(handle))
        print("name={!r}, standard={!r}".format(
            getattr(template, "name", None),
            getattr(template, "standard", None),
        ))
        print("room_conditions:")
        pprint.pprint(dict(template.get_room_conditions()), width=180)
        print("apache_systems:")
        pprint.pprint(dict(template.get_apache_systems()), width=180)
        print("gains:")
        pprint.pprint(_records(template.get_casual_gains()), width=220)
        print("air_exchanges:")
        pprint.pprint(_records(template.get_air_exchanges()), width=220)
    for body in rooms:
        room_data = body.get_room_data()
        print("--- ROOM id={!r} ---".format(getattr(body, "id", None)))
        print("general:")
        pprint.pprint(dict(room_data.get_general()), width=180)
        print("gains:")
        pprint.pprint(_records(room_data.get_internal_gains()), width=220)
        print("air_exchanges:")
        pprint.pprint(_records(room_data.get_air_exchanges()), width=220)
    print("Inspection complete; no project data was changed or saved.")


if __name__ == "__main__":
    run()
