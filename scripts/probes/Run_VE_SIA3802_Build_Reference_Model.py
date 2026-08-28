"""Constructeur du projet de référence SIA 380/2 — mode sûr et incrémental.

GARDE PRINCIPAL : ce script refuse de muter un projet dont le chemin ne
contient pas _TEST, _COPY ou _DISPOSABLE.  Il ne touche JAMAIS l'original.

PRINCIPE : applique les substitutions de la spec SIA 380/2 dans l'ordre de
confiance décroissante, chacune avec capability-check + readback immédiat.
Toute famille dont le readback échoue est marquée FAILED_READBACK et le
script continue les autres.  Aucun lancement d'ApacheSim.

Ordre des mutations :
  (a) Infiltration       → air_exchange record.set(max_flow = 0.15 m³/h/m²)
  (b) Émission           → set_apache_systems(radiant_fraction = 0)
  (c) Capacité illimitée → set_apache_systems(unlimited = True)
  (d) Génération         → set_heating(SCoP) / set_cooling(SEER)
  (e) Enveloppe opaque   → create_construction + assign_construction
  (f) Vitrage            → create_construction + assign_construction_to_opening
  (g) Frame fraction     → opening.set_properties (⚠ si setter disponible)

Sources API confirmées dans ce dépôt :
  ve_api.py, ve_asset_provisioner.py, ve_construction_binder.py,
  scripts/construire_test4_dans_ve.py, ve_field_policy.py
⚠ À VÉRIFIER API : frame fraction setter sur opening, propriétés exactes
  de get_properties() sur VECdbConstruction.

Écrit : <project_parent>/sia3802_reference_build_receipt.json
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime
from pathlib import Path


# Placer la racine du dépôt EN PREMIER sur sys.path (source : Run_VE_SIA4010_Construire_Test4.py:65-67)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
while str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Phase 0 : purge du cache de modules VE (obligatoire — VE cache entre runs)
# Source du patron : Run_VE_SIA4010_Construire_Test4.py (lignes 57-67)
# Le même interpréteur est réutilisé d'un click Run au suivant ; des modules
# chargés depuis un autre dépôt peuvent rester en cache.  On les expurge
# avant tout import de production.
# ---------------------------------------------------------------------------
_PAQUETS_A_PURGER = ("scripts", "ve_adapter", "engine", "ui", "swiss_sia")
_PREFIXES_A_PURGER = _PAQUETS_A_PURGER + tuple(_p + "." for _p in _PAQUETS_A_PURGER)
for _mod in tuple(sys.modules):
    if _mod in _PAQUETS_A_PURGER or _mod.startswith(_PREFIXES_A_PURGER):
        del sys.modules[_mod]


# ===========================================================================
# Constantes
# ===========================================================================

SCHEMA_VERSION = "1.0"
OPERATION = "SIA3802_BUILD_REFERENCE_MODEL"

# Résistances surfaciques ISO 6946:2017, tableau 1
_RSI_WALL = 0.13    # m²K/W — flux horizontal (murs)
_RSO_WALL = 0.04
_RSI_ROOF = 0.10    # m²K/W — flux ascendant (toits)
_RSO_ROOF = 0.04
_RSI_FLOOR = 0.17   # m²K/W — flux descendant (planchers)
_RSO_FLOOR = 0.04
_RSI_GLAZ = 0.13    # m²K/W — ISO 15099 pour vitrages verticaux
_RSO_GLAZ = 0.04

# Matériau de référence : laine minérale (source : DTU / EN ISO 10211)
_INSUL_CONDUCTIVITY = 0.04     # W/(mK)
_INSUL_DENSITY = 50.0          # kg/m³
_INSUL_SPECIFIC_HEAT = 840.0   # J/(kgK)

# Conductivité du verre (EN 673)
_GLASS_CONDUCTIVITY = 1.0      # W/(mK)
_GLASS_THICKNESS = 0.004       # m (4 mm pane)

# Tolérance float32 VE (source : ve_field_policy.py:47-48)
_REL_TOL = 1.0e-5   # légèrement relâché pour les U calculés par couche
_ABS_TOL = 1.0e-6


# ===========================================================================
# Utilitaires
# ===========================================================================

def _jsonable(value, depth=0):
    """Convertit les types VE en valeurs JSON sûres."""
    if depth > 4:
        return repr(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v, depth + 1) for k, v in list(value.items())[:200]}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v, depth + 1) for v in list(value)[:200]]
    enum_val = getattr(value, "value", None)
    if enum_val is not None and enum_val is not value:
        return {"name": str(value), "value": _jsonable(enum_val, depth + 1)}
    return str(value)


def _values_close(a, b):
    """Comparaison float32 après round-trip VE (source : ve_field_policy.py:148-175)."""
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=_REL_TOL, abs_tol=_ABS_TOL)
    return a == b


def _ok(target, actual, label):
    """Retourne (bool, dict) pour un readback simple."""
    if _values_close(target, actual):
        return True, {"field": label, "target": target, "readback": actual, "ok": True}
    return False, {
        "field": label,
        "target": target,
        "readback": actual,
        "ok": False,
        "delta": (actual - target) if isinstance(target, (int, float))
                  and isinstance(actual, (int, float)) else None,
    }


def _is_room_body(body):
    """Filtre les corps de type room (source : ve_api.py:532)."""
    try:
        t = str(getattr(body, "type", "") or "").lower().replace("_", "").replace(" ", "")
        return t.endswith("room")
    except Exception:
        return False


def _resolve_enum(iesve, paths, member_name):
    """
    Résout un membre d'enum VE depuis plusieurs chemins connus.
    Source : ve_asset_provisioner.py — même logique, version autonome.
    """
    for path in paths:
        container = iesve
        for part in path.split("."):
            container = getattr(container, part, None)
            if container is None:
                break
        if container is not None:
            member = getattr(container, member_name, None)
            if member is not None:
                return member
    return None


def _construction_id(construction):
    """Extrait l'ID depuis un objet VECdbConstruction (source : ve_api.py:689-701)."""
    if isinstance(construction, str):
        return construction
    val = getattr(construction, "id", None)
    if val:
        return str(val)
    if hasattr(construction, "get_properties"):
        try:
            props = dict(construction.get_properties())
            val = props.get("id", props.get("construction_id", ""))
            if val:
                return str(val)
        except Exception:
            pass
    return str(construction)


# ===========================================================================
# Garde disposable
# ===========================================================================

def _assert_disposable(project_path: str, iesve_module):
    """
    Refuse toute mutation si le projet n'est pas explicitement jetable.
    Source : swiss_sia/compliance_hub.py:225 (is_disposable_project)
    """
    # Importer is_disposable_project depuis le module de production
    from swiss_sia.compliance_hub import is_disposable_project
    if not is_disposable_project(project_path):
        raise RuntimeError(
            "REFUS DE MUTATION : le projet actif n'est pas une copie jetable.\n"
            "Son chemin : {}\n"
            "Renommez la copie en ajoutant _TEST, _COPY ou _DISPOSABLE "
            "à son nom, puis rouvrez-la dans VE avant de relancer ce script.\n"
            "Le projet original ZOER n'a PAS été modifié.".format(project_path)
        )
    print("Garde disposable : OK — {}".format(project_path))


# ===========================================================================
# CDB helpers
# ===========================================================================

