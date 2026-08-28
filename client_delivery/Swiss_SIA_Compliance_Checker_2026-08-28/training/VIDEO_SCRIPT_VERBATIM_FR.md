# Script vidéo mot pour mot — Modèle SIA 380/2 analysé puis corrigé

- **Modèle filmé :** `SIA_compatible_model_TEST_before_heating_fix`
- **Premier rapport de référence :** `20260828_141738`
- **Langue parlée :** français
- **Interface :** anglais par défaut
- **Durée estimée :** 17 à 20 minutes de narration, hors temps de chargement

Ce document est la version téléprompteur. Les lignes **Action / écran** ne sont
pas prononcées. Seuls les paragraphes introduits par **À dire exactement** sont
lus à voix haute.

## Valeurs à remplacer avant l’enregistrement

Remplacer tous les marqueurs ci-dessous par les valeurs réellement revues. Ne pas
enregistrer la vidéo tant qu’un marqueur subsiste dans une phrase qui sera lue.

| Marqueur | Valeur attendue |
|---|---|
| `<<PRESENTER_NAME>>` | Nom et prénom du présentateur |
| `<<REVIEWER_NAME>>` | Nom et prénom du reviewer responsable |
| `<<BUILDING_STATUS>>` | `new building` ou `existing building`, selon le dossier |
| `<<LOCATION>>` | Localisation ou station approuvée |
| `<<ALTITUDE_M>>` | Altitude documentée en mètres |
| `<<WEATHER_SOURCE>>` | Document ou autorité ayant approuvé la météo |
| `<<WEATHER_REFERENCE>>` | Page, feuille ou référence de la source météo |
| `<<ASSUMPTIONS_REGISTER>>` | Nom et version du registre des hypothèses |
| `<<VENTILATION_SOURCE>>` | Note de calcul ou séquence de commande ventilation |
| `<<LIGHTING_SOURCE>>` | Étude d’éclairage et source SIA 387/4 |
| `<<COOLING_CLASS>>` | `air-cooled` ou `water-cooled` |
| `<<COOLING_CAPACITY_KW>>` | Puissance nominale revue |
| `<<COOLING_METRIC>>` | EER ou SEER retenu et sa valeur |
| `<<ELECTRICAL_POWER_W_M2>>` | Puissance électrique de dimensionnement |
| `<<PROJECT_INDEX>>` | Indice énergétique global du projet |
| `<<REFERENCE_INDEX>>` | Indice énergétique global de la référence |
| `<<INDEX_UNIT>>` | Unité commune, par exemple `kWh per square metre per year` |

## 1. Ouverture

### Action / écran — 00:00

Afficher une diapositive avec le logo IES et le titre :
`SIA 380/2 engineering assessment in IESVE`.

### À dire exactement

> « Bonjour. Je m’appelle <<PRESENTER_NAME>>, et je vais vous présenter l’outil
> IES d’évaluation technique SIA 380/2 intégré à IESVE. »

> « Nous allons partir d’un modèle déjà simulé mais dont le dossier de preuves
> est encore incomplet. Nous générerons un premier rapport, nous examinerons les
> éléments manquants, puis nous expliquerons comment corriger le modèle et
> compléter les preuves avant de générer une nouvelle évaluation. »

> « L’objectif n’est pas de produire artificiellement un résultat vert. L’objectif
> est d’obtenir une conclusion traçable, compréhensible et défendable. »

## 2. Portée du produit

### Action / écran — 00:30

Passer de la diapositive à IESVE ouvert sur le modèle.

### À dire exactement

> « Avant de commencer, je précise la portée du produit. Cet outil fournit une
> évaluation d’ingénierie fondée sur le modèle VE, les résultats ApacheSim et les
> preuves acceptées par un reviewer identifié. »

> « Il ne délivre pas un certificat officiel SIA, il ne remplace pas une décision
> cantonale, et il ne remplace pas la responsabilité du professionnel qui valide
> les données du projet. »

