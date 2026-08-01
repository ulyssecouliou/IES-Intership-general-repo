# Spec — Grandeur « température opérative » des Tables 30 / 32 (Test SIA 4010 n° 1)

> Statut : **TRANCHÉ SOUS CONDITION** (une vérification bloquante nommée en §8).
> Auteur : `norm-analyst`. Date : 2026-07-31.
> Convention : `VÉRIFIÉ` = lu mot pour mot à l'emplacement cité / `INFÉRÉ` = déduction
> explicite, marquée / `NON VÉRIFIÉ` = source absente ou illisible dans cet environnement.

---

## 1. La question

Parmi les six définitions de température concurrentes exposées au niveau zone par le
fichier `.aps` IESVE, **laquelle est la grandeur « operative Temperatur » exigée par la
spécification SIA 4010 Test 1 pour la Table 30 (moyennes mensuelles) et la Table 32
(max / min / moyenne annuels des cas 600FF et 900FF) ?**

---

## 2. Verdict

### 2.1 Sur la grandeur normative — **TRANCHÉ**, confiance **ÉLEVÉE**

La grandeur des Tables 30, 32 (et 34) est la **température OPÉRATIVE**, et **non** la
température d'air. La spécification SIA l'écrit littéralement, et elle **distingue
explicitement** les deux dans la même page : elle demande de livrer les **deux** séries
horaires, puis ne construit les tables 30/32/34 que sur l'**opérative**.

→ **Exclus** : `Air temperature` (#6), `Mean radiant temperature` (#5).
→ **Exclu** : `Environmental temperature` (#4) — voir §5.3 (INFÉRÉ).

### 2.2 Sur la variable IESVE — **TRANCHÉ SOUS CONDITION**, confiance **MOYENNE-HAUTE**

**Variable à lier, Table 30 ET Table 32 (et Table 34) :**

| Champ | Valeur exacte |
|---|---|
| `aps_varname` | **`Comfort temperature`** |
| `display_name` (VistaPro) | **`Dry resultant temperature`** |
| `model_level` | **`z`** (zone) |
| `metric_unit` | **`°C`** |
| `metric_divisor` / `metric_offset` | **1.0 / 0.0** |

Une seule et même variable pour les deux tables : la Table 30 et la Table 32 sont deux
agrégations différentes de **la même série horaire** (spec Test 1, points 3 et 7 —
§4.1). L'agrégation, elle, diffère : voir §6.

**Condition bloquante** : le contrôle α = 0.5 de §8.1 doit passer. Tant qu'il n'a pas été
exécuté sur un `.aps` réel, la liaison reste **provisoire**.

---

## 3. Preuves — ce que dit la spécification SIA (VÉRIFIÉ)

Source : `SIA_4010_geteilter_Link\Test1\Spezifikation_Test1.pdf`, extraction texte relue
à `…\scratchpad\norme\spec_test1.txt` (123 lignes, lue intégralement).
*(les tréma sont restitués ; l'extraction les rend en `?`)*

| Ligne | Citation mot pour mot | Portée |
|---|---|---|
| 72-73 | « Jahresdatensätze, zu übertragen in die Auswertungsdatei **Resultaterfassung_Test1.xlsx**, für » | en-tête des livrables |
| **76** | « 2) Alle Fälle ausser 1E: **Stündliche Raumluft- und operative Temperatur** » | **les DEUX séries horaires sont livrées, donc distinctes** |
| **82** | « 3) **monatliche Mittelwerte der operativen Temperatur** » | **→ Table 30** |
| **90-91** | « 7) **stündliche max., min. und mittlere operative Temperatur pro Jahr**, 600FF, 900FF » | **→ Table 32** |
| 92-93 | « 8) stündliche Mittelwerte der operativen Temperatur, 4. Januar, 600FF, 900FF » | → Table 34 |