def _collect_cdb_project_objects(value, depth=0, seen=None):
    """
    Parcours récursif du retour de get_projects() pour trouver les VECdbProject.

    PIÈGE DOCUMENTÉ (source : engine/tests/test_run_test1_preflight.py:168-243) :
    get_projects() retourne un dict INDEXÉ PAR DES ENUMS (iesve.project_types.*),
    pas par des chaînes ni des entiers. Un table.get('project') échoue
    silencieusement.  Un projects[0] sur ce dict retourne la clé 0 → KeyError.

    Solution : parcourir les VALUES du dict sans supposer la forme des clés,
    et identifier les projets CDB par la présence de get_construction().

    Source : swiss_sia/data_extractor.py:728-757 (méthode de production,
    logique copiée pour autonomie dans ce script Run).
    """
    if seen is None:
        seen = set()
    projects = []
    if value is None or depth > 6:
        return projects
    marker = id(value)
    if marker in seen:
        return projects
    seen.add(marker)
    if hasattr(value, "get_construction"):
        projects.append(value)
        return projects
    if isinstance(value, dict):
        for nested in value.values():
            projects.extend(_collect_cdb_project_objects(nested, depth + 1, seen))
        return projects
    if isinstance(value, (list, tuple, set)):
        for nested in value:
            projects.extend(_collect_cdb_project_objects(nested, depth + 1, seen))
    return projects


def _cdb_project(iesve):
    """
    Retourne le premier projet CDB courant.
    Source clé : ve_api.py:628, data_extractor.py:654-670, et le piège
    documenté dans test_run_test1_preflight.py:235-243 (enum keys).
    """
    database = iesve.VECdbDatabase.get_current_database()
    raw = database.get_projects()
    found = _collect_cdb_project_objects(raw)
    if not found:
        raise RuntimeError(
            "Aucun projet CDB courant disponible (get_projects() a renvoyé "
            "{} — vérifier que VE a un projet ouvert)".format(type(raw).__name__)
        )
    return found[0]


def _get_construction_obj(cdb_proj, cid, cc_enum):
    """
    Résout une construction depuis son ID, tolère les deux signatures.
    Source : ve_api.py:676, ve_asset_provisioner.py:1590-1598
    """
    for args in ((cid, cc_enum), (cid,)):
        try:
            obj = cdb_proj.get_construction(*args)
            if obj is not None:
                return obj
        except Exception:
            continue
    return None


def _get_opaque_class(iesve):
    return _resolve_enum(
        iesve,
        ["VECdbProject.construction_class", "construction_class"],
        "opaque",
    )


def _get_glazed_class(iesve):
    return _resolve_enum(
        iesve,
        ["VECdbProject.construction_class", "construction_class"],
        "glazed",
    )


def _get_element_category(iesve, name):
    """name = "wall" | "roof" | "ground_floor" | "ext_glazing"."""
    return _resolve_enum(
        iesve,
        ["VECdbProject.element_categories", "element_categories"],
        name,
    )


def _get_material_category(iesve, name):
    """name = "other" | "glass" | "all"."""
    return _resolve_enum(
        iesve,
        ["VECdbProject.material_categories", "material_categories"],
        name,
    )


# ===========================================================================
# Pre-flight : vérification des capacités avant toute mutation
# ===========================================================================

def _preflight(iesve, project, cdb_proj, model):
    """
    Vérifie que tous les membres API requis sont disponibles.
    Retourne (ok: bool, rapport: dict).
    Aucune mutation ici.
    """
    checks = {}

    def chk(label, condition, note=""):
        checks[label] = {"ok": bool(condition), "note": note}
        return bool(condition)

    # CDB base
    chk("cdb_project", cdb_proj is not None, "VECdbDatabase.get_current_database().get_projects()")
    chk("create_material", hasattr(cdb_proj, "create_material"),
        "source: ve_mutation_policy_probe.py:300")
    chk("create_construction", hasattr(cdb_proj, "create_construction"),
        "source: ve_asset_provisioner.py:1681")
    chk("get_construction_ids", hasattr(cdb_proj, "get_construction_ids"),
        "source: ve_asset_provisioner.py:1582")

    # Enums
    chk("element_categories.wall",
        _get_element_category(iesve, "wall") is not None,
        "source: Run_VE_Reference_Model_Capability_Probe.py:116")
    chk("element_categories.roof",
        _get_element_category(iesve, "roof") is not None)
    chk("element_categories.ground_floor",
        _get_element_category(iesve, "ground_floor") is not None)
    chk("element_categories.ext_glazing",
        _get_element_category(iesve, "ext_glazing") is not None)
    chk("material_categories.other",
        _get_material_category(iesve, "other") is not None)
    chk("material_categories.glass",
        _get_material_category(iesve, "glass") is not None)
    chk("construction_class.opaque", _get_opaque_class(iesve) is not None,
        "source: ve_api.py:642")
    chk("construction_class.glazed", _get_glazed_class(iesve) is not None,
        "source: Run_VE_Inspect_Reference_Constructions.py:59")

    # Bodies
    chk("model.get_bodies", hasattr(model, "get_bodies"),
        "source: ve_api.py:543")
    if cdb_proj:
        # Test une construction quelconque pour confirmer get_layers
        opaque_cls = _get_opaque_class(iesve)
        if opaque_cls and hasattr(cdb_proj, "get_construction_ids"):
            try:
                ids = list(cdb_proj.get_construction_ids(opaque_cls))[:1]
                if ids:
                    obj = _get_construction_obj(cdb_proj, ids[0], opaque_cls)
                    chk("construction.get_layers", hasattr(obj, "get_layers"),
                        "source: ve_api.py:748")
                    chk("construction.set_const_class", hasattr(obj, "set_const_class"),
                        "source: ve_asset_provisioner.py:1682")
                    chk("construction.add_layer", hasattr(obj, "add_layer"),
                        "source: ve_asset_provisioner.py:1716")
                    chk("construction.delete_layer", hasattr(obj, "delete_layer"),
                        "source: ve_asset_provisioner.py:1698")
            except Exception as exc:
                checks["construction_sample"] = {"ok": False, "note": str(exc)}

    # Rooms sample
    try:
        all_bodies = list(model.get_bodies(False))
        rooms = [b for b in all_bodies if _is_room_body(b)]
        if rooms:
            body = rooms[0]
            chk("body.assign_construction",
                hasattr(body, "assign_construction"),
                "source: ve_api.py:764")
            chk("body.assign_construction_to_opening",
                hasattr(body, "assign_construction_to_opening"),
                "source: ve_api.py:790")
            chk("body.get_surfaces", hasattr(body, "get_surfaces"),
                "source: ve_api.py:762")
            if hasattr(body, "get_room_data"):
                rd = body.get_room_data()
                chk("room_data.get_air_exchanges",
                    hasattr(rd, "get_air_exchanges"),
                    "source: ve_api.py:1022")
                chk("room_data.set_apache_systems",
                    hasattr(rd, "set_apache_systems"),
                    "source: ve_api.py:1089")
                chk("room_data.get_apache_systems",
                    hasattr(rd, "get_apache_systems"),
                    "source: ve_api.py:1427")
    except Exception as exc:
        checks["rooms_sample"] = {"ok": False, "note": str(exc)}

    # Generation
    chk("project.apache_systems",
        hasattr(project, "apache_systems"),
        "source: Run_VE_SIA3802_Reference_Extraction_Probe.py:82")
    systems_ok = False
    if hasattr(project, "apache_systems"):
        try:
            systems = list(project.apache_systems() or [])
            if systems:
                s = systems[0]
                chk("system.set_heating", hasattr(s, "set_heating"),
                    "source: scripts/construire_test4_dans_ve.py:CLES_DES_SETTERS")
                chk("system.set_cooling", hasattr(s, "set_cooling"),
                    "source: scripts/construire_test4_dans_ve.py:CLES_DES_SETTERS")
                chk("system.heating", hasattr(s, "heating"),
                    "source: Run_VE_SIA3802_Reference_Extraction_Probe.py:112")
                chk("system.cooling", hasattr(s, "cooling"),
                    "source: Run_VE_SIA3802_Reference_Extraction_Probe.py:114")
                systems_ok = True
        except Exception as exc:
            checks["apache_systems_sample"] = {"ok": False, "note": str(exc)}
    if not systems_ok:
        checks.setdefault("system.set_heating", {"ok": False, "note": "no systems found"})
        checks.setdefault("system.set_cooling", {"ok": False, "note": "no systems found"})

    failed = [k for k, v in checks.items() if not v["ok"]]
    ok = len(failed) == 0
    return ok, {"checks": checks, "failed": failed, "ok": ok}


