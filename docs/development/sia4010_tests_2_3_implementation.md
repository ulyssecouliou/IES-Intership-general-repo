# SIA 4010 Tests 2 and 3 - VE implementation contract

Status: implementation specification, fail-closed where normative inputs are unavailable  
Scope: official SIA 4010 Test 2 variants 2A-2D and Test 3 variants 3A-3L  
Target runtime: IESVE / VEScripts / ApacheSim  
Date of review: 2026-07-29

## 1. Executive decision

The official local package is sufficient to define:

- the common one-zone geometry;
- the Test 2/3 climate identity and simulation calendar;
- the thermal and optical glazing inputs;
- the fabric-awning properties;
- the slat optical values at the specified reference position;
- all Test 2 and Test 3 variant combinations;
- the required annual and hourly outputs;
- the official annual acceptance bands;
- the frequency-distribution bins and comparison rule.

It is **not sufficient for an exact autonomous VE implementation** because the
following normative data are referenced but not included:

1. SIA 387/4:2017 table 9 (or the applicable 2023 equivalent): exact solar
   protection control functions 1, 2 and 3.
2. SIA 387/4 table 10: exact lighting-control functions 1 to 6.
3. SIA 2024:2021 category 3.1: hourly schedules and annual simultaneity profiles
   for occupancy, equipment and lighting.
4. The controlled SIA 2028 `DRY normal, Zürich Kloten` weather dataset.

Accordingly, the interface may prepare all 16 scenarios, but `CREATE_IN_ACTIVE_VE_PROJECT`
must remain blocked unless those four source-qualified assets are available and
the relevant VE controls have passed read-back verification.

## 2. Source register

| Source | Scope used | SHA-256 |
|---|---|---|
| `SIA_4010_geteilter_Link/Test2/Spezifikation_Test2.pdf` | Test 2 model, cases and outputs, pp. 1-2 | `3E89BE97B4771D0B5A146BAF7E53926BF528948F78159EDE7AFA8F01963E0608` |
| `SIA_4010_geteilter_Link/Test2/Resultaterfassung_Test2.xlsx` | official annual bands, hourly transfer schema, histogram bins | `0D34793B0A193E0FAC52918A359AC50809046FE7BB56DBAB4412ED42332D4D1E` |
| `SIA_4010_geteilter_Link/Test3/Spezifikation_Test3.pdf` | Test 3 model, cases and outputs, pp. 1-3 | `012BBFAC77D636A2447D046712401CC482455A5C0550A443E3A9CAF5BA7DF3A3` |
| `SIA_4010_geteilter_Link/Test3/Resultaterfassung_Test3.xlsx` | official annual bands, hourly transfer schema, histogram bins | `36410DE9039680C1AAF277C118B66F5410029B910F7969CBB0756E70F1E5EEE9` |
| `references/standards/SIA 4010-2023 FR.pdf` | validation classes and combinations, pp. 46-52, especially tables 63 and 65 | `C613DA0F8A40C19ABC15BB07DA9422BF19D2453FDAA1E9F8A043B2814F598421` |
| `SIA_4010_geteilter_Link/Beispielgebäude/Dokumentation_Beispielgebäude_V5.pdf` | fabric awning/glazing data, pp. 7-9 | `38D231786467B1A117C99F2CFE8D09DD03C921BB894378A061C2F6D9BC14C75D` |

The reference-program user reports are useful diagnostic evidence only. They
must not override the official specifications or the SIA standard.

## 3. Common deterministic model

### 3.1 Geometry

Tests 2 and 3 reuse the ISO EN 52016 / ASHRAE 140 test cell, south facing.
The existing `Sia4010CellGeometryGenerator` can be reused.

