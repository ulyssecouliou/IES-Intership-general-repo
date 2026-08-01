# ADR-001 — Architecture du MSP : deux processus, classeur SIA rempli, cas générés par script

> Statut : **ACCEPTÉE** (2026-07-30). Clôt la « décision d'architecture bloquante »
> laissée ouverte par la Phase 0 (`PROJECT_PLAN.md` §2).
> Toute affirmation ci-dessous porte sa source. Ce qui n'est pas vérifié est marqué
> `⚠ À VÉRIFIER` — ne pas le traiter comme acquis.

---

## 1. Décisions produit (arbitrées par le commanditaire)

| # | Décision | Conséquence |
|---|---|---|
| D1 | **Les deux périmètres, validation d'abord.** MSP = valider IESVE contre les cas officiels SIA 4010 (tests 1 à 5). La vérification des modèles de projet clients réutilisera ensuite le moteur et le reporting. | Le moteur et le format de résultats doivent être conçus dès maintenant pour accepter *deux sources d'entrée* : cas SIA paramétriques (MSP) et modèle client arbitraire (V2). |
| D2 | **Aucune interface web, ni locale, ni différée.** Le « navigateur » est une interface **dans VE** : dialogue Tkinter lancé depuis le *Python Scripts navigator*. Livrables = Excel + PDF. | La couche 4 « app web locale » de `PROJECT_PLAN.md` §2 est **supprimée du projet**, pas reportée. Le contrat JSON reste la frontière *interne* entre extraction, moteur et reporting. |
| D3 | **Les cas de test sont générés par script**, pas modélisés à la main. | Reproductible à chaque version de VE ; c'est le différenciateur du produit. Faisabilité vérifiée en §3. |

---

## 2. Décision technique n°1 — UN SEUL processus, entièrement dans VE

L'environnement Python de VE embarque tout ce dont le produit a besoin
(`VEScripts-API-VE2023.pdf` §1.3, *3rd Party Libraries*) :

| Bibliothèque | Version | Usage dans le produit |
|---|---|---|
| **Pywin32** (COM) | 219 | **piloter Excel** : remplir le classeur SIA officiel, forcer le recalcul, préserver les *chartsheets* |
| **ReportLab** | 3.2 | **PDF client** |
| XlsxWriter / Xlrd | 0.7.3 / 0.9.4 | création / lecture de classeurs (complément du COM) |
| Numpy / Pandas / Scipy | 1.11.0 / 0.18.1 / 0.17.0 | agrégation des séries horaires, classes de fréquence |
| Matplotlib (+Seaborn) | 1.5.1 | graphiques intégrés au PDF |
| Jinja2 / Pillow | 2.8 / 3.0.0 | gabarits de rapport par client, images |
| Tkinter | stdlib | **l'interface dans VE** (§1.2 renvoie explicitement au tutoriel Tkinter) |

**Conséquence : pas de second processus.** Le produit est **un seul script package
installable** (§3.2/§3.3) : il apparaît dans le *Python Scripts navigator*, ouvre son
dialogue Tkinter, génère les cas, simule, agrège, remplit le classeur SIA et émet le
PDF. Rien à installer chez le client en dehors de VE.

