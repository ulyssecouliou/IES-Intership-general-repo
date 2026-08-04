"""Fail-closed ApacheSim execution for source-traced SIA 4010 Test 1 cases.

The official Test 1 specification prescribes an annual simulation from
1 January to 31 December 2011 and hourly result datasets. It does not prescribe
an ApacheSim calculation timestep or a preconditioning duration. This module
therefore sets only the confirmed period, hourly reporting interval and a
collision-free APS filename. Unspecified engine settings are recorded before
and after the run but are never silently replaced by generic defaults.

Execution is still a runtime qualification, not a compliance result. The APS
must subsequently pass the qualified binding, required-output and official
comparison workflow.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

from .case_registry import get_case_capability
from .model_scenario import ModelScenario
from .scenario_preflight import is_temporary_ve_project


SIMULATION_QUALIFICATION_CASES: Tuple[str, ...] = (
    "600",
    "640",
    "600FF",
    "900",
    "940",
    "900FF",
)
TEST1_SIMULATION_SOURCE = "SIA 4010 Test 1 specification, pages 1-2"
MODEL_REPORT_RELATIVE_PATH = Path(
    "reference_model_artifacts/reports/reference_model_report.json"
)
RUNTIME_INPUT_REPORT_GLOB = (
    "sia4010_test1_runtime_input_qualification_*.json"
)
RUNTIME_INPUT_READY_STATUS = (
    "PROVISIONAL_ENGINE_MAPPING_APPLIED_READY_FOR_SIMULATION"
)


class ApacheSimQualificationError(RuntimeError):
    """Raised when the guarded simulation cannot be executed or verified."""


@dataclass(frozen=True)
class ApacheSimQualificationReceipt:
    """Machine-readable evidence for one synchronous ApacheSim execution."""

    status: str
    variant: str
    case_id: str
    project_path: str
    model_report_path: str
    model_report_sha256: str
    scenario_path: str
    scenario_sha256: str
    requested_options: Dict[str, Any]
    options_before: Dict[str, Any]
    options_after: Dict[str, Any]
    results_path: str
    results_sha256: str
    results_size_bytes: int
    audit_path: str
    compliance_claim_allowed: bool = False
    runtime_input_report_path: str = ""
    runtime_input_report_sha256: str = ""
    aps_evaluation_required: bool = True
    runtime_qualification_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe representation."""

        return asdict(self)


def _load_json(path: Path, context: str) -> Dict[str, Any]:
    """Load one JSON object with a contextual fail-closed error."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ApacheSimQualificationError(
            "Unable to read {} at '{}': {}".format(context, path, exc)
        ) from exc
    if not isinstance(payload, dict):
        raise ApacheSimQualificationError(
            "{} must contain a JSON object: {}".format(context, path)
        )
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write one audit object atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256(path: Path) -> str:
    """Return an uppercase SHA-256 checksum."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _json_safe_mapping(value: Any, context: str) -> Dict[str, Any]:
    """Normalize an ApacheSim option mapping for evidence serialization."""

    if not isinstance(value, Mapping):
        raise ApacheSimQualificationError(
            "{} did not return a mapping".format(context)
        )
    return {str(key): item for key, item in value.items()}


def _validation_statuses(report: Mapping[str, Any]) -> Dict[str, str]:
    """Index model-validation results by stable control ID."""

    statuses: Dict[str, str] = {}
    for item in report.get("validation_results", []) or []:
        if isinstance(item, Mapping) and item.get("control_id"):
            statuses[str(item["control_id"])] = str(item.get("status") or "")
    return statuses


def _sequence(value: Any) -> list:
    """Normalize VE collection proxies without assuming a concrete type."""

    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return [value]


def _latest_runtime_input_report(project_path: Path) -> Path:
    """Return the newest Test 1 runtime-input qualification artifact."""

    diagnostic_dir = project_path / "sia4010_artifacts" / "diagnostics"
    candidates = sorted(
        diagnostic_dir.glob(RUNTIME_INPUT_REPORT_GLOB),
        key=lambda path: (path.stat().st_mtime_ns, path.name),
        reverse=True,
    )
    if not candidates:
        raise ApacheSimQualificationError(
            "Run the controlled Test 1 runtime-input qualification before "
            "ApacheSim; no qualification report was found"
        )
    return candidates[0]


