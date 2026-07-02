"""SIA 380/2, SIA 4010, and scoring configuration values.

Important:

* Directly usable values are traced to the official SIA 380/2:2022 FR and
  SIA 4010:2023 FR PDFs available in the repository.
* When SIA 380/2 refers to SIA 2024, SIA 387/4, SIA 382/1, or SIA 380, the
  checker must not invent a single generic threshold.
* SIA 4010 validates a method or software workflow through official files and
  tests. The PDF does not provide standalone numerical tolerances that would
  justify an autonomous pass/fail decision.
"""

from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent

# =============================================================================
# SIA 380/2:2022 - limit and target values extracted from the PDF
# =============================================================================
SIA3802_SOURCE_REFERENCES = {
    "table_2": "SIA 380/2:2022 FR, tableau 2, pages PDF 32-35",
    "table_3": "SIA 380/2:2022 FR, tableau 3, pages PDF 36-37",
    "table_4": "SIA 380/2:2022 FR, tableau 4, page PDF 37",
    "tables_5_9": "SIA 380/2:2022 FR, tableaux 5-9, pages PDF 38-39",
    "table_10": "SIA 380/2:2022 FR, tableau 10, page PDF 46",
    "method": "SIA 380/2:2022 FR, chapitres 4-7 et annexe A",
}

SIA3802_LIMIT_VALUES = {
    # Envelope and openings
    "external_wall_u": 0.20,
    "external_wall_against_ground_u": 0.30,
    "internal_partition_non_bearing_u": 0.30,
    "internal_partition_bearing_u": 2.70,
    "internal_wall_unconditioned_u": 0.28,
    "ground_floor_u": 0.30,
    "intermediate_floor_u": 0.64,
    "intermediate_floor_unconditioned_u": 0.30,
    "flat_roof_u": 0.20,
    "window_u": 1.10,
    "thermal_bridge_psi_chi": 0.0,
    "window_frame_fraction": 0.25,
    "glazing_ratio_source": "SIA 2024",
    "glazing_g_value": 0.50,
    "glazing_light_transmittance": 0.70,
    "infiltration_m3_h_m2": 0.15,
    # Ventilation / AHU for the reference project
    "ventilation_efficiency": 1.0,
    "duct_airtightness_class": "C",
    "ahu_airtightness_class": "L2",
    "ahu_heat_transfer_w_m2k": 0.70,
    "supply_duct_heat_transfer_unconditioned_w_k": 15,
    "pressure_drop_supply_pa": 700,
    "pressure_drop_extract_pa": 500,
    "heat_recovery_pressure_drop_pa": 300,
    "heat_recovery_temperature_efficiency": 0.73,
    "heat_recovery_humidity_efficiency": 0.0,
    # Control and systems
    "cooling_control_delta_t_k": -1.8,
    "heating_control_delta_t_k": 1.2,
    "pv_power_w_per_m2_sre": 10,
    "pv_conversion_efficiency": 0.90,
}

SIA3802_TARGET_VALUES = {
    "external_wall_u": 0.14,
    "external_wall_against_ground_u": 0.20,
    "internal_partition_non_bearing_u": 0.30,
    "internal_partition_bearing_u": 2.70,
    "internal_wall_unconditioned_u": 0.20,
    "ground_floor_u": 0.20,
    "intermediate_floor_u": 0.64,
    "intermediate_floor_unconditioned_u": 0.20,
    "flat_roof_u": 0.14,
    "window_u": 0.88,
    "thermal_bridge_psi_chi": 0.0,
    "window_frame_fraction": 0.25,
    "glazing_ratio_source": "SIA 2024",
    "glazing_g_value": 0.50,
    "glazing_light_transmittance": 0.70,
    "infiltration_m3_h_m2": 0.15,
    "ventilation_efficiency": 1.4,
    "duct_airtightness_class": "C",
    "ahu_airtightness_class": "L1",
    "ahu_heat_transfer_w_m2k": 0.50,
    "supply_duct_heat_transfer_unconditioned_w_k": 10,
    "pressure_drop_supply_pa": 550,
    "pressure_drop_extract_pa": 350,
    "heat_recovery_pressure_drop_pa": 400,
    "heat_recovery_temperature_efficiency": 0.78,
    "heat_recovery_humidity_efficiency": 0.60,
    "cooling_control_delta_t_k": 0.0,
    "heating_control_delta_t_k": 0.0,
    "pv_modules_efficiency": 0.17,
    "pv_conversion_efficiency": 0.90,
}

SIA3802_SOLAR_PROTECTION_CATEGORIES = {
    1: {
        "lamellae": {"solar_reflectance": 0.70, "solar_transmittance": 0.00},
        "fabric": {"solar_reflectance": 0.50, "solar_transmittance": 0.25},
    },
    2: {"lamellae": {"solar_reflectance": 0.70, "solar_transmittance": 0.00}},
    3: {
        "lamellae": {"solar_reflectance": 0.50, "solar_transmittance": 0.00},
        "fabric": {"solar_reflectance": 0.35, "solar_transmittance": 0.25},
    },
    4: {
        "lamellae": {"solar_reflectance": 0.30, "solar_transmittance": 0.00},
        "fabric": {"solar_reflectance": 0.25, "solar_transmittance": 0.10},
    },
    5: {"fabric": {"solar_reflectance": 0.20, "solar_transmittance": 0.05}},
}

SIA3802_VENTILATION_CONTROL_TABLE = {
    ("monozone", "<=3"): {
        "limit": "one speed, time schedule control",
        "target": "two speeds 67/100%, time schedule control",
    },
    ("monozone", "3-6"): {
        "limit": "two speeds 67/100%, time schedule control",
        "target": "variable speed >=25%, demand control by occupancy",
    },
    ("monozone", ">6"): {
        "limit": "variable speed >=25%, demand control by occupancy",
        "target": "variable speed >=25%, demand control by gas sensor",
    },
    ("multizone", "<=3"): {
        "limit": "two speeds 67/100%, time schedule control by zone",
        "target": "two speeds 67/100%, occupancy control by zone",
    },
    ("multizone", "3-6"): {
        "limit": "two speeds 67/100%, occupancy control by zone",
        "target": "variable speed >=25%, demand control by occupancy per room",
    },
    ("multizone", ">6"): {
        "limit": "variable speed >=25%, demand control by gas sensor by zone",
        "target": "variable speed >=25%, demand control by gas sensor per room",
    },
}

SIA3802_COOLING_EER_SEER_LIMITS = {
    "air_cooled": {
        "<=12": {"eer": 2.90, "seer": 3.80},
        "12-50": {"eer": 3.00, "seer": 3.90},
        "50-150": {"eer": 3.10, "seer": 4.00},
        "150-450": {"eer": 3.20, "seer": 4.20},
        "450-1000": {"eer": 3.40, "seer": 4.40},
    },
    "water_cooled": {
        "12-50": {"eer": 4.05, "seer": 4.50},
        "50-150": {"eer": 4.25, "seer": 4.80},
        "150-450": {"eer": 4.65, "seer": 5.50},
        "450-1000": {"eer": 5.05, "seer": 6.10},
        ">1000": {"eer": 5.50, "seer": 6.70},
    },
}

SIA3802_HEATING_SCOP_LIMITS = {
    "air_water_heat_pump": {
        "<=12": 3.00,
        "12-50": 3.10,
        "50-150": 3.20,
    },
    "ground_source_heat_pump": {
        "12-50": 4.00,
        "50-150": 4.20,
        "150-450": 4.60,
        "450-1000": 5.00,
        ">1000": 5.50,
    },
}

# Operational SIA 380/2 values used by the checker.
SIA3802_U_VALUES = {
    "external_wall": SIA3802_LIMIT_VALUES["external_wall_u"],
    "roof": SIA3802_LIMIT_VALUES["flat_roof_u"],
    "floor": SIA3802_LIMIT_VALUES["ground_floor_u"],
    "window": SIA3802_LIMIT_VALUES["window_u"],
    "door": SIA3802_LIMIT_VALUES["window_u"],
    "thermal_bridge": SIA3802_LIMIT_VALUES["thermal_bridge_psi_chi"],
}

SIA3802_THRESHOLDS = {
    # Valeurs directes SIA 380/2.
    "solar_factor_max": SIA3802_LIMIT_VALUES["glazing_g_value"],
    "light_transmittance_min": SIA3802_LIMIT_VALUES["glazing_light_transmittance"],
    "window_frame_fraction": SIA3802_LIMIT_VALUES["window_frame_fraction"],
    "infiltration_m3_h_m2": SIA3802_LIMIT_VALUES["infiltration_m3_h_m2"],
    # Indicateurs de revue uniquement: pas des seuils pass/fail SIA 380/2 directs.
    "wwr_max": 0.3,
    "ventilation_rate_min": None,
    "lighting_power_max": None,
    "equipment_power_max": None,
    "hvac_efficiency_min": None,
    "renewable_energy_min": None,
    "primary_energy_max": None,
}

