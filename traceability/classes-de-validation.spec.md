# Classes de validation SIA 4010 — état point par point

> Statut : **ÉTABLI**, sur pièces. Établi le 2026-08-05.
>
> **Conclusion en une phrase** : les huit classes sont bloquées par **un seul et
> même fichier**, `KLO_dry_normal.PRN` (SIA 2028 DRY, station Zürich-Kloten, jeu
> « Gegenwart »). La classe la plus facile — la 5 — n'a besoin que de la
> **température d'air horaire** de ce fichier, rien d'autre.

---

## 1. La matrice qui fait foi

SIA 4010:2023, **tableau 63** (p. 48), lu mot pour mot. Ce tableau, et non nos
suppositions, définit quels tests chaque classe exige.

| Classe | Applications couvertes | Protection solaire | Tests exigés |
|---|---|---|---|
| **1A** | évaluation du besoin de refroidissement ; puissance thermique requise **de base** | sans régulation selon la position du soleil (p. ex. stores en tissu) | **1 et 2A** |
| **1B** | idem | stores à **lamelles** | **1 et 2** |
| **2A** | énergie d'éclairage (SIA 387/4:2023 §3.4) ; besoin de chaleur chauffage et refroidissement | tissu | **1, 2A, 3A à F** |
| **2B** | idem | lamelles | **1 à 3** |
| **3** | évaluation du besoin d'humidification et de déshumidification | — | **1, 4 à 6** |
| **4A** | puissance thermique requise **liée au système** ; besoin d'énergie refroidissement et chauffage | tissu | **1, 2A, 3A à F, 4 à 7** |
| **4B** | idem | lamelles | **1 à 7** |
| **5** | besoins d'énergie de refroidissement et de chauffage **pour des profils de besoins existants** | — | **7 seul** |

**Fait structurant** : la classe 5 est la **seule** qui n'exige pas le Test 1.
C'est donc, sans ambiguïté, la plus facile — et c'est par elle qu'il faut
commencer.

---

## 2. Ce dont chaque test a besoin, vérifié

| Test | Climat | Bâtiment | Données d'usage SIA 2024 | Autre |
|---|---|---|---|---|
| **1** cas 600/640/900/940/600FF/900FF | **DRYCOLD Denver — EN NOTRE POSSESSION, vérifié** | pièce d'essai ISO 52016-1 ch. 7, **spec figée** | aucune | — |
| **1** cas diagnostiques 1A→1E | **Kloten** | idem | 1D et 1E : usage | 1E = seul cas à critère pass/fail |
| **2**, **2A** | **Kloten** | pièce d'essai | aucune | lamelles (2) / tissu (2A) |
| **3**, **3A–F** | **Kloten** | pièce d'essai | aucune | protection solaire |
| **4** | **Kloten** | bâtiment exemple, local `101` Hörsaal | **fiche 4.4**, niveau *Zielwerte* | consigne **résolue**, cf. §4 |
| **5** | **Kloten** | bâtiment exemple, 8 locaux | **fiches 3.1, 3.2, 3.3**, *Standardwerte* | — |
| **6** | **Kloten** | bâtiment exemple, 2 locaux | **fiches 6.2, 6.4**, *Standardwerte* | — |
| **7** | **Kloten — température d'air seule** | **aucun** | **aucune** | profils de charge **donnés** |

### 2.1 Pourquoi le Test 7 est le moins exigeant — établi sur la spécification

`Spezifikation_Test7.pdf` (4 p.) ne demande **ni modèle thermique de bâtiment,
ni solaire, ni vitrage, ni protection solaire, ni données d'usage** :

- **Profils de consommation** : « Es sind einheitliche Profile gemäss
  `Lastverläufe_220607.xlsx` zu verwenden » — froid et chaud, plus le profil de
  charge ECS. **Fournis par le SIA.**
