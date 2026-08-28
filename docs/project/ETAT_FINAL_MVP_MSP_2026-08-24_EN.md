> **Note:** Translated from French original. See [ETAT_FINAL_MVP_MSP_2026-08-24.md](ETAT_FINAL_MVP_MSP_2026-08-24.md) for the source document.

# MVP / MSP closure status as of 24 August 2026

## Delivery decision

The product is a **deliverable MVP for internal review and supervised client demonstration**. It runs from IESVE, reads the model and the APS, collects project evidence, and produces a PDF and an Excel workbook in IES style. It constitutes neither a SIA certificate nor a SIA 4010 attestation.

The software MSP for readiness/audit is sufficiently established for an internal handover, subject to the final IESVE smoke test. Model compliance remains a project decision dependent on external evidence and a competent review.

## Last known real run

Latest export produced: `2026-08-24 17:55:03` for `SIA_compatible_model_TEST`.

- verdict: **NOT DETERMINED**;
- blocking findings: **0**;
- missing evidence: **4**;
- the comfort screen reports 1462 hours, but the normative operative-temperature method is not yet fully demonstrated: this number must therefore not become an automatic non-compliance;
- the modified ventilation and repaired heating profile have been simulated in a verified annual APS;
- the report still needs to be regenerated after entering and accepting the project evidence.

## What is completed on the product side

- Run-button launch and client interface;
- building strategy configurable per model;
- guided editor for six families of technical evidence;
- evidence storage in the active VE project, with `.bak` backup;
- fail-closed validation: an incomplete acceptance is forced to `pending`;
- 16/16 CSV templates registered and prepared without overwriting reviewed data;
- VE/CDB/APS extraction and SIA 380/2 checks available;
- PDF and Excel report with uniform IES header/footer;
- evidence pack ZIP, manifests and audit trail;
- SIA 4010 claim safeguards;
- Python tests and local release gate.

## What still depends on the project or a third party

| Item | Responsible party | Closure condition |
| --- | --- | --- |
| Approved building status and climate | Energy/SIA manager | Source, date and signature in the Project and climate tab |
| Overall project/reference energy comparison | Energy/SIA manager | Complete signed calculation with project/reference values |
| Ventilation controls and cooling performance | HVAC engineer | Design notes, manufacturer data sheets and class confirmation |
| Lighting controls | Electrical/lighting engineer | Signed SIA 387/4 mapping |
| Design electrical power | HVAC/electrical engineer | W/m2, area and cooling-need category |
| Complete summer comfort method | Simulation/SIA manager | Operative temperature, occupancy, threshold and period documented |
| Official SIA 4010 validation | SIA / competent sub-commission | Official package, results and external attestation |

## Strict limitations

The code cannot invent a technical value, sign on behalf of an engineer, independently choose the normative cooling-need category, purchase or redistribute a licensed standard, or produce a SIA 4010 attestation. Nor can it make a physical model compliant solely by changing the report.

The user operating procedure is described in `docs/user/WORKFLOW_CLIENT_SIA3802_FR.md` and the handover checklist in `docs/project/RELEASE_ACCEPTANCE_CHECKLIST.md`.
