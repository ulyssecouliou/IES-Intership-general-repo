# Vitrage du cas 600 — valeur normative & demande EN ISO 52016-1:2017

> Statut : **NOTE D'ANALYSE NORMATIVE** — annexe de `traceability/test-1.spec.md` §4
> (« Vitrage ») et §8 pt 3. Ne fige aucune valeur.
> Auteur : `norm-analyst`. Date : 2026-07-31.
> Convention de marquage : **[V]** = vérifié dans une source citée avec fichier + ligne ;
> **[I]** = inféré / calculé par moi à partir de sources vérifiées ; **[?]** = non
> vérifiable avec les sources en main.

## Sources effectivement lues pour cette note

| Source | Chemin | Statut |
|---|---|---|
| ASHRAE 140:2023 (texte extrait) | `C:\Users\ulysse.couliou\.claude\jobs\d1486f24\tmp\ashrae140.txt` | lu, l. 2975-3420 vérifiées ligne à ligne |
| Spécification SIA Test 1 (texte extrait) | `…\scratchpad\norme\spec_test1.txt` | lue intégralement (123 l.) |
| SIA 4010:2023 (texte extrait, FR) | `…\scratchpad\norme\sia_4010_2023.txt` | recherches ciblées « 52016 », « ASHRAE » |
| SIA 380/2:2022 (texte extrait, FR) | `…\scratchpad\norme\sia_380_2_2022.txt` | recherches ciblées « 52016 » |
| Manifeste d'actifs VE | `C:\Users\ulysse.couliou\Documents\switzerland\SIA4010_Test1_Case600\reference_model_assets.json` | lu intégralement |
| Config VE | `…\SIA4010_Test1_Case600\reference_model_config.json` | l. 1-145 lues |
| Manifeste de cas SIA (variante `test`) | `C:\Users\ulysse.couliou\Documents\switzerland\test\sia4010_case_manifest.json` | bloc `iso_test1_glazing`, l. 522-548 |
| Résultats QA du run en échec | `…\SIA4010_Test1_Case600\reference_model_artifacts\reports\excel_ready\validation_results.csv` | l. 25-30 |
| Surface API IESVE | `C:\Users\ulysse.couliou\Documents\SIA_Compliance_Scripts\ve_adapter\ve_api_surface.json` | l. 5948-5973, 8139-8162 |

**Sources ABSENTES de `/refs` — donc rien de ce qui en dépend n'est vérifié :**
- **EN ISO 52016-1:2017** (texte intégral, ch. 7, tableau 27) — la seule source
  *formellement* citée par SIA pour le vitrage. → Partie B.
- **ASHRAE 140:2017** — l'édition explicitement nommée comme base par la spec SIA.
- **NREL/TP-472-6231 (BESTEST 1995), Part I, Tables 1-7 et 1-8** — source citée par
  `reference_model_assets.json` et `reference_model_config.json` pour **toutes** les
  valeurs du vitrage (3,0 / 0,789 / 0,86156 / 1,06 / 6,297 / 0,003175 / 0,013).
  **Ce document n'est pas dans `/refs`. Aucune de ces valeurs n'est donc vérifiée**,
  au sens de CLAUDE.md règle 1. Elles sont seulement *cohérentes entre elles* (démontré
  en A.3).

---

# PARTIE A — Quelle valeur pour le vitrage du cas 600 ?

## A.0 Verdict

1. **La question « 3,0 ou 2,10 ? » est indécidable avec les sources en main.** Elle ne
   peut être tranchée que par EN ISO 52016-1:2017 ch. 7 (ou, à défaut, ASHRAE 140:2017).
   C'est la justification directe de la Partie B. **[V/I — confiance haute]**
2. **Mais la question posée au modèle est mal posée.** Dans ASHRAE 140:2023 — la seule
   édition en main — **la fenêtre n'est PAS spécifiée par un U-value**. Le normatif est
   la **Table 7-10 (« Normative Table 7-10 »)** : couches, épaisseurs, λ, ρ, cp, gaz,
   émittance, optique par vitre. Le U-value 2,10 est dans une **table informative** et la
   norme dit **explicitement** qu'il **doit** varier d'un logiciel à l'autre.
   **[V — confiance très haute, ashrae140.txt l. 3169, 3174-3186, 3294]**
3. **Conséquence immédiate et actionnable : le contrôle `VE-THERM-004` est mal spécifié.**
   Comparer un U rapporté par le CDB à un U tabulé, avec une tolérance absolue de
   0,005 W/(m²K), contredit la norme source elle-même. Ce contrôle doit être remplacé
   par un contrôle **sur les couches**, ou rendu **explicite quant à la convention de
   résistances superficielles**. **[I — confiance haute]**
