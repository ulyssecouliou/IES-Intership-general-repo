"""Four-language copy for the project-local SIA 380/2 evidence editor."""

from __future__ import annotations

from typing import Dict, Tuple

from .reference_model.sia4010.ui_translations import LANGUAGES, normalize_language


def _four(en: str, de: str, fr: str, it: str) -> Dict[str, str]:
    return dict(zip(LANGUAGES, (en, de, fr, it)))


TEXT = {
    "window_title": _four(
        "IES - SIA 380/2 project evidence",
        "IES - Projektnachweise SIA 380/2",
        "IES - Preuves projet SIA 380/2",
        "IES - Prove di progetto SIA 380/2",
    ),
    "status_initial": _four(
        "Items remain pending until the evidence is complete and signed.",
        "Einträge bleiben ausstehend, bis der Nachweis vollständig und unterzeichnet ist.",
        "Les éléments restent en attente tant que la preuve n’est pas complète et signée.",
        "Gli elementi restano in sospeso finché la prova non è completa e firmata.",
    ),
    "eyebrow": _four(
        "PROJECT EVIDENCE · SIA 380/2",
        "PROJEKTNACHWEISE · SIA 380/2",
        "PREUVES PROJET · SIA 380/2",
        "PROVE DI PROGETTO · SIA 380/2",
    ),
    "intro": _four(
        "Enter traceable values only. The software never accepts incomplete evidence.",
        "Nur rückverfolgbare Werte eingeben. Die Software akzeptiert niemals unvollständige Nachweise.",
        "Saisissez uniquement des valeurs traçables. Le logiciel n’accepte jamais une preuve incomplète.",
        "Inserire solo valori tracciabili. Il software non accetta mai prove incomplete.",
    ),
    "language": _four("Language", "Sprache", "Langue", "Lingua"),
    "previous": _four("‹ Previous", "‹ Zurück", "‹ Précédent", "‹ Precedente"),
    "next": _four("Next ›", "Weiter ›", "Suivant ›", "Successivo ›"),
    "add": _four(
        "+ Add row", "+ Zeile hinzufügen", "+ Ajouter une ligne", "+ Aggiungi riga"
    ),
    "delete": _four(
        "Delete this row",
        "Diese Zeile löschen",
        "Supprimer cette ligne",
        "Elimina questa riga",
    ),
    "save": _four(
        "Save active tab",
        "Aktiven Reiter speichern",
        "Enregistrer l’onglet actif",
        "Salva scheda attiva",
    ),
    "return_to_report": _four(
        "Return to report",
        "Zum Bericht zurÃ¼ckkehren",
        "Retourner au rapport",
        "Torna al rapporto",
    ),
    "row": _four(
        "Row {current} / {total}",
        "Zeile {current} / {total}",
        "Ligne {current} / {total}",
        "Riga {current} / {total}",
    ),
    "dialog_title": _four(
        "SIA 380/2 evidence",
        "Nachweise nach SIA 380/2",
        "Preuves SIA 380/2",
        "Prove SIA 380/2",
    ),
    "saved_pending": _four(
        "Saved, but {count} row(s) requested as accepted remain PENDING: information or signature is incomplete.",
        "Gespeichert, aber {count} als akzeptiert angeforderte Zeile(n) bleiben PENDING: Angaben oder Unterschrift sind unvollständig.",
        "Enregistré, mais {count} ligne(s) demandée(s) comme acceptée(s) restent PENDING : informations ou signature incomplètes.",
        "Salvato, ma {count} riga/righe richieste come accettate restano PENDING: informazioni o firma incomplete.",
    ),
    "saved_ok": _four(
        "Saved: {rows} row(s), {accepted} accepted.",
        "Gespeichert: {rows} Zeile(n), {accepted} akzeptiert.",
        "Enregistré : {rows} ligne(s), {accepted} acceptée(s).",
        "Salvato: {rows} riga/righe, {accepted} accettate.",
    ),
}


