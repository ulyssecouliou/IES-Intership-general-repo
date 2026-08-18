"""Interactive HTML client dashboard for the SIA compliance analysis.

This is a third client deliverable next to the Excel workbook and the PDF report
(``compliance_report_pdf.py``). It renders one self-contained HTML file that the
client opens in a browser: every SIA criterion, sortable, filterable by section
and status, each row expandable to its justification (SIA article, measured vs
reference, source, recommendation, and any ``[TO VERIFY]`` caveat).

It is populated from the REAL analysis output — the ``ComplianceVerdict``, the
``SIA_COMPLIANCE_REQUIREMENT_MATRIX`` and the checker alerts — never fabricated
data. It is pure Python (no ``iesve``) so it runs in CI and inside VEScripts
alike. Like the PDF, it is an evidence view, not a certificate: the scope block
and the fail-closed status mapping say so.

Visual language follows the IES / IESVE brand (iesve.com): IES navy ``#041b4a``
identification band, the VE blue accent ``#3daedc`` / ``#004387``, the IES slate
text and light-grey ground, an Aleo-style slab display paired with a Camphor-Pro
-style geometric sans (system-font fallbacks, since the artifact/report CSP does
not load web fonts).
"""

from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from swiss_sia.compliance_report_pdf import (
    normalize_report_scope,
    scoped_verdict_status,
    summarise_model,
)
from swiss_sia.compliance_verdict import (
    COMPLIANT,
    NOT_COMPLIANT,
    NOT_DETERMINED,
    _INDETERMINATE_RULE_MARKERS,
    build_compliance_verdict,
)
from swiss_sia.config import SIA_COMPLIANCE_REQUIREMENT_MATRIX
from swiss_sia.company_profile import CompanyProfile, load_company_profile
from swiss_sia.reference_model.sia4010.ui_translations import translate

# A "cannot compare" alert is, for the client's reading, undetermined evidence,
# not a determined failure. Mirror the verdict engine's indeterminate markers and
# extend with the checker's comparability markers for the display mapping only.
_UNVERIFIABLE_MARKERS = tuple(_INDETERMINATE_RULE_MARKERS) + (
    "NOT_COMPARABLE",
    "SOURCE_NOT_COMPARABLE",
)

# Blocking severities (a rule that ran and found a real violation).
_BLOCKING_SEVERITIES = {"CRITICAL", "HIGH"}

# Status vocabulary shared with the front-end. Never a PASS on missing evidence.
STATUS_CONFORME = "conforme"
STATUS_NON_CONFORME = "non_conforme"
STATUS_A_DETERMINER = "a_determiner"
STATUS_ECART = "ecart"
STATUS_NON_VERIFIABLE = "non_verifiable"

# Requirement-matrix domain -> dashboard section id. Every domain in
# SIA_COMPLIANCE_REQUIREMENT_MATRIX is mapped explicitly; an unmapped domain
# falls back to "cvc" (a neutral systems bucket) and NEVER to "global" — "global"
# is the single decisive-gate section and must not be polluted by stray domains.
_DOMAIN_TO_SECTION = {
    "Envelope": "enveloppe",
    "Openings": "ouvertures",
    "Solar protection": "ouvertures",
    "Ventilation": "ventilation",
    "Gains": "gains",
    "Setpoints": "consignes",
    "Heating": "cvc",
    "Cooling": "cvc",
    "HVAC": "cvc",
    "Dynamic results": "confort",
    "Summer Comfort": "confort",
    "Global Reference Comparison": "global",
}
_DEFAULT_SECTION = "cvc"

_SECTION_LABELS = {
    "fr": {
        "enveloppe": "Enveloppe", "ouvertures": "Ouvertures", "ventilation": "Ventilation",
        "gains": "Gains internes", "consignes": "Consignes", "cvc": "CVC / Génération",
        "confort": "Confort d'été", "global": "Comparaison globale", "sia4010": "SIA 4010",
    },
    "en": {
        "enveloppe": "Envelope", "ouvertures": "Openings", "ventilation": "Ventilation",
        "gains": "Internal gains", "consignes": "Setpoints", "cvc": "HVAC / Generation",
        "confort": "Summer comfort", "global": "Global comparison", "sia4010": "SIA 4010",
    },
}
_SECTION_ORDER = [
    "enveloppe", "ouvertures", "ventilation", "gains",
    "consignes", "cvc", "confort", "global", "sia4010",
]