**Conséquence directe** : la spec exige la température d'air *aussi*, mais **aucune** des
sorties dérivées 3/7/8 n'est construite sur elle. Lier `Air temperature` aux Tables 30/32
contredirait le texte. C'est le point décisif, et il ne dépend d'aucune interprétation.

**Ce que la spec ne dit PAS** : elle ne **définit pas** la température opérative (pas de
formule, pas de pondération, pas de renvoi d'article). C'est l'origine réelle de
l'ambiguïté. Voir §7.

---

## 4. Preuves — ASHRAE 140:2023 (VÉRIFIÉ) : la source amont dit l'inverse, et c'est important

Source : `ASHRAE 140_2023_D_86892.pdf`, extraction texte
`C:\Users\ulysse.couliou\.claude\jobs\d1486f24\tmp\ashrae140.txt` (27 379 lignes).

### 4.1 ASHRAE 140 impose la température d'AIR pour les cas en flottement libre

- **Définition, l. 1080-1081** : « *hourly free-floating zone air temperature: zone air
  temperature for a given hour during which heating and cooling equipment is OFF or for
  an unconditioned zone.* »
- **§7.3.6.1 à 7.3.6.3, l. 5966-5970** : « *Annual mean **zone air temperature** (°C)* » /
  « *Annual hourly integrated minimum **zone air temperature** (°C)…* » /
  « *Annual hourly integrated maximum **zone air temperature** (°C)…* »
- **Note informative, l. 5972-5975 (identique l. 4829-4835)** : « *the free-float zone air
  temperature is for the **zone air only, assuming well-mixed air with no radiant
  effects** (i.e., equivalent to what would be obtained from an aspirated temperature
  sensor perfectly shielded from solar and infrared radiation).* »
- **Table 7-47, l. 6001-6002** : sortie horaire du 1er février pour 600FF/900FF =
  « *Hourly integrated free-float **zone air temperature** (°C)* ».

### 4.2 Le mot « operative » n'existe pas dans ASHRAE 140:2023

Recherches exhaustives sur les 27 379 lignes : `operative` → **0 occurrence** ;
`operative temperature` → **0** ; `mean radiant` → **0** ; `radiant temperature` → **0**.
(`radiant` n'apparaît que pour l'émittance IR, l'absorptance solaire, la « Radiant Time
Series » et les notes « no radiant effects ».)

### 4.3 Conséquence normative — à ne pas manquer

**SIA 4010 Test 1 DÉVIE délibérément d'ASHRAE 140 sur cette sortie.** ASHRAE demande
l'air ; SIA demande l'opérative (et collecte l'air en plus). **ASHRAE 140 ne peut donc
PAS être invoqué pour justifier de lier `Air temperature` aux Tables 30/32** — c'est
précisément l'erreur « fausse mais plausible » que la question cherchait à éviter.

### 4.4 Point adjacent résolu au passage : la température de RÉGULATION, elle, est l'air

- **§7.2.1.13 a/b, l. 3395-3396** : « *a. 100% convective air system. b. **The thermostat
  senses only the air temperature.*** »
- **Note informative §7.2.1.13.1.1, l. 3410** : « *"Temperature" refers to conditioned-zone
  air temperature.* »

Il n'y a donc **aucune contradiction** : on **régule sur l'air** (20 / 27 °C) et on
**rapporte l'opérative**. Le modèle IESVE sondé (§5.2) fait exactement cela — c'est un
indice de conformité, pas une preuve.

---

## 5. Preuves — côté programmes de référence et côté IESVE

### 5.1 Anwenderberichte : aucune preuve d'usage (VÉRIFIÉ, résultat négatif)

Les **4** rapports Test 1 ont été lus intégralement :
`…\scratchpad\norme\anwender_test1_1.txt` (EXCEL SN EN ISO 52016-1, 31 l.),
`…_2.txt` (EnergyPlus 9.1.0/OpenStudio, 25 l.), `…_3.txt` (TAS EDSL, 18 l.),
`…_4.txt` (IDA ICE 5.0 Beta 23, 21 l.).

- **`operativ` → 0 occurrence dans les 4 fichiers.**
- Aucun ne nomme la variable de sortie exportée, ni sa définition.
- Le seul énoncé approchant : rapport EnergyPlus l. 18-19, « *Auch sind die **Free-Float
  Temperaturen** beim Case 600FF und 900FF bei den höheren Werten im Programmvergleich* »
  — sans définition.

→ **L'hypothèse « un programme de référence dit quelle grandeur il a exportée » est
fausse.** Cette piste est close.

### 5.2 Sonde runtime IESVE sur un cas 600 (VÉRIFIÉ, données réelles)

Source : `C:\Users\ulysse.couliou\Documents\IES Internship\IES-Intership-general-repo\references\iesve\probes\sia4010_aps_temperature_binding_evidence.json`
(zone `SIA4010_TEST_1_600_ZONE`, 48 m², 8760 pas, l. 18-68).

| Variable | `aps_varname` | min | max | somme | **moyenne annuelle** |
|---|---|---|---|---|---|
| `Air temperature` | `Room air temperature` | 19.999998 | 27.000002 | 202 936.11790 | **23.1662 °C** |
| `Dry resultant temperature` | `Comfort temperature` | 18.137789 | 32.525875 | 207 347.09587 | **23.6698 °C** |

Deux lectures immédiates :
1. L'air est **écrêté exactement** à 20.000 / 27.000 → régulation sur l'air, conforme à
   ASHRAE 140 §7.2.1.13 b (§4.4).
2. La dry resultant **flotte** (18.14 … 32.53) → ce n'est pas la grandeur régulée ; elle
   contient donc bien une composante radiante.

### 5.3 Discriminant numérique contre les valeurs de référence Table 30 (INFÉRÉ, fort)

Valeurs de référence, **Table 30, cas 600, ligne annuelle (ligne 70)** —
`refs\reference-data\test-1.ref.json` l. 5199-5223 :

| Programme | annuel [°C] | cellule |
|---|---|---|
| Daten Norm EN ISO 52016-1 | 23.3083 | C70 |
| IDA ICE 5.0 β23 | 23.9159 | D70 |
| EXCEL SIA 380/2 | 23.2630 | E70 |
| EnergyPlus 9.1.0 | 23.6425 | F70 |
| EDSL-Tas 9.5.2 | 23.9188 | G70 |
| — bande — | **[23.2630 ; 23.9188]** | |
| — moyenne des 5 — | **23.6097** | |

Confrontation avec la sonde IESVE (§5.2) :

| Candidat IESVE | moyenne annuelle | position |
|---|---|---|
| **`Dry resultant temperature`** | **23.6698** | **DANS la bande**, à **+0.060 K** de la moyenne des 5 programmes |
| `Air temperature` | 23.1662 | **HORS bande**, **−0.097 K sous le minimum** |

→ Corroboration nette du verdict §2. **Ce n'est pas une preuve** : voir les
contre-arguments §7.

### 5.4 Antériorité dans le dépôt (contexte, non probant)

- `ve_adapter\test1_adapter.py` l. 835-843 lie déjà `operative_temperature` →
  `Comfort temperature` / `Dry resultant temperature`, mais en signalant lui-même
  l'incohérence de version de sa justification.
- `…\IES-Intership-general-repo\config\sia4010_aps_bindings_ve_runtime.json` l. 75-84 :
  même liaison, `"status": "RUNTIME_METADATA_CONFIRMED"`, justification sémantique
  « *IES documents dry resultant temperature as operative temperature in still-air
  conditions* », `"source_reference": "https://help.iesve.com/ve2025/hot_water_radiator_control_.htm"`.
  → **Source web VE2025, absente de `/refs` (qui est VE2023) : NON VÉRIFIÉE par moi.**
  `AUDIT.md` l. 358-369 avait déjà abaissé le statut de cette liaison pour ce motif.
  Le présent document **ne la valide pas par ce chemin** ; il la reprend pour d'autres
  raisons (§3, §4, §5.3) et la conditionne (§8.1).

---

## 6. Table 30 ≠ Table 32 : ce ne sont pas la même moyenne (INFÉRÉ, fort — impact code)

Découvert en confrontant les deux tables du même classeur :

| Programme | Table 30, annuel (600FF) | Table 32, « Average » (600FF) | écart |
|---|---|---|---|
| ISO 52016-1 | 25.875 (AI70) | 25.9 (C107) | +0.025 |
| IDA ICE | 27.21592 (AJ70) | 27.25330 (D107) | +0.0374 |
| EXCEL SIA 380/2 | 26.00222 (AK70) | 26.04944 (E107) | +0.0472 |
| EnergyPlus | 26.14802 (AL70) | 26.18676 (F107) | +0.0388 |
| EDSL-Tas | 25.21285 (AM70) | 25.25604 (G107) | +0.0431 |

Sources : `refs\reference-data\test-1.ref.json` l. 7031-7055 ;
`refs\reference-data\table_32_corrected.json` l. 86-119.

**Inférence** :
- **Table 30, ligne « annuel » = moyenne NON pondérée des 12 moyennes mensuelles.**
  Reconstruction exacte sur la colonne ISO (publiée à 1 décimale) :
  23.3083333…× 12 = **279.7** (cas 600) ; 25.875 × 12 = **310.5** (600FF) ;
  25.9083333…× 12 = **310.9** (900FF). Trois fois un multiple exact de 0.1 → la cellule
  est bien un `AVERAGE` de 12 valeurs à 1 décimale.
- **Table 32, « Average » = moyenne pondérée par les heures (8760 valeurs).**
  L'écart est systématiquement **positif et de l'ordre de 0.04 K** : signature attendue
  du repondérage des mois à 31 jours (juillet, août) contre février (28 j).

**Conséquence code — anomalie à corriger** :
`ve_adapter\test1_adapter.py` l. 962 calcule `moyenne_annuelle = sum(serie)/len(serie)`
(**pondérée heures**) et la place en l. 1006 dans `monthly['annual']`, c.-à-d. face à la
**Table 30**. Or Table 30 attend la moyenne des 12 mensuelles. Biais latent ≈ **0.04 K**,
invisible à l'œil, systématique. La ligne 1016 (Table 32) est en revanche correcte.
→ **INFÉRÉ, à confirmer par la formule Excel** (§8.2) avant toute correction.

---

## 7. Contre-arguments à ma propre conclusion

1. **La spec SIA ne définit jamais « operative Temperatur ».** Ni la spec Test 1
   (`spec_test1.txt`, lue intégralement), ni SIA 4010:2023 (texte français intégral :
   `…\scratchpad\norme\sia_4010_2023.txt`, **0 occurrence de « température »**), ni les
   Anwenderberichte. Le verdict §2.2 repose donc sur une définition **externe** que je
   n'ai pas pu lire (§8.1). C'est la faiblesse principale.
2. **Chaque programme de référence a pu utiliser SA propre définition d'opérative.**
   Rien dans le corpus ne l'exclut. La bande de la Table 30 pourrait alors mélanger
   plusieurs pondérations. Coller à cette bande ne prouve donc pas l'identité de
   définition.
3. **Le discriminant numérique §5.3 est faible en marge.** Écart Ta↔Tdr = 0.50 K contre
   une largeur de bande inter-programmes de 0.66 K. Un modèle IESVE mal construit
   pourrait déplacer les deux candidats et inverser la conclusion.
4. **La sonde §5.2 porte sur un `.aps` non qualifié.** Projet `"test"`, fichier
   `"test.aps"` ; rien ne prouve que la géométrie/les constructions respectent la spec
   (réserve déjà consignée `AUDIT.md` l. 361-363, et §8 pt 2-4 de
   `traceability\test-1.spec.md` : constructions, vitrage, infiltration toujours `[REQUIS]`).
5. **`Dry resultant temperature` n'est pas une constante physique : sa pondération dépend
   d'un réglage de modèle** (vitesse d'air du template). Un changement silencieux de ce
   réglage change la valeur sans changer le nom de la variable. D'où le garde-fou §8.1,
   qui n'est pas optionnel.
6. **Argument contraire sérieux en faveur de l'air** : la cellule d'essai vient
   d'ASHRAE 140, qui exige explicitement l'air et interdit les effets radiants (§4.1).
   Si l'on démontrait que le classeur SIA alimente en fait les Tables 30/32 depuis la
   colonne « Raumlufttemperatur », l'étiquette « operativ » serait un abus de langage et
   le verdict s'inverserait. **Ce contrôle est nommé en §8.2 ; il n'a pas été fait.**

---

## 8. Ce qui reste NON VÉRIFIÉ — et comment le lever

### 8.1 BLOQUANT — définition de la pondération, et contrôle empirique associé

**Source manquante n° 1 : `refs\SIA-380-2-2022.pdf`.** Le PDF est présent mais
**illisible dans cette session** : le rendu page échoue (`pdftoppm` absent) et les flux
texte sont compressés (`Grep` → 0 occurrence). C'est la norme mère (SIA 4010 est sa
« Wegleitung ») : c'est là que doit se trouver la définition de θ_op / température
opérative. **Action : extraction `pdftotext` par l'orchestrateur, puis relecture.**

