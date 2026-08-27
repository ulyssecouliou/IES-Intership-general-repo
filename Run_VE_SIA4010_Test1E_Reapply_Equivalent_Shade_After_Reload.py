"""Reapply the Test 1E shade subset after the new construction has persisted.

VE 2025 may persist a newly created CDB construction and its assignments while
resetting shade properties written in the creation session.  This guarded
second pass targets only the already-persisted and already-assigned equivalent
construction.  It never saves the project.
"""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPECTED_PROJECT_PREFIX = "sia4010_test1_1e_equivalent_glazing_disposable"
ASSIGNMENT_REPORT = Path("sia4010_artifacts/diagnostics/sia4010_test1e_equivalent_5layer_assignment.json")
REAPPLICATION_REPORT = Path("sia4010_artifacts/diagnostics/sia4010_test1e_equivalent_shade_reapplication.json")


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run():
    import iesve  # type: ignore

    from swiss_sia.reference_model.sia4010.test1e_awning_qualification import _live_targets
    from swiss_sia.reference_model.sia4010.test2a_shading_qualification import _assert_subset
    from swiss_sia.reference_model.ve_api import IesVeGateway

    project = iesve.VEProject.get_current_project()
    project_path = Path(str(getattr(project, "path", "") or "")).resolve()
    if not project_path.name.casefold().startswith(EXPECTED_PROJECT_PREFIX):
        raise RuntimeError("Open the saved equivalent-glazing disposable project first")

    assignment_path = project_path / ASSIGNMENT_REPORT
    checksum_path = assignment_path.with_suffix(assignment_path.suffix + ".sha256")
    if not assignment_path.is_file() or not checksum_path.is_file():
        raise RuntimeError("The checksum-bound equivalent assignment receipt is missing")
    checksum = checksum_path.read_text(encoding="ascii").split()[0].lower()
    if checksum != _sha256(assignment_path):
        raise RuntimeError("The equivalent assignment receipt checksum does not match")
    assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
    if assignment.get("status") != "EQUIVALENT_5LAYER_ASSIGNED_AND_READBACK_VERIFIED":
        raise RuntimeError("The equivalent assignment receipt is not eligible")

    report_path = project_path / REAPPLICATION_REPORT
    if report_path.exists():
        raise RuntimeError(
            "This guarded reapplication has already run. If persistence still "
            "fails, send the verifier output; do not repeat mutations blindly."
        )

    gateway = IesVeGateway(iesve)
    targets = _live_targets(gateway)
    construction_id = str(assignment["candidate_construction_id"])
    if any(target["construction_id"] != construction_id for target in targets):
        raise RuntimeError("The two windows no longer use the equivalent construction")
    construction = gateway._get_construction(construction_id)
    before = dict(construction.get_properties())
    plan = dict(assignment["shade_plan"])
    missing = sorted(set(plan) - set(before))
    if missing:
        raise RuntimeError("Persisted construction lacks shade fields: {}".format(missing))

    report = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "STARTED",
        "project": str(project_path),
        "assignment_report": str(assignment_path),
        "assignment_report_sha256": checksum,
        "construction_id": construction_id,
        "before": {key: before.get(key) for key in plan},
        "written": plan,
        "opening_assignments": [],
        "project_saved_by_script": False,
        "compliance_claim_allowed": False,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    try:
        construction.set_properties(plan)
        after = dict(construction.get_properties())
        _assert_subset(plan, after)
        for target in targets:
            target["body"].assign_construction_to_opening(
                construction, target["surface"], target["opening"].get_id()
            )
            readback_id = gateway._construction_identifier(target["opening"].get_construction())
            if readback_id != construction_id:
                raise RuntimeError("Opening assignment read-back changed")
            report["opening_assignments"].append(
                {"opening_id": target["opening_id"], "construction_id": readback_id}
            )
        report.update(
            {
                "status": "PERSISTED_CONSTRUCTION_SHADE_REAPPLIED_AND_READBACK_VERIFIED",
                "after": {key: after.get(key) for key in plan},
                "next_action": (
                    "Press Ctrl+S, close and reopen the project, then rerun the "
                    "equivalent 5-layer persistence verifier."
                ),
            }
        )
    except Exception as exc:
        restoration_errors = []
        try:
            original = {key: before[key] for key in plan}
            construction.set_properties(original)
            _assert_subset(original, dict(construction.get_properties()))
        except Exception as restore_exc:
            restoration_errors.append(str(restore_exc))
        report.update(
            {
                "status": "FAILED_RESTORED" if not restoration_errors else "FAILED_UNSAFE",
                "error": "{}: {}".format(type(exc).__name__, exc),
                "restoration_errors": restoration_errors,
                "recovery_action": "Close without saving if restoration was unsafe.",
            }
        )
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError("Equivalent shade reapplication failed; see {}".format(report_path)) from exc

    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    report_path.with_suffix(report_path.suffix + ".sha256").write_text(
        "{}  {}\n".format(_sha256(report_path), report_path.name), encoding="ascii"
    )
    print("SIA 4010 TEST 1E EQUIVALENT SHADE REAPPLICATION: {}".format(report["status"]))
    print("Construction: {}; openings reassigned: {}".format(construction_id, len(targets)))
    print("Shade control: 150/150 W/m2; diagnostic direct transmittance: 0.04")
    print("Project saved by script: NO")
    print("Report: {}".format(report_path))
    print("NEXT: Ctrl+S, close, reopen, then rerun the persistence verifier.")
    print("This remains a diagnostic equivalent, not a Test 1 PASS.")
    return report_path


if __name__ == "__main__":
    run()
