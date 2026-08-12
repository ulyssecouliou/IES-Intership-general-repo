"""Fail-closed hybrid execution strategy for SIA 4010 VE projects.

The installed ``iesve`` API is sufficient for direct Test 1 generation and
selected guarded bindings, but it has not demonstrated full construction of
the ApacheHVAC/plant topologies required by Tests 4-7.  This module permits a
reviewed VE project template to fill that technical gap without weakening the
evidence gate.  An unreviewed project, a missing checksum, or stale template
always remains blocked.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple, Union

from ..exceptions import ConfigurationError
from .case_registry import get_case_capability
from .model_scenario import TEST_CASES


TEMPLATE_BINDINGS_FILENAME = "sia4010_template_bindings.json"
QUALIFIED = "QUALIFIED"

_ROOT_CRITICAL_SUFFIXES = {
    ".mdl",
    ".mit",
    ".mec",
    ".asp",
    ".mcl",
    ".msf",
    ".mtd",
    ".mwf",
}
_SUBDIRECTORY_CRITICAL_SUFFIXES = {
    "apache": {
        ".apa",
        ".asd",
        ".asi",
        ".bri",
        ".ccn",
        ".clc",
        ".con",
        ".dfa",
        ".mat",
        ".mec",
        ".mhf",
        ".opt",
        ".pdb",
        ".pro",
        ".sdb",
        ".sys",
        ".wea",
    },
    "macroflo": {".mfl", ".mfo"},
    "suncast": {".gsk", ".ini", ".shd"},
}
_ROOT_CRITICAL_NAMES = {"project content.db", "roomgroups.xml"}


def _load_json(path: Path, context: str) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigurationError("Invalid {}: {}".format(context, exc)) from exc
    if not isinstance(payload, dict):
        raise ConfigurationError("{} must be a JSON object".format(context))
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _case_key(variant: str, case_id: str) -> str:
    if case_id not in TEST_CASES.get(variant, ()):
        raise ConfigurationError(
            "Unknown SIA 4010 case: {}/{}".format(variant, case_id)
        )
    return "{}/{}".format(variant, case_id)


def critical_project_files(project_path: Union[str, Path]) -> Tuple[Path, ...]:
    """Return the deterministic input files included in a template signature."""

    root = Path(project_path)
    if not root.is_dir():
        raise ConfigurationError(
            "VE template project directory does not exist: {}".format(root)
        )
    selected = []
    for path in root.iterdir():
        if not path.is_file():
            continue
        if (
            path.name.lower() in _ROOT_CRITICAL_NAMES
            or path.suffix.lower() in _ROOT_CRITICAL_SUFFIXES
        ):
            selected.append(path)
    for directory_name, suffixes in _SUBDIRECTORY_CRITICAL_SUFFIXES.items():
        directory = root / directory_name
        if not directory.is_dir():
            continue
        selected.extend(
            path
            for path in directory.rglob("*")
            if path.is_file() and path.suffix.lower() in suffixes
        )
    selected = sorted(set(selected), key=lambda item: item.relative_to(root).as_posix())
    mdl_files = [path for path in selected if path.suffix.lower() == ".mdl"]
    if not mdl_files:
        raise ConfigurationError(
            "VE template contains no root .mdl file: {}".format(root)
        )
    if not (root / "Project Content.db").is_file():
        raise ConfigurationError(
            "VE template contains no Project Content.db: {}".format(root)
        )
    return tuple(selected)


def project_signature(project_path: Union[str, Path]) -> Dict[str, Any]:
    """Return a stable checksum manifest for the template's model inputs."""

    root = Path(project_path).resolve()
    files = {
        path.relative_to(root).as_posix(): _sha256(path)
        for path in critical_project_files(root)
    }
    return {
        "algorithm": "sha256",
        "critical_file_count": len(files),
        "files": files,
        "template_signature_sha256": _canonical_sha256(files),
    }


@dataclass(frozen=True)
class TemplateRequirement:
    """Execution requirement for one official base test."""

    test_id: str
    strategy: str
    template_allowed: bool
    required_evidence: Tuple[str, ...]


