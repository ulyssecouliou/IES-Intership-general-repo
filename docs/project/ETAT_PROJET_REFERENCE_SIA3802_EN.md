> **Note:** Translated from French original. See [ETAT_PROJET_REFERENCE_SIA3802.md](ETAT_PROJET_REFERENCE_SIA3802.md) for the source document.

# Status report -- SIA 380/2 reference project

## Executive summary

The **SIA 380/2 reference project** input specification is an automated Python component that prepares the decisive comparison required by `# SIA 380/2:2022 7.2.5.2`: overall compliance holds if the project energy demand **is lower** than that of the reference project. The component is **functional, tested and delivered**; it produces a deterministic specification of the substitutions to apply (envelope, windows, infiltration, generation, usage). **Eight of the fourteen input families are automated**; six remain blocked, either because the standard was not supplied (`# SIA 380` for overall aggregation), because no API exists to expose them (`# SIA 387/4` for lighting), or by architectural choice (a real VE probe is required for ventilation). **Decision of 2026-08-20: no paid standard will be purchased to lift these two documentary gaps.** The affected checks therefore remain outside the verdict scope, with no reconstructed value. **Two strictly downstream executable blockers** bar a client verdict: the definition of the SIA 380 overall index and a VE reference-model builder (separate, requires real VE).

---

## Normative context

- **Decisive pathway**: `# SIA 380/2:2022 7.2.5.2` -- "the overall performance is met when the project value according to chapter 6 is **lower** than the corresponding limit or target value of the **reference project**". Binary verdict, calculated bound, not a SIA constant.
- **Link to SIA 4010 validation**: `# SIA 380/2:2022 6.2.2.1` -- a calculation method is only admissible if it "can demonstrate **validation according to SIA 4010** for the systems under consideration". SIA 380/2 compliance therefore **presupposes** SIA 4010 validation of the tool (IESVE/ApacheSim).
- **Reference project composition**: `# SIA 380/2:2022 7.2.5.3` -- geometry, usage and climate identical to the project; **only Table 2 data** (envelope, generation, emission, SIA 2024 setpoints/gains) are substituted.

---

## Status of the 14 input families -- Table 2 + Tables 3-9 (SIA 380/2:2022)

