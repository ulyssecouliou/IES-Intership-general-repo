"""Transient, restored opening-assignment qualification for Test 2A.

The fixed-closed Test 2A CDB probe is intentionally unassigned.  This module
proves the next native boundary without pretending to generate the test: one
existing opening is assigned the checksummed probe construction, read back,
and immediately restored to its original construction.  Both transitions are
verified.  The project must be disposable because a native-process failure
between the two setters can still leave the live model partially mutated.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple

from ..exceptions import ConfigurationError, VeMutationError
from ..ve_api import IesVeGateway
from .model_scenario import ModelScenario
from .scenario_preflight import is_temporary_ve_project


REPORT_DIRECTORY = Path("sia4010_artifacts") / "diagnostics"
SCENARIO_FILENAME = "sia_model_scenario.json"
MUTATION_SCOPE = "ONE_OPENING_TRANSIENT_ASSIGNMENT_WITH_VERIFIED_RESTORATION"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _validated_optical_report(project_path: Path) -> Tuple[Path, Dict[str, Any]]:
    reports = sorted(
        (project_path / REPORT_DIRECTORY).glob(
            "sia2a_2e1_optical_setter_*.json"
        )
    )
    if len(reports) != 1:
        raise ConfigurationError(
            "Opening assignment requires exactly one Test 2A optical setter "
            "report; found {}".format(len(reports))
        )
    report_path = reports[0]
    checksum_path = report_path.with_suffix(report_path.suffix + ".sha256")
    if not checksum_path.is_file():
        raise ConfigurationError(
            "Optical setter report checksum is missing: {}".format(
                checksum_path
            )
        )
    expected = checksum_path.read_text(encoding="ascii").split()[0].lower()
    if expected != _sha256(report_path):
        raise ConfigurationError("Optical setter report checksum mismatch")
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    if (
        payload.get("status") != "PASS"
        or payload.get("fixed_closed_storage_qualified") is not True
        or payload.get("combined_threshold_optical_storage_qualified")
        is not True
        or payload.get("compliance_claim_allowed") is not False
    ):
        raise ConfigurationError(
            "Optical setter prerequisite is not a combined fail-closed PASS"
        )
    return report_path, payload


def _opening_candidates(gateway: IesVeGateway) -> Tuple[Dict[str, Any], ...]:
    candidates = []
    for body in gateway.model.get_bodies(False):
        for surface in body.get_surfaces():
            for opening in surface.get_openings():
                original = opening.get_construction()
                if original is None:
                    continue
                properties = dict(opening.get_properties())
                identifier = str(opening.get_id())
                candidates.append(
                    {
                        "body": body,
                        "surface": surface,
                        "opening": opening,
                        "opening_id": identifier,
                        "opening_type": str(properties.get("type", "")),
                        "opening_area_m2": float(
                            properties.get("area", 0.0) or 0.0
                        ),
                        "original_construction": original,
                        "original_construction_id": (
                            gateway._construction_identifier(original)
                        ),
                    }
                )
    candidates.sort(
        key=lambda item: (
            str(getattr(item["body"], "id", "")),
            str(getattr(item["surface"], "index", "")),
            item["opening_id"],
        )
    )
    return tuple(candidates)


def qualify_test2a_opening_assignment(
    iesve_module: Any,
    project: Any,
) -> Path:
    """Assign, read back and restore one opening construction."""

    project_path = Path(str(getattr(project, "path", "") or ""))
    if not project_path.is_dir() or is_temporary_ve_project(project_path):
        raise ConfigurationError(
            "Save a disposable VE project outside the temporary VEPROJ folder"
        )
    scenario_path = project_path / SCENARIO_FILENAME
    scenario = ModelScenario.load(scenario_path)
    if (
        not scenario.is_official
        or scenario.variant != "test_2A"
        or scenario.case_id != "2A"
    ):
        raise ConfigurationError(
            "Opening assignment qualification is restricted to test_2A/2A"
        )
    prior = sorted(
        (project_path / REPORT_DIRECTORY).glob(
            "sia2a_opening_assignment_*.json"
        )
    )
    if prior:
        raise ConfigurationError(
            "Opening assignment qualification already exists; use a fresh "
            "disposable project: {}".format(prior[-1])
        )
    optical_path, optical = _validated_optical_report(project_path)
    candidate_id = str(
        optical.get("setter_result", {}).get("construction_id", "")
    )
    if not candidate_id:
        raise ConfigurationError(
            "Optical setter report has no candidate construction ID"
        )

    gateway = IesVeGateway(iesve_module)
    if gateway.project_path.resolve() != project_path.resolve():
        raise ConfigurationError(
            "Active VE project changed during Test 2A qualification"
        )
    candidate = gateway._get_construction(candidate_id)
    layers = list(candidate.get_layers())
    if not layers or any(
        not gateway._construction_layer_is_resolved(candidate, layer)
        for layer in layers
    ):
        raise ConfigurationError(
            "The combined Test 2A probe construction has unresolved layers; "
            "it cannot be assigned safely"
        )
    openings = _opening_candidates(gateway)
    if not openings:
        raise ConfigurationError(
            "No opening with an existing construction is available for the "
            "transient Test 2A assignment"
        )
    selected = openings[0]
    if selected["original_construction_id"] == candidate_id:
        raise ConfigurationError(
            "Selected opening already uses the probe construction"
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    report_path = project_path / REPORT_DIRECTORY / (
        "sia2a_opening_assignment_{}.json".format(timestamp)
    )
    report: Dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "STARTED",
        "project": {
            "name": str(getattr(project, "name", "")),
            "path": str(project_path),
        },
        "scenario": scenario.to_dict(),
        "source_contracts": {
            "scenario": {
                "path": str(scenario_path),
                "sha256": _sha256(scenario_path),
            },
            "combined_optical_setter_report": {
                "path": str(optical_path),
                "sha256": _sha256(optical_path),
            },
        },
        "mutation_scope": MUTATION_SCOPE,
        "candidate_construction_id": candidate_id,
        "candidate_layer_count": len(layers),
        "available_opening_count": len(openings),
        "selected_opening": {
            "opening_id": selected["opening_id"],
            "opening_type": selected["opening_type"],
            "opening_area_m2": selected["opening_area_m2"],
            "original_construction_id": selected[
                "original_construction_id"
            ],
        },
        "mutation_boundary_entered": False,
        "candidate_assignment_readback_verified": False,
        "original_assignment_restored": False,
        "opening_assignment_performed": False,
        "opening_assignment_persisted": False,
        "geometry_changed": False,
        "simulation_performed": False,
        "dynamic_equivalence_qualified": False,
        "compliance_claim_allowed": False,
        "claim_guardrail": (
            "A PASS qualifies only one transient native opening assignment and "
            "verified restoration. It does not validate the candidate's "
            "thermal/optical physics, dynamic control, APS outputs or SIA "
            "compliance."
        ),
    }
    _write_json(report_path, report)

    body = selected["body"]
    surface = selected["surface"]
    opening = selected["opening"]
    original = selected["original_construction"]
    restored = False
    assignment_error = None
    try:
        report.update(
            {
                "status": "MUTATION_STARTED",
                "mutation_boundary_entered": True,
            }
        )
        _write_json(report_path, report)
        body.assign_construction_to_opening(
            candidate, surface, opening.get_id()
        )
        assigned_id = gateway._construction_identifier(
            opening.get_construction()
        )
        if assigned_id != candidate_id:
            raise VeMutationError(
                "Candidate construction assignment did not persist"
            )
        report["candidate_assignment_readback_verified"] = True
    except Exception as exc:
        assignment_error = exc
    finally:
        if report["mutation_boundary_entered"]:
            try:
                body.assign_construction_to_opening(
                    original, surface, opening.get_id()
                )
                restored_id = gateway._construction_identifier(
                    opening.get_construction()
                )
                restored = restored_id == selected[
                    "original_construction_id"
                ]
            except Exception as restore_exc:
                report["restoration_error"] = "{}: {}".format(
                    type(restore_exc).__name__, restore_exc
                )
            report["original_assignment_restored"] = restored
            report["opening_assignment_performed"] = True
            report["opening_assignment_persisted"] = not restored
            _write_json(report_path, report)

    if assignment_error is not None or not restored:
        report.update(
            {
                "status": "FAIL",
                "error": (
                    "{}: {}".format(
                        type(assignment_error).__name__, assignment_error
                    )
                    if assignment_error is not None
                    else "Original opening construction was not restored"
                ),
                "recovery_action": (
                    "Discard this disposable project. The original opening "
                    "construction could not be fully qualified and restored."
                ),
            }
        )
        _write_json(report_path, report)
        if assignment_error is not None:
            raise VeMutationError(
                "Transient opening assignment failed: {}".format(
                    assignment_error
                )
            ) from assignment_error
        raise VeMutationError(
            "Original opening construction was not restored; discard project"
        )
    report.update(
        {
            "status": "PASS",
            "completed_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    _write_json(report_path, report)
    report_path.with_suffix(report_path.suffix + ".sha256").write_text(
        "{}  {}\n".format(_sha256(report_path), report_path.name),
        encoding="ascii",
    )
    return report_path
