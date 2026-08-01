# Swiss VE Model Builder — guide opérateur

## Périmètre réel

L’interface couvre les huit classes SIA 4010 (`1A`, `1B`, `2A`, `2B`, `3`,
`4A`, `4B`, `5`) et les 24 variantes exactes de la matrice officielle.

Cette couverture a trois niveaux qui ne doivent pas être confondus :

1. **Framework** : spécifications et classeurs officiels vérifiés par checksum,
   variantes routées, bandes de référence analysées et navigateur disponible.
2. **Préparation** : dossier source-tracé, liste des entrées manquantes, file
   d’exécution et étapes de validation produits sans modifier VE.
3. **Génération VE** : mutation automatisée et relue dans VE. À ce jour, seul
   `test_1/600` possède ce niveau éprouvé.

Cinq cas supplémentaires, `test_1/640`, `test_1/600FF`, `test_1/900`,
`test_1/940` et `test_1/900FF`, possèdent un
générateur en état `RUNTIME_QUALIFICATION_READY`. L’interface les expose avec
le bouton distinct `Qualifier le générateur dans VE`. Ils ne passent au registre
de preuves qu’après une exécution complète et des read-backs réussis dans un
projet jetable neuf.

Les cas 900, 940 et 900FF utilisent la définition publique haute masse
d’ASHRAE 140-2017 Addendum a, tableau 5-27 : mur en bloc de béton, isolation
mousse et bardage bois, dalle béton et isolation idéale de plancher, avec la
toiture du cas 600 inchangée. Cette source est marquée `PUBLIC_REFERENCE` :
elle ne remplace pas la confirmation demandée à la SIA pour l’identité exacte
avec SN EN ISO 52016-1:2017, chapitre 7. La qualification s’arrête si VE ne
conserve pas les valeurs nulles de densité et de capacité calorifique de
l’isolation idéale, au lieu d’introduire silencieusement une valeur minimale.

Une préparation ou une couverture framework n’est jamais présentée comme une
validation SIA.

## Règles de sécurité

- Un cas officiel correspond à **un projet VE jetable et sauvegardé**.
- Une classe peut exiger plusieurs projets : un par cas exact.
- Le bouton `Créer dans VE` n’est actif que si un générateur contrôlé existe.
- Le bouton `Qualifier le générateur dans VE` n’est actif que pour un
  générateur source-tracé encore non vérifié ; son résultat ne vaut jamais
  déclaration de conformité.
- Les cas non implémentés restent accessibles avec `Préparer et contrôler` ;
  l’interface crée alors un audit exploitable et signale les bloqueurs.
- Un projet VE temporaire `VEPROJ` non sauvegardé ne peut jamais être muté.
- Aucun paramètre officiel absent n’est inventé.
- Une comparaison positive aux bandes officielles reste distincte de
  l’attestation externe SIA.

## Utilisation dans VEScripts

1. Ouvrir ou créer un projet VE jetable, puis le sauvegarder.
2. Exécuter `Run_VE_SIA_Model_Builder_UI_Probe.py`.
3. Vérifier `SIA MODEL BUILDER UI PROBE: READY`.
4. Exécuter `Run_VE_SIA_Model_Builder_UI.py`.
5. Choisir la classe, la variante et le cas.
6. Cliquer sur `Préparer et contrôler`.
7. Examiner le statut et le JSON dans
   `sia4010_artifacts/model_builder/`.
8. Si `Créer dans VE` est actif, lancer la mutation contrôlée dans le projet
   jetable. Sinon, traiter les bloqueurs indiqués par le rapport.

Le bouton `Entrées normatives externes` crée, uniquement s’il est absent, le
fichier `sia4010_external_inputs.json` à la racine du projet VE sauvegardé, puis
l’ouvre. Le modèle source est
`config/sia4010_external_inputs.example.json`. Un fichier existant n’est jamais
écrasé.

Chaque entrée déléguée doit contenir :

- le chemin et le SHA-256 du fichier source ;
- sa provenance et l’autorité qui l’a fourni ;
- la référence de licence ou d’autorisation d’usage ;
- l’identité du dataset, son format et son périmètre sémantique ;
- le chemin et le SHA-256 d’un rapport de validation technique indépendant ;
- `normative_authorization_status = CONFIRMED` et
  `technical_validation.status = PASS`.

