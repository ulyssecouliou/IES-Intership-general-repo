# SIA 4010 / SIA 380-2 — Entrées & sorties attendues pour coder la validation de compliance suisse

> **But du document**  
> Servir de checklist technique pour développer un outil de validation automatique compatible avec la logique SIA 4010:2023 / SIA 380/2:2022.  
> Ce document liste les **entrées à modéliser**, les **sorties à produire**, les **tests 1 à 7** et les **classes de validation** à couvrir.

> **Limite importante**  
> Les PDF SIA 380/2 et SIA 4010 décrivent la procédure, les exigences, les matrices et les familles de résultats.  
> Les **spécifications détaillées de chaque test**, le **bâtiment exemple**, les **fichiers numériques DXF/IFC**, les **profils de charge du test 7**, les **résultats de référence** et les **fichiers Excel d’évaluation officiels** sont publiés séparément par la SIA. Pour coder un validateur complet, ces fichiers officiels doivent être intégrés comme datasets de référence.

---

## 1. Architecture minimale attendue du moteur de validation

### 1.1 Résolution temporelle

Toutes les méthodes de calcul doivent supporter :

- pas de temps **≤ 1 h** ;
- calcul multizone ;
- profils horaires annuels ;
- agrégations mensuelles et annuelles ;
- exports par test, variante, zone, sous-système et agent énergétique.

### 1.2 Unités principales à standardiser

| Grandeur | Unité cible |
|---|---:|
| Température | °C |
| Humidité relative | % |
| Rapport de mélange / teneur en eau | g/kg ou kg/kg air sec |
| Irradiance solaire | W/m² |
| Puissance thermique | W ou kW |
| Énergie | kWh |
| Débit volumique d’air | m³/h |
| Débit massique | kg/h ou kg/s |
| Pression / perte de charge | Pa |
| Surface | m² |
| Coefficient U / H | W/(m²·K), W/K |
| COP / EER / rendement | sans unité |
| CO₂ | ppm |

### 1.3 Structure de données recommandée

```text
project/
  metadata.json
  climate/
    hourly_weather.csv
  geometry/
    zones.json
    constructions.json
    windows.json
    shading.json
  schedules/
    occupancy.csv
    equipment.csv
    lighting.csv
    moisture.csv
  hvac/
    ventilation_systems.json
    heating_systems.json
    cooling_systems.json
    storage_systems.json
    generation_systems.json
    pv_systems.json
  validation/
    test_01/
      inputs.json
      outputs.csv
      summary.json
    test_02/
      variant_2A/
      variant_2B/
      variant_2C/
      variant_2D/
    ...
```

### 1.4 Sortie CSV horaire générique recommandée

Colonnes minimales utiles pour automatiser les comparaisons :

```csv
timestamp,test_id,variant_id,zone_id,system_id,subsystem_id,
theta_air_C,theta_op_C,rh_pct,x_kg_per_kg,co2_ppm,
phi_H_W,phi_C_W,qH_kWh,qC_kWh,
phi_hum_kg_h,phi_dehum_kg_h,hum_energy_kWh,dehum_energy_kWh,
lighting_power_W,lighting_energy_kWh,daylight_illuminance_lux,
solar_gain_W,total_transmitted_solar_W,window_irradiance_W_m2,blind_angle_deg,shading_state,
airflow_sup_m3_h,airflow_eta_m3_h,supply_air_temp_C,return_air_temp_C,
fan_energy_kWh,coil_heat_power_W,coil_cool_total_power_W,coil_cool_latent_power_W,
hr_heat_transfer_W,hr_latent_transfer_W,hr_aux_energy_kWh,
energy_supplied_to_subsystem_kWh,aux_energy_kWh,thermal_losses_kWh,recoverable_losses_kWh,
carrier,delivered_energy_kWh,pv_yield_kWh
```

---

## 2. Entrées communes à tous les tests

### 2.1 Métadonnées de validation

| Entrée | Description |
|---|---|
| `test_id` | Numéro du test SIA 4010 : 1 à 7 |
| `variant_id` | Sous-variante officielle : 2A, 2B, 3A, 5D, etc. |
| `validation_class_target` | Classe visée : 1A, 1B, 2A, 2B, 3, 4A, 4B, 5 |
| `software_name` | Nom/version du logiciel ou moteur |
| `calculation_timestep` | Pas de temps, max. 1 h |
| `calendar_definition` | Année, jours ouvrables, repos, vacances, horaires d’occupation |
| `location` | Station climatique ou localisation du cas test |
| `standard_versions` | Versions SIA/EN utilisées |
| `calculation_mode` | Dimensionnement, besoin annuel, énergie, validation test |

### 2.2 Climat horaire

Entrées climatiques horaires à prévoir :

| Variable | Description |
|---|---|
| `theta_e` | Température extérieure |
| `phi_e` | Humidité relative extérieure |
| `x_e` | Rapport de mélange extérieur |
| `Gsol_g` | Irradiance solaire globale horizontale |
| `Gsol_b` | Irradiance solaire directe normale |
| `Gsol_d` | Irradiance solaire diffuse horizontale |
| `Idif_N/E/S/W` | Irradiance diffuse sur façades verticales cardinales |
| `alpha_sol` | Hauteur du soleil |
| `gamma_sol` | Azimut du soleil |
| `rho_G` | Albédo |
| `wind_avg` | Vitesse moyenne du vent |
| `wind_gust` | Rafale / vitesse de pointe |

### 2.3 Géométrie, zones et enveloppe

| Famille d’entrée | Paramètres attendus |
|---|---|
| Zones thermiques | ID local, usage SIA 2024, surface nette, volume, hauteur, orientation |
| Éléments opaques | Surfaces, orientation, inclinaison, U/R, capacités thermiques, couches, masse, contact extérieur/sol/local voisin |
| Éléments transparents | Surface fenêtre `Aw`, surface vitrée, facteur cadre `FF`, `Uw`, `Ug`, `gg`, transmission lumineuse, orientation |
| Ponts thermiques | ψ, χ, affectation par façade ou élément |
| Inertie | Capacités thermiques selon les nœuds / modèle dynamique |
| TABS | Surface activée, température max hiver, température min été, résistance entre fluide et couche conductrice |
| Ombrages fixes | Horizon, surplombs, écrans latéraux, angles α/β/γ, facteurs `Fsh` direct/diffus |

