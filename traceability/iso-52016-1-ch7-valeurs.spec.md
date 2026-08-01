# Spec — modèle d'entrée du Test SIA 4010 n° 1, d'après EN ISO 52016-1:2017 §7.2

> Statut : **SPEC FIGÉE** sur les valeurs ci-dessous.
> Source : **BS EN ISO 52016-1:2017**, clause **7 « Quality control »**, §7.2
> « Hourly method: verification cases », pages 122 à 134.
> Lue le 2026-07-31 sur l'exemplaire consulté par le commanditaire (accès
> institutionnel BSI). Pages capturées et relues : 122 à 134 intégralement.
>
> Ce document lève **trois des points `[REQUIS]`** que `traceability/test-1.spec.md`
> §10 laissait ouverts depuis le début du projet : valeurs de constructions,
> valeurs de vitrage, valeur d'infiltration.

---

## 1. Ce que ce chapitre est, et pourquoi il fait autorité ici

`§7.2.2.1`, NOTE : « *The verification cases are based on the BESTEST 600 and 900
cases as described in ANSI/ASHRAE 140* ».

La spécification SIA du Test 1 renvoie formellement à « ISO EN 52016:2017
Kapitel 7 » pour la Verglasung, la Lüftung, les Wärmeeinträge et les
Testresultate. Ce chapitre 7 **reproduit** les valeurs au lieu de se contenter de
renvoyer à ASHRAE 140 — c'était la question ouverte, elle est tranchée.

Point de version acté : l'exemplaire cite **ASHRAE 140 de 2014** dans ses
références normatives. Les valeurs d'ASHRAE 140:**2023** (`refs/`) ne sont donc
**pas** la cible du Test 1 : elles portent des révisions postérieures, sa
Table 7-11 note elle-même « *Updates to Standard 140-2017 are highlighted in
bold* ».

---

## 2. Géométrie — `§7.2.2.2`, figure 2, tableau 22

Zone unique, **8,0 × 6,0 × 2,7 m**, volume **129,6 m³**.
Deux fenêtres de **3,0 × 2,0 m** en façade, allège **0,2 m**, linteau **0,5 m**,
retours latéraux 0,5 m et entraxe 1,0 m.

| Composant | Aire [m²] |
|---|---|
| Mur (façade fenêtrée) | 9,6 |
| Mur (gauche) | 16,2 |
| Mur (droite) | 16,2 |
| Mur (arrière) | 21,6 |
| Fenêtre | 12,0 |
| Plancher | 48,0 |
| Plafond | 48,0 |

« *Unless otherwise stated, all constructions are external (outdoor).* »

---

## 3. Constructions opaques — `§7.2.2.3`, tableaux 23 et 24

Ordre des couches : **intérieur → extérieur**.

### 3.1 Cas LÉGER (tableau 23)

| Élément | Couche | D [m] | λ [W/(m·K)] | R [m²K/W] | κ [J/(m²K)] | ρ [kg/m³] | c [J/(kg·K)] |
|---|---|---|---|---|---|---|---|
| Mur ext. | Plasterboard | 0,012 | 0,160 | 0,075 | 9576 | 950 | 840 |
| | Fiberglass quilt | 0,066 | 0,040 | 1,650 | 665 | 12 | 840 |
| | Wood siding | 0,009 | 0,140 | 0,064 | 4293 | 530 | 900 |
| | **total surf-surf** | | | **1,789** | | | |
| Plancher | Timber flooring | 0,025 | 0,140 | 0,179 | 19500 | 650 | 1200 |
| | Insulation ᵃ | 1,003 | 0,040 | 25,075 | 0 ᵇ | 0 ᵇ | 0 ᵇ |
| | **total surf-surf** | | | **25,254** | | | |
| Toiture | Plasterboard | 0,010 | 0,160 | 0,063 | 7980 | 950 | 840 |
| | Fiberglass quilt | 0,1118 | 0,040 | 2,794 | 1127 | 12 | 840 |
| | Roofdeck | 0,019 | 0,140 | 0,136 | 9063 | 530 | 900 |
| | **total surf-surf** | | | **2,992** | | | |

