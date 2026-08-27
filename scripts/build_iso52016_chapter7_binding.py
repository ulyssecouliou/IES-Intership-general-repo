# -*- coding: utf-8 -*-
"""Writes the normalised binding artefact for the chapter 7 test cell.

WHY THIS SCRIPT EXISTS. The delegated-inputs manifest never consumes the
primary source directly: it consumes a normalised artefact linked to the exact
fingerprint of that source. This artefact must therefore be **reproducible** —
reconstructible identically from the source — otherwise the proof chain stops
at a file nobody knows how to remake.

WHAT IT DOES NOT DO. It does not convert units, complete any missing value,
or choose any convention. It transcribes, reorders the layers in the direction
the contract expects, and **declares** the single field the source does not
carry.

THE PROVISIONAL VALUE. `config/iso52016_chapter7_confirmed_inputs.json` carries
no infrared emissivity, which the contract requires. Rather than inventing one,
the script derives it from the radiative coefficients the source already carries,
then declares it in `declared_provisional_values` with its derivation, its
assumption, and what clears it. The loader rejects such a declaration if the
artefact does not simultaneously prohibit any compliance claim, and the Test 2A
generating contract turns it into a verdict blocker. A provisional value makes
the chain executable; it never underpins a result.
"""

from __future__ import print_function

import argparse
import hashlib
import io
import json
import os
import sys

_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RACINE)

#: Stefan-Boltzmann constant, W/(m2 K4).
SIGMA = 5.670374419e-8

#: Reference temperatures assumed for the source's radiative coefficients.
#: The source does not state them: this is the assumption to confirm.
T_INTERIEUR_K = 293.15
T_EXTERIEUR_K = 273.15

#: Identifiers expected by the normalised contract.
SCHEMA_ID = "sia4010.iso52016_chapter7_test_cell.v1"
SCHEMA_VERSION = "1.0"


def _empreinte(chemin):
    """Returns the SHA-256 of a file.

    Args:
        chemin: Absolute path to the file.

    Returns:
        str: Lowercase hexadecimal fingerprint.
    """
    digest = hashlib.sha256()
    with open(chemin, "rb") as flux:
        for bloc in iter(lambda: flux.read(65536), b""):
            digest.update(bloc)
    return digest.hexdigest()


def emissivite_derivee(coefficient_radiatif, temperature_k):
    """Derives an emissivity from a linearised radiative coefficient.

    The standard linearisation of radiative transfer is written
    h_r = 4 epsilon sigma T^3, giving epsilon = h_r / (4 sigma T^3).

    Args:
        coefficient_radiatif: h_r in W/(m2 K).
        temperature_k: Assumed reference temperature, in K.

    Returns:
        float: Derived emissivity, dimensionless.
    """
    return coefficient_radiatif / (4.0 * SIGMA * temperature_k**3)


def _construction(identifiant, couches_interieur_vers_exterieur, emissivite, absorptance):
    """Transcribes an opaque construction in the direction expected by the contract.

    The source lists layers from inside to outside; the normalised contract
    expects them from outside to inside. Reversal is the only processing applied.

    Args:
        identifiant: Stable construction identifier.
        couches_interieur_vers_exterieur: Layers as the source lists them.
        emissivite: Derived provisional emissivity, applied to both faces.
        absorptance: Solar absorptance stated by the source.

    Returns:
        dict: Normalised construction block.
    """
    return {
        "construction_id": identifiant,
        "layers_outside_to_inside": [
            {
                "material_id": couche["material"],
                "thickness_m": couche["thickness_m"],
                "conductivity_w_mk": couche["conductivity_w_mk"],
                "density_kg_m3": couche["density_kg_m3"],
                "specific_heat_j_kgk": couche["specific_heat_j_kgk"],
            }
            for couche in reversed(couches_interieur_vers_exterieur)
        ],
        "surface_properties": {
            "inside_ir_emissivity": emissivite,
            "outside_ir_emissivity": emissivite,
            "inside_solar_absorptance": absorptance,
            "outside_solar_absorptance": absorptance,
        },
    }


