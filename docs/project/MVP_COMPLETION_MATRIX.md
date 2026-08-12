# MVP Completion Matrix — état factuel

**Date d'établissement** : 2026-08-11
**Source de vérité principale** : code + `config/sia4010_all_classes.json` + `refs/reference-data/*.json` + `sia4010_evidence/autonomy/sia4010_case_evidence.json` + `SIA_4010_geteilter_Link/official_manifest.json`.
**Portée** : sept tests SIA 4010:2023 (30 cas, dont le cas diagnostique 1E séparé) + readiness SIA 380/2:2022 (huit axes).

Cette matrice n'est ni un certificat, ni un rapport commercial. Elle documente l'état réel du dépôt, en séparant explicitement (a) test Python, (b) qualification VE réelle, (c) preuve/APS enregistrée, (d) critère officiel disponible. Elle est destinée à servir de backlog exécutable pour clore le MVP.

---

## Vocabulaire de statut

| Statut | Signification opérationnelle |
|---|---|
| `NOT_STARTED` | Ni moteur Python, ni générateur VE, ni preuve. |
| `IMPLEMENTED_UNQUALIFIED` | Moteur Python présent et testé en CI ; aucun run VE réel qualifié. |
| `READY_FOR_REAL_VE` | Générateur VE ou runtime-probe implémenté et testé sur `iesve` factice ; attend uniquement une exécution dans VEScripts avec `iesve` réel. |
| `RESULTS_RECORDED_NO_CRITERION` | Résultat APS extrait et enregistré ; le critère d'acceptation officiel n'existe pas ou n'est pas encore établi (cas Test 1 hors 1E, Tests 4/6 sans Testkriterien). |
| `READY_FOR_OFFICIAL_REVIEW` | Preuve, critère, extraction et verdict formés ; attend l'attestation de la sous-commission SIA. |
| `BLOCKED_BY_EXTERNAL_EVIDENCE` | Bloqué par une donnée externe non fournie (climat SIA 2028 solaire, licence, réponse SIA en attente). |

Aucune ligne ne peut porter `PASS` / `VALIDATED` : la validation SIA 4010 est un acte réservé à la sous-commission SIA (SIA 4010:2023 §4.6.2).

---

## 1. SIA 4010 — Test 1 (7 cas, dont 1E)

Test 1 est le **seul** test dont la spécification énonce ses propres critères ([`Spezifikation_Test1.pdf`, section Testkriterien] cité verbatim dans [engine/test1_engine.py:14-25](engine/test1_engine.py)). Le cas **1E** est le seul avec verdict pass/fail (Streubereich sur 4 programmes de référence). Les six autres cas sont explicitement **sans critère** — l'engine produit un delta informatif par programme. Météo = ISO 52016-1 DRYCOLD (Denver Stapleton) ; **pas SIA 2028**. Le fichier météo est fourni et audité ([`refs/reference-data/iso-52016-1-climat-drycold.json`](refs/reference-data/iso-52016-1-climat-drycold.json)).

