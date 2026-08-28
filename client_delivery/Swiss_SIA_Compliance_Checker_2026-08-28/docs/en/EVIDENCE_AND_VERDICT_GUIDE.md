# Project evidence and verdict guide

## Fail-closed principle

The evidence editor records reviewer-owned declarations. It does not decide on
behalf of the reviewer. A row requested as `accepted` is forced back to
`pending` when a required value, source, date or reviewer is missing.

Evidence files are project-local and must match the active VE project label.
Never reuse an accepted row from another building without a new review.

## The seven evidence tabs

### 1. Project and climate

Record the project identifier, building status, climate basis, exact weather
file, site, altitude, weather authority, calculation use, scenario/period and
the source of the location and altitude. Also record reviewer identity, role,
organisation, competence basis, acceptance scope, date and source.

Declare the ventilation and lighting scope, flow/power sources, assumptions
register and the exact acknowledgement `ENGINEERING_ASSESSMENT_ONLY`.

### 2. SIA 2024 use mapping

Map every assessed room or thermal template to its real SIA 2024 use category.
The software must not infer a category solely from a room or template name.

### 3. Global comparison

Use:

```text
comparison_scope  = complete_sia3802_project
comparison_metric = global_energy_expenditure_index_sia380
```

Enter the reviewed project and reference values in the same unit. A `pass` is
valid only when the project value is less than or equal to the reference value.
Heating or cooling energy alone is not this whole-project comparison.

### 4. Ventilation control

Document every applicable system or scope: system ID, rooms/zones, mono- or
multizone type, canonical control class, airflow band, specific airflow,
airflow/fan command, demand sensor, control scope, minimum airflow and schedule.
Reconcile the declaration with the implemented VE controls and HVAC design.

### 5. Cooling generator

Record the actual air- or water-cooled class, nominal capacity, EER and/or SEER,
unit, manufacturer source, reviewer and date. An autosized zero capacity or an
unsupported efficiency value is not accepted evidence.

### 6. Lighting control

Map each room or template to the exact SIA 387/4 control type and record the
daylight-control state. A VE `ON` flag does not, by itself, prove a SIA 387/4
classification.

### 7. Electrical power

Record building status, required design electrical power in W/m², conditioned
area, cooling presence and cooling-necessity category. Use the approved sizing
calculation covering relevant fans, pumps, auxiliaries and conditioning loads.

## Shared review fields

Every accepted row must identify the responsible reviewer and traceable source.
Where exposed by the tab, complete `review_status`, `reviewer`, `review_date`,
`source_document`, `source_reference` and `notes`.

Use a person's full name as reviewer. An organisation name, an AI system or a
placeholder is not a reviewer identity.

## Evidence does not replace the model

Reviewer evidence can resolve facts that are genuinely external to VE. It must
not be used to conceal a known model defect or to claim a control strategy that
has not been implemented. After technical model changes, rerun ApacheSim and
regenerate the reports.
