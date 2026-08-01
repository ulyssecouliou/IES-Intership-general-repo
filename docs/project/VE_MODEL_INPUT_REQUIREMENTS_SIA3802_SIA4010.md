# VE Model Input Requirements for SIA 380/2 and SIA 4010

Date: 2026-07-07

## Purpose

This document is a practical VE modelling checklist for Swiss SIA compliance
readiness. It lists the model inputs that must be present, the encoded reference
project values, the directly applicable method conditions and the evidence that
must be attached when the standards require external or official validation
files.

It is intentionally conservative:

- SIA 380/2 Tables 2 to 9 primarily define reference-project inputs. Their
  values are useful diagnostics, but an individual component deviation is not a
  standalone compliance failure. The complete project/reference result is the
  decisive method gate.
- SIA 4010 validates a calculation method or software workflow through official
  tests, reference outputs and reviewer confirmation. It does not provide a
  standalone building kWh/m2 or CO2 threshold that would allow an autonomous
  pass/fail certificate from a client model alone.
- When SIA 380/2 delegates values to SIA 2024, SIA 2028, SIA 382/1,
  SIA 384/3, SIA 387/4, SIA 2056 or official SIA 4010 files, this document
  marks the entry as an evidence requirement instead of inventing a threshold.

## Source Basis

| Source | Use in this document |
| --- | --- |
| `references/standards/SIA 380-2-2022 FR.pdf` | SIA 380/2 method, reference-project values, comfort conditions and delegated evidence requirements. |
| `references/standards/SIA 4010-2023 FR.pdf` | SIA 4010 tests, validation classes, climate/test setup and official evidence requirements. |
| `SIA 4010 Register validierter Software_24-09-17.pdf` | Manager-provided register context for validation classes and software guardrails. |
| `swiss_sia/config.py` | Source-traced values currently encoded in the checker. |

## Reading Rule

| Column | Meaning |
| --- | --- |
| Input | VE model field, template field, CDB construction value, APS output or evidence file. |
| Required value | Reference-project value, method condition, maximum, minimum or allowed value according to the stated scope. |
| Type | `max`, `min`, `allowed`, `evidence` or `official`. |
| Script impact | How the current checker uses the value. |
| Professional evidence | What must be kept for reviewer/client audit. |

## Immediate Status for the Current 3-Room Test Model

Latest reviewed workbook:

`reports/Swiss_Compliance_Report__SIA_compatible_model__-__20260716_100912.xlsx`

| Area | Current issue | Required correction |
| --- | --- | --- |
| Climate | APS and project both use `DublinIWEC.fwt`, but no reviewed Swiss climate provenance is provided | Select the representative SIA 2028 DRY Swiss station, rerun Apache and complete the project metadata CSV. |
| Opaque envelope | Wall `0.1855`, roof `0.1800`, floor `0.2200 W/(m2K)` | Values are below the limit reference inputs; improve to the target reference inputs only if this golden model is intended to represent the target project. |
| Glazing `STD_EXT2` | `g_perp EN 410 = 0.5269`, `tau_v = 0.65` | Use `g_perp <= 0.50` and `tau_v >= 0.70`, or provide a reviewed active shading g-total calculation. |
| Infiltration | Missing in all three rooms | Provide comparable values in `m3/(h.m2)` and document the relationship to the `0.15` reference input. |
| Ventilation rates | Missing in all three rooms | Provide outdoor/supply airflow per room/area and control type. |
| Internal gains | Lighting/equipment missing | Fill lighting, equipment, occupancy and schedules from room templates. |
| HVAC efficiency | Generic `SYST0000` value `2.5`; generator type/capacity missing | Document generator type, capacity band, EER/SEER or SCOP, controls and system outputs. |
| Dynamic evidence | Current cooling/CO2 values were read before the APS metric conversion fix | Rerun before resizing plant; then verify the metric unit/conversion trace and complete annual outputs. |
| SIA 4010 evidence | `0/5` official evidence families | Attach official evidence files and class/test manifests before any validation claim. |

The complete model-specific sequence is documented in
`SIA_COMPATIBLE_MODEL_REFERENCE_ACTIONS.md`.

## SIA 380/2: VE Inputs and Reference-Project Diagnostics

Unless a row explicitly says otherwise, the values in the following component
tables are reference-project inputs used by the SIA 380/2 calculation method.
The checker reports deviations as `REFERENCE_DEVIATION`; it does not turn them
into standalone building-compliance failures.

