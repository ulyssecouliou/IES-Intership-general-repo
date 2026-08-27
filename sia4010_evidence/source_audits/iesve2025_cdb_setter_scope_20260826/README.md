# IESVE 2025 `VECdbConstruction.set_properties` scope

Accessed: 2026-08-26

Primary source: https://help.iesve.com/ve2025/6_1_29_1_methods_defined_here.htm

The official IESVE 2025 Python API page lists the accepted dictionary entries
for `VECdbConstruction.set_properties`. The external-shade entries include the
active flag, code, profile, raise/lower irradiance expressions, diffuse factors
and direct transmittances at the documented angles. The list includes
`external_shade_transmittance_0` but does not include
`external_shade_solar_reflectance` or
`external_shade_visible_reflectance`.

Runtime confirmation in VE 2025 on 2026-08-26 rejected the latter property with
`unrecognised option: external_shade_solar_reflectance`, even though both
reflectance values were visible through `get_properties()`.

Decision: qualify only the documented writable subset. Keep solar and visible
external-shade reflectance mapping and all resulting optical equivalence claims
fail-closed. This is an IESVE API capability decision, not a SIA acceptance
decision.
