"""Sonde de capacité de construction du projet de référence SIA 380/2.

Dry-run strict : ce script ne mute RIEN dans le projet VE.  Il lit le modèle
actif, construit la spec de substitution SIA 380/2 et sonde, pour chaque
famille de substitution, si l'API VE expose les getters, setters et fonctions
de readback nécessaires au constructeur de projet de référence (Phase B).

Utilisation :
  Ouvrir dans IESVE VEScripts avec le projet client actif → Run.
  Le rapport JSON est écrit dans le répertoire parent du projet VE.

Familles sondées :
  1. Enveloppe opaque (murs/toits/planchers — U-value)
  2. Vitrage (window_u, frame_fraction, g_value, τ_v)
  3. Infiltration (q50 bâtiment)
  4. Génération refroidissement (EER — famille la plus incertaine)
  5. Génération chauffage (SCOP / PAC)
  6. Émission (directive radiant_fraction = 0)
  7. Capacité illimitée (directive)

Verdicts par substitution :
  MUTABLE          — setter + capability-check + readback disponibles
  NO_SETTER        — getter/résolution OK mais setter absent
  NO_CAPABILITY    — construction résolue mais propriété non exposée
  UNRESOLVED       — construction/cible non localisable dans la CDB

Sources API citées pour chaque membre :
  Module existant  → ligne du module dans ce dépôt
  ⚠ À VÉRIFIER API → membre non trouvé dans les modules existants ;
                      vérification manuelle requise sur le projet ZOER réel.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)


# ---------------------------------------------------------------------------
# Phase 0 : purge du cache de modules VE
# VE maintient l'interpréteur Python entre deux clics Run et met en cache les
# modules dans sys.modules.  Sans purge, un deuxième Run réutilise le code de
# l'exécution précédente — leçon acquise en session.  Obligatoire.
# ---------------------------------------------------------------------------
for _mod_name in [n for n in list(sys.modules)
                  if n == "swiss_sia" or n.startswith("swiss_sia.")]:
    del sys.modules[_mod_name]


# ---------------------------------------------------------------------------
# Constantes de verdict
# ---------------------------------------------------------------------------
VERDICT_MUTABLE = "MUTABLE"
VERDICT_NO_SETTER = "NO_SETTER"
VERDICT_NO_CAPABILITY = "NO_CAPABILITY"
VERDICT_UNRESOLVED = "UNRESOLVED"
VERDICT_UNCERTAIN = "UNCERTAIN"          # génération — setter API non vérifiée
VERDICT_DIRECTIVE = "DIRECTIVE_PROBED"  # directives sans valeur projet


# ---------------------------------------------------------------------------
# Utilitaires de sérialisation
# Même pattern que Run_VE_SIA3802_Reference_Extraction_Probe.py et
# Run_VE_Reference_Model_Capability_Probe.py — JSON-safe, depth-bounded.
# ---------------------------------------------------------------------------

def _jsonable(value, depth=0):
    """Convertit les types VE (enums, Boost.Python) en valeurs JSON sûres."""
    if depth > 4:
        return repr(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {
            str(k): _jsonable(v, depth + 1)
            for k, v in list(value.items())[:100]
        }
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v, depth + 1) for v in list(value)[:100]]
    enum_value = getattr(value, "value", None)
    if enum_value is not None and enum_value is not value:
        return {"name": str(value), "value": _jsonable(enum_value, depth + 1)}
    return str(value)


def _has_callable(obj, name):
    """Retourne (bool, détail) pour la présence d'un attribut callable."""
    if obj is None:
        return False, "objet est None"
    if not hasattr(obj, name):
        return False, "attribut '{}' absent".format(name)
    member = getattr(obj, name)
    if not callable(member):
        return False, "'{}' présent mais non callable".format(name)
    return True, "callable"


# ---------------------------------------------------------------------------
# Accès CDB : chemin identique à IesVeGateway._cdb_project()
# Source : swiss_sia/reference_model/ve_api.py:628
# ---------------------------------------------------------------------------

def _resolve_cdb_project(iesve):
    """Retourne le premier projet CDB courant ou None si indisponible."""
    try:
        database = iesve.VECdbDatabase.get_current_database()
        projects = database.get_projects()
        candidates = projects.get(0, []) if isinstance(projects, dict) else []
        return candidates[0] if candidates else None
    except Exception as exc:
        print("WARN: CDB non disponible : {}".format(exc))
        return None


# ---------------------------------------------------------------------------
# Sonde CDB globale : enums et capacités de création
# ---------------------------------------------------------------------------

def _probe_cdb_capabilities(iesve, cdb_project):
    """Inventorie les capacités CDB requises pour créer des constructions réf."""
    result = {
        "cdb_project_available": cdb_project is not None,
    }

    # create_construction (source : ve_mutation_policy_probe.py:303)
    result["create_construction"] = {
        "available": hasattr(cdb_project, "create_construction") if cdb_project else False,
        "source": "ve_mutation_policy_probe.py:303",
    }

    # get_construction (source : ve_api.py:676)
    result["get_construction"] = {
        "available": hasattr(cdb_project, "get_construction") if cdb_project else False,
        "source": "ve_api.py:676",
    }

    # get_construction_ids (source : Run_VE_Reference_Model_Capability_Probe.py:239)
    result["get_construction_ids"] = {
        "available": hasattr(cdb_project, "get_construction_ids") if cdb_project else False,
        "source": "Run_VE_Reference_Model_Capability_Probe.py:239",
    }

    # create_material (source : ve_mutation_policy_probe.py:300)
    result["create_material"] = {
        "available": hasattr(cdb_project, "create_material") if cdb_project else False,
        "source": "ve_mutation_policy_probe.py:300",
    }

    # uvalue_types.iso — sur la CLASSE VECdbProject, pas l'instance
    # (source : ve_api.py:648-657)
    cdb_project_cls = getattr(iesve, "VECdbProject", None)
    uvalue_types = getattr(cdb_project_cls, "uvalue_types", None)
    if uvalue_types is None:
        uvalue_types = getattr(iesve, "uvalue_types", None)
    iso_member = getattr(uvalue_types, "iso", None)
    result["uvalue_types_iso"] = {
        "available": iso_member is not None,
        "value": _jsonable(iso_member),
        "source": "ve_api.py:648-657 — sur VECdbProject (classe), pas l'instance",
    }

    # construction_class.opaque / .glazed (source : ve_api.py:642)
    cc_container = getattr(cdb_project_cls, "construction_class", None)
    if cc_container is None:
        cc_container = getattr(iesve, "construction_class", None)
    result["construction_class_opaque"] = {
        "available": getattr(cc_container, "opaque", None) is not None,
        "source": "ve_api.py:642",
    }
    result["construction_class_glazed"] = {
        "available": getattr(cc_container, "glazed", None) is not None,
        "source": "Run_VE_Inspect_Reference_Constructions.py:59",
    }

    return result