def _validate_runtime_input_evidence(
    *,
    project: Any,
    project_path: Path,
    scenario: ModelScenario,
    scenario_path: Path,
) -> Tuple[Path, Dict[str, Any]]:
    """Verify the qualification artifact and the live VE room read-back."""

    report_path = _latest_runtime_input_report(project_path)
    report = _load_json(report_path, "Test 1 runtime-input qualification")
    if report.get("status") != RUNTIME_INPUT_READY_STATUS:
        raise ApacheSimQualificationError(
            "Test 1 runtime-input qualification is not simulation-ready: {!r}".format(
                report.get("status")
            )
        )
    report_project = report.get("project") or {}
    try:
        reported_project_path = Path(str(report_project.get("path") or "")).resolve()
    except (OSError, RuntimeError) as exc:
        raise ApacheSimQualificationError(
            "Runtime-input qualification contains an invalid project path"
        ) from exc
    if reported_project_path != project_path.resolve():
        raise ApacheSimQualificationError(
            "Runtime-input qualification belongs to another VE project: {}".format(
                reported_project_path
            )
        )
    report_scenario = report.get("scenario") or {}
    selection = report_scenario.get("selection") or {}
    actual_pair = (
        str(selection.get("variant") or ""),
        str(selection.get("case_id") or ""),
    )
    expected_pair = (scenario.variant, scenario.case_id)
    if actual_pair != expected_pair:
        raise ApacheSimQualificationError(
            "Runtime-input qualification belongs to {}/{} instead of {}/{}".format(
                actual_pair[0] or "<unknown>",
                actual_pair[1] or "<unknown>",
                expected_pair[0],
                expected_pair[1],
            )
        )
    if str(report.get("scenario_sha256") or "").upper() != _sha256(
        scenario_path
    ):
        raise ApacheSimQualificationError(
            "Runtime-input qualification is stale: scenario checksum mismatch"
        )

    mutation = report.get("mutation") or {}
    mapping = report.get("mapping") or {}
    capacity = report.get("capacity_semantics") or {}
    guardrails = report.get("guardrails") or {}
    if mutation.get("only_intended_field") != "furniture_mass_factor":
        raise ApacheSimQualificationError(
            "Runtime-input qualification does not prove the intended single-field mutation"
        )
    try:
        requested_factor = float(mutation.get("requested"))
        verified_factor = float(mutation.get("verified_after"))
        mapped_factor = float(mapping.get("furniture_mass_factor"))
    except (TypeError, ValueError) as exc:
        raise ApacheSimQualificationError(
            "Runtime-input qualification contains a non-numeric furniture factor"
        ) from exc
    factors = (requested_factor, verified_factor, mapped_factor)
    if not all(math.isfinite(value) for value in factors) or not (
        math.isclose(requested_factor, verified_factor, rel_tol=0.0, abs_tol=1.0e-6)
        and math.isclose(requested_factor, mapped_factor, rel_tol=0.0, abs_tol=1.0e-6)
    ):
        raise ApacheSimQualificationError(
            "Runtime-input qualification furniture-factor evidence is inconsistent"
        )
    if capacity.get("verified") is not True:
        raise ApacheSimQualificationError(
            "Runtime-input qualification does not verify capacity semantics"
        )
    if guardrails.get("capacity_fields_mutated") is not False:
        raise ApacheSimQualificationError(
            "Runtime-input qualification does not prove unchanged capacity fields"
        )
    if guardrails.get("compliance_claim_allowed") is not False:
        raise ApacheSimQualificationError(
            "Runtime-input qualification has an unsafe compliance-claim flag"
        )

    expected_room_name = "SIA4010_TEST_1_{}_ZONE".format(scenario.case_id)
    if str((report.get("room") or {}).get("name") or "") != expected_room_name:
        raise ApacheSimQualificationError(
            "Runtime-input qualification references the wrong VE room"
        )
    models = _sequence(getattr(project, "models", []))
    if not models:
        raise ApacheSimQualificationError(
            "The active VE project exposes no model for runtime-input read-back"
        )
    bodies = [
        body
        for body in _sequence(models[0].get_bodies(False))
        if hasattr(body, "get_room_data")
        and str(getattr(body, "name", "")) == expected_room_name
    ]
    if len(bodies) != 1:
        raise ApacheSimQualificationError(
            "Expected exactly one live VE room named {!r}; found {}".format(
                expected_room_name, len(bodies)
            )
        )
    room_data = bodies[0].get_room_data()
    live_conditions = dict(room_data.get_room_conditions())
    try:
        live_factor = float(live_conditions.get("furniture_mass_factor"))
    except (TypeError, ValueError) as exc:
        raise ApacheSimQualificationError(
            "Live VE furniture_mass_factor is unavailable"
        ) from exc
    if not math.isclose(
        live_factor, verified_factor, rel_tol=0.0, abs_tol=1.0e-6
    ):
        raise ApacheSimQualificationError(
            "Live VE furniture factor does not match the qualification report: "
            "live={}, qualified={}. Save/reapply the controlled qualification.".format(
                live_factor, verified_factor
            )
        )
    live_system = dict(room_data.get_apache_systems())
    conditioned = bool(capacity.get("conditioned"))
    if bool(live_system.get("conditioned")) != conditioned:
        raise ApacheSimQualificationError(
            "Live VE conditioned state differs from the qualification report"
        )
    if conditioned and not (
        bool(live_system.get("heating_capacity_unlimited"))
        and bool(live_system.get("cooling_capacity_unlimited"))
    ):
        raise ApacheSimQualificationError(
            "Live VE conditioned room no longer has unlimited heating and cooling capacity"
        )
    return report_path, report