| # | Input family | SIA source | Status | Unblockers / Blocking cause |
|---|---|---|---|---|
| **1** | Opaque envelope (U walls/roofs/floors) | Table 3, pp. 36-37 | **AUTOMATED** | VE U-value extraction (ModelAnalyzer API). Full tests. |
| **2** | Windows U + frame fraction | Table 2, pp. 32-33 | **AUTOMATED** | VE U and frame_fraction extraction (OpeningData API). Full tests. |
| **3** | Glazing g-perp (solar factor) + tau (visible transmittance) | Table 2, pp. 32-33 | **AUTOMATED** | VE solar_factor extraction (EN 410 proven) + visible_transmittance. Full tests. |
| **4** | Infiltration (0.15 m3/(h*m2)) | Table 2, pp. 32-33 | **AUTOMATED** | VE extraction in net m3/(h*m2). Strict unit, no extrapolation. Full tests. |
| **5** | Cooling (air generator EER) | Tables 5-9, pp. 38-39 | **AUTOMATED** | VE capacity + EER extraction (SIA bands <=150 kW encoded). [CAVEAT] SN EN 14825 absent from `/refs` -- SEER/SCoP VE equivalence unproven [TO VERIFY]. Full tests. |
| **6** | Heating (air-water heat pump SCOP) | Tables 8-9, pp. 38-39 | **AUTOMATED** | VE capacity + SCOP extraction (SIA bands <=150 kW encoded). [CAVEAT] SN EN 14825 absent -- SCOP VE equivalence unproven [TO VERIFY]. Full tests. |
| **7** | Convective emission + unlimited capacity | Table 2, pp. 32-33 | **AUTOMATED** | Prescriptive SIA directive (stated value, never compared), resolved as REFERENCE_DIRECTIVE status. Full tests. |
| **8** | Setpoints theta/phi + internal gains (A_p, M, p_Be, E_vm) -- SIA 2024 identical project/reference | Table 2 -> SIA 2024, `# 7.2.5.3` [TRACED] | **AUTOMATED** | SIA 2024:2021 JSON data frozen in `/refs`; `# 7.2.5.3` guarantees project/reference identity -> no differentiating substitution. Full tests. |
| **9** | Thermal bridges (psi=0, chi=0) | Table 2, pp. 32-33 | **NOT AUTOMATED** | **Cause**: VEScripts API does not expose them. Evidence: API review, no capability to readback psi/chi per construction. |
| **10** | Glazing ratio (fg) + solar protections | Table 2 + Table 10 + SIA 387/4 | **NOT AUTOMATED** | **Cause**: SIA 2024 reference (Glasanteil, col9) traced, but the **project** quantity is not exposed -- the model's WWR (window/wall) != Glasanteil (glass only). Linking the two would be a false mapping. Unblocker: exact definition of fg + extraction of a compliant project glass fraction. |
| **11** | Lighting power (pLi) + controls | Table 2 -> SIA 387/4 | **NOT AUTOMATED** | **Cause**: standard **SIA 387/4 absent from `/refs`**. Lighting input table SIA 387/4 Table 9/10 inaccessible. Documentary blocker. |
| **12** | Ventilation (epsilon_V; classes C/L2/L1; U_ahu) | Table 2 + Table 4; `# 7.1.1` -> SIA 382/1 | **NOT AUTOMATED** | **Cause**: NCM/UK context (centralised system, annual profile), real VE probe required. Architecture: separate component needed (independent of this module). |
| **13** | Photovoltaics (installed power, efficiency) | Table 2, pp. 32-33 | **NOT AUTOMATED** | **Cause**: SIA reference frozen (10 W/m2 SRE at 90% system efficiency). Project value requires VE probe. Architecture: separate component needed (independent of this module). |
| **14** | SIA 380 overall index (annual aggregation/weighting) | `# SIA 380/2:2022 6.1.2`, delegated to **SIA 380** | **NOT AUTOMATED** | **Cause**: **standard SIA 380 absent from `/refs`**. Overall index unit/definition inaccessible. Major normative blocker (see Blockers section). |

---

## Status detail

### Automated families (8)

**Active components, validated tests**:

- **Envelope, windows, glazing** (1-3): deterministic extraction of U-values and properties from the VE model, matching `# SIA 380/2:2022 Table 3, pp. 36-37` and `# Table 2, pp. 32-33`. Direct substitution, no interpolation.
- **Infiltration** (4): differentiating substitution -- project value (zone maximum, net m3/(h*m2), strict unit) compared against the reference `# SIA 380/2:2022 Table 2` of 0.15 m3/(h*m2). A project value in a different unit is a conversion blocker, never silently substituted.
- **Generation** (5-6): project capacity determines the SIA table 5-9 band. EER/SCOP encoded, never extrapolated. **Important caveat**: SN EN 14825 (SEER/SCOP definition) is absent; the VE properties named `eer` and `scop` are accepted as-is, equivalence unproven [TO VERIFY].
- **Emission + capacity** (7): prescriptive SIA (no project value), resolved as a directive.
- **SIA 2024 -- standard usage** (8): `# SIA 380/2:2022 7.2.5.3` guarantees that SIA 2024 setpoints, airflows and gains are **identical** between project and reference. SIA 2024:2021 JSON frozen in `/refs`. No differentiating substitution (even though it passes through the specification, it affects no delta).

**All tested** (`tests/test_reference_project.py`, classes `SurfaceSubstitutionTests`, `OpeningSubstitutionTests`, `InfiltrationSubstitutionTests`, `GenerationSubstitutionTests`, `ReferenceDirectiveTests`, `UsageStandardInputTests`).

### Non-automated families (6)

**Causes and explicit unblockers**:

#### Thermal bridges (9)
- **SIA 380/2:2022 Table 2, pp. 32-33**: psi = 0 W/(m*K), chi = 0 W/K (limit and target identical).
- **Blocker**: IESVE/VEScripts API does not expose them (upstream capability review).
- **Unblocker**: VEScripts API extension for psi/chi readback per construction.

#### Glazing ratio + solar protections (10)
- **SIA 380/2:2022 Table 2, pp. 32-33**: fg ("glazed surface ratio") -> reference **SIA 2024**; project = "project-specific" (differentiating substitution).
- **Blocker** (norm-analyst verdict, `traceability/sia380-2-pathway.spec.md` section 8.1): the SIA 2024 reference is traced (Glasanteil, col9), but **the project quantity is not exposed**. The model computes a WWR = window/wall; the Glasanteil isolates the **glass** from the frame (via Fw col10) and uses a different denominator. WWR != fg: linking them would be a false mapping, which is prohibited.
- **Unblocker**: the exact definition of fg (numerator glass vs window; denominator facade/SRE) then extraction of a compliant project glass fraction (`[TO VERIFY]` i, j).

#### Lighting (11)
- **SIA 380/2:2022 Table 2, pp. 32-33**: pLi (nominal lighting power) and controls (categories 4/2, controls 2/3) -> **SIA 387/4**.
- **Blocker**: standard **SIA 387/4 absent from `/refs`**. Lighting input table not located.
- **Project decision (2026-08-20)**: no purchase. This family stays `NOT_CHECKABLE`; only a controlled link under a licence supplied by IES or a reviewer could reopen it.

#### Ventilation (12)
- **SIA 380/2:2022 Table 2 + Table 4, pp. 32-33 and p. 37; `# 7.1.1` -> SIA 382/1**.
- **Blocker**: system design (efficiency epsilon_V, airtightness classes C/L2/L1, U_ahu). NCM/UK context (centralised network) requires a real VE probe (air_handler.efficiency, duct_classes, annual_profile).
- **Unblocker**: separate VE component for ventilation (independent of this module). Requires real VE.

#### Photovoltaics (13)
- **SIA 380/2:2022 Table 2, pp. 32-33**: nominal installed power, system efficiency.
- **Blocker**: **frozen SIA reference** (10 W/m2 SRE, 90% efficiency). Project value requires VE probe (roof, tilt, shading, panel model).
- **Unblocker**: separate VE component for PV (independent of this module). Requires real VE.

#### SIA 380 overall aggregation (14)
- **SIA 380/2:2022 6.1.2**: "annual aggregation and weighting are performed **according to SIA 380**" (standard absent).
- **Major blocker**: **energy expenditure index unit** (SIA 380/2:2022 6.1.4) not defined in 380/2 (delegated to SIA 380). No fixed kWh/m2: it is a weighted calculated index. Formula unknown.
- **Project decision (2026-08-20)**: no purchase. Automatic aggregation stays out of scope; a complete index, with unit, source and reviewer approval, can still be imported through the existing evidence path.

---

## Two strictly downstream executable blockers

The `swiss_sia/reference_project.py` component produces an **input specification**, never a verdict. Two downstream steps remain **necessary** for an executable client verdict:

### Blocker 1: SIA 380 index unit [OUT OF ACQUISITION SCOPE]

**Description**: The `# SIA 380/2:2022 7.2.5.2` criterion compares two indices: `project_index < reference_index`. Both indices are constructed per `# 6.1.4` ("energy expenditure index **according to SIA 380**"). But SIA 380 is **absent** (not supplied as of 2026-08-14).

**Impact**: Impossible to express the verdict in a comprehensible unit/scale (kWh/m2/year? points? consumption class?). The numerical comparison is executable in code, but **not communicable** to a client without a unit.

**Approach adopted**: do not calculate or guess this index. Accept only a complete reviewed result (metric, scope, project/reference values, unit, source, reviewer and date) through the existing overall comparison CSV.

### Blocker 2: VE reference-model builder [ARCHITECTURE DEPENDENCY]