> « Le moteur applique une logique fail-closed. Lorsqu’une donnée nécessaire
> manque, il affiche `NOT_DETERMINED`. Il ne transforme jamais une information
> inconnue en conformité. »

> « Le lanceur client analyse le projet en lecture seule. Il ne modifie pas les
> pièces, les constructions, les systèmes ou les paramètres de simulation. »

## 3. Présenter le modèle analysé

### Action / écran — 01:15

Montrer le nom du projet, Model Viewer, les trois pièces et le dossier Vista.

### À dire exactement

> « Le projet actif s’appelle
> `SIA_compatible_model_TEST_before_heating_fix`. Il s’agit ici d’un modèle de
> démonstration, et non d’un projet client confidentiel. »

> « Le modèle contient trois pièces thermiques : `Office_01`, `Corridor_01` et
> `Office_02`. Leur surface totale analysée est de cinquante mètres carrés et leur
> volume total est de cent quarante mètres cubes. »

> « Le système Apache détecté porte l’identifiant `SYST0000`. Le fichier météo
> actif est `CHE_GVE_2060_RCP85_DRY.epw`. À ce stade, le nom du fichier est un fait
> technique détecté par VE ; sa pertinence climatique n’est pas encore une preuve
> acceptée. »

> « Avant chaque analyse, je vérifie que le projet est enregistré et que le
> fichier APS est postérieur à la dernière modification du modèle. Si une entrée
> VE a changé, je relance ApacheSim avant de continuer. »

## 4. Lancer l’interface client

### Action / écran — 02:00

Ouvrir Python Scripts Navigator et lancer `Run_VE_Swiss_Compliance.py`.

### À dire exactement

> « Dans Python Scripts Navigator, je lance
> `Run_VE_Swiss_Compliance.py`. C’est le lanceur destiné au rapport bâtiment
> client SIA 380/2. »

> « Les scripts dont le nom contient SIA 4010 appartiennent à la campagne interne
> de qualification du logiciel. Ils ne font pas partie de ce parcours client. »

> « Le bandeau supérieur confirme le projet actif, la météo détectée et le dossier
> dans lequel les rapports seront générés. »

## 5. Présenter l’interface principale

### Action / écran — 02:30

Montrer la fenêtre entière, puis le formulaire à gauche et le panneau de résultat
à droite.

### À dire exactement

> « L’interface est divisée en deux zones. À gauche, je renseigne le contexte du
> rapport, la stratégie du bâtiment, les images et les preuves. À droite, je vois
> le résultat de la dernière exécution et les liens vers les livrables. »

> « Avant le premier calcul, le panneau de droite indique simplement que
> l’évaluation n’a pas encore été générée. »

## 6. Remplir Project details

### Action / écran — 02:55

Saisir les valeurs suivantes :

- `Client name` : `IES — Internal product demonstration` ;
- `Project name` : `SIA_compatible_model_TEST_before_heating_fix` ;
- `Project address` : `Synthetic assessment model — no client address` ;
- `Contact details` : `IES Swiss compliance development team` ;
- `Report reference` : `SIA3802-DEMO-2026-08-28` ;
- `Prepared by` : `<<PRESENTER_NAME>>`.

### À dire exactement

> « Je commence par identifier le livrable. Je renseigne le client, le nom exact
> du projet, une description du site, le contact, une référence documentaire et
> la personne qui prépare le rapport. »

> « Le nom du client et le nom du projet sont nécessaires pour lancer la
> génération. Les autres champs permettent d’obtenir un document professionnel
> et traçable. »

> « Le champ `Prepared by` identifie l’auteur du rapport. Il ne remplace pas le
> reviewer qui accepte les preuves techniques. »

## 7. Montrer les quatre langues

### Action / écran — 03:30

Passer de `English` à `Français`, parcourir brièvement l’interface, puis revenir à
`English`.

### À dire exactement

> « L’anglais est la langue par défaut. L’interface et les rapports sont également
> disponibles en allemand, français et italien. »

