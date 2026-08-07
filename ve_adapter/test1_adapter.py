# -*- coding: utf-8 -*-
"""Adaptateur VE -- SIA 4010 Test n 1 (ASHRAE 140 / EN ISO 52016-1 ch. 7).

Ce module est le SEUL endroit du depot qui importe `iesve`. Il traduit entre
l'API VE (VEScripts) et le JSON normalise attendu par
`engine/test1_engine.py::evaluer_test1()`. Le moteur ne doit jamais savoir que
VE existe (CLAUDE.md, "separation dur/pur") ; cet adaptateur ne doit jamais
inventer de valeur, de tolerance ou d'article de norme (CLAUDE.md, regle n 1).

Ecrit en style prudent Python 3.4 (pas de f-string, pas de `dataclasses`) --
ADR-001 §2 n'a PAS tranche la version de Python embarquee dans VEScripts au
moment ou ce fichier est ecrit ; voir `ve_adapter/Run_VE_Probe_Runtime.py`.
Aucune regle de compatibilite n'est donc *garantie*, mais ce choix reste sans
cout et evite de casser le produit si le guide VE 2023 (Python 3.4.3, §2.2 de
l'ADR) s'avere exact.

--------------------------------------------------------------------------
CE QUI EST VERIFIE (chaque symbole `iesve` cite ci-dessous a ete lu dans
`refs/VEScripts-API-VE2023.pdf`, section indiquee -- extraction texte
`pdftotext -layout`, relue integralement) :
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
    `.construction_class` (enums -- valeurs EXACTES non relues fiablement,
    tableau source corrompu par l'extraction multi-colonnes, cf. note plus
    bas : resolues dynamiquement, jamais codees en dur)   §6.1.32
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
    `inside_surface_resistance`, `inside_surface_emissivity` -- AU NIVEAU
    CONSTRUCTION, pas seulement au niveau couche : cf. reserve ci-dessous) §6.1.28
  - `VECdbLayer.set_properties()/get_properties()` : `convection_coefficient`
    (W/m2K), `resistance` (m2K/W), `thickness` (m) -- AU NIVEAU COUCHE       §6.1.30
  - `VEThermalTemplate.set_room_conditions(dict)` /
    `get_room_conditions()` / `add_air_exchange()` / `add_gain()` /
    `apply_changes()`                                                 §6.1.46
  - `iesve.ApacheSim()` ; `.set_options(dict)` / `.get_options()` /
    `.run_simulation(queue_to_tasks=False)`                           §6.1.3
  - `iesve.ResultsReader.open(filename)` ; `.get_room_list()` /
    `.get_room_results(room_id, aps_var, vista_var, var_level,
    start_day=-1, end_day=-1)` / `.get_variables()` / `.get_units()`  §6.1.14
  - `iesve.VELocate()` ; `.open_wea_data()` / `.set(dict)` (cle
    `weather_file`) / `.save_and_close()`                             §6.1.36
  - `iesve.ImportGBXML.Import_file(file_name, heal_geometry, cap_mode,
    cap_height)` -- ATTENTION CASSE : methode documentee avec un "I"
    MAJUSCULE ("Import_file"), alors que `swiss_sia/reference_model/
    ve_api.py:493` (depot externe, non porte ici) appelle
    `self.iesve.ImportGBXML.import_file(...)` en minuscule -- possible bug
    dans ce depot externe, JAMAIS verifie en conditions reelles (ni par eux
    ni par moi). Ce module utilise la casse documentee.                §6.1.9

--------------------------------------------------------------------------
CE QUI N'EST PAS VERIFIE -- ecrit honnetement, marque `# ⚠ A VERIFIER API`
dans le code, jamais comble par supposition :
--------------------------------------------------------------------------
  1. **Creation de la geometrie (corps/pieces) -- NON FOURNIE ICI.** L'API
     documentee ne montre aucun constructeur de type "creer une piece/un
     corps depuis zero" en dehors de l'import gbXML
     (`ImportGBXML.Import_file`, §6.1.9). Ce module NE genere PAS de gbXML et
     N'IMPORTE PAS de geometrie : ecrire un gbXML valide sans pouvoir le
     verifier contre une VE reelle serait fabriquer un contenu non verifiable
     de plus, contraire a la doctrine (CLAUDE.md, regle n 1). Ce point est
     laisse explicitement ouvert -- `GEOMETRIE_CELLULE` (plus bas) documente
     les cotes verifiees, mais leur traduction en objets VE (via gbXML ou
     tout autre moyen) reste a faire par `ve-adapter-engineer` face a une VE
     reelle. Toutes les fonctions de ce module qui suivent (materiaux,
     constructions, gabarit thermique, simulation, extraction) supposent une
     cellule DEJA modelisee (import manuel ou futur mecanisme verifie).
  2. **Quel reglage pilote reellement le coefficient de surface externe
     ApacheSim au pas de temps ?** Table 7-7 (ASHRAE 140:2023, verifiee mot
     pour mot par `norm-analyst`, `traceability/test-1.spec.md` §3.1) donne
     les valeurs. Mais DEUX mecanismes API distincts existent et je n'ai
     verifie NI l'un ni l'autre contre une simulation reelle :
       (a) `VECdbLayer.set_properties({'convection_coefficient': ...})`
           sur la couche EXTERIEURE de la construction (cite par ADR-001 §3
           comme "le" mecanisme) ;
       (b) `VECdbConstruction.set_properties({'outside_surface_resistance':
           ..., 'outside_surface_emissivity': ...})` AU NIVEAU CONSTRUCTION
           (trouve en lisant §6.1.28 pour CE document -- non cite par
           ADR-001 §3, qui ne mentionne que (a)).
     Rien ne prouve que (a) ou (b) -- ou aucun des deux -- pilote le calcul
     DYNAMIQUE d'ApacheSim (ils pourraient n'affecter que le calcul de U
     "statique" affiche dans la boite de dialogue Constructions). La
     fonction `appliquer_coefficient_surface_externe_table_7_7()` ci-dessous
     est fournie a titre d'ESSAI DOCUMENTE, desactivee par defaut
     (`appliquer=False`), et n'est PAS invoquee par le pipeline de
     generation de cas sans decision explicite de l'appelant. Point renvoye
     a `ve-adapter-engineer` (prochaine session avec VE reel) et
     `norm-analyst` -- cf. `traceability/test-1.spec.md` §8 pt 6.
  3. **Instanciation d'un nouvel `AirExchange` / `EnergyGain`.** Le PDF
     documente `get()`/attributs pour des instances DEJA existantes
     (§6.1.2 AirExchange, §6.1.5 CasualGain/EnergyGain) mais aucun exemple
     "Basic usage" ne montre comment en creer une NOUVELLE instance depuis
     un script (a la difference de `iesve.ApacheSim()`, `iesve.VELocate()`,
     qui ont un exemple explicite). Ce module suppose `iesve.AirExchange()`
     et `iesve.EnergyGain()` par coherence avec le reste de la librairie,
     mais CE POINT PRECIS N'EST PAS CONFIRME -- marque `# ⚠ A VERIFIER API`.
  4. **Noms exacts des variables APS** ("Room units heating load", "Comfort
     temperature", etc.). L'API dit explicitement que ces noms figurent dans
     un "units spreadsheet" separe, absent de `/refs`, et que la seule
     source fiable est `get_variables()` a l'execution. Ce module ne code
     donc AUCUN nom de variable en dur dans le chemin d'extraction
     "de confiance" : `LIAISONS_APS_CANDIDATES` (plus bas) reprend, a titre
     de CANDIDAT NON CONFIRME, les noms trouves dans le depot externe
     `IES-Intership-general-repo/config/sia4010_aps_bindings_ve_runtime.json`
     (dont l'auteur affirme les avoir obtenus par une sonde VE reelle,
     2026-07-28/29) -- affirmation que je NE PEUX PAS revalider ici (pas de
     VE dans cet environnement). `extraire_candidat_test1()` REFUSE de s'en
     servir sauf si l'appelant passe explicitement
     `accepter_liaisons_non_confirmees=True`, et le fait alors savoir dans
     le JSON produit (cle `_provenance`).
  5. **Valeurs numeriques des materiaux legers/lourds et du vitrage.**
     `traceability/test-1.spec.md` §4/§8 les maintient `[REQUIS]` : la piste
     ASHRAE 140:2023 Table 7-2/7-27 est "un point de depart documente a tres
     forte presomption, PAS une preuve" (deux reserves non levees : version
     2017 vs 2023 de la norme, gras non preserve par l'extraction texte).
     Ce module les reprend a l'identique (memes chiffres, meme reserve) ;
     voir `MATERIAUX_LEGERS`/`MATERIAUX_LOURDS` plus bas. Le vitrage et
     l'infiltration restent entierement `[REQUIS]` -- non fournis ici.

Rien de ce qui precede n'est resolu par ce fichier. Il pose le contrat
d'extraction (le vrai livrable de cette etape) et fournit un pipeline de
generation de cas qui echoue explicitement, avec message precis, partout ou
un point ci-dessus bloque reellement l'execution.
"""

