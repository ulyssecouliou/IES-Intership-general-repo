# SIA 4010 classes 1A and 1B — VE execution runbook

## Current automated scope

The implementation now:

- verifies all 56 files in the official SIA package with SHA-256;
- reads the official Test 1 and Test 2 acceptance bands;
- evaluates Test 2A, 2B, 2C and 2D separately;
- requires both the annual and hourly-frequency criteria for Test 2;
- applies the specification's `solar heat gain OR transmitted radiation`
  alternative without treating a missing alternative as a failure;
- rejects partial Test 1 coverage;
- generates and validates the common 8 m x 6 m x 2.7 m cell geometry with the
  two exact 3 m x 2 m south windows;
- produces fail-closed HTML and JSON Navigator reports for classes 1A and 1B.

This is technical validation automation, not an SIA certification issuer.

## Exact class scopes

| Class | Exact variants | Simulation portfolio |
|---|---|---|
| 1A | `test_1`, `test_2A` | Test 1 cases 600, 640, 600FF, 900, 940, 900FF and 1E; plus Test 2A |
| 1B | `test_1`, `test_2B`, `test_2C`, `test_2D` | The same Test 1 portfolio; plus Test 2B, 2C and 2D |

A generic `test_2` result never satisfies an exact class variant.

## Controlled inputs still required

The case manifest deliberately blocks model creation until these sources are
available:

1. ISO EN 52016-1:2017 chapter 7 / ASHRAE 140 inputs:
   lightweight and heavyweight constructions, Test 1 glazing, infiltration and
   related boundary conventions.
2. Denver `DRYCOLD` electronic insert referenced by the official Test 1
   specification.
3. SIA 2024:2021 category 3.1 hourly and annual schedules for people,
   equipment and lighting.
4. SIA 387/4:2017 table 9 control functions 1, 2 and 3.
5. Zurich-Kloten SIA 2028 `DRY normal` weather dataset.

Do not replace these inputs with project defaults or approximate schedules.
Populate `config/sia4010_classes_1a_1b.json`, change a parameter from
`PLACEHOLDER_REQUIRED` to `CONFIRMED`, and cite its controlled source only after
the value has been checked.

## What to run now in IESVE

Use a copy of the existing VE project.

1. In the VE Scripts window, run `Run_VE_SIA4010_Navigator.py`.
2. Open:
   - `sia4010_evidence/navigator/sia4010_navigator_1a.html`
   - `sia4010_evidence/navigator/sia4010_navigator_1b.html`
3. If the active project already has an APS file, run
   `Run_VE_SIA4010_APS_Probe.py`.
4. Send the generated
   `<VE project>/sia4010_artifacts/diagnostics/sia4010_aps_probe_*.json`
   back for binding qualification.

The APS probe is read-only. It records candidate variable names, units,
timesteps, rooms and bounded numeric summaries. It does not alter the model or
the APS file.

## Workflow after the missing controlled inputs are supplied

1. Validate every parameter and source in the case manifest.
2. Generate the exact VE cell and create the source-traced constructions,
   glazing, schedules and dynamic shading controls.
3. Create one immutable model fingerprint per official case.
4. Run ApacheSim for the prescribed calendar and weather.
5. Extract complete hourly series with confirmed ResultsReader bindings.
6. Calculate Test 1 monthly, annual and hourly-integrated peak values.
7. Calculate Test 2 annual results and frequency distributions using the
   official workbook classes.
8. Transfer candidate series into working copies of the official SIA
   workbooks; preserve originals and checksums.
9. Run the official-band comparator and regenerate the Navigator.
10. Submit the complete evidence package for SIA/sub-commission review.

Only an independently traceable official attestation can move the final
Navigator gate beyond `READY_FOR_OFFICIAL_REVIEW`.
