"""Pure configuration and capability summary for the Swiss Compliance Hub."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, Tuple


@dataclass(frozen=True)
class HubAction:
    """One workflow exposed by the VEScripts hub."""

    action_id: str
    title: str
    description: str
    launcher: str
    badge: str
    mutates_ve: bool = False
    requires_disposable_project: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe action record."""
        return asdict(self)


ACTIONS: Tuple[HubAction, ...] = (
    HubAction(
        "client_audit",
        "1. Audit client en lecture seule",
        "Analyse le modele, l APS et les donnees manquantes sans modifier VE.",
        "Run_VE_Swiss_Compliance_Remediation_Probe.py",
        "READ-ONLY",
    ),
    HubAction(
        "evidence",
        "2. Completer les preuves SIA 380/2",
        "Collecte les metadonnees revues et refuse toute acceptation incomplete.",
        "Run_VE_Swiss_Compliance_Evidence_Wizard.py",
        "FAIL-CLOSED",
    ),
    HubAction(
        "report",
        "3. Generer le rapport de conformite",
        "Produit le rapport auditable SIA 380/2 et la prevalidation logicielle.",
        "Run_VE_Swiss_Compliance.py",
        "REPORT",
    ),
    HubAction(
        "reference_model",
        "4. Preparer et creer un modele de reference parametrique",
        "Choisit le climat, prepare les JSON locaux, puis lance le generateur. "
        "La couverture SIA 380/2 reste partielle.",
        "Run_VE_Swiss_Reference_Model_Setup.py",
        "PARTIAL / MUTATION",
        mutates_ve=True,
        requires_disposable_project=True,
    ),
    HubAction(
        "sia4010_lab",
        "5. Laboratoire SIA 4010",
        "Ouvre le Model Builder officiel. Chaque cas utilise un projet jetable distinct.",
        "Run_VE_SIA_Model_Builder_UI.py",
        "1/30 VERIFIED",
        mutates_ve=True,
        requires_disposable_project=True,
    ),
    HubAction(
        "sia4010_test1_fast_start",
        "6. Executer rapidement le prochain cas Test 1",
        "Prepare le climat et le scenario, cree ou reprend le cas, lance "
        "ApacheSim puis evalue l APS dans un projet jetable vide.",
        "Run_VE_SIA4010_Test1_Fast_Start.py",
        "6 ISO CASES / MUTATION",
        mutates_ve=True,
        requires_disposable_project=True,
    ),
    HubAction(
        "sia4010_hybrid_readiness",
        "7. Verifier les routes directes et templates SIA 4010",
        "Distingue les cas generables par VEScripts des cas exigeant un template "
        "VE qualifie et verifie son empreinte sans modifier le modele.",
        "Run_VE_SIA4010_Hybrid_Readiness.py",
        "READ-ONLY / FAIL-CLOSED",
    ),
    HubAction(
        "sia4010_template_capture",
        "8. Capturer un template VE candidat",
        "Calcule l empreinte du projet actif. Une revue independante reste "
        "obligatoire avant toute reutilisation.",
        "Run_VE_SIA4010_Capture_Active_Template.py",
        "CAPTURE ONLY",
    ),
    HubAction(
        "sia4010_template_copy",
        "9. Creer un projet jetable depuis un template qualifie",
        "Copie uniquement un template approuve et checksum-valide vers un "
        "nouveau dossier sans jamais ecraser un projet existant.",
        "Run_VE_SIA4010_Create_Disposable_From_Template.py",
        "QUALIFIED TEMPLATE",
    ),
    HubAction(
        "navigator",
        "10. Etat des classes SIA 4010",
        "Reconstruit le navigateur de preuves des 8 classes et 30 cas exacts.",
        "Run_VE_SIA4010_Navigator.py",
        "READ-ONLY",
    ),
)


def action_map() -> Dict[str, HubAction]:
    """Return the workflow registry indexed by stable action ID."""
    return {action.action_id: action for action in ACTIONS}


def is_disposable_project(project_path: str) -> bool:
    """Return whether the saved project name explicitly marks a disposable copy."""
    normalized = str(project_path or "").rstrip("/\\").replace("/", "\\")
    name = normalized.split("\\")[-1].upper() if normalized else ""
    return name.endswith(("_TEST", "_COPY", "_DISPOSABLE")) or "DISPOSABLE" in name


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
