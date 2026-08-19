# -*- coding: utf-8 -*-
"""VE adapter -- SIA 4010 Test no. 1 (ASHRAE 140 / EN ISO 52016-1 ch. 7).

This module is the ONLY place in the repository that imports `iesve`. It
translates between the VE API (VEScripts) and the normalised JSON expected by
`engine/test1_engine.py::evaluer_test1()`. The engine must never know that
VE exists (CLAUDE.md, "separation dur/pur"); this adapter must never
invent a value, tolerance or standard article (CLAUDE.md, rule no. 1).

Written in cautious Python 3.4 style (no f-strings, no `dataclasses`) --
ADR-001 §2 has NOT settled the Python version embedded in VEScripts at
the time this file was written; see `ve_adapter/Run_VE_Probe_Runtime.py`.
No compatibility rule is therefore *guaranteed*, but this choice remains
cost-free and avoids breaking the product if the VE 2023 guide (Python 3.4.3,
§2.2 of the ADR) proves correct.

--------------------------------------------------------------------------
WHAT HAS BEEN VERIFIED (each `iesve` symbol cited below was read in
`refs/VEScripts-API-VE2023.pdf`, indicated section -- text extraction
`pdftotext -layout`, read in full):
--------------------------------------------------------------------------
  - `iesve.VEProject.get_current_project()`                           §6.1.40
  - `VEProject.create_profile(type, reference, modulating, units)`    §6.1.40
  - `VEProject.save_profiles()`                                       §6.1.40
  - `VEProject.thermal_templates(assigned, allow_ncm)`                §6.1.40
  - `VEProfile.set_data(...)` / `get_data()`                          §6.1.39
  - `VECdbDatabase.get_current_database()` / `.get_projects()`        §6.1.29
  - `VECdbProject.create_material(material_category)`                §6.1.32
  - `VECdbProject.create_construction(element_category)`              §6.1.32
  - `VECdbProject.get_material(_ids)` / `get_construction(_ids)`      §6.1.32
  - `VECdbProject.material_categories` / `.element_categories` /
    `.construction_class` (enums -- EXACT values not reliably re-read,
    source table corrupted by multi-column text extraction, cf. note
    below: resolved dynamically, never hard-coded)   §6.1.32
  - `VECdbMaterial.set_properties()/get_properties()` : `conductivity`,
    `density`, `specific_heat_capacity`, `thickness`, `inside_emissivity`,
    `outside_emissivity`, `inside_reflectance`, `outside_reflectance`,
    `transmittance`, `visible_transmittance`, `refractive_index`,
    `surface_type`, `description`, `angular_dependence`,
    `vapour_resistivity`                                              §6.1.31
  - `VECdbConstruction.add_layer(material_id, is_cavity)` /
    `insert_layer()` / `delete_layer(layer_id)` / `get_layers()` /
    `set_const_class()` / `set_properties()` (incl.
    `outside_surface_resistance`, `outside_surface_emissivity`,
    `inside_surface_resistance`, `inside_surface_emissivity` -- AT
    CONSTRUCTION LEVEL, not only at layer level: cf. reservation below) §6.1.28
  - `VECdbLayer.set_properties()/get_properties()` : `convection_coefficient`
    (W/m2K), `resistance` (m2K/W), `thickness` (m) -- AT LAYER LEVEL       §6.1.30
  - `VEThermalTemplate.set_room_conditions(dict)` /
    `get_room_conditions()` / `add_air_exchange()` / `add_gain()` /
    `apply_changes()`                                                 §6.1.46
  - `iesve.ApacheSim()` ; `.set_options(dict)` / `.get_options()` /
    `.run_simulation(queue_to_tasks=False)`                           §6.1.3
  - `iesve.ResultsReader.open(filename)` ; `.get_room_list()` /
    `.get_room_results(room_id, aps_var, vista_var, var_level,
    start_day=-1, end_day=-1)` / `.get_variables()` / `.get_units()`  §6.1.14
  - `iesve.VELocate()` ; `.open_wea_data()` / `.set(dict)` (key
    `weather_file`) / `.save_and_close()`                             §6.1.36
  - `iesve.ImportGBXML.Import_file(file_name, heal_geometry, cap_mode,
    cap_height)` -- NOTE CASING: method documented with a capital "I"
    ("Import_file"), whereas `swiss_sia/reference_model/
    ve_api.py:493` (external repo, not carried here) calls
    `self.iesve.ImportGBXML.import_file(...)` in lowercase -- possible bug
    in that external repo, NEVER verified under real conditions (neither by
    them nor by us). This module uses the documented casing.          §6.1.9

--------------------------------------------------------------------------
WHAT HAS NOT BEEN VERIFIED -- stated honestly, marked `# ⚠ A VERIFIER API`
in the code, never filled in by guesswork:
--------------------------------------------------------------------------
  1. **Geometry creation (bodies/rooms) -- NOT PROVIDED HERE.** The
     documented API shows no constructor of type "create a room/body from
     scratch" outside of gbXML import
     (`ImportGBXML.Import_file`, §6.1.9). This module does NOT generate
     gbXML and does NOT import geometry: writing a valid gbXML without being
     able to verify it against a real VE would be creating yet more
     unverifiable content, contrary to doctrine (CLAUDE.md, rule no. 1). This
     point is explicitly left open -- `GEOMETRIE_CELLULE` (below) documents
     the verified dimensions, but their translation into VE objects (via gbXML
     or any other means) remains to be done by `ve-adapter-engineer` against a
     real VE. All functions in this module that follow (materials,
     constructions, thermal template, simulation, extraction) assume a cell
     ALREADY modelled (manual import or future verified mechanism).
  2. **Which setting actually controls the external surface coefficient in
     ApacheSim at each time step?** Table 7-7 (ASHRAE 140:2023, verified word
     for word by `norm-analyst`, `traceability/test-1.spec.md` §3.1) gives
     the values. But TWO distinct API mechanisms exist and neither has been
     verified against a real simulation:
       (a) `VECdbLayer.set_properties({'convection_coefficient': ...})`
           on the EXTERNAL layer of the construction (cited by ADR-001 §3
           as "the" mechanism);
       (b) `VECdbConstruction.set_properties({'outside_surface_resistance':
           ..., 'outside_surface_emissivity': ...})` AT CONSTRUCTION LEVEL
           (found by reading §6.1.28 for THIS document -- not cited by
           ADR-001 §3, which only mentions (a)).
     Nothing proves that (a) or (b) -- or neither -- controls the DYNAMIC
     ApacheSim calculation (they might only affect the "static" U-value
     displayed in the Constructions dialog). The function
     `appliquer_coefficient_surface_externe_table_7_7()` below
     is provided as a DOCUMENTED TRIAL, disabled by default
     (`appliquer=False`), and is NOT invoked by the case generation pipeline
     without an explicit decision from the caller. Point referred back to
     `ve-adapter-engineer` (next session with real VE) and
     `norm-analyst` -- cf. `traceability/test-1.spec.md` §8 pt 6.
  3. **Instantiation of a new `AirExchange` / `EnergyGain`.** The PDF
     documents `get()`/attributes for ALREADY EXISTING instances
     (§6.1.2 AirExchange, §6.1.5 CasualGain/EnergyGain) but no
     "Basic usage" example shows how to create a NEW instance from
     a script (unlike `iesve.ApacheSim()`, `iesve.VELocate()`,
     which have an explicit example). This module assumes `iesve.AirExchange()`
     and `iesve.EnergyGain()` for consistency with the rest of the library,
     but THIS SPECIFIC POINT IS NOT CONFIRMED -- marked `# ⚠ A VERIFIER API`.
  4. **Exact APS variable names** ("Room units heating load", "Comfort
     temperature", etc.). The API explicitly states that these names appear in
     a separate "units spreadsheet", absent from `/refs`, and that the only
     reliable source is `get_variables()` at runtime. This module therefore
     hard-codes NO variable name in the "trusted" extraction path:
     `LIAISONS_APS_CANDIDATES` (below) carries, as UNCONFIRMED CANDIDATES,
     the names found in the external repository
     `IES-Intership-general-repo/config/sia4010_aps_bindings_ve_runtime.json`
     (whose author claims to have obtained them via a real VE probe on
     2026-07-28/29) -- a claim that CANNOT be revalidated here (no VE in
     this environment). `extraire_candidat_test1()` REFUSES to use them
     unless the caller explicitly passes
     `accepter_liaisons_non_confirmees=True`, and then announces this in
     the produced JSON (key `_provenance`).
  5. **Numerical values of light/heavy materials and glazing.**
     `traceability/test-1.spec.md` §4/§8 keeps them `[REQUIS]`: the
     ASHRAE 140:2023 Table 7-2/7-27 trail is "a documented starting point with
     strong presumption, NOT a proof" (two unresolved reservations: 2017 vs
     2023 version of the standard, bold not preserved by text extraction).
     This module carries them identically (same figures, same reservation);
     see `MATERIAUX_LEGERS`/`MATERIAUX_LOURDS` below. Glazing and
     infiltration remain entirely `[REQUIS]` -- not provided here.

None of the above is resolved by this file. It sets the extraction contract
(the real deliverable of this step) and provides a case generation pipeline
that fails explicitly, with a precise message, everywhere one of the above
points actually blocks execution.
"""