> ## ✅ MESURÉ DANS VE — 2026-07-31, sonde `ve_adapter/Run_VE_Probe_Runtime.py`
>
> La contradiction ci-dessous est **tranchée par l'exécution**. Le tableau des
> bibliothèques ci-dessus, issu du guide VE 2023, était périmé sur toute la ligne.
>
> ```
> sys.version    : 3.12.3 (tags/v3.12.3:f6650f9, Apr 9 2024) [MSC v.1938 64 bit]
> sys.executable : C:/Program Files/IES/VE 2025/apps/python/pythonw.exe
> ```
>
> | Bibliothèque | Guide VE 2023 | **Mesuré (VE 2025)** |
> |---|---|---|
> | Python | 3.4.3 | **3.12.3** |
> | numpy / pandas / scipy | 1.11.0 / 0.18.1 / 0.17.0 | **1.26.4 / 2.2.3 / 1.14.1** |
> | matplotlib | 1.5.1 | **3.10.0** |
> | **win32com.client** (COM) | 219 | **présent** |
> | **reportlab** | 3.2 | **4.2.0** |
> | xlsxwriter / xlrd | 0.7.3 / 0.9.4 | **3.2.0 / 2.0.1** |
> | **openpyxl** | *non listé* | **3.1.2** |
> | jinja2 / Pillow | 2.8 / 3.0.0 | **3.1.5 / 10.3.0** |
> | tkinter / iesve | stdlib / — | **présents** |
>
> **Conséquences fermes :**
>
> 1. **La contrainte « Python 3.4 » est ANNULÉE.** f-strings, `dataclasses`,
>    annotations : tout est disponible. Aucune règle de style de compatibilité
>    n'entre dans `CLAUDE.md`. (Le code déjà écrit sans f-string reste valable,
>    simplement inutilement prudent — pas de réécriture nécessaire.)
> 2. **L'architecture mono-processus est confirmée par la mesure**, pas seulement
>    par la documentation : COM pour remplir le classeur SIA officiel avec
>    recalcul et graphiques préservés, ReportLab pour le PDF, Tkinter pour
>    l'interface. Un seul package installable, rien à installer chez le client.
> 3. **`openpyxl` est présent dans VE** alors qu'il n'est pas documenté. Le moteur
>    et ses tests peuvent donc tourner à l'identique en CI et dans VE.
>
> **⚠ NOUVEAU POINT OUVERT — la doc API est en retard de deux versions.**
> L'installation est **VE 2025** ; `refs/VEScripts-API-VE2023.pdf` documente
> VE 2023. Toutes les affirmations d'API de cet ADR (§3 : `ApacheSim.run_simulation`,
> `ResultsReader.get_room_results`, `VECdbMaterial.set_properties`…) en sont
> tirées. Une API rétrécit rarement, mais elle s'étend : **obtenir le guide
> VEScripts VE 2025** avant de figer la couche adaptateur. La sonde de capacité
> `Run_VE_Reference_Model_Capability_Probe.py` du dépôt existant inventorie la
> surface réellement installée — c'est le contrôle à croiser.

**Version de Python : CONTESTÉE au moment de la rédaction, tranchée depuis
(encadré ci-dessus).** Deux sources se contredisaient :

- *La documentation* : l'aide de l'éditeur renvoie à **Python 3.4.3** (§2.2,
  *Help → Python Documentation*), et les bibliothèques listées ci-dessus sont toutes
  de 2016 (numpy 1.11, pandas 0.18.1, matplotlib 1.5.1). Cohérent avec un 3.4.
- *Le terrain* : le dépôt `IES-Intership-general-repo`, dont le lanceur
  `Run_VE_Swiss_Compliance.py` s'exécute depuis la fenêtre Scripts d'IESVE, utilise
  `@dataclass` dans **49 de ses 90 modules** et des f-strings dans 14. Ces
  constructions exigent Python **3.7+** et lèveraient une `SyntaxError` en 3.4.

Si le lanceur fonctionne réellement en production, le guide VE 2023 est périmé sur ce
point et **aucune contrainte 3.4 ne doit être imposée au code**. La preuve terrain pèse
plus lourd que le lien d'aide, mais elle n'a pas été observée directement ici.

> `⚠ À TRANCHER AVANT D'ÉCRIRE LA MOINDRE RÈGLE DE STYLE.` Exécuter dans VEScripts :
> `import sys; print(sys.version)`, puis l'import réel de chaque bibliothèque du
> tableau ci-dessus (leurs versions peuvent être tout aussi périmées dans le guide).
> Tant que ce n'est pas fait, **aucune règle de compatibilité n'entre dans
> `CLAUDE.md`** : une contrainte 3.4 imposée à tort appauvrirait le code sans raison,
> et une contrainte absente à tort casserait le produit à l'exécution.