### Project, Climate and Geometry

| Input | Required value | Type | Script impact | Professional evidence |
| --- | --- | --- | --- | --- |
| Active VE project path | Saved project folder, not a temporary VE copy | evidence | Preflight check | Screenshot/path of the open project. |
| Weather/climate basis | SIA 2028 DRY / CH2018 basis where applicable | evidence | Coverage warning until confirmed | Weather file name, location, altitude and climate scenario. |
| Thermal rooms/zones | All heated/cooled rooms must be extracted | evidence | No-room models are not checkable | Room schedule/export with area and volume. |
| SIA 2024 use category | One category per thermal zone | evidence | Required for schedules, gains, ventilation and lighting assumptions | Room-to-SIA-2024 mapping table. |

### Envelope U-Values

Values are source-traced to SIA 380/2:2022 Table 3 and are reference-project
diagnostics.

| VE input | Required value | Type | Target value | Script impact | Professional evidence |
| --- | ---: | --- | ---: | --- | --- |
| External wall U-value | `<= 0.20 W/(m2K)` | max | `0.14 W/(m2K)` | Automated when surface is classified as external wall | CDB construction build-up and U-value source. |
| External wall against ground U-value | `<= 0.30 W/(m2K)` | max | `0.20 W/(m2K)` | Evidence/adjacency dependent | Boundary condition and construction proof. |
| Internal non-bearing partition U-value | `<= 0.30 W/(m2K)` | max | `0.30 W/(m2K)` | Evidence/adjacency dependent | Boundary condition and construction proof. |
| Internal bearing partition U-value | `<= 2.70 W/(m2K)` | max | `2.70 W/(m2K)` | Evidence/adjacency dependent | Boundary condition and construction proof. |
| Internal wall to unconditioned area U-value | `<= 0.28 W/(m2K)` | max | `0.20 W/(m2K)` | Evidence/adjacency dependent | Boundary condition and construction proof. |
| Ground floor U-value | `<= 0.30 W/(m2K)` | max | `0.20 W/(m2K)` | Automated when surface is classified as floor | Boundary condition and CDB construction proof. |
| Intermediate floor U-value | `<= 0.64 W/(m2K)` | max | `0.64 W/(m2K)` | Evidence/adjacency dependent | Boundary condition and construction proof. |
| Intermediate floor to unconditioned area U-value | `<= 0.30 W/(m2K)` | max | `0.20 W/(m2K)` | Evidence/adjacency dependent | Boundary condition and construction proof. |
| Flat roof U-value | `<= 0.20 W/(m2K)` | max | `0.14 W/(m2K)` | Automated when surface is classified as roof | CDB construction build-up and U-value source. |
| Thermal bridge psi/chi | `0.00` retained value | max/evidence | `0.00` | Evidence requirement | Thermal bridge calculation or reviewer statement. |

### Windows, Glazing and Openings

Values are source-traced to SIA 380/2:2022 Table 2 and are reference-project
diagnostics.

| VE input | Required value | Type | Target value | Script impact | Professional evidence |
| --- | ---: | --- | ---: | --- | --- |
| Window Uw | `<= 1.10 W/(m2K)` | max | `0.88 W/(m2K)` | Automated when CDB/opening Uw is available | Glazing/frame CDB export or manufacturer data. |
| Glazing normal solar factor `g_perp` | `<= 0.50` | max | `0.50` | Automated when EN 410 `bs_en_410` is available | EN 410 value or manufacturer proof. |
| Visible light transmittance `tau_v` | `>= 0.70` | min | `0.70` | Automated when CDB value is available | CDB or manufacturer transmittance proof. |
| Window frame fraction `ff` | `<= 0.25` | max | `0.25` | Automated when frame fraction is available | Frame/glass split or facade schedule. |
| Glazing ratio / WWR | Delegated to SIA 2024/reference calculation | evidence | No standalone hard limit encoded | The checker only uses `0.30` as a design-review indicator | SIA 2024 room-use and facade ratio justification. |
| Door U-value when treated as opening | `<= 1.10 W/(m2K)` | max | `0.88 W/(m2K)` | Conservative opening-style check | Confirm whether door is opening or opaque construction. |

### Solar Protection

Values are source-traced to SIA 380/2:2022 table 10 and SIA 4010 table 65.

