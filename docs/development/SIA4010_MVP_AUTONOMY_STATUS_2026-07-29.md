# SIA 380/2 + SIA 4010 MVP — état d’autonomie

Date : 2026-07-29  
Périmètre : interface VEScripts, huit classes SIA 4010, 24 variantes et
30 cas exacts.

## Résultat de l’itération

| Couche | Couverture | Statut réel |
| --- | ---: | --- |
| Classes routées | 8/8 | PASS |
| Variantes officielles analysées | 24/24 | PASS |
| Cas possédant une préparation source-tracée | 30/30 | PASS |
| Cas capables de produire un gbXML déterministe en préparation | 23/30 (Tests 1-3) | PARTIEL |
| Géométrie IFC officielle extraite | Tests 4/5/6 | PASS SOURCE, PAS ENCORE gbXML |
| Parseurs de bandes annuelles | Tests 1-7 | PASS |
| Critères de distributions horaires | Tests 2, 3 et 5 | PASS |
| Générateurs VE contrôlés | 1/30 (`test_1/600`) | PARTIEL |
| Générateurs prêts pour qualification VE | 5/30 (`test_1/640`, `600FF`, `900`, `940`, `900FF`) | À EXÉCUTER DANS VE |
| Cas avec découverte runtime VE en lecture seule | 13/30 (`test_2A/2A` + Test 3A-3L) | IMPLÉMENTÉE |
| Sonde runtime Test 2A | graphe natif de profils, CDB vitrage/store, ouvertures et sources | LECTURE SEULE, FAIL-CLOSED, À EXÉCUTER DANS VE |
| Qualification profils Test 2A | daily/weekly/yearly uniquement, après sonde READY | IMPLÉMENTÉE, À EXÉCUTER DANS UN PROJET JETABLE |
| Qualification setters du store Test 2A | un objet CDB vitré non affecté, actif + seuils 150/150 uniquement | IMPLÉMENTÉE, À EXÉCUTER DANS UN PROJET JETABLE |
| Qualification optique fixe 2E1 | un second objet CDB non affecté, cinq champs à correspondance directe uniquement | IMPLÉMENTÉE, À EXÉCUTER APRÈS LE PASS DES SEUILS |
| Sonde runtime Test 3 | 12/12 variantes, gains éclairage/templates/zones/capteurs | LECTURE SEULE, IMPLÉMENTÉE, À EXÉCUTER DANS VE |
| Chemins ApacheSim contrôlés prêts à qualifier | 6/30 (`600`, `640`, `600FF`, `900`, `940`, `900FF`) | À EXÉCUTER DANS VE |
| Lancements ApacheSim réellement qualifiés dans VE | 0/30 | NON DÉMONTRÉ |
| Liaisons APS qualifiées | 11 cas : les 7 cas Test 1 et Tests 2A-2D | PARTIEL GLOBAL |
| Périmètre APS requis implémenté | 11 cas : les 7 cas Test 1 et Tests 2A-2D | PASS LOGICIEL, VE À EXÉCUTER |
| Séries APS du diagnostic 2E1 | 1/8 : gain solaire total de zone uniquement | FAIL-CLOSED, 7 LIAISONS À QUALIFIER |
| Sonde APS surface/fenêtre | lecture par `room_id` + `aps_handle` exact | IMPLÉMENTÉE DANS L’INTERFACE, À EXÉCUTER SUR 2E1 |
| Températures Test 1 | air + opérative, séries annuelles qualifiées | PASS MÉTADONNÉES VE |
| Comparaison APS avec critères officiels | Test 1/1E et Tests 2A-2D | PASS LOGICIEL, VE À EXÉCUTER |
| Résultats APS sans faux verdict | Test 1/600, 640, 900, 940 | PASS LOGICIEL, AUCUNE BORNE OFFICIELLE |
| Registre d’évidence inter-projets | 30/30 cas | PASS |
| Attestation officielle SIA | externe | NON FOURNIE |

`FRAMEWORK_COVERAGE_PASS` signifie que le logiciel sait lire et router les
exigences. Il ne signifie pas que les 30 modèles existent.

Contrôles de régression exécutés le 2026-07-29 :

