# Spec — pathways de justification SIA 380/2:2022 et verdict client décisif

> Statut : **ARBITRAGE RENDU (confiance élevée).** Pathway décisif, grandeur,
> critère verbatim, composition du projet de référence, climat de calcul et pont
> vers SIA 4010 sont **vérifiés en lecture directe du PDF** (chapitres 5-7,
> Tableaux 2-3). Les `[TO VERIFY]` restants sont **hors `/refs`** (SIA 380, SIA
> 2024 Merkblätter, SIA 387/4) ou portent sur le climat d'**application** et le
> choix de voie de consigne.
> Auteur : `norm-analyst`, 2026-08-14.
> Portée : SIA 380/2:2022 FR (`refs/SIA-380-2-2022.pdf`), vérification d'un
> bâtiment CLIENT (application), distincte du climat/protocole de TEST SIA 4010.

---

## 0. Régime de preuve et cadrage

- **[TRACÉ PDF]** — lu en direct dans `refs/SIA-380-2-2022.pdf` (extraction
  PyMuPDF). Locator + valeur strictement nécessaires ; pas de redistribution de
  pages.
- **[TRACÉ]** — relayé d'une extraction antérieure figée en dépôt (`config.py`,
  `figure1.json`, `sia-2024-2021.tables.json`, `critere-test4.spec.md`) ; non
  re-vérifié cette tâche.
- **[INTERPRÉTATION]** — lecture explicitement marquée, justifiée par un article
  cité ; jamais présentée comme citation.
- **[TO VERIFY]** — hors `/refs` ou non localisé ; question précise en §6.
  **Aucune valeur, formule ou tolérance inventée.**

**Cadrage** : SIA 380/2:2022 = « **Méthode dynamique pour la détermination des
besoins, puissance et besoin d'énergie** » (`# SIA 380/2:2022 p.1`) [TRACÉ PDF],
**remplace SIA 382/2:2011 et SIA 2044:2019**. C'est la **méthode de calcul
dynamique** du besoin ; les valeurs limites de besoin sont **calculées** (projet
de référence, §7.2.5), pas tabulées en kWh/m². Structure chapitres 1-7. **La
table des matières (p.3) place « 3.1 Humidification » (p.21) — §3.1 n'est PAS le
climat** (correction).

**Pont normatif capital** : `# SIA 380/2:2022 6.2.2.1` [TRACÉ PDF] — une méthode
de calcul n'est admise que si elle « peut justifier d'une **validation selon SIA
4010** pour les systèmes considérés ». → SIA 380/2 **exige** que l'outil
(IESVE/ApacheSim) soit validé SIA 4010. Entrées minimales : `# SIA 380/2:2022
6.2.2.2` → annexe A.3 + normes EN [TRACÉ PDF] ; ECS : `# SIA 380/2:2022 6.2.2.5`
→ SIA 385/2 [TRACÉ PDF].

---

## 1. Pathways de justification définis par SIA 380/2:2022

- **PATHWAY A — justificatif par valeurs limites/cibles (composant/entrée).**
  `# SIA 380/2:2022 7.2.1.2` [TRACÉ PDF] : « pour les justificatifs (**cas
  d'application 1 et 2 selon SIA 380**), les valeurs de projet calculées sont
  comparées aux valeurs limites et valeurs cibles ». Valeurs par élément =
  **Tableau 3** (§3). Sens de « cas d'application 1 et 2 » défini dans **SIA 380**
  (absente) → `[TO VERIFY]` (b).
- **PATHWAY B — performance globale via projet de référence (DÉCISIF).**
  `# SIA 380/2:2022 7.2.5.1` [TRACÉ PDF] : valeurs limites/cibles de l'indice
  global obtenues en appliquant les **chapitres 5 et 6** à un **projet de
  référence**, sur base du **bilan global selon SIA 380**.
  `# SIA 380/2:2022 7.2.5.2` [TRACÉ PDF] — **critère verbatim** : « La performance
  globale est respectée lorsque la valeur de projet selon le chapitre 6 est
  **inférieure** à la valeur limite ou à la valeur cible correspondante du
  **projet de référence**. »

---

## 2. Grandeur décisive, unité et critère

### 2.1 Pathway B — performance globale (le verdict)

- **Grandeur** : `# SIA 380/2:2022 6.1.4` [TRACÉ PDF] « Le résultat est l'**indice
  de dépense d'énergie du bâtiment selon SIA 380**. Il correspond à la **valeur de
  l'objet**. » Ce que produit le ch.6 : `# 6.1.1` [TRACÉ PDF] (besoins chauffage,
  refroidissement, humid./déshumid., éclairage, ECS si couplée, autres + PV).