import calendar
import json
import os


# --------------------------------------------------------------------------
# Normative constants -- all sourced, no invented values.
# --------------------------------------------------------------------------

# The 7 mandatory cases of Test 1 (docs/ADR-001-architecture-MSP.md §5 ;
# traceability/test-1.spec.md §7). "1E" is the only one carrying a criterion.
CAS_TEST1 = ('600', '640', '900', '940', '1E', '600FF', '900FF')

MASSE_PAR_CAS = {
    '600': 'legere', '640': 'legere', '600FF': 'legere',
    '900': 'lourde', '940': 'lourde', '900FF': 'lourde',
    '1E': 'legere',  # 1E = 1D diagnostic case, based on case 600 (light).
}

# Monthly keys identical to those in `test-1.ref.json` / `test1_engine.py`.
MOIS = (
    'month_01', 'month_02', 'month_03', 'month_04', 'month_05', 'month_06',
    'month_07', 'month_08', 'month_09', 'month_10', 'month_11', 'month_12',
)

ANNEE_SIMULATION = 2011  # traceability/test-1.spec.md §4 : "1.1.2011-31.12.2011".
assert not calendar.isleap(ANNEE_SIMULATION)  # safeguard: the monthly aggregation
# below assumes a 365-day year (8760 h at hourly time step).

# --------------------------------------------------------------------------
# Cell geometry -- traceability/test-1.spec.md §4 (Figure 2),
# independently cross-checked with the external repository (config
# `sia4010_classes_1a_1b.json`, parameters `cell_*`/`south_window_*`,
# status CONFIRMED in THAT external repository): both sources agree and
# close dimensionally (2*0.5 + 2*3.0 + 1.0 = 8.0 m = south facade width).
# Audit verdict: KEEP (AUDIT.md, "Element audite n 2", §A).
GEOMETRIE_CELLULE = {
    'largeur_facade_sud_m': 8.0,
    'profondeur_m': 6.0,
    'hauteur_m': 2.7,
    'nombre_fenetres_sud': 2,
    'largeur_fenetre_m': 3.0,
    'hauteur_fenetre_m': 2.0,
    'allege_m': 0.2,
    'trumeau_lateral_m': 0.5,
    'trumeau_central_m': 1.0,
}


def _verifier_fermeture_geometrie(g=GEOMETRIE_CELLULE):
    """Safeguard: the geometry must close dimensionally (cf. spec §4)."""
    largeur_calculee = (
        2.0 * g['trumeau_lateral_m'] +
        g['nombre_fenetres_sud'] * g['largeur_fenetre_m'] +
        g['trumeau_central_m']
    )
    if abs(largeur_calculee - g['largeur_facade_sud_m']) > 1e-9:
        raise ValueError(
            'Geometrie de la cellule Test 1 incoherente : facade calculee '
            '{0} m != largeur declaree {1} m'.format(
                largeur_calculee, g['largeur_facade_sud_m']))


_verifier_fermeture_geometrie()


# Table 7-2 (light case) and Table 7-27 (heavy case), ASHRAE 140:2023 --
# verified word for word by `norm-analyst` (traceability/test-1.spec.md §4).
# STATUS: "strong presumption, NOT a proof" -- SIA 4010 formally cites
# EN ISO 52016-1:2017 (absent from /refs) as source; two unresolved
# reservations (2017 vs 2023 version; bold deltas not preserved by text
# extraction). Reproduced HERE IDENTICALLY from the spec -- NOT a new value,
# NOT an additional confirmation.
#
# Fields: conductivity [W/(m.K)], thickness [m], density [kg/m3],
# specific heat capacity [J/(kg.K)]. Order: interior -> exterior.
MATERIAUX_LEGERS = {
    'mur': (
        {'nom': 'plasterboard', 'conductivite': 0.16, 'epaisseur': 0.012,
         'masse_volumique': 950.0, 'capacite_thermique': 840.0},
        {'nom': 'fiberglass_quilt', 'conductivite': 0.04, 'epaisseur': 0.066,
         'masse_volumique': 12.0, 'capacite_thermique': 840.0},
        {'nom': 'wood_siding', 'conductivite': 0.14, 'epaisseur': 0.009,
         'masse_volumique': 530.0, 'capacite_thermique': 900.0},
    ),
    # RESERVATION LIFTED on 2026-08-07. The cp values for the roof were marked
    # None because the TEXT EXTRACTION of the table shifted them by one column.
    # They are now read from an INDEPENDENT source of that extraction:
    # `config/iso52016_chapter7_confirmed_inputs.json`, Table 23 page 124 of
    # BS EN ISO 52016-1:2017, captured as images whose sha256 is recorded.
    # Two distinct paths, same values -- this is no longer an assumption.
    #
    # The densities already present (950, 12, 530) also agree there,
    # which corroborates the column alignment.
    'toit': (
        {'nom': 'plasterboard_toit', 'conductivite': 0.16, 'epaisseur': 0.010,
         'masse_volumique': 950.0, 'capacite_thermique': 840.0},
        {'nom': 'fiberglass_quilt_toit', 'conductivite': 0.04, 'epaisseur': 0.1118,
         'masse_volumique': 12.0, 'capacite_thermique': 840.0},
        {'nom': 'roofdeck', 'conductivite': 0.14, 'epaisseur': 0.019,
         'masse_volumique': 530.0, 'capacite_thermique': 900.0},
    ),
    'plancher': (
        {'nom': 'timber_flooring', 'conductivite': 0.14, 'epaisseur': 0.025,
         'masse_volumique': 650.0, 'capacite_thermique': 1200.0},
        {'nom': 'floor_insulation', 'conductivite': 0.04, 'epaisseur': 1.003,
         'masse_volumique': 0.0, 'capacite_thermique': 0.0},  # cf. note
    ),
}
# The reservation on roof cp values (traceability/test-1.spec.md §4, column
# shifted during text extraction) is LIFTED: cf. comment above the 'toit'
# block. It was not lifted by re-reading the same extraction, but by
# confronting an independent capture of Table 23.
# FLOOR INSULATION: RESERVATION LIFTED on 2026-08-07, by a probe in VE.
#
# ISO 52016-1 Table 23 (p. 124) gives for `ideal_floor_insulation` a density
# of 0, a specific heat of 0 and a surface capacity of 0:
# it is an IDEAL insulator, with no mass. ASHRAE 140:2023 note (a) states the
# application rule: "minimum density/specific heat the tested software
# allows, but not < 0". The value was therefore SOFTWARE-DEPENDENT by
# design of the standard, and could not be read from any document.
#
# It was PROBED. `_echelle_de_minimum` wrote then re-read 0 / 0.001 / 0.01
# / 0.1 / 1 / 10 on a test material. VE KEEPS 0.0 EXACTLY:
#
#     {"ecrit": 0.0, "density_relu": 0.0, "cp_relu": 0.0, "conserve": true}
#
# The minimum VE allows is therefore zero, it is not < 0, and it coincides
# with the ISO 52016-1 value. Both standards converge: no compromise
# is necessary, and the 10 kg/m3 / 1400 J/(kg.K) from the external repo
# (noted in AUDIT.md as an undocumented choice) was indeed excessive.

