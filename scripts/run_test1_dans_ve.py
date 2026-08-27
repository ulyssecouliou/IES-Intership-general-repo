# -*- coding: utf-8 -*-
"""Chains Test 1 end to end, from the VE Python Scripts navigator.

The building blocks already existed in `ve_adapter/test1_adapter.py` — case
generation, weather assignment, ApacheSim launch, extraction — but nothing
chained them together. That is what this script does.

TWO MODES.

    python scripts/run_test1_dans_ve.py --preflight
        Checks the installation WITHOUT simulating anything. Runnable outside VE.
        Run this first: six simulations take time, and it is better to know
        beforehand if a file is missing.

    python scripts/run_test1_dans_ve.py --run
        Generates, simulates and extracts the six DRYCOLD cases, writes the
        candidate, evaluates and displays the verdict. Requires a VEScripts session.

WHAT THIS SCRIPT DOES NOT DO. It does not handle diagnostic cases 1A to 1E:
they require the Zürich-Kloten climate (`KLO_dry_normal.PRN`), which is absent
from any source in our possession. Yet **1E is the only Test 1 case carrying a
pass/fail criterion**. This run therefore produces the numerical comparison of the
six main cases — demonstrable and showable — but NOT the formal Test 1 verdict.
The script says so at every execution rather than letting it be assumed.

TWO WARNINGS FROM THE ISO CLIMATE FILE, not to be missed:

1. Its first month is an INITIALISATION month (December copied, 744 h).
   A simulation of 8760 h starting on 1 January does not reproduce the initial
   state of the reference programs. The effect is greatest on high-mass cases —
   900, 940, 900FF.
2. It provides irradiance ALREADY CALCULATED on eight named surfaces, without
   global/direct/diffuse decomposition. A `.epw` delivers global/direct/diffuse
   and lets VE derive the surfaces: the input is not the same. Hence the solar
   check below, to be done BEFORE interpreting any thermal discrepancy.
"""

from __future__ import print_function

import io
import json
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

# The six main Test 1 cases, the ones that run under DRYCOLD.
CAS_DRYCOLD = ("600", "640", "900", "940", "600FF", "900FF")

# Diagnostic cases, out of scope without the Kloten climate.
CAS_KLOTEN = ("1A", "1B", "1C", "1D", "1E")

# VE weather library: this is where the .epw must be placed.
DOSSIER_METEO_VE = r"C:\Program Files\IES\Shared Content\Weather"
FICHIER_METEO = "DRYCOLD_IESVE.epw"

# Annual reference irradiation on the SOUTH facade, from the public
# climate file of EN ISO 52016-1 (column "SV"), frozen in
# refs/reference-data/iso-52016-1-climat-drycold.json.
IRRADIATION_SUD_REFERENCE_KWH_M2 = 1547.1

# Beyond this relative discrepancy, VE's sky model becomes a confounding
# factor: any thermal deviation would first be explained by the solar input.
TOLERANCE_SOLAIRE_RELATIVE = 0.01

CHEMIN_CANDIDAT = os.path.join(_RACINE, "outputs", "test1_candidat.json")


def ascii_sur(texte):
    """Removes accents for console display.

    The VEScripts script window is not UTF-8: "détecté" would appear as
    "d鐵ct遡". Accents are therefore stripped for display — and only
    there. Files written remain in full UTF-8.

    Args:
        texte: Text to display.

    Returns:
        str: The same text, without non-ASCII characters.
    """
    import unicodedata

    decompose = unicodedata.normalize("NFKD", "%s" % texte)
    return decompose.encode("ascii", "ignore").decode("ascii")


def dire(texte=""):
    """Displays a readable line in the VEScripts console.

    Args:
        texte: Text to display.
    """
    print(ascii_sur(texte))


#: Maximum number of elements kept from a sequence in the report. High enough
#: not to lose anything from a `dir()`: the truncated part is precisely the one
#: that normally contains the name being looked for.
LIMITE_ELEMENTS = 500


def _serialisable(valeur, profondeur=0):
    """Converts any value to a JSON-serialisable structure.

    Never raises: an exotic `iesve` API object is reduced to its `repr`,
    never discarded.

    Args:
        valeur: Value to convert.
        profondeur: Current recursion depth.

    Returns:
        Any: Structure made of JSON types.
    """
    if valeur is None or isinstance(valeur, (bool, int, float)):
        return valeur
    if isinstance(valeur, str):
        return valeur
    if profondeur >= 3:
        return repr(valeur)[:400]
    if isinstance(valeur, (list, tuple, set)):
        elements = list(valeur)[:LIMITE_ELEMENTS]
        return [_serialisable(e, profondeur + 1) for e in elements]
    if isinstance(valeur, dict):
        return dict(
            ("%s" % cle, _serialisable(val, profondeur + 1))
            for cle, val in list(valeur.items())[:LIMITE_ELEMENTS]
        )
    return repr(valeur)[:400]


