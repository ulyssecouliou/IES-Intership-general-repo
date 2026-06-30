# Swiss SIA Compliance Checker

Professional IESVE Run-button workflow for Swiss SIA 380/2:2022 readiness checks and SIA 4010:2023 validation-evidence tracking.

This project produces a readiness and audit workbook. It must not be used as an official SIA certificate unless all required evidence is complete and reviewed by the responsible compliance authority.

## Supported Workflow

Use this file from the IESVE Scripts window:

```text
Run_VE_Swiss_Compliance.py
```

The end user does not need PowerShell or command-line access.

## What The Tool Does

- Opens the active IESVE project through the IESVE Python API.
- Extracts rooms, surfaces, openings and available model data.
- Runs automated and partial SIA 380/2 checks where the VE data is available.
- Builds a conservative SIA 4010 readiness matrix.
- Scans `sia4010_evidence/` for official evidence files.
- Generates a timestamped Excel workbook in `reports/`.
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
- `ASSUMPTIONS LIMITS`: certification guardrails and known limitations.
- `AUDIT LOG`: run metadata, evidence state and audit guardrails.
- `SUMMARY`: score summary.
- `ACTION PLAN`: grouped remediation actions.
- `COMPLIANCE RESULTS`: category results.
- `SIA REQUIREMENTS`: source-traced requirement matrix.
- `SIA DATA COVERAGE`: data, APS/Vista and evidence coverage for SIA 380/2 and all SIA 4010 classes.
- `INPUT REQUEST`: practical list of missing client/model-reviewer inputs.
- `SIA4010 READINESS`: SIA 4010 evidence and test readiness.
- `DYNAMIC RESULTS`: APS/Vista indicators when IESVE ResultsReader exposes them.
- `ALERT SUMMARY`: grouped technical findings.
- `ALERTS`: raw detailed findings.
- `DATA QUALITY`: extraction coverage and missing-data risks.
- `DETAILED SCORES`: score components.
- `ROOMS`: extracted room-level data.

## Key Files

- `Run_VE_Swiss_Compliance.py`: IESVE Run-button launcher.
- `main.py`: compatibility wrapper for existing shortcuts.
- `swiss_sia/app.py`: workflow orchestration and timestamped report naming.
- `swiss_sia/excel_report.py`: Excel workbook generation.
- `swiss_sia/sia380_checker.py`: SIA 380/2 checks.
- `swiss_sia/sia4010_checker.py`: SIA 4010 readiness/evidence checks.
- `swiss_sia/config.py`: PDF-traced values, requirement matrix and validation classes.
- `docs/source/`: Sphinx documentation source.
- `docs/project/`: project notes, handoff material and compliance traceability notes.
- `references/standards/`: local PDF standards/reference copies.
- `references/iesve/`: IESVE API notes and reference PDFs.
- `scripts/quality/validate_release.py`: local release-quality validator.

## Repository Layout

```text
.
|-- Run_VE_Swiss_Compliance.py      # VE Run-button launcher
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
- `SIA4010_candidate_results_APS_Vista_*`
- `SIA4010_reference_comparison_plots_*`
- `SIA4010_validation_class_confirmation_*`

File presence and classification are readiness indicators only. The content, official source and comparison validity must still be reviewed manually.

## MVP Status

The MVP is suitable for internal manager review when:

- It runs from the IESVE Run button.
- A timestamped report is generated.
- `MANAGER DASHBOARD` is first.
- `CLIENT SUMMARY`, `P1 REMEDIATION`, `ASSUMPTIONS LIMITS` and `AUDIT LOG` are present.
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