# ---------------------------------------------------------------------------
# Sonde d'une construction individuelle via ConstructionBinder
# Sources : swiss_sia/reference_model/ve_construction_binder.py
# ---------------------------------------------------------------------------

def _probe_construction(binder, construction_id):
    """
    Résout une construction CDB et rapporte getter/propriétés disponibles.
    NE MUTE RIEN — résolution read-only.
    """
    from swiss_sia.reference_model.ve_construction_binder import BindStatus

    result = binder.resolve(construction_id)

    probe = {
        "construction_id": construction_id,
        "resolution_status": result.status.value,
        "signatures_tried": list(result.signatures_tried),
        "last_exception": result.last_exception_repr,
    }

    if result.status is not BindStatus.RESOLVED:
        probe["verdict"] = VERDICT_UNRESOLVED
        return probe

    construction = result.construction

    # --- get_properties()
    # Source : Run_VE_Inspect_Reference_Constructions.py:74
    ok_gp, detail_gp = _has_callable(construction, "get_properties")
    prop_info = {"available": ok_gp, "detail": detail_gp,
                 "source": "Run_VE_Inspect_Reference_Constructions.py:74"}
    u_value_key = None
    if ok_gp:
        try:
            props = dict(construction.get_properties())
            prop_info["property_keys"] = sorted(str(k) for k in props)
            # Recherche du champ U-value dans les propriétés.
            # ⚠ À VÉRIFIER API : le nom exact du champ U dans get_properties()
            # n'est pas documenté explicitement dans les modules existants.
            # Les candidats ci-dessous sont déduits des noms VE courants.
            for candidate in (
                "thermal_transmittance",
                "u_value",
                "U_value",
                "uvalue",
                "overall_u_value",
                "u",
            ):
                if candidate in props:
                    u_value_key = candidate
                    prop_info["u_value_key_found"] = candidate
                    prop_info["u_value_current"] = _jsonable(props[candidate])
                    break
            if u_value_key is None:
                prop_info["u_value_key_found"] = None
                prop_info["note"] = (
                    "Aucun champ U-value identifié par candidature. "
                    "VE calcule le U à partir des couches (get_layers), "
                    "pas forcément via un champ direct. "
                    "⚠ À VÉRIFIER API : confirmer sur le projet ZOER réel."
                )
        except Exception as exc:
            prop_info["error"] = str(exc)
    probe["getter_get_properties"] = prop_info

    # --- get_layers()
    # Source : ve_api.py:748
    ok_gl, detail_gl = _has_callable(construction, "get_layers")
    layers_info = {"available": ok_gl, "detail": detail_gl,
                   "source": "ve_api.py:748"}
    if ok_gl:
        try:
            layers = list(construction.get_layers())
            layers_info["layer_count"] = len(layers)
            sample = []
            for layer in layers[:3]:
                linfo = {}
                ok_lp, _ = _has_callable(layer, "get_properties")
                linfo["get_properties_available"] = ok_lp
                if ok_lp:
                    try:
                        lprops = dict(layer.get_properties())
                        linfo["property_keys"] = sorted(str(k) for k in lprops)
                    except Exception as exc:
                        linfo["get_properties_error"] = str(exc)
                # ⚠ À VÉRIFIER API : set_properties() sur une couche —
                # non documenté dans les modules existants.
                linfo["set_properties_present"] = hasattr(layer, "set_properties")
                linfo["set_present"] = hasattr(layer, "set")
                sample.append(linfo)
            layers_info["layer_sample"] = sample
        except Exception as exc:
            layers_info["get_layers_error"] = str(exc)
    probe["getter_get_layers"] = layers_info

    # --- attribut opaque (source : ve_api.py:708)
    probe["attr_opaque"] = {
        "available": hasattr(construction, "opaque"),
        "value": _jsonable(getattr(construction, "opaque", None)),
        "source": "ve_api.py:708",
    }

    # --- get_g_values() — glazé seulement, gardé par hasattr
    # Source : Run_VE_Reference_Model_Capability_Probe.py:272
    if hasattr(construction, "get_g_values"):
        gv_info = {
            "available": True,
            "source": "Run_VE_Reference_Model_Capability_Probe.py:272",
        }
        try:
            gv_info["value"] = _jsonable(construction.get_g_values())
        except Exception as exc:
            gv_info["error"] = str(exc)
        probe["getter_get_g_values"] = gv_info
    else:
        probe["getter_get_g_values"] = {"available": False}

    probe["u_value_key_in_properties"] = u_value_key
    return probe


# ---------------------------------------------------------------------------
# Sonde corps / surfaces / ouvertures (read-only enumération)
# ---------------------------------------------------------------------------

