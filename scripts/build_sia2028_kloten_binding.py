# -*- coding: utf-8 -*-
"""Writes the normalised binding artefact for the SIA 2028 Kloten test climate.

WHY THIS SCRIPT EXISTS. This artefact had been written by hand, which left the
proof chain ending at a file nobody knew how to remake, and with absolute paths
carrying one machine's username. It is now generated, hence reproducible and
portable.

TWO PROPERTIES THAT MATTER HERE.

1. **Relative paths.** The consumer resolves `weather_file.path` relative to
   the binding artefact's own directory, and the manifest resolves the binding
   path relative to the report's directory. Relative paths are therefore both
   portable and exact; an absolute path would not survive another clone.

2. **The EPW is not in the repository, and that is intentional.** `.gitignore`
   excludes `generated_weather/`: these are derived artefacts, regenerable from
   the tracked official sources. The artefact therefore explicitly declares the
   command that regenerates the EPW, so a fresh clone knows what to run instead
   of discovering a missing file.

WHAT IT DOES NOT DO. It converts nothing: conversion is the work of
`swiss_sia.sia_dry_epw`, whose derivation sheet is re-read here to carry
its checks forward rather than copying them from memory.
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

SCHEMA_ID = "sia4010.sia2028_hourly_weather.v1"
SCHEMA_VERSION = "1.0"

#: Command that regenerates the EPW from the tracked official source.
COMMANDE_REGENERATION = "python Convert_MeteoSwiss_Station_Weather.py --station KLO"


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


def _relatif(chemin, base):
    """Returns a relative path with POSIX separators.

    Args:
        chemin: Absolute path to the target.
        base: Reference directory.

    Returns:
        str: Portable relative path.
    """
    return os.path.relpath(chemin, base).replace(os.sep, "/")


def construire(racine, repertoire_sortie):
    """Builds the weather binding payload.

    Args:
        racine: Repository root.
        repertoire_sortie: Directory where the artefact will be written; used as
            the base for relative paths, because that is the base the consumer
            applies.

    Returns:
        dict: Payload ready to write.

    Raises:
        AssertionError: If the EPW or derivation sheet are missing, rather than
            writing a binding that points into a void.
    """
    source = os.path.join(racine, "references", "standards", "sia2028", "KLO_dry.txt")
    dossier = os.path.join(racine, "generated_weather", "KLO")
    epw = os.path.join(dossier, "KLO_SIA2028_DRY_NORMAL_IESVE_CANDIDATE.epw")
    derivation_path = os.path.join(
        dossier, "KLO_SIA2028_DRY_NORMAL_IESVE_DERIVATION.json"
    )

    assert os.path.isfile(source), source
    assert os.path.isfile(epw), (
        "EPW absent. C'est un artefact derive, exclu du depot par "
        "convention ; regenerez-le avec : %s" % COMMANDE_REGENERATION
    )
    assert os.path.isfile(derivation_path), derivation_path

    with io.open(derivation_path, encoding="utf-8") as flux:
        derivation = json.load(flux)

    # The hour count is measured from the file, not declared: a truncated EPW
    # must cause the binding to fail, not pass through.
    with io.open(epw, encoding="utf-8", errors="replace") as flux:
        lignes = [ligne for ligne in flux if ligne.strip()]
    heures = len(lignes) - 8
    assert heures == 8760, heures

    controles = derivation.get("controls") or derivation.get("controles") or {}
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "primary_source_sha256": _empreinte(source),
        "primary_source_path": _relatif(source, repertoire_sortie),
        "station_name": "Zurich-Kloten",
        "dataset_identity": ("SIA 2028 DRY normal, Zurich-Kloten, 8760 hourly records"),
        "source_locator": (
            "KLO_dry.txt supplied directly by Prof. Gerhard Zweifel, SIA 4010 "
            "validation contact, in answer to the candidate's request; "
            "converted by swiss_sia.sia_dry_epw.v1"
        ),
        "weather_file": {
            "path": _relatif(epw, repertoire_sortie),
            "sha256": _empreinte(epw),
            "format": "EPW",
            "hour_count": heures,
        },
        "conversion_record": {
            "path": _relatif(derivation_path, repertoire_sortie),
            "method": "swiss_sia.sia_dry_epw.v1",
            "controls": controles,
        },
        "derived_artifact_not_in_repository": {
            "why": (
                "generated_weather/ is excluded by .gitignore: converted "
                "weather candidates are derived artifacts, regenerable from "
                "the tracked official sources under references/standards/."
            ),
            "regenerate_with": COMMANDE_REGENERATION,
            "source_of_truth": _relatif(source, repertoire_sortie),
        },
        "claim_guardrail": (
            "Assignable transport conversion of an official SIA-supplied "
            "dataset. It is not an SIA-issued EPW, and its presence proves no "
            "simulation result and no validation."
        ),
        "declared_incompleteness": {
            "columns_to_verify": [
                "This is a transport conversion of an official dataset, not an "
                "official SIA-issued EPW.",
                "Columns marked TO_VERIFY in the provenance record must not "
                "drive a regulatory result until the legend is confirmed in "
                "writing.",
                "IESVE WeatherFileReader read-back is mandatory before " "assignment.",
                "This is the SIA 4010 test climate. It is not the CH2018 "
                "RCP 8.5 '2035' application climate of clause 3.1.1.",
            ],
            "written_as_epw_missing": {
                "total_sky_cover": (
                    "column nto000sw is NA on 7665 of 8760 hours; written as "
                    "the EPW sentinel 99 rather than estimated. The supplied "
                    "horizontal infrared is what the solver uses for sky "
                    "longwave."
                ),
                "ground_albedo": (
                    "column bodenalbedo is supplied but its legend is "
                    "unconfirmed; not written as the EPW albedo field"
                ),
                "others": "EPW documented missing-value sentinels",
            },
        },
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

    sortie_dir = os.path.join(_RACINE, "references", "standards", "sia2028")
    charge = construire(_RACINE, sortie_dir)
    print("  heures comptees : %d" % charge["weather_file"]["hour_count"])
    print("  epw             : %s" % charge["weather_file"]["path"])
    print("  source          : %s" % charge["primary_source_path"])

    cible = os.path.join(sortie_dir, "KLO_SIA2028_DRY_NORMAL.binding.json")
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
