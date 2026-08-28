> **Note:** Translated from French original. See [audit-reference-project-2026-08.md](audit-reference-project-2026-08.md) for the source document.

# Independent audit — SIA 380/2 reference project (`swiss_sia/reference_project.py`)

> Role: `qa-auditor` (independent from implementation agents).
> Date: 2026-08-14.
> Purpose: verify that every frozen value across the **8 families** of the SIA 380/2:2022
> reference project is FAITHFUL to the SIA source, that the substitution logic is correct,
> and produce a signed traceability matrix.
> No production code line was modified. Nothing was committed.

---

## 0. Level of evidence — I DID OPEN the PDF

Unlike `traceability/sia380-2-generation-reference.spec.md` SS0 (where the
`norm-analyst` agent **was unable to open** `refs/SIA-380-2-2022.pdf`), **I extracted
the primary PDF with PyMuPDF (`fitz` 1.28.0)** and read the cells one by one.

| Element | Detail |
|---|---|
| PDF opened | `refs/SIA-380-2-2022.pdf` (64 pages), watermark "iNorm License, IES, Johan Haeberle, 372332" (legitimate licensed copy) |
| Table 2 | PDF pages **32-35** (idx 31-34) — fully extracted |
| Table 3 | PDF pages **36-37** (idx 35-36) — fully extracted |
| Tables 5-7 | PDF page **38** (idx 37) — fully extracted |
| Tables 8-9 | PDF page **39** (idx 38) — fully extracted |
| SIA 2024 JSON | `refs/reference-data/sia-2024-2021.usage-data.json` (45 usages) — read via Python |
| Tests | `tests/test_reference_project.py` — **40/40 PASS**; + adversarial boundary tests below |

**Verdict markers**:
- **PASS** = code value identical to the primary SIA 380/2 source (PDF), reproducible here.
- **WARNING** = code correct, but primary source **absent from `/refs`** (therefore not signable) OR minor observation.
- **FAIL** = wrong value (none found).

---

## 1. Traceability matrix — the 8 families emitted by `reference_project.py`

Systematic normative locator: `# SIA 380/2:2022`. Source decimal separator "," normalised to dot.

### Family 1 — `opaque_envelope_constructions` (Table 3, limit value)

| Code parameter | Code value | Source value (limit) | PDF locator | Verdict |
|---|---|---|---|---|
| `external_wall_u` | 0.20 | 0,2 (External wall, row 1) | Tab 3, p36 | **PASS** |
| `flat_roof_u` | 0.20 | 0,2 (Flat roof, row 1) | Tab 3, p37 | **PASS** |
| `ground_floor_u` | 0.30 | 0,3 (Floor against ground, row 1) | Tab 3, p36 | **PASS** |

Emitted unit `W/(m2K)` conforms to the header "W/(m2-K), limit value". `reference_project` uses only
the **limit** column (the other Table 3 constructions are cross-checked in SS3).

### Family 2 — `window_u_value_and_frame_fraction` (Table 2, limit value)

| Code parameter | Code value | Source value (limit) | Symbol | PDF locator | Verdict |
|---|---|---|---|---|---|
| `window_u` | 1.10 | 1,1 | Uw | Tab 2, p32 | **PASS** |
| `window_frame_fraction` | 0.25 | 0,25 | ff | Tab 2, p32 | **PASS** |

### Family 3 — `glazing_solar_and_visible_properties` (Table 2, limit value)

| Code parameter | Code value | Source value (limit) | Symbol | PDF locator | Verdict |
|---|---|---|---|---|---|
| `glazing_g_value` (g-perp) | 0.50 | 0,50 | g-perp | Tab 2, p32 | **PASS** |
| `glazing_light_transmittance` (tau) | 0.70 | 0,70 | tau | Tab 2, p32 | **PASS** |

### Family 4 — `infiltration` (Table 2)

| Code parameter | Code value | Source value (limit) | Unit | PDF locator | Verdict |
|---|---|---|---|---|---|
| `infiltration_m3_h_m2` | 0.15 | 0,15 (project/limit/target columns all = 0,15) | m3/(h-m2) | Tab 2, p32 | **PASS** |

### Family 5 — `cooling_generation_and_auxiliaries` (Table 5, air-cooled chiller, EER full load, limit)

| Power band | Code value (EER) | Source value (EER full-load limit) | PDF locator | Verdict |
|---|---|---|---|---|
| `P <= 12 kW` | 2.90 | 2,90 | Tab 5, p38 | **PASS** |
| `12 < P <= 50 kW` | 3.00 | 3,00 | Tab 5, p38 | **PASS** |
| `50 < P <= 150 kW` | 3.10 | 3,10 | Tab 5, p38 | **PASS** |
| **Switchover threshold** `>= 150 kW` | EER+ blocker (Tab 7) | Tab 2: "< 150 kW -> air"; "from 150 kW -> water, dry post-cooler" | Tab 2, p34; SS7.2.5.4-5 | **PASS** |

