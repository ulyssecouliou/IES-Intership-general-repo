# -*- coding: utf-8 -*-
"""VE adapter -- SIA 4010 Test no. 7 (validation class 5).

This module is the only place in the repository (together with `test1_adapter.py`)
that imports `iesve`. It translates between the VE API (VEScripts) and the
normalised JSON expected by `engine/test7_engine.py::evaluer_test7()`: a dict
`{german_label: annual_value_kWh}`. The engine must never know that VE
exists (CLAUDE.md, "pure/hard separation"); this adapter must never
invent a value, tolerance or unverified API symbol
(CLAUDE.md, rule no. 1).

--------------------------------------------------------------------------
WHAT TEST 7 REQUIRES, AND WHAT IT DOES NOT (Spezifikation_Test7.pdf,
Schema.pdf, read in full -- traceability/classes-de-validation.spec.md
§2.1 independently reaches the same conclusion):
--------------------------------------------------------------------------
  - NO thermal building model, NO geometry, NO glazing.
    Load profiles (cooling, heating, DHW) are PROVIDED by SIA in
    `Lastverläufe_220607.xlsx` (sheet `Gruppen`, 8760 h). This file lives
    outside this repository (external path `SIA_4010_geteilter_Link/Test7/`);
    its structure is documented but its contents are NOT vendored or parsed
    here -- see the "WHAT IS NOT DONE" section below, point 1.
  - Climate: SIA 2028 DRY normal, Zürich Kloten, period 1.1.2022-31.12.2022
    (Spezifikation_Test7.pdf p.1) -- **different year from Test 1** (2011).
    The ONLY climate variable involved is the hourly outdoor air temperature
    (it sets the operating point of the dry cooler / outdoor-air heat exchanger,
    Spezifikation_Test7.pdf p.4: "Temperaturdifferenz Aussenluft -
    Vorlauftemperatur 4 K bei Volllast"). This series is an official source
    already frozen:
    `refs/reference-data/sia-2028-kloten-temperature.csv` (8760 h, column
    `theta_e_air_c` -- traceability/classes-de-validation.spec.md §3.0).
  - Plant: reversible water-water heat pump Climaveneta NX-W-Y/H 0182,
    2 storage tanks of 2000 l, lump-sum distribution (5% losses,
    2% auxiliaries), dry cooler 70 kW / outdoor-air heat exchanger
    76 kW, water-glycol circuit 30% at 19'000 kg/h -- all these values are
    captured below AS CONSTANTS, sourced, for documentation and for
    a future manual network build (see just below: their automatic build
    is NOT possible with the documented API).
  - PV: roof 150 modules (18x7 + 6x4) at 310 W = 45 kWp declared,
    tilt 10°, east/west orientation; south facade 52 modules (13x4) at
    310 W = 15.6 kWp declared; inverter 97%. The quantity "PV-Ertrag"
    REQUIRES irradiance on the plane of THESE exact modules -- absent from
    any official source in our possession (idem
    traceability/classes-de-validation.spec.md §3.1). This module ALWAYS returns
    `None` for this quantity -- never an estimate. See the PV section
    below: this refusal is **deliberate**, not an API knowledge gap.

--------------------------------------------------------------------------
WHAT IS VERIFIED (each `iesve` symbol cited below was read in
`refs/VEScripts-API-VE2023.pdf`, section indicated -- text extraction
`pdftotext -layout`, read in full):
--------------------------------------------------------------------------
  - `iesve.ResultsReader.open(filename)`                                §6.1.14.2
  - `ResultsReader.get_variables()` -> list of dicts `{aps_varname,
    display_name, model_level, units_type}`                            §6.1.14.2
  - `ResultsReader.get_units()` -> dict indexed by `units_type`, each
    entry carrying `units_metric.display_name` (usage example given
    literally in the PDF)                                               §6.1.14.2
  - `ResultsReader.get_hvac_component_results(component_id, component_type,
    var_name, start_day=-1, end_day=-1)` -- model level `h` = "HVAC
    component level" (level table, §6.1.14.1)                          §6.1.14.2
  - `ResultsReader.results_per_day` (attribute)                         §6.1.14.3
  - `iesve.VELocate()`; `.open_wea_data()` / `.set(dict)` (key
    `weather_file`) / `.save_and_close()` -- same mechanism, already verified
    and used by `test1_adapter.py::assigner_meteo_drycold`              §6.1.36
  - Existence of the class `HVACComponentTypes` (enumeration) and its
    members `awhp`, `aahp`, `wahp`, `hot_water_loop`, `chilled_water_loop`,
    `thermal_storage_tank`, `pump`, `heat_transfer_loop`, `junction`,
    `room`, `boiler`, `chiller`, `cooling_tower`, `fan`, `damper` -- read
    in the "Enums Defined Here" block that opens §6.1.7 "HVAC Network".
    ⚠ This block is a two-column table merged by text extraction (same
    symptom as `material_categories` in `test1_adapter.py`: several
    unrelated enumerations appear interleaved). None of these member names
    is therefore hardcoded as the identifier of "the" right component:
    see below why this module does NOT need to resolve that ambiguity itself.
  - `HVACNetwork` (class), static method `load_network(name) ->
    HVACNetwork`, attribute `components` (list of `HVACComponent`)      §6.1.7.5
  - `HVACAbstractComponent.aps_component_type` (attribute, type
    `HVACComponentTypes`) -- **a component ALREADY obtained** (via
    `HVACNetwork.components` or `get_component_by_id`) therefore carries its
    own already-resolved `component_type` value; it is never
    necessary to guess the spelling of an enum member to obtain it.
    §6.1.7 (block `HVACAbstractComponent`, just after the enums above)
  - Table "component types currently available" of
    `get_hvac_component_results` (numbered list 1-54 associating an integer
    to an `iesve.HVAC...` class)                                        §6.1.14.2
    ⚠ This table is ALSO a visible two-column merge (e.g. entries 30 and 31
    both carry "iesve.HVACHeatPump", which is suspect): it is NOT used
    here to guess a numeric code. See the next section.

--------------------------------------------------------------------------
WHAT IS NOT DONE HERE, AND WHY -- marked `# ⚠ À VÉRIFIER API` in
the code, never filled in by assumption:
--------------------------------------------------------------------------
  1. **Building the ApacheHVAC network (heat pump, 2 tanks, dry cooler,
     outdoor-air heat exchanger, pumps, load control) -- NOT PROVIDED
     HERE, and intentionally.** `refs/VEScripts-API-VE2023.pdf` documents,
     for `HVACNetwork`/`HVACComponent`/`HVACPrototypeSystem`, only
     READ methods (`load_network`, `get_component_by_id`,
     `components`, `get_node_data`, `get_peak_data`, ...) -- explicit
     search for `add_component|create_component|insert_component|
     new_network|create_network|macro` in the full text extraction:
     **zero occurrences**. No component or macro-flow network CREATION
     method is documented. Building a call to `iesve.HVACSomething().create(...)`
     anyway would be inventing a symbol -- forbidden by rule no. 1.
     **Direct and important consequence**: the Test 7 system (Schema.pdf)
     must be built ONCE, by hand, in the ApacheHVAC editor of a real VE,
     before this module can read anything. This point is deferred to `ve-adapter-engineer`
     (next session with real VE) -- it is NOT resolved here, exactly
     as `test1_adapter.py` had deferred geometry/room creation.
  2. **Reading the SIA load profiles (`Lastverläufe_220607.xlsx`) --
     NOT PARSED HERE.** Its structure is documented (sheet `Gruppen`:
     8760 h x 11 power columns in W; sheet `Grundlagen`: detail
     per test/room -- traceability/classes-de-validation.spec.md §2.2).
     As long as the ApacheHVAC network cannot be built by this
     module (point 1), writing a parser to feed `VEProfile` objects
     that would in any case be connected to nothing would be dead code and
     unverifiable. Deferred to the same extension point as point 1.
  3. **Resolving the exact member of `HVACComponentTypes` for "reversible
     water-water heat pump".** The members visible in the documented table
     are `awhp` (air-water), `aahp` (air-air), `wahp`
     (water-air/exhaust-air?) -- NONE explicitly named for a WATER-WATER
     heat pump. `ve_adapter/ve_api_surface.json` (introspection probe of a
     real VE 2025 installation, 2026-07-31 -- **NOT a `/refs`
     document**, used here only as corroboration, never as the sole
     justification of a symbol) confirms the EXISTENCE of a class
     `iesve.HVACWaterWaterHeatPump`, but this name appears in NO
     documented enumeration of `HVACComponentTypes`. **This module works
     around the problem rather than guessing**: it requires the caller to
     supply an ALREADY-RESOLVED `component_type` (typically read directly
     from `HVACComponent.aps_component_type` of a component obtained from
     a real VE -- §6.1.7 above), never a member name to be
     interpreted here.
  4. **Exact APS variable names** (`aps_varname`) for each
     Test 7 quantity. As for Test 1 (`test1_adapter.py`, point 4
     of its own docstring), the PDF consistently refers to a separate
     "units spreadsheet"/"variables list", absent from `/refs`. **No
     external repository consulted carries proven bindings for Test 7**
     (unlike Test 1, where an external configuration file
     existed): this module therefore provides NO candidate bindings, not
     even an "unconfirmed" one -- the caller must discover them
     (aid provided: `decouvrir_variables_hvac()`, read-only, never
     invoked automatically) and supply them explicitly via the
     `plan_extraction` parameter.
  5. **`PV-Ertrag` -- deliberate refusal, not an API gap.** `EnergyUse.
     prm_elec_gen_pv` (§6.1.14.4) IS a documented and usable symbol
     with `get_energy_results()`/`get_energy_results_ex()`; the class
     `VERenewables` appears in the class diagram of the guide (no
     text section, no documented method -- search `VERenewables`
     in the full extraction: zero occurrences outside the diagram). Even if
     one or the other produced a number, that number would be derived from
     the irradiance of the weather file assigned to the simulation -- NOT from
     a verified official source for the exact module planes declared
     (roof 10° east/west, vertical south facade). Using it would amount to
     laundering an unverifiable datum into a validated result. **This module
     therefore contains NO code path touching PV/VERenewables/
     `prm_elec_gen_pv`**: `PV-Ertrag` is absent from all output produced
     here, by design, never `None` disguised as zero or as an average.

Written in a conservative style (no f-strings, no dataclasses) for consistency
with `test1_adapter.py`, although the runtime probe (`probe_runtime_resultat.txt`,
real VE 2025) established Python 3.12 -- no compatibility constraint is therefore
*required*, this choice remains simply costless.
"""

