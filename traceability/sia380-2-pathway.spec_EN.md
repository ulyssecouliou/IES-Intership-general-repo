> **Note:** Translated from French original. See [sia380-2-pathway.spec.md](sia380-2-pathway.spec.md) for the source document.

# Spec --- SIA 380/2:2022 Justification Pathways and Decisive Client Verdict

> Status: **RULING RENDERED (high confidence).** Decisive pathway, quantity,
> verbatim criterion, reference project composition, calculation climate and
> bridge to SIA 4010 are **verified by direct PDF reading** (chapters 5--7,
> Tables 2--3). The remaining `[TO VERIFY]` items are **outside `/refs`** (SIA 380, SIA
> 2024 Merkblaetter, SIA 387/4) or concern the **application** climate and the
> setpoint pathway choice.
> Author: `norm-analyst`, 2026-08-14.
> Scope: SIA 380/2:2022 FR (`refs/SIA-380-2-2022.pdf`), verification of a
> CLIENT building (application), distinct from the SIA 4010 TEST climate/protocol.

---

## 0. Evidence regime and framing

- **[TRACED PDF]** --- read directly from `refs/SIA-380-2-2022.pdf` (PyMuPDF
  extraction). Locator + strictly necessary value; no page redistribution.
- **[TRACED]** --- relayed from a prior extraction frozen in the repository (`config.py`,
  `figure1.json`, `sia-2024-2021.tables.json`, `critere-test4.spec.md`); not
  re-verified this task.
- **[INTERPRETATION]** --- explicitly marked reading, justified by a cited
  article; never presented as a citation.
- **[TO VERIFY]** --- outside `/refs` or not located; specific question in §6.
  **No value, formula or tolerance invented.**

**Framing**: SIA 380/2:2022 = "**Dynamic method for the determination of
energy demands, power and energy requirements**" (`# SIA 380/2:2022 p.1`) [TRACED PDF],
**replaces SIA 382/2:2011 and SIA 2044:2019**. It is the **dynamic calculation
method** for the demand; the limit values are **calculated** (reference
project, §7.2.5), not tabulated in kWh/m2. Structure chapters 1--7. **The
table of contents (p. 3) places "3.1 Humidification" (p. 21) --- §3.1 is NOT
the climate** (correction).

**Key normative bridge**: `# SIA 380/2:2022 6.2.2.1` [TRACED PDF] --- a calculation
method is admissible only if it "can demonstrate **validation per SIA
4010** for the systems considered". -> SIA 380/2 **requires** that the tool
(IESVE/ApacheSim) be SIA 4010 validated. Minimum inputs: `# SIA 380/2:2022
6.2.2.2` -> annex A.3 + EN standards [TRACED PDF]; DHW: `# SIA 380/2:2022 6.2.2.5`
-> SIA 385/2 [TRACED PDF].

---

## 1. Justification pathways defined by SIA 380/2:2022

- **PATHWAY A --- justification by limit/target values (component/input).**
  `# SIA 380/2:2022 7.2.1.2` [TRACED PDF]: "for justifications (**application
  cases 1 and 2 per SIA 380**), the calculated project values are
  compared with the limit values and target values". Values per element =
  **Table 3** (§3). Meaning of "application cases 1 and 2" defined in **SIA 380**
  (absent) -> `[TO VERIFY]` (b).
- **PATHWAY B --- overall performance via reference project (DECISIVE).**
  `# SIA 380/2:2022 7.2.5.1` [TRACED PDF]: limit/target values of the
  overall index obtained by applying **chapters 5 and 6** to a **reference
  project**, based on the **overall energy balance per SIA 380**.
  `# SIA 380/2:2022 7.2.5.2` [TRACED PDF] --- **verbatim criterion**: "The overall
  performance is met when the project value per chapter 6 is
  **lower than** the corresponding limit or target value of the
  **reference project**."

---

## 2. Decisive quantity, unit and criterion

### 2.1 Pathway B --- overall performance (the verdict)