| VE input | Required value | Type | Script impact | Professional evidence |
| --- | --- | --- | --- | --- |
| Solar protection type/category | Category 1 to 5 where applicable | evidence | Required for SIA 4010 test 2 readiness | Blind type, position, optical data and control note. |
| Active control profile | Threshold/control documented | evidence | Required for solar-control readiness | VE profile, control thresholds and operating logic. |
| Active `g_total_with_shading` | Required if glazing `g_perp > 0.50` and shading is used to justify compliance | evidence | Missing value raises an alert when `g_perp > 0.50` | Manufacturer data or reviewed ISO 52022-3 / ISO 15099 calculation. |
| Fabric blind method | Equal direct/diffuse solar transmission/reflection, or active total glazing-plus-shading g-value | evidence | Required for SIA 4010 solar variants | Reviewer note and source calculation. |

Solar-protection optical category values encoded in the project:

| Category | Type | Solar reflectance | Solar transmittance |
| ---: | --- | ---: | ---: |
| 1 | lamellae | `0.70` | `0.00` |
| 1 | fabric | `0.50` | `0.25` |
| 2 | lamellae | `0.70` | `0.00` |
| 3 | lamellae | `0.50` | `0.00` |
| 3 | fabric | `0.35` | `0.25` |
| 4 | lamellae | `0.30` | `0.00` |
| 4 | fabric | `0.25` | `0.10` |
| 5 | fabric | `0.20` | `0.05` |

### Infiltration and Ventilation

| VE input | Required value | Type | Target value | Script impact | Professional evidence |
| --- | ---: | --- | ---: | --- | --- |
| Infiltration | `<= 0.15 m3/(h.m2)` | max | `0.15 m3/(h.m2)` | Automated only when units are comparable | Air-exchange template and unit conversion basis. |
| Ventilation rate | No single universal SIA 380/2 threshold encoded | evidence | Determined by use category and airflow band | Presence removes missing-data alert | Outdoor/supply airflow per room and floor area. |
| Ventilation control | See control table below | allowed/evidence | See target column | Used for table 4 readiness | Mono/multizone, fan control, sensors and schedules. |

SIA 380/2 ventilation control table encoded in the project:

| System | Airflow band m3/(h.m2) | Limit control | Target control |
| --- | --- | --- | --- |
| monozone | `<=3` | one speed, time schedule control | two speeds 67/100%, time schedule control |
| monozone | `3-6` | two speeds 67/100%, time schedule control | variable speed >=25%, demand control by occupancy |
| monozone | `>6` | variable speed >=25%, demand control by occupancy | variable speed >=25%, demand control by gas sensor |
| multizone | `<=3` | two speeds 67/100%, time schedule control by zone | two speeds 67/100%, occupancy control by zone |
| multizone | `3-6` | two speeds 67/100%, occupancy control by zone | variable speed >=25%, demand control by occupancy per room |
| multizone | `>6` | variable speed >=25%, demand control by gas sensor by zone | variable speed >=25%, demand control by gas sensor per room |

### AHU, Heat Recovery and Pressure Drops

| VE input | Limit value | Type | Target value | Script impact | Professional evidence |
| --- | ---: | --- | ---: | --- | --- |
| Ventilation efficiency indicator | `1.0` | min/evidence | `1.4` | Evidence gap until extracted | AHU/system schedule. |
| Duct airtightness class | `C` | allowed | `C` | Evidence gap | Duct leakage class. |
| AHU airtightness class | `L2` | allowed | `L1` | Evidence gap | AHU leakage class. |
| AHU heat transfer | `<= 0.70 W/(m2K)` | max | `0.50 W/(m2K)` | Evidence gap | AHU data sheet. |
| Supply duct heat transfer in unconditioned space | `<= 15 W/K` | max | `10 W/K` | Evidence gap | Duct location and heat loss evidence. |
| Supply pressure drop | `<= 700 Pa` | max | `550 Pa` | Evidence gap | Fan/AHU pressure-drop data. |
| Extract pressure drop | `<= 500 Pa` | max | `350 Pa` | Evidence gap | Fan/AHU pressure-drop data. |
| Heat recovery pressure drop | `<= 300 Pa` retained limit | max | `400 Pa` target encoded | Evidence gap | Recovery unit data and reviewer confirmation. |
| Heat recovery temperature efficiency | `>= 0.73` | min | `0.78` | Evidence gap | Recovery efficiency source. |
| Heat recovery humidity efficiency | `>= 0.00` | min | `0.60` | Evidence gap | Moisture recovery evidence where applicable. |
| Cooling control delta T | `-1.8 K` retained value | evidence | `0.0 K` | Evidence gap | Cooling control note. |
| Heating control delta T | `1.2 K` retained value | evidence | `0.0 K` | Evidence gap | Heating control note. |

