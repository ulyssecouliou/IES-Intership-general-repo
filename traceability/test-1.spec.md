# Spec — Test SIA 4010 n° 1 : Tests de base de l'enveloppe du bâtiment

> Statut : **SPEC FIGÉE** sur le modèle d'entrée (révisé le 2026-07-31 — voir §10).
> La spécification SIA du Test 1 est dans le dépôt, lue et vérifiée mot pour mot.
> **Résolu le 2026-07-31** : les **valeurs numériques des constructions, du vitrage
> et de l'infiltration** — lecture directe de `BS EN ISO 52016-1:2017` §7.2
> (p. 122-134), qui **reproduit** ces valeurs. Elles font désormais foi dans
> `traceability/iso-52016-1-ch7-valeurs.spec.md`, avec citation de clause pour
> chaque grandeur. Le §4 du présent document reste comme historique.
>
> **Réserve 2017 vs 2023 levée** : ISO 52016-1:2017 cite **ASHRAE 140 de 2014**.
> L'exemplaire ASHRAE 140:**2023** de `/refs` porte des révisions postérieures et
> n'est donc **pas** la cible du Test 1 (sa Table 7-11 note elle-même
> « *Updates to Standard 140-2017 are highlighted in bold* »). Le coefficient de
> surface externe se lit maintenant au **tableau 25 d'ISO 52016-1** (h_ce = 20,
> h_lr;e = 4,14 W/(m²·K)), et non plus dans la Table 7-7 d'ASHRAE 140:2023 — les
> deux relèvent de conventions différentes et ne se mélangent pas.
>
> Sources en main :
> - `refs/SIA-4010-2023.pdf` — SIA 4010:2023 intégral, lu et vérifié.
> - `refs/SIA-380-2-2022.pdf` — SIA 380/2:2022 intégral (pas relu en détail pour ce test).
> - `SIA_4010_geteilter_Link/Test1/Spezifikation_Test1.pdf` — **spécification officielle
>   Test 1 (allemand), lue intégralement et vérifiée (2 pages)**.
> - `SIA_4010_geteilter_Link/Test1/Anwenderberichte/` — 4 rapports d'application des
>   programmes de référence (EnergyPlus, IDA-ICE, TAS, EXCEL 52016-1), lus.
> - `ASHRAE 140_2023_D_86892.pdf` — **texte intégral lu cette session via extraction**
>   (voir encart de vérification ci-dessous). Sections 7.2.1.9.3, Table 7-7, Table 7-2,
>   Table 7-27 et §7.2.2.2.x vérifiées mot pour mot.
>
> - **`BS EN ISO 52016-1:2017` §7.2, pages 122 à 134 — LUES le 2026-07-31.** Le
>   « tableau 27 » que cite SIA 4010 est la **liste des six cas d'essai**
>   (600, 640, 900, 940, 600FF, 900FF), pas un tableau de valeurs. Les tables 28 à
>   34 de cette norme **sont** la colonne `Daten EN ISO 52016-1 2017` du classeur
>   SIA — vérifié par recoupement direct (600FF : max 63,5 / min −16,9).
> - `SIA_4010_geteilter_Link/Test1/Resultaterfassung_Test1.xlsx` — présent et
>   audité (`AUDIT.md`, « GARDER — SIGNÉ », passe 4).
>
> Sources encore absentes, mais **plus bloquantes pour le Test 1** :
> - `NREL/TP-472-6231` (BESTEST 1995) et `ASHRAE 140-2014` : ISO 52016-1 §7.2 se
>   suffit à elle-même.
> - Annexe E d'ISO 52016-1 (p. 176-183), traitement des fenêtres : non capturée,
>   non nécessaire au déblocage.
> Provenance de chaque élément : `[SIA4010]` = SIA 4010:2023 vérifié / `[SpezT1]` =
> spécification Test 1 vérifiée / `[AnwT1]` = rapport d'application Test 1 vérifié /
> `[ASHRAE140:2023]` = ASHRAE 140:2023 vérifié mot pour mot sur extraction texte cette
> session / `[STD]` = connaissance standard à confirmer / `[REQUIS]` = valeur à obtenir
> d'une source encore absente/illisible.

