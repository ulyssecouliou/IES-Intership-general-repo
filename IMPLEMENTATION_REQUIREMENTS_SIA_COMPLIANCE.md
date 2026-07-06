# Plan d'implémentation complète - Conformité SIA 380-2 et 4010

**Version:** 2026-07-03  
**Statut actuel:** Les modèles passant le script SIA4010Checker ne sont **PAS** compliant suisse.  
**Raison:** Le checker ne validait que ~40% des exigences SIA 380/2 et ~15% de SIA 4010.  
**Destination:** Donner tout ceci à Claude Code pour implémenter.

---

## Executive Summary

**Conclusion:** Un modèle déclaré "READY_FOR_OFFICIAL_REVIEW" par le checker actuel ne peut **PAS** être présenté comme conforme SIA 380-2 ou SIA 4010 sans:
1. Extraction complète de TOUTES les données obligatoires SIA depuis IESVE
2. Vérification de TOUTES les exigences SIA 380/2 Tableaux 2-10
3. Contrôle des conditions SIA 4010 (climat, puissances dynamiques, conditions)
4. Lien entre les données extraites et les normes externes (SIA 2024, SIA 387/4, SIA 2028)
5. Preuves documentaires auditables pour chaque seuil/décision

**Impact:** Le code doit:
- Enrichir l'extraction VE d'au moins **50 nouvelles métriques**
- Ajouter ~25 nouvelles règles SIA 380/2
- Ajouter ~15 nouvelles règles SIA 4010
- Générer un rapport de **preuve** avec traçabilité PDF SIA

---

## PART 1: DONNÉES À EXTRAIRE DE IESVE (Non implémentées)

### 1.1 Données projet manquantes

| Donnée | Type | Source IESVE | Utilité | Priorité |
|--------|------|-------------|---------|----------|
| Version logiciel IESVE | texte | API IESVE | Traçabilité logiciel; SIA 4010 validation | **HAUTE** |
| Moteur de calcul utilisé | texte | config projet | Statut SIA 4010 pour IESVE | **HAUTE** |
| Fichier météo utilisé | chemin fichier | ApacheSim config | Validation SIA 2028/DRY; SIA 4010 section 3.1.1 | **HAUTE** |
| Station climatique | texte | métadonnées météo | Alignment SIA 2028; variantes 2035 RCP 8.5 | **HAUTE** |
| Scénario climatique (RCP/année) | texte | ApacheSim | SIA 4010 recommande RCP 8.5/2035 pour surchauffe | **HAUTE** |
| Calendrier de référence | texte | projet | Éviter weekends pour puissances ref. (SIA 4010) | **MOYENNE** |
| Pas de temps simulation | entier (min) | ApacheSim | SIA 380/2 demande horaire | **MOYENNE** |
| Période de simulation chauffage | dates | Vista résultats | Capture jours froids SIA 4010 / pré-cond 14j | **HAUTE** |
| Période de simulation refroidissement | dates | Vista résultats | Capture jours chauds SIA 4010 / pré-cond 14j | **HAUTE** |
| Résultats APS chauffage (fichier) | chemin | Vista export | Puissances horaires chauffage pour ref. | **HAUTE** |
| Résultats APS refroidissement (fichier) | chemin | Vista export | Puissances horaires refroidissement pour ref. | **HAUTE** |
| Type de bâtiment (usage principal) | texte | propriétés projet | SIA 2024 profil par usage | **MOYENNE** |

### 1.2 Données de surface (Modèle thermique) - Manquantes ou incomplètes

#### 1.2.1 Classification des surfaces opaques

Actuellement: le checker traite "external_wall", "roof", "floor" comme fallback.  
Exigence SIA 380/2 Tableau 3: identifier précisément chaque type pour appliquer le U correct.

| Type de surface | U limite SIA | Conditions d'extraction VE | Nouveau champ code |
|---|---:|---|---|
| Mur extérieur | 0.20 | Orientation, surface brute/nette | `surface_type_exact` |
| Mur contre terrain | 0.30 | Profondeur, surface de contact | `wall_against_ground_depth_m` |
| Paroi interne non porteuse | 0.30 | Locaux non climatisés adjacents | `internal_partition_non_bearing` |
| Paroi interne porteuse | 2.70 | Pas de contrôle SIA enveloppe | `internal_partition_bearing` |
| Paroi interne contre local non climatisé | 0.28 → 0.20 | Identification local non-conditionné | `internal_wall_unconditioned_side` |
| Sol contre terrain | 0.30 → 0.20 | Profondeur, année constru. | `floor_against_ground_depth_m` |
| Plancher intermédiaire | 0.64 | Locaux climatisés des 2 côtés | `intermediate_floor_conditioned_both_sides` |
| Plancher intermédiaire contre cave non-cond. | 0.30 → 0.20 | Cave non-chauffée identifiée | `floor_unconditioned_side` |
| Toiture plate | 0.20 | Pente < 5° | `roof_pitch_degrees` |
| Toiture avec pente | 0.20 (ref) | Pente >= 5°; orientation | `roof_pitch_degrees`, `roof_orientation` |

**Action code:** 
- Enrichir `model_analyzer.py` / `RoomData` / `Surface` avec champ `surface_type_precise` (enum)
- Lire depuis IESVE API: type d'élément via `iesve.element.type`, conditions de bord, adjacent zones
- Appliquer le U correct en fonction du type exact dans `sia380_checker.py`
- **Règle:** Si type de surface ne peut pas être déterminé avec certitude → EVIDENCE_MISSING au lieu de fallback

#### 1.2.2 Données sur les surfaces (champs manquants)

| Donnée | Format | Source IESVE | Raison |
|--------|--------|--------------|--------|
| Orientation surface | deg (N=0, E=90, S=180, W=270) | `Surface.orientation` | Impacts solaire, dimensionnement; SIA 2024 |
| Pente surface | deg ou % | `Surface.pitch` | Différence toiture/murs; SIA 4010 |
| Surface nette vs brute | m2 pour chaque | `Surface.net_area`, `Surface.gross_area` | Calculs pont thermique; SIA 380/2 |
| Pont thermique linéaire | W/(m.K) | `Surface.linear_thermal_bridge` ou CDB | SIA 380/2 tableau 2; actuellement = 0 |
| Pont thermique ponctuel | W/K | CDB / connections | SIA 380/2 tableau 2; actuellement = 0 |
| Facteur de conversion température | - | CDB / sol+terrain | Calcul besoins pour surfaces partiellement non-cond. |

**Action code:**
- Parser depuis IESVE: `orientation`, `pitch`, `linear_thermal_bridge_psi`, `punctual_thermal_bridge_chi`
- Extraire surface nette = brute - cadrements/stores (SIA 380/2)
- Lier à CDB: si pont thermique non fourni par élément, chercher par type de jonction
- **Règle:** Pont thermique = 0 est acceptable seulement avec justification explicite du projet

### 1.3 Données sur les ouvertures - Manquantes

#### 1.3.1 Paramètres vitrage détaillés

Actuellement: U-value, solar_factor (g), visible_transmittance, frame_fraction sont codés.  
Manquent: traçabilité source, type de verre, origine données g.

| Donnée | Format | Source IESVE | Raison | Nouveau champ |
|--------|--------|--------------|--------|---|
| Référence standard verre | texte (EN 410 code) | Base données verre | Preuve que g = valeur SIA | `glazing_standard_reference` |
| g perp (solaire perpendiculaire) | 0-1 | Fiche technique | SIA 380/2 demande g_perp; pas g_hém | `g_perp_en410` |
| g hémi (solaire hémisphérique) | 0-1 | Fiche technique | Alternative si g_perp absent | `g_hemispherical_en410` |
| Épaisseur lame air | mm | Fiche technique | Calcul conduction cadre; impact U | `glazing_air_gap_mm` |
| Type de gaz remplissage | texte (Air, Argon, Krypton) | Fiche technique | Impact U-value | `glazing_fill_gas_type` |
| Nombre de parois vitrées | entier | Fiche technique | Impact U-value et g | `glazing_pane_count` |
| Transmission lumineuse (tau) | 0-1 | Fiche technique (EN 410) | SIA 380/2 table 2: tau >= 0.70 | `light_transmittance_tau_en410` |
| Source donnée g-value | enum | metadata | Preuve d'origine (datasheet/calcul/ref) | `g_value_source_method` |
| Catégorie protection solaire (si stores) | 1-5 | Fiche store | SIA 380/2 tableau 10 | `shading_category_sia` |
| Réflectance store (si tissu) | 0-1 | Fiche store | SIA 380/2 tableau 10 | `shading_reflectance` |
| Transmittance store (si tissu) | 0-1 | Fiche store | SIA 380/2 tableau 10 | `shading_transmittance` |
| g total (vitrage + store actif) | 0-1 | Calc SN EN ISO 52022-3 | Alternative pour g+store | `g_total_with_shading` |
| Seuil de commande stores | W/m2 ou lux | Stratégie de contrôle | SIA 387/4 commande stores | `shading_control_threshold` |
| Type de commande stores | enum | Stratégie de contrôle | Manuel, auto-irradiance, auto-température, capteur | `shading_control_type` |