Le rapport technique suit le modèle
`config/sia4010_external_input_validation_report.example.json`. Son contenu
doit identifier l’entrée, reprendre le SHA-256 exact de la source, documenter
le validateur et la méthode, et fournir au moins un contrôle nommé. Un statut
global `PASS` est refusé si un seul contrôle n’est pas `PASS`.

Il référence aussi un `binding_artifact` distinct, avec son chemin, son SHA-256
et le `schema_id` attendu pour cette famille d’entrée. Cette séparation permet
de conserver le PDF, classeur ou dataset autorisé comme preuve primaire tout en
fournissant au générateur un artefact normalisé contrôlé. Le rapport est refusé
si le schéma, le fichier ou l’empreinte de cet artefact ne correspond pas.

Pour `test_2A/2A` et les Tests 3, le bouton copie également six modèles dans
`sia4010_external_input_templates/` :

- cellule et enveloppe légère ISO 52016 chapitre 7 ;
- fichier météo horaire SIA 2028 Zürich-Kloten ;
- profils SIA 2024 catégorie 3.1.
- fonctions SIA 387/4 Tables 9 et 10 ;
- détail source-tracé du store toile du bâtiment exemple ;
- décision d’autorité sur l’identité du dispositif 3K/3L.

Les schémas publiés correspondants sont :

- `schemas/sia4010_iso_test_cell_binding.schema.json` ;
- `schemas/sia4010_sia2028_weather_binding.schema.json` ;
- `schemas/sia4010_sia2024_usage_profiles_binding.schema.json`.
- `schemas/sia4010_sia3874_controls_binding.schema.json` ;
- `schemas/sia4010_shading_device_binding.schema.json` ;
- `schemas/sia4010_authority_decision_binding.schema.json`.

Lorsque leurs trois preuves atteignent réellement `READY_FOR_BINDING`,
`Préparer et contrôler` produit automatiquement
`sia4010_artifacts/model_builder/test2a/generator_input.json`. Ce contrat
vérifie notamment la fermeture des dimensions de fenêtres, la cohérence entre
la géométrie du PDF SIA et la transcription ISO, les 8 760 heures météo et le
jeu exact des profils occupation/équipement/éclairage.

Les trois horaires fonctionnels SIA 2024 et les objets natifs VE sont deux
contrats distincts. Une série logique de 8 760 valeurs ne peut jamais être
transmise à `VEProject.create_profile("yearly", ...)` : dans VE, un profil
annuel contient des périodes référençant des profils hebdomadaires, lesquels
référencent sept profils journaliers. L’artefact SIA 2024 peut donc fournir un
`ve_profile_graph` explicite avec :

- des nœuds `daily`, `weekly` et `yearly` ayant chacun une référence VE unique ;
- exactement sept `profile_ref` journaliers par nœud hebdomadaire ;
- des périodes annuelles contiguës couvrant exactement les jours 1 à 365 ;
- trois sorties explicites pour occupation, équipement et éclairage ;
- un `source_locator` sur chaque nœud et sur le graphe complet.

Sans ce graphe, le statut est
`SOURCE_BINDINGS_READY_PROFILE_GRAPH_REQUIRED`. Avec un graphe valide, il
devient `SOURCE_BINDINGS_READY_VE_BINDING_REQUIRED`. Dans les deux cas, la
mutation VE demeure désactivée tant que les setters/read-backs du store toile
dynamique et des profils SIA 2024 ne sont pas qualifiés. Le contrat d’entrée ne
doit donc jamais être présenté comme un modèle Test 2A exécuté.

Pour qualifier séparément le graphe de profils et les setters CDB du store dans
un projet jetable :

1. préparer le scénario officiel `test_2A/2A` ;
2. exécuter `Sonder le runtime Test 2A` ;
3. attendre le statut
   `READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION` ;
4. cliquer `Qualifier les profils Test 2A` ;
5. dans le même écran, cliquer `Qualifier les setters du store Test 2A` ;
6. après son PASS, cliquer `Qualifier l’optique fixe 2E1`.

Le second bouton demeure désactivé jusqu’au PASS de la sonde en lecture seule.
Il appelle
`Run_VE_SIA4010_Test2A_Profile_Qualification.py`, refuse tout homonyme avant la
première création, matérialise les dépendances dans l’ordre, sauvegarde chaque
niveau puis relit exactement le type et les données. Son rapport
`sia2a_profiles_*.json` et son `.sha256` ne qualifient que cette frontière :
aucune géométrie, construction, template, charge, protection solaire, météo ou
simulation n’est créée.