**Source manquante n° 2 : EN ISO 52016-1:2017** — totalement absente de `/refs`, alors
que c'est la source formellement citée par la spec Test 1 pour la cellule d'essai.

**Source manquante n° 3 : documentation IESVE des 6 grandeurs.** `refs\VEScripts-API-VE2023.pdf`
(extrait relu : `…\jobs\d1486f24\tmp\vescripts_api.txt`) ne contient **aucune** occurrence
de `operative`, `dry resultant`, `environmental temp`, `mean radiant`, `comfort temp`.
Les formules exactes des 6 variables **ne sont pas vérifiables dans `/refs`.**

**Contrôle empirique qui remplace ces sources en attendant** — il ne suppose aucune
formule : sur un `.aps` du cas 600FF, extraire les 6 séries horaires (8760 valeurs) et,
pour chaque candidat `C`, résoudre α dans `C(h) = α·Ta(h) + (1−α)·Tmr(h)` (moindres
carrés sur les 8760 points, plus résidu max).

| α mesuré | Lecture |
|---|---|
| **α = 0.500 ± 0.001, résidu max < 0.01 K** | le candidat est la moyenne arithmétique air/radiant → **c'est celui à lier** |
| α ≠ 0.5 mais résidu faible | pondération non-50/50 → **escalade**, ne pas lier avant d'avoir lu SIA 380/2 |
| résidu élevé | le candidat n'est pas une combinaison linéaire de Ta et Tmr → **exclure** |

