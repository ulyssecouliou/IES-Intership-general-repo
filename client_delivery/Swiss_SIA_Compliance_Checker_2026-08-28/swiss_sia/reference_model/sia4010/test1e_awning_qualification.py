"""Guarded in-place qualification of the Test 1E fabric-awning fields.

Case 1E is case 1D with the Test 2 E1 fabric awning.  Replacing the existing
window construction would risk changing the qualified glazing layers.  This
module therefore writes only the documented VE 2025 shade subset on the
construction(s) already assigned to the two source-identified south windows,
reads every value back and restores the original subset if anything fails.

The solar/visible reflectance setters are unavailable.  A PASS here is thus a
provisional VE mapping receipt, never a compliance result or template review.
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
from .official_input_contract import Sia4010OfficialInputContract
from .scenario_preflight import is_temporary_ve_project
from .test2a_shading_control import build_test2a_fabric_awning_control
from .test2a_shading_qualification import (
    _assert_subset,
    _coerce_active_value,
    _coerce_threshold_value,
)

REPORT_DIRECTORY = Path("sia4010_artifacts") / "diagnostics"
MODEL_PROBE_PATTERN = "sia4010_test1e_model_probe_*.json"
EXPECTED_OPENING_IDS = frozenset(
    {
        "B1929707-293B-49C8-B47D-16D27EBCA0E6",
        "9D5E0355-C746-4210-83FB-3B779195DB10",
    }
)
WRITABLE_FIELDS = (
    "external_shade_active",
    "external_shade_profile",
    "external_shade_transmittance_0",
    "external_shade_radiation_to_lower",
    "external_shade_radiation_to_raise",
)

PROVISIONAL_ANGULAR_TRANSMITTANCE_PLAN = {
    "external_shade_transmittance_0": 0.04,
    # The two misspellings are the public VE 2025 property names.
    "external_shade_transmitance_15": 0.04,
    "external_shade_transmittance_30": 0.04,
    "external_shade_transmittance_45": 0.04,
    "external_shade_transmittance_60": 0.04,
    "external_shade_transmitance_75": 0.04,
    "external_shade_transmittance_90": 0.0,
}


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
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _validated_model_probe(project_path: Path, scenario_path: Path) -> Path:
    reports = sorted((project_path / REPORT_DIRECTORY).glob(MODEL_PROBE_PATTERN))
    if len(reports) != 1:
        raise ConfigurationError(
            "Test 1E awning qualification requires exactly one model probe; "
            "found {}".format(len(reports))
        )
    report_path = reports[0]
    checksum_path = report_path.with_suffix(report_path.suffix + ".sha256")
    if not checksum_path.is_file():
        raise ConfigurationError("Model-probe checksum is missing")
    expected = checksum_path.read_text(encoding="ascii").split()[0].lower()
    if expected != _sha256(report_path):
        raise ConfigurationError("Model-probe checksum mismatch")
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    if (
        payload.get("status") != "OPENINGS_DISCOVERED_READY_FOR_EXACT_TARGET_REVIEW"
        or payload.get("body_count") != 1
        or payload.get("opening_count") != 2
        or payload.get("readback_errors") != []
        or payload.get("scenario_sha256") != _sha256(scenario_path)
    ):
        raise ConfigurationError("Model probe is incomplete or stale")
    observed_ids = {
        str(opening.get("id") or "")
        for body in payload.get("bodies", ())
        for surface in body.get("surfaces", ())
        for opening in surface.get("openings", ())
    }
    if observed_ids != EXPECTED_OPENING_IDS:
        raise ConfigurationError(
            "Model probe opening identities changed: {}".format(sorted(observed_ids))
        )
    return report_path


def _live_targets(gateway: IesVeGateway) -> Tuple[Dict[str, Any], ...]:
    rows = []
    for body in gateway.model.get_bodies(False):
        for surface in body.get_surfaces():
            surface_properties = dict(surface.get_properties())
            for opening in surface.get_openings():
                opening_id = str(opening.get_id())
                if opening_id not in EXPECTED_OPENING_IDS:
                    continue
                opening_properties = dict(opening.get_properties())
                construction_readback = opening.get_construction()
                if construction_readback is None:
                    raise ConfigurationError(
                        "Opening {} has no assigned construction".format(opening_id)
                    )
                construction_id = gateway._construction_identifier(construction_readback)
                construction = (
                    construction_readback
                    if hasattr(construction_readback, "get_properties")
                    else gateway._get_construction(construction_id)
                )
                rows.append(
                    {
                        "body": body,
                        "surface": surface,
                        "opening": opening,
                        "opening_id": opening_id,
                        "opening_area_m2": float(opening_properties.get("area", 0.0)),
                        "surface_orientation_deg": float(
                            surface_properties.get("orientation", 0.0)
                        ),
                        "construction": construction,
                        "construction_id": construction_id,
                    }
                )
    if {row["opening_id"] for row in rows} != EXPECTED_OPENING_IDS:
        raise ConfigurationError("The two source-identified 1E windows are not live")
    for row in rows:
        if (
            abs(row["opening_area_m2"] - 6.0) > 1.0e-6
            or abs(row["surface_orientation_deg"] - 180.0) > 1.0e-6
            or not row["construction_id"]
        ):
            raise ConfigurationError(
                "Opening {} no longer matches the qualified south-window "
                "identity".format(row["opening_id"])
            )
    return tuple(sorted(rows, key=lambda item: item["opening_id"]))


def _write_plan(properties: Mapping[str, Any], control: Any) -> Dict[str, Any]:
    missing = sorted(set(WRITABLE_FIELDS) - set(properties))
    if missing:
        raise ConfigurationError(
            "Assigned glazing construction lacks shade fields: {}".format(missing)
        )
    if not isinstance(properties["external_shade_profile"], str):
        raise ConfigurationError("external_shade_profile is not a native string")
    return {
        "external_shade_active": _coerce_active_value(
            properties["external_shade_active"]
        ),
        # IESVE's documented discrete-control semantics evaluate the lower/
        # raise conditions only while the operation profile is off or none.
        # ``ON`` belongs solely to the fixed-closed 2E1 optical probe and would
        # force the dynamic 1E awning down continuously.
        "external_shade_profile": str(properties["external_shade_profile"]),
        "external_shade_transmittance_0": float(
            control.fixed_closed_candidate_setter_plan["external_shade_transmittance_0"]
        ),
        "external_shade_radiation_to_lower": _coerce_threshold_value(
            properties["external_shade_radiation_to_lower"],
            control.setter_plan["external_shade_radiation_to_lower"],
            "external_shade_radiation_to_lower",
        ),
        "external_shade_radiation_to_raise": _coerce_threshold_value(
            properties["external_shade_radiation_to_raise"],
            control.setter_plan["external_shade_radiation_to_raise"],
            "external_shade_radiation_to_raise",
        ),
    }


def qualify_test1e_awning(
    iesve_module: Any,
    project: Any,
    repository_root: Path,
) -> Path:
    """Apply and verify only the writable 1E awning subset in place."""

    project_path = Path(str(getattr(project, "path", "") or ""))
    if not project_path.is_dir() or is_temporary_ve_project(project_path):
        raise ConfigurationError("Save the dedicated Test 1E template project first")
    if project_path.name.casefold() != "sia4010_test1_1e_template":
        raise ConfigurationError("Awning qualification is restricted to the 1E template")
    scenario_path = project_path / "sia_model_scenario.json"
    scenario = ModelScenario.load(scenario_path)
    if not scenario.is_official or (scenario.variant, scenario.case_id) != (
        "test_1",
        "1E",
    ):
        raise ConfigurationError("Awning qualification requires official test_1/1E")
    prior = sorted((project_path / REPORT_DIRECTORY).glob("sia4010_test1e_awning_*.json"))
    if prior:
        latest = json.loads(prior[-1].read_text(encoding="utf-8"))
        safe_retry = (
            len(prior) == 1
            and latest.get("status") == "FAIL_RESTORED"
            and latest.get("mutation_performed") is False
            and latest.get("construction_mutations") == []
            and latest.get("restoration_errors") == []
        )
        if not safe_retry:
            raise ConfigurationError(
                "A 1E awning mutation already exists; inspect or discard the "
                "project: {}".format(prior[-1])
            )
    model_probe = _validated_model_probe(project_path, scenario_path)
    contract_path = repository_root / "config" / "sia4010_official_input_contract.json"
    contract = Sia4010OfficialInputContract.load(contract_path)
    control = build_test2a_fabric_awning_control(contract.test("2").confirmed_inputs)
    gateway = IesVeGateway(iesve_module)
    targets = _live_targets(gateway)
    constructions = {}
    for target in targets:
        constructions.setdefault(target["construction_id"], target["construction"])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    report_path = (
        project_path
        / REPORT_DIRECTORY
        / "sia4010_test1e_awning_{}.json".format(timestamp)
    )
    report: Dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "STARTED",
        "project_path": str(project_path),
        "scenario": scenario.to_dict(),
        "source_contracts": {
            "scenario": {"path": str(scenario_path), "sha256": _sha256(scenario_path)},
            "model_probe": {"path": str(model_probe), "sha256": _sha256(model_probe)},
            "official_input_contract": {
                "path": str(contract_path),
                "sha256": _sha256(contract_path),
            },
        },
        "target_openings": [
            {
                key: target[key]
                for key in (
                    "opening_id",
                    "opening_area_m2",
                    "surface_orientation_deg",
                    "construction_id",
                )
            }
            for target in targets
        ],
        "unique_construction_count": len(constructions),
        "fabric_awning_control": control.to_dict(),
        "construction_mutations": [],
        "mutation_performed": False,
        "readback_verified": False,
        "restoration_performed": False,
        "project_saved_by_script": False,
        "compliance_claim_allowed": False,
        "remaining_blockers": [
            "EXTERNAL_SHADE_SOLAR_VISIBLE_REFLECTANCE_SETTERS_UNAVAILABLE",
            "DYNAMIC_APS_EQUIVALENCE_NOT_YET_DEMONSTRATED",
            "INDEPENDENT_TEMPLATE_REVIEW_REQUIRED",
        ],
    }
    _write_json(report_path, report)

    originals = {}
    try:
        report["status"] = "MUTATION_STARTED"
        _write_json(report_path, report)
        for construction_id, construction in constructions.items():
            before = dict(construction.get_properties())
            plan = _write_plan(before, control)
            originals[construction_id] = {key: before[key] for key in WRITABLE_FIELDS}
            construction.set_properties(plan)
            after = dict(construction.get_properties())
            _assert_subset(plan, after)
            report["construction_mutations"].append(
                {
                    "construction_id": construction_id,
                    "before": originals[construction_id],
                    "written": plan,
                    "after": {key: after.get(key) for key in WRITABLE_FIELDS},
                }
            )
        report.update(
            {
                "status": "PROVISIONAL_AWNING_APPLIED_AND_READBACK_VERIFIED",
                "mutation_performed": True,
                "readback_verified": True,
                "next_action": (
                    "Save the project, then complete independent optical/template "
                    "review before capture. Do not claim Test 1 PASS yet."
                ),
            }
        )
    except Exception as exc:
        restoration_errors = []
        for construction_id, values in originals.items():
            construction = constructions[construction_id]
            try:
                construction.set_properties(values)
                _assert_subset(values, dict(construction.get_properties()))
            except Exception as restore_exc:
                restoration_errors.append(
                    "{}: {}: {}".format(
                        construction_id,
                        type(restore_exc).__name__,
                        restore_exc,
                    )
                )
        report.update(
            {
                "status": "FAIL_RESTORED" if not restoration_errors else "FAIL_UNSAFE",
                "error": "{}: {}".format(type(exc).__name__, exc),
                "restoration_performed": not restoration_errors,
                "restoration_errors": restoration_errors,
                "recovery_action": (
                    "Close without saving and discard this template copy."
                ),
            }
        )
        _write_json(report_path, report)
        raise VeMutationError(
            "Test 1E awning qualification failed; see {}".format(report_path)
        ) from exc

    _write_json(report_path, report)
    report_path.with_suffix(report_path.suffix + ".sha256").write_text(
        "{}  {}\n".format(_sha256(report_path), report_path.name),
        encoding="ascii",
    )
    return report_path


def verify_test1e_awning_persistence(
    iesve_module: Any,
    project: Any,
) -> Path:
    """Verify the saved/reopened model still exposes the exact written subset."""

    project_path = Path(str(getattr(project, "path", "") or ""))
    if not project_path.is_dir() or is_temporary_ve_project(project_path):
        raise ConfigurationError("Open the saved Test 1E template project first")
    scenario_path = project_path / "sia_model_scenario.json"
    scenario = ModelScenario.load(scenario_path)
    if (scenario.variant, scenario.case_id) != ("test_1", "1E"):
        raise ConfigurationError("Persistence verification requires test_1/1E")
    reports = sorted(
        (project_path / REPORT_DIRECTORY).glob("sia4010_test1e_awning_*.json")
    )
    successful = []
    for path in reports:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if payload.get("status") in {
            "PROVISIONAL_AWNING_APPLIED_AND_READBACK_VERIFIED",
            "PROVISIONAL_AWNING_REASSIGNED_AND_READBACK_VERIFIED",
        }:
            successful.append((path, payload))
    reassigned = [
        item
        for item in successful
        if item[1].get("opening_reassignment_performed") is True
    ]
    selected = reassigned if reassigned else successful
    if len(selected) != 1:
        raise ConfigurationError(
            "Expected exactly one applicable successful 1E awning report; found "
            "{}".format(len(selected))
        )
    mutation_path, mutation = selected[0]
    checksum_path = mutation_path.with_suffix(mutation_path.suffix + ".sha256")
    if not checksum_path.is_file() or checksum_path.read_text(encoding="ascii").split()[
        0
    ].lower() != _sha256(mutation_path):
        raise ConfigurationError("Successful awning report checksum mismatch")

    persisted_candidates = list(project_path.glob("*.mdl"))
    project_content = project_path / "Project Content.db"
    if project_content.is_file():
        persisted_candidates.append(project_content)
    newest_persisted = max(
        (path.stat().st_mtime for path in persisted_candidates),
        default=0.0,
    )
    if newest_persisted <= mutation_path.stat().st_mtime:
        raise ConfigurationError(
            "No VE project file is newer than the awning mutation. Save, close "
            "and reopen the project before persistence verification."
        )

    gateway = IesVeGateway(iesve_module)
    targets = _live_targets(gateway)
    constructions = {
        target["construction_id"]: target["construction"] for target in targets
    }
    expected_by_id = {
        str(item.get("construction_id") or ""): {
            **(item.get("written") or {}),
            "external_shade_profile": str(
                (item.get("before") or {}).get("external_shade_profile", "")
            ),
        }
        for item in mutation.get("construction_mutations", ())
    }
    if set(expected_by_id) != set(constructions):
        raise ConfigurationError("Live construction identities changed after mutation")
    readback = []
    for construction_id, construction in sorted(constructions.items()):
        properties = dict(construction.get_properties())
        expected = expected_by_id[construction_id]
        comparable = {
            key: value
            for key, value in expected.items()
            if key != "external_shade_profile"
        }
        _assert_subset(comparable, properties)
        actual_profile = str(properties.get("external_shade_profile", ""))
        if actual_profile.strip().casefold() not in {"", "none", "off"}:
            raise VeMutationError(
                "Test 1E dynamic shade requires an OFF/NONE operation profile; "
                "read back {!r}".format(actual_profile)
            )
        readback.append(
            {
                "construction_id": construction_id,
                "expected": expected,
                "actual": {key: properties.get(key) for key in expected},
            }
        )

    output = project_path / REPORT_DIRECTORY / "sia4010_test1e_awning_persistence.json"
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "PERSISTED_AWNING_READBACK_VERIFIED",
        "project_path": str(project_path),
        "scenario": {"variant": scenario.variant, "case_id": scenario.case_id},
        "mutation_report": {
            "path": str(mutation_path),
            "sha256": _sha256(mutation_path),
        },
        "persisted_project_files": [
            {
                "path": str(path),
                "modified_epoch": path.stat().st_mtime,
                "sha256": _sha256(path),
            }
            for path in persisted_candidates
            if path.is_file()
        ],
        "opening_ids": sorted(EXPECTED_OPENING_IDS),
        "construction_readback": readback,
        "mutation_performed": False,
        "project_saved_by_script": False,
        "compliance_claim_allowed": False,
        "remaining_blockers": mutation.get("remaining_blockers", []),
        "next_action": (
            "Capture the active project as a Test 1E template candidate and "
            "complete independent review before qualification."
        ),
    }
    _write_json(output, payload)
    output.with_suffix(output.suffix + ".sha256").write_text(
        "{}  {}\n".format(_sha256(output), output.name),
        encoding="ascii",
    )
    return output


def reapply_test1e_awning_with_opening_assignment(
    iesve_module: Any,
    project: Any,
) -> Path:
    """Reapply the proven subset and reassign EXTW to force model serialization."""

    project_path = Path(str(getattr(project, "path", "") or ""))
    scenario_path = project_path / "sia_model_scenario.json"
    scenario = ModelScenario.load(scenario_path)
    if (scenario.variant, scenario.case_id) != ("test_1", "1E"):
        raise ConfigurationError("Reassignment requires official test_1/1E")
    reports = sorted(
        (project_path / REPORT_DIRECTORY).glob("sia4010_test1e_awning_*.json")
    )
    originals = []
    for path in reports:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("status") == "PROVISIONAL_AWNING_APPLIED_AND_READBACK_VERIFIED":
            originals.append((path, payload))
    if len(originals) != 1:
        raise ConfigurationError(
            "Reassignment requires exactly one prior in-memory PASS; found {}".format(
                len(originals)
            )
        )
    original_path, original = originals[0]
    original_checksum = original_path.with_suffix(original_path.suffix + ".sha256")
    if not original_checksum.is_file() or original_checksum.read_text(
        encoding="ascii"
    ).split()[0].lower() != _sha256(original_path):
        raise ConfigurationError("Prior awning PASS checksum mismatch")
    if any(
        payload.get("opening_reassignment_performed") is True
        for path in reports
        for payload in [json.loads(path.read_text(encoding="utf-8"))]
    ):
        raise ConfigurationError("Opening reassignment already ran in this project")

    gateway = IesVeGateway(iesve_module)
    targets = _live_targets(gateway)
    constructions = {
        target["construction_id"]: target["construction"] for target in targets
    }
    mutations = {
        str(item.get("construction_id") or ""): item
        for item in original.get("construction_mutations", ())
    }
    if set(mutations) != set(constructions):
        raise ConfigurationError("Prior and live construction identities differ")
    for construction_id, construction in constructions.items():
        _assert_subset(
            mutations[construction_id]["before"],
            dict(construction.get_properties()),
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    report_path = (
        project_path
        / REPORT_DIRECTORY
        / "sia4010_test1e_awning_reassignment_{}.json".format(timestamp)
    )
    report = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "STARTED",
        "project_path": str(project_path),
        "scenario": scenario.to_dict(),
        "source_mutation_report": {
            "path": str(original_path),
            "sha256": _sha256(original_path),
        },
        "target_opening_ids": [target["opening_id"] for target in targets],
        "construction_mutations": [],
        "opening_assignments": [],
        "mutation_performed": False,
        "opening_reassignment_performed": False,
        "project_saved_by_script": False,
        "compliance_claim_allowed": False,
        "remaining_blockers": original.get("remaining_blockers", []),
    }
    _write_json(report_path, report)
    changed = []
    try:
        report["status"] = "MUTATION_STARTED"
        _write_json(report_path, report)
        for construction_id, construction in constructions.items():
            before = dict(construction.get_properties())
            written = mutations[construction_id]["written"]
            construction.set_properties(written)
            after = dict(construction.get_properties())
            _assert_subset(written, after)
            changed.append(construction_id)
            report["construction_mutations"].append(
                {
                    "construction_id": construction_id,
                    "before": {key: before.get(key) for key in WRITABLE_FIELDS},
                    "written": written,
                    "after": {key: after.get(key) for key in WRITABLE_FIELDS},
                }
            )
        for target in targets:
            target["body"].assign_construction_to_opening(
                target["construction"],
                target["surface"],
                target["opening"].get_id(),
            )
            readback_id = gateway._construction_identifier(
                target["opening"].get_construction()
            )
            if readback_id != target["construction_id"]:
                raise VeMutationError(
                    "Opening {} construction read-back mismatch".format(
                        target["opening_id"]
                    )
                )
            report["opening_assignments"].append(
                {
                    "opening_id": target["opening_id"],
                    "construction_id": readback_id,
                    "readback_verified": True,
                }
            )
        report.update(
            {
                "status": "PROVISIONAL_AWNING_REASSIGNED_AND_READBACK_VERIFIED",
                "mutation_performed": True,
                "opening_reassignment_performed": True,
                "next_action": "Save, close, reopen, then verify persistence.",
            }
        )
    except Exception as exc:
        restoration_errors = []
        for construction_id in changed:
            try:
                values = mutations[construction_id]["before"]
                constructions[construction_id].set_properties(values)
                _assert_subset(
                    values, dict(constructions[construction_id].get_properties())
                )
            except Exception as restore_exc:
                restoration_errors.append("{}: {}".format(construction_id, restore_exc))
        report.update(
            {
                "status": "FAIL_RESTORED" if not restoration_errors else "FAIL_UNSAFE",
                "error": "{}: {}".format(type(exc).__name__, exc),
                "restoration_errors": restoration_errors,
                "recovery_action": "Close without saving and discard this copy.",
            }
        )
        _write_json(report_path, report)
        raise VeMutationError(
            "Test 1E opening reassignment failed; see {}".format(report_path)
        ) from exc
    _write_json(report_path, report)
    report_path.with_suffix(report_path.suffix + ".sha256").write_text(
        "{}  {}\n".format(_sha256(report_path), report_path.name),
        encoding="ascii",
    )
    return report_path


def apply_test1e_provisional_angular_diagnostic(
    iesve_module: Any,
    project: Any,
    *,
    angular_transmittance: float = 0.04,
    diagnostic_label: str = "PROVISIONAL_ENGINEERING_ASSUMPTION",
) -> Path:
    """Apply a guarded angular subset for a diagnostic or sensitivity run.

    The default repeats the source normal-incidence value through 75 degrees.
    A non-default value is a numerical sensitivity input, never a source input.
    Neither route can authorize a Test 1 acceptance claim.  The VE 2025 Python
    API also cannot write either shade reflectance.
    """

    value = float(angular_transmittance)
    if not 0.0 <= value <= 1.0:
        raise ConfigurationError("Angular transmittance must be between 0 and 1")
    plan = {
        key: (0.0 if key == "external_shade_transmittance_90" else value)
        for key in PROVISIONAL_ANGULAR_TRANSMITTANCE_PLAN
    }

    project_path = Path(str(getattr(project, "path", "") or ""))
    if not project_path.is_dir() or is_temporary_ve_project(project_path):
        raise ConfigurationError("Open the saved disposable Test 1E project first")
    if project_path.name.casefold() != "sia4010_test_1_1e_disposable":
        raise ConfigurationError(
            "The provisional angular diagnostic is restricted to "
            "SIA4010_TEST_1_1E_DISPOSABLE"
        )
    scenario = ModelScenario.load(project_path / "sia_model_scenario.json")
    if (scenario.variant, scenario.case_id) != ("test_1", "1E"):
        raise ConfigurationError("Angular diagnostic requires test_1/1E")

    gateway = IesVeGateway(iesve_module)
    targets = _live_targets(gateway)
    constructions = {
        target["construction_id"]: target["construction"] for target in targets
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    report_path = (
        project_path
        / REPORT_DIRECTORY
        / "sia4010_test1e_provisional_angular_diagnostic_{}.json".format(timestamp)
    )
    report: Dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "STARTED",
        "project_path": str(project_path),
        "scenario": scenario.to_dict(),
        "source_status": diagnostic_label,
        "assumption": (
            "Direct shade transmittance {:.6g} repeated from 0 through 75 "
            "degrees; 90-degree transmittance set to zero. No reviewed angular "
            "curve is available."
        ).format(value),
        "sensitivity_derivation": (
            "Non-default values are bracketed from the qualified unshaded 1D "
            "result and the prior 1E result. They are exploratory numerical "
            "sensitivities, not SIA or manufacturer inputs."
        ),
        "written_plan": dict(plan),
        "construction_mutations": [],
        "opening_assignments": [],
        "mutation_performed": False,
        "readback_verified": False,
        "project_saved_by_script": False,
        "compliance_claim_allowed": False,
        "remaining_manual_inputs": {
            "external_shade_solar_reflectance": 0.490,
            "external_shade_visible_reflectance": 0.496,
        },
        "remaining_blockers": [
            "ANGULAR_CURVE_NOT_AUTHORITY_CONFIRMED",
            "EXTERNAL_SHADE_REFLECTANCE_SETTERS_UNAVAILABLE",
            "APS_EQUIVALENCE_NOT_YET_DEMONSTRATED",
            "TEMPLATE_SIGNATURE_REQUALIFICATION_REQUIRED",
        ],
    }
    _write_json(report_path, report)

    originals: Dict[str, Dict[str, Any]] = {}
    changed = []
    try:
        for construction_id, construction in constructions.items():
            before = dict(construction.get_properties())
            missing = sorted(set(plan) - set(before))
            if missing:
                raise ConfigurationError(
                    "Construction {} lacks angular shade fields: {}".format(
                        construction_id, missing
                    )
                )
            originals[construction_id] = {key: before[key] for key in plan}
            construction.set_properties(plan)
            after = dict(construction.get_properties())
            _assert_subset(plan, after)
            changed.append(construction_id)
            report["construction_mutations"].append(
                {
                    "construction_id": construction_id,
                    "before": originals[construction_id],
                    "written": dict(plan),
                    "after": {key: after.get(key) for key in plan},
                }
            )
        for target in targets:
            target["body"].assign_construction_to_opening(
                target["construction"],
                target["surface"],
                target["opening"].get_id(),
            )
            readback_id = gateway._construction_identifier(
                target["opening"].get_construction()
            )
            if readback_id != target["construction_id"]:
                raise VeMutationError(
                    "Opening {} construction read-back mismatch".format(
                        target["opening_id"]
                    )
                )
            report["opening_assignments"].append(
                {
                    "opening_id": target["opening_id"],
                    "construction_id": readback_id,
                    "readback_verified": True,
                }
            )
        report.update(
            {
                "status": "PROVISIONAL_ANGULAR_DIAGNOSTIC_APPLIED_AND_READBACK_VERIFIED",
                "mutation_performed": True,
                "readback_verified": True,
                "next_action": (
                    "Manually enter the two controlled reflectances in APcdb, "
                    "save, close, reopen, and run the optical readback."
                ),
            }
        )
    except Exception as exc:
        restoration_errors = []
        for construction_id in changed:
            try:
                constructions[construction_id].set_properties(originals[construction_id])
                _assert_subset(
                    originals[construction_id],
                    dict(constructions[construction_id].get_properties()),
                )
            except Exception as restore_exc:
                restoration_errors.append("{}: {}".format(construction_id, restore_exc))
        report.update(
            {
                "status": "FAIL_RESTORED" if not restoration_errors else "FAIL_UNSAFE",
                "error": "{}: {}".format(type(exc).__name__, exc),
                "restoration_errors": restoration_errors,
                "recovery_action": "Close without saving if status is FAIL_UNSAFE.",
            }
        )
        _write_json(report_path, report)
        raise VeMutationError(
            "Test 1E angular diagnostic failed; see {}".format(report_path)
        ) from exc

    _write_json(report_path, report)
    report_path.with_suffix(report_path.suffix + ".sha256").write_text(
        "{}  {}\n".format(_sha256(report_path), report_path.name),
        encoding="ascii",
    )
    return report_path
