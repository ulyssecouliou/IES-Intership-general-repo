# -*- coding: utf-8 -*-
"""Collects SIA 380/2 evidence for a client model — pure core.

TWO THINGS NOT TO CONFUSE, and this module exists to keep them separate:

    SIA 4010  validates the SOFTWARE and its methods. This is the work on the
              seven reference tests, in refs/ and engine/. It says nothing
              about a client building.
    SIA 380/2 judges the compliance of a client BUILDING. This is the object
              of this module. Validated software is not sufficient: the project
              data and documentary evidence are also required.

A technical PASS — a readable APS, a successful extraction — is neither of
the above. The three vocabularies are distinct and remain so throughout.

WHAT THIS MODULE NEVER DOES
    - invent a regulatory value, a location, an altitude, a ventilation flow
      rate, a lighting power;
    - replace a missing datum with zero;
    - declare a building compliant;
    - modify the VE model.

Pure Python: no `iesve`, no `tkinter`. Testable in continuous integration.
"""

from __future__ import annotations

import csv
import io
import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Status vocabulary
# ---------------------------------------------------------------------------
#
# These seven values are not synonyms. Confusing them is precisely what
# produces a false compliance declaration.

#: The VE model is at fault: something is missing or incorrect in it.
DEFAUT_MODELE = "MODEL_DEFECT"

#: The model may be correct, but a client datum is missing to judge it.
#: This is not a model defect.
DONNEE_CLIENT_MANQUANTE = "CLIENT_DATA_MISSING"

#: The quantity was not requested from ApacheSim. The model and data
#: may be perfectly correct.
SORTIE_NON_ACTIVEE = "SIM_OUTPUT_NOT_ENABLED"

#: The VEScripts API does not expose what is needed to reach a conclusion.
LIMITE_VESCRIPTS = "VESCRIPT_LIMITATION"

#: A document is missing, not a technical datum.
PREUVE_MANQUANTE = "DOCUMENTARY_EVIDENCE_MISSING"

#: The check does not apply to this project. NEVER confuse with a check
#: that could not be performed.
NON_APPLICABLE = "NOT_APPLICABLE"

#: A conclusion cannot be reached for lack of evidence. Different from NON_APPLICABLE.
NON_VERIFIABLE = "NOT_CHECKABLE"

#: A technical read succeeded. Does not constitute compliance or validation.
PASS_TECHNIQUE = "TECHNICAL_PASS"

#: No SIA verdict can be issued in the current state.
VERDICT_SIA_IMPOSSIBLE = "SIA_VERDICT_NOT_POSSIBLE"

CATEGORIES = (
    DEFAUT_MODELE,
    DONNEE_CLIENT_MANQUANTE,
    SORTIE_NON_ACTIVEE,
    LIMITE_VESCRIPTS,
    PREUVE_MANQUANTE,
    NON_APPLICABLE,
    NON_VERIFIABLE,
    PASS_TECHNIQUE,
    VERDICT_SIA_IMPOSSIBLE,
)

EXPLICATION_DES_CATEGORIES = {
    DEFAUT_MODELE: "Le modele VE est en cause.",
    DONNEE_CLIENT_MANQUANTE: (
        "Une donnee du projet manque. Le modele n est pas forcement fautif."
    ),
    SORTIE_NON_ACTIVEE: (
        "La grandeur n a pas ete demandee a ApacheSim. Ni le modele ni les "
        "donnees ne sont en cause."
    ),
    LIMITE_VESCRIPTS: "L API VEScripts n expose pas de quoi trancher.",
    PREUVE_MANQUANTE: "Il manque un document, pas une donnee technique.",
    NON_APPLICABLE: "Le controle ne s applique pas a ce projet.",
    NON_VERIFIABLE: "Impossible de conclure faute d element.",
    PASS_TECHNIQUE: (
        "Lecture technique reussie. Ne vaut ni conformite SIA 380/2 ni "
        "validation SIA 4010."
    ),
    VERDICT_SIA_IMPOSSIBLE: "Aucun verdict SIA ne peut etre rendu en l etat.",
}

NON_FOURNI = "NOT_PROVIDED"
EN_ATTENTE = "pending"
ACCEPTE = "accepted"

STATUTS_BATIMENT = ("NEW_BUILDING", "EXISTING_BUILDING")


# ---------------------------------------------------------------------------
# Fields requested of the reviewer
# ---------------------------------------------------------------------------
#
# `obligatoire_pour_accepter` marks fields without which the `accepted`
# status is REFUSED. The list is intentionally broader than the one
# required by `evidence_manager._normalize_project_metadata_record` downstream:
# it is better to refuse here than to let through an overly light acceptance.