FAMILY_TEXT = {
    "project_metadata": _four(
        "Project and climate", "Projekt und Klima", "Projet et climat", "Progetto e clima"
    ),
    "usage_mapping": _four(
        "SIA 2024 use mapping",
        "Nutzungszuordnung SIA 2024",
        "Affectation d’usage SIA 2024",
        "Mappatura d’uso SIA 2024",
    ),
    "global_comparison": _four(
        "Global comparison", "Gesamtvergleich", "Comparaison globale", "Confronto globale"
    ),
    "ventilation_control": _four(
        "Ventilation control",
        "Lüftungsregelung",
        "Commande de ventilation",
        "Controllo della ventilazione",
    ),
    "cooling_generator": _four(
        "Cooling generator",
        "Kälteerzeuger",
        "Générateur de froid",
        "Generatore di raffrescamento",
    ),
    "lighting_mapping": _four(
        "Lighting control",
        "Beleuchtungsregelung",
        "Commande d’éclairage",
        "Controllo dell’illuminazione",
    ),
    "electrical_power": _four(
        "Electrical power",
        "Elektrische Leistung",
        "Puissance électrique",
        "Potenza elettrica",
    ),
}


FAMILY_HELP = {
    "project_metadata": _four(
        "Building status and climate basis approved by the energy lead.",
        "Gebäudestatus und Klimagrundlage, freigegeben durch die Energieverantwortung.",
        "Statut du bâtiment et base climatique approuvés par le responsable énergie.",
        "Stato dell’edificio e base climatica approvati dal responsabile energia.",
    ),
    "usage_mapping": _four(
        "Map each room or thermal template to the SIA 2024 category confirmed by the reviewer.",
        "Jeden Raum oder jedes thermische Template der vom Prüfer bestätigten SIA-2024-Kategorie zuordnen.",
        "Associez chaque pièce ou template thermique à la catégorie SIA 2024 confirmée par le réviseur.",
        "Associare ogni locale o template termico alla categoria SIA 2024 confermata dal revisore.",
    ),
    "global_comparison": _four(
        "Whole-project comparison with the SIA reference, from the signed calculation.",
        "Gesamtprojektvergleich mit der SIA-Referenz aus der unterzeichneten Berechnung.",
        "Comparaison du projet complet avec la référence SIA, issue du calcul signé.",
        "Confronto dell’intero progetto con il riferimento SIA, tratto dal calcolo firmato.",
    ),
    "ventilation_control": _four(
        "One row per system or zone. Values prefilled from VE still require confirmation.",
        "Eine Zeile pro System oder Zone. Aus VE vorbefüllte Werte müssen bestätigt werden.",
        "Une ligne par système ou zone. Les valeurs préremplies depuis VE restent à confirmer.",
        "Una riga per sistema o zona. I valori precompilati da VE devono essere confermati.",
    ),
    "cooling_generator": _four(
        "Class, capacity and EER/SEER from the approved manufacturer data sheet.",
        "Klasse, Leistung und EER/SEER gemäss freigegebenem Herstellerdatenblatt.",
        "Classe, puissance et EER/SEER d’après la fiche fabricant approuvée.",
        "Classe, potenza ed EER/SEER dalla scheda tecnica approvata del produttore.",
    ),
    "lighting_mapping": _four(
        "Map each room or template to its SIA 387/4 control type.",
        "Jeden Raum oder jedes Template dem Regelungstyp nach SIA 387/4 zuordnen.",
        "Associez chaque pièce ou template à son type de commande SIA 387/4.",
        "Associare ogni locale o template al tipo di controllo SIA 387/4.",
    ),
    "electrical_power": _four(
        "Design power in W/m² and the cooling-necessity category.",
        "Auslegungsleistung in W/m² und Kategorie der Kühlnotwendigkeit.",
        "Puissance de dimensionnement en W/m² et catégorie de nécessité du froid.",
        "Potenza di progetto in W/m² e categoria di necessità del raffrescamento.",
    ),
}