# Backward-compatible aliases for older local scripts/imports.
SIA3801_U_VALUES = SIA3802_U_VALUES
SIA3801_THRESHOLDS = SIA3802_THRESHOLDS

# =============================================================================
# SIA 4010:2023 - method/software validation, not a standalone building threshold
# =============================================================================
SIA4010_SOURCE_REFERENCES = {
    "purpose": "SIA 4010:2023 FR, page PDF 8, clauses 2.3-2.6",
    "tests": "SIA 4010:2023 FR, tableau 62, page PDF 46",
    "classes": "SIA 4010:2023 FR, tableau 63, page PDF 48",
    "infrastructure": "SIA 4010:2023 FR, clauses 4.6.1-4.6.2, pages PDF 48-49",
    "test_2_3_variants": "SIA 4010:2023 FR, tableau 65, page PDF 52",
    "test_5_variants": "SIA 4010:2023 FR, tableau 66, page PDF 52",
    "validated_software_register": "SIA 4010 Register validierter Software_24-09-17.pdf, pages 1-2, Zurich 2024-09-17",
    "manager_navigator_backlog": "Sia 380_2 Navigator - Executive Summary & Product Backlog.docx",
}

SIA4010_VALIDATION_TESTS = {
    "test_1": "Basic envelope tests according to EN ISO 52016-1 / ASHRAE 140",
    "test_2": "Solar protection control according to SIA 387/4 and SIA 380/2 Annex A",
    "test_3": "Lighting control according to SIA 387/4",
    "test_4": "Single-room all-air air-conditioning system",
    "test_5": "Multizone AHU with reheater, cooler, humidifier and heat/moisture wheel",
    "test_6": "Three-stage ventilation with heat recovery, constant airflow and overflow",
    "test_7": "Heating/cooling emission, distribution, storage and generation; total heating/cooling need",
}

SIA4010_VALIDATION_CLASSES = {
    "1A": "Tests 1 and 2A",
    "1B": "Tests 1 and 2",
    "2A": "Tests 1, 2A, 3A to 3F",
    "2B": "Tests 1 to 3",
    "3": "Tests 1 and 4 to 6",
    "4A": "Tests 1, 2A, 3A to 3F, 4 to 7",
    "4B": "Tests 1 to 7",
    "5": "Test 7",
}

SIA4010_VALIDATION_CLASS_DETAILS = {
    "1A": {
        "applications": "Cooling need assessment and basic thermal load calculation",
        "solar_protection": "Without sun-position-dependent control, e.g. fabric awnings",
        "tests": "1 and 2A",
        "source": SIA4010_SOURCE_REFERENCES["validated_software_register"],
    },
    "1B": {
        "applications": "Cooling need assessment and basic thermal load calculation",
        "solar_protection": "Rafflamellenstoren / venetian blinds",
        "tests": "1 and 2",
        "source": SIA4010_SOURCE_REFERENCES["validated_software_register"],
    },
    "2A": {
        "applications": "Lighting energy according to SIA 387/4:2023 clause 3.4, heating demand and cooling demand",
        "solar_protection": "Without sun-position-dependent control, e.g. fabric awnings",
        "tests": "1, 2A, 3A to 3F",
        "source": SIA4010_SOURCE_REFERENCES["validated_software_register"],
    },
    "2B": {
        "applications": "Lighting energy according to SIA 387/4:2023 clause 3.4, heating demand and cooling demand",
        "solar_protection": "Rafflamellenstoren / venetian blinds",
        "tests": "1 to 3",
        "source": SIA4010_SOURCE_REFERENCES["validated_software_register"],
    },
    "3": {
        "applications": "Need assessment for humidification and dehumidification",
        "solar_protection": "Not separately restricted in the manager-provided register",
        "tests": "1, 4 to 6",
        "source": SIA4010_SOURCE_REFERENCES["validated_software_register"],
    },
    "4A": {
        "applications": "System-related thermal load calculation, cooling energy demand and heating energy demand",
        "solar_protection": "Without sun-position-dependent control, e.g. fabric awnings",
        "tests": "1, 2A, 3A to 3F, 4 to 7",
        "source": SIA4010_SOURCE_REFERENCES["validated_software_register"],
    },
    "4B": {
        "applications": "System-related thermal load calculation, cooling energy demand and heating energy demand",
        "solar_protection": "Rafflamellenstoren / venetian blinds",
        "tests": "1 to 7",
        "source": SIA4010_SOURCE_REFERENCES["validated_software_register"],
    },
    "5": {
        "applications": "Cooling and heating energy demand with existing demand profiles",
        "solar_protection": "Not separately restricted in the manager-provided register",
        "tests": "7",
        "source": SIA4010_SOURCE_REFERENCES["validated_software_register"],
    },
}

SIA4010_VALIDATED_SOFTWARE_REGISTER = [
    {
        "institution": "Equa Solutions AG, Zug",
        "software": "IDA-ICE 5.0 beta",
        "validation_classes": ["1A", "1B", "2A", "2B", "3", "4A", "4B", "5"],
        "valid_until": "2029-03-20",
        "source": SIA4010_SOURCE_REFERENCES["validated_software_register"],
    },
    {
        "institution": "Fachhochschule Nordwestschweiz, Muttenz",
        "software": "Energy+ / OpenStudio",
        "validation_classes": ["1A", "1B", "2A", "2B", "4A", "4B"],
        "valid_until": "2029-03-20",
        "source": SIA4010_SOURCE_REFERENCES["validated_software_register"],
    },
    {
        "institution": "Lemon Consult AG, Zurich",
        "software": "EDSL Tas",
        "validation_classes": ["1A", "3", "4A"],
        "valid_until": "2029-03-20",
        "source": SIA4010_SOURCE_REFERENCES["validated_software_register"],
    },
    {
        "institution": "E4tech Software SA, Lausanne",
        "software": "Lesosai 2024 build 1903",
        "validation_classes": ["1A", "1B", "2A", "2B", "3"],
        "valid_until": "2029-09-17",
        "source": SIA4010_SOURCE_REFERENCES["validated_software_register"],
    },
]

SIA4010_IESVE_REGISTER_STATUS = {
    "software": "IESVE",
    "listed_in_manager_register": False,
    "register_date": "2024-09-17",
    "source": SIA4010_SOURCE_REFERENCES["validated_software_register"],
    "guardrail": (
        "IESVE is not listed in the manager-provided SIA 4010 validated-software register. "
        "Do not claim software-level SIA 4010 validation without separate official evidence."
    ),
}

SIA3802_NAVIGATOR_BACKLOG = [
    {
        "epic": "EPIC 1",
        "name": "Regulatory Framework & Project Setup",
        "user_story": "Explicitly select SIA 380/2:2022 as the regulatory framework.",
        "acceptance_criteria": "Mandatory framework selection; framework visible; framework locked once calculation starts.",
        "current_project_status": "PARTIAL - report states standards scope, but VE input locking is not implemented.",
        "next_action": "Add project-template fingerprint and framework-lock evidence in preflight/audit log.",
    },
    {
        "epic": "EPIC 2",
        "name": "Climate Data Management",
        "user_story": "Select climate files from a validated list.",
        "acceptance_criteria": "Closed list of approved climate files; no manual weather edits; warning for non-SIA files.",
        "current_project_status": "READINESS_ONLY - climate evidence is requested but not enforced as a closed VE list.",
        "next_action": "Create approved Swiss climate-file manifest and compare active VE weather file against it.",
    },
    {
        "epic": "EPIC 3",
        "name": "Thermal Zoning & Usage Classification",
        "user_story": "Assign each thermal zone to a SIA usage category.",
        "acceptance_criteria": "Mandatory SIA usage per zone; locked schedules; cross-zone consistency checks.",
        "current_project_status": "PARTIAL - rooms are extracted, but SIA 2024 usage assignment remains evidence-driven.",
        "next_action": "Add room-by-room SIA 2024 usage mapping template and validation sheet.",
    },
    {
        "epic": "EPIC 4",
        "name": "Building Envelope Inputs",
        "user_story": "Select envelope U-values from SIA tables or justify manual values.",
        "acceptance_criteria": "Normative value library; justification required for manual inputs; automatic SIA comparison.",
        "current_project_status": "PARTIAL - automated comparison exists for extracted envelope/opening values.",
        "next_action": "Add evidence fields for manual overrides and construction-library provenance.",
    },
    {
        "epic": "EPIC 5",
        "name": "Internal Gains",
        "user_story": "Use predefined SIA profiles for occupants, lighting and equipment.",
        "acceptance_criteria": "Closed SIA profile libraries; no optimized/adaptive profiles; visible densities and power values.",
        "current_project_status": "MISSING - gains are checked as data coverage, not constrained by SIA profile libraries.",
        "next_action": "Build SIA profile manifest and detect deviations from active room templates/profiles.",
    },
    {
        "epic": "EPIC 6",
        "name": "Ventilation & Infiltration",
        "user_story": "Ventilation rates follow SIA-defined values and scenarios.",
        "acceptance_criteria": "Predefined SIA airflow rates; limited operating modes; simplified infiltration model only.",
        "current_project_status": "PARTIAL - infiltration readiness exists; full ventilation mode locking is not implemented.",
        "next_action": "Map VE ventilation/MacroFlo fields to SIA airflow scenarios and evidence requirements.",
    },
    {
        "epic": "EPIC 7",
        "name": "Setpoints & Control Logic",
        "user_story": "Temperature setpoints are fixed and SIA-compliant.",
        "acceptance_criteria": "Fixed heating/cooling setpoints; no adaptive control; limited night setback options.",
        "current_project_status": "MISSING - setpoint/control locking is not automated.",
        "next_action": "Extract thermal template setpoints/profiles and flag adaptive or unsupported controls.",
    },
    {
        "epic": "EPIC 8",
        "name": "Technical Systems",
        "user_story": "Select generic SIA-compliant system templates with bounded efficiencies.",
        "acceptance_criteria": "Generic system library; normative efficiency ranges; no implicit optimization.",
        "current_project_status": "PARTIAL - HVAC readiness and SIA 380/2 efficiency tables are traced, but templates are not locked.",
        "next_action": "Create generic system-template manifest and map VE Apache/HVAC networks to SIA ranges.",
    },
    {
        "epic": "EPIC 9",
        "name": "Results, Validation & Reporting",
        "user_story": "Map results automatically to SIA 380/2 indicators.",
        "acceptance_criteria": "Standardized result tables; consistency checks; error/warning list before calculation approval.",
        "current_project_status": "PARTIAL - Excel report, dynamic result readiness and alerts are implemented.",
        "next_action": "Expand APS/Vista extraction for official SIA result tables and comparison workbooks.",
    },
    {
        "epic": "EPIC 10",
        "name": "Audit Trail & Compliance Report",
        "user_story": "Generate an assumption report so compliance can be reviewed and defended.",
        "acceptance_criteria": "Full assumption log; compliance status per input; exportable PDF/DOC report.",
        "current_project_status": "PARTIAL - Excel audit report exists; exportable PDF/DOC package remains future work.",
        "next_action": "Add evidence-pack export and optional DOCX/PDF manager package generation.",
    },
]