### 2.4 Protections solaires

| Entrée | Description |
|---|---|
| Type | Store en tissu, store à lamelles, protection extérieure/intérieure |
| Catégorie | Catégorie de protection solaire SIA |
| Commande | Type de régulation selon SIA 387/4, tableau 9 |
| Seuils | Irradiance d’actionnement, température ou logique de pilotage |
| Lamelles | Angle, position de travail, correction selon hauteur solaire |
| Matériau | Transmission/reflexion solaire directe et diffuse |
| Vent | Stratégie en cas de vent si demandée par le test |
| État horaire | Activé/désactivé, angle, facteur de transmission/reflexion effectif |

### 2.5 Occupation, apports internes et humidité

| Entrée | Description |
|---|---|
| Type d’usage SIA 2024 | Bureau, salle de réunion, restaurant, cuisine, amphithéâtre, etc. |
| Profil personnes | Occupation horaire, jours ouvrables/repos, saisonnalité |
| Activité métabolique | `M`, production chaleur sensible/latente |
| Appareils | Puissance spécifique, profil horaire, chaleur sensible/latente |
| Éclairage | Puissance spécifique, éclairement cible, commande, influence lumière du jour |
| Sources d’humidité | Personnes, appareils, plantes, sanitaires, cuisine, autres |
| Simultanéité | Facteurs mensuels/annuels si applicables |

### 2.6 Consignes intérieures

| Entrée | Description |
|---|---|
| `theta_set_H` | Consigne chauffage |
| `theta_set_C` | Consigne refroidissement |
| Courbes adaptatives | Courbes selon température extérieure moyenne glissante 48 h |
| Limites de confort | Limite haute/basse, y compris décalages par usage |
| Écart de régulation | `Δθctr` chauffage/refroidissement |
| `RH_min`, `RH_max` | Bornes humidification/déshumidification |
| Calendrier d’utilisation | Périodes d’occupation et fonctionnement systèmes |

### 2.7 Ventilation et infiltration

| Entrée | Description |
|---|---|
| Infiltration | Débit spécifique par surface nette |
| Air neuf requis | Débits hygiéniques par personne / par usage |
| Ventilation naturelle | Fenêtres, aération hygiénique/thermique |
| Ventilation mécanique | Débits soufflage/reprise, zones desservies |
| CO₂ | Seuils, profils de production, logique VAV si test |
| Commande débit | `SUP_AIR_FLW_CTRL`, `AIR_FLOW_CTRL` |
| Commande température soufflage | `SUP_AIR_TEMP_CTRL` |
| Fuites gaines | Classe d’étanchéité, facteur de fuite |
| Fuites CTA/AHU | Classe, facteur de fuite |
| Pertes de distribution | Surface gaines, coefficient H/U, position conditionnée/non conditionnée |

### 2.8 Systèmes techniques

Chaque sous-système doit être modélisable avec :

| Sous-système | Entrées principales |
|---|---|
| Émission chaud/froid | Type émetteur, puissance nominale, fraction convective/radiative, contrôle, auxiliaires |
| Distribution chaud/froid | Débits, pertes de charge, pompes, rendement, régulation, pertes récupérables |
| Stockage chaud/froid | Volume, pertes, emplacement, température, charge/décharge, pompes |
| Production froid | Type générateur, EER nominal/partiel, puissance frigorifique, free cooling, rejet chaleur |
| Production chaleur | PAC, chaudière, solaire, CCF, district heating, COP/rendement, priorités |
| Ventilation/AHU | Fans, coils, récupérateur, humidificateur, dégivrage, recirculation |
| ECS | Profil de charge, couplage avec production chaleur |
| PV | Surface, nombre modules, azimut, inclinaison, coefficient de puissance crête, performance système |
| Auxiliaires | Pompes, ventilateurs, régulation, équipements divers |
| Agents énergétiques | Électricité, gaz, chaleur/froid externe, solaire, autre |

---

## 3. Sorties communes de conformité

### 3.1 Sorties bâtiment / zone / local

| Sortie | Description |
|---|---|
| `theta_air_C` | Température d’air intérieure horaire |
| `theta_op_C` | Température opérative ou opérative simplifiée |
| `RH_pct` | Humidité relative intérieure |
| `x_kg_per_kg` | Teneur en humidité intérieure |
| `CO2_ppm` | Concentration CO₂ si ventilation contrôlée |
| `cooling_need_status` | Refroidissement nécessaire / souhaitable / non nécessaire |
| `humidification_need_status` | Humidification requise ou non |
| `dehumidification_need_status` | Déshumidification requise ou non |
| `hours_above_upper_limit` | Heures de dépassement limite haute |
| `hours_below_lower_limit` | Heures sous limite basse |
| `comfort_violations` | Liste des dépassements par zone et période |

### 3.2 Sorties puissance et besoin utile

| Sortie | Description |
|---|---|
| `Phi_H_W` | Puissance thermique de chauffage horaire |
| `Phi_C_W` | Puissance thermique de refroidissement horaire |
| `Phi_H_peak_W` | Puissance chauffage de dimensionnement |
| `Phi_C_peak_W` | Puissance refroidissement de dimensionnement |
| `QH_kWh` | Besoin de chaleur chauffage |
| `QC_kWh` | Besoin de froid refroidissement |
| `QH_monthly_kWh`, `QC_monthly_kWh` | Agrégation mensuelle |
| `QH_annual_kWh`, `QC_annual_kWh` | Agrégation annuelle |
| `Phi_hum`, `Phi_dehum` | Besoin humidification / déshumidification |
| `simultaneous_heating_cooling` | Chauffage et refroidissement simultanés éventuels |

### 3.3 Sorties énergie des systèmes

Pour chaque sous-système et chaque pas de temps :