| Parameter | Value | Unit | Source |
|---|---:|---|---|
| internal width (east-west) | 8.0 | m | source-traced case manifest / Test 1-2 cell |
| internal depth (north-south) | 6.0 | m | same |
| internal height | 2.7 | m | same |
| net floor area | 48.0 | m2 | Test 2 p. 1; Test 3 p. 1 |
| thermal zones | 1 | count | specifications |
| south windows | 2 | count | test-cell definition |
| each window width | 3.0 | m | test-cell definition |
| each window height | 2.0 | m | test-cell definition |
| sill height | 0.2 | m | test-cell definition |
| side margins | 0.5 | m | test-cell definition |
| centre opaque gap | 1.0 | m | test-cell definition |
| south facade | `y = 0` | coordinate contract | existing generator |
| construction type | lightweight | - | Test 2 p. 1; Test 3 p. 1 |

Geometry acceptance checks:

- exactly one closed room and six boundary surfaces;
- floor area `48.0 m2`, volume `129.6 m3`;
- exactly two openings, each `6.0 m2`, both on the south facade;
- no overlap and no unassigned surface/opening;
- fixed north axis and source coordinate system;
- no fixed geometric shade: dynamic protection belongs to the opening system.

The opaque lightweight construction remains inherited from ISO EN 52016:2017
chapter 7. The repository currently uses the public BESTEST lightweight source
as a qualified public reference, but its exact identity with ISO EN 52016
chapter 7 must remain an audit warning until confirmed.

### 3.2 Calendar and weather

| Parameter | Required value |
|---|---|
| location | Zürich Kloten |
| climate | SIA 2028 `DRY normal, Zürich Kloten` |
| period | Saturday 2022-01-01 through Saturday 2022-12-31 |
| hourly records | exactly 8760 |
| workbook convention | end-of-hour labels, `01/01 01:00:00` through year end |

Do not substitute the Denver `DRYCOLD_IESVE.epw` used by Test 1. A converted
weather file is acceptable only when the original SIA 2028 dataset, conversion
method, calendar, radiation components, timezone, station coordinates and
checksum are recorded. The reference reports identify vertical irradiation and
albedo treatment as materially sensitive.

### 3.3 Envelope and glazing

| Property | Required value | Unit |
|---|---:|---|
| product | SGG Planitherm XN 4/14/4/14/4 | - |
| layer sequence | 4 mm glass / 14 mm 90% argon-10% air / 4 mm glass / 14 mm gas / 4 mm glass | - |
| glazing `g` | 0.545 | - |
| `Ug` | 0.654 | W/(m2 K) |
| visible transmittance `tau_v` | 0.742 | - |
| visible reflectance `rho_v` | 0.145 | - |

Tests 2/3 concern solar protection and lighting. Nevertheless, the glazing
thermal/solar/visible properties must all be represented and verified
separately. VE rounding must be handled by a source-specific canonicalization
rule, never a generic relaxed tolerance.

### 3.4 Use, gains and ideal loads

| Parameter | Required value | Unit | Source |
|---|---:|---|---|
| use category | SIA 2024:2021 `3.1 Einzel-Gruppenbüro` | - | Test 2/3 p. 1 |
| people | 3.43 (14 m2/person) | persons | Test 2/3 p. 1 |
| activity | 1.2 | met | Test 2/3 p. 1 |
| equipment gain | 11.0 | W/m2 | Test 2/3 p. 1 |
| lighting installed power / gain | 12.5 | W/m2 | Test 2 p. 2; Test 3 p. 1 |
| infiltration, Test 2 | 0.15 | m3/(h m2), facade-area basis | Test 2 p. 1 |
| infiltration, Test 3 | specification prints `-` | - | Test 3 p. 1 |
| heating | ideal, 20 C room setpoint | - | Test 2/3 p. 1 |
| cooling | ideal, 27 C room setpoint | - | Test 2/3 p. 1 |
| HVAC plant | none | - | Test 2/3 |

The dash for Test 3 infiltration must not be silently converted to the Test 2
value. The implementation contract should encode it as an explicit
`NONE/0` decision with the source locator and verify the room read-back.

People, equipment and lighting use the SIA 2024:2021 schedules and annual
simultaneity. Exact profiles are a blocker until a controlled copy is available.
For Test 3 lighting, the specification explicitly states annual simultaneity
`0.8` for January-December. The updated Excel reference report confirms that
the reference programs retained this constant `0.8` reduction. That report is
diagnostic evidence; the specification remains the controlling source.

