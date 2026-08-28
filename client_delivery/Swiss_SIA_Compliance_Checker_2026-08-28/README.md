# Swiss SIA Compliance Checker — Client Delivery

Release date: 28 August 2026
Target runtime: IESVE 2025 / embedded Python 3.12
Default language: English
Optional languages: German, French and Italian

## Start here

Keep this entire folder together. Do not copy only the launcher: the
`swiss_sia`, `ui`, `config`, `assets`, `refs` and `templates` folders are runtime
dependencies.

1. Open and save the building model in IESVE 2025.
2. Confirm that the active model and the latest annual APS results belong to
   the same project state.
3. In the IESVE Scripts window, select `Run_VE_Swiss_Compliance.py` from this
   folder and press **Run**.
4. Complete the project information and strategy declarations.
5. Use **Project Evidence** to review the seven evidence families.
6. Capture the Model Viewer image.
7. Select **Generate Excel + PDF**.
8. Read every limitation and unresolved item before issuing the report.

Generated reports are written under:

```text
<active VE project>/SIA Compliance Reports/
```

Project-specific evidence is written under:

```text
<active VE project>/sia4010_evidence/
```

Despite this historical folder name, the client launcher reports the building
assessment scope for SIA 380/2 only. It does not present SIA 4010 software
validation as a property of a client building.

## Included launchers

| File | Purpose | Changes the VE model? |
|---|---|---:|
| `Run_VE_Swiss_Compliance.py` | Main client interface and Excel/PDF report generation | No |
| `Run_VE_Swiss_Compliance_Remediation_Probe.py` | Read-only diagnosis of model items requiring correction | No |
| `Prepare_Client_SIA_Weather.py` | Command-line conversion of an authorised weather archive into an audited EPW candidate | No |
| `Run_VE_Verify_Client_SIA_Weather.py` | Read-only IESVE verification of a derived EPW candidate | No |

The main launcher is the normal client entry point. The other three files are
support tools and should be used only when their documented situation applies.

## Documentation map

English is the canonical documentation language:

- `docs/en/QUICK_START.md` — normal client workflow;
- `docs/en/EVIDENCE_AND_VERDICT_GUIDE.md` — the seven evidence tabs and verdict
  rules;
- `docs/en/GLOBAL_COMPARISON_GUIDE.md` — decisive whole-project comparison;
- `docs/en/VE_MODEL_CORRECTIONS_GUIDE.md` — changes required in VE or evidence;
- `docs/en/GLAZING_EVIDENCE_GUIDE.md` — glazing and solar-protection evidence;
- `docs/en/REVIEW_GOVERNANCE.md` — reviewer responsibility and traceability;
- `docs/en/LIMITATIONS_AND_RESPONSIBILITIES.md` — legal and technical scope;
- `docs/en/TROUBLESHOOTING.md` — common operating problems;
- `docs/en/LANGUAGE_SUPPORT.md` — English default and language switching;
- `docs/en/AI_USAGE_AND_GOVERNANCE.md` — AI development disclosure.

French operator material is under `docs/fr/`. The demonstration video,
teleprompter, Word script and presentation files are under `training/`.

## Configuration

`config/company_profile.json` contains the report issuer profile. The client
logo and project-specific report details are selected in the interface and are
stored under the active VE project, not hard-coded into the software.

Do not place credentials, confidential source standards or unrelated client
files in this delivery folder.

## Compliance statement

The software provides a deterministic engineering assessment of the analysed
model and the evidence supplied by the user. It does not issue an official SIA
certificate, does not certify IESVE, and does not replace the responsible
project authority or the SIA validation body.

`COMPLIANT` may be displayed only when the implemented decisive checks pass and
the required reviewed evidence is complete. Missing evidence remains
`NOT_DETERMINED`; an entered value is never treated as proof merely because it
was typed into the interface.

## Integrity

`MANIFEST_SHA256.txt` lists every delivered file except the manifest itself.
Use it to verify that a copied delivery is complete and unchanged.