# ===========================================================================
# Applicateur (a) : Infiltration
# ===========================================================================

def _apply_infiltration(spec, model):
    """
    Substitution : q50 → valeur de référence SIA 380/2 Table 2.
    Membre clé : room_data.get_air_exchanges() + record.set(max_flow=ref)
    Source : ve_api.py:1022,1283 ; ve_api.py:1033 (type_val/type_str)
    TRAP : si units_val n'est pas m³/(h·m²), le flux converti doit être ajusté.
    Le script applique max_flow = ref_value en conservant units_val courant et
    signale en log si les unités semblent différentes.
    """
    results = []
    # Récupérer la valeur de référence depuis la spec
    ref_sub = next(
        (s for s in spec.substitutions
         if s.parameter == "infiltration_m3_h_m2" and s.reference_value is not None),
        None,
    )
    if ref_sub is None:
        return {
            "family": "infiltration",
            "status": "SKIP",
            "reason": "Pas de substitution infiltration SUBSTITUTABLE dans la spec",
        }
    ref_value = ref_sub.reference_value  # ex : 0.15 m³/(h·m²)
    rooms_mutated = 0
    rooms_failed = 0

    try:
        all_bodies = list(model.get_bodies(False))
        rooms = [b for b in all_bodies if _is_room_body(b)]
    except Exception as exc:
        return {"family": "infiltration", "status": "PREFLIGHT_FAIL", "error": str(exc)}

    for body in rooms:
        if not hasattr(body, "get_room_data"):
            continue
        room_name = str(getattr(body, "name", "") or "")
        try:
            room_data = body.get_room_data()
            exchanges = list(room_data.get_air_exchanges())
        except Exception as exc:
            results.append({"room": room_name, "ok": False, "error": str(exc)})
            rooms_failed += 1
            continue

        for record in exchanges:
            try:
                data = dict(record.get())
            except Exception:
                data = {}
            type_label = str(
                data.get("type_str", data.get("type_val", "")) or ""
            ).lower().replace("_", "")
            name_label = str(data.get("name", "") or "").lower()
            if "infiltrat" not in type_label and "infiltrat" not in name_label:
                continue

            current_flow = data.get("max_flow")
            units_val = data.get("units_val")

            # Construire le payload minimal (source : ve_api.py:1271-1282)
            payload = {
                "max_flow": ref_value,
                "max_flow_from_template": False,
            }
            if units_val is not None:
                payload["units_val"] = units_val
                payload["units_val_from_template"] = False

            try:
                record.set(payload)
            except Exception as exc:
                results.append({
                    "room": room_name, "ok": False,
                    "mutation": "record.set", "error": str(exc),
                })
                rooms_failed += 1
                continue

            # Readback (source : ve_api.py:59 — _record_data via record.get())
            try:
                after = dict(record.get())
            except Exception as exc:
                results.append({
                    "room": room_name, "ok": False,
                    "readback": "record.get failed", "error": str(exc),
                })
                rooms_failed += 1
                continue

            rb_flow = after.get("max_flow")
            rb_ok, rb_detail = _ok(ref_value, rb_flow, "max_flow")
            results.append({
                "room": room_name,
                "ok": rb_ok,
                "target": ref_value,
                "before": current_flow,
                "readback": rb_flow,
                "units_val": units_val,
                "units_warning": (
                    "units_val inconnu — vérifier que max_flow est bien en m³/(h·m²)"
                ) if units_val is None else None,
                "readback_detail": rb_detail,
            })
            if rb_ok:
                rooms_mutated += 1
            else:
                rooms_failed += 1

    overall = "OK" if rooms_failed == 0 and rooms_mutated > 0 else (
        "PARTIAL" if rooms_mutated > 0 else "FAILED_READBACK"
    )
    return {
        "family": "infiltration",
        "status": overall,
        "reference_value": ref_value,
        "unit": "m3/(h.m2)",
        "rooms_mutated": rooms_mutated,
        "rooms_failed": rooms_failed,
        "per_room": results,
    }


# ===========================================================================
# Applicateur (b)+(c) : Émission + Capacité
# ===========================================================================

def _apply_emission_capacity(model):
    """
    (b) radiant_fraction → 0 pour tous les rooms.
    (c) capacity unlimited → True pour tous les rooms.
    Source : ve_api.py:1427,1089 ; clés ve_api.py:1429-1441.

    Payload minimal : seules les clés connues-writables sont incluses pour
    éviter de soumettre des clés display-only (ve_api.py:1067 commentaire).
    """
    results_emission = []
    results_capacity = []
    ok_em = 0
    fail_em = 0
    ok_cap = 0
    fail_cap = 0

    try:
        all_bodies = list(model.get_bodies(False))
        rooms = [b for b in all_bodies if _is_room_body(b)]
    except Exception as exc:
        err = {"family": "emission+capacity", "status": "PREFLIGHT_FAIL", "error": str(exc)}
        return err, err

    for body in rooms:
        if not hasattr(body, "get_room_data"):
            continue
        room_name = str(getattr(body, "name", "") or "")
        try:
            room_data = body.get_room_data()
            before = dict(room_data.get_apache_systems())
        except Exception as exc:
            results_emission.append({"room": room_name, "ok": False, "error": str(exc)})
            results_capacity.append({"room": room_name, "ok": False, "error": str(exc)})
            fail_em += 1
            fail_cap += 1
            continue

        # --- (b) Émission : radiant_fraction = 0 ---
        # Source : ve_api.py:1396-1425 (pattern set + readback)
        emit_payload = {}
        for key in ("heating_plant_radiant_fraction", "cooling_plant_radiant_fraction"):
            if key in before:
                emit_payload[key] = 0.0
                flag = "{}_from_template".format(key)
                if flag in before:
                    emit_payload[flag] = False

        if emit_payload:
            try:
                room_data.set_apache_systems(emit_payload)
                after_em = dict(room_data.get_apache_systems())
                h_ok, h_det = _ok(0.0, after_em.get("heating_plant_radiant_fraction"), "hrf")
                c_ok, c_det = _ok(0.0, after_em.get("cooling_plant_radiant_fraction"), "crf")
                rb_ok = h_ok and c_ok
                results_emission.append({
                    "room": room_name, "ok": rb_ok,
                    "before_hrf": before.get("heating_plant_radiant_fraction"),
                    "after_hrf": after_em.get("heating_plant_radiant_fraction"),
                    "before_crf": before.get("cooling_plant_radiant_fraction"),
                    "after_crf": after_em.get("cooling_plant_radiant_fraction"),
                })
                if rb_ok:
                    ok_em += 1
                else:
                    fail_em += 1
            except Exception as exc:
                results_emission.append({"room": room_name, "ok": False, "error": str(exc)})
                fail_em += 1
        else:
            results_emission.append({
                "room": room_name, "ok": None,
                "skip": "heating_plant_radiant_fraction absent du dict apache_systems",
            })

        # --- (c) Capacité : unlimited = True ---
        cap_payload = {}
        for key in ("heating_capacity_unlimited", "cooling_capacity_unlimited"):
            if key in before:
                cap_payload[key] = True
                flag = "{}_from_template".format(key)
                if flag in before:
                    cap_payload[flag] = False

        if cap_payload:
            try:
                # Relire le dict à jour après mutation emission
                before_cap = dict(room_data.get_apache_systems())
                room_data.set_apache_systems(cap_payload)
                after_cap = dict(room_data.get_apache_systems())
                h_ok, _ = _ok(True, after_cap.get("heating_capacity_unlimited"), "hcu")
                c_ok, _ = _ok(True, after_cap.get("cooling_capacity_unlimited"), "ccu")
                rb_ok = h_ok and c_ok
                results_capacity.append({
                    "room": room_name, "ok": rb_ok,
                    "before_hcu": before_cap.get("heating_capacity_unlimited"),
                    "after_hcu": after_cap.get("heating_capacity_unlimited"),
                    "before_ccu": before_cap.get("cooling_capacity_unlimited"),
                    "after_ccu": after_cap.get("cooling_capacity_unlimited"),
                })
                if rb_ok:
                    ok_cap += 1
                else:
                    fail_cap += 1
            except Exception as exc:
                results_capacity.append({"room": room_name, "ok": False, "error": str(exc)})
                fail_cap += 1
        else:
            results_capacity.append({
                "room": room_name, "ok": None,
                "skip": "heating_capacity_unlimited absent du dict apache_systems",
            })

    em_status = "OK" if fail_em == 0 and ok_em > 0 else (
        "PARTIAL" if ok_em > 0 else "FAILED_READBACK"
    )
    cap_status = "OK" if fail_cap == 0 and ok_cap > 0 else (
        "PARTIAL" if ok_cap > 0 else "FAILED_READBACK"
    )
    return (
        {"family": "emission", "status": em_status,
         "directive": "radiant_fraction = 0 (convective)",
         "rooms_ok": ok_em, "rooms_failed": fail_em, "per_room": results_emission},
        {"family": "capacity", "status": cap_status,
         "directive": "heating_capacity_unlimited = True, cooling_capacity_unlimited = True",
         "rooms_ok": ok_cap, "rooms_failed": fail_cap, "per_room": results_capacity},
    )