> ---
> ## ✅ VÉRIFICATION — SESSION 2026-07-30 #1 (norm-analyst)
> - **`Spezifikation_Test1.pdf` lue intégralement** (sans le paramètre `pages`). Toutes
>   les citations `[SpezT1]` sont vérifiées mot pour mot.
> - **Les 4 Anwenderberichte Test 1 lus** : identifient les programmes de référence
>   (base du critère de plage du cas 1E) et confirment le fichier météo.
> - **CORRECTION MAJEURE du §6** : l'hypothèse d'un critère min–max uniforme pour tous
>   les cas est **FAUSSE**. Aucun critère de déviation pour 600/640/900/940/600FF/900FF ;
>   **seul le cas 1E** a un vrai critère pass/fail. Détail en §6.
> ---
> ## ✅ VÉRIFICATION — SESSION 2026-07-30 #2 (norm-analyst)
> - **`ASHRAE 140_2023_D_86892.pdf` LU cette session.** Le PDF (26 Mo) dépasse la limite
>   de l'outil Read et ses flux texte sont compressés (Grep inopérant). **Méthode** :
>   l'orchestrateur a extrait le texte intégral via `pdftotext` (outil Bash, **hors de
>   mes propres outils** ; extraction faite par l'orchestrateur, pas par moi) vers le
>   fichier texte brut :
>   `C:\Users\ulysse.couliou\.claude\jobs\d1486f24\tmp\ashrae140.txt` (27 379 lignes).
>   J'ai relu ce `.txt` moi-même et **vérifié chaque chiffre / chaque phrase citée** aux
>   emplacements suivants (numéros de ligne du `.txt`) :
>   - Table 7-7 (l. 2999-3019) — coefficients de surface externes Case 600.
>   - §7.2.1.9.3 (l. 3021-3057) — procédure de choix convectif seul / combiné.
>   - Informative Note 900-series (l. 4363-4368) + §7.2.2.2.1.1 (l. 4373-4376).
>   - Table 7-2 (l. 2774-2801) et Table 7-27 (l. 4386-4418) — propriétés matériaux.
>   - Tables informatives 7-3 (l. 2820-2847) et 7-28 (l. 4468+) — conductances calculées.
> - **Limite de la méthode d'extraction** : `pdftotext` ne préserve **pas** la mise en
>   forme grasse. Or la note a de la Table 7-7 dit « Changes to Standard 140-2017 are
>   highlighted in bold ». Je **ne peux donc pas savoir** quelles valeurs ont changé
>   entre 2017 et 2023. Conséquence directe traitée en §4.
> - **RÉSOLU** : coefficient de transfert thermique externe → §3 et §8 pt 1.
> - **NON résolu mais mieux documenté** : valeurs numériques des constructions → §4.
> ---

## 1. Objet
Vérifier que le moteur de simulation thermique dynamique reproduit correctement la
physique de l'enveloppe (transmission, inertie thermique, gains solaires par les
vitrages, infiltration, flottement libre de la température) sur la cellule de test
normalisée ASHRAE 140 / EN ISO 52016-1 ch. 7, en variantes légère (Leichtbau) et
lourde (Massivbau). Aucun système technique réel n'intervient : le chauffage et le
refroidissement sont modélisés par des **éléments idéaux**. `[SIA4010]` `[SpezT1]`

## 2. Classes de validation concernées
Le Test 1 est requis dans **toutes les classes sauf la classe 5**. `[SIA4010 §4.5, tab. 63 — confirmé]`

| Classe | Tests requis | Test 1 requis ? |
|---|---|---|
| 1A | 1 + 2A | ✅ |
| 1B | 1 + 2 | ✅ |
| 2A | 1, 2A, 3A–F | ✅ |
| 2B | 1 à 3 | ✅ |
| 3 | 1, 4 à 6 | ✅ |
| 4A | 1, 2A, 3A–F, 4 à 7 | ✅ |
| 4B | 1 à 7 | ✅ |
| 5 | 7 | ❌ |

Conséquence produit : le Test 1 est le premier à implémenter (tranche verticale
Phase 1) car il conditionne 7 des 8 classes.

## 3. Référentiel normatif
- Cellule de test selon **SN EN ISO 52016-1:2017, §7.2.2**, correspondant à
  **ASHRAE 140:2017**. `[SIA4010 §4.2 tab. 62 ; Annexe A tab. 64, ligne 1 — confirmé]`
  La spec Test 1 confirme : « Testraum gemäss ISO EN 52016:2017 (Basis ASHRAE 140:2017) ».
  `[SpezT1 — confirmé mot pour mot]`
- Étendue : cas de base selon **EN ISO 52016-1:2017, chapitre 7** (« Konstruktionen /
  Infiltration / Verglasung : ISO EN 52016:2017 Kapitel 7 »). `[SpezT1 — confirmé]`
  Le SIA 4010 tab. 64 (ligne 1) mentionne en outre le tableau 27 d'EN ISO 52016-1 et la
  possibilité d'ajouter des cas complémentaires ASHRAE 140 « si les aspects souhaités ne
  sont pas couverts ». `[SIA4010 tab. 64 — confirmé]`
- Module DPEB associé : **M2-2**. `[SIA4010 tab. 64 — confirmé]`

### 3.1 Coefficient de transfert thermique externe — ✅ RÉSOLU (session 2)
La question était inscrite par la norme elle-même dans la colonne « Commentaires » de la
ligne Test 1 du tableau 64 (« Coefficient de transfert thermique externe ? »), **non
tranchée** par SIA 4010 ni par la spec Test 1 ni par les Anwenderberichte. `[SIA4010 tab. 64 — confirmé]`
Elle est **tranchée par la source amont ASHRAE 140:2023**, référentiel de la cellule.

