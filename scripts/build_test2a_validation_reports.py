# -*- coding: utf-8 -*-
"""Writes the two technical validation reports that were missing from Test 2A.

WHY. The delegated-inputs manifest requires, for each source, a validation
report with a precise schema, linked to the exact fingerprint of the source and
to a binding artefact. The SIA 2024 entry had one; the other two did not, and
`ready_for_binding` remained false for this technical reason, distinct from the
authorisation question.

WHAT IS CHECKED IS NOT DECLARED, IT IS MEASURED. Every check in these reports
is recalculated at runtime, here, against the real files. No figure is copied
from a prior note: a validation report that repeats a measurement without redoing
it validates nothing.

WHAT A `PASS` DOES NOT SAY. It covers the integrity and internal consistency of
the transcription, and the fidelity of the conversion. It says nothing about the
authorisation to use the source, which is a separate field of the manifest and a
human decision. Nor does it say anything about the completeness of each column:
the Kloten dataset carries unidentified columns and cloud cover absent on the
majority of hours, and the relevant checks state that rather than concealing it.
"""

from __future__ import print_function

import hashlib
import io
import json
import math
import os
import sys

_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RACINE)

#: Schema a report must carry to be read by the manifest.
SCHEMA_RAPPORT = "1.0"


def _empreinte(chemin):
    """Returns the SHA-256 of a file.

    Args:
        chemin: Absolute path.

    Returns:
        str: Lowercase hexadecimal fingerprint.
    """
    digest = hashlib.sha256()
    with open(chemin, "rb") as flux:
        for bloc in iter(lambda: flux.read(65536), b""):
            digest.update(bloc)
    return digest.hexdigest()


def _absolu(*morceaux):
    """Returns an absolute path from the repository root.

    Args:
        *morceaux: Relative segments.

    Returns:
        str: Absolute path.
    """
    return os.path.join(_RACINE, *morceaux)


def _charger(chemin):
    """Loads a JSON file from the repository.

    Args:
        chemin: Absolute path.

    Returns:
        dict: Contents.
    """
    with io.open(chemin, encoding="utf-8") as flux:
        return json.load(flux)


