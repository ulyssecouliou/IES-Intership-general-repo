"""Qualify an equivalent Test 2A base-glazing U-value in disposable VE CDB.

The fixed-closed optical probe creates one unassigned glazed construction and
proves that the Test 2A threshold and direct optical fields can coexist.  This
module reuses that exact object, changes only its single native layer thermal
resistance, and solves it against VE's ISO U-factor read-back.  The target is
the source-traced base-glazing value (0.654 W/(m2 K)); the separate combined
glazing-plus-awning value is deliberately not inferred.

A PASS is an engine-storage qualification for an equivalent layer only.  It
does not prove the manufacturer's 4/14/4/14/4 layer build-up, the awning's
thermal contribution, a final opening assignment, dynamic behaviour, an APS
result, or SIA compliance.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

from ..exceptions import ConfigurationError, VeMutationError
from ..ve_api import IesVeGateway
from .model_scenario import ModelScenario
from .official_input_contract import Sia4010OfficialInputContract
from .scenario_preflight import is_temporary_ve_project


REPORT_DIRECTORY = Path("sia4010_artifacts") / "diagnostics"
SCENARIO_FILENAME = "sia_model_scenario.json"
MUTATION_SCOPE = "ONE_UNASSIGNED_GLAZED_CDB_LAYER_RESISTANCE"
DEFAULT_QA_TOLERANCE_W_M2K = 0.001


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _load_combined_optical_report(project_path: Path) -> Tuple[Path, Dict[str, Any]]:
    """Load the sole checksummed combined threshold/optical prerequisite."""

    reports = sorted(
        (project_path / REPORT_DIRECTORY).glob("sia2a_2e1_optical_setter_*.json")
    )
    if len(reports) != 1:
        raise ConfigurationError(
            "Thermal glazing qualification requires exactly one optical setter "
            "report; found {}".format(len(reports))
        )
    report_path = reports[0]
    checksum_path = report_path.with_suffix(report_path.suffix + ".sha256")
    if not checksum_path.is_file():
        raise ConfigurationError(
            "Optical setter checksum is missing: {}".format(checksum_path)
        )
    expected_sha = checksum_path.read_text(encoding="ascii").split()[0].lower()
    if expected_sha != _sha256(report_path):
        raise ConfigurationError("Optical setter report checksum mismatch")
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    setter = payload.get("setter_result", {})
    if (
        payload.get("status") != "PASS"
        or payload.get("fixed_closed_storage_qualified") is not True
        or payload.get("combined_threshold_optical_storage_qualified") is not True
        or setter.get("threshold_and_optical_fields_co_stored") is not True
    ):
        raise ConfigurationError(
            "Optical prerequisite does not prove combined threshold/optical storage"
        )
    construction_id = str(setter.get("construction_id", "")).strip()
    if not construction_id:
        raise ConfigurationError("Optical prerequisite has no construction ID")
    return report_path, payload


def _solve_equivalent_resistance(
    layer: Any,
    construction: Any,
    uvalue_type: Any,
    target_u: float,
    qa_tolerance: float,
) -> Dict[str, float]:
    """Biselect one layer resistance against VE's native ISO U-factor."""

    def evaluate(requested: float) -> Tuple[float, float]:
        layer.set_properties({"resistance": requested})
        persisted = float(dict(layer.get_properties())["resistance"])
        u_value = float(construction.get_u_factor(uvalue_type))
        if not math.isfinite(persisted) or not math.isfinite(u_value):
            raise VeMutationError("VE returned a non-finite glazing value")
        return persisted, u_value

    lower = 0.000001
    upper = 20.0
    _, u_lower = evaluate(lower)
    _, u_upper = evaluate(upper)
    if not (u_lower > target_u > u_upper):
        raise VeMutationError(
            "Base-glazing U target is not bracketed: target={}, U({})={}, "
            "U({})={}".format(target_u, lower, u_lower, upper, u_upper)
        )
    final_resistance = lower
    final_u = u_lower
    solve_tolerance = max(qa_tolerance / 10.0, 0.000001)
    for _ in range(64):
        midpoint = (lower + upper) / 2.0
        final_resistance, final_u = evaluate(midpoint)
        if abs(final_u - target_u) <= solve_tolerance:
            break
        if final_u > target_u:
            lower = midpoint
        else:
            upper = midpoint
    if abs(final_u - target_u) > qa_tolerance:
        raise VeMutationError(
            "Equivalent glazing calibration failed: target={}, actual={}".format(
                target_u, final_u
            )
        )
    return {
        "requested_target_u_w_m2k": target_u,
        "verified_iso_u_w_m2k": final_u,
        "absolute_difference_w_m2k": abs(final_u - target_u),
        "equivalent_layer_resistance_m2k_w": final_resistance,
        "qa_tolerance_w_m2k": qa_tolerance,
    }