import calendar
import csv
import io
import json
import os

# --------------------------------------------------------------------------
# Normative constants -- all sourced from `Spezifikation_Test7.pdf`
# (4 pages, read in full) and `Schema.pdf`. None is used to
# build anything in VE (cf. docstring, "WHAT IS NOT DONE" section, point 1):
# they document the system that someone will have to build by hand,
# and serve as self-consistency guards below.
# --------------------------------------------------------------------------

# Spezifikation_Test7.pdf p.1: "Simulationsperiode 1.1.2022 bis 31.12.2022".
# Different from Test 1 (2011) -- do NOT reuse ANNEE_SIMULATION from
# test1_adapter.py by mistake.
ANNEE_SIMULATION = 2022
assert not calendar.isleap(ANNEE_SIMULATION)  # guard: 8760 h assumed.
HEURES_PAR_AN = 365 * 24

CLIMAT = {
    "jeu": "SIA 2028 DRY normal",
    "station": "Zürich Kloten",
    "periode": "1.1.2022-31.12.2022",
}

# Spezifikation_Test7.pdf p.2: "Climaveneta NX-W-Y /H 0182, Wasser-Wasser-
# Wärmepumpe, reversibel, Scrollverdichter, 2-stufig".
CLIMAVENETA_NX_W_Y_H_0182 = {
    "type": "PAC eau-eau, réversible, compresseurs scroll, 2 étages "
    "(Wasser-Wasser-Wärmepumpe, reversibel, Scrollverdichter, "
    "2-stufig)",
    "puissance_nominale_froid_kw": 55.9,
    "puissance_nominale_chaud_kw": 60.0,
    # EN 14825 characteristic fields (table 5 / table 12,
    # Spezifikation_Test7.pdf p.2-4): part-load test conditions.
    # Not reproduced in detail here -- this module does not build
    # the heat pump in VE (docstring, point 1); only the nominal
    # capacities serve as documentary consistency guards.
}

