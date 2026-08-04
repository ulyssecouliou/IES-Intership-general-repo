"""Apply and verify the remaining ISO Test 1 room runtime input mapping.

This guarded VEScript changes only ``furniture_mass_factor`` on the single
active Test 1 room. Heating and cooling capacities are read and verified but
never rewritten when VE already represents them as unlimited.
"""

import hashlib
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TEST1_CASES = {"600", "640", "900", "940", "600FF", "900FF"}


def _sequence(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return [value]


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def run():
    """Mutate one field only after all source and runtime gates pass."""

    try:
        import iesve  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Run this script from the IESVE VEScripts editor.") from exc

    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.sia4010.test1_runtime_inputs import (
        PROVISIONAL_AIR_SPECIFIC_HEAT_J_KGK,
        PROVISIONAL_DENSITY_SOURCE,
        PROVISIONAL_REFERENCE_AIR_DENSITY_KG_M3,
        build_furniture_condition_payload,
        calculate_furniture_mass_factor,
        validate_capacity_semantics,
    )

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("Open a saved disposable Test 1 project first.")
    project_path = Path(str(getattr(project, "path", "") or ""))
    if not project_path.is_dir():
        raise RuntimeError("Save the disposable VE project before qualification.")
    scenario_path = project_path / "sia_model_scenario.json"
    scenario = ModelScenario.load(scenario_path)
    if scenario.variant != "test_1" or scenario.case_id not in TEST1_CASES:
        raise RuntimeError(
            "Runtime-input qualification supports exact Test 1 cases only; "
            "active case is {}/{}".format(scenario.variant, scenario.case_id)
        )

    models = _sequence(getattr(project, "models", []))
    if not models:
        raise RuntimeError("The active project exposes no VE model.")
    bodies = [
        body
        for body in _sequence(models[0].get_bodies(False))
        if hasattr(body, "get_room_data")
    ]
    expected_name = "SIA4010_TEST_1_{}_ZONE".format(scenario.case_id)
    exact = [body for body in bodies if str(getattr(body, "name", "")) == expected_name]
    if len(exact) != 1:
        raise RuntimeError(
            "Expected exactly one room named {!r}; found {}".format(
                expected_name, len(exact)
            )
        )
    body = exact[0]
    room_data = body.get_room_data()
    general = dict(room_data.get_general())
    before_conditions = dict(room_data.get_room_conditions())
    before_system = dict(room_data.get_apache_systems())
    if not hasattr(room_data, "set_room_conditions"):
        raise RuntimeError("VERoomData.set_room_conditions is unavailable")

    area = general.get("floor_area", general.get("floor_area_m2"))
    volume = general.get("volume", general.get("room_volume"))
    if area is None or volume is None:
        raise RuntimeError("Room area or volume is unavailable")
    if not math.isclose(float(area), 48.0, rel_tol=0.0, abs_tol=1.0e-6):
        raise RuntimeError("Test 1 room floor area is not 48.0 m2")
    if not math.isclose(float(volume), 129.6, rel_tol=0.0, abs_tol=1.0e-6):
        raise RuntimeError("Test 1 room volume is not 129.6 m3")

    density = PROVISIONAL_REFERENCE_AIR_DENSITY_KG_M3
    mapping = calculate_furniture_mass_factor(
        floor_area_m2=float(area),
        room_volume_m3=float(volume),
        reference_air_density_kg_m3=float(density),
        air_specific_heat_j_kgk=PROVISIONAL_AIR_SPECIFIC_HEAT_J_KGK,
    )
    conditioned = bool(before_system.get("conditioned"))
    capacity_receipt = validate_capacity_semantics(
        before_system,
        conditioned=conditioned,
    )

    payload = build_furniture_condition_payload(
        before_conditions, mapping.furniture_mass_factor
    )
    rollback_payload = {
        key: before_conditions[key] for key in payload if key in before_conditions
    }
    restored = False
    try:
        room_data.set_room_conditions(payload)
        after_conditions = dict(room_data.get_room_conditions())
        actual = float(after_conditions.get("furniture_mass_factor"))
        if not math.isclose(
            actual,
            mapping.furniture_mass_factor,
            rel_tol=0.0,
            abs_tol=1.0e-6,
        ):
            raise RuntimeError(
                "Furniture factor read-back mismatch: requested={}, actual={}".format(
                    mapping.furniture_mass_factor, actual
                )
            )
        after_system = dict(room_data.get_apache_systems())
        for key in (
            "heating_capacity_unlimited",
            "heating_capacity_unit",
            "heating_capacity_value",
            "cooling_capacity_unlimited",
            "cooling_capacity_unit",
            "cooling_capacity_value",
        ):
            if before_system.get(key) != after_system.get(key):
                raise RuntimeError(
                    "Unrelated capacity field changed during qualification: {}".format(
                        key
                    )
                )
    except Exception:
        try:
            room_data.set_room_conditions(rollback_payload)
            restored = True
        except Exception:
            restored = False
        raise

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = (
        project_path
        / "sia4010_artifacts"
        / "diagnostics"
        / "sia4010_test1_runtime_input_qualification_{}.json".format(stamp)
    )
    report = {
        "schema_version": "1.0",
        "status": "PROVISIONAL_ENGINE_MAPPING_APPLIED_READY_FOR_SIMULATION",
        "project": {
            "name": str(getattr(project, "name", "") or ""),
            "path": str(project_path),
        },
        "scenario": scenario.to_dict(),
        "scenario_sha256": _sha256(scenario_path),
        "room": {
            "id": str(getattr(body, "id", "")),
            "name": str(getattr(body, "name", "")),
        },
        "mutation": {
            "only_intended_field": "furniture_mass_factor",
            "before": before_conditions.get("furniture_mass_factor"),
            "requested": mapping.furniture_mass_factor,
            "verified_after": actual,
            "restoration_attempted": restored,
        },
        "mapping": mapping.to_dict(),
        "capacity_semantics": capacity_receipt,
        "reference_air_density_binding": {
            "value_kg_m3": density,
            "source": PROVISIONAL_DENSITY_SOURCE,
            "aplocate_opened": False,
        },
        "guardrails": {
            "project_save_called": False,
            "capacity_fields_mutated": False,
            "compliance_claim_allowed": False,
            "remaining_confirmation": (
                "Confirm ApacheSim room-air specific heat with the IES solver "
                "team; current 1005 J/(kg K) is explicitly provisional"
            ),
        },
    }
    _write_json(report_path, report)

    print("SIA 4010 TEST 1 RUNTIME-INPUT QUALIFICATION: {}".format(report["status"]))
    print("Project: {}".format(report["project"]["name"]))
    print("Case: test_1/{}".format(scenario.case_id))
    print(
        "Provisional reference air density: {} kg/m3 (ApLocate not opened)".format(density)
    )
    print("Furniture factor before: {}".format(report["mutation"]["before"]))
    print("Furniture factor verified: {}".format(actual))
    print("Heating/cooling capacity: VE unlimited, unchanged")
    print("Report: {}".format(report_path))
    print("Save the VE project after reviewing the report.")
    return report_path


if __name__ == "__main__":
    run()