Attente (INFÉRÉ, à confirmer) : `Dry resultant temperature`,
`Operative temperature (ASHRAE)` et `Operative temperature (TM 52/CIBSE)` devraient
**tous trois donner α = 0.5 en air calme** et être alors numériquement interchangeables ;
`Environmental temperature` devrait donner α ≈ 1/3 (méthode d'admittance CIBSE, pas une
température opérative). **Ces valeurs attendues ne sont PAS sourcées** : elles sont
l'objet du test, pas son hypothèse.

**Garde-fou permanent à implanter dans `ve_adapter/`** (pas seulement une fois) : à chaque
extraction, vérifier `|Tdr(h) − 0.5·(Ta(h)+Tmr(h))| ≤ 0.01 K` sur les 8760 heures et
**refuser d'écrire le JSON candidat** si le contrôle échoue, avec un message explicite.
Motif : un changement de vitesse d'air dans le template produirait sinon un résultat faux
et parfaitement plausible.

### 8.2 BLOQUANT pour la traçabilité — lire le classeur SIA lui-même

`SIA_4010_geteilter_Link\Test1\Resultaterfassung_Test1.xlsx` est **présent** mais je ne
peux pas ouvrir un `.xlsx`. À extraire (openpyxl, `data_only=False`), feuille
« Zusammenfassung Testfälle » :

