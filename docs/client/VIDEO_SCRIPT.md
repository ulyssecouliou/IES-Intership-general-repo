# Script vidéo client — Évaluation SIA 380/2 dans IESVE

**État du document :** vérifié par rapport au produit au 28 août 2026

**Voix off :** français

**Interface filmée :** anglais par défaut, avec démonstration du changement de langue

**Durée cible :** 12 à 15 minutes

**Lanceur client unique :** `Run_VE_Swiss_Compliance.py`

> [!IMPORTANT]
> Le produit réalise une **évaluation technique SIA 380/2** du projet VE actif.
> Il ne délivre ni certificat officiel SIA, ni décision cantonale, ni validation
> SIA 4010 du logiciel.

## 1. Message que la vidéo doit faire comprendre

À la fin de la vidéo, le client doit avoir compris que l’outil :

1. lit le modèle VE ouvert et les résultats ApacheSim disponibles ;
2. automatise les contrôles que l’API permet d’établir ;
3. demande des preuves pour les informations que VE ne peut pas prouver seul ;
4. conserve le nom du reviewer, la date et la source de chaque preuve ;
5. produit un PDF de synthèse et un classeur Excel d’audit ;
6. affiche `NOT_DETERMINED` lorsqu’une information décisive manque, au lieu de
   transformer l’inconnu en conformité ;
7. n’apporte aucune modification silencieuse au modèle VE.

Les termes ci-dessous doivent être expliqués clairement :

| Terme | Signification à donner au client |
|---|---|
| `pending` | La preuve est préparée mais n’a pas encore été acceptée. |
| `accepted` | Une personne identifiée a vérifié la ligne, sa source et son périmètre, puis en assume la responsabilité. |
| `COMPLIANT` | Les portes de décision implémentées sont fermées favorablement dans le périmètre documenté. Des réserves non décisives peuvent rester visibles. |
| `NOT_COMPLIANT` | Une exigence déterminée ou la comparaison globale a échoué. |
| `NOT_DETERMINED` | Une donnée ou une preuve nécessaire manque encore. Ce statut n’affirme pas que le bâtiment est non conforme. |
| SIA 4010 | Campagne de qualification du logiciel par cas de test ; elle ne constitue pas le rapport d’un bâtiment client. |
| Certification officielle | Décision d’une autorité compétente ; elle reste extérieure à l’outil. |

## 2. Narration recommandée : deux passages, pas un faux résultat vert

La meilleure démonstration montre le fonctionnement réel du produit en deux
passages :

1. **Premier passage :** générer le rapport avec les données disponibles. Montrer
   que le résultat reste `NOT_DETERMINED` lorsque les preuves sont incomplètes.
2. **Revue :** ouvrir **Project Evidence**, compléter uniquement les preuves
   réelles, et expliquer quelles corrections doivent être réalisées dans VE.
3. **Deuxième passage :** après correction du modèle, nouvelle simulation et
   acceptation des preuves, régénérer les rapports et montrer le nouveau verdict.

Si le calcul de référence ou une autre preuve décisive n’est pas terminé, ne pas
filmer un statut `COMPLIANT` artificiel. Le comportement fail-closed est une
fonction du produit à montrer, pas un défaut à dissimuler.

## 3. Préparation avant l’enregistrement

### 3.1 Projet à utiliser

Utiliser une copie synthétique sans données client confidentielles. Idéalement,
enregistrer une copie propre sous un nom neutre comme `SIA3802_CLIENT_DEMO`.
Si la vidéo utilise le projet actuel, conserver son nom exact :
`SIA_compatible_model_TEST_before_heating_fix`.

Le nom du dossier actif est important : il détermine l’identifiant du projet et
les fichiers de preuves chargés dans `sia4010_evidence/`.

### 3.2 État technique nécessaire

