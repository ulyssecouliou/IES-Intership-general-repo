# Contrat d'extraction adaptateur VE — familles SIA 380/2 Tableau 2 non encore automatisées

> Statut : **FAISABILITÉ TRACÉE** — lecture directe du PDF `refs/VEScripts-API-VE2023.pdf`
> (248 pages, extraction PyMuPDF). Aucun membre API n'est cité sans numéro de page source.
> Tout membre supposé mais non localisé dans le PDF est marqué explicitement.
> Auteur : `ve-adapter-engineer`, 2026-08-14.
> Portée : familles SIA 380/2:2022 Tableau 2 absentes de `IMPLEMENTED_REFERENCE_INPUT_FAMILIES`
> dans `swiss_sia/reference_project.py`. Ce document est un **contrat de faisabilité**,
> pas du code. Aucun code de production adapter n'est écrit ici.

---

## 0. Conventions de marquage

| Marqueur | Signification |
|---|---|
| **[PDF p.N]** | Membre trouvé dans le PDF, page N exacte |
| **[EXPOSÉ]** | Membre documenté dans le PDF, extractible via API |
| **[EXPOSÉ-NCM/UK]** | Exposé mais dans des méthodes `*_ncm()` : données UK Building Regulations — correspondance sémantique avec les paramètres SIA 380/2 à confirmer par sonde VE réelle |
| **[NON EXPOSÉ]** | Terme absent du PDF, aucun membre candidat trouvé |
| **[NÉCESSITE SONDE VE]** | Membre candidat plausible mais non localisé, ou instanciation non documentée |
| **capability-check + readback** | Rappel obligatoire : tout membre marqué [EXPOSÉ] reste conditionnel à un capability-check au runtime et à un readback de la valeur modifiée, conformément à la règle de fer du CLAUDE.md |

---

## 1. Famille : `thermal_bridges` — ψ [W/(m·K)] et χ [W/K]

**Valeur de référence SIA 380/2:2022 Tableau 2** : ψ = 0, χ = 0.
**Clé config** : `thermal_bridge_psi_chi = 0.0`.

### 1.1 Résultat de la recherche dans le PDF

- Terme exact **« thermal bridge »** : **absent** du PDF VEScripts-API-VE2023 (recherche
  exhaustive sur 248 pages).
- Terme **« psi »** : présent à la page 9 uniquement — il s'agit du menu de la barre
  d'outils de débogage du script editor (« Run Debugger (Shift + F5) »). Aucun rapport
  avec les ponts thermiques.
- Terme **« chi »** : présent à plusieurs pages mais uniquement comme sous-chaîne de mots
  communs (« machine », « mechanism », etc.) — aucun contexte de pont thermique linéique
  ou ponctuel.
- Aucun objet VE documenté n'expose un attribut `psi`, `chi`, `thermal_bridge_psi`,
  `thermal_bridge_chi`, ni aucun équivalent.

### 1.2 Analyse

L'API VEScripts 2023 ne documente aucune surface de lecture des coefficients de ponts
thermiques (linéiques ψ ou ponctuels χ) du modèle géothermique.

**Cas particulier important pour le projet de référence** : la valeur normative est ψ = χ = 0.
Pour la construction du projet de référence (Pathway B, `# SIA 380/2:2022 7.2.5.3`), la
directive consiste à forcer la contribution des ponts thermiques à zéro dans le modèle de
référence. Cette directive ne requiert pas de lire la valeur projet. Elle demande en revanche
de **savoir comment ApacheSim prend en compte les ponts thermiques** (construction CDB,
paramètre de run, ou simplement absent du moteur thermique) pour déterminer l'action de
substitution — information non documentée dans le PDF VEScripts.

Pour le Pathway A (comparaison valeur projet / limite, `# SIA 380/2:2022 7.2.1.2`), la
valeur projet ψ/χ n'est pas extractible via API.

### 1.3 Verdict

| Grandeur | Statut | Membre API | Page PDF |
|---|---|---|---|
| ψ projet [W/(m·K)] | **NON EXPOSÉ** | — | — |
| χ projet [W/K] | **NON EXPOSÉ** | — | — |
| Action de substitution (forcer ψ=χ=0) | **NÉCESSITE SONDE VE** | mécanisme non documenté | — |

