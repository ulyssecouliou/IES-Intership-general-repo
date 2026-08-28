> **Note:** Translated from French original. See [classes-de-validation.spec.md](classes-de-validation.spec.md) for the source document.

# SIA 4010 Validation Classes --- Point-by-Point Status

> Status: **ESTABLISHED**, based on evidence. Established 2026-08-05.
>
> **One-sentence conclusion**: all eight classes are blocked by **a single
> file**, `KLO_dry_normal.PRN` (SIA 2028 DRY, Zurich-Kloten station, dataset
> "Gegenwart"). The easiest class --- class 5 --- needs only the
> **hourly air temperature** from this file, nothing else.

---

## 1. The authoritative matrix

SIA 4010:2023, **table 63** (p. 48), read verbatim. This table, and not our
assumptions, defines which tests each class requires.

| Class | Covered applications | Solar protection | Required tests |
|---|---|---|---|
| **1A** | cooling demand assessment; **basic** required thermal capacity | without regulation based on sun position (e.g. fabric blinds) | **1 and 2A** |
| **1B** | same | **louvre** blinds | **1 and 2** |
| **2A** | lighting energy (SIA 387/4:2023 §3.4); heating and cooling energy demand | fabric | **1, 2A, 3A to F** |
| **2B** | same | louvres | **1 to 3** |
| **3** | humidification and dehumidification demand assessment | --- | **1, 4 to 6** |
| **4A** | **system-related** required thermal capacity; cooling and heating energy demand | fabric | **1, 2A, 3A to F, 4 to 7** |
| **4B** | same | louvres | **1 to 7** |
| **5** | cooling and heating energy demand **for existing demand profiles** | --- | **7 only** |

**Structural fact**: class 5 is the **only** one that does not require Test 1.
It is therefore, unambiguously, the easiest --- and it is the one to start
with.

---

## 2. What each test requires, verified

| Test | Climate | Building | SIA 2024 usage data | Other |
|---|---|---|---|---|
| **1** cases 600/640/900/940/600FF/900FF | **DRYCOLD Denver --- IN OUR POSSESSION, verified** | test room ISO 52016-1 ch. 7, **spec frozen** | none | --- |
| **1** diagnostic cases 1A->1E | **Kloten** | same | 1D and 1E: usage | 1E = only case with pass/fail criterion |
| **2**, **2A** | **Kloten** | test room | none | louvres (2) / fabric (2A) |
| **3**, **3A--F** | **Kloten** | test room | none | solar protection |
| **4** | **Kloten** | example building, room `101` Hoersaal | **sheet 4.4**, *Zielwerte* level | setpoint **resolved**, cf. §4 |
| **5** | **Kloten** | example building, 8 rooms | **sheets 3.1, 3.2, 3.3**, *Standardwerte* | --- |
| **6** | **Kloten** | example building, 2 rooms | **sheets 6.2, 6.4**, *Standardwerte* | --- |
| **7** | **Kloten --- air temperature only** | **none** | **none** | load profiles **provided** |

### 2.1 Why Test 7 is the least demanding --- established from the specification

`Spezifikation_Test7.pdf` (4 pp.) requires **neither a building thermal model,
nor solar, nor glazing, nor solar protection, nor usage data**:

- **Load profiles**: "Es sind einheitliche Profile gemaess
  `Lastverlaeufe_220607.xlsx` zu verwenden" --- cold and heat, plus the DHW
  load profile. **Provided by SIA.**
- **Distribution**: lump sums (5% losses, 2% auxiliary energy).
- **Storage**: two 2,000 l water tanks, charging control described.
- **Generation**: Climaveneta NX-W-Y/H 0182, reversible water-to-water heat
  pump, 55.9 kW cooling / 60.0 kW heating, characteristic fields given per
  EN 14825.
- **Outdoor air unit**: dry cooler 70 kW in cooling mode, outdoor air heat
  exchanger 76 kW in heating mode; "**Temperaturdifferenz
  Aussenluft -- Vorlauftemperatur 4 K (bei Volllast)**".

It is this last line that creates the weather dependency, and **it alone**: the
outdoor air temperature sets the source/sink temperature, hence the operating
point of the heat pump in its characteristic field.

### 2.2 Negative check: the provided profiles do not contain weather data

`Lastverlaeufe_220607.xlsx` was inspected column by column.

- sheet `Gruppen`: 8765 rows x 11 columns --- hour, then power values in W
  (Kuehldecke T5+T6; Lueftung T4/T5/T6 cooling; BWW, Lueftung T4/T5/T6,
  Heizdecke T5, Konvektoren T6 heating);
- sheet `Grundlagen`: 8769 rows x 46 columns --- detail by test and by
  room, areas, DHW, tank state of charge.

Header search across both sheets:
`aussen|extern|temperat|theta|°C|klima|wetter` -> **no matches**.