# ===========================================================================
# Applicateur (d) : Génération
# ===========================================================================

def _apply_generation(spec, project):
    """
    Substitue les paramètres de performance des systèmes HVAC.
    Source setters : scripts/construire_test4_dans_ve.py:CLES_DES_SETTERS
    TRAP documenté : set_heating() sans argument retourne None silencieusement.
    → Toujours passer un dict, même minimal.

    SCoP (VE) ↔ SCOP (SIA 380/2 Table 8) : correspondance supposée — ⚠ À VÉRIFIER.
    SEER (VE) ↔ EER (SIA 380/2 Table 5) : correspondance supposée — ⚠ À VÉRIFIER.
    """
    results = []

    # Indexer les substitutions de génération par scope système
    heating_by_scope = {
        s.scope: s for s in spec.substitutions
        if s.parameter == "heating_generation_scop" and s.reference_value is not None
    }
    cooling_by_scope = {
        s.scope: s for s in spec.substitutions
        if s.parameter == "cooling_generation_eer" and s.reference_value is not None
    }

    if not heating_by_scope and not cooling_by_scope:
        return {
            "family": "generation",
            "status": "SKIP",
            "reason": "Pas de substitution génération SUBSTITUTABLE dans la spec",
        }

    try:
        systems = list(project.apache_systems() or [])
    except Exception as exc:
        return {"family": "generation", "status": "PREFLIGHT_FAIL", "error": str(exc)}

    ok_count = 0
    fail_count = 0

    for system in systems:
        sys_id = str(getattr(system, "id", "") or getattr(system, "name", "") or "")
        sys_name = str(getattr(system, "name", "") or "")
        scope = sys_id or sys_name

        sys_result = {"system_id": sys_id, "system_name": sys_name}

        # --- Chauffage : set_heating({"SCoP": ref_scop, "is_heat_pump": True}) ---
        if scope in heating_by_scope and hasattr(system, "set_heating") and hasattr(system, "heating"):
            heat_sub = heating_by_scope[scope]
            ref_scop = heat_sub.reference_value

            try:
                before_h = dict(system.heating() or {})
            except Exception as exc:
                sys_result["heating_error"] = "heating() failed: {}".format(exc)
                fail_count += 1
                results.append(sys_result)
                continue

            # Mise à jour ciblée : ne modifier que SCoP et is_heat_pump
            # Source : CLES_DES_SETTERS['set_heating'] = ('fuel', 'gen_seasonal_eff',
            #          'SCoP', 'gen_size', ..., 'is_heat_pump', ...)
            heat_payload = dict(before_h)
            heat_payload["SCoP"] = ref_scop
            heat_payload["is_heat_pump"] = True  # la référence est toujours une PAC

            try:
                system.set_heating(heat_payload)
            except Exception as exc:
                sys_result["heating_set_error"] = str(exc)
                fail_count += 1
                results.append(sys_result)
                continue

            # Readback
            try:
                after_h = dict(system.heating() or {})
                rb_scop = after_h.get("SCoP")
                h_ok, h_det = _ok(ref_scop, rb_scop, "SCoP")
                sys_result["heating"] = {
                    "ok": h_ok,
                    "target_SCoP": ref_scop,
                    "before_SCoP": before_h.get("SCoP"),
                    "readback_SCoP": rb_scop,
                    "is_heat_pump_set": after_h.get("is_heat_pump"),
                    "readback_detail": h_det,
                    "uncertainty": "⚠ SCoP(VE) ↔ SCOP(SIA 380/2 Table 8) — à confirmer",
                }
                if h_ok:
                    ok_count += 1
                else:
                    fail_count += 1
            except Exception as exc:
                sys_result["heating_readback_error"] = str(exc)
                fail_count += 1

        # --- Refroidissement : set_cooling({"SEER": ref_eer}) ---
        if scope in cooling_by_scope and hasattr(system, "set_cooling") and hasattr(system, "cooling"):
            cool_sub = cooling_by_scope[scope]
            ref_eer = cool_sub.reference_value

            try:
                before_c = dict(system.cooling() or {})
            except Exception as exc:
                sys_result["cooling_error"] = "cooling() failed: {}".format(exc)
                fail_count += 1
                results.append(sys_result)
                continue

            cool_payload = dict(before_c)
            cool_payload["SEER"] = ref_eer

            try:
                system.set_cooling(cool_payload)
            except Exception as exc:
                sys_result["cooling_set_error"] = str(exc)
                fail_count += 1
                results.append(sys_result)
                continue

            try:
                after_c = dict(system.cooling() or {})
                rb_seer = after_c.get("SEER")
                c_ok, c_det = _ok(ref_eer, rb_seer, "SEER")
                sys_result["cooling"] = {
                    "ok": c_ok,
                    "target_SEER": ref_eer,
                    "before_SEER": before_c.get("SEER"),
                    "readback_SEER": rb_seer,
                    "readback_detail": c_det,
                    "uncertainty": "⚠ SEER(VE) ↔ EER(SIA 380/2 Table 5) — à confirmer",
                }
                if c_ok:
                    ok_count += 1
                else:
                    fail_count += 1
            except Exception as exc:
                sys_result["cooling_readback_error"] = str(exc)
                fail_count += 1

        results.append(sys_result)

    status = "OK" if fail_count == 0 and ok_count > 0 else (
        "PARTIAL" if ok_count > 0 else "FAILED_READBACK"
    )
    return {
        "family": "generation",
        "status": status,
        "ok_count": ok_count,
        "fail_count": fail_count,
        "per_system": results,
        "uncertainty_SCoP": "SCoP(VE) = SCOP(SN EN 14825) — non prouvé identique",
        "uncertainty_SEER": "SEER(VE) vs EER Table 5 SIA 380/2 — non prouvé identique",
    }


