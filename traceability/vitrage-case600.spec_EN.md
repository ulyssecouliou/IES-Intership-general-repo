> **Note:** Translated from French original. See [vitrage-case600.spec.md] for the source document.

# Case 600 Glazing — normative value & EN ISO 52016-1:2017 request

> Status: **NORMATIVE ANALYSIS NOTE** — appendix to `traceability/test-1.spec.md` §4
> ("Vitrage") and §8 pt 3. Does not freeze any value.
> Author: `norm-analyst`. Date: 2026-07-31.
> Marking convention: **[V]** = verified in a cited source with file + line;
> **[I]** = inferred / calculated by me from verified sources; **[?]** = not
> verifiable with the sources at hand.

## Sources actually read for this note

| Source | Path | Status |
|---|---|---|
| ASHRAE 140:2023 (extracted text) | `C:\Users\ulysse.couliou\.claude\jobs\d1486f24\tmp\ashrae140.txt` | read, l. 2975-3420 verified line by line |
| SIA Test 1 specification (extracted text) | `…\scratchpad\norme\spec_test1.txt` | read in full (123 l.) |
| SIA 4010:2023 (extracted text, FR) | `…\scratchpad\norme\sia_4010_2023.txt` | targeted searches "52016", "ASHRAE" |
| SIA 380/2:2022 (extracted text, FR) | `…\scratchpad\norme\sia_380_2_2022.txt` | targeted searches "52016" |
| VE asset manifest | `C:\Users\ulysse.couliou\Documents\switzerland\SIA4010_Test1_Case600\reference_model_assets.json` | read in full |
| VE config | `…\SIA4010_Test1_Case600\reference_model_config.json` | l. 1-145 read |
| SIA case manifest (`test` variant) | `C:\Users\ulysse.couliou\Documents\switzerland\test\sia4010_case_manifest.json` | block `iso_test1_glazing`, l. 522-548 |
| QA results from the failed run | `…\SIA4010_Test1_Case600\reference_model_artifacts\reports\excel_ready\validation_results.csv` | l. 25-30 |
| IESVE API surface | `C:\Users\ulysse.couliou\Documents\SIA_Compliance_Scripts\ve_adapter\ve_api_surface.json` | l. 5948-5973, 8139-8162 |

**Sources MISSING from `/refs` — therefore nothing depending on them is verified:**
- **EN ISO 52016-1:2017** (full text, ch. 7, table 27) — the only source
  *formally* cited by SIA for the glazing. → Part B.
- **ASHRAE 140:2017** — the edition explicitly named as the basis by the SIA specification.
- **NREL/TP-472-6231 (BESTEST 1995), Part I, Tables 1-7 and 1-8** — source cited by
  `reference_model_assets.json` and `reference_model_config.json` for **all**
  glazing values (3.0 / 0.789 / 0.86156 / 1.06 / 6.297 / 0.003175 / 0.013).
  **This document is not in `/refs`. None of these values is therefore verified**,
  per CLAUDE.md rule 1. They are only *internally consistent* (demonstrated
  in A.3).

---

# PART A — What value for the Case 600 glazing?

## A.0 Verdict

1. **The question "3.0 or 2.10?" is undecidable with the sources at hand.** It can
   only be settled by EN ISO 52016-1:2017 ch. 7 (or, failing that, ASHRAE 140:2017).
   This is the direct justification for Part B. **[V/I — high confidence]**
2. **But the question posed to the model is itself ill-posed.** In ASHRAE 140:2023 — the only
   edition at hand — **the window is NOT specified by a U-value**. The normative reference is
   **Table 7-10 ("Normative Table 7-10")**: layers, thicknesses, lambda, rho, cp, gas,
   emittance, optics per pane. The U-value 2.10 is in an **informative table** and the
   standard says **explicitly** that it **must** vary from one software to another.
   **[V — very high confidence, ashrae140.txt l. 3169, 3174-3186, 3294]**