| Sortie | Description |
|---|---|
| `energy_supplied_to_subsystem_kWh` | Énergie à fournir au sous-système |
| `aux_energy_kWh` | Énergie auxiliaire |
| `thermal_losses_kWh` | Pertes thermiques |
| `recoverable_losses_kWh` | Part récupérable des pertes |
| `delivered_energy_by_carrier_kWh` | Énergie reçue de l’extérieur par agent énergétique |
| `weighted_energy_index` | Indice de dépense d’énergie pondéré |
| `project_vs_limit` | Comparaison valeur projet / valeur limite |
| `project_vs_target` | Comparaison valeur projet / valeur cible |
| `pv_yield_kWh` | Production PV horaire / annuelle |

### 3.4 Sorties de validation

| Sortie | Utilité |
|---|---|
| Fichier horaire par test | Comparaison fine avec résultats de référence |
| Résumé par variante | Valeurs intégrées, pics, erreurs, écarts |
| Fichier compatible Excel SIA | Collage/import dans le fichier d’évaluation officiel |
| Rapport d’écarts | Écart absolu, relatif, max, RMSE, tolérance officielle |
| Statut test | Réussi / échoué / incomplet |
| Statut classe | Classe validable si tous les tests nécessaires sont réussis |

---

## 4. Classes de validation SIA 4010

| Classe | Applications couvertes | Protection solaire | Tests requis | Couverture minimale à coder |
|---|---|---|---|---|
| **1A** | Évaluation du besoin de refroidissement + calcul de base de la puissance thermique requise | Sans régulation selon position du soleil, ex. store en tissu | **1 + 2A** | Enveloppe + climat + besoins + protection solaire simple |
| **1B** | Même usage que 1A | Stores à lamelles | **1 + 2** | 1A + régulation stores à lamelles |
| **2A** | Énergie d’éclairage SIA 387/4 + besoin chauffage/refroidissement | Sans régulation selon position du soleil | **1 + 2A + 3A à 3F** | 1A + éclairage et lumière du jour |
| **2B** | Même usage que 2A | Stores à lamelles | **1 à 3** | 2A + toutes variantes stores à lamelles / éclairage |
| **3** | Besoin d’humidification et de déshumidification | Non déterminant | **1 + 4 à 6** | Enveloppe + ventilation/AHU + humidité |
| **4A** | Puissance thermique requise propre au système + besoin d’énergie chauffage/refroidissement | Sans régulation selon position du soleil | **1 + 2A + 3A à 3F + 4 à 7** | Chaîne complète bâtiment + systèmes, hors lamelles avancées |
| **4B** | Couverture complète de SIA 380/2 | Stores à lamelles | **1 à 7** | Couverture complète, certification la plus large |
| **5** | Besoins d’énergie chauffage/refroidissement pour profils de besoins existants | Non déterminant | **7** | Calcul systèmes sur profils de charge fournis |

---

## 5. Tests 1 à 7 — Entrées et sorties attendues

---

# Test 1 — Tests de base de l’enveloppe du bâtiment

## Objectif

Valider le modèle thermique de base de l’enveloppe du bâtiment selon SN EN ISO 52016-1 / ASHRAE 140 / BESTEST.

## Modules et périmètre

| Élément | Valeur |
|---|---|
| Module DPEB | M2-2 |
| Référence | SN EN ISO 52016-1:2017, chapitre 7, tableau 27 |
| Objet | Cellule de test selon SN EN ISO 52016-1 / ASHRAE 140 |
| Niveau | Local / cellule thermique |

## Entrées à coder

### Entrées géométriques

- Dimensions de la cellule test officielle.
- Surface de plancher.
- Volume d’air.
- Hauteur du local.
- Surfaces opaques par orientation.
- Fenêtres et surfaces vitrées, si prévues dans le cas test.
- Adjacences : extérieur, sol, local voisin, zone non conditionnée.

### Entrées enveloppe

- Composition des parois.
- Coefficients U / résistances R.
- Capacités thermiques.
- Coefficients de transfert superficiel.
- Masse thermique.
- Ponts thermiques si définis.
- Propriétés solaires des vitrages.
- Facteurs d’ombrage fixes.

### Entrées climatiques

- Fichier météo horaire officiel du test.
- Température extérieure.
- Rayonnement direct/diffus/global.
- Position solaire.
- Vent si requis.
- Conditions de préconditionnement si définies.

### Entrées d’usage

- Consignes chauffage/refroidissement.
- Horaires.
- Infiltration / ventilation selon cas test.
- Apports internes sensibles.
- Éventuels cas sans chauffage/refroidissement pour température libre.

## Sorties à produire

| Sortie | Niveau | Unité |
|---|---|---:|
| Température d’air intérieure horaire | cellule | °C |
| Température opérative horaire si demandée | cellule | °C |
| Puissance chauffage horaire | cellule | W |
| Puissance refroidissement horaire | cellule | W |
| Besoin chauffage intégré | cellule | kWh |
| Besoin refroidissement intégré | cellule | kWh |
| Puissance chauffage maximale | cellule | W |
| Puissance refroidissement maximale | cellule | W |
| Bilan thermique par composant si disponible | cellule | W/kWh |

## Points de contrôle pour coder

- Stabilité numérique au pas horaire.
- Conservation énergétique.
- Sensibilité aux apports solaires.
- Réponse dynamique de l’inertie.
- Transmission opaque et transparente.
- Gestion des cas sans système ou système idéal.

---

# Test 2 — Type et régulation de la protection solaire

## Objectif

Valider le calcul des protections solaires, en particulier la transition entre :

- climat suisse ;
- usage suisse ;
- infiltration suisse ;
- logique SIA 387/4 ;
- calcul solaire SIA 380/2 annexe A.

## Modules et périmètre

| Élément | Valeur |
|---|---|
| Modules DPEB | M2-8, M9-2 |
| Références | SIA 380/2:2022 §2.2.2.3 ; SIA 387/4:2023 §3.4.3 |
| Objet | Comme test 1 avec adaptations |
| Climat | Zurich-Kloten |
| Usage | Bureau individuel selon SIA 2024 |
| Nombre de variantes | 4 |

## Variantes

