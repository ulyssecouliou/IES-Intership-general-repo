# Champs du wizard et des preuves projet

## Règle préalable

Il n'existe aucune valeur générique à saisir pour rendre n'importe quel modèle
conforme. Chaque valeur doit correspondre au bâtiment analysé, à une source
contrôlée et à l'acceptation d'une personne responsable.

## Project and climate

Compléter :

- `project_id` et `building_status` ;
- `weather_basis`, `weather_file`, `location`, `altitude_m` ;
- `weather_source_authority`, `weather_use_case`,
  `weather_scenario_period`, `location_source`, `altitude_source` ;
- `review_status`, `reviewer`, `reviewer_role`, `reviewer_organisation` ;
- `reviewer_competence_basis`, `reviewer_acceptance_scope`, `review_date` ;
- `source_document`, `source_reference`, `notes` ;
- `assumptions_status`, `assumptions_register` ;
- `report_use_acknowledgement = ENGINEERING_ASSESSMENT_ONLY` ;
- `ventilation_strategy`, `ventilation_justification`,
  `ventilation_flow_source`, `ventilation_scope` ;
- `lighting_scope`, `lighting_power_source`,
  `lighting_scope_justification` ;
- `system_power_source`, `aps_outputs_required`,
  `aps_outputs_justification`.

## SIA 2024 use mapping

Créer une ligne couvrant chaque pièce ou template avec : `room_id` ou
`thermal_template_id`, `sia2024_category`, reviewer, source, notes et statut de
revue. Ne pas déduire la catégorie uniquement du nom de la pièce.

## Global comparison

Utiliser obligatoirement :

```text
comparison_scope  = complete_sia3802_project
comparison_metric = global_energy_expenditure_index_sia380
```

Ajouter les valeurs réelles `project_value`, `reference_value`, leur unité,
la conclusion, le reviewer, la date et la note de calcul. `pass` n'est valide
que si le projet est inférieur ou égal à la référence.

## Ventilation control

Documenter : système, locaux/zones, type mono/multizone, classe de commande,
bande et débit spécifique, commandes de débit et ventilateur, capteur, portée,
minimum, horaire, reviewer, date et source.

## Cooling generator

Documenter : classe air/eau, puissance nominale réelle, EER et/ou SEER, unité,
fiche fabricant, reviewer et date.

## Lighting control

Documenter : pièce ou template, type exact de commande SIA 387/4, commande de
lumière du jour, reviewer et source. Un état VE `ON` ne suffit pas à établir le
type normatif.

## Electrical power

Documenter : statut du bâtiment, puissance électrique requise en W/m², surface
conditionnée, présence et nécessité du froid, unité, calcul de dimensionnement,
reviewer et date.

## Acceptation

Choisir `accepted` et cocher la confirmation finale uniquement après une revue
réelle. Un nom d'entreprise ou un outil d'IA ne remplace pas le nom de la
personne responsable. Une ligne documentée prouve la traçabilité ; elle ne
constitue pas, à elle seule, une certification SIA.