### Cooling Generator EER/SEER

Values are source-traced to SIA 380/2:2022 tables 5 to 9.

| Generator type | Capacity band kW | Minimum EER | Minimum SEER |
| --- | --- | ---: | ---: |
| air cooled | `<=12` | `2.90` | `3.80` |
| air cooled | `12-50` | `3.00` | `3.90` |
| air cooled | `50-150` | `3.10` | `4.00` |
| air cooled | `150-450` | `3.20` | `4.20` |
| air cooled | `450-1000` | `3.40` | `4.40` |
| water cooled | `12-50` | `4.05` | `4.50` |
| water cooled | `50-150` | `4.25` | `4.80` |
| water cooled | `150-450` | `4.65` | `5.50` |
| water cooled | `450-1000` | `5.05` | `6.10` |
| water cooled | `>1000` | `5.50` | `6.70` |

Required VE/evidence inputs:

- generator type;
- rated capacity band;
- EER and SEER;
- part-load curve where applicable;
- heat rejection type;
- free-cooling availability;
- distribution temperature and flow control;
- pump control;
- cooling storage type, location and control where applicable.

### Heating / Heat Pump SCOP

Values are source-traced to SIA 380/2:2022 tables 5 to 9 and delegated SIA
384/3 evidence where applicable.

| Generator type | Capacity band kW | Minimum SCOP |
| --- | --- | ---: |
| air/water heat pump | `<=12` | `3.00` |
| air/water heat pump | `12-50` | `3.10` |
| air/water heat pump | `50-150` | `3.20` |
| ground-source heat pump | `12-50` | `4.00` |
| ground-source heat pump | `50-150` | `4.20` |
| ground-source heat pump | `150-450` | `4.60` |
| ground-source heat pump | `450-1000` | `5.00` |
| ground-source heat pump | `>1000` | `5.50` |

Required VE/evidence inputs:

- heating generator type;
- rated capacity band;
- SCOP or SIA 384/3 hourly-method evidence;
- emission, distribution, storage and generation data;
- auxiliary energy;
- solar thermal and cogeneration data where applicable.

### PV and Electricity

| VE input | Required value | Type | Target value | Script impact | Professional evidence |
| --- | ---: | --- | ---: | --- | --- |
| PV power | `10 W/m2 SRE` | evidence | `10 W/m2 SRE` | Evidence gap | PV schedule and SRE basis. |
| PV conversion efficiency | `0.90` | min/evidence | `0.90` | Evidence gap | Inverter/system performance data. |
| PV module efficiency | Not a limit encoded | evidence | `0.17` | Evidence gap | Module data sheet. |
| General technical electricity | Delegated to SIA 2056 / SIA 2024 / SIA 387/4 | evidence | Not encoded as a universal threshold | Evidence gap | Lighting, user electricity and technical electricity breakdown. |

### Internal Gains, Schedules and Lighting

SIA 380/2 delegates many usage values to SIA 2024 and SIA 387/4. The checker
therefore requires evidence instead of inventing fixed values.

| VE input | Required value | Type | Script impact | Professional evidence |
| --- | --- | --- | --- | --- |
| Occupancy gains | Present and mapped to SIA 2024 use category | evidence | Missing data alert if absent | Room template and SIA 2024 mapping. |
| Equipment gains | Present and mapped to SIA 2024 use category | evidence | Missing data alert if absent | Room template and SIA 2024 mapping. |
| Lighting power density | Present and mapped to SIA 387/4 / SIA 2024 | evidence | Missing data alert if absent | Lighting schedule and control note. |
| Occupancy schedule | Auditable hourly/weekly profile | evidence | Coverage gap if absent | Exported VE profile or reviewer workbook. |
| Equipment schedule | Auditable hourly/weekly profile | evidence | Coverage gap if absent | Exported VE profile or reviewer workbook. |
| Lighting schedule/control | Auditable schedule plus daylight/presence control type | evidence | Required for SIA 4010 test 3 readiness | SIA 387/4 control mapping. |
| HVAC schedule/setpoints | Auditable profiles and setpoints | evidence | Required for dynamic method confidence | Heating/cooling setpoint and calendar proof. |
| Shading schedule/control | Auditable solar-control thresholds | evidence | Required for SIA 4010 test 2 readiness | Shading device and control proof. |