4. **L'écart 3,0 → 2,917 n'est PAS un « verre différent »** : c'est un problème de
   plomberie du modèle. Trois hypothèses restent ouvertes (A.6) et aucune n'est
   tranchable sans sonder VE. L'hypothèse « convention de résistances » du commanditaire
   est plausible mais **pas seule en lice**. **[I — confiance moyenne-haute]**
5. **NE PAS calibrer les couches pour atteindre 3,0.** Ce serait graver dans le modèle
   une valeur dont même la source citée est absente du dépôt.

## A.1 Vérification indépendante de la Table 7-11 (décalage de colonnes)

La lecture du commanditaire est **CONFIRMÉE**, avec une précision : `ho` = 17,8
(extérieur) et `hi` = 4,5 (intérieur). Le décalage `pdftotext` porte sur l'alignement
vertical, pas sur l'**ordre** : 9 libellés, 9 valeurs, ordre préservé.

Appariement rétabli (`ashrae140.txt` l. 3294-3313) et **preuve croisée de chaque ligne** :

| # | Libellé (l. 3296-3312) | Valeur | Preuve indépendante |
|---|---|---|---|
| 1 | Effective conductance of air gap (hs) | 5,208 W/(m²K) [R 0,19200] | note b (l. 3315) : 0,0625/0,012 = **5,2083** ✔ |
| 2 | Conductance of each glass pane | 328 W/(m²K) [R 0,00305] | note c (l. 3318) : 1,00/0,003048 = **328,08** ✔ |
| 3 | **Exterior** combined surface coeff. (ho) | 17,8 W/(m²K) [R 0,05618] | **Table 7-7, l. 3012** : Windows, hcomb,ext = **17,8** ✔ ; 1/17,8 = 0,05618 ✔ |
| 4 | **Interior** combined surface coeff. (hi) | 4,5 W/(m²K) [R 0,22222] | **Table 7-9, l. 3091** : Windows, hcomb,int = **4,5** ✔ ; 1/4,5 = 0,22222 ✔ |
| 5 | U-factor from interior air to ambient air | 2,10 W/(m²K) [R 0,47650] | note e (l. 3320) : 0,192+2×0,00305+0,05618+0,22222 = **0,47650** → U = **2,0986** ✔ |
| 6 | Double-pane SHGC | 0,769 à incidence normale | **Table 7-12, l. 3338** : angle 0° → SHGC **0,769** ✔ |
| 7 | Double-pane shading coefficient (SC) | 0,883 à incidence normale | note h (l. 3327) : SC = SHGC/0,87 = 0,769/0,87 = **0,8839** ✔ |
| 8 | Index of refraction | 1,493 | — (plausible verre sodocalcique) |
| 9 | Extinction coefficient | 0,0337/mm | — |

Preuve supplémentaire du couple (ho, hi) : à la l. 3833-3834, dans la table du cas 660,
les mêmes libellés sont **correctement alignés** par l'extraction et donnent
`ho = 17,8 [R 0,05618]` / `hi = 4,5 [R 0,22222]`. **[V — confiance très haute]**

> ⚠ Remarque de méthode : le même type de décalage existe l. 5083-5086 (annexe
> récapitulative), où `hi` et `ho` sont **inversés** par rapport à 3833-3834. Ne jamais
> lire une table de ce PDF sans recoupement arithmétique.

## A.2 Ce qui est NORMATIF, dans ASHRAE 140:2023, pour la fenêtre du cas 600

Trois citations décisives, vérifiées mot pour mot :

- **§7.2.1.11.2 « Window Properties »** (l. 3169) :
  « **The properties of the window provided in Table 7-10 shall be applied.** »
  → Le normatif, c'est la **Table 7-10** : 2 vitres, **3,048 mm**, λ verre **1,00 W/(m·K)**,
  lame d'air **12,0 mm**, ρ 2470, cp 750, émittance IR 0,840, transmittance directe par
  vitre **0,834** et réflectance **0,075** à incidence normale (l. 3218-3267). **[V]**
- **Note informative 1 de §7.2.1.11.2** (l. 3174-3176) :
  « Informative Table 7-11 includes calculated values derived from fundamental properties
  of **Normative Table 7-10** and alternative constant surface coefficients of Sections
  7.2.1.9.3 and 7.2.1.10.3, **for programs that may need this information**. » **[V]**
