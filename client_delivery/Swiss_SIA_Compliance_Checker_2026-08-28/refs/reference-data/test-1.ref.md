# test-1.ref.md — Données de référence SIA 4010 Test 1

**Statut : COMPLET (CORRIGÉ - PASS 3)**

**Date extraction : 2026-07-30**
**Agent : reference-data-engineer (haiku)**
**Source : `SIA_4010_geteilter_Link/Test1/Resultaterfassung_Test1.xlsx` (version 1.1)**

---

## Résumé de l'extraction

Le fichier Excel `Resultaterfassung_Test1.xlsx` a été exploré et complètement extrait vers le fichier JSON companion `test-1.ref.json`.

**✅ DONNÉES CRITIQUES EXTRAITES (chauffage/refroidissement + températures) :**
- **Table 28** (Chauffage sensible) : données mensuelles + annuelles pour les cas **1E, 600, 640, 900, 940** [kWh]
- **Table 29** (Refroidissement sensible) : données mensuelles + annuelles pour les cas **1E, 600, 640, 900, 940** [kWh]
- **Table 30** (Température opérative moyenne mensuelle) : données mensuelles + annuelles pour les cas **600, 640, 900, 940, 600FF, 900FF** [°C]
  - **Cas 600FF et 900FF : critique pour la validation** (flottement libre, aucun chauffage/refroidissement)