### APS/Vista Dynamic Outputs

| APS/Vista output | Required value | Type | Script impact | Professional evidence |
| --- | --- | --- | --- | --- |
| Heating demand/load | Present in APS/Vista | evidence | Used for dynamic results and SIA 4010 test 7 readiness | APS output and timestep basis. |
| Cooling demand/load | Present in APS/Vista | evidence | Used for dynamic results and SIA 4010 test 7 readiness | APS output and timestep basis. |
| Room operative temperature | Complete annual hourly/sub-hourly series for every assessed room | evidence | Evaluated against the SIA 180 upper/lower curves | APS output and room/result-variable traceability. |
| SIA 180 upper/lower curves | Complete annual series aligned with every room temperature series | evidence | Required for annual comfort; fixed 26 C / 27 C indicators are diagnostic only | APS variable mapping and curve provenance. |
| Occupancy | Complete aligned annual series for every assessed room | evidence | Restricts the annual comfort assessment to occupied periods | Schedule/profile proof. |
| Window operability | Explicitly known for every assessed room | evidence | Operable rooms use a 0 h upper-exceedance limit; otherwise 100 h for new and 400 h for existing buildings | MacroFlo/opening evidence and reviewer confirmation. |
| Lighting energy | Present where available | evidence | SIA 4010 test 3 readiness | APS variable mapping. |
| Fan energy | Present where available | evidence | Tests 4 to 7 readiness | APS variable mapping. |
| Pump energy | Present where available | evidence | Test 7 readiness | APS variable mapping. |
| Auxiliary energy | Present where available | evidence | Test 7 readiness | APS variable mapping. |
| Heating/cooling coil energy | Present where available | evidence | Tests 4 and 7 readiness | APS variable mapping. |
| CO2 | Present or manual evidence | evidence | Tests 4 to 6 readiness | APS variable mapping; fractions are normalized to ppm by the checker. |
| Relative humidity | Present where available | evidence | Tests 5 to 6 readiness | APS variable mapping. |
| Final energy by carrier/system | Present or official workbook output | evidence | SIA 4010 test 7 remains partial without it | Filled official workbook or system-energy export. |

### Whole-Project SIA 380/2 Comparison

Component diagnostics cannot establish the final method result. The project
must include one reviewed record named:

```text
SIA3802_global_reference_comparison_<project>.csv
```

The record is accepted only when `comparison_scope` is
`complete_sia3802_project`, the review is accepted, project and reference
values are numeric and use the same stated unit, the project value is not above
the reference value, and reviewer/date/source fields are complete. The checker
returns `NOT_CHECKABLE` when this proof is absent or incomplete.

## SIA 4010: Official Validation Inputs

### Core Rule

SIA 4010 has no autonomous building-level max/min threshold for:

- heating demand;
- cooling demand;
- primary energy;
- CO2 emissions;
- renewable-energy share.

The checker therefore keeps these indicators separate from official validation.
Official SIA 4010 validation requires official test cases, official evaluation
workbooks, candidate results, reference comparisons and validation class
confirmation.

### Official Evidence Families

All five evidence families are required before the workflow can reach
`READY_FOR_OFFICIAL_REVIEW`.

| Evidence family | Required filename prefix | Accepted extensions | Example |
| --- | --- | --- | --- |
| Official SIA test specifications | `SIA4010_official_test_specs_` | `.pdf`, `.docx`, `.xlsx` | `SIA4010_official_test_specs_class_4B.pdf` |
| Official SIA Excel evaluation workbooks | `SIA4010_official_evaluation_workbook_` | `.xlsx`, `.xlsm` | `SIA4010_official_evaluation_workbook_class_4B.xlsx` |
| Candidate software/model results | `SIA4010_candidate_results_` | `.xlsx`, `.xlsm`, `.csv`, `.pdf` | `SIA4010_candidate_results_class_4B_test_1_to_7.xlsx` |
| Reference-result comparisons | `SIA4010_reference_comparison_` | `.pdf`, `.xlsx`, `.xlsm`, `.csv`, `.png` | `SIA4010_reference_comparison_class_4B.pdf` |
| Validation class confirmation | `SIA4010_validation_class_confirmation_` | `.pdf`, `.docx`, `.txt`, `.csv` | `SIA4010_validation_class_confirmation_class_4B.pdf` |

