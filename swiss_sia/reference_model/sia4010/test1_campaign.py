"""Deterministic campaign status for the six ISO 52016 Test 1 cases."""

from typing import Any, Dict, Mapping, Tuple


TEST1_CAMPAIGN_CASES: Tuple[str, ...] = (
    "600",
    "640",
    "600FF",
    "900",
    "940",
    "900FF",
)


def _case_stage(record: Mapping[str, Any]) -> str:
    """Return the next fail-closed execution stage for one ledger record."""

    model = record.get("model_evidence") or {}
    simulation = record.get("simulation_evidence") or {}
    result = record.get("result_evidence") or {}
    if (
        result.get("required_output_scope_complete") is True
        and result.get("simulation_link_status") == "VERIFIED"
        and int(result.get("observed_metric_count") or 0) > 0
    ):
        return "REFERENCE_RESULTS_COMPLETE"
    if simulation.get("status") == "SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION":
        return "EVALUATE_APS"
    if model.get("status") == "VERIFIED":
        return "QUALIFY_RUNTIME_AND_SIMULATE"
    if record.get("case_id") == "600":
        return "CREATE_GUARDED_MODEL"
    return "QUALIFY_GENERATOR_IN_FRESH_PROJECT"


def build_test1_campaign_status(
    registry: Mapping[str, Any],
) -> Dict[str, Any]:
    """Summarize Test 1 evidence without promoting reference-only results."""

    cases = registry.get("cases") or {}
    rows = []
    for case_id in TEST1_CAMPAIGN_CASES:
        key = "test_1/{}".format(case_id)
        record = cases.get(key) or {"case_id": case_id}
        stage = _case_stage(record)
        rows.append(
            {
                "variant": "test_1",
                "case_id": case_id,
                "recommended_project_name": "SIA4010_TEST1_{}".format(case_id),
                "stage": stage,
                "reference_results_complete": (
                    stage == "REFERENCE_RESULTS_COMPLETE"
                ),
                "formal_compliance_verdict": "NOT_AVAILABLE_WITHOUT_ACCEPTANCE_CRITERION",
            }
        )
    pending = [
        row for row in rows if not row["reference_results_complete"]
    ]
    return {
        "schema_version": "1.0",
        "status": (
            "TEST1_REFERENCE_CAMPAIGN_COMPLETE"
            if not pending
            else "TEST1_REFERENCE_CAMPAIGN_IN_PROGRESS"
        ),
        "case_count": len(rows),
        "reference_results_complete_count": len(rows) - len(pending),
        "next_case": pending[0] if pending else None,
        "cases": rows,
        "claim_guardrail": (
            "Complete reference-result evidence is not an SIA compliance "
            "verdict when the official source supplies no acceptance criterion."
        ),
    }
