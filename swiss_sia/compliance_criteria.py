# -*- coding: utf-8 -*-
"""Machine-readable client SIA 380/2 compliance-criteria manifest (pure).

Builds the single structured checklist that both the engine and an analyst read
to answer, for a client VE model + its ApacheSim ``.aps``:

  1. Which criteria must a client model meet to be fully SIA 380/2 compliant?
  2. From the VE model and its .aps results, what can be evaluated (and how)?
  3. What can VE NOT provide, so the criterion cannot be auto-decided?

Every regulatory value comes from ``swiss_sia/config.py`` (itself sourced), never
from this module: it only joins the requirement matrix (verdict-bearing criteria)
with the data-coverage matrix (inputs each criterion needs) and adds a capability
layer derived from the code's own ``automation`` signals.

Pure Python, no ``iesve`` import. The runtime fill lives in
``swiss_sia/compliance_criteria_evaluator.py``; the JSON writer lives in
``scripts/build_client_compliance_criteria.py``.
"""

from __future__ import annotations

from typing import Any, Dict, List

from swiss_sia import config

# ---------------------------------------------------------------------------
# Capability layer -- derived from the code, not invented.
# ---------------------------------------------------------------------------
# `automation` in the config matrices already records how far the toolchain can
# go for each input. Map it to a plain capability verdict the analyst reads
# directly. A few criteria carry a stronger, code-grounded caveat (no ingestion
# path in VE at all, or a missing normative source): those override the generic
# mapping via _CAPABILITY_OVERRIDES below.
_AUTOMATION_TO_CAPABILITY = {
    "AUTOMATED": "VE_AVAILABLE",
    "PARTIAL": "VE_PARTIAL",
    "REFERENCE_DIAGNOSTIC": "VE_PARTIAL",
    "EVIDENCE_SCAN": "EXTERNAL_EVIDENCE",
    "READINESS_ONLY": "EXTERNAL_EVIDENCE",
    "NOT_IMPLEMENTED": "NOT_AVAILABLE",
}

CAPABILITY_LEGEND = {
    "VE_AVAILABLE": "VE exposes this directly; the Run-button script extracts it automatically.",
    "VE_PARTIAL": "VE can expose it, but the value may be missing/ambiguous per model; it then falls to NOT_CHECKABLE (never a silent pass) and may need a reviewer confirmation.",
    "EXTERNAL_EVIDENCE": "VE does not produce this; it is supplied as reviewer/official evidence files under sia4010_evidence/.",
    "NOT_AVAILABLE": "No path in VE (or in the current toolchain) produces this today; it cannot be auto-decided and must never be inferred.",
}

# Code-grounded caveats that override or annotate the generic mapping.
_CAPABILITY_OVERRIDES = {
    "SIA3802_THERMAL_BRIDGES": {
        "ve_capability": "VE_AVAILABLE",
        "ve_capability_note": (
            "VE 2025.2 exposes psi/chi per surface (VESurface."
            "get_thermal_bridges_non_repeating/_random), so the model's thermal-"
            "bridge conductance H_tb = sum(psi.L.flux) + sum(chi.count) [W/K] is read "
            "directly. A junction left at psi=0 may be an un-entered default, so an "
            "all-zero read is surfaced but not treated as complete evidence. On older "
            "VE (members absent) or unset models, supply a reviewed schedule via "
            "SIA3802_thermal_bridges_<project>.csv."
        ),
    },
    "SIA3802_ELECTRICAL_POWER": {
        "ve_capability": "EXTERNAL_EVIDENCE",
        "ve_capability_note": (
            "SIA 380/2 §7.2.4 required electrical power (fluid transport + "
            "conditioning incl. cooling) per conditioned net floor area is a DESIGN "
            "sizing figure with a daily simultaneity factor (§7.2.4.3); VE does not "
            "expose it. Supply it via SIA3802_electrical_power_<project>.csv; the "
            "tool compares it to 7 W/m2 (new) / 12 W/m2 (existing). [Whether an "
            "exceedance is a hard verdict gate is pending norm-analyst.]"
        ),
    },
    "SIA3802_DESIGN_POWER_DAYS": {
        "ve_capability": "NOT_AVAILABLE",
        "ve_capability_note": (
            "The prescribed heating/cooling design-day workflow is NOT_IMPLEMENTED; "
            "annual room peaks must never be substituted for it."
        ),
    },
    "SIA3802_COOLING_EER_SEER": {
        "ve_capability_note": (
            "Generator type/EER extractable, but an autosized generator leaves the "
            "capacity greyed out so the SIA 380/2 table 5 power band cannot be "
            "resolved from the model; supply the reviewed manufacturer class + "
            "capacity + declared SEER (or nominal EER) via "
            "SIA3802_cooling_generators_<project>.csv. A declared SEER is EN 14825 "
            "by construction (SN EN 14825:2018 is now a verified reference and SIA "
            "380/2 table 5 defines its SEER minima 'selon SN EN 14825'), so it is "
            "compared to the SIA SEER band cleanly. A seasonal index read from the "
            "VE model still needs its EN 14825 computation confirmed."
        ),
    },
    "SIA3802_HEATING_SCOP": {
        "ve_capability_note": (
            "Heat-pump type/SCOP extractable, but the seasonal SCoP equivalence rests "
            "on SN EN 14825 (absent from refs/): the SCoP verdict stays indicative "
            "[TO VERIFY], not a proven pass."
        ),
    },
    "SIA3802_LIGHTING_CONTROL": {
        "ve_capability_note": (
            "Lighting power/schedules extractable. SIA 387/4 (the lighting-control "
            "numeric tables) is absent from refs/, so the tool cannot itself verify "
            "the control type. Best effort: a reviewer-confirmed SIA 387/4 control "
            "mapping (SIA3874_lighting_control_mapping_<project>.csv) covering the "
            "lit rooms is credited UNDER RESERVE -- a reviewer attestation, not an "
            "independently verified pass. Only the shading control (table 9) is "
            "fully referenced (SIA 387/4:2023 confirmed)."
        ),
    },
}

