"""IESVE Run-button launcher for the guarded Test 2A shade setter probe."""

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

for module_name in tuple(sys.modules):
    if module_name == "swiss_sia.reference_model" or module_name.startswith(
        "swiss_sia.reference_model."
    ):
        del sys.modules[module_name]


def run():
    """Run the one-object setter probe against the active saved VE project."""

    from swiss_sia.reference_model.sia4010.native_ui import (
        ModelBuilderController,
    )
    from swiss_sia.reference_model.sia4010.test2a_shading_qualification import (
        qualify_test2a_shading_setters,
    )
    from swiss_sia.reference_model.ve_api import IesVeGateway

    gateway = IesVeGateway()
    manifest_path = gateway.project_path / "sia4010_external_inputs.json"
    if manifest_path.is_file():
        with manifest_path.open("r", encoding="utf-8") as stream:
            manifest_payload = json.load(stream)
        office_entry = manifest_payload.get("inputs", {}).get(
            "sia2024_office_3_1_standard_profiles", {}
        )
        validation = office_entry.get("technical_validation", {})
        already_prepared = (
            office_entry.get("normative_authorization_status") == "CONFIRMED"
            and validation.get("status") == "PASS"
            and bool(office_entry.get("source_sha256"))
            and bool(validation.get("report_sha256"))
        )
        if already_prepared:
            _path, refreshed, _authorizations = (
                ModelBuilderController.install_prepared_external_input_manifest(
                    gateway.project_path, PROJECT_ROOT
                )
            )
            if refreshed:
                print(
                    "Project evidence manifest refreshed from the "
                    "checksum-bound repository evidence."
                )
    report = qualify_test2a_shading_setters(
        gateway.iesve,
        gateway.project,
        repository_root=PROJECT_ROOT,
    )
    print("CONTROLLED TEST 2A SHADING SETTER QUALIFICATION: PASS")
    print("Project: {}".format(gateway.project.name))
    print("Report: {}".format(report))
    print(
        "No geometry, opening assignment, layer, optical mapping, template, "
        "weather or simulation was changed."
    )
    print(
        "The control semantics and this IESVE mapping are authority-confirmed. "
        "Optical result equivalence remains fail-closed."
    )
    return report


if __name__ == "__main__":
    run()