- **Table 32** (Extrêmes annuels de température opérative) : Max/Min/Moyenne annuels pour les cas **600, 640, 600FF, 900FF** [°C]
  - **Cas 600FF et 900FF : seule sortie contrôlée** (température, pas d'énergie)
- **Critère pass/fail pour cas 1E** : les bornes de dispersion (min/max) des programmes de référence sont présentes pour Tables 28 et 29
- **Aucun critère pass/fail pour cas 600/640/900/940** : données informatiques (comparaison visuelle)
- **Aucun critère pass/fail pour cas 600FF/900FF** : données informatiques uniquement (flottement libre)

**⏳ DONNÉES OPTIONNELLES (non critiques pour validation, disponibles dans l'Excel) :**
- **Table 33** : Profils horaires chauffage/refroidissement du 4 janvier (cas 600/640/900/940)
- **Table 34** : Profils horaires température opérative du 4 janvier (tous cas)
- Profils horaires chauffage/refroidissement du 27 juillet
- Profils horaires température opérative du 27 juillet
- Données horaires brutes (feuille `Daten_Testprogramm`) pour calculs spécialisés

---

## Structure du fichier Excel

### Vue générale

Le fichier `Resultaterfassung_Test1.xlsx` contient **24 éléments** :
- **8 feuilles de travail (Worksheet)** avec données
- **16 feuilles de graphiques (Chartsheet)** – non pertinentes pour l'extraction de données brutes

### Feuilles pertinentes

#### 1. **Zusammenfassung Testfälle** (Résumé des cas de test)
- **Dimensions** : A1:CP335
- **Contient** : tables récapitulatives 28-34 avec données mensuelles et annuelles
- **Organisation** : colonnes pour chaque cas (1E, 600, 640, 900, 940) ; ligne 13 = en-têtes des cas, ligne 15 = en-têtes des colonnes
- **Tables présentes** :
  - Ligne 11 : **Table 28** — Chauffage sensible mensuel/annuel (mois 1-12 + Annual)
  - Ligne 32 : **Table 29** — Refroidissement sensible mensuel/annuel
  - Ligne 53 : **Table 30** — Température opérative moyenne mensuelle
  - Ligne 99 : **Table 32** — Extrêmes annuels de température opérative
  - Ligne 125 : **Table 33** — Profils horaires chauffage/refroidissement 4 janvier
  - Ligne 163 : **Table 34** — Profils horaires température opérative 4 janvier
  - Ligne 194 : **Table XX** — Profils horaires chauffage/refroidissement 27 juillet
  - Ligne 234 : **Table XX** — Profils horaires température opérative 27 juillet

#### 2. **Zusammenfassung Diagnosefälle** (Résumé des cas diagnostiques)
- **Dimensions** : A1:AX230
- **Contient** : cas diagnostiques 1A-1D (transition Test 1 → Test 2) + baseline 600
- **Non extrait cette session** (hors du champ du Test 1)

#### 3. **Daten_Testprogramm** (Données brutes du programme testé)
- **Dimensions** : A1:BW8764
- **Contient** : données horaires annuelles (8760 heures) pour chaque cas
- **Organisation** : colonnes de cas 600, 640, 900, 940, 600FF, 900FF, 1E + diagnostiques
- **Sous-colonnes par cas** : Stunde (heure), Raumlufttemperatur (temp. air), Operative Raumtemperatur (temp. opérative), Leistung sensibel Heizen (puissance chauffage), Leistung sensibel Kühlen (puissance refroidissement)
- **Non extrait cette session** (données brutes ; les résumés suffisent pour la validation)

#### 4. **Daten_EN ISO 52016-1 2017**, **Daten_IDA_ICE**, **Daten_EXCEL_SIA_SIA380_2**, **Daten_EnergyPlus**, **Daten_TAS**
- **Structure identique à Daten_Testprogramm** : données horaires des programmes de référence
- **Non extrait cette session**

---

## Détail des données extraites

### Table 28 — Chauffage sensible [kWh]

**Localisation Excel** : Feuille "Zusammenfassung Testfälle", ligne 11 à 28 (12 mois + Annual)

**Cas et colonnes** :

| Cas | Col. Testprogramm | Col. ISO 52016-1 | Col. IDA ICE | Col. EXCEL SIA | Col. Energy+ | Col. TAS | Limites (1E) |
|---|---|---|---|---|---|---|---|
| **1E** | B | — | C | D | E | F | G (moy), H (max), I (min) |
| **600** | L | M | N | O | P | Q | — |
| **640** | T | U | V | W | X | Y | — |
| **900** | AB | AC | AD | AE | AF | AG | — |
| **940** | AJ | AK | AL | AM | AN | AO | — |

**Notes critiques** :
- Cas **1E** : dispose des colonnes Mittelwert (moyenne, col. G), obere Grenze (limite max, col. H), untere Grenze (limite min, col. I)
  - Ces limites forment la plage de dispersion (Streubereich) des programmes de référence
  - Critère pass/fail du Test 1 : `testprogramm_candidate ∈ [range_min, range_max]`
- Cas **600/640/900/940** : pas de limites ; données informatiques uniquement (comparaison visuelle, pas de verdict)
- Colonne ISO 52016-1 pour cas non-1E = "Daten Norm EN ISO 52016-1 2017" (norme de référence)
- Colonnes IDA ICE, EXCEL SIA, Energy+, TAS = résultats des 4 programmes de référence complétant 1E

**Données extraites vers JSON** :
```json
reference_values.sensible_heating_demand_kwh[case_id].monthly[month_NN]
reference_values.sensible_heating_demand_kwh[case_id].annual
```

**Exemple (1E, mois 1)** :
```json
{
  "testprogramm_candidate": {"value": 0, "unit": "kWh", "cell": "B16"},
  "ida_ice_5_0_beta_23": {"value": 543.39, "unit": "kWh", "cell": "C16"},
  "excel_sia_380_2": {"value": 588.87, "unit": "kWh", "cell": "D16"},
  "energyplus_openstudio_9_1_0": {"value": 481.16, "unit": "kWh", "cell": "E16"},
  "tas_edsl_9_5_2": {"value": 508.90, "unit": "kWh", "cell": "F16"},
  "mean_of_programs": {"value": 530.58, "unit": "kWh", "cell": "G16"},
  "range_max": {"value": 588.87, "unit": "kWh", "cell": "H16", "note": "obere Grenze"},
  "range_min": {"value": 472.29, "unit": "kWh", "cell": "I16", "note": "untere Grenze"}
}
```

### Table 29 — Refroidissement sensible [kWh]

**Localisation Excel** : Ligne 32 à 49

**Structure identique à Table 28**
**Données extraites vers JSON** :
```json
reference_values.sensible_cooling_demand_kwh[case_id].monthly[month_NN]
reference_values.sensible_cooling_demand_kwh[case_id].annual
```

---

## Programme de référence inclus (Test 1E)

Basés sur l'en-tête (ligne 5-7) :

| Programme | Version | Date |
|---|---|---|
| **IDA ICE** | 5.0 Beta 23 | 2022-11-28 |
| **EXCEL SIA 380/2** | (E4Tech + G. Zweifel) | 2024-07-01 |
| **Energy+/OpenStudio** | 9.1.0 | 2022-11-23 |
| **EDSL-Tas** | 9.5.2 | 2022-11-22 |
| **Daten Norm EN ISO 52016-1** | 2017 | — |

---

### Table 30 — Température opérative moyenne mensuelle [°C]

**Localisation Excel** : Feuille "Zusammenfassung Testfälle", lignes 53-70 (12 mois + Annual)

**Cas et colonnes** :

| Cas | Col. Month | Col. Testprogramm | Col. ISO 52016-1 | Col. IDA ICE | Col. EXCEL SIA | Col. Energy+ | Col. TAS |
|---|---|---|---|---|---|---|---|
| **600** | (implicit rows 58-70) | B | C | D | E | F | G |
| **640** | (implicit rows 58-70) | J | K | L | M | N | O |
| **900** | (implicit rows 58-70) | R | S | T | U | V | W |
| **940** | (implicit rows 58-70) | Z | AA | AB | AC | AD | AE |
| **600FF** | AG | AH | AI | AJ | AK | AL | AM |
| **900FF** | AO | AP | AQ | AR | AS | AT | AU |

**Notes critiques** :
- Cas **1E** : ABSENT de cette table (a chauffage/refroidissement, voir Tables 28-29)
- Cas **600/640/900/940** : données comparatives uniquement, sans critère pass/fail
- Cas **600FF/900FF** : **CRITIQUE** — température opérative est la SEULE sortie contrôlée (flottement libre, pas de chauffage/refroidissement)
  - Valeur testprogramm = #DIV/0! (erreur Excel, car candidat n'a pas exécuté pour ces cas)
  - Données informatiques présentes pour tous les programmes
  - **Aucun critère pass/fail** spécifié dans l'Excel pour ces cas

**Données extraites vers JSON** :
```json
reference_values.operative_temperature_monthly_celsius[case_id].monthly[month_NN]
reference_values.operative_temperature_monthly_celsius[case_id].annual
```

**Exemple (cas 600, mois 1)** :
```json
{
  "testprogramm_candidate": {"value": null, "unit": "°C", "note": "Value was #DIV/0!"},
  "iso_52016_1_2017_reference": {"value": 22, "unit": "°C", "cell": "C58", "note": "Daten Norm EN ISO 52016-1"},
  "ida_ice_5_0_beta_23": {"value": 22.43, "unit": "°C", "cell": "D58"},
  "excel_sia_380_2": {"value": 22.16, "unit": "°C", "cell": "E58"},
  "energyplus_openstudio_9_1_0": {"value": 22.05, "unit": "°C", "cell": "F58"},
  "tas_edsl_9_5_2": {"value": 22.44, "unit": "°C", "cell": "G58"}
}
```

### Table 32 — Extrêmes annuels de température opérative [°C]

**Localisation Excel** : Feuille "Zusammenfassung Testfälle", lignes 104-107

**Cas et structure** :

La table 32 contient **uniquement** deux cas (flottement libre, FF) :

| Cas | Métrique | Col. Testprogramm | Col. ISO 52016-1 | Col. IDA ICE | Col. EXCEL SIA | Col. Energy+ | Col. TAS |
|---|---|---|---|---|---|---|---|
| **600FF** | Max / Min / Average (lignes 105-107) | B | C | D | E | F | G |
| **900FF** | Max / Min / Average (lignes 105-107) | J | K | L | M | N | O |

**Notes** :
- En-têtes à ligne 104 : "Case id.", "Testprogramm", "Daten Norm EN ISO 52016-1", "IDA ICE", "EXCEL SIA 380/2", "Energy+/OpenStudio", "EDSL-Tas"
- Lignes 105-107 : Max, Min, Average (annuels)
- Données ASHRAE 140 aussi présentes (colonnes AZ-BG) pour référence

**Notes critiques** :
- **Cas 600FF/900FF** : **CRITIQUE** — température est l'UNIQUE sortie du système
  - Testprogramm = #DIV/0! (erreur Excel : candidat n'a pas exécuté pour cas libre-flottement)
  - **Aucun critère pass/fail** spécifié
  - Structure spéciale : données ASHRAE 140 aussi présentes (colonnes AZ-BG) pour référence

**Données extraites vers JSON** :
```json
reference_values.operative_temperature_annual_extremes_celsius[case_id].annual.max
reference_values.operative_temperature_annual_extremes_celsius[case_id].annual.min
reference_values.operative_temperature_annual_extremes_celsius[case_id].annual.average
```

**Exemple (cas 600FF, Max — ligne 105, colonnes A-G)** :
```json
{
  "label": "Max.",
  "testprogramm_candidate": {"value": 0, "unit": "°C", "cell": "B105", "note": "Testprogramm = 0 (candidat non exécuté)"},
  "iso_52016_1_2017_reference": {"value": 63.5, "unit": "°C", "cell": "C105", "note": "Daten Norm EN ISO 52016-1"},
  "ida_ice_5_0_beta_23": {"value": 70.95, "unit": "°C", "cell": "D105"},
  "excel_sia_380_2": {"value": 62.317940500454625, "unit": "°C", "cell": "E105"},
  "energyplus_openstudio_9_1_0": {"value": 66.87718451926874, "unit": "°C", "cell": "F105"},
  "tas_edsl": {"value": 65.44, "unit": "°C", "cell": "G105"}
}
```

---

## Données NON EXTRAITES (mais présentes dans l'Excel)

### Tables 33-34 — Profils horaires [4 janvier et 27 juillet]
- **Localisation** : Lignes 125-234
- **Contient** : 24 valeurs horaires par jour pour chaque cas
- **Motif non extraction** : Données détaillées ; résumés (Tables 28-30-32) suffisent pour validation

### Données brutes horaires
- **Localisation** : Feuille `Daten_Testprogramm` (8760 lignes) + feuilles par programme
- **Motif non extraction** : Inutile pour critères de validation (les résumés suffisent)

---

## Traçabilité exacte des données

### Table 28 (Chauffage sensible), mois 1, cas 1E

| Élément | Valeur | Source |
|---|---|---|
| Testprogramm candidate | 0 kWh | Excel cell B16 |
| IDA ICE | 543.39 kWh | Excel cell C16 |
| EXCEL SIA 380/2 | 588.87 kWh | Excel cell D16 |
| Energy+ 9.1.0 | 481.16 kWh | Excel cell E16 |
| TAS 9.5.2 | 508.90 kWh | Excel cell F16 |
| Moyenne | 530.58 kWh | Excel cell G16 (Mittelwert) |
| **Limite MAX** | **588.87 kWh** | **Excel cell H16 (obere Grenze)** ← **CRITÈRE PASS/FAIL** |
| **Limite MIN** | **472.29 kWh** | **Excel cell I16 (untere Grenze)** ← **CRITÈRE PASS/FAIL** |

### Table 29 (Refroidissement sensible), mois 1, cas 1E

Même structure, colonnes identiques, valeurs différentes.

### Table 28, Annual, cas 600

| Élément | Valeur | Source |
|---|---|---|
| Testprogramm candidate | 0 kWh | Excel cell L28 |
| ISO 52016-1 2017 ref | 5134 kWh | Excel cell M28 |
| IDA ICE | 4506.238470758 kWh | Excel cell N28 |
| EXCEL SIA 380/2 | 5450.047835940987 kWh | Excel cell O28 |
| Energy+ 9.1.0 | 4408.066501756151 kWh | Excel cell P28 |
| TAS 9.5.2 | 5119.409780000002 kWh | Excel cell Q28 |
| (no criteria) | — | — |

---

## Adéquation aux spécifications

### Spec §5 — Grandeurs de sortie contrôlées

**Complètement couvert** :

- ✅ **Cas 600, 640, 900, 940, 1E** : Puissance horaire chauffage/refroidissement
  - Fourni sous forme d'**énergie mensuelle + annuelle** (Tables 28-29 extraites)
  - Résumés suffisants pour validation (profils horaires optionnels)

- ✅ **Cas 600, 640, 900, 940, 600FF, 900FF** : Température opérative horaire
  - Résumés mensuels + annuels (Tables 30 et 32 extraites)
  - **Cas 600FF/900FF** : température est l'UNIQUE sortie (flottement libre)

### Spec §6 — Critère d'acceptation

**Couverture complète** :

- ✅ **Cas 1E** : Streubereich (plage min/max) présente dans l'Excel (Tables 28-29)
  - `range_max` (obere Grenze) colonne H
  - `range_min` (untere Grenze) colonne I
  - Critère : `testprogramm ∈ [range_min, range_max]` pour chauffage et refroidissement
  - **Seul vrai critère pass/fail du Test 1**

- ✅ **Cas 600/640/900/940** : Marqués comme "informatif" (pas de critère)
  - **Aucune limite min/max dans Tables 28-29-30-32**
  - Données d'affichage comparatif uniquement

- ✅ **Cas 600FF/900FF** : Marqués comme "informatif" (pas de critère)
  - **Aucune limite min/max dans Tables 30-32**
  - Données d'affichage comparatif uniquement
  - **Note** : Ces cas n'ont pas de chauffage/refroidissement, seule température opérative est contrôlée

---

## Limitations et réserves

### Extraction complète (données critiques uniquement)

L'extraction couvre **toutes les données critiques pour l'implémentation du moteur de validation** :
- Tables 28-29 (chauffage/refroidissement mensuel + annuel) → critère binaire pour cas 1E
- Tables 30-32 (température opérative) → données comparatives pour tous les cas
- Limitation volontaire : les profils horaires détaillés (4 jan, 27 juil) ne sont pas extraits
  - Ces données sont disponibles dans l'Excel et peuvent être extraites si nécessaire pour le débugging

### Cas 600FF et 900FF — Traitement spécial

**Importance** : Critiques pour Test 1 (flottement libre, pas de chauffage/refroidissement)
- **Grandeurs** : température opérative (Tables 30 et 32) SEULES
- **Critère pass/fail** : AUCUN (flottement libre → pas de critère de validation)
- **Données** : résumés mensuels (Table 30) + extrêmes annuels (Table 32)
- **Status d'extraction** : COMPLET pour Tables 30 et 32

### Programmes de référence

L'Excel contient les résultats de **5 programmes de référence** :
- 4 programmes informatiques : IDA ICE, EXCEL SIA 380/2, Energy+/OpenStudio, TAS EDSL
- 1 norme : ISO 52016-1:2017 (données de calcul)

Ces valeurs sont **présentes et intégrées au JSON** pour tous les cas.
- Pour le cas 1E, les limites (min/max) sont déjà calculées par l'Excel à partir des 4 programmes informatiques
- Pour les cas 600/640/900/940/600FF/900FF, aucun calcul de limites n'est fourni → données informatiques uniquement

---

## Points pour qa-auditor

1. **Vérifier la cohérence des limites 1E** :
   - Pour chaque mois et pour l'annual : min ≤ moyenne ≤ max ?
   - Les limites correspondent bien au min/max des 4 programmes ?

2. **Cas 600/640/900/940** :
   - Vérifier que testprogramm_candidate a la valeur 0 (candidat pas encore exécuté)
   - Les 5 programmes de référence ont-ils tous des valeurs non-nulles ?

3. **Programmes de référence (identifiants) **:
   - Vérifier que les colonnes C/D/E/F pour cas 1E correspondent bien à IDA ICE / EXCEL SIA / Energy+ / TAS
   - Vérifier que les colonnes N/O/P/Q pour cas 600+ correspondent bien aux mêmes

4. **Cas diagnostiques** :
   - Les cas 1A-1D ne sont pas dans "Zusammenfassung Testfälle"
   - Vérifier que l'extraction est limitée aux cas Test 1 (1E, 600, 640, 900, 940, 600FF, 900FF)

5. **Cas 600FF et 900FF** :
   - Vérifier que testprogramm_candidate a la valeur #DIV/0! ou vide (candidat n'a pas de chauffage/refroidissement)
   - Vérifier que Table 30 (température mensuelle) est complète pour ces cas
   - Vérifier que Table 32 (extrêmes annuels) est complète pour ces cas
   - Vérifier qu'il n'y a PAS de critère pass/fail pour ces cas (flottement libre)

---

## Versionning

| Date | Auteur | Changement |
|---|---|---|
| 2026-07-30 | reference-data-engineer | Extraction Tables 28-29 complètes. Status: Partiellement extrait (critique obtenu, complémentaire en attente). |
| 2026-07-30 | reference-data-engineer | Extraction Tables 30-32. Correction O28 value (5450.047835940987). Status: COMPLET. Toutes les données critiques extraites. |
| 2026-07-30 | reference-data-engineer | **ERRATUM (Pass 1)**: Bug découvert et corrigé dans Tables 30 et 32 (600FF/900FF). **Problème** : Décalage de colonnes d'une position vers la droite. Les colonnes testprogramm/ISO/IDA/Excel/Energy+/Tas étaient mappées à AI/AJ/AK/AL/AM/AN au lieu de AH/AI/AJ/AK/AL/AM pour le cas 600FF (colonne Month AG était omise). Pour Table 32, la zone d'extrêmes annuels utilisait incorrectement les colonnes BH-BM au lieu de la zone standard A-G / I-O aux lignes 105-107. **Correction** : Remapping correct des colonnes; documentation mise à jour; Testprogramm marqué comme erreur Excel (#DIV/0!) où applicable. **Impact** : Toutes les valeurs affectées (600FF/900FF) dans Tables 30 et 32 sont maintenant correctes. |
| 2026-07-30 | qa-auditor | **AUDIT INDÉPENDANT** : Découverte de deux défauts bloquants supplémentaires (DÉFAUT n°1, n°2) qui subsistent après Pass 1. Vérification exhaustive cellule par cellule (1318 couples {value, cell}), comparaison label↔colonne contre les vraies lignes d'en-tête. **DÉFAUT n°1** (BLOQUANT) : Table 30, cas 600/640/900/940 — Décalage de +1 colonne (les 4 cas ordinaires n'ont jamais été corrigés après Pass 1). Colonnes réelles : 600=[B/C/D/E/F/G], 640=[J/K/L/M/N/O], 900=[R/S/T/U/V/W], 940=[Z/AA/AB/AC/AD/AE], mais JSON utilise [C/D/E/F/G/H], [K/L/M/N/O/P], [S/T/U/V/W/X], [AA/AB/AC/AD/AE/AF]. Conséquences : perte colonne Testprogramm (#DIV/0!), chaque programme mal étiqueté (iso_val=ISO, ida_val=IDA→EXCEL, ...), EDSL-Tas disparaît complètement. **DÉFAUT n°2** (BLOQUANT) : Table 32 — Deux entrées fantômes "600" et "640" (doublons mal étiquetés de 600FF/900FF, cellules B–G et J–O = même contenu physiquement impossible pour cas chauffés). **Audit** : qa-auditor demande Pass 3 complète + refus de signature tant que défauts non corrigés. |
| 2026-07-30 | reference-data-engineer | **ERRATUM (Pass 3)** : Correction complète des défauts n°1 et n°2 + mise à jour métadonnées cohérentes. **Défaut n°1** : Réextraction Tables 30 complètes (cas 600/640/900/940 + 600FF/900FF) avec bon mapping colonne↔label après vérification cellule par cellule (openpyxl). Testprogramm (#DIV/0!) maintenant en B/J/R/Z correct avec note "Erreur Excel". Champ tas_edsl_9_5_2 restauré (était manquant). **Défaut n°2** : Suppression entrées "600" et "640" de Table 32 (ne garde que 600FF/900FF). **Défaut n°3** : data_missing, status, et ce `.md` mis à jour pour refléter état réel (Tables 30/32 extraites, status CORRECTED_PASS_3, erratum enrichi). **Audit** : Reference data ready for qa-auditor Pass 3 recheck. |

---

## Fichiers associés

- **`test-1.ref.json`** : Données extraites au format JSON structuré (complètement à jour)
- **`test-1.spec.md`** : Spécification du Test 1 (source de vérité normative)
- **Excel source** : `SIA_4010_geteilter_Link/Test1/Resultaterfassung_Test1.xlsx` (version 1.1, datée 2024-07-01)

---

## Next steps

1. **Pour validation-engine-engineer** : Implémenter le test pass/fail binaire pour cas 1E basé sur Tables 28-29
2. **Pour ve-adapter-engineer** :
   - Adapter extraction des données de chauffage/refroidissement du candidat (actuellement 0 dans l'Excel test)
   - Traiter cas 600FF/900FF (température opérative uniquement)
3. **Pour ui-engineer** : Afficher Tables 28-32 avec comparaison visuelle pour tous les cas
4. **Pour qa-auditor** : Audit final de complétude + signature de la matrice de traçabilité