# ===========================================================================
# Fabrique : construction de référence opaque
# ===========================================================================

def _surface_resistances_for_type(element_type):
    """Retourne (Rsi, Rso) selon le type de surface (source : ISO 6946:2017 T.1)."""
    if "roof" in element_type or "ceiling" in element_type:
        return _RSI_ROOF, _RSO_ROOF
    if "floor" in element_type or "ground" in element_type or "slab" in element_type:
        return _RSI_FLOOR, _RSO_FLOOR
    return _RSI_WALL, _RSO_WALL   # walls, default


def _calc_insul_thickness(u_target, rsi, rso, lam=_INSUL_CONDUCTIVITY):
    """
    Épaisseur de la couche isolante pour atteindre U_target W/(m²K).
    U = 1 / (Rsi + t/λ + Rso)  →  t = λ × (1/U - Rsi - Rso)
    Retourne None si le résultat est négatif (U_target trop grand pour ce λ).
    """
    r_needed = 1.0 / u_target - rsi - rso
    if r_needed <= 0:
        return None
    return lam * r_needed


def _create_opaque_reference_construction(iesve, cdb_proj, element_type, u_target, name_hint):
    """
    Crée une construction opaque de référence à U-value cible.
    Source pattern : ve_asset_provisioner.py:1680-1745

    Structure : surface_inside_resistance | couche isolante | surface_outside_resistance
    Retourne (construction_id: str, u_calculated: float, warnings: list).
    ⚠ À VÉRIFIER : les clés exactes de set_properties() sur VECdbConstruction.
    """
    warnings = []

    # Surface resistances selon le type de surface
    rsi, rso = _surface_resistances_for_type(element_type)
    thickness = _calc_insul_thickness(u_target, rsi, rso)
    if thickness is None or thickness <= 0:
        raise ValueError(
            "U_target={} W/(m²K) irréalisable avec λ={} W/(mK) "
            "(Rsi={} + Rso={} dépassent déjà 1/U)".format(
                u_target, _INSUL_CONDUCTIVITY, rsi, rso
            )
        )

    # --- Créer le matériau isolant ---
    mat_cat = _get_material_category(iesve, "other")
    if mat_cat is None:
        raise RuntimeError("material_categories.other non disponible")
    material = cdb_proj.create_material(mat_cat)

    mat_props = {
        "conductivity": _INSUL_CONDUCTIVITY,
        "density": _INSUL_DENSITY,
        "specific_heat_capacity": _INSUL_SPECIFIC_HEAT,
    }
    # ⚠ À VÉRIFIER API : clés exactes de set_properties() sur un matériau VE.
    # Pattern déduit de ve_asset_provisioner.py:_create_material (ne figure pas
    # explicitement dans le code montré, mais le pattern est : create + set_properties).
    material.set_properties(mat_props)
    try:
        mat_after = dict(material.get_properties())
        for k, v in mat_props.items():
            got = mat_after.get(k)
            if got is not None and not _values_close(v, got):
                warnings.append("Matériau : {} attendu={} lu={}".format(k, v, got))
    except Exception as exc:
        warnings.append("Readback matériau impossible : {}".format(exc))

    mat_id = str(getattr(material, "id", "") or "")
    if not mat_id:
        raise RuntimeError("Le matériau créé n'a pas d'ID persistant")

    # --- Créer la construction opaque ---
    elem_cat_name = {
        "wall": "wall", "roof": "roof",
        "floor": "ground_floor",
    }.get(element_type.split("_")[0], "wall")
    elem_cat = _get_element_category(iesve, elem_cat_name)
    if elem_cat is None:
        raise RuntimeError("element_categories.{} non disponible".format(elem_cat_name))

    opaque_class = _get_opaque_class(iesve)
    if opaque_class is None:
        raise RuntimeError("construction_class.opaque non disponible")

    construction = cdb_proj.create_construction(elem_cat)
    construction.set_const_class(opaque_class)

    # Supprimer les couches par défaut (source : ve_asset_provisioner.py:1688-1704)
    initial_layers = list(construction.get_layers())
    for lyr in initial_layers:
        if hasattr(lyr, "get_id"):
            construction.delete_layer(lyr.get_id())

    # Ajouter la couche isolante
    construction.add_layer(mat_id, False)   # is_cavity=False
    layer = list(construction.get_layers())[-1]

    layer_props = {"thickness": thickness}
    layer.set_properties(layer_props)
    try:
        lp_after = dict(layer.get_properties())
        t_got = lp_after.get("thickness")
        if t_got is not None and not _values_close(thickness, t_got):
            warnings.append(
                "Couche : épaisseur attendue={:.4f} m lue={} m".format(thickness, t_got)
            )
    except Exception as exc:
        warnings.append("Readback couche impossible : {}".format(exc))

    # Définir les résistances surfaciques sur la construction
    # ⚠ À VÉRIFIER API : ces clés sont présentes dans ve_field_policy.py:365
    # comme champs de readback mais leur écriture via set_properties n'est
    # pas prouvée en production sur ce dépôt.
    try:
        surf_props = {
            "inside_surface_resistance": rsi,
            "outside_surface_resistance": rso,
        }
        if hasattr(construction, "set_properties"):
            construction.set_properties(surf_props)
        else:
            warnings.append("set_properties non disponible — Rsi/Rso non écrits")
    except Exception as exc:
        warnings.append("set_properties(surface_resistances) échoué : {}".format(exc))

    # Nommer la construction pour la traçabilité
    try:
        desc = "SIA3802_REF_{} U={:.3f} W/(m2K) lam={} t={:.4f}m".format(
            name_hint.upper(), u_target, _INSUL_CONDUCTIVITY, thickness
        )
        construction.set_properties({"description": desc})
    except Exception:
        pass

    cid = str(getattr(construction, "id", "") or "")
    if not cid:
        raise RuntimeError("La construction créée n'a pas d'ID persistant")

    u_calculated = 1.0 / (rsi + thickness / _INSUL_CONDUCTIVITY + rso)
    return cid, construction, u_calculated, warnings


# ===========================================================================
# Fabrique : construction de référence vitrée
# ===========================================================================

