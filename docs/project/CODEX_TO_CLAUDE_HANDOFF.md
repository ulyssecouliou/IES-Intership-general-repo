# Passation Codex vers Claude — SIA 380/2 et SIA 4010

**Date de l'état :** 2026-08-12  
**Dépôt :** `C:\Users\ulysse.couliou\Documents\IES Internship\IES-Intership-general-repo`  
**Branche observée :** `main`  
**HEAD observé :** `26ff677ab30c9be006f6d84f1a69f9b6197afe5f`  
**Environnement VE réel :** IESVE 2025, Python VE 3.12.3  
**Environnement des tests locaux de cette passation :** Python 3.13

## 1. Mission et limite de la revendication

Le produit visé est un ensemble de VEScripts exécutables dans IESVE qui :

1. extrait et contrôle un modèle client pour préparer une évaluation SIA 380/2:2022 ;
2. crée, qualifie, simule et compare les cas de validation SIA 4010:2023 ;
3. produit des preuves auditables JSON/Excel/PDF ;
4. échoue de manière conservative lorsqu'une valeur normative, une liaison VE ou une preuve manque.

Le logiciel produit actuellement des diagnostics, des contrôles de readiness et des résultats de référence. Il ne doit jamais présenter un modèle comme certifié ou officiellement validé par la SIA sans critères applicables, dossier de preuves complet, revue indépendante et attestation prévue par la procédure SIA.

## 2. Règles absolues pour la reprise

- Lire d'abord `CLAUDE.md`, puis `docs/CLAUDE_REFERENCE.md`.
- Ne jamais inventer une valeur réglementaire, climatique, physique, une tolérance ou une signature `iesve`.
- Une donnée manquante reste `NOT_CHECKABLE`, `WARNING` ou `FAIL`, jamais `PASS`.
- Ne pas confondre le climat des tests SIA 4010 avec le climat d'application d'un projet suisse SIA 380/2.
- Toute mutation VE doit être précédée d'un capability check et suivie d'un read-back.
- Les tests avec doubles Python ne remplacent pas une qualification dans IESVE 2025.
- Ne jamais modifier directement un JSON figé sous `refs/reference-data/` : modifier son producteur puis le régénérer.
- Ne pas lancer `git reset`, `git checkout --`, un nettoyage massif ou une réécriture générale.
- Ne pas publier, pousser, ouvrir une PR ou transmettre des documents sous licence sans autorisation explicite.

## 3. État Git à préserver

> **Mise à jour 2026-08-12.** Cette section décrivait 168 entrées non propres.
> Ce n'est plus l'état : ce travail a été regroupé en commits sur la branche
> `sia4010-evidence-hardening-20260812`, et `main` reste intact. La règle qui
> suit demeure valable pour toute reprise ultérieure — il faut relire
> `git status --short` au lieu de se fier à un décompte figé dans un document.

Règle permanente : les changements non commités appartiennent à l'utilisateur et
regroupent plusieurs jours de développement Codex/Claude. Inspecter
`git status --short` et des diffs ciblés avant toute modification, puis
conserver tous les changements sans rapport avec la tâche en cours. Un diff
volumineux n'est pas une invitation à reformater le dépôt : un seul fichier
météo EPW pèse 8 760 lignes.

## 4. Ordre de lecture recommandé

### Doctrine et architecture

1. `CLAUDE.md`
2. `docs/CLAUDE_REFERENCE.md`
3. le présent fichier
4. `README.md`
5. `docs/project/MVP_COMPLETION_MATRIX.md`
6. `docs/project/HYBRID_EXECUTION_STATUS_20260811.md`
7. `docs/project/TONIGHT_SIA4010_EXECUTION_RUNBOOK_FR.md`

### Sources de vérité machine-readable

1. `config/sia4010_all_classes.json`
2. `config/sia4010_official_input_contract.json`
3. `config/iso52016_chapter7_confirmed_inputs.json`
4. `SIA_4010_geteilter_Link/official_manifest.json`
5. `refs/reference-data/*.json`
6. `sia4010_evidence/autonomy/sia4010_case_evidence.json`

### Chaîne Test 1 active