**Procédure normative** — ASHRAE 140:2023 **§7.2.1.9.3** « Alternative Constant Convective
and Combined (Radiative and Convective) Surface Coefficients », vérifiée mot pour mot
(`.txt` l. 3021-3044) : `[ASHRAE140:2023 §7.2.1.9.3 — confirmé]`
- **(a)** Si le logiciel testé calcule **lui-même** les coefficients convectifs extérieurs
  **ET** l'échange radiatif infrarouge, tous deux **variables au pas de temps**, alors ces
  calculs s'appliquent et le tableau 7-7 est **ignoré** (« those calculations shall be
  applied; skip the remaining instructions »).
- **(b)** Sinon, la Table 7-7 s'applique :
  - **(b.1)** logiciel qui calcule l'échange IR variable dans le temps **mais pas** les
    coefficients convectifs → appliquer le coefficient **convectif seul** `hconv,ext`.
  - **(b.2)** logiciel qui ne calcule **ni** convection **ni** IR variables → appliquer le
    coefficient **combiné** `hcomb,ext`.
  - **(b.3)** d'autres valeurs (non spécifiées) ne sont pas interdites s'il existe une base
    mathématique/physique/logique, appliquées de façon cohérente sur tous les cas et
    documentées dans le Standard Output Report (Annexe A2). `[ASHRAE140:2023 §7.2.1.9.3 — confirmé]`

**Valeurs — Table 7-7** « Alternative Constant Exterior Convective and Combined Surface
Coefficients for Each Surface Type, Case 600 », en **W/(m²·K)**, vérifiées mot pour mot
(`.txt` l. 2999-3012) : `[ASHRAE140:2023 Table 7-7 — confirmé]`

| Type de surface | `hconv,ext` (convectif seul) | `hcomb,ext` (combiné conv.+rad.) |
|---|---|---|
| Walls (murs) | **11.9** | **21.6** |
| Roof (toiture) | **14.4** | **21.8** |
| Raised floor (plancher surélevé) | **0.8** | **5.2** |
| Windows (fenêtres) | **8.0** | **17.8** |

- Ces coefficients sont **calculés pour une vitesse de vent = 0** (note c de la Table 7-7,
  `.txt` l. 3017 : « Calculated for wind speed = 0 as described in Section 7.2.1.9 »).
  `[ASHRAE140:2023 Table 7-7 note c — confirmé]`
- La note a de la Table 7-7 (`.txt` l. 3015) indique « Changes to Standard 140-2017 are
  highlighted in bold ». **L'extraction texte ne préserve pas le gras** : je ne peux donc
  pas savoir si l'une de ces valeurs a changé entre ASHRAE 140:2017 (version citée par SIA
  4010) et 2023 (version en main). Réserve à garder à l'esprit ; cf. §4. `[ASHRAE140:2023 — confirmé, gras non exploitable]`

**Application aux cas SIA Test 1** — la Table 7-7 est définie pour le Case 600. Elle
s'applique **à l'identique** aux cas lourds car les **textures de surface** (donc les
coefficients de surface) sont **inchangées** entre 600-series et 900-series :
- Informative Note (`.txt` l. 4363-4368) : « For Cases 900 through 950 and 985, the
  high-mass cases are the same as the corresponding low-mass 600-series cases except that
  material properties are taken from Table 7-27 rather than Table 7-2 … the roof properties
  **and all surface textures are unchanged**. » `[ASHRAE140:2023 — confirmé]`
- §7.2.2.2.1.1 (`.txt` l. 4373-4376) : « The surface textures of Sections 7.2.1.9.2 and
  7.2.1.10.2 (Case 600) **shall continue to apply**. » `[ASHRAE140:2023 §7.2.2.2.1.1 — confirmé]`
- Confirmation numérique : les tables informatives des conductances donnent le **même**
  coefficient de surface extérieur pour mur (21.6), plancher (5.2), toit (21.8) en cas
  léger (Table 7-3, `.txt` l. 2830/2838/2846) **et** lourd (Table 7-28, `.txt` l. 4478/4486).
  `[ASHRAE140:2023 Tables 7-3 & 7-28 — confirmé]`
- Les cas **640/940** (réduit nocturne) sont modélisés « exactly the same as » 600/900
  hormis les consignes / matériaux (§7.2.2.2.5 pour 940, `.txt` l. 4457-4459) : coefficients
  de surface **inchangés**. `[ASHRAE140:2023 §7.2.2.2.5 — confirmé]`
- **Interprétation (marquée comme telle)** : les cas **600FF / 900FF** (flottement libre)
  ne modifient que le régime de régulation (pas de consigne), non la géométrie ni les
  textures de surface ; la Table 7-7 s'y applique donc **identiquement**. Non recontrôlé
  ligne à ligne dans le `.txt` mais cohérent avec la logique « FF = même bâtiment sans
  HVAC ». À confirmer si un doute apparaît.

