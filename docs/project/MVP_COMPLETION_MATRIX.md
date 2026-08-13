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
| `BLOCKED_BY_EXTERNAL_EVIDENCE` | Bloqué par une donnée externe non fournie (licence, réponse SIA en attente, valeur non énoncée par la source). Le climat SIA 2028 n'en fait plus partie : il est reçu, converti, validé et lié depuis le 2026-08-12. |

Aucune ligne ne peut porter `PASS` / `VALIDATED` : la validation SIA 4010 est un acte réservé à la sous-commission SIA (SIA 4010:2023 §4.6.2).

---

## 1. SIA 4010 — Test 1 (7 cas, dont 1E)

La spécification du Test 1 énonce ses propres critères ([`Spezifikation_Test1.pdf`, section Testkriterien] cité verbatim dans [engine/test1_engine.py:14-25](engine/test1_engine.py)). ~~Test 1 est le **seul** test dans ce cas.~~ **Faux, corrigé le 2026-08-12** : recherche plein texte dans les sept spécifications — la section `Testkriterien` existe aussi dans `Spezifikation_Test2.pdf` (p. 2/2), `Test3.pdf` (p. 3/3) et `Test5.pdf` (p. 5/5), et y énonce la bande annuelle **et** le critère de distribution. Elle est absente des specs des Tests 4 et 6 (zéro occurrence), et aucun des sept **classeurs** ne contient ce mot — la section n'appartient qu'aux spécifications. Cette croyance erronée s'était propagée dans les cinq références figées, dans le producteur et dans l'interface ; voir les notes de résolution aux §2, 3 et 5. Le cas **1E** est le seul avec verdict pass/fail (Streubereich sur 4 programmes de référence). Les six autres cas sont explicitement **sans critère** — l'engine produit un delta informatif par programme. Météo = ISO 52016-1 DRYCOLD (Denver Stapleton) ; **pas SIA 2028**. Le fichier météo est fourni et audité ([`refs/reference-data/iso-52016-1-climat-drycold.json`](refs/reference-data/iso-52016-1-climat-drycold.json)).

