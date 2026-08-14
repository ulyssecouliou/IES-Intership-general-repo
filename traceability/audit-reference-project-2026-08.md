# Audit indépendant — Projet de référence SIA 380/2 (`swiss_sia/reference_project.py`)

> Rôle : `qa-auditor` (indépendant des agents d'implémentation).
> Date : 2026-08-14.
> Objet : vérifier que chaque valeur figée des **8 familles** du projet de référence
> SIA 380/2:2022 est FIDÈLE à la source SIA, que la logique de substitution est correcte,
> et produire une matrice de traçabilité signée.
> Aucune ligne de code de production n'a été modifiée. Rien n'a été commité.

---

## 0. Niveau de preuve — j'ai OUVERT le PDF

Contrairement à `traceability/sia380-2-generation-reference.spec.md` §0 (où l'agent
`norm-analyst` **n'a pas pu ouvrir** `refs/SIA-380-2-2022.pdf`), **j'ai extrait le PDF
primaire avec PyMuPDF (`fitz` 1.28.0)** et lu les cellules une par une.

| Élément | Détail |
|---|---|
| PDF ouvert | `refs/SIA-380-2-2022.pdf` (64 pages), watermark « iNorm License, IES, Johan Haeberle, 372332 » (copie licenciée légitime) |
| Tableau 2 | pages PDF **32-35** (idx 31-34) — extraites intégralement |
| Tableau 3 | pages PDF **36-37** (idx 35-36) — extraites intégralement |
| Tableaux 5-7 | page PDF **38** (idx 37) — extraites intégralement |
| Tableaux 8-9 | page PDF **39** (idx 38) — extraites intégralement |
| JSON SIA 2024 | `refs/reference-data/sia-2024-2021.usage-data.json` (45 usages) — lu via Python |
| Tests | `tests/test_reference_project.py` — **40/40 PASS** ; + tests adverses de bornes ci-dessous |

**Marqueurs de verdict** :
- **PASS** = valeur du code identique à la source primaire SIA 380/2 (PDF), reproductible ici.
- **WARNING** = code correct, mais source primaire **absente de `/refs`** (donc non signable) OU observation mineure.
- **FAIL** = valeur fausse (aucune trouvée).

---

## 1. Matrice de traçabilité — les 8 familles émises par `reference_project.py`

Locator normatif systématique : `# SIA 380/2:2022`. Séparateur décimal source « , » normalisé au point.

### Famille 1 — `opaque_envelope_constructions` (Tableau 3, valeur limite)

| Paramètre code | Valeur code | Valeur source (VL) | Locator PDF | Verdict |
|---|---|---|---|---|
| `external_wall_u` | 0.20 | 0,2 (Mur extérieur, ligne 1) | Tab 3, p36 | **PASS** |
| `flat_roof_u` | 0.20 | 0,2 (Toiture plate, ligne 1) | Tab 3, p37 | **PASS** |
| `ground_floor_u` | 0.30 | 0,3 (Sol contre terrain, ligne 1) | Tab 3, p36 | **PASS** |

Unité émise `W/(m2K)` conforme à l'en-tête « W/(m²·K), valeur limite ». `reference_project` n'utilise que
la colonne **limite** (les autres constructions du Tableau 3 sont recoupées en §3).

### Famille 2 — `window_u_value_and_frame_fraction` (Tableau 2, valeur limite)

| Paramètre code | Valeur code | Valeur source (VL) | Symbole | Locator PDF | Verdict |
|---|---|---|---|---|---|
| `window_u` | 1.10 | 1,1 | Uw | Tab 2, p32 | **PASS** |
| `window_frame_fraction` | 0.25 | 0,25 | ff | Tab 2, p32 | **PASS** |

### Famille 3 — `glazing_solar_and_visible_properties` (Tableau 2, valeur limite)

| Paramètre code | Valeur code | Valeur source (VL) | Symbole | Locator PDF | Verdict |
|---|---|---|---|---|---|
| `glazing_g_value` (g⊥) | 0.50 | 0,50 | g⊥ | Tab 2, p32 | **PASS** |
| `glazing_light_transmittance` (τ) | 0.70 | 0,70 | τ | Tab 2, p32 | **PASS** |

### Famille 4 — `infiltration` (Tableau 2)

| Paramètre code | Valeur code | Valeur source (VL) | Unité | Locator PDF | Verdict |
|---|---|---|---|---|---|
| `infiltration_m3_h_m2` | 0.15 | 0,15 (colonnes projet/VL/VC toutes = 0,15) | m3/(h·m2) | Tab 2, p32 | **PASS** |

### Famille 5 — `cooling_generation_and_auxiliaries` (Tableau 5, refroidisseur à air, EER pleine charge, limite)

| Bande de puissance | Valeur code (EER) | Valeur source (EER limite pleine charge) | Locator PDF | Verdict |
|---|---|---|---|---|
| `P ≤ 12 kW` | 2.90 | 2,90 | Tab 5, p38 | **PASS** |
| `12 < P ≤ 50 kW` | 3.00 | 3,00 | Tab 5, p38 | **PASS** |
| `50 < P ≤ 150 kW` | 3.10 | 3,10 | Tab 5, p38 | **PASS** |
| **Seuil de bascule** `≥ 150 kW` | bloqueur EER+ (Tab 7) | Tab 2 : « < 150 kW → air » ; « à partir de 150 kW → eau, post-refroidisseur à sec » | Tab 2, p34 ; §7.2.5.4-5 | **PASS** |

Grandeur = **EER pleine charge directement nommé** (jamais SEER) → contourne l'équivalence
non prouvée SEER↔SN EN 14825. Cibles 3,10/3,15/3,20 (Tab 5) recoupées en §3.

### Famille 6 — `heating_generation` (Tableau 8, PAC air-eau, SCOP, limite)

| Bande de puissance | Valeur code (SCOP) | Valeur source (SCOP limite) | Locator PDF | Verdict |
|---|---|---|---|---|
| `P ≤ 12 kW` | 3.00 | 3,0 | Tab 8, p39 | **PASS** |
| `12 < P ≤ 50 kW` | 3.10 | 3,10 | Tab 8, p39 | **PASS** |
| `50 < P ≤ 150 kW` | 3.20 | 3,20 | Tab 8, p39 | **PASS** |
| **Cible (`target`)** | `None` | Tableau 8 n'a **AUCUNE** ligne « valeurs cibles » | Tab 8, p39 | **PASS** |
| `P > 150 kW` | bloqueur | Tableau 8 s'arrête à ≤ 150 kW | Tab 8, p39 | **PASS** |

Type = **PAC air-eau** conforme à Tab 2 (VL = « PAC air-eau »). `target=None` est **exact** :
j'ai vérifié sur le PDF que le Tableau 8 ne comporte pas de colonne cible (la cible chaud
est portée par le Tableau 9 saumure-eau, hors périmètre `reference_project`).

### Famille 7 — `emission_system_and_unlimited_capacity` (Tableau 2, directives)

| Paramètre code | Valeur/directive code | Source | Locator PDF | Verdict |
|---|---|---|---|---|
| `emission_system_type` | `REFERENCE_DIRECTIVE`, radiant_fraction 0.0, « Convective emission » | « Type de système d'émission : par convection / par convection » | Tab 2, p33 | **PASS** |
| `max_heating_cooling_capacity` | `REFERENCE_DIRECTIVE`, « Unlimited heating and cooling capacity » (reference_value=None) | « Puissance maximale de chauffage et de refroidissement : illimitée / illimitée » | Tab 2, p33 | **PASS** |

Sémantique correcte : directive prescriptive du run de référence, **project_value=None**, jamais un bloqueur (voir §4).

### Famille 8 — `sia2024_internal_gains_profiles_and_setpoints` (§7.2.5.3 + SIA 2024, usage 1.01)

Source figée lue : `refs/reference-data/sia-2024-2021.usage-data.json`, usage `1.01` (« Wohnen MFH »).

| Paramètre code | Colonne JSON | Symbole JSON | Valeur code | Unité (octets UTF-8 vérifiés) | Verdict |
|---|---|---|---|---|---|
| `theta_i_mean` | **col30** | `theta_i_mean` (« Mittlere Raumtemperatur (Exploitation/Energie) ») | 25 | °C (`c2 b0 43`, propre) | **WARNING** |
| `phi_i` | col34 | `phi_i` (« Relative Raumluftfeuchte ») | 60 | % | **WARNING** |
| `A_p` | col42 | `A_p` (« Personenfläche ») | 35 | m² (`m c2 b2`, propre) | **WARNING** |
| `M` | col43 | `M` (« Aktivitätsgrad ») | 1.2 | met | **WARNING** |
| `p_Be` | col51 | `p_Be` (« Elektrische Leistung Geräte ») | 10 | W/m2 | **WARNING** |
| `E_vm` | col64 | `E_vm` (« Beleuchtungsstärke ») | 150 | lx | **WARNING** |

**Le CODE est correct** : lit bien **col30** (exploitation) et **jamais col28** (design = 26 °C) ;
symboles et unités concordent ; statut `STANDARD_USAGE_INPUT`, `project_value=None`,
déduplication par code d'usage, bloqueur agrégé unique si code inconnu (tests 40/40 PASS).

**Pourquoi WARNING et non PASS** : la **source primaire SIA 2024:2021 Raumdatenblätter V221
est ABSENTE de `/refs`** (seuls existent des JSON dérivés `sia-2024-2021.usage-data.json` /
`.tables.json`, extraction `reference-data-engineer` datée 2026-08-14). Je peux prouver
*code ↔ JSON figé*, mais **pas** *JSON ↔ SIA 2024 primaire*. Conformément à la méthode
(« si une valeur de référence [primaire] est absente, le test ne peut PAS être signé »), je
**ne signe pas** la fidélité normative de ces 6 valeurs → renvoi `reference-data-engineer`
(figer/joindre la source primaire) + `norm-analyst` (confirmer que col30 « exploitation » est
bien la consigne à substituer pour le calcul FROID SIA 380/2 ; cf. observation O-2).

---

## 2. Vérification de la LOGIQUE de substitution (tests adverses exécutés)

### 2.1 Sélection de bande génération — bornes 12 / 50 / 150 kW

Tests adverses que j'ai exécutés (non prévus par l'implémenteur) via `build_reference_project_specification` :

