# Swiss SIA 380/2 Reference Model Engineering Basis

Baseline ID: `SIA3802_LIMIT_REFERENCE_OFFICE_2026_01`

## 1. Claim boundary

This baseline is an executable reference model for a Swiss SIA 380/2-oriented
workflow. It is not an official SIA 4010 software-validation result and is not
proof of regulatory compliance for a real building. The final claim requires
the licensed external standards, an approved project brief, simulation results,
the official SIA 4010 test package, and independent review.

## 2. Geometry

- Single storey, 20 m by 12 m by 3 m.
- Four deterministic thermal zones in a two-by-two grid.
- North axis at 0 degrees.
- One repeatable window pattern, one external door, and generated overhang
  shading surfaces.
- Geometry values are software reference-model assumptions, not regulatory
  limits.

## 3. SIA 380/2 comparison-project inputs

The licensed project copy of SIA 380/2:2022 is the controlled source.

- External wall: table 3 limit construction, declared U = 0.20 W/(m2 K).
- Flat roof: table 3 limit construction, declared U = 0.20 W/(m2 K).
- Ground floor: table 3 limit construction, declared U = 0.30 W/(m2 K).
- Whole window: table 2 limit input, Uw = 1.10 W/(m2 K).
- Glazing: table 2, g = 0.50 and visible transmittance = 0.70.
- Window frame share: table 2, 25 percent.
- Thermal bridges: table 2 comparison-project value of zero.
- Infiltration: table 2, 0.15 m3/(h m2), represented in VE as
  0.0416666667 L/(s m2).
- Heat-recovery temperature ratio: table 2 limit input, 0.73 at the declared
  reference condition.
- Solar protection: external venetian blind, comparison-project solar-protection
  category 4 and SIA 387/4 control category 2, with facade-wise automatic
  irradiance-based control, following table 2 and clauses 7.1.2.3-7.1.2.4.

The equivalent glazing layer and door layer are software representations, not
manufacturer products. Their calculated VE properties must be read back and
reviewed after the first real-VE run.

## 4. Office engineering assumptions

SIA 380/2 delegates several usage inputs to SIA 2024 and SIA 387/4. Because a
controlled SIA 2024 data table is not part of this input package, the following
values are deliberately labelled project assumptions rather than SIA values:

- Generic office reference use.
- Occupancy density: 15 m2/person.
- Occupied outdoor air: 10 L/(s person).
- People gains: 75 W/person sensible and 45 W/person latent.
- Lighting: 12 W/m2.
- Equipment: 20 W/m2 with 10 percent out-of-hours standby.
- Heating setpoint: 20 degC.
- Cooling setpoint: 26 degC.
- Daily occupied period: 08:00-18:00, with transition points at 07:00 and
  19:00.

Replace these assumptions with a licensed, reviewer-approved SIA 2024/SIA
387/4 mapping before making a formal compliance claim.

## 5. HVAC boundary

The baseline creates conditioned room data, gains, infiltration and mechanical
outdoor-air exchange. It intentionally does not create a detailed ApacheHVAC
network or claim system-level SIA compliance. A later version must add the
approved supply, distribution, emission, generation, controls, auxiliaries and
part-load behavior.

## 6. Climate

The configured weather input is the client-provided EPW file
`SMA_2035_RCP85_DRY.epw`, whose header identifies Zurich Fluntern at latitude
47.377925 and longitude 8.565742. The filename and data year identify the
selected 2035 RCP8.5 DRY scenario. The project reviewer must confirm that this
is the required SIA 2028 climate decision for the intended assessment.

## 7. Required real-VE qualification

Run `Run_VE_Reference_Model_Capability_Probe.py` first. Then execute the model
generator only in a disposable blank VE project. Accept the baseline only when:

- all creation capabilities are present;
- the EPW opens through `WeatherFileReader`;
- profiles, materials, constructions and the thermal template persist;
- every surface and opening assignment reads back correctly;
- the CDB-reported ISO U-values match the declarations within the software QA
  tolerance;
- glazing g-value, light transmittance and frame fraction read back correctly;
- no validation result is `FAIL`.
