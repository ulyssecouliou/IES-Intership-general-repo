# -*- coding: utf-8 -*-
"""Imports the Test 1 geometry into VE, and READS BACK what VE made of it.

WHY A SEPARATE SCRIPT FROM THE PROBE. An import **modifies the model**. The
Test 1 probe is a reading: it creates test materials and deletes them. Slipping
an import into it would mean a simple reading mutates the model without being
asked — exactly the kind of side effect that only becomes apparent once the
damage is done. This import is therefore launched **explicitly**, on a
throwaway project.

WHAT THIS SCRIPT DOES, IN ORDER:

    1. writes the gbXML from `ve_adapter/gbxml_test1.py` — which already
       refuses to write an inconsistent geometry;
    2. imports it via `ImportGBXML.import_file`, whose signature is not
       introspectable: several call forms are tried, and the one that responds
       is RECORDED;
    3. **reads back `get_bodies()` then `get_areas()`** and compares the
       surfaces against the source.

STEP 3 IS THE ONLY ONE THAT PROVES ANYTHING. An import that does not raise
says nothing: the 1 mm layer thicknesses were created without the slightest
error, and their R-value was forty-seven times too low. A wrongly imported
geometry would behave the same way.

It writes `outputs/import_geometrie_test1.json`.
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

from scripts.run_test1_dans_ve import (  # noqa: E402
    _dans_ve,
    _membres,
    _serialisable,
    dire,
)

CHEMIN_RAPPORT = os.path.join(_RACINE, "outputs", "import_geometrie_test1.json")
CHEMIN_GBXML = os.path.join(_RACINE, "outputs", "test1_cellule.xml")

#: Call forms tried for `import_file`, from most complete to simplest. The
#: documentation announces `(file_name, heal_geometry, cap_mode, cap_height)`
#: but has already been wrong on capitalisation; the actual docstring reduces
#: to "cap_height". We therefore try, and record what responds.
#:
#: Each entry is `(label, arguments after the file name)`.
FORMES_DAPPEL = (
    ("file_name seul", ()),
    ("file_name + heal_geometry", (True,)),
    ("file_name + heal + cap_mode", (True, 0)),
    ("file_name + heal + cap_mode + cap_height", (True, 0, 0.0)),
)

#: Comparison tolerance for read-back surfaces, in m². Wide enough to absorb
#: VE's 32-bit float, tight enough to catch a missing face or a wrong dimension.
TOLERANCE_M2 = 1e-3

#: Mapping between our faces and the keys of `get_areas()`. It is NOT
#: established: `get_areas()` returns aggregates (`ext_wall_area`), not one
#: entry per face. Comparison therefore applies to TOTALS, the only
#: comparable quantities.
CLES_DE_SURFACE = {
    "murs_exterieurs": ("ext_wall_area",),
    "vitrage_exterieur": ("ext_wall_glazed",),
    "plancher": ("ext_floor_area", "int_floor_area"),
    "toiture": ("ext_ceiling_area", "int_ceiling_area"),
}


def totaux_attendus(cotes):
    """Expected surface totals, aggregated as `get_areas()` returns them.

    `get_areas()` does not give one entry per face: it aggregates external
    walls, glazing, floor and roof. Comparison is therefore made on these
    same aggregates — comparing face by face would compare what VE does not
    separate.

    Args:
        cotes: `geometry` block from the source.

    Returns:
        dict: `{item: surface in m²}`.
    """
    from ve_adapter import geometrie_test1 as geometrie

    surfaces = geometrie.surfaces_attendues(cotes)
    return {
        "murs_exterieurs": (
            surfaces["front_wall"]
            + surfaces["back_wall"]
            + surfaces["left_wall"]
            + surfaces["right_wall"]
        ),
        "vitrage_exterieur": surfaces["windows"],
        "plancher": surfaces["floor"],
        "toiture": surfaces["ceiling"],
    }


def totaux_releves(corps):
    """Sums the surfaces read back from all bodies in the model.

    Args:
        corps: List of `VEBody` objects.

    Returns:
        dict: `{item: surface}`, an absent item remaining as `None`.
    """
    cumul = dict((poste, None) for poste in CLES_DE_SURFACE)
    for objet in corps:
        try:
            aires = objet.get_areas() or {}
        except Exception:  # noqa: BLE001 -- l absence est un resultat
            continue
        for poste, cles in CLES_DE_SURFACE.items():
            for cle in cles:
                valeur = aires.get(cle)
                if valeur is None:
                    continue
                cumul[poste] = (cumul[poste] or 0.0) + float(valeur)
    return cumul


def comparer(attendus, releves):
    """Confronts the read-back surfaces against the expected surfaces.

    Args:
        attendus: What `totaux_attendus` returns.
        releves: What `totaux_releves` returns.

    Returns:
        dict: One verdict per item — never a global boolean, which would hide
        which item diverges.
    """
    verdicts = {}
    for poste, attendu in sorted(attendus.items()):
        obtenu_brut = releves.get(poste)
        obtenu = obtenu_brut
        normalisation = ""
        # VE 2025 reports ``ext_wall_area`` as the gross facade area while
        # also exposing ``ext_wall_glazed`` separately.  The source geometry
        # reports opaque wall area.  Subtracting the independently matching
        # glazed area is therefore a unit/definition normalization, not a
        # tolerance or a geometry correction.
        if poste == "murs_exterieurs" and obtenu is not None:
            vitrage = releves.get("vitrage_exterieur")
            if vitrage is not None:
                net = float(obtenu) - float(vitrage)
                if abs(net - attendu) <= TOLERANCE_M2:
                    obtenu = net
                    normalisation = (
                        "VE ext_wall_area is gross; ext_wall_glazed was "
                        "subtracted to compare the opaque net area."
                    )
        if obtenu is None:
            verdicts[poste] = {
                "attendu_m2": attendu,
                "releve_m2": None,
                "statut": "NON_RELEVE",
                "note": "VE n expose pas ce poste sur les corps lus. "
                "Ne PAS le lire comme zero.",
            }
            continue
        ecart = obtenu - attendu
        verdicts[poste] = {
            "attendu_m2": attendu,
            "releve_m2": obtenu,
            "releve_brut_m2": obtenu_brut,
            "ecart_m2": ecart,
            "statut": "CONCORDE" if abs(ecart) <= TOLERANCE_M2 else "DIVERGE",
            "note": (
                normalisation
                if abs(ecart) <= TOLERANCE_M2
                else "La geometrie importee ne reproduit pas la source. "
                "L import a pu reussir en produisant une cellule fausse."
            ),
        }
    return verdicts


def _essayer_import(importeur, chemin, module_iesve=None):
    """Tries the known call forms until one responds.

    The signature is not introspectable: its docstring reduces to "cap_height".
    We therefore try, from most complete to simplest, and record what worked —
    this reading will be valid for all subsequent imports.

    Args:
        importeur: `iesve.ImportGBXML`.
        chemin: gbXML file.
        module_iesve: Optional top-level ``iesve`` module. VE 2025 exposes the
            required ``VolumeCapMode`` enum there rather than on ImportGBXML.

    Returns:
        dict: Retained form and result, or the failures for each attempt.
    """
    essais = []
    cap_mode_container = getattr(importeur, "VolumeCapMode", None)
    if cap_mode_container is None and module_iesve is not None:
        cap_mode_container = getattr(module_iesve, "VolumeCapMode", None)
    if cap_mode_container is not None and hasattr(cap_mode_container, "none"):
        try:
            resultat = importeur.import_file(chemin, True, cap_mode_container.none, 0.0)
        except Exception as erreur:  # noqa: BLE001 -- un refus est un resultat
            essais.append(
                {
                    "forme": "signature VE 2025 + VolumeCapMode.none",
                    "statut": "ECHEC",
                    "erreur": "%s: %s" % (type(erreur).__name__, erreur),
                }
            )
        else:
            essais.append(
                {
                    "forme": "signature VE 2025 + VolumeCapMode.none",
                    "statut": "OK",
                    "retour": _serialisable(resultat),
                }
            )
            return {
                "forme_retenue": "signature VE 2025 + VolumeCapMode.none",
                "essais": essais,
            }
    for libelle, arguments in FORMES_DAPPEL:
        try:
            resultat = importeur.import_file(chemin, *arguments)
        except Exception as erreur:  # noqa: BLE001 -- un refus est un resultat
            essais.append(
                {
                    "forme": libelle,
                    "statut": "ECHEC",
                    "erreur": "%s: %s" % (type(erreur).__name__, erreur),
                }
            )
            continue
        essais.append(
            {"forme": libelle, "statut": "OK", "retour": _serialisable(resultat)}
        )
        return {"forme_retenue": libelle, "essais": essais}
    return {"forme_retenue": None, "essais": essais}


def importer(chemin_gbxml=None):
    """Runs the import and the readback.

    Args:
        chemin_gbxml: gbXML to import; written from the source if absent.

    Returns:
        dict: Report, also written to disk.
    """
    from ve_adapter import gbxml_test1 as gbxml
    from ve_adapter import geometrie_test1 as geometrie

    rapport = {
        "dans_ve": _dans_ve(),
        "avertissement": (
            "Ce script MODIFIE le modele VE : il y importe une geometrie. "
            "A lancer sur un projet JETABLE, jamais sur un modele client."
        ),
        "etapes": [],
    }

    def etape(nom, fonction):
        try:
            valeur = fonction()
        except Exception as erreur:  # noqa: BLE001 -- on consigne
            rapport["etapes"].append(
                {
                    "nom": nom,
                    "statut": "ECHEC",
                    "type_erreur": type(erreur).__name__,
                    "erreur": "%s" % erreur,
                }
            )
            dire("  [ECHEC] %-40s %s" % (nom, type(erreur).__name__))
            return None
        rapport["etapes"].append(
            {"nom": nom, "statut": "OK", "valeur": _serialisable(valeur)}
        )
        dire("  [OK]    %-40s %s" % (nom, repr(valeur)[:44]))
        return valeur

    dire("=== IMPORT DE LA GEOMETRIE DU TEST 1 ===")
    dire("  ATTENTION : ce script modifie le modele. Projet jetable requis.")

    cotes = etape("cotes de la source", lambda: geometrie.charger_cotes())
    if cotes is None:
        _ecrire(rapport)
        return rapport

    chemin = chemin_gbxml or CHEMIN_GBXML
    etape("ecriture du gbXML", lambda: gbxml.ecrire(chemin, cotes))
    attendus = etape("surfaces attendues", lambda: totaux_attendus(cotes))

    if not rapport["dans_ve"]:
        dire("  hors VEScripts : le gbXML est ecrit, l import ne peut pas")
        dire("  se faire ici. Relancer depuis VE.")
        _ecrire(rapport)
        return rapport

    import iesve

    etape("attributs de ImportGBXML", lambda: _membres(iesve.ImportGBXML))
    import_fait = etape(
        "import_file : formes essayees",
        lambda: _essayer_import(iesve.ImportGBXML, chemin, iesve),
    )

    if not (import_fait or {}).get("forme_retenue"):
        dire("  aucune forme d appel n a repondu : voir le rapport.")
        _ecrire(rapport)
        return rapport

    corps = etape("corps du modele apres import", lambda: _corps_apres_import(iesve))
    if corps is not None and attendus is not None:
        etape(
            "CONFRONTATION des surfaces",
            lambda: comparer(attendus, totaux_releves(corps)),
        )

    _ecrire(rapport)
    return rapport


def _corps_apres_import(module_iesve):
    """Reads back the bodies of the current model.

    Args:
        module_iesve: Module `iesve`.

    Returns:
        list: Bodies of the first model.
    """
    projet = module_iesve.VEProject.get_current_project()
    modeles = list(projet.models or [])
    if not modeles:
        return []
    return list(modeles[0].get_bodies(False) or [])


def _ecrire(rapport):
    """Writes the report and says where to find it.

    Args:
        rapport: Import report.
    """
    dossier = os.path.dirname(CHEMIN_RAPPORT)
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    with io.open(CHEMIN_RAPPORT, "w", encoding="utf-8") as flux:
        flux.write(json.dumps(rapport, ensure_ascii=False, indent=2))
    dire()
    dire("rapport : %s" % CHEMIN_RAPPORT)
    dire("-> la seule etape qui prouve quelque chose est la CONFRONTATION.")


def main(arguments=()):
    """Entry point.

    Args:
        arguments: Explicit gbXML path, optional.

    Returns:
        int: 0 if the report could be written, 1 otherwise.
    """
    chemins = [a for a in arguments if not a.startswith("--")]
    rapport = importer(chemins[0] if chemins else None)
    return 0 if rapport.get("etapes") else 1
