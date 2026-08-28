"""Read-only inspection of partially created Swiss reference constructions."""

import pprint

import iesve


def _resolve_container(nested_name, top_level_name):
    nested = getattr(iesve.VECdbProject, nested_name, None)
    return nested or getattr(iesve, top_level_name, None)


def _cdb_project():
    projects = iesve.VECdbDatabase.get_current_database().get_projects()
    candidates = projects.get(0, []) if isinstance(projects, dict) else []
    if not candidates:
        raise RuntimeError("Current CDB has no editable project database")
    return candidates[0]


def _construction(cdb_project, identifier, construction_class):
    for arguments in ((identifier, construction_class), (identifier,)):
        try:
            value = cdb_project.get_construction(*arguments)
            if value is not None:
                return value
        except Exception:
            continue
    return None


def _layer_material_ids(construction):
    """Return all resolvable material IDs without changing the construction."""

    result = []
    opaque = bool(getattr(construction, "opaque", True))
    for layer in construction.get_layers():
        for opaque_flag in (opaque, not opaque):
            try:
                value = str(layer.get_material(opaque_flag))
            except Exception:
                continue
            if value and value not in result:
                result.append(value)
    return result


def run():
    project = iesve.VEProject.get_current_project()
    cdb_project = _cdb_project()
    classes = _resolve_container("construction_class", "construction_class")
    if classes is None:
        raise RuntimeError("construction_class enum is unavailable")

    print("Project: {}".format(project.name))
    print("READ-ONLY CONSTRUCTION INSPECTION")
    found = 0
    for class_name in ("opaque", "glazed"):
        construction_class = getattr(classes, class_name)
        identifiers = list(cdb_project.get_construction_ids(construction_class))
        print("{} construction IDs ({}): {!r}".format(class_name, len(identifiers), identifiers))
        for identifier in identifiers:
            construction = _construction(cdb_project, identifier, construction_class)
            if construction is None:
                continue
            try:
                material_ids = _layer_material_ids(construction)
            except Exception:
                material_ids = []
            properties = {}
            try:
                properties = dict(construction.get_properties())
            except Exception:
                pass
            description = str(properties.get("description", ""))
            generated = (
                str(identifier).upper().startswith("PY")
                or str(identifier).upper() == "WALL"
                or description.startswith("SIA_REF_")
                or any(
                    material_id.upper().startswith(("PYOP", "PYGL"))
                    for material_id in material_ids
                )
            )
            if not generated:
                continue
            found += 1
            print("--- construction {} ---".format(found))
            print("class: {!r}".format(class_name))
            print("id: {!r}".format(identifier))
            print("python_type: {!r}".format(type(construction)))
            print("category: {!r}".format(getattr(construction, "category", None)))
            print("opaque: {!r}".format(getattr(construction, "opaque", None)))
            print("resolved_material_ids: {!r}".format(material_ids))
            try:
                print("properties:")
                pprint.pprint(properties, width=140)
            except Exception as exc:
                print("properties_error: {!r}".format(exc))
            try:
                layers = list(construction.get_layers())
            except Exception as exc:
                print("layers_error: {!r}".format(exc))
                continue
            print("layer_count: {}".format(len(layers)))
            for index, layer in enumerate(layers):
                print("layer[{}].python_type: {!r}".format(index, type(layer)))
                try:
                    print("layer[{}].properties:".format(index))
                    pprint.pprint(dict(layer.get_properties()), width=140)
                except Exception as exc:
                    print("layer[{}].properties_error: {!r}".format(index, exc))
                for opaque_flag in (True, False):
                    try:
                        material = layer.get_material(opaque_flag)
                        print(
                            "layer[{}].get_material({}): {!r}".format(
                                index, opaque_flag, material
                            )
                        )
                    except Exception as exc:
                        print(
                            "layer[{}].get_material({}) error: {!r}".format(
                                index, opaque_flag, exc
                            )
                        )
    print("Reference/Python constructions found: {}".format(found))
    print("Inspection complete; no project data was changed.")


if __name__ == "__main__":
    run()
