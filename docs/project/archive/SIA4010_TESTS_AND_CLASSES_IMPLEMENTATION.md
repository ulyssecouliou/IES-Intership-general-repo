# SIA 4010 Tests and Validation Classes - Implementation Note

This note describes how the project supports the SIA 4010:2023 validation tests
and validation classes while keeping certification wording conservative.

## Scope

The implementation supports all seven SIA 4010 validation tests and all
validation classes listed in the manager-provided register and traced back to
SIA 4010:2023 table 63.

The tool is a readiness and audit workflow. It does not certify IESVE, the
active model or the generated report by itself. A validation claim requires
official SIA files, candidate results, reference comparisons and responsible
reviewer or sub-commission acceptance.

## PDF-Based Prevalidation

The project now includes a `SIA4010 PREVALIDATION` workbook sheet and a Python
module, `swiss_sia/sia4010_prevalidation.py`, that perform the closest possible
prevalidation from the published SIA 380/2:2022 and SIA 4010:2023 PDFs.

This mode is designed for MVP/MSP use when the paid SIA execution package is
not available. It uses:

- SIA 4010 table 62 for the seven validation tests.
- SIA 4010 table 63 for classes 1A to 5.
- SIA 4010 annex A table 64 for the test matrix and required result families.
- SIA 4010 tables 65-66 for test 2/3 and test 5 variants.
- SIA 380/2 tables and annex A for envelope, openings, infiltration, solar
  protection and related dynamic assumptions.
- Available VE model data and APS/Vista outputs.

The resulting statuses are intentionally named as prechecks:

- `PDF_PRECHECK_PASS`
- `PDF_PRECHECK_PARTIAL`
- `PDF_PRECHECK_FAIL`
- `MISSING_VE_DATA`
- `NEEDS_SIA_EXECUTION_PACKAGE`
- `OFFICIAL_VALIDATION_REQUIRED`

These statuses are not official SIA validation statuses.

## Tests Covered

| Test | Domain | Current implementation |
| --- | --- | --- |
| Test 1 | Basic envelope / EN ISO 52016-1 / ASHRAE 140 basis | Checks VE readiness for rooms, envelope, U-values and openings; requires official test model and reference outputs for validation. |
| Test 2 | Solar-protection control linked to SIA 387/4 and SIA 380/2 Annex A | Checks glazing, g-values, shading type/control and active `g_total` evidence where needed; requires official evaluation files. |
| Test 3 | Lighting control according to SIA 387/4 | Checks lighting-power availability; daylight/control mapping and official files remain required. |
| Test 4 | Single-room all-air air-conditioning system | Checks HVAC, airflow and dynamic demand/temperature readiness; CO2 and official amphitheatre evidence remain required. |
| Test 5 | Multizone AHU with heat/moisture recovery | Checks HVAC/ventilation readiness; detailed fan, recovery and humidifier identifiers remain required. |
| Test 6 | Three-stage ventilation with heat recovery and overflow | Checks ventilation readiness; staged airflow, recovery and overflow logic remain required. |
| Test 7 | Heating/cooling emission, distribution, storage and generation | Checks dynamic demand and system-energy readiness; final energy, auxiliaries and official loads/evaluation files remain required. |

The exact execution matrix contains 24 variants: `1`, `2A-2D`, `3A-3L`, `4`,
`5A-5D`, `6` and `7`. The PDF prevalidation sheet remains intentionally
aggregated into seven base tests; the exact variant resolver separately checks
the system identifiers and class-specific scope.

## Validation Classes Covered

| Class | Required tests | Implementation status |
| --- | --- | --- |
| 1A | Test 1 and Test 2A | Supported in `SIA4010 CLASS MATRIX`. |
| 1B | Test 1 and Tests 2B-2D | Supported in `SIA4010 CLASS MATRIX`. |
| 2A | Test 1, Test 2A and Tests 3A-3F | Supported in `SIA4010 CLASS MATRIX`. |
| 2B | Test 1, Tests 2B-2D and Tests 3A-3L | Supported in `SIA4010 CLASS MATRIX`. |
| 3 | Test 1 and Tests 4 to 6 | Supported in `SIA4010 CLASS MATRIX`. |
| 4A | Test 1, Test 2A, Tests 3A-3F and Tests 4 to 7 | Supported in `SIA4010 CLASS MATRIX`. |
| 4B | Test 1, Tests 2B-2D, Tests 3A-3L and Tests 4 to 7 | Supported in `SIA4010 CLASS MATRIX`. |
| 5 | Test 7 | Supported in `SIA4010 CLASS MATRIX`. |

## Status Logic

The workbook uses conservative status wording:

- `CLASS_NOT_SELECTED`: no official validation class confirmation was detected.
- `NOT_REQUESTED`: another class is selected; this class is shown for matrix
  completeness.
- `NOT_CHECKABLE`: official evidence is absent or insufficient.
- `EVIDENCE_INCOMPLETE`: at least one required evidence family is missing.
- `READY_FOR_OFFICIAL_REVIEW`: all required evidence families are detected, but
  official reviewer acceptance is still required.
