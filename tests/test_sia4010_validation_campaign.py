"""Tests for the optimized all-class SIA 4010 campaign queue."""

import hashlib
import json
from pathlib import Path

from swiss_sia.reference_model.sia4010.evidence_registry import (
    new_registry_payload,
)
from swiss_sia.reference_model.sia4010.validation_campaign import (
    CAMPAIGN_PHASES,
    build_validation_campaign,
    write_validation_campaign,
)


def _evidence(path: Path, *, status: str = "PASS"):
    path.write_text("evidence", encoding="utf-8")
    return {
        "status": status,
        "artifact_path": str(path),
        "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _complete_case(registry, tmp_path: Path, key: str):
    safe = key.replace("/", "_")
    record = registry["cases"][key]
    project = tmp_path / safe
    project.mkdir()
    model = project / "model.json"
    scenario = project / "scenario.json"
    aps = project / "result.aps"
    simulation_audit = project / "simulation.json"
    result_audit = project / "evaluation.json"
    for path in (model, scenario, aps, simulation_audit, result_audit):
        path.write_text(path.name, encoding="utf-8")

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    record["model_evidence"] = {
        "status": "VERIFIED",
        "artifact_path": str(model),
        "artifact_sha256": sha(model),
        "project_path": str(project),
    }
    record["simulation_evidence"] = {
        "status": "SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION",
        "artifact_path": str(simulation_audit),
        "artifact_sha256": sha(simulation_audit),
        "project_path": str(project),
        "scenario_path": str(scenario),
        "scenario_sha256": sha(scenario),
        "model_report_path": str(model),
        "model_report_sha256": sha(model),
        "results_path": str(aps),
        "results_sha256": sha(aps),
        "results_size_bytes": aps.stat().st_size,
        "model_evidence_link_status": "VERIFIED",
        "aps_evaluation_required": True,
        "compliance_claim_allowed": False,
    }
    record["result_evidence"] = {
        "status": "OFFICIAL_RESULTS_RECORDED",
        "artifact_path": str(result_audit),
        "artifact_sha256": sha(result_audit),
        "project_path": str(project),
        "aps_path": str(aps),
        "aps_sha256": sha(aps),
        "simulation_link_status": "VERIFIED",
    }


def test_phase_order_unlocks_quick_classes_first():
    assert [phase.phase_id for phase in CAMPAIGN_PHASES] == [
        "P0",
        "P1",
        "P2",
        "P3",
        "P4",
        "P5",
        "P6",
    ]
    assert CAMPAIGN_PHASES[1].unlocks == ("1A",)
    assert CAMPAIGN_PHASES[-1].unlocks == ("5", "4A", "4B")


def test_empty_ledger_starts_with_case_600_reconciliation():
    payload = build_validation_campaign(new_registry_payload())
    assert payload["summary"]["complete_exact_cases"] == 0
    assert payload["next_action"]["case_key"] == "test_1/600"
    assert payload["next_action"]["action_code"] == "RECONCILE_TEST1_600"


def test_completed_test1_moves_queue_to_test2a(tmp_path):
    registry = new_registry_payload()
    for key in tuple(registry["cases"]):
        if key.startswith("test_1/"):
            _complete_case(registry, tmp_path, key)
    payload = build_validation_campaign(registry)
    assert payload["phases"][0]["status"] == "COMPLETE"
    assert payload["next_action"]["case_key"] == "test_2A/2A"
    assert payload["next_action"]["launcher"].endswith(
        "Test2A_Qualification_One_Click.py"
    )


def test_class_is_complete_only_with_all_linked_case_evidence(tmp_path):
    registry = new_registry_payload()
    for key in tuple(registry["cases"]):
        if key.startswith("test_1/") or key == "test_2A/2A":
            _complete_case(registry, tmp_path, key)
    payload = build_validation_campaign(registry)
    assert payload["classes"]["1A"]["status"].startswith("TECHNICALLY_COMPLETE")
    assert payload["classes"]["1A"]["official_attestation_required"] is True
    assert payload["classes"]["1B"]["status"] == "INCOMPLETE"


def test_changed_artifact_reopens_case(tmp_path):
    registry = new_registry_payload()
    _complete_case(registry, tmp_path, "test_1/600")
    Path(registry["cases"]["test_1/600"]["result_evidence"]["artifact_path"]).write_text(
        "changed", encoding="utf-8"
    )
    payload = build_validation_campaign(registry)
    case = payload["cases"]["test_1/600"]
    assert case["result_valid"] is False
    assert case["complete"] is False


def test_writer_creates_json_and_html(tmp_path):
    repository = tmp_path / "repo"
    registry_path = repository / "ledger.json"
    registry_path.parent.mkdir()
    registry_path.write_text(json.dumps(new_registry_payload()), encoding="utf-8")
    output = repository / "campaign"
    payload = write_validation_campaign(
        repository,
        registry_path=registry_path,
        output_directory=output,
    )
    assert Path(payload["artifacts"]["json"]).is_file()
    html_text = Path(payload["artifacts"]["html"]).read_text(encoding="utf-8")
    assert "accelerated campaign" in html_text
    assert "NEXT ACTION" in html_text
