# Runbook de rush MVP — 13 août 2026

## Résultat visé

Livrer un MVP VEScripts qui :

1. analyse un modèle client pour la SIA 380/2 sans inventer de verdict ;
2. prépare, exécute et audite les cas SIA 4010 réellement implémentés ;
3. compare les résultats lorsque le critère officiel existe ;
4. retourne `NOT_CHECKABLE` ou un bloqueur traçable lorsque la preuve manque ;
5. conserve les checksums du modèle, de la simulation et de l'APS.

Le MVP n'est pas une attestation SIA. L'attestation de la sous-commission reste
un processus externe.

## État vérifié du code

- Tous les groupes de tests Python passent en exécution partitionnée.
- Le gate `python scripts/quality/validate_release.py` réussit : 292 contrôles
  bloquants passent. Les avertissements restants concernent la documentation
  historique en français et le registre logiciel optionnel absent.
- Le classeur Excel le plus récent s'ouvre et contient toutes les feuilles,
  graphiques et dessins attendus, sans marqueur d'erreur de formule évident.
- Le navigateur recense 34 cas exacts : 2 modèles/simulations/résultats APS
  avec checksums valides, aucune classe prête à revue officielle.

## File VE prioritaire — aucun besoin externe

La campagne Test 1 contient maintenant dix cas exécutables. Deux sont complets
dans le ledger (`640`, `600FF`). Les huit cas suivants sont à exécuter, dans cet
ordre :

1. `600` — simulation présente, APS à réévaluer/requalifier après correction ;
2. `900` ;
3. `940` ;
4. `900FF` ;
5. `1A` ;
6. `1B` ;
7. `1C` ;
8. `1D`.

Pour chaque cas :

1. créer et enregistrer un projet VE jetable vide nommé exactement
   `SIA4010_TEST1_<CAS>` ;
2. lancer `Run_VE_SIA4010_Test1_Fast_Start.py` dans VEScripts ;
3. ne pas relancer sur un autre cas dans le même projet ;
4. enregistrer le projet lorsque le script le demande ;
5. relancer `Run_VE_SIA4010_Navigator.py` après chaque cas ;
6. conserver le projet, l'audit modèle, l'audit ApacheSim, l'APS et l'évaluation.

Les cas `1A` à `1D` produisent un livrable annuel horaire chauffage/froid. La
spécification ne leur donne ni résultats de référence ni tolérance : leur état
terminal est `DIAGNOSTIC_DELIVERABLE_RECORDED_NO_ACCEPTANCE_CRITERION`, jamais
un PASS inventé.

Le cas `1E` n'appartient pas à la campagne exécutable : sa dynamique de store
reste à confirmer.

## Démonstration SIA 380/2 sur modèle client

Dans une copie du projet client :

1. lancer `Run_VE_Swiss_Compliance_Hub.py` ;
2. lancer le diagnostic read-only ;
3. compléter les métadonnées projet, correspondances d'usages et preuves qui
   sont signalées manquantes ;
4. charger un APS appartenant au même projet et au même climat ;
5. générer le rapport Excel et le paquet de preuves ;
6. vérifier que tout contrôle non démontrable reste `WARNING`, `FAIL` ou
   `NOT_CHECKABLE`, jamais `PASS`.

Pour un projet comme ZOER, les manques déjà observés sont : ventilation
mécanique exploitable par local, gains VE de type Lighting, variables APS
électricité auxiliaire/ventilateurs/pompes/batteries, métadonnées et identité du
climat. Ils concernent le modèle ou les sorties APS, pas le moteur de règles.

## Développement interne restant, sans réponse SIA

Ces lots peuvent être développés, mais chacun exige ensuite une qualification
réelle dans VE :