import calendar
import json
import os


# --------------------------------------------------------------------------
# Constantes normatives -- toutes sourcees, aucune valeur inventee.
# --------------------------------------------------------------------------

# Les 7 cas obligatoires du Test 1 (docs/ADR-001-architecture-MSP.md §5 ;
# traceability/test-1.spec.md §7). "1E" est le seul a porter un critere.
CAS_TEST1 = ('600', '640', '900', '940', '1E', '600FF', '900FF')

MASSE_PAR_CAS = {
    '600': 'legere', '640': 'legere', '600FF': 'legere',
    '900': 'lourde', '940': 'lourde', '900FF': 'lourde',
    '1E': 'legere',  # 1E = cas diagnostic 1D, base sur le cas 600 (leger).
}

# Cles mensuelles identiques a celles de `test-1.ref.json` / `test1_engine.py`.
MOIS = (
    'month_01', 'month_02', 'month_03', 'month_04', 'month_05', 'month_06',
    'month_07', 'month_08', 'month_09', 'month_10', 'month_11', 'month_12',
)

ANNEE_SIMULATION = 2011  # traceability/test-1.spec.md §4 : "1.1.2011-31.12.2011".
assert not calendar.isleap(ANNEE_SIMULATION)  # garde-fou : l'agregation mensuelle
# ci-dessous suppose une annee de 365 jours (8760 h a pas horaire).

# --------------------------------------------------------------------------
# Geometrie de la cellule -- traceability/test-1.spec.md §4 (Figure 2),
# recoupee independamment avec le depot externe (config
# `sia4010_classes_1a_1b.json`, parametres `cell_*`/`south_window_*`,
# statut CONFIRMED dans CE depot externe) : les deux sources concordent et
# ferment dimensionnellement (2*0.5 + 2*3.0 + 1.0 = 8.0 m = largeur facade
# sud). Verdict d'audit : GARDER (AUDIT.md, "Element audite n 2", §A).
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
    """Garde-fou : la geometrie doit fermer dimensionnellement (cf. spec §4)."""
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


