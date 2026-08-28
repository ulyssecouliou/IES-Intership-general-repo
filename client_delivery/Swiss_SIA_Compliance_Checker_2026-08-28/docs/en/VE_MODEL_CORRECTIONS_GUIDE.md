# VE Model Corrections Guide — SIA 380/2:2022 Compliance

This guide lists, criterion by criterion, **what to modify** to resolve `NOT_CHECKABLE` / `PARTIAL` verdicts in a client model, with **two paths** :

- **VE Path** — editing the model in the IESVE interface (genuinely improves the actual model).
- **CSV Path** — reviewer evidence in `sia4010_evidence/` (guaranteed path, supported by the tool).

VE menu labels may vary depending on version — verify them on screen;
the locations below are indicative (validated on VE 2025.2).

> **Integrity Rule.** A criterion passes **OK** only with (1) **real values**
> (VE or manufacturer datasheet) and (2) for the CSV path, `review_status=accepted` **signed
> by a reviewer**. Example values in `pending` remain `NOT_CHECKABLE` :
> this is intentional — the tool never manufactures compliance.

After each batch of modifications: rerun **`Run_VE_Swiss_Compliance.py`** and
watch the manifest tally evolve.

---

## 1. Thermal bridges ψ/χ — `SIA3802_THERMAL_BRIDGES`

**Direct VE reading** (VE 2025.2: `VESurface.get_thermal_bridges_non_repeating/_random`).
The criterion is **OK** as soon as at least one junction has a non-zero ψ; the tool calculates
`H_tb = Σ(ψ·L·flux) + Σ(χ·count)` in W/K. Junctions left at **ψ=0** are
flagged (possible unmeasured defect) — correct to avoid underestimation.

**VE Path** :
1. `Apache` → **Construction Database Manager** → tab **Thermal Bridges**
   (or the Thermal Bridges dialogue at model level).
2. For each **junction type with ψ=0** (lintel, jamb/reveal, sill/spandrel,
   wall-roof, wall-partition…), enter the ψ (W/m·K) from a **SIA catalogue** or
   a calculation (building physics engineer).
3. Save. Verify with the read-only probe
   `Run_VE_SIA3802_Probe_Thermal_Bridges.py` (lists each ψ + total H_tb).

**CSV Path (fallback, older VE)** : `SIA3802_thermal_bridges_<project>.csv`
(method + total ψ.L+χ W/K OR schema reference + reviewer + date + source).

---

## 2. Cooling generator — SEER — `SIA3802_COOLING_EER_SEER`

Autosize obscures the capacity → the SIA 380/2 tables 5/6 band cannot be resolved from
the model. A **declared SEER** (ErP/Ecodesign datasheet, SN EN 14825:2018) is compared
properly against the band.

**VE Path** :
1. `Apache` → **Apache Systems / ApacheHVAC** → cooling generator (chiller).
2. **Disable autosize** of the capacity → enter the **nominal capacity (kW)**.
3. If a **Seasonal EER / SEER** field exists, enter the SEER from the datasheet
   (otherwise → CSV path).

**CSV Path** : `SIA3802_cooling_generators_<project>.csv`
- `generator_class` = `air_cooled` or `water_cooled`
- `capacity_kw`, `seer` (manufacturer datasheet), `nominal_eer` optional
- `review_status` : `pending` → **`accepted`** (reviewer + date + real source)

**SEER thresholds (SIA 380/2:2022 tables 5 & 6, limit values)** :

| Power kW | ≤12 | >12–50 | >50–150 | >150–450 | >450–1000 | >1000 |
|---|---|---|---|---|---|---|
| **Air** (Table 5) | 3.80 | 3.90 | 4.00 | 4.20 | 4.40 | — |
| **Water** (Table 6) | — | 4.50 | 4.80 | 5.50 | 6.10 | 6.70 |

*(Water cooler + dry cooling = Table 7 EER+, outside SEER scope.)*

---

## 3. AHU / Heat recovery — `SIA3802_AHU_HEAT_RECOVERY`

**VE Path** :
1. `Apache` → **Apache Systems / ApacheHVAC** → the **AHU**.
2. On the **heat recovery exchanger** : **temperature effectiveness** (η, e.g. 0.78),
   **type** (plate / rotary wheel).
3. Fill in **pressure drop** and **SFP** if fields exist.

**CSV Path** : `SIA3802_ahu_heat_recovery_<project>.csv`
(sealing class + recovery η = quantum Table 4 ; Δp and SFP optional ;
`pending` → `accepted`).

---

## 4. Ventilation control — `SIA3802_VENTILATION_CONTROL`

**VE Path** :
1. `Apache` → AHU ventilation system (or per-room).
2. Fill in **system type** (single-zone/multi-zone) + **control strategy**
   (constant / demand-controlled / CO₂). The tool reads control identifiers from
   the Apache system.

**CSV Path** : `SIA3802_ventilation_control_<project>.csv`
(type + control class + flow band ≤3 / 3-6 / >6 m³/h·m² ;
`pending` → `accepted`).

---

## 5. Solar protection — `SIA3802_SOLAR_PROTECTION_CONTROL`

**VE Path (recommended)** :
1. `Apache` → **Construction Database Manager** → **Glazing** construction →
   sections **External / Internal / Local shade**.
2. Activate a **blind** (e.g. external Venetian blind), fill in its
   optical properties and **g_total with blind**.
3. Attach a **control strategy** (schedule / irradiance threshold) to windows.

**CSV Path** : `glazing_solar_protection_<project>.csv`
(type + g_total + control, by façade). ⚠️ Credit requires that reviewed windows
**cover all external windows** seen by VE (otherwise PARTIAL).

---

## 6 & 7. Out of scope for model editing

- **Lighting** — `SIA3802_LIGHTING_CONTROL` (PARTIAL) : blocked by the absence of
  **SIA 387/4** (normative source). No VE editing can unblock it
  until the standard is acquired.
- **Design Power** — `SIA3802_DESIGN_POWER_DAYS` (NOT_AVAILABLE) :
  requires dedicated design-day simulations + tool development (reading `.aps` files
  from sizing days). Not a simple model edit.

---

## Decisive vs Diagnostic

SIA 380/2 compliance is decided on the **global project/reference comparison
(§ 7.2.5.2)**, provided and accepted by a reviewer
(`SIA3802_global_reference_comparison_<project>.csv`). The criteria above are
**diagnostics** : they enrich the file, but do not decide compliance alone. See `docs/project/GUIDE_COMPARAISON_GLOBALE_SIA3802.md`.