1. **Libellés allemands exacts** des lignes 53 (Table 30) et 104 (Table 32) → disent-ils
   « operative Temperatur » ou « Raumlufttemperatur » ? *(lève le contre-argument §7.6)*
2. **Formules** de `C70`, `AI70`, `AQ70` (annuel Table 30) et `C107`, `K107` (Average
   Table 32) → confirment ou infirment l'inférence §6.
3. **Colonnes AZ-BG** signalées comme « données ASHRAE 140 » par
   `refs\reference-data\test-1.ref.md` l. 205/211 : quel en-tête, quelles valeurs ? Si le
   classeur juxtapose des températures d'air ASHRAE 140 et ses propres colonnes
   « operativ », leur écart chiffre directement la déviation §4.3.
4. Sur les feuilles de saisie par programme : les colonnes d'entrée horaires
   « Raumlufttemperatur » et « operative Temperatur » sont-elles deux colonnes
   **distinctes** et **différentes** en valeurs ? Si elles sont identiques pour un
   programme donné, ce programme a livré la même série deux fois → à documenter.

### 8.3 Non bloquant, à consigner

- Le contrôle α n'a **jamais** été exécuté : la liaison actuelle du dépôt (§5.4) repose
  sur une page d'aide VE2025 non versionnée. À ne pas confondre avec une vérification.
