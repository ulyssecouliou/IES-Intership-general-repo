# Manager Multilingual Brief

Last updated: 2026-06-30  
Project: Swiss SIA Compliance Checker for IESVE  
Standards scope: SIA 380/2:2022 and SIA 4010:2023  
Languages: English, French, German, Italian

> This document is a manager-facing summary. It is not an official SIA certificate.
> The generated Excel workbook is a readiness and audit report until all required
> SIA 4010 official evidence, reference comparisons, and reviewer sign-off are complete.

---

## English

### Executive Summary

The Swiss SIA Compliance Checker is an IESVE Run-button workflow that reviews an
active VE model against source-traced SIA 380/2:2022 checks and SIA 4010:2023
validation-readiness requirements.

The current workflow:

- opens the active IESVE project directly through the IESVE Python API;
- extracts rooms, surfaces, openings, construction values, and available model data;
- reads APS/Vista dynamic results when `iesve.ResultsReader` can access the APS file;
- generates one timestamped Excel workbook per run;
- creates a professional manager dashboard, remediation board, data coverage matrix,
  input request checklist, and SIA 4010 readiness matrix;
- keeps SIA 4010 as `NOT_CHECKABLE` until official evidence is supplied.

### Latest Verified Status

The latest verified workbook is:

`reports/Swiss_Compliance_Report__ZOER_32_C1__-__20260630_113724.xlsx`

Current verified indicators:

- Excel generation works from VE.
- Charts are present and configured to display correctly.
- APS/Vista results are readable for `ZOER_C1.aps`.
- Dynamic result coverage is available for 4 rooms and 392.5 m2.
- No formula errors were detected in the checked workbook.

### What Can Be Claimed

Safe wording:

- "The tool provides a professional readiness report."
- "The report identifies automated SIA 380/2 checks, partial checks, and missing evidence."
- "The APS/Vista file was read successfully for dynamic indicators."
- "SIA 4010 validation remains evidence-dependent and is not claimed as passed."

Unsafe wording:

- "The model is fully SIA certified."
- "IESVE is validated under SIA 4010 by this report alone."
- "All SIA 380/2 and SIA 4010 requirements are complete."

### Main Current Blockers

The current model is not ready for a final compliance claim because:

- glazing solar factor values are currently reported around `g = 0.75`, above the
  current SIA 380/2 reference limit used by the checker (`0.50`);
- two external wall elements are above the current U-value limit (`0.222 W/m2K`
  versus `0.20 W/m2K`);
- ventilation/AHU control, heat recovery, pressure drop, lighting control, and
  generator efficiency evidence are still missing or partial;
- the SIA 4010 official evidence pack is not yet supplied;
- the intended SIA 4010 validation class is not yet confirmed.

### What The Manager Should Ask For Next

Priority evidence to collect:

1. Target SIA 4010 validation class (`1A`, `1B`, `2A`, `2B`, `3`, `4A`, `4B`, or `5`).
2. Official SIA 4010 test specifications and evaluation workbooks.
3. Candidate IESVE outputs transferred into the official evaluation files.
4. Reference comparison plots/tables from the official SIA workbooks.
5. Glazing and shading evidence: g-value definition, active `g_total`, controls.
6. Ventilation/AHU schedules: airflow, fan control, heat recovery, leakage classes.
7. Heating/cooling plant data: type, power band, COP/SCOP/EER/SEER.
8. Lighting data: power density, daylight control, presence control.
9. Room-use mapping: VE room name to real use and SIA 2024 category.

---

## Français

### Résumé Exécutif

Le Swiss SIA Compliance Checker est un workflow lancé depuis le bouton Run de
IESVE. Il analyse le modèle VE actif avec des contrôles tracés vers la
SIA 380/2:2022 et une matrice de readiness pour la validation SIA 4010:2023.

Le workflow actuel :

- ouvre le projet IESVE actif via l'API Python IESVE;
- extrait les pièces, surfaces, ouvertures, constructions et données disponibles;
- lit les résultats dynamiques APS/Vista quand `iesve.ResultsReader` peut accéder
  au fichier APS;