Le bouton du store appelle
`Run_VE_SIA4010_Test2A_Shading_Setter_Qualification.py`. Il crée exactement une
construction vitrée CDB non affectée, ne touche à aucune couche et vérifie
uniquement la persistance de `external_shade_active`,
`external_shade_radiation_to_lower=150` et
`external_shade_radiation_to_raise=150`. Un rapport antérieur, même `STARTED`,
interdit toute répétition dans le même projet : il faut alors jeter le projet.
Son PASS signifie seulement `CDB_STORAGE_AND_READBACK_ONLY`. Le PDF fourni ne
précise pas le signal exact, l’opérateur d’activation ni la règle de remontée ;
ces champs restent donc inconnus. Le PASS ne qualifie pas non plus la mémoire
d’état au pas de temps ni la conversion de `g_total=0.059` vers les champs
optiques VE.

Le dernier bouton appelle
`Run_VE_SIA4010_Test2A_2E1_Optical_Setter_Qualification.py`. Il exige le
rapport précédent et son SHA-256 valides, refuse une seconde exécution dans le
même projet et crée une autre construction vitrée CDB non affectée. Il écrit et
relit seulement les champs à correspondance directe : activation, profil `ON`,
transmission solaire normale `0.040`, réflexion solaire extérieure `0.490` et
réflexion visible extérieure `0.496`. Son PASS signifie uniquement que VE
stocke ces cinq champs. Il maintient explicitement
`fixed_closed_optical_mapping_qualified=false` et
`diagnostic_candidate_generation_authorized=false` : les valeurs angulaires,
la réflexion intérieure, la transmission visible, les gains secondaires et
l’équivalence des sorties APS restent à qualifier.
Après l’écriture du rapport et de son SHA-256, le même VEScript reconstruit
automatiquement `test2a/generator_input.json` et
`test2a/source_binding_audit.json`. L’interface affiche leur statut. Le statut
attendu après les trois qualifications est
`RUNTIME_STORAGE_QUALIFIED_MODEL_BINDING_REQUIRED` ; il confirme les frontières
de stockage mais conserve `mutation_supported=false`.

Le contrat optique conserve désormais les identités exactes de la documentation
du bâtiment exemple : `g_total=0.059 = tau_e 0.040 + qi 0.019`, avec
`qi=0.006` convection + `0.013` rayonnement thermique + `0.000` ventilation.
Le cas officiel `Diag 2E1` — store toile toujours fermé — est enregistré comme
gate préalable. Son schéma est désormais lié au classeur officiel dont le
SHA-256 est contrôlé : `Daten_Testprogramm!X5:X8764` pour le temps,
`Y5:AA8764` pour les trois irradiations et `BD5:BH8764` pour les cinq sorties
du diagnostic. Les feuilles des programmes de référence utilisent les mêmes
colonnes de grandeurs sur les lignes 4 à 8763. Cette liaison prouve où lire et
écrire les 8 760 valeurs ; elle ne prouve pas que les cellules candidates sont
remplies ni que VE reproduit le store. Aucun rapport `g_total/g_vitrage` n’est
accepté comme facteur de transmission VE sans une simulation 2E1 et une
équivalence de sortie qualifiées.

Le classeur ne définit toutefois aucune borne ni règle PASS/FAIL pour 2E1 :
ses feuilles sont des graphiques de diagnostic. Le comparateur
`test2a_diagnostic_evaluation.py` reproduit donc uniquement les valeurs
annuelles des programmes de référence et leur enveloppe de distribution
horaire. Il peut signaler `WITHIN_TECHNICAL_REFERENCE_ENVELOPE`, mais son
rapport conserve obligatoirement `acceptance_criterion_available=false`,
`compliance_pass=false` et `optical_mapping_qualified=false`. Une décision
technique séparée et revue reste nécessaire avant d’autoriser la représentation
optique fixe fermée.

Le contrat APS est volontairement incomplet à ce stade : une seule des huit
séries est qualifiée, `Window solar gains` au niveau zone pour le gain solaire
total. Les sept autres restent bloquées avec
`UNBOUND_RUNTIME_EVIDENCE_REQUIRED`. Une évaluation 2E1 exige en outre le
scénario exact `SIA4010_TEST_2A_2E1`, le store `ALWAYS_CLOSED`, une simulation
terminée et le SHA-256 du fichier APS correspondant. Elle refuse donc un APS
Case 600 ou un APS du contrôle dynamique 2A.