> « Le changement de langue est immédiat et conserve les informations déjà
> saisies. Pour cette démonstration, je reviens ensuite à l’anglais afin de
> générer le livrable client par défaut. »

## 8. Expliquer Model and strategy

### Action / écran — 04:00

Montrer les valeurs actuelles :

- `Solar shading = NO` ;
- `Operable windows = YES` ;
- `Mechanical cooling = TO_CONFIRM`.

### À dire exactement

> « Cette section décrit la stratégie réelle du bâtiment. Pour le premier
> passage, le modèle déclare qu’il n’y a pas de protection solaire, que les
> fenêtres sont ouvrables et que la présence exacte du refroidissement mécanique
> reste à confirmer. »

> « `TO_CONFIRM` est un choix volontairement prudent. Il indique que le dossier
> n’est pas encore assez complet pour répondre oui ou non. »

> « Une déclaration ne remplace jamais le modèle ou la preuve de conception. Je
> ne sélectionne pas une valeur simplement pour changer la couleur du rapport. »

> « Dans `Strategy notes`, j’indique toujours le périmètre de la stratégie et la
> référence au document qui la décrit. »

## 9. Ajouter les éléments visuels

### Action / écran — 04:35

Choisir éventuellement un logo autorisé, cadrer Model Viewer, puis cliquer sur
`Capture Model Viewer`.

### À dire exactement

> « Je peux ajouter un logo client autorisé. Cette étape est facultative. »

> « Je capture ensuite Model Viewer afin que le rapport montre clairement le
> modèle évalué. IESVE passe brièvement au premier plan pendant la capture, puis
> l’interface du rapport revient automatiquement au premier plan. »

> « Si la capture automatique n’est pas disponible, je peux sélectionner une
> image manuellement. »

## 10. Générer le premier rapport

### Action / écran — 05:00

Cliquer sur `Generate compliance report`.

### À dire exactement

> « Je génère maintenant le premier rapport, avant de compléter les preuves
> manquantes. Ce premier passage est important, car il montre exactement ce que
> l’outil peut établir à partir du dossier actuel. »

> « Le moteur enregistre le contexte du rapport, extrait les données VE, choisit
> les résultats APS disponibles, charge les preuves du projet, exécute les règles
> et génère deux fichiers horodatés : un classeur Excel et un PDF. »

> « Le logiciel n’exécute pas silencieusement une nouvelle simulation et ne
> corrige pas le modèle à notre place. »

### Action / écran

Attendre l’ouverture d’Excel puis du PDF, puis revenir au panneau de résultat.

### À dire exactement

> « Les fichiers ouverts sont ceux de l’exécution courante, et non un alias plus
> ancien. Je peux également les rouvrir avec les boutons `Open Excel`, `Open PDF`
> et `Open folder`. »

## 11. Expliquer le premier verdict

### Action / écran — 05:45

Afficher le panneau de résultat puis le résumé du rapport `20260828_141738`.

### À dire exactement

> « Le premier verdict est `NOT_DETERMINED`. Cela ne signifie pas que le bâtiment
> est non conforme. Cela signifie qu’une conclusion complète n’est pas encore
> défendable avec les informations disponibles. »

> « L’enveloppe est évaluée `COMPLIANT`. Les ouvertures et vitrages sont évalués
> `COMPLIANT`. Les gains internes, les consignes et le domaine HVAC sont également
> évalués `COMPLIANT` dans le périmètre automatisé. »

> « La ventilation reste `NOT_DETERMINED` pour les trois pièces, car le type de
> système et la classe de commande ne sont pas prouvés. »

> « Le domaine dynamique reste `NOT_DETERMINED` parce que la provenance revue de
> la météo, de la localisation et de l’altitude n’a pas encore été fournie. »

> « Enfin, la comparaison globale entre le projet complet et son projet de
> référence est absente. Cette comparaison est la porte décisive de la conclusion
> SIA 380/2. »