def _validate_model_evidence(
    report: Mapping[str, Any],
    *,
    project_path: Path,
    variant: str,
    case_id: str,
) -> None:
    """Require an exact-case, checksum-traced mutation and readable weather."""

    overall = str(report.get("overall_status") or "")
    if overall not in {"PASS", "WARNING"}:
        raise ApacheSimQualificationError(
            "Reference-model report is not simulation-ready: overall_status={!r}".format(
                overall
            )
        )
    mode = str(report.get("run_metadata", {}).get("mode") or "")
    if mode not in {"VE_MUTATION", "VE_RESUME_AFTER_IMPORT"}:
        raise ApacheSimQualificationError(
            "Reference-model report does not prove a completed VE mutation: {!r}".format(
                mode
            )
        )
    asset_manifest = (
        report.get("additional_data", {}).get("asset_manifest") or {}
    )
    if not isinstance(asset_manifest, Mapping):
        asset_manifest = {}
    metadata = asset_manifest.get("metadata") or {}
    if not isinstance(metadata, Mapping):
        metadata = {}
    actual_pair = (
        str(metadata.get("sia4010_variant") or ""),
        str(metadata.get("sia4010_case_id") or ""),
    )
    if actual_pair == ("", ""):
        frozen_checksum = str(asset_manifest.get("source_checksum") or "")
        generated = report.get("generated_geometry") or {}
        generated_spaces = generated.get("spaces") if isinstance(
            generated, Mapping
        ) else []
        if not isinstance(generated_spaces, list):
            generated_spaces = []
        expected_building = "SIA4010_TEST_1_{}_BUILDING".format(case_id)
        expected_space = "SIA4010_TEST_1_{}_SPACE".format(case_id)
        expected_room = "SIA4010_TEST_1_{}_ZONE".format(case_id)
        matching_spaces = [
            space
            for space in generated_spaces
            if isinstance(space, Mapping)
            and str(space.get("identifier") or "") == expected_space
            and str(space.get("name") or "") == expected_room
        ]
        frozen_identity_is_exact = (
            str(generated.get("identifier") or "") == expected_building
            and len(matching_spaces) == 1
            and re.fullmatch(r"[0-9A-Fa-f]{64}", frozen_checksum) is not None
        )
        if frozen_identity_is_exact:
            actual_pair = (variant, case_id)
    if actual_pair != (variant, case_id):
        raise ApacheSimQualificationError(
            "Model evidence belongs to {}/{} instead of {}/{}".format(
                actual_pair[0] or "<unknown>",
                actual_pair[1] or "<unknown>",
                variant,
                case_id,
            )
        )
    snapshot = report.get("ve_model_snapshot")
    if not isinstance(snapshot, Mapping):
        raise ApacheSimQualificationError(
            "Reference-model report has no verified VE model snapshot"
        )
    spaces = snapshot.get("spaces")
    if not isinstance(spaces, list) or len(spaces) != 1:
        raise ApacheSimQualificationError(
            "Test 1 simulation requires exactly one verified VE room; report has {}".format(
                len(spaces) if isinstance(spaces, list) else 0
            )
        )
    statuses = _validation_statuses(report)
    if statuses.get("VE-WEA-001") != "PASS":
        raise ApacheSimQualificationError(
            "VE-WEA-001 must PASS before ApacheSim; found {!r}".format(
                statuses.get("VE-WEA-001")
            )
        )