MATERIAUX_LOURDS = {
    'mur': (
        {'nom': 'concrete_block', 'conductivite': 0.51, 'epaisseur': 0.100,
         'masse_volumique': 1400.0, 'capacite_thermique': 1000.0},
        {'nom': 'foam_insulation', 'conductivite': 0.04, 'epaisseur': 0.0615,
         'masse_volumique': 10.0, 'capacite_thermique': 1400.0},
        {'nom': 'wood_siding', 'conductivite': 0.14, 'epaisseur': 0.009,
         'masse_volumique': 530.0, 'capacite_thermique': 900.0},
    ),
    # Roof identical to the light case (ASHRAE 140:2023, note c, confirmed
    # word for word by norm-analyst: "high-mass case roof is the same as
    # the low-mass case roof").
    'toit': MATERIAUX_LEGERS['toit'],
    'plancher': (
        {'nom': 'concrete_slab', 'conductivite': 1.13, 'epaisseur': 0.080,
         'masse_volumique': 1400.0, 'capacite_thermique': 1000.0},
        {'nom': 'floor_insulation_lourd', 'conductivite': 0.04, 'epaisseur': 1.007,
         'masse_volumique': 0.0, 'capacite_thermique': 0.0},  # same note as above
    ),
}

MATERIAUX_PAR_MASSE = {'legere': MATERIAUX_LEGERS, 'lourde': MATERIAUX_LOURDS}


# Table 7-7 ASHRAE 140:2023 -- alternative EXTERNAL surface coefficients,
# zero wind, verified word for word (traceability/test-1.spec.md §3.1). Column
# choice = function of ApacheSim convection algorithm
# (§7.2.1.9.3 (a)/(b.1)/(b.2), NOT SETTLED -- cf. point 2 of the docstring).
COEFFICIENTS_SURFACE_TABLE_7_7 = {
    'mur': {'convectif_seul': 11.9, 'combine': 21.6},
    'toit': {'convectif_seul': 14.4, 'combine': 21.8},
    'plancher_surelevee': {'convectif_seul': 0.8, 'combine': 5.2},
    'fenetre': {'convectif_seul': 8.0, 'combine': 17.8},
}

# Setpoints (traceability/test-1.spec.md §4) -- ideal elements, no real HVAC
# ("HLK-Anlage : Keine vorhanden").
CONSIGNE_CHAUFFAGE_C = 20.0
CONSIGNE_REFROIDISSEMENT_C = 27.0
CONSIGNE_CHAUFFAGE_REDUITE_C = 10.0  # cases 640/940, 23:00-07:00
HEURE_DEBUT_CONFORT = 7   # 07:00
HEURE_FIN_CONFORT = 23    # 23:00
GAIN_EQUIPEMENT_W = 200.0  # constant, 24h/24, all year.

CAS_AVEC_CONSIGNE_REDUITE = ('640', '940')
CAS_FLOTTEMENT_LIBRE = ('600FF', '900FF')
CAS_AVEC_CONDITIONNEMENT = ('600', '640', '900', '940', '1E')


# --------------------------------------------------------------------------
# Lazy import of `iesve` -- never at module level, so that this
# file remains readable/inspectable by tools that don't have VE
# (cf. convention already adopted in `ve_adapter/Run_VE_Probe_Runtime.py`).
# --------------------------------------------------------------------------

def _iesve():
    """Imports `iesve` on demand; precise error if VE is unavailable."""
    try:
        import iesve
        return iesve
    except ImportError as erreur:
        raise ImportError(
            "Module 'iesve' indisponible : ce code doit s'executer depuis "
            "la fenetre Scripts d'IESVE (VEScripts), pas en Python autonome. "
            "Erreur d'origine : " + str(erreur))


def _resoudre_membre_enum(conteneur, nom_attribut_enum, nom_membre):
    """Dynamically resolves an `iesve` enum member -- NEVER hard-codes
    the exact spelling of a member (e.g. `material_categories.opaque`) because
    the source table in `refs/VEScripts-API-VE2023.pdf` §6.1.32 is corrupted
    by multi-column text extraction (columns from several enums merged):
    no member spelling there is reliable. Precise error if absent.
    """
    enum = getattr(conteneur, nom_attribut_enum, None)
    if enum is None:
        raise AttributeError(
            "Enum 'iesve.{0}.{1}' introuvable -- l'API a peut-etre change de "
            "nom depuis VEScripts-API-VE2023.pdf §6.1.32.".format(
                conteneur, nom_attribut_enum))
    membre = getattr(enum, nom_membre, None)
    if membre is None:
        raise AttributeError(
            "Membre '{0}' introuvable dans l'enum 'iesve.{1}.{2}' -- "
            "verifier l'orthographe exacte cote VE (non lisible de facon "
            "fiable dans refs/VEScripts-API-VE2023.pdf, tableau corrompu par "
            "l'extraction texte).".format(nom_membre, conteneur, nom_attribut_enum))
    return membre


# --------------------------------------------------------------------------
# Material and construction creation (VECdbMaterial, VECdbConstruction,
# VECdbLayer -- §6.1.28/30/31/32).
#
# Write pattern (create, write properties, RE-READ and VERIFY the
# return of `get_properties()`, fail loudly on divergence) inspired by
# `IES-Intership-general-repo/swiss_sia/reference_model/ve_asset_provisioner.py`
# (`_create_materials`/`_create_construction`, audit verdict KEEP for the
# PATTERN only -- cf. AUDIT.md, "Element audite n 2", §B.1). The code
# below is rewritten here, not copied: shorter, specific to Test 1,
# without the generic reuse/disambiguation logic (out of scope --
# this module assumes a disposable VE project, dedicated to one case at a
# time, in accordance with the caution already established by that same
# external repo ("Run it only in a fresh saved disposable project",
# case_registry.py).
# --------------------------------------------------------------------------

def creer_materiau(cdb_project, definition):
    """Creates an opaque CDB material and VERIFIES the readback of its properties.

    `definition`: one of the dicts from `MATERIAUX_LEGERS`/`MATERIAUX_LOURDS`
    (single layer). Raises a precise error if a numerical property is
    `None` (cf. documented reservations above on roof cp / floor insulation):
    this module refuses to create a material with an invented property.
    """
    iesve = _iesve()
    for cle in ('conductivite', 'epaisseur', 'masse_volumique', 'capacite_thermique'):
        if definition.get(cle) is None:
            raise ValueError(
                "Materiau '{0}' : propriete '{1}' non confirmee (cf. "
                "reserves documentees dans test1_adapter.py sur les Tables "
                "7-2/7-27 ASHRAE 140:2023) -- creation refusee plutot que "
                "d'inventer une valeur.".format(definition['nom'], cle))
    # CORRECTED on 2026-08-06, after probe v2 in a real VE.
    #
    # Two cumulative errors here:
    #   1. the enum lives on the MODULE `iesve`, not on `VECdbProject` -- that
    #      is what the probe reported with "Enum ... introuvable";
    #   2. `material_categories` has NO member `opaque`. Its 20 members
    #      are library families (concretes, insulating, timber, boards...).
    #      `opaque` belongs to `construction_class`, not here:
    #      the two enums had been confused.
    #
    # `other` is a LIBRARY CLASSIFICATION choice, with no effect on the
    # simulation -- the physical properties are carried by `definition`.
    # Stating it clearly rather than leaving the impression it is a physical
    # parameter.
    categorie_materiau = _resoudre_membre_enum(
        iesve, 'material_categories', 'other')
    materiau = cdb_project.create_material(categorie_materiau)
    # CORRECTED on 2026-08-07, against a real VE. `set_properties` converts
    # ALL values to float: passing a string raises
    # "could not convert string to float: 'plasterboard'".
    #
    # Keys actually accepted, observed via `get_properties()` on a new
    # material: id, description, specific_heat_capacity, category,
    # conductivity, density, vapour_resistivity.
    #
    #   * `description` is READ there but NOT WRITTEN -- after writing it
    #     always reads "New Python Material". The material name must therefore
    #     be carried differently; it remains here as a traceability comment.
    #   * `thickness` DOES NOT EXIST at material level. Thickness belongs to
    #     the LAYER (`VECdbLayer`, §6.1.30), which is physically correct:
    #     the same material can be used at several thicknesses. The module
    #     docstring already noted this; the code contradicted it.
    proprietes = {
        'conductivity': definition['conductivite'],
        'density': definition['masse_volumique'],
        'specific_heat_capacity': definition['capacite_thermique'],
    }
    materiau.set_properties(proprietes)
    _verifier_proprietes_ecrites(materiau, proprietes, definition['nom'])
    relu = dict(materiau.get_properties())
    for cle, valeur in proprietes.items():
        valeur_relue = relu.get(cle)
        if valeur_relue is None or abs(float(valeur_relue) - float(valeur)) > 1e-6:
            raise RuntimeError(
                "VECdbMaterial.set_properties() : releture divergente pour "
                "'{0}' du materiau '{1}' (ecrit={2}, relu={3}). Le materiau "
                "cree ne correspond pas a la demande -- ne pas continuer."
                .format(cle, definition['nom'], valeur, valeur_relue))
    return materiau