# The concrete quantities the ApacheSim .aps must yield, per aps-sourced
# criterion. These are the fields swiss_sia/simulation_results.py::DynamicResults
# reads through iesve.ResultsReader inside VE -- listed here so the manifest states
# exactly what the .aps has to expose for each criterion to be decidable.
_APS_QUANTITIES = {
    "SIA3802_DYNAMIC_APS_RESULTS": [
        "readable .aps in the project Vista folder",
        "results_per_hour / timestep metadata",
        "room and system variable list via get_variables()",
        "EPW/weather provenance of the run",
    ],
    "SIA3802_HOURLY_TEMPERATURES": [
        "hourly room temperature series (dry resultant temperature)",
        "hourly occupancy series",
        "SIA 180 upper/lower comfort-limit curves",
        "occupied_hours_above_sia180_upper",
        "occupied_hours_below_sia180_lower",
        "annual_comfort_period_complete (full-year coverage flag)",
    ],
    "SIA3802_HEATING_COOLING_DEMANDS": [
        "heating_kwh (annual)",
        "cooling_kwh (annual)",
        "coil_heating_kwh / coil_cooling_kwh",
        "room area for kWh/m2 normalisation",
        "peak_heating_w / peak_cooling_w where available",
    ],
    "SIA3802_DESIGN_POWER_DAYS": [
        "dedicated design-day .aps result files (NOT annual peaks)",
        "15-minute load series over the prescribed heating/cooling design days",
        "traceable weather/setup metadata for the design-day run",
    ],
}


