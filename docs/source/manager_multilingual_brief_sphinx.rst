Manager Multilingual Brief
==========================

Last updated: 2026-06-30

Project: Swiss SIA Compliance Checker for IESVE

Standards scope: SIA 380/2:2022 and SIA 4010:2023

Languages: English, French, German, Italian

.. warning::

   This document is a manager-facing summary. It is not an official SIA
   certificate. The generated Excel workbook is a readiness and audit report
   until all required SIA 4010 official evidence, reference comparisons, and
   reviewer sign-off are complete.

English
-------

Executive Summary
~~~~~~~~~~~~~~~~~

The Swiss SIA Compliance Checker is an IESVE Run-button workflow that reviews
an active VE model against source-traced SIA 380/2:2022 checks and
SIA 4010:2023 validation-readiness requirements.

The current workflow:

* opens the active IESVE project directly through the IESVE Python API;
* extracts rooms, surfaces, openings, construction values, and available model
  data;
* reads APS/Vista dynamic results when ``iesve.ResultsReader`` can access the
  APS file;
* generates one timestamped Excel workbook per run;
* creates a professional manager dashboard, remediation board, data coverage
  matrix, input request checklist, and SIA 4010 readiness matrix;
* keeps SIA 4010 as ``NOT_CHECKABLE`` until official evidence is supplied.

Latest Verified Status
~~~~~~~~~~~~~~~~~~~~~~

The latest verified workbook is:

``reports/Swiss_Compliance_Report__ZOER_32_C1__-__20260630_113724.xlsx``

Current verified indicators:

* Excel generation works from VE.
* Charts are present and configured to display correctly.
* APS/Vista results are readable for ``ZOER_C1.aps``.
* Dynamic result coverage is available for 4 rooms and 392.5 m2.
* No formula errors were detected in the checked workbook.

Safe wording:

* "The tool provides a professional readiness report."
* "The report identifies automated SIA 380/2 checks, partial checks, and
  missing evidence."
* "The APS/Vista file was read successfully for dynamic indicators."
* "SIA 4010 validation remains evidence-dependent and is not claimed as
  passed."

Unsafe wording:

* "The model is fully SIA certified."
* "IESVE is validated under SIA 4010 by this report alone."
* "All SIA 380/2 and SIA 4010 requirements are complete."

Main Current Blockers
~~~~~~~~~~~~~~~~~~~~~

The current model is not ready for a final compliance claim because:

* glazing solar factor values are currently reported around ``g = 0.75``,
  above the current SIA 380/2 reference limit used by the checker
  (``0.50``);
* two external wall elements are above the current U-value limit
  (``0.222 W/m2K`` versus ``0.20 W/m2K``);
* ventilation/AHU control, heat recovery, pressure drop, lighting control, and
  generator efficiency evidence are still missing or partial;
* the SIA 4010 official evidence pack is not yet supplied;
* the intended SIA 4010 validation class is not yet confirmed.

What The Manager Should Ask For Next
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Priority evidence to collect:

1. Target SIA 4010 validation class: ``1A``, ``1B``, ``2A``, ``2B``, ``3``,
   ``4A``, ``4B``, or ``5``.
2. Official SIA 4010 test specifications and evaluation workbooks.
3. Candidate IESVE outputs transferred into the official evaluation files.
4. Reference comparison results for each selected validation class.
5. Glazing and shading evidence, including g-values and control assumptions.
6. Ventilation/AHU evidence, including heat recovery, pressure drops, control
   strategy, and measured or modelled airflow assumptions.
7. Heating/cooling plant efficiency evidence.
8. Lighting power density and control strategy evidence.
9. Room-use mapping to the selected SIA profiles.

Français
--------

Résumé Exécutif
~~~~~~~~~~~~~~~

Le Swiss SIA Compliance Checker est un workflow lancé directement depuis le
bouton Run de IESVE. Il analyse le modèle VE actif avec des contrôles
traçables vers la SIA 380/2:2022 et une matrice de préparation à la
validation SIA 4010:2023.

Le workflow actuel:

* ouvre le projet IESVE actif via l'API Python IESVE;
* extrait les locaux, surfaces, ouvertures, valeurs de construction et données
  disponibles du modèle;
