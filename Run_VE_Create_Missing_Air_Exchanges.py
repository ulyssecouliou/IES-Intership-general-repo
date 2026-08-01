"""Controlled creation/reuse of Swiss reference air exchanges only."""

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


def run():
    """Create/reuse and verify only manifest air-exchange records."""

    project = iesve.VEProject.get_current_project()
    project_path = Path(str(project.path))
    manifest = load_asset_manifest(project_path / "reference_model_assets.json")
    provisioner = IesVeAssetProvisioner(iesve, project, None)
    provisioner._preflight_runtime_enums(manifest)
    profile_ids = provisioner._create_profiles(manifest)
    exchanges, names = provisioner._create_air_exchanges(
        manifest, profile_ids, ""
    )
    if set(exchanges) != {definition.key for definition in manifest.air_exchanges}:
        raise RuntimeError("Not every manifest air exchange was provisioned")
    print("CONTROLLED AIR-EXCHANGE PROVISIONING: PASS")
    print("Project: {}".format(project.name))
    print("Air-exchange count: {}".format(len(names)))
    print("Names: {!r}".format(names))
    print("No geometry, material, construction, gain, template or weather was changed.")
    return names


if __name__ == "__main__":
    run()
