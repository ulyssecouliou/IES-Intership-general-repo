> **Note:** Translated from French original. See [test-1.spec.md](test-1.spec.md) for the source document.

# Spec --- SIA 4010 Test No. 1: Building Envelope Baseline Tests

> Status: **SPEC FROZEN** on the input model (revised 2026-07-31 --- see §10).
> The SIA specification for Test 1 is in the repository, read and verified verbatim.
> **Resolved 2026-07-31**: the **numerical values for constructions, glazing
> and infiltration** --- direct reading from `BS EN ISO 52016-1:2017` §7.2
> (pp. 122--134), which **reproduces** these values. They are now authoritative in
> `traceability/iso-52016-1-ch7-valeurs.spec.md`, with clause citation for
> each quantity. §4 of this document remains as historical record.
>
> **2017 vs 2023 caveat lifted**: ISO 52016-1:2017 cites **ASHRAE 140 of 2014**.
> The ASHRAE 140:**2023** copy in `/refs` carries later revisions and is
> therefore **not** the target of Test 1 (its Table 7-11 itself notes
> "*Updates to Standard 140-2017 are highlighted in bold*"). The external
> surface coefficient is now read from **table 25 of ISO 52016-1** (h_ce = 20,
> h_lr;e = 4.14 W/(m2-K)), and no longer from Table 7-7 of ASHRAE 140:2023 ---
> the two follow different conventions and must not be mixed.
>
> Sources in hand:
> - `refs/SIA-4010-2023.pdf` --- SIA 4010:2023 full text, read and verified.
> - `refs/SIA-380-2-2022.pdf` --- SIA 380/2:2022 full text (not re-read in detail for this test).
> - `SIA_4010_geteilter_Link/Test1/Spezifikation_Test1.pdf` --- **official Test 1
>   specification (German), read in full and verified (2 pages)**.
> - `SIA_4010_geteilter_Link/Test1/Anwenderberichte/` --- 4 application reports from
>   reference programs (EnergyPlus, IDA-ICE, TAS, EXCEL 52016-1), read.
> - `ASHRAE 140_2023_D_86892.pdf` --- **full text read this session via extraction**
>   (see verification box below). Sections 7.2.1.9.3, Table 7-7, Table 7-2,
>   Table 7-27 and §7.2.2.2.x verified verbatim.
>
> - **`BS EN ISO 52016-1:2017` §7.2, pages 122 to 134 --- READ on 2026-07-31.** The
>   "table 27" cited by SIA 4010 is the **list of six test cases**
>   (600, 640, 900, 940, 600FF, 900FF), not a table of values. Tables 28 through
>   34 of this standard **are** the `Daten EN ISO 52016-1 2017` column of the SIA
>   workbook --- verified by direct cross-check (600FF: max 63.5 / min -16.9).
> - `SIA_4010_geteilter_Link/Test1/Resultaterfassung_Test1.xlsx` --- present and
>   audited (`AUDIT.md`, "KEEP --- SIGNED", pass 4).
>
> Sources still absent, but **no longer blocking for Test 1**:
> - `NREL/TP-472-6231` (BESTEST 1995) and `ASHRAE 140-2014`: ISO 52016-1 §7.2 is
>   self-sufficient.
> - Annex E of ISO 52016-1 (pp. 176--183), window treatment: not captured,
>   not needed for unblocking.
> Provenance of each element: `[SIA4010]` = SIA 4010:2023 verified / `[SpezT1]` =
> Test 1 specification verified / `[AnwT1]` = Test 1 application report verified /
> `[ASHRAE140:2023]` = ASHRAE 140:2023 verified verbatim on text extraction this
> session / `[STD]` = standard knowledge to be confirmed / `[REQUIS]` = value to be obtained
> from a source still absent/unreadable.

