# Open Items Backlog - Swiss SIA Compliance Checker

This file is the persistent project memory for items that are not fully solved yet. The generated Excel workbook also includes an `OPEN ITEMS BACKLOG` sheet, built dynamically from the current model alerts, data-coverage gaps and manager navigator backlog.

## Recently Closed

- `g_total / g_perp EN 410` false blocker: resolved. The checker now uses `VECdbConstruction.get_g_values().bs_en_410` as the SIA `g_perp` candidate when available, and no longer requires `g_total` when the retained EN 410 value already satisfies `g <= 0.50`.
- Mixed French/English report labels in key sheets: mostly resolved for manager-facing sheets.
- Post-VE verification of new report tabs: verified on `Swiss_Compliance_Report__ZOER_32_C1__-__20260701_231313.xlsx`. The report now includes `FRAME FRACTION AUDIT`, `ENVELOPE U REVIEW` and `OPEN ITEMS BACKLOG`.
- Remaining visible French text in `DATA QUALITY`: fixed in the workbook generator after reviewing `Swiss_Compliance_Report__ZOER_32_C1__-__20260701_231313.xlsx`; verify on the next VE Run.
- SIA 4010 validation-class framework: implemented a class matrix covering `1A`, `1B`, `2A`, `2B`, `3`, `4A`, `4B` and `5`, with required tests, class status, missing official evidence and safe validation wording.
- SIA 4010 PDF-based prevalidation: implemented a dedicated prevalidation engine and workbook sheet for tests `1` to `7` and classes `1A` to `5`, using only SIA 380/2 + SIA 4010 published requirements and available VE/APS data.
- SIA 380/2 justification workflow: implemented reviewer-signed CSV scanning and a dedicated `SIA3802 JUSTIFICATIONS` workbook sheet so retained deviations can be shown as `JUSTIFIED_BY_EVIDENCE` without hiding the original model value.
- Internal fixture QA while waiting for official Excel files: implemented deterministic reference/problem scenarios, SIA 4010 PASS/FAIL state-machine checks and anti-overclaim validation in the release validator.
- Raw CDB glazing false-positive guard: report helpers no longer waive `g_total` evidence unless the base g-value is proven as EN 410/SIA-comparable.
- Python source documentation language policy: project-owned Python docstrings/comments are checked as English-only during release validation.
- APS/Vista optional output expansion: the dynamic collector now attempts lighting, fan, pump, auxiliary, heating coil, cooling coil, CO2 and relative humidity outputs when `ResultsReader.get_variables()` exposes matching room variables.
- SIA 380/2 full compliance gap audit: `SIA3802_FULL_COMPLIANCE_GAP_AUDIT.md` now records encoded values, coverage status and missing evidence before any complete compliance claim.
- APS CO2 unit normalization: APS CO2 values returned as fractions are converted to ppm in the dynamic-results workflow, avoiding report values such as `0.0004 ppm` when the intended reading is about `400 ppm`.
- ZOER 32 C1 remediation handoff: `ZOER_32_C1_REMEDIATION_ACTION_PACK.md` and draft evidence CSV files now document the exact model blockers and reviewer fields required before stronger compliance wording.

## Current High-Value Open Items

- Frame fraction audit: construction-level `ff` values, failing counts and evidence needs are now exposed in the generated workbook; keep monitoring after each VE Run.
- Envelope U-value review: construction-level external wall/roof/floor U-value gaps are now exposed in the generated workbook; keep monitoring after each VE Run.
- Frame fraction remediation from latest report: `STD_EXTW` has `ff=0.30` across 99 windows and `STD_EXT2` has `ff=0.35` across 27 windows, both above the retained readiness value `ff <= 0.25`; either update VE/CDB frame/glass split or provide audited facade justification.
- Envelope U-value remediation from latest report: `STD_EXT1, STD_PAR1, STD_WAL2` external wall group has `U=0.222 W/(m2K)` against the retained limit `0.20 W/(m2K)`; either update construction assignment/build-up or provide a full SIA 380/2 reference-calculation justification.
- SIA 4010 official evidence: still incomplete until official SIA test specifications, evaluation workbooks, candidate results, reference comparisons and validation class confirmation are provided. The new `SIA4010 CLASS MATRIX` sheet will show which class can be reviewed once those files are present.
- Waiting-for-Excel action plan: keep using `WAITING_FOR_OFFICIAL_EXCEL_ACTION_PLAN.md` to decide what can progress safely before the official SIA workbooks arrive.
- Post-VE verification of new report tabs: rerun the VE script and verify that `SIA3802 JUSTIFICATIONS` and `SIA4010 CLASS MATRIX` are present and readable in the generated workbook.
- Post-VE verification of new prevalidation tab: rerun the VE script and verify that `SIA4010 PREVALIDATION` lists all seven tests and all eight validation classes.
- SIA 2024 use-category mapping: still needed for room use, schedules, gains, ventilation and lighting assumptions.
- Ventilation/AHU extraction: still needs airflow bands, controls, fan data, pressure drops, airtightness, heat/moisture recovery and humidification fields.
- APS/Vista variable expansion: room-level optional outputs are implemented; next VE Run must confirm which variables the client APS file actually exposes, and system/component-level results still need deeper mapping.
- Lighting/SIA 387/4 mapping: still needs power density, daylight/control strategy and official comparison outputs.
- HVAC efficiencies: still needs generator type, capacity bands, EER/SEER/SCOP and part-load evidence.
- Evidence-pack export: still needed for a manager/client package containing Excel, raw outputs, assumptions and official evidence index.
- Full English cleanup: project-owned Python comments/docstrings are now enforced; older non-code project notes can be cleaned progressively when they become delivery artifacts.
- ZOER 32 C1 next-run verification: after VE model edits, regenerate the report and verify that the CO2 dynamic-results columns are reported in ppm, that the frame-fraction and U-value blockers are resolved or justified, and that the SIA 4010 evidence files remain conservative until reviewed.

## Working Rule

When a new limitation is discovered, add it in one of three places:

- Dynamic Excel backlog: if it can be derived from the current VE model, alert groups, coverage matrix or navigator backlog.
- This Markdown file: if it is a project/product task that should remain visible even when the current model changes.
- Evidence templates: if the missing item must be provided by the model reviewer, client or compliance reviewer.
