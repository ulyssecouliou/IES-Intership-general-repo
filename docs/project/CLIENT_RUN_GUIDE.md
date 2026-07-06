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
- `SIA4010_candidate_results_*`
- `SIA4010_reference_comparison_*`
- `SIA4010_validation_class_confirmation_*`

Example filenames for a class 4B evidence package:
- `SIA4010_official_test_specs_class_4B.pdf`
- `SIA4010_official_evaluation_workbook_class_4B.xlsx`
- `SIA4010_candidate_results_class_4B_test_1_to_7.xlsx`
- `SIA4010_reference_comparison_class_4B.pdf`
- `SIA4010_validation_class_confirmation_class_4B.pdf`

Optional but recommended evidence manifest:
- copy `templates/evidence/sia4010_evidence_index_template.csv` into `sia4010_evidence/`;
- rename it as `SIA4010_evidence_index_<project>.csv`;
- fill `provided_file_name`, `source_authority`, `version_or_date`, `tests_covered`, `reviewer` and `review_status`.

Optional but recommended class-selection manifest:
- copy `templates/evidence/sia4010_class_validation_template.csv` into `sia4010_evidence/`;
- rename it as `SIA4010_class_validation_<project>.csv`;
- set exactly one row to `selected = yes` for the target class `1A`, `1B`, `2A`, `2B`, `3`, `4A`, `4B` or `5`.

Optional official test-result manifest:
- copy `templates/evidence/sia4010_official_test_results_template.csv` into `sia4010_evidence/`;
- rename it as `SIA4010_official_test_results_<project>.csv`;
- fill `status`, `reference_file`, `candidate_file`, `deviation`, `tolerance`, `reviewer`, `review_date`, `source_authority` and `source_reference` for every reviewed test.

Only explicit PASS/VALIDATED rows with the required metadata can upgrade an
individual SIA 4010 test to `VALIDATED`. The selected validation class remains
blocked until the five official evidence families and the class manifest are
also documented. The `reference_file` and `candidate_file` entries must match
files present in `sia4010_evidence/`; text-only file names are not enough.

File detection is a readiness indicator only. The file content, official source
and comparison validity must still be reviewed by the responsible compliance
reviewer.

For glazing and solar-protection evidence, use:

```text
docs/project/GLAZING_EVIDENCE_GUIDE.md
```

It maps the required evidence to the documented IESVE API objects and explains
what can be extracted automatically from VE/CDB versus what still requires a
reviewed external source.

## How To Run In VE

1. Open the IESVE Scripts window.
2. If the reviewer CSV files are not prepared yet, select:

```text
Prepare_SIA4010_Evidence_Folder.py
```

3. Click `Run`.
4. Fill or review the generated files in `sia4010_evidence/` when evidence is available.
5. Select:

```text
Run_VE_Swiss_Compliance.py
```

6. Click `Run`.
7. Wait until the log says the Excel report and evidence-pack ZIP have been generated.

## Report Output

Reports are written to:

```text
reports/
```

Each successful run creates:

- a timestamped Excel workbook;
- the latest workbook alias, when Excel is not locking it;
- a timestamped evidence-pack ZIP for manager/reviewer handoff.

Evidence-pack ZIP naming:

```text
Swiss_Compliance_Evidence_Pack__<project>__<model>__<timestamp>.zip
```

The ZIP contains the timestamped report, files currently present in
`sia4010_evidence/`, evidence templates, key project guidance documents and a
JSON manifest. It intentionally does not include licensed SIA standard PDFs from
`references/standards`. Files in `sia4010_evidence/` are filtered by safe
evidence naming rules; excluded files are listed in
`manifest/evidence_pack_manifest.json`.

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
- `FACADE GLAZING REVIEW`: construction-level glazing, solar-factor and shading evidence action sheet.
- `VE G-VALUES AUDIT`: CDB g-value, EN 410, building-regulation and BFRC traceability for glazing.
- `ASSUMPTIONS LIMITS`: certification guardrails, assumptions and known limits.
- `AUDIT LOG`: run metadata, APS/Vista status, evidence status and certification guardrails.
- `SUMMARY`: score summary.
- `ACTION PLAN`: grouped remediation actions.
- `COMPLIANCE RESULTS`: category-level result tables.
- `SIA REQUIREMENTS`: auditable list of SIA criteria, sources and automation status.
- `SIA DATA COVERAGE`: data, APS/Vista and evidence coverage by requirement.
- `INPUT REQUEST`: owner-ready missing input/evidence checklist.
- `SIA3802 JUSTIFICATIONS`: reviewer-signed retained SIA 380/2 deviations, if supplied.
- `SIA4010 READINESS`: official validation evidence matrix.
- `SIA4010 PREVALIDATION`: PDF-based prevalidation of tests 1 to 7 and classes 1A to 5 from VE/APS data.
- `SIA4010 CLASS MATRIX`: class-by-class SIA 4010 matrix for classes 1A to 5.
- `SIA4010 SOFTWARE REGISTER`: manager-provided software-register guardrail and validation-class detail.
- `NAVIGATOR BACKLOG`: manager-provided SIA 380/2 navigator roadmap and current project gaps.
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
4. Use `FACADE GLAZING REVIEW` when openings, g-values or solar protection dominate the P1 actions.
5. Use `SIA4010 SOFTWARE REGISTER` before making any statement about software-level SIA 4010 validation.
6. Use `NAVIGATOR BACKLOG` to explain the path from the current MVP to the constrained SIA 380/2 navigator.
7. Use `ASSUMPTIONS LIMITS` to show why the report is professional and conservative.
8. Use `AUDIT LOG`, `SIA DATA COVERAGE`, `SIA REQUIREMENTS`, `SIA3802 JUSTIFICATIONS`, `SIA4010 READINESS`, `SIA4010 PREVALIDATION` and `SIA4010 CLASS MATRIX` when technical traceability is needed.