@dataclass(frozen=True)
class TemplateBinding:
    """One reviewed project-template binding supplied by the operator."""

    template_id: str
    project_path: Path
    qualification_manifest: Path
    covered_cases: Tuple[str, ...]
    status: str


@dataclass(frozen=True)
class TemplateValidation:
    """Qualification outcome for one configured template binding."""

    status: str
    template_id: str
    issues: Tuple[str, ...]
    template_signature_sha256: str = ""

    @property
    def usable(self) -> bool:
        return self.status == "QUALIFIED_TEMPLATE_VERIFIED"


@dataclass(frozen=True)
class HybridCasePlan:
    """Chosen execution route for one exact SIA 4010 case."""

    variant: str
    case_id: str
    base_test_id: str
    route: str
    status: str
    template_id: str
    blocker_code: str
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HybridReadinessReceipt:
    """Auditable hybrid-plan result for all exact cases."""

    status: str
    report_path: Path
    cases: Tuple[HybridCasePlan, ...]
    direct_cases: int
    template_cases: int
    blocked_cases: int


@dataclass(frozen=True)
class TemplateInstantiationReceipt:
    """Result of one immutable-template copy into a disposable project."""

    status: str
    variant: str
    case_id: str
    template_id: str
    source_project: Path
    disposable_project: Path
    template_signature_sha256: str
    report_path: Path


def load_requirements(path: Union[str, Path]) -> Dict[str, TemplateRequirement]:
    """Load and validate the immutable template-strategy contract."""

    source = Path(path)
    payload = _load_json(source, "SIA 4010 template requirements")
    if str(payload.get("schema_version")) != "1.0":
        raise ConfigurationError("Unsupported template-requirement schema")
    families = payload.get("families")
    if not isinstance(families, dict) or set(families) != set("1234567"):
        raise ConfigurationError(
            "Template requirements must define exact families 1 through 7"
        )
    result: Dict[str, TemplateRequirement] = {}
    for test_id, row in families.items():
        if not isinstance(row, dict):
            raise ConfigurationError(
                "Template requirement {} must be an object".format(test_id)
            )
        evidence = row.get("required_evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ConfigurationError(
                "Template requirement {} has no evidence list".format(test_id)
            )
        result[test_id] = TemplateRequirement(
            test_id=test_id,
            strategy=str(row.get("strategy") or "").strip(),
            template_allowed=bool(row.get("template_allowed")),
            required_evidence=tuple(str(item) for item in evidence),
        )
        if not result[test_id].strategy:
            raise ConfigurationError(
                "Template requirement {} has no strategy".format(test_id)
            )
    return result


def load_bindings(path: Union[str, Path]) -> Tuple[TemplateBinding, ...]:
    """Load optional project-local bindings; a missing file means no templates."""

    source = Path(path)
    if not source.is_file():
        return ()
    payload = _load_json(source, "SIA 4010 template bindings")
    if str(payload.get("schema_version")) != "1.0":
        raise ConfigurationError("Unsupported template-binding schema")
    rows = payload.get("bindings")
    if not isinstance(rows, list):
        raise ConfigurationError("Template bindings must contain a bindings list")
    bindings = []
    identifiers = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ConfigurationError("Each template binding must be an object")
        template_id = str(row.get("template_id") or "").strip()
        if not template_id or template_id in identifiers:
            raise ConfigurationError(
                "Template IDs must be non-empty and unique: {!r}".format(template_id)
            )
        identifiers.add(template_id)
        cases = tuple(str(item) for item in row.get("covered_cases", ()))
        for item in cases:
            try:
                variant, case_id = item.split("/", 1)
            except ValueError as exc:
                raise ConfigurationError(
                    "Invalid covered-case key: {!r}".format(item)
                ) from exc
            _case_key(variant, case_id)
        bindings.append(
            TemplateBinding(
                template_id=template_id,
                project_path=Path(str(row.get("project_path") or "")),
                qualification_manifest=Path(
                    str(row.get("qualification_manifest") or "")
                ),
                covered_cases=cases,
                status=str(row.get("status") or "").upper(),
            )
        )
    return tuple(bindings)