- `OFFICIAL_RESULTS_RECORDED`: every exact result row and referenced result file
  required by the selected class is recorded, but the SIA sub-commission
  attestation is not independently demonstrated.

The checker never produces `VALIDATED`, certification or a non-zero official
SIA 4010 score from the manifest alone.

## Required Evidence Families

The scanner expects five official evidence families in `sia4010_evidence/`:

- Official SIA test specifications.
- Official SIA Excel evaluation workbooks.
- Candidate IESVE/model results transferred into the official workbooks.
- Reference-result graphs or comparison tables generated by the official files.
- Validation class requested and confirmed by SIA or the responsible authority.

## Evidence Manifest

The scanner also reads optional project manifests named:

```text
SIA4010_evidence_index_<project>.csv
```

The manifest is not counted as evidence by itself. It documents detected files
with source authority, version/date, tests covered, reviewer and review status.
This separates two levels of readiness:

- file detected with a strict SIA 4010 prefix and accepted extension;
- file documented by a manifest row with accepted `review_status`, source and
  test coverage.

All five evidence families must be detected and all five families must be
documented in the manifest before the workflow can reach
`READY_FOR_OFFICIAL_REVIEW`. Result rows can then move the selected scope to
`OFFICIAL_RESULTS_RECORDED`; only the responsible SIA authority can establish a
validated claim.

## Class Selection Manifest

The checker can also read:

```text
SIA4010_class_validation_<project>.csv
```

This file is based on `templates/evidence/sia4010_class_validation_template.csv`.
It should contain all classes from `1A` to `5`, with exactly one row marked
`selected = yes`. When present, this CSV is used before filename-based class
detection.

The selected class is considered documented only when the selected row has an
accepted `review_status`, `reviewer`, `source_authority` and
`source_reference`. This still does not create an official validation claim; it
only makes the requested class explicit and auditable in the report.

## Official Test-Result Manifest

The checker can also read:

```text
SIA4010_official_test_results_<project>.csv
```

This file is based on
`templates/evidence/sia4010_official_test_results_template.csv`. It records
explicit reviewer outcomes for the exact variants required by the selected
class. Accepted PASS values are `pass`,
`passed`, `validated`, `official_pass` and `official_validated`. Accepted FAIL
values are `fail`, `failed`, `not_passed` and `rejected`.

A test is upgraded to `OFFICIAL_RESULTS_RECORDED` only when every exact variant
required by the selected class has a PASS/VALIDATED row and includes
`reference_file`, `candidate_file`, `reviewer`, `review_date`,
`deviation`, `tolerance`, `source_authority` and `source_reference`. The
referenced candidate and reference files must also exist in `sia4010_evidence/`.
Malformed IDs such as `test_10` are rejected instead of being normalized to
`test_1`.

This ingestion status does not assert that the row, workbook formula or method
has been accepted by the SIA sub-commission. Its official score remains zero.

Reduced and full scopes are intentionally distinct. `test_2A` never satisfies
`test_2B`; `test_3A` to `test_3F` never satisfy a class requiring `test_3A` to
`test_3L`; and `test_5A` to `test_5D` must each be documented where required.

The class matrix remains conservative:

- the selected class must be documented by
  `SIA4010_class_validation_<project>.csv`;
- all five official evidence families must be present and documented by
  `SIA4010_evidence_index_<project>.csv`;
- every exact variant required by the selected class must have an explicit
  PASS/VALIDATED official result row.

## Files Added for This Workflow

- `swiss_sia/sia4010_checker.py`: returns `classes` results covering all
  validation classes.
- `swiss_sia/sia4010_checker.py`: imports official test-result rows and uses
  them to distinguish `READY_FOR_OFFICIAL_REVIEW` from
  `OFFICIAL_RESULTS_RECORDED`.
- `swiss_sia/sia4010_prevalidation.py`: returns PDF-based prevalidation results
  for tests 1 to 7 and classes 1A to 5.
- `swiss_sia/excel_report.py`: writes `SIA4010 CLASS MATRIX`.
- `swiss_sia/excel_report.py`: writes `SIA4010 PREVALIDATION`.
- `templates/evidence/sia4010_class_validation_template.csv`: class tracker for
  reviewer handoff.
- `templates/evidence/sia4010_official_test_results_template.csv`: result
  tracker for official PASS/VALIDATED/FAIL rows on all 24 exact variants.
- `scripts/quality/validate_release.py`: checks that the class matrix and
  templates remain present.

## Remaining Work for Full Official Validation

- Obtain the official SIA 4010 test packages and evaluation workbooks.
- Populate the official workbooks with candidate IESVE outputs.
- Fill `SIA4010_official_test_results_<project>.csv` from the reviewed official
  comparison package.
- Extract additional VE outputs for CO2, lighting energy, fan/pump auxiliaries,
  final energy by carrier and detailed AHU/generation identifiers.
- Attach reviewer/sub-commission acceptance for the requested class.