SIA4010_REQUIRED_EVIDENCE = [
    "Official SIA test specifications",
    "Official SIA Excel evaluation workbooks",
    "Candidate software/model results transferred into the official evaluation workbooks",
    "Reference-result graphs/comparisons generated by the official files",
    "Validation class requested and confirmed by SIA or the responsible sub-commission",
]

SIA4010_CLIMATE_AND_3802_COMPLEMENTS = {
    "summer_overheating_climate": {
        "source": "SIA 4010:2023 FR, page PDF 9, clause 3.1.1",
        "requirement": "Use SIA 2028 DRY data; CH2018/RCP 8.5 period 2035 may or must be used according to the summer overheating application.",
    },
    "heating_design_preconditioning": {
        "source": "SIA 4010:2023 FR, page PDF 9, clause 3.1.2",
        "requirement": "Use the coldest 4-day January period from the normal DRY, with the preceding 14 normal DRY days as preconditioning, avoiding weekends via the calendar.",
    },
    "cooling_design_preconditioning": {
        "source": "SIA 4010:2023 FR, page PDF 9, clause 3.1.3",
        "requirement": "Use the hottest relevant days in June, August and October, with preceding 14 normal DRY days as preconditioning; RCP 8.5 period 2035 DRY is recommended for the climate scenario.",
    },
    "setpoint_shift_by_use": {
        "source": "SIA 4010:2023 FR, page PDF 10, clause 3.1.4",
        "lower_curve_shift_k": {
            "SIA2024_3.04": 1,
            "SIA2024_5.01_to_5.03": 1,
            "SIA2024_6.03_to_6.04": 1,
            "SIA2024_9.01": 3,
        },
        "upper_curve_shift_k": {
            "SIA2024_6.03_to_6.04": 2,
            "SIA2024_9.01": 4,
        },
    },
    "fabric_blind_solar_method": {
        "source": "SIA 4010:2023 FR, page PDF 10, clause 3.1.5",
        "requirement": "For fabric blinds, use equal direct/diffuse solar transmission/reflection, or replace glazing g with total glazing-plus-shading g when shading is active.",
    },
}

SIA4010_TECHNICAL_IDENTIFIERS = {
    "SUP_AIR_TEMP_CTRL": ["NO_CTRL", "CONST", "ODA_COMP", "LOAD_COMP"],
    "SUP_AIR_FLW_CTRL": ["ODA", "LOAD"],
    "AIR_FLOW_CTRL": ["NO_CTRL", "ON/OFF_CTRL", "MULTI_STAGE", "VARIABLE"],
    "SYS_TYPE": ["SINGLE_ZONE", "MULTI_ZONE"],
    "FAN_CTRL": ["NO_CTRL", "CONST_PRES", "MIN_PRES", "DIRECT"],
    "FAN_MOTOR_LOCATION": ["IN_AIR", "OUTS_AIR"],
    "GND_PREH_CTRL": ["NO_CTRL", "BYPASS"],
    "RCA_CTRL": ["FIX", "VARIABLE"],
    "HEAT_REC_TYPE": ["PLATE", "ROT_NH", "ROT_HYG", "ROT_SORP", "PUMP_CIRC", "OTHER"],
    "HEAT_REC_CTRL": ["NO_CTRL", "BYPASS", "SPEED", "HYDR"],
    "FROST_PROTECTION": ["PREH", "BYPASS", "RECIRC"],
    "DEFR_CTRL": ["DIRECT", "INDIRECT"],
    "SUP_FAN_LOCATION_HR": ["UP_HR", "DOWN_HR"],
    "ETA_FAN_LOCATION_HR": ["UP_HR", "DOWN_HR"],
    "HUM_TYPE": ["CONTACT", "ROT_SPRAY", "HI_PRES", "HYBRID", "STEAM", "OTHER"],
    "HUM_CTRL": ["NO_CTRL", "ON_OFF", "SPEED"],
    "HUM_STEAM_ENERGY": ["HUM_CR_EL", "HUM_CR_GAS", "HUM_CR_SOL", "HUM_CR_OTHER"],
    "AHU_LOCATION": ["CND", "NC"],
    "CLG_GEN_TMP_CTRL": ["CONST", "VARIABLE"],
    "CLG_DISTR_TMP_CTRL": ["CONST", "ODA_COMP", "MAX_TMP"],
    "CLG_DISTR_FLW_CTRL": ["CONST", "VARIABLE"],
    "CLG_EN_DISTR_CTRL": ["NO_CTRL", "PRIO"],
    "PUMP_CTRL_CODE": [0, 1, 2, 3, 4],
    "CLG_GENERATOR_TYPE": ["COMP", "ABS", "OTHER"],
    "HEAT_REJECTION_TYPE": ["AIR_C_COND", "DRY", "WET", "HYBRID", "OTHER"],
    "FREE_COOLING": ["YES", "NO"],
    "HBRD_HEAT_REJ_CTRL": ["TEMP", "MAX_POWER"],
    "CLG_STORAGE_TYPE": ["STO_TYPE_CW", "STO_TYPE_ICE", "STO_TYPE_PCM"],
    "CLG_STORAGE_LOCATION": ["CLG_STO_LOC_CND", "CLG_STO_LOC_NC", "CLG_STO_LOC_EXT"],
    "CLG_STO_CTRL": ["CONT", "TIME", "TEMP", "LOAD_PRED"],
}

SIA4010_LEAKAGE_FACTORS = {
    "ducts": {
        "unknown": 1.45,
        "A": 1.18,
        "B": 1.06,
        "C": 1.02,
        "D": 1.00,
        "default_new": "B",
        "default_existing_or_unknown": "unknown",
        "source": "SIA 4010:2023 FR, page PDF 12, tableaux 3-4",
    },
    "ahu": {
        "L3": 1.10,
        "L2": 1.04,
        "L1": 1.01,
        "default_new": "L1",
        "default_existing": "L3",
        "source": "SIA 4010:2023 FR, page PDF 13, tableaux 5-6",
    },
}

