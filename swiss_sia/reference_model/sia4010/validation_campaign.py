"""Accelerated, evidence-driven campaign plan for all SIA 4010 classes.

The validation classes share many exact cases.  Running them in numerical
class order wastes operator time and obscures the common Test 1 dependency.
This module turns the checksum ledger into one deterministic execution queue:

* finish the common Test 1 campaign once;
* close the A and B solar-protection branches;
* close the corresponding lighting branches;
* close HVAC/ventilation;
* finish generation, which also closes class 5 by itself.

The planner never turns preparation or a successful simulation into a PASS.
An exact case is complete only when its model, ApacheSim run and linked APS
evaluation artifacts are still present and checksum-valid.
"""

from __future__ import annotations

import hashlib
import html
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple, Union

from ...config import SIA4010_CLASS_TEST_MATRIX
from ..exceptions import ConfigurationError
from .case_registry import get_case_capability
from .evidence_registry import load_registry
from .model_scenario import TEST_CASES

SCHEMA_VERSION = "1.0"
REGISTRY_RELATIVE_PATH = Path("sia4010_evidence/autonomy/sia4010_case_evidence.json")
OUTPUT_RELATIVE_DIRECTORY = Path("sia4010_evidence/autonomy/campaign")


@dataclass(frozen=True)
class CampaignPhase:
    """One ordered milestone that unlocks one or more validation classes."""

    phase_id: str
    label: str
    variants: Tuple[str, ...]
    unlocks: Tuple[str, ...]
    rationale: str


CAMPAIGN_PHASES: Tuple[CampaignPhase, ...] = (
    CampaignPhase(
        "P0",
        "Common thermal-model foundation",
        ("test_1",),
        (),
        "Test 1 is shared by every class except class 5; run it once first.",
    ),
    CampaignPhase(
        "P1",
        "Fast A solar branch",
        ("test_2A",),
        ("1A",),
        "The single fabric-awning case is the shortest first class unlock.",
    ),
    CampaignPhase(
        "P2",
        "B solar branch",
        ("test_2B", "test_2C", "test_2D"),
        ("1B",),
        "The three slat-control cases reuse one controlled template family.",
    ),
    CampaignPhase(
        "P3",
        "A lighting branch",
        tuple("test_3{}".format(letter) for letter in "ABCDEF"),
        ("2A",),
        "Six lighting variants build directly on the completed A branch.",
    ),
    CampaignPhase(
        "P4",
        "B lighting extension",
        tuple("test_3{}".format(letter) for letter in "GHIJKL"),
        ("2B",),
        "The remaining lighting variants complete the wider B scope.",
    ),
    CampaignPhase(
        "P5",
        "HVAC and ventilation branch",
        ("test_4", "test_5A", "test_5B", "test_5C", "test_5D", "test_6"),
        ("3",),
        "One reviewed example-building template family can serve these cases.",
    ),
    CampaignPhase(
        "P6",
        "Generation and final integration",
        ("test_7",),
        ("5", "4A", "4B"),
        "Test 7 closes class 5 alone and completes classes 4A/4B after prior phases.",
    ),
)


@dataclass(frozen=True)
class ExactCaseProgress:
    """Strict current state and next operator action for one exact case."""

    variant: str
    case_id: str
    base_test_id: str
    model_valid: bool
    simulation_valid: bool
    result_valid: bool
    complete: bool
    next_action_code: str
    launcher: str
    instruction: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _artifact_valid(record: Mapping[str, Any]) -> bool:
    path_text = str(record.get("artifact_path", "") or "")
    expected = str(record.get("artifact_sha256", "") or "").lower()
    if not path_text or not expected:
        return False
    path = Path(path_text)
    if not path.is_file() or _sha256(path) != expected:
        return False
    qualification_text = str(record.get("qualification_artifact_path", "") or "")
    qualification_sha = str(record.get("qualification_artifact_sha256", "") or "").lower()
    if qualification_text or qualification_sha:
        qualification = Path(qualification_text)
        return (
            bool(qualification_text)
            and bool(qualification_sha)
            and qualification.is_file()
            and _sha256(qualification) == qualification_sha
        )
    return True