# Spezifikation_Test7.pdf p.1, blocks "Kälteverteilung" / "Wärmeverteilung".
DISTRIBUTION_FROID = {
    "pertes_pct_de_la_chaleur_absorbee": 5.0,  # "5% der aufgenommenen Wärme"
    "auxiliaire_pct_de_la_chaleur_absorbee": 2.0,  # "2% der aufgenommenen Wärme"
    "auxiliaire_recupere_comme_charge_thermique_pct": 50.0,
}
DISTRIBUTION_CHAUD = {
    "pertes_pct_de_la_chaleur_delivree": 5.0,  # "5% der abgegebenen Wärme"
    "auxiliaire_pct_de_la_chaleur_delivree": 2.0,  # "2% der abgegebenen Wärme"
    "auxiliaire_recupere_dans_circuit_chauffage_pct": 50.0,
}

# Spezifikation_Test7.pdf p.1, "Kältespeicherung"/"Wärmespeicherung":
# "Technischer Speicher zur Vermeidung kurzer Laufzeiten, Volumen 2'000 l".
STOCKAGE_FROID_LITRES = 2000
STOCKAGE_CHAUD_LITRES = 2000

# Spezifikation_Test7.pdf p.4, block "Aussenluftgerät".
AEROREFROIDISSEUR_SEC_KW = 70.0  # "Luftgekühlter Trockenrückkühler"
ECHANGEUR_AIR_EXTERIEUR_KW = 76.0  # "Aussenluft-Wärmeübertrager"
VENTILATEUR_PUISSANCE_SPECIFIQUE_KW_PAR_KW = 0.045  # "Antriebsleistung Ventilator"

# Spezifikation_Test7.pdf p.4, block "Rückkühl-/Aussenluftkreis". The "?" in
# the glycol fraction is reproduced VERBATIM from the source -- it is SIA
# itself that leaves this point uncertain in its specification, not an
# omission by this module.
CIRCUIT_GLYCOL = {
    "fluide": "Wasser-Glykol-Gemisch 30%?",  # "?" present in the SIA source
    "massflow_kg_par_h": 19000.0,
    "spread_k": 4.0,  # "Temperaturspreizung"
    "delta_t_air_fluide_pleine_charge_k": 4.0,  # "bei Volllast"
    "pompe_puissance_utile_dans_circuit_pct": 50.0,  # "Pumpenabwärme ... wärmewirksam"
    "pertes_pct": 5.0,
}