SIA4010_SYSTEM_REQUIREMENT_SOURCES = {
    "ventilation": {
        "pages": "SIA 4010:2023 FR, pages PDF 11-17 and 24-28",
        "table_range": "Tables 1-23 and 34-35",
        "requires": [
            "airflow control identifiers",
            "duct and AHU leakage/airtightness",
            "fan control and pressure drops",
            "heat/moisture recovery",
            "humidification type/control/energy carrier",
            "AHU and duct heat losses",
            "zone design airflows",
        ],
    },
    "cooling": {
        "pages": "SIA 4010:2023 FR, pages PDF 18-22 and 29-36",
        "table_range": "Tables 24-33 and 36-48",
        "requires": [
            "cooling generation temperature control",
            "distribution temperature/flow control",
            "pump control",
            "storage type/location/control",
            "generator type",
            "heat rejection type",
            "free cooling availability",
            "part-load EER data",
        ],
    },
    "heating": {
        "pages": "SIA 4010:2023 FR, pages PDF 23 and 36-44",
        "table_range": "Tables 49-59",
        "requires": [
            "BACS/control identifiers",
            "emission, distribution, storage and generation data",
            "boiler/generator input data",
            "heat pump calculation according to SIA 384/3 hourly method",
            "solar thermal and cogeneration inputs where applicable",
        ],
    },
    "domestic_hot_water": {
        "pages": "SIA 4010:2023 FR, page PDF 44",
        "table_range": "Referenced to SIA 385/2",
        "requires": ["DHW heat demand and hourly load cycles if coupled to heat generation"],
    },
    "general_building_electricity": {
        "pages": "SIA 4010:2023 FR, page PDF 44",
        "table_range": "Referenced to SIA 2056 / SIA 2024 / SIA 387/4",
        "requires": ["general technical electricity, user electricity/appliances, lighting, PV inputs"],
    },
    "photovoltaics": {
        "pages": "SIA 4010:2023 FR, page PDF 45",
        "table_range": "Tables 60-61",
        "requires": ["number/area/orientation/tilt of PV modules, peak power coefficient, system performance factor"],
    },
}

SIA4010_TEST_READINESS_REQUIREMENTS = {
    "test_1": {
        "source": "SIA 4010:2023 FR, tableau 62 page PDF 46; annexe A page PDF 50",
        "domain": "Basic envelope EN ISO 52016-1 / ASHRAE 140",
        "model_requirements": [
            "zones/rooms extracted",
            "external envelope surfaces extracted",
            "opaque construction U-values extracted",
            "external window/opening data extracted",
            "official test model and reference outputs attached",
        ],
        "next_action": "Import/run the official test case and compare hourly outputs with the SIA file.",
    },
    "test_2": {
        "source": "SIA 4010:2023 FR, tableau 62 page PDF 46; tableau 65 page PDF 52",
        "domain": "Solar-protection control SIA 387/4 + SIA 380/2 Annex A",
        "model_requirements": [
            "external glazing and g-values extracted",
            "solar protection type/category documented",
            "solar protection control strategy documented",
            "CH climate/use/infiltration diagnostic scenario attached",
            "official test 2 evaluation file attached",
        ],
        "next_action": "Extract or document blinds, control thresholds and active g_total.",
    },
    "test_3": {
        "source": "SIA 4010:2023 FR, tableau 62 page PDF 46; tableau 65 page PDF 52",
        "domain": "Lighting control SIA 387/4",
        "model_requirements": [
            "lighting power extracted",
            "daylight control strategy documented",
            "SIA 387/4 lighting control type documented",
            "lighting energy outputs available",
            "official test 3 evaluation file attached",
        ],
        "next_action": "Map VE templates to lighting power and SIA 387/4 control strategy.",
    },
    "test_4": {
        "source": "SIA 4010:2023 FR, tableau 62 page PDF 46; annexe A page PDF 50",
        "domain": "Single-room all-air air-conditioning system",
        "model_requirements": [
            "HVAC systems extracted",
            "ventilation/airflow data extracted",
            "cooling/heating coil outputs available",
            "CO2/temperature hourly outputs available",
            "official amphitheatre test model and evaluation file attached",
        ],
        "next_action": "Export the required APS/Vista hourly results for supply air, CO2, coils and powers.",
    },
    "test_5": {
        "source": "SIA 4010:2023 FR, tableau 62 page PDF 46; tableau 66 page PDF 52",
        "domain": "Complex multizone AHU with heat/moisture recovery",
        "model_requirements": [
            "multizone HVAC/AHU data extracted",
            "fan control identifier documented",
            "heat/moisture recovery type documented",
            "humidifier type/control documented",
            "official test 5 variant/evaluation file attached",
        ],
        "next_action": "Map VE AHU data to variants 5A-5D: FAN_CTRL, recovery unit and humidifier.",
    },
    "test_6": {
        "source": "SIA 4010:2023 FR, tableau 62 page PDF 46; annexe A page PDF 51",
        "domain": "Three-stage ventilation with heat recovery and overflow",
        "model_requirements": [
            "ventilation systems extracted",
            "constant airflow and stage data documented",
            "heat recovery data documented",
            "restaurant/kitchen overflow represented",
            "official test 6 evaluation file attached",
        ],
        "next_action": "Extract airflow rates, stages, recovery and restaurant/kitchen overflow logic.",
    },
    "test_7": {
        "source": "SIA 4010:2023 FR, tableau 62 page PDF 46; annexe A page PDF 51",
        "domain": "Heating/cooling emission, distribution, storage and generation",
        "model_requirements": [
            "heating/cooling demand outputs available",
            "final energy by system/carrier available",
            "emission/distribution/storage/generation data documented",
            "pump/fan/auxiliary energy available",
            "official test 7 loads and evaluation file attached",
        ],
        "next_action": "Read APS/Vista outputs and separate needs, final energy, auxiliaries, storage and generation.",
    },
}

SIA4010_TEST_CLASS_COVERAGE = {
    "test_1": ["1A", "1B", "2A", "2B", "3", "4A", "4B"],
    "test_2": ["1B", "2B", "4B"],
    "test_2A": ["1A", "2A", "4A"],
    "test_3": ["2B", "4B"],
    "test_3A_to_3F": ["2A", "4A"],
    "test_4": ["3", "4A", "4B"],
    "test_5": ["3", "4A", "4B"],
    "test_6": ["3", "4A", "4B"],
    "test_7": ["4A", "4B", "5"],
}

SIA4010_THRESHOLDS = {
    # The SIA 4010 PDF does not define standalone building limits in kWh/m2 or
    # CO2. These keys are kept only for future client indicators.
    "heating_demand_max": None,
    "cooling_demand_max": None,
    "primary_energy_max": None,
    "co2_emissions_max": None,
    "renewable_energy_min": None,
}

