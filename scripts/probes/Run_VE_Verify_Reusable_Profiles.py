"""Read-only VE 2025.2 verification of reusable reference profiles.

This diagnostic exercises the exact generator profile-reuse path, but first
proves that every requested profile already exists.  Consequently the path
cannot call create_profile() or save_profiles().  It is intended to isolate a
native Boost.Python host crash without mutating the active VE project.
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


def run():
    """Verify all manifest profiles through the generator's reuse code."""

    project = iesve.VEProject.get_current_project()
    project_path = Path(str(project.path))
    manifest = load_asset_manifest(project_path / "reference_model_assets.json")
    requested = {definition.reference for definition in manifest.profiles}
    existing = set()
    for collection in project.profiles():
        for profile in collection.values():
            reference = getattr(profile, "reference", getattr(profile, "name", ""))
            if reference:
                existing.add(str(reference))
    missing = sorted(requested - existing)
    if missing:
        raise RuntimeError(
            "Read-only reuse probe stopped because profiles are missing: {}".format(
                missing
            )
        )
    provisioner = IesVeAssetProvisioner(iesve, project, None)
    identifiers = provisioner._create_profiles(manifest)
    print("READ-ONLY REUSABLE PROFILE VERIFICATION: PASS")
    print("Project: {}".format(project.name))
    print("Identifiers: {!r}".format(identifiers))
    print("No profile was created or saved.")
    return identifiers


if __name__ == "__main__":
    run()