1. liaison contrôle solaire pour `2A` à `2D` ;
2. liaison contrôle éclairage pour `3A` à `3L` ;
3. topologie HVAC du Test 4 ;
4. HVAC multizone du Test 5 ;
5. séquence de ventilation du Test 6 ;
6. systèmes énergétiques du Test 7 ;
7. extraction APS des familles encore marquées `UNAVAILABLE`.

Priorité recommandée après Test 1 : Test 2A, car son bundle de sources et sa
chaîne de qualification préparatoire existent déjà. Sa valeur provisoire
d'émissivité interdit actuellement tout verdict.

## Chaîne Test 2A maintenant automatisée

Prérequis VE : une copie jetable enregistrée contenant au moins une ouverture
vitrée. Un projet complètement vide ne permet pas la lecture d'un proxy
d'ouverture et doit rester bloqué avant mutation.

Par l'interface :

1. lancer `Run_VE_SIA_Model_Builder_UI.py` ;
2. choisir `test_2A / 2A` ;
3. cliquer sur **Lancer la chaîne gardée Test 2A** ;
4. lire l'avertissement de portée puis confirmer uniquement dans la copie
   jetable ;
5. conserver le rapport
   `sia4010_test2a_qualification_chain_*.json` et son `.sha256`.

Sans interface, lancer directement
`Run_VE_SIA4010_Test2A_Qualification_One_Click.py`.

Le statut terminal positif de cette chaîne est maintenant
`RUNTIME_STORAGE_THERMAL_AND_OPENING_ASSIGNMENT_QUALIFIED_MODEL_GENERATION_REQUIRED`.
Il qualifie les profils natifs, deux sondes CDB, la coexistence des seuils et
des propriétés optiques sur le même objet, le facteur U ISO du vitrage de base
par une couche thermiquement équivalente, puis une affectation transitoire à
une ouverture avec restauration relue. Il ne génère toujours pas le modèle, ne
laisse pas le store affecté, ne simule pas et n'autorise aucun verdict. Les
prochains travaux internes sont donc la composition fabricant 4/14/4/14/4 et
le U combiné vitrage-store, la dynamique horaire, les optiques
angulaires/secondaires, puis la preuve APS.

Attention : la source SIA 2024 reçue donne les 24 fractions horaires, deux
jours de repos par semaine et 261 jours d'utilisation par an, mais elle ne dit
pas quels jours de semaine sont les jours de repos ni comment les 261 jours
sont placés dans le calendrier VE. Le code refuse donc de créer un graphe
daily/weekly/yearly en inventant cette convention. Il faut une confirmation
d'autorité ou une convention de campagne écrite et acceptée.

## Besoins externes minimaux

### Bloquants normatifs ou d'autorité

- dynamique exacte du store du cas 1E ;
- émissivités IR par défaut de la cellule ISO 52016 chapitre 7, ou confirmation
  que la valeur dérivée 0,90 est admissible ;
- SIA 387/4 tableau 10 et clarification de l'édition 2017/2023 ;
- fiches SIA 2024 auditorium, bâtiment exemple, restaurant 6.2 et cuisine 6.4 ;
- EN 16798-5-1 annexe D pour le récupérateur rotatif du Test 5 ;
- clarifications d'autorité encore consignées pour 3K/3L, la précédence PV et
  les critères applicables aux Tests 4 et 6.

### Nécessaires à la revendication finale, pas au fonctionnement du MVP

- revue et signature des preuves projet ;
- résultats officiels importés dans les classeurs/artefacts attendus ;
- attestation de la sous-commission SIA.

Le détail source par source reste dans
`docs/project/REGISTRE_DEMANDES_EXTERNES.md`.

## Commandes de contrôle hors VE

```powershell
python -m pytest -q -p no:cacheprovider
python scripts/quality/validate_release.py
python Run_VE_SIA4010_Navigator.py
git diff --check
```

Le test d'extraction des six classeurs d'autorité est volontairement lent : il
charge chaque classeur une seule fois par module afin de conserver une vraie
couverture d'intégration sans multiplier les lectures.