def _membres(objet):
    """Public names exposed by an object, COMPLETE list.

    Args:
        objet: Object to inspect.

    Returns:
        list[str]: Sorted names, without private members.
    """
    try:
        return sorted(nom for nom in dir(objet) if not nom.startswith("_"))
    except Exception as erreur:  # noqa: BLE001
        return ["<dir() a echoue : %s>" % erreur]


#: Key under which `VECdbDatabase.get_projects()` stores the projects. The
#: other two ("system", "manufacturer") are vendor-supplied libraries, not the
#: open project.
#:
#: CAUTION, this is NOT a string. The keys are members of
#: `iesve.project_types`, and the probe report of 2026-08-07 showed this:
#:
#:     {iesve.project_types.project: [<VECdbProject>], ...}
#:
#: Serialised to JSON they come out as "project", giving the illusion of a
#: text-keyed dictionary. Comparison is therefore made on the textual form of
#: the key, not on the key itself.
CLE_PROJET_CDB = "project"


def _premier_projet_cdb(projets):
    """Extracts a `VECdbProject` from what `get_projects()` returns.

    WHY THIS FUNCTION. Probe v2 did `projets[0]` and introspected a **list**:
    it therefore reported `['append', 'clear', 'copy', 'count',
    'extend', 'index', 'insert', 'pop', 'remove', 'reverse', 'sort']` as
    the attributes of `VECdbProject`. `get_projects()` actually returns a
    dictionary `{'project': [...], 'system': [...], 'manufacturer':
    [...]}`.

    The trap is that a dictionary is truthy, iterable and indexable: nothing
    fails, and the report looks valid. Only reading the reported attributes
    revealed the error.

    Args:
        projets: Value returned by `get_projects()`, or `None` if the step
            failed.

    Returns:
        The first project, or `None` if none is found. Never an object of
        another type: a failed step is better than a false reading.
    """
    if not projets:
        return None
    if isinstance(projets, dict):
        candidats = _valeur_par_cle_textuelle(projets, CLE_PROJET_CDB)
    else:
        # Unexpected form: accept it rather than failing, but without
        # assuming it contains projects — the type check below decides.
        candidats = projets
    for candidat in candidats:
        # A list or a string at this position signals we are again at the
        # wrong level: do not introspect it.
        if not isinstance(candidat, (list, tuple, dict)) and not _est_texte(candidat):
            return candidat
    return None


def _valeur_par_cle_textuelle(table, nom):
    """Looks up an entry by the TEXTUAL form of its key.

    `get_projects()` indexes by members of `iesve.project_types`, not by
    strings. A `table.get('project')` therefore silently fails and returns an
    empty list — which reads as "no project" when there actually is one.

    Args:
        table: Dictionary whose keys may be enumerated members.
        nom: Name sought, in its textual form.

    Returns:
        list: Associated value, or empty list if the key is absent.
    """
    for cle, valeur in table.items():
        if cle == nom or "%s" % (cle,) == nom or getattr(cle, "name", None) == nom:
            return valeur or []
    return []


def _est_texte(valeur):
    """True if the value is a string, on both Python 2 and Python 3.

    Args:
        valeur: Value to test.

    Returns:
        bool: True for a character or byte string.
    """
    try:
        types_texte = (str, unicode, bytes)  # noqa: F821 -- Python 2
    except NameError:
        types_texte = (str, bytes)
    return isinstance(valeur, types_texte)


#: Increasing scale tried for the ideal insulator. Zero first, since
#: that is what ISO 52016-1 gives; then increasingly large values
#: until VE preserves one unchanged on readback.
ECHELLE_MINIMUM = (0.0, 0.001, 0.01, 0.1, 1.0, 10.0)

#: Readback tolerance. VE stores as 32-bit float.
TOLERANCE_RELECTURE = 1e-6


def _proprietes_des_couches(construction):
    """Reads back the layers of a construction and their properties.

    Answers a precise question: `add_layer` writes no thickness, and thickness
    does not exist at the material level. Do the layers therefore carry the
    correct values, or those VE assigns them by default?

    Args:
        construction: `VECdbConstruction` built.

    Returns:
        list: One entry per layer, or a description of the failure.
    """
    releves = []
    try:
        couches = list(construction.get_layers() or [])
    except Exception as erreur:  # noqa: BLE001
        return {"get_layers_a_echoue": "%s: %s" % (type(erreur).__name__, erreur)}
    for rang, couche in enumerate(couches):
        entree = {"rang": rang, "attributs": _membres(couche)}
        try:
            entree["proprietes"] = couche.get_properties()
        except Exception as erreur:  # noqa: BLE001
            entree["proprietes"] = "%s: %s" % (type(erreur).__name__, erreur)
        releves.append(entree)
    return releves