Optional parsed manifests:

| Manifest | Required columns | Accepted review statuses |
| --- | --- | --- |
| `SIA4010_evidence_index_<project>.csv` | `evidence_family`, `provided_file_name`, `source_authority`, `version_or_date`, `tests_covered`, `reviewer`, `review_status` | `provided`, `present`, `reviewed`, `accepted`, `approved`, `complete`, `ready_for_official_review` |
| `SIA4010_class_validation_<project>.csv` | `validation_class`, `selected`, `required_tests`, `reviewer`, `review_status`, `review_date`, `source_authority`, `source_reference` | `selected`, `requested`, `confirmed`, `reviewed`, `accepted`, `approved`, `ready_for_official_review` |
| `SIA4010_official_test_results_<project>.csv` | `test_id`, `status`, `reference_file`, `candidate_file`, `deviation`, `tolerance`, `reviewer`, `review_date`, `source_authority`, `source_reference` | PASS: `pass`, `passed`, `validated`, `official_pass`, `official_validated`; FAIL: `fail`, `failed`, `not_passed`, `rejected` |

### Validation Tests

| Test | Scope | Required VE/model inputs | Official requirement |
| --- | --- | --- | --- |
| Test 1 | Basic envelope tests according to EN ISO 52016-1 / ASHRAE 140 | zones/rooms, external envelope, opaque U-values, external windows/openings, dynamic APS file | Official test model and reference outputs. |
| Test 2 / 2A-2D | Solar-protection control according to SIA 387/4 and SIA 380/2 Annex A | external glazing, EN 410 g-values, exact shading type/control, climate/use/infiltration diagnostic | Official test 2 evaluation file and comparison for every required exact variant. |
| Test 3 / 3A-3L | Lighting control according to SIA 387/4 | lighting power, daylight control, exact lighting/shading-control identifiers and lighting energy outputs | Official lighting evaluation file and comparison for every required exact variant. |
| Test 4 | Single-room all-air air-conditioning system | HVAC systems, ventilation/airflow, coil outputs, CO2, temperature hourly outputs | Official amphitheatre test model/evaluation file. |
| Test 5 | Multizone AHU with reheater, cooler, humidifier and heat/moisture wheel | multizone AHU, fan control, heat/moisture recovery, humidifier type/control | Official test 5 variant/evaluation file. |
| Test 6 | Three-stage ventilation with heat recovery, constant airflow and overflow | ventilation systems, staged/constant airflow, heat recovery, restaurant/kitchen overflow | Official test 6 evaluation file. |
| Test 7 | Heating/cooling emission, distribution, storage and generation | heating/cooling demand, final energy by system/carrier, distribution/storage/generation, pump/fan/auxiliary energy | Official test 7 loads and evaluation file. |

### Validation Classes

| Class | Required tests | Application | Solar-protection condition |
| --- | --- | --- | --- |
| 1A | Test 1 and Test 2A | Cooling need assessment and basic thermal load calculation | Without sun-position-dependent control, e.g. fabric awnings. |
| 1B | Test 1 and Tests 2B-2D | Cooling need assessment and basic thermal load calculation | Rafflamellenstoren / venetian blinds. |
| 2A | Test 1, Test 2A, Tests 3A-3F | Lighting energy according to SIA 387/4, heating demand and cooling demand | Without sun-position-dependent control, e.g. fabric awnings. |
| 2B | Test 1, Tests 2B-2D and Tests 3A-3L | Lighting energy according to SIA 387/4, heating demand and cooling demand | Rafflamellenstoren / venetian blinds. |
| 3 | Test 1 and Tests 4 to 6 | Need assessment for humidification and dehumidification | Not separately restricted in the manager-provided register. |
| 4A | Test 1, Test 2A, Tests 3A-3F, Tests 4 to 7 | System-related thermal load calculation, cooling energy demand and heating energy demand | Without sun-position-dependent control, e.g. fabric awnings. |
| 4B | Test 1, Tests 2B-2D, Tests 3A-3L and Tests 4 to 7 | System-related thermal load calculation, cooling energy demand and heating energy demand | Rafflamellenstoren / venetian blinds. |
| 5 | Test 7 | Cooling and heating energy demand with existing demand profiles | Not separately restricted in the manager-provided register. |

