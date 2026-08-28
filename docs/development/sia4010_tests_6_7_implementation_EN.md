> **Note:** Translated from French original. See [sia4010_tests_6_7_implementation.md](sia4010_tests_6_7_implementation.md) for the source document.

# SIA 4010 - VE implementation plan for Tests 6 and 7

## Status and principle

This document translates the official local files into generator contracts. It does not constitute a certification. Any value not explicitly present in these sources remains either blocking or configurable with `source`, `unit`, `validation_range` and status `UNCONFIRMED`.

Main sources:

- `SIA_4010_geteilter_Link/Test6/Spezifikation_Test6.pdf`, PDF pages 1-5.
- `SIA_4010_geteilter_Link/Test6/Resultaterfassung_Test6.xlsx`, sheets `Daten Testprogramm` and `Zusammenfassung`.
- `SIA_4010_geteilter_Link/Test7/Spezifikation_Test7.pdf`, PDF pages 1-4.
- `SIA_4010_geteilter_Link/Test7/Lastverläufe_220607.xlsx`, sheet `Gruppen`.
- `SIA_4010_geteilter_Link/Test7/Resultaterfassung Test7.xlsx`, sheets `Daten Testprogramm` and `Zusammenfassung`.
- `SIA_4010_geteilter_Link/Test7/Schema.pdf`, PDF page 1; `PV_Layout.pdf`, PDF pages 1-2.
- `SIA_4010_geteilter_Link/Test7/datenblatt-asm605_201901_5bb_v1_de.pdf`, PDF page 2.
- `SIA_4010_geteilter_Link/Beispielgebäude/Dokumentation_Beispielgebäude_V5.pdf`, PDF pages 3-10, and associated IFC.

## Test 6 - model and geometry

| Parameter | Value to impose | Source |
|---|---:|---|
| Site / weather | Zürich-Kloten, SIA 2028 `DRY normal` | specification p.1 |
| Period | 01.01.2022-31.12.2022, hourly timestep | specification p.1; workbook 8760 values |
| Zone 001 | Restaurant, area 237.4 m2, IFC height 3.0 m | specification p.1; IFC `IFCSPACE 001` |
| Zone 002 | Kitchen, area 35.9 m2, IFC height 3.0 m | specification pp.2-3; IFC `IFCSPACE 002` |
| Footprint 001 | `(23.032,5.979),(19.742,5.979),(19.742,10.669),(3.792,10.669),(3.792,-2.470),(23.032,-2.470)` | IFC |
| Footprint 002 | rectangle `(29.642,10.669),(19.972,10.669),(19.972,6.959),(29.642,6.959)` | IFC |
| Other zones | do not simulate them; their shared walls are adiabatic | specification pp.1-3 |
| Envelope | exact constructions from the building documentation | documentation pp.6-9 |
| Infiltration | 0.15 m3/(h.m2), both zones | specification pp.1 and 3 |

The Test 6 specification takes precedence over the general documentation for usages: restaurant `6.2 Selbstbedienungsrestaurant` and kitchen `6.4 Küche zu Selbstbedienungsrestaurant`, per prSIA 2024:2021. The number of occupants, gains, schedules and simultaneity factors are not reproduced in the PDF: they must not be invented.

## Test 6 - ventilation and sequence

| Element | HVAC contract |
|---|---|
| Restaurant | supply 3000 m3/h, return 2650 m3/h at 100%; 350 m3/h overpressure towards kitchen |
| Kitchen | supply 3150 m3/h, extract 3500 m3/h at 100%; receives 350 m3/h from restaurant |
| Central unit | total airflow 6150 m3/h; level 1 = 2050 (33.3%), level 2 = 4100 (66.7%), level 3 = 6150 (100%) |
| Monday-Saturday schedule | 00:00-07:00=0; 07:00-08:00=0.333; 08:00-10:00=0.667; 10:00-12:00=1; 12:00-13:00=0.667; 13:00-16:00=0.333; 16:00-24:00=0 |
| Sunday | 0 all day |
| Nominal pressures | supply 750 Pa; extract 550 Pa |
| Fans | supply 2021 W at 1865 min-1; extract 1460 W at 1700 min-1; motors in airstream, after heat recovery |
| Ductwork | ducts and lengths from specification p.3; ductwork airtightness class D, central unit L1 |
| Heat recovery | water-glycol loop 30%, nominal thermal efficiency 0.71, 2100 l/h, pump 185 W |
| Heat recovery controls | pump speed modulated on supply setpoint; frost protection on exhaust air >= 5 C; minimum pump flow 50% |
| Supply setpoint | 20 C up to Text=12 C; interpolation to 18 C at Text=20 C; 18 C above |
| Cooling coil | 30 kW; heat exchange efficiency 0.7; air 26.3/22 C wet-bulb, 14.2 g/kg, 52% RH to 17 C; water inlet 13 C |
| Chilled water | 18 C up to Text=12 C; interpolation to 13 C at Text=20 C; 13 C above |
| Heating coil | 35 kW; air +2 to 19 C; water inlet 40 C |
| Hot water | 40 C up to Text=-8 C; interpolation to 20 C at Text=20 C; 20 C above |
| Restaurant heating | convectors active during ventilation; water curve 40 C at -8 C to 20 C at 20 C outdoor |
| Restaurant cooling | chilled ceiling active during ventilation; room setpoint based on 48 h sliding outdoor average, curves from p.2 |
| Kitchen | no heating/cooling emission; heating setpoint 21 C |

## Test 6 - outputs and acceptance