Le bouton `Sonder les sorties APS actives` lance la sonde en lecture seule sur
le dernier APS. Elle inventorie les surfaces du modèle et tente les lectures de
niveau surface uniquement avec le `room_id` et l’`aps_handle` exacts fournis
par VE. Le statut `READY_FOR_SURFACE_BINDING_REVIEW` signifie que des séries
ont été lues ; il ne signifie pas que leur signification physique est déjà
qualifiée ni qu’elles correspondent aux colonnes officielles 2E1.

La préparation renvoie `MISSING_MANIFEST`, `BLOCKED`,
`READY_FOR_BINDING` ou `NOT_REQUIRED` pour ces entrées. Même
`READY_FOR_BINDING` ne déclare aucune conformité : il autorise seulement le
développement du binding correspondant. Une erreur de checksum, un identifiant
inconnu ou un manifeste provenant d’un autre projet arrête le workflow.

Le bouton `Préparer toute la classe` vérifie une seule fois le package officiel
et produit :

- un audit par cas exact ;
- un index de classe ;
- une file d’exécution ordonnée ;
- les entrées officielles et générateurs encore bloquants ;
- le contrat complet génération → ApacheSim → APS → comparaison → rapport.

Il ne crée pas silencieusement plusieurs projets VE : l’API qualifiée utilisée
par le MVP modifie le projet actif mais ne fournit pas encore une création et
une sauvegarde fiables de projets indépendants.

Le bouton `Préparer les 8 classes` exécute la même préparation sur toute la
matrice en un seul passage de vérification du package. Il écrit
`SIA4010_all_classes_preparation.json`, distingue les 30 cas uniques des
occurrences répétées entre classes et conserve chaque bloqueur. Pour les Tests
4, 5 et 6, les espaces requis sont extraits du fichier IFC officiel avec leur
empreinte, altitude, hauteur, aire, volume et checksum source.

Le même audit contient `external_input_matrix` : les 30 cas y sont associés aux
17 entrées déléguées cataloguées, avec les cas affectés, le statut de chaque
preuve et les problèmes exacts. Sans manifeste projet, les six cas Test 1
autonomes par rapport à cette couche sont `NOT_REQUIRED` et les 24 autres sont
`MISSING_MANIFEST`; cela ne modifie pas leur statut de générateur VE.

Cette commande initialise aussi
`sia4010_evidence/autonomy/sia4010_case_evidence.json`. Ce registre central
coordonne les projets jetables, revérifie les checksums avant chaque gate et
reconstruit les huit rapports dans
`sia4010_evidence/autonomy/navigator/`.

Le schéma `1.1` du registre distingue trois preuves pour chaque cas exact :
rapport du modèle, exécution ApacheSim et évaluation APS. Les registres `1.0`
existants sont migrés sans effacer leurs rapports. Un gate de résultat exige que
l’APS évalué soit exactement celui produit par la simulation enregistrée.

Le bouton `Ouvrir le navigateur de preuves` reconstruit ces huit rapports avant
de les ouvrir. Son journal affiche le nombre de modèles, simulations et
évaluations APS dont les fichiers et empreintes sont encore valides.

L’interface HTML autonome et l’interface native utilisent toutes deux
`config/sia4010_all_classes.json` comme manifeste officiel par défaut. L’ancien
manifeste `sia4010_classes_1a_1b.json` reste une source géométrique spécialisée
pour la cellule commune des Tests 1 à 3 ; il n’est plus présenté comme le
manifeste global à l’opérateur.

## Sonde runtime Test 3

Après avoir préparé un scénario exact `test_3A/3A` à `test_3L/3L` dans un
projet jetable sauvegardé, le bouton `Sonder le runtime éclairage Test 3`
exécute
`Run_VE_SIA4010_Test3_Runtime_Capability_Probe.py`.

Cette sonde appelle uniquement des getters. Elle relève :

- les gains d’éclairage globaux, dans les templates et dans chaque zone ;
- la présence et la valeur des champs `variation_profile`,
  `dimming_profile`, `max_illuminance` et `installed_power_density` ;
- la disponibilité d’un setter sur chaque proxy, sans jamais l’appeler ;
- les membres publics liés aux capteurs, à l’éclairement, au daylight et aux
  photocellules ;
- la disponibilité des entrées externes exigées par le cas sélectionné ;
- les bloqueurs distincts des douze variantes, y compris la clarification
  spécifique 3K/3L et les bindings APS encore absents.

