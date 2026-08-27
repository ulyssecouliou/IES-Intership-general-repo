# Wegleitung SIA 4010 / Validierung / Anwenderbericht

**Test Nr.** 1

> Status: `ANWENDERBERICHT_DRAFT_UNSIGNED`
>
> This report states what was executed and observed. It is not a validation claim, and it carries no SIA or IES conformity statement. Only the SIA sub-commission can attest a validation.

---

## Programm

IES Virtual Environment, 2025.2.0.0, ApacheSim, Integrated Environmental Solutions (IES); Version string read from ve_model_snapshot.ve_version in the recorded 600FF model report, not from documentation.

## Eingabeparameter

- Test cell per BS EN ISO 52016-1:2017 clause 7, as required by the SIA 4010 Test 1 specification.
- Mechanical ventilation set to zero and verified zero by read-back after mutation (corrected 2026-08-12, commit c7e906b).
- Prescribed infiltration retained separately from ventilation: max flow 0.3075 with units_val = 2, verified retained by read-back; every other air exchange verified exactly zero.
- Thermal-template inheritance disabled, so the room condition carries the case values rather than an inherited template.
- Free-floating cases (600FF, 900FF) run without heating or cooling setpoints; the six normative cases carry no acceptance criterion by specification.

## Daten

- Climate: ISO 52016-1 DRYCOLD (Denver Stapleton), file DRYCOLD_IESVE.epw, path recorded in the model report parameter 'weather_file'. This is the Test 1 climate; it is NOT SIA 2028.
- Reference results: refs/reference-data/test-1.ref.json, frozen from Resultaterfassung_Test1.xlsx, status CORRECTED_PASS_4.
- Acceptance criterion: Spezifikation_Test1.pdf, section Testkriterien, quoted verbatim in engine/test1_engine.py lines 14-25. Case 1E is the only case carrying a pass/fail criterion; the six normative cases state 'Es gibt dafuer kein Abweichungskriterium'.
- Recorded results and checksums: sia4010_evidence/autonomy/sia4010_case_evidence.json, reproduced in the generated 'Recorded evidence' section of this report.

## Spezielle Annahmen

- Results recorded before 2026-08-12 12:55 predate the zero-mechanical-ventilation correction and are treated as baselines to requalify, not as results. At the time of writing this applies to cases 600 (APS of 2026-08-09) and 640 (APS of 2026-08-11); case 600FF was requalified after the correction (APS of 2026-08-12 14:18).
- Cases 900, 940, 900FF and 1E carry no recorded result and are listed as such rather than omitted, so the scope of the submission is unambiguous.
- Case 1E is not generated: the specification defines it as diagnostic case 1D plus a fabric awning, and cases 1A to 1D are not implemented.

## Feststellungen

> [TO VERIFY] This section is never generated. It must be written by the engineer answering for the submission.
>
> Declare and explain every deviation from the reference results here. A documented deviation is admissible: the E4Tech reference program itself declared large deviations in cooling energy for case 900, attributing them to the wall model and possibly to climate data and infiltration. An undeclared deviation is not.

---

## Recorded evidence

Read from the central evidence ledger. This section is generated and must not be edited by hand; correct the ledger instead.

| Case | Model | Simulation | Result | Metrics | Criterion available | Output scope complete |
|---|---|---|---|---:|---|---|
| `test_1/1E` | MISSING | NOT_RUN | NOT_CHECKABLE | — | not recorded | not recorded |
| `test_1/600` | VERIFIED | SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION | REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION | 88 | no | yes |
| `test_1/600FF` | VERIFIED | SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION | REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION | 39 | no | yes |
| `test_1/640` | VERIFIED | SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION | REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION | 88 | no | yes |
| `test_1/900` | MISSING | NOT_RUN | NOT_CHECKABLE | — | not recorded | not recorded |
| `test_1/900FF` | MISSING | NOT_RUN | NOT_CHECKABLE | — | not recorded | not recorded |
| `test_1/940` | MISSING | NOT_RUN | NOT_CHECKABLE | — | not recorded | not recorded |

### Result files and checksums

| Case | APS file | SHA-256 |
|---|---|---|
| `test_1/600` | `SIA4010_test_1_600_20260809_235015.aps` | `060ef2e22954d60491ccc154d9f8bb2d776a4cc581f488546cd901784e3fb61e` |
| `test_1/600FF` | `SIA4010_test_1_600FF_20260812_141823.aps` | `bcbb9deb7b42a6702d6b288fabbca47981ede9dc5aaa522c32f65a41df34f813` |
| `test_1/640` | `SIA4010_test_1_640_20260811_234852.aps` | `82629753568e33c341c6831417caad97d1f02de92a222c7e5b2b0b9ae43d8592` |

### Cases without a recorded result

Listed rather than omitted, so the scope of the submission is unambiguous.

- `test_1/1E` — model MISSING, simulation NOT_RUN
- `test_1/900` — model MISSING, simulation NOT_RUN
- `test_1/900FF` — model MISSING, simulation NOT_RUN
- `test_1/940` — model MISSING, simulation NOT_RUN

---

## Outstanding before this report can be signed

- Feststellungen: at least one observation, written by a named engineer. Declare and explain every deviation from the reference results here.
- author: the person answering for these observations
- report_date: the date the observations were made

---

[TO VERIFY] date / author — the form is signed by a person, never by the software.

<sub>Evidence ledger: `C:\Users\ulysse.couliou\Documents\IES Internship\IES-Intership-general-repo\sia4010_evidence\autonomy\sia4010_case_evidence.json`</sub>