- **Agrégation/pondération** : `# SIA 380/2:2022 6.1.2` [TRACÉ PDF] « L'agrégation
  en valeurs annuelles et la pondération s'effectuent **selon SIA 380** » →
  **délégué**, pas un trou de l'outil.
- **Critère** (verbatim §7.2.5.2) : `indice_projet(ch.6) <
  indice_limite_ou_cible(référence)`, inégalité **stricte**, borne **calculée**.
- **Conséquence code** : `cooling_demand_max=None`/`heating_demand_max=None`
  **CONFORMES**.
- **Unité/définition de l'indice** : relèvent de **SIA 380** (absente) →
  `[TO VERIFY]` (a).

### 2.2 Pathway A — par valeurs limites/cibles (diagnostic)

U `W/(m²·K)`, ψ `W/(m·K)`, χ `W/K`, ff, g⊥, τ, infiltration `m³/(h·m²)`, εV,
U_ahu `W/(m²·K)` ; critère `valeur_projet ≤/≥ limite|cible` (`# 7.2.1.2`).

### 2.3 Nécessité de refroidissement — screening STATED (à ne pas confondre)

- Refroidissement **nécessaire** si dépassement de la **courbe limite supérieure**
  (§5.2.2.5) **> 100 h/an** (neuf, `# 3.2.4.3` [TRACÉ PDF]) ; **400 h** (existant,
  `# 3.2.4.5` [TRACÉ PDF]). Base : `# 3.2.4.2` → SIA 180:2014 fig. 3 + annexe C.2.
- **⚠ Distinct** de la **protection chaleur été** `# 7.1.2.1` → **SIA 180:2014
  ch.5** [TRACÉ PDF]. Les 100/400 h ≠ critère de confort d'été.

### 2.4 Exigences déléguées (ch.7) et 2.5 puissances

Ventilation `# 7.1.1` → SIA 382/1 ; chaleur été `# 7.1.2.1` → SIA 180 ch.5
[TRACÉ PDF]. Puissances de dimensionnement `# 4.2-4.3` [TRACÉ] (`W`/`W/m²`).

---

## 3. Projet de référence

### 3.1 Articles et tables (vérifiés)

- `# SIA 380/2:2022 7.2.5.1` et **`7.2.5.3`** [TRACÉ PDF] : « les grandeurs
  d'entrée du projet de référence sont au **Tableau 2** ; **à l'exception de ces
  grandeurs, le projet de référence est calculé avec les mêmes données que le
  projet à l'étude** » (géométrie, usage et climat identiques ; seul le Tableau 2
  est substitué).
- **Tableau 2** `# SIA 380/2:2022 tableau 2, p.32-33` [TRACÉ PDF] (Limite / Cible)
  — voir la liste complète des lignes plus bas ; grandeurs numériques distinctes
  (Uw 1,1/0,88 ; ψ/χ 0/0 ; ff 0,25 ; g⊥ 0,50 ; τ 0,70 ; infiltration 0,15 ;
  εV 1/1,4 ; classes C, L2/L1 ; U_ahu 0,7/0,5 ; émission convection ; ΦH/C,max
  illimitée). Les grandeurs « SIA 2024 » / « SIA 387/4 » : voir **§7**.
