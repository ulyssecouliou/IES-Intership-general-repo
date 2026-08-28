> **Note:** Translated from French original. See [sia380-2-adapter-extraction-contract.spec.md] for the source document.

# VE Adapter Extraction Contract — SIA 380/2 Table 2 Families Not Yet Automated

> Status: **TRACED FEASIBILITY** — direct reading of the PDF `refs/VEScripts-API-VE2023.pdf`
> (248 pages, PyMuPDF extraction). No API member is cited without a source page number.
> Any member assumed but not located in the PDF is explicitly marked.
> Author: `ve-adapter-engineer`, 2026-08-14.
> Scope: SIA 380/2:2022 Table 2 families absent from `IMPLEMENTED_REFERENCE_INPUT_FAMILIES`
> in `swiss_sia/reference_project.py`. This document is a **feasibility contract**,
> not code. No production adapter code is written here.

---

## 0. Marking Conventions

| Marker | Meaning |
|---|---|
| **[PDF p.N]** | Member found in the PDF, exact page N |
| **[EXPOSÉ]** | Member documented in the PDF, extractable via API |
| **[EXPOSÉ-NCM/UK]** | Exposed but in `*_ncm()` methods: UK Building Regulations data — semantic correspondence with SIA 380/2 parameters to be confirmed by real VE probe |
| **[NON EXPOSÉ]** | Term absent from the PDF, no candidate member found |
| **[NÉCESSITE SONDE VE]** | Plausible candidate member but not located, or instantiation not documented |
| **capability-check + readback** | Mandatory reminder: any member marked [EXPOSÉ] remains conditional on a runtime capability-check and a readback of the modified value, in accordance with the CLAUDE.md iron rule |

---

## 1. Family: `thermal_bridges` — ψ [W/(m·K)] and χ [W/K]

**SIA 380/2:2022 Table 2 reference value**: ψ = 0, χ = 0.
**Config key**: `thermal_bridge_psi_chi = 0.0`.

### 1.1 PDF Search Results

- Exact term **"thermal bridge"**: **absent** from the VEScripts-API-VE2023 PDF (exhaustive
  search across 248 pages).
- Term **"psi"**: present on page 9 only — it refers to the script editor debug toolbar menu
  ("Run Debugger (Shift + F5)"). No relation to thermal bridges.
- Term **"chi"**: present on several pages but only as a substring of common words
  ("machine", "mechanism", etc.) — no context related to linear or point thermal bridges.
- No documented VE object exposes a `psi`, `chi`, `thermal_bridge_psi`,
  `thermal_bridge_chi` attribute, or any equivalent.

### 1.2 Analysis

The VEScripts 2023 API does not document any surface for reading thermal bridge coefficients
(linear ψ or point χ) from the geothermal model.

**Important special case for the reference project**: the normative value is ψ = χ = 0.
For the reference project construction (Pathway B, `# SIA 380/2:2022 7.2.5.3`), the
directive is to force the thermal bridge contribution to zero in the reference model. This
directive does not require reading the project value. It does, however, require **knowing how
ApacheSim accounts for thermal bridges** (CDB construction, run parameter, or simply absent
from the thermal engine) in order to determine the substitution action — information not
documented in the VEScripts PDF.

For Pathway A (project value vs. limit comparison, `# SIA 380/2:2022 7.2.1.2`), the
project ψ/χ value is not extractable via API.

### 1.3 Verdict

| Quantity | Status | API Member | PDF Page |
|---|---|---|---|
| ψ project [W/(m·K)] | **NON EXPOSÉ** | — | — |
| χ project [W/K] | **NON EXPOSÉ** | — | — |
| Substitution action (force ψ=χ=0) | **NÉCESSITE SONDE VE** | mechanism not documented | — |

**Consequence for the adapter**: the `thermal_bridges` family remains **out of scope
of the documented API**. It cannot be automated without a dedicated VE probe to
determine how VE/ApacheSim models (or ignores) thermal bridges.

---

## 2. Family: `ventilation_system_and_controls`

**SIA 380/2:2022 Table 2 reference values** (Limit / Target):
- εV recovery efficiency: 1.0 / 1.4
- Duct airtightness class: C
- AHU airtightness class: L2 / L1
- U_ahu,SUP [W/(m²·K)]: 0.7 / 0.5