* lit les résultats dynamiques APS/Vista lorsque ``iesve.ResultsReader`` peut
  accéder au fichier APS;
* génère un seul classeur Excel horodaté par exécution;
* produit un tableau de bord manager, un plan de remédiation, une matrice de
  couverture des données, une checklist de demandes client et une matrice de
  préparation SIA 4010;
* maintient la SIA 4010 en statut ``NOT_CHECKABLE`` tant que les preuves
  officielles ne sont pas fournies.

Dernier Statut Vérifié
~~~~~~~~~~~~~~~~~~~~~~

Le dernier classeur vérifié est:

``reports/Swiss_Compliance_Report__ZOER_32_C1__-__20260630_113724.xlsx``

Indicateurs vérifiés:

* la génération Excel fonctionne depuis VE;
* les graphiques sont présents et configurés pour s'afficher correctement;
* les résultats APS/Vista sont lisibles pour ``ZOER_C1.aps``;
* la couverture dynamique concerne 4 locaux et 392.5 m2;
* aucune erreur de formule n'a été détectée dans le classeur contrôlé.

Formulations sûres:

* "L'outil fournit un rapport professionnel de préparation à la conformité."
* "Le rapport identifie les contrôles SIA 380/2 automatisés, partiels et les
  preuves manquantes."
* "Le fichier APS/Vista a été lu avec succès pour les indicateurs dynamiques."
* "La validation SIA 4010 reste dépendante des preuves et n'est pas déclarée
  comme réussie."

Formulations à éviter:

* "Le modèle est entièrement certifié SIA."
* "IESVE est validé selon la SIA 4010 uniquement par ce rapport."
* "Toutes les exigences SIA 380/2 et SIA 4010 sont couvertes et complètes."

Blocages Actuels
~~~~~~~~~~~~~~~~

Le modèle actuel n'est pas encore prêt pour une déclaration finale de
conformité car:

* les facteurs solaires de vitrage sont actuellement autour de ``g = 0.75``,
  au-dessus de la limite de référence SIA 380/2 utilisée par le checker
  (``0.50``);
* deux éléments de mur extérieur dépassent la limite U actuelle
  (``0.222 W/m2K`` contre ``0.20 W/m2K``);
* les preuves sur la ventilation/AHU, la récupération de chaleur, les pertes
  de charge, le contrôle de l'éclairage et le rendement des générateurs sont
  manquantes ou partielles;
* le pack officiel de preuves SIA 4010 n'est pas encore fourni;
* la classe de validation SIA 4010 visée n'est pas encore confirmée.

Ce Que Le Manager Doit Demander Maintenant
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Preuves prioritaires à collecter:

1. Classe SIA 4010 cible: ``1A``, ``1B``, ``2A``, ``2B``, ``3``, ``4A``,
   ``4B`` ou ``5``.
2. Spécifications officielles SIA 4010 et fichiers d'évaluation.
3. Résultats IESVE transférés dans les fichiers officiels d'évaluation.
4. Comparaisons de référence pour chaque classe de validation retenue.
5. Preuves vitrage et protections solaires, incluant g-values et hypothèses
   de contrôle.
6. Preuves ventilation/AHU, incluant récupération de chaleur, pertes de charge,
   stratégie de contrôle et débits.
7. Preuves de rendement chauffage/refroidissement.
8. Puissance d'éclairage et stratégie de contrôle.
9. Correspondance des locaux avec les profils SIA sélectionnés.

Deutsch
-------

Management-Zusammenfassung
~~~~~~~~~~~~~~~~~~~~~~~~~~

Der Swiss SIA Compliance Checker ist ein IESVE-Workflow, der direkt über den
Run-Button gestartet wird. Er prüft das aktive VE-Modell anhand
quellenbasierter SIA 380/2:2022-Prüfungen und einer
SIA 4010:2023-Validierungsbereitschaftsmatrix.

Der aktuelle Workflow:

* öffnet das aktive IESVE-Projekt über die IESVE Python API;
* extrahiert Räume, Flächen, Öffnungen, Konstruktionswerte und verfügbare
  Modelldaten;
* liest APS/Vista-Dynamikergebnisse, wenn ``iesve.ResultsReader`` auf die
  APS-Datei zugreifen kann;