- [ ] Le projet VE est enregistré, et non ouvert depuis une copie temporaire.
- [ ] Les pièces thermiques, constructions, fenêtres et systèmes sont visibles.
- [ ] ApacheSim a été relancé après la dernière modification du modèle.
- [ ] Le fichier APS retenu correspond bien aux entrées actuelles.
- [ ] La vue Model Viewer est propre et correctement cadrée.
- [ ] Les documents sources utilisés dans la démonstration existent réellement.
- [ ] La personne déclarée comme reviewer a réellement effectué la revue.
- [ ] Les anciens PDF et classeurs sont fermés.
- [ ] Les notifications Windows et les données personnelles sont masquées.
- [ ] Le dossier `SIA Compliance Reports` est accessible en écriture.

### 3.3 Valeurs observées dans le premier rapport du modèle actuel

Ces valeurs servent à commenter le premier passage ; elles ne doivent pas être
présentées comme une configuration générique applicable à tous les clients.

| Élément | Valeur observée |
|---|---|
| Projet | `SIA_compatible_model_TEST_before_heating_fix` |
| Météo active | `CHE_GVE_2060_RCP85_DRY.epw` |
| Pièces | 3 |
| Surface analysée | 50 m² |
| Volume analysé | 140 m³ |
| Système | `SYST0000` |
| Débit spécifique observé | 7.25 m³/(h·m²) |
| Protection solaire déclarée | `NO` |
| Fenêtres ouvrables déclarées | `YES` |
| Refroidissement mécanique | `TO_CONFIRM` |
| Premier verdict | `NOT_DETERMINED` |

Le premier rapport conclut déjà favorablement sur l’enveloppe, les ouvertures,
les gains, les consignes et le HVAC dans le périmètre automatisé. Il reste
indéterminé principalement à cause de la comparaison globale, de la commande de
ventilation et de la provenance climatique.

### 3.4 Contexte professionnel à saisir dans l’interface

| Champ | Valeur recommandée pour la vidéo interne |
|---|---|
| Client name | `IES — Internal product demonstration` |
| Project name | Nom exact du dossier VE actif |
| Project address | `Synthetic assessment model — no client address` si le modèle est réellement synthétique |
| Contact details | Équipe ou personne IES qui présente le produit |
| Report reference | `SIA3802-DEMO-2026-08-28` |
| Prepared by | Nom réel du présentateur |
| Report language | `English`, puis passage momentané à `Français` |
| Solar shading | Valeur réellement applicable au modèle |
| Operable windows | Valeur réellement applicable au modèle |
| Mechanical cooling | `TO_CONFIRM` tant que la présence et le périmètre du froid ne sont pas prouvés |
| Strategy notes | Description factuelle avec référence au document de conception |

## 4. Script parlé, écran par écran

### Séquence 0 — Titre et promesse (15 secondes)

> **ÉCRAN :** titre « SIA 380/2 engineering assessment in IESVE », logo IES,
> puis transition vers IESVE.

> **VOIX OFF :**
> « Cette démonstration présente l’outil IES d’évaluation technique SIA 380/2.
> À partir du projet IESVE actif, de ses résultats ApacheSim et des preuves revues
> par l’équipe projet, il produit un rapport client lisible et un classeur d’audit
> détaillé. »

### Séquence 1 — Expliquer la portée et la sécurité (30 secondes)

> **ÉCRAN :** IESVE ouvert sur le modèle.

> **VOIX OFF :**
> « L’outil ne délivre pas une certification officielle. Il fournit une
> évaluation d’ingénierie traçable. Sa logique est fail-closed : lorsqu’une donnée
> décisive manque, le résultat est `NOT_DETERMINED`, jamais un faux résultat
> conforme. Le script client fonctionne en lecture seule et ne modifie pas le
> modèle VE. »

### Séquence 2 — Vérifier le projet avant le lancement (45 secondes)

> **ACTION :** montrer le nom du projet, Model Viewer, les trois pièces, puis le
> dossier Vista contenant un APS récent.

> **VOIX OFF :**
> « Le contrôle porte toujours sur le projet VE actuellement ouvert. Je vérifie
> son nom, les pièces thermiques, l’enveloppe, les ouvertures, les systèmes et la
> présence d’un APS cohérent avec la dernière version du modèle. Si une entrée VE
> a changé depuis la simulation, je relance ApacheSim avant de générer le
> rapport. »

