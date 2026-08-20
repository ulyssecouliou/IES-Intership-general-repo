# -*- coding: utf-8 -*-
"""Fill the client SIA 380/2 compliance-criteria manifest against one model.

Takes the analysis a Run-button pass already produced -- the static SIA 380/2
results, the ApacheSim ``.aps`` dynamic results, the rooms and the reviewer
global comparison -- and writes a per-criterion verdict into the manifest:

    OK · PARTIAL · NOT_OK · NOT_CHECKABLE · NOT_AVAILABLE_IN_VE · NEEDS_REVIEWER_EVIDENCE

It reuses the existing, tested coverage engine
(``ExcelReportGenerator._build_sia_data_coverage_rows``), which already reads the
``.aps`` payload, so the JSON stays consistent with the Excel SIA DATA COVERAGE
sheet. The overall headline comes from ``build_compliance_verdict`` so it can
never disagree with the PDF/HTML reports. Missing evidence never becomes OK.

Pure Python, no ``iesve`` import.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from swiss_sia.compliance_criteria import build_manifest
from swiss_sia.compliance_verdict import build_compliance_verdict
from swiss_sia.excel_report import ExcelReportGenerator

# Coverage status (data availability) -> runtime status, by VE capability class.
_COVERAGE_TO_RUNTIME = {
    "AVAILABLE": "OK",
    "PARTIAL": "PARTIAL",
    "MISSING": "NOT_CHECKABLE",
    # A criterion that the norm does not apply to this model (e.g. SCOP with no
    # heat pump) is neither a pass nor a gap: it is out of scope, not silently OK.
    "NON_APPLICABLE": "NON_APPLICABLE",
}


def _coverage_rows(
    sia3802_results: Dict[str, Any],
    sia4010_results: Dict[str, Any],
    rooms_data: List[Any],
    preflight_checks: List[Dict[str, Any]],
    dynamic_results: Dict[str, Any],
) -> Dict[str, Any]:
    """Return {id: (coverage_status, evidence)} from the shared coverage engine."""
    generator = ExcelReportGenerator.__new__(ExcelReportGenerator)
    rows = generator._build_sia_data_coverage_rows(
        sia3802_results or {},
        sia4010_results or {},
        list(rooms_data or []),
        list(preflight_checks or []),
        dynamic_results or {},
    )
    return {
        str(row.get("id", "")): (
            str(row.get("coverage_status", "MISSING")).upper(),
            str(row.get("current_evidence", "")),
        )
        for row in rows
    }


def _runtime_status_for(criterion: Dict[str, Any], coverage: Any) -> Any:
    """Map one criterion's capability + coverage status to a runtime verdict."""
    capability = criterion.get("ve_capability", "VE_PARTIAL")
    if capability == "NOT_AVAILABLE":
        return (
            "NOT_AVAILABLE_IN_VE",
            criterion.get("ve_capability_note")
            or "VE cannot produce this quantity; not auto-decidable.",
        )

    coverage_status, evidence = coverage or ("MISSING", "No coverage evidence for this criterion.")

    if capability == "EXTERNAL_EVIDENCE":
        if coverage_status == "AVAILABLE":
            return "OK", evidence
        if coverage_status == "PARTIAL":
            return "PARTIAL", evidence
        return "NEEDS_REVIEWER_EVIDENCE", evidence

    # VE_AVAILABLE / VE_PARTIAL: data availability drives the status. A missing
    # or placeholder input is NOT_CHECKABLE, never a silent pass.
    return _COVERAGE_TO_RUNTIME.get(coverage_status, "NOT_CHECKABLE"), evidence


