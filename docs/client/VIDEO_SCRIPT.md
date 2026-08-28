# Script vidéo client — Évaluation SIA 380/2 dans IESVE

**État du document :** aligné sur le produit au 28 août 2026

**Format conseillé :** capture d’écran IESVE + voix off en français

**Durée cible :** 10 à 12 minutes

**Interface montrée :** anglais par défaut, avec démonstration du changement de langue

**Lanceur client :** `Run_VE_Swiss_Compliance.py`

> [!IMPORTANT]
> L’outil produit une **évaluation technique SIA 380/2** fondée sur le modèle VE,
> les résultats APS et les preuves acceptées. Il ne délivre ni certificat officiel
> SIA, ni validation cantonale, ni attestation SIA 4010.

## 1. Ce que la démonstration doit prouver

La vidéo doit montrer quatre choses distinctes :

1. l’extraction en lecture seule des données disponibles dans le projet VE et le
   fichier APS ;
2. la saisie du contexte client et des déclarations propres au projet ;
3. la collecte contrôlée des preuves que VE ne peut pas établir seul ;
4. la génération d’un PDF et d’un classeur Excel avec une décision fail-closed.

Les termes suivants ne doivent pas être confondus :

| Terme affiché | Signification |
|---|---|
| `accepted` | Une ligne de preuve est complète et un reviewer réel en assume la responsabilité. |
| `COMPLIANT` | Le moteur a pu conclure techniquement dans le périmètre SIA 380/2 implémenté. |
| `NOT_COMPLIANT` | Au moins une non-conformité déterminée ou une comparaison contradictoire a été trouvée. |
| `NOT_DETERMINED` | Une preuve ou une donnée décisive manque ; l’inconnu n’est jamais transformé en réussite. |
| Validation SIA 4010 | Qualification du logiciel par des cas de test officiels ; elle ne juge pas un bâtiment client. |
| Certification officielle | Décision d’une autorité ou d’un organisme compétent ; elle n’est pas fournie par ce logiciel. |

## 2. Préparation avant l’enregistrement

Utiliser un projet synthétique dédié à la démonstration, jamais un projet client
confidentiel. Le projet doit être enregistré et avoir été simulé avec ApacheSim.

- [ ] Ouvrir le bon dossier VE et vérifier son nom exact.
- [ ] Vérifier qu’un APS récent correspond aux entrées actuelles du modèle.
- [ ] Préparer les documents sources réellement revus.
- [ ] Faire signer ou accepter les preuves par la personne qui les a effectivement contrôlées.
- [ ] Compléter les sept onglets pertinents de **Project Evidence**.
- [ ] Vérifier que la comparaison globale projet/référence provient d’un vrai calcul.
- [ ] Préparer une vue propre dans Model Viewer.
- [ ] Désactiver les notifications Windows.
- [ ] Fermer les anciens PDF et classeurs pour éviter de montrer un rapport périmé.

> [!WARNING]
> Les textes `DEMO`, `EXAMPLE`, `ILLUSTRATIVE`, `PLACEHOLDER` et
> `NOT_A_REAL_REVIEW` sont volontairement rejetés comme provenance de revue dans
> les métadonnées et la comparaison globale. Les fichiers d’exemple du dépôt
> servent de gabarits : ils ne doivent pas être présentés comme preuves acceptées.
> Cette règle vise les **preuves**, pas la référence descriptive du rapport client.

## 3. Fiche de saisie de la démonstration

Les valeurs ci-dessous peuvent être utilisées dans le **contexte du rapport**.
Elles ne remplacent aucune preuve technique.