> **À MONTRER :** le projet est enregistré ; ne pas ouvrir ou modifier de scripts
> internes SIA 4010 pendant la démonstration client.

### Séquence 3 — Lancer l’interface client (30 secondes)

> **ACTION :** dans Python Scripts Navigator, exécuter
> `Run_VE_Swiss_Compliance.py`.

> **VOIX OFF :**
> « Voici le lanceur client unique. Il génère uniquement l’évaluation bâtiment
> SIA 380/2. Les scripts SIA 4010 du dépôt servent à la qualification interne du
> moteur et ne font pas partie de ce parcours client. »

> **À MONTRER :** dans le bandeau supérieur, le projet actif, la météo détectée
> et le dossier de sortie.

### Séquence 4 — Présenter l’interface (30 secondes)

> **ÉCRAN :** vue complète de la fenêtre.

> **VOIX OFF :**
> « À gauche se trouvent les informations et les actions de l’évaluation. À
> droite se trouve le résultat du dernier calcul : verdict, compteurs, domaines
> et accès direct aux livrables. Avant la première génération, ce panneau indique
> simplement que l’évaluation n’a pas encore été lancée. »

### Séquence 5 — Compléter Project details et changer de langue (60 secondes)

> **ACTION :** remplir `Client name`, `Project name`, adresse, contact,
> `Report reference` et `Prepared by`. Passer de `English` à `Français`, puis
> revenir à `English`.

> **VOIX OFF :**
> « Ces champs identifient le livrable. Le nom du client et le nom du projet sont
> nécessaires pour générer le rapport ; les autres champs assurent une remise
> professionnelle et traçable. L’anglais est la langue par défaut. L’interface
> et les rapports existent également en allemand, français et italien. Le
> changement de langue est immédiat. »

> **À EXPLIQUER :** le fichier météo est en lecture seule dans cette fenêtre. Le
> fait de le détecter ne prouve pas qu’il convient à la localisation ou au calcul.

### Séquence 6 — Déclarer Model & strategy (60 secondes)

> **ACTION :** montrer les trois choix `Solar shading`, `Operable windows` et
> `Mechanical cooling`, puis `Strategy notes`.

> **VOIX OFF :**
> « Ces déclarations décrivent la stratégie réelle du bâtiment et déterminent
> certains contrôles applicables. Elles ne remplacent ni le modèle ni les
> documents de conception. Je choisis `YES` ou `NO` seulement lorsqu’une preuve
> existe ; sinon je conserve `TO_CONFIRM`. Les notes indiquent le périmètre et la
> source de la stratégie. »

> **À NE PAS FAIRE :** choisir une réponse uniquement pour obtenir une couleur
> verte.

### Séquence 7 — Logo et capture Model Viewer (45 secondes)

> **ACTION :** choisir éventuellement un logo autorisé, cadrer Model Viewer puis
> cliquer sur `Capture Model Viewer`.

> **VOIX OFF :**
> « Le logo est facultatif. La capture Model Viewer documente le modèle évalué.
> IESVE passe brièvement au premier plan pour effectuer la capture, puis
> l’interface revient automatiquement au premier plan. Si la capture automatique
> n’est pas disponible, je peux sélectionner une image manuellement. »

### Séquence 8 — Générer le premier rapport (45 secondes)

> **ACTION :** cliquer sur `Generate compliance report` avant de compléter les
> preuves manquantes.

> **VOIX OFF :**
> « Je lance maintenant une première évaluation. Le logiciel enregistre le
> contexte du rapport, lit VE et l’APS, charge les preuves déjà présentes, exécute
> les contrôles puis génère un PDF et un classeur Excel horodatés. Il ne relance
> pas silencieusement ApacheSim et ne change aucune entrée du modèle. »

> **À MONTRER :** Excel s’ouvre d’abord, puis le PDF. Revenir ensuite à
> l’interface, où les boutons permettent d’ouvrir le PDF, Excel ou leur dossier
> exact.