**Config keys**: `ventilation_efficiency`, `duct_airtightness_class`,
`ahu_airtightness_class`, `ahu_heat_transfer_w_m2k`.

### 2.1 Recovery Efficiency εV

**VE Object**: `VEApacheSystem` — method `ventilation_ncm()` **[PDF p.192]**.

Returned dictionary — relevant keys:

| API Key | Type | Description | PDF Page | Status |
|---|---|---|---|---|
| `heat_recovery_efficiency` | float | Seasonal heat recovery efficiency | p.192 | **[EXPOSÉ-NCM/UK]** |
| `heat_recovery_efficiency_known` | bool | Is the efficiency known? | p.192 | **[EXPOSÉ-NCM/UK]** |
| `default_heat_recovery_efficiency` | float | Default heat recovery efficiency | p.192 | **[EXPOSÉ-NCM/UK]** |
| `heat_recovery_type` | ncm_heat_recovery_type | Heat recovery type | p.192 | **[EXPOSÉ-NCM/UK]** |
| `variable_heat_recovery` | bool | Variable-efficiency heat recovery | p.192 | **[EXPOSÉ-NCM/UK]** |

Enum values `ncm_heat_recovery_type` **[PDF p.193]**:
`no_heat_recovery`, `plate_heat_exchanger`, `heat_pipes`, `thermal_wheel`, `run_around_coil`.

**NCM/UK reservation**: `ventilation_ncm()` is a method specific to the NCM workflow
(UK Building Regulations). The efficiency it returns is the user input for the
SBEM/NCM calculation, not a value measured according to a SIA/EN standard. The correspondence
between `heat_recovery_efficiency` (NCM) and εV from SIA 380/2 Table 2 requires confirmation
by VE probe with a calibrated model.

Full access path:
```python
# ⚠ capability-check + readback obligatoires en VE réel
import iesve
system = iesve.VEApacheSystem.default()  # ou via project.apache_systems()
vent_ncm = system.ventilation_ncm()
epsilon_v = vent_ncm.get("heat_recovery_efficiency")  # float ou None
```

### 2.2 Duct Airtightness Class

**VE Object**: `VEApacheSystem` — method `system_adjustment_ncm()` **[PDF p.192]**.

| API Key | Type | Description | PDF Page | Status |
|---|---|---|---|---|
| `ductwork_leakage_test` | ncm_leakage_test | CEN duct airtightness classification | p.192 | **[EXPOSÉ-NCM/UK]** |
| `ductwork_leakage_test_done` | bool | Airtightness test performed? | p.192 | **[EXPOSÉ-NCM/UK]** |

Enum values `ncm_leakage_test` **[PDF p.193]**:
`not_tested`, `class_a`, `class_b`, `class_c`, `class_d`.

**Correspondence warning**: the VE duct airtightness classes
(`class_a`...`class_d`) are NCM/UK classes (CIBSE TM44 / EN 12237). The SIA 380/2
Table 2 standard mentions class "C" without specifying the reference EN. The
correspondence class_c (NCM) <-> class C (SIA) is plausible but is not documented
in the PDF and must be confirmed by the SIA engineer or the VE probe.

### 2.3 AHU Airtightness Class

**VE Object**: `VEApacheSystem` — method `system_adjustment_ncm()` **[PDF p.192]**.

| API Key | Type | Description | PDF Page | Status |
|---|---|---|---|---|
| `cen_class` | ncm_leakage_standard | CEN AHU classification | p.192 | **[EXPOSÉ-NCM/UK]** |
| `ahu_meets_standards` | bool | Does the AHU meet CEN standards? | p.189 (set_), p.191 | **[EXPOSÉ-NCM/UK]** |

Enum values `ncm_leakage_standard` **[PDF p.193]**:
`class_l1`, `class_l2`, `class_l3`, `not_compliant`.

**Correspondence**: `class_l1` -> L1 and `class_l2` -> L2 from SIA 380/2 is probable but
not confirmed in the PDF. VE probe required.

### 2.4 Specific Fan Power (SFP)

Two candidate members located:

| API Key | Object | Method | Unit | PDF Page | Status |
|---|---|---|---|---|---|
| `SFP` | VEApacheSystem | `auxiliary_energy()` | W/(l/s) | p.181 | **[EXPOSÉ]** |
| `specific_fan_power` | VEApacheSystem | `system_adjustment_ncm()` | float | p.192 | **[EXPOSÉ-NCM/UK]** |

Note: `SFP` in `auxiliary_energy()` is documented without NCM suffix — it is the
system SFP, accessible regardless of workflow. `specific_fan_power` in
`system_adjustment_ncm()` is the NCM value manually entered by the user.
For project extraction, `auxiliary_energy().SFP` is preferred (direct model data).

### 2.5 U_ahu,SUP [W/(m²·K)] — AHU Thermal Transmittance Coefficient

**Search result**: no dictionary documented in the PDF contains a
`U_ahu`, `ahu_heat_transfer`, `thermal_transmittance_ahu` field or equivalent. Page
191 shows `solar_water_heating_ncm()` with thermal loss fields
(piping, volume, insulation), but only for solar water heaters, not for
AHUs.

**Status**: **NON EXPOSÉ** in the documented VEScripts API.

### 2.6 Ventilation Family Verdict

| SIA 380/2 Quantity | API Member | Object.method | Page | Status |
|---|---|---|---|---|
| εV recovery efficiency | `heat_recovery_efficiency` | `VEApacheSystem.ventilation_ncm()` | p.192 | **EXPOSÉ-NCM/UK** |
| Recovery type | `heat_recovery_type` | `VEApacheSystem.ventilation_ncm()` | p.192 | **EXPOSÉ-NCM/UK** |
| Variable recovery | `variable_heat_recovery` | `VEApacheSystem.ventilation_ncm()` | p.192 | **EXPOSÉ-NCM/UK** |
| Duct class | `ductwork_leakage_test` | `VEApacheSystem.system_adjustment_ncm()` | p.192 | **EXPOSÉ-NCM/UK** |
| AHU class (L1/L2) | `cen_class` | `VEApacheSystem.system_adjustment_ncm()` | p.192 | **EXPOSÉ-NCM/UK** |
| SFP [W/(l/s)] | `SFP` | `VEApacheSystem.auxiliary_energy()` | p.181 | **EXPOSÉ** |
| U_ahu,SUP [W/(m²·K)] | — | — | — | **NON EXPOSÉ** |

**Conclusion**: εV, recovery type, airtightness classes, and SFP are **adapter-feasible**
with NCM/UK reservation. U_ahu,SUP is **out of scope of the documented API**.

---

## 3. Family: `emission_system_and_unlimited_capacity`

**SIA 380/2:2022 Table 2 reference values**:
- Emission type: convection (radiant_fraction = 0)
- ΦH,max / ΦC,max: unlimited (run directive, not a numerical comparison)

### 3.1 Emission Type (Radiant / Convective Fraction)

The radiant fraction is exposed at two levels:

**VERoomData level** — method `get_apache_systems()` **[PDF p.229]**:

The documentation describes in prose: "*Heating: size (kW), radiant fraction, supply air
temperature and whether the heating capacity is unlimited*". The corresponding key seen
in the mirror method `set_apache_systems()` **[PDF p.233]** is:

| API Key | Type | Description | PDF Page | Status |
|---|---|---|---|---|
| `heating_plant_radiant_fraction` | float | Heating system radiant fraction | p.233, p.242 | **[EXPOSÉ]** |
| `cooling_plant_radiant_fraction` | float | Cooling system radiant fraction | p.233, p.242 | **[EXPOSÉ]** |

Interpretation: `heating_plant_radiant_fraction = 0.0` -> 100% convective emission,
compliant with the "by convection" directive of SIA 380/2 Table 2.

**VEThermalTemplate level** — method `get_apache_systems()` **[PDF p.242]**:

These same keys are explicitly listed in the dictionary returned by
`VEThermalTemplate.get_apache_systems()` (p.242), which confirms the existence of the fields.

### 3.2 Unlimited Capacity ΦH,max / ΦC,max

**VE Object**: `VEThermalTemplate` — method `get_apache_systems()` **[PDF p.242]**.