def _is_room_body(body):
    """
    Filtre les corps de type room.
    Source : ve_api.py:532 (IesVeGateway._is_room) — même logique,
    version défensive sans dépendance à iesve.VEBody.VEBody_type.
    """
    try:
        type_str = str(getattr(body, "type", "") or "")
        normalised = type_str.lower().replace("_", "").replace(" ", "")
        return normalised.endswith("room")
    except Exception:
        return False


def _probe_body_surface_api(model):
    """
    Sonde les API corps/surfaces/ouvertures sur 2 rooms au maximum.
    Lit UNIQUEMENT des handles — aucun set_* appelé.

    Membres vérifiés et leurs sources :
      model.get_bodies(False)            → ve_api.py:543
      body.get_surfaces()                → ve_api.py:762
      body.assign_construction           → ve_api.py:764  (hasattr uniquement)
      body.assign_construction_to_opening→ ve_api.py:790  (hasattr uniquement)
      surface.get_constructions()        → ve_api.py:767
      surface.get_openings()             → ve_api.py:776
      surface.get_properties()           → ve_api.py:607
      opening.get_id()                   → ve_api.py:790
      opening.get_construction()         → ve_api.py:793
      opening.get_properties()           → ve_api.py:779
    """
    result = {
        "get_bodies_available": False,
        "body_get_surfaces_available": False,
        "body_assign_construction_present": False,
        "body_assign_construction_to_opening_present": False,
        "surface_get_constructions_available": False,
        "surface_get_openings_available": False,
        "surface_get_properties_available": False,
        "opening_get_id_present": False,
        "opening_get_construction_present": False,
        "opening_get_properties_present": False,
        "sample_surface_count": 0,
        "sample_opening_count": 0,
        "errors": [],
    }

    ok_gb, _ = _has_callable(model, "get_bodies")
    result["get_bodies_available"] = ok_gb
    if not ok_gb:
        return result

    try:
        all_bodies = list(model.get_bodies(False))
    except Exception as exc:
        result["errors"].append("get_bodies: {}".format(exc))
        return result

    room_bodies = [b for b in all_bodies if _is_room_body(b)]

    for body in room_bodies[:2]:
        # assign_construction / to_opening : hasattr uniquement, JAMAIS appelé
        result["body_assign_construction_present"] = (
            result["body_assign_construction_present"]
            or hasattr(body, "assign_construction")
        )
        result["body_assign_construction_to_opening_present"] = (
            result["body_assign_construction_to_opening_present"]
            or hasattr(body, "assign_construction_to_opening")
        )

        ok_gs, _ = _has_callable(body, "get_surfaces")
        result["body_get_surfaces_available"] = (
            result["body_get_surfaces_available"] or ok_gs
        )
        if not ok_gs:
            continue

        try:
            surfaces = list(body.get_surfaces())
        except Exception as exc:
            result["errors"].append("get_surfaces: {}".format(exc))
            continue

        result["sample_surface_count"] += len(surfaces)

        for surface in surfaces[:4]:
            result["surface_get_constructions_available"] = (
                result["surface_get_constructions_available"]
                or hasattr(surface, "get_constructions")
            )
            result["surface_get_openings_available"] = (
                result["surface_get_openings_available"]
                or hasattr(surface, "get_openings")
            )
            result["surface_get_properties_available"] = (
                result["surface_get_properties_available"]
                or hasattr(surface, "get_properties")
            )

            if not hasattr(surface, "get_openings"):
                continue
            try:
                openings = list(surface.get_openings())
            except Exception:
                continue
            result["sample_opening_count"] += len(openings)
            for opening in openings[:2]:
                result["opening_get_id_present"] = (
                    result["opening_get_id_present"] or hasattr(opening, "get_id")
                )
                result["opening_get_construction_present"] = (
                    result["opening_get_construction_present"]
                    or hasattr(opening, "get_construction")
                )
                result["opening_get_properties_present"] = (
                    result["opening_get_properties_present"]
                    or hasattr(opening, "get_properties")
                )

    return result


# ---------------------------------------------------------------------------
# Sonde infiltration (air exchange records)
# ---------------------------------------------------------------------------

def _probe_infiltration_api(model):
    """
    Sonde la disponibilité du setter d'infiltration sur des rooms réels.
    NE MUTE RIEN — hasattr et record.get() uniquement.

    Membres vérifiés et leurs sources :
      body.get_room_data()               → ve_api.py:1483
      room_data.get_air_exchanges()      → ve_api.py:1022
      record.get()                       → ve_api.py:59 (_record_data)
      record.set()                       → ve_api.py:1283  (hasattr uniquement)
    Clés du payload vérifiées (source : ve_api.py:1271) :
      max_flow, units_val, variation_profile, adjacent_condition_val
    """
    result = {
        "get_room_data_available": False,
        "get_air_exchanges_available": False,
        "infiltration_records_found": 0,
        "infiltration_record_set_present": False,
        "infiltration_record_get_present": False,
        "sample_record_keys": [],
        "sample_flow_keys": [],
        "errors": [],
    }

    try:
        bodies = [b for b in model.get_bodies(False) if _is_room_body(b)]
    except Exception as exc:
        result["errors"].append("get_bodies: {}".format(exc))
        return result

    for body in bodies[:8]:
        if not hasattr(body, "get_room_data"):
            continue
        result["get_room_data_available"] = True
        try:
            room_data = body.get_room_data()
        except Exception as exc:
            result["errors"].append("get_room_data: {}".format(exc))
            continue

        ok_gae, _ = _has_callable(room_data, "get_air_exchanges")
        result["get_air_exchanges_available"] = (
            result["get_air_exchanges_available"] or ok_gae
        )
        if not ok_gae:
            continue

        try:
            exchanges = list(room_data.get_air_exchanges())
        except Exception as exc:
            result["errors"].append("get_air_exchanges: {}".format(exc))
            continue

        for record in exchanges:
            try:
                data = dict(record.get())
            except Exception:
                data = {}
            # Identification des records d'infiltration par type ou nom.
            # Source du pattern : ve_api.py:1033 (exchange_key via type_val/type_str)
            type_label = str(
                data.get("type_str", data.get("type_val", "")) or ""
            ).lower().replace("_", "")
            name_label = str(data.get("name", "") or "").lower()
            if "infiltrat" not in type_label and "infiltrat" not in name_label:
                continue

            result["infiltration_records_found"] += 1
            result["infiltration_record_set_present"] = (
                result["infiltration_record_set_present"] or hasattr(record, "set")
            )
            result["infiltration_record_get_present"] = (
                result["infiltration_record_get_present"] or hasattr(record, "get")
            )
            if not result["sample_record_keys"]:
                result["sample_record_keys"] = sorted(str(k) for k in data)
                # Clés liées au débit : max_flow, units_val, max_flows (pluriel)
                # Source : ve_api.py:1271
                result["sample_flow_keys"] = [
                    k for k in result["sample_record_keys"]
                    if any(tok in k for tok in ("flow", "unit", "adjacent"))
                ]

    return result


