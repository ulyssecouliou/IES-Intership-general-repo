"""Repair and resume an existing Case 600 room without importing geometry.

Run this only in the disposable VE project whose Case 600 geometry is already
imported. It replaces non-portable custom DAY_* references with persistent ON,
rebuilds the source-traced package, verifies the window, and reapplies the
template content at room level. No gbXML is imported again.
"""

import json
import sys
from pathlib import Path

import iesve


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPOSITORY_ROOT) in sys.path:
    sys.path.remove(str(REPOSITORY_ROOT))
sys.path.insert(0, str(REPOSITORY_ROOT))

# VE retains imported modules between Run-button executions.
for module_name in tuple(sys.modules):
    if (
        module_name == "Run_VE_Calibrate_External_Glazing_UValue"
        or module_name == "swiss_sia"
        or module_name.startswith("swiss_sia.")
    ):
        del sys.modules[module_name]


EXPECTED_ROOM_NAME = "SIA4010_TEST_1_600_ZONE"
EXPECTED_SCENARIO_ID = "SIA4010_1A_600"
WEATHER_FILENAME = "DRYCOLD_IESVE.epw"


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _is_room(body):
    try:
        return body.type == iesve.VEBody.VEBody_type.room
    except Exception:
        return str(getattr(body, "type", "")).casefold().endswith("room")


def run():
    """Repair the interrupted asset, then resume without geometry import."""

    from swiss_sia.reference_model.asset_manifest import load_asset_manifest
    from swiss_sia.reference_model.config_loader import load_configuration
    from swiss_sia.reference_model.sia4010.case_geometry import (
        Sia4010CellGeometryGenerator,
        validate_cell_geometry,
    )
    from swiss_sia.reference_model.sia4010.case_manifest import (
        Sia4010CaseManifest,
    )
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.sia4010.mvp_bundle import (
        build_case600_mvp_bundle,
    )
    from swiss_sia.reference_model.sia4010.scenario_preflight import (
        evaluate_scenario,
    )
    from swiss_sia.reference_model.ve_api import IesVeGateway
    from swiss_sia.reference_model.workflow import ReferenceModelWorkflow

    print("SIA 4010 CASE 600 - PORTABLE PROFILE REPAIR AND RESUME")
    gateway = IesVeGateway()
    project_path = gateway.project_path
    rooms = [
        body
        for body in gateway.model.get_bodies(False)
        if _is_room(body)
    ]
    matching_rooms = [
        body
        for body in rooms
        if str(getattr(body, "name", "")) == EXPECTED_ROOM_NAME
    ]
    if len(rooms) != 1 or len(matching_rooms) != 1:
        raise RuntimeError(
            "Safety gate: expected exactly one existing Case 600 room named "
            "'{}'; found rooms={} matching={}. No mutation was attempted.".format(
                EXPECTED_ROOM_NAME, len(rooms), len(matching_rooms)
            )
        )

    scenario_path = project_path / "sia_model_scenario.json"
    scenario = ModelScenario.load(scenario_path)
    if scenario.scenario_id != EXPECTED_SCENARIO_ID:
        raise RuntimeError(
            "Safety gate: expected scenario '{}', found '{}'.".format(
                EXPECTED_SCENARIO_ID, scenario.scenario_id
            )
        )
    weather_path = project_path / WEATHER_FILENAME
    if not weather_path.is_file():
        raise RuntimeError(
            "Verified IESVE weather file is missing: {}".format(weather_path)
        )

    print("Step 1/5 - rebuild corrected source-traced Case 600 bundle")
    bundle = build_case600_mvp_bundle(
        project_path, REPOSITORY_ROOT, weather_path
    )
    preflight = evaluate_scenario(
        scenario, project_path, REPOSITORY_ROOT
    )
    if not preflight.allows_mutation:
        raise RuntimeError(
            "Corrected Case 600 preflight blocked resume: {}".format(
                "; ".join(preflight.blockers)
            )
        )

    case_manifest = Sia4010CaseManifest.load(bundle.case_manifest_path)
    geometry = Sia4010CellGeometryGenerator(case_manifest).generate(
        identifier="SIA4010_TEST_1_600"
    )
    geometry_validation = validate_cell_geometry(geometry, case_manifest)
    if not geometry_validation.passed:
        raise RuntimeError(
            "Corrected Case 600 geometry contract failed: {}".format(
                geometry_validation.checks
            )
        )

    print("Step 2/5 - replace every volatile DAY_* asset reference with ON")
    asset_manifest = load_asset_manifest(bundle.asset_manifest_path)
    repaired_gains = {
        key: gateway.reconcile_existing_gain(asset_manifest, key)
        for key in ("people_gain", "lighting_gain", "equipment_gain")
    }
    repaired_exchanges = {
        key: gateway.reconcile_existing_air_exchange(asset_manifest, key)
        for key in ("infiltration", "outdoor_air")
    }
    repair_path = (
        project_path
        / "sia4010_artifacts"
        / "diagnostics"
        / "case600_portable_profile_repair.json"
    )
    _write_json(
        repair_path,
        {
            "schema_version": "1.0",
            "scenario_id": scenario.scenario_id,
            "scope": "GLOBAL_GAINS_AND_AIR_EXCHANGES_TO_BUILTIN_ON",
            "geometry_imported": False,
            "profiles_created": False,
            "gain_receipts": repaired_gains,
            "air_exchange_receipts": repaired_exchanges,
        },
    )
    print("Portable profile repair: PASS")

    print("Step 3/5 - calibrate and verify the VE whole-window U-value")
    from Run_VE_Calibrate_External_Glazing_UValue import (
        run as calibrate_external_glazing,
    )

    calibrate_external_glazing()

    print("Step 4/5 - resume assignments without importing geometry")
    parameters = load_configuration(bundle.config_path).with_overrides(
        {
            "asset_provisioning_mode": {
                "value": "create",
                "source": "Controlled Case 600 resume",
                "source_locator": str(scenario_path),
            },
            "asset_manifest_file": {
                "value": str(bundle.asset_manifest_path),
                "source": "Controlled Case 600 resume",
                "source_locator": str(scenario_path),
            },
        }
    )
    workflow = ReferenceModelWorkflow(
        parameters,
        gateway,
        geometry_factory=lambda: geometry,
        geometry_artifact_name="SIA4010_1A_600.gbxml",
    )
    outcome = workflow.run(dry_run=False, resume_after_import=True)

    print("Step 5/5 - report")
    print(outcome.message)
    print("Status: {}".format(outcome.status.value))
    print("Portable profile repair report: {}".format(repair_path))
    print("Audit report: {}".format(outcome.artifacts.report_json))
    return outcome


if __name__ == "__main__":
    run()