- La sonde `.aps` disponible ne couvre que **2** des 6 variables (air + dry resultant) et
  un cas **600**, pas **600FF**. Une nouvelle sonde couvrant les 6 variables sur 600FF est
  nécessaire pour §8.1.

---

## 9. Récapitulatif de la liaison à implanter

```
Table 30 (moyennes mensuelles, cas 600/640/900/940/600FF/900FF)
Table 32 (max/min/moyenne annuels, cas 600FF/900FF)
Table 34 (profil horaire du 4 janvier, 600FF/900FF)
    ← une seule série horaire zone, 8760 valeurs :
        aps_varname   = "Comfort temperature"
        display_name  = "Dry resultant temperature"
        model_level   = "z"
        unité         = "°C"   (divisor 1.0, offset 0.0)
    ← sous réserve du contrôle α = 0.5 (§8.1), sinon ESCALADE.

Agrégations (INFÉRÉ §6, à confirmer §8.2) :
    Table 30 mensuel  = moyenne des heures du mois
    Table 30 annuel   = moyenne NON pondérée des 12 moyennes mensuelles   ← ≠ code actuel
    Table 32 max/min  = max/min des 8760 valeurs horaires
    Table 32 average  = moyenne des 8760 valeurs horaires                 ← code actuel OK

À NE PAS lier : "Air temperature", "Mean radiant temperature",
                "Environmental temperature".
Acceptables SEULEMENT si α = 0.5 mesuré, et alors équivalentes :
                "Operative temperature (ASHRAE)", "Operative temperature (TM 52/CIBSE)".
```

**Aucune tolérance n'est associée à ces tables** : les cas 600/640/900/940/600FF/900FF
n'ont **aucun critère de déviation** (`spec_test1.txt` l. 96-100, « *Es gibt dafür kein
Abweichungskriterium* »). Le choix de la variable n'en est pas moins critique : c'est la
comparaison visuelle publiée qui serait fausse.

---

## 10. Citations — emplacements exacts