**FROID (air, Tab 5) :**
```
cc=12.0     -> SUBSTITUTABLE  EER=2.9     (≤12 inclusif)
cc=12.0001  -> SUBSTITUTABLE  EER=3.0     (>12)
cc=50.0     -> SUBSTITUTABLE  EER=3.0     (≤50 inclusif)
cc=50.0001  -> SUBSTITUTABLE  EER=3.1     (>50)
cc=149.999  -> SUBSTITUTABLE  EER=3.1
cc=150.0    -> PROJECT_VALUE_MISSING (bloqueur EER+)   <-- seuil ≥150 = eau
cc=200.0    -> PROJECT_VALUE_MISSING (bloqueur EER+)
```
**CHAUD (air-eau, Tab 8) :**
```
hc=150.0    -> SUBSTITUTABLE  SCOP=3.2    (≤150 inclusif)
hc=150.0001 -> PROJECT_VALUE_MISSING (Tab 8 s'arrête à 150)
hc=300.0    -> PROJECT_VALUE_MISSING
```

**Verdict PASS.** Bandes `]p_min ; p_max]` (ouvert à gauche, fermé à droite) ; bande basse `≤12`
inclusive. **Asymétrie voulue et correcte au seuil 150 kW** :
- Froid : `≥ 150` → bloqueur (le *type* de machine bascule air→eau, Tab 2 « à partir de 150 kW »).
- Chaud : `= 150` → substituable 3,20 (le *type* reste PAC air-eau ; seule l'étendue tabulée du Tab 8 s'arrête à 150).