- compilation Python : PASS ;
- suite complète : 538 tests, PASS, 11 tests conditionnels ignorés ;
- distributions horaires avec `SIA4010_RUN_HEAVY=1` : 36 tests, PASS ;
- audit officiel : 8/8 classes, 24/24 variantes et 30/30 préparations, PASS ;
- contrôle visuel de l’interface : PASS, y compris la sélection `4B/test_7` ;
- manifeste par défaut de l’interface : `config/sia4010_all_classes.json`.

## Ce que l’interface fait maintenant

- propose les huit classes et les 24 variantes exactes ;
- verrouille les fonctionnalités imposées par chaque cas officiel ;
- permet de préparer n’importe quel cas sans modifier VE ;
- vérifie les checksums du package officiel ;
- inclut le PDF, le classeur et les sources bâtiment/profils nécessaires ;
- inclut les valeurs déjà confirmées et les dépendances encore absentes ;
- produit une file d’exécution complète pour toute la classe sélectionnée ;
- prépare aussi les huit classes en une opération, avec un index global des
  30 cas uniques ;
- extrait du fichier IFC officiel les salles requises par les Tests 4, 5 et 6,
  sans approximation géométrique ;
- enregistre les rapports modèle, l’exécution ApacheSim et l’évaluation APS avec
  leurs SHA-256 dans un ledger commun ;
- relie explicitement chaque évaluation APS au fichier produit par la simulation
  correspondante ; un APS étranger ou une ancienne simulation ne satisfait
  aucun gate ;
- migre sans perte le ledger `1.0` vers le schéma `1.1`, qui possède une preuve
  de simulation distincte pour chacun des 30 cas ;
- invalide automatiquement une preuve déplacée, supprimée ou modifiée ;
- reconstruit les huit navigateurs à partir des preuves réellement disponibles ;
- ouvre directement depuis l’interface le navigateur global reconstruit, avec
  les compteurs de modèles, simulations et évaluations APS encore valides ;
- crée et ouvre depuis l’interface un manifeste de preuves normatives externes
  propre au projet, sans jamais écraser un manifeste existant ;
- exige pour chaque entrée déléguée un fichier et un rapport de validation
  intègres, une provenance, une autorité, une licence, un format, un périmètre
  et une autorisation normative confirmée avant `READY_FOR_BINDING` ;
- sépare la preuve normative primaire de l’artefact machine normalisé consommé
  par les futurs générateurs, et lie les deux par schéma et SHA-256 dans le
  rapport technique ;
- ajoute les bloqueurs externes exacts à chaque préparation de cas et refuse de
  confondre `READY_FOR_BINDING` avec un générateur VE ou une attestation SIA ;
- produit dans l’audit global une matrice 30 cas × 17 entrées déléguées afin de
  montrer immédiatement quelles acquisitions ou clarifications débloquent
  quelles variantes ;
- possède pour Test 2A trois chargeurs normalisés qui vérifient la cellule ISO,
  la météo annuelle SIA 2028 et les profils SIA 2024 sans valeur de secours ;
- sépare désormais les horaires fonctionnels SIA 2024 du graphe natif VE :
  aucune série de 8 760 scalaires ne peut être traitée comme un profil annuel
  VE, et seul un graphe `daily` → `weekly` → `yearly` complet, source-tracé,
  sans cycle et couvrant les jours 1 à 365 peut franchir le preflight ;
- construit conditionnellement un contrat générateur Test 2A immuable lorsque
  ces trois entrées sont autorisées et validées, tout en maintenant la mutation
  VE à `False` jusqu’à qualification des profils et du store dynamique ;
- expose dans l’interface, uniquement pour `test_2A/2A`, une sonde runtime
  strictement en lecture seule qui inventorie les types de profils, les champs
  CDB du store extérieur et les proxies d’ouverture ; son statut le plus élevé
  autorise seulement la qualification contrôlée des profils dans un projet
  jetable, jamais la mutation du modèle complet ni un verdict SIA ;
- expose ensuite un bouton distinct `Qualifier les profils Test 2A`, désactivé
  tant que la sonde n’est pas prête ; cette opération crée et relit uniquement
  le graphe source-tracé, avec collision fail-closed, rapport JSON et SHA-256 ;
- encode séparément ce que le PDF officiel confirme réellement pour le store
  toile — régulation par seuil d’irradiation et valeur d’activation
  150 W/m² — et conserve à `null` le signal exact, l’opérateur de comparaison,
  la règle de remontée et la mémoire d’état, absents du document fourni ;