> ---
> ## VERIFICATION --- SESSION 2026-07-30 #1 (norm-analyst)
> - **`Spezifikation_Test1.pdf` read in full** (without the `pages` parameter). All
>   `[SpezT1]` citations are verified verbatim.
> - **All 4 Test 1 Anwenderberichte read**: identify the reference programs
>   (basis for case 1E range criterion) and confirm the weather file.
> - **MAJOR CORRECTION to §6**: the assumption of a uniform min-max criterion for all
>   cases is **FALSE**. No deviation criterion for 600/640/900/940/600FF/900FF;
>   **only case 1E** has a real pass/fail criterion. Details in §6.
> ---
> ## VERIFICATION --- SESSION 2026-07-30 #2 (norm-analyst)
> - **`ASHRAE 140_2023_D_86892.pdf` READ this session.** The PDF (26 MB) exceeds the
>   Read tool limit and its text streams are compressed (Grep inoperable). **Method**:
>   the orchestrator extracted the full text via `pdftotext` (Bash tool, **outside
>   my own tools**; extraction done by the orchestrator, not by me) to the plain text
>   file:
>   `C:\Users\ulysse.couliou\.claude\jobs\d1486f24\tmp\ashrae140.txt` (27,379 lines).
>   I re-read this `.txt` myself and **verified each number / each quoted sentence** at
>   the following locations (line numbers from the `.txt`):
>   - Table 7-7 (ll. 2999--3019) --- external surface coefficients Case 600.
>   - §7.2.1.9.3 (ll. 3021--3057) --- convective-only vs combined selection procedure.
>   - Informative Note 900-series (ll. 4363--4368) + §7.2.2.2.1.1 (ll. 4373--4376).
>   - Table 7-2 (ll. 2774--2801) and Table 7-27 (ll. 4386--4418) --- material properties.
>   - Informative tables 7-3 (ll. 2820--2847) and 7-28 (ll. 4468+) --- calculated conductances.
> - **Limitation of the extraction method**: `pdftotext` does **not** preserve bold
>   formatting. Yet note a of Table 7-7 says "Changes to Standard 140-2017 are
>   highlighted in bold". I therefore **cannot know** which values changed
>   between 2017 and 2023. Direct consequence addressed in §4.
> - **RESOLVED**: external heat transfer coefficient -> §3 and §8 pt 1.
> - **NOT resolved but better documented**: numerical construction values -> §4.
> ---

## 1. Purpose
Verify that the dynamic thermal simulation engine correctly reproduces
envelope physics (transmission, thermal inertia, solar gains through glazing,
infiltration, free-float temperature) on the ASHRAE 140 / EN ISO 52016-1 ch. 7
standardised test cell, in lightweight (Leichtbau) and heavyweight (Massivbau)
variants. No real technical system is involved: heating and cooling are modelled
by **ideal elements**. `[SIA4010]` `[SpezT1]`

## 2. Relevant validation classes
Test 1 is required in **all classes except class 5**. `[SIA4010 §4.5, tab. 63 --- confirmed]`

| Class | Required tests | Test 1 required? |
|---|---|---|
| 1A | 1 + 2A | Yes |
| 1B | 1 + 2 | Yes |
| 2A | 1, 2A, 3A--F | Yes |
| 2B | 1 to 3 | Yes |
| 3 | 1, 4 to 6 | Yes |
| 4A | 1, 2A, 3A--F, 4 to 7 | Yes |
| 4B | 1 to 7 | Yes |
| 5 | 7 | No |

Product consequence: Test 1 is the first to implement (vertical slice
Phase 1) because it conditions 7 of 8 classes.

## 3. Normative framework
- Test cell per **SN EN ISO 52016-1:2017, §7.2.2**, corresponding to
  **ASHRAE 140:2017**. `[SIA4010 §4.2 tab. 62; Annex A tab. 64, line 1 --- confirmed]`
  The Test 1 spec confirms: "Testraum gemaess ISO EN 52016:2017 (Basis ASHRAE 140:2017)".
  `[SpezT1 --- confirmed verbatim]`