| API Key | Type | Description | PDF Page | Status |
|---|---|---|---|---|
| `heating_capacity_unlimited` | bool | Unlimited heating capacity | p.242 | **[EXPOSÉ]** |
| `cooling_capacity_unlimited` | bool | Unlimited cooling capacity | p.242 | **[EXPOSÉ]** |

The enum `heating_cooling_capacity_unit` **[PDF p.245]** confirms:
`unlimited`, `kilowatts`, `watts_per_metre_squared`.

**Note on VERoomData**: the `get_apache_systems()` documentation on page 229 describes
the same fields in prose ("*whether the heating capacity is unlimited*"). The exact keys
in the returned dictionary are not explicitly listed — they are visible in the
mirror method `set_apache_systems()` **[PDF p.233]**: `heating_capacity_unlimited` (bool)
and `cooling_capacity_unlimited` (bool). A real VE capability-check remains mandatory
to confirm that `get_apache_systems()` returns these keys.

**Access via VEThermalTemplate recommended** as the dictionary is explicitly documented.

### 3.3 Directive vs. Comparison

ΦH,max / ΦC,max "unlimited" is a reference project **run directive**
(`# SIA 380/2:2022 Tableau 2`): in the reference model, capacities must not
constrain the calculation. There is therefore **no project value to extract** for this
quantity. The adapter must only verify (or force) the boolean flag to `True` in
the reference model, not compare a numerical value.

### 3.4 Emission Family Verdict

| SIA 380/2 Quantity | API Member | Object.method | Page | Status |
|---|---|---|---|---|
| Heating radiant fraction | `heating_plant_radiant_fraction` | `VEThermalTemplate.get_apache_systems()` | p.242 | **EXPOSÉ** |
| Cooling radiant fraction | `cooling_plant_radiant_fraction` | `VEThermalTemplate.get_apache_systems()` | p.242 | **EXPOSÉ** |
| Unlimited heating capacity (bool) | `heating_capacity_unlimited` | `VEThermalTemplate.get_apache_systems()` | p.242 | **EXPOSÉ** |
| Unlimited cooling capacity (bool) | `cooling_capacity_unlimited` | `VEThermalTemplate.get_apache_systems()` | p.242 | **EXPOSÉ** |
| ΦH,max / ΦC,max numerical project value | (directive, not extraction) | — | — | **NON APPLICABLE** |

**Conclusion**: family is **adapter-feasible** (radiant fraction + unlimited capacity).
Capability-check + readback mandatory in real VE, in particular for `VERoomData.get_apache_systems()`.

---

## 4. Family: `cooling_generation_and_auxiliaries` — Project EER/SEER

**SIA 380/2:2022 reference value**: EER/SEER calculated from Tables 5-9
(not coded in `SIA3802_LIMIT_VALUES` as it depends on the generator type). The extraction
targets the **project value**.

### 4.1 Located API Members

**VE Object**: `VEApacheSystem` — method `cooling()` **[PDF p.182]**.

| API Key | Type | Unit | Description | PDF Page | Status |
|---|---|---|---|---|---|
| `nominal_eer` | float | kW/kW | Generator nominal EER | p.182 | **[EXPOSÉ]** |
| `SEER` | float | kW/kW | Seasonal energy efficiency ratio | p.182 | **[EXPOSÉ]** |
| `SSEER` | float | kW/kW | System seasonal energy efficiency ratio | p.182 | **[EXPOSÉ]** |

Via method `cooling_ncm()` **[PDF p.182]**:

| API Key | Type | Description | PDF Page | Status |
|---|---|---|---|---|
| `generator_nominal_eer` | float | Nominal EER (NCM) | p.182 | **[EXPOSÉ-NCM/UK]** |
| `generator_seasonal_eer` | float | Seasonal EER (NCM) | p.182 | **[EXPOSÉ-NCM/UK]** |
| `generator_nominal_eer_known` | bool | Is nominal EER known? | p.182 | **[EXPOSÉ-NCM/UK]** |
| `generator_seasonal_eer_known` | bool | Is seasonal EER known? | p.182 | **[EXPOSÉ-NCM/UK]** |

Useful complementary field:

| API Key | Type | Description | PDF Page | Status |
|---|---|---|---|---|
| `has_absorption_chiller` | bool | Presence of an absorption chiller | p.182 | **[EXPOSÉ]** |