| Champ de l’interface principale | Valeur de démonstration conseillée |
|---|---|
| Client name | `IES — Internal presentation` |
| Project name | Le nom exact du dossier VE actif, par exemple `SIA_compatible_model_TEST` |
| Project address | `Synthetic assessment model — no client address` |
| Contact details | Nom ou équipe IES qui présente l’outil |
| Report reference | `SIA3802-DEMO-2026-08-28` |
| Prepared by | Nom réel du présentateur |
| Report language | `English` au lancement ; montrer ensuite le passage vers `Français` |
| Solar shading | `YES`, `NO` ou `TO_CONFIRM` selon le modèle actif et ses preuves |
| Operable windows | `YES`, `NO` ou `TO_CONFIRM` selon le modèle actif et ses preuves |
| Mechanical cooling | `YES`, `NO` ou `TO_CONFIRM` selon le modèle actif et ses preuves |
| Strategy notes | Résumé factuel de la stratégie et référence au document de conception |
| Client logo | Facultatif ; uniquement un fichier autorisé |
| Model Viewer image | Capture automatique, ou image choisie manuellement si la capture échoue |

Ne jamais choisir `YES` ou `NO` uniquement pour obtenir une couleur verte. Si la
stratégie n’est pas démontrée, sélectionner `TO_CONFIRM` : le rapport doit alors
rester prudent.

### État actuel des exemples `SIA_compatible_model_TEST`

Les CSV suivis dans le dépôt ne constituent pas, en l’état, un dossier accepté :

- les métadonnées et la comparaison `280/320` indiquent explicitement qu’elles
  sont illustratives ; le moteur les rejette comme provenance de revue ;
- la ventilation est `pending` et utilise l’ancienne valeur libre
  `demand_controlled`, qui n’est pas une classe acceptée par le formulaire actuel ;
- le générateur de froid est une hypothèse `pending` ;
- l’éclairage contient encore des marqueurs à compléter ;
- la puissance électrique contient encore des marqueurs à compléter.

Pour filmer un statut `COMPLIANT`, ces exemples doivent être remplacés dans le
dossier **du modèle actif** par des valeurs réellement calculées et revues. Il ne
suffit pas de changer `pending` en `accepted` : l’éditeur recalculera l’acceptation
et remettra une ligne invalide à `pending`.

---

## 4. Script parlé, écran par écran

### Séquence 1 — Introduction (30 secondes)

> **ÉCRAN :** titre de la démonstration, puis IESVE.

Bonjour. Cette démonstration présente l’outil d’évaluation technique SIA 380/2
intégré à IESVE. Il analyse un projet VE actif, exploite les résultats ApacheSim,
recueille les preuves qui ne sont pas disponibles dans l’API et produit un rapport
PDF ainsi qu’un classeur Excel traçables.

L’outil applique une logique fail-closed : une donnée manquante produit
`NOT_DETERMINED`, jamais un faux résultat conforme. Le rapport reste une évaluation
d’ingénierie et non une certification officielle SIA.

### Séquence 2 — Ouvrir et contrôler le modèle (45 secondes)

> **ACTION :** ouvrir le projet synthétique enregistré et afficher Model Viewer.

Le contrôle porte toujours sur le projet VE actuellement ouvert. Avant de lancer
l’outil, je vérifie le nom du dossier, la géométrie, les pièces thermiques, les
constructions, les systèmes et la présence de résultats APS cohérents avec le
modèle actuel.

Le script client ne modifie pas le modèle. Il lit les données disponibles et
signale explicitement ce qu’il ne peut pas établir.

### Séquence 3 — Lancer l’interface client (30 secondes)

> **ACTION :** ouvrir Python Scripts Navigator et exécuter
> `Run_VE_Swiss_Compliance.py`.

Ce lanceur génère le rapport client SIA 380/2. Les travaux internes de validation
SIA 4010 sont volontairement absents du livrable bâtiment, car ils qualifient le
logiciel et non le projet client.

L’en-tête de l’interface affiche le projet actif, le fichier météo détecté et le
dossier de sortie du rapport.

### Séquence 4 — Compléter le contexte du rapport (60 secondes)

> **ÉCRAN :** section **01 — Project details**.

À gauche se trouve le formulaire ; à droite, le panneau de résultats. Je renseigne
le client, le nom du projet, l’adresse ou la description du site, le contact, la
référence du rapport et la personne qui l’a préparé.

Seuls le nom du client et le nom du projet sont techniquement obligatoires pour
lancer la génération, mais les autres champs sont nécessaires pour un livrable
professionnel et traçable.