> « Le rapport ne masque pas ces manques. Pour chacun d’eux, il indique l’action à
> effectuer, la preuve attendue et la personne responsable. »

## 12. Montrer le premier PDF

### Action / écran — 06:40

Parcourir la couverture, le résumé, les domaines, les constats et la gouvernance.

### À dire exactement

> « La couverture identifie le projet, la météo détectée, le préparateur et les
> déclarations principales. »

> « Le résumé exécutif présente la décision et les domaines évalués. Il permet à
> un responsable de comprendre immédiatement ce qui est établi et ce qui reste à
> compléter. »

> « Les pages techniques montrent les valeurs observées, les références, les
> écarts, la conséquence sur le verdict et l’action recommandée. »

> « Les dernières pages documentent les limites de méthode, les hypothèses, les
> sources, l’identité du reviewer et la portée juridique du rapport. »

> « Le nombre de pages est dynamique. Il dépend du modèle, des preuves et des
> constats de l’exécution. »

## 13. Montrer le premier classeur Excel

### Action / écran — 07:20

Montrer `CLIENT SUMMARY`, `ACTION DASHBOARD`, `REVIEW GOVERNANCE`, `INPUT REQUEST`,
`REFERENCE PROJECT`, `DATA QUALITY` et `ROOMS`.

### À dire exactement

> « Le PDF est le document de synthèse. Le classeur Excel constitue la piste
> d’audit détaillée. »

> « `CLIENT SUMMARY` résume la décision client. `ACTION DASHBOARD` classe les
> actions par priorité. `REVIEW GOVERNANCE` montre les responsabilités et les
> sources manquantes. `INPUT REQUEST` indique les informations à demander au
> client ou aux spécialistes. »

> « `REFERENCE PROJECT` prépare les substitutions du modèle de référence, mais ne
> constitue pas encore son résultat énergétique. `DATA QUALITY` explique la
> qualité et les limites de l’extraction. `ROOMS` présente les pièces analysées. »

> « Une couleur verte ne remplace pas la revue de ces sources. Le classeur permet
> de retrouver la logique de chaque conclusion. »

## 14. Ouvrir Project Evidence

### Action / écran — 08:10

Revenir à l’interface et cliquer sur `Project Evidence`.

### À dire exactement

> « Je vais maintenant examiner les preuves que VE ne peut pas établir seul. Je
> clique sur `Project Evidence`. »

> « Les preuves sont enregistrées dans le dossier `sia4010_evidence` du projet
> actif. Elles restent donc attachées au bon modèle et ne dépendent pas d’un
> chemin absolu vers un autre projet. »

> « Les boutons `Previous` et `Next` permettent de parcourir les lignes. `Add`
> crée une ligne, `Delete` supprime la ligne affichée, et le compteur indique la
> position courante. »

> « Le bouton `Save` enregistre uniquement l’onglet actif. Je dois donc enregistrer
> séparément chaque onglet que je modifie. »

> « Une ligne incomplète demandée comme `accepted` est automatiquement ramenée à
> `pending`. Le formulaire ne permet pas de contourner les exigences de preuve. »

## 15. Corriger Project and climate

### Action / écran — 08:45

Ouvrir l’onglet `Project and climate`. Remplir uniquement avec les valeurs
réellement revues.

### À dire exactement

> « Le premier onglet documente le statut du bâtiment, la météo, la localisation,
> l’altitude, le reviewer, les hypothèses et le périmètre de l’évaluation. »

> « Le `project_id` correspond automatiquement au dossier VE actif. Pour ce
> projet, le statut revu est <<BUILDING_STATUS>>. »

> « Le fichier actif reste `CHE_GVE_2060_RCP85_DRY.epw`. La localisation approuvée
> est <<LOCATION>> et l’altitude documentée est <<ALTITUDE_M>> mètres. »

> « La source climatique est <<WEATHER_SOURCE>>, à la référence
> <<WEATHER_REFERENCE>>. Je ne déduis jamais la localisation uniquement du nom du
> fichier météo. »