| Cas | Exigence + source | Implémentation Python | Test Python | Générateur VE (état) | APS enregistré (ce projet) | Critère officiel | Statut | Prochain geste minimal |
|---|---|---|---|---|---|---|---|---|
| **1E** *(diagnostique)* | Streubereich pass/fail sur 4 programmes. Source : `Spezifikation_Test1.pdf` Testkriterien | [engine/test1_engine.py](engine/test1_engine.py) — `CAS_AVEC_CRITERE=('1E',)`, `evaluer_periode_1e` | [engine/tests/test_test1_engine.py](engine/tests/test_test1_engine.py) + `test_ref_integrity.py` | `NOT_IMPLEMENTED` — pas de branche dédiée dans [swiss_sia/reference_model/sia4010/case_registry.py:222-286](swiss_sia/reference_model/sia4010/case_registry.py); autonomy JSON confirme `mutation=False, runtime_qual=False` | Non | ÉNONCÉ (spec Test 1) ; référence FIGÉE dans [`refs/reference-data/test-1.ref.json`](refs/reference-data/test-1.ref.json) `CORRECTED_PASS_4` | `IMPLEMENTED_UNQUALIFIED` | **Chaîne de dépendances, pas un simple générateur.** [traceability/test-1.spec.md:349](traceability/test-1.spec.md) définit 1E comme « cas diagnostic **1D** + protection solaire par **store tissu** (Stoffmarkise) selon le test diagnostic **2 E1** ». Or `test_1/1A`…`1D` ne sont **pas** des cas enregistrés (`ConfigurationError: Unknown SIA 4010 variant/case combination`). Il faut donc, dans l'ordre : (1) enregistrer et générer 1D, (2) lier le store tissu — un gabarit existe déjà, `config/external_input_examples/sia_example_fabric_awning.binding.example.json`, et une qualification d'ombrage existe pour le Test 2A ([test2a_shading_qualification.py](swiss_sia/reference_model/sia4010/test2a_shading_qualification.py)), (3) inscrire 1E. Ne pas commencer par 1E |
| **600** *(6 cas normatifs — sans critère)* | Comparaison informative aux programmes de référence. Source : Testkriterien ("Es gibt dafuer kein Abweichungskriterium") | [engine/test1_engine.py](engine/test1_engine.py) — `comparer_periode_informative` | Idem 1E | `GUARDED_MUTATION_READY` — [case_registry.py:222](swiss_sia/reference_model/sia4010/case_registry.py) branche `case600_mvp_v1` ; APS réel et évaluation présents dans `sia4010_evidence/autonomy/sia4010_case_evidence.json` | **Oui, mais pré-correction** : `switzerland\test1_600\Vista\SIA4010_test_1_600_20260809_235015.aps`, `observed_metric_count=88`, `simulation_link_status=VERIFIED` — du 2026-08-09, donc **antérieur** à `c7e906b` (2026-08-12 12:55). Base de référence, non citable comme résultat | Aucun critère (par spec) | `RESULTS_RECORDED_NO_CRITERION` | Requalifier après la correction ventilation, puis **verrouiller** le pipeline 600 comme référence de non-régression |
| **640** | Informatif (idem 600) | Idem | Idem | `RUNTIME_QUALIFICATION_READY` — generator `test1_lightweight_runtime_probe_v1` ; blocker `VE_RUNTIME_QUALIFICATION_REQUIRED` | **Oui, mais pré-correction** : APS `…_640_20260811_234852.aps`, du 2026-08-11, donc **antérieur** au commit de correction `c7e906b` (2026-08-12 12:55). `result_evidence = REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION`, mais c'est une **base de référence à requalifier**, pas une preuve citable | Aucun | `READY_FOR_REAL_VE` | Requalifier (runtime inputs + ApacheSim + nouvel APS) comme fait pour 600FF le 2026-08-12 |
| **900** | Informatif (idem 600, haute masse) | Idem | Idem | `RUNTIME_QUALIFICATION_READY` — generator `test1_heavyweight_runtime_probe_v1` | Non | Aucun | `READY_FOR_REAL_VE` | Idem 640 |
| **940** | Informatif | Idem | Idem | `RUNTIME_QUALIFICATION_READY` — heavyweight | Non | Aucun | `READY_FOR_REAL_VE` | Idem |
| **600FF** *(free-float)* | Informatif | Idem | Idem | `RUNTIME_QUALIFICATION_READY` — lightweight | **Oui, et POST-correction** — le seul cas dans cet état. Requalifié le 2026-08-12 : ventilation mécanique nulle vérifiée à zéro après read-back, infiltration prescrite 0,3075 `units_val=2` conservée séparément. APS `SIA4010_test_1_600FF_20260812_141823.aps`, sha256 `bcbb9deb…34f813`, 39 métriques ; entrée ledger écrite à 14:18:27 UTC, soit **après** le commit de correction `c7e906b` (12:55:25). Simulation exécutée, statut `SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION` | Aucun | `READY_FOR_REAL_VE` | Qualifier l'APS (dernière étape de la chaîne pour ce cas) |
| **900FF** | Informatif | Idem | Idem | `RUNTIME_QUALIFICATION_READY` — heavyweight | Non | Aucun | `READY_FOR_REAL_VE` | Idem |

**Note d'audit** : les paths locaux dans [`sia4010_evidence/autonomy/sia4010_case_evidence.json`](sia4010_evidence/autonomy/sia4010_case_evidence.json) pointent hors dépôt (`C:\...\switzerland\test1_600\...`). Seuls les entrées `test_1/600` ont été inspectées et portent réellement des artefacts vérifiés ; les 29 autres entrées portent la même structure de champs mais ne sont pas garantie d'artefacts persistés au même niveau — à confirmer par un audit d'existence de fichiers avant de citer.

---

## 2. SIA 4010 — Test 2 (4 cas)

Classe(s) concernée(s) : `1A` (cas 2A), `1B` (2B, 2C, 2D), `2A` (2A), `2B` (2B-2D), `4A` (2A), `4B` (2B-2D). Météo Kloten = **bloqué par irradiance solaire manquante**. Critère : bande annuelle **+** distribution horaire ; réponse d'autorité `Streubereich = min/max des programmes` reçue le 2026-08-10 et intégrée à [engine/sia_distributions_engine.py:11-19](engine/sia_distributions_engine.py).