L’anglais est la langue par défaut. L’interface et le rapport peuvent basculer en
anglais, allemand, français ou italien. Le changement est immédiat ; ici je passe
en français, puis je reviens en anglais pour générer le rapport client par défaut.

Le fichier météo affiché est lu depuis VE. Cette détection est un fait technique,
pas une approbation de la base climatique.

### Séquence 5 — Déclarer la stratégie du bâtiment (60 secondes)

> **ÉCRAN :** section **02 — Model & strategy**.

Ces trois déclarations décrivent le projet réel : protection solaire, fenêtres
ouvrables et refroidissement mécanique. Elles orientent les contrôles applicables,
mais elles ne remplacent pas les données du modèle ni les documents de conception.

Je choisis une réponse seulement lorsqu’elle est démontrée. Sinon, je laisse
`TO_CONFIRM`. Dans les notes, j’indique le périmètre, le mode de commande et la
référence de la preuve correspondante.

Je peux ajouter un logo client autorisé. Je lance ensuite la capture de Model
Viewer. IESVE passe brièvement au premier plan pour la capture, puis l’interface
revient automatiquement au premier plan. Une sélection manuelle reste disponible
en secours.

### Séquence 6 — Ouvrir Project Evidence (2 à 3 minutes)

> **ACTION :** cliquer sur **Project Evidence**.

Ce bouton ouvre l’éditeur de preuves du projet. Il ne s’agit pas du wizard unique
historique : l’éditeur actuel contient sept onglets et enregistre des CSV locaux au
projet dans `sia4010_evidence/`.

1. **Project and climate** : statut du bâtiment, climat, reviewer, hypothèses,
   ventilation, éclairage et sorties de systèmes.
2. **SIA 2024 usage mapping** : correspondance de chaque pièce ou template VE avec
   sa catégorie d’usage SIA 2024.
3. **Global comparison** : comparaison décisive de l’indice énergétique global du
   projet avec celui du projet de référence.
4. **Ventilation control** : type de système, classe de commande et bande de débit.
5. **Cooling generator** : classe, puissance et EER ou SEER du générateur, si le
   refroidissement existe.
6. **Lighting control** : correspondance entre pièce ou template et type de
   commande SIA 387/4.
7. **Electrical power** : puissance électrique de dimensionnement selon le statut
   du bâtiment et la nécessité du refroidissement.

Une ligne demandée comme `accepted` mais incomplète est automatiquement ramenée à
`pending`. L’éditeur ne modifie aucun objet VE. À la fermeture, l’interface client
revient au premier plan.

> **À DIRE PENDANT LA DÉMO :** « Je n’entre pas une valeur parce qu’elle semble
> plausible. Je saisis la valeur du calcul, du modèle ou de la fiche technique, et
> j’indique toujours qui l’a revue et dans quel document elle se trouve. »

### Séquence 7 — Générer l’évaluation (45 secondes)

> **ACTION :** cliquer sur **Generate compliance report**.

L’outil enregistre le contexte du rapport dans le dossier du projet, extrait les
données VE, sélectionne les résultats APS, charge les preuves acceptées, exécute
les contrôles et génère deux livrables horodatés : un PDF et un classeur Excel.

Le temps dépend du modèle. L’outil ne relance pas silencieusement une simulation et
ne modifie pas les entrées VE. Si les entrées ont changé depuis le dernier APS, il
faut d’abord relancer ApacheSim.

Les deux livrables de l’exécution courante s’ouvrent automatiquement. Les boutons à
droite permettent aussi de rouvrir le PDF, le classeur ou leur dossier exact.

### Séquence 8 — Lire la décision dans l’interface (60 secondes)

> **ÉCRAN :** panneau **03 — Assessment result**.

Le bandeau indique `COMPLIANT`, `NOT_COMPLIANT` ou `NOT_DETERMINED`. Les compteurs
distinguent les constats bloquants des constats consultatifs. Les cartes présentent
ensuite le statut de chaque domaine.