Ce qui, lui, est acquis quelle que soit la réponse : `engine/` reste du Python **pur**
(aucun `import iesve`) afin d'être testable en CI sans licence VE, et le même moteur
tourne aux deux endroits — en CI et à l'intérieur de VE.

---

## 3. Décision technique n°2 — Les cas sont générés par l'API (D3 est faisable)

> ## ✅ CONFRONTÉ À VE 2025 — 2026-07-31
> Sondes `Run_VE_Probe_API_Surface.py` (surface du module) et
> `Run_VE_Reference_Model_Capability_Probe.py` (capacités réelles sur projet).
> Le tableau ci-dessous venait du PDF VE 2023 ; il est désormais **vérifié contre
> l'installation**.
>
> - **309 symboles publics** exposés par `iesve` en VE 2025, contre ~41 documentés
>   en 2023. **Aucun symbole documenté en 2023 n'a disparu.**
> - **Un seul écart sur le chemin critique** : `ApacheSim.save_options` n'existe
>   plus, remplacé par **`set_options`**. Méthodes réelles :
>   `get_options`, `set_options`, `reset_options`, `run_simulation`,
>   `run_compliance_simulation`, `run_loads_sizing`, `run_room_zone_loads`,
>   `set_hvac_network`, `show_simulation_dialog`, `stitch`.
>   Vérifié : `save_options` n'est **utilisé nulle part** dans
>   `IES-Intership-general-repo` — rien à corriger.
> - **L'API d'écriture est confirmée en exécution**, pas seulement en signature :
>   `create_material`, `create_construction`, `create_profile`,
>   `create_thermal_template`, `create_air_exchange`,
>   `assign_thermal_template_to_rooms`, `rebuild_adjacencies` répondent tous
>   `true`. Les énumérations résolvent (mur=2, toit=0, plancher=4, cloison=3,
>   porte=8, vitrage ext=6 ; opaque=0, vitré=1 ; uvalue iso=1). Les matériaux
>   exposent `conductivity`, `density`, `specific_heat_capacity`.
>   **D3 tient sur la version installée.**
> - **`VESurface.id` et `.name` sont des MÉTHODES** en VE 2025 (membres réels :
>   `get_adjacencies, get_areas, get_constructions, get_opening_by_id,
>   get_opening_totals, get_openings, get_properties,
>   get_thermal_bridges_non_repeating, get_thermal_bridges_random, id, index,
>   move, type`). Un `getattr` sans appel rend l'objet méthode — c'est le défaut
>   corrigé dans `aps_probe.py`, qui rendait l'identité des 354 surfaces
>   inutilisable.
> - **`ResultsReader` : 49 méthodes**, dont `get_peak_results` (voie directe pour
>   la Table 31), `get_all_room_results`, `get_surface_results`, `get_variables`,
>   `results_per_day`, `get_unmet_hours`.
> - **~140 symboles `HVAC*` ajoutés** depuis 2023 (`HVACNetwork`, `HVACBoiler`,
>   `HVACChiller`, `HVACHeatPump`, `HVACWaterWaterHeatPump`, `HVACVRFSystem`,
>   `HVACHeatRecoveryModel`…). Les tests 4 à 7 sont donc nettement mieux outillés
>   que ne le laissait croire la doc — y compris le point identifié comme le plus
>   dur du projet, la méthode PAC détaillée SIA 384/3 (`PROJECT_PLAN.md` phase 3).
>
> **⚠ NOUVELLE QUESTION NORMATIVE — quelle température opérative ?**
> L'`.aps` expose **deux** définitions concurrentes, plus deux voisines :
> `Operative temperature (ASHRAE)`, `Operative temperature (TM 52/CIBSE)`,
> `Dry resultant temperature` et `Environmental temperature` (toutes en °C,
> niveau zone, dérivées de `Room air temperature & Room radiant temp`).
> Les Tables 30 et 32 du Test 1 comparent une température opérative sans
> préciser laquelle. **Choisir la mauvaise produit une erreur silencieuse et
> plausible** — exactement le risque que le projet existe pour éliminer.
> À trancher par `norm-analyst` sur ASHRAE 140 (dont le Test 1 dérive) et les
> Anwenderberichte, avant tout binding.

