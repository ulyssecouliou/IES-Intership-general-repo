# Swiss SIA Compliance Checker

## Unified VEScripts hub

Open and save the target VE project, then run
`Run_VE_Swiss_Compliance_Hub.py` from the IESVE Scripts window. The scrollable
hub delegates to the existing read-only client audit, evidence wizard,
controlled reviewed-template remediation, compliance report, reference-model
workflow, SIA 4010 Model Builder and
eight-class navigator. VE-mutating entries are disabled unless the active
project name explicitly ends in `_TEST`, `_COPY` or `_DISPOSABLE`.

For a reviewed room-level correction on a disposable client copy, use the hub
action **Apply reviewed room templates** or run
`Run_VE_SIA3802_Approved_Template_Remediation.py`. The operation requires named
approval evidence, creates an immutable preview, verifies VE read-back and then
requires the read-only audit to be rerun before the copy is saved. It never
creates or guesses regulatory values.

Hub action 4 first opens `Run_VE_Swiss_Reference_Model_Setup.py`. The setup
requires an explicitly selected EPW, copies it and the maintained JSON inputs
into the disposable project, records the EPW SHA-256 and LOCATION metadata,
backs up any existing project JSON, and only then starts the fail-closed VE
generator. An unknown climate scenario remains
`UNCONFIRMED_REVIEW_REQUIRED`; it is never inferred from a filename.

The hub reports the current capability boundary rather than implying complete
validation: one of the 30 exact SIA 4010 cases has a verified guarded mutation
path, five have runtime-qualification paths, and the remaining cases are still
preparation/readiness workflows.

Professional IESVE Run-button workflow for Swiss SIA 380/2:2022 readiness checks and SIA 4010:2023 validation-evidence tracking.

This project produces readiness and audit artifacts. The workbook and evidence
pack are never official SIA certificates by themselves; official certification
or validation remains a separate decision by the responsible authority after
reviewing the required evidence.

## Supported Workflow

Use this file from the IESVE Scripts window:

```text
Run_VE_Swiss_Compliance.py
```

For a first read-only diagnosis on a disposable client-model copy, run:

```text
Run_VE_Swiss_Compliance_Remediation_Probe.py
```

The remediation probe lists the exact surfaces, openings and rooms requiring
review and separates VE-model corrections from VEScripts extraction gaps,
ApacheSim output gaps and reviewer-owned evidence.  It writes JSON and text
diagnostics under the active project without changing VE model data.

If reviewer CSV files need to be initialized first, run:

```text
Prepare_SIA4010_Evidence_Folder.py
```

The end user does not need PowerShell or command-line access.

## What The Tool Does

- Opens the active IESVE project through the IESVE Python API.
- Extracts rooms, surfaces, openings and available model data.
- Runs automated and partial SIA 380/2 checks where the VE data is available.
- Builds a conservative SIA 4010 readiness matrix.
- Scans `sia4010_evidence/` for official evidence files.
- Generates a timestamped Excel workbook in `reports/`.
- Generates a timestamped evidence-pack ZIP in `reports/`.
- Generates one Excel workbook per run by default. The optional latest-report alias is disabled in `swiss_sia/config.py`.

## What The Tool Does Not Claim

- It does not certify the model as fully SIA compliant.
- It does not validate IESVE or the model under SIA 4010 without official SIA evidence files.
- It does not replace the responsible engineer or compliance reviewer.
- It does not invent pass/fail decisions where the PDF requires external standards, official test files or reviewer judgement.

## Main Workbook Sheets

