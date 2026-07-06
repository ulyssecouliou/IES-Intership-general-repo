# SIA 4010 PDF-Based Prevalidation Strategy

## Purpose

The official SIA 4010 execution package may be expensive or unavailable during
early project development. This project therefore implements a professional
prevalidation layer based on the published SIA 380/2:2022 and SIA 4010:2023
PDFs, the active VE model and available APS/Vista dynamic results.

This approach is intended for MVP/MSP delivery:

- identify whether a model is close to the SIA 4010 validation scope;
- expose missing model data before any paid validation step;
- show which validation classes are realistically reachable;
- keep official validation wording protected.

## What It Can Do

The `SIA4010 PREVALIDATION` sheet evaluates:

- Test 1: basic envelope thermal behaviour.
- Test 2: solar-protection control.
- Test 3: lighting control.
- Test 4: single-room all-air air-conditioning system.
- Test 5: complex multizone AHU with heat/moisture recovery.
- Test 6: three-stage ventilation with heat recovery and overflow.
- Test 7: heating/cooling emission, distribution, storage and generation.

It also evaluates the validation classes:

- `1A`
- `1B`
- `2A`
- `2B`
- `3`
- `4A`
- `4B`
- `5`

## Source Basis

The prevalidation is based on:

- SIA 4010:2023 table 62, page PDF 46.
- SIA 4010:2023 table 63, page PDF 48.
- SIA 4010:2023 annex A table 64, pages PDF 50-51.
- SIA 4010:2023 tables 65-66, page PDF 52.
- SIA 380/2:2022 envelope, opening, infiltration, solar-protection and dynamic
  method references.
- The documented IESVE route `VECdbConstruction.get_g_values().bs_en_410` for
  automatically comparable glazing `g_perp` evidence. Raw CDB `g_value`,
  `building_regulations` and `bfrc` values remain audit evidence unless a
  reviewer/manufacturer source proves they are comparable.

## Status Wording

The prevalidation uses explicit non-official statuses:

- `PDF_PRECHECK_PASS`: the published-PDF precheck is satisfied from available
  VE/APS data.
- `PDF_PRECHECK_PARTIAL`: some relevant evidence exists but the precheck is not
  complete.
- `PDF_PRECHECK_FAIL`: available data contradicts a retained SIA 380/2 or SIA
  4010 PDF-based requirement.
- `MISSING_VE_DATA`: the model/API does not expose enough data to decide.
- `NEEDS_SIA_EXECUTION_PACKAGE`: the paid SIA execution package is required to
  move beyond prevalidation.
- `OFFICIAL_VALIDATION_REQUIRED`: SIA sub-commission review remains required
  before any official SIA 4010 validation claim.

## What It Cannot Do

The PDF-based prevalidation cannot replace:

- official SIA test descriptions that are distributed separately;
- official SIA evaluation files;
- official reference result comparisons;
- official class confirmation;
- SIA sub-commission acceptance.

For solar-protection tests, a raw VE/CDB `g_value` alone cannot replace EN 410
`g_perp` evidence. If `bs_en_410` is absent, tests 2/2A remain partial or missing
until the reviewer attaches equivalent proof.

## Manager-Safe Wording

Use:

> The model has been assessed through a SIA 380/2 and SIA 4010 PDF-based
> prevalidation. The report identifies which SIA 4010 tests and validation
> classes are close to the published validation scope, and which model data or
> official execution-package elements remain missing.

Avoid:

> The model is SIA 4010 validated.

Avoid:

> IESVE is officially validated for classes 1A to 5 by this report.

## Implementation Files

- `swiss_sia/sia4010_prevalidation.py`
- `swiss_sia/config.py`
- `swiss_sia/excel_report.py`
- `docs/project/SIA4010_TESTS_AND_CLASSES_IMPLEMENTATION.md`
