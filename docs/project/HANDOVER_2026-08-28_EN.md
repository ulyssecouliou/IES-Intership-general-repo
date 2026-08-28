> **Note:** Translated from French original. See [HANDOVER_2026-08-28.md](HANDOVER_2026-08-28.md) for the source document.

# Final handover -- SIA 380/2 compliance and SIA 4010 validation

> **Historical French record.** The canonical maintainer documentation is in
> English. Start with `FINAL_TRANSMISSION_RECEIPT_2026-08-28.md`,
> `NEW_MAINTAINER_START_HERE.md`, `AUTHORITY_RESPONSE_2026-08-28.md` and
> `SIA4010_TESTS_1_7_STATUS_2026-08-28.md`. This dated French document is kept
> only for continuity and must not override the later English status records.

Reference date: 28 August 2026  
Canonical repository: `https://github.com/ulyssecouliou/IES-Intership-general-repo`  
Canonical branch after handover: `main`

Visibility verified on 27 August 2026: the repository returns `404` on
anonymous access and is therefore currently private or restricted. The 60
evidence e-mails are versioned on `main`; they will become publicly accessible
if the owner confirms and applies the switch to public visibility. This action
would expose the entire repository and must remain an explicit decision by the
IES/GitHub owner.

## 1. Purpose and legal scope

The repository contains two related but distinct products:

1. a technical assessment of an IESVE client model according to SIA 380/2:2022;
2. a preparation, qualification and evidence-collection pipeline for the
   SIA 4010 software validation tests.

The software does not issue an official SIA certificate, does not replace a
qualified reviewer, and cannot turn missing evidence into compliance. Verdicts
are deliberately *fail-closed*.

## 2. Entry point for the new maintainer

Read in this order:

1. `README.md`;
2. this document;
3. `docs/project/FINAL_TRANSMISSION_RECEIPT_2026-08-28.md`;
4. `docs/project/NEW_MAINTAINER_START_HERE.md`;
5. `docs/project/TRANSMISSION_CHECKLIST_2026-08-28.md`;
6. `docs/project/AI_USAGE_AND_GOVERNANCE.md`;
7. `docs/project/ENGLISH_DEFAULT_AND_LANGUAGE_SUPPORT.md`;
8. `docs/project/INTERNAL_DATASET_INVENTORY.md`;
6. `docs/project/ARCHITECTURE_AND_RUNTIME_GUIDE.md`;
7. `docs/project/DATA_EVIDENCE_AND_LICENSING.md`;
8. `docs/project/TESTING_RELEASE_AND_OPERATIONS.md`;
9. `docs/project/GITHUB_AND_OWNERSHIP_TRANSFER.md`;
10. `CLAUDE.md` and `docs/CLAUDE_REFERENCE.md`;
11. `docs/user/WORKFLOW_CLIENT_SIA3802_FR.md`;
12. `docs/project/RELEASE_ACCEPTANCE_CHECKLIST.md`;
13. `docs/project/REVIEW_GOVERNANCE_SIA.md`;
14. `docs/project/REGISTRE_DEMANDES_EXTERNES.md`.

Main launch point in IESVE 2025:

```text
Run_VE_Swiss_Compliance.py
```

Embedded Python observed in VE 2025: `3.12.3`.

## 3. Client product SIA 380/2 status

### Delivered

- client interface and EN/FR/DE/IT language selection;
- English by default, translations verified by tests;
- VE, CDB and APS extraction;
- project evidence wizard with *fail-closed* acceptance;
- evidence stored in the model folder, with no hard-coded absolute project path;
- PDF and Excel reports with IES styling, cover page, header and footer;
- Model Viewer capture and main window brought back to the foreground;
- evidence pack, manifests, checksums and audit trail;
- limitations, reservations, responsible parties and actions displayed in the reports;
- legal wording: technical assessment, not official certification.

### Last client model examined

`SIA_compatible_model_TEST_before_heating_fix`

Latest report produced on 27 August 2026:

- overall verdict: `NOT DETERMINED`;
- blocking findings identified: `0`;
- missing evidence: `4`;
- envelope, openings, gains, setpoints and HVAC: `COMPLIANT` within the
  automatable scope of the report;
- ventilation: `NOT DETERMINED`;
- dynamic comfort: `NOT DETERMINED`.

This result is correct: the wizard must not be filled with invented values
to artificially produce a green screen.

### Evidence still required on a real project

- weather/location/altitude and climatic use accepted by a reviewer;
- overall project/reference energy comparison per SIA 380/2;
- prescribed hot/cold design-day simulations;
- ventilation control per Table 4, sensors and airflow reduction;
- SIA 2024 usage mapping;
- SIA 387/4 lighting mapping and power source;
- fan, pump, auxiliary and coil powers;
- cooling generator class and AHU heat recovery;
- complete dynamic comfort evidence;
- reviewer name, competence, scope and dated acceptance.