# Spezifikation_Test7.pdf p.4, block "Bivalenz": backup boiler below the
# bivalence temperature.
BIVALENCE = {
    "vecteur_energetique": "gaz",
    "rendement": 0.9,
}

# Spezifikation_Test7.pdf p.4, block "Eigenerzeugung" / "Photovoltaik".
# ⚠ UNRESOLVED DISCREPANCY (see `verifier_coherence_puissance_pv()` below):
# 150 x 310 W = 46.5 kWp and 52 x 310 W = 16.12 kWp, whereas the
# source declares 45 kWp and 15.6 kWp -- 150 x 300 W = 45 kWp and
# 52 x 300 W = 15.6 kWp match EXACTLY. The per-module power read ("310 W")
# is therefore probably a confusion between the model name
# ("AEG AS-M605-310") and the actual power ("300 W"?). Not resolved without
# a visual re-reading of page 4 of the source PDF. NO FUNCTIONAL IMPACT HERE:
# `PV-Ertrag` is in any case never calculated by this module (cf. docstring,
# point 5).
PV_SYSTEME = {
    "toit_modules": 150,  # 18 x 7 + 6 x 4
    "toit_w_par_module_lu": 310.0,  # as extracted -- discrepancy above
    "toit_kwp_declare": 45.0,
    "toit_inclinaison_deg": 10.0,
    "toit_orientation": "est/ouest",
    "facade_modules": 52,  # 13 x 4, south facade
    "facade_w_par_module_lu": 310.0,  # as extracted -- discrepancy above
    "facade_kwp_declare": 15.6,
    "facade_orientation": "sud",
    "onduleur_rendement": 0.97,
    "modele_module": "AEG AS-M605-310",
}


def verifier_coherence_puissance_pv():
    """Documents (without raising) the arithmetic discrepancy found in the source.

    Does not affect ANY calculation: `PV-Ertrag` is never produced by this module,
    regardless of the outcome of this check. Serves only to keep the
    discrepancy visible and tested rather than silent.
    """
    toit_a_310 = PV_SYSTEME["toit_modules"] * PV_SYSTEME["toit_w_par_module_lu"] / 1000.0
    toit_a_300 = PV_SYSTEME["toit_modules"] * 300.0 / 1000.0
    facade_a_310 = (
        PV_SYSTEME["facade_modules"] * PV_SYSTEME["facade_w_par_module_lu"] / 1000.0
    )
    facade_a_300 = PV_SYSTEME["facade_modules"] * 300.0 / 1000.0
    return {
        "toit_kwp_declare": PV_SYSTEME["toit_kwp_declare"],
        "toit_kwp_calcule_a_310w": toit_a_310,
        "toit_coherent_a_310w": abs(toit_a_310 - PV_SYSTEME["toit_kwp_declare"]) < 1e-6,
        "toit_kwp_calcule_a_300w": toit_a_300,
        "toit_coherent_a_300w": abs(toit_a_300 - PV_SYSTEME["toit_kwp_declare"]) < 1e-6,
        "facade_kwp_declare": PV_SYSTEME["facade_kwp_declare"],
        "facade_kwp_calcule_a_310w": facade_a_310,
        "facade_coherent_a_310w": abs(facade_a_310 - PV_SYSTEME["facade_kwp_declare"])
        < 1e-6,
        "facade_kwp_calcule_a_300w": facade_a_300,
        "facade_coherent_a_300w": abs(facade_a_300 - PV_SYSTEME["facade_kwp_declare"])
        < 1e-6,
    }


# --------------------------------------------------------------------------
# The 11 Test 7 quantities -- labels VERBATIM (German), identical to
# `refs/reference-data/test-7.ref.json`. A dedicated test verifies this
# match word for word: it is the matching key for
# `engine/test7_engine.py::evaluer_test7`; a typo here would silently make
# a quantity NOT_CHECKABLE.
# --------------------------------------------------------------------------

LIBELLE_PV_ERTRAG = "PV-Ertrag"