**Conséquence pour l'adaptateur** : la famille `thermal_bridges` reste **hors de portée
de l'API documentée**. Elle ne peut pas être automatisée sans sonde VE dédiée pour
déterminer comment VE/ApacheSim modélise (ou ignore) les ponts thermiques.

---

## 2. Famille : `ventilation_system_and_controls`

**Valeurs de référence SIA 380/2:2022 Tableau 2** (Limite / Cible) :
- εV efficacité de récupération : 1,0 / 1,4
- Classe étanchéité des gaines : C
- Classe étanchéité de l'appareil (AHU) : L2 / L1
- U_ahu,SUP [W/(m²·K)] : 0,7 / 0,5

**Clés config** : `ventilation_efficiency`, `duct_airtightness_class`,
`ahu_airtightness_class`, `ahu_heat_transfer_w_m2k`.

### 2.1 Efficacité de récupération εV

**Objet VE** : `VEApacheSystem` — méthode `ventilation_ncm()` **[PDF p.192]**.

Dictionnaire retourné — clés pertinentes :

| Clé API | Type | Description | Page PDF | Statut |
|---|---|---|---|---|
| `heat_recovery_efficiency` | float | Efficacité de récupération de chaleur saisonnière | p.192 | **[EXPOSÉ-NCM/UK]** |
| `heat_recovery_efficiency_known` | bool | L'efficacité est-elle connue ? | p.192 | **[EXPOSÉ-NCM/UK]** |
| `default_heat_recovery_efficiency` | float | Efficacité de récupération par défaut | p.192 | **[EXPOSÉ-NCM/UK]** |
| `heat_recovery_type` | ncm_heat_recovery_type | Type de récupérateur | p.192 | **[EXPOSÉ-NCM/UK]** |
| `variable_heat_recovery` | bool | Récupération à efficacité variable | p.192 | **[EXPOSÉ-NCM/UK]** |

Valeurs enum `ncm_heat_recovery_type` **[PDF p.193]** :
`no_heat_recovery`, `plate_heat_exchanger`, `heat_pipes`, `thermal_wheel`, `run_around_coil`.

**Réserve NCM/UK** : `ventilation_ncm()` est une méthode spécifique au workflow NCM
(UK Building Regulations). L'efficacité qu'elle retourne est l'entrée utilisateur pour le
calcul SBEM/NCM, pas une valeur mesurée selon une norme SIA/EN. La correspondance entre
`heat_recovery_efficiency` (NCM) et le εV de SIA 380/2 Tableau 2 requiert confirmation
par sonde VE avec un modèle calibré.

Chemin d'accès complet :
```python
# ⚠ capability-check + readback obligatoires en VE réel
import iesve
system = iesve.VEApacheSystem.default()  # ou via project.apache_systems()
vent_ncm = system.ventilation_ncm()
epsilon_v = vent_ncm.get("heat_recovery_efficiency")  # float ou None
```

### 2.2 Classe d'étanchéité des gaines

**Objet VE** : `VEApacheSystem` — méthode `system_adjustment_ncm()` **[PDF p.192]**.

| Clé API | Type | Description | Page PDF | Statut |
|---|---|---|---|---|
| `ductwork_leakage_test` | ncm_leakage_test | Classification CEN de l'étanchéité des gaines | p.192 | **[EXPOSÉ-NCM/UK]** |
| `ductwork_leakage_test_done` | bool | Test d'étanchéité réalisé ? | p.192 | **[EXPOSÉ-NCM/UK]** |

Valeurs enum `ncm_leakage_test` **[PDF p.193]** :
`not_tested`, `class_a`, `class_b`, `class_c`, `class_d`.

**Mise en garde de correspondance** : les classes d'étanchéité des gaines VE
(`class_a`…`class_d`) sont des classes NCM/UK (CIBSE TM44 / EN 12237). La norme
SIA 380/2 Tableau 2 mentionne la classe « C » sans préciser l'EN de référence. La
correspondance class_c (NCM) ↔ classe C (SIA) est plausible mais n'est pas documentée
dans le PDF et doit être confirmée par l'ingénieur SIA ou la sonde VE.