- **Notes informatives 2 et 3** (l. 3178-3186) — le point capital :
  - « For programs that calculate time-step varying surface infrared radiative exchange
    or convective coefficients or both, … **variation … may be expected: individual
    surface coefficient U-factors, air gap effective conductance, and overall U-factors.** »
  - « For programs that automatically calculate heat transfer within an air space or empty
    cavity, **variation … may be expected: effective air gap conductance and overall
    U-factor.** » **[V]**

**Lecture (interprétation, marquée comme telle) :** la norme *anticipe et autorise
explicitement* qu'un logiciel comme ApacheSim rapporte un U de vitrage différent du U
tabulé, précisément à cause (i) des coefficients de surface et (ii) de la conductance de
lame. **Imposer une tolérance de 0,005 W/(m²K) sur le U du vitrage est donc contraire à
l'instruction de la norme source.** Le critère normatif porte sur les **couches**, pas sur
le U. **[I — confiance très haute]**

## A.3 Les trois valeurs : provenance et arithmétique

### a) 3,0 W/(m²K) — le jeu « BESTEST 1995 »
Déclaré dans `reference_model_config.json` l. 124-128 (`project_window_u_w_m2k` = 3.0) et
`reference_model_assets.json` l. 1336-1432. Le jeu complet est lisible dans
`C:\Users\ulysse.couliou\Documents\switzerland\test\sia4010_case_manifest.json`
l. 531-547 : 2 vitres, **3,175 mm**, lame **13 mm**, conductance de lame **6,297 W/(m²K)**,
λ verre **1,06 W/(m·K)**, ρ 2500, cp 750, ε 0,9, τ_vitre **0,86156**, **U 3,0**,
**SHGC 0,789**, **SC 0,907**. **[V — le fichier dit bien cela]**

**Cohérence interne du jeu (calcul par moi, [I]) :**
- R_vitre = 0,003175/1,06 = 0,0029953 ; deux vitres = **0,0059906**
- R_lame = 1/6,297 = **0,15880578** — **exactement** la valeur inscrite dans
  `reference_model_assets.json` l. 1412 (`0.1588057805304113`). ✔
- R_assemblage (surface à surface) = **0,1647964** → **U_ss = 6,068 W/(m²K)**
- Pour obtenir U = 3,000 il faut R_total = 0,333333, donc des films de **0,168537 m²K/W**
  (≈ Rsi 0,1206 [hi = 8,29] + Rse 0,0479 [he ≈ 20,9]).
- SC 0,907 = 0,789/0,87 → même relation que la note h d'ASHRAE 140. ✔

→ **Le jeu « 1995 » est arithmétiquement cohérent et complet.** Mais sa source
(NREL/TP-472-6231) **n'est pas dans `/refs`** : je ne peux pas certifier un seul de ses
chiffres, ni la valeur des coefficients de surface qui produisent le 3,0. **[?]**

### b) 2,10 W/(m²K) — le jeu « ASHRAE 140:2023 »
- R_assemblage = 2×(0,003048/1,00) + 1/5,2083 = 0,006096 + 0,192000 = **0,198096**
  → **U_ss = 5,048 W/(m²K)**
- + films fenêtre de la suite BESTEST (1/17,8 + 1/4,5 = 0,278402) → R = 0,476498
  → **U = 2,0986 ≈ 2,10** ✔ **[V+I — confiance très haute]**

### c) 2,917 W/(m²K) — ce que le CDB VE rapporte
`validation_results.csv` l. 28 : `cdb_w_m2k = 2.917067766189575`, `declared_w_m2k = 3.0`,
`qa_tolerance_w_m2k = 0.005`, `tolerance_is_regulatory = false`. **[V]**
→ R_total(VE) = **0,3428100 m²K/W**, soit **ΔR = +0,0094767** par rapport au 3,0 déclaré.

### Tableau comparatif — l'effet « convention » et l'effet « verre » sont du même ordre

| Assemblage | R verre+lame | + films BESTEST fenêtre 1995 (0,1685) | + films ISO 6946 (0,13+0,04) | + films ASHRAE 140 fenêtre (0,2784) |
|---|---|---|---|---|
| Jeu 1995 (3,175 mm, λ 1,06, lame 6,297) | 0,16480 → **6,068** | **3,003** | 2,982 | 2,256 |
| Jeu 2023 (3,048 mm, λ 1,00, lame 5,208) | 0,19810 → **5,048** | 2,745 | 2,717 | **2,099** |

(Calculs [I], sur la base des chiffres [V] de la Table 7-10/7-11 et du manifeste.)

**Enseignement :** changer de convention de films fait bouger le U de **2,10 → 3,00**, soit
plus que changer de verre. Le U seul ne discrimine donc **rien** ; il ne devient une
information que si la convention de films est déclarée avec lui.