* erstellt pro Lauf eine einzige zeitgestempelte Excel-Arbeitsmappe;
* erstellt Management-Dashboard, Maßnahmenplan, Datenabdeckungsmatrix,
  Input-Checkliste und SIA 4010-Bereitschaftsmatrix;
* belässt SIA 4010 auf ``NOT_CHECKABLE``, solange die offiziellen Nachweise
  fehlen.

Zuletzt Verifizierter Stand
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Die zuletzt geprüfte Arbeitsmappe ist:

``reports/Swiss_Compliance_Report__ZOER_32_C1__-__20260630_113724.xlsx``

Verifizierte Punkte:

* die Excel-Erzeugung funktioniert aus VE;
* Diagramme sind vorhanden und korrekt für die Anzeige konfiguriert;
* APS/Vista-Ergebnisse sind für ``ZOER_C1.aps`` lesbar;
* dynamische Ergebnisabdeckung liegt für 4 Räume und 392.5 m2 vor;
* in der geprüften Arbeitsmappe wurden keine Formelfehler gefunden.

Sichere Aussagen:

* "Das Tool liefert einen professionellen Readiness-Report."
* "Der Bericht trennt automatisierte SIA 380/2-Prüfungen, Teilprüfungen und
  fehlende Nachweise."
* "Die APS/Vista-Datei wurde erfolgreich für dynamische Kennwerte gelesen."
* "Die SIA 4010-Validierung bleibt nachweisabhängig und wird nicht als
  bestanden deklariert."

Zu vermeidende Aussagen:

* "Das Modell ist vollständig SIA-zertifiziert."
* "IESVE ist allein durch diesen Bericht nach SIA 4010 validiert."
* "Alle Anforderungen aus SIA 380/2 und SIA 4010 sind vollständig abgedeckt."

Aktuelle Hauptblocker
~~~~~~~~~~~~~~~~~~~~~

Das aktuelle Modell ist noch nicht bereit für eine endgültige
Konformitätsaussage, weil:

* die g-Werte der Verglasung aktuell etwa ``g = 0.75`` betragen und damit über
  dem im Checker verwendeten SIA 380/2-Referenzwert von ``0.50`` liegen;
* zwei Außenwandelemente über dem aktuellen U-Wert-Grenzwert liegen
  (``0.222 W/m2K`` gegenüber ``0.20 W/m2K``);
* Nachweise zu Lüftung/AHU, Wärmerückgewinnung, Druckverlusten,
  Beleuchtungsregelung und Erzeugerwirkungsgrad fehlen oder unvollständig
  sind;
* das offizielle SIA 4010-Nachweispaket noch nicht vorliegt;
* die Zielklasse der SIA 4010-Validierung noch nicht bestätigt ist.

Was Das Management Jetzt Anfordern Sollte
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Priorisierte Nachweise:

1. Zielklasse SIA 4010: ``1A``, ``1B``, ``2A``, ``2B``, ``3``, ``4A``,
   ``4B`` oder ``5``.
2. Offizielle SIA 4010-Testspezifikationen und Bewertungsdateien.
3. IESVE-Kandidatenergebnisse in den offiziellen Bewertungsdateien.
4. Referenzvergleiche für jede ausgewählte Validierungsklasse.
5. Nachweise zu Verglasung und Sonnenschutz, inklusive g-Werte und
   Regelannahmen.
6. Nachweise zu Lüftung/AHU, inklusive Wärmerückgewinnung, Druckverlusten,
   Regelstrategie und Luftmengen.
7. Nachweise zu Heiz- und Kühlanlageneffizienz.
8. Beleuchtungsleistung und Regelstrategie.
9. Raumzuordnung zu den ausgewählten SIA-Profilen.

Italiano
--------

Sintesi Per Il Management
~~~~~~~~~~~~~~~~~~~~~~~~~

Lo Swiss SIA Compliance Checker è un workflow IESVE avviabile direttamente dal
pulsante Run. Analizza il modello VE attivo rispetto a controlli tracciabili
SIA 380/2:2022 e a una matrice di preparazione alla validazione
SIA 4010:2023.

Il workflow attuale:

* apre il progetto IESVE attivo tramite l'API Python IESVE;
* estrae locali, superfici, aperture, valori costruttivi e dati disponibili
  del modello;
* legge i risultati dinamici APS/Vista quando ``iesve.ResultsReader`` può
  accedere al file APS;