| Variante | Protection solaire | Régulation |
|---|---|---|
| **2A** | Store en tissu | Sans régulation selon position du soleil |
| **2B** | Stores à lamelles | Type de régulation solaire 1 |
| **2C** | Stores à lamelles | Type de régulation solaire 2 |
| **2D** | Stores à lamelles | Type de régulation solaire 3 |

## Entrées à coder

### Entrées héritées du test 1

- Cellule / local de base.
- Géométrie.
- Enveloppe.
- Climat.
- Fenêtre.
- Infiltration.
- Consignes.
- Apports internes.

### Entrées spécifiques protection solaire

| Entrée | Description |
|---|---|
| `solar_protection_type` | Store tissu ou store à lamelles |
| `solar_control_type` | Type de commande SIA 387/4, tableau 9 |
| `activation_threshold` | Seuil d’irradiance sur plan de fenêtre |
| `window_plane_irradiance` | Rayonnement au niveau de la fenêtre |
| `blind_angle` | Angle des lamelles |
| `fixed_shading_angle` | Angle fixe de protection solaire pour cas diagnostic |
| `tau_dir`, `tau_dif` | Transmission solaire directe/diffuse |
| `rho_dir`, `rho_dif` | Réflexion solaire directe/diffuse |
| `F_tau_beta`, `F_tau_delta` | Corrections transmission selon angle lamelles / soleil |
| `F_rho_beta`, `F_rho_delta` | Corrections réflexion |
| `Fsh_dir`, `Fsh_dif` | Facteurs d’ombrage direct/diffus |
| `gg` ou `gtot` | Valeur g vitrage seul ou vitrage + protection |
| `state_schedule` | État horaire activé/désactivé |

## Sorties à produire

| Sortie | Niveau | Unité |
|---|---|---:|
| Rayonnement au plan de fenêtre | fenêtre | W/m² |
| État de protection solaire | fenêtre/pas horaire | bool / code |
| Angle des lamelles | fenêtre/pas horaire | ° |
| Facteurs de transmission/reflexion effectifs | fenêtre | - |
| Rayonnement total transmis | fenêtre/local | W |
| Apports solaires `Φsol` | local | W |
| Apports solaires intégrés | local | kWh |
| Température intérieure résultante | local | °C |
| Besoin chauffage/refroidissement impacté | local | W/kWh |

## Points de contrôle pour coder

- La régulation solaire doit être indépendante par façade si nécessaire.
- Pour les lamelles, il faut restituer l’angle horaire.
- Pour le store tissu, prévoir une méthode simplifiée par `gtot`.
- Conserver les sorties intermédiaires solaires, pas seulement le besoin final.

---

# Test 3 — Régulation de l’éclairage

## Objectif

Valider le calcul de l’éclairage avec prise en compte :

- lumière du jour ;
- protection solaire ;
- types de commande d’éclairage ;
- puissance et énergie d’éclairage.

## Modules et périmètre

| Élément | Valeur |
|---|---|
| Modules DPEB | M2-7, M9-2 |
| Références | SIA 380/2:2022 §2.2.2.4 ; SIA 387/4:2023 §3.4.4 |
| Objet | Comme test 2, avec éclairage spécifié |
| Nombre de variantes | 12 |

## Combinaisons test 2 + test 3

| Protection solaire | Variante protection | Variante éclairage | Type régulation éclairage |
|---|---:|---:|---:|
| Store en tissu | 2A | 3A | 1 |
| Store en tissu | 2A | 3B | 2 |
| Store en tissu | 2A | 3C | 3 |
| Store en tissu | 2A | 3D | 4 |
| Store en tissu | 2A | 3E | 5 |
| Store en tissu | 2A | 3F | 6 |
| Stores à lamelles | 2B | 3G | 1 |
| Stores à lamelles | 2B | 3H | 3 |
| Stores à lamelles | 2C | 3I | 1 |
| Stores à lamelles | 2C | 3J | 3 |
| Stores à lamelles | 2D | 3K | 1 |
| Stores à lamelles | 2D | 3L | 3 |

## Entrées à coder

### Entrées héritées

- Toutes les entrées du test 2.
- État horaire de protection solaire.
- Facteurs solaires et lumineux des vitrages/protections.

### Entrées éclairage

| Entrée | Description |
|---|---|
| `lighting_control_type` | Type de commande SIA 387/4 tableau 10 |
| `lighting_power_density` | Puissance spécifique d’éclairage |
| `target_illuminance` | Éclairement cible |
| `maintenance_factor` | Indice de maintenance |
| `daylight_transmission` | Transmission lumineuse vitrage/protection |
| `room_reflectance` | Réflexions internes si nécessaires |
| `occupancy_schedule` | Profil de présence |
| `manual_override` | Commande manuelle si type de régulation l’exige |
| `dimming_curve` | Courbe de gradation |
| `standby_power` | Veille éventuelle |

## Sorties à produire

| Sortie | Niveau | Unité |
|---|---|---:|
| Flux de lumière du jour | local/zone | lm ou facteur |
| Éclairement naturel | point/local | lux |
| Fraction de besoin couvert par jour | local | - |
| Puissance instantanée éclairage `PL,ac` | local | W |
| Énergie éclairage horaire | local | kWh |
| Énergie éclairage annuelle | local/bâtiment | kWh |
| Apport thermique de l’éclairage | local | W |
| Statut commande éclairage | local/pas horaire | code |

## Points de contrôle pour coder

- L’éclairage est à la fois une consommation électrique et un apport thermique interne.
- Les protections solaires doivent influencer l’éclairement naturel.
- Les sorties doivent permettre de comparer séparément puissance, énergie et lumière du jour.

---

# Test 4 — Climatisation d’une seule pièce, système à air seul

## Objectif

Valider une installation de conditionnement d’air pour une seule pièce, sans émission de chaleur/froid autre que la ventilation.

## Modules et périmètre

| Élément | Valeur |
|---|---|
| Modules DPEB | M5-5, M5-6, M5-8 |
| Références | SN EN 16798-7:2017 ; SN EN 16798-5-1:2017 |
| Objet | Bâtiment exemple, amphithéâtre sans fenêtre |
| Système | Air conditionné, système à air seul |
| Variante | 1 |