def _safe_result_stem(variant: str, case_id: str, stamp: str) -> str:
    """Return a path-free collision-resistant APS filename."""

    raw = "SIA4010_{}_{}_{}".format(variant, case_id, stamp)
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw).strip("._")
    if not stem:
        raise ApacheSimQualificationError("Unable to create a safe APS filename")
    return "{}.aps".format(stem)


def _assert_option_readback(
    requested: Mapping[str, Any],
    actual: Mapping[str, Any],
) -> None:
    """Require every explicitly set ApacheSim option to read back exactly."""

    mismatches = {
        key: {"requested": expected, "readback": actual.get(key)}
        for key, expected in requested.items()
        if actual.get(key) != expected
    }
    if mismatches:
        raise ApacheSimQualificationError(
            "ApacheSim option read-back mismatch: {}".format(mismatches)
        )


def _wait_for_nonempty_file(path: Path, timeout_seconds: float = 10.0) -> None:
    """Wait briefly for a synchronous run to flush its APS file."""

    deadline = time.monotonic() + max(0.0, float(timeout_seconds))
    while True:
        if path.is_file() and path.stat().st_size > 0:
            return
        if time.monotonic() >= deadline:
            break
        time.sleep(0.1)
    raise ApacheSimQualificationError(
        "ApacheSim returned without a non-empty APS file at '{}'".format(path)
    )