### 4.2 Access Path

```python
# ⚠ capability-check + readback obligatoires en VE réel
import iesve
project = iesve.VEProject.get_current_project()
for system in project.apache_systems():
    cooling = system.cooling()       # dict [PDF p.182]
    eer     = cooling.get("nominal_eer")   # float kW/kW ou None
    seer    = cooling.get("SEER")          # float kW/kW ou None
```

### 4.3 Cooling Family Verdict

| Quantity | API Member | Object.method | Page | Status |
|---|---|---|---|---|
| Project nominal EER | `nominal_eer` | `VEApacheSystem.cooling()` | p.182 | **EXPOSÉ** |
| Project SEER | `SEER` | `VEApacheSystem.cooling()` | p.182 | **EXPOSÉ** |
| Project SSEER | `SSEER` | `VEApacheSystem.cooling()` | p.182 | **EXPOSÉ** |

**Conclusion**: family is **adapter-feasible**. Already partially extracted in
`model_analyzer.py` (`eer`, `seer`, `sseer` in `_analyze_hvac_systems`).

---

## 5. Family: `heating_generation` — Project SCOP/Efficiency

**SIA 380/2:2022 reference value**: SCOP/efficiency calculated from Tables
8-9 (depends on the generator type). The extraction targets the **project value**.

### 5.1 Located API Members

**VE Object**: `VEApacheSystem` — method `heating()` **[PDF p.183]**.

| API Key | Type | Unit | Description | PDF Page | Status |
|---|---|---|---|---|---|
| `SCoP` | float | kW/kW | Seasonal coefficient of performance | p.183 | **[EXPOSÉ]** |
| `gen_seasonal_eff` | float | — | Generator seasonal efficiency | p.183 | **[EXPOSÉ]** |
| `Is_heat_pump` | bool | — | Is the generator a heat pump? | p.183 | **[EXPOSÉ]** |
| `del_eff` | float | — | Distribution efficiency | p.183 | **[EXPOSÉ]** |
| `fuel` | int | — | Fuel type (see `fuel_names()`) | p.183 | **[EXPOSÉ]** |

Via method `heating_ncm()` **[PDF p.183]**:

| API Key | Type | Description | PDF Page | Status |
|---|---|---|---|---|
| `generator_seasonal_efficiency` | float | Seasonal efficiency (NCM) | p.183 | **[EXPOSÉ-NCM/UK]** |
| `generator_seasonal_efficiency_known` | bool | Is efficiency known? | p.183 | **[EXPOSÉ-NCM/UK]** |
| `heat_source` | ncm_heat_source | Heat source type | p.183 | **[EXPOSÉ-NCM/UK]** |

Enum values `ncm_heat_source` **[PDF p.193]** (relevant excerpt):
`lthw_boiler`, `heat_pump_electric_air_source`, `heat_pump_electric_ground_or_water_source`,
`district_heating`, etc.

### 5.2 Access Path

```python
# ⚠ capability-check + readback obligatoires en VE réel
import iesve
project = iesve.VEProject.get_current_project()
for system in project.apache_systems():
    heating = system.heating()           # dict [PDF p.183]
    scop    = heating.get("SCoP")        # float kW/kW ou None
    seff    = heating.get("gen_seasonal_eff")   # float ou None
    is_hp   = heating.get("Is_heat_pump")       # bool ou None
```

### 5.3 Heating Family Verdict

| Quantity | API Member | Object.method | Page | Status |
|---|---|---|---|---|
| Project SCOP | `SCoP` | `VEApacheSystem.heating()` | p.183 | **EXPOSÉ** |
| Seasonal efficiency | `gen_seasonal_eff` | `VEApacheSystem.heating()` | p.183 | **EXPOSÉ** |
| Heat pump type | `Is_heat_pump` | `VEApacheSystem.heating()` | p.183 | **EXPOSÉ** |

**Conclusion**: family is **adapter-feasible**. Already partially extracted in
`model_analyzer.py` (`scop` in `_analyze_hvac_systems`).

---

## 6. Family: `photovoltaic_generation`

**SIA 380/2:2022 Table 2 reference values** (config):
- `pv_power_w_per_m2_sre = 10` W/m²·SRE (PV power per m² of SRE)
- `pv_conversion_efficiency = 0.90` (overall conversion efficiency)