- Scope: baseline cases per **EN ISO 52016-1:2017, chapter 7** ("Konstruktionen /
  Infiltration / Verglasung: ISO EN 52016:2017 Kapitel 7"). `[SpezT1 --- confirmed]`
  SIA 4010 tab. 64 (line 1) also mentions table 27 of EN ISO 52016-1 and the
  option to add supplementary ASHRAE 140 cases "if the desired aspects are
  not covered". `[SIA4010 tab. 64 --- confirmed]`
- Associated EPBD module: **M2-2**. `[SIA4010 tab. 64 --- confirmed]`

### 3.1 External heat transfer coefficient --- RESOLVED (session 2)
The question was inscribed by the standard itself in the "Comments" column of the
Test 1 line of table 64 ("Coefficient de transfert thermique externe?"), **not
settled** by SIA 4010 nor by the Test 1 spec nor by the Anwenderberichte. `[SIA4010 tab. 64 --- confirmed]`
It is **settled by the upstream source ASHRAE 140:2023**, the test cell's reference.

**Normative procedure** --- ASHRAE 140:2023 **§7.2.1.9.3** "Alternative Constant Convective
and Combined (Radiative and Convective) Surface Coefficients", verified verbatim
(`.txt` ll. 3021--3044): `[ASHRAE140:2023 §7.2.1.9.3 --- confirmed]`
- **(a)** If the software being tested computes **itself** the external convective
  coefficients **AND** infrared radiative exchange, both **variable at each time step**,
  then those calculations apply and Table 7-7 is **ignored** ("those calculations shall be
  applied; skip the remaining instructions").
- **(b)** Otherwise, Table 7-7 applies:
  - **(b.1)** software that computes time-variable IR exchange **but not** convective
    coefficients -> apply the **convective-only** coefficient `hconv,ext`.
  - **(b.2)** software that computes **neither** time-variable convection **nor** IR -> apply the
    **combined** coefficient `hcomb,ext`.
  - **(b.3)** other values (unspecified) are not forbidden if there exists a
    mathematical/physical/logical basis, applied consistently across all cases and
    documented in the Standard Output Report (Annex A2). `[ASHRAE140:2023 §7.2.1.9.3 --- confirmed]`

**Values --- Table 7-7** "Alternative Constant Exterior Convective and Combined Surface
Coefficients for Each Surface Type, Case 600", in **W/(m2-K)**, verified verbatim
(`.txt` ll. 2999--3012): `[ASHRAE140:2023 Table 7-7 --- confirmed]`

| Surface type | `hconv,ext` (convective only) | `hcomb,ext` (combined conv.+rad.) |
|---|---|---|
| Walls | **11.9** | **21.6** |
| Roof | **14.4** | **21.8** |
| Raised floor | **0.8** | **5.2** |
| Windows | **8.0** | **17.8** |

- These coefficients are **calculated for wind speed = 0** (note c of Table 7-7,
  `.txt` l. 3017: "Calculated for wind speed = 0 as described in Section 7.2.1.9").
  `[ASHRAE140:2023 Table 7-7 note c --- confirmed]`
- Note a of Table 7-7 (`.txt` l. 3015) states "Changes to Standard 140-2017 are
  highlighted in bold". **The text extraction does not preserve bold**: I therefore
  cannot know whether any of these values changed between ASHRAE 140:2017 (version cited by SIA
  4010) and 2023 (version in hand). Caveat to keep in mind; cf. §4. `[ASHRAE140:2023 --- confirmed, bold not exploitable]`

**Application to SIA Test 1 cases** --- Table 7-7 is defined for Case 600. It
applies **identically** to the heavyweight cases because **surface textures** (hence
surface coefficients) are **unchanged** between the 600-series and 900-series:
- Informative Note (`.txt` ll. 4363--4368): "For Cases 900 through 950 and 985, the
  high-mass cases are the same as the corresponding low-mass 600-series cases except that
  material properties are taken from Table 7-27 rather than Table 7-2 ... the roof properties
  **and all surface textures are unchanged**." `[ASHRAE140:2023 --- confirmed]`
- §7.2.2.2.1.1 (`.txt` ll. 4373--4376): "The surface textures of Sections 7.2.1.9.2 and
  7.2.1.10.2 (Case 600) **shall continue to apply**." `[ASHRAE140:2023 §7.2.2.2.1.1 --- confirmed]`
- Numerical confirmation: the informative conductance tables give the **same**
  exterior surface coefficient for wall (21.6), floor (5.2), roof (21.8) in the lightweight
  case (Table 7-3, `.txt` ll. 2830/2838/2846) **and** the heavyweight case (Table 7-28, `.txt` ll. 4478/4486).
  `[ASHRAE140:2023 Tables 7-3 & 7-28 --- confirmed]`
- Cases **640/940** (night setback) are modelled "exactly the same as" 600/900
  except for setpoints / materials (§7.2.2.2.5 for 940, `.txt` ll. 4457--4459): surface
  coefficients **unchanged**. `[ASHRAE140:2023 §7.2.2.2.5 --- confirmed]`
- **Interpretation (marked as such)**: cases **600FF / 900FF** (free-float)
  only modify the control regime (no setpoint), not the geometry or
  surface textures; Table 7-7 therefore applies **identically**. Not cross-checked
  line by line in the `.txt` but consistent with the logic "FF = same building without
  HVAC". To be confirmed if any doubt arises.

**Conclusion §3.1**: for the Test 1 cell (cases 600/640/600FF/900/940/900FF/1E), the
external surface coefficients are those of **Table 7-7**, zero wind, **the choice of
column (`hconv,ext` only vs `hcomb,ext` combined) depending on the software's algorithm**
per §7.2.1.9.3 (a)/(b). **The EXACT value to use for this project therefore depends on
the surface convection algorithm configured in ApacheSim/IESVE** (does it compute
time-variable convection? IR exchange?). This specific point is deferred to
`ve-adapter-engineer` --- cf. §8 pt 6. `[ASHRAE140:2023 §7.2.1.9.3 --- confirmed; ApacheSim interpretation not settled]`

## 4. Input quantities (test cell definition) `[SpezT1 --- confirmed]`
Single zone, **south** orientation (windows facing south).

**Site & weather**
- Site: **Denver, CO**.
- Weather file: **DRYCOLD.TMY (BESTEST) Denver, CO**, EN ISO 52010-1 dataset
  published with EN ISO 52016-1 (`http://standards.iso.org/iso/52016/-1/ed-1`). `[SpezT1]`
  Confirmed by the Anwenderberichte ("Klimadaten aus Original-Datei nach SN EN ISO
  52010-1 ... Denver, CO"). `[AnwT1]`
  Warning --- documentation note: two Anwenderberichte incorrectly label this climate "hot-dry"
  and one labels it "dry cold"; the SIA spec is authoritative = **DRYCOLD** (dry cold). `[SpezT1]`
- Simulation period: **1.1.2011 -- 31.12.2011** (full year). `[SpezT1]`

**Geometry** `[SpezT1, Figure 2]`
- Internal dimensions: **6.0 m x 8.0 m**, height **2.7 m**.
- Net area: **48 m2**.
- Two south-facing windows, **2.0 m x 3.0 m each** (positions dimensioned on Figure 2:
  sill heights 0.2 m / 0.5 m, mullions 0.5 m and 1.0 m).

**Constructions** `[SpezT1]`
- Variants **Leichtbau (lightweight)** and **Massivbau (heavyweight)** per EN ISO 52016-1 ch. 7.
- Numerical values (layer compositions, U-values, thermal capacities): **NOT given
  by the SIA spec** --- formal reference to **EN ISO 52016-1 ch. 7** (basis ASHRAE 140:2017).
  **Status: `[REQUIS]` --- remains open** (EN ISO 52016-1:2017 still absent from `/refs`).
- **Strong lead documented this session (presumed, NOT frozen)**: ASHRAE 140:2023
  provides these same material properties, verified verbatim:
  - **Table 7-2** "Fundamental Material Thermal Property Specifications Low-Mass Case"
    (`.txt` ll. 2774--2801) --- **lightweight** case: `[ASHRAE140:2023 Table 7-2 --- confirmed]`

    | Layer (interior -> exterior) | k [W/(m-K)] | th. [m] | U [W/(m2-K)] | R [m2-K/W] | rho [kg/m3] | cp [J/(kg-K)] |
    |---|---|---|---|---|---|---|
    | Wall --- Plasterboard | 0.16 | 0.012 | 13.333 | 0.075 | 950 | 840 |
    | Wall --- Fiberglass quilt | 0.04 | 0.066 | 0.606 | 1.650 | 12 | 840 |
    | Wall --- Wood siding | 0.14 | 0.009 | 15.556 | 0.064 | 530 | 900 |
    | Floor --- Timber flooring | 0.14 | 0.025 | 5.600 | 0.179 | 650 | 1200 |
    | Floor --- Insulation | 0.04 | 1.003 | 0.040 | 25.075 | 0 (a) | 0 (a) |
    | Roof --- Plasterboard | 0.16 | 0.010 | 16.000 | 0.063 | 950 | (see note) |
    | Roof --- Fiberglass quilt | 0.04 | 0.1118 | 0.358 | 2.794 | 12 | (see note) |
    | Roof --- Roofdeck | 0.14 | 0.019 | 7.368 | 0.136 | 530 | (see note) |

    (a) "Underfloor insulation has the minimum density and specific heat the program being
    tested will allow, but not < 0" (`.txt` l. 2801). The roof cp values are misaligned in
    the text extraction (column shifted ll. 2779--2786) --- **to be re-verified** against EN ISO
    52016-1 or a more reliable PDF reading before use. `[ASHRAE140:2023 --- confirmed except roof cp to re-verify]`
    - Confirms the `[AnwT1]` clue from the EXCEL report: floor insulated ~**1 m** (1.003 m lightweight).
  - **Table 7-27** "Fundamental Material Thermal Property Specification, High-Mass Case"
    (`.txt` ll. 4386--4418) --- **heavyweight** case: `[ASHRAE140:2023 Table 7-27 --- confirmed]`

    | Layer (interior -> exterior) | k [W/(m-K)] | th. [m] | U [W/(m2-K)] | R [m2-K/W] | rho [kg/m3] | cp [J/(kg-K)] |
    |---|---|---|---|---|---|---|
    | Wall --- Concrete Block | 0.51 | 0.100 | 5.100 | 0.196 | 1400 | 1000 |
    | Wall --- Foam Insulation | 0.04 | 0.0615 | 0.651 | 1.537 | 10 | 1400 |
    | Wall --- Wood Siding | 0.14 | 0.009 | 15.556 | 0.064 | 530 | 900 |
    | Floor --- Concrete Slab | 1.13 | 0.080 | 14.125 | 0.071 | 1400 | 1000 |
    | Floor --- Insulation | 0.04 | 1.007 | 0.040 | 25.175 | 0 (b) | 0 (b) |

    Roof **identical** to the lightweight case (note c, `.txt` l. 4418: "The high-mass case roof
    is the same as the low-mass case roof"). (a) floor insulation thickness slightly
    adjusted (1.007 m) to equalise total R-values. (b) density/cp set to minimum allowed, >= 0.
    `[ASHRAE140:2023 Table 7-27 --- confirmed]`

  - **TWO EXPLICIT CAVEATS --- why these values remain `[REQUIS]` and are not frozen:**
    1. **Version 2017 vs 2023**: SIA 4010 formally cites **EN ISO 52016-1:2017** (basis
       **ASHRAE 140:2017**). We only have in hand **ASHRAE 140:2023**. These tables are
       presumed equivalent but **not proven identical** to the cited source.
    2. **Bold not preserved**: note a of Table 7-7 (and by extension the 2023 document)
       states "Changes to Standard 140-2017 are highlighted in bold". The
       `pdftotext` extraction **erases bold**: it is impossible to know which values changed
       between 2017 and 2023. A 2023 figure may differ from the 2017 value actually targeted
       by SIA 4010.
    -> **These tables are a documented starting point with very high presumption, NOT
    proof.** To be confirmed against **EN ISO 52016-1:2017 tab. 27** (absent from `/refs`) before
    freezing. Status maintained at **`[REQUIS]`**. `[ASHRAE140:2023 --- presumption, to confirm vs EN ISO 52016-1:2017]`

**Glazing** `[SpezT1]`
- Per EN ISO 52016-1 ch. 7. Values (g, U, solar transmission) **NOT given** by
  the SIA spec --- reference to EN ISO 52016-1 ch. 7. `[REQUIS]`
  Note: ASHRAE 140:2023 §7 also documents the window (same 2017/2023 caveats
  as above); **not extracted/verified this session** --- to be addressed in a dedicated pass.

**Infiltration / ventilation** `[SpezT1]`
- Mechanical ventilation ("Lueftung"): **none** ("-").
- Infiltration: per EN ISO 52016-1 ch. 7. Numerical value (rate) **NOT given** by
  the SIA spec. `[REQUIS]` (ASHRAE 140:2023 §7 documents it; not extracted this session.)

**Solar protection** `[SpezT1]`
- **None** ("Ohne"), except case 1E (fabric blind, cf. §7).

**Internal gains** `[SpezT1 --- confirmed]`
- Occupants: **none** (Anzahl: Keine).
- Equipment: **200 W total**, **constant 24 h** profile, present **all year
  (1.1.--31.12.)**.
- Lighting: **0 W/m2**.

**Setpoints (ideal elements, no real HVAC --- "HLK-Anlage: Keine vorhanden")** `[SpezT1]`
- Heating: ideal element, setpoint **20 degC**.
  - Cases 640/940 (controlled night setback): **20 degC from 07:00 to 23:00**, **10 degC from 23:00
    to 07:00**.
- Cooling: ideal element, setpoint **27 degC**.

## 5. Controlled output quantities `[SpezT1 --- confirmed]`
Annual datasets to be transferred to **`Resultaterfassung_Test1.xlsx`**:
1. Cases **600, 640, 900, 940 and 1E**: hourly heating and cooling **power**.
2. **All cases except 1E**: hourly air **temperature** and hourly **operative
   temperature**.

Derived test results (automatically computed from the annual datasets):
1. Sensible heating energy, **monthly and annual** [kWh].
2. Sensible cooling energy, **monthly and annual** [kWh].
3. **Monthly means** of operative temperature.
4. Hourly heating/cooling demand for **4 January**.
5. Hourly heating/cooling demand for **27 July**.
6. **Maximum hourly** heating and cooling demands.
7. Hourly operative temperature **max / min / annual mean** --- cases **600FF and 900FF**.
8. Hourly operative temperature means for **4 January** --- cases **600FF and 900FF**.

## 6. Acceptance criterion / tolerance `[SpezT1 --- CORRECTED session 1]`
> Major correction: the former §6 assumed a uniform min-max criterion for all
> cases. **This is false.** The Test 1 spec ("Testkriterien" section) states literally:

- Cases **600, 640, 900, 940, 600FF and 900FF**: results are **displayed for
  comparison** with reference results. **"Es gibt dafuer kein
  Abweichungskriterium"** --- there is **NO deviation criterion** (no
  pass/fail). `[SpezT1 --- confirmed verbatim]`
- Case **1E** only: **"Resultate fuer den Test 1E muessen im Streubereich der
  enthaltenen Referenzprogramme liegen"** --- results **must fall within the
  dispersion range (Streubereich) of the included reference programs**. This is the
  **only real pass/fail criterion** of Test 1. `[SpezT1 --- confirmed verbatim]`

Reference programs included (basis for case 1E dispersion range), identified
from the Test 1 Anwenderberichte: `[AnwT1 --- confirmed]`
- **EnergyPlus 9.1.0 / OpenStudio**
- **IDA ICE 5.0 Beta 23**
- **TAS (EDSL)**
- **EXCEL SN EN ISO 52016-1** (E4Tech, SIA 2044 pre-study framework, completed by G. Zweifel)

-> Consequences for `engine/`:
- Do NOT implement a pass/fail test on 600/640/900/940/600FF/900FF: produce the
  **comparative display** vs reference, without verdict.
- Implement the **only** binary test on case **1E**: "value within [min, max] of
  reference programs" per controlled quantity. The bounds (min/max of the dispersion)
  come from `Resultaterfassung_Test1.xlsx`. `[REQUIS --- evaluation Excel absent]`
- Note: this "transfer to the Excel which generates the comparison" mode is consistent with
  SIA 4010 §2.5 and §4.4 (evaluation file on www.sia.ch/sia4010). `[SIA4010 --- confirmed]`

## 7. List of test cases `[SpezT1 --- confirmed]`
**Main cases** (per EN ISO 52016-1 ch. 7):
| Case | Construction | Regime |
|---|---|---|
| 600 | Leichtbau (lightweight) | heating 20 degC / cooling 27 degC |
| 640 | Leichtbau (lightweight) | night setback (20 degC 07--23 h / 10 degC 23--07 h) / cooling 27 degC |
| 600FF | Leichtbau (lightweight) | free-float |
| 900 | Massivbau (heavyweight) | heating 20 degC / cooling 27 degC |
| 940 | Massivbau (heavyweight) | night setback (20 degC 07--23 h / 10 degC 23--07 h) / cooling 27 degC |
| 900FF | Massivbau (heavyweight) | free-float |

**Additional case with criterion**:
| Case | Definition |
|---|---|
| 1E | **Diagnostic case 1D** + solar protection by **fabric blind (Stoffmarkise)** per **diagnostic test 2 E1**. Only case subject to a pass/fail criterion (§6). |

**Diagnostic cases (transition Test 1 -> Test 2)** --- results to deliver: annual datasets
with hourly heating/cooling power. `[SpezT1 --- confirmed]`
| Case | Definition |
|---|---|
| Diag 1A | Case 600 with **Zurich-Kloten climate data** |
| Diag 1B | Diag 1A + **new window** per Test 2 specification |
| Diag 1C | Diag 1B + **adjusted infiltration** per Test 2 specification |
| Diag 1D | Diag 1C + **usage (occupants/equipment/lighting) per SIA 2024**, cf. Test 2 specification |

-> Test 1 is therefore a **precise subset** (lightweight 600/640/600FF + heavyweight
900/940/900FF + 1E + diagnostics 1A--1D), **not** the entirety of the ASHRAE 140 suite.

## 8. Uncertainty zones (to be resolved before "done")
1. **External heat transfer coefficient** --- **RESOLVED** (session 2).
   Table 7-7 coefficients (zero wind); column choice per §7.2.1.9.3 (a)/(b).
   Cf. §3.1. **Still dependent** on the ApacheSim algorithm -> deferred to pt 6 below.
   `[ASHRAE140:2023 §7.2.1.9.3 + Table 7-7 --- confirmed]`
2. **Numerical construction values** (layers, U, capacities) lightweight/heavyweight.
   **Still `[REQUIS]`**: strong lead via ASHRAE 140:2023 Table 7-2 / 7-27 (§4) but
   **not frozen** (2017/2023 caveats + bold not preserved). To be confirmed vs EN ISO
   52016-1:2017 tab. 27 (absent from `/refs`).
3. **Glazing** (U, g, solar transmission). `[REQUIS --- EN ISO 52016-1 ch. 7 absent;
   also documented by ASHRAE 140:2023 §7 but not extracted this session]`
4. **Exact infiltration rate**. `[REQUIS --- same as pt 3]`
5. **Case 1E dispersion bounds** (min/max of reference programs, per quantity).
   `[REQUIS --- Resultaterfassung_Test1.xlsx absent]`
6. **ApacheSim/VE settings** --- **POINT CLARIFIED (session 2)**:
   - Determine whether ApacheSim/IESVE's external surface convection model computes
     **time-variable** convection and/or **time-variable IR** exchange -> this
     decides, via ASHRAE 140:2023 §7.2.1.9.3, which branch applies:
     - time-variable convection + IR computed -> let ApacheSim handle it (branch a);
     - time-variable IR only -> force `hconv,ext` (11.9 / 14.4 / 0.8 / 8.0);
     - neither -> force `hcomb,ext` (21.6 / 21.8 / 5.2 / 17.8).
   - Verify that the retained value/mode is applied **consistently** across all
     cases and documented (requirement §7.2.1.9.3 b.3).
   - Other cell conventions to frame: interior solar radiation distribution
     (internal reflectance 0.4 noted by IDA-ICE `[AnwT1]`), ground coupling through the
     ~1 m insulated floor (zero-wind assumption / air under floor = ambient, ASHRAE 140:2023
     Informative Note ll. 2803--2812).
   -> **To be framed with `ve-adapter-engineer`.** `[ASHRAE140:2023 --- framework confirmed; ApacheSim settings to be determined]`

**Points now RESOLVED** (removed from uncertainties):
- External heat transfer coefficient -> §3.1 (session 2). `[ASHRAE140:2023]`
- Exact scope of cases -> §7. `[SpezT1]`
- Reference weather file -> DRYCOLD.TMY (BESTEST) Denver, period 2011. `[SpezT1]`
- Acceptance criterion structure -> §6 (no criterion for baseline cases, dispersion
  range for 1E only). `[SpezT1]`
- Geometry, internal gains, setpoints -> §4. `[SpezT1]`

Non-blocking point confirmed: the "example building" (DXF/IFC + loads) from SIA 4010 §4.3
is used **only for tests 4 to 7** --- no effect on Test 1.

## 9. Citations
> SIA 4010: full reading of `refs/SIA-4010-2023.pdf`. Test 1 specification:
> full reading of `SIA_4010_geteilter_Link/Test1/Spezifikation_Test1.pdf` (2 pages).
> Anwenderberichte: 4 Test 1 PDFs read. ASHRAE 140:2023: read this session via text
> extraction (`pdftotext`, by the orchestrator; `.txt` file re-read and verified by me).
> EN ISO 52016-1:2017: still absent from `/refs` --- not verifiable.
- SIA 4010:2023: §2.5, §4.2 tab. 62, §4.3, §4.4, §4.5 tab. 63, Annex A tab. 64 line 1
  (incl. open question "external heat transfer coefficient"). --- **confirmed**.
- `Spezifikation_Test1.pdf` (SIA 4010 Test 1): Standort/Klima/Simulationsperiode,
  Gebaeude & Figure 2 (geometry), Raum (constructions, infiltration, Waermeabgabe,
  Kaelteabgabe, Waermeeintraege, Verglasung, Sonnenschutz, HLK), Testfaelle, Zu liefernde
  Resultate, Testresulate, **Testkriterien**, Diagnosefaelle. --- **confirmed verbatim**.
- Anwenderberichte Test 1: EnergyPlus 9.1.0/OpenStudio, IDA ICE 5.0 Beta 23, TAS (EDSL),
  EXCEL SN EN ISO 52016-1 (E4Tech/Zweifel). --- **confirmed** (reference programs, weather).
- **ASHRAE 140:2023** (`ASHRAE 140_2023_D_86892.pdf`, via text extraction
  `C:\Users\ulysse.couliou\.claude\jobs\d1486f24\tmp\ashrae140.txt`):
  §7.2.1.9.3, Table 7-7 (+ notes a and c), Informative Note 900-series, §7.2.2.2.1.1,
  §7.2.2.2.5, Table 7-2, Table 7-27, Informative Tables 7-3 & 7-28. --- **confirmed
  verbatim**; caveats: roof cp (Table 7-2) misaligned, to be re-verified; bold (2017<->2023
  deltas) not preserved by extraction.
- EN ISO 52016-1:2017 §7.2.2, ch. 7 (tab. 27): *absent from `/refs` --- not verifiable*.
  This is the source formally cited by SIA 4010 for §4 values; its absence
  keeps those values at `[REQUIS]` despite the ASHRAE 140:2023 lead.

## 10. Path from DRAFT to SPEC FROZEN
- [x] Test 1 specification read and verified (`Spezifikation_Test1.pdf`).
- [x] Acceptance criterion structure corrected and frozen (§6).
- [x] List of cases, weather, geometry, gains, setpoints frozen (§4, §7).
- [x] **External heat transfer coefficient settled** (ASHRAE 140:2023 §7.2.1.9.3
      + Table 7-7, §3.1) --- still to be translated into a concrete ApacheSim setting (§8 pt 6,
      `ve-adapter-engineer`).
- [x] Numerical construction/glazing/infiltration values **confirmed vs EN ISO
      52016-1:2017 ch. 7** --- **RESOLVED 2026-07-31** by direct reading of
      pages 122 to 134 of `BS EN ISO 52016-1:2017` §7.2. The chapter **reproduces**
      the values rather than referring to ASHRAE 140. Everything is recorded in
      `traceability/iso-52016-1-ch7-valeurs.spec.md`: geometry (tab. 22),
      lightweight and heavyweight constructions layer by layer (tab. 23 and 24), glazing
      (§7.2.2.6: **U_W = 2.984 W/(m2-K)**, g_gl;n = 0.789, R_se;v = 0.04,
      R_si;v = 0.13, F_fr = 0), surface coefficients (tab. 25), infiltration
      (**0.41 h^-1 continuous**, no ventilation system), internal gains
      (200 W continuous), setpoints (20/27 continuous; 10/27 at night for
      intermittent), alpha_sol, F_sky, convective fractions, capacities.
      The **2017 vs 2023 caveat is lifted**: the copy cites **ASHRAE 140 of
      2014**, so the ASHRAE 140:2023 values from `/refs` are NOT the target ---
      they carry later revisions. The "table 27" cited by
      SIA 4010 is the **list of six test cases**, not a table of values.
- [x] Case 1E dispersion bounds (`Resultaterfassung_Test1.xlsx`) --- extracted
      and audited (`AUDIT.md`, verdict "KEEP --- SIGNED", pass 3), then
      completed by Table 31 in pass 4.

> Status decision, revised **2026-07-31**: **SPEC FROZEN** on the input model.
> All six boxes of this path are checked. `BS EN ISO 52016-1:2017` §7.2
> was read directly (pp. 122--134) and **reproduces** all physical values:
> the Test 1 input model is now fully defined, with clause citation for
> each quantity.
>
> Two caveats from this document are **moot**: the ASHRAE 140:2023 lead is
> no longer needed (ISO is self-sufficient), and the 2017 vs 2023 question
> is settled --- ISO 52016-1:2017 cites **ASHRAE 140 of 2014**, so the 2023
> copy in `/refs` carries later revisions and is **not** the target. §4 of this
> document remains valid as historical record, but
> `iso-52016-1-ch7-valeurs.spec.md` is now authoritative on the values.
>
> What remains open no longer concerns the input model but its **execution**:
> the ApacheSim setting corresponding to the table 25 coefficients (§8 pt 6),
> the IESVE variable to bind for operative temperature
> (`traceability/temperature-operative.spec.md`), and the six cases still to
> be generated and simulated.
