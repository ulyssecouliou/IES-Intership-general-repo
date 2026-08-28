> **Note:** Translated from French original. See [SIA4010_TEST1_SIX_CASES_EXECUTION_GUIDE.md](SIA4010_TEST1_SIX_CASES_EXECUTION_GUIDE.md) for the source document.

# SIA 4010 Test 1 -- controlled execution of the six cases

## Target outcome

The MVP covers the six hourly cases prescribed by ISO 52016-1, clause 7.2:

| Case | Construction | Control |
|---|---|---|
| 600 | lightweight | continuous, 20 °C / 27 °C |
| 640 | lightweight | intermittent, 20 °C from 07:00 to 23:00 and 10 °C at night; cooling 27 °C |
| 900 | heavyweight | continuous, 20 °C / 27 °C |
| 940 | heavyweight | intermittent, 20 °C from 07:00 to 23:00 and 10 °C at night; cooling 27 °C |
| 600FF | lightweight | free-running |
| 900FF | heavyweight | free-running |

Each case must be run in its own saved VE project. Never reuse a project that has already received the geometry of another case.

## Campaign preparation

Create six empty, saved VE projects, for example:

```text
SIA4010_TEST1_600
SIA4010_TEST1_640
SIA4010_TEST1_900
SIA4010_TEST1_940
SIA4010_TEST1_600FF
SIA4010_TEST1_900FF
```

Keep an intact copy of each project before any mutation. The controlled weather file must be present in each project as specified by the case manifest.

## Walkthrough in VEScripts

For each project:

1. Open the project corresponding to the case in VE.
2. Run `Run_VE_SIA_Model_Builder_UI.py` from VEScripts.
3. Select the `SIA4010_OFFICIAL` profile, class `1A`, variant `test_1`
   and the case matching the project name.
4. Click **Prepare / Preparer** and review the preflight report.
5. Click **Create / Creer dans VE** once only.
6. Click **Probe Test 1 runtime inputs / Sonder les entrees runtime
   Test 1**. This step is strictly read-only.
7. As long as the probe does not return
   `READY_FOR_CONTROLLED_BINDING_REVIEW`, do not claim an exact
   reproduction of the ISO case.
8. After controlled qualification of furniture and power fields, click
   **Simulate & evaluate / Simuler et evaluer**.
9. Open the evidence browser and archive the evaluation JSON together
   with the corresponding APS file.

## Automated ISO checks

The centralised configuration verifies, among other things:

- geometry 8 m x 6 m x 2.7 m, two windows of 3 m x 2 m and volume 129.6 m3;
- lightweight and heavyweight variants from tables 23 and 24;
- glazing `U = 2.984 W/(m2.K)`, `g = 0.71` and zero re-reflection fraction;
- opaque solar absorptivity 0.6;
- continuous infiltration 0.41 vol/h, no mechanical ventilation;
- continuous sensible internal gain 200 W;
- air + furniture capacity 10 000 J/(m2.K);
- available heating and cooling capacities of 1 000 000 W;
- annual period and hourly outputs required for tables 28 to 34.

## Interpreting results

Tables 28 to 34 are integrated into the machine-readable catalogue
`config/iso52016_test1_verification_cases.json`. For each available result,
the report contains the ISO value, the APS value, the signed deviation, the
absolute deviation and the relative deviation.

The supplied ISO pages do not define an acceptance tolerance. The software must
therefore display `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION` rather
than a false PASS. A normative verdict can only be produced if a traceable,
official tolerance is provided at a later date.

## Method declarations -- annexes A.10 and B.10

The three choices in annex A.10 are currently declared **No** out of caution,
because the public IES documentation describes ApacheSim formulations that
differ from or are more general than the numbered methods 6.5.5.2, 6.5.6.3.1
and 6.5.7.1. This choice correctly triggers the validation cases of clause 7.2.
A written confirmation from the IES solver team could replace this declaration,
but only with an archived source.

## Remaining runtime blocker

The non-VE workstation cannot introspect native Boost.Python types. The report
produced by the **Probe Test 1 runtime inputs** button is therefore the
necessary evidence before implementing the setters:

- `furniture_mass_factor`;
- flags, units and values for heating/cooling capacities;
- values read back after assignment.

This guard prevents VE crashes already encountered when assigning enumerations
with an incompatible Python type.
