# Anomalie — cas 900, tableaux 28 et 29 d'EN ISO 52016-1:2017

> Statut : **ÉTABLI**, preuves reproductibles. Confiance élevée.
> Établi le 2026-08-03 par recoupement de trois sources indépendantes.
>
> **Conclusion en une phrase** : les colonnes du cas 900 des tableaux 28 et 29
> d'EN ISO 52016-1:2017 sont **interverties de nature** — le tableau intitulé
> « heating » contient un profil de refroidissement, et réciproquement. Le
> classeur d'évaluation du SIA a détecté l'erreur et l'a corrigée sans le
> signaler.

---

## 1. Les faits

### 1.1 Ce que la norme imprime (page 131)

Lu directement sur `sia4010_evidence/ISO_52016_1_2017/page_131.png` du dépôt
`IES-Intership-general-repo`, capture fournie sous licence dont le sha256
déclaré a été recalculé et vérifié :
`C9B126485D50987C2E7F37F50B46C319E673612181119F228E42B5630CE5DA7E`.

**Tableau 28 — « Test results sensible energy needs for heating », cas 900 :**

```
mois   1    2    3    4    5    6    7    8    9   10   11   12   annuel
      84   53  121  147  175  308  638  656  626  418   84   48    3360
```

**Tableau 29 — « … for cooling », cas 900 :**

```
mois   1    2    3    4    5    6    7    8    9   10   11   12   annuel
      16   14   13    5    2    0    0    0    2    6    5   13      76
```

### 1.2 Ce que les profils disent

| Série | Mois du maximum | Saison | Total |
|---|---|---|---|
| ISO tab. 28, dit « chauffage » | **août** | été | 3358 |
| ISO tab. 29, dit « refroidissement » | **janvier** | hiver | 76 |

Un besoin de **chauffage** qui culmine en **août** et s'effondre en décembre est
physiquement impossible sous le climat DRYCOLD de Denver. Les deux colonnes
portent la forme de l'autre grandeur.

### 1.3 Ce que le classeur SIA porte

`SIA_4010_geteilter_Link/Test1/Resultaterfassung_Test1.xlsx`, feuille
`Daten EN ISO 52016-1 2017`, colonne D (cas 900) :

| Grandeur | Valeurs mensuelles | Total |
|---|---|---|
| refroidissement 900 | 84, 53, 121, 147, 175, 308, 638, 656, 626, 418, 84, 48 | 3358 |
| chauffage 900 | 455,85 · 433,15 · 191,61 · 108,90 · 12,91 · 14,60 · 0 · 0 · 1,34 · 48,15 · 184,33 · 372,12 | 1823 |

**La colonne « refroidissement 900 » du SIA est IDENTIQUE, mois par mois, à la
colonne « heating » du tableau 28 d'ISO.** Vérifié : 12 valeurs sur 12, écart nul.

Le SIA a donc pris la colonne mal étiquetée d'ISO et l'a placée là où elle
appartient physiquement.

Sa colonne de **chauffage** 900, elle, ne vient pas de la norme imprimée : elle
est en pleine précision alors que les cas 600, 640 et 940 sont des entiers
recopiés, et la feuille déclare en L44-L45 :
`Quelle: EPBD Excel | Nov 2019`.

---

## 2. Le contrôle qui tranche : les quatre autres programmes

Les quatre programmes de référence du Test 1 encadrent la valeur attendue.

**Chauffage annuel, cas 900 (kWh)**

| Programme | Valeur |
|---|---|
| IDA-ICE 5.0 beta 23 | 1264 |
| EXCEL SIA 380/2 | 2672 |
| EnergyPlus / OpenStudio 9.1.0 | 1229 |
| EDSL-Tas 9.5.2 | 1803 |
| **plage des quatre** | **1229 – 2672** |
| colonne ISO du classeur SIA | **1823 — dans la plage** |
| ISO imprimée | **3360 — hors plage** |

**Refroidissement annuel, cas 900 (kWh)**

| Programme | Valeur |
|---|---|
| IDA-ICE | 3177 |
| EXCEL SIA 380/2 | 4653 |
| EnergyPlus / OpenStudio | 2515 |
| EDSL-Tas | 2326 |
| **plage des quatre** | **2326 – 4653** |
| colonne ISO du classeur SIA | **3358 — dans la plage** |
| ISO imprimée | **76 — hors plage, d'un facteur 30** |

