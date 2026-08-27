"""Bind the captured equivalent Test 1E model for diagnostic simulation only."""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPECTED_PROJECT_PREFIX = "sia4010_test1_1e_equivalent_glazing_disposable"
DIAGNOSTIC_STATUS = "DIAGNOSTIC_EQUIVALENT_MODEL_VERIFIED"


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run():
    import iesve  # type: ignore

    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.sia4010.template_strategy import project_signature

    project = iesve.VEProject.get_current_project()
    project_path = Path(str(getattr(project, "path", "") or "")).resolve()
    if not project_path.name.casefold().startswith(EXPECTED_PROJECT_PREFIX):
        raise RuntimeError("Open the captured equivalent-glazing disposable project first")
    scenario_path = project_path / "sia_model_scenario.json"
    scenario = ModelScenario.load(scenario_path)
    if (scenario.variant, scenario.case_id) != ("test_1", "1E") or not scenario.is_official:
        raise RuntimeError("Equivalent diagnostic preparation requires official test_1/1E")

    template_dir = project_path / "sia4010_artifacts" / "templates"
    candidate_path = template_dir / "sia4010_template_candidate.json"
    persistence_path = (
        project_path
        / "sia4010_artifacts"
        / "diagnostics"
        / "sia4010_test1e_equivalent_5layer_persistence.json"
    )
    if not candidate_path.is_file() or not persistence_path.is_file():
        raise RuntimeError("Candidate capture and persistence receipt are both required")
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    persistence = json.loads(persistence_path.read_text(encoding="utf-8"))
    if candidate.get("status") != "CANDIDATE_REQUIRES_INDEPENDENT_REVIEW":
        raise RuntimeError("Template candidate status is invalid")
    if persistence.get("status") != "EQUIVALENT_5LAYER_ASSIGNMENT_PERSISTENCE_VERIFIED":
        raise RuntimeError("Equivalent glazing persistence is not verified")
    signature = project_signature(project_path)
    current_digest = str(signature["template_signature_sha256"]).lower()
    if str(candidate.get("template_signature_sha256") or "").lower() != current_digest:
        raise RuntimeError("The active VE model changed after candidate capture")

    output = template_dir / "template_model_evidence.json"
    payload = {
        "schema_version": "1.0",
        "status": DIAGNOSTIC_STATUS,
        "variant": "test_1",
        "case_id": "1E",
        "template_id": "SIA4010_TEST1_1E_EQUIVALENT_GLAZING_DIAGNOSTIC_20260826",
        "project_path": str(project_path),
        "scenario_path": str(scenario_path),
        "scenario_sha256": _sha256(scenario_path),
        "candidate_manifest_path": str(candidate_path),
        "candidate_manifest_sha256": _sha256(candidate_path),
        "persistence_report_path": str(persistence_path),
        "persistence_report_sha256": _sha256(persistence_path),
        "template_signature_sha256": current_digest,
        "critical_file_count": signature["critical_file_count"],
        "diagnostic_scope": "TEST1E_EQUIVALENT_GLAZING_SENSITIVITY",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "workflow_status": "DIAGNOSTIC_INPUT_VERIFIED",
        "independent_template_review_complete": False,
        "compliance_claim_allowed": False,
        "claim_guardrail": (
            "This proves exact identity of the persisted equivalent-glazing "
            "diagnostic model only. It is not an independently qualified "
            "template and cannot establish a Test 1 or SIA PASS."
        ),
    }
    template_dir.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("SIA 4010 TEST 1E EQUIVALENT DIAGNOSTIC MODEL: {}".format(DIAGNOSTIC_STATUS))
    print("Project: {}".format(project_path))
    print("Signature: {}".format(current_digest))
    print("Model proof: {}".format(output))
    print("Independent template review complete: NO")
    print("Compliance claim allowed: NO")
    print("NEXT: run Run_VE_SIA4010_Simulate_Qualified_Template.py; it will route as a diagnostic simulation.")
    return output


if __name__ == "__main__":
    run()