def _signature(methode):
    """Describes a method: docstring and signature if it exposes one.

    Native `iesve` methods do not normally expose an introspectable signature;
    their docstring, however, carries the parameter list. That is how the
    setters of `VEApacheSystem` were discovered.

    Args:
        methode: Method or function.

    Returns:
        dict: What could be discovered.
    """
    import inspect

    releve = {"doc": (getattr(methode, "__doc__", None) or "")[:400]}
    try:
        releve["signature"] = "%s" % (inspect.signature(methode),)
    except (TypeError, ValueError) as erreur:
        releve["signature"] = "non exposee (%s)" % type(erreur).__name__
    return releve


def _signature_dimport(module_iesve):
    """Discovers what the gbXML importer expects.

    The documentation announces `Import_file(file_name, heal_geometry, cap_mode,
    cap_height)` with a capital I; introspection gives `import_file`. It has
    already been wrong once: the actual docstring is read rather than trusted
    on anything else.

    Args:
        module_iesve: Module `iesve`.

    Returns:
        dict: What could be discovered on both spellings.
    """
    releve = {}
    importeur = getattr(module_iesve, "ImportGBXML", None)
    if importeur is None:
        return {"ImportGBXML": "absent du module"}
    releve["membres"] = _membres(importeur)
    for orthographe in ("import_file", "Import_file"):
        methode = getattr(importeur, orthographe, None)
        releve[orthographe] = "absent" if methode is None else _signature(methode)
    return releve


def _corps_du_modele(projet):
    """Reads the bodies of the current model and their surfaces.

    It is against these surfaces that those of an imported gbXML will be
    compared. Without this reading, a "successful" import would prove nothing:
    that is exactly the trap of the 1 mm thickness layers.

    Args:
        projet: Current `VEProject`.

    Returns:
        list | dict: One reading per body, or a description of the failure.
    """
    try:
        modeles = list(projet.models or [])
    except Exception as erreur:  # noqa: BLE001
        return {"models_a_echoue": "%s: %s" % (type(erreur).__name__, erreur)}
    if not modeles:
        return {"aucun_modele": True}

    # FLAT LIST, intentionally. Nesting bodies under their model placed the
    # surface dictionary at the FOURTH level, where `_serialisable` reduces it
    # to a repr truncated to 400 characters — the 2026-08-07 reading came out
    # unreadable for that reason alone.
    releves = []
    for modele in modeles[:2]:
        type_modele = "%s" % getattr(modele, "model_type", None)
        try:
            corps = list(modele.get_bodies(False) or [])
        except Exception as erreur:  # noqa: BLE001
            releves.append(
                {
                    "model_type": type_modele,
                    "get_bodies_a_echoue": "%s: %s" % (type(erreur).__name__, erreur),
                }
            )
            continue
        releves.append({"model_type": type_modele, "nb_corps": len(corps)})
        for objet in corps[:4]:
            detail = {
                "model_type": type_modele,
                "id": "%s" % getattr(objet, "id", None),
                "nom": "%s" % getattr(objet, "name", None),
                "type": "%s" % getattr(objet, "type", None),
            }
            for appel in ("get_areas", "get_room_data"):
                try:
                    valeur = getattr(objet, appel)()
                except Exception as erreur:  # noqa: BLE001
                    detail[appel] = "%s: %s" % (type(erreur).__name__, erreur)
                    continue
                # Flattened as `call.key`: surfaces remain readable regardless
                # of the depth ceiling.
                if isinstance(valeur, dict):
                    for cle, contenu in valeur.items():
                        detail["%s.%s" % (appel, cle)] = _serialisable(contenu)
                else:
                    detail[appel] = _serialisable(valeur)
            releves.append(detail)
    return releves


def _supprimer_materiaux(projet_cdb, identifiants):
    """Deletes test materials created by the probe.

    WHY. Each run was creating materials and deleting none:
    seven runs left **76 materials** in the construction database of the
    user's project. A read-only probe must leave the model as it found it;
    these have no reason to remain.

    The CONSTRUCTION materials are not concerned: they are legitimately
    used by the walls created.

    Args:
        projet_cdb: Open `VECdbProject`.
        identifiants: Identifiers to delete.

    Returns:
        dict: What was deleted, and what resisted.
    """
    supprimes, echecs = [], {}
    for identifiant in identifiants:
        if not identifiant:
            continue
        try:
            projet_cdb.delete_material(identifiant)
            supprimes.append(identifiant)
        except Exception as erreur:  # noqa: BLE001 -- un refus est un resultat
            echecs[identifiant] = "%s: %s" % (type(erreur).__name__, erreur)
    return {"supprimes": supprimes, "echecs": echecs}