# ---------------------------------------------------------------------------
# Sonde émission + capacité illimitée (directives)
# ---------------------------------------------------------------------------

def _probe_emission_capacity_api(model):
    """
    Sonde la disponibilité des setters apache_systems pour les directives
    radiant_fraction et unlimited_capacity.  NE MUTE RIEN.

    Membres vérifiés et leurs sources :
      body.get_room_data()               → ve_api.py:1483
      room_data.get_apache_systems()     → ve_api.py:1427
      room_data.set_apache_systems()     → ve_api.py:1089  (hasattr uniquement)

    Clés vérifiées dans le dict apache_systems (source : ve_api.py:1429-1441) :
      heating_plant_radiant_fraction
      cooling_plant_radiant_fraction
      heating_capacity_unlimited
      cooling_capacity_unlimited
      HVAC_system
      HVAC_methodology
    """
    result = {
        "get_room_data_available": False,
        "get_apache_systems_available": False,
        "set_apache_systems_present": False,
        "heating_plant_radiant_fraction_present": False,
        "cooling_plant_radiant_fraction_present": False,
        "heating_capacity_unlimited_present": False,
        "cooling_capacity_unlimited_present": False,
        "HVAC_system_present": False,
        "HVAC_methodology_present": False,
        "sample_apache_system_keys": [],
        "errors": [],
    }

    try:
        bodies = [b for b in model.get_bodies(False) if _is_room_body(b)]
    except Exception as exc:
        result["errors"].append("get_bodies: {}".format(exc))
        return result

    for body in bodies[:5]:
        if not hasattr(body, "get_room_data"):
            continue
        result["get_room_data_available"] = True
        try:
            room_data = body.get_room_data()
        except Exception as exc:
            result["errors"].append("get_room_data: {}".format(exc))
            continue

        result["set_apache_systems_present"] = (
            result["set_apache_systems_present"] or hasattr(room_data, "set_apache_systems")
        )
        ok_gas, _ = _has_callable(room_data, "get_apache_systems")
        result["get_apache_systems_available"] = (
            result["get_apache_systems_available"] or ok_gas
        )
        if not ok_gas:
            continue

        try:
            sys_data = dict(room_data.get_apache_systems())
        except Exception as exc:
            result["errors"].append("get_apache_systems: {}".format(exc))
            continue

        if not result["sample_apache_system_keys"]:
            result["sample_apache_system_keys"] = sorted(str(k) for k in sys_data)

        for key, flag in (
            ("heating_plant_radiant_fraction", "heating_plant_radiant_fraction_present"),
            ("cooling_plant_radiant_fraction", "cooling_plant_radiant_fraction_present"),
            ("heating_capacity_unlimited", "heating_capacity_unlimited_present"),
            ("cooling_capacity_unlimited", "cooling_capacity_unlimited_present"),
            ("HVAC_system", "HVAC_system_present"),
            ("HVAC_methodology", "HVAC_methodology_present"),
        ):
            if key in sys_data:
                result[flag] = True

    return result


# ---------------------------------------------------------------------------
# Sonde génération (HVAC system — famille la plus incertaine)
# ---------------------------------------------------------------------------