| Affirmation | Emplacement |
|---|---|
| SIA exige l'opérative pour Tables 30/32/34, distincte de l'air | `…\scratchpad\norme\spec_test1.txt` l. 76, 82, 90-93 (PDF : `SIA_4010_geteilter_Link\Test1\Spezifikation_Test1.pdf`) |
| Aucun critère de déviation pour 600…900FF | `spec_test1.txt` l. 96-100 |
| ASHRAE 140 : sortie FF = zone air temperature | `…\jobs\d1486f24\tmp\ashrae140.txt` l. 1080-1081, 5966-5970, 5972-5975, 4829-4835, 6001-6004 |
| ASHRAE 140 : thermostat sur l'air | idem, l. 3395-3396, 3410 |
| ASHRAE 140 : 0 occurrence de « operative » / « mean radiant » | recherche exhaustive sur les 27 379 lignes du même fichier |
| Anwenderberichte : 0 occurrence de « operativ » | `…\scratchpad\norme\anwender_test1_1..4.txt` (lus intégralement) |
| SIA 4010:2023 (fr) : 0 occurrence de « température » | `…\scratchpad\norme\sia_4010_2023.txt` |
| Sonde IESVE cas 600 (2 variables, 8760 pas) | `…\IES-Intership-general-repo\references\iesve\probes\sia4010_aps_temperature_binding_evidence.json` l. 18-68 ; qualification sémantique l. 70-75 |
| Liaison préexistante + justification VE2025 | `…\IES-Intership-general-repo\config\sia4010_aps_bindings_ve_runtime.json` l. 75-84 ; `ve_adapter\test1_adapter.py` l. 835-843 ; `AUDIT.md` l. 358-369 |
| Table 30 cas 600 annuel (5 programmes) | `refs\reference-data\test-1.ref.json` l. 5199-5223 |
| Table 30 cas 600FF/900FF annuel | idem l. 7031-7055 et l. 7489-7513 |
| Table 32 cas 600FF/900FF | `refs\reference-data\table_32_corrected.json` l. 86-119 et l. 206-239 |
| Colonnes ASHRAE 140 AZ-BG signalées dans le classeur | `refs\reference-data\test-1.ref.md` l. 205, 211 (**non vérifié par moi**) |
| Agrégation annuelle du code | `ve_adapter\test1_adapter.py` l. 950-963 (l. 962), l. 1004-1018 |
| VEScripts API VE2023 : aucune des 6 grandeurs documentée | `…\jobs\d1486f24\tmp\vescripts_api.txt` (0 occurrence) |
| SIA 380/2:2022 illisible dans cette session | `refs\SIA-380-2-2022.pdf` — rendu impossible (`pdftoppm` absent), Grep → 0 |
| EN ISO 52016-1:2017 | **absente de `/refs`** |

---

## 11. Ce qui me ferait changer d'avis

1. SIA 380/2:2022 (ou EN ISO 52016-1:2017) définissant θ_op avec une pondération **≠
   50/50** → il faudrait alors construire une grandeur dérivée depuis `Room air
   temperature` + `Room radiant temperature`, et **aucune** variable IESVE native ne
   conviendrait.
2. Le classeur `Resultaterfassung_Test1.xlsx` montrant que les Tables 30/32 sont
   alimentées par la colonne d'air → verdict inversé vers `Air temperature`.
3. Un contrôle α (§8.1) donnant α ≠ 0.5 pour `Dry resultant temperature` sur le modèle
   Test 1 → la liaison tomberait au profit de la variable qui donne α = 0.5, ou d'une
   dérivation explicite.
4. Une note SIA (rectificatif `www.sia.ch/rectificatif`, ou FAQ SIA 4010) définissant la
   grandeur → prime sur tout ce qui précède.

---

## 12. Journal

| Date | Auteur | Changement |
|---|---|---|
| 2026-07-31 | norm-analyst | Création. Verdict : opérative confirmée (VÉRIFIÉ) ; liaison `Comfort temperature` / `Dry resultant temperature` **sous condition** du contrôle α = 0.5. Découvertes annexes : ASHRAE 140 exige l'air (déviation SIA assumée) ; Table 30 annuel ≠ Table 32 average (biais 0.04 K dans le code actuel). |
