# SIA 380/2 Full Compliance Gap Audit

Date: 2026-07-06

This document explains what the current Swiss SIA Compliance Checker can verify
against SIA 380/2:2022, what is only partially covered, and what is still
missing before the project can support a complete professional compliance
claim. It is intentionally conservative: if the current code cannot trace a
value to a local standard reference, a VE API field, APS/Vista output, or a
reviewer evidence file, the item remains a gap.

## Standards Basis

The current implementation is based on the local project standards:

- `references/standards/SIA 380-2-2022 FR.pdf`
- `references/standards/SIA 4010-2023 FR.pdf`

SIA 380/2 also refers to other SIA standards and technical bases for some
inputs and calculation assumptions, including SIA 2024, SIA 2028, SIA 382/1,
SIA 384/3, SIA 387/4 and SIA 2056. The checker must not invent those delegated
values. Where SIA 380/2 delegates the value or method to another standard, the
current product reports the evidence requirement and blocks final wording until
the reviewer supplies a traceable mapping or accepted external evidence.

## Current Verdict

The project is a professional SIA 380/2 and SIA 4010 readiness/audit workflow.
It is not yet a final compliance certificate.

The strongest automated coverage today is:

- room and external-envelope extraction;
- external opaque surface U-value checks where the surface type is classified;
- roof U-value checks;
- window Uw checks;
- conservative EN 410 based `g_perp` handling when `bs_en_410` is exposed by
  the IESVE CDB API;
- visible transmittance and frame-fraction diagnostics when CDB values exist;
- infiltration diagnostics when VE exposes units that can be normalized to
  `m3/(h.m2)`;
- APS/Vista heating, cooling, temperature, occupancy and expanded optional
  outputs when `iesve.ResultsReader` exposes matching variables.

The main missing blocks for full SIA 380/2 compliance are:

- SIA 2024 use-category mapping for each room;
- complete schedules for occupancy, equipment, lighting, shading and HVAC;
- full ventilation-control and AHU evidence from SIA 380/2 table 4;
- cooling generator EER/SEER evidence by type and power band;
- heating/heat-pump SCOP and SIA 384/3 evidence by type and power band;
- final energy by system/carrier and complete generation/distribution/storage
  chain;
- official SIA 4010 execution/evaluation workbooks or reviewer-accepted
  equivalent evidence for tests 1 to 7 and validation classes 1A to 5.

## Source-Traced Values Currently Encoded

The following values are currently encoded in `swiss_sia.config` and checked or
reported with source references to the local SIA 380/2 PDF.

### Envelope and Openings

| Criterion | Limit | Target | Current automation |
| --- | ---: | ---: | --- |
| Window Uw | 1.10 W/(m2K) | 0.88 W/(m2K) | Automated when VE/CDB exposes Uw |
| Glazing normal solar factor `g_perp` | 0.50 | 0.50 | Partial; EN 410 value is accepted automatically, raw CDB `g_value` is not |
| Glazing light transmittance | 0.70 | 0.70 | Partial; depends on CDB value availability |
| Window frame fraction | 0.25 | 0.25 | Partial; depends on CDB frame/glass evidence |
| Infiltration reference | 0.15 m3/(h.m2) | 0.15 m3/(h.m2) | Partial; only when VE units are explicit enough |
| External wall U-value | 0.20 W/(m2K) | 0.14 W/(m2K) | Automated when surface classification is reliable |
| Flat roof U-value | 0.20 W/(m2K) | 0.14 W/(m2K) | Automated when surface classification is reliable |
| Ground floor U-value | 0.30 W/(m2K) | 0.20 W/(m2K) | Partial; boundary classification must be confirmed |
| External wall against ground U-value | 0.30 W/(m2K) | 0.20 W/(m2K) | Partial; boundary classification must be confirmed |
| Internal wall to unconditioned area | 0.28 W/(m2K) | 0.20 W/(m2K) | Partial; adjacency classification required |
| Internal non-bearing partition | 0.30 W/(m2K) | 0.30 W/(m2K) | Partial; adjacency classification required |
| Internal bearing partition | 2.70 W/(m2K) | 2.70 W/(m2K) | Partial; adjacency classification required |
| Intermediate floor | 0.64 W/(m2K) | 0.64 W/(m2K) | Partial; adjacency classification required |
| Intermediate floor to unconditioned area | 0.30 W/(m2K) | 0.20 W/(m2K) | Partial; adjacency classification required |
| Thermal bridge psi/chi | 0.00 | 0.00 | Evidence requirement only |

### Ventilation and AHU

| Criterion | Limit | Target | Current automation |
| --- | ---: | ---: | --- |
| Ventilation efficiency indicator | 1.0 | 1.4 | Not fully automated |
| Heat recovery temperature efficiency | 0.73 | 0.78 | Not fully automated |
| Heat recovery humidity efficiency | 0.00 | 0.60 | Not fully automated |
| Supply pressure drop | 700 Pa | 550 Pa | Not fully automated |
| Extract pressure drop | 500 Pa | 350 Pa | Not fully automated |
| Heat recovery pressure drop | 300 Pa | 400 Pa | Not fully automated |
| Duct airtightness class | C | C | Evidence requirement only |
| AHU airtightness class | L2 | L1 | Evidence requirement only |
| AHU heat transfer | 0.70 W/(m2K) | 0.50 W/(m2K) | Evidence requirement only |
| Supply duct heat transfer in unconditioned space | 15 W/K | 10 W/K | Evidence requirement only |
| Heating control delta T | 1.2 K | 0.0 K | Evidence requirement only |
| Cooling control delta T | -1.8 K | 0.0 K | Evidence requirement only |

### Cooling, Heating and PV

