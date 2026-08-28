# Quick start

## Before opening the interface

1. Work on an authorised copy of the client model.
2. Open and save that project in IESVE 2025.
3. Confirm the active weather file and latest annual APS results.
4. Close earlier reports that are still open in Excel or a PDF viewer.
5. Prepare the approved client logo and the source documents required by the
   evidence review.

## Run the assessment

1. Open the IESVE Scripts window.
2. Select `Run_VE_Swiss_Compliance.py` in the root of this delivery.
3. Press **Run**.
4. Enter the client, project, site, contact, author and report-reference data.
5. Review the building strategy declarations. These describe the project but
   never override objects read from VE.
6. Use the language selector if required. English is the default.
7. Capture the active Model Viewer image or select an authorised image.
8. Open **Project Evidence** and review all seven tabs.
9. Save each evidence tab after completing it.
10. Return to the main window and select **Generate Excel + PDF**.

The window returns to the foreground after Model Viewer capture and after the
evidence editor closes.

## Read the result correctly

- `COMPLIANT`: the decisive implemented checks pass and no autonomous blocker
  remains in the assessed scope;
- `NOT_COMPLIANT`: at least one determined blocking requirement fails;
- `NOT_DETERMINED`: required model data, results, method or reviewed evidence is
  missing.

Do not describe a coverage score as a compliance percentage. Do not describe a
`COMPLIANT` engineering assessment as an official SIA certificate.

## When a new APS simulation is required

Run a new annual ApacheSim simulation after changing geometry, constructions,
profiles, internal gains, setpoints, ventilation, HVAC systems, weather or any
input that affects results. A new APS is not required for a corrected client
name, logo, reviewer note or source-reference typo.