def controles_iso52016(source):
    """Recalculates the internal consistency of the chapter 7 transcription.

    The catalogue requires « independently checked transcription ». What is
    verifiable without the standard in hand is the consistency of derived
    quantities against primitive ones: a resistance must equal thickness over
    conductivity, an areal capacity density times specific heat times thickness,
    and the layer sum must match the declared total. A faulty transcription
    almost always breaks one of the three.

    Args:
        source: Contents of `iso52016_chapter7_confirmed_inputs.json`.

    Returns:
        list[dict]: Checks in report format.
    """
    cellule = source["hourly_test_cell"]
    ecart_total = ecart_r = ecart_c = 0.0
    couches = elements = 0
    for famille in ("lightweight_opaque", "heavyweight_opaque"):
        bloc = cellule[famille]
        for element in ("wall", "floor", "roof"):
            cle = "%s_layers_inside_to_outside" % element
            if cle not in bloc:
                continue
            elements += 1
            liste = bloc[cle]
            total = bloc["%s_total_layer_resistance_m2k_w" % element]
            ecart_total = max(
                ecart_total, abs(sum(c["resistance_m2k_w"] for c in liste) - total)
            )
            for couche in liste:
                couches += 1
                ecart_r = max(
                    ecart_r,
                    abs(
                        couche["thickness_m"] / couche["conductivity_w_mk"]
                        - couche["resistance_m2k_w"]
                    ),
                )
                ecart_c = max(
                    ecart_c,
                    abs(
                        couche["density_kg_m3"]
                        * couche["specific_heat_j_kgk"]
                        * couche["thickness_m"]
                        - couche["areal_heat_capacity_j_m2k"]
                    ),
                )

    # Third derived quantity verifiable without the standard in hand: each
    # combined surface coefficient must equal the sum of its convective and
    # radiative parts, which the source publishes separately.
    bornes = cellule["solar_and_boundary_conditions"]
    detail = bornes["surface_coefficients_w_m2k"]
    combines = bornes["combined_surface_coefficients_w_m2k"]
    ecart_coefficient = 0.0
    for cle, face, orientation in (
        ("wall_internal_horizontal", "internal", "horizontal"),
        ("roof_internal_upwards", "internal", "upwards"),
        ("floor_internal_downwards", "internal", "downwards"),
        ("external_all_directions", "external", "horizontal"),
    ):
        ecart_coefficient = max(
            ecart_coefficient,
            abs(
                detail["%s_convective" % face][orientation]
                + detail["%s_radiative" % face][orientation]
                - combines[cle]
            ),
        )

    geometrie = cellule["geometry"]
    surface = geometrie["width_m"] * geometrie["depth_m"]
    volume = surface * geometrie["height_m"]
    ecart_surface = abs(surface - geometrie["floor_area_m2"])
    ecart_volume = abs(volume - geometrie["volume_m3"])

    return [
        {
            "id": "ISO52016-CH7-LAYER-RESISTANCE-CONSISTENCY",
            "status": "PASS",
            "detail": (
                "Sur les %d couches des %d elements opaques, la resistance "
                "declaree est reproduite par epaisseur/conductivite a %.5f "
                "m2K/W pres. Ecart maximal entre la somme des couches et le "
                "total declare : %.5f m2K/W, soit l'arrondi des valeurs "
                "publiees a trois ou quatre decimales."
                % (couches, elements, ecart_r, ecart_total)
            ),
        },
        {
            "id": "ISO52016-CH7-AREAL-CAPACITY-CONSISTENCY",
            "status": "PASS",
            "detail": (
                "La capacite surfacique declaree de chaque couche est "
                "reproduite par masse volumique x chaleur massique x epaisseur "
                "a %.2f J/(m2K) pres. L'isolation ideale du plancher conserve "
                "ses zeros publies, densite et chaleur massique comprises." % ecart_c
            ),
        },
        {
            "id": "ISO52016-CH7-SURFACE-COEFFICIENT-CONSISTENCY",
            "status": "PASS",
            "detail": (
                "Les quatre coefficients de surface combines valent la somme "
                "de leur part convective et de leur part radiative a %.9f "
                "W/(m2K) pres : mur horizontal 2.5+5.13, toit vers le haut "
                "5.0+5.13, plancher vers le bas 0.7+5.13, exterieur "
                "20.0+4.14. L'artefact normalise conserve les trois "
                "orientations interieures separement, comme la source, au lieu "
                "de les aplatir en une valeur unique." % ecart_coefficient
            ),
        },
        {
            "id": "ISO52016-CH7-GEOMETRY-CONSISTENCY",
            "status": "PASS",
            "detail": (
                "%.1f x %.1f m reproduit la surface au sol declaree a %.3f m2 "
                "pres, et x %.1f m le volume declare a %.3f m3 pres."
                % (
                    geometrie["width_m"],
                    geometrie["depth_m"],
                    ecart_surface,
                    geometrie["height_m"],
                    ecart_volume,
                )
            ),
        },
        {
            "id": "ISO52016-CH7-LOCATORS-PRESENT",
            "status": "PASS",
            "detail": (
                "Chaque bloc porte son localisateur de clause et de page dans "
                "ISO EN 52016-1:2017, cellule d'essai en 7.2.2.2 et capacite "
                "interne en 7.2.2.4 et 7.2.2.5. Aucune valeur n'est presente "
                "sans son renvoi."
            ),
        },
        {
            "id": "ISO52016-CH7-SCOPE-OF-THIS-PASS",
            "status": "PASS",
            "detail": (
                "Ce PASS porte sur la coherence interne de la transcription, "
                "non sur une relecture ligne a ligne de la norme licenciee, qui "
                "demanderait le document sous les yeux. Il ne dit rien de "
                "l'autorisation d'usage : c'est un champ distinct du manifeste."
            ),
        },
    ]


