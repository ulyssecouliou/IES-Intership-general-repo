# Swiss Compliance Workbench — Presentation Outline

## Slide 1 — Product outcome

**IESVE-native Swiss compliance automation**

- SIA 380/2 client-model pre-check
- SIA 4010 software verification laboratory
- reproducible, source-traced and fail-closed
- runs from VEScripts; no external terminal required

## Slide 2 — Why this product is needed

- Compliance inputs are distributed across VE objects, weather, simulation output
  and project evidence.
- Missing data must not be replaced by invented defaults.
- Manual review is slow and difficult to reproduce.
- A client needs findings, provenance and next actions in one auditable workflow.

## Slide 3 — End-to-end architecture

```text
Client VE model
    -> read-only extraction
    -> SIA 380/2 controls
    -> evidence review
    -> JSON / text / Excel-ready report

Official SIA 4010 files
    -> checksum verification
    -> 34 exact case contracts
    -> guarded VE model / template route
    -> ApacheSim
    -> qualified APS extraction
    -> official comparison
    -> evidence dashboard
```

## Slide 4 — Live client model audit

Model: `ZOER_32_C1_TEST`

- 4 rooms
- 81 significant external surfaces checked
- 150 windows checked
- profiles and APS inspected
- actionable ventilation, lighting, output and weather-evidence warnings
- zero model mutation

## Slide 5 — SIA 4010 verification laboratory

- 8 validation classes
- 34 exact cases catalogued
- official files and checksums bound to each case
- exact scenario and feature locking
- guarded model, simulation, APS and result gates
- no acceptance criterion is invented

## Slide 6 — Working reference execution

Model: `Test_640_Test1`

- exact Test 1 case
- model audit without failing controls
- annual ApacheSim result available
- APS linked to the active scenario
- 88 metrics extracted
- official reference results recorded

Status is deliberately not presented as PASS because no official acceptance band
is available for that result table.

## Slide 7 — Current MVP maturity

| Capability | Current state |
| --- | --- |
| Client-model read-only audit | Demo-ready |
| Evidence capture | Implemented, fail-closed |
| Auditable report generation | Implemented |
| Official case/source registry | 34/34 exact cases |
| Verified guarded VE generator | 1 case |
| Runtime qualification routes | 9 cases |
| Test 1 model-to-APS chain | Executed |
| Checksum-valid complete case evidence | 2/34 cases |
| Full 34-case official validation | Not complete |

## Slide 8 — Remaining bounded work

- Test 2: solar-protection control and output binding
- Test 3: lighting/daylight control binding
- Tests 4–6: HVAC topology and multizone sequences
- Test 7: plant and energy-system binding
- review/encode official acceptance gates where not explicit
- complete regression pack across supported VE versions

## Slide 9 — Closing message

**The MVP workflow is operational; the remaining risk is concentrated in known,
case-specific VE bindings and official acceptance evidence.**

Next milestone: convert the qualified routes into repeatable case generators and
close the evidence gates one validation class at a time.
