"""Pure workflow registry and local status model for the compliance cockpit."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple


@dataclass(frozen=True)
class HubAction:
    """One existing VEScripts workflow exposed by the client cockpit."""

    action_id: str
    section: str
    title: str
    description: str
    launcher: str
    badge: str
    button_label: str = "Run"
    mutates_ve: bool = False
    requires_disposable_project: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe action record."""
        return asdict(self)


@dataclass(frozen=True)
class ProjectSnapshot:
    """Fail-safe summary of evidence already present beside the active model."""

    project_name: str
    project_kind: str
    model_files: int
    aps_files: int
    client_audit_status: str
    template_remediation_status: str
    model_audit_status: str
    scenario: str
    result_status: str
    result_scope_complete: Optional[bool]
    recommended_action: str

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe snapshot for reports and UI tests."""
        return asdict(self)


ACTIONS: Tuple[HubAction, ...] = (
    HubAction(
        "client_audit",
        "Client model workflow",
        "1. Inspect active client model",
        "Run the read-only SIA 380/2 remediation audit across model and APS data. "
        "No VE object is changed.",
        "Run_VE_Swiss_Compliance_Remediation_Probe.py",
        "READ-ONLY",
        "Run audit",
    ),
    HubAction(
        "client_sia2024_classroom_template",
        "Client model workflow",
        "2. Create SIA 2024 classroom reference template",
        "Create or strictly verify the source-traced SIA 2024 usage 4.01 "
        "profiles, gains, air exchanges and thermal template. Review-required "
        "VE mappings remain explicit; no room is changed.",
        "Run_VE_SIA3802_Create_Classroom_Reference_Template.py",
        "SIA-SOURCED / REVIEW",
        "Create / verify",
        mutates_ve=True,
        requires_disposable_project=True,
    ),
    HubAction(
        "client_template_remediation",
        "Client model workflow",
        "3. Apply reviewed room templates",
        "Preview and assign an existing, independently reviewed VE thermal "
        "template to explicit rooms in a saved client-model copy. Every write "
        "is checksum-bound and read back; no regulatory value is invented.",
        "Run_VE_SIA3802_Approved_Template_Remediation.py",
        "CONTROLLED MUTATION",
        "Preview / apply",
        mutates_ve=True,
        requires_disposable_project=True,
    ),
    HubAction(
        "evidence",
        "Client model workflow",
        "4. Complete project evidence",
        "Capture reviewed source, weather and project metadata. Missing evidence "
        "remains visible and blocks overclaiming.",
        "Run_VE_Swiss_Compliance_Evidence_Wizard.py",
        "FAIL-CLOSED",
        "Open wizard",
    ),
    HubAction(
        "report",
        "Client model workflow",
        "5. Generate auditable report",
        "Export the current SIA 380/2 software pre-check, assumptions, findings and "
        "traceable evidence package.",
        "Run_VE_Swiss_Compliance.py",
        "REPORT",
        "Generate report",
    ),
    HubAction(
        "navigator",
        "SIA 4010 verification laboratory",
        "Evidence dashboard - all validation classes",
        "Rebuild the checksum-controlled navigator for 8 validation classes and "
        "34 exact cases without changing VE.",
        "Run_VE_SIA4010_Navigator.py",
        "34 CASES / READ-ONLY",
        "Open dashboard",
    ),
    HubAction(
        "sia4010_prepare_all",
        "SIA 4010 verification laboratory",
        "Prepare all official case contracts",
        "Verify the official source bundle and prepare source-traced contracts, "
        "blockers and execution queues for every class.",
        "Run_VE_SIA4010_Prepare_All_Classes.py",
        "SOURCE-TRACED",
        "Prepare contracts",
    ),
    HubAction(
        "sia4010_lab",
        "SIA 4010 verification laboratory",
        "Open SIA 4010 Model Builder",
        "Select an official case, inspect locked features and run only the guarded "
        "qualification routes available for the active disposable project.",
        "Run_VE_SIA_Model_Builder_UI.py",
        "1 VERIFIED + 9 QUALIFYING",
        "Open laboratory",
        mutates_ve=True,
        requires_disposable_project=True,
    ),
    HubAction(
        "sia4010_evaluate",
        "SIA 4010 verification laboratory",
        "Evaluate latest linked APS",
        "Extract the qualified hourly variables and compare them with the official "
        "case outputs. A verdict is issued only when an official criterion exists.",
        "Run_VE_SIA4010_Evaluate_Active_Case.py",
        "READ-ONLY APS",
        "Evaluate APS",
    ),
    HubAction(
        "sia4010_simulate",
        "SIA 4010 verification laboratory",
        "Run guarded ApacheSim + APS evaluation",
        "Simulate a prepared exact Test 1 case and register the model-to-APS evidence "
        "chain. Use only a saved disposable project.",
        "Run_VE_SIA4010_Simulate_Active_Case.py",
        "CONTROLLED RUN",
        "Simulate + evaluate",
        mutates_ve=True,
        requires_disposable_project=True,
    ),
    HubAction(
        "sia4010_hybrid_readiness",
        "Advanced / controlled model creation",
        "Check direct-generator and template routes",
        "Identify cases supported through VEScripts and cases requiring a reviewed "
        "VE template, with checksum verification.",
        "Run_VE_SIA4010_Hybrid_Readiness.py",
        "READ-ONLY",
        "Check readiness",
    ),
    HubAction(
        "reference_model",
        "Advanced / controlled model creation",
        "Create parametric Swiss reference model",
        "Prepare project-local configuration and generate the current reference "
        "model implementation. This is a compliance-ready baseline, not an SIA "
        "certification.",
        "Run_VE_Swiss_Reference_Model_Setup.py",
        "PARTIAL / MUTATION",
        "Start setup",
        mutates_ve=True,
        requires_disposable_project=True,
    ),
    HubAction(
        "sia4010_test1_fast_start",
        "Advanced / controlled model creation",
        "Continue a Test 1 runtime qualification",
        "Prepare, create or resume one exact Test 1 case, then simulate and evaluate. "
        "Use only for development after reviewing the current blockers.",
        "Run_VE_SIA4010_Test1_Fast_Start.py",
        "DEVELOPMENT",
        "Continue qualification",
        mutates_ve=True,
        requires_disposable_project=True,
    ),
    HubAction(
        "sia4010_template_capture",
        "Advanced / controlled model creation",
        "Capture candidate VE template fingerprint",
        "Record the active project fingerprint for independent review. Capture does "
        "not qualify or approve a template.",
        "Run_VE_SIA4010_Capture_Active_Template.py",
        "CAPTURE ONLY",
        "Capture fingerprint",
    ),
    HubAction(
        "sia4010_template_copy",
        "Advanced / controlled model creation",
        "Create disposable project from reviewed template",
        "Copy a checksum-approved template into a new project folder without "
        "overwriting an existing project.",
        "Run_VE_SIA4010_Create_Disposable_From_Template.py",
        "QUALIFIED TEMPLATE",
        "Create copy",
    ),
)


def action_map() -> Dict[str, HubAction]:
    """Return the workflow registry indexed by stable action ID."""
    return {action.action_id: action for action in ACTIONS}


def is_disposable_project(project_path: str) -> bool:
    """Return whether the saved project name explicitly marks a disposable copy."""
    normalized = str(project_path or "").rstrip("/\\").replace("/", "\\")
    name = normalized.split("\\")[-1].upper() if normalized else ""
    explicit_suffix = name.endswith(("_TEST", "_COPY", "_DISPOSABLE"))
    validation_case = name.startswith("SIA4010_TEST") or (
        name.startswith("TEST_") and "_TEST" in name
    )
    return explicit_suffix or "DISPOSABLE" in name or validation_case


def build_capability_summary(capabilities: Iterable[Any]) -> Dict[str, int]:
    """Summarize exact SIA 4010 generation capability without overclaiming."""
    rows = list(capabilities)
    guarded = sum(bool(getattr(row, "mutation_supported", False)) for row in rows)
    runtime = sum(
        bool(getattr(row, "runtime_qualification_supported", False)) for row in rows
    )
    return {
        "exact_cases": len(rows),
        "guarded_mutation_cases": guarded,
        "runtime_qualification_cases": runtime,
        "not_implemented_cases": max(0, len(rows) - guarded - runtime),
    }


def _latest_file(root: Path, pattern: str) -> Optional[Path]:
    """Return the most recently modified matching file, if any."""
    try:
        matches = [path for path in root.glob(pattern) if path.is_file()]
    except OSError:
        return None
    return max(matches, key=lambda path: path.stat().st_mtime) if matches else None


def _read_json(path: Optional[Path]) -> Dict[str, Any]:
    """Read a JSON object without allowing stale or corrupt UI data to crash VE."""
    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def build_project_snapshot(project_path: str) -> ProjectSnapshot:
    """Inspect only project-local artifacts and return a truthful demo snapshot."""
    root = Path(str(project_path or "")).resolve()
    project_name = root.name or "Unsaved project"
    disposable = is_disposable_project(str(root))
    project_kind = "Disposable validation project" if disposable else "Client project"

    try:
        model_files = len(
            [
                path
                for path in root.glob("*.mdl")
                if "tmpsave" not in path.stem.lower()
            ]
        )
        aps_files = len(list((root / "Vista").glob("*.aps")))
    except OSError:
        model_files = 0
        aps_files = 0

    audit_path = _latest_file(
        root,
        "sia_compliance_artifacts/diagnostics/"
        "swiss_sia_remediation_probe_*.json",
    )
    audit = _read_json(audit_path)
    client_audit_status = str(audit.get("status") or "NOT RUN").upper()

    remediation_path = _latest_file(
        root,
        "sia_compliance_artifacts/template_remediation/"
        "sia3802_template_receipt_*.json",
    )
    remediation = _read_json(remediation_path)
    template_remediation_status = str(
        remediation.get("status") or "NOT RUN"
    ).upper()

    model_audit = _read_json(
        root / "reference_model_artifacts" / "reports" / "reference_model_report.json"
    )
    model_audit_status = str(
        model_audit.get("overall_status") or model_audit.get("status") or "NOT RUN"
    ).upper()

    scenario_payload = _read_json(root / "sia_model_scenario.json")
    selection = scenario_payload.get("selection") or {}
    if not isinstance(selection, dict):
        selection = {}
    variant = str(selection.get("variant") or "").strip()
    case_id = str(selection.get("case_id") or "").strip()
    scenario = "{}/{}".format(variant, case_id) if variant and case_id else "NOT SELECTED"

    result = _read_json(
        _latest_file(root, "sia4010_artifacts/results/*_evaluation.json")
    )
    result_status = str(result.get("status") or "NOT RUN").upper()
    scope_value = result.get("required_output_scope_complete")
    result_scope_complete = scope_value if isinstance(scope_value, bool) else None

    audit_is_older_than_remediation = bool(
        audit_path
        and remediation_path
        and audit_path.stat().st_mtime < remediation_path.stat().st_mtime
    )
    if template_remediation_status == "APPLIED_AND_READBACK_VERIFIED" and (
        audit_path is None or audit_is_older_than_remediation
    ):
        recommended_action = (
            "Rerun the post-remediation client audit before saving the VE copy."
        )
    elif template_remediation_status == "FAIL":
        recommended_action = "Close without saving and reopen the disposable copy."
    elif client_audit_status in {"WARNING", "FAIL"}:
        recommended_action = "Review findings, complete evidence, then generate the report."
    elif client_audit_status == "NOT RUN" and not disposable:
        recommended_action = "Run the read-only client model audit."
    elif scenario != "NOT SELECTED" and aps_files and result_status == "NOT RUN":
        recommended_action = "Evaluate the latest linked APS result."
    elif disposable and scenario == "NOT SELECTED":
        recommended_action = "Open the SIA 4010 laboratory and prepare one exact case."
    elif disposable and not aps_files:
        recommended_action = "Review the case audit before running guarded ApacheSim."
    elif result_status != "NOT RUN":
        recommended_action = "Open the evidence dashboard and review remaining gates."
    else:
        recommended_action = "Generate the auditable client report."

    return ProjectSnapshot(
        project_name=project_name,
        project_kind=project_kind,
        model_files=model_files,
        aps_files=aps_files,
        client_audit_status=client_audit_status,
        template_remediation_status=template_remediation_status,
        model_audit_status=model_audit_status,
        scenario=scenario,
        result_status=result_status,
        result_scope_complete=result_scope_complete,
        recommended_action=recommended_action,
    )