**Description**: The `reference_project.py` component produces a **specification** (list of substitutions). What remains:
1. **Build** the VE reference model (copy the project + apply the Table 2 substitutions).
2. **Run** the VE/ApacheSim simulation (energy run).
3. **Extract** the energy demand (SIA 380 index of the reference project).

This builder is a **separate component**, requires a **real VE probe** (IESVE.exe or VEScripts.IVEProject), and falls outside this module (pure Python).

**Impact**: Without this builder, the reference run will not be launched automatically. Even with a complete specification, the SIA 380/2 verdict remains blocked.

**Unblocker**: Development of the VE-builder component (outside the scope of the pure `engine/` module). To be placed in `ve_adapter/` or a dedicated UI script.

---

## Documented reservations

### SN EN 14825 caveat -- SEER/SCOP definition

`# SIA 380/2:2022 Tables 5-9, pp. 38-39` specify EER (air chiller <150 kW) and SCOP (air-water heat pumps <=150 kW) according to **SN EN 14825** (edition not determined here), a standard absent from `/refs`.

**Consequence**: The quantities named `eer` and `scop` in the VE model are accepted *in extenso*. No equivalence verification between:
- SN EN 14825 definitions (EN standards).
- IESVE/ApacheSim implementation.

**Marked**: `[TO VERIFY]` in the code, recorded in the source of each generation SCOP substitution (`reference_project.py`, `_generation_substitution`).

### SIA data licence

The files `sia-2024-2021.usage-data.json` and SIA 380/2 tables encoded in `config.py` are provided under **IES licence**. No redistribution extends beyond the internal use of the repository.

### These specifications are not a compliance conclusion

`# SIA 380/2:2022 7.2.5.1-7.2.5.3`: the reference project is a **bound calculation** (the limit). Compliance follows only if:
1. The **project run** has been launched (demand calculated, chapter 6).
2. The **reference run** has been launched (bound demand, Table 2 applied).
3. The two have been **compared** (`project_index < reference_index`).
4. A **review** gate has accepted the result (evidence_manager, qa-auditor).

The `reference_project.py` specification = step 1 of 4. Never a standalone verdict.

---

## Summary for management

| Aspect | Status |
|---|---|
| **`reference_project.py` component** | **Delivered, tested, active** -- exports a deterministic specification. |
| **Family automation / 14** | **8 / 14** -- envelope, windows, glazing, infiltration, generation, emission, SIA 2024 usage. |
| **VEScripts API obstacles** | **1**: thermal bridges (psi/chi not exposed). |
| **Documentary normative obstacles** | **2**: SIA 387/4 (lighting) + SIA 380 (overall index) absent. |
| **Design obstacles** | **3**: fg (project quantity not exposed -- WWR != Glasanteil); ventilation (real probe); PV (real probe). |
| **Executable client verdict?** | **NO** -- 2 downstream blockers: (1) SIA 380 index out of acquisition scope, unless reviewed evidence imported; (2) separate VE-builder required. |
| **Release timeline?** | Depends on the VE-builder and, for an overall verdict, on a complete index supplied and approved externally. No technical dependency on reference_project.py. |

---

## References

- `# SIA 380/2:2022 7.2.5` -- Pathway B, project/reference comparison (PDF pages 33-35).
- `# SIA 380/2:2022 7.2.5.3` -- Identical project/reference composition, Table 2 substituted (PDF page 34).
- `# SIA 380/2:2022 6.1.2, 6.1.4` -- Aggregation and overall index, delegated to SIA 380.
- `# SIA 380/2:2022 6.2.2.1` -- SIA 4010 validation requirement (PDF page 25).
- `traceability/sia380-2-pathway.spec.md` -- In-depth SIA 380/2 pathway analysis (16 [TO VERIFY] questions listed).
- `swiss_sia/reference_project.py` -- Implementation of substitution collectors (one per family).
- `tests/test_reference_project.py` -- Suite covering surfaces, windows, glazing, infiltration, generation, directives and SIA 2024 usage.

---

**Author**: Claude Code, for IES management review  
**Date**: 2026-08-14  
**Audience**: Management, non-code-specialists  
**Status**: Traceable, honest, readable