# =============================================================================
# CATEGORY WEIGHTS FOR THE COMPLIANCE SCORE
# =============================================================================
SIA_COMPLIANCE_REQUIREMENT_MATRIX = [
    {
        "id": "SIA3802_ENV_EXT_WALL_U",
        "standard": "SIA 380/2:2022",
        "domain": "Envelope",
        "criterion": "External wall U-value",
        "limit": SIA3802_LIMIT_VALUES["external_wall_u"],
        "unit": "W/(m2K)",
        "target": SIA3802_TARGET_VALUES["external_wall_u"],
        "source": SIA3802_SOURCE_REFERENCES["table_3"],
        "automation": "AUTOMATED",
        "implemented_rule": "SIA3802_U_VALUE_EXTERNAL_WALL",
        "mvp_status": "MVP",
        "next_action": "Keep extracting opaque parent construction U-values and report failures by construction/area.",
    },
    {
        "id": "SIA3802_ENV_ROOF_U",
        "standard": "SIA 380/2:2022",
        "domain": "Envelope",
        "criterion": "Flat roof U-value",
        "limit": SIA3802_LIMIT_VALUES["flat_roof_u"],
        "unit": "W/(m2K)",
        "target": SIA3802_TARGET_VALUES["flat_roof_u"],
        "source": SIA3802_SOURCE_REFERENCES["table_3"],
        "automation": "AUTOMATED",
        "implemented_rule": "SIA3802_U_VALUE_ROOF",
        "mvp_status": "MVP",
        "next_action": "Improve roof/floor classification where VE surface type is ambiguous.",
    },
    {
        "id": "SIA3802_ENV_GROUND_FLOOR_U",
        "standard": "SIA 380/2:2022",
        "domain": "Envelope",
        "criterion": "Ground floor / floor against unconditioned U-value",
        "limit": SIA3802_LIMIT_VALUES["ground_floor_u"],
        "unit": "W/(m2K)",
        "target": SIA3802_TARGET_VALUES["ground_floor_u"],
        "source": SIA3802_SOURCE_REFERENCES["table_3"],
        "automation": "PARTIAL",
        "implemented_rule": "SIA3802_U_VALUE_FLOOR",
        "mvp_status": "MVP",
        "next_action": "Separate ground, basement-unconditioned and intermediate floor cases.",
    },
    {
        "id": "SIA3802_OPENING_WINDOW_U",
        "standard": "SIA 380/2:2022",
        "domain": "Openings",
        "criterion": "Window Uw",
        "limit": SIA3802_LIMIT_VALUES["window_u"],
        "unit": "W/(m2K)",
        "target": SIA3802_TARGET_VALUES["window_u"],
        "source": SIA3802_SOURCE_REFERENCES["table_2"],
        "automation": "AUTOMATED",
        "implemented_rule": "SIA3802_U_VALUE_WINDOW",
        "mvp_status": "MVP",
        "next_action": "Confirm that extracted VE value is window Uw, not glass centre U only.",
    },
    {
        "id": "SIA3802_OPENING_G_VALUE",
        "standard": "SIA 380/2:2022",
        "domain": "Openings",
        "criterion": "Glazing normal solar factor g_perp",
        "limit": SIA3802_LIMIT_VALUES["glazing_g_value"],
        "unit": "-",
        "target": SIA3802_TARGET_VALUES["glazing_g_value"],
        "source": SIA3802_SOURCE_REFERENCES["table_2"],
        "automation": "PARTIAL",
        "implemented_rule": "SIA3802_SOLAR_FACTOR",
        "mvp_status": "MVP",
        "next_action": "Confirm whether VE value is EN 410 g_perp / SHGC / construction g-value and document mapping.",
    },
    {
        "id": "SIA3802_OPENING_LIGHT_TRANSMITTANCE",
        "standard": "SIA 380/2:2022",
        "domain": "Openings",
        "criterion": "Glazing light transmittance tau",
        "limit": SIA3802_LIMIT_VALUES["glazing_light_transmittance"],
        "unit": "minimum",
        "target": SIA3802_TARGET_VALUES["glazing_light_transmittance"],
        "source": SIA3802_SOURCE_REFERENCES["table_2"],
        "automation": "PARTIAL",
        "implemented_rule": "SIA3802_VISIBLE_TRANSMITTANCE",
        "mvp_status": "MSP",
        "next_action": "Extract visible transmittance from CDB glazing properties or require external evidence.",
    },
    {
        "id": "SIA3802_AIRTIGHTNESS_INFILTRATION",
        "standard": "SIA 380/2:2022",
        "domain": "Ventilation",
        "criterion": "Infiltration reference value",
        "limit": SIA3802_LIMIT_VALUES["infiltration_m3_h_m2"],
        "unit": "m3/(h.m2)",
        "target": SIA3802_TARGET_VALUES["infiltration_m3_h_m2"],
        "source": SIA3802_SOURCE_REFERENCES["table_2"],
        "automation": "PARTIAL",
        "implemented_rule": "SIA3802_INFILTRATION_M3_H_M2",
        "mvp_status": "MVP",
        "next_action": "Use direct l/(s.m2 facade) conversion when VE exposes it; otherwise require unit justification.",
    },
    {
        "id": "SIA3802_SOLAR_PROTECTION",
        "standard": "SIA 380/2:2022",
        "domain": "Solar protection",
        "criterion": "Solar protection category and control",
        "limit": "category 4 limit / category 2 target; control category 2 limit / 3 target",
        "unit": "category",
        "target": "category 2 protection and control category 3",
        "source": f"{SIA3802_SOURCE_REFERENCES['table_2']}; {SIA3802_SOURCE_REFERENCES['table_10']}",
        "automation": "PARTIAL",
        "implemented_rule": "SIA3802_SOLAR_PROTECTION_TYPE_MISSING / SIA3802_SOLAR_PROTECTION_CONTROL_MISSING / SIA3802_G_TOTAL_WITH_SHADING_MISSING",
        "mvp_status": "MSP",
        "next_action": "Map VE shading devices, optical properties, controls and active g_total.",
    },
    {
        "id": "SIA3802_VENTILATION_CONTROL",
        "standard": "SIA 380/2:2022",
        "domain": "Ventilation",
        "criterion": "Ventilation control according to system type and airflow band",
        "limit": "Table 4 by monozone/multizone and <=3 / 3-6 / >6 m3/(h.m2)",
        "unit": "control class",
        "target": "Table 4 target control",
        "source": SIA3802_SOURCE_REFERENCES["table_4"],
        "automation": "PARTIAL",
        "implemented_rule": "SIA3802_VENTILATION_RATE",
        "mvp_status": "MSP",
        "next_action": "Extract airflow per m2, zone/system type and control identifiers.",
    },
    {
        "id": "SIA3802_COOLING_EER_SEER",
        "standard": "SIA 380/2:2022",
        "domain": "Cooling",
        "criterion": "Cooling generator EER/SEER by type and power band",
        "limit": "Tables 5-7",
        "unit": "EER/SEER",
        "target": "Tables 5-7 target values",
        "source": SIA3802_SOURCE_REFERENCES["tables_5_9"],
        "automation": "PARTIAL",
        "implemented_rule": "SIA3802_HVAC_EFFICIENCY",
        "mvp_status": "MSP",
        "next_action": "Extract cooling generator type, cooling power, EER/SEER and part-load data.",
    },
    {
        "id": "SIA3802_HEATING_SCOP",
        "standard": "SIA 380/2:2022",
        "domain": "Heating",
        "criterion": "Heat pump SCOP by type and power band",
        "limit": "Tables 8-9",
        "unit": "SCOP",
        "target": "Tables 8-9 target values where provided",
        "source": SIA3802_SOURCE_REFERENCES["tables_5_9"],
        "automation": "PARTIAL",
        "implemented_rule": "SIA3802_HVAC_EFFICIENCY",
        "mvp_status": "MSP",
        "next_action": "Extract heating generator type, power band and SCOP/SIA 384/3 evidence.",
    },
    {
        "id": "SIA3802_DYNAMIC_METHOD",
        "standard": "SIA 380/2:2022",
        "domain": "Dynamic results",
        "criterion": "Hourly dynamic calculation with SIA 2028 DRY and required preconditioning",
        "limit": "Hourly method, annual heating/cooling needs and design periods",
        "unit": "method evidence",
        "target": "Complete APS/Vista hourly evidence pack",
        "source": SIA3802_SOURCE_REFERENCES["method"],
        "automation": "PARTIAL",
        "implemented_rule": "APS/Vista dynamic result extraction",
        "mvp_status": "MSP",
        "next_action": "Read APS/Vista outputs for heating, cooling, temperatures, CO2 and timestep metadata.",
    },
    {
        "id": "SIA4010_VALIDATION_TESTS",
        "standard": "SIA 4010:2023",
        "domain": "Validation",
        "criterion": "Official validation tests 1-7 and validation class",
        "limit": "Official SIA evaluation files and reference results required",
        "unit": "evidence",
        "target": "Validated class 4B when all tests 1-7 are passed",
        "source": f"{SIA4010_SOURCE_REFERENCES['tests']}; {SIA4010_SOURCE_REFERENCES['classes']}",
        "automation": "READINESS_ONLY",
        "implemented_rule": "SIA4010_VALIDATION_EVIDENCE_MISSING",
        "mvp_status": "MVP",
        "next_action": "Detect evidence folder/files and keep tests NOT_CHECKABLE until official comparisons are attached.",
    },
]

# =============================================================================
# REPORT OUTPUT STRATEGY
# =============================================================================
# "timestamped" keeps one unique workbook per VE Run. A separate latest-report
# alias can be re-enabled later, but it is disabled by default to avoid producing
# two Excel files for one run.
REPORT_OUTPUT_MODE = "timestamped"
CREATE_LATEST_REPORT_ALIAS = False

