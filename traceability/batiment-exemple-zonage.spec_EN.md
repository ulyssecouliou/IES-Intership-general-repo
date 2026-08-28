> **Note:** Translated from French original. See [batiment-exemple-zonage.spec.md] for the source document.

# SIA 4010 Example Building -- rooms, thermal zoning and boundary conditions (tests 4 to 7)

> Status: **ARBITRATION RENDERED** -- room perimeter: high confidence (tests 4, 5, 6),
> medium-high (test 7). Zoning: determined for tests 4, 5, 6.
> **Revision 2 (2026-07-31, 2nd pass)**: the 12 Anwenderberichte of tests 5/6/7 and the
> **coordinate-based** extractions have been processed. Three open items from rev. 1 are
> addressed: S8.1 (floor over basement) -> **resolved by reasoned default**, S8.2 (GW/ZW) -> **resolved
> by reasoned default**, S8.3 (setpoints tests 4/5) -> **normative chain established, values
> reconstructed for test 5, still open for test 4**. Test 6 setpoints are
> now **read** (S8.4). Two items remain undecidable (S8.6, S8.7).
> Author: `norm-analyst`.
> Scope: example building only (SIA 4010 S4.3). Tests 1 to 3 do not use this
> building (test cell EN ISO 52016-1 / ASHRAE 140).
> Applicable validation classes: **3, 4A, 4B** (tab. 63, cf. `critere-test4.spec.md` S3.2).

## 0. Citation and status convention

**[V]** verified by direct reading of a source from this session ·
**[C]** verified by arithmetic cross-check of two **[V]** sources ·
**[I]** inference, justified on the spot · **[U]** **usage** established by an Anwenderbericht -- editor
report, **not a prescription** · **[?]** not determinable with available sources.