def _probe_generation_api(iesve, project, model):
    """
    Sonde la disponibilité des setters pour le swap de génération (PAC + SCOP/EER).
    NE MUTE RIEN.

    Membres confirmés dans le dépôt :
      project.apache_systems()           → Run_VE_SIA3802_Reference_Extraction_Probe.py:82

    ⚠ À VÉRIFIER API (non documentés dans les modules existants) :
      - Setter COP/SCOP/EER sur VEApacheSystem
      - Méthode pour changer le type de générateur (PAC vs chaudière)
      - project.create_apache_system()   → ve_mutation_policy_probe.py:278
        (confirmé comme hasattr-probed, signature inconnue)
    """
    result = {
        "apache_systems_project_callable": False,
        "system_count": 0,
        "create_apache_system_present": False,   # source : ve_mutation_policy_probe.py:278
        "HVAC_system_key_in_room": False,        # source : ve_api.py:1430
        "sample_systems": [],
        "uncertainty_note": (
            "⚠ À VÉRIFIER API : aucun setter COP/SCOP/EER sur VEApacheSystem "
            "n'est documenté dans les modules existants de ce dépôt. "
            "Le swap de génération (PAC) requiert soit (a) modifier un "
            "ApacheSystem existant, soit (b) en créer un nouveau avec "
            "project.create_apache_system() puis l'affecter aux rooms via "
            "set_apache_systems({'HVAC_system': ...}). "
            "Les deux chemins doivent être confirmés sur le projet ZOER réel."
        ),
        "errors": [],
    }

    # create_apache_system sur project (source : ve_mutation_policy_probe.py:278)
    result["create_apache_system_present"] = hasattr(project, "create_apache_system")

    # project.apache_systems() (source : Run_VE_SIA3802_Reference_Extraction_Probe.py:82)
    ok_as, _ = _has_callable(project, "apache_systems")
    result["apache_systems_project_callable"] = ok_as
    if ok_as:
        try:
            systems_list = list(project.apache_systems() or [])
            result["system_count"] = len(systems_list)
            for system in systems_list[:3]:
                sys_info = {
                    "id": str(getattr(system, "id", "") or getattr(system, "name", "") or ""),
                    "name": str(getattr(system, "name", "") or ""),
                }
                # Inventaire des membres publics : report complet, sans appel blind.
                public_callable = []
                public_attr = []
                for attr_name in sorted(dir(system)):
                    if attr_name.startswith("_"):
                        continue
                    try:
                        member = getattr(system, attr_name, None)
                        if callable(member):
                            public_callable.append(attr_name)
                        else:
                            public_attr.append(attr_name)
                    except Exception:
                        pass
                sys_info["callable_members"] = public_callable
                sys_info["non_callable_members"] = public_attr

                # Appel des getters documentés pour lire les paramètres systèmes.
                # Sources confirmées dans ce dépôt :
                #   ventilation_ncm()       → Run_VE_SIA3802_Reference_Extraction_Probe.py:85
                #   system_adjustment_ncm() → ibid. :88
                #   auxiliary_energy()      → ibid. :91
                #   heating()               → ibid. :112  (retourne un dict)
                #   cooling()               → ibid. :114  (retourne un dict)
                # ⚠ À VÉRIFIER API : get_properties() — non documenté dans les modules.
                # NOTE : set_properties() est seulement sondé via hasattr, jamais appelé.
                read_only_methods = (
                    "ventilation_ncm",
                    "system_adjustment_ncm",
                    "auxiliary_energy",
                    "heating",
                    "cooling",
                    "get_properties",    # ⚠ À VÉRIFIER API
                )
                for method_name in read_only_methods:
                    if not hasattr(system, method_name):
                        continue
                    try:
                        val = getattr(system, method_name)
                        if callable(val):
                            try:
                                returned = val()
                                sys_info[method_name + "_result"] = _jsonable(returned)
                            except Exception as exc:
                                sys_info[method_name + "_error"] = str(exc)
                    except Exception:
                        pass

                # Setters : hasattr uniquement, JAMAIS appelés (dry-run strict).
                # ⚠ À VÉRIFIER API : set_properties(), set_heating(), set_cooling()
                for setter_name in ("set_properties", "set_heating", "set_cooling"):
                    sys_info["setter_{}_present".format(setter_name)] = hasattr(
                        system, setter_name
                    )
                result["sample_systems"].append(sys_info)
        except Exception as exc:
            result["errors"].append("project.apache_systems(): {}".format(exc))

    # Vérification que HVAC_system key est présente dans room_data.get_apache_systems()
    # (clé setter confirmée : ve_api.py:1430, utilisée pour set_apache_systems)
    try:
        bodies = [b for b in model.get_bodies(False) if _is_room_body(b)]
        for body in bodies[:2]:
            if not hasattr(body, "get_room_data"):
                continue
            try:
                room_data = body.get_room_data()
                if hasattr(room_data, "get_apache_systems"):
                    sys_data = dict(room_data.get_apache_systems())
                    if "HVAC_system" in sys_data:
                        result["HVAC_system_key_in_room"] = True
                    break
            except Exception:
                pass
    except Exception:
        pass

    return result


# ---------------------------------------------------------------------------
# Logique de verdict par substitution
# ---------------------------------------------------------------------------

# Familles dont le scope est un ID de construction (ConstructionBinder)
_CONSTRUCTION_ELEMENT_TYPES = frozenset({"wall", "roof", "floor", "opening"})

# Familles qui n'ont pas de construction à résoudre
_NON_CONSTRUCTION_ELEMENT_TYPES = frozenset({
    "infiltration",
    "emission",
    "capacity",
    "cooling_generator",
    "heating_generator",
    "ventilation",
    "unclassified",
})


def _derive_verdict(element_type, construction_probes, body_surface_api):
    """
    Dérive le verdict MUTABLE/NO_SETTER/NO_CAPABILITY/UNRESOLVED
    à partir des résultats de sonde de construction et des API corps/surfaces.

    Pour atteindre MUTABLE :
      - La construction doit être résolue (RESOLVED)
      - get_properties() doit être disponible
      - Pour opaques : body.get_surfaces() + body.assign_construction disponibles
        + surface.get_constructions() pour readback
      - Pour ouvertures : body.assign_construction_to_opening
        + opening.get_construction() pour readback
    Note : la CRÉATION de la construction de référence (create_construction)
    est une capacité CDB globale vérifiée séparément, pas par substitution.
    """
    if not construction_probes:
        return VERDICT_UNRESOLVED

    # Vérifier que toutes les constructions du scope sont résolues
    for cp in construction_probes:
        if cp.get("resolution_status") != "RESOLVED":
            return VERDICT_UNRESOLVED

    # Vérifier get_properties()
    for cp in construction_probes:
        if not cp.get("getter_get_properties", {}).get("available"):
            return VERDICT_NO_CAPABILITY

    is_opening = (element_type == "opening")

    if not is_opening:
        # Surfaces opaques : get_surfaces + assign_construction (hasattr)
        if not body_surface_api.get("body_get_surfaces_available"):
            return VERDICT_NO_CAPABILITY
        if not body_surface_api.get("body_assign_construction_present"):
            return VERDICT_NO_SETTER
        # Readback : surface.get_constructions()
        if not body_surface_api.get("surface_get_constructions_available"):
            return VERDICT_NO_CAPABILITY
    else:
        # Ouvertures : assign_construction_to_opening (hasattr)
        if not body_surface_api.get("body_assign_construction_to_opening_present"):
            return VERDICT_NO_SETTER
        # Readback : opening.get_construction()
        if not body_surface_api.get("opening_get_construction_present"):
            return VERDICT_NO_CAPABILITY

    return VERDICT_MUTABLE