Sources initiales : `refs/VEScripts-API-VE2023.pdf`. L'API `iesve` est **en
écriture**, pas seulement en lecture :

| Besoin des tests SIA | Méthode API vérifiée | Section |
|---|---|---|
| Propriétés matériaux (λ, ρ, cp, ε, α, τ) — ASHRAE 140 tab. 7-2 / 7-27 | `VECdbMaterial.set_properties()` : `conductivity`, `density`, `specific_heat_capacity`, `thickness`, `inside/outside_emissivity`, `…_reflectance`, `transmittance`, `visible_transmittance`, `refractive_index` | §6.1.31 |
| Composition des constructions | `VECdbConstruction.add_layer()`, `insert_layer()`, `delete_layer()`, `set_properties()`, `set_f_factor()` | §6.1.28 |
| **Coefficient de surface externe** (point ouvert de `test-1.spec.md` §8 pt 6) | `VECdbLayer.set_properties()` : `convection_coefficient` (W/m²K), `resistance`, `thickness` | §6.1.30 |
| Affectation aux surfaces / locaux | `assign_construction()`, `assign_thermal_template_to_rooms()` | — |
| Consignes, apports, infiltration | `set_room_conditions()`, `add_air_exchange()`, `create_profile()`, `save_profiles()` | §6.1.2, 6.1.5, 6.1.39, 6.1.42 |
| Protection solaire (Test 2) | `VESuncast`, `VESurface` (`get_results(shading_filename, …)`) | §6.1.44, 6.1.45 |
| Systèmes aérauliques (Tests 4-5) | `VEApacheSystem.set_apache_systems()`, section *HVAC Network* | §6.1.7, 6.1.26 |
| **Lancer la simulation sans interface** | `ApacheSim.save_options({...})` + `run_simulation()`. Options : `start/end_month`, `start/end_day`, `simulation_timestep`, `reporting_interval`, `HVAC`, `HVAC_filename`, `suncast`, `macroflo`, `preconditioning_days`, `results_filename`, options de sortie détaillée par local | §6.1.3 |
| **Lire les résultats horaires** | `ResultsReader.open(f)`, `get_room_results(room_id, aps_var, vista_var, var_level, start_day, end_day)` → tableau numpy ; `get_variables()` pour l'inventaire | §6.1.14 |
| Fichier météo de référence (DRYCOLD.TMY) | `WeatherFileReader.open_weather_file()`, `get_results(variable, start_day, end_day)` | §6.1.47 |
| **Distribution** | *Script package* installable (Tools → Manage Scripts), ajouté automatiquement au *Python Scripts navigator*, **chiffrable** et **soumis à licence** | §3.2, §3.3 |

Conclusion : le pipeline complet — *construire le cas → simuler → extraire l'horaire →
agréger* — est réalisable en script. La modélisation manuelle n'est nécessaire que pour
le **bâtiment exemple** des tests 4-7 (géométrie IFC/DWG), pas pour les cas 1 à 3.

Point de distribution notable : « navigateur » est un objet VE réel (*Python Scripts
navigator*), et les packages peuvent être **chiffrés et licenciés**. Le produit se
distribue donc nativement, sans installeur maison.

---

## 4. Décision technique n°3 — On remplit le classeur SIA, on ne le réimplémente pas

**Preuve** (`Test1/Resultaterfassung_Test1.xlsx`, feuille `Zusammenfassung Testfälle`) :

```
B16 = IF(Daten_Testprogramm!$H$3="Handeingabe"; Daten_Testprogramm!N28; Daten_Testprogramm!F28)
```

