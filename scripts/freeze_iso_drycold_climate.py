# -*- coding: utf-8 -*-
"""Freeze the public climate data of EN ISO 52016-1:2017 (DRYCOLD case).

THE AUTHORITATIVE SOURCE, free and public -- the only one the Test 1
specification names:

    Spezifikation_Test1.pdf : « Klima | DRYCOLD.TMY (BESTEST) Denver, CO /
                                http://standards.iso.org/iso/52016/-1/ed-1 »

The portal holds exactly ONE file:
`ISO_52016_1_BESTEST_ClimData_2016.08.24.xls`. It is NOT a weather file
but a converted hourly table, and it carries two explicit warnings
that change how Test 1 must be run -- see `avertissements_du_fichier`.

WHY THIS SCRIPT EXISTS. The Codex repository carried a file
`DRYCOLD_TMY_ISO_SOURCE_VERIFICATION.json` declaring
`{"status": "PASS", "source_identity_supported": true}` with a SHA-256 digest
that is the digest of a 30-BYTE TEST STUB, not of the real file
of 8760 hours. The attestation certified nothing. This file therefore starts
from the public source, with its digest recomputed here.

That is the failure this whole repository is built against: a document that
LOOKS like verification, carrying a real algorithm and a real-looking digest,
attesting to something that was never checked. Nothing about it reads as
suspicious until someone recomputes the hash.

Usage :
    python scripts/freeze_iso_drycold_climate.py
"""

from __future__ import print_function

import hashlib
import io
import json
import os

import xlrd

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
_XLS = os.path.join(_RACINE, "refs", "ISO_52016_1_BESTEST_ClimData_2016.08.24.xls")
_SORTIE = os.path.join(
    _RACINE, "refs", "reference-data", "iso-52016-1-climat-drycold.json"
)

URL = (
    "https://standards.iso.org/iso/52016/-1/ed-1/"
    "ISO_52016_1_BESTEST_ClimData_2016.08.24.xls"
)

# The eight surfaces on which the file gives irradiance, in the order
# of columns 6 to 13. Labels read from row 4 of the sheet.
SURFACES = ("NV", "EV", "SV", "WV", "N45", "S45", "VOID", "H")

# Row of the first data point, and the length of the warm-up month.
PREMIERE_LIGNE_DONNEES = 5
HEURES_INITIALISATION = 744  # December duplicated at the front

CONSEQUENCE = (
    "Le fichier ISO fournit l'irradiance DÉJÀ CALCULÉE sur huit surfaces "
    "nommées, sans décomposition global / direct / diffus. Les quatre "
    "programmes de référence ont donc été alimentés en irradiance DE SURFACE. "
    "Un .epw fournit global / direct / diffus et laisse le modèle de ciel du "
    "programme dériver les surfaces : l'entrée n'est pas la même. L'écart de "
    "modèle de ciel doit être quantifié AVANT d'interpréter tout écart "
    "thermique, sans quoi on attribuerait au moteur thermique de VE une "
    "divergence d'origine radiative."
)

INITIALISATION = (
    "Les 744 premières heures sont un mois d'initialisation (décembre "
    "recopié). Une simulation VE de 8760 heures partant du 1er janvier ne "
    "reproduit donc PAS l'état initial des programmes de référence. L'effet "
    "est maximal sur les cas à forte masse (900, 940, 900FF). Le "
    "préconditionnement de VE doit être réglé pour refléter ce mois."
)


def _lignes(feuille):
    """Data rows: the ones whose `month` column holds a number."""
    lues = []
    for r in range(PREMIERE_LIGNE_DONNEES, feuille.nrows):
        valeur = feuille.cell_value(r, 1)
        if isinstance(valeur, float):
            lues.append([feuille.cell_value(r, c) for c in range(16)])
    return lues


def construire():
    with open(_XLS, "rb") as f:
        octets = f.read()
    empreinte = hashlib.sha256(octets).hexdigest()

    feuille = xlrd.open_workbook(_XLS).sheet_by_index(0)
    toutes = _lignes(feuille)
    annee = toutes[HEURES_INITIALISATION:]

    avertissements = []
    for r in (0, 1):
        for c in range(feuille.ncols):
            valeur = feuille.cell_value(r, c)
            if isinstance(valeur, str) and valeur.strip():
                avertissements.append(valeur.strip())

    temperatures = [weather_row[5] for weather_row in annee]
    irradiations = dict(
        (nom, round(sum(weather_row[6 + i] for weather_row in annee) / 1000.0, 1))
        for i, nom in enumerate(SURFACES)
    )

    return {
        "source": {
            "norme": "EN ISO 52016-1:2017",
            "element": "données climatiques publiques associées au chapitre 7",
            "fichier": os.path.basename(_XLS),
            "url": URL,
            "octets": len(octets),
            "sha256": empreinte,
            "telecharge_le": "2026-08-05",
            "gratuit": True,
            "auteur_metadonnee_xls": "Thor Endre Lexow, ISO, 2016-08-24",
            "designee_par": "Spezifikation_Test1.pdf, ligne « Klima »",
        },
        "avertissements_du_fichier": avertissements,
        "structure": {
            "lignes_de_donnees": len(toutes),
            "heures_initialisation": HEURES_INITIALISATION,
            "heures_annee": len(annee),
            "mois_initialisation": 12,
            "colonnes": {
                "0": "hours/calc",
                "1": "month",
                "2": "week",
                "3": "day/week",
                "4": "hours/week",
                "5": "theta_e;air [°C]",
                "6-13": "I_sol [W/m2] sur " + ", ".join(SURFACES),
                "14": "v_w [m/s]",
                "15": "H [g/kg]",
            },
        },
        "agregats_annuels": {
            "theta_e_air_c": {
                "min": min(temperatures),
                "max": max(temperatures),
                "moyenne": round(sum(temperatures) / len(temperatures), 4),
            },
            "v_w_m_s_moyenne": round(
                sum(weather_row[14] for weather_row in annee) / len(annee), 4
            ),
            "irradiation_kwh_m2_an": irradiations,
        },
        "consequence_pour_la_validation": CONSEQUENCE,
        "consequence_initialisation": INITIALISATION,
        "attestation_codex_invalidee": {
            "fichier": ".codex_tmp/test_checksum_bound_weather_verification_is_preserved/"
            "DRYCOLD_TMY_ISO_SOURCE_VERIFICATION.json",
            "declarait": '{"status": "PASS", "source_identity_supported": true}',
            "sha256_declare": "95490E30E3CC864D209923DEF3E089F5EF52015742285C79A637340C3F178FDC",
            "ce_que_cette_empreinte_designe": "un stub de test de 30 octets sur une seule ligne, PAS le "
            "fichier réel de 8760 heures (sha256 c33778b4…)",
            "statut": "ATTESTATION SANS VALEUR — remplacée par le présent fichier",
        },
    }


def main():
    donnees = construire()
    with io.open(_SORTIE, "w", encoding="utf-8") as f:
        f.write(json.dumps(donnees, ensure_ascii=False, indent=2))
        f.write("\n")

    source = donnees["source"]
    print("frozen: %s" % os.path.relpath(_XLS, _RACINE))
    print("  %d octets, sha256 %s" % (source["octets"], source["sha256"]))
    print("frozen: %s" % os.path.relpath(_SORTIE, _RACINE))
    print()
    print("reference annual irradiation, kWh/m2:")
    for nom, valeur in donnees["agregats_annuels"]["irradiation_kwh_m2_an"].items():
        print("   %-5s %8.1f" % (nom, valeur))


if __name__ == "__main__":
    main()