- **Quantity**: `# SIA 380/2:2022 6.1.4` [TRACED PDF] "The result is the **building
  energy expenditure index per SIA 380**. It corresponds to the **object
  value**." What chapter 6 produces: `# 6.1.1` [TRACED PDF] (heating demand,
  cooling demand, humid./dehumid., lighting, DHW if coupled, other + PV).
- **Aggregation/weighting**: `# SIA 380/2:2022 6.1.2` [TRACED PDF] "Aggregation
  into annual values and weighting is carried out **per SIA 380**" ->
  **delegated**, not a gap in the tool.
- **Criterion** (verbatim §7.2.5.2): `project_index(ch.6) <
  limit_or_target_index(reference)`, **strict** inequality, **calculated** bound.
- **Code consequence**: `cooling_demand_max=None`/`heating_demand_max=None`
  **COMPLIANT**.
- **Unit/definition of the index**: falls under **SIA 380** (absent) ->
  `[TO VERIFY]` (a).

### 2.2 Pathway A --- by limit/target values (diagnostic)

U `W/(m2-K)`, psi `W/(m-K)`, chi `W/K`, ff, g-perp, tau, infiltration `m3/(h-m2)`, epsilon-V,
U_ahu `W/(m2-K)`; criterion `project_value <=/>= limit|target` (`# 7.2.1.2`).

### 2.3 Cooling necessity --- STATED screening (not to be confused)

- Cooling is **necessary** if the **upper limit curve** exceedance
  (§5.2.2.5) **> 100 h/yr** (new build, `# 3.2.4.3` [TRACED PDF]); **400 h** (existing,
  `# 3.2.4.5` [TRACED PDF]). Basis: `# 3.2.4.2` -> SIA 180:2014 fig. 3 + annex C.2.
- **Distinct** from **summer heat protection** `# 7.1.2.1` -> **SIA 180:2014
  ch. 5** [TRACED PDF]. The 100/400 h threshold is not the summer comfort criterion.

### 2.4 Delegated requirements (ch. 7) and 2.5 power

Ventilation `# 7.1.1` -> SIA 382/1; summer heat `# 7.1.2.1` -> SIA 180 ch. 5
[TRACED PDF]. Design power `# 4.2--4.3` [TRACED] (`W`/`W/m2`).

---

## 3. Reference project

### 3.1 Articles and tables (verified)

- `# SIA 380/2:2022 7.2.5.1` and **`7.2.5.3`** [TRACED PDF]: "the reference
  project input quantities are in **Table 2**; **except for these quantities,
  the reference project is calculated with the same data as the actual
  project**" (identical geometry, usage and climate; only Table 2 is
  substituted).
- **Table 2** `# SIA 380/2:2022 table 2, pp. 32--33` [TRACED PDF] (Limit / Target)
  --- see the full row list below; distinct numerical values
  (Uw 1.1/0.88; psi/chi 0/0; ff 0.25; g-perp 0.50; tau 0.70; infiltration 0.15;
  epsilon-V 1/1.4; classes C, L2/L1; U_ahu 0.7/0.5; convection emission; Phi-H/C,max
  unlimited). Quantities marked "SIA 2024" / "SIA 387/4": see **§7**.
- **Table 3** `# SIA 380/2:2022 table 3, pp. 36--37` [TRACED PDF] --- header
  U-values (limit/target): external wall **0.2/0.14**; against ground **0.3/0.2**; against
  unconditioned space **0.28/0.2** W/(m2-K).
- Setpoints & comfort: `# figure 1 / §5.2.2.1--5.2.2.5, p. 27` [TRACED].

### 3.2 Mapping Table 2/3 <-> `reference_project.py` families