> « Le reviewer responsable est <<REVIEWER_NAME>>. J’indique son rôle, son
> organisation, la base de sa compétence, la portée exacte qu’il accepte et la
> date de revue. »

> « Le registre des hypothèses est <<ASSUMPTIONS_REGISTER>>. Je ne choisis
> `NO_UNRESOLVED_ASSUMPTIONS` que lorsque toutes les hypothèses ouvertes ont
> réellement été fermées. »

> « La portée juridique est enregistrée avec la valeur exacte
> `ENGINEERING_ASSESSMENT_ONLY`. Cela rappelle que le rapport est une évaluation
> technique et non une certification officielle. »

> « La ventilation est déclarée `MECHANICAL_PRESENT`, avec son périmètre et la
> source <<VENTILATION_SOURCE>>. L’éclairage est déclaré `IN_SCOPE`, avec la
> source <<LIGHTING_SOURCE>>. »

> « Les sorties APS nécessaires et la source des puissances systèmes sont
> également documentées. Je passe la ligne à `accepted` seulement après avoir
> vérifié chaque champ et chaque document. »

## 16. Corriger SIA 2024 use mapping

### Action / écran — 10:05

Ouvrir `SIA 2024 use mapping` et montrer les trois pièces.

### À dire exactement

> « Cet onglet associe chaque pièce ou chaque template thermique à sa véritable
> catégorie d’usage SIA 2024. »

> « Les identifiants du modèle sont `SP000000` pour `Office_01`, `SP000001` pour
> `Corridor_01` et `SP000002` pour `Office_02`. »

> « Si le programme des locaux confirme réellement les deux bureaux en catégorie
> `3.01` et le corridor en catégorie `12.03`, je saisis ces catégories avec leur
> feuille source et le reviewer. Je ne les déduis pas seulement des noms des
> pièces. »

> « Si ces pièces utilisent encore un template de classe `4.01`, je corrige le
> template VE ou je documente explicitement la raison de cette différence avant
> d’accepter la correspondance. »

## 17. Examiner Global comparison

### Action / écran — 10:45

Ouvrir `Global comparison`.

### À dire exactement

> « La comparaison globale est la porte décisive. Le périmètre est
> `complete_sia3802_project` et la métrique est
> `global_energy_expenditure_index_sia380`. »

> « La valeur du projet et la valeur de référence doivent provenir de deux calculs
> complets, cohérents, exprimés dans la même unité et revus par la même autorité
> technique. »

> « À ce stade de la première revue, je ne fabrique pas ces valeurs. Je termine
> d’abord le modèle de référence et son calcul. »

## 18. Corriger Ventilation control

### Action / écran — 11:15

Ouvrir `Ventilation control` et parcourir les trois lignes.

### À dire exactement

> « Le modèle expose un débit spécifique de `7.25` mètres cubes par heure et par
> mètre carré pour les trois pièces. La bande applicable est donc `GT_6`. »

> « Le système détecté est `SYST0000`. S’il dessert réellement plusieurs zones,
> je documente le type `multizone`. »

> « Pour un système multizone dans la bande supérieure à six, une simple commande
> une vitesse sur horaire ne suffit pas. La commande conforme à la limite doit
> réellement assurer une vitesse variable pilotée par un capteur de qualité d’air
> ou de gaz au niveau de la zone. »

> « Je ne sélectionne pas `variable_gas_sensor` uniquement pour obtenir un pass.
> Je vérifie ou je corrige d’abord la commande dans VE et dans la séquence de
> contrôle, puis je cite <<VENTILATION_SOURCE>> et je fais accepter la preuve par
> <<REVIEWER_NAME>>. »

## 19. Corriger Cooling generator

### Action / écran — 12:00

Ouvrir `Cooling generator`.

### À dire exactement

> « Le premier rapport a relevé une efficacité générique de `2.5`, mais il ne
> disposait ni de la classe du générateur ni de sa puissance nominale. Cette
> valeur ne suffit donc pas à établir la conformité. »

