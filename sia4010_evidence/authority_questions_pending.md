# SIA 4010 — consolidated pending authority questions

Status date: 2026-08-28

This register contains only unresolved authority questions or technical work
that must remain fail-closed. Candidate engineering assumptions must never be
presented as SIA requirements.

## Resolved written authority decisions

- Test 1E / Test 2A solar-protection semantics:
  `authority_decisions/2026-08-26_test1e_solar_control_decision.json`.
- SIA 2024 category 3.1 calendar and hourly convention:
  `authority_decisions/2026-08-26_sia2024_3_1_calendar_decision.json`.
- Remaining use data, Test 3 edition interpretation, Tests 4/5 fan policy,
  Test 5 EPB authority, Test 6 categories and Test 7 PV precedence/split:
  `authority_decisions/2026-08-28_remaining_sia4010_clarifications_decision.json`.
- The authority-supplied SIA 2024 workbook is preserved and checksum-bound at
  `source_audits/sia2024_required_use_types_20260828/`. Source custody is
  verified; cell-level validation and VE binding are not complete.

## Campaign-wide documents still required

1. Confirm the latest applicable SIA 4010 test-package revision.
2. Provide the current FAQ or controlled clarification log, if one exists.
3. Provide the corrected Test 7 specification when issued.
4. Confirm the Test 6 example-building category numbering after the authority's
   announced check.

## Test 1E / Test 2A — IESVE optical representation

1. Identify the accepted IESVE representation of the fabric-awning solar and
   visible reflectances. VE reads these values but the documented Python setter
   rejects them.
2. Confirm whether equivalence through qualified hourly transmitted-energy and
   APS results is acceptable when those reflectance setters are unavailable.
3. Confirm the applicable long-wave emittance or exact licensed ISO source.
4. Identify an accepted output/audit method for exterior-plane incident
   irradiance and shade activation during the annual run.
5. Confirm whether ApacheSim dynamic surface coefficients are acceptable for
   the ISO cell, or identify supported fixed-coefficient settings and expected
   read-back evidence.

The current diagnostics are not a PASS. The official 1E comparison remains
failed and parameter tuning must not replace a controlled optical mapping.

## Test 3 — remaining implementation work

The authority confirmed that relevant chapter 3.4 control functions did not
change between editions and that Table 10 is the only supplied definition.

1. Obtain the licensed SIA 387/4 Table 10 content and implement types 1–6.
2. Qualify the exact hourly sensor, control and lighting-power reporting path in
   VE/APS. CalcuLight is not an authorized substitute for the hourly method.

## Test 4 — remaining implementation work

The auditorium data source was supplied. No official numeric fan curve,
interpolation method or tolerance is prescribed because candidate tools may use
different part-load models.

1. Validate and bind the supplied auditorium workbook data.
2. Select, document and validate an IESVE-compatible fan approximation.
3. Quantify result sensitivity and qualify the exact VE model and outputs.

## Test 5 — remaining implementation work

The required room-use data were supplied. The existing EPB Center Annex D
workbook is authorized. The authority identified a newer version at
<https://epb.center/document/demo-en-16798-5-1/>.

1. Validate and bind the supplied room-use data.
2. Retrieve, checksum and compare the newer EPB workbook before rebinding.
3. Document and validate the candidate-specific fan approximation.
4. Close room-system read-back, exact model, simulation and APS comparison.

## Test 6 — remaining implementation work

Categories `6.2 Selbstbedienungsrestaurant` and
`6.4 Kueche zu Selbstbedienungsrestaurant` are confirmed and their source data
were supplied.

1. Validate and bind the relevant workbook cells.
2. Await the authority's check of conflicting example-building numbering.
3. Close stage-control, room-system read-back, exact model and APS qualification.

## Test 7 — remaining implementation work

The authoritative installed total is `62.62 kWp`; `60.6 kWp` in the
specification is an acknowledged error. The 150-module / 45.0 kWp roof is split
equally: 75 modules / 22.5 kWp east and the same west.

1. Preserve the discrepancy until the corrected specification is issued.
2. Bind the exact orientation/module inputs and heat-pump performance data.
3. Close room/plant read-back, exact model, simulation and APS comparison.

## Claim boundary

The written responses resolve source meaning and precedence only. The software
may report readiness, provisional comparisons and observed results, but it must
not report an official SIA PASS until the source data, VE implementation,
simulation outputs and applicable authority review are complete.
