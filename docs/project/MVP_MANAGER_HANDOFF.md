# Swiss SIA Compliance Checker - MVP Manager Handoff

## Objective

Deliver a professional IESVE Run-button workflow that reviews a VE model against the currently automated SIA 380/2:2022 checks, separates SIA 4010:2023 official validation evidence, and produces a manager/client-facing readiness workbook subject to reviewer approval.

This MVP is a readiness and audit workflow. It must not be described as a final SIA certificate until the open P1 items, missing MSP checks, and official SIA 4010 evidence pack are resolved and reviewed by the responsible compliance authority.

## What Is Included

- `Run_VE_Swiss_Compliance.py`: VE Run-button launcher.
- `main.py`: orchestration, unique report naming, preflight checks and latest-report alias.
- `excel_report.py`: professional Excel workbook generation.
- `sia380_checker.py`: automated and partial SIA 380/2 checks.
- `sia4010_checker.py`: SIA 4010 readiness and evidence scan, intentionally conservative.
- `config.py`: PDF-traced values, requirement matrix, validation classes and evidence expectations.
- `sia4010_evidence/`: drop zone for official validation files.
- `reports/`: timestamped workbook outputs.

## Manager Demo Flow

1. Open the target client project in IESVE.
2. Open the VE Scripts window.
3. Run `Run_VE_Swiss_Compliance.py`.
4. Open the latest timestamped workbook in `reports/`.
5. Start with `MANAGER DASHBOARD`.
6. Use `CLIENT SUMMARY` to explain the safe claim wording.
7. Use `P1 REMEDIATION` to show the immediate correction plan.
8. Use `ASSUMPTIONS LIMITS` to show professional risk control.
9. Use `SIA REQUIREMENTS` and `SIA4010 READINESS` if technical traceability is challenged.

## Current MVP Verdict Logic

- The workbook can support: "automated SIA 380/2 readiness review for extracted VE data".
- The workbook can support: "SIA 4010 evidence readiness matrix".
- The workbook must not support: "the model is fully SIA compliant".
- The workbook must not support: "the software/model is officially SIA 4010 validated".

## Workbook Sheets To Review

- `MANAGER DASHBOARD`: first page, KPI cards, charts and top actions.
- `CLIENT SUMMARY`: safe executive wording and immediate decisions.
- `PREFLIGHT`: confirms whether VE extraction and report generation are trustworthy.
- `P1 REMEDIATION`: owner-ready corrective action board for priority findings.
- `ASSUMPTIONS LIMITS`: certification guardrails and known limitations.
- `SUMMARY`: detailed score summary.
- `ACTION PLAN`: grouped actions from all alerts.
- `SIA REQUIREMENTS`: requirement matrix with source, status and next action.
- `SIA4010 READINESS`: official test/evidence matrix.
- `ALERT SUMMARY`: grouped technical findings.
- `ALERTS`: raw detailed findings.
- `DATA QUALITY`: extraction coverage and missing data risks.
- `DETAILED SCORES`: score components.
- `ROOMS`: extracted room-level data.

## Immediate P1 Treatment

The current client model should be treated in this order:

1. Glazing solar factor review.
   - Confirm whether VE `solar_factor` is EN 410 `g_perp`, SHGC, or a construction-level proxy.
   - If the retained SIA value is really above `0.50`, update glazing/shading or document a full reference calculation route.

2. External wall U-value review.
   - Resolve external wall constructions above `0.20 W/m2K`.
   - Either improve the construction assignment or attach a justified SIA 380/2 reference calculation.

3. SIA 4010 evidence pack.
   - Collect official SIA test specifications.
   - Collect official SIA Excel evaluation workbooks.
   - Export candidate APS/Vista results.
   - Generate reference comparisons.
   - Confirm target validation class.

## MVP Acceptance

The MVP is ready for internal manager review when:

- It runs from the VE Run button without PowerShell.
- A timestamped workbook is generated.
- `MANAGER DASHBOARD` is first.
- `CLIENT SUMMARY`, `P1 REMEDIATION` and `ASSUMPTIONS LIMITS` are present.
- SIA 4010 remains `NOT_CHECKABLE` unless official evidence is provided.
- Missing evidence is never treated as a false PASS.
- The latest workbook has no obvious Excel formula errors.

## MSP Roadmap

The MSP should add:

- APS/Vista hourly result extraction.
- Dynamic heating/cooling and temperature evidence sheets.
- SIA 2024 use-category mapping.
- SIA 387/4 lighting and solar-control mapping.
- Ventilation/AHU control checks.
- Cooling EER/SEER and heating SCOP by type and power band.
- PV evidence and energy balance support.
- Official SIA 4010 evaluation workbook import/comparison.
- Exportable evidence pack for audit handoff.