# What the tool / VE structurally cannot establish, each with its justification.
# Single source shared by the HTML dashboard and the PDF report annex. Stable
# facts about the documented VE API and the available sources, not per-model
# results: shown so a reader understands why some criteria can never be
# auto-decided (they are reserves, never silent passes).
CLIENT_LIMITATIONS = {
    "fr": [
        {"title": "Ponts thermiques (ψ/χ)",
         "why": "VE 2025.2 expose ψ/χ par surface : la conductance de ponts thermiques H_tb (W/K) est lue directement. Une jonction laissée à ψ=0 peut être un défaut non saisi (à vérifier). Sur VE plus ancienne ou modèle non renseigné, un calcul relu (CSV) reste le repli."},
        {"title": "Puissance de dimensionnement",
         "why": "Le calcul par les jours de dimensionnement prescrits n'est pas implémenté ; les pics annuels ne peuvent pas s'y substituer."},
        {"title": "SEER saisonnier (froid)",
         "why": "SN EN 14825:2018 est désormais une référence vérifiée et SIA 380/2 table 5 définit ses minima SEER « selon SN EN 14825» : un SEER déclaré fabricant (ErP/Ecodesign) est comparé proprement à la bande SIA. Seul un indice saisonnier lu du modèle VE reste [TO VERIFY] (calcul EN 14825 non confirmé)."},
        {"title": "SCoP saisonnier (chaud)",
         "why": "La clause de calcul du SCoP (EN 14825, chaud) n'est pas encore vérifiée : verdict indicatif [TO VERIFY], pas un pass prouvé."},
        {"title": "Contrôle de l'éclairage",
         "why": "SIA 387/4 (référence de contrôle éclairage) est absente des sources vérifiées : le verdict de contrôle ne peut pas être clôturé."},
        {"title": "Comparaison globale (§ 7.2.5.2)",
         "why": "Décisive pour la conformité SIA 380/2, elle n'est pas calculée côté client (le projet de référence n'est pas simulé) : elle est fournie et acceptée par un relecteur."},
        {"title": "Écriture des gains / ventilation dans les pièces",
         "why": "L'API VE documentée n'expose pas de membre pour écrire des gains au niveau pièce (VERoomData) ; la préparation du modèle se fait dans l'interface VE. L'outil lit et audite, il ne modifie pas le modèle."},
        {"title": "Confort d'été (SIA 180)",
         "why": "Le verdict de surchauffe exige un résultat APS annuel complet et la provenance météo vérifiée. Si l'opérabilité des fenêtres est inconnue, le contrôle utilise 0 h comme valeur de dépistage conservatrice mais le domaine reste NOT_DETERMINED. Pour une fenêtre non opérable avec statut bâtiment inconnu, 100 h/an (NEUF) est utilisé pour le dépistage, sans transformer la preuve manquante en conformité."},
        {"title": "Protection solaire — stratégie de régulation",
         "why": "VE expose les dispositifs d'ombrage mais pas la stratégie de régulation active (SIA 380/2 table 10). La catégorie de contrôle et le g_total actif doivent être fournis par preuve du relecteur. Tant que cette preuve manque, le verdict global reste NOT_DETERMINED (porte autonome §7.1.2)."},
        {"title": "Catégorie d'usage SIA 2024",
         "why": "L'affectation de chaque zone thermique à une catégorie SIA 2024 n'est pas déductible automatiquement du modèle VE. Un mapping relecteur (CSV) est requis ; sans lui, les horaires, gains et hypothèses de vitrage ne sont pas comparables aux références normatives."},
        {"title": "Récupération de chaleur CTA",
         "why": "La classe d'étanchéité des conduits, le type et l'efficacité de récupération de chaleur et les pertes de charge ne sont que partiellement exposés par VE. La preuve complète (fiche technique CTA, classe L1/L2) doit être fournie par le relecteur."},
        {"title": "Horaires et profils d'utilisation",
         "why": "VE expose les profils de template sous forme de profil équivalent journalier. Les horaires hebdomadaires complets et les exceptions ne sont pas automatiquement extraits : un export ou une confirmation du relecteur est nécessaire pour la traçabilité normative."},
    ],
    "en": [
        {"title": "Thermal bridges (ψ/χ)",
         "why": "VE 2025.2 exposes ψ/χ per surface: the thermal-bridge conductance H_tb (W/K) is read directly. A junction left at ψ=0 may be an un-entered default (to verify). On older VE or an unset model, a reviewed calculation (CSV) is the fallback."},
        {"title": "Design-day power",
         "why": "The prescribed heating/cooling design-day workflow is not implemented; annual room peaks must never be substituted for it."},
        {"title": "Seasonal SEER (cooling)",
         "why": "SN EN 14825:2018 is now a verified reference and SIA 380/2 table 5 defines its SEER minima 'selon SN EN 14825': a declared SEER (manufacturer ErP/Ecodesign) is compared cleanly to the SIA band. Only a seasonal index read from the VE model stays [TO VERIFY] (its EN 14825 computation is unconfirmed)."},
        {"title": "Seasonal SCoP (heating)",
         "why": "The heating SCoP calculation clause (EN 14825) is not yet verified: indicative [TO VERIFY], not a proven pass."},
        {"title": "Lighting control",
         "why": "SIA 387/4 (lighting-control reference) is absent from the verified sources: the control verdict cannot be closed."},
        {"title": "Global comparison (§ 7.2.5.2)",
         "why": "Decisive for SIA 380/2 compliance, it is not computed client-side (the reference project is not simulated): it is supplied and accepted by a reviewer."},
        {"title": "Writing room gains / ventilation",
         "why": "The documented VE API exposes no member to write room-level gains (VERoomData); model preparation is done in the VE interface. The tool reads and audits, it does not modify the model."},
        {"title": "Summer comfort (SIA 180)",
         "why": "The overheating verdict requires a complete annual APS result and verified weather provenance. When window operability is unknown, the check uses 0 h as a conservative screening value but the domain remains NOT_DETERMINED. For a non-operable window with unknown building status, 100 h/year (NEW) is used for screening without turning missing evidence into compliance."},
        {"title": "Solar protection — control strategy",
         "why": "VE exposes shading devices but not the active control strategy (SIA 380/2 table 10). The control category and active g_total must be supplied as reviewer evidence. Until this evidence is provided, the overall verdict stays NOT_DETERMINED (autonomous gate §7.1.2)."},
        {"title": "SIA 2024 use category",
         "why": "Assigning each thermal zone to a SIA 2024 use category cannot be derived automatically from the VE model. A reviewer mapping (CSV) is required; without it, schedules, gains and glazing assumptions are not comparable to normative references."},
        {"title": "AHU heat recovery",
         "why": "Duct leakage class, heat-recovery type/efficiency and pressure drops are only partially exposed by VE. Complete evidence (AHU data sheet, L1/L2 class) must be supplied by the reviewer."},
        {"title": "Schedules and usage profiles",
         "why": "VE exposes template profiles as daily-equivalent profiles. Full weekly schedules and exceptions are not automatically extracted: an export or reviewer confirmation is needed for normative traceability."},
    ],
}