| Cas | Implémentation Python | Test Python | Générateur VE | APS enregistré | Critère officiel | Statut | Prochain geste minimal |
|---|---|---|---|---|---|---|---|
| **2A** | [engine/sia_bandes_engine.py](engine/sia_bandes_engine.py) + [engine/sia_distributions_engine.py](engine/sia_distributions_engine.py) ; source-traced bundle Test 2A dans [swiss_sia/reference_model/sia4010/test2a_source_bundle.py](swiss_sia/reference_model/sia4010/test2a_source_bundle.py) | `engine/tests/test_sia_bandes_engine.py`, `test_distributions_engine.py`, `test_references_bandes.py`, `test_distributions_ref.py`, `tests/test_sia4010_test2a_*` (10 fichiers) | `NOT_IMPLEMENTED` mutation ; `runtime_discovery_supported=True` + `source_bound_bundle_supported=True` ([case_registry.py:48-63](swiss_sia/reference_model/sia4010/case_registry.py)) | Non | Bande annuelle : `ENONCE_DANS_LA_SPEC` (moteur) ; distribution : `CONFIRME_AUTORITE_2026-08-10` ; référence FIGÉE [`refs/reference-data/test-2.ref.json`](refs/reference-data/test-2.ref.json) + [`test-2.distributions.ref.json`](refs/reference-data/test-2.distributions.ref.json) | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` (SIA 2028 solaire) | Débloquer SIA 2028 solaire (question 1 du courriel brouillon 2026-08-10) puis implémenter le générateur VE 2A |
| **2B** | Idem 2A | Idem | `NOT_IMPLEMENTED` | Non | Idem | Idem | Idem |
| **2C** | Idem | Idem | `NOT_IMPLEMENTED` | Non | Idem | Idem | Idem |
| **2D** | Idem | Idem | `NOT_IMPLEMENTED` | Non | Idem | Idem | Idem |

**Discordance à corriger** : `refs/reference-data/test-2.ref.json.critere.statut = "INFERE"` alors que `sia_bandes_engine.CRITERE_PAR_TEST[2] = "ENONCE_DANS_LA_SPEC"`. À aligner (le moteur est correct — la spec Test 2 énonce bien le critère de bande annuelle).

---

## 3. SIA 4010 — Test 3 (12 cas)

Classe(s) : `2A` (3A-3F), `2B` (3A-3L), `4A` (3A-3F), `4B` (3A-3L). ~~Météo Kloten = bloqué (SIA 2028 solaire).~~ **Climat reçu et installé le 2026-08-12** (voir §10).

**Probe runtime exécutée en VE 2025 réel le 2026-08-12** — première exécution de cette probe. Projet `ZOER_32_C1_TEST`, scénario `test_3A/3A` préparé par [Run_VE_SIA4010_Prepare_Case_Scenario.py](Run_VE_SIA4010_Prepare_Case_Scenario.py). Verdict `SOURCE_BINDINGS_REQUIRED` : **20 champs d'éclairage observés**, 4 membres liés aux capteurs, 12 variantes exactes auditées. Rapport `sia4010_artifacts/diagnostics/sia4010_test3_runtime_capability_20260812_170256.json`. Aucune donnée de modèle modifiée. Ce que cela établit : l'API VE expose bien la surface nécessaire ; ce qui manque n'est pas une capacité VE mais les **liaisons de sources externes** (SIA 2024 notamment). Ce n'est ni une validation ni une revendication de conformité.

| Cas | Implémentation Python | Test Python | Générateur VE | APS enregistré | Critère officiel | Statut | Prochain geste minimal |
|---|---|---|---|---|---|---|---|
| **3A**..**3L** (12 cas) | `sia_bandes_engine.py` + `sia_distributions_engine.py` ; bundle Test 3 dans [test3_source_bundle.py](swiss_sia/reference_model/sia4010/test3_source_bundle.py), runtime probe dans [test3_runtime_capability.py](swiss_sia/reference_model/sia4010/test3_runtime_capability.py) | `engine/tests/test_sia_bandes_engine.py` (`(3, 12)`), `test_distributions_engine.py`, `test_references_bandes.py`, `tests/test_sia4010_test3_*` (3 fichiers) | `NOT_IMPLEMENTED` mutation ; `runtime_discovery_supported=True` + `source_bound_bundle_supported=True` | Non | Bande annuelle : `ENONCE_DANS_LA_SPEC` ; distribution : `CONFIRME_AUTORITE_2026-08-10` ; référence FIGÉE dans [`refs/reference-data/test-3.ref.json`](refs/reference-data/test-3.ref.json) (12 cas) + [`test-3.distributions.ref.json`](refs/reference-data/test-3.distributions.ref.json) (12 individuels + 4 agrégats A-F, G-H, I-J, K-L) | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` | Débloquer SIA 2028 solaire puis générateur VE Test 3 (éclairage + apports internes + facteurs de contrôle) |

**Discordance** : idem Test 2 (`test-3.ref.json.critere.statut = "INFERE"` vs moteur `ENONCE_DANS_LA_SPEC`).

---

## 4. SIA 4010 — Test 4 (1 cas)

Classe(s) : `3`, `4A`, `4B`. **Pas de section Testkriterien** dans `Spezifikation_Test4.pdf` — question 3 du courriel du 2026-08-07 (brouillon non envoyé) reste ouverte. Météo Kloten = bloqué solaire.

**Probe runtime Tests 4-7 exécutée en VE 2025 réel le 2026-08-12** — première exécution. Projet `ZOER_32_C1_TEST`, scénarios `test_4/4` puis `test_7/7` préparés par [Run_VE_SIA4010_Prepare_Case_Scenario.py](Run_VE_SIA4010_Prepare_Case_Scenario.py). Verdict `SOURCE_BINDINGS_REQUIRED` pour les deux : collection de systèmes Apache observée, read-back système par pièce observé, **29 membres spécifiques aux centrales**, 7 cas exacts audités. Rapports sous `sia4010_artifacts/diagnostics/sia4010_tests4_7_runtime_capability_20260812_170438.json` et `..._170514.json`. Aucune donnée de modèle modifiee. Ce que cela etablit : la surface ApacheHVAC necessaire est presente dans VE ; le blocage restant est la liaison des sources externes et le critere de distribution, pas une capacite VE manquante.

