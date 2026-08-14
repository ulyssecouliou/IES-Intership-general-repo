# Spécification normative — Génération de froid et de chaleur (SIA 380/2:2022 Tableaux 5-9)

> Rôle : `norm-analyst`. Date : 2026-08-14.
> Portée : règles de sélection machine-lisibles pour la famille « génération froid/chaud »
> du projet de référence SIA 380/2:2022, à destination de `reference-data-engineer`
> (figer les tables) et `validation-engine-engineer` (câbler la substitution).
> Ce document ne modifie aucun code de production.

> **MISE À JOUR 2026-08-14 — plusieurs `[TO VERIFY]` ci-dessous ont été RÉSOLUS**
> par lecture directe du PDF lors de l'audit indépendant. Source de résolution
> faisant foi : `traceability/audit-reference-project-2026-08.md`. Résolus : la
> borne 150 kW (`# 7.2.5.4` « < 150 kW » air / « à partir de 150 kW » eau),
> l'inclusivité des bandes, le **Tableau 7 entier** (grandeur EER+ pleine charge
> ET charge 50 %, non comparable au `eer`/`seer` VE), le **Tableau 8 = LIMITE
> seule** (pas de colonne cible), le **Tableau 9 = limite ET cible**, et les
> articles `# 7.2.5.8`/`# 7.2.5.9`. Restent ouverts : l'équivalence
> `seer`/`scop`(VE) ↔ SN EN 14825 (norme EN absente) et le choix de méthode
> (Pathway A vs B) — le code implémente la substitution (Pathway B) avec ces
> deux points marqués `[TO VERIFY]`.

---

## 0. Avertissement de traçabilité (IMPORTANT — à lire en premier)

**Je n'ai pas pu ouvrir `refs/SIA-380-2-2022.pdf` dans cette session.** Contrairement à
l'énoncé de la tâche, `Bash`/PyMuPDF est désactivé, `poppler` (rendu PDF) est absent, et
`Grep` ne peut pas décompresser les flux `FlateDecode` du PDF. **Aucune extraction PDF
directe n'a donc été réalisée par moi.**

Ce que j'ai fait à la place :
1. J'ai repris les valeurs `[TRACÉ PDF]` fournies par l'agent appelant.
2. Je les ai **recoupées avec une extraction antérieure déjà présente dans le dépôt** :
   `docs/project/SIA_3802_4010_PDF_TRACEABILITY.md` §7 (qui cite « SIA 380/2:2022 FR,
   tableaux 5-9 pages PDF 38-39 et tableau 2 page PDF 35 »).

Conséquences sur le niveau de preuve, marqué pour chaque valeur :

| Marqueur | Sens |
|---|---|
| **[TRACÉ+CORROBORÉ]** | Valeur fournie par l'agent appelant **et** identique dans la trace repo antérieure → double source concordante |
| **[TRACÉ-1SRC]** | Valeur d'une seule source (agent appelant OU repo), non recoupée |
| **[TO VERIFY]** | Non extractible ici, ou point non explicite → question précise posée |
| **[INTERPRÉTATION]** | Déduction logique de ma part, distincte de l'exigence normative |

Aucune valeur ci-dessous n'a été inventée ni interpolée. **Une relecture PDF réelle
(page 35, 38, 39) reste requise pour lever le statut « je n'ai pas ouvert le PDF ».**

---

## 1. Règle de sélection du FROID

### 1.1 Type de machine de référence (source : Tableau 2, §7.2.5.4 / §7.2.5.5)

| Puissance de froid `cooling_capacity_kw` | Machine de référence | Article | Table(s) d'efficacité | Preuve |
|---|---|---|---|---|
| `< 150 kW` | Machine frigorifique à compresseur, **à AIR** | `# SIA 380/2:2022 7.2.5.4` | **Tableau 5** | **[TRACÉ-1SRC]** (agent) |
| `≥ 150 kW` | Compresseur **à EAU avec post-refroidisseur à sec** | `# SIA 380/2:2022 7.2.5.5` | **Tableaux 6 et 7** | **[TRACÉ-1SRC]** (agent) |