3. **Immediate and actionable consequence: the `VE-THERM-004` check is ill-specified.**
   Comparing a U reported by the CDB to a tabulated U, with an absolute tolerance of
   0.005 W/(m²K), contradicts the source standard itself. This check must be replaced
   by a check **on the layers**, or made **explicit about the surface resistance
   convention**. **[I — high confidence]**
4. **The 3.0 → 2.917 discrepancy is NOT a "different glass"**: it is a model plumbing
   problem. Three hypotheses remain open (A.6) and none can be settled without probing
   VE. The commissioner's "surface resistance convention" hypothesis is plausible but
   **not the only contender**. **[I — medium-high confidence]**
5. **DO NOT calibrate the layers to reach 3.0.** This would engrave in the model a value
   whose very source is absent from the repository.

## A.1 Independent verification of Table 7-11 (column offset)

The commissioner's reading is **CONFIRMÉ**, with one clarification: `ho` = 17.8
(exterior) and `hi` = 4.5 (interior). The `pdftotext` offset concerns the vertical
alignment, not the **order**: 9 labels, 9 values, order preserved.

Restored mapping (`ashrae140.txt` l. 3294-3313) and **cross-proof for each line**:

| # | Label (l. 3296-3312) | Value | Independent proof |
|---|---|---|---|
| 1 | Effective conductance of air gap (hs) | 5,208 W/(m²K) [R 0.19200] | note b (l. 3315): 0.0625/0.012 = **5.2083** ✔ |
| 2 | Conductance of each glass pane | 328 W/(m²K) [R 0.00305] | note c (l. 3318): 1.00/0.003048 = **328.08** ✔ |
| 3 | **Exterior** combined surface coeff. (ho) | 17.8 W/(m²K) [R 0.05618] | **Table 7-7, l. 3012**: Windows, hcomb,ext = **17.8** ✔; 1/17.8 = 0.05618 ✔ |
| 4 | **Interior** combined surface coeff. (hi) | 4.5 W/(m²K) [R 0.22222] | **Table 7-9, l. 3091**: Windows, hcomb,int = **4.5** ✔; 1/4.5 = 0.22222 ✔ |
| 5 | U-factor from interior air to ambient air | 2.10 W/(m²K) [R 0.47650] | note e (l. 3320): 0.192+2×0.00305+0.05618+0.22222 = **0.47650** → U = **2.0986** ✔ |
| 6 | Double-pane SHGC | 0.769 at normal incidence | **Table 7-12, l. 3338**: angle 0° → SHGC **0.769** ✔ |
| 7 | Double-pane shading coefficient (SC) | 0.883 at normal incidence | note h (l. 3327): SC = SHGC/0.87 = 0.769/0.87 = **0.8839** ✔ |
| 8 | Index of refraction | 1.493 | — (plausible soda-lime glass) |
| 9 | Extinction coefficient | 0.0337/mm | — |

Additional proof for the (ho, hi) pair: at l. 3833-3834, in the case 660 table,
the same labels are **correctly aligned** by the extraction and yield
`ho = 17.8 [R 0.05618]` / `hi = 4.5 [R 0.22222]`. **[V — very high confidence]**

> ⚠ Methodological note: the same kind of offset exists at l. 5083-5086 (summary
> appendix), where `hi` and `ho` are **swapped** compared to 3833-3834. Never
> read a table from this PDF without arithmetic cross-checking.

## A.2 What is NORMATIVE, in ASHRAE 140:2023, for the Case 600 window

Three decisive quotations, verified word for word:

- **§7.2.1.11.2 "Window Properties"** (l. 3169):
  "**The properties of the window provided in Table 7-10 shall be applied.**"
  → The normative reference is **Table 7-10**: 2 panes, **3.048 mm**, lambda glass **1.00 W/(m·K)**,
  air gap **12.0 mm**, rho 2470, cp 750, IR emittance 0.840, direct transmittance per
  pane **0.834** and reflectance **0.075** at normal incidence (l. 3218-3267). **[V]**
