"""Read-only capability probe for VE mutation policy.

The probe never mutates a VE project.  It inspects an active ``iesve``
runtime and its ``VEProject`` / ``VECdbProject`` handles to answer, for each
capability the mutation policy relies on:

* is the attribute exposed?
* is it callable?
* for signature-sensitive members, do the documented signature variants
  resolve on a benign lookup?

The output is a structured ``ProbeReport`` with one ``CapabilityFinding`` per
row and a global status derived from the worst finding.  This is the
``READY_FOR_REAL_VE_QUALIFICATION`` deliverable: it proves that the policy's
assumptions about the runtime hold, without touching model state.

The module is pure Python so it can be exercised with a fake ``iesve`` in CI.
Launchers only add a thin ``import iesve`` shell.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from .ve_construction_binder import BindStatus, ConstructionBinder
from .ve_field_policy import ReadbackStatus


class ProbeStatus(Enum):
    """Per-capability outcome."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass(frozen=True)
class CapabilityFinding:
    """One probe row."""

    capability_id: str
    status: ProbeStatus
    detail: str
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProbeReport:
    """Aggregated probe outcome."""

    generated_at_utc: str
    project_id: Optional[str]
    findings: Tuple[CapabilityFinding, ...]

    @property
    def overall(self) -> ProbeStatus:
        if any(f.status is ProbeStatus.FAIL for f in self.findings):
            return ProbeStatus.FAIL
        if any(f.status is ProbeStatus.WARNING for f in self.findings):
            return ProbeStatus.WARNING
        return ProbeStatus.PASS

    def to_json(self) -> Dict[str, Any]:
        return {
            "schema_version": "1.0",
            "generated_at_utc": self.generated_at_utc,
            "project_id": self.project_id,
            "overall": self.overall.value,
            "status_reference": (
                "READY_FOR_REAL_VE_QUALIFICATION when overall is PASS or "
                "WARNING; requires operator review before any mutation when FAIL"
            ),
            "findings": [
                {
                    "capability_id": f.capability_id,
                    "status": f.status.value,
                    "detail": f.detail,
                    "evidence": f.evidence,
                }
                for f in self.findings
            ],
        }


# ---------------------------------------------------------------------------
# Individual probe checks
# ---------------------------------------------------------------------------


def _has_callable(obj: Any, name: str) -> Tuple[bool, str]:
    """Return ``(is_callable, detail)`` for one attribute lookup."""

    if obj is None:
        return False, "target object is None"
    if not hasattr(obj, name):
        return False, "attribute '{}' missing".format(name)
    member = getattr(obj, name)
    if not callable(member):
        return False, "'{}' is present but not callable".format(name)
    return True, "callable"


def _probe_attribute(
    target: Any,
    capability_id: str,
    attribute: str,
    *,
    kind: str = "callable",
    required: bool = True,
) -> CapabilityFinding:
    """Uniform helper for the attribute-presence checks."""

    if target is None:
        return CapabilityFinding(
            capability_id=capability_id,
            status=ProbeStatus.FAIL if required else ProbeStatus.WARNING,
            detail="No target object bound",
            evidence={"target": None, "attribute": attribute, "kind": kind},
        )
    if kind == "callable":
        ok, detail = _has_callable(target, attribute)
    else:
        ok = hasattr(target, attribute)
        detail = "attribute present" if ok else "attribute missing"
    if ok:
        return CapabilityFinding(
            capability_id=capability_id,
            status=ProbeStatus.PASS,
            detail=detail,
            evidence={"attribute": attribute, "kind": kind},
        )
    return CapabilityFinding(
        capability_id=capability_id,
        status=ProbeStatus.FAIL if required else ProbeStatus.WARNING,
        detail=detail,
        evidence={"attribute": attribute, "kind": kind, "required": required},
    )