## A.4 Réponse à la question 2 — « 2,10 est-il bien un U air-air ? À quoi le comparer ? »

**Oui, films inclus des deux côtés.** Le libellé (l. 3304) est « U-factor from **interior
air to ambient air** » et la formule de la note e (l. 3320) additionne explicitement
`1/hi` et `1/ho`. **[V — confiance très haute]**

**Mais ces films sont spécifiques à la suite d'essai** : 17,8 / 4,5 sont les valeurs
« alternative constant » des Tables 7-7 / 7-9, applicables **seulement** au cas où le
logiciel ne calcule ni la convection ni l'IR variables au pas de temps
(§7.2.1.9.3 / §7.2.1.10.3 branche b.2, déjà tranché dans `test-1.spec.md` §3.1).
Elles ne correspondent à **aucune** convention normalisée générique. **[V]**

**Conséquence pour IESVE :**
- `VECdbConstruction` expose `get_u_factor`, `get_default_resistances`, `get_layers`,
  `get_g_values` (`ve_api_surface.json` l. 5948-5973) et l'énumération
  `uvalue_types` = **{ ashrae, cibse, iso, t24 }** (l. 8139-8162). **[V]**
- Il n'existe **aucune** valeur de `uvalue_types` correspondant aux films 17,8 / 4,5.
  Donc **il n'existe pas de grandeur IESVE à laquelle comparer directement 2,10** —
  ni 3,0. **[I — confiance haute]**
- La seule grandeur comparable sans convention est le **U surface-à-surface**
  (verre + lame seuls) : **6,068** pour le jeu 1995, **5,048** pour le jeu 2023.
  → **Action `ve-adapter-engineer` :** vérifier si VE peut restituer un U sans films, et
  relever `get_default_resistances()` + `get_u_factor()` pour **chacune** des 4 valeurs
  de `uvalue_types`. Ces 4 nombres, mis côte à côte, quantifient l'effet de convention et
  refermeront le débat en une exécution. **[recommandation, non normatif]**

## A.5 Réponse à la question 3 — g = 0,789 vs SHGC = 0,769

Ce sont **la même grandeur physique** (facteur solaire à incidence normale, vitrage
double nu) issues de **deux spécifications de fenêtre différentes** :

| | Jeu 1995 (dans le modèle) | Jeu 2023 (Table 7-10/7-11/7-12) |
|---|---|---|
| τ solaire **par vitre**, incid. normale | 0,86156 | **0,834** (l. 3265) |
| réflectance par vitre | non déclarée | **0,075** (l. 3267) |
| SHGC double, incid. normale | **0,789** | **0,769** (l. 3304, l. 3338) |
| SC double | **0,907** (= 0,789/0,87) | **0,883** (= 0,769/0,87, l. 3305) |
| U air-air | 3,0 | 2,10 |
| λ verre / épaisseur / lame | 1,06 / 3,175 mm / 13 mm | 1,00 / 3,048 mm / 12,0 mm |

**Ce ne sont donc pas des grandeurs différentes : ce sont deux éditions différentes.**
Les deux jeux sont chacun **internes-cohérents** (relation SC = SHGC/0,87 vérifiée dans
les deux). **Il est interdit de les panacher** : prendre U de l'un et g de l'autre
produirait une fenêtre qui n'existe dans aucune norme. **[I — confiance très haute]**

Le modèle actuel est **entièrement dans le jeu 1995** (λ 1,06 ; 0,86156 ; 0,789 ; 6,297).
Il est donc **au moins cohérent**. La question ouverte est seulement : *est-ce la bonne
édition ?*

## A.6 Diagnostic du 2,917 — trois hypothèses, aucune tranchée

**Défaut de traçabilité constaté d'abord :** dans `reference_model_assets.json`, les deux
couches de verre de `external_glazing` (l. 1401-1406 et l. 1427-1431) ont
`"properties": {}` — **aucune épaisseur n'est déclarée**. Le 3,175 mm figure uniquement
dans `sia4010_case_manifest.json` l. 534, qui n'alimente pas ce paquet d'actifs. De plus,
un log d'une itération antérieure montre VE restituant une épaisseur de couche vitrée de
**0,0 m** (`…\SWISSG\reference_model_artifacts\logs\reference_model.log` l. 130 :
« requested glazed thickness=0.024 m, VE read-back=0.0 m »). **[V]**
→ **Le U du CDB n'est pas reproductible depuis les entrées déclarées.** Le contrôle
`VE-THERM-004` compare donc deux nombres dont l'un n'a pas de dérivation traçable.