Ces deux règles reflètent fidèlement le PDF : bascule de type froid par Tableau 2 (§7.2.5.4-5) ;
étendue de tabulation chaud par Tableau 8.

### 2.2 Gate EN 410 du g⊥ (`_comparable_g_perp`)

- g dont la source ne prouve pas EN 410 **et** sans champ `g_value_bs_en_410` → `None` → bloqueur
  (« a g_total including shading must not be substituted »). Correct : jamais substituer un g_total.
- source contenant `bs_en_410` **ou** champ EN 410 présent → accepté (renvoie `solar_factor`, repli `g_value_bs_en_410`).
- Miroir explicite du `SIA3802Checker._is_sia_comparable_g_value`. **PASS** (tests 246-278 concordants).

### 2.3 Gate d'unité infiltration (`_collect_infiltration_substitution`)

- Ne lit que `infiltration_m3_h_m2` (seule unité comparable au Tab 2).
- Si absente mais `infiltration_rate` présent → bloqueur **de conversion d'unité** (jamais de substitution silencieuse).
- Worst-case = `max` (jamais moyenne). **PASS**.

### 2.4 Sémantique `STANDARD_USAGE_INPUT` / `REFERENCE_DIRECTIVE`

- Les deux statuts ont `project_value=None` et ne sont **jamais** comptés comme bloqueurs
  (`status == SUBSTITUTABLE and reference_value is None` seul déclenche le bloqueur « No encoded SIA reference value »).
