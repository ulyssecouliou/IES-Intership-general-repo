"""Fail-closed governance checks for client SIA engineering assessments.

The numerical checkers decide technical findings. This module decides whether
the seven review domains surrounding those findings are documented well enough
to be relied upon. A documented domain is not a SIA compliance decision and is
never presented as one.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping, Sequence, Tuple

DOCUMENTED = "DOCUMENTED"
RESERVE = "RESERVE"
BLOCKED = "BLOCKED"

ENGINEERING_ASSESSMENT_ACKNOWLEDGEMENT = "ENGINEERING_ASSESSMENT_ONLY"

GOVERNANCE_REQUIRED_FIELDS: Tuple[str, ...] = (
    "weather_source_authority",
    "weather_use_case",
    "weather_scenario_period",
    "location_source",
    "altitude_source",
    "reviewer_role",
    "reviewer_organisation",
    "reviewer_competence_basis",
    "reviewer_acceptance_scope",
    "assumptions_status",
    "assumptions_register",
    "report_use_acknowledgement",
    "ventilation_scope",
)

DOMAIN_COPY = {
    "weather_location": {
        "en": "Weather and location",
        "de": "Klima und Standort",
        "fr": "Météo et localisation",
        "it": "Clima e ubicazione",
    },
    "ventilation_strategy": {
        "en": "Ventilation strategy",
        "de": "Lüftungsstrategie",
        "fr": "Stratégie de ventilation",
        "it": "Strategia di ventilazione",
    },
    "lighting_scope": {
        "en": "Lighting assessment scope",
        "de": "Umfang der Beleuchtungsbewertung",
        "fr": "Périmètre de l’éclairage",
        "it": "Ambito della valutazione dell’illuminazione",
    },
    "flow_power_sources": {
        "en": "Flow-rate and power sources",
        "de": "Quellen für Volumenströme und Leistungen",
        "fr": "Sources des débits et puissances",
        "it": "Fonti delle portate e delle potenze",
    },
    "external_assumptions": {
        "en": "Assumptions outside VE",
        "de": "Annahmen ausserhalb von VE",
        "fr": "Hypothèses absentes de VE",
        "it": "Ipotesi esterne a VE",
    },
    "reviewer_acceptance": {
        "en": "Reviewer identity and acceptance",
        "de": "Prüferidentität und Annahme",
        "fr": "Identité et acceptation du reviewer",
        "it": "Identità e accettazione del revisore",
    },
    "legal_scope": {
        "en": "Legal scope of the report",
        "de": "Rechtlicher Geltungsbereich des Berichts",
        "fr": "Portée juridique du rapport",
        "it": "Portata giuridica del rapporto",
    },
}

STATUS_COPY = {
    DOCUMENTED: {
        "en": "Documented",
        "de": "Dokumentiert",
        "fr": "Documenté",
        "it": "Documentato",
    },
    RESERVE: {
        "en": "Reserve",
        "de": "Vorbehalt",
        "fr": "Réserve",
        "it": "Riserva",
    },
    BLOCKED: {
        "en": "Blocked",
        "de": "Blockiert",
        "fr": "Bloqué",
        "it": "Bloccato",
    },
}

LEGAL_WORDING = {
    "en": (
        "This report is an engineering assessment of the analysed model and the "
        "evidence supplied for review. It is not an official SIA certificate, "
        "does not attest official software-method validation, and does not replace the "
        "decision of the responsible project authority."
    ),
    "de": (
        "Dieser Bericht ist eine technische Beurteilung des analysierten Modells "
        "und der zur Prüfung vorgelegten Nachweise. Er ist kein offizielles "
        "SIA-Zertifikat, bestätigt keine offizielle Validierung der Softwaremethode und "
        "ersetzt nicht den Entscheid der zuständigen Projektinstanz."
    ),
    "fr": (
        "Ce rapport est une évaluation d’ingénierie du modèle analysé et des "
        "preuves soumises à la revue. Il ne constitue pas un certificat officiel "
        "SIA, n’atteste pas une validation officielle de la méthode logicielle et ne remplace pas "
        "la décision de l’autorité responsable du projet."
    ),
    "it": (
        "Il presente rapporto è una valutazione tecnica del modello analizzato e "
        "delle prove sottoposte a revisione. Non è un certificato ufficiale SIA, "
        "non attesta una validazione ufficiale del metodo software e non sostituisce la "
        "decisione dell’autorità responsabile del progetto."
    ),
}

REPORT_COPY = {
    "section_title": {
        "en": "Review governance and evidence",
        "de": "Prüfgovernance und Nachweise",
        "fr": "Gouvernance de la revue et preuves",
        "it": "Governance della revisione e prove",
    },
    "overall_status": {
        "en": "Overall evidence status",
        "de": "Gesamtstatus der Nachweise",
        "fr": "Statut global des preuves",
        "it": "Stato complessivo delle prove",
    },
    "status": {
        "en": "Status",
        "de": "Status",
        "fr": "Statut",
        "it": "Stato",
    },
    "domain": {
        "en": "Domain",
        "de": "Bereich",
        "fr": "Domaine",
        "it": "Ambito",
    },
    "evidence": {
        "en": "Evidence recorded",
        "de": "Erfasster Nachweis",
        "fr": "Preuve enregistrée",
        "it": "Prova registrata",
    },
    "uncertainty": {
        "en": "Uncertainty / limitation",
        "de": "Unsicherheit / Grenze",
        "fr": "Incertitude / limite",
        "it": "Incertezza / limite",
    },
    "action": {
        "en": "Required action",
        "de": "Erforderliche Massnahme",
        "fr": "Action requise",
        "it": "Azione richiesta",
    },
    "responsible": {
        "en": "Responsible party",
        "de": "Verantwortliche Stelle",
        "fr": "Responsable",
        "it": "Responsabile",
    },
    "missing": {
        "en": "Missing or unresolved",
        "de": "Fehlend oder ungeklärt",
        "fr": "Manquant ou non résolu",
        "it": "Mancante o irrisolto",
    },
    "not_provided": {
        "en": "not provided",
        "de": "nicht angegeben",
        "fr": "non renseigné",
        "it": "non indicato",
    },
    "traceability_note": {
        "en": "A documented row confirms traceability only; it is not a compliance pass.",
        "de": "Eine dokumentierte Zeile bestätigt nur die Rückverfolgbarkeit; sie ist kein Konformitätsnachweis.",
        "fr": "Une ligne documentée confirme uniquement la traçabilité ; elle ne constitue pas une validation de conformité.",
        "it": "Una riga documentata conferma solo la tracciabilità; non costituisce un esito di conformità.",
    },
}

# Localized reviewer guidance. English findings retain their contextual wording
# assembled below; the other report languages use this controlled catalogue so
# an export never falls back to unexplained English prose.
GUIDANCE_COPY = {
    "weather_location": {
        "de": (
            "Die Dateikennung allein belegt weder Eignung von Station, Zeitraum noch Szenario.",
            "Amtliche Quelle, Berechnungszweck, Szenario/Zeitraum, Standort und Höhenquelle bestätigen.",
            "Energiefachperson / verantwortliche Prüfperson",
        ),
        "fr": (
            "L’identité du fichier ne prouve pas, à elle seule, l’adéquation de la station, de la période ou du scénario.",
            "Confirmer la source officielle, l’usage du calcul, le scénario et la période, la station, la localisation et la provenance de l’altitude.",
            "Spécialiste énergie du projet / reviewer responsable",
        ),
        "it": (
            "L’identità del file non dimostra da sola l’idoneità di stazione, periodo o scenario.",
            "Confermare fonte ufficiale, uso del calcolo, scenario/periodo, stazione, ubicazione e fonte dell’altitudine.",
            "Specialista energetico / revisore responsabile",
        ),
    },
    "ventilation_strategy": {
        "de": (
            "Die Erklärung bleibt prüferverantwortet; VE-Zuordnungen und Regelungen müssen damit übereinstimmen.",
            "Strategie mit Raum-/Systemzuordnungen, Zeitplänen, Regelungen und Auslegungsvolumenströmen abgleichen.",
            "HLK-Planung / verantwortliche Prüfperson",
        ),
        "fr": (
            "La déclaration reste sous la responsabilité du reviewer ; les affectations et régulations VE doivent lui correspondre.",
            "Réconcilier la stratégie déclarée avec les affectations des locaux et systèmes, les horaires, les régulations et les calculs de débit.",
            "Concepteur CVC / reviewer responsable",
        ),
        "it": (
            "La dichiarazione resta responsabilità del revisore; assegnazioni e controlli VE devono corrispondervi.",
            "Conciliare la strategia con assegnazioni, orari, controlli e calcoli delle portate di progetto.",
            "Progettista HVAC / revisore responsabile",
        ),
    },
    "lighting_scope": {
        "de": (
            "Die Umfangsangabe beweist nicht die Richtigkeit aller Raumzuordnungen und Regelungen.",
            "Bewertete Räume, Ausschlüsse, Leistungsgrundlage und Quelle der Lichtregelung angeben.",
            "Lichtplanung / verantwortliche Prüfperson",
        ),
        "fr": (
            "La définition du périmètre ne prouve pas que toutes les affectations de locaux et les régulations sont correctes.",
            "Indiquer les locaux évalués, les exclusions, la base de puissance installée ou projetée et la source des commandes d’éclairage.",
            "Concepteur éclairage / reviewer responsable",
        ),
        "it": (
            "La definizione dell’ambito non prova la correttezza di tutte le assegnazioni e dei controlli.",
            "Indicare locali valutati, esclusioni, base della potenza e fonte dei controlli illuminazione.",
            "Progettista illuminotecnico / revisore responsabile",
        ),
    },
    "flow_power_sources": {
        "de": (
            "Aus VE gelesene Werte bleiben Modelleingaben; ihre Auslegungsherkunft ist prüferverantwortet.",
            "Berechnungen, Listen oder Herstellerdaten archivieren und den in VE verwendeten Wert eindeutig benennen.",
            "HLK-/Lichtplanung und Modellautor",
        ),
        "fr": (
            "Les valeurs lues dans VE restent des entrées du modèle ; leur provenance de conception demeure sous la responsabilité du reviewer.",
            "Archiver les calculs, bordereaux ou données fabricant et identifier exactement la valeur utilisée dans VE.",
            "Concepteurs CVC/éclairage et auteur du modèle",
        ),
        "it": (
            "I valori letti in VE restano input del modello; la loro provenienza progettuale resta responsabilità del revisore.",
            "Archiviare calcoli, prospetti o dati del produttore e identificare il valore esatto usato in VE.",
            "Progettisti HVAC/illuminazione e autore del modello",
        ),
    },
    "external_assumptions": {
        "de": (
            "Offene Annahmen können das Ergebnis verändern; die Software kann die Vollständigkeit des Registers nicht beweisen.",
            "Jede offene Annahme klären oder als benannten Vorbehalt mit Verantwortlichem und Termin beibehalten.",
            "Modellautor und verantwortliche Prüfperson",
        ),
        "fr": (
            "Les hypothèses ouvertes peuvent modifier le verdict ; le logiciel ne peut pas prouver que le registre est exhaustif.",
            "Résoudre chaque hypothèse ouverte ou la conserver comme réserve nommée avec un responsable et une échéance.",
            "Auteur du modèle et reviewer responsable",
        ),
        "it": (
            "Le ipotesi aperte possono modificare l’esito; il software non può provare che il registro sia esaustivo.",
            "Risolvere ogni ipotesi aperta o mantenerla come riserva nominata con responsabile e scadenza.",
            "Autore del modello e revisore responsabile",
        ),
    },
    "reviewer_acceptance": {
        "de": (
            "Identität und Kompetenz sind deklarierte Nachweise; die Software authentifiziert sie nicht.",
            "Datierte Annahme der fachkundigen Person für den ausdrücklich genannten Prüfumfang einholen.",
            "Benannte verantwortliche Prüfperson",
        ),
        "fr": (
            "L’identité et la compétence sont des preuves déclarées ; le logiciel ne les authentifie pas.",
            "Obtenir l’acceptation datée de la personne compétente pour le périmètre de revue explicitement défini.",
            "Reviewer responsable nommé",
        ),
        "it": (
            "Identità e competenza sono prove dichiarate; il software non le autentica.",
            "Ottenere l’accettazione datata della persona competente per l’ambito di revisione dichiarato.",
            "Revisore responsabile nominato",
        ),
    },
    "legal_scope": {
        "de": (
            "Die Nicht-Zertifizierungs-Erklärung muss von der Prüfperson angenommen sein.",
            "Wortlaut in jedem Export beibehalten und die Annahme der verantwortlichen Prüfperson erfassen.",
            "Berichtaussteller und verantwortliche Prüfperson",
        ),
        "fr": (
            "La portée de non-certification doit être acceptée par le reviewer.",
            "Conserver cette formulation dans chaque export et enregistrer l’acceptation du reviewer responsable.",
            "Émetteur du rapport et reviewer responsable",
        ),
        "it": (
            "La portata di non-certificazione deve essere accettata dal revisore.",
            "Mantenere la formulazione in ogni esportazione e registrare l’accettazione del revisore responsabile.",
            "Emittente del rapporto e revisore responsabile",
        ),
    },
}


@dataclass(frozen=True)
class GovernanceFinding:
    domain: str
    status: str
    title: str
    evidence: str
    uncertainty: str
    required_action: str
    responsible_party: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


def _language(value: str) -> str:
    code = str(value or "en").strip().lower()
    return code if code in {"de", "en", "fr", "it"} else "en"


def legal_wording(language: str = "en") -> str:
    """Return the approved non-certification wording."""

    return LEGAL_WORDING[_language(language)]


def report_text(key: str, language: str = "en") -> str:
    """Return localized report copy used by every export renderer."""

    return _text(REPORT_COPY[key], language)


def _text(values: Mapping[str, str], language: str) -> str:
    code = _language(language)
    return values.get(code) or values["en"]


def _value(record: Mapping[str, Any], key: str) -> str:
    return str(record.get(key) or "").strip()


def _missing(record: Mapping[str, Any], fields: Sequence[str]) -> List[str]:
    return [field for field in fields if not _value(record, field)]


def project_metadata_governance_gaps(record: Mapping[str, Any]) -> List[str]:
    """Return missing or unresolved governance fields for one metadata row."""

    gaps = _missing(record, GOVERNANCE_REQUIRED_FIELDS)
    strategy = _value(record, "ventilation_strategy")
    lighting_scope = _value(record, "lighting_scope")
    aps_required = _value(record, "aps_outputs_required")

    if strategy in {"MECHANICAL_PRESENT", "MECHANICAL_EXPECTED"} and not _value(
        record, "ventilation_flow_source"
    ):
        gaps.append("ventilation_flow_source")
    if lighting_scope == "IN_SCOPE" and not _value(record, "lighting_power_source"):
        gaps.append("lighting_power_source")
    if lighting_scope == "OUT_OF_SCOPE" and not _value(
        record, "lighting_scope_justification"
    ):
        gaps.append("lighting_scope_justification")
    if aps_required == "YES" and not _value(record, "system_power_source"):
        gaps.append("system_power_source")
    if _value(record, "assumptions_status") == "UNDER_REVIEW":
        gaps.append("assumptions_status")
    if _value(record, "report_use_acknowledgement") != (
        ENGINEERING_ASSESSMENT_ACKNOWLEDGEMENT
    ):
        gaps.append("report_use_acknowledgement")
    return sorted(set(gaps))


def _finding(
    domain: str,
    status: str,
    language: str,
    evidence: str,
    uncertainty: str,
    action: str,
    responsible_party: str,
) -> GovernanceFinding:
    code = _language(language)
    if code != "en":
        localized = GUIDANCE_COPY[domain][code]
        missing_detail = ""
        if ": " in uncertainty and uncertainty.lower().startswith(
            ("missing", "missing or unresolved")
        ):
            missing_detail = " ({})".format(uncertainty.split(": ", 1)[1])
        uncertainty = localized[0] + missing_detail
        action = localized[1]
        responsible_party = localized[2]
    return GovernanceFinding(
        domain=domain,
        status=status,
        title=_text(DOMAIN_COPY[domain], language),
        evidence=evidence,
        uncertainty=uncertainty,
        required_action=action,
        responsible_party=responsible_party,
    )


def evaluate_assessment_governance(
    metadata: Mapping[str, Any],
    dynamic_results: Mapping[str, Any],
    language: str = "en",
) -> Tuple[GovernanceFinding, ...]:
    """Evaluate the seven review domains without granting a compliance pass."""

    record = metadata or {}
    dynamic = dynamic_results or {}
    findings: List[GovernanceFinding] = []

    weather_fields = (
        "weather_basis",
        "weather_file",
        "location",
        "altitude_m",
        "weather_source_authority",
        "weather_use_case",
        "weather_scenario_period",
        "location_source",
        "altitude_source",
    )
    weather_missing = _missing(record, weather_fields)
    weather_match = str(dynamic.get("reviewed_weather_match_status") or "").upper()
    weather_status = (
        BLOCKED if weather_missing or weather_match == "MISMATCH" else DOCUMENTED
    )
    if not weather_missing and weather_match not in {"MATCH", "MISMATCH"}:
        weather_status = RESERVE
    findings.append(
        _finding(
            "weather_location",
            weather_status,
            language,
            "basis={}; file={}; location={}; altitude={} m; match={}".format(
                _value(record, "weather_basis") or "not provided",
                _value(record, "weather_file") or "not provided",
                _value(record, "location") or "not provided",
                _value(record, "altitude_m") or "not provided",
                weather_match or "NOT_CHECKABLE",
            ),
            (
                "Missing: " + ", ".join(weather_missing)
                if weather_missing
                else "The software verifies file identity only; suitability of the station, period and scenario remains reviewer-owned."
            ),
            "Confirm the official source, intended calculation use, scenario/period, station/location and altitude provenance.",
            "Project energy specialist / responsible reviewer",
        )
    )

    strategy = _value(record, "ventilation_strategy")
    ventilation_missing = _missing(
        record, ("ventilation_strategy", "ventilation_justification", "ventilation_scope")
    )
    if strategy in {"MECHANICAL_PRESENT", "MECHANICAL_EXPECTED"} and not _value(
        record, "ventilation_flow_source"
    ):
        ventilation_missing.append("ventilation_flow_source")
    ventilation_status = (
        BLOCKED if ventilation_missing or strategy == "UNDER_REVIEW" else DOCUMENTED
    )
    findings.append(
        _finding(
            "ventilation_strategy",
            ventilation_status,
            language,
            "strategy={}; scope={}; flow source={}".format(
                strategy or "not provided",
                _value(record, "ventilation_scope") or "not provided",
                _value(record, "ventilation_flow_source") or "not provided",
            ),
            (
                "Missing or unresolved: " + ", ".join(ventilation_missing)
                if ventilation_missing
                else "The declaration is reviewer-owned; VE assignments and controls must still agree with it."
            ),
            "Reconcile the declared strategy with room/system assignments, schedules, controls and design flow calculations.",
            "HVAC designer / responsible reviewer",
        )
    )

    lighting_scope = _value(record, "lighting_scope")
    lighting_missing = _missing(record, ("lighting_scope",))
    if lighting_scope == "IN_SCOPE" and not _value(record, "lighting_power_source"):
        lighting_missing.append("lighting_power_source")
    if lighting_scope == "OUT_OF_SCOPE" and not _value(
        record, "lighting_scope_justification"
    ):
        lighting_missing.append("lighting_scope_justification")
    lighting_status = (
        BLOCKED if lighting_missing or lighting_scope == "UNDER_REVIEW" else DOCUMENTED
    )
    findings.append(
        _finding(
            "lighting_scope",
            lighting_status,
            language,
            "scope={}; power source={}".format(
                lighting_scope or "not provided",
                _value(record, "lighting_power_source") or "not provided",
            ),
            (
                "Missing or unresolved: " + ", ".join(lighting_missing)
                if lighting_missing
                else "Scope documentation does not prove that all room mappings and controls are correct."
            ),
            "State the assessed rooms, exclusions, installed/design power basis and lighting-control source.",
            "Lighting designer / responsible reviewer",
        )
    )

    source_missing: List[str] = []
    if strategy in {"MECHANICAL_PRESENT", "MECHANICAL_EXPECTED"} and not _value(
        record, "ventilation_flow_source"
    ):
        source_missing.append("ventilation_flow_source")
    if lighting_scope == "IN_SCOPE" and not _value(record, "lighting_power_source"):
        source_missing.append("lighting_power_source")
    if _value(record, "aps_outputs_required") == "YES" and not _value(
        record, "system_power_source"
    ):
        source_missing.append("system_power_source")
    if not _value(record, "aps_outputs_required"):
        source_missing.append("aps_outputs_required")
    findings.append(
        _finding(
            "flow_power_sources",
            BLOCKED if source_missing else DOCUMENTED,
            language,
            "airflow={}; lighting={}; systems={}".format(
                _value(record, "ventilation_flow_source")
                or "not applicable/not provided",
                _value(record, "lighting_power_source") or "not applicable/not provided",
                _value(record, "system_power_source") or "not applicable/not provided",
            ),
            (
                "Missing: " + ", ".join(source_missing)
                if source_missing
                else "Values read from VE remain model inputs; their design provenance is reviewer-owned."
            ),
            "Archive calculations, schedules or manufacturer data and identify the exact value used in VE.",
            "HVAC/lighting designer and model author",
        )
    )

    assumptions_status = _value(record, "assumptions_status")
    assumptions_missing = _missing(record, ("assumptions_status", "assumptions_register"))
    if assumptions_missing or assumptions_status == "UNDER_REVIEW":
        assumption_result = BLOCKED
    elif assumptions_status == "OPEN_ASSUMPTIONS":
        assumption_result = RESERVE
    else:
        assumption_result = DOCUMENTED
    findings.append(
        _finding(
            "external_assumptions",
            assumption_result,
            language,
            "status={}; register={}".format(
                assumptions_status or "not provided",
                _value(record, "assumptions_register") or "not provided",
            ),
            (
                "Open assumptions remain unresolved and may change the verdict."
                if assumptions_status == "OPEN_ASSUMPTIONS"
                else (
                    "Missing: " + ", ".join(assumptions_missing)
                    if assumptions_missing
                    else "The software records the declaration but cannot prove that the register is exhaustive."
                )
            ),
            "Resolve each open assumption or retain it as a named report reserve with owner and due date.",
            "Model author and responsible reviewer",
        )
    )

    reviewer_fields = (
        "reviewer",
        "review_date",
        "reviewer_role",
        "reviewer_organisation",
        "reviewer_competence_basis",
        "reviewer_acceptance_scope",
    )
    reviewer_missing = _missing(record, reviewer_fields)
    reviewer_status = BLOCKED if reviewer_missing else DOCUMENTED
    findings.append(
        _finding(
            "reviewer_acceptance",
            reviewer_status,
            language,
            "reviewer={}; role={}; organisation={}; date={}".format(
                _value(record, "reviewer") or "not provided",
                _value(record, "reviewer_role") or "not provided",
                _value(record, "reviewer_organisation") or "not provided",
                _value(record, "review_date") or "not provided",
            ),
            (
                "Missing: " + ", ".join(reviewer_missing)
                if reviewer_missing
                else "Identity and competence are declared evidence; the software does not authenticate them."
            ),
            "Obtain dated acceptance from the competent person for the explicitly stated review scope.",
            "Named responsible reviewer",
        )
    )

    acknowledgement = _value(record, "report_use_acknowledgement")
    legal_status = (
        DOCUMENTED
        if acknowledgement == ENGINEERING_ASSESSMENT_ACKNOWLEDGEMENT
        else BLOCKED
    )
    findings.append(
        _finding(
            "legal_scope",
            legal_status,
            language,
            legal_wording(language),
            (
                "The required acknowledgement is recorded."
                if legal_status == DOCUMENTED
                else "The reviewer has not accepted the non-certification scope."
            ),
            "Keep this wording in every exported report and obtain the responsible reviewer's acknowledgement.",
            "Report issuer and responsible reviewer",
        )
    )

    return tuple(findings)


def governance_summary(findings: Sequence[GovernanceFinding]) -> Dict[str, Any]:
    counts = {DOCUMENTED: 0, RESERVE: 0, BLOCKED: 0}
    for finding in findings:
        counts[finding.status] = counts.get(finding.status, 0) + 1
    overall = BLOCKED if counts[BLOCKED] else RESERVE if counts[RESERVE] else DOCUMENTED
    return {
        "overall_status": overall,
        "counts": counts,
        "findings": [finding.to_dict() for finding in findings],
    }


def status_label(status: str, language: str = "en") -> str:
    values = STATUS_COPY.get(str(status or "").upper(), STATUS_COPY[BLOCKED])
    return _text(values, language)
