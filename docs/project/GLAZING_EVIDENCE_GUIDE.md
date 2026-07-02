# Glazing And Solar-Protection Evidence Guide

## Purpose

This guide explains how glazing evidence is retrieved from IESVE and how to
complete any remaining evidence manually for Swiss SIA 380/2:2022 and
SIA 4010:2023 readiness reporting.

The workflow should always prefer audited VE/CDB data over manual entry. Manual
evidence is only used when the IESVE API does not expose a value, when the
meaning of a value is ambiguous, or when an external reviewer/manufacturer
source is required.

## IESVE API Source Map

The local reference is `references/iesve/VEScripts.pdf`.

Useful API objects and documented fields:

- `VEProject.get_current_project()` opens the active VE project.
- `VEModel.get_bodies(False)` returns VE bodies/rooms.
- `VEBody.get_surfaces()` returns the room bounding surfaces.
- `VESurface.get_openings()` returns `VEGeometry` openings assigned to a
  surface.
- `VESurface.get_constructions()` returns construction IDs used by the surface,
  including opening constructions.
- `VEGeometry.get_construction()` returns the construction ID assigned to an
  opening.
- `VEGeometry.get_properties()` returns opening data such as area, index, type,
  width and height.
- `VECdbProject.get_construction(construction_id, construction_class)` resolves
  the CDB construction.
- `VECdbConstruction.get_properties()` exposes glazing, frame and shade fields
  such as `g_value`, `light_transmittance`,
  `visible_light_transmittance`, `frame_percent`,
  `external_shade_active`, `external_shade_profile`,
  `internal_shade_active`, `internal_shade_profile`,
  `local_shade_active` and related shade properties.
- `VECdbConstruction.get_g_values()` exposes named g-values such as
  `bs_en_410`, `building_regulations` and `bfrc`.
- `VECdbConstruction.get_u_factor(uvalue_types)` exposes U-values by method.
- `VECdbConstruction.get_layers()` and `VECdbLayer.get_properties()` can expose
  layer/material properties when construction-level values are incomplete.
- `VEMacroFlo.get()` can provide opening natural-ventilation/openability
  evidence, but it is not a glazing optical-property source.
- `VESuncast.get_results(...)` can provide shading/insolation result evidence,
  but it does not replace the need to document glazing optical values and active
  shade controls.

Relevant pages in `VEScripts.pdf`:

- Pages 195-196: `VEBody`, `get_areas()`, `get_surfaces()`.
- Pages 198-200: `VECdbConstruction`, `get_properties()`, `get_g_values()`,
  frame, light-transmittance and shade fields.
- Pages 202-203: `VECdbLayer` and `VECdbMaterial` properties.
- Pages 204-206: `VECdbProject`, construction classes and glazing categories.
- Page 210: `VEGeometry.get_construction()` and `VEGeometry.get_properties()`.
- Page 215: `VEMacroFlo.get()` for opening type/openability evidence.
- Pages 222-223: `VEProject.profiles()` and `thermal_templates()`.
- Page 239: `VESuncast.get_results(...)`.
- Pages 240-241: `VESurface.get_areas()`, `get_constructions()` and
  `get_openings()`.

## What Is Retrieved Automatically

The extractor attempts to populate the following evidence directly from
opening properties and CDB construction properties:

- Opening construction ID.
- Opening area.
- Window U-value / Uw.
- Glazing solar factor / g-value.
- Visible transmittance from `visible_transmittance`,
  `visible_light_transmittance`, `light_transmittance`, `tau_v`, `tau` or
  `tvis`.
- Frame fraction from `frame_fraction`, `frame_factor`, `frame_percent`,
  `frame_inside_surface_area_ratio` or `frame_outside_surface_area_ratio`.
- Solar-protection type from direct shade fields or active CDB shade flags.
- Solar-protection control from shade profiles and radiation thresholds.
- Effective glazing-plus-shading g-value when VE exposes a direct value such as
  `g_total`, `effective_g_value`, `shaded_g_value` or equivalent.
- Named VE/CDB g-values from `VECdbConstruction.get_g_values()`:
  `bs_en_410`, `building_regulations` and `bfrc`. The generated workbook sheet
  `VE G-VALUES AUDIT` exposes these side by side so reviewers can prove whether
  a CDB `g_value` such as `0.75` is the same value as the SIA-comparable EN 410
  normal solar factor.

Percent values are normalized to fractions where needed. For example,
`frame_percent = 25` is interpreted as `0.25`.

## What Still Needs Reviewer Evidence

The following items may remain manual because VE may not expose them as a
single certifiable field:

- Confirmation that the VE `solar_factor` / `g_value` is the correct SIA
  comparable value, for example EN 410 `g_perp` or a justified SHGC mapping.
- Manufacturer glazing schedule when the CDB value is not sufficient or not
  auditable.
- Active `g_total` with solar protection if the base glazing g-value exceeds
  the SIA threshold and a shaded value is claimed.
- Blind/shade optical properties when they are not fully defined in the CDB.
- Control logic and thresholds if the CDB only references a profile name.
- Reviewer confirmation that the value applies to the correct SIA use category,
  orientation, room and simulation scenario.

## How To Complete The Evidence Template

Use `templates/evidence/glazing_solar_protection_template.csv`.

For each construction listed in the workbook sheet `FACADE GLAZING REVIEW`:

1. Keep the `project_name`, `model_name` and `construction_id`.
2. Fill or confirm `window_uw_w_m2k`.
3. Fill or confirm `glazing_g_perp_or_shgc`.
4. Fill `visible_transmittance_tau_v`.
5. Fill `frame_fraction` as a fraction, for example `0.25`.
6. Fill `solar_protection_type` and `solar_protection_category` if a shade is
   used.
7. Fill `shading_control_strategy` and `control_thresholds`.
8. Fill `g_total_with_shading` only if the shaded value is used for compliance.
9. Add `source_document` and `source_page_or_sheet`.
10. Set `review_status` to `reviewed` only after the responsible reviewer has
    checked source, applicability and SIA interpretation.

Store filled evidence under `sia4010_evidence/` or another reviewed evidence
folder referenced by the report.

If the issue is specifically whether a VE/CDB g-value is comparable to SIA
`g_perp`, use `templates/evidence/g_values_audit_template.csv` together with
the workbook sheet `VE G-VALUES AUDIT`. This is the preferred place to document:

- the raw CDB `g_value`;
- `bs_en_410`, `building_regulations` and `bfrc`;
- the selected SIA `g_perp` candidate;
- whether the CDB value is proven to be different from EN 410;
- whether `g_total_with_shading` is directly available or requires an external
  calculation/reviewer evidence.

## Current ZOER_32_C1 Finding Pattern

The latest report shows three glazing constructions in the facade review:

- `STD_EXTW`
- `STD_EXT1`
- `STD_EXT2`

They currently have acceptable extracted Uw values, but an extracted g-value of
about `0.75`, compared against the current SIA 380/2 readiness threshold of
`0.50`. If that `0.75` is the correct comparable EN 410 normal solar factor,
the glazing fails the readiness check unless an auditable active-shading
`g_total` is provided and accepted.

## Practical Rule

Use this hierarchy:

1. Automated VE/CDB extraction from the API.
2. Official VE/CDB export or screenshot proving the same values.
3. Manufacturer schedule or reviewer evidence when VE does not expose the
   field.
4. Manual input template, only with source and reviewer sign-off.

Never convert a missing value into a pass. Missing evidence must remain visible
in the report until it is genuinely sourced and reviewed.
