# -*- coding: utf-8 -*-
"""Collecte des preuves SIA 380/2 d'un modele client — noyau pur.

DEUX CHOSES QU IL NE FAUT PAS CONFONDRE, et ce module existe pour les tenir
separees :

    SIA 4010  valide le LOGICIEL et ses methodes. C est le travail sur les
              sept tests de reference, dans refs/ et engine/. Il ne dit rien
              d un batiment client.
    SIA 380/2 juge la conformite d un BATIMENT client. C est l objet de ce
              module. Un logiciel valide n y suffit pas : il y faut les
              donnees du projet et des preuves documentaires.

Un PASS technique — un APS lisible, une extraction reussie — n est ni l un ni
l autre. Les trois vocabulaires sont distincts et le restent partout ici.

CE QUE CE MODULE NE FAIT JAMAIS
    - inventer une valeur reglementaire, une localisation, une altitude, un
      debit de ventilation, une puissance d eclairage ;
    - remplacer une donnee manquante par zero ;
    - declarer un batiment conforme ;
    - modifier le modele VE.

Python pur : ni `iesve`, ni `tkinter`. Testable en integration continue.
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
# Vocabulaire des statuts
# ---------------------------------------------------------------------------
#
# Ces sept valeurs ne sont pas des synonymes. Les confondre est precisement ce
# qui produit une fausse declaration de conformite.

#: Le modele VE est en cause : quelque chose y manque ou y est faux.
DEFAUT_MODELE = "MODEL_DEFECT"

#: Le modele est peut-etre correct, mais une donnee du client manque pour en
#: juger. Ce n est pas un defaut du modele.
DONNEE_CLIENT_MANQUANTE = "CLIENT_DATA_MISSING"

#: La grandeur n a pas ete demandee a ApacheSim. Le modele et les donnees
#: peuvent etre parfaits.
SORTIE_NON_ACTIVEE = "SIM_OUTPUT_NOT_ENABLED"

#: L API VEScripts n expose pas ce qu il faudrait pour trancher.
LIMITE_VESCRIPTS = "VESCRIPT_LIMITATION"

#: Il manque un document, pas une donnee technique.
PREUVE_MANQUANTE = "DOCUMENTARY_EVIDENCE_MISSING"

#: Le controle ne s applique pas a ce projet. A ne JAMAIS confondre avec un
#: controle qu on n a pas su faire.
NON_APPLICABLE = "NOT_APPLICABLE"

#: On ne peut pas conclure, faute d element. Different de NON_APPLICABLE.
NON_VERIFIABLE = "NOT_CHECKABLE"

#: Une lecture technique a reussi. Ne vaut ni conformite ni validation.
PASS_TECHNIQUE = "TECHNICAL_PASS"

#: Aucun verdict SIA ne peut etre rendu en l etat.
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
        "Une donnee du projet manque. Le modele n est pas forcement fautif."),
    SORTIE_NON_ACTIVEE: (
        "La grandeur n a pas ete demandee a ApacheSim. Ni le modele ni les "
        "donnees ne sont en cause."),
    LIMITE_VESCRIPTS: "L API VEScripts n expose pas de quoi trancher.",
    PREUVE_MANQUANTE: "Il manque un document, pas une donnee technique.",
    NON_APPLICABLE: "Le controle ne s applique pas a ce projet.",
    NON_VERIFIABLE: "Impossible de conclure faute d element.",
    PASS_TECHNIQUE: (
        "Lecture technique reussie. Ne vaut ni conformite SIA 380/2 ni "
        "validation SIA 4010."),
    VERDICT_SIA_IMPOSSIBLE: "Aucun verdict SIA ne peut etre rendu en l etat.",
}

NON_FOURNI = "NOT_PROVIDED"
EN_ATTENTE = "pending"
ACCEPTE = "accepted"

STATUTS_BATIMENT = ("NEW_BUILDING", "EXISTING_BUILDING")


# ---------------------------------------------------------------------------
# Champs demandes au reviseur
# ---------------------------------------------------------------------------
#
# `obligatoire_pour_accepter` marque les champs sans lesquels le statut
# `accepted` est REFUSE. La liste est volontairement plus large que celle
# qu exige `evidence_manager._normalize_project_metadata_record` en aval :
# mieux vaut refuser ici que laisser passer une acceptation trop legere.

CHAMPS: Tuple[Dict[str, Any], ...] = (
    {"nom": "project_id", "libelle": "Identifiant du projet",
     "aide": "Doit correspondre au dossier du projet VE actif.",
     "obligatoire_pour_accepter": True, "type": "texte"},
    {"nom": "building_status", "libelle": "Statut du batiment",
     "aide": "Decide du seuil de confort dynamique 100 h / 400 h.",
     "obligatoire_pour_accepter": True, "type": "choix",
     "choix": STATUTS_BATIMENT},
    {"nom": "weather_basis", "libelle": "Base climatique",
     "aide": "Ex. SIA 2028 DRY. A justifier par une source.",
     "obligatoire_pour_accepter": True, "type": "texte"},
    {"nom": "weather_file", "libelle": "Fichier meteo revu",
     "aide": "Le fichier que le reviseur declare correct pour ce projet.",
     "obligatoire_pour_accepter": True, "type": "texte"},
    {"nom": "location", "libelle": "Localisation",
     "aide": "Commune ou station. Jamais deduite du nom du fichier meteo.",
     "obligatoire_pour_accepter": True, "type": "texte"},
    {"nom": "altitude_m", "libelle": "Altitude (m)",
     "aide": "Altitude du projet, en metres.",
     "obligatoire_pour_accepter": True, "type": "nombre"},
    {"nom": "review_status", "libelle": "Statut de revision",
     "aide": "pending tant que les preuves sont incompletes.",
     "obligatoire_pour_accepter": True, "type": "choix",
     "choix": (EN_ATTENTE, ACCEPTE)},
    {"nom": "reviewer", "libelle": "Reviseur",
     "aide": "Personne qui engage sa responsabilite sur ces donnees.",
     "obligatoire_pour_accepter": True, "type": "texte"},
    {"nom": "review_date", "libelle": "Date de revision (AAAA-MM-JJ)",
     "aide": "Date a laquelle le reviseur a valide ces donnees.",
     "obligatoire_pour_accepter": True, "type": "date"},
    {"nom": "source_document", "libelle": "Document source",
     "aide": "Cahier des charges ou document controle.",
     "obligatoire_pour_accepter": True, "type": "texte"},
    {"nom": "source_reference", "libelle": "Reference dans la source",
     "aide": "Clause, page ou numero d approbation.",
     "obligatoire_pour_accepter": False, "type": "texte"},
    {"nom": "notes", "libelle": "Notes",
     "aide": "Tout ce qui aide un relecteur ulterieur.",
     "obligatoire_pour_accepter": False, "type": "texte_long"},

    # --- MODEL-003 : ventilation -------------------------------------------
    {"nom": "ventilation_strategy", "libelle": "Strategie de ventilation",
     "aide": "Ce que le projet prevoit reellement.",
     "obligatoire_pour_accepter": True, "type": "choix",
     "choix": ("NATURAL_ONLY", "MECHANICAL_PRESENT", "MECHANICAL_EXPECTED",
               "UNDER_REVIEW")},
    {"nom": "ventilation_justification",
     "libelle": "Justification de l absence ou de la presence",
     "aide": "Pourquoi cette strategie ; obligatoire des qu on accepte.",
     "obligatoire_pour_accepter": True, "type": "texte_long"},
    {"nom": "ventilation_flow_source", "libelle": "Source des debits",
     "aide": "D ou viennent les debits. Jamais inventes.",
     "obligatoire_pour_accepter": False, "type": "texte"},

    # --- MODEL-004 : eclairage ---------------------------------------------
    {"nom": "lighting_scope", "libelle": "Perimetre de l eclairage",
     "aide": "L eclairage fait-il partie du perimetre evalue ?",
     "obligatoire_pour_accepter": True, "type": "choix",
     "choix": ("IN_SCOPE", "OUT_OF_SCOPE", "UNDER_REVIEW")},
    {"nom": "lighting_power_source", "libelle": "Source de la puissance",
     "aide": "Obligatoire si l eclairage est dans le perimetre.",
     "obligatoire_pour_accepter": False, "type": "texte"},

    # --- SIM-003 : sorties ApacheSim ---------------------------------------
    {"nom": "aps_outputs_required",
     "libelle": "Sorties fan/pump/auxiliary/coils necessaires ?",
     "aide": "NO si le systeme modelise n en produit pas — a justifier.",
     "obligatoire_pour_accepter": True, "type": "choix",
     "choix": ("YES", "NO", "UNDER_REVIEW")},
    {"nom": "aps_outputs_justification",
     "libelle": "Justification des sorties APS",
     "aide": "Obligatoire quand on repond NO.",
     "obligatoire_pour_accepter": False, "type": "texte_long"},
)

#: Colonnes du gabarit officiel, dans leur ordre. Les champs supplementaires
#: sont ajoutes APRES : `evidence_manager` lit par nom de colonne et tolere
#: les colonnes en trop, mais l ordre du gabarit reste lisible a l oeil.
COLONNES_GABARIT = (
    "project_id", "building_status", "weather_basis", "weather_file",
    "location", "altitude_m", "review_status", "reviewer", "review_date",
    "source_document", "source_reference", "notes",
)


def noms_des_champs() -> List[str]:
    """Noms de tous les champs, dans l ordre d affichage."""
    return [champ["nom"] for champ in CHAMPS]


def colonnes_csv() -> List[str]:
    """Colonnes du CSV : le gabarit officiel, puis les champs ajoutes."""
    supplementaires = [nom for nom in noms_des_champs()
                       if nom not in COLONNES_GABARIT]
    return list(COLONNES_GABARIT) + supplementaires


def champ(nom: str) -> Dict[str, Any]:
    """Definition d un champ.

    Raises:
        KeyError: Si le champ n existe pas. Rendre un dict vide laisserait
            croire a un champ sans contrainte.
    """
    for definition in CHAMPS:
        if definition["nom"] == nom:
            return definition
    raise KeyError("champ inconnu : %r" % nom)


# ---------------------------------------------------------------------------
# Pre-remplissage : uniquement ce qui est techniquement demontre
# ---------------------------------------------------------------------------

def prefill(detecte: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """Valeurs pre-remplies, limitees a ce qui est techniquement demontre.

    Le `project_id` est pre-rempli car il se lit sur le dossier du projet VE
    actif. RIEN D AUTRE ne l est : ni la localisation, ni l altitude, ni la
    base climatique, ni le fichier meteo revu — aucun n est demontrable par
    lecture du modele.

    En particulier, le fichier meteo DETECTE n est PAS recopie dans
    `weather_file`. Ce champ porte le fichier que le REVISEUR declare correct ;
    les confondre reviendrait a faire valider par le logiciel ce que seul un
    humain peut declarer.

    Args:
        detecte: Faits releves dans VE, ex. `{'project_id': ...}`.

    Returns:
        dict: Champ -> valeur, uniquement pour les champs demontres.
    """
    detecte = detecte or {}
    valeurs = dict((nom, "") for nom in noms_des_champs())
    valeurs["review_status"] = EN_ATTENTE
    identifiant = (detecte.get("project_id") or "").strip()
    if identifiant:
        valeurs["project_id"] = identifiant
    return valeurs


def faits_techniques(detecte: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Faits releves dans VE, presentes SANS les melanger aux reponses.

    Ils s affichent pour informer le reviseur, jamais pour repondre a sa
    place. Chacun porte son statut : un fichier meteo detecte n est pas un
    fichier meteo revu.

    Args:
        detecte: Ce que la sonde a releve.

    Returns:
        dict: Faits, chacun avec sa valeur et son statut.
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
        "project_id": fait("project_id", PASS_TECHNIQUE,
                           "Lu sur le dossier du projet VE actif."),
        "aps_file": fait("aps_file", PASS_TECHNIQUE,
                         "Fichier de resultats retenu."),
        "detected_weather_file": fait(
            "detected_weather_file", PASS_TECHNIQUE,
            "Detecte dans VE. Prouve une correspondance TECHNIQUE avec l APS, "
            "PAS qu il s agisse d un climat suisse approuve."),
        "total_area_m2": fait("total_area_m2", PASS_TECHNIQUE,
                              "Somme des surfaces de locaux."),
        "total_heating_kwh": fait(
            "total_heating_kwh", PASS_TECHNIQUE,
            "Extrait via « Room units heating load » (Heating plant sensible "
            "load), jamais via la serie steady state."),
        "total_cooling_kwh": fait("total_cooling_kwh", PASS_TECHNIQUE,
                                  "Extrait via « Room units cooling load »."),
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def valider_champ(nom: str, valeur: Any) -> Optional[str]:
    """Controle une valeur isolee.

    Args:
        nom: Nom du champ.
        valeur: Valeur saisie.

    Returns:
        str | None: Motif du refus, ou `None` si la valeur convient. Une
        valeur VIDE n est jamais refusee ici : l incompletude se traite au
        moment d accepter, pas a la saisie.
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
    """Controle toutes les valeurs saisies.

    Args:
        reponses: Champ -> valeur.

    Returns:
        dict: Champ -> motif, vide si tout convient.
    """
    erreurs = {}
    for nom in noms_des_champs():
        motif = valider_champ(nom, (reponses or {}).get(nom))
        if motif:
            erreurs[nom] = motif
    return erreurs