def creer_construction_opaque(cdb_project, categorie_element, classe_construction,
                               couches):
    """Creates a multi-layer opaque construction (wall/roof/floor).

    `categorie_element`: name of the `element_categories` enum member
    (e.g. 'wall', 'roof', 'ground_floor' -- §6.1.32; EXACT spelling not
    reliably readable from the corrupted PDF, must CONFIRM against VE before
    first real use, cf. `_resoudre_membre_enum`).
    `classe_construction`: name of the `construction_class` enum member.
    `couches`: sequence of material dicts (interior -> exterior), same
    keys as `MATERIAUX_LEGERS`/`MATERIAUX_LOURDS`.

    Returns the created construction (VE object), after verifying that the
    layer count has persisted (cf. AUDIT.md on ve_asset_provisioner:
    VE 2025.2 creates a default layer that must be removed -- same caution
    applied here).
    """
    iesve = _iesve()
    # Both enums live on the MODULE `iesve`, verified by probe v2:
    # element_categories -> roof=0, ceiling/int_floor=1, wall=2, partition=3,
    # ground_floor=4, roof_light=5, ext_glazing=6, int_glazing=7, door=8;
    # construction_class -> opaque=0, glazed=1, shade=4, misc=5, none=-1.
    categorie = _resoudre_membre_enum(
        iesve, 'element_categories', categorie_element)
    classe = _resoudre_membre_enum(
        iesve, 'construction_class', classe_construction)
    construction = cdb_project.create_construction(categorie)
    construction.set_const_class(classe)

    couches_par_defaut = list(construction.get_layers())
    identifiants_par_defaut = [couche.get_id() for couche in couches_par_defaut]

    materiaux_crees = []
    for definition in couches:
        materiau = creer_materiau(cdb_project, definition)
        materiaux_crees.append(materiau)
        materiau_id = _identifiant_materiau(materiau)
        if materiau_id is None:
            raise RuntimeError(
                "Materiau '{0}' cree sans identifiant persistant -- "
                "impossible de l'ajouter a la construction.".format(
                    definition['nom']))
        construction.add_layer(materiau_id, False)  # False = not a cavity
        _poser_epaisseur_de_couche(construction, definition)

    for identifiant in identifiants_par_defaut:
        construction.delete_layer(identifiant)

    couches_finales = list(construction.get_layers())
    if len(couches_finales) != len(couches):
        raise RuntimeError(
            "Construction : {0} couches demandees, {1} persistees apres "
            "creation -- ne pas continuer avec une construction "
            "incomplete.".format(len(couches), len(couches_finales)))
    return construction, materiaux_crees


#: Readback relative tolerance. VE stores in 32-bit float: 0.16 written
#: comes back as 0.1599999964237213. An exact comparison would fail on a
#: write that is nevertheless correct, and a tolerance too wide would pass
#: a genuinely wrong value. 1e-6 relative separates the two unambiguously.
TOLERANCE_RELECTURE = 1e-6


#: Default thickness VE assigns to a freshly added layer, in m.
#: Observed on 2026-08-07: `add_layer` writes NO thickness, and the three
#: wall layers all came back at 1 mm instead of 12, 66 and 9 mm.
EPAISSEUR_PAR_DEFAUT_VE_M = 0.001


def _poser_epaisseur_de_couche(construction, definition):
    """Writes the thickness on the LAST added layer, and reads it back.

    WHY THIS FUNCTION EXISTS. `add_layer(materiau_id, False)` creates the
    layer but writes no thickness, and `thickness` does not exist at
    material level. Without this call, the three wall layers came back at
    1 mm -- the construction was created without raising, and its resistances
    were wrong. The probe was green.

    Thickness belongs to the LAYER (`VECdbLayer`, §6.1.30). Keys accepted,
    observed on 2026-08-07: thickness, resistance, convection_coefficient.

    Args:
        construction: `VECdbConstruction` being assembled.
        definition: Layer from the reference data, carrying `epaisseur` and `nom`.

    Raises:
        RuntimeError: If the thickness is not accepted. A 1 mm layer
            would simulate without signalling anything.
    """
    couches = list(construction.get_layers() or [])
    if not couches:
        raise RuntimeError(
            "Couche '{0}' ajoutee mais introuvable dans get_layers().".format(
                definition['nom']))
    couche = couches[-1]
    attendue = definition['epaisseur']
    couche.set_properties({'thickness': attendue})

    relue = (couche.get_properties() or {}).get('thickness')
    if relue is None or abs(relue - attendue) > TOLERANCE_RELECTURE * attendue:
        raise RuntimeError(
            "Couche '{0}' : epaisseur ecrite {1} m, relue {2} m. VE donne "
            "{3} m par defaut -- une couche laissee a cette valeur simulerait "
            "sans rien signaler.".format(
                definition['nom'], attendue, relue, EPAISSEUR_PAR_DEFAUT_VE_M))


def _identifiant_materiau(materiau):
    """Persistent identifier of a CDB material.

    CORRECTED on 2026-08-07. The code read `materiau.id`, which does not
    exist: `VECdbMaterial` only exposes `get_properties`, `set_properties` and
    `get_review_summary_string`. The identifier is a KEY in the dictionary
    returned by `get_properties()` -- observed: `{'id': 'PYOP3', ...}`.

    The attribute is still tried first: if a VE version added it, it should
    be used.

    Args:
        materiau: Freshly created `VECdbMaterial`.

    Returns:
        str | None: Identifier, or `None` if not found.
    """
    direct = getattr(materiau, 'id', None)
    if direct is not None:
        return direct
    try:
        return (materiau.get_properties() or {}).get('id')
    except Exception:  # noqa: BLE001 -- absence is a result, not a crash
        return None


def _verifier_proprietes_ecrites(materiau, proprietes, nom):
    """Reads back a material and compares its properties to what was written.

    WHY READ BACK. `set_properties` returns nothing and does not always raise:
    the 2026-08-07 probe showed that `set_heating()` even accepts a call with
    no argument. A silently ignored write would go unnoticed, and the
    simulation would run on default values producing plausible numbers.

    Args:
        materiau: Freshly written `VECdbMaterial`.
        proprietes: What was just requested.
        nom: Material name, for the message.

    Raises:
        RuntimeError: If a property was not accepted, or if readback is
            impossible.
    """
    relues = materiau.get_properties()
    ecarts = []
    for cle, attendu in proprietes.items():
        obtenu = relues.get(cle)
        if obtenu is None:
            ecarts.append(u'%s : absent de la relecture' % cle)
            continue
        reference = abs(attendu) if attendu else 1.0
        if abs(obtenu - attendu) > TOLERANCE_RELECTURE * reference:
            ecarts.append(u'%s : ecrit %r, relu %r' % (cle, attendu, obtenu))
    if ecarts:
        raise RuntimeError(
            u'materiau %r : %d propriete(s) non prise(s) par VE -- %s. '
            u'Cles acceptees par set_properties : conductivity, density, '
            u'specific_heat_capacity, vapour_resistivity.'
            % (nom, len(ecarts), u' ; '.join(ecarts)))


