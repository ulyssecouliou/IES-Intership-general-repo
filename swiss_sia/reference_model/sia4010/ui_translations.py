"""Shared user-interface translations for the Swiss VE Model Builder.

Swiss compliance work is carried out in the three national languages, so the
builder is offered in German, French and Italian alongside English. Both
front-ends read this single catalogue: the native Tk window imports it directly,
and the standalone HTML builder has it injected at build time, so a wording
change is made once and applies everywhere.

German entries use Swiss orthography (double-s rather than the eszett letter),
as is standard for Swiss technical documents. Standard identifiers that must
stay verbatim -
``SIA 380/2``, ``SIA 4010``, profile and execution-mode codes, file names - are
deliberately not translated.
"""

from typing import Dict, Mapping

# Language codes match the documentation toolchain (docs/tools/build_docs.py).
LANGUAGES = ("en", "de", "fr", "it")
DEFAULT_LANGUAGE = "en"

LANGUAGE_LABELS: Dict[str, str] = {
    "en": "English",
    "de": "Deutsch",
    "fr": "Français",
    "it": "Italiano",
}

# key -> {language code -> text}
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # ---------------------------------------------------------------- shell
    "window_title": {
        "en": "Swiss VE Model Builder - SIA 380/2 + SIA 4010",
        "de": "Swiss VE Model Builder - SIA 380/2 + SIA 4010",
        "fr": "Swiss VE Model Builder - SIA 380/2 + SIA 4010",
        "it": "Swiss VE Model Builder - SIA 380/2 + SIA 4010",
    },
    "header_eyebrow": {
        "en": "VIRTUAL ENVIRONMENT  ·  SWISS COMPLIANCE TOOLKIT",
        "de": "VIRTUAL ENVIRONMENT  ·  SCHWEIZER COMPLIANCE-TOOLKIT",
        "fr": "VIRTUAL ENVIRONMENT  ·  BOÎTE À OUTILS CONFORMITÉ SUISSE",
        "it": "VIRTUAL ENVIRONMENT  ·  STRUMENTI CONFORMITÀ SVIZZERA",
    },
    "header_title": {
        "en": "Swiss VE Model Builder",
        "de": "Swiss VE Model Builder",
        "fr": "Swiss VE Model Builder",
        "it": "Swiss VE Model Builder",
    },
    "brand_subtitle": {
        "en": "Swiss compliance toolkit",
        "de": "Schweizer Compliance-Toolkit",
        "fr": "Boîte à outils conformité suisse",
        "it": "Strumenti conformità Svizzera",
    },
    "lede": {
        "en": (
            "Prepare a reproducible, verifiable and fail-closed scenario before "
            "anything is created in VE. Official cases lock the normative features."
        ),
        "de": (
            "Bereiten Sie ein reproduzierbares, überprüfbares und standardmässig "
            "gesperrtes Szenario vor, bevor in VE etwas erstellt wird. Offizielle "
            "Fälle sperren die normativen Funktionen."
        ),
        "fr": (
            "Préparez un scénario reproductible, vérifiable et fermé par défaut "
            "avant toute création dans VE. Les cas officiels verrouillent les "
            "caractéristiques normatives."
        ),
        "it": (
            "Prepara uno scenario riproducibile, verificabile e chiuso per "
            "impostazione predefinita prima di creare qualsiasi cosa in VE. I casi "
            "ufficiali bloccano le caratteristiche normative."
        ),
    },
    "eyebrow_generator": {
        "en": "Controlled generator",
        "de": "Kontrollierter Generator",
        "fr": "Générateur contrôlé",
        "it": "Generatore controllato",
    },
    "language_label": {
        "en": "Language",
        "de": "Sprache",
        "fr": "Langue",
        "it": "Lingua",
    },
    # ------------------------------------------------------------- sections
    "section_scenario": {
        "en": "Scenario",
        "de": "Szenario",
        "fr": "Scénario",
        "it": "Scenario",
    },
    "scenario_hint": {
        "en": "One disposable VE project corresponds to exactly one case.",
        "de": "Ein wegwerfbares VE-Projekt entspricht genau einem Fall.",
        "fr": "Un projet VE jetable correspond à un seul cas.",
        "it": "Un progetto VE usa e getta corrisponde a un solo caso.",
    },
    "panel_scenario_title": {
        "en": "Configure the scenario",
        "de": "Szenario konfigurieren",
        "fr": "Configurer le scénario",
        "it": "Configura lo scenario",
    },
    "panel_scenario_sub": {
        "en": (
            "An official case generates a disposable VE model. The normative "
            "features are locked."
        ),
        "de": (
            "Ein offizieller Fall erzeugt ein wegwerfbares VE-Modell. Die "
            "normativen Funktionen sind gesperrt."
        ),
        "fr": (
            "Un cas officiel génère un modèle VE jetable. Les caractéristiques "
            "normatives sont verrouillées."
        ),
        "it": (
            "Un caso ufficiale genera un modello VE usa e getta. Le "
            "caratteristiche normative sono bloccate."
        ),
    },
    "panel_manifest_title": {
        "en": "Generated manifest",
        "de": "Erzeugtes Manifest",
        "fr": "Manifeste généré",
        "it": "Manifesto generato",
    },
    "panel_manifest_sub": {
        "en": "This file becomes the single instruction for the VEScript.",
        "de": "Diese Datei wird zur einzigen Anweisung für das VEScript.",
        "fr": "Ce fichier devient l’unique instruction du VEScript.",
        "it": "Questo file diventa l’unica istruzione per il VEScript.",
    },
    "section_files": {
        "en": "Files",
        "de": "Dateien",
        "fr": "Fichiers",
        "it": "File",
    },
    "files_hint": {
        "en": "Paths relative to the repository or to the active VE project.",
        "de": "Pfade relativ zum Repository oder zum aktiven VE-Projekt.",
        "fr": "Chemins relatifs au dépôt ou au projet VE actif.",
        "it": "Percorsi relativi al repository o al progetto VE attivo.",
    },
    "section_input_files": {
        "en": "Input files",
        "de": "Eingabedateien",
        "fr": "Fichiers d’entrée",
        "it": "File di ingresso",
    },
    "section_features": {
        "en": "Features",
        "de": "Funktionen",
        "fr": "Fonctionnalités",
        "it": "Funzionalità",
    },
    "section_model_features": {
        "en": "Model features",
        "de": "Modellfunktionen",
        "fr": "Fonctionnalités du modèle",
        "it": "Funzionalità del modello",
    },
    # --------------------------------------------------------------- fields
    "label_scenario_id": {
        "en": "Scenario identifier",
        "de": "Szenario-Bezeichner",
        "fr": "Identifiant du scénario",
        "it": "Identificatore dello scenario",
    },
    "label_profile": {
        "en": "Profile",
        "de": "Profil",
        "fr": "Profil",
        "it": "Profilo",
    },
    "label_class": {
        "en": "Class",
        "de": "Klasse",
        "fr": "Classe",
        "it": "Classe",
    },
    "label_target_class": {
        "en": "Target class",
        "de": "Zielklasse",
        "fr": "Classe cible",
        "it": "Classe di destinazione",
    },
    "label_variant": {
        "en": "Test / variant",
        "de": "Test / Variante",
        "fr": "Test / variante",
        "it": "Test / variante",
    },
    "label_case": {
        "en": "Case",
        "de": "Fall",
        "fr": "Cas",
        "it": "Caso",
    },
    "label_official_case": {
        "en": "Official case",
        "de": "Offizieller Fall",
        "fr": "Cas officiel",
        "it": "Caso ufficiale",
    },
    "label_identifier": {
        "en": "Identifier",
        "de": "Bezeichner",
        "fr": "Identifiant",
        "it": "Identificatore",
    },
    "label_execution_mode": {
        "en": "Execution mode",
        "de": "Ausführungsmodus",
        "fr": "Mode d’exécution",
        "it": "Modalità di esecuzione",
    },
    "label_case_manifest": {
        "en": "Case manifest",
        "de": "Fallmanifest",
        "fr": "Manifeste des cas",
        "it": "Manifesto dei casi",
    },
    "label_official_case_manifest": {
        "en": "Official case manifest",
        "de": "Offizielles Fallmanifest",
        "fr": "Manifeste des cas officiels",
        "it": "Manifesto dei casi ufficiali",
    },
    "label_ve_config": {
        "en": "VE configuration",
        "de": "VE-Konfiguration",
        "fr": "Configuration VE",
        "it": "Configurazione VE",
    },
    "label_ve_assets": {
        "en": "VE case assets",
        "de": "VE-Assets des Falls",
        "fr": "Assets VE du cas",
        "it": "Asset VE del caso",
    },
    # -------------------------------------------------------------- choices
    "option_official": {
        "en": "Official SIA 4010 case",
        "de": "Offizieller Fall nach SIA 4010",
        "fr": "Cas officiel SIA 4010",
        "it": "Caso ufficiale SIA 4010",
    },
    "option_custom": {
        "en": "Custom, non-official model",
        "de": "Benutzerdefiniertes, nicht offizielles Modell",
        "fr": "Modèle personnalisé non officiel",
        "it": "Modello personalizzato non ufficiale",
    },
    "option_prepare_only": {
        "en": "Prepare and check - no VE change",
        "de": "Vorbereiten und prüfen - keine VE-Änderung",
        "fr": "Préparer et contrôler - aucune modification VE",
        "it": "Prepara e verifica - nessuna modifica a VE",
    },
    "option_create": {
        "en": "Create in the active VE project",
        "de": "Im aktiven VE-Projekt erstellen",
        "fr": "Créer dans le projet VE actif",
        "it": "Crea nel progetto VE attivo",
    },
    "locked_badge": {
        "en": "LOCKED",
        "de": "GESPERRT",
        "fr": "VERROUILLÉ",
        "it": "BLOCCATO",
    },
    # -------------------------------------------------------------- notices
    "notice_official": {
        "en": (
            "Official mode: the features are imposed by the selected case. Any "
            "deviation is rejected by the launcher."
        ),
        "de": (
            "Offizieller Modus: Die Funktionen werden durch den gewählten Fall "
            "vorgegeben. Jede Abweichung wird vom Launcher abgelehnt."
        ),
        "fr": (
            "Mode officiel : les fonctionnalités sont imposées par le cas "
            "sélectionné. Toute divergence est refusée par le lanceur."
        ),
        "it": (
            "Modalità ufficiale: le funzionalità sono imposte dal caso "
            "selezionato. Ogni divergenza viene rifiutata dal launcher."
        ),
    },
    "notice_custom": {
        "en": (
            "Custom mode: exploratory preparation only. Features may be changed, "
            "but no automated creation and no SIA 4010 validation is permitted."
        ),
        "de": (
            "Benutzerdefinierter Modus: nur explorative Vorbereitung. Funktionen "
            "können geändert werden, aber keine automatisierte Erstellung und "
            "keine Validierung nach SIA 4010 ist zulässig."
        ),
        "fr": (
            "Mode personnalisé : préparation exploratoire uniquement. Les "
            "fonctionnalités peuvent être modifiées, mais aucune création "
            "automatisée ni validation SIA 4010 n’est autorisée."
        ),
        "it": (
            "Modalità personalizzata: solo preparazione esplorativa. Le "
            "funzionalità possono essere modificate, ma non sono consentite né la "
            "creazione automatizzata né la validazione SIA 4010."
        ),
    },
    "features_hint_official": {
        "en": "The official options are imposed by the case.",
        "de": "Die offiziellen Optionen werden durch den Fall vorgegeben.",
        "fr": "Les options officielles sont imposées par le cas.",
        "it": "Le opzioni ufficiali sono imposte dal caso.",
    },
    "features_hint_custom": {
        "en": "Free exploration: preparation only, no VE mutation.",
        "de": "Freie Erkundung: nur Vorbereitung, keine VE-Mutation.",
        "fr": "Exploration libre : préparation uniquement, sans mutation VE.",
        "it": "Esplorazione libera: solo preparazione, nessuna mutazione di VE.",
    },
    # -------------------------------------------------------------- statuses
    "status_ready_title": {
        "en": "READY FOR PREVALIDATION",
        "de": "BEREIT FÜR DIE VORPRÜFUNG",
        "fr": "PRÊT POUR PRÉVALIDATION",
        "it": "PRONTO PER LA PREVALIDAZIONE",
    },
    "status_ready_detail": {
        "en": "Start by preparing the case without changing VE.",
        "de": "Beginnen Sie mit der Vorbereitung des Falls, ohne VE zu ändern.",
        "fr": "Commence par préparer le cas sans modifier VE.",
        "it": "Inizia preparando il caso senza modificare VE.",
    },
    "status_no_mutation_title": {
        "en": "No mutation risk",
        "de": "Kein Mutationsrisiko",
        "fr": "Aucun risque de mutation",
        "it": "Nessun rischio di mutazione",
    },
    "status_no_mutation_detail": {
        "en": (
            "The first run produces only the geometry, the model plan and the "
            "prevalidation report."
        ),
        "de": (
            "Der erste Lauf erzeugt nur die Geometrie, den Modellplan und den "
            "Vorprüfbericht."
        ),
        "fr": (
            "La première exécution produit uniquement la géométrie, le plan de "
            "modèle et le rapport de prévalidation."
        ),
        "it": (
            "La prima esecuzione produce solo la geometria, il piano del modello "
            "e il rapporto di prevalidazione."
        ),
    },
    "status_prevalidation_required_title": {
        "en": "Prevalidation required",
        "de": "Vorprüfung erforderlich",
        "fr": "Prévalidation obligatoire",
        "it": "Prevalidazione obbligatoria",
    },
    "status_prevalidation_required_detail": {
        "en": (
            "Creation stays blocked until the official data and the exact case "
            "assets are confirmed."
        ),
        "de": (
            "Die Erstellung bleibt blockiert, bis die offiziellen Daten und die "
            "genauen Fall-Assets bestätigt sind."
        ),
        "fr": (
            "La création restera bloquée tant que les données officielles et les "
            "assets exacts du cas ne sont pas confirmés."
        ),
        "it": (
            "La creazione resta bloccata finché i dati ufficiali e gli asset "
            "esatti del caso non sono confermati."
        ),
    },
    "status_unsaved_title": {
        "en": "VE PROJECT NOT SAVED",
        "de": "VE-PROJEKT NICHT GESPEICHERT",
        "fr": "PROJET VE NON ENREGISTRÉ",
        "it": "PROGETTO VE NON SALVATO",
    },
    "status_unsaved_detail": {
        "en": (
            "Save this disposable project into a permanent folder first. "
            "Preparation remains available, but creation is disabled."
        ),
        "de": (
            "Speichern Sie dieses wegwerfbare Projekt zuerst in einem permanenten "
            "Ordner. Die Vorbereitung bleibt verfügbar, die Erstellung ist "
            "deaktiviert."
        ),
        "fr": (
            "Enregistre d’abord ce projet jetable dans un dossier permanent. "
            "La préparation reste disponible, mais la création est désactivée."
        ),
        "it": (
            "Salva prima questo progetto usa e getta in una cartella permanente. "
            "La preparazione resta disponibile, ma la creazione è disattivata."
        ),
    },
    "status_invalid_title": {
        "en": "INVALID SCENARIO",
        "de": "UNGÜLTIGES SZENARIO",
        "fr": "SCÉNARIO INVALIDE",
        "it": "SCENARIO NON VALIDO",
    },
    "status_processing_title": {
        "en": "PROCESSING",
        "de": "VERARBEITUNG LÄUFT",
        "fr": "TRAITEMENT EN COURS",
        "it": "ELABORAZIONE IN CORSO",
    },
    "status_processing_detail": {
        "en": "VE stays available after this operation finishes.",
        "de": "VE bleibt nach Abschluss dieses Vorgangs verfügbar.",
        "fr": "VE reste disponible après la fin de cette opération.",
        "it": "VE resta disponibile al termine di questa operazione.",
    },
    "status_preparing_all_classes_detail": {
        "en": "Verifying the official package and preparing all eight classes.",
        "de": "Offizielles Paket wird geprüft und alle acht Klassen werden vorbereitet.",
        "fr": "Vérification du paquet officiel et préparation des huit classes.",
        "it": "Verifica del pacchetto ufficiale e preparazione di tutte le otto classi.",
    },
    "status_all_classes_result": {
        "en": (
            "{classes} classes and {unique} unique cases prepared; "
            "{geometry} deterministic gbXML cases; "
            "{blocked} class-case occurrences remain blocked; audit: {audit}"
        ),
        "de": (
            "{classes} Klassen und {unique} eindeutige Fälle vorbereitet; "
            "{geometry} deterministische gbXML-Fälle; "
            "{blocked} Klassen-Fall-Vorkommen bleiben blockiert; Audit: {audit}"
        ),
        "fr": (
            "{classes} classes et {unique} cas uniques préparés ; "
            "{geometry} cas gbXML déterministes ; "
            "{blocked} occurrences classe-cas restent bloquées ; audit : {audit}"
        ),
        "it": (
            "{classes} classi e {unique} casi unici preparati; "
            "{geometry} casi gbXML deterministici; "
            "{blocked} occorrenze classe-caso restano bloccate; audit: {audit}"
        ),
    },
    "status_evaluating_aps_detail": {
        "en": "Reading the newest APS file with runtime-qualified bindings.",
        "de": "Neueste APS-Datei wird mit laufzeitqualifizierten Bindungen gelesen.",
        "fr": "Lecture du dernier APS avec les liaisons qualifiées dans VE.",
        "it": "Lettura dell'ultimo APS con binding qualificati nel runtime.",
    },
    "status_simulating_detail": {
        "en": (
            "Running the confirmed annual period in ApacheSim, then reading "
            "and evaluating the new APS file."
        ),
        "de": (
            "Der bestätigte Jahreszeitraum wird in ApacheSim ausgeführt; "
            "anschliessend wird die neue APS-Datei gelesen und ausgewertet."
        ),
        "fr": (
            "Exécution de la période annuelle confirmée dans ApacheSim, puis "
            "lecture et évaluation du nouvel APS."
        ),
        "it": (
            "Esecuzione del periodo annuale confermato in ApacheSim, quindi "
            "lettura e valutazione del nuovo file APS."
        ),
    },
    "status_simulation_result": {
        "en": "{case}: simulation and APS workflow status {status}; report: {artifact}",
        "de": "{case}: Status Simulation und APS {status}; Bericht: {artifact}",
        "fr": "{case} : statut simulation et APS {status} ; rapport : {artifact}",
        "it": "{case}: stato simulazione e APS {status}; rapporto: {artifact}",
    },
    "status_aps_result": {
        "en": (
            "{variant}/{case}: {metrics} observed metrics and {distributions} "
            "distribution criteria; report: {artifact}"
        ),
        "de": (
            "{variant}/{case}: {metrics} beobachtete Kennwerte und "
            "{distributions} Verteilungskriterien; Bericht: {artifact}"
        ),
        "fr": (
            "{variant}/{case} : {metrics} métriques observées et "
            "{distributions} critères de distribution ; rapport : {artifact}"
        ),
        "it": (
            "{variant}/{case}: {metrics} metriche osservate e {distributions} "
            "criteri di distribuzione; rapporto: {artifact}"
        ),
    },
    "status_aps_partial_scope": {
        "en": (
            "Partial scope: sensible loads only; required temperature outputs "
            "are not yet runtime-qualified."
        ),
        "de": (
            "Teilumfang: nur fühlbare Lasten; erforderliche "
            "Temperaturausgaben sind noch nicht laufzeitqualifiziert."
        ),
        "fr": (
            "Périmètre partiel : charges sensibles uniquement ; les sorties de "
            "température requises ne sont pas encore qualifiées dans VE."
        ),
        "it": (
            "Ambito parziale: solo carichi sensibili; le uscite di temperatura "
            "richieste non sono ancora qualificate nel runtime."
        ),
    },
    "status_failed_title": {
        "en": "FAILED",
        "de": "FEHLGESCHLAGEN",
        "fr": "ÉCHEC",
        "it": "ESITO NEGATIVO",
    },
    "status_blocked_title": {
        "en": "PREVALIDATION BLOCKED",
        "de": "VORPRÜFUNG BLOCKIERT",
        "fr": "PRÉVALIDATION BLOQUÉE",
        "it": "PREVALIDAZIONE BLOCCATA",
    },
    "status_blocked_detail": {
        "en": "Consult the prevalidation report.",
        "de": "Konsultieren Sie den Vorprüfbericht.",
        "fr": "Consulte le rapport de prévalidation.",
        "it": "Consulta il rapporto di prevalidazione.",
    },
    "status_audit_detail": {
        "en": "Consult the audit report before continuing.",
        "de": "Konsultieren Sie den Auditbericht, bevor Sie fortfahren.",
        "fr": "Consulte le rapport d’audit avant de continuer.",
        "it": "Consulta il rapporto di audit prima di continuare.",
    },
    "status_done_title": {
        "en": "COMPLETED",
        "de": "ABGESCHLOSSEN",
        "fr": "TERMINÉ",
        "it": "COMPLETATO",
    },
    "status_done_detail": {
        "en": "The artifacts were written into the project folder.",
        "de": "Die Artefakte wurden in den Projektordner geschrieben.",
        "fr": "Les artefacts ont été écrits dans le dossier du projet.",
        "it": "Gli artefatti sono stati scritti nella cartella del progetto.",
    },
    # --------------------------------------------------------------- panels
    "project_active": {
        "en": "ACTIVE PROJECT",
        "de": "AKTIVES PROJEKT",
        "fr": "PROJET ACTIF",
        "it": "PROGETTO ATTIVO",
    },
    "log_header": {
        "en": "ACTIVITY LOG",
        "de": "AKTIVITÄTSPROTOKOLL",
        "fr": "JOURNAL D'ACTIVITÉ",
        "it": "REGISTRO ATTIVITÀ",
    },
    "log_ready": {
        "en": "Interface ready. Start with « Prepare and check ».",
        "de": "Oberfläche bereit. Beginnen Sie mit « Vorbereiten und prüfen ».",
        "fr": "Interface prête. Lance d’abord « Préparer et contrôler ».",
        "it": "Interfaccia pronta. Inizia con « Prepara e verifica ».",
    },
    "log_temporary_project": {
        "en": "WARNING - temporary VEPROJ project detected; mutation forbidden.",
        "de": "WARNING - temporäres VEPROJ-Projekt erkannt; Mutation verboten.",
        "fr": "WARNING - projet temporaire VEPROJ détecté ; mutation interdite.",
        "it": "WARNING - progetto VEPROJ temporaneo rilevato; mutazione vietata.",
    },
    "log_operation_done": {
        "en": "operation finished.",
        "de": "Vorgang abgeschlossen.",
        "fr": "opération terminée.",
        "it": "operazione terminata.",
    },
    "log_mvp_bundle": {
        "en": "source-traced case bundle",
        "de": "quellenverfolgbares Fallpaket",
        "fr": "bundle de cas traçable aux sources",
        "it": "pacchetto del caso tracciabile alle fonti",
    },
    # -------------------------------------------------------------- buttons
    "btn_prepare": {
        "en": "Prepare and check",
        "de": "Vorbereiten und prüfen",
        "fr": "Préparer et contrôler",
        "it": "Prepara e verifica",
    },
    "btn_create": {
        "en": "Create in VE",
        "de": "In VE erstellen",
        "fr": "Créer dans VE",
        "it": "Crea in VE",
    },
    "btn_qualify_ve": {
        "en": "Qualify generator in VE",
        "de": "Generator in VE qualifizieren",
        "fr": "Qualifier le générateur dans VE",
        "it": "Qualifica il generatore in VE",
    },
    "btn_simulate_and_evaluate": {
        "en": "Run ApacheSim + evaluate APS",
        "de": "ApacheSim starten + APS auswerten",
        "fr": "Lancer ApacheSim + évaluer l’APS",
        "it": "Avvia ApacheSim + valuta APS",
    },
    "btn_prepare_class": {
        "en": "Prepare the whole class",
        "de": "Gesamte Klasse vorbereiten",
        "fr": "Préparer toute la classe",
        "it": "Prepara l'intera classe",
    },
    "btn_prepare_all_classes": {
        "en": "Prepare all 8 classes",
        "de": "Alle 8 Klassen vorbereiten",
        "fr": "Préparer les 8 classes",
        "it": "Prepara tutte le 8 classi",
    },
    "btn_evaluate_aps": {
        "en": "Evaluate active APS",
        "de": "Aktives APS auswerten",
        "fr": "Évaluer l’APS actif",
        "it": "Valuta l’APS attivo",
    },
    "btn_open_artifacts": {
        "en": "Open artifacts",
        "de": "Artefakte öffnen",
        "fr": "Ouvrir les artefacts",
        "it": "Apri gli artefatti",
    },
    "btn_open_navigator": {
        "en": "Open evidence navigator",
        "de": "Evidenz-Navigator öffnen",
        "fr": "Ouvrir le navigateur de preuves",
        "it": "Apri il navigatore delle evidenze",
    },
    "btn_external_inputs": {
        "en": "External normative inputs",
        "de": "Externe normative Eingaben",
        "fr": "Entrées normatives externes",
        "it": "Input normativi esterni",
    },
    "btn_probe_test2a_runtime": {
        "en": "Probe Test 2A runtime",
        "de": "Test-2A-Laufzeit pruefen",
        "fr": "Sonder le runtime Test 2A",
        "it": "Sonda runtime Test 2A",
    },
    "btn_probe_active_aps": {
        "en": "Probe active APS outputs",
        "de": "Aktive APS-Ausgaben pruefen",
        "fr": "Sonder les sorties APS actives",
        "it": "Sonda le uscite APS attive",
    },
    "btn_qualify_test2a_profiles": {
        "en": "Qualify Test 2A profiles",
        "de": "Test-2A-Profile qualifizieren",
        "fr": "Qualifier les profils Test 2A",
        "it": "Qualifica profili Test 2A",
    },
    "btn_qualify_test2a_shading": {
        "en": "Qualify Test 2A shade setters",
        "de": "Test-2A-Sonnenschutz-Setter qualifizieren",
        "fr": "Qualifier les setters du store Test 2A",
        "it": "Qualifica setter schermatura Test 2A",
    },
    "btn_qualify_test2a_2e1_optics": {
        "en": "Qualify 2E1 fixed-shade optics",
        "de": "Feste 2E1-Sonnenschutzoptik qualifizieren",
        "fr": "Qualifier l’optique fixe 2E1",
        "it": "Qualifica ottica fissa 2E1",
    },
    "btn_probe_test3_runtime": {
        "en": "Probe Test 3 lighting runtime",
        "de": "Test-3-Beleuchtungslaufzeit pruefen",
        "fr": "Sonder le runtime éclairage Test 3",
        "it": "Sonda runtime illuminazione Test 3",
    },
    "btn_probe_hvac_plant_runtime": {
        "en": "Probe Tests 4-7 HVAC/plant runtime",
        "de": "HVAC/Anlagen-Laufzeit Tests 4-7 pruefen",
        "fr": "Sonder le runtime HVAC/energie Tests 4-7",
        "it": "Sonda runtime HVAC/impianti Test 4-7",
    },
    "btn_close": {
        "en": "Close",
        "de": "Schliessen",
        "fr": "Fermer",
        "it": "Chiudi",
    },
    "btn_download_json": {
        "en": "Download the JSON",
        "de": "JSON herunterladen",
        "fr": "Télécharger le JSON",
        "it": "Scarica il JSON",
    },
    "btn_copy": {
        "en": "Copy",
        "de": "Kopieren",
        "fr": "Copier",
        "it": "Copia",
    },
    "toast_downloaded": {
        "en": "JSON file generated.",
        "de": "JSON-Datei erzeugt.",
        "fr": "Fichier JSON généré.",
        "it": "File JSON generato.",
    },
    "toast_copied": {
        "en": "JSON copied.",
        "de": "JSON kopiert.",
        "fr": "JSON copié.",
        "it": "JSON copiato.",
    },
    "toast_copy_failed": {
        "en": "Copy unavailable: use the download instead.",
        "de": "Kopieren nicht verfügbar: Verwenden Sie den Download.",
        "fr": "Copie indisponible : utilise le téléchargement.",
        "it": "Copia non disponibile: usa il download.",
    },
    "usage_hint": {
        "en": (
            "Save the file as {file} in the disposable VE project folder, then "
            "run {script}."
        ),
        "de": (
            "Speichern Sie die Datei als {file} im Ordner des wegwerfbaren "
            "VE-Projekts und führen Sie dann {script} aus."
        ),
        "fr": (
            "Enregistre le fichier sous {file} dans le dossier du projet VE "
            "jetable, puis exécute {script}."
        ),
        "it": (
            "Salva il file come {file} nella cartella del progetto VE usa e "
            "getta, quindi esegui {script}."
        ),
    },
    # -------------------------------------------------------------- dialogs
    "dlg_invalid_scenario": {
        "en": "Invalid scenario",
        "de": "Ungültiges Szenario",
        "fr": "Scénario invalide",
        "it": "Scenario non valido",
    },
    "dlg_prepare_mode_title": {
        "en": "Preparation mode",
        "de": "Vorbereitungsmodus",
        "fr": "Mode préparation",
        "it": "Modalità preparazione",
    },
    "dlg_prepare_mode_body": {
        "en": "Creation is reserved for qualified official cases.",
        "de": "Die Erstellung ist qualifizierten offiziellen Fällen vorbehalten.",
        "fr": "La création est réservée aux cas officiels qualifiés.",
        "it": "La creazione è riservata ai casi ufficiali qualificati.",
    },
    "dlg_aps_unqualified_title": {
        "en": "APS binding not qualified",
        "de": "APS-Bindung nicht qualifiziert",
        "fr": "Liaison APS non qualifiée",
        "it": "Binding APS non qualificato",
    },
    "dlg_aps_unqualified_body": {
        "en": (
            "This exact case has no runtime-qualified APS mapping. Run the "
            "read-only APS probe and qualify the required variables first."
        ),
        "de": (
            "Für diesen exakten Fall gibt es keine laufzeitqualifizierte "
            "APS-Zuordnung. Führen Sie zuerst die schreibgeschützte APS-Prüfung aus."
        ),
        "fr": (
            "Ce cas exact ne possède pas de mapping APS qualifié dans VE. "
            "Exécutez d’abord la sonde APS en lecture seule et qualifiez les variables."
        ),
        "it": (
            "Questo caso esatto non dispone di una mappatura APS qualificata "
            "nel runtime. Esegui prima la sonda APS in sola lettura."
        ),
    },
    "dlg_unsaved_title": {
        "en": "VE project not saved",
        "de": "VE-Projekt nicht gespeichert",
        "fr": "Projet VE non enregistré",
        "it": "Progetto VE non salvato",
    },
    "dlg_unsaved_body": {
        "en": "Save this disposable project into a permanent folder before creating.",
        "de": (
            "Speichern Sie dieses wegwerfbare Projekt vor der Erstellung in einem "
            "permanenten Ordner."
        ),
        "fr": (
            "Enregistre ce projet jetable dans un dossier permanent avant toute "
            "création."
        ),
        "it": (
            "Salva questo progetto usa e getta in una cartella permanente prima "
            "della creazione."
        ),
    },
    "dlg_create_title": {
        "en": "Create in the active VE project?",
        "de": "Im aktiven VE-Projekt erstellen?",
        "fr": "Créer dans le projet VE actif ?",
        "it": "Creare nel progetto VE attivo?",
    },
    "dlg_create_body": {
        "en": (
            "The script will try to create case {case} in the active project "
            "{project}.\n\nPrevalidation will automatically block the operation "
            "if any official data or asset is missing.\n\nContinue?"
        ),
        "de": (
            "Das Skript versucht, den Fall {case} im aktiven Projekt {project} zu "
            "erstellen.\n\nDie Vorprüfung blockiert den Vorgang automatisch, wenn "
            "offizielle Daten oder ein Asset fehlen.\n\nFortfahren?"
        ),
        "fr": (
            "Le script va tenter de créer le cas {case} dans le projet actif "
            "{project}.\n\nLa prévalidation bloquera automatiquement l’opération "
            "si une donnée officielle ou un asset manque.\n\nContinuer ?"
        ),
        "it": (
            "Lo script tenterà di creare il caso {case} nel progetto attivo "
            "{project}.\n\nLa prevalidazione bloccherà automaticamente "
            "l’operazione se mancano dati ufficiali o un asset.\n\nContinuare?"
        ),
    },
    "dlg_qualification_title": {
        "en": "Run the VE runtime qualification?",
        "de": "VE-Laufzeitqualifikation ausführen?",
        "fr": "Exécuter la qualification VE ?",
        "it": "Eseguire la qualifica runtime VE?",
    },
    "dlg_qualification_body": {
        "en": (
            "Case {case} has a source-traced generator that has not yet been "
            "qualified in VE. This operation may modify only the saved "
            "disposable project {project}.\n\nEvery setter is read back and a "
            "failure remains a failed qualification, never a compliance "
            "claim.\n\nContinue?"
        ),
        "de": (
            "Für Fall {case} ist ein quellenverfolgbarer, in VE noch nicht "
            "qualifizierter Generator vorhanden. Der Vorgang darf nur das "
            "gespeicherte Wegwerfprojekt {project} ändern.\n\nJeder gesetzte "
            "Wert wird zurückgelesen; ein Fehler bleibt eine fehlgeschlagene "
            "Qualifikation und wird nie als Konformität ausgegeben.\n\n"
            "Fortfahren?"
        ),
        "fr": (
            "Le cas {case} possède un générateur traçable aux sources qui "
            "n’est pas encore qualifié dans VE. Cette opération ne peut "
            "modifier que le projet jetable enregistré {project}.\n\nChaque "
            "valeur écrite est relue ; un échec reste une qualification "
            "échouée et ne devient jamais une déclaration de conformité.\n\n"
            "Continuer ?"
        ),
        "it": (
            "Il caso {case} dispone di un generatore tracciabile alle fonti "
            "non ancora qualificato in VE. L’operazione può modificare solo "
            "il progetto usa e getta salvato {project}.\n\nOgni valore scritto "
            "viene riletto; un errore resta una qualifica fallita e non diventa "
            "mai una dichiarazione di conformità.\n\nContinuare?"
        ),
    },
    "dlg_qualification_unavailable": {
        "en": "No guarded runtime-qualification generator exists for this case.",
        "de": (
            "Für diesen Fall ist kein abgesicherter Generator zur "
            "Laufzeitqualifikation vorhanden."
        ),
        "fr": (
            "Aucun générateur de qualification VE contrôlé n’existe pour ce cas."
        ),
        "it": (
            "Per questo caso non esiste un generatore controllato di qualifica VE."
        ),
    },
    "dlg_simulation_title": {
        "en": "Run ApacheSim and evaluate the APS?",
        "de": "ApacheSim starten und APS auswerten?",
        "fr": "Lancer ApacheSim et évaluer l’APS ?",
        "it": "Avviare ApacheSim e valutare l’APS?",
    },
    "dlg_simulation_body": {
        "en": (
            "The script will synchronously simulate case {case} in the saved "
            "project {project}, using only the confirmed annual period and "
            "hourly reporting settings. It will then apply the qualified APS "
            "bindings and comparison.\n\nThe calculation timestep and "
            "preconditioning are not prescribed by the supplied Test 1 "
            "specification and will not be silently overwritten.\n\nContinue?"
        ),
        "de": (
            "Das Skript simuliert Fall {case} synchron im gespeicherten Projekt "
            "{project} und setzt nur den bestätigten Jahreszeitraum sowie die "
            "stündliche Ausgabe. Anschliessend werden die qualifizierten "
            "APS-Bindungen und der Vergleich ausgeführt.\n\nRechenzeitschritt "
            "und Vorkonditionierung sind in der gelieferten Testspezifikation "
            "1 nicht vorgeschrieben und werden nicht stillschweigend "
            "überschrieben.\n\nFortfahren?"
        ),
        "fr": (
            "Le script simulera de façon synchrone le cas {case} dans le projet "
            "enregistré {project}, en ne réglant que la période annuelle "
            "confirmée et la sortie horaire. Il appliquera ensuite les "
            "liaisons APS qualifiées et la comparaison.\n\nLe pas de calcul "
            "et le préconditionnement ne sont pas prescrits par la "
            "spécification Test 1 fournie et ne seront pas remplacés "
            "silencieusement.\n\nContinuer ?"
        ),
        "it": (
            "Lo script simulerà in modo sincrono il caso {case} nel progetto "
            "salvato {project}, impostando solo il periodo annuale confermato "
            "e l'output orario. Applicherà quindi i binding APS qualificati e "
            "il confronto.\n\nIl passo di calcolo e il precondizionamento non "
            "sono prescritti dalla specifica Test 1 fornita e non saranno "
            "sovrascritti silenziosamente.\n\nContinuare?"
        ),
    },
    "dlg_simulation_unavailable": {
        "en": (
            "Guarded ApacheSim execution is not available for this case or no "
            "completed exact-case model report is present."
        ),
        "de": (
            "Für diesen Fall ist keine abgesicherte ApacheSim-Ausführung "
            "verfügbar oder der Bericht des vollständig erstellten exakten "
            "Modells fehlt."
        ),
        "fr": (
            "L’exécution ApacheSim contrôlée n’est pas disponible pour ce cas "
            "ou aucun rapport de modèle exact entièrement créé n’est présent."
        ),
        "it": (
            "L'esecuzione ApacheSim controllata non è disponibile per questo "
            "caso oppure manca il rapporto del modello esatto completato."
        ),
    },
    "status_runtime_qualification_available": {
        "en": (
            "A guarded runtime qualification is available for {variant}/{case}; "
            "use a fresh saved disposable project."
        ),
        "de": (
            "Für {variant}/{case} ist eine abgesicherte Laufzeitqualifikation "
            "verfügbar; verwenden Sie ein frisches gespeichertes Wegwerfprojekt."
        ),
        "fr": (
            "Une qualification VE contrôlée est disponible pour "
            "{variant}/{case} ; utilisez un projet jetable neuf et enregistré."
        ),
        "it": (
            "È disponibile una qualifica runtime controllata per "
            "{variant}/{case}; usa un progetto usa e getta nuovo e salvato."
        ),
    },
    "status_test2a_source_binding_ready": {
        "en": (
            "The three Test 2A source bindings are ready. Prepare and check "
            "will write the immutable generator input; VE mutation remains "
            "disabled until profile and fabric-awning setters are qualified."
        ),
        "de": (
            "Die drei Quellenbindungen für Test 2A sind bereit. Vorbereiten "
            "und prüfen schreibt die unveränderliche Generatoreingabe; die "
            "VE-Mutation bleibt bis zur Qualifizierung der Profil- und "
            "Stoffmarkisen-Setter deaktiviert."
        ),
        "fr": (
            "Les trois bindings source du Test 2A sont prêts. Préparer et "
            "contrôler écrira l'entrée immuable du générateur ; la mutation VE "
            "reste désactivée jusqu'à qualification des profils et du store toile."
        ),
        "it": (
            "I tre binding sorgente del Test 2A sono pronti. Prepara e verifica "
            "scriverà l'input immutabile del generatore; la mutazione VE resta "
            "disabilitata fino alla qualifica dei profili e della tenda in tessuto."
        ),
    },
    "dlg_no_artifacts_title": {
        "en": "No artifact",
        "de": "Kein Artefakt",
        "fr": "Aucun artefact",
        "it": "Nessun artefatto",
    },
    "dlg_no_artifacts_body": {
        "en": "Run « Prepare and check » first.",
        "de": "Führen Sie zuerst « Vorbereiten und prüfen » aus.",
        "fr": "Exécute d’abord « Préparer et contrôler ».",
        "it": "Esegui prima « Prepara e verifica ».",
    },
    "dlg_no_navigator_title": {
        "en": "No evidence navigator",
        "de": "Kein Evidenz-Navigator",
        "fr": "Aucun navigateur de preuves",
        "it": "Nessun navigatore delle evidenze",
    },
    "dlg_no_navigator_body": {
        "en": "Run « Prepare all 8 classes » first.",
        "de": "Führen Sie zuerst « Alle 8 Klassen vorbereiten » aus.",
        "fr": "Exécute d’abord « Préparer les 8 classes ».",
        "it": "Esegui prima « Prepara tutte le 8 classi ».",
    },
    "dlg_external_inputs_title": {
        "en": "External normative inputs",
        "de": "Externe normative Eingaben",
        "fr": "Entrées normatives externes",
        "it": "Input normativi esterni",
    },
    "dlg_external_inputs_created": {
        "en": (
            "A fail-closed evidence template was created and opened:\n{path}\n\n"
            "The normalized Test 2A binding templates are in:\n{templates}\n\n"
            "Complete only fields supported by real source, licence and "
            "technical-validation evidence. This action does not enable a "
            "generator by itself."
        ),
        "de": (
            "Eine Fail-Closed-Evidenzvorlage wurde erstellt und geöffnet:\n"
            "{path}\n\nDie normalisierten Bindungsvorlagen für Test 2A liegen "
            "unter:\n{templates}\n\nFüllen Sie nur Felder aus, die durch echte Quellen-, "
            "Lizenz- und technische Validierungsnachweise belegt sind. Diese "
            "Aktion aktiviert keinen Generator."
        ),
        "fr": (
            "Un modèle de preuves fail-closed a été créé et ouvert :\n{path}\n\n"
            "Les modèles de binding normalisé du Test 2A se trouvent dans :\n"
            "{templates}\n\n"
            "Complétez uniquement les champs étayés par une source réelle, "
            "une licence et un rapport de validation technique. Cette action "
            "n'active aucun générateur à elle seule."
        ),
        "it": (
            "È stato creato e aperto un modello di evidenza fail-closed:\n"
            "{path}\n\nI modelli di binding normalizzato del Test 2A sono in:\n"
            "{templates}\n\nCompila solo i campi supportati da fonti, licenze e "
            "validazioni tecniche reali. Questa azione non abilita da sola "
            "alcun generatore."
        ),
    },
    "status_external_inputs": {
        "en": "External inputs: {action} — {path}",
        "de": "Externe Eingaben: {action} — {path}",
        "fr": "Entrées externes : {action} — {path}",
        "it": "Input esterni: {action} — {path}",
    },
    "external_inputs_created": {
        "en": "template created",
        "de": "Vorlage erstellt",
        "fr": "modèle créé",
        "it": "modello creato",
    },
    "external_inputs_existing": {
        "en": "existing manifest validated",
        "de": "vorhandenes Manifest validiert",
        "fr": "manifeste existant validé",
        "it": "manifesto esistente convalidato",
    },
    "dlg_test2a_probe_title": {
        "en": "Test 2A runtime capability",
        "de": "Test-2A-Laufzeitfaehigkeit",
        "fr": "Capacite runtime du Test 2A",
        "it": "Capacita runtime Test 2A",
    },
    "dlg_test2a_probe_unavailable": {
        "en": "Select the official test_2A / 2A case in a saved project.",
        "de": (
            "Waehlen Sie den offiziellen Fall test_2A / 2A in einem "
            "gespeicherten Projekt."
        ),
        "fr": (
            "Selectionnez le cas officiel test_2A / 2A dans un projet "
            "enregistre."
        ),
        "it": (
            "Seleziona il caso ufficiale test_2A / 2A in un progetto salvato."
        ),
    },
    "dlg_test2a_probe_complete": {
        "en": (
            "Read-only probe status: {status}\n\nReport: {report}\n\n"
            "No VE object was changed."
        ),
        "de": (
            "Status der schreibgeschuetzten Pruefung: {status}\n\n"
            "Bericht: {report}\n\nKein VE-Objekt wurde geaendert."
        ),
        "fr": (
            "Statut de la sonde en lecture seule : {status}\n\n"
            "Rapport : {report}\n\nAucun objet VE n'a ete modifie."
        ),
        "it": (
            "Stato della sonda in sola lettura: {status}\n\n"
            "Rapporto: {report}\n\nNessun oggetto VE e stato modificato."
        ),
    },
    "status_test2a_probe": {
        "en": "Test 2A read-only runtime probe: {status} - {report}",
        "de": "Test-2A-Laufzeitpruefung (nur Lesen): {status} - {report}",
        "fr": "Sonde runtime Test 2A en lecture seule : {status} - {report}",
        "it": "Sonda runtime Test 2A in sola lettura: {status} - {report}",
    },
    "dlg_test3_probe_title": {
        "en": "Test 3 lighting runtime capability",
        "de": "Test-3-Beleuchtungslaufzeitfaehigkeit",
        "fr": "Capacité runtime éclairage du Test 3",
        "it": "Capacità runtime illuminazione Test 3",
    },
    "dlg_test3_probe_unavailable": {
        "en": (
            "Prepare and select one exact official Test 3A-3L case in a saved "
            "disposable project."
        ),
        "de": (
            "Bereiten Sie in einem gespeicherten Wegwerfprojekt einen exakten "
            "offiziellen Fall Test 3A-3L vor und waehlen Sie ihn aus."
        ),
        "fr": (
            "Préparez et sélectionnez un cas officiel exact Test 3A-3L dans "
            "un projet jetable enregistré."
        ),
        "it": (
            "Prepara e seleziona un caso ufficiale esatto Test 3A-3L in un "
            "progetto usa e getta salvato."
        ),
    },
    "dlg_test3_probe_complete": {
        "en": (
            "Read-only Test 3 probe: {status}\n\nLighting fields: {fields}\n"
            "Sensor-related members: {sensors}\n\nReport: {report}\n\n"
            "All 12 variants were audited. No VE object was changed."
        ),
        "de": (
            "Schreibgeschuetzte Test-3-Pruefung: {status}\n\n"
            "Beleuchtungsfelder: {fields}\nSensorbezogene Mitglieder: "
            "{sensors}\n\nBericht: {report}\n\nAlle 12 Varianten wurden "
            "geprueft. Kein VE-Objekt wurde geaendert."
        ),
        "fr": (
            "Sonde Test 3 en lecture seule : {status}\n\nChamps éclairage : "
            "{fields}\nMembres liés aux capteurs : {sensors}\n\nRapport : "
            "{report}\n\nLes 12 variantes ont été auditées. Aucun objet VE "
            "n’a été modifié."
        ),
        "it": (
            "Sonda Test 3 in sola lettura: {status}\n\nCampi illuminazione: "
            "{fields}\nMembri relativi ai sensori: {sensors}\n\nRapporto: "
            "{report}\n\nTutte le 12 varianti sono state verificate. Nessun "
            "oggetto VE è stato modificato."
        ),
    },
    "status_test3_probe": {
        "en": (
            "Test 3 runtime probe {status}: {fields} lighting fields, "
            "{sensors} sensor members - {report}"
        ),
        "de": (
            "Test-3-Laufzeitpruefung {status}: {fields} Beleuchtungsfelder, "
            "{sensors} Sensormitglieder - {report}"
        ),
        "fr": (
            "Sonde runtime Test 3 {status} : {fields} champs éclairage, "
            "{sensors} membres capteur - {report}"
        ),
        "it": (
            "Sonda runtime Test 3 {status}: {fields} campi illuminazione, "
            "{sensors} membri sensore - {report}"
        ),
    },
    "dlg_hvac_plant_probe_title": {
        "en": "Tests 4-7 HVAC and plant runtime capability",
        "de": "HVAC- und Anlagen-Laufzeitfaehigkeit Tests 4-7",
        "fr": "Capacite runtime HVAC et energie Tests 4-7",
        "it": "Capacita runtime HVAC e impianti Test 4-7",
    },
    "dlg_hvac_plant_probe_unavailable": {
        "en": "Prepare and select one exact official Test 4, 5A-5D, 6 or 7 case in a saved disposable project.",
        "de": "Bereiten Sie in einem gespeicherten Wegwerfprojekt einen exakten offiziellen Fall Test 4, 5A-5D, 6 oder 7 vor.",
        "fr": "Preparez et selectionnez un cas officiel exact Test 4, 5A-5D, 6 ou 7 dans un projet jetable enregistre.",
        "it": "Prepara e seleziona un caso ufficiale esatto Test 4, 5A-5D, 6 o 7 in un progetto usa e getta salvato.",
    },
    "dlg_hvac_plant_probe_complete": {
        "en": "Read-only Tests 4-7 probe: {status}. Apache collection: {apache}; room read-back: {room}; plant members: {plant}. All 7 exact cases were audited. No VE object was changed. Report: {report}",
        "de": "Schreibgeschuetzte Tests-4-7-Pruefung: {status}. Apache-Sammlung: {apache}; Raum-Readback: {room}; Anlagenmitglieder: {plant}. Alle 7 exakten Faelle wurden geprueft. Kein VE-Objekt wurde geaendert. Bericht: {report}",
        "fr": "Sonde Tests 4-7 en lecture seule : {status}. Collection Apache : {apache} ; relecture zone : {room} ; membres energie : {plant}. Les 7 cas exacts ont ete audites. Aucun objet VE n'a ete modifie. Rapport : {report}",
        "it": "Sonda Test 4-7 in sola lettura: {status}. Collezione Apache: {apache}; lettura zona: {room}; membri impianto: {plant}. Tutti i 7 casi esatti sono stati verificati. Nessun oggetto VE e stato modificato. Rapporto: {report}",
    },
    "status_hvac_plant_probe": {
        "en": "Tests 4-7 runtime probe {status}: Apache={apache}, room={room}, plant members={plant} - {report}",
        "de": "Tests-4-7-Laufzeitpruefung {status}: Apache={apache}, Raum={room}, Anlagenmitglieder={plant} - {report}",
        "fr": "Sonde runtime Tests 4-7 {status} : Apache={apache}, zone={room}, membres energie={plant} - {report}",
        "it": "Sonda runtime Test 4-7 {status}: Apache={apache}, zona={room}, membri impianto={plant} - {report}",
    },
    "status_probing_aps_detail": {
        "en": "Reading room and exact surface-handle APS series.",
        "de": "Raum- und exakte Oberflaechen-APS-Reihen werden gelesen.",
        "fr": "Lecture des series APS de zone et des surfaces identifiees.",
        "it": "Lettura delle serie APS di zona e delle superfici identificate.",
    },
    "status_aps_probe": {
        "en": (
            "APS probe {status}; {surfaces} surface series "
            "({surface_status}); report: {report}"
        ),
        "de": (
            "APS-Pruefung {status}; {surfaces} Oberflaechenreihen "
            "({surface_status}); Bericht: {report}"
        ),
        "fr": (
            "Sonde APS {status} ; {surfaces} series de surface "
            "({surface_status}) ; rapport : {report}"
        ),
        "it": (
            "Sonda APS {status}; {surfaces} serie di superficie "
            "({surface_status}); rapporto: {report}"
        ),
    },
    "dlg_aps_probe_title": {
        "en": "APS output capability",
        "de": "APS-Ausgabefaehigkeit",
        "fr": "Capacite des sorties APS",
        "it": "Capacita delle uscite APS",
    },
    "dlg_aps_probe_unavailable": {
        "en": "Save the project and run ApacheSim before probing APS outputs.",
        "de": (
            "Speichern Sie das Projekt und starten Sie ApacheSim, bevor Sie "
            "APS-Ausgaben pruefen."
        ),
        "fr": (
            "Enregistrez le projet et lancez ApacheSim avant de sonder les "
            "sorties APS."
        ),
        "it": (
            "Salva il progetto ed esegui ApacheSim prima di sondare le "
            "uscite APS."
        ),
    },
    "dlg_aps_probe_complete": {
        "en": (
            "Read-only APS probe: {status}\n\nSurface series: {surfaces} "
            "({surface_status})\n\nReport: {report}\n\nNo VE or APS data "
            "was changed."
        ),
        "de": (
            "APS-Pruefung nur lesend: {status}\n\nOberflaechenreihen: "
            "{surfaces} ({surface_status})\n\nBericht: {report}\n\nKeine "
            "VE- oder APS-Daten wurden geaendert."
        ),
        "fr": (
            "Sonde APS en lecture seule : {status}\n\nSeries de surface : "
            "{surfaces} ({surface_status})\n\nRapport : {report}\n\nAucune "
            "donnee VE ou APS n'a ete modifiee."
        ),
        "it": (
            "Sonda APS in sola lettura: {status}\n\nSerie di superficie: "
            "{surfaces} ({surface_status})\n\nRapporto: {report}\n\nNessun "
            "dato VE o APS e stato modificato."
        ),
    },
    "dlg_test2a_profile_qualification_title": {
        "en": "Test 2A profile qualification",
        "de": "Test-2A-Profilqualifizierung",
        "fr": "Qualification des profils Test 2A",
        "it": "Qualificazione profili Test 2A",
    },
    "dlg_test2a_profile_qualification_unavailable": {
        "en": (
            "Run the read-only Test 2A runtime probe first. Profile mutation "
            "is enabled only when that probe is ready."
        ),
        "de": (
            "Fuehren Sie zuerst die schreibgeschuetzte Test-2A-"
            "Laufzeitpruefung aus. Die Profilmutation wird nur bei einem "
            "bereiten Ergebnis freigegeben."
        ),
        "fr": (
            "Exécute d’abord la sonde runtime Test 2A en lecture seule. La "
            "mutation des profils n’est activée que si cette sonde est prête."
        ),
        "it": (
            "Esegui prima la sonda runtime Test 2A in sola lettura. La "
            "mutazione dei profili viene abilitata solo se la sonda è pronta."
        ),
    },
    "dlg_test2a_profile_qualification_body": {
        "en": (
            "This will create only the source-bound daily, weekly and yearly "
            "profiles in disposable project {project}. Existing references "
            "cause a fail-closed stop. Continue?"
        ),
        "de": (
            "Dies erstellt nur die quellengebundenen Tages-, Wochen- und "
            "Jahresprofile im Wegwerfprojekt {project}. Vorhandene Referenzen "
            "fuehren zu einem sicheren Abbruch. Fortfahren?"
        ),
        "fr": (
            "Cette opération créera uniquement les profils journaliers, "
            "hebdomadaires et annuels liés aux sources dans le projet jetable "
            "{project}. Toute référence existante provoquera un arrêt "
            "fail-closed. Continuer ?"
        ),
        "it": (
            "Questa operazione creerà solo i profili giornalieri, settimanali "
            "e annuali legati alle fonti nel progetto usa e getta {project}. "
            "Un riferimento esistente provoca un arresto fail-closed. "
            "Continuare?"
        ),
    },
    "dlg_test2a_profile_qualification_complete": {
        "en": (
            "Profile creation and exact read-back passed.\n\nReport: {report}\n\n"
            "No other VE object was changed."
        ),
        "de": (
            "Profilerstellung und exaktes Ruecklesen bestanden.\n\n"
            "Bericht: {report}\n\nKein anderes VE-Objekt wurde geaendert."
        ),
        "fr": (
            "La création et la relecture exacte des profils ont réussi.\n\n"
            "Rapport : {report}\n\nAucun autre objet VE n’a été modifié."
        ),
        "it": (
            "Creazione e rilettura esatta dei profili superate.\n\n"
            "Rapporto: {report}\n\nNessun altro oggetto VE è stato modificato."
        ),
    },
    "status_test2a_profile_qualification": {
        "en": "Test 2A profile qualification: {count} profiles - {report}",
        "de": "Test-2A-Profilqualifizierung: {count} Profile - {report}",
        "fr": "Qualification des profils Test 2A : {count} profils - {report}",
        "it": "Qualificazione profili Test 2A: {count} profili - {report}",
    },
    "dlg_test2a_shading_qualification_title": {
        "en": "Test 2A shade setter qualification",
        "de": "Test-2A-Sonnenschutz-Setter-Qualifizierung",
        "fr": "Qualification des setters du store Test 2A",
        "it": "Qualificazione setter schermatura Test 2A",
    },
    "dlg_test2a_shading_qualification_unavailable": {
        "en": (
            "Run the read-only Test 2A runtime probe first. CDB mutation is "
            "enabled only when that probe is ready."
        ),
        "de": (
            "Fuehren Sie zuerst die schreibgeschuetzte Test-2A-"
            "Laufzeitpruefung aus. Die CDB-Mutation wird nur bei einem "
            "bereiten Ergebnis freigegeben."
        ),
        "fr": (
            "Exécutez d’abord la sonde runtime Test 2A en lecture seule. La "
            "mutation CDB n’est activée que lorsque cette sonde est prête."
        ),
        "it": (
            "Esegui prima la sonda runtime Test 2A in sola lettura. La "
            "mutazione CDB viene abilitata solo quando la sonda è pronta."
        ),
    },
    "dlg_test2a_shading_qualification_body": {
        "en": (
            "This creates one unassigned glazed CDB construction in disposable "
            "project {project} and tests only the active flag and the two "
            "150 W/m2 threshold setters. It does not qualify dynamic behaviour "
            "or optics. Continue?"
        ),
        "de": (
            "Dies erstellt eine nicht zugewiesene verglaste CDB-Konstruktion "
            "im Wegwerfprojekt {project} und prueft nur das Aktiv-Flag sowie "
            "die beiden 150-W/m2-Schwellenwert-Setter. Dynamik und Optik werden "
            "nicht qualifiziert. Fortfahren?"
        ),
        "fr": (
            "Cette opération crée une construction vitrée CDB non affectée "
            "dans le projet jetable {project} et teste uniquement le drapeau "
            "actif ainsi que les deux setters de seuil à 150 W/m². Elle ne "
            "qualifie ni le comportement dynamique ni l’optique. Continuer ?"
        ),
        "it": (
            "Questa operazione crea una costruzione vetrata CDB non assegnata "
            "nel progetto usa e getta {project} e verifica solo il flag attivo "
            "e i due setter di soglia a 150 W/m². Non qualifica il comportamento "
            "dinamico né l’ottica. Continuare?"
        ),
    },
    "dlg_test2a_shading_qualification_complete": {
        "en": (
            "CDB shade-field storage and exact read-back passed.\n\n"
            "Report: {report}\n\nDynamic equality, timestep handling and "
            "Soltis optical equivalence remain blocked."
        ),
        "de": (
            "Speicherung und exaktes Ruecklesen der CDB-Sonnenschutzfelder "
            "bestanden.\n\nBericht: {report}\n\nDynamische Gleichheit, "
            "Zeitschrittbehandlung und optische Soltis-Aequivalenz bleiben "
            "gesperrt."
        ),
        "fr": (
            "Le stockage et la relecture exacte des champs CDB du store ont "
            "réussi.\n\nRapport : {report}\n\nL’égalité dynamique, la gestion "
            "des pas de temps et l’équivalence optique Soltis restent bloquées."
        ),
        "it": (
            "Memorizzazione e rilettura esatta dei campi CDB della schermatura "
            "superate.\n\nRapporto: {report}\n\nUguaglianza dinamica, gestione "
            "del passo temporale ed equivalenza ottica Soltis restano bloccate."
        ),
    },
    "status_test2a_shading_qualification": {
        "en": (
            "Test 2A shade setter qualification: construction {construction} "
            "- {report}"
        ),
        "de": (
            "Test-2A-Sonnenschutz-Setter: Konstruktion {construction} - {report}"
        ),
        "fr": (
            "Qualification des setters du store Test 2A : construction "
            "{construction} - {report}"
        ),
        "it": (
            "Qualificazione setter schermatura Test 2A: costruzione "
            "{construction} - {report}"
        ),
    },
    "dlg_test2a_2e1_optical_title": {
        "en": "Test 2A / 2E1 fixed-shade optical qualification",
        "de": "Test 2A / 2E1 Qualifizierung der festen Sonnenschutzoptik",
        "fr": "Qualification optique du store fixe Test 2A / 2E1",
        "it": "Qualificazione ottica schermatura fissa Test 2A / 2E1",
    },
    "dlg_test2a_2e1_optical_unavailable": {
        "en": (
            "First pass the read-only Test 2A runtime probe and the shade "
            "threshold setter qualification in this disposable project."
        ),
        "de": (
            "Fuehren Sie in diesem Wegwerfprojekt zuerst die "
            "schreibgeschuetzte Test-2A-Laufzeitpruefung und die "
            "Qualifizierung der Sonnenschutz-Schwellenwert-Setter aus."
        ),
        "fr": (
            "Dans ce projet jetable, réussissez d’abord la sonde runtime "
            "Test 2A en lecture seule puis la qualification des setters de "
            "seuil du store."
        ),
        "it": (
            "In questo progetto usa e getta, completa prima la sonda runtime "
            "Test 2A in sola lettura e la qualificazione dei setter di soglia "
            "della schermatura."
        ),
    },
    "dlg_test2a_2e1_optical_body": {
        "en": (
            "This creates one additional unassigned glazed CDB construction "
            "in disposable project {project}. It writes and reads back only "
            "direct-name fixed-closed optical fields. It changes no geometry, "
            "opening, layer, template or simulation. Continue?"
        ),
        "de": (
            "Dies erstellt eine weitere nicht zugewiesene verglaste "
            "CDB-Konstruktion im Wegwerfprojekt {project}. Nur direkt "
            "zuordenbare Optikfelder fuer den dauerhaft geschlossenen Zustand "
            "werden geschrieben und zurueckgelesen. Geometrie, Oeffnung, "
            "Schicht, Vorlage und Simulation bleiben unveraendert. Fortfahren?"
        ),
        "fr": (
            "Cette opération crée une construction vitrée CDB supplémentaire "
            "non affectée dans le projet jetable {project}. Elle écrit et relit "
            "uniquement les champs optiques à correspondance directe pour "
            "l’état toujours fermé. Elle ne modifie ni géométrie, ni ouverture, "
            "ni couche, ni template, ni simulation. Continuer ?"
        ),
        "it": (
            "Questa operazione crea un’ulteriore costruzione vetrata CDB non "
            "assegnata nel progetto usa e getta {project}. Scrive e rilegge "
            "solo i campi ottici a corrispondenza diretta per lo stato sempre "
            "chiuso. Non modifica geometria, apertura, strato, template o "
            "simulazione. Continuare?"
        ),
    },
    "dlg_test2a_2e1_optical_complete": {
        "en": (
            "Direct-name fixed-closed CDB field storage passed.\n\n"
            "Report: {report}\n\nRebuilt bundle: {bundle_status}\n"
            "{bundle}\n\nAngular transmittance, inside reflectance, "
            "visible transmittance, secondary heat transfer and APS output "
            "equivalence remain explicitly blocked."
        ),
        "de": (
            "Die Speicherung direkt zuordenbarer CDB-Felder fuer den dauerhaft "
            "geschlossenen Zustand wurde bestanden.\n\nBericht: {report}\n\n"
            "Neu erstelltes Bundle: {bundle_status}\n{bundle}\n\n"
            "Winkelabhaengige Transmission, innere Reflexion, sichtbare "
            "Transmission, sekundaerer Waermetransport und APS-"
            "Ausgabeaequivalenz bleiben ausdruecklich gesperrt."
        ),
        "fr": (
            "Le stockage des champs CDB à correspondance directe pour l’état "
            "toujours fermé a réussi.\n\nRapport : {report}\n\nBundle "
            "reconstruit : {bundle_status}\n{bundle}\n\nLa transmission "
            "angulaire, la réflexion intérieure, la transmission visible, le "
            "transfert thermique secondaire et l’équivalence des sorties APS "
            "restent explicitement bloqués."
        ),
        "it": (
            "La memorizzazione dei campi CDB a corrispondenza diretta per lo "
            "stato sempre chiuso è riuscita.\n\nRapporto: {report}\n\n"
            "Bundle ricostruito: {bundle_status}\n{bundle}\n\n"
            "Trasmissione angolare, riflessione interna, trasmissione visibile, "
            "trasferimento termico secondario ed equivalenza delle uscite APS "
            "restano esplicitamente bloccati."
        ),
    },
    "status_test2a_2e1_optical": {
        "en": (
            "Test 2A / 2E1 fixed-shade CDB storage: construction "
            "{construction}; bundle {bundle_status} - {bundle}; report {report}"
        ),
        "de": (
            "Test 2A / 2E1 CDB-Speicherung der festen Sonnenschutzoptik: "
            "Konstruktion {construction}; Bundle {bundle_status} - {bundle}; "
            "Bericht {report}"
        ),
        "fr": (
            "Stockage CDB du store fixe Test 2A / 2E1 : construction "
            "{construction} ; bundle {bundle_status} - {bundle} ; rapport "
            "{report}"
        ),
        "it": (
            "Memorizzazione CDB schermatura fissa Test 2A / 2E1: costruzione "
            "{construction}; bundle {bundle_status} - {bundle}; rapporto "
            "{report}"
        ),
    },
    "status_navigator_summary": {
        "en": (
            "Evidence navigator: {models}/{total} models, "
            "{simulations}/{total} simulations, {evaluations} linked APS "
            "evaluations."
        ),
        "de": (
            "Evidenz-Navigator: {models}/{total} Modelle, "
            "{simulations}/{total} Simulationen, {evaluations} verknüpfte "
            "APS-Auswertungen."
        ),
        "fr": (
            "Navigateur de preuves : {models}/{total} modèles, "
            "{simulations}/{total} simulations, {evaluations} évaluations APS "
            "liées."
        ),
        "it": (
            "Navigatore delle evidenze: {models}/{total} modelli, "
            "{simulations}/{total} simulazioni, {evaluations} valutazioni APS "
            "collegate."
        ),
    },
    "report_title": {
        "en": "SIA Compliance Report",
        "de": "SIA-Konformitätsbericht",
        "fr": "Rapport de conformité SIA",
        "it": "Rapporto di conformità SIA",
    },
    "report_subtitle": {
        "en": "Assessment of one IESVE model against SIA 380/2:2022 and SIA 4010:2023",
        "de": "Beurteilung eines IESVE-Modells nach SIA 380/2:2022 und SIA 4010:2023",
        "fr": "Évaluation d'un modèle IESVE selon SIA 380/2:2022 et SIA 4010:2023",
        "it": "Valutazione di un modello IESVE secondo SIA 380/2:2022 e SIA 4010:2023",
    },
    "verdict_heading": {
        "en": "Assessed result",
        "de": "Beurteiltes Ergebnis",
        "fr": "Résultat évalué",
        "it": "Risultato valutato",
    },
    "verdict_compliant": {
        "en": "COMPLIANT",
        "de": "KONFORM",
        "fr": "CONFORME",
        "it": "CONFORME",
    },
    "verdict_not_compliant": {
        "en": "NOT COMPLIANT",
        "de": "NICHT KONFORM",
        "fr": "NON CONFORME",
        "it": "NON CONFORME",
    },
    "verdict_not_determined": {
        "en": "NOT DETERMINED",
        "de": "NICHT BESTIMMT",
        "fr": "NON DÉTERMINÉ",
        "it": "NON DETERMINATO",
    },
    "findings_blocking_advisory": {
        "en": "Blocking / advisory findings",
        "de": "Blockierende / hinweisende Befunde",
        "fr": "Constats bloquants / indicatifs",
        "it": "Riscontri bloccanti / indicativi",
    },
    "section_identification": {
        "en": "Identification",
        "de": "Identifikation",
        "fr": "Identification",
        "it": "Identificazione",
    },
    "section_domains": {
        "en": "Assessment by SIA 380/2 domain",
        "de": "Beurteilung nach SIA 380/2-Bereich",
        "fr": "Évaluation par domaine SIA 380/2",
        "it": "Valutazione per ambito SIA 380/2",
    },
    "section_model": {
        "en": "Analysed model (schematic)",
        "de": "Analysiertes Modell (schematisch)",
        "fr": "Modèle analysé (schéma)",
        "it": "Modello analizzato (schema)",
    },
    "section_key_figures": {
        "en": "Key figures",
        "de": "Kennzahlen",
        "fr": "Chiffres clés",
        "it": "Dati chiave",
    },
    "section_signature": {
        "en": "Issued by",
        "de": "Ausgestellt von",
        "fr": "Établi par",
        "it": "Redatto da",
    },
    "column_domain": {
        "en": "Domain",
        "de": "Bereich",
        "fr": "Domaine",
        "it": "Ambito",
    },
    "column_status": {
        "en": "Status",
        "de": "Status",
        "fr": "Statut",
        "it": "Stato",
    },
    "column_blocking": {
        "en": "Blocking",
        "de": "Blockierend",
        "fr": "Bloquants",
        "it": "Bloccanti",
    },
    "column_advisory": {
        "en": "Advisory",
        "de": "Hinweisend",
        "fr": "Indicatifs",
        "it": "Indicativi",
    },
    "domain_envelope": {
        "en": "Envelope",
        "de": "Gebäudehülle",
        "fr": "Enveloppe",
        "it": "Involucro",
    },
    "domain_openings": {
        "en": "Openings and glazing",
        "de": "Öffnungen und Verglasung",
        "fr": "Ouvertures et vitrages",
        "it": "Aperture e vetrate",
    },
    "domain_ventilation": {
        "en": "Ventilation",
        "de": "Lüftung",
        "fr": "Ventilation",
        "it": "Ventilazione",
    },
    "domain_gains": {
        "en": "Internal gains",
        "de": "Interne Wärmelasten",
        "fr": "Apports internes",
        "it": "Apporti interni",
    },
    "domain_setpoints": {
        "en": "Operating setpoints",
        "de": "Betriebs-Sollwerte",
        "fr": "Consignes d'exploitation",
        "it": "Valori di regolazione",
    },
    "domain_hvac": {
        "en": "HVAC systems",
        "de": "HLK-Anlagen",
        "fr": "Installations CVC",
        "it": "Impianti HVAC",
    },
    "legend_opaque": {
        "en": "Opaque envelope",
        "de": "Opake Hülle",
        "fr": "Enveloppe opaque",
        "it": "Involucro opaco",
    },
    "legend_glazed": {
        "en": "Glazing",
        "de": "Verglasung",
        "fr": "Vitrages",
        "it": "Vetrate",
    },
    "figure_rooms": {
        "en": "Thermal rooms",
        "de": "Thermische Räume",
        "fr": "Locaux thermiques",
        "it": "Locali termici",
    },
    "figure_floor_area": {
        "en": "Net floor area",
        "de": "Nettogeschossfläche",
        "fr": "Surface de plancher nette",
        "it": "Superficie netta",
    },
    "figure_volume": {
        "en": "Volume",
        "de": "Volumen",
        "fr": "Volume",
        "it": "Volume",
    },
    "figure_opaque": {
        "en": "External opaque area",
        "de": "Externe opake Fläche",
        "fr": "Surface opaque extérieure",
        "it": "Superficie opaca esterna",
    },
    "figure_glazed": {
        "en": "External glazed area",
        "de": "Externe Verglasungsfläche",
        "fr": "Surface vitrée extérieure",
        "it": "Superficie vetrata esterna",
    },
    "figure_wwr": {
        "en": "Window-to-wall ratio",
        "de": "Fensterflächenanteil",
        "fr": "Taux de vitrage",
        "it": "Rapporto vetrato/parete",
    },
    "field_project": {
        "en": "Project",
        "de": "Projekt",
        "fr": "Projet",
        "it": "Progetto",
    },
    "field_model": {
        "en": "VE model",
        "de": "VE-Modell",
        "fr": "Modèle VE",
        "it": "Modello VE",
    },
    "field_generated": {
        "en": "Generated",
        "de": "Erstellt",
        "fr": "Généré",
        "it": "Generato",
    },
    "field_framework": {
        "en": "Regulatory framework",
        "de": "Regelwerk",
        "fr": "Cadre réglementaire",
        "it": "Quadro normativo",
    },
    "field_reference": {
        "en": "Report reference",
        "de": "Berichtsreferenz",
        "fr": "Référence du rapport",
        "it": "Riferimento rapporto",
    },
    "value_unavailable": {
        "en": "Not specified",
        "de": "Nicht angegeben",
        "fr": "Non spécifié",
        "it": "Non specificato",
    },
    "company_unspecified": {
        "en": "Engineering office not configured",
        "de": "Ingenieurbüro nicht konfiguriert",
        "fr": "Bureau d'ingénieurs non configuré",
        "it": "Studio di ingegneria non configurato",
    },
    "sia4010_readiness_attestation_required": {
        "en": "SIA 4010: readiness, attestation required",
        "de": "SIA 4010: Bereitschaft, Bestätigung erforderlich",
        "fr": "SIA 4010 : readiness, attestation requise",
        "it": "SIA 4010: predisposizione, attestazione richiesta",
    },
    "scope_line_1": {
        "en": (
            "This is an engineering assessment of the analysed model. It is not "
            "an official SIA certificate and not an SIA 4010 validation "
            "attestation."
        ),
        "de": (
            "Dies ist eine ingenieurtechnische Beurteilung des analysierten "
            "Modells. Es ist kein offizielles Zertifikat der SIA und keine "
            "Validierungsbestätigung nach SIA 4010."
        ),
        "fr": (
            "Ceci est une évaluation d'ingénierie du modèle analysé. Ce n'est "
            "pas un certificat SIA officiel ni une attestation de validation "
            "SIA 4010."
        ),
        "it": (
            "Questa è una valutazione ingegneristica del modello analizzato. "
            "Non è un certificato SIA ufficiale né un'attestazione di "
            "validazione SIA 4010."
        ),
    },
    "scope_line_2": {
        "en": (
            "A SIA 380/2 compliance conclusion requires the reviewed "
            "project/reference comparison; SIA 4010 validation requires SIA "
            "sub-commission attestation."
        ),
        "de": (
            "Eine Konformitätsaussage nach SIA 380/2 erfordert den geprüften "
            "Projekt-/Referenzvergleich; die Validierung nach SIA 4010 "
            "erfordert die Bestätigung der SIA-Subkommission."
        ),
        "fr": (
            "Une conclusion de conformité SIA 380/2 exige la comparaison "
            "projet/référence vérifiée ; la validation SIA 4010 exige "
            "l'attestation de la sous-commission SIA."
        ),
        "it": (
            "Una conclusione di conformità SIA 380/2 richiede il confronto "
            "progetto/riferimento verificato; la validazione SIA 4010 richiede "
            "l'attestazione della sottocommissione SIA."
        ),
    },
    "scope_outstanding": {
        "en": "Outstanding evidence: {items}.",
        "de": "Ausstehende Nachweise: {items}.",
        "fr": "Évidences manquantes : {items}.",
        "it": "Evidenze mancanti: {items}.",
    },
    "outstanding_global_reference_comparison": {
        "en": "reviewed project/reference comparison",
        "de": "geprüfter Projekt-/Referenzvergleich",
        "fr": "comparaison projet/référence vérifiée",
        "it": "confronto progetto/riferimento verificato",
    },
    "outstanding_sia3802_domain_evidence": {
        "en": "outstanding SIA 380/2 domain evidence",
        "de": "fehlende Nachweise zu den Bereichen nach SIA 380/2",
        "fr": "preuves manquantes par domaine SIA 380/2",
        "it": "prove mancanti per dominio SIA 380/2",
    },
    "outstanding_sia4010_official_results": {
        "en": "official SIA 4010 test results",
        "de": "offizielle Testergebnisse nach SIA 4010",
        "fr": "résultats officiels des tests SIA 4010",
        "it": "risultati ufficiali dei test SIA 4010",
    },
    "outstanding_sia4010_validation_class": {
        "en": "selected SIA 4010 validation class",
        "de": "gewählte Validierungsklasse nach SIA 4010",
        "fr": "classe de validation SIA 4010 retenue",
        "it": "classe di validazione SIA 4010 selezionata",
    },
    "outstanding_sia4010_class_readiness": {
        "en": "SIA 4010 class readiness record",
        "de": "Klassenbereitschaftsnachweis nach SIA 4010",
        "fr": "relevé de préparation des classes SIA 4010",
        "it": "registro di preparazione delle classi SIA 4010",
    },
    "signature_name": {
        "en": "Name",
        "de": "Name",
        "fr": "Nom",
        "it": "Nome",
    },
    "signature_role": {
        "en": "Function",
        "de": "Funktion",
        "fr": "Fonction",
        "it": "Funzione",
    },
    "signature_date": {
        "en": "Date and signature",
        "de": "Datum und Unterschrift",
        "fr": "Date et signature",
        "it": "Data e firma",
    },
    "footer_not_certificate": {
        "en": "Engineering assessment report - not an official SIA certificate.",
        "de": (
            "Ingenieurtechnischer Beurteilungsbericht - kein offizielles "
            "SIA-Zertifikat."
        ),
        "fr": "Rapport d'évaluation d'ingénierie - pas un certificat SIA officiel.",
        "it": (
            "Rapporto di valutazione ingegneristica - non un certificato SIA "
            "ufficiale."
        ),
    },
    "footer_page": {
        "en": "Page {page} / {total}",
        "de": "Seite {page} / {total}",
        "fr": "Page {page} / {total}",
        "it": "Pagina {page} / {total}",
    },
    "dlg_open_failed_title": {
        "en": "Cannot open",
        "de": "Öffnen nicht möglich",
        "fr": "Ouverture impossible",
        "it": "Apertura non riuscita",
    },
    "btn_probe_test1_runtime_inputs": {
        "en": "Probe Test 1 runtime inputs",
        "de": "Test-1-Laufzeiteingaben pruefen",
        "fr": "Sonder les entrees runtime Test 1",
        "it": "Sonda input runtime Test 1",
    },
    "dlg_test1_input_probe_title": {
        "en": "Test 1 runtime inputs",
        "de": "Test-1-Laufzeiteingaben",
        "fr": "Entrees runtime du Test 1",
        "it": "Input runtime Test 1",
    },
    "dlg_test1_input_probe_unavailable": {
        "en": "Select one official Test 1 case in a saved disposable project.",
        "de": "Waehlen Sie einen offiziellen Test-1-Fall in einem gespeicherten Wegwerfprojekt.",
        "fr": "Selectionnez un cas officiel Test 1 dans un projet jetable enregistre.",
        "it": "Seleziona un caso ufficiale Test 1 in un progetto usa e getta salvato.",
    },
    "status_probing_test1_inputs_detail": {
        "en": "Reading Test 1 furniture and heating/cooling capacity bindings...",
        "de": "Test-1-Moebel- und Heiz-/Kuehlleistungsbindungen werden gelesen...",
        "fr": "Lecture des liaisons mobilier et puissances chaud/froid du Test 1...",
        "it": "Lettura dei binding arredi e potenze caldo/freddo del Test 1...",
    },
    "status_test1_input_probe": {
        "en": "Test 1 read-only input probe: {status} - {report}",
        "de": "Test-1-Eingabepruefung (nur Lesen): {status} - {report}",
        "fr": "Sonde des entrees Test 1 en lecture seule : {status} - {report}",
        "it": "Sonda input Test 1 in sola lettura: {status} - {report}",
    },
    "dlg_test1_input_probe_complete": {
        "en": "Read-only probe status: {status}\n\nReport: {report}\n\nNo VE object was changed.",
        "de": "Status der schreibgeschuetzten Pruefung: {status}\n\nBericht: {report}\n\nKein VE-Objekt wurde geaendert.",
        "fr": "Statut de la sonde en lecture seule : {status}\n\nRapport : {report}\n\nAucun objet VE n'a ete modifie.",
        "it": "Stato della sonda in sola lettura: {status}\n\nRapporto: {report}\n\nNessun oggetto VE e stato modificato.",
    },
    "btn_qualify_test1_runtime_inputs": {
        "en": "Apply Test 1 capacity mapping",
        "de": "Test-1-Kapazitaetsabbildung anwenden",
        "fr": "Appliquer la capacite du Test 1",
        "it": "Applica capacita Test 1",
    },
    "dlg_test1_input_qualify_title": {
        "en": "Test 1 capacity mapping",
        "de": "Test-1-Kapazitaetsabbildung",
        "fr": "Capacite interne du Test 1",
        "it": "Capacita interna Test 1",
    },
    "dlg_test1_input_qualify_body": {
        "en": "Case {case} in {project}: apply furniture_mass_factor and fully convective heating/cooling, verify read-back, and keep unlimited capacities unchanged? The project will not be saved automatically.",
        "de": "Fall {case} in {project}: furniture_mass_factor und voll konvektive Heizung/Kuehlung anwenden, Readback pruefen und unbegrenzte Leistungen unveraendert lassen? Das Projekt wird nicht automatisch gespeichert.",
        "fr": "Cas {case} dans {project} : appliquer furniture_mass_factor et le chauffage/refroidissement entierement convectifs, verifier la relecture et laisser les puissances illimitees inchangees ? Le projet ne sera pas enregistre automatiquement.",
        "it": "Caso {case} in {project}: applicare furniture_mass_factor e riscaldamento/raffrescamento interamente convettivi, verificare la rilettura e lasciare invariate le potenze illimitate? Il progetto non sara salvato automaticamente.",
    },
    "status_qualifying_test1_inputs_detail": {
        "en": "Applying and reading back the guarded Test 1 capacity mapping...",
        "de": "Kontrollierte Test-1-Kapazitaetsabbildung wird angewendet und zurueckgelesen...",
        "fr": "Application et relecture controlees de la capacite du Test 1...",
        "it": "Applicazione e rilettura controllate della capacita Test 1...",
    },
    "status_test1_input_qualification": {
        "en": "Test 1 capacity mapping: {status} - {report}",
        "de": "Test-1-Kapazitaetsabbildung: {status} - {report}",
        "fr": "Capacite du Test 1 : {status} - {report}",
        "it": "Capacita Test 1: {status} - {report}",
    },
    "dlg_test1_input_qualify_complete": {
        "en": "Status: {status}\n\nReport: {report}\n\nReview the provisional engine constant, then save the VE project.",
        "de": "Status: {status}\n\nBericht: {report}\n\nPruefen Sie die vorlaeufige Motorkonstante und speichern Sie dann das VE-Projekt.",
        "fr": "Statut : {status}\n\nRapport : {report}\n\nVerifiez la constante moteur provisoire, puis enregistrez le projet VE.",
        "it": "Stato: {status}\n\nRapporto: {report}\n\nVerifica la costante motore provvisoria, poi salva il progetto VE.",
    },
    "template_remediation_technical_section": {
        "en": "3. Confirm controlled technical application",
        "de": "3. Kontrollierte technische Anwendung bestaetigen",
        "fr": "3. Confirmer l'application technique controlee",
        "it": "3. Confermare l'applicazione tecnica controllata",
    },
    "template_remediation_automatic_evidence_help": {
        "en": (
            "No form is required. The plan records the active project, exact VE "
            "template fingerprint, selected room IDs, generation date and any "
            "matching source-traced provisioning receipt automatically. Missing "
            "source evidence remains NOT_CHECKABLE. Applying never grants a "
            "compliance verdict."
        ),
        "de": (
            "Kein Formular ist erforderlich. Der Plan erfasst automatisch das aktive "
            "Projekt, den exakten VE-Template-Fingerabdruck, die ausgewaehlten "
            "Raum-IDs, das Erstellungsdatum und einen passenden quellenverfolgten "
            "Bereitstellungsbeleg. Fehlende Quellenbelege bleiben NOT_CHECKABLE. "
            "Die Anwendung erteilt nie ein Konformitaetsurteil."
        ),
        "fr": (
            "Aucun formulaire n'est requis. Le plan enregistre automatiquement le "
            "projet actif, l'empreinte exacte du template VE, les identifiants des "
            "locaux, la date de generation et tout recu de provisioning source. Une "
            "preuve source manquante reste NOT_CHECKABLE. L'application n'accorde "
            "jamais un verdict de conformite."
        ),
        "it": (
            "Non e richiesto alcun modulo. Il piano registra automaticamente il "
            "progetto attivo, l'impronta esatta del template VE, gli ID dei locali, "
            "la data di generazione e ogni ricevuta di provisioning tracciata alla "
            "fonte. Le prove mancanti restano NOT_CHECKABLE. L'applicazione non "
            "concede mai un verdetto di conformita."
        ),
    },
    "template_remediation_copy_confirmation": {
        "en": "I confirm this is a saved disposable project copy.",
        "de": "Ich bestaetige, dass dies eine gespeicherte Wegwerf-Projektkopie ist.",
        "fr": "Je confirme qu'il s'agit d'une copie de projet jetable enregistree.",
        "it": "Confermo che questa e una copia di progetto usa e getta salvata.",
    },
    "template_remediation_apply_confirmation": {
        "en": (
            "I authorize the technical application of the exact checksum-bound "
            "preview to the selected rooms. I understand that this grants no SIA "
            "compliance verdict."
        ),
        "de": (
            "Ich genehmige die technische Anwendung der exakt checksumgebundenen "
            "Vorschau auf die ausgewaehlten Raeume. Mir ist bewusst, dass dies kein "
            "SIA-Konformitaetsurteil erteilt."
        ),
        "fr": (
            "J'autorise l'application technique de la previsualisation exacte liee "
            "au checksum aux locaux selectionnes. Je comprends que cela n'accorde "
            "aucun verdict de conformite SIA."
        ),
        "it": (
            "Autorizzo l'applicazione tecnica dell'anteprima esatta vincolata al "
            "checksum ai locali selezionati. Comprendo che cio non concede alcun "
            "verdetto di conformita SIA."
        ),
    },
    "template_remediation_confirmation_changed": {
        "en": "Selection or confirmation changed. Create a new preview before applying.",
        "de": "Auswahl oder Bestaetigung wurde geaendert. Vor der Anwendung eine neue Vorschau erstellen.",
        "fr": "La selection ou la confirmation a change. Creez une nouvelle previsualisation avant d'appliquer.",
        "it": "La selezione o la conferma e cambiata. Creare una nuova anteprima prima di applicare.",
    },
    "template_remediation_apply_locked": {
        "en": "Apply is locked until technical application is confirmed.",
        "de": "Die Anwendung bleibt gesperrt, bis die technische Anwendung bestaetigt ist.",
        "fr": "L'application est verrouillee jusqu'a confirmation de l'application technique.",
        "it": "L'applicazione e bloccata finche l'applicazione tecnica non viene confermata.",
    },
    "template_remediation_preview_ready": {
        "en": "Technical preview ready; review the immutable plan before applying.",
        "de": "Technische Vorschau bereit; den unveraenderlichen Plan vor der Anwendung pruefen.",
        "fr": "Previsualisation technique prete ; examinez le plan immuable avant application.",
        "it": "Anteprima tecnica pronta; verificare il piano immutabile prima dell'applicazione.",
    },
    "template_remediation_gain_structure_status": {
        "en": "Room gain-structure capability",
        "de": "Faehigkeit der Raumlaststruktur",
        "fr": "Capacite de structure des gains du local",
        "it": "Capacita della struttura dei carichi del locale",
    },
    "template_remediation_missing_gain_families": {
        "en": "missing gain families",
        "de": "fehlende Lastfamilien",
        "fr": "familles de gains manquantes",
        "it": "famiglie di carico mancanti",
    },
    "template_remediation_gain_structure_blocked": {
        "en": (
            "Application is blocked before mutation: the documented VERoomData "
            "API cannot create missing room-level gain families. Add them through "
            "VE Query Room, then create a new preview."
        ),
        "de": (
            "Die Anwendung wird vor der Mutation blockiert: Die dokumentierte "
            "VERoomData-API kann fehlende Raumlastfamilien nicht erstellen. Fuegen "
            "Sie sie ueber VE Query Room hinzu und erstellen Sie eine neue Vorschau."
        ),
        "fr": (
            "L'application est bloquee avant mutation : l'API VERoomData documentee "
            "ne peut pas creer les familles de gains manquantes dans le local. "
            "Ajoutez-les via VE Query Room, puis creez une nouvelle previsualisation."
        ),
        "it": (
            "L'applicazione e bloccata prima della modifica: l'API VERoomData "
            "documentata non puo creare le famiglie di carico mancanti nel locale. "
            "Aggiungerle tramite VE Query Room, poi creare una nuova anteprima."
        ),
    },
    "template_remediation_gain_structure_bridge": {
        "en": (
            "Applying will temporarily add the missing gain families to the source "
            "template, verify the selected rooms, assign the target template, then "
            "restore and verify the source template. Close VE without saving if any "
            "read-back fails."
        ),
        "de": (
            "Bei der Anwendung werden die fehlenden Lastfamilien voruebergehend zum "
            "Quell-Template hinzugefuegt, die ausgewaehlten Raeume geprueft, das "
            "Ziel-Template zugewiesen und danach das Quell-Template wiederhergestellt "
            "und geprueft. Bei einem Lesefehler VE ohne Speichern schliessen."
        ),
        "fr": (
            "L'application ajoutera temporairement les familles de gains manquantes "
            "au template source, verifiera les locaux selectionnes, affectera le "
            "template cible, puis restaurera et verifiera le template source. En cas "
            "d'echec de lecture, fermez VE sans sauvegarder."
        ),
        "it": (
            "L'applicazione aggiungera temporaneamente le famiglie di carico mancanti "
            "al template sorgente, verifichera i locali selezionati, assegnera il "
            "template di destinazione, quindi ripristinera e verifichera il template "
            "sorgente. Se una lettura fallisce, chiudere VE senza salvare."
        ),
    },
}


