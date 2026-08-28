> **Note:** Translated from French original. See [sia4010_tests_4_5_implementation.md](sia4010_tests_4_5_implementation.md) for the source document.

# SIA 4010 Tests 4 and 5 - VE implementation contract

Status: fail-closed specification for `test_4`, `test_5A`, `test_5B`, `test_5C`, `test_5D` (2026-07-29).

## Official sources

| Source | Usage |
|---|---|
| `Test4/Spezifikation_Test4.pdf`, pp. 1-3 | room, gains, setpoints, AHU, heat exchanger, coils |
| `Test4/Resultaterfassung Test4.xlsx` | annual bands, hourly transfer, diagnostics |
| `Test5/Spezifikation_Test5.pdf`, pp. 1-5 | zones, ductwork, AHU, variants, criteria |
| `Test5/Resultaterfassung_Test5.xlsx` | annual bands and hourly distributions |
| `Beispielgebäude/Dokumentation_Beispielgebäude_V5.pdf`, pp. 4, 6-10 | floor plans, envelope, glazing, blinds, room assignments |
| `Beispielgebäude/IFC_Beispielebäude_201106_abstractBIM.ifc` | polygons, levels, volumes, adjacencies |
| `references/standards/SIA 380-2-2022 FR.pdf`, pp. 36-37 | Test 4 limit-value constructions |

User reports are diagnostic, never normative.

## Common inputs

| Parameter | Value |
|---|---|
| weather | SIA 2028 `DRY normal, Zürich Kloten` |
| period | Saturday 01.01.2022 to Saturday 31.12.2022, 8760 hours |
| infiltration | 0.15 m3/(h m2) |
| outdoor CO2 | 400 ppm |
| geometry | extracted from the IFC, north orientation and adjacencies preserved |
| unmodelled neighbours | explicit adiabatic surfaces |

`DRYCOLD_IESVE.epw` is forbidden here. The Test 5 workbook uses 2011, a non-leap year also starting on a Saturday: transfer by hour-of-year without modifying the 2022 timestamps used in the audit.

## Geometry

### Test 4

One zone, IFC room `101`, Hörsaal 4.4, windowless, spanning two storeys, exterior roof: 165.81 m2, height 6.38 m, volume 1058 m3 (IFC `#2343-#2349`; specification p. 1). No duplicates, no openings, no orphan surfaces.

### Test 5

Maintain eight separate zones, required for per-zone CO2 VAV:

| Room | Usage | Area m2 | Volume m3 |
|---|---|---:|---:|
| 100 | meeting room 3.3 | 31.62 | 95 |
| 102 | large office 3.2 | 104.94 | 315 |
| 200 | meeting room 3.3 | 31.62 | 95 |
| 201-204 | office 3.1, each | 17.14 | 51 |
| 205 | office 3.1 | 33.13 | 99 |

Total: 269.87 m2, 815 m3, height 3 m. Window dimensions from the IFC.
Envelope per documentation pp. 6-9: glazing Planitherm XN 4/14/4/14/4,
`Ug=0.654`, `g=0.545`, `tau_v=0.742`; frame 15%, `Uf=1.3`, absorptance 0.6;
no thermal bridges; external Soltis screen at 150 W/m2, `g_total=0.059`.

## Test 4 - HVAC parameters

Limit-value constructions per SIA 380/2 Table 3: wall/roof `U=0.20 W/(m2K)`;
create the layers from pp. 36-37 and verify the VE U-value. The PDF cites FprSIA:
log an edition-equivalence warning.

| Domain | Value |
|---|---|
| usage | Hörsaal SIA 2024:2021, target values |
| occupants | 55, 3 m2/person, 1.2 met, SIA 2024 profiles |
| equipment | 10 W/m2, SIA 2024 profiles |
| lighting | 6.4 W/m2, 07:00-18:00, off all July |
| airflow | 1700 m3/h, variable 20-100%, CO2 600-1000 ppm |
| schedule | weekdays 05:00-20:00, off July |
| supply/extract fans (ZUL/ABL) | 500/400 Pa; 407/331 W; 2790/2730 min-1 |
| location | exterior roof; motors in airstream; fans after heat recovery |
| heat recovery (WRG) | plate type without moisture, efficiency 0.75, bypass on setpoint |
| heat recovery summer/frost | 100% bypass in cooling; bypass for exhaust air >=0 C |
| supply air | local PI; cooling 16-22.5 C; heating 22.5-29 C |
| cooling coil | 12.8 kW; efficiency 0.85; bypass 0.065; water 13 C |
| cooling air state | inlet 29.5 C/22 C wet-bulb/14.2 g/kg/52%; outlet 16 C |
| heating coil | 11.4 kW; air 8->29 C; design water 31 C, operating 40 C |

Setpoints based on 48 h sliding outdoor average (p. 2): heating 22 C up to 19 C, ramp to 23.5 C at 23.5 C; cooling 23 C up to 12 C, ramp to 25 C at 17 C.

## Test 5 - common parameters

