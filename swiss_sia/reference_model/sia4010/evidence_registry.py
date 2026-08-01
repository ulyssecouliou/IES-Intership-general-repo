"""Persistent cross-project evidence ledger for all SIA 4010 exact cases.

Each official case must live in its own disposable VE project.  This ledger is
the safe coordination boundary between those projects: it stores checksummed
artifact locators, never copies opaque VE state, and rebuilds all eight class
navigators conservatively from the evidence actually present.
"""

import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple, Union

from ...config import SIA4010_CLASS_TEST_MATRIX
from ..exceptions import ConfigurationError
from .active_case_evaluation import ActiveCaseEvaluationReceipt
from .apachesim_qualification import (
    ApacheSimQualificationReceipt,
    TEST1_SIMULATION_SOURCE,
)
from .case_registry import all_case_capabilities, get_case_capability
from .model_scenario import ModelScenario, TEST_CASES
from .navigator import Sia4010ValidationNavigator
from .navigator_report import write_navigator_artifacts
from .preparation_bundle import AllClassesPreparationReceipt
from .test_loader import Sia4010TestLoader


SCHEMA_VERSION = "1.1"
_LEGACY_SCHEMA_VERSIONS = {"1.0"}
_MODEL_PASS = {"PASS"}
_SIMULATION_PASS = "SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION"