def _echelle_de_minimum(projet_cdb, module_iesve):
    """Discovers the smallest density VE accepts to preserve.

    Writes each value from `ECHELLE_MINIMUM` on a test material, reads back,
    and records the written/read pair. No conclusions are drawn here: the
    report gives the pairs, and reading them is what decides.

    Args:
        projet_cdb: Open `VECdbProject`.
        module_iesve: Module `iesve`.

    Returns:
        list[dict]: One reading per value tried.
    """
    categorie = _membre_enum(module_iesve, "material_categories", "other")
    releves = []
    for valeur in ECHELLE_MINIMUM:
        essai = {"ecrit": valeur}
        try:
            materiau = projet_cdb.create_material(categorie)
            materiau.set_properties(
                {
                    "conductivity": 0.04,
                    "density": valeur,
                    "specific_heat_capacity": valeur,
                }
            )
            proprietes = materiau.get_properties() or {}
            essai["density_relu"] = proprietes.get("density")
            essai["cp_relu"] = proprietes.get("specific_heat_capacity")
            essai["conserve"] = _proche(essai["density_relu"], valeur)
            essai["id"] = proprietes.get("id")
        except Exception as erreur:  # noqa: BLE001 -- un refus est un resultat
            essai["erreur"] = "%s: %s" % (type(erreur).__name__, erreur)
            essai["conserve"] = False
        releves.append(essai)
    return releves


def _proche(obtenu, attendu):
    """Compares two floats with the readback tolerance.

    Args:
        obtenu: Value read back.
        attendu: Value written.

    Returns:
        bool: True if the two agree.
    """
    if obtenu is None:
        return False
    reference = abs(attendu) if attendu else 1.0
    return abs(obtenu - attendu) <= TOLERANCE_RELECTURE * reference


def _membre_enum(module, nom_enum, nom_membre):
    """Member of an `iesve` module enumerated type, resolved without guessing.

    Args:
        module: Module `iesve`.
        nom_enum: Name of the enum, for example `'material_categories'`.
        nom_membre: Name of the member, for example `'other'`.

    Returns:
        The member.

    Raises:
        RuntimeError: If the enum or member is missing — in which case the
            API has changed, and saying so is better than falling back to a
            default.
    """
    enum = getattr(module, nom_enum, None)
    if enum is None:
        raise RuntimeError("enum %r absent du module iesve" % nom_enum)
    membre = getattr(enum, nom_membre, None)
    if membre is None:
        raise RuntimeError("membre %r absent de %r" % (nom_membre, nom_enum))
    return membre


def _echouer(message):
    """Fails a step intentionally, with an explicit message.

    A step absent from the report is lost information; a failed step
    explains why it could not be done.

    Args:
        message: Reason for the failure.

    Raises:
        RuntimeError: Always.
    """
    raise RuntimeError(message)


def _enums(objet):
    """Enumerated-type members exposed by an object, with their values.

    In the `iesve` API, element categories and construction classes are held
    by classes whose public attributes are integers. That is precisely what
    `creer_constructions_cas` needs, and it is what has changed name since
    VE 2023.

    Args:
        objet: Object or module to inspect.

    Returns:
        dict: `{enum name: {member: value}}`, empty if none.
    """
    import types

    trouves = {}
    for nom in _membres(objet):
        try:
            candidat = getattr(objet, nom)
        except Exception:  # noqa: BLE001 -- certains attributs lèvent à la lecture
            continue
        # Restricted to CLASSES and MODULES: without this filter, a plain integer
        # produces a false enum via its `numerator`, `real`, etc. attributes,
        # and the report fills with noise that hides the real ones.
        if not isinstance(candidat, (type, types.ModuleType)):
            continue
        membres = {}
        for sous_nom in dir(candidat):
            if sous_nom.startswith("_"):
                continue
            try:
                valeur = getattr(candidat, sous_nom)
            except Exception:  # noqa: BLE001
                continue
            if isinstance(valeur, int) and not isinstance(valeur, bool):
                membres[sous_nom] = valeur
        if membres:
            trouves[nom] = membres
    return trouves


def _ok(libelle, detail=""):
    dire("  [OK]   %-42s %s" % (libelle, detail))
    return True