Sur ΔR = +0,0094767 m²K/W, trois causes suffisent chacune, seules ou combinées :

| Hyp. | Cause | Valeur qu'il faudrait | Plausibilité |
|---|---|---|---|
| **H1** | Convention de résistances superficielles VE ≠ films implicites du 3,0 | films VE = **0,178014** au lieu de 0,168537 | forte — c'est exactement ce qu'annonce la note 2 de §7.2.1.11.2 |
| **H2** | VE recalcule la lame au lieu d'utiliser la R déclarée | conductance de lame **≈ 5,94** au lieu de 6,297 | forte — exactement la note 3 de §7.2.1.11.2 |
| **H3** | Épaisseur de vitre non déclarée → défaut VE | ≈ **8,2 mm par vitre** (si seule cause) | faible seule, mais non exclue en combinaison |

**Aucune ne peut être départagée analytiquement** : une équation (U = 2,917), trois
inconnues. **[I — confiance haute sur le raisonnement, aucune conclusion sur la cause]**

**Signature de convention visible aussi sur l'opaque** (`validation_results.csv` l. 25-27,
tous PASS) : mur 0,514 déclaré / **0,51039** CDB ; toiture 0,318 / **0,31916** ; plancher
0,039 / **0,039272**. Le même biais existe partout ; il ne fait échouer que le vitrage.
Raison arithmétique : la tolérance **absolue** de 0,005 W/(m²K) vaut **0,97 %** sur un mur
à 0,514 mais **0,17 %** sur une fenêtre à 3,0 — soit un critère **6 fois plus sévère** sur
le composant le plus sensible aux conventions. **La règle QA elle-même est mal
dimensionnée.** **[I — confiance haute]**

## A.7 Ce qu'il faut faire — et ne pas faire

**Ne pas faire :**
- ❌ Calibrer épaisseur / λ / R de lame pour retomber sur 3,0 (ou sur 2,10). Interdit :
  graverait une valeur dont la source n'est pas dans `/refs`.
- ❌ Remplacer 3,0 par 2,10 « parce que c'est la norme la plus récente ». La spec SIA
  renvoie à l'édition **2017**, pas à 2023, ni à 1995.
- ❌ Panacher (U 2,10 + g 0,789, ou λ 1,06 + τ 0,834).

**Faire, dans cet ordre :**
1. **Requalifier `VE-THERM-004`** : le passer de FAIL bloquant à **INFO / avertissement**
   tant que la Partie B n'a pas abouti, en journalisant explicitement la convention.
   Justification normative : ASHRAE 140:2023 §7.2.1.11.2 notes 2 et 3 (l. 3178-3186)
   annoncent que ce U **doit** varier selon le logiciel.
2. **Déplacer le contrôle sur les entrées normatives** : épaisseurs, λ, ρ, cp, gaz /
   R de lame, optique par vitre — c'est-à-dire l'équivalent de la Table 7-10, une fois
   confirmée l'édition. C'est le seul contrôle qui soit réellement normatif.
3. **Déclarer l'épaisseur des vitres dans `reference_model_assets.json`** (couches
   l. 1401-1432) : sans elle, aucun contrôle de vitrage n'est reproductible. Corriger ce
   défaut **ne dépend d'aucune norme manquante** — c'est une remise en cohérence avec
   `sia4010_case_manifest.json` l. 534, à faire dès maintenant.
4. **Sonder VE** (`ve-adapter-engineer`) : `get_layers()`, `get_default_resistances()`,
   `get_u_factor()` × {ashrae, cibse, iso, t24}, `get_g_values()`. Un seul run
   discrimine H1/H2/H3.
5. **Obtenir EN ISO 52016-1:2017 ch. 7** → Partie B. Seule voie pour trancher l'édition.

## A.8 Ce que je n'ai PAS vérifié

- Aucune valeur de NREL/TP-472-6231 (document absent). Les 3,0 / 0,789 / 0,86156 / 1,06 /
  6,297 / 3,175 mm / 13 mm sont **repris du dépôt, pas vérifiés à la source**.
- Le contenu d'**ASHRAE 140:2017** et d'**EN ISO 52016-1:2017**. Réserve « gras non
  préservé » de `test-1.spec.md` §4 toujours ouverte : la note a de la Table 7-10
  (l. 3270) et de la Table 7-11 (l. 3314) dit « Updates to Standard 140-2017 are
  highlighted in bold », et l'extraction efface le gras. **Je ne peux donc pas dire
  quelles cellules de ces tables ont changé entre 2017 et 2023.**
