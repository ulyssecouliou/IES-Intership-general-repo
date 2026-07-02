# Open Items Backlog - Swiss SIA Compliance Checker

This file is the persistent project memory for items that are not fully solved yet. The generated Excel workbook also includes an `OPEN ITEMS BACKLOG` sheet, built dynamically from the current model alerts, data-coverage gaps and manager navigator backlog.

## Recently Closed

- `g_total / g_perp EN 410` false blocker: resolved. The checker now uses `VECdbConstruction.get_g_values().bs_en_410` as the SIA `g_perp` candidate when available, and no longer requires `g_total` when the retained EN 410 value already satisfies `g <= 0.50`.
- Mixed French/English report labels in key sheets: mostly resolved for manager-facing sheets.
- Post-VE verification of new report tabs: verified on `Swiss_Compliance_Report__ZOER_32_C1__-__20260701_231313.xlsx`. The report now includes `FRAME FRACTION AUDIT`, `ENVELOPE U REVIEW` and `OPEN ITEMS BACKLOG`.
- Remaining visible French text in `DATA QUALITY`: fixed in the workbook generator after reviewing `Swiss_Compliance_Report__ZOER_32_C1__-__20260701_231313.xlsx`; verify on the next VE Run.

## Current High-Value Open Items

- Frame fraction audit: construction-level `ff` values, failing counts and evidence needs are now exposed in the generated workbook; keep monitoring after each VE Run.
- Envelope U-value review: construction-level external wall/roof/floor U-value gaps are now exposed in the generated workbook; keep monitoring after each VE Run.
- Frame fraction remediation from latest report: `STD_EXTW` has `ff=0.30` across 99 windows and `STD_EXT2` has `ff=0.35` across 27 windows, both above the retained readiness value `ff <= 0.25`; either update VE/CDB frame/glass split or provide audited facade justification.
- Envelope U-value remediation from latest report: `STD_EXT1, STD_PAR1, STD_WAL2` external wall group has `U=0.222 W/(m2K)` against the retained limit `0.20 W/(m2K)`; either update construction assignment/build-up or provide a full SIA 380/2 reference-calculation justification.
- SIA 4010 official evidence: still incomplete until official SIA test specifications, evaluation workbooks, candidate results, reference comparisons and validation class confirmation are provided.
- SIA 2024 use-category mapping: still needed for room use, schedules, gains, ventilation and lighting assumptions.
- Ventilation/AHU extraction: still needs airflow bands, controls, fan data, pressure drops, airtightness, heat/moisture recovery and humidification fields.
- Lighting/SIA 387/4 mapping: still needs power density, daylight/control strategy and official comparison outputs.
- HVAC efficiencies: still needs generator type, capacity bands, EER/SEER/SCOP and part-load evidence.
- Evidence-pack export: still needed for a manager/client package containing Excel, raw outputs, assumptions and official evidence index.
- Full English cleanup: manager-facing sheets are mostly English, but older project notes and low-level implementation comments should be cleaned progressively.

## Working Rule

When a new limitation is discovered, add it in one of three places:

- Dynamic Excel backlog: if it can be derived from the current VE model, alert groups, coverage matrix or navigator backlog.
- This Markdown file: if it is a project/product task that should remain visible even when the current model changes.
- Evidence templates: if the missing item must be provided by the model reviewer, client or compliance reviewer.
