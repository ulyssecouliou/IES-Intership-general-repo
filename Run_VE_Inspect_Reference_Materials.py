"""Read-only inspection of partially created Swiss reference CDB materials."""

import pprint

import iesve


REFERENCE_PREFIX = "SIA_REF_"


def _enum_container():
    nested = getattr(iesve.VECdbProject, "material_categories", None)
    return nested or getattr(iesve, "material_categories", None)


def run():
    project = iesve.VEProject.get_current_project()
    projects = iesve.VECdbDatabase.get_current_database().get_projects()
    candidates = projects.get(0, []) if isinstance(projects, dict) else []
    if not candidates:
        raise RuntimeError("Current CDB has no editable project database")
    cdb_project = candidates[0]
    categories = _enum_container()
    if categories is None or not hasattr(categories, "all"):
        raise RuntimeError("material_categories.all is unavailable")

    print("Project: {}".format(project.name))
    print("READ-ONLY MATERIAL INSPECTION")
    found = 0
    for material_id in cdb_project.get_material_ids(categories.all):
        try:
            material = cdb_project.get_material(material_id)
            properties = dict(material.get_properties())
        except Exception:
            continue
        description = str(properties.get("description", ""))
        if not description.startswith(REFERENCE_PREFIX):
            continue
        found += 1
        print("--- material {} ---".format(found))
        print("material_id: {!r}".format(material_id))
        print("python_type: {!r}".format(type(material)))
        print("category: {!r}".format(getattr(material, "category", None)))
        print("property_keys: {!r}".format(sorted(str(key) for key in properties)))
        print("properties:")
        pprint.pprint(properties, width=140)
    print("Reference materials found: {}".format(found))
    print("Inspection complete; no project data was changed.")


if __name__ == "__main__":
    run()