- génère un seul rapport Excel horodaté par lancement;
- produit un dashboard manager, un plan de remédiation, une matrice de couverture
  des données, une checklist des inputs manquants, et une matrice SIA 4010;
- garde la SIA 4010 en statut `NOT_CHECKABLE` tant que les preuves officielles ne
  sont pas fournies.

### Dernier Statut Vérifié

Le dernier rapport vérifié est :

`reports/Swiss_Compliance_Report__ZOER_32_C1__-__20260630_113724.xlsx`

Indicateurs vérifiés :

- la génération Excel fonctionne depuis VE;
- les graphiques sont présents et configurés correctement;
- le fichier APS/Vista `ZOER_C1.aps` est lu avec succès;
- les résultats dynamiques couvrent 4 pièces et 392.5 m2;
- aucune erreur de formule n'a été détectée dans le classeur vérifié.

### Ce Que L'on Peut Dire

Formulations sûres :

- "L'outil produit un rapport professionnel de readiness."
- "Le rapport sépare les contrôles SIA 380/2 automatisés, partiels et les preuves manquantes."
- "Le fichier APS/Vista a été lu pour les indicateurs dynamiques."
- "La validation SIA 4010 reste dépendante des preuves officielles et n'est pas déclarée comme réussie."

Formulations à éviter :

- "Le modèle est entièrement certifié SIA."
- "IESVE est validé SIA 4010 uniquement par ce rapport."
- "Toutes les exigences SIA 380/2 et SIA 4010 sont couvertes et passées."

### Blocages Actuels

Le modèle n'est pas encore prêt pour une affirmation finale de conformité car :

- les facteurs solaires des vitrages sont actuellement autour de `g = 0.75`, au-dessus
  de la limite de référence utilisée par le checker (`0.50`);
- deux éléments de murs extérieurs dépassent la limite U actuelle (`0.222 W/m2K`
  contre `0.20 W/m2K`);
- les données ventilation/AHU, récupération de chaleur, pertes de charge, contrôle
  éclairage et efficacité des générateurs restent manquantes ou partielles;
- le pack de preuves officielles SIA 4010 n'est pas encore fourni;
- la classe de validation SIA 4010 visée n'est pas encore confirmée.

### Ce Que Le Manager Doit Demander Maintenant

Preuves prioritaires à collecter :

1. Classe SIA 4010 visée (`1A`, `1B`, `2A`, `2B`, `3`, `4A`, `4B` ou `5`).
2. Spécifications officielles des tests SIA 4010 et fichiers Excel d'évaluation.
3. Résultats candidats IESVE transférés dans les fichiers officiels.
4. Comparaisons aux résultats de référence issues des workbooks officiels.
5. Preuves vitrages/stores : définition du g, `g_total` actif, stratégie de contrôle.
6. Données ventilation/AHU : débits, contrôle ventilateur, récupération, étanchéité.
7. Données chauffage/refroidissement : type, puissance, COP/SCOP/EER/SEER.
8. Données éclairage : puissance, contrôle lumière du jour, présence.
9. Mapping des usages : nom pièce VE, usage réel, catégorie SIA 2024.

---

## Deutsch

### Management-Zusammenfassung

Der Swiss SIA Compliance Checker ist ein IESVE Run-Button Workflow. Er prüft das
aktive VE-Modell anhand nachvollziehbarer SIA 380/2:2022 Kriterien und einer
SIA 4010:2023 Validierungs-Readiness-Matrix.

Der aktuelle Workflow:

- öffnet das aktive IESVE-Projekt über die IESVE Python API;
- extrahiert Räume, Flächen, Öffnungen, Konstruktionen und verfügbare Modelldaten;
- liest APS/Vista Simulationsergebnisse, wenn `iesve.ResultsReader` auf die APS-Datei
  zugreifen kann;
- erzeugt pro Lauf genau eine zeitgestempelte Excel-Datei;
- erstellt ein Manager-Dashboard, eine Remediation-Liste, eine Datenabdeckungs-Matrix,
  eine Input-Request-Checkliste und eine SIA 4010 Readiness-Matrix;