Le rapport `sia4010_test3_runtime_capability_*.json` et son `.sha256` couvrent
les douze variantes. Même le statut
`READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION` autorise seulement le
développement d’un probe étroit de setters dans une nouvelle copie jetable.
Il conserve `mutation_authorized=false`, `simulation_performed=false` et
`compliance_claim_allowed=false`.

Lorsque toutes les preuves externes du cas sélectionné sont réellement
`READY_FOR_BINDING`, `Préparer et contrôler` remplace automatiquement la
préparation générique par un bundle source-tracé :

`sia4010_artifacts/model_builder/test3/<3A-3L>/generator_input.json`.

Ce bundle vérifie le jeu exact des fonctions SIA 387/4 (ombrage 1–3,
éclairage 1–6), le détail du store, la cohérence de la cellule ISO, le couple
de contrôles prescrit par la matrice 3A–3L, la bande annuelle officielle et le
contrat de distribution horaire `Beleuchtungsleistung`. Il ne lance ni VE ni
ApacheSim. Les variantes 3K/3L exigent une décision SIA liée par checksum et
restent bloquées tant que cette décision n’a pas été traduite en mapping runtime
qualifié.

## Case 600 exécutable

Pour `test_1/600`, l’interface crée automatiquement les fichiers source-tracés
locaux :

- `sia4010_case_manifest.json` ;
- `reference_model_config.json` ;
- `reference_model_assets.json` ;
- `sia4010_case600_mvp_audit.json`.

La météo BESTEST DRYCOLD doit être présente et vérifiée. Le workflow :

1. crée et relit les profils, matériaux, constructions, gains, échanges d’air
   et template thermique ;
2. importe la géométrie gbXML ;
3. assigne et relit les constructions, ouvertures, template et météo ;
4. exécute la validation finale et écrit le rapport d’audit.

Après création, le modèle est prêt pour le calcul annuel. Le VEScript
`Run_VE_SIA4010_APS_Probe.py` peut ensuite vérifier en lecture seule le fichier
APS. Les variables ne sont utilisées que si leur métadonnée correspond au
contrat qualifié `config/sia4010_aps_bindings_ve_runtime.json`.
La même opération est accessible dans l’interface avec
`Sonder les sorties APS actives`; le rapport inclut aussi les lectures de
surface par `aps_handle` lorsqu’elles sont disponibles.

Pour les cas `600`, `640`, `600FF`, `900`, `940` et `900FF`, le bouton
`Lancer ApacheSim + évaluer l’APS` automatise cette chaîne. Il exige d’abord un
rapport de mutation du cas exact avec une seule zone et une météo relue
`VE-WEA-001 = PASS`. Il règle la période du 1er janvier au 31 décembre et la
sortie horaire prescrites par la spécification Test 1, crée un APS unique sans
écraser une preuve antérieure, enregistre la chaîne scénario → modèle →
ApacheSim → APS avec ses empreintes, puis lance immédiatement l’évaluation
qualifiée.

La spécification Test 1 fournie n’impose ni pas de calcul ApacheSim ni durée de
préconditionnement. Ces deux options sont donc laissées telles qu’elles sont
dans le projet et enregistrées avant/après dans l’audit. La réussite de l’appel
ApacheSim produit le statut
`SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION` ; elle ne devient un résultat
exploitable qu’après vérification des 8760 valeurs horaires et de toutes les
liaisons APS requises.

Pour les sept cas Test 1 (`600`, `640`, `600FF`, `900`, `940`, `900FF`,
`1E`) et pour `test_2A` à `test_2D`, le bouton
`Évaluer l’APS actif` lit le dernier APS, vérifie les métadonnées qualifiées,
calcule les métriques officielles et, pour le Test 2, la distribution horaire.
Le résultat est enregistré avec les checksums APS/bindings dans le registre
inter-projets. Pour `600`, `640`, `900` et `940`, le classeur officiel ne
fournit pas de borne d’acceptation : l’interface enregistre les 28 résultats
avec `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION`, jamais avec un PASS
de conformité. `1E` conserve sa comparaison bornée. Les cas free-float
`600FF`/`900FF` utilisent les liaisons annuelles qualifiées de température
d’air et de température opérative.

Une évaluation lancée séparément sur un APS qui ne correspond à aucune
simulation enregistrée reste disponible comme diagnostic, mais porte
`simulation_link_status = NOT_LINKED` et ne peut jamais satisfaire le
navigateur.

## Cas non encore générés

L’interface n’essaie plus de fabriquer une géométrie générique avec des valeurs
non liées. Elle renvoie `PREPARED_WITH_BLOCKERS` et enregistre notamment :