Les valeurs du classeur SIA tombent au cœur du nuage des quatre programmes ; les
valeurs imprimées d'ISO en sortent des deux côtés.

---

## 3. Pourquoi les autres cas ne sont pas concernés

Pour 600, 640 et 940, la norme imprimée et le classeur SIA concordent à ±2 près,
ce qui correspond à l'arrondi entre la somme des mensuelles et l'annuel imprimé :

| Cas | ISO imprimée | Classeur SIA |
|---|---|---|
| 600 chauffage | 5133 | 5134 |
| 640 chauffage | 3112 | 3110 |
| 940 chauffage | 1303 | 1301 |
| 600 refroidissement | 7503 | 7504 |
| 640 refroidissement | 7057 | 7058 |
| 940 refroidissement | 3261 | 3260 |

**Seul le cas 900 diverge, et sur les douze mois des deux tableaux.** Cela exclut
une erreur de transcription de notre côté : une erreur de lecture toucherait des
cellules isolées, pas exactement une colonne sur quatre, dans deux tableaux.

Les tableaux 30 (température opérative) et 32 (extrêmes en flottement libre) sont
**indemnes** : 600FF max 63,5 / min −16,9 / moy 25,9 et 900FF 44,4 / −2,4 / 26,0
concordent exactement entre la norme et le classeur.

---

## 4. Conséquences pratiques

**Pour le moteur** : la vérité de référence reste `test-1.ref.json`, c'est-à-dire
le classeur SIA. C'est lui que SIA 4010 désigne comme fichier d'évaluation
(§4.4), et il est le seul des deux à être cohérent avec les quatre programmes.
**Ne jamais « corriger » nos données vers les valeurs imprimées d'ISO.**

**Pour la configuration de Codex** :
`config/iso52016_test1_verification_cases.json` transcrit fidèlement la norme
imprimée, cas 900 compris. C'est correct en tant que relevé de la norme, mais ce
fichier ne doit pas servir de référence de comparaison pour le cas 900. Il porte
déjà `comparison_policy.mode = "REFERENCE_ONLY"`, ce qui limite le risque ; une
note explicite sur le cas 900 y serait néanmoins prudente.

**Pour la sous-commission SIA** : c'est une quatrième question à poser, et la
mieux étayée des quatre. Elle ne demande pas un arbitrage d'interprétation mais
la confirmation d'un fait : le classeur corrige-t-il sciemment un erratum de la
norme, et cet erratum est-il connu ?

Les trois autres questions restent : définition du `Streubereich` pour les
distributions de fréquence, ensemble des variantes contributrices, et nombre de
classes hors bande entraînant l'échec.

---

## 5. Reproduction

1. Recalculer le sha256 de `page_131.png` et le comparer à celui déclaré dans
   `config/iso52016_chapter7_confirmed_inputs.json` → `evidence_sha256`.
2. Lire les tableaux 28 et 29 sur l'image.
3. Extraire les colonnes `iso_52016_1_2017_reference` du cas 900 de
   `refs/reference-data/test-1.ref.json`.
4. Constater l'identité mois par mois entre le tableau 28 d'ISO et la colonne de
   refroidissement du SIA, et la divergence sur les douze mois du chauffage.
5. Situer les deux candidats dans la plage des quatre autres programmes.

## 6. Ce qui reste non vérifié

- L'existence d'un **erratum publié** par l'ISO sur ce point : non recherchée.
- La **provenance exacte** de l'« EPBD Excel, Nov 2019 » d'où le SIA tire sa
  colonne de chauffage 900 : ce fichier n'est pas en notre possession.
- Les **profils horaires** des tableaux 33 et 34 pour le cas 900 : non contrôlés,
  ils ne couvrent que 600/640/900/940 pour les charges et 600FF/900FF pour les
  températures.

_Établi le 2026-08-03. Trois sources indépendantes : la norme imprimée (capture
sous licence, empreinte vérifiée), le classeur d'évaluation SIA, et les quatre
programmes de référence._
