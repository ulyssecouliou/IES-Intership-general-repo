# Pack de prompts Claude — finalisation du MVP SIA 380/2 + SIA 4010

Date de préparation : 2026-08-11  
Dépôt : `C:\Users\ulysse.couliou\Documents\IES Internship\IES-Intership-general-repo`

## 1. Réglage conseillé

Dans l'application Claude, ouvrir une nouvelle tâche pour chaque prompt et sélectionner le modèle dans l'interface.

| Travail | Modèle | Effort |
|---|---|---|
| Analyse normative, architecture, diagnostic difficile, revue finale | Claude Opus 4.7 | `xhigh` |
| Implémentation Python bornée, tests, refactorisation | Claude Sonnet 4.6 | `high` |
| Blocage particulièrement difficile ou revue finale unique | Claude Opus 4.7 | `max`, une seule passe |
| Classement documentaire sans décision normative | Haiku, facultatif | `medium` |

Ne pas utiliser Haiku pour interpréter une norme, décider d'un critère d'acceptation, modifier une mutation VE ou déclarer un test conforme.

Si l'application ne propose pas exactement ces versions, choisir le dernier Opus disponible pour les tâches d'analyse et le dernier Sonnet disponible pour l'implémentation. Ne pas interrompre un travail en changeant de modèle au milieu d'une tâche.

## 2. En-tête commun à coller avant chaque prompt

```text
CONTEXTE ET RÈGLES NON NÉGOCIABLES

Dépôt de travail :
C:\Users\ulysse.couliou\Documents\IES Internship\IES-Intership-general-repo

Produit : extension Python/VEScripts pour IESVE 2025, Python 3.12.3 embarqué, destinée à :
1. contrôler la readiness/compliance SIA 380/2:2022 d'un modèle client IESVE ;
2. exécuter et documenter les sept tests de validation SIA 4010:2023 ;
3. produire des preuves auditées sans jamais transformer une absence de preuve en PASS.

Avant toute action :
- lis CLAUDE.md puis les documents ciblés dans docs/project ;
- exécute git status --short et inspecte les diffs des fichiers que tu envisages de modifier ;
- le worktree contient beaucoup de changements légitimes de l'utilisateur et de Codex : préserve-les tous ;
- interdiction de git reset, checkout, restore, clean, stash, rebase, ou de réécrire un fichier sans examiner son diff ;
- ne fais aucun commit, push, PR, installation, téléchargement ou contact externe sans demande explicite ;
- ne modifie jamais les fichiers officiels SIA/ISO ni les classeurs sources ; traite-les comme des preuves en lecture seule.

Règles réglementaires :
- n'invente aucune valeur, tolérance, convention temporelle, variable APS, signature VEScripts ou règle de conformité ;
- chaque valeur réglementaire doit porter sa source exacte, son unité et son statut de preuve ;
- si une donnée manque : NOT_CHECKABLE ou BLOCKED_BY_EXTERNAL_EVIDENCE, jamais PASS ;
- distingue strictement : test Python, qualification dans VE réel, comparaison aux références, revue officielle SIA ;
- aucune phrase ne doit prétendre que SIA ou IES a certifié le produit.

Règles d'architecture :
- le moteur pur Python ne doit pas importer iesve ;
- tout accès iesve reste isolé dans les adaptateurs/launchers VE ;
- toute mutation VE est précédée d'un capability check et suivie d'un read-back ;
- les arrondis propres à VE doivent être explicitement modélisés et audités, pas masqués par une tolérance globale ;
- conserve les formats de rapports et la compatibilité avec les artefacts existants, sauf justification et migration testée ;
- limite tes modifications au périmètre du prompt.

Sources de vérité principales :
- config/sia4010_classes_1a_1b.json
- config/sia4010_official_input_contract.json
- config/iso52016_chapter7_confirmed_inputs.json
- SIA_4010_geteilter_Link/
- docs/project/SIA3802_SIA4010_IMPLEMENTATION_STATUS.md
- docs/project/OPEN_ITEMS_BACKLOG.md
- docs/project/SIA4010_TESTS_AND_CLASSES_IMPLEMENTATION.md
- docs/project/Guide_complet_SIA_380_2_et_SIA_4010_FR.docx

Méthode obligatoire :
1. fais une inspection ciblée ;
2. présente un plan court et les risques ;
3. implémente seulement ce qui est prouvé ;
4. ajoute ou adapte les tests ;
5. exécute les tests pertinents ;
6. termine par : résultat, fichiers modifiés, tests exécutés, limites, action VE exacte à faire par Ulysse.

Les tests nécessitant iesve ne peuvent être déclarés qualifiés qu'après exécution réelle dans VEScripts. Si tu ne peux pas lancer VE, produis un launcher sûr et l'instruction d'exécution, puis arrête le statut à READY_FOR_REAL_VE_QUALIFICATION.
```