**Borne exacte au seuil 150 kW** : l'agent appelant a relevé « `< 150 kW` → air ;
`≥ 150 kW` → eau », donc **150 kW exactement → EAU**. Je n'ai pas pu confirmer l'inégalité
sur le PDF. → **[TO VERIFY]** : le Tableau 2 écrit-il bien « < 150 / ≥ 150 » (et non
« ≤ 150 / > 150 ») ? Point load-bearing pour un projet dont la puissance vaut exactement 150 kW.

### 1.2 Correspondance bande ↔ intervalle de puissance

Notation des tables (`≤12 / >12–50 / >50–150 / >150–450 / >450–1000 / >1000`) → intervalles
**ouverts à gauche, fermés à droite** :

| Bande | Intervalle `P` [kW] | Preuve |
|---|---|---|
| B1 | `P ≤ 12` | [TRACÉ+CORROBORÉ] |
| B2 | `12 < P ≤ 50` | [TRACÉ+CORROBORÉ] |
| B3 | `50 < P ≤ 150` | [TRACÉ+CORROBORÉ] |
| B4 | `150 < P ≤ 450` | [TRACÉ+CORROBORÉ] |
| B5 | `450 < P ≤ 1000` | [TRACÉ+CORROBORÉ] |
| B6 | `P > 1000` | [TRACÉ+CORROBORÉ] |

**[INTERPRÉTATION]** L'inclusivité (fermé à droite `≤`, ouvert à gauche `>`) est déduite de
la notation « >12–50 » (= `]12 ; 50]`). → **[TO VERIFY]** : confirmer sur le PDF le
traitement des valeurs rondes exactes (12, 50, 150, 450, 1000 kW), en particulier si le
seuil 150 kW de §1.1 coïncide avec la borne de bande.

**Asymétrie des domaines couverts** (relevée, non une erreur) :
- Tableau 5 (AIR) : bandes B1→B5 (**pas de bande B6 `>1000`**).
- Tableau 6 (EAU) : bandes B2→B6 (**pas de bande B1 `≤12`**).

**[INTERPRÉTATION + TO VERIFY]** Le Tableau 6 comporte des bandes B2/B3 (`<150 kW`) alors
que la règle §1.1 n'invoque l'eau qu'à `≥150 kW`. Lecture cohérente : la **sélection** du
type de machine (air vs eau) est régie par le seuil 150 kW du Tableau 2/§7.2.5.4-5 ; les
bandes basses du Tableau 6 servent d'autres contextes de la norme (ou le cas projet-eau
volontaire). Pour la construction du projet de référence, seules les bandes B4→B6 du
Tableau 6 sont atteintes via la règle `≥150 kW`. → **[TO VERIFY]** : confirmer que le
projet de référence n'utilise jamais Tableau 6 en dessous de 150 kW.

### 1.3 Rôle respectif des Tableaux 6 et 7 (`≥150 kW`)

**[TO VERIFY] — Tableau 7 NON EXTRAIT.** Le Tableau 7 (« refroidisseurs à eau avec
post-refroidissement à sec », p38-39) est **absent des deux sources** (agent appelant :
coupé ; trace repo : non extraite). Je ne peux pas le figer.
Questions précises pour la relecture PDF :
- Q7.1 : le Tableau 7 donne-t-il les EER/SEER de la **combinaison** chiller-eau +
  post-refroidisseur à sec, ou seulement le **déclassement** dû au post-refroidissement ?
- Q7.2 : au `≥150 kW`, la valeur de substitution est-elle prise dans le Tableau 6, le
  Tableau 7, ou une composition des deux (§7.2.5.5) ?
- Q7.3 : bandes de puissance du Tableau 7 (identiques au Tableau 6 : B2→B6 ? ou B4→B6 ?).

---

## 2. Règle de sélection du CHAUD

### 2.1 Types DIFFÉRENTS pour limite et cible (source : Tableau 2, §7.2.5.8 / §7.2.5.9)

| Niveau | Système de référence | Table | Preuve |
|---|---|---|---|
| **Réf. LIMITE** | PAC **air-eau** | **Tableau 8** | **[TRACÉ+CORROBORÉ]** |
| **Réf. CIBLE** | PAC **sonde géothermique (saumure-eau)** | **Tableau 9** | **[TRACÉ+CORROBORÉ]** |

