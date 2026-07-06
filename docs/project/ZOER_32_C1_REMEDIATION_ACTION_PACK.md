# ZOER 32 C1 Remediation Action Pack

## Purpose

This action pack translates the latest reviewed Swiss compliance report into
concrete model, evidence and reviewer actions for the `ZOER_32_C1` VE model.
It is intentionally conservative: it improves the project workflow without
claiming final SIA 380/2 or SIA 4010 compliance before the model and official
evidence are complete.

## Reviewed Baseline

| Item | Value |
| --- | --- |
| Reviewed workbook | `reports/Swiss_Compliance_Report__ZOER_32_C1__-__20260706_145738.xlsx` |
| Generated on | 2026-07-06 14:57:38 |
| Analysed rooms | 4 |
| Analysed floor area | 392.5 m2 |
| SIA 380/2 automated readiness score | 45.6/100 |
| Model health score | 65.8/100 |
| SIA 4010 evidence families | 0/5 |
| APS/Vista status | Available |
| Selected APS file | `ZOER_C1.aps` |

## Immediate P1 Remediation Items

| Scope | Current value | Retained readiness limit | Status | Required action |
| --- | ---: | ---: | --- | --- |
| `STD_EXTW` frame fraction | 0.30 | 0.25 | Fail | Reduce the VE/CDB frame fraction to `<= 0.25`, or provide reviewer-accepted facade/window evidence proving why the retained value is acceptable. |
| `STD_EXT2` frame fraction | 0.35 | 0.25 | Fail | Reduce the VE/CDB frame fraction to `<= 0.25`, or provide reviewer-accepted facade/window evidence proving why the retained value is acceptable. |
| `STD_EXT1; STD_PAR1; STD_WAL2` external wall group | 0.222316 W/(m2K) | 0.20 W/(m2K) | Fail | Update the construction build-up or assignment to reach `U <= 0.20 W/(m2K)`, or attach a full SIA 380/2 reference-calculation justification. |
| SIA 4010 official evidence | 0/5 families | 5/5 families | Not checkable | Provide official test specifications, official evaluation workbooks, candidate results, reference comparisons and validation-class confirmation. |

## What Is Already Working

- The glazing g-value workflow now uses the SIA-comparable EN 410 candidate from
  `VECdbConstruction.get_g_values().bs_en_410` when available.
- The raw CDB value `g = 0.75` is no longer treated as the comparable SIA
  `g_perp` when EN 410 evidence is available.
- `STD_EXTW`, `STD_EXT1` and `STD_EXT2` now have defensible g-value traceability
  in the report.
- APS/Vista optional result extraction is active for lighting, fans, pumps,
  auxiliary energy, coils, CO2 and relative humidity when variables are exposed.
- CO2 values returned as fractions by APS are normalized to ppm in the next
  generated report.

## VE Model Actions

Use these actions inside VE before rerunning the compliance script.

| Step | Action | Expected effect |
| --- | --- | --- |
| 1 | Open the construction data used by `STD_EXTW` and reduce the modeled frame fraction from `0.30` to `<= 0.25`, if this matches the real facade. | Removes one SIA 380/2 opening blocker. |
| 2 | Open the construction data used by `STD_EXT2` and reduce the modeled frame fraction from `0.35` to `<= 0.25`, if this matches the real facade. | Removes one SIA 380/2 opening blocker. |
| 3 | Review the external wall construction group `STD_EXT1; STD_PAR1; STD_WAL2` and update the build-up or assignment so the U-value is `<= 0.20 W/(m2K)`, if this matches the project design. | Removes the external-wall thermal-transmittance blocker. |
| 4 | If any failing value is intentionally retained, complete the draft SIA 380/2 justification CSV and attach the calculation/source evidence. | Keeps the deviation visible while allowing reviewer acceptance. |
| 5 | Check room schedules, use categories, ventilation airflow, ventilation controls, lighting power/control, AHU data, heating/cooling plant efficiency and final-energy evidence. | Improves SIA 380/2 delegated inputs and SIA 4010 tests 3 to 7 readiness. |
| 6 | Rerun Apache/Vista simulation after any construction, weather, schedule or system change. | Prevents stale APS results. |
| 7 | Run `Run_VE_Swiss_Compliance.py` from the VE script runner. | Generates the next Excel report and evidence pack. |
| 8 | Run `RUN_IESVE_EXTRACTION_PROBE.py` from the VE script runner. | Captures the latest API availability and APS variables for development checks. |

## Evidence Files Prepared

The following draft files are prepared in `sia4010_evidence/`.

| File | Purpose | Counts as accepted evidence now |
| --- | --- | --- |
| `SIA3802_justification_ZOER_32_C1_draft.csv` | Draft reviewer justification rows for the two frame-fraction blockers and the external-wall U-value blocker. | No |
| `SIA4010_evidence_index_ZOER_32_C1_draft.csv` | Draft checklist for the five required SIA 4010 evidence families. | No |
| `SIA4010_class_validation_ZOER_32_C1_draft.csv` | Draft class matrix for classes `1A` to `5`; no class is selected yet. | No |
| `SIA4010_official_test_results_ZOER_32_C1_draft.csv` | Draft result tracker for SIA 4010 tests 1 to 7. | No |

These files must be completed by a responsible reviewer before they can change
the generated report status.

## Minimum Reviewer Fields Needed

| Workflow | Fields that must be completed |
| --- | --- |
| SIA 380/2 justification | `decision_status`, `review_status`, `reviewer`, `review_date`, `source_document`, `source_reference`, `justification_summary` |
| SIA 4010 evidence index | `provided_file_name`, `source_authority`, `version_or_date`, `tests_covered`, `reviewer`, `review_status` |
| SIA 4010 class validation | exactly one `selected = yes`, plus `required_tests`, `reviewer`, `review_status`, `review_date`, `source_authority`, `source_reference` |
| SIA 4010 official test results | `status`, `reference_file`, `candidate_file`, `deviation`, `tolerance`, `reviewer`, `review_date`, `source_authority`, `source_reference` |

## Recommended Next Run Acceptance Target

The next regenerated report should show:

- no stale APS/weather warning;
- CO2 values in ppm instead of tiny fractions;
- frame-fraction blockers resolved or explicitly pending reviewer evidence;
- external-wall U-value blocker resolved or explicitly pending reviewer
  evidence;
- SIA 4010 still conservative unless the official evidence files are provided;
- charts visible in `MANAGER DASHBOARD`;
- no formula-error markers in the workbook.

## Safe Manager Wording

Use this wording until official evidence is complete:

> The tool provides a professional SIA 380/2 and SIA 4010 readiness audit for
> the VE model. It identifies model blockers, missing evidence and official
> validation prerequisites. It does not yet issue a final SIA compliance
> certificate because the model corrections and SIA 4010 official evidence pack
> are not complete.