### Séquence 9 — Expliquer le premier verdict (90 secondes)

> **ÉCRAN :** panneau de résultat, puis page de synthèse du PDF.

> **VOIX OFF :**
> « Le premier résultat est `NOT_DETERMINED`. Cela ne signifie pas que le bâtiment
> a échoué. Cela signifie que le dossier ne permet pas encore une conclusion
> complète. Ici, l’enveloppe, les ouvertures, les gains, les consignes et le HVAC
> sont déjà évalués conformes dans le périmètre automatisé. La ventilation et le
> confort dynamique restent indéterminés, et la comparaison globale du projet
> avec sa référence n’a pas encore été fournie. »

> **À MONTRER DANS LE PDF :**

- le verdict général ;
- les statuts par domaine ;
- l’action prioritaire demandant la comparaison globale ;
- les éléments manquants avec leur responsable et leur preuve attendue ;
- la formulation juridique de l’évaluation technique.

### Séquence 10 — Ouvrir Project Evidence (3 à 4 minutes)

> **ACTION :** revenir à l’interface et cliquer sur `Project Evidence`.

> **VOIX OFF D’INTRODUCTION :**
> « VE ne contient pas toutes les informations nécessaires à une revue SIA. Cet
> éditeur enregistre donc les preuves externes dans le dossier du projet. Les
> valeurs préremplies sont des faits détectés ou des propositions à confirmer ;
> elles ne sont jamais acceptées automatiquement. »

Avant de détailler les onglets, montrer les commandes communes :

- `Previous` et `Next` changent de ligne dans l’onglet actif ;
- `Add` crée une nouvelle ligne et `Delete` retire la ligne affichée ;
- le compteur indique la ligne courante et le nombre total de lignes ;
- `Save` enregistre **l’onglet actif uniquement** ; il faut donc enregistrer
  séparément chaque onglet modifié ;
- `Return to report` ferme l’éditeur et rend le premier plan à l’interface client.

Montrer les sept onglets dans l’ordre :

#### 10.1 Project and climate

> « Cet onglet documente le statut neuf ou existant, la base climatique, la
> localisation et l’altitude, les sources, le reviewer, le registre des
> hypothèses et la portée juridique. Il déclare aussi les périmètres de
> ventilation, d’éclairage et des sorties APS. Le fichier météo doit correspondre
> au fichier actif, mais sa pertinence reste approuvée par le spécialiste énergie. »

Points à montrer :

- `project_id` correspond au dossier VE actif ;
- `review_status` reste `pending` pendant la préparation ;
- `reviewer` est une personne, pas seulement le nom d’une société ;
- `report_use_acknowledgement` doit être
  `ENGINEERING_ASSESSMENT_ONLY` ;
- les valeurs `UNDER_REVIEW` bloquent l’acceptation ;
- le reviewer doit confirmer explicitement sa responsabilité.

#### 10.2 SIA 2024 use mapping

> « Chaque pièce ou template est associé à sa véritable catégorie SIA 2024. La
> catégorie vient du programme des locaux et de la source contrôlée ; elle n’est
> pas devinée à partir du nom de la pièce. »

Pour le modèle actuel, montrer les trois identifiants `SP000000`, `SP000001` et
`SP000002`. Si la revue définit réellement les deux bureaux en `3.01` et le
corridor en `12.03`, saisir ces valeurs avec leur source. Si le modèle conserve
un template de classe `4.01`, expliquer que cette contradiction doit être
corrigée ou justifiée avant acceptation.

#### 10.3 Global comparison

> « Cette comparaison est la porte décisive. Elle utilise le même indice global
> et la même unité pour le projet et le projet de référence. `pass` n’est valable
> que lorsque la valeur projet est inférieure ou égale à la référence. Ces deux
> nombres doivent venir d’un calcul revu ; ils ne sont pas déduits des couleurs
> des contrôles élémentaires. »

Afficher les valeurs fixes :

- `comparison_scope = complete_sia3802_project` ;
- `comparison_metric = global_energy_expenditure_index_sia380`.