## Configuration technique

| Élément | Valeur attendue |
|---|---|
| Type | VAV zone unique |
| Pilotage | CO₂ |
| `SYS_TYPE` | `SINGLE_ZONE` |
| `FAN_CTRL` | `DIRECT` |
| Soufflage | Température d’air fourni régulée selon température de pièce |
| Récupération de chaleur | Échangeur à plaques |
| Protection givrage | Bypass |
| Émission chaud/froid | Aucune hors ventilation |

## Entrées à coder

### Bâtiment / zone

- Géométrie de l’amphithéâtre.
- Volume.
- Occupation horaire.
- Production CO₂.
- Apports internes personnes/appareils/éclairage.
- Consignes température et CO₂.
- Données climatiques.

### Ventilation

| Entrée | Description |
|---|---|
| Débit nominal soufflage/reprise | m³/h |
| Débit mini/max VAV | m³/h |
| Courbe de régulation CO₂ | seuils et loi de débit |
| `SUP_AIR_TEMP_CTRL` | Régulation température soufflage |
| Température soufflage min/max | °C |
| Fuites gaines / AHU | Classes et facteurs |
| Pertes thermiques gaines/AHU | U, H, surfaces, emplacement |
| Fan data | Pressions, puissances, rendement, courbes |
| Récupérateur | Type plate, efficacité thermique |
| Dégivrage | Bypass, seuils |
| Batterie chaude | Puissance, efficacité, température eau si applicable |
| Batterie froide | Puissance sensible/latente, bypass factor, efficacité |

## Sorties à produire

| Sortie | Niveau | Unité |
|---|---|---:|
| Débit d’air fourni/repris | zone/système | m³/h |
| Énergie ventilateur | système | kWh |
| Température d’air fourni | système | °C |
| Température d’air intérieur | zone | °C |
| Température opérative intérieure | zone | °C |
| Concentration CO₂ | zone | ppm |
| Puissance réchauffeur d’air | système | W |
| Puissance refroidisseur d’air totale | système | W |
| Puissance refroidisseur d’air latente | système | W |
| Énergie auxiliaire récupération chaleur | système | kWh |
| État bypass / dégivrage | système | code |

## Points de contrôle pour coder

- Couplage CO₂ → débit d’air → puissance ventilateur.
- Couplage température pièce → température soufflage → batteries.
- Séparation refroidissement sensible / latent.
- Le système est à air seul : pas d’émetteur local séparé.

---

# Test 5 — Unité de traitement d’air multizone complexe

## Objectif

Valider une AHU multizone avec :

- réchauffeur d’air ;
- refroidisseur d’air ;
- humidificateur ;
- récupération de chaleur à rotor ;
- récupération d’humidité.

## Modules et périmètre

| Élément | Valeur |
|---|---|
| Modules DPEB | M5-5, M5-6, M5-8 |
| Références | SN EN 16798-7:2017 ; SN EN 16798-5-1:2017 |
| Objet | Bureaux et salles de réunion |
| Système | Ventilation bureaux multizone |
| Nombre de variantes | 4 |

## Zones du bâtiment exemple

- Bureaux.
- Salles de réunion.
- Bureaux individuels.
- Bureau d’angle / groupe.
- Étages de bureaux du bâtiment exemple.

## Configuration technique

| Élément | Valeur attendue |
|---|---|
| Type | VAV multizone |
| Pilotage | CO₂ |
| `SYS_TYPE` | `MULTI_ZONE` |
| Température soufflage | Guidée par température extérieure |
| Récupération chaleur | Rotor |
| `FAN_CTRL` | `CONST_PRES` ou `MIN_PRES` |
| Récupérateur | Hygroscopique ou non hygroscopique |
| Humidificateur | Adiabatique ou vapeur |

## Variantes test 5

| Variante | `FAN_CTRL` | Récupérateur de chaleur | Humidificateur |
|---|---|---|---|
| **5A** | `MIN_PRES` | Hygroscopique | Adiabatique |
| **5B** | `CONST_PRES` | Hygroscopique | Adiabatique |
| **5C** | `CONST_PRES` | Non hygroscopique | Adiabatique |
| **5D** | `CONST_PRES` | Non hygroscopique | Vapeur |

## Entrées à coder

### Zones et usages

- Géométrie et volume de chaque zone.
- Occupation horaire.
- Charges internes.
- Production CO₂.
- Sources d’humidité.
- Consignes température et humidité.
- Débits d’air requis par zone.

### AHU multizone

| Entrée | Description |
|---|---|
| `SYS_TYPE` | `MULTI_ZONE` |
| `FAN_CTRL` | `CONST_PRES` ou `MIN_PRES` |
| `AIR_FLOW_CTRL` | Variable ou multi-stage selon variante |
| Débits nominaux / mini / max | Par zone et système |
| Pressions nominales | Soufflage/reprise |
| Courbes ventilateurs | Rendement, pression, puissance |
| Fuites gaines | Classe/facteur |
| Fuites AHU | Classe/facteur |
| Pertes gaines/AHU | H/U, surface, zone conditionnée ou non |
| Température soufflage | Loi selon température extérieure |
| Récupérateur rotor | Hygroscopique ou non, efficacité chaleur/humidité |
| Vitesse rotor | Max, contrôle, puissance auxiliaire |
| Dégivrage | Seuils, stratégie |
| Batterie chaude | Rendement, puissance, températures |
| Batterie froide | Rendement, puissance, sensible/latent |
| Humidificateur | Type, rendement, énergie spécifique, débit eau |
| Humidificateur vapeur | Agent énergétique |
| Auxiliaires | Régulation, pompes, rotor, traitement eau |

## Sorties à produire