| Family (code key) | Source | Locator | Status |
|---|---|---|---|
| `opaque_envelope_constructions` | Table 3 | pp. 36--37 [TRACED PDF] | IMPLEMENTED |
| `window_u_value_and_frame_fraction` | Table 2 | pp. 32--33 [TRACED PDF] | IMPLEMENTED |
| `thermal_bridges` (psi=0, chi=0) | Table 2 | pp. 32--33 [TRACED PDF] | MISSING |
| `glazing_solar_and_visible_properties` (g-perp 0.50; tau 0.70) | Table 2 | pp. 32--33 [TRACED PDF] | MISSING |
| `glazed_area_ratio_solar_protection_and_control` (fg; blind; cat. 4/2; control 2/3) | Table 2 + tab. 10 + SIA 387/4 | pp. 32--33, p. 46 [TRACED PDF]; fg/control delegated | MISSING |
| `infiltration` (0.15) | Table 2 | pp. 32--33 [TRACED PDF] | MISSING |
| `sia2024_internal_gains_profiles_and_setpoints` | Table 2 -> SIA 2024 | **see §7** | MISSING (partially traceable --- §7) |
| `sia3874_lighting_power_and_control` | Table 2 -> SIA 387/4 | delegated (absent) | MISSING |
| `emission_system_and_unlimited_capacity` (convection; unlimited) | Table 2 | pp. 32--33 [TRACED PDF] | MISSING |
| `ventilation_system_and_controls` (epsilon-V 1/1.4; C; L2/L1; U_ahu 0.7/0.5) | Table 2 + Table 4 | pp. 32--33, p. 37 [TRACED PDF] | MISSING |
| `cooling_generation_and_auxiliaries` | Tables 5--9 | pp. 38--39 [TRACED] | MISSING |
| `heating_generation` | Tables 8--9 | pp. 38--39 [TRACED] | MISSING |
| `photovoltaic_generation` | Table 2 | pp. 32--33 [TRACED]; PV article to confirm | MISSING |
| `sia380_annual_aggregation_and_weighting` | delegated **SIA 380** | `# 6.1.2` [TRACED PDF] -> SIA 380 outside `/refs` | MISSING **by normative delegation** |

`# 7.2.5.3` guarantees that geometry, usage and climate are **identical** to the project.

---

## 4. Calculation climate and usage data (CLIENT verification)

- **Calculation climate**: `# SIA 380/2:2022 5.2.1.2, p. 26` [TRACED PDF] "a
  **DRY per SIA 2028** shall be used"; winter/summer design data
  `# ch. 2, p. 12` [TRACED PDF]; annex p. 59: "**Normal** DRY, per SIA 2028"
  and **CH2018 available as option** for climate evolution [TRACED PDF].
- **Requalification**: "CH2018 RCP8.5 2035" (CLAUDE.md §3.1.1) refers to
  **SIA 4010** (`# SIA 4010:2023 3.1.1, p. 9` [TRACED]), not the body of 380/2 (which
  mandates DRY/SIA 2028, CH2018 optional/annex). -> `[TO VERIFY]` (c).
- **§7.2.5.3** [TRACED PDF]: the reference project shares this climate.
- **Usage data** (setpoints, air flows, gains, fg): **delegated to SIA 2024** ---
  detail and traceability per quantity in **§7**.

---

## 5. Recommendation

**Target Pathway B --- `# 7.2.5`** [TRACED PDF] (two runs project + reference, calculated
bound §7.2.5.2, identical climate §7.2.5.3), Pathway A as diagnostic. Normative
prerequisite: SIA 4010 validation (`# 6.2.2.1`). **Overall verdict** `NOT_CHECKABLE`
as long as the SIA 380 index unit (a) is not traced; never `PASS` without the
two runs + SIA 4010 validation + review. Inputs/outputs: cf. §3.1, §4, §7.

---

## 6. Remaining `[TO VERIFY]` points