- **Tableau 3** `# SIA 380/2:2022 tableau 3, p.36-37` [TRACÉ PDF] — U de tête
  (limite/cible) : mur ext. **0,2/0,14** ; contre terrain **0,3/0,2** ; contre
  local non conditionné **0,28/0,2** W/(m²·K).
- Consignes & confort : `# figure 1 / §5.2.2.1-5.2.2.5, p.27` [TRACÉ].

### 3.2 Mapping Tableau 2/3 ↔ familles de `reference_project.py`

| Famille (clé code) | Source | Locator | Statut |
|---|---|---|---|
| `opaque_envelope_constructions` | Tableau 3 | p.36-37 [TRACÉ PDF] | IMPLEMENTED |
| `window_u_value_and_frame_fraction` | Tableau 2 | p.32-33 [TRACÉ PDF] | IMPLEMENTED |
| `thermal_bridges` (ψ=0, χ=0) | Tableau 2 | p.32-33 [TRACÉ PDF] | MISSING |
| `glazing_solar_and_visible_properties` (g⊥ 0,50 ; τ 0,70) | Tableau 2 | p.32-33 [TRACÉ PDF] | MISSING |
| `glazed_area_ratio_solar_protection_and_control` (fg ; store ; cat. 4/2 ; cmde 2/3) | Tableau 2 + tab.10 + SIA 387/4 | p.32-33, p.46 [TRACÉ PDF] ; fg/cmde délégués | MISSING |
| `infiltration` (0,15) | Tableau 2 | p.32-33 [TRACÉ PDF] | MISSING |
| `sia2024_internal_gains_profiles_and_setpoints` | Tableau 2 → SIA 2024 | **voir §7** | MISSING (partiellement traçable — §7) |
| `sia3874_lighting_power_and_control` | Tableau 2 → SIA 387/4 | délégué (absent) | MISSING |
| `emission_system_and_unlimited_capacity` (convection ; illimitée) | Tableau 2 | p.32-33 [TRACÉ PDF] | MISSING |
| `ventilation_system_and_controls` (εV 1/1,4 ; C ; L2/L1 ; U_ahu 0,7/0,5) | Tableau 2 + Tableau 4 | p.32-33, p.37 [TRACÉ PDF] | MISSING |
| `cooling_generation_and_auxiliaries` | Tableaux 5-9 | p.38-39 [TRACÉ] | MISSING |
| `heating_generation` | Tableaux 8-9 | p.38-39 [TRACÉ] | MISSING |
| `photovoltaic_generation` | Tableau 2 | p.32-33 [TRACÉ] ; article PV à confirmer | MISSING |
| `sia380_annual_aggregation_and_weighting` | délégué **SIA 380** | `# 6.1.2` [TRACÉ PDF] → SIA 380 hors `/refs` | MISSING **par délégation normative** |

`# 7.2.5.3` garantit que géométrie, usage et climat sont **identiques** au projet.

---

## 4. Climat de calcul et données d'usage (vérification CLIENT)

- **Climat de calcul** : `# SIA 380/2:2022 5.2.1.2, p.26` [TRACÉ PDF] « on
  utilisera une **DRY selon SIA 2028** » ; données de dimensionnement hiver/été
  `# ch.2, p.12` [TRACÉ PDF] ; annexe p.59 : « DRY **normale**, selon SIA 2028 »
  et **CH2018 disponible en option** pour l'évolution climatique [TRACÉ PDF].
- **⚠ Requalification** : « CH2018 RCP8.5 2035 » (CLAUDE.md §3.1.1) renvoie à
  **SIA 4010** (`# SIA 4010:2023 3.1.1, p.9` [TRACÉ]), pas au corps de 380/2 (qui
  impose DRY/SIA 2028, CH2018 optionnel/annexe). → `[TO VERIFY]` (c).