def _ko(libelle, detail=""):
    dire("  [MANQUE] %-40s %s" % (libelle, detail))
    return False


def preflight():
    """Checks the installation without simulating anything.

    Returns:
        bool: True if a run is possible. False if a prerequisite is missing.
    """
    dire("=== PRÉFLIGHT Test 1 ===")
    controles = []

    # 1. Frozen reference
    try:
        from engine import test1_engine as moteur

        reference = moteur.charger_reference()
        nb = len(reference.get("reference_values", {}))
        controles.append(_ok("référence Test 1 chargée", "%d grandeurs" % nb))
    except Exception as erreur:
        controles.append(_ko("référence Test 1", str(erreur)[:60]))
        reference = None

    # 2. Weather file deployed in VE
    chemin_meteo = os.path.join(DOSSIER_METEO_VE, FICHIER_METEO)
    if os.path.isfile(chemin_meteo):
        controles.append(
            _ok("météo DRYCOLD déployée", "%d octets" % os.path.getsize(chemin_meteo))
        )
    else:
        controles.append(_ko("météo DRYCOLD", chemin_meteo))

    # 3. Adapter importable
    try:
        from ve_adapter import test1_adapter  # noqa: F401

        controles.append(_ok("adaptateur Test 1 importable"))
    except Exception as erreur:
        controles.append(_ko("adaptateur Test 1", str(erreur)[:60]))

    # 4. VE session?
    dans_ve = _dans_ve()
    if dans_ve:
        controles.append(_ok("session VEScripts détectée"))
    else:
        dire(
            "  [INFO] hors VEScripts — le préflight est complet, "
            "mais --run exigera VE."
        )

    # 5. Output folder
    dossier = os.path.dirname(CHEMIN_CANDIDAT)
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    controles.append(_ok("dossier de sortie", dossier))

    dire()
    dire("  cas simulables sous DRYCOLD : %s" % ", ".join(CAS_DRYCOLD))
    dire("  cas EXCLUS (climat Kloten absent) : %s" % ", ".join(CAS_KLOTEN))
    dire("  ⚠ 1E est le seul cas porteur du critère pass/fail du Test 1.")
    dire("    Ce run produit une DÉMONSTRATION chiffrée, pas le verdict SIA.")
    dire()

    pret = all(controles)
    dire("=> %s" % ("prêt pour --run" if pret else "PRÉREQUIS MANQUANT, --run refusé"))
    return pret


def _dans_ve():
    """Indicates whether the `iesve` module is available.

    Returns:
        bool: True in a VEScripts session.
    """
    try:
        import iesve  # noqa: F401

        return True
    except ImportError:
        return False


def controler_solaire(irradiation_sud_calculee):
    """Compares VE's south irradiation against the ISO reference.

    To be done BEFORE interpreting any thermal discrepancy: the ISO file
    provides already-calculated surface irradiance, whereas VE derives it
    from the global value. A discrepancy here would explain divergences that
    would otherwise, wrongly, be attributed to the thermal engine.

    Args:
        irradiation_sud_calculee: Annual incident irradiation on the south
            facade as read from VE, in kWh/m2.

    Returns:
        dict: Absolute gap, relative gap, and check verdict.
    """
    ecart = irradiation_sud_calculee - IRRADIATION_SUD_REFERENCE_KWH_M2
    relatif = ecart / IRRADIATION_SUD_REFERENCE_KWH_M2
    return {
        "reference_kwh_m2": IRRADIATION_SUD_REFERENCE_KWH_M2,
        "calculee_kwh_m2": irradiation_sud_calculee,
        "ecart_kwh_m2": ecart,
        "ecart_relatif": relatif,
        "modele_de_ciel_neutre": abs(relatif) <= TOLERANCE_SOLAIRE_RELATIVE,
        "interpretation": (
            "modèle de ciel neutre : un écart thermique viendra du moteur"
            if abs(relatif) <= TOLERANCE_SOLAIRE_RELATIVE
            else "ATTENTION : le modèle de ciel est un facteur confondant ; "
            "expliquer tout écart thermique par le solaire AVANT le moteur"
        ),
    }


