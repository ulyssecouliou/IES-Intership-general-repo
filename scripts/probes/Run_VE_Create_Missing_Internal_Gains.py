"""Controlled creation/reuse of Swiss reference internal gains only."""

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


def run():
    """Create/reuse and verify only people, lighting, and equipment gains."""

    project = iesve.VEProject.get_current_project()
    project_path = Path(str(project.path))
    manifest = load_asset_manifest(project_path / "reference_model_assets.json")
    provisioner = IesVeAssetProvisioner(iesve, project, None)
    provisioner._preflight_runtime_enums(manifest)
    profile_ids = provisioner._create_profiles(manifest)
    gains, identifiers = provisioner._create_gains(manifest, profile_ids, "")
    if set(gains) != {definition.key for definition in manifest.gains}:
        raise RuntimeError("Not every manifest gain was provisioned")
    print("CONTROLLED INTERNAL-GAIN PROVISIONING: PASS")
    print("Project: {}".format(project.name))
    print("Gain count: {}".format(len(identifiers)))
    print("Identifiers: {!r}".format(identifiers))
    print("No geometry, material, construction, exchange, template or weather was changed.")
    return identifiers


if __name__ == "__main__":
    run()