> « Le générateur revu est de type <<COOLING_CLASS>>, sa puissance nominale est de
> <<COOLING_CAPACITY_KW>> kilowatts et la performance retenue est
> <<COOLING_METRIC>>. »

> « Ces informations proviennent de la fiche fabricant approuvée. Le moteur peut
> alors sélectionner la bande de puissance correcte et appliquer le seuil
> correspondant. »

## 20. Corriger Lighting control

### Action / écran — 12:35

Ouvrir `Lighting control`.

### À dire exactement

> « VE détecte une commande lumière du jour active dans les trois pièces, mais
> `daylight control on` ne suffit pas à déterminer une classe SIA 387/4. »

> « J’associe chaque pièce ou template au type de commande réellement défini dans
> l’étude d’éclairage <<LIGHTING_SOURCE>>. J’indique le reviewer et la référence
> exacte de la source avant d’accepter les lignes. »

## 21. Corriger Electrical power

### Action / écran — 13:00

Ouvrir `Electrical power`.

### À dire exactement

> « La surface nette conditionnée du modèle est de cinquante mètres carrés. La
> puissance requise n’est pas une valeur inventée à partir d’un pic annuel : elle
> vient du calcul de dimensionnement des ventilateurs, pompes, auxiliaires et du
> froid, avec le facteur de simultanéité applicable. »

> « La puissance revue est de <<ELECTRICAL_POWER_W_M2>> watts par mètre carré. Je
> documente également le statut du bâtiment, la présence du froid et sa catégorie
> de nécessité, puis je cite la note de calcul. »

## 22. Enregistrer et revenir au rapport

### Action / écran — 13:35

Dans chaque onglet modifié, cliquer sur `Save`. Montrer le message de sauvegarde,
puis cliquer sur `Return to report`.

### À dire exactement

> « J’enregistre chaque onglet modifié. Le message indique le nombre de lignes
> enregistrées et le nombre de lignes réellement acceptées. »

> « Si une ligne reste `pending`, je lis les champs manquants au lieu de forcer son
> statut. »

> « Je clique ensuite sur `Return to report`. L’interface principale revient
> automatiquement au premier plan. »

## 23. Expliquer les corrections effectuées hors du wizard

### Action / écran — 14:00

Montrer VE, puis éventuellement `ACTION DASHBOARD` ou `INPUT REQUEST`.

### À dire exactement

> « Le formulaire documente les preuves, mais il ne transforme pas le modèle. Les
> contrôles de ventilation, les templates, le générateur, l’éclairage et les
> autres entrées incorrectes doivent être corrigés dans VE. »

> « Après ces corrections, j’enregistre le projet et je relance ApacheSim. Le
> nouvel APS doit correspondre exactement au modèle que je vais évaluer. »

> « Les valeurs `g égale zéro virgule cinq` et `tau v égale zéro virgule sept`
> sont des entrées du projet de référence. Je ne modifie pas automatiquement le
> vitrage du client pour faire disparaître une alerte de diagnostic. J’évalue
> l’effet dans la comparaison globale. »

> « Les calculs de puissance de dimensionnement et le calcul du projet de
> référence sont réalisés dans leurs workflows dédiés, puis revus avant d’être
> saisis comme preuves. »

## 24. Compléter la comparaison globale après calcul

### Action / écran — 14:40

Rouvrir `Project Evidence`, onglet `Global comparison`, et saisir les valeurs
réelles.

### À dire exactement

> « Le calcul complet est maintenant disponible. L’indice global du projet est
> <<PROJECT_INDEX>> <<INDEX_UNIT>>. L’indice global du projet de référence est
> <<REFERENCE_INDEX>> <<INDEX_UNIT>>. »

> « Les deux valeurs utilisent le même périmètre, la même métrique et la même
> unité. »

> « Comme la valeur du projet est inférieure ou égale à la valeur de référence,
> je sélectionne `pass`, j’indique le reviewer <<REVIEWER_NAME>>, la date et la
> note de calcul, puis j’enregistre la ligne comme `accepted`. »

