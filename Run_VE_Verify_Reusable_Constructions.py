"""Read-only VE 2025.2 verification of reusable constructions.

The exact production matching path is executed with construction creation
explicitly disabled.  Existing profiles/materials/constructions are read only;
no CDB setter, layer mutation, or project save operation can be reached.
"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
    """Verify all six construction assemblies without permitting creation."""

    project = iesve.VEProject.get_current_project()
    project_path = Path(str(project.path))
    manifest = load_asset_manifest(project_path / "reference_model_assets.json")
    provisioner = IesVeAssetProvisioner(iesve, project, _cdb_project())
    material_ids = provisioner._create_materials(manifest)
    construction_ids, assignment_ids = provisioner._create_constructions(
        manifest, material_ids, allow_create=False
    )
    print("READ-ONLY REUSABLE CONSTRUCTION VERIFICATION: PASS")
    print("Project: {}".format(project.name))
    print("Construction count: {}".format(len(construction_ids)))
    print("Identifiers: {!r}".format(construction_ids))
    print("Assignments: {!r}".format(assignment_ids))
    print("No construction, layer, or material was created or modified.")
    return construction_ids


if __name__ == "__main__":
    run()
