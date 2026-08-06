# Bâtiment exemple SIA 4010 — locaux, zonage thermique et conditions aux limites (tests 4 à 7)

> Statut : **ARBITRAGE RENDU** — périmètre des locaux : confiance élevée (tests 4, 5, 6),
> moyenne-haute (test 7). Zonage : déterminé pour les tests 4, 5, 6.
> **Révision 2 (2026-07-31, 2ᵉ passe)** : les 12 Anwenderberichte des tests 5/6/7 et les
> extractions **par coordonnées** ont été dépouillés. Trois points ouverts de la rév. 1 sont
> traités : §8.1 (plancher sur cave) → **tranché par défaut argumenté**, §8.2 (GW/ZW) → **tranché
> par défaut argumenté**, §8.3 (consignes tests 4/5) → **chaîne normative établie, valeurs
> reconstruites pour le test 5, encore ouvertes pour le test 4**. Les consignes du test 6 sont
> désormais **lues** (§8.4). Deux points restent indécidables (§8.6, §8.7).
> Auteur : `norm-analyst`.
> Portée : bâtiment exemple uniquement (SIA 4010 §4.3). Tests 1 à 3 n'utilisent pas ce
> bâtiment (cellule de test EN ISO 52016-1 / ASHRAE 140).
> Classes de validation concernées : **3, 4A, 4B** (tab. 63, cf. `critere-test4.spec.md` §3.2).

## 0. Convention de citation et de statut

**[V]** vérifié par lecture directe d'une source de cette session ·
**[C]** vérifié par recoupement arithmétique de deux sources **[V]** ·
**[I]** inférence, justifiée sur place · **[U]** **usage** établi par un Anwenderbericht — rapport
d'éditeur, **pas une prescription** · **[?]** non déterminable avec les sources disponibles.

Sources lues (répertoire d'extraction de session `…\scratchpad\norme\`) :

| Fichier | Rôle | Fiabilité de l'extraction |
|---|---|---|
| `spec_test4_cellules.txt` (3 p.), `spec_test5_cellules.txt` (5 p.), `spec_test6_cellules.txt` (5 p.), `spec_test7_cellules.txt` (4 p.) | spécifications, **extraction par coordonnées** (`scripts/pdf_table_cells.py`) | **haute** : colonnes d'une ligne séparées par ` \| ` dans l'ordre réel → **source à utiliser en priorité** |
| `doc_beispielgebaeude_cellules.txt` (10 p.) | documentation du bâtiment exemple, par coordonnées | **haute** : tab. 1 (compositions) et tab. 3 (vitrage) désormais correctement appariés |
| `spec_test4.txt`, `spec_test5.txt`, `spec_test6.txt`, `spec_test7.txt`, `*_raw/_brut.txt` | anciennes extractions `-layout` / brutes | **dégradée** (colonnes décalées) — conservées seulement comme **recoupement** |
| `anwender_test4_1..4`, `anwender_test5_1..4`, `anwender_test6_1..4`, `anwender_test7_1..4` | 16 rapports d'éditeurs | haute (texte courant), mais **sources défectueuses** : cf. §12.4 |
| `sia_4010_2023.txt` (3109 l.), `sia_380_2_2022.txt` (3603 l.) | normes | **texte courant fiable ; tableaux et figures scramblés** — tab. 3 de SIA 380/2 lu par recoupement arithmétique uniquement (§8.2) |
| `INVENTAIRE_batiment_exemple.txt`, `PREUVE_classeurs.txt`, `PREUVE_classeur_test4.txt` | IFC et classeurs d'évaluation | haute |

Sources primaires correspondantes : `SIA_4010_geteilter_Link/Beispielgebäude/`,
`SIA_4010_geteilter_Link/Test<N>/Spezifikation_Test<N>.pdf`,
`SIA_4010_geteilter_Link/Test<N>/Anwenderberichte/`, `refs/SIA-4010-2023.pdf`,
`refs/SIA-380-2-2022.pdf`.

**Non présentes dans `/refs`** : SIA 2024:2021 (ni prSIA 2024) — **bon de commande au §11** —,
SIA 2028, SIA 180:2014, SN EN 16798-5-1, SN EN 16798-7, SN EN ISO 52016-1, SN EN ISO 52120-1,
SN EN 15316-2, SIA 387/4:2023. Aucune valeur ne leur est attribuée ici.

---

## 1. Réponse courte — tableau test → locaux → zones

*(inchangé par la 2ᵉ passe ; aucune source nouvelle ne le contredit — au contraire, `anwender_test5_1.txt`
l. 18-20 et `anwender_test6_1.txt` l. 18 confirment 8 et 2 zones, cf. §12.1)*

| Test | Locaux (n° / désignation) | Id IFC | Étage IFC | Surface IFC brute m² | Zones thermiques | Confiance |
|---|---|---|---|---|---|---|
| **4** | `101` Hörsaal | `#2343` | Storey 3.4 (traverse 3.4 **et** 6.8) | 165,81 | **1** | ~95 % |
| **5** | `100` Sitzungszimmer | `#2266` | Storey 3.4 | 31,62 | **8** (1 local = 1 zone) | ~95 % |
| | `102` Grossraumbüro | `#2245` | Storey 3.4 | 104,94 | | |
| | `200` Sitzungszimmer | `#3658` | Storey 6.8 | 31,62 | | |
| | `201` Büro | `#3500` | Storey 6.8 | 17,14 | | |
| | `202` Büro | `#3522` | Storey 6.8 | 17,14 | | |
| | `203` Büro | `#3544` | Storey 6.8 | 17,14 | | |
| | `204` Büro | `#3566` | Storey 6.8 | 17,14 | | |
| | `205` Büro (Gruppen-/Eckbüro) | `#3586` | Storey 6.8 | 33,13 | | |
| **6** | `001` Restaurant | `#835` | Storey 0.0 | 237,36 | **2**, couplées par 350 m³/h | ~95 % |
| | `002` Küche | `#855` | Storey 0.0 | 35,88 | | |
| **7** | les **10 locaux des tests 5 et 6** ; le local du test 4 **n'entre que par ses batteries** | — | — | 269,87 + 273,24 | **0 zone à simuler** : charges fournies par `Lastverläufe_220607.xlsx` | ~90 % |

Totaux : test 5 = 269,87 m² ; test 6 = 273,24 m² ; tests 4+5+6 = 708,92 m² sur les
1405,32 m² du bâtiment, soit **11 locaux utilisés sur 29** ; 18 locaux hors périmètre.

Aucun local cité par une spécification ne manque à l'IFC : **zéro écart bloquant** (§6).

---

## 2. Base normative du périmètre

**[V]** SIA 4010:2023 §4.3 (`sia_4010_2023.txt` l. 2680-2693) : « Pour les tests **4 à 7**, un
bâtiment exemple a été défini … La documentation du bâtiment exemple peut être téléchargée
en tant que document séparé … Des données numériques sont disponibles … : plans, coupes et
vues au format DXF ; modèles 3D au format IFC ; **exécution de la charge pour le test 7**. »

**[V]** Tableau 62 « Tests de validation », colonne **Zone** (l. 2649-2674) :

| Test | Colonne « Zone » du tab. 62 |
|---|---|
| 1-3 | « cellule de test selon SN EN ISO 52016-1:2017, chiffre 7.2.2 (= ASHRAE 140:2017) » |
| 4 | « exemple de bâtiment, **amphithéâtre (sans fenêtre)** » |
| 5 | « exemple de bâtiment, **bureaux et salles de réunion** » |
| 6 | « exemple de bâtiment, **restaurant et cuisine** » |
| 7 | « **installations des tests 4 à 6 et zones des tests 5 et 6** » |

**[V]** Tableau 64, colonne « Objet — spatial » :
- test 4 (l. 2880-2892) : « exemple de bâtiment, amphithéâtre (sans fenêtre), **sans émission
  de chaleur ou de froid autre que la ventilation** » ; technique : « installation VAV à
  **zone unique** … SYS_TYPE=**SINGLE_ZONE** ».
- test 5 (l. 2915-2930) : « exemple de bâtiment, **1. + 2. étage supérieur : 1 bureau [ouvert],
  2 salles de réunion, 4 bureaux individuels, 1 bureau d'angle / de groupe** » ; technique :
  « installation VAV à **zones multiples** … SYS_TYPE=**MULTI_ZONE** ».
  `[I]` « 1 bureau [RDC] » dans l'extraction est une coquille de traduction pour
  *Grossraumbüro* : le décompte 1+2+4+1 = **8** correspond exactement aux 8 locaux énumérés
  par la spécification, et aucun local du test 5 n'est au rez-de-chaussée (l. 11-13).
- test 6 (l. 2939-2942) : « exemple de bâtiment, **restaurant et cuisine** ».
- test 7 (l. 2951-2992) : « **toutes les pièces des tests 5 et 6, ainsi que tous les systèmes
  de ventilation** … (étages de bureaux via des plafonds chauffants/réfrigérants, restaurant
  via des plafonds réfrigérants) … diffusion et distribution de chaleur (étages de bureaux via
  des plafonds chauffants/réfrigérants, restaurant via des **convecteurs**) … production de
  froid, production de chaleur, autoproduction d'électricité (PV) » ; commentaire
  (l. 2951-2956) : « Peut représenter en même temps les besoins énergétiques totaux du
  bâtiment. **Des profils précalculés pour les besoins en espace sont fournis.** »

---

## 3. Test par test

### 3.1 Test 4 — un local, une zone

**[V]** `spec_test4_cellules.txt` p. 1 l. 8-10 (= `spec_test4.txt` l. 11-13), mot pour mot :

> « Testgebäude Raum "**Hörsaal**", **fensterlos**, **zweigeschossig, im 1. Und 2. OG**, **mit
> Dach gegen Aussenklima**, gemäss Dokumentation Beispielgebäude » — « Nettofläche | **165.8 m2** »

- Rattachement : `#2343`, n° `101`, `Hörsaal`, Storey 3.4, 165,81 m², h moy. **6,38 m**,
  1058 m³ (`INVENTAIRE` l. 29). Écart de surface **+0,01 m²** (l. 47). **[V]**
- **Le local est un seul `IfcSpace`** traversant les deux niveaux (h 6,38 m ≈ 3,0 + 3,4 m,
  entre-étages 3,4 m). Il ne doit **pas** être scindé par étage. **[C]**
- **Sa dalle de couverture est bien la toiture** : 3,4 + 6,38 = 9,78 ≈ **Storey 9.8**, dernier
  niveau de l'IFC, qui ne porte aucun local (`INVENTAIRE` l. 4, 10-38). **[C]**
- Une zone unique, corroborée par « **Einzonen**-Klimaanlage mit variablem Volumenstrom »
  (`spec_test4_cellules.txt` p. 2 l. 5) et `SYS_TYPE=SINGLE_ZONE` (tab. 64 l. 2882-2884). **[V]**
- Cohérence de dimensionnement : 55 personnes à 3 m²/pers (p. 1 l. 26) → 165 m² ≈ 165,81 ;
  débit nominal 1700 m³/h (p. 2 l. 9) / 165,81 m² = 10,25 m³/(h·m²) ≈ 10 m³/(h·m²) annoncé
  (p. 1 l. 19-21). **[C]**
- **Constructions : ce test seul déroge à la documentation.** « Konstruktionen | Gemäss FprSIA
  380/2:2022, **Tabelle 3 "Grenzwert"** » (p. 1 l. 12) **[V]**. Cf. §8.2.
- **Usage : ce test seul demande les *Zielwerte* de SIA 2024.** « Nutzung | Standardnutzung
  "Hörsaal" gemäss SIA 2024:2021; **Zielwerte** » (p. 1 l. 18) **[V]** — les tests 5 et 6
  demandent les **Standardwerte** (§11). Le niveau de valeur est donc **choisi domaine par
  domaine** : on ne peut pas transposer d'un domaine à l'autre (§8.2).
- Consigne de température : **cellule vide dans le PDF** — cf. §8.5.
- Fenêtres : aucune (`fensterlos`) → le vitrage de la documentation (§7.2) est hors sujet ici.
- Parois extérieures opaques : la spécification ne dit rien d'autre que « fensterlos » et
  « Dach gegen Aussenklima ». À lire dans la géométrie IFC/DXF. **[?]** (§8.7)

### 3.2 Test 5 — huit locaux, huit zones

**[V]** `spec_test5_cellules.txt` p. 1 l. 8-10, mot pour mot :

> « **1. OG: Räume 100 (Sitzungszimmer), 102 (Grossraumbüro); 2. OG: Räume 200
> (Sitzungszimmer), 201 bis 204 (Einzelbüros) und 205 (Gruppenbüro)**; gemäss Plänen
> Dokumentation » — « Nettofläche | **Gemäss Dokumentation** » (p. 1 l. 11)

- **Un local = une zone (8 zones)** — statut **[I] très fort**, cinq appuis convergents :
  1. « Ersatzluftanlage, **zonenweise** CO2-geregelt » (p. 1 l. 19) **[V]** ;
  2. « Regelung | CO2-abhängig, **pro Zone** mit Volumenstromregler geregelt » (p. 2 l. 21) **[V]** ;
  3. tab. 64 énumère les 8 locaux **individuellement**, `SYS_TYPE=MULTI_ZONE` (l. 2915-2930) **[V]** ;
  4. un diagnostic est demandé **par local** : « CO2-Konzentration **GR-Büro** » (p. 5 l. 24-26) **[V]** ;
  5. **[U]** le programme de référence « Excel » a instancié **6 tableurs de zone** pour couvrir
     les 8 locaux — « Jeweils zur Berechnung der **6 verschiedenen Raumtypen (Einzelbüro,
     Einzelbüro mit schwerer Innenwand, Gruppenbüro, Grossraumbüro, Sitzungszimmer,
     Sitzungszimmer mit Dach)** » (`anwender_test5_1.txt` l. 18-20). Six **types**, pas six zones :
     `201`-`204` se répartissent en deux types selon la paroi intérieure.
  → **Aucune source n'autorise à regrouper 201-204 en une zone.** Ne pas le faire.
- **Conséquence nouvelle et importante** (appui 5) : les quatre bureaux individuels **ne sont pas
  thermiquement identiques** — deux d'entre eux ont une *schwere Innenwand* (iw2 porteuse,
  béton 0,2 m), les deux autres une paroi légère (iw1). L'inertie des **parois intérieures
  adiabatiques** est donc bien un paramètre du test : elle discrimine deux types de bureau
  pourtant de même surface (17,14 m²). Cela **confirme §4.2** : « adiabat » = flux nul,
  **masse conservée**. Statut : **[U] fort**, confiance ~95 %. Reste à établir par la géométrie
  **quels** locaux parmi `201`-`204` portent la paroi lourde. **[?]** (§8.7)
