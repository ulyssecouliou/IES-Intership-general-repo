"""Deterministic campaign status for every SIA 4010 Test 1 case.

The six ISO 52016 cases and diagnostic links 1A to 1D are reference/output
deliverables without a formal acceptance criterion.  Case 1E is separate: it
is the sole judged case and must pass through the qualified-template route.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple

TEST1_ISO_CASES: Tuple[str, ...] = (
    "600",
    "640",
    "600FF",
    "900",
    "940",
    "900FF",
)

TEST1_DIAGNOSTIC_CASES: Tuple[str, ...] = (
    "1A",
    "1B",
    "1C",
    "1D",
)

TEST1_JUDGED_CASES: Tuple[str, ...] = ("1E",)

TEST1_CAMPAIGN_CASES: Tuple[str, ...] = (
    TEST1_ISO_CASES + TEST1_DIAGNOSTIC_CASES + TEST1_JUDGED_CASES
)


def _sha256(path: Path) -> str:
    """Return the lowercase digest of one evidence artifact."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _artifact_matches(evidence: Mapping[str, Any], prefix: str) -> bool:
    """Check one ``*_path``/``*_sha256`` pair without modifying evidence."""

    path = Path(str(evidence.get(prefix + "_path", "") or ""))
    expected = str(evidence.get(prefix + "_sha256", "") or "").lower()
    return bool(expected) and path.is_file() and _sha256(path) == expected


def _simulation_is_current(simulation: Mapping[str, Any]) -> bool:
    """Require every simulation input/output checksum to remain current."""

    return (
        simulation.get("status") == "SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION"
        and simulation.get("model_evidence_link_status") == "VERIFIED"
        and _artifact_matches(simulation, "artifact")
        and _artifact_matches(simulation, "results")
        and _artifact_matches(simulation, "model_report")
        and _artifact_matches(simulation, "scenario")
    )


def _requires_floor_insulation_reconciliation(simulation: Mapping[str, Any]) -> bool:
    """Detect the exact superseded zero-mass floor-material failure."""

    path = Path(str(simulation.get("model_report_path", "") or ""))
    if not path.is_file():
        return False
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    for result in report.get("validation_results", []):
        message = str(result.get("message", ""))
        if (
            str(result.get("status", "")).upper() == "FAIL"
            and "xps_ground" in message
            and "density" in message
            and "specific_heat_capacity" in message
        ):
            return True
    return False


def _case_stage(record: Mapping[str, Any]) -> str:
    """Return the next fail-closed execution stage for one ledger record."""

    model = record.get("model_evidence") or {}
    simulation = record.get("simulation_evidence") or {}
    result = record.get("result_evidence") or {}
    simulation_current = _simulation_is_current(simulation)
    if (
        result.get("required_output_scope_complete") is True
        and result.get("simulation_link_status") == "VERIFIED"
        and int(result.get("observed_metric_count") or 0) > 0
        and simulation_current
    ):
        return (
            "JUDGED_RESULTS_COMPLETE"
            if str(record.get("case_id", "")).upper() == "1E"
            else "REFERENCE_RESULTS_COMPLETE"
        )
    if simulation_current:
        return "EVALUATE_APS"
    if simulation.get("status") == "SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION":
        if _requires_floor_insulation_reconciliation(simulation):
            return "RECONCILE_FLOOR_INSULATION"
        return "REQUALIFY_SIMULATION_EVIDENCE"
    if model.get("status") == "VERIFIED":
        if str(record.get("case_id", "")).upper() == "1E":
            return "QUALIFY_TEMPLATE_AND_SIMULATE"
        return "QUALIFY_RUNTIME_AND_SIMULATE"
    if str(record.get("case_id", "")).upper() == "1E":
        return "QUALIFY_EXACT_1E_TEMPLATE"
    if record.get("case_id") == "600":
        return "CREATE_GUARDED_MODEL"
    return "QUALIFY_GENERATOR_IN_FRESH_PROJECT"