### 2.3 Classe d'étanchéité de l'appareil (AHU)

**Objet VE** : `VEApacheSystem` — méthode `system_adjustment_ncm()` **[PDF p.192]**.

| Clé API | Type | Description | Page PDF | Statut |
|---|---|---|---|---|
| `cen_class` | ncm_leakage_standard | Classification CEN de l'AHU | p.192 | **[EXPOSÉ-NCM/UK]** |
| `ahu_meets_standards` | bool | L'AHU respecte-t-il les standards CEN ? | p.189 (set_), p.191 | **[EXPOSÉ-NCM/UK]** |

Valeurs enum `ncm_leakage_standard` **[PDF p.193]** :
`class_l1`, `class_l2`, `class_l3`, `not_compliant`.

**Correspondance** : `class_l1` → L1 et `class_l2` → L2 de SIA 380/2 est probable mais
non confirmée dans le PDF. Sonde VE requise.

### 2.4 Puissance spécifique des ventilateurs (SFP)

Deux membres candidats localisés :

| Clé API | Objet | Méthode | Unité | Page PDF | Statut |
|---|---|---|---|---|---|
| `SFP` | VEApacheSystem | `auxiliary_energy()` | W/(l/s) | p.181 | **[EXPOSÉ]** |
| `specific_fan_power` | VEApacheSystem | `system_adjustment_ncm()` | float | p.192 | **[EXPOSÉ-NCM/UK]** |

Note : `SFP` dans `auxiliary_energy()` est documenté sans suffixe NCM — c'est le
SFP du système, accessible quel que soit le workflow. `specific_fan_power` dans
`system_adjustment_ncm()` est la valeur NCM saisie manuellement par l'utilisateur.
Pour l'extraction projet, `auxiliary_energy().SFP` est préférable (données modèle directes).

### 2.5 U_ahu,SUP [W/(m²·K)] — coefficient de déperdition thermique de l'AHU

**Résultat de la recherche** : aucun dictionnaire documenté dans le PDF ne contient un
champ `U_ahu`, `ahu_heat_transfer`, `thermal_transmittance_ahu` ou équivalent. La page
191 montre `solar_water_heating_ncm()` avec des champs de pertes thermiques
(canalisations, volume, isolation), mais uniquement pour les chauffe-eau solaires, pas pour
les AHU.

**Statut** : **NON EXPOSÉ** dans l'API VEScripts documentée.

### 2.6 Verdict famille ventilation

| Grandeur SIA 380/2 | Membre API | Objet.méthode | Page | Statut |
|---|---|---|---|---|
| εV efficacité récupération | `heat_recovery_efficiency` | `VEApacheSystem.ventilation_ncm()` | p.192 | **EXPOSÉ-NCM/UK** |
| Type récupérateur | `heat_recovery_type` | `VEApacheSystem.ventilation_ncm()` | p.192 | **EXPOSÉ-NCM/UK** |
| Récupération variable | `variable_heat_recovery` | `VEApacheSystem.ventilation_ncm()` | p.192 | **EXPOSÉ-NCM/UK** |
| Classe gaines | `ductwork_leakage_test` | `VEApacheSystem.system_adjustment_ncm()` | p.192 | **EXPOSÉ-NCM/UK** |
| Classe AHU (L1/L2) | `cen_class` | `VEApacheSystem.system_adjustment_ncm()` | p.192 | **EXPOSÉ-NCM/UK** |
| SFP [W/(l/s)] | `SFP` | `VEApacheSystem.auxiliary_energy()` | p.181 | **EXPOSÉ** |
| U_ahu,SUP [W/(m²·K)] | — | — | — | **NON EXPOSÉ** |

**Conclusion** : εV, type récupérateur, classes d'étanchéité et SFP sont **adapter-faisables**
avec réserve NCM/UK. U_ahu,SUP est **hors de portée de l'API documentée**.

---

## 3. Famille : `emission_system_and_unlimited_capacity`