- le PDF de spécification officiel ;
- le classeur d’évaluation officiel ;
- leurs checksums ;
- la variante et le cas exacts ;
- les entrées structurées encore non liées ;
- le bloqueur logiciel du générateur VE ;
- les critères annuels et, pour les tests 2, 3 et 5, les distributions horaires
  obligatoires.

## Statuts à comprendre

| Statut | Signification |
| --- | --- |
| `READY_FOR_PREPARATION` | scénario valide pour une opération sans mutation |
| `PREPARED_WITH_BLOCKERS` | sources vérifiées, mais entrées/générateur incomplets |
| `READY_FOR_PROVISIONAL_VE_MUTATION` | mutation MVP possible avec hypothèses publiques explicitement signalées |
| `READY_FOR_VE_MUTATION` | aucune entrée requise non résolue dans le contrat |
| `NOT_CHECKABLE` | résultat APS ou critère officiel manquant |
| `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION` | résultats calculés et tracés, mais aucune borne officielle ne permet un verdict |
| `OFFICIAL_RESULTS_RECORDED` | critères implémentés dans les bandes, sans attestation SIA |
| `READY_FOR_OFFICIAL_REVIEW` | dossier technique complet à soumettre |

## Fichiers principaux

- interface native : `Run_VE_SIA_Model_Builder_UI.py` ;
- probe UI : `Run_VE_SIA_Model_Builder_UI_Probe.py` ;
- lanceur scénario : `Run_VE_SIA_Model_Builder.py` ;
- préparation non graphique des huit classes :
  `Run_VE_SIA4010_Prepare_All_Classes.py` ;
- analyse APS qualifiée du cas actif Test 1 ou Test 2A-2D :
  `Run_VE_SIA4010_Evaluate_Active_Case.py` ;
- sonde APS de zone et de surface strictement en lecture seule :
  `Run_VE_SIA4010_APS_Probe.py` et
  `swiss_sia/reference_model/sia4010/aps_probe.py` ;
- simulation annuelle Test 1 et évaluation APS en une opération :
  `Run_VE_SIA4010_Simulate_Active_Case.py` ;
- contrat des scénarios : `swiss_sia/reference_model/sia4010/model_scenario.py` ;
- registre des capacités : `swiss_sia/reference_model/sia4010/case_registry.py` ;
- entrées confirmées et dépendances Tests 2 à 7 :
  `config/sia4010_official_input_contract.json` ;
- modèle des preuves externes à copier dans chaque projet :
  `config/sia4010_external_inputs.example.json` ;
- modèle du rapport lié à chaque source :
  `config/sia4010_external_input_validation_report.example.json` ;
- validation des sources, droits, formats et rapports externes :
  `swiss_sia/reference_model/sia4010/external_input_manifest.py` ;
- validation sémantique des trois artefacts Test 2A :
  `swiss_sia/reference_model/sia4010/normalized_external_inputs.py` ;
- contrat générateur Test 2A conditionnel :
  `swiss_sia/reference_model/sia4010/test2a_source_bundle.py` ;
- sonde runtime Test 2A strictement en lecture seule :
  `Run_VE_SIA4010_Test2A_Runtime_Capability_Probe.py` et
  `swiss_sia/reference_model/sia4010/test2a_runtime_capability.py` ;
- qualification contrôlée du seul graphe de profils Test 2A :
  `Run_VE_SIA4010_Test2A_Profile_Qualification.py`,
  `swiss_sia/reference_model/sia4010/test2a_profile_binding.py` et
  `swiss_sia/reference_model/sia4010/test2a_profile_qualification.py` ;
- contrat binaire source-tracé et qualification étroite des setters du store :
  `swiss_sia/reference_model/sia4010/test2a_shading_control.py`,
  `swiss_sia/reference_model/sia4010/test2a_shading_qualification.py` et
  `Run_VE_SIA4010_Test2A_Shading_Setter_Qualification.py` ;
- préparation tous cas/classes :
  `swiss_sia/reference_model/sia4010/preparation_bundle.py` ;
- préflight fail-closed :
  `swiss_sia/reference_model/sia4010/scenario_preflight.py` ;
- comparaison officielle : `swiss_sia/reference_model/sia4010/test_runner.py` ;
- navigateur de classe : `swiss_sia/reference_model/sia4010/navigator.py` ;
- manifeste huit classes : `config/sia4010_all_classes.json`.