# Table 7-2 (cas leger) et Table 7-27 (cas lourd), ASHRAE 140:2023 --
# verifiees mot pour mot par `norm-analyst` (traceability/test-1.spec.md §4).
# STATUT : "presomption forte, PAS une preuve" -- SIA 4010 cite formellement
# EN ISO 52016-1:2017 (absent de /refs) comme source ; deux reserves non
# levees (version 2017 vs 2023 ; mise en gras des deltas non preservee par
# l'extraction texte). Reprises ICI A L'IDENTIQUE de ce que dit la spec --
# PAS une valeur nouvelle, PAS une confirmation supplementaire.
#
# Champs : conductivite [W/(m.K)], epaisseur [m], masse volumique [kg/m3],
# capacite thermique massique [J/(kg.K)]. Ordre : interieur -> exterieur.
MATERIAUX_LEGERS = {
    'mur': (
        {'nom': 'plasterboard', 'conductivite': 0.16, 'epaisseur': 0.012,
         'masse_volumique': 950.0, 'capacite_thermique': 840.0},
        {'nom': 'fiberglass_quilt', 'conductivite': 0.04, 'epaisseur': 0.066,
         'masse_volumique': 12.0, 'capacite_thermique': 840.0},
        {'nom': 'wood_siding', 'conductivite': 0.14, 'epaisseur': 0.009,
         'masse_volumique': 530.0, 'capacite_thermique': 900.0},
    ),
    'toit': (
        {'nom': 'plasterboard_toit', 'conductivite': 0.16, 'epaisseur': 0.010,
         'masse_volumique': 950.0, 'capacite_thermique': None},  # ⚠ cf. note
        {'nom': 'fiberglass_quilt_toit', 'conductivite': 0.04, 'epaisseur': 0.1118,
         'masse_volumique': 12.0, 'capacite_thermique': None},
        {'nom': 'roofdeck', 'conductivite': 0.14, 'epaisseur': 0.019,
         'masse_volumique': 530.0, 'capacite_thermique': None},
    ),
    'plancher': (
        {'nom': 'timber_flooring', 'conductivite': 0.14, 'epaisseur': 0.025,
         'masse_volumique': 650.0, 'capacite_thermique': 1200.0},
        {'nom': 'floor_insulation', 'conductivite': 0.04, 'epaisseur': 1.003,
         'masse_volumique': None, 'capacite_thermique': None},  # (a) cf. note
    ),
}
# Note capacite_thermique=None (toit) : traceability/test-1.spec.md §4 --
# "Les cp du toit sont mal alignes dans l'extraction texte (colonne decalee) --
# a revalider avant usage." Ne JAMAIS inventer une valeur ici : la construction
# du cas leger reste bloquee sur la toiture jusqu'a revalidation (norm-analyst).
# Note masse_volumique/capacite_thermique=None (isolant de plancher) :
# ASHRAE 140:2023 note (a) -- "minimum density/specific heat le logiciel
# testé autorise, mais pas < 0". Valeur numerique exacte a fixer avec
# `ve-adapter-engineer` en fonction de ce qu'IESVE accepte reellement
# (le depot externe utilise 10 kg/m3 / 1400 J/(kg.K) sans le documenter
# comme choix delibere -- voir AUDIT.md, verdict CORRIGER).

MATERIAUX_LOURDS = {
    'mur': (
        {'nom': 'concrete_block', 'conductivite': 0.51, 'epaisseur': 0.100,
         'masse_volumique': 1400.0, 'capacite_thermique': 1000.0},
        {'nom': 'foam_insulation', 'conductivite': 0.04, 'epaisseur': 0.0615,
         'masse_volumique': 10.0, 'capacite_thermique': 1400.0},
        {'nom': 'wood_siding', 'conductivite': 0.14, 'epaisseur': 0.009,
         'masse_volumique': 530.0, 'capacite_thermique': 900.0},
    ),
    # Toiture identique au cas leger (ASHRAE 140:2023, note c, confirmee
    # mot pour mot par norm-analyst : "high-mass case roof is the same as
    # the low-mass case roof").
    'toit': MATERIAUX_LEGERS['toit'],
    'plancher': (
        {'nom': 'concrete_slab', 'conductivite': 1.13, 'epaisseur': 0.080,
         'masse_volumique': 1400.0, 'capacite_thermique': 1000.0},
        {'nom': 'floor_insulation_lourd', 'conductivite': 0.04, 'epaisseur': 1.007,
         'masse_volumique': None, 'capacite_thermique': None},  # (b), idem note ci-dessus
    ),
}

MATERIAUX_PAR_MASSE = {'legere': MATERIAUX_LEGERS, 'lourde': MATERIAUX_LOURDS}


# Table 7-7 ASHRAE 140:2023 -- coefficients de surface EXTERNE alternatifs,
# vent nul, verifies mot pour mot (traceability/test-1.spec.md §3.1). Choix
# de colonne = fonction de l'algorithme de convection d'ApacheSim
# (§7.2.1.9.3 (a)/(b.1)/(b.2), NON TRANCHE -- cf. point 2 de la docstring).
COEFFICIENTS_SURFACE_TABLE_7_7 = {
    'mur': {'convectif_seul': 11.9, 'combine': 21.6},
    'toit': {'convectif_seul': 14.4, 'combine': 21.8},
    'plancher_surelevee': {'convectif_seul': 0.8, 'combine': 5.2},
    'fenetre': {'convectif_seul': 8.0, 'combine': 17.8},
}

# Consignes (traceability/test-1.spec.md §4) -- elements ideaux, pas de HVAC
# reel ("HLK-Anlage : Keine vorhanden").
CONSIGNE_CHAUFFAGE_C = 20.0
CONSIGNE_REFROIDISSEMENT_C = 27.0
CONSIGNE_CHAUFFAGE_REDUITE_C = 10.0  # cas 640/940, 23h00-07h00
HEURE_DEBUT_CONFORT = 7   # 07:00
HEURE_FIN_CONFORT = 23    # 23:00
GAIN_EQUIPEMENT_W = 200.0  # constant, 24h/24, toute l'annee.