Quantity = **EER full load directly named** (never SEER) -> bypasses the unproven
SEER<->SN EN 14825 equivalence. Targets 3.10/3.15/3.20 (Tab 5) cross-checked in SS3.

### Family 6 — `heating_generation` (Table 8, air-to-water heat pump, SCOP, limit)

| Power band | Code value (SCOP) | Source value (SCOP limit) | PDF locator | Verdict |
|---|---|---|---|---|
| `P <= 12 kW` | 3.00 | 3,0 | Tab 8, p39 | **PASS** |
| `12 < P <= 50 kW` | 3.10 | 3,10 | Tab 8, p39 | **PASS** |
| `50 < P <= 150 kW` | 3.20 | 3,20 | Tab 8, p39 | **PASS** |
| **Target (`target`)** | `None` | Table 8 has **NO** "target values" row | Tab 8, p39 | **PASS** |
| `P > 150 kW` | blocker | Table 8 stops at <= 150 kW | Tab 8, p39 | **PASS** |

Type = **air-to-water heat pump** per Tab 2 (limit = "PAC air-eau"). `target=None` is **exact**:
I verified on the PDF that Table 8 has no target column (the heating target
is carried by Table 9 brine-to-water, outside the `reference_project` scope).

### Family 7 — `emission_system_and_unlimited_capacity` (Table 2, directives)

| Code parameter | Code value/directive | Source | PDF locator | Verdict |
|---|---|---|---|---|
| `emission_system_type` | `REFERENCE_DIRECTIVE`, radiant_fraction 0.0, "Convective emission" | "Type de systeme d'emission : par convection / par convection" | Tab 2, p33 | **PASS** |
| `max_heating_cooling_capacity` | `REFERENCE_DIRECTIVE`, "Unlimited heating and cooling capacity" (reference_value=None) | "Puissance maximale de chauffage et de refroidissement : illimitee / illimitee" | Tab 2, p33 | **PASS** |

Semantics correct: prescriptive directive of the reference run, **project_value=None**, never a blocker (see SS4).

### Family 8 — `sia2024_internal_gains_profiles_and_setpoints` (SS7.2.5.3 + SIA 2024, usage 1.01)

Frozen source read: `refs/reference-data/sia-2024-2021.usage-data.json`, usage `1.01` ("Wohnen MFH").

| Code parameter | JSON column | JSON symbol | Code value | Unit (UTF-8 bytes verified) | Verdict |
|---|---|---|---|---|---|
| `theta_i_mean` | **col30** | `theta_i_mean` ("Mittlere Raumtemperatur (Exploitation/Energie)") | 25 | °C (`c2 b0 43`, clean) | **WARNING** |
| `phi_i` | col34 | `phi_i` ("Relative Raumluftfeuchte") | 60 | % | **WARNING** |
| `A_p` | col42 | `A_p` ("Personenflache") | 35 | m² (`m c2 b2`, clean) | **WARNING** |
| `M` | col43 | `M` ("Aktivitatsgrad") | 1.2 | met | **WARNING** |
| `p_Be` | col51 | `p_Be` ("Elektrische Leistung Gerate") | 10 | W/m2 | **WARNING** |
| `E_vm` | col64 | `E_vm` ("Beleuchtungsstarke") | 150 | lx | **WARNING** |

**The CODE is correct**: it reads **col30** (exploitation) and **never col28** (design = 26 °C);
symbols and units match; status `STANDARD_USAGE_INPUT`, `project_value=None`,
deduplication by usage code, single aggregate blocker if code unknown (tests 40/40 PASS).

**Why WARNING and not PASS**: the **primary source SIA 2024:2021 Raumdatenblätter V221
is ABSENT from `/refs`** (only derived JSONs exist: `sia-2024-2021.usage-data.json` /
`.tables.json`, `reference-data-engineer` extraction dated 2026-08-14). I can prove
*code <-> frozen JSON*, but **not** *JSON <-> primary SIA 2024*. In keeping with the method
("if a [primary] reference value is absent, the test CANNOT be signed"), I
**do not sign** the normative fidelity of these 6 values -> referral to `reference-data-engineer`
(freeze/attach the primary source) + `norm-analyst` (confirm that col30 "exploitation" is
indeed the setpoint to substitute for the COOLING SIA 380/2 calculation; cf. observation O-2).

