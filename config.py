"""
Configuration des valeurs SIA 380/2, SIA 4010 et poids des scores.

Important:
- Les valeurs directement utilisables ci-dessous sont tracées aux PDF présents
  dans le dépôt: SIA 380/2:2022 FR et SIA 4010:2023 FR.
- Quand SIA 380/2 renvoie à SIA 2024, SIA 387/4, SIA 382/1 ou SIA 380, le
  checker ne doit pas inventer de seuil unique.
- SIA 4010 valide une méthode/un logiciel via fichiers et tests officiels. Le
  PDF ne donne pas de tolérances numériques permettant un pass/fail autonome.
"""

# =============================================================================
# SIA 380/2:2022 - valeurs limites et cibles extraites du PDF
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
    # Enveloppe et ouvertures
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
    # Ventilation / CTA pour le projet de référence
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
    # Régulation et systèmes
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

# Noms legacy conservés pour éviter de casser les modules existants. Les valeurs
# pointent maintenant vers les valeurs limites SIA 380/2:2022 lorsqu'elles sont
# directement disponibles dans le PDF.
SIA3801_U_VALUES = {
    "external_wall": SIA3802_LIMIT_VALUES["external_wall_u"],
    "roof": SIA3802_LIMIT_VALUES["flat_roof_u"],
    "floor": SIA3802_LIMIT_VALUES["ground_floor_u"],
    "window": SIA3802_LIMIT_VALUES["window_u"],
    "door": SIA3802_LIMIT_VALUES["window_u"],
    "thermal_bridge": SIA3802_LIMIT_VALUES["thermal_bridge_psi_chi"],
}