_STATUS_LABELS = {
    "fr": {
        STATUS_CONFORME: "Conforme", STATUS_NON_CONFORME: "Non conforme",
        STATUS_A_DETERMINER: "À déterminer", STATUS_ECART: "Écart de référence",
        STATUS_NON_VERIFIABLE: "Non vérifiable",
    },
    "en": {
        STATUS_CONFORME: "Compliant", STATUS_NON_CONFORME: "Not compliant",
        STATUS_A_DETERMINER: "To be determined", STATUS_ECART: "Reference deviation",
        STATUS_NON_VERIFIABLE: "Not checkable",
    },
}

_UI = {
    "fr": {
        "title": "Analyse de conformité — modèle client",
        "subtitle": "Évaluation des preuves SIA 380/2 et readiness SIA 4010 · générée depuis IESVE",
        "product": "Navigateur de conformité SIA",
        "brand_sub": "IESVE · Analyse du modèle",
        "search": "Rechercher un critère, un article SIA…",
        "sort": "Trier", "reset": "Réinitialiser", "status": "Statut", "section": "Section",
        "all": "Toutes", "criterion": "Critère", "type": "Type",
        "measured_ref": "Mesuré / Référence", "decisif": "Décisif", "diagnostic": "Diagnostic",
        "article": "Article SIA", "interpretation": "Interprétation",
        "source": "Source / provenance", "recommendation": "Recommandation",
        "severity": "Sévérité", "precheck": "Indice de pré-vérification",
        "precheck_hint": "Indicateur automatique — <b>PAS</b> un taux de conformité. La conformité se décide sur la comparaison globale (§ 7.2.5.2).",
        "empty": "Aucun critère ne correspond aux filtres actifs.",
        "sort_section": "Section", "sort_status": "Statut", "sort_severity": "Sévérité",
        "sort_name": "Nom", "sort_type": "Type (décisif d'abord)",
        "theme": "Thème", "dark": "Sombre", "light": "Clair",
        "f_cabinet": "Cabinet", "f_project": "Projet", "f_model": "Modèle VE",
        "f_date": "Date d'analyse", "f_framework": "Référentiel", "f_climate": "Climat de calcul",
        "not_specified": "non spécifié",
        "scope": ("<b>Portée.</b> Cet écran restitue l'analyse automatique du modèle. Les critères "
                  "<b>Décisifs</b> pilotent le verdict ; les critères <b>Diagnostic</b> sont des écarts "
                  "aux entrées du projet de référence SIA 380/2, pas des échecs autonomes. Un critère "
                  "<b>Non vérifiable</b> ne devient jamais un succès : preuve manquante ≠ conformité. La "
                  "conformité globale SIA 380/2 se décide sur la comparaison relue projet/référence "
                  "(§ 7.2.5.2) ; la validation SIA 4010 exige les résultats officiels <b>et</b> "
                  "l'attestation de la sous-commission SIA (art. 4.6.2). Ce document ne constitue pas un certificat."),
        "sev_haute": "Haute", "sev_moyenne": "Moyenne", "sev_basse": "Basse",
    },
    "en": {
        "title": "Compliance analysis — client model",
        "subtitle": "SIA 380/2 evidence assessment and SIA 4010 readiness · generated from IESVE",
        "product": "SIA Compliance Navigator",
        "brand_sub": "IESVE · Model analysis",
        "search": "Search a criterion, an SIA article…",
        "sort": "Sort", "reset": "Reset", "status": "Status", "section": "Section",
        "all": "All", "criterion": "Criterion", "type": "Type",
        "measured_ref": "Measured / Reference", "decisif": "Decisive", "diagnostic": "Diagnostic",
        "article": "SIA article", "interpretation": "Interpretation",
        "source": "Source / provenance", "recommendation": "Recommendation",
        "severity": "Severity", "precheck": "Automated precheck index",
        "precheck_hint": "Automated indicator — <b>NOT</b> a compliance rate. Compliance is decided on the global comparison (§ 7.2.5.2).",
        "empty": "No criterion matches the active filters.",
        "sort_section": "Section", "sort_status": "Status", "sort_severity": "Severity",
        "sort_name": "Name", "sort_type": "Type (decisive first)",
        "theme": "Theme", "dark": "Dark", "light": "Light",
        "f_cabinet": "Office", "f_project": "Project", "f_model": "VE model",
        "f_date": "Analysis date", "f_framework": "Framework", "f_climate": "Calc. climate",
        "not_specified": "not specified",
        "scope": ("<b>Scope.</b> This view reflects the automated model analysis. <b>Decisive</b> criteria "
                  "drive the verdict; <b>Diagnostic</b> criteria are deviations from SIA 380/2 reference-project "
                  "inputs, not standalone failures. A <b>Not checkable</b> criterion never becomes a pass: "
                  "missing evidence is not compliance. Overall SIA 380/2 compliance is decided on the reviewed "
                  "project/reference comparison (§ 7.2.5.2); SIA 4010 validation requires the official results "
                  "<b>and</b> SIA sub-commission attestation (art. 4.6.2). This is not a certificate."),
        "sev_haute": "High", "sev_moyenne": "Medium", "sev_basse": "Low",
    },
}