- lässt SIA 4010 auf `NOT_CHECKABLE`, solange die offiziellen Nachweise fehlen.

### Zuletzt Verifizierter Stand

Der zuletzt geprüfte Bericht ist:

`reports/Swiss_Compliance_Report__ZOER_32_C1__-__20260630_113724.xlsx`

Verifizierte Punkte:

- Excel-Erzeugung funktioniert aus VE heraus;
- Diagramme sind vorhanden und korrekt konfiguriert;
- `ZOER_C1.aps` wird erfolgreich gelesen;
- dynamische Ergebnisse sind für 4 Räume und 392.5 m2 verfügbar;
- im geprüften Workbook wurden keine Formelfehler gefunden.

### Sichere Aussage

Sichere Formulierungen:

- "Das Tool erstellt einen professionellen Readiness-Bericht."
- "Der Bericht trennt automatisierte SIA 380/2 Prüfungen, Teilprüfungen und fehlende Nachweise."
- "Die APS/Vista-Datei wurde für dynamische Kennwerte erfolgreich gelesen."
- "SIA 4010 bleibt nachweisabhängig und wird nicht als bestanden deklariert."

Zu vermeiden:

- "Das Modell ist vollständig SIA-zertifiziert."
- "IESVE ist allein durch diesen Bericht nach SIA 4010 validiert."
- "Alle SIA 380/2 und SIA 4010 Anforderungen sind vollständig erfüllt."

### Aktuelle Hauptblocker

Das Modell ist noch nicht bereit für eine finale Konformitätsaussage, weil:

- die gemeldeten solaren Glaswerte bei etwa `g = 0.75` liegen und damit über dem
  aktuell verwendeten Referenzgrenzwert (`0.50`);
- zwei Außenwand-Elemente über dem aktuellen U-Wert-Grenzwert liegen (`0.222 W/m2K`
  gegenüber `0.20 W/m2K`);
- Lüftung/AHU, Wärmerückgewinnung, Druckverluste, Lichtregelung und Anlagenwirkungsgrade
  noch fehlen oder nur teilweise belegt sind;
- das offizielle SIA 4010 Nachweispaket noch fehlt;
- die Ziel-Validierungsklasse nach SIA 4010 noch nicht bestätigt ist.

### Was Das Management Jetzt Anfordern Sollte

Prioritäre Nachweise:

1. Zielklasse nach SIA 4010 (`1A`, `1B`, `2A`, `2B`, `3`, `4A`, `4B` oder `5`).
2. Offizielle SIA 4010 Testspezifikationen und Excel-Auswertungsdateien.
3. IESVE-Kandidatenergebnisse in den offiziellen Auswertungsdateien.
4. Referenzvergleichstabellen oder Diagramme aus den offiziellen Workbooks.
5. Nachweise für Glas und Sonnenschutz: g-Wert, aktives `g_total`, Regelstrategie.
6. Lüftung/AHU: Volumenströme, Ventilatorregelung, Wärmerückgewinnung, Dichtheitsklassen.
7. Heiz-/Kälteanlagen: Typ, Leistungsbereich, COP/SCOP/EER/SEER.
8. Beleuchtung: Leistung, Tageslichtregelung, Präsenzregelung.
9. Nutzungszuordnung: VE-Raumname, reale Nutzung, SIA 2024 Kategorie.

---

## Italiano

### Sintesi Per Il Management

Lo Swiss SIA Compliance Checker è un workflow eseguibile dal pulsante Run di
IESVE. Analizza il modello VE attivo con controlli tracciati alla SIA 380/2:2022
e con una matrice di readiness per la validazione SIA 4010:2023.

Il workflow attuale:

- apre il progetto IESVE attivo tramite l'API Python di IESVE;
- estrae locali, superfici, aperture, costruzioni e dati disponibili del modello;
- legge i risultati dinamici APS/Vista quando `iesve.ResultsReader` può accedere
  al file APS;
- genera un solo report Excel con timestamp per ogni esecuzione;
- produce dashboard manageriale, piano di remediation, matrice di copertura dati,
  checklist degli input mancanti e matrice SIA 4010;