---

## 2. Verification of the substitution LOGIC (adversarial tests executed)

### 2.1 Generation band selection — 12 / 50 / 150 kW boundaries

Adversarial tests I executed (not planned by the implementer) via `build_reference_project_specification`:

**COOLING (air, Tab 5):**
```
cc=12.0     -> SUBSTITUTABLE  EER=2.9     (≤12 inclusif)
cc=12.0001  -> SUBSTITUTABLE  EER=3.0     (>12)
cc=50.0     -> SUBSTITUTABLE  EER=3.0     (≤50 inclusif)
cc=50.0001  -> SUBSTITUTABLE  EER=3.1     (>50)
cc=149.999  -> SUBSTITUTABLE  EER=3.1
cc=150.0    -> PROJECT_VALUE_MISSING (bloqueur EER+)   <-- seuil ≥150 = eau
cc=200.0    -> PROJECT_VALUE_MISSING (bloqueur EER+)
```
**HEATING (air-to-water, Tab 8):**
```
hc=150.0    -> SUBSTITUTABLE  SCOP=3.2    (≤150 inclusif)
hc=150.0001 -> PROJECT_VALUE_MISSING (Tab 8 s'arrête à 150)
hc=300.0    -> PROJECT_VALUE_MISSING
```

**Verdict PASS.** Bands `]p_min ; p_max]` (open on the left, closed on the right); lowest band `<=12`
inclusive. **Intentional and correct asymmetry at the 150 kW threshold**:
- Cooling: `>= 150` -> blocker (the machine *type* switches from air to water, Tab 2 "from 150 kW onwards").
- Heating: `= 150` -> substitutable 3.20 (the *type* remains air-to-water heat pump; only the tabulated extent of Tab 8 stops at 150).

Both rules faithfully reflect the PDF: cooling type switchover via Table 2 (SS7.2.5.4-5);
heating tabulation extent via Table 8.

### 2.2 EN 410 gate for g-perp (`_comparable_g_perp`)

- g whose source does not prove EN 410 **and** with no `g_value_bs_en_410` field -> `None` -> blocker
  ("a g_total including shading must not be substituted"). Correct: never substitute a g_total.
- Source containing `bs_en_410` **or** EN 410 field present -> accepted (returns `solar_factor`, fallback `g_value_bs_en_410`).
- Explicit mirror of `SIA3802Checker._is_sia_comparable_g_value`. **PASS** (tests 246-278 concordant).

### 2.3 Infiltration unit gate (`_collect_infiltration_substitution`)

- Only reads `infiltration_m3_h_m2` (sole unit comparable to Tab 2).
- If absent but `infiltration_rate` present -> **unit conversion** blocker (never silent substitution).
- Worst-case = `max` (never average). **PASS**.

### 2.4 `STANDARD_USAGE_INPUT` / `REFERENCE_DIRECTIVE` semantics

- Both statuses have `project_value=None` and are **never** counted as blockers
  (`status == SUBSTITUTABLE and reference_value is None` alone triggers the "No encoded SIA reference value" blocker).
- Conforms to SS7.2.5.3 (usage quantities identical between project and reference — verified on PDF Tab 2:
  all these quantities show "SIA 2024" in both the limit **and** target columns) and to Tab 2 (prescriptive
  emission/capacity directives). **PASS**.

### 2.5 theta = col30 (exploitation) never col28 (design)

Confirmed on the code side (`_SIA2024_USAGE_SYMBOLS[0] = ("theta_i_mean", "30", ...)`) and on the data
side (col28=`theta_i_design`=26; col30=`theta_i_mean`=25; test `test_theta_i_mean_uses_col30...` verifies 25 != 26). **PASS**.

---

## 3. Cross-check of the `config.py` scope against the PDF (corroboration)

Beyond the 22 emitted frozen values, I cross-checked **cell by cell** all SIA 380/2 constants
within the read scope against Tables 2/3/5-9. **All concordant (0 deviations).**

