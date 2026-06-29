# Plan d'implementation professionnel - Swiss SIA Compliance Checker

## Objectif

Construire un outil IESVE defensible pour verifier la qualite d'un modele VE, extraire les donnees necessaires via l'API `iesve`, lire les resultats Apache/Vista, et produire un dossier de preuve pour SIA 380/2:2022 et SIA 4010:2023.

## Positionnement normatif

- SIA 380/2:2022 definit les calculs dynamiques: besoins, puissances, energie, conditions horaires, donnees climatiques, profils d'usage et comparaison aux exigences/projets de reference.
- SIA 4010:2023 est une ligne directrice de validation des logiciels/methodes pour SIA 380/2. Elle decrit sept tests de validation; elle ne doit pas etre traitee comme une simple liste de seuils projet.
- Le checker doit donc separer:
  - qualite du modele VE;
  - conformite/controle SIA 380/2 du modele;
  - statut de validation SIA 4010 de la methode ou du logiciel.

## Architecture cible

- `iesve_gateway`: seule couche qui appelle directement `iesve`.
- `model_analyzer`: transforme les objets VE en donnees domaine stables.
- `simulation_results`: ouvre les fichiers APS via `ResultsReader`, decouvre les variables, convertit les series en heures/kWh.
- `construction_resolver`: resout constructions, U-values, g-values et couches via `VECdbConstruction`.
- `rules`: regles pures avec resultats `PASS`, `FAIL`, `WARNING`, `UNKNOWN`, `NOT_APPLICABLE`.
- `sia380_checker`: controles SIA 380/2 lies au modele et aux resultats dynamiques.
- `sia4010_checker`: matrice de validation logiciel/methode, avec import futur des fichiers officiels SIA.
- `reporting`: rapport Excel `xlsxwriter`, sans `openpyxl`, avec preuves et hypotheses.

## Priorites techniques

1. Stabiliser l'extraction VE:
   - `VEProject.get_current_project()`;
   - `project.models[0]`;
   - `model.get_bodies(False)`;
   - filtre strict des rooms;
   - `body.get_areas()`, `body.get_room_data()`, `body.get_surfaces()`;
   - `surface.get_areas()`, `surface.get_properties()`, `surface.get_openings()`, `surface.get_constructions()`.

2. Stabiliser les resultats dynamiques:
   - trouver les fichiers APS dans `project.path + "Vista"`;
   - ouvrir par nom de fichier avec `iesve.ResultsReader.open(aps_file_name)`;
   - utiliser `rf.get_variables()` pour identifier les `aps_varname`;
   - convertir les retours numpy avec `.tolist()`;
   - fermer `rf.close()`.

3. Remplacer les placeholders:
   - aucun `PASS` fictif;
   - aucune valeur chauffage/refroidissement inventee;
   - toute donnee manquante doit devenir `UNKNOWN` ou `NOT_CHECKABLE`.

4. Ajouter la tracabilite:
   - source API;
   - unite;
   - hypothese;
   - niveau de confiance;
   - section normative;
   - statut et recommandation.

## Rapport attendu

Onglets minimum:

- `Executive Summary`: scores, risques critiques, perimetre, statut global.
- `Model QA`: erreurs de modele avant conformite.
- `SIA 380-2`: criteres, valeurs projet, valeurs limites/cibles, statut.
- `SIA 4010`: matrice des sept tests et classes de validation.
- `Rooms`: surface, volume, template, HVAC, gains, ventilation.
- `Envelope`: surfaces, constructions, U-values, ouvertures, WWR.
- `Dynamic Results`: chauffage, refroidissement, confort, energie, APS source.
- `Assumptions`: SIA 2024/SIA 2028/valeurs projet/defaults.
- `API Diagnostics`: methodes disponibles, variables APS, erreurs.
- `Audit Log`: version VE, projet, date, fichier APS, chemins, exceptions.

## Definition de "qualite professionnelle"

Un resultat professionnel ne doit jamais masquer l'incertitude. Si la donnee ou le test manque, le rapport doit le dire explicitement, montrer l'impact sur le score de confiance, et expliquer quelle action permet de rendre le point verifiable.

