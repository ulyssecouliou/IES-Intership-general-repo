# Evidence Templates

These templates define the minimum evidence fields needed to move from a
readiness report toward a defensible Swiss SIA review.

Use them as client/model-reviewer handoff files. Filled files can be stored in
`sia4010_evidence/` and referenced from the generated Excel report.

## SIA 4010 Naming Rule

The SIA 4010 evidence scanner is intentionally strict. A file is counted for an
official evidence family only when its filename starts with the documented
prefix and uses an accepted file extension. This avoids false positives from
generic files such as `validation.xlsx` or `report.pdf`.

Expected prefixes:

- `SIA4010_official_test_specs_`
- `SIA4010_official_evaluation_workbook_`
- `SIA4010_candidate_results_`
- `SIA4010_reference_comparison_`
- `SIA4010_validation_class_confirmation_`

Example for class 4B:

- `SIA4010_official_test_specs_class_4B.pdf`
- `SIA4010_official_evaluation_workbook_class_4B.xlsx`
- `SIA4010_candidate_results_class_4B_test_1_to_7.xlsx`
- `SIA4010_reference_comparison_class_4B.pdf`
- `SIA4010_validation_class_confirmation_class_4B.pdf`

## SIA 4010 Evidence Manifest

Use `sia4010_evidence_index_template.csv` as the reviewer handoff manifest.
Copy it into `sia4010_evidence/`, rename it for the project, and fill one row
per evidence family:

```text
SIA4010_evidence_index_<project>.csv
```

The manifest is parsed by the checker but is not counted as evidence by itself.
It makes a detected evidence file stronger by documenting:

- the exact `provided_file_name`;
- the official or responsible `source_authority`;
- the `version_or_date`;
- the covered SIA 4010 tests;
- the reviewer;
- the `review_status`.

Accepted documented `review_status` values are `provided`, `present`,
`reviewed`, `accepted`, `approved`, `complete` and
`ready_for_official_review`. Rows marked `missing` remain visible in the report
but do not count as documented evidence.

## SIA 4010 Class Manifest

Use `sia4010_class_validation_template.csv` to select the target validation
class explicitly. Copy it into `sia4010_evidence/`, rename it for the project,
and set exactly one row to `selected = yes`:

```text
SIA4010_class_validation_<project>.csv
```

The checker uses this CSV before filename-based class detection. It documents
the target class, required tests, reviewer, review status, source authority and
source reference. The class manifest does not count as an official evidence
family by itself; the separate validation-class confirmation file is still
required for the five-family SIA 4010 evidence pack.

## SIA 4010 Official Test Results

Use `sia4010_official_test_results_template.csv` when a reviewer can document
official results. Copy it into `sia4010_evidence/`, rename it for the project,
and fill one row per exact variant required by the selected class:

```text
SIA4010_official_test_results_<project>.csv
```

Accepted PASS values are `pass`, `passed`, `validated`, `official_pass` and
`official_validated`. Accepted FAIL values are `fail`, `failed`, `not_passed`
and `rejected`.

A PASS/VALIDATED row is accepted as `OFFICIAL_RESULTS_RECORDED` only when the row includes
`reference_file`, `candidate_file`, `reviewer`, `review_date`,
`deviation`, `tolerance`, `source_authority` and `source_reference`. The
`reference_file` and `candidate_file` values must match the configured
`SIA4010_reference_comparison_` and `SIA4010_candidate_results_` evidence
families. Missing metadata or wrong-family files remain visible but do not
record the result. A separate SIA sub-commission attestation is still required
before any validated or certified claim.

Variant identifiers are not collapsed. For example, `test_2A` cannot satisfy
`test_2B`, six rows `test_3A` to `test_3F` cannot satisfy the twelve-variant
scope `test_3A` to `test_3L`, and a generic `test_5` row cannot replace
`test_5A` to `test_5D`.

## Templates

- `sia2024_usage_mapping_template.csv`: reviewer-accepted VE room/template to
  SIA 2024 use-category mapping. The checker never invents missing SIA 2024
  categories or numeric values.
- `sia3874_lighting_control_mapping_template.csv`: reviewer-accepted VE
  lighting/daylight-control to SIA 387/4 control-type mapping used by SIA 4010
  test-3 readiness. It does not replace the official comparison workbook.
- `sia3802_project_metadata_template.csv`: reviewer-approved active-project
  metadata. It selects the new/existing building comfort allowance and proves
  the reviewed weather file, climate basis, location and altitude. The
  `project_id` must match the active VE project folder name.
- `sia3802_global_reference_comparison_template.csv`: reviewer-approved global
  project/reference result. Component deviations remain diagnostic until this
  project-level comparison is documented and accepted.
- `glazing_solar_protection_template.csv`: glazing, frame and shading evidence
  needed for SIA 380/2 opening and solar-protection checks.
- `g_values_audit_template.csv`: VE/CDB g-value traceability template for
  proving whether a raw `g_value` is the same value as EN 410 `g_perp`, and for
  documenting any `g_total_with_shading` calculation/evidence.
- `sia4010_evidence_index_template.csv`: official validation-evidence tracker
  for SIA 4010 tests, workbooks, candidate outputs, reference comparisons and
  validation class confirmation.
- `sia4010_class_validation_template.csv`: class-by-class tracker for SIA 4010
  classes 1A, 1B, 2A, 2B, 3, 4A, 4B and 5. Use it to document the intended
  class, required tests and official reviewer status.
- `sia4010_official_test_results_template.csv`: reviewer-filled result tracker
  for explicit SIA 4010 result outcomes on all 24 exact variants. Recorded
  result rows do not replace the SIA sub-commission attestation.
- `sia4010_software_register_review_template.csv`: manager-register review
  template. This is a guardrail file only; it must not be counted as official
  SIA 4010 validation evidence for the active IESVE workflow.
- `sia3802_justifications_template.csv`: reviewer-signed justification template
  for retained SIA 380/2 deviations. Accepted rows can move report items to
  `JUSTIFIED_BY_EVIDENCE` while keeping model values and limits visible.

## Glazing Retrieval Guide

Use `docs/project/GLAZING_EVIDENCE_GUIDE.md` before filling the glazing template.
It explains which fields are retrieved automatically from IESVE/CDB through the
documented VEScript API and which fields still need external reviewer evidence.

## Important Guardrail

Evidence templates do not create official SIA validation by themselves. The
responsible reviewer must confirm source, applicability, version and acceptance.