def _file_pair_valid(record: Mapping[str, Any], prefix: str) -> bool:
    path_text = str(record.get("{}_path".format(prefix), "") or "")
    expected = str(record.get("{}_sha256".format(prefix), "") or "").lower()
    path = Path(path_text)
    return bool(path_text and expected and path.is_file() and _sha256(path) == expected)


def _simulation_valid(record: Mapping[str, Any]) -> bool:
    if (
        str(record.get("status", "")) != "SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION"
        or record.get("model_evidence_link_status") != "VERIFIED"
        or record.get("aps_evaluation_required") is not True
        or record.get("compliance_claim_allowed") is not False
        or not _artifact_valid(record)
    ):
        return False
    if not all(
        _file_pair_valid(record, prefix)
        for prefix in ("scenario", "model_report", "results")
    ):
        return False
    results = Path(str(record.get("results_path", "") or ""))
    try:
        return results.stat().st_size == int(record.get("results_size_bytes", -1))
    except (OSError, TypeError, ValueError):
        return False


def _same_path(left: Any, right: Any) -> bool:
    if not left or not right:
        return False
    return Path(str(left)).resolve(strict=False) == Path(str(right)).resolve(strict=False)


def _result_valid(result: Mapping[str, Any], simulation: Mapping[str, Any]) -> bool:
    status = str(result.get("status", "")).upper()
    return (
        result.get("simulation_link_status") == "VERIFIED"
        and _artifact_valid(result)
        and _simulation_valid(simulation)
        and _same_path(result.get("aps_path"), simulation.get("results_path"))
        and str(result.get("aps_sha256", "")).lower()
        == str(simulation.get("results_sha256", "")).lower()
        and bool(status)
        and "FAIL" not in status
        and status != "NOT_CHECKABLE"
    )


def _next_action(
    variant: str,
    case_id: str,
    record: Mapping[str, Any],
    *,
    model_valid: bool,
    simulation_valid: bool,
    result_valid: bool,
) -> Tuple[str, str, str]:
    capability = get_case_capability(variant, case_id)
    if model_valid and simulation_valid and result_valid:
        return (
            "PRESERVE_EVIDENCE",
            "",
            "Case complete; preserve its checksummed evidence.",
        )
    if not model_valid:
        if variant == "test_1" and case_id == "600":
            return (
                "RECONCILE_TEST1_600",
                "Run_VE_SIA4010_Test1_Reconcile_Floor_Insulation.py",
                "Open the existing case 600 project, reconcile the floor insulation, then run Fast Start.",
            )
        if variant == "test_1" and case_id != "1E":
            return (
                "RUN_TEST1_FAST_START",
                "Run_VE_SIA4010_Test1_Fast_Start.py",
                "Open a fresh saved disposable project named for this exact case and run Fast Start.",
            )
        if variant == "test_2A":
            return (
                "QUALIFY_OR_BIND_TEST2A_TEMPLATE",
                "Run_VE_SIA4010_Test2A_Qualification_One_Click.py",
                "Qualify the Test 2A setters in a disposable project, then bind an independently reviewed exact-case template.",
            )
        if variant == "test_1" and case_id == "1E":
            return (
                "BIND_TEST1E_QUALIFIED_TEMPLATE",
                "Run_VE_SIA4010_Capture_Active_Template.py",
                "Capture the exact 1E model, complete independent review, bind it, create a disposable copy, then run Verify Template Model.",
            )
        return (
            "BIND_QUALIFIED_TEMPLATE",
            "Run_VE_SIA4010_Capture_Active_Template.py",
            "Build or open the exact official case, capture it, complete independent review, then bind the qualified template.",
        )
    if not simulation_valid:
        if variant == "test_1" and case_id == "1E":
            launcher = "scripts/probes/Run_VE_SIA4010_Simulate_Qualified_Template.py"
        elif capability.base_test_id == "1":
            launcher = "Run_VE_SIA4010_Simulate_Active_Case.py"
        elif capability.base_test_id == "2":
            launcher = "scripts/probes/Run_VE_SIA4010_Simulate_Qualified_Template.py"
        else:
            launcher = "Run_VE_SIA4010_Tests4_7_Runtime_Capability_Probe.py"
        return (
            "RUN_APACHESIM",
            launcher,
            "Open the verified exact-case project, run the guarded annual simulation and retain the new APS evidence.",
        )
    if not result_valid:
        if capability.base_test_id in {"1", "2"}:
            launcher = "Run_VE_SIA4010_Evaluate_Active_Case.py"
            instruction = "Run the qualified APS extraction and official comparison for this exact case."
        else:
            launcher = "Run_VE_SIA4010_Tests4_7_Runtime_Capability_Probe.py"
            instruction = "Qualify the missing APS output bindings before attempting an official comparison."
        return "EVALUATE_APS", launcher, instruction
    return (
        "REVIEW_EVIDENCE",
        "Run_VE_SIA4010_Navigator.py",
        "Rebuild the evidence navigator and review the inconsistent case state.",
    )