> « Si la valeur projet était supérieure à la référence, je sélectionnerais
> `fail`. Je ne modifierais pas le résultat de la comparaison. »

## 25. Générer la seconde évaluation

### Action / écran — 15:20

Revenir à l’interface et cliquer sur `Generate compliance report`.

### À dire exactement

> « Le modèle, l’APS et les preuves sont maintenant cohérents. Je génère une
> seconde évaluation. »

> « Les nouveaux fichiers sont horodatés et n’écrasent pas le rapport initial. La
> comparaison avant et après correction reste donc auditable. »

## 26. Phrase finale selon le verdict obtenu

### Si le verdict est `COMPLIANT`

> « Le verdict est maintenant `COMPLIANT`. Cela signifie que les portes de
> décision implémentées sont fermées favorablement dans le périmètre revu. »

> « Les éventuelles réserves techniques restent visibles dans les livrables. Ce
> résultat reste une évaluation d’ingénierie et non une certification officielle
> SIA. »

### Si le verdict reste `NOT_DETERMINED`

> « Le verdict reste `NOT_DETERMINED`. Une ou plusieurs preuves décisives sont
> encore ouvertes. Le rapport indique précisément lesquelles, ainsi que l’action,
> la source et le responsable attendus. »

> « Je conserve ce statut jusqu’à la fermeture réelle du dossier. »

### Si le verdict devient `NOT_COMPLIANT`

> « Le verdict est `NOT_COMPLIANT`. Le dossier est maintenant suffisamment
> documenté pour identifier une non-conformité déterminée. »

> « Le rapport indique la valeur observée, la référence, l’écart et l’action
> corrective. La prochaine étape est de modifier la conception ou le modèle, puis
> de simuler et d’évaluer à nouveau. »

## 27. Présenter les livrables finaux

### Action / écran — 16:00

Montrer le PDF final et les feuilles Excel principales.

### À dire exactement

> « Le PDF final est destiné à la décision et à la communication. Il présente la
> couverture, le verdict, les domaines, les constats, les actions, les limites et
> la gouvernance. »

> « Le classeur Excel conserve la piste d’audit détaillée : données extraites,
> règles, sources, preuves, hypothèses et résultats. »

> « Les deux documents doivent toujours être remis ensemble. Le PDF résume la
> conclusion ; Excel permet de la reproduire et de la défendre. »

## 28. Conclusion mot pour mot

### Action / écran — 16:30

Revenir à l’interface avec le verdict final visible.

### À dire exactement

> « En résumé, l’outil IESVE automatise les informations techniques accessibles,
> identifie ce qui doit être confirmé par les spécialistes et conserve une piste
> d’audit complète. »

> « Il permet de passer d’un modèle et de données dispersées à une évaluation SIA
> 380/2 structurée, multilingue et compréhensible. »

> « Sa valeur principale est la transparence : lorsqu’une preuve manque, il le
> dit ; lorsqu’une non-conformité existe, il la montre ; et lorsqu’une conclusion
> favorable est possible, il en conserve toutes les sources. »

> « L’outil aide l’ingénieur et le reviewer. La décision officielle reste du
> ressort de l’autorité compétente. Merci. »

## Checklist téléprompteur

- [ ] Tous les marqueurs `<<...>>` ont été remplacés.
- [ ] Les valeurs prononcées correspondent au rapport filmé.
- [ ] Le premier rapport montré est bien `20260828_141738` ou son équivalent
  régénéré avant correction.
- [ ] Le second rapport est postérieur à toutes les corrections et à la nouvelle
  simulation.
- [ ] Aucun nom de client réel ou donnée confidentielle n’apparaît.
- [ ] Le reviewer cité a réellement accepté les preuves.
- [ ] Le verdict prononcé correspond exactement au verdict affiché.
- [ ] Le mot « certification » n’est utilisé que pour expliquer ce que l’outil ne
  fournit pas.