def _decisive_gate_status(sia3802_results: Dict[str, Any]) -> Any:
    """Return the runtime status of the decisive global comparison gate."""
    comparison = (sia3802_results or {}).get("global_reference_comparison", {}) or {}
    status = str(comparison.get("status") or "").upper()
    if status == "REVIEWED_RESULT_AVAILABLE":
        return "OK", "Reviewed project/reference comparison available; project <= reference."
    if status == "REVIEWED_RESULT_CONTRADICTS_ACCEPTANCE":
        return (
            "NOT_OK",
            "Reviewed comparison marked accepted, but the project value exceeds the reference "
            "(SIA 380/2:2022 7.2.5.2).",
        )
    return (
        "NEEDS_REVIEWER_EVIDENCE",
        "No reviewed global project/reference comparison provided; the decisive SIA 380/2 gate "
        "(7.2.5.2) cannot be established. See docs/project/GUIDE_COMPARAISON_GLOBALE_SIA3802.md.",
    )


def evaluate_client_compliance(
    sia3802_results: Optional[Dict[str, Any]],
    sia4010_results: Optional[Dict[str, Any]],
    dynamic_results: Optional[Dict[str, Any]],
    rooms_data: Optional[List[Any]],
    preflight_checks: Optional[List[Dict[str, Any]]] = None,
    *,
    scope: str = "both",
    generated_at: str = "",
    project_label: str = "",
    model_name: str = "",
) -> Dict[str, Any]:
    """Return the manifest with every criterion evaluated against this model.

    In the client ``"sia3802"`` scope the SIA 4010 criteria are dropped: they
    report the toolchain's validation-class evidence, not the client building.
    """
    sia3802 = dict(sia3802_results or {})
    sia4010 = dict(sia4010_results or {})
    rooms = list(rooms_data or [])
    # The ApacheSim .aps room results are SIA 380/2 evidence (summer comfort,
    # energy). The coverage stats read them from sia4010["dynamic_results"]; in
    # the client scope the SIA 4010 checks are skipped and sia4010 is empty, so
    # attach the explicitly-passed dynamic results here or the .aps criteria
    # would wrongly read as NOT_CHECKABLE.
    if dynamic_results and not sia4010.get("dynamic_results"):
        sia4010["dynamic_results"] = dynamic_results
    manifest = build_manifest()
    if str(scope or "").strip().lower() == "sia3802":
        manifest["criteria"] = [
            criterion for criterion in manifest["criteria"]
            if not str(criterion.get("standard") or "").startswith("SIA 4010")
        ]
        manifest["meta"]["scope"] = "sia3802"

    status_by_id = _coverage_rows(
        sia3802, sia4010, rooms, preflight_checks or [], dynamic_results or {}
    )

    for criterion in manifest["criteria"]:
        status, evidence = _runtime_status_for(
            criterion, status_by_id.get(criterion["id"])
        )
        criterion["runtime_status"] = status
        criterion["runtime_evidence"] = evidence

    gate_status, gate_evidence = _decisive_gate_status(sia3802)
    manifest["decisive_gate"]["runtime_status"] = gate_status
    manifest["decisive_gate"]["runtime_evidence"] = gate_evidence

    reference_project = sia3802.get("reference_project", {}) or {}
    reference_blockers = list(reference_project.get("blockers", []) or [])

    verdict = build_compliance_verdict(sia3802, sia4010, len(rooms))
    tally: Dict[str, int] = {}
    for criterion in manifest["criteria"]:
        tally[criterion["runtime_status"]] = tally.get(criterion["runtime_status"], 0) + 1

    manifest["evaluation"] = {
        "project_label": project_label,
        "model_name": model_name,
        "generated_at": generated_at,
        "rooms_analysed": len(rooms),
        "overall_sia3802_status": verdict.sia3802_status,
        "overall_sia3802_reason": verdict.sia3802_reason,
        "decisive_gate_status": gate_status,
        "outstanding": list(verdict.outstanding),
        "reference_project_status": str(reference_project.get("status") or ""),
        "reference_project_blockers": reference_blockers,
        "criteria_status_tally": tally,
        "note": (
            "Component criteria are diagnostics; overall SIA 380/2 compliance is the "
            "decisive gate plus no NOT_CHECKABLE/NOT_OK domain. See verdict_logic."
        ),
    }
    return manifest