def _case_progress(
    variant: str,
    case_id: str,
    record: Mapping[str, Any],
) -> ExactCaseProgress:
    model = record.get("model_evidence") or {}
    simulation = record.get("simulation_evidence") or {}
    result = record.get("result_evidence") or {}
    model_valid = model.get("status") == "VERIFIED" and _artifact_valid(model)
    simulation_valid = _simulation_valid(simulation)
    result_valid = _result_valid(result, simulation)
    action, launcher, instruction = _next_action(
        variant,
        case_id,
        record,
        model_valid=model_valid,
        simulation_valid=simulation_valid,
        result_valid=result_valid,
    )
    return ExactCaseProgress(
        variant=variant,
        case_id=case_id,
        base_test_id=get_case_capability(variant, case_id).base_test_id,
        model_valid=model_valid,
        simulation_valid=simulation_valid,
        result_valid=result_valid,
        complete=model_valid and simulation_valid and result_valid,
        next_action_code=action,
        launcher=launcher,
        instruction=instruction,
    )


def _required_exact_cases(variants: Iterable[str]) -> Tuple[str, ...]:
    return tuple(
        "{}/{}".format(variant, case_id)
        for variant in variants
        for case_id in TEST_CASES[variant]
    )


def build_validation_campaign(
    registry: Mapping[str, Any],
) -> Dict[str, Any]:
    """Build an optimized all-class campaign from one loaded evidence ledger."""

    records = registry.get("cases")
    if not isinstance(records, Mapping):
        raise ConfigurationError("SIA 4010 evidence registry has no cases object")
    progress: Dict[str, ExactCaseProgress] = {}
    for variant, case_ids in TEST_CASES.items():
        for case_id in case_ids:
            key = "{}/{}".format(variant, case_id)
            if key not in records:
                raise ConfigurationError("Evidence registry is missing {}".format(key))
            progress[key] = _case_progress(variant, case_id, records[key])

    phases = []
    first_action: Optional[Dict[str, Any]] = None
    for phase in CAMPAIGN_PHASES:
        keys = _required_exact_cases(phase.variants)
        pending = [key for key in keys if not progress[key].complete]
        phase_payload = {
            **asdict(phase),
            "exact_case_count": len(keys),
            "complete_case_count": len(keys) - len(pending),
            "pending_cases": pending,
            "status": (
                "COMPLETE"
                if not pending
                else "IN_PROGRESS" if len(pending) < len(keys) else "NOT_STARTED"
            ),
        }
        phases.append(phase_payload)
        if first_action is None and pending:
            item = progress[pending[0]]
            first_action = {
                "phase_id": phase.phase_id,
                "case_key": pending[0],
                "action_code": item.next_action_code,
                "launcher": item.launcher,
                "instruction": item.instruction,
            }

    classes = {}
    for class_id, variants in SIA4010_CLASS_TEST_MATRIX.items():
        keys = _required_exact_cases(variants)
        pending = [key for key in keys if not progress[key].complete]
        classes[class_id] = {
            "status": (
                "TECHNICALLY_COMPLETE_AWAITING_SIA_ATTESTATION"
                if not pending
                else "INCOMPLETE"
            ),
            "required_variants": list(variants),
            "exact_case_count": len(keys),
            "complete_case_count": len(keys) - len(pending),
            "pending_cases": pending,
            "official_attestation_required": True,
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "registry_updated_at_utc": registry.get("updated_at_utc"),
        "summary": {
            "validation_classes": len(classes),
            "technically_complete_classes": sum(
                row["status"].startswith("TECHNICALLY_COMPLETE")
                for row in classes.values()
            ),
            "exact_cases": len(progress),
            "complete_exact_cases": sum(item.complete for item in progress.values()),
        },
        "next_action": first_action,
        "phases": phases,
        "classes": classes,
        "cases": {key: item.to_dict() for key, item in progress.items()},
        "claim_guardrail": (
            "The campaign optimizes technical evidence collection. Only the responsible SIA body can grant official validation."
        ),
    }