Classes ISO 52016-1 : mur « Very light / Evenly (D) », plancher « Very light /
Internal (I) », toiture « Very light / Evenly (D) ».

### 3.2 Cas LOURD (tableau 24)

| Élément | Couche | D [m] | λ | R | κ | ρ | c |
|---|---|---|---|---|---|---|---|
| Mur ext. | Concrete block | 0,100 | 0,510 | 0,196 | 140000 | 1400 | 1000 |
| | Foam insulation | 0,0615 | 0,040 | 1,537 | 861 | 10 | 1400 |
| | Wood siding | 0,009 | 0,140 | 0,064 | 4293 | 530 | 900 |
| | **total surf-surf** | | | **1,797** | | | |
| Plancher | Concrete slab | 0,080 | 1,130 | 0,071 | 112000 | 1400 | 1000 |
| | Insulation ᵃ | 1,007 | 0,040 | 25,175 | 0 ᵇ | 0 ᵇ | 0 ᵇ |
| | **total surf-surf** | | | **25,246** | | | |
| Toiture | *identique au cas léger* | | | **2,992** | | | |

Classes : mur « Heavy / Internal (I) », plancher « Medium / Internal (I) »,
toiture « Very light / Evenly (D) ». Note ᶜ : « *For the heavyweight case wall and
floor properties are more massive and the roof properties are unchanged.* »

ᵃ **Plancher volontairement suridolé** pour découpler thermiquement du sol :
« *the thermal resistance of the floor can be used in the calculations instead of
the effective thermal resistance (R_c;f;eff), with the outdoor air as external
environment* ». La résistance de la couche épaisse est imposée sur la
**première conductance (la plus extérieure)**, afin que la masse thermique du
plancher réel soit conservée ; `h_1 = 0,04 W/(m²K)`.

ᵇ Isolant sous plancher : ρ, c et κ **pris à zéro** pour l'application du document.

---

## 4. Vitrage — `§7.2.2.6` — CECI CLÔT LA QUESTION DU U

```
g_gl;n = 0,789
F_w    = 0,9   (facteur de correction, vitrage non diffusant)  →  g_gl = 0,71
U_W    = 2,984 W/(m²·K)
R_se;v = 0,04  m²K/W      (cf. tableau 25)
R_si;v = 0,13  m²K/W      (cf. tableau 25)
F_fr   = 0                (aucune fraction de cadre)
```

Le texte est explicite : « *For the application of this document the following
input data are **adapted*** ». **U_W = 2,984 est une donnée d'entrée normative**,
pas une valeur à recalculer — d'où la légitimité de l'imposer.

NOTE de la norme : « *In ANSI/ASHRAE 140 a value is given for double pane shading
reduction factor (0,907). Therefore the U_w value is adapted to obtain the same
R_c value for the window.* » Et plus loin : « *The values for R_se;v and R_si;v in
this document are different from the values in ANSI/ASHRAE 140 … Therefore the
U_w value is adapted to obtain the same R_c value for the window.* »

### 4.1 Pourquoi trois valeurs circulaient — résolu

**Un seul vitrage, trois conventions de résistances de surface.** L'hypothèse
« convention plutôt que verre différent » est confirmée par la norme elle-même.

| Convention | U [W/(m²·K)] | R totale | R du noyau |
|---|---|---|---|
| **ISO 52016-1:2017 (normatif ici)** | **2,984** | 0,33512 | **0,16512** |
| BESTEST 1995 / config actuelle | 3,0 | 0,33333 | 0,16333 |
| ASHRAE 140:2023 (coeff. combinés 17,8 / 4,5) | 2,10 | 0,47650 | — |
| ce que VE calcule aujourd'hui | 2,917 | 0,34282 | 0,17282 |

L'écart de VE vaut **+0,0077 m²K/W sur le noyau**. Il recoupe le défaut relevé
dans `AUDIT-swiss-sia-existant.md` : les deux couches de verre de
`reference_model_assets.json` portent `"properties": {}`, **sans épaisseur
déclarée**, donc VE applique un défaut.