Les colonnes `Testprogramm` sont **calculées**, jamais saisies. `Daten_Testprogramm`
contient deux zones miroir : à gauche les agrégats dérivés des 8760 h, à droite
(`J:N`) la **saisie manuelle** activée par `H3 = "Handeingabe"`. Moyennes,
`obere/untere Grenze` et verdicts se recalculent seuls.

**Conséquences** :

1. Le livrable Excel est le **formulaire officiel SIA rempli** — crédibilité maximale
   auprès du SIA et des clients, et zéro risque de divergence d'interprétation.
2. Le moteur `engine/` recalcule les **mêmes verdicts de façon indépendante**. Deux
   chemins de calcul qui concordent = l'argument qualité du produit. S'ils divergent,
   on a un bug, et on le sait avant le client.
3. Chemin de moindre risque pour le MSP : **mode `Handeingabe`** (agrégats seulement,
   peu de cellules). Le remplissage horaire intégral (8760 × N colonnes) est une
   montée en puissance ultérieure, pas un prérequis.

**Remplissage : par COM, pas par `openpyxl`.** `openpyxl` ne recalcule pas les formules
et **détruit les graphiques** — or ces classeurs contiennent de vraies *chartsheets*
(Test 5 en compte ~28). Le pilotage d'Excel via **Pywin32/COM, disponible dans VE**
(§2), remplit `Daten_Testprogramm`, force le recalcul et préserve tout le reste.
À exécuter **sur une copie**, jamais sur les fichiers de `SIA_4010_geteilter_Link/`
qui sont la source figée. `⚠ À VÉRIFIER` : le poste client doit avoir Excel installé —
sinon prévoir un repli (XlsxWriter, classeur reconstruit, sans les graphiques SIA).

---

## 5. Périmètre réel du MSP (chiffré sur les sources)

`Daten_Testprogramm` L4/L5 distingue explicitement `obligatorisch: Testfälle` et
`freiwillig: Diagnosefälle`. **Les cas de diagnostic sont facultatifs** — hors MSP.

| Test | Cas obligatoires (Testfälle) | Grandeurs | Bâtiment exemple ? |
|---|---|---|---|
| 1 | 600, 640, 900, 940, 1E (+ 600FF, 900FF en flottement libre) | besoins chaud/froid mensuels+annuels, T° opérative mensuelle, extrêmes annuels | non — zone unique |
| 2 | 2A–2D | énergie annuelle d'apport solaire + classes de fréquence | non |
| 3 | `⚠ à confirmer` (structure identique à 2) | éclairage | non |
| 4 | `⚠ à confirmer` | — | **oui** |
| 5 | 5A–5D | 8 grandeurs annuelles (ventilateurs, batteries chaud/froid total+latent, WRG total+latent+auxiliaire, humidification) + classes de fréquence + profils semaine hiver/été | **oui** |

Ordre de grandeur : **~20-24 cas obligatoires** pour les tests 1 à 5. Tous les
classeurs partagent la même mécanique : `Testfälle` / `Diagnosefälle` / valeurs
annuelles / `Häufigkeitsklassen` / `Mittelwert` + `obere/untere Grenze`.

→ **Un seul moteur générique**, piloté par un descripteur déclaratif par test
(`refs/reference-data/testN.map.json` : feuille, ligne d'en-tête, blocs cas↔colonnes,
libellés de grandeurs), et non cinq implémentations.

---

## 6. Chemin critique

Le goulot n'est pas le code (≈25 % de l'effort) mais :

1. **Le spike VE** — zéro ligne écrite à ce jour dans `ve_adapter/`, variance la plus
   haute. Livrable : version Python + paquets réellement disponibles, et un aller-retour
   complet *écrire une construction → simuler → lire l'horaire → JSON*.