def construire(chemin_source):
    """Builds the binding artefact payload.

    Args:
        chemin_source: Absolute path to `iso52016_chapter7_confirmed_inputs.json`.

    Returns:
        dict: Payload ready to write.

    Raises:
        AssertionError: If the two emissivity derivations do not converge,
            rather than writing a value only one calculation supports.
    """
    with io.open(chemin_source, encoding="utf-8") as flux:
        source = json.load(flux)
    cellule = source["hourly_test_cell"]
    geometrie = cellule["geometry"]
    fenetres = geometrie["windows"]
    bornes = cellule["solar_and_boundary_conditions"]
    coefficients = bornes["combined_surface_coefficients_w_m2k"]
    detail = bornes["surface_coefficients_w_m2k"]
    absorptance = bornes["opaque_solar_absorptance"]

    # The source gives the radiative shares by orientation. They are equal
    # across all three, and the derivation only holds if they remain so: a
    # revised source that differentiates them would invalidate the single emissivity.
    radiatifs = {}
    for face in ("internal", "external"):
        valeurs = set(detail["%s_radiative" % face].values())
        assert len(valeurs) == 1, (face, valeurs)
        radiatifs[face] = valeurs.pop()

    # Consistency check of the source itself: each combined coefficient must
    # equal the sum of its convective and radiative parts. All four match
    # exactly; a discrepancy would flag a transcription error before it propagates.
    for cle_combinee, face, orientation in (
        ("wall_internal_horizontal", "internal", "horizontal"),
        ("roof_internal_upwards", "internal", "upwards"),
        ("floor_internal_downwards", "internal", "downwards"),
        ("external_all_directions", "external", "horizontal"),
    ):
        somme = (
            detail["%s_convective" % face][orientation]
            + detail["%s_radiative" % face][orientation]
        )
        assert abs(somme - coefficients[cle_combinee]) < 1e-9, (
            cle_combinee,
            somme,
            coefficients[cle_combinee],
        )

    interieur = emissivite_derivee(radiatifs["internal"], T_INTERIEUR_K)
    exterieur = emissivite_derivee(radiatifs["external"], T_EXTERIEUR_K)
    assert abs(interieur - exterieur) < 0.01, (interieur, exterieur)
    emissivite = round((interieur + exterieur) / 2.0, 2)

    leger = cellule["lightweight_opaque"]
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "primary_source_sha256": _empreinte(chemin_source),
        # Relative to the repository root: the fingerprint is what genuinely
        # links the artefact to its source; the path is only a landmark,
        # and an absolute path would carry one machine's username.
        "primary_source_path": os.path.relpath(chemin_source, _RACINE).replace(
            os.sep, "/"
        ),
        "source_locator": cellule["source_locator"],
        "cell": {
            "width_m": geometrie["width_m"],
            "depth_m": geometrie["depth_m"],
            "height_m": geometrie["height_m"],
            "south_windows": {
                "count": fenetres["count"],
                "width_m": fenetres["width_m"],
                "height_m": fenetres["height_m"],
                "sill_m": fenetres["sill_m"],
                "side_margin_m": fenetres["side_margin_m"],
                "gap_m": fenetres["gap_m"],
            },
        },
        "surface_coefficients_w_m2k": {
            "wall_inside_horizontal": coefficients["wall_internal_horizontal"],
            "roof_inside_upwards": coefficients["roof_internal_upwards"],
            "floor_inside_downwards": coefficients["floor_internal_downwards"],
            "external_all_directions": coefficients["external_all_directions"],
        },
        "lightweight_opaque_constructions": {
            "external_wall": _construction(
                "ISO_CH7_LW_EXTERNAL_WALL",
                leger["wall_layers_inside_to_outside"],
                emissivite,
                absorptance,
            ),
            "roof": _construction(
                "ISO_CH7_LW_ROOF",
                leger["roof_layers_inside_to_outside"],
                emissivite,
                absorptance,
            ),
            "floor": _construction(
                "ISO_CH7_LW_FLOOR",
                leger["floor_layers_inside_to_outside"],
                emissivite,
                absorptance,
            ),
        },
        "status": "PROVISIONAL_VALUES_PRESENT_RECALCULATION_REQUIRED",
        "compliance_claim_allowed": False,
        "declared_provisional_values": [
            {
                "field": (
                    "lightweight_opaque_constructions.*.surface_properties."
                    "inside_ir_emissivity et outside_ir_emissivity"
                ),
                "provisional_value": emissivite,
                "why_not_in_source": (
                    "iso52016_chapter7_confirmed_inputs.json ne porte aucune "
                    "emissivite infrarouge, que le contrat normalise exige "
                    "pour les deux faces de chaque construction opaque."
                ),
                "how_derived": (
                    "epsilon = h_r / (4 sigma T^3) applique aux coefficients "
                    "radiatifs que la source porte : interieur %.2f / %.3f a "
                    "%.2f K = %.4f ; exterieur %.2f / %.4f a %.2f K = %.4f. "
                    "Les deux convergent a %.4f pres, et la valeur retenue est "
                    "leur moyenne arrondie a deux decimales."
                    % (
                        radiatifs["internal"],
                        4.0 * SIGMA * T_INTERIEUR_K**3,
                        T_INTERIEUR_K,
                        interieur,
                        radiatifs["external"],
                        4.0 * SIGMA * T_EXTERIEUR_K**3,
                        T_EXTERIEUR_K,
                        exterieur,
                        abs(interieur - exterieur),
                    )
                ),
                "assumption_to_confirm": (
                    "Les temperatures de reference de ces coefficients "
                    "radiatifs, que la source n'enonce pas : %.2f K a "
                    "l'interieur et %.2f K a l'exterieur."
                    % (T_INTERIEUR_K, T_EXTERIEUR_K)
                ),
                "cleared_by": (
                    "NON resolu par les pages ISO deja capturees. "
                    "iso52016_chapter7_confirmed_inputs.json porte les pages "
                    "123 a 126 seulement, et son bloc "
                    "unresolved_from_current_captures enonce que la page 126 "
                    "dit uniquement qu'une emittance standard est "
                    "implicitement supposee, sans valeur numerique. La valeur "
                    "est donc definie ailleurs dans ISO EN 52016-1:2017, hors "
                    "des pages capturees. Voie subsidiaire : la specification "
                    "parente du cas 600, NREL/TP-472-6231, presente dans le "
                    "depot, qui ne donnerait que le statut PUBLIC_REFERENCE "
                    "selon references/standards/bestest/README.md. "
                    "Registre des demandes externes, point I1."
                ),
            },
        ],
        "claim_guardrail": (
            "Transcription normalisee de la cellule d'essai du chapitre 7. "
            "Elle porte une valeur PROVISOIRE declaree ci-dessus : elle rend "
            "la chaine de generation executable, elle ne fonde aucun resultat, "
            "aucune comparaison SIA et aucune attestation avant recalcul."
        ),
    }