- expose `Qualifier les setters du store Test 2A` après la même sonde
  read-only ; cette opération crée un seul vitrage CDB non affecté, conserve sa
  couche par défaut, écrit seulement le drapeau actif et les deux seuils, puis
  relit exactement les valeurs ;
- interdit un second essai du store dès qu’un rapport `STARTED`, `FAIL` ou
  `PASS` existe dans le projet jetable, afin qu’un crash natif ne puisse jamais
  être confondu avec une exécution vierge ;
- expose après ce PASS `Qualifier l’optique fixe 2E1` ; ce probe exige le
  rapport de seuil et son SHA-256, écrit puis relit uniquement l’activation, le
  profil `ON`, la transmission solaire normale et les deux réflexions
  extérieures à correspondance directe, sans modifier géométrie, ouverture,
  couche, template ou simulation ;
- relit les trois familles de rapports de qualification dans le bundle Test 2A,
  contrôle leurs SHA-256, leur projet et leurs garde-fous, puis renvoie
  `RUNTIME_STORAGE_QUALIFIED_MODEL_BINDING_REQUIRED` lorsque les trois
  frontières de stockage sont prouvées ; ce statut n’autorise toujours aucune
  génération ; le VEScript optique reconstruit désormais ce bundle et affiche
  son audit automatiquement dans la même exécution ;
- maintient après ce PASS cinq bloqueurs explicites : signal d’irradiation
  exact, opérateur d’activation, règle de remontée, traitement de l’état au pas
  de temps et correspondance optique du `g_total=0.059` Soltis ; aucun de ces
  points n’est inventé ni déclaré qualifié ;
- transcrit les composantes optiques fermées du store depuis la documentation
  du bâtiment exemple et vérifie les deux identités physiques
  `0.040 + 0.019 = 0.059` et `0.006 + 0.013 + 0.000 = 0.019` avant tout accès
  à VE ;
- crée un contrat diagnostic `2E1` à store toujours fermé, exigeant les huit
  séries horaires d’irradiation et de gains solaires ;
- lie désormais ces huit séries au classeur officiel contrôlé par SHA-256 :
  `X5:X8764`, `Y5:AA8764` et `BD5:BH8764` dans `Daten_Testprogramm`, avec les
  lignes 4-8763 correspondantes dans les feuilles de référence ;
- distingue explicitement `OFFICIAL_2E1_SCHEMA_BOUND` d’une qualification
  optique : le premier prouve le schéma de transfert, tandis que le second
  exige encore une simulation fixe fermée et la comparaison des sorties ;
  tout ratio simplifié `g_total/g_vitrage` reste interdit jusque-là ;
- charge les six valeurs annuelles disponibles de gain solaire total, les sept
  valeurs de rayonnement transmis et la distribution horaire de six programmes
  de référence pour 2E1, sans traiter les zéros d’absence comme des résultats ;
- produit une comparaison technique annuelle et horaire, mais conserve
  `REFERENCE_DIAGNOSTIC_RECORDED_NO_ACCEPTANCE_CRITERION`,
  `compliance_pass=false` et `optical_mapping_qualified=false`, car le classeur
  fournit des graphiques diagnostiques et aucune règle d’acceptation 2E1 ;
- lie actuellement une seule des huit sorties 2E1 à une variable APS confirmée :
  `Window solar gains` au niveau zone pour le gain solaire total ; les sept
  autres séries restent explicitement `UNBOUND_RUNTIME_EVIDENCE_REQUIRED` ;
- exige pour toute évaluation 2E1 l’identité exacte
  `SIA4010_TEST_2A_2E1/test_2A/2E1`, l’état `ALWAYS_CLOSED`, une simulation
  terminée, le chemin APS exact et son SHA-256 ; un APS Case 600 ou 2A
  dynamique est refusé avant extraction ;
- expose dans l’interface `Sonder les sorties APS actives`, qui inventorie les
  surfaces VE et lit les variables de niveau `s` uniquement avec leur
  `room_id` et leur `aps_handle` exacts ; cette sonde ne crée aucun binding et
  ne modifie ni VE ni l’APS ;
- analyse directement l’APS actif pour les sept cas Test 1
  `600`, `640`, `600FF`, `900`, `940`, `900FF`, `1E` et pour `test_2A` à
  `test_2D` ;