- Conforme à §7.2.5.3 (grandeurs d'usage identiques projet/référence — vérifié sur PDF Tab 2 :
  toutes ces grandeurs affichent « SIA 2024 » dans les colonnes VL **et** VC) et au Tab 2 (directives
  émission/puissance prescriptives). **PASS**.

### 2.5 θ = col30 (exploitation) jamais col28 (design)

Confirmé côté code (`_SIA2024_USAGE_SYMBOLS[0] = ("theta_i_mean", "30", …)`) et côté données
(col28=`theta_i_design`=26 ; col30=`theta_i_mean`=25 ; test `test_theta_i_mean_uses_col30…` vérifie 25 ≠ 26). **PASS**.

---

## 3. Recoupement du périmètre `config.py` contre le PDF (corroboration)

Au-delà des 22 valeurs émises, j'ai recoupé **cellule par cellule** l'ensemble des constantes
SIA 380/2 du périmètre lu contre Tableaux 2/3/5-9. **Toutes concordantes (0 écart).**

| Bloc config | Contenu vérifié | Source | Écarts |
|---|---|---|---|
| `SIA3802_LIMIT_VALUES` / `SIA3802_TARGET_VALUES` — enveloppe | 9 constructions × (VL+VC) : 0,20/0,14 · 0,30/0,20 · 0,30/0,30 · 2,70/2,70 · 0,28/0,20 · 0,30/0,20 · 0,64/0,64 · 0,30/0,20 · 0,20/0,14 | Tab 3 p36-37 | 0 |
| ... ponts thermiques | ψ/χ = 0/0 (VL et VC) | Tab 2 p32 | 0 |
| ... ventilation/AHU/pertes de charge | εV 1,0/1,4 · gaines C/C · AHU L2/L1 · Uahu 0,70/0,50 · Hdu 15/10 · Δp SUP 700/550 · Δp ETA 500/350 · Δp hr 300/400 | Tab 2 p33-34 | 0 |
| ... récupération de chaleur | ηrec,θ 0,73/0,78 · ηrec,x 0,0/0,60 | Tab 2 p34 | 0 |
| ... régulation Δθctr | froid **−1,8**/0 · chaud **+1,2**/0 (**signes vérifiés**) | Tab 2 p34-35 | 0 |
| ... photovoltaïque | PPV 10 WP/m² · ηconv 0,90/0,90 · cible ηPV,STC 0,17 | Tab 2 p35 | 0 |
| `SIA3802_COOLING_EER_SEER_LIMITS/TARGETS` — air | 5 bandes EER+SEER, limite et cible (2,90…3,40 / 3,80…4,40 ; 3,10…3,60 / 4,20…5,00) | Tab 5 p38 | 0 |
| ... eau | 5 bandes EER+SEER, limite et cible (4,05…5,50 / 4,50…6,70 ; 4,45…6,00 / 5,90…8,00) | Tab 6 p38 | 0 |
| `SIA3802_WATER_COOLED_POST_COOLING_EERPLUS` | 5 bandes EER+ pleine charge/50 %, limite et cible (3,15…3,70 / 4,55…6,00 ; 3,95…4,50 / 5,60…8,00) | Tab 7 p38-39 | 0 |
| ... auxiliaires §7.2.5.6 | ventilateurs 0,036 · pompe post-refr. 0,012 · pompe eau froide 0,015 | p39 §7.2.5.6 | 0 |
| `SIA3802_HEATING_SCOP_LIMITS/TARGETS` — air-eau | 3,00/3,10/3,20 ; cible `None` | Tab 8 p39 | 0 |
| ... saumure-eau (`heating_brine_water_hp`) | limite 4,00/4,20/4,60/5,00/5,50 ; cible 4,40/4,60/5,00/5,50/6,00 | Tab 9 p39 | 0 |