- **Informative Note 1 of §7.2.1.11.2** (l. 3174-3176):
  "Informative Table 7-11 includes calculated values derived from fundamental properties
  of **Normative Table 7-10** and alternative constant surface coefficients of Sections
  7.2.1.9.3 and 7.2.1.10.3, **for programs that may need this information**." **[V]**
- **Informative Notes 2 and 3** (l. 3178-3186) — the crucial point:
  - "For programs that calculate time-step varying surface infrared radiative exchange
    or convective coefficients or both, … **variation … may be expected: individual
    surface coefficient U-factors, air gap effective conductance, and overall U-factors.**"
  - "For programs that automatically calculate heat transfer within an air space or empty
    cavity, **variation … may be expected: effective air gap conductance and overall
    U-factor.**" **[V]**

**Reading (interpretation, marked as such):** the standard *anticipates and explicitly
authorises* that a software such as ApacheSim reports a glazing U different from the
tabulated U, precisely because of (i) surface coefficients and (ii) air gap conductance.
**Imposing a tolerance of 0.005 W/(m²K) on the glazing U is therefore contrary to the
instruction of the source standard.** The normative criterion bears on the **layers**, not on
the U. **[I — very high confidence]**

## A.3 The three values: provenance and arithmetic

### a) 3.0 W/(m²K) — the "BESTEST 1995" set
Declared in `reference_model_config.json` l. 124-128 (`project_window_u_w_m2k` = 3.0) and
`reference_model_assets.json` l. 1336-1432. The full set is readable in
`C:\Users\ulysse.couliou\Documents\switzerland\test\sia4010_case_manifest.json`
l. 531-547: 2 panes, **3.175 mm**, air gap **13 mm**, air gap conductance **6.297 W/(m²K)**,
lambda glass **1.06 W/(m·K)**, rho 2500, cp 750, epsilon 0.9, tau_pane **0.86156**, **U 3.0**,
**SHGC 0.789**, **SC 0.907**. **[V — the file does say this]**

**Internal consistency of the set (my calculation, [I]):**
- R_pane = 0.003175/1.06 = 0.0029953; two panes = **0.0059906**
- R_gap = 1/6.297 = **0.15880578** — **exactly** the value recorded in
  `reference_model_assets.json` l. 1412 (`0.1588057805304113`). ✔
- R_assembly (surface to surface) = **0.1647964** → **U_ss = 6.068 W/(m²K)**
- To obtain U = 3.000, R_total = 0.333333 is needed, hence film resistances of **0.168537 m²K/W**
  (≈ Rsi 0.1206 [hi = 8.29] + Rse 0.0479 [he ≈ 20.9]).
- SC 0.907 = 0.789/0.87 → same relation as note h of ASHRAE 140. ✔

→ **The "1995" set is arithmetically consistent and complete.** But its source
(NREL/TP-472-6231) **is not in `/refs`**: I cannot certify a single one of its
numbers, nor the surface coefficient values that produce the 3.0. **[?]**

### b) 2.10 W/(m²K) — the "ASHRAE 140:2023" set
- R_assembly = 2×(0.003048/1.00) + 1/5.2083 = 0.006096 + 0.192000 = **0.198096**
  → **U_ss = 5.048 W/(m²K)**
- + BESTEST window films (1/17.8 + 1/4.5 = 0.278402) → R = 0.476498
  → **U = 2.0986 ≈ 2.10** ✔ **[V+I — very high confidence]**

### c) 2.917 W/(m²K) — what the VE CDB reports
`validation_results.csv` l. 28: `cdb_w_m2k = 2.917067766189575`, `declared_w_m2k = 3.0`,
`qa_tolerance_w_m2k = 0.005`, `tolerance_is_regulatory = false`. **[V]**
→ R_total(VE) = **0.3428100 m²K/W**, i.e. **ΔR = +0.0094767** compared to the declared 3.0.

### Comparative table — the "convention" effect and the "glass" effect are of the same order

