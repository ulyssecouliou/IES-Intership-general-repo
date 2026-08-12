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
individual SIA 4010 test to `OFFICIAL_RESULTS_RECORDED`. This status is an
auditable ingestion state, not a validation decision. The selected validation
class remains blocked until the five official evidence families and the class
manifest are also documented, and no `VALIDATED` claim is produced without a
separate SIA sub-commission attestation. The `reference_file` and
`candidate_file` entries must match files present in `sia4010_evidence/`;
text-only file names are not enough.

For the whole-project SIA 380/2 method comparison, fill the generated file:

```text
SIA3802_global_reference_comparison_<project>.csv
```

The accepted row must cover `complete_sia3802_project`, use
`comparison_metric = global_energy_expenditure_index_sia380`, identify the
project and reference values and unit, show a favourable project/reference
result, and include reviewer, review date and source traceability. This is the
SIA 380 energy expenditure index required by SIA 380/2 clauses 6.1.4 and 7.2.5;
heating or cooling energy alone is not an accepted substitute. Component checks
against Tables 2 to 9 remain diagnostics and cannot replace this comparison.

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
2. Select:

```text
Run_VE_Swiss_Compliance.py
```

3. Click `Run`.
4. The launcher creates any missing project-scoped evidence templates without
   overwriting completed reviewer files.
5. Wait until the log says the Excel report and evidence-pack ZIP have been generated.
6. Fill or review the generated files in `sia4010_evidence/` when external
   evidence is available, then rerun the same launcher.

## Report Output

Reports are written to:

```text
reports/
```

Each successful run creates:

- a timestamped Excel workbook;
- a timestamped one-page compliance report PDF on the engineering office's
  letterhead, beside the workbook and with the same base name;
- a timestamped evidence-pack ZIP for manager/reviewer handoff.

### Compliance report PDF

The PDF is the client-facing deliverable. It carries the office letterhead and
logo, the assessed verdict per SIA 380/2 domain, a schematic of the analysed
model (external opaque and glazed area per orientation), the key figures, the
scope statements and a signature block.

Configure the letterhead once by copying the template:

```text
config/company_profile.template.json  ->  config/company_profile.json
```

Fill in the office name, address, contacts, author and report reference, and set
`logo_path` to a PNG (greyscale or RGB, non-interlaced, no alpha) or a JPEG. Any
field left empty is printed as "not specified" - nothing is invented. If the
file is absent the PDF is still produced, with the letterhead visibly unset.

Choose the language with the `SIA_REPORT_LANGUAGE` environment variable
(`en`, `de`, `fr`, `it`; English by default).

The PDF is an engineering assessment report, not an official SIA certificate and
not an SIA 4010 validation attestation. A domain reads COMPLIANT only when it
was actually evaluated with no blocking finding; the overall SIA 380/2 statement
additionally requires the reviewed project/reference comparison, and SIA 4010
always requires SIA sub-commission attestation. Everything else is reported as
NOT DETERMINED, with the outstanding evidence named in the report.

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

The convenience alias `reports/Swiss_Compliance_Report.xlsx` is disabled by
default, so one Excel workbook is generated per run. The evidence-pack ZIP is a
separate handoff archive, not a second report.

## How To Read The Workbook

- `COVER`: branded landing page with the project, date, headline KPIs and the non-certification disclaimer.
- `INDEX`: clickable index linking to every sheet, grouped by section.
- `MANAGER DASHBOARD`: executive summary, KPI cards, charts and priority actions.
- `ACTION DASHBOARD`: consolidated action and priority view.
- `CLIENT SUMMARY`: safe wording for manager/client communication.
- `PREFLIGHT`: confirms whether the VE run and data extraction are trustworthy.
- `P1 REMEDIATION`: owner-ready action board for priority issues.
- `FACADE GLAZING REVIEW`: construction-level glazing, solar-factor and shading evidence action sheet.
- `FRAME FRACTION AUDIT`: construction-level frame-fraction values, failing counts and evidence needs.
- `ENVELOPE U REVIEW`: construction-level external wall/roof/floor U-value gaps.
- `VE G-VALUES AUDIT`: CDB g-value, EN 410, building-regulation and BFRC traceability for glazing.
- `ASSUMPTIONS LIMITS`: certification guardrails, assumptions and known limits.
- `AUDIT LOG`: run metadata, APS/Vista status, evidence status and certification guardrails.
- `SIA DATA COVERAGE`: data, APS/Vista and evidence coverage by requirement.
- `INPUT REQUEST`: owner-ready missing input/evidence checklist.
- `SIA3802 JUSTIFICATIONS`: reviewer-signed retained SIA 380/2 deviations, if supplied.
- `OPEN ITEMS BACKLOG`: dynamic backlog of model alerts, coverage gaps and navigator items.
- `SIA4010 READINESS`: official validation evidence matrix.
- `SIA4010 PREVALIDATION`: PDF-based prevalidation of tests 1 to 7 and classes 1A to 5 from VE/APS data.
- `SIA4010 CLASS MATRIX`: class-by-class SIA 4010 matrix, including the non-gating automated band cross-check column (`NOT_RUN` until an official test run is performed).
- `SIA4010 SOFTWARE REGISTER`: manager-provided software-register guardrail and validation-class detail.
- `NAVIGATOR BACKLOG`: manager-provided SIA 380/2 navigator roadmap and current project gaps.
- `DYNAMIC RESULTS`: APS/Vista dynamic indicators when readable from VE.
- `ALERT SUMMARY`: grouped technical findings.
- `ALERTS`: detailed alerts (repetitive low-severity rules are capped for readability, with a per-rule summary).
- `DATA QUALITY`: extraction coverage and missing-data risks.
- `DETAILED SCORES`: score components.
- `ROOMS`: extracted room data.

The legacy `SUMMARY`, `COMPLIANCE RESULTS`, `ACTION PLAN` and `SIA REQUIREMENTS`
sheets were consolidated into the sheets above and are no longer generated.

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