# =============================================================================
# SIA DATA COVERAGE MATRIX
# =============================================================================
# This matrix is intentionally data-oriented. It tells the report which model
# values, simulation outputs or external evidence are needed before a requirement
# can move from readiness review to a defensible compliance conclusion.
SIA_DATA_COVERAGE_MATRIX = [
    {
        "id": "SIA3802_PROJECT_CLIMATE",
        "standard": "SIA 380/2:2022 + SIA 4010:2023",
        "validation_scope": "All SIA 4010 classes",
        "domain": "Project setup",
        "criterion": "Project location, altitude, weather file and SIA 2028 DRY / CH2018 climate basis",
        "expected_value": "Documented Swiss climate basis; SIA 4010 summer/heating/cooling design periods where applicable",
        "data_needed": "VE project settings, weather file name, location, altitude and climate scenario",
        "expected_source": "VE project settings plus reviewer confirmation",
        "coverage_key": "project_climate",
        "automation": "PARTIAL",
        "preferred_format": "Screenshot/export of VE project weather settings or short reviewer note",
        "destination": "sia4010_evidence/",
        "source": f"{SIA3802_SOURCE_REFERENCES['method']}; {SIA4010_SOURCE_REFERENCES['purpose']}",
        "owner": "Model reviewer",
        "next_action": "Confirm the exact SIA 2028/CH2018 weather basis used by the simulation.",
    },
    {
        "id": "SIA3802_ROOM_GEOMETRY",
        "standard": "SIA 380/2:2022",
        "validation_scope": "All building checks",
        "domain": "Geometry",
        "criterion": "Thermal rooms/zones, floor area and volume",
        "expected_value": "Complete heated/cooled room set with auditable area and volume",
        "data_needed": "Room id, name, floor area, volume and zone membership",
        "expected_source": "IESVE model API",
        "coverage_key": "rooms",
        "automation": "AUTOMATED",
        "preferred_format": "Extracted directly by the Run-button script",
        "destination": "Excel ROOMS sheet",
        "source": SIA3802_SOURCE_REFERENCES["method"],
        "owner": "Developer",
        "next_action": "Resolve any missing/duplicated VE rooms before relying on scores.",
    },
    {
        "id": "SIA3802_USE_CATEGORY_SIA2024",
        "standard": "SIA 380/2:2022",
        "validation_scope": "All building checks",
        "domain": "Use category",
        "criterion": "SIA 2024 use category mapping for schedules, gains and glazing-related assumptions",
        "expected_value": "One justified SIA 2024 use category per thermal zone",
        "data_needed": "Zone use, schedules, occupancy, equipment and lighting assumptions",
        "expected_source": "VE room templates plus reviewer mapping",
        "coverage_key": "use_category",
        "automation": "PARTIAL",
        "preferred_format": "Excel/CSV mapping table: VE room -> SIA 2024 category",
        "destination": "sia4010_evidence/",
        "source": SIA3802_SOURCE_REFERENCES["method"],
        "owner": "Compliance reviewer",
        "next_action": "Provide or confirm the room-to-SIA-2024 mapping.",
    },
    {
        "id": "SIA3802_EXTERNAL_ENVELOPE",
        "standard": "SIA 380/2:2022",
        "validation_scope": "Envelope checks",
        "domain": "Envelope",
        "criterion": "External opaque surfaces with areas and types",
        "expected_value": "External walls, roofs and floors classified with gross/net areas",
        "data_needed": "Surface type, external/internal status, area, construction id",
        "expected_source": "IESVE model API",
        "coverage_key": "external_surfaces",
        "automation": "AUTOMATED",
        "preferred_format": "Extracted directly by the Run-button script",
        "destination": "Excel ALERTS / DATA QUALITY sheets",
        "source": SIA3802_SOURCE_REFERENCES["table_3"],
        "owner": "Developer",
        "next_action": "Improve classification where VE surface type/adjacency is ambiguous.",
    },
    {
        "id": "SIA3802_OPAQUE_U_VALUES",
        "standard": "SIA 380/2:2022",
        "validation_scope": "Envelope checks",
        "domain": "Envelope",
        "criterion": "Opaque construction U-values",
        "expected_value": "Wall 0.20, roof 0.20, ground floor 0.30 W/(m2K) limit values where applicable",
        "data_needed": "U-value per external opaque construction",
        "expected_source": "IESVE CDB/construction data",
        "coverage_key": "surface_u_values",
        "automation": "AUTOMATED",
        "preferred_format": "Extracted CDB properties or construction schedule export",
        "destination": "Excel SIA REQUIREMENTS / ALERTS sheets",
        "source": SIA3802_SOURCE_REFERENCES["table_3"],
        "owner": "Developer",
        "next_action": "Confirm construction U-values and floor/roof classification.",
    },
    {
        "id": "SIA3802_WINDOW_UW",
        "standard": "SIA 380/2:2022",
        "validation_scope": "Opening checks",
        "domain": "Openings",
        "criterion": "Window Uw",
        "expected_value": "Uw limit 1.10 W/(m2K), target 0.88 W/(m2K)",
        "data_needed": "External window areas, construction ids and Uw values",
        "expected_source": "IESVE opening/construction data",
        "coverage_key": "window_u_values",
        "automation": "AUTOMATED",
        "preferred_format": "Extracted directly by the Run-button script",
        "destination": "Excel SIA REQUIREMENTS / ALERTS sheets",
        "source": SIA3802_SOURCE_REFERENCES["table_2"],
        "owner": "Developer",
        "next_action": "Confirm the extracted value is total window Uw, not glass-only U.",
    },
    {
        "id": "SIA3802_WINDOW_G_VALUE",
        "standard": "SIA 380/2:2022",
        "validation_scope": "Opening and solar checks",
        "domain": "Openings",
        "criterion": "Glazing normal solar factor",
        "expected_value": "g_perp limit/target 0.50 where applicable",
        "data_needed": "External glazing g-value or SHGC mapping",
        "expected_source": "IESVE CDB glazing data plus mapping note",
        "coverage_key": "window_g_values",
        "automation": "PARTIAL",
        "preferred_format": "Extracted value plus note confirming EN 410 g_perp/SHGC interpretation",
        "destination": "Excel ALERTS plus sia4010_evidence/",
        "source": SIA3802_SOURCE_REFERENCES["table_2"],
        "owner": "Compliance reviewer",
        "next_action": "Confirm the exact meaning of the VE solar-factor field.",
    },
    {
        "id": "SIA3802_LIGHT_TRANSMITTANCE",
        "standard": "SIA 380/2:2022",
        "validation_scope": "Opening and daylight checks",
        "domain": "Openings",
        "criterion": "Glazing visible light transmittance",
        "expected_value": "tau_v minimum 0.70 where applicable",
        "data_needed": "Visible transmittance per glazing construction",
        "expected_source": "IESVE CDB glazing data or manufacturer evidence",
        "coverage_key": "visible_transmittance",
        "automation": "PARTIAL",
        "preferred_format": "CDB export or manufacturer glazing schedule",
        "destination": "sia4010_evidence/",
        "source": SIA3802_SOURCE_REFERENCES["table_2"],
        "owner": "Model reviewer",
        "next_action": "Extract visible transmittance or request glazing evidence.",
    },
    {
        "id": "SIA3802_FRAME_FRACTION",
        "standard": "SIA 380/2:2022",
        "validation_scope": "Opening checks",
        "domain": "Openings",
        "criterion": "Window frame fraction",
        "expected_value": "Frame fraction reference value 0.25",
        "data_needed": "Frame/glass split or equivalent window construction definition",
        "expected_source": "IESVE opening construction data or external schedule",
        "coverage_key": "frame_fraction",
        "automation": "PARTIAL",
        "preferred_format": "Window schedule with frame fraction",
        "destination": "sia4010_evidence/",
        "source": SIA3802_SOURCE_REFERENCES["table_2"],
        "owner": "Model reviewer",
        "next_action": "Document frame fraction or equivalent VE modelling assumption.",
    },
    {
        "id": "SIA3802_SOLAR_PROTECTION_CONTROL",
        "standard": "SIA 380/2:2022 + SIA 4010:2023",
        "validation_scope": "SIA 4010 classes 1A, 1B, 2A, 2B, 4A, 4B",
        "domain": "Solar protection",
        "criterion": "Solar protection category, optical properties and control strategy",
        "expected_value": "SIA 380/2 table 10 categories and active-control evidence",
        "data_needed": "Blind type, reflectance/transmittance, active g_total and control thresholds",
        "expected_source": "VE shading data plus reviewer evidence",
        "coverage_key": "solar_protection",
        "automation": "PARTIAL",
        "preferred_format": "Shading schedule/export and control strategy note",
        "destination": "sia4010_evidence/",
        "source": f"{SIA3802_SOURCE_REFERENCES['table_10']}; {SIA4010_SOURCE_REFERENCES['test_2_3_variants']}",
        "owner": "Compliance reviewer",
        "next_action": "Map VE shading devices and controls to SIA categories.",
    },
    {
        "id": "SIA3802_INFILTRATION",
        "standard": "SIA 380/2:2022",
        "validation_scope": "Envelope / ventilation checks",
        "domain": "Ventilation",
        "criterion": "Reference infiltration / airtightness input",
        "expected_value": "0.15 m3/(h.m2) reference value where applicable",
        "data_needed": "Infiltration value and unit conversion basis per room or facade",
        "expected_source": "IESVE air-exchange data plus unit mapping",
        "coverage_key": "infiltration",
        "automation": "PARTIAL",
        "preferred_format": "Extracted air-exchange data or infiltration schedule",
        "destination": "Excel DATA QUALITY plus sia4010_evidence/",
        "source": SIA3802_SOURCE_REFERENCES["table_2"],
        "owner": "Developer",
        "next_action": "Confirm unit conversion to m3/(h.m2) where VE exposes different units.",
    },
    {
        "id": "SIA3802_INTERNAL_GAINS",
        "standard": "SIA 380/2:2022",
        "validation_scope": "Dynamic method checks",
        "domain": "Internal gains",
        "criterion": "Occupancy, equipment and lighting gains",
        "expected_value": "Use-specific gains consistent with SIA 2024/project assumptions",
        "data_needed": "People, equipment, lighting gains and schedules",
        "expected_source": "VE room templates/internal gains",
        "coverage_key": "internal_gains",
        "automation": "PARTIAL",
        "preferred_format": "VE template export or room-use schedule",
        "destination": "sia4010_evidence/",
        "source": SIA3802_SOURCE_REFERENCES["method"],
        "owner": "Model reviewer",
        "next_action": "Provide missing schedules and verify use-category assumptions.",
    },
    {
        "id": "SIA3802_SCHEDULES",
        "standard": "SIA 380/2:2022 + SIA 4010:2023",
        "validation_scope": "All dynamic checks",
        "domain": "Schedules",
        "criterion": "Occupancy, HVAC, lighting, shading and equipment schedules",
        "expected_value": "Auditable schedules used by annual and design-period simulations",
        "data_needed": "Hourly/weekly schedules and exceptions",
        "expected_source": "VE profiles/templates or exported schedule workbook",
        "coverage_key": "schedules",
        "automation": "NOT_IMPLEMENTED",
        "preferred_format": "CSV/XLSX schedule export",
        "destination": "sia4010_evidence/",
        "source": SIA3802_SOURCE_REFERENCES["method"],
        "owner": "Model reviewer",
        "next_action": "Export schedules from VE or document assumptions.",
    },
    {
        "id": "SIA3802_VENTILATION_RATES",
        "standard": "SIA 380/2:2022",
        "validation_scope": "Ventilation checks",
        "domain": "Ventilation",
        "criterion": "Design ventilation rate by room/area",
        "expected_value": "Rate needed to select table 4 control band",
        "data_needed": "Outdoor air / supply airflow per room and floor area",
        "expected_source": "IESVE air-exchange data",
        "coverage_key": "ventilation_rates",
        "automation": "PARTIAL",
        "preferred_format": "Extracted air-exchange data",
        "destination": "Excel DATA QUALITY",
        "source": SIA3802_SOURCE_REFERENCES["table_4"],
        "owner": "Developer",
        "next_action": "Normalize airflow to m3/(h.m2) and connect to control bands.",
    },
    {
        "id": "SIA3802_VENTILATION_CONTROL",
        "standard": "SIA 380/2:2022 + SIA 4010:2023",
        "validation_scope": "SIA 4010 classes 3, 4A, 4B",
        "domain": "Ventilation",
        "criterion": "Ventilation control class / airflow modulation",
        "expected_value": "Table 4 control strategy by system type and airflow band",
        "data_needed": "Monozone/multizone flag, fan control, demand-control sensors and minimum flow",
        "expected_source": "VE system/AHU data plus reviewer confirmation",
        "coverage_key": "ventilation_control",
        "automation": "NOT_IMPLEMENTED",
        "preferred_format": "AHU/system schedule and controls note",
        "destination": "sia4010_evidence/",
        "source": SIA3802_SOURCE_REFERENCES["table_4"],
        "owner": "Compliance reviewer",
        "next_action": "Map VE HVAC control objects to SIA 380/2 and SIA 4010 identifiers.",
    },
    {
        "id": "SIA3802_AHU_HEAT_RECOVERY",
        "standard": "SIA 380/2:2022 + SIA 4010:2023",
        "validation_scope": "SIA 4010 classes 3, 4A, 4B",
        "domain": "Ventilation",
        "criterion": "AHU leakage, heat recovery, pressure drops and heat transfer",
        "expected_value": "Duct class C, AHU L2/L1 and heat-recovery values per SIA tables where applicable",
        "data_needed": "Duct/AHU leakage class, heat recovery type/efficiency, pressure drops, fan data",
        "expected_source": "VE AHU/system data and external design evidence",
        "coverage_key": "ahu_heat_recovery",
        "automation": "NOT_IMPLEMENTED",
        "preferred_format": "AHU schedule/export and fan/heat-recovery data sheet",
        "destination": "sia4010_evidence/",
        "source": f"{SIA3802_SOURCE_REFERENCES['table_4']}; {SIA4010_SYSTEM_REQUIREMENT_SOURCES['ventilation']['pages']}",
        "owner": "Compliance reviewer",
        "next_action": "Collect AHU and ventilation evidence for SIA 4010 tests 5 and 6.",
    },
    {
        "id": "SIA3802_COOLING_EER_SEER",
        "standard": "SIA 380/2:2022 + SIA 4010:2023",
        "validation_scope": "SIA 4010 classes 3, 4A, 4B",
        "domain": "Cooling",
        "criterion": "Cooling generator type, power band, EER/SEER and part-load data",
        "expected_value": "SIA 380/2 tables 5-7 values by generator type/power band",
        "data_needed": "Generator type, rated power, EER/SEER, part-load curve and heat rejection type",
        "expected_source": "VE Apache systems, plant data and manufacturer evidence",
        "coverage_key": "cooling_efficiency",
        "automation": "NOT_IMPLEMENTED",
        "preferred_format": "Cooling plant schedule/export",
        "destination": "sia4010_evidence/",
        "source": SIA3802_SOURCE_REFERENCES["tables_5_9"],
        "owner": "Model reviewer",
        "next_action": "Extract or document cooling generator performance.",
    },
    {
        "id": "SIA3802_HEATING_SCOP",
        "standard": "SIA 380/2:2022 + SIA 4010:2023",
        "validation_scope": "SIA 4010 classes 4A, 4B, 5",
        "domain": "Heating",
        "criterion": "Heat-pump type, power band and SCOP / SIA 384/3 evidence",
        "expected_value": "SIA 380/2 tables 8-9 values where heat pumps are applicable",
        "data_needed": "Generator type, rated power, SCOP, hourly method evidence for heat pumps",
        "expected_source": "VE plant data and manufacturer/evaluation evidence",
        "coverage_key": "heating_efficiency",
        "automation": "NOT_IMPLEMENTED",
        "preferred_format": "Heating plant schedule/export",
        "destination": "sia4010_evidence/",
        "source": SIA3802_SOURCE_REFERENCES["tables_5_9"],
        "owner": "Model reviewer",
        "next_action": "Extract or document heating generator performance.",
    },
    {
        "id": "SIA3802_LIGHTING_CONTROL",
        "standard": "SIA 380/2:2022 + SIA 4010:2023",
        "validation_scope": "SIA 4010 classes 2A, 2B, 4A, 4B",
        "domain": "Lighting",
        "criterion": "Lighting power and SIA 387/4 daylight/presence control",
        "expected_value": "Lighting control evidence compatible with SIA 387/4 references",
        "data_needed": "Lighting power density, schedules, daylight control and presence control",
        "expected_source": "VE gains/templates plus reviewer evidence",
        "coverage_key": "lighting_control",
        "automation": "PARTIAL",
        "preferred_format": "Lighting schedule/export and control strategy note",
        "destination": "sia4010_evidence/",
        "source": SIA4010_SOURCE_REFERENCES["test_2_3_variants"],
        "owner": "Compliance reviewer",
        "next_action": "Map VE lighting controls to SIA 387/4 categories.",
    },
    {
        "id": "SIA3802_DYNAMIC_APS_RESULTS",
        "standard": "SIA 380/2:2022 + SIA 4010:2023",
        "validation_scope": "All dynamic and SIA 4010 tests",
        "domain": "Dynamic results",
        "criterion": "APS/Vista hourly or sub-hourly results available for the active model",
        "expected_value": "Readable APS file with timestep metadata and room/system variables",
        "data_needed": "APS file, variable list, room results and timestep",
        "expected_source": "IESVE ResultsReader inside VE",
        "coverage_key": "dynamic_aps",
        "automation": "PARTIAL",
        "preferred_format": "APS/Vista results in the project Vista folder",
        "destination": "VE project Vista folder",
        "source": SIA3802_SOURCE_REFERENCES["method"],
        "owner": "Developer",
        "next_action": "Read APS via IESVE ResultsReader and expose variables in the report.",
    },
    {
        "id": "SIA3802_HOURLY_TEMPERATURES",
        "standard": "SIA 380/2:2022 + SIA 4010:2023",
        "validation_scope": "Thermal comfort and tests 4-6",
        "domain": "Dynamic results",
        "criterion": "Hourly temperature / overheating indicators",
        "expected_value": "Occupied hours above selected temperature thresholds and supporting series",
        "data_needed": "Room temperatures, occupancy and timestep",
        "expected_source": "APS/Vista room results",
        "coverage_key": "hourly_temperatures",
        "automation": "PARTIAL",
        "preferred_format": "APS/Vista results or exported CSV/XLSX",
        "destination": "VE project Vista folder or sia4010_evidence/",
        "source": SIA3802_SOURCE_REFERENCES["method"],
        "owner": "Developer",
        "next_action": "Confirm available APS variable names for temperature and occupancy.",
    },
    {
        "id": "SIA3802_HEATING_COOLING_DEMANDS",
        "standard": "SIA 380/2:2022 + SIA 4010:2023",
        "validation_scope": "Energy and SIA 4010 test 7",
        "domain": "Dynamic results",
        "criterion": "Annual heating/cooling demand and peak loads",
        "expected_value": "kWh and kWh/m2 by room/building, plus peak W where available",
        "data_needed": "Heating load, cooling load, room area and timestep",
        "expected_source": "APS/Vista room results",
        "coverage_key": "heating_cooling_demands",
        "automation": "PARTIAL",
        "preferred_format": "APS/Vista results or exported CSV/XLSX",
        "destination": "VE project Vista folder or sia4010_evidence/",
        "source": SIA4010_TEST_READINESS_REQUIREMENTS["test_7"]["source"],
        "owner": "Developer",
        "next_action": "Read load variables and aggregate to kWh/m2.",
    },
    {
        "id": "SIA4010_OFFICIAL_TEST_SPECS",
        "standard": "SIA 4010:2023",
        "validation_scope": "All SIA 4010 classes",
        "domain": "Official evidence",
        "criterion": "Official SIA test specifications",
        "expected_value": "Official test specification files for the selected class",
        "data_needed": "SIA 4010 official test files/specifications",
        "expected_source": "Official SIA package or responsible validation authority",
        "coverage_key": "evidence_official_test_specifications",
        "automation": "EVIDENCE_SCAN",
        "preferred_format": "PDF/DOCX/XLSX with filename prefix SIA4010_official_test_specs_",
        "destination": "sia4010_evidence/",
        "source": SIA4010_SOURCE_REFERENCES["tests"],
        "owner": "Compliance reviewer",
        "next_action": "Place official test specifications in the evidence folder.",
    },
    {
        "id": "SIA4010_OFFICIAL_EVALUATION_WORKBOOKS",
        "standard": "SIA 4010:2023",
        "validation_scope": "All SIA 4010 classes",
        "domain": "Official evidence",
        "criterion": "Official SIA evaluation workbooks",
        "expected_value": "Official evaluation workbook(s) for the selected validation class",
        "data_needed": "SIA official Excel evaluation files",
        "expected_source": "Official SIA package or responsible validation authority",
        "coverage_key": "evidence_official_evaluation_workbooks",
        "automation": "EVIDENCE_SCAN",
        "preferred_format": "XLSX with filename prefix SIA4010_official_evaluation_workbook_",
        "destination": "sia4010_evidence/",
        "source": SIA4010_SOURCE_REFERENCES["infrastructure"],
        "owner": "Compliance reviewer",
        "next_action": "Place official evaluation workbooks in the evidence folder.",
    },
    {
        "id": "SIA4010_CANDIDATE_RESULTS",
        "standard": "SIA 4010:2023",
        "validation_scope": "All SIA 4010 classes",
        "domain": "Official evidence",
        "criterion": "Candidate IESVE results transferred into official files",
        "expected_value": "Candidate software outputs for every required official test",
        "data_needed": "APS/Vista outputs and filled evaluation workbooks",
        "expected_source": "IESVE results plus official SIA workbook",
        "coverage_key": "evidence_candidate_results",
        "automation": "EVIDENCE_SCAN",
        "preferred_format": "XLSX/CSV/PDF with filename prefix SIA4010_candidate_results_",
        "destination": "sia4010_evidence/",
        "source": SIA4010_SOURCE_REFERENCES["tests"],
        "owner": "Compliance reviewer",
        "next_action": "Attach candidate results for every required SIA test.",
    },
    {
        "id": "SIA4010_REFERENCE_COMPARISONS",
        "standard": "SIA 4010:2023",
        "validation_scope": "All SIA 4010 classes",
        "domain": "Official evidence",
        "criterion": "Reference comparison plots/tables",
        "expected_value": "Official workbook comparisons against reference outputs",
        "data_needed": "Reference output comparisons, plots and deviations",
        "expected_source": "Official SIA evaluation workbook",
        "coverage_key": "evidence_reference_comparisons",
        "automation": "EVIDENCE_SCAN",
        "preferred_format": "PDF/XLSX with filename prefix SIA4010_reference_comparison_",
        "destination": "sia4010_evidence/",
        "source": SIA4010_SOURCE_REFERENCES["infrastructure"],
        "owner": "Compliance reviewer",
        "next_action": "Attach comparison evidence generated by the official workbook.",
    },
    {
        "id": "SIA4010_VALIDATION_CLASS_CONFIRMATION",
        "standard": "SIA 4010:2023",
        "validation_scope": "Classes 1A, 1B, 2A, 2B, 3, 4A, 4B, 5",
        "domain": "Official evidence",
        "criterion": "Validation class selected and confirmed",
        "expected_value": "Selected class and required test set confirmed",
        "data_needed": "Class confirmation and responsible reviewer/authority note",
        "expected_source": "SIA/sub-commission/client compliance decision",
        "coverage_key": "evidence_validation_class_confirmation",
        "automation": "EVIDENCE_SCAN",
        "preferred_format": "PDF/DOCX/TXT with filename containing class_4B, class_4A, etc.",
        "destination": "sia4010_evidence/",
        "source": SIA4010_SOURCE_REFERENCES["classes"],
        "owner": "Compliance reviewer",
        "next_action": "Confirm which class is claimed before any final validation wording.",
    },
]

