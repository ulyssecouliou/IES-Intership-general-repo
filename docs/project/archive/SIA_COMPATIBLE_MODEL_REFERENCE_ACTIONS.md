# SIA-Compatible VE Reference Model Action Plan

Date: 2026-07-16

## Purpose

This document defines the actions required to turn the current three-room
`SIA_compatible_model` VE project into a controlled internal reference model
for SIA 380/2:2022 readiness and regression testing.

The model can become a reliable golden building fixture. It cannot, by itself,
validate every SIA 4010 class because SIA 4010 validates a calculation method
or software workflow through several prescribed test buildings, system
variants, official comparison files and reviewer confirmation.

## Reviewed Baseline

Workbook reviewed:

`reports/Swiss_Compliance_Report__SIA_compatible_model__-__20260716_112311.xlsx`

| Item | Current observation | Decision |
| --- | --- | --- |
| Model scope | 3 rooms, 50 m2, 140 m3 | Suitable for a small internal golden building model. |
| SIA 380/2 precheck score | 75/100 | Useful readiness score only; the global reviewed comparison is still missing. |
| Model health score | 44.7/100 | Improve missing room, plant, climate and dynamic-result evidence. |
| SIA 4010 class result | 0/5; tests 1-7 not checkable | Correct conservative result until the separate official test portfolio is complete. |
| Rooms | `Office_01`, `Corridor_01`, `Office_02` | Keep the simple geometry and make every room input auditable. |
| WWR | 30% in every room | Keep as a design-review value; it is not a universal standalone SIA 380/2 pass/fail limit. |
| External wall | `U = 0.1855 W/(m2K)` | Below the Table 3 limit reference input `0.20`; target benchmark is `0.14`. |
| Roof | `U = 0.1800 W/(m2K)` | Below the Table 3 limit reference input `0.20`; target benchmark is `0.14`. |
| Ground floor | `U = 0.2200 W/(m2K)` | Below the Table 3 limit reference input `0.30`; target benchmark is `0.20`. |
| Window Uw | `0.6138 W/(m2K)` | Better than the Table 2 target reference input `0.88`; retain evidence. |
| EN 410 g_perp | `0.5269` | Above the Table 2 reference input `0.50`; use the actual value in the global comparison, or change the glazing when reproducing the reference-input fixture. |
| Raw CDB g-value | `0.75` | Do not use as SIA g_perp; the VE API proves that it differs from `bs_en_410`. |
| Visible transmittance | `tau_v = 0.65` | Change to or document `tau_v >= 0.70` for the reference-input benchmark. |
| Frame fraction | `0.10` | Below the `0.25` reference input; retain CDB/frame evidence. |
| Shading | All activation fields are zero | No active solar protection is modelled, so `g_total` is not applicable. Add a real device and calculation only if the design needs active shading. |
| Weather | `DublinIWEC.fwt` | Not a reviewed Swiss SIA climate basis; replace for the Swiss reference workflow. |
| Infiltration | Missing in all rooms | Add explicit comparable data in `m3/(h.m2)`. |
| Ventilation | Missing in all rooms | Add design outdoor/supply airflow and control evidence. |
| Gains | Equipment and lighting data missing | Complete all room templates and profiles. |
| HVAC | `SYST0000`, generic efficiency `2.5`, generator class missing | Define real plant type, capacity, efficiency metrics and controls. |
| Annual comfort | 0 rooms with complete annual evidence | Export complete aligned temperature, occupancy and both SIA 180 limit series. |
| Dynamic energy | Cooling `40.4603 kWh/m2`; heating and other end uses unavailable | Keep the cooling result as a diagnostic and enable the missing full-year result variables. |
| SIA 4010 evidence | 0/5 official evidence families | Keep the result `NOT_CHECKABLE` until official evidence is available. |

## Important Rerun Before Model Decisions

The reviewed workbook already includes the APS metric conversion and exact
project-evidence isolation corrections. It was generated before the final
active-shading and evidence-template corrections made on 2026-07-16:

1. numeric shade activation fields equal to zero no longer count as active
   solar-protection evidence;
2. `g_total` is required only for a genuinely active device, not merely because
   the base EN 410 value is above the Table 2 reference input;
3. all evidence templates are now project-neutral and inject the active project
   label into their CSV content.