- « Sitzungszimmer **mit Dach** » (même citation) confirme que les locaux du 2. OG ont la
  toiture plate en contact avec l'extérieur, et que `100` (1. OG) ne l'a pas. **[U]** — cohérent
  avec l'IFC (Storey 9.8 = niveau de toiture, §6 E8).
- Le local `101` Hörsaal (test 4) est **mitoyen** des locaux du test 5 sur les deux niveaux. **[C]**
  (219,68 + 165,81 = 385,49 ≈ 385,32 m² du RDC).
- Locaux non-zones mais **indispensables comme support technique** :
  - `U102` Technik : « Geräteaufstellung | **UG, Raum U102, unkonditioniert** » (p. 2 l. 7) **[V]** ;
  - `022` Steigzone : « Verteilsystem | **Steigzone entlang Liftschacht (Raum 022)** … Kanäle
    0.3 x 0.3 m, totale Länge ZUL 14 m, Kanäle 0.3 x 0.15 m, Länge 5 m; **U-Wert 0.6 W/m2 K** »
    (p. 2 l. 8-10) **[V]** — le U de 0,6 W/(m²K) des gaines de colonne est **nouveau** (l'ancienne
    extraction ne donnait que 1,1) ;
  - Corridors `110`/`210` : « **Deckenbereich Korridor 1. + 2. OG** : Kanäle 0.3 x 0.15 m,
    Länge ZUL 20 m; **U-Wert 1.1 W/m2 K** » (p. 2 l. 11-12) **[V]** ;
  - gaines **dans** les zones : « Deckenbereich Zonen 1. + 2. OG: Rohre ⌀ 0.125 m, Länge 24 m,
    Rohre ⌀ 0.1 m, Länge 40 m; U-Wert 1.1 W/m2 K » (p. 2 l. 13-14) **[V]**.
- Températures de référence des locaux techniques : « **Temperatur-Randbedingungen
  Zentrale/Steigzone : 15°C (Okt. – März), 28°C (April – Sept.)** » (p. 2 l. 15-16) **[V]**.
- Émission : « Heiz-/Kühldecken — **Für Test 5 nur als Randbedingung relevant, Vorbestimmung
  für Test 7** » ; « Betriebszeit | Wie Betriebszeit Lüftung » (p. 1 l. 25-28) **[V]**.
- Consignes : « Sollwerte | Temperatur » **sans valeur** (p. 2 l. 1) ; CO2 **950 – 1200 ppm**,
  air extérieur 400 ppm (p. 2 l. 2) ; **Rel. Feuchte min. 30 %** (Sollwert Befeuchtung, p. 2 l. 3).
  **[V]** — les 950/1200 ppm **corrigent** la rév. 1, qui n'avait pas pu lire cette ligne.
- **Quatre variantes 5A-5D** reconstruites au §12.2.

### 3.3 Test 6 — deux locaux, deux zones couplées

**[V]** `spec_test6_cellules.txt` p. 1 l. 8-12 (Restaurant) et p. 2 l. 48-52 (Küche) :

> « **Restaurant** — Selbstbedienungsrestaurant im EG: **Raum 001 (Restaurant)** gemäss Plänen
> Dokumentation — Nettofläche | Gemäss Dokumentation (**237.4 m2**) »
> « **Küche** — Küche zu Selbstbedienungsrestaurant im EG: **Raum 002 (Küche)** gemäss Plänen
> Dokumentation — Nettofläche | Gemäss Dokumentation (**35.9 m2**) »

- Rattachement : `#835`/`001`/237,36 m² (écart −0,04) et `#855`/`002`/35,88 m² (écart −0,02). **[V]**
- **Deux zones distinctes, aérauliquement couplées** : « Überströmung von 10% des Küchen-
  Abluftvolumenstroms (**350 m3/h**) in die Küche durch **Überdruck** » (p. 1 l. 26-27) ; côté
  cuisine « Überströmung von ca. 10% des Abluftvolumenstroms (350 m3/h) aus dem Restaurant
  mittels **Unterdruck** » (p. 3 l. 5-6). **[V]**
- Bilan aéraulique **exactement fermé sur ces deux locaux seulement** : ZUL 3000 + 3150 =
  **6150** = « Nennvolumenstrom | Stufe 3 | 6'150 m3/h | 100% » (p. 3 l. 38) ; ABL 2650 + 3500 =
  **6150** ; 3000 − 2650 = 350 = 3500 − 3150. **[C]**
  → Corroboré **[U]** : « Die Ablufttemperatur wurde Abluft-Volumenstromgewichtet aus **den
  beiden Raumtemperaturen** errechnet » (`anwender_test6_1.txt` l. 23-25) — *les deux*, donc
  aucun autre local n'alimente la reprise.
- Émission : Restaurant → **Konvektoren** « In Betrieb während Betriebszeit der Lüftung »
  (p. 1 l. 30-31), Vorlauftemperatur glissante **(−8 ; 40) → (20 ; 20) °C** (p. 2 l. 1-16) **[V]**
  + **Kühldecken** « Für Test 6 nur als Randbedingung relevant, Vorbestimmung für Test 7 »
  (p. 2 l. 17-21), **dont la cellule « Vorlauftemperatur » est vide** (p. 2 l. 22) **[V]**.
  Küche → Wärmeabgabe « **keine** », Kälteabgabe « **keine** » (p. 3 l. 9-12). **[V]**
- **Consignes du Restaurant : désormais lues intégralement — cf. §8.4.**
- Cuisine : « Tempera-tur Küche | **Sollwert heizen: 21°C** » (p. 3 l. 25-27) **[V]** — la
  contradiction apparente de la rév. 1 est **résolue** au §8.4.
- Locaux support technique : « Geräteaufstellung | **Keller, unkonditioniert** » (p. 3 l. 31) et
  « Verteilsystem | Zentrale und Steigzone zwischen Küche und Restaurant … Kanäle 0.4 x 0.7 m,
  Länge ZUL total 8 m; Deckenbereich Küche: ZUL-Kanal 0.3 x 0.6 m, Länge total 6 m;
  Deckenbereich Restaurant: ZUL-Kanal 0.3 x 0.6 m, Länge total 16 m, Rohre ⌀ 0.18 m, Länge
  total 45 m » (p. 3 l. 32-36) **[V]**. **Aucun U-Wert et aucune température ambiante** ne sont
  donnés pour ces gaines, contrairement au test 5 — cf. §8.6.
- **Règle d'adiabaticité abrégée pour la cuisine** : « Randbedingungen | Bauteile gegen
  Nachbarzonen, die nicht Gegenstand des Tests sind: **adiabat** » (p. 2 l. 54) — sans le tiret
  « zones d'autres tests ». **[V]** Cf. §4.3.

### 3.4 Test 7 — aucune zone à simuler, des groupes de distribution

`spec_test7_cellules.txt` ne nomme **aucun local** (4 pages, vérifié) : « Gebäude | Testgebäude
gemäss Dokumentation » (p. 1 l. 7). Le périmètre spatial vient donc **uniquement** de SIA 4010
tab. 62 et tab. 64 (§2). Ce que la spécification énumère, ce sont **9 groupes de distribution** :

| Type | Groupe | Réf. | Local(aux) desservi(s) |
|---|---|---|---|
| Froid | Test 4 Luftkühler | p. 1 l. 8 | `101` (via la centrale du test 4) |
| Froid | Test 5 Luftkühler | p. 1 l. 9 | 8 locaux du test 5 |
| Froid | Test 6 Luftkühler | p. 1 l. 10 | `001` + `002` |
| Froid | **Test 5 + 6 Kühldecken** | p. 1 l. 11 | 8 locaux du test 5 **et** `001` |
| Chaud | Test 4 Lufterwärmer | p. 1 l. 18 | `101` |
| Chaud | Test 5 Lufterwärmer | p. 1 l. 19 | 8 locaux du test 5 |
| Chaud | Test 6 Lufterwärmer | p. 1 l. 20 | `001` + `002` |
| Chaud | **Test 5 Heizdecken** | p. 1 l. 21 | 8 locaux du test 5 |
| Chaud | **Test 6 Konvektoren** | p. 1 l. 22 | `001` |

- La cuisine `002` n'appartient à **aucun** groupe d'émission ; elle n'est desservie que par
  l'air. **[C]**
- **Les charges ne sont pas à resimuler** : « Verbrauchsprofile | **Es sind einheitliche Profile
  gemäss `Lastverläufe_220607.xlsx` zu verwenden** » (p. 1 l. 12 froid, l. 23 chaud) ;
  « Warmwasserladung | Ladeprofil (Wärme am Eingang des Warmwasserspeichers), gemäss
  `Lastverläufe_220607.xlsx` — Temperatur: 60°C » (p. 1 l. 13-17). **[V]**
  → **Confirmé [U] par les 4 rapports** : « Wärmebedarfsprofile gemäss gegebener Datei wie in
  der Spezifikation angegeben » (`anwender_test7_1.txt` l. 38, `_2.txt` l. 19, `_3.txt` l. 11) et
  « Ein selbst erstelltes Spreadsheet, das die **elektrischen Verbrauchsprofile aus den Tests 4,
  5 und 6 aggregiert** » (`_1.txt` l. 19-21). **Aucun programme de référence n'a resimulé de
  zone au test 7.** Confiance ~90 % → l'ancien §8.8 est levé (reste le mapping colonnes, §8.7).
- ⚠ **[U] réserve** : IDA-ICE a **modifié** le fichier de charges — « wurde die Spalte BWW im
  Excel Lastverläufe **erweitert** » pour éviter l'interpolation linéaire entre points horaires
  (`anwender_test7_3.txt` l. 11-16). C'est une entorse au mot *einheitliche* ; à connaître avant
  de comparer une exécution à pas de temps fin.
- Le local `101` du test 4 entre au test 7 **par ses deux batteries seulement** : tab. 62 dit
  « **installations** des tests 4 à 6 et **zones** des tests 5 et 6 » (l. 2665-2667). **[V + I]**

---

## 4. Règle d'adiabaticité et conditions aux limites