- **[I, confiance faible — à ne pas utiliser comme preuve]** L'existence même de la note
  « Updates to Standard 140-2017 » suggère que la Table 7-10 (approche « propriétés
  fondamentales / WINDOW 7 ») **existait déjà en 2017**, ce qui rendrait le jeu 1995
  obsolète pour SIA. Mais c'est une inférence sur une mise en forme que je ne peux pas
  lire. Elle **ne justifie aucune modification du modèle**.
- Les convention de résistances superficielles réellement appliquées par IESVE (aucune
  documentation VE dans `/refs` sur `get_default_resistances`).
- Le contenu de `Resultaterfassung_Test1.xlsx`, qui pourrait contenir les entrées de
  référence utilisées par les 4 programmes de référence SIA.

---

# PARTIE B — Liste de photos à demander : EN ISO 52016-1:2017

## B.0 Consignes générales de prise de vue (à transmettre telles quelles)

- **Une photo = une page entière**, à plat, sans coupe. Si un tableau se poursuit sur la
  page suivante, photographier **les deux pages**.
- **L'en-tête et le pied de page doivent être lisibles sur chaque cliché** : ils portent
  la référence d'édition (du type `EN ISO 52016-1:2017 (E)`) et le numéro de page. C'est
  notre preuve d'édition, cliché par cliché.
- **Inclure systématiquement le titre du tableau ET toutes ses notes de bas de tableau**
  (a, b, c…). Dans ASHRAE 140 ce sont les notes qui portent la convention de calcul ; il
  faut supposer qu'il en va de même ici.
- Ne pas recadrer, ne pas redresser, ne pas passer en noir & blanc : le **gras** et
  l'italique sont porteurs de sens (cf. A.8).

## B.1 — PRIORITÉ 0 : preuve d'édition et repérage (indispensable, ~6 clichés)

| # | Ce qu'il faut | Pourquoi chez nous |
|---|---|---|
| **B1.1** | **Page de couverture / page de titre** : numéro complet de la norme, titre, **date/année d'édition**, mention « ed-1 » si présente, ICS, et la page d'avant-propos national suisse (SN) si elle existe | Lever la réserve **2017 vs 2023** ouverte dans `test-1.spec.md` §4 et §10. Sans ça, tout le reste est inexploitable |
| **B1.2** | **Table des matières complète** (toutes les pages) | Nous ne savons **pas** où se trouve le tableau 27, ni quels sont les sous-articles de 7.x. Cf. B.5 |
| **B1.3** | **Liste des tableaux** et **liste des figures**, si le document en comporte une | Localiser le **tableau 27** cité par SIA 4010. Si cette liste n'existe pas, voir B.5 |
| **B1.4** | **Première page du chapitre 7** (titre du chapitre + premier paragraphe) | Confirmer que le ch. 7 est bien le chapitre « validation / contrôle qualité » et non autre chose. Nous le supposons seulement |
| **B1.5** | **Toutes les têtes de sous-articles 7.1 à 7.n** (peut se faire par photos des pages où elles apparaissent) | SIA 4010 renvoie précisément à **7.2.2** ; SIA 380/2 renvoie à **7.2**. Il faut la structure pour ne rien manquer |
| **B1.6** | **Page(s) des références normatives** où **ASHRAE 140** est citée, avec **son année** | La spec SIA dit « (Basis ASHRAE 140:2017) ». Or ISO 52016-1 est de 2017 : elle référence peut-être ASHRAE 140-2014 ou -2011. **Contrôle de cohérence critique** pour savoir quel jeu de fenêtre est réellement visé |

## B.2 — PRIORITÉ 1 : le bloquant (Test 1, cas 600/900)