| # | Specific question | Where to resolve | Impact |
|---|---|---|---|
| **(a)** | Unit/definition of the "energy expenditure index" + aggregation/weighting | **SIA 380** (absent) --- delegated by `# 6.1.2`/`# 6.1.4` | Verdict unit. Delegated by the standard. |
| **(c)** | **Application** climate mandated beyond the SIA 2028 DRY (year/CH2018 scenario?) | Annex 380/2 p. 59 + **SIA 4010 §3.1.1** | Client climate traceability. |
| **(b)** | "application cases 1 and 2" (§7.2.1.2); **SIA 2024 / SIA 387/4** values | SIA 380, SIA 2024, SIA 387/4 (absent) | Limit/target + delegated inputs. |
| **(f)** | **Setpoint pathway** theta-i,set for energy calculation: normal figure 1 (`# 5.2.2.1--.5`) vs simplified `# 5.2.2.6` (SIA 2024 Table 13); does "theta-i,set = SIA 2024" in Table 2 refer to Table 13? | Text `# 5.2.2` (pp. 26--27) + Table 2 header | Setpoint table choice (§7). |
| **(g)** | phi-i,set: are the **design** humidity values (SIA 2024 Table 11) the **operating setpoint** for the humid./dehumid. demand (ch. 6)? | Text chapter 6 (pp. 29--30) | phi-i,set source (§7). |
| **(h)** | **Table 2 column header/legend** (p. 32): does an "SIA 2024" cell without a project value = **identity** (project also SIA 2024) or substitution with a free project value? | Table 2 introductory text (p. 32) | Confirms the "identity" regime of §7 (Q-A). |
| (e) | **PV** articles (Table 2); **delta-theta_ctr** (SN EN 15316-2, absent) | SIA 380/2; EN outside `/refs` | Completes Table 2. |

---

## 7. "Setpoints / air flows" family of the reference project (Table 2 x SIA 2024)

Targeted response for the SIA 2024 collector implementation. Anchoring:
`# SIA 380/2:2022 7.2.5.3, table 2, pp. 32--33` [TRACED PDF]; frozen SIA 2024
data `refs/reference-data/sia-2024-2021.tables.json` [TRACED].

### 7.1 Regime of each Table 2 cell (Q-A)

- **"project-specific" on the project side + "SIA 2024" on the reference side** ->
  **differentiating substitution**: the project keeps its value, the reference
  substitutes SIA 2024 (case of **qv**).
- **Empty project cell + "SIA 2024" on the reference side** -> **[INTERPRETATION]
  identity**: the quantity is a **standardised usage datum** (SIA
  2024), **identical** in the project and the reference. Justification: `# 7.2.5.3`
  (outside Table 2 = same data; here the SIA 2024 value applies on both
  sides because usage is not a free parameter of the energy calculation) + the very title
  of SIA 2024 "**Usage data** for premises". **Consequence**:
  no project/reference delta, but **the SIA 2024 value is still needed for
  BOTH runs**. -> to be confirmed by the Table 2 header, `[TO VERIFY]` (h).

### 7.2 Verdict per quantity {substitution | identity | blocked-Merkblaetter}

| Quantity (Table 2) | Regime | Reference source + locator | Coding verdict |
|---|---|---|---|
| **qv** air flow `m3/(h-P)` | **substitution** | nominal value = SIA 2024 **Table 11** `air_neuf_hygiene_m3_h_pers` (day; `_nuit` for residential) [TRACED] | **VALUE codable** (Tab. 11); **annual operating profile = BLOCKED-Merkblaetter** |
| **theta-i,set,H/C** `degC` | **identity** | normal pathway **figure 1 `# 5.2.2.1--.5`** (offset `# 5.2.2.5` via theta_design **Table 11**); simplified pathway **`# 5.2.2.6` = Table 13** (annex B) [TRACED] | **codable** (two pathways traced, **NOT Merkblaetter**); choice `[TO VERIFY]` (f) |
| **phi-i,set,H/C** `%` | **identity** | SIA 2024 **Table 11** `humidite_relative_h/c_pct` (design values) [TRACED] | **codable** (only traced humidity table); design->operation caveat `[TO VERIFY]` (g) |
| **internal gains** (AP, M, pBe, pLiAc, Evm; occupant/equipment/lighting profiles, schedules, simultaneities, m2/pers) | **identity** | **SIA 2024 usage sheets** (Merkblaetter 3.1, 4.4, 6.2...) --- **absent from `/refs`** (`sia-2024-2021.tables.json.ce_qui_reste_manquant`) [TRACED] | **BLOCKED-Merkblaetter** --- neither Table 11 nor Table 13 contain them |