| Sortie | Niveau | Unité |
|---|---|---:|
| Débits par zone | zone | m³/h |
| Énergie ventilateur | AHU | kWh |
| Énergie réchauffeur d’air | AHU | kWh |
| Énergie refroidisseur d’air totale | AHU | kWh |
| Énergie refroidisseur d’air latente | AHU | kWh |
| Transfert total récupération chaleur | AHU | kWh ou W |
| Transfert latent récupération chaleur | AHU | kWh ou W |
| Énergie auxiliaire récupération chaleur | AHU | kWh |
| Énergie humidification | AHU | kWh |
| Fuites distribution | AHU/gaines | m³/h ou kg/h |
| Pertes thermiques distribution/AHU | AHU/gaines | kWh |
| Température soufflage/reprise | AHU/zone | °C |
| Humidité soufflage/reprise | AHU/zone | kg/kg ou % |
| CO₂ par zone | zone | ppm |

## Points de contrôle pour coder

- Le modèle doit gérer plusieurs zones avec demandes différentes.
- Le rotor hygroscopique transfère chaleur et humidité.
- L’humidificateur adiabatique et vapeur n’ont pas le même bilan énergétique.
- Les fuites et pertes AHU/distribution doivent être identifiables séparément.

---

# Test 6 — Ventilation à niveaux avec récupération de chaleur et débordement

## Objectif

Valider un système de ventilation restaurant/cuisine avec :

- récupération de chaleur ;
- débit constant ou niveaux de débit ;
- débordement d’air entre restaurant et cuisine ;
- pertes de distribution et AHU ;
- batteries chaud/froid.

> Note de codage : la description générale mentionne un système à trois niveaux, tandis que la matrice détaillée décrit une ventilation à deux niveaux. Le moteur doit donc gérer une configuration multi-niveaux paramétrable, sans hardcoder le nombre de niveaux.

## Modules et périmètre

| Élément | Valeur |
|---|---|
| Modules DPEB | M5-5, M5-6, M5-8 |
| Références | SN EN 16798-7:2017 ; SN EN 16798-5-1:2017 |
| Objet | Restaurant et cuisine |
| Système | Ventilation restaurant/cuisine |
| Variante | 1 |

## Configuration technique

| Élément | Valeur attendue |
|---|---|
| Débit | Constant / niveaux de débit |
| Température soufflage | Guidée par température extérieure |
| Récupération chaleur | Oui |
| Débordement | Restaurant → cuisine, excédent air fourni ou air repris |
| Zones | Restaurant et cuisine |

## Entrées à coder

| Famille | Entrées |
|---|---|
| Zones | Géométrie restaurant/cuisine, usages, horaires, charges |
| Débits | Débits soufflage/reprise par zone et niveau |
| Débordement | Sens, quantité, conditions d’activation |
| Récupération chaleur | Type, efficacité, contrôle, auxiliaires |
| Température soufflage | Loi selon température extérieure |
| Batteries | Réchauffeur/refroidisseur, rendement, puissances |
| Ventilateurs | Pressions, courbes, rendement, contrôle |
| Fuites | Gaines et AHU |
| Pertes thermiques | Distribution + AHU |
| Humidité | Charges latentes cuisine/restaurant, déshumidification |
| Climat | Données horaires |
| Consignes | Température, humidité, horaire fonctionnement |

## Sorties à produire

| Sortie | Niveau | Unité |
|---|---|---:|
| Débit d’air | zone/système | m³/h |
| Débordement restaurant/cuisine | entre zones | m³/h |
| Énergie ventilateurs | système | kWh |
| Puissance réchauffeur d’air | système | W |
| Puissance refroidisseur d’air totale | système | W |
| Puissance refroidisseur d’air latente | système | W |
| Puissance récupération chaleur chauffage | système | W |
| Puissance récupération chaleur refroidissement | système | W |
| Énergie auxiliaire récupération chaleur | système | kWh |
| Pertes distribution + AHU | système | kWh |
| Température air fourni | système | °C |
| Température air repris | système | °C |
| Humidité air fourni/repris | système | kg/kg |

## Points de contrôle pour coder

- Le bilan massique entre restaurant et cuisine doit être fermé.
- Les pertes et fuites doivent être visibles dans les sorties.
- Les puissances récupération chaleur en chauffage et refroidissement doivent être séparables.
- Les charges latentes doivent être isolées pour le refroidisseur d’air.

---

# Test 7 — Émission, distribution, stockage et production de chaleur/froid

## Objectif

Valider la chaîne complète des systèmes techniques :

- émission ;
- distribution ;
- stockage ;
- production de chaleur ;
- production de froid ;
- eau chaude sanitaire intégrée ;
- photovoltaïque ;
- besoin total d’énergie chauffage/refroidissement.

## Modules et périmètre

| Élément | Valeur |
|---|---|
| Modules froid | M4-5, M4-6, M4-7, M4-8 |
| Modules chauffage | M3-5, M3-6, M3-7, M3-8 |
| Références | SN EN 16798-9, SN EN 15316-2, SN EN 15316-3, SN EN 15316-5, SN EN 16798-15, SN EN 16798-13, SIA 384/3 |
| Zones | Pièces des tests 5 et 6 |
| Systèmes | Tous les systèmes de ventilation des tests 4 à 6 |
| Variante | 1 |

## Configuration technique

| Domaine | Configuration |
|---|---|
| Émission froid bureaux | Plafonds chauffants/réfrigérants |
| Émission froid restaurant | Plafonds réfrigérants |
| Émission chaleur bureaux | Plafonds chauffants/réfrigérants |
| Émission chaleur restaurant | Convecteurs |
| Distribution | Réseaux chaud/froid avec pompes |
| Stockage | Stockage froid et chaleur, charge/décharge pour prolonger fonctionnement |
| Production froid | Machine frigorifique à compresseur avec refroidisseur sec |
| Production chaleur | Bivalent : PAC air/eau + chaudière gaz de pointe |
| ECS | Profil de charge donné, intégré |
| PV | Autoproduction d’électricité |

## Entrées à coder

### Entrées de demande

- Besoins horaires de chauffage par zone.
- Besoins horaires de refroidissement par zone.
- Profils précalculés fournis si utilisés.
- Besoins ventilation issus des tests 4 à 6.
- Profil horaire ECS.
- Consignes et horaires.

### Émission chaud/froid