GRANDEURS_TEST7 = (
    {
        "libelle_de": "Zugeführte elektrische Energie Kältemaschine",
        "unite": "kWh",
        "role_systeme": "Énergie électrique reçue par la production de "
        "froid (PAC en mode froid).",
    },
    {
        "libelle_de": "Total abgeführte Wärme",
        "unite": "kWh",
        "role_systeme": "Chaleur totale évacuée côté froid (à répartir "
        "entre récupération chaude et rejet au "
        "refroidisseur sec -- cf. les deux grandeurs "
        "suivantes).",
    },
    {
        "libelle_de": "Hilfsenergie Kälteerzeugung",
        "unite": "kWh",
        "role_systeme": "Énergie auxiliaire de la production de froid "
        "(2 % de la chaleur absorbée, DISTRIBUTION_FROID).",
    },
    {
        "libelle_de": "Aus Kälteerzeugung an die Wärmeseite gelieferte W.",
        "unite": "kWh",
        "role_systeme": "Chaleur récupérée côté condenseur et livrée au "
        "circuit chaud (charge du ballon chaud) en cas de "
        "besoin simultané -- Schema.pdf, bloc "
        "« Wärmerückgewinnung ». Plancher à zéro dans le "
        "classeur de référence : ne peut pas être négative.",
    },
    {
        "libelle_de": "Über Rückkühler abgeführte Wärme",
        "unite": "kWh",
        "role_systeme": "Chaleur rejetée via le refroidisseur sec "
        "(AEROREFROIDISSEUR_SEC_KW) -- le reliquat non "
        "récupéré côté chaud.",
    },
    {
        "libelle_de": "Zugeführte elektrische Energie Wärmepumpe",
        "unite": "kWh",
        "role_systeme": "Énergie électrique reçue par la production de "
        "chaleur (PAC en mode chaud).",
    },
    {
        "libelle_de": "Zugeführte Wärme der Wärmeerzeugung, Heizen",
        "unite": "kWh",
        "role_systeme": "Chaleur livrée par la production de chaleur pour "
        "le chauffage des locaux.",
    },
    {
        "libelle_de": "Zugeführte Wärme der Wärmeerzeugung, Warmwasser",
        "unite": "kWh",
        "role_systeme": "Chaleur livrée par la production de chaleur pour "
        "l'eau chaude sanitaire (charge du ballon ECS à "
        "60 °C, Spezifikation_Test7.pdf p.1).",
    },
    {
        "libelle_de": "Energie Heizkessel",
        "unite": "kWh",
        "role_systeme": "Énergie de la chaudière d'appoint (gaz, "
        "rendement 0.9, BIVALENCE), active sous la "
        "température de bivalence. Plancher à zéro dans "
        "le classeur de référence.",
    },
    {
        "libelle_de": "Hilfsenergie Wärmeerzeugung",
        "unite": "kWh",
        "role_systeme": "Énergie auxiliaire de la production de chaleur "
        "(2 % de la chaleur délivrée, DISTRIBUTION_CHAUD).",
    },
    {
        "libelle_de": LIBELLE_PV_ERTRAG,
        "unite": "kWh",
        "role_systeme": "Production électrique photovoltaïque -- JAMAIS "
        "calculée ici. Cf. docstring de module, point 5.",
    },
)

_LIBELLES_CONNUS = frozenset(g["libelle_de"] for g in GRANDEURS_TEST7)
_LIBELLES_VERIFIABLES_SANS_IRRADIANCE = frozenset(
    g["libelle_de"] for g in GRANDEURS_TEST7 if g["libelle_de"] != LIBELLE_PV_ERTRAG
)


# --------------------------------------------------------------------------
# Kloten outdoor air temperature -- official source already frozen
# (refs/reference-data/sia-2028-kloten-temperature.csv). Pure
# Python read (standard `csv` module), no dependency on `iesve`: this is
# NOT a simulation result, it is INPUT DATA whose only
# purpose here is (a) the future weather assignment (`assigner_meteo_kloten`)
# and (b) a cross-check against what VE will actually have simulated
# (`verifier_temperature_exterieure_simulee`), to catch a wrong
# weather file assigned before trusting anything else.
# --------------------------------------------------------------------------

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
CHEMIN_TEMPERATURE_KLOTEN_DEFAUT = os.path.join(
    _RACINE, "refs", "reference-data", "sia-2028-kloten-temperature.csv"
)


def charger_temperature_exterieure_kloten(chemin=None):
    """Load the hourly outdoor air temperature for Kloten (8760 h).

    Source: `refs/reference-data/sia-2028-kloten-temperature.csv`, column
    `theta_e_air_c` -- traceability/classes-de-validation.spec.md §3.0
    (extracted from `Test4/Resultaterfassung Test4.xlsx`, sheet
    `Wetterdaten`, output of the EnergyPlus reference program).

    Validates that the hours are contiguous and sorted 1..8760: a silently
    reordered or truncated source would corrupt every cross-check.
    """
    chemin = chemin or CHEMIN_TEMPERATURE_KLOTEN_DEFAUT
    heures, valeurs = [], []
    with io.open(chemin, encoding="utf-8", newline="") as flux:
        for ligne in csv.DictReader(flux):
            heures.append(int(ligne["heure"]))
            valeurs.append(float(ligne["theta_e_air_c"]))
    if len(valeurs) != HEURES_PAR_AN:
        raise ValueError(
            "Température Kloten : {0} valeurs lues, {1} attendues "
            "(8760 h). Fichier tronqué ou mal formé : {2}".format(
                len(valeurs), HEURES_PAR_AN, chemin
            )
        )
    if heures != list(range(1, HEURES_PAR_AN + 1)):
        raise ValueError(
            "Température Kloten : colonne `heure` non contiguë/non triée "
            "1..8760 dans {0} -- refus d'utiliser une série dont l'ordre "
            "temporel n'est pas garanti.".format(chemin)
        )
    return valeurs