def _lang(language: str) -> str:
    code = (language or "en").strip().lower()[:2]
    return code if code in _UI else "en"


def _sev_name(alert: Any) -> str:
    severity = getattr(alert, "severity", None)
    name = getattr(severity, "name", None) or getattr(severity, "value", None) or severity
    return str(name or "").upper()


def _sev_bucket(sev_name: str) -> str:
    if sev_name in ("CRITICAL", "HIGH"):
        return "haute"
    if sev_name in ("MEDIUM",):
        return "moyenne"
    return "basse"


def _num(value: Any) -> Optional[str]:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    text = ("%.3f" % f).rstrip("0").rstrip(".")
    return text or "0"


def _reference_text(entry: Dict[str, Any]) -> str:
    limit = _num(entry.get("limit"))
    target = _num(entry.get("target"))
    unit = str(entry.get("unit") or "").strip()
    if limit is not None:
        return "{}{}".format(limit, (" " + unit) if unit and unit != "-" else "")
    if target is not None:
        return "{}{}".format(target, (" " + unit) if unit and unit != "-" else "")
    return "—"


def _matching_alerts(rule: str, alerts: Sequence[Any]) -> List[Any]:
    """Alerts whose rule matches an implemented_rule.

    An implemented_rule can list several rules separated by ``/`` (e.g. the solar
    protection requirement); match against any of them.
    """
    if not rule:
        return []
    candidates = [r.strip() for r in str(rule).split("/") if r.strip()]
    hits = []
    for alert in alerts or ():
        arule = str(getattr(alert, "rule", "") or "")
        for cand in candidates:
            if arule == cand or arule.startswith(cand + "_") or cand in arule:
                hits.append(alert)
                break
    return hits