| Entrée | Description |
|---|---|
| Type émetteur | Plafond chauffant/réfrigérant, plafond réfrigérant, convecteur |
| Puissance nominale | Chauffage/refroidissement |
| Fraction convective/radiative | Selon type |
| Régulation | Variation température, hystérésis, contrôle local |
| TABS | Surface, température départ max/min |
| Auxiliaires terminaux | Puissance, part load, contrôle |

### Distribution chaud/froid

| Entrée | Description |
|---|---|
| Débits nominaux | Réseau chaud/froid |
| Pertes de charge | Branches et composants |
| Pompes | Puissance, rendement, IEE |
| Régulation pompes | Non régulée, on/off, multi-étages, vitesse variable |
| Températures départ/retour | Constantes ou compensées |
| Pertes thermiques | H/U, emplacement, récupérabilité |
| Priorités | En cas de puissance insuffisante |

### Stockage chaud/froid

| Entrée | Description |
|---|---|
| Volume | Stockage eau chaude/froide |
| Température fonctionnement | °C |
| Coefficient de perte | W/K |
| Position | Zone conditionnée, non conditionnée, extérieur |
| Charge/décharge | Loi de contrôle |
| Pompes stockage | Puissance, débit |
| Pertes récupérables | Fraction récupérable |
| Type de stockage froid | Eau froide, glace, PCM si applicable |
| Type de stockage chaud | Chauffage, ECS, combiné |

### Production froid

| Entrée | Description |
|---|---|
| Type générateur | Compression |
| Type rejet chaleur | Refroidisseur sec |
| Puissance frigorifique nominale | kW |
| EER nominal | - |
| EER part-load | Courbes / points A-B-C-D et 5e point |
| Températures évaporateur/condenseur | Conditions nominales et partielles |
| Free cooling | Oui/non si applicable |
| Rejet chaleur | Puissance auxiliaire, mode sec/humide/hybride |
| Priorités générateurs | Si plusieurs |
| Récupération chaleur | Chaleur récupérable côté chaud |

### Production chaleur

| Entrée | Description |
|---|---|
| PAC air/eau | Puissance nominale, COP, courbes selon charge/températures |
| Source chaleur | Air extérieur |
| Chaudière gaz | Puissance, rendement, combustible, pertes |
| Bivalence | Seuils, ordre de priorité |
| Températures système | Source, départ, retour |
| Auxiliaires | Pompes source, ventilateurs, brûleur, régulation |
| ECS | Couplage avec production chaleur |

### Photovoltaïque

| Entrée | Description |
|---|---|
| Nombre modules | `N` |
| Surface modules | m² |
| Azimut | ° |
| Inclinaison | ° |
| Coefficient puissance crête | kW/m² |
| Facteur performance système | - |
| Batterie éventuelle | Rendement charge/décharge, pertes |

## Sorties à produire

### Sorties froid

| Sortie | Niveau | Unité |
|---|---|---:|
| Énergie électrique fournie à la machine frigorifique | production froid | kWh |
| Chaleur totale extraite | production froid | kWh |
| Énergie auxiliaire production froid | production froid | kWh |
| Chaleur fournie par production froid côté chaleur | récupération | kWh |
| Chaleur extraite/rejetée par refroidisseur | rejet chaleur | kWh |
| État free cooling / rejet sec | production froid | code |
| Températures évaporateur/condenseur | production froid | °C |
| EER effectif | production froid | - |

### Sorties chaleur

| Sortie | Niveau | Unité |
|---|---|---:|
| Énergie électrique PAC | production chaleur | kWh |
| Chaleur fournie par production chaleur | production chaleur | kWh |
| Chaleur fournie au chauffage | chauffage | kWh |
| Chaleur fournie à l’ECS | ECS | kWh |
| Énergie chaudière | chaudière | kWh ou combustible |
| Énergie auxiliaire production chaleur | production chaleur | kWh |
| COP effectif PAC | PAC | - |
| Part PAC / part chaudière | système | % |
| État bivalence | système | code |

### Sorties distribution / stockage

| Sortie | Niveau | Unité |
|---|---|---:|
| Énergie pompes chaud/froid | distribution | kWh |
| Pertes distribution chaud/froid | distribution | kWh |
| Pertes récupérables | distribution | kWh |
| État charge/décharge stockage | stockage | code |
| Énergie chargée/déchargée | stockage | kWh |
| Pertes stockage | stockage | kWh |
| Température stockage | stockage | °C |

### Sorties globales bâtiment

| Sortie | Niveau | Unité |
|---|---|---:|
| Besoin total énergie chauffage | bâtiment | kWh |
| Besoin total énergie refroidissement | bâtiment | kWh |
| Énergie finale par agent énergétique | bâtiment | kWh |
| Énergie auxiliaire totale | bâtiment | kWh |
| Production PV | bâtiment | kWh |
| Autoconsommation PV si modélisée | bâtiment | kWh |
| Indice énergétique pondéré | bâtiment | selon SIA 380 |
| Valeur projet / valeur limite / valeur cible | bâtiment | selon SIA 380 |

## Points de contrôle pour coder

- Le calcul doit remonter du besoin utile vers la production.
- Chaque sous-système doit exposer : énergie fournie, auxiliaires, pertes, pertes récupérables.
- Les profils horaires par agent énergétique sont indispensables.
- Les stockages doivent être dynamiques, pas de simples rendements fixes.
- La PAC et la machine frigorifique doivent être sensibles à la charge partielle et aux températures.
- Le test 7 peut être utilisé seul pour la classe 5 si des profils de besoins existants sont fournis.

---

## 6. Mapping tests → fonctions logicielles à développer