def _sha256(path: Path) -> str:
    """Return one lowercase SHA-256 digest."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Atomically write one UTF-8 JSON ledger."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _case_key(variant: str, case_id: str) -> str:
    """Return the stable exact-case ledger key."""

    return "{}/{}".format(variant, case_id)


def _empty_simulation_evidence() -> Dict[str, Any]:
    """Return one fail-closed ApacheSim evidence slot."""

    return {
        "status": "NOT_RUN",
        "artifact_path": "",
        "artifact_sha256": "",
        "project_path": "",
        "scenario_path": "",
        "scenario_sha256": "",
        "model_report_path": "",
        "model_report_sha256": "",
        "results_path": "",
        "results_sha256": "",
        "results_size_bytes": 0,
        "model_evidence_link_status": "NOT_LINKED",
        "aps_evaluation_required": True,
        "compliance_claim_allowed": False,
    }


def _empty_case_record(variant: str, case_id: str) -> Dict[str, Any]:
    """Return a fail-closed record for one registered exact case."""

    capability = get_case_capability(variant, case_id)
    return {
        "variant": variant,
        "case_id": case_id,
        "base_test_id": capability.base_test_id,
        "capability": capability.to_dict(),
        "preparation_artifacts": [],
        "geometry_artifact": None,
        "model_evidence": {
            "status": "MISSING",
            "artifact_path": "",
            "artifact_sha256": "",
            "project_path": "",
        },
        "simulation_evidence": _empty_simulation_evidence(),
        "result_evidence": {
            "status": "NOT_CHECKABLE",
            "artifact_path": "",
            "artifact_sha256": "",
            "project_path": "",
            "aps_path": "",
            "aps_sha256": "",
            "simulation_link_status": "NOT_LINKED",
        },
    }


def new_registry_payload() -> Dict[str, Any]:
    """Return a complete 30-case ledger with no evidence claims."""

    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "cases": {
            _case_key(item.variant, item.case_id): _empty_case_record(
                item.variant, item.case_id
            )
            for item in all_case_capabilities()
        },
        "claim_guardrail": (
            "The ledger coordinates source-traced technical evidence. Missing, "
            "unreadable or checksum-mismatched artifacts never satisfy a gate."
        ),
    }


def load_registry(path: Union[str, Path]) -> Dict[str, Any]:
    """Load one ledger or create an empty 30-case payload."""

    registry_path = Path(path)
    if not registry_path.is_file():
        return new_registry_payload()
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigurationError(
            "Invalid SIA 4010 evidence registry: {}".format(exc)
        ) from exc
    source_version = str(payload.get("schema_version", ""))
    if source_version not in {SCHEMA_VERSION, *_LEGACY_SCHEMA_VERSIONS}:
        raise ConfigurationError(
            "Unsupported evidence registry schema: {}".format(
                payload.get("schema_version")
            )
        )
    expected = {
        _case_key(item.variant, item.case_id)
        for item in all_case_capabilities()
    }
    if set(payload.get("cases", {})) != expected:
        raise ConfigurationError(
            "Evidence registry exact-case set does not match the 30-case contract"
        )
    for capability in all_case_capabilities():
        record = payload["cases"][
            _case_key(capability.variant, capability.case_id)
        ]
        record["base_test_id"] = capability.base_test_id
        record["capability"] = capability.to_dict()
        if source_version in _LEGACY_SCHEMA_VERSIONS:
            record.setdefault(
                "simulation_evidence", _empty_simulation_evidence()
            )
            result = record.setdefault("result_evidence", {})
            result.setdefault("aps_path", "")
            result.setdefault("aps_sha256", "")
            result.setdefault("simulation_link_status", "NOT_LINKED")
        elif "simulation_evidence" not in record:
            raise ConfigurationError(
                "Evidence registry case '{}' has no simulation evidence slot".format(
                    _case_key(capability.variant, capability.case_id)
                )
            )
    if source_version in _LEGACY_SCHEMA_VERSIONS:
        payload["migrated_from_schema_version"] = source_version
        payload["schema_version"] = SCHEMA_VERSION
    return payload


def synchronize_preparation(
    registry_path: Union[str, Path],
    receipt: AllClassesPreparationReceipt,
) -> Dict[str, Any]:
    """Merge an all-class preparation receipt without erasing later evidence."""

    path = Path(registry_path)
    payload = load_registry(path)
    for class_receipt in receipt.classes:
        for case in class_receipt.cases:
            record = payload["cases"][_case_key(case.variant, case.case_id)]
            preparation = str(case.audit_path)
            if preparation not in record["preparation_artifacts"]:
                record["preparation_artifacts"].append(preparation)
            record["preparation_artifacts"].sort()
            if case.geometry_artifact_path is not None:
                geometry = Path(case.geometry_artifact_path)
                record["geometry_artifact"] = {
                    "path": str(geometry),
                    "sha256": _sha256(geometry) if geometry.is_file() else "",
                    "status": (
                        "VERIFIED"
                        if geometry.is_file()
                        else "MISSING"
                    ),
                }
    payload["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    _write_json(path, payload)
    return payload


def register_model_outcome(
    registry_path: Union[str, Path],
    scenario: ModelScenario,
    *,
    workflow_status: str,
    report_path: Union[str, Path],
    project_path: Union[str, Path],
) -> Dict[str, Any]:
    """Record one generated-model report only after checksum verification."""

    if not scenario.is_official:
        raise ConfigurationError("Custom scenarios cannot enter the SIA ledger")
    report = Path(report_path)
    if not report.is_file():
        raise ConfigurationError(
            "Model audit report does not exist: {}".format(report)
        )
    path = Path(registry_path)
    payload = load_registry(path)
    record = payload["cases"][
        _case_key(scenario.variant, scenario.case_id)
    ]
    normalized = str(workflow_status).strip().upper()
    record["model_evidence"] = {
        "status": (
            "VERIFIED"
            if normalized in _MODEL_PASS
            else "FAILED"
            if "FAIL" in normalized
            else "BLOCKED_WARNINGS"
        ),
        "workflow_status": normalized,
        "artifact_path": str(report),
        "artifact_sha256": _sha256(report),
        "project_path": str(project_path),
    }
    payload["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    _write_json(path, payload)
    return payload


def register_case_evaluation(
    registry_path: Union[str, Path],
    receipt: ActiveCaseEvaluationReceipt,
    *,
    project_path: Union[str, Path],
) -> Dict[str, Any]:
    """Record one checksummed APS comparison artifact in the shared ledger."""

    if receipt.artifact_path is None or not receipt.artifact_path.is_file():
        raise ConfigurationError(
            "Active-case evaluation artifact is missing: {}".format(
                receipt.artifact_path
            )
        )
    artifact_payload = _load_json_artifact(
        Path(receipt.artifact_path), "active-case evaluation"
    )
    for key, expected in (
        ("variant", receipt.variant),
        ("case_id", receipt.case_id),
        ("status", receipt.status),
    ):
        if str(artifact_payload.get(key, "")) != str(expected):
            raise ConfigurationError(
                "Active-case evaluation {} mismatch: expected {!r}, found {!r}".format(
                    key, expected, artifact_payload.get(key)
                )
            )
    source_evidence = artifact_payload.get("source_evidence")
    if not isinstance(source_evidence, Mapping):
        raise ConfigurationError(
            "Active-case evaluation has no source_evidence object"
        )
    aps_path = Path(str(source_evidence.get("aps_path", "") or ""))
    aps_sha256 = str(source_evidence.get("aps_sha256", "") or "").lower()
    if not aps_path.is_file() or not aps_sha256:
        raise ConfigurationError(
            "Active-case evaluation APS evidence is missing: {}".format(aps_path)
        )
    if _sha256(aps_path) != aps_sha256:
        raise ConfigurationError(
            "Active-case evaluation APS checksum mismatch: {}".format(aps_path)
        )

    path = Path(registry_path)
    payload = load_registry(path)
    record = payload["cases"][_case_key(receipt.variant, receipt.case_id)]
    simulation = record["simulation_evidence"]
    simulation_linked = (
        _simulation_evidence_is_valid(simulation)
        and _same_path(simulation.get("results_path"), aps_path)
        and str(simulation.get("results_sha256", "")).lower() == aps_sha256
        and _same_path(simulation.get("project_path"), project_path)
    )
    record["result_evidence"] = {
        "status": receipt.status,
        "artifact_path": str(receipt.artifact_path),
        "artifact_sha256": _sha256(receipt.artifact_path),
        "project_path": str(project_path),
        "aps_path": str(aps_path),
        "aps_sha256": aps_sha256,
        "simulation_link_status": (
            "VERIFIED" if simulation_linked else "NOT_LINKED"
        ),
        "observed_metric_count": receipt.observed_metric_count,
        "distribution_criterion_count": receipt.distribution_criterion_count,
        "acceptance_criterion_available": (
            getattr(receipt, "acceptance_criterion_available", None)
        ),
        "required_output_scope_complete": (
            getattr(receipt, "required_output_scope_complete", None)
        ),
    }
    payload["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    _write_json(path, payload)
    return payload


def _load_json_artifact(path: Path, context: str) -> Dict[str, Any]:
    """Load one JSON evidence object with a fail-closed error."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigurationError(
            "Invalid {} artifact '{}': {}".format(context, path, exc)
        ) from exc
    if not isinstance(payload, dict):
        raise ConfigurationError(
            "{} artifact must contain a JSON object: {}".format(context, path)
        )
    return payload


