"""
Configuration des seuils SIA 380/2, SIA 4010, et poids des scores.
Ce module centralise toutes les constantes utilisées par le Swiss Compliance Checker.
"""

# =============================================================================
# SEUILS SIA 380/2 (U-values en W/m²K)
# =============================================================================
SIA3801_U_VALUES = {
    "external_wall": 0.24,  # U-value maximale pour les murs extérieurs
    "roof": 0.20,          # U-value maximale pour les toitures
    "floor": 0.24,         # U-value maximale pour les planchers
    "window": 1.3,         # U-value maximale pour les fenêtres
    "door": 1.5,           # U-value maximale pour les portes
    "thermal_bridge": 0.05,  # Valeur maximale pour les ponts thermiques (W/mK)
}

# =============================================================================
# SEUILS SIA 380/2 (Autres)
# =============================================================================
SIA3801_THRESHOLDS = {
    "ventilation_rate_min": 0.5,   # Débit de ventilation minimal (h⁻¹)
    "hvac_efficiency_min": 0.9,    # Rendement minimal des systèmes CVC (90%)
    "lighting_power_max": 12,      # Puissance maximale d'éclairage (W/m²) pour les bureaux
    "equipment_power_max": 20,     # Puissance maximale des équipements (W/m²) pour les bureaux
    "renewable_energy_min": 0.2,   # Part minimale des énergies renouvelables (20%)
    "primary_energy_max": 100,     # Consommation maximale d'énergie primaire (kWh/m²/an)
    "solar_factor_max": 0.6,       # Facteur solaire maximal pour les fenêtres
    "wwr_max": 0.3,               # Window-to-Wall Ratio maximal (30%)
}

# =============================================================================
# SEUILS SIA 4010
# =============================================================================
SIA4010_THRESHOLDS = {
    "heating_demand_max": 50,      # Besoin maximal en chauffage (kWh/m²/an)
    "cooling_demand_max": 20,      # Besoin maximal en refroidissement (kWh/m²/an)
    "primary_energy_max": 100,     # Consommation maximale d'énergie primaire (kWh/m²/an)
    "co2_emissions_max": 20,       # Émissions maximales de CO₂ (kg CO₂/m²/an)
    "renewable_energy_min": 0.2,   # Part minimale des énergies renouvelables (20%)
}

# =============================================================================
# POIDS DES CATÉGORIES POUR LE COMPLIANCE SCORE
# =============================================================================
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
