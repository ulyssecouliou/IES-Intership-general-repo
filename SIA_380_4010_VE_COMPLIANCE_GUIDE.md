# Guide de conformite SIA 380/2 et SIA 4010 pour modeles IESVE

Version: 2026-06-29  
Projet: Swiss Compliance Checker pour IESVE  
Public cible: developpeur IESVE, manager technique, auditeur modele, ingenieur energie  

## 1. Objectif du document

Ce document sert de base de travail pour comprendre ce qu'il faut controler dans un modele IESVE afin de produire un dossier de conformite defendable vis-a-vis de:

- SIA 380/2:2022, pour les controles projet lies au modele thermique dynamique, aux donnees d'entree, aux resultats et aux indicateurs energetiques.
- SIA 4010:2023, pour la validation de la methode/du logiciel via des tests officiels de reference.

Il ne remplace pas les normes SIA sous licence. Les valeurs et methodes ci-dessous doivent etre verifiees contre les documents officiels, le contexte du projet, le type de batiment, les exigences cantonales et les instructions du client.

## 2. Principe central

Un modele ne doit pas etre declare conforme simplement parce qu'un script a tourne.

Pour etre defendable, le rapport doit distinguer:

| Niveau | Question | Exemple de statut |
|---|---|---|
| Qualite modele | Les donnees VE sont-elles presentes et coherentes ? | PASS, WARNING, MISSING |
| Controle SIA 380/2 | Les valeurs projet respectent-elles les criteres applicables ? | PASS, FAIL, NOT_APPLICABLE |
| Validation SIA 4010 | La methode/le logiciel est-il valide par les tests officiels ? | PASS, FAIL, NOT_CHECKABLE |
| Preuve documentaire | Peut-on prouver la source de chaque valeur ? | EVIDENCE_OK, EVIDENCE_MISSING |

Regle professionnelle: une donnee absente doit produire une alerte explicite, jamais un PASS implicite.

## 3. Etat actuel du checker

Le checker extrait deja:

- pieces VE selectionnees;
- surfaces, ouvertures et surfaces nettes/grosses;
- constructions CDB;
- U-values opaques et vitrees;
- g-values de vitrages;
- WWR par zone;
- gains internes partiels;
- ventilation partielle;
- systemes Apache/HVAC partiels;
- rapport Excel avec alertes brutes, synthese groupee et plan d'action.

Le checker ne couvre pas encore completement:

- resultats dynamiques APS/Vista chauffage/refroidissement;
- energie finale/primaire par usage;
- CO2;
- confort d'ete horaire;
- meteo SIA 2028 / scenarios climatiques;
- ponts thermiques detailles;
- validation officielle SIA 4010 par fichiers de reference.

## 4. Architecture technique recommandee

| Couche | Role | Fichiers actuels |
|---|---|---|
| API Gateway IESVE | Appels directs a `iesve` | `data_extractor.py` |
| Normalisation modele | Objets domaine stables | `model_analyzer.py` |
| Regles | Alertes, severite, categories | `rule_engine.py` |
| SIA 380/2 | Controle du modele/projet | `sia380_checker.py` |
| SIA 4010 | Validation methode/tests | `sia4010_checker.py` |
| Scores | Compliance Score, Health Score | `health_score.py` |
| Reporting | Excel, preuves, action plan | `excel_report.py` |
| Orchestration VE | Script lance par bouton Run | `main.py` |

## 5. Donnees minimales a extraire depuis VE

### 5.1 Projet

| Donnee | Source IESVE cible | Utilisation |
|---|---|---|
| Chemin projet | `VEProject.get_current_project().path` | nommage, logs, audit |
| Modele actif | projet courant / model list | perimetre analyse |
| Version VE | API projet si disponible | tracabilite |
| Fichier meteo | ApacheSim / projet | SIA 380/2, climat |
| Fichiers APS | dossier Vista / resultats | chauffage, froid, confort, energie |

### 5.2 Pieces / zones

| Donnee | Unite | Controle |
|---|---:|---|
| identifiant piece | texte | unicite, preuve |
| nom piece | texte | lisibilite rapport |
| surface | m2 | non nulle, reference intensites |
| volume | m3 | non nul, ventilation |
| template thermique | texte | profils usage |
| conditions de piece | selon API | consignes, horaires |
| systemes HVAC affectes | texte/dict | couverture CVC |

### 5.3 Surfaces opaques

