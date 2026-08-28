> **Note:** Translated from French original. See [sia380-2-generation-reference.spec.md](sia380-2-generation-reference.spec.md) for the source document.

# Normative Specification — Cooling and Heating Generation (SIA 380/2:2022 Tables 5-9)

> Role: `norm-analyst`. Date: 2026-08-14.
> Scope: machine-readable selection rules for the "cooling/heating generation" family
> of the SIA 380/2:2022 reference project, intended for `reference-data-engineer`
> (freeze the tables) and `validation-engine-engineer` (wire the substitution).
> This document does not modify any production code.

> **UPDATE 2026-08-14 — several `[TO VERIFY]` below have been RESOLVED**
> through direct PDF reading during the independent audit. Authoritative resolution
> source: `traceability/audit-reference-project-2026-08.md`. Resolved: the
> 150 kW threshold (`# 7.2.5.4` "< 150 kW" air / "from 150 kW" water),
> band inclusivity, **Table 7 in full** (variable EER+ full load
> AND 50% load, not comparable to `eer`/`seer` from VE), **Table 8 = LIMIT
> only** (no target column), **Table 9 = limit AND target**, and
> articles `# 7.2.5.8`/`# 7.2.5.9`. Remaining open: the equivalence
> `seer`/`scop`(VE) ↔ SN EN 14825 (EN standard absent) and the method choice
> (Pathway A vs B) — the code implements the substitution (Pathway B) with these
> two points marked `[TO VERIFY]`.

---

## 0. Traceability Warning (IMPORTANT — read first)

**I was unable to open `refs/SIA-380-2-2022.pdf` in this session.** Contrary to
the task statement, `Bash`/PyMuPDF is disabled, `poppler` (PDF rendering) is absent, and
`Grep` cannot decompress the `FlateDecode` streams in the PDF. **No direct PDF
extraction was therefore performed by me.**