**Conclusion §3.1** : pour la cellule Test 1 (cas 600/640/600FF/900/940/900FF/1E), les
coefficients de surface externes sont ceux de la **Table 7-7**, vent nul, **le choix de la
colonne (`hconv,ext` seul vs `hcomb,ext` combiné) dépendant de l'algorithme du logiciel**
selon §7.2.1.9.3 (a)/(b). **La valeur EXACTE à retenir pour ce projet dépend donc de
l'algorithme de convection de surface configuré dans ApacheSim/IESVE** (calcule-t-il la
convection variable au pas de temps ? l'échange IR ?). Ce point précis est renvoyé à
`ve-adapter-engineer` — cf. §8 pt 6. `[ASHRAE140:2023 §7.2.1.9.3 — confirmé ; interprétation ApacheSim non tranchée]`

## 4. Grandeurs d'entrée (définition de la cellule de test) `[SpezT1 — confirmé]`
Zone unique, orientation **Sud** (fenêtres au Sud).

**Site & météo**
- Site : **Denver, CO**.
- Fichier météo : **DRYCOLD.TMY (BESTEST) Denver, CO**, jeu de données EN ISO 52010-1
  publié avec EN ISO 52016-1 (`http://standards.iso.org/iso/52016/-1/ed-1`). `[SpezT1]`
  Confirmé par les Anwenderberichte (« Klimadaten aus Original-Datei nach SN EN ISO
  52010-1 … Denver, CO »). `[AnwT1]`
  ⚠ Note documentaire : deux Anwenderberichte qualifient à tort ce climat de « hot-dry »
  et un de « dry cold » ; la spec SIA fait foi = **DRYCOLD** (froid sec). `[SpezT1]`
- Période de simulation : **1.1.2011 – 31.12.2011** (année entière). `[SpezT1]`

**Géométrie** `[SpezT1, Figure 2]`
- Dimensions intérieures : **6,0 m × 8,0 m**, hauteur **2,7 m**.
- Surface nette : **48 m²**.
- Deux fenêtres au Sud, **2,0 m × 3,0 m chacune** (positions cotées sur la Figure 2 :
  allèges 0,2 m / 0,5 m, trumeaux 0,5 m et 1,0 m).

**Constructions** `[SpezT1]`
- Variantes **Leichtbau (légère)** et **Massivbau (lourde)** selon EN ISO 52016-1 ch. 7.
- Valeurs numériques (compositions de couches, U, capacités thermiques) : **NON données
  par la spec SIA** — renvoi formel à **EN ISO 52016-1 ch. 7** (base ASHRAE 140:2017).
  **Statut : `[REQUIS]` — reste ouvert** (EN ISO 52016-1:2017 toujours absent de `/refs`).