| Assembly | R glass+gap | + BESTEST 1995 window films (0.1685) | + ISO 6946 films (0.13+0.04) | + ASHRAE 140 window films (0.2784) |
|---|---|---|---|---|
| 1995 set (3.175 mm, lambda 1.06, gap 6.297) | 0.16480 → **6.068** | **3.003** | 2.982 | 2.256 |
| 2023 set (3.048 mm, lambda 1.00, gap 5.208) | 0.19810 → **5.048** | 2.745 | 2.717 | **2.099** |

(Calculations [I], based on [V] numbers from Table 7-10/7-11 and the manifest.)

**Takeaway:** changing the film convention shifts the U from **2.10 → 3.00**, i.e.
more than changing the glass. The U alone therefore discriminates **nothing**; it becomes
meaningful only if the film convention is declared alongside it.

## A.4 Answer to question 2 — "Is 2.10 truly an air-to-air U? What should it be compared to?"

**Yes, films included on both sides.** The label (l. 3304) is "U-factor from **interior
air to ambient air**" and the note e formula (l. 3320) explicitly sums
`1/hi` and `1/ho`. **[V — very high confidence]**

**But these films are specific to the test suite**: 17.8 / 4.5 are the
"alternative constant" values from Tables 7-7 / 7-9, applicable **only** when the
software does not calculate either variable convection or variable IR at each time step
(§7.2.1.9.3 / §7.2.1.10.3 branch b.2, already settled in `test-1.spec.md` §3.1).
They correspond to **no** generic standardised convention. **[V]**

**Consequence for IESVE:**
- `VECdbConstruction` exposes `get_u_factor`, `get_default_resistances`, `get_layers`,
  `get_g_values` (`ve_api_surface.json` l. 5948-5973) and the enumeration
  `uvalue_types` = **{ ashrae, cibse, iso, t24 }** (l. 8139-8162). **[V]**
- There is **no** `uvalue_types` value corresponding to the 17.8 / 4.5 films.
  Therefore **there is no IESVE quantity to which 2.10 can be directly compared** —
  nor 3.0. **[I — high confidence]**
- The only comparable quantity without convention is the **surface-to-surface U**
  (glass + gap only): **6.068** for the 1995 set, **5.048** for the 2023 set.
  → **Action for `ve-adapter-engineer`:** verify whether VE can return a U without films, and
  record `get_default_resistances()` + `get_u_factor()` for **each** of the 4
  `uvalue_types` values. Those 4 numbers, side by side, quantify the convention effect and
  will close the debate in a single execution. **[recommendation, non-normative]**

## A.5 Answer to question 3 — g = 0.789 vs SHGC = 0.769

These are **the same physical quantity** (solar factor at normal incidence, bare
double glazing) from **two different window specifications**:

| | 1995 set (in the model) | 2023 set (Table 7-10/7-11/7-12) |
|---|---|---|
| Solar transmittance **per pane**, normal incidence | 0.86156 | **0.834** (l. 3265) |
| Reflectance per pane | not declared | **0.075** (l. 3267) |
| Double-pane SHGC, normal incidence | **0.789** | **0.769** (l. 3304, l. 3338) |
| Double-pane SC | **0.907** (= 0.789/0.87) | **0.883** (= 0.769/0.87, l. 3305) |
| Air-to-air U | 3.0 | 2.10 |
| Lambda glass / thickness / gap | 1.06 / 3.175 mm / 13 mm | 1.00 / 3.048 mm / 12.0 mm |

**These are therefore not different quantities: they are two different editions.**
Both sets are each **internally consistent** (relation SC = SHGC/0.87 verified in
both). **Mixing them is forbidden**: taking U from one and g from the other
would produce a window that exists in no standard. **[I — very high confidence]**

The current model is **entirely within the 1995 set** (lambda 1.06; 0.86156; 0.789; 6.297).
It is therefore **at least consistent**. The only open question is: *is this the right
edition?*

## A.6 Diagnosis of the 2.917 — three hypotheses, none settled