- **§7.2.5.3** [TRACÉ PDF] : le projet de référence partage ce climat.
- **Données d'usage** (consignes, débits, gains, fg) : **déléguées SIA 2024** —
  détail et traçabilité par grandeur en **§7**.

---

## 5. Recommandation

**Cibler le Pathway B — `# 7.2.5`** [TRACÉ PDF] (deux runs projet+référence, borne
calculée §7.2.5.2, climat identique §7.2.5.3), Pathway A en diagnostic. Pré-requis
normatif : validation SIA 4010 (`# 6.2.2.1`). **Verdict global** `NOT_CHECKABLE`
tant que l'unité de l'indice SIA 380 (a) n'est pas tracée ; jamais `PASS` sans les
deux runs + validation SIA 4010 + revue. Entrées/sorties : cf. §3.1, §4, §7.

---

## 6. Points `[TO VERIFY]` restants

| # | Question précise | Où trancher | Impact |
|---|---|---|---|
| **(a)** | Unité/définition de l'« indice de dépense d'énergie » + agrégation/pondération | **SIA 380** (absente) — délégué par `# 6.1.2`/`# 6.1.4` | Unité du verdict. Délégué par la norme. |
| **(c)** | Climat d'**application** imposé au-delà du DRY SIA 2028 (année/scénario CH2018 ?) | Annexe 380/2 p.59 + **SIA 4010 §3.1.1** | Traçabilité climat client. |
| **(b)** | « cas d'application 1 et 2 » (§7.2.1.2) ; valeurs **SIA 2024 / SIA 387/4** | SIA 380, SIA 2024, SIA 387/4 (absentes) | Limite/cible + entrées déléguées. |
| **(f)** | **Voie de consigne θi,set** du calcul d'énergie : normale figure 1 (`# 5.2.2.1-.5`) vs simplifiée `# 5.2.2.6` (SIA 2024 Tableau 13) ; « θi,set = SIA 2024 » du Tableau 2 désigne-t-il le Tableau 13 ? | Texte `# 5.2.2` (p.26-27) + chapeau Tableau 2 | Choix de la table θ (§7). |
| **(g)** | φi,set : les valeurs d'humidité de **dimensionnement** (SIA 2024 Tableau 11) sont-elles la **consigne d'exploitation** de la demande humid./déshumid. (ch.6) ? | Texte chapitre 6 (p.29-30) | Source φi,set (§7). |
| **(h)** | **Chapeau/légende des colonnes du Tableau 2** (p.32) : une cellule « SIA 2024 » sans valeur projet = **identité** (projet aussi SIA 2024) ou substitution sur valeur projet libre ? | Texte introductif Tableau 2 (p.32) | Confirme le régime « identité » de §7 (Q-A). |
| (e) | Articles **PV** (Tableau 2) ; **δθ_ctr** (SN EN 15316-2, absente) | SIA 380/2 ; EN hors `/refs` | Complète Tableau 2. |

---

## 7. Famille « consignes / débits » du projet de référence (Tableau 2 × SIA 2024)

Réponse ciblée à l'implémentation du collecteur SIA 2024. Ancrage :
`# SIA 380/2:2022 7.2.5.3, tableau 2, p.32-33` [TRACÉ PDF] ; données SIA 2024
figées `refs/reference-data/sia-2024-2021.tables.json` [TRACÉ].

### 7.1 Régime de chaque cellule du Tableau 2 (Q-A)

- **« spéc. au proj. » côté projet + « SIA 2024 » côté référence** →
  **substitution différenciante** : le projet garde sa valeur, la référence
  substitue SIA 2024 (cas de **qv**).
