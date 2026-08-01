"""Focused read-only inspection of glazed construction candidates in VE."""

import pprint

import iesve


def _enum_container(nested_name, top_level_name):
    return getattr(iesve.VECdbProject, nested_name, None) or getattr(
        iesve, top_level_name, None
    )


def _cdb_project():
    projects = iesve.VECdbDatabase.get_current_database().get_projects()
    candidates = projects.get(0, []) if isinstance(projects, dict) else []
    if not candidates:
        raise RuntimeError("Current CDB has no editable project database")
    return candidates[0]


def _construction(cdb_project, identifier, construction_class):
    for arguments in ((identifier, construction_class), (identifier,)):
        try:
            result = cdb_project.get_construction(*arguments)
            if result is not None:
                return result
        except Exception:
            continue
    return None


def run():
    project = iesve.VEProject.get_current_project()
    cdb_project = _cdb_project()
    classes = _enum_container("construction_class", "construction_class")
    categories = _enum_container("element_categories", "element_categories")
    glazed = classes.glazed
    print("Project: {}".format(project.name))
    print("READ-ONLY EXTERNAL-GLAZING CONSTRUCTION INSPECTION")
    print("expected_category: {!r}".format(categories.ext_glazing))
    identifiers = list(cdb_project.get_construction_ids(glazed))
    print("glazed_ids: {!r}".format(identifiers))
    for identifier in identifiers:
        construction = _construction(cdb_project, identifier, glazed)
        if construction is None:
            continue
        print("--- candidate {!r} ---".format(identifier))
        print("category: {!r}".format(getattr(construction, "category", None)))
        try:
            print("properties:")
            pprint.pprint(dict(construction.get_properties()), width=150)
        except Exception as exc:
            print("properties_error: {!r}".format(exc))
        layers = list(construction.get_layers())
        print("layer_count: {}".format(len(layers)))
        for index, layer in enumerate(layers):
            print("layer[{}].properties:".format(index))
            pprint.pprint(dict(layer.get_properties()), width=150)
            for opaque_flag in (False, True):
                try:
                    material = layer.get_material(opaque_flag)
                    if material is None:
                        print("layer[{}].material({}): None".format(index, opaque_flag))
                        continue
                    material_properties = dict(material.get_properties())
                    print(
                        "layer[{}].material({}): id={!r}, description={!r}, category={!r}".format(
                            index,
                            opaque_flag,
                            material_properties.get("id"),
                            material_properties.get("description"),
                            material_properties.get("category"),
                        )
                    )
                except Exception as exc:
                    print(
                        "layer[{}].material({}) error: {!r}".format(
                            index, opaque_flag, exc
                        )
                    )
    print("Inspection complete; no project data was changed.")


if __name__ == "__main__":
    run()