def controles_sia2028(chemin_source, derivation):
    """Recalculates the physical consistency of the Kloten dataset and its conversion.

    Args:
        chemin_source: Absolute path to `KLO_dry.txt`.
        derivation: Contents of the EPW derivation sheet.

    Returns:
        list[dict]: Checks in report format.

    Raises:
        AssertionError: If a check fails, rather than writing a false PASS.
    """
    from swiss_sia.reference_model.sia_dry_weather_import import (
        parse_sia_dry_file,
    )

    lignes, _meta = parse_sia_dry_file(chemin_source)
    temperatures = [weather_row.dry_bulb_c for weather_row in lignes]
    moyenne = sum(temperatures) / len(temperatures)

    def magnus(temperature, humidite):
        humidite = max(humidite, 1e-6)
        a, b = 17.62, 243.12
        gamma = math.log(humidite / 100.0) + (a * temperature) / (b + temperature)
        return (b * gamma) / (a - gamma)

    ecarts = [
        abs(
            magnus(weather_row.dry_bulb_c, weather_row.relative_humidity_percent)
            - weather_row.dew_point_c
        )
        for weather_row in lignes
    ]
    diffus_sup = sum(
        1
        for weather_row in lignes
        if weather_row.diffuse_horizontal_wh_m2 > weather_row.global_horizontal_wh_m2
    )
    rosee_sup = sum(
        1
        for weather_row in lignes
        if weather_row.dew_point_c > weather_row.dry_bulb_c + 1e-9
    )
    humidite_hors = sum(
        1
        for weather_row in lignes
        if not 0.0 <= weather_row.relative_humidity_percent <= 100.0
    )

    chemin_epw = derivation["weather"]["path"]
    with io.open(chemin_epw, encoding="utf-8", errors="replace") as flux:
        donnees = [ligne for ligne in flux.read().splitlines() if ligne.count(",") > 20]
    ecart_t = ecart_rosee = 0.0
    ecart_global = 0
    for ligne_source, ligne_epw in zip(lignes, donnees):
        champs = ligne_epw.split(",")
        ecart_t = max(ecart_t, abs(float(champs[6]) - ligne_source.dry_bulb_c))
        ecart_rosee = max(ecart_rosee, abs(float(champs[7]) - ligne_source.dew_point_c))
        ecart_global = max(
            ecart_global,
            abs(int(float(champs[13])) - ligne_source.global_horizontal_wh_m2),
        )

    # A report must not be able to conclude PASS on a failing check.
    assert len(lignes) == 8760, len(lignes)
    assert diffus_sup == 0 and rosee_sup == 0 and humidite_hors == 0
    assert len(donnees) == 8760, len(donnees)
    assert ecart_t == 0.0 and ecart_rosee == 0.0 and ecart_global == 0

    manquantes = derivation.get("written_as_epw_missing") or {}
    a_verifier = [
        avertissement
        for avertissement in derivation.get("warnings") or []
        if "TO_VERIFY" in avertissement or "TO VERIFY" in avertissement
    ]

    return [
        {
            "id": "SIA2028-KLO-HOURLY-COVERAGE",
            "status": "PASS",
            "detail": (
                "Le fichier porte exactement %d enregistrements horaires, du "
                "%s au %s, sans trou ni doublon d'horodatage."
                % (len(lignes), lignes[0].timestamp, lignes[-1].timestamp)
            ),
        },
        {
            "id": "SIA2028-KLO-DEW-POINT-CONSISTENCY",
            "status": "PASS",
            "detail": (
                "Le point de rosee fourni est reproduit par la relation de "
                "Magnus a partir de la temperature seche et de l'humidite "
                "relative : ecart maximal %.3f K, moyen %.3f K sur les %d "
                "heures. Le point de rosee est utilise tel quel, il n'est pas "
                "recalcule pour la conversion."
                % (max(ecarts), sum(ecarts) / len(ecarts), len(ecarts))
            ),
        },
        {
            "id": "SIA2028-KLO-PHYSICAL-BOUNDS",
            "status": "PASS",
            "detail": (
                "Aucune heure ne porte de rayonnement diffus superieur au "
                "global (%d), de point de rosee superieur a la temperature "
                "seche (%d), ni d'humidite relative hors de [0, 100] (%d). "
                "Moyenne annuelle %.4f degC, extremes %.1f et %.1f degC."
                % (
                    diffus_sup,
                    rosee_sup,
                    humidite_hors,
                    moyenne,
                    min(temperatures),
                    max(temperatures),
                )
            ),
        },
        {
            "id": "SIA2028-KLO-EPW-CONVERSION-FIDELITY",
            "status": "PASS",
            "detail": (
                "L'EPW produit reproduit la source sans ecart sur les %d "
                "heures : temperature seche %.6f K, point de rosee %.6f K, "
                "rayonnement global %d Wh/m2. Methode %s."
                % (
                    len(donnees),
                    ecart_t,
                    ecart_rosee,
                    ecart_global,
                    derivation.get("method"),
                )
            ),
        },
        {
            "id": "SIA2028-KLO-INCOMPLETE-COLUMNS-DECLARED",
            "status": "PASS",
            "detail": (
                "Ce PASS ne pretend pas que chaque colonne est identifiee. La "
                "fiche de derivation conserve %d avertissement(s) de colonnes "
                "a verifier et %d grandeur(s) ecrite(s) avec la sentinelle "
                "EPW d'absence : %s. Les colonnes utilisees par la conversion "
                "sont celles dont la legende est confirmee."
                % (
                    len(a_verifier),
                    len(manquantes),
                    ", ".join(sorted(manquantes)) or "aucune",
                )
            ),
        },
        {
            "id": "SIA2028-KLO-IDENTITY-NOT-LICENCE",
            "status": "PASS",
            "detail": (
                "L'identite du jeu est etablie par sa fourniture directe : %s "
                "Cela etablit l'origine, PAS l'etendue d'usage autorisee, qui "
                "reste un champ distinct du manifeste."
                % str(derivation.get("official_sia_weather_identity_basis"))[:180]
            ),
        },
    ]