def _probe_construction_binder(cdb_project: Any, iesve_module: Any) -> CapabilityFinding:
    """Confirm the str -> VECdbConstruction resolver can dispatch."""

    if cdb_project is None or not hasattr(cdb_project, "get_construction"):
        return CapabilityFinding(
            capability_id="CDB_CONSTRUCTION_LOOKUP",
            status=ProbeStatus.FAIL,
            detail="cdb_project.get_construction unavailable",
            evidence={},
        )
    binder = ConstructionBinder(iesve_module=iesve_module, cdb_project=cdb_project)
    # We probe with a deliberately implausible identifier so no real
    # construction is created or fetched.  We only care that dispatch runs
    # far enough to hit both documented signatures (or return NOT_FOUND).
    result = binder.resolve("__ve_mutation_policy_probe_absent_construction__")
    if result.status is BindStatus.RESOLVED:
        # Extremely unlikely; still safe -- we did not mutate anything.
        return CapabilityFinding(
            capability_id="CDB_CONSTRUCTION_LOOKUP",
            status=ProbeStatus.PASS,
            detail="Binder unexpectedly resolved the probe id; dispatch works.",
            evidence={"signatures_tried": list(result.signatures_tried)},
        )
    if result.status is BindStatus.NOT_FOUND:
        return CapabilityFinding(
            capability_id="CDB_CONSTRUCTION_LOOKUP",
            status=ProbeStatus.PASS,
            detail="Binder dispatched documented signatures without crashing.",
            evidence={
                "signatures_tried": list(result.signatures_tried),
                "last_exception_repr": result.last_exception_repr,
            },
        )
    return CapabilityFinding(
        capability_id="CDB_CONSTRUCTION_LOOKUP",
        status=ProbeStatus.FAIL,
        detail="Binder cannot dispatch construction lookup.",
        evidence={
            "signatures_tried": list(result.signatures_tried),
            "last_exception_repr": result.last_exception_repr,
        },
    )


# ---------------------------------------------------------------------------
# Probe orchestration
# ---------------------------------------------------------------------------


def _iso_now_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def run_probe(
    iesve_module: Any,
    project: Any,
    cdb_project: Any,
    *,
    project_id: Optional[str] = None,
    clock: Optional[Callable[[], str]] = None,
) -> ProbeReport:
    """Run the read-only probe against the currently active VE handles.

    None of the checks mutate state; every call is a read-only ``hasattr``,
    ``callable`` or benign lookup.
    """

    findings: List[CapabilityFinding] = []
    now = (clock or _iso_now_utc)()

    findings.append(
        _probe_attribute(project, "PROJECT_ROOMS", "rooms", kind="attribute")
    )
    findings.append(_probe_attribute(project, "PROJECT_SAVE_PROFILES", "save_profiles"))
    findings.append(_probe_attribute(project, "PROJECT_CREATE_PROFILE", "create_profile"))
    findings.append(
        _probe_attribute(project, "PROJECT_CREATE_CASUAL_GAIN", "create_casual_gain")
    )
    findings.append(
        _probe_attribute(project, "PROJECT_CREATE_AIR_EXCHANGE", "create_air_exchange")
    )
    findings.append(
        _probe_attribute(project, "PROJECT_CREATE_APACHE_SYSTEM", "create_apache_system")
    )
    findings.append(
        _probe_attribute(project, "PROJECT_CREATE_THERMAL_TEMPLATE", "create_thermal_template")
    )

    findings.append(_probe_attribute(cdb_project, "CDB_UVALUE_TYPES", "uvalue_types", kind="attribute"))
    findings.append(_probe_attribute(cdb_project, "CDB_CREATE_MATERIAL", "create_material"))
    findings.append(
        _probe_attribute(cdb_project, "CDB_CREATE_CONSTRUCTION", "create_construction")
    )
    findings.append(_probe_construction_binder(cdb_project, iesve_module))

    findings.append(
        _probe_attribute(
            iesve_module,
            "IESVE_CONSTRUCTION_CLASS_ENUM",
            "construction_class",
            kind="attribute",
            required=False,
        )
    )
    findings.append(
        _probe_attribute(
            iesve_module,
            "IESVE_ELEMENT_CATEGORIES_ENUM",
            "element_categories",
            kind="attribute",
            required=False,
        )
    )
    findings.append(
        _probe_attribute(
            iesve_module,
            "IESVE_MATERIAL_CATEGORIES_ENUM",
            "material_categories",
            kind="attribute",
            required=False,
        )
    )

    return ProbeReport(
        generated_at_utc=now,
        project_id=project_id,
        findings=tuple(findings),
    )


def write_probe_report(report: ProbeReport, output_dir: str) -> str:
    """Persist ``report`` as JSON under ``output_dir``; return the written path."""

    os.makedirs(output_dir, exist_ok=True)
    stamp = report.generated_at_utc.replace(":", "-")
    path = os.path.join(output_dir, "ve_mutation_policy_probe_{}.json".format(stamp))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report.to_json(), handle, ensure_ascii=False, indent=2, sort_keys=True)
    return path


__all__ = [
    "ProbeStatus",
    "CapabilityFinding",
    "ProbeReport",
    "run_probe",
    "write_probe_report",
]