### 4.1 Le texte, mot pour mot **[V]**

`spec_test4_cellules.txt` p. 1 l. 13-17 (à l'identique `spec_test5_cellules.txt` p. 1 l. 13-17 et
`spec_test6_cellules.txt` p. 1 l. 14-18 pour le Restaurant) :

> « **Bauteile gegen Nachbarzonen, die nicht Gegenstand des Tests sind:**
> – **Gegen Nachbarzonen von anderen Tests, falls sie mitgerechnet werden: Sollwerte gemäss
>   jeweiliger Testspezifikation**
> – **Ansonsten sowie alle übrigen Innenbauteile adiabat** »

Traduction de travail (la mienne, à contrôler par un germanophone) : *« Éléments de
construction contre des zones voisines qui ne sont pas l'objet du test : — contre des zones
voisines relevant d'autres tests, si celles-ci sont calculées conjointement : valeurs de
consigne selon la spécification de test correspondante ; — sinon, ainsi que tous les autres
éléments intérieurs : adiabatique. »*

**Point de structure, décisif pour §8.1** : la règle est une **partition exhaustive** à deux
branches (`falls sie mitgerechnet werden` / `Ansonsten sowie alle übrigen Innenbauteile`). Il
n'existe **aucune troisième branche** pour un local non conditionné du bâtiment. **[V]**

### 4.2 Portée exacte, décomposée