## 3. Ordre recommandé

Exécuter les prompts 0 à 3 en premier. Ensuite 4 à 9. Terminer par 10 et 11. Une nouvelle tâche Claude par prompt. Ne passer au prompt suivant que lorsque le précédent retourne soit `COMPLETE`, soit `BLOCKED_BY_EXTERNAL_EVIDENCE` avec un contournement documenté.

---

## Prompt 0 — Assainir le contrat Claude du dépôt

Modèle : **Opus 4.7**  
Effort : **high**  
Budget : faible

```text
[COLLER L'EN-TÊTE COMMUN]

TÂCHE UNIQUE : corriger le contrat de travail Claude sans modifier le code fonctionnel.

Le CLAUDE.md actuel contient notamment un routage de modèles obsolète ou non documenté (« Sonnet 5 », « Opus 4.8 ») et des caractères d'encodage corrompus. Inspecte aussi docs/CLAUDE_REFERENCE.md si présent.

Actions :
1. Corrige uniquement les noms de modèles et l'encodage UTF-8.
2. Remplace le routage par : Opus 4.7 xhigh pour analyse normative/architecture/revue ; Sonnet 4.6 high pour implémentation ; max seulement pour blocage ou revue finale ; Haiku uniquement pour tâches mécaniques non normatives.
3. Préserve toutes les règles réglementaires et de sécurité déjà valides.
4. Vérifie que les chemins et documents cités existent ; signale les références mortes sans inventer de remplacement.
5. N'ajoute pas de système complexe de skills ou d'agents à ce stade.

Critère de fin : diff minimal limité à la documentation de pilotage, encodage propre, aucune modification Python/JSON.
```

---

## Prompt 1 — Audit différentiel et plan de fermeture du MVP

Modèle : **Opus 4.7**  
Effort : **xhigh**

```text
[COLLER L'EN-TÊTE COMMUN]

TÂCHE UNIQUE : établir l'état réel du produit à partir du code et des preuves, pas seulement des anciens documents.

Inspecte les moteurs SIA 380/2, les sept moteurs SIA 4010, les launchers VEScripts, le hub UI, les tests, les fichiers officiels et les artefacts actuellement enregistrés. Recoupe les documents de statut avec le code réel et git diff.

Crée ou actualise docs/project/MVP_COMPLETION_MATRIX.md avec, pour chaque fonctionnalité et chaque cas :
- exigence et source ;
- implémentation existante ;
- test Python ;
- qualification VE réelle ;
- APS/preuve disponible ;
- critère officiel disponible ;
- statut parmi NOT_STARTED, IMPLEMENTED_UNQUALIFIED, READY_FOR_REAL_VE, RESULTS_RECORDED_NO_CRITERION, READY_FOR_OFFICIAL_REVIEW, BLOCKED_BY_EXTERNAL_EVIDENCE ;
- prochain geste minimal.

La matrice doit couvrir :
- SIA 4010 Test 1 : 600, 640, 900, 940, 600FF, 900FF et le cas diagnostic 1E, clairement séparé des six cas normatifs ;
- Test 2 : 2A à 2D ;
- Test 3 : 3A à 3L ;
- Test 4 ;
- Test 5 : quatre variantes ;
- Test 6 ;
- Test 7 ;
- readiness SIA 380/2 : modèle, enveloppe, ventilation, éclairage, confort dynamique, systèmes, résultats APS, comparaison bâtiment de référence et preuves.

Marque explicitement les anciens documents devenus obsolètes depuis la réception des classeurs officiels et de la réponse SIA. N'implémente rien d'autre pendant cette tâche.

Critère de fin : une matrice factuelle, reliée aux fichiers et utilisable comme backlog exécutable.
```