SIA4010_EVIDENCE_DIR = "sia4010_evidence"
SIA4010_EVIDENCE_FILE_PATTERNS = {
    "official_test_specifications": ["spec", "specification", "beschreibung", "description", "test"],
    "official_evaluation_workbooks": ["evaluation", "auswertung", "validation", "excel", ".xlsx"],
    "candidate_results": ["candidate", "result", "results", "iesve", "ve", "vista", "aps"],
    "reference_comparisons": ["reference", "comparison", "compare", "graph", "chart", "plot"],
    "validation_class_confirmation": ["class", "classe", "validation", "confirmation", "sia"],
}

CATEGORY_WEIGHTS = {
    "envelope": 0.25,    # Poids de l'enveloppe (murs, toitures, planchers)
    "openings": 0.20,    # Poids des ouvertures (fenêtres, portes)
    "ventilation": 0.15, # Poids de la ventilation
    "hvac": 0.20,        # HVAC system weight
    "energy": 0.15,      # Energy weight (consumption, emissions)
    "simulation": 0.05,  # Poids des tests de simulation (SIA 4010)
}

# =============================================================================
# SIA 4010 TEST WEIGHTS
# =============================================================================
SIA4010_TEST_WEIGHTS = {
    "test_1": 0.15,  # BESTEST basic envelope
    "test_2": 0.10,  # Solar-protection control
    "test_3": 0.10,  # Lighting control
    "test_4": 0.10,  # HVAC system (single room)
    "test_5": 0.15,  # HVAC system (multizone)
    "test_6": 0.10,  # Ventilation system
    "test_7": 0.30,  # Total energy needs
}