def validate_binding(
    binding: TemplateBinding,
    requirement: TemplateRequirement,
) -> TemplateValidation:
    """Verify path, human review, evidence coverage and current checksums."""

    issues = []
    if not requirement.template_allowed:
        issues.append("TEMPLATE_NOT_ALLOWED_FOR_TEST_{}".format(requirement.test_id))
    if binding.status != QUALIFIED:
        issues.append("BINDING_STATUS_NOT_QUALIFIED")
    if not binding.project_path.is_dir():
        issues.append("TEMPLATE_PROJECT_NOT_FOUND")
    if not binding.qualification_manifest.is_file():
        issues.append("QUALIFICATION_MANIFEST_NOT_FOUND")
    if issues:
        return TemplateValidation("TEMPLATE_BLOCKED", binding.template_id, tuple(issues))
    qualification = _load_json(
        binding.qualification_manifest,
        "template qualification manifest",
    )
    if str(qualification.get("schema_version")) != "1.0":
        issues.append("QUALIFICATION_SCHEMA_UNSUPPORTED")
    if str(qualification.get("status") or "").upper() != QUALIFIED:
        issues.append("QUALIFICATION_NOT_APPROVED")
    if not str(qualification.get("reviewer") or "").strip():
        issues.append("QUALIFICATION_REVIEWER_MISSING")
    if not str(qualification.get("reviewed_at") or "").strip():
        issues.append("QUALIFICATION_DATE_MISSING")
    if not str(qualification.get("ve_version") or "").strip():
        issues.append("VE_VERSION_MISSING")
    evidence = set(str(item) for item in qualification.get("evidence", ()))
    missing_evidence = sorted(set(requirement.required_evidence) - evidence)
    issues.extend("MISSING_EVIDENCE:{}".format(item) for item in missing_evidence)
    qualified_cases = set(str(item) for item in qualification.get("covered_cases", ()))
    if not set(binding.covered_cases) <= qualified_cases:
        issues.append("BINDING_CASES_NOT_COVERED_BY_QUALIFICATION")
    signature = project_signature(binding.project_path)
    expected = str(qualification.get("template_signature_sha256") or "").lower()
    actual = str(signature["template_signature_sha256"]).lower()
    if not expected:
        issues.append("QUALIFIED_SIGNATURE_MISSING")
    elif expected != actual:
        issues.append("TEMPLATE_SIGNATURE_MISMATCH")
    return TemplateValidation(
        "QUALIFIED_TEMPLATE_VERIFIED" if not issues else "TEMPLATE_BLOCKED",
        binding.template_id,
        tuple(issues),
        actual,
    )


def _find_template(
    case_key: str,
    requirement: TemplateRequirement,
    bindings: Iterable[TemplateBinding],
) -> Tuple[Optional[TemplateBinding], Optional[TemplateValidation]]:
    candidates = tuple(item for item in bindings if case_key in item.covered_cases)
    if len(candidates) > 1:
        raise ConfigurationError(
            "Multiple template bindings cover {}: {}".format(
                case_key,
                [item.template_id for item in candidates],
            )
        )
    if not candidates:
        return None, None
    validation = validate_binding(candidates[0], requirement)
    return candidates[0], validation