| Config block | Content verified | Source | Deviations |
|---|---|---|---|
| `SIA3802_LIMIT_VALUES` / `SIA3802_TARGET_VALUES` — envelope | 9 constructions x (limit+target): 0.20/0.14 - 0.30/0.20 - 0.30/0.30 - 2.70/2.70 - 0.28/0.20 - 0.30/0.20 - 0.64/0.64 - 0.30/0.20 - 0.20/0.14 | Tab 3 p36-37 | 0 |
| ... thermal bridges | psi/chi = 0/0 (limit and target) | Tab 2 p32 | 0 |
| ... ventilation/AHU/pressure losses | epsilon_V 1.0/1.4 - ducts C/C - AHU L2/L1 - Uahu 0.70/0.50 - Hdu 15/10 - Delta_p SUP 700/550 - Delta_p ETA 500/350 - Delta_p hr 300/400 | Tab 2 p33-34 | 0 |
| ... heat recovery | eta_rec,theta 0.73/0.78 - eta_rec,x 0.0/0.60 | Tab 2 p34 | 0 |
| ... control Delta_theta_ctr | cooling **-1.8**/0 - heating **+1.2**/0 (**signs verified**) | Tab 2 p34-35 | 0 |
| ... photovoltaics | PPV 10 WP/m2 - eta_conv 0.90/0.90 - target eta_PV,STC 0.17 | Tab 2 p35 | 0 |
| `SIA3802_COOLING_EER_SEER_LIMITS/TARGETS` — air | 5 bands EER+SEER, limit and target (2.90...3.40 / 3.80...4.40; 3.10...3.60 / 4.20...5.00) | Tab 5 p38 | 0 |
| ... water | 5 bands EER+SEER, limit and target (4.05...5.50 / 4.50...6.70; 4.45...6.00 / 5.90...8.00) | Tab 6 p38 | 0 |
| `SIA3802_WATER_COOLED_POST_COOLING_EERPLUS` | 5 bands EER+ full-load/50%, limit and target (3.15...3.70 / 4.55...6.00; 3.95...4.50 / 5.60...8.00) | Tab 7 p38-39 | 0 |
| ... auxiliaries SS7.2.5.6 | fans 0.036 - post-cooler pump 0.012 - chilled water pump 0.015 | p39 SS7.2.5.6 | 0 |
| `SIA3802_HEATING_SCOP_LIMITS/TARGETS` — air-to-water | 3.00/3.10/3.20; target `None` | Tab 8 p39 | 0 |
| ... brine-to-water (`heating_brine_water_hp`) | limit 4.00/4.20/4.60/5.00/5.50; target 4.40/4.60/5.00/5.50/6.00 | Tab 9 p39 | 0 |

---

## 4. What my PDF reading RESOLVES in `sia380-2-generation-reference.spec.md`

The `norm-analyst` agent left 15 `[TO VERIFY]` markers for lack of having opened the PDF. My primary reading **resolves 7** of them:

| # spec | Question | Resolution via PDF reading | Status |
|---|---|---|---|
| 1 | 150 kW boundary: "< 150 / >= 150" vs "<= 150 / > 150"? | Tab 2 p34: "< 150 kW" (air) / "from 150 kW" (water) -> **< 150 / >= 150** | **RESOLVED** |
| 2 | Inclusivity of round boundaries 12/50/150... | Headers "<= 12", "> 12... <= 50" -> `]p_min ; p_max]`, band 1 `<=` inclusive | **RESOLVED** |
| 3 | Table 7 not extracted (values/bands) | **Extracted** p38-39: EER+ full load & 50%, bands 12-50->1000; = `SIA3802_WATER_COOLED_POST_COOLING_EERPLUS` | **RESOLVED** |
| 10 | Does Table 8 have a target column? | Tab 8 p39: **no**, only "Grenzwert" (limit values) -> `target=None` correct | **RESOLVED** |
| 11 | Does Table 9 carry both limit AND target? | Tab 9 p39: **yes**, "Grenzwert" (limit values) AND "Zielwerte" (target values) | **RESOLVED** |
| 12 | Exact articles for Tab 8/9 | p39: SS7.2.5.8 = air-to-water heat pump (Tab 8); SS7.2.5.9 = brine-to-water heat pump (Tab 9) | **RESOLVED** |
| 13 | SS7.2.5.6 basis for auxiliary percentages | p39: fans/pump = share of the **post-cooling capacity**; chilled water pump = share of the **chiller capacity** | **RESOLVED** |