def _classify(entry: Dict[str, Any], alerts: Sequence[Any]) -> Dict[str, Any]:
    """Map one requirement matrix entry + its alerts to a dashboard criterion.

    Fail-closed: a not-implemented requirement, or one whose evidence is missing
    or not comparable, is Non vérifiable — never Conforme.
    """
    rule = entry.get("implemented_rule") or ""
    automation = str(entry.get("automation") or "").upper()
    hits = _matching_alerts(rule, alerts)

    status = STATUS_CONFORME
    severity = "basse"
    description = str(entry.get("next_action") or entry.get("criterion") or "")
    recommendation = str(entry.get("next_action") or "")

    if automation in ("NOT_IMPLEMENTED",):
        status = STATUS_NON_VERIFIABLE
        description = "Ce critère n'est pas encore implémenté ; aucun verdict automatique n'est produit."
    elif hits:
        # Take the most severe / most telling alert for the display.
        def _rank(a):
            r = str(getattr(a, "rule", "") or "").upper()
            unverifiable = any(m in r for m in _UNVERIFIABLE_MARKERS)
            blocking = _sev_name(a) in _BLOCKING_SEVERITIES and not unverifiable
            # unverifiable first (most conservative), then blocking, then advisory
            return (0 if unverifiable else (1 if blocking else 2))
        lead = sorted(hits, key=_rank)[0]
        lead_rule = str(getattr(lead, "rule", "") or "").upper()
        description = str(getattr(lead, "description", "") or description)
        recommendation = str(getattr(lead, "recommendation", "") or recommendation)
        severity = _sev_bucket(_sev_name(lead))
        if any(m in lead_rule for m in _UNVERIFIABLE_MARKERS):
            status = STATUS_NON_VERIFIABLE
        elif _sev_name(lead) in _BLOCKING_SEVERITIES:
            status = STATUS_NON_CONFORME
        elif automation == "REFERENCE_DIAGNOSTIC":
            status = STATUS_ECART
        else:
            status = STATUS_A_DETERMINER
    elif automation == "PARTIAL":
        # Partial automated coverage with no alert is not a pass: it is undetermined.
        status = STATUS_A_DETERMINER
        description = "Couverture automatique partielle pour ce critère ; évaluation à compléter."
    else:
        # Rule implemented, no alert raised -> passed / within the reference input.
        status = STATUS_CONFORME

    section = _DOMAIN_TO_SECTION.get(str(entry.get("domain") or ""), _DEFAULT_SECTION)
    is_diagnostic = automation == "REFERENCE_DIAGNOSTIC"
    source = str(entry.get("source") or entry.get("standard") or "")
    caveat = ""
    blob = (source + " " + description + " " + recommendation)
    if "[TO VERIFY]" in blob or "14825" in blob or "TO VERIFY" in blob.upper():
        caveat = ("Comparaison dépendante d'une source non vérifiée "
                  "(p. ex. SN EN 14825) — indicatif, pas un succès prouvé. [TO VERIFY]")

    return {
        "id": str(entry.get("id") or rule or entry.get("criterion") or "crit"),
        "section": section,
        "name": str(entry.get("criterion") or entry.get("id") or "Critère"),
        "type": "diagnostic" if is_diagnostic else "decisif",
        "status": status,
        "value": "",
        "reference": _reference_text(entry),
        "unit": str(entry.get("unit") or ""),
        "article": source,
        "description": description,
        "source": source,
        "recommendation": recommendation or "—",
        "severity": severity,
        "caveat": caveat,
    }


def _global_comparison_criterion(sia3802: Dict[str, Any]) -> Dict[str, Any]:
    comparison = (sia3802 or {}).get("global_reference_comparison", {}) or {}
    if not isinstance(comparison, dict):
        comparison = {}
    cstatus = str(comparison.get("status") or "")
    if cstatus == "REVIEWED_RESULT_AVAILABLE":
        status = STATUS_CONFORME
        desc = ("Comparaison globale relue et acceptée ; la valeur projet respecte "
                "la valeur du projet de référence.")
    elif cstatus == "REVIEWED_RESULT_CONTRADICTS_ACCEPTANCE":
        status = STATUS_NON_CONFORME
        desc = ("La comparaison acceptée est contredite par les chiffres (valeur "
                "projet > référence). L'acceptation ne prime pas sur les nombres.")
    else:
        status = STATUS_A_DETERMINER
        desc = ("Porte décisive : la conformité globale SIA 380/2 exige une "
                "comparaison relue projet/référence, non fournie à ce stade.")
    project_value = _num(comparison.get("project_value"))
    reference_value = _num(comparison.get("reference_value"))
    ref_text = "—"
    if project_value is not None and reference_value is not None:
        ref_text = "{} → {}".format(project_value, reference_value)
    return {
        "id": "SIA3802_GLOBAL_REFERENCE_COMPARISON",
        "section": "global",
        "name": "Comparaison globale projet / référence",
        "type": "decisif",
        "status": status,
        "value": "",
        "reference": ref_text,
        "unit": "",
        "article": "SIA 380/2:2022 § 7.2.5.2",
        "description": desc,
        "source": str(comparison.get("source") or "Comparaison relue (CSV)"),
        "recommendation": "Fournir la comparaison projet/référence relue et acceptée.",
        "severity": "haute",
        "caveat": "",
    }