- attribue aux cas Test 1 sans bornes le statut
  `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION`, sans PASS de
  conformité ; seul `1E` possède une comparaison bornée ;
- extrait pour les cas conditionnés les charges mensuelles/annuelles, pics,
  journées du 4 janvier et du 27 juillet, et températures opératives mensuelles ;
- extrait pour `600FF` et `900FF` les températures opératives mensuelles,
  annuelles max/min/moyenne et les 24 valeurs du 4 janvier ;
- impose un projet VE jetable et sauvegardé par cas exact ;
- désactive `Créer dans VE` si aucun générateur contrôlé n’existe ;
- propose séparément `Qualifier le générateur dans VE` pour les cas 640,
  600FF, 900, 940 et 900FF, uniquement dans un projet jetable sauvegardé ;
- applique aux cas lourds 900/940/900FF les couches publiques traçables
  d’ASHRAE 140-2017 Addendum a, tableau 5-27, sans les promouvoir en entrées
  normatives ISO confirmées ;
- impose un échec de qualification si VE ne conserve pas les propriétés
  thermiques nulles de l’isolant idéal du plancher lourd ou exige une valeur
  minimale qui n’a pas été approuvée ;
- propose `Lancer ApacheSim + évaluer l’APS` pour les six cas Test 1 dont le
  modèle peut être créé ou qualifié ;
- ne règle que la période annuelle confirmée du 1.1.2011 au 31.12.2011, la
  sortie horaire et un nom APS sans écrasement ; le pas de calcul et le
  préconditionnement, absents de la spécification Test 1 fournie, sont
  conservés et audités au lieu d’être inventés ;
- exige avant simulation un rapport exact du bon cas, une mutation VE
  terminée, une seule zone et `VE-WEA-001 = PASS`, puis enchaîne
  automatiquement l’extraction et la comparaison APS ;
- vérifie et enregistre avant la comparaison le scénario, le rapport modèle, la
  spécification Test 1, le contrat temporel, les options ApacheSim relues et le
  nouvel APS ; toute empreinte modifiée bloque le navigateur ;
- empêche le lanceur de fabriquer une géométrie générique pour un cas non lié ;
- conserve les garde-fous « comparaison technique ≠ validation officielle ».
- expose pour chaque scénario exact `test_3A` à `test_3L` une sonde runtime
  strictement en lecture seule ; elle inventorie les gains d’éclairage globaux,
  ceux des templates et des zones, les champs de profil/dimming/éclairement/
  puissance, ainsi que les symboles capteur réellement exposés par VE ;
- produit dans ce même rapport une matrice des 12 variantes avec leur couple
  store/commande d’éclairage et des bloqueurs distincts pour sources externes,
  champs VE, capteur, APS et clarification 3K/3L ; aucun nom de membre observé
  n’est automatiquement promu en setter ou en binding APS ;
- exige désormais séparément le détail source-tracé du store toile du bâtiment
  exemple pour tous les cas Test 3 ; la présence des Tables 9/10 ne suffit plus
  à déclarer leurs sources prêtes ;
- valide un artefact normalisé fermé pour les trois fonctions d’ombrage de la
  Table 9 et les six fonctions d’éclairage de la Table 10 : identifiants,
  signaux, paramètres, conventions temporelles, règles AST sans code Python,
  références, priorités et actions par défaut sont contrôlés fail-closed ;
- construit automatiquement, lorsque les 17 preuves nécessaires au cas sont
  réellement `READY_FOR_BINDING`, un bundle Test 3 par variante comprenant la
  cellule ISO, la météo, les profils, le couple officiel de contrôles, le store,
  la bande annuelle, le contrat de distribution horaire et tous les SHA-256 ;
- conserve dans ce bundle `mutation_supported=false`,
  `simulation_performed=false` et `compliance_claim_allowed=false` jusqu’à
  qualification séparée de l’interpréteur, du capteur, des contrôles VE et des
  variables APS ; les cas 3K/3L gardent en plus un verrou d’interprétation de
  la décision d’autorité ;

## Contrats ajoutés

- `case_registry.py` : état unique de chaque générateur ;
- `preparation_bundle.py` : préparation d’un cas ou d’une classe ;
- `sia4010_official_input_contract.json` : valeurs confirmées Tests 2-7,
  sources et dépendances explicites ;