SIA3801_THRESHOLDS = {
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

# =============================================================================
# SIA 4010:2023 - validation de méthode/logiciel, pas seuil bâtiment autonome
# =============================================================================
SIA4010_SOURCE_REFERENCES = {
    "purpose": "SIA 4010:2023 FR, page PDF 8, clauses 2.3-2.6",
    "tests": "SIA 4010:2023 FR, tableau 62, page PDF 46",
    "classes": "SIA 4010:2023 FR, tableau 63, page PDF 48",
    "infrastructure": "SIA 4010:2023 FR, clauses 4.6.1-4.6.2, pages PDF 48-49",
    "test_2_3_variants": "SIA 4010:2023 FR, tableau 65, page PDF 52",
    "test_5_variants": "SIA 4010:2023 FR, tableau 66, page PDF 52",
}

SIA4010_VALIDATION_TESTS = {
    "test_1": "Tests de base de l'enveloppe selon EN ISO 52016-1 / ASHRAE 140",
    "test_2": "Régulation de la protection solaire selon SIA 387/4 et SIA 380/2 annexe A",
    "test_3": "Régulation de l'éclairage selon SIA 387/4",
    "test_4": "Climatisation d'une seule pièce, système à air seul",
    "test_5": "CTA multizone avec réchauffeur, refroidisseur, humidificateur et rotor chaleur/humidité",
    "test_6": "Ventilation à trois niveaux avec récupération de chaleur, débit constant et débordement",
    "test_7": "Émission, distribution, stockage et production de chaud/froid; besoin total chauffage/refroidissement",
}

SIA4010_VALIDATION_CLASSES = {
    "1A": "Tests 1 et 2A",
    "1B": "Tests 1 et 2",
    "2A": "Tests 1, 2A, 3A à 3F",
    "2B": "Tests 1 à 3",
    "3": "Tests 1 et 4 à 6",
    "4A": "Tests 1, 2A, 3A à 3F, 4 à 7",
    "4B": "Tests 1 à 7",
    "5": "Test 7",
}

SIA4010_REQUIRED_EVIDENCE = [
    "Spécifications officielles des tests SIA",
    "Fichiers Excel officiels d'évaluation SIA",
    "Résultats du logiciel/modèle candidat transférés dans les fichiers d'évaluation",
    "Graphiques/comparaisons aux résultats de référence générés par les fichiers officiels",
    "Classe de validation demandée et confirmée par la SIA/sous-commission",
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
        "domain": "Enveloppe de base EN ISO 52016-1 / ASHRAE 140",
        "model_requirements": [
            "zones/rooms extracted",
            "external envelope surfaces extracted",
            "opaque construction U-values extracted",
            "external window/opening data extracted",
            "official test model and reference outputs attached",
        ],
        "next_action": "Importer/executer le cas test officiel et comparer les sorties horaires au fichier SIA.",
    },
    "test_2": {
        "source": "SIA 4010:2023 FR, tableau 62 page PDF 46; tableau 65 page PDF 52",
        "domain": "Regulation protection solaire SIA 387/4 + SIA 380/2 annexe A",
        "model_requirements": [
            "external glazing and g-values extracted",
            "solar protection type/category documented",
            "solar protection control strategy documented",
            "CH climate/use/infiltration diagnostic scenario attached",
            "official test 2 evaluation file attached",
        ],
        "next_action": "Extraire ou documenter les stores, seuils de commande et g_total actif.",
    },
    "test_3": {
        "source": "SIA 4010:2023 FR, tableau 62 page PDF 46; tableau 65 page PDF 52",
        "domain": "Regulation eclairage SIA 387/4",
        "model_requirements": [
            "lighting power extracted",
            "daylight control strategy documented",
            "SIA 387/4 lighting control type documented",
            "lighting energy outputs available",
            "official test 3 evaluation file attached",
        ],
        "next_action": "Mapper les templates VE vers puissance eclairage et commande SIA 387/4.",
    },
    "test_4": {
        "source": "SIA 4010:2023 FR, tableau 62 page PDF 46; annexe A page PDF 50",
        "domain": "Climatisation mono-piece, systeme a air seul",
        "model_requirements": [
            "HVAC systems extracted",
            "ventilation/airflow data extracted",
            "cooling/heating coil outputs available",
            "CO2/temperature hourly outputs available",
            "official amphitheatre test model and evaluation file attached",
        ],
        "next_action": "Exporter les resultats horaires APS/Vista requis pour air fourni, CO2, batteries et puissances.",
    },
    "test_5": {
        "source": "SIA 4010:2023 FR, tableau 62 page PDF 46; tableau 66 page PDF 52",
        "domain": "CTA multizone complexe avec recuperation chaleur/humidite",
        "model_requirements": [
            "multizone HVAC/AHU data extracted",
            "fan control identifier documented",
            "heat/moisture recovery type documented",
            "humidifier type/control documented",
            "official test 5 variant/evaluation file attached",
        ],
        "next_action": "Mapper AHU VE vers variantes 5A-5D: FAN_CTRL, recuperateur et humidificateur.",
    },
    "test_6": {
        "source": "SIA 4010:2023 FR, tableau 62 page PDF 46; annexe A page PDF 51",
        "domain": "Ventilation trois niveaux avec recuperation et debordement",
        "model_requirements": [
            "ventilation systems extracted",
            "constant airflow and stage data documented",
            "heat recovery data documented",
            "restaurant/kitchen overflow represented",
            "official test 6 evaluation file attached",
        ],
        "next_action": "Extraire debits, niveaux, recuperation et logique de debordement restaurant/cuisine.",
    },
    "test_7": {
        "source": "SIA 4010:2023 FR, tableau 62 page PDF 46; annexe A page PDF 51",
        "domain": "Emission, distribution, stockage, production chaud/froid",
        "model_requirements": [
            "heating/cooling demand outputs available",
            "final energy by system/carrier available",
            "emission/distribution/storage/generation data documented",
            "pump/fan/auxiliary energy available",
            "official test 7 loads and evaluation file attached",
        ],
        "next_action": "Lire les sorties APS/Vista et separer besoins, energie finale, auxiliaires, stockage et production.",
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
    # Le PDF SIA 4010 ne définit pas de limites bâtiment autonomes en kWh/m2 ou
    # CO2. Ces clés sont conservées seulement pour de futurs indicateurs client.
    "heating_demand_max": None,
    "cooling_demand_max": None,
    "primary_energy_max": None,
    "co2_emissions_max": None,
    "renewable_energy_min": None,
}

# =============================================================================
# POIDS DES CATÉGORIES POUR LE COMPLIANCE SCORE
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
        "implemented_rule": "SIA3801_U_VALUE_EXTERNAL_WALL",
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
        "implemented_rule": "SIA3801_U_VALUE_ROOF",
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
        "implemented_rule": "SIA3801_U_VALUE_FLOOR",
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
        "implemented_rule": "SIA3801_U_VALUE_WINDOW",
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
        "implemented_rule": "SIA3801_SOLAR_FACTOR",
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
        "automation": "NOT_IMPLEMENTED",
        "implemented_rule": "",
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
        "automation": "NOT_IMPLEMENTED",
        "implemented_rule": "",
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
        "automation": "NOT_IMPLEMENTED",
        "implemented_rule": "SIA3801_VENTILATION_RATE",
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
        "automation": "NOT_IMPLEMENTED",
        "implemented_rule": "SIA3801_HVAC_EFFICIENCY",
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
        "automation": "NOT_IMPLEMENTED",
        "implemented_rule": "SIA3801_HVAC_EFFICIENCY",
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
        "automation": "NOT_IMPLEMENTED",
        "implemented_rule": "",
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
    "hvac": 0.20,        # Poids des systèmes CVC
    "energy": 0.15,      # Poids de l'énergie (consommation, émissions)
    "simulation": 0.05,  # Poids des tests de simulation (SIA 4010)
}

