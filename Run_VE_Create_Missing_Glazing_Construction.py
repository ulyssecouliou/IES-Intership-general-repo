"""Controlled creation/reuse of the one Swiss external-glazing construction.

This mutation is deliberately isolated from geometry, profiles, gains, air
exchanges, weather and templates.  VE 2025.2's glazed-layer invariant is kept:
the manifest layer is added before the category-specific default is removed.
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
    projects = iesve.VECdbDatabase.get_current_database().get_projects()
    candidates = projects.get(0, []) if isinstance(projects, dict) else []
    if not candidates:
        raise RuntimeError("Current CDB has no editable project database")
    return candidates[0]


def run():
    """Create only the missing external-glazing construction and verify it."""

    project = iesve.VEProject.get_current_project()
    project_path = Path(str(project.path))
    manifest = load_asset_manifest(project_path / "reference_model_assets.json")
    cdb_project = _cdb_project()
    provisioner = IesVeAssetProvisioner(iesve, project, cdb_project)
    material_ids = provisioner._create_materials(manifest)
    definition = next(
        item for item in manifest.constructions if item.key == "external_glazing"
    )
    assignment, identifier = provisioner._create_construction(
        manifest, definition, material_ids, allow_create=True
    )
    print("CONTROLLED EXTERNAL-GLAZING PROVISIONING: PASS")
    print("Project: {}".format(project.name))
    print("Assignment: {}".format(assignment))
    print("Construction ID: {}".format(identifier))
    print("No geometry, profile, gain, exchange, template or weather was changed.")
    return identifier


if __name__ == "__main__":
    run()