def _sia4010_criteria(sia4010: Dict[str, Any]) -> List[Dict[str, Any]]:
    tests = (sia4010 or {}).get("tests", {}) or {}
    rows: List[Dict[str, Any]] = []
    for name, data in sorted(tests.items()):
        data = data or {}
        st = str(data.get("status", "") or "").upper()
        if st in ("FAIL", "FAILED"):
            status = STATUS_NON_CONFORME
        elif st in ("OFFICIAL_RESULTS_RECORDED", "READY_FOR_OFFICIAL_REVIEW"):
            status = STATUS_A_DETERMINER
        else:
            status = STATUS_NON_VERIFIABLE
        rows.append({
            "id": "SIA4010_" + str(name),
            "section": "sia4010",
            "name": "SIA 4010 — {}".format(str(name).replace("_", " ").title()),
            "type": "decisif",
            "status": status,
            "value": "",
            "reference": "attestation requise",
            "unit": "",
            "article": "SIA 4010:2023",
            "description": ("La readiness plafonne à « résultats officiels enregistrés » ; "
                            "la validation exige l'attestation de la sous-commission SIA (art. 4.6.2)."),
            "source": "Registre de preuves SIA 4010",
            "recommendation": "Compléter le paquet officiel et solliciter l'attestation.",
            "severity": "moyenne",
            "caveat": "",
        })
    return rows