def _create_glazed_reference_construction(
    iesve, cdb_proj, u_target, g_value, tau_v, name_hint
):
    """
    Crée une construction vitrée simple verre + cavité calibrée à U_target.
    Structure : pane de verre (g, τ_v) | cavité R calibrée
    Source pattern : ve_asset_provisioner.py:1726-1734 (glazed path)
    ⚠ À VÉRIFIER API : propriétés exactes du matériau verre (transmittance,
    visible_transmittance) et de la couche cavité (resistance).
    """
    warnings_list = []

    # Résistance de la cavité pour atteindre U_target
    # U = 1 / (Rsi + R_glass + R_cavity + Rso)
    r_glass = _GLASS_THICKNESS / _GLASS_CONDUCTIVITY  # ≈ 0.004 m²K/W
    r_cavity_needed = 1.0 / u_target - _RSI_GLAZ - r_glass - _RSO_GLAZ
    if r_cavity_needed <= 0:
        # U trop grand : utiliser cavité minimale (0.17 m²K/W pour lame d'air)
        r_cavity_needed = 0.01
        warnings_list.append(
            "U_target={} élevé : R_cavity calculée négative, utilisée à 0.01 m²K/W".format(
                u_target
            )
        )

    # --- Matériau verre ---
    glass_cat = _get_material_category(iesve, "glass")
    if glass_cat is None:
        raise RuntimeError("material_categories.glass non disponible")

    glass_mat = cdb_proj.create_material(glass_cat)
    glass_props = {
        "conductivity": _GLASS_CONDUCTIVITY,
        "density": 2500.0,
        "specific_heat_capacity": 750.0,
        "transmittance": g_value,          # g_perp EN 410
        "visible_transmittance": tau_v,    # τ_v EN 410
    }
    # ⚠ À VÉRIFIER API : clés transmittance / visible_transmittance sur verre VE.
    # Référence partielle : ve_field_policy.py:248-267 (readback de ces propriétés
    # confirme leur existence en lecture).
    glass_mat.set_properties(glass_props)
    glass_mat_id = str(getattr(glass_mat, "id", "") or "")
    if not glass_mat_id:
        raise RuntimeError("Matériau verre sans ID persistant")

    # --- Construction vitrée ---
    glaz_cat = _get_element_category(iesve, "ext_glazing")
    if glaz_cat is None:
        raise RuntimeError("element_categories.ext_glazing non disponible")
    glazed_class = _get_glazed_class(iesve)
    if glazed_class is None:
        raise RuntimeError("construction_class.glazed non disponible")

    construction = cdb_proj.create_construction(glaz_cat)
    construction.set_const_class(glazed_class)

    # Récupérer les couches initiales (la couche par défaut glazée ne doit PAS
    # être supprimée avant d'en avoir ajouté de nouvelles — ve_asset_provisioner.py:1683)
    initial_layers = list(construction.get_layers())
    initial_layer_ids = []
    for lyr in initial_layers:
        if hasattr(lyr, "get_id"):
            initial_layer_ids.append(lyr.get_id())

    # Ajouter pane de verre
    construction.add_layer(glass_mat_id, False)
    glass_layer = list(construction.get_layers())[-1]
    glass_layer_props = {"thickness": _GLASS_THICKNESS}
    glass_layer.set_properties(glass_layer_props)

    # Ajouter cavité thermique
    # is_cavity=True : couche cavité (resistance, pas de matériau)
    # ⚠ À VÉRIFIER API : add_layer(material_id, is_cavity=True) — quand
    # is_cavity=True, material_id peut être vide ou ignoré.
    try:
        construction.add_layer("", True)   # cavité sans matériau
        cavity_layer = list(construction.get_layers())[-1]
        cav_props = {"resistance": r_cavity_needed}
        cavity_layer.set_properties(cav_props)
    except Exception as exc:
        warnings_list.append("Ajout cavité échoué ({}), tentative avec mat_id='0'".format(exc))
        try:
            construction.add_layer("0", True)
            cavity_layer = list(construction.get_layers())[-1]
            cavity_layer.set_properties({"resistance": r_cavity_needed})
        except Exception as exc2:
            warnings_list.append("Cavité également échouée avec id='0' : {}".format(exc2))

    # Supprimer les couches initiales par défaut (APRÈS avoir ajouté les nôtres)
    for lid in initial_layer_ids:
        try:
            construction.delete_layer(lid)
        except Exception:
            pass

    # Résistances surfaciques
    try:
        surf_res = {
            "inside_surface_resistance": _RSI_GLAZ,
            "outside_surface_resistance": _RSO_GLAZ,
        }
        if hasattr(construction, "set_properties"):
            construction.set_properties(surf_res)
    except Exception as exc:
        warnings_list.append("set_properties(surface_resistances glazed) : {}".format(exc))

    # Description traçable
    try:
        desc = "SIA3802_REF_GLAZ U={:.2f} g={:.2f} tau={:.2f}".format(
            u_target, g_value, tau_v
        )
        construction.set_properties({"description": desc})
    except Exception:
        pass

    cid = str(getattr(construction, "id", "") or "")
    if not cid:
        raise RuntimeError("Construction vitrée sans ID persistant")

    u_calc = 1.0 / (_RSI_GLAZ + r_glass + r_cavity_needed + _RSO_GLAZ)
    return cid, construction, u_calc, warnings_list


# ===========================================================================
# Applicateur (e) : Enveloppe opaque
# ===========================================================================

def _apply_opaque_envelope(spec, iesve, cdb_proj, model):
    """
    Pour chaque type de surface (wall/roof/floor) :
      1. Détermine la référence U (une valeur par type, identique pour tous les scopes)
      2. Crée UNE construction de référence par type
      3. Assigne à toutes les surfaces de ce type (tous rooms)
      4. Readback : surface.get_constructions() contient le nouvel ID

    Source : ve_api.py:762-774,767
    """
    results = []

    # Grouper les substitutions opaque par element_type et prendre le reference_value
    # (identique pour tous les scopes de même type car c'est la valeur normative Table 3)
    type_to_ref = {}
    for sub in spec.substitutions:
        if sub.element_type not in ("wall", "roof", "floor"):
            continue
        if sub.reference_value is None:
            continue
        if sub.element_type not in type_to_ref:
            type_to_ref[sub.element_type] = sub.reference_value

    if not type_to_ref:
        return {"family": "opaque_envelope", "status": "SKIP",
                "reason": "Pas de substitution opaque avec reference_value dans la spec"}

    try:
        all_bodies = list(model.get_bodies(False))
        rooms = [b for b in all_bodies if _is_room_body(b)]
    except Exception as exc:
        return {"family": "opaque_envelope", "status": "PREFLIGHT_FAIL", "error": str(exc)}

    for elem_type, u_ref in type_to_ref.items():
        type_result = {
            "element_type": elem_type,
            "u_target": u_ref,
        }
        try:
            cid, construction_obj, u_calc, warns = _create_opaque_reference_construction(
                iesve, cdb_proj, elem_type, u_ref, elem_type
            )
            type_result["construction_created"] = {
                "id": cid,
                "u_calculated": u_calc,
                "warnings": warns,
            }
            print("  [{}] Construction ref créée : id={} U_calc={:.4f} W/(m²K)".format(
                elem_type, cid, u_calc
            ))
        except Exception as exc:
            type_result["status"] = "CONSTRUCTION_CREATE_FAILED"
            type_result["error"] = str(exc)
            results.append(type_result)
            continue

        ok_surf = 0
        fail_surf = 0
        surf_results = []

        for body in rooms:
            if not hasattr(body, "get_surfaces"):
                continue
            try:
                surfaces = list(body.get_surfaces())
            except Exception:
                continue
            for surface in surfaces:
                # Déterminer le type de surface — logique exacte de ve_api.py:607-620.
                # NOTE : "wall" seul ne doit PAS correspondre à "internalwall" ;
                # on utilise exactement les prédicats de ve_api.py.
                try:
                    props = surface.get_properties() if hasattr(surface, "get_properties") else {}
                    s_type = str(
                        props.get("type", "") if isinstance(props, dict)
                        else getattr(surface, "type", "")
                    ).lower().replace("_", "").replace(" ", "")
                except Exception:
                    s_type = ""

                # is_external : si l'attribut est accessible et faux, ignorer
                # (source : model_analyzer.py:is_external)
                is_ext = getattr(surface, "is_external", None)
                if is_ext is False:
                    continue

                # Correspondance type (source : ve_api.py:607-620, verbatim)
                if elem_type == "wall":
                    matches = (
                        "externalwall" in s_type
                        or "extwall" in s_type
                        or s_type == "wall"
                    )
                elif elem_type == "roof":
                    matches = "roof" in s_type or "externalceiling" in s_type
                elif elem_type == "floor":
                    matches = "ground" in s_type or "slab" in s_type
                else:
                    matches = False
                if not matches:
                    continue

                # Assigner la construction de référence (source : ve_api.py:764)
                try:
                    body.assign_construction(construction_obj, surface)
                except Exception as exc:
                    surf_results.append({
                        "surface": s_type, "ok": False,
                        "assign_error": str(exc),
                    })
                    fail_surf += 1
                    continue

                # Readback (source : ve_api.py:766-773)
                try:
                    assigned_ids = [
                        _construction_id(c) for c in surface.get_constructions()
                    ]
                    rb_ok = cid in assigned_ids
                    surf_results.append({
                        "surface_type": s_type,
                        "ok": rb_ok,
                        "ref_construction_id": cid,
                        "assigned_ids_after": assigned_ids,
                    })
                    if rb_ok:
                        ok_surf += 1
                    else:
                        fail_surf += 1
                except Exception as exc:
                    surf_results.append({
                        "surface_type": s_type, "ok": False,
                        "readback_error": str(exc),
                    })
                    fail_surf += 1

        type_result["status"] = "OK" if fail_surf == 0 and ok_surf > 0 else (
            "PARTIAL" if ok_surf > 0 else "FAILED_READBACK"
        )
        type_result["surfaces_ok"] = ok_surf
        type_result["surfaces_failed"] = fail_surf
        type_result["surface_details"] = surf_results[:50]  # limiter le JSON
        results.append(type_result)

    overall = "OK" if all(r.get("status") == "OK" for r in results) else (
        "PARTIAL" if any(r.get("status") == "OK" for r in results) else "FAILED_READBACK"
    )
    return {"family": "opaque_envelope", "status": overall, "per_type": results}


