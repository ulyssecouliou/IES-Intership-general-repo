# -*- coding: utf-8 -*-
u"""Freezes the SN EN 14825:2018 cooling-SEER reference data.

Why a build script (not a hand-written JSON): refs/reference-data/ files must be
produced by code that RECOMPUTES and CONFRONTS the transcribed values to their
source, so the proof chain required by CLAUDE.md rule 2 holds.

SN EN 14825:2018 is licensed and is NOT in refs/ (it may not be redistributed).
The numeric content here is transcribed from targeted screenshots of the
published document provided by the user on 2026-08-20 (Clause 1, Clause 3.1,
Clause 4 tables 2-5, Annex A table A.1). This mirrors the sia-387-4-2017 blinds
reference, which was likewise frozen from provided captures.

CROSS-CHECKS performed here before writing (fail -> no write):
  1. The four cooling part-load ratios are RECOMPUTED from their temperatures via
     the standard's own formula (Tj-16)/(Tdesignc-16) with Tdesignc=35 C and
     confronted to the transcribed percentages (Table 2), to 2 decimals.
  2. The reference cooling season bin hours (Table A.1) are summed and confronted
     to the transcribed total.
  3. SIA 380/2:2022 table 5 (page PDF 38) is confirmed to defer the SEER column
     to SN EN 14825 -- recorded as the normative link that makes a declared SEER
     comparable to the SIA band (voie A).

Usage:
    python scripts/build_sn_en_14825_seer.py            # display + cross-check
    python scripts/build_sn_en_14825_seer.py --ecrire   # + write JSON
"""

from __future__ import print_function

import json
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
_SORTIE = os.path.join(_RACINE, "refs", "reference-data",
                       "sn-en-14825-2018.cooling-seer.json")

T_DESIGN_C = 35  # reference design temperature for cooling (Clause 4.1)

# Transcribed from Table 2 (outdoor air-to-recycled air). The part-load ratios
# are the same across tables 2-5; only the exchanger temperatures differ.
POINTS_FROID = [
    {"point": "A", "T_ext_C": 35, "taux_transcrit": 100.00},
    {"point": "B", "T_ext_C": 30, "taux_transcrit": 73.68},
    {"point": "C", "T_ext_C": 25, "taux_transcrit": 47.37},
    {"point": "D", "T_ext_C": 20, "taux_transcrit": 21.05},
]

# Transcribed from Table A.1 (== Table D.1 "Average"): reference cooling season.
BINS_FROID = [
    (1, 17, 205), (2, 18, 227), (3, 19, 225), (4, 20, 225), (5, 21, 216),
    (6, 22, 215), (7, 23, 218), (8, 24, 197), (9, 25, 178), (10, 26, 158),
    (11, 27, 137), (12, 28, 109), (13, 29, 88), (14, 30, 63), (15, 31, 39),
    (16, 32, 31), (17, 33, 24), (18, 34, 17), (19, 35, 13), (20, 36, 9),
    (21, 37, 4),
]
TOTAL_HEURES_TRANSCRIT = 2598


def _cross_check():
    """Recompute part-load ratios and bin-hour total; raise on any mismatch."""
    for pt in POINTS_FROID:
        recompute = round(
            (pt["T_ext_C"] - 16.0) / (T_DESIGN_C - 16.0) * 100.0, 2
        )
        if abs(recompute - pt["taux_transcrit"]) > 0.01:
            raise SystemExit(
                "CROSS-CHECK FAILED: point {} ratio recomputed {} != transcribed {}"
                .format(pt["point"], recompute, pt["taux_transcrit"])
            )
    total = sum(h for _, _, h in BINS_FROID)
    if total != TOTAL_HEURES_TRANSCRIT:
        raise SystemExit(
            "CROSS-CHECK FAILED: bin-hour sum {} != transcribed total {}"
            .format(total, TOTAL_HEURES_TRANSCRIT)
        )
    return total


