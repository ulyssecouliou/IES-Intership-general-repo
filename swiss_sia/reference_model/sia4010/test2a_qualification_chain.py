"""Fail-closed orchestration for the disposable Test 2A VE probes.

The individual Test 2A probes intentionally qualify narrow native VE storage
boundaries.  This module joins them without widening their claims: the
read-only capability report must be ready before the first setter is called,
every report is checksum-linked, and the one opening assignment is restored
before the terminal status says that model generation and APS equivalence are
still required.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Union

from ..exceptions import ConfigurationError
from .model_scenario import ModelScenario
from .scenario_preflight import is_temporary_ve_project


REPORT_DIRECTORY = Path("sia4010_artifacts") / "diagnostics"
REPORT_PATTERN = "sia4010_test2a_qualification_chain_*.json"
SCENARIO_FILENAME = "sia_model_scenario.json"
READY_STATUS = "READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION"
FINAL_STATUS = (
    "RUNTIME_STORAGE_THERMAL_AND_OPENING_ASSIGNMENT_QUALIFIED_"
    "MODEL_GENERATION_REQUIRED"
)
MUTATION_SCOPE = (
    "PROJECT_PROFILES_TWO_CDB_PROBES_ONE_THERMAL_CALIBRATION_"
    "AND_ONE_RESTORED_OPENING_ASSIGNMENT"
)


class Test2AQualificationBlocked(ConfigurationError):
    """Raised after a durable audit records a fail-closed chain stop."""


@dataclass(frozen=True)
class Test2AQualificationChainReceipt:
    """Terminal receipt for the narrowly scoped Test 2A qualification chain."""

    status: str
    report_path: Path
    mutation_supported: bool
    compliance_claim_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe receipt for VEScripts callers."""

        payload = asdict(self)
        payload["report_path"] = str(self.report_path)
        return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _report_evidence(
    output: Union[str, Path],
    *,
    label: str,
    expected_status: str,
    expected_scope: str = "",
) -> Dict[str, Any]:
    """Load and validate one immutable, non-compliance probe report."""

    path = Path(output)
    if not path.is_file():
        raise Test2AQualificationBlocked(
            "{} report was not written: {}".format(label, path)
        )
    checksum_path = path.with_suffix(path.suffix + ".sha256")
    if not checksum_path.is_file():
        raise Test2AQualificationBlocked(
            "{} checksum was not written: {}".format(label, checksum_path)
        )
    try:
        expected_sha = checksum_path.read_text(encoding="ascii").split()[0]
    except (IndexError, OSError) as exc:
        raise Test2AQualificationBlocked(
            "{} checksum is unreadable: {}".format(label, exc)
        ) from exc
    actual_sha = _sha256(path)
    if expected_sha != actual_sha:
        raise Test2AQualificationBlocked(
            "{} checksum does not match its report".format(label)
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != expected_status:
        raise Test2AQualificationBlocked(
            "{} status is {!r}; expected {!r}".format(
                label, payload.get("status"), expected_status
            )
        )
    if payload.get("compliance_claim_allowed") is True:
        raise Test2AQualificationBlocked(
            "{} report incorrectly authorizes a compliance claim".format(label)
        )
    if expected_scope and payload.get("mutation_scope") != expected_scope:
        raise Test2AQualificationBlocked(
            "{} mutation scope is {!r}; expected {!r}".format(
                label, payload.get("mutation_scope"), expected_scope
            )
        )
    return {
        "label": label,
        "status": payload["status"],
        "path": str(path),
        "sha256": actual_sha,
    }


def _optical_evidence(output: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate the optical report and its fail-closed rebuilt bundle."""

    report = _report_evidence(
        output.get("report_path", ""),
        label="Test 2A fixed-closed optical setter",
        expected_status="PASS",
        expected_scope="ONE_UNASSIGNED_GLAZED_CDB_CONSTRUCTION",
    )
    if output.get("mutation_supported") is not False:
        raise Test2AQualificationBlocked(
            "The rebuilt Test 2A bundle must keep mutation_supported=False"
        )
    audit_path = Path(str(output.get("bundle_audit_path", "")))
    if not audit_path.is_file():
        raise Test2AQualificationBlocked(
            "Rebuilt Test 2A bundle audit was not written: {}".format(audit_path)
        )
    audit_checksum = audit_path.with_suffix(audit_path.suffix + ".sha256")
    if not audit_checksum.is_file():
        raise Test2AQualificationBlocked(
            "Rebuilt Test 2A bundle checksum was not written: {}".format(
                audit_checksum
            )
        )
    expected_audit_sha = audit_checksum.read_text(encoding="ascii").split()[0]
    actual_audit_sha = _sha256(audit_path)
    if expected_audit_sha != actual_audit_sha:
        raise Test2AQualificationBlocked(
            "Rebuilt Test 2A bundle checksum does not match its audit"
        )
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit.get("mutation_supported") is not False:
        raise Test2AQualificationBlocked(
            "Rebuilt Test 2A bundle audit must remain fail-closed"
        )
    if audit.get("status") != output.get("bundle_status"):
        raise Test2AQualificationBlocked(
            "Rebuilt Test 2A bundle status does not match its audit"
        )
    report.update(
        {
            "bundle_status": output.get("bundle_status"),
            "bundle_audit_path": str(audit_path),
            "bundle_audit_sha256": actual_audit_sha,
            "mutation_supported": False,
        }
    )
    return report


def _opening_assignment_evidence(output: Union[str, Path]) -> Dict[str, Any]:
    """Require both candidate read-back and restoration before advancing."""

    report = _report_evidence(
        output,
        label="transient_opening_assignment_and_restoration",
        expected_status="PASS",
        expected_scope=(
            "ONE_OPENING_TRANSIENT_ASSIGNMENT_WITH_VERIFIED_RESTORATION"
        ),
    )
    payload = json.loads(Path(output).read_text(encoding="utf-8"))
    if (
        payload.get("candidate_assignment_readback_verified") is not True
        or payload.get("original_assignment_restored") is not True
        or payload.get("opening_assignment_persisted") is not False
    ):
        raise Test2AQualificationBlocked(
            "Opening assignment report does not prove read-back and restoration"
        )
    return report


def _thermal_glazing_evidence(output: Union[str, Path]) -> Dict[str, Any]:
    """Require a source-bound base-glazing U-value read-back PASS."""

    report = _report_evidence(
        output,
        label="base_glazing_thermal_storage",
        expected_status="PASS",
        expected_scope="ONE_UNASSIGNED_GLAZED_CDB_LAYER_RESISTANCE",
    )
    payload = json.loads(Path(output).read_text(encoding="utf-8"))
    calibration = payload.get("calibration_result", {})
    if (
        payload.get("base_glazing_thermal_storage_qualified") is not True
        or payload.get("manufacturer_layer_build_up_qualified") is not False
        or payload.get("combined_glazing_awning_u_qualified") is not False
        or float(calibration.get("absolute_difference_w_m2k", 1.0))
        > float(calibration.get("qa_tolerance_w_m2k", 0.0))
    ):
        raise Test2AQualificationBlocked(
            "Thermal glazing report does not prove the narrow base-U read-back"
        )
    return report


def run_test2a_qualification_chain(
    project: Any,
    prepare: Callable[[], Any],
    runtime_probe: Callable[[], Union[str, Path]],
    profile_qualification: Callable[[], Union[str, Path]],
    shading_qualification: Callable[[], Union[str, Path]],
    optical_qualification: Callable[[], Mapping[str, Any]],
    thermal_glazing_qualification: Callable[[], Union[str, Path]],
    opening_assignment_qualification: Callable[[], Union[str, Path]],
) -> Test2AQualificationChainReceipt:
    """Run the guarded Test 2A probe chain in one fresh disposable project."""

    project_path = Path(str(getattr(project, "path", "") or ""))
    if not project_path.is_dir() or is_temporary_ve_project(project_path):
        raise Test2AQualificationBlocked(
            "Save a fresh disposable VE project outside the temporary VEPROJ "
            "folder before Test 2A qualification"
        )
    report_directory = project_path / REPORT_DIRECTORY
    prior_chains = sorted(report_directory.glob(REPORT_PATTERN))
    prior_mutations = sorted(report_directory.glob("sia2a_profiles_*.json"))
    prior_mutations += sorted(
        report_directory.glob("sia2a_external_shade_setter_*.json")
    )
    prior_mutations += sorted(
        report_directory.glob("sia2a_2e1_optical_setter_*.json")
    )
    prior_mutations += sorted(
        report_directory.glob("sia2a_thermal_glazing_*.json")
    )
    prior_mutations += sorted(
        report_directory.glob("sia2a_opening_assignment_*.json")
    )
    if prior_chains or prior_mutations:
        previous = (prior_chains + prior_mutations)[-1]
        raise Test2AQualificationBlocked(
            "Test 2A qualification evidence already exists. Discard this "
            "project and use a fresh disposable copy: {}".format(previous)
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    report_path = report_directory / (
        "sia4010_test2a_qualification_chain_{}.json".format(timestamp)
    )
    audit: Dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "STARTED",
        "project": {
            "name": str(getattr(project, "name", "")),
            "path": str(project_path),
        },
        "scenario": {"variant": "test_2A", "case_id": "2A"},
        "stages": [],
        "mutation_scope": MUTATION_SCOPE,
        "mutation_boundary_entered": False,
        "model_generated": False,
        "opening_assignment_performed": False,
        "opening_assignment_restored": False,
        "simulation_performed": False,
        "aps_equivalence_qualified": False,
        "mutation_supported": False,
        "compliance_claim_allowed": False,
        "claim_guardrail": (
            "This chain qualifies only native profile creation and narrow CDB "
            "setter storage/read-back, an equivalent base-glazing U-value, "
            "plus one transient, restored opening "
            "assignment in a disposable project. It does not generate Test "
            "2A, prove dynamic control or APS "
            "equivalence, validate SIA 4010, or attest compliance."
        ),
    }
    _write_json(report_path, audit)

    stage = "prepare_source_bound_scenario"
    try:
        preparation_result = prepare()
        if preparation_result not in (None, 0):
            raise Test2AQualificationBlocked(
                "Test 2A scenario preparation returned {!r}".format(
                    preparation_result
                )
            )
        scenario_path = project_path / SCENARIO_FILENAME
        scenario = ModelScenario.load(scenario_path)
        if (
            not scenario.is_official
            or scenario.variant != "test_2A"
            or scenario.case_id != "2A"
        ):
            raise Test2AQualificationBlocked(
                "Prepared scenario is not official test_2A/2A"
            )
        audit["stages"].append(
            {
                "label": stage,
                "status": "PASS",
                "path": str(scenario_path),
                "sha256": _sha256(scenario_path),
            }
        )
        _write_json(report_path, audit)

        stage = "read_only_runtime_capability"
        runtime = _report_evidence(
            runtime_probe(),
            label=stage,
            expected_status=READY_STATUS,
        )
        audit["stages"].append(runtime)
        _write_json(report_path, audit)

        audit["mutation_boundary_entered"] = True
        stage = "native_profile_graph"
        profiles = _report_evidence(
            profile_qualification(),
            label=stage,
            expected_status="PASS",
            expected_scope="PROJECT_PROFILES_ONLY",
        )
        audit["stages"].append(profiles)
        _write_json(report_path, audit)

        stage = "external_shade_threshold_storage"
        shading = _report_evidence(
            shading_qualification(),
            label=stage,
            expected_status="PASS",
            expected_scope="ONE_UNASSIGNED_GLAZED_CDB_CONSTRUCTION",
        )
        audit["stages"].append(shading)
        _write_json(report_path, audit)

        stage = "fixed_closed_optical_storage_and_bundle_rebuild"
        optical = _optical_evidence(optical_qualification())
        audit["stages"].append(optical)

        stage = "base_glazing_thermal_storage"
        thermal = _thermal_glazing_evidence(
            thermal_glazing_qualification()
        )
        audit["stages"].append(thermal)

        stage = "transient_opening_assignment_and_restoration"
        assignment = _opening_assignment_evidence(
            opening_assignment_qualification()
        )
        audit["stages"].append(assignment)
        audit.update(
            {
                "status": FINAL_STATUS,
                "completed_at": datetime.now().isoformat(timespec="seconds"),
                "opening_assignment_performed": True,
                "opening_assignment_restored": True,
                "remaining_blockers": [
                    "TEST2A_FINAL_OPENING_BINDING_NOT_IMPLEMENTED",
                    "TEST2A_MANUFACTURER_LAYER_BUILD_UP_NOT_QUALIFIED",
                    "TEST2A_COMBINED_GLAZING_AWNING_U_NOT_QUALIFIED",
                    "TEST2A_DYNAMIC_CONTROL_EQUIVALENCE_NOT_QUALIFIED",
                    "TEST2A_ANGULAR_AND_SECONDARY_OPTICS_NOT_QUALIFIED",
                    "TEST2A_APS_EQUIVALENCE_NOT_QUALIFIED",
                    "PROVISIONAL_EMISSIVITY_PREVENTS_COMPLIANCE_VERDICT",
                ],
            }
        )
        _write_json(report_path, audit)
        report_path.with_suffix(report_path.suffix + ".sha256").write_text(
            "{}  {}\n".format(_sha256(report_path), report_path.name),
            encoding="ascii",
        )
        return Test2AQualificationChainReceipt(
            status=FINAL_STATUS,
            report_path=report_path,
            mutation_supported=False,
            compliance_claim_allowed=False,
        )
    except Exception as exc:
        audit.update(
            {
                "status": "BLOCKED" if not audit["mutation_boundary_entered"] else "FAIL",
                "failed_stage": stage,
                "error": "{}: {}".format(type(exc).__name__, exc),
                "recovery_action": (
                    "Discard this project if the mutation boundary was entered; "
                    "correct the reported cause and restart in a fresh disposable "
                    "project."
                ),
            }
        )
        _write_json(report_path, audit)
        if isinstance(exc, Test2AQualificationBlocked):
            raise
        raise Test2AQualificationBlocked(str(exc)) from exc