def normalize_language(language: str) -> str:
    """Return a supported language code, falling back to the default.

    Accepts a plain code or a locale such as ``de-CH`` / ``fr_CH``, so a value
    read from the environment or the browser can be passed straight in.
    """

    text = str(language or "").strip().lower().replace("_", "-")
    if not text:
        return DEFAULT_LANGUAGE
    if text in LANGUAGES:
        return text
    prefix = text.split("-", 1)[0]
    return prefix if prefix in LANGUAGES else DEFAULT_LANGUAGE


def translate(key: str, language: str = DEFAULT_LANGUAGE) -> str:
    """Return one translated string, falling back to English then to the key.

    A missing key returns the key itself rather than raising, so a partially
    translated interface degrades to a visible marker instead of crashing the
    VEScripts window.
    """

    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    return entry.get(normalize_language(language)) or entry.get(DEFAULT_LANGUAGE, key)


def catalog_for(language: str) -> Dict[str, str]:
    """Return every translated string for one language, keyed by message id."""

    code = normalize_language(language)
    return {key: translate(key, code) for key in TRANSLATIONS}


def full_catalog() -> Dict[str, Mapping[str, str]]:
    """Return the ``{language: {key: text}}`` catalogue for every language.

    Used to embed all languages in the standalone HTML builder so it can switch
    language offline, without a server round trip.
    """

    return {code: catalog_for(code) for code in LANGUAGES}


def missing_translations() -> Dict[str, list]:
    """Return ``{language: [missing keys]}`` for catalogue completeness checks."""

    gaps: Dict[str, list] = {}
    for code in LANGUAGES:
        absent = [
            key
            for key, entry in TRANSLATIONS.items()
            if not str(entry.get(code) or "").strip()
        ]
        if absent:
            gaps[code] = absent
    return gaps
