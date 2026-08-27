# SIA 4010 - consolidated pending authority questions

Status date: 2026-08-26

This register groups only questions whose answers affect the normative meaning
of a validation case. Candidate engineering assumptions must not be presented
as SIA requirements while an item remains open.

## Campaign-wide controlled documents

1. Please confirm the latest applicable SIA 4010 test-package revision and
   provide the current FAQ or controlled clarification log, if one exists.
2. The formerly public `SIA 2024 Raumdatenblätter` Excel tool is no longer
   available from its documented energytools.ch location. May SIA provide or
   identify the controlled machine-readable dataset to use for this campaign?
3. If that workbook cannot be supplied, may the GPL-3.0 ETH Zurich HIVE
   SIA-2024 dataset be used after case-by-case reconciliation? Its schedule
   generator explicitly describes some profiles as inspired by SIA 2024 and
   selected 6.2/6.4 values differ from the later official harmonisation report,
   so the candidate will not treat it as normative without written approval.

## Resolved authority decisions

- Test 1E / Test 2A dynamic solar-protection semantics were resolved by direct
  written response from Prof. Gerhard Zweifel received on 2026-08-26. See
  `authority_decisions/2026-08-26_test1e_solar_control_decision.json`.
- The SIA 2024 category 3.1 annual calendar, hour-ending convention and direct
  0.80 hourly occupancy multiplier were resolved by direct written response
  from Prof. Gerhard Zweifel received on 2026-08-26. See
  `authority_decisions/2026-08-26_sia2024_3_1_calendar_decision.json`.

## Test 1E / Test 2A - acceptable IESVE optical representation

1. IESVE 2025 exposes the external-shade solar and visible reflectances through
   `VECdbConstruction.get_properties()`, but the official documented
   `set_properties()` entry list omits both fields and the runtime rejects them
   as unrecognised options. Is it acceptable for this validation campaign to
   use the documented writable transmission factors and demonstrate
   equivalence through the required hourly transmitted-energy / APS results?
   If not, which IESVE representation or manually configured construction
   should be used for the supplied fabric-awning optical data?
2. The captured ISO 52016-1 Chapter 7 pages state that standard long-wave
   emittance is implicit but do not include its numeric value. The parent
   BESTEST/ASHRAE references consistently specify 0.90 for both interior and
   exterior opaque-surface infrared emittance. May 0.90 be used as the
   authoritative value for the SIA 4010 Test 2 cell, or can the applicable ISO
   clause/page be provided? Until confirmed, the software keeps this value
   provisional and prohibits a Test 2 verdict.
3. A persisted IESVE 2025 diagnostic model using the confirmed 150/150 W/m2
   control, normal-incidence fabric transmittance 0.04, equivalent glazing
   U=0.65393 W/(m2.K), g=0.545 and VT=0.742 passes 10 of the 28 official 1E
   bands. Annual heating is 3191.97 kWh (upper band 2995.37), annual cooling is
   262.03 kWh (lower band 446.94), and peak cooling is 1.273 kW (lower band
   1.752). A non-source 0.21 transmittance sensitivity passes 20/28 but still
   fails eight monthly heating bands. Can SIA or IES provide the accepted
   IESVE-native representation of the Soltis 92-2048-Alu awning, including
   angular direct transmission, diffuse sky/ground transmission, solar and
   visible reflectance, and secondary absorbed-solar heat transfer? Parameter
   tuning will not be used as a substitute for this controlled mapping.
4. The qualified APS output exposes the annual `Window solar gains` series
   (1268.58 kWh integrated for the equivalent diagnostic) but no populated
   exterior-plane incident-irradiance or shade-state series. Which IESVE output
   or audit method is accepted to prove that the device closes at >=150 W/m2
   and reopens below 150 W/m2 during the annual run?