1. `Run_VE_SIA4010_Test1_Fast_Start.py`
2. `Run_VE_SIA4010_Test1_Active_Case_One_Click.py`
3. `Run_VE_SIA4010_Test1_Qualify_Runtime_Inputs.py`
4. `Run_VE_SIA4010_Simulate_Active_Case.py`
5. `swiss_sia/reference_model/sia4010/mvp_bundle.py`
6. `swiss_sia/reference_model/sia4010/test1_variant_bundle.py`
7. `swiss_sia/reference_model/sia4010/test1_runtime_inputs.py`
8. `swiss_sia/reference_model/sia4010/apachesim_qualification.py`
9. `swiss_sia/reference_model/sia4010/active_case_evaluation.py`
10. tests homonymes sous `tests/`

## 5. État vérifié de la campagne SIA 4010 Test 1

Le ledger central `sia4010_evidence/autonomy/sia4010_case_evidence.json`, mis à jour le 2026-08-12 à 07:49 UTC, contient :

| Cas | Modèle | Simulation enregistrée | Évaluation APS | Métriques | Portée de sortie |
| --- | --- | --- | --- | ---: | --- |
| `test_1/600` | `VERIFIED` | enregistrée | `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION` | 88 | complète |
| `test_1/640` | `VERIFIED` | enregistrée | `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION` | 88 | complète |
| `test_1/600FF` | `VERIFIED` | enregistrée | `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION` | 39 | complète |
| `test_1/900` | manquant | non lancée | `NOT_CHECKABLE` | — | — |
| `test_1/940` | manquant | non lancée | `NOT_CHECKABLE` | — | — |
| `test_1/900FF` | manquant | non lancée | `NOT_CHECKABLE` | — | — |

Projets et dernières preuves enregistrées :

- 600 : `C:\Users\ulysse.couliou\Documents\switzerland\test1_600`
- 640 : `C:\Users\ulysse.couliou\Documents\switzerland\Test_640_Test1`
- 600FF : `C:\Users\ulysse.couliou\Documents\switzerland\SIA4010_TEST1_600FF`

Le statut `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION` est intentionnel. Les sources ISO disponibles donnent des résultats de référence pour le Test 1, mais aucune bande de décision démontrée dans le projet. Ne pas le convertir en `PASS`.

## 6. Dernière correction en cours — ventilation mécanique du Test 1

Une anomalie a été identifiée après les simulations ci-dessus : le template générique VE pouvait conserver `system_air_minimum_flowrate = 10 L/s/person`, alors que le Test 1 ISO ne comporte aucune ventilation mécanique ; seule l'infiltration prescrite doit rester active.

La correction actuelle :

- force le débit minimal système à `0.0` ;
- désactive l'héritage du template ;
- vérifie le read-back dans la qualification runtime ;
- bloque ApacheSim si la preuve ou l'état VE réel n'est plus nul ;
- conserve l'infiltration séparée à 0,41 ACH, soit environ 14,76 L/s pour le local de 129,6 m³.

Fichiers centraux modifiés :

- `swiss_sia/reference_model/sia4010/mvp_bundle.py`
- `swiss_sia/reference_model/sia4010/test1_runtime_inputs.py`
- `Run_VE_SIA4010_Test1_Qualify_Runtime_Inputs.py`
- `swiss_sia/reference_model/sia4010/apachesim_qualification.py`
- `tests/test_sia4010_mvp_bundle.py`
- `tests/test_sia4010_test1_runtime_inputs.py`
- `tests/test_sia4010_apachesim_qualification.py`

Vérification locale effectuée lors de cette passation :

```text
python -m pytest -q tests/test_sia4010_mvp_bundle.py \
  tests/test_sia4010_test1_runtime_inputs.py \
  tests/test_sia4010_apachesim_qualification.py

31 passed
```

La correction n'a pas encore été requalifiée par un nouveau run VE consigné après sa dernière modification. Les APS existants des cas 600, 640 et 600FF sont donc des baselines techniques, pas des preuves finales de cette correction.

## 7. Prochaine action exacte dans IESVE

> **Mise à jour 2026-08-12 — cette priorité est atteinte pour 600FF.** Le cas a
> été requalifié après la correction : ventilation mécanique vérifiée à zéro
> après read-back, infiltration prescrite conservée, ApacheSim exécuté, APS
> `SIA4010_test_1_600FF_20260812_141823.aps` enregistré au ledger avec son
> sha256. Reste pour ce cas la seule qualification de l'APS
> (`SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION`).
>
> **Priorité suivante** : requalifier **640** puis **600**, dont les APS
> enregistrés datent du 2026-08-11 et du 2026-08-09, donc d'avant la correction
> `c7e906b` (2026-08-12 12:55) — ce sont des bases de référence, pas des
> résultats citables. Ensuite seulement 900, 940 et 900FF.