def _next_action(stage: str, record: Mapping[str, Any]) -> Dict[str, Any]:
    """Return exact operator instructions for the next guarded VEScript."""

    model = record.get("model_evidence") or {}
    simulation = record.get("simulation_evidence") or {}
    result = record.get("result_evidence") or {}
    existing_project = str(
        simulation.get("project_path")
        or result.get("project_path")
        or model.get("project_path")
        or ""
    )
    if stage == "EVALUATE_APS":
        return {
            "script": "Run_VE_SIA4010_Evaluate_Active_Case.py",
            "requires_fresh_project": False,
            "project_path": existing_project,
            "instruction": (
                "Open the existing project_path in VE, then run the script to "
                "checksum-link the newest qualified APS result. Do not create a "
                "new blank project for this stage."
            ),
        }
    if stage == "QUALIFY_RUNTIME_AND_SIMULATE":
        return {
            "script": "Run_VE_SIA4010_Test1_Active_Case_One_Click.py",
            "requires_fresh_project": False,
            "project_path": existing_project,
            "instruction": (
                "Open the existing verified case project and run the guarded "
                "runtime qualification, simulation and APS evaluation."
            ),
        }
    if stage == "QUALIFY_TEMPLATE_AND_SIMULATE":
        return {
            "script": "scripts/probes/Run_VE_SIA4010_Verify_Template_Model.py",
            "requires_fresh_project": False,
            "project_path": existing_project,
            "follow_up_script": "scripts/probes/Run_VE_SIA4010_Simulate_Qualified_Template.py",
            "instruction": (
                "Open the disposable exact-case 1E template copy, verify its "
                "checksum-bound model evidence, then run the qualified-template "
                "ApacheSim and APS comparison."
            ),
        }
    if stage == "QUALIFY_EXACT_1E_TEMPLATE":
        return {
            "script": "scripts/probes/Run_VE_SIA4010_Test1E_Prepare_Template.py",
            "requires_fresh_project": True,
            "project_path": "",
            "instruction": (
                "Open the completed exact case 1D project and use Save As to "
                "create a separate copy named SIA4010_TEST1_1E_TEMPLATE. Run "
                "the preparer in that copy. Then add and independently review "
                "only the prescribed 1E fabric awning before capture/binding."
            ),
        }
    if stage == "REQUALIFY_SIMULATION_EVIDENCE":
        return {
            "script": "Run_VE_SIA4010_Simulate_Active_Case.py",
            "requires_fresh_project": False,
            "project_path": existing_project,
            "instruction": (
                "Open the existing case project and rerun the guarded "
                "simulation because one or more registered model/scenario "
                "checksums changed after the previous APS was produced. The "
                "script will create current simulation evidence and evaluate "
                "the resulting APS."
            ),
        }
    if stage == "RECONCILE_FLOOR_INSULATION":
        return {
            "script": "Run_VE_SIA4010_Test1_Reconcile_Floor_Insulation.py",
            "requires_fresh_project": False,
            "project_path": existing_project,
            "follow_up_script": "Run_VE_SIA4010_Test1_Active_Case_One_Click.py",
            "instruction": (
                "Open the backed-up existing case project and run the narrow "
                "zero-mass floor-insulation reconciliation. Save after PASS, "
                "then run the follow_up_script to regenerate current model, "
                "simulation and APS evidence."
            ),
        }
    if stage in ("CREATE_GUARDED_MODEL", "QUALIFY_GENERATOR_IN_FRESH_PROJECT"):
        return {
            "script": "Run_VE_SIA4010_Test1_Fast_Start.py",
            "requires_fresh_project": True,
            "project_path": "",
            "instruction": (
                "Create and save a fresh blank disposable VE project using the "
                "recommended_project_name, then run Fast Start."
            ),
        }
    return {
        "script": "",
        "requires_fresh_project": False,
        "project_path": existing_project,
        "instruction": "No execution is required; preserve the checksummed evidence.",
    }