`⚠ NON DONNÉ PAR ISO` : épaisseur des vitres, λ du verre, épaisseur de lame. La
norme impose `U_W`, `g`, `R_se;v`, `R_si;v` et `F_fr` ; la composition en couches
est libre **pourvu que U_W = 2,984 soit atteint** sous ces résistances de surface.
Le 3,175 mm et la lame 6,297 de la config viennent de BESTEST 1995, source
absente de `/refs` — à conserver comme moyen, pas comme valeur normative.

---

## 5. Coefficients d'échange de surface — `§7.2.2.10`, tableau 25

Valeurs d'ISO 13789, en W/(m²·K) :

| Coefficient | Symbole | Vers le haut | Horizontal | Vers le bas |
|---|---|---|---|---|
| convectif, surface intérieure | h_ci | 5,0 | 2,5 | 0,7 |
| convectif, surface extérieure | h_ce | 20 | 20 | 20 |
| radiatif, surface intérieure | h_lr;i | 5,13 | 5,13 | 5,13 |
| radiatif, surface extérieure | h_lr;e | 4,14 | 4,14 | 4,14 |

C'est **la réponse au point §8 pt 6 de `test-1.spec.md`** (coefficient de surface
externe), pour la voie ISO. À ne pas confondre avec les coefficients combinés
d'ASHRAE 140:2023 (17,8 / 4,5), qui relèvent d'une autre convention.

---

## 6. Autres paramètres du modèle

| Grandeur | Valeur | Clause |
|---|---|---|
| Capacité interne, cas léger | C_m = **3,84 MJ/K** (classe « very light », 80 000·A_use) | §7.2.2.4 |
| Capacité interne, cas lourd | C_m = **12,48 MJ/K** (classe « heavy », 260 000·A_use) | §7.2.2.4 |
| Capacité air + mobilier | κ_m;int = **10 000 J/(m²·K)** | §7.2.2.5 |
| Absorption solaire, opaques | α_sol = **0,6** | §7.2.2.7 |
| Facteur de vue du ciel | F_sky = **1,0** toiture / **0,5** murs | §7.2.2.8 |
| Fractions convectives | f_int;c = **0,40** ; f_sol;c = **0,10** ; f_H;c = f_C;c = **1,00** | §7.2.2.9 |
| Apports internes | **200 W en continu**, 24 h/24 toute l'année → q_int = **1,453 W/m²** | §7.2.2.13 |
| Infiltration | **0,41 h⁻¹ en continu**, q_v = 0,0148 m³/s = **1,107 m³/(m²·h)**. **Aucun système de ventilation.** Indépendante du vent et de l'écart de température. Facteur **0,822** appliqué pour l'altitude 1609 m. | §7.2.2.14 |
| Puissances disponibles | Φ_H;avail = Φ_C;avail = **1000 kW** (effectivement infinies) | §7.2.2.16 |
| Écart ciel | Δθ_sky;r = **11 K** constant, tous pas de temps | §7.2.2.12 |
| Température de sol | **égale à la température d'air extérieur** (θ_gr;vi;m remplacée par θ_e) | §7.2.2.12 |
| Facteurs d'utilisation (méthode mensuelle) | a_H;0 = a_C;0 = 1,0 ; τ_H;0 = τ_C;0 = 15 h | §7.2.2.11 |

### 6.1 Consignes de thermostat — `§7.2.2.15`

**Continu** : θ_int;set;H = **20 °C**, θ_int;set;C = **27 °C**.

**Intermittent** : de 07 h 00 à 23 h 00 → 20 / 27 °C ; de 23 h 00 à 07 h 00 →
**10** / 27 °C. « *(no night time set back for cooling)* ».

### 6.2 Climat — `§7.2.2.12`

Données converties **selon ISO 52010-1**. Les valeurs horaires (température,
rayonnement direct et diffus par orientation, hauteur et azimut solaires) sont
dans le classeur publié à `http://standards.iso.org/iso/52016/-1/ed-1`.
Valeurs mensuelles au tableau 26.

> Cela **confirme** la réserve consignée dans la config du projet : le classeur
> ISO porte le rayonnement déjà projeté par orientation, converti selon
> ISO 52010-1, tandis que notre EPW **reconstruit** le diffus depuis le TMY1. Les
> deux séries ne sont pas la même chose ; le contrôle orientation par orientation
> devient possible (colonne `S` contre la fenêtre sud du cas 600).

---