- **Piste forte documentée cette session (présumée, PAS figée)** : ASHRAE 140:2023
  fournit ces mêmes propriétés matériaux, vérifiées mot pour mot :
  - **Table 7-2** « Fundamental Material Thermal Property Specifications Low-Mass Case »
    (`.txt` l. 2774-2801) — cas **léger** : `[ASHRAE140:2023 Table 7-2 — confirmé]`

    | Couche (intérieur → extérieur) | k [W/(m·K)] | ép. [m] | U [W/(m²·K)] | R [m²·K/W] | ρ [kg/m³] | cp [J/(kg·K)] |
    |---|---|---|---|---|---|---|
    | Mur — Plasterboard | 0.16 | 0.012 | 13.333 | 0.075 | 950 | 840 |
    | Mur — Fiberglass quilt | 0.04 | 0.066 | 0.606 | 1.650 | 12 | 840 |
    | Mur — Wood siding | 0.14 | 0.009 | 15.556 | 0.064 | 530 | 900 |
    | Plancher — Timber flooring | 0.14 | 0.025 | 5.600 | 0.179 | 650 | 1200 |
    | Plancher — Insulation | 0.04 | 1.003 | 0.040 | 25.075 | 0 (a) | 0 (a) |
    | Toit — Plasterboard | 0.16 | 0.010 | 16.000 | 0.063 | 950 | (voir note) |
    | Toit — Fiberglass quilt | 0.04 | 0.1118 | 0.358 | 2.794 | 12 | (voir note) |
    | Toit — Roofdeck | 0.14 | 0.019 | 7.368 | 0.136 | 530 | (voir note) |

    (a) « Underfloor insulation has the minimum density and specific heat the program being
    tested will allow, but not < 0 » (`.txt` l. 2801). Les cp du toit sont mal alignés dans
    l'extraction texte (colonne décalée l. 2779-2786) — **à revérifier** contre EN ISO
    52016-1 ou une relecture PDF plus fiable avant usage. `[ASHRAE140:2023 — confirmé sauf cp toit à revérifier]`
    - Confirme l'indice `[AnwT1]` du rapport EXCEL : plancher isolé ~**1 m** (1.003 m léger).
  - **Table 7-27** « Fundamental Material Thermal Property Specification, High-Mass Case »
    (`.txt` l. 4386-4418) — cas **lourd** : `[ASHRAE140:2023 Table 7-27 — confirmé]`

    | Couche (intérieur → extérieur) | k [W/(m·K)] | ép. [m] | U [W/(m²·K)] | R [m²·K/W] | ρ [kg/m³] | cp [J/(kg·K)] |
    |---|---|---|---|---|---|---|
    | Mur — Concrete Block | 0.51 | 0.100 | 5.100 | 0.196 | 1400 | 1000 |
    | Mur — Foam Insulation | 0.04 | 0.0615 | 0.651 | 1.537 | 10 | 1400 |
    | Mur — Wood Siding | 0.14 | 0.009 | 15.556 | 0.064 | 530 | 900 |
    | Plancher — Concrete Slab | 1.13 | 0.080 | 14.125 | 0.071 | 1400 | 1000 |
    | Plancher — Insulation | 0.04 | 1.007 | 0.040 | 25.175 | 0 (b) | 0 (b) |

    Toiture **identique** au cas léger (note c, `.txt` l. 4418 : « The high-mass case roof
    is the same as the low-mass case roof »). (a) épaisseur d'isolant plancher légèrement
    ajustée (1.007 m) pour égaliser les R totaux. (b) densité/cp minimaux autorisés, ≥ 0.
    `[ASHRAE140:2023 Table 7-27 — confirmé]`

  - **⚠ DEUX RÉSERVES EXPLICITES — pourquoi ces valeurs restent `[REQUIS]` et non figées :**
    1. **Version 2017 vs 2023** : SIA 4010 cite formellement **EN ISO 52016-1:2017** (base
       **ASHRAE 140:2017**). Nous n'avons en main que **ASHRAE 140:2023**. Ces tables sont
       présumées équivalentes mais **non prouvées identiques** à la source citée.
    2. **Gras non préservé** : la note a de la Table 7-7 (et par extension le document 2023)
       signale « Changes to Standard 140-2017 are highlighted in bold ». L'extraction
       `pdftotext` **efface le gras** : impossible de savoir quelles valeurs ont changé
       entre 2017 et 2023. Un chiffre 2023 peut différer de la valeur 2017 réellement visée
       par SIA 4010.
    → **Ces tables sont un point de départ documenté à très forte présomption, PAS une
    preuve.** À confirmer contre **EN ISO 52016-1:2017 tab. 27** (absent de `/refs`) avant
    figeage. Statut maintenu **`[REQUIS]`**. `[ASHRAE140:2023 — présomption, à confirmer c. EN ISO 52016-1:2017]`

**Vitrage** `[SpezT1]`
- Selon EN ISO 52016-1 ch. 7. Valeurs (g, U, transmission solaire) **NON données** par
  la spec SIA — renvoi à EN ISO 52016-1 ch. 7. `[REQUIS]`
  Note : ASHRAE 140:2023 §7 documente aussi la fenêtre (mêmes réserves version 2017/2023
  que ci-dessus) ; **non extrait/vérifié cette session** — à traiter dans une passe dédiée.

**Infiltration / ventilation** `[SpezT1]`
- Ventilation mécanique (« Lüftung ») : **aucune** (« - »).
- Infiltration : selon EN ISO 52016-1 ch. 7. Valeur numérique (taux) **NON donnée** par
  la spec SIA. `[REQUIS]` (ASHRAE 140:2023 §7 la documente ; non extrait cette session.)

**Protection solaire** `[SpezT1]`
- **Aucune** (« Ohne »), sauf cas 1E (store tissu, cf. §7).

**Apports internes** `[SpezT1 — confirmé]`
- Personnes : **aucune** (Anzahl : Keine).
- Équipements : **200 W au total**, profil **constant 24 h**, présent **toute l'année
  (1.1.–31.12.)**.
- Éclairage : **0 W/m²**.

**Consignes (éléments idéaux, pas de HVAC réel — « HLK-Anlage : Keine vorhanden »)** `[SpezT1]`
- Chauffage : élément idéal, consigne **20 °C**.
  - Cas 640/940 (réduit nocturne piloté) : **20 °C de 07:00 à 23:00**, **10 °C de 23:00
    à 07:00**.
- Refroidissement : élément idéal, consigne **27 °C**.

## 5. Grandeurs de sortie contrôlées `[SpezT1 — confirmé]`
Jeux de données annuels à transférer dans **`Resultaterfassung_Test1.xlsx`** :
1. Cas **600, 640, 900, 940 et 1E** : **puissance horaire** de chauffage et de
   refroidissement.