**Remaining unresolved (external standards absent from `/refs`, beyond my scope)**: `SEER`/`SCOP` (VE)
equivalence with **SN EN 14825** (#8/#9 of the spec); SS7.2.5.7 method via **SN EN 16798-13:2017**
(#14). `reference_project` neutralises them correctly: cooling compared on full-load EER (not SEER),
and caveat `[SCOP per SN EN 14825 - VE index equivalence TO VERIFY]` attached to every SCOP line (see SS5).

---

## 5. Verification of required caveats

| Expected caveat | Present? | Location | Verdict |
|---|---|---|---|
| `[TO VERIFY]` SN EN 14825 on SCOP | Yes | `_generation_substitution` adds `" [SCOP per SN EN 14825 - VE index equivalence TO VERIFY]"` if `grandeur == "SCOP"`; `config.py` l.44-46 `[TO VERIFY]` | **PASS** |
| Cooling >= 150 kW -> EER+ blocker (Tab 7) | Yes | `_collect_generation_substitutions`: `cooling_capacity >= SIA3802_COOLING_AIR_CHILLER_MAX_KW` -> blocker, `reference_value=None`, message "Table 7 EER+ ... not auto-comparable" | **PASS** |
| No `iesve` import (hard/pure separation) | Yes | imports = `json, os, dataclasses, typing, .config, .model_analyzer`; "iesve" only appears in **comments** (l.114, 672). Tests run without VE. | **PASS** |

---

## 6. Divergences and observations

### Value divergences: **NONE** (0 CRITICAL, 0 MAJOR, 0 MINOR)

All frozen values verifiable against `refs/SIA-380-2-2022.pdf` are **faithful**.

### Observations (do not block signature of families 1-7)

- **O-1 — WARNING (traceability, family 8)**: primary source **SIA 2024:2021 absent from `/refs`**.
  The 6 anchor values (25/60/35/1.2/10/150) are proven *code <-> frozen JSON* but not
  *JSON <-> primary source*. -> `reference-data-engineer`: attach/freeze the primary source (Raumdatenblätter V221).
- **O-2 — INFO (semantics, family 8)**: col30 (`theta_i_mean` = 25 °C) is **constant across 32 usages**;
  label "Mittlere Raumtemperatur (Exploitation/Energie)". SIA 380/2 deals with **COOLING**, so a
  mean setpoint of 25 °C is plausible (vs col28 design 26 °C). Choice of col30 **correct** for an
  energy/cooling calculation, but Tab 2 distinguishes theta_i,set,**C** (summer) and theta_i,set,**H** (winter):
  `norm-analyst` must confirm that the single substituted value covers the requirement (documentary here,
  `project_value=None`, feeds no calculation in this module). Same for `phi_i` (summer vs winter).
- **O-3 — INFO (scope)**: `reference_project` builds only the **"limit value"** reference project
  (via `SIA3802_LIMIT_VALUES`). The **"target value"** reference project (SS7.2.5.2 authorises conformity
  by limit **or** target) is not generated. Not an error (the limit is the stricter basis), but should be
  documented explicitly to prevent a reader from believing the SIA 380/2 conclusion is complete.
- **O-4 — INFO (scope, not exercised)**: the lowest band of `heating_brine_water_hp` (`upper_kw=50`) covers
  `P<12` whereas Table 9 only tabulates from 12 kW onwards ([INTERPRETATION] extension). **No effect
  on `reference_project`** (which uses only `heating_air_water_hp`). Flagged for any other consumer.
- **O-5 — INFO (representation)**: the emission directive encodes "convective" as `radiant_fraction=0.0`.
  Acceptable machine representation (explicit `directive` field); this 0.0 is not a normative table number.

---

## 7. Signed overall verdict

**Numbers.** 22 frozen values emitted by the 8 families + 1 threshold rule (150 kW) + 2 qualitative
directives, **all verified**; ~110 constants in the `config.py` scope cross-checked cell by cell
against Tables 2/3/5-9. **Value divergences: 0.** Tests: `tests/test_reference_project.py` 40/40 PASS
+ my adversarial boundary tests PASS.

**Signature decision (per family):**

| Family | Verdict | Signable |
|---|---|---|
| 1 — opaque_envelope_constructions | PASS | **YES** |
| 2 — window_u_value_and_frame_fraction | PASS | **YES** |
| 3 — glazing_solar_and_visible_properties | PASS | **YES** |
| 4 — infiltration | PASS | **YES** |
| 5 — cooling_generation_and_auxiliaries | PASS | **YES** |
| 6 — heating_generation | PASS | **YES** |
| 7 — emission_system_and_unlimited_capacity | PASS | **YES** |
| 8 — sia2024_internal_gains_profiles_and_setpoints | WARNING | **NO** (primary source SIA 2024 absent from `/refs`) |

**Families 1 to 7 (core traceable to SIA 380/2:2022 PDF): AUDITED OK — 2026-08-14 — qa-auditor.**

**Family 8 (SIA 2024): NOT SIGNED.** The code behaviour is correct and reproducible against the frozen
JSON, but the normative fidelity of the 6 anchor values is not provable as long as the primary source
SIA 2024:2021 Raumdatenblätter is not present in `/refs`. Referral to `reference-data-engineer`
(primary source) and `norm-analyst` (confirmation of O-2). The signature will be extended to family 8 after O-1 is lifted.

> — `qa-auditor`, 2026-08-14
