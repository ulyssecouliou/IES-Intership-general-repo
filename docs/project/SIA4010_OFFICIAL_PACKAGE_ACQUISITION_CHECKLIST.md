# SIA 4010 official test package - acquisition and placement checklist

Purpose: list exactly which official SIA 4010 artifacts must be obtained to run
and validate the seven-test procedure, and the exact file names / locations the
existing code expects. Nothing here is invented: expected results, tolerances,
example-building geometry and evaluation workbooks are official SIA artifacts
and must come from the source below. Until they are present, the software
reports SIA 4010 as prevalidation / `NOT_CHECKABLE` only, never as validated.

## 1. Authoritative source

Per SIA 4010:2023 FR, chiffre 4.3 and 4.4, the execution material is a separate
download, not part of the standard PDF:

- Source: `www.sia.ch/sia4010`
- Provided material (per the standard):
  - detailed description of each test (separate documents);
  - example building for tests 4-7: DXF plans/sections/views, IFC 3D models,
    and the load schedule for test 7;
  - one EXCEL evaluation workbook per test, into which results are transferred
    and which produces the comparison against the reference results.

Obtaining these files is a user action (download + licence acceptance). Do not
ask the assistant to download them.

## 2. The seven tests (from SIA 4010:2023, Annexe A / Tableau 64)

| Test | Domain | Basis |
|---|---|---|
| Test 1 | Building envelope, construction physics | BESTEST -> ASHRAE 140 / SN EN ISO 52016-1 |
| Test 2 | Envelope + solar protection | BESTEST-derived + SIA solar-protection handling |
| Test 3 | Lighting / daylight control | SIA 387/4 control variants |
| Test 4 | Building services - single room | Example building |
| Test 5 | Building services - multizone / AHU | Example building |
| Test 6 | Ventilation system | Example building |
| Test 7 | Total energy needs | Example building + test-7 load schedule |

Which tests are required depends on the target **validation class** (Tableau 63:
`1A, 1B, 2A, 2B, 3, 4A, 4B, 5`). Select the class first; it fixes the required
test subset. The class matrix is already represented in the software.

## 3. What to download per test

For each applicable test N (1-7), obtain from `www.sia.ch/sia4010`:

1. the detailed test description document;
2. the official EXCEL evaluation workbook (`.xlsx` or `.xlsm`);
3. the reference results for that test (usually embedded in the workbook);
4. for tests 4-7 additionally: the example-building numeric model files
   (DXF, IFC) and, for test 7, the load schedule.

## 4. Exact placement expected by the code

### 4.1 Per-test evaluation workbooks

The result-transfer adapters in `swiss_sia/sia4010_test_adapters.py` currently
fail closed and require, for each test N:

```
sia4010_evidence/SIA4010_official_evaluation_workbook_test_<N>_*.xlsx
  or
sia4010_evidence/SIA4010_official_evaluation_workbook_test_<N>_*.xlsm
```

(`<N>` = 1..7). Until the real workbook layout is available, the adapters raise
`NotImplementedError` rather than guessing worksheet names, cells, units or
formulas.

### 4.2 Checksum-verified bundle for expected results

The loader `swiss_sia/reference_model/sia4010/test_loader.py` consumes a bundle
folder containing `official_manifest.json`:

- required manifest fields: `schema_version` (must be `"1.0"`), `issued_by`
  (must contain `SIA`), `source_url`, `files` (non-empty list);
- each `files[]` entry: `path` (relative, no `..`), `role`, `sha256`, `test_ids`;
- the loader recomputes and verifies every SHA-256; a mismatch is rejected.

Provide expected results as a CSV file declared with `role`
`expected_results_csv`, with exactly these columns:

```
test_id, case_id, metric, expected_value, unit,
absolute_tolerance, relative_tolerance, source_locator
```

The comparator (`compliance_comparator.py`) compares only when units match and
an official tolerance is present; otherwise it returns `NOT_CHECKABLE`. It never
invents a tolerance.

### 4.3 Existing per-project evidence files

The following are already generated per project under `sia4010_evidence/` and
are reviewer-owned; complete them but do not let file presence alone imply a
pass:

- `SIA4010_official_test_results_<project>.csv`
- `SIA4010_class_validation_<project>.csv`
- `SIA4010_evidence_index_<project>.csv`

## 5. Non-file prerequisites (cannot be satisfied by downloads alone)

- Selected target validation class (Tableau 63), agreed with the reviewer.
- Independent SIA sub-commission review / attestation per SIA 4010 clauses
  4.6.1-4.6.2. Recorded reference results transferred into the workbooks are
  `OFFICIAL_RESULTS_RECORDED`, not `VALIDATED`, until this attestation exists.
- An official FAIL always overrides a PASS; missing or contradictory evidence
  stays "not validated".

## 6. Software behaviour by state

| State | Software result |
|---|---|
| No official files | Prevalidation readiness only; SIA 4010 `NOT_CHECKABLE` |
| Workbooks present, no attestation | `OFFICIAL_RESULTS_RECORDED`, official score 0 |
| Workbooks + reviewer attestation + class met | Class-scoped validation reportable |
| Any official FAIL | Overrides PASS; class not validated |

## 7. Suggested next steps once files are available

1. Choose the target validation class; confirm the required test subset.
2. Place the evaluation workbooks and build the checksum bundle as in section 4.
3. Ask the maintainer to (a) wire the loader end to end and (b) implement the
   per-test Excel transfer adapters against the real workbook layouts.
4. Run the Test 1-7 model families through the workflow and transfer results.
5. Obtain the sub-commission attestation before any validation wording is used.