**SIA provides the loads, not the outdoor conditions.** Class 5 therefore
cannot be made self-contained.

---

## 3. What is blocking, by class

> **REVISION OF 2026-08-05** --- the Kloten outdoor temperature was found
> in an official source: `Test4/Resultaterfassung Test4.xlsx`,
> sheet **`Wetterdaten`**. The weather blocker is therefore reduced to **solar
> radiation** and **humidity**. Cf. §3.0.

### 3.0 What the official package actually contains as weather data

Exhaustive scan of the seven evaluation workbooks, all sheets, headers
across 14 rows, pattern
`site outdoor|drybulb|dew ?point|humidity|feuchte|solar radiation|horizontal radiation|beam|diffuse solar|direct solar|globalstrahlung|wind ?speed|barometric`:

| Workbook | Matches | Content |
|---|---|---|
| Test 1, 2, 3, 6, 7 | **0** | --- |
| **Test 4** | **1** | sheet `Wetterdaten` --- `Site Outdoor Air Drybulb Temperature [C](Hourly)` and `EMS Two Day Average OA Temp [C](Hourly)`, **8760 values each** |
| Test 5 | 21 | humidifier power and air humidity values --- **results, not climate** |

**Acquired**: hourly outdoor air temperature for Zurich-Kloten,
min -13.02 / max 34.10 / **mean 9.469 degC** --- consistent with the station. Frozen
in `refs/reference-data/sia-2028-kloten-temperature.{json,csv}`.

**Still absent from all official sources**: **solar radiation**
(in any form) and **outdoor air humidity**.

### 3.1 Blockers by class, after revision

| Class | Kloten solar | Kloten humidity | Usage data | Other |
|---|---|---|---|---|
| **5** | **yes** --- mandatory variable no. 14 "Elektrische Energie PV" | no | --- | --- |
| **1A** | **yes** | no | --- | --- |
| **1B** | **yes** | no | --- | louvre model |
| **2A** | **yes** | no | --- | lighting / daylight |
| **2B** | **yes** | no | --- | louvres + lighting |
| **3** | **yes** | **yes** | sheets **4.4; 3.1--3.3; 6.2, 6.4** | --- |
| **4A** | **yes** | **yes** | same | --- |
| **4B** | **yes** | **yes** | same | **SIA 387/4:2023** tab. 9 (we have **2017**) |

**8 out of 8 classes depend on Kloten solar radiation.** It is now
the single dominant blocker --- temperature, for its part, is acquired.

### 3.1 Why the free CH2018 dataset cannot substitute for it

Three independent reasons, each sufficient on its own:

1. **Period.** The free package only contains 2035 and 2060 (RCP 2.6 / 8.5).
   Column `time.yy` verified. No present-period file.
2. **Content.** All four reference programs write
   "**Original-SIA-Datei**"; IDA ICE names it `KLO_dry_normal.PRN`. The
   Test 2 Excel report specifies: "Die Original-Klimadaten nach SIA 2028
   **enthalten die Solarstrahlung auf die vertikalen Flaechen der
   Haupthimmelsrichtungen**". The CH2018 CSV only carries `gls`, `str.diffus`,
   `str.direkt` --- **no vertical columns**.
3. **Format.** `.PRN` versus `.csv`.

Warning --- honest caveat on the word "normal": we initially read
`SIA 2028 DRY normal` as designating the present period. Nothing establishes
this. Since the CH2018 package delivers exactly two variants --- `DRY` and
`1in10-warmsummer` --- "normal" **most likely distinguishes the normal DRY
year from the decadal warm-summer year**. The conclusion does not change:
reasons 2 and 3 hold regardless of interpretation.

### 3.2 And VE does not read `.PRN`

Library shipped with VE 2025, `C:\Program Files\IES\Shared Content\Weather`:
460 files, **no Swiss station**, extensions `.epw` (211), `.fwt` (197),
`.wea` (51). No `.PRN` under `Program Files\IES`.

A conversion will therefore be necessary, and it will have to honestly handle
the vertical irradiance columns that `.epw` does not provide in the same
location. **To be verified before purchase, not after.**

---

## 4. What has been unblocked and is no longer an obstacle

- **Test 4 setpoint (open point O1)** --- **CLOSED**. SIA 2024:2021 table 11
  gives for usage **4.04 Hoersaal: 21 degC / 26 degC**, identical to the
  reference group 1.01--3.03 (unanimously 21/26). **Zero** offset on both
  curves. Table 11 moreover distinguishes **no** level
  Standardwert/Zielwert/Grenzwert: the design temperature does not depend
  on the level specified by the specification.
