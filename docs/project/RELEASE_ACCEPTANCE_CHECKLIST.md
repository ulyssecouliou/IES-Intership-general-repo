# Release Acceptance Checklist - Swiss SIA Compliance Checker

## MVP Acceptance

The MVP is acceptable when all items below are true.

- Runs from `Run_VE_Swiss_Compliance_Hub.py` inside IESVE with the Run button;
  the Hub delegates the client audit/report to the maintained compliance path.
- Does not require PowerShell or command-line arguments.
- Creates a timestamped Excel report in `reports/`.
- Opens on the compact `COVER`/`INDEX` navigation path and exposes
  `MANAGER DASHBOARD` as the primary executive worksheet.
- A SIA 380/2 client-scope workbook includes `COVER`, `MODEL VIEWER`, `INDEX`,
  `MANAGER DASHBOARD`, `ACTION DASHBOARD`, `CLIENT SUMMARY`, `PREFLIGHT`,
  `P1 REMEDIATION`, `FACADE GLAZING REVIEW`, `FRAME FRACTION AUDIT`,
  `ENVELOPE U REVIEW`, `VE G-VALUES AUDIT`, `ASSUMPTIONS LIMITS`, `AUDIT LOG`,
  `COMPLIANCE RESULTS`, `REFERENCE PROJECT`, `SIA REQUIREMENTS`,
  `SIA DATA COVERAGE`, `INPUT REQUEST`, `SIA3802 JUSTIFICATIONS`,
  `OPEN ITEMS BACKLOG`, `NAVIGATOR BACKLOG`, `DYNAMIC RESULTS`,
  `ALERT SUMMARY`, `ALERTS`, `DATA QUALITY` and `ROOMS`.
- A combined SIA 380/2 + SIA 4010 scope additionally exposes the maintained
  SIA 4010 readiness, prevalidation, class-matrix and software-register sheets.
- Separates SIA 380/2 automated checks from SIA 4010 official evidence status.
- Never treats missing SIA 4010 evidence as a building `PASS`.
- Never treats `NOT_CHECKABLE` as a red `FAIL` in the executive view.
- Lists SIA 4010 detected evidence files and missing evidence families.
- Shows a SIA 4010 class matrix covering `1A`, `1B`, `2A`, `2B`, `3`, `4A`, `4B` and `5`, including required tests and missing official evidence.
- Shows PDF-based SIA 4010 prevalidation for tests `1` to `7` and classes `1A` to `5`, with explicit wording that official SIA validation still requires the SIA execution package/sub-commission review.
- Shows reviewer-signed SIA 380/2 justifications separately from automated model values.
- Lists priority remediation actions with owner/evidence expectations.
- Shows VE/CDB glazing g-value traceability, including `bs_en_410`, `building_regulations`, `bfrc` and any active `g_total_with_shading` evidence status.
- Shows frame-fraction and envelope U-value remediation rows by construction.
- Maintains an `OPEN ITEMS BACKLOG` sheet so deferred or incomplete items remain visible across review cycles.
- Shows the manager-provided SIA 4010 software-register guardrail and states that IESVE is not software-level validated by that register unless separate official evidence is supplied.
- Shows the manager-provided SIA 380/2 navigator backlog and distinguishes current MVP capabilities from future constrained-input navigator work.
- States safe claim wording and certification guardrails.
- Produces a critical or fail preflight status if no VE rooms are extracted.
- Compiles without Python syntax errors.
- Opens in Excel without a repair prompt.
- Contains no obvious formula error values such as `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?` or `#N/A`.
- Produces a paginated PDF with readable findings, observed model values,
  applicable limits, normative sources and distinct blocking/missing/advisory counts.
- Generates all 16 project-specific evidence CSV templates without overwriting
  reviewer-edited files.

## MVP Known Limits

- SIA 380/2 direct checks cover envelope U-values, window Uw, glazing g-value and partial infiltration evidence.
- Ventilation, lighting, HVAC systems, dynamic results and SIA 4010 official validation remain readiness checks unless required data/evidence is complete.
- The workbook is a professional readiness/audit report, not an official SIA certificate.

## MSP Acceptance

The MSP should add the following.

- Expanded APS/Vista result reading for CO2, lighting, fans, final energy and richer hourly traces.
- Expanded `DYNAMIC RESULTS` worksheet with more hourly/annual outputs and data-source traceability.
- SIA 2024 use-category mapping for occupancy, gains, lighting, ventilation and schedules.
- SIA 387/4 lighting and solar protection control mapping.
- Full ventilation/AHU checks: airflow bands, control class, pressure drops, airtightness, heat/moisture recovery.
- Cooling EER/SEER and heating SCOP checks by system type and power band.
- PV worksheet covering area, tilt, azimuth, peak power and performance factor.
- Automatic population or import of official SIA 4010 evaluation workbooks.
- Evidence pack export containing report, raw outputs, assumptions, official evidence list and audit log.

## Release Smoke Test

Before sharing a release, run this minimum test.

Automated local check, outside VE:

```powershell
python -m pip install -r scripts/quality/requirements.txt
python scripts/quality/validate_release.py
```

1. Open a known VE model.
2. Run `Run_VE_Swiss_Compliance_Hub.py` from VE and choose the client audit/report action.
3. Confirm a timestamped workbook appears in `reports/`.
4. Confirm the `COVER`/`INDEX` navigation and `MANAGER DASHBOARD` are readable.
5. Confirm `CLIENT SUMMARY`, `P1 REMEDIATION`, `ASSUMPTIONS LIMITS` and `AUDIT LOG` are present.
6. Confirm `PREFLIGHT` has no unexpected `FAIL`.
7. Confirm SIA 4010 tests remain `NOT_CHECKABLE` unless official evidence was provided.
8. In combined scope, confirm `SIA4010 PREVALIDATION` lists tests `1` to `7`.
9. In combined scope, confirm `SIA4010 CLASS MATRIX` lists all classes from `1A` to `5`.
10. Confirm no worksheet is blank or unreadable.
11. Confirm `COMPLIANCE RESULTS`, `ALERT SUMMARY`, `ALERTS` and `DATA QUALITY` are present.
12. Confirm Excel opens the workbook without asking to repair it.
13. Confirm the PDF contains no raw translation key, clipped finding or contradictory pass/fail wording.
14. Run **Complete project evidence** and confirm 16 project-labelled CSV files are present.
