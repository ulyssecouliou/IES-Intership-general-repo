# SIA 380/2 wizard values — direction demonstration

> **DEMO ONLY — NOT AN OFFICIAL SIA CERTIFICATE**  
> These values document the current synthetic test model. `accepted` may only be
> selected and the final confirmation checked by the named person after an
> actual review. Wizard completion documents evidence governance; it does not
> override missing technical criteria or turn `NOT DETERMINED` into a genuine
> compliance verdict.

## Identification and climate

| Wizard field | Value to enter |
|---|---|
| Project identifier | `SIA_compatible_model_TEST_before_heating_fix` |
| Building status | `NEW_BUILDING` |
| Climate basis | `CH2018 RCP8.5 2060 DRY — MeteoSwiss-derived IESVE transport candidate` |
| Reviewed weather file | `CHE_GVE_2060_RCP85_DRY.epw` |
| Location | `Genève / Cointrin weather station — synthetic demonstration model` |
| Altitude (m) | `411` |
| Weather source authority | `MeteoSwiss; project conversion to IESVE EPW` |
| Weather use case | `SIA3802_COOLING_NEED` |
| Weather scenario and period | `CH2018 RCP8.5, 2060, DRY future climate scenario` |
| Location source | `Active EPW LOCATION header: GVE, 46.247519, 6.127742` |
| Altitude source | `Active EPW LOCATION header: station elevation 411 m` |

## Review and responsibility

| Wizard field | Value to enter |
|---|---|
| Review status | `accepted` **only after actual approval; otherwise `pending`** |
| Reviewer | `[FULL NAME OF THE PERSON WHO ACTUALLY APPROVES]` |
| Reviewer role | `Responsible SIA 380/2 technical reviewer` |
| Reviewer organisation | `IES` |
| Reviewer competence basis | `[ACTUAL RELEVANT QUALIFICATION OR EXPERIENCE OF THE NAMED REVIEWER]` |
| Reviewer acceptance scope | `Climate inputs, model inputs, ventilation and lighting scope, flow and power sources, assumptions, reported results and all explicitly stated reserves for this synthetic demonstration model.` |
| Review date | `2026-08-27` **only if approval occurs on this date** |
| Source document | `IES internal SIA 380/2 synthetic demonstration-model review pack — 2026-08-27` **only if this controlled review record exists** |
| Source reference | `Active VE model, project evidence CSV files and report 20260827_125422` |
| Notes | `Synthetic management demonstration. This engineering assessment is not an official SIA certificate and does not establish official validation of IESVE.` |

## Assumptions and legal scope

| Wizard field | Value to enter |
|---|---|
| Assumptions status | `OPEN_ASSUMPTIONS` |
| Assumptions register | Use the text below |
| Report-use acknowledgement | `ENGINEERING_ASSESSMENT_ONLY` |

### Assumptions register

```text
Open assumptions and reserves:
1. Suitability of the CH2018 RCP8.5 2060 DRY weather dataset for the selected SIA 380/2 use requires responsible-reviewer acceptance.
2. The recorded elevation is the weather-station elevation; the project-site elevation is not independently confirmed.
3. Ventilation Table 4 system type, FAN_CTRL, sensor strategy and airflow-reduction logic remain to be evidenced.
4. Lighting control classification and approved installed/design lighting-power provenance remain to be evidenced.
5. Fan, pump, auxiliary and coil electrical-power evidence remains incomplete.
6. Cooling-generator classification and AHU heat-recovery evidence remain incomplete.
7. Prescribed heating and cooling design-day calculations are not available.
8. The decisive reviewed project/reference comparison is not complete.
9. Dynamic-comfort evidence is incomplete.
Owners: project energy specialist, HVAC designer, lighting designer and named responsible reviewer.
Due date: before any final compliance conclusion.
```

## Ventilation

| Wizard field | Value to enter |
|---|---|
| Ventilation strategy | `MECHANICAL_PRESENT` |
| Ventilation justification | `Mechanical ventilation is modelled in all three thermal rooms. VE readback gives 2.014 L/s/m², equivalent to 7.25 m³/(h·m²). Operable windows are also present. The SIA 380/2 Table 4 control classification, FAN_CTRL value, sensor strategy and airflow-reduction logic remain under review.` |
| Ventilation flow-rate source | `IESVE room air-exchange readback and assigned thermal templates: 2.014 L/s/m² = 7.25 m³/(h·m²). Design provenance must be reconciled with the approved HVAC airflow schedule.` |
| Ventilation scope | `All three thermal rooms: Office_01, Corridor_01 and Office_02; associated mechanical ventilation system and scheduled auxiliary airflow. Operable windows are recorded separately.` |

## Lighting and system power

| Wizard field | Value to enter |
|---|---|
| Lighting assessment scope | `IN_SCOPE` |
| Lighting power source | `IESVE room-template lighting-gain readback: 8.59 W/m² in the assessed rooms; final acceptance requires reconciliation with the approved lighting schedule and SIA 387/4 control mapping.` |
| Lighting scope justification | `Lighting is included for all assessed thermal rooms. Installed/design power and control classification remain subject to the lighting schedule and SIA 387/4 mapping.` |
| System power source | `IESVE system readback supplemented by the SIA3802 electrical-power evidence file and approved HVAC schedules or manufacturer data. Current evidence remains incomplete.` |
| Fan/pump/auxiliary/coil outputs required? | `YES` |
| APS output justification | `Required for fan, pump, auxiliary and coil electrical-power assessment; the required result evidence must be attached before a final conclusion.` |

## Final confirmation

Check **“I confirm that I reviewed this information…”** only when the named
reviewer has actually reviewed the listed sources, accepts the exact scope and
reserves above, and takes responsibility for that declaration.

## Conditions still required for a genuine compliant display

The application must continue to report `NOT DETERMINED` until the following
evidence is supplied and passes its checks:

1. reviewed project/reference comparison;
2. prescribed heating and cooling design-day results;
3. SIA 380/2 Table 4 ventilation-control evidence for all three rooms;
4. SIA 387/4 lighting-control mapping and approved lighting-power source;
5. fan, pump, auxiliary and coil electrical-power evidence;
6. cooling-generator and AHU heat-recovery classifications;
7. complete dynamic-comfort evidence.

Do not edit the evidence files or software logic merely to suppress these
findings. A presentation-only all-green screen must use a clearly labelled,
separate synthetic fixture whose complete passing evidence has been reviewed.