Rerun `Run_VE_Swiss_Compliance.py` once before changing the glazing. The new
report should classify `STD_EXT2` as a reference-input deviation with no active
shading, not as missing `g_total` evidence.

## Phase 0 - Establish a Clean Project Baseline

1. Open `SIA_compatible_model` in VE.
2. Run `Prepare_SIA4010_Evidence_Folder.py` from the VE Run button.
3. Confirm that ten files are created with suffix
   `SIA_compatible_model`, not `ZOER_32_C1`.
4. Run `Run_VE_Swiss_Compliance.py` without changing the model.
5. Confirm that `SIA3802 JUSTIFICATIONS` contains no ZOER records and that all
   generated evidence rows use `SIA_compatible_model` as the project ID.
6. Confirm that `DYNAMIC RESULTS` includes APS source labels with metric unit
   and conversion information.
7. Archive this report as the corrected baseline.

## Phase 1 - Climate and Project Metadata

### VE changes

1. Decide the Swiss reference location with the manager or responsible
   compliance reviewer.
2. Select the normal DRY climate for the most representative SIA 2028 station.
3. Use the required 2022 calendar basis for the annual summer-comfort method:
   1 January 2022 is Saturday, with the corresponding workdays and holidays.
4. Rerun Apache after changing the weather file so the APS weather reference
   matches the active VE project weather.

### Evidence changes

Complete:

`sia4010_evidence/SIA3802_project_metadata_SIA_compatible_model.csv`

Required fields include:

- exact `project_id`;
- `NEW_BUILDING` or `EXISTING_BUILDING`;
- weather basis and weather filename;
- Swiss location and altitude;
- reviewer, review date, source document and source reference;
- accepted review status.

Do not label a Dublin IWEC file as a SIA 2028 Swiss climate file.

## Phase 2 - Room Uses, Gains and Schedules

### Room mapping

Use one reviewed mapping row for each room:

| VE room | Intended use family | Required controlled decision |
| --- | --- | --- |
| `Office_01` | Office | Exact SIA 2024 category and use profile. |
| `Corridor_01` | Circulation/corridor | Exact SIA 2024 category and use profile. |
| `Office_02` | Office | Exact SIA 2024 category and use profile. |

Complete:

`sia4010_evidence/SIA2024_usage_mapping_SIA_compatible_model.csv`

SIA 380/2 delegates these numeric use assumptions to SIA 2024. The current two
PDFs do not contain the missing SIA 2024 category tables, so the script must not
invent category codes, densities or schedules.

### VE thermal-template inputs

For every room, provide:

- people density or count and sensible/latent gains;
- equipment power density and profile;
- lighting power density and profile;
- occupancy profile;
- heating and cooling setpoint profiles;
- HVAC availability profile;
- shading profile where applicable;
- weekly schedule, holidays and exceptions;
- daylight and presence-control settings where applicable.

For the Table 11 method, the system schedule starts one hour before occupancy,
stops one hour after occupancy and operates through the lunch break.

### Lighting evidence

Complete:

`sia4010_evidence/SIA3874_lighting_control_mapping_SIA_compatible_model.csv`

The exact SIA 387/4 control type and numeric lighting assumptions require the
controlled SIA 387/4 source or reviewer evidence. They are not reconstructed
from SIA 380/2 or SIA 4010 alone.

## Phase 3 - Infiltration, Ventilation and Openings

### Infiltration

Add an infiltration air exchange to all three rooms with an API-readable unit.
For an internal Table 2 reference-input fixture, use:

`0.15 m3/(h.m2)`

If VE stores `l/(s.m2)`, use the documented conversion and keep the unit source.
For a real project model, this value remains part of the project/reference
method and is not an autonomous airtightness certificate.

### Ventilation

For every room, provide the design outdoor or supply airflow and enough data to
derive `m3/(h.m2)`. Then document:

- monozone or multizone system type;
- one-speed, two-speed or variable-speed fan control;
- minimum flow fraction;
- time, occupancy or gas-sensor demand control;
- zone or room control scope;
- heat-recovery type and efficiency;
- AHU and duct leakage class;
- supply/extract pressure drops;
- fan and pump control identifiers.

Select the Table 4 target control only after the airflow band (`<=3`, `3-6` or
`>6 m3/(h.m2)`) and monozone/multizone type are known.

### Window operability