CAS_AVEC_CONSIGNE_REDUITE = ('640', '940')
CAS_FLOTTEMENT_LIBRE = ('600FF', '900FF')
CAS_AVEC_CONDITIONNEMENT = ('600', '640', '900', '940', '1E')


# --------------------------------------------------------------------------
# Import paresseux de `iesve` -- jamais au niveau module, pour que ce
# fichier reste lisible/inspectable par des outils qui n'ont pas VE
# (cf. convention deja adoptee par `ve_adapter/Run_VE_Probe_Runtime.py`).
# --------------------------------------------------------------------------

def _iesve():
    """Importe `iesve` a la demande ; erreur precise si VE est indisponible."""
    try:
        import iesve
        return iesve
    except ImportError as erreur:
        raise ImportError(
            "Module 'iesve' indisponible : ce code doit s'executer depuis "
            "la fenetre Scripts d'IESVE (VEScripts), pas en Python autonome. "
            "Erreur d'origine : " + str(erreur))


def _resoudre_membre_enum(conteneur, nom_attribut_enum, nom_membre):
    """Resout dynamiquement un membre d'enum `iesve` -- ne code JAMAIS en dur
    l'orthographe exacte d'un membre (ex. `material_categories.opaque`) car le
    tableau source de `refs/VEScripts-API-VE2023.pdf` §6.1.32 est corrompu par
    l'extraction texte multi-colonnes (colonnes de plusieurs enums fusionnees) :
    aucune orthographe de membre n'y est fiable. Erreur precise si absent.
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
# Generation des materiaux et constructions (VECdbMaterial, VECdbConstruction,
# VECdbLayer -- §6.1.28/30/31/32).
#
# Pattern d'ecriture (creer, ecrire les proprietes, RELIRE et VERIFIER le
# retour de `get_properties()`, echouer fort en cas de divergence) inspire de
# `IES-Intership-general-repo/swiss_sia/reference_model/ve_asset_provisioner.py`
# (`_create_materials`/`_create_construction`, verdict d'audit GARDER pour le
# PATTERN uniquement -- cf. AUDIT.md, "Element audite n 2", §B.1). Le code
# ci-dessous est reecrit ici, pas copie : plus court, specifique au Test 1,
# sans la logique generique de reutilisation/desambiguisation (hors perimetre
# -- ce module suppose un projet VE jetable, dedie a un seul cas a la fois,
# conformement a la prudence deja actee par ce meme depot externe
# ("Run it only in a fresh saved disposable project", case_registry.py).
# --------------------------------------------------------------------------

def creer_materiau(cdb_project, definition):
    """Cree un materiau CDB opaque et VERIFIE la relecture de ses proprietes.

    `definition` : un des dicts de `MATERIAUX_LEGERS`/`MATERIAUX_LOURDS`
    (couche unique). Leve une erreur precise si une propriete numerique est
    `None` (cf. reserves documentees plus haut sur cp toiture / isolant de
    plancher) : ce module refuse de creer un materiau avec une propriete
    inventee.
    """
    iesve = _iesve()
    for cle in ('conductivite', 'epaisseur', 'masse_volumique', 'capacite_thermique'):
        if definition.get(cle) is None:
            raise ValueError(
                "Materiau '{0}' : propriete '{1}' non confirmee (cf. "
                "reserves documentees dans test1_adapter.py sur les Tables "
                "7-2/7-27 ASHRAE 140:2023) -- creation refusee plutot que "
                "d'inventer une valeur.".format(definition['nom'], cle))
    # CORRIGE le 2026-08-06, apres la sonde v2 dans une VE reelle.
    #
    # Deux erreurs cumulees ici :
    #   1. l enum vit sur le MODULE `iesve`, pas sur `VECdbProject` -- c est
    #      ce que la sonde a signale par « Enum ... introuvable » ;
    #   2. `material_categories` n a AUCUN membre `opaque`. Ses 20 membres
    #      sont des familles de bibliotheque (concretes, insulating, timber,
    #      boards...). `opaque` appartient a `construction_class`, pas ici :
    #      les deux enums avaient ete confondus.
    #
    # `other` est un choix de CLASSEMENT en bibliotheque, sans effet sur la
    # simulation -- les proprietes physiques sont portees par `definition`.
    # Le declarer ainsi plutot que de laisser croire a un parametre physique.
    categorie_materiau = _resoudre_membre_enum(
        iesve, 'material_categories', 'other')
    materiau = cdb_project.create_material(categorie_materiau)
    # CORRIGE le 2026-08-07, contre une VE reelle. `set_properties` convertit
    # TOUTES les valeurs en flottant : passer une chaine leve
    # « could not convert string to float: 'plasterboard' ».
    #
    # Les cles reellement acceptees, relevees par `get_properties()` sur un
    # materiau neuf : id, description, specific_heat_capacity, category,
    # conductivity, density, vapour_resistivity.
    #
    #   * `description` s y LIT mais ne s y ECRIT pas — apres ecriture elle
    #     vaut toujours « New Python Material ». Le nom du materiau doit donc
    #     etre porte autrement ; il reste ici en commentaire de tracabilite.
    #   * `thickness` N EXISTE PAS au niveau materiau. L epaisseur appartient
    #     a la COUCHE (`VECdbLayer`, §6.1.30), ce qui est physiquement juste :
    #     un meme materiau sert a plusieurs epaisseurs. La docstring de ce
    #     module le notait deja ; le code la contredisait.
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
    """Cree une construction opaque multicouche (mur/toit/plancher).

    `categorie_element` : nom du membre de l'enum `element_categories`
    (ex. 'wall', 'roof', 'ground_floor' -- §6.1.32 ; orthographe EXACTE non
    lisible de facon fiable dans le PDF corrompu, a CONFIRMER cote VE avant
    premier usage reel, cf. `_resoudre_membre_enum`).
    `classe_construction` : nom du membre de l'enum `construction_class`.
    `couches` : sequence de dicts materiau (interieur -> exterieur), memes
    cles que `MATERIAUX_LEGERS`/`MATERIAUX_LOURDS`.

    Retourne la construction creee (objet VE), apres verification que le
    nombre de couches a bien persiste (cf. AUDIT.md sur ve_asset_provisioner :
    VE 2025.2 cree une couche par defaut qu'il faut retirer -- meme prudence
    reprise ici).
    """
    iesve = _iesve()
    # Les deux enums vivent sur le MODULE `iesve`, verifie par la sonde v2 :
    # element_categories -> roof=0, ceiling/int_floor=1, wall=2, partition=3,
    # ground_floor=4, roof_light=5, ext_glazing=6, int_glazing=7, door=8 ;
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
        construction.add_layer(materiau_id, False)  # False = pas une cavite

    for identifiant in identifiants_par_defaut:
        construction.delete_layer(identifiant)

    couches_finales = list(construction.get_layers())
    if len(couches_finales) != len(couches):
        raise RuntimeError(
            "Construction : {0} couches demandees, {1} persistees apres "
            "creation -- ne pas continuer avec une construction "
            "incomplete.".format(len(couches), len(couches_finales)))
    return construction, materiaux_crees


#: Tolerance relative de relecture. VE stocke en flottant 32 bits : 0,16 ecrit
#: ressort en 0,1599999964237213. Une comparaison exacte echouerait sur une
#: ecriture pourtant correcte, et une tolerance trop large laisserait passer
#: une valeur reellement fausse. 1e-6 relatif separe les deux sans ambiguite.
TOLERANCE_RELECTURE = 1e-6


def _identifiant_materiau(materiau):
    """Identifiant persistant d'un materiau CDB.

    CORRIGE le 2026-08-07. Le code lisait `materiau.id`, qui n existe pas :
    `VECdbMaterial` n expose que `get_properties`, `set_properties` et
    `get_review_summary_string`. L identifiant est une CLE du dictionnaire
    rendu par `get_properties()` — releve : `{'id': 'PYOP3', ...}`.

    L attribut est tout de meme tente en premier : si une version de VE
    l ajoutait, autant s en servir.

    Args:
        materiau: `VECdbMaterial` fraichement cree.

    Returns:
        str | None: Identifiant, ou `None` s il reste introuvable.
    """
    direct = getattr(materiau, 'id', None)
    if direct is not None:
        return direct
    try:
        return (materiau.get_properties() or {}).get('id')
    except Exception:  # noqa: BLE001 -- l absence est un resultat, pas un plantage
        return None


def _verifier_proprietes_ecrites(materiau, proprietes, nom):
    """Relit un materiau et confronte ses proprietes a ce qui a ete ecrit.

    POURQUOI RELIRE. `set_properties` ne rend rien et ne leve pas toujours :
    la reconnaissance du 2026-08-07 a montre que `set_heating()` accepte meme
    un appel sans argument. Une ecriture ignoree passerait donc inapercue, et
    la simulation tournerait sur des valeurs par defaut en produisant des
    nombres credibles.

    Args:
        materiau: `VECdbMaterial` fraichement ecrit.
        proprietes: Ce qui vient d'etre demande.
        nom: Nom du materiau, pour le message.

    Raises:
        RuntimeError: Si une propriete n'a pas ete prise, ou si la relecture
            est impossible.
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
    """Cree les 3 constructions opaques (mur/toit/plancher) d'une masse donnee.

    `masse` : 'legere' ou 'lourde' (cle de `MASSE_PAR_CAS`).
    Retourne un dict {'mur': construction, 'toit': ..., 'plancher': ...}.

    ORTHOGRAPHES CONFIRMEES le 2026-08-06 contre une VE 2025 reelle, et figees
    dans `refs/reference-data/iesve-enums-ve2025.json` : element_categories
    wall=2, roof=0, ground_floor=4 ; construction_class opaque=0. La reserve
    « presumes par coherence de nommage anglais » qui figurait ici est levee.

    `cdb_project` est un `VECdbProject`, PAS un `VECdbDatabase` : c'est le
    projet qui porte `create_construction`. La sonde s'y etait trompee.
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
    """Applique -- OU NON -- un coefficient de surface externe Table 7-7.

    DESACTIVE PAR DEFAUT (`appliquer=False`) : cf. point 2 de la docstring de
    module. N'ecrit RIEN sur la couche/la construction sauf demande explicite.

    `type_surface` : cle de `COEFFICIENTS_SURFACE_TABLE_7_7`
    ('mur'/'toit'/'plancher_surelevee'/'fenetre').
    `branche` : 'convectif_seul' ou 'combine' (§7.2.1.9.3 (b.1)/(b.2)) --
    choix NON TRANCHE, a fournir explicitement par l'appelant apres
    verification de l'algorithme de convection d'ApacheSim (renvoye a
    `ve-adapter-engineer`, traceability/test-1.spec.md §8 pt 6).

    Ecrit sur la couche EXTERIEURE (`VECdbLayer.set_properties
    ({'convection_coefficient': ...})`, §6.1.30) -- mecanisme (a) de la
    reserve documentee plus haut ; le mecanisme (b) (proprietes au niveau
    construction) n'est PAS applique ici, faute de preuve qu'un des deux (ou
    aucun) pilote reellement ApacheSim.
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
# Gabarit thermique -- consignes, profils, apports, infiltration
# (VEThermalTemplate, VEProfile, AirExchange, EnergyGain -- §6.1.2/5/39/46).
# --------------------------------------------------------------------------