**Action code:**
- Enrichir `Opening` class: ajouter tous ces champs
- Créer nouvelle règle SIA380/2: "demander g_perp; si absent ET pas de preuve calc → evidence_missing"
- Créer calcul g_total si stores présents (utiliser formule SN EN ISO 52022-3)
- Lier à base de données: glazing + shading tables communes pour validation rapide
- **Règle validation:** g fourni vs g SIA seuil → comparaison stricte (pas d'approximation)

#### 1.3.2 Données cadre et menuiserie

| Donnée | Format | Source IESVE | Raison | Nouveau champ |
|--------|--------|--------------|--------|---|
| Largeur cadre | mm | Fiche fenêtre ou mesure | Part cadre = ff = W_cadre/W_total | `frame_width_mm` |
| Profondeur cadre | mm | Fiche fenêtre | Impact sur mesure/calculs | `frame_depth_mm` |
| Matériau cadre | enum | Fiche fenêtre | Bois, alu, PVC, fibre composite | `frame_material_type` |
| U cadre | W/(m².K) | Fiche fenêtre (EN 10077-1) | Calcul Uw réal. vs déclaré | `frame_u_value` |
| Espacement intercalaire | mm | Fiche fenêtre | Pont thermique intercalaire | `spacer_width_mm` |
| Type intercalaire | enum | Fiche fenêtre | Alum. chaud, alum., plastique | `spacer_type_thermal` |
| Largeur totale ouverture | m | VE extraction | Calcul cadre fraction exacte | `opening_total_width_m` |
| Hauteur totale ouverture | m | VE extraction | Calcul cadre fraction exacte | `opening_total_height_m` |

**Action code:**
- Calculer `frame_fraction_actual = (2*W_cadre*H + 2*W_cadre*L - 4*W_cadre²) / (H*L)` = SIA 380/2 ff formule réelle
- Comparer avec `ff_declared` → alerte si écart > 5%
- **Règle:** ff = 0.25 est limite SIA; vérifier ou demander justification

#### 1.3.3 Données orientations et surfaces

| Donnée | Format | Nouvelle règle |
|--------|--------|---|
| Orientation ouverture | deg (N=0, E=90, S=180, W=270) | SIA 2024 profil solaire par orientation |
| Surface brute (y.c. cadre) | m² | SIA 380/2 calculs |
| Surface nette (vitrée seul.) | m² | SIA 380/2 calculs |
| Part surface vitrée de la paroi | ratio | SIA 2024 / SIA 387/4 |
| Paroi support (nord/sud/est/ouest) | texte | SIA 2024 données par orientation |

### 1.4 Données ventilation - Manquantes ou incomplètes

#### 1.4.1 Débits de ventilation exigés par SIA 380/2 Tableau 4

Actuellement: le code dit "ventilation_rate_min = None".  
Exigence SIA 380/2 Tableau 4: débit air = fonction (zone monozone? multizone?), débit air neuf [m³/(h.m²)], type de commande.

| Donnée | Format | Source IESVE | Raison SIA |
|--------|--------|--------------|-----------|
| Type zonage ventilation | enum (monozone/multizone) | Apache AHU config | SIA 380/2 table 4 débit/contrôle |
| Débit air neuf nominal | m³/h | Apache AHU spec. | Débit = f(table 4) = f(surface zone + occupation) |
| Débit air neuf par m² surface | m³/(h.m²) | Calc = débit / surface zone | SIA 380/2 table 4 seuil: ≤3, 3-6, >6 |
| Débit air extrait | m³/h | Apache AHU spec. | Équilibre; SIA 387/4 exfiltration |
| Classement étanchéité gaines | class (A/B/C) | Fiche gaines / AS projet | SIA 380/2 limite = C; cible = C |
| Classement étanchéité AHU | class (L1/L2/L3) | Fiche AHU / dossier technique | SIA 380/2 limite = L2; cible = L1 |
| Efficacité récupération thermique | ratio (0-1) | Fiche AHU / norme EN 13053 | SIA 380/2 Température: limite 0.73, cible 0.78 |
| Efficacité récupération humidité | ratio (0-1) | Fiche AHU / norme EN 13053 | SIA 380/2 Humidité: limite 0.0, cible 0.60 |
| U-value CTA zone non-cond. | W/(m².K) | Fiche CTA isol. | SIA 380/2 limite 0.70, cible 0.50 |
| Perte thermique CTA zone non-cond. | W/K | Calc. surface * U | SIA 380/2 |
| Perte thermique gaines zone non-cond. | W/K | Calc. perimeter * H | SIA 380/2 limite 15 W/K, cible 10 W/K |
| Perte charge air neuf (supply) | Pa | Fiche AHU + réseau | SIA 380/2 limite 700 Pa, cible 550 Pa |
| Perte charge air repris (extract) | Pa | Fiche AHU + réseau | SIA 380/2 limite 500 Pa, cible 350 Pa |
| Perte charge récupération thermique | Pa | Fiche AHU | SIA 380/2 limite 300 Pa, cible 400 Pa (!! note bizarre dans PDF) |
| Commande ventilation type | enum | Apache config | SIA 380/2 table 4: 1 vitesse, 2 vitesses, variable ≥25% |
| Commande ventilation détection | enum | Capteurs Apache | SIA 380/2 table 4: horloge, occupants, gaz CO2 |
| Commande par zone (si multizone) | bool | Apache zone control | SIA 380/2 table 4: par zone obligatoire |
| Filtre air catégorie | enum (G4/F7/H11/H13) | Fiche filtration | SIA 380/2 tableau 2 implicite / SIA 2024 |
| Humidification (si présente) | bool | Apache humidity | SIA 4010 section 3.1.1: stores tissu + confort |
| Type commande humidification | enum | Apache hygrostat | Rh%, température, cogénération |

**Action code:**
- Créer classe `VentilationSystem` avec tous ces champs
- Implémenter extraction Apache AHU via IESVE API
- Créer règle SIA380/2: vérifier (monozone/multizone) + (débit m³/h.m²) → appliquer bonne ligne table 4
- Créer alertes:
  - Si débit m³/h.m² non fourni → devoir appeler SIA 2024
  - Si commande = horloge ET débit > 6 m³/h.m² → FAIL (minimum = variable ≥25%)
  - Si multizone ET pas de commande par zone → FAIL
  - Si étanchéité gaines > C → WARNING
  - Si étanchéité AHU > L2 → WARNING
  - Si récupération thermique < 0.73 → FAIL
  - Si gaines en zone non-cond. ET perte > 15 W/K → FAIL

#### 1.4.2 Infiltration d'air - Exigence SIA 380/2 Tableau 2

Actuellement: règle code `infiltration_m3_h_m2 <= 0.15`.  
Manquent: données VE sur l'infiltration et sa traçabilité.

| Donnée | Format | Source IESVE | Raison |
|--------|--------|--------------|--------|
| Infiltration déclarée (n50) | h⁻¹ | Fiche ventilation / test pressurisation | VE peut exporter n50 depuis matériaux |
| Infiltration nominal m3/(h.m2) | ratio | Calc. n50 → infiltration typique | Convertir test pressurisation (n50) → nominal |
| Conversion facteur | - | SIA 2028 ou standard | "Facteur 20" standard: nominal = n50/20 |
| Source infiltration | enum | Métadonnées VE | Mesure, hypothèse, test pressurisation |
| Justification si n50 absent | texte | Dossier projet | SIA 380/2: justifier hypothèse conservative |

**Action code:**
- Enrichir extraction VE: lire `infiltration_n50` depuis simulation ou données d'entrée
- Implémenter conversion: `infiltration_nominal = n50 / 20`
- Créer règle SIA380/2: comparer avec 0.15 m³/(h.m²)
- Créer alerte: si infiltration absent → demander justification OR utiliser 0.15 conservative

### 1.5 Données sur l'éclairage et commandes - Manquantes

Actuellement: le code dit "lighting_power_max = None".  
Exigence SIA 380/2: pas de seuil direct; renvoie à SIA 387/4 et SIA 2024.

| Donnée | Format | Source IESVE | Raison |
|--------|--------|--------------|--------|
| Puissance éclairage nominal | W/m² | Zone thermique ApacheSim | SIA 387/4 tableau 9 par usage |
| Efficacité éclairage (luminaire) | lm/W | Fiche luminaires | SIA 387/4 donnée |
| Type lampes | enum (LED/halogène/fluorescent) | Fiche luminaires | Impact efficacité et durée |
| Densité puissance installée | W/m² | Somme luminaires / surface zone | SIA 387/4 limite par usage |
| Commande éclairage type | enum (manuel/horloge/daylight/occupancy) | Apache config | SIA 387/4 tableau 9 catégories |
| Réduction luminosité si lumière jour | ratio (%) | Apache daylight config | SIA 387/4: commande daylight gain ~20-30% |
| Réduction luminosité si inoccupation | ratio (%) | Apache occupancy config | SIA 387/4: commande présence gain ~15-20% |
| Facteur de lumière du jour moyen | ratio (%) | Calcul ou données zone | SIA 387/4: indicateur confort visuel |
| Zone de travail vs circulation | classification | VE zone classification | SIA 387/4: seuils différents |
| Référence SIA 2024 usage | texte (ex. 2.05) | Classification zone usage | SIA 2024 profil éclairage |

**Action code:**
- Enrichir extraction VE: lire Apache `lighting_power_density` W/m²
- Créer classe `LightingData` avec tous les champs
- Implémenter règles SIA387/4 par type d'usage SIA 2024 (créer lookup table)
- **Règle:** Pas de verdict PASS/FAIL direct; générer Evidence Required (lien SIA 2024 usage)
- Générer alerte: "Éclairage: vérifier puissance vs SIA 387/4 usage [X] → seuil y W/m²"

### 1.6 Données équipements internes et gains - Manquantes

Actuellement: le code dit "equipment_power_max = None".  
Exigence SIA 380/2: pas de seuil direct; renvoie à SIA 2024 profils d'usage.

| Donnée | Format | Source IESVE | Raison SIA 2024 |
|--------|--------|--------------|---|
| Puissance équipements nominal | W/m² | Zone ApacheSim | SIA 2024: tableau gains internes par usage |
| Type équipements | enum (informatique/bureautique/cuisine/autre) | Classification zone | SIA 2024: profils énergétiques |
| Gain interne équipements | W | Calcul = puissance * facteur d'utilisation | SIA 2024: profils d'usage |
| Facteur d'utilisation équipements | ratio (0-1) | SIA 2024 profil | SIA 2024: dépend du type zone / horaires |
| Gain interne personnes | W/personne | SIA 2024 standard (~100 W/pers) | SIA 2024: tableau 2 |
| Densité personnes | pers/m² | Zone classification | SIA 2024: par type de zone (bureau = 0.07, réunion = 1.0, etc.) |
| Horaires occupation profil | texte (fichier ou type) | Apache occupancy profile | SIA 2024: profils heures de bureau, etc. |
| Gain interne autres sources | W/m² | VE données d'entrée | Cuisson, procédé, etc. |
| Référence SIA 2024 usage principal | texte (ex. 2.05) | Zone classification usage | SIA 2024 lookup |
| Profil d'utilisation complet | enum | ApacheSim profil | SIA 2024 profil numéro complet |

**Action code:**
- Enrichir extraction VE: lire `equipment_power_density`, `occupant_density`, profils usage
- Créer classe `InteriorGains` avec tous les champs
- Lier à base de données SIA 2024: lookup usage → profil énergétique → gains internes attendus
- **Règle:** Comparer donnée VE vs SIA 2024 profil → Evidence Required (preuve source donnée)
- Générer alerte: "Équipements: zone usage [X] (SIA 2024 [Y.Z]) → gains internes attendus = W/m² selon norme"

### 1.7 Données systèmes chauffage - Manquantes

Actuellement: le code ne traite pas les systèmes complètement.  
Exigence SIA 380/2 Tableaux 5-9: chaque type de générateur (chaudière, PAC, etc.) a des seuils EER/SEER/SCOP distincts.

| Donnée | Format | Source IESVE | Raison | Priorité |
|--------|--------|--------------|--------|----------|
| Type générateur chaleur | enum (chaudière gaz/fioul, PAC air-eau, PAC géothermale, réseau chaleur, solaire, biomasse) | Apache Heater config | SIA 380/2: seuils SCOP différents par type | **HAUTE** |
| SCOP (Seasonal COP) | ratio | Fiche équipement / EN 14825 | SIA 380/2 tableaux 7-8 | **HAUTE** |
| COP nominal | ratio | Fiche équipement | Contrôle cohérence SCOP |
| Puissance nominale | kW | Apache spec. | Déterminer banda SIA 380/2 pour seuil SCOP | **HAUTE** |
| Température eau entrée | °C | Apache config / capteurs | PAC: régime (air-eau, géothermale) | **MOYENNE** |
| Température eau sortie | °C | Apache config / courbes | PAC: ΔT pour calcul SCOP |
| Source chaleur (si PAC) | enum (air extérieur, géothermal, eau) | Apache config | SIA 380/2: seuils SCOP sont source-spécifique | **HAUTE** |
| Puissance auxiliaire | W | Apache config | Pertes réseau, pompe, contrôle | **MOYENNE** |
| Distribution chaleur type | enum (radiateur, plancher chauffant, air chaud) | Apache distribution | Impact rendement émission / SIA 380/2 | **MOYENNE** |
| Rendement émission | ratio (%) | Fiche courbes SIA 380/2 | SIA 380/2 tableau 5: rendement émission |
| Rendement distribution | ratio (%) | Calc. pertes tuyauterie | SIA 380/2 tableau 5 |
| Rendement génération | ratio (%) | Calc. ou mesure | SIA 380/2 tableau 5 |
| Rendement stockage | ratio (%) | Si accumulateur présent | SIA 380/2 tableau 5 |
| Intégration énergie renouvelable | enum (solair thermique, biomasse, PAC géothermale) | Apache config | SIA 380/2: règles spécifiques par type |
| Fiabilité données SCOP | bool | Dossier technique | Si SCOP absent → devoir utiliser seuil min. SIA |

**Action code:**
- Créer classe `HeatingSystem` avec tous les champs
- Implémenter extraction Apache: lire type générateur, SCOP, puissance, source
- Créer lookup table SIA 380/2 Tableaux 7-8: (type générateur, source, puissance banda) → SCOP limite / cible
- Implémenter règles:
  - Type = PAC air-eau + puissance 12-50 kW → SCOP limite = 3.10 (SIA 380/2 tableau 7)
  - Type = PAC géothermale + puissance 12-50 kW → SCOP limite = 4.00 (SIA 380/2 tableau 8)
  - Vérifier SCOP disponible vs seuil; si sous seuil → FAIL
  - Si SCOP non fourni → EVIDENCE_MISSING
- Générer alerte traçabilité: "Système chauffage [type]: SCOP [valeur] vs SIA seuil [seuil] (SIA 380/2 tableau Y)"

### 1.8 Données systèmes refroidissement - Manquantes

Exigence SIA 380/2 Tableaux 5-6: chaque type de groupe froid (air-air, air-eau) a des seuils EER/SEER distincts.

| Donnée | Format | Source IESVE | Raison | Priorité |
|--------|--------|--------------|--------|----------|
| Type groupe froid | enum (air-air, air-eau, eau-eau) | Apache Cooler config | SIA 380/2: seuils EER/SEER différents | **HAUTE** |
| EER (Efficiency Ratio cooling) | ratio | Fiche équipement / EN 14825 | SIA 380/2 tableau 6 | **HAUTE** |
| SEER (Seasonal EER) | ratio | Fiche équipement | SIA 380/2 tableau 6 | **HAUTE** |
| COP nominal refroidissement | ratio | Fiche équipement | Contrôle cohérence EER/SEER |
| Puissance nominale refroidissement | kW | Apache spec. | Déterminer banda SIA 380/2 pour seuil EER | **HAUTE** |
| Température eau évaporateur | °C | Apache config | Régime froid |
| Température eau condenseur | °C | Apache config | Régime chaud; impacte SEER |
| Rejet de chaleur (type) | enum (air ambiant, eau nappe, tour aéroréfrigérante) | Apache config | Impact température condenseur / SEER | **MOYENNE** |
| Free cooling possible | bool | Apache config | Réduction consommation; SIA 4010 section 3.3.2 | **MOYENNE** |
| Type compresseur | enum (scroll, vis, piston) | Fiche équipement | Impact rendement |
| Puissance auxiliaire (ventilateur) | W | Apache config | Pertes condenseur, pompe |
| Rendement émission | ratio (%) | Fiche courbes | SIA 380/2 tableau 6: rendement émission |
| Rendement distribution | ratio (%) | Calc. pertes tuyauterie | SIA 380/2 tableau 6 |
| Rendement stockage froid | ratio (%) | Si accumulateur froid présent | SIA 380/2 tableau 6 |

**Action code:**
- Créer classe `CoolingSystem` avec tous les champs
- Implémenter extraction Apache: lire type groupe, EER, SEER, puissance, rejet de chaleur
- Créer lookup table SIA 380/2 Tableau 6: (type groupe, puissance banda) → EER limite / SEER limite
- Implémenter règles:
  - Type = air-air, puissance 12-50 kW → EER limite 3.00, SEER limite 3.90 (SIA 380/2 tableau 6a)
  - Type = eau-eau, puissance 50-150 kW → EER limite 4.25, SEER limite 4.80 (SIA 380/2 tableau 6b)
  - Vérifier EER et SEER vs seuils; si sous seuil → FAIL
  - Si EER/SEER non fourni → EVIDENCE_MISSING
- Générer alerte traçabilité: "Groupe froid [type]: EER/SEER [valeurs] vs SIA seuils (SIA 380/2 tableau Y)"

### 1.9 Données eau chaude sanitaire (ECS) - Manquantes

Exigence SIA 380/2: pas de seuil direct ECS; renvoie à SIA 385/2 et SIA 4010.

| Donnée | Format | Source IESVE | Raison SIA |
|--------|--------|--------------|-----------|
| Source ECS (générateur) | enum (chaudière, PAC, solaire, réseau, électrique) | Apache Heater ou config | SIA 385/2 méthode par source |
| Volume accumulation | litre | Apache tank config | Dimensionnement; SIA 385/2 |
| Température eau chaude | °C | Apache set point | Standard 60°C SIA 385/2 |
| Rendement solaire thermique (si présent) | ratio (%) | Fiche capteur / test | SIA 380/2: facteur rendement intégré |
| Apport solaire annuel | kWh | Simulation ou calcul | SIA 385/2 énergétique; preuve partiel |
| Perte thermique accumulation | W/K | Fiche tank / calc. (U surface) | SIA 380/2 Tableau 2: limite pertes |
| Puissance générateur ECS | kW | Apache config | Dimensionnement appoint |
| Efficacité générateur ECS | ratio (%) | Fiche équipement | SIA 385/2 rendement |

**Action code:**
- Créer classe `DHWSystem` avec tous les champs
- Implémenter extraction VE: lire générateur, volume, températures
- Créer règles SIA385/2 basiques (non exhaustive; renvoie à norme externe)
- Générer Evidence Required: "ECS: vérifier dimensionnement vs SIA 385/2 norme complète"

### 1.10 Données photovoltaïque (PV) - Manquantes

Exigence SIA 380/2 Tableau 2: puissance PV >= 10 W/m² SRE (Surface de Référence Énergétique).

| Donnée | Format | Source IESVE | Raison |
|--------|--------|--------------|--------|
| Présence PV | bool | Apache PV config | SIA 380/2 considère PV |
| Puissance nominale PV | kWc | Apache PV spec. | Puissance crête |
| Rendement module PV | ratio (%) | Fiche module STC | SIA 380/2: η = 0.17 standard |
| Rendement onduleur PV | ratio (%) | Fiche onduleur | Pertes conversion DC→AC |
| Surface SRE du bâtiment | m² | Calcul ou données bâtiment | Dénominateur pour seuil 10 W/m² |
| Surface PV installée | m² | Plan ou extraction VE | Numérateur |
| Densité puissance PV réelle | W/m² SRE | Calc. = Nominal / SRE | SIA 380/2: comparer vs 10 W/m² |
| Orientation panneaux | deg | Plan/VE extraction | Impact rendement optimal |
| Pente panneaux | deg | Plan/VE extraction | Impact rendement optimal |
| Ombrage PV | facteur (%) | Simulation ou mesure | Réduction rendement |
| Intégration au bâtiment | enum (toiture/façade/sol) | VE model | Type intégration BIPV |
| Production annuelle PV | kWh | Simulation PVsyst ou equiv. | SIA 380/2 évaluation annuelle |

**Action code:**
- Créer classe `PhotovoltaicSystem` avec tous les champs
- Implémenter extraction VE: lire puissance, surface, orientation
- Créer règle SIA380/2: calculer densité = Nominal / SRE; comparer avec 10 W/m²
- Générer alerte: "PV: densité [X W/m² SRE] vs SIA seuil 10 W/m² → [PASS/FAIL]"

---

## PART 2: RÈGLES SIA 380/2 À IMPLÉMENTER (Manquantes)

### 2.1 Enveloppe thermique - Règles manquantes

#### Règle 2.1.1: U-values constructions - Classification exacte des surfaces

**Actuellement:** Le code applique un fallback simple pour wall/roof/floor.  
**Manquant:** Classification précise selon SIA 380/2 tableau 3.

**Nouvelles règles à ajouter:**

```
Règle SIA3802_EXTERNAL_WALL_CLASSIFICATION
Description: Paroi extérieure → U limite 0.20 W/(m².K); 
  MAIS vérifier si c'est "contre terrain" (U limit 0.30) ou "contre local non-cond." (U limit 0.28).
Check: 
  - Si surface.adjacent_zone = "unconditioned" → utiliser 0.28 limite
  - Si surface.adjacent_zone = "exterior" ET surface.is_against_ground = True → utiliser 0.30 limite
  - Sinon → utiliser 0.20 limite
Seuil: seuil limite correspondant + cible correspondante
Evidence: Classification preuve, U-value source

Règle SIA3802_INTERMEDIATE_FLOOR_CLASSIFICATION
Description: Plancher intermédiaire peut être 0.64 (tous côtés climatisés) 
  ou 0.30 (un côté non-climatisé).
Check:
  - Si floor.above_zone.conditioned = True ET floor.below_zone.conditioned = True → U = 0.64
  - Sinon (au moins 1 côté non-cond.) → U = 0.30
Seuil: U limite appropriée

Règle SIA3802_ROOF_PITCH_CLASSIFICATION
Description: Toiture plate (pente < 5°) vs pente (pente >= 5°).
  SIA 380/2 table 3 distingue "Toiture plate". Au-delà, généralement traité comme toiture.
Check: 
  - Si surface.pitch < 5 → Toiture plate: U limit = 0.20
  - Sinon → Toiture pente: U limit = 0.20 (même) ou spécifique selon projet
Seuil: 0.20 W/(m².K)
```

#### Règle 2.1.2: Ponts thermiques linéaires et ponctuels

**Actuellement:** Tous les ponts = 0 (par défaut).  
**Manquant:** Extraction et contrôle ponts thermiques.

```
Règle SIA3802_LINEAR_THERMAL_BRIDGE
Description: Les ponts thermiques linéaires (psi, W/(m.K)) doivent être:
  1. Extraits depuis VE (Construction Database ou assemblages);
  2. Ou justifiés par SIA 4010 / norme EN ISO 14683.
Check:
  - Si surface.psi_linear > 0 → extraire valeur et source
  - Si surface.psi_linear = 0 → demander preuve (calcul EN 14683, design sans pont, etc.)
Seuil: À comparer avec SIA 380/2 hypothèses de référence (si projet fourni)
Evidence: Source psi (CDB, calcul, hypothèse)

Règle SIA3802_PUNCTUAL_THERMAL_BRIDGE
Description: Ponts ponctuels (chi, W/K) pour jonctions spéciales.
Check: Même logique que linéaire
Evidence: Source chi
```

#### Règle 2.1.3: Surface nette vs brute

**Actuellement:** Données non distinguées.  
**Manquant:** Calcul surface nette (hors cadrements, stores).

```
Règle SIA3802_NET_AREA_CALCULATION
Description: SIA 380/2 table 2 utilise surface nette de vitrage (hors cadre).
  Surface nette vitrage = Surface brute ouverture - Surface cadre.
Check:
  - Si surface.net_area disponible → utiliser
  - Sinon calculer: net_area = gross_area * (1 - frame_fraction)
  - Vérifier cohérence: |net_area - calculated| < 5%
Seuil: Vérification cohérence
Evidence: Source surface brute et frame fraction
```

### 2.2 Ouvertures (Vitrages et menuiserie) - Règles manquantes

#### Règle 2.2.1: Uw fenêtres - Traçabilité g-value

**Actuellement:** U-value fenêtres contrôlée; g-value basique.  
**Manquant:** Traçabilité g-value selon EN 410.

```
Règle SIA3802_GLAZING_G_VALUE_TRACEABILITY
Description: La valeur g (solaire) doit être g_perp selon EN 410, 
  pas g_hémisphérique ni approx.
Check:
  - Si opening.g_value_source = "EN410_perpendicular" → accepter
  - Si opening.g_value_source = "calculated_iso52022-3" → accepter
  - Si opening.g_value_source = "approx_or_unknown" → Evidence Required
Seuil: SIA 380/2 table 2: g_perp <= 0.50 (limite)
Evidence: Fiche vitrage EN 410, certificat, calcul ISO 52022-3

Règle SIA3802_GLAZING_LIGHT_TRANSMITTANCE
Description: Transmittance lumineuse tau >= 0.70 (SIA 380/2 table 2).
Check: opening.light_transmittance >= 0.70
Seuil: >= 0.70 W/(m².K)
Severity: MEDIUM si absent
Evidence: Fiche vitrage EN 410

Règle SIA3802_GLAZING_WITH_SHADING_G_TOTAL
Description: Si stores présents ET g-value store n'est pas fournie,
  calculer g-total selon SN EN ISO 52022-3.
Check:
  - Si shading_type = "fabric" ET shading.g_total absent → calculer via formule
  - Formula: g_total = g_glass * tau_shading + rho_shading * (1 - g_glass)
  - Utiliser g_total pour les calculs surchauffe
Seuil: Calculé
Evidence: Valeurs composantes (g_glass, tau_shading, rho_shading)
```

#### Règle 2.2.2: Frame fraction exacte

**Actuellement:** frame_fraction donnée; pas de vérification exacte.  
**Manquant:** Calcul frame_fraction réelle vs déclarée.

```
Règle SIA3802_FRAME_FRACTION_EXACT
Description: Frame fraction doit correspondre aux dimensions réelles.
  ff_exact = (2*frame_width*(H+W) - 4*frame_width²) / (H*W)
Check:
  - Calculer ff_exact depuis dimensions cadre et ouverture
  - Comparer avec opening.frame_fraction_declared
  - Si écart > 5% → WARNING
Seuil: ff <= 0.25 (SIA 380/2 table 2 limite)
Evidence: Plan fenêtre avec dimensions

Règle SIA3802_FRAME_U_VALUE_CHECK
Description: Vérifier cohérence U-value cadre vs Uw globale.
Check: 
  - Uw doit être calculée selon EN 10077-1
  - Si Uw fournie mais pas U_cadre → devoir justifier
Seuil: Uw <= 1.10 W/(m².K) (SIA 380/2 table 2)
Evidence: Calcul EN 10077-1 ou certification fenêtre
```

#### Règle 2.2.3: Protection solaire - Catégories SIA

**Actuellement:** Pas de contrôle catégorie protection.  
**Manquant:** Classification stores par catégorie SIA 380/2 tableau 10.

```
Règle SIA3802_SHADING_CATEGORY_CLASSIFICATION
Description: Les stores doivent être classés en catégorie 1-5 (SIA 380/2 tableau 10).
  Chaque catégorie a reflectance/transmittance définie.
Check:
  - Si shading_category = 1 ET shading_type = "fabric" → 
    doit avoir rho=0.50, tau=0.25
  - Si shading_category = 1 ET shading_type = "lamellae" → 
    doit avoir rho=0.70, tau=0.00
  - Etc. pour catégories 2-5
Seuil: Vérification cohérence données
Evidence: Fiche store, référence SIA 380/2 tableau 10

Règle SIA3802_SHADING_CONTROL_SIA3874
Description: La commande des stores doit respecter SIA 387/4 tableau 9.
Check:
  - Extraire type de commande (manuel/auto-irradiance/auto-temp/gaz)
  - Comparer seuil de commande avec SIA 387/4 recommandations
Seuil: Dépend type usage zone
Evidence: Paramètres Apache shading control, justification seuil
```

### 2.3 Ventilation et infiltration - Règles manquantes

#### Règle 2.3.1: Débit air neuf vs table 4 SIA

**Actuellement:** Pas de vérification table 4.  
**Manquant:** Vérifier type monozone/multizone et débit → appliquer commande exigée.

```
Règle SIA3802_VENTILATION_COMMAND_TABLE4
Description: SIA 380/2 table 4 définit type de commande en fonction de:
  - Type zonage: monozone vs multizone
  - Débit air neuf: <= 3, 3-6, > 6 m³/(h.m²)
Check:
  1. Déterminer débit_m3_h_m2 = AHU.nominal_flow / sum(room_areas)
  2. Si ventilation_type = "monozone":
       - Si debit <= 3: demande = horaire 1-2 vitesses
       - Si 3 < debit <= 6: demande = 2 vitesses 67/100 ou variable >= 25%
       - Si debit > 6: demande = variable >= 25% + occupation ou CO2
  3. Si ventilation_type = "multizone":
       - Même logique mais OBLIGATOIREMENT par zone
Check: Comparer AHU.control_type vs demande table 4
Severity: HIGH si commande < demande
Evidence: Plan AHU, seuil configuration, démonstration contrôle par zone

Règle SIA3802_VENTILATION_AIRTIGHTNESS_CLASS
Description: Étanchéité gaines/AHU doit être au minimum C/L2 (SIA 380/2 table 2).
Check:
  - Si ductwork.airtightness_class > C → FAIL (trop mauvais)
  - Si ahu.airtightness_class > L2 → FAIL
Seuil: C pour gaines, L2 pour AHU (limite); C et L1 (cible)
Evidence: Fiche équipement, test étanchéité

Règle SIA3802_VENTILATION_HEAT_RECOVERY
Description: Efficacité récupération thermique doit respecter SIA 380/2.
Check:
  - Si heat_recovery_present = True:
    - Efficacité température >= 0.73 (limite SIA 380/2)
    - Efficacité humidité >= 0.0 (limite; pas d'exigence)
    - Pour cible: >= 0.78 (température), >= 0.60 (humidité)
Seuil: Limite 0.73, Cible 0.78
Severity: HIGH si < 0.73
Evidence: Fiche récupérateur EN 13053, test de performance

Règle SIA3802_VENTILATION_PRESSURE_DROP
Description: Pertes de charge doivent rester dans limites SIA 380/2 table 2.
Check:
  - Supply_pressure_drop <= 700 Pa (limite), cible 550 Pa
  - Extract_pressure_drop <= 500 Pa (limite), cible 350 Pa
  - HeatRecovery_pressure_drop <= 300 Pa (limite), cible 400 Pa
Seuil: Voir limites/cibles
Evidence: Calcul réseau, fiche équipement
```

#### Règle 2.3.2: Infiltration d'air n50 → nominal

**Actuellement:** Pas d'extraction n50.  
**Manquant:** Convertir n50 → nominal et contrôler.

```
Règle SIA3802_INFILTRATION_N50_CONVERSION
Description: Infiltration nominale = n50 / 20 (standard SIA 2028).
Check:
  - Si infiltration_n50 disponible → calc. nominal = n50 / 20
  - Si infiltration_nominal directement fournie → comparer avec n50 / 20
  - Si écart > 10% → WARNING (méthode de conversion différente?)
Seuil: Nominal <= 0.15 m³/(h.m²) (SIA 380/2 table 2)
Evidence: Source n50 (test, hypothèse, standard)

Règle SIA3802_INFILTRATION_JUSTIFICATION
Description: Si infiltration n'est pas mesurée, elle doit être justifiée.
Check:
  - Si infiltration_source = "measured" → OK
  - Si infiltration_source = "assumption" → Evidence Required (justifier 0.15 ou autre)
Severity: MEDIUM si source inconnue
```

### 2.4 Éclairage - Règles manquantes

**Actuellement:** lighting_power_max = None.  
**Manquant:** Lier à SIA 387/4 et SIA 2024.

```
Règle SIA3802_LIGHTING_POWER_SIA3874
Description: Puissance éclairage doit respecter SIA 387/4 tableau 9 
  selon type de zone et commandes disponibles.
Check:
  - Lookup(zone_usage_SIA2024, room_type) → P_max SIA 387/4
  - Comparer lighting_power_density vs P_max
  - Appliquer réductions commande (daylight -20%, occupancy -15%)
Severity: MEDIUM si > seuil (pas FAIL; SIA renvoie à norme externe)
Evidence: Référence SIA 387/4 tableau 9, justification commandes

Règle SIA3802_LIGHTING_CONTROL_TYPE
Description: Type de commande éclairage doit être documenté.
Check:
  - Extraire control_type (manuel/horloge/daylight/occupancy/smart)
  - Comparer avec SIA 387/4 recommandations par zone
Severity: LOW si absent
Evidence: Plan de commande, programmation Apache
```

### 2.5 Équipements internes - Règles manquantes

**Actuellement:** equipment_power_max = None.  
**Manquant:** Lier à SIA 2024 profils.

```
Règle SIA3802_EQUIPMENT_GAINS_SIA2024
Description: Gains équipements doivent correspondre à SIA 2024 profil d'usage.
Check:
  - Lookup(zone_usage_SIA2024) → expected_gains W/m²
  - Comparer données VE vs SIA 2024
  - Si écart > 20% → Evidence Required (justifier)
Severity: LOW si pas de justification
Evidence: Référence SIA 2024, justification donnée VE

Règle SIA3802_OCCUPANT_DENSITY_SIA2024
Description: Densité d'occupation doit correspondre à SIA 2024.
Check:
  - Lookup(zone_usage_SIA2024) → expected_occupant_density pers/m²
  - Comparer données VE
Severity: MEDIUM si diverge fortement (> 50%)
Evidence: Plans, justification occupation réelle
```

### 2.6 Chauffage - Règles manquantes

**Actuellement:** Pas de vérification SCOP.  
**Manquant:** Extraction système, SCOP vs table SIA.

```
Règle SIA3802_HEATING_SCOP_LIMITS
Description: SCOP système chauffage doit respecter SIA 380/2 tableaux 7-8.
Check:
  1. Identifier type_generator (PAC air-eau, géothermale, chaudière, etc.)
  2. Identifier puissance nominale → banda SIA
  3. Lookup(generator_type, power_band) → SCOP_limit, SCOP_target
  4. Comparer avec system.SCOP fournie
Seuil: SCOP >= SCOP_limit
Severity: HIGH si SCOP < limite
Evidence: Fiche équipement, certification, test EN 14825

Règle SIA3802_HEAT_PUMP_SOURCE
Description: Source chaleur PAC détermine le seuil SCOP SIA.
Check:
  - Si heat_pump_source = "air": utiliser tableau 7 (PAC air-eau)
  - Si heat_pump_source = "ground": utiliser tableau 8 (PAC géothermale)
  - Sinon: demander clarification
Severity: HIGH (bloquer si source inconnue)
Evidence: Plans, documentation équipement

Règle SIA3802_HEATING_SYSTEM_EFFICIENCY_CHAIN
Description: Rendement total chauffage = émission × distribution × génération.
Check: 
  - Comparer données VE vs chaîne SIA 380/2 table 5
  - Si rendement global < 0.90 × 0.95 × (scop_nominal) → FAIL
Severity: MEDIUM (dépend chaîne)
Evidence: Calcul rendement total, sources chaque étape
```

### 2.7 Refroidissement - Règles manquantes

**Actuellement:** Pas de vérification EER/SEER.  
**Manquant:** Extraction système, EER/SEER vs table SIA.

```
Règle SIA3802_COOLING_EER_SEER_LIMITS
Description: EER et SEER système refroidissement doivent respecter SIA 380/2 tableau 6.
Check:
  1. Identifier type_cooler (air-air, air-eau, eau-eau, etc.)
  2. Identifier puissance nominale → banda SIA
  3. Lookup(cooler_type, power_band) → EER_limit, SEER_limit
  4. Comparer avec system.EER et system.SEER fournies
Seuil: EER >= EER_limit ET SEER >= SEER_limit
Severity: HIGH si < limites
Evidence: Fiche équipement, certification, test EN 14825

Règle SIA3802_COOLING_HEAT_REJECTION
Description: Rejet de chaleur condenseur doit être documenté.
Check:
  - Identifier rejet_type (air ambiant, nappe, tour aéroréfrigérante)
  - Si air ambiant: noter impact température, saisonnalité
  - Si nappe: documenter capacité, impacts hydrologiques
Severity: LOW (documentation)
Evidence: Plans refroidissement, données condenseur

Règle SIA3802_COOLING_FREE_COOLING
Description: Si free cooling possible, documenter mode et gain.
Check:
  - Si system.free_cooling_available = True:
    - Documenter seuil d'activation (température/enthalpie)
    - Estimer gain annuel (réduction EER)
Severity: LOW (indicateur)
Evidence: Schéma refroidissement, seuil commande
```

### 2.8 Photovoltaïque - Règles manquantes

**Actuellement:** Pas de vérification PV.  
**Manquant:** Calcul densité PV vs seuil SIA.

```
Règle SIA3802_PHOTOVOLTAIC_POWER_DENSITY
Description: Densité puissance PV >= 10 W/m² SRE (SIA 380/2 table 2).
Check:
  - Calculer SRE (Surface de Référence Énergétique) = surface habitable chauf
  - Calculer densité_pv = puissance_nominale_kWc / SRE_m2 × 1000
  - Comparer avec 10 W/m²
Seuil: >= 10 W/m² (minimum SIA)
Severity: MEDIUM si < 10 (recommandation, pas obligation)
Evidence: Plans PV, données SRE

Règle SIA3802_PHOTOVOLTAIC_EFFICIENCY
Description: Rendement module PV dépend type technologie.
Check:
  - Si pv_module_efficiency > 0.22 → vérifier cohérence (technologie haute ?)
  - SIA 380/2 suppose η = 0.17
Severity: LOW (information)
Evidence: Fiche module PV, datasheet
```

---

## PART 3: CONDITIONS SIA 4010:2023 À IMPLÉMENTER (Manquantes)

### 3.1 Données climatiques et dimensionnement dynamique

**Actuellement:** La puissance n'est pas extraite depuis Vista; les conditions SIA 4010 ne sont pas appliquées.  
**Manquant:** Extraction APS/Vista, vérification conditions dynamiques.

```
Règle SIA4010_CLIMATE_DRY_REFERENCE
Description: SIA 4010 section 3.1.1 exige climat DRY selon SIA 2028.
Check:
  - Vérifier météo_file lié à SIA 2028 Design Reference Year
  - Vérifier pas de temps = horaire
  - Vérifier station climatique valide (Zurich-Kloten, Genève, etc.)
  - Vérifier période = année complète (1 janvier - 31 décembre)
Severity: HIGH
Evidence: Métadonnées fichier météo, certification SIA 2028

Règle SIA4010_PRECONDITIONING_HEATING
Description: SIA 4010 section 3.1.2: chauffage dimensionnement 
  utilise 4 jours froids + 14 jours pré-conditionnement.
Check:
  - Extraire fichier APS chauffage Vista
  - Identifier jours de référence (exemple: 24-27 janvier Zurich)
  - Vérifier pré-cond. = 14 jours avant (ex: 10-23 janvier)
  - Vérifier pas de weekend si possible
Severity: HIGH si période manquante
Evidence: Dates fichier APS, calendrier bâtiment

Règle SIA4010_PRECONDITIONING_COOLING
Description: SIA 4010 section 3.1.3: refroidissement dimensionnement 
  utilise 3 jours chauds (juin, août, octobre) + 14j pré-cond. chacun.
Check:
  - Extraire fichier APS refroidissement Vista
  - Identifier jours de référence 3 (ex: 21 juin, 16 août, 16 octobre Zurich)
  - Vérifier pré-cond. = 14 jours avant chaque (7-20 juin, etc.)
  - Vérifier pas de weekend si possible
Severity: HIGH si période manquante
Evidence: Dates fichier APS, calendrier bâtiment

Règle SIA4010_CLIMATE_SCENARIO_2035_RCP85
Description: SIA 4010 recommande scénario RCP 8.5 / 2035 pour surchauffe.
Check:
  - Si application sensible à surchauffe (bureaux, commerces):
    - Vérifier metadata météo = CH2018 RCP 8.5 2035 ou justifier autre
  - Si métadonnée absent → Evidence Required (documenter choix)
Severity: MEDIUM (recommandation)
Evidence: Sélection scenario, justification si différent
```

### 3.2 Résultats dynamiques chauffage et refroidissement

**Actuellement:** Les puissances horaires chauffage/refroidissement ne sont pas extraites ni validées.  
**Manquant:** Extraction Vista APS, contrôle puissances.

```
Règle SIA4010_HEATING_POWER_EXTRACTION
Description: Extraire puissance chauffage horaire depuis fichier APS Vista.
Check:
  - Vérifier fichier APS refroidissement disponible dans répertoire Vista
  - Lire puissances horaires: Phi_H,t (W) pour chaque heure
  - Sommer sur 4 jours de référence: Q_H = Σ Phi_H,t × Δt
  - Comparer avec données projet
Severity: HIGH si absent
Evidence: Fichier APS Vista, structure données

Règle SIA4010_COOLING_POWER_EXTRACTION
Description: Extraire puissance refroidissement horaire depuis fichier APS Vista.
Check:
  - Vérifier fichier APS refroidissement disponible
  - Lire puissances horaires: Phi_C,t (W) pour chaque heure
  - Sommer sur 3×4 jours = 3 périodes de référence
  - Comparer avec données projet
Severity: HIGH si absent
Evidence: Fichier APS Vista, structure données

Règle SIA4010_ANNUAL_ENERGY_BALANCE
Description: Vérifier somme annuelle besoins chauffage/refroidissement.
Check:
  - Lire résultats annuels Vista: Q_H,annual, Q_C,annual
  - Vérifier cohérence avec somme des périodes de référence
  - Vérifier valeurs plausibles (par exemple, Q_H > 0, Q_C >= 0)
Severity: MEDIUM (validation cohérence)
Evidence: Fichiers Vista résultats
```

### 3.3 Conditions d'utilisation SIA 2024

**Actuellement:** Pas de vérification décalages SIA 4010 section 3.1.4.  
**Manquant:** Extraire usages zone, vérifier décalages consignes SIA 4010.

```
Règle SIA4010_USAGE_SETPOINT_OFFSET
Description: SIA 4010 section 3.1.4 définit décalages consignes selon usage SIA 2024.
Check:
  1. Identifier usage_sia2024 (ex: 2.05 = bureau paysager)
  2. Lookup(usage_sia2024) → offset_chauffage, offset_refroidissement
  3. Vérifier consignes chauffage/refroidissement appliquées incluent décalage
  
  Exemples SIA 4010:
  - 3.04 Guichets: +1K courbe basse (chauffage +1)
  - 5.01-5.03 Magasins: +1K courbe basse
  - 6.03/6.04 Cuisines: +1K basse, +2K haute
  - 9.01 Production grossier: +3K basse, +4K haute
  - Gymnases/fitness/vestiaires: pas de décalage; limites constantes

Severity: MEDIUM si offset absent
Evidence: Plans Apache occupation, consignes par zone

Règle SIA4010_COMFORT_CURVE_DEPENDENCY
Description: Certaines usages (gymnases, piscines) = limites constantes, 
  pas courbes dépendantes habillement.
Check:
  - Si usage in [gymnase, piscine, fitness, vestiaire, douche]:
    - Vérifier limites temperature = constantes (pas de courbe saisonnière)
  - Else:
    - Vérifier courbes habillement SIA 2024 appliquées
Severity: MEDIUM si non conforme
Evidence: Profil Apache utilisation
```

### 3.4 Stores et facteur solaire total

**Actuellement:** Pas de lien SIA 4010 stores-tissu.  
**Manquant:** Vérifier règles SIA 4010 section 3.1.5.

```
Règle SIA4010_FABRIC_SHADING_G_TOTAL_METHOD
Description: SIA 4010 section 3.1.5 assimile stores tissu à coefficients globaux 
  OR calcule g_total via SN EN ISO 52022-3.
Check:
  - Si shading_type = "fabric" ET shading_category known:
    - Utiliser table SIA 380/2 tableau 10: rho et tau du store
    - Calculer g_total = g_vitrage × tau_store + rho_store × (1 - g_vitrage)
  - Ou si g_total fourni directement → accepter
Severity: MEDIUM si g_total incohérent
Evidence: Fiche store, calcul ISO 52022-3

Règle SIA4010_SHADING_CONTROL_COMMAND
Description: Commande stores doit être documentée pour calculer apports réels.
Check:
  - Identifier seuil commande stores (W/m² irradiance ou température)
  - Extraire profil ouverture/fermeture stores depuis Apache
  - Comparer avec SIA 387/4 recommandations
Severity: LOW (documentation)
Evidence: Schéma commande, paramètres Apache
```

### 3.5 Validation systèmes techniques

**Actuellement:** Pas de liens SIA 4010 vers systèmes ventilation/chauffage/refroidissement.  
**Manquant:** Vérifier section 3.2 et entrées techniques tables 34-61 SIA 4010.

```
Règle SIA4010_VENTILATION_SYSTEM_VALIDATION
Description: SIA 4010 section 3.3.1 définit données entrée ventilation 
  issues normes EN et SIA.
Check:
  - Vérifier debit air neuf = source SIA 2024 ou justifié
  - Vérifier fuites gaines/AHU = catégorie EN 14182 ou justifié
  - Vérifier récupération thermique = rendement EN 13053 ou mesure
  - Vérifier humidification (si présente) = documentée

Severity: MEDIUM si source manquante
Evidence: Plan ventilation, fiches équipement, calculs

Règle SIA4010_COOLING_SYSTEM_VALIDATION
Description: SIA 4010 section 3.3.2 définit données entrée refroidissement 
  issues normes EN et SIA.
Check:
  - Vérifier EER/SEER = EN 14825 ou mesure
  - Vérifier free cooling = stratégie documentée
  - Vérifier rejet chaleur = dimensionné
  
Severity: MEDIUM si source manquante
Evidence: Fiches équipement, plans refroidissement

Règle SIA4010_HEATING_SYSTEM_VALIDATION
Description: SIA 4010 section 3.3.3 définit données entrée chauffage 
  issues normes EN et SIA.
Check:
  - Vérifier SCOP/COP = EN 14825 ou mesure
  - Vérifier température source (si PAC) = documentée
  - Vérifier courbe chauffage = dimensionnée SIA 4010 chauffage
  
Severity: MEDIUM si source manquante
Evidence: Fiches équipement, courbes chauffage
```

---

## PART 4: AUDIT ET PREUVES DOCUMENTAIRES

### 4.1 Audit trail (Traçabilité)

Chaque seuil, valeur, calcul doit avoir une trace PDF SIA ou source externe vérifiable.

```
Classe AuditEntry:
  - Propriété contrôlée (ex: "window_u_value")
  - Seuil SIA (ex: 1.10 W/(m².K))
  - Référence PDF (ex: "SIA 380/2:2022 tableau 2, page 32")
  - Valeur extraite VE (ex: 1.05)
  - Résultat (PASS/FAIL/WARNING)
  - Preuve (fichier/document/calcul)
  - Date audit

Implémentation:
  - Chaque règle doit inclure champ "source_reference" (table SIA, page)
  - Rapport final = liste audit entries avec preuves
  - Export: rapport PDF avec lien audit trace VE → SIA
```

### 4.2 Preuves manquantes - Alertes Evidence Required

```
Classe EvidenceRequired:
  - Propriété manquante (ex: "glazing_g_value_source")
  - Exigence SIA (ex: "EN 410 g-perpendicular")
  - Document attendu (ex: "Fiche vitrage, certification, calcul ISO 52022-3")
  - Action (ex: "Fournir fiche vitrage avec g_perp ou calcul ISO 52022-3")
  - Priorité (HIGH/MEDIUM/LOW)

Implémentation:
  - Pour chaque Evidence Required: générer ligne rapport + action plan
  - Regrouper par catégorie pour synthèse manager
```

---

## PART 5: RÉSUMÉ DES NOUVELLES RÈGLES ET CHAMPS À IMPLÉMENTER

### 5.1 Nouvelles métriques d'extraction (Data fields)

**Total estimé: ~60-70 nouveaux champs VE**

| Domaine | Nombre champs | Exemples |
|---------|---:|---|
| Classification surfaces opaques | 8 | surface_type_precise, wall_against_ground_depth_m, roof_pitch_degrees |
| Paramètres thermiques surfaces | 5 | linear_thermal_bridge_psi, punctual_thermal_bridge_chi, net_area |
| Vitrages détaillés | 12 | g_perp_en410, glazing_air_gap_mm, light_transmittance_tau_en410 |
| Menuiserie détaillée | 8 | frame_width_mm, frame_u_value, spacer_type_thermal |
| Stores/protection solaire | 8 | shading_category_sia, shading_reflectance, g_total_with_shading |
| Ventilation système | 18 | duct_airtightness_class, heat_recovery_temp_efficiency, ahu_u_value |
| Infiltration | 3 | infiltration_n50, infiltration_source |
| Éclairage | 6 | lighting_control_type, daylight_reduction_ratio |
| Équipements internes | 5 | equipment_power_density, occupant_density, sia2024_usage_code |
| Chauffage système | 10 | heating_type, SCOP, heat_pump_source, heating_efficiency_chain |
| Refroidissement système | 8 | cooler_type, EER, SEER, cooling_heat_rejection_type |
| Eau chaude sanitaire | 6 | dhw_generator_type, tank_volume_L, temperature_setpoint_degC |
| Photovoltaïque | 8 | pv_nominal_power_kWc, pv_module_efficiency, pv_density_w_m2_sre |
| Données projet | 12 | iesve_version, calculation_engine, weather_file, climate_scenario, aes_heating_file |

### 5.2 Nouvelles règles SIA 380/2 à implémenter

**Total estimé: ~25 nouvelles règles**

| Domaine | Nombre | Exemples |
|---------|---:|---|
| Classification et construction | 6 | EXTERNAL_WALL_CLASSIFICATION, INTERMEDIATE_FLOOR_CLASSIFICATION, NET_AREA_CALCULATION |
| Vitrages | 5 | GLAZING_G_VALUE_TRACEABILITY, FRAME_FRACTION_EXACT, SHADING_CATEGORY_CLASSIFICATION |
| Ventilation | 6 | VENTILATION_COMMAND_TABLE4, AIRTIGHTNESS_CLASS, HEAT_RECOVERY, INFILTRATION_N50_CONVERSION |
| Éclairage | 2 | LIGHTING_POWER_SIA3874, LIGHTING_CONTROL_TYPE |
| Équipements | 2 | EQUIPMENT_GAINS_SIA2024, OCCUPANT_DENSITY_SIA2024 |
| Chauffage | 3 | HEATING_SCOP_LIMITS, HEAT_PUMP_SOURCE, HEATING_EFFICIENCY_CHAIN |
| Refroidissement | 3 | COOLING_EER_SEER_LIMITS, COOLING_HEAT_REJECTION, COOLING_FREE_COOLING |
| PV | 1 | PHOTOVOLTAIC_POWER_DENSITY |

### 5.3 Nouvelles règles SIA 4010 à implémenter

**Total estimé: ~12-15 nouvelles règles**

| Domaine | Nombre | Exemples |
|---------|---:|---|
| Climat et dynamique | 4 | CLIMATE_DRY_REFERENCE, PRECONDITIONING_HEATING, COOLING_REFERENCE_DAYS |
| Résultats puissances | 2 | HEATING_POWER_EXTRACTION, COOLING_POWER_EXTRACTION |
| Conditions d'utilisation | 2 | USAGE_SETPOINT_OFFSET, COMFORT_CURVE_DEPENDENCY |
| Stores/protection | 2 | FABRIC_SHADING_G_TOTAL_METHOD, SHADING_CONTROL_COMMAND |
| Validation systèmes | 3 | VENTILATION_SYSTEM_VALIDATION, COOLING_SYSTEM_VALIDATION, HEATING_SYSTEM_VALIDATION |

---

## PART 6: FICHIERS À MODIFIER ET CRÉER

### 6.1 Modifications code existant

```
swiss_sia/
├── config.py
│   ├── Ajouter SIA4010_SYSTEM_VALIDATION_TABLES (ventilation, chauffage, froid)
│   ├── Enrichir SIA3802_LIMIT_VALUES (50-70 nouveaux champs)
│   └── Ajouter constantes extraction Vista APS
│
├── model_analyzer.py
│   ├── Surface class: ajouter ~10 nouveaux champs (type_precise, psi_linear, chi_punctual, etc.)
│   ├── Opening class: ajouter ~12 nouveaux champs (g_perp_en410, frame_width_mm, etc.)
│   ├── RoomData class: ajouter ~8 nouveaux champs (occupant_density, equipment_power, etc.)
│   ├── Créer classe VentilationSystem (~18 champs)
│   ├── Créer classe HeatingSystem (~10 champs)
│   ├── Créer classe CoolingSystem (~8 champs)
│   ├── Créer classe DHWSystem (~6 champs)
│   ├── Créer classe PhotovoltaicSystem (~8 champs)
│   └── Créer classe LightingData (~6 champs)
│
├── data_extractor.py
│   ├── Ajouter 60-70 extractions VE nouvelles
│   ├── Ajouter extraction fichier APS Vista (chauffage, refroidissement)
│   ├── Ajouter extraction métadonnées projet (version, moteur, climat, scénario)
│   └── Créer parseur Vista pour puissances horaires
│
├── sia380_checker.py
│   ├── Ajouter 25 nouvelles règles SIA 380/2
│   ├── Enrichir `_setup_rules()` avec toutes les nouvelles règles
│   └── Ajouter méthodes validation par domaine (enveloppe, ventilation, etc.)
│
├── sia4010_checker.py
│   ├── Ajouter 12-15 nouvelles règles SIA 4010
│   ├── Ajouter extraction puissances chauffage/refroidissement Vista
│   ├── Ajouter vérification conditions dynamiques SIA 4010
│   └── Enrichir `check_all()` avec nouvelles vérifications
│
├── rule_engine.py
│   └── (Pas de modification majeure; étendre si nécessaire)
│
├── health_score.py
│   ├── Recalculer scoring: 40% → 70-80% couverture SIA
│   └── Adapter poids règles (SIA 4010 = poids nouveau)
│
└── excel_report.py
    ├── Ajouter colonne "SIA Source Reference" (table, page)
    ├── Ajouter sheet "Audit Trail" (traçabilité PDF SIA)
    ├── Ajouter sheet "Evidence Required" (actions à faire)
    ├── Enrichir colonnes détails (g_perp, SCOP, EER, etc.)
    └── Ajouter validation sommaire par domaine SIA
```

### 6.2 Fichiers à créer

```
swiss_sia/
├── sia_extraction.py (Nouveau)
│   ├── Classe SIADataExtractor
│   ├── Méthodes extraction IESVE détaillée (~60-70 champs)
│   ├── Méthodes parsing Vista APS
│   └── Méthodes validation données
│
├── sia_audit_trail.py (Nouveau)
│   ├── Classe AuditEntry (propriété, seuil SIA, ref, preuve)
│   ├── Classe EvidenceRequired (action à faire)
│   ├── Générateur audit trail complet
│   └── Sérialisation audit → rapport
│
├── sia_reference_tables.py (Nouveau)
│   ├── Table lookup SIA 380/2 (constructions par type + conditions)
│   ├── Table lookup SIA 387/4 (éclairage par usage SIA 2024)
│   ├── Table lookup SIA 2024 (profils usage, gains, débits)
│   ├── Table lookup SIA 4010 (décalages consignes par usage)
│   └── Table lookup SIA 2028 (stations climatiques, périodes ref.)
│
└── tests/
    └── test_sia_completeness.py (Nouveau)
        ├── Tests unitaires: chaque nouvelle règle
        ├── Tests intégration: chaîne enveloppe → résultats
        ├── Tests audit trail: traçabilité PDF complète
        └── Tests exemple modèles (pass/fail scenarios)
```

---

## PART 7: PLAN D'IMPLÉMENTATION PAR ÉTAPES

### Phase 1: Extraction données (Semaine 1-2)

1. Enrichir `model_analyzer.py` classes Surface, Opening, RoomData (~50 champs)
2. Enrichir `data_extractor.py` extraction VE (~60-70 champs)
3. Créer `sia_extraction.py` extractor centralisé
4. Créer `sia_reference_tables.py` lookups SIA 2024/387/4/2028
5. Tester extraction sur modèle exemple

### Phase 2: Règles SIA 380/2 (Semaine 2-3)

1. Ajouter 25 nouvelles règles dans `sia380_checker.py`
2. Créer classe `AuditEntry` et `EvidenceRequired`
3. Implémenter traçabilité PDF (source_reference pour chaque règle)
4. Tester chaque règle avec données exemple

### Phase 3: Conditions SIA 4010 (Semaine 3-4)

1. Implémenter extraction Vista APS (puissances chauffage/refroidissement)
2. Ajouter 12-15 nouvelles règles SIA 4010
3. Vérifier conditions dynamiques (preconditioning, jours ref., climat DRY)
4. Tester sur modèle exemple

### Phase 4: Reporting et audit trail (Semaine 4)

1. Enrichir `excel_report.py` (colonnes SIA refs, audit trail, evidence required)
2. Générer rapport final: audit complet + preuves + actions
3. Créer tests complets (`test_sia_completeness.py`)

### Phase 5: Validation finale (Semaine 5)

1. Audit manuel rapport vs PDF SIA 380/2 et 4010
2. Vérifier chaque alerte Evidence Required est justifiée
3. Optimiser performance extraction (60-70 champs = temps acceptable)
4. Documenter pour utilisateur

---

## PART 8: RÉSUMÉ FINAL

### ✅ Statut AVANT implémentation
- Script actuel: ~40% SIA 380/2, ~15% SIA 4010
- **Conclusion:** Modèles déclarés conformes NE SONT PAS réellement conformes
- Raison: Donnees manquantes, règles incomplètes, pas de traçabilité

### 📋 Statut APRÈS implémentation (cible)

| Aspect | Avant | Après | Gain |
|--------|-------|-------|------|
| Champs extraction | ~20 | ~80 | +4x |
| Règles SIA 380/2 | ~15 | ~40 | +2.7x |
| Règles SIA 4010 | ~5 | ~20 | +4x |
| Audit trail | Non | Oui | 100% |
| Evidence traceability | Non | Oui | 100% |
| Couverture SIA 380/2 | 40% | 75-80% | +1.9x |
| Couverture SIA 4010 | 15% | 60-70% | +4x |

### ✅ Résultat final attendu

**Rapport généré par Claude Code:**
- ✅ **Page 1:** Résumé conformité (nombre PASS/FAIL/WARNING/EVIDENCE REQUIRED)
- ✅ **Pages 2-X:** Détail règles par domaine SIA (enveloppe, ventilation, etc.)
- ✅ **Audit trail:** Chaque seuil = référence PDF SIA (tableau, page)
- ✅ **Evidence required:** Liste actions à faire pour compléter conformité
- ✅ **Action plan:** Priorisation (HAUTE/MOYENNE/BASSE) des actions manquantes

**Conclusion defendable:**
- Si TOUTES les rules = PASS + Evidence Required = fermée → modèle = SIA 380-2 conforme (à traçabilité complète)
- Si au moins 1 FAIL (ex: SCOP insuffisante) → modèle = NON conforme cette partie
- SIA 4010 = jamais "PASS" sans dossier officiel; reste "READY_FOR_OFFICIAL_REVIEW"

---

## END OF DOCUMENT

**Destination:** Donner intégralement ce document à Claude Code pour implémentation complète.  
**Temps estimé:** 8-10 jours développement + tests + documentation.  
**Résultat:** Script production-ready conformité SIA 380-2 et SIA 4010.