Ne pas inventer `project_value` ou `reference_value` pour la vidéo.

#### 10.4 Ventilation control

> « Une ligne documente chaque système ou zone : type mono ou multizone, classe
> de commande, bande de débit, capteurs, plage de variation et périmètre de
> commande. Les valeurs doivent correspondre au système réel. »

Pour le modèle actuel, montrer :

- système `SYST0000` ;
- débit spécifique `7.25 m3/(h.m2)` ;
- bande `GT_6` ;
- trois pièces couvertes.

Expliquer que `one_speed_time_schedule` ne suffit pas si le système est réellement
`multizone` dans la bande `GT_6`. La limite exige alors une commande à vitesse
variable par capteur de qualité d’air/gaz par zone. Il faut modifier ou prouver la
commande réelle ; il ne faut pas simplement sélectionner `variable_gas_sensor`.

#### 10.5 Cooling generator

> « Si le refroidissement mécanique existe, la classe air ou eau, la puissance et
> l’EER ou le SEER proviennent de la fiche fabricant approuvée. Le programme
> sélectionne ensuite la bande de puissance applicable. Une efficacité générique
> lue dans VE ne suffit pas à prouver la classe normative. »

Pour le modèle actuel, la valeur observée `2.5` et la puissance absente ne doivent
pas être présentées comme une preuve acceptée.

#### 10.6 Lighting control

> « Le logiciel peut détecter des gains ou une gradation, mais la classe de
> commande SIA 387/4 reste une correspondance revue. Chaque ligne doit couvrir
> une pièce ou un template et citer l’étude d’éclairage ou la source de contrôle. »

Préciser que `daylight_control = ON` ne suffit pas, à lui seul, à déterminer la
classe SIA 387/4.

#### 10.7 Electrical power

> « La puissance requise est une puissance de dimensionnement en W par mètre
> carré de surface nette conditionnée. Elle inclut le périmètre applicable des
> ventilateurs, pompes, auxiliaires et du froid, avec le facteur de simultanéité.
> Elle ne doit pas être remplacée sans justification par un pic APS annuel. »

Pour le modèle actuel, montrer `conditioned_area_m2 = 50` et expliquer que la
puissance réelle, le statut du bâtiment et la catégorie de nécessité du froid
doivent venir du calcul et du reviewer.

> **PHRASE CLÉ À DIRE :**
> « Je ne saisis pas une valeur parce qu’elle semble plausible. Je saisis la
> valeur du modèle, du calcul ou de la fiche technique, puis j’indique qui l’a
> vérifiée et où elle peut être retrouvée. »

Sur un onglet représentatif, cliquer sur `Save` et montrer le message indiquant
le nombre de lignes enregistrées et acceptées. Expliquer qu’une ligne demandée
comme `accepted` mais incomplète est automatiquement enregistrée `pending` : le
formulaire ne permet pas de contourner les exigences de preuve.

À la fermeture de l’éditeur, montrer que l’interface principale revient au
premier plan.

> [!NOTE]
> `Run_VE_Swiss_Compliance_Evidence_Wizard.py` est un assistant séparé consacré
> aux métadonnées et à la gouvernance. Le parcours client normal utilise le bouton
> `Project Evidence`, qui donne accès aux sept familles. Ne montrer le launcher
> séparé que si la vidéo doit spécifiquement illustrer la confirmation formelle du
> reviewer ; il ne remplace pas les six autres onglets.

### Séquence 11 — Expliquer ce qui doit être corrigé hors du wizard (60 secondes)

> **ÉCRAN :** `Action Dashboard` ou `Input Request` dans Excel.

> **VOIX OFF :**
> « L’éditeur de preuves ne transforme pas le modèle. Si le contrôle de
> ventilation, le générateur, l’éclairage, la météo ou une autre entrée sont
> incorrects, ils doivent être corrigés dans VE puis simulés à nouveau. Les
> puissances de dimensionnement et la comparaison globale doivent être calculées
> dans leurs workflows dédiés. Le rapport indique pour chaque point l’action, la
> preuve attendue et le responsable. »