def build_hybrid_case_plans(
    requirements: Mapping[str, TemplateRequirement],
    bindings: Iterable[TemplateBinding],
) -> Tuple[HybridCasePlan, ...]:
    """Choose direct generation or a checksum-qualified template per case."""

    plans = []
    binding_rows = tuple(bindings)
    for variant, case_ids in TEST_CASES.items():
        for case_id in case_ids:
            capability = get_case_capability(variant, case_id)
            requirement = requirements[capability.base_test_id]
            if capability.mutation_supported:
                plans.append(
                    HybridCasePlan(
                        variant,
                        case_id,
                        capability.base_test_id,
                        "DIRECT_VESCRIPT",
                        "READY_FOR_GUARDED_MUTATION",
                        "",
                        "",
                        capability.generator_id,
                    )
                )
                continue
            if capability.runtime_qualification_supported:
                plans.append(
                    HybridCasePlan(
                        variant,
                        case_id,
                        capability.base_test_id,
                        "DIRECT_VESCRIPT",
                        "READY_FOR_REAL_VE_QUALIFICATION",
                        "",
                        capability.blocker_code,
                        capability.blocker_detail,
                    )
                )
                continue
            if variant == "test_1" and case_id == "1E":
                plans.append(
                    HybridCasePlan(
                        variant,
                        case_id,
                        capability.base_test_id,
                        "DIAGNOSTIC_ONLY",
                        "SOURCE_PREPARATION_ONLY",
                        "",
                        capability.blocker_code,
                        "Case 1E is diagnostic and is not one of the six ISO Test 1 cases.",
                    )
                )
                continue
            key = _case_key(variant, case_id)
            binding, validation = _find_template(key, requirement, binding_rows)
            if binding is not None and validation is not None and validation.usable:
                plans.append(
                    HybridCasePlan(
                        variant,
                        case_id,
                        capability.base_test_id,
                        "QUALIFIED_VE_TEMPLATE",
                        "READY_FROM_QUALIFIED_TEMPLATE",
                        binding.template_id,
                        "",
                        validation.template_signature_sha256,
                    )
                )
            else:
                issues = (
                    validation.issues
                    if validation is not None
                    else ("NO_QUALIFIED_TEMPLATE_BINDING",)
                )
                plans.append(
                    HybridCasePlan(
                        variant,
                        case_id,
                        capability.base_test_id,
                        "QUALIFIED_VE_TEMPLATE",
                        "BLOCKED_TEMPLATE_REQUIRED",
                        binding.template_id if binding is not None else "",
                        capability.blocker_code,
                        "; ".join(issues),
                    )
                )
    return tuple(plans)