2. **Tous les cas sauf 1E** : **température horaire** de l'air et **température
   opérative** horaire.

Résultats de test dérivés (calculés automatiquement à partir des jeux annuels) :
1. Énergie sensible **mensuelle et annuelle** de chauffage [kWh].
2. Énergie sensible **mensuelle et annuelle** de refroidissement [kWh].
3. **Moyennes mensuelles** de la température opérative.
4. Besoins horaires de chauffage/refroidissement du **4 janvier**.
5. Besoins horaires de chauffage/refroidissement du **27 juillet**.
6. **Besoins horaires maximaux** de chauffage et de refroidissement.
7. Température opérative horaire **max / min / moyenne annuelle** — cas **600FF et 900FF**.
8. Moyennes horaires de la température opérative du **4 janvier** — cas **600FF et 900FF**.

## 6. Critère d'acceptation / tolérance `[SpezT1 — CORRIGÉ session 1]`
> Correction majeure : l'ancien §6 supposait un critère min–max uniforme pour tous les
> cas. **C'est faux.** La spec Test 1 (rubrique « Testkriterien ») dit littéralement :

- Cas **600, 640, 900, 940, 600FF et 900FF** : les résultats sont **affichés à titre
  comparatif** avec les résultats de référence. **« Es gibt dafür kein
  Abweichungskriterium »** — il n'existe **AUCUN critère de déviation** (pas de
  pass/fail). `[SpezT1 — confirmé mot pour mot]`
- Cas **1E** uniquement : **« Resultate für den Test 1E müssen im Streubereich der
  enthaltenen Referenzprogramme liegen »** — les résultats **doivent tomber dans la
  plage de dispersion (Streubereich) des programmes de référence inclus**. C'est le
  **seul vrai critère pass/fail** du Test 1. `[SpezT1 — confirmé mot pour mot]`

Programmes de référence inclus (base de la plage de dispersion du cas 1E), identifiés
par les Anwenderberichte Test 1 : `[AnwT1 — confirmé]`
- **EnergyPlus 9.1.0 / OpenStudio**
- **IDA ICE 5.0 Beta 23**
- **TAS (EDSL)**
- **EXCEL SN EN ISO 52016-1** (E4Tech, cadre pré-étude SIA 2044, complété par G. Zweifel)

→ Conséquences pour `engine/` :
- Ne PAS implémenter de test pass/fail sur 600/640/900/940/600FF/900FF : produire la
  **représentation comparative** vs référence, sans verdict.
- Implémenter le **seul** test binaire sur le cas **1E** : « valeur ∈ [min, max] des
  programmes de référence » par grandeur contrôlée. Les bornes (min/max de la dispersion)
  viennent de `Resultaterfassung_Test1.xlsx`. `[REQUIS — Excel d'éval absent]`
