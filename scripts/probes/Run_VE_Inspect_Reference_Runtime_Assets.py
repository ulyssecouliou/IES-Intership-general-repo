"""Read-only inspection of Swiss reference gains, exchanges, and templates."""

import pprint

import iesve


REFERENCE_PREFIX = "SIA_REF_"


def _record_data(record):
    try:
        return dict(record.get())
    except Exception as exc:
        return {"inspection_error": repr(exc)}


def _reference_records(records):
    result = []
    for record in records:
        data = _record_data(record)
        name = str(data.get("name", getattr(record, "name", "")))
        if name.startswith(REFERENCE_PREFIX):
            result.append((record, data))
    return result


def _public_members(value):
    """Return non-callable public enum/container members."""

    result = {}
    if value is None:
        return result
    for name in dir(value):
        if name.startswith("_"):
            continue
        try:
            member = getattr(value, name)
        except Exception as exc:
            result[name] = "<error: {}>".format(exc)
            continue
        if not callable(member):
            result[name] = repr(member)
    return result


def _resolve_path(path):
    current = iesve
    for part in path.split("."):
        if not hasattr(current, part):
            return None
        current = getattr(current, part)
    return current


def _thermal_templates(project):
    errors = []
    for arguments in ((False, False), (False,)):
        try:
            return project.thermal_templates(*arguments)
        except Exception as exc:
            errors.append("{}: {}".format(arguments, exc))
    raise RuntimeError("thermal_templates failed: {}".format(" | ".join(errors)))


def run():
    project = iesve.VEProject.get_current_project()
    print("Project: {}".format(project.name))
    print("READ-ONLY RUNTIME-ASSET INSPECTION")

    print("create_casual_gain.__doc__: {!r}".format(project.create_casual_gain.__doc__))
    print("create_air_exchange.__doc__: {!r}".format(project.create_air_exchange.__doc__))
    for path in (
        "CasualGain.CasualGain_type",
        "CasualGain_type",
        "PeopleGain.PeopleGain_type",
        "PeopleGain_type",
        "LightingGain.LightingGain_type",
        "LightingGain_type",
        "EnergyGain.EnergyGain_type",
        "EnergyGain_type",
        "AirExchange.AirExchange_type",
        "AirExchange_type",
        "AirExchange.AdjacentCondition_type",
        "AdjacentCondition_type",
        "AirExchange.AirChange_unit",
        "AirChange_unit",
    ):
        value = _resolve_path(path)
        if value is not None:
            print("{} members:".format(path))
            pprint.pprint(_public_members(value), width=140)

    all_gains = list(project.casual_gains())
    print("All casual gains found: {}".format(len(all_gains)))
    for index, gain in enumerate(all_gains, start=1):
        print("--- all gain {} ---".format(index))
        print("python_type: {!r}".format(type(gain)))
        print("id: {!r}".format(getattr(gain, "id", None)))
        print("set.__doc__: {!r}".format(getattr(gain, "set", None).__doc__ if hasattr(gain, "set") else None))
        pprint.pprint(_record_data(gain), width=140)

    gains = _reference_records(all_gains)
    print("Reference gains found: {}".format(len(gains)))
    for index, (gain, data) in enumerate(gains, start=1):
        print("--- gain {} ---".format(index))
        print("python_type: {!r}".format(type(gain)))
        print("id: {!r}".format(getattr(gain, "id", None)))
        pprint.pprint(data, width=140)

    all_exchanges = list(project.air_exchanges())
    print("All air exchanges found: {}".format(len(all_exchanges)))
    for index, exchange in enumerate(all_exchanges, start=1):
        print("--- all air exchange {} ---".format(index))
        print("python_type: {!r}".format(type(exchange)))
        print("id: {!r}".format(getattr(exchange, "id", None)))
        print("set.__doc__: {!r}".format(getattr(exchange, "set", None).__doc__ if hasattr(exchange, "set") else None))
        pprint.pprint(_record_data(exchange), width=140)

    exchanges = _reference_records(all_exchanges)
    print("Reference air exchanges found: {}".format(len(exchanges)))
    for index, (exchange, data) in enumerate(exchanges, start=1):
        print("--- air exchange {} ---".format(index))
        print("python_type: {!r}".format(type(exchange)))
        print("id: {!r}".format(getattr(exchange, "id", None)))
        pprint.pprint(data, width=140)

    templates = [
        (handle, template)
        for handle, template in _thermal_templates(project).items()
        if str(getattr(template, "name", "")).startswith("SIA")
    ]
    print("Reference thermal templates found: {}".format(len(templates)))
    for index, (handle, template) in enumerate(templates, start=1):
        print("--- thermal template {} ---".format(index))
        print("handle: {!r}".format(handle))
        print("name: {!r}".format(getattr(template, "name", None)))
        print("python_type: {!r}".format(type(template)))
        for method_name in (
            "get_room_conditions",
            "get_apache_systems",
            "get_casual_gains",
            "get_air_exchanges",
        ):
            try:
                value = getattr(template, method_name)()
                print("{}:".format(method_name))
                pprint.pprint(value, width=140)
            except Exception as exc:
                print("{}_error: {!r}".format(method_name, exc))

    print("Inspection complete; no project data was changed.")


if __name__ == "__main__":
    run()