| Cas | Exigence + source | Implémentation Python | Test Python | Générateur VE (état) | APS enregistré (ce projet) | Critère officiel | Statut | Prochain geste minimal |
|---|---|---|---|---|---|---|---|---|
| **1E** *(diagnostique)* | Streubereich pass/fail sur 4 programmes. Source : `Spezifikation_Test1.pdf` Testkriterien | [engine/test1_engine.py](engine/test1_engine.py) — `CAS_AVEC_CRITERE=('1E',)`, `evaluer_periode_1e` | [engine/tests/test_test1_engine.py](engine/tests/test_test1_engine.py) + `test_ref_integrity.py` | `NOT_IMPLEMENTED` — pas de branche dédiée dans [swiss_sia/reference_model/sia4010/case_registry.py:222-286](swiss_sia/reference_model/sia4010/case_registry.py); autonomy JSON confirme `mutation=False, runtime_qual=False` | Non | ÉNONCÉ (spec Test 1) ; référence FIGÉE dans [`refs/reference-data/test-1.ref.json`](refs/reference-data/test-1.ref.json) `CORRECTED_PASS_4` | `IMPLEMENTED_UNQUALIFIED` | **Chaîne de cinq maillons, désormais FIGÉE** dans [`refs/reference-data/test-1.diagnostics.ref.json`](refs/reference-data/test-1.diagnostics.ref.json) (producteur : [scripts/build_test1_diagnostics_reference.py](scripts/build_test1_diagnostics_reference.py), 43 champs relevés et 0 à confirmer (recompté sur le fichier le 2026-08-13), SHA-256 des trois PDF sources). La spec écrit : 1A = cas 600 + climat Zürich-Kloten ; 1B = +nouvelle fenêtre ; 1C = +infiltration **0,15 m³/(h·m²)** ; 1D = +usage SIA 2024 catégorie **3.1 Einzel-Gruppenbüro** ; 1E = +store **Soltis 92-2048-Alu** (SergeFerrari), fermé à **150 W/m²**, lame d'air 1 cm. Fenêtre entière relevée store rentré/déployé (EN ISO 52022-3 été et référence, EN 410) : g<sub>tot</sub> 0,545 → 0,059. **SIA 2024 ne bloque PAS** : la catégorie exigée est exactement celle de l'extrait d'autorité du 2026-08-10 que nous détenons. ~~Reste à faire : enregistrer 1A-1D, lier l'usage, générer.~~ **Fait le 2026-08-13** : 1A à 1D sont enregistrés, générables et évaluables (voir la note sous ce tableau). Seul **1E** reste bloqué, et sur un seul point — la dynamique du store, demande S2 au SIA. Son dispositif et ses propriétés optiques sont figés ; c'est la règle de commande qui manque |
| **600** *(6 cas normatifs — sans critère)* | Comparaison informative aux programmes de référence. Source : Testkriterien ("Es gibt dafuer kein Abweichungskriterium") | [engine/test1_engine.py](engine/test1_engine.py) — `comparer_periode_informative` | Idem 1E | `GUARDED_MUTATION_READY` — [case_registry.py:222](swiss_sia/reference_model/sia4010/case_registry.py) branche `case600_mvp_v1` ; APS réel et évaluation présents dans `sia4010_evidence/autonomy/sia4010_case_evidence.json` | **Oui, mais pré-correction** : `switzerland\test1_600\Vista\SIA4010_test_1_600_20260809_235015.aps`, `observed_metric_count=88`, `simulation_link_status=VERIFIED` — du 2026-08-09, donc **antérieur** à `c7e906b` (2026-08-12 12:55). Base de référence, non citable comme résultat | Aucun critère (par spec) | `RESULTS_RECORDED_NO_CRITERION` | Requalifier après la correction ventilation, puis **verrouiller** le pipeline 600 comme référence de non-régression |
| **640** | Informatif (idem 600) | Idem | Idem | `RUNTIME_QUALIFICATION_READY` — generator `test1_lightweight_runtime_probe_v1` ; blocker `VE_RUNTIME_QUALIFICATION_REQUIRED` | **Oui, mais pré-correction** : APS `…_640_20260811_234852.aps`, du 2026-08-11, donc **antérieur** au commit de correction `c7e906b` (2026-08-12 12:55). `result_evidence = REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION`, mais c'est une **base de référence à requalifier**, pas une preuve citable | Aucun | `READY_FOR_REAL_VE` | Requalifier (runtime inputs + ApacheSim + nouvel APS) comme fait pour 600FF le 2026-08-12 |
| **900** | Informatif (idem 600, haute masse) | Idem | Idem | `RUNTIME_QUALIFICATION_READY` — generator `test1_heavyweight_runtime_probe_v1`. **Rien à écrire** : [native_ui.py:242](swiss_sia/reference_model/sia4010/native_ui.py) route déjà 900/940/900FF vers `build_test1_runtime_probe_bundle`, et [test1_variant_bundle.py:277](swiss_sia/reference_model/sia4010/test1_variant_bundle.py) applique l'enveloppe haute masse Table 24. Le ledger porte déjà une géométrie `VERIFIED` (`SIA4010_test_1_900.gbxml`) | Non | Aucun | `READY_FOR_REAL_VE` | Créer un projet VE neuf **sauvegardé dans un dossier nommé `..._TEST1_900`** (le cas est déduit du nom du dossier, [Fast_Start:111-119](Run_VE_SIA4010_Test1_Fast_Start.py)) puis lancer Fast Start |
| **940** | Informatif | Idem | Idem | `RUNTIME_QUALIFICATION_READY` — heavyweight | Non | Aucun | `READY_FOR_REAL_VE` | Idem, dossier `..._TEST1_940` |
| **600FF** *(free-float)* | Informatif | Idem | Idem | `RUNTIME_QUALIFICATION_READY` — lightweight | **Oui, et POST-correction** — le seul cas dans cet état. Requalifié le 2026-08-12 : ventilation mécanique nulle vérifiée à zéro après read-back, infiltration prescrite 0,3075 `units_val=2` conservée séparément. APS `SIA4010_test_1_600FF_20260812_141823.aps`, sha256 `bcbb9deb…34f813`, 39 métriques ; entrée ledger écrite à 14:18:27 UTC, soit **après** le commit de correction `c7e906b` (12:55:25). Simulation exécutée, statut `SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION` | Aucun | `READY_FOR_REAL_VE` | Qualifier l'APS (dernière étape de la chaîne pour ce cas) |
| **900FF** | Informatif | Idem | Idem | `RUNTIME_QUALIFICATION_READY` — heavyweight | Non | Aucun | `READY_FOR_REAL_VE` | Idem, dossier `..._TEST1_900FF`. Le tri par longueur décroissante garantit que `900FF` est reconnu avant `900` |

**Cas diagnostiques 1A à 1D — enregistrés le 2026-08-12, exécutables depuis le 2026-08-13.** Ils manquaient au registre alors que 1E y était, ce qui laissait le seul cas jugé du Test 1 sans la base que sa définition exige.

Le blocage `TEST1_DIAGNOSTIC_CHAIN_GENERATOR_NOT_IMPLEMENTED` qu'ils portaient était **faux** : `test1_diagnostic_bundle` appliquait déjà les quatre maillons figés et rendait `READY_FOR_PROVISIONAL_RUNTIME_QUALIFICATION`. Ce qui manquait réellement était ailleurs, et a été fait :