FIELD_TEXT: Dict[str, Dict[str, str]] = {
    "project_id": _four("Project", "Projekt", "Projet", "Progetto"),
    "building_status": _four(
        "Building status", "Gebäudestatus", "Statut du bâtiment", "Stato dell’edificio"
    ),
    "weather_basis": _four(
        "Approved climate basis",
        "Freigegebene Klimagrundlage",
        "Base climatique approuvée",
        "Base climatica approvata",
    ),
    "weather_file": _four("Weather file", "Wetterdatei", "Fichier météo", "File meteo"),
    "location": _four(
        "Location / station", "Ort / Station", "Localité / station", "Località / stazione"
    ),
    "altitude_m": _four("Altitude (m)", "Höhe (m)", "Altitude (m)", "Altitudine (m)"),
    "weather_source_authority": _four(
        "Weather source authority",
        "Herausgeber der Klimadaten",
        "Autorité de la source météo",
        "Autorità della fonte meteo",
    ),
    "weather_use_case": _four(
        "Weather dataset use",
        "Verwendungszweck der Klimadaten",
        "Usage du jeu climatique",
        "Uso del set climatico",
    ),
    "weather_scenario_period": _four(
        "Climate scenario and period",
        "Klimaszenario und Zeitraum",
        "Scénario et période climatiques",
        "Scenario e periodo climatici",
    ),
    "location_source": _four(
        "Location source",
        "Quelle des Standorts",
        "Source de la localisation",
        "Fonte dell’ubicazione",
    ),
    "altitude_source": _four(
        "Altitude source",
        "Quelle der Höhenangabe",
        "Source de l’altitude",
        "Fonte dell’altitudine",
    ),
    "review_status": _four(
        "Review status", "Prüfstatus", "Statut de revue", "Stato della revisione"
    ),
    "reviewer": _four(
        "Responsible reviewer",
        "Verantwortliche Prüfstelle",
        "Responsable / réviseur",
        "Responsabile / revisore",
    ),
    "reviewer_role": _four(
        "Reviewer role",
        "Rolle der prüfenden Person",
        "Rôle du reviewer",
        "Ruolo del revisore",
    ),
    "reviewer_organisation": _four(
        "Reviewer organisation",
        "Organisation der prüfenden Person",
        "Organisation du reviewer",
        "Organizzazione del revisore",
    ),
    "reviewer_competence_basis": _four(
        "Reviewer competence basis",
        "Kompetenzgrundlage der prüfenden Person",
        "Base de compétence du reviewer",
        "Base di competenza del revisore",
    ),
    "reviewer_acceptance_scope": _four(
        "Reviewer acceptance scope",
        "Umfang der Annahme durch die prüfende Person",
        "Périmètre accepté par le reviewer",
        "Ambito accettato dal revisore",
    ),
    "review_date": _four(
        "Review date (YYYY-MM-DD)",
        "Prüfdatum (JJJJ-MM-TT)",
        "Date de revue (AAAA-MM-JJ)",
        "Data revisione (AAAA-MM-GG)",
    ),
    "source_document": _four(
        "Source document", "Quelldokument", "Document source", "Documento sorgente"
    ),
    "source_reference": _four(
        "Page / clause / reference",
        "Seite / Ziffer / Referenz",
        "Page / clause / référence",
        "Pagina / clausola / riferimento",
    ),
    "notes": _four("Notes", "Notizen", "Notes", "Note"),
    "assumptions_status": _four(
        "Assumptions status",
        "Status der Annahmen",
        "Statut des hypothèses",
        "Stato delle ipotesi",
    ),
    "assumptions_register": _four(
        "Assumptions register",
        "Annahmenregister",
        "Registre des hypothèses",
        "Registro delle ipotesi",
    ),
    "report_use_acknowledgement": _four(
        "Report-use acknowledgement",
        "Bestätigung des Berichtszwecks",
        "Reconnaissance de la portée du rapport",
        "Presa d’atto dell’uso del rapporto",
    ),
    "comparison_scope": _four("Scope", "Umfang", "Périmètre", "Ambito"),
    "comparison_metric": _four("Metric", "Kennwert", "Indicateur", "Indicatore"),
    "project_value": _four(
        "Project value", "Projektwert", "Valeur projet", "Valore di progetto"
    ),
    "reference_value": _four(
        "Reference value", "Referenzwert", "Valeur de référence", "Valore di riferimento"
    ),
    "comparison_result": _four("Result", "Ergebnis", "Résultat", "Risultato"),
    "unit": _four("Unit", "Einheit", "Unité", "Unità"),
    "system_id": _four("VE system", "VE-System", "Système VE", "Sistema VE"),
    "room_or_zone": _four("Room / zone", "Raum / Zone", "Pièce / zone", "Locale / zona"),
    "system_type": _four(
        "System type", "Systemtyp", "Type de système", "Tipo di sistema"
    ),
    "control_class": _four(
        "Control class", "Regelungsklasse", "Classe de commande", "Classe di controllo"
    ),
    "airflow_band": _four(
        "Airflow band", "Luftmengenbereich", "Bande de débit", "Fascia di portata"
    ),
    "specific_airflow_m3_h_m2": _four(
        "Specific airflow (m³/h/m²)",
        "Spezifischer Luftstrom (m³/h/m²)",
        "Débit spécifique (m³/h/m²)",
        "Portata specifica (m³/h/m²)",
    ),
    "air_flow_control": _four(
        "AIR_FLOW_CTRL read from VE",
        "AIR_FLOW_CTRL aus VE",
        "AIR_FLOW_CTRL lu dans VE",
        "AIR_FLOW_CTRL letto da VE",
    ),
    "fan_control": _four(
        "FAN_CTRL read from VE",
        "FAN_CTRL aus VE",
        "FAN_CTRL lu dans VE",
        "FAN_CTRL letto da VE",
    ),
    "demand_sensor": _four(
        "Demand sensor", "Bedarfssensor", "Capteur de demande", "Sensore di domanda"
    ),
    "control_scope": _four(
        "Control scope",
        "Regelungsumfang",
        "Portée de la commande",
        "Ambito del controllo",
    ),
    "minimum_airflow_percent": _four(
        "Minimum airflow (%)",
        "Mindestluftmenge (%)",
        "Débit minimum (%)",
        "Portata minima (%)",
    ),
    "time_schedule": _four(
        "Schedule / profile",
        "Zeitplan / Profil",
        "Horaire / profil",
        "Programma / profilo",
    ),
    "generator_class": _four(
        "Generator class",
        "Erzeugerklasse",
        "Classe du générateur",
        "Classe del generatore",
    ),
    "capacity_kw": _four(
        "Nominal capacity (kW)",
        "Nennleistung (kW)",
        "Puissance nominale (kW)",
        "Potenza nominale (kW)",
    ),
    "nominal_eer": _four("Nominal EER", "Nenn-EER", "EER nominal", "EER nominale"),
    "seer": _four(
        "Declared SEER", "Deklarierter SEER", "SEER déclaré", "SEER dichiarato"
    ),
    "room_id": _four("Room ID", "Raum-ID", "ID pièce", "ID locale"),
    "thermal_template_id": _four(
        "Thermal template ID",
        "ID des thermischen Templates",
        "ID du template thermique",
        "ID template termico",
    ),
    "sia2024_category": _four(
        "SIA 2024 use category",
        "Nutzungskategorie nach SIA 2024",
        "Catégorie d’usage SIA 2024",
        "Categoria d’uso SIA 2024",
    ),
    "sia3874_control_type": _four(
        "SIA 387/4 control type",
        "Regelungstyp nach SIA 387/4",
        "Type de commande SIA 387/4",
        "Tipo di controllo SIA 387/4",
    ),
    "daylight_control": _four(
        "Daylight control",
        "Tageslichtregelung",
        "Commande de lumière du jour",
        "Controllo della luce diurna",
    ),
    "required_electrical_power_w_m2": _four(
        "Required electrical power (W/m²)",
        "Erforderliche elektrische Leistung (W/m²)",
        "Puissance électrique requise (W/m²)",
        "Potenza elettrica richiesta (W/m²)",
    ),
    "conditioned_area_m2": _four(
        "Conditioned area (m²)",
        "Konditionierte Fläche (m²)",
        "Surface conditionnée (m²)",
        "Superficie climatizzata (m²)",
    ),
    "cooling_present": _four(
        "Cooling present",
        "Kühlung vorhanden",
        "Refroidissement présent",
        "Raffrescamento presente",
    ),
    "cooling_category": _four(
        "Cooling-necessity category",
        "Kategorie der Kühlnotwendigkeit",
        "Catégorie de nécessité du froid",
        "Categoria di necessità del raffrescamento",
    ),
    "ventilation_strategy": _four(
        "Ventilation strategy",
        "Lüftungsstrategie",
        "Stratégie de ventilation",
        "Strategia di ventilazione",
    ),
    "ventilation_justification": _four(
        "Ventilation justification",
        "Begründung der Lüftung",
        "Justification de la ventilation",
        "Giustificazione della ventilazione",
    ),
    "ventilation_flow_source": _four(
        "Ventilation flow-rate source",
        "Quelle der Lüftungsvolumenströme",
        "Source des débits de ventilation",
        "Fonte delle portate di ventilazione",
    ),
    "ventilation_scope": _four(
        "Ventilation scope",
        "Umfang der Lüftungsdeklaration",
        "Périmètre de la ventilation",
        "Ambito della ventilazione",
    ),
    "lighting_scope": _four(
        "Lighting assessment scope",
        "Umfang der Beleuchtungsbewertung",
        "Périmètre de l’évaluation de l’éclairage",
        "Ambito della valutazione dell’illuminazione",
    ),
    "lighting_power_source": _four(
        "Lighting power source",
        "Quelle der Beleuchtungsleistung",
        "Source de la puissance d’éclairage",
        "Fonte della potenza di illuminazione",
    ),
    "lighting_scope_justification": _four(
        "Lighting-scope justification",
        "Begründung des Beleuchtungsumfangs",
        "Justification du périmètre éclairage",
        "Giustificazione dell’ambito illuminazione",
    ),
    "system_power_source": _four(
        "System power source",
        "Quelle der Anlagenleistungen",
        "Source des puissances des systèmes",
        "Fonte delle potenze degli impianti",
    ),
    "aps_outputs_required": _four(
        "Fan/pump/auxiliary/coil outputs required?",
        "Ausgaben für Ventilator/Pumpe/Hilfsenergie/Register erforderlich?",
        "Sorties ventilateur/pompe/auxiliaires/batteries requises ?",
        "Sono richiesti output di ventilatori/pompe/ausiliari/batterie?",
    ),
    "aps_outputs_justification": _four(
        "APS output justification",
        "Begründung der APS-Ausgaben",
        "Justification des sorties APS",
        "Giustificazione degli output APS",
    ),
}


