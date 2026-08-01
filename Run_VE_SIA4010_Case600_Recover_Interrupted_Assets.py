"""Controlled recovery after an interrupted Case 600 asset-provisioning run.

The script is intentionally narrow:

* the active scenario must be SIA4010_1A_600;
* no room may exist yet (the interruption happened before gbXML import);
* only the exact-name non-zero equipment gain is reconciled;
* the corrected gain is read back before the normal guarded workflow resumes.
"""

import json
import sys
from pathlib import Path

import iesve


REPOSITORY_ROOT = Path(__file__).resolve().parent
if str(REPOSITORY_ROOT) in sys.path:
    sys.path.remove(str(REPOSITORY_ROOT))
sys.path.insert(0, str(REPOSITORY_ROOT))

for module_name in tuple(sys.modules):
    if (
        module_name == "Run_VE_SIA_Model_Builder"
        or module_name == "swiss_sia"
        or module_name.startswith("swiss_sia.")
    ):
        del sys.modules[module_name]


EXPECTED_SCENARIO_ID = "SIA4010_1A_600"
WEATHER_FILENAME = "DRYCOLD_IESVE.epw"


def _is_room(body):
    """Return whether one VE body is a thermal room."""

    try:
        return body.type == iesve.VEBody.VEBody_type.room
    except Exception:
        return str(getattr(body, "type", "")).casefold().endswith("room")


def _write_json(path, payload):
    """Atomically write one recovery audit artifact."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def run():
    """Repair the interrupted gain and resume the normal Case 600 workflow."""

    from swiss_sia.reference_model.asset_manifest import load_asset_manifest
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.sia4010.mvp_bundle import (
        build_case600_mvp_bundle,
    )
    from swiss_sia.reference_model.ve_api import IesVeGateway

    print("SIA 4010 CASE 600 - CONTROLLED ASSET RECOVERY")
    gateway = IesVeGateway()
    project_path = gateway.project_path
    rooms = [
        body for body in gateway.model.get_bodies(False) if _is_room(body)
    ]
    if rooms:
        raise RuntimeError(
            "Safety gate: expected no room before asset recovery; found {}. "
            "No mutation was attempted.".format(len(rooms))
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

    print("Step 1/4 - rebuild the source-traced Case 600 bundle")
    bundle = build_case600_mvp_bundle(
        project_path, REPOSITORY_ROOT, weather_path
    )
    manifest = load_asset_manifest(bundle.asset_manifest_path)

    print("Step 2/4 - reconcile the exact non-zero equipment gain")
    gain_receipt = gateway.reconcile_existing_gain(
        manifest, "equipment_gain"
    )
    if gain_receipt["status"] not in {
        "ALREADY_MATCHED",
        "RECONCILED_AND_VERIFIED",
    }:
        raise RuntimeError(
            "Equipment-gain recovery did not reach a verified state: {}".format(
                gain_receipt
            )
        )
    print("Gain recovery: {}".format(gain_receipt["status"]))

    print("Step 3/4 - reconcile the exact non-zero infiltration exchange")
    exchange_receipt = gateway.reconcile_existing_air_exchange(
        manifest, "infiltration"
    )
    if exchange_receipt["status"] not in {
        "NOT_PRESENT",
        "ALREADY_MATCHED",
        "RECONCILED_AND_VERIFIED",
    }:
        raise RuntimeError(
            "Infiltration recovery did not reach a verified state: {}".format(
                exchange_receipt
            )
        )
    print("Air-exchange recovery: {}".format(exchange_receipt["status"]))

    report_path = (
        project_path
        / "sia4010_artifacts"
        / "diagnostics"
        / "case600_interrupted_asset_recovery.json"
    )
    _write_json(
        report_path,
        {
            "schema_version": "1.0",
            "scenario_id": scenario.scenario_id,
            "scope": (
                "EXACT_NAME_NONZERO_EQUIPMENT_GAIN_AND_"
                "INFILTRATION_EXCHANGE_ONLY"
            ),
            "room_count_before_recovery": 0,
            "geometry_imported_by_recovery_step": False,
            "gain_receipt": gain_receipt,
            "air_exchange_receipt": exchange_receipt,
        },
    )
    print("Recovery report: {}".format(report_path))

    print("Step 4/4 - resume the normal guarded Model Builder workflow")
    # Import only after reconciliation: the launcher's hot-reload guard clears
    # project modules, and its run() creates a fresh VE gateway for the resume.
    import Run_VE_SIA_Model_Builder as model_builder

    return model_builder.run()


if __name__ == "__main__":
    run()