def write_hybrid_readiness(
    project_root: Union[str, Path],
    repository_root: Union[str, Path],
    *,
    bindings_path: Optional[Union[str, Path]] = None,
) -> HybridReadinessReceipt:
    """Write the active project's complete direct/template execution plan."""

    project = Path(project_root)
    repository = Path(repository_root)
    requirement_path = repository / "config" / "sia4010_template_requirements.json"
    selected_bindings_path = (
        Path(bindings_path)
        if bindings_path is not None
        else project / TEMPLATE_BINDINGS_FILENAME
    )
    requirements = load_requirements(requirement_path)
    bindings = load_bindings(selected_bindings_path)
    cases = build_hybrid_case_plans(requirements, bindings)
    direct = sum(item.route == "DIRECT_VESCRIPT" for item in cases)
    templated = sum(item.status == "READY_FROM_QUALIFIED_TEMPLATE" for item in cases)
    blocked = sum(item.status == "BLOCKED_TEMPLATE_REQUIRED" for item in cases)
    status = (
        "READY_FOR_CASE_EXECUTION"
        if blocked == 0
        else "HYBRID_EXECUTION_BLOCKED"
    )
    report_path = (
        project
        / "sia4010_artifacts"
        / "templates"
        / "sia4010_hybrid_readiness.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "requirements": str(requirement_path),
        "bindings": str(selected_bindings_path),
        "summary": {
            "exact_cases": len(cases),
            "direct_cases": direct,
            "qualified_template_cases": templated,
            "blocked_template_cases": blocked,
        },
        "cases": [item.to_dict() for item in cases],
        "claim_guardrail": (
            "Readiness proves only that an execution route is available. "
            "Official APS comparison and SIA review remain separate gates."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return HybridReadinessReceipt(
        status=status,
        report_path=report_path,
        cases=cases,
        direct_cases=direct,
        template_cases=templated,
        blocked_cases=blocked,
    )


def instantiate_qualified_case(
    project_root: Union[str, Path],
    repository_root: Union[str, Path],
    variant: str,
    case_id: str,
    destination_parent: Union[str, Path],
) -> TemplateInstantiationReceipt:
    """Copy one verified template to a new disposable VE project directory.

    The source is hashed before and after the copy.  The destination must not
    exist, so no model can be overwritten or silently resumed from stale data.
    The function copies files only; opening the new project and every VE
    mutation remain explicit operator actions.
    """

    project = Path(project_root).resolve()
    repository = Path(repository_root).resolve()
    parent = Path(destination_parent).resolve()
    if not parent.is_dir():
        raise ConfigurationError(
            "Disposable-project parent does not exist: {}".format(parent)
        )
    capability = get_case_capability(variant, case_id)
    requirements = load_requirements(
        repository / "config" / "sia4010_template_requirements.json"
    )
    requirement = requirements[capability.base_test_id]
    bindings = load_bindings(project / TEMPLATE_BINDINGS_FILENAME)
    key = _case_key(variant, case_id)
    binding, validation = _find_template(key, requirement, bindings)
    if binding is None or validation is None or not validation.usable:
        issues = (
            validation.issues
            if validation is not None
            else ("NO_QUALIFIED_TEMPLATE_BINDING",)
        )
        raise ConfigurationError(
            "No usable qualified template for {}: {}".format(
                key,
                "; ".join(issues),
            )
        )
    source = binding.project_path.resolve()
    safe_variant = variant.upper().replace("/", "_")
    safe_case = case_id.upper().replace("/", "_")
    target = parent / "SIA4010_{}_{}_DISPOSABLE".format(
        safe_variant,
        safe_case,
    )
    if target.exists():
        raise ConfigurationError(
            "Disposable-project target already exists: {}".format(target)
        )
    if source == parent or source in parent.parents or source in target.parents:
        raise ConfigurationError(
            "Disposable target must be outside the qualified template: {}".format(
                source
            )
        )
    before = project_signature(source)
    shutil.copytree(source, target, copy_function=shutil.copy2)
    after_source = project_signature(source)
    copied = project_signature(target)
    signature = str(before["template_signature_sha256"])
    if after_source["template_signature_sha256"] != signature:
        raise ConfigurationError(
            "Qualified template changed while it was being copied"
        )
    if copied["template_signature_sha256"] != signature:
        raise ConfigurationError(
            "Disposable copy does not match the qualified template signature"
        )
    report_path = (
        target
        / "sia4010_artifacts"
        / "templates"
        / "template_instantiation.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "status": "DISPOSABLE_TEMPLATE_COPY_VERIFIED",
        "variant": variant,
        "case_id": case_id,
        "template_id": binding.template_id,
        "source_project": str(source),
        "disposable_project": str(target),
        "template_signature_sha256": signature,
        "qualification_manifest": str(binding.qualification_manifest),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "next_action": (
            "Open the copied .mdl in VE, run the exact case binding/read-back "
            "workflow, then ApacheSim and qualified APS evaluation."
        ),
        "claim_guardrail": (
            "A verified template copy is not a passing result and does not "
            "grant SIA validation."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return TemplateInstantiationReceipt(
        status=payload["status"],
        variant=variant,
        case_id=case_id,
        template_id=binding.template_id,
        source_project=source,
        disposable_project=target,
        template_signature_sha256=signature,
        report_path=report_path,
    )


def capture_template_candidate(
    project_root: Union[str, Path],
    covered_cases: Iterable[str],
    *,
    ve_version: str,
    operator: str,
) -> Path:
    """Capture an active project signature without claiming qualification."""

    project = Path(project_root).resolve()
    normalized_cases = []
    for item in covered_cases:
        value = str(item).strip()
        variant, case_id = value.split("/", 1)
        normalized_cases.append(_case_key(variant, case_id))
    if not normalized_cases:
        raise ConfigurationError("At least one covered case is required")
    signature = project_signature(project)
    output = (
        project
        / "sia4010_artifacts"
        / "templates"
        / "sia4010_template_candidate.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "status": "CANDIDATE_REQUIRES_INDEPENDENT_REVIEW",
        "project_path": str(project),
        "covered_cases": sorted(set(normalized_cases)),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "captured_by": str(operator).strip(),
        "ve_version": str(ve_version).strip(),
        **signature,
        "required_next_action": (
            "Review geometry, constructions, controls, HVAC/plant topology, "
            "weather and required outputs against the official sources. Then "
            "create a separate qualification manifest with status QUALIFIED."
        ),
        "claim_guardrail": "A captured candidate is not a qualified template.",
    }
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output
