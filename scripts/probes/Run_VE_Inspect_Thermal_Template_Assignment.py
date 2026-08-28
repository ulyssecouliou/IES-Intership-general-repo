"""Read-only inspection of thermal-template assignment in generated rooms.

This diagnostic calls getters only.  It does not assign a template, modify
room data, save the project, or invoke any VE mutation method.
"""

import pprint

import iesve


REFERENCE_ROOM_PREFIX = "SIA_REF_ZONE_"


def _thermal_templates(project, assigned):
    """Read templates across the observed one/two-argument VE signatures."""

    last_error = None
    for arguments in ((assigned, False), (assigned,)):
        try:
            return project.thermal_templates(*arguments)
        except Exception as exc:
            last_error = exc
    raise RuntimeError(
        "Unable to read thermal templates with supported signatures: {}".format(
            last_error
        )
    )


def _print_template_collection(label, templates):
    print("{} count: {}".format(label, len(templates)))
    for handle, template in templates.items():
        print(
            "  handle={!r}, name={!r}, id={!r}, python_type={!r}".format(
                handle,
                getattr(template, "name", None),
                getattr(template, "id", None),
                type(template),
            )
        )


def run():
    project = iesve.VEProject.get_current_project()
    model = project.models[0]
    print("Project: {}".format(project.name))
    print("READ-ONLY THERMAL-TEMPLATE ASSIGNMENT INSPECTION")

    all_templates = _thermal_templates(project, False)
    assigned_templates = _thermal_templates(project, True)
    _print_template_collection("All templates", all_templates)
    _print_template_collection("Assigned templates", assigned_templates)

    rooms = [
        body
        for body in model.get_bodies(False)
        if str(getattr(body, "name", "")).startswith(REFERENCE_ROOM_PREFIX)
    ]
    print("Reference rooms found: {}".format(len(rooms)))
    for index, body in enumerate(rooms, start=1):
        room_data = body.get_room_data()
        general = dict(room_data.get_general())
        print("--- room {} ---".format(index))
        print("name: {!r}".format(getattr(body, "name", None)))
        print("id: {!r}".format(getattr(body, "id", None)))
        print("body_python_type: {!r}".format(type(body)))
        print("room_data_python_type: {!r}".format(type(room_data)))
        print("general_keys: {!r}".format(sorted(str(key) for key in general)))
        print("template_related_general_values:")
        pprint.pprint(
            {
                str(key): value
                for key, value in general.items()
                if "template" in str(key).lower()
            },
            width=160,
        )
        print("complete_general_data:")
        pprint.pprint(general, width=160)
        try:
            gains = list(room_data.get_internal_gains())
            print("internal_gain_count: {}".format(len(gains)))
        except Exception as exc:
            print("internal_gain_read_error: {!r}".format(exc))
        try:
            exchanges = list(room_data.get_air_exchanges())
            print("air_exchange_count: {}".format(len(exchanges)))
        except Exception as exc:
            print("air_exchange_read_error: {!r}".format(exc))

    print("Inspection complete; no project data was changed or saved.")


if __name__ == "__main__":
    run()