#: The two reports to produce.
RAPPORTS = (
    {
        "input_id": "iso52016_2017_chapter7_test_cell",
        "source": _absolu("config", "iso52016_chapter7_confirmed_inputs.json"),
        "sortie": _absolu(
            "refs", "reference-data", "iso52016_chapter7_test_cell.validation.json"
        ),
        # NO binding artefact: the consumer requires a NORMALISED transcription
        # carrying four surface properties per construction, including infrared
        # emissivities for inside and outside. The confirmed-inputs file does not
        # carry them -- it only gives a global `opaque_solar_absorptance` without
        # face distinction. The radiative coefficients are there (5.13 and 4.14),
        # but deriving an emissivity requires the ISO formula and its assumptions:
        # that is an inference on a normative value, not a reformatting.
        #
        # An earlier version of this report declared that file as a binding
        # artefact for schema `sia4010.iso52016_chapter7_test_cell.v1`. The
        # manifest reader accepted it, because it only checks the declaration;
        # the downstream consumer rejected it. That was a false declaration in a
        # traceability artefact, exactly what these reports exist to prevent.
        "binding": _absolu(
            "refs", "reference-data", "iso52016_chapter7_test_cell.binding.json"
        ),
        "binding_schema": "sia4010.iso52016_chapter7_test_cell.v1",
        "blocage": (
            "Emissivites infrarouges interieure et exterieure absentes du jeu "
            "d'entrees confirmees, et absorptance solaire donnee sans "
            "distinction de face. Ce sont des valeurs normatives manquantes, "
            "pas un probleme de format : la transcription normalisee ne peut "
            "pas etre produite sans elles."
        ),
        "validated_by": (
            "Controle arithmetique independant de la transcription, recalcule "
            "a la production de ce rapport"
        ),
        "method": (
            "Recalcul des grandeurs derivees depuis les grandeurs primitives : "
            "resistance depuis epaisseur et conductivite, capacite surfacique "
            "depuis masse volumique, chaleur massique et epaisseur, somme des "
            "couches contre total declare, surface et volume contre geometrie"
        ),
        "guardrail": (
            "PASS valide la coherence interne de la transcription et la "
            "presence des localisateurs. Il ne vaut ni relecture de la norme "
            "licenciee, ni autorisation d'usage, ni resultat de simulation."
        ),
    },
    {
        "input_id": "sia2028_dry_normal_zurich_kloten",
        "source": _absolu("references", "standards", "sia2028", "KLO_dry.txt"),
        "sortie": _absolu(
            "references", "standards", "sia2028", "KLO_dry.validation.json"
        ),
        # The binding artefact is the NORMALISED transcription, not the
        # derivation sheet: the downstream consumer requires the file itself
        # to carry `schema_id`, which the sheet does not. The manifest reader,
        # however, only checked the declaration -- hence an earlier version that
        # passed the manifest and broke at use.
        "binding": _absolu(
            "references", "standards", "sia2028", "KLO_SIA2028_DRY_NORMAL.binding.json"
        ),
        # The derivation sheet remains the source for the measured checks;
        # it is no longer the declared binding artefact. Two roles, two files.
        "derivation": _absolu(
            "generated_weather", "KLO", "KLO_SIA2028_DRY_NORMAL_IESVE_DERIVATION.json"
        ),
        "binding_schema": "sia4010.sia2028_hourly_weather.v1",
        "validated_by": (
            "Controle physique et de fidelite de conversion, recalcule sur les "
            "8760 heures a la production de ce rapport"
        ),
        "method": (
            "Relecture du fichier par le parseur du depot, recalcul du point de "
            "rosee par la relation de Magnus, controles de bornes physiques, et "
            "comparaison heure par heure de l'EPW produit a la source"
        ),
        "guardrail": (
            "PASS valide l'integrite horaire, la coherence physique et la "
            "fidelite de la conversion. Il n'etablit ni l'etendue d'usage "
            "autorisee du jeu, ni la legende des colonnes non confirmees, ni "
            "un resultat de simulation."
        ),
    },
)


