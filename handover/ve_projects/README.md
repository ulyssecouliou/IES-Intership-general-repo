# VE project snapshots

Status date: 27 August 2026

These archives are private IES handover snapshots of the VE projects used for
the final client-product and SIA 4010 investigations. They are versioned because
the incoming maintainer must not depend on the departing contributor's Windows
profile or `Documents\switzerland` folder.

## Contents

| Archive | Role |
|---|---|
| `SIA_compatible_model_TEST.zip` | Last client-model test project used for SIA 380/2 report development |
| `SIA4010_TEST1_1E_TEMPLATE.zip` | Test 1E exact-template working project |
| `SIA4010_TEST_1_1E_DISPOSABLE.zip` | Test 1E controlled disposable model and APS diagnostics |
| `SIA4010_TEST1_1E_EQUIVALENT_GLAZING_DISPOSABLE_V2.zip` | Test 1E equivalent-glazing diagnostic branch |
| `SIA4010_TEST2A_DISPOSABLE_V3.zip` | Latest Test 2A disposable qualification project |
| `SIA4010_TEST3A_DISPOSABLE.zip` | Test 3A capability project |
| `SIA4010_TEST4_DISPOSABLE.zip` | Test 4 capability project |
| `SIA4010_TEST5A_DISPOSABLE.zip` | Test 5A capability project |
| `SIA4010_TEST6_DISPOSABLE.zip` | Test 6 capability project |
| `SIA4010_TEST7_DISPOSABLE.zip` | Test 7 capability project |

Verify every archive against `SHA256SUMS.txt` before extraction. Extract each
archive into a writable local directory, open the resulting project folder in
IESVE 2025 and work only on a copy. Historical JSON receipts can contain the
original absolute workstation path; maintained launchers derive live paths from
the active VE project and must not depend on those historical strings.

## Limits

- These snapshots are reproducibility inputs, not official SIA certificates.
- A disposable or diagnostic model is not automatically an accepted reference
  model; retain the status recorded in its evidence files.
- Do not reuse client evidence for another project.
- Keep this repository private. The archives may contain internal, licensed or
  project-specific material and are not cleared for public redistribution.
- Generated reports should normally be regenerated from the active project and
  current source commit rather than treated as timeless truth.