- `official_input_contract.py` : validation stricte de ce contrat ;
- `sia4010_external_inputs.example.json` : modèle projet des 17 sources,
  datasets, transcriptions ou clarifications délégués ;
- `external_input_manifest.py` : contrôle fail-closed des chemins, SHA-256,
  provenance, droits d’usage, périmètre et validation technique ;
- `test2a_runtime_capability.py` : preuve en lecture seule des API profils et
  store réellement exposées par la version VE active ;
- `test2a_diagnostic_workbook.py` : liaison SHA-256 et plages officielles 2E1 ;
- `test2a_diagnostic_evaluation.py` : comparaison technique 2E1 sans faux
  critère d’acceptation ni promotion automatique de la correspondance optique ;
- `test2a_diagnostic_aps.py` : matrice APS 1/8, preuve de simulation
  checksummée, extraction fail-closed et rapport 2E1 sans faux PASS ;
- `test3_external_bindings.py` : validation normalisée des Tables 9/10, du
  dispositif d’ombrage et de la décision d’autorité 3K/3L ;
- `test3_source_bundle.py` : contrat générateur Test 3 source-tracé pour les
  douze variantes, sans mutation VE ni verdict implicite ;
- `aps_probe.py` : découverte en lecture seule des séries de zone et de surface
  par identité VE exacte ;
- rapports d’implémentation détaillés Tests 2-3, 4-5 et 6-7.

## Bloqueurs qui empêchent encore « tout automatique »

### Dépendances normatives/données

- météo SIA 2028 DRY normal Zürich-Kloten contrôlée ;
- profils exacts SIA 2024 pour bureaux, amphithéâtre, restaurant et cuisine ;
- fonctions SIA 387/4 Tables 9 et 10 pour stores et éclairage ;
- détails ISO 52016 chapitre 7 non encore confirmés ligne par ligne ;
- EN 16798-5-1 annexe D pour le comportement partiel de la récupération
  rotative ;
- clarification SIA du dispositif 3K/3L ;
- décision de préséance entre 60.6 et 62.62 kWp pour le PV Test 7.

### Capacités VE non encore qualifiées

- stores dynamiques à lames et contrôle angulaire ;
- capteur lumière à coordonnées explicites et six algorithmes de commande ;
- import déterministe des espaces IFC du bâtiment exemple ;
- création/lecture complète ApacheHVAC : VAV, CO2, réseaux, récupérateurs,
  batteries, humidification et overflow ;
- réseaux hydrauliques, stockages, PAC réversible, bivalence et PV ;
- lancement ApacheSim avec paramètres officiels depuis VEScripts ;
- extraction APS qualifiée de chaque quantité Tests 3-7.

Un système Apache générique, un rendement constant ou une courbe inventée ne
peut pas être utilisé comme remplacement silencieux.

## Exécution à faire demain dans VE

1. Ouvrir le projet jetable Case 600 existant.
2. Exécuter `Run_VE_SIA4010_All_Classes_Coverage_Audit.py`.
3. Ouvrir `Run_VE_SIA_Model_Builder_UI.py`.
4. Cliquer `Préparer les 8 classes`.
5. Vérifier
   `sia4010_artifacts/model_builder/SIA4010_all_classes_preparation.json`.
6. Sélectionner une classe et, si nécessaire, cliquer
   `Préparer toute la classe` pour son index détaillé.
7. Vérifier le fichier
   `sia4010_artifacts/model_builder/SIA4010_<CLASSE>_class_preparation.json`.
8. Pour Case 600, utiliser `Créer dans VE` dans une copie propre.
9. Dans cinq projets jetables neufs et distincts, sélectionner successivement
   `test_1/640`, `test_1/600FF`, `test_1/900`, `test_1/940` et
   `test_1/900FF`, puis utiliser
   `Qualifier le générateur dans VE`.
10. Conserver chaque rapport, y compris en cas d’échec de qualification.
11. Après chaque création/qualification réussie des six cas pris en charge,
    cliquer `Lancer ApacheSim + évaluer l’APS`. Conserver également le rapport
    `sia4010_artifacts/simulation/SIA4010_test_1_<CAS>_apachesim_qualification.json`.
    Le bouton inscrit automatiquement cette simulation dans le ledger central
    avant d’évaluer l’APS.