`COMPLIANT` signifie que la comparaison globale revue est favorable et qu’aucune
porte autonome ou non-conformité déterminée ne bloque la conclusion. Des réserves
techniques peuvent rester visibles ; elles ne sont jamais masquées.

`NOT_DETERMINED` signifie généralement que la comparaison globale, la preuve de
ventilation, le contrôle de protection solaire, la puissance électrique ou une
autre donnée décisive n’est pas suffisamment documentée.

### Séquence 9 — Présenter les rapports (2 minutes)

> **ACTION :** montrer d’abord le PDF, puis Excel.

Le contenu et le nombre de pages sont dynamiques. Ils dépendent du modèle, des
preuves et du nombre de constats ; il ne faut donc pas annoncer un nombre fixe de
pages ou de findings.

Dans le PDF, je montre :

- la couverture IES et l’identification du projet ;
- le résumé exécutif et la décision ;
- la comparaison globale projet/référence ;
- les statuts par domaine ;
- les constats avec valeur observée, référence, effet et action requise ;
- les réserves, limites d’automatisation et éléments de gouvernance ;
- la mention juridique indiquant qu’il s’agit d’une évaluation technique.

Dans Excel, je montre :

- la couverture et le sommaire ;
- les feuilles de données extraites ;
- les contrôles détaillés et leurs sources ;
- les constats et les preuves utilisées ;
- la traçabilité qui permet à un reviewer de reproduire la conclusion.

Le rapport doit être lu avec ses sources. Une couleur verte seule ne remplace pas
la revue du dossier.

### Séquence 10 — Conclusion (30 secondes)

À partir d’un projet VE simulé et d’un dossier de preuves revu, l’outil transforme
des données dispersées en une évaluation SIA 380/2 structurée, traçable et
multilingue. Il automatise ce qui est exposé par VE, demande explicitement ce qui
nécessite une responsabilité humaine et refuse de conclure lorsque l’information
est insuffisante.

Le résultat aide l’ingénieur à préparer et contrôler le dossier ; la décision
officielle reste du ressort de l’autorité compétente.

---

## 5. Guide exact de tous les champs

### 5.1 Interface principale

| Champ | Contenu attendu | Effet |
|---|---|---|
| `client_name` | Nom réel du client ou de l’entité de démonstration | Obligatoire pour générer |
| `project_name` | Nom exact et stable du projet | Obligatoire ; ne change pas le dossier VE actif |
| `project_address` | Adresse officielle ou description explicite du modèle synthétique | Identification du rapport |
| `client_contact` | Contact responsable du dossier | Traçabilité client |
| `report_reference` | Référence documentaire unique | Traçabilité et versionnage |
| `prepared_by` | Auteur réel du rapport | Ne remplace pas le reviewer des preuves |
| `language` | `en`, `de`, `fr` ou `it` via la liste | Anglais par défaut |
| `weather_file` | Lecture seule depuis VE | Fait technique, pas validation climatique |
| `solar_shading` | `YES`, `NO` ou `TO_CONFIRM` | Active le contexte de protection solaire |
| `window_operability` | `YES`, `NO` ou `TO_CONFIRM` | Contexte du confort dynamique |
| `mechanical_cooling` | `YES`, `NO` ou `TO_CONFIRM` | Contexte des contrôles de froid |
| `building_strategy_notes` | Description factuelle, périmètre et source | Visible dans le rapport |
| `client_logo_path` | PNG/JPG autorisé | Facultatif |
| `model_viewer_image_path` | Capture automatique ou PNG/JPG choisi | Facultatif mais recommandé |

### 5.2 Project Evidence — onglet Project and climate

Le `project_id` est lié au dossier actif. Pour une preuve acceptable, tous les
champs obligatoires ci-dessous doivent être remplis avec des informations réelles.

