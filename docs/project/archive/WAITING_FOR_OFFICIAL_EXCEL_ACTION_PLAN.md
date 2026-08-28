# Waiting for Official SIA 4010 Excel Files - Action Plan

## Purpose

This note defines what can be improved safely while the official SIA 4010 Excel
workbooks and detailed comparison files are not available yet.

The project must keep moving, but it must not claim final SIA 4010 validation
until the official evidence package and reviewer-accepted results are present.

## Safe Work Available Now

| Workstream | What can be done now | Professional value |
| --- | --- | --- |
| VE extraction | Improve extraction of room, surface, opening, construction, shading, HVAC and APS/Vista metadata | Reduces uncertainty before official test execution |
| SIA 380/2 checks | Strengthen automated checks for U-values, EN 410 g-values, light transmittance, frame fraction and infiltration | Improves model-readiness quality |
| SIA 4010 readiness | Maintain tests 1 to 7 and classes 1A to 5 as readiness/status matrices | Keeps the method-validation path visible without overclaiming |
| Evidence workflow | Prepare folder, templates, manifest rules and ZIP handoff pack | Makes official file intake fast once files arrive |
| Report quality | Improve manager-facing wording, visuals, backlog and action sheets | Makes the deliverable easier to review with clients |
| Internal QA | Run deterministic fixtures and claim-safety checks without official files | Prevents false PASS/VALIDATED outcomes |

## Work That Must Stay Blocked

The following items must remain blocked until official SIA evidence is available:

- final SIA 4010 `VALIDATED` wording for a software/method class;
- official validation of tests 1 to 7;
- official class confirmation from 1A to 5;
- official candidate-versus-reference comparison using the paid SIA workbooks;
- final certificate-like wording for a client model.

## Current Autonomous Improvements Completed

- Added deterministic internal fixtures for SIA 380/2 and SIA 4010 release checks.
- Added claim-safety checks proving that raw CDB `g_value` is not accepted as SIA
  `g_perp`, even when it is numerically below the SIA readiness limit.
- Hardened the report helper so `g_total` is not waived unless the base g-value
  is proven as SIA-comparable EN 410 evidence.
- Hardened evidence detection so legacy boolean flags do not count as official
  SIA 4010 evidence files.
- Confirmed that SIA 4010 readiness does not inflate the automated SIA 380/2
  compliance score.
- Added surface `tilt` and normalized adjacency metadata to the normalized VE
  surface model.

## Next Best Actions Without Excel

1. Expand APS/Vista variable inventory for tests 4 to 7.
2. Improve HVAC/AHU extraction for airflow, fans, pumps, heat recovery,
   humidification and system controls.
3. Add daylight and lighting-control evidence fields for SIA 4010 test 3.
4. Add richer probe output for real VE projects, especially dynamic variables
   and Apache Systems fields.
5. Run the VE button script on the next available client model and compare the
   workbook against the release-validation expectations.

## Evidence Intake When Files Arrive

Place official and reviewer-filled files in `sia4010_evidence/` using the
documented filename prefixes:

- `SIA4010_official_test_specs_<project>.*`
- `SIA4010_official_evaluation_workbook_<project>.*`
- `SIA4010_candidate_results_<project>.*`
- `SIA4010_reference_comparison_<project>.*`
- `SIA4010_validation_class_confirmation_<project>.*`
- `SIA4010_evidence_index_<project>.csv`
- `SIA4010_class_validation_<project>.csv`
- `SIA4010_official_test_results_<project>.csv`

Only the official test-result CSV can move individual tests from
`READY_FOR_OFFICIAL_REVIEW` to `VALIDATED`, and only when the referenced files
exist and the full evidence pack is ready.

## Safe Manager Wording

Use:

- "The tool provides SIA 380/2 model-readiness checks and SIA 4010 validation
  readiness tracking."
- "SIA 4010 tests/classes are prepared, but official validation remains evidence
  dependent."
- "The current output is not an official SIA certificate."

Avoid:

- "The model is fully SIA 4010 certified."
- "IESVE is validated for all SIA 4010 classes by this script alone."
- "A raw VE/CDB g-value is automatically equivalent to EN 410 g_perp."