| # | Clause / tableau demandé | Ce qu'on en attend **exactement** | Usage chez nous |
|---|---|---|---|
| **B2.1** | **§7.2.2 en intégralité** (toutes les pages du sous-article) | Description complète de la cellule d'essai : géométrie, orientation, liste des cas | SIA 4010 tab. 62 et tab. 64 ligne 1 citent nommément « chiffre 7.2.2 » (`sia_4010_2023.txt` l. 2652-2653 et 2850) |
| **B2.2** | **Tableau 27 en intégralité** : titre, corps, **toutes** les notes, **plus la page qui le précède** (paragraphe d'introduction) | Inconnu — c'est justement ce qu'on cherche | SIA 4010 le cite comme **le champ d'application du Test 1** (`sia_4010_2023.txt` l. 2652-2653 : « selon EN ISO 52016-1:2017, chapitre 7, tableau 27 » ; idem tab. 64 l. 2844-2850) |
| **B2.3** | **La clause et/ou le tableau du ch. 7 qui définit la FENÊTRE** | Impérativement : (i) nombre de vitres, **épaisseur de vitre**, **λ**, **ρ**, **cp**, **émissivité IR** ; (ii) lame : **épaisseur**, **gaz**, et si elle est donnée en **conductance/résistance** ou en gaz à calculer ; (iii) optique : **transmittance et réflectance solaires par vitre à incidence normale**, et/ou **g / SHGC du double vitrage**, et toute table angulaire ; (iv) **le U s'il est donné, ET la phrase qui dit quels coefficients de surface il inclut** ; (v) les **coefficients de surface intérieur et extérieur applicables à la fenêtre** | **C'EST LA QUESTION 1.** Départage le jeu « 1995 » (λ 1,06 / 3,175 mm / lame 13 mm à 6,297 / τ 0,86156 / g 0,789 / U 3,0) du jeu « 2023 » (λ 1,00 / 3,048 mm / lame 12,0 mm à 5,208 / τ 0,834 / g 0,769 / U 2,10). Spec SIA : « Verglasung : ISO EN 52016:2017 Kapitel 7 » (`spec_test1.txt` l. 60) |
| **B2.4** | **La clause / les tableaux du ch. 7 donnant les CONSTRUCTIONS OPAQUES**, variantes **Leichtbau** ET **Massivbau** | Pour **mur, toiture, plancher**, dans les **deux** variantes : ordre des couches, **épaisseur, λ, ρ, cp de chaque couche** ; le **U déclaré** ; et **les coefficients de surface avec lesquels ce U est déclaré** | Lève le point `[REQUIS]` n° 2 de `test-1.spec.md` §8, aujourd'hui couvert seulement par présomption (ASHRAE 140:2023 Tables 7-2 / 7-27). Spec SIA : « Konstruktionen … Leichtbau / Massivbau » (`spec_test1.txt` l. 18-21) |
| **B2.5** | **La clause du ch. 7 donnant l'INFILTRATION** | Taux **et** unité (h⁻¹ ? m³/h ? à quelle référence de volume ?), caractère constant ou non, et si le débit est corrigé en densité/température | Lève le point `[REQUIS]` n° 4 de `test-1.spec.md` §8. Le modèle actuel pose 0,5 h⁻¹ sans source vérifiée (`sia4010_case_manifest.json` l. 558-563) |
| **B2.6** | **La clause du ch. 7 donnant les COEFFICIENTS DE TRANSFERT DE SURFACE** de la cellule (intérieur / extérieur, convectif seul vs combiné) | Les valeurs, et la règle de choix | SIA 4010 tab. 64 inscrit **explicitement la question ouverte** « Coefficient de transfert thermique externe ? » (`sia_4010_2023.txt` l. 2848-2849). Tranché provisoirement via ASHRAE 140:2023 Table 7-7 dans `test-1.spec.md` §3.1 — à confirmer à la source |
| **B2.7** | **La clause du ch. 7 donnant les APPORTS INTERNES et la VENTILATION** de la cellule | Puissance, répartition radiatif/convectif, horaire | La spec SIA donne 200 W constants (`spec_test1.txt` l. 45, 50-51) mais renvoie aussi au ch. 7 ; il faut vérifier la **fraction radiative** (le modèle pose 0,6 sans source vérifiée) |
| **B2.8** | **La clause du ch. 7 listant les CAS d'essai** et, si elles y figurent, **les valeurs de référence / plages de dispersion** | Liste des cas (600, 640, 900, 940, FF…) et tout tableau de résultats | Vérifier que les cas SIA (`spec_test1.txt` l. 64-66) sont bien un sous-ensemble ; et couvrir le point `[REQUIS]` n° 5 (bornes du cas 1E) au cas où |

## B.3 — PRIORITÉ 2 : utile au projet, non bloquant pour le Test 1

| # | Demandé | Pourquoi |
|---|---|---|
| **B3.1** | **Tableaux 11 à 20** (données d'entrée), avec leurs notes | SIA 380/2:2022 A.2.2 : « Les données d'entrée sont selon SN EN ISO 52016-1:2017, **tableaux 11 à 20** » (`sia_380_2_2022.txt` l. 2301-2302). Nécessaires aux tests 2 et suivants |
| **B3.2** | **L'ANNEXE NATIONALE SUISSE (SN)** à EN ISO 52016-1:2017 : page de titre + sommaire + tous les tableaux de valeurs standard | SIA 380/2 A.2.2 : « Les valeurs standard sont données dans **l'annexe nationale** à la norme SN EN ISO 52016-1:2017 » (`sia_380_2_2022.txt` l. 2302-2303). **Attention : cette annexe peut être un document séparé** — le préciser au collègue |
| **B3.3** | **§6.5.7.2 et §6.5.7.3** (propriétés des éléments opaques) | Remplacés par SIA 380/2 A.2.3 (`sia_380_2_2022.txt` l. 2317-2319) : il faut savoir ce qui est remplacé |
| **B3.4** | **Annexe G** (éléments transparents dynamiques) | SIA 380/2 A.2.4 s'appuie dessus (`sia_380_2_2022.txt` l. 2389) — pertinent pour le Test 2 (protections solaires) |
| **B3.5** | **§6.5.4.5** (puissance requise de base vs propre au système) | Cité par SIA 380/2 4.1.1.4 (`sia_380_2_2022.txt` l. 1216) |
| **B3.6** | **§7.2** (au-delà de 7.2.2) | SIA 380/2 2.2.2 : une méthode est admissible si elle répond au « chiffre 7.2 » (`sia_380_2_2022.txt` l. 1049) |

## B.4 — PRIORITÉ 3 : à tenter AVANT de solliciter le collègue (coût nul)

**`http://standards.iso.org/iso/52016/-1/ed-1`** — insert électronique ISO de l'édition 1,
**cité par la spécification SIA Test 1 elle-même** (`spec_test1.txt` l. 4) et par un
Anwenderbericht (`…\norme\anwender_test1_2.txt` l. 12). Il est établi qu'il contient le
fichier météo DRYCOLD. **Vérifier s'il contient aussi les classeurs d'entrées et/ou de
résultats des cas d'essai du chapitre 7.** Si oui, une bonne partie de B.2 tombe et la
demande de photos peut être réduite à B.1 + B2.2 + B2.3. **[I — à vérifier, coût nul]**

## B.5 — Ce que je ne sais PAS localiser (à demander explicitement)

- **Je ne sais pas dans quel chapitre ni à quelle page se trouve le « tableau 27 ».**
  Je sais seulement que SIA 4010 l'associe au chapitre 7 (`sia_4010_2023.txt` l. 2652-2653,
  2844-2850) et que SIA 380/2 place les tableaux 11 à 20 dans les données d'entrée
  (l. 2301) — ce qui rend cohérent, mais **ne prouve pas**, que le tableau 27 soit dans le
  ch. 7. **→ Demander d'abord B1.2 + B1.3 (sommaire + liste des tableaux), et attendre ces
  clichés avant de commander le reste si le budget de demandes est vraiment de un.**
- **Je ne sais pas si le chapitre 7 est bien le chapitre de validation** ni s'il contient
  réellement les données de la cellule d'essai, ou s'il ne fait que renvoyer à ASHRAE 140.
  **Si le ch. 7 se contente de renvoyer à ASHRAE 140 sans reproduire les valeurs**, alors
  la question 1 se déplace sur **ASHRAE 140:2017**, et il faudra acquérir cette édition
  (achat ASHRAE, ~quelques centaines de CHF) plutôt que d'insister sur l'ISO.
  **→ Demander que le collègue signale ce cas de figure explicitement.**
- **Je ne sais pas si l'annexe nationale suisse est reliée au même fascicule** ou publiée
  séparément (B3.2).

## B.6 — Message court, prêt à transmettre au collègue

> Norme : **SN EN ISO 52016-1:2017**. Photos de pages entières, en-têtes et pieds de page
> compris, notes de bas de tableau comprises, sans recadrage ni noir & blanc.
>
> **Étape 1 (à envoyer en premier, 6 clichés) :** page de titre ; table des matières
> complète ; liste des tableaux et des figures ; première page du chapitre 7 ; page(s) des
> références normatives où ASHRAE 140 apparaît avec son année.
>
> **Étape 2 (dès que l'étape 1 nous a permis de repérer les pages) :** chiffre 7.2.2 en
> entier ; tableau 27 en entier avec la page qui le précède ; toutes les pages du
> chapitre 7 qui donnent les données de la cellule d'essai — **vitrage** (épaisseurs, λ,
> ρ, cp, lame et son gaz/sa résistance, transmittance et facteur solaire, U et la phrase
> qui dit ce que ce U inclut), **constructions opaques légère et massive** (couches, λ, ρ,
> cp, U), **infiltration**, **coefficients de transfert de surface**, **apports internes**,
> **liste des cas d'essai**.
>
> **Si le chapitre 7 ne fait que renvoyer à ASHRAE 140 sans donner les valeurs :
> nous le dire — nous changerons de source.**