| Donnee | Unite | Controle |
|---|---:|---|
| type surface | wall, roof, floor, etc. | classification |
| surface brute | m2 | WWR, enveloppe |
| surface nette | m2 | U-value opaque moyenne |
| externalite | booleen | enveloppe externe |
| construction id | texte | resolution CDB |
| U-value | W/m2K | comparaison seuil |
| couches / resistances | SI | audit construction |

### 5.4 Ouvertures

| Donnee | Unite | Controle |
|---|---:|---|
| type ouverture | window, door, hole | classification |
| surface | m2 | WWR, surface affectee |
| construction id | texte | regroupement action |
| U-value | W/m2K | performance vitrage/porte |
| g-value | fraction 0-1 | controle solaire |
| SHGC / EN 410 / shading | fraction | a clarifier pour SIA |
| orientation | degres/cardinal | analyse solaire |

### 5.5 Ventilation

| Donnee | Unite | Controle |
|---|---:|---|
| infiltration | ach ou m3/h | qualite modele |
| ventilation naturelle | ach ou m3/h | scenario |
| ventilation mecanique | m3/h, l/s, ach | SIA 380/2 |
| recuperation chaleur | % | systeme |
| horaires | profil | resultats dynamiques |

### 5.6 Gains internes

| Donnee | Unite | Controle |
|---|---:|---|
| occupants | W/m2, personnes, profil | usage |
| eclairage | W/m2 | puissance specifique |
| equipements | W/m2 | gains internes |
| horaires | profil | calcul dynamique |
| source hypothese | texte | SIA 2024/client |

### 5.7 HVAC et energie

| Donnee | Unite | Controle |
|---|---:|---|
| systeme affecte | texte | couverture |
| rendement | fraction | efficacite |
| energie chauffage | kWh/an, kWh/m2a | SIA 380/2 |
| energie froid | kWh/an, kWh/m2a | SIA 380/2 |
| auxiliaires | kWh/an | energie finale |
| sources energie | texte | CO2/primaire |
| emissions | kgCO2/m2a | indicateur |

## 6. Valeurs actuellement implementees dans le checker

Attention: ce tableau documente les valeurs codees aujourd'hui dans `config.py`. Il ne suffit pas a certifier officiellement un modele. Ces seuils doivent etre parametrables par type de batiment, perimetre, canton, version normative et instruction client.

### 6.1 U-values

| Element | Seuil actuel | Unite | Source actuelle |
|---|---:|---|---|
| mur exterieur | 0.24 | W/m2K | `SIA3801_U_VALUES["external_wall"]` |
| toiture | 0.20 | W/m2K | `SIA3801_U_VALUES["roof"]` |
| plancher | 0.24 | W/m2K | `SIA3801_U_VALUES["floor"]` |
| fenetre | 1.30 | W/m2K | `SIA3801_U_VALUES["window"]` |
| porte | 1.50 | W/m2K | `SIA3801_U_VALUES["door"]` |
| pont thermique | 0.05 | W/mK | `SIA3801_U_VALUES["thermal_bridge"]` |

### 6.2 Autres seuils SIA 380/2 actuellement codes

| Critere | Seuil actuel | Unite | Remarque |
|---|---:|---|---|
| ventilation minimale | 0.5 | h-1 | a confirmer selon usage et unite VE |
| rendement HVAC minimal | 0.90 | fraction | placeholder projet |
| puissance eclairage max | 12 | W/m2 | bureau par defaut, a parametrer |
| puissance equipements max | 20 | W/m2 | bureau par defaut, a parametrer |
| part renouvelable min | 0.20 | fraction | indicateur energie |
| energie primaire max | 100 | kWh/m2a | placeholder projet |
| facteur solaire max | 0.60 | fraction | point critique a verrouiller |
| WWR max | 0.30 | fraction | indicateur de controle, pas toujours critere final |

### 6.3 Indicateurs SIA 4010 actuellement codes

Ces seuils sont conserves comme champs techniques, mais SIA 4010 doit d'abord etre traitee comme une validation de methode/logiciel par tests officiels.

| Indicateur | Seuil actuel | Unite |
|---|---:|---|
| besoin chauffage max | 50 | kWh/m2a |
| besoin refroidissement max | 20 | kWh/m2a |
| energie primaire max | 100 | kWh/m2a |
| emissions CO2 max | 20 | kgCO2/m2a |
| renouvelable min | 0.20 | fraction |

## 7. Calculs principaux

### 7.1 U-value moyenne opaque

Pour une piece ou un ensemble de surfaces:

```text
U_moyen = somme(U_i * A_net_i) / somme(A_net_i)
```

avec:

- `U_i` = U-value de la construction opaque;
- `A_net_i` = surface nette opaque;
- exclusion des surfaces dont `A_net_i <= 1e-6`.

Raison: une surface completement vitree peut avoir une surface opaque nette nulle; elle ne doit pas polluer la moyenne des murs opaques.

### 7.2 Window-to-Wall Ratio

```text
WWR = surface_totale_fenetres_exterieures / surface_brute_murs_exterieurs
```

Le checker utilise les fenetres externes normalisees et les murs externes bruts. Les portes et trous ne doivent pas etre melanges aux fenetres sauf decision methodologique explicite.

### 7.3 Surface vitree affectee par construction

```text
A_vitrage_construction = somme(A_ouverture_i)
```

Regroupement actuel dans `ALERT SUMMARY`:

```text
cle = categorie + construction_id + type_objet + regle
```

Exemple:

```text
Openings + STD_EXTW + window + SIA3801_SOLAR_FACTOR
```

### 7.4 Intensite energetique

Pour les resultats dynamiques futurs:

```text
E_specifique = E_annuelle / S_reference
```

avec:

- `E_annuelle` en kWh/an;
- `S_reference` a definir: surface de reference energetique, surface utile, ou surface VE selon instruction projet.

Le choix de `S_reference` doit etre trace dans le rapport.

### 7.5 Emissions CO2

Implementation cible:

```text
CO2_specifique = somme(E_source_j * facteur_CO2_j) / S_reference
```

Les facteurs CO2 actuellement codes sont des placeholders:

| Source | Facteur actuel | Unite |
|---|---:|---|
| electricite | 0.05 | kgCO2/kWh |
| gaz | 0.20 | kgCO2/kWh |
| mazout | 0.25 | kgCO2/kWh |
| bois | 0.02 | kgCO2/kWh |
| solaire | 0.00 | kgCO2/kWh |
| eolien | 0.00 | kgCO2/kWh |
| chauffage urbain | 0.10 | kgCO2/kWh |

Ces facteurs doivent etre remplaces par les sources officielles applicables au projet.

### 7.6 Compliance Score actuel

Le score global est actuellement:

```text
Compliance Score = 0.70 * Score_SIA380 + 0.30 * Score_SIA4010
```

Le score SIA 380/2 est une moyenne ponderee des categories:

| Categorie | Poids actuel |
|---|---:|
| envelope | 0.25 |
| openings | 0.20 |
| ventilation | 0.15 |
| hvac | 0.20 |

Le code contient aussi `energy` et `simulation`, mais le score SIA 380/2 courant ne les integre pas encore tant que les resultats APS ne sont pas stabilises.

### 7.7 Health Score actuel

```text
Health Score = 0.40 * completude + 0.30 * coherence + 0.30 * absence_erreurs_critiques
```

Penalites de donnees manquantes:

| Severite | Penalite actuelle |
|---|---:|
| Critical | 15 |
| High | 10 |
| Medium | 6 |
| Low | 3 |

## 8. Criteres de controle SIA 380/2 a couvrir

### 8.1 Perimetre et tracabilite

| Controle | Statut attendu | Preuve |
|---|---|---|
| projet VE actif identifie | PASS | chemin projet |
| modele et zones selectionnes | PASS | ids pieces |
| version script | PASS | log / hash |
| date de run | PASS | rapport |
| fichier rapport unique | PASS | nom archive |

### 8.2 Geometrie

| Controle | Calcul / verification | Risque |
|---|---|---|
| surface piece > 0 | `area > 0` | intensites fausses |
| volume piece > 0 | `volume > 0` | ventilation fausse |
| surfaces externes presentes | count surfaces externes | enveloppe incomplete |
| ouvertures externes classees | type window/door/hole | WWR faux |
| surfaces nettes coherentes | net <= gross | U moyen faux |

### 8.3 Enveloppe opaque

| Controle | Calcul | Donnee VE |
|---|---|---|
| construction affectee | construction id non vide | `surface.get_constructions()` |
| U-value resolue | U-value numerique | CDB construction |
| U mur | `U <= seuil mur` | `u_factors["iso"]` ou methode choisie |
| U toiture | `U <= seuil toiture` | CDB |
| U plancher | `U <= seuil plancher` | CDB |
| surfaces sans U | alerte MISSING | rapport |

### 8.4 Ouvertures et solaire