## 4. Solar-protection systems

### 4.1 Activation

All protection systems are external. Activation threshold:

```text
incident total solar irradiance on exterior window plane >= 150 W/m2
```

The threshold signal, comparison convention at equality, release hysteresis
and timestep state handling must come from the applicable normative control
definition. They must not be guessed.

### 4.2 Fabric awning (Test 2A; Test 3A-3F)

Product: `Soltis 92-2048-Alu`, external fabric screen.

| Combined glazing + shade property | Value |
|---|---:|
| summer `g_total` | 0.059 |
| direct solar transmittance | 0.040 |
| outside solar reflectance | 0.490 |
| inside solar reflectance | 0.456 |
| visible transmittance | 0.058 |
| outside visible reflectance | 0.496 |
| inside visible reflectance | 0.395 |

Example-building documentation also records 1 cm gaps at top, sides and bottom.
SIA 4010 section 3.1.5 permits the simpler combined-`g_total` substitution for
fabric screens when activated. The generator must record whether it uses:

- a detailed external layer/cavity representation, or
- the permitted two-state combined glazing construction.

Both modes require an explicit read-back and an output-equivalence check.

### 4.3 Metal slats (Tests 2B-2D; Test 3G-3L subject to source issue below)

Product: `Slat Metal B (WIN7)`.

| Optical property at 45-degree working position / 45-degree sun altitude | Value |
|---|---:|
| visible transmittance | 0.00 |
| visible beam transmittance | 0.07 |
| visible diffuse transmittance | 0.39 |
| visible reflectance | 0.50 |
| visible beam reflectance | 0.36 |
| visible diffuse reflectance | 0.21 |

These values do not define the complete angular optical model. An exact
implementation also needs slat width, spacing, distance to glazing, orientation,
angle sign convention, angle limits, solar properties and the three control
functions. If VE cannot represent them natively, a per-timestep EMS-like
controller or an equivalent scheduled-state implementation is required.

### 4.4 Fixed-angle diagnostic cases

Test 2 diagnostic cases are essential qualification hooks:

| Case | Protection state |
|---|---|
| 2E1 | fabric awning always closed |
| 2E2 | slats always closed at -45 degrees |
| 2E3 | slats always closed at 0 degrees |
| 2E4 | slats always closed at +45 degrees |
| 2E5 | slats always closed at 90 degrees |

They are not validation-class variants but should be implemented before
claiming the dynamic 2B-2D controls are qualified. They isolate angular
optics from control logic.

## 5. Test 2 variant contract

| Variant | Protection | Control |
|---|---|---|
| 2A | external Soltis fabric awning | irradiation threshold, no sun-position slat regulation |
| 2B | external Slat Metal B | SIA 387/4 table 9 function 1 |
| 2C | external Slat Metal B | SIA 387/4 table 9 function 2 |
| 2D | external Slat Metal B | SIA 387/4 table 9 function 3 |

Test 2 classes:

- validation class 1A requires Test 1 + 2A;
- validation class 1B requires Test 1 + 2A-2D (the standard abbreviates this
  as Tests 1 and 2).

### 5.1 Obligatory hourly result contract

At least one of these two physical alternatives is required for each case:

1. total room solar heat gain, including secondary gains, in W; or
2. total transmitted solar radiation, excluding secondary gains, in W.

The candidate must use the same alternative consistently for the annual band
and hourly comparison. Recommended VE path: total room solar heat gain, because
the current APS qualification work already targets that quantity.

Mandatory comparison rule:

- annual sum in kWh must lie inside the official lower/upper band;
- hourly frequency distribution must lie within the scatter band of the
  reference programs.

The repository intentionally registers the histogram criterion only for
`Solarer Wärmeeintrag gesamt`, because the workbook does not define a dedicated
bin column for total transmitted solar radiation. Therefore an autonomous
pass should currently require the total-solar-heat-gain path.