Explicitly classify every assessed room as operable or non-operable. Keep the
MacroFlo/opening evidence. Annual comfort cannot be finalized when window
operability is unknown.

## Phase 4 - Glazing and Solar Protection

### Preferred golden-model option

Replace or edit `STD_EXT2` so that:

- `VECdbConstruction.get_g_values().bs_en_410 <= 0.50`;
- visible transmittance `tau_v >= 0.70`;
- window Uw remains `<= 0.88 W/(m2K)` for the target benchmark;
- frame fraction remains documented and `<= 0.25` in the current diagnostic;
- raw CDB `g_value` is retained only as audit information.

This is the simplest reference fixture because it avoids relying on an
unverified shaded total g-value.

### Alternative shaded option

If the design needs active shading while `g_perp` remains `0.5269`, create a
real active solar-protection system:

1. select a Table 10 category and actual device type;
2. enter reviewed solar reflectance and transmittance;
3. define raise/lower thresholds and schedules;
4. document wind availability/resistance assumptions;
5. calculate or import an auditable active glazing-plus-shading g_total;
6. complete `glazing_solar_protection_SIA_compatible_model.csv` and
   `g_values_audit_SIA_compatible_model.csv`.

The VEScripts API does not expose a documented direct
`g_total_with_shading` construction field. A derived value therefore needs a
manufacturer source or a reviewed ISO 52022-3 / ISO 15099 calculation.

Do not add a fictitious shading device merely to make the readiness score rise.
Without active shading, retain `g_perp = 0.5269` as the project input and let the
reviewed global project/reference calculation determine the building result.

## Phase 5 - Envelope Benchmark Level

The current opaque envelope is below the limit reference inputs. For a stronger
target-level golden model, use the following target diagnostics:

| Component | Current | Limit reference | Target reference | Recommended golden-model action |
| --- | ---: | ---: | ---: | --- |
| External wall | `0.1855` | `0.20` | `0.14` | Keep for limit fixture or improve to `<=0.14` for target fixture. |
| Flat roof | `0.1800` | `0.20` | `0.14` | Keep for limit fixture or improve to `<=0.14` for target fixture. |
| Ground floor | `0.2200` | `0.30` | `0.20` | Keep for limit fixture or improve to `<=0.20` for target fixture. |
| Window Uw | `0.6138` | `1.10` | `0.88` | Keep. |

Keep construction build-ups, boundary conditions and U-value provenance. Do
not describe an individual component match as the final building compliance
result. The complete project/reference comparison remains decisive.

## Phase 6 - HVAC and Plant

The current generic `SYST0000` efficiency of `2.5` is not enough to select a
normative efficiency row. Define the actual plant before checking values.

### Cooling plant

Provide:

- air-cooled or water-cooled classification;
- rated cooling capacity and capacity band;
- EER and SEER;
- part-load curve;
- condenser and heat-rejection type;
- free cooling, storage, pump and auxiliary data where applicable.

If the selected plant is air-cooled and `<=12 kW`, the encoded Table 5-7
reference values are:

- limit: `EER >= 2.90`, `SEER >= 3.80`;
- target: `EER >= 3.10`, `SEER >= 4.20`.

Use another row when the type or capacity differs.

### Heating plant

Provide:

- generator type and rated capacity;
- SCOP or the delegated SIA 384/3 hourly-method evidence;
- emission, distribution, storage and generation data;
- pump, fan and auxiliary energy;
- heat-recovery interaction where applicable.

If the selected plant is an air/water heat pump and `<=12 kW`, the encoded
Table 8 limit is `SCOP >= 3.00`. Table 8 does not provide a separate air/water
target column, so the script must not synthesize one.

## Phase 7 - APS Outputs and Dynamic Method

Enable and retain the following full-year APS/Vista outputs:

- room heating demand/load;
- room cooling demand/load;
- room operative or dry-resultant temperature;
- occupancy;
- SIA 180 upper limit curve;
- SIA 180 lower limit curve;
- lighting energy;
- fan energy;
- pump energy;
- auxiliary energy;
- heating and cooling coil energy;
- CO2 and relative humidity;
- final energy by system and carrier.

All annual comfort series must cover exactly 365 days at the same timestep.
The current fixed 26 C and 27 C indicators are diagnostics only. For the final
annual assessment, compare occupied temperatures against both SIA 180 curves.

