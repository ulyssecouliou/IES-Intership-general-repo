> **Note:** Translated from French original. See [WORKFLOW_CLIENT_SIA3802_FR.md](WORKFLOW_CLIENT_SIA3802_FR.md) for the source document.

# SIA 380/2 Client Workflow

## 1. Before launching

1. Open and save the correct project in IESVE 2025.
2. Verify that the latest annual APS matches the active model.
3. Close in Excel/PDF any old reports with the same name.
4. Gather the source documents listed in the "What to request" section.

## 2. Enter report information

From the VE Scripts window, launch
`Run_VE_Swiss_Compliance.py` directly. Fill in the client, project, address,
reference, author, and the strategy specific to the building: solar protections,
operable windows, and mechanical cooling.

These declarations describe the project; they do not replace the objects detected in VE.

## 3. Complete the technical evidence

Click **Project Evidence** in the interface. The seven tabs are:

1. **Project and climate**: new/existing status, climatic basis, station, altitude, and approved source.
2. **SIA 2024 assignment**: reviewed mapping between each room or VE template and its actual usage category.
3. **Global comparison**: energy consumption index for the full project, reference, unit, and signed result.
4. **Ventilation control**: one row per system/zone, with type, control class, flow rate range, and source.
5. **Cooling generator**: air/water class, capacity, EER and/or SEER.
6. **Lighting control**: room or template mapping to SIA 387/4.
7. **Electrical power**: required power in W/m2, conditioned area, presence and necessity of cooling.

Leave `review_status = pending` as long as the responsible person has not approved the row. If `accepted` is chosen while a name, date, required value, or source is missing, the software automatically resets the row to `pending`.

CSV files are saved in `<VE project>/sia4010_evidence/`. The previous file is kept as `.bak` when a modification is made.

## 4. Generate and check

Click **Generate Excel + PDF**. Deliverables are written to `<VE project>/SIA Compliance Reports/`.

- `COMPLIANT`: all decisive criteria within scope are evaluated and no blocking evidence is missing;
- `NOT COMPLIANT`: at least one evaluated criterion fails;
- `NOT DETERMINED`: an essential piece of evidence or method is still missing.

Never present the coverage indicator as a regulatory verdict.

## 5. When to rerun ApacheSim

Rerun the simulation if the model, profiles, ventilation, systems, setpoints, or weather have changed. A correction to a client name, logo, documentary source, or signature does not require a new APS calculation; simply regenerate the report.

## What to request and from whom

### Energy manager / SIA specialist

- applicable new or existing status;
- approved climatic basis, station, and altitude;
- SIA 380 project/reference global comparison with values, unit, and conclusion;
- selected summer comfort method, threshold, occupancy period, and operative temperature treatment;
- name, date, and reference of the document authorizing acceptance.

### HVAC engineer

- mapping between VE system IDs and design systems;
- single-zone/multi-zone type, control class, minimum flow rate, schedule, demand sensor, and specific flow rate range;
- cooling generator capacity and EER/SEER performance;
- AHU datasheets, heat recovery, and pressure drop data if applicable.

### Electrical / lighting engineer

- room/template mapping to SIA 387/4 control types;
- daylight strategy and design document;
- required electrical power for auxiliaries/transport/conditioning and conditioned area used in the calculation.

### Architect / facade specialist

- type and control of solar protections;
- actually operable windows and opening strategy;
- glazing datasheets, `g_total` with protection, and thermal bridge treatment.

### Project manager / client

- official project and client identity;
- authorized logo, report reference, and recipients;
- approved source documents and persons authorized to sign evidence.

### IES / SIA or competent authority

- official SIA 4010 package and terms of use;
- confirmation of the targeted validation class;
- submission procedure and final sub-commission attestation.

The software can prepare, check, and package this information. It cannot approve it or issue the attestation in place of these responsible parties.

## Understanding a missing data item

A missing data item does not necessarily indicate that the VE model is wrong.
It may belong to one of these four families:

1. **Not modeled**: the object or property should exist in VE but is not populated.
2. **Not exposed by the API**: the data may exist in the interface or ApacheHVAC, but VEScripts cannot reliably read it.
3. **External to the model**: the value belongs to a calculation note, a manufacturer datasheet, a drawing, or a project decision.
4. **Method not automated**: the software does not yet implement the prescribed protocol, for example design days or the full reference building simulation.

The workbook contains two complementary aids:

- `CAPABILITY GUIDE` explains what is automated, what is not, why, the exact evidence expected, who is responsible, and the effect on the verdict;
- `INPUT REQUEST` filters this list to show only the items still needed for the active project.

The approach is deliberately conservative: an unknown piece of information stays
`NOT_CHECKABLE` or `NOT DETERMINED`. It never becomes zero, compliant, or
non-compliant by assumption.

## Interface and report language

English is selected by default for a new project. The language selector
offers `English`, `Deutsch`, `Francais`, and `Italiano`. The change is
applied immediately to the entire window and the selection is saved in
the project context. It is then reused for the evidence editor,
the Excel workbook, and the PDF report. Technical values and regulatory
identifiers (`SIA 380/2`, VE codes, `PENDING` states, etc.) are not translated.
