# Public BESTEST evidence used by the MVP

## Status

The SIA 4010 Test 1 Case 600 MVP uses the public IEA BESTEST specification as
an executable engineering reference:

- NREL/TP-472-6231, *International Energy Agency Building Energy Simulation
  Test (BESTEST) and Diagnostic Method* (1995)
- DOI: <https://doi.org/10.2172/90674>

The source is not redistributed in this repository. The DOI is the controlled
public locator.

## Evidence rule

Values traced only to this public source have the machine-readable status
`PUBLIC_REFERENCE`. They may be used for an internal MVP demonstration, but
they do not permit a normative SIA 4010 compliance claim.

Before changing them to `CONFIRMED_NORMATIVE`, an authorized reviewer must
compare them line by line with ISO 52016-1:2017 Chapter 7 and record:

1. the controlled document edition;
2. the clause/table/cell locator;
3. the reviewer and review date;
4. any difference from the public BESTEST definition;
5. the approved resulting value and unit convention.

## Deliberately unresolved evidence

- identity of the client weather file with the required Denver DRYCOLD dataset;
- exact ISO Chapter 7 identity of envelope, glazing and infiltration inputs;
- VE runtime read-back of the Case 600 glazing U-value and g-value;
- visible transmittance, currently an explicit non-energy proxy because Case
  600 does not evaluate daylighting.