- **Cellule projet VIDE + « SIA 2024 » côté référence** → **[INTERPRÉTATION]
  identité** : la grandeur est une **donnée d'utilisation standardisée** (SIA
  2024), **identique** dans le projet et la référence. Justification : `# 7.2.5.3`
  (hors Tableau 2 = mêmes données ; ici la valeur SIA 2024 s'impose des deux
  côtés car l'usage n'est pas un paramètre libre du calcul d'énergie) + le titre
  même de SIA 2024 « **Données d'utilisation** des locaux ». **Conséquence** :
  pas de delta projet/référence, mais **la valeur SIA 2024 reste nécessaire pour
  les DEUX runs**. → à confirmer par le chapeau du Tableau 2, `[TO VERIFY]` (h).

### 7.2 Verdict par grandeur {substitution | identité | bloqué-Merkblätter}

| Grandeur (Tableau 2) | Régime | Source de référence + locator | Verdict codage |
|---|---|---|---|
| **qv** débit `m³/(h·P)` | **substitution** | valeur nominale = SIA 2024 **Tableau 11** `air_neuf_hygiene_m3_h_pers` (jour ; `_nuit` pour résidentiel) [TRACÉ] | **VALEUR codable** (Tab.11) ; **profil annuel d'exploitation = BLOQUÉ-Merkblätter** |
| **θi,set,H/C** `°C` | **identité** | voie normale **figure 1 `# 5.2.2.1-.5`** (décalage `# 5.2.2.5` via θ_design **Tableau 11**) ; voie simplifiée **`# 5.2.2.6` = Tableau 13** (annexe B) [TRACÉ] | **codable** (deux voies tracées, **PAS Merkblätter**) ; choix `[TO VERIFY]` (f) |
| **φi,set,H/C** `%` | **identité** | SIA 2024 **Tableau 11** `humidite_relative_h/c_pct` (valeurs de dimensionnement) [TRACÉ] | **codable** (seule table humidité tracée) ; caveat design→exploitation `[TO VERIFY]` (g) |
| **gains internes** (AP, M, pBe, pLiAc, Evm ; profils personnes/appareils/éclairage, horaires, simultanéités, m²/pers) | **identité** | **Fiches d'utilisation SIA 2024** (Merkblätter 3.1, 4.4, 6.2…) — **absentes de `/refs`** (`sia-2024-2021.tables.json.ce_qui_reste_manquant`) [TRACÉ] | **BLOQUÉ-Merkblätter** — ni Tableau 11 ni Tableau 13 ne les contiennent |

### 7.3 Avertissement design vs exploitation (Q-B, Q-C)

- **Tableau 11 = Auslegungswerte (valeurs de DIMENSIONNEMENT, ch.4).** `θ_design`
  (Tab.11) nourrit la **puissance de dimensionnement** `# 4.2-4.3`, **PAS** la
  consigne du calcul d'énergie ch.5-6. Utiliser `θ_design` comme consigne
  d'énergie serait une **erreur de catégorie**.
- **Q-C — θi,set (énergie, ch.5-6)** : source = **figure 1** (`# 5.2.2`, une figure
  de 380/2, décalée par usage via θ_design Tab.11) **ou** **Tableau 13** SIA 2024
  (`# 5.2.2.6`, voie simplifiée « surtout planification précoce »). **Jamais les
  Merkblätter.** Le libellé « θi,set = SIA 2024 » du Tableau 2 pointe littéralement
  vers le Tableau 13 (dont le titre vise « la **Berechnung des jährlichen**
  Klimakälte- und Heizwärmebedarfs »), mais la voie normale 380/2 est la figure 1
  → `[TO VERIFY]` (f).
- **Q-B — qv (énergie)** : la **valeur nominale par personne** est le débit
  hygiénique **Tableau 11** (`air_neuf_hygiene`, 29 `m³/h·P` usages courants, 48
  cuisines/production grossière, 73 sport ; **nuit** = valeur entre parenthèses,
  ex. 15 en résidentiel). Mais le **calcul d'énergie annuel** exige le **profil
  d'exploitation** (heures de fonctionnement, modulation par occupation, réduction
  nocturne pondérée), qui est une donnée d'**exploitation des Merkblätter
  (absentes)**. → la **valeur** est tracée ; le **profil annuel est BLOQUÉ**.
  jour/nuit : les deux niveaux sont tracés (Tab.11) ; leur pondération annuelle ne
  l'est pas.