def champs_manquants(reponses: Dict[str, Any]) -> List[str]:
    """Champs obligatoires encore vides.

    Args:
        reponses: Champ -> valeur.

    Returns:
        list[str]: Noms des champs manquants, dans l ordre d affichage.
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
    """Obligations qui dependent d autres reponses.

    Args:
        reponses: Champ -> valeur.

    Returns:
        list[str]: Motifs de refus.
    """
    reponses = reponses or {}
    motifs = []

    def rempli(nom: str) -> bool:
        return bool(("%s" % (reponses.get(nom) or "")).strip())

    if reponses.get("lighting_scope") == "IN_SCOPE" and not rempli(
            "lighting_power_source"):
        motifs.append(
            "l eclairage est declare DANS le perimetre : la source de la "
            "puissance est exigee (elle ne peut pas etre deduite du gain "
            "Miscellaneous existant)")

    if reponses.get("ventilation_strategy") in (
            "MECHANICAL_PRESENT", "MECHANICAL_EXPECTED") and not rempli(
                "ventilation_flow_source"):
        motifs.append(
            "une ventilation mecanique est declaree : la source des debits "
            "est exigee (ils ne s inventent pas)")

    if reponses.get("aps_outputs_required") == "NO" and not rempli(
            "aps_outputs_justification"):
        motifs.append(
            "les sorties APS sont declarees non necessaires : la "
            "justification est exigee, sans quoi « non applicable » et "
            "« sortie absente » deviennent indiscernables")

    if reponses.get("ventilation_strategy") == "UNDER_REVIEW":
        motifs.append("la strategie de ventilation est encore en revision")
    if reponses.get("lighting_scope") == "UNDER_REVIEW":
        motifs.append("le perimetre de l eclairage est encore en revision")
    if reponses.get("aps_outputs_required") == "UNDER_REVIEW":
        motifs.append("les sorties APS sont encore en revision")

    return motifs


def evaluer_acceptation(
    reponses: Dict[str, Any],
    confirmation_utilisateur: bool = False,
) -> Dict[str, Any]:
    """Decide si le statut `accepted` peut etre ecrit.

    FAIL-CLOSED. Toute incertitude ramene a `pending`. Le statut demande par
    l utilisateur n est jamais repris tel quel : il est RECALCULE.

    Args:
        reponses: Champ -> valeur.
        confirmation_utilisateur: Case cochee explicitement par le reviseur.

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
# Correspondance meteo
# ---------------------------------------------------------------------------