- Note : ce mode « transfert dans l'Excel qui génère la comparaison » est cohérent avec
  SIA 4010 §2.5 et §4.4 (fichier d'évaluation sur www.sia.ch/sia4010). `[SIA4010 — confirmé]`

## 7. Liste des cas de test `[SpezT1 — confirmé]`
**Cas principaux** (selon EN ISO 52016-1 ch. 7) :
| Cas | Construction | Régime |
|---|---|---|
| 600 | Leichtbau (légère) | chauffage 20 °C / refroid. 27 °C |
| 640 | Leichtbau (légère) | réduit nocturne (20 °C 07–23 h / 10 °C 23–07 h) / refroid. 27 °C |
| 600FF | Leichtbau (légère) | flottement libre (free-float) |
| 900 | Massivbau (lourde) | chauffage 20 °C / refroid. 27 °C |
| 940 | Massivbau (lourde) | réduit nocturne (20 °C 07–23 h / 10 °C 23–07 h) / refroid. 27 °C |
| 900FF | Massivbau (lourde) | flottement libre (free-float) |

**Cas additionnel avec critère** :
| Cas | Définition |
|---|---|
| 1E | **Cas diagnostic 1D** + protection solaire par **store tissu (Stoffmarkise)** selon le **test diagnostic 2 E1**. Seul cas soumis à un critère pass/fail (§6). |

**Cas diagnostiques (transition Test 1 → Test 2)** — résultats à livrer : jeux annuels
avec puissance horaire chauffage/refroidissement. `[SpezT1 — confirmé]`
| Cas | Définition |
|---|---|
| Diag 1A | Cas 600 avec **données climatiques Zürich-Kloten** |
| Diag 1B | Diag 1A + **nouvelle fenêtre** selon spécification Test 2 |
| Diag 1C | Diag 1B + **infiltration ajustée** selon spécification Test 2 |
| Diag 1D | Diag 1C + **utilisation (personnes/équipements/éclairage) selon SIA 2024**, cf. spécification Test 2 |

→ Le Test 1 est donc un **sous-ensemble précis** (léger 600/640/600FF + lourd
900/940/900FF + 1E + diagnostics 1A–1D), **pas** l'intégralité de la suite ASHRAE 140.

## 8. Zones d'incertitude (à lever avant "done")
1. **Coefficient de transfert thermique externe** — ✅ **RÉSOLU** (session 2).
   Coefficients de la Table 7-7 (vent nul) ; choix colonne selon §7.2.1.9.3 (a)/(b).
   Cf. §3.1. **Reste dépendant** de l'algorithme ApacheSim → renvoyé au pt 6 ci-dessous.
   `[ASHRAE140:2023 §7.2.1.9.3 + Table 7-7 — confirmé]`
2. **Valeurs numériques des constructions** (couches, U, capacités) légère/lourde.
   **Toujours `[REQUIS]`** : piste forte via ASHRAE 140:2023 Table 7-2 / 7-27 (§4) mais
   **non figée** (réserves version 2017/2023 + gras non préservé). À confirmer c. EN ISO
   52016-1:2017 tab. 27 (absent de `/refs`).
3. **Vitrage** (U, g, transmission solaire). `[REQUIS — EN ISO 52016-1 ch. 7 absent ;
   documenté aussi par ASHRAE 140:2023 §7 mais non extrait cette session]`
4. **Taux d'infiltration** exact. `[REQUIS — idem pt 3]`
5. **Bornes de dispersion du cas 1E** (min/max des programmes de référence, par grandeur).
   `[REQUIS — Resultaterfassung_Test1.xlsx absent]`
6. **Réglages ApacheSim/VE** — **POINT PRÉCISÉ (session 2)** :
   - Déterminer si le modèle de convection de surface extérieure d'ApacheSim/IESVE calcule
     la convection **variable au pas de temps** et/ou l'échange **IR** variable → cela
     décide, via ASHRAE 140:2023 §7.2.1.9.3, quelle branche s'applique :
     - convection + IR variables calculés → laisser ApacheSim faire (branche a) ;
     - IR variable seul → forcer `hconv,ext` (11.9 / 14.4 / 0.8 / 8.0) ;
     - ni l'un ni l'autre → forcer `hcomb,ext` (21.6 / 21.8 / 5.2 / 17.8).
   - Vérifier que la valeur/le mode retenu est appliqué **de façon cohérente** sur tous les
     cas et documenté (exigence §7.2.1.9.3 b.3).
   - Autres conventions cellule à cadrer : distribution du rayonnement solaire intérieur
     (réflexion interne 0.4 notée par IDA-ICE `[AnwT1]`), couplage au sol via le plancher
     isolé ~1 m (hypothèse vent nul / air sous plancher = ambiant, ASHRAE 140:2023
     Informative Note l. 2803-2812).
   → **À cadrer avec `ve-adapter-engineer`.** `[ASHRAE140:2023 — cadre confirmé ; réglage ApacheSim à déterminer]`

**Points désormais RÉSOLUS** (retirés des incertitudes) :
- Coefficient de transfert thermique externe → §3.1 (session 2). `[ASHRAE140:2023]`
- Étendue exacte des cas → §7. `[SpezT1]`
- Fichier météo de référence → DRYCOLD.TMY (BESTEST) Denver, période 2011. `[SpezT1]`
- Structure du critère d'acceptation → §6 (aucun critère pour les cas de base, plage de
  dispersion pour 1E seul). `[SpezT1]`
- Géométrie, apports internes, consignes → §4. `[SpezT1]`

Point non bloquant confirmé : le « bâtiment exemple » (DXF/IFC + charges) de SIA 4010 §4.3
ne sert **qu'aux tests 4 à 7** — sans effet sur le Test 1.