**Valeurs de référence SIA 380/2:2022 Tableau 2** :
- Type d'émission : convection (radiant_fraction = 0)
- ΦH,max / ΦC,max : illimitée (directive de run, pas une comparaison numérique)

### 3.1 Type d'émission (fraction radiante / convective)

La fraction radiante est exposée à deux niveaux :

**Niveau VERoomData** — méthode `get_apache_systems()` **[PDF p.229]** :

La documentation décrit en prose : « *Heating: size (kW), radiant fraction, supply air
temperature and whether the heating capacity is unlimited* ». La clé correspondante vue
dans la méthode miroir `set_apache_systems()` **[PDF p.233]** est :

| Clé API | Type | Description | Page PDF | Statut |
|---|---|---|---|---|
| `heating_plant_radiant_fraction` | float | Fraction radiante du système de chauffage | p.233, p.242 | **[EXPOSÉ]** |
| `cooling_plant_radiant_fraction` | float | Fraction radiante du système de refroidissement | p.233, p.242 | **[EXPOSÉ]** |

Interprétation : `heating_plant_radiant_fraction = 0.0` → émission 100% convective,
conforme à la directive « par convection » du Tableau 2 SIA 380/2.

**Niveau VEThermalTemplate** — méthode `get_apache_systems()` **[PDF p.242]** :

Ces mêmes clés sont explicitement listées dans le dictionnaire retourné par
`VEThermalTemplate.get_apache_systems()` (p.242), ce qui confirme l'existence des champs.

### 3.2 Capacité illimitée ΦH,max / ΦC,max

**Objet VE** : `VEThermalTemplate` — méthode `get_apache_systems()` **[PDF p.242]**.

| Clé API | Type | Description | Page PDF | Statut |
|---|---|---|---|---|
| `heating_capacity_unlimited` | bool | Capacité de chauffage illimitée | p.242 | **[EXPOSÉ]** |
| `cooling_capacity_unlimited` | bool | Capacité de refroidissement illimitée | p.242 | **[EXPOSÉ]** |

L'enum `heating_cooling_capacity_unit` **[PDF p.245]** confirme :
`unlimited`, `kilowatts`, `watts_per_metre_squared`.

**Note sur VERoomData** : la documentation de `get_apache_systems()` à la page 229 décrit
les mêmes champs en prose (« *whether the heating capacity is unlimited* »). Les clés exactes
dans le dictionnaire retourné ne sont pas listées explicitement — elles sont visibles dans la
méthode miroir `set_apache_systems()` **[PDF p.233]** : `heating_capacity_unlimited` (bool)
et `cooling_capacity_unlimited` (bool). Un capability-check en VE réel reste obligatoire
pour confirmer que `get_apache_systems()` retourne ces clés.

**Accès via VEThermalTemplate recommandé** car le dictionnaire est explicitement documenté.

### 3.3 Directive vs comparaison

ΦH,max / ΦC,max « illimitée » est une **directive de run** du projet de référence
(`# SIA 380/2:2022 Tableau 2`) : dans le modèle de référence, les capacités ne doivent pas
contraindre le calcul. Il n'y a donc **pas de valeur projet à extraire** pour cette
grandeur. L'adaptateur doit seulement vérifier (ou forcer) le flag boolean à `True` dans
le modèle de référence, pas comparer une valeur numérique.

### 3.4 Verdict famille émission

| Grandeur SIA 380/2 | Membre API | Objet.méthode | Page | Statut |
|---|---|---|---|---|
| Fraction radiante chauffage | `heating_plant_radiant_fraction` | `VEThermalTemplate.get_apache_systems()` | p.242 | **EXPOSÉ** |
| Fraction radiante refroidissement | `cooling_plant_radiant_fraction` | `VEThermalTemplate.get_apache_systems()` | p.242 | **EXPOSÉ** |
| Capacité chauffage illimitée (bool) | `heating_capacity_unlimited` | `VEThermalTemplate.get_apache_systems()` | p.242 | **EXPOSÉ** |
| Capacité refroidissement illimitée (bool) | `cooling_capacity_unlimited` | `VEThermalTemplate.get_apache_systems()` | p.242 | **EXPOSÉ** |
| ΦH,max / ΦC,max valeur numérique projet | (directive, pas extraction) | — | — | **NON APPLICABLE** |