- mantiene SIA 4010 in stato `NOT_CHECKABLE` finché non sono disponibili le prove ufficiali.

### Ultimo Stato Verificato

L'ultimo workbook verificato è:

`reports/Swiss_Compliance_Report__ZOER_32_C1__-__20260630_113724.xlsx`

Indicatori verificati:

- la generazione Excel funziona da VE;
- i grafici sono presenti e configurati correttamente;
- il file `ZOER_C1.aps` viene letto correttamente;
- i risultati dinamici coprono 4 locali e 392.5 m2;
- non sono stati rilevati errori di formula nel workbook controllato.

### Cosa Si Può Dichiarare

Formulazioni sicure:

- "Lo strumento produce un report professionale di readiness."
- "Il report separa controlli SIA 380/2 automatizzati, controlli parziali e prove mancanti."
- "Il file APS/Vista è stato letto per gli indicatori dinamici."
- "La validazione SIA 4010 resta dipendente dalle prove ufficiali e non viene dichiarata superata."

Formulazioni da evitare:

- "Il modello è completamente certificato SIA."
- "IESVE è validato SIA 4010 solo tramite questo report."
- "Tutti i requisiti SIA 380/2 e SIA 4010 sono completamente coperti."

### Blocchi Principali Attuali

Il modello non è ancora pronto per una dichiarazione finale di conformità perché:

- i fattori solari del vetro sono attualmente intorno a `g = 0.75`, sopra il limite
  di riferimento usato dal checker (`0.50`);
- due elementi di parete esterna superano il limite U attuale (`0.222 W/m2K`
  rispetto a `0.20 W/m2K`);
- ventilazione/AHU, recupero di calore, perdite di pressione, controllo illuminazione
  ed efficienze degli impianti sono ancora mancanti o parziali;
- il pacchetto ufficiale di prove SIA 4010 non è ancora disponibile;
- la classe di validazione SIA 4010 target non è ancora confermata.

### Cosa Richiedere Ora

Prove prioritarie da raccogliere:

1. Classe SIA 4010 target (`1A`, `1B`, `2A`, `2B`, `3`, `4A`, `4B` o `5`).
2. Specifiche ufficiali dei test SIA 4010 e workbook Excel ufficiali.
3. Output candidati IESVE trasferiti nei file ufficiali.
4. Tabelle/grafici di confronto con i risultati di riferimento.
5. Prove su vetri e schermature: definizione del g, `g_total` attivo, strategia di controllo.
6. Ventilazione/AHU: portate, controllo ventilatori, recupero calore, classi di tenuta.
7. Impianti caldo/freddo: tipo, potenza, COP/SCOP/EER/SEER.
8. Illuminazione: potenza, controllo daylight, controllo presenza.
9. Mappatura degli usi: nome locale VE, uso reale, categoria SIA 2024.

---

## Controlled Glossary

| Concept | English | Français | Deutsch | Italiano |
|---|---|---|---|---|
| Readiness report | readiness report | rapport de readiness | Readiness-Bericht | report di readiness |
| Official evidence | official evidence | preuve officielle | offizieller Nachweis | prova ufficiale |
| Validation class | validation class | classe de validation | Validierungsklasse | classe di validazione |
| Not checkable | not checkable | non vérifiable | nicht prüfbar | non verificabile |
| Automated indicator | automated indicator | indicateur automatisé | automatischer Indikator | indicatore automatizzato |
| Reference comparison | reference comparison | comparaison de référence | Referenzvergleich | confronto di riferimento |

## Recommended Manager Discussion Agenda

1. Confirm the target SIA 4010 class.
2. Review the latest Excel dashboard and `INPUT REQUEST` P1 items.
3. Decide who owns glazing/shading, AHU/ventilation, HVAC plant, lighting, and SIA 4010 official evidence.
4. Collect the missing evidence into `sia4010_evidence/`.
5. Re-run `Run_VE_Swiss_Compliance.py` from VE.
6. Review whether blockers move from `MISSING` to `PARTIAL` or `AVAILABLE`.
