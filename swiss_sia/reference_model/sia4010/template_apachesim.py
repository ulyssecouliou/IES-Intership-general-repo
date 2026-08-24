"""Guarded annual ApacheSim execution for qualified SIA 4010 templates.

The supported routes are diagnostic Test 1E and Test 2A-2D because their
one-zone APS extraction and official comparison bindings are already qualified.
The runner does not guess an engine timestep or preconditioning duration.  It
sets only the full-year period, hourly output and a collision-free APS name.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Union

from .model_scenario import ModelScenario
from .scenario_preflight import is_temporary_ve_project
from .template_strategy import project_signature


SUPPORTED_TEMPLATE_CASES = frozenset(
    {
        ("test_1", "1E"),
        ("test_2A", "2A"),
        ("test_2B", "2B"),
        ("test_2C", "2C"),
        ("test_2D", "2D"),
    }
)
TEMPLATE_MODEL_STATUS = "QUALIFIED_TEMPLATE_MODEL_VERIFIED"
SIMULATION_STATUS = "SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION"
TEST2_SIMULATION_SOURCE = "SIA 4010 Test 2 specification, pages 1-2"
TEST1E_SIMULATION_SOURCE = (
    "SIA 4010 Test 1 diagnostic 1E specification, pages 1-2"
)


class TemplateApacheSimError(RuntimeError):
    """Raised when a qualified-template simulation cannot be proved."""


@dataclass(frozen=True)
class TemplateApacheSimReceipt:
    """Checksummed evidence returned by one synchronous Test 2 run."""

    status: str
    variant: str
    case_id: str
    project_path: str
    model_report_path: str
    model_report_sha256: str
    scenario_path: str
    scenario_sha256: str
    requested_options: Dict[str, Any]
    options_before: Dict[str, Any]
    options_after: Dict[str, Any]
    results_path: str
    results_sha256: str
    results_size_bytes: int
    audit_path: str
    source_path: str
    source_sha256: str
    compliance_claim_allowed: bool = False
    aps_evaluation_required: bool = True
    template_qualification_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path, context: str) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise TemplateApacheSimError(
            "Invalid {} '{}': {}".format(context, path, exc)
        ) from exc
    if not isinstance(payload, dict):
        raise TemplateApacheSimError("{} must be a JSON object".format(context))
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _same_path(left: Any, right: Any) -> bool:
    if not left or not right:
        return False
    return Path(str(left)).resolve(strict=False) == Path(str(right)).resolve(
        strict=False
    )


def _json_mapping(value: Any, context: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TemplateApacheSimError("{} did not return a mapping".format(context))
    try:
        return json.loads(json.dumps(dict(value), default=str))
    except (TypeError, ValueError) as exc:
        raise TemplateApacheSimError(
            "{} cannot be serialized: {}".format(context, exc)
        ) from exc


def _verify_file_pair(payload: Mapping[str, Any], prefix: str) -> Path:
    path = Path(str(payload.get("{}_path".format(prefix)) or ""))
    expected = str(payload.get("{}_sha256".format(prefix)) or "").lower()
    if not path.is_file() or not expected or _sha256(path) != expected:
        raise TemplateApacheSimError(
            "Template model {} evidence is missing or stale: {}".format(
                prefix, path
            )
        )
    return path


def verify_template_model_evidence(
    project_path: Union[str, Path],
    scenario: ModelScenario,
) -> Path:
    """Return the intact exact-case model proof or fail closed."""

    project = Path(project_path).resolve()
    evidence_path = (
        project
        / "sia4010_artifacts"
        / "templates"
        / "template_model_evidence.json"
    )
    evidence = _load_json(evidence_path, "qualified template model evidence")
    if evidence.get("status") != TEMPLATE_MODEL_STATUS:
        raise TemplateApacheSimError(
            "Template model evidence is not verified: {!r}".format(
                evidence.get("status")
            )
        )
    if (
        str(evidence.get("variant") or "") != scenario.variant
        or str(evidence.get("case_id") or "") != scenario.case_id
    ):
        raise TemplateApacheSimError(
            "Template model evidence belongs to another exact case"
        )
    if not _same_path(evidence.get("project_path"), project):
        raise TemplateApacheSimError(
            "Template model evidence belongs to another VE project"
        )
    scenario_evidence = _verify_file_pair(evidence, "scenario")
    if not _same_path(scenario_evidence, project / "sia_model_scenario.json"):
        raise TemplateApacheSimError("Template evidence points to another scenario")
    _verify_file_pair(evidence, "instantiation_report")
    _verify_file_pair(evidence, "qualification_manifest")
    current = project_signature(project)["template_signature_sha256"]
    if str(evidence.get("template_signature_sha256") or "").lower() != str(
        current
    ).lower():
        raise TemplateApacheSimError(
            "VE project inputs changed after template-model verification"
        )
    if evidence.get("compliance_claim_allowed") is not False:
        raise TemplateApacheSimError("Template model evidence has unsafe guardrails")
    return evidence_path


def _safe_results_name(variant: str, case_id: str, stamp: str) -> str:
    value = re.sub(
        r"[^A-Za-z0-9_.-]+",
        "_",
        "SIA4010_{}_{}_{}".format(variant, case_id, stamp),
    ).strip("._")
    if not value:
        raise TemplateApacheSimError("Cannot create a safe APS filename")
    return value + ".aps"


def _wait_for_aps(path: Path, timeout_seconds: float) -> None:
    deadline = time.monotonic() + max(0.0, float(timeout_seconds))
    while not (path.is_file() and path.stat().st_size > 0):
        if time.monotonic() >= deadline:
            raise TemplateApacheSimError(
                "ApacheSim returned without a non-empty APS file: {}".format(path)
            )
        time.sleep(0.1)


def run_qualified_template_apachesim(
    *,
    project: Any,
    apachesim_factory: Callable[[], Any],
    repository_root: Union[str, Path],
    now: Optional[datetime] = None,
    file_wait_seconds: float = 10.0,
) -> TemplateApacheSimReceipt:
    """Run an exact qualified Test 1E/2 template for a full hourly year."""

    project_path = Path(str(getattr(project, "path", "") or "")).resolve()
    if not project_path.is_dir():
        raise TemplateApacheSimError(
            "The active VE project is unavailable or unsaved: {}".format(project_path)
        )
    if is_temporary_ve_project(project_path):
        raise TemplateApacheSimError(
            "Template ApacheSim is forbidden in a temporary VEPROJ project"
        )
    scenario_path = project_path / "sia_model_scenario.json"
    scenario = ModelScenario.load(scenario_path)
    if not scenario.is_official or (
        scenario.variant, scenario.case_id
    ) not in SUPPORTED_TEMPLATE_CASES:
        raise TemplateApacheSimError(
            "Qualified-template ApacheSim supports Test 1E and Test 2A-2D only"
        )
    model_evidence_path = verify_template_model_evidence(project_path, scenario)
    is_test1e = (scenario.variant, scenario.case_id) == ("test_1", "1E")
    test_directory = "Test1" if is_test1e else "Test2"
    specification_name = (
        "Spezifikation_Test1.pdf" if is_test1e else "Spezifikation_Test2.pdf"
    )
    simulation_source = (
        TEST1E_SIMULATION_SOURCE if is_test1e else TEST2_SIMULATION_SOURCE
    )
    specification = (
        Path(repository_root)
        / "SIA_4010_geteilter_Link"
        / test_directory
        / specification_name
    )
    if not specification.is_file():
        raise TemplateApacheSimError(
            "Official case specification is missing: {}".format(specification)
        )
    calendar_source = (
        Path(repository_root)
        / "SIA_4010_geteilter_Link"
        / "Test2"
        / "Spezifikation_Test2.pdf"
    )
    if not calendar_source.is_file():
        raise TemplateApacheSimError(
            "Official 2022 calendar source is missing: {}".format(
                calendar_source
            )
        )

    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    stamp = current_time.astimezone(timezone.utc).strftime("%Y%m%d_%H%M%S")
    results_name = _safe_results_name(scenario.variant, scenario.case_id, stamp)
    results_path = project_path / "Vista" / results_name
    if results_path.exists():
        raise TemplateApacheSimError(
            "Refusing to overwrite APS evidence: {}".format(results_path)
        )
    audit_path = (
        project_path
        / "sia4010_artifacts"
        / "simulation"
        / "SIA4010_{}_{}_template_apachesim.json".format(
            scenario.variant, scenario.case_id
        )
    )
    requested = {
        "start_day": 1,
        "start_month": 1,
        "end_day": 31,
        "end_month": 12,
        "reporting_interval": 3,
        "results_filename": results_name,
    }
    base = {
        "schema_version": "1.0",
        "status": "STARTED",
        "generated_at_utc": current_time.astimezone(timezone.utc).isoformat(),
        "variant": scenario.variant,
        "case_id": scenario.case_id,
        "project_path": str(project_path),
        "source": simulation_source,
        "source_file": {
            "path": str(specification),
            "sha256": _sha256(specification),
        },
        "calendar_source_file": {
            "path": str(calendar_source),
            "sha256": _sha256(calendar_source),
            "basis": (
                "Diagnostic 1E inherits the Test 2 Zurich-Kloten 2022 "
                "calendar through the Test 1 diagnostic chain."
                if is_test1e
                else "Test 2 prescribes the Zurich-Kloten 2022 calendar."
            ),
        },
        "confirmed_contract": {
            "simulation_period": "2022-01-01 through 2022-12-31",
            "required_result_frequency": "hourly",
            "requested_apachesim_options": requested,
        },
        "deliberately_unset_engine_options": {
            "simulation_timestep": "Not prescribed; retained and recorded.",
            "preconditioning_days": "Not prescribed; retained and recorded.",
        },
        "template_model_evidence": {
            "path": str(model_evidence_path),
            "sha256": _sha256(model_evidence_path),
            "status": TEMPLATE_MODEL_STATUS,
        },
        "compliance_claim_allowed": False,
        "aps_evaluation_required": True,
        "template_qualification_required": True,
    }
    before: Dict[str, Any] = {}
    after: Dict[str, Any] = {}
    try:
        sim = apachesim_factory()
        for method in ("get_options", "set_options", "run_simulation"):
            if not callable(getattr(sim, method, None)):
                raise TemplateApacheSimError(
                    "ApacheSim.{} is unavailable".format(method)
                )
        before = _json_mapping(sim.get_options(), "ApacheSim.get_options()")
        if sim.set_options(dict(requested)) is not True:
            raise TemplateApacheSimError("ApacheSim.set_options() did not return True")
        after = _json_mapping(
            sim.get_options(), "ApacheSim.get_options() read-back"
        )
        mismatches = {
            key: {"requested": value, "readback": after.get(key)}
            for key, value in requested.items()
            if after.get(key) != value
        }
        if mismatches:
            raise TemplateApacheSimError(
                "ApacheSim option read-back mismatch: {}".format(mismatches)
            )
        if sim.run_simulation(queue_to_tasks=False) is not True:
            raise TemplateApacheSimError(
                "ApacheSim.run_simulation(queue_to_tasks=False) did not return True"
            )
        _wait_for_aps(results_path, file_wait_seconds)
    except Exception as exc:
        error = exc if isinstance(exc, TemplateApacheSimError) else TemplateApacheSimError(str(exc))
        _write_json(
            audit_path,
            {
                **base,
                "status": "FAIL",
                "error": str(error),
                "options_before": before,
                "options_after": after,
                "results_path": str(results_path),
            },
        )
        raise TemplateApacheSimError("{} Audit: {}".format(error, audit_path)) from exc

    receipt = TemplateApacheSimReceipt(
        status=SIMULATION_STATUS,
        variant=scenario.variant,
        case_id=scenario.case_id,
        project_path=str(project_path),
        model_report_path=str(model_evidence_path),
        model_report_sha256=_sha256(model_evidence_path),
        scenario_path=str(scenario_path),
        scenario_sha256=_sha256(scenario_path),
        requested_options=dict(requested),
        options_before=before,
        options_after=after,
        results_path=str(results_path),
        results_sha256=_sha256(results_path),
        results_size_bytes=results_path.stat().st_size,
        audit_path=str(audit_path),
        source_path=str(specification),
        source_sha256=_sha256(specification),
    )
    _write_json(
        audit_path,
        {
            **base,
            **receipt.to_dict(),
            "claim_guardrail": (
                "A successful simulation is not a result. Qualified APS "
                "extraction and both official Test 2 criteria remain required."
            ),
        },
    )
    return receipt