def verifier_temperature_exterieure_simulee(
    serie_simulee, serie_reference=None, tolerance_c=0.01
):
    """Compare a series extracted from a real VE to the Kloten reference.

    Does NOT guess ANY APS weather variable name: the caller must have already
    extracted `serie_simulee` (8760 values, °C) by their own means
    (`ResultsReader.get_weather_results`, §6.1.14.2, level `w` -- variable name
    not confirmed here, cf. module docstring point 4). This
    check is then pure computation, testable without VE.

    Returns a dict {'coherent', 'ecart_max_c', 'heure_ecart_max',
    'nb_heures'}. A misconfigured VE (wrong weather file, time offset)
    shows up here BEFORE trusting a system result.
    """
    serie_reference = (
        serie_reference
        if serie_reference is not None
        else charger_temperature_exterieure_kloten()
    )
    if len(serie_simulee) != len(serie_reference):
        raise ValueError(
            "Comparaison météo : {0} valeurs simulées contre {1} de "
            "référence -- séries de longueur différente, non "
            "comparables.".format(len(serie_simulee), len(serie_reference))
        )
    ecarts = [abs(float(a) - float(b)) for a, b in zip(serie_simulee, serie_reference)]
    ecart_max = max(ecarts) if ecarts else 0.0
    indice_max = ecarts.index(ecart_max) if ecarts else -1
    return {
        "coherent": ecart_max <= tolerance_c,
        "ecart_max_c": ecart_max,
        "heure_ecart_max": indice_max
        + 1,  # 1-based, matching the `heure` column of the CSV
        "nb_heures": len(serie_reference),
    }


# --------------------------------------------------------------------------
# Lazy import of `iesve` -- never at module level (same convention
# as `test1_adapter.py`), so that this file remains readable/inspectable
# by tools that do not have VE.
# --------------------------------------------------------------------------


def _iesve():
    """Imports `iesve` on demand; precise error if VE is unavailable."""
    try:
        import iesve

        return iesve
    except ImportError as erreur:
        raise ImportError(
            "Module 'iesve' indisponible : ce code doit s'exécuter depuis "
            "la fenêtre Scripts d'IESVE (VEScripts), pas en Python "
            "autonome. Erreur d'origine : " + str(erreur)
        )


def assigner_meteo_kloten(chemin_fichier_meteo):
    """Assign the SIA 2028 DRY normal weather file, Kloten, to the current
    project (§6.1.36 -- same mechanism, already verified, as
    `test1_adapter.py::assigner_meteo_drycold`).

    This module does NOT provide the weather file itself (conversion from
    the original SIA format to a VE-readable format -- out of scope,
    cf. traceability/classes-de-validation.spec.md §3.2); it merely points
    to it.
    """
    iesve = _iesve()
    locate = iesve.VELocate()
    if locate.open_wea_data() == -1:
        raise RuntimeError("VELocate.open_wea_data() a échoué.")
    try:
        locate.set({"weather_file": chemin_fichier_meteo})
    finally:
        locate.save_and_close()


# --------------------------------------------------------------------------
# HVAC variable discovery -- NOT for trusted extraction (no
# pass/fail verdict must depend on it). To be used manually by
# `ve-adapter-engineer` on a real VE to build `plan_extraction`
# -- never called by `extraire_candidat_test7()`.
# --------------------------------------------------------------------------

NIVEAU_HVAC_COMPOSANT = "h"  # "HVAC component level", §6.1.14.1
NIVEAUX_APACHE_SYSTEMES = ("v", "j", "r")  # misc / energy / carbon systems


def decouvrir_variables_hvac(
    results_file, jetons_requis=(), niveaux=(NIVEAU_HVAC_COMPOSANT,)
):
    """Search, by tokens (substrings, case-insensitive), the
    variables of the open `.aps` file whose model level belongs to
    `niveaux`. Follows the same principle as
    `test1_adapter.py::decouvrir_candidats_variable`.
    """
    try:
        variables = results_file.get_variables()
    except Exception as erreur:
        raise RuntimeError("ResultsReader.get_variables() a échoué : {0}".format(erreur))
    jetons = [jeton.lower() for jeton in jetons_requis]
    resultats = []
    for variable in variables or []:
        niveau_variable = str(variable.get("model_level") or "")
        if niveau_variable not in niveaux:
            continue
        hay = (
            str(variable.get("aps_varname") or "")
            + " "
            + str(variable.get("display_name") or "")
        ).lower()
        if all(jeton in hay for jeton in jetons):
            resultats.append(variable)
    return resultats