Usages, gains, schedules and simultaneity factors: SIA 2024:2021 standard values per zone. Fresh air 25 m3/h/person. Heated/cooled ceiling panels active per ventilation schedule; their energy is not a Test 5 criterion.
Temperature setpoints identical to Test 4; CO2 950-1200 ppm; minimum humidification 30% RH.

| AHU/controls | Value |
|---|---|
| system | multi-zone, per-zone CO2 VAV, AHU in U102 unconditioned |
| airflow | 1040 m3/h, 30-100%, weekdays 06:00-19:00 |
| supply/extract fans (ZUL/ABL) | 770/520 Pa; 420/290 W; 3000/2500 min-1 |
| controls | VFD on differential pressure; motors in airstream; after heat recovery |
| supply air | 20 C if Text<=12; ramp to 18 C if Text=20; then 18 C |
| heat recovery (WRG) | rotary, 20 min-1, auxiliary 120 W, speed modulated |
| heat recovery summer | stopped if Text > supply setpoint; no cooling recovery |
| cooling coil | 8.6 kW; efficiency 0.765; bypass 0.065; air 29.5->17 C |
| chilled water | 18 C if Text<=12, ramp to 13 C at Text=20, min. 10 C for RH<=60% |
| heating coil | 3.5 kW; air 10.5->19 C |
| hot water | 40 C if Text<=-10, ramp to 18 C at Text=20, then 18 C |

Ductwork (p. 2): 14 m of 0.3x0.3 m + 5 m of 0.3x0.15 m, `U=0.6`;
20 m of 0.3x0.15 m, `U=1.1`; 24 m diameter 0.125 m + 40 m diameter 0.10 m,
`U=1.1`. Duct ambient: 15 C Oct-Mar, 28 C Apr-Sep. Ductwork airtightness class B,
AHU L1.

## Test 5 variants

| Case | Constant pressure supply+extract | Rotor (sensible/latent) | Humidifier |
|---|---:|---|---|
| 5A | 50+50 Pa | hygroscopic 0.67/0.42 | wetted media |
| 5B | 270+270 Pa | hygroscopic 0.67/0.42 | wetted media |
| 5C | 270+270 Pa | non-hygroscopic 0.69/0.30 | wetted media |
| 5D | 270+270 Pa | non-hygroscopic 0.69/0.30 | electric steam |

Rotor per EN 16798-5-1 Annex D. Wetted media 5A-C: 4.9 kg/h, pump
0.01 Wh/m3, modulated valve, pump active with ventilation and demand.
Steam 5D: 4.9 kg/h, electrical energy.

## Official criteria

Test 4, annual bands kWh: fans `688.458-970.500`; heater
`2442.426-3252.073`; total cooler `1287.652-1400.008`. The AA-AR hourly
series in the workbook are transfers/diagnostics, not a confirmed standalone
histogram criterion.

Test 5, annual bands kWh:

- 5A: fans 426.029-592.790; heating 537.583-1239.733; cooling 521.404-1483.122.
- 5B: fans 590.778-739.407; heating 535.613-1159.517; cooling
  533.047-1494.639; total heat recovery 4481.814-4911.595; latent 301.952-965.774.
- 5C: heating 607.035-1097.952; total cooling 569.513-1424.518; latent 0-281.557;
  total heat recovery 4161.449-4693.191; latent 30.863-169.113; auxiliary 215.935-329.031.
- 5D: heating 314.395-888.059; humidification 137.757-329.786.

Mandatory histograms: 5A fans/heating/cooling; 5B heating/cooling/total heat
recovery/latent; 5C airflow, fans, heating, total/latent cooling, total/latent
heat recovery, heat recovery auxiliary; 5D heating. Each bin must remain within
the official band. No official bin for steam power: do not invent one.

## API, workflow and blockers

Recommended API: `Sia4010Test45ScenarioFactory.create_test4/create_test5`,
immutable contracts `IfcRoomSelection`, `QualifiedFanCurve`, `DuctSegmentInput`,
`HeatRecoveryInput`, `CoilInput`; adapters `VeApacheHvacCapabilityProbe`,
`VeApacheHvacAdapter.provision/verify_readback`,
`Sia4010Test45ApsExtractor`, `OfficialWorkbookExporter.export_copy`.

Workflow: verify sources/checksums -> parse IFC -> validate geometry ->
probe VE without mutation -> create envelope/templates -> create HVAC ductwork ->
full read-back -> qualified weather -> 8760 h -> qualify APS
identity/unit/sign -> annual bands -> Test 5 histograms -> JSON/CSV and
workbook copy. One disposable project per variant, fingerprint mandatory.

Explicit blockers: SIA 2024 profiles missing; DRY-normal weather file missing;
EN 16798-5-1 Annex D missing; fan curves available only as graphs;
detailed ApacheHVAC creation/read-back not proven; per-zone CO2 VAV, duct
losses, latent heat recovery/coil and humidifier power APS to be qualified. Any
absence yields `NOT_CHECKABLE` or blocks the mutation, never `PASS`.