def correspondance_meteo(detecte: Optional[str],
                         revu: Optional[str]) -> Dict[str, Any]:
    """Compare le fichier meteo detecte et celui que le reviseur declare.

    Une correspondance ne vaut PAS approbation du climat : elle dit seulement
    que le reviseur parle du meme fichier que VE. `DRYCOLD_IESVE.epw` peut
    correspondre parfaitement et n etre en rien un climat suisse approuve.

    Args:
        detecte: Fichier meteo lu dans VE.
        revu: Fichier meteo declare par le reviseur.

    Returns:
        dict: `detecte`, `revu`, `statut`, `note`.
    """
    detecte_nu = (detecte or "").strip()
    revu_nu = (revu or "").strip()

    if not revu_nu:
        statut = NON_VERIFIABLE
        note = ("Aucun fichier meteo revu : impossible de dire si VE utilise "
                "celui que le projet exige.")
    elif not detecte_nu:
        statut = NON_VERIFIABLE
        note = "Aucun fichier meteo detecte dans VE."
    elif os.path.basename(detecte_nu).lower() == os.path.basename(
            revu_nu).lower():
        statut = PASS_TECHNIQUE
        note = ("VE utilise le fichier declare par le reviseur. Cela ne dit "
                "RIEN de l approbation du climat lui-meme.")
    else:
        statut = DEFAUT_MODELE
        note = ("VE utilise « %s » alors que le reviseur declare « %s ». "
                "L un des deux est a corriger." % (detecte_nu, revu_nu))

    return {"detecte": detecte_nu or NON_FOURNI,
            "revu": revu_nu or NON_FOURNI,
            "statut": statut, "note": note}