### Climate and Test Setup Complements

| SIA 4010 input | Required setup |
| --- | --- |
| Summer overheating climate | Use SIA 2028 DRY data; CH2018/RCP 8.5 period 2035 may or must be used according to the summer overheating application. |
| Heating design preconditioning | Use the coldest 4-day January period from the normal DRY, with the preceding 14 normal DRY days as preconditioning, avoiding weekends via the calendar. |
| Cooling design preconditioning | Use the hottest relevant days in June, August and October, with preceding 14 normal DRY days as preconditioning; RCP 8.5 period 2035 DRY is recommended for the climate scenario. |
| Fabric blind solar method | Use equal direct/diffuse solar transmission/reflection, or replace glazing g with total glazing-plus-shading g when shading is active. |

Setpoint curve shifts encoded from SIA 4010:

| Use category | Lower curve shift | Upper curve shift |
| --- | ---: | ---: |
| `SIA2024_3.04` | `+1 K` | not encoded |
| `SIA2024_5.01_to_5.03` | `+1 K` | not encoded |
| `SIA2024_6.03_to_6.04` | `+1 K` | `+2 K` |
| `SIA2024_9.01` | `+3 K` | `+4 K` |

### SIA 4010 Leakage Factors

| System | Class | Factor | Default use |
| --- | --- | ---: | --- |
| ducts | unknown | `1.45` | Default existing or unknown. |
| ducts | A | `1.18` | Evidence value. |
| ducts | B | `1.06` | Default new. |
| ducts | C | `1.02` | SIA 380/2 retained duct class. |
| ducts | D | `1.00` | Evidence value. |
| AHU | L3 | `1.10` | Default existing. |
| AHU | L2 | `1.04` | SIA 380/2 retained AHU class. |
| AHU | L1 | `1.01` | Default new / target AHU class. |

### SIA 4010 System Data Families

| Family | Required inputs | Source scope |
| --- | --- | --- |
| ventilation | airflow control identifiers; duct and AHU leakage/airtightness; fan control and pressure drops; heat/moisture recovery; humidification type/control/energy carrier; AHU and duct heat losses; zone design airflows | SIA 4010 pages PDF 11-17 and 24-28, tables 1-23 and 34-35 |
| cooling | cooling generation temperature control; distribution temperature/flow control; pump control; storage type/location/control; generator type; heat rejection type; free cooling availability; part-load EER data | SIA 4010 pages PDF 18-22 and 29-36, tables 24-33 and 36-48 |
| heating | BACS/control identifiers; emission, distribution, storage and generation data; boiler/generator input data; heat pump calculation according to SIA 384/3 hourly method; solar thermal and cogeneration inputs where applicable | SIA 4010 pages PDF 23 and 36-44, tables 49-59 |
| domestic hot water | DHW heat demand and hourly load cycles if coupled to heat generation | SIA 4010 page PDF 44, referenced to SIA 385/2 |
| general building electricity | general technical electricity, user electricity/appliances, lighting, PV inputs | SIA 4010 page PDF 44, referenced to SIA 2056 / SIA 2024 / SIA 387/4 |
| photovoltaics | number/area/orientation/tilt of PV modules, peak power coefficient, system performance factor | SIA 4010 page PDF 45, tables 60-61 |

### SIA 4010 Technical Identifiers

These are accepted identifiers currently encoded for system/evidence mapping.