| Criterion | Limit/Source | Current automation |
| --- | --- | --- |
| Cooling EER/SEER by generator type and power band | SIA 380/2 tables 5 to 9 | Not fully automated |
| Heating/heat-pump SCOP by type and power band | SIA 380/2 tables 5 to 9 and delegated evidence | Not fully automated |
| PV power | 10 W/m2 SRE | Evidence requirement only |
| PV conversion efficiency | 0.90 | Evidence requirement only |
| PV module efficiency target | 0.17 | Evidence requirement only |

## Implementation Coverage by Compliance Area

| Area | Current status | What the code does now | Missing for complete compliance |
| --- | --- | --- | --- |
| Climate and project setup | Partial | Reports active project and APS weather references when exposed | SIA 2028 DRY / CH2018 climate confirmation and altitude/location trace |
| Room geometry | Automated | Extracts thermal rooms, floor area and volume | Reviewer confirmation that VE zones match the SIA calculation zones |
| SIA 2024 use categories | Partial | Reports rooms and gains, but does not classify official use categories | One official SIA 2024 mapping per thermal room |
| External envelope | Automated/partial | Extracts surfaces, U-values, tilt and adjacency metadata | Full adjacency and boundary validation for all non-standard surfaces |
| Window Uw | Automated | Checks external windows against the encoded SIA 380/2 value | Manufacturer/CDB trace where VE values are disputed |
| Glazing `g_perp` | Partial | Uses EN 410 `bs_en_410` when exposed; flags raw CDB `g_value` as non-comparable | EN 410 or manufacturer evidence for every glazing construction |
| Light transmittance | Partial | Reads CDB visible transmittance when available | Evidence for constructions where VE does not expose tau |
| Frame fraction | Partial | Checks frame fraction when CDB exposes it | Confirm frame/glass split or provide facade evidence |
| Solar protection | Partial | Reports type, control, category and active `g_total` when exposed | Manufacturer/proven `g_total_with_shading` and control mapping |
| Infiltration | Partial | Converts explicit compatible units to `m3/(h.m2)` | Unit-safe mapping for all infiltration templates |
| Internal gains | Partial | Extracts lighting/equipment/occupancy indicators from VE where available | SIA 2024 profile mapping and schedules |
| Schedules | Not implemented | Listed as a blocker | Full auditable schedule export or reviewer workbook |
| Ventilation rates | Partial | Extracts room ventilation rates where VE exposes them | Table 4 control class, airflow band and AHU evidence |
| AHU heat recovery | Not implemented | Listed as evidence gap | Recovery type, efficiencies, pressure drops, leakage and controls |
| Cooling EER/SEER | Not implemented | Listed as evidence gap | Generator type, capacity band, EER/SEER and part-load evidence |
| Heating SCOP | Not implemented | Listed as evidence gap | Heat-pump/heating type, capacity band and SCOP evidence |
| Lighting control | Partial | Reads lighting gains and now APS lighting energy if available | SIA 387/4 daylight/presence/control variant mapping |
| Dynamic APS results | Partial | Reads APS rooms, loads, temperatures, occupancy and optional system outputs | Official method setup, climate/use validation and reference comparisons |
| Hourly temperatures | Partial | Counts occupied hours above 26 C and 27 C when temperature and occupancy exist | Official comfort/overheating criterion mapping |
| Heating/cooling demands | Partial | Integrates APS heating/cooling loads to kWh and kWh/m2 | Official annual/reference comparison workflow |

## New APS/Vista Outputs Added in This Pass

The APS/Vista collector now attempts to extract the following optional outputs
per room when `iesve.ResultsReader.get_variables()` exposes matching APS
variables:

- lighting energy;
- fan energy;
- pump energy;
- auxiliary energy;
- heating coil energy;
- cooling coil energy;
- peak and average CO2;
- peak and average relative humidity.

These values improve readiness for SIA 4010 tests 3, 4, 5 and 7. They do not
replace official SIA 4010 comparison workbooks or reviewer acceptance.

## Required Inputs Before a Complete Claim

To move from professional readiness reporting to a complete compliance package,
the project still needs:

- a room-by-room SIA 2024 use-category mapping;
- schedule exports or reviewer-filled schedule evidence;
- official climate/weather basis evidence for the simulated project;
- EN 410/manufacturer glazing evidence for all glazing constructions;
- `g_total_with_shading` evidence where solar protection is active or needed;
- ventilation system and AHU evidence for controls, flows, pressure drops,
  heat/moisture recovery, leakage and heat transfer;
- cooling generator EER/SEER evidence by type and power band;
- heating/heat-pump SCOP evidence by type and power band;
- final energy by system/carrier and auxiliary energy evidence;
- SIA 4010 evidence package for tests 1 to 7 and selected classes 1A to 5.

## Safe Report Wording

Use this wording until all missing evidence is resolved:

> The workbook is a SIA 380/2 and SIA 4010 readiness and audit report based on
> the available VE model, CDB construction data, APS/Vista outputs and local
> source-traced rules. It is not a final SIA compliance certificate and does not
> replace the official SIA 4010 validation package or reviewer acceptance.

## Immediate Next Actions

1. Run the updated VE script and confirm the `DYNAMIC RESULTS` sheet now shows
   lighting, fan, pump, auxiliary, coil, CO2 and humidity columns.
2. Run the updated extraction probe and inspect `aps_diagnostics` to see the
   real APS variable names exposed by the client model.
3. Fill the evidence templates for SIA 2024 mappings, glazing proof, schedules,
   AHU/ventilation, cooling EER/SEER and heating SCOP.
4. Keep SIA 4010 tests 1 to 7 in PDF-based prevalidation mode until official or
   reviewer-accepted comparison evidence is provided.