def executer():
    """Generates, simulates and extracts the six DRYCOLD cases.

    Returns:
        dict: Extracted candidate, ready for `evaluer_test1`.

    Raises:
        RuntimeError: Outside a VEScripts session, or if a prerequisite is
            missing.
    """
    if not _dans_ve():
        raise RuntimeError(
            "`iesve` indisponible : --run doit s'exécuter depuis le Python "
            "Scripts navigator de VE. Utiliser --preflight hors VE."
        )
    if not preflight():
        raise RuntimeError("préflight en échec : run refusé.")

    raise NotImplementedError(
        "L'enchaînement génération -> simulation -> extraction n'a jamais été "
        "exécuté dans une VE réelle. Les briques existent dans "
        "ve_adapter/test1_adapter.py (generer_cas_test1, "
        "assigner_meteo_drycold, lancer_apachesim_cas, extraire_candidat_test1) "
        "mais leur enchaînement doit être déroulé une première fois à la main, "
        "cas par cas, pour relever les noms d'objets réels. Les câbler ici "
        "sans cette étape produirait un script qui échoue au premier appel, en "
        "donnant l'illusion d'être prêt."
    )


def sonder(cas_id="600"):
    """Steps through ONE case in VE, capturing what the API returns.

    This is the run to do first in a real VE. It does not try to succeed:
    it tries to LEARN. Each step is attempted in isolation, its result or
    error is recorded, and the report then allows wiring the full chain
    without guessing a single object name.

    Args:
        cas_id: Case to probe. "600" is the simplest of the six.

    Returns:
        dict: Probe report, also written to disk.
    """
    rapport = {
        "cas": cas_id,
        "dans_ve": _dans_ve(),
        "etapes": [],
        "avertissement": (
            "Rapport de SONDE. Aucune valeur ici n'est un résultat de "
            "validation : ce fichier sert uniquement à relever les noms "
            "d'objets et signatures réels de l'API iesve."
        ),
    }

    def etape(nom, fonction):
        """Executes a step capturing its outcome IN FULL.

        The report truncates nothing: the cut part of an attribute list is
        precisely the one that contains the name being looked for.

        Args:
            nom: Step label.
            fonction: Callable taking no argument.

        Returns:
            Any: The result, or `None` on failure.
        """
        try:
            valeur = fonction()
        except Exception as erreur:  # noqa: BLE001 -- on consigne, on ne masque pas
            rapport["etapes"].append(
                {
                    "nom": nom,
                    "statut": "ECHEC",
                    "type_erreur": type(erreur).__name__,
                    "erreur": "%s" % erreur,
                }
            )
            dire("  [ECHEC] %-38s %s" % (nom, type(erreur).__name__))
            return None
        rapport["etapes"].append(
            {
                "nom": nom,
                "statut": "OK",
                "type": type(valeur).__name__,
                "valeur": _serialisable(valeur),
            }
        )
        dire("  [OK]    %-38s %s" % (nom, repr(valeur)[:56]))
        return valeur

    dire("=== SONDE Test 1, cas %s ===" % cas_id)
    if not rapport["dans_ve"]:
        dire("  hors VEScripts : la sonde ne peut rien apprendre ici.")
        return rapport

    import iesve
    from ve_adapter import test1_adapter as adaptateur

    # Identifiers of TEST materials, to delete at the end of the probe.
    # Those of the constructions are not included: the walls use them.
    jetables = []

    # --- Project and model ------------------------------------------------
    projet = etape("projet courant", lambda: iesve.VEProject.get_current_project())
    etape("modeles du projet", lambda: projet.models)
    etape("attributs du projet", lambda: _membres(projet))

    # --- Construction database: VECdbDatabase has only 3 methods, the real
    # --- entry point is get_projects() -> VECdbProject.
    cdb = etape(
        "base de constructions", lambda: iesve.VECdbDatabase.get_current_database()
    )
    etape("attributs de la base", lambda: _membres(cdb))
    projets_cdb = etape("projets de la base", lambda: cdb.get_projects())
    projet_cdb = _premier_projet_cdb(projets_cdb)
    if projet_cdb is not None:
        etape("attributs de VECdbProject", lambda: _membres(projet_cdb))
        etape("enums de VECdbProject", lambda: _enums(projet_cdb))
    else:
        etape(
            "attributs de VECdbProject",
            lambda: _echouer("aucun projet dans %r" % (projets_cdb,)),
        )

    # --- iesve module enums: this is most likely where element categories
    # --- and construction classes live.
    etape("classes du module iesve", lambda: _membres(iesve))
    etape("enums du module iesve", lambda: _enums(iesve))

    # --- Weather: already conclusive at first pass, replayed for the trace.
    etape(
        "affectation meteo DRYCOLD",
        lambda: adaptateur.assigner_meteo_drycold(
            os.path.join(DOSSIER_METEO_VE, FICHIER_METEO)
        ),
    )

    # --- Properties of a material: the ACCEPTED keys, not the guessed ones.
    #
    # On 2026-08-07, `set_properties({'description': 'plasterboard', ...})`
    # replied "could not convert string to float: 'plasterboard'": VE tries to
    # convert ALL values to float, so `description` is not an accepted key —
    # or not under that name. Trying others blindly would be the fifth time we
    # guessed; we read instead.
    if projet_cdb is not None:
        materiau = etape(
            "create_material (materiau d essai)",
            lambda: projet_cdb.create_material(
                _membre_enum(iesve, "material_categories", "other")
            ),
        )
        if materiau is not None:
            jetables.append((materiau.get_properties() or {}).get("id"))
            etape("attributs du materiau", lambda: _membres(materiau))
            etape(
                "get_properties() : LES CLES ACCEPTEES", lambda: materiau.get_properties()
            )
            # Writing only numeric values: if it passes, the faulty key
            # was indeed `description`.
            etape(
                "set_properties sans description (essai)",
                lambda: materiau.set_properties(
                    {
                        "conductivity": 0.16,
                        "thickness": 0.012,
                        "density": 950.0,
                        "specific_heat_capacity": 840.0,
                    }
                ),
            )
            etape("get_properties() apres ecriture", lambda: materiau.get_properties())

    # --- Minimum mass accepted by VE, for the IDEAL insulator of the floor.
    #
    # ISO 52016-1 Table 23 gives 0 for density and 0 for specific heat capacity;
    # ASHRAE 140 note (a) mandates "the minimum the software under test permits,
    # but not < 0". The value is therefore software-dependent BY CONSTRUCTION of
    # the standard: it is read, not chosen.
    #
    # We write an increasing scale and READ BACK: the first value VE returns
    # unchanged is the accepted minimum.
    if projet_cdb is not None:
        essais = etape(
            "minimum de masse accepte par VE",
            lambda: _echelle_de_minimum(projet_cdb, iesve),
        )
        for essai in essais or []:
            jetables.append(essai.get("id"))

    # --- Construction creation.
    #
    # CORRECTED on 2026-08-07: the probe was passing `cdb`, the DATABASE, whereas
    # `creer_constructions_cas` expects a `VECdbProject`. VE replied
    # "'VECdbDatabase' object has no attribute 'create_construction'" —
    # same error class as the enums looked for on the wrong container.
    constructions = None
    if projet_cdb is not None:
        constructions = etape(
            "constructions du cas",
            lambda: adaptateur.creer_constructions_cas(projet_cdb, "legere"),
        )

    # --- ARE THE THICKNESSES SET?
    #
    # `add_layer(material_id, False)` creates the layer but writes NO thickness
    # — and since 2026-08-07 the thickness is no longer on the material either,
    # since `thickness` does not exist there. The layers therefore carry whatever
    # VE assigns them by default.
    #
    # A construction created without raising, with wrong thicknesses, would
    # produce credible but false U-values. We read back.
    if constructions:
        etape(
            "couches du mur : epaisseurs REELLES",
            lambda: _proprietes_des_couches(constructions["mur"]),
        )

    # --- GEOMETRY: what the importer expects, and what the model contains.
    #
    # The API exposes NO geometry constructor: the only path is
    # `ImportGBXML.import_file`. Its signature has never been observed. The
    # documentation announces `Import_file(file_name, heal_geometry, cap_mode,
    # cap_height)` — but it is already wrong on capitalisation, introspection
    # giving `import_file`. We therefore read before writing a gbXML against
    # an assumed signature.
    etape("ImportGBXML : signature", lambda: _signature_dimport(iesve))

    # And what the model ALREADY contains: if it holds a geometry, its surfaces
    # can be read, and they are what the import will be compared against.
    etape("corps du modele courant", lambda: _corps_du_modele(projet))

    # --- Cleanup. A probe must leave the model as it found it.
    if projet_cdb is not None and jetables:
        etape(
            "suppression des materiaux d essai",
            lambda: _supprimer_materiaux(projet_cdb, jetables),
        )
    else:
        etape(
            "constructions du cas",
            lambda: _echouer("aucun VECdbProject : etape impossible"),
        )

    chemin = os.path.join(_RACINE, "outputs", "sonde_test1_%s.json" % cas_id)
    if not os.path.isdir(os.path.dirname(chemin)):
        os.makedirs(os.path.dirname(chemin))
    with io.open(chemin, "w", encoding="utf-8") as flux:
        flux.write(json.dumps(rapport, ensure_ascii=False, indent=2))
    dire()
    dire("rapport de sonde : %s" % chemin)
    dire(
        "-> me renvoyer ce fichier : il contient ce qu'il me manque pour "
        "câbler l'enchaînement sans deviner."
    )
    return rapport