2. **Le bâtiment exemple** (tests 4-7) — modélisation humaine depuis
   `Beispielgebäude/` (IFC abstractBIM + 10 DWG + `Dokumentation_..._V5.pdf`).
   Non parallélisable par du code, à lancer indépendamment.
3. **Procurement des normes** — EN ISO 52016-1:2017 bloque le gel de
   `traceability/test-1.spec.md`. Coût faible, effet débloquant élevé, décision
   hors ingénierie.

## 7. Levier de process : rendre l'audit exécutable

`AUDIT.md` a coûté trois passes de vérification manuelle sur **un seul** fichier de
référence. Les 1336 comparaisons cellule↔valeur, les contrôles libellé↔colonne et la
formule du `Streubereich` sont des assertions déterministes → `engine/tests/`.
`qa-auditor` audite alors **les invariants une fois**, au lieu des données à chaque
régénération. Sans ça, le coût de l'audit croît linéairement avec 5 tests × N passes.

État vérifié le 2026-07-30 sur `refs/reference-data/test-1.ref.json` (passe 3) :
1336/1336 cellules concordantes, 0 incohérence libellé↔colonne en Table 30 sur les
6 cas, Table 32 réduite à 600FF/900FF. Les défauts n°1 et n°2 d'`AUDIT.md` sont
corrigés — mais l'audit **n'a pas été rejoué formellement** et la signature reste
refusée dans `AUDIT.md`.

---

## 7 bis. Angle mort de la CI — mesuré, puis FERMÉ (2026-07-31)

> **Correctif appliqué.** L'empreinte de cellules brutes décrite en fin de
> section existe : `refs/reference-data/test-1.cells.json` (38 Ko, 1352 cellules
> dont 80 erreurs Excel conservées telles quelles, plus les lignes d'en-tête
> 15/36/57/81/104), générée par `scripts/build_cell_fingerprint.py`.
>
> Nouvelle mesure par mutation, **sans le classeur** (conditions CI) :
>
> | Mutation injectée | Avant | Après |
> |---|---|---|
> | Défaut n°1 — décalage de colonnes (+1), Table 30 | **non détectée** | détectée (3 tests) |
> | Défaut n°2 — cas fantôme « 600 » en Table 32 | détectée | détectée |
> | Erreur Excel convertie silencieusement en 0 | **non détectée** | détectée |
> | Fausse formule `Streubereich` (min/max) | détectée | détectée |
> | Suppression silencieuse de la Table 31 | — | détectée (2 tests) |
>
> Le dispositif ne peut pas devenir un faux témoin : quand le classeur **et**
> l'empreinte sont présents, l'empreinte est vérifiée cellule à cellule contre le
> classeur ; et `test_empreinte_couvre_toutes_les_cellules_citees` échoue si une
> régénération du JSON cite des cellules que l'empreinte ne couvre pas.
> Le sha256 de la source enregistré dans l'empreinte
> (`7f7d2bc829ea0bb2…`) **coïncide avec celui du `official_manifest.json` du
> SIA** : la source est bien le fichier officiel non modifié.
>
> Effet de bord appréciable : la suite tombe de 17 s à 4,5 s sans le classeur.
>
> Le texte ci-dessous documente le constat initial, conservé pour la traçabilité.

### Constat initial (2026-07-30)

`engine/tests/test_ref_integrity.py` a été validé par mutation : quatre corruptions
volontaires ont été injectées dans une copie du JSON de référence.

| Mutation injectée | Détectée avec le classeur | Détectée **sans** le classeur (cas CI) |
|---|---|---|
| Défaut n°1 — décalage de colonnes (+1), Table 30 | oui | **non** |
| Défaut n°2 — cas fantôme « 600 » en Table 32 | oui | oui |
| Erreur Excel convertie silencieusement en 0 | oui | **non** |
| Fausse formule `Streubereich` (min/max) | oui | oui |

Autrement dit : **la CI telle que configurée ne peut pas attraper la classe de bug qui
s'est réellement produite.** Les deux contrôles les plus forts — fidélité
valeur↔cellule et libellé↔colonne — exigent la source, absente du dépôt (130 Mo pour
les sept classeurs).