| Champ | Valeur ou contenu attendu |
|---|---|
| `project_id` | Nom exact du dossier VE actif ; ne pas le modifier. |
| `building_status` | `NEW_BUILDING` ou `EXISTING_BUILDING`, d’après le mandat ou le permis. |
| `weather_basis` | Nom officiel de la base climatique approuvée. |
| `weather_file` | Nom exact du fichier que le reviewer déclare correct ; il doit correspondre au fichier VE détecté. |
| `location` | Commune, coordonnées ou station approuvée ; ne jamais l’inférer du nom du fichier. |
| `altitude_m` | Altitude numérique du projet en mètres. |
| `weather_source_authority` | Organisme ou publication qui fournit le jeu climatique. |
| `weather_use_case` | `SIA3802_COOLING_NEED`, `SIA180_SUMMER_COMFORT`, `HVAC_SIZING` ou `MULTIPLE_REVIEWED_USES`. |
| `weather_scenario_period` | Scénario et période exacts, par exemple présent, 2035 ou 2060 avec le scénario climatique applicable. |
| `location_source` | Adresse officielle, plan, coordonnées ou station approuvée. |
| `altitude_source` | Relevé, géodonnées officielles ou document de projet. |
| `review_status` | `pending` pendant la préparation ; `accepted` uniquement après revue complète. |
| `reviewer` | Nom et prénom de la personne qui assume la revue. |
| `reviewer_role` | Fonction dans la revue technique. |
| `reviewer_organisation` | Organisation au nom de laquelle la preuve est acceptée. |
| `reviewer_competence_basis` | Expérience, mandat ou qualification pertinente. |
| `reviewer_acceptance_scope` | Liste précise des données, hypothèses et parties du projet acceptées. |
| `review_date` | Date réelle au format `YYYY-MM-DD`. |
| `source_document` | Nom du document effectivement contrôlé. |
| `source_reference` | Clause, page, feuille ou identifiant d’approbation ; facultatif mais recommandé. |
| `notes` | Informations utiles sans marqueur de gabarit ou affirmation non prouvée. |
| `assumptions_status` | `NO_UNRESOLVED_ASSUMPTIONS`, `OPEN_ASSUMPTIONS` ou `UNDER_REVIEW`. Le dernier bloque l’acceptation. |
| `assumptions_register` | Nom, version et emplacement du registre des hypothèses, même si aucune hypothèse ne reste ouverte. |
| `report_use_acknowledgement` | Exactement `ENGINEERING_ASSESSMENT_ONLY`. |
| `ventilation_strategy` | `NATURAL_ONLY`, `MECHANICAL_PRESENT`, `MECHANICAL_EXPECTED` ou `UNDER_REVIEW`. |
| `ventilation_justification` | Pourquoi cette stratégie correspond au projet et comment elle est modélisée. |
| `ventilation_flow_source` | Calcul ou document d’origine des débits ; obligatoire pour une ventilation mécanique présente ou attendue. |
| `ventilation_scope` | Systèmes, zones et modes naturels/mécaniques couverts. |
| `lighting_scope` | `IN_SCOPE`, `OUT_OF_SCOPE` ou `UNDER_REVIEW`. |
| `lighting_power_source` | Source des puissances d’éclairage ; obligatoire si `IN_SCOPE`. |
| `lighting_scope_justification` | Frontière et justification ; obligatoire si `OUT_OF_SCOPE`. |
| `system_power_source` | Calcul ou documentation des ventilateurs, pompes, auxiliaires et batteries ; obligatoire si les sorties APS sont requises. |
| `aps_outputs_required` | `YES`, `NO` ou `UNDER_REVIEW`. |
| `aps_outputs_justification` | Justification obligatoire si `aps_outputs_required=NO`. |

Conditions supplémentaires :

- aucune valeur `UNDER_REVIEW` n’est compatible avec une acceptation finale ;
- `OPEN_ASSUMPTIONS` peut être enregistré, mais les hypothèses restent des
  réserves visibles ; pour un dossier entièrement fermé, utiliser
  `NO_UNRESOLVED_ASSUMPTIONS` seulement si c’est vrai ;
- l’acceptation juridique doit rester `ENGINEERING_ASSESSMENT_ONLY` ;
- le nom du reviewer, la date et la source ne doivent jamais être fictifs.