**Confirmé** : limite et cible reposent sur des **types de générateur différents** (air-eau
vs saumure-eau) **et des tables différentes** (8 vs 9). Ce n'est donc pas la même machine
lue à deux colonnes : ce sont deux machines de référence distinctes. Grandeur comparée :
`heating_capacity_kw` détermine la bande dans chaque table.

**[TO VERIFY]** Articles exacts : l'énoncé situe la génération de chaleur en §7.2.5.8/9
d'après la plage §7.2.5.4-9. Je n'ai pas confirmé le numéro d'article précis attaché aux
Tableaux 8 et 9 (§7.2.5.8 vs §7.2.5.9) → confirmer sur PDF p39.

### 2.2 Bandes de puissance chauffage

| Table | Bandes présentes | Preuve |
|---|---|---|
| Tableau 8 (air-eau, limite) | B1 `≤12`, B2 `12–50`, B3 `50–150` (**s'arrête à 150 kW**) | [TRACÉ+CORROBORÉ] |
| Tableau 9 (saumure-eau, cible) | B2 `12–50`, B3 `50–150`, B4 `150–450`, B5 `450–1000`, B6 `>1000` | [TRACÉ+CORROBORÉ] |

**[TO VERIFY] — asymétrie de domaine limite/cible.** Le Tableau 8 (limite) s'arrête à
150 kW ; le Tableau 9 (cible) couvre jusqu'à `>1000 kW` mais **ne commence qu'à 12 kW**.
Deux zones sans correspondance directe :
- `P > 150 kW` : pas de valeur LIMITE air-eau tabulée → comment est fixée la limite au-delà
  de 150 kW ? (renvoi à §7.2.5.7 calcul détaillé ? autre table ?)
- `P ≤ 12 kW` : pas de valeur CIBLE saumure-eau tabulée → quelle cible sous 12 kW ?
Ces deux points doivent être tranchés par relecture PDF avant câblage.

---

## 3. Sens de la comparaison

**Confirmé : la valeur de référence est un SEUIL MINIMAL** — le générateur projet est
conforme si son efficacité est **`≥`** la valeur de table (EER, SEER et SCOP sont des
coefficients d'efficacité : « plus haut = meilleur »).

- Base : les colonnes sont nommées « valeur limite » (= plancher à ne pas franchir vers le
  bas) et « valeur cible » (objectif plus exigeant, donc plus élevé). Cohérent avec les
  chiffres : cible > limite dans chaque bande (ex. air B1 : EER 3,10 cible > 2,90 limite).
- **[INTERPRÉTATION]** Le sens physique (COP/EER/SEER/SCOP croissant = plus efficace) est
  non ambigu ; la direction `projet ≥ référence` en découle.

**[TO VERIFY] — méthode de comparaison (Pathway A vs Pathway B).** Deux lectures possibles,
non tranchées ici faute d'accès au texte de §7.2.5 :
- Pathway A (comparaison directe) : `EER_projet ≥ EER_limite` et `SEER_projet ≥ SEER_limite`.
- Pathway B (projet de référence) : on **construit** une machine de référence à laquelle on
  **assigne** la valeur de table, puis on compare les besoins énergétiques simulés.
La grandeur figée est la même (valeur de table) ; la mécanique de substitution diffère.
`validation-engine-engineer` doit savoir laquelle avant câblage. → confirmer sur PDF.

---

## 4. Grandeur exacte comparée : EER pleine charge vs SEER

### 4.1 Les tables donnent DEUX grandeurs

Pour le froid, chaque bande fournit **à la fois** :
- **EER pleine charge** (point nominal),
- **SEER** saisonnier, référencé **`SN EN 14825`** (mention relevée par l'agent).

→ **[TO VERIFY]** Laquelle est la grandeur de substitution du projet de référence — EER
seul, SEER seul, ou **les deux simultanément** ? Les deux colonnes existent, donc a priori
**les deux contraintes s'appliquent** ; le texte de §7.2.5.4-5 doit le confirmer. Le SEER
(saisonnier) est l'indice pertinent pour l'énergie annuelle ; l'EER pleine charge est le
point de dimensionnement.

### 4.2 Correspondance SEER (SN EN 14825) ↔ `seer` extrait de VE — NON PROUVÉE

`swiss_sia/model_analyzer.py` (l.681-682, l.698-699) extrait :
- `seer = cooling.get("SEER")` (VE `VEApacheSystem.cooling()`, [PDF VEScripts p.182]) ;
- `sseer = cooling.get("SSEER")` (efficacité saisonnière **système**, auxiliaires inclus).

→ **[TO VERIFY]** L'indice `SEER` renvoyé par l'API IESVE est-il **défini/mesuré selon
`SN EN 14825`** (mêmes conditions aux limites, mêmes points de charge partielle, même
pondération climatique) ? **Rien ne le prouve** :
- Le PDF `SN EN 14825` **n'est pas présent dans `/refs`** → je ne peux ni citer ni vérifier
  la définition normative du SEER. **Norme EN absente signalée.**
- Le contrat d'extraction adaptateur (`traceability/sia380-2-adapter-extraction-contract.spec.md`
  §4) marque `SEER` comme `[EXPOSÉ]` mais **sans preuve de conformité EN 14825**.
Tant que non prouvé : **ne pas assimiler `seer` (VE) à SEER (SN EN 14825)**.

→ **[TO VERIFY] secondaire** : la comparaison doit-elle porter sur `seer` (générateur) ou
`sseer` (système, auxiliaires §7.2.5.6 inclus) ? Le SIA 380/2 intègre des auxiliaires de
post-refroidissement (§3 ci-dessous), ce qui pourrait pointer vers un indice « système ».

---

## 5. Tables 5-9 machine-lisibles

> Toutes les valeurs froid ci-dessous sont **[TRACÉ+CORROBORÉ]** (agent appelant ET
> `docs/project/SIA_3802_4010_PDF_TRACEABILITY.md` §7, l.122-151, concordantes).
> Locator normatif : `# SIA 380/2:2022 Tableau N`, pages PDF 38-39 (froid/chaud),
> Tableau 2 page PDF 35 (sélection). **Pages non re-vérifiées par moi (voir §0).**
> Unité EER/SEER/SCOP = kW/kW (sans dimension). Séparateur décimal normalisé au point.

### 5.1 Tableau 5 — Froid, refroidisseurs à AIR (`# SIA 380/2:2022 Tableau 5`, p38)

| band_id | p_min_kw | p_max_kw | eer_full_load_limit | seer_limit | eer_full_load_target | seer_target |
|---|---|---|---|---|---|---|
| B1 | 0 | 12 | 2.90 | 3.80 | 3.10 | 4.20 |
| B2 | 12 | 50 | 3.00 | 3.90 | 3.15 | 4.35 |
| B3 | 50 | 150 | 3.10 | 4.00 | 3.20 | 4.50 |
| B4 | 150 | 450 | 3.20 | 4.20 | 3.40 | 4.80 |
| B5 | 450 | 1000 | 3.40 | 4.40 | 3.60 | 5.00 |

`p_min` exclusif, `p_max` inclusif (cf. §1.2). Sélection : type AIR ssi `cooling_capacity_kw < 150`.

### 5.2 Tableau 6 — Froid, refroidisseurs à EAU (`# SIA 380/2:2022 Tableau 6`, p38)

| band_id | p_min_kw | p_max_kw | eer_full_load_limit | seer_limit | eer_full_load_target | seer_target |
|---|---|---|---|---|---|---|
| B2 | 12 | 50 | 4.05 | 4.50 | 4.45 | 5.90 |
| B3 | 50 | 150 | 4.25 | 4.80 | 4.65 | 6.10 |
| B4 | 150 | 450 | 4.65 | 5.50 | 5.05 | 6.90 |
| B5 | 450 | 1000 | 5.05 | 6.10 | 5.50 | 7.40 |
| B6 | 1000 | null | 5.50 | 6.70 | 6.00 | 8.00 |

Sélection : type EAU ssi `cooling_capacity_kw ≥ 150` (voir aussi Tableau 7, §1.3).

### 5.3 Tableau 7 — Froid, EAU avec post-refroidissement à sec (`# SIA 380/2:2022 Tableau 7`, p38-39)

**[TO VERIFY] — NON EXTRAIT.** Absent des deux sources. Table à figer après relecture PDF.
Structure attendue (à confirmer) : mêmes colonnes EER/SEER (limite/cible) que Tableau 6,
bandes ≥ B4 (`≥150 kW`). Voir questions Q7.1-Q7.3 (§1.3).

### 5.4 Tableau 8 — Chaud, PAC air-eau — réf. LIMITE (`# SIA 380/2:2022 Tableau 8`, p39)

| band_id | p_min_kw | p_max_kw | scop_limit | scop_target |
|---|---|---|---|---|
| B1 | 0 | 12 | 3.00 | [TO VERIFY] |
| B2 | 12 | 50 | 3.10 | [TO VERIFY] |
| B3 | 50 | 150 | 3.20 | [TO VERIFY] |

SCOP selon **`SN EN 14825`** (mention relevée). Colonne « cible » : la trace repo indique
« non donné dans la table extraite » (l.144-146) → **[TO VERIFY]** : le Tableau 8 a-t-il
une colonne cible, ou la cible chaud est-elle **exclusivement** portée par le Tableau 9
(saumure-eau) conformément à §2.1 ? Lecture cohérente avec §2.1 : la cible air-eau n'existe
pas car la cible = saumure-eau. **[INTERPRÉTATION]** à confirmer.

### 5.5 Tableau 9 — Chaud, PAC saumure-eau (sonde géothermique) — réf. CIBLE (`# SIA 380/2:2022 Tableau 9`, p39)

| band_id | p_min_kw | p_max_kw | scop_limit | scop_target |
|---|---|---|---|---|
| B2 | 12 | 50 | 4.00 | 4.40 |
| B3 | 50 | 150 | 4.20 | 4.60 |
| B4 | 150 | 450 | 4.60 | 5.00 |
| B5 | 450 | 1000 | 5.00 | 5.50 |
| B6 | 1000 | null | 5.50 | 6.00 |

**[TRACÉ+CORROBORÉ]** via trace repo §7 (l.147-151), qui complète les bandes non fournies
par l'agent appelant. **[TO VERIFY]** : le Tableau 9 porte-t-il **deux** colonnes
(limite ET cible) ? La trace repo les nomme « SCOP limite / SCOP cible », ce qui suggère
que la table saumure-eau comporte elle-même une limite ET une cible — à réconcilier avec
§2.1 (où la table 9 = réf. cible). Question ouverte pour la relecture.

---

## 6. Auxiliaires et méthode (§7.2.5.6 / §7.2.5.7)

**[TRACÉ-1SRC — NON RE-VÉRIFIÉ]** (agent appelant uniquement, non recoupé, non ouvert par moi) :

- `# SIA 380/2:2022 7.2.5.6` — auxiliaires de post-refroidissement (part de l'énergie) :
  ventilateurs **3.6 %**, pompes **1.2 %**, pompe eau froide **1.5 %**.
  → **[TO VERIFY]** base de calcul exacte (% de quoi : énergie froid ? puissance ?).
- `# SIA 380/2:2022 7.2.5.7` — méthode : **Annexe A** + **`SN EN 16798-13:2017`**,
  tableaux **NA.3** et **NA.4**.
  → **Norme EN absente signalée** : `SN EN 16798-13:2017` **n'est pas dans `/refs`** →
  tableaux NA.3/NA.4 **non citables ni vérifiables** ici. À obtenir avant tout câblage
  de cette méthode.

---

## 7. Résumé pour reference-data-engineer / validation-engine-engineer

### 7.1 Règles de sélection

- **FROID** : `cooling_capacity_kw < 150` → **AIR / Tableau 5** ; `≥ 150` → **EAU avec
  post-refroidisseur à sec / Tableaux 6 (+7)**. Bandes `]p_min ; p_max]`. Type déterminé
  par le seuil 150 kW (Tableau 2/§7.2.5.4-5) ; la bande par la puissance.
- **CHAUD** : réf. **LIMITE = PAC air-eau / Tableau 8** (bandes jusqu'à 150 kW) ; réf.
  **CIBLE = PAC saumure-eau / Tableau 9** (bandes 12 kW → >1000 kW). Types et tables
  **différents** entre limite et cible — confirmé.
- **Sens** : référence = **seuil minimal** ; conforme si `efficacité_projet ≥ valeur_table`
  (EER, SEER, SCOP croissants = meilleurs) — confirmé.

### 7.2 Grandeur comparée

- Froid : les tables donnent **EER pleine charge ET SEER (SN EN 14825)** ; probablement les
  deux contraintes s'appliquent (**[TO VERIFY]** laquelle est la substitution primaire).
- **Ne pas** assimiler le `seer` extrait de VE au SEER `SN EN 14825` sans preuve
  (**[TO VERIFY]** ; `SN EN 14825` absent de `/refs`). Arbitrage `seer` vs `sseer`
  (auxiliaires) également ouvert.

### 7.3 Liste des [TO VERIFY] (questions précises)

1. Borne 150 kW froid : « < 150 / ≥ 150 » vs « ≤ 150 / > 150 » ? (§1.1)
2. Inclusivité des bornes de bande aux valeurs rondes 12/50/150/450/1000 kW. (§1.2)
3. **Tableau 7 entier non extrait** : valeurs, bandes, et rôle vs Tableau 6 au `≥150 kW`
   (Q7.1-Q7.3). (§1.3, §5.3)
4. Zone `P > 150 kW` sans limite air-eau (Tableau 8) : d'où vient la limite ? (§2.2)
5. Zone `P ≤ 12 kW` sans cible saumure-eau (Tableau 9). (§2.2)
6. Méthode de comparaison : Pathway A (valeur vs seuil) ou Pathway B (projet de
   référence construit) ? (§3)
7. Grandeur de substitution froid : EER, SEER, ou les deux ? (§4.1)
8. `seer` (VE) ≡ SEER `SN EN 14825` ? — **`SN EN 14825` absent de `/refs`**. (§4.2)
9. Comparaison sur `seer` (générateur) ou `sseer` (système + auxiliaires §7.2.5.6) ? (§4.2)
10. Tableau 8 a-t-il une colonne cible, ou la cible chaud est-elle uniquement Tableau 9 ? (§5.4)
11. Tableau 9 porte-t-il limite **et** cible, à réconcilier avec « Tableau 9 = réf. cible » ? (§5.5)
12. Articles exacts Tableaux 8/9 (§7.2.5.8 vs §7.2.5.9). (§2.1)
13. §7.2.5.6 : base de calcul des % auxiliaires. (§6)
14. §7.2.5.7 : **`SN EN 16798-13:2017` absent de `/refs`** — NA.3/NA.4 non citables. (§6)
15. **Confirmation transverse** : re-lecture réelle du PDF p35/38/39 (non ouvert dans
    cette session, cf. §0).

### 7.4 Normes EN manquantes dans `/refs` (blocage externe)

| Norme | Requise par | Impact |
|---|---|---|
| `SN EN 14825` | définition SEER/SCOP des Tableaux 5-9 | correspondance `seer`(VE)↔SEER non vérifiable |
| `SN EN 16798-13:2017` | méthode §7.2.5.7 (tableaux NA.3/NA.4) | méthode non citable |

---

## 8. Sources

| Source | Localisation | Usage |
|---|---|---|
| Agent appelant (`[TRACÉ PDF]`) | message de tâche | valeurs Tableaux 2, 5, 6, 8, 9 (partiel), §7.2.5.6-7 |
| `docs/project/SIA_3802_4010_PDF_TRACEABILITY.md` §7 | dépôt, l.116-163 | corroboration Tableaux 5, 6, 8 ; complétion Tableau 9 |
| `swiss_sia/model_analyzer.py` | dépôt, l.680-701 | champs projet extraits (eer, seer, sseer, scop, capacités, classes) |
| `traceability/sia380-2-adapter-extraction-contract.spec.md` §4-5 | dépôt | membres API VE (nominal_eer, SEER, SSEER, SCoP) et réserve NCM/UK |
| `refs/SIA-380-2-2022.pdf` | dépôt | **NON OUVERT dans cette session** (voir §0) — relecture p35/38/39 requise |