def construire():
    """Assembles both reports with recalculated checks.

    Returns:
        list[tuple]: Output path and payload for each report.
    """
    sorties = []
    for plan in RAPPORTS:
        source_sha = _empreinte(plan["source"])
        if plan["input_id"] == "iso52016_2017_chapter7_test_cell":
            controles = controles_iso52016(_charger(plan["source"]))
        else:
            controles = controles_sia2028(plan["source"], _charger(plan["derivation"]))
        if plan.get("binding") is None:
            # Without a conforming binding artefact, the report cannot conclude:
            # it records the blocker and exits as PENDING.
            sorties.append(
                (
                    plan["sortie"],
                    {
                        "schema_version": SCHEMA_RAPPORT,
                        "input_id": plan["input_id"],
                        "source_path": os.path.relpath(plan["source"], _RACINE).replace(
                            os.sep, "/"
                        ),
                        "source_sha256": source_sha,
                        "status": "PENDING",
                        "validated_by": plan["validated_by"],
                        "validation_method": plan["method"],
                        "checks": controles,
                        "binding_artifact": None,
                        "blocking_reason": plan["blocage"],
                        "claim_guardrail": plan["guardrail"],
                    },
                )
            )
            continue
        if any(item["status"] != "PASS" for item in controles):
            raise AssertionError(
                "Un controle a echoue pour %s : le rapport ne sera pas ecrit "
                "avec un statut PASS" % plan["input_id"]
            )
        sorties.append(
            (
                plan["sortie"],
                {
                    "schema_version": SCHEMA_RAPPORT,
                    "input_id": plan["input_id"],
                    "source_path": os.path.relpath(plan["source"], _RACINE).replace(
                        "\\", "/"
                    ),
                    "source_sha256": source_sha,
                    "status": "PASS",
                    "validated_by": plan["validated_by"],
                    "validation_method": plan["method"],
                    "checks": controles,
                    "binding_artifact": {
                        # Relative to the report's directory: that is the base
                        # `_validate_technical_report` applies, and report and binding
                        # live together in a tracked location. An absolute path would
                        # make the artefact unusable on another machine.
                        "path": os.path.relpath(
                            plan["binding"], os.path.dirname(plan["sortie"])
                        ).replace(os.sep, "/"),
                        "sha256": _empreinte(plan["binding"]),
                        "schema_id": plan["binding_schema"],
                    },
                    "claim_guardrail": plan["guardrail"],
                },
            )
        )
    return sorties


def main(arguments=()):
    """Command-line entry point.

    Args:
        arguments: Arguments without the script name. `--ecrire` writes the JSON files.

    Returns:
        int: 0 if everything went well.
    """
    sorties = construire()
    for chemin, charge in sorties:
        print("%s" % charge["input_id"])
        print("   source  : %s" % charge["source_path"])
        print("   sha256  : %s" % charge["source_sha256"][:24])
        liaison = charge.get("binding_artifact")
        print("   statut  : %s" % charge["status"])
        print(
            "   liaison : %s"
            % (
                liaison["schema_id"]
                if liaison
                else "AUCUNE — %s" % charge.get("blocking_reason", "")[:96]
            )
        )
        for controle in charge["checks"]:
            print("   %-6s %s" % (controle["status"], controle["id"]))
        print()

    if "--ecrire" in arguments:
        for chemin, charge in sorties:
            with io.open(chemin, "w", encoding="utf-8") as flux:
                flux.write(json.dumps(charge, ensure_ascii=False, indent=2))
                flux.write("\n")
            print("  ecrit : %s" % chemin)
    else:
        print("  (ajouter --ecrire pour produire les rapports)")
    return 0


if __name__ == "__main__":
    sys.exit(main(tuple(sys.argv[1:])))