# ---------------------------------------------------------------------------
# Synthèse par famille
# ---------------------------------------------------------------------------

def _worst_verdict(verdicts):
    """Retourne le verdict le plus défavorable de la liste."""
    priority = {
        VERDICT_UNRESOLVED: 0,
        VERDICT_NO_CAPABILITY: 1,
        VERDICT_NO_SETTER: 2,
        VERDICT_UNCERTAIN: 3,
        VERDICT_MUTABLE: 4,
    }
    if not verdicts:
        return VERDICT_UNRESOLVED
    return min(verdicts, key=lambda v: priority.get(v, -1))


def _build_family_summary(
    substitution_probes,
    infiltration_probe,
    emission_capacity_probe,
    generation_probe,
    cdb_caps,
):
    """Agrège les verdicts par famille pour la console et le JSON."""
    families = {}

    # Famille 1 : enveloppe opaque (mur, toit, plancher)
    opaque_probes = [
        p for p in substitution_probes
        if p.get("element_type") in ("wall", "roof", "floor")
    ]
    if opaque_probes:
        opaque_verdicts = [p.get("verdict", VERDICT_UNRESOLVED) for p in opaque_probes]
        families["1_opaque_envelope (wall/roof/floor U-value)"] = {
            "substitution_count": len(opaque_probes),
            "verdict": _worst_verdict(opaque_verdicts),
            "create_construction_available": cdb_caps.get(
                "create_construction", {}
            ).get("available"),
            "note": (
                "La mutation cible l'AFFECTATION d'une construction de référence "
                "créée dans la CDB (create_construction + assign_construction), "
                "pas la modification de la construction projet existante."
            ),
        }

    # Famille 2 : vitrage (ouvertures)
    glazing_probes = [
        p for p in substitution_probes
        if p.get("element_type") == "opening"
    ]
    if glazing_probes:
        glazing_verdicts = [p.get("verdict", VERDICT_UNRESOLVED) for p in glazing_probes]
        families["2_glazing (window_u / frame_fraction / g_value / τ_v)"] = {
            "substitution_count": len(glazing_probes),
            "verdict": _worst_verdict(glazing_verdicts),
            "create_construction_glazed_available": cdb_caps.get(
                "construction_class_glazed", {}
            ).get("available"),
            "assign_construction_to_opening_present": True,  # confirmé ve_api.py:790
        }

    # Famille 3 : infiltration
    inf_records = infiltration_probe.get("infiltration_records_found", 0)
    inf_set = infiltration_probe.get("infiltration_record_set_present", False)
    inf_get_ae = infiltration_probe.get("get_air_exchanges_available", False)
    if not inf_get_ae:
        inf_verdict = VERDICT_NO_CAPABILITY
    elif inf_records == 0:
        # Aucun record d'infiltration trouvé dans l'échantillon.
        # Peut indiquer un projet sans infiltration explicite ou un mapping de type différent.
        inf_verdict = VERDICT_NO_CAPABILITY
    elif not inf_set:
        inf_verdict = VERDICT_NO_SETTER
    else:
        inf_verdict = VERDICT_MUTABLE
    families["3_infiltration (building q50)"] = {
        "verdict": inf_verdict,
        "records_found_in_sample": inf_records,
        "get_air_exchanges_available": inf_get_ae,
        "record_set_present": inf_set,
        "sample_record_keys": infiltration_probe.get("sample_record_keys", []),
        "sample_flow_keys": infiltration_probe.get("sample_flow_keys", []),
    }

    # Famille 4 : génération refroidissement
    gen_cooling = [
        p for p in substitution_probes
        if p.get("element_type") == "cooling_generator"
    ]
    families["4_cooling_generation (EER reference)"] = {
        "verdict": VERDICT_UNCERTAIN,
        "substitution_count": len(gen_cooling),
        "apache_systems_callable": generation_probe.get("apache_systems_project_callable"),
        "system_count": generation_probe.get("system_count", 0),
        "HVAC_system_key_in_room": generation_probe.get("HVAC_system_key_in_room"),
        "create_apache_system_present": generation_probe.get("create_apache_system_present"),
        "note": generation_probe.get("uncertainty_note", ""),
    }

    # Famille 5 : génération chauffage
    gen_heating = [
        p for p in substitution_probes
        if p.get("element_type") == "heating_generator"
    ]
    families["5_heating_generation (SCOP / PAC reference)"] = {
        "verdict": VERDICT_UNCERTAIN,
        "substitution_count": len(gen_heating),
        "apache_systems_callable": generation_probe.get("apache_systems_project_callable"),
        "system_count": generation_probe.get("system_count", 0),
        "note": generation_probe.get("uncertainty_note", ""),
    }

    # Famille 6 : émission (directive — radiant_fraction = 0)
    em_gas = emission_capacity_probe.get("get_apache_systems_available", False)
    em_set = emission_capacity_probe.get("set_apache_systems_present", False)
    em_rf_h = emission_capacity_probe.get("heating_plant_radiant_fraction_present", False)
    em_rf_c = emission_capacity_probe.get("cooling_plant_radiant_fraction_present", False)
    if not em_gas:
        em_verdict = VERDICT_NO_CAPABILITY
    elif not em_set:
        em_verdict = VERDICT_NO_SETTER
    elif not em_rf_h:
        em_verdict = VERDICT_NO_CAPABILITY
    else:
        em_verdict = VERDICT_MUTABLE
    families["6_emission_directive (radiant_fraction = 0)"] = {
        "verdict": em_verdict,
        "get_apache_systems_available": em_gas,
        "set_apache_systems_present": em_set,
        "heating_plant_radiant_fraction_key": em_rf_h,
        "cooling_plant_radiant_fraction_key": em_rf_c,
        "source_keys": "ve_api.py:1439-1440",
    }

    # Famille 7 : capacité illimitée (directive)
    cap_set = emission_capacity_probe.get("set_apache_systems_present", False)
    cap_h = emission_capacity_probe.get("heating_capacity_unlimited_present", False)
    cap_c = emission_capacity_probe.get("cooling_capacity_unlimited_present", False)
    if not em_gas:
        cap_verdict = VERDICT_NO_CAPABILITY
    elif not cap_set:
        cap_verdict = VERDICT_NO_SETTER
    elif not cap_h:
        cap_verdict = VERDICT_NO_CAPABILITY
    else:
        cap_verdict = VERDICT_MUTABLE
    families["7_capacity_directive (unlimited heating/cooling)"] = {
        "verdict": cap_verdict,
        "set_apache_systems_present": cap_set,
        "heating_capacity_unlimited_key": cap_h,
        "cooling_capacity_unlimited_key": cap_c,
        "source_keys": "ve_api.py:1433-1434",
    }

    return families


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------