Préciser que les valeurs de vitrage `g = 0.50` et `tau_v = 0.70` sont des entrées
du projet de référence. Il ne faut pas modifier le vitrage du client uniquement
pour faire disparaître une alerte de diagnostic ; l’effet doit être évalué dans
la comparaison globale.

### Séquence 12 — Régénérer après correction et revue (45 secondes)

> **ACTION :** après les vraies corrections, la nouvelle simulation et
> l’acceptation des preuves, cliquer à nouveau sur `Generate compliance report`.

> **VOIX OFF :**
> « Après toute modification de VE, je relance ApacheSim. Après toute modification
> des preuves, je régénère le rapport. Les livrables sont horodatés : la vidéo doit
> toujours montrer ceux de l’exécution courante. »

Si le verdict final est `COMPLIANT`, dire :

> « Le dossier satisfait les portes de décision implémentées dans le périmètre
> revu. Les éventuelles réserves restent visibles dans le rapport. Il s’agit
> toujours d’une évaluation technique et non d’une certification officielle. »

Si le verdict reste `NOT_DETERMINED`, dire :

> « Le moteur a terminé son analyse, mais une ou plusieurs preuves décisives
> restent ouvertes. Le rapport fournit la liste exacte des actions nécessaires
> pour continuer. »

### Séquence 13 — Présenter le PDF (75 secondes)

> **ACTION :** parcourir les pages sans annoncer un nombre fixe de pages.

Montrer :

1. la couverture IES, le projet, la météo et les déclarations principales ;
2. le résumé exécutif et le verdict ;
3. les domaines Envelope, Openings, Ventilation, Gains, Setpoints, HVAC et Dynamic ;
4. la comparaison globale projet/référence ;
5. les constats détaillés et leurs actions ;
6. les limites de méthode et les réserves ;
7. la gouvernance : climat, stratégie, sources, hypothèses et reviewer ;
8. la mention juridique finale.

> **VOIX OFF :**
> « Le PDF est conçu pour la décision et la communication. Il montre ce qui est
> établi, ce qui manque, l’impact sur le verdict et l’action attendue. Le contenu
> est dynamique et dépend du modèle et des preuves de l’exécution. »

### Séquence 14 — Présenter Excel (75 secondes)

> **ACTION :** montrer les feuilles suivantes :

- `COVER` et `INDEX` ;
- `CLIENT SUMMARY` ;
- `ACTION DASHBOARD` ;
- `REVIEW GOVERNANCE` ;
- `INPUT REQUEST` ;
- `REFERENCE PROJECT` ;
- `DATA QUALITY` et `ROOMS` ;
- les feuilles techniques utiles au cas analysé.

> **VOIX OFF :**
> « Excel constitue la piste d’audit. Il contient les données extraites, les
> sources, les règles, les constats et les actions. Un reviewer peut ainsi
> comprendre comment la conclusion a été construite et retrouver la preuve
> utilisée. Une couleur seule ne remplace jamais cette traçabilité. »

### Séquence 15 — Conclusion (30 secondes)

> **VOIX OFF :**
> « L’outil transforme un projet VE simulé et un dossier de preuves revu en une
> évaluation SIA 380/2 structurée, traçable et multilingue. Il automatise les faits
> accessibles dans VE, demande explicitement les informations qui nécessitent une
> responsabilité humaine et refuse de conclure lorsque le dossier est
> insuffisant. Il aide l’ingénieur et le reviewer ; la décision officielle reste
> du ressort de l’autorité compétente. »

## 5. Ce qu’il ne faut pas montrer ou affirmer

- Ne pas dire « le logiciel certifie le bâtiment ».
- Ne pas dire « `accepted` signifie conforme » : `accepted` signifie seulement
  que la preuve a été revue.
- Ne pas remplir un reviewer avec `IES` sans nom de personne.
- Ne pas utiliser `DEMO`, `EXAMPLE`, `ILLUSTRATIVE`, `PLACEHOLDER` ou
  `NOT_A_REAL_REVIEW` comme provenance d’une preuve acceptée.
