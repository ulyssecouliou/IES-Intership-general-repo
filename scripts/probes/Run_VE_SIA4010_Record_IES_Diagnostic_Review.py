"""Record an IES-reviewed Test 1E diagnostic model with explicit reservations.

This launcher never creates a QUALIFIED template or a compliance claim.  It
binds the user's confirmed IES review to the captured semantic model signature,
the persisted awning proof and the known VE 2025 limitations, then creates the
guarded model evidence required for a diagnostic ApacheSim run.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load(path, context):
    if not path.is_file():
        raise RuntimeError("Missing {}: {}".format(context, path))
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _file_evidence(path):
    return {"path": str(path), "sha256": _sha256(path)}


def run():
    import iesve

    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.sia4010.template_strategy import project_signature

    project = iesve.VEProject.get_current_project()
    project_path = Path(str(getattr(project, "path", "") or "")).resolve()
    scenario_path = project_path / "sia_model_scenario.json"
    scenario = ModelScenario.load(scenario_path)
    if (scenario.variant, scenario.case_id) != ("test_1", "1E"):
        raise RuntimeError("IES diagnostic review requires active test_1/1E")

    templates = project_path / "sia4010_artifacts" / "templates"
    diagnostics = project_path / "sia4010_artifacts" / "diagnostics"
    candidate_path = templates / "sia4010_template_candidate.json"
    persistence_path = diagnostics / "sia4010_test1e_awning_persistence.json"
    candidate = _load(candidate_path, "captured template candidate")
    persistence = _load(persistence_path, "persisted awning proof")
    if candidate.get("status") != "CANDIDATE_REQUIRES_INDEPENDENT_REVIEW":
        raise RuntimeError("Template candidate status is not reviewable")
    if persistence.get("status") != "PERSISTED_AWNING_READBACK_VERIFIED":
        raise RuntimeError("Persisted Test 1E awning proof is incomplete")

    current = project_signature(project_path)
    captured_signature = str(candidate.get("template_signature_sha256") or "").lower()
    current_signature = str(current.get("template_signature_sha256") or "").lower()
    if captured_signature != current_signature:
        raise RuntimeError(
            "The VE model changed after candidate capture; recapture before review"
        )

    reservations = [
        {
            "code": "EXTERNAL_SHADE_REFLECTANCE_FIELDS_UNAVAILABLE_IN_VE2025",
            "observed": {"solar": 0.10, "visible": 0.10},
            "source_target": {"solar": 0.490, "visible": 0.496},
        },
        {
            "code": "ANGULAR_SHADE_CURVE_NOT_AUTHORITY_CONFIRMED",
            "observed": "0.04 from 0 through 90 degrees",
        },
        {
            "code": "APACHESIM_AIR_SPECIFIC_HEAT_BINDING_PROVISIONAL",
            "observed": "1005 J/(kg K)",
        },
    ]
    now = datetime.now(timezone.utc).isoformat()
    review_path = templates / "sia4010_diagnostic_review.json"
    review = {
        "schema_version": "1.0",
        "status": "DIAGNOSTIC_REVIEWED_WITH_RESERVATIONS",
        "reviewer": "IES",
        "reviewed_at": now,
        "covered_cases": ["test_1/1E"],
        "template_signature_sha256": current_signature,
        "reservations": reservations,
        "independent_template_review_complete": True,
        "compliance_claim_allowed": False,
        "claim_guardrail": (
            "IES review authorizes a diagnostic run only. It does not qualify "
            "the template, establish a Test 1 PASS or grant SIA validation."
        ),
    }
    _write(review_path, review)

    evidence_path = templates / "template_model_evidence.json"
    evidence = {
        "schema_version": "1.0",
        "status": "DIAGNOSTIC_REVIEWED_MODEL_VERIFIED",
        "variant": "test_1",
        "case_id": "1E",
        "template_id": "SIA4010_TEST1_1E_IES_DIAGNOSTIC_REVIEWED_20260827",
        "project_path": str(project_path),
        "scenario_path": str(scenario_path),
        "scenario_sha256": _sha256(scenario_path),
        "candidate_manifest": str(candidate_path),
        "candidate_manifest_path": str(candidate_path),
        "candidate_manifest_sha256": _sha256(candidate_path),
        "persistence_report": str(persistence_path),
        "persistence_report_path": str(persistence_path),
        "persistence_report_sha256": _sha256(persistence_path),
        "diagnostic_review": str(review_path),
        "diagnostic_review_path": str(review_path),
        "diagnostic_review_sha256": _sha256(review_path),
        "template_signature_sha256": current_signature,
        "critical_file_count": current.get("critical_file_count"),
        "verified_at": now,
        "diagnostic_scope": "TEST1E_IES_REVIEWED_WITH_RESERVATIONS",
        "independent_template_review_complete": True,
        "reservations": reservations,
        "workflow_status": "DIAGNOSTIC_ONLY",
        "compliance_claim_allowed": False,
        "claim_guardrail": review["claim_guardrail"],
    }
    _write(evidence_path, evidence)

    print("SIA 4010 TEST 1E IES REVIEW: DIAGNOSTIC_REVIEWED_MODEL_VERIFIED")
    print("Project: {}".format(project_path))
    print("Reviewer: IES")
    print("Reservations: {}".format(len(reservations)))
    print("Review: {}".format(review_path))
    print("Model proof: {}".format(evidence_path))
    print("Compliance claim allowed: NO")
    print("NEXT: run Run_VE_SIA4010_Simulate_Qualified_Template.py")
    return evidence_path


if __name__ == "__main__":
    run()