**Conclusion** : famille **adapter-faisable** (fraction radiante + capacité illimitée).
Capability-check + readback obligatoires en VE réel, notamment pour `VERoomData.get_apache_systems()`.

---

## 4. Famille : `cooling_generation_and_auxiliaries` — EER/SEER projet

**Valeur de référence SIA 380/2:2022** : EER/SEER calculé à partir du Tableau 5-9
(non codé dans `SIA3802_LIMIT_VALUES` car dépend du type de générateur). L'extraction
vise la **valeur projet**.

### 4.1 Membres API localisés

**Objet VE** : `VEApacheSystem` — méthode `cooling()` **[PDF p.182]**.

| Clé API | Type | Unité | Description | Page PDF | Statut |
|---|---|---|---|---|---|
| `nominal_eer` | float | kW/kW | EER nominal du générateur | p.182 | **[EXPOSÉ]** |
| `SEER` | float | kW/kW | Efficacité énergétique saisonnière | p.182 | **[EXPOSÉ]** |
| `SSEER` | float | kW/kW | Efficacité énergétique saisonnière système | p.182 | **[EXPOSÉ]** |

Via méthode `cooling_ncm()` **[PDF p.182]** :

| Clé API | Type | Description | Page PDF | Statut |
|---|---|---|---|---|
| `generator_nominal_eer` | float | EER nominal (NCM) | p.182 | **[EXPOSÉ-NCM/UK]** |
| `generator_seasonal_eer` | float | EER saisonnier (NCM) | p.182 | **[EXPOSÉ-NCM/UK]** |
| `generator_nominal_eer_known` | bool | EER nominal connu ? | p.182 | **[EXPOSÉ-NCM/UK]** |
| `generator_seasonal_eer_known` | bool | EER saisonnier connu ? | p.182 | **[EXPOSÉ-NCM/UK]** |

Champ complémentaire utile :

| Clé API | Type | Description | Page PDF | Statut |
|---|---|---|---|---|
| `has_absorption_chiller` | bool | Présence d'un groupe à absorption | p.182 | **[EXPOSÉ]** |

### 4.2 Chemin d'accès

```python
# ⚠ capability-check + readback obligatoires en VE réel
import iesve
project = iesve.VEProject.get_current_project()
for system in project.apache_systems():
    cooling = system.cooling()       # dict [PDF p.182]
    eer     = cooling.get("nominal_eer")   # float kW/kW ou None
    seer    = cooling.get("SEER")          # float kW/kW ou None
```

### 4.3 Verdict famille refroidissement

| Grandeur | Membre API | Objet.méthode | Page | Statut |
|---|---|---|---|---|
| EER nominal projet | `nominal_eer` | `VEApacheSystem.cooling()` | p.182 | **EXPOSÉ** |
| SEER projet | `SEER` | `VEApacheSystem.cooling()` | p.182 | **EXPOSÉ** |
| SSEER projet | `SSEER` | `VEApacheSystem.cooling()` | p.182 | **EXPOSÉ** |

**Conclusion** : famille **adapter-faisable**. Déjà partiellement extraite dans
`model_analyzer.py` (`eer`, `seer`, `sseer` dans `_analyze_hvac_systems`).

---

## 5. Famille : `heating_generation` — SCOP/rendement projet

**Valeur de référence SIA 380/2:2022** : SCOP/rendement calculé à partir des Tableaux
8-9 (dépend du type de générateur). L'extraction vise la **valeur projet**.

### 5.1 Membres API localisés

**Objet VE** : `VEApacheSystem` — méthode `heating()` **[PDF p.183]**.