### 7.3 Design vs operation warning (Q-B, Q-C)

- **Table 11 = Auslegungswerte (DESIGN values, ch. 4).** theta_design
  (Tab. 11) feeds the **design power** `# 4.2--4.3`, **NOT** the
  energy calculation setpoint ch. 5--6. Using theta_design as an energy
  setpoint would be a **category error**.
- **Q-C --- theta-i,set (energy, ch. 5--6)**: source = **figure 1** (`# 5.2.2`, a
  380/2 figure, offset by usage via theta_design Tab. 11) **or** **Table 13** SIA 2024
  (`# 5.2.2.6`, simplified pathway "especially early planning"). **Never the
  Merkblaetter.** The label "theta-i,set = SIA 2024" in Table 2 literally points
  to Table 13 (whose title targets "the **Berechnung des jaehrlichen**
  Klimakaelte- und Heizwaermebedarfs"), but the normal 380/2 pathway is figure 1
  -> `[TO VERIFY]` (f).
- **Q-B --- qv (energy)**: the **nominal per-person value** is the hygienic air flow
  **Table 11** (`air_neuf_hygiene`, 29 `m3/h-P` common usages, 48
  kitchens/coarse production, 73 sport; **night** = value in brackets,
  e.g. 15 for residential). But the **annual energy calculation** requires the **operating
  profile** (operating hours, occupancy modulation, weighted night
  reduction), which is an **operating datum from the Merkblaetter
  (absent)**. -> the **value** is traced; the **annual profile is BLOCKED**.
  day/night: both levels are traced (Tab. 11); their annual weighting is
  not.

### 7.4 Conclusion for the SIA 2024 collector

Code **only** the quantities with an unambiguously traced source:
- **phi-i,set** (Table 11) --- codable, under caveat (g).
- **theta-i,set** (figure 1 `# 5.2.2` and/or Table 13 `# 5.2.2.6`) --- codable, expose
  **both pathways** and let (f) select; **do not** inject theta_design.
- **qv nominal value** (Table 11) --- codable; explicitly mark the
  **annual profile as BLOCKED-Merkblaetter**.
- **Internal gains** --- **DO NOT** map from Table 11/13: correct conclusion
  = "**family blocked: SIA 2024 usage sheets (Merkblaetter)
  required**". They are available free online (`fiches_utilisation_en_ligne`,
  post-corrigenda) but **not in the repository**.

Warning --- **Corrigenda caveat**: `sia-2024-2021.tables.json.corrigenda.controle_effectue
= false` --- no value from Tables 11/13 is confirmed post-rectification;
the online Merkblaetter, for their part, are post-corrigenda. To be resolved before freezing.

---

## 8. Ruling on `fg` (Glazed area ratio) and reference lighting

> Addition `norm-analyst`, 2026-08-14. Wiring of the reference project
> (`swiss_sia/reference_project.py`, families
> `glazed_area_ratio_solar_protection_and_control` fg component and
> `sia3874_lighting_power_and_control`). No formula/value invented; no
> code modified. `[TO VERIFY]` (i)--(l) extend §6. Verified frozen data read
> directly: `refs/reference-data/sia-2024-2021.usage-data.json`.

### 8.1 `fg` --- reference quantity and project quantity

**Table 2 row** `# SIA 380/2:2022 table 2, pp. 32--33` [TRACED PDF]: "Glazed
area ratio", symbol **fg**, unit "--"; **project = "project-specific"**,
**reference limit = "SIA 2024"**, **target = "SIA 2024"** -> **differentiating
substitution** (§7.1 regime): project = actual ratio, reference = SIA 2024
value by usage.