CHAMPS: Tuple[Dict[str, Any], ...] = (
    {
        "nom": "project_id",
        "libelle": "Identifiant du projet",
        "aide": "Doit correspondre au dossier du projet VE actif.",
        "obligatoire_pour_accepter": True,
        "type": "texte",
    },
    {
        "nom": "building_status",
        "libelle": "Statut du batiment",
        "aide": "Decide du seuil de confort dynamique 100 h / 400 h.",
        "obligatoire_pour_accepter": True,
        "type": "choix",
        "choix": STATUTS_BATIMENT,
    },
    {
        "nom": "weather_basis",
        "libelle": "Base climatique",
        "aide": "Ex. SIA 2028 DRY. A justifier par une source.",
        "obligatoire_pour_accepter": True,
        "type": "texte",
    },
    {
        "nom": "weather_file",
        "libelle": "Fichier meteo revu",
        "aide": "Le fichier que le reviseur declare correct pour ce projet.",
        "obligatoire_pour_accepter": True,
        "type": "texte",
    },
    {
        "nom": "location",
        "libelle": "Localisation",
        "aide": "Commune ou station. Jamais deduite du nom du fichier meteo.",
        "obligatoire_pour_accepter": True,
        "type": "texte",
    },
    {
        "nom": "altitude_m",
        "libelle": "Altitude (m)",
        "aide": "Altitude du projet, en metres.",
        "obligatoire_pour_accepter": True,
        "type": "nombre",
    },
    {
        "nom": "weather_source_authority",
        "libelle": "Autorite de la source meteo",
        "aide": "Organisme ou publication qui fournit le jeu climatique.",
        "obligatoire_pour_accepter": True,
        "type": "texte",
    },
    {
        "nom": "weather_use_case",
        "libelle": "Usage du jeu climatique",
        "aide": "Le jeu doit etre adapte au controle realise ; un fichier ne convient pas automatiquement a tous les usages.",
        "obligatoire_pour_accepter": True,
        "type": "choix",
        "choix": (
            "SIA3802_COOLING_NEED",
            "SIA180_SUMMER_COMFORT",
            "HVAC_SIZING",
            "MULTIPLE_REVIEWED_USES",
        ),
    },
    {
        "nom": "weather_scenario_period",
        "libelle": "Scenario et periode climatique",
        "aide": "Ex. present SIA 2028 DRY, 2035 RCP8.5 DRY ou 2060 RCP2.6.",
        "obligatoire_pour_accepter": True,
        "type": "texte",
    },
    {
        "nom": "location_source",
        "libelle": "Source de la localisation",
        "aide": "Plan, adresse officielle, coordonnees ou station approuvee.",
        "obligatoire_pour_accepter": True,
        "type": "texte",
    },
    {
        "nom": "altitude_source",
        "libelle": "Source de l altitude",
        "aide": "Releve geometre, donnees officielles ou document de projet.",
        "obligatoire_pour_accepter": True,
        "type": "texte",
    },
    {
        "nom": "review_status",
        "libelle": "Statut de revision",
        "aide": "pending tant que les preuves sont incompletes.",
        "obligatoire_pour_accepter": True,
        "type": "choix",
        "choix": (EN_ATTENTE, ACCEPTE),
    },
    {
        "nom": "reviewer",
        "libelle": "Reviseur",
        "aide": "Personne qui engage sa responsabilite sur ces donnees.",
        "obligatoire_pour_accepter": True,
        "type": "texte",
    },
    {
        "nom": "reviewer_role",
        "libelle": "Role du reviseur",
        "aide": "Fonction exercee dans la revue technique de ce projet.",
        "obligatoire_pour_accepter": True,
        "type": "texte",
    },
    {
        "nom": "reviewer_organisation",
        "libelle": "Organisation du reviseur",
        "aide": "Entite pour laquelle le reviseur accepte la responsabilite de la preuve.",
        "obligatoire_pour_accepter": True,
        "type": "texte",
    },
    {
        "nom": "reviewer_competence_basis",
        "libelle": "Base de competence du reviseur",
        "aide": "Experience, mandat ou qualification pertinente ; le logiciel ne la deduit pas.",
        "obligatoire_pour_accepter": True,
        "type": "texte_long",
    },
    {
        "nom": "reviewer_acceptance_scope",
        "libelle": "Perimetre accepte par le reviseur",
        "aide": "Indiquer exactement quelles donnees et hypotheses sont approuvees.",
        "obligatoire_pour_accepter": True,
        "type": "texte_long",
    },
    {
        "nom": "review_date",
        "libelle": "Date de revision (AAAA-MM-JJ)",
        "aide": "Date a laquelle le reviseur a valide ces donnees.",
        "obligatoire_pour_accepter": True,
        "type": "date",
    },
    {
        "nom": "source_document",
        "libelle": "Document source",
        "aide": "Cahier des charges ou document controle.",
        "obligatoire_pour_accepter": True,
        "type": "texte",
    },
    {
        "nom": "source_reference",
        "libelle": "Reference dans la source",
        "aide": "Clause, page ou numero d approbation.",
        "obligatoire_pour_accepter": False,
        "type": "texte",
    },
    {
        "nom": "notes",
        "libelle": "Notes",
        "aide": "Tout ce qui aide un relecteur ulterieur.",
        "obligatoire_pour_accepter": False,
        "type": "texte_long",
    },
    {
        "nom": "assumptions_status",
        "libelle": "Statut des hypotheses",
        "aide": "Une hypothese ouverte reste une reserve visible dans le rapport.",
        "obligatoire_pour_accepter": True,
        "type": "choix",
        "choix": (
            "NO_UNRESOLVED_ASSUMPTIONS",
            "OPEN_ASSUMPTIONS",
            "UNDER_REVIEW",
        ),
    },
    {
        "nom": "assumptions_register",
        "libelle": "Registre des hypotheses",
        "aide": "Document et reference recensant les hypotheses, y compris celles absentes de VE.",
        "obligatoire_pour_accepter": True,
        "type": "texte_long",
    },
    {
        "nom": "report_use_acknowledgement",
        "libelle": "Reconnaissance de la portee du rapport",
        "aide": "Confirme que le resultat est une evaluation technique et non un certificat officiel SIA.",
        "obligatoire_pour_accepter": True,
        "type": "choix",
        "choix": ("ENGINEERING_ASSESSMENT_ONLY", "UNDER_REVIEW"),
    },
    # --- MODEL-003: ventilation -------------------------------------------
    {
        "nom": "ventilation_strategy",
        "libelle": "Strategie de ventilation",
        "aide": "Ce que le projet prevoit reellement.",
        "obligatoire_pour_accepter": True,
        "type": "choix",
        "choix": (
            "NATURAL_ONLY",
            "MECHANICAL_PRESENT",
            "MECHANICAL_EXPECTED",
            "UNDER_REVIEW",
        ),
    },
    {
        "nom": "ventilation_justification",
        "libelle": "Justification de l absence ou de la presence",
        "aide": "Pourquoi cette strategie ; obligatoire des qu on accepte.",
        "obligatoire_pour_accepter": True,
        "type": "texte_long",
    },
    {
        "nom": "ventilation_flow_source",
        "libelle": "Source des debits",
        "aide": "D ou viennent les debits. Jamais inventes.",
        "obligatoire_pour_accepter": False,
        "type": "texte",
    },
    {
        "nom": "ventilation_scope",
        "libelle": "Perimetre de la ventilation",
        "aide": "Systemes, zones et modes naturel/mecanique couverts par la declaration.",
        "obligatoire_pour_accepter": True,
        "type": "texte_long",
    },
    # --- MODEL-004: lighting ----------------------------------------------
    {
        "nom": "lighting_scope",
        "libelle": "Perimetre de l eclairage",
        "aide": "L eclairage fait-il partie du perimetre evalue ?",
        "obligatoire_pour_accepter": True,
        "type": "choix",
        "choix": ("IN_SCOPE", "OUT_OF_SCOPE", "UNDER_REVIEW"),
    },
    {
        "nom": "lighting_power_source",
        "libelle": "Source de la puissance",
        "aide": "Obligatoire si l eclairage est dans le perimetre.",
        "obligatoire_pour_accepter": False,
        "type": "texte",
    },
    {
        "nom": "lighting_scope_justification",
        "libelle": "Justification du perimetre eclairage",
        "aide": "Obligatoire si l eclairage est exclu ou partiellement couvert.",
        "obligatoire_pour_accepter": False,
        "type": "texte_long",
    },
    {
        "nom": "system_power_source",
        "libelle": "Source des puissances des systemes",
        "aide": "Calcul de dimensionnement ou documentation des ventilateurs, pompes, auxiliaires et batteries.",
        "obligatoire_pour_accepter": False,
        "type": "texte_long",
    },
    # --- SIM-003: ApacheSim outputs ---------------------------------------
    {
        "nom": "aps_outputs_required",
        "libelle": "Sorties fan/pump/auxiliary/coils necessaires ?",
        "aide": "NO si le systeme modelise n en produit pas — a justifier.",
        "obligatoire_pour_accepter": True,
        "type": "choix",
        "choix": ("YES", "NO", "UNDER_REVIEW"),
    },
    {
        "nom": "aps_outputs_justification",
        "libelle": "Justification des sorties APS",
        "aide": "Obligatoire quand on repond NO.",
        "obligatoire_pour_accepter": False,
        "type": "texte_long",
    },
)