| Clé API | Type | Unité | Description | Page PDF | Statut |
|---|---|---|---|---|---|
| `SCoP` | float | kW/kW | Coefficient de performance saisonnier | p.183 | **[EXPOSÉ]** |
| `gen_seasonal_eff` | float | — | Efficacité saisonnière du générateur | p.183 | **[EXPOSÉ]** |
| `Is_heat_pump` | bool | — | Le générateur est-il une pompe à chaleur ? | p.183 | **[EXPOSÉ]** |
| `del_eff` | float | — | Efficacité de distribution | p.183 | **[EXPOSÉ]** |
| `fuel` | int | — | Combustible (voir `fuel_names()`) | p.183 | **[EXPOSÉ]** |

Via méthode `heating_ncm()` **[PDF p.183]** :

| Clé API | Type | Description | Page PDF | Statut |
|---|---|---|---|---|
| `generator_seasonal_efficiency` | float | Efficacité saisonnière (NCM) | p.183 | **[EXPOSÉ-NCM/UK]** |
| `generator_seasonal_efficiency_known` | bool | Efficacité connue ? | p.183 | **[EXPOSÉ-NCM/UK]** |
| `heat_source` | ncm_heat_source | Type de source de chaleur | p.183 | **[EXPOSÉ-NCM/UK]** |

Valeurs enum `ncm_heat_source` **[PDF p.193]** (extrait pertinent) :
`lthw_boiler`, `heat_pump_electric_air_source`, `heat_pump_electric_ground_or_water_source`,
`district_heating`, etc.

### 5.2 Chemin d'accès

```python
# ⚠ capability-check + readback obligatoires en VE réel
import iesve
project = iesve.VEProject.get_current_project()
for system in project.apache_systems():
    heating = system.heating()           # dict [PDF p.183]
    scop    = heating.get("SCoP")        # float kW/kW ou None
    seff    = heating.get("gen_seasonal_eff")   # float ou None
    is_hp   = heating.get("Is_heat_pump")       # bool ou None
```

### 5.3 Verdict famille chauffage

| Grandeur | Membre API | Objet.méthode | Page | Statut |
|---|---|---|---|---|
| SCOP projet | `SCoP` | `VEApacheSystem.heating()` | p.183 | **EXPOSÉ** |
| Rendement saisonnier | `gen_seasonal_eff` | `VEApacheSystem.heating()` | p.183 | **EXPOSÉ** |
| Type pompe à chaleur | `Is_heat_pump` | `VEApacheSystem.heating()` | p.183 | **EXPOSÉ** |

**Conclusion** : famille **adapter-faisable**. Déjà partiellement extraite dans
`model_analyzer.py` (`scop` dans `_analyze_hvac_systems`).

---

## 6. Famille : `photovoltaic_generation`

**Valeurs de référence SIA 380/2:2022 Tableau 2** (config) :
- `pv_power_w_per_m2_sre = 10` W/m²·SRE (puissance PV par m² de SRE)
- `pv_conversion_efficiency = 0.90` (efficacité de conversion globale)

L'extraction vise les **entrées de modèle** (surface, efficacité configurées par
l'utilisateur), non les **résultats de simulation** (production annuelle kWh).

### 6.1 Accès à l'objet VERenewables

La hiérarchie de classes **[PDF p.18-19]** montre `VERenewables` au même niveau que
`VEProject` et `VEApacheSystem`, instanciable directement via `iesve.VERenewables()`.
Cependant, **aucun exemple d'instanciation n'est documenté dans le PDF** (ni méthode
statique `get_current_renewables()`, ni attribut sur VEProject). Ce point nécessite une
**sonde VE réelle** pour confirmer l'instanciation correcte.

### 6.2 Entrées de modèle PV documentées

**Objet VE** : `VERenewables` — méthode `get_pv_data()` **[PDF p.225]**.

| Clé API | Type | Description | Page PDF | Statut |
|---|---|---|---|---|
| `area` | float | Surface du panneau PV (m²) | p.225 | **[EXPOSÉ]** |
| `cell_efficiency` | float | Efficacité de cellule | p.225 | **[EXPOSÉ]** |
| `azimuth` | float | Azimut du PV | p.225 | **[EXPOSÉ]** |
| `inclination` | float | Inclinaison du PV | p.225 | **[EXPOSÉ]** |
| `shading_factor` | float | Facteur d'ombrage | p.225 | **[EXPOSÉ]** |
| `type_id` | string | ID du type PV → renvoi vers `get_pv_type_by_id()` | p.225 | **[EXPOSÉ]** |
| `id` | string | ID du panneau PV | p.225 | **[EXPOSÉ]** |