| Manque réel | Correction |
|---|---|
| `config/sia4010_classes_1a_1b.json` ne déclarait pas les quatre cas ni leurs paramètres exacts | Quatre blocs ajoutés, dérivés maillon par maillon : 1A = 600 avec Kloten ; 1B = +vitrage Test 2 ; 1C = +infiltration Test 2 ; 1D = +usage SIA 2024. Les consignes restent `test1_*`, aucun maillon ne les modifie |
| Le rôle `zurich_kloten_dry_weather_file` restait `PLACEHOLDER_REQUIRED`, donc le préflight refusait la mutation | `_bind_kloten_case_manifest_role` le renseigne avec le chemin résolu et son empreinte, en statut `CONFIRMED` — pas `CONFIRMED_NORMATIVE`, qui affirmerait une relecture ligne à ligne inexistante |
| Aucun chemin d'évaluation APS : le chemin Test 1 compare aux résultats **ISO**, impossible ici (climat Kloten, et zéro référence dans `test-1.ref.json`) | Nouvelle portée `HOURLY_DELIVERABLE_ONLY_NO_REFERENCE` et branche dédiée qui enregistre le livrable **sans aucune comparaison** |
| `Run_VE_SIA4010_Test1_Fast_Start.py` avait une liste de cas en dur | Étendue aux quatre ; 1E reste dehors, sa dynamique de store n'est pas énoncée |

État : `RUNTIME_QUALIFICATION_READY`, générateur `test1_diagnostic_chain_probe_v1`, préflight `READY_FOR_VE_MUTATION` avec zéro paramètre manquant. Ils sont les **seuls** cas dont toutes les entrées sont `CONFIRMED` : leur climat vient du SIA, là où les six cas ISO tournent sur le DRYCOLD public.

### Un drapeau de conformité qui basculait sur la qualité des entrées

Ce sont ces quatre cas qui l'ont révélé. `ModelScenario.readiness` calculait `compliance_claim_allowed = is_official and not blockers and not provisional` : des entrées toutes confirmées suffisaient donc à autoriser une revendication de conformité. La formule n'était sûre que **par accident** — tous les cas portaient au moins une entrée `PUBLIC_REFERENCE` (le climat DRYCOLD), jusqu'au premier cas entièrement confirmé. Pour 1D, le scénario disait `True` pendant que son audit et son manifeste d'actifs disaient `False`.

Deux raisons indépendantes le rendaient faux : ces cas n'ont **aucun critère** auquel se conformer, et des entrées complètes ne disent rien d'un générateur qualifié, d'une simulation exécutée ni de l'attestation de la sous-commission (§4.6.2). Le champ est désormais **toujours** `False` dans un scénario, et le fait réellement établi est exposé sous son vrai nom, `official_inputs_fully_confirmed`.