| Identifier | Accepted values |
| --- | --- |
| `SUP_AIR_TEMP_CTRL` | `NO_CTRL`, `CONST`, `ODA_COMP`, `LOAD_COMP` |
| `SUP_AIR_FLW_CTRL` | `ODA`, `LOAD` |
| `AIR_FLOW_CTRL` | `NO_CTRL`, `ON/OFF_CTRL`, `MULTI_STAGE`, `VARIABLE` |
| `SYS_TYPE` | `SINGLE_ZONE`, `MULTI_ZONE` |
| `FAN_CTRL` | `NO_CTRL`, `CONST_PRES`, `MIN_PRES`, `DIRECT` |
| `FAN_MOTOR_LOCATION` | `IN_AIR`, `OUTS_AIR` |
| `GND_PREH_CTRL` | `NO_CTRL`, `BYPASS` |
| `RCA_CTRL` | `FIX`, `VARIABLE` |
| `HEAT_REC_TYPE` | `PLATE`, `ROT_NH`, `ROT_HYG`, `ROT_SORP`, `PUMP_CIRC`, `OTHER` |
| `HEAT_REC_CTRL` | `NO_CTRL`, `BYPASS`, `SPEED`, `HYDR` |
| `FROST_PROTECTION` | `PREH`, `BYPASS`, `RECIRC` |
| `DEFR_CTRL` | `DIRECT`, `INDIRECT` |
| `SUP_FAN_LOCATION_HR` | `UP_HR`, `DOWN_HR` |
| `ETA_FAN_LOCATION_HR` | `UP_HR`, `DOWN_HR` |
| `HUM_TYPE` | `CONTACT`, `ROT_SPRAY`, `HI_PRES`, `HYBRID`, `STEAM`, `OTHER` |
| `HUM_CTRL` | `NO_CTRL`, `ON_OFF`, `SPEED` |
| `HUM_STEAM_ENERGY` | `HUM_CR_EL`, `HUM_CR_GAS`, `HUM_CR_SOL`, `HUM_CR_OTHER` |
| `AHU_LOCATION` | `CND`, `NC` |
| `CLG_GEN_TMP_CTRL` | `CONST`, `VARIABLE` |
| `CLG_DISTR_TMP_CTRL` | `CONST`, `ODA_COMP`, `MAX_TMP` |
| `CLG_DISTR_FLW_CTRL` | `CONST`, `VARIABLE` |
| `CLG_EN_DISTR_CTRL` | `NO_CTRL`, `PRIO` |
| `PUMP_CTRL_CODE` | `0`, `1`, `2`, `3`, `4` |
| `CLG_GENERATOR_TYPE` | `COMP`, `ABS`, `OTHER` |
| `HEAT_REJECTION_TYPE` | `AIR_C_COND`, `DRY`, `WET`, `HYBRID`, `OTHER` |
| `FREE_COOLING` | `YES`, `NO` |
| `HBRD_HEAT_REJ_CTRL` | `TEMP`, `MAX_POWER` |
| `CLG_STORAGE_TYPE` | `STO_TYPE_CW`, `STO_TYPE_ICE`, `STO_TYPE_PCM` |
| `CLG_STORAGE_LOCATION` | `CLG_STO_LOC_CND`, `CLG_STO_LOC_NC`, `CLG_STO_LOC_EXT` |
| `CLG_STO_CTRL` | `CONT`, `TIME`, `TEMP`, `LOAD_PRED` |

## Minimum VE Model Checklist Before Rerunning the Script

For a small three-room model, the fastest path to a clean readiness report is:

1. Assign every external wall, roof and floor to traceable constructions and
   review them against the SIA 380/2 reference-project U-values.
2. Use traceable glazing and review `Uw`, EN 410 `g_perp`, `tau_v` and `ff`
   against the Table 2 reference-project inputs.
3. If glazing `g_perp > 0.50`, attach reviewed active `g_total_with_shading`
   evidence. For the current automated checker, using `g_perp <= 0.50` is the
   cleanest route.
4. Add infiltration for every room in comparable `m3/(h.m2)` units and review
   it against the `0.15` reference-project input.
5. Add outdoor/supply ventilation rates for every room and document mono/multi
   zone control, airflow band and fan control.
6. Add occupancy, equipment, lighting gains and schedules for every room.
7. Add lighting control evidence compatible with SIA 387/4.
8. Add HVAC generator type, capacity band, EER/SEER or SCOP, pressure drops,
   fan/pump/auxiliary evidence and final energy by carrier.
9. Confirm weather/climate basis and rerun APS/Vista after every model change.
10. Provide the reviewed complete SIA 380/2 project/reference comparison; do
    not infer it from the component diagnostics.
11. For SIA 4010, select one validation class and attach all official evidence
    families; otherwise keep the report wording as readiness/prevalidation.

## Safe Compliance Wording

Use this wording until every model value and official evidence file is present:

> The VE model has been assessed using source-traced SIA 380/2 reference-project
> diagnostics, method gates and a SIA 4010 readiness/prevalidation workflow.
> The report identifies model diagnostics, delegated evidence requirements and
> official validation-package gaps. It is not a final SIA compliance certificate
> and does not establish SIA 4010 validation without the responsible authority's
> attestation.