def classify_data_source(expected_source: str) -> List[str]:
    """Infer the data source(s) that feed a criterion from the coverage wording.

    Keeps the answer to "static model vs .aps vs reviewer" explicit per row.
    """
    text = (expected_source or "").lower()
    aps = "aps" in text or "vista" in text or "resultsreader" in text
    static = ("model api" in text or "cdb" in text or "construction" in text
              or "opening" in text or "air-exchange" in text or "apache systems" in text
              or "plant data" in text or "templates" in text or "shading" in text
              or "profiles" in text or "system data" in text)
    reviewer = ("reviewer" in text or "csv" in text or "official" in text
                or "manufacturer" in text or "authority" in text
                or "evidence" in text or "sub-commission" in text
                or "decision" in text or "schedule" in text or "export" in text
                or "note" in text or "data sheet" in text or "metadata" in text)
    project = "project settings" in text or "weather" in text or "location" in text
    sources: List[str] = []
    if project:
        sources.append("ve_project_settings")
    if aps:
        sources.append("aps_simulation_results")
    if static:
        sources.append("ve_static_model")
    if reviewer:
        sources.append("reviewer_or_external_evidence")
    return sources or ["ve_static_model"]


def _key_match(cov: Dict[str, Any], req: Dict[str, Any]) -> bool:
    """Loose match between a coverage input and a verdict-bearing requirement."""
    cov_crit = (cov.get("criterion") or "").lower()
    req_crit = (req.get("criterion") or "").lower()
    if not cov_crit or not req_crit:
        return False
    tokens = ("u-value", "uw", "solar factor", "transmittance", "frame",
              "infiltration", "eer", "scop", "ventilation control", "dynamic")
    for token in tokens:
        if token in cov_crit and token in req_crit:
            return True
    return cov_crit == req_crit