**Frozen data** (`refs/reference-data/sia-2024-2021.usage-data.json`) [TRACED]:
- `column_mappings."9"`: symbol **fg**, label **"Glasanteil (glazing
  percentage)"**, unit **%**; e.g. usage 1.01 (Wohnen MFH) `parameters."9".value =
  30%`.
- col10 = **Fw** "Abminderungsfaktor Fensterrahmen" (window frame reduction
  factor, 0.75 for 1.01) --- **distinct** column from the glazed fraction.
- **"Fensteranteil / Bruttofassade" (col11): ABSENT from JSON** --- 0 occurrences of
  `Fensteranteil`/`Bruttofassade`/`Fassade` (search verified). The extraction
  contains **only** the Glasanteil (col9).

**Reference quantity** --- The reference for the **fg** of SIA 380/2 is the
**Glasanteil (SIA 2024 col9, symbol fg)**, e.g. 30% for Wohnen MFH, **and not** the
Fensteranteil Bruttofassade (col11). Basis: **symbol identity** fg<->fg +
semantics "glazed surfaces" = "Glas"; col11 carries a **different symbol** and
is **outside `/refs`**. -> **[INTERPRETATION]** anchored (symbol + label), but the
**clause defining the symbol fg** (SIA 380/2) and the **definition of
"Glasanteil"** (SIA 2024) **are not in `/refs`** -> `[TO VERIFY] (i)`.

**Required project quantity vs model** --- On the project side, "project-specific" = actual
glazed fraction **as defined by fg**. The model exposes a **WWR =
window_area / wall_area** (`model_analyzer.py` ll. 1132--1133, supplied data). This
**is not** the Glasanteil:
- **Numerator**: Glasanteil = **glass** area (SIA 2024 separates glass
  (col9) from the **frame** via Fw (col10)); WWR = **window** area (glass +
  frame). Difference approx. frame factor -> quantities **not identical**.
- **Denominator**: that of the Glasanteil (gross facade? SRE? element?)
  **not read** (definition outside `/refs`); `wall_area` from the model (gross vs net of
  openings) **not characterised** -> not proven equal.
- **[INTERPRETATION]**: col9 = 30% with Fw = 0.75 (col10) separated => the Glasanteil
  is not a simple glass/window ratio (~0.7). The quantity analogous to a WWR
  window/facade would be the **Fensteranteil (col11)** --- precisely **not** the
  referent of fg.

**fg VERDICT**:
- **Reference**: SIA 2024 **Glasanteil (col9, symbol fg)** --- traced, available.
  **Not** the Fensteranteil Bruttofassade (col11, absent).
- **Project**: **glass** fraction defined as fg; the model's **WWR window/wall**
  is a **different quantity**.
- **Wireable with the existing WWR? NO --- `[TO VERIFY]`.** Do not map WWR->fg.
  Required: (i) definition of fg + of Glasanteil; (j) "glass fraction" project
  quantity consistent (or window->glass conversion explicitly traced; Fw col10
  available but its use as a conversion remains to be validated). Until traced,
  the **fg component** of `glazed_area_ratio...` remains **MISSING**; the **reference
  value col9** nonetheless remains traced for the reference run.

### 8.2 Lighting --- `pLi` (SIA 387/4) vs SIA 2024 data in our possession

**Table 2 row** `# SIA 380/2:2022 table 2, pp. 32--33` [TRACED PDF]:
- "Specific lighting power", symbol **pLi**, unit **W/m2**:
  **reference (limit AND target) = "SIA 387/4"**.
- "Illuminance (maintenance index)" **Evm**: **reference = "SIA 2024"**.
- Control: **"SIA 387/4:2017, table 10"** -> manual / continuous LED regulation.

**What WE have** (`usage-data.json`) [TRACED]:
- col64 **E_vm** "Beleuchtungsstaerke" [lx] (150 lx for 1.01).
- col71 **eta_lm** "Leuchten-Lichtausbeute" [lm/W] (90 lm/W for 1.01).
- `annual_energy_kwhm2`: **unlabelled** numbered columns (keys 3...24, kWh/m2).
  **No** label "Beleuchtung"/"Elektrizitaet"/"Heizwaerme" in the
  file (verified) -> the **annual lighting demand KZ is not identifiable**
  -> `[TO VERIFY] (k)`.