---

## Prompt 2 — Stabiliser la couche VE avant de générer d'autres cas

Modèle : **Sonnet 4.6**  
Effort : **high**  
Passer à Opus 4.7 xhigh seulement si une signature Boost.Python reste ambiguë.

```text
[COLLER L'EN-TÊTE COMMUN]

TÂCHE UNIQUE : rendre la création/reprise des modèles déterministe et sûre dans VE 2025.

Corrige par conception les familles d'erreurs déjà observées :
- valeurs zéro relues par VE comme environ 1e-6 ;
- propriétés optiques/résistances arrondies à 3, 4 ou 5 décimales ;
- variation_profile relu comme ON au lieu de DAY_xxxx ;
- options non reconnues comme solar_reflected_fraction, dhw_unit ou output_HVAC_controllers ;
- types Boost.Python exigeant un objet VECdbConstruction au lieu d'un identifiant str ;
- exécution reprise après import partiel, sans dupliquer pièces ou assets ;
- fenêtres Tkinter interprétées comme un blocage ou un crash.

Objectifs d'implémentation :
1. Introduire une politique centralisée de normalisation/read-back propre à chaque champ VE, avec justification et journalisation, sans tolérance globale permissive.
2. Filtrer les options par capacités réellement exposées avant tout set(). Une option inconnue doit être omise avec WARNING audité si elle est non indispensable, ou bloquer avant mutation si elle est indispensable.
3. Rendre les reprises idempotentes : reuse/verify ou fail-closed avant mutation, jamais duplication silencieuse.
4. Ajouter des tests unitaires avec doubles/fakes reproduisant chaque erreur ci-dessus.
5. Ajouter un probe VEScript court et sûr pour les signatures qui ne peuvent pas être prouvées hors VE.

Ne lance pas une campagne SIA 4010 dans cette tâche. Ne change aucune valeur normative.

Critère de fin : tests Python verts et un launcher de qualification VE donnant des résultats PASS/WARNING/FAIL par capacité, sans crash ni boucle UI.
```

---

## Prompt 3 — Corriger le moteur officiel des critères et des classeurs

Modèle : **Opus 4.7**  
Effort : **xhigh**

```text
[COLLER L'EN-TÊTE COMMUN]

TÂCHE UNIQUE : aligner le moteur d'évaluation sur les derniers classeurs et réponses officielles disponibles.

Éléments confirmés à intégrer comme preuves sourcées :
- Test 7 : le classeur corrigé est C:\Users\ulysse.couliou\Downloads\Resultaterfassung Test7.xlsx ; l'ancienne règle utilisant moyenne/borne haute était une erreur ; la règle corrigée doit utiliser borne basse/borne haute.
- Tests 2, 3 et 5 : pour chaque classe de fréquence, le Streubereich est l'enveloppe min/max des programmes de référence, avec appréciation proportionnée. Ne remplace pas cette règle par moyenne ± écart maximal.
- Les totaux visibles inférieurs à 8760 ne signifient pas nécessairement des heures absentes : certaines heures sont hors limites des classes affichées. Conserver et auditer un compteur hors classe.
- Tests 4, 6 et 7 : les résultats requis sont ceux listés dans leurs classeurs Excel. Réinspecter ces classeurs ; ne maintenir aucune affirmation non prouvée disant que Test 4 ou 6 n'a pas de distribution.

Actions :
1. Comparer le classeur Test 7 corrigé à la copie du dépôt et importer une copie immuable dans la zone officielle prévue, avec checksum et provenance, sans altérer l'original.
2. Corriger les parseurs/contrats/évaluateurs et ajouter des tests de régression sur les bornes basse/haute, enveloppes par bin, heures hors classes et résultats exigés.
3. Ne jamais inventer une tolérance pour Test 1 ou un critère absent : conserver RESULTS_RECORDED_NO_CRITERION.
4. Produire une note de traçabilité citant la réponse SIA et les cellules/règles effectivement lues.

Critère de fin : tous les tests de parsing et de critères passent ; chaque verdict explique la formule, les références et les éventuelles données hors classe.
```