def main(argv=None):
    """Entry point.

    Args:
        argv: Arguments, `sys.argv[1:]` by default.

    Returns:
        int: 0 on success.
    """
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument(
        "--ecrire",
        action="store_true",
        help="Écrit l'artefact ; sinon affiche seulement le résumé.",
    )
    options = analyseur.parse_args(argv)

    source = os.path.join(_RACINE, "config", "iso52016_chapter7_confirmed_inputs.json")
    charge = construire(source)
    provisoire = charge["declared_provisional_values"][0]
    print("  emissivite provisoire : %s" % provisoire["provisional_value"])
    print(
        "  coefficients          : %s"
        % json.dumps(charge["surface_coefficients_w_m2k"], sort_keys=True)
    )
    for nom, bloc in sorted(charge["lightweight_opaque_constructions"].items()):
        print(
            "  %-14s : %s"
            % (
                nom,
                " -> ".join(
                    couche["material_id"] for couche in bloc["layers_outside_to_inside"]
                ),
            )
        )

    cible = os.path.join(
        _RACINE, "refs", "reference-data", "iso52016_chapter7_test_cell.binding.json"
    )
    if not options.ecrire:
        print("  (essai a blanc, rien n'est ecrit)")
        return 0
    with io.open(cible, "w", encoding="utf-8") as flux:
        flux.write(json.dumps(charge, ensure_ascii=False, indent=2) + "\n")
    print("  ecrit : %s" % cible)
    print("  sha256: %s" % _empreinte(cible))
    return 0


if __name__ == "__main__":
    sys.exit(main())