def text(key: str, language: str = "en", **values: object) -> str:
    """Return localized UI copy, falling back visibly to reviewed English."""

    code = normalize_language(language)
    entry = TEXT[key]
    return (entry.get(code) or entry["en"]).format(**values)


def family_title(key: str, language: str = "en") -> str:
    code = normalize_language(language)
    return FAMILY_TEXT[key].get(code) or FAMILY_TEXT[key]["en"]


def family_help(key: str, language: str = "en") -> str:
    code = normalize_language(language)
    return FAMILY_HELP[key].get(code) or FAMILY_HELP[key]["en"]


def field_label(key: str, language: str = "en") -> str:
    code = normalize_language(language)
    entry = FIELD_TEXT.get(key)
    if entry is None:
        return key.replace("_", " ").capitalize()
    return entry.get(code) or entry["en"]


def missing_translations() -> Tuple[str, ...]:
    """Return incomplete catalogue locations for release-gate tests."""

    missing = []
    for group_name, group in (
        ("text", TEXT),
        ("family", FAMILY_TEXT),
        ("help", FAMILY_HELP),
        ("field", FIELD_TEXT),
    ):
        for key, entry in group.items():
            for code in LANGUAGES:
                if not str(entry.get(code) or "").strip():
                    missing.append("{}/{}/{}".format(group_name, key, code))
    return tuple(missing)