| Cas | Implémentation Python | Test Python | Générateur VE | APS | Critère officiel | Statut | Prochain geste |
|---|---|---|---|---|---|---|---|
| **4** | `engine/sia_bandes_engine.py` (bande annuelle uniquement — pas de distribution : `TESTS_SUPPORTES=(2,3,5)`) ; consignes de température FIGÉES dans [`refs/reference-data/test-4.consignes.json`](refs/reference-data/test-4.consignes.json) | `engine/tests/test_references_bandes.py` (`(4, 3, 3)`), `test_construire_test4.py` (script hors moteur) | `NOT_IMPLEMENTED` — blocker `VE_HEATING_COOLING_SETPOINT_BINDING_NOT_IMPLEMENTED` ([case_registry.py](swiss_sia/reference_model/sia4010/case_registry.py)) | Non | `INFERE` (SIA 4010 §4.4 délègue au classeur) ; référence FIGÉE [`refs/reference-data/test-4.ref.json`](refs/reference-data/test-4.ref.json) 3 grandeurs | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` | (a) Envoyer le courriel 2026-08-07 pour confirmer le critère bande annuelle seul ; (b) débloquer SIA 2028 solaire ; (c) implémenter le générateur VE (chauffage/rafraîchissement + courbe de consigne SIA 380/2 fig. 1) |

---

## 5. SIA 4010 — Test 5 (4 cas)

Classe(s) : `3`, `4A`, `4B`. Nomenclature effective **5A, 5B, 5C, 5D** — les identifiants « 5.1..5.4 » n'existent nulle part dans le dépôt.

| Cas | Implémentation Python | Test Python | Générateur VE | APS | Critère | Statut | Prochain geste |
|---|---|---|---|---|---|---|---|
| **5A**..**5D** (4 cas) | `sia_bandes_engine.py` + `sia_distributions_engine.py` ; réseau ventilation figé dans [`refs/reference-data/test-5.reseau.json`](refs/reference-data/test-5.reseau.json) (statuts `RELEVE/A_CONFIRMER/RELEVE_SUR_GRAPHIQUE`) | `engine/tests/test_references_bandes.py` (`(5, 8, 16)`), `test_distributions_engine.py`, `test_reseau_ventilation.py` | `NOT_IMPLEMENTED` — blocker `VE_MECHANICAL_VENTILATION_BINDING_NOT_IMPLEMENTED` | Non | Bande annuelle : `ENONCE_DANS_LA_SPEC` (moteur) ; distribution : `CONFIRME_AUTORITE_2026-08-10` ; FIGÉE [`refs/reference-data/test-5.ref.json`](refs/reference-data/test-5.ref.json) (16 lignes grandeur×cas) + [`test-5.distributions.ref.json`](refs/reference-data/test-5.distributions.ref.json) (16 distributions ; 1 sans `cas` — réserve documentée dans la ref) | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` | Débloquer SIA 2028 solaire ; implémenter les liaisons ApacheHVAC (récupérateur, batteries, humidificateur) ; qualifier avec probe dédiée `test4_7_runtime_capability_probe` |

**Discordance** : idem T2/T3 (`test-5.ref.json.critere.statut = "INFERE"` vs moteur `ENONCE_DANS_LA_SPEC`).
**Réserve documentée** : une distribution T5 n'a pas de libellé `cas` dans le classeur ; la réserve figure dans le JSON, ne pas la « corriger » silencieusement.

---

## 6. SIA 4010 — Test 6 (1 cas)

Classe(s) : `3`, `4A`, `4B`. Pas de section Testkriterien (idem Test 4 — question 3 du courriel 2026-08-07 ouverte).

| Cas | Implémentation Python | Test Python | Générateur VE | APS | Critère | Statut | Prochain geste |
|---|---|---|---|---|---|---|---|
| **6** | `sia_bandes_engine.py` (bande annuelle seule) ; réseau figé [`refs/reference-data/test-6.reseau.json`](refs/reference-data/test-6.reseau.json) | `engine/tests/test_references_bandes.py` (`(6, 6, 6)`), `test_reseau_ventilation.py` | `NOT_IMPLEMENTED` — blocker `VE_HVAC_HYDRAULIC_BINDING_NOT_IMPLEMENTED` | Non | `INFERE` ; référence FIGÉE [`refs/reference-data/test-6.ref.json`](refs/reference-data/test-6.ref.json) 6 grandeurs | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` | (a) Confirmer critère bande annuelle seule via SIA ; (b) débloquer SIA 2028 solaire ; (c) implémenter le générateur VE (réseau + circuit hydraulique) |

---

## 7. SIA 4010 — Test 7 (1 cas)

Classe(s) : `4A`, `4B`, `5` (Test 7 est le seul test de la classe `5`). PV + machine frigorifique + réseau.

| Cas | Implémentation Python | Test Python | Générateur VE | APS | Critère | Statut | Prochain geste |
|---|---|---|---|---|---|---|---|
| **7** | [engine/test7_engine.py](engine/test7_engine.py) — moteur dédié 11 bandes (5 froid + 5 chaud + 1 PV), Testgrössen vs Diagnosegrössen, verrou PV/irradiance | `engine/tests/test_test7_engine.py`, `test_references_bandes.py`, `scripts/build_test7_reference.py` | `NOT_IMPLEMENTED` — blocker `VE_ENERGY_SYSTEM_BINDING_NOT_IMPLEMENTED` | Non | `INFERE` au sens spec (pas de Testkriterien) **mais** classeur officiel corrigé par SIA le 2026-08-10 (règle conditionnelle L8→N8) et audit consigné [`sia4010_evidence/source_audits/test7-corrected-workbook-20260810.json`](sia4010_evidence/source_audits/test7-corrected-workbook-20260810.json) : `VERIFIED_CORRECTION_READY_FOR_TEST7_EVALUATION`. Référence FIGÉE [`refs/reference-data/test-7.ref.json`](refs/reference-data/test-7.ref.json) daté 2026-08-10 (11 grandeurs, bandes numériquement identiques après correction) | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` | Débloquer SIA 2028 solaire (irradiance nécessaire pour la production PV) ; implémenter la chaîne émission/distribution/stockage/génération VE ; extraire les 11 grandeurs annuelles depuis APS |

---

## 8. SIA 4010 — vue par classe de validation

Résumé exécutif dérivé de [`config/sia4010_all_classes.json`](config/sia4010_all_classes.json). Une classe n'est jamais « validée » sans attestation de la sous-commission — la colonne « État » synthétise uniquement la couverture logicielle.