def run_qualified_apachesim(
    *,
    project: Any,
    apachesim_factory: Callable[[], Any],
    repository_root: Path,
    now: Optional[datetime] = None,
    file_wait_seconds: float = 10.0,
) -> ApacheSimQualificationReceipt:
    """Run the active exact Test 1 case with only confirmed temporal options."""

    project_path = Path(str(getattr(project, "path", "") or ""))
    if not project_path.is_dir():
        raise ApacheSimQualificationError(
            "The active VE project path is unavailable or unsaved: '{}'".format(
                project_path
            )
        )
    if is_temporary_ve_project(project_path):
        raise ApacheSimQualificationError(
            "ApacheSim qualification is forbidden in a temporary VEPROJ project"
        )
    scenario_path = project_path / "sia_model_scenario.json"
    scenario = ModelScenario.load(scenario_path)
    if not scenario.is_official or scenario.variant != "test_1":
        raise ApacheSimQualificationError(
            "ApacheSim qualification currently supports official Test 1 only"
        )
    if scenario.case_id not in SIMULATION_QUALIFICATION_CASES:
        raise ApacheSimQualificationError(
            "ApacheSim qualification is unavailable for {}/{}".format(
                scenario.variant, scenario.case_id
            )
        )
    capability = get_case_capability(scenario.variant, scenario.case_id)
    if not (
        capability.mutation_supported
        or capability.runtime_qualification_supported
    ):
        raise ApacheSimQualificationError(
            "No guarded model generator exists for {}/{}".format(
                scenario.variant, scenario.case_id
            )
        )
    specification_path = (
        Path(repository_root)
        / "SIA_4010_geteilter_Link"
        / "Test1"
        / "Spezifikation_Test1.pdf"
    )
    if not specification_path.is_file():
        raise ApacheSimQualificationError(
            "Official Test 1 specification is missing: {}".format(
                specification_path
            )
        )

    model_report_path = project_path / MODEL_REPORT_RELATIVE_PATH
    model_report = _load_json(model_report_path, "reference-model report")
    _validate_model_evidence(
        model_report,
        project_path=project_path,
        variant=scenario.variant,
        case_id=scenario.case_id,
    )
    runtime_input_report_path, runtime_input_report = (
        _validate_runtime_input_evidence(
            project=project,
            project_path=project_path,
            scenario=scenario,
            scenario_path=scenario_path,
        )
    )

    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    stamp = current_time.astimezone(timezone.utc).strftime("%Y%m%d_%H%M%S")
    results_filename = _safe_result_stem(
        scenario.variant, scenario.case_id, stamp
    )
    results_path = project_path / "Vista" / results_filename
    if results_path.exists():
        raise ApacheSimQualificationError(
            "Refusing to overwrite existing APS evidence: {}".format(
                results_path
            )
        )

    audit_path = (
        project_path
        / "sia4010_artifacts"
        / "simulation"
        / "SIA4010_{}_{}_apachesim_qualification.json".format(
            scenario.variant, scenario.case_id
        )
    )
    requested_options = {
        "start_day": 1,
        "start_month": 1,
        "end_day": 31,
        "end_month": 12,
        "reporting_interval": 3,
        "results_filename": results_filename,
    }
    base_audit: Dict[str, Any] = {
        "schema_version": "1.0",
        "status": "STARTED",
        "generated_at_utc": current_time.astimezone(timezone.utc).isoformat(),
        "variant": scenario.variant,
        "case_id": scenario.case_id,
        "project_path": str(project_path),
        "source": TEST1_SIMULATION_SOURCE,
        "source_file": {
            "path": str(specification_path),
            "sha256": _sha256(specification_path),
        },
        "runtime_input_qualification": {
            "path": str(runtime_input_report_path),
            "sha256": _sha256(runtime_input_report_path),
            "status": runtime_input_report.get("status"),
            "compliance_claim_allowed": False,
        },
        "confirmed_contract": {
            "simulation_period": "2011-01-01 through 2011-12-31",
            "required_result_frequency": "hourly",
            "requested_apachesim_options": requested_options,
        },
        "deliberately_unset_engine_options": {
            "simulation_timestep": (
                "Not prescribed by the supplied Test 1 specification; retained "
                "from the active VE project and recorded in option snapshots."
            ),
            "preconditioning_days": (
                "Not prescribed by the supplied Test 1 specification; retained "
                "from the active VE project and recorded in option snapshots."
            ),
        },
        "required_postconditions": [
            "non-empty APS file",
            "exactly 8760 hourly values for every required annual series",
            "qualified variable identity, unit, sign and timestep",
            "complete active-case APS evaluation",
        ],
        "compliance_claim_allowed": False,
        "runtime_qualification_required": True,
        "aps_evaluation_required": True,
    }

    options_before: Dict[str, Any] = {}
    options_after: Dict[str, Any] = {}
    try:
        sim = apachesim_factory()
        for method in ("get_options", "set_options", "run_simulation"):
            if not callable(getattr(sim, method, None)):
                raise ApacheSimQualificationError(
                    "ApacheSim.{} is unavailable".format(method)
                )
        options_before = _json_safe_mapping(
            sim.get_options(), "ApacheSim.get_options()"
        )
        if sim.set_options(dict(requested_options)) is not True:
            raise ApacheSimQualificationError(
                "ApacheSim.set_options() did not return True"
            )
        options_after = _json_safe_mapping(
            sim.get_options(), "ApacheSim.get_options() read-back"
        )
        _assert_option_readback(requested_options, options_after)
        if sim.run_simulation(queue_to_tasks=False) is not True:
            raise ApacheSimQualificationError(
                "ApacheSim.run_simulation(queue_to_tasks=False) did not return True"
            )
        _wait_for_nonempty_file(results_path, file_wait_seconds)
    except Exception as exc:
        error = (
            exc
            if isinstance(exc, ApacheSimQualificationError)
            else ApacheSimQualificationError(str(exc))
        )
        base_audit.update(
            {
                "status": "FAIL",
                "error": str(error),
                "options_before": options_before,
                "options_after": options_after,
                "results_path": str(results_path),
            }
        )
        _write_json(audit_path, base_audit)
        raise ApacheSimQualificationError(
            "{} Audit: {}".format(error, audit_path)
        ) from exc

    receipt = ApacheSimQualificationReceipt(
        status="SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION",
        variant=scenario.variant,
        case_id=scenario.case_id,
        project_path=str(project_path),
        model_report_path=str(model_report_path),
        model_report_sha256=_sha256(model_report_path),
        scenario_path=str(scenario_path),
        scenario_sha256=_sha256(scenario_path),
        runtime_input_report_path=str(runtime_input_report_path),
        runtime_input_report_sha256=_sha256(runtime_input_report_path),
        requested_options=dict(requested_options),
        options_before=options_before,
        options_after=options_after,
        results_path=str(results_path),
        results_sha256=_sha256(results_path),
        results_size_bytes=results_path.stat().st_size,
        audit_path=str(audit_path),
    )
    payload = receipt.to_dict()
    payload.update(
        {
            "source": TEST1_SIMULATION_SOURCE,
            "source_file": base_audit["source_file"],
            "runtime_input_qualification": base_audit[
                "runtime_input_qualification"
            ],
            "confirmed_contract": base_audit["confirmed_contract"],
            "deliberately_unset_engine_options": base_audit[
                "deliberately_unset_engine_options"
            ],
            "required_postconditions": base_audit["required_postconditions"],
            "claim_guardrail": (
                "A successful ApacheSim call is not a SIA result. The APS must "
                "pass the complete qualified extraction and comparison path."
            ),
        }
    )
    _write_json(audit_path, payload)
    return receipt
