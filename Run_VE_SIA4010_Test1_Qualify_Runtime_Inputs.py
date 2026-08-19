"""Apply and verify the remaining ISO Test 1 room runtime input mapping.

This guarded VEScript always changes the ISO room-capacity mapping.  For a
conditioned case it also qualifies the two ideal-load emission fractions; for
a free-floating case it deliberately leaves all ideal-load fields untouched.
Heating and cooling capacities are read and verified but never rewritten.
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

TEST1_CASES = {
    "600",
    "640",
    "900",
    "940",
    "600FF",
    "900FF",
    "1A",
    "1B",
    "1C",
    "1D",
}


def _reload_reference_model_package():
    """Drop the cached repository package before importing it from disk.

    VEScripts keeps one Python interpreter alive between Run-button presses, so
    a module imported by an earlier run stays in ``sys.modules`` even after its
    source file changes.  Pressing this launcher on its own therefore used to
    import a stale ``test1_runtime_inputs`` and fail with ``ImportError`` on a
    newly added helper.  Only this repository package is dropped; the native
    ``iesve`` extension and the active VE project are untouched.

    This runs when the operator executes the launcher, not at import time, so
    importing this module from a test never invalidates classes another module
    already holds.
    """

    for module_name in tuple(sys.modules):
        if module_name == "swiss_sia.reference_model" or module_name.startswith(
            "swiss_sia.reference_model."
        ):
            del sys.modules[module_name]


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
    """Mutate only the runtime fields applicable to the active Test 1 case."""

    _reload_reference_model_package()
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
        build_ideal_load_system_payload,
        build_zero_mechanical_ventilation_payload,
        calculate_furniture_mass_factor,
        is_conditioned_state,
        is_off_profile,
        validate_capacity_semantics,
        validate_ideal_load_emission_semantics,
        validate_prescribed_infiltration_preserved,
        validate_zero_mechanical_ventilation_semantics,
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
    conditioned = scenario.case_id not in {"600FF", "900FF"}
    free_floating_controls = None
    if conditioned:
        if not is_conditioned_state(before_system.get("conditioned")):
            raise RuntimeError(
                "Conditioned Test 1 case is not conditioned in the live VE room"
            )
    else:
        free_floating_controls = {
            key: before_conditions.get(key)
            for key in ("heating_profile", "cooling_profile")
        }
        if not all(is_off_profile(value) for value in free_floating_controls.values()):
            raise RuntimeError(
                "Free-floating Test 1 case requires live heating_profile=OFF "
                "and cooling_profile=OFF; read-back={}".format(
                    free_floating_controls
                )
            )
    capacity_receipt = validate_capacity_semantics(
        before_system,
        conditioned=conditioned,
    )

    payload = build_furniture_condition_payload(
        before_conditions, mapping.furniture_mass_factor
    )
    system_payload = build_zero_mechanical_ventilation_payload(before_system)
    if conditioned:
        system_payload.update(build_ideal_load_system_payload(before_system))
    rollback_payload = {
        key: before_conditions[key] for key in payload if key in before_conditions
    }
    system_rollback_payload = {
        key: before_system[key] for key in system_payload if key in before_system
    }
    restored = False
    try:
        room_data.set_room_conditions(payload)
        if system_payload:
            room_data.set_apache_systems(system_payload)
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
        ventilation_receipt = validate_zero_mechanical_ventilation_semantics(
            after_system
        )
        # Zeroing the Apache system outdoor-air flow must never also remove or
        # zero the ISO clause 7.2.2.14 infiltration: read it back separately.
        infiltration_receipt = validate_prescribed_infiltration_preserved(
            room_data.get_air_exchanges()
        )
        if conditioned:
            emission_receipt = validate_ideal_load_emission_semantics(after_system)
        else:
            emission_receipt = {
                "applicable": False,
                "verified": True,
                "reason": (
                    "Free-floating Test 1 cases have no ideal heating or "
                    "cooling emission to qualify"
                ),
            }
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
            if system_rollback_payload:
                room_data.set_apache_systems(system_rollback_payload)
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
            "intended_fields": (
                [
                    "furniture_mass_factor",
                    "system_air_minimum_flowrate",
                    "heating_plant_radiant_fraction",
                    "cooling_plant_radiant_fraction",
                ]
                if conditioned
                else [
                    "furniture_mass_factor",
                    "system_air_minimum_flowrate",
                ]
            ),
            "before": before_conditions.get("furniture_mass_factor"),
            "requested": mapping.furniture_mass_factor,
            "verified_after": actual,
            "system_before": {
                key: before_system.get(key)
                for key in (
                    "heating_plant_radiant_fraction",
                    "cooling_plant_radiant_fraction",
                )
            },
            "system_verified_after": emission_receipt,
            "mechanical_ventilation_verified_after": ventilation_receipt,
            "prescribed_infiltration_verified_after": infiltration_receipt,
            # The keys actually submitted to set_apache_systems, as opposed to
            # ``intended_fields`` above which is a fixed expectation. A
            # template-inheritance flag only appears here when this VE release
            # exposes it on room read-back, so a reviewer can tell "inheritance
            # disabled" apart from "inheritance not exposed by VE".
            "applied_system_payload_keys": sorted(system_payload),
            "applied_room_condition_payload_keys": sorted(payload),
            "restoration_attempted": restored,
        },
        "mapping": mapping.to_dict(),
        "capacity_semantics": capacity_receipt,
        "free_floating_controls": (
            {
                "applicable": True,
                "expected": {
                    "heating_profile": "OFF",
                    "cooling_profile": "OFF",
                },
                "verified_after": free_floating_controls,
                "verified": True,
                "conditioned_readback_advisory": before_system.get("conditioned"),
            }
            if not conditioned
            else {"applicable": False, "verified": True}
        ),
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
    print(
        "Mechanical ventilation: {:.6g} L/s/person, verified zero".format(
            ventilation_receipt["ve_system_air_minimum_flowrate"]
        )
    )
    print(
        "Prescribed infiltration: {:.6g} (VE units_val={}), verified retained".format(
            infiltration_receipt["ve_infiltration_max_flow"],
            infiltration_receipt["ve_infiltration_units_val"],
        )
    )
    print(
        "Other air exchanges: {} present, all verified zero".format(
            len(infiltration_receipt["ve_other_air_exchanges"])
        )
    )
    print(
        "Template inheritance keys accepted by this VE build: {}".format(
            ", ".join(
                key
                for key in report["mutation"]["applied_system_payload_keys"]
                if key.endswith("_from_template")
            )
            or "none exposed on room read-back"
        )
    )
    if conditioned:
        print("Heating/cooling emission: fully convective, verified")
        print("Heating/cooling capacity: VE unlimited, unchanged")
    else:
        print("Heating/cooling emission: not applicable (free floating)")
        print("Heating/cooling capacity: not applicable, unchanged")
    print("Report: {}".format(report_path))
    print("Save the VE project after reviewing the report.")
    return report_path


if __name__ == "__main__":
    run()