---

## 4. Ce que ma lecture PDF RÉSOUT dans `sia380-2-generation-reference.spec.md`

L'agent `norm-analyst` a laissé 15 `[TO VERIFY]` faute d'avoir ouvert le PDF. Ma lecture primaire en **résout 7** :

| # spec | Question | Résolution par lecture PDF | Statut |
|---|---|---|---|
| 1 | Borne 150 kW : « < 150 / ≥ 150 » vs « ≤ 150 / > 150 » ? | Tab 2 p34 : « < 150 kW » (air) / « à partir de 150 kW » (eau) → **< 150 / ≥ 150** | **RÉSOLU** |
| 2 | Inclusivité des bornes rondes 12/50/150… | En-têtes « ≤ 12 », « > 12… ≤ 50 » → `]p_min ; p_max]`, bande 1 `≤` inclusif | **RÉSOLU** |
| 3 | Tableau 7 non extrait (valeurs/bandes) | **Extrait** p38-39 : EER+ pleine charge & 50 %, bandes 12-50→>1000 ; = `SIA3802_WATER_COOLED_POST_COOLING_EERPLUS` | **RÉSOLU** |
| 10 | Tableau 8 a-t-il une colonne cible ? | Tab 8 p39 : **non**, seulement « valeurs limites » → `target=None` correct | **RÉSOLU** |
| 11 | Tableau 9 porte-t-il limite ET cible ? | Tab 9 p39 : **oui**, « valeurs limites » ET « valeurs cibles » | **RÉSOLU** |
| 12 | Articles exacts Tab 8/9 | p39 : §7.2.5.8 = PAC air-eau (Tab 8) ; §7.2.5.9 = PAC saumure-eau (Tab 9) | **RÉSOLU** |
| 13 | §7.2.5.6 base des % auxiliaires | p39 : ventilateurs/pompe = part de la **puissance de post-refroidissement** ; pompe eau froide = part de la **puissance du générateur de froid** | **RÉSOLU** |