def creer_profil_consigne_chauffage(project, cas_id):
    """Cree le profil journalier de consigne de chauffage pour un cas.

    Cas 600/900/1E/*FF : profil non necessaire (consigne constante -- ecrite
    directement via `heating_setpoint` dans `set_room_conditions`, pas de
    profil). Cas 640/940 : profil journalier 20 degC (07h-23h) / 10 degC
    (23h-07h), traceability/test-1.spec.md §4.

    Retourne l'identifiant du profil cree, ou None si aucun profil requis.
    """
    if cas_id not in CAS_AVEC_CONSIGNE_REDUITE:
        return None
    profil = project.create_profile('daily', 'SIA4010_T1_chauffage_reduit_' + cas_id,
                                     False, 0)
    # VEProfile.set_data() -- profil journalier : liste [x, y, formule].
    # x = heure (0-24), y = valeur (degC). Deux paliers, transitions nettes.
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
    """Construit le dict `room_conditions` attendu par
    `VEThermalTemplate.set_room_conditions()` (§6.1.46) pour un cas donne.

    ⚠ A VERIFIER API : les cles `heating_setpoint_type`/`cooling_setpoint_type`
    documentees dans refs/VEScripts-API-VE2023.pdf §6.1.46 sont mal
    extraites ("heating_setpoint_typeconstant"/"heating_setpoint_typeprofile"
    -- fusion probable de deux lignes par `pdftotext`). Ce module ecrit les
    cles `heating_setpoint`/`cooling_setpoint` (valeurs constantes) et
    `heating_profile` (si profil reduit) sans fixer `*_setpoint_type`
    explicitement : a completer/corriger avec `ve-adapter-engineer` une fois
    la VE reelle disponible pour lire `get_room_conditions()` et voir la
    forme exacte attendue en retour.
    """
    conditions = {
        'cooling_setpoint': CONSIGNE_REFROIDISSEMENT_C,
    }
    if cas_id in CAS_FLOTTEMENT_LIBRE:
        # Flottement libre : aucun element ideal actif. Ne PAS ecrire de
        # consigne -- laisser le template sans chauffage/refroidissement.
        # ⚠ A VERIFIER API : mecanisme exact pour desactiver un element ideal
        # deja configure (retirer les cles ? ecrire une valeur sentinelle ?).
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
    """Cree l'apport interne 'equipements' constant 200 W, 24h/24, permanent.

    traceability/test-1.spec.md §4 : "Equipements : 200 W au total, profil
    constant 24 h, present toute l'annee".

    ⚠ A VERIFIER API : `iesve.EnergyGain()` (constructeur) n'a PAS d'exemple
    "Basic usage" dans refs/VEScripts-API-VE2023.pdf §6.1.5 -- seuls `get()`
    et les attributs d'une instance existante y sont documentes. Ce module
    suppose la construction sans argument par coherence avec le reste de la
    librairie (`iesve.ApacheSim()`, `iesve.VELocate()`), sans preuve directe.
    """
    iesve = _iesve()
    gain = iesve.EnergyGain()  # ⚠ A VERIFIER API -- cf. docstring ci-dessus.
    gain.set({
        'max_power_consumption': GAIN_EQUIPEMENT_W,
        'max_sensible_gain': GAIN_EQUIPEMENT_W,
        'radiant_fraction': 0.0,  # ⚠ A VERIFIER : non specifie par la spec Test 1 ;
        # 0.0 = tout convectif, valeur PAR DEFAUT dans ce module et non une
        # valeur normative -- a confirmer avec norm-analyst avant usage reel.
        'type_str': 'Miscellaneous',
        'units_val': 1,  # 1 = W (total), pas W/m2 -- §6.1.5.
    })
    return gain


