"""Assign the verified Test 1E equivalent glazing to the two target windows.

This is a guarded diagnostic operation.  It never saves the VE project and it
does not turn the equivalent construction into an official product definition
or a SIA compliance result.
"""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

EXPECTED_PROJECT_PREFIX = "sia4010_test1_1e_equivalent_glazing_disposable"
CREATION_REPORT = (
    Path("sia4010_artifacts")
    / "diagnostics"
    / "sia4010_test1e_equivalent_5layer_glazing.json"
)
ASSIGNMENT_REPORT = (
    Path("sia4010_artifacts")
    / "diagnostics"
    / "sia4010_test1e_equivalent_5layer_assignment.json"
)
SHADE_PLAN = {
    "external_shade_active": 1,
    # NONE leaves the irradiance expressions in authority-confirmed control.
    "external_shade_profile": "NONE",
    "external_shade_radiation_to_lower": "ii>150.0",
    "external_shade_radiation_to_raise": "ii<150.0",
    # This constant angular subset is an explicit diagnostic assumption.
    "external_shade_transmittance_0": 0.04,
    "external_shade_transmitance_15": 0.04,
    "external_shade_transmittance_30": 0.04,
    "external_shade_transmittance_45": 0.04,
    "external_shade_transmittance_60": 0.04,
    "external_shade_transmitance_75": 0.04,
    "external_shade_transmittance_90": 0.0,
}


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def run():
    import iesve  # type: ignore

    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.sia4010.test1e_awning_qualification import (
        _live_targets,
    )
    from swiss_sia.reference_model.sia4010.test2a_shading_qualification import (
        _assert_subset,
    )
    from swiss_sia.reference_model.ve_api import IesVeGateway

    project = iesve.VEProject.get_current_project()
    project_path = Path(str(getattr(project, "path", "") or "")).resolve()
    if not project_path.name.casefold().startswith(EXPECTED_PROJECT_PREFIX):
        raise RuntimeError(
            "Open the equivalent-glazing disposable project first; active folder: "
            + project_path.name
        )
    scenario = ModelScenario.load(project_path / "sia_model_scenario.json")
    if (scenario.variant, scenario.case_id) != ("test_1", "1E"):
        raise RuntimeError("Equivalent assignment requires official test_1/1E")

    creation_path = project_path / CREATION_REPORT
    if not creation_path.is_file():
        raise RuntimeError("Run the equivalent 5-layer creation script first")
    creation = json.loads(creation_path.read_text(encoding="utf-8"))
    if (
        creation.get("status")
        != "UNASSIGNED_EQUIVALENT_5LAYER_CREATED_AND_VERIFIED"
        or creation.get("assigned_to_openings") is not False
    ):
        raise RuntimeError("The equivalent-glazing creation receipt is not eligible")
    construction_id = str(creation.get("construction_id") or "")
    if not construction_id:
        raise RuntimeError("The creation receipt has no construction identifier")

    report_path = project_path / ASSIGNMENT_REPORT
    if report_path.exists():
        raise RuntimeError(
            "An assignment receipt already exists. Do not repeat the mutation; "
            "run the persistence verifier after saving and reopening."
        )

    gateway = IesVeGateway(iesve)
    targets = _live_targets(gateway)
    candidate = gateway._get_construction(construction_id)
    candidate_before = dict(candidate.get_properties())
    missing = sorted(set(SHADE_PLAN) - set(candidate_before))
    if missing:
        raise RuntimeError("Equivalent construction lacks shade fields: {}".format(missing))

    report = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "STARTED",
        "project": str(project_path),
        "scenario": scenario.to_dict(),
        "creation_report": str(creation_path),
        "creation_report_sha256": _sha256(creation_path),
        "candidate_construction_id": construction_id,
        "shade_plan": dict(SHADE_PLAN),
        "opening_assignments": [],
        "mutation_performed": False,
        "project_saved_by_script": False,
        "compliance_claim_allowed": False,
    }
    _write(report_path, report)

    original_assignments = {
        target["opening_id"]: target["construction"] for target in targets
    }
    assigned = []
    try:
        candidate.set_properties(SHADE_PLAN)
        candidate_after = dict(candidate.get_properties())
        _assert_subset(SHADE_PLAN, candidate_after)
        report["candidate_shade_readback"] = {
            key: candidate_after.get(key) for key in SHADE_PLAN
        }

        for target in targets:
            target["body"].assign_construction_to_opening(
                candidate, target["surface"], target["opening"].get_id()
            )
            assigned.append(target)
            readback_id = gateway._construction_identifier(
                target["opening"].get_construction()
            )
            if readback_id != construction_id:
                raise RuntimeError(
                    "Opening {} read back construction {} instead of {}".format(
                        target["opening_id"], readback_id, construction_id
                    )
                )
            report["opening_assignments"].append(
                {
                    "opening_id": target["opening_id"],
                    "area_m2": target["opening_area_m2"],
                    "orientation_deg": target["surface_orientation_deg"],
                    "original_construction_id": target["construction_id"],
                    "assigned_construction_id": readback_id,
                    "readback_verified": True,
                }
            )
        report.update(
            {
                "status": "EQUIVALENT_5LAYER_ASSIGNED_AND_READBACK_VERIFIED",
                "mutation_performed": True,
                "assignment_count": len(assigned),
                "limitations": [
                    "Equivalent glass layers remain a proxy rather than a manufacturer product definition.",
                    "The constant 0.04 angular transmittance through 75 degrees is a diagnostic assumption.",
                    "Solar and visible shade reflectance remain unavailable to the Python setter.",
                    "A new APS comparison is required; this receipt is not a Test 1 PASS.",
                ],
                "next_action": (
                    "Press Ctrl+S, close and reopen this project, then run "
                    "Run_VE_SIA4010_Test1E_Verify_Equivalent_5Layer_Persistence.py."
                ),
            }
        )
    except Exception as exc:
        restoration_errors = []
        for target in reversed(assigned):
            try:
                target["body"].assign_construction_to_opening(
                    original_assignments[target["opening_id"]],
                    target["surface"],
                    target["opening"].get_id(),
                )
            except Exception as restore_exc:
                restoration_errors.append(
                    "opening {}: {}".format(target["opening_id"], restore_exc)
                )
        try:
            candidate.set_properties(
                {key: candidate_before[key] for key in SHADE_PLAN}
            )
            _assert_subset(
                {key: candidate_before[key] for key in SHADE_PLAN},
                dict(candidate.get_properties()),
            )
        except Exception as restore_exc:
            restoration_errors.append("candidate shade: {}".format(restore_exc))
        report.update(
            {
                "status": "FAILED_RESTORED" if not restoration_errors else "FAILED_UNSAFE",
                "error": "{}: {}".format(type(exc).__name__, exc),
                "restoration_errors": restoration_errors,
                "recovery_action": "Close this project without saving and discard the copy.",
            }
        )
        _write(report_path, report)
        raise RuntimeError("Equivalent glazing assignment failed; see {}".format(report_path)) from exc

    _write(report_path, report)
    report_path.with_suffix(report_path.suffix + ".sha256").write_text(
        "{}  {}\n".format(_sha256(report_path), report_path.name), encoding="ascii"
    )
    print("SIA 4010 TEST 1E EQUIVALENT GLAZING ASSIGNMENT: {}".format(report["status"]))
    print("Construction: {}".format(construction_id))
    print("Openings assigned and read back: {}".format(len(assigned)))
    print("Shade control: 150/150 W/m2; diagnostic direct transmittance: 0.04")
    print("Project saved by script: NO")
    print("Report: {}".format(report_path))
    print("NEXT: Ctrl+S, close, reopen, then run the persistence verifier.")
    print("This is a diagnostic assignment, not a Test 1 PASS.")
    return report_path


if __name__ == "__main__":
    run()