### 7.4 Conclusion pour le collecteur SIA 2024

Coder **uniquement** les grandeurs à source tracée sans ambiguïté :
- **φi,set** (Tableau 11) — codable, sous caveat (g).
- **θi,set** (figure 1 `# 5.2.2` et/ou Tableau 13 `# 5.2.2.6`) — codable, exposer
  les **deux voies** et laisser (f) sélectionner ; **ne pas** injecter θ_design.
- **qv valeur nominale** (Tableau 11) — codable ; marquer explicitement le
  **profil annuel comme BLOQUÉ-Merkblätter**.
- **Gains internes** — **NE PAS** mapper depuis Tableau 11/13 : conclusion
  correcte = « **famille bloquée : fiches d'utilisation SIA 2024 (Merkblätter)
  requises** ». Elles sont gratuites en ligne (`fiches_utilisation_en_ligne`,
  post-corrigenda) mais **hors dépôt**.

⚠ **Réserve corrigenda** : `sia-2024-2021.tables.json.corrigenda.controle_effectue
= false` — aucune valeur des Tableaux 11/13 n'est confirmée post-rectificatif ;
les Merkblätter en ligne, elles, sont post-corrigenda. À lever avant figeage.

---

## 8. Arbitrage `fg` (Taux des surfaces vitrées) et éclairage de référence

> Ajout `norm-analyst`, 2026-08-14. Câblage du projet de référence
> (`swiss_sia/reference_project.py`, familles
> `glazed_area_ratio_solar_protection_and_control` volet fg et
> `sia3874_lighting_power_and_control`). Aucune formule/valeur inventée ; aucun
> code modifié. `[TO VERIFY]` (i)-(l) étendent §6. Données figées vérifiées en
> lecture directe : `refs/reference-data/sia-2024-2021.usage-data.json`.

### 8.1 `fg` — grandeur de référence et grandeur projet

**Ligne Tableau 2** `# SIA 380/2:2022 tableau 2, p.32-33` [TRACÉ PDF] : « Taux des
surfaces vitrées », symbole **fg**, unité « – » ; **projet = « spéc. au proj. »**,
**référence limite = « SIA 2024 »**, **cible = « SIA 2024 »** → **substitution
différenciante** (régime §7.1) : projet = ratio réel, référence = valeur SIA 2024
par usage.

**Données figées** (`refs/reference-data/sia-2024-2021.usage-data.json`) [TRACÉ] :
- `column_mappings."9"` : symbole **fg**, label **« Glasanteil (pourcentage de
  vitrage) »**, unité **%** ; ex. usage 1.01 (Wohnen MFH) `parameters."9".value =
  30 %`.
- col10 = **Fw** « Abminderungsfaktor Fensterrahmen » (facteur de réduction du
  cadre, 0,75 pour 1.01) — colonne **distincte** de la fraction vitrée.
- **« Fensteranteil / Bruttofassade » (col11) : ABSENTE du JSON** — 0 occurrence de
  `Fensteranteil`/`Bruttofassade`/`Fassade` (recherche vérifiée). L'extraction ne
  contient **que** la Glasanteil (col9).

**Grandeur de référence** — La référence du **fg** de SIA 380/2 est la
**Glasanteil (SIA 2024 col9, symbole fg)**, p.ex. 30 % en Wohnen MFH, **et non** le
Fensteranteil Bruttofassade (col11). Base : **identité de symbole** fg↔fg +
sémantique « surfaces vitrées » = « Glas » ; le col11 porte un **autre symbole** et
est **hors `/refs`**. → **[INTERPRÉTATION]** ancrée (symbole + label), mais la
**clause de définition du symbole fg** (SIA 380/2) et la **définition de
« Glasanteil »** (SIA 2024) **ne sont pas dans `/refs`** → `[TO VERIFY] (i)`.

