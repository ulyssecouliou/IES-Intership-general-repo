# IESVE VEScript Python API — Complete Reference
> Source: VE 2023 VEScript User Guide | Version: VE 2023 | Language: Python 3
> All API methods return **metric units** regardless of VE display settings.
> **Never use `argparse` in VE Scripting Editor scripts.**
> **Required Excel library: `xlsxwriter` (not openpyxl).**

---

## TABLE OF CONTENTS

1. [Environment & Setup](#1-environment--setup)
2. [Class Hierarchy Overview](#2-class-hierarchy-overview)
3. [Top-Level Module Methods](#3-top-level-module-methods)
4. [VEProject](#4-veproject)
5. [VEModel](#5-vemodel)
6. [VEBody](#6-vebody)
7. [VESurface](#7-vesurface)
8. [VEAdjacency](#8-veadjacency)
9. [VEGeometry](#9-vegeometry)
10. [VERoomData](#10-veroomdata)
11. [RoomAirExchange](#11-roomairexchange)
12. [RoomInternalGain](#12-roominternalgain)
13. [VEThermalTemplate](#13-vethermaltemplate)
14. [AirExchange](#14-airexchange)
15. [CasualGain](#15-casualgain)
16. [VEProfile](#16-veprofile)
17. [VEApacheSystem](#17-veapachesystem)
18. [ApacheSim](#18-apachesim)
19. [ResultsReader](#19-resultsreader)
20. [RoomGroups](#20-roomgroups)
21. [VELocate](#21-velocate)
22. [WeatherFileReader](#22-weatherfilereader)
23. [VECdbConstruction](#23-vecdbconstruction)
24. [VECdbDatabase / VECdbProject / VECdbLayer / VECdbMaterial](#24-vecdbdatabase--vecdbproject--vecdblayer--vecdbmaterial)
25. [EnergySources](#25-energysources)
26. [VEEnergyMeter](#26-veenergymeter)
27. [VERenewables](#27-verenewables)
28. [VEMacroFlo](#28-vemacroflo)
29. [VESuncast](#29-vesuncast)
30. [VESankey](#30-vesankey)
31. [VEComponentProcess](#31-vecomponentprocess)
32. [HVAC Network Classes](#32-hvac-network-classes)
33. [ProjectInfo](#33-projectinfo)
34. [Mv2 (Model Viewer 2)](#34-mv2-model-viewer-2)
35. [Available Third-Party Libraries](#35-available-third-party-libraries)
36. [Critical Patterns & Anti-Patterns](#36-critical-patterns--anti-patterns)
37. [Complete Working Code Templates](#37-complete-working-code-templates)

---

## 1. Environment & Setup

```python
import iesve           # Always required — the main VE API module
import xlsxwriter      # Required for Excel output (NOT openpyxl)
import tkinter as tk   # Available for GUI dialogs
from tkinter import ttk
import tkinter.messagebox as messagebox
import os
import numpy as np     # Available (v1.11.0)
```

**Key Rules:**
- Scripts run inside the VE Scripting Editor — no `argparse`, no `sys.argv`
- `xlsxwriter` is the required library for Excel. `openpyxl` does NOT work in VE environment
- All values returned are in **metric units** (m, m², m³, °C, W, l/s, etc.)
- The Vista results folder is always at: `project.path + "Vista"`
- APS files are opened by filename only (not full path) when using `ResultsReader.open()`

---

## 2. Class Hierarchy Overview

```
iesve (module)
├── VEProject                   ← Entry point for all model data
│   ├── .models[]               → List[VEModel]
│   ├── .thermal_templates()    → Dict[handle, VEThermalTemplate]
│   ├── .profiles()             → ({daily}, {group})
│   ├── .apache_systems()       → List[VEApacheSystem]
│   ├── .casual_gains()         → List[CasualGain]
│   └── .air_exchanges()        → List[AirExchange]
│
├── VEModel
│   └── .get_bodies(False)      → List[VEBody]
│
├── VEBody
│   ├── .get_room_data()        → VERoomData
│   ├── .get_surfaces()         → List[VESurface]
│   └── .get_areas()            → dict
│
├── VERoomData
│   ├── .get_general()          → dict
│   ├── .get_internal_gains()   → List[RoomInternalGain]
│   ├── .get_air_exchanges()    → List[RoomAirExchange]
│   ├── .get_apache_systems()   → dict
│   └── .get_room_conditions()  → dict
│
├── VESurface
│   ├── .get_adjacencies()      → List[VEAdjacency]
│   ├── .get_openings()         → List[VEGeometry]
│   └── .get_areas()            → dict
│
├── ResultsReader               ← Static class for APS results
│   └── .open(filename)         → ResultsReader instance
│
├── RoomGroups                  ← Room grouping and HVAC zones
├── VELocate                    ← Location/weather data
├── ApacheSim                   ← Run simulations
└── VESankey                    ← Sankey diagrams
```

---

## 3. Top-Level Module Methods

```python
iesve.get_application_folder() -> str
# Returns the installation path of the VE application
```

---

## 4. VEProject

**The primary entry point. Always start here.**

### Static Methods

```python
project = iesve.VEProject.get_current_project()  # Returns the currently open project
```

### Instance Methods

```python
project.air_exchanges() -> list                  # All AirExchange objects in project
project.apache_systems() -> list                 # All VEApacheSystem objects
project.archive_project(destination: str, full: bool) -> bool
project.casual_gains() -> list                   # All CasualGain objects
project.create_profile(type, reference=None, modulating=True, units=-1) -> VEProfile
    # type: 'daily' | 'weekly' | 'yearly' | 'compact' | 'freeform'
    # units: 0=metric, 1=IP, -1=none
project.daily_profile(profileID: str) -> VEProfile
project.daily_profiles([profileIDs]) -> dict     # {profileID: VEProfile}
project.deregister_content(path: str)
project.get_display_units() -> DisplayUnits      # metric | imperial
project.get_language_code() -> tuple[str, str]
project.get_macro_flo_opening_by_id(openingID) -> opening_type
project.get_macro_flo_opening_types() -> list
project.get_scenario_base_project_path() -> str
project.get_version() -> str                     # e.g. "2023.1.0.23"
project.group_profile(profileID: str) -> VEProfile
project.group_profiles([profileIDs]) -> dict
project.profiles() -> tuple                      # ({daily_profiles}, {group_profiles})
project.register_content(path, category, displayString, notification: bool)
project.save_profiles() -> bool
project.thermal_templates(assigned=True, allow_ncm=False) -> dict
    # assigned=False → returns ALL templates, not just assigned ones
    # Returns: {template_handle: VEThermalTemplate}
```

### Attributes

```python
project.content_folder   # str — project content folder path
project.models           # list[VEModel] — index 0 is always the real building
project.name             # str — project title
project.path             # str — project folder path (includes trailing backslash on Windows)
```

### Enums

```python
iesve.VEProject.DisplayUnits   # metric, imperial
iesve.VEProject.ProfileUnits   # metric, imperial, none
```

---

## 5. VEModel

### Accessing the Model

```python
project = iesve.VEProject.get_current_project()
model = project.models[0]   # Index 0 = real/proposed building
```

### Methods

```python
model.assign_thermal_template_to_rooms(template, [roomID_list])
model.get_assigned_profiles(expandProfiles=False) -> list  # [profileID strings]
model.get_bodies(selectedOnly: bool) -> list[VEBody]
    # selectedOnly=False → ALL bodies; True → only selected
model.get_bodies_and_ids(selectedOnly: bool) -> dict  # {roomID: VEBody}
model.get_exterior_lighting_details(LightingStandard) -> dict
model.get_included_bodies_for_umlh() -> list[VEBody]
model.get_excluded_bodies_for_umlh() -> list[VEBody]
model.get_mep_details(attribute_type=None) -> dict
model.rebuild_adjacencies()
model.suncast() -> VESuncast
```

### Attributes

```python
model.id           # str — model description
model.model_type   # VEModels enum
```

### Enums

```python
# VEModels enum values:
# VEModels_NA, RealBuilding, ActualBuilding, NotionalBuilding,
# TypicalBuilding, ReferenceBuilding, ProposedBuilding, BaselineBuilding,
# NewZealandProposedBuilding, NewZealandReferenceBuilding,
# GreenMarkProposedBuilding, GreenMarkReferenceBuilding,
# SunCastSolarVisBuilding, LEEDSunCastSS71Building,
# Title24ProposedBuilding, Section63PrescriptiveBuilding,
# Title24StandardDesignBuilding, NECBProposedBuilding, NECBReferenceBuilding

# LightingStandard enum values:
# PRM2007, PRM2010, PRM2013, IECC2012, NECB2011, PRM2016, NECB2017
```

---

## 6. VEBody

Represents a single space/room in the model.

### Accessing Bodies

```python
bodies = model.get_bodies(False)   # False = all bodies, not just selected
for body in bodies:
    if body.type == iesve.VEBody.VEBody_type.room:
        room_data = body.get_room_data()
```

### Methods

```python
body.assign_construction(construction_id, surface)
body.assign_construction_to_opening(construction_id, surface, opening_id)
body.assign_opening_type_by_id(surface_index, macroflo_id, opening_id)
body.get_areas() -> dict         # All area types in m², volume in m³
body.get_assigned_constructions() -> list[tuple]  # [(constructionID, '')]
body.get_assigned_profiles() -> list[tuple]       # [(profileID, '')]
body.get_index()                 # Returns the body's APS index
body.get_processes() -> list[VEComponentProcess]
body.get_properties() -> dict    # min_height, max_height, floor_height_above_ground
body.get_room_data(type=attribute_type.active_attributes) -> VERoomData
body.get_surfaces() -> list[VESurface]
body.is_3d_shade() -> bool
body.select()                    # Selects body for VEGeometry operations
```

### get_areas() — Return Dictionary Keys

```python
areas = body.get_areas()
# All values in m² (except volume which is in m³):
areas['int_floor_area']       areas['ext_floor_area']
areas['int_floor_opening']    areas['ext_floor_opening']
areas['int_floor_glazed']     areas['ext_floor_glazed']
areas['int_ceiling_area']     areas['ext_ceiling_area']
areas['int_ceiling_opening']  areas['ext_ceiling_opening']
areas['int_ceiling_glazed']   areas['ext_ceiling_glazed']
areas['int_ceiling_door']     areas['ext_ceiling_door']
areas['int_wall_area']        areas['ext_wall_area']
areas['int_wall_opening']     areas['ext_wall_opening']
areas['int_wall_glazed']      areas['ext_wall_glazed']
areas['int_wall_door']        areas['ext_wall_door']
areas['volume']               # m³
```

### Attributes

```python
body.bim_id         # str — BIM ID
body.cad_object_id  # str — CAD object ID
body.id             # str — unique room ID (unique within the model)
body.hvac_methodology  # VEBody_hvac_methodology enum: apache_system | apache_hvac
body.name           # str (get & set)
body.selected       # bool
body.subtype        # VEBody_subtype enum
body.type           # VEBody_type enum
```

### Enums

```python
# VEBody_type:
# 3D: room, adjacent_building, topographical_shade, local_shade, tree
# 2D: road, pavement, parking_bay, hard_landscape, pervious_landscape,
#     soft_landscape_turf, soft_landscape_shrubs, soft_landscape_groundcover,
#     soft_landscape_mixedveg, soft_landscape_wetlands, vegetated_shade, water, boundary
# 1D: annotation

# VEBody_subtype:
# Spaces: room, void, ra_plenum, sa_plenum
# Boundaries: boundary_site, boundary_leed, boundary_stormwater, ...

# attribute_type:
# real_attributes, ncm_attributes, bprm_attributes, t24_attributes,
# green_star_attributes, new_zealand_attributes, green_mark_attributes,
# necb_attributes, active_attributes

# hvac_methodology:
# apache_system, apache_hvac
```

---

## 7. VESurface

Represents a bounding surface of a body/room.

### Accessing Surfaces

```python
surfaces = body.get_surfaces()
for surface in surfaces:
    props = surface.get_properties()
    adjacencies = surface.get_adjacencies()
    openings = surface.get_openings()
```

### Methods

```python
surface.get_adjacencies() -> list[VEAdjacency]
surface.get_areas() -> dict       # See keys below
surface.get_constructions() -> list  # [construction_id strings]
surface.get_openings() -> list[VEGeometry]
surface.get_opening_by_id(opening_id) -> VEGeometry
surface.get_opening_totals() -> dict
    # Keys: openings, doors, holes, windows,
    #       external_doors, external_holes, external_windows
surface.get_properties() -> dict
surface.move(distance) -> list
surface.id() -> str              # Surface ID
```

### get_properties() Keys

```python
props = surface.get_properties()
props['aps_handle']   # int — APS handle (used in ResultsReader surface calls)
props['area']         # float, m² — surface area
props['id']           # str — surface ID
props['orientation']  # float — degrees from north (not adjusted for site angle)
props['thickness']    # float — meters
props['tilt']         # float — degrees from horizontal (0=horizontal/up, 90=vertical)
props['type']         # str — surface type string
```

### get_areas() Keys

```python
areas = surface.get_areas()
# Keys: area, total_gross, total_net, total_window, total_door, total_hole,
#       total_gross_openings, internal_gross, internal_net, internal_window,
#       internal_door, internal_hole, internal_gross_openings,
#       external_gross, external_net, external_window, external_door,
#       external_hole, external_gross_openings
```

### Attributes

```python
surface.index   # int — index within parent body
surface.type    # VESurface_type enum
```

### Enums

```python
# VESurface_type:
# floor, ceiling, ext_wall, int_glazing, ext_glazing, int_door, ext_door,
# ground_floor, roof, roof_glazing, int_wall, hole
```

---

## 8. VEAdjacency

### Accessing

```python
adjacencies = surface.get_adjacencies()
for adj in adjacencies:
    props = adj.get_properties()
    construction_id = adj.get_construction()
```

### Methods

```python
adj.get_properties() -> dict
adj.get_construction() -> str    # construction ID
```

### get_properties() Keys

```python
props = adj.get_properties()
props['aps_handle']      # int — APS handle
props['body_id']         # str — room ID on the other side of the adjacency
props['distance']        # float, meters — distance between the two rooms
props['surface_index']   # int — index of surface in adjacent room
props['door']            # float, m² — total door area in adjacency
props['gross']           # float, m² — gross area including all openings
props['hole']            # float, m² — total hole opening area
props['window']          # float, m² — total glazed opening area
```

---

## 9. VEGeometry

Represents an opening (window, door, hole) in a surface.

### Accessing Openings

```python
openings = surface.get_openings()
for opening in openings:
    props = opening.get_properties()
    construction_id = opening.get_construction()
    opening_id = opening.get_id()
    macroflo_id = opening.get_macroflo_id()
```

### Instance Methods

```python
opening.get_construction() -> str     # Construction ID (empty string if none)
opening.get_id() -> str               # Opening ID
opening.get_macroflo_id() -> str      # Macroflo opening ID
opening.get_properties() -> dict      # See keys below
opening.move_opening(xdistance, ydistance)
```

### get_properties() Keys

```python
props = opening.get_properties()
props['aps_handle']     # int
props['area']           # float, m²
props['aspect_ratio']   # float
props['height']         # float, m (accurate only for rectangular openings)
props['index']          # int — opening index (used in ResultsReader)
props['macroflo_type']  # str
props['perimeter']      # float, m
props['sill_height']    # float, m
props['type']           # str — 'door', 'window', or 'hole'
props['width']          # float, m (accurate only for rectangular openings)
```

### Static Methods (model-level geometry operations)

```python
iesve.VEGeometry.centre_to_origin()
iesve.VEGeometry.get_building_orientation() -> float   # degrees
iesve.VEGeometry.get_wwr() -> float                    # window-to-wall ratio
iesve.VEGeometry.reduce_ext_windows(max_wwr: float)
iesve.VEGeometry.remove_doors(flag: int, opening_area: float)
    # flag: 0=all, 1=internal, 2=external
iesve.VEGeometry.remove_holes(flag: int, opening_area: float)
iesve.VEGeometry.remove_openings_below_area_threshold(area_threshold: float)
iesve.VEGeometry.set_body_opening_type(opening_type: str)
    # opening_type: 'door' | 'window' | 'hole'
iesve.VEGeometry.set_building_orientation(orientation: float)
iesve.VEGeometry.set_colour(colour_index: int)
    # 0=BLUE, 1=GREEN, 2=RED, 3=YELLOW, 4=PURPLE, 5=ORANGE, 6=CYAN,
    # 7=LIGHT GREY, 48=WHITE, 56=BLACK
iesve.VEGeometry.set_percent_doors(percent_doors: int)
iesve.VEGeometry.set_percent_glazing(percent_glazing: int)   # external surfaces
iesve.VEGeometry.set_percent_holes(percent_holes: int)
iesve.VEGeometry.set_percent_wall_glazing(percent_glazing: int)
```

### Enums

```python
# opening_internality: any, internal, external
```

---

## 10. VERoomData

The primary interface for room-level model data. Returned by `body.get_room_data()`.

### Accessing

```python
room_data = body.get_room_data()
# or with specific attribute type:
room_data = body.get_room_data(iesve.VEBody.attribute_type.real_attributes)
```

### Methods

```python
room_data.get_air_exchanges() -> list[RoomAirExchange]
room_data.get_apache_systems() -> dict       # System assignment and HVAC config
room_data.get_building_regs() -> dict        # NCM models only
room_data.get_general() -> dict              # Room name, ID, area, volume, template
room_data.get_internal_gains() -> list[RoomInternalGain]
room_data.get_ncm_lighting() -> dict         # NCM models only
room_data.get_necb_2017_lighting_controls() -> dict
room_data.get_room_conditions() -> dict      # Setpoints, schedules, humidity
room_data.get_transpired_solar_collectors() -> list  # NCM only
room_data.set(general_data, room_conditions_data, systems_data)
room_data.set_apache_systems(data: dict)
room_data.set_building_regs(data: dict)
room_data.set_collector_area(surface_number, collector_area)
room_data.set_general(data: dict)
room_data.set_ncm_lighting(data: dict)
room_data.set_room_conditions(data: dict)
```

### get_general() Keys

```python
gen = room_data.get_general()
# Includes: body name, body ID, general template, thermal template,
#           room volume (m³), floor area (m²),
#           lettable_perc, circ_perc, included_in_building_floor_area
# Key lookup: gen['thermal_template'] → thermal template name/ID assigned
```

### get_apache_systems() Keys

```python
sys_data = room_data.get_apache_systems()
# Key structure:
sys_data['HVAC_system']            # str — HVAC system ID
sys_data['HVAC_system_from_template']  # bool
sys_data['HVAC_methodology']       # str — 'apache_system' | 'apache_hvac'
sys_data['conditioned']            # bool
sys_data['aux_vent_system']        # str — auxiliary ventilation system ID
sys_data['dhw_system']             # str — DHW system ID
# Heating:
sys_data['heating_unit_size']      # float, kW (or W/m² depending on unit)
sys_data['heating_capacity_unlimited']  # bool
sys_data['heating_design_supply_temp']  # float, °C
# Cooling:
sys_data['cooling_unit_size']      # float, kW
sys_data['cooling_capacity_unlimited']  # bool
sys_data['cooling_design_supply_temp']  # float, °C
# Outside air:
sys_data['system_air_minimum_flowrate']  # float
sys_data['system_air_minimum_flowrate_from_template']  # bool
```

### get_room_conditions() Keys

```python
cond = room_data.get_room_conditions()
# Heating setpoint:
cond['heating_setpoint']              # float, °C (if constant)
cond['heating_setpoint_type']         # 'constant' | 'variable' | 'two_value'
cond['heating_setpoint_profile']      # str — profile ID (if variable)
cond['heating_profile']               # str — profile ID
# Cooling setpoint:
cond['cooling_setpoint']              # float, °C (if constant)
cond['cooling_setpoint_type']         # 'constant' | 'variable' | 'two_value'
cond['cooling_setpoint_profile']      # str
cond['cooling_profile']               # str
# DHW:
cond['dhw']                           # float
cond['dhw_profile']                   # str — profile ID
# Humidity:
cond['sat_perc_lower']               # float, %
cond['sat_perc_upper']               # float, %
# Other:
cond['solar_reflected_fraction']     # float
cond['furniture_mass_factor']        # float
cond['plant_profile']                # str — profile ID
cond['plant_profile_type']           # int: 0=heating, 1=cooling, 2=independent
```

### Attributes

```python
room_data.id   # str — room ID
```

### Enums

```python
# conditioned_flag: no_free_floating, not_applicable, no_tempered, yes
# setpoint_type: constant, variable, two_value
# demand_controlled_ventilation: none, occupancy_density, gas_sensors, enhanced_ventilation
# heat_recovery: no_heat_recovery, plate_heat_exchanger, heat_pipes, thermal_wheel, run_around_coil
```

---

## 11. RoomAirExchange

Returned by `room_data.get_air_exchanges()`.

### Methods

```python
air_ex.get() -> dict
```

### get() Return Dictionary Keys

```python
data = air_ex.get()
data['adjacent_condition_string']     # str
data['adjacent_condition_val']        # int: 1=ext_air, 2=ext_air+offset, 3=adjacent, 5=profile
data['adjacent_condition_val_from_template']  # bool
data['max_flow_from_template']        # bool
data['max_flows']                     # dict of 4 floats indexed by int (various unit conversions)
data['name']                          # str
data['offset_temperature']            # float (only if adjacent_condition_val == 2)
data['temperature_profile']           # str — profile ID
data['temperature_profile_from_template']  # bool
data['type_val']                      # int: 0=Infiltration, 1=NatVent, 2=AuxVent
data['units_strs']                    # dict of str indexed by int (unit labels)
data['units_val']                     # int: 0=ach, 1=l/s, 2=l/s/m², 3=l/s/person, 4=l/(s.m²fac)
data['variation_profile']             # str — profile ID
data['variation_profile_from_template']  # bool
```

**type_val values:**
- `0` = Infiltration
- `1` = Natural Ventilation
- `2` = Auxiliary Ventilation

**units_val values:**
- `0` = ach
- `1` = l/s
- `2` = l/s/m²
- `3` = l/s/person
- `4` = l/(s.m² façade)

---

## 12. RoomInternalGain

Returned by `room_data.get_internal_gains()`. Three subclasses: `RoomPowerGain`, `RoomLightingGain`, `RoomPeopleGain`.

### Methods

```python
gain.get() -> dict
```

### RoomPowerGain — get() Keys

```python
data = gain.get()
data['type_str']                 # 'Machinery' | 'Miscellaneous' | 'Cooking' | 'Computers'
data['type_val']                 # int: 2=Machinery, 3=Misc, 4=Cooking, 5=Computers
data['name']                     # str
data['max_sensible_gains']       # dict of floats indexed by int (multiple unit conversions)
data['max_latent_gains']         # dict of floats indexed by int
data['max_power_consumptions']   # dict of floats indexed by int
data['units_strs']               # dict of str (unit labels) indexed by int
data['units_val']                # int: 0=W/m², 1=W
data['radiant_fraction']         # float
data['diversity_factor']         # float
data['energy_source']            # str — fuel name
data['variation_profile']        # str — profile ID
```

### RoomLightingGain — get() Keys

```python
data = gain.get()
data['type_str']                 # 'Fluorescent Lighting' | 'Tungsten Lighting'
data['type_val']                 # int: 0=Fluorescent, 1=Tungsten
data['name']                     # str
data['max_sensible_gains']       # dict of floats indexed by int
data['max_power_consumptions']   # dict of floats indexed by int
data['units_str']                # str: 'W/m²' | 'W' | 'lux'
data['units_val']                # int: 0=W/m², 1=W, 2=lux
data['radiant_fraction']         # float
data['diversity_factor']         # float
data['ballast']                  # float
data['design_illuminance']       # float, lux (only if units_val==2)
data['minimum_illuminance']      # float, lux (only if units_val==2)
data['maximum_illuminance']      # float, lux (only if units_val==2)
data['installed_power_density']  # float, W/m²/(100lux) (only if units_val==2)
data['dimming_profile']          # str — profile ID
data['variation_profile']        # str — profile ID
```

### RoomPeopleGain — get() Keys

```python
data = gain.get()
data['type_str']                 # 'People'
data['type_val']                 # int: 6=People
data['name']                     # str
data['occupancies']              # dict of floats: {0: m²/person value, 1: people value}
data['units_strs']               # dict: {0: 'm²/person', 1: 'people'}
data['units_val']                # int: 0=m²/person, 1=people
data['max_sensible_gains']       # dict of floats indexed by int
data['max_latent_gains']         # dict of floats indexed by int
data['diversity_factor']         # float
data['variation_profile']        # str — profile ID
```

---

## 13. VEThermalTemplate

### Accessing

```python
templates = project.thermal_templates(assigned=False)
# templates is a dict: {handle: VEThermalTemplate}
for handle, tmpl in templates.items():
    gains = tmpl.get_casual_gains()
    air_exs = tmpl.get_air_exchanges()
```

### Methods

```python
tmpl.add_air_exchange(airExchange)
tmpl.add_gain(casualGain)
tmpl.apply_changes()              # REQUIRED after modifying template data
tmpl.get() -> tuple               # (roomConditions, apSystems, casualGains, airExchanges)
tmpl.get_air_exchanges() -> list[AirExchange]
tmpl.get_apache_systems() -> dict
tmpl.get_casual_gains() -> list[CasualGain]
tmpl.get_room_conditions() -> dict
tmpl.remove_air_exchange(airExchange)
tmpl.remove_gain(casualGain)
tmpl.set(room_conditions, system_data)
tmpl.set_apache_systems(system_data: dict)
tmpl.set_room_conditions(room_conditions: dict)
```

### get_apache_systems() Keys

```python
sys = tmpl.get_apache_systems()
sys['HVAC_system']                   # str — HVAC system ID
sys['aux_vent_system']               # str — aux vent system ID
sys['aux_vent_system_same']          # bool
sys['dhw_system']                    # str — DHW system ID
sys['dhw_system_same']               # bool
sys['heating_capacity_unlimited']    # bool
sys['heating_capacity_value']        # float
sys['heating_capacity_units']        # int: -1=unlimited, 0=kW, 1=W/m²
sys['heating_plant_radiant_fraction']  # float
sys['cooling_capacity_unlimited']    # bool
sys['cooling_capacity_value']        # float
sys['cooling_capacity_units']        # int
sys['cooling_plant_radiant_fraction']  # float
sys['system_air_minimum_flowrate']   # float
sys['system_air_minimum_flowrate_units']  # int: 0=ach, 1=l/s, 2=l/s/m², 3=l/s/person
sys['system_air_free_cooling']       # float
sys['system_air_free_cooling_units'] # int
sys['system_air_variation_profile']  # str — profile ID
```

### Attributes

```python
tmpl.name      # str — template description
tmpl.standard  # VEThermalTemplate_standard enum
```

### Enums

```python
# VEThermalTemplate_standard: generic, NCM, PRM_FloridaECB, NECB, t24
# heating_cooling_capacity_unit: unlimited, kilowatts, watts_per_metre_squared
```

---

## 14. AirExchange

Used in `VEThermalTemplate`. Represents air exchange template data.

### Methods

```python
ae.get() -> dict
```

### get() Keys

```python
data = ae.get()
data['adjacent_condition_string']  # str
data['adjacent_condition_val']     # int: 1=ext, 2=ext+offset, 3=adjacent, 5=profile
data['max_flow']                   # float
data['name']                       # str
data['offset_temperature']         # float
data['temperature_profile']        # str — profile ID
data['type_str']                   # 'Infiltration' | 'Natural Ventilation' | 'Auxiliary ventilation'
data['type_val']                   # int: 0=Infiltration, 1=NatVent, 2=AuxVent
data['units_str']                  # 'ach' | 'l/s' | 'l/s/m²' | 'l/s/person' | 'l/(s.m² fac)'
data['units_val']                  # int: 0=ach, 1=l/s, 2=l/s/m², 3=l/s/person, 4=l/(s.m²fac)
data['variation_profile']          # str — profile ID
```

### Attributes

```python
ae.name   # str — descriptive string
```

### Enums

```python
# AdjacentCondition_type: external_air, external_air_and_offset_temp,
#                          from_adjacent_room, temperature_from_profile
# AirExchange_type: infiltration, mechanical_ventilation, natural_ventilation
```

---

## 15. CasualGain

Used in `VEThermalTemplate`. Three subclasses: `EnergyGain`, `LightingGain`, `PeopleGain`.

### Methods

```python
gain.get() -> dict
```

### EnergyGain — get() Keys

```python
data = gain.get()
data['energy_source']          # str — fuel name
data['max_latent_gain']        # float
data['max_power_consumption']  # float
data['max_sensible_gain']      # float
data['name']                   # str
data['radiant_fraction']       # float
data['type_str']               # 'Machinery' | 'Miscellaneous' | 'Cooking' | 'Computers'
data['type_val']               # EnergyGain_type enum
data['units_str']              # 'W/m²' | 'W'
data['units_val']              # int: 0=W/m², 1=W
data['variation_profile']      # str — profile ID
```

### LightingGain — get() Keys

```python
data = gain.get()
data['ballast']                # float
data['design_illuminance']     # float, lux
data['dimming_profile']        # str — profile ID
data['diversity_factor']       # float
data['energy_source']          # str
data['maximum_illuminance']    # float, lux
data['max_power_consumption']  # float
data['max_sensible_gain']      # float
data['minimum_illuminance']    # float, lux
data['name']                   # str
data['radiant_fraction']       # float
data['type_str']               # 'Fluorescent Lighting' | 'Tungsten Lighting'
data['type_val']               # LightingGain_type enum
data['units_str']              # 'W/m²' | 'W' | 'lux'
data['units_val']              # int: 0=W/m², 1=W, 2=lux
data['variation_profile']      # str
```

### PeopleGain — get() Keys

```python
data = gain.get()
data['diversity_factor']       # float
data['max_latent_gain']        # float, W
data['max_sensible_gain']      # float
data['name']                   # str
data['number_of_people']       # float (only if units_val==1)
data['occupancy_density']      # float (only if units_val==0)
data['type_str']               # 'People'
data['type_val']               # PeopleGain_type enum
data['units_str']              # 'm²/person' | 'people'
data['units_val']              # int: 0=m²/person, 1=people
data['variation_profile']      # str
```

### Attributes

```python
gain.name   # str — descriptive string
```

### Enums

```python
# EnergyGain_type: machinery, miscellaneous, cooking, computers,
#                  data_centre_equipment, refrigeration, process_equipment,
#                  local_fans, transformers, motors
# LightingGain_type: fluorescent, tungsten, general, task, display, process, unknown
# PeopleGain_type: people
```

---

## 16. VEProfile

### Accessing Profiles

```python
day_profiles, group_profiles = project.profiles()
# day_profiles: {profileID: VEProfile}
# group_profiles: {profileID: VEProfile}

for pid, profile in group_profiles.items():
    if profile.is_weekly():
        data = profile.get_data()   # list of daily profile IDs
    elif profile.is_yearly():
        data = profile.get_data()   # [[weeklyID, fromDay, toDay], ...]
```

### Methods

```python
profile.get_data() -> varies_by_type
profile.set_data(data) -> bool
profile.is_absolute() -> bool
profile.is_group() -> bool        # True if weekly/yearly/compact/freeform
profile.is_modulating() -> bool
profile.add_category(category)
profile.clear_category(category)
profile.get_categories() -> list[profile_category]
profile.set_categories(list[profile_category])
profile.is_supported_category(category) -> bool
profile.has_category(category) -> bool

# Group profile methods (weekly, yearly, compact, freeform):
profile.is_compact() -> bool
profile.is_freeform() -> bool
profile.is_weekly() -> bool
profile.is_yearly() -> bool

# Free form only:
profile.is_graphable() -> bool
profile.load_data(hide_ui=True)   # MUST call before accessing free form data
profile.save_data(hide_ui=True)
```

### Profile Data Structures

```python
# Daily profile data:
# [[x, y, formula], [x, y, formula], ...]
# x=time_of_day, y=value (0 if formula), formula=str ('' if no formula)

# Weekly profile data:
# [Monday, ..., Sunday, Holiday, Heating-Rm, Cooling-Rm,
#  Heating-Sys, Cooling-Sys]  # exactly 12 IDs in VE 2025

# Yearly profile data:
# [[weeklyProfileID, fromDay, toDay], ...]
# fromDay/toDay: 1-365

# Compact profile data:
# [[[toDay, toMonth], [desc, firstTime, secondTime], ...], ...]
# firstTime/secondTime: [True, startHr, startMin, endHr, endMin] OR [False, 0, 0]

# Free form profile data:
# [[month, day, hour, minute, value], ...]
# month:1-12, day:1-31, hour:0-23, minute:0-59
```

### Attributes

```python
profile.id         # str — profile ID
profile.reference  # str — profile name/reference
# CompactProfile only:
profile.num_periods  # int
```

### Enums

```python
# profile_category: none, occupancy, lighting, hvac, misc, ventilation,
#                   daylighting, equipment, solar, heating, cooling,
#                   plant, water, hvac_linked, emissions_factors
```

---

## 17. VEApacheSystem

### Accessing

```python
systems = project.apache_systems()
for system in systems:
    heating = system.heating()
    cooling = system.cooling()
```

### Methods

```python
system.air_supply() -> dict
system.apply_ncm()
system.auxiliary_energy(show_ncm=False) -> dict
system.bivalent_systems_ncm() -> dict
system.control() -> dict          # {'master_zone': room_id_string}
system.cooling(show_ncm=False) -> dict
system.cooling_ncm() -> dict
system.general_ncm() -> dict
system.heating(show_ncm=False) -> dict
system.heating_ncm() -> dict
system.hot_water(show_ncm=False) -> dict
system.metering_provision_ncm() -> dict
system.set_air_supply(data: dict)
system.set_auxiliary_energy(data: dict)
system.set_bivalent_systems_ncm(data)
system.set_control(control_id)
system.set_cooling(data: dict)
system.set_cooling_ncm(data: dict)
system.set_default(system_id)
system.set_general_ncm(data: dict)
system.set_heating(data: dict)
system.set_heating_ncm(data: dict)
system.set_hot_water(data: dict)
system.set_metering_provision_ncm(data: dict)
system.set_name(name: str)
system.set_solar_water_heating(data: dict)
system.set_solar_water_heating_ncm(data: dict)
system.set_system_adjustment_ncm(data: dict)
system.set_system_controls_ncm(data: dict)
system.set_ventilation_ncm(data: dict)
system.solar_water_heating() -> dict
system.solar_water_heating_derived() -> dict
system.solar_water_heating_ncm() -> dict
system.system_adjustment_ncm() -> dict
system.system_controls_ncm() -> dict
system.ventilation_ncm() -> dict
```

### Static Methods

```python
VEApacheSystem.default() -> str          # ID of default Apache system
VEApacheSystem.fuel_name(fuel_id) -> str
VEApacheSystem.meter_name(fuel_id, meter_branch) -> str
```

### air_supply() Keys

```python
data = system.air_supply()
data['condition']             # int — supply condition
data['cooling_max_flow']      # float, l/s
data['OA_max_flow']           # float, l/s
data['profile']               # str (only if condition == 1)
data['temperature_difference']  # float, K (0 = no sizing)
```

### heating() Keys

```python
data = system.heating()
data['del_eff']              # float — delivery efficiency
data['fuel']                 # int — fuel type
data['gen_seasonal_eff']     # float — seasonal efficiency
data['gen_size']             # float, kW
data['HR_effectiveness']     # float — heat recovery effectiveness
data['HR_return_temp']       # float, °C
data['Is_heat_pump']         # bool
data['meter_cef']            # float, kgCO2/kWh
data['meter_pef']            # float
data['SCoP']                 # float, kW/kW — seasonal COP
data['used_with_CHP']        # bool
```

### cooling() Keys

```python
data = system.cooling()
data['cool_vent_mechanism']   # int — see cooling_mech_names()
data['del_eff']               # float
data['free_cooling']          # cmm_free_cooling enum
data['fuel']                  # int (only if not absorption chiller)
data['gen_size']              # float, kW
data['has_absorption_chiller']  # bool
data['nominal_eer']           # float, kW/kW
data['pump_and_fan_power_perc']  # float
data['SEER']                  # float, kW/kW
data['SSEER']                 # float, kW/kW
```

### Attributes

```python
system.id     # str — Apache system ID
system.name   # str — Apache system name
```

### Enums

```python
# AuxEnergyMethod_type: SFPs, SFPs_with_min_AEV, SFPs_and_AEV, AEV
# cmm_free_cooling: not_a_cmm_system, natural_ventilation, mechanical_ventilation
# Conditioning_type: external_air, temperature_from_schedule
# CoolingMechanism_type: air_conditioning, mechanical_ventilation, natural_ventilation
# dhw_parent_type: unset, dedicated_dhw_boiler, standalone_water_heater,
#                  instantaneous_dhw_only, instantaneous_combi, heat_pump
# SolarHeating_type: none, flat, parabolic
# fuel_type: anthracite, biogas, biomass, coal, district_heating, dual, elec,
#             grid_displaced_elec, lpg, misc_a...misc_z, nat_gas, none, oil,
#             smokeless, waste, grid_displaced_pv
```

---

## 18. ApacheSim

### Usage

```python
sim = iesve.ApacheSim()
sim.show_simulation_dialog()   # Opens dialog, returns True if simulation ran

# Or programmatic:
sim.set_options({'results_filename': 'my_results.aps'})
sim.run_simulation()
```

### Methods

```python
sim.get_options() -> dict
sim.reset_options() -> bool
sim.run_compliance_simulation() -> bool   # Uses Parallel Simulation Manager
sim.run_room_zone_loads()
sim.run_loads_sizing()
sim.run_simulation(queue_to_tasks=False) -> bool
sim.set_hvac_network(network_name: str)
sim.set_options({options}) -> bool
sim.show_simulation_dialog() -> bool
sim.stitch(output_file_path: str, files_to_stitch: list)
```

### get_options() / set_options() Keys

```python
# Basic timing:
'aux_ventilation'        # bool, default True
'cooling_end_month'      # int, 1-12
'cooling_start_month'    # int, 1-12
'end_day'                # int, 1-31
'end_month'              # int, 1-12
'start_day'              # int, 1-31
'start_month'            # int, 1-12
# HVAC:
'HVAC'                   # bool
'HVAC_filename'          # str
# Simulation settings:
'macroflo'               # bool (required for opening-level results)
'nat_ventilation'        # bool, default True
'preconditioning_days'   # int, 0-365
'radiance'               # bool
'reporting_interval'     # int: 0=6min, 1=10min, 2=30min, 3=60min
'results_filename'       # str (file placed in Vista folder)
'simulation_timestep'    # int: 0=1min, 1=2min, 2=6min, 3=10min, 4=30min
'suncast'                # bool
'suncast_filename'       # str
# Output options (all rooms):
'output_conduction_gains'         # bool, default False
'output_HVAC_components'          # bool, default False
'output_HVAC_systems'             # bool, default True
'output_latent_internal_gains'    # bool, default False
'output_latent_ventilation_gains' # bool, default False
'output_sensible_internal_gains'  # bool, default True
'output_standard_outputs'         # bool, default True
# Detailed output (specific rooms only):
'detailed_conduction_gains'       # bool
'detailed_convective_gains'       # bool, default True
'detailed_external_solar'         # bool
'detailed_HVAC_systems'           # bool, default True
'detailed_internal_solar'         # bool
'detailed_latent_internal_gains'  # bool, default True
'detailed_latent_ventilation_gains'  # bool, default True
'detailed_microflo'               # bool, default True
'detailed_rooms'                  # list[str] — room IDs
'detailed_sensible_internal_gains'  # bool, default True
'detailed_standard_outputs'       # bool, default True
'detailed_surface_temps'          # bool, default True
```

### Enums

```python
# time_step: one_minute, two_minutes, six_minutes, ten_minutes, thirty_minutes
# reporting_interval: six_minutes, ten_minutes, thirty_minutes, sixty_minutes
```

---

## 19. ResultsReader

**The core interface for reading Apache simulation results (APS files).**

### Opening an APS File

```python
# Pattern 1: Static call (most common — used in BR18 reference scripts)
rf = iesve.ResultsReader.open(aps_file_name)
# aps_file_name is just the filename (e.g., 'my_results.aps')
# NOT the full path — the VE looks in the Vista folder automatically

# Pattern 2: Instantiate first
rf = iesve.ResultsReader()
rf.open_aps_data(aps_file_name)  # Returns 1 on success

# Always close when done:
rf.close()
```

### Variable Levels (Model Level Flags)

| Flag | Level | Reading Method |
|------|-------|----------------|
| `'w'` | Weather | `get_weather_results()` |
| `'z'` | Room/Zone level | `get_room_results()` |
| `'v'` | Apache systems misc | `get_apache_system_results()` |
| `'j'` | Apache systems energy | `get_apache_system_results()` |
| `'r'` | Apache systems carbon | `get_apache_system_results()` |
| `'l'` | Building loads | `get_results()` |
| `'e'` | Building energy | `get_results()` |
| `'c'` | Building carbon | `get_results()` |
| `'s'` | Surface level | `get_surface_results()` |
| `'o'` | Opening level | `get_opening_results()` |
| `'n'` | HVAC node level | `get_hvac_node_results()` |
| `'h'` | HVAC component level | `get_hvac_component_results()` |

### Primary Result Reading Methods

```python
# Room-level results (most commonly used):
rf.get_room_results(room_id, aps_var, vista_var, var_level,
                    start_day=-1, end_day=-1) -> numpy.ndarray
# Example:
temps = rf.get_room_results(room_id, 'Comfort temperature',
                            'Dry resultant temperature', 'z').tolist()
occupancy = rf.get_room_results(room_id, 'Number of people',
                                'Number of people', 'z').tolist()

# Model-level results:
rf.get_results(aps_var, vista_var, var_level,
               start_day=-1, end_day=-1) -> numpy.ndarray

# Weather results:
rf.get_weather_results(aps_var, vista_var,
                       start_day=-1, end_day=-1) -> numpy.ndarray

# Surface results:
rf.get_surface_results(room_id, aps_handle, aps_var, vista_var,
                       start_day=-1, end_day=-1) -> numpy.ndarray
# aps_handle: from surface.get_properties()['aps_handle']

# Opening results (requires macroflo in simulation):
rf.get_opening_results(room_id, surface_index, opening_index, aps_var, vista_var,
                       start_day=-1, end_day=-1) -> numpy.ndarray

# Apache system results:
rf.get_apache_system_results(system_id, aps_var, vista_var, var_level,
                             start_day=-1, end_day=-1) -> numpy.ndarray

# HVAC component results:
rf.get_hvac_component_results(component_id, component_type, var_name,
                              start_day=-1, end_day=-1) -> numpy.ndarray

# HVAC node results:
rf.get_hvac_node_results(node_nr, layer_nr=-1, var_name='',
                         start_day=-1, end_day=-1) -> numpy.ndarray

# Peak results at room level:
rf.get_peak_results(roomID, [variables]) -> dict
# variables: list of APS variable name strings
```

### "get_all_" Variants (return dict of numpy arrays, keyed by display name)

```python
rf.get_all_room_results(room_id, aps_var, var_level,
                        start_day=-1, end_day=-1) -> dict
rf.get_all_results(aps_var, var_level, start_day=-1, end_day=-1) -> dict
rf.get_all_weather_results(aps_var, start_day=-1, end_day=-1) -> dict
rf.get_all_apache_system_results(system_id, aps_var, var_level,
                                 start_day=-1, end_day=-1) -> dict
rf.get_all_surface_results(room_id, aps_handle, aps_var,
                           start_day=-1, end_day=-1) -> dict
rf.get_all_opening_results(room_id, surface_index, opening_index, aps_var,
                           start_day=-1, end_day=-1) -> dict
rf.get_all_component_process_results(room_id, index_in_room, aps_var, var_level,
                                     start_day=-1, end_day=-1) -> dict
rf.get_all_process_results(process_name, aps_var, start_day=-1, end_day=-1) -> dict
```

### Discovery Methods

```python
# Get all rooms in results file:
rf.get_room_list() -> list
# Returns: [(room_name, room_id, room_area, room_volume), ...]

rf.get_room_ids() -> list[str]   # Just room IDs

rf.get_room_geometry_details(room_id) -> dict
# Returns: opaque, glazed, internal_wall, external_wall, internal_glazed,
#          num_open, num_surf, external_glazed, rooflight, door, floor,
#          ground_floor, ceiling, roof (all in m²)
# Pass list of IDs to get list of dicts instead

rf.get_conditioned_sizes() -> tuple   # (area, volume, number_of_rooms)

rf.get_variables() -> list[dict]
# Each dict: {aps_varname, display_name, model_level, units_type}
# Use aps_varname for ALL ResultsReader function calls (NOT display_name!)

rf.get_units() -> dict
# {unit_type: {units_IP: {divisor, offset, display_name},
#              units_metric: {divisor, offset, display_name}}}

rf.get_apache_systems() -> list
# [(system_name, system_id), ...]

rf.get_component_objects() -> list
# [(room_id, index_in_room, component_name, [(var_name, var_unit, var_level)]), ...]

rf.get_process_list() -> list[str]
rf.get_process_variables(process) -> list   # [(name, units), ...]
rf.get_data_file_details(filename, date_time_format) -> dict
rf.get_unmet_hours() -> dict  # {'cooling': ..., 'heating': ...}
```

### Energy Methods

```python
rf.get_energy_uses(used_only=True) -> dict
# {id: {id, name, tied_source_id, used}}

rf.get_energy_sources(used_only=True) -> dict
# {id: {cef, id, name, used}}

rf.get_energy_meters(used_only=True) -> dict
# {id: {has_subs, id, name, parent_id, source_id, used}}

rf.get_energy_results(
    use_id=iesve.ResultsReader.EnergyUse.unspecified,
    source_id=iesve.ResultsReader.EnergySource.unspecified,
    meter_id=iesve.ResultsReader.EnergyMeter.unspecified,
    type='e',           # 'e'=energy(W), 'c'=carbon(kgC)
    add_subs=-1,        # -1=default, 1=include sub-meters, 0=exclude
    start_day=-1,
    end_day=-1
) -> numpy.ndarray or None
# Examples:
# get_energy_results()                                       → Total Energy
# get_energy_results(source_id=elec)                        → Electricity
# get_energy_results(use_id=prm_space_heating)              → Space Heating

rf.get_energy_results_ex(
    use_ids=None,       # None, single id, or list of ids
    source_ids=None,    # None, single id, or list of ids
    type='e',
    start_day=-1,
    end_day=-1
) -> numpy.ndarray or None
```

### Attributes (APS File Properties)

```python
rf.first_day              # int — first simulation day with results (1=Jan 1)
rf.last_day               # int — last simulation day with results (365=Dec 31)
rf.results_per_day        # int — number of result timesteps per 24h
rf.plot_data_offset_secs  # int — plot data offset in seconds
rf.weather_file           # str — weather file used for simulation
rf.hvac_file              # str — HVAC network file used
rf.plot_year              # int
rf.simulation_year        # int
rf.first_weekday_plot_year  # int — day-of-week of Jan 1 (Sun=1)
```

### Enums

```python
# EnergyUse: unspecified, prm_interior_lighting, prm_exterior_lighting,
#             prm_space_heating, prm_space_cooling, prm_pumps,
#             prm_heat_rejection, prm_fans_interior_central,
#             prm_fans_interior_local, prm_fans_garage, prm_fans_exhaust,
#             prm_fans_process, prm_services_water_heating,
#             prm_receptacle_equipment, prm_interior_lighting_process,
#             prm_refrigeration, prm_data_center_equipment, prm_cooking,
#             prm_elevators_escalators, prm_other_process, prm_humidification,
#             prm_chp, prm_elec_gen_chp, prm_elec_gen_wind, prm_elec_gen_pv,
#             prm_transformer, prm_motor, prm_interior_lighting_unregulated
# EnergySource: unspecified, elec, nat_gas, oil, coal, misc_a, misc_b,
#                none, lpg, biogas, biomass, waste, misc_c...misc_z,
#                district_heating, grid_disp_elec, grid_disp_elec_pv
# EnergyMeter: unspecified
# VariableSource: system, project
# VariableType: standard, derived, process, energy_meter
```

### HVAC Component Type IDs (for get_hvac_component_results)

```python
# 1  = HVACRoom
# 2  = HVACHeatingCoil (simple)
# 3  = HVACCoolingCoil (simple)
# 4  = HVACSprayChamber
# 5  = HVACSteamHumidifier
# 7  = HVACJunction
# 8  = HVACDuct
# 10 = HVACAirToAirHeatEnthalpyExchanger
# 13 = HVACBoiler (part load)
# 14 = HVACPLCChiller
# 15 = HVACFan
# 16 = HVACDamper
# 18 = HVACUnitaryCoolingSystem
# 19 = HVACDedicatedWatersideEconomizer
# 20 = HVACEWCChiller
# 21 = HVACEnhancedBoiler (hot water)
# 23 = HVACEACChiller
# 24 = HVACDXCoolingInstance
# 25 = HVACCoolingCoil (advanced)
# 26 = HVACChilledWaterLoop
# 27 = HVACHeatingCoil (advanced)
# 28 = HVACHotWaterLoop
# 29 = HVACGenericHeatSource
# 30 = HVACHeatPump (air-water)
# 31 = HVACHeatPump (air-air)
# 32 = HVACSolarWaterHeater
# 33 = HVACHeatTransferLoop
# 34 = HVACWaterAirHeatPump
# 35 = HVACGenericCoolingSource
# 36 = HVACRadiatorRoom
# 37 = HVACChilledCeiling
# 38 = HVACCondenserWaterLoop
# 39 = HVACCoolingTower
# 40 = HVACDryFluidCooler
# 41 = HVACPreCoolingLoop
# 42 = HVACWaterSourceLoop
# 43 = HVACWaterWaterHeatExchanger
# 44 = HVACPCMBattery
# 45 = HVACPump
# 50 = HVACSolarAirCollectorBIST
# 51 = HVACAirFilter
# 52 = HVACPlenum
# 53 = HVACThermalStorageLoop
# 54 = HVACThermalStorageTank
```

---

## 20. RoomGroups

Interface for Room Groups and HVAC Zones.

### Instantiation

```python
room_groups = iesve.RoomGroups()
```

### Grouping Scheme Methods

```python
room_groups.get_grouping_schemes() -> list[dict]
# Each dict: {'handle': int, 'name': str}

room_groups.create_grouping_scheme(name: str) -> int   # Returns handle

room_groups.get_room_groups(scheme_handle: int) -> list[dict]
# Each dict: {
#   'colour': tuple(R, G, B),  # each 0-255
#   'handle': int,
#   'name': str,
#   'rooms': list[str]         # list of room IDs
# }

room_groups.create_room_group(scheme_handle, group_name,
                               colour=(0,0,0)) -> int  # Returns handle

room_groups.assign_rooms_to_group(scheme_handle, group_handle,
                                   [room_ids])  # list of str or VEBody objects
```

### HVAC Zone Methods

```python
room_groups.get_zone_groups() -> list[dict]
# Each dict: {'name': str, 'id': str}

room_groups.get_zones(zone_group_id: str) -> list[dict]
# Each dict: {'name': str, 'id': str,
#             'rooms': list[str], 'master_room': str}

room_groups.create_zone_group(name: str) -> str    # Returns zone group ID
room_groups.create_zone(zone_group_id: str, zone_name: str) -> str  # Returns zone ID
room_groups.assign_rooms_to_zone(zone_id)
```

---

## 21. VELocate

### Usage

```python
locator = iesve.VELocate()
locator.open_wea_data()   # Returns -1 on failure
location = locator.get()
locator.save_and_close()
```

### Methods

```python
locator.close_wea_data() -> None
locator.get() -> dict
locator.open_wea_data() -> int     # -1=failure, else success
locator.save_and_close() -> None
locator.set(data: dict) -> None
locator.set_max_dry_bulb(temperature: float, month)
locator.set_max_wet_bulb(temperature: float, month)
locator.set_min_dry_bulb(temperature: float, month)
```

### get() / set() Keys

```python
data = locator.get()
data['altitude']                    # float, m
data['city']                        # str
data['country']                     # str
data['dst_correction']              # float
data['dst_from_month']              # float, 1-12
data['dst_to_month']                # float, 1-12
data['external CO2']                # float, ppm  (note: space in key)
data['ground_reflectance_summer']   # float
data['ground_reflectance_winter']   # float
data['ground_reflectance_summer_from_month']  # float, 1-12
data['ground_reflectance_summer_to_month']    # float, 1-12
data['heating_loads percentile']    # float, % (note: space in key)
data['cooling_loads percentile']    # float, % (note: space in key)
data['latitude']                    # float, degrees
data['longitude']                   # float, degrees
data['national_climate_zone']       # int or str
data['summer_drybulb']              # float, °C
data['summer_wetbulb']              # float, °C
data['winter_drybulb']              # float, °C
data['time_zone']                   # float
data['weather_ source']             # str (note: space in key)
data['weather_file']                # str — weather file path
```

### Enums

```python
# design_weather_source: ashrae, custom, apl, user
# month: january, february, march, april, may, june, july,
#        august, september, october, november, december
```

---

## 22. WeatherFileReader

### Usage

```python
wea = iesve.WeatherFileReader()
result = wea.open_weather_file('WashingtonTMY2.fwt')
if result > 0:
    dry_bulb = wea.get_results(3, 1, 365)   # variable=3=dry bulb, all year
wea.close()
```

### Methods

```python
wea.open_weather_file(filename: str) -> int   # > 0 = success, ≤ 0 = error
wea.close()
wea.get_results(variable, start_day, end_day) -> numpy.ndarray
# variable: int or weather_variable enum, start_day/end_day: 1-365
```

### Weather Variables

| ID | Variable | Units |
|----|----------|-------|
| 1 | Cloud cover | Oktas |
| 2 | Wind direction [E of N] | Degrees |
| 3 | Dry bulb temperature | °C |
| 4 | Wet bulb temperature | °C |
| 5 | Direct normal radiation | W/m² |
| 6 | Diffuse horizontal radiation | W/m² |
| 7 | Solar altitude | Degrees |
| 8 | Solar azimuth | Degrees |
| 9 | Atmospheric pressure | Pa |
| 10 | Wind speed | m/s |
| 11 | Relative humidity | % |
| 12 | Humidity ratio (moisture content) | kg/kg |
| 13 | Global radiation | W/m² |
| 14 | Dew point temperature | °C |
| 15 | Running-mean temperature | °C |
| 16 | Max-adaptive temperature | °C |

### Attributes

```python
wea.feb29          # bool — True if leap year
wea.lat            # float — latitude
wea.long           # float — longitude
wea.site           # str — site description
wea.solar_rad_convention  # str
wea.start_weekday  # str — first day of year
wea.time_convention  # str
wea.time_zone      # float — hours ahead of GMT
wea.year           # int — data start year
```

---

## 23. VECdbConstruction

Construction database interface.

### Methods

```python
cdb_const.add_layer(material_id, is_cavity)
cdb_const.delete_layer(layer_id)
cdb_const.get_default_resistances()
cdb_const.get_g_values() -> dict       # bs_en_410, building_regulations, bfrc
cdb_const.get_layers() -> list
cdb_const.get_properties(u_value_types=None) -> dict
cdb_const.get_review_summary_string() -> str
cdb_const.get_u_factor(uvalue_types) -> float
cdb_const.insert_layer(layer_id, insert_before)
cdb_const.set_const_class(construction_class)
cdb_const.set_f_factor(ffactor)
cdb_const.set_properties(properties: dict)
```

### set_properties() Keys (selection of key properties)

```python
# Glazing:
'g_value', 'glazing_type', 'light_transmittance', 'visible_light_transmittance'
# Shading:
'external_shade_active', 'external_shade_code', 'external_shade_day_resistance'
'internal_shade_active', 'internal_shade_code'
# Frame:
'frame_percent', 'frame_type', 'frame_material', 'frame_resistance'
# Surface properties:
'inside_surface_emissivity', 'outside_surface_emissivity'
'inside_surface_resistance', 'outside_surface_resistance'
# Bridging:
'thermal_bridging_coefficient'
```

### Attributes

```python
cdb_const.category       # CDB construction category
cdb_const.c_factor       # float (ASHRAE only)
cdb_const.f_factor       # float
cdb_const.id             # str — construction ID
cdb_const.is_editable    # bool
cdb_const.opaque         # bool
cdb_const.reference      # str — description
cdb_const.regulation     # int: 0=CIBSE, 1=EN_ISO, 2=ASHRAE901, 3=ASHRAE901, 4=T24
```

### Enums (VECdbProject / VECdbConstruction)

```python
# construction_class: none, opaque, glazed, hard_landscaping, soft_landscaping, shade, misc
# element_categories: roof, ceiling, wall, partition, ground_floor, roof_light,
#                     ext_glazing, int_glazing, door, int_floor, ...
# uvalue_types: cibse, iso, ashae, t24
# glazing_types: none, single_glazed, double_glazed_air_or_argon_filled,
#                double_glazed_low_e_hard_coat, double_glazed_low_e_soft_coat,
#                triple_glazed_air_or_argon_filled, triple_glazed_low_e_hard_coat,
#                triple_glazed_low_e_soft_coat
# standard: generic, cibse, ashrae_general, ashrae_901, t24, ncm, sbem, nz, gm, bre, monodraught
```

---

## 24. VECdbDatabase / VECdbProject / VECdbLayer / VECdbMaterial

```python
# Database access:
db = iesve.VECdbDatabase.get_current_database()  # static
projects = db.get_projects()  # {0: [project_type='Project'], 1: [System], 2: [Manufacturer]}

# Project access:
project = projects[0][0]   # first project of type 'Project'
construction_ids = project.get_construction_ids(
    iesve.VECdbProject.construction_class.none)  # none = all classes
construction = project.get_construction(construction_id,
    iesve.VECdbProject.construction_class.none)

# Layer access (from construction):
layers = construction.get_layers()
for layer in layers:
    layer_props = layer.get_properties()   # resistance, thickness, convection_coefficient
    material_str = layer.get_material(is_opaque=True)

# Material access:
material_ids = project.get_material_ids(
    iesve.VECdbProject.material_categories.all)
material = project.get_material(material_id)
mat_props = material.get_properties()
# mat_props keys: conductivity, density, thickness, specific_heat_capacity,
#                 transmittance, vapour_resistivity, description, ...
```

---

## 25. EnergySources

```python
# Static methods (no instantiation needed):
sources = iesve.EnergySources.get_all_energy_source_data()
# Returns list of dicts: [{carbon_emissions_factor, fuel_code, id, name, source_energy_factor}]

source = iesve.EnergySources.get_energy_source_data_by_id(id)

meter = iesve.EnergySources.get_energy_meter(source_id, meter_id)
# Returns VEEnergyMeter
```

---

## 26. VEEnergyMeter

```python
meter.get() -> dict
# Dict entries: name, source_data, id
```

---

## 27. VERenewables

```python
renewables = iesve.VERenewables()

# CHP:
chp_data = renewables.get_chp_data() -> dict
# Keys: electrical_generation_meter, is_enabled, min_fraction_rated_heat_output,
#       min_power_efficiency, min_thermal_efficiency, profile, quality_index,
#       rated_heat_output, rated_power_efficiency, rated_thermal_efficiency, source_meter

# PV:
pv_list = renewables.get_pv_data() -> list[dict]
pv_data = renewables.get_pv_data_by_id(id) -> dict
pv_type = renewables.get_pv_type_by_id(id) -> dict
pv_types = renewables.get_pv_types() -> list[dict]
# PV dict keys: area, azimuth, cell_efficiency, cell_surface, description,
#               geometric_concentration, id, inclination, linear_temperature_factor,
#               meter, num_cells, optical_efficiency, power_temperature_coefficient,
#               shading_factor, spectral_factor, tracking_device_power_losses,
#               tracking_error, type_id

# Wind:
wind_data = renewables.get_wind_data() -> dict
# Keys: hub_height, is_enabled, meter, rated_power

# Set methods:
renewables.set_chp_data(data: dict)
renewables.set_pv_data(data: dict, id)
renewables.set_pv_type_data(data: dict, id)
renewables.set_wind_data(data: dict)
```

---

## 28. VEMacroFlo

```python
macroflo = iesve.VEMacroFlo()
openings = macroflo.get() -> list[dict]
# Each dict: crack_flow_coefficient, crack_length, description,
#            equivalent_orifice_area, exposure_type, openable_area,
#            opening_category, opening_threshold, profile, reference_id
macroflo.set(data: dict)
macroflo.reload_wind_coefficients()
```

### Enums

```python
# opening_type: custom_sharp_edge_orifice, window_door_side_hung, window_centre_hung,
#               window_top_hung, window_bottom_hung, parallel_hung_windows_flaps,
#               window_sash, sliding_roller_door, louvre, grille, duct, acoustic_duct
```

---

## 29. VESuncast

```python
suncast = model.suncast()
suncast.run(from_month, to_month, design_day, use_diffuse)
results = suncast.get_results(shading_filename, body_index, surface_index,
                               surface_id, opening_num=0)
# Returns list of lists of dicts, each: {external, external_pc, internal, internal_pc}

sun_times = suncast.get_sun_up_down() -> list[dict]
# Each dict: {date, down_azi, down_time, up_azi, up_time}

altitudes = suncast.get_solar_altitudes(shading_filename, design_day) -> list
```

---

## 30. VESankey

```python
sankey = iesve.VESankey('depth')   # 'depth' = depth-first node sorting
sankey.add_column_names(['col1', 'col2', 'col3'])
sankey.add_node_names_in_order(['Node A', 'Node B', 'Node C'])
sankey.add_node_columns({'Node A': 0, 'Node B': 1, 'Node C': 2})
sankey.add_node_colours({'Node A': (255, 0, 0), 'Node B': (0, 255, 0)})
sankey.add_connections([('Node A', 'Node B', 100.0),
                         ('Node B', 'Node C', 80.0)])
sankey.set_title('Energy Flow')
sankey.set_units_str('kWh')
sankey.set_weight_width_ratio(ratio)
ratio = sankey.recommended_ratio()
sankey.generate_sankey()
sankey.save_svg('output.svg')
sankey.save_png('output.png')
sankey.clear()   # Clear for reuse
```

---

## 31. VEComponentProcess

```python
processes = body.get_processes()
for proc in processes:
    name = proc.get_name() -> str
    sys_inputs = proc.get_system_inputs() -> list[dict]
    waste_heats = proc.get_waste_heats() -> list[dict]
    mat_inputs = proc.get_material_inputs() -> list[dict]
    mat_outputs = proc.get_material_outputs() -> list[dict]
    energy_inputs = proc.get_energy_inputs() -> list[dict]
    heat_outputs = proc.get_heat_outputs() -> list[dict]
    misc = proc.get_miscellaneous() -> list[dict]
    product = proc.get_product() -> str
```

---

## 32. HVAC Network Classes

### Loading the Network

```python
network = iesve.HVACNetwork.load_network(network_name)
# Or as instance method on existing network object
```

### HVACNetwork Attributes

```python
network.chilled_water_loop_ids   # list[str]
network.chilled_water_loops      # list[HVACChilledWaterLoop]
network.components               # list[HVACComponent]
network.controllers              # list[HVACController]
network.dhw_systems              # list[HVACDHWSystem]
network.generic_heat_sources     # list[HVACGenericHeatSource]
network.hot_water_loop_ids       # list[str]
network.hot_water_loops          # list[HVACHotWaterLoop]
network.multiplexes              # list[HVACMultiplex]
network.name                     # str
network.non_master_rooms         # list[str] — non-master room IDs in HVAC zones
network.path                     # str
network.systems                  # list[HVACPrototypeSystem]
network.systems_dict             # dict[system_id: HVACPrototypeSystem]
network.vrf_systems              # list[HVACVRFSystem]
```

### HVACNetwork Methods

```python
network.get_component_by_id(id) -> HVACComponent
network.get_controller_by_id(id) -> HVACController
network.get_multiplex_by_id(id) -> HVACMultiplex
network.get_multiplex_on_prototype_system(system_id) -> HVACMultiplex
network.get_system_by_id(system_id) -> HVACPrototypeSystem
network.is_updated_post_sizing(system_id) -> bool
network.has_t24_non_compliant_systems(sys_classification) -> bool
```

### HVACPrototypeSystem Methods

```python
system = network.get_system_by_id(system_id)
system.get_cooling_design_load(layer_number) -> float
system.get_heating_design_load(layer_number) -> float
system.get_cooling_design_load_per_area(layer_number) -> float
system.get_heating_design_load_per_area(layer_number) -> float
system.get_cooling_max_primary_airflow(layer_number) -> float
system.get_heating_max_primary_airflow(layer_number) -> float
system.get_node_data() -> dict
system.get_peak_data(layer_number) -> dict
system.get_room_cooling_peak_month(layer_number) -> str
system.get_room_cooling_peak_time(layer_number) -> str
system.get_room_heating_peak_month(layer_number) -> str
system.get_room_heating_peak_time(layer_number) -> str
system.get_room_id_for_umlh(layer_number) -> str
system.get_room_occupancy_data() -> dict
system.get_room_or_zone(layer_number) -> HVACRoom | HVACZone | None
system.get_space_id(layer_number) -> str
system.get_space_ids(layer_number) -> list
system.get_system_configuration_option() -> SystemConfigurationOptions
system.get_system_parameters() -> SystemParameters
```

### HVACPrototypeSystem Attributes

```python
system.components          # list[HVACComponent]
system.controllers         # list[HVACController]
system.is_sizing_enabled   # bool
system.is_valid            # bool
system.multiplex           # HVACMultiplex
system.number_of_layers    # int
system.standard            # str
system.system_type         # HVACPrototypeSystemType enum
```

### SystemParameters Methods

```python
sp = system.get_system_parameters()
schedules = sp.get_schedules() -> dict
sys_params = sp.get_system_parameters(layer_number) -> dict
zone_temp_humid = sp.get_zone_temperature_humidity_equipment(layer_number) -> dict
zone_vent = sp.get_zone_ventilation_exhaust(layer_number) -> dict
zone_loads = sp.get_zone_loads_airflows() -> dict
zone_airflows = sp.get_zone_airflows_turndown_engineering(layer_number) -> dict
zone_dist = sp.get_zone_airflow_distribution(layer_number) -> dict
```

### Key HVAC Component Attributes

```python
# HVACAbstractBoiler:
boiler.output_capacity         # float
boiler.oversizing_factor       # float
boiler.distribution_losses     # float
boiler.model_type              # HVACBoilerType enum

# HVACAbstractChiller:
chiller.chiller_type           # HVACChillerType enum
chiller.output_capacity        # float

# HVACElectricChiller:
elec_chiller.cop               # float — design COP
elec_chiller.iplv              # float — integrated part load value
elec_chiller.min_part_load_ratio  # float

# HVACFan:
fan.design_fan_power           # float
fan.design_flow_rate           # float
fan.is_variable_air_volume     # bool

# HVACHeatPump:
hp.heat_pump_type              # HVACHeatPumpType enum
hp.performance                 # dict: {source_temperature, cop, max_output}

# HVACZone:
zone.rooms                     # list[HVACRoom]
zone.room_ids                  # list[str]
zone.zone_id                   # str
```

### Key HVAC Enums

```python
# HVACBoilerType: hot_water_boiler, part_load_curve_boiler
# HVACChillerType: CoolingChiller, DischargeChiller, ElectricAirCooled,
#                  ElectricWaterCooled, PartLoadCurve
# HVACHeatPumpType: air_source_heat_pump, air_water_heat_pump, air_air_heat_pump
# HVACPrototypeSystemType: prm_system_1 ... prm_system_10, actimass_system, ...
# HeatingSourceSystemType: heating_system_generic, heating_system_hot_water_loop,
#                           heating_system_aa_heat_pump, heating_system_wa_heat_pump,
#                           heating_system_heat_transfer_loop, heating_system_electric,
#                           heating_system_vrf, heating_system_aa_heat_pump_advanced
# HVACCoolingSourceSystemType: legacy, chilled_water_loop, unitary_cooling,
#                               waterside_economizer, direct_expansion,
#                               water_air_heat_pump, generic_cooling_source,
#                               variable_refrigerant_flow, aa_heat_pump_advanced
# SystemConfigurationOptions: package_thermal_unit, single_zone_system,
#                              multi_zone_doas, multi_zone_ahu
```

---

## 33. ProjectInfo

```python
proj_info = iesve.ProjectInfo()
data = proj_info.get() -> dict
# Keys: address, building_owner, conditioned_floor_area,
#       design_team, energy_analyst, project_name
proj_info.set(data: dict)
```

---

## 34. Mv2 (Model Viewer 2)

```python
mv2 = iesve.Mv2()
mv2.take_snapshot(file_name='Snapshot', path='', view_mode=iesve.Mv2.mv2_viewmode.shaded,
                  components=False)
mv2.take_snapshot_or_create_blank_image(file_name='Snapshot', path='',
                                         view_mode=iesve.Mv2.mv2_viewmode.shaded,
                                         components=False)
```

### Enums

```python
# mv2_viewmode: shaded, textured, hidden_line, xray, component
```

---

## 35. Available Third-Party Libraries

| Library | Version | Use |
|---------|---------|-----|
| `numpy` | 1.11.0 | Array math, results processing |
| `scipy` | 0.17.0 | Scientific computation |
| `pandas` | 0.18.1 | DataFrames |
| `matplotlib` | 1.5.1 | Plotting (file output only) |
| `xlsxwriter` | 0.7.3 | **Required** for Excel output |
| `xlrd` | 0.9.4 | Read Excel files |
| `docx` | 0.8.5 | Word documents |
| `tkinter` | stdlib | GUI dialogs |
| `lxml` | 3.4.4 | XML read/write |
| `pywin32` | 219 | Windows COM |
| `CoolProp` | 5.1.1 | Thermodynamic properties |
| `reportlab` | 3.2 | PDF creation |
| `jinja2` | 2.8 | Templates |
| `Pillow` | 3.0.0 | Image processing |
| `pint` | 0.7.1 | Unit conversion |
| `requests` | 2.9.1 | HTTP requests |
| `bokeh` | 0.10.0 | HTML plotting (file only) |
| `arrow` | 0.7.0 | Date/time |
| `seaborn` | 0.7.0 | Plot formatting |
| `numexpr` | 2.4.6 | Fast numpy evaluation |

---

## 36. Critical Patterns & Anti-Patterns

### ✅ CORRECT Patterns

```python
# 1. Always get project first:
project = iesve.VEProject.get_current_project()

# 2. Real building is always index 0:
model = project.models[0]

# 3. Get all bodies (rooms) — use False for ALL:
bodies = model.get_bodies(False)

# 4. Filter to rooms only:
rooms = [b for b in bodies if b.type == iesve.VEBody.VEBody_type.room]

# 5. ResultsReader — open by filename, not full path:
rf = iesve.ResultsReader.open('my_results.aps')  # ✅

# 6. ALWAYS call .tolist() to convert numpy array:
temps = rf.get_room_results(room_id, 'Comfort temperature',
                            'Dry resultant temperature', 'z').tolist()

# 7. Vista folder path:
vista_path = project.path + 'Vista'  # or os.path.join(project.path, 'Vista')

# 8. Timesteps to hours conversion:
rph = rf.results_per_day / 24   # results per hour (e.g., 6 if 10-min timestep)

# 9. AirExchange type checking:
ae_data = air_exchange.get()
if ae_data['type_val'] == 0:  # Infiltration
    ...
elif ae_data['type_val'] == 1:  # Natural Ventilation
    ...
elif ae_data['type_val'] == 2:  # Auxiliary Ventilation
    ...

# 10. Internal gain type checking:
gain_data = gain.get()
if gain_data['type_str'] == 'People':
    occupancy_density = gain_data['occupancies'].get(0, 0)  # m²/person

# 11. Thermal templates — all templates, not just assigned:
all_templates = project.thermal_templates(assigned=False)

# 12. HVAC system key in get_apache_systems():
sys_dict = room_data.get_apache_systems()
hvac_id = sys_dict.get('HVAC_system', '')   # key is 'HVAC_system'

# 13. xlsxwriter only (not openpyxl):
workbook = xlsxwriter.Workbook(output_path)
ws = workbook.add_worksheet('Results')
ws.write(0, 0, 'Value', fmt)
workbook.close()

# 14. Room groups — pass the handle (int) not the dict:
schemes = room_groups.get_grouping_schemes()
for scheme in schemes:
    handle = scheme['handle']   # int
    groups = room_groups.get_room_groups(handle)
    for group in groups:
        room_ids = group['rooms']   # list of str
```

### ❌ Anti-Patterns

```python
# WRONG: Using argparse in VE scripts
import argparse  # ❌ — crashes in VE Scripting Editor

# WRONG: Using openpyxl
import openpyxl  # ❌ — not available in VE environment

# WRONG: Full path to ResultsReader.open()
rf = iesve.ResultsReader.open('C:/Projects/MyProject/Vista/results.aps')  # ❌

# WRONG: Forgetting .tolist() when iterating:
temps = rf.get_room_results(room_id, 'Comfort temperature',
                            'Dry resultant temperature', 'z')
for t in temps:  # ❌ — may fail; always convert to list first
    ...

# WRONG: Inventing API methods (they don't exist):
body.get_u_value()     # ❌ — doesn't exist
room.get_floor_area()  # ❌ — use body.get_areas()['int_floor_area']

# WRONG: Getting thermal template name from wrong place
gen = room_data.get_general()
# gen['thermal_template'] is the template name — confirm key name in your VE version

# WRONG: Using display name in ResultsReader (use aps_varname):
rf.get_room_results(room_id, 'Dry Resultant Temp', 'Dry Resultant Temp', 'z')  # ❌ risky
# Use the exact APS variable names as confirmed from rf.get_variables()
```

---

## 37. Complete Working Code Templates

### Template 1: Basic Room Data Extraction

```python
import iesve
import xlsxwriter
import os

def run():
    project = iesve.VEProject.get_current_project()
    model = project.models[0]
    bodies = model.get_bodies(False)

    results = []
    for body in bodies:
        if body.type != iesve.VEBody.VEBody_type.room:
            continue
        try:
            room_data = body.get_room_data()
            gen = room_data.get_general()
            areas = body.get_areas()

            # Internal gains
            gains = room_data.get_internal_gains()
            people_gains = [g for g in gains if g.get().get('type_str') == 'People']

            # Air exchanges
            air_exs = room_data.get_air_exchanges()
            infiltration = [a for a in air_exs if a.get().get('type_val') == 0]

            row = {
                'name': body.name,
                'id': body.id,
                'floor_area': areas.get('int_floor_area', 0) + areas.get('ext_floor_area', 0),
                'volume': areas.get('volume', 0),
                'thermal_template': gen.get('thermal_template', 'N/A'),
                'n_people_gains': len(people_gains),
                'n_infiltration': len(infiltration),
            }
            results.append(row)
        except Exception as e:
            print(f'Error processing {body.name}: {e}')

    # Write to Excel
    out_path = os.path.join(project.path, 'room_data_extract.xlsx')
    wb = xlsxwriter.Workbook(out_path)
    ws = wb.add_worksheet('Rooms')
    headers = ['Name', 'ID', 'Floor Area (m²)', 'Volume (m³)',
               'Thermal Template', 'People Gains', 'Infiltration']
    for col, h in enumerate(headers):
        ws.write(0, col, h)
    for row_idx, row in enumerate(results, 1):
        ws.write(row_idx, 0, row['name'])
        ws.write(row_idx, 1, row['id'])
        ws.write(row_idx, 2, row['floor_area'])
        ws.write(row_idx, 3, row['volume'])
        ws.write(row_idx, 4, row['thermal_template'])
        ws.write(row_idx, 5, row['n_people_gains'])
        ws.write(row_idx, 6, row['n_infiltration'])
    wb.close()
    print(f'Saved: {out_path}')

if __name__ == '__main__':
    run()
```

### Template 2: APS Results Reading (Overheating Check)

```python
import iesve
import xlsxwriter
import os

THRESHOLD = 26.0

def run():
    project = iesve.VEProject.get_current_project()
    vista_path = project.path + 'Vista'

    # List APS files
    aps_files = [f for f in os.listdir(vista_path) if f.endswith('.aps')]
    if not aps_files:
        print('No APS files found.')
        return

    aps_file = aps_files[0]   # Use first APS file
    rf = iesve.ResultsReader.open(aps_file)
    rph = rf.results_per_day / 24   # results per hour

    room_list = rf.get_room_list()
    # room_list: [(room_name, room_id, room_area, room_volume), ...]

    results = []
    for room_name, room_id, room_area, room_volume in room_list:
        try:
            temps = rf.get_room_results(
                room_id, 'Comfort temperature', 'Dry resultant temperature', 'z'
            ).tolist()
            occupancy = rf.get_room_results(
                room_id, 'Number of people', 'Number of people', 'z'
            ).tolist()

            occ_hours_above = 0
            total_occ_hours = 0
            for i, t in enumerate(temps):
                if i < len(occupancy) and occupancy[i] > 0:
                    total_occ_hours += 1
                    if t > THRESHOLD:
                        occ_hours_above += 1

            results.append({
                'name': room_name,
                'id': room_id,
                'area': round(room_area, 2),
                'occ_hours_above': round(occ_hours_above / rph, 1),
                'total_occ_hours': round(total_occ_hours / rph, 1),
            })
        except Exception as e:
            print(f'Error for {room_name}: {e}')

    rf.close()

    # Write Excel
    out_path = os.path.join(project.path, 'overheating_check.xlsx')
    wb = xlsxwriter.Workbook(out_path)
    ws = wb.add_worksheet('Overheating')
    fmt_h = wb.add_format({'bold': True, 'bg_color': '#1F4E78', 'font_color': 'white'})
    headers = ['Room Name', 'Room ID', 'Area (m²)',
               f'Occ Hrs > {THRESHOLD}°C', 'Total Occ Hours']
    for col, h in enumerate(headers):
        ws.write(0, col, h, fmt_h)
    for row_idx, r in enumerate(results, 1):
        ws.write(row_idx, 0, r['name'])
        ws.write(row_idx, 1, r['id'])
        ws.write(row_idx, 2, r['area'])
        ws.write(row_idx, 3, r['occ_hours_above'])
        ws.write(row_idx, 4, r['total_occ_hours'])
    wb.close()
    print(f'Saved: {out_path}')

if __name__ == '__main__':
    run()
```

### Template 3: Room Groups Pattern (as used in BR18 scripts)

```python
import iesve

def get_rooms_by_group(room_groups, scheme_name, group_name):
    """Return list of room IDs in a named group within a named scheme."""
    schemes = room_groups.get_grouping_schemes()
    for scheme in schemes:
        if scheme['name'] == scheme_name:
            groups = room_groups.get_room_groups(scheme['handle'])
            for group in groups:
                if group['name'] == group_name:
                    return group['rooms']   # list of room ID strings
    return []

def run():
    project = iesve.VEProject.get_current_project()
    rg = iesve.RoomGroups()

    rooms_to_analyse = get_rooms_by_group(
        rg, 'Overheating Analysis', 'Analyse Overheating Results'
    )
    if not rooms_to_analyse:
        print('No rooms found in group.')
        return

    vista_path = project.path + 'Vista'
    rf = iesve.ResultsReader.open('simulation.aps')
    rph = rf.results_per_day / 24

    for room_id in rooms_to_analyse:
        temps = rf.get_room_results(
            room_id, 'Comfort temperature', 'Dry resultant temperature', 'z'
        ).tolist()
        print(f'{room_id}: peak = {max(temps):.2f}°C')

    rf.close()

if __name__ == '__main__':
    run()
```

### Template 4: tkinter GUI (standard VE script pattern)

```python
import iesve
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
import xlsxwriter
import os

class MyScriptWindow(tk.Frame):
    def __init__(self, master, project, results_reader):
        super().__init__(master)
        self.master = master
        self.project = project
        self.results_reader = results_reader
        self.master.title('My VE Script')
        self.master.attributes('-topmost', True)
        self._build_ui()

    def _build_ui(self):
        self.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        # APS file selector
        ttk.Label(self, text='Select APS file:').grid(row=0, column=0, sticky='w')
        vista = os.path.join(self.project.path, 'Vista')
        aps_files = [f for f in os.listdir(vista) if f.endswith('.aps')]
        self.listbox = tk.Listbox(self, height=6, width=50)
        for f in aps_files:
            self.listbox.insert(tk.END, f)
        if aps_files:
            self.listbox.select_set(0)
        self.listbox.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=5)

        # Output filename
        ttk.Label(self, text='Output filename:').grid(row=2, column=0, sticky='w')
        self.out_entry = ttk.Entry(self, width=40)
        self.out_entry.insert(0, 'my_report')
        self.out_entry.grid(row=3, column=0, columnspan=2, sticky='ew')

        # Buttons
        ttk.Button(self, text='Run', command=self._run).grid(row=4, column=0, pady=10)
        ttk.Button(self, text='Cancel', command=self.master.destroy).grid(row=4, column=1)

    def _run(self):
        aps_file = self.listbox.get(tk.ACTIVE)
        if not aps_file:
            messagebox.showerror('Error', 'Select an APS file.')
            return
        out_name = self.out_entry.get().strip() or 'my_report'
        if not out_name.endswith('.xlsx'):
            out_name += '.xlsx'
        out_path = os.path.join(self.project.path, out_name)

        try:
            rf = self.results_reader.open(aps_file)
            # ... do work ...
            rf.close()

            wb = xlsxwriter.Workbook(out_path)
            ws = wb.add_worksheet('Results')
            ws.write(0, 0, 'Done')
            wb.close()
            messagebox.showinfo('Done', f'Saved: {out_path}')
            os.startfile(out_path)
            self.master.destroy()
        except Exception as e:
            messagebox.showerror('Error', str(e))

if __name__ == '__main__':
    project = iesve.VEProject.get_current_project()
    root = tk.Tk()
    MyScriptWindow(root, project, iesve.ResultsReader)
    root.mainloop()
```

---

*End of IESVE VEScript API Reference*
*Generated from VE 2023 VEScript User Guide — all content verified against source document*