def build_test1_campaign_status(
    registry: Mapping[str, Any],
) -> Dict[str, Any]:
    """Summarize reference deliverables and the separately judged 1E case."""

    cases = registry.get("cases") or {}
    rows = []
    for case_id in TEST1_CAMPAIGN_CASES:
        key = "test_1/{}".format(case_id)
        record = cases.get(key) or {"case_id": case_id}
        stage = _case_stage(record)
        judged = case_id in TEST1_JUDGED_CASES
        row = {
            "variant": "test_1",
            "case_id": case_id,
            "recommended_project_name": (
                "SIA4010_TEST1_1E_TEMPLATE"
                if judged
                else "SIA4010_TEST1_{}".format(case_id)
            ),
            "stage": stage,
            "reference_results_complete": (
                not judged and stage == "REFERENCE_RESULTS_COMPLETE"
            ),
            "judged_results_complete": (judged and stage == "JUDGED_RESULTS_COMPLETE"),
            "formal_compliance_verdict": (
                str((record.get("result_evidence") or {}).get("status") or "")
                if stage == "JUDGED_RESULTS_COMPLETE"
                else (
                    "PENDING_QUALIFIED_1E_RESULT"
                    if judged
                    else "NOT_AVAILABLE_WITHOUT_ACCEPTANCE_CRITERION"
                )
            ),
        }
        row["next_action"] = _next_action(stage, record)
        rows.append(row)
    reference_rows = [row for row in rows if row["case_id"] not in TEST1_JUDGED_CASES]
    pending = [row for row in reference_rows if not row["reference_results_complete"]]
    iso_rows = [row for row in rows if row["case_id"] in TEST1_ISO_CASES]
    diagnostic_rows = [row for row in rows if row["case_id"] in TEST1_DIAGNOSTIC_CASES]
    pending_iso = [row for row in iso_rows if not row["reference_results_complete"]]
    pending_diagnostics = [
        row for row in diagnostic_rows if not row["reference_results_complete"]
    ]
    judged_row = next(row for row in rows if row["case_id"] == "1E")
    judged_complete = judged_row["judged_results_complete"]
    formal_status = (
        "TEST1_JUDGED_RESULT_RECORDED"
        if judged_complete
        else "BLOCKED_DIAGNOSTIC_1E_VE_QUALIFICATION_REQUIRED"
    )
    return {
        "schema_version": "1.0",
        "status": (
            "TEST1_REFERENCE_CAMPAIGN_COMPLETE"
            if not pending
            else "TEST1_REFERENCE_CAMPAIGN_IN_PROGRESS"
        ),
        "case_count": len(rows),
        "reference_case_count": len(reference_rows),
        "reference_results_complete_count": len(reference_rows) - len(pending),
        "next_case": pending[0] if pending else (None if judged_complete else judged_row),
        "iso_status": (
            "TEST1_ISO_REFERENCE_CAMPAIGN_COMPLETE"
            if not pending_iso
            else "TEST1_ISO_REFERENCE_CAMPAIGN_IN_PROGRESS"
        ),
        "iso_case_count": len(iso_rows),
        "iso_reference_results_complete_count": len(iso_rows) - len(pending_iso),
        "next_iso_case": pending_iso[0] if pending_iso else None,
        "diagnostic_status": (
            "TEST1_DIAGNOSTIC_DELIVERABLES_COMPLETE"
            if not pending_diagnostics
            else "TEST1_DIAGNOSTIC_DELIVERABLES_IN_PROGRESS"
        ),
        "diagnostic_case_count": len(diagnostic_rows),
        "diagnostic_deliverables_complete_count": (
            len(diagnostic_rows) - len(pending_diagnostics)
        ),
        "next_diagnostic_case": (pending_diagnostics[0] if pending_diagnostics else None),
        "judged_case_count": 1,
        "judged_results_complete_count": int(judged_complete),
        "judged_case": judged_row,
        "formal_test1_status": formal_status,
        "formal_test1_blocker": (
            ""
            if judged_complete
            else (
                "Diagnostic case 1E is the only Test 1 case with a pass/fail "
                "criterion. Its fabric-awning control semantics and IESVE "
                "threshold mapping were confirmed by Prof. Gerhard Zweifel "
                "on 2026-08-26. The optical mapping, VE assignment/read-back, "
                "APS binding and scored simulation still require qualification. "
                "VE 2025 runtime testing also proved that CDB set_properties "
                "changes are not serialized by project save; the external "
                "shade must therefore be persisted through the APcdb interface "
                "or an IES-supported persistence route."
            )
        ),
        "cases": rows,
        "claim_guardrail": (
            "Complete reference-result evidence is not an SIA compliance "
            "verdict when the official source supplies no acceptance criterion."
        ),
    }