**Grandeur projet requise vs modèle** — Côté projet, « spéc. au proj. » = fraction
vitrée réelle **selon la définition de fg**. Le modèle expose un **WWR =
window_area / wall_area** (`model_analyzer.py` l.1132-1133, donnée fournie). Ce
**n'est pas** la Glasanteil :
- **Numérateur** : Glasanteil = surface de **verre** (SIA 2024 isole le verre
  (col9) du **cadre** via Fw (col10)) ; WWR = surface de **fenêtre** (verre +
  cadre). Écart ≈ facteur de cadre → grandeurs **non identiques**.
- **Dénominateur** : celui de la Glasanteil (façade brute ? SRE ? élément ?)
  **non lu** (définition hors `/refs`) ; `wall_area` du modèle (brut vs net des
  baies) **non caractérisé** → non prouvé égal.
- **[INTERPRÉTATION]** : col9 = 30 % avec Fw = 0,75 (col10) séparés ⇒ la Glasanteil
  n'est pas un simple verre/fenêtre (~0,7). La grandeur analogue à un WWR
  window/façade serait le **Fensteranteil (col11)** — précisément **pas** le
  référent de fg.

**VERDICT fg** :
- **Référence** : SIA 2024 **Glasanteil (col9, symbole fg)** — tracée, disponible.
  **Pas** le Fensteranteil Bruttofassade (col11, absent).
- **Projet** : fraction de **verre** définie comme fg ; le **WWR window/wall** du
  modèle est une **grandeur différente**.
- **Câblable avec le WWR existant ? NON — `[TO VERIFY]`.** Ne pas relier WWR→fg.
  Requis : (i) définition de fg + de la Glasanteil ; (j) grandeur projet « fraction
  de verre » cohérente (ou conversion window→glass explicitement tracée ; Fw col10
  disponible mais son usage comme conversion reste à valider). Tant que non tracé,
  le **volet fg** de `glazed_area_ratio…` reste **MISSING** ; la **valeur de
  référence col9** demeure néanmoins tracée pour le run de référence.

### 8.2 Éclairage — `pLi` (SIA 387/4) vs données SIA 2024 en notre possession

**Ligne Tableau 2** `# SIA 380/2:2022 tableau 2, p.32-33` [TRACÉ PDF] :
- « Puissance spécifique de l'éclairage », symbole **pLi**, unité **W/m²** :
  **référence (limite ET cible) = « SIA 387/4 »**.
- « Éclairement (indice de maintenance) » **Evm** : **référence = « SIA 2024 »**.
- Commande : **« SIA 387/4:2017, tableau 10 »** → manuelle / régulation continue LED.

**Ce que NOUS avons** (`usage-data.json`) [TRACÉ] :
- col64 **E_vm** « Beleuchtungsstärke » [lx] (150 lx en 1.01).
- col71 **eta_lm** « Leuchten-Lichtausbeute » [lm/W] (90 lm/W en 1.01).
- `annual_energy_kwhm2` : colonnes **numérotées SANS légende** (clés 3…24, kWh/m²).
  **Aucune** étiquette « Beleuchtung »/« Elektrizität »/« Heizwärme » dans le
  fichier (vérifié) → la **demande annuelle d'éclairage KZ n'est pas identifiable**
  → `[TO VERIFY] (k)`.
- **SIA 387/4 (partie éclairage, méthode pLi + tableau 10) : ABSENTE de `/refs`.**

**Analyse normative** :
1. La grandeur de référence exigée est **pLi [W/m²]**, **source SIA 387/4** — pas
   SIA 2024 (cité seulement pour Evm). La commande (tab.10) est aussi **SIA 387/4**.
