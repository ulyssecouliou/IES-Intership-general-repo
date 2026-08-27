# -*- coding: utf-8 -*-
"""Confronts the GEOMETRY of the IFC against the QUANTITIES it declares itself.

READ-ONLY. Modifies neither the IFC nor any VE model.

Why: before importing the example building into IESVE, it is necessary to know
if its geometry is usable. Two independent derivations exist in the file, and
they must agree:

  1. the **declared quantities** (`IFCQUANTITYAREA('GrossFloorArea', ...)`,
     `GrossVolume`, `AverageHeight`), read by
     `scripts/inspect_ifc_example_building.py`;
  2. the **actual geometry** (closed profiles extruded vertically), read by
     `AbstractBimIfcSpaceExtractor` from the `IES-Intership-general-repo`
     repository, which computes the area of each polygon and the volume of
     the prism.

If the two agree, the geometry is sound and importable. If they diverge, this
must be elucidated BEFORE the import: a wrong surface would propagate into all
results of Tests 4 to 7 without being visible.

The extractor from the existing repository is deliberately *fail-closed*: it
refuses rotations and non-vertical extrusions rather than approximating them.
This script only runs it and compares; it implements no geometry.

Usage :
    python scripts/crosscheck_ifc_geometry.py [chemin_depot_existant]
"""

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

DEPOT_DEFAUT = RACINE

# Comparison tolerances. These are NOT normative: they are internal control
# thresholds, chosen wide so as to flag only genuine disagreements.
# A polygon area and a quantity rounded to 2 decimal places in the file
# cannot coincide exactly.
TOL_SURFACE_M2 = 0.05
TOL_VOLUME_M3 = 1.0
TOL_HAUTEUR_M = 0.02


def main():
    depot = sys.argv[1] if len(sys.argv) > 1 else DEPOT_DEFAUT
    if not os.path.isdir(depot):
        sys.stderr.write("Depot existant introuvable : " + depot + "\n")
        return 1

    # ⚠ IMPORT ORDER: the existing repository also has a `scripts` package.
    # Import ours BEFORE adding its path to `sys.path`, otherwise `scripts`
    # resolves there and `inspect_ifc_example_building` becomes unreachable.
    from scripts.inspect_ifc_example_building import IFC_DEFAUT, inventaire

    sys.path.insert(0, depot)
    try:
        from swiss_sia.reference_model.sia4010.ifc_space_extractor import (
            AbstractBimIfcSpaceExtractor,
        )
    except ImportError as erreur:
        sys.stderr.write("Import de l extracteur impossible : " + str(erreur) + "\n")
        return 1

    if not os.path.isfile(IFC_DEFAUT):
        sys.stderr.write("IFC introuvable : " + IFC_DEFAUT + "\n")
        return 1

    _entites, _etages, locaux = inventaire(IFC_DEFAUT)
    declare = {}
    for local in locaux:
        mesures = local["quantites"]
        declare[local["nom"]] = {
            "surface": mesures.get("GrossFloorArea"),
            "volume": mesures.get("GrossVolume"),
            "hauteur": mesures.get("AverageHeight"),
            "designation": local["designation"],
            "etage": local["etage"],
        }

    extracteur = AbstractBimIfcSpaceExtractor(IFC_DEFAUT)
    try:
        geometrie = extracteur.extract()
    except Exception as erreur:
        print("L extracteur a REFUSE le fichier (comportement fail-closed) :")
        print("   " + type(erreur).__name__ + " : " + str(erreur))
        print("")
        print("C est une information, pas necessairement un defaut : l extracteur")
        print("rejette ce qu il ne sait pas lire exactement. A elucider avant import.")
        return 2

    print("=== GEOMETRIE vs QUANTITES DECLAREES ===")
    print(
        "locaux lus par la geometrie : %d / %d declares" % (len(geometrie), len(declare))
    )
    premier = next(iter(geometrie.values()))
    print("source sha256 (trace par l extracteur) : %s..." % premier.source_sha256[:16])
    print("")

    entete = "%-6s %-22s %9s %9s %8s   %8s %8s %7s"
    print(
        entete
        % (
            "Local",
            "Designation",
            "Geo m2",
            "Decl m2",
            "ecart",
            "Geo m3",
            "Decl m3",
            "H geo",
        )
    )
    ecarts_surface, ecarts_volume, ecarts_hauteur, absents = [], [], [], []
    for numero in sorted(geometrie):
        record = geometrie[numero]
        reference = declare.get(numero)
        if reference is None:
            absents.append(numero)
            continue
        d_surface = (
            record.area_m2 - reference["surface"]
            if reference["surface"] is not None
            else None
        )
        d_volume = (
            record.volume_m3 - reference["volume"]
            if reference["volume"] is not None
            else None
        )
        d_hauteur = (
            record.height_m - reference["hauteur"]
            if reference["hauteur"] is not None
            else None
        )
        print(
            entete
            % (
                numero,
                (reference["designation"] or "")[:22],
                "%.2f" % record.area_m2,
                (
                    "%.2f" % reference["surface"]
                    if reference["surface"] is not None
                    else "-"
                ),
                "%+.3f" % d_surface if d_surface is not None else "-",
                "%.1f" % record.volume_m3,
                "%.1f" % reference["volume"] if reference["volume"] is not None else "-",
                "%.2f" % record.height_m,
            )
        )
        if d_surface is not None and abs(d_surface) > TOL_SURFACE_M2:
            ecarts_surface.append((numero, d_surface))
        if d_volume is not None and abs(d_volume) > TOL_VOLUME_M3:
            ecarts_volume.append((numero, d_volume))
        if d_hauteur is not None and abs(d_hauteur) > TOL_HAUTEUR_M:
            ecarts_hauteur.append((numero, d_hauteur))

    print("")
    print(
        "somme des surfaces, geometrie : %.2f m2"
        % sum(r.area_m2 for r in geometrie.values())
    )
    print(
        "somme des surfaces, declarees : %.2f m2"
        % sum(v["surface"] or 0.0 for v in declare.values())
    )
    print("")

    verdict = 0
    for libelle, liste, unite, seuil in (
        ("surface", ecarts_surface, "m2", TOL_SURFACE_M2),
        ("volume", ecarts_volume, "m3", TOL_VOLUME_M3),
        ("hauteur", ecarts_hauteur, "m", TOL_HAUTEUR_M),
    ):
        if liste:
            verdict = 3
            print(
                "ECART %s au-dela de %.2f %s : %d local/locaux"
                % (libelle, seuil, unite, len(liste))
            )
            for numero, delta in liste[:10]:
                print("   local %-6s %+.3f %s" % (numero, delta, unite))
        else:
            print(
                "%-8s : concordance sur les %d locaux (seuil %.2f %s)"
                % (libelle, len(geometrie), seuil, unite)
            )
    if absents:
        verdict = 3
        print("locaux lus par la geometrie mais absents des quantites : %s" % absents)

    print("")
    if verdict == 0:
        print("VERDICT : geometrie et quantites declarees concordent.")
        print("La geometrie de l IFC est exploitable pour l import IESVE.")
    else:
        print("VERDICT : divergences a elucider AVANT tout import.")
    return verdict


if __name__ == "__main__":
    sys.exit(main())
