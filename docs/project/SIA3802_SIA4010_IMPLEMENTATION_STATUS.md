# SIA 380/2 and SIA 4010 Implementation Status

## Purpose and Claim Boundary

This document is the implementation truth table for the IESVE Swiss compliance
workflow. It separates three concepts that must never be merged:

- **Automated check**: the code obtains a traceable VE/CDB/APS value and applies
  a locally encoded criterion from the available standards.
- **Readiness check**: the code confirms that model inputs and result families
  needed by a standard test are present, but does not reproduce the official
  comparison.
- **Official validation**: an authorised reviewer uses the official test
  specification, evaluation workbook, reference results and class confirmation.

The generated workbook is an audit and prevalidation artifact. It is not a SIA
certificate and must not be presented as one.

## SIA 380/2 Coverage

| Area | Implemented behaviour | Current conclusion | Remaining dependency |
| --- | --- | --- | --- |
| Geometry and model selection | Uses the documented real VE model at `project.models[0]`; extracts rooms, areas, volumes, surfaces and openings | Automated when the VE API exposes valid objects | Reviewer confirmation that VE zoning matches the assessment zoning |
| Reference-project envelope and windows | Compares classified walls, roofs, floors and windows with the inputs in Tables 2 and 3 | Automated diagnostic for elements with a valid comparable U-value | These component differences are not standalone compliance failures; the complete project/reference result is decisive |
| Reference-project glazing and solar protection | Prefers EN 410 `bs_en_410` for `g_perp`; retains raw CDB `g_value` as non-comparable; checks visible transmittance, frame fraction and shading evidence | Partial diagnostic and conservative | Manufacturer/CDB provenance and `g_total_with_shading` evidence when required; final decision remains global |
| Cooling-need screening | Integrates daily-equivalent internal gains and applies the three Table 1 window-support scenarios | Automated screening when profiles and window support are extractable | SIA 2024 use-category/profile acceptance; this screening is not an annual energy limit |
| Infiltration and ventilation rate | Keeps unit-safe facade/floor quantities separate and derives the applicable airflow band | Partial reference-project diagnostic | Reviewed unit provenance where VE metadata is incomplete |
| Ventilation control | Maps documented monozone/multizone and control identifiers to Table 4 | Automated reference-project diagnostic when system type, airflow and control are all extractable | External evidence for ambiguous controls; AHU leakage/pressure-drop data |
| Cooling efficiency | Applies exact EER and SEER Table 5-7 values by generator class and capacity band; reports target values separately | Automated reference-project diagnostic when class, capacity and metric are available | Table 7 `EER+`, auxiliary shares and part-load/system evidence cannot be replaced by SSEER |
| Heating efficiency | Applies exact SCOP Table 8-9 values by heat-pump class and capacity band | Automated reference-project diagnostic when source class, capacity and SCOP are available | SIA 384/3 or manufacturer evidence where the VE class/metric is unavailable |
| Schedules and internal gains | Resolves VE profile groups and computes representative daily-equivalent hours; reports occupancy, equipment and lighting gains; the authority-supplied SIA 2024:2021 category 3.1 standard values are checksum-bound and normalized | Partial | Exact native VE weekday/date/hour-boundary mapping for category 3.1; reviewed SIA 2024 mappings for all other use categories |
| Lighting | Extracts lighting power and daylight-dimming identifiers; accepts only reviewed external control mappings | Readiness only for delegated SIA 387/4 requirements | Controlled SIA 387/4 mapping and official test-3 comparison |
| Annual dynamic comfort | Evaluates each room from APS temperature, occupancy and SIA 180 upper/lower curves; requires complete annual series and known window operability; applies 0 h upper exceedance for operable-window rooms, otherwise 100 h for new and 400 h for existing buildings, plus 0 h below the lower curve | Automated only when every room is complete, building status is reviewed and approved/active weather filenames match exactly | Fill `SIA3802_project_metadata_<project>.csv`; verify operability, APS curve names and SIA 2028 weather provenance |
| Heating/cooling energy | Integrates non-empty APS W series to kWh and kWh/m2; missing series remain `None` | Partial | System/final-energy breakdown and official test-7 reference comparison |
| Reference-project generation | Produces source-traced substitutions for opaque-envelope constructions and window U-value/frame fraction | Partial input specification only; deliberately never reports `READY_FOR_REFERENCE_RUN` | Implement the remaining SIA 380/2 Table 2 families and the SIA 380 annual aggregation/weighting before an automated reference run |
| Whole-project/reference result | Imports one reviewed SIA 380 global energy expenditure index for the complete SIA 380/2 project/reference calculation and checks that project value does not exceed reference value | Required compliance gate; never inferred from component diagnostics or heating/cooling energy alone | Fill `SIA3802_global_reference_comparison_<project>.csv` with the canonical metric, scope, values, unit, reviewer, date and source; SIA 380 aggregation/weighting remains an external normative dependency |
| Design power | Encodes the 14-day preconditioning and 4-day heating/3-day cooling selection methods | Not checkable from annual peaks | Dedicated design-day result files and result-variable mapping |