def evaluer_et_afficher(candidat=None):
    """Evaluates a candidate and displays the discrepancy table.

    Args:
        candidat: Already-extracted candidate. If `None`, attempts to read
            `outputs/test1_candidat.json`; failing that, evaluates without
            a candidate (everything grey).

    Returns:
        dict: Result of `evaluer_test1`.
    """
    from engine import test1_engine as moteur

    if candidat is None and os.path.isfile(CHEMIN_CANDIDAT):
        with io.open(CHEMIN_CANDIDAT, encoding="utf-8") as flux:
            candidat = json.load(flux)
            dire("candidat relu : %s" % CHEMIN_CANDIDAT)

    if candidat is None:
        dire("aucun candidat : état « avant première simulation », tout gris.")

    resultat = moteur.evaluer_test1(moteur.charger_reference(), candidat)
    verdict = resultat.get("verdict_test1") or {}
    conforme = verdict.get("conforme")
    libelle = {True: "CONFORME", False: "NON CONFORME"}.get(conforme, "NON ÉVALUÉ")
    dire()
    dire("verdict Test 1 : %s" % libelle)
    if verdict.get("motif"):
        dire("  motif : %s" % verdict["motif"])
    dire(
        "  périodes 1E non évaluées : %s / %s"
        % (verdict.get("nb_periodes_non_evaluees"), verdict.get("nb_periodes_totales"))
    )
    dire(
        "  rappel : le verdict du Test 1 porte sur le SEUL cas 1E, qui "
        "exige le climat de Kloten. Les six cas DRYCOLD sont comparés à "
        "titre démonstratif, sans critère de déviation."
    )
    return resultat