- `MANAGER DASHBOARD`: executive KPIs, charts and top actions.
- `CLIENT SUMMARY`: safe manager/client-facing wording and immediate decisions.
- `PREFLIGHT`: run readiness and extraction checks.
- `P1 REMEDIATION`: owner-ready board for priority issues.
- `FACADE GLAZING REVIEW`: construction-level glazing/solar-protection action sheet.
- `FRAME FRACTION AUDIT`: construction-level frame-fraction failures and evidence needs.
- `ENVELOPE U REVIEW`: construction-level envelope U-value review and remediation status.
- `VE G-VALUES AUDIT`: CDB `g_value`, `bs_en_410`, `building_regulations`, `bfrc` and `g_total` traceability.
- `ASSUMPTIONS LIMITS`: certification guardrails and known limitations.
- `AUDIT LOG`: run metadata, evidence state and audit guardrails.
- `SUMMARY`: score summary.
- `ACTION PLAN`: grouped remediation actions.
- `COMPLIANCE RESULTS`: category results.
- `SIA REQUIREMENTS`: source-traced requirement matrix.
- `SIA DATA COVERAGE`: data, APS/Vista and evidence coverage for SIA 380/2 and all SIA 4010 classes.
- `INPUT REQUEST`: practical list of missing client/model-reviewer inputs.
- `SIA3802 JUSTIFICATIONS`: reviewer-signed retained deviations that can be shown as `JUSTIFIED_BY_EVIDENCE`.
- `OPEN ITEMS BACKLOG`: persistent dynamic backlog for unresolved model and product gaps.
- `SIA4010 READINESS`: SIA 4010 evidence and test readiness.
- `SIA4010 PREVALIDATION`: PDF-based prevalidation for tests 1 to 7 and classes 1A to 5, using SIA 380/2 + SIA 4010 published requirements.
- `SIA4010 CLASS MATRIX`: class-by-class SIA 4010 matrix for 1A, 1B, 2A, 2B, 3, 4A, 4B and 5.
- `SIA4010 SOFTWARE REGISTER`: manager-provided validated-software register guardrail.
- `NAVIGATOR BACKLOG`: SIA 380/2 navigator product backlog from the manager reference document.
- `DYNAMIC RESULTS`: APS/Vista indicators when IESVE ResultsReader exposes them.
- `ALERT SUMMARY`: grouped technical findings.
- `ALERTS`: raw detailed findings.
- `DATA QUALITY`: extraction coverage and missing-data risks.
- `DETAILED SCORES`: score components.
- `ROOMS`: extracted room-level data.

## Key Files

- `Run_VE_Swiss_Compliance.py`: IESVE Run-button launcher.
- `Run_VE_Swiss_Compliance_Remediation_Probe.py`: read-only disposable-copy diagnostic launcher.
- `Run_VE_SIA3802_Approved_Template_Remediation.py`: checksum-bound assignment of an existing, independently reviewed thermal template to explicitly selected rooms in a disposable copy.
- `Prepare_SIA4010_Evidence_Folder.py`: IESVE Run-button helper that prepares project-named evidence CSV files.
- `main.py`: compatibility wrapper for existing shortcuts.
- `swiss_sia/app.py`: workflow orchestration and timestamped report naming.
- `swiss_sia/excel_report.py`: Excel workbook generation.
- `swiss_sia/sia380_checker.py`: SIA 380/2 checks.
- `swiss_sia/sia4010_checker.py`: SIA 4010 readiness/evidence checks.
- `swiss_sia/sia4010_prevalidation.py`: PDF-based SIA 4010 prevalidation from VE/APS data.
- `swiss_sia/evidence_manager.py`: reviewer-evidence scanner for retained SIA 380/2 justifications.
- `swiss_sia/evidence_bootstrap.py`: evidence-template initializer for users without command-line access.
- `swiss_sia/evidence_pack.py`: manager/reviewer evidence-pack ZIP export.
- `swiss_sia/config.py`: PDF-traced values, requirement matrix and validation classes.
- `docs/source/`: Sphinx documentation source.
- `docs/project/`: project notes, handoff material and compliance traceability notes.
- `docs/project/GLAZING_EVIDENCE_GUIDE.md`: IESVE/CDB glazing evidence retrieval and handoff guide.
- `docs/project/MODEL_REMEDIATION_PLAYBOOK.md`: practical VE/CDB remediation workflow for the current ZOER_32_C1 findings.
- `docs/project/SIA3802_CLIENT_TEMPLATE_REMEDIATION_EN.md`: scope, safety contract, approval inputs and runtime procedure for client-template remediation.
- `docs/project/MANAGER_REFERENCE_INTEGRATION.md`: integration note for the manager-provided register and navigator backlog.
- `references/standards/`: local PDF standards/reference copies.
- `references/iesve/`: IESVE API notes and reference PDFs.
- `scripts/quality/validate_release.py`: local release-quality validator.