def creer_infiltration(project, taux_infiltration_ach):
    """Cree l'objet AirExchange 'Infiltration' du Test 1.

    ⚠ NON UTILISABLE EN L'ETAT : le taux d'infiltration exact reste `[REQUIS]`
    (traceability/test-1.spec.md §4/§8 pt 4 -- renvoi a EN ISO 52016-1 ch. 7,
    absent de `/refs`). Cette fonction n'invente donc aucune valeur par
    defaut : `taux_infiltration_ach` DOIT etre fourni explicitement par
    l'appelant, avec sa propre justification/citation, et cette fonction
    leve une erreur si `None`.

    ⚠ A VERIFIER API : `iesve.AirExchange()` (constructeur) -- meme reserve
    que `creer_gain_equipement()' ci-dessus (§6.1.2 ne montre pas de
    "Basic usage" avec constructeur).
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
# Orchestration d'un cas -- assemble materiaux/constructions/gabarit.
# --------------------------------------------------------------------------

def generer_cas_test1(project, cdb_project, gabarit_thermique, cas_id,
                       taux_infiltration_ach=None):
    """Genere un cas du Test 1 (hors 1E) dans le projet VE courant.

    `gabarit_thermique` : objet `VEThermalTemplate` deja assigne aux pieces
    de la cellule de test (assignation/geometrie hors perimetre de cette
    fonction -- cf. point 1 de la docstring de module, geometrie non
    verifiee end-to-end).

    Cas '1E' NON SUPPORTE ICI : necessite le store tissu (Stoffmarkise) du
    test diagnostic 2 E1 (traceability/test-1.spec.md §7), qui appartient au
    Test 2, pas au Test 1. Le depot externe audite (case_registry.py,
    `IES-Intership-general-repo`) arrive independamment a la meme conclusion
    : le cas 1E est absent de sa liste de cas "apachesim_qualification_
    supported" -- recoupement qui renforce la decision de le laisser hors
    perimetre ici plutot que d'improviser une modelisation du store.
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
    """Assigne le fichier meteo DRYCOLD.TMY au projet courant (§6.1.36).

    traceability/test-1.spec.md §4 : "Fichier meteo : DRYCOLD.TMY (BESTEST)
    Denver, CO". Ce module ne fournit PAS le fichier lui-meme (a obtenir/
    convertir separement -- hors perimetre) ; il se contente de le pointer.
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
# Simulation ApacheSim (§6.1.3).
#
# ⚠ ADR-001 §3 cite `ApacheSim.save_options({...})` (repris de l'exemple
# "Basic usage" du PDF, ligne ~960 de l'extraction texte). Mais la table
# formelle "Methods Defined Here" du MEME document (§6.1.3.1) ne liste PAS
# `save_options` : elle liste `set_options({options}) -> Bool` et
# `get_options() -> dict`. C'est une incoherence interne au PDF source (pas
# une erreur introduite ici) : l'exemple d'usage semble perime par rapport a
# la table de methodes. Ce module utilise `set_options()`/`get_options()`
# (methode formellement documentee, et systematiquement relue apres
# ecriture ci-dessous) et NE reprend PAS `save_options`. A signaler a
# `norm-analyst`/`ve-adapter-engineer` : corriger la citation d'ADR-001 §3.
# --------------------------------------------------------------------------

def lancer_apachesim_cas(nom_fichier_aps, options_supplementaires=None):
    """Lance une simulation ApacheSim annuelle pour un cas et retourne le
    nom du fichier .aps genere.

    traceability/test-1.spec.md §4 : periode 1.1.2011-31.12.2011, pas horaire
    implicite (non precise par la spec Test 1 -- IESVE par defaut ; ⚠ A
    VERIFIER si un pas plus fin est necessaire pour respecter le protocole
    ASHRAE 140).
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
        'HVAC': False,  # Test 1 : elements ideaux, pas de reseau HVAC reel.
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
# Extraction des resultats (.aps, ResultsReader -- §6.1.14) -> JSON
# normalise attendu par engine/test1_engine.py::evaluer_test1().
#
# FORME CONFIRMEE ICI (leve le "⚠ A VERIFIER" laisse par
# `engine/test1_engine.py::evaluer_test1`, docstring) :
#   - miroir exact de `reference_values` dans test-1.ref.json : memes
#     grandeurs, memes cas par grandeur (verifie contre le JSON de reference
#     lui-meme -- pas suppose) :
#       sensible_heating_demand_kwh / sensible_cooling_demand_kwh :
#           cas {1E, 600, 640, 900, 940} ; noeud {monthly: {month_01..12},
#           annual: <scalaire>}.
#       operative_temperature_monthly_celsius :
#           cas {600, 640, 900, 940, 600FF, 900FF} ; noeud
#           {monthly: {month_01..12, annual: <scalaire>}} -- **l'annuel est
#           IMBRIQUE sous `monthly`**, pas un frere de `monthly` (asymetrie
#           deja actee par AUDIT.md, "remarques non bloquantes" pt 1, pour
#           la reference elle-meme -- ce module produit un candidat qui
#           respecte la MEME asymetrie, volontairement, pour que
#           `test1_engine.py::_perioder_temperature_mensuelle` s'applique
#           sans modification).
#       operative_temperature_annual_extremes_celsius :
#           cas {600FF, 900FF} ; noeud {extremes: {max, min, average}}.
#   - feuilles terminales = **nombres bruts** (`float`) ou `None` (jamais
#     un dict `{"value": ...}`) : forme la plus simple des deux acceptees
#     par `test1_engine.py::_valeur_candidate`.
# --------------------------------------------------------------------------