The encoded annual limits are:

- new non-operable building: at most `100 h` above the upper curve;
- existing non-operable building: at most `400 h` above the upper curve;
- operable rooms: `0 h` above the upper curve;
- all cases: `0 h` below the lower curve.

## Phase 8 - Heating and Cooling Design Power

Annual peaks are not design-power evidence. Run dedicated design sequences:

- heating: four reference days after 14 preconditioning days, 96 quarter-hour
  values per day sequence;
- cooling: three reference days after 14 preconditioning days, 72 quarter-hour
  values per day sequence.

Retain the dedicated APS files, weather/setup metadata, timestep and extracted
peak calculation.

## Phase 9 - Whole-Project SIA 380/2 Decision

Complete:

`sia4010_evidence/SIA3802_global_reference_comparison_SIA_compatible_model.csv`

The accepted row must contain:

- `project_id = SIA_compatible_model`;
- `comparison_scope = complete_sia3802_project`;
- numeric project and reference values;
- the same explicit unit;
- a compliant comparison result;
- reviewer, review date, source document and source reference;
- accepted review status.

Without this reviewed global comparison, the correct status remains
`NOT_CHECKABLE`, even if every component diagnostic matches a reference value.

## Phase 10 - SIA 4010 Test Portfolio

Do not attempt to force all SIA 4010 tests into the three-room golden building.
Maintain a separate validation portfolio:

| Test | Required model family |
| --- | --- |
| 1 | Standardized BESTEST test cell. |
| 2A-2D | Test-1 cell with the prescribed fabric/lamellae solar-protection controls. |
| 3A-3L | Test-2 base cell with prescribed SIA 387/4 lighting and coupled shading variants. |
| 4 | Windowless amphitheatre with a single-zone all-air system. |
| 5A-5D | Office-floor multizone AHU variants with reheating, cooling, humidification and heat/moisture recovery. |
| 6 | Restaurant/kitchen model with three-stage ventilation, recovery, constant airflow and overflow. |
| 7 | Heating/cooling emission, distribution, storage and generation using tests 5/6 rooms or supplied demand profiles. |

Official class validation then uses the SIA 4010 class matrix:

- `1A`: tests 1 and 2A;
- `1B`: tests 1 and 2;
- `2A`: tests 1, 2A and 3A-3F;
- `2B`: tests 1 to 3;
- `3`: tests 1 and 4 to 6;
- `4A`: tests 1, 2A, 3A-3F and 4 to 7;
- `4B`: tests 1 to 7;
- `5`: test 7.

The five official evidence families remain mandatory: official specifications,
official evaluation workbooks, candidate results, reference comparisons and
validation-class confirmation. The internal prevalidation score is never an
official PASS.

## Acceptance Checklist

The internal golden model is ready when all of the following are true:

- the active weather is a reviewed Swiss SIA basis and matches the APS file;
- every room has accepted SIA 2024 and SIA 387/4 mappings where applicable;
- every room has infiltration, ventilation, gains and auditable profiles;
- `STD_EXT2` has compliant/reference-ready EN 410 glazing evidence or a
  complete active shading calculation;
- plant type, capacity, EER/SEER/SCOP and auxiliaries are documented;
- full-year APS outputs have valid metric conversion traces;
- every room has complete aligned annual comfort evidence;
- dedicated heating and cooling design-power runs are attached;
- the global SIA 380/2 project/reference comparison is reviewed and accepted;
- the report contains no foreign-project evidence rows;
- SIA 4010 remains explicitly non-certified until the separate official test
  portfolio and authority evidence are complete.

## Source Traceability

- SIA 380/2:2022 FR: Table 1 page PDF 21; Tables 2-3 pages PDF 32-37;
  Table 4 page PDF 37; Tables 5-9 pages PDF 38-39; Table 10 page PDF 46;
  Table 11, normative Annex C, page PDF 59; clauses 3.2.4.3-3.2.4.4 and
  clauses 4.2-4.3.
- SIA 4010:2023 FR: Table 62 page PDF 46; Table 63 page PDF 48;
  clauses 4.6.1-4.6.2 pages PDF 48-49; Tables 64-66 pages PDF 50-52.
- VEScripts API: `ResultsReader.get_variables()`, `get_units()`,
  `get_room_results()` and `VECdbConstruction.get_g_values()`.