def _valeur_unite_declaree(results_file, aps_varname, niveau):
    """Unit name (metric) declared by the `.aps` file for a given
    variable -- via `get_variables()` (`units_type`) then
    `get_units()` (usage example given literally by the PDF,
    §6.1.14.2, function `get_units`). Does NOT guess any unit: if the
    variable or its `units_type` is not found, raises a precise error
    rather than assuming kW/kWh.
    """
    variables = results_file.get_variables() or []
    for variable in variables:
        if (
            str(variable.get("aps_varname") or "") == aps_varname
            and str(variable.get("model_level") or "") == niveau
        ):
            type_unite = variable.get("units_type")
            unites = results_file.get_units() or {}
            bloc = unites.get(type_unite)
            if not bloc or "units_metric" not in bloc:
                raise RuntimeError(
                    "get_units() ne définit pas l'unité '{0}' pour la "
                    "variable '{1}' (niveau '{2}').".format(
                        type_unite, aps_varname, niveau
                    )
                )
            return bloc["units_metric"].get("display_name")
    raise RuntimeError(
        "Variable APS '{0}' (niveau '{1}') introuvable dans ce fichier "
        ".aps -- impossible de vérifier son unité.".format(aps_varname, niveau)
    )


def _serie_horaire_composant(
    results_file, component_id, component_type, aps_varname, resultats_par_jour
):
    """Read the full annual series of an HVAC component
    (`get_hvac_component_results`, §6.1.14.2) and reduce it to an HOURLY
    step (mean of sub-steps), regardless of the actual simulation timestep.
    Same logic, validated by mutation tests, as
    `test1_adapter.py::_lire_serie_horaire` -- re-implemented here so that
    this file remains self-contained (each `*_adapter.py` in the repository
    is loaded independently by its own tests, `ve_adapter/` not being a
    package).
    """
    brute = results_file.get_hvac_component_results(
        component_id, component_type, aps_varname
    )
    if hasattr(brute, "tolist"):
        brute = brute.tolist()
    valeurs = [float(v) for v in brute]
    pas_par_jour = float(resultats_par_jour)
    pas_par_heure = pas_par_jour / 24.0
    if pas_par_heure <= 0:
        raise RuntimeError("results_per_day invalide ({0}).".format(resultats_par_jour))
    pas_entiers = int(round(pas_par_heure))
    if abs(pas_par_heure - pas_entiers) > 1e-9 or pas_entiers <= 0:
        raise RuntimeError(
            "Pas de simulation non multiple entier de l heure "
            "(results_per_day={0}) -- agrégation horaire non fiable.".format(
                resultats_par_jour
            )
        )
    if len(valeurs) % pas_entiers != 0:
        raise RuntimeError(
            "Série de {0} valeurs non divisible par {1} pas/heure -- "
            "année incomplète ?".format(len(valeurs), pas_entiers)
        )
    horaire = []
    for debut in range(0, len(valeurs), pas_entiers):
        fenetre = valeurs[debut : debut + pas_entiers]
        horaire.append(sum(fenetre) / pas_entiers)
    if len(horaire) != HEURES_PAR_AN:
        raise RuntimeError(
            "Série horaire de {0} valeurs != 8760 (année {1} non complète "
            "ou non standard).".format(len(horaire), ANNEE_SIMULATION)
        )
    return horaire


def _energie_annuelle_kwh(serie_puissance_kw):
    """Annual sum [kWh] of an hourly power series [kW].

    Validates (average kW over the hour) x (1 h) = kWh: direct summation is
    therefore correct ONLY because the series is already hourly (guaranteed
    by `_serie_horaire_composant`). Separate function to remain
    testable/mutable independently of .aps reading (e.g. plausible mutation:
    average instead of sum, which would give a plausible but wrong number).
    """
    if len(serie_puissance_kw) != HEURES_PAR_AN:
        raise ValueError(
            "Série de {0} valeurs != 8760 : agrégation annuelle refusée.".format(
                len(serie_puissance_kw)
            )
        )
    return float(sum(serie_puissance_kw))


# --------------------------------------------------------------------------
# Extraction plan -- THIS MODULE PROVIDES NO CANDIDATE BINDINGS (cf.
# docstring, point 4). The caller must build, against a real VE,
# a dict:
#   plan_extraction = {
#       libelle_de: {
#           'component_id': <str, HVACComponent.id>,
#           'component_type': <HVACComponentTypes value ALREADY resolved,
#                              typically HVACComponent.aps_component_type>,
#           'aps_varname': <str, confirmed via get_variables()>,
#           'unite_attendue': <str, e.g. 'kW' -- compared against
#                              _valeur_unite_declaree() before reading>,
#       },
#       ...
#   }
# --------------------------------------------------------------------------