- **SIA 387/4 (lighting part, pLi method + table 10): ABSENT from `/refs`.**

**Normative analysis**:
1. The required reference quantity is **pLi [W/m2]**, **source SIA 387/4** --- not
   SIA 2024 (cited only for Evm). The control (tab. 10) is also **SIA 387/4**.
2. **"Annual KZ" pathway**: the KZ demand is an **energy [kWh/(m2-a)]**, not a
   **power [W/m2]**, and plays a **different role** (pre-computed result under
   SIA 2024 conditions, not the pLi input for the dynamic ch. 6 reference-project
   run). Substituting kWh/m2-a for pLi = **category error**; moreover the
   column is **not identifiable** (§ above) -> **not admissible**.
3. **"Evm + efficacy" pathway**: going from Evm [lx] and eta_lm [lm/W] to pLi [W/m2]
   requires the **factors from the SIA 387/4 method** (room utilisation factor,
   maintenance factor...). pLi = Evm / eta_lm **alone** (utilisation = maintenance
   = 1) would be a **forbidden simplification / invented formula**; these factors
   are **precisely** the missing content of SIA 387/4 -> **not admissible without
   SIA 387/4**. No pLi formula proposed.
4. The **lighting control** (SIA 387/4 tab. 10) is also **outside `/refs`**.

**Lighting VERDICT**: **BLOCKED SIA 387/4.** The family
`sia3874_lighting_power_and_control` **remains blocked** until the lighting part
of SIA 387/4 (pLi method + table 10) is provided. Only **Evm (col64)** is
traced via SIA 2024 and wireable as **reference illuminance** --- but **Evm is not pLi**
and unblocks **neither** the power **nor** the control. `eta_lm (col71)` is one
input among others of the absent method, **unusable alone**.

### 8.3 Added `[TO VERIFY]` (extending §6)

| # | Specific question | Where to resolve | Impact |
|---|---|---|---|
| (i) | Exact definition of **fg** (numerator glass vs window; denominator gross facade/SRE/element) | SIA 380/2 symbol clause + SIA 2024 def. "Glasanteil" (outside `/refs`) | fg<->Glasanteil identity; comparability |
| (j) | **Project** quantity "glass fraction" conforming to fg; WWR window/wall convertible (via Fw col10)? semantics of `wall_area` (gross/net) | SIA 380/2 + SIA 2024 + model code | Wiring on project side |
| (k) | Legend of `annual_energy_kwhm2` columns (which key = Beleuchtung?) | KZ_Raum_2024 sheet SIA 2024 (unlabelled in repository) | Identify the lighting KZ demand |
| (l) | **pLi** method + **table 10** (control) from **SIA 387/4** | SIA 387/4 lighting part (outside `/refs`) | Unblocks the lighting family |

---

## Standards called but absent from `/refs` (no value invented)
- **SIA 380** --- overall energy balance/index, aggregation/weighting (§6.1.2/.4), calculated
  limit (§7.2.5.1).
- **SIA 2024** --- Tables 11/13 **traced** (frozen in repository); **Merkblaetter
  (usage sheets) ABSENT** -> gains/profiles/schedules blocked (§7).
- **SIA 387/4** --- lighting, controls tab. 9/10 (Table 2).
- **SIA 382/1** --- ventilation (§7.1.1); **SIA 385/2** --- DHW (§6.2.2.5).
- **SIA 180:2014** --- summer heat ch. 5 (§7.1.2.1); fig. 3/4, annex C.2 (§3.2.4.2).
- **SN EN ISO 52016-1:2017 §7.2**, **SN EN 15316-2:2017**, EN standards from annex A.3
  (§6.2.2.2).

**The Pathway B success criterion is acquired** (`# 7.2.5.2`, [TRACED PDF]) and
depends on no invented constant.