# Liaisons candidates non confirmees -- portees, avec attribution explicite,
# depuis `IES-Intership-general-repo/config/sia4010_aps_bindings_ve_runtime.json`
# (depot externe, non consolide dans ce depot -- ADR-001 §8 laisse la
# consolidation ouverte). L'auteur de ce fichier affirme les avoir obtenues
# par une sonde VE reelle le 2026-07-28/29 (checksum, evidence_locator dans
# le fichier source). Je n'ai PAS pu revalider cette affirmation (pas de VE
# dans cet environnement) -- verdict d'audit CORRIGER (AUDIT.md, "Element
# audite n 2", §C.2) : a reconfirmer par une sonde VE reelle avant tout
# usage en production. `extraire_candidat_test1()` refuse de s'en servir
# sans `accepter_liaisons_non_confirmees=True` explicite.
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
        # Le depot externe cite https://help.iesve.com/ve2025/... pour
        # justifier "dry resultant temperature" = "operative temperature"
        # en air calme -- page VE2025, alors que nos refs/ sont VE2023 :
        # incoherence de version supplementaire, jamais reconciliee ici.
    },
}


def decouvrir_candidats_variable(results_file, jetons_requis, niveau=None):
    """Aide a la DECOUVERTE de variables APS -- PAS pour l'extraction de
    confiance (aucun verdict pass/fail ne doit s'appuyer sur cette fonction).

    Recherche par jetons (sous-chaines, insensible a la casse) dans
    `aps_varname`/`display_name`, retournes par `get_variables()` (§6.1.14).
    A utiliser manuellement par `ve-adapter-engineer` face a une VE reelle
    pour CONFIRMER ou CORRIGER `LIAISONS_APS_CANDIDATES` -- jamais appelee
    par `extraire_candidat_test1()`.
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
    """Resout une liaison candidate contre les variables REELLEMENT
    presentes dans le fichier .aps ouvert (jamais de nom en dur non verifie
    a l'execution)."""
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
    """Lit une serie annuelle complete via `get_room_results()` (§6.1.14) et
    la ramene a un pas HORAIRE (moyenne des sous-pas), quel que soit le pas
    de simulation reel."""
    brute = results_file.get_room_results(
        room_id, liaison['aps_varname'], liaison['display_name'],
        liaison['model_level'])  # start_day/end_day omis = annee complete.
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
    """Retourne un dict {'month_01': somme, ..., 'month_12': somme} + le
    total annuel, a partir d une serie horaire complete (8760 valeurs)."""
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
    """Comme `_agreger_mensuel_sommes` mais moyenne (pour la temperature).

    Rend `(mensuel, moyenne_des_mensuelles, moyenne_horaire)`.

    ⚠ LES DEUX MOYENNES ANNUELLES SONT DIFFERENTES, ET LE CLASSEUR SIA LES
    UTILISE A DEUX ENDROITS DIFFERENTS. Ne pas les confondre :

      * `moyenne_des_mensuelles` -> **Table 30**, ligne `Annual`. Formule du
        classeur relevee directement : `B70 = AVERAGE(B58:B69)`, soit la moyenne
        NON PONDEREE des 12 moyennes mensuelles (verifie aussi en C70, AI70,
        AQ70). Les mois n'ayant pas le meme nombre d'heures, ce n'est PAS la
        moyenne horaire.
      * `moyenne_horaire` -> **Table 32**, ligne `Average`, qui vient de
        l'agregat horaire de `Daten_Testprogramm`
        (`B107 = ...Daten_Testprogramm!C104`).

    L'ecart mesure entre les deux vaut environ 0.04 K sur les programmes de
    reference. Utiliser la moyenne horaire face a la Table 30 introduit donc un
    biais systematique silencieux — c'est le defaut que ce commentaire existe
    pour empecher de reintroduire.
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
    """Extrait, pour UN cas deja simule (fichier .aps ouvert), les grandeurs
    candidates du Test 1 dans la forme MIROIR de `test-1.ref.json` (feuilles
    terminales = scalaires bruts). Ne remplit QUE les grandeurs pertinentes
    pour ce cas (cf. mapping grandeur/cas verifie contre `test-1.ref.json`
    en tete de section) ; les autres grandeurs sont omises (pas `None` --
    `test1_engine.py::evaluer_test1` gere l'absence via `candidat_grandeur.
    get(cas)` -> `None` -> chaque periode evaluee avec candidat `None`).
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
        # kW moyen sur l'heure -> kWh (pas horaire => energie = puissance).
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

    if cas_id not in ('1E',):  # Table 30 : pas de colonne pour 1E (AUDIT.md pt 3).
        liaison_temperature = _resoudre_liaison(
            results_file, 'operative_temperature', liaisons)
        serie_temperature = _lire_serie_horaire(
            results_file, room_id, liaison_temperature, resultats_par_jour)
        (mensuel_temp, annuel_des_mensuelles,
         annuel_horaire) = _agreger_mensuel_moyennes(serie_temperature)
        mensuel_temp_avec_annuel = dict(mensuel_temp)
        # Table 30 ligne `Annual` = AVERAGE des 12 mensuelles (B70 du classeur),
        # PAS la moyenne horaire : ecart systematique d'environ 0.04 K.
        mensuel_temp_avec_annuel['annual'] = annuel_des_mensuelles
        resultat['operative_temperature_monthly_celsius'] = {
            'monthly': mensuel_temp_avec_annuel,
        }

        if cas_id in CAS_FLOTTEMENT_LIBRE:
            resultat['operative_temperature_annual_extremes_celsius'] = {
                'extremes': {
                    'max': max(serie_temperature),
                    'min': min(serie_temperature),
                    # Table 32 ligne `Average` : ici c'est bien la moyenne
                    # HORAIRE, conformement a Daten_Testprogramm!C104.
                    'average': annuel_horaire,
                },
            }

    return resultat


def extraire_candidat_test1(chemins_aps_par_cas, resolveur_room_id=None,
                             liaisons=None, accepter_liaisons_non_confirmees=False):
    """Point d'entree principal de l'extraction -- construit le JSON complet
    attendu par `engine/test1_engine.py::evaluer_test1(reference, candidat)`.

    `chemins_aps_par_cas` : dict {cas_id: chemin_fichier_aps}. Seuls les cas
    presents sont extraits (les autres restent absents du candidat -- le
    moteur gere cette absence sans lever d'erreur, cf. docstring
    `evaluer_test1`).
    `resolveur_room_id` : fonction(results_file) -> room_id. Par defaut,
    exige exactement UNE piece dans le fichier .aps (Test 1 = zone unique,
    traceability/test-1.spec.md §4) et leve une erreur precise sinon.
    `liaisons` : dict de liaisons APS confirmees. Si `None`, utilise
    `LIAISONS_APS_CANDIDATES` -- MAIS seulement si
    `accepter_liaisons_non_confirmees=True` est passe explicitement, sinon
    leve une erreur (cf. reserve documentee plus haut : ces liaisons ne sont
    pas confirmees par une VE reelle DANS CET ENVIRONNEMENT).
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
        # get_room_list() -> [(nom, id, aire, volume), ...] (§6.1.14).
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
# Mode fixture -- fonctionnement SANS licence VE (PROJECT_PLAN.md §5,
# "Adaptateur VE extrait les grandeurs requises, ou stub documente si VE
# indispo"). JSON PLAUSIBLE, PAS issu d'une simulation reelle -- pour que
# `ui-engineer` cable le navigateur sans VE.
# --------------------------------------------------------------------------

_ICI = os.path.dirname(os.path.abspath(__file__))
CHEMIN_FIXTURE_DEFAUT = os.path.join(_ICI, 'fixtures', 'test1_candidat.exemple.json')


def charger_fixture_test1(chemin=None):
    """Charge la fixture JSON d'exemple du Test 1 (mode sans VE).

    Ce JSON N'A JAMAIS ete produit par une simulation IESVE reelle -- il
    sert uniquement a developper `ui-engineer`/`validation-engine-engineer`
    sans licence VE. Le champ `_provenance.source` du fichier le rappelle
    explicitement pour eviter toute confusion en aval.
    """
    chemin = chemin or CHEMIN_FIXTURE_DEFAUT
    with open(chemin, encoding='utf-8') as flux:
        return json.load(flux)