def creer_constructions_cas(cdb_project, masse):
    """Creates the 3 opaque constructions (wall/roof/floor) for a given mass.

    `masse`: 'legere' or 'lourde' (key of `MASSE_PAR_CAS`).
    Returns a dict {'mur': construction, 'toit': ..., 'plancher': ...}.

    SPELLINGS CONFIRMED on 2026-08-06 against a real VE 2025, and frozen
    in `refs/reference-data/iesve-enums-ve2025.json`: element_categories
    wall=2, roof=0, ground_floor=4; construction_class opaque=0. The
    reservation "presumed by consistency of English naming" that appeared here
    is lifted.

    `cdb_project` is a `VECdbProject`, NOT a `VECdbDatabase`: it is the
    project that carries `create_construction`. The probe had confused the two.
    """
    materiaux = MATERIAUX_PAR_MASSE[masse]
    constructions = {}
    constructions['mur'], _ = creer_construction_opaque(
        cdb_project, 'wall', 'opaque', materiaux['mur'])
    constructions['toit'], _ = creer_construction_opaque(
        cdb_project, 'roof', 'opaque', materiaux['toit'])
    constructions['plancher'], _ = creer_construction_opaque(
        cdb_project, 'ground_floor', 'opaque', materiaux['plancher'])
    return constructions


def appliquer_coefficient_surface_externe_table_7_7(construction, type_surface,
                                                      branche, appliquer=False):
    """Applies -- OR NOT -- an external surface coefficient from Table 7-7.

    DISABLED BY DEFAULT (`appliquer=False`): cf. point 2 of the module
    docstring. Writes NOTHING to the layer/construction unless explicitly
    requested.

    `type_surface`: key of `COEFFICIENTS_SURFACE_TABLE_7_7`
    ('mur'/'toit'/'plancher_surelevee'/'fenetre').
    `branche`: 'convectif_seul' or 'combine' (§7.2.1.9.3 (b.1)/(b.2)) --
    NOT SETTLED choice, must be provided explicitly by the caller after
    verifying the ApacheSim convection algorithm (referred back to
    `ve-adapter-engineer`, traceability/test-1.spec.md §8 pt 6).

    Writes to the EXTERNAL layer (`VECdbLayer.set_properties
    ({'convection_coefficient': ...})`, §6.1.30) -- mechanism (a) of the
    documented reservation above; mechanism (b) (properties at construction
    level) is NOT applied here, for lack of proof that either one (or
    neither) actually drives ApacheSim.
    """
    if not appliquer:
        return None
    valeur = COEFFICIENTS_SURFACE_TABLE_7_7[type_surface][branche]
    couches = list(construction.get_layers())
    if not couches:
        raise RuntimeError('Construction sans couche : impossible de fixer '
                            'le coefficient de surface externe.')
    couche_exterieure = couches[-1]
    couche_exterieure.set_properties({'convection_coefficient': valeur})
    relu = dict(couche_exterieure.get_properties())
    valeur_relue = relu.get('convection_coefficient')
    if valeur_relue is None or abs(float(valeur_relue) - valeur) > 1e-6:
        raise RuntimeError(
            'VECdbLayer.set_properties() : relecture divergente pour '
            'convection_coefficient (ecrit={0}, relu={1}).'.format(
                valeur, valeur_relue))
    return valeur


# --------------------------------------------------------------------------
# Thermal template -- setpoints, profiles, gains, infiltration
# (VEThermalTemplate, VEProfile, AirExchange, EnergyGain -- §6.1.2/5/39/46).
# --------------------------------------------------------------------------

def creer_profil_consigne_chauffage(project, cas_id):
    """Creates the daily heating setpoint profile for a case.

    Cases 600/900/1E/*FF: no profile needed (constant setpoint -- written
    directly via `heating_setpoint` in `set_room_conditions`, no profile).
    Cases 640/940: daily profile 20°C (07h-23h) / 10°C (23h-07h),
    traceability/test-1.spec.md §4.

    Returns the identifier of the created profile, or None if no profile is
    required.
    """
    if cas_id not in CAS_AVEC_CONSIGNE_REDUITE:
        return None
    profil = project.create_profile('daily', 'SIA4010_T1_chauffage_reduit_' + cas_id,
                                     False, 0)
    # VEProfile.set_data() -- daily profile: list [x, y, formula].
    # x = hour (0-24), y = value (degC). Two steps, sharp transitions.
    donnees = [
        [0, CONSIGNE_CHAUFFAGE_REDUITE_C, 0],
        [HEURE_DEBUT_CONFORT, CONSIGNE_CHAUFFAGE_C, 0],
        [HEURE_FIN_CONFORT, CONSIGNE_CHAUFFAGE_REDUITE_C, 0],
        [24, CONSIGNE_CHAUFFAGE_REDUITE_C, 0],
    ]
    if profil.set_data(donnees) is not True:
        raise RuntimeError(
            "VEProfile.set_data() a echoue pour le profil de consigne "
            "reduite du cas {0}.".format(cas_id))
    if project.save_profiles() is not True:
        raise RuntimeError('VEProject.save_profiles() a echoue.')
    return getattr(profil, 'id', None) or getattr(profil, 'reference', None)


def construire_conditions_ambiance(cas_id, profil_chauffage_id=None):
    """Builds the `room_conditions` dict expected by
    `VEThermalTemplate.set_room_conditions()` (§6.1.46) for a given case.

    ⚠ A VERIFIER API: the keys `heating_setpoint_type`/`cooling_setpoint_type`
    documented in refs/VEScripts-API-VE2023.pdf §6.1.46 are poorly
    extracted ("heating_setpoint_typeconstant"/"heating_setpoint_typeprofile"
    -- probable merge of two lines by `pdftotext`). This module writes the
    keys `heating_setpoint`/`cooling_setpoint` (constant values) and
    `heating_profile` (if reduced profile) without explicitly setting
    `*_setpoint_type`: to be completed/corrected with `ve-adapter-engineer`
    once a real VE is available to read `get_room_conditions()` and see the
    exact expected return form.
    """
    conditions = {
        'cooling_setpoint': CONSIGNE_REFROIDISSEMENT_C,
    }
    if cas_id in CAS_FLOTTEMENT_LIBRE:
        # Free float: no active ideal element. Do NOT write a
        # setpoint -- leave the template without heating/cooling.
        # ⚠ A VERIFIER API: exact mechanism to disable an ideal element
        # already configured (remove keys? write a sentinel value?).
        return {}
    if cas_id in CAS_AVEC_CONSIGNE_REDUITE:
        if not profil_chauffage_id:
            raise ValueError(
                "Cas {0} exige un profil de consigne reduite -- appeler "
                "creer_profil_consigne_chauffage() d'abord.".format(cas_id))
        conditions['heating_profile'] = profil_chauffage_id
    else:
        conditions['heating_setpoint'] = CONSIGNE_CHAUFFAGE_C
    return conditions


def creer_gain_equipement(project):
    """Creates the constant 200 W 'equipment' internal gain, 24h/24, all year.

    traceability/test-1.spec.md §4: "Equipements : 200 W au total, profil
    constant 24 h, present toute l'annee".

    ⚠ A VERIFIER API: `iesve.EnergyGain()` (constructor) has NO
    "Basic usage" example in refs/VEScripts-API-VE2023.pdf §6.1.5 -- only
    `get()` and the attributes of an existing instance are documented there.
    This module assumes no-argument construction for consistency with the rest
    of the library (`iesve.ApacheSim()`, `iesve.VELocate()`), without direct
    proof.
    """
    iesve = _iesve()
    gain = iesve.EnergyGain()  # ⚠ A VERIFIER API -- cf. docstring above.
    gain.set({
        'max_power_consumption': GAIN_EQUIPEMENT_W,
        'max_sensible_gain': GAIN_EQUIPEMENT_W,
        'radiant_fraction': 0.0,  # ⚠ A VERIFIER: not specified by Test 1 spec;
        # 0.0 = all convective, DEFAULT value in this module and not a
        # normative value -- to confirm with norm-analyst before real use.
        'type_str': 'Miscellaneous',
        'units_val': 1,  # 1 = W (total), not W/m2 -- §6.1.5.
    })
    return gain