# ===========================================================================
# Applicateur (f)+(g) : Vitrage + Frame fraction
# ===========================================================================

def _apply_glazing(spec, iesve, cdb_proj, model):
    """
    Crée une construction vitrée de référence par scope et l'assigne aux ouvertures.
    Tente également de modifier la frame_fraction si opening.set_properties()
    est disponible (⚠ non confirmé dans les modules existants).

    Source assign : ve_api.py:790 (assign_construction_to_opening)
    Source readback : ve_api.py:793 (opening.get_construction())
    """
    results = []

    # Grouper les 4 paramètres de vitrage par scope (construction ID)
    glazing_by_scope = {}
    for sub in spec.substitutions:
        if sub.element_type != "opening":
            continue
        if sub.reference_value is None:
            continue
        scope_ids = [s.strip() for s in str(sub.scope or "").split(",") if s.strip()]
        for sid in scope_ids:
            glazing_by_scope.setdefault(sid, {})
            glazing_by_scope[sid][sub.parameter] = sub.reference_value

    if not glazing_by_scope:
        return {"family": "glazing", "status": "SKIP",
                "reason": "Pas de substitution vitrée avec reference_value dans la spec"}

    try:
        all_bodies = list(model.get_bodies(False))
        rooms = [b for b in all_bodies if _is_room_body(b)]
    except Exception as exc:
        return {"family": "glazing", "status": "PREFLIGHT_FAIL", "error": str(exc)}

    for scope_id, params in glazing_by_scope.items():
        u_target = params.get("window_u", 1.1)
        g_value = params.get("glazing_g_value", 0.5)
        tau_v = params.get("glazing_light_transmittance", 0.5)
        frame_frac = params.get("window_frame_fraction")

        scope_result = {
            "scope_id": scope_id,
            "u_target": u_target,
            "g_target": g_value,
            "tau_v_target": tau_v,
            "frame_fraction_target": frame_frac,
        }

        try:
            cid, glaz_obj, u_calc, warns = _create_glazed_reference_construction(
                iesve, cdb_proj, u_target, g_value, tau_v,
                "GLAZ_{}".format(scope_id[:8])
            )
            scope_result["construction_created"] = {
                "id": cid, "u_calculated": u_calc, "warnings": warns,
            }
            print("  [glazing scope={}] id={} U_calc={:.3f}".format(scope_id, cid, u_calc))
        except Exception as exc:
            scope_result["status"] = "CONSTRUCTION_CREATE_FAILED"
            scope_result["error"] = str(exc)
            results.append(scope_result)
            continue

        ok_op = 0
        fail_op = 0
        opening_results = []

        for body in rooms:
            if not hasattr(body, "get_surfaces"):
                continue
            try:
                surfaces = list(body.get_surfaces())
            except Exception:
                continue
            for surface in surfaces:
                if not hasattr(surface, "get_openings"):
                    continue
                try:
                    openings = list(surface.get_openings())
                except Exception:
                    continue
                for opening in openings:
                    # Vérifier si cette ouverture utilise l'ancienne construction
                    try:
                        props = dict(opening.get_properties()) if hasattr(opening, "get_properties") else {}
                    except Exception:
                        props = {}
                    opening_type = str(props.get("type", "") or "").lower()
                    if "door" in opening_type:
                        continue   # ne pas modifier les portes

                    # Vérifier si c'est une ouverture de la scope concernée
                    # (en comparant l'ID de construction actuel)
                    current_cid = None
                    if hasattr(opening, "get_construction"):
                        try:
                            current_cid = _construction_id(opening.get_construction())
                        except Exception:
                            pass
                    if current_cid != scope_id and current_cid is not None:
                        continue  # cette ouverture n'utilise pas la construction scope

                    # Assigner la construction de référence (source : ve_api.py:790)
                    op_id = None
                    if hasattr(opening, "get_id"):
                        try:
                            op_id = opening.get_id()
                        except Exception:
                            pass
                    try:
                        body.assign_construction_to_opening(glaz_obj, surface, op_id)
                    except Exception as exc:
                        opening_results.append({
                            "opening_id": str(op_id), "ok": False,
                            "assign_error": str(exc),
                        })
                        fail_op += 1
                        continue

                    # Readback construction (source : ve_api.py:793)
                    try:
                        assigned_cid = _construction_id(opening.get_construction())
                        rb_ok = (assigned_cid == cid)
                        op_entry = {
                            "opening_id": str(op_id),
                            "ok": rb_ok,
                            "ref_construction_id": cid,
                            "readback_construction_id": assigned_cid,
                        }
                    except Exception as exc:
                        op_entry = {
                            "opening_id": str(op_id), "ok": False,
                            "readback_error": str(exc),
                        }
                        rb_ok = False

                    # Tentative frame fraction (⚠ À VÉRIFIER API)
                    if frame_frac is not None and hasattr(opening, "set_properties"):
                        try:
                            opening.set_properties({"frame_fraction": frame_frac})
                            after_props = dict(opening.get_properties()) if hasattr(opening, "get_properties") else {}
                            got_ff = after_props.get("frame_fraction")
                            ff_ok = _values_close(frame_frac, got_ff) if got_ff is not None else False
                            op_entry["frame_fraction"] = {
                                "ok": ff_ok,
                                "target": frame_frac,
                                "readback": got_ff,
                            }
                        except Exception as exc:
                            op_entry["frame_fraction"] = {
                                "ok": False,
                                "error": str(exc),
                                "note": "⚠ opening.set_properties() non confirmé dans les modules existants",
                            }
                    elif frame_frac is not None:
                        op_entry["frame_fraction"] = {
                            "ok": None,
                            "note": "⚠ opening.set_properties() absent — frame_fraction non modifiée",
                        }

                    opening_results.append(op_entry)
                    if rb_ok:
                        ok_op += 1
                    else:
                        fail_op += 1

        scope_result["status"] = "OK" if fail_op == 0 and ok_op > 0 else (
            "PARTIAL" if ok_op > 0 else "FAILED_READBACK"
        )
        scope_result["openings_ok"] = ok_op
        scope_result["openings_failed"] = fail_op
        scope_result["opening_details"] = opening_results[:50]
        results.append(scope_result)

    overall = "OK" if all(r.get("status") == "OK" for r in results) else (
        "PARTIAL" if any(r.get("status") == "OK" for r in results) else "FAILED_READBACK"
    )
    return {"family": "glazing", "status": overall, "per_scope": results}


