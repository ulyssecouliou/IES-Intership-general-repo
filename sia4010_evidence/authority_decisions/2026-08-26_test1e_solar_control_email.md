# SIA 4010 Test 1E solar-control authority decision

- Received: 2026-08-26
- Authority: Prof. Gerhard Zweifel
- Medium: direct written email response supplied by the validation candidate
- Scope: Test 1E fabric-awning irradiance control and IESVE field mapping

## Questions and answers retained as controlled evidence

1. Governing signal: total solar irradiance incident on the exterior plane of
   the glazing.
2. Closing rule: close when irradiance is greater than or equal to 150 W/m2.
3. Reopening rule: reopen when irradiance falls below 150 W/m2.
4. Timestep rule: with hourly timesteps, equality is not expected to occur. A
   sub-hourly tool may activate during the hour. The shading state is not a
   required reported variable; it affects transmitted energy, reported as an
   hourly sum.
5. Hysteresis: none.
6. IESVE mapping: setting both
   `external_shade_radiation_to_lower` and
   `external_shade_radiation_to_raise` to 150 W/m2 was confirmed correct.

## Normalized implementation rule

- Signal: `total_solar_irradiance_incident_on_exterior_glazing_plane`
- Close: `irradiance >= 150 W/m2`
- Reopen: `irradiance < 150 W/m2`
- Hysteresis: `false`
- IESVE lower threshold: `150 W/m2`
- IESVE raise threshold: `150 W/m2`
- Required reporting effect: hourly sum of transmitted energy

This decision resolves the normative control-semantics questions. It does not
by itself prove the optical mapping, VE model assignment/read-back, APS output
binding or Test 1E acceptance-band result.