def creer_infiltration(project, taux_infiltration_ach):
    """Creates the 'Infiltration' AirExchange object for Test 1.

    ⚠ NOT USABLE AS IS: the exact infiltration rate remains `[REQUIS]`
    (traceability/test-1.spec.md §4/§8 pt 4 -- refers to EN ISO 52016-1 ch. 7,
    absent from `/refs`). This function therefore invents no default value:
    `taux_infiltration_ach` MUST be provided explicitly by the caller, with
    its own justification/citation, and this function raises if `None`.

    ⚠ A VERIFIER API: `iesve.AirExchange()` (constructor) -- same reservation
    as `creer_gain_equipement()` above (§6.1.2 shows no "Basic usage" with
    constructor).
    """
    if taux_infiltration_ach is None:
        raise ValueError(
            "Taux d'infiltration non fourni : traceability/test-1.spec.md "
            "§8 pt 4 le maintient '[REQUIS]' (EN ISO 52016-1 ch. 7, absent "
            "de /refs). Ne pas inventer une valeur par defaut ici.")
    iesve = _iesve()
    infiltration = iesve.AirExchange()  # ⚠ A VERIFIER API.
    type_infiltration = _resoudre_membre_enum(
        iesve, 'AirExchange_type', 'infiltration')
    infiltration.set({
        'type_val': type_infiltration,
        'max_flow': taux_infiltration_ach,
        'units_val': 0,  # 0 = ach, §6.1.2.
        'adjacent_condition_val': 1,  # 1 = External air, §6.1.2.
    })
    return infiltration


# --------------------------------------------------------------------------
# Case orchestration -- assembles materials/constructions/template.
# --------------------------------------------------------------------------

def generer_cas_test1(project, cdb_project, gabarit_thermique, cas_id,
                       taux_infiltration_ach=None):
    """Generates a Test 1 case (excluding 1E) in the current VE project.

    `gabarit_thermique`: `VEThermalTemplate` object already assigned to the
    rooms of the test cell (assignment/geometry outside the scope of this
    function -- cf. point 1 of the module docstring, geometry not verified
    end-to-end).

    Case '1E' NOT SUPPORTED HERE: requires the fabric blind (Stoffmarkise) from
    diagnostic test 2 E1 (traceability/test-1.spec.md §7), which belongs to
    Test 2, not Test 1. The audited external repo (case_registry.py,
    `IES-Intership-general-repo`) reaches the same conclusion independently:
    case 1E is absent from its list of "apachesim_qualification_supported"
    cases -- a cross-check that reinforces the decision to leave it out of
    scope here rather than improvising a blind model.
    """
    if cas_id == '1E':
        raise NotImplementedError(
            "Cas 1E non supporte par generer_cas_test1() : necessite le "
            "store tissu du test diagnostic 2 E1 (Test 2), hors perimetre "
            "de cet adaptateur Test 1. Voir traceability/test-1.spec.md §7.")
    if cas_id not in CAS_TEST1:
        raise ValueError("Cas Test 1 inconnu : {0!r} (attendus : {1})".format(
            cas_id, CAS_TEST1))

    masse = MASSE_PAR_CAS[cas_id]
    constructions = creer_constructions_cas(cdb_project, masse)

    profil_chauffage_id = None
    if cas_id in CAS_AVEC_CONSIGNE_REDUITE:
        profil_chauffage_id = creer_profil_consigne_chauffage(project, cas_id)

    conditions = construire_conditions_ambiance(cas_id, profil_chauffage_id)
    if gabarit_thermique.set_room_conditions(conditions) is False:
        raise RuntimeError(
            "VEThermalTemplate.set_room_conditions() a renvoye False pour "
            "le cas {0}.".format(cas_id))

    gain = creer_gain_equipement(project)
    gabarit_thermique.add_gain(gain)

    infiltration = None
    if taux_infiltration_ach is not None:
        infiltration = creer_infiltration(project, taux_infiltration_ach)
        gabarit_thermique.add_air_exchange(infiltration)

    gabarit_thermique.apply_changes()

    return {
        'cas_id': cas_id,
        'masse': masse,
        'constructions': constructions,
        'profil_chauffage_id': profil_chauffage_id,
        'gain_equipement': gain,
        'infiltration': infiltration,
    }


def assigner_meteo_drycold(chemin_fichier_meteo):
    """Assigns the DRYCOLD.TMY weather file to the current project (§6.1.36).

    traceability/test-1.spec.md §4: "Fichier meteo : DRYCOLD.TMY (BESTEST)
    Denver, CO". This module does NOT provide the file itself (to be obtained/
    converted separately -- out of scope); it merely points to it.
    """
    iesve = _iesve()
    locate = iesve.VELocate()
    if locate.open_wea_data() == -1:
        raise RuntimeError('VELocate.open_wea_data() a echoue.')
    try:
        locate.set({'weather_file': chemin_fichier_meteo})
    finally:
        locate.save_and_close()


# --------------------------------------------------------------------------
# ApacheSim simulation (§6.1.3).
#
# ⚠ ADR-001 §3 cites `ApacheSim.save_options({...})` (taken from the "Basic
# usage" example in the PDF, line ~960 of the text extraction). But the
# formal "Methods Defined Here" table of the SAME document (§6.1.3.1) does
# NOT list `save_options`: it lists `set_options({options}) -> Bool` and
# `get_options() -> dict`. This is an internal inconsistency in the source
# PDF (not an error introduced here): the usage example appears to be
# outdated relative to the methods table. This module uses `set_options()`/
# `get_options()` (formally documented method, and systematically read back
# after writing below) and does NOT carry over `save_options`. To flag to
# `norm-analyst`/`ve-adapter-engineer`: correct the ADR-001 §3 citation.
# --------------------------------------------------------------------------

def lancer_apachesim_cas(nom_fichier_aps, options_supplementaires=None):
    """Launches an annual ApacheSim simulation for one case and returns the
    name of the generated .aps file.

    traceability/test-1.spec.md §4: period 1.1.2011-31.12.2011, implicit
    hourly time step (not specified by the Test 1 spec -- IESVE default;
    ⚠ A VERIFIER whether a finer step is needed to comply with the
    ASHRAE 140 protocol).
    """
    iesve = _iesve()
    sim = iesve.ApacheSim()
    for methode in ('get_options', 'set_options', 'run_simulation'):
        if not hasattr(sim, methode):
            raise RuntimeError(
                "ApacheSim.{0} indisponible dans cette version de VE -- "
                "verifier refs/VEScripts-API-VE2023.pdf §6.1.3.".format(methode))
    options = {
        'start_month': 1, 'start_day': 1,
        'end_month': 12, 'end_day': 31,
        'HVAC': False,  # Test 1: ideal elements, no real HVAC network.
        'results_filename': nom_fichier_aps,
    }
    if options_supplementaires:
        options.update(options_supplementaires)
    if sim.set_options(options) is not True:
        raise RuntimeError('ApacheSim.set_options() n a pas renvoye True.')
    relues = dict(sim.get_options())
    divergences = {}
    for cle, valeur in options.items():
        valeur_relue = relues.get(cle)
        if valeur_relue != valeur:
            divergences[cle] = (valeur, valeur_relue)
    if divergences:
        raise RuntimeError(
            'ApacheSim.get_options() : relecture divergente apres '
            'set_options() : {0}'.format(divergences))
    if sim.run_simulation(queue_to_tasks=False) is not True:
        raise RuntimeError(
            'ApacheSim.run_simulation(queue_to_tasks=False) n a pas '
            'renvoye True pour {0}.'.format(nom_fichier_aps))
    return nom_fichier_aps


# --------------------------------------------------------------------------
# Result extraction (.aps, ResultsReader -- §6.1.14) -> normalised JSON
# expected by engine/test1_engine.py::evaluer_test1().
#
# FORM CONFIRMED HERE (resolves the "⚠ A VERIFIER" left by
# `engine/test1_engine.py::evaluer_test1`, docstring):
#   - exact mirror of `reference_values` in test-1.ref.json: same
#     quantities, same cases per quantity (verified against the reference
#     JSON itself -- not assumed):
#       sensible_heating_demand_kwh / sensible_cooling_demand_kwh:
#           cases {1E, 600, 640, 900, 940}; node {monthly: {month_01..12},
#           annual: <scalar>}.
#       operative_temperature_monthly_celsius:
#           cases {600, 640, 900, 940, 600FF, 900FF}; node
#           {monthly: {month_01..12, annual: <scalar>}} -- **the annual is
#           NESTED under `monthly`**, not a sibling of `monthly` (asymmetry
#           already noted by AUDIT.md, "remarques non bloquantes" pt 1, for
#           the reference itself -- this module produces a candidate that
#           respects the SAME asymmetry, deliberately, so that
#           `test1_engine.py::_perioder_temperature_mensuelle` applies
#           without modification).
#       operative_temperature_annual_extremes_celsius:
#           cases {600FF, 900FF}; node {extremes: {max, min, average}}.
#   - terminal leaves = **raw numbers** (`float`) or `None` (never
#     a dict `{"value": ...}`): the simpler of the two forms accepted
#     by `test1_engine.py::_valeur_candidate`.
# --------------------------------------------------------------------------