The extraction targets **model inputs** (user-configured area, efficiency),
not **simulation results** (annual kWh production).

### 6.1 Access to the VERenewables Object

The class hierarchy **[PDF p.18-19]** shows `VERenewables` at the same level as
`VEProject` and `VEApacheSystem`, instantiable directly via `iesve.VERenewables()`.
However, **no instantiation example is documented in the PDF** (no static method
`get_current_renewables()`, no attribute on VEProject). This point requires a
**real VE probe** to confirm the correct instantiation.

### 6.2 Documented PV Model Inputs

**VE Object**: `VERenewables` — method `get_pv_data()` **[PDF p.225]**.

| API Key | Type | Description | PDF Page | Status |
|---|---|---|---|---|
| `area` | float | PV panel area (m²) | p.225 | **[EXPOSÉ]** |
| `cell_efficiency` | float | Cell efficiency | p.225 | **[EXPOSÉ]** |
| `azimuth` | float | PV azimuth | p.225 | **[EXPOSÉ]** |
| `inclination` | float | PV inclination | p.225 | **[EXPOSÉ]** |
| `shading_factor` | float | Shading factor | p.225 | **[EXPOSÉ]** |
| `type_id` | string | PV type ID -> references `get_pv_type_by_id()` | p.225 | **[EXPOSÉ]** |
| `id` | string | PV panel ID | p.225 | **[EXPOSÉ]** |

**VE Object**: `VERenewables` — method `get_pv_type_by_id(id)` **[PDF p.226]**.

| API Key | Type | Description | PDF Page | Status |
|---|---|---|---|---|
| `electrical_conversion_efficiency` | float | Electrical conversion efficiency | p.226 | **[EXPOSÉ]** |
| `module_nominal_efficiency` | float | Module nominal efficiency | p.226 | **[EXPOSÉ]** |
| `technology` | string | PV technology | p.226 | **[EXPOSÉ]** |
| `degradation_factor` | float | Degradation factor | p.226 | **[EXPOSÉ]** |

### 6.3 PV Simulation Results (vs. Model Inputs)

The **annual PV production** result is accessible via `ResultsReader` with the enum
`EnergyUse.prm_elec_gen_pv` **[PDF p.159]**. These are simulation results
(`ResultsReader.get_results()`), not user-configured inputs.

**For the reference project construction**, the **configured project value**
(area x efficiency) is the relevant quantity, not the simulated result.

### 6.4 Correspondence with SIA Config Keys

| SIA Config Key | Candidate API Member | Method | Page | Note |
|---|---|---|---|---|
| `pv_power_w_per_m2_sre` (10 W/m²·SRE) | (normative value, not extraction) | — | — | Reference value, not project value |
| `pv_conversion_efficiency` (0.90) | `electrical_conversion_efficiency` | `get_pv_type_by_id()` | p.226 | Correspondence to be confirmed |
| Installed area [m²] | `area` (per panel) | `get_pv_data()` | p.225 | Sum across all panels |

### 6.5 Total Installed Power

There is no direct "total installed power" member in the API. It is derived:

```
P_installed [W] = sum_i( area[i] × cell_efficiency[i] ) × ref_irradiance
```

This derivation is not documented in the PDF as a direct API member.

### 6.6 Photovoltaic Family Verdict

| Quantity | API Member | Object.method | Page | Status |
|---|---|---|---|---|
| Panel area [m²] | `area` | `VERenewables.get_pv_data()` | p.225 | **EXPOSÉ** |
| Cell efficiency | `cell_efficiency` | `VERenewables.get_pv_data()` | p.225 | **EXPOSÉ** |
| Conversion efficiency | `electrical_conversion_efficiency` | `VERenewables.get_pv_type_by_id()` | p.226 | **EXPOSÉ** |
| Total installed power | (derived, not a direct member) | — | — | **NÉCESSITE SONDE VE** |
| VERenewables instantiation | `iesve.VERenewables()` | — | p.18-19 (hierarchy) | **NÉCESSITE SONDE VE** |

**Conclusion**: model inputs are **adapter-feasible** subject to
confirmation of `VERenewables` instantiation and total power derivation. The distinction
between model data and simulation results must be maintained
(never use `ResultsReader` results as a configured project value).