### 5.3 Onglet SIA 2024 usage mapping

Créer une ligne par pièce ou par template thermique. Utiliser `room_id` **ou**
`thermal_template_id`; au moins l’un des deux doit être renseigné.

| Champ | Contenu attendu |
|---|---|
| `room_id` | Identifiant VE exact de la pièce, si la ligne vise une pièce. |
| `thermal_template_id` | Identifiant exact du template, si la ligne couvre toutes ses pièces. |
| `sia2024_category` | Catégorie SIA 2024 revue, par exemple `3.01` uniquement si la source l’établit. |
| `review_status` | `accepted` après contrôle. |
| `reviewer` | Reviewer réel. |
| `source_document` | Données d’utilisation SIA 2024 ou document de programmation contrôlé. |
| `source_reference` | Catégorie, feuille, page ou cellule. |
| `notes` | Explication de la correspondance et des éventuelles exceptions. |

L’objectif est de couvrir toutes les pièces analysées sans doublon contradictoire.

### 5.4 Onglet Global comparison — porte décisive

Cette ligne ne peut pas être inventée à partir des checks élémentaires. Elle doit
venir du calcul complet du projet et de son projet de référence, avec la même
métrique et la même unité.

| Champ | Valeur attendue |
|---|---|
| `project_id` | Projet actif. |
| `comparison_scope` | Exactement `complete_sia3802_project`. |
| `comparison_metric` | Exactement `global_energy_expenditure_index_sia380`. |
| `project_value` | Valeur numérique issue du calcul du projet. |
| `reference_value` | Valeur numérique issue du calcul du projet de référence. |
| `unit` | Unité commune réelle, par exemple `MJ/m2a` ou `kWh/m2a`; ne pas convertir implicitement. |
| `comparison_result` | `pass` uniquement si `project_value <= reference_value`; sinon `fail`. |
| `reviewer` | Reviewer du calcul. |
| `review_date` | Date réelle de revue. |
| `review_status` | `accepted` seulement après contrôle des deux valeurs et du périmètre. |
| `source_document` | Nom/version du calcul signé ou contrôlé. |
| `source_reference` | Feuille, cellule, clause ou identifiant du calcul. |
| `notes` | Méthode, hypothèses communes et périmètre. |

Une ligne marquée `accepted` avec `project_value > reference_value` produit une
non-conformité déterminée. Une ligne avec une provenance de démonstration est
refusée.

### 5.5 Onglet Ventilation control

Créer une ligne par système ou périmètre de commande.

| Champ | Contenu attendu |
|---|---|
| `project_id` | Projet actif. |
| `system_id` | Identifiant ou nom exact du système Apache. |
| `room_or_zone` | Zone ou groupe de pièces couvert. |
| `system_type` | `monozone` ou `multizone`. |
| `control_class` | `one_speed_time_schedule`, `two_speeds_time_schedule`, `two_speeds_occupancy`, `variable_occupancy` ou `variable_gas_sensor`. |
| `airflow_band` | `LE_3`, `3_TO_6` ou `GT_6`. |
| `specific_airflow_m3_h_m2` | Débit spécifique calculé en m³/(h·m²). |
| `unit` | `m3/(h.m2)`. |
| `air_flow_control` | Description du contrôle de débit réellement installé/modélisé. |
| `fan_control` | Commande du ventilateur. |
| `demand_sensor` | Capteur ou signal de demande ; laisser factuel. |
| `control_scope` | `system`, `zone` ou `room`. |
| `minimum_airflow_percent` | Minimum réel de débit, si applicable. |
| `time_schedule` | Profil ou horaire VE exact. |
| `review_status` | `accepted` après vérification. |
| `reviewer`, `review_date` | Responsable et date réels. |
| `source_document`, `source_reference` | Schéma de principe, séquence de commande ou note de calcul. |
| `notes` | Limites et correspondance avec VE. |

La bande déclarée doit être cohérente avec le débit numérique. La valeur libre
`demand_controlled` n’est pas une classe valide : choisir l’une des cinq classes
exactes proposées par l’interface.