def _same_path(left: Any, right: Any) -> bool:
    """Compare two filesystem locators without requiring that they exist."""

    left_text = str(left or "")
    right_text = str(right or "")
    if not left_text or not right_text:
        return False
    return Path(left_text).resolve(strict=False) == Path(right_text).resolve(
        strict=False
    )


def _verified_file(path_value: Any, digest_value: Any, context: str) -> Path:
    """Return a checksum-verified evidence file or fail closed."""

    path = Path(str(path_value or ""))
    expected = str(digest_value or "").lower()
    if not path.is_file():
        raise ConfigurationError("{} does not exist: {}".format(context, path))
    actual = _sha256(path)
    if not expected or actual != expected:
        raise ConfigurationError(
            "{} checksum mismatch: expected {}, found {}".format(
                context, expected or "<missing>", actual
            )
        )
    return path


def register_case_simulation(
    registry_path: Union[str, Path],
    receipt: ApacheSimQualificationReceipt,
    *,
    project_path: Union[str, Path],
) -> Dict[str, Any]:
    """Record a checksum-verified model-to-ApacheSim-to-APS evidence chain."""

    capability = get_case_capability(receipt.variant, receipt.case_id)
    if not capability.apachesim_qualification_supported:
        raise ConfigurationError(
            "ApacheSim evidence is not supported for {}/{}".format(
                receipt.variant, receipt.case_id
            )
        )
    if receipt.status != _SIMULATION_PASS:
        raise ConfigurationError(
            "ApacheSim receipt is not successful: {}".format(receipt.status)
        )
    if (
        receipt.compliance_claim_allowed is not False
        or receipt.aps_evaluation_required is not True
        or receipt.runtime_qualification_required is not True
    ):
        raise ConfigurationError(
            "ApacheSim receipt guardrails are incomplete or unsafe"
        )
    expected_options = {
        "start_day": 1,
        "start_month": 1,
        "end_day": 31,
        "end_month": 12,
        "reporting_interval": 3,
        "results_filename": Path(receipt.results_path).name,
    }
    for key, expected in expected_options.items():
        if receipt.requested_options.get(key) != expected:
            raise ConfigurationError(
                "ApacheSim receipt option {} mismatch: expected {!r}, found {!r}".format(
                    key, expected, receipt.requested_options.get(key)
                )
            )
        if receipt.options_after.get(key) != expected:
            raise ConfigurationError(
                "ApacheSim option read-back {} mismatch: expected {!r}, found {!r}".format(
                    key, expected, receipt.options_after.get(key)
                )
            )
    if not _same_path(receipt.project_path, project_path):
        raise ConfigurationError(
            "ApacheSim project mismatch: receipt={!r}, active={!r}".format(
                receipt.project_path, str(project_path)
            )
        )

    audit_path = Path(receipt.audit_path)
    if not audit_path.is_file():
        raise ConfigurationError(
            "ApacheSim audit does not exist: {}".format(audit_path)
        )
    scenario_path = _verified_file(
        receipt.scenario_path,
        receipt.scenario_sha256,
        "ApacheSim scenario",
    )
    model_report_path = _verified_file(
        receipt.model_report_path,
        receipt.model_report_sha256,
        "ApacheSim model report",
    )
    results_path = _verified_file(
        receipt.results_path,
        receipt.results_sha256,
        "ApacheSim APS",
    )
    if results_path.stat().st_size != int(receipt.results_size_bytes):
        raise ConfigurationError(
            "ApacheSim APS size mismatch: expected {}, found {}".format(
                receipt.results_size_bytes, results_path.stat().st_size
            )
        )

    scenario = ModelScenario.load(scenario_path)
    if (
        not scenario.is_official
        or scenario.variant != receipt.variant
        or scenario.case_id != receipt.case_id
    ):
        raise ConfigurationError(
            "ApacheSim scenario identity does not match {}/{}".format(
                receipt.variant, receipt.case_id
            )
        )

    audit = _load_json_artifact(audit_path, "ApacheSim qualification")
    for key, expected in (
        ("status", receipt.status),
        ("variant", receipt.variant),
        ("case_id", receipt.case_id),
        ("results_sha256", receipt.results_sha256),
        ("scenario_sha256", receipt.scenario_sha256),
        ("model_report_sha256", receipt.model_report_sha256),
    ):
        if str(audit.get(key, "")) != str(expected):
            raise ConfigurationError(
                "ApacheSim audit {} mismatch: expected {!r}, found {!r}".format(
                    key, expected, audit.get(key)
                )
            )
    for key, expected_path in (
        ("project_path", project_path),
        ("results_path", results_path),
        ("scenario_path", scenario_path),
        ("model_report_path", model_report_path),
    ):
        if not _same_path(audit.get(key), expected_path):
            raise ConfigurationError(
                "ApacheSim audit {} does not match {}".format(key, expected_path)
            )
    if (
        audit.get("compliance_claim_allowed") is not False
        or audit.get("aps_evaluation_required") is not True
        or audit.get("runtime_qualification_required") is not True
    ):
        raise ConfigurationError(
            "ApacheSim audit guardrails are incomplete or unsafe"
        )
    if audit.get("source") != TEST1_SIMULATION_SOURCE:
        raise ConfigurationError(
            "ApacheSim audit does not cite the qualified Test 1 source"
        )
    source_file = audit.get("source_file")
    if not isinstance(source_file, Mapping):
        raise ConfigurationError(
            "ApacheSim audit has no checksum-traced source file"
        )
    _verified_file(
        source_file.get("path"),
        source_file.get("sha256"),
        "ApacheSim Test 1 specification",
    )
    confirmed = audit.get("confirmed_contract")
    if not isinstance(confirmed, Mapping):
        raise ConfigurationError(
            "ApacheSim audit has no confirmed temporal contract"
        )
    if confirmed.get("simulation_period") != (
        "2011-01-01 through 2011-12-31"
    ):
        raise ConfigurationError(
            "ApacheSim audit simulation period is not the confirmed annual period"
        )
    if confirmed.get("required_result_frequency") != "hourly":
        raise ConfigurationError(
            "ApacheSim audit result frequency is not hourly"
        )
    if confirmed.get("requested_apachesim_options") != dict(
        receipt.requested_options
    ):
        raise ConfigurationError(
            "ApacheSim audit requested options do not match the receipt"
        )

    path = Path(registry_path)
    payload = load_registry(path)
    record = payload["cases"][
        _case_key(receipt.variant, receipt.case_id)
    ]
    model = record["model_evidence"]
    model_linked = (
        model.get("status") == "VERIFIED"
        and _artifact_is_valid(model)
        and _same_path(model.get("artifact_path"), model_report_path)
        and _same_path(model.get("project_path"), project_path)
    )
    record["simulation_evidence"] = {
        "status": receipt.status,
        "artifact_path": str(audit_path),
        "artifact_sha256": _sha256(audit_path),
        "project_path": str(project_path),
        "scenario_path": str(scenario_path),
        "scenario_sha256": receipt.scenario_sha256,
        "model_report_path": str(model_report_path),
        "model_report_sha256": receipt.model_report_sha256,
        "results_path": str(results_path),
        "results_sha256": receipt.results_sha256,
        "results_size_bytes": receipt.results_size_bytes,
        "model_evidence_link_status": (
            "VERIFIED" if model_linked else "NOT_LINKED"
        ),
        "aps_evaluation_required": True,
        "compliance_claim_allowed": False,
    }
    payload["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    _write_json(path, payload)
    return payload


def _artifact_is_valid(evidence: Mapping[str, Any]) -> bool:
    """Return whether an evidence locator still exists with the stored digest."""

    path_text = str(evidence.get("artifact_path", "") or "")
    expected = str(evidence.get("artifact_sha256", "") or "").lower()
    if not path_text or not expected:
        return False
    path = Path(path_text)
    return path.is_file() and _sha256(path) == expected


def _simulation_evidence_is_valid(evidence: Mapping[str, Any]) -> bool:
    """Return whether every file in one ApacheSim evidence chain is intact."""

    if (
        str(evidence.get("status", "")) != _SIMULATION_PASS
        or evidence.get("aps_evaluation_required") is not True
        or evidence.get("compliance_claim_allowed") is not False
        or not _artifact_is_valid(evidence)
    ):
        return False
    for prefix in ("scenario", "model_report", "results"):
        path_text = str(evidence.get("{}_path".format(prefix), "") or "")
        expected = str(
            evidence.get("{}_sha256".format(prefix), "") or ""
        ).lower()
        path = Path(path_text)
        if not path_text or not expected or not path.is_file():
            return False
        if _sha256(path) != expected:
            return False
    results = Path(str(evidence["results_path"]))
    return (
        results.stat().st_size == int(evidence.get("results_size_bytes", -1))
    )


def _variant_model_status(
    cases: Mapping[str, Any], variant: str
) -> str:
    """Return PASS only when every exact model case is checksum-valid."""

    return (
        "PASS"
        if all(
            cases[_case_key(variant, case_id)]["model_evidence"]["status"]
            == "VERIFIED"
            and _artifact_is_valid(
                cases[_case_key(variant, case_id)]["model_evidence"]
            )
            for case_id in TEST_CASES[variant]
        )
        else "BLOCKED"
    )


def _variant_result_record(
    cases: Mapping[str, Any], variant: str
) -> Optional[Mapping[str, Any]]:
    """Return the exact official-result evidence record for one variant."""

    result_case_ids = ("1E",) if variant == "test_1" else TEST_CASES[variant]
    case_records = tuple(
        cases[_case_key(variant, case_id)]
        for case_id in result_case_ids
    )
    records = tuple(item["result_evidence"] for item in case_records)
    if not records or not all(
        _artifact_is_valid(result)
        and result.get("simulation_link_status") == "VERIFIED"
        and _simulation_evidence_is_valid(case["simulation_evidence"])
        and _same_path(
            result.get("aps_path"),
            case["simulation_evidence"].get("results_path"),
        )
        and str(result.get("aps_sha256", "")).lower()
        == str(
            case["simulation_evidence"].get("results_sha256", "")
        ).lower()
        for case, result in zip(case_records, records)
    ):
        return None
    statuses = {str(item.get("status", "")).upper() for item in records}
    status = (
        "FAILED"
        if any("FAIL" in item for item in statuses)
        else "OFFICIAL_RESULTS_RECORDED"
        if statuses == {"OFFICIAL_RESULTS_RECORDED"}
        else "NOT_CHECKABLE"
    )
    return {
        "status": status,
        "artifact_path": ";".join(
            str(item["artifact_path"]) for item in records
        ),
    }


def build_all_class_navigators(
    registry_path: Union[str, Path],
    bundle_root: Union[str, Path],
    output_directory: Union[str, Path],
) -> Dict[str, Any]:
    """Rebuild all eight navigators from checksum-valid ledger evidence."""

    payload = load_registry(registry_path)
    bundle = Sia4010TestLoader().load_bundle(bundle_root)
    cases = payload["cases"]
    output = Path(output_directory)
    evaluations = {}
    artifacts = {}
    for class_id, variants in SIA4010_CLASS_TEST_MATRIX.items():
        model_statuses = {
            variant: _variant_model_status(cases, variant)
            for variant in variants
        }
        result_records = {
            variant: _variant_result_record(cases, variant)
            for variant in variants
        }
        locators = {
            variant: str(record["artifact_path"])
            for variant, record in result_records.items()
            if record is not None
        }
        result_map = {
            variant: {"status": record["status"]}
            for variant, record in result_records.items()
            if record is not None
        }
        evaluation = Sia4010ValidationNavigator.evaluate(
            class_id,
            bundle_verified=True,
            model_case_statuses=model_statuses,
            candidate_result_locators=locators,
            test_results_map=result_map,
        )
        evaluations[class_id] = evaluation.to_dict()
        artifacts[class_id] = write_navigator_artifacts(
            evaluation, output
        )
    global_payload = {
        "schema_version": SCHEMA_VERSION,
        "official_bundle": {
            "root": str(bundle.root),
            "manifest": str(bundle.manifest_path),
            "verified": True,
        },
        "registry_path": str(Path(registry_path)),
        "classes": evaluations,
        "artifacts": artifacts,
        "summary": {
            "validation_classes": len(evaluations),
            "exact_cases": len(cases),
            "checksum_valid_model_cases": sum(
                record["model_evidence"].get("status") == "VERIFIED"
                and _artifact_is_valid(record["model_evidence"])
                for record in cases.values()
            ),
            "checksum_valid_apachesim_cases": sum(
                _simulation_evidence_is_valid(
                    record["simulation_evidence"]
                )
                for record in cases.values()
            ),
            "simulation_linked_aps_evaluations": sum(
                record["result_evidence"].get("simulation_link_status")
                == "VERIFIED"
                and _artifact_is_valid(record["result_evidence"])
                for record in cases.values()
            ),
            "ready_for_official_review": sum(
                item["overall_status"] == "READY_FOR_OFFICIAL_REVIEW"
                for item in evaluations.values()
            ),
            "official_band_failures": sum(
                item["overall_status"] == "OFFICIAL_BAND_FAILED"
                for item in evaluations.values()
            ),
        },
        "claim_guardrail": (
            "Only a checksum-valid model, ApacheSim execution and linked APS "
            "evaluation satisfy a gate. The result remains a technical "
            "navigator, not an SIA attestation."
        ),
    }
    global_json = output / "sia4010_all_classes_navigator.json"
    global_html = output / "sia4010_all_classes_navigator.html"
    global_payload["global_artifacts"] = {
        "json": str(global_json),
        "html": str(global_html),
    }
    _write_json(global_json, global_payload)
    rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            html.escape(class_id),
            html.escape(item["overall_status"]),
            html.escape(artifacts[class_id]["html"]),
        )
        for class_id, item in evaluations.items()
    )
    global_html.write_text(
        (
            "<!doctype html><html lang='fr'><meta charset='utf-8'>"
            "<title>SIA 4010 — huit classes</title>"
            "<style>body{{font:15px Segoe UI,Arial;margin:32px;color:#17202a}}"
            "table{{border-collapse:collapse;width:100%}}th,td{{padding:10px;"
            "border:1px solid #d9e0e6;text-align:left}}th{{background:#17324d;"
            "color:white}}</style><h1>Navigateur SIA 4010 — huit classes</h1>"
            "<table><thead><tr><th>Classe</th><th>État</th>"
            "<th>Rapport</th></tr></thead><tbody>{}</tbody></table>"
            "<p>{}</p></html>"
        ).format(rows, html.escape(global_payload["claim_guardrail"])),
        encoding="utf-8",
    )
    return global_payload