| Situation d'un élément intérieur | Traitement | Statut |
|---|---|---|
| Entre deux locaux **tous deux objets du même test** (`001`↔`002` ; `201`↔`202`) | **Non concerné** : couplage thermique normal entre zones simulées | **[I]** — la règle ne vise que les voisins « die **nicht** Gegenstand des Tests sind » |
| Contre un local **objet d'un autre test**, cet autre test étant calculé conjointement (`101`↔`102`, `101`↔`200`) | Frontière à **température imposée** = consigne de la spécification de l'autre test | **[V]** |
| Contre un local **objet d'un autre test non calculé** | **adiabatique** (« Ansonsten ») | **[V]** |
| Contre tout autre local (corridors, WC, gaines, cage d'escalier, cave, annexes cuisine, UG entier) | **adiabatique** | **[V]** |
| Élément intérieur **au sein d'une même zone** (cloison interne, dalle intermédiaire du Hörsaal) | « alle übrigen Innenbauteile adiabat » | **[V]** |

**Interprétation, marquée comme telle** : « adiabat » signifie **flux nul à la frontière, masse
thermique conservée** — l'élément reste modélisé avec ses couches, seule sa face opposée est
isolée. Trois appuis :
(a) sens usuel en simulation dynamique ;
(b) **[U]** le programme « Excel » a dû **ajouter** la prise en compte des parois internes à son
tableur, pour les tests 4, 5 **et** 6 (« ergänzt durch G. Zweifel zur Berücksichtigung von …
**internen Wänden** » — `anwender_test4_1.txt` l. 17, `anwender_test5_1.txt` l. 16,
`anwender_test6_1.txt` l. 16) — inutile si les parois internes étaient simplement supprimées ;
(c) **[U] nouveau et plus fort** : le même programme distingue « Einzelbüro » et « Einzelbüro
**mit schwerer Innenwand** » comme deux types de zone à calculer séparément
(`anwender_test5_1.txt` l. 18-19). La nature de la paroi intérieure adiabatique **change donc
le résultat** : sa masse est bien prise en compte.
Statut **[I]** appuyé sur **[U]**, confiance ~95 % (rév. 1 : 90 %). **Décision de conception :
conserver la masse.**

### 4.3 Nuance du test 6 pour la cuisine **[V]**

La cuisine reçoit la version **courte** de la règle (`spec_test6_cellules.txt` p. 2 l. 54), sans
le tiret « zones d'autres tests ». Comme le seul voisin « objet du test » de la cuisine est le
Restaurant (couplé), la différence de rédaction est **sans effet pratique**. `[I]`

### 4.4 Conditions aux limites par test — synthèse opérationnelle

| Test | Extérieur | Sol / UG | Voisins d'autres tests | Autres locaux |
|---|---|---|---|---|
| 4 | toiture 165,81 m² (Storey 9.8) **[C]** ; parois opaques éventuelles **[?]** ; **aucune fenêtre** **[V]** | pas de contact terrain (1./2. OG) | `102`, `100`, `110` (1. OG) et `200`-`205`, `210` (2. OG) : consignes du test 5 **si** calculé, sinon adiabat | adiabat |
| 5 | façades + fenêtres + stores en tissu (§7.2) ; **toiture pour les locaux du 2. OG** **[U]** | plancher sur 1. OG (pas de terrain) | `101` : consigne du test 4 **si** calculé, sinon adiabat | corridors, WC, gaines, cage d'escalier : adiabat |
| 6 | façades RDC + fenêtres | **plancher sur cave : adiabatique** — §8.1, tranché par défaut argumenté | `101` (si mitoyen) : consigne du test 4 si calculé | `003`, `004`, `010`, `011`, `012` : adiabat |
| 7 | sans objet (charges fournies) | sans objet | sans objet | sans objet |

**Locaux et niveaux non utilisés (18 locaux)** : `U101`, `U102`, `U110`, `020`, `021`, `022`,
`023`, `003`, `004`, `010`, `011`, `012`, `110`, `112`, `113`, `210`, `211`, `212`.
Traitement normatif : **hors périmètre de simulation ; frontière adiabatique**. Deux d'entre eux
gardent un rôle **non thermique** : `U102` (implantation de la centrale, test 5) et `022`
(cheminement des gaines, test 5), avec la température imposée 15/28 °C (§3.2). **[V]**

---

## 5. Rattachement complet IFC ↔ spécifications

29 locaux de l'IFC, statut par test. Usage SIA d'après `doc_beispielgebaeude_cellules.txt`
p. 10 l. 5-33 (table désormais lue **sans décalage**).

| Id IFC | N° | Désignation | Étage | m² | Usage SIA (doc) | Statut |
|---|---|---|---|---|---|---|
| `#51` | U101 | Lager | -3.5 | 237,36 | 12.4 Nebenraum | hors périmètre (adiabat) |
| `#75` | U110 | Verkehrsfläche | -3.5 | 32,44 | 12.1 Verkehrsfläche | hors périmètre |
| `#101` | U102 | Technik | -3.5 | 118,91 | 12.4 Nebenraum | **support** : centrale test 5, non conditionné |
| `#122` | 021 | Treppenhaus | -3.5 | 17,85 | 12.3 Treppenhaus | hors périmètre (h ≈ 13,3 m) |
| `#144` | 020 | Lift | -3.5 | 2,40 | 12.3 Treppenhaus | hors périmètre (h ≈ 13,3 m) |
| `#166` | 022 | Steigzone | -3.5 | 0,78 | — | **support** : gaines test 5 (h ≈ 12,8 m), 15/28 °C |
| `#188` | 023 | Steigzone | -3.5 | 1,84 | — | hors périmètre (h ≈ 6,5 m) |
| `#835` | 001 | Restaurant | 0.0 | 237,36 | 6.1 Restaurant | **zone test 6** (spec : 6.2 SB-Restaurant, §6 E2) |
| `#855` | 002 | Küche | 0.0 | 35,88 | 6.3 Küche zu Restaurant | **zone test 6** (spec : 6.4, §6 E2) |
| `#877` | 003 | Lager Küche | 0.0 | 11,39 | 12.4 Nebenraum | hors périmètre |
| `#898` | 004 | Kühlraum | 0.0 | 10,24 | 12.11 Kühlraum | hors périmètre |
| `#920` | 011 | WC Damen | 0.0 | 14,62 | 12.7 WC | hors périmètre |
| `#941` | 012 | WC Herren | 0.0 | 14,61 | 12.7 WC | hors périmètre |
| `#964` | 010 | Verkehrsfläche | 0.0 | 61,22 | 12.1 Verkehrsfläche | hors périmètre |
| `#2245` | 102 | Grossraumbüro | 3.4 | 104,94 | 3.2 Grossraumbüro | **zone test 5** |
| `#2266` | 100 | Sitzungszimmer | 3.4 | 31,62 | 3.3 Sitzungszimmer | **zone test 5** (sans toiture) |
| `#2284` | 112 | WC Damen | 3.4 | 14,62 | 12.7 WC | hors périmètre |
| `#2302` | 113 | WC Herren | 3.4 | 14,61 | 12.7 WC | hors périmètre |
| `#2323` | 110 | Verkehrsfläche | 3.4 | 57,14 | 12.1 Verkehrsfläche | hors périmètre ; **gaines test 5** |
| `#2343` | 101 | Hörsaal | 3.4 | 165,81 | 4.4 Hörsaal | **zone test 4** (traverse 3.4 + 6.8) |
| `#3500` | 201 | Büro | 6.8 | 17,14 | 3.1 Einzel-, Gruppenbüro | **zone test 5** |
| `#3522` | 202 | Büro | 6.8 | 17,14 | 3.1 | **zone test 5** |
| `#3544` | 203 | Büro | 6.8 | 17,14 | 3.1 | **zone test 5** |
| `#3566` | 204 | Büro | 6.8 | 17,14 | 3.1 | **zone test 5** |
| `#3586` | 205 | Büro | 6.8 | 33,13 | 3.1 | **zone test 5** (« Gruppenbüro ») |
| `#3604` | 211 | WC Damen | 6.8 | 14,62 | 12.7 WC | hors périmètre |
| `#3622` | 212 | WC Herren | 6.8 | 14,61 | 12.7 WC | hors périmètre |
| `#3640` | 210 | Verkehrsfläche | 6.8 | 57,14 | 12.1 Verkehrsfläche | hors périmètre ; **gaines test 5** |
| `#3658` | 200 | Sitzungszimmer | 6.8 | 31,62 | 3.3 Sitzungszimmer | **zone test 5** (**avec toiture**, `anwender_test5_1.txt` l. 20) |

**Convention de surface — tranchée [C]** : les « Nettofläche » des spécifications sont les
`GrossFloorArea` de l'IFC (valeur absolue). Trois concordances indépendantes :
165,8 ↔ 165,81 · 237,4 ↔ 237,36 · 35,9 ↔ 35,88. La documentation ne contient **aucun tableau
de surfaces** (chapitre 1 = figures seules, `doc_beispielgebaeude_cellules.txt` p. 3-5) : l'IFC
est la seule source numérique de surfaces. `NetFloorArea` **n'existe pas** dans ce fichier.

---

## 6. Écarts spécifications ↔ IFC / documentation

| # | Écart | Gravité | Détail |
|---|---|---|---|
| E1 | **Aucun local manquant** | — | Les 11 locaux cités (dont `U102` et `022`) existent tous. |
| E2 | Usage du Restaurant : **`6.1 Restaurant`** (doc p. 10 l. 5) vs **`6.2 "Selbstbedienungerestaurant"`** (spec test 6 p. 1 l. 19) | **moyenne** | La spécification prime. Idem cuisine : doc `6.3` (p. 10 l. 6) vs spec `6.4` (p. 2 l. 55). **Deux usages SIA 2024 différents → données d'usage différentes.** À figer **d'après les specs**. Cf. §11. |
| E3 | La spec distingue « Einzelbüros » / « Gruppenbüro » (test 5 p. 1 l. 9), la doc leur donne **un seul** usage `3.1` (p. 10 l. 23-27) | faible | Un seul jeu SIA 2024 pour les cinq. |
| E4 | Doc : page de garde « **Version 4**, 15. Januar 2021 » (p. 1 l. 2-3) alors que le fichier s'appelle `Dokumentation_Beispielgebäude_V5.pdf` | faible mais à acter | **Non résolu.** |
| E5 | Doc : « **prSIA** 2024:2021 » (p. 10 l. 2) ; specs 4 et 5 : « SIA 2024:2021 » ; spec 6 : les deux — « SIA 2024:2021 » (p. 1 l. 19, p. 2 l. 55) **et** « prSIA 2024:2021 » (p. 2 l. 28, p. 3 l. 18) | faible | Projet vs norme publiée, **incohérence interne au test 6**. Une seule édition doit être utilisée. Cf. §11. |
| E6 | Spec test 4 : « **FprSIA** 380/2:2022 » (p. 1 l. 12) ; `/refs` contient **SIA 380/2:2022** publiée | faible | Le tab. 3 de `/refs` reproduit exactement les résistances de la doc (§8.2) : **présomption forte d'identité**, mais le libellé reste divergent. |
| E7 | Doc : 8 compositions ; SIA 380/2 tab. 3 : **9** — la doc **omet « Paroi intérieure contre local non conditionné »** (U 0,28 ; `sia_380_2_2022.txt` l. 1986-1992) | faible | La doc conserve en revanche **« Zwischendecke gegen unkonditioniert (Keller) »**. Analyse de cette asymétrie : §8.1. |
| E8 | Storey 9.8 ne porte **aucun local** | — | Niveau de **toiture** (6,8 + 3,0 = 9,8). Ne pas créer de zone. **[C]** |
| **E9** | **Les specs des tests 4, 6 et 7 ne contiennent AUCUN bloc « Zu liefernde Resultate » / « Testkriterien »** | **élevée** | Vérifié par recherche exhaustive sur les deux extractions : présent dans `spec_test1.txt` l. 69-73, `spec_test2.txt` l. 70, `spec_test3.txt` l. 149, `spec_test5_cellules.txt` p. 4 l. 46 + p. 5 l. 4-9 ; **absent** des tests 4, 6, 7. Les grandeurs et critères de ces trois tests doivent donc être pris dans SIA 4010 tab. 64/65 et dans les `Resultaterfassung_Test<N>.xlsx`. **Confirme et généralise** le défaut déjà relevé pour le test 4. |
| **E10** | **Cellules de valeur vides dans les PDF** | **élevée** | Test 4 : « Sollwerte / Raumlufttemperatur » (p. 2 l. 1-3) ; test 5 : « Sollwerte / Temperatur » (p. 2 l. 1) ; test 6 : « Kälteabgabe / Kühldecken / Vorlauftemperatur » (p. 2 l. 22). Les trois confirmés par trois méthodes d'extraction. Cf. §8.5. |

---

## 7. Ce que la documentation du bâtiment exemple ajoute

Elle **ne contient ni zonage, ni règle d'adiabaticité** : son sommaire n'a que trois chapitres —
Geometrie, Gebäudehülle, Nutzung (p. 2 l. 2-13). **Ne pas chercher le zonage dans la
documentation.**

### 7.1 Géométrie (ch. 1, p. 3-5) — figures seulement
Grundrisse 1.UG/EG/1.OG/2.OG, Längsschnitt, Querschnitte, façades E/O/S/N. **Aucune côte ni
surface exploitable en texte.** → géométrie à prendre de l'IFC / des DXF-DWG.

### 7.2 Enveloppe (ch. 2, p. 6-9) — le vrai apport, **désormais lu sans décalage**

- **Tabelle 1** (p. 6 l. 6-50) : **8 compositions**, couche par couche. Colonnes, dans l'ordre
  réel confirmé par l'en-tête (p. 6 l. 6-8) : `Nr. | Material/Baustoff | Dicke [m] | Lambda GW
  [W/(mK)] | Lambda ZW [W/(mK)] | Dichte [kg/m³] | sp. W.kap. [kJ/(kgK)]`. **[V]**
  ⚠ **La mise en garde de la rév. 1 (« ne pas figer les λ depuis ce texte ») est LEVÉE** :
  l'appariement est vérifié par deux contrôles indépendants — (a) λ_GW > λ_ZW pour les **cinq**
  couches isolantes et λ_GW = λ_ZW pour toutes les autres ; (b) le recoupement arithmétique
  complet avec SIA 380/2 tab. 3 (§8.2). Les λ peuvent être figés **depuis ce fichier**.
- Compositions : `aw1` Aussenwände (p. 6 l. 9-13), `aw2` Aussenwände gegen Erdreich (l. 14-16),
  `iw1` Innenwände nicht tragend (l. 17-20), `iw2` Innenwände tragend (l. 21-24), Boden über
  Erdreich (l. 25-29), Zwischendecke (l. 30-36), **Zwischendecke gegen unkonditioniert
  (Keller)** (l. 37-44), Flachdach (l. 45-49). Ordre des couches « **von innen nach aussen bzw.
  oben nach unten** » (l. 50). **[V]**
- Principe explicite (p. 6 l. 3-5) : « Die Bauteile werden für die Berechnung eines
  **Grenzwertes (GW)** und eines **Zielwertes (ZW)** bestimmt. Es werden die
  **Dämmeigenschaften bei gleicher Stärke variiert**, damit die Geometrie des Gebäudes
  gleichbleibt. » → **seuls les λ changent, jamais les épaisseurs** : une seule géométrie IESVE,
  deux jeux de matériaux. **[V]**
- **Constat nouveau et opérationnel** : `iw1`, `iw2` et `Zwischendecke` ont des λ **identiques**
  en GW et ZW (p. 6 l. 17-24 et 30-36). **Le choix GW/ZW n'affecte donc aucun élément
  intérieur** — il ne porte que sur `aw1`, `aw2`, `Boden über Erdreich`, `Zwischendecke gegen
  unkonditioniert` et `Flachdach`. **[V]**
- **Vitrage** (p. 7 l. 5-12) : Planitherm XN Saint-Gobain, **triple** — 1. SGG PLANITHERM XN
  4 mm / 2. Air 10 % + Argon 90 % EN 673 14 mm / 3. SGG PLANICLEAR 4 mm / 4. Air-Argon 14 mm /
  5. SGG PLANITHERM XN 4 mm (gespiegelt). **[V]**
- **Propriétés vitrage — appariement symbole↔valeur désormais VÉRIFIÉ** (p. 8 l. 6-23, p. 9
  l. 7-11), colonnes `Without shading | With shading` : **[V]**
  - EN ISO 52022-3 (summer) : gtot 0,545 / 0,059 ; gc 0,022 / 0,006 ; gth 0,044 / 0,013 ;
    gv 0,000 / 0,000 ; qi 0,066 / 0,019
  - EN ISO 52022-3 (reference) : gtot 0,542 / 0,056 ; **Ug 0,646 / 0,574 W/(m²K)**
  - EN 410 : τe 0,479 / 0,040 ; ρe 0,323 / 0,490 ; ρ'e 0,323 / 0,456 ; τv 0,742 / 0,058 ;
    ρv 0,145 / 0,496 ; ρ'v 0,145 / 0,395 ; τuv 0,234 / 0,012
  - ISO 15099 (summer) gtot 0,545 / 0,059 ; ISO 15099 (winter) **Ug 0,654 / 0,582**
  ⚠ **La mise en garde de la rév. 1 sur l'interversion des libellés est LEVÉE.**
- **Protection solaire** (p. 7 l. 18 et p. 8 l. 1-5) : store en tissu **extérieur** Soltis
  92-2048-Alu SergeFerrari ; **jeu d'air de 1 cm** en haut, sur les côtés et en bas ;
  « Der Sonnenschutz wird bei einer Solarstrahlung von **150 W/m2 auf der Aussenseite**
  (gemäss der Sonnenschutzregelung) geschlossen. » **[V]**
- **Cadre** (p. 9 l. 14) : « **Rahmenanteil 15 %**, U-Wert = **1.3 W/(m2K)**, abs = **0.6** ». **[V]**
- **Ponts thermiques** (p. 9 l. 16) : « Es werden **keine Wärmebrücken** berücksichtigt. » **[V]**
- **[C] Le vitrage n'a PAS de variante GW/ZW** : un seul jeu de propriétés est donné, et
  Uw ≈ 0,85 × 0,646 + 0,15 × 1,3 = **0,74 W/(m²K)**, inférieur aux **deux** valeurs du projet de
  référence de SIA 380/2 tab. 2 (« Valeur U des fenêtres (verre et cadre) Uw : valeur limite
  **1,1**, valeur cible **0,88** » — `sia_380_2_2022.txt` l. 1713). Le bâtiment exemple **n'est
  donc pas un projet de référence** au sens de SIA 380/2 ch. 7 ; son enveloppe est une donnée
  figée. Conséquence pratique : la question GW/ZW ne concerne **que** l'isolation opaque.

### 7.3 Usage (ch. 3, p. 10) — l'apport pour les zones
- Table **Raumnummer → Bezeichnung → Nutzung (SIA)** pour **les 29 locaux** (p. 10 l. 5-33) ;
  seuls `022` et `023` n'ont pas d'usage (« - »). **[V]**
- « Die Nutzungsdaten werden gemäss **prSIA 2024:2021** angenommen » (p. 10 l. 2). **[V]**
- « Die **Zeitpläne** für Personenbelegung, Geräte und Beleuchtung können ebenfalls dem
  Merkblatt entnommen werden. Die Beleuchtungsregelung erfolgt gemäss diesem Zeitplan
  (**keine Tageslichtabhängige Beleuchtungsregelung**). » (p. 10 l. 34-36) **[V]** — **pas** de
  régulation d'éclairage sur la lumière du jour dans les tests 4 à 7.

---

## 8. Points ouverts — état après la 2ᵉ passe

### 8.1 Plancher du rez-de-chaussée sur la cave (test 6) — **TRANCHÉ : adiabatique**

**Réponse à la question posée : les Anwenderberichte du test 6 ne disent RIEN sur ce plancher.**
Recherche exhaustive par expression régulière sur les 16 rapports
(`keller|erdreich|unkonditioniert|adiabat|Grenzwert|Zielwert|Konstruktion|Bauteil|U-Wert|Aufbau|Boden|Decke`) :
**trois occurrences en tout**, toutes hors sujet — `anwender_test1_1.txt` l. 15 et l. 20
(constructions ASHRAE 140, test 1), `anwender_test2_1.txt` l. 23 (albédo du sol),
`anwender_test5_4.txt` l. 32 (« Druckaufbau »). **Statut : négatif vérifié [V].** Les rapports
des tests 4 à 7 ne documentent que la technique (WRG, ventilateurs, batteries, régulation) —
**aucun** ne décrit l'enveloppe ni les conditions aux limites.

Faute d'usage documenté, l'arbitrage se fait sur la norme et sur la structure des sources.

**Décision : plancher `001`/`002` sur cave = ADIABATIQUE. [I], confiance ~80 %.** Trois motifs,
par ordre de force :

1. **La règle est une partition exhaustive à deux branches** (§4.1, `spec_test6_cellules.txt`
   p. 1 l. 14-18). La cave n'est pas « Gegenstand des Tests » et n'est l'objet d'**aucun** autre
   test (aucune spécification ne la mentionne comme zone) ; le plancher est un `Innenbauteil`.
   La branche « Ansonsten sowie alle übrigen Innenbauteile: adiabat » s'applique **littéralement
   et sans reste**. **[V]** sur le texte, **[I]** sur l'application.
2. **Aucune température de cave n'est donnée nulle part.** Or la spécification du test 5 **donne**
   une température ambiante là où elle est nécessaire (« Temperatur-Randbedingungen
   Zentrale/Steigzone: 15°C (Okt. – März), 28°C (April – Sept.) », p. 2 l. 15-16) — et ce
   uniquement pour des **pertes de gaines**, pas pour une frontière de zone. Le test 6 mentionne
   la cave **seulement** comme lieu d'implantation de la centrale (« Geräteaufstellung | Keller,
   unkonditioniert », p. 3 l. 31) et ne fournit **ni U-Wert de gaine, ni température ambiante**
   (p. 3 l. 32-36). Un flux de chaleur vers la cave serait donc **non calculable** avec les
   données fournies : la spécification serait incomplète. L'hypothèse adiabatique est la seule
   qui rende la spécification **fermée**. **[C]** — argument le plus décisif.
3. **L'argument « cette composition n'a d'emploi que là » ne tient pas.** Contre-preuve : la
   documentation contient aussi `aw2` *Aussenwände gegen Erdreich* (p. 6 l. 14-16) et *Boden
   über Erdreich* (p. 6 l. 25-29), qui ne servent qu'au **1. UG**, donc **hors du périmètre de
   tous les tests**. La Tabelle 1 décrit **le bâtiment entier**, pas les besoins des tests. La
   présence de la composition « Zwischendecke gegen unkonditioniert (Keller) » ne prouve donc
   **rien** sur son statut thermique dans le test 6. **[C]** — ceci **corrige** le raisonnement
   de la rév. 1, qui surestimait ce signal.

**Contre-argument restant, à consigner** : le bâtiment a bel et bien été conçu avec ce plancher
**isolé** — la composition « Zwischendecke gegen unkonditioniert (Keller) » (p. 6 l. 37-44)
est la « Zwischendecke » ordinaire (p. 6 l. 30-36) **plus une couche 6 d'EPS de 0,13 m** sous la
dalle. Cette isolation n'a de sens que pour séparer conditionné et non conditionné. Le rendre
adiabatique revient à ignorer un élément documenté de l'enveloppe thermique. L'écart de U entre
les deux lectures est total (0,245 W/(m²K) en GW, cf. §8.2, contre 0) sur **237,36 m²** sous le
Restaurant + 35,88 m² sous la cuisine.

**Résolution empirique recommandée, non ambiguë** — c'est un travail de moteur, pas de norme :
simuler le test 6 dans les **deux** hypothèses et comparer les sommes annuelles au **Streubereich
des 4 programmes de référence** figé dans `Resultaterfassung_Test6.xlsx` (bande =
`Mittelwert ± max |écart|`, formules prouvées dans `PREUVE_classeurs.txt` l. 9-11, 28-39).
Sur 273 m² à ΔU ≈ 0,25 W/(m²K), l'écart de besoin de chaleur doit être largement hors bande :
**le test est discriminant**. → tâche `validation-engine-engineer`, à faire **avant** figeage.
**Jusque-là : ne pas déclarer le test 6 « done ».**

### 8.2 Variante GW ou ZW des constructions (tests 5 et 6) — **TRANCHÉ : GW par défaut argumenté**

**Réponse à la question posée : les Anwenderberichte ne disent RIEN sur GW/ZW.** Même recherche
exhaustive qu'au §8.1 : **aucune** occurrence de `Grenzwert`, `Zielwert`, `Konstruktion`,
`Aufbau`, `U-Wert`, `Bauteil` dans les 12 rapports des tests 5, 6 et 7. **Négatif vérifié [V].**

En revanche, **l'extraction par coordonnées permet une démonstration arithmétique nouvelle** :
la colonne **GW** de la documentation est la transposition **exacte, à épaisseur du bâtiment**,
des compositions **« valeur limite » de SIA 380/2:2022 tab. 3**. Preuve : pour les **cinq**
couches isolantes, λ_GW = λ_réel × (d_doc / d_VL,SIA), au dernier chiffre affiché.

| Composition | Couche isolante | d_doc | λ_ZW (doc) | λ_GW (doc) | d_VL (tab. 3) | λ_ZW × d_doc/d_VL | Verdict |
|---|---|---|---|---|---|---|---|
| `aw1` Aussenwände | EPS | 0,25 | 0,033 | **0,055** | 0,15 | 0,033 × 0,25/0,15 = **0,0550** | identité exacte |
| `aw2` geg. Erdreich | XPS | 0,16 | 0,033 | **0,053** | 0,10 | 0,033 × 1,60 = **0,0528** | 0,053 (arrondi) |
| Boden über Erdreich | XPS | 0,16 | 0,033 | **0,053** | 0,10 | **0,0528** | 0,053 (arrondi) |
| Zwischendecke g. unkond. | EPS c. 6 | 0,13 | 0,033 | **0,054** | 0,08 | 0,033 × 0,13/0,08 = **0,0536** | 0,054 (arrondi) |
| Flachdach | EPS | 0,27 | 0,034 | **0,057** | 0,16 | 0,034 × 0,27/0,16 = **0,0574** | 0,057 (arrondi) |

Citations : λ et d de la doc — `doc_beispielgebaeude_cellules.txt` p. 6 l. 12, 15, 29, 43, 47.
Épaisseurs de SIA 380/2 tab. 3 — `sia_380_2_2022.txt` l. 1955 (mur ext. EPS 0,15 VL / 0,22 VC),
l. 1964 (XPS 0,1 / 0,16), l. 1999 (sol XPS 0,1 / 0,16), l. 2037 + 2040 (plancher sur cave, EPS
0,08 VL / 0,13 VC — l. 2031-2032), l. 2049 + 2036 (toiture EPS 0,16 VL / 0,24 VC).

⚠ **Réserve d'extraction, à ne pas masquer** : le tab. 3 de SIA 380/2 est **scramblé** dans mon
extraction texte (colonnes entremêlées). Les couples d'épaisseurs ci-dessus sont une **lecture
reconstruite**, validée par **sept** valeurs U du même tableau que je retrouve par calcul depuis
la colonne GW de la doc : mur ext. 0,196 → « 0,2 » (l. 1951) ; mur contre terrain 0,308 →
« 0,3 » (l. 1965) ; sol contre terrain 0,300 → « 0,3 » (l. 1999) ; plancher intermédiaire
0,599 → « 0,64 » (l. 2011, écart imputable aux résistances de surface) ; paroi int. non
porteuse 0,301 → « 0,3 » (l. 1973) ; paroi int. porteuse 2,61 → « 2,7 » (l. 1982) ; toiture
0,197 → « 0,2 » (l. 2050). **[C]** — mais le tab. 3 devrait être **relu sur rendu visuel** avant
figeage définitif (§10).

**Ce que cela établit (et n'établit pas)** :
- **[C]** doc **GW ≡ SIA 380/2 tab. 3 « valeur limite »**. Donc « Gemäss Dokumentation » + GW
  donne **exactement** la même enveloppe que le test 4, qui dit « Tabelle 3 "Grenzwert" ».
- **[C]** doc **ZW = λ réel du matériau à l'épaisseur du bâtiment**, ce qui **égale** la « valeur
  cible » de tab. 3 pour `aw2`, `Boden über Erdreich` et `Zwischendecke gegen unkonditioniert`
  (d_doc = d_VC : 0,16 / 0,16 / 0,13) mais la **dépasse** pour `aw1` (0,25 > 0,22, R +13,6 %) et
  `Flachdach` (0,27 > 0,24, R +12,5 %). Le ZW de la doc n'est donc **pas** rigoureusement la
  valeur cible normative.
- **[V]** Aucune source lue ne **prescrit** le jeu à employer pour les tests 5 et 6.

**Décision : employer GW pour les tests 5, 6 et 7. [I], confiance ~80 %.** Motifs :
1. **Cohérence physique obligatoire.** La règle §4.1 prévoit explicitement que les tests soient
   « mitgerechnet » ensemble. Dans un modèle couplé, la paroi `101`↔`102` et la dalle
   `101`↔`001` sont **le même élément** pour le test 4 (figé sur GW) et pour les tests 5/6. Deux
   λ pour un même mur est impossible. **[I] fort.**
2. **GW est le seul jeu ancré à une valeur normative** (identité exacte avec tab. 3 valeur
   limite, ci-dessus) ; ZW s'en écarte de 12-14 % sur deux compositions. Un exercice de
   validation reproduit une référence, pas une intention. **[C] + [I].**
3. SIA 380/2 §7.2.3 : « Les **valeurs limites** … **doivent être respectées** » contre « Les
   valeurs cibles **doivent être visées** » (`sia_380_2_2022.txt` l. 1658-1663) — seule la
   valeur limite est une exigence. **[V]**, portée argumentative moyenne.
4. Un U plus élevé (GW) donne des besoins plus grands, donc un test **plus discriminant** entre
   programmes. Argument d'ingénierie, **pas** normatif.

**Contre-argument à consigner** : le test 4 **mélange** les niveaux — constructions au
**Grenzwert** de SIA 380/2 (p. 1 l. 12) et usage aux **Zielwerte** de SIA 2024 (p. 1 l. 18),
alors que les tests 5 et 6 prennent les **Standardwerte** de SIA 2024. Le niveau de valeur est
donc choisi **domaine par domaine** : on ne peut pas déduire le niveau de construction du niveau
d'usage, ni l'inverse. Ce constat interdit tout raisonnement par analogie et **maintient le
point comme une interprétation, non un fait**.

**Portée de l'incertitude, chiffrée.** U calculés depuis la doc (résistances de surface
**assumées [I]** : Rsi 0,13 / Rse 0,04 pour les parois verticales sur l'extérieur ; Rsi 0,17 /
Rse 0 contre terrain ; Rsi = Rse = 0,17 pour un flux descendant intérieur) :

| Composition | R couches GW | U GW | R couches ZW | U ZW | U GW / U ZW |
|---|---|---|---|---|---|
| `aw1` Aussenwände | 4,925 | **0,196** | 7,955 | **0,123** | 1,59 |
| `aw2` gegen Erdreich | 3,119 | **0,308** | 4,948 | **0,197** | 1,56 |
| Boden über Erdreich | 3,165 | **0,300** | 4,994 | **0,194** | 1,55 |
| Zwischendecke g. unkond. (Keller) | 3,736 | **0,245** | 5,268 | **0,178** | 1,38 |
| Flachdach | 4,908 | **0,197** | 8,113 | **0,121** | 1,63 |
| Zwischendecke (identique GW/ZW) | 1,329 | 0,599 | 1,329 | 0,599 | 1,00 |
| `iw1` (identique GW/ZW) | 3,057 | 0,301 | 3,057 | 0,301 | 1,00 |
| `iw2` (identique GW/ZW) | 0,123 | 2,61 | 0,123 | 2,61 | 1,00 |

→ écart de **~55 à 63 %** sur le U des éléments extérieurs opaques ; **nul** sur les éléments
intérieurs. Le choix pèse donc sur : test 5 → façades des 8 zones **et toiture des 6 zones du
2. OG** ; test 6 → façades du RDC (+ plancher sur cave si §8.1 était renversé) ; test 4 → figé
sur GW, donc non concerné.

**Résolution empirique recommandée** : identique au §8.1 — simuler GW et ZW, confronter aux
bandes de `Resultaterfassung_Test5.xlsx` / `_Test6.xlsx`. Un écart de 55 % sur le U opaque est
très largement hors bande : **le test est discriminant et tranchera**. **Ne pas déclarer les
tests 5 et 6 « done » avant.**

### 8.3 Consignes de température des tests 4 et 5 — **chaîne normative établie ; test 5 reconstruit, test 4 encore ouvert**

**Réponse à la question posée** :
1. **Confirmé [V]** : la cellule de valeur est **vide dans le PDF source**, pour le test 4
   (`spec_test4_cellules.txt` p. 2 l. 1-3 : `Raumluft-` / `Sollwerte` / `temperatur`, sans
   valeur, alors que la ligne suivante porte bien « CO2 | 600 – 1000 ppm, Aussenluftkonzentration
   400 ppm ») **et** pour le test 5 (`spec_test5_cellules.txt` p. 2 l. 1 : « Sollwerte |
   Temperatur », sans valeur, la ligne suivante portant « CO2 | 950 – 1200 ppm »). Défaut de
   spécification, cf. E10.
2. **Aucun Anwenderbericht ne donne de valeur numérique de consigne.** Recherche exhaustive sur
   les 16 rapports : les seules mentions sont **qualitatives** —
   `anwender_test4_1.txt` l. 15-16, `anwender_test5_1.txt` l. 14-15, `anwender_test6_1.txt`
   l. 14-15 : le tableur a été étendu pour « **zeitabhängige Raumtemperatur-Sollwerte** » et
   pour la « **Wahl des Raumtemperatur-Sollwertes zwischen operativ und Luft** » ;
   `anwender_test4_2.txt` l. 17 (« die operativen Temperaturen sind ähnlich verteilt ») ;
   `anwender_test4_3.txt` l. 14 (« Bei Anlagensimulationen wertet TAS nur die Raumlufttemperatur
   aus ») ; `anwender_test5_3.txt` l. 51 et `anwender_test6_3.txt` l. 36 (« ideale Heater und
   Cooler »). **Négatif vérifié [V].**
3. **Mais la spécification ne délègue PAS la consigne à SIA 2024** : elle relève de
   **SIA 380/2:2022 §5.2.2.3 et figure 1**, qui sont **dans `/refs`**. Chaîne établie :

   | Maillon | Source | Contenu |
   |---|---|---|
   | Nature de la grandeur | SIA 380/2 §5.2.2.3, l. 1414-1415 **[V]** | « Les valeurs de consigne peuvent être fixées pour la **température moyenne de l'air intérieur** ou pour la **température opérative simplifiée**. Le choix est à discuter avec le mandant. » → explique **mot pour mot** la « Wahl … zwischen operativ und Luft » des rapports |
   | Forme des consignes | SIA 380/2 §5.2.2.3, l. 1421-1435 **[V]** | régulation **sans** communication (`HEAT_EMIS_CTRL_DEF = 1 ou 2` selon SN EN ISO 52120-1 tab. 5) → **valeurs constantes** au maximum de la courbe de consigne chauffage / au minimum de la courbe de consigne refroidissement ; régulation **avec** communication (3 ou 4) → **courbes variables de la figure 1** (lignes en pointillé) |
   | Courbes | SIA 380/2 **figure 1** (l. 1446-1467) **[V] partiellement** | « Températures ambiantes de consigne pour le chauffage et le refroidissement » ; axes lus : ordonnée **20 à 27 °C** (20 = limite inférieure, 27 = limite supérieure, 22 = `valeur de consigne chauffage, Tset;H`), abscisse **10 à 25 °C** = « Température extérieure moyenne glissante sur **48 heures** » ; écart `Tctr` entre consigne et limite |
   | Origine du confort | SIA 380/2 §5.2.2.5, l. 1469-1472 **[V]** | limites « découlent des exigences de **SIA 180:2014 §2.3.1** … correspondent à celles de **SIA 180:2014, figure 4, pour les locaux d'habitation et les bureaux** » |
   | Décalage par usage | SIA 380/2 §5.2.2.5, l. 1477-1479 **[V]** | « les limites seront décalées suivant la **différence entre les valeurs de dimensionnement de l'utilisation correspondante et les utilisations 1.01 à 3.03 selon SIA 2024:2021, tableau 11** » |
   | Décalages chiffrés | SIA 4010 §3.2, l. 384-390 **[V]** | « Le décalage des courbes pour les utilisations **autres que les utilisations 1.01 à 3.03** … donne **notamment** une courbe … décalée de **1 K** pour les utilisations 3.04, 5.01 à 5.03 et **6.03 et 6.04 (cuisines)**, et de 3 K pour 9.01 … Un déplacement de la courbe de point de réglage **supérieure vers le haut** … pour les utilisations **6.03 et 6.04 (cuisines) de 2 K**, pour 9.01 de 4 K » |
   | Simplification | SIA 380/2, l. 1481-1482 **[V]** | « Pour simplifier … on peut … utiliser les valeurs de consigne selon **SIA 2024:2021, annexe B, tableau 13** » |
   | Consignes de **dimensionnement** | SIA 380/2 §4.2.4 (l. 1271-1273) et §4.3.2.1 (l. 1322) **[V]** | pour la **puissance** de base : « tirées de **SIA 2024:2021, tableau 11** » ; pour la puissance « propre au système » : courbes variables de la figure 1 |

4. **Conséquence pour le test 5 — reconstruction.** Les usages du test 5 sont **3.1, 3.2, 3.3**
   (doc p. 10 l. 16, 18, 22-27) = **3.01 à 3.03**, donc dans la plage **explicitement non
   décalée** de SIA 4010 §3.2. Les consignes du test 5 sont donc la **courbe de base** de
   SIA 380/2 figure 1. Or cette courbe de base est **numériquement lisible** dans la
   spécification du test 6 (§8.4), et le contrôle croisé de la cuisine (21 °C = 22 − 1 K) la
   confirme. D'où, **[I] fort, confiance ~80 %** :

   | Test 5 — consigne (Raumtemperatur, air ou opérative selon §5.2.2.3) | Θe, moyenne glissante 48 h |
   |---|---|
   | **Chauffage** : 22,0 °C | ≤ 19 °C |
   | montée linéaire 22,0 → 23,5 °C | 19 → 23,5 °C |
   | 23,5 °C | ≥ 23,5 °C (palier **[I]**) |
   | **Refroidissement** : 23,0 °C | ≤ 12 °C |
   | montée linéaire 23,0 → 25,0 °C | 12 → 17,5 °C |
   | 25,0 °C | ≥ 17,5 °C (palier **[I]**) |

   Réserves explicites : (a) le palier au-delà du dernier point de rupture est **inféré** ;
   (b) l'hypothèse « usage 6.02 non décalé » qui autorise à identifier la courbe du test 6 à la
   courbe de base est **[I]** (voir §8.4) ; (c) rien ne dit si le test 5 emploie les **courbes**
   ou les **constantes** de §5.2.2.3 — l'usage des programmes de référence
   (« **zeitabhängige** Raumtemperatur-Sollwerte ») plaide fortement pour les **courbes** [U].
   **Vérification obligatoire avant figeage : rendu visuel de SIA 380/2:2022 figure 1** (p. 26,
   `refs/SIA-380-2-2022.pdf`). C'est **dans le dépôt** : levier le moins coûteux et le plus
   décisif — il n'avait pas été identifié à la rév. 1.

5. **Test 4 — reste ouvert [?].** L'usage est **4.4 Hörsaal** (doc p. 10 l. 17), **hors** de la
   plage 1.01-3.03. Un décalage est donc possible et se calcule d'après **SIA 2024:2021
   tab. 11**, absent de `/refs`. Deux indices convergents mais insuffisants :
   - SIA 4010 §3.2 énumère les usages décalés et **ne cite pas 4.04** — mais l'adverbe
     « **notamment** » rend la liste **non exhaustive** : le silence n'est pas une preuve.
     **[I] ~65 %** en faveur d'un décalage nul.
   - Le test 4 demande les **Zielwerte** de SIA 2024 (p. 1 l. 18) là où les tests 5 et 6
     demandent les Standardwerte : si tab. 11 distingue ces niveaux pour la température, la
     consigne du test 4 diffère **aussi** par ce biais. **[?]**
   Certain en revanche : la consigne du test 4 porte sur la **température de l'air** — libellé de
   ligne « Raumluft-temperatur » (p. 2 l. 1-3) **et** « PI-Regler zur Einhaltung des
   **Raumlufttemperatur**-Sollwerts » (p. 3 l. 14). **[V]**
   ⚠ Ne pas confondre avec la **température de soufflage** : « Zulufttemperatur | 16 – 22.5°C
   (kühlen), 22.5 – 29°C (heizen), PI-Regler … » (p. 3 l. 12-14). **[V]**
   → **Conclusion honnête : la consigne de local du test 4 n'est déterminable par AUCUNE source
   disponible.** Elle nécessite SIA 2024:2021 tab. 11 (et, si l'on veut la voie simplifiée,
   annexe B tab. 13). C'est la **justification d'acquisition** demandée : cf. §11.

### 8.4 Consignes du test 6 — **LUES** (nouveau)

L'extraction par coordonnées rend le graphique de la spécification du test 6 exploitable.
`spec_test6_cellules.txt` p. 2 l. 35-47 — axe des ordonnées **« Raumlufttemperatur »**
(donc **température d'air**, non opérative **[V]**), graduations 21,5 à 25,5 ; abscisse
**« gleitender 48-h-Mittelwert Aussenlufttemperatur »**, −15 à 35 °C ; légende `Kühlen` /
`Heizen` ; **quatre étiquettes de points** : `17.5; 25`, `23.5; 23.5`, `12; 23`, `19; 22`.

Recoupement de position **[C]** : dans l'extraction `-layout` (`spec_test6.txt` l. 87-99), les
étiquettes `17.5; 25` et `12; 23` sont à la **même abscisse de colonne**, et `23.5; 23.5` et
`19; 22` à une autre, plus à droite — c'est-à-dire regroupées **par courbe** (points de gauche /
points de droite). Combiné à la contrainte physique T_consigne,froid ≥ T_consigne,chaud (la
répartition inverse donnerait un refroidissement à 22 °C sous un chauffage à 23 °C), l'affectation
est **univoque** :

| Test 6 — Restaurant, consigne de **température d'air** | Θe, moyenne glissante 48 h |
|---|---|
| **Heizen** 22,0 °C | ≤ 19 °C |
| 22,0 → 23,5 °C (pente exactement 1/3) | 19 → 23,5 °C |
| 23,5 °C | ≥ 23,5 °C **[I]** |
| **Kühlen** 23,0 °C | ≤ 12 °C |
| 23,0 → 25,0 °C (pente 2/5,5 = 0,364) | 12 → 17,5 °C |
| 25,0 °C | ≥ 17,5 °C **[I]** |

Statut : les **quatre points [V]** (deux extractions indépendantes) ; l'**affectation aux
courbes [C]** ; les **paliers [I]**.

**Contrôle croisé qui verrouille la valeur 22 °C — et résout l'ancien §8.2 (cuisine)** : la
cuisine est l'usage **6.4**, pour lequel SIA 4010 §3.2 (l. 386-387) prescrit une courbe
inférieure **décalée de 1 K**. Or la spécification donne à la cuisine « Sollwert heizen:
**21°C** » (`spec_test6_cellules.txt` p. 3 l. 25-27) = **22 − 1**. **[C]** Cette coïncidence :
- confirme que le palier de chauffage de la courbe de base est bien **22,0 °C** ;
- confirme que le décalage des cuisines est **vers le bas** pour la courbe inférieure ;
- établit **[I]** que l'usage **6.02 (Restaurant) n'est PAS décalé** — donc que la courbe lue
  ci-dessus **est** la courbe de base de SIA 380/2 figure 1, ce qui autorise le report au
  test 5 (§8.3.4). Confiance ~85 %.
- **résout l'ancienne contradiction §8.2 de la rév. 1** : la cuisine porte une consigne de
  chauffage (21 °C) **sans émetteur** (« Wärmeabgabe | keine ») parce que sa chaleur ne peut
  venir que de l'air neuf ; la consigne est la **cible de la régulation de l'air**, pas d'un
  émetteur de zone. Reste à confirmer côté moteur que 21 °C est atteignable avec un air neuf
  plafonné à 20 °C (`spec_test6_cellules.txt` p. 4 l. 26-33 : Zulufttemperatur glissante
  (12 ; 20) → (20 ; 18) °C) : très probablement **non** en hiver, la température de la cuisine
  flottant alors sous 21 °C sous l'effet des apports internes de process. **[I]**, à vérifier
  numériquement. Note : la cuisine reçoit « inkl. **Prozesswärme** (Strahlungsanteil 15%) »
  (p. 2 l. 57) — apport interne considérable qui rend le point crédible.

### 8.5 Ce qui reste réellement ouvert

| # | Point | Impact | Ce qui le lèverait |
|---|---|---|---|
| **O1** | **Consigne de local du test 4** (usage 4.4 Hörsaal) : valeur absente du PDF, décalage éventuel par rapport à la courbe de base inconnu, niveau « Zielwerte » de SIA 2024 non caractérisé | **bloquant** pour le test 4 et pour tout couplage `101`↔zones du test 5 | **SIA 2024:2021 tab. 11** (+ annexe B tab. 13) — §11 ; à défaut, FAQ SIA 4010 (§4.6.1, `sia_4010_2023.txt` l. 2790-2792) |
| **O2** | **Valeurs exactes de SIA 380/2 figure 1** (limites, consignes, `Tctr`, points de rupture) | conditionne §8.3.4 et §8.4 ; sans cela, la courbe reconstruite reste une inférence | **rendu visuel de `refs/SIA-380-2-2022.pdf` p. 26** — dans le dépôt, coût nul |
| **O3** | **GW ou ZW** : aucune prescription trouvée ; défaut GW argumenté à ~80 % | ~55-63 % sur le U opaque, tests 5 et 6 | simulation comparative contre `Resultaterfassung_Test5/6.xlsx` (§8.2) ; ou FAQ SIA / sous-commission (SIA 4010 §4.6.2) |
| **O4** | **Plancher sur cave** : adiabatique retenu à ~80 % | 273 m² à ΔU 0,245 W/(m²K), test 6 | simulation comparative (§8.1) ; ou FAQ SIA |
| **O5** | **Régulation avec ou sans communication** (§5.2.2.3) : courbes variables ou constantes aux extrema ? | change la consigne de 0 à 1,5 K et peut créer un chauffage/refroidissement **simultané** (SIA 380/2 §5.2.2.4, l. 1438-1444) | les rapports disent « **zeitabhängige** Sollwerte » [U] → courbes ; à confirmer par la classe `HEAT_EMIS_CTRL_DEF` de chaque test (SN EN ISO 52120-1 tab. 5, **absente de `/refs`**) |
| **O6** | **Air ou opérative ?** Tranché pour le test 4 (air, p. 3 l. 14) et le test 6 (axe « Raumlufttemperatur »). **Non tranché pour le test 5** : la ligne dit seulement « Temperatur » (p. 2 l. 1) | les classeurs exigent **les deux** distributions (`PREUVE_classeur_test4.txt` l. 22 : `P21=Mittlere Raumlufttemperatur`, `W21=Operative Temperatur`) | `Resultaterfassung_Test5.xlsx` ; SIA 380/2 §5.2.2.3 laisse le choix au mandant |
| **O7** | **Variante 5A-5D à employer au test 7** pour « Elektrische Energie Tests 4 bis 6 » : non spécifiée | change directement une grandeur de test du test 7 | **[U]** Tas a pris **5C** et le signale explicitement (`anwender_test7_4.txt` l. 35-38) ; à confirmer par les autres classeurs |

### 8.6 Températures ambiantes des gaines hors zones — **partiellement levé [U]**

- Test 5 : donné pour Zentrale/Steigzone (15/28 °C, p. 2 l. 15-16) ; **non donné** pour le
  « Deckenbereich Korridor 1. + 2. OG » (20 m, U 1,1 W/(m²K), p. 2 l. 11-12) ni pour les gaines
  « Deckenbereich Zonen » (p. 2 l. 13-14), alors que « Wärmeverluste Verteilung » est un
  diagnostic demandé (p. 5 l. 27-31). **[V]** du manque.
- **Usage documenté [U]**, identique pour les tests 5 et 6 : « Die Berechnung der Verteilverluste
  wurde vereinfacht durchgeführt: **Steigzonen: Verluste mit konstanter Umgebungstemperatur im
  Sommer 28 °C, im Winter 15 °C. In den Zonen wurde als Umgebung die mittlere Raumtemperatur
  aller Zonen verwendet. Die Verluste werden weder in der Zone noch berücksichtigt im
  Wärmebedarf.** » (`anwender_test5_3.txt` l. 53-56 ; `anwender_test6_3.txt` l. 38-41, mot pour
  mot). Un seul programme sur quatre le documente ; les autres soit ne calculent pas ces pertes
  (`anwender_test5_2.txt` l. 20-24, EnergyPlus), soit ne les définissent pas
  (`anwender_test5_4.txt` l. 36-37, Tas). → **Convention retenue** : gaines en colonne à
  15/28 °C ; gaines dans une zone à la température **moyenne** des zones ; pertes **non**
  imputées à la zone ni au besoin de chaleur. Statut **[U]**, confiance ~70 % (un seul
  déclarant), **à confronter à la bande**.
- Test 6 : la spécification ne donne **ni U-Wert ni température** pour ses gaines (p. 3
  l. 32-36) — argument fort du §8.1.

### 8.7 Adjacences géométriques réelles — inchangé **[?]**

Je n'ai que des surfaces, pas de topologie. Non établi :
- le Hörsaal `101` a-t-il des parois **extérieures** (et lesquelles) ?
- quels locaux du test 5 sont **mitoyens** du Hörsaal, sur quelle surface, à quel niveau ?
- le Hörsaal est-il au-dessus du **Restaurant** (interface test 4 ↔ test 6) ?
- répartition des fenêtres par local (aucune source texte) ;
- **nouveau** : **lesquels** de `201`-`204` portent la « schwere Innenwand » (§3.2, appui 5) ?
- **nouveau** : mapping colonne ↔ groupe de distribution dans `Lastverläufe_220607.xlsx`.
→ Ce sont des **calculs de géométrie**, pas des lectures de norme : à faire par
`ve-adapter-engineer` sur `IfcRelSpaceBoundary` / les DWG, **avant** d'écrire les affectations
adiabatiques.

---

## 9. Conséquences directes pour l'import IESVE

1. **11 zones à créer au total**, jamais 29 : `101` (test 4) ; `100`, `102`, `200`, `201`, `202`,
   `203`, `204`, `205` (test 5) ; `001`, `002` (test 6). Test 7 : **aucune** (confirmé [U], §3.4).
2. `101` = **une seule** zone de 6,38 m de hauteur ; ne pas la couper au niveau 6.8.
3. Ne pas créer de zone sur `Storey 9.8` (niveau de toiture).
4. Surfaces de référence = `GrossFloorArea` IFC en valeur absolue (§5).
5. Trois modèles séparés (un par test) sont **conformes** et plus sûrs que le bâtiment complet :
   la règle §4 rend alors toutes les parois intérieures adiabatiques, sans avoir à importer les
   consignes d'un autre test. Le modèle couplé n'est autorisé qu'une fois O1 levé.
6. **Conserver la masse thermique des éléments adiabatiques** — décision maintenant appuyée
   (§4.2, confiance ~95 %) et **distinguer iw1 / iw2 par local** dans les bureaux `201`-`204`.
7. `002` est couplée à `001` par un transfert d'air de **350 m³/h** : transfert inter-zones, pas
   de l'air neuf. Réserve : Tas n'a pas pu le modéliser (`anwender_test6_4.txt` l. 22-23) — la
   bande de référence intègre donc **un** programme sans transfert.
8. Paramétrer les matériaux en **deux jeux GW/ZW à épaisseurs identiques**, **GW par défaut**
   (§8.2), le test 4 étant figé sur GW ; **aucun élément intérieur n'est affecté** par ce choix.
9. Ne pas activer de régulation d'éclairage sur la lumière du jour (§7.3).
10. **Plancher `001`/`002` sur cave : adiabatique** par défaut (§8.1), avec la variante
    non adiabatique paramétrable pour l'essai discriminant.
11. Consignes : implémenter une **courbe** fonction de la moyenne glissante 48 h de la
    température extérieure (pas une constante), avec un commutateur **air / opérative**
    (SIA 380/2 §5.2.2.3). Valeurs du test 6 : §8.4 ; du test 5 : §8.3.4 (à confirmer par O2) ;
    du test 4 : **bloqué** par O1.
12. La moyenne glissante 48 h de la température extérieure est une grandeur **d'entrée à
    calculer** depuis le fichier climatique — la prévoir dans `engine/`.

---

## 10. Ce qui lèverait le plus d'incertitudes, par ordre de rendement

| Priorité | Source | Ce qu'elle tranche | Coût |
|---|---|---|---|
| **1** | **Rendu visuel de `refs/SIA-380-2-2022.pdf`, figure 1 (p. 26, §5.2.2.4) et tableau 3 (p. 35-36)** | **O2** (courbes de consigne, `Tctr`, points de rupture) et la réserve d'extraction du §8.2 (épaisseurs VL/VC). **Déjà dans le dépôt.** | nul |
| **2** | **SIA 2024:2021** (ou prSIA 2024:2021) — tab. 11, annexe B tab. 13, horaires, simultanéités | **O1** (consigne du test 4), le décalage de l'usage 4.04, et **toutes** les données d'usage des 11 zones (§11) | achat |
| 3 | **Simulation comparative GW/ZW et cave adiabatique/non** contre `Resultaterfassung_Test5.xlsx` / `_Test6.xlsx` | **O3** et **O4**, empiriquement et sans ambiguïté | travail moteur |
| 4 | **Géométrie IFC (frontières d'espaces) ou DWG** | §8.7 : adjacences, parois extérieures du Hörsaal, fenêtres par local, `201`-`204` iw1/iw2 | travail adaptateur |
| 5 | **`Resultaterfassung_Test4/5/6/7.xlsx` et `Lastverläufe_220607.xlsx`** | **E9** (grandeurs et critères des tests 4, 6, 7, absents des PDF), **O6**, **O7**, mapping des groupes du test 7 | lecture xlsx |
| 6 | **FAQ SIA 4010** (annoncée par §4.6.1, `sia_4010_2023.txt` l. 2790-2792 ; hors dépôt) | **O3**, **O4** avec autorité supérieure à toute inférence | demande SIA |
| 7 | **SN EN ISO 52120-1:2022 tab. 5** | **O5** (classes `HEAT_EMIS_CTRL_DEF` / `CLG_EMIS_CTRL_DEF`, donc courbes ou constantes) | achat |
| — | ~~Anwenderberichte des tests 5, 6, 7~~ | **ÉPUISÉ** : dépouillés, **muets** sur l'enveloppe, les constructions et les consignes numériques. Utiles seulement pour les usages de modélisation (§12) | fait |

---

## 11. Usages SIA 2024:2021 requis — bon de commande

**Constat** : SIA 2024:2021 (et prSIA 2024:2021) sont **absents de `/refs`**. Les spécifications
des tests 4, 5 et 6 et la documentation y renvoient **au moins 21 fois**. Sans ce cahier
technique, **aucune** des 11 zones ne peut être renseignée en apports internes, occupation et
horaires, et la consigne du test 4 reste indéterminable (O1).

### 11.1 Usages à extraire (numérotation de la documentation / des specs)

| Usage | Locaux | Niveau de valeur demandé | Source du renvoi |
|---|---|---|---|
| **4.4 Hörsaal** (« Standardnutzung "Hörsaal" ») | `101` | **Zielwerte** | `spec_test4_cellules.txt` p. 1 l. 18 ; doc p. 10 l. 17 |
| **3.1 Einzel-, Gruppenbüro** | `201`-`205` | **Standardwerte** | `spec_test5_cellules.txt` p. 1 l. 18 ; doc p. 10 l. 23-27 |
| **3.2 Grossraumbüro** | `102` | **Standardwerte** | idem ; doc p. 10 l. 18 |
| **3.3 Sitzungszimmer** | `100`, `200` | **Standardwerte** | idem ; doc p. 10 l. 16, 22 |
| **6.2 Selbstbedienungsrestaurant** | `001` | **Standardwerte** | `spec_test6_cellules.txt` p. 1 l. 19-21 (⚠ la doc dit 6.1, cf. E2) |
| **6.4 Küche zu Selbstbedienungsrestaurant** | `002` | **Standardwerte**, « inkl. **Prozesswärme** (Strahlungsanteil 15 %) » | `spec_test6_cellules.txt` p. 2 l. 55-57 (⚠ la doc dit 6.3, cf. E2) |
| *(pour mémoire, variante « bâtiment complet » seulement)* | 12.1, 12.3, 12.4, 12.7, 12.11 | — | doc p. 10 l. 7-33 |

### 11.2 Données à extraire, par renvoi relevé

| # | Donnée | Renvoi (fichier, ligne) |
|---|---|---|
| 1 | **Tab. 11 — valeurs de dimensionnement** : température ambiante de consigne chauffage et refroidissement, surface par personne, activité, puissances installées | `sia_380_2_2022.txt` l. 1271-1273 (§4.2.4, puissance de chauffage) ; l. 1322 (§4.3.2.1, puissance de froid) ; l. 1477-1479 (§5.2.2.5, **calcul du décalage des courbes**) ; `sia_4010_2023.txt` l. 384-390 (§3.2) |
| 2 | **Annexe B, tab. 13 — valeurs de consigne** (voie simplifiée) | `sia_380_2_2022.txt` l. 1481-1482 |
| 3 | Personen : **Anzahl**, **Aktivitätsgrad**, **Zeitplan**, **Jahresgleichzeitigkeit** — tests 5 et 6 | `spec_test5_cellules.txt` p. 1 l. 29-36 ; `spec_test6_cellules.txt` p. 2 l. 23-30 et p. 3 l. 13-20 |
| 4 | Personen : **Zeitplan** et **Jahresgleichzeitigkeit** — test 4 (l'effectif 55 et 1,2 met sont **donnés**) | `spec_test4_cellules.txt` p. 1 l. 29-30 |
| 5 | Geräte : **Wärmeeintragsleistung**, **Zeitplan**, **Jahresgleichzeitigkeit** — tests 5 et 6 | `spec_test5_cellules.txt` p. 1 l. 35-38 ; `spec_test6_cellules.txt` p. 2 l. 29-32 et p. 3 l. 19-22 |
| 6 | Geräte : **Zeitplan** et **Jahresgleichzeitigkeit** — test 4 (10 W/m² **donné**) | `spec_test4_cellules.txt` p. 1 l. 33-34 |
| 7 | Beleuchtung : **Wärmeeintragsleistung** et **Zeitplan** — tests 5 et 6 (test 4 : 6,4 W/m² et « Ein 07:00-18:00, aus im Juli » **donnés**) | `spec_test5_cellules.txt` p. 1 l. 39-41 ; `spec_test6_cellules.txt` p. 2 l. 33-34 et p. 3 l. 23-24 ; test 4 p. 1 l. 35-38 |
| 8 | **Débits d'air neuf de référence** — cités **pour être écartés**, mais à connaître pour tracer l'écart : « Nenn-Volumenstrom 10 m3/(h∙m2) {**abweichend von SIA 2024:2021**} » (test 4) et « 25 m3/h pro Person (alle Nutzungen, **abweichend von SIA 2024:2021**) » (test 5) | `spec_test4_cellules.txt` p. 1 l. 19-21 ; `spec_test5_cellules.txt` p. 1 l. 20-22 |
| 9 | **Zeitpläne** de personnes, appareils et éclairage — renvoi global de la documentation | `doc_beispielgebaeude_cellules.txt` p. 10 l. 2 et l. 34-36 |
| 10 | Édition de référence : **SIA 2024:2021 vs prSIA 2024:2021** — le test 6 emploie **les deux** libellés | E5 ; `spec_test6_cellules.txt` p. 1 l. 19 et p. 2 l. 28 |
| 11 | Distinction **Standardwert / Zielwert / Grenzwert** dans SIA 2024, pour chaque grandeur ci-dessus | requise par les niveaux différents du test 4 (Zielwerte) et des tests 5-6 (Standardwerte) |
| 12 | Contrôle de cohérence à faire dès réception : 1040 m³/h ÷ 25 m³/(h·pers) = **41,6 personnes** sur 269,87 m² du test 5 → **6,5 m²/pers** ; à confronter à la surface par personne de tab. 11 pour 3.01-3.03 | `spec_test5_cellules.txt` p. 2 l. 18 et p. 1 l. 20-22 |

**Autres normes citées par les tests et absentes de `/refs`** (à signaler dans le même mouvement) :
SIA 2028 (climat DRY, cité en tête de **chaque** spécification), SIA 180:2014 (origine des
limites de confort, `sia_380_2_2022.txt` l. 1469-1470), SN EN ISO 52120-1:2022 tab. 5 (classes
de régulation d'émission, **O5**), SN EN 15316-2:2017 (`Tctr`, l. 1417-1419), SN EN 16798-5-1 et
-7 (dont l'annexe nationale NA.2.2.4 utilisée par un programme de référence,
`anwender_test5_1.txt` l. 35-36), SN EN 16798-9 / -13 / -15, SN EN 15316-4-2 / -4-3 / -5 (test 7),
SIA 387/4:2023 (commande de protection solaire).

---

## 12. Apports secondaires des Anwenderberichte (statut **[U]** : usage, non prescription)

### 12.1 Ensemble contributeur des bandes

**Quatre** programmes de référence par test, identiques pour les tests 4 à 7 :

| Programme | Version | Rapports | Auteur / date |
|---|---|---|---|
| Tableurs des normes EN (colonne « Excel » des classeurs) | EN ISO 52016-1 (E4Tech / SIA 2044) étendu par G. Zweifel + EN 16798-5-1 (epb.center 25.10.2021) + EN 16798-7 (12.7.2021, **test 4 seulement**) + EN 16798-9 / -13 / 15316-4-2 (test 7) | `anwender_test4_1`, `_test5_1`, `_test6_1`, `_test7_1` | G. Zweifel, 11.11.2022 |
| EnergyPlus / OpenStudio | 9.1.0 | `_test4_2`, `_test5_2`, `_test6_2`, `_test7_2` | C. Messmer, 12.11.2022 |
| IDA-ICE | 5.0 Beta 22 (tests 4-6), Beta 23 (test 7) | `_test4_4`, `_test5_3`, `_test6_3`, `_test7_3` | F. Sidler / Ch. Stettler, 18-21.11.2022 |
| EDSL Tas | 9.5.4 | `_test4_3`, `_test5_4`, `_test6_4`, `_test7_4` | R. Schär-Sommer / M. Fehr, 17.11.2022 et 15-16.05.2023 |

Corroboré par la structure du classeur : `PREUVE_classeur_test4.txt` l. 9-12 — colonnes
`D = 'Daten Testprogramm'` (le candidat), `E = IDA_ICE`, `F = Excel`, `G = EnergyPlus`,
`H = TAS` ; bande en `T8 = Mittelwert`, `U8 = obere Grenze`, `V8 = untere Grenze`. **[V]**
Le nombre de contributeurs est donc **4**, non 5 : la colonne `D` est le programme testé.

**Nombre d'instances de zone déclarées** : test 4 → 3 instances du tableur 52016-1 pour 1 zone
(`anwender_test4_1.txt` l. 8 ; l'itération de la fig. p. 1 explique pourquoi) ; test 5 → **6**
instances pour 8 locaux (`_test5_1.txt` l. 8, 18-20) ; test 6 → **2** instances pour 2 locaux
(`_test6_1.txt` l. 8, 18). Cohérent avec le zonage du §1.

### 12.2 Variantes du test 5 — reconstruction **[C]**

`spec_test5_cellules.txt` p. 3 l. 6-14 et p. 4 l. 34-35 donnent trois lignes « Variante | 5A |
5B | 5C | 5D » avec **deux** valeurs seulement par ligne. La répartition sur les quatre colonnes
se reconstruit sans ambiguïté par recoupement avec les rapports :

| Variante | Konstantdruckanteil (ZUL+ABL) | WRG rotatif | Humidificateur |
|---|---|---|---|
| **5A** | **50 + 50 Pa** | Hygroskopisch (η_T 0,67 ; η_x 0,42) | Kontaktbefeuchter |
| **5B** | 270 + 270 Pa | Hygroskopisch | Kontaktbefeuchter |
| **5C** | 270 + 270 Pa | **Nicht hygroskopisch** (η_T 0,69 ; η_x 0,3) | Kontaktbefeuchter |
| **5D** | 270 + 270 Pa | Nicht hygroskopisch | **Dampf** |

Appuis : (a) IDA-ICE donne **un** jeu de coefficients de ventilateur pour « Test 5A » et **un
autre** pour « Test 5B…D » (`anwender_test5_3.txt` l. 13-27) → la coupure de pression est
1 / 3, pas 2 / 2 ; (b) IDA-ICE : « Rotortype: **Hygroscopic** » pour « Test A, B » et
« **Untreated** » pour « Test C, D » (l. 29-35) → coupure 2 / 2 ; (c) Tas, au test 7 : « wurde
**Test 5C mit Kontaktbefeuchter und höherem Konstantdruckanteil** herangezogen. Die Varianten
mit **tieferem Konstantdruckanteil** oder **Dampfbefeuchter** weisen einen abweichenden
elektrischen Energiebedarf auf » (`anwender_test7_4.txt` l. 35-38) → 5C = pression haute +
contact, et il existe des variantes à pression basse et à vapeur ; (d) Zweifel : « Die
Veränderungen der Resultate zwischen den Varianten (**Ventilatorregelung, WRG-Typ und
Befeuchtertyp**) » (`anwender_test5_1.txt` l. 64-65) → exactement **trois** changements pour
quatre variantes, soit un paramètre modifié à chaque marche. Confiance ~90 %.
Grandeurs à livrer, différentes par variante : `spec_test5_cellules.txt` p. 4 l. 46-60 et p. 5
l. 1-3 ; diagnostics p. 5 l. 12-40, « **Test 5D keine** » (p. 5 l. 41). **[V]**
Critères du test 5 (p. 5 l. 4-9) : « Zulässiger Bereich für Jahressummen: **Mittelwerte der
Referenzprogramme +/- maximale Abweichung**. Die **Häufigkeitsverteilungen** müssen im
**Streubereich** der Referenzprogramme liegen. » **[V]** — identique aux formules des classeurs
(`PREUVE_classeurs.txt` l. 9-11).

### 12.3 Reprise d'air, apports internes, régulation CO2 — usages notables

- **Ancien §8.6 (test 5 : d'où l'air est-il repris ?) — LEVÉ [U], confiance ~90 %** : « Ebenso
  wurde die **Ablufttemperatur volumenstromgewichtet aus den verschiedenen Raumtemperaturen**
  errechnet » (`anwender_test5_1.txt` l. 25-26). La reprise se fait **dans les 8 zones
  desservies**, l'état est le mélange pondéré par les débits ; **aucune cascade par les WC**.
  Même formulation pour le test 6, « aus den **beiden** Raumtemperaturen » (`_test6_1.txt`
  l. 23-25). Le terme « Ersatzluftanlage » reste défini dans **aucune** source de `/refs`.
- **Régulation CO2, substitut employé faute de bilan CO2** : « ein vereinfachter Ansatz gemäss
  SN EN 16798-7, **Anhang NA, Ziffer NA.2.2.4** … fctrl = focc + **0,33** · (1 − focc) » au
  test 4 (`anwender_test4_1.txt` l. 66-73) et « fctrl = focc + **0,167** · (1 − focc) » au test 5,
  « wobei der Faktor zur Berücksichtigung des **kleineren CO2-Proportionalbands (gegenüber
  Test 4)** auf 0.167 gesetzt wurde » (`anwender_test5_1.txt` l. 34-46). **[U]** — utile pour
  interpréter les écarts de débit aux premières heures d'occupation, **pas** une prescription.
- **Émetteurs idéaux** : IDA-ICE a utilisé « **ideale Heater und Cooler** » dans les zones du
  test 5 (`anwender_test5_3.txt` l. 51) et pour le Restaurant du test 6 (`_test6_3.txt` l. 36).
- **Défauts et non-livraisons connus** (à retenir avant de conclure d'un écart à la bande) :
  Tas n'a modélisé **ni** la KVS-WRG du test 6 (remplacée par un échangeur à η constant 0,71,
  `_test6_4.txt` l. 10-15) **ni** le transfert Restaurant→Küche (l. 22-23) ; sa « Wärmeabfuhr
  Luftkühler total » est ~30 % au-dessus des autres, cause déclarée : absence d'heure d'été
  (l. 34-37) ; au test 5, Tas n'a pas défini les pertes de distribution (l. 36-37) et sa
  « Luftkühler latent » est « unrealistisch tief » (l. 38-42) ; EnergyPlus n'a pas calculé les
  pertes et fuites de gaines au test 5 (`_test5_2.txt` l. 20-24) ; au test 7, Tas signale
  l'absence de colonne « Kälterückgewinnung » dans le fichier de résultats (`_test7_4.txt`
  l. 43) et une production PV nettement surestimée (l. 60-64).

### 12.4 Défauts des sources — recoupement croisé

| Défaut | Preuve |
|---|---|
| `anwender_test4_3.txt` (Tas, test 4) contient un paragraphe **du test 3** : « Aufgrund der Feststellungen aus Test 2 kann in **Test 3** nur eine Auswahl an Fällen gerechnet werden (Sonnenschutzregelung 2 und 4) » | l. 10-12 — défaut déjà connu, **confirmé** |
| `anwender_test6_3.txt` (IDA-ICE, test 6) porte l'intitulé « Eingaben Zuluftventilator **Test 5A** » | l. 13 — bloc recopié du rapport du test 5 (les coefficients, eux, diffèrent : valeurs propres au test 6) |
| Les rapports IDA-ICE des tests **5 et 6** annoncent « CO2-Regelung in der Zone: Level of CO2 min. **600** ppm, max. **1000** ppm » | `_test5_3.txt` l. 45-46 et `_test6_3.txt` l. 29-30, **mot pour mot identiques** à `_test4_4.txt` l. 29-30. Or la spec du test **5** exige **950 – 1200 ppm** (`spec_test5_cellules.txt` p. 2 l. 2) et le test **6 n'a aucune régulation CO2** (installation à 3 étages sur horaire). → **bloc recopié du rapport du test 4** ; ne pas en tirer de valeur |
| `anwender_test5_4.txt` (Tas) parle d'un seuil « < **900** ppm » là où la spec dit 950 ppm | l. 26-27 — écart non expliqué |
| Specs des tests **4, 6 et 7** : **aucun** bloc « Zu liefernde Resultate » / « Testkriterien » | cf. E9 |
| Spec du test 6 : cellule « Kühldecken / Vorlauftemperatur » **vide** | `spec_test6_cellules.txt` p. 2 l. 22 |
| Specs des tests 4 et 5 : cellule de consigne de température **vide** | cf. E10, §8.3 |
| Test 7 : IDA-ICE a **modifié** le fichier de charges imposé (colonne BWW densifiée) alors que la spec exige des profils « **einheitliche** » | `_test7_3.txt` l. 11-16 vs `spec_test7_cellules.txt` p. 1 l. 12 et l. 23 |

**Règle de travail qui en découle** : un Anwenderbericht n'est **jamais** utilisé seul. Toute
valeur qui n'apparaît que dans un rapport, et qui contredit une spécification, est traitée comme
un **défaut du rapport**, pas comme une donnée.