Correctif proposé, peu coûteux : générer une **empreinte de cellules brutes** (adresse
→ valeur telle quelle, plus les lignes d'en-tête), quelques dizaines de Ko, versionnée
dans `refs/reference-data/`. Elle est produite depuis le classeur et re-vérifiée contre
lui dès qu'il est présent ; la CI compare alors le JSON de référence à l'empreinte.
Ce n'est pas circulaire : l'empreinte contient les cellules **brutes**, le JSON contient
leur **interprétation** (quel programme, quelle grandeur) — c'est précisément
l'interprétation qui était fausse dans les défauts n°1 et n°2.

## 8. Le dépôt existant change le plan

`C:\Users\ulysse.couliou\Documents\IES Internship\IES-Intership-general-repo` contient
déjà un produit en fonctionnement, bien plus avancé que le présent squelette :

- lanceur `Run_VE_Swiss_Compliance.py` utilisable depuis la fenêtre Scripts d'IESVE ;
- paquet `swiss_sia/` (5,8 Mo, 90 modules) : `sia4010_checker.py`, `sia380_checker.py`,
  `data_extractor.py`, `model_analyzer.py`, `excel_report.py`, et
  `reference_model/sia4010/` (`native_ui.py`, `navigator.py`, `test_runner.py`,
  `evidence_registry.py`, `workbook_loaders.py`, `frequency_distribution.py`,
  `compliance_comparator.py`, bundles Test 1 / Test 2A / Test 3…) ;
- **42 scripts `Run_VE_*.py`** d'inspection et de création d'actifs VE (constructions,
  templates thermiques, échanges d'air, vitrages, sonde APS, sonde de capacité) ;
- **538 tests** collectés ;
- `.codex_tmp/` : `DRYCOLD.TMY`, fichiers d'accompagnement ASHRAE 140, sondes Case 600.

Conséquences directes sur les décisions ci-dessus :

1. **Le spike VE (§6 pt 1) est en grande partie déjà réalisé.** Il ne reste que la
   question de version/bibliothèques (§2), qui tient en une ligne.
2. **D2 et D3 sont déjà implémentées** dans ce dépôt (interface native dans VE, actifs
   créés par script). Les reconstruire ici serait du gaspillage pur.
3. La valeur produite par le présent dépôt est ailleurs : les **données de référence
   vérifiées** (`test-1.ref.json`, 1336/1336), la **spec tracée** du Test 1, cet ADR, et
   le **test d'intégrité exécutable**. Ce sont des actifs portables.

→ **Décision de consolidation à prendre** : un seul dépôt. La direction recommandée est
de porter la rigueur d'ici (référence vérifiée, tests d'intégrité, traçabilité
clause→code→test) **vers** le dépôt qui fonctionne, et non l'inverse. Reste à appliquer
la doctrine `CLAUDE.md` : le code existant est présumé faux tant qu'il n'a pas été
confronté aux valeurs de référence désormais disponibles — c'est exactement l'audit que
`test-1.ref.json` rend enfin possible.

## 9. Ce que cette décision NE tranche PAS

- La version exacte de Python dans VEScripts — la liste des bibliothèques est
  documentée (§2), leur import réel reste à confirmer par le spike.
- La présence d'Excel sur le poste client, dont dépend la voie COM (§4).
- Les cas obligatoires des tests 3 et 4 (§5).
- Le variant de modélisation de fenêtre à retenir pour le Test 2 : les programmes de
  référence livrent trois variantes (`Fe det Spec`, `Fe det non Spec`, `Fe einf`) ;
  laquelle correspond à IESVE reste à déterminer avec `norm-analyst`.
- Les valeurs physiques de constructions/vitrage/infiltration du Test 1, toujours
  suspendues à EN ISO 52016-1:2017 (cf. `traceability/test-1.spec.md` §10).