**Objet VE** : `VERenewables` — méthode `get_pv_type_by_id(id)` **[PDF p.226]**.

| Clé API | Type | Description | Page PDF | Statut |
|---|---|---|---|---|
| `electrical_conversion_efficiency` | float | Efficacité de conversion électrique | p.226 | **[EXPOSÉ]** |
| `module_nominal_efficiency` | float | Efficacité nominale du module | p.226 | **[EXPOSÉ]** |
| `technology` | string | Technologie PV | p.226 | **[EXPOSÉ]** |
| `degradation_factor` | float | Facteur de dégradation | p.226 | **[EXPOSÉ]** |

### 6.3 Résultats de simulation PV (vs entrées de modèle)

Le résultat de **production PV annuelle** est accessible via `ResultsReader` avec l'enum
`EnergyUse.prm_elec_gen_pv` **[PDF p.159]**. Ce sont des résultats de simulation
(`ResultsReader.get_results()`), pas des entrées configurées par l'utilisateur.

**Pour la construction du projet de référence**, c'est la **valeur projet configurée**
(surface × efficacité) qui est pertinente, non le résultat simulé.

### 6.4 Correspondance avec les clés config SIA

| Clé config SIA | Membre API candidat | Méthode | Page | Note |
|---|---|---|---|---|
| `pv_power_w_per_m2_sre` (10 W/m²·SRE) | (valeur normative, pas extraction) | — | — | Valeur de référence, pas valeur projet |
| `pv_conversion_efficiency` (0.90) | `electrical_conversion_efficiency` | `get_pv_type_by_id()` | p.226 | Correspondance à confirmer |
| Surface installée [m²] | `area` (par panneau) | `get_pv_data()` | p.225 | Somme sur tous les panneaux |

### 6.5 Puissance installée totale

Il n'existe pas de membre direct « puissance totale installée » dans l'API. Elle se dérive :

```
P_installed [W] = sum_i( area[i] × cell_efficiency[i] ) × ref_irradiance
```

Cette dérivation n'est pas documentée dans le PDF comme un membre API direct.

### 6.6 Verdict famille photovoltaïque

| Grandeur | Membre API | Objet.méthode | Page | Statut |
|---|---|---|---|---|
| Surface panneau [m²] | `area` | `VERenewables.get_pv_data()` | p.225 | **EXPOSÉ** |
| Efficacité de cellule | `cell_efficiency` | `VERenewables.get_pv_data()` | p.225 | **EXPOSÉ** |
| Efficacité de conversion | `electrical_conversion_efficiency` | `VERenewables.get_pv_type_by_id()` | p.226 | **EXPOSÉ** |
| Puissance totale installée | (dérivée, non membre direct) | — | — | **NÉCESSITE SONDE VE** |
| Instanciation VERenewables | `iesve.VERenewables()` | — | p.18-19 (hiérarchie) | **NÉCESSITE SONDE VE** |

**Conclusion** : les entrées de modèle sont **adapter-faisables** sous réserve de
confirmation de l'instanciation de `VERenewables` et de la dérivation de la puissance
totale. La distinction données modèle / résultats simulation doit être respectée
(ne jamais utiliser les résultats du `ResultsReader` comme valeur projet configurée).

---

## 7. Résumé de faisabilité

### 7.1 Tableau récapitulatif