| Controle | Calcul | Point a verrouiller |
|---|---|---|
| U fenetre | `U_window <= seuil` | valeur ISO/CIBSE/ASHRAE selon methode |
| U porte | `U_door <= seuil` | classification porte |
| facteur solaire | `g <= seuil` | g-value vs SHGC vs EN 410 |
| protections solaires | actif, profil, seuils | effet store/ombrage |
| WWR | `A_window / A_wall` | indicateur ou critere final ? |

Point critique actuel: le modele client remonte `g = 0.750` sur plusieurs constructions. Avant conclusion definitive, il faut confirmer quelle valeur doit etre comparee:

- `g_value` CDB;
- `g_values["bs_en_410"]`;
- SHGC;
- facteur apres protection solaire;
- facteur saisonnier/effectif dynamique.

### 8.5 Ventilation

| Controle | Calcul | Preuve attendue |
|---|---|---|
| debit extrait | valeur non nulle | API air exchanges |
| unite clarifiee | ach, m3/h, l/s | mapping VE |
| debit minimal | comparaison seuil | seuil par usage |
| recuperation chaleur | rendement | HVAC / Apache |
| horaires | profil associe | template |

### 8.6 Gains internes

| Controle | Calcul | Preuve attendue |
|---|---|---|
| eclairage | W/m2 <= seuil | template thermique |
| equipements | W/m2 <= seuil | template |
| occupants | profil et densite | template/SIA 2024 |
| horaires | profil coherent | Apache profile |

### 8.7 HVAC

| Controle | Calcul | Preuve attendue |
|---|---|---|
| systeme affecte | systeme par zone | Apache systems |
| rendement connu | `eta >= seuil` | system data |
| consignes | chauffage/froid | room conditions |
| ventilation mecanique | debit + horaire | HVAC/Air exchanges |
| auxiliaires | kWh/an | APS/Vista |

### 8.8 Resultats dynamiques

Ces controles sont indispensables pour une conformite complete, mais pas encore finalises dans le script.

| Indicateur | Formule | Source cible |
|---|---|---|
| besoin chauffage | kWh chauffage / surface ref | APS/Vista |
| besoin refroidissement | kWh froid / surface ref | APS/Vista |
| puissance chauffage | max puissance | APS/Vista |
| puissance froid | max puissance | APS/Vista |
| heures surchauffe | heures occupees au-dessus seuil | temperature horaire |
| energie finale | somme par usage/source | resultats systeme |
| energie primaire | finale * facteurs | facteurs officiels |
| CO2 | finale * facteurs CO2 | facteurs officiels |

## 9. SIA 4010: validation methode/logiciel

SIA 4010 ne doit pas etre traitee comme une simple checklist de seuils projet. Elle sert a documenter si la methode de calcul ou le logiciel est valide pour les familles de calcul concernees.

### 9.1 Tests officiels a couvrir

| Test | Objet | Statut actuel |
|---|---|---|
| 1 | enveloppe de base / comparaisons reference | NOT_CHECKABLE |
| 2 | protection solaire et regulation | NOT_CHECKABLE |
| 3 | eclairage et regulation | NOT_CHECKABLE |
| 4 | climatisation une piece | NOT_CHECKABLE |
| 5 | AHU multizone avec recuperation/humidification | NOT_CHECKABLE |
| 6 | ventilation trois niveaux avec recuperation | NOT_CHECKABLE |
| 7 | emission, distribution, stockage, production chaud/froid | NOT_CHECKABLE |

### 9.2 Classes de validation

| Classe | Couverture attendue |
|---|---|
| 1A | besoins froid/puissance thermique de base, protection solaire simplifiee |
| 1B | idem avec stores a lamelles |
| 2A | eclairage + besoins chauffage/froid, protection solaire simplifiee |
| 2B | idem avec stores a lamelles |
| 3 | humidification/deshumidification |
| 4A | systemes + energie chauffage/froid, stores simplifiees |
| 4B | systemes + energie chauffage/froid, stores a lamelles |
| 5 | energie chauffage/froid avec profils de besoins existants |

### 9.3 Preuves requises pour passer de NOT_CHECKABLE a PASS/FAIL

| Preuve | Description |
|---|---|
| fichier modele test | modele officiel ou equivalent parametre |
| fichier APS/resultats | sortie simulation reproductible |
| valeurs de reference | resultats officiels SIA ou matrice fournie |
| tolerances | ecarts acceptables par indicateur |
| version logiciel | version IESVE, moteur simulation |
| options simulation | timestep, reporting interval, HVAC, meteo |
| comparaison | ecart absolu, relatif, statut |

