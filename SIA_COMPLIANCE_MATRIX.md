# Matrice de conformite SIA 380/2 + SIA 4010

## SIA 380/2:2022 - controles projet

| Domaine | Critere a controler | Donnee IESVE/API | Resultat attendu | Statut implementation |
|---|---|---|---|---|
| Perimetre | Projet VE actif et modele reel | `VEProject.get_current_project()`, `project.models[0]` | Projet et modele identifies | Partiel |
| Geometrie | Pieces, surfaces, volumes, surfaces nettes | `model.get_bodies(False)`, `body.get_areas()` | Rooms exploitables, surface/volume non nuls | En cours |
| Enveloppe | Constructions affectees | `surface.get_constructions()` | Aucune surface critique sans construction | A faire |
| Enveloppe | U-values opaques | `VECdbConstruction.get_u_factor(...)` | Valeur projet et reference connues | A faire |
| Ouvertures | Fenetres/portes, surfaces, WWR | `surface.get_openings()`, `opening.get_properties()` | WWR et surfaces vitrages coherents | En cours |
| Solaire | g-value, protections solaires, commande | `VECdbConstruction.get_g_values()`, donnees shading | Strategie documentee | A faire |
| Usage | Profils personnes/appareils/eclairage | `room_data.get_internal_gains()`, `gain.get()` | Donnees projet ou SIA 2024 documentees | En cours |
| Ventilation | Infiltration, ventilation naturelle/auxiliaire | `room_data.get_air_exchanges()`, `air_ex.get()` | Debits et unites traces | En cours |
| HVAC | Systemes Apache/HVAC assignes | `room_data.get_apache_systems()`, `project.apache_systems()` | Couverture systemes complete | En cours |
| Simulation | Calcul horaire ou plus fin | `ApacheSim.set_options()`, `run_simulation()` | Fichier APS produit | A faire |
| Resultats | Chauffage/refroidissement annuels | `ResultsReader.get_room_results()` ou variables APS | kWh/m2/an avec source APS | A faire |
| Energie | Energie finale/ponderee, sources | `ResultsReader.get_energy_results()` | Energie par usage/source | A faire |
| Confort ete | Heures de depassement | `get_room_results()` temperature + occupation | Heures occupees et seuils | A faire |
| Meteo | DRY SIA 2028 / scenario CH2018 si applicable | `rf.weather_file`, donnees projet | Fichier meteo trace | A faire |

## SIA 4010:2023 - validation methode/logiciel

| Test | Objet | Resultats attendus | Statut checker |
|---|---|---|---|
| 1 | Tests enveloppe EN ISO 52016-1 / ASHRAE 140 | Comparaison aux resultats de reference SIA | NOT_CHECKABLE sans fichiers SIA |
| 2 | Type et regulation protection solaire | Apports solaires, rayonnement transmis, angle lamelles | NOT_CHECKABLE sans fichiers SIA |
| 3 | Regulation eclairage SIA 387/4 | Puissance/energie eclairage, lumiere du jour | NOT_CHECKABLE sans fichiers SIA |
| 4 | Climatisation une piece, systeme a air seul | Debits, ventilateurs, temperatures, chaud/froid | NOT_CHECKABLE sans fichiers SIA |
| 5 | AHU multizone avec recuperation/humidification | Ventilateur, batteries, humidification, pertes | NOT_CHECKABLE sans fichiers SIA |
| 6 | Ventilation trois niveaux avec recuperation | Debits, energie ventilateurs, recuperation | NOT_CHECKABLE sans fichiers SIA |
| 7 | Emission/distribution/stockage/production chaud/froid | Energie totale chauffage/refroidissement | NOT_CHECKABLE sans fichiers SIA |

## Classes de validation SIA 4010

| Classe | Usage | Tests requis |
|---|---|---|
| 1A | Refroidissement besoin + puissance thermique de base sans regulation solaire position soleil | 1 + 2A |
| 1B | Idem avec stores a lamelles | 1 + 2 |
| 2A | Energie eclairage + besoins chauffage/refroidissement sans regulation solaire position soleil | 1 + 2A + 3A-F |
| 2B | Idem avec stores a lamelles | 1 a 3 |
| 3 | Humidification/deshumidification | 1 + 4 a 6 |
| 4A | Puissance liee au systeme + energie chauffage/refroidissement sans stores a lamelles | 1 + 2A + 3A-F + 4 a 7 |
| 4B | Idem avec stores a lamelles | 1 a 7 |
| 5 | Energie chauffage/refroidissement avec profils de besoins existants | 7 |