Sources read (session extraction directory `...\scratchpad\norme\`):

| File | Role | Extraction reliability |
|---|---|---|
| `spec_test4_cellules.txt` (3 pp.), `spec_test5_cellules.txt` (5 pp.), `spec_test6_cellules.txt` (5 pp.), `spec_test7_cellules.txt` (4 pp.) | specifications, **coordinate-based extraction** (`scripts/pdf_table_cells.py`) | **high**: single-line columns separated by ` \| ` in actual order -> **source to use preferentially** |
| `doc_beispielgebaeude_cellules.txt` (10 pp.) | example building documentation, by coordinates | **high**: tab. 1 (compositions) and tab. 3 (glazing) now correctly paired |
| `spec_test4.txt`, `spec_test5.txt`, `spec_test6.txt`, `spec_test7.txt`, `*_raw/_brut.txt` | older `-layout` / raw extractions | **degraded** (shifted columns) -- kept only as **cross-check** |
| `anwender_test4_1..4`, `anwender_test5_1..4`, `anwender_test6_1..4`, `anwender_test7_1..4` | 16 editor reports | high (running text), but **defective sources**: cf. S12.4 |
| `sia_4010_2023.txt` (3109 l.), `sia_380_2_2022.txt` (3603 l.) | standards | **running text reliable; tables and figures scrambled** -- tab. 3 of SIA 380/2 read by arithmetic cross-check only (S8.2) |
| `INVENTAIRE_batiment_exemple.txt`, `PREUVE_classeurs.txt`, `PREUVE_classeur_test4.txt` | IFC and evaluation workbooks | high |

Corresponding primary sources: `SIA_4010_geteilter_Link/Beispielgebäude/`,
`SIA_4010_geteilter_Link/Test<N>/Spezifikation_Test<N>.pdf`,
`SIA_4010_geteilter_Link/Test<N>/Anwenderberichte/`, `refs/SIA-4010-2023.pdf`,
`refs/SIA-380-2-2022.pdf`.

**Not present in `/refs`**: SIA 2024:2021 (nor prSIA 2024) -- **purchase order in S11** --,
SIA 2028, SIA 180:2014, SN EN 16798-5-1, SN EN 16798-7, SN EN ISO 52016-1, SN EN ISO 52120-1,
SN EN 15316-2, SIA 387/4:2023. No value is attributed to them here.

---

## 1. Short answer -- test -> rooms -> zones table

*(unchanged by the 2nd pass; no new source contradicts it -- on the contrary, `anwender_test5_1.txt`
l. 18-20 and `anwender_test6_1.txt` l. 18 confirm 8 and 2 zones, cf. S12.1)*

| Test | Rooms (no. / designation) | IFC Id | IFC Storey | IFC gross area m2 | Thermal zones | Confidence |
|---|---|---|---|---|---|---|
| **4** | `101` Hörsaal | `#2343` | Storey 3.4 (spans 3.4 **and** 6.8) | 165.81 | **1** | ~95 % |
| **5** | `100` Sitzungszimmer | `#2266` | Storey 3.4 | 31.62 | **8** (1 room = 1 zone) | ~95 % |
| | `102` Grossraumbüro | `#2245` | Storey 3.4 | 104.94 | | |
| | `200` Sitzungszimmer | `#3658` | Storey 6.8 | 31.62 | | |
| | `201` Büro | `#3500` | Storey 6.8 | 17.14 | | |
| | `202` Büro | `#3522` | Storey 6.8 | 17.14 | | |
| | `203` Büro | `#3544` | Storey 6.8 | 17.14 | | |
| | `204` Büro | `#3566` | Storey 6.8 | 17.14 | | |
| | `205` Büro (Gruppen-/Eckbüro) | `#3586` | Storey 6.8 | 33.13 | | |
| **6** | `001` Restaurant | `#835` | Storey 0.0 | 237.36 | **2**, coupled by 350 m3/h | ~95 % |
| | `002` Küche | `#855` | Storey 0.0 | 35.88 | | |
| **7** | the **10 rooms from tests 5 and 6**; the test 4 room **enters only through its coils** | -- | -- | 269.87 + 273.24 | **0 zones to simulate**: loads provided by `Lastverläufe_220607.xlsx` | ~90 % |

Totals: test 5 = 269.87 m2; test 6 = 273.24 m2; tests 4+5+6 = 708.92 m2 out of
1405.32 m2 of the building, i.e. **11 rooms used out of 29**; 18 rooms outside scope.

No room cited by a specification is missing from the IFC: **zero blocking discrepancy** (S6).

---

## 2. Normative basis for the perimeter

**[V]** SIA 4010:2023 S4.3 (`sia_4010_2023.txt` l. 2680-2693): "For tests **4 to 7**, an
example building has been defined ... The example building documentation can be downloaded
as a separate document ... Digital data are available ...: floor plans, sections and
views in DXF format; 3D models in IFC format; **load execution for test 7**."

**[V]** Table 62 "Validation tests", **Zone** column (l. 2649-2674):

| Test | Tab. 62 "Zone" column |
|---|---|
| 1-3 | "test cell per SN EN ISO 52016-1:2017, clause 7.2.2 (= ASHRAE 140:2017)" |
| 4 | "example building, **amphitheatre (windowless)**" |
| 5 | "example building, **offices and meeting rooms**" |
| 6 | "example building, **restaurant and kitchen**" |
| 7 | "**installations from tests 4 to 6 and zones from tests 5 and 6**" |

**[V]** Table 64, "Object -- spatial" column:
- test 4 (l. 2880-2892): "example building, amphitheatre (windowless), **without heat or cold
  emission other than ventilation**"; technical: "VAV system with
  **single zone** ... SYS_TYPE=**SINGLE_ZONE**".
- test 5 (l. 2915-2930): "example building, **1st + 2nd upper floor: 1 open-plan [office],
  2 meeting rooms, 4 individual offices, 1 corner / group office**"; technical:
  "VAV system with **multiple zones** ... SYS_TYPE=**MULTI_ZONE**".
  `[I]` "1 office [ground floor]" in the extraction is a translation typo for
  *Grossraumbüro*: the count 1+2+4+1 = **8** matches exactly the 8 rooms listed
  by the specification, and no test 5 room is on the ground floor (l. 11-13).
- test 6 (l. 2939-2942): "example building, **restaurant and kitchen**".
- test 7 (l. 2951-2992): "**all rooms from tests 5 and 6, as well as all ventilation
  systems** ... (office floors via Heizdecken/Kühldecken, restaurant
  via Kühldecken) ... heat diffusion and distribution (office floors via
  Heizdecken/Kühldecken, restaurant via **Konvektoren**) ... cold
  production, heat production, self-generation of electricity (PV)"; comment
  (l. 2951-2956): "May simultaneously represent the total energy demand of the
  building. **Pre-calculated profiles for space demands are provided.**"

---

## 3. Test by test

### 3.1 Test 4 -- one room, one zone

**[V]** `spec_test4_cellules.txt` p. 1 l. 8-10 (= `spec_test4.txt` l. 11-13), verbatim:

> « Testgebäude Raum "**Hörsaal**", **fensterlos**, **zweigeschossig, im 1. Und 2. OG**, **mit
> Dach gegen Aussenklima**, gemäss Dokumentation Beispielgebäude » -- « Nettofläche | **165.8 m2** »

- Assignment: `#2343`, no. `101`, `Hörsaal`, Storey 3.4, 165.81 m2, mean h **6.38 m**,
  1058 m3 (`INVENTAIRE` l. 29). Area discrepancy **+0.01 m2** (l. 47). **[V]**
- **The room is a single `IfcSpace`** spanning both levels (h 6.38 m ~ 3.0 + 3.4 m,
  inter-storey 3.4 m). It must **not** be split by floor. **[C]**
- **Its cover slab is indeed the roof**: 3.4 + 6.38 = 9.78 ~ **Storey 9.8**, the last
  IFC level, which carries no room (`INVENTAIRE` l. 4, 10-38). **[C]**
- A single zone, corroborated by « **Einzonen**-Klimaanlage mit variablem Volumenstrom »
  (`spec_test4_cellules.txt` p. 2 l. 5) and `SYS_TYPE=SINGLE_ZONE` (tab. 64 l. 2882-2884). **[V]**
- Sizing consistency: 55 persons at 3 m2/pers (p. 1 l. 26) -> 165 m2 ~ 165.81;
  Nennvolumenstrom 1700 m3/h (p. 2 l. 9) / 165.81 m2 = 10.25 m3/(h*m2) ~ 10 m3/(h*m2) stated
  (p. 1 l. 19-21). **[C]**
- **Constructions: this test alone departs from the documentation.** « Konstruktionen | Gemäss FprSIA
  380/2:2022, **Tabelle 3 "Grenzwert"** » (p. 1 l. 12) **[V]**. Cf. S8.2.
- **Usage: this test alone requests the *Zielwerte* from SIA 2024.** « Nutzung | Standardnutzung
  "Hörsaal" gemäss SIA 2024:2021; **Zielwerte** » (p. 1 l. 18) **[V]** -- tests 5 and 6
  request the **Standardwerte** (S11). The value level is therefore **chosen domain by
  domain**: one cannot transpose from one domain to another (S8.2).
- Temperature setpoint: **empty cell in the PDF** -- cf. S8.5.
- Windows: none (`fensterlos`) -> the documentation glazing (S7.2) is irrelevant here.
- Opaque external walls: the specification says nothing beyond "fensterlos" and
  "Dach gegen Aussenklima". To be read from the IFC/DXF geometry. **[?]** (S8.7)

### 3.2 Test 5 -- eight rooms, eight zones

**[V]** `spec_test5_cellules.txt` p. 1 l. 8-10, verbatim:

> « **1. OG: Räume 100 (Sitzungszimmer), 102 (Grossraumbüro); 2. OG: Räume 200
> (Sitzungszimmer), 201 bis 204 (Einzelbüros) und 205 (Gruppenbüro)**; gemäss Plänen
> Dokumentation » -- « Nettofläche | **Gemäss Dokumentation** » (p. 1 l. 11)

- **One room = one zone (8 zones)** -- status **[I] very strong**, five converging supports:
  1. « Ersatzluftanlage, **zonenweise** CO2-geregelt » (p. 1 l. 19) **[V]**;
  2. « Regelung | CO2-abhängig, **pro Zone** mit Volumenstromregler geregelt » (p. 2 l. 21) **[V]**;
  3. tab. 64 lists the 8 rooms **individually**, `SYS_TYPE=MULTI_ZONE` (l. 2915-2930) **[V]**;
  4. a diagnostic is requested **per room**: « CO2-Konzentration **GR-Büro** » (p. 5 l. 24-26) **[V]**;
  5. **[U]** the reference program "Excel" instantiated **6 zone workbooks** to cover
     the 8 rooms -- « Jeweils zur Berechnung der **6 verschiedenen Raumtypen (Einzelbüro,
     Einzelbüro mit schwerer Innenwand, Gruppenbüro, Grossraumbüro, Sitzungszimmer,
     Sitzungszimmer mit Dach)** » (`anwender_test5_1.txt` l. 18-20). Six **types**, not six zones:
     `201`-`204` are split into two types based on the internal wall.
  -> **No source authorises grouping 201-204 into one zone.** Do not do it.
- **Important new consequence** (support 5): the four individual offices **are not
  thermally identical** -- two of them have a *schwere Innenwand* (iw2 load-bearing,
  concrete 0.2 m), the other two a lightweight partition (iw1). The inertia of **adiabatic
  internal walls** is therefore a test parameter: it discriminates between two office types
  despite having the same area (17.14 m2). This **confirms S4.2**: "adiabat" = zero flux,
  **mass retained**. Status: **[U] strong**, confidence ~95 %. Still to be established from the geometry:
  **which** rooms among `201`-`204` carry the heavy wall. **[?]** (S8.7)
- « Sitzungszimmer **mit Dach** » (same citation) confirms that 2. OG rooms have the
  flat roof in contact with the exterior, and that `100` (1. OG) does not. **[U]** -- consistent
  with the IFC (Storey 9.8 = roof level, S6 E8).
- Room `101` Hörsaal (test 4) is **adjacent** to test 5 rooms on both levels. **[C]**
  (219.68 + 165.81 = 385.49 ~ 385.32 m2 of the ground floor).
- Rooms that are non-zones but **essential as technical support**:
  - `U102` Technik: « Geräteaufstellung | **UG, Raum U102, unkonditioniert** » (p. 2 l. 7) **[V]**;
  - `022` Steigzone: « Verteilsystem | **Steigzone entlang Liftschacht (Raum 022)** ... Kanäle
    0.3 x 0.3 m, totale Länge ZUL 14 m, Kanäle 0.3 x 0.15 m, Länge 5 m; **U-Wert 0.6 W/m2 K** »
    (p. 2 l. 8-10) **[V]** -- the U of 0.6 W/(m2K) for the riser ducts is **new** (the earlier
    extraction only yielded 1.1);
  - Corridors `110`/`210`: « **Deckenbereich Korridor 1. + 2. OG** : Kanäle 0.3 x 0.15 m,
    Länge ZUL 20 m; **U-Wert 1.1 W/m2 K** » (p. 2 l. 11-12) **[V]**;
  - Ducts **within** zones: « Deckenbereich Zonen 1. + 2. OG: Rohre dia. 0.125 m, Länge 24 m,
    Rohre dia. 0.1 m, Länge 40 m; U-Wert 1.1 W/m2 K » (p. 2 l. 13-14) **[V]**.
- Reference temperatures for technical rooms: « **Temperatur-Randbedingungen
  Zentrale/Steigzone : 15°C (Okt. -- März), 28°C (April -- Sept.)** » (p. 2 l. 15-16) **[V]**.
- Emission: « Heiz-/Kühldecken -- **Für Test 5 nur als Randbedingung relevant, Vorbestimmung
  für Test 7** »; « Betriebszeit | Wie Betriebszeit Lüftung » (p. 1 l. 25-28) **[V]**.
- Setpoints: « Sollwerte | Temperatur » **without value** (p. 2 l. 1); CO2 **950 -- 1200 ppm**,
  outdoor air 400 ppm (p. 2 l. 2); **Rel. Feuchte min. 30 %** (Sollwert Befeuchtung, p. 2 l. 3).
  **[V]** -- the 950/1200 ppm **correct** rev. 1, which could not read this line.
- **Four variants 5A-5D** reconstructed in S12.2.

### 3.3 Test 6 -- two rooms, two coupled zones

**[V]** `spec_test6_cellules.txt` p. 1 l. 8-12 (Restaurant) and p. 2 l. 48-52 (Küche):

> « **Restaurant** -- Selbstbedienungsrestaurant im EG: **Raum 001 (Restaurant)** gemäss Plänen
> Dokumentation -- Nettofläche | Gemäss Dokumentation (**237.4 m2**) »
> « **Küche** -- Küche zu Selbstbedienungsrestaurant im EG: **Raum 002 (Küche)** gemäss Plänen
> Dokumentation -- Nettofläche | Gemäss Dokumentation (**35.9 m2**) »

- Assignment: `#835`/`001`/237.36 m2 (discrepancy -0.04) and `#855`/`002`/35.88 m2 (discrepancy -0.02). **[V]**
- **Two distinct zones, aeraulically coupled**: « Überströmung von 10% des Küchen-
  Abluftvolumenstroms (**350 m3/h**) in die Küche durch **Überdruck** » (p. 1 l. 26-27); kitchen
  side « Überströmung von ca. 10% des Abluftvolumenstroms (350 m3/h) aus dem Restaurant
  mittels **Unterdruck** » (p. 3 l. 5-6). **[V]**
- Air balance **exactly closed on these two rooms only**: ZUL 3000 + 3150 =
  **6150** = « Nennvolumenstrom | Stufe 3 | 6'150 m3/h | 100% » (p. 3 l. 38); ABL 2650 + 3500 =
  **6150**; 3000 - 2650 = 350 = 3500 - 3150. **[C]**
  -> Corroborated **[U]**: « Die Ablufttemperatur wurde Abluft-Volumenstromgewichtet aus **den
  beiden Raumtemperaturen** errechnet » (`anwender_test6_1.txt` l. 23-25) -- *the two*, so
  no other room feeds the return air.
- Emission: Restaurant -> **Konvektoren** « In Betrieb während Betriebszeit der Lüftung »
  (p. 1 l. 30-31), sliding supply temperature **(−8 ; 40) -> (20 ; 20) °C** (p. 2 l. 1-16) **[V]**
  \+ **Kühldecken** « Für Test 6 nur als Randbedingung relevant, Vorbestimmung für Test 7 »
  (p. 2 l. 17-21), **whose "Vorlauftemperatur" cell is empty** (p. 2 l. 22) **[V]**.
  Küche -> Wärmeabgabe « **keine** », Kälteabgabe « **keine** » (p. 3 l. 9-12). **[V]**
- **Restaurant setpoints: now fully read -- cf. S8.4.**
- Kitchen: « Tempera-tur Küche | **Sollwert heizen: 21°C** » (p. 3 l. 25-27) **[V]** -- the
  apparent contradiction from rev. 1 is **resolved** in S8.4.
- Technical support rooms: « Geräteaufstellung | **Keller, unkonditioniert** » (p. 3 l. 31) and
  « Verteilsystem | Zentrale und Steigzone zwischen Küche und Restaurant ... Kanäle 0.4 x 0.7 m,
  Länge ZUL total 8 m; Deckenbereich Küche: ZUL-Kanal 0.3 x 0.6 m, Länge total 6 m;
  Deckenbereich Restaurant: ZUL-Kanal 0.3 x 0.6 m, Länge total 16 m, Rohre dia. 0.18 m, Länge
  total 45 m » (p. 3 l. 32-36) **[V]**. **No U-Wert and no ambient temperature** are
  given for these ducts, unlike test 5 -- cf. S8.6.
- **Abbreviated adiabaticity rule for the kitchen**: « Randbedingungen | Bauteile gegen
  Nachbarzonen, die nicht Gegenstand des Tests sind: **adiabat** » (p. 2 l. 54) -- without the
  dash "zones from other tests". **[V]** Cf. S4.3.

### 3.4 Test 7 -- no zone to simulate, distribution groups

`spec_test7_cellules.txt` names **no room** (4 pages, verified): « Gebäude | Testgebäude
gemäss Dokumentation » (p. 1 l. 7). The spatial perimeter therefore comes **solely** from SIA 4010
tab. 62 and tab. 64 (S2). What the specification enumerates are **9 distribution groups**:

| Type | Group | Ref. | Served room(s) |
|---|---|---|---|
| Cold | Test 4 Luftkühler | p. 1 l. 8 | `101` (via the test 4 AHU) |
| Cold | Test 5 Luftkühler | p. 1 l. 9 | 8 rooms of test 5 |
| Cold | Test 6 Luftkühler | p. 1 l. 10 | `001` + `002` |
| Cold | **Test 5 + 6 Kühldecken** | p. 1 l. 11 | 8 rooms of test 5 **and** `001` |
| Hot | Test 4 Lufterwärmer | p. 1 l. 18 | `101` |
| Hot | Test 5 Lufterwärmer | p. 1 l. 19 | 8 rooms of test 5 |
| Hot | Test 6 Lufterwärmer | p. 1 l. 20 | `001` + `002` |
| Hot | **Test 5 Heizdecken** | p. 1 l. 21 | 8 rooms of test 5 |
| Hot | **Test 6 Konvektoren** | p. 1 l. 22 | `001` |

- Kitchen `002` belongs to **no** emission group; it is served only by
  air. **[C]**
- **The loads are not to be re-simulated**: « Verbrauchsprofile | **Es sind einheitliche Profile
  gemäss `Lastverläufe_220607.xlsx` zu verwenden** » (p. 1 l. 12 cold, l. 23 hot);
  « Warmwasserladung | Ladeprofil (Wärme am Eingang des Warmwasserspeichers), gemäss
  `Lastverläufe_220607.xlsx` -- Temperatur: 60°C » (p. 1 l. 13-17). **[V]**
  -> **Confirmed [U] by all 4 reports**: « Wärmebedarfsprofile gemäss gegebener Datei wie in
  der Spezifikation angegeben » (`anwender_test7_1.txt` l. 38, `_2.txt` l. 19, `_3.txt` l. 11) and
  « Ein selbst erstelltes Spreadsheet, das die **elektrischen Verbrauchsprofile aus den Tests 4,
  5 und 6 aggregiert** » (`_1.txt` l. 19-21). **No reference program re-simulated any
  zone in test 7.** Confidence ~90 % -> the former S8.8 is lifted (column mapping remains, S8.7).
- Warning **[U] caveat**: IDA-ICE **modified** the load file -- « wurde die Spalte BWW im
  Excel Lastverläufe **erweitert** » to avoid linear interpolation between hourly points
  (`anwender_test7_3.txt` l. 11-16). This is a departure from the word *einheitliche*; to be known before
  comparing a fine-timestep run.
- Room `101` from test 4 enters test 7 **through its two coils only**: tab. 62 says
  « **installations** des tests 4 à 6 et **zones** des tests 5 et 6 » (l. 2665-2667). **[V + I]**

---

## 4. Adiabaticity rule and boundary conditions

### 4.1 The text, verbatim **[V]**

`spec_test4_cellules.txt` p. 1 l. 13-17 (identically `spec_test5_cellules.txt` p. 1 l. 13-17 and
`spec_test6_cellules.txt` p. 1 l. 14-18 for the Restaurant):

> « **Bauteile gegen Nachbarzonen, die nicht Gegenstand des Tests sind:**
> -- **Gegen Nachbarzonen von anderen Tests, falls sie mitgerechnet werden: Sollwerte gemäss
>   jeweiliger Testspezifikation**
> -- **Ansonsten sowie alle übrigen Innenbauteile adiabat** »

Working translation (mine, to be checked by a German speaker): *"Building elements against
neighbouring zones that are not the subject of the test: -- against neighbouring zones
pertaining to other tests, if these are calculated jointly: setpoint values according to the
corresponding test specification; -- otherwise, as well as all other interior elements:
adiabatic."*

**Structural point, decisive for S8.1**: the rule is an **exhaustive two-branch partition**
(`falls sie mitgerechnet werden` / `Ansonsten sowie alle übrigen Innenbauteile`). There
is **no third branch** for an unconditioned building room. **[V]**

### 4.2 Exact scope, decomposed

| Situation of an interior element | Treatment | Status |
|---|---|---|
| Between two rooms **both subject to the same test** (`001`<->`002`; `201`<->`202`) | **Not concerned**: normal thermal coupling between simulated zones | **[I]** -- the rule targets only neighbours "die **nicht** Gegenstand des Tests sind" |
| Against a room **subject to another test**, that other test being calculated jointly (`101`<->`102`, `101`<->`200`) | Boundary at **imposed temperature** = setpoint from the other test's specification | **[V]** |
| Against a room **subject to another test not being calculated** | **adiabatic** ("Ansonsten") | **[V]** |
| Against any other room (corridors, WC, shafts, staircase, basement, kitchen annexes, entire UG) | **adiabatic** | **[V]** |
| Interior element **within the same zone** (internal partition, Hörsaal intermediate slab) | « alle übrigen Innenbauteile adiabat » | **[V]** |

**Interpretation, marked as such**: "adiabat" means **zero flux at the boundary, thermal mass
retained** -- the element remains modelled with its layers, only its opposite face is
insulated. Three supports:
(a) standard meaning in dynamic simulation;
(b) **[U]** the "Excel" program had to **add** internal wall consideration to its
workbook, for tests 4, 5 **and** 6 (« ergänzt durch G. Zweifel zur Berücksichtigung von ...
**internen Wänden** » -- `anwender_test4_1.txt` l. 17, `anwender_test5_1.txt` l. 16,
`anwender_test6_1.txt` l. 16) -- pointless if internal walls were simply removed;
(c) **[U] new and stronger**: the same program distinguishes "Einzelbüro" and "Einzelbüro
**mit schwerer Innenwand**" as two zone types to calculate separately
(`anwender_test5_1.txt` l. 18-19). The nature of the adiabatic internal wall **therefore
changes the result**: its mass is indeed taken into account.
Status **[I]** supported by **[U]**, confidence ~95 % (rev. 1: 90 %). **Design decision:
retain the mass.**

### 4.3 Test 6 nuance for the kitchen **[V]**

The kitchen receives the **short** version of the rule (`spec_test6_cellules.txt` p. 2 l. 54), without
the dash "zones from other tests". Since the kitchen's only "subject of the test" neighbour is the
Restaurant (coupled), the wording difference is **without practical effect**. `[I]`

### 4.4 Boundary conditions by test -- operational summary

| Test | Exterior | Ground / UG | Neighbours from other tests | Other rooms |
|---|---|---|---|---|
| 4 | roof 165.81 m2 (Storey 9.8) **[C]**; possible opaque walls **[?]**; **no window** **[V]** | no ground contact (1./2. OG) | `102`, `100`, `110` (1. OG) and `200`-`205`, `210` (2. OG): test 5 setpoints **if** calculated, otherwise adiabatic | adiabatic |
| 5 | facades + windows + fabric blinds (S7.2); **roof for 2. OG rooms** **[U]** | floor over 1. OG (no ground) | `101`: test 4 setpoint **if** calculated, otherwise adiabatic | corridors, WC, shafts, staircase: adiabatic |
| 6 | ground floor facades + windows | **floor over basement: adiabatic** -- S8.1, resolved by reasoned default | `101` (if adjacent): test 4 setpoint if calculated | `003`, `004`, `010`, `011`, `012`: adiabatic |
| 7 | not applicable (loads provided) | not applicable | not applicable | not applicable |

**Unused rooms and levels (18 rooms)**: `U101`, `U102`, `U110`, `020`, `021`, `022`,
`023`, `003`, `004`, `010`, `011`, `012`, `110`, `112`, `113`, `210`, `211`, `212`.
Normative treatment: **outside the simulation perimeter; adiabatic boundary**. Two of them
retain a **non-thermal** role: `U102` (AHU plant room, test 5) and `022`
(duct routing, test 5), with imposed temperature 15/28 °C (S3.2). **[V]**

---

## 5. Complete IFC <-> specifications mapping

29 IFC rooms, status per test. SIA usage from `doc_beispielgebaeude_cellules.txt`
p. 10 l. 5-33 (table now read **without offset**).

| IFC Id | No. | Designation | Storey | m2 | SIA usage (doc) | Status |
|---|---|---|---|---|---|---|
| `#51` | U101 | Lager | -3.5 | 237.36 | 12.4 Nebenraum | outside scope (adiabatic) |
| `#75` | U110 | Verkehrsfläche | -3.5 | 32.44 | 12.1 Verkehrsfläche | outside scope |
| `#101` | U102 | Technik | -3.5 | 118.91 | 12.4 Nebenraum | **support**: test 5 AHU, unconditioned |
| `#122` | 021 | Treppenhaus | -3.5 | 17.85 | 12.3 Treppenhaus | outside scope (h ~ 13.3 m) |
| `#144` | 020 | Lift | -3.5 | 2.40 | 12.3 Treppenhaus | outside scope (h ~ 13.3 m) |
| `#166` | 022 | Steigzone | -3.5 | 0.78 | -- | **support**: test 5 ducts (h ~ 12.8 m), 15/28 °C |
| `#188` | 023 | Steigzone | -3.5 | 1.84 | -- | outside scope (h ~ 6.5 m) |
| `#835` | 001 | Restaurant | 0.0 | 237.36 | 6.1 Restaurant | **test 6 zone** (spec: 6.2 SB-Restaurant, S6 E2) |
| `#855` | 002 | Küche | 0.0 | 35.88 | 6.3 Küche zu Restaurant | **test 6 zone** (spec: 6.4, S6 E2) |
| `#877` | 003 | Lager Küche | 0.0 | 11.39 | 12.4 Nebenraum | outside scope |
| `#898` | 004 | Kühlraum | 0.0 | 10.24 | 12.11 Kühlraum | outside scope |
| `#920` | 011 | WC Damen | 0.0 | 14.62 | 12.7 WC | outside scope |
| `#941` | 012 | WC Herren | 0.0 | 14.61 | 12.7 WC | outside scope |
| `#964` | 010 | Verkehrsfläche | 0.0 | 61.22 | 12.1 Verkehrsfläche | outside scope |
| `#2245` | 102 | Grossraumbüro | 3.4 | 104.94 | 3.2 Grossraumbüro | **test 5 zone** |
| `#2266` | 100 | Sitzungszimmer | 3.4 | 31.62 | 3.3 Sitzungszimmer | **test 5 zone** (without roof) |
| `#2284` | 112 | WC Damen | 3.4 | 14.62 | 12.7 WC | outside scope |
| `#2302` | 113 | WC Herren | 3.4 | 14.61 | 12.7 WC | outside scope |
| `#2323` | 110 | Verkehrsfläche | 3.4 | 57.14 | 12.1 Verkehrsfläche | outside scope; **test 5 ducts** |
| `#2343` | 101 | Hörsaal | 3.4 | 165.81 | 4.4 Hörsaal | **test 4 zone** (spans 3.4 + 6.8) |
| `#3500` | 201 | Büro | 6.8 | 17.14 | 3.1 Einzel-, Gruppenbüro | **test 5 zone** |
| `#3522` | 202 | Büro | 6.8 | 17.14 | 3.1 | **test 5 zone** |
| `#3544` | 203 | Büro | 6.8 | 17.14 | 3.1 | **test 5 zone** |
| `#3566` | 204 | Büro | 6.8 | 17.14 | 3.1 | **test 5 zone** |
| `#3586` | 205 | Büro | 6.8 | 33.13 | 3.1 | **test 5 zone** (« Gruppenbüro ») |
| `#3604` | 211 | WC Damen | 6.8 | 14.62 | 12.7 WC | outside scope |
| `#3622` | 212 | WC Herren | 6.8 | 14.61 | 12.7 WC | outside scope |
| `#3640` | 210 | Verkehrsfläche | 6.8 | 57.14 | 12.1 Verkehrsfläche | outside scope; **test 5 ducts** |
| `#3658` | 200 | Sitzungszimmer | 6.8 | 31.62 | 3.3 Sitzungszimmer | **test 5 zone** (**with roof**, `anwender_test5_1.txt` l. 20) |

**Area convention -- resolved [C]**: the "Nettofläche" values from the specifications are the
IFC `GrossFloorArea` (absolute value). Three independent matches:
165.8 <-> 165.81 * 237.4 <-> 237.36 * 35.9 <-> 35.88. The documentation contains **no area
table** (chapter 1 = figures only, `doc_beispielgebaeude_cellules.txt` p. 3-5): the IFC
is the sole numerical source of areas. `NetFloorArea` **does not exist** in this file.

---

## 6. Discrepancies between specifications <-> IFC / documentation

| # | Discrepancy | Severity | Detail |
|---|---|---|---|
| E1 | **No missing room** | -- | All 11 cited rooms (including `U102` and `022`) exist. |
| E2 | Restaurant usage: **`6.1 Restaurant`** (doc p. 10 l. 5) vs **`6.2 "Selbstbedienungerestaurant"`** (spec test 6 p. 1 l. 19) | **medium** | The specification prevails. Same for kitchen: doc `6.3` (p. 10 l. 6) vs spec `6.4` (p. 2 l. 55). **Two different SIA 2024 usages -> different usage data.** To be frozen **from the specs**. Cf. S11. |
| E3 | The spec distinguishes "Einzelbüros" / "Gruppenbüro" (test 5 p. 1 l. 9), the doc gives them **a single** usage `3.1` (p. 10 l. 23-27) | low | A single SIA 2024 data set for all five. |
| E4 | Doc: title page "**Version 4**, 15. Januar 2021" (p. 1 l. 2-3) while the file is named `Dokumentation_Beispielgebäude_V5.pdf` | low but to be noted | **Unresolved.** |
| E5 | Doc: "**prSIA** 2024:2021" (p. 10 l. 2); specs 4 and 5: "SIA 2024:2021"; spec 6: both -- "SIA 2024:2021" (p. 1 l. 19, p. 2 l. 55) **and** "prSIA 2024:2021" (p. 2 l. 28, p. 3 l. 18) | low | Draft vs published standard, **internal inconsistency within test 6**. A single edition must be used. Cf. S11. |
| E6 | Spec test 4: "**FprSIA** 380/2:2022" (p. 1 l. 12); `/refs` contains **SIA 380/2:2022** published | low | Tab. 3 from `/refs` reproduces exactly the resistances from the doc (S8.2): **strong presumption of identity**, but the label remains divergent. |
| E7 | Doc: 8 compositions; SIA 380/2 tab. 3: **9** -- the doc **omits "Wall against unconditioned room"** (U 0.28; `sia_380_2_2022.txt` l. 1986-1992) | low | The doc however retains **« Zwischendecke gegen unkonditioniert (Keller) »**. Analysis of this asymmetry: S8.1. |
| E8 | Storey 9.8 carries **no room** | -- | **Roof** level (6.8 + 3.0 = 9.8). Do not create a zone. **[C]** |
| **E9** | **The specs for tests 4, 6 and 7 contain NO "Zu liefernde Resultate" / "Testkriterien" block** | **high** | Verified by exhaustive search across both extractions: present in `spec_test1.txt` l. 69-73, `spec_test2.txt` l. 70, `spec_test3.txt` l. 149, `spec_test5_cellules.txt` p. 4 l. 46 + p. 5 l. 4-9; **absent** from tests 4, 6, 7. The quantities and criteria for these three tests must therefore be taken from SIA 4010 tab. 64/65 and from the `Resultaterfassung_Test<N>.xlsx`. **Confirms and generalises** the defect already identified for test 4. |
| **E10** | **Empty value cells in the PDFs** | **high** | Test 4: « Sollwerte / Raumlufttemperatur » (p. 2 l. 1-3); test 5: « Sollwerte / Temperatur » (p. 2 l. 1); test 6: « Kälteabgabe / Kühldecken / Vorlauftemperatur » (p. 2 l. 22). All three confirmed by three extraction methods. Cf. S8.5. |

---

## 7. What the example building documentation adds

It **contains neither zoning nor adiabaticity rule**: its table of contents has only three chapters --
Geometrie, Gebäudehülle, Nutzung (p. 2 l. 2-13). **Do not look for zoning in the
documentation.**

### 7.1 Geometry (ch. 1, p. 3-5) -- figures only
Grundrisse 1.UG/EG/1.OG/2.OG, Längsschnitt, Querschnitte, facades E/W/S/N. **No exploitable
dimension or area in text.** -> geometry to be taken from the IFC / DXF-DWG.

### 7.2 Envelope (ch. 2, p. 6-9) -- the real contribution, **now read without offset**

- **Tabelle 1** (p. 6 l. 6-50): **8 compositions**, layer by layer. Columns, in the actual
  order confirmed by the header (p. 6 l. 6-8): `Nr. | Material/Baustoff | Dicke [m] | Lambda GW
  [W/(mK)] | Lambda ZW [W/(mK)] | Dichte [kg/m3] | sp. W.kap. [kJ/(kgK)]`. **[V]**
  Warning: **The rev. 1 caveat ("do not freeze lambdas from this text") is LIFTED**: the
  pairing is verified by two independent checks -- (a) lambda_GW > lambda_ZW for the **five**
  insulation layers and lambda_GW = lambda_ZW for all others; (b) the complete arithmetic
  cross-check with SIA 380/2 tab. 3 (S8.2). The lambdas can be frozen **from this file**.
- Compositions: `aw1` Aussenwände (p. 6 l. 9-13), `aw2` Aussenwände gegen Erdreich (l. 14-16),
  `iw1` Innenwände nicht tragend (l. 17-20), `iw2` Innenwände tragend (l. 21-24), Boden über
  Erdreich (l. 25-29), Zwischendecke (l. 30-36), **Zwischendecke gegen unkonditioniert
  (Keller)** (l. 37-44), Flachdach (l. 45-49). Layer order "**von innen nach aussen bzw.
  oben nach unten**" (l. 50). **[V]**
- Explicit principle (p. 6 l. 3-5): « Die Bauteile werden für die Berechnung eines
  **Grenzwertes (GW)** und eines **Zielwertes (ZW)** bestimmt. Es werden die
  **Dämmeigenschaften bei gleicher Stärke variiert**, damit die Geometrie des Gebäudes
  gleichbleibt. » -> **only the lambdas change, never the thicknesses**: a single IESVE geometry,
  two material sets. **[V]**
- **New and operationally relevant finding**: `iw1`, `iw2` and `Zwischendecke` have **identical**
  lambdas in GW and ZW (p. 6 l. 17-24 and 30-36). **The GW/ZW choice therefore affects no interior
  element** -- it applies only to `aw1`, `aw2`, `Boden über Erdreich`, `Zwischendecke gegen
  unkonditioniert` and `Flachdach`. **[V]**
- **Glazing** (p. 7 l. 5-12): Planitherm XN Saint-Gobain, **triple** -- 1. SGG PLANITHERM XN
  4 mm / 2. Air 10 % + Argon 90 % EN 673 14 mm / 3. SGG PLANICLEAR 4 mm / 4. Air-Argon 14 mm /
  5. SGG PLANITHERM XN 4 mm (gespiegelt). **[V]**
- **Glazing properties -- symbol-to-value pairing now VERIFIED** (p. 8 l. 6-23, p. 9
  l. 7-11), columns `Without shading | With shading`: **[V]**
  - EN ISO 52022-3 (summer): gtot 0.545 / 0.059; gc 0.022 / 0.006; gth 0.044 / 0.013;
    gv 0.000 / 0.000; qi 0.066 / 0.019
  - EN ISO 52022-3 (reference): gtot 0.542 / 0.056; **Ug 0.646 / 0.574 W/(m2K)**
  - EN 410: tau_e 0.479 / 0.040; rho_e 0.323 / 0.490; rho'_e 0.323 / 0.456; tau_v 0.742 / 0.058;
    rho_v 0.145 / 0.496; rho'_v 0.145 / 0.395; tau_uv 0.234 / 0.012
  - ISO 15099 (summer) gtot 0.545 / 0.059; ISO 15099 (winter) **Ug 0.654 / 0.582**
  Warning: **The rev. 1 caveat about label inversion is LIFTED.**
- **Solar shading** (p. 7 l. 18 and p. 8 l. 1-5): external fabric blind Soltis
  92-2048-Alu SergeFerrari; **1 cm air gap** at top, sides and bottom;
  « Der Sonnenschutz wird bei einer Solarstrahlung von **150 W/m2 auf der Aussenseite**
  (gemäss der Sonnenschutzregelung) geschlossen. » **[V]**
- **Frame** (p. 9 l. 14): « **Rahmenanteil 15 %**, U-Wert = **1.3 W/(m2K)**, abs = **0.6** ». **[V]**
- **Thermal bridges** (p. 9 l. 16): « Es werden **keine Wärmebrücken** berücksichtigt. » **[V]**
- **[C] The glazing has NO GW/ZW variant**: a single property set is given, and
  Uw ~ 0.85 x 0.646 + 0.15 x 1.3 = **0.74 W/(m2K)**, below **both** reference project values
  from SIA 380/2 tab. 2 ("Window U-value (glass and frame) Uw: limit value
  **1.1**, target value **0.88**" -- `sia_380_2_2022.txt` l. 1713). The example building **is
  therefore not a reference project** in the sense of SIA 380/2 ch. 7; its envelope is a fixed
  input. Practical consequence: the GW/ZW question concerns **only** opaque insulation.

### 7.3 Usage (ch. 3, p. 10) -- the contribution for zones
- Table **Raumnummer -> Bezeichnung -> Nutzung (SIA)** for **all 29 rooms** (p. 10 l. 5-33);
  only `022` and `023` have no usage ("-"). **[V]**
- « Die Nutzungsdaten werden gemäss **prSIA 2024:2021** angenommen » (p. 10 l. 2). **[V]**
- « Die **Zeitpläne** für Personenbelegung, Geräte und Beleuchtung können ebenfalls dem
  Merkblatt entnommen werden. Die Beleuchtungsregelung erfolgt gemäss diesem Zeitplan
  (**keine Tageslichtabhängige Beleuchtungsregelung**). » (p. 10 l. 34-36) **[V]** -- **no**
  daylight-dependent lighting control in tests 4 to 7.

---

## 8. Open items -- status after the 2nd pass

### 8.1 Ground floor slab over basement (test 6) -- **RESOLVED: adiabatic**

**Answer to the question asked: the Anwenderberichte of test 6 say NOTHING about this floor.**
Exhaustive regex search across the 16 reports
(`keller|erdreich|unkonditioniert|adiabat|Grenzwert|Zielwert|Konstruktion|Bauteil|U-Wert|Aufbau|Boden|Decke`):
**three occurrences in total**, all off-topic -- `anwender_test1_1.txt` l. 15 and l. 20
(ASHRAE 140 constructions, test 1), `anwender_test2_1.txt` l. 23 (ground albedo),
`anwender_test5_4.txt` l. 32 ("Druckaufbau"). **Status: verified negative [V].** The test 4
to 7 reports document only HVAC (HRU, fans, coils, controls) --
**none** describes the envelope or boundary conditions.

Lacking documented usage, the arbitration is based on the standard and on the structure of sources.

**Decision: floor `001`/`002` over basement = ADIABATIC. [I], confidence ~80 %.** Three reasons,
in order of strength:

1. **The rule is an exhaustive two-branch partition** (S4.1, `spec_test6_cellules.txt`
   p. 1 l. 14-18). The basement is not "Gegenstand des Tests" and is the subject of **no** other
   test (no specification mentions it as a zone); the floor is an `Innenbauteil`.
   The branch "Ansonsten sowie alle übrigen Innenbauteile: adiabat" applies **literally
   and without remainder**. **[V]** on the text, **[I]** on the application.
2. **No basement temperature is given anywhere.** Yet the test 5 specification **does** give
   an ambient temperature where it is needed ("Temperatur-Randbedingungen
   Zentrale/Steigzone: 15°C (Okt. -- März), 28°C (April -- Sept.)", p. 2 l. 15-16) -- and this
   only for **duct losses**, not for a zone boundary. Test 6 mentions
   the basement **only** as AHU location ("Geräteaufstellung | Keller,
   unkonditioniert", p. 3 l. 31) and provides **neither U-Wert for ducts nor ambient temperature**
   (p. 3 l. 32-36). A heat flow towards the basement would therefore be **uncomputable** with the
   data provided: the specification would be incomplete. The adiabatic hypothesis is the only one
   that makes the specification **closed**. **[C]** -- the most decisive argument.
3. **The argument "this composition has no use elsewhere" does not hold.** Counter-proof: the
   documentation also contains `aw2` *Aussenwände gegen Erdreich* (p. 6 l. 14-16) and *Boden
   über Erdreich* (p. 6 l. 25-29), which serve only the **1. UG**, hence **outside the scope of
   all tests**. Tabelle 1 describes **the entire building**, not the test requirements. The
   presence of the "Zwischendecke gegen unkonditioniert (Keller)" composition therefore proves
   **nothing** about its thermal status in test 6. **[C]** -- this **corrects** the rev. 1
   reasoning, which overestimated this signal.

**Remaining counter-argument, to be recorded**: the building was indeed designed with this
**insulated** floor -- the "Zwischendecke gegen unkonditioniert (Keller)" composition (p. 6 l. 37-44)
is the ordinary "Zwischendecke" (p. 6 l. 30-36) **plus a 0.13 m EPS layer 6** under the
slab. This insulation only makes sense to separate conditioned from unconditioned. Rendering it
adiabatic amounts to ignoring a documented element of the thermal envelope. The U-value gap between
the two readings is total (0.245 W/(m2K) in GW, cf. S8.2, versus 0) over **237.36 m2** under the
Restaurant + 35.88 m2 under the kitchen.

**Recommended empirical resolution, unambiguous** -- this is engine work, not normative:
simulate test 6 under **both** hypotheses and compare the annual sums to the **Streubereich
of the 4 reference programs** frozen in `Resultaterfassung_Test6.xlsx` (band =
`Mittelwert +/- max |deviation|`, formulas proven in `PREUVE_classeurs.txt` l. 9-11, 28-39).
Over 273 m2 at delta_U ~ 0.25 W/(m2K), the heating demand gap should be well outside the band:
**the test is discriminating**. -> task `validation-engine-engineer`, to be done **before** freezing.
**Until then: do not declare test 6 "done".**

### 8.2 GW or ZW construction variant (tests 5 and 6) -- **RESOLVED: GW by reasoned default**

**Answer to the question asked: the Anwenderberichte say NOTHING about GW/ZW.** Same exhaustive
search as in S8.1: **no** occurrence of `Grenzwert`, `Zielwert`, `Konstruktion`,
`Aufbau`, `U-Wert`, `Bauteil` in the 12 reports of tests 5, 6 and 7. **Verified negative [V].**

However, **the coordinate-based extraction enables a new arithmetic demonstration**:
the **GW** column of the documentation is the **exact transposition, at building thickness**,
of the **"limit value" compositions from SIA 380/2:2022 tab. 3**. Proof: for the **five**
insulation layers, lambda_GW = lambda_real x (d_doc / d_VL,SIA), to the last displayed digit.

| Composition | Insulation layer | d_doc | lambda_ZW (doc) | lambda_GW (doc) | d_VL (tab. 3) | lambda_ZW x d_doc/d_VL | Verdict |
|---|---|---|---|---|---|---|---|
| `aw1` Aussenwände | EPS | 0.25 | 0.033 | **0.055** | 0.15 | 0.033 x 0.25/0.15 = **0.0550** | exact match |
| `aw2` geg. Erdreich | XPS | 0.16 | 0.033 | **0.053** | 0.10 | 0.033 x 1.60 = **0.0528** | 0.053 (rounded) |
| Boden über Erdreich | XPS | 0.16 | 0.033 | **0.053** | 0.10 | **0.0528** | 0.053 (rounded) |
| Zwischendecke g. unkond. | EPS c. 6 | 0.13 | 0.033 | **0.054** | 0.08 | 0.033 x 0.13/0.08 = **0.0536** | 0.054 (rounded) |
| Flachdach | EPS | 0.27 | 0.034 | **0.057** | 0.16 | 0.034 x 0.27/0.16 = **0.0574** | 0.057 (rounded) |

Citations: lambda and d from the doc -- `doc_beispielgebaeude_cellules.txt` p. 6 l. 12, 15, 29, 43, 47.
SIA 380/2 tab. 3 thicknesses -- `sia_380_2_2022.txt` l. 1955 (ext. wall EPS 0.15 VL / 0.22 VC),
l. 1964 (XPS 0.1 / 0.16), l. 1999 (ground floor XPS 0.1 / 0.16), l. 2037 + 2040 (floor over basement, EPS
0.08 VL / 0.13 VC -- l. 2031-2032), l. 2049 + 2036 (roof EPS 0.16 VL / 0.24 VC).

Warning: **Extraction caveat, not to be hidden**: SIA 380/2 tab. 3 is **scrambled** in my
text extraction (interleaved columns). The thickness pairs above are a **reconstructed
reading**, validated by **seven** U-values from the same table that I recover by calculation from
the doc's GW column: ext. wall 0.196 -> "0.2" (l. 1951); wall against ground 0.308 ->
"0.3" (l. 1965); ground floor 0.300 -> "0.3" (l. 1999); intermediate slab
0.599 -> "0.64" (l. 2011, discrepancy attributable to surface resistances); non-load-bearing
int. wall 0.301 -> "0.3" (l. 1973); load-bearing int. wall 2.61 -> "2.7" (l. 1982); roof
0.197 -> "0.2" (l. 2050). **[C]** -- but tab. 3 should be **re-read from visual rendering** before
final freezing (S10).

**What this establishes (and does not establish)**:
- **[C]** doc **GW = SIA 380/2 tab. 3 "limit value"**. Therefore "Gemäss Dokumentation" + GW
  gives **exactly** the same envelope as test 4, which says "Tabelle 3 'Grenzwert'".
- **[C]** doc **ZW = real material lambda at building thickness**, which **equals** the "target
  value" from tab. 3 for `aw2`, `Boden über Erdreich` and `Zwischendecke gegen unkonditioniert`
  (d_doc = d_VC: 0.16 / 0.16 / 0.13) but **exceeds** it for `aw1` (0.25 > 0.22, R +13.6 %) and
  `Flachdach` (0.27 > 0.24, R +12.5 %). The doc ZW is therefore **not** rigorously the
  normative target value.
- **[V]** No source read **prescribes** which set to use for tests 5 and 6.

**Decision: use GW for tests 5, 6 and 7. [I], confidence ~80 %.** Reasons:
1. **Mandatory physical consistency.** The S4.1 rule explicitly provides for tests to be
   "mitgerechnet" together. In a coupled model, the `101`<->`102` wall and the
   `101`<->`001` slab are **the same element** for test 4 (frozen on GW) and for tests 5/6. Two
   lambdas for the same wall is impossible. **[I] strong.**
2. **GW is the only set anchored to a normative value** (exact match with tab. 3 limit
   value, above); ZW deviates by 12-14 % on two compositions. A validation exercise
   reproduces a reference, not an intent. **[C] + [I].**
3. SIA 380/2 S7.2.3: "The **limit values** ... **must be complied with**" versus "The
   target values **should be aimed for**" (`sia_380_2_2022.txt` l. 1658-1663) -- only the
   limit value is a requirement. **[V]**, moderate argumentative weight.
4. A higher U (GW) yields larger demands, hence a **more discriminating** test between
   programs. Engineering argument, **not** normative.

**Counter-argument to be recorded**: test 4 **mixes** the levels -- constructions at the
**Grenzwert** of SIA 380/2 (p. 1 l. 12) and usage at the **Zielwerte** of SIA 2024 (p. 1 l. 18),
while tests 5 and 6 take the **Standardwerte** of SIA 2024. The value level is
therefore chosen **domain by domain**: one cannot deduce the construction level from the usage
level, nor the converse. This observation precludes any reasoning by analogy and **maintains the
item as an interpretation, not a fact**.

**Scope of uncertainty, quantified.** U-values calculated from the doc (surface resistances
**assumed [I]**: Rsi 0.13 / Rse 0.04 for vertical walls against exterior; Rsi 0.17 /
Rse 0 against ground; Rsi = Rse = 0.17 for downward interior flow):

| Composition | R layers GW | U GW | R layers ZW | U ZW | U GW / U ZW |
|---|---|---|---|---|---|
| `aw1` Aussenwände | 4.925 | **0.196** | 7.955 | **0.123** | 1.59 |
| `aw2` gegen Erdreich | 3.119 | **0.308** | 4.948 | **0.197** | 1.56 |
| Boden über Erdreich | 3.165 | **0.300** | 4.994 | **0.194** | 1.55 |
| Zwischendecke g. unkond. (Keller) | 3.736 | **0.245** | 5.268 | **0.178** | 1.38 |
| Flachdach | 4.908 | **0.197** | 8.113 | **0.121** | 1.63 |
| Zwischendecke (identical GW/ZW) | 1.329 | 0.599 | 1.329 | 0.599 | 1.00 |
| `iw1` (identical GW/ZW) | 3.057 | 0.301 | 3.057 | 0.301 | 1.00 |
| `iw2` (identical GW/ZW) | 0.123 | 2.61 | 0.123 | 2.61 | 1.00 |

-> gap of **~55 to 63 %** on the U-value of opaque exterior elements; **nil** on interior
elements. The choice therefore affects: test 5 -> facades of the 8 zones **and roof of the 6
2. OG zones**; test 6 -> ground floor facades (+ floor over basement if S8.1 were overturned); test 4 -> frozen
on GW, therefore unaffected.

**Recommended empirical resolution**: identical to S8.1 -- simulate GW and ZW, compare to the
bands from `Resultaterfassung_Test5.xlsx` / `_Test6.xlsx`. A 55 % gap on opaque U is
well outside any band: **the test is discriminating and will settle the matter**. **Do not declare
tests 5 and 6 "done" beforehand.**

### 8.3 Temperature setpoints for tests 4 and 5 -- **normative chain established; test 5 reconstructed, test 4 still open**

**Answer to the question asked**:
1. **Confirmed [V]**: the value cell is **empty in the source PDF**, for test 4
   (`spec_test4_cellules.txt` p. 2 l. 1-3: `Raumluft-` / `Sollwerte` / `temperatur`, without
   value, while the following line does carry "CO2 | 600 -- 1000 ppm, Aussenluftkonzentration
   400 ppm") **and** for test 5 (`spec_test5_cellules.txt` p. 2 l. 1: "Sollwerte |
   Temperatur", without value, the following line carrying "CO2 | 950 -- 1200 ppm"). Specification
   defect, cf. E10.
2. **No Anwenderbericht gives a numerical setpoint value.** Exhaustive search across
   the 16 reports: the only mentions are **qualitative** --
   `anwender_test4_1.txt` l. 15-16, `anwender_test5_1.txt` l. 14-15, `anwender_test6_1.txt`
   l. 14-15: the workbook was extended for « **zeitabhängige Raumtemperatur-Sollwerte** » and
   for the « **Wahl des Raumtemperatur-Sollwertes zwischen operativ und Luft** »;
   `anwender_test4_2.txt` l. 17 ("die operativen Temperaturen sind ähnlich verteilt");
   `anwender_test4_3.txt` l. 14 ("Bei Anlagensimulationen wertet TAS nur die Raumlufttemperatur
   aus"); `anwender_test5_3.txt` l. 51 and `anwender_test6_3.txt` l. 36 ("ideale Heater und
   Cooler"). **Verified negative [V].**
3. **But the specification does NOT delegate the setpoint to SIA 2024**: it falls under
   **SIA 380/2:2022 S5.2.2.3 and figure 1**, which are **in `/refs`**. Chain established:

   | Link | Source | Content |
   |---|---|---|
   | Nature of the quantity | SIA 380/2 S5.2.2.3, l. 1414-1415 **[V]** | "The setpoint values can be set for the **mean indoor air temperature** or for the **simplified operative temperature**. The choice is to be discussed with the client." -> explains **word for word** the "Wahl ... zwischen operativ und Luft" from the reports |
   | Form of setpoints | SIA 380/2 S5.2.2.3, l. 1421-1435 **[V]** | control **without** communication (`HEAT_EMIS_CTRL_DEF = 1 or 2` per SN EN ISO 52120-1 tab. 5) -> **constant values** at the maximum of the heating setpoint curve / at the minimum of the cooling setpoint curve; control **with** communication (3 or 4) -> **variable curves from figure 1** (dashed lines) |
   | Curves | SIA 380/2 **figure 1** (l. 1446-1467) **[V] partially** | "Room setpoint temperatures for heating and cooling"; axes read: ordinate **20 to 27 °C** (20 = lower limit, 27 = upper limit, 22 = `heating setpoint, Tset;H`), abscissa **10 to 25 °C** = "**48-hour** running mean outdoor temperature"; deviation `Tctr` between setpoint and limit |
   | Comfort origin | SIA 380/2 S5.2.2.5, l. 1469-1472 **[V]** | limits "are derived from the requirements of **SIA 180:2014 S2.3.1** ... correspond to those of **SIA 180:2014, figure 4, for residential and office spaces**" |
   | Usage-based offset | SIA 380/2 S5.2.2.5, l. 1477-1479 **[V]** | "the limits shall be offset by the **difference between the design values of the corresponding usage and usages 1.01 to 3.03 per SIA 2024:2021, table 11**" |
   | Quantified offsets | SIA 4010 S3.2, l. 384-390 **[V]** | "The offset of curves for usages **other than 1.01 to 3.03** ... gives **notably** a curve ... offset by **1 K** for usages 3.04, 5.01 to 5.03 and **6.03 and 6.04 (kitchens)**, and by 3 K for 9.01 ... A shift of the **upper** setpoint curve **upward** ... for usages **6.03 and 6.04 (kitchens) by 2 K**, for 9.01 by 4 K" |
   | Simplification | SIA 380/2, l. 1481-1482 **[V]** | "For simplification ... one may ... use the setpoint values per **SIA 2024:2021, annex B, table 13**" |
   | **Design** setpoints | SIA 380/2 S4.2.4 (l. 1271-1273) and S4.3.2.1 (l. 1322) **[V]** | for base **capacity**: "taken from **SIA 2024:2021, table 11**"; for "system-specific" capacity: variable curves from figure 1 |

4. **Consequence for test 5 -- reconstruction.** Test 5 usages are **3.1, 3.2, 3.3**
   (doc p. 10 l. 16, 18, 22-27) = **3.01 to 3.03**, hence within the range **explicitly
   not offset** per SIA 4010 S3.2. Test 5 setpoints are therefore the **base curve** from
   SIA 380/2 figure 1. This base curve is **numerically readable** in the
   test 6 specification (S8.4), and the kitchen cross-check (21 °C = 22 - 1 K) confirms
   it. Hence, **[I] strong, confidence ~80 %**:

   | Test 5 -- setpoint (Raumtemperatur, air or operative per S5.2.2.3) | Theta_e, 48 h running mean |
   |---|---|
   | **Heating**: 22.0 °C | <= 19 °C |
   | linear rise 22.0 -> 23.5 °C | 19 -> 23.5 °C |
   | 23.5 °C | >= 23.5 °C (plateau **[I]**) |
   | **Cooling**: 23.0 °C | <= 12 °C |
   | linear rise 23.0 -> 25.0 °C | 12 -> 17.5 °C |
   | 25.0 °C | >= 17.5 °C (plateau **[I]**) |

   Explicit caveats: (a) the plateau beyond the last breakpoint is **inferred**;
   (b) the assumption "usage 6.02 not offset" which authorises identifying the test 6 curve with the
   base curve is **[I]** (see S8.4); (c) nothing states whether test 5 uses the **curves**
   or the **constants** from S5.2.2.3 -- the usage by reference programs
   ("**zeitabhängige** Raumtemperatur-Sollwerte") strongly argues for **curves** [U].
   **Mandatory verification before freezing: visual rendering of SIA 380/2:2022 figure 1** (p. 26,
   `refs/SIA-380-2-2022.pdf`). This is **in the repository**: least-cost and most
   decisive lever -- it had not been identified in rev. 1.

5. **Test 4 -- remains open [?].** The usage is **4.4 Hörsaal** (doc p. 10 l. 17), **outside** the
   1.01-3.03 range. An offset is therefore possible and is calculated from **SIA 2024:2021
   tab. 11**, absent from `/refs`. Two converging but insufficient clues:
   - SIA 4010 S3.2 enumerates the offset usages and **does not cite 4.04** -- but the adverb
     "**notably**" makes the list **non-exhaustive**: silence is not proof.
     **[I] ~65 %** in favour of a zero offset.
   - Test 4 requests the **Zielwerte** from SIA 2024 (p. 1 l. 18) where tests 5 and 6
     request the Standardwerte: if tab. 11 distinguishes these levels for temperature, the
     test 4 setpoint differs **also** by this path. **[?]**
   Certain however: the test 4 setpoint is for **air temperature** -- line label
   "Raumluft-temperatur" (p. 2 l. 1-3) **and** « PI-Regler zur Einhaltung des
   **Raumlufttemperatur**-Sollwerts » (p. 3 l. 14). **[V]**
   Warning: Do not confuse with **supply air temperature**: « Zulufttemperatur | 16 -- 22.5°C
   (kühlen), 22.5 -- 29°C (heizen), PI-Regler ... » (p. 3 l. 12-14). **[V]**
   -> **Honest conclusion: the test 4 room setpoint is not determinable from ANY available
   source.** It requires SIA 2024:2021 tab. 11 (and, if the simplified path is desired,
   annex B tab. 13). This is the **justification for acquisition** requested: cf. S11.

### 8.4 Test 6 setpoints -- **READ** (new)

The coordinate-based extraction makes the test 6 specification graph exploitable.
`spec_test6_cellules.txt` p. 2 l. 35-47 -- ordinate axis **« Raumlufttemperatur »**
(hence **air temperature**, not operative **[V]**), graduations 21.5 to 25.5; abscissa
**« gleitender 48-h-Mittelwert Aussenlufttemperatur »**, -15 to 35 °C; legend `Kühlen` /
`Heizen`; **four point labels**: `17.5; 25`, `23.5; 23.5`, `12; 23`, `19; 22`.

Position cross-check **[C]**: in the `-layout` extraction (`spec_test6.txt` l. 87-99), the
labels `17.5; 25` and `12; 23` are at the **same column position**, and `23.5; 23.5` and
`19; 22` at another, further right -- i.e. grouped **by curve** (left points /
right points). Combined with the physical constraint T_setpoint,cool >= T_setpoint,heat (the
reverse assignment would give cooling at 22 °C below heating at 23 °C), the assignment
is **unambiguous**:

| Test 6 -- Restaurant, **air temperature** setpoint | Theta_e, 48 h running mean |
|---|---|
| **Heizen** 22.0 °C | <= 19 °C |
| 22.0 -> 23.5 °C (slope exactly 1/3) | 19 -> 23.5 °C |
| 23.5 °C | >= 23.5 °C **[I]** |
| **Kühlen** 23.0 °C | <= 12 °C |
| 23.0 -> 25.0 °C (slope 2/5.5 = 0.364) | 12 -> 17.5 °C |
| 25.0 °C | >= 17.5 °C **[I]** |

Status: the **four points [V]** (two independent extractions); the **curve assignment [C]**; the **plateaux [I]**.

**Cross-check that locks the 22 °C value -- and resolves the former S8.2 (kitchen)**: the
kitchen is usage **6.4**, for which SIA 4010 S3.2 (l. 386-387) prescribes a lower curve
**offset by 1 K**. The specification gives the kitchen "Sollwert heizen:
**21°C**" (`spec_test6_cellules.txt` p. 3 l. 25-27) = **22 - 1**. **[C]** This coincidence:
- confirms that the heating plateau of the base curve is indeed **22.0 °C**;
- confirms that the kitchen offset is **downward** for the lower curve;
- establishes **[I]** that usage **6.02 (Restaurant) is NOT offset** -- hence the curve read
  above **is** the SIA 380/2 figure 1 base curve, which authorises transfer to
  test 5 (S8.3.4). Confidence ~85 %.
- **resolves the former contradiction S8.2 from rev. 1**: the kitchen carries a heating
  setpoint (21 °C) **without emitter** ("Wärmeabgabe | keine") because its heat can
  only come from supply air; the setpoint is the **air regulation target**, not a
  zone emitter target. Still to confirm on the engine side that 21 °C is achievable with supply air
  capped at 20 °C (`spec_test6_cellules.txt` p. 4 l. 26-33: sliding Zulufttemperatur
  (12 ; 20) -> (20 ; 18) °C): very probably **not** in winter, the kitchen temperature
  then floating below 21 °C under the effect of internal process gains. **[I]**, to be verified
  numerically. Note: the kitchen receives « inkl. **Prozesswärme** (Strahlungsanteil 15%) »
  (p. 2 l. 57) -- considerable internal gain that makes the point credible.

### 8.5 What remains truly open

| # | Item | Impact | What would resolve it |
|---|---|---|---|
| **O1** | **Test 4 room setpoint** (usage 4.4 Hörsaal): value absent from PDF, possible offset from base curve unknown, "Zielwerte" level from SIA 2024 uncharacterised | **blocking** for test 4 and for any `101`<->test 5 zone coupling | **SIA 2024:2021 tab. 11** (+ annex B tab. 13) -- S11; failing that, SIA 4010 FAQ (S4.6.1, `sia_4010_2023.txt` l. 2790-2792) |
| **O2** | **Exact values from SIA 380/2 figure 1** (limits, setpoints, `Tctr`, breakpoints) | conditions S8.3.4 and S8.4; without this, the reconstructed curve remains an inference | **visual rendering of `refs/SIA-380-2-2022.pdf` p. 26** -- in the repository, zero cost |
| **O3** | **GW or ZW**: no prescription found; GW default argued at ~80 % | ~55-63 % on opaque U, tests 5 and 6 | comparative simulation against `Resultaterfassung_Test5/6.xlsx` (S8.2); or SIA FAQ / sub-commission (SIA 4010 S4.6.2) |
| **O4** | **Floor over basement**: adiabatic retained at ~80 % | 273 m2 at delta_U 0.245 W/(m2K), test 6 | comparative simulation (S8.1); or SIA FAQ |
| **O5** | **Control with or without communication** (S5.2.2.3): variable curves or constants at extrema? | changes the setpoint by 0 to 1.5 K and can create **simultaneous** heating/cooling (SIA 380/2 S5.2.2.4, l. 1438-1444) | the reports say "**zeitabhängige** Sollwerte" [U] -> curves; to be confirmed by the `HEAT_EMIS_CTRL_DEF` class of each test (SN EN ISO 52120-1 tab. 5, **absent from `/refs`**) |
| **O6** | **Air or operative?** Resolved for test 4 (air, p. 3 l. 14) and test 6 (axis "Raumlufttemperatur"). **Not resolved for test 5**: the line says only "Temperatur" (p. 2 l. 1) | the workbooks require **both** distributions (`PREUVE_classeur_test4.txt` l. 22: `P21=Mittlere Raumlufttemperatur`, `W21=Operative Temperatur`) | `Resultaterfassung_Test5.xlsx`; SIA 380/2 S5.2.2.3 leaves the choice to the client |
| **O7** | **Variant 5A-5D to use in test 7** for "Elektrische Energie Tests 4 bis 6": not specified | directly changes a test 7 test quantity | **[U]** Tas took **5C** and explicitly flags it (`anwender_test7_4.txt` l. 35-38); to be confirmed by the other workbooks |

### 8.6 Ambient temperatures of ducts outside zones -- **partially lifted [U]**

- Test 5: given for Zentrale/Steigzone (15/28 °C, p. 2 l. 15-16); **not given** for the
  "Deckenbereich Korridor 1. + 2. OG" (20 m, U 1.1 W/(m2K), p. 2 l. 11-12) nor for the
  "Deckenbereich Zonen" ducts (p. 2 l. 13-14), even though "Wärmeverluste Verteilung" is a
  requested diagnostic (p. 5 l. 27-31). **[V]** of the gap.
- **Documented usage [U]**, identical for tests 5 and 6: « Die Berechnung der Verteilverluste
  wurde vereinfacht durchgeführt: **Steigzonen: Verluste mit konstanter Umgebungstemperatur im
  Sommer 28 °C, im Winter 15 °C. In den Zonen wurde als Umgebung die mittlere Raumtemperatur
  aller Zonen verwendet. Die Verluste werden weder in der Zone noch berücksichtigt im
  Wärmebedarf.** » (`anwender_test5_3.txt` l. 53-56; `anwender_test6_3.txt` l. 38-41, word for
  word). Only one program out of four documents this; the others either do not calculate these losses
  (`anwender_test5_2.txt` l. 20-24, EnergyPlus), or do not define them
  (`anwender_test5_4.txt` l. 36-37, Tas). -> **Convention adopted**: riser ducts at
  15/28 °C; ducts within a zone at the **mean** zone temperature; losses **not**
  attributed to the zone nor to the heating demand. Status **[U]**, confidence ~70 % (single
  declarant), **to be compared against the band**.
- Test 6: the specification gives **neither U-Wert nor temperature** for its ducts (p. 3
  l. 32-36) -- strong argument from S8.1.

### 8.7 Actual geometric adjacencies -- unchanged **[?]**

Only areas are available, not topology. Not established:
- does Hörsaal `101` have **exterior** walls (and which ones)?
- which test 5 rooms are **adjacent** to the Hörsaal, over what area, at which level?
- is the Hörsaal above the **Restaurant** (test 4 <-> test 6 interface)?
- window distribution per room (no text source);
- **new**: **which** of `201`-`204` carry the "schwere Innenwand" (S3.2, support 5)?
- **new**: column-to-distribution-group mapping in `Lastverläufe_220607.xlsx`.
-> These are **geometry calculations**, not standard readings: to be done by
`ve-adapter-engineer` on `IfcRelSpaceBoundary` / the DWGs, **before** writing the adiabatic
assignments.

---

## 9. Direct consequences for the IESVE import

1. **11 zones to create in total**, never 29: `101` (test 4); `100`, `102`, `200`, `201`, `202`,
   `203`, `204`, `205` (test 5); `001`, `002` (test 6). Test 7: **none** (confirmed [U], S3.4).
2. `101` = **a single** zone of 6.38 m height; do not split it at level 6.8.
3. Do not create a zone on `Storey 9.8` (roof level).
4. Reference areas = IFC `GrossFloorArea` absolute value (S5).
5. Three separate models (one per test) are **compliant** and safer than the complete building:
   the S4 rule then makes all interior walls adiabatic, without having to import
   setpoints from another test. The coupled model is only permitted once O1 is lifted.
6. **Retain the thermal mass of adiabatic elements** -- decision now supported
   (S4.2, confidence ~95 %) and **distinguish iw1 / iw2 per room** in offices `201`-`204`.
7. `002` is coupled to `001` by an air transfer of **350 m3/h**: inter-zone transfer, not
   outdoor air. Caveat: Tas could not model it (`anwender_test6_4.txt` l. 22-23) -- the
   reference band therefore includes **one** program without transfer.
8. Set up materials in **two GW/ZW sets with identical thicknesses**, **GW by default**
   (S8.2), test 4 being frozen on GW; **no interior element is affected** by this choice.
9. Do not activate daylight-dependent lighting control (S7.3).
10. **Floor `001`/`002` over basement: adiabatic** by default (S8.1), with the
    non-adiabatic variant configurable for the discriminating test.
11. Setpoints: implement a **curve** as a function of the 48 h running mean of the
    outdoor temperature (not a constant), with an **air / operative** switch
    (SIA 380/2 S5.2.2.3). Test 6 values: S8.4; test 5: S8.3.4 (to be confirmed by O2);
    test 4: **blocked** by O1.
12. The 48 h running mean outdoor temperature is an **input quantity to
    calculate** from the weather file -- plan for it in `engine/`.

---

## 10. What would lift the most uncertainties, in order of payoff

| Priority | Source | What it resolves | Cost |
|---|---|---|---|
| **1** | **Visual rendering of `refs/SIA-380-2-2022.pdf`, figure 1 (p. 26, S5.2.2.4) and table 3 (p. 35-36)** | **O2** (setpoint curves, `Tctr`, breakpoints) and the S8.2 extraction caveat (VL/VC thicknesses). **Already in the repository.** | nil |
| **2** | **SIA 2024:2021** (or prSIA 2024:2021) -- tab. 11, annex B tab. 13, schedules, simultaneities | **O1** (test 4 setpoint), the 4.04 usage offset, and **all** usage data for the 11 zones (S11) | purchase |
| 3 | **Comparative simulation GW/ZW and basement adiabatic/non-adiabatic** against `Resultaterfassung_Test5.xlsx` / `_Test6.xlsx` | **O3** and **O4**, empirically and unambiguously | engine work |
| 4 | **IFC geometry (space boundaries) or DWG** | S8.7: adjacencies, Hörsaal exterior walls, windows per room, `201`-`204` iw1/iw2 | adapter work |
| 5 | **`Resultaterfassung_Test4/5/6/7.xlsx` and `Lastverläufe_220607.xlsx`** | **E9** (quantities and criteria for tests 4, 6, 7, absent from PDFs), **O6**, **O7**, test 7 group mapping | xlsx reading |
| 6 | **SIA 4010 FAQ** (announced by S4.6.1, `sia_4010_2023.txt` l. 2790-2792; not in repository) | **O3**, **O4** with authority above any inference | SIA request |
| 7 | **SN EN ISO 52120-1:2022 tab. 5** | **O5** (`HEAT_EMIS_CTRL_DEF` / `CLG_EMIS_CTRL_DEF` classes, hence curves or constants) | purchase |
| -- | ~~Test 5, 6, 7 Anwenderberichte~~ | **EXHAUSTED**: processed, **silent** on envelope, constructions and numerical setpoints. Useful only for modelling practices (S12) | done |

---

## 11. Required SIA 2024:2021 usages -- purchase order

**Finding**: SIA 2024:2021 (and prSIA 2024:2021) are **absent from `/refs`**. The test 4, 5 and 6
specifications and the documentation reference them **at least 21 times**. Without this
technical guide, **none** of the 11 zones can be populated with internal gains, occupancy and
schedules, and the test 4 setpoint remains indeterminate (O1).

### 11.1 Usages to extract (documentation / specification numbering)

| Usage | Rooms | Requested value level | Referral source |
|---|---|---|---|
| **4.4 Hörsaal** (« Standardnutzung "Hörsaal" ») | `101` | **Zielwerte** | `spec_test4_cellules.txt` p. 1 l. 18; doc p. 10 l. 17 |
| **3.1 Einzel-, Gruppenbüro** | `201`-`205` | **Standardwerte** | `spec_test5_cellules.txt` p. 1 l. 18; doc p. 10 l. 23-27 |
| **3.2 Grossraumbüro** | `102` | **Standardwerte** | idem; doc p. 10 l. 18 |
| **3.3 Sitzungszimmer** | `100`, `200` | **Standardwerte** | idem; doc p. 10 l. 16, 22 |
| **6.2 Selbstbedienungsrestaurant** | `001` | **Standardwerte** | `spec_test6_cellules.txt` p. 1 l. 19-21 (Warning: the doc says 6.1, cf. E2) |
| **6.4 Küche zu Selbstbedienungsrestaurant** | `002` | **Standardwerte**, « inkl. **Prozesswärme** (Strahlungsanteil 15 %) » | `spec_test6_cellules.txt` p. 2 l. 55-57 (Warning: the doc says 6.3, cf. E2) |
| *(for reference, "complete building" variant only)* | 12.1, 12.3, 12.4, 12.7, 12.11 | -- | doc p. 10 l. 7-33 |

### 11.2 Data to extract, by identified referral

| # | Data item | Referral (file, line) |
|---|---|---|
| 1 | **Tab. 11 -- design values**: room setpoint temperature for heating and cooling, area per person, activity, installed capacities | `sia_380_2_2022.txt` l. 1271-1273 (S4.2.4, heating capacity); l. 1322 (S4.3.2.1, cooling capacity); l. 1477-1479 (S5.2.2.5, **curve offset calculation**); `sia_4010_2023.txt` l. 384-390 (S3.2) |
| 2 | **Annex B, tab. 13 -- setpoint values** (simplified path) | `sia_380_2_2022.txt` l. 1481-1482 |
| 3 | Personen: **Anzahl**, **Aktivitätsgrad**, **Zeitplan**, **Jahresgleichzeitigkeit** -- tests 5 and 6 | `spec_test5_cellules.txt` p. 1 l. 29-36; `spec_test6_cellules.txt` p. 2 l. 23-30 and p. 3 l. 13-20 |
| 4 | Personen: **Zeitplan** and **Jahresgleichzeitigkeit** -- test 4 (headcount 55 and 1.2 met are **given**) | `spec_test4_cellules.txt` p. 1 l. 29-30 |
| 5 | Geräte: **Wärmeeintragsleistung**, **Zeitplan**, **Jahresgleichzeitigkeit** -- tests 5 and 6 | `spec_test5_cellules.txt` p. 1 l. 35-38; `spec_test6_cellules.txt` p. 2 l. 29-32 and p. 3 l. 19-22 |
| 6 | Geräte: **Zeitplan** and **Jahresgleichzeitigkeit** -- test 4 (10 W/m2 **given**) | `spec_test4_cellules.txt` p. 1 l. 33-34 |
| 7 | Beleuchtung: **Wärmeeintragsleistung** and **Zeitplan** -- tests 5 and 6 (test 4: 6.4 W/m2 and "Ein 07:00-18:00, aus im Juli" **given**) | `spec_test5_cellules.txt` p. 1 l. 39-41; `spec_test6_cellules.txt` p. 2 l. 33-34 and p. 3 l. 23-24; test 4 p. 1 l. 35-38 |
| 8 | **Outdoor air reference flow rates** -- cited **to be overridden**, but to be known for tracing the deviation: « Nenn-Volumenstrom 10 m3/(h*m2) {**abweichend von SIA 2024:2021**} » (test 4) and « 25 m3/h pro Person (alle Nutzungen, **abweichend von SIA 2024:2021**) » (test 5) | `spec_test4_cellules.txt` p. 1 l. 19-21; `spec_test5_cellules.txt` p. 1 l. 20-22 |
| 9 | **Zeitpläne** for occupancy, equipment and lighting -- global referral from the documentation | `doc_beispielgebaeude_cellules.txt` p. 10 l. 2 and l. 34-36 |
| 10 | Reference edition: **SIA 2024:2021 vs prSIA 2024:2021** -- test 6 uses **both** labels | E5; `spec_test6_cellules.txt` p. 1 l. 19 and p. 2 l. 28 |
| 11 | Distinction **Standardwert / Zielwert / Grenzwert** in SIA 2024, for each quantity above | required by the different levels of test 4 (Zielwerte) and tests 5-6 (Standardwerte) |
| 12 | Consistency check to perform upon receipt: 1040 m3/h / 25 m3/(h*pers) = **41.6 persons** over 269.87 m2 of test 5 -> **6.5 m2/pers**; to be compared to the area per person from tab. 11 for 3.01-3.03 | `spec_test5_cellules.txt` p. 2 l. 18 and p. 1 l. 20-22 |

**Other standards cited by the tests and absent from `/refs`** (to be flagged in the same step):
SIA 2028 (DRY climate, cited at the top of **every** specification), SIA 180:2014 (origin of
comfort limits, `sia_380_2_2022.txt` l. 1469-1470), SN EN ISO 52120-1:2022 tab. 5 (emission
control classes, **O5**), SN EN 15316-2:2017 (`Tctr`, l. 1417-1419), SN EN 16798-5-1 and
-7 (including national annex NA.2.2.4 used by a reference program,
`anwender_test5_1.txt` l. 35-36), SN EN 16798-9 / -13 / -15, SN EN 15316-4-2 / -4-3 / -5 (test 7),
SIA 387/4:2023 (solar shading control).

---

## 12. Secondary contributions from the Anwenderberichte (status **[U]**: usage, not prescription)

### 12.1 Contributing set for the bands

**Four** reference programs per test, identical for tests 4 to 7:

| Program | Version | Reports | Author / date |
|---|---|---|---|
| EN standard workbooks ("Excel" column in workbooks) | EN ISO 52016-1 (E4Tech / SIA 2044) extended by G. Zweifel + EN 16798-5-1 (epb.center 25.10.2021) + EN 16798-7 (12.7.2021, **test 4 only**) + EN 16798-9 / -13 / 15316-4-2 (test 7) | `anwender_test4_1`, `_test5_1`, `_test6_1`, `_test7_1` | G. Zweifel, 11.11.2022 |
| EnergyPlus / OpenStudio | 9.1.0 | `_test4_2`, `_test5_2`, `_test6_2`, `_test7_2` | C. Messmer, 12.11.2022 |
| IDA-ICE | 5.0 Beta 22 (tests 4-6), Beta 23 (test 7) | `_test4_4`, `_test5_3`, `_test6_3`, `_test7_3` | F. Sidler / Ch. Stettler, 18-21.11.2022 |
| EDSL Tas | 9.5.4 | `_test4_3`, `_test5_4`, `_test6_4`, `_test7_4` | R. Schär-Sommer / M. Fehr, 17.11.2022 and 15-16.05.2023 |

Corroborated by the workbook structure: `PREUVE_classeur_test4.txt` l. 9-12 -- columns
`D = 'Daten Testprogramm'` (the candidate), `E = IDA_ICE`, `F = Excel`, `G = EnergyPlus`,
`H = TAS`; band in `T8 = Mittelwert`, `U8 = obere Grenze`, `V8 = untere Grenze`. **[V]**
The number of contributors is therefore **4**, not 5: column `D` is the program under test.

**Number of zone instances declared**: test 4 -> 3 instances of the 52016-1 workbook for 1 zone
(`anwender_test4_1.txt` l. 8; the iteration in fig. p. 1 explains why); test 5 -> **6**
instances for 8 rooms (`_test5_1.txt` l. 8, 18-20); test 6 -> **2** instances for 2 rooms
(`_test6_1.txt` l. 8, 18). Consistent with the S1 zoning.

### 12.2 Test 5 variants -- reconstruction **[C]**

`spec_test5_cellules.txt` p. 3 l. 6-14 and p. 4 l. 34-35 give three rows "Variante | 5A |
5B | 5C | 5D" with **only two** values per row. The distribution across the four columns
can be reconstructed unambiguously by cross-checking with the reports:

| Variant | Konstantdruckanteil (ZUL+ABL) | WRG rotatif | Humidifier |
|---|---|---|---|
| **5A** | **50 + 50 Pa** | Hygroskopisch (eta_T 0.67; eta_x 0.42) | Kontaktbefeuchter |
| **5B** | 270 + 270 Pa | Hygroskopisch | Kontaktbefeuchter |
| **5C** | 270 + 270 Pa | **Nicht hygroskopisch** (eta_T 0.69; eta_x 0.3) | Kontaktbefeuchter |
| **5D** | 270 + 270 Pa | Nicht hygroskopisch | **Dampf** |

Supports: (a) IDA-ICE gives **one** set of fan coefficients for "Test 5A" and **another**
for "Test 5B...D" (`anwender_test5_3.txt` l. 13-27) -> the pressure split is
1 / 3, not 2 / 2; (b) IDA-ICE: « Rotortype: **Hygroscopic** » for "Test A, B" and
« **Untreated** » for "Test C, D" (l. 29-35) -> split 2 / 2; (c) Tas, for test 7: « wurde
**Test 5C mit Kontaktbefeuchter und höherem Konstantdruckanteil** herangezogen. Die Varianten
mit **tieferem Konstantdruckanteil** oder **Dampfbefeuchter** weisen einen abweichenden
elektrischen Energiebedarf auf » (`anwender_test7_4.txt` l. 35-38) -> 5C = high pressure +
contact, and variants with low pressure and steam exist; (d) Zweifel: « Die
Veränderungen der Resultate zwischen den Varianten (**Ventilatorregelung, WRG-Typ und
Befeuchtertyp**) » (`anwender_test5_1.txt` l. 64-65) -> exactly **three** changes for
four variants, i.e. one parameter changed at each step. Confidence ~90 %.
Quantities to deliver, differing by variant: `spec_test5_cellules.txt` p. 4 l. 46-60 and p. 5
l. 1-3; diagnostics p. 5 l. 12-40, « **Test 5D keine** » (p. 5 l. 41). **[V]**
Test 5 criteria (p. 5 l. 4-9): « Zulässiger Bereich für Jahressummen: **Mittelwerte der
Referenzprogramme +/- maximale Abweichung**. Die **Häufigkeitsverteilungen** müssen im
**Streubereich** der Referenzprogramme liegen. » **[V]** -- identical to the workbook formulas
(`PREUVE_classeurs.txt` l. 9-11).

### 12.3 Return air, internal gains, CO2 control -- notable practices

- **Former S8.6 (test 5: where is air returned from?) -- LIFTED [U], confidence ~90 %**: « Ebenso
  wurde die **Ablufttemperatur volumenstromgewichtet aus den verschiedenen Raumtemperaturen**
  errechnet » (`anwender_test5_1.txt` l. 25-26). Return air is drawn **from the 8 served
  zones**, the state being the flow-weighted mix; **no cascade via the WCs**.
  Same wording for test 6, « aus den **beiden** Raumtemperaturen » (`_test6_1.txt`
  l. 23-25). The term "Ersatzluftanlage" remains defined in **no** source from `/refs`.
- **CO2 control, substitute used in lieu of CO2 balance**: « ein vereinfachter Ansatz gemäss
  SN EN 16798-7, **Anhang NA, Ziffer NA.2.2.4** ... fctrl = focc + **0.33** * (1 - focc) » for
  test 4 (`anwender_test4_1.txt` l. 66-73) and « fctrl = focc + **0.167** * (1 - focc) » for test 5,
  « wobei der Faktor zur Berücksichtigung des **kleineren CO2-Proportionalbands (gegenüber
  Test 4)** auf 0.167 gesetzt wurde » (`anwender_test5_1.txt` l. 34-46). **[U]** -- useful for
  interpreting flow deviations during the first hours of occupancy, **not** a prescription.
- **Ideal emitters**: IDA-ICE used « **ideale Heater und Cooler** » in test 5 zones
  (`anwender_test5_3.txt` l. 51) and for the test 6 Restaurant (`_test6_3.txt` l. 36).
- **Known defects and non-deliveries** (to be kept in mind before concluding from a band deviation):
  Tas modelled **neither** the test 6 KVS-WRG (replaced by a constant-eta 0.71 exchanger,
  `_test6_4.txt` l. 10-15) **nor** the Restaurant->Küche transfer (l. 22-23); its "Wärmeabfuhr
  Luftkühler total" is ~30 % above the others, stated cause: absence of daylight saving time
  (l. 34-37); for test 5, Tas did not define distribution losses (l. 36-37) and its
  "Luftkühler latent" is "unrealistisch tief" (l. 38-42); EnergyPlus did not calculate
  duct losses and leaks for test 5 (`_test5_2.txt` l. 20-24); for test 7, Tas flags
  the absence of a "Kälterückgewinnung" column in the results file (`_test7_4.txt`
  l. 43) and a significantly overestimated PV production (l. 60-64).

### 12.4 Source defects -- cross-check

| Defect | Proof |
|---|---|
| `anwender_test4_3.txt` (Tas, test 4) contains a paragraph **from test 3**: « Aufgrund der Feststellungen aus Test 2 kann in **Test 3** nur eine Auswahl an Fällen gerechnet werden (Sonnenschutzregelung 2 und 4) » | l. 10-12 -- defect already known, **confirmed** |
| `anwender_test6_3.txt` (IDA-ICE, test 6) bears the heading « Eingaben Zuluftventilator **Test 5A** » | l. 13 -- block copied from the test 5 report (the coefficients themselves differ: values specific to test 6) |
| The IDA-ICE reports for tests **5 and 6** state « CO2-Regelung in der Zone: Level of CO2 min. **600** ppm, max. **1000** ppm » | `_test5_3.txt` l. 45-46 and `_test6_3.txt` l. 29-30, **word for word identical** to `_test4_4.txt` l. 29-30. Yet the test **5** spec requires **950 -- 1200 ppm** (`spec_test5_cellules.txt` p. 2 l. 2) and test **6 has no CO2 control** (3-stage schedule-based system). -> **block copied from the test 4 report**; do not derive any value from it |
| `anwender_test5_4.txt` (Tas) mentions a threshold « < **900** ppm » where the spec says 950 ppm | l. 26-27 -- unexplained discrepancy |
| Specs for tests **4, 6 and 7**: **no** "Zu liefernde Resultate" / "Testkriterien" block | cf. E9 |
| Test 6 spec: cell « Kühldecken / Vorlauftemperatur » **empty** | `spec_test6_cellules.txt` p. 2 l. 22 |
| Specs for tests 4 and 5: temperature setpoint cell **empty** | cf. E10, S8.3 |
| Test 7: IDA-ICE **modified** the imposed load file (BWW column densified) while the spec requires "**einheitliche**" profiles | `_test7_3.txt` l. 11-16 vs `spec_test7_cellules.txt` p. 1 l. 12 and l. 23 |

**Working rule that follows**: an Anwenderbericht is **never** used alone. Any
value that appears only in one report, and contradicts a specification, is treated as a
**report defect**, not as data.