### 5.6 Onglet Cooling generator

À remplir uniquement si un générateur de froid fait partie du projet évalué.

| Champ | Contenu attendu |
|---|---|
| `project_id` | Projet actif. |
| `generator_class` | `air_cooled` ou `water_cooled`. |
| `capacity_kw` | Puissance nominale numérique en kW. |
| `nominal_eer` | EER nominal W/W, si disponible. |
| `seer` | SEER déclaré selon sa source, si disponible. |
| `unit` | `EER/SEER=W/W;kW`. |
| `review_status` | `accepted` après comparaison avec la bande applicable. |
| `reviewer`, `review_date` | Responsable et date réels. |
| `source_document`, `source_reference` | Fiche fabricant et référence précise. |
| `notes` | Conditions nominales, norme de déclaration et limites. |

Au moins `nominal_eer` ou `seer` doit être numérique. Si le bâtiment ne comporte
aucun refroidissement, ne pas fabriquer de générateur : déclarer la stratégie
`NO`, compléter correctement la puissance électrique et laisser ce volet non
applicable selon les faits du modèle.

### 5.7 Onglet Lighting control

Créer une ligne par pièce ou template couvert.

| Champ | Contenu attendu |
|---|---|
| `room_id` / `thermal_template_id` | Au moins un identifiant VE exact. |
| `sia3874_control_type` | Type de commande SIA 387/4 confirmé par la source. |
| `daylight_control` | Profil, gradation, capteur ou description de la commande lumière du jour. |
| `review_status` | `accepted` après revue. |
| `reviewer` | Reviewer réel. |
| `source_document`, `source_reference` | Étude d’éclairage, fiche de commande ou clause. |
| `notes` | Correspondance entre la source et la pièce/template VE. |

### 5.8 Onglet Electrical power

La puissance attendue est une puissance de dimensionnement par surface nette
conditionnée. Elle ne doit pas être remplacée par un pic annuel APS sans
justification méthodologique.

| Champ | Contenu attendu |
|---|---|
| `project_id` | Projet actif. |
| `building_status` | `NEW_BUILDING` ou `EXISTING_BUILDING`. |
| `required_electrical_power_w_m2` | Valeur numérique non négative en W/m², issue du calcul de dimensionnement. |
| `conditioned_area_m2` | Surface nette conditionnée utilisée au dénominateur. |
| `cooling_present` | `YES` ou `NO`. |
| `cooling_category` | `necessary`, `desirable` ou `none`. |
| `unit` | `W/m2`. |
| `review_status` | `accepted` après contrôle du calcul et de la catégorie. |
| `reviewer`, `review_date` | Responsable et date réels. |
| `source_document`, `source_reference` | Note de dimensionnement et référence. |
| `notes` | Périmètre des ventilateurs, pompes, auxiliaires, batteries et simultanéité. |

Le contrôle utilise le seuil applicable au statut du bâtiment et tient compte de
la catégorie de nécessité du refroidissement. Une puissance absente, une unité
ambiguë ou une catégorie inconnue maintient la conclusion à `NOT_DETERMINED`.

### 5.9 Preuves complémentaires non exposées dans les sept onglets

Certaines preuves restent des CSV contrôlés. Copier le gabarit correspondant dans
le dossier `sia4010_evidence/` **du projet VE actif**, le renommer avec le label
exact du projet, puis remplacer chaque marqueur par une donnée revue.

#### Protection solaire active

Fichier : `glazing_solar_protection_<project>.csv`

Gabarit : `docs/project/templates/glazing_solar_protection_TEMPLATE.csv`

Renseigner au minimum le projet/modèle, la construction ou façade, le nombre de
fenêtres couvertes, le type de protection, la catégorie, la stratégie et les
seuils de commande, le `g_total_with_shading`, le document source, sa référence,
le reviewer et `review_status=accepted`. Le nombre de fenêtres doit être cohérent
avec les ouvertures externes détectées. Une protection active sans type ou commande
documentée maintient la décision à `NOT_DETERMINED`.