def main():
    """Lance la sonde et écrit le rapport JSON à côté du projet VE."""
    import importlib

    try:
        iesve = importlib.import_module("iesve")
    except Exception as exc:
        print("Ce script doit s'exécuter depuis IESVE VEScripts : %s" % exc)
        return

    # --- Imports swiss_sia APRÈS la purge en tête de fichier ---
    from swiss_sia.data_extractor import VEDataExtractor
    from swiss_sia.model_analyzer import ModelAnalyzer
    from swiss_sia.reference_project import (
        build_reference_project_specification,
        REFERENCE_DIRECTIVE,
        STANDARD_USAGE_INPUT,
    )
    from swiss_sia.reference_model.ve_construction_binder import ConstructionBinder

    project = iesve.VEProject.get_current_project()
    project_path = str(getattr(project, "path", "") or "")
    model = project.models[0] if getattr(project, "models", None) else None

    print("=" * 60)
    print("SIA 380/2 Reference-Build Capability Probe")
    print("Dry-run strict — aucune mutation du modèle VE")
    print("Projet : %s" % project_path)
    print("=" * 60)

    # --- Extraction du modèle et construction de la spec ---
    print("\n[1/7] Extraction du modèle et construction de la spec SIA 380/2...")
    extractor = VEDataExtractor(project)
    analyzer = ModelAnalyzer(extractor)
    rooms = analyzer.analyze_all_rooms()
    spec = build_reference_project_specification(rooms, analyzer)
    print("      Spec : %d substitutions, %d bloqueurs, statut : %s"
          % (len(spec.substitutions), len(spec.blockers), spec.status))

    # --- CDB ---
    print("[2/7] Résolution du projet CDB...")
    cdb_project = _resolve_cdb_project(iesve)
    cdb_caps = _probe_cdb_capabilities(iesve, cdb_project)
    binder = (
        ConstructionBinder(iesve_module=iesve, cdb_project=cdb_project)
        if cdb_project else None
    )
    print("      CDB disponible : %s" % cdb_caps["cdb_project_available"])
    print("      create_construction : %s"
          % cdb_caps.get("create_construction", {}).get("available"))

    # --- API corps/surfaces/ouvertures ---
    print("[3/7] Sonde API corps/surfaces/ouvertures...")
    body_surface_api = _probe_body_surface_api(model) if model else {}
    print("      get_surfaces disponible : %s"
          % body_surface_api.get("body_get_surfaces_available"))
    print("      assign_construction présent : %s"
          % body_surface_api.get("body_assign_construction_present"))
    print("      assign_construction_to_opening présent : %s"
          % body_surface_api.get("body_assign_construction_to_opening_present"))

    # --- Sonde par substitution (familles construction-based seulement) ---
    print("[4/7] Sonde par substitution (construction-based)...")
    substitution_probes = []
    skipped_directives = 0
    skipped_usage = 0
    skipped_non_construction = 0

    for sub in spec.substitutions:
        # Exclusion des directives et inputs identiques projet/référence
        if sub.status == REFERENCE_DIRECTIVE:
            skipped_directives += 1
            continue
        if sub.status == STANDARD_USAGE_INPUT:
            skipped_usage += 1
            continue

        sub_probe = {
            "parameter": sub.parameter,
            "scope": sub.scope,
            "element_type": sub.element_type,
            "project_value": sub.project_value,
            "reference_value": sub.reference_value,
            "reference_target_value": sub.reference_target_value,
            "unit": sub.unit,
            "spec_status": sub.status,
        }

        if sub.element_type not in _CONSTRUCTION_ELEMENT_TYPES:
            # Génération, ventilation, etc. — sondés dans des sections dédiées
            skipped_non_construction += 1
            sub_probe["verdict"] = "SEE_DEDICATED_FAMILY_PROBE"
            sub_probe["note"] = (
                "Element type '{}' n'utilise pas ConstructionBinder. "
                "Voir les sections génération/infiltration/émission."
            ).format(sub.element_type)
            substitution_probes.append(sub_probe)
            continue

        # Extraction des IDs de construction depuis le scope (virgule-séparés)
        scope_ids = [s.strip() for s in str(sub.scope or "").split(",") if s.strip()]

        if not scope_ids:
            sub_probe["verdict"] = VERDICT_UNRESOLVED
            sub_probe["error"] = "Scope vide — aucun ID de construction à résoudre"
            substitution_probes.append(sub_probe)
            continue

        if binder is None:
            sub_probe["verdict"] = VERDICT_UNRESOLVED
            sub_probe["error"] = "CDB non disponible — ConstructionBinder inopérant"
            sub_probe["construction_probes"] = []
            substitution_probes.append(sub_probe)
            continue

        # Résolution de chaque ID du scope
        construction_probes = []
        for cid in scope_ids:
            cp = _probe_construction(binder, cid)
            construction_probes.append(cp)

        sub_probe["construction_probes"] = construction_probes
        sub_probe["verdict"] = _derive_verdict(
            sub.element_type, construction_probes, body_surface_api
        )
        substitution_probes.append(sub_probe)

    print("      Substitutions sondées (construction) : %d"
          % sum(1 for p in substitution_probes
                if p.get("verdict") not in (None, "SEE_DEDICATED_FAMILY_PROBE")))
    print("      Directives exclues : %d | Usage standard exclus : %d"
          % (skipped_directives, skipped_usage))

    # --- Infiltration ---
    print("[5/7] Sonde infiltration (air exchange records)...")
    infiltration_probe = _probe_infiltration_api(model) if model else {}
    print("      Records infiltration trouvés : %d"
          % infiltration_probe.get("infiltration_records_found", 0))
    print("      record.set() présent : %s"
          % infiltration_probe.get("infiltration_record_set_present"))

    # --- Émission + capacité ---
    print("[6/7] Sonde émission + capacité illimitée (directives)...")
    emission_capacity_probe = _probe_emission_capacity_api(model) if model else {}
    print("      get_apache_systems disponible : %s"
          % emission_capacity_probe.get("get_apache_systems_available"))
    print("      set_apache_systems présent : %s"
          % emission_capacity_probe.get("set_apache_systems_present"))
    print("      heating_plant_radiant_fraction key : %s"
          % emission_capacity_probe.get("heating_plant_radiant_fraction_present"))
    print("      heating_capacity_unlimited key : %s"
          % emission_capacity_probe.get("heating_capacity_unlimited_present"))

    # --- Génération ---
    print("[7/7] Sonde génération (HVAC — famille la plus incertaine)...")
    generation_probe = _probe_generation_api(iesve, project, model) if model else {}
    print("      project.apache_systems() callable : %s"
          % generation_probe.get("apache_systems_project_callable"))
    print("      Systèmes trouvés : %d"
          % generation_probe.get("system_count", 0))
    print("      ⚠ Setter COP/SCOP/EER : NON DOCUMENTÉ dans les modules existants")

    # --- Synthèse par famille ---
    family_summary = _build_family_summary(
        substitution_probes,
        infiltration_probe,
        emission_capacity_probe,
        generation_probe,
        cdb_caps,
    )

    # --- Rapport final ---
    report = {
        "schema_version": "1.0",
        "probe": "sia3802_reference_build_capability",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dry_run_strict": True,
        "no_mutation_performed": True,
        "project_path": project_path,
        "spec_summary": {
            "status": spec.status,
            "substitution_count": len(spec.substitutions),
            "blocker_count": len(spec.blockers),
            "blockers": list(spec.blockers),
            "implemented_families": list(spec.implemented_input_families),
            "missing_families": list(spec.missing_input_families),
        },
        "cdb_capabilities": cdb_caps,
        "body_surface_api": body_surface_api,
        "substitution_probes": substitution_probes,
        "infiltration_probe": infiltration_probe,
        "emission_capacity_probe": emission_capacity_probe,
        "generation_probe": generation_probe,
        "family_summary": family_summary,
        "api_uncertainty_points": [
            "generation_swap: les getters heating()/cooling() sur VEApacheSystem sont "
            "confirmés (Run_VE_SIA3802_Reference_Extraction_Probe.py:112-114) mais aucun "
            "setter COP/SCOP/EER n'est documenté dans les modules existants. "
            "Le swap de type de générateur (PAC) via set_apache_systems({'HVAC_system': ...}) "
            "ou create_apache_system() nécessite vérification sur le projet ZOER réel.",
            "opaque_u_value_readback: le nom exact du champ U-value dans "
            "VECdbConstruction.get_properties() n'est pas dans les modules existants "
            "— la sonde tente de le découvrir.",
            "infiltration_scope: l'identification des records par type_str='Infiltration' "
            "dépend de la convention de nommage du projet ; un projet sans infiltration "
            "explicite peut retourner 0 records alors que la capacité est présente.",
            "create_construction_signature: la signature exacte de "
            "cdb_project.create_construction() n'est pas documentée — requiert "
            "une inspection sur le projet ZOER réel avant toute mutation.",
        ],
        "compliance_claim": "NOT_APPLICABLE — sonde de capacité uniquement",
    }

    # --- Affichage console du résumé ---
    print("\n" + "=" * 60)
    print("RÉSUMÉ PAR FAMILLE")
    print("=" * 60)
    print("%-48s %s" % ("Famille", "Verdict"))
    print("-" * 60)
    for family_name, family_info in sorted(family_summary.items()):
        verdict = family_info.get("verdict", "?")
        print("%-48s %s" % (family_name, verdict))

    # --- Écriture JSON ---
    out_dir = Path(project_path).parent if project_path else PROJECT_ROOT
    out_path = out_dir / "sia3802_reference_build_capability.json"
    try:
        out_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print("\nRapport JSON écrit : %s" % out_path)
    except Exception as exc:
        print("\nImpossible d'écrire le JSON (%s) — dump console :" % exc)
        print(json.dumps(report, ensure_ascii=False, indent=2)[:4000])

    print("\nSonde terminée. Aucune mutation effectuée.")


if __name__ == "__main__":
    main()