def build_criteria(
    sia3802_results: Optional[Dict[str, Any]],
    sia4010_results: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Map the real analysis output to the dashboard's criteria list (pure)."""
    sia3802 = dict(sia3802_results or {})
    alerts = list(sia3802.get("alerts", []) or [])
    criteria: List[Dict[str, Any]] = []
    for entry in SIA_COMPLIANCE_REQUIREMENT_MATRIX:
        if str(entry.get("standard") or "").startswith("SIA 4010"):
            continue  # SIA 4010 handled from its own results below
        if str(entry.get("domain") or "") == "Global Reference Comparison":
            continue  # the decisive gate is added once, from the live comparison
        criteria.append(_classify(entry, alerts))
    # The decisive global comparison, from the live reviewed-comparison status.
    criteria.append(_global_comparison_criterion(sia3802))
    criteria.extend(_sia4010_criteria(sia4010_results or {}))
    return criteria


def _verdict_banner(
    verdict: Any, code: str, scope: str = "both"
) -> Dict[str, str]:
    """Return a scope-aware, fail-closed verdict banner payload."""

    normalized_scope = normalize_report_scope(scope)
    status = scoped_verdict_status(verdict, normalized_scope)
    status_key = {
        COMPLIANT: "verdict_compliant",
        NOT_COMPLIANT: "verdict_not_compliant",
        NOT_DETERMINED: "verdict_not_determined",
    }.get(status, "verdict_not_determined")
    tone = {
        COMPLIANT: "ok",
        NOT_COMPLIANT: "crit",
        NOT_DETERMINED: "warn",
    }.get(status, "warn")
    heading = (
        "SIA 380/2"
        if normalized_scope == "sia3802"
        else translate("verdict_heading", code)
    )
    title = "{}: {}".format(heading, translate(status_key, code))
    detail = ("Ceci est une évaluation de preuves, pas un certificat. La validation SIA 4010 requiert "
              "l'attestation de la sous-commission SIA (art. 4.6.2)." if code == "fr" else
              "This is an evidence assessment, not a certificate. SIA 4010 validation requires SIA "
              "sub-commission attestation (art. 4.6.2).")
    if normalized_scope == "sia3802":
        detail = "{}<br>{}".format(
            translate("sia4010_readiness_attestation_required", code), detail
        )
    return {"tone": tone, "title": title, "detail": detail}


def build_payload(
    *,
    project_label: str,
    model_name: str,
    rooms_data: Optional[Sequence[Any]],
    sia3802_results: Optional[Dict[str, Any]],
    sia4010_results: Optional[Dict[str, Any]],
    verdict: Any,
    profile: Optional[CompanyProfile],
    language: str,
    generated_at: str,
    scope: str = "both",
) -> Dict[str, Any]:
    """Assemble the JSON payload the front-end renders (pure, deterministic)."""
    code = _lang(language)
    ui = _UI[code]
    office_name = getattr(profile, "company_name", "") or getattr(profile, "office_name", "") if profile else ""
    reference = getattr(profile, "report_reference", "") if profile else ""
    ns = ui["not_specified"]
    identification = [
        {"k": ui["f_cabinet"], "v": office_name or ns, "mono": False},
        {"k": ui["f_project"], "v": project_label or ns, "mono": False},
        {"k": ui["f_model"], "v": model_name or ns, "mono": True},
        {"k": ui["f_date"], "v": generated_at, "mono": True},
        {"k": ui["f_framework"], "v": "SIA 380/2:2022 · 4010:2023", "mono": True},
        {"k": ui["f_climate"], "v": "SIA 2028 DRY · Zürich-Kloten", "mono": True},
    ]
    criteria = build_criteria(sia3802_results, sia4010_results)
    return {
        "meta": {
            "lang": code,
            "ui": ui,
            "sectionLabels": _SECTION_LABELS[code],
            "sectionOrder": _SECTION_ORDER,
            "statusLabels": _STATUS_LABELS[code],
            "identification": identification,
            "verdict": _verdict_banner(verdict, code, scope),
            "reference": reference,
        },
        "criteria": criteria,
    }


def render_compliance_report_html(
    output_path: Union[str, Path],
    project_label: str,
    rooms_data: Optional[Sequence[Any]],
    sia3802_results: Optional[Dict[str, Any]],
    sia4010_results: Optional[Dict[str, Any]],
    score_result: Any = None,
    profile: Optional[CompanyProfile] = None,
    project_root: Optional[Union[str, Path]] = None,
    language: str = "en",
    model_name: str = "",
    generated_at: Optional[str] = None,
    scope: str = "both",
) -> Path:
    """Render the interactive HTML dashboard and return the written path.

    Mirrors ``render_compliance_report_pdf`` inputs so both deliverables read the
    same verdict and model summary.
    """
    report_scope = normalize_report_scope(scope)
    office = profile if profile is not None else load_company_profile(project_root or Path.cwd())
    rooms = list(rooms_data or [])
    verdict = build_compliance_verdict(sia3802_results, sia4010_results, len(rooms))
    _ = summarise_model(rooms)  # reserved for a future model-figures panel
    stamp = generated_at or datetime.now().strftime("%Y-%m-%d %H:%M")
    payload = build_payload(
        project_label=project_label,
        model_name=model_name,
        rooms_data=rooms,
        sia3802_results=sia3802_results,
        sia4010_results=sia4010_results,
        verdict=verdict,
        profile=office,
        language=language,
        generated_at=stamp,
        scope=report_scope,
    )
    code = _lang(language)
    doc = _TEMPLATE.replace("__PAGE_TITLE__", html.escape(_UI[code]["product"]))
    # Escape "</" so a criterion string can never break out of the <script> tag.
    payload_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    doc = doc.replace("__DATA_JSON__", payload_json)
    out = Path(output_path)
    out.write_text(doc, encoding="utf-8")
    return out


# The template is defined in a sibling module to keep this file readable; it is
# imported lazily so a template-only edit never risks the logic above.
from swiss_sia.compliance_report_html_template import TEMPLATE as _TEMPLATE  # noqa: E402