- **Distribution** : forfaits (5 % de pertes, 2 % d'énergie auxiliaire).
- **Stockage** : deux ballons d'eau de 2 000 l, régulation de charge décrite.
- **Production** : Climaveneta NX-W-Y/H 0182, PAC eau-eau réversible, 55,9 kW
  froid / 60,0 kW chaud, champs de caractéristiques donnés selon EN 14825.
- **Appareil sur air extérieur** : refroidisseur sec 70 kW en mode froid,
  échangeur sur air extérieur 76 kW en mode chaud ; « **Temperaturdifferenz
  Aussenluft – Vorlauftemperatur 4 K (bei Volllast)** ».

C'est cette dernière ligne qui crée la dépendance météo, et **elle seule** : la
température d'air extérieur fixe la température de source/puits, donc le point
de fonctionnement de la PAC dans son champ de caractéristiques.

### 2.2 Contrôle négatif : les profils fournis ne contiennent pas la météo

`Lastverläufe_220607.xlsx` a été inspecté colonne par colonne.

- feuille `Gruppen` : 8765 lignes × 11 colonnes — heure, puis puissances en W
  (Kühldecke T5+T6 ; Lüftung T4/T5/T6 en froid ; BWW, Lüftung T4/T5/T6,
  Heizdecke T5, Konvektoren T6 en chaud) ;
- feuille `Grundlagen` : 8769 lignes × 46 colonnes — détail par test et par
  local, surfaces, ECS, état de charge des ballons.

Recherche sur les en-têtes empilés des deux feuilles :
`aussen|extern|temperat|theta|°C|klima|wetter` → **aucune occurrence**.

**Le SIA fournit les charges, pas les conditions extérieures.** La classe 5 ne
peut donc pas être rendue autonome.

---

## 3. Ce qui bloque, par classe

> **RÉVISION DU 2026-08-05** — la température extérieure de Kloten a été
> retrouvée dans une source officielle : `Test4/Resultaterfassung Test4.xlsx`,
> feuille **`Wetterdaten`**. Le bloqueur météo se réduit donc au **rayonnement
> solaire** et à l'**humidité**. Cf. §3.0.

### 3.0 Ce que le dossier officiel contient réellement en météo

Balayage exhaustif des sept classeurs d'évaluation, toutes feuilles, en-têtes
sur 14 lignes, motif
`site outdoor|drybulb|dew ?point|humidity|feuchte|solar radiation|horizontal radiation|beam|diffuse solar|direct solar|globalstrahlung|wind ?speed|barometric` :

| Classeur | Occurrences | Contenu |
|---|---|---|
| Test 1, 2, 3, 6, 7 | **0** | — |
| **Test 4** | **1** | feuille `Wetterdaten` — `Site Outdoor Air Drybulb Temperature [C](Hourly)` et `EMS Two Day Average OA Temp [C](Hourly)`, **8760 valeurs chacune** |
| Test 5 | 21 | puissances d'humidificateur et humidité de l'air repris — **résultats, pas climat** |

**Acquis** : température d'air extérieur horaire de Zürich-Kloten,
min −13,02 / max 34,10 / **moyenne 9,469 °C** — cohérent avec la station. Figée
dans `refs/reference-data/sia-2028-kloten-temperature.{json,csv}`.

**Toujours absents de toute source officielle** : le **rayonnement solaire**
(sous quelque forme que ce soit) et l'**humidité de l'air extérieur**.

### 3.1 Bloqueurs par classe, après révision

| Classe | Solaire Kloten | Humidité Kloten | Données d'usage | Autre |
|---|---|---|---|---|
| **5** | **oui** — grandeur obligatoire n° 14 « Elektrische Energie PV » | non | — | — |
| **1A** | **oui** | non | — | — |
| **1B** | **oui** | non | — | modèle de lamelles |
| **2A** | **oui** | non | — | éclairage / lumière du jour |
| **2B** | **oui** | non | — | lamelles + éclairage |
| **3** | **oui** | **oui** | fiches **4.4 ; 3.1–3.3 ; 6.2, 6.4** | — |
| **4A** | **oui** | **oui** | idem | — |
| **4B** | **oui** | **oui** | idem | **SIA 387/4:2023** tab. 9 (nous avons **2017**) |

**8 classes sur 8 dépendent du rayonnement solaire de Kloten.** C'est désormais
le bloqueur unique et dominant — la température, elle, est acquise.

### 3.1 Pourquoi le jeu gratuit CH2018 ne s'y substitue pas

Trois raisons indépendantes, chacune suffisante :

1. **Période.** Le paquet gratuit ne contient que 2035 et 2060 (RCP 2.6 / 8.5).
   Colonne `time.yy` vérifiée. Aucun fichier de période présente.
2. **Contenu.** Les quatre programmes de référence écrivent tous
   « **Original-SIA-Datei** » ; IDA ICE la nomme `KLO_dry_normal.PRN`. Le
   rapport Excel du Test 2 précise : « Die Original-Klimadaten nach SIA 2028
   **enthalten die Solarstrahlung auf die vertikalen Flächen der
   Haupthimmelsrichtungen** ». Le CSV CH2018 ne porte que `gls`, `str.diffus`,
   `str.direkt` — **aucune colonne verticale**.
3. **Format.** `.PRN` contre `.csv`.

⚠ Réserve honnête sur le mot « normal » : nous avons d'abord lu
`SIA 2028 DRY normal` comme désignant la période présente. Rien ne l'établit.
Le paquet CH2018 livrant exactement deux variantes — `DRY` et
`1in10-warmsummer` —, « normal » distingue **plus probablement l'année DRY
normale de l'année à été chaud décennal**. La conclusion ne change pas : les
raisons 2 et 3 tiennent quelle que soit la lecture.

### 3.2 Et VE ne lit pas le `.PRN`

Bibliothèque livrée avec VE 2025, `C:\Program Files\IES\Shared Content\Weather` :
460 fichiers, **aucune station suisse**, extensions `.epw` (211), `.fwt` (197),
`.wea` (51). Aucun `.PRN` sous `Program Files\IES`.

Une conversion sera donc nécessaire, et elle devra traiter honnêtement les
colonnes d'irradiance verticale que `.epw` ne prévoit pas au même endroit.
**À vérifier avant l'achat, pas après.**

---

## 4. Ce qui a été débloqué et n'est plus un obstacle

- **Consigne du test 4 (point ouvert O1)** — **FERMÉ**. SIA 2024:2021 tableau 11
  donne pour l'usage **4.04 Hörsaal : 21 °C / 26 °C**, identiques au groupe de
  référence 1.01–3.03 (unanime à 21/26). Décalage **nul** sur les deux courbes.
  Le tableau 11 ne distingue par ailleurs **aucun** niveau
  Standardwert/Zielwert/Grenzwert : la température de dimensionnement ne dépend
  pas du niveau demandé par la spécification.
- **Figure 1 de SIA 380/2 (point ouvert O2)** — **FERMÉ**, valeurs exactes
  extraites du dessin vectoriel, résidu < 0,001 °C. Limites 20,5→22,0 et
  24,5→26,5 ; ruptures en 12 / 17,5 / 19 / 23,5 ; `Δθctr` = 0,700 K ; consignes
  constantes 22,7 et 23,8. Concordance 8/8 avec SIA 180:2014 figure 4.
- **Règle de décalage par usage** — vérifiée sur **10 valeurs sur 10** publiées
  par SIA 4010 §3.1.4, reproduites depuis le tableau 11
  (`engine/tests/test_setpoint_curves.py`).
- **Climat du Test 1** — source ISO téléchargée, figée, empreinte recalculée.
  La température du `.epw` déployé dans VE concorde sur **8760 heures à
  0,000 K**, le vent à 0,00 m/s près.

---

## 5. Deux avertissements qui affecteront les résultats du Test 1

Découverts en lisant le fichier climatique ISO lui-même, et non signalés
jusqu'ici dans le dossier.

**5.1 Mois d'initialisation.** Le fichier porte en clair : « *ATTENTION: The
first month is for initialization only; these data are copied from the last
month = December* ». 9504 lignes = 8760 + 744. Une simulation VE de
8760 heures partant du 1er janvier **ne reproduit pas l'état initial** des
programmes de référence. Effet maximal sur les cas à forte masse — **900, 940,
900FF**. Le préconditionnement de VE doit refléter ce mois.

**5.2 Nature de l'entrée solaire.** Le fichier ISO fournit l'irradiance **déjà
calculée** sur huit surfaces nommées (NV, EV, SV, WV, N45, S45, VOID, H), sans
décomposition global/direct/diffus. Les programmes de référence ont donc reçu
une irradiance de surface. Un `.epw` fournit global/direct/diffus et laisse le
modèle de ciel du programme dériver les surfaces : **l'entrée n'est pas la
même**. Le global horizontal diffère déjà de **−0,9 %** (1832 contre
1849 kWh/m²·an).

C'est le mécanisme exact qui fait d'EXCEL un *outlier* au Test 2 — mais en sens
inverse : ici ce sont les **références** qui ont utilisé l'irradiance
pré-calculée, et c'est nous qui la recalculerons.

**Contrôle préalable recommandé, coût une simulation** : lancer le cas 600,
relever l'irradiation incidente annuelle sur la façade **sud**, comparer à
**SV = 1547,1 kWh/m²·an**. Écart < 1 % → le modèle de ciel n'est pas un facteur
confondant. Écart de plusieurs pour cent → tout écart thermique ultérieur
s'explique d'abord par là, et non par le moteur thermique de VE.

Irradiation annuelle de référence figée, kWh/m²·an :

| NV | EV | SV | WV | N45 | S45 | H |
|---|---|---|---|---|---|---|
| 429,7 | 1150,0 | 1547,1 | 1046,6 | 853,5 | 2239,8 | 1848,5 |

---

## 6. Chemin le plus court vers la première classe signée

1. **Acheter** le jeu SIA 2028 « Gegenwart », station **Zürich-Kloten**. Repère
   au moment de commander : le fichier doit s'appeler `KLO_dry_normal` et **ne
   porter aucune année** — ni 2035, ni 2060, ni `RCP`.
2. **Vérifier** que la conversion vers un format lisible par VE (`.epw` ou
   `.fwt`) préserve la température horaire, et documenter ce que devient
   l'irradiance verticale.
3. **Classe 5 d'abord** : Test 7 seul, aucun modèle de bâtiment, profils
   fournis. C'est la seule classe atteignable avec ce seul apport.
4. Puis **classe 1A**, qui n'ajoute que le Test 1 (déjà prêt côté climat) et le
   Test 2A.

**Téléchargements gratuits à faire en parallèle**, sans lesquels les classes 3,
4A et 4B resteront bloquées même une fois la météo acquise :

- fiches d'utilisation SIA 2024 **3.1, 3.2, 3.3, 4.4, 6.2, 6.4** —
  `https://www.sia.ch/de/cms/dienstleistungen/normenundordnungen?item=15143#15152`
  (version en ligne déjà post-rectificatifs, d'après le SIA) ;
- **corrigenda SIA 2024 et SIA 180** — nos tableaux 11 et 13 et les critères de
  confort portent `controle_effectue: false` ;
- **SIA 2028/C2:2023 tableau 10** et les « Anwendungsempfehlungen ».

---

## 7. Ce qui reste non vérifié

- L'édition **2023** du tableau 9 de SIA 387/4 (nous avons la **2017**) — bloque
  la seule classe 4B.
- **SN EN 15316-2:2017**, qui définit `Δθctr` : 0,700 K est la valeur *dessinée*
  par la figure 1, pas une valeur dont nous connaissons la portée.
- **SN EN ISO 52120-1:2022 tableau 5** : sans lui, on ne sait pas si les
  régulations VE relèvent des consignes constantes ou variables.
- **EN ISO 52016-1 §6.5.5** : pondération de la température opérative, écart
  quantifié à 0,174 K entre les deux lectures possibles.
- Le **nombre de classes hors bande** entraînant l'échec — question ouverte à la
  sous-commission SIA, avec trois autres.

_Établi le 2026-08-05. Sources : SIA 4010:2023 tab. 63 et §3.1.4 ; SIA 380/2:2022
§5.2.2.x ; les sept `Spezifikation_TestN.pdf` ; les rapports d'application des
quatre programmes de référence ; `Lastverläufe_220607.xlsx` ; le fichier
climatique public d'EN ISO 52016-1 ; la bibliothèque météo de VE 2025._