| Cas | Champ d'évaluation APS | Entrées déléguées exigées | Statut |
|---|---|---|---|
| **1A** | `UNAVAILABLE` — aucun critère énoncé | cellule ISO + climat Kloten | bundle `READY_FOR_PROVISIONAL_RUNTIME_QUALIFICATION` |
| **1B** | `UNAVAILABLE` | idem 1A | idem |
| **1C** | `UNAVAILABLE` | + SIA 2024 (l'infiltration 0,15 en est tirée) | idem |
| **1D** | `UNAVAILABLE` | + SIA 2024 (usage) | idem |

**Générateur écrit et atteignable depuis VE (2026-08-13).** [test1_diagnostic_bundle.py](swiss_sia/reference_model/sia4010/test1_diagnostic_bundle.py) applique la chaîne cumulativement, chaque valeur relue dans le référentiel figé — le module ne porte aucune constante normative. `prepare_supported_mvp_bundle` route désormais les cinq cas ; sans ce câblage le générateur existait mais rien ne l'appelait, et préparer 1A produisait le repli générique en silence. Vérifié sur 1D : climat `Zurich-Kloten - SIA 2028 DRY normal`, infiltration 0,15, vitrage g 0,545 / Ug 0,654, appareils 11 W/m², éclairage 12,5 W/m², occupants 68,6 W/personne (4,9 W/m² × 14 m²).

Le fichier météo de Kloten est résolu **hors** du constructeur — projet, puis dossier Weather de VE, puis `generated_weather/KLO/` — parce que sa localisation dépend de la machine et qu'un constructeur dont le résultat en dépend n'est pas testable deux fois de la même façon. Introuvable, il **bloque** ; il ne laisse jamais le climat de Denver en place sous une étiquette Kloten.

**Point normatif à ne pas perdre** : la spécification exige pour 1A-1D des *jeux annuels de puissance horaire* et n'énonce **aucun critère de comparaison** — « Zu liefernde Resultate: Jahresdatensätze mit stündlicher Leistung Heizen und Kühlen ». `test-1.ref.json` ne porte donc aucune bande pour eux, et il ne faut pas en inventer : ce sont des **livrables**, pas des cas jugés. Seul 1E est jugé. Conséquence sur les compteurs : 30 → **34 cas exacts**, 8 classes et **24 variantes inchangées** — ce sont des cas de `test_1`, pas de nouvelles variantes.

**Incident diagnostiqué le 2026-08-12 — matériau CDB périmé, à ne pas rediagnostiquer.** Le run du cas 600 a échoué sur `VeMutationError: existing material xps_ground read-back mismatch: {'density': {'expected': 0.0, 'actual': 10.0}, 'specific_heat_capacity': {'expected': 0.0, 'actual': 1400.0}}`. Ce n'était **ni un défaut de code, ni une erreur de manifeste** : le garde-fou a correctement refusé de réutiliser un matériau CDB dont les valeurs stockées ne correspondaient plus. Chaîne de preuve : le manifeste local du projet déclare `xps_ground` à densité 0 / cp 0 (source NREL/TP-472-6231 BESTEST) ; la révision antérieure du même fichier, `reference_model_assets.pre_glazing_calibration.json`, déclarait 10,0 / 1400,0 sous la **même description** `SIA600_FLOOR_INSULATION`, et c'est elle qui a créé le matériau dans la CDB. L'autorité tranche : [config/iso52016_chapter7_confirmed_inputs.json](config/iso52016_chapter7_confirmed_inputs.json) donne pour la couche plancher `ideal_floor_insulation` densité 0, cp 0, capacité surfacique 0 ; les 10/1400 sont ceux de `foam_insulation`, l'isolation du **mur** lourd. Les deux partagent la conductivité 0,04, ce qui explique la confusion. **Résolution** : corriger le matériau dans la base de constructions VE (densité et chaleur spécifique à 0). VE persiste 1e-6 et `ve_field_policy.VE_THERMAL_MASS_MINIMUM` accepte déjà cette valeur canonique. Aucune valeur physique n'a été modifiée dans le dépôt.

**Note d'audit** : les paths locaux dans [`sia4010_evidence/autonomy/sia4010_case_evidence.json`](sia4010_evidence/autonomy/sia4010_case_evidence.json) pointent hors dépôt (`C:\...\switzerland\test1_600\...`). Seuls les entrées `test_1/600` ont été inspectées et portent réellement des artefacts vérifiés ; les 29 autres entrées portent la même structure de champs mais ne sont pas garantie d'artefacts persistés au même niveau — à confirmer par un audit d'existence de fichiers avant de citer.

---

## 2. SIA 4010 — Test 2 (4 cas)

Classe(s) concernée(s) : `1A` (cas 2A), `1B` (2B, 2C, 2D), `2A` (2A), `2B` (2B-2D), `4A` (2A), `4B` (2B-2D). Météo Kloten = **disponible et liée** : `KLO_dry.txt` porte les quatre colonnes solaires (global horizontal, somme annuelle 1 105 564 Wh/m² ; diffus horizontal ; direct normal ; infrarouge horizontal), plus le vertical sud. L'affirmation « bloqué par irradiance solaire manquante » qui figurait ici était fausse et n'avait jamais été vérifiée contre le fichier ; elle est corrigée le 2026-08-13. Critère : bande annuelle **+** distribution horaire ; réponse d'autorité `Streubereich = min/max des programmes` reçue le 2026-08-10 et intégrée à [engine/sia_distributions_engine.py:11-19](engine/sia_distributions_engine.py).

| Cas | Implémentation Python | Test Python | Générateur VE | APS enregistré | Critère officiel | Statut | Prochain geste minimal |
|---|---|---|---|---|---|---|---|
| **2A** | [engine/sia_bandes_engine.py](engine/sia_bandes_engine.py) + [engine/sia_distributions_engine.py](engine/sia_distributions_engine.py) ; source-traced bundle Test 2A dans [swiss_sia/reference_model/sia4010/test2a_source_bundle.py](swiss_sia/reference_model/sia4010/test2a_source_bundle.py) | `engine/tests/test_sia_bandes_engine.py`, `test_distributions_engine.py`, `test_references_bandes.py`, `test_distributions_ref.py`, `tests/test_sia4010_test2a_*` (10 fichiers) | `NOT_IMPLEMENTED` mutation ; `runtime_discovery_supported=True` + `source_bound_bundle_supported=True` ([case_registry.py:48-63](swiss_sia/reference_model/sia4010/case_registry.py)) | Non | Bande annuelle : `ENONCE_DANS_LA_SPEC` (moteur) ; distribution : `CONFIRME_AUTORITE_2026-08-10` ; référence FIGÉE [`refs/reference-data/test-2.ref.json`](refs/reference-data/test-2.ref.json) + [`test-2.distributions.ref.json`](refs/reference-data/test-2.distributions.ref.json) | `IMPLEMENTED_UNQUALIFIED` ; les trois entrées déléguées sont `READY_FOR_BINDING` et le bundle source se construit de bout en bout, statut `SOURCE_BINDINGS_PROVISIONAL_RECALCULATION_REQUIRED` avec `verdict_derivation_allowed: false` | Recalculer l'émissivité IR provisoire depuis ISO EN 52016-1 clauses 7.2.2.7-7.2.2.10 (registre point I1), fournir le graphe de profils VE natif, puis implémenter le générateur VE 2A |
| **2B** | Idem 2A | Idem | `NOT_IMPLEMENTED` | Non | Idem | Idem | Idem |
| **2C** | Idem | Idem | `NOT_IMPLEMENTED` | Non | Idem | Idem | Idem |
| **2D** | Idem | Idem | `NOT_IMPLEMENTED` | Non | Idem | Idem | Idem |

**Discordance résolue le 2026-08-12.** La référence figée portait `critere.statut = "INFERE"` alors que le moteur portait `ENONCE_DANS_LA_SPEC`. Tranché sur les PDF officiels et non par alignement d'un fichier sur l'autre : recherche plein texte dans `Spezifikation_Test2.pdf` — section « Testkriterien » **présente**, page 2/2, énonçant la bande annuelle mot pour mot. Le moteur avait raison ; le producteur `scripts/build_sia_reference.py` écrivait un `INFERE` uniforme et la phrase fausse « seul le Test 1 énonce ses critères dans sa spécification ». Références régénérées : seules les deux lignes du bloc `critere` changent, `grandeurs` identique au bit près. Le même texte faux s'affichait dans l'interface pour tous les tests à bandes ([verdict_view.py](ui/verdict_view.py)) — corrigé aussi. Garde-fou : [test_references_bandes.py](engine/tests/test_references_bandes.py) confronte désormais référence et moteur test par test, et échoue s'ils divergent. La référence reste volontairement indépendante du moteur : c'est la preuve contre laquelle il est jugé.

---

## 3. SIA 4010 — Test 3 (12 cas)

Classe(s) : `2A` (3A-3F), `2B` (3A-3L), `4A` (3A-3F), `4B` (3A-3L). ~~Météo Kloten = bloqué (SIA 2028 solaire).~~ **Climat reçu et installé le 2026-08-12** (voir §10).

**Probe runtime exécutée en VE 2025 réel le 2026-08-12** — première exécution de cette probe. Projet `ZOER_32_C1_TEST`, scénario `test_3A/3A` préparé par [Run_VE_SIA4010_Prepare_Case_Scenario.py](Run_VE_SIA4010_Prepare_Case_Scenario.py). Verdict `SOURCE_BINDINGS_REQUIRED` : **20 champs d'éclairage observés**, 4 membres liés aux capteurs, 12 variantes exactes auditées. Rapport `sia4010_artifacts/diagnostics/sia4010_test3_runtime_capability_20260812_170256.json`. Aucune donnée de modèle modifiée. Ce que cela établit : l'API VE expose bien la surface nécessaire ; ce qui manque n'est pas une capacité VE mais les **liaisons de sources externes** (SIA 2024 notamment). Ce n'est ni une validation ni une revendication de conformité.

| Cas | Implémentation Python | Test Python | Générateur VE | APS enregistré | Critère officiel | Statut | Prochain geste minimal |
|---|---|---|---|---|---|---|---|
| **3A**..**3L** (12 cas) | `sia_bandes_engine.py` + `sia_distributions_engine.py` ; bundle Test 3 dans [test3_source_bundle.py](swiss_sia/reference_model/sia4010/test3_source_bundle.py), runtime probe dans [test3_runtime_capability.py](swiss_sia/reference_model/sia4010/test3_runtime_capability.py) | `engine/tests/test_sia_bandes_engine.py` (`(3, 12)`), `test_distributions_engine.py`, `test_references_bandes.py`, `tests/test_sia4010_test3_*` (3 fichiers) | `NOT_IMPLEMENTED` mutation ; `runtime_discovery_supported=True` + `source_bound_bundle_supported=True` | Non | Bande annuelle : `ENONCE_DANS_LA_SPEC` ; distribution : `CONFIRME_AUTORITE_2026-08-10` ; référence FIGÉE dans [`refs/reference-data/test-3.ref.json`](refs/reference-data/test-3.ref.json) (12 cas) + [`test-3.distributions.ref.json`](refs/reference-data/test-3.distributions.ref.json) (12 individuels + 4 agrégats A-F, G-H, I-J, K-L) | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` | Générateur VE Test 3 (éclairage + apports internes + facteurs de contrôle) — le climat n'est plus un bloqueur |

**Discordance résolue le 2026-08-12.** La référence figée portait `critere.statut = "INFERE"` alors que le moteur portait `ENONCE_DANS_LA_SPEC`. Tranché sur les PDF officiels et non par alignement d'un fichier sur l'autre : recherche plein texte dans `Spezifikation_Test3.pdf` — section « Testkriterien » **présente**, page 3/3, énonçant la bande annuelle mot pour mot. Le moteur avait raison ; le producteur `scripts/build_sia_reference.py` écrivait un `INFERE` uniforme et la phrase fausse « seul le Test 1 énonce ses critères dans sa spécification ». Références régénérées : seules les deux lignes du bloc `critere` changent, `grandeurs` identique au bit près. Le même texte faux s'affichait dans l'interface pour tous les tests à bandes ([verdict_view.py](ui/verdict_view.py)) — corrigé aussi. Garde-fou : [test_references_bandes.py](engine/tests/test_references_bandes.py) confronte désormais référence et moteur test par test, et échoue s'ils divergent. La référence reste volontairement indépendante du moteur : c'est la preuve contre laquelle il est jugé.

---

## 4. SIA 4010 — Test 4 (1 cas)

Classe(s) : `3`, `4A`, `4B`. **Pas de section Testkriterien** dans `Spezifikation_Test4.pdf` — question 3 du courriel du 2026-08-07 (brouillon non envoyé) reste ouverte. Météo Kloten = bloqué solaire.

**Probe runtime Tests 4-7 exécutée en VE 2025 réel le 2026-08-12** — première exécution. Projet `ZOER_32_C1_TEST`, scénarios `test_4/4` puis `test_7/7` préparés par [Run_VE_SIA4010_Prepare_Case_Scenario.py](Run_VE_SIA4010_Prepare_Case_Scenario.py). Verdict `SOURCE_BINDINGS_REQUIRED` pour les deux : collection de systèmes Apache observée, read-back système par pièce observé, **29 membres spécifiques aux centrales**, 7 cas exacts audités. Rapports sous `sia4010_artifacts/diagnostics/sia4010_tests4_7_runtime_capability_20260812_170438.json` et `..._170514.json`. Aucune donnée de modèle modifiee. Ce que cela etablit : la surface ApacheHVAC necessaire est presente dans VE ; le blocage restant est la liaison des sources externes et le critere de distribution, pas une capacite VE manquante.

| Cas | Implémentation Python | Test Python | Générateur VE | APS | Critère officiel | Statut | Prochain geste |
|---|---|---|---|---|---|---|---|
| **4** | `engine/sia_bandes_engine.py` (bande annuelle uniquement — pas de distribution : `TESTS_SUPPORTES=(2,3,5)`) ; consignes de température FIGÉES dans [`refs/reference-data/test-4.consignes.json`](refs/reference-data/test-4.consignes.json) | `engine/tests/test_references_bandes.py` (`(4, 3, 3)`), `test_construire_test4.py` (script hors moteur) | `NOT_IMPLEMENTED` — blocker `VE_HEATING_COOLING_SETPOINT_BINDING_NOT_IMPLEMENTED` ([case_registry.py](swiss_sia/reference_model/sia4010/case_registry.py)) | Non | `INFERE` (SIA 4010 §4.4 délègue au classeur) ; référence FIGÉE [`refs/reference-data/test-4.ref.json`](refs/reference-data/test-4.ref.json) 3 grandeurs | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` | (a) Envoyer le courriel 2026-08-07 pour confirmer le critère bande annuelle seul ; (b) implémenter le générateur VE (chauffage/rafraîchissement + courbe de consigne SIA 380/2 fig. 1) |

---

## 5. SIA 4010 — Test 5 (4 cas)

Classe(s) : `3`, `4A`, `4B`. Nomenclature effective **5A, 5B, 5C, 5D** — les identifiants « 5.1..5.4 » n'existent nulle part dans le dépôt.

| Cas | Implémentation Python | Test Python | Générateur VE | APS | Critère | Statut | Prochain geste |
|---|---|---|---|---|---|---|---|
| **5A**..**5D** (4 cas) | `sia_bandes_engine.py` + `sia_distributions_engine.py` ; réseau ventilation figé dans [`refs/reference-data/test-5.reseau.json`](refs/reference-data/test-5.reseau.json) (statuts `RELEVE/A_CONFIRMER/RELEVE_SUR_GRAPHIQUE`) | `engine/tests/test_references_bandes.py` (`(5, 8, 16)`), `test_distributions_engine.py`, `test_reseau_ventilation.py` | `NOT_IMPLEMENTED` — blocker `VE_MECHANICAL_VENTILATION_BINDING_NOT_IMPLEMENTED` | Non | Bande annuelle : `ENONCE_DANS_LA_SPEC` (moteur) ; distribution : `CONFIRME_AUTORITE_2026-08-10` ; FIGÉE [`refs/reference-data/test-5.ref.json`](refs/reference-data/test-5.ref.json) (16 lignes grandeur×cas) + [`test-5.distributions.ref.json`](refs/reference-data/test-5.distributions.ref.json) (16 distributions ; 1 sans `cas` — réserve documentée dans la ref) | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` | Implémenter les liaisons ApacheHVAC (récupérateur, batteries, humidificateur) ; qualifier avec probe dédiée `test4_7_runtime_capability_probe` |

**Discordance résolue le 2026-08-12.** La référence figée portait `critere.statut = "INFERE"` alors que le moteur portait `ENONCE_DANS_LA_SPEC`. Tranché sur les PDF officiels et non par alignement d'un fichier sur l'autre : recherche plein texte dans `Spezifikation_Test5.pdf` — section « Testkriterien » **présente**, page 5/5, énonçant la bande annuelle mot pour mot. Le moteur avait raison ; le producteur `scripts/build_sia_reference.py` écrivait un `INFERE` uniforme et la phrase fausse « seul le Test 1 énonce ses critères dans sa spécification ». Références régénérées : seules les deux lignes du bloc `critere` changent, `grandeurs` identique au bit près. Le même texte faux s'affichait dans l'interface pour tous les tests à bandes ([verdict_view.py](ui/verdict_view.py)) — corrigé aussi. Garde-fou : [test_references_bandes.py](engine/tests/test_references_bandes.py) confronte désormais référence et moteur test par test, et échoue s'ils divergent. La référence reste volontairement indépendante du moteur : c'est la preuve contre laquelle il est jugé.
**Réserve documentée** : une distribution T5 n'a pas de libellé `cas` dans le classeur ; la réserve figure dans le JSON, ne pas la « corriger » silencieusement.

---

## 6. SIA 4010 — Test 6 (1 cas)

Classe(s) : `3`, `4A`, `4B`. Pas de section Testkriterien (idem Test 4 — question 3 du courriel 2026-08-07 ouverte).

| Cas | Implémentation Python | Test Python | Générateur VE | APS | Critère | Statut | Prochain geste |
|---|---|---|---|---|---|---|---|
| **6** | `sia_bandes_engine.py` (bande annuelle seule) ; réseau figé [`refs/reference-data/test-6.reseau.json`](refs/reference-data/test-6.reseau.json) | `engine/tests/test_references_bandes.py` (`(6, 6, 6)`), `test_reseau_ventilation.py` | `NOT_IMPLEMENTED` — blocker `VE_HVAC_HYDRAULIC_BINDING_NOT_IMPLEMENTED` | Non | `INFERE` ; référence FIGÉE [`refs/reference-data/test-6.ref.json`](refs/reference-data/test-6.ref.json) 6 grandeurs | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` | (a) Confirmer critère bande annuelle seule via SIA ; (b) implémenter le générateur VE (réseau + circuit hydraulique) |

---

## 7. SIA 4010 — Test 7 (1 cas)

Classe(s) : `4A`, `4B`, `5` (Test 7 est le seul test de la classe `5`). PV + machine frigorifique + réseau.

| Cas | Implémentation Python | Test Python | Générateur VE | APS | Critère | Statut | Prochain geste |
|---|---|---|---|---|---|---|---|
| **7** | [engine/test7_engine.py](engine/test7_engine.py) — moteur dédié 11 bandes (5 froid + 5 chaud + 1 PV), Testgrössen vs Diagnosegrössen, verrou PV/irradiance | `engine/tests/test_test7_engine.py`, `test_references_bandes.py`, `scripts/build_test7_reference.py` | `NOT_IMPLEMENTED` — blocker `VE_ENERGY_SYSTEM_BINDING_NOT_IMPLEMENTED` | Non | `INFERE` au sens spec (pas de Testkriterien) **mais** classeur officiel corrigé par SIA le 2026-08-10 (règle conditionnelle L8→N8) et audit consigné [`sia4010_evidence/source_audits/test7-corrected-workbook-20260810.json`](sia4010_evidence/source_audits/test7-corrected-workbook-20260810.json) : `VERIFIED_CORRECTION_READY_FOR_TEST7_EVALUATION`. Référence FIGÉE [`refs/reference-data/test-7.ref.json`](refs/reference-data/test-7.ref.json) daté 2026-08-10 (11 grandeurs, bandes numériquement identiques après correction) | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` | Implémenter la chaîne émission/distribution/stockage/génération VE ; extraire les 11 grandeurs annuelles depuis APS |

---

## 8. SIA 4010 — vue par classe de validation

Résumé exécutif dérivé de [`config/sia4010_all_classes.json`](config/sia4010_all_classes.json). Une classe n'est jamais « validée » sans attestation de la sous-commission — la colonne « État » synthétise uniquement la couverture logicielle.

| Classe | Variantes exigées | Cas VE exécutés | Générateurs VE prêts | État global |
|---|---|---|---|---|
| **1A** | `test_1` + `test_2A` | 1 sur 8 (T1/600) | 6/8 (T1/600 mutation + 5 T1 runtime-probe) | Partiel : Test 1 avance ; Test 2A a ses trois entrées liées, reste le générateur VE et l'émissivité à recalculer |
| **1B** | `test_1` + `test_2B..2D` | 1 sur 10 | 6/10 | Idem |
| **2A** | `test_1` + `test_2A` + `test_3A..3F` | 1 sur 14 | 6/14 | Entrées déléguées liées ; générateurs VE 2A et 3x à implémenter |
| **2B** | `test_1` + `test_2B..2D` + `test_3A..3L` | 1 sur 22 | 6/22 | Idem |
| **3** | `test_1` + `test_4` + `test_5A..5D` + `test_6` | 1 sur 13 | 6/13 | Testkriterien 4/6 ouverts (demande S1) ; générateurs VE 4/5/6 à implémenter |
| **4A** | 15 variantes | 1 sur 21 | 6/21 | Test 7 attend la chaîne systèmes énergétiques |
| **4B** | 23 variantes | 1 sur 30 | 6/30 | Idem |
| **5** | `test_7` | 0 sur 1 | 0/1 | Test 7 attend la chaîne systèmes énergétiques (émission, distribution, stockage, génération) |

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
| **Émissivité IR de la cellule ISO chapitre 7** | Une valeur provisoire 0,90 rend le Test 2A générable mais non jugeable : bloqueur `DELEGATED_INPUT_CARRIES_PROVISIONAL_VALUE`, `verdict_derivation_allowed: false` | Répondable **en interne** depuis la copie licenciée d'ISO EN 52016-1:2017, clauses 7.2.2.7 à 7.2.2.10 — voir [`REGISTRE_DEMANDES_EXTERNES.md`](docs/project/REGISTRE_DEMANDES_EXTERNES.md) point I1 | Interne, à la charge d'Ulysse |

### Deux bloqueurs qui n'existaient pas

Consignés parce que les deux auraient été présentés comme réels en démonstration.

1. **« Météo Kloten bloquée par irradiance solaire manquante »** — faux. `KLO_dry.txt`
   porte les quatre colonnes solaires : global horizontal (somme annuelle
   1 105 564 Wh/m²), diffus horizontal, direct normal, infrarouge horizontal,
   plus le vertical sud. Le bloqueur avait été levé pour le Test 3 le 2026-08-12
   mais la mention subsistait à **douze** autres endroits de ce document —
   lignes 20, 67, 84, 98, 108, 121, 131, 141, 143, 145, 146, 148 — dont la
   légende du vocabulaire de statut elle-même. Corrigé partout le 2026-08-13.
2. **« Coefficient de surface intérieur non énoncé par la source »** — faux
   également, et de mon fait cette fois. La source donne les trois coefficients
   par orientation ; c'était le contrat normalisé qui les aplatissait. Corrigé en
   étendant le contrat, pas en déclarant une valeur provisoire.

Les deux partagent la même cause que les erreurs précédentes de ce projet :
conclure d'une comparaison sans vérifier qu'elle portait sur le bon objet.

### Deux défauts de chaîne de preuve, dans mon propre travail du 2026-08-13

Aucun des deux n'aurait été visible sur cette machine : les deux ne cassaient que
sur un autre clone, c'est-à-dire au moment de la revue par un tiers.

| Défaut | Ce qui se serait passé | Correction |
|---|---|---|
| L'artefact de liaison météo avait été écrit dans `generated_weather/`, exclu par `.gitignore:276` | Sur un clone frais, le Test 2A échouait sur `binding artifact is unavailable` — la liaison n'était pas dans le dépôt | Déplacé dans `references/standards/sia2028/`, avec le rapport et la source. Producteur reproductible ajouté : [scripts/build_sia2028_kloten_binding.py](scripts/build_sia2028_kloten_binding.py) — il était écrit à la main |
| Les quatre artefacts portaient des chemins absolus contenant le nom d'utilisateur, là où les références déjà suivies en portent **zéro** | Irrésolvables sur toute autre machine | Chemins relatifs partout. Le lecteur résout la liaison relativement au **rapport** et l'EPW relativement à la **liaison** : le relatif est donc la forme exacte, pas un pis-aller |

L'EPW lui-même reste hors du dépôt, et c'est la convention voulue
(`.gitignore` : artefacts dérivés régénérables). La liaison le déclare désormais
explicitement, avec la commande qui le régénère, au lieu de laisser découvrir un
fichier manquant.

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