## 9. Citations
> SIA 4010 : lecture intégrale de `refs/SIA-4010-2023.pdf`. Spécification Test 1 :
> lecture intégrale de `SIA_4010_geteilter_Link/Test1/Spezifikation_Test1.pdf` (2 pages).
> Anwenderberichte : 4 PDF Test 1 lus. ASHRAE 140:2023 : lu cette session via extraction
> texte (`pdftotext`, par l'orchestrateur ; fichier `.txt` relu et vérifié par moi).
> EN ISO 52016-1:2017 : toujours absent de `/refs` — non vérifiable.
- SIA 4010:2023 : §2.5, §4.2 tab. 62, §4.3, §4.4, §4.5 tab. 63, Annexe A tab. 64 ligne 1
  (incl. question ouverte « coefficient de transfert thermique externe »). — **confirmées**.
- `Spezifikation_Test1.pdf` (SIA 4010 Test 1) : Standort/Klima/Simulationsperiode,
  Gebäude & Figure 2 (géométrie), Raum (constructions, infiltration, Wärmeabgabe,
  Kälteabgabe, Wärmeeinträge, Verglasung, Sonnenschutz, HLK), Testfälle, Zu liefernde
  Resultate, Testresulate, **Testkriterien**, Diagnosefälle. — **confirmées mot pour mot**.
- Anwenderberichte Test 1 : EnergyPlus 9.1.0/OpenStudio, IDA ICE 5.0 Beta 23, TAS (EDSL),
  EXCEL SN EN ISO 52016-1 (E4Tech/Zweifel). — **confirmés** (programmes de référence, météo).
- **ASHRAE 140:2023** (`ASHRAE 140_2023_D_86892.pdf`, via extraction texte
  `C:\Users\ulysse.couliou\.claude\jobs\d1486f24\tmp\ashrae140.txt`) :
  §7.2.1.9.3, Table 7-7 (+ notes a et c), Informative Note 900-series, §7.2.2.2.1.1,
  §7.2.2.2.5, Table 7-2, Table 7-27, Tables informatives 7-3 & 7-28. — **confirmées mot
  pour mot** ; réserves : cp du toit (Table 7-2) mal alignés à revérifier ; gras (deltas
  2017↔2023) non préservé par l'extraction.
- EN ISO 52016-1:2017 §7.2.2, ch. 7 (tab. 27) : *absent de `/refs` — non vérifiable*.
  C'est la source formellement citée par SIA 4010 pour les valeurs de §4 ; son absence
  maintient ces valeurs en `[REQUIS]` malgré la piste ASHRAE 140:2023.

## 10. Chemin pour passer de BROUILLON à SPEC FIGÉE
- [x] Spécification du Test 1 lue et vérifiée (`Spezifikation_Test1.pdf`).
- [x] Structure du critère d'acceptation corrigée et figée (§6).
- [x] Liste des cas, météo, géométrie, apports, consignes figées (§4, §7).
- [x] **Coefficient de transfert thermique externe tranché** (ASHRAE 140:2023 §7.2.1.9.3
      + Table 7-7, §3.1) — reste à traduire en réglage ApacheSim concret (§8 pt 6,
      `ve-adapter-engineer`).
- [x] Valeurs numériques constructions/vitrage/infiltration **confirmées c. EN ISO
      52016-1:2017 ch. 7** — **RÉSOLU le 2026-07-31** par lecture directe des
      pages 122 à 134 de `BS EN ISO 52016-1:2017` §7.2. Le chapitre **reproduit**
      les valeurs au lieu de renvoyer à ASHRAE 140. Tout est consigné dans
      `traceability/iso-52016-1-ch7-valeurs.spec.md` : géométrie (tab. 22),
      constructions légère et lourde couche par couche (tab. 23 et 24), vitrage
      (§7.2.2.6 : **U_W = 2,984 W/(m²·K)**, g_gl;n = 0,789, R_se;v = 0,04,
      R_si;v = 0,13, F_fr = 0), coefficients de surface (tab. 25), infiltration
      (**0,41 h⁻¹ en continu**, sans système de ventilation), apports internes
      (200 W en continu), consignes (20/27 continu ; 10/27 la nuit en
      intermittent), α_sol, F_sky, fractions convectives, capacités.
      La réserve **2017 vs 2023 est levée** : l'exemplaire cite **ASHRAE 140 de
      2014**, donc les valeurs d'ASHRAE 140:2023 de `/refs` ne sont PAS la cible —
      elles portent des révisions postérieures. Le « tableau 27 » que cite
      SIA 4010 est la **liste des six cas d'essai**, pas un tableau de valeurs.
- [x] Bornes de dispersion du cas 1E (`Resultaterfassung_Test1.xlsx`) — extraites
      et auditées (`AUDIT.md`, verdict « GARDER — SIGNÉ », passe 3), puis
      complétées par la Table 31 en passe 4.

> Décision de statut, révisée le **2026-07-31** : **SPEC FIGÉE** sur le modèle
> d'entrée. Les six cases de ce chemin sont cochées. `BS EN ISO 52016-1:2017` §7.2
> a été lue directement (p. 122-134) et **reproduit** toutes les valeurs
> physiques : le modèle d'entrée du Test 1 est désormais entièrement défini, avec
> citation de clause pour chaque grandeur.
>
> Deux réserves de ce document sont **caduques** : la piste ASHRAE 140:2023 n'est
> plus nécessaire (ISO se suffit), et la question 2017 vs 2023 est tranchée — ISO
> 52016-1:2017 cite **ASHRAE 140 de 2014**, donc l'exemplaire 2023 de `/refs`
> porte des révisions postérieures et n'est **pas** la cible. Le §4 de ce document
> reste valable comme historique, mais `iso-52016-1-ch7-valeurs.spec.md` fait
> désormais foi sur les valeurs.
>
> Ce qui reste ouvert ne concerne plus le modèle d'entrée mais son **exécution** :
> le réglage ApacheSim correspondant aux coefficients du tableau 25 (§8 pt 6), la
> variable IESVE à lier pour la température opérative
> (`traceability/temperature-operative.spec.md`), et les six cas encore à générer
> et simuler.