---

## Prompt 4 — Fermer la famille SIA 4010 Test 1

Modèle : **Opus 4.7**  
Effort : **xhigh**

```text
[COLLER L'EN-TÊTE COMMUN]

TÂCHE UNIQUE : finaliser la génération, qualification, simulation et extraction des six cas normatifs ISO 52016/SIA 4010 Test 1 : 600, 640, 900, 940, 600FF, 900FF. Le cas 1E reste diagnostic et ne doit pas être compté comme septième cas normatif.

À préserver : géométrie 8 x 6 x 2,7 m, deux fenêtres sud 3 x 2 m, constructions légères/lourdes, vitrage, gains, infiltration, thermostats, capacités et sorties définis par les sources ISO déjà capturées dans config/iso52016_chapter7_confirmed_inputs.json.

Travail :
1. Vérifier que chaque paramètre source est réellement appliqué et relu dans VE, y compris mobilier/capacité thermique, fraction convective, systèmes idéaux, profils, infiltration et horodatage.
2. Résoudre proprement l'identité du climat Denver DRYCOLD. Les EPW et FWT actuellement comparés ne sont pas identiques ; aucun fichier ne peut être déclaré officiel par ressemblance. Ajouter empreinte, provenance, comparaison horaire et blocage si l'identité exigée n'est pas prouvée.
3. Qualifier la convention des heures/jours pour les tableaux horaires du 4 janvier et du 27 juillet.
4. Produire un orchestrateur séquentiel sûr : préparation d'un projet jetable par cas, création, sauvegarde demandée si nécessaire, simulation ApacheSim, extraction APS, comparaison aux tableaux 28 à 34, ledger checksum.
5. Le système doit reprendre après interruption sans recréer des assets ni réimporter la géométrie.
6. Comme aucune bande d'acceptation officielle n'est prouvée pour les valeurs de référence ISO, enregistrer les écarts mais ne pas convertir la proximité en PASS.

Livrables : launchers VEScripts, rapports par cas, matrice des six cas, tests Python et instructions exactes pour les exécutions réelles dans VE.

Critère de fin hors VE : READY_FOR_REAL_VE_QUALIFICATION pour les six cas. Critère de fin après retours VE : six APS liés et checksum-valides avec sorties complètes, au statut RESULTS_RECORDED_NO_CRITERION ou READY_FOR_OFFICIAL_REVIEW selon les règles réellement disponibles.
```

---

## Prompt 5 — Implémenter et qualifier le Test 2 (2A–2D)

Modèle : **Opus 4.7**  
Effort : **xhigh**

```text
[COLLER L'EN-TÊTE COMMUN]

TÂCHE UNIQUE : rendre exécutables les quatre variantes officielles du SIA 4010 Test 2.

Lis le document et le classeur officiels avant d'écrire du code. Extrais dans un contrat source-tracé : géométrie, orientation, enveloppe, vitrage, protections solaires, calendrier, règles de déclenchement/angle/état, gains, ventilation, thermostats, climat SIA 2028 et résultats exigés.

Implémente :
1. une famille de scénarios 2A–2D sans duplication de logique ;
2. un adaptateur VE capability-aware pour les protections solaires dynamiques ;
3. un read-back prouvant l'état, les seuils et la commande réellement appliqués ;
4. les bindings APS pour toutes les grandeurs et distributions exigées ;
5. l'évaluation annuelle et l'enveloppe min/max par classe de fréquence, avec compteur d'heures hors classes ;
6. les launchers de création, qualification, simulation et reprise ;
7. les tests unitaires, fixtures officielles checksumées et rapports par variante.

Le climat Zurich-Kloten DRY normal SIA 2028 doit être identifié par provenance et empreinte ; un EPW converti sans audit adjacent ne peut pas satisfaire la preuve.

Critère de fin : quatre variantes prêtes pour VE réel puis quatre APS complets et évaluables ; aucune protection solaire approximée ou valeur inventée.
```