## Repository Layout

```text
.
|-- Run_VE_Swiss_Compliance.py      # VE Run-button launcher
|-- Prepare_SIA4010_Evidence_Folder.py # VE helper for evidence CSV setup
|-- main.py                         # compatibility wrapper
|-- swiss_sia/                      # production Python package
|-- scripts/                        # probes, quality checks and legacy utilities
|-- docs/                           # Sphinx docs + project notes
|-- references/                     # standards and IESVE reference material
|-- reports/                        # generated workbooks/logs
`-- sia4010_evidence/               # official SIA 4010 evidence drop zone
```

## SIA 4010 Evidence

Place official evidence in:

```text
sia4010_evidence/
```

Recommended filename prefixes:

- `SIA4010_official_test_specs_*`
- `SIA4010_official_evaluation_workbook_*`
- `SIA4010_candidate_results_*`
- `SIA4010_reference_comparison_*`
- `SIA4010_validation_class_confirmation_*`

File presence and classification are readiness indicators only. The content, official source and comparison validity must still be reviewed manually.

## MVP Status

The MVP is suitable for internal manager review when:

- It runs from the IESVE Run button.
- A timestamped report is generated.
- `MANAGER DASHBOARD` is first.
- `CLIENT SUMMARY`, `P1 REMEDIATION`, `FACADE GLAZING REVIEW`, `ASSUMPTIONS LIMITS` and `AUDIT LOG` are present.
- `VE G-VALUES AUDIT`, `SIA4010 SOFTWARE REGISTER` and `NAVIGATOR BACKLOG` are present for manager traceability.
- SIA 4010 remains `NOT_CHECKABLE` unless official evidence is complete.
- The workbook opens in Excel without repair prompts.

Run this local quality check outside VE before sharing a release:

```powershell
python -m pip install -r scripts/quality/requirements.txt
python scripts/quality/validate_release.py
```

## MSP Direction

The minimum saleable product should add:

- Expanded APS/Vista hourly result extraction for CO2, lighting, fans and final energy.
- Richer dynamic heating/cooling and temperature evidence.
- SIA 2024 use-category mapping.
- SIA 387/4 lighting and solar-control mapping.
- Ventilation/AHU control checks.
- Cooling EER/SEER and heating SCOP checks by system type and power band.
- PV evidence and energy balance support.
- Import/comparison support for official SIA 4010 evaluation workbooks.

## Navigateur de validation SIA 4010

> Verifie 2026-08-16 -- voir `docs/project/AUDIT_COMPLET_2026-08-16.md`.
> L'outil client de production vit **entierement dans `swiss_sia/`**. Le triptyque
> `engine/`+`ve_adapter/`+`ui/` ci-dessous n'est PAS le runtime client.

| Couche | Role | Statut |
|---|---|---|
| `swiss_sia/` | extraction VE, regles SIA 380/2 & 4010, scoring, rapports Excel + PDF client, evidence | **PRODUCTION** |
| `swiss_sia/reference_model/ve_api.py`, `data_extractor.py` | seul acces `iesve` de production | production |
| `refs/reference-data/` | valeurs de reference figees, recalculees et confrontees | donnees |
| `engine/` + `ve_adapter/` | recompute SIA 4010 independant + build des references (`scripts/build_*.py`) | outillage, hors runtime client |
| `ui/` | UI/exports Tkinter herites ; seuls `ui/design.py`+`ui/tk_theme.py` (styles) servent encore | herite |
| `traceability/` | matrices clause -> code -> test (etat de signature par test) | tracabilite |

Lancer le controle d installation, hors VE :

```
python scripts/run_test1_dans_ve.py --preflight
```

Dans VE, le meme fichier au bouton Run lance la sonde d introspection.