**Traceability deficiency noted first:** in `reference_model_assets.json`, the two
glass layers of `external_glazing` (l. 1401-1406 and l. 1427-1431) have
`"properties": {}` — **no thickness is declared**. The 3.175 mm appears only in
`sia4010_case_manifest.json` l. 534, which does not feed this asset package. Furthermore,
a log from a prior iteration shows VE returning a glass layer thickness of
**0.0 m** (`…\SWISSG\reference_model_artifacts\logs\reference_model.log` l. 130:
"requested glazed thickness=0.024 m, VE read-back=0.0 m"). **[V]**
→ **The CDB U is not reproducible from the declared inputs.** The `VE-THERM-004` check
therefore compares two numbers, one of which has no traceable derivation.

Given ΔR = +0.0094767 m²K/W, three causes are each sufficient, alone or in combination:

| Hyp. | Cause | Required value | Plausibility |
|---|---|---|---|
| **H1** | VE surface resistance convention ≠ implicit films of the 3.0 | VE films = **0.178014** instead of 0.168537 | strong — this is exactly what Note 2 of §7.2.1.11.2 announces |
| **H2** | VE recalculates the air gap instead of using the declared R | air gap conductance **≈ 5.94** instead of 6.297 | strong — exactly Note 3 of §7.2.1.11.2 |
| **H3** | Undeclared pane thickness → VE default | ≈ **8.2 mm per pane** (if sole cause) | weak alone, but not excluded in combination |

**None can be distinguished analytically**: one equation (U = 2.917), three
unknowns. **[I — high confidence in the reasoning, no conclusion on the cause]**

**Convention signature visible also on opaques** (`validation_results.csv` l. 25-27,
all PASS): wall 0.514 declared / **0.51039** CDB; roof 0.318 / **0.31916**; floor
0.039 / **0.039272**. The same bias exists everywhere; it only causes failure for the glazing.
Arithmetic reason: the **absolute** tolerance of 0.005 W/(m²K) represents **0.97 %** for a wall
at 0.514 but **0.17 %** for a window at 3.0 — i.e. a criterion **6 times more stringent** on
the component most sensitive to conventions. **The QA rule itself is poorly
calibrated.** **[I — high confidence]**

## A.7 What to do — and what not to do

**Do not do:**
- ❌ Calibrate thickness / lambda / R of gap to match 3.0 (or 2.10). Forbidden:
  this would engrave a value whose source is not in `/refs`.
- ❌ Replace 3.0 with 2.10 "because it's the most recent standard". The SIA spec
  refers to the **2017** edition, not 2023, nor 1995.
- ❌ Mix sets (U 2.10 + g 0.789, or lambda 1.06 + tau 0.834).

**Do, in this order:**
1. **Requalify `VE-THERM-004`**: change it from blocking FAIL to **INFO / warning**
   as long as Part B has not concluded, explicitly logging the convention.
   Normative justification: ASHRAE 140:2023 §7.2.1.11.2 notes 2 and 3 (l. 3178-3186)
   announce that this U **must** vary by software.
2. **Move the check to the normative inputs**: thicknesses, lambda, rho, cp, gas /
   gap R, per-pane optics — i.e. the equivalent of Table 7-10, once
   the edition is confirmed. This is the only check that is genuinely normative.
3. **Declare the pane thickness in `reference_model_assets.json`** (layers
   l. 1401-1432): without it, no glazing check is reproducible. Correcting this
   deficiency **does not depend on any missing standard** — it is a consistency fix with
   `sia4010_case_manifest.json` l. 534, to be done immediately.
4. **Probe VE** (`ve-adapter-engineer`): `get_layers()`, `get_default_resistances()`,
   `get_u_factor()` × {ashrae, cibse, iso, t24}, `get_g_values()`. A single run
   discriminates H1/H2/H3.
5. **Obtain EN ISO 52016-1:2017 ch. 7** → Part B. The only path to settle the edition question.

## A.8 What I have NOT verified

- No value from NREL/TP-472-6231 (document absent). The 3.0 / 0.789 / 0.86156 / 1.06 /
  6.297 / 3.175 mm / 13 mm are **taken from the repository, not verified at source**.