def _status_badge(status: str) -> str:
    css = (
        "ok"
        if status == "COMPLETE" or status.startswith("TECHNICALLY_COMPLETE")
        else "work" if status == "IN_PROGRESS" else "blocked"
    )
    return "<span class='badge {}'>{}</span>".format(
        css, html.escape(status.replace("_", " "))
    )


def _render_html(payload: Mapping[str, Any]) -> str:
    summary = payload["summary"]
    next_action = payload.get("next_action") or {}
    phase_cards = []
    for phase in payload["phases"]:
        pending = phase["pending_cases"]
        phase_cards.append(
            "<section class='card'><div class='phase'><span>{}</span>{}</div>"
            "<h2>{}</h2><p>{}</p><div class='meter'><i style='width:{}%'></i></div>"
            "<p class='small'>{}/{} exact cases complete · unlocks {}</p>"
            "{}</section>".format(
                html.escape(phase["phase_id"]),
                _status_badge(phase["status"]),
                html.escape(phase["label"]),
                html.escape(phase["rationale"]),
                int(
                    100 * phase["complete_case_count"] / max(1, phase["exact_case_count"])
                ),
                phase["complete_case_count"],
                phase["exact_case_count"],
                html.escape(", ".join(phase["unlocks"]) or "shared foundation"),
                (
                    "<p class='pending'>Next pending: {}</p>".format(
                        html.escape(pending[0])
                    )
                    if pending
                    else ""
                ),
            )
        )
    class_rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}/{}</td><td>{}</td></tr>".format(
            html.escape(class_id),
            _status_badge(row["status"]),
            row["complete_case_count"],
            row["exact_case_count"],
            html.escape(
                ", ".join(row["pending_cases"][:4])
                + (" …" if len(row["pending_cases"]) > 4 else "")
            ),
        )
        for class_id, row in payload["classes"].items()
    )
    next_block = "<div class='next'><span>NEXT ACTION · {}</span><h2>{}</h2><p>{}</p><code>{}</code></div>".format(
        html.escape(str(next_action.get("phase_id", ""))),
        html.escape(str(next_action.get("case_key", "Campaign complete"))),
        html.escape(
            str(
                next_action.get(
                    "instruction",
                    "Preserve the evidence and submit it for official review.",
                )
            )
        ),
        html.escape(str(next_action.get("launcher", ""))),
    )
    template = """<!doctype html><html lang='en'><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>SIA 4010 accelerated validation campaign</title>
<style>
:root{--navy:#071c2c;--blue:#0069ff;--cyan:#39d6c5;--paper:#f3f7fa;--ink:#142b3b;--muted:#607483;--red:#b8324a;--amber:#9a6300}
*{box-sizing:border-box}body{margin:0;background:var(--paper);font:15px/1.55 "Segoe UI",Arial;color:var(--ink)}
header{padding:38px max(28px,6vw);color:white;background:linear-gradient(120deg,var(--navy),#123f5e)}
header p{margin:6px 0 0;color:#cde3ef}h1{margin:0;font-size:clamp(28px,4vw,46px);letter-spacing:-1.4px}
main{max-width:1200px;margin:auto;padding:28px}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:-54px}
.stat,.card,.next,.tablebox{background:white;border:1px solid #dbe6ed;border-radius:16px;box-shadow:0 8px 28px #102a3a12}
.stat{padding:18px}.stat b{font-size:28px;display:block}.stat span,.small{color:var(--muted)}
.next{margin:20px 0;padding:24px;border-left:6px solid var(--cyan)}.next span,.phase span{font-weight:700;letter-spacing:.08em;color:#17746d}.next h2{margin:5px 0}.next code{display:inline-block;padding:9px 12px;border-radius:8px;background:#edf4f8;color:#17384d}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}.card{padding:20px}.card h2{margin:7px 0;font-size:20px}.phase{display:flex;justify-content:space-between;align-items:center}
.badge{font-size:11px;font-weight:700;padding:5px 9px;border-radius:999px}.badge.ok{background:#dff7ef;color:#08745f}.badge.work{background:#fff0c9;color:var(--amber)}.badge.blocked{background:#ffe3e8;color:var(--red)}
.meter{height:7px;background:#e7eef3;border-radius:9px;overflow:hidden}.meter i{display:block;height:100%;background:linear-gradient(90deg,var(--blue),var(--cyan))}.pending{margin-bottom:0;color:#37576b}
.tablebox{margin-top:18px;overflow:hidden}.tablebox h2{padding:18px 20px;margin:0}table{border-collapse:collapse;width:100%}th,td{padding:12px 16px;border-top:1px solid #e2eaf0;text-align:left}th{background:#f8fafc;color:#456070}
footer{padding:20px 0;color:var(--muted)}@media(max-width:760px){.stats,.grid{grid-template-columns:1fr}.stats{margin-top:0}main{padding:18px}th:nth-child(4),td:nth-child(4){display:none}}
</style><header><h1>SIA 4010 · accelerated campaign</h1><p>One evidence queue for all eight validation classes</p></header><main>
<div class='stats'><div class='stat'><b>{complete}/{cases}</b><span>exact cases complete</span></div><div class='stat'><b>{classes}/8</b><span>classes technically complete</span></div><div class='stat'><b>7</b><span>optimized milestones</span></div></div>
{next_block}<div class='grid'>{phase_cards}</div><div class='tablebox'><h2>Validation-class readiness</h2><table><thead><tr><th>Class</th><th>Status</th><th>Cases</th><th>First pending cases</th></tr></thead><tbody>{class_rows}</tbody></table></div>
<footer>{guardrail}</footer></main></html>"""
    replacements = {
        "{complete}": str(summary["complete_exact_cases"]),
        "{cases}": str(summary["exact_cases"]),
        "{classes}": str(summary["technically_complete_classes"]),
        "{next_block}": next_block,
        "{phase_cards}": "".join(phase_cards),
        "{class_rows}": class_rows,
        "{guardrail}": html.escape(str(payload["claim_guardrail"])),
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    return template


def write_validation_campaign(
    repository_root: Union[str, Path],
    *,
    registry_path: Optional[Union[str, Path]] = None,
    output_directory: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Build and persist JSON/HTML campaign artifacts."""

    repository = Path(repository_root).resolve()
    registry_file = (
        Path(registry_path) if registry_path else repository / REGISTRY_RELATIVE_PATH
    )
    output = (
        Path(output_directory)
        if output_directory
        else repository / OUTPUT_RELATIVE_DIRECTORY
    )
    payload = build_validation_campaign(load_registry(registry_file))
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "sia4010_validation_campaign.json"
    html_path = output / "sia4010_validation_campaign.html"
    payload["artifacts"] = {"json": str(json_path), "html": str(html_path)}
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    html_path.write_text(_render_html(payload), encoding="utf-8")
    return payload