2. **Voie « KZ annuel »** : la demande KZ est une **énergie [kWh/(m²·a)]**, pas une
   **puissance [W/m²]**, et joue un rôle **différent** (résultat pré-calculé en
   conditions SIA 2024, non l'entrée pLi du run dynamique ch.6 du projet de
   référence). Substituer kWh/m²·a à pLi = **erreur de catégorie** ; de plus la
   colonne n'est **pas identifiable** (§ ci-dessus) → **non recevable**.
3. **Voie « Evm + efficacité »** : passer de Evm [lx] et eta_lm [lm/W] à pLi [W/m²]
   exige les **facteurs de la méthode SIA 387/4** (facteur d'utilisation du local,
   facteur de maintenance…). pLi = Evm / eta_lm **seul** (utilisation = maintenance
   = 1) serait une **simplification interdite / formule inventée** ; ces facteurs
   sont **précisément** le contenu manquant de SIA 387/4 → **non recevable sans
   SIA 387/4**. Aucune formule pLi proposée.
4. La **commande d'éclairage** (SIA 387/4 tab.10) est également **hors `/refs`**.

**VERDICT éclairage** : **BLOQUÉ SIA 387/4.** La famille
`sia3874_lighting_power_and_control` **reste bloquée** tant que la partie éclairage
de SIA 387/4 (méthode pLi + tableau 10) n'est pas fournie. Seul **Evm (col64)** est
tracé SIA 2024 et câblable comme **éclairement de référence** — mais **Evm ≠ pLi**
et ne débloque **ni** la puissance **ni** la commande. `eta_lm (col71)` est un
intrant parmi d'autres de la méthode absente, **inutilisable seul**.

### 8.3 `[TO VERIFY]` ajoutés (étendent §6)

| # | Question précise | Où trancher | Impact |
|---|---|---|---|
| (i) | Définition exacte de **fg** (numérateur verre vs fenêtre ; dénominateur façade brute/SRE/élément) | SIA 380/2 clause du symbole + SIA 2024 déf. « Glasanteil » (hors `/refs`) | Identité fg↔Glasanteil ; comparabilité |
| (j) | Grandeur **projet** « fraction de verre » conforme à fg ; WWR window/wall convertible (via Fw col10) ? sémantique de `wall_area` (brut/net) | SIA 380/2 + SIA 2024 + code modèle | Câblage côté projet |
| (k) | Légende des colonnes `annual_energy_kwhm2` (quelle clé = Beleuchtung ?) | Feuille KZ_Raum_2024 SIA 2024 (non légendée en dépôt) | Identifier la demande KZ éclairage |
| (l) | Méthode **pLi** + **tableau 10** (commande) de **SIA 387/4** | SIA 387/4 partie éclairage (hors `/refs`) | Débloque la famille éclairage |

---

## Normes appelées mais absentes de `/refs` (aucune valeur inventée)
- **SIA 380** — bilan/indice global, agrégation/pondération (§6.1.2/.4), limite
  calculée (§7.2.5.1).
- **SIA 2024** — Tableaux 11/13 **tracés** (figés en dépôt) ; **Merkblätter
  (fiches d'utilisation) ABSENTES** → gains/profils/horaires bloqués (§7).
- **SIA 387/4** — éclairage, commandes tab. 9/10 (Tableau 2).
- **SIA 382/1** — ventilation (§7.1.1) ; **SIA 385/2** — ECS (§6.2.2.5).
- **SIA 180:2014** — chaleur été ch.5 (§7.1.2.1) ; fig. 3/4, annexe C.2 (§3.2.4.2).
- **SN EN ISO 52016-1:2017 §7.2**, **SN EN 15316-2:2017**, EN de l'annexe A.3
  (§6.2.2.2).

**Le critère de réussite du Pathway B est acquis** (`# 7.2.5.2`, [TRACÉ PDF]) et
ne dépend d'aucune constante inventée.