| Classe | Variantes exigées | Cas VE exécutés | Générateurs VE prêts | État global |
|---|---|---|---|---|
| **1A** | `test_1` + `test_2A` | 1 sur 8 (T1/600) | 6/8 (T1/600 mutation + 5 T1 runtime-probe) | Partiel : Test 1 avance, Test 2A bloqué (SIA 2028 solaire) |
| **1B** | `test_1` + `test_2B..2D` | 1 sur 10 | 6/10 | Idem |
| **2A** | `test_1` + `test_2A` + `test_3A..3F` | 1 sur 14 | 6/14 | Bloqué SIA 2028 solaire (Tests 2/3) |
| **2B** | `test_1` + `test_2B..2D` + `test_3A..3L` | 1 sur 22 | 6/22 | Idem |
| **3** | `test_1` + `test_4` + `test_5A..5D` + `test_6` | 1 sur 13 | 6/13 | Bloqué SIA 2028 solaire + Testkriterien 4/6 ouverts |
| **4A** | 15 variantes | 1 sur 21 | 6/21 | Bloqué SIA 2028 solaire ; Test 7 attend systèmes énergétiques |
| **4B** | 23 variantes | 1 sur 30 | 6/30 | Idem |
| **5** | `test_7` | 0 sur 1 | 0/1 | Bloqué SIA 2028 solaire ; Test 7 attend systèmes énergétiques |

---

## 9. SIA 380/2 — readiness (huit axes)

Toute la logique est portée par `swiss_sia/sia380_checker.py` (checks unitaires) + `swiss_sia/reference_project.py` (spécification du bâtiment de référence). Le climat d'application (CH2018 RCP 8.5 « 2035 » — SIA 4010 §3.1.1) reste **du texte de règle** dans le checker (aucun binding binaire), et la question du choix imposé côté conformité SIA 380/2 est ouverte (question 2 du courriel brouillon 2026-08-10). Chaque axe ci-dessous a une couverture Python testée en CI ; aucun ne peut être déclaré « qualifié » sans exécution VE réelle + CSV projet remplis.