### 5.2 Official annual bands

| Case | Solar heat gain mean | lower | upper | Transmitted radiation mean | lower | upper | Unit |
|---|---:|---:|---:|---:|---:|---:|---|
| 2A | 1048.9221 | 895.5315 | 1202.3127 | 914.5974 | 836.3697 | 992.8251 | kWh |
| 2B | 1522.8049 | 1167.2920 | 1878.3178 | 1275.4248 | 1088.2345 | 1462.6152 | kWh |
| 2C | 1571.8077 | 1228.9588 | 1914.6566 | 1317.8821 | 1143.7475 | 1492.0166 | kWh |
| 2D | 1938.0460 | 1723.0860 | 2153.0060 | 1625.9053 | 1565.1485 | 1686.6622 | kWh |

Source locators are `Zusammenfassung!N14:N17` for solar heat gain and
`Zusammenfassung!AA14:AA17` for transmitted radiation (the parser records the
upper-bound column as the locator).

### 5.3 Test 2 workbook transfer map

Sheet: `Daten_Testprogramm`; timestamps and data occupy rows 5-8764.

| Quantity/case | Columns |
|---|---|
| date/time | X |
| total/direct/diffuse irradiation on window plane | Y/Z/AA |
| 2A: total, direct, diffuse, secondary solar gain; transmitted radiation | AC/AD/AE/AF/AG |
| 2B: total, direct, diffuse, secondary gain; slat angle; transmitted radiation | AI/AJ/AK/AL/AM/AN |
| 2C: same sequence | AP/AQ/AR/AS/AT/AU |
| 2D: same sequence | AW/AX/AY/AZ/BA/BB |
| 2E1: total, direct, diffuse, secondary solar gain; transmitted radiation | BD/BE/BF/BG/BH |

The 2E1 candidate schema is checksum- and header-qualified by
`test2a_diagnostic_workbook.py`: timestamps are `X5:X8764`, the three common
irradiation series are `Y5:AA8764`, and the five fixed-closed fabric-awning
outputs are `BD5:BH8764`. Reference `Daten_*` sheets use rows 4-8763 and mark
the same diagnostic with `BC2 = "2 E1"`. This closes the transfer-schema
binding only; it does not qualify the VE fixed-closed optical representation or
the dynamic 2A control.

The workbook provides diagnostic charts, not a 2E1 acceptance rule. The
implementation therefore reads the six available annual total-gain references,
the seven transmitted-radiation references and the six-program total-gain
histogram scatter. It reports technical alignment only. Even a candidate inside
every derived reference envelope remains
`REFERENCE_DIAGNOSTIC_RECORDED_NO_ACCEPTANCE_CRITERION`, with no compliance
PASS and no automatic optical-mapping qualification.

The current runtime-qualified APS contract covers exactly one of these eight
series: zone-level `Window solar gains` for
`hourly_room_solar_heat_gain_total`. The other seven series remain explicitly
unbound. `test2a_diagnostic_aps.py` refuses token-based substitution and
requires checksummed simulation evidence for the exact fixed-closed
`SIA4010_TEST_2A_2E1` scenario. The interface APS probe can now read
surface-level candidates through exact VE `room_id` and `aps_handle`
identities; those candidates still require physical review before a binding
may be added.

Diagnostic blocks 2E2-2E5 remain implementation and qualification hooks for
the fixed-angle slat cases.

Histogram upper edges for total solar heat gain (`Haeufigkeitsklassen!C4:C23`,
W):

```text
10, 100, 150, 200, 250, 300, 350, 400, 450, 500,
550, 600, 650, 700, 750, 800, 850, 900, 950, 1000
```

Counts include the overflow bin as implemented by `distribution_reference.py`.

## 6. Test 3 lighting model

### 6.1 Room and sensor inputs