### Exact Boundary Rules

- Capacity `12 kW` belongs to the `12-50` band. Other boundaries are selected
  deterministically from the encoded tables.
- Table 7 water-cooled post-cooling `EER+` is not inferred from `SEER`, `SSEER`
  or a nominal EER.
- Empty APS series return `None`, never zero consumption.
- Fixed `26 C` and `27 C` occupied-hour indicators are diagnostics only and do
  not replace the SIA 180 upper/lower curves.
- Missing climate, use-category, lighting-control or reviewed global comparison data
  results in an explicit incomplete/not-checkable status, never an assumed pass.

## SIA 4010 Tests and Classes

The readiness resolver contains 24 explicit test variants and the exact class
matrix represented in the provided SIA 4010 reference material.

| Class | Required variants | Automated product status |
| --- | --- | --- |
| 1A | `1`, `2A` | Variant readiness only |
| 1B | `1`, `2B-2D` | Variant readiness only |
| 2A | `1`, `2A`, `3A-3F` | Variant readiness only |
| 2B | `1`, `2B-2D`, `3A-3L` | Variant readiness only |
| 3 | `1`, `4`, `5A-5D`, `6` | Variant readiness only |
| 4A | `1`, `2A`, `3A-3F`, `4`, `5A-5D`, `6`, `7` | Variant readiness only |
| 4B | `1`, `2B-2D`, `3A-3L`, `4`, `5A-5D`, `6`, `7` | Variant readiness only |
| 5 | `7` | Variant readiness only |

The resolver evaluates both model requirements and official-evidence presence.
Its allowed final statuses are deliberately restricted to:

- `NOT_CHECKABLE`;
- `EVIDENCE_INCOMPLETE`;
- `READY_FOR_OFFICIAL_REVIEW`;
- `OFFICIAL_RESULTS_RECORDED`.

`OFFICIAL_RESULTS_RECORDED` means that every required exact result row and its
referenced files were found. It still returns a zero official score and never
grants `PASS`, `VALIDATED` or a certification statement without separate SIA
sub-commission attestation.

The separate official-result ingestion path preserves exact variant IDs. A
generic or reduced result cannot validate a broader class scope: `2A` is not
`2B`, `3A-3F` is not `3A-3L`, and all four `5A-5D` rows are required where the
class matrix lists them.

## Official Workbook Integration Boundary

Seven adapter functions exist in `swiss_sia.sia4010_test_adapters`. They raise
`NotImplementedError` with a test-specific expected filename until the matching
official workbook is supplied. This is intentional: worksheet names, cells,
units and formulas must not be guessed.

Expected patterns are:

```text
sia4010_evidence/SIA4010_official_evaluation_workbook_test_1_*.xlsx
...
sia4010_evidence/SIA4010_official_evaluation_workbook_test_7_*.xlsx
```

Macro-enabled `.xlsm` workbooks are also accepted by the integration contract.

## External Data That Cannot Be Invented

The two available standards refer to delegated standards and official test
packages. The code therefore provides controlled evidence scaffolds instead of
inventing values:

- `SIA2024_usage_mapping_<project>.csv` for room/use/profile acceptance;
- `SIA3874_lighting_control_mapping_<project>.csv` for lighting-control mapping;
- `SIA3802_project_metadata_<project>.csv` for reviewed building status,
  climate basis, weather file, location and altitude;
- `SIA3802_global_reference_comparison_<project>.csv` for the reviewed complete
  project/reference result;
- official SIA 4010 test specifications and evaluation workbooks;
- candidate and reference result files;
- reviewer/class confirmation;
- design-day APS/Vista results and reviewed climate provenance.

## Verification Baseline

The deterministic suite covers exact Table 1 and Tables 2-11 constants and
boundaries used by the new logic, SIA 180 curve counting, empty APS handling,
all 24 SIA 4010 variants, all eight validation classes and the seven workbook
adapter guardrails. The release validator additionally audits documentation,
evidence naming, anti-overclaim behaviour, fixtures and report structure.

The final release gate must still include a real IESVE Run-button execution on
each supported VE version because `iesve` is only available inside VE.