# =============================================================================
# CO2 EMISSION FACTORS (kg CO2/kWh)
# =============================================================================
EMISSION_FACTORS = {
    "electricity": 0.05,   # Swiss electricity mix
    "gas": 0.20,          # Gaz naturel
    "oil": 0.25,          # Fioul
    "wood": 0.02,         # Bois
    "solar": 0.0,         # Solaire
    "wind": 0.0,          # Wind
    "district_heating": 0.1,  # Chauffage urbain
}

# =============================================================================
# CHEMINS DES FICHIERS
# =============================================================================
OUTPUT_DIR = "reports"  # Dossier de sortie pour les rapports
EXCEL_REPORT_NAME = "Swiss_Compliance_Report.xlsx"  # Nom du fichier Excel
LOG_FILE = "swiss_compliance_checker.log"  # Fichier de log

# =============================================================================
# PARAMÈTRES DE SIMULATION (ApacheSim)
# =============================================================================
SIMULATION_PARAMS = {
    "results_filename": "swiss_compliance_simulation",  # Results file name
    "simulation_timestep": 2,  # 0=1min, 1=2min, 2=6min, 3=10min, 4=30min
    "reporting_interval": 2,   # 0=6min, 1=10min, 2=30min, 3=60min
    "HVAC": True,              # Include HVAC systems
    "nat_ventilation": True,   # Inclure la ventilation naturelle
    "aux_ventilation": True,   # Inclure la ventilation auxiliaire
}

# =============================================================================
# PARAMÈTRES DE RAPPORT EXCEL
# =============================================================================
EXCEL_FORMATS = {
    "header": {
        "bold": True,
        "text_wrap": True,
        "valign": "top",
        "fg_color": "#1F4E78",
        "font_color": "white",
        "font_size": 14,
        "border": 1,
    },
    "subheader": {
        "bold": True,
        "fg_color": "#2E75B6",
        "font_size": 12,
        "border": 1,
    },
    "pass": {
        "bg_color": "#E2EFDA",
        "font_color": "#375623",
        "border": 1,
    },
    "warning": {
        "bg_color": "#FFF2CC",
        "font_color": "#7F6000",
        "border": 1,
    },
    "fail": {
        "bg_color": "#FDECEA",
        "font_color": "#C00000",
        "border": 1,
    },
    "critical": {
        "bg_color": "#F2C7C7",
        "font_color": "#9C0006",
        "border": 1,
    },
    "score": {
        "bold": True,
        "font_size": 16,
    },
}

# =============================================================================
# ALERT-TYPE PENALTIES (for Health Score calculation)
# =============================================================================
PENALTIES = {
    "missing_template": 5.0,       # Missing thermal template
    "missing_hvac": 5.0,           # Missing HVAC system
    "missing_construction": 2.0,   # Missing construction
    "zero_area_room": 8.0,         # Room with zero area
    "zero_volume_room": 8.0,       # Room with zero volume
    "tiny_area_room": 3.0,         # Room with area <= 1 m2
    "tiny_volume_room": 2.0,       # Room with volume <= 2 m3
    "duplicate_room_name": 2.0,    # Duplicate room name
    "suspicious_wwr": 3.0,         # WWR > 0.80 or < 0 on external walls
    "zero_area_surface": 3.0,      # Surface with zero area
    "no_external_openings": 2.0,   # No external opening
    "missing_occupancy": 4.0,      # Missing occupancy profile
    "missing_lighting": 3.0,       # Missing lighting profile
    "missing_equipment": 2.0,      # Missing equipment profile
    "missing_ventilation": 4.0,    # Missing ventilation profile
    "missing_infiltration": 3.0,   # Missing infiltration profile
    "invalid_opening": 2.0,         # Invalid opening
}
