# Swiss SIA Compliance Checker - VE Run Guide

## Purpose

This workflow generates a professional readiness report for Swiss SIA 380/2:2022
and SIA 4010:2023 checks from the active IESVE model.

It is designed for the IESVE Run button. No PowerShell step is required.

## Before Running

1. Open the target client project in IESVE.
2. Confirm the correct model is active.
3. Close any open copy of `reports/Swiss_Compliance_Report.xlsx`.
4. If SIA 4010 evidence is available, place it in:

```text
sia4010_evidence/
```

Expected SIA 4010 evidence:
- Official SIA test specifications.
- Official SIA Excel evaluation workbooks.
- Candidate IESVE / APS / Vista outputs.
- Reference comparisons or official evaluation plots.
- Validation class confirmation.

Recommended evidence filename prefixes:
- `SIA4010_official_test_specs_*`
- `SIA4010_official_evaluation_workbook_*`
- `SIA4010_candidate_results_APS_Vista_*`
- `SIA4010_reference_comparison_plots_*`
- `SIA4010_validation_class_confirmation_*`

File detection is a readiness indicator only. The file content, official source
and comparison validity must still be reviewed by the responsible compliance
reviewer.

## How To Run In VE

1. Open the IESVE Scripts window.
2. Select:

```text
Run_VE_Swiss_Compliance.py
```

3. Click `Run`.
4. Wait until the log says the Excel report has been generated.

## Report Output

Reports are written to:

```text
reports/
```

Each run creates a timestamped workbook, for example:

```text
Swiss_Compliance_Report__Project__Model__YYYYMMDD_HHMMSS.xlsx
```

The script also tries to update:

```text
reports/Swiss_Compliance_Report.xlsx
```

If that alias cannot be updated, it is usually because Excel has the file open.
Use the timestamped report instead.

## How To Read The Workbook

- `MANAGER DASHBOARD`: executive summary, KPI cards, charts and priority actions.
- `CLIENT SUMMARY`: safe wording for manager/client communication.
- `PREFLIGHT`: confirms whether the VE run and data extraction are trustworthy.
- `P1 REMEDIATION`: owner-ready action board for priority issues.
- `ASSUMPTIONS LIMITS`: certification guardrails, assumptions and known limits.
- `AUDIT LOG`: run metadata, APS/Vista status, evidence status and certification guardrails.
- `SUMMARY`: score summary.
- `ACTION PLAN`: grouped remediation actions.
- `COMPLIANCE RESULTS`: category-level result tables.
- `SIA REQUIREMENTS`: auditable list of SIA criteria, sources and automation status.
- `SIA DATA COVERAGE`: data, APS/Vista and evidence coverage by requirement.
- `INPUT REQUEST`: owner-ready missing input/evidence checklist.
- `SIA4010 READINESS`: official validation evidence matrix.
- `DYNAMIC RESULTS`: APS/Vista dynamic indicators when readable from VE.
- `ALERT SUMMARY`: grouped technical findings.
- `ALERTS`: raw detailed alerts.
- `DATA QUALITY`: extraction coverage and missing-data risks.
- `DETAILED SCORES`: score components.
- `ROOMS`: extracted room data.

## Verdict Rules

- `PASS`: the automated check found no blocking issue for that implemented rule.
- `FAIL`: an implemented check found a non-conforming or problematic value.
- `MISSING`: required data was not extracted.
- `NOT_CHECKABLE`: the script cannot legally or technically decide without external evidence.
- `NOT_IMPLEMENTED`: criterion is known and traced, but not automated yet.
- `PARTIAL_CHECK`: a useful automated check exists, but it still needs reviewer confirmation.

## Important Limitation

This workbook is not, by itself, an official SIA certificate.

SIA 4010 validates methods/software through official test cases, evaluation files
and reference comparisons. The script must not claim SIA 4010 validation until
those official evidence files are complete and reviewed by the responsible
compliance authority.

## Manager Demo Order

1. Start with `MANAGER DASHBOARD`.
2. Use `CLIENT SUMMARY` for safe executive wording.
3. Use `P1 REMEDIATION` to explain what must be fixed first.
4. Use `ASSUMPTIONS LIMITS` to show why the report is professional and conservative.
5. Use `AUDIT LOG`, `SIA DATA COVERAGE`, `SIA REQUIREMENTS` and `SIA4010 READINESS` when technical traceability is needed.