# =============================================================================
# POIDS DES TESTS SIA 4010
# =============================================================================
SIA4010_TEST_WEIGHTS = {
    "test_1": 0.15,  # BESTEST (Enveloppe de base)
    "test_2": 0.10,  # Contrôle du Sonnenschutz
    "test_3": 0.10,  # Contrôle de l'éclairage
    "test_4": 0.10,  # Système CVC (Einzelraum)
    "test_5": 0.15,  # Système CVC (Mehrzonen)
    "test_6": 0.10,  # Lüftungsanlage (Système de ventilation)
    "test_7": 0.30,  # Besoins énergétiques totaux
}

# =============================================================================
# FACTEURS D'ÉMISSION CO₂ (kg CO₂/kWh)
# =============================================================================
EMISSION_FACTORS = {
    "electricity": 0.05,   # Mix électrique suisse
    "gas": 0.20,          # Gaz naturel
    "oil": 0.25,          # Fioul
    "wood": 0.02,         # Bois
    "solar": 0.0,         # Solaire
    "wind": 0.0,          # Éolien
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
    "results_filename": "swiss_compliance_simulation",  # Nom du fichier de résultats
    "simulation_timestep": 2,  # 0=1min, 1=2min, 2=6min, 3=10min, 4=30min
    "reporting_interval": 2,   # 0=6min, 1=10min, 2=30min, 3=60min
    "HVAC": True,              # Inclure les systèmes CVC
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
# PÉNALITÉS PAR TYPE D'ALERTE (pour le calcul du Health Score)
# =============================================================================
PENALTIES = {
    "missing_template": 5.0,       # Template thermique manquant
    "missing_hvac": 5.0,           # Système CVC manquant
    "missing_construction": 2.0,   # Construction manquante
    "zero_area_room": 8.0,         # Pièce avec une surface nulle
    "zero_volume_room": 8.0,       # Pièce avec un volume nul
    "tiny_area_room": 3.0,         # Pièce avec une surface ≤ 1 m²
    "tiny_volume_room": 2.0,       # Pièce avec un volume ≤ 2 m³
    "duplicate_room_name": 2.0,    # Nom de pièce dupliqué
    "suspicious_wwr": 3.0,         # WWR > 0.80 ou < 0 sur les murs extérieurs
    "zero_area_surface": 3.0,      # Surface avec une aire nulle
    "no_external_openings": 2.0,   # Aucune ouverture externe
    "missing_occupancy": 4.0,      # Profil d'occupation manquant
    "missing_lighting": 3.0,       # Profil d'éclairage manquant
    "missing_equipment": 2.0,      # Profil d'équipements manquant
    "missing_ventilation": 4.0,    # Profil de ventilation manquant
    "missing_infiltration": 3.0,   # Profil d'infiltration manquant
    "invalid_opening": 2.0,         # Ouverture invalide
}