def extraire_grandeur_test7(
    results_file, libelle_de, entree_plan, resultats_par_jour=None
):
    """Extract the annual energy [kWh] for ONE Test 7 quantity, from an
    already-open `.aps` file.

    Explicitly refuses `PV-Ertrag` (never a code path for this quantity,
    cf. module docstring point 5) and any unknown quantity
    (guard against a typo that would silently break matching with
    `engine/test7_engine.py`).
    """
    if libelle_de == LIBELLE_PV_ERTRAG:
        raise ValueError(
            "'PV-Ertrag' ne peut pas figurer dans un plan d'extraction : "
            "cette grandeur exige l'irradiance sur le plan des modules, "
            "absente de toute source officielle. Ce module la renvoie "
            "toujours absente -- voir docstring, point 5."
        )
    if libelle_de not in _LIBELLES_CONNUS:
        raise KeyError(
            "Grandeur Test 7 inconnue : {0!r}. Grandeurs attendues : "
            "{1}".format(libelle_de, sorted(_LIBELLES_CONNUS))
        )
    for cle in ("component_id", "component_type", "aps_varname", "unite_attendue"):
        if cle not in entree_plan:
            raise KeyError(
                "Plan d'extraction incomplet pour {0!r} : clé '{1}' "
                "manquante.".format(libelle_de, cle)
            )

    resultats_par_jour = resultats_par_jour or getattr(
        results_file, "results_per_day", 24
    )

    unite_declaree = _valeur_unite_declaree(
        results_file, entree_plan["aps_varname"], NIVEAU_HVAC_COMPOSANT
    )
    if unite_declaree != entree_plan["unite_attendue"]:
        raise RuntimeError(
            "Grandeur {0!r} : unité déclarée par le fichier .aps "
            "({1!r}) != unité attendue par le plan d'extraction "
            "({2!r}). Refus de lire une série dont l'unité n'est pas "
            "celle supposée.".format(
                libelle_de, unite_declaree, entree_plan["unite_attendue"]
            )
        )

    serie = _serie_horaire_composant(
        results_file,
        entree_plan["component_id"],
        entree_plan["component_type"],
        entree_plan["aps_varname"],
        resultats_par_jour,
    )
    return _energie_annuelle_kwh(serie)


def extraire_candidat_test7_depuis_fichier(
    results_file, plan_extraction, resultats_par_jour=None
):
    """Build the candidate `{label: annual_value}` expected by
    `engine/test7_engine.py::evaluer_test7()`, from an already-open `.aps` file.
    Fills ONLY the quantities present in `plan_extraction` --
    a quantity absent from the plan remains absent from the candidate (never
    `0.0`, never an average value): the engine then treats it as NOT_CHECKABLE,
    never a default success.
    """
    candidat = {}
    for libelle_de, entree in plan_extraction.items():
        candidat[libelle_de] = extraire_grandeur_test7(
            results_file, libelle_de, entree, resultats_par_jour
        )
    candidat["_provenance"] = {
        "source": "ve_adapter.test7_adapter.extraire_candidat_test7",
        "grandeurs_extraites": sorted(plan_extraction.keys()),
        "pv_ertrag_disponible": False,
        "annee_simulation": ANNEE_SIMULATION,
    }
    return candidat


def extraire_candidat_test7(chemin_aps, plan_extraction, resultats_par_jour=None):
    """Main entry point: opens the `.aps` file, extracts, closes.

    `plan_extraction`: see the "Extraction plan" section above.
    No default plan is provided -- the caller must have built it
    against a real VE (cf. module docstring, point 4).
    """
    iesve = _iesve()
    results_file = iesve.ResultsReader.open(chemin_aps)
    try:
        return extraire_candidat_test7_depuis_fichier(
            results_file, plan_extraction, resultats_par_jour
        )
    finally:
        results_file.close()


# --------------------------------------------------------------------------
# Fixture mode -- operation WITHOUT VE licence (PROJECT_PLAN.md §5).
# PLAUSIBLE JSON, NOT produced by a real IESVE simulation -- so that
# `ui-engineer`/`validation-engine-engineer` can wire Test 7 without VE.
# --------------------------------------------------------------------------

CHEMIN_FIXTURE_DEFAUT = os.path.join(_ICI, "fixtures", "test7_candidat.exemple.json")


def charger_fixture_test7(chemin=None):
    """Load the Test 7 example JSON fixture (no-VE mode).

    This JSON has NEVER been produced by a real IESVE simulation -- its
    ten checkable values are derived from the mean of the reference programs
    (`refs/reference-data/test-7.ref.json`), perturbed by +1%
    to remain visually distinguishable from the reference (same principle
    as `test1_adapter.py::charger_fixture_test1`, which perturbs by +2%).
    `PV-Ertrag` is ABSENT (never fabricated), including in the fixture.
    The `_provenance.source` field recalls this explicitly.
    """
    chemin = chemin or CHEMIN_FIXTURE_DEFAUT
    with io.open(chemin, encoding="utf-8") as flux:
        return json.load(flux)