What I did instead:
1. I took the `[TRACÉ PDF]` values provided by the calling agent.
2. I **cross-checked them against a prior extraction already present in the repository**:
   `docs/project/SIA_3802_4010_PDF_TRACEABILITY.md` §7 (which cites "SIA 380/2:2022 FR,
   tables 5-9 PDF pages 38-39 and table 2 PDF page 35").

Consequences on the level of evidence, marked for each value:

| Marker | Meaning |
|---|---|
| **[TRACÉ+CORROBORÉ]** | Value provided by the calling agent **and** identical in the prior repo trace → two concordant sources |
| **[TRACÉ-1SRC]** | Value from a single source (calling agent OR repo), not cross-checked |
| **[TO VERIFY]** | Not extractable here, or point not explicit → precise question posed |
| **[INTERPRÉTATION]** | Logical deduction on my part, distinct from the normative requirement |

No value below was invented or interpolated. **An actual PDF re-reading
(pages 35, 38, 39) remains required to lift the "I did not open the PDF" status.**

---

## 1. Cooling Selection Rule

### 1.1 Reference Machine Type (source: Tableau 2, §7.2.5.4 / §7.2.5.5)

| Cooling capacity `cooling_capacity_kw` | Reference machine | Article | Efficiency table(s) | Evidence |
|---|---|---|---|---|
| `< 150 kW` | Compression chiller, **AIR-cooled** | `# SIA 380/2:2022 7.2.5.4` | **Tableau 5** | **[TRACÉ-1SRC]** (agent) |
| `≥ 150 kW` | Compressor **WATER-cooled with dry post-cooler** | `# SIA 380/2:2022 7.2.5.5` | **Tableaux 6 and 7** | **[TRACÉ-1SRC]** (agent) |

**Exact threshold at 150 kW**: the calling agent noted "`< 150 kW` → air;
`≥ 150 kW` → water", hence **150 kW exactly → WATER**. I was unable to confirm the inequality
from the PDF. → **[TO VERIFY]**: does Tableau 2 indeed say "< 150 / ≥ 150" (and not
"≤ 150 / > 150")? This is load-bearing for a project whose capacity is exactly 150 kW.

### 1.2 Band-to-Capacity-Interval Mapping

Table notation (`≤12 / >12–50 / >50–150 / >150–450 / >450–1000 / >1000`) → intervals
**open on the left, closed on the right**:

| Band | Interval `P` [kW] | Evidence |
|---|---|---|
| B1 | `P ≤ 12` | [TRACÉ+CORROBORÉ] |
| B2 | `12 < P ≤ 50` | [TRACÉ+CORROBORÉ] |
| B3 | `50 < P ≤ 150` | [TRACÉ+CORROBORÉ] |
| B4 | `150 < P ≤ 450` | [TRACÉ+CORROBORÉ] |
| B5 | `450 < P ≤ 1000` | [TRACÉ+CORROBORÉ] |
| B6 | `P > 1000` | [TRACÉ+CORROBORÉ] |

**[INTERPRÉTATION]** The inclusivity (closed on the right `≤`, open on the left `>`) is deduced from
the notation ">12–50" (= `]12 ; 50]`). → **[TO VERIFY]**: confirm on the PDF the
handling of exact round values (12, 50, 150, 450, 1000 kW), in particular whether the
150 kW threshold from §1.1 coincides with the band boundary.

**Domain coverage asymmetry** (noted, not an error):
- Tableau 5 (AIR): bands B1→B5 (**no B6 band `>1000`**).
- Tableau 6 (WATER): bands B2→B6 (**no B1 band `≤12`**).

**[INTERPRÉTATION + TO VERIFY]** Tableau 6 contains bands B2/B3 (`<150 kW`) even though
the §1.1 rule only invokes water at `≥150 kW`. Consistent reading: the **selection** of
the machine type (air vs water) is governed by the 150 kW threshold from Tableau 2/§7.2.5.4-5;
the low bands in Tableau 6 serve other contexts within the standard (or the voluntary
water-project case). For reference project construction, only bands B4→B6 of
Tableau 6 are reached via the `≥150 kW` rule. → **[TO VERIFY]**: confirm that the
reference project never uses Tableau 6 below 150 kW.

### 1.3 Respective Roles of Tableaux 6 and 7 (`≥150 kW`)

**[TO VERIFY] — Tableau 7 NOT EXTRACTED.** Tableau 7 ("water-cooled chillers with
dry post-cooling", p38-39) is **absent from both sources** (calling agent:
cut off; repo trace: not extracted). I cannot freeze it.
Specific questions for the PDF re-reading:
- Q7.1: does Tableau 7 give the EER/SEER of the **combination** water chiller +
  dry post-cooler, or only the **derating** due to post-cooling?
- Q7.2: at `≥150 kW`, is the substitution value taken from Tableau 6,
  Tableau 7, or a composition of both (§7.2.5.5)?
- Q7.3: Tableau 7 power bands (same as Tableau 6: B2→B6? or B4→B6?).

---

## 2. Heating Selection Rule

### 2.1 DIFFERENT Types for Limit and Target (source: Tableau 2, §7.2.5.8 / §7.2.5.9)

| Level | Reference system | Table | Evidence |
|---|---|---|---|
| **Ref. LIMIT** | **Air-to-water** heat pump | **Tableau 8** | **[TRACÉ+CORROBORÉ]** |
| **Ref. TARGET** | **Ground-source (brine-to-water)** heat pump | **Tableau 9** | **[TRACÉ+CORROBORÉ]** |

**Confirmed**: limit and target rely on **different generator types** (air-to-water
vs brine-to-water) **and different tables** (8 vs 9). This is therefore not the same machine
read at two columns: these are two distinct reference machines. Compared variable:
`heating_capacity_kw` determines the band in each table.

**[TO VERIFY]** Exact articles: the statement places heating generation at §7.2.5.8/9
based on the §7.2.5.4-9 range. I have not confirmed the specific article number attached to
Tableaux 8 and 9 (§7.2.5.8 vs §7.2.5.9) → confirm on PDF p39.

### 2.2 Heating Capacity Bands

| Table | Bands present | Evidence |
|---|---|---|
| Tableau 8 (air-to-water, limit) | B1 `≤12`, B2 `12–50`, B3 `50–150` (**stops at 150 kW**) | [TRACÉ+CORROBORÉ] |
| Tableau 9 (brine-to-water, target) | B2 `12–50`, B3 `50–150`, B4 `150–450`, B5 `450–1000`, B6 `>1000` | [TRACÉ+CORROBORÉ] |

**[TO VERIFY] — limit/target domain asymmetry.** Tableau 8 (limit) stops at
150 kW; Tableau 9 (target) covers up to `>1000 kW` but **only starts at 12 kW**.
Two zones without direct correspondence:
- `P > 150 kW`: no tabulated air-to-water LIMIT value → how is the limit set beyond
  150 kW? (reference to §7.2.5.7 detailed calculation? other table?)
- `P ≤ 12 kW`: no tabulated brine-to-water TARGET value → what target below 12 kW?
Both points must be resolved by PDF re-reading before wiring.

---

## 3. Direction of Comparison

**Confirmed: the reference value is a MINIMUM THRESHOLD** — the project generator is
compliant if its efficiency is **`≥`** the table value (EER, SEER and SCOP are
efficiency coefficients: "higher = better").

- Basis: columns are named "Grenzwert" (= floor not to be crossed downward)
  and "Zielwerte" (more demanding objective, hence higher). Consistent with the
  numbers: target > limit in every band (e.g. air B1: EER 3.10 target > 2.90 limit).
- **[INTERPRÉTATION]** The physical direction (increasing COP/EER/SEER/SCOP = more efficient) is
  unambiguous; the direction `project ≥ reference` follows from it.

**[TO VERIFY] — comparison method (Pathway A vs Pathway B).** Two possible readings,
not resolved here for lack of access to the §7.2.5 text:
- Pathway A (direct comparison): `EER_project ≥ EER_limit` and `SEER_project ≥ SEER_limit`.
- Pathway B (reference project): a reference machine is **constructed** to which the
  table value is **assigned**, then simulated energy demands are compared.
The frozen variable is the same (table value); the substitution mechanics differ.
`validation-engine-engineer` must know which one before wiring. → confirm on PDF.

---

## 4. Exact Compared Variable: Full-Load EER vs SEER

### 4.1 The Tables Provide TWO Variables

For cooling, each band provides **both**:
- **Full-load EER** (nominal point),
- **SEER** seasonal, referenced to **`SN EN 14825`** (mention noted by the agent).

→ **[TO VERIFY]** Which is the reference project substitution variable — EER
alone, SEER alone, or **both simultaneously**? Both columns exist, so a priori
**both constraints apply**; the §7.2.5.4-5 text must confirm this. SEER
(seasonal) is the relevant index for annual energy; full-load EER is the
design point.

### 4.2 SEER (SN EN 14825) ↔ VE-extracted `seer` Correspondence — NOT PROVEN

`swiss_sia/model_analyzer.py` (l.681-682, l.698-699) extracts:
- `seer = cooling.get("SEER")` (VE `VEApacheSystem.cooling()`, [PDF VEScripts p.182]);
- `sseer = cooling.get("SSEER")` (seasonal **system** efficiency, auxiliaries included).

→ **[TO VERIFY]** Is the `SEER` index returned by the IESVE API **defined/measured according to
`SN EN 14825`** (same boundary conditions, same part-load points, same
climate weighting)? **Nothing proves it**:
- The `SN EN 14825` PDF **is not present in `/refs`** → I can neither cite nor verify
  the normative definition of SEER. **Missing EN standard flagged.**
- The adapter extraction contract (`traceability/sia380-2-adapter-extraction-contract.spec.md`
  §4) marks `SEER` as `[EXPOSÉ]` but **without proof of EN 14825 conformity**.
As long as unproven: **do not equate `seer` (VE) with SEER (SN EN 14825)**.

→ **[TO VERIFY] secondary**: should the comparison be on `seer` (generator) or
`sseer` (system, auxiliaries §7.2.5.6 included)? SIA 380/2 integrates post-cooling
auxiliaries (§3 below), which could point toward a "system" index.

---

## 5. Machine-Readable Tables 5-9

> All cooling values below are **[TRACÉ+CORROBORÉ]** (calling agent AND
> `docs/project/SIA_3802_4010_PDF_TRACEABILITY.md` §7, l.122-151, concordant).
> Normative locator: `# SIA 380/2:2022 Tableau N`, PDF pages 38-39 (cooling/heating),
> Tableau 2 PDF page 35 (selection). **Pages not re-verified by me (see §0).**
> EER/SEER/SCOP unit = kW/kW (dimensionless). Decimal separator normalised to period.

### 5.1 Tableau 5 — Cooling, AIR-cooled chillers (`# SIA 380/2:2022 Tableau 5`, p38)

| band_id | p_min_kw | p_max_kw | eer_full_load_limit | seer_limit | eer_full_load_target | seer_target |
|---|---|---|---|---|---|---|
| B1 | 0 | 12 | 2.90 | 3.80 | 3.10 | 4.20 |
| B2 | 12 | 50 | 3.00 | 3.90 | 3.15 | 4.35 |
| B3 | 50 | 150 | 3.10 | 4.00 | 3.20 | 4.50 |
| B4 | 150 | 450 | 3.20 | 4.20 | 3.40 | 4.80 |
| B5 | 450 | 1000 | 3.40 | 4.40 | 3.60 | 5.00 |

`p_min` exclusive, `p_max` inclusive (cf. §1.2). Selection: AIR type iff `cooling_capacity_kw < 150`.

### 5.2 Tableau 6 — Cooling, WATER-cooled chillers (`# SIA 380/2:2022 Tableau 6`, p38)

| band_id | p_min_kw | p_max_kw | eer_full_load_limit | seer_limit | eer_full_load_target | seer_target |
|---|---|---|---|---|---|---|
| B2 | 12 | 50 | 4.05 | 4.50 | 4.45 | 5.90 |
| B3 | 50 | 150 | 4.25 | 4.80 | 4.65 | 6.10 |
| B4 | 150 | 450 | 4.65 | 5.50 | 5.05 | 6.90 |
| B5 | 450 | 1000 | 5.05 | 6.10 | 5.50 | 7.40 |
| B6 | 1000 | null | 5.50 | 6.70 | 6.00 | 8.00 |

Selection: WATER type iff `cooling_capacity_kw ≥ 150` (see also Tableau 7, §1.3).

### 5.3 Tableau 7 — Cooling, WATER with dry post-cooling (`# SIA 380/2:2022 Tableau 7`, p38-39)

**[TO VERIFY] — NOT EXTRACTED.** Absent from both sources. Table to be frozen after PDF re-reading.
Expected structure (to be confirmed): same EER/SEER columns (limit/target) as Tableau 6,
bands ≥ B4 (`≥150 kW`). See questions Q7.1-Q7.3 (§1.3).

### 5.4 Tableau 8 — Heating, air-to-water heat pump — ref. LIMIT (`# SIA 380/2:2022 Tableau 8`, p39)

| band_id | p_min_kw | p_max_kw | scop_limit | scop_target |
|---|---|---|---|---|
| B1 | 0 | 12 | 3.00 | [TO VERIFY] |
| B2 | 12 | 50 | 3.10 | [TO VERIFY] |
| B3 | 50 | 150 | 3.20 | [TO VERIFY] |

SCOP per **`SN EN 14825`** (mention noted). "Target" column: the repo trace indicates
"not given in the extracted table" (l.144-146) → **[TO VERIFY]**: does Tableau 8 have
a target column, or is the heating target **exclusively** carried by Tableau 9
(brine-to-water) in accordance with §2.1? Reading consistent with §2.1: the air-to-water
target does not exist because the target = brine-to-water. **[INTERPRÉTATION]** to be confirmed.

### 5.5 Tableau 9 — Heating, brine-to-water heat pump (ground source) — ref. TARGET (`# SIA 380/2:2022 Tableau 9`, p39)

| band_id | p_min_kw | p_max_kw | scop_limit | scop_target |
|---|---|---|---|---|
| B2 | 12 | 50 | 4.00 | 4.40 |
| B3 | 50 | 150 | 4.20 | 4.60 |
| B4 | 150 | 450 | 4.60 | 5.00 |
| B5 | 450 | 1000 | 5.00 | 5.50 |
| B6 | 1000 | null | 5.50 | 6.00 |

**[TRACÉ+CORROBORÉ]** via repo trace §7 (l.147-151), which completes the bands not provided
by the calling agent. **[TO VERIFY]**: does Tableau 9 carry **two** columns
(limit AND target)? The repo trace names them "SCOP limite / SCOP cible", suggesting
that the brine-to-water table itself contains both a limit AND a target — to be reconciled with
§2.1 (where table 9 = ref. target). Open question for the re-reading.

---

## 6. Auxiliaries and Method (§7.2.5.6 / §7.2.5.7)

**[TRACÉ-1SRC — NOT RE-VERIFIED]** (calling agent only, not cross-checked, not opened by me):

- `# SIA 380/2:2022 7.2.5.6` — post-cooling auxiliaries (energy share):
  fans **3.6 %**, pumps **1.2 %**, chilled water pump **1.5 %**.
  → **[TO VERIFY]** exact calculation basis (% of what: cooling energy? capacity?).
- `# SIA 380/2:2022 7.2.5.7` — method: **Annex A** + **`SN EN 16798-13:2017`**,
  tables **NA.3** and **NA.4**.
  → **Missing EN standard flagged**: `SN EN 16798-13:2017` **is not in `/refs`** →
  tables NA.3/NA.4 **cannot be cited or verified** here. Must be obtained before any wiring
  of this method.

---

## 7. Summary for reference-data-engineer / validation-engine-engineer

### 7.1 Selection Rules

- **COOLING**: `cooling_capacity_kw < 150` → **AIR / Tableau 5**; `≥ 150` → **WATER with
  dry post-cooler / Tableaux 6 (+7)**. Bands `]p_min ; p_max]`. Type determined
  by the 150 kW threshold (Tableau 2/§7.2.5.4-5); band by capacity.
- **HEATING**: ref. **LIMIT = air-to-water heat pump / Tableau 8** (bands up to 150 kW); ref.
  **TARGET = brine-to-water heat pump / Tableau 9** (bands 12 kW → >1000 kW). Types and tables
  **different** between limit and target — confirmed.
- **Direction**: reference = **minimum threshold**; compliant if `project_efficiency ≥ table_value`
  (increasing EER, SEER, SCOP = better) — confirmed.

### 7.2 Compared Variable

- Cooling: the tables give **full-load EER AND SEER (SN EN 14825)**; both
  constraints probably apply (**[TO VERIFY]** which is the primary substitution).
- **Do not** equate `seer` extracted from VE with SEER `SN EN 14825` without proof
  (**[TO VERIFY]**; `SN EN 14825` absent from `/refs`). `seer` vs `sseer`
  (auxiliaries) arbitration also open.

### 7.3 List of [TO VERIFY] (specific questions)

1. 150 kW cooling threshold: "< 150 / ≥ 150" vs "≤ 150 / > 150"? (§1.1)
2. Band boundary inclusivity at round values 12/50/150/450/1000 kW. (§1.2)
3. **Tableau 7 entirely unextracted**: values, bands, and role vs Tableau 6 at `≥150 kW`
   (Q7.1-Q7.3). (§1.3, §5.3)
4. Zone `P > 150 kW` without air-to-water limit (Tableau 8): where does the limit come from? (§2.2)
5. Zone `P ≤ 12 kW` without brine-to-water target (Tableau 9). (§2.2)
6. Comparison method: Pathway A (value vs threshold) or Pathway B (constructed reference
   project)? (§3)
7. Cooling substitution variable: EER, SEER, or both? (§4.1)
8. `seer` (VE) ≡ SEER `SN EN 14825`? — **`SN EN 14825` absent from `/refs`**. (§4.2)
9. Comparison on `seer` (generator) or `sseer` (system + auxiliaries §7.2.5.6)? (§4.2)
10. Does Tableau 8 have a target column, or is the heating target solely in Tableau 9? (§5.4)
11. Does Tableau 9 carry both limit **and** target, to be reconciled with "Tableau 9 = ref. target"? (§5.5)
12. Exact articles for Tableaux 8/9 (§7.2.5.8 vs §7.2.5.9). (§2.1)
13. §7.2.5.6: calculation basis for the auxiliary percentages. (§6)
14. §7.2.5.7: **`SN EN 16798-13:2017` absent from `/refs`** — NA.3/NA.4 cannot be cited. (§6)
15. **Cross-cutting confirmation**: actual PDF re-reading of pages 35/38/39 (not opened in
    this session, cf. §0).

### 7.4 Missing EN Standards in `/refs` (external blocker)

| Standard | Required by | Impact |
|---|---|---|
| `SN EN 14825` | SEER/SCOP definition in Tableaux 5-9 | `seer`(VE)↔SEER correspondence unverifiable |
| `SN EN 16798-13:2017` | method §7.2.5.7 (tables NA.3/NA.4) | method not citable |

---

## 8. Sources

| Source | Location | Usage |
|---|---|---|
| Calling agent (`[TRACÉ PDF]`) | task message | Tableaux 2, 5, 6, 8, 9 (partial) values, §7.2.5.6-7 |
| `docs/project/SIA_3802_4010_PDF_TRACEABILITY.md` §7 | repository, l.116-163 | corroboration Tableaux 5, 6, 8; completion Tableau 9 |
| `swiss_sia/model_analyzer.py` | repository, l.680-701 | extracted project fields (eer, seer, sseer, scop, capacities, classes) |
| `traceability/sia380-2-adapter-extraction-contract.spec.md` §4-5 | repository | VE API members (nominal_eer, SEER, SSEER, SCoP) and NCM/UK caveat |
| `refs/SIA-380-2-2022.pdf` | repository | **NOT OPENED in this session** (see §0) — re-reading pages 35/38/39 required |