#: Columns of the official template, in order. Additional fields are
#: added AFTER: `evidence_manager` reads by column name and tolerates
#: extra columns, but the template order remains human-readable.
COLONNES_GABARIT = (
    "project_id",
    "building_status",
    "weather_basis",
    "weather_file",
    "location",
    "altitude_m",
    "review_status",
    "reviewer",
    "review_date",
    "source_document",
    "source_reference",
    "notes",
)


def noms_des_champs() -> List[str]:
    """Names of all fields, in display order."""
    return [champ["nom"] for champ in CHAMPS]


def colonnes_csv() -> List[str]:
    """CSV columns: the official template, then any added fields."""
    supplementaires = [nom for nom in noms_des_champs() if nom not in COLONNES_GABARIT]
    return list(COLONNES_GABARIT) + supplementaires


def champ(nom: str) -> Dict[str, Any]:
    """Field definition.

    Raises:
        KeyError: If the field does not exist. Returning an empty dict would
            suggest a field without constraints.
    """
    for definition in CHAMPS:
        if definition["nom"] == nom:
            return definition
    raise KeyError("champ inconnu : %r" % nom)


# ---------------------------------------------------------------------------
# Pre-fill: only what is technically demonstrated
# ---------------------------------------------------------------------------


def prefill(detecte: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """Pre-filled values, limited to what is technically demonstrated.

    The `project_id` is pre-filled because it can be read from the active VE
    project folder. NOTHING ELSE is: not the location, not the altitude, not
    the climate basis, not the reviewed weather file — none is demonstrable by
    reading the model.

    In particular, the DETECTED weather file is NOT copied into `weather_file`.
    That field holds the file that the REVIEWER declares correct; conflating
    the two would amount to letting the software validate what only a human can
    declare.

    Args:
        detecte: Facts gathered in VE, e.g. `{'project_id': ...}`.

    Returns:
        dict: Field -> value, only for demonstrated fields.
    """
    detecte = detecte or {}
    valeurs = dict((nom, "") for nom in noms_des_champs())
    valeurs["review_status"] = EN_ATTENTE
    identifiant = (detecte.get("project_id") or "").strip()
    if identifiant:
        valeurs["project_id"] = identifiant
    return valeurs


def faits_techniques(detecte: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Facts gathered in VE, presented WITHOUT mixing them with the responses.

    They are displayed to inform the reviewer, never to answer on their
    behalf. Each carries its status: a detected weather file is not a
    reviewed weather file.

    Args:
        detecte: What the probe observed.

    Returns:
        dict: Facts, each with its value and status.
    """
    detecte = detecte or {}

    def fait(cle: str, statut: str, note: str) -> Dict[str, Any]:
        valeur = detecte.get(cle)
        return {
            "valeur": valeur if valeur is not None else NON_FOURNI,
            "statut": statut if valeur is not None else NON_VERIFIABLE,
            "note": note,
        }

    return {
        "project_id": fait(
            "project_id", PASS_TECHNIQUE, "Lu sur le dossier du projet VE actif."
        ),
        "aps_file": fait("aps_file", PASS_TECHNIQUE, "Fichier de resultats retenu."),
        "detected_weather_file": fait(
            "detected_weather_file",
            PASS_TECHNIQUE,
            "Detecte dans VE. Prouve une correspondance TECHNIQUE avec l APS, "
            "PAS qu il s agisse d un climat suisse approuve.",
        ),
        "total_area_m2": fait(
            "total_area_m2", PASS_TECHNIQUE, "Somme des surfaces de locaux."
        ),
        "total_heating_kwh": fait(
            "total_heating_kwh",
            PASS_TECHNIQUE,
            "Extrait via « Room units heating load » (Heating plant sensible "
            "load), jamais via la serie steady state.",
        ),
        "total_cooling_kwh": fait(
            "total_cooling_kwh",
            PASS_TECHNIQUE,
            "Extrait via « Room units cooling load ».",
        ),
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def valider_champ(nom: str, valeur: Any) -> Optional[str]:
    """Validate one value in isolation.

    Args:
        nom: Field name.
        valeur: Entered value.

    Returns:
        str | None: Reason for rejection, or `None` if the value is
        acceptable. An EMPTY value is never rejected here: incompleteness
        is handled at acceptance time, not at entry.
    """
    definition = champ(nom)
    texte = ("" if valeur is None else "%s" % valeur).strip()
    if not texte:
        return None

    if definition["type"] == "choix" and texte not in definition["choix"]:
        return "valeur hors des choix : %s" % ", ".join(definition["choix"])

    if definition["type"] == "nombre":
        try:
            float(texte.replace(",", "."))
        except ValueError:
            return "valeur numerique attendue"

    if definition["type"] == "date":
        try:
            datetime.strptime(texte, "%Y-%m-%d")
        except ValueError:
            return "date attendue au format AAAA-MM-JJ"

    return None


def valider(reponses: Dict[str, Any]) -> Dict[str, str]:
    """Validate all entered values.

    Args:
        reponses: Field -> value.

    Returns:
        dict: Field -> reason, empty if everything is acceptable.
    """
    erreurs = {}
    for nom in noms_des_champs():
        motif = valider_champ(nom, (reponses or {}).get(nom))
        if motif:
            erreurs[nom] = motif
    return erreurs


def champs_manquants(reponses: Dict[str, Any]) -> List[str]:
    """Mandatory fields that are still empty.

    Args:
        reponses: Field -> value.

    Returns:
        list[str]: Names of missing fields, in display order.
    """
    manquants = []
    for definition in CHAMPS:
        if not definition["obligatoire_pour_accepter"]:
            continue
        valeur = ("%s" % ((reponses or {}).get(definition["nom"]) or "")).strip()
        if not valeur:
            manquants.append(definition["nom"])
    return manquants


def _conditionnels(reponses: Dict[str, Any]) -> List[str]:
    """Obligations that depend on other answers.

    Args:
        reponses: Field -> value.

    Returns:
        list[str]: Reasons for rejection.
    """
    reponses = reponses or {}
    motifs = []

    def rempli(nom: str) -> bool:
        return bool(("%s" % (reponses.get(nom) or "")).strip())

    if reponses.get("lighting_scope") == "IN_SCOPE" and not rempli(
        "lighting_power_source"
    ):
        motifs.append(
            "l eclairage est declare DANS le perimetre : la source de la "
            "puissance est exigee (elle ne peut pas etre deduite du gain "
            "Miscellaneous existant)"
        )

    if reponses.get("lighting_scope") == "OUT_OF_SCOPE" and not rempli(
        "lighting_scope_justification"
    ):
        motifs.append(
            "l eclairage est declare HORS perimetre : la justification et la "
            "frontiere d evaluation sont exigees"
        )

    if reponses.get("ventilation_strategy") in (
        "MECHANICAL_PRESENT",
        "MECHANICAL_EXPECTED",
    ) and not rempli("ventilation_flow_source"):
        motifs.append(
            "une ventilation mecanique est declaree : la source des debits "
            "est exigee (ils ne s inventent pas)"
        )

    if reponses.get("aps_outputs_required") == "NO" and not rempli(
        "aps_outputs_justification"
    ):
        motifs.append(
            "les sorties APS sont declarees non necessaires : la "
            "justification est exigee, sans quoi « non applicable » et "
            "« sortie absente » deviennent indiscernables"
        )

    if reponses.get("aps_outputs_required") == "YES" and not rempli(
        "system_power_source"
    ):
        motifs.append(
            "les sorties de systemes sont requises : la source des puissances "
            "ventilateurs, pompes, auxiliaires et batteries est exigee"
        )

    if reponses.get("ventilation_strategy") == "UNDER_REVIEW":
        motifs.append("la strategie de ventilation est encore en revision")
    if reponses.get("lighting_scope") == "UNDER_REVIEW":
        motifs.append("le perimetre de l eclairage est encore en revision")
    if reponses.get("aps_outputs_required") == "UNDER_REVIEW":
        motifs.append("les sorties APS sont encore en revision")
    if reponses.get("assumptions_status") == "UNDER_REVIEW":
        motifs.append("le registre des hypotheses est encore en revision")
    if reponses.get("report_use_acknowledgement") != "ENGINEERING_ASSESSMENT_ONLY":
        motifs.append(
            "la portee juridique du rapport n est pas acceptee : le document "
            "reste une evaluation d ingenierie, pas un certificat officiel SIA"
        )

    return motifs


def evaluer_acceptation(
    reponses: Dict[str, Any],
    confirmation_utilisateur: bool = False,
) -> Dict[str, Any]:
    """Decide whether the `accepted` status can be written.

    FAIL-CLOSED. Any uncertainty reverts to `pending`. The status requested
    by the user is never taken as-is: it is RECALCULATED.

    Args:
        reponses: Field -> value.
        confirmation_utilisateur: Box explicitly checked by the reviewer.

    Returns:
        dict: `statut_effectif`, `accepte`, `motifs_de_refus`, `manquants`,
        `erreurs`.
    """
    reponses = reponses or {}
    erreurs = valider(reponses)
    manquants = champs_manquants(reponses)
    motifs = list(_conditionnels(reponses))

    demande = ("%s" % (reponses.get("review_status") or "")).strip()
    if demande != ACCEPTE:
        motifs.append("le statut demande n est pas « accepted »")
    if erreurs:
        motifs.append("valeurs invalides : %s" % ", ".join(sorted(erreurs)))
    if manquants:
        motifs.append("champs obligatoires vides : %s" % ", ".join(manquants))
    if not confirmation_utilisateur:
        motifs.append("confirmation explicite du reviseur absente")

    accepte = not motifs
    return {
        "statut_effectif": ACCEPTE if accepte else EN_ATTENTE,
        "accepte": accepte,
        "motifs_de_refus": motifs,
        "manquants": manquants,
        "erreurs": erreurs,
    }


# ---------------------------------------------------------------------------
# Weather matching
# ---------------------------------------------------------------------------


def correspondance_meteo(detecte: Optional[str], revu: Optional[str]) -> Dict[str, Any]:
    """Compare the detected weather file with the one the reviewer declares.

    A match does NOT mean climate approval: it only says the reviewer is
    referring to the same file as VE. `DRYCOLD_IESVE.epw` can match
    perfectly and still not be an approved Swiss climate.

    Args:
        detecte: Weather file read from VE.
        revu: Weather file declared by the reviewer.

    Returns:
        dict: `detecte`, `revu`, `statut`, `note`.
    """
    detecte_nu = (detecte or "").strip()
    revu_nu = (revu or "").strip()

    if not revu_nu:
        statut = NON_VERIFIABLE
        note = (
            "Aucun fichier meteo revu : impossible de dire si VE utilise "
            "celui que le projet exige."
        )
    elif not detecte_nu:
        statut = NON_VERIFIABLE
        note = "Aucun fichier meteo detecte dans VE."
    elif os.path.basename(detecte_nu).lower() == os.path.basename(revu_nu).lower():
        statut = PASS_TECHNIQUE
        note = (
            "VE utilise le fichier declare par le reviseur. Cela ne dit "
            "RIEN de l approbation du climat lui-meme."
        )
    else:
        statut = DEFAUT_MODELE
        note = (
            "VE utilise « %s » alors que le reviseur declare « %s ». "
            "L un des deux est a corriger." % (detecte_nu, revu_nu)
        )

    return {
        "detecte": detecte_nu or NON_FOURNI,
        "revu": revu_nu or NON_FOURNI,
        "statut": statut,
        "note": note,
    }


# ---------------------------------------------------------------------------
# Writing: evidence CSV, and audit JSON
# ---------------------------------------------------------------------------


def sauvegarder_avant_ecriture(
    chemin: str, horodatage: Optional[str] = None
) -> Optional[str]:
    """Copy an existing file before overwriting it.

    Args:
        chemin: File to preserve.
        horodatage: Imposed suffix; otherwise the current time.

    Returns:
        str | None: Path of the backup, or `None` if nothing to preserve.
    """
    if not os.path.exists(chemin):
        return None
    marque = horodatage or datetime.now().strftime("%Y%m%d_%H%M%S")
    racine, extension = os.path.splitext(chemin)
    sauvegarde = "%s.backup_%s%s" % (racine, marque, extension)
    shutil.copy2(chemin, sauvegarde)
    return sauvegarde


def ecrire_csv(
    chemin: str,
    reponses: Dict[str, Any],
    statut_effectif: str,
    horodatage: Optional[str] = None,
) -> Dict[str, Any]:
    """Write the evidence CSV, after backing up any existing file.

    The written status is the one RECALCULATED by `evaluer_acceptation`,
    never the one requested by the user.

    Args:
        chemin: CSV file to write.
        reponses: Field -> value.
        statut_effectif: Recalculated status.
        horodatage: Imposed backup suffix.

    Returns:
        dict: `chemin`, `sauvegarde`, `colonnes`.
    """
    dossier = os.path.dirname(chemin)
    if dossier and not os.path.isdir(dossier):
        os.makedirs(dossier)

    sauvegarde = sauvegarder_avant_ecriture(chemin, horodatage)
    colonnes = colonnes_csv()
    ligne = {}
    for nom in colonnes:
        valeur = (reponses or {}).get(nom, "")
        ligne[nom] = ("" if valeur is None else "%s" % valeur).strip()
    ligne["review_status"] = statut_effectif

    with io.open(chemin, "w", encoding="utf-8", newline="") as flux:
        redacteur = csv.DictWriter(flux, fieldnames=colonnes)
        redacteur.writeheader()
        redacteur.writerow(ligne)

    return {"chemin": chemin, "sauvegarde": sauvegarde, "colonnes": colonnes}


def construire_audit(
    reponses: Dict[str, Any],
    detecte: Optional[Dict[str, Any]],
    acceptation: Dict[str, Any],
    actions_restantes: Sequence[str],
    chemin_csv: str,
    sauvegarde: Optional[str] = None,
    horodatage: Optional[str] = None,
) -> Dict[str, Any]:
    """Compose the audit JSON.

    Args:
        reponses: Field -> value.
        detecte: Facts gathered in VE.
        acceptation: What `evaluer_acceptation` returns.
        actions_restantes: Remaining actions.
        chemin_csv: Written CSV.
        sauvegarde: Optional backup.
        horodatage: Imposed timestamp.

    Returns:
        dict: Audit structure.
    """
    detecte = detecte or {}
    marque = horodatage or datetime.now().strftime("%Y%m%d_%H%M%S")
    meteo = correspondance_meteo(
        detecte.get("detected_weather_file"), (reponses or {}).get("weather_file")
    )
    return {
        "schema_version": "1.0",
        "generated_at": marque,
        "purpose": (
            "Collecte de preuves pour une evaluation SIA 380/2 d un modele "
            "client. NE constitue ni une declaration de conformite SIA 380/2, "
            "ni une validation SIA 4010 du logiciel."
        ),
        "ve_data_modified": False,
        "ve_data_modified_note": (
            "Aucune donnee VE n a ete modifiee. Cet assistant lit le modele "
            "et ecrit des fichiers de preuve ; il ne mute rien."
        ),
        "project_id": (reponses or {}).get("project_id") or NON_FOURNI,
        "responses": dict(
            (nom, (reponses or {}).get(nom, "") or "") for nom in noms_des_champs()
        ),
        "missing_fields": list(acceptation.get("manquants") or []),
        "field_errors": dict(acceptation.get("erreurs") or {}),
        "sources": {
            "source_document": (reponses or {}).get("source_document") or NON_FOURNI,
            "source_reference": (reponses or {}).get("source_reference") or NON_FOURNI,
            "ventilation_flow_source": (
                (reponses or {}).get("ventilation_flow_source") or NON_FOURNI
            ),
            "lighting_power_source": (
                (reponses or {}).get("lighting_power_source") or NON_FOURNI
            ),
        },
        "review": {
            "reviewer": (reponses or {}).get("reviewer") or NON_FOURNI,
            "review_date": (reponses or {}).get("review_date") or NON_FOURNI,
            "requested_status": (reponses or {}).get("review_status") or NON_FOURNI,
            "effective_status": acceptation.get("statut_effectif"),
            "accepted": bool(acceptation.get("accepte")),
            "refusal_reasons": list(acceptation.get("motifs_de_refus") or []),
        },
        "weather": {
            "detected_in_ve": meteo["detecte"],
            "reviewed": meteo["revu"],
            "match_status": meteo["statut"],
            "note": meteo["note"],
        },
        "technical_facts": faits_techniques(detecte),
        "remaining_actions": list(actions_restantes),
        "evidence_csv": {"path": chemin_csv, "backup": sauvegarde},
        "guardrail": (
            "PASS technique, conformite SIA 380/2 et validation SIA 4010 sont "
            "trois choses distinctes. Ce fichier ne prononce aucune des deux "
            "dernieres."
        ),
    }


def ecrire_audit(
    dossier: str, audit: Dict[str, Any], project_id: str, horodatage: Optional[str] = None
) -> str:
    """Write the audit JSON, without ever overwriting an existing file.

    Args:
        dossier: `sia_compliance_artifacts/evidence/` folder.
        audit: Structure to write.
        project_id: Identifier, for the filename.
        horodatage: Imposed timestamp.

    Returns:
        str: Written path.
    """
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    marque = (
        horodatage
        or audit.get("generated_at")
        or datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    nom = "SIA3802_evidence_audit_%s_%s.json" % (
        (project_id or "UNKNOWN").strip() or "UNKNOWN",
        marque,
    )
    chemin = os.path.join(dossier, nom)
    with io.open(chemin, "w", encoding="utf-8") as flux:
        flux.write(json.dumps(audit, ensure_ascii=False, indent=2))
        flux.write("\n")
    return chemin


# ---------------------------------------------------------------------------
# Remaining actions, by finding type
# ---------------------------------------------------------------------------
#
# Each action carries its CATEGORY. This is what prevents confusing a model
# defect with a missing client datum, or a disabled ApacheSim output with a
# non-applicable check — three situations that call for three different
# responses, from three different people.


def actions_ventilation(
    reponses: Dict[str, Any], constat: Optional[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """Actions for MODEL-003, according to the declared strategy.

    Args:
        reponses: Field -> value.
        constat: What the probe observed, e.g.
            `{'infiltration_only': True, 'oa_max_flow': 0.0}`.

    Returns:
        list[dict]: Actions, each with its category.
    """
    reponses = reponses or {}
    constat = constat or {}
    strategie = reponses.get("ventilation_strategy") or ""
    actions = []

    if constat.get("infiltration_only") is True:
        actions.append(
            {
                "controle": "MODEL-003",
                "categorie": PASS_TECHNIQUE,
                "constat": "Les locaux ne portent qu une infiltration.",
                "action": "Aucune — c est une lecture du modele, pas un defaut.",
            }
        )
    elif constat.get("infiltration_only") is None:
        actions.append(
            {
                "controle": "MODEL-003",
                "categorie": NON_VERIFIABLE,
                "constat": "Composition des echanges d air non relevee.",
                "action": "Relancer la sonde sur le projet actif.",
            }
        )

    debit = constat.get("oa_max_flow")
    if debit is None:
        actions.append(
            {
                "controle": "MODEL-003",
                "categorie": LIMITE_VESCRIPTS,
                "constat": "OA_max_flow non expose par l API pour ces locaux.",
                "action": (
                    "Verifier le debit d air neuf dans l interface VE ; "
                    "l API ne permet pas de le confirmer ici."
                ),
            }
        )
    elif float(debit) == 0.0:
        actions.append(
            {
                "controle": "MODEL-003",
                "categorie": PASS_TECHNIQUE,
                "constat": "OA_max_flow = 0 : aucun air neuf mecanique.",
                "action": "Aucune — coherent avec une infiltration seule.",
            }
        )

    if strategie == "NATURAL_ONLY":
        justifiee = bool((reponses.get("ventilation_justification") or "").strip())
        actions.append(
            {
                "controle": "MODEL-003",
                "categorie": PASS_TECHNIQUE if justifiee else PREUVE_MANQUANTE,
                "constat": "Ventilation naturelle declaree.",
                "action": (
                    "Conserver la justification au dossier ; aucune "
                    "modification du modele n est requise."
                ),
            }
        )
    elif strategie in ("MECHANICAL_PRESENT", "MECHANICAL_EXPECTED"):
        actions.append(
            {
                "controle": "MODEL-003",
                "categorie": DEFAUT_MODELE,
                "constat": (
                    "Une ventilation mecanique est attendue, mais les "
                    "locaux ne portent qu une infiltration."
                ),
                "action": (
                    "Dans VE : Building Template Manager > Air Exchanges, "
                    "ajouter un echange de type Auxiliary Ventilation ou "
                    "Natural Ventilation selon le systeme reel, renseigner "
                    "son debit et son profil depuis la source declaree, "
                    "puis relancer ApacheSim. NE PAS creer cet echange "
                    "automatiquement : le debit ne s invente pas."
                ),
            }
        )
    else:
        actions.append(
            {
                "controle": "MODEL-003",
                "categorie": DONNEE_CLIENT_MANQUANTE,
                "constat": "Strategie de ventilation non tranchee.",
                "action": "Faire trancher la strategie par le client ou le CVC.",
            }
        )
    return actions


def actions_eclairage(
    reponses: Dict[str, Any], constat: Optional[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """Actions for MODEL-004, according to the declared scope.

    Args:
        reponses: Field -> value.
        constat: Observations, e.g.
            `{'lighting_gain_present': False, 'misc_gain_w_m2': 5.0}`.

    Returns:
        list[dict]: Actions, each with its category.
    """
    reponses = reponses or {}
    constat = constat or {}
    perimetre = reponses.get("lighting_scope") or ""
    actions = []

    if constat.get("lighting_gain_present") is False:
        misc = constat.get("misc_gain_w_m2")
        detail = (
            "" if misc is None else " Un gain Miscellaneous de %s W/m2 existe." % misc
        )
        actions.append(
            {
                "controle": "MODEL-004",
                "categorie": PASS_TECHNIQUE,
                "constat": "Aucun gain VE de type Lighting.%s" % detail,
                "action": (
                    "Aucune — et NE PAS convertir le gain Miscellaneous en "
                    "Lighting : ce sont deux grandeurs distinctes, et la "
                    "conversion fabriquerait une puissance d eclairage."
                ),
            }
        )

    if perimetre == "OUT_OF_SCOPE":
        actions.append(
            {
                "controle": "MODEL-004",
                "categorie": NON_APPLICABLE,
                "constat": "L eclairage est hors du perimetre evalue.",
                "action": "Aucune. Conserver la justification au dossier.",
            }
        )
    elif perimetre == "IN_SCOPE":
        actions.append(
            {
                "controle": "MODEL-004",
                "categorie": DONNEE_CLIENT_MANQUANTE,
                "constat": "L eclairage est dans le perimetre mais non modelise.",
                "action": (
                    "Obtenir du client la puissance installee (W/m2), le "
                    "profil horaire et leur source. Puis, dans VE : "
                    "Building Template Manager > Internal Gains, ajouter "
                    "un gain de type Lighting et relancer ApacheSim. NE "
                    "PAS deduire la puissance du gain Miscellaneous."
                ),
            }
        )
    else:
        actions.append(
            {
                "controle": "MODEL-004",
                "categorie": DONNEE_CLIENT_MANQUANTE,
                "constat": "Perimetre de l eclairage non tranche.",
                "action": "Faire trancher le perimetre par le client.",
            }
        )
    return actions


#: APS outputs that the probe declares absent, and where to enable them in VE.
OU_ACTIVER_LES_SORTIES = {
    "lighting": "ApacheSim > Results, cocher les consommations d eclairage.",
    "fan": "ApacheSim > Results, energies de ventilateurs (niveau systeme).",
    "pump": "ApacheSim > Results, energies de pompes.",
    "auxiliary": "ApacheSim > Results, energies auxiliaires.",
    "heating_coil": "ApacheSim > Results, charge de la batterie chaude.",
    "cooling_coil": "ApacheSim > Results, charge de la batterie froide.",
}


def actions_sorties_aps(
    reponses: Dict[str, Any], absentes: Sequence[str]
) -> List[Dict[str, str]]:
    """Actions for SIM-003, without ever converting an absence to zero.

    CENTRAL DISTINCTION. An output absent because the modelled system does
    not produce it is NOT_APPLICABLE. The same output absent because
    ApacheSim did not produce it is SORTIE_NON_ACTIVEE. The two are corrected
    differently, and neither equals zero.

    Args:
        reponses: Field -> value.
        absentes: Quantities without an APS binding.

    Returns:
        list[dict]: Actions, each with its category.
    """
    reponses = reponses or {}
    besoin = reponses.get("aps_outputs_required") or ""
    actions = []

    if not absentes:
        return [
            {
                "controle": "SIM-003",
                "categorie": PASS_TECHNIQUE,
                "constat": "Toutes les sorties attendues sont presentes.",
                "action": "Aucune.",
            }
        ]

    if besoin == "NO":
        actions.append(
            {
                "controle": "SIM-003",
                "categorie": NON_APPLICABLE,
                "constat": (
                    "Sorties absentes : %s. Le reviseur declare qu elles "
                    "ne s appliquent pas au systeme modelise." % ", ".join(absentes)
                ),
                "action": (
                    "Aucune. Conserver la justification. Ces grandeurs "
                    "restent ABSENTES, elles ne valent pas zero."
                ),
            }
        )
        return actions

    if besoin == "YES":
        for grandeur in absentes:
            actions.append(
                {
                    "controle": "SIM-003",
                    "categorie": SORTIE_NON_ACTIVEE,
                    "constat": "Sortie « %s » absente de l APS." % grandeur,
                    "action": OU_ACTIVER_LES_SORTIES.get(
                        grandeur, "Activer cette sortie dans ApacheSim, puis relancer."
                    ),
                }
            )
        actions.append(
            {
                "controle": "SIM-003",
                "categorie": SORTIE_NON_ACTIVEE,
                "constat": "Apres activation, l APS doit etre regenere.",
                "action": (
                    "Relancer ApacheSim sur l annee complete, puis "
                    "relancer la sonde. Ne PAS combler les series "
                    "manquantes par des zeros."
                ),
            }
        )
        return actions

    actions.append(
        {
            "controle": "SIM-003",
            "categorie": NON_VERIFIABLE,
            "constat": (
                "Sorties absentes : %s. Leur necessite n est pas "
                "tranchee." % ", ".join(absentes)
            ),
            "action": (
                "Determiner si le systeme modelise produit ces grandeurs. "
                "Tant que ce n est pas tranche, « non applicable » et "
                "« sortie non activee » restent indiscernables."
            ),
        }
    )
    return actions


def actions_preuves(acceptation: Dict[str, Any]) -> List[Dict[str, str]]:
    """Actions for EVID-001, on documentary evidence.

    Args:
        acceptation: What `evaluer_acceptation` returns.

    Returns:
        list[dict]: Actions.
    """
    if acceptation.get("accepte"):
        return [
            {
                "controle": "EVID-001",
                "categorie": PASS_TECHNIQUE,
                "constat": "Metadonnees completes et acceptees par un reviseur.",
                "action": "Aucune.",
            }
        ]
    return [
        {
            "controle": "EVID-001",
            "categorie": PREUVE_MANQUANTE,
            "constat": (
                "Metadonnees incompletes : %s"
                % "; ".join(acceptation.get("motifs_de_refus") or [])
            ),
            "action": (
                "Completer les champs manquants dans l assistant, puis "
                "cocher la confirmation explicite."
            ),
        }
    ]


def actions_restantes(
    reponses: Dict[str, Any],
    detecte: Optional[Dict[str, Any]],
    acceptation: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Assemble all actions, and conclude on the SIA verdict.

    Args:
        reponses: Field -> value.
        detecte: Probe observations.
        acceptation: What `evaluer_acceptation` returns.

    Returns:
        list[dict]: Ordered actions, with the conclusion last.
    """
    detecte = detecte or {}
    actions = []
    actions.extend(actions_ventilation(reponses, detecte.get("ventilation")))
    actions.extend(actions_eclairage(reponses, detecte.get("lighting")))
    actions.extend(
        actions_sorties_aps(reponses, detecte.get("missing_aps_outputs") or ())
    )
    actions.extend(actions_preuves(acceptation))

    meteo = correspondance_meteo(
        detecte.get("detected_weather_file"), (reponses or {}).get("weather_file")
    )
    actions.append(
        {
            "controle": "EVID-002",
            "categorie": meteo["statut"],
            "constat": "Meteo VE < %s > / revue < %s >."
            % (meteo["detecte"], meteo["revu"]),
            "action": meteo["note"],
        }
    )

    bloquants = [
        a
        for a in actions
        if a["categorie"]
        in (
            DEFAUT_MODELE,
            DONNEE_CLIENT_MANQUANTE,
            PREUVE_MANQUANTE,
            NON_VERIFIABLE,
            SORTIE_NON_ACTIVEE,
        )
    ]
    if bloquants or not acceptation.get("accepte"):
        actions.append(
            {
                "controle": "SIA-380-2",
                "categorie": VERDICT_SIA_IMPOSSIBLE,
                "constat": "%d point(s) bloquant(s) subsistent." % len(bloquants),
                "action": (
                    "Aucun verdict de conformite SIA 380/2 ne peut etre "
                    "rendu. Les PASS techniques ci-dessus n y suffisent "
                    "pas, et la validation SIA 4010 du logiciel est une "
                    "question distincte."
                ),
            }
        )
    else:
        actions.append(
            {
                "controle": "SIA-380-2",
                "categorie": NON_VERIFIABLE,
                "constat": "Aucun point bloquant recense par cet assistant.",
                "action": (
                    "Les preuves collectees sont completes. Le verdict de "
                    "conformite reste du ressort d un ingenieur : cet "
                    "assistant ne le prononce pas."
                ),
            }
        )
    return actions