---

## 7. Feasibility Summary

### 7.1 Summary Table

| Family | Overall Verdict | Key Member(s) | PDF Page | Residual Blocker |
|---|---|---|---|---|
| `thermal_bridges` | **OUT OF API SCOPE** | none found | — | No documented ψ/χ access; VE substitution mechanism unknown |
| `ventilation_system_and_controls` | **PARTIALLY FEASIBLE** | `heat_recovery_efficiency`, `cen_class`, `ductwork_leakage_test`, `SFP` | p.181, p.192 | U_ahu,SUP absent; NCM/UK <-> SIA correspondence to be confirmed |
| `emission_system_and_unlimited_capacity` | **FEASIBLE** | `heating_plant_radiant_fraction`, `heating_capacity_unlimited`, `cooling_capacity_unlimited` | p.229, p.242 | Capability-check required on `VERoomData.get_apache_systems()` |
| `cooling_generation_and_auxiliaries` | **FEASIBLE** (already partially extracted) | `nominal_eer`, `SEER`, `SSEER` | p.182 | None (existing extraction in `model_analyzer.py`) |
| `heating_generation` | **FEASIBLE** (already partially extracted) | `SCoP`, `gen_seasonal_eff` | p.183 | None (existing extraction in `model_analyzer.py`) |
| `photovoltaic_generation` | **FEASIBLE subject to conditions** | `area`, `cell_efficiency`, `electrical_conversion_efficiency` | p.225, p.226 | VERenewables instantiation to be confirmed; total power derived |

### 7.2 Suggested Implementation Priority

1. **`emission_system_and_unlimited_capacity`**: members explicitly documented in
   `VEThermalTemplate` (p.242), high feasibility. Binary normative value (bool).

2. **`cooling_generation_and_auxiliaries`** and **`heating_generation`**: members already
   extracted in `model_analyzer.py` — it suffices to add the family in
   `IMPLEMENTED_REFERENCE_INPUT_FAMILIES` with their substitution logic.

3. **`photovoltaic_generation`**: feasible after confirmation of `VERenewables`
   instantiation by VE probe.

4. **`ventilation_system_and_controls`**: feasible for εV, classes, and SFP, but the
   NCM/UK context requires semantic validation before producing a
   `SUBSTITUTABLE` verdict. U_ahu,SUP remains blocked.

5. **`thermal_bridges`**: not feasible via documented API. Escalation required to the VE
   product team or implementation via dedicated VE probe.

### 7.3 Mandatory Invariants for Any Implementation

- Any member marked [EXPOSÉ] or [EXPOSÉ-NCM/UK] in this document remains conditional on
  a **runtime capability-check** (`hasattr` + try/except) and a **readback** of
  the value after any mutation, in accordance with the project's iron rules.
- The `*_ncm()` methods of `VEApacheSystem` are only present in models
  configured in NCM mode. A pure Apache HVAC model will not return them — the adapter
  code must handle this absence without a fatal exception.
- A `None` value returned by the API is distinct from a `0.0` value: `None` means
  "not specified in the model", never substituted with a default value.
- This document does not modify any production code file.

---

## 8. Sources

| Source | Location | Reading |
|---|---|---|
| VEScripts-API-VE2023.pdf (248 pages) | `refs/VEScripts-API-VE2023.pdf` | Targeted PyMuPDF extraction, pages 3, 9, 18-19, 47, 56, 63, 65, 85, 95, 97-100, 102, 115, 159, 175-176, 181-193, 225-233, 242, 245 |
| `swiss_sia/reference_project.py` | codebase | IMPLEMENTED / MISSING families, read in full |
| `swiss_sia/model_analyzer.py` | codebase | `RoomData` fields, `_analyze_hvac_systems`, read in full |
| `swiss_sia/data_extractor.py` | codebase | Existing extraction methods, read in full |
| `swiss_sia/config.py` | codebase | `SIA3802_LIMIT_VALUES`, read |
| `traceability/sia380-2-pathway.spec.md` | codebase | Table 2 Limit/Target, §3.2 Mapping |

**SIA 380/2:2022 Tableau 2**: primary normative source for reference values.
No limit or target value is invented or interpolated in this document.