**Restent non résolus (normes externes absentes de `/refs`, hors de ma portée)** : équivalence
`SEER`/`SCOP` (VE) ↔ **SN EN 14825** (#8/#9 de la spec) ; méthode §7.2.5.7 via **SN EN 16798-13:2017**
(#14). `reference_project` les neutralise correctement : froid comparé sur EER pleine charge (pas SEER),
et caveat `[SCOP per SN EN 14825 - VE index equivalence TO VERIFY]` attaché à chaque ligne SCOP (voir §5).

---

## 5. Vérification des caveats exigés

| Caveat attendu | Présent ? | Emplacement | Verdict |
|---|---|---|---|
| `[TO VERIFY]` SN EN 14825 sur SCOP | Oui | `_generation_substitution` ajoute `" [SCOP per SN EN 14825 - VE index equivalence TO VERIFY]"` si `grandeur == "SCOP"` ; `config.py` l.44-46 `[TO VERIFY]` | **PASS** |
| Froid ≥ 150 kW → bloqueur EER+ (Tab 7) | Oui | `_collect_generation_substitutions` : `cooling_capacity >= SIA3802_COOLING_AIR_CHILLER_MAX_KW` → bloqueur, `reference_value=None`, message « Table 7 EER+ … not auto-comparable » | **PASS** |
| Pas d'import `iesve` (séparation dur/pur) | Oui | imports = `json, os, dataclasses, typing, .config, .model_analyzer` ; « iesve » n'apparaît qu'en **commentaire** (l.114, 672). Tests s'exécutent sans VE. | **PASS** |

---

## 6. Divergences et observations

### Divergences de valeur : **AUCUNE** (0 CRITIQUE, 0 MAJEURE, 0 MINEURE)

Toutes les valeurs figées vérifiables contre `refs/SIA-380-2-2022.pdf` sont **fidèles**.

### Observations (ne bloquent pas la signature des familles 1-7)

- **O-1 — WARNING (traçabilité, famille 8)** : source primaire **SIA 2024:2021 absente de `/refs`**.
  Les 6 valeurs d'ancrage (25/60/35/1,2/10/150) sont prouvées *code ↔ JSON figé* mais non
  *JSON ↔ primaire*. → `reference-data-engineer` : joindre/figer la source primaire (Raumdatenblätter V221).
- **O-2 — INFO (sémantique, famille 8)** : col30 (`theta_i_mean` = 25 °C) est **constante sur 32 usages** ;
  libellé « Mittlere Raumtemperatur (Exploitation/Energie) ». SIA 380/2 traite du **FROID**, donc une
  consigne moyenne 25 °C est plausible (vs col28 design 26 °C). Choix col30 **correct** pour un calcul
  énergie/froid, mais Tab 2 distingue θi,set,**C** (été) et θi,set,**H** (hiver) : `norm-analyst` doit
  confirmer que la valeur unique substituée couvre bien le besoin (documentaire ici, `project_value=None`,
  n'alimente aucun calcul dans ce module). Idem `phi_i` (été vs hiver).
- **O-3 — INFO (portée)** : `reference_project` ne construit que le projet de référence **« valeur limite »**
  (via `SIA3802_LIMIT_VALUES`). Le projet de référence **« valeur cible »** (§7.2.5.2 autorise la conformité
  par VL **ou** VC) n'est pas généré. Non-erreur (la limite est la base la plus stricte), mais à documenter
  explicitement pour éviter qu'un lecteur croie la conclusion SIA 380/2 complète.
- **O-4 — INFO (portée, non exercée)** : la bande basse de `heating_brine_water_hp` (`upper_kw=50`) couvre
  `P<12` alors que le Tableau 9 ne tabule qu'à partir de 12 kW ([INTERPRÉTATION] d'extension). **Sans effet
  sur `reference_project`** (qui n'utilise que `heating_air_water_hp`). Signalé pour tout autre consommateur.
- **O-5 — INFO (représentation)** : la directive d'émission encode « par convection » en `radiant_fraction=0.0`.
  Représentation machine acceptable (champ `directive` explicite) ; ce 0.0 n'est pas un nombre normatif de table.

---

## 7. Verdict global signé

**Chiffres.** 22 valeurs figées émises par les 8 familles + 1 règle de seuil (150 kW) + 2 directives
qualitatives, **toutes vérifiées** ; ~110 constantes du périmètre `config.py` recoupées cellule par cellule
contre Tableaux 2/3/5-9. **Divergences de valeur : 0.** Tests : `tests/test_reference_project.py` 40/40 PASS
+ mes tests adverses de bornes PASS.

**Décision de signature (par famille) :**

| Famille | Verdict | Signable |
|---|---|---|
| 1 — opaque_envelope_constructions | PASS | **OUI** |
| 2 — window_u_value_and_frame_fraction | PASS | **OUI** |
| 3 — glazing_solar_and_visible_properties | PASS | **OUI** |
| 4 — infiltration | PASS | **OUI** |
| 5 — cooling_generation_and_auxiliaries | PASS | **OUI** |
| 6 — heating_generation | PASS | **OUI** |
| 7 — emission_system_and_unlimited_capacity | PASS | **OUI** |
| 8 — sia2024_internal_gains_profiles_and_setpoints | WARNING | **NON** (source primaire SIA 2024 absente de `/refs`) |

**Familles 1 à 7 (cœur traçable au PDF SIA 380/2:2022) : AUDITÉ OK — 2026-08-14 — qa-auditor.**

**Famille 8 (SIA 2024) : NON SIGNÉE.** Le comportement du code est correct et reproductible contre le JSON
figé, mais la fidélité normative des 6 valeurs d'ancrage n'est pas prouvable tant que la source primaire
SIA 2024:2021 Raumdatenblätter n'est pas présente dans `/refs`. Renvoi à `reference-data-engineer`
(source primaire) et `norm-analyst` (confirmation O-2). La signature sera étendue à la famille 8 après levée d'O-1.

> — `qa-auditor`, 2026-08-14