| Famille | Verdict global | Membre(s) clé(s) | Page PDF | Blocage résiduel |
|---|---|---|---|---|
| `thermal_bridges` | **HORS DE PORTÉE API** | aucun trouvé | — | Aucun accès ψ/χ documenté ; mécanisme de substitution VE inconnu |
| `ventilation_system_and_controls` | **PARTIELLEMENT FAISABLE** | `heat_recovery_efficiency`, `cen_class`, `ductwork_leakage_test`, `SFP` | p.181, p.192 | U_ahu,SUP absent ; correspondance NCM/UK ↔ SIA à confirmer |
| `emission_system_and_unlimited_capacity` | **FAISABLE** | `heating_plant_radiant_fraction`, `heating_capacity_unlimited`, `cooling_capacity_unlimited` | p.229, p.242 | Capability-check requis sur `VERoomData.get_apache_systems()` |
| `cooling_generation_and_auxiliaries` | **FAISABLE** (déjà partiellement extrait) | `nominal_eer`, `SEER`, `SSEER` | p.182 | Aucun (extraction existante dans `model_analyzer.py`) |
| `heating_generation` | **FAISABLE** (déjà partiellement extrait) | `SCoP`, `gen_seasonal_eff` | p.183 | Aucun (extraction existante dans `model_analyzer.py`) |
| `photovoltaic_generation` | **FAISABLE sous conditions** | `area`, `cell_efficiency`, `electrical_conversion_efficiency` | p.225, p.226 | Instanciation VERenewables à confirmer ; puissance totale dérivée |

### 7.2 Priorité d'implémentation suggérée

1. **`emission_system_and_unlimited_capacity`** : membres explicitement documentés dans
   `VEThermalTemplate` (p.242), faisabilité haute. Valeur normative binaire (bool).

2. **`cooling_generation_and_auxiliaries`** et **`heating_generation`** : membres déjà
   extraits dans `model_analyzer.py` — il suffit d'ajouter la famille dans
   `IMPLEMENTED_REFERENCE_INPUT_FAMILIES` avec leur logique de substitution.

3. **`photovoltaic_generation`** : faisable après confirmation de l'instanciation de
   `VERenewables` par sonde VE.

4. **`ventilation_system_and_controls`** : faisable pour εV, classes et SFP, mais le
   contexte NCM/UK requiert une validation sémantique avant de produire un verdict
   `SUBSTITUTABLE`. U_ahu,SUP reste bloqué.

5. **`thermal_bridges`** : non faisable par API documentée. Escalade requise vers l'équipe
   produit VE ou implémentation par sonde VE dédiée.

### 7.3 Invariants obligatoires pour toute implémentation

- Tout membre marqué [EXPOSÉ] ou [EXPOSÉ-NCM/UK] dans ce document reste conditionnel à
  un **capability-check au runtime** (`hasattr` + try/except) et à un **readback** de
  la valeur après toute mutation, conformément aux règles de fer du projet.
- Les méthodes `*_ncm()` de `VEApacheSystem` ne sont présentes que dans les modèles
  configurés en mode NCM. Un modèle Apache HVAC pur ne les retournera pas — le code
  adapter doit gérer cette absence sans exception fatale.
- Une valeur retournée `None` par l'API est distincte d'une valeur `0.0` : `None` signifie
  « non renseignée dans le modèle », jamais substitué à une valeur par défaut.
- Ce document ne modifie aucun fichier de code de production.

---

## 8. Sources

| Source | Localisation | Lecture |
|---|---|---|
| VEScripts-API-VE2023.pdf (248 pages) | `refs/VEScripts-API-VE2023.pdf` | Extraction PyMuPDF ciblée, pages 3, 9, 18-19, 47, 56, 63, 65, 85, 95, 97-100, 102, 115, 159, 175-176, 181-193, 225-233, 242, 245 |
| `swiss_sia/reference_project.py` | codebase | Familles IMPLEMENTED / MISSING, lues intégralement |
| `swiss_sia/model_analyzer.py` | codebase | Champs `RoomData`, `_analyze_hvac_systems`, lus intégralement |
| `swiss_sia/data_extractor.py` | codebase | Méthodes d'extraction existantes, lues intégralement |
| `swiss_sia/config.py` | codebase | `SIA3802_LIMIT_VALUES`, lu |
| `traceability/sia380-2-pathway.spec.md` | codebase | Tableau 2 Limite/Cible, §3.2 Mapping |

**SIA 380/2:2022 Tableau 2** : source normative primaire pour les valeurs de référence.
Aucune valeur limite ou cible n'est inventée ou interpolée dans ce document.