## 7. Cas d'essai — tableau 27, `§7.2.3`

**C'est le « tableau 27 » que SIA 4010 cite en Annexe A, tab. 64.** Ce n'est pas
un tableau de valeurs : c'est la définition du périmètre du Test 1.

| Test | BESTEST | Construction | Thermostat |
|---|---|---|---|
| 1 | 600 | Lightweight | Continuous |
| 2 | 640 | Lightweight | Intermittent |
| 3 | 900 | Heavyweight | Continuous |
| 4 | 940 | Heavyweight | Intermittent |
| 5 | 600FF | Lightweight | Free floating |
| 6 | 900FF | Heavyweight | Free floating |

Le cas **1E** du classeur SIA n'appartient pas à cette liste : c'est un ajout du
SIA, et c'est le seul cas doté d'un critère pass/fail (cf. `test-1.spec.md` §6).

## 8. Résultats de référence — tableaux 28 à 34, `§7.2.4`

Grandeurs à calculer et rapporter : besoins mensuels et annuels de chaud
`Q_H;nd` et de froid `Q_C;nd` ; pour la méthode horaire, en plus : moyennes
mensuelles de température opérative `θ_op;av`, besoins horaires et températures
opératives du **4 janvier** et du **27 juillet**.

**Ces tables SONT la colonne `Daten EN ISO 52016-1 2017` du classeur SIA.**
Vérifié par recoupement direct : tableau 32 donne 600FF **Max 63,5 / Min −16,9 /
Average 25,9** et 900FF **44,4 / −2,4 / 26,0** — identique à
`refs/reference-data/test-1.ref.json`. Tableau 30, cas 600 mois 1 = **22,0**,
identique également.

Correspondance des tables :

| ISO 52016-1 | Contenu | Table du classeur SIA |
|---|---|---|
| 28 | besoins de chaud | 28 |
| 29 | besoins de froid | 29 |
| 30 | température opérative moyenne | 30 |
| 31 | charges de pointe horaires annuelles | 31 |
| 32 | extrêmes annuels de température opérative | 32 |
| 33 | charges horaires du 4 janvier | 33 |
| 34 | températures opératives horaires du 4 janvier | 34 |

La numérotation du classeur SIA **reprend celle d'ISO 52016-1**. C'est pourquoi
`test-1.ref.json` porte des « Table 28/29/30/31/32 » : ce sont les tables ISO.

---

## 9. Limites explicites — `§7.2.1`

Ces cas **n'incluent pas** :

- le transfert de chaleur du plancher couplé au sol (couvert par ISO/TR 52016-2) ;
- le couplage thermique entre deux zones ou plus ;
- l'effet des ponts thermiques ;
- les vérandas et autres espaces non conditionnés ;
- l'ombrage solaire par obstacles extérieurs (proches ou lointains) ;
- les schémas de régulation complexes (interruption de week-end, ventilation
  nocturne en free cooling, bypass de récupération…) ;
- les besoins **latents** — « *the equation is straightforward and can be easily
  checked analytically* ».

Utile pour ne pas chercher à valider ce que la norme ne teste pas.

---

## 10. Ce qui reste non vérifié

- **Annexe E** (normative), *Heat transfer and solar heat gains of windows and
  special elements*, pages 176-183 : non capturée. Elle préciserait le traitement
  des fenêtres, mais le point bloquant est levé sans elle.
- `§6.5.9 Temperature of adjacent thermally unconditioned zone` (p. 78-80) : non
  capturée. Elle porte sur le point ouvert du **Test 6** (température de la cave),
  pas sur le Test 1.
- **Épaisseur et λ des vitres** : non donnés par ISO (cf. §4 ci-dessus).
- **Transmission lumineuse visible** : non donnée par ISO. La valeur 0,86156 de la
  config reste un `IMPLEMENTATION_PROXY`, sans effet sur les sorties du Test 1.
- **NREL/TP-472-6231** (BESTEST 1995) et **ASHRAE 140-2014** restent absents de
  `/refs`. Ils ne sont plus bloquants pour le Test 1, ISO 52016-1 §7.2 étant
  auto-suffisant.

_Établi le 2026-07-31 après lecture directe des pages 122 à 134._