| Parameter | Value | Unit |
|---|---:|---|
| ceiling/wall/floor visible reflectance | 0.7 / 0.5 / 0.2 | - |
| sensor x, room centre | 4.0 | m |
| sensor y, room depth | 2.7 | m |
| working-plane height | 0.75 | m |
| daylight penetration depth | 5.4 (2 x room height) | m |
| daylight-controlled area | 43.2 (5.4 x 8.0) | m2 |
| constant/time-scheduled area | 4.8 (0.6 x 8.0) | m2 |
| maintained illuminance setpoint `E_vm` | 500 | lux |
| switching hysteresis `Delta E_vm` | 250 | lux |
| presence correction `k_Pr` | 1.0 | - |
| installed lighting power | 12.5 | W/m2 |
| annual lighting simultaneity | 0.8, Jan-Dec | - |

The sensor coordinate description in the source labels both room-centre and
table-height lines with `(x)`; the machine contract should encode the intended
3D point as `(4.0, 2.7, 0.75)` and keep a source-note about the typographical
label.

Exact control curves, switching states, delay/hysteresis behaviour, presence
interaction and efficacy/room-utilization calculation for control types 1-6
must be transcribed from SIA 387/4 table 10 and its referenced clauses. They
must not be inferred from the annual reference values.

### 6.2 Exact Test 3 combinations

Table 65 of SIA 4010 and Test 3 pp. 2-3 define:

| Variant | Solar protection source | Shading control | Lighting control |
|---|---|---:|---:|
| 3A | 2A fabric | threshold/fabric | 1 |
| 3B | 2A fabric | threshold/fabric | 2 |
| 3C | 2A fabric | threshold/fabric | 3 |
| 3D | 2A fabric | threshold/fabric | 4 |
| 3E | 2A fabric | threshold/fabric | 5 |
| 3F | 2A fabric | threshold/fabric | 6 |
| 3G | 2B slats | 1 | 1 |
| 3H | 2B slats | 1 | 3 |
| 3I | 2C slats | 2 | 1 |
| 3J | 2C slats | 2 | 3 |
| 3K | 2D slats | 3 | 1 |
| 3L | 2D slats | 3 | 3 |

Source inconsistency to resolve:

- SIA 4010 table 65 maps 3K/3L to Test 2D, which Test 2 defines as metal slats.
- Test 3 p. 2 says `3G bis 3J` are slats, omitting K/L.
- the Excel and EnergyPlus user reports describe 3K/L as fabric-awning cases.

The normative matrix and Test 2 specification support the slat interpretation,
but autonomous creation of 3K/L must remain blocked until the current SIA FAQ
or SIA validation authority confirms the intended device. User reports are not
normative evidence.

### 6.3 Obligatory results and acceptance

Scored result for every variant:

- total whole-room lighting power, hourly, in kW/W as indicated by the target
  field; annual energy in kWh.

Both criteria are mandatory:

- annual lighting-energy sum within the official lower/upper band;
- hourly lighting-power frequency distribution within the reference-program
  scatter band.

Diagnostic results:

- daylight luminous flux through the window for groups A-F, G-H, I-J and K-L;
- work-plane illuminance at the controlled-area centre for all cases;
- lighting control signal for all cases.

Diagnostics must be retained in the machine audit even though they are not
scored as validation criteria.

### 6.4 Official Test 3 annual bands

| Case | Mean | Lower | Upper | Unit |
|---|---:|---:|---:|---|
| 3A | 665.4158 | 652.6036 | 678.2281 | kWh |
| 3B | 1008.1858 | 982.7040 | 1033.6676 | kWh |
| 3C | 806.1356 | 795.8950 | 816.3763 | kWh |
| 3D | 1091.9401 | 1081.6320 | 1102.2483 | kWh |
| 3E | 1155.4712 | 1131.4168 | 1179.5256 | kWh |
| 3F | 1184.2370 | 1150.8190 | 1217.6551 | kWh |
| 3G | 446.8306 | 355.4851 | 538.1762 | kWh |
| 3H | 631.7467 | 558.3924 | 705.1010 | kWh |
| 3I | 430.4980 | 339.4050 | 521.5911 | kWh |
| 3J | 618.7742 | 545.7156 | 691.8329 | kWh |
| 3K | 404.9608 | 373.2540 | 436.6677 | kWh |
| 3L | 598.3066 | 572.7190 | 623.8941 | kWh |