| Fonction logicielle | Tests concernés |
|---|---|
| Moteur thermique enveloppe multizone | 1, 2, 3, 4, 5, 6 |
| Calcul solaire direct/diffus par orientation | 1, 2, 3 |
| Protections solaires tissu | 2A, 3A-F, 1A, 2A, 4A |
| Protections solaires lamelles | 2B-D, 3G-L, 1B, 2B, 4B |
| Lumière du jour + commande éclairage | 3 |
| Ventilation naturelle / infiltration | 1, 2, 3 |
| Ventilation mécanique simple zone | 4 |
| Ventilation mécanique multizone | 5 |
| CO₂ / VAV | 4, 5 |
| Récupération chaleur sensible | 4, 5, 6 |
| Récupération humidité | 5 |
| Humidification adiabatique/vapeur | 5 |
| Débordement interzone | 6 |
| Batteries air chaud/froid | 4, 5, 6 |
| Distribution hydraulique froid | 7 |
| Distribution hydraulique chaud | 7 |
| Stockage froid/chaleur | 7 |
| Production froid compression | 7 |
| Production chaleur PAC + chaudière | 7 |
| ECS couplée | 7 |
| PV | 7 |
| Agrégation énergie par agent | 7, classes 4A/4B/5 |
| Comparaison valeur projet / référence | Compliance globale SIA 380 |

---

## 7. Checklist de développement par priorité

### Priorité 1 — Socle de validation

- [ ] Import météo horaire.
- [ ] Modèle de zone thermique.
- [ ] Enveloppe opaque/transparente.
- [ ] Apports solaires.
- [ ] Infiltration.
- [ ] Consignes.
- [ ] Puissance chauffage/refroidissement.
- [ ] Exports horaires.

### Priorité 2 — Classes 1A / 1B

- [ ] Test 1 complet.
- [ ] Test 2A store tissu.
- [ ] Tests 2B-D stores à lamelles.
- [ ] Sorties solaires détaillées.
- [ ] Détection besoin refroidissement.
- [ ] Puissances de base.

### Priorité 3 — Classes 2A / 2B

- [ ] Lumière du jour.
- [ ] Commandes éclairage 1 à 6.
- [ ] Variantes 3A à 3L.
- [ ] Énergie éclairage.
- [ ] Apport thermique éclairage.

### Priorité 4 — Classe 3

- [ ] AHU simple zone.
- [ ] AHU multizone.
- [ ] CO₂ / VAV.
- [ ] Humidification.
- [ ] Déshumidification.
- [ ] Récupération humidité.
- [ ] Tests 4 à 6.

### Priorité 5 — Classes 4A / 4B / 5

- [ ] Émission chaud/froid.
- [ ] Distribution hydraulique.
- [ ] Pompes et auxiliaires.
- [ ] Stockage chaud/froid.
- [ ] Production froid.
- [ ] Production chaleur.
- [ ] ECS.
- [ ] PV.
- [ ] Profils horaires par agent énergétique.
- [ ] Indice énergétique global.
- [ ] Test 7.

---

## 8. Règles de décision pour certifier une classe

Pseudo-logique :

```python
def validation_class_status(passed_tests, passed_variants):
    status = {}

    status["1A"] = passed_tests[1] and passed_variants["2A"]
    status["1B"] = passed_tests[1] and passed_tests[2]

    status["2A"] = (
        passed_tests[1]
        and passed_variants["2A"]
        and all(passed_variants[v] for v in ["3A", "3B", "3C", "3D", "3E", "3F"])
    )

    status["2B"] = passed_tests[1] and passed_tests[2] and passed_tests[3]

    status["3"] = (
        passed_tests[1]
        and passed_tests[4]
        and passed_tests[5]
        and passed_tests[6]
    )

    status["4A"] = (
        passed_tests[1]
        and passed_variants["2A"]
        and all(passed_variants[v] for v in ["3A", "3B", "3C", "3D", "3E", "3F"])
        and passed_tests[4]
        and passed_tests[5]
        and passed_tests[6]
        and passed_tests[7]
    )

    status["4B"] = all(passed_tests[i] for i in range(1, 8))

    status["5"] = passed_tests[7]

    return status
```

---

## 9. Données externes indispensables non incluses dans les PDF

À intégrer avant une certification réelle :

| Élément | Utilisation |
|---|---|
| Spécification officielle test 1 | Cas exacts EN ISO 52016 / ASHRAE 140 |
| Spécification officielle test 2 | Cas solaires, seuils, géométrie, variantes |
| Spécification officielle test 3 | Cas éclairage, contrôles, points de calcul |
| Spécification officielle test 4 | Amphithéâtre, AHU, profils, références |
| Spécification officielle test 5 | Bureaux, AHU multizone, humidification |
| Spécification officielle test 6 | Restaurant/cuisine, débordement |
| Spécification officielle test 7 | Profils de charge, systèmes de génération |
| Fichiers Excel d’évaluation | Références, tolérances, statut réussite |
| Bâtiment exemple DXF/IFC | Géométrie tests 4 à 7 |
| Profils horaires officiels | Occupation, charges, ECS, besoins précalculés |
| Résultats de référence | Comparaison automatique |
| FAQ SIA 4010 | Décisions d’interprétation |

---

## 10. Résumé ultra-court pour coder

| Test | Ce que tu dois savoir calculer | Sorties clés |
|---:|---|---|
| 1 | Enveloppe dynamique | Températures, puissances, besoins |
| 2 | Protection solaire | `Φsol`, rayonnement transmis, angle/état stores |
| 3 | Éclairage avec lumière du jour | Puissance/énergie éclairage, lux, flux jour |
| 4 | AHU simple zone air seul | Débits, fan, T soufflage/intérieure, coils, CO₂ |
| 5 | AHU multizone + rotor + humidification | Énergies fan/coils/humidification, récupération chaleur/humidité |
| 6 | Ventilation restaurant/cuisine + débordement | Débits, overflow, HR, coils, pertes, T soufflage/reprise |
| 7 | Chaîne complète systèmes chaud/froid/ECS/PV | Énergie finale par agent, pertes, auxiliaires, PV, indice global |

---

## 11. Références internes aux documents utilisés

- SIA 380/2:2022 — calculs énergétiques dynamiques, besoins, puissances, énergie, annexes A/B/C.
- SIA 4010:2023 — lignes directrices, procédure de validation, classes de validation, tests 1 à 7, matrice de validation.
- Les valeurs numériques officielles des tests doivent provenir des fichiers d’évaluation et spécifications SIA 4010 séparés.