def _build(total_heures):
    return {
        "norme": "SN EN 14825:2018",
        "titre": (
            u"Climatiseurs, groupes refroidisseurs de liquides et pompes à "
            u"chaleur, avec compresseur entraîné par moteur électrique — "
            u"Essais et détermination des caractéristiques à charge partielle "
            u"et calcul des performances saisonnières"
        ),
        "portee_de_ce_fichier": (
            u"Base numérique du SEER (froid) référencée par SIA 380/2:2022 "
            u"tableau 5. Localisateur de traçabilité interne, PAS une "
            u"redistribution du standard."
        ),
        "statut": (
            u"FIGÉ pour le SEER froid (voie A : SEER déclaré fabricant). "
            u"SCOP chaud NON figé (tables 6-9 reçues, clause de calcul chaud "
            u"non vérifiée)."
        ),
        "date_extraction": "2026-08-20",
        "genere_par": "scripts/build_sn_en_14825_seer.py",
        "source": {
            "nature": u"captures d'écran ciblées du document publié",
            "fournisseur": u"utilisateur (accès SN EN 14825:2018)",
            "date_reception": "2026-08-20",
            "elements": [
                "Clause 1 (Scope)",
                "Clause 3.1.1 (active mode), 3.1.2 (SCOPon), 3.1.72 (reference cooling season)",
                "Clause 4 - tableaux 2 a 5 (part load conditions for space cooling)",
                "Annexe A - tableau A.1 (bins de la saison de refroidissement de reference)",
            ],
        },
        "lien_sia_380_2": {
            "citation": (
                u"SIA 380/2:2022 FR, tableau 5, page PDF 38 : colonnes "
                u"« EER à pleine charge — valeur minimale » ET "
                u"« SEER selon SN EN 14825 — valeur minimale »."
            ),
            "reference_normative": (
                u"SIA 380/2:2022 FR, page PDF 6 : SN EN 14825:2018 listée comme "
                u"référence normative."
            ),
            "consequence": (
                u"Le seuil SEER de SIA 380/2 tableau 5 est défini SELON EN 14825:2018. "
                u"Un SEER déclaré fabricant (ErP/Ecodesign, calculé selon EN 14825) "
                u"est donc directement comparable à la bande SEER de SIA."
            ),
        },
        "champ_application": {
            "texte": (
                "air conditioners, heat pumps and liquid chilling packages, "
                "including comfort and process chillers; factory made units per "
                "EN 14511-1; DX-to-water(brine) per EN 15879-1; hybrid units."
            ),
            "grandeurs_definies": [
                "SEER", "SEERon", "eta_s_c", "SCOP", "SCOPon", "SCOPnet",
                "eta_s_h", "SEPR",
            ],
        },
        "conditions_charge_partielle_froid": {
            "source": "tableau 2 (outdoor air-to-recycled air); tableaux 3-5 pour water/brine et air-to-water",
            "temperature_design_froid_C": T_DESIGN_C,
            "temperature_interieure_C": "27 (19 bulbe humide)",
            "formule_taux_charge": "(T_ext - 16) / (Tdesignc - 16)",
            "points": [
                {
                    "point": pt["point"],
                    "taux_charge_pourcent": pt["taux_transcrit"],
                    "T_ext_C": pt["T_ext_C"],
                }
                for pt in POINTS_FROID
            ],
        },
        "saison_de_refroidissement_de_reference": {
            "source": "tableau A.1 (identique au tableau D.1, colonne Average)",
            "unite_T": "degC",
            "unite_heures": "h",
            "total_heures": total_heures,
            "bins": [
                {"j": j, "T_j": t, "h_j": h} for (j, t, h) in BINS_FROID
            ],
        },
        "voie_de_verification_retenue": {
            "voie": "A - SEER declare fabricant",
            "justification": (
                u"Sur le marché EU/CH, le SEER déclaré (fiche ErP/Ecodesign) est "
                u"calculé selon EN 14825 par obligation réglementaire ; il est donc "
                u"EN 14825 par construction et comparable à la bande SIA sans recalcul. "
                u"La clause de calcul (agrégation SEERon + Cd) n'est nécessaire que "
                u"pour la voie B (recalcul depuis les 4 points A/B/C/D), non retenue."
            ),
            "reserve_restante": (
                u"Si le SEER provient du calcul interne de VE (et non d'une fiche), "
                u"il faut confirmer que VE calcule selon EN 14825. Un SEER déclaré "
                u"fabricant ne porte pas cette réserve."
            ),
        },
    }


def main():
    total = _cross_check()
    payload = _build(total)
    print("SN EN 14825:2018 cooling-SEER reference")
    print("  part-load ratios recomputed and confirmed (A/B/C/D).")
    print("  reference cooling season bins:", len(BINS_FROID),
          "total hours:", total)
    print("  output:", _SORTIE)
    if "--ecrire" in sys.argv:
        with open(_SORTIE, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print("  WRITTEN.")
    else:
        print("  (dry run: pass --ecrire to write)")


if __name__ == "__main__":
    main()
