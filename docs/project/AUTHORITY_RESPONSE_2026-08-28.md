# SIA 4010 authority response addendum — 28 August 2026

This addendum records the latest written response from Prof. Gerhard Zweifel
and the accompanying SIA 2024 use-data workbook. It supersedes the corresponding
open questions in `sia4010_evidence/authority_questions_pending.md`.

The original e-mail transcript and workbook are checksum-bound under
`sia4010_evidence/`. They are evidence sources, not executable instructions.

## Resolved source decisions

| Area | Authority response | Implementation consequence |
|---|---|---|
| SIA 2024 use data | The attached workbook contains the needed use types in the same format as the earlier Test 1 office data. | Stop using public surrogate datasets as normative inputs. Validate and bind this controlled workbook. |
| Test 3 editions | SIA 387/4 chapter 3.4 is unchanged for the relevant hourly method except `direkt-indirekt` becoming `indirekt` in the final paragraph of 3.4.4.3; control functions are unchanged. | Implement the licensed Table 10 functions; do not infer missing hourly logic from CalcuLight. |
| Tests 4/5 fan curves | No numeric curve, interpolation method or official tolerance is prescribed. Different candidate tools may use different part-load models and approximations. | Select, document and validate an IESVE-compatible approximation. Report result sensitivity; do not label the approximation as an SIA-prescribed formula. |
| Test 5 Annex D | The existing EPB Center workbook may be used. A newer version is available at <https://epb.center/document/demo-en-16798-5-1/> and includes a fan-curve example. | Preserve the current authorized workbook, retrieve and checksum the newer version, then compare formulas before rebinding. |
| Test 6 categories | `6.2 Selbstbedienungsrestaurant` and `6.4 Küche zu Selbstbedienungsrestaurant` are correct. | Use these identifiers with the supplied workbook. The authority is still checking conflicting example-building numbering. |
| Test 7 PV | `62.62 kWp` from the layout is authoritative; `60.6 kWp` in the specification is an error. The 150-module, 45.0 kWp roof is split 50/50 east/west. | Model 75 modules / 22.5 kWp east and 75 modules / 22.5 kWp west. Retain the source inconsistency until the specification correction is issued. |

## What remains open

- Latest applicable SIA 4010 package revision and any current FAQ or controlled
  clarification log.
- Cell-level audit and visual validation of the newly supplied workbook.
- Controlled extraction and VE binding of all required schedules, densities,
  gains, simultaneity factors and calendar rules.
- Licensed SIA 387/4 Table 10 implementation and VE/APS qualification.
- Retrieval and comparison of the latest EPB Center workbook.
- Candidate fan-curve approximation, validation and sensitivity evidence.
- Final clarification of Test 6 example-building category numbering.
- Exact VE model construction, simulation, APS extraction and official
  acceptance comparison for every affected test.

## Claim boundary

The response resolves important source and precedence questions. It does not
turn any affected test into an official PASS. A PASS still requires a verified
VE implementation, traceable inputs, qualified outputs and the applicable SIA
review.