---

## Prompt 6 — Implémenter et qualifier le Test 3 (3A–3L)

Modèle : **Opus 4.7**  
Effort : **xhigh**

```text
[COLLER L'EN-TÊTE COMMUN]

TÂCHE UNIQUE : rendre exécutables les douze variantes officielles du SIA 4010 Test 3, consacrées à l'éclairage et à la lumière du jour.

Lis les documents et classeurs officiels. Construis un contrat source-tracé couvrant chaque combinaison 3A–3L : géométrie, vitrage/protections, puissance d'éclairage, profils, capteurs, seuils, gradation/commutation, zones de contrôle, lumière du jour, climat et sorties demandées.

Implémente :
1. une matrice paramétrique 3A–3L ;
2. les bindings VE des gains Lighting et commandes daylight, avec capability checks et read-back ;
3. une erreur bloquante lorsque VE ne permet pas de prouver un capteur ou une commande indispensable ;
4. extraction APS des consommations et distributions requises ;
5. enveloppe min/max des références par classe, compteur hors classe et sommes annuelles ;
6. launchers de campagne/reprise et rapports checksumés ;
7. tests unitaires et tests de cohérence entre contrat, modèle et classeur.

Ne remplace pas les exigences du Test 3 par un simple indicateur SIA 387/4 et ne déduis pas une commande daylight à partir d'un nom de template.

Critère de fin : douze cas générables et qualifiables dans VE, chacun avec preuves de commande et sorties APS exigées.
```

---

## Prompt 7 — Construire le bâtiment d'exemple commun puis le Test 4

Modèle : **Opus 4.7**  
Effort : **xhigh**

```text
[COLLER L'EN-TÊTE COMMUN]

TÂCHE UNIQUE : établir une base exacte et réutilisable du bâtiment d'exemple officiel, puis implémenter le Test 4.

Ne réutilise pas le modèle de référence simple si la géométrie, le zonage ou les systèmes ne correspondent pas au dossier officiel. Inspecte tous les fichiers client/officiels disponibles, mais garde-les en lecture seule.

Étapes :
1. Extraire un manifeste source-tracé du bâtiment d'exemple : pièces, surfaces, ouvertures, orientations, adjacences, templates, calendriers, systèmes et climat.
2. Générer/importer le modèle de façon déterministe, vérifier volumes/aires/adjacences/constructions et produire une empreinte canonique.
3. Implémenter le système et les commandes exacts du Test 4 avec Apache Systems si exigé.
4. Cartographier toutes les sorties listées dans le classeur Test 4, y compris toute distribution réellement présente.
5. Ajouter simulation, extraction APS, évaluateur, reprise et rapports.

Aucune topologie HVAC ne doit être inventée. Si l'API Python ne permet pas de construire un composant requis, produire un probe ciblé ou documenter un gabarit VE source-tracé comme dépendance explicite.

Critère de fin : modèle de base checksumé, Test 4 prêt pour qualification VE, puis APS complet relié aux résultats demandés.
```

---

## Prompt 8 — Implémenter les Tests 5 et 6

Modèle : **Opus 4.7**  
Effort : **xhigh** ; utiliser `max` seulement pour la topologie multizone si xhigh bloque.