* genera una sola cartella Excel con timestamp per ogni esecuzione;
* produce dashboard manageriale, piano di remediation, matrice di copertura
  dati, checklist input e matrice di readiness SIA 4010;
* mantiene SIA 4010 in stato ``NOT_CHECKABLE`` finché le evidenze ufficiali
  non sono fornite.

Ultimo Stato Verificato
~~~~~~~~~~~~~~~~~~~~~~~

L'ultima cartella verificata è:

``reports/Swiss_Compliance_Report__ZOER_32_C1__-__20260630_113724.xlsx``

Indicatori verificati:

* la generazione Excel funziona da VE;
* i grafici sono presenti e configurati correttamente;
* i risultati APS/Vista sono leggibili per ``ZOER_C1.aps``;
* la copertura dinamica è disponibile per 4 locali e 392.5 m2;
* non sono stati rilevati errori di formula nella cartella controllata.

Dichiarazioni sicure:

* "Lo strumento fornisce un report professionale di readiness."
* "Il report identifica controlli SIA 380/2 automatici, parziali ed evidenze
  mancanti."
* "Il file APS/Vista è stato letto con successo per gli indicatori dinamici."
* "La validazione SIA 4010 resta dipendente dalle evidenze e non viene
  dichiarata superata."

Dichiarazioni da evitare:

* "Il modello è completamente certificato SIA."
* "IESVE è validato secondo SIA 4010 solo tramite questo report."
* "Tutti i requisiti SIA 380/2 e SIA 4010 sono completi."

Blocchi Principali Attuali
~~~~~~~~~~~~~~~~~~~~~~~~~~

Il modello attuale non è ancora pronto per una dichiarazione finale di
conformità perché:

* i fattori solari dei vetri sono attualmente circa ``g = 0.75``, superiori al
  limite di riferimento SIA 380/2 usato dal checker (``0.50``);
* due elementi di parete esterna superano il limite U attuale
  (``0.222 W/m2K`` rispetto a ``0.20 W/m2K``);
* evidenze su ventilazione/AHU, recupero calore, perdite di carico, controllo
  illuminazione ed efficienza generatori sono mancanti o parziali;
* il pacchetto ufficiale di evidenze SIA 4010 non è ancora disponibile;
* la classe di validazione SIA 4010 target non è ancora confermata.

Cosa Richiedere Ora
~~~~~~~~~~~~~~~~~~~

Evidenze prioritarie da raccogliere:

1. Classe SIA 4010 target: ``1A``, ``1B``, ``2A``, ``2B``, ``3``, ``4A``,
   ``4B`` o ``5``.
2. Specifiche ufficiali SIA 4010 e file di valutazione.
3. Output IESVE candidati trasferiti nei file ufficiali di valutazione.
4. Confronti di riferimento per ogni classe di validazione selezionata.
5. Evidenze su vetri e schermature, inclusi g-value e ipotesi di controllo.
6. Evidenze su ventilazione/AHU, inclusi recupero calore, perdite di carico,
   strategia di controllo e portate.
7. Evidenze sull'efficienza degli impianti di riscaldamento/raffrescamento.
8. Potenza di illuminazione e strategia di controllo.
9. Mappatura dei locali ai profili SIA selezionati.

Controlled Glossary
-------------------

.. list-table::
   :header-rows: 1
   :widths: 20 20 20 20

   * - English
     - French
     - German
     - Italian
   * - Readiness report
     - Rapport de préparation
     - Readiness-Report
     - Report di readiness
   * - Official evidence
     - Preuve officielle
     - Offizieller Nachweis
     - Evidenza ufficiale
   * - Not checkable
     - Non vérifiable
     - Nicht prüfbar
     - Non verificabile
   * - Compliance claim
     - Déclaration de conformité
     - Konformitätsaussage
     - Dichiarazione di conformità

Recommended Manager Discussion Agenda
-------------------------------------

1. Confirm the target outcome: internal QA, client readiness, or formal
   compliance submission.
2. Confirm the target SIA 4010 validation class.
3. Review the latest report dashboard and the P1 remediation list.
4. Assign ownership for missing SIA 380/2 model inputs and SIA 4010 evidence.
5. Decide the next VE run date after model corrections and evidence collection.