def qualify_test2a_base_glazing_thermal_storage(
    iesve_module: Any,
    project: Any,
    repository_root: Optional[Path] = None,
    gateway_factory: Callable[..., Any] = IesVeGateway,
) -> Path:
    """Calibrate/read back the source-bound Test 2A base-glazing U-value."""

    project_path = Path(str(getattr(project, "path", "") or ""))
    if not project_path.is_dir() or is_temporary_ve_project(project_path):
        raise ConfigurationError(
            "Save a fresh disposable VE project outside temporary VEPROJ first"
        )
    scenario_path = project_path / SCENARIO_FILENAME
    scenario = ModelScenario.load(scenario_path)
    if (
        not scenario.is_official
        or scenario.variant != "test_2A"
        or scenario.case_id != "2A"
    ):
        raise ConfigurationError(
            "Thermal glazing qualification is restricted to official test_2A/2A"
        )
    existing = sorted(
        (project_path / REPORT_DIRECTORY).glob("sia2a_thermal_glazing_*.json")
    )
    if existing:
        raise ConfigurationError(
            "Thermal glazing qualification already exists; use a fresh disposable "
            "project: {}".format(existing[-1])
        )
    optical_path, optical = _load_combined_optical_report(project_path)
    construction_id = str(optical["setter_result"]["construction_id"])
    root = Path(repository_root) if repository_root else Path(__file__).resolve().parents[3]
    contract_path = root / "config" / "sia4010_official_input_contract.json"
    contract = Sia4010OfficialInputContract.load(contract_path)
    inputs = contract.test("2").confirmed_inputs
    target_u = float(inputs["glazing_u_w_m2k"])
    combined_reference_u = float(inputs["variant_2A_reference_u_w_m2k"])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    report_path = project_path / REPORT_DIRECTORY / (
        "sia2a_thermal_glazing_{}.json".format(timestamp)
    )
    report: Dict[str, Any] = {
        "schema_version": "1.0",
        "qualification_kind": "SIA4010_TEST2A_BASE_GLAZING_THERMAL_STORAGE",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "STARTED",
        "project": {
            "name": str(getattr(project, "name", "")),
            "path": str(project_path),
        },
        "scenario": scenario.to_dict(),
        "mutation_scope": MUTATION_SCOPE,
        "mutation_boundary_entered": False,
        "construction_id": construction_id,
        "target_base_glazing_u_w_m2k": target_u,
        "separate_combined_glazing_awning_reference_u_w_m2k": combined_reference_u,
        "source_contracts": {
            "official_test2_contract": {
                "path": str(contract_path),
                "sha256": _sha256(contract_path),
            },
            "combined_optical_prerequisite": {
                "path": str(optical_path),
                "sha256": _sha256(optical_path),
            },
        },
        "base_glazing_thermal_storage_qualified": False,
        "manufacturer_layer_build_up_qualified": False,
        "combined_glazing_awning_u_qualified": False,
        "opening_assignment_performed": False,
        "simulation_performed": False,
        "compliance_claim_allowed": False,
        "claim_guardrail": (
            "A PASS proves only an equivalent single-layer CDB resistance whose "
            "VE ISO U-factor matches the official base-glazing target. It does "
            "not prove the manufacturer layer build-up, combined shade U-value, "
            "dynamic control, APS equivalence, SIA validation or compliance."
        ),
    }
    _write_json(report_path, report)
    try:
        gateway = gateway_factory(iesve_module)
        construction = gateway._get_construction(construction_id)
        layers = list(construction.get_layers())
        if len(layers) != 1:
            raise VeMutationError(
                "Equivalent thermal qualification requires exactly one native "
                "layer; found {}".format(len(layers))
            )
        layer_properties = dict(layers[0].get_properties())
        if "resistance" not in layer_properties:
            raise VeMutationError("Native glazing layer exposes no resistance field")
        report["mutation_boundary_entered"] = True
        report["status"] = "MUTATION_STARTED"
        report["initial_layer_properties"] = layer_properties
        _write_json(report_path, report)
        result = _solve_equivalent_resistance(
            layers[0],
            construction,
            gateway._uvalue_type_iso(),
            target_u,
            DEFAULT_QA_TOLERANCE_W_M2K,
        )
        report.update(
            {
                "status": "PASS",
                "calibration_result": result,
                "base_glazing_thermal_storage_qualified": True,
                "remaining_blockers": [
                    "TEST2A_MANUFACTURER_4_14_4_14_4_LAYER_BUILD_UP_NOT_QUALIFIED",
                    "TEST2A_COMBINED_GLAZING_AWNING_U_NOT_QUALIFIED",
                    "TEST2A_FINAL_OPENING_BINDING_NOT_IMPLEMENTED",
                    "TEST2A_DYNAMIC_CONTROL_EQUIVALENCE_NOT_QUALIFIED",
                    "TEST2A_APS_EQUIVALENCE_NOT_QUALIFIED",
                ],
            }
        )
    except Exception as exc:
        report.update(
            {
                "status": "FAIL",
                "error": "{}: {}".format(type(exc).__name__, exc),
                "mutation_state": (
                    "UNKNOWN_AFTER_MUTATION_BOUNDARY"
                    if report.get("mutation_boundary_entered")
                    else "NO_MUTATION_BOUNDARY_ENTERED"
                ),
                "recovery_action": (
                    "Discard this disposable project after any entered mutation "
                    "boundary, correct the cause, and restart from a fresh copy."
                ),
            }
        )
        _write_json(report_path, report)
        raise
    _write_json(report_path, report)
    report_path.with_suffix(report_path.suffix + ".sha256").write_text(
        "{}  {}\n".format(_sha256(report_path), report_path.name),
        encoding="ascii",
    )
    return report_path