```text
[COLLER L'EN-TÊTE COMMUN]

TÂCHE UNIQUE : à partir du bâtiment d'exemple qualifié au prompt précédent, implémenter les quatre variantes du Test 5 et le Test 6.

Pour chaque cas, extrais d'abord le contrat exact depuis les fichiers officiels : systèmes, zones, débits, consignes, récupérations, ventilateurs/pompes, séquences, calendriers et résultats exigés.

Implémente :
1. la topologie multizone et les quatre variantes du Test 5 sans copier-coller de modèle ;
2. la ventilation/commande étagée exacte du Test 6 ;
3. les preuves read-back des débits, séquences et composants ;
4. les sorties APS de chauffage, refroidissement, éclairage, ventilateurs, pompes, auxiliaires et batteries lorsque le classeur les exige ;
5. les sommes annuelles et distributions par enveloppe min/max des références ;
6. les campagnes séquentielles, reprise, ledger et tests.

Un APS où les variables système requises ne sont pas présentes doit rester EVIDENCE_INCOMPLETE. Ne substitue pas une énergie de zone à une énergie de système.

Critère de fin : cinq cas prêts pour VE réel, puis APS et évaluations complètes par cas.
```

---

## Prompt 9 — Implémenter le Test 7 corrigé

Modèle : **Opus 4.7**  
Effort : **max** pour l'analyse initiale, puis **Sonnet 4.6 high** dans une nouvelle tâche pour l'implémentation approuvée.

```text
[COLLER L'EN-TÊTE COMMUN]

TÂCHE UNIQUE : implémenter le Test 7 avec le classeur corrigé et une traçabilité complète du système énergétique.

Analyse d'abord le document officiel et le classeur corrigé. Le critère de feuille Zusammenfassung doit utiliser la borne basse et la borne haute. N'utilise plus l'ancienne formule moyenne/borne haute.

Le contrat doit couvrir : profils de charge, générateurs, courbes de performance, stockage, auxiliaires, commandes, priorités, PV, pas de temps, climat et résultats exigés. Construis des bindings VE/APS explicites et des contrôles d'équilibre énergétique.

Point bloquant à conserver : une divergence de puissance PV a été repérée entre 60,6 kWp et 62,62 kWp. Ne choisis pas une valeur. Cherche si la version corrigée ou une source autorisée tranche ; sinon marque le cas BLOCKED_BY_EXTERNAL_EVIDENCE et rends le choix configurable avec provenance obligatoire.

Implémente après validation du plan :
1. import des profils et contrôle des unités/pas de temps ;
2. performance partielle et stockage/commande ;
3. production PV et auxiliaires ;
4. extraction APS et contrôles de conservation ;
5. comparaison aux bornes corrigées ;
6. launchers, reprise, tests et ledger.

Critère de fin : modèle Test 7 prêt pour qualification réelle, ou blocage limité et précisément documenté à la seule décision externe restante.
```

---

## Prompt 10 — Finaliser le contrôleur de modèles clients SIA 380/2

Modèle : **Opus 4.7**  
Effort : **xhigh**

```text
[COLLER L'EN-TÊTE COMMUN]

TÂCHE UNIQUE : transformer les diagnostics existants en workflow client SIA 380/2 complet, auditable et fail-closed.

Le produit ne doit pas prétendre qu'un bâtiment est conforme à partir de quelques U-values. Il doit séparer : qualité du modèle, données manquantes, calculs vérifiables, résultats de simulation, comparaison au bâtiment de référence et décision finale revue.

Complète ou consolide :
1. extraction des pièces, enveloppe, Uw/g/frame, ponts thermiques, gains, profils, ventilation, éclairage, systèmes, météo et APS ;
2. contrôles SIA 380/2 avec article/source/unité/statut ;
3. confort dynamique seulement si séries APS, météo, ouvrants et métadonnées sont complets ;
4. chauffage/refroidissement et ventilation/éclairage/auxiliaires sans substituer des variables absentes ;
5. puissance de dimensionnement avec procédure 14 jours + jours de calcul si elle est prouvée et disponible ;
6. familles du bâtiment de référence, agrégation annuelle et pondérations uniquement depuis sources confirmées ;
7. import contrôlé de `SIA3802_global_reference_comparison_<project>.csv` pour l'indice global, avec schéma, source, checksum et revue humaine ;
8. assistant de métadonnées/preuves pour transformer les WARNING résolubles en contrôles vérifiables ;
9. rapport JSON, texte et Excel cohérents.

Utilise le projet client jetable ZOER_32_C1_TEST comme cas de non-régression en lecture seule. Ne modifie jamais le modèle client lors d'un audit par défaut.

Critère de fin : le rapport distingue clairement PASS, WARNING, FAIL, NOT_CHECKABLE et les actions correctives ; toute déclaration globale exige la comparaison de référence et les preuves nécessaires.
```