# ---------------------------------------------------------------------------
# Ecriture : CSV de preuves, et JSON d audit
# ---------------------------------------------------------------------------

def sauvegarder_avant_ecriture(chemin: str,
                               horodatage: Optional[str] = None) -> Optional[str]:
    """Copie un fichier existant avant de l ecraser.

    Args:
        chemin: Fichier a preserver.
        horodatage: Suffixe impose ; sinon l heure courante.

    Returns:
        str | None: Chemin de la sauvegarde, ou `None` si rien a preserver.
    """
    if not os.path.exists(chemin):
        return None
    marque = horodatage or datetime.now().strftime("%Y%m%d_%H%M%S")
    racine, extension = os.path.splitext(chemin)
    sauvegarde = "%s.backup_%s%s" % (racine, marque, extension)
    shutil.copy2(chemin, sauvegarde)
    return sauvegarde


def ecrire_csv(chemin: str, reponses: Dict[str, Any],
               statut_effectif: str,
               horodatage: Optional[str] = None) -> Dict[str, Any]:
    """Ecrit le CSV de preuves, apres sauvegarde de l existant.

    Le statut ecrit est celui que `evaluer_acceptation` a RECALCULE, jamais
    celui que l utilisateur a demande.

    Args:
        chemin: Fichier CSV a ecrire.
        reponses: Champ -> valeur.
        statut_effectif: Statut recalcule.
        horodatage: Suffixe de sauvegarde impose.

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


def construire_audit(reponses: Dict[str, Any],
                     detecte: Optional[Dict[str, Any]],
                     acceptation: Dict[str, Any],
                     actions_restantes: Sequence[str],
                     chemin_csv: str,
                     sauvegarde: Optional[str] = None,
                     horodatage: Optional[str] = None) -> Dict[str, Any]:
    """Compose le JSON d audit.

    Args:
        reponses: Champ -> valeur.
        detecte: Faits releves dans VE.
        acceptation: Ce que rend `evaluer_acceptation`.
        actions_restantes: Ce qu il reste a faire.
        chemin_csv: CSV ecrit.
        sauvegarde: Sauvegarde eventuelle.
        horodatage: Horodatage impose.

    Returns:
        dict: Structure d audit.
    """
    detecte = detecte or {}
    marque = horodatage or datetime.now().strftime("%Y%m%d_%H%M%S")
    meteo = correspondance_meteo(detecte.get("detected_weather_file"),
                                 (reponses or {}).get("weather_file"))
    return {
        "schema_version": "1.0",
        "generated_at": marque,
        "purpose": (
            "Collecte de preuves pour une evaluation SIA 380/2 d un modele "
            "client. NE constitue ni une declaration de conformite SIA 380/2, "
            "ni une validation SIA 4010 du logiciel."),
        "ve_data_modified": False,
        "ve_data_modified_note": (
            "Aucune donnee VE n a ete modifiee. Cet assistant lit le modele "
            "et ecrit des fichiers de preuve ; il ne mute rien."),
        "project_id": (reponses or {}).get("project_id") or NON_FOURNI,
        "responses": dict((nom, (reponses or {}).get(nom, "") or "")
                          for nom in noms_des_champs()),
        "missing_fields": list(acceptation.get("manquants") or []),
        "field_errors": dict(acceptation.get("erreurs") or {}),
        "sources": {
            "source_document": (reponses or {}).get("source_document") or NON_FOURNI,
            "source_reference": (reponses or {}).get("source_reference") or NON_FOURNI,
            "ventilation_flow_source": (
                (reponses or {}).get("ventilation_flow_source") or NON_FOURNI),
            "lighting_power_source": (
                (reponses or {}).get("lighting_power_source") or NON_FOURNI),
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
            "dernieres."),
    }


def ecrire_audit(dossier: str, audit: Dict[str, Any],
                 project_id: str,
                 horodatage: Optional[str] = None) -> str:
    """Ecrit le JSON d audit, sans jamais ecraser un fichier existant.

    Args:
        dossier: Dossier `sia_compliance_artifacts/evidence/`.
        audit: Structure a ecrire.
        project_id: Identifiant, pour le nom de fichier.
        horodatage: Horodatage impose.

    Returns:
        str: Chemin ecrit.
    """
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    marque = horodatage or audit.get("generated_at") or datetime.now().strftime(
        "%Y%m%d_%H%M%S")
    nom = "SIA3802_evidence_audit_%s_%s.json" % (
        (project_id or "UNKNOWN").strip() or "UNKNOWN", marque)
    chemin = os.path.join(dossier, nom)
    with io.open(chemin, "w", encoding="utf-8") as flux:
        flux.write(json.dumps(audit, ensure_ascii=False, indent=2))
        flux.write(u"\n")
    return chemin


# ---------------------------------------------------------------------------
# Actions restantes, par nature de constat
# ---------------------------------------------------------------------------
#
# Chaque action porte sa CATEGORIE. C est elle qui empeche de confondre un
# defaut du modele avec une donnee client absente, ou une sortie ApacheSim
# desactivee avec un controle non applicable — trois situations qui appellent
# trois gestes differents, de trois personnes differentes.

def actions_ventilation(reponses: Dict[str, Any],
                        constat: Optional[Dict[str, Any]] = None
                        ) -> List[Dict[str, str]]:
    """Actions pour MODEL-003, selon la strategie declaree.

    Args:
        reponses: Champ -> valeur.
        constat: Ce que la sonde a observe, ex.
            `{'infiltration_only': True, 'oa_max_flow': 0.0}`.

    Returns:
        list[dict]: Actions, chacune avec sa categorie.
    """
    reponses = reponses or {}
    constat = constat or {}
    strategie = reponses.get("ventilation_strategy") or ""
    actions = []

    if constat.get("infiltration_only") is True:
        actions.append({
            "controle": "MODEL-003",
            "categorie": PASS_TECHNIQUE,
            "constat": "Les locaux ne portent qu une infiltration.",
            "action": "Aucune — c est une lecture du modele, pas un defaut.",
        })
    elif constat.get("infiltration_only") is None:
        actions.append({
            "controle": "MODEL-003",
            "categorie": NON_VERIFIABLE,
            "constat": "Composition des echanges d air non relevee.",
            "action": "Relancer la sonde sur le projet actif.",
        })

    debit = constat.get("oa_max_flow")
    if debit is None:
        actions.append({
            "controle": "MODEL-003",
            "categorie": LIMITE_VESCRIPTS,
            "constat": "OA_max_flow non expose par l API pour ces locaux.",
            "action": ("Verifier le debit d air neuf dans l interface VE ; "
                       "l API ne permet pas de le confirmer ici."),
        })
    elif float(debit) == 0.0:
        actions.append({
            "controle": "MODEL-003",
            "categorie": PASS_TECHNIQUE,
            "constat": "OA_max_flow = 0 : aucun air neuf mecanique.",
            "action": "Aucune — coherent avec une infiltration seule.",
        })

    if strategie == "NATURAL_ONLY":
        justifiee = bool((reponses.get("ventilation_justification") or "").strip())
        actions.append({
            "controle": "MODEL-003",
            "categorie": PASS_TECHNIQUE if justifiee else PREUVE_MANQUANTE,
            "constat": "Ventilation naturelle declaree.",
            "action": ("Conserver la justification au dossier ; aucune "
                       "modification du modele n est requise."),
        })
    elif strategie in ("MECHANICAL_PRESENT", "MECHANICAL_EXPECTED"):
        actions.append({
            "controle": "MODEL-003",
            "categorie": DEFAUT_MODELE,
            "constat": ("Une ventilation mecanique est attendue, mais les "
                        "locaux ne portent qu une infiltration."),
            "action": ("Dans VE : Building Template Manager > Air Exchanges, "
                       "ajouter un echange de type Auxiliary Ventilation ou "
                       "Natural Ventilation selon le systeme reel, renseigner "
                       "son debit et son profil depuis la source declaree, "
                       "puis relancer ApacheSim. NE PAS creer cet echange "
                       "automatiquement : le debit ne s invente pas."),
        })
    else:
        actions.append({
            "controle": "MODEL-003",
            "categorie": DONNEE_CLIENT_MANQUANTE,
            "constat": "Strategie de ventilation non tranchee.",
            "action": "Faire trancher la strategie par le client ou le CVC.",
        })
    return actions


def actions_eclairage(reponses: Dict[str, Any],
                      constat: Optional[Dict[str, Any]] = None
                      ) -> List[Dict[str, str]]:
    """Actions pour MODEL-004, selon le perimetre declare.

    Args:
        reponses: Champ -> valeur.
        constat: Observations, ex.
            `{'lighting_gain_present': False, 'misc_gain_w_m2': 5.0}`.

    Returns:
        list[dict]: Actions, chacune avec sa categorie.
    """
    reponses = reponses or {}
    constat = constat or {}
    perimetre = reponses.get("lighting_scope") or ""
    actions = []

    if constat.get("lighting_gain_present") is False:
        misc = constat.get("misc_gain_w_m2")
        detail = ("" if misc is None
                  else " Un gain Miscellaneous de %s W/m2 existe." % misc)
        actions.append({
            "controle": "MODEL-004",
            "categorie": PASS_TECHNIQUE,
            "constat": "Aucun gain VE de type Lighting.%s" % detail,
            "action": ("Aucune — et NE PAS convertir le gain Miscellaneous en "
                       "Lighting : ce sont deux grandeurs distinctes, et la "
                       "conversion fabriquerait une puissance d eclairage."),
        })

    if perimetre == "OUT_OF_SCOPE":
        actions.append({
            "controle": "MODEL-004",
            "categorie": NON_APPLICABLE,
            "constat": "L eclairage est hors du perimetre evalue.",
            "action": "Aucune. Conserver la justification au dossier.",
        })
    elif perimetre == "IN_SCOPE":
        actions.append({
            "controle": "MODEL-004",
            "categorie": DONNEE_CLIENT_MANQUANTE,
            "constat": "L eclairage est dans le perimetre mais non modelise.",
            "action": ("Obtenir du client la puissance installee (W/m2), le "
                       "profil horaire et leur source. Puis, dans VE : "
                       "Building Template Manager > Internal Gains, ajouter "
                       "un gain de type Lighting et relancer ApacheSim. NE "
                       "PAS deduire la puissance du gain Miscellaneous."),
        })
    else:
        actions.append({
            "controle": "MODEL-004",
            "categorie": DONNEE_CLIENT_MANQUANTE,
            "constat": "Perimetre de l eclairage non tranche.",
            "action": "Faire trancher le perimetre par le client.",
        })
    return actions


#: Sorties APS que la sonde declare absentes, et ou les activer dans VE.
OU_ACTIVER_LES_SORTIES = {
    "lighting": "ApacheSim > Results, cocher les consommations d eclairage.",
    "fan": "ApacheSim > Results, energies de ventilateurs (niveau systeme).",
    "pump": "ApacheSim > Results, energies de pompes.",
    "auxiliary": "ApacheSim > Results, energies auxiliaires.",
    "heating_coil": "ApacheSim > Results, charge de la batterie chaude.",
    "cooling_coil": "ApacheSim > Results, charge de la batterie froide.",
}


def actions_sorties_aps(reponses: Dict[str, Any],
                        absentes: Sequence[str]) -> List[Dict[str, str]]:
    """Actions pour SIM-003, sans jamais convertir une absence en zero.

    DISTINCTION CENTRALE. Une sortie absente parce que le systeme modelise
    n en produit pas est NON_APPLICABLE. La meme sortie absente parce
    qu ApacheSim ne l a pas produite est SORTIE_NON_ACTIVEE. Les deux se
    corrigent differemment, et aucune ne vaut zero.

    Args:
        reponses: Champ -> valeur.
        absentes: Grandeurs sans liaison APS.

    Returns:
        list[dict]: Actions, chacune avec sa categorie.
    """
    reponses = reponses or {}
    besoin = reponses.get("aps_outputs_required") or ""
    actions = []

    if not absentes:
        return [{
            "controle": "SIM-003",
            "categorie": PASS_TECHNIQUE,
            "constat": "Toutes les sorties attendues sont presentes.",
            "action": "Aucune.",
        }]

    if besoin == "NO":
        actions.append({
            "controle": "SIM-003",
            "categorie": NON_APPLICABLE,
            "constat": ("Sorties absentes : %s. Le reviseur declare qu elles "
                        "ne s appliquent pas au systeme modelise."
                        % ", ".join(absentes)),
            "action": ("Aucune. Conserver la justification. Ces grandeurs "
                       "restent ABSENTES, elles ne valent pas zero."),
        })
        return actions

    if besoin == "YES":
        for grandeur in absentes:
            actions.append({
                "controle": "SIM-003",
                "categorie": SORTIE_NON_ACTIVEE,
                "constat": "Sortie « %s » absente de l APS." % grandeur,
                "action": OU_ACTIVER_LES_SORTIES.get(
                    grandeur,
                    "Activer cette sortie dans ApacheSim, puis relancer."),
            })
        actions.append({
            "controle": "SIM-003",
            "categorie": SORTIE_NON_ACTIVEE,
            "constat": "Apres activation, l APS doit etre regenere.",
            "action": ("Relancer ApacheSim sur l annee complete, puis "
                       "relancer la sonde. Ne PAS combler les series "
                       "manquantes par des zeros."),
        })
        return actions

    actions.append({
        "controle": "SIM-003",
        "categorie": NON_VERIFIABLE,
        "constat": ("Sorties absentes : %s. Leur necessite n est pas "
                    "tranchee." % ", ".join(absentes)),
        "action": ("Determiner si le systeme modelise produit ces grandeurs. "
                   "Tant que ce n est pas tranche, « non applicable » et "
                   "« sortie non activee » restent indiscernables."),
    })
    return actions


def actions_preuves(acceptation: Dict[str, Any]) -> List[Dict[str, str]]:
    """Actions pour EVID-001, sur les preuves documentaires.

    Args:
        acceptation: Ce que rend `evaluer_acceptation`.

    Returns:
        list[dict]: Actions.
    """
    if acceptation.get("accepte"):
        return [{
            "controle": "EVID-001",
            "categorie": PASS_TECHNIQUE,
            "constat": "Metadonnees completes et acceptees par un reviseur.",
            "action": "Aucune.",
        }]
    return [{
        "controle": "EVID-001",
        "categorie": PREUVE_MANQUANTE,
        "constat": ("Metadonnees incompletes : %s"
                    % "; ".join(acceptation.get("motifs_de_refus") or [])),
        "action": ("Completer les champs manquants dans l assistant, puis "
                   "cocher la confirmation explicite."),
    }]


def actions_restantes(reponses: Dict[str, Any],
                      detecte: Optional[Dict[str, Any]],
                      acceptation: Dict[str, Any]) -> List[Dict[str, str]]:
    """Assemble toutes les actions, et conclut sur le verdict SIA.

    Args:
        reponses: Champ -> valeur.
        detecte: Observations de la sonde.
        acceptation: Ce que rend `evaluer_acceptation`.

    Returns:
        list[dict]: Actions ordonnees, la conclusion en dernier.
    """
    detecte = detecte or {}
    actions = []
    actions.extend(actions_ventilation(reponses, detecte.get("ventilation")))
    actions.extend(actions_eclairage(reponses, detecte.get("lighting")))
    actions.extend(actions_sorties_aps(
        reponses, detecte.get("missing_aps_outputs") or ()))
    actions.extend(actions_preuves(acceptation))

    meteo = correspondance_meteo(detecte.get("detected_weather_file"),
                                 (reponses or {}).get("weather_file"))
    actions.append({
        "controle": "EVID-002",
        "categorie": meteo["statut"],
        "constat": "Meteo VE < %s > / revue < %s >."
                   % (meteo["detecte"], meteo["revu"]),
        "action": meteo["note"],
    })

    bloquants = [a for a in actions
                 if a["categorie"] in (DEFAUT_MODELE, DONNEE_CLIENT_MANQUANTE,
                                       PREUVE_MANQUANTE, NON_VERIFIABLE,
                                       SORTIE_NON_ACTIVEE)]
    if bloquants or not acceptation.get("accepte"):
        actions.append({
            "controle": "SIA-380-2",
            "categorie": VERDICT_SIA_IMPOSSIBLE,
            "constat": "%d point(s) bloquant(s) subsistent." % len(bloquants),
            "action": ("Aucun verdict de conformite SIA 380/2 ne peut etre "
                       "rendu. Les PASS techniques ci-dessus n y suffisent "
                       "pas, et la validation SIA 4010 du logiciel est une "
                       "question distincte."),
        })
    else:
        actions.append({
            "controle": "SIA-380-2",
            "categorie": NON_VERIFIABLE,
            "constat": "Aucun point bloquant recense par cet assistant.",
            "action": ("Les preuves collectees sont completes. Le verdict de "
                       "conformite reste du ressort d un ingenieur : cet "
                       "assistant ne le prononce pas."),
        })
    return actions
