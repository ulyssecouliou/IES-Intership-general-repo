# SIA 4010 Evidence Folder

Place official SIA 4010 validation evidence here before running the VE script.

Expected evidence families:
- Official SIA test specifications.
- Official SIA Excel evaluation workbooks.
- Candidate IESVE/APS/Vista results exported for the SIA tests.
- Reference comparisons, plots or official evaluation outputs.
- Validation class confirmation evidence.

The checker scans this folder and reports evidence presence, but it does not
claim official SIA 4010 validation until the official comparison files are
complete and reviewed by the responsible compliance authority.

## Evidence Manifest

For a professional review, also copy the manifest template into this folder and
rename it for the project:

```text
SIA4010_evidence_index_<project>.csv
```

Source template:

```text
templates/evidence/sia4010_evidence_index_template.csv
```

The manifest does not count as evidence by itself. It documents each evidence
file with:

- `provided_file_name`;
- `source_authority`;
- `version_or_date`;
- `tests_covered`;
- `reviewer`;
- `review_status`;
- `notes`.

Accepted documented `review_status` values are:

- `provided`;
- `present`;
- `reviewed`;
- `accepted`;
- `approved`;
- `complete`;
- `ready_for_official_review`.

Rows left as `missing` are shown in the report but do not make an evidence
family documented.

## Validation-Class Manifest

To select the target SIA 4010 validation class explicitly, also copy the class
template into this folder and rename it for the project:

```text
SIA4010_class_validation_<project>.csv
```

Source template:

```text
templates/evidence/sia4010_class_validation_template.csv
```

Set exactly one row to `selected = yes`. The checker supports all classes:

- `1A`;
- `1B`;
- `2A`;
- `2B`;
- `3`;
- `4A`;
- `4B`;
- `5`.

Accepted documented `review_status` values for the selected class are:

- `selected`;
- `requested`;
- `confirmed`;
- `reviewed`;
- `accepted`;
- `approved`;
- `ready_for_official_review`.

This class manifest does not count as official evidence by itself. It documents
which validation class is being requested and who reviewed that request.

## Official Test-Result Manifest

To document explicit PASS/FAIL outcomes for tests 1 to 7, copy the official
test-result template into this folder and rename it for the project:

```text
SIA4010_official_test_results_<project>.csv
```

Source template:

```text
templates/evidence/sia4010_official_test_results_template.csv
```

Accepted PASS values are:

- `pass`;
- `passed`;
- `validated`;
- `official_pass`;
- `official_validated`.

Accepted FAIL values are:

- `fail`;
- `failed`;
- `not_passed`;
- `rejected`.

A PASS/VALIDATED row only validates the test when `reference_file`,
`candidate_file`, `deviation`, `tolerance`, `reviewer`, `review_date`,
`source_authority` and `source_reference` are filled. The `reference_file` and
`candidate_file` values must match files present in this folder. Tests without a
complete official result row stay `READY_FOR_OFFICIAL_REVIEW`,
`EVIDENCE_INCOMPLETE` or `NOT_CHECKABLE`.

## Recommended Naming

Use explicit filenames so the evidence scan can classify files reliably:

- `SIA4010_official_test_specs_`
- `SIA4010_official_evaluation_workbook_`
- `SIA4010_candidate_results_`
- `SIA4010_reference_comparison_`
- `SIA4010_validation_class_confirmation_`

Examples for a class 4B review:

- `SIA4010_official_test_specs_class_4B.pdf`
- `SIA4010_official_evaluation_workbook_class_4B.xlsx`
- `SIA4010_candidate_results_class_4B_test_1_to_7.xlsx`
- `SIA4010_reference_comparison_class_4B.pdf`
- `SIA4010_validation_class_confirmation_class_4B.pdf`

Accepted file types depend on the evidence family:

- official test specifications: `.pdf`, `.docx`, `.xlsx`;
- official evaluation workbooks: `.xlsx`, `.xlsm`;
- candidate results: `.xlsx`, `.xlsm`, `.csv`, `.pdf`;
- reference comparisons: `.pdf`, `.xlsx`, `.xlsm`, `.csv`, `.png`;
- validation class confirmation: `.pdf`, `.docx`, `.txt`, `.csv`.

File type and filename classification are not sufficient for validation. The
content, official source, reference comparison and requested validation class
must still be reviewed manually.

## Minimum Evidence Pack

Before any official SIA 4010 validation claim, provide:

1. Official test specifications.
2. Official Excel evaluation workbooks.
3. Candidate software/model results inserted or linked to the official workbooks.
4. Generated comparison plots or reference result comparisons.
5. Requested/confirmed validation class.

If only this `README.md` is present, the report should remain `NOT_CHECKABLE`.