---

## Prompt 11 — Interface, campagne complète et revue de livraison

Modèle : **Sonnet 4.6 high** pour l'implémentation UI, puis **Opus 4.7 xhigh** dans une nouvelle tâche pour la revue finale.

```text
[COLLER L'EN-TÊTE COMMUN]

TÂCHE UNIQUE : intégrer les moteurs désormais stables dans une interface VEScripts utilisable, puis préparer la livraison MVP.

L'interface doit rester compatible avec le Python/Tkinter embarqué de VE, ne jamais masquer les boutons sur un petit écran et ne jamais faire passer mainloop pour un crash.

Fonctions attendues :
1. deux parcours distincts : Audit SIA 380/2 d'un modèle client en lecture seule ; Campagne SIA 4010 sur projets jetables ;
2. navigateur des sept tests, variantes, prérequis, preuves et statuts ;
3. boutons visibles avec fenêtre redimensionnable, scroll vertical, dimensions basées sur l'écran et fermeture sûre ;
4. exécution d'une seule étape VE à la fois, barre d'état, journal, annulation contrôlée et reprise ;
5. blocage avant mutation si projet non jetable, météo/preuve absente ou préflight FAIL ;
6. liens vers rapports et instruction utilisateur exacte après chaque étape ;
7. aucun thread d'arrière-plan ne doit appeler iesve si l'API l'interdit ;
8. campagne complète séquentielle, mais avec points de sauvegarde entre les cas pour éviter les crashes VE.

Ajoute des tests de logique UI hors VE et un probe réel minimal. Puis, dans une nouvelle tâche Opus :
- audite le diff complet ;
- exécute la suite de tests ;
- vérifie la matrice de traçabilité ;
- recherche les PASS non justifiés, valeurs magiques, sources manquantes et chemins absolus ;
- prépare docs/project/MVP_HANDOFF.md avec installation sans droits admin, parcours de démonstration, limitations et checklist de qualification VE.

Critère de fin : démonstration reproductible depuis Run_VE_Swiss_Compliance_Hub.py, sans certification abusive et avec limitations explicites.
```

## 4. Prompt court à utiliser après chaque sortie réelle de VE

Modèle : **Sonnet 4.6**  
Effort : **high**

```text
Voici la sortie réelle de VEScripts et, le cas échéant, le chemin du rapport JSON/APS. Analyse d'abord le dernier échec vérifiable. Ne relance pas une refactorisation générale. Identifie si la cause est : modèle, donnée/source, signature iesve, read-back/arrondi, simulation, binding APS ou critère officiel. Corrige la cause minimale, ajoute un test de régression hors VE, puis donne-moi un seul script exact à relancer. Préserve le worktree et ne déclare aucun PASS sans nouvelle preuve VE.

[COLLER ICI LA SORTIE ET LES CHEMINS]
```

## 5. Discipline pour économiser les tokens

1. Une tâche Claude par prompt, jamais l'ensemble du projet dans une seule conversation.
2. Donner d'abord les chemins des rapports, pas leur contenu intégral ; demander à Claude de les ouvrir.
3. Après une heure ou un gros changement, demander un handoff court dans `docs/project/handoffs/` puis ouvrir une nouvelle tâche.
4. Utiliser Sonnet pour exécuter un plan déjà validé ; réserver Opus aux décisions difficiles.
5. Ne pas demander à Claude de « tout améliorer ». Toujours imposer un périmètre, des fichiers et un critère de fin.
6. Après chaque exécution VE, corriger un seul blocage à la fois.