Procédure, inchangée :

1. Ouvrir le projet jetable sauvegardé correspondant dans IESVE 2025.
2. Exécuter dans VEScripts :
   `Run_VE_SIA4010_Test1_Fast_Start.py`
3. Vérifier dans la sortie une preuve équivalente à :
   `Mechanical ventilation: 0 L/s/person, verified zero`
4. Vérifier que l'infiltration prescrite est conservée. **À réconcilier** : ce
   document annonçait 0,41 ACH / environ 14,76 L/s, tandis que le read-back réel
   du 600FF a relevé `max_flow = 0,3075` avec `units_val = 2`. Les deux chiffres
   n'ont pas été rapprochés et l'unité derrière `units_val = 2` n'est pas
   démontrée ici : ne pas trancher, relever la valeur observée et la comparer à
   la spécification avant d'en faire un critère.
5. Vérifier que l'ApacheSim qualifié s'exécute et produit un nouvel APS.
6. Vérifier que le ledger central est mis à jour avec les nouveaux SHA-256.
7. Seulement après ce run, exécuter successivement les cas 900, 940 et 900FF dans des projets jetables distincts.

Si le Fast Start échoue, ne pas contourner le garde-fou. Lire le dernier JSON sous :

- `<projet>/reference_model_artifacts/reports/`
- `<projet>/sia4010_artifacts/diagnostics/`
- `<projet>/sia4010_artifacts/simulation/`
- `<projet>/apache/status.json`

## 8. Autres découvertes Test 1 à conserver

- Le cas 640 a produit des écarts importants par rapport aux valeurs ISO ; ils ne sont pas résolus par le préconditionnement ou par un setpoint constant.
- Le gain interne de 200 W continu a été vérifié dans le modèle et dans l'APS : environ 1 752 kWh/an.
- L'infiltration a été vérifiée à environ 14,76 L/s dans l'APS.
- Le transport solaire a montré un écart : irradiation sud VE autour de 1 477 kWh/m² contre environ 1 547,1 kWh/m² ISO dans un diagnostic ; le transport météo expérimental a réduit, mais pas supprimé, cet écart.
- Les coefficients convectifs APS observés diffèrent légèrement des cibles ISO et les coefficients radiatifs n'ont pas été résolus comme variables APS.
- Pour les cas contrôlés, l'entrée Apache doit démontrer `RFCONT=0.5` afin d'utiliser une température opérative/dry-resultant. Un run 600FF a d'abord été bloqué à `RFCONT=0`, puis relancé après correction.
- Le diagnostic de convention horaire a trouvé un meilleur alignement avec un offset APS de +1 h et un offset `ResultsReader` de +1 800 s ; ceci nécessite encore une décision de binding documentée avant toute comparaison horaire normative.
- Les expériences A/B sont des diagnostics. Elles ne doivent pas être inscrites comme preuves de conformité.

## 9. Tests 2 à 7 et classes de validation

La matrice du produit couvre huit classes et 24 variantes exactes dans `config/sia4010_all_classes.json`. Cela signifie que le framework connaît la couverture attendue ; cela ne signifie pas que les modèles VE sont tous générés ou validés.

État d'exécution :

- routes directes principalement développées pour les six cas ISO du Test 1 ;
- Test 2A dispose de probes et d'une préparation partielle ;
- **2026-08-12 — les probes Tests 3 et 4-7 sont débloquées.** Elles refusaient de démarrer sans `sia_model_scenario.json` pour un cas officiel exact, et les deux seuls écrivains scriptés de ce fichier étaient câblés sur le Test 1 ; la voie générique n'existait que dans la fenêtre Tkinter. [`Run_VE_SIA4010_Prepare_Case_Scenario.py`](Run_VE_SIA4010_Prepare_Case_Scenario.py) comble ce trou en `PREPARE_ONLY`. La chaîne a été répétée hors VE avant d'être proposée : `prepare_case_bundle` réussit pour `test_3A`, `test_4` et `test_7` avec le statut `PREPARED_WITH_BLOCKERS`, et les deux probes franchissent alors leur portail de scénario. Attention : préparer un cas dans un projet qui porte déjà le scénario d'un autre cas l'écrase — le launcher refuse par défaut et exige `ALLOW_SCENARIO_REPLACEMENT = True` ;
- Tests 2 à 7 nécessitent encore des bindings VE réels, des templates qualifiés ou des topologies ApacheHVAC démontrées ;
- aucun template VE qualifié n'était enregistré dans le dernier statut hybride lu ;
- Tests 4 à 7 ne peuvent pas être déclarés exécutables de bout en bout tant que les réseaux exacts ne sont ni générés avec des setters vérifiés, ni fournis puis capturés et revus.

