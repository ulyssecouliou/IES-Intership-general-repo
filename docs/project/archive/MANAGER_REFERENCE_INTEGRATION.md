# Manager Reference Integration

## Purpose

This note records how the manager-provided documents are integrated into the
Swiss SIA Compliance Checker project.

Reviewed documents:

- `SIA 4010 Register validierter Software_24-09-17.pdf`
- `Sia 380_2 Navigator - Executive Summary & Product Backlog.docx`

These files improve the product guardrails and roadmap. They do not, by
themselves, certify IESVE, the Python checker or any client model.

## SIA 4010 Validated-Software Register

The register is dated 2024-09-17 and lists validated calculation programs and
their SIA 4010 validation classes.

Extracted register entries:

| Institution | Software | Classes | Valid until |
|---|---|---|---|
| Equa Solutions AG, Zug | IDA-ICE 5.0 beta | 1A, 1B, 2A, 2B, 3, 4A, 4B, 5 | 2029-03-20 |
| Fachhochschule Nordwestschweiz, Muttenz | Energy+ / OpenStudio | 1A, 1B, 2A, 2B, 4A, 4B | 2029-03-20 |
| Lemon Consult AG, Zurich | EDSL Tas | 1A, 3, 4A | 2029-03-20 |
| E4tech Software SA, Lausanne | Lesosai 2024 build 1903 | 1A, 1B, 2A, 2B, 3 | 2029-09-17 |

Project decision:

- `IESVE` is not listed in the manager-provided register.
- The checker must therefore keep SIA 4010 as evidence/readiness only.
- The report must not claim software-level SIA 4010 validation for IESVE unless
  separate official evidence is supplied and reviewed.

Implemented project changes:

- `swiss_sia/config.py` now contains the register entries and IESVE guardrail.
- `SIA4010 SOFTWARE REGISTER` is added to the generated Excel workbook.
- `sia4010_software_register_review_template.csv` is available as a guardrail
  review template.
- `SIA4010_IESVE_NOT_IN_MANAGER_REGISTER` is emitted as a low-severity alert.

## SIA 4010 Class Detail From Register

The register also clarifies how validation classes relate to applications,
solar-protection treatment and test sets.

| Class | Application scope | Solar-protection scope | Tests |
|---|---|---|---|
| 1A | Cooling need assessment and basic thermal load | No sun-position-dependent control | 1 and 2A |
| 1B | Cooling need assessment and basic thermal load | Rafflamellenstoren / venetian blinds | 1 and 2 |
| 2A | Lighting energy, heating demand and cooling demand | No sun-position-dependent control | 1, 2A, 3A to 3F |
| 2B | Lighting energy, heating demand and cooling demand | Rafflamellenstoren / venetian blinds | 1 to 3 |
| 3 | Humidification/dehumidification need assessment | Not separately restricted in the register | 1, 4 to 6 |
| 4A | System-related load, cooling energy and heating energy | No sun-position-dependent control | 1, 2A, 3A to 3F, 4 to 7 |
| 4B | System-related load, cooling energy and heating energy | Rafflamellenstoren / venetian blinds | 1 to 7 |
| 5 | Cooling/heating energy with existing demand profiles | Not separately restricted in the register | 7 |

Implementation note:

- This class detail is visible in the Excel register sheet.
- It complements, but does not replace, the SIA 4010:2023 class mapping already
  extracted from the standard PDF.

## SIA 380/2 Navigator Backlog

The navigator document defines the target product direction:

- normative-first inputs;
- separate constrained `SIA 380/2 Mode` and unconstrained advanced mode;
- closed lists for climate, usage, profiles, setpoints and technical systems;
- justifications for manual values;
- full auditability and exportable reports.

The current checker is a professional readiness/reporting MVP, not yet the full
constrained input navigator.

Implemented project changes:

- `swiss_sia/config.py` now contains `SIA3802_NAVIGATOR_BACKLOG`.
- `NAVIGATOR BACKLOG` is added to the generated Excel workbook.
- The backlog distinguishes implemented, partial and missing product capabilities.

## Main Product Gaps Identified

The manager backlog confirms the following missing or partial items for MSP:

- project-template fingerprinting and framework lock;
- approved Swiss climate-file manifest;
- room-by-room SIA 2024 usage-category assignment;
- closed SIA profile libraries for occupants, lighting and equipment;
- stronger ventilation/MacroFlo mapping to SIA scenarios;
- fixed setpoint/control extraction and unsupported-control alerts;
- generic HVAC system-template manifest with bounded efficiencies;
- expanded APS/Vista extraction and official SIA evaluation workbook import;
- exportable evidence package in PDF/DOCX in addition to Excel.

## Guardrail For Manager Communication

Safe wording:

- "The tool provides SIA 380/2 readiness checks and SIA 4010 evidence tracking."
- "SIA 4010 remains evidence-dependent and requires official validation evidence."
- "The current product is a constrained-reporting MVP and a roadmap toward a
  full SIA 380/2 navigator."

Avoid wording:

- "IESVE is validated under SIA 4010 by this checker."
- "The active client model is fully SIA 4010 validated."
- "The SIA 4010 software register proves this VE workflow is accepted."