5. ApacheSim reports dynamic convective surface coefficients rather than the
   ISO targets used to define the test cell (for example external mean 19.025
   versus 20.0 W/(m2.K), internal wall 2.087 versus 2.5, roof 4.591 versus 5.0,
   and floor 0.291 versus 0.7); radiative coefficient series are unavailable.
   Must the candidate reproduce the fixed ISO 52016-1 surface coefficients in
   Test 1 diagnostics, or are ApacheSim's dynamic algorithms accepted? If fixed
   values are required, which supported IESVE 2025 settings establish them in
   ApacheSim and what read-back evidence is expected?

## Test 4 - auditorium profiles and fan curves

1. Please provide the complete SIA 2024:2021 `Hörsaal` target-value dataset:
   24-hour people and equipment schedules, annual simultaneity factors,
   use/rest-day calendar rules, exceptions, and hour-boundary convention.
2. Is digitisation of the fan characteristic graph on page 2 of
   `Spezifikation_Test4.pdf` acceptable for validation?
3. If yes, what digitisation tolerance is accepted? If not, can the original
   numerical fan-curve dataset be supplied?

## Test 3 - SIA 387/4 lighting-control functions

1. Please provide the complete normative content of SIA 387/4 Table 10 for
   lighting-control types 1 to 6 used by SIA 4010 Tests 3A to 3F, including
   equations, thresholds, hysteresis, time dependence and state memory.
2. `Spezifikation_Test3.pdf` cites SIA 387/4:2017, while the official SIA
   programme register updated on 2026-02-10 describes class 2A using
   SIA 387/4:2023, section 3.4. Which edition and exact control-function
   implementation must govern this validation campaign?
3. Please confirm the hourly evaluation convention for the daylight sensor,
   lighting-control signal and reported total lighting power.

## Test 7 - photovoltaic precedence and allocation

1. Which value governs the candidate model: the 60.6 kWp total stated in
   `Spezifikation_Test7.pdf` (45.0 kWp roof plus 15.6 kWp south facade), or the
   62.62 kWp total derived from `PV_Layout.pdf`?
2. For the roof array, how must the 150 modules / 45.0 kWp be allocated between
   the east- and west-facing planes?
3. If `PV_Layout.pdf` takes precedence, please confirm the authoritative module
   counts and installed peak power for each orientation and facade.

## Test 6 - restaurant and kitchen standard profiles

1. Please provide the complete SIA 2024:2021 standard-value datasets for category
   6.2 `Selbstbedienungsrestaurant` and category 6.4 `Kueche`, including the
   24-hour people, equipment, lighting and process-heat schedules; occupancy
   density and activity; sensible/latent and moisture gains; annual
   simultaneity factors; use/rest-day rules; holidays or exceptions; and the
   hour-boundary convention.
2. Please confirm that categories 6.2 and 6.4 in the Test 6 specification are
   the authoritative category identifiers for this campaign. The supplied
   example-building material appears to use different 6.x numbering, so an
   edition-dependent mapping must not be inferred by the candidate.

## Test 5 - multizone AHU, rotary recovery and fan curves

1. Please provide the complete room-by-room SIA 2024:2021 standard-value
   datasets required by Test 5 for rooms 100, 102 and 200-205, including use
   categories, 24-hour people/equipment/lighting schedules, densities,
   sensible/latent and moisture gains, annual simultaneity, use/rest-day and
   holiday rules, and the hour-boundary convention.
2. May the publicly available EPB Center workbook
   `Demo_EN_16798-5-1_2021-06-09.xlsm`, authored by Gerhard Zweifel, be used as
   the authoritative implementation reference for the EN 16798-5-1 Annex D
   rotary heat-recovery part-load model in Tests 5A-5D? If not, please provide
   or authorize the exact equations and coefficients that must govern the
   implementation. The workbook itself states that it supports implementation
   but does not replace the standard.
3. Is numerical digitization of the fan characteristic chart on page 2 of
   `Spezifikation_Test5.pdf` acceptable for validation? If yes, what curve
   interpretation, interpolation method and numerical tolerance are required?
   If not, please provide the original numerical fan dataset.

## Claim boundary

Until written answers are received, the software may report source and runtime
readiness, provisional engineering comparisons, and observed results. It must
not report an official SIA pass for the affected cases.
