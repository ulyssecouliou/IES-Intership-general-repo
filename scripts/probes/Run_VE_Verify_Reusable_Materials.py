"""Read-only VE 2025.2 verification of reusable reference materials.

The script proves that every manifest material description already exists in
the expected CDB category before exercising the generator's reuse path.  It
therefore cannot call create_material() and does not mutate the active project.
"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

for module_name in tuple(sys.modules):
    if module_name == "swiss_sia.reference_model" or module_name.startswith(
        "swiss_sia.reference_model."
    ):
        del sys.modules[module_name]

import iesve

from swiss_sia.reference_model.asset_manifest import load_asset_manifest
from swiss_sia.reference_model.ve_asset_provisioner import IesVeAssetProvisioner


def _cdb_project():
    database = iesve.VECdbDatabase.get_current_database()
    projects = database.get_projects()
    candidates = projects.get(0, []) if isinstance(projects, dict) else []
    if not candidates:
        raise RuntimeError("Current CDB has no editable project database")
    return candidates[0]


def run():
    """Verify all manifest materials through the generator's reuse code."""

    project = iesve.VEProject.get_current_project()
    project_path = Path(str(project.path))
    manifest = load_asset_manifest(project_path / "reference_model_assets.json")
    cdb_project = _cdb_project()
    provisioner = IesVeAssetProvisioner(iesve, project, cdb_project)

    missing = []
    for definition in manifest.materials:
        category = provisioner._resolve_enum(
            ("VECdbProject.material_categories", "material_categories"),
            (definition.category,),
            "material category",
        )
        description = str(definition.raw_properties().get("description", ""))
        descriptions = []
        for identifier in cdb_project.get_material_ids(category):
            material = cdb_project.get_material(identifier)
            descriptions.append(str(material.get_properties().get("description", "")))
        if description not in descriptions:
            missing.append(description)
    if missing:
        raise RuntimeError(
            "Read-only reuse probe stopped because materials are missing: {}".format(
                sorted(missing)
            )
        )

    identifiers = provisioner._create_materials(manifest)
    print("READ-ONLY REUSABLE MATERIAL VERIFICATION: PASS")
    print("Project: {}".format(project.name))
    print("Material count: {}".format(len(identifiers)))
    print("Identifiers: {!r}".format(identifiers))
    print("No material was created or modified.")
    return identifiers


if __name__ == "__main__":
    run()