Source locators: `Resultaterfassung_Test3.xlsx`,
`Zusammenfassung!P11:P16`, `P18:P19`, `P21:P22`, `P24:P25`.

### 6.5 Test 3 workbook transfer map

Sheet: `Daten_Testprogramm`; rows 5-8764 hold exactly 8760 hours.

| Cases | Shared diagnostics | Per-case control/power columns |
|---|---|---|
| 3A-3F | daylight flux V; illuminance W | 3A Y/Z, 3B AB/AC, 3C AE/AF, 3D AH/AI, 3E AK/AL, 3F AN/AO |
| 3G-3H | daylight flux AQ; illuminance AR | 3G AT/AU, 3H AW/AX |
| 3I-3J | daylight flux AZ; illuminance BA | 3I BC/BD, 3J BF/BG |
| 3K-3L | daylight flux BI; illuminance BJ | 3K BL/BM, 3L BO/BP |

In every per-case pair, the first column is the lighting-control signal and the
second is total lighting power in W. Timestamp is column T.

Histogram upper edges for scored lighting power
(`Haeufigkeitsklassen!B4:B23`, W):

```text
25, 50, 75, 100, 125, 150, 175, 200, 225, 250,
275, 300, 325, 350, 375, 400, 425, 450, 475, 500
```

Illuminance bins exist in column C, but illuminance is diagnostic and must not
be treated as a scored criterion.

## 7. Proposed generator API

Use immutable, source-traced contracts. One disposable VE project represents
one exact variant.

```python
@dataclass(frozen=True)
class TestCellInput:
    geometry: CellGeometryInput
    envelope: LightweightEnvelopeInput
    glazing: GlazingInput
    weather: QualifiedWeatherInput
    usage: QualifiedSia2024OfficeInput
    ideal_loads: IdealLoadInput

@dataclass(frozen=True)
class SolarProtectionInput:
    device: Literal["FABRIC", "METAL_SLAT"]
    activation_w_m2: float
    optical_model: QualifiedOpticalModel
    control_function: Literal["FABRIC_THRESHOLD", "SIA3874_T9_1",
                              "SIA3874_T9_2", "SIA3874_T9_3"]
    diagnostic_fixed_angle_deg: float | None = None

@dataclass(frozen=True)
class LightingControlInput:
    control_type: Literal[1, 2, 3, 4, 5, 6]
    sensor_xyz_m: tuple[float, float, float]
    setpoint_lux: float
    hysteresis_lux: float
    controlled_area_m2: float
    scheduled_area_m2: float
    annual_simultaneity: float
    normative_definition: SourceTracedControlDefinition

@dataclass(frozen=True)
class OfficialScenario:
    family: Literal["2", "3"]
    variant: str
    cell: TestCellInput
    shading: SolarProtectionInput
    lighting: LightingControlInput | None
    output_contract: HourlyOutputContract
```

Required services:

```python
class Sia4010Test23ScenarioFactory:
    def create_test2(self, variant: Literal["2A", "2B", "2C", "2D"]) -> OfficialScenario: ...
    def create_test3(self, variant: Literal["3A", ..., "3L"]) -> OfficialScenario: ...

class VeSolarProtectionAdapter:
    def capabilities(self) -> SolarProtectionCapabilities: ...
    def provision(self, scenario: OfficialScenario) -> ProvisioningReceipt: ...
    def verify_readback(self, receipt: ProvisioningReceipt) -> ValidationResult: ...

class VeLightingControlAdapter:
    def capabilities(self) -> LightingControlCapabilities: ...
    def provision(self, scenario: OfficialScenario) -> ProvisioningReceipt: ...
    def verify_readback(self, receipt: ProvisioningReceipt) -> ValidationResult: ...

class Sia4010HourlyResultExtractor:
    def extract_test2(self, aps_file: Path, case: str) -> Test2HourlyResult: ...
    def extract_test3(self, aps_file: Path, case: str) -> Test3HourlyResult: ...

class Sia4010OfficialWorkbookExporter:
    def build_transfer_payload(self, result: Test2HourlyResult | Test3HourlyResult) -> Mapping[str, Sequence[float]]: ...
```