Responsibilities: see `docs/project/REVIEW_GOVERNANCE_SIA.md`.

## 4. SIA 4010 validation test status

### Test 1

- six reference ISO cases (`600`, `640`, `600FF`, `900`, `940`, `900FF`)
  simulated and recorded;
- four annual diagnostic deliverables (`1A` to `1D`) recorded;
- `1E` prepared, shading controls `150/150 W/m2` confirmed by
  Professor Gerhard Zweifel and qualified in VE;
- Test 1 overall **not completed** because `1E` still fails the official comparison.

Main 1E blocker: VE 2025 returns external protection reflectances at
approximately `0.100`, whereas the target values are:

```text
external_shade_solar_reflectance   = 0.490
external_shade_visible_reflectance = 0.496
```

The Python setters are not exposed (`unrecognised option`) and the fields
have not been identified in APcdb. Do not replace this blocker with a silent
assumption. Other reservations: APS optical equivalence, incident radiation
on the exterior plane not exposed in the APS tried, radiative surface
coefficients unavailable in the APS series, and numerical failure of the
official 1E band.

### Test 2A

- geometry: 1 volume and 2 openings imported and read back;
- shading control setter: `PASS`;
- writable optical subset 2E1: `PASS`;
- not completed: native profile graphs, non-writable reflectances,
  angular optics/secondary exchanges and APS equivalence remain to be closed.

### Test 3

- variants and lighting/sensor API surface audited;
- facade blind binding added;
- not completed: exact sources, qualified model, simulation and comparison.

### Tests 4, 5, 6 and 7

- exact cases and plant/HVAC API surfaces audited;
- external bindings added for fan curves, staged control and heat-pump
  performance tables;
- not completed: `Room system read-back` observed false in probes and
  `SOURCE_BINDINGS_REQUIRED`; exact models, simulations and criteria must
  still be qualified.

### External questions already raised and responses integrated

- Test 1E: total incident solar radiation on the exterior plane; closure
  at `>= 150 W/m2`, reopening below `150 W/m2`, no hysteresis; VE mapping
  `lower=150`, `raise=150` confirmed.
- Test 2A: Saturday/Sunday rest, 1 January is a Saturday, no public holidays,
  365-day calendar, values applied to the hour ending at the ordinal,
  simultaneity `0.80` directly on the hourly profile.

The 60 Outlook e-mails are archived under `docs/project/emails/` and published
with the repository in order to transmit the normative clarifications and
useful exchanges. This publication was explicitly authorised by the project
manager on 27 August 2026. The folder README indexes the threads and recalls
the precautions for handling personal and internal information.

## 5. Reproducible software validation

From the repository root:

```powershell
python -m pytest -q
python -m black --check --line-length 90 core engine schemas swiss_sia ui scripts tests ve_adapter
python -m flake8 swiss_sia ui scripts core schemas engine ve_adapter tests --jobs 1 --config .flake8
python -m mypy --strict --show-error-codes core schemas
python -m mypy --strict --show-error-codes --exclude '^$' swiss_sia/assessment_governance.py swiss_sia/client_report_context.py swiss_sia/project_evidence_translations.py swiss_sia/value_integrity.py
```

Under a Windows sandbox that blocks access to temporary directories, the
suite may produce many spurious `PermissionError` failures. The delivery
reference must be run with a fully accessible `%TEMP%`. Tests requiring the
native IESVE runtime must additionally be launched from VE 2025.

## 6. Private data included and remaining exclusions

The private repository now contains the authorised normative and internal
sources, the evidence e-mails, as well as ten ZIP snapshots of the reference,
diagnostic and client-test VE/APS projects. Their SHA-256 checksums and usage
rules are documented in `handover/ve_projects/`.

Deliberately absent: future active VE projects not yet frozen, regenerable
repetitive reports and outputs, local dependencies, caches, Office lock files
and temporary directories. The presence of licensed sources in this private
repository does not authorise their public redistribution.

## 7. Recommended next actions

1. Ask the IES/APcdb team how to enter or map the two external reflectances
   of Test 1E in VE 2025.
2. Re-run 1E with a reviewed exact model, capture the template, simulate
   and then analyse the official evaluation report.
3. Finalise the native profile and APS equivalence for Test 2A.
4. Obtain/validate the source bindings and system read-back for Tests
   3 to 7, then run each exact model.
5. On the client product, test a real project file that has all signed
   evidence, without using the demonstration model as proof of compliance.

## 8. Absolute rules going forward

- never invent a normative value, evidence or IESVE API;
- never turn `NOT_CHECKABLE` into `PASS`;
- never confuse a Python test, VE qualification and official SIA validation;
- never redistribute a standard, workbook or correspondence without rights;
- keep paths relative to the repository or the model folder;
- commit per task and maintain `main` as the canonical branch.