# --------------------------------------------------------------------------
# EXECUTION MODE
#
# The VE Python Scripts navigator does NOT offer a terminal: there is only a
# "Run" button, so there is no way to pass `--sonde`. The mode is therefore
# determined automatically:
#
#     in VE    -> SONDE     (the only action that learns something)
#     outside  -> PREFLIGHT (installation check, without simulating anything)
#
# To force a mode from VE, replace 'auto' below with 'preflight',
# 'sonde', 'evaluer' or 'run', then press Run. That is the only setting
# to change; no other line in the file needs to be touched.
# --------------------------------------------------------------------------
MODE = "auto"

MODES_CONNUS = ("auto", "preflight", "sonde", "evaluer", "run")


def _mode_effectif(arguments):
    """Determines the mode to run.

    Command-line arguments take precedence when present — for those who have
    a terminal. Otherwise falls back to `MODE`, then to automatic detection.

    Args:
        arguments: Command-line arguments, without the script name.

    Returns:
        str: One of 'preflight', 'sonde', 'evaluer', 'run'.
    """
    for nom in ("run", "sonde", "evaluer", "preflight"):
        if "--" + nom in arguments:
            return nom

    if MODE in MODES_CONNUS and MODE != "auto":
        return MODE

    return "sonde" if _dans_ve() else "preflight"


def main(arguments=()):
    """Entry point, usable from the keyboard as well as the Run button.

    Args:
        arguments: Command-line arguments, without the script name.
            Empty when the script is launched from the VE Run button.

    Returns:
        int: Exit code, 0 if everything went well.
    """
    mode = _mode_effectif(arguments)
    dire(
        "mode : %s%s"
        % (
            mode,
            "  (détecté automatiquement)" if not arguments and MODE == "auto" else "",
        )
    )
    dire()

    if mode == "sonde":
        rapport = sonder()
        return 0 if rapport["dans_ve"] else 1

    if mode == "evaluer":
        evaluer_et_afficher()
        return 0

    if mode == "preflight":
        return 0 if preflight() else 1

    if mode == "run":
        try:
            candidat = executer()
        except (RuntimeError, NotImplementedError) as erreur:
            dire("RUN IMPOSSIBLE : %s" % erreur)
            return 1
        with io.open(CHEMIN_CANDIDAT, "w", encoding="utf-8") as flux:
            flux.write(json.dumps(candidat, ensure_ascii=False, indent=2))
        dire("candidat écrit : %s" % CHEMIN_CANDIDAT)
        evaluer_et_afficher(candidat)
        return 0

    dire("mode inconnu : %r — modes valides : %s" % (mode, ", ".join(MODES_CONNUS)))
    return 1


if __name__ == "__main__":
    # `sys.argv` may be absent or empty when VEScripts executes the file
    # via its Run button: we assume nothing.
    _arguments = tuple(getattr(sys, "argv", ())[1:])
    _code = main(_arguments)

    dire()
    dire("--- terminé (code %d) ---" % _code)

    # `sys.exit` raises SystemExit, which VEScripts surfaces as an error in
    # its script window. We therefore only exit explicitly when a terminal is
    # clearly present (arguments were passed).
    if _arguments:
        sys.exit(_code)