Do not automate direct writes into the immutable official workbook. Generate a
transfer payload plus a copied output workbook, preserving source checksum and
all formulas.

## 8. Guarded VE workflow

For each selected variant:

1. Resolve exact sources and checksums.
2. Fail preflight if weather, SIA 2024 profiles or required SIA 387/4 control
   definitions are missing.
3. Probe VE capabilities without mutation:
   - dynamic external shading;
   - angle/state control at hourly or finer resolution;
   - solar direct/diffuse/secondary result access;
   - daylight sensor at explicit coordinates;
   - lighting signal and whole-room power result access.
4. Generate and validate common geometry.
5. Provision/reuse source-qualified materials and constructions.
6. Provision independent templates for the selected exact variant.
7. Import geometry once.
8. Assign and read back envelope, glazing, schedules, protection and lighting.
9. Run Test 2E fixed-angle diagnostics for a new slat adapter.
10. Simulate 8760 hours with the qualified Zürich-Kloten weather.
11. Extract APS values with identity, unit, sign and timestep qualification.
12. Compare annual bands.
13. Compare every hourly histogram bin.
14. Export diagnostics and copied workbook transfer.
15. Permit `OFFICIAL_RESULTS_RECORDED` only if every mandatory criterion passes
    and no required input remains provisional.

Idempotency:

- detect a deterministic scenario fingerprint in the active project;
- reuse only objects whose full read-back matches;
- otherwise fail and require a new disposable project;
- never repair a different scenario in place.

## 9. Explicit VE blockers and required probes

| Blocker | Required evidence before implementation can pass |
|---|---|
| exact SIA 387/4 shading functions unavailable | controlled table 9 transcription with equation/state tests |
| exact SIA 387/4 lighting functions unavailable | controlled table 10 transcription and 6 golden control-series tests |
| SIA 2024 schedules unavailable | 8760-value profile set or fully specified schedule generator with checksum |
| Zürich-Kloten weather unavailable | original file or controlled conversion plus 8760-hour radiation verification |
| slat angular solar properties incomplete | full device optical dataset or validated VE library construction |
| dynamic slat angle assignment through VE API unproven | capability probe and read-back at -45/0/45/90 degrees |
| total room solar heat gain APS identity not fully qualified | diagnostic comparison against Test 2 workbook/program band |
| daylight sensor/control API unproven | coordinate, lux signal, control signal and lighting power read-back |
| 3K/3L protection-device inconsistency | current SIA FAQ or written SIA validation-authority decision |
| Test 3 infiltration dash ambiguous | explicit source decision and room air-exchange read-back |

## 10. Recommended implementation order

1. Add the missing controlled inputs to the configuration layer; keep values
   `null` with `PLACEHOLDER_REQUIRED` until sourced.
2. Implement Test 2A using the permitted two-state fabric `g_total` method.
3. Qualify APS total room solar heat gain and pass 2A annual + distribution.
4. Implement Test 2E1-2E5 fixed-state diagnostics.
5. Implement Test 2B-2D only after the table 9 functions and slat API are proven.
6. Implement the common Test 3 sensor/lighting result adapter.
7. Implement 3A-3F after all six table 10 control definitions are encoded.
8. Reuse qualified 2B-2D controls for 3G-3L after resolving the 3K/3L source
   inconsistency.
9. Add copied-workbook export and a machine-readable audit package.

This sequence reaches useful class coverage early: Test 2A completes the
solar-protection component of classes 1A, 2A and 4A; Tests 3A-3F then complete
their lighting-control component. Slat-dependent B classes remain fail-closed
until the normative and VE angular-control blockers are resolved.