- The content of **ASHRAE 140:2017** and **EN ISO 52016-1:2017**. The "bold not
  preserved" caveat from `test-1.spec.md` §4 remains open: note a of Table 7-10
  (l. 3270) and Table 7-11 (l. 3314) says "Updates to Standard 140-2017 are
  highlighted in bold", and the extraction erases bold. **I therefore cannot tell
  which cells in these tables changed between 2017 and 2023.**
- **[I, low confidence — do not use as evidence]** The very existence of the note
  "Updates to Standard 140-2017" suggests that Table 7-10 (the "fundamental
  properties / WINDOW 7" approach) **already existed in 2017**, which would make the 1995
  set obsolete for SIA. But this is an inference about formatting that I cannot
  read. It **does not justify any model modification**.
- The surface resistance conventions actually applied by IESVE (no VE
  documentation in `/refs` on `get_default_resistances`).
- The content of `Resultaterfassung_Test1.xlsx`, which might contain the reference
  inputs used by the 4 SIA reference programs.

---

# PART B — Photo request list: EN ISO 52016-1:2017

## B.0 General photography instructions (to be forwarded as-is)

- **One photo = one full page**, flat, no cropping. If a table continues on the
  next page, photograph **both pages**.
- **The header and footer must be legible on every shot**: they carry the
  edition reference (e.g. `EN ISO 52016-1:2017 (E)`) and the page number. This is
  our edition proof, shot by shot.
- **Systematically include the table title AND all its footnotes**
  (a, b, c…). In ASHRAE 140 the notes carry the calculation convention; the
  same should be assumed here.
- Do not crop, do not straighten, do not convert to black & white: **bold** and
  *italics* carry meaning (cf. A.8).

## B.1 — PRIORITY 0: edition proof and locating (essential, ~6 shots)

| # | What is needed | Why we need it |
|---|---|---|
| **B1.1** | **Cover page / title page**: full standard number, title, **edition date/year**, "ed-1" mention if present, ICS, and the Swiss national foreword (SN) page if it exists | Resolve the **2017 vs 2023** caveat opened in `test-1.spec.md` §4 and §10. Without this, everything else is unusable |
| **B1.2** | **Complete table of contents** (all pages) | We do **not** know where table 27 is located, nor what the sub-articles of 7.x are. See B.5 |
| **B1.3** | **List of tables** and **list of figures**, if the document has one | Locate **table 27** cited by SIA 4010. If this list does not exist, see B.5 |
| **B1.4** | **First page of chapter 7** (chapter title + first paragraph) | Confirm that ch. 7 is indeed the "validation / quality control" chapter and not something else. We only assume this |
| **B1.5** | **All sub-article headings 7.1 to 7.n** (can be done via photos of the pages where they appear) | SIA 4010 refers precisely to **7.2.2**; SIA 380/2 refers to **7.2**. The structure is needed so nothing is missed |
| **B1.6** | **Page(s) of the normative references** where **ASHRAE 140** is cited, with **its year** | The SIA spec says "(Basis ASHRAE 140:2017)". Yet ISO 52016-1 is from 2017: it may reference ASHRAE 140-2014 or -2011. **Critical consistency check** to know which window set is actually intended |

## B.2 — PRIORITY 1: the blocker (Test 1, cases 600/900)

| # | Clause / table requested | What we expect from it **exactly** | Our use |
|---|---|---|---|
| **B2.1** | **§7.2.2 in full** (all pages of the sub-article) | Full description of the test cell: geometry, orientation, list of cases | SIA 4010 tab. 62 and tab. 64 line 1 cite by name "chiffre 7.2.2" (`sia_4010_2023.txt` l. 2652-2653 and 2850) |
| **B2.2** | **Table 27 in full**: title, body, **all** notes, **plus the page preceding it** (introductory paragraph) | Unknown — this is precisely what we are looking for | SIA 4010 cites it as **the scope of Test 1** (`sia_4010_2023.txt` l. 2652-2653: "selon EN ISO 52016-1:2017, chapitre 7, tableau 27"; same at tab. 64 l. 2844-2850) |
| **B2.3** | **The clause and/or table from ch. 7 that defines the WINDOW** | Imperatively: (i) number of panes, **pane thickness**, **lambda**, **rho**, **cp**, **IR emissivity**; (ii) air gap: **thickness**, **gas**, and whether it is given as **conductance/resistance** or as gas to be calculated; (iii) optics: **solar transmittance and reflectance per pane at normal incidence**, and/or **g / SHGC of the double glazing**, and any angular table; (iv) **the U if given, AND the sentence stating which surface coefficients it includes**; (v) the **interior and exterior surface coefficients applicable to the window** | **THIS IS QUESTION 1.** Settles the "1995" set (lambda 1.06 / 3.175 mm / gap 13 mm at 6.297 / tau 0.86156 / g 0.789 / U 3.0) vs the "2023" set (lambda 1.00 / 3.048 mm / gap 12.0 mm at 5.208 / tau 0.834 / g 0.769 / U 2.10). SIA spec: "Verglasung : ISO EN 52016:2017 Kapitel 7" (`spec_test1.txt` l. 60) |
| **B2.4** | **The clause / tables from ch. 7 giving the OPAQUE CONSTRUCTIONS**, **Leichtbau** AND **Massivbau** variants | For **wall, roof, floor**, in **both** variants: layer order, **thickness, lambda, rho, cp of each layer**; the **declared U**; and **the surface coefficients with which this U is declared** | Resolves the `[REQUIS]` item #2 from `test-1.spec.md` §8, today covered only by assumption (ASHRAE 140:2023 Tables 7-2 / 7-27). SIA spec: "Konstruktionen … Leichtbau / Massivbau" (`spec_test1.txt` l. 18-21) |
| **B2.5** | **The clause from ch. 7 giving the INFILTRATION** | Rate **and** unit (h⁻¹? m³/h? at what reference volume?), whether constant or not, and whether the flow is corrected for density/temperature | Resolves the `[REQUIS]` item #4 from `test-1.spec.md` §8. The current model sets 0.5 h⁻¹ without a verified source (`sia4010_case_manifest.json` l. 558-563) |
| **B2.6** | **The clause from ch. 7 giving the SURFACE TRANSFER COEFFICIENTS** of the cell (interior / exterior, convective only vs combined) | The values, and the selection rule | SIA 4010 tab. 64 explicitly records the open question "External heat transfer coefficient?" (`sia_4010_2023.txt` l. 2848-2849). Provisionally settled via ASHRAE 140:2023 Table 7-7 in `test-1.spec.md` §3.1 — to be confirmed at source |
| **B2.7** | **The clause from ch. 7 giving the INTERNAL GAINS and VENTILATION** of the cell | Power, radiative/convective split, schedule | The SIA spec gives 200 W constant (`spec_test1.txt` l. 45, 50-51) but also refers to ch. 7; the **radiative fraction** must be verified (the model assumes 0.6 without a verified source) |
| **B2.8** | **The clause from ch. 7 listing the TEST CASES** and, if present, **the reference values / dispersion ranges** | List of cases (600, 640, 900, 940, FF…) and any results table | Verify that the SIA cases (`spec_test1.txt` l. 64-66) are indeed a subset; and cover `[REQUIS]` item #5 (case 1E bounds) in case |

## B.3 — PRIORITY 2: useful to the project, not blocking for Test 1

| # | Requested | Why |
|---|---|---|
| **B3.1** | **Tables 11 to 20** (input data), with their notes | SIA 380/2:2022 A.2.2: "Les donnees d'entree sont selon SN EN ISO 52016-1:2017, **tableaux 11 a 20**" (`sia_380_2_2022.txt` l. 2301-2302). Needed for Tests 2 and above |
| **B3.2** | **The SWISS NATIONAL ANNEX (SN)** to EN ISO 52016-1:2017: title page + summary + all tables of standard values | SIA 380/2 A.2.2: "Les valeurs standard sont donnees dans **l'annexe nationale** a la norme SN EN ISO 52016-1:2017" (`sia_380_2_2022.txt` l. 2302-2303). **Note: this annex may be a separate document** — mention this to the colleague |
| **B3.3** | **§6.5.7.2 and §6.5.7.3** (opaque element properties) | Replaced by SIA 380/2 A.2.3 (`sia_380_2_2022.txt` l. 2317-2319): we need to know what is being replaced |
| **B3.4** | **Annex G** (dynamic transparent elements) | SIA 380/2 A.2.4 relies on it (`sia_380_2_2022.txt` l. 2389) — relevant for Test 2 (solar shading) |
| **B3.5** | **§6.5.4.5** (base required power vs system-specific) | Cited by SIA 380/2 4.1.1.4 (`sia_380_2_2022.txt` l. 1216) |
| **B3.6** | **§7.2** (beyond 7.2.2) | SIA 380/2 2.2.2: a method is admissible if it meets "chiffre 7.2" (`sia_380_2_2022.txt` l. 1049) |

## B.4 — PRIORITY 3: to try BEFORE asking the colleague (zero cost)

**`http://standards.iso.org/iso/52016/-1/ed-1`** — ISO electronic insert for edition 1,
**cited by the SIA Test 1 specification itself** (`spec_test1.txt` l. 4) and by an
Anwenderbericht (`…\norme\anwender_test1_2.txt` l. 12). It is established that it contains the
DRYCOLD weather file. **Check whether it also contains the input and/or results workbooks
for the chapter 7 test cases.** If so, a large part of B.2 becomes unnecessary and the
photo request can be reduced to B.1 + B2.2 + B2.3. **[I — to be verified, zero cost]**

## B.5 — What I do NOT know how to locate (to be asked explicitly)

- **I do not know in which chapter or on which page "table 27" is located.**
  I only know that SIA 4010 associates it with chapter 7 (`sia_4010_2023.txt` l. 2652-2653,
  2844-2850) and that SIA 380/2 places tables 11 to 20 in the input data
  (l. 2301) — which is consistent with, but **does not prove**, table 27 being in
  ch. 7. **→ Ask for B1.2 + B1.3 (table of contents + list of tables) first, and wait for these
  shots before ordering the rest if the request budget is truly limited to one.**
- **I do not know whether chapter 7 is indeed the validation chapter** nor whether it actually
  contains the test cell data, or whether it merely refers to ASHRAE 140.
  **If ch. 7 simply refers to ASHRAE 140 without reproducing the values**, then
  question 1 shifts to **ASHRAE 140:2017**, and that edition must be acquired
  (ASHRAE purchase, ~a few hundred CHF) rather than insisting on the ISO.
  **→ Ask the colleague to flag this scenario explicitly.**
- **I do not know whether the Swiss national annex is bound into the same volume** or published
  separately (B3.2).

## B.6 — Short message, ready to forward to the colleague

> Standard: **SN EN ISO 52016-1:2017**. Full-page photographs, headers and footers
> included, table footnotes included, no cropping, no black & white.
>
> **Step 1 (to be sent first, 6 shots):** title page; complete table of contents;
> list of tables and figures; first page of chapter 7; page(s) of
> the normative references where ASHRAE 140 appears with its year.
>
> **Step 2 (as soon as Step 1 has allowed us to locate the pages):** article 7.2.2 in
> full; table 27 in full with the page preceding it; all pages from
> chapter 7 that give the test cell data — **glazing** (thicknesses, lambda,
> rho, cp, gap and its gas/resistance, transmittance and solar factor, U and the sentence
> stating what that U includes), **lightweight and heavyweight opaque constructions** (layers, lambda, rho,
> cp, U), **infiltration**, **surface transfer coefficients**, **internal gains**,
> **list of test cases**.
>
> **If chapter 7 merely refers to ASHRAE 140 without giving the values:
> let us know — we will change our source.**
