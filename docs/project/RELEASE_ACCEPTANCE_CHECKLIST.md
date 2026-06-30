# Release Acceptance Checklist - Swiss SIA Compliance Checker

## MVP Acceptance

The MVP is acceptable when all items below are true.

- Runs from `Run_VE_Swiss_Compliance.py` inside IESVE with the Run button.
- Does not require PowerShell or command-line arguments.
- Creates a timestamped Excel report in `reports/`.
- Opens with `MANAGER DASHBOARD` as the first worksheet.
- Includes `CLIENT SUMMARY`, `PREFLIGHT`, `P1 REMEDIATION`, `ASSUMPTIONS LIMITS`, `AUDIT LOG`, `SUMMARY`, `ACTION PLAN`, `COMPLIANCE RESULTS`, `SIA REQUIREMENTS`, `SIA DATA COVERAGE`, `INPUT REQUEST`, `SIA4010 READINESS`, `DYNAMIC RESULTS`, `ALERT SUMMARY`, `ALERTS`, `DATA QUALITY`, `DETAILED SCORES`, and `ROOMS`.
- Separates SIA 380/2 automated checks from SIA 4010 official evidence status.
- Never treats missing SIA 4010 evidence as a building `PASS`.
- Never treats `NOT_CHECKABLE` as a red `FAIL` in the executive view.
- Lists SIA 4010 detected evidence files and missing evidence families.
- Lists priority remediation actions with owner/evidence expectations.
- States safe claim wording and certification guardrails.
- Produces a critical or fail preflight status if no VE rooms are extracted.
- Compiles without Python syntax errors.
- Opens in Excel without a repair prompt.
- Contains no obvious formula error values such as `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?` or `#N/A`.

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
2. Run `Run_VE_Swiss_Compliance.py` from VE.
3. Confirm a timestamped workbook appears in `reports/`.
4. Confirm `MANAGER DASHBOARD` is the first worksheet.
5. Confirm `CLIENT SUMMARY`, `P1 REMEDIATION`, `ASSUMPTIONS LIMITS` and `AUDIT LOG` are present.
6. Confirm `PREFLIGHT` has no unexpected `FAIL`.
7. Confirm SIA 4010 tests remain `NOT_CHECKABLE` unless official evidence was provided.
8. Confirm no worksheet is blank or unreadable.
9. Confirm `SUMMARY`, `COMPLIANCE RESULTS`, `ALERT SUMMARY` and `DETAILED SCORES` are present.
10. Confirm Excel opens the workbook without asking to repair it.