# Unconfirmed candidate bindings -- carried, with explicit attribution,
# from `IES-Intership-general-repo/config/sia4010_aps_bindings_ve_runtime.json`
# (external repo, not consolidated in this repo -- ADR-001 §8 leaves
# consolidation open). The author of that file claims to have obtained them
# via a real VE probe on 2026-07-28/29 (checksum, evidence_locator in the
# source file). That claim CANNOT be revalidated here (no VE in this
# environment) -- audit verdict CORRECT (AUDIT.md, "Element audite n 2",
# §C.2): to be reconfirmed by a real VE probe before any production use.
# `extraire_candidat_test1()` refuses to use them without explicit
# `accepter_liaisons_non_confirmees=True`.
LIAISONS_APS_CANDIDATES = {
    'sensible_heating_power': {
        'aps_varname': 'Room units heating load',
        'display_name': 'Heating plant sensible load',
        'model_level': 'z',
        'unite_attendue': 'kW',
    },
    'sensible_cooling_power': {
        'aps_varname': 'Room units cooling load',
        'display_name': 'Cooling plant sensible load',
        'model_level': 'z',
        'unite_attendue': 'kW',
    },
    'room_air_temperature': {
        'aps_varname': 'Room air temperature',
        'display_name': 'Air temperature',
        'model_level': 'z',
        'unite_attendue': '°C',
    },
    'operative_temperature': {
        'aps_varname': 'Comfort temperature',
        'display_name': 'Dry resultant temperature',
        'model_level': 'z',
        'unite_attendue': '°C',
        # The external repo cites https://help.iesve.com/ve2025/... to
        # justify "dry resultant temperature" = "operative temperature"
        # in still air -- VE2025 page, whereas our refs/ are VE2023:
        # additional version inconsistency, never reconciled here.
    },
}


def decouvrir_candidats_variable(results_file, jetons_requis, niveau=None):
    """Aids DISCOVERY of APS variables -- NOT for trusted extraction
    (no pass/fail verdict should rely on this function).

    Searches by tokens (substrings, case-insensitive) in
    `aps_varname`/`display_name`, returned by `get_variables()` (§6.1.14).
    To be used manually by `ve-adapter-engineer` against a real VE to
    CONFIRM or CORRECT `LIAISONS_APS_CANDIDATES` -- never called by
    `extraire_candidat_test1()`.
    """
    resultats = []
    try:
        variables = results_file.get_variables()
    except Exception as erreur:
        raise RuntimeError(
            'ResultsReader.get_variables() a echoue : {0}'.format(erreur))
    jetons = [jeton.lower() for jeton in jetons_requis]
    for variable in variables or []:
        aps_varname = str(variable.get('aps_varname') or '')
        display_name = str(variable.get('display_name') or '')
        niveau_variable = str(variable.get('model_level') or '')
        hay = (aps_varname + ' ' + display_name).lower()
        if niveau and niveau_variable and niveau_variable.lower() != niveau.lower():
            continue
        if all(jeton in hay for jeton in jetons):
            resultats.append(variable)
    return resultats


def _resoudre_liaison(results_file, quantite_id, liaisons):
    """Resolves a candidate binding against the variables ACTUALLY
    present in the open .aps file (never a hard-coded unverified name
    at runtime)."""
    liaison = liaisons.get(quantite_id)
    if liaison is None:
        raise KeyError(
            "Aucune liaison APS fournie pour la grandeur '{0}'.".format(
                quantite_id))
    variables = results_file.get_variables()
    for variable in variables or []:
        if (str(variable.get('aps_varname') or '') == liaison['aps_varname'] and
                str(variable.get('model_level') or '') == liaison['model_level']):
            return liaison
    raise RuntimeError(
        "Variable APS '{0}' (niveau '{1}') introuvable dans ce fichier .aps "
        "-- la liaison candidate pour '{2}' ne correspond pas a ce resultat "
        "de simulation. Ne pas deviner une autre variable en remplacement."
        .format(liaison['aps_varname'], liaison['model_level'], quantite_id))


def _lire_serie_horaire(results_file, room_id, liaison, resultats_par_jour):
    """Reads a complete annual series via `get_room_results()` (§6.1.14) and
    resamples it to HOURLY (average of sub-steps), regardless of the actual
    simulation time step."""
    brute = results_file.get_room_results(
        room_id, liaison['aps_varname'], liaison['display_name'],
        liaison['model_level'])  # start_day/end_day omitted = full year.
    if hasattr(brute, 'tolist'):
        brute = brute.tolist()
    valeurs = [float(v) for v in brute]
    pas_par_jour = float(resultats_par_jour)
    pas_par_heure = pas_par_jour / 24.0
    if pas_par_heure <= 0:
        raise RuntimeError('results_per_day invalide ({0}).'.format(
            resultats_par_jour))
    pas_entiers = int(round(pas_par_heure))
    if abs(pas_par_heure - pas_entiers) > 1e-9 or pas_entiers <= 0:
        raise RuntimeError(
            'Pas de simulation non multiple entier de l heure '
            '(results_per_day={0}) -- agregation horaire non fiable.'
            .format(resultats_par_jour))
    if len(valeurs) % pas_entiers != 0:
        raise RuntimeError(
            'Serie de {0} valeurs non divisible par {1} pas/heure -- '
            'annee incomplete ?'.format(len(valeurs), pas_entiers))
    horaire = []
    for debut in range(0, len(valeurs), pas_entiers):
        fenetre = valeurs[debut:debut + pas_entiers]
        horaire.append(sum(fenetre) / pas_entiers)
    if len(horaire) != 365 * 24:
        raise RuntimeError(
            'Serie horaire de {0} valeurs != 8760 (annee {1} non complete '
            'ou non standard).'.format(len(horaire), ANNEE_SIMULATION))
    return horaire


def _agreger_mensuel_sommes(serie_horaire, annee=ANNEE_SIMULATION):
    """Returns a dict {'month_01': sum, ..., 'month_12': sum} plus the
    annual total, from a complete hourly series (8760 values)."""
    if calendar.isleap(annee) or len(serie_horaire) != 365 * 24:
        raise ValueError('Agregation mensuelle : annee non standard ou '
                          'serie incomplete.')
    mensuel = {}
    curseur = 0
    for indice_mois in range(1, 13):
        nb_heures = calendar.monthrange(annee, indice_mois)[1] * 24
        fenetre = serie_horaire[curseur:curseur + nb_heures]
        mensuel[MOIS[indice_mois - 1]] = sum(fenetre)
        curseur += nb_heures
    return mensuel, sum(serie_horaire)


def _agreger_mensuel_moyennes(serie_horaire, annee=ANNEE_SIMULATION):
    """Like `_agreger_mensuel_sommes` but averages (for temperature).

    Returns `(mensuel, moyenne_des_mensuelles, moyenne_horaire)`.

    ⚠ THE TWO ANNUAL AVERAGES ARE DIFFERENT, AND THE SIA WORKBOOK USES THEM
    IN TWO DIFFERENT PLACES. Do not confuse them:

      * `moyenne_des_mensuelles` -> **Table 30**, row `Annual`. Formula
        observed directly in the workbook: `B70 = AVERAGE(B58:B69)`, i.e.
        the UN-WEIGHTED average of the 12 monthly means (also verified in
        C70, AI70, AQ70). Since months do not have the same number of hours,
        this is NOT the hourly mean.
      * `moyenne_horaire` -> **Table 32**, row `Average`, which comes from
        the hourly aggregate of `Daten_Testprogramm`
        (`B107 = ...Daten_Testprogramm!C104`).

    The measured difference between the two is about 0.04 K on the reference
    programmes. Using the hourly mean against Table 30 therefore introduces a
    systematic silent bias -- that is the defect this comment exists to
    prevent from being reintroduced.
    """
    if calendar.isleap(annee) or len(serie_horaire) != 365 * 24:
        raise ValueError('Agregation mensuelle : annee non standard ou '
                          'serie incomplete.')
    mensuel = {}
    curseur = 0
    for indice_mois in range(1, 13):
        nb_heures = calendar.monthrange(annee, indice_mois)[1] * 24
        fenetre = serie_horaire[curseur:curseur + nb_heures]
        mensuel[MOIS[indice_mois - 1]] = sum(fenetre) / len(fenetre)
        curseur += nb_heures
    moyenne_des_mensuelles = sum(mensuel.values()) / 12.0
    moyenne_horaire = sum(serie_horaire) / len(serie_horaire)
    return mensuel, moyenne_des_mensuelles, moyenne_horaire