## 10. Rapport Excel attendu

Le rapport professionnel doit contenir au minimum:

| Onglet | Role |
|---|---|
| SUMMARY | KPI globaux |
| ACTION PLAN | priorites manager/client |
| COMPLIANCE RESULTS | scores categories |
| ALERT SUMMARY | alertes regroupees |
| ALERTS | preuves detaillees |
| DATA QUALITY | qualite extraction/API |
| DETAILED SCORES | scores detailles |
| ROOMS | zones, WWR, U moyen |
| ENVELOPE | a ajouter, surfaces/constructions |
| DYNAMIC RESULTS | a ajouter, APS/Vista |
| SIA4010 VALIDATION | a ajouter, tests officiels |
| ASSUMPTIONS | a ajouter, hypotheses |
| API DIAGNOSTICS | a ajouter, fonctions/erreurs |

## 11. Statuts recommandes

| Statut | Sens |
|---|---|
| PASS | critere verifie et conforme |
| FAIL | critere verifie et non conforme |
| WARNING | risque ou depassement non bloquant |
| MISSING | donnee absente |
| UNKNOWN | donnee insuffisante |
| NOT_APPLICABLE | critere hors perimetre |
| NOT_CHECKABLE | test impossible sans preuve externe |

## 12. Checklist de certification complete

### 12.1 Avant simulation

- projet VE identifie;
- zones a analyser selectionnees/documentees;
- geometrie propre;
- surfaces externes coherentes;
- constructions affectees;
- U-values resolues;
- vitrages et portes classes;
- g-values et protections solaires documentees;
- templates d'usage affectes;
- ventilation documentee;
- systemes HVAC affectes;
- fichier meteo identifie;
- hypotheses projet listees.

### 12.2 Simulation

- options ApacheSim tracees;
- timestep et reporting interval documentes;
- HVAC/natural ventilation/aux ventilation coherents;
- simulation terminee sans erreur;
- fichier APS conserve;
- variables resultats inventoriees;
- conversion unites validee.

### 12.3 Apres simulation

- chauffage annuel extrait;
- refroidissement annuel extrait;
- puissances max extraites;
- temperatures horaires extraites;
- heures de depassement calculees;
- energie finale par usage extraite;
- energie primaire calculee avec facteurs officiels;
- CO2 calcule avec facteurs officiels;
- resultats par zone et globaux reconciles.

### 12.4 Validation SIA 4010

- classe de validation cible definie;
- tests requis identifies;
- modeles tests disponibles;
- resultats de reference disponibles;
- tolerances disponibles;
- resultats IESVE generes;
- ecarts calcules;
- matrice PASS/FAIL signee.

## 13. Gaps actuels et roadmap

| Priorite | Travail | Impact |
|---|---|---|
| P1 | verrouiller valeur solaire applicable SIA | evite faux FAIL massif vitrage |
| P1 | lire resultats APS/Vista | necessaire conformite complete |
| P1 | noms de rapports uniques | audit multi-modeles |
| P1 | matrice SIA 4010 evidence-based | evite faux PASS |
| P2 | onglet ENVELOPE detaille | audit construction |
| P2 | onglet ASSUMPTIONS | defendabilite |
| P2 | meteo et options simulation | reproductibilite |
| P3 | graphiques manager | lisibilite |
| P3 | export PDF | partage client |

## 14. Definition d'un dossier compliant defendable

Un modele VE peut etre considere pret pour revue de conformite lorsque:

1. toutes les donnees d'entree necessaires sont presentes ou explicitement justifiees;
2. les seuils applicables sont confirmes dans les documents officiels;
3. les calculs sont reproductibles;
4. chaque valeur du rapport a une source VE/API/resultat;
5. les resultats dynamiques sont issus d'un APS identifie;
6. les alertes restantes sont expliquees ou resolues;
7. SIA 4010 est documentee par tests officiels ou marquee NOT_CHECKABLE;
8. le rapport archive unique est conserve avec date, projet et version.

## 15. Regle d'or pour le manager/client

Le livrable ne doit pas seulement dire:

```text
Le modele est conforme / non conforme.
```

Il doit dire:

```text
Ce qui est conforme, ce qui ne l'est pas, ce qui n'est pas encore verifiable,
quelle valeur le prouve, d'ou vient cette valeur, et quelle action permet de fermer le point.
```