| Axe | Module porteur | Test Python | APS/donnée requise | Critère | Statut | Prochain geste minimal |
|---|---|---|---|---|---|---|
| **Modèle / métadonnées / climat** | [swiss_sia/evidence_manager.py](swiss_sia/evidence_manager.py) `scan_sia3802_project_metadata` + [reference_model/client_weather_conversion.py](swiss_sia/reference_model/client_weather_conversion.py) | [tests/test_project_metadata_evidence.py](tests/test_project_metadata_evidence.py), `test_client_weather_conversion.py`, `test_sia4010_weather_conversion.py`, `test_sia4010_weather_verification.py` | CSV `SIA3802_project_metadata_<project>.csv` rempli + météo CH2018 identifiée | Statut nouveau/existant, altitude, fichier météo tolérance non chiffrée | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` (question 2 SIA sur climat 380/2) | Remplir métadonnées ZOER, envoyer courriel 2026-08-10, générer les 4 climats de ZOER via `generated_weather/GVE/` |
| **Enveloppe** (U, ff, ponts thermiques) | `sia380_checker._check_envelope` + [reference_project.py](swiss_sia/reference_project.py) `build_reference_project_specification` | `tests/test_sia3802_normative_extensions.py`, `test_reference_project.py`, `test_reference_model_asset_provisioning.py` | Constructions VE + `bs_en_410` glazing | Diagnostic vs Tables 2/3 SIA 380/2:2022 ; jamais standalone `FAIL` (design décidé sur global) | `IMPLEMENTED_UNQUALIFIED` (rapports ZOER générés) | Post-VE réel : verrouiller `ff` restants (`STD_EXTW` ff=0.30, `STD_EXT2` ff=0.35 signalés dans `OPEN_ITEMS_BACKLOG.md`) |
| **Ventilation** (débits, contrôles, récupération) | `sia380_checker._check_ventilation` + règle `SIA3802_VENTILATION_CONTROL_CLASS` | `tests/test_sia3802_normative_extensions.py::test_table_4_ventilation_control_pass_fail_and_missing` | Airflow, contrôle Table 4, récupération | Diagnostic Table 4 | `IMPLEMENTED_UNQUALIFIED` | Compléter `SIA2024_usage_mapping_<project>.csv` + preuves AHU (pertes de charge, étanchéité, efficacité récupération vérifiée) |
| **Éclairage** | `sia380_checker._check_gains` + règle `SIA3802_LIGHTING_POWER` + `evidence_manager.scan_sia3874_lighting_mappings` | `tests/test_sia3802_normative_extensions.py`, `test_solar_protection_logic.py` | Puissance lumineuse VE + mapping contrôle SIA 3874 | Readiness only (SIA 387/4 délégué) | `IMPLEMENTED_UNQUALIFIED` | Remplir `SIA3874_lighting_control_mapping_<project>.csv` réviseur ; attacher résultats Test 3 après VE réel |
| **Confort dynamique** | `sia380_checker._check_dynamic_method` + règle `SIA3802_SUMMER_COMFORT_DYNAMIC` | `tests/test_sia3802_normative_extensions.py` | Séries annuelles APS température/occupation + courbes SIA 180 sup/inf | 0 h sup pour fenêtres opérables, sinon 100 h neuf/400 h existant, 0 h inf | `IMPLEMENTED_UNQUALIFIED` | Remplir métadonnées CSV, vérifier séries annuelles complètes par pièce, statuer sur l'opérabilité des fenêtres |
| **Systèmes CVC/ECS** | `sia380_checker._check_hvac`, `_check_hvac_metric`, `_check_setpoints` | `tests/test_sia3802_normative_extensions.py::test_hvac_eer_seer_and_scop_pass_fail_and_missing` | Classe générateur, capacité, EER/SEER/SCOP, Table 7 EER+ | Bandes Tables 5-9 SIA 380/2:2022 | `IMPLEMENTED_UNQUALIFIED` | Post-VE réel : compléter EER+, auxiliaires, part-load ; retirer `SYST0000` unclassified sur SIA_compatible_model |
| **Résultats APS** | [swiss_sia/simulation_results.py](swiss_sia/simulation_results.py) + [runtime_inventory.py](swiss_sia/runtime_inventory.py) (untracked) | `test_iesve_extraction_contract.py`, `test_runtime_inventory.py`, `test_sia4010_aps_probe.py`, `test_sia4010_qualified_aps.py` | Fichier `.aps` complet, variables room-level | Extraction avec unités et conversions | `IMPLEMENTED_UNQUALIFIED` | Sur prochain Run VE, confirmer variables APS exposées et sondes `Run_VE_SIA4010_APS_Probe.py` + `Run_VE_SIA4010_Qualify_APS_Hour_Convention.py` |
| **Comparaison bâtiment de référence + preuves** | `reference_project.py` (spec) + `sia380_checker._check_global_reference_comparison` + `evidence_manager.find_accepted_global_comparison` | `tests/test_reference_project.py`, `test_project_metadata_evidence.py`, `test_evidence_bootstrap.py`, `test_claim_safety_extensions.py` | CSV `SIA3802_global_reference_comparison_<project>.csv` rempli et signé | Gate compliance (jamais inféré des composants) | `BLOCKED_BY_EXTERNAL_EVIDENCE` | Remplir + faire réviser le CSV pour ZOER ; l'agrégation/pondération annuelle SIA 380 reste externe |

**Puissance de dimensionnement** — annexée : la sélection 14 j préconditionnement + 4 j chauffage / 3 j refroidissement est encodée mais **`NOT_CHECKABLE` depuis les pics annuels** (`OPEN_ITEMS_BACKLOG.md`). Statut : `NOT_STARTED` pour un run réel — fichiers APS design-day séparés et mapping de variables à produire.

---

## 10. Bloqueurs externes transversaux

| Bloqueur | Impact | Statut | Origine |
|---|---|---|---|
| ~~**SIA 2028 DRY normal solaire Zurich Kloten**~~ | ~~Bloque les 8 classes SIA 4010~~ | **LEVÉ le 2026-08-12.** `KLO_dry.txt` fourni par la SIA, importé en source tracée (`references/standards/sia2028/`, SHA-256 `aa3f3853…37ffd`), authentifié sur quatre axes indépendants (moyenne annuelle 9,4692 °C et max 34,1 °C identiques à une extraction indépendante, offset 0 ; point de rosée 0,538 K sur 8760 lignes ; enthalpie 0,131 kJ/kg ; humidité absolue 0,109 g/kg), converti en EPW et installé dans VE. **Réserve** : 11 colonnes sur 24 restent `[TO VERIFY]` faute de légende publiée — voir `KLO_dry.provenance.json`. IES n'a **pas** de licence SIA 2028 : ce fichier est notre seule source. | Externe SIA — reçu |
| **Base climatique 380/2 sur bâtiment réel** | Bloque compliance SIA 380/2 sur bâtiment réel (Meteonorm/IWEC/TMY acceptables ?) | Question 2 du même brouillon | Externe SIA |
| **SIA 2024 en machine-readable** | Ralentit tests 2-6 (fiches d'usage transcrites depuis PDF) | Question 3 du même brouillon ; contournement partiel : extrait autorité cat. 3.1 (bureau) daté 2026-08-10 dans [`sia4010_evidence/source_audits/sia2024_3_1_authority_20260810/`](sia4010_evidence/source_audits/sia2024_3_1_authority_20260810/) | Externe SIA |
| **Critère de distribution Tests 4, 6 et 7** | Les distributions sont extraites mais ne produisent aucun verdict : statut `RESULTS_RECORDED_NO_CRITERION` | **Question reformulée le 2026-08-12.** Notre affirmation précédente — « ces classeurs n'ont ni classes de fréquence ni feuilles de distribution » — était **fausse**, relevée par Prof. Zweifel. Ils en ont : feuille `Haeufigkeitskassen` (sans le `l`, contre `Haeufigkeitsklassen` dans les Tests 2/3/5, ce qui expliquait notre angle mort), et les feuilles `Verteilung` y sont des **graphiques** et non des feuilles de calcul. 38 distributions désormais figées (T4 = 11, T6 = 10, T7 = 17). La question qui reste : la règle min/max confirmée le 2026-08-10 pour les Tests 2/3/5 est-elle opposable ici, alors que ces classeurs ne portent aucune section `Testkriterien` et qu'aucune cellule n'y calcule de bande ? Brouillon vérifié : [`SIA_CORRESPONDANCE_ZWEIFEL_2026-08-12.md`](docs/project/SIA_CORRESPONDANCE_ZWEIFEL_2026-08-12.md) — **non envoyé** | Externe SIA |
| **Attestation sous-commission** | Aucune classe ne peut porter `VALIDATED` avant attestation | SIA 4010:2023 §4.6.2 | Externe SIA |
| **Exécution VE 2025 réelle** | Tous les cas T1/(640..900FF) et tout Test 2-7 non exécutables sans `iesve` réel | Toute qualification `RUNTIME_QUALIFICATION_READY` → `READY_FOR_REAL_VE` | Interne, à la charge d'Ulysse |
| **Systèmes énergétiques VE (Test 7)** | Émission/distribution/stockage/génération non liés à un pattern de mutation VE testé | Blocker `VE_ENERGY_SYSTEM_BINDING_NOT_IMPLEMENTED` | Interne, non planifié |

---

## 11. Réponses SIA reçues (2026-08-10) — à ne pas oublier

Trois preuves d'autorité ont été **reçues et intégrées** ; à distinguer des deux brouillons non envoyés :

- **Streubereich = enveloppe min/max des programmes** — clarification écrite de Prof. Gerhard Zweifel intégrée à [engine/sia_distributions_engine.py:11-19](engine/sia_distributions_engine.py) et à chaque `test-*.distributions.ref.json` (`statut_critere = "CONFIRME_AUTORITE_2026-08-10"`).
- **Classeur Test 7 corrigé** — la règle conditionnelle passe de `$L8..$M8` à `$N8..$M8` (bande inclusive `lower..upper`) ; bornes numériques identiques ; audit dans [`sia4010_evidence/source_audits/test7-corrected-workbook-20260810.json`](sia4010_evidence/source_audits/test7-corrected-workbook-20260810.json). Fichier `.pre-correction` conservé dans `superseded_sources/Test7/`.
- **SIA 2024 catégorie 3.1 (bureau)** — extrait autorité + binding + validation `PASS` dans [`sia4010_evidence/source_audits/sia2024_3_1_authority_20260810/`](sia4010_evidence/source_audits/sia2024_3_1_authority_20260810/). Les autres catégories restent à transcrire manuellement depuis les fiches PDF SIA 2024:2021.

---

## 12. Documents devenus obsolètes ou incomplets depuis la réception des classeurs officiels et des trois autorités du 2026-08-10

Ces documents sont conservés **en l'état** (ils gardent une valeur historique et d'audit), mais ne doivent plus être cités comme source de vérité pour une décision d'implémentation.

| Document | Raison de l'obsolescence |
|---|---|
| [docs/project/SIA3802_SIA4010_IMPLEMENTATION_STATUS.md](docs/project/SIA3802_SIA4010_IMPLEMENTATION_STATUS.md) | Prescrit `swiss_sia.sia4010_test_adapters` comme boundary d'intégration classeur ; le code effectif vit désormais dans `swiss_sia/reference_model/sia4010/` (52 modules, dont 12 modifiés et 2 untracked). Le tableau des classes reporte uniformément « Variant readiness only » alors que `case_registry.all_case_capabilities()` distingue désormais `GUARDED_MUTATION_READY`, `RUNTIME_QUALIFICATION_READY`, `NOT_IMPLEMENTED` par cas. Ignore complètement la surface untracked (`compliance_hub*`, `evidence_wizard*`, `remediation_probe`, `runtime_inventory`, `reference_model_setup*`, `hour_convention`, `test1_campaign`). |
| [docs/project/SIA4010_TESTS_AND_CLASSES_IMPLEMENTATION.md](docs/project/SIA4010_TESTS_AND_CLASSES_IMPLEMENTATION.md) | Cite `swiss_sia/sia4010_checker.py`, `swiss_sia/sia4010_prevalidation.py` comme les modules d'implémentation ; la logique effective par cas est passée dans `swiss_sia/reference_model/sia4010/*` (documenté dans `OPEN_ITEMS_BACKLOG.md:7` recently-closed 2026-07-23) mais ce document n'a jamais été mis à jour. Antérieur à l'arrivée des classeurs officiels. |
| [docs/project/CLIENT_RUN_GUIDE.md](docs/project/CLIENT_RUN_GUIDE.md) | Désigne `Run_VE_Swiss_Compliance.py` comme unique point d'entrée client. La stratégie actuelle (cf. [`swiss_sia/compliance_hub.py`](swiss_sia/compliance_hub.py) et le prompt 11 de `PROMPTS_CLAUDE_FIN_MVP.md`) fait de `Run_VE_Swiss_Compliance_Hub.py` (untracked) le démonstrateur final agrégeant 6 workflows. Le guide n'a pas été mis à jour. |
| [docs/project/SIA_MODEL_BUILDER_GUIDE.md](docs/project/SIA_MODEL_BUILDER_GUIDE.md) | Le paragraphe (§annexe fichiers de config) déclare `config/sia4010_classes_1a_1b.json` « spécialisé Tests 1-3, plus manifeste global » et pointe vers `config/sia4010_all_classes.json`. Ce dernier fichier existe bien et couvre les 8 classes. **Contradictoire** avec [docs/project/PROMPTS_CLAUDE_FIN_MVP.md](docs/project/PROMPTS_CLAUDE_FIN_MVP.md) qui reliste `sia4010_classes_1a_1b.json` en source de vérité. Aligner en pointant `sia4010_all_classes.json`. |
| [docs/project/OPEN_ITEMS_BACKLOG.md](docs/project/OPEN_ITEMS_BACKLOG.md) | Dernière entrée « Recently Closed » datée 2026-07-23. Prédate le gel des références (2026-08-06), le corrigendum Test 7 (2026-08-10), la clarification Streubereich (2026-08-10) et l'ensemble des launchers untracked (Hub, Evidence Wizard, Remediation Probe, Reference Model Setup, Test 1 One-Click / Campaign Status / Weather AB / Convective AB, Compare Weather Transports, Qualify APS Hour Convention). Nécessite une passe « Recently Closed 2026-08 » et une mise à jour de « Current High-Value Open Items ». |
| [docs/project/SIA4010_FULL_COMPLIANCE_ANALYSIS.md](docs/project/SIA4010_FULL_COMPLIANCE_ANALYSIS.md), [SIA3802_FULL_COMPLIANCE_GAP_AUDIT.md](docs/project/SIA3802_FULL_COMPLIANCE_GAP_AUDIT.md), [WAITING_FOR_OFFICIAL_EXCEL_ACTION_PLAN.md](docs/project/WAITING_FOR_OFFICIAL_EXCEL_ACTION_PLAN.md), [SIA4010_OFFICIAL_PACKAGE_ACQUISITION_CHECKLIST.md](docs/project/SIA4010_OFFICIAL_PACKAGE_ACQUISITION_CHECKLIST.md) | Rédigés avant l'arrivée du paquet officiel SIA (les 55 fichiers listés dans [`SIA_4010_geteilter_Link/official_manifest.json`](SIA_4010_geteilter_Link/official_manifest.json) sont désormais présents localement). Leur portée « à faire pour obtenir le paquet » est superseded. Le classeur Test 7 pré-correction est en `sia4010_evidence/superseded_sources/`. |
| [docs/project/SIA4010_PDF_PREVALIDATION_STRATEGY.md](docs/project/SIA4010_PDF_PREVALIDATION_STRATEGY.md) | Stratégie « préqualification depuis les seuls PDF » élaborée avant réception des classeurs. Depuis, les valeurs sont extraites et FIGÉES depuis les xlsx officiels dans `refs/reference-data/*.json` (statut `FIGÉ — bandes recalculées et confrontées au classeur`). Le mécanisme de préqualification PDF reste utilisable comme filet, mais n'est plus la voie principale. |
| [docs/project/SIA4010_CASE600_MVP_DEMO.md](docs/project/SIA4010_CASE600_MVP_DEMO.md), [SIA4010_TEST1_SIX_CASES_EXECUTION_GUIDE.md](docs/project/SIA4010_TEST1_SIX_CASES_EXECUTION_GUIDE.md) | À vérifier ligne par ligne contre l'actuel `case_registry.py` et `sia4010_case_evidence.json` : la nomenclature de statut a évolué (`GUARDED_MUTATION_READY` / `RUNTIME_QUALIFICATION_READY`) et le contenu APS de `test_1/600` est désormais consigné dans l'autonomy ledger. |
| [docs/project/SIA_COMPLIANCE_MATRIX.md](docs/project/SIA_COMPLIANCE_MATRIX.md) | Matrice conformité SIA 380/2 antérieure au moteur SIA 4010 par cas et à la distinction claire entre readiness et validation. Le présent document (`MVP_COMPLETION_MATRIX.md`) prend le relais **côté MVP** ; l'ancienne matrice reste consultable pour l'axe 380/2 fin. |

**Ce qui n'est PAS obsolète et reste source de vérité machine-lisible** :
- [config/sia4010_all_classes.json](config/sia4010_all_classes.json) — 8 classes × 24 variantes × cas.
- [config/sia4010_official_input_contract.json](config/sia4010_official_input_contract.json) — inputs officiels confirmés par test.
- [config/iso52016_chapter7_confirmed_inputs.json](config/iso52016_chapter7_confirmed_inputs.json) — Test 1 climat + géométrie.
- [SIA_4010_geteilter_Link/official_manifest.json](SIA_4010_geteilter_Link/official_manifest.json) — 55 fichiers officiels SIA 4010 avec SHA-256.
- Tous les JSON sous `refs/reference-data/` datés du 2026-08-06 ou 2026-08-10.
- Trois preuves d'autorité du 2026-08-10 (voir §11).

---

## 13. Ordre de bataille suggéré pour clore le MVP

Cet ordre n'est pas prescriptif ; il découle des dépendances externes / internes visibles ci-dessus.

1. **Envoyer les deux brouillons courriers SIA** (`2026-08-07-questions-sia4010-EN.md` et `2026-08-10-donnees-sia-2028-EN.md`) après vérification Johan sur la licence IES SIA 2028. Sans réponse, Tests 2-7 restent bloqués.
2. **Aligner les statuts critères dans `refs/reference-data/`** : `test-2.ref.json`, `test-3.ref.json`, `test-5.ref.json` portent `INFERE` alors que le moteur les catégorise `ENONCE_DANS_LA_SPEC`. Corriger le producteur (script sous `scripts/`), pas le fichier de sortie.
3. **Exécuter les 5 runtime-probes Test 1** (`640, 600FF, 900, 940, 900FF`) dans un projet VE 2025 jetable, ce qui ne dépend d'aucune réponse SIA (climat DRYCOLD Denver disponible).
4. **Mettre à jour `SIA3802_SIA4010_IMPLEMENTATION_STATUS.md` et `OPEN_ITEMS_BACKLOG.md`** pour incorporer la surface untracked (Hub, Evidence Wizard, Remediation Probe, Reference Model Setup, Hour Convention, Test 1 Campaign) et les 3 preuves d'autorité 2026-08-10.
5. **Aligner `SIA_MODEL_BUILDER_GUIDE.md` et `PROMPTS_CLAUDE_FIN_MVP.md`** sur `config/sia4010_all_classes.json` comme unique source de vérité de la matrice classes/variantes/cas.
6. **Sous réserve des points 1 et 3**, implémenter dans l'ordre : Test 2A (a le bundle source), puis Test 3, puis Test 5, puis Tests 4/6, puis Test 7.

*Fin de matrice. Toute cellule signalée `TO VERIFY` ou toute nouvelle réponse SIA doit être répercutée ici en même temps que dans le producteur de référence correspondant.*