# ===========================================================================
# Main
# ===========================================================================

def main():
    """
    Orchestre le cycle complet : garde → spec → pre-flight → mutations → rapport.
    """
    import importlib

    try:
        iesve = importlib.import_module("iesve")
    except Exception as exc:
        print("Ce script doit s'exécuter depuis IESVE VEScripts : {}".format(exc))
        return

    from swiss_sia.data_extractor import VEDataExtractor
    from swiss_sia.model_analyzer import ModelAnalyzer
    from swiss_sia.reference_project import build_reference_project_specification

    project = iesve.VEProject.get_current_project()
    project_path = str(getattr(project, "path", "") or "")
    model = project.models[0] if getattr(project, "models", None) else None

    print("=" * 65)
    print("SIA 380/2 — Constructeur de projet de référence")
    print("=" * 65)
    print("Projet : {}".format(project_path))

    # ----------------------------------------------------------------
    # GARDE PRINCIPAL : copie jetable obligatoire
    # ----------------------------------------------------------------
    try:
        _assert_disposable(project_path, iesve)
    except RuntimeError as exc:
        print("\n{}".format(exc))
        return

    # ----------------------------------------------------------------
    # Extraction de la spec SIA 380/2
    # ----------------------------------------------------------------
    print("\n[1/8] Extraction de la spec SIA 380/2...")
    extractor = VEDataExtractor(project)
    analyzer = ModelAnalyzer(extractor)
    rooms = analyzer.analyze_all_rooms()
    spec = build_reference_project_specification(rooms, analyzer)
    print("      Statut spec : {} | {} substitutions | {} bloqueurs".format(
        spec.status, len(spec.substitutions), len(spec.blockers)
    ))

    # ----------------------------------------------------------------
    # CDB
    # ----------------------------------------------------------------
    print("[2/8] Connexion CDB...")
    try:
        cdb_proj = _cdb_project(iesve)
        print("      CDB : OK")
    except Exception as exc:
        print("      CDB IMPOSSIBLE : {}".format(exc))
        cdb_proj = None

    # ----------------------------------------------------------------
    # Pre-flight
    # ----------------------------------------------------------------
    print("[3/8] Pre-flight capability check (aucune mutation)...")
    pf_ok, pf_report = _preflight(iesve, project, cdb_proj, model)
    if pf_report["failed"]:
        print("      CAPABILITIES MANQUANTES : {}".format(pf_report["failed"]))
    else:
        print("      Pre-flight : OK — toutes les capacités disponibles")

    if not pf_ok:
        print("\nPRE-FLIGHT BLOQUANT. Rapport partiel écrit. Aucune mutation effectuée.")
        _write_report(project_path, {
            "schema_version": SCHEMA_VERSION,
            "operation": OPERATION,
            "status": "BLOCKED_PREFLIGHT",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "project_path": project_path,
            "preflight": pf_report,
        })
        return

    # ----------------------------------------------------------------
    # Mutations : (a) infiltration → (b)+(c) émission+capacité →
    #             (d) génération → (e) enveloppe → (f) vitrage
    # ----------------------------------------------------------------
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "operation": OPERATION,
        "status": "IN_PROGRESS",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_path": project_path,
        "spec_status": spec.status,
        "no_apachesim": True,
        "preflight": pf_report,
        "mutations": {},
    }

    print("[4/8] (a) Infiltration...")
    result_infil = _apply_infiltration(spec, model)
    receipt["mutations"]["infiltration"] = result_infil
    print("      Statut : {} | rooms_mutated={}".format(
        result_infil["status"],
        result_infil.get("rooms_mutated", "n/a"),
    ))

    print("[5/8] (b)+(c) Émission + Capacité illimitée...")
    result_em, result_cap = _apply_emission_capacity(model)
    receipt["mutations"]["emission"] = result_em
    receipt["mutations"]["capacity"] = result_cap
    print("      Émission : {} | rooms_ok={}".format(
        result_em["status"], result_em.get("rooms_ok", "n/a")
    ))
    print("      Capacité  : {} | rooms_ok={}".format(
        result_cap["status"], result_cap.get("rooms_ok", "n/a")
    ))

    print("[6/8] (d) Génération (HVAC set_heating / set_cooling)...")
    result_gen = _apply_generation(spec, project)
    receipt["mutations"]["generation"] = result_gen
    print("      Statut : {} | ok_count={}".format(
        result_gen["status"], result_gen.get("ok_count", "n/a")
    ))

    if cdb_proj is not None:
        print("[7/8] (e) Enveloppe opaque (create_construction + assign)...")
        result_opaque = _apply_opaque_envelope(spec, iesve, cdb_proj, model)
        receipt["mutations"]["opaque_envelope"] = result_opaque
        print("      Statut : {}".format(result_opaque["status"]))

        print("[8/8] (f) Vitrage (create_construction glazed + assign_to_opening)...")
        result_glaz = _apply_glazing(spec, iesve, cdb_proj, model)
        receipt["mutations"]["glazing"] = result_glaz
        print("      Statut : {}".format(result_glaz["status"]))
    else:
        print("[7/8] Enveloppe : SKIP (CDB non disponible)")
        print("[8/8] Vitrage   : SKIP (CDB non disponible)")
        receipt["mutations"]["opaque_envelope"] = {"status": "SKIP", "reason": "CDB unavailable"}
        receipt["mutations"]["glazing"] = {"status": "SKIP", "reason": "CDB unavailable"}

    # Statut global
    all_statuses = [v.get("status") for v in receipt["mutations"].values()]
    if all(s == "OK" for s in all_statuses):
        receipt["status"] = "ALL_OK"
    elif any(s == "OK" or s == "PARTIAL" for s in all_statuses):
        receipt["status"] = "PARTIAL"
    else:
        receipt["status"] = "FAILED"

    # ----------------------------------------------------------------
    # Résumé console
    # ----------------------------------------------------------------
    print("\n" + "=" * 65)
    print("RÉSUMÉ DES MUTATIONS")
    print("=" * 65)
    for fam, res in receipt["mutations"].items():
        print("  %-35s %s" % (fam, res.get("status", "?")))
    print("\nStatut global : {}".format(receipt["status"]))
    print("ApacheSim : PAS lancé — lancer séparément après vérification.")
    print("Avertissements de correspondance API :")
    print("  - SCoP(VE) ↔ SCOP(SIA 380/2 Table 8) : ⚠ à confirmer")
    print("  - SEER(VE) ↔ EER(SIA 380/2 Table 5)  : ⚠ à confirmer")
    print("  - frame_fraction setter sur opening   : ⚠ si non disponible, non modifié")

    # ----------------------------------------------------------------
    # Écriture JSON
    # ----------------------------------------------------------------
    _write_report(project_path, receipt)


def _write_report(project_path, payload):
    """Écrit le rapport JSON à côté du projet VE."""
    out_dir = Path(project_path).parent if project_path else PROJECT_ROOT
    out_path = out_dir / "sia3802_reference_build_receipt.json"
    try:
        out_path.write_text(
            json.dumps(_jsonable(payload), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print("\nRapport JSON écrit : {}".format(out_path))
    except Exception as exc:
        print("\nImpossible d'écrire le JSON ({}) — dump console :".format(exc))
        print(json.dumps(_jsonable(payload), ensure_ascii=False, indent=2)[:5000])


if __name__ == "__main__":
    main()