#### Récupération de chaleur de la CTA

Fichier : `SIA3802_ahu_heat_recovery_<project>.csv`

Gabarit : `docs/project/templates/SIA3802_ahu_heat_recovery_TEMPLATE.csv`

Renseigner `project_id`, `leakage_class`, `heat_recovery_type`,
`heat_recovery_temperature_efficiency`, les pertes de charge et le SFP lorsqu’ils
sont disponibles, l’unité, le reviewer, la date et la fiche technique source.

#### Ponts thermiques

Fichier : `SIA3802_thermal_bridges_<project>.csv`

Gabarit : `docs/project/templates/SIA3802_thermal_bridges_TEMPLATE.csv`

Renseigner `project_id`, `assessment_method` et soit
`total_psi_chi_w_per_k`, soit `schedule_reference`, puis l’unité, le reviewer, la
date et le calcul source. Une valeur zéro n’est recevable que si elle est
explicitement justifiée et revue.

---

## 6. Wizard de gouvernance séparé

`Run_VE_Swiss_Compliance_Evidence_Wizard.py` ouvre un wizard distinct. Il reprend
les champs de l’onglet **Project and climate**, affiche en lecture seule les faits
détectés et demande une confirmation explicite du reviewer.

Pour qu’il écrive `accepted` :

1. sélectionner `accepted` ;
2. remplir tous les champs obligatoires et toutes les obligations conditionnelles ;
3. éliminer les valeurs `UNDER_REVIEW` ;
4. accepter `ENGINEERING_ASSESSMENT_ONLY` ;
5. cocher la confirmation de responsabilité ;
6. cliquer sur **Validate**, puis **Save evidence**.

Le wizard écrit un CSV et un audit JSON. Il ne modifie pas VE et ne donne pas à
lui seul un verdict `COMPLIANT`.

---

## 7. Ce qui doit être vrai pour afficher COMPLIANT

Remplir des champs ne suffit pas. À l’exécution courante, le moteur exige :

1. au moins une pièce analysée ;
2. aucun finding déterminé de sévérité bloquante ;
3. une comparaison globale acceptée avec `project_value <= reference_value` ;
4. aucune contradiction entre la comparaison et son statut ;
5. une preuve de ventilation complète lorsque la ventilation s’applique ;
6. un contrôle de protection solaire documenté lorsqu’une protection active est présente ;
7. une puissance électrique évaluée et non bloquante ;
8. des entrées VE et un APS cohérents avec le dossier de preuves.

Les autres manques restent visibles comme réserves. Le rapport peut donc afficher
`COMPLIANT` avec réserves, mais jamais masquer une porte autonome incomplète ou une
non-conformité déterminée.

### Ordre recommandé pour obtenir une démonstration honnête

1. corriger le modèle et relancer ApacheSim si nécessaire ;
2. compléter **Project and climate** avec le reviewer réel ;
3. couvrir toutes les pièces dans **SIA 2024 usage mapping** ;
4. renseigner les commandes de ventilation et de protection solaire applicables ;
5. compléter refroidissement, éclairage et puissance électrique selon le périmètre ;
6. calculer puis faire revoir la comparaison globale projet/référence ;
7. relancer `Run_VE_Swiss_Compliance.py` ;
8. lire les éventuels constats restants et les corriger à partir de leur action requise ;
9. régénérer le PDF et Excel après toute modification du modèle ou des preuves.

### Contrôle final avant la vidéo

- [ ] Aucun champ de preuve ne contient un nom fictif ou un marqueur de gabarit.
- [ ] Le reviewer a réellement accepté le périmètre indiqué.
- [ ] Les fichiers sources existent et leurs références sont vérifiables.
- [ ] Les valeurs projet et référence utilisent la même métrique et la même unité.
- [ ] Le statut de chaque stratégie correspond au modèle actif.
- [ ] L’APS a été régénéré après la dernière modification du modèle.
- [ ] Le rapport affiché porte l’horodatage de l’exécution filmée.
- [ ] La conclusion orale dit « évaluation technique », jamais « certification officielle ».