12. En cas de diagnostic complémentaire, cliquer
    `Sonder les sorties APS actives` ou exécuter
    `Run_VE_SIA4010_APS_Probe.py`. Pour 2E1, utiliser impérativement un projet
    fixe fermé réellement simulé ; le rapport doit indiquer
    `READY_FOR_SURFACE_BINDING_REVIEW` avant toute revue des sept séries
    manquantes.
13. Pour réévaluer séparément n’importe quel cas Test 1 ou un Test 2A-2D,
    exécuter
    `Run_VE_SIA4010_Evaluate_Active_Case.py`.
14. Exécuter `Run_VE_SIA4010_Navigator.py` pour reconstruire les huit rapports.
15. Conserver le rapport modèle, le rapport de simulation, le rapport APS et le
    ledger central. `Run_VE_SIA4010_Navigator.py` doit afficher les compteurs de
    modèles, simulations et évaluations APS dont les checksums sont encore valides.

Qualification préparatoire séparée du Test 2A :

1. utiliser un projet VE jetable sauvegardé contenant au moins une ouverture
   vitrée ;
2. sélectionner `test_2A/2A` dans l’interface ;
3. ouvrir `Entrées normatives externes` et ne compléter le manifeste qu’avec
   les trois datasets autorisés, leurs artefacts normalisés et leurs rapports
   de validation ;
4. dans l’artefact SIA 2024, fournir un `ve_profile_graph` source-tracé avec
   des références uniques, sept jours par semaine, une couverture annuelle
   continue de 1 à 365 et les trois sorties occupation/équipement/éclairage ;
5. cliquer `Sonder le runtime Test 2A`, ou exécuter directement
   `Run_VE_SIA4010_Test2A_Runtime_Capability_Probe.py` ;
6. si et seulement si le statut est
   `READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION`, cliquer
   `Qualifier les profils Test 2A`, ou exécuter
   `Run_VE_SIA4010_Test2A_Profile_Qualification.py` ;
7. sans relancer la sonde après une mutation partielle, cliquer également
   `Qualifier les setters du store Test 2A`, ou exécuter
   `Run_VE_SIA4010_Test2A_Shading_Setter_Qualification.py` ;
8. après le PASS des setters de seuil, cliquer
   `Qualifier l’optique fixe 2E1`, ou exécuter
   `Run_VE_SIA4010_Test2A_2E1_Optical_Setter_Qualification.py` ;
9. conserver les quatre rapports JSON et leurs fichiers `.sha256`.

Le statut `NATIVE_PROFILE_GRAPH_REQUIRED` indique que les trois sources sont
validées mais que leur transcription en objets natifs VE n’est pas encore
fournie. Il bloque volontairement toute qualification de mutation.

Le statut `READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION` ne crée lui-même aucun
objet. Il déverrouille uniquement les qualifications étroites. Un PASS du
graphe qualifie les profils natifs ; un PASS du store qualifie seulement les
setters de seuil CDB. Le troisième probe écrit et relit uniquement les champs
optiques VE dont le nom correspond directement aux données officielles du store
fermé : activation, profil `ON`, transmission solaire normale, réflexion
solaire extérieure et réflexion visible extérieure. Il ne déduit aucune valeur
angulaire et ne prétend pas représenter la réflexion intérieure, la transmission
visible, les gains secondaires ou l’équivalence APS. Aucun de ces PASS ne
qualifie le comportement dynamique complet, le modèle Test 2A/2E1, ApacheSim ou
l’APS.

Résultat attendu de la préparation de classe :

```text
CLASS_PREPARED_WITH_BLOCKERS
```

Ce statut est correct : il prouve que l’interface voit chaque cas, connaît ses
sources et refuse de dépasser les capacités réellement implémentées.

## Critère de fin du MVP définitif

Le MVP pourra être présenté comme entièrement autonome pour une classe
seulement lorsque chaque cas exigé par cette classe possède :

1. des entrées officielles sans dépendance non résolue ;
2. un générateur VE idempotent avec read-back ;
3. une simulation annuelle qualifiée ;
4. toutes les séries APS obligatoires ;
5. toutes les bandes annuelles dans les limites ;
6. toutes les distributions horaires obligatoires dans les limites ;
7. un rapport navigateur `READY_FOR_OFFICIAL_REVIEW`.

L’attestation officielle reste une décision externe de l’organisme SIA.