- Ne pas saisir `pass` dans la comparaison globale sans les deux valeurs calculées.
- Ne pas sélectionner une meilleure classe de ventilation que celle réellement
  installée ou modélisée.
- Ne pas accepter `SEER = 2.5` comme conforme sans classe, puissance et source.
- Ne pas déduire une catégorie SIA 2024 uniquement du nom `Office` ou `Corridor`.
- Ne pas déduire une classe SIA 387/4 uniquement de `daylight_control = ON`.
- Ne pas présenter un APS antérieur à la dernière modification du modèle.
- Ne pas montrer les scripts expérimentaux ou la campagne interne SIA 4010 dans
  le parcours client.
- Ne pas promettre un nombre fixe de pages, de feuilles ou de constats.

## 6. Référence rapide des sept onglets Project Evidence

Cette section sert de pense-bête au présentateur. Elle ne doit pas être lue en
entier pendant la vidéo.

### 6.1 Project and climate

Champs obligatoires ou conditionnels à expliquer :

- identité : `project_id`, `building_status` ;
- climat : `weather_basis`, `weather_file`, `location`, `altitude_m`,
  `weather_source_authority`, `weather_use_case`, `weather_scenario_period`,
  `location_source`, `altitude_source` ;
- revue : `review_status`, `reviewer`, `reviewer_role`,
  `reviewer_organisation`, `reviewer_competence_basis`,
  `reviewer_acceptance_scope`, `review_date`, `source_document`,
  `source_reference`, `notes` ;
- hypothèses : `assumptions_status`, `assumptions_register` ;
- portée juridique : `report_use_acknowledgement` avec la valeur exacte
  `ENGINEERING_ASSESSMENT_ONLY` ;
- ventilation : `ventilation_strategy`, `ventilation_justification`,
  `ventilation_flow_source`, `ventilation_scope` ;
- éclairage : `lighting_scope`, `lighting_power_source`,
  `lighting_scope_justification` ;
- sorties systèmes : `system_power_source`, `aps_outputs_required`,
  `aps_outputs_justification`.

Règles essentielles :

- `MECHANICAL_PRESENT` ou `MECHANICAL_EXPECTED` exige une source de débit ;
- `IN_SCOPE` pour l’éclairage exige une source de puissance ;
- `OUT_OF_SCOPE` exige une justification ;
- `aps_outputs_required = YES` exige une source de puissance système ;
- `aps_outputs_required = NO` exige une justification ;
- `UNDER_REVIEW` n’est pas une acceptation finale ;
- `OPEN_ASSUMPTIONS` reste une réserve visible.

### 6.2 SIA 2024 use mapping

Une ligne doit comporter :

- `room_id` ou `thermal_template_id` ;
- `sia2024_category` ;
- `review_status`, `reviewer` ;
- `source_document`, `source_reference`, `notes`.

Toutes les pièces analysées doivent être couvertes, sans doublon contradictoire.

### 6.3 Global comparison

Valeurs fixes :

- `comparison_scope = complete_sia3802_project` ;
- `comparison_metric = global_energy_expenditure_index_sia380`.

Valeurs issues du calcul : `project_value`, `reference_value`, `unit` et
`comparison_result`. Pour être acceptée, la ligne doit avoir un reviewer, une
date, une source et `project_value <= reference_value` lorsque le résultat est
`pass`.

### 6.4 Ventilation control

Une ligne documente : `system_id`, `room_or_zone`, `system_type`,
`control_class`, `airflow_band`, `specific_airflow_m3_h_m2`, la commande de
débit et du ventilateur, le capteur, le périmètre, le minimum, le profil, le
reviewer, la date et la source.

Classes proposées :

- `one_speed_time_schedule` ;
- `two_speeds_time_schedule` ;
- `two_speeds_occupancy` ;
- `variable_occupancy` ;
- `variable_gas_sensor`.

Bandes proposées : `LE_3`, `3_TO_6`, `GT_6`.