def build_manifest() -> Dict[str, Any]:
    """Return the full static compliance-criteria manifest (runtime_status unset)."""
    requirement_by_domain: Dict[Any, List[Dict[str, Any]]] = {}
    for req in config.SIA_COMPLIANCE_REQUIREMENT_MATRIX:
        requirement_by_domain.setdefault(req.get("domain"), []).append(req)

    criteria: List[Dict[str, Any]] = []
    for cov in config.SIA_DATA_COVERAGE_MATRIX:
        automation = cov.get("automation", "PARTIAL")
        capability = _AUTOMATION_TO_CAPABILITY.get(automation, "VE_PARTIAL")
        note = ""
        override = _CAPABILITY_OVERRIDES.get(cov["id"])
        if override:
            capability = override.get("ve_capability", capability)
            note = override.get("ve_capability_note", "")

        thresholds: Dict[str, Any] = {}
        for req in requirement_by_domain.get(cov.get("domain"), []):
            if _key_match(cov, req):
                thresholds = {
                    "limit": req.get("limit"),
                    "target": req.get("target"),
                    "unit": req.get("unit"),
                }
                break

        criteria.append({
            "id": cov["id"],
            "standard": cov.get("standard"),
            "domain": cov.get("domain"),
            "criterion": cov.get("criterion"),
            "expected_value": cov.get("expected_value"),
            "article_source": cov.get("source"),
            "thresholds": thresholds,
            "data_needed": cov.get("data_needed"),
            "expected_source": cov.get("expected_source"),
            "data_source": classify_data_source(cov.get("expected_source")),
            "aps_quantities": _APS_QUANTITIES.get(cov["id"], []),
            "automation": automation,
            "ve_capability": capability,
            "ve_capability_note": note,
            "coverage_key": cov.get("coverage_key", ""),
            "preferred_format": cov.get("preferred_format"),
            "destination": cov.get("destination"),
            "owner": cov.get("owner"),
            "runtime_status": "TO_BE_EVALUATED",
            "runtime_evidence": "",
            "next_action": cov.get("next_action"),
        })

    return {
        "meta": {
            "title": "Client SIA 380/2 compliance criteria -- machine-readable manifest",
            "purpose": (
                "Single structured checklist to evaluate a client VE model + .aps "
                "against SIA 380/2:2022. runtime_status is filled per model by "
                "swiss_sia/compliance_criteria_evaluator.py. Missing evidence never "
                "becomes PASS."
            ),
            "generated_from": (
                "swiss_sia/config.py: SIA_COMPLIANCE_REQUIREMENT_MATRIX + "
                "SIA_DATA_COVERAGE_MATRIX (regulatory values sourced there, not here)"
            ),
            "builder": "swiss_sia/compliance_criteria.py::build_manifest",
            "standard": "SIA 380/2:2022",
            "verdict_logic": {
                "reference": "swiss_sia/compliance_verdict.py",
                "compliant_requires_all": [
                    "at least one room analysed",
                    "no determined blocking (CRITICAL/HIGH) finding in the six domains",
                    "the reviewed global comparison does not contradict acceptance (project <= reference)",
                    "no domain left NOT_DETERMINED (no MISSING / NOT_CHECKABLE / placeholder)",
                    "the decisive global comparison is present and REVIEWED_RESULT_AVAILABLE",
                ],
                "note": (
                    "Component criteria are diagnostics; they do not decide compliance. "
                    "SIA 380/2 decides on the global project/reference comparison "
                    "(the decisive_gate below)."
                ),
            },
            "runtime_status_legend": {
                "TO_BE_EVALUATED": "Static template value; not yet run against a model.",
                "OK": "Evidence present from the model/.aps; no blocking finding.",
                "PARTIAL": "Some evidence present; at least one input still missing.",
                "NOT_OK": "A determined blocking finding (value out of range / contradiction).",
                "NOT_CHECKABLE": "Required model/.aps evidence missing or placeholder; never a pass.",
                "NOT_AVAILABLE_IN_VE": "VE structurally cannot produce this; not auto-decidable.",
                "NEEDS_REVIEWER_EVIDENCE": "Requires reviewer/official evidence files.",
                "NON_APPLICABLE": "The norm does not apply this criterion to this model (e.g. SCOP with no heat pump); out of scope, never a silent pass.",
            },
            "data_source_legend": {
                "ve_project_settings": "VE project location/altitude/weather settings.",
                "ve_static_model": "VE static model via the model/CDB API (geometry, constructions, systems).",
                "aps_simulation_results": "ApacheSim .aps/Vista results via ResultsReader (dynamic needs, temperatures, energy). The .aps is the required source for every dynamic criterion; it is read at runtime inside VE (iesve.ResultsReader, binary format), by swiss_sia/simulation_results.py, and its quantities fill each aps criterion's runtime_status. See each aps criterion's aps_quantities.",
                "reviewer_or_external_evidence": "Reviewer CSV or official/manufacturer files under sia4010_evidence/.",
            },
            "ve_capability_legend": CAPABILITY_LEGEND,
        },
        "decisive_gate": {
            "id": "SIA3802_GLOBAL_REFERENCE_COMPARISON",
            "article": "SIA 380/2:2022 §7.2.5.2",
            "criterion": "Project global energy-expenditure index <= reference-project index",
            "data_source": ["reviewer_or_external_evidence"],
            "ve_capability": "EXTERNAL_EVIDENCE",
            "ve_capability_note": (
                "Not computed automatically (the reference project is not simulated "
                "client-side). Provide the accepted reviewer record: see "
                "docs/project/GUIDE_COMPARAISON_GLOBALE_SIA3802.md and its CSV template."
            ),
            "runtime_status": "TO_BE_EVALUATED",
            "runtime_evidence": "",
        },
        "criteria": criteria,
    }
