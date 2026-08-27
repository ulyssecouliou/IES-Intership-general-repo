"""Derive the reported compliance verdict for the company SIA report.

The verdict is deliberately conservative and fail-closed, because the report
carries a company signature:

- a per-domain status is ``COMPLIANT`` only when the domain was actually
  evaluated and produced no critical or high finding;
- any critical or high determined finding makes the overall ``NOT_COMPLIANT``;
- the overall SIA 380/2 statement is decided on the reviewed global
  project/reference comparison (SIA 380/2:2022 §7.2.5.2): with that comparison
  reviewed and satisfied and no determined failure, the statement is
  ``COMPLIANT`` and any unverifiable component diagnostic that is only a Table 2
  reference input is reported as a visible reserve in ``outstanding`` rather than
  downgrading the verdict. The AUTONOMOUS SIA 380/2:2022 §7.1 requirements are
  the exception (norm-analyst A4): incomplete ventilation (§7.1.1), unverified
  solar-protection control (§7.1.2.2-5) and a DETERMINED summer-overheating
  failure (§7.1.2.1 -> SIA 180) are essential gates, not reserves;
- without the decisive comparison the statement stays ``NOT_DETERMINED`` -
  never silently compliant.

Treating component diagnostics as reserves (not blockers) once the decisive
gate is met is a product decision (2026-08-19) PENDING norm-analyst /
qa-auditor sign-off. The SIA 4010 statement reports the validation-class state
of the toolchain and never reads as an official validation: that requires the
official test results plus SIA sub-commission attestation.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

COMPLIANT = "COMPLIANT"
NOT_COMPLIANT = "NOT_COMPLIANT"
NOT_DETERMINED = "NOT_DETERMINED"

# Reported SIA 380/2 domains, in reading order, mapped to the alert category the
# checker emits for them.
DOMAINS: Tuple[Tuple[str, str], ...] = (
    ("envelope", "Envelope"),
    ("openings", "Openings"),
    ("ventilation", "Ventilation"),
    ("gains", "Gains"),
    ("setpoints", "Setpoints"),
    ("hvac", "HVAC"),
    # SIA 380/2:2022 summer thermal protection (dynamic comfort). A DETERMINED
    # over-heating failure (SIA3802_SUMMER_COMFORT_DYNAMIC, HIGH) must block the
    # verdict; a not-checkable comfort run (missing full-year APS / weather
    # mismatch) carries an indeterminate marker and stays a reserve, never a
    # false failure. Before this entry the HIGH rule was emitted but ignored by
    # the verdict (audit A3, 2026-08-20).
    ("dynamic", "Dynamic Method"),
)

_BLOCKING_SEVERITIES = {"CRITICAL", "HIGH"}
_INDETERMINATE_RULE_MARKERS = (
    "MISSING",
    "NOT_CHECKABLE",
    "PLACEHOLDER",
    "UNAVAILABLE",
    "RULE_EXECUTION_ERROR",
)

# Rules that correspond to documented structural limitations of the toolchain
# (NOT_AVAILABLE capability or explicitly informational diagnostics).  These
# carry indeterminate markers in their name but must NOT downgrade a domain to
# NOT_DETERMINED: the tool structurally cannot check them, so they are reported
# as visible reserves rather than evidence gaps.
# SIA 380/2:2022 §5.3.4-5 design-day: no dedicated workflow exists.
# Table 7 EER+: VE cannot decompose post-cooling auxiliary power shares.
# Table 1 cooling-need screening: explicitly informational, "not an autonomous
# compliance verdict" per the checker docstring.
# Cooling generator class: VE NCM chiller-type field is UK-specific and
# typically unpopulated on Swiss models; EER/SEER values are read directly.
# SIA 2024 mapping: requires licensed SIA 2024 standard, external to VE.
# SIA 387/4 lighting control: requires licensed SIA 387/4, external to VE.
_KNOWN_LIMITATION_RULES = frozenset(
    {
        "SIA3802_HEATING_DESIGN_POWER_NOT_CHECKABLE",
        "SIA3802_COOLING_DESIGN_POWER_NOT_CHECKABLE",
        "SIA3802_COOLING_EERPLUS_NOT_CHECKABLE",
        "SIA3802_COOLING_NEED_SCREENING_NOT_CHECKABLE",
        "SIA3802_COOLING_GENERATOR_CLASS_MISSING",
        "SIA3802_SIA2024_MAPPING_MISSING",
        "SIA3802_LIGHTING_CONTROL_TYPE_MISSING",
    }
)


@dataclass(frozen=True)
class DomainVerdict:
    """Reported status of one SIA 380/2 domain."""

    domain: str
    status: str
    blocking_count: int
    missing_count: int
    advisory_count: int
    reason: str
    limitation_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Return the domain verdict as serializable data."""

        return {
            "domain": self.domain,
            "status": self.status,
            "blocking_count": self.blocking_count,
            "missing_count": self.missing_count,
            "advisory_count": self.advisory_count,
            "limitation_count": self.limitation_count,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ComplianceVerdict:
    """Overall reported verdict for one analysed VE model."""

    sia3802_status: str
    sia3802_reason: str
    sia4010_status: str
    sia4010_reason: str
    domains: Tuple[DomainVerdict, ...] = ()
    blocking_total: int = 0
    missing_total: int = 0
    advisory_total: int = 0
    outstanding: Tuple[str, ...] = ()

    @property
    def overall_status(self) -> str:
        """Return the combined status, taking the least favourable of the two."""

        for status in (NOT_COMPLIANT, NOT_DETERMINED):
            if status in (self.sia3802_status, self.sia4010_status):
                return status
        return COMPLIANT

    def to_dict(self) -> Dict[str, Any]:
        """Return the verdict as serializable data."""

        return {
            "overall_status": self.overall_status,
            "sia3802_status": self.sia3802_status,
            "sia3802_reason": self.sia3802_reason,
            "sia4010_status": self.sia4010_status,
            "sia4010_reason": self.sia4010_reason,
            "domains": [domain.to_dict() for domain in self.domains],
            "blocking_total": self.blocking_total,
            "missing_total": self.missing_total,
            "advisory_total": self.advisory_total,
            "outstanding": list(self.outstanding),
        }


def _severity_name(alert: Any) -> str:
    """Return the upper-case severity name of one alert, however it is typed."""

    severity = getattr(alert, "severity", None)
    name = getattr(severity, "name", None) or getattr(severity, "value", None) or severity
    return str(name or "").upper()


def _category(alert: Any) -> str:
    """Return the alert category as a plain string."""

    return str(getattr(alert, "category", "") or "")


def _count_by_category(alerts: Sequence[Any]) -> Dict[str, Dict[str, int]]:
    """Count blocking, advisory and incomplete-evidence alerts by category."""

    counts: Dict[str, Dict[str, int]] = {}
    for alert in alerts or ():
        bucket = counts.setdefault(
            _category(alert),
            {"blocking": 0, "advisory": 0, "indeterminate": 0, "limitation": 0},
        )
        rule_name = str(getattr(alert, "rule", "") or "").upper()
        if rule_name in _KNOWN_LIMITATION_RULES:
            bucket["limitation"] += 1
        elif any(marker in rule_name for marker in _INDETERMINATE_RULE_MARKERS):
            bucket["indeterminate"] += 1
        elif _severity_name(alert) in _BLOCKING_SEVERITIES:
            bucket["blocking"] += 1
        else:
            bucket["advisory"] += 1
    return counts


def _domain_evaluated(sia3802_results: Dict[str, Any], key: str) -> bool:
    """Return whether the checker actually produced a result for one domain."""

    return isinstance(sia3802_results.get(key), dict)


def build_compliance_verdict(
    sia3802_results: Optional[Dict[str, Any]],
    sia4010_results: Optional[Dict[str, Any]],
    rooms_analysed: int,
) -> ComplianceVerdict:
    """Return the reported verdict, fail-closed on every missing input."""

    sia3802 = dict(sia3802_results or {})
    sia4010 = dict(sia4010_results or {})
    alerts = list(sia3802.get("alerts", []) or [])
    counts = _count_by_category(alerts)

    outstanding: List[str] = []
    domains: List[DomainVerdict] = []
    for key, category in DOMAINS:
        bucket = counts.get(
            category, {"blocking": 0, "advisory": 0, "indeterminate": 0, "limitation": 0}
        )
        blocking = bucket["blocking"]
        advisory = bucket["advisory"]
        indeterminate = bucket["indeterminate"]
        limitation = bucket["limitation"]
        if not rooms_analysed or not _domain_evaluated(sia3802, key):
            status = NOT_DETERMINED
            reason = "domain_not_evaluated"
        elif blocking:
            status = NOT_COMPLIANT
            reason = "blocking_findings"
        elif indeterminate:
            status = NOT_DETERMINED
            reason = "evidence_incomplete"
        elif limitation:
            status = COMPLIANT
            reason = "no_blocking_finding_with_limitations"
        else:
            status = COMPLIANT
            reason = "no_blocking_finding"
        domains.append(
            DomainVerdict(
                domain=key,
                status=status,
                blocking_count=blocking,
                missing_count=indeterminate,
                advisory_count=advisory,
                limitation_count=limitation,
                reason=reason,
            )
        )

    domain_evidence_incomplete = any(item.status == NOT_DETERMINED for item in domains)
    ventilation_evidence_incomplete = any(
        item.domain == "ventilation" and item.status == NOT_DETERMINED for item in domains
    )
    # Solar-protection control is an AUTONOMOUS SIA 380/2:2022 §7.1.2.2-5
    # requirement, not just a Table 2 reference input: the global comparison does
    # not subsume it (norm-analyst A4, 2026-08-20). So active solar protection
    # whose control is not documented (SIA3802_SOLAR_PROTECTION_CONTROL_MISSING /
    # _TYPE_MISSING, category "Openings") must force NOT_DETERMINED, exactly like
    # ventilation -- never a silent COMPLIANT-with-reserve. It fires only when
    # shading is actually present, so a model that legitimately needs none is not
    # over-blocked.
    solar_protection_control_incomplete = any(
        "SOLAR_PROTECTION_CONTROL" in str(getattr(alert, "rule", "") or "").upper()
        or "SOLAR_PROTECTION_TYPE" in str(getattr(alert, "rule", "") or "").upper()
        for alert in alerts
    )
    blocking_total = sum(item.blocking_count for item in domains)
    missing_total = sum(item.missing_count for item in domains)
    advisory_total = sum(item.advisory_count for item in domains)

    # SIA 380/2 decides on the reviewed global project/reference comparison.
    comparison = sia3802.get("global_reference_comparison", {}) or {}
    comparison_status = str(comparison.get("status") or "")
    comparison_available = comparison_status == "REVIEWED_RESULT_AVAILABLE"
    # A reviewed comparison whose figures contradict the reviewer's acceptance
    # (project value above the reference, against SIA 380/2:2022 7.2.5.2) is a
    # DETERMINED non-compliance, not missing evidence: acceptance never overrides
    # the numbers. The checker raises SIA3802_GLOBAL_REFERENCE_DISCREPANCY, but
    # its category sits outside the six scored domains, so the verdict must act on
    # the status explicitly here rather than through blocking_total.
    comparison_contradicts = comparison_status == "REVIEWED_RESULT_CONTRADICTS_ACCEPTANCE"
    # SIA 380/2:2022 §7.2.4 required electrical power is an AUTONOMOUS,
    # conditionally-blocking requirement (norm-analyst A5): a reviewed exceedance
    # with desirable/superfluous cooling is a determined NON-compliance; an
    # exceedance whose cooling-necessity class is unknown, or missing power, is
    # NOT_DETERMINED. The checker resolves this into a single verdict_status.
    electrical_power_status = str(
        (sia3802.get("electrical_power", {}) or {}).get("verdict_status") or ""
    )
    electrical_power_not_compliant = electrical_power_status == "NOT_COMPLIANT"
    electrical_power_incomplete = electrical_power_status == "NOT_DETERMINED"
    # SIA 380/2:2022 §7.2.5.2 decides overall compliance on the reviewed global
    # project/reference comparison; the per-component checks are diagnostics of
    # the reference-project inputs, not the verdict itself. So once the decisive
    # comparison is reviewed and satisfied and no DETERMINED failure exists, the
    # SIA 380/2 statement is COMPLIANT, and unverifiable component diagnostics
    # remain visible reserves (in `outstanding`) rather than downgrading the
    # verdict. A determined out-of-range finding (blocking_total) or a comparison
    # that contradicts its acceptance still fails closed. The autonomous §7.1
    # requirements (ventilation, solar-protection control, summer comfort) are
    # gated below, not treated as reserves.
    # Product decision 2026-08-19; norm-analyst A4 ruling 2026-08-20
    # (traceability/audit-A4-verdict-porte-decisive-sia3802.md); qa-auditor
    # traceability sign-off still pending before commercial use.
    if not rooms_analysed:
        sia3802_status, sia3802_reason = NOT_DETERMINED, "no_room_analysed"
    elif blocking_total:
        sia3802_status, sia3802_reason = NOT_COMPLIANT, "blocking_findings"
    elif comparison_contradicts:
        sia3802_status, sia3802_reason = (
            NOT_COMPLIANT,
            "global_comparison_contradicts_acceptance",
        )
    elif electrical_power_not_compliant:
        sia3802_status, sia3802_reason = (
            NOT_COMPLIANT,
            "electrical_power_exceeds_7_2_4_limit",
        )
    elif not comparison_available:
        sia3802_status, sia3802_reason = NOT_DETERMINED, "global_comparison_missing"
    elif ventilation_evidence_incomplete:
        sia3802_status, sia3802_reason = (
            NOT_DETERMINED,
            "ventilation_evidence_incomplete",
        )
    elif solar_protection_control_incomplete:
        sia3802_status, sia3802_reason = (
            NOT_DETERMINED,
            "solar_protection_control_incomplete",
        )
    elif electrical_power_incomplete:
        sia3802_status, sia3802_reason = (
            NOT_DETERMINED,
            "electrical_power_evidence_incomplete",
        )
    else:
        sia3802_status, sia3802_reason = COMPLIANT, (
            "comparison_reviewed_no_blocker_with_reserves"
            if domain_evidence_incomplete
            else "comparison_reviewed_no_blocker"
        )
    if not comparison_available:
        outstanding.append("global_reference_comparison")
    if domain_evidence_incomplete:
        outstanding.append("sia3802_domain_evidence")
    if ventilation_evidence_incomplete:
        outstanding.append("sia3802_ventilation_evidence")
    if solar_protection_control_incomplete:
        outstanding.append("sia3802_solar_protection_control")
    if electrical_power_not_compliant or electrical_power_incomplete:
        outstanding.append("sia3802_electrical_power")

    # SIA 4010 reports the toolchain's validation-class state. Official class
    # validation additionally requires SIA sub-commission attestation, so the
    # strongest status this report can carry is "results recorded".
    class_rows = sia4010.get("class_readiness", {}) or {}
    tests = sia4010.get("tests", {}) or {}
    blocked_tests = [
        name
        for name, data in tests.items()
        if str((data or {}).get("status", "")).upper()
        in {"NOT_CHECKABLE", "EVIDENCE_INCOMPLETE"}
    ]
    selected_class = str(sia4010.get("validation_class") or "").strip()
    if not tests:
        sia4010_status, sia4010_reason = NOT_DETERMINED, "no_official_test_state"
    elif any(
        str((data or {}).get("status", "")).upper() in {"FAIL", "FAILED"}
        for data in tests.values()
    ):
        sia4010_status, sia4010_reason = NOT_COMPLIANT, "official_test_failed"
    elif blocked_tests or not selected_class:
        sia4010_status, sia4010_reason = NOT_DETERMINED, "official_evidence_incomplete"
    else:
        sia4010_status, sia4010_reason = NOT_DETERMINED, "attestation_required"
    if blocked_tests:
        outstanding.append("sia4010_official_results")
    if not selected_class:
        outstanding.append("sia4010_validation_class")
    if not class_rows:
        outstanding.append("sia4010_class_readiness")

    return ComplianceVerdict(
        sia3802_status=sia3802_status,
        sia3802_reason=sia3802_reason,
        sia4010_status=sia4010_status,
        sia4010_reason=sia4010_reason,
        domains=tuple(domains),
        blocking_total=blocking_total,
        missing_total=missing_total,
        advisory_total=advisory_total,
        outstanding=tuple(dict.fromkeys(outstanding)),
    )