### 6.5 Cooling generator

Documenter : `generator_class`, `capacity_kw`, `nominal_eer` et/ou `seer`,
`unit`, reviewer, date et fiche fabricant. La classe est `air_cooled` ou
`water_cooled`. Au moins un EER ou SEER doit être numérique.

### 6.6 Lighting control

Documenter : `room_id` ou `thermal_template_id`, `sia3874_control_type`,
`daylight_control`, reviewer et source. Le type SIA 387/4 doit venir d’une source
contrôlée.

### 6.7 Electrical power

Documenter : `building_status`, `required_electrical_power_w_m2`,
`conditioned_area_m2`, `cooling_present`, `cooling_category`, `unit`, reviewer,
date et note de dimensionnement.

La puissance doit être une valeur non négative en `W/m2`. La catégorie de froid
est `necessary`, `desirable` ou `none`.

## 7. Preuves complémentaires hors des sept onglets

Ne les montrer que si elles s’appliquent au projet filmé :

- protection solaire active :
  `glazing_solar_protection_<project>.csv` ;
- récupération de chaleur et CTA :
  `SIA3802_ahu_heat_recovery_<project>.csv` ;
- ponts thermiques :
  `SIA3802_thermal_bridges_<project>.csv` ;
- justifications revues :
  `SIA3802_justifications_<project>.csv` ou fichier conforme au gabarit.

Ces preuves sont stockées dans `sia4010_evidence/` sous le dossier du projet
actif. Elles nécessitent également un reviewer et une source. Elles ne doivent
pas être copiées depuis un autre projet sans revue.

## 8. Conditions à expliquer pour un verdict COMPLIANT

Le présentateur doit être capable d’expliquer qu’un affichage `COMPLIANT` exige
notamment :

1. un modèle contenant au moins une pièce analysable ;
2. aucun constat déterminé bloquant ;
3. une comparaison globale acceptée et favorable ;
4. une preuve de ventilation complète lorsque la ventilation mécanique
   s’applique ;
5. une preuve de protection solaire lorsque la protection est active ;
6. une puissance électrique évaluée et non bloquante ;
7. un modèle, un APS et des preuves cohérents entre eux ;
8. l’acceptation juridique indiquant que le rapport reste une évaluation
   d’ingénierie.

Le rapport peut afficher `COMPLIANT` avec des réserves techniques visibles. Il ne
doit jamais être décrit comme « parfaitement certifié ».

## 9. Checklist juste avant d’appuyer sur Enregistrer

- [ ] Le projet filmé est synthétique ou autorisé.
- [ ] Le nom du dossier VE et le `project_id` correspondent.
- [ ] Le modèle a été sauvegardé.
- [ ] L’APS est postérieur à la dernière modification du modèle.
- [ ] Les déclarations YES/NO/TO_CONFIRM sont factuelles.
- [ ] La météo détectée est visible, mais son approbation n’est pas présumée.
- [ ] Chaque preuve acceptée a un reviewer réel et une source retrouvable.
- [ ] Aucun marqueur de gabarit ne subsiste dans les preuves montrées.
- [ ] La comparaison globale utilise la même métrique et la même unité.
- [ ] Les deux livrables montrés portent l’horodatage de l’exécution filmée.
- [ ] Le PDF et Excel s’ouvrent correctement.
- [ ] Les quatre langues peuvent être sélectionnées.
- [ ] L’interface revient au premier plan après Model Viewer et Project Evidence.
- [ ] La conclusion orale utilise « évaluation technique », jamais
  « certification officielle ».

## 10. Version courte de la conclusion commerciale

> « IESVE extrait automatiquement les informations techniques disponibles,
> identifie ce qui doit encore être confirmé par l’équipe projet et conserve une
> piste d’audit complète. Le client obtient un résumé lisible pour la décision et
> un classeur détaillé pour la revue. Lorsqu’une preuve manque, l’outil le dit
> explicitement : il privilégie une conclusion défendable plutôt qu’un faux
> résultat vert. »