- **Figure 1 of SIA 380/2 (open point O2)** --- **CLOSED**, exact values
  extracted from the vector drawing, residual < 0.001 degC. Limits 20.5->22.0 and
  24.5->26.5; breakpoints at 12 / 17.5 / 19 / 23.5; `delta-theta_ctr` = 0.700 K; constant
  setpoints 22.7 and 23.8. 8/8 concordance with SIA 180:2014 figure 4.
- **Usage-based offset rule** --- verified against **10 out of 10** values
  published by SIA 4010 §3.1.4, reproduced from table 11
  (`engine/tests/test_setpoint_curves.py`).
- **Test 1 climate** --- ISO source downloaded, frozen, fingerprint recalculated.
  The `.epw` temperature deployed in VE agrees across **8760 hours to
  0.000 K**, wind to 0.00 m/s.

---

## 5. Two warnings that will affect Test 1 results

Discovered by reading the ISO climate file itself, and not reported
until now in the dossier.

**5.1 Initialisation month.** The file states in clear text: "*ATTENTION: The
first month is for initialization only; these data are copied from the last
month = December*". 9504 lines = 8760 + 744. A VE simulation of
8760 hours starting from 1 January **does not reproduce the initial state** of
the reference programs. Maximum effect on high-mass cases --- **900, 940,
900FF**. VE preconditioning must reflect this month.

**5.2 Nature of the solar input.** The ISO file provides irradiance **already
computed** on eight named surfaces (NV, EV, SV, WV, N45, S45, VOID, H), without
global/direct/diffuse decomposition. The reference programs thus received a
surface irradiance. An `.epw` provides global/direct/diffuse and lets the
program's sky model derive the surfaces: **the input is not the same**. The
global horizontal already differs by **-0.9%** (1832 vs 1849 kWh/m2-yr).

This is the exact mechanism that makes EXCEL an *outlier* in Test 2 --- but in
the opposite direction: here it is the **references** that used the
pre-computed irradiance, and it is we who will recompute it.

**Recommended pre-check, cost one simulation**: run case 600, note the
annual incident irradiation on the **south** facade, compare with
**SV = 1547.1 kWh/m2-yr**. Deviation < 1% -> the sky model is not a
confounding factor. Deviation of several percent -> any subsequent thermal
deviation is explained first by that, and not by VE's thermal engine.

Frozen annual reference irradiation, kWh/m2-yr:

| NV | EV | SV | WV | N45 | S45 | H |
|---|---|---|---|---|---|---|
| 429.7 | 1150.0 | 1547.1 | 1046.6 | 853.5 | 2239.8 | 1848.5 |

---

## 6. Shortest path to the first signed class

1. **Purchase** the SIA 2028 "Gegenwart" dataset, station **Zurich-Kloten**.
   Reference when ordering: the file must be named `KLO_dry_normal` and
   **carry no year** --- neither 2035, nor 2060, nor `RCP`.
2. **Verify** that conversion to a VE-readable format (`.epw` or
   `.fwt`) preserves the hourly temperature, and document what becomes of the
   vertical irradiance.
3. **Class 5 first**: Test 7 only, no building model, profiles
   provided. It is the only class achievable with this single input.
4. Then **class 1A**, which only adds Test 1 (already ready on the climate side)
   and Test 2A.

**Free downloads to carry out in parallel**, without which classes 3,
4A and 4B will remain blocked even once the weather data is acquired:

- SIA 2024 usage sheets **3.1, 3.2, 3.3, 4.4, 6.2, 6.4** ---
  `https://www.sia.ch/de/cms/dienstleistungen/normenundordnungen?item=15143#15152`
  (online version already post-corrigenda, according to SIA);
- **SIA 2024 and SIA 180 corrigenda** --- our tables 11 and 13 and comfort
  criteria carry `controle_effectue: false`;
- **SIA 2028/C2:2023 table 10** and the "Anwendungsempfehlungen".

---

## 7. What remains unverified

- The **2023** edition of SIA 387/4 table 9 (we have **2017**) --- blocks
  class 4B only.
- **SN EN 15316-2:2017**, which defines `delta-theta_ctr`: 0.700 K is the *drawn* value
  from figure 1, not a value whose scope we know.
- **SN EN ISO 52120-1:2022 table 5**: without it, we cannot tell whether VE
  controls fall under constant or variable setpoints.
- **EN ISO 52016-1 §6.5.5**: operative temperature weighting, quantified
  deviation of 0.174 K between the two possible interpretations.
- The **number of out-of-band classes** triggering failure --- open question to
  the SIA sub-commission, along with three others.

_Established 2026-08-05. Sources: SIA 4010:2023 tab. 63 and §3.1.4; SIA 380/2:2022
§5.2.2.x; the seven `Spezifikation_TestN.pdf` files; the application reports of the
four reference programs; `Lastverlaeufe_220607.xlsx`; the public climate file
from EN ISO 52016-1; the VE 2025 weather library._