Clarifications SIA reçues et déjà intégrées :

- pour les distributions des Tests 2, 3 et 5, le `Streubereich` est l'enveloppe min/max des programmes de référence par classe ;
- les heures hors bornes des classes expliquent des sommes inférieures à 8 760 dans certains tableaux ; il ne faut pas modifier ces références ;
- le classeur Test 7 corrigé utilise la borne inférieure et la borne supérieure ;
- les résultats requis pour les Tests 4, 6 et 7 sont ceux listés dans les classeurs Excel.

## 10. État SIA 380/2

La chaîne client sait déjà :

- extraire géométrie, zones, enveloppe, fenêtres, constructions et une partie des templates/profils ;
- produire des diagnostics sur U-values, vitrage, ventilation, gains, éclairage et résultats APS ;
- générer un rapport Excel d'audit/readiness ;
- conserver les valeurs inconnues comme preuves manquantes plutôt que les inventer.

Elle ne constitue pas encore un calcul automatique complet et autonome du projet de référence SIA 380/2. Les dépendances restantes comprennent notamment :

- la validation des catégories d'usage SIA 2024 et des horaires natifs ;
- les liaisons contrôlées SIA 387/4 pour l'éclairage ;
- les détails systèmes/AHU/auxiliaires lorsqu'ils ne sont pas exposés dans APS ;
- les métadonnées climatiques et bâtiment revues ;
- la comparaison globale projet/référence avec l'indicateur canonique et sa pondération SIA 380 ;
- la revue humaine et la provenance des preuves.

Le démonstrateur client reste `Run_VE_Swiss_Compliance_Hub.py`, mais les anciennes documentations peuvent encore désigner `Run_VE_Swiss_Compliance.py`. Vérifier le code actuel avant de modifier les guides.

## 11. Tests à lancer avant toute livraison

Commencer par les tests ciblés de la zone modifiée, puis élargir :

```powershell
python -m pytest -q tests/test_sia4010_mvp_bundle.py tests/test_sia4010_test1_runtime_inputs.py tests/test_sia4010_apachesim_qualification.py
python -m unittest discover -s tests -p "test_*.py"
python -m compileall -q swiss_sia scripts Run_VE_Swiss_Compliance.py Run_VE_Swiss_Reference_Model.py
python scripts/quality/validate_release.py
git diff --check
git status --short
```

Une réussite locale ne clôt pas un changement de binding `iesve`. Ajouter la preuve du run réel IESVE 2025 et le chemin du JSON de read-back.

## 12. Stratégie de travail recommandée à Claude

1. Reproduire/inspecter avant d'éditer.
2. Traiter un seul bloqueur runtime à la fois.
3. Faire une modification minimale et ajouter un test de non-régression.
4. Demander à l'utilisateur uniquement les runs qui nécessitent réellement IESVE.
5. Après chaque run, lire le JSON, identifier la cause précise et mettre à jour le ledger seulement via les interfaces existantes.
6. Ne pas multiplier les scripts A/B si une propriété peut être vérifiée par read-back déterministe.
7. Ne pas optimiser des résultats vers une valeur de référence en modifiant des paramètres physiques sans source normative.
8. Conserver une distinction explicite entre `IMPLEMENTED`, `LOCAL_TESTED`, `REAL_VE_QUALIFIED`, `RESULTS_RECORDED` et `OFFICIALLY_ACCEPTED`.

## 13. Critère de fin réaliste du MVP

Le MVP démontrable est atteint lorsque :

- le Hub s'ouvre et exécute les contrôles client sans crash ;
- un modèle client produit un rapport SIA 380/2 conservateur et traçable ;
- les cas SIA 4010 annoncés comme supportés ont chacun un modèle jetable, un read-back VE, une simulation APS, une comparaison et des checksums ;
- les tests non supportés apparaissent clairement bloqués avec l'action requise ;
- aucune absence de critère ou de preuve n'est transformée en conformité.

Le MVP ne doit pas promettre que les sept tests ou les huit classes sont déjà validés à 100 % : l'état des preuves ne le démontre pas encore.