Export each hour: supply/extract airflow, total and separate fan power, heating/cooling coils (including latent/sensible), heat recovery heating/cooling, heat recovery auxiliary, supply/return/post-recovery temperatures and occupancy diagnostic. The 6 official annual bands are:

| Quantity | Low | Reference | High | kWh |
|---|---:|---:|---:|---|
| Fans | 3320.807 | 3853.655 | 4386.504 | kWh |
| Heating coil | 1397.590 | 1788.934 | 2180.278 | kWh |
| Total cooling coil | 2447.749 | 3619.145 | 4790.542 | kWh |
| Heat recovery heating | 27315.566 | 28311.310 | 29307.054 | kWh |
| Heat recovery cooling | -332.370 | -222.217 | -112.063 | kWh |
| Heat recovery auxiliary | 131.770 | 205.465 | 279.160 | kWh |

## Test 7 - inputs and energy chain

Test 7 can be run without regenerating the zones: strictly import the 8760 hourly values in W from `Lastverläufe_220607.xlsx`, sheet `Gruppen`, rows 6-8765.

| Column | Load |
|---|---|
| B | ceiling cooling T5+T6 |
| C/D/E | ventilation cooling T4/T5/T6 |
| F | domestic hot water heat at tank inlet, setpoint 60 C |
| G/H/I | ventilation heating T4/T5/T6 |
| J/K | ceiling heating T5 / convectors T6 |

Cooling distribution: losses 5% of absorbed heat; auxiliaries 2%; 50% of auxiliaries become cooling circuit load. Heating distribution: losses 5% of delivered heat; auxiliaries 2%; 50% recovered in the heating circuit. Hot and cold storage: water, 2000 l each; apply exactly the high/low commands described on p.1. The schematic on p.1 defines the connections, flow rates and temperature laws and must be treated as the graphical reference source.

Generator: Climaveneta NX-W-Y/H 0182, reversible water-to-water, two Scroll compressors/stages; 55.9 kW cooling and 60.0 kW heating (specification pp.2-3). Separate hot/cold modelling permitted. Implement the capacity/EER/COP tables from pages 2-3, including standby/thermostat/idle/crankcase heater consumption, bivalent temperature -7 C and cut-off -10 C; do not replace with a constant COP.

External circuit: dry cooler 70 kW in cooling, air heat exchanger 76 kW in heating, fan 0.045 kW/kW, water-glycol 30% to be confirmed, 19000 kg/h, delta T 4 K, air-to-leaving approach 4 K at full load; 50% of pump heat acts on the circuit; losses 5%. During simultaneous cooling with heating demand, charge the hot tank via the condenser. Below bivalence, gas backup boiler, efficiency 0.9 (specification p.4).

PV: AEG AS-M605-310 modules, inverter efficiency 97%. Roof 150 modules, 10 deg tilt, east/west; south facade 52 modules. The layout gives 46.5 + 16.12 = 62.62 kWp, while specification p.4 states 45 + 15.6 = 60.6 kWp: block the mutation until a precedence rule is approved. The exact east/west split is not quantified. The datasheet p.2 provides notably Pmax 310 W, Vmp 32.6 V, Imp 9.51 A, Voc 40.1 V, Isc 10.04 A, efficiency 19.1%, NOCT 45 C and Pmax coefficient -0.40%/K.

## Test 7 - official annual bands

| Quantity (kWh) | Low | Reference | High |
|---|---:|---:|---:|
| Chiller electricity | 3373.784 | 3928.779 | 4483.774 |
| Total rejected heat | 22468.020 | 23762.689 | 25057.357 |
| Cooling auxiliaries | 1088.723 | 2187.597 | 3286.470 |
| Cooling to heating side | 0 | 331.788 | 935.926 |
| Dry cooler heat | 27293.358 | 28122.460 | 28951.562 |
| Heat pump electricity | 8081.321 | 8727.624 | 9373.927 |
| Space heating | 7415.879 | 7847.662 | 8279.446 |
| Domestic hot water | 22871.194 | 23707.189 | 24543.183 |
| Boiler gas | 0 | 44.150 | 126.399 |
| Heating auxiliaries | 595.881 | 1228.061 | 1860.240 |
| PV production | 54069.923 | 56975.555 | 59881.188 |

## VE blockers and recommended API

- No controlled VE generator currently exists for `test_6/6` or `test_7/7`; the interface must remain `PREPARE_ONLY`.
- The package does not contain the SIA 2028 `DRY normal` Zürich-Kloten weather file: blocking requirement with checksum and 8760 check.
- The prSIA 2024:2021 values for usages 6.2/6.4 are missing: inject a source-traced parameter file, never arbitrary values.
- VEScripts can create/assign a simplified Apache system, but reliable creation of a complete ApacheHVAC network, hydraulic circuits, storage, cascaded recovery, bivalence and PV is not demonstrated. Plan either a signed VE/APHVAC template to clone and parameterise, or an independent hourly Python Test 7 solver whose results are audited.
- Hourly conversions must preserve signs, units and conventions: Test 6 exports W; Test 7 requires kWh per timestep in the workbook; perform an annual energy balance check before comparison.

Recommended API: `prepare(case, sources) -> PreflightReceipt`, `build_geometry(Test6GeometryConfig)`, `bind_official_usage(UsageDataset)`, `build_test6_airside(Test6AirsideConfig)`, `load_test7_profiles(ProfileWorkbookBinding)`, `build_test7_plant(Test7PlantConfig)`, `run_or_export()`, `extract_hourly(OutputBindingMap)`, `compare(OfficialBandSet)`. Each step must be idempotent, carry a `source_locator`/checksum, read back VE objects after mutation, and refuse any `PASS` claim if weather, usages, machine table, hydraulic network or PV remain unresolved.