def extraire_candidat_cas(results_file, room_id, cas_id, resultats_par_jour,
                           liaisons=LIAISONS_APS_CANDIDATES):
    """Extracts, for ONE already-simulated case (open .aps file), the
    candidate Test 1 quantities in the MIRROR form of `test-1.ref.json`
    (terminal leaves = raw scalars). Fills ONLY the quantities relevant
    to this case (cf. quantity/case mapping verified against `test-1.ref.json`
    at the top of the section); other quantities are omitted (not `None` --
    `test1_engine.py::evaluer_test1` handles absence via `candidat_grandeur.
    get(cas)` -> `None` -> each period evaluated with candidate `None`).
    """
    resultat = {}

    if cas_id in CAS_AVEC_CONDITIONNEMENT:
        liaison_chauffage = _resoudre_liaison(
            results_file, 'sensible_heating_power', liaisons)
        liaison_refroidissement = _resoudre_liaison(
            results_file, 'sensible_cooling_power', liaisons)
        serie_chauffage_kw = _lire_serie_horaire(
            results_file, room_id, liaison_chauffage, resultats_par_jour)
        serie_refroidissement_kw = _lire_serie_horaire(
            results_file, room_id, liaison_refroidissement, resultats_par_jour)
        # Mean kW over the hour -> kWh (hourly step => energy = power).
        mensuel_chauffage, annuel_chauffage = _agreger_mensuel_sommes(
            serie_chauffage_kw)
        mensuel_refroidissement, annuel_refroidissement = _agreger_mensuel_sommes(
            serie_refroidissement_kw)
        resultat['sensible_heating_demand_kwh'] = {
            'monthly': mensuel_chauffage, 'annual': annuel_chauffage,
        }
        resultat['sensible_cooling_demand_kwh'] = {
            'monthly': mensuel_refroidissement, 'annual': annuel_refroidissement,
        }

    if cas_id not in ('1E',):  # Table 30: no column for 1E (AUDIT.md pt 3).
        liaison_temperature = _resoudre_liaison(
            results_file, 'operative_temperature', liaisons)
        serie_temperature = _lire_serie_horaire(
            results_file, room_id, liaison_temperature, resultats_par_jour)
        (mensuel_temp, annuel_des_mensuelles,
         annuel_horaire) = _agreger_mensuel_moyennes(serie_temperature)
        mensuel_temp_avec_annuel = dict(mensuel_temp)
        # Table 30 row `Annual` = AVERAGE of the 12 monthly means (B70 in the
        # workbook), NOT the hourly mean: systematic difference of about 0.04 K.
        mensuel_temp_avec_annuel['annual'] = annuel_des_mensuelles
        resultat['operative_temperature_monthly_celsius'] = {
            'monthly': mensuel_temp_avec_annuel,
        }

        if cas_id in CAS_FLOTTEMENT_LIBRE:
            resultat['operative_temperature_annual_extremes_celsius'] = {
                'extremes': {
                    'max': max(serie_temperature),
                    'min': min(serie_temperature),
                    # Table 32 row `Average`: here it is indeed the HOURLY
                    # mean, in accordance with Daten_Testprogramm!C104.
                    'average': annuel_horaire,
                },
            }

    return resultat


def extraire_candidat_test1(chemins_aps_par_cas, resolveur_room_id=None,
                             liaisons=None, accepter_liaisons_non_confirmees=False):
    """Main entry point for extraction -- builds the complete JSON expected
    by `engine/test1_engine.py::evaluer_test1(reference, candidat)`.

    `chemins_aps_par_cas`: dict {cas_id: chemin_fichier_aps}. Only the
    cases present are extracted (others remain absent from the candidate --
    the engine handles this absence without raising, cf. docstring of
    `evaluer_test1`).
    `resolveur_room_id`: function(results_file) -> room_id. By default,
    requires exactly ONE room in the .aps file (Test 1 = single zone,
    traceability/test-1.spec.md §4) and raises a precise error otherwise.
    `liaisons`: dict of confirmed APS bindings. If `None`, uses
    `LIAISONS_APS_CANDIDATES` -- BUT only if
    `accepter_liaisons_non_confirmees=True` is explicitly passed, otherwise
    raises (cf. documented reservation above: these bindings are not
    confirmed by a real VE IN THIS ENVIRONMENT).
    """
    if liaisons is None:
        if not accepter_liaisons_non_confirmees:
            raise RuntimeError(
                "Aucune liaison APS confirmee fournie. LIAISONS_APS_"
                "CANDIDATES n'a pas ete revalide dans cet environnement "
                "(pas de VE disponible) -- passer explicitement "
                "accepter_liaisons_non_confirmees=True pour les utiliser "
                "en connaissance de cause, ou fournir vos propres liaisons "
                "confirmees via le parametre `liaisons`.")
        liaisons = LIAISONS_APS_CANDIDATES

    def _room_id_unique(results_file):
        pieces = list(results_file.get_room_list())
        if len(pieces) != 1:
            raise RuntimeError(
                "Attendu exactement 1 piece dans le fichier .aps du Test 1 "
                "(zone unique) ; trouve {0}.".format(len(pieces)))
        # get_room_list() -> [(name, id, area, volume), ...] (§6.1.14).
        return pieces[0][1]

    resolveur_room_id = resolveur_room_id or _room_id_unique

    iesve = _iesve()
    candidat = {}
    provenance_par_cas = {}
    for cas_id, chemin_aps in chemins_aps_par_cas.items():
        if cas_id not in CAS_TEST1:
            raise ValueError('Cas Test 1 inconnu : {0!r}'.format(cas_id))
        results_file = iesve.ResultsReader.open(chemin_aps)
        try:
            room_id = resolveur_room_id(results_file)
            resultats_par_jour = getattr(results_file, 'results_per_day', 24)
            valeurs_cas = extraire_candidat_cas(
                results_file, room_id, cas_id, resultats_par_jour, liaisons)
        finally:
            results_file.close()
        for grandeur, noeud in valeurs_cas.items():
            candidat.setdefault(grandeur, {})[cas_id] = noeud
        provenance_par_cas[cas_id] = chemin_aps

    candidat['_provenance'] = {
        'source': 've_adapter.test1_adapter.extraire_candidat_test1',
        'liaisons_confirmees': liaisons is not LIAISONS_APS_CANDIDATES,
        'fichiers_aps': provenance_par_cas,
        'annee_simulation': ANNEE_SIMULATION,
    }
    return candidat


# --------------------------------------------------------------------------
# Fixture mode -- operation WITHOUT a VE licence (PROJECT_PLAN.md §5,
# "VE adapter extracts required quantities, or documented stub if VE
# unavailable"). PLAUSIBLE JSON, NOT from a real simulation -- so that
# `ui-engineer` can wire the navigator without VE.
# --------------------------------------------------------------------------

_ICI = os.path.dirname(os.path.abspath(__file__))
CHEMIN_FIXTURE_DEFAUT = os.path.join(_ICI, 'fixtures', 'test1_candidat.exemple.json')


def charger_fixture_test1(chemin=None):
    """Loads the Test 1 example JSON fixture (VE-less mode).

    This JSON has NEVER been produced by a real IESVE simulation -- it
    serves only to develop `ui-engineer`/`validation-engine-engineer`
    without a VE licence. The `_provenance.source` field in the file
    states this explicitly to avoid any downstream confusion.
    """
    chemin = chemin or CHEMIN_FIXTURE_DEFAUT
    with open(chemin, encoding='utf-8') as flux:
        return json.load(flux)
