# -*- coding: utf-8 -*-
"""Freezes the diagnostic case chain 1A to 1E for Test 1, from their PDFs.

WHY THIS FILE EXISTS. Case **1E** is the only Test 1 case carrying a pass/fail
criterion, and it cannot be generated: the specification defines it as
« Diagnosefall 1D, jedoch mit Stoffmarkisen-Sonnenschutz », and 1D is itself at
the end of a chain 1A → 1B → 1C → 1D. None of this was frozen, so nobody
could build 1E without guessing. This producer extracts the chain and its
parameters from where they are written.

FOUR SOURCES, FOUR ROLES.

* `Spezifikation_Test1.pdf` states the chain itself (Diag 1A to 1D) and the
  definition of 1E. The German text is extracted **verbatim**: a French
  paraphrase in a reference dataset would be an interpretation disguised as
  data.
* `Spezifikation_Test2.pdf` carries what each link adds — the window,
  infiltration, the SIA 2024 occupancy profile, blind control.
* `Dokumentation_Beispielgebäude_V5.pdf` carries the properties of the whole
  window, blind deployed and retracted — under TWO standard families, which
  matters: the U value is not the same under every standard, and comparing
  against the wrong block causes a difference in standards to appear as a
  contradiction between documents. This is the error an earlier version of
  this producer made, and that `_concordance_du_u` now prevents.
* the SIA 2024 authority extract of 2026-08-10, outside the shared link: the
  specification refers to the profile sheet without reproducing it, and it is
  that extract which gives the sensible heat gain of occupants.

WHAT IS NOT FOUND IS NOT FILLED IN. Each field comes out with its status:
`RELEVE` if found as-is in the text layer, `A_CONFIRMER` with the reason
otherwise. An explicit `null` is better than a plausible value.

THE COLUMN ORDER PITFALL. The optical table gives two numbers per row, unnamed:
« Total solar energy transmittance gtot 0.545 0.059 ». The order comes from a
separate header, « Without shading With shading ». If this header is absent
from the extracted text, **all** optical properties come out as `A_CONFIRMER`
rather than resting on an assumed order: swapping them would give a blind that
transmits ten times too much solar radiation, and the result would still appear
plausible.

WHAT THIS FILE DOES NOT DO. It builds no VE model, registers no case, and does
not claim that 1E is validatable. It provides the traced data without which
that question cannot even be asked.
"""

from __future__ import print_function

import hashlib
import io
import json
import os
import re
import sys

_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SPECS = os.path.join(_RACINE, "SIA_4010_geteilter_Link")
_SORTIE = os.path.join(_RACINE, "refs", "reference-data")

#: Field statuses. `A_CONFIRMER` is not a polite variant of "ok".
RELEVE = "RELEVE"
A_CONFIRMER = "A_CONFIRMER"

_NOMBRE = r"(-?\d+(?:[.,]\d+)?)"

#: The three sources, with their role. The path is relative to `_SPECS`.
SOURCES = (
    (
        "specification_test_1",
        os.path.join("Test1", "Spezifikation_Test1.pdf"),
        "Énonce la chaîne Diag 1A à 1D et la définition du cas 1E.",
    ),
    (
        "specification_test_2",
        os.path.join("Test2", "Spezifikation_Test2.pdf"),
        "Porte la fenêtre, l'infiltration, l'usage SIA 2024 et la régulation "
        "du store que les maillons ajoutent.",
    ),
    (
        "documentation_batiment_exemple",
        os.path.join("Beispielgebäude", "Dokumentation_Beispielgebäude_V5.pdf"),
        "Porte les propriétés de la fenêtre entière, store déployé et rentré.",
    ),
)

#: Fourth source, outside the shared link: the SIA 2024 authority extract
#: received on 2026-08-10. The specification refers to SIA 2024:2021 without
#: reproducing the profile sheet; this extract provides the sensible heat gain
#: of occupants and the schedules. Without it, link 1D would remain blocked on
#: a met → watts conversion — but no conversion is needed, the sheet directly
#: gives W/m².
SOURCE_SIA_2024 = os.path.join(
    "sia4010_evidence",
    "source_audits",
    "sia2024_3_1_authority_20260810",
    "sia2024_office_3_1_standard_profiles.binding.json",
)

#: Values read from the extract: `(bloc, key, path in standard_values)`.
CHAMPS_SIA_2024 = (
    (
        "apports",
        "personnes_gain_sensible_w_m2",
        ("people", "sensible_heat_gain_at_24c_w_m2"),
    ),
    (
        "apports",
        "personnes_simultaneite_annuelle",
        ("people", "annual_simultaneity_factor"),
    ),
    ("apports", "personnes_heures_par_jour", ("people", "use_hours_per_day_h")),
    ("apports", "personnes_jours_par_an", ("people", "use_days_per_year_d")),
)

#: Chain links. The pattern extracts the German definition verbatim from
#: `Spezifikation_Test1.pdf`. `ajoute` names, in French, what the link adds to
#: the previous one — it is a reading index, not normative data: the data is
#: the German citation.
CHAINE = (
    ("1A", r"Diag\s*1A\s*(.*?)\s*Diag\s*1\s*B", "climat Zürich-Kloten"),
    ("1B", r"Diag\s*1\s*B\s*(.*?)\s*Diag\s*1C", "nouvelle fenêtre"),
    ("1C", r"Diag\s*1C\s*(.*?)\s*Diag\s*1D", "infiltration ajustée"),
    ("1D", r"Diag\s*1D\s*(.*?)\s*Zu\s*liefernde", "usage SIA 2024"),
    ("1E", r"Testfall\s*1E\s*:\s*(.*?)\s*Zu\s*liefernde", "store tissu (Stoffmarkise)"),
)

#: Parameters extracted from `Spezifikation_Test2.pdf`.
#: `(bloc, key, pattern, conversion, location)`.
PARAMETRES_TEST_2 = (
    (
        "usage",
        "categorie_sia_2024",
        r'Standardnutzung\s*"([^"]+)"\s*gem[äa]ss\s*SIA\s*2024:2021',
        None,
        "Nutzung / Standardnutzung",
    ),
    (
        "usage",
        "personnes_par_piece",
        r"Personen\s*Anzahl\s*→?\s*" + _NOMBRE,
        "nombre",
        "Wärmeeinträge / Personen / Anzahl",
    ),
    (
        "infiltration",
        "debit_m3_h_m2",
        r"Infiltration\s*" + _NOMBRE + r"\s*m3/\(h\*m2\)\s*gem[äa]ss\s*SIA\s*2024:2021",
        "nombre",
        "Lüftung / Infiltration",
    ),
    (
        "consignes",
        "chauffage_celsius",
        r"Ideales\s*Heizelement,\s*Raumtemperatur-Sollwert\s*" + _NOMBRE + r"\s*°C",
        "nombre",
        "Wärmeabgabe",
    ),
    (
        "consignes",
        "refroidissement_celsius",
        r"Ideales\s*K[üu]hlelement,\s*Raumtemperatur-Sollwert\s*" + _NOMBRE + r"\s*°C",
        "nombre",
        "Kälteabgabe",
    ),
    # The type contains a space (« Soltis 92-2048-Alu »), so `\S+` cannot be
    # used for the first group: it would only extract « Soltis ».
    (
        "store",
        "produit",
        r"Test\s*2A\s*Stoffmarkise\s*Typ\s*(.+?)\s+von\s+(\S+)",
        "produit",
        "Sonnenschutz / Test 2A Stoffmarkise",
    ),
    (
        "store",
        "seuil_activation_w_m2",
        r"Aktivierung\s*→?\s*Schwellenwert\s*" + _NOMBRE + r"\s*W/m2",
        "nombre",
        "Sonnenschutz Extern / Aktivierung",
    ),
    # The glazing for link 1B. The specification quantifies it directly, which
    # resolves a question left open by the example building documentation:
    # that document gives two total g values, under summer (0.545) and
    # reference (0.542) conditions. The specification retains 0.545. We
    # therefore extract from the specification, which defines the case, not
    # from the documentation.
    # The type contains spaces, like the blind: `\S+` would only extract « SGG ».
    (
        "vitrage",
        "type",
        r"Verglasung\s*Typ\s*(.+?)\s*Gesamtenergie",
        None,
        "Verglasung / Typ",
    ),
    (
        "vitrage",
        "g_total",
        r"durchlassgrad\s*gg\s*:?\s*→?\s*" + _NOMBRE,
        "nombre",
        "Verglasung / Gesamtenergiedurchlassgrad gg",
    ),
    (
        "vitrage",
        "u_vitrage_w_m2k",
        r"U-Wert\s*Ug\s*→?\s*" + _NOMBRE + r"\s*W/m2K",
        "nombre",
        "Verglasung / U-Wert Ug",
    ),
    # The Greek symbols in these two lines are NOT Unicode Greek characters:
    # extraction renders them as private-use-area glyphs from the Symbol font.
    # A pattern written with the real Greek letters would never match, and the
    # field would come out as A_CONFIRMER, suggesting that the specification
    # does not give the value. Hence the wildcard.
    (
        "vitrage",
        "transmission_visible",
        r"Transmission\s*v\s*\S*:\s*→?\s*" + _NOMBRE,
        "nombre",
        "Verglasung / Transmission v",
    ),
    (
        "vitrage",
        "reflexion_visible",
        r"Reflexion\s*v\s*\S*:\s*→?\s*" + _NOMBRE,
        "nombre",
        "Verglasung / Reflexion v",
    ),
    # Internal gains for link 1D. Power densities are in the specification;
    # only the SCHEDULES refer to SIA 2024:2021, and for category 3.1 we hold
    # the authority extract of 2026-08-10.
    (
        "apports",
        "personnes_m2_par_personne",
        r"\(" + _NOMBRE + r"\s*m2\s*pro\s*Person\)",
        "nombre",
        "Wärmeeinträge / Personen",
    ),
    (
        "apports",
        "personnes_activite_met",
        r"Aktivit[äa]tsgrad\s*→?\s*" + _NOMBRE + r"\s*met",
        "nombre",
        "Wärmeeinträge / Personen / Aktivitätsgrad",
    ),
    (
        "apports",
        "appareils_w_m2",
        r"Ger[äa]te\s*W[äa]rmeeintragsleistung\s*→?\s*" + _NOMBRE + r"\s*W/m2",
        "nombre",
        "Wärmeeinträge / Geräte",
    ),
    (
        "apports",
        "eclairage_w_m2",
        r"Beleuchtung\s*W[äa]rmeeintragsleistung\s*→?\s*" + _NOMBRE + r"\s*W/m2",
        "nombre",
        "Wärmeeinträge / Beleuchtung",
    ),
    (
        "apports",
        "eclairage_puissance_installee_w_m2",
        r"Anschlusswert\s*→?\s*" + _NOMBRE + r"\s*W/m2",
        "nombre",
        "Wärmeeinträge / Beleuchtung / Anschlusswert",
    ),
)

#: Parameters extracted from the example building documentation.
PARAMETRES_BATIMENT = (
    (
        "store",
        "lame_d_air_cm",
        r"Luftspalt\s*von\s*" + _NOMBRE + r"\s*cm",
        "nombre",
        "2.2.2 Verschattung",
    ),
    (
        "store",
        "seuil_fermeture_w_m2",
        r"bei\s*einer\s*Solarstrahlung\s*von\s*" + _NOMBRE + r"\s*W/m2",
        "nombre",
        "2.2.2 Verschattung",
    ),
    # Thickness of the blind layer, first row of the shaded window layer table.
    # In millimetres in the document.
    (
        "store",
        "epaisseur_couche_mm",
        r"1\.\s*Generic\s*screen\s*shade\s*" + _NOMBRE,
        "nombre",
        "Tabelle 3 / Layer 1 Generic screen shade",
    ),
    # The frame, which link 1B also carries.
    (
        "cadre",
        "part_pourcent",
        r"Rahmenanteil\s*" + _NOMBRE + r"\s*%",
        "nombre",
        "2.2.3 Fensterrahmen",
    ),
    (
        "cadre",
        "u_w_m2k",
        r"Rahmenanteil[^,]*,\s*U-Wert\s*=\s*" + _NOMBRE + r"\s*W/\(m2K\)",
        "nombre",
        "2.2.3 Fensterrahmen",
    ),
)

#: Header that FIXES the order of the two columns in the optical table.
#: Without it, no optical property is extracted.
ORDRE_COLONNES = re.compile(r"Without\s+shading\s+With\s+shading")

#: Optical table blocks: `(key, start, end)`. Bounds are the printed headers;
#: they avoid confusing the two `gtot` rows, which carry different values
#: under summer and reference conditions.
BLOCS_OPTIQUES = (
    (
        "en_iso_52022_3_conditions_ete",
        r"EN\s*ISO\s*52022-3\s*\(summer\s*conditions\)\s*:",
        r"EN\s*ISO\s*52022-3\s*\(reference\s*conditions\)\s*:",
    ),
    (
        "en_iso_52022_3_conditions_reference",
        r"EN\s*ISO\s*52022-3\s*\(reference\s*conditions\)\s*:",
        r"EN\s*410\s*:",
    ),
    ("en_410", r"EN\s*410\s*:", r"Layer\s*d\s*\[mm\]"),
    # The documentation describes the SAME window under two standard families,
    # in two successive tables: EN ISO 52022-3 with EN 410 first, ISO 15099
    # next. The U value is not the same — 0.646 under EN ISO 52022-3 reference
    # conditions, 0.654 under ISO 15099 winter conditions — and the
    # specification uses the second value. Omitting these two blocks caused a
    # difference in standards to appear as a contradiction between documents;
    # see `_concordance_du_u`.
    (
        "iso_15099_conditions_ete",
        r"ISO\s*15099\s*\(summer\s*conditions\)\s*:",
        r"ISO\s*15099\s*\(winter\s*conditions\)\s*:",
    ),
    (
        "iso_15099_conditions_hiver",
        r"ISO\s*15099\s*\(winter\s*conditions\)\s*:",
        r"Tabelle",
    ),
)

#: Quantities sought in each optical block, by their printed symbol.
#: `(key, pattern of the label and symbol, unit)`.
GRANDEURS_OPTIQUES = (
    ("g_total", r"Total\s*solar\s*energy\s*transmittance\s*gtot", "-"),
    ("facteur_convection_gc", r"Convection\s*factor\s*gc", "-"),
    ("facteur_rayonnement_gth", r"Thermal\s*radiation\s*factor\s*gth", "-"),
    ("facteur_ventilation_gv", r"Ventilation\s*factor\s*gv", "-"),
    (
        "transfert_secondaire_qi",
        r"Secondary\s*internal\s*heat\s*transfer\s*factor\s*qi",
        "-",
    ),
    ("u_vitrage_w_m2k", r"U-value\s*of\s*glazing\s*Ug", "W/(m2 K)"),
    ("transmission_solaire_directe_te", r"Direct\s*solar\s*transmittance\s*[τt]e", "-"),
    ("reflexion_solaire_exterieure_re", r"Solar\s*reflectance\s*outside\s*[ρp]e", "-"),
    (
        "reflexion_solaire_interieure_re_prime",
        r"Solar\s*reflectance\s*inside\s*[ρp]'e",
        "-",
    ),
    ("transmission_visible_tv", r"Visual\s*transmittance\s*[τt]v", "-"),
    ("reflexion_visible_exterieure_rv", r"Visual\s*reflectance\s*outside\s*[ρp]v", "-"),
    (
        "reflexion_visible_interieure_rv_prime",
        r"Visual\s*reflectance\s*inside\s*[ρp]'v",
        "-",
    ),
    ("transmission_uv_tuv", r"UV-transmittance\s*[τt]uv", "-"),
)


def _nombre(texte):
    """Converts a number from the PDF to a numeric value.

    Args:
        texte: Number as written in the PDF.

    Returns:
        float | int: Numeric value.
    """
    valeur = float(texte.replace(",", "."))
    return int(valeur) if valeur == int(valeur) else valeur


def _empreinte(chemin):
    """Returns the SHA-256 of a source file.

    Args:
        chemin: File path.

    Returns:
        str: Hexadecimal digest.
    """
    digest = hashlib.sha256()
    with open(chemin, "rb") as flux:
        for bloc in iter(lambda: flux.read(65536), b""):
            digest.update(bloc)
    return digest.hexdigest()


def _texte_normalise(chemin):
    """Extracts the text layer from a PDF, with normalised whitespace.

    Normalisation is necessary: extraction cuts table rows at varying points,
    and a pattern written against raw text would match or not depending on the
    layout.

    Args:
        chemin: PDF path.

    Returns:
        str: Text with whitespace collapsed to single spaces.

    Raises:
        IOError: If the PDF is missing.
    """
    if not os.path.exists(chemin):
        raise IOError("source absente : %s" % chemin)
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader
    lecteur = PdfReader(chemin)
    brut = "\n".join((page.extract_text() or "") for page in lecteur.pages)
    return " ".join(brut.split())


def _champ_absent(source, raison):
    """Returns an unextracted field, with the reason for its absence.

    Args:
        source: Location sought in the document.
        raison: Why the value was not extracted.

    Returns:
        dict: Field in `A_CONFIRMER`.
    """
    return {"valeur": None, "statut": A_CONFIRMER, "source": source, "raison": raison}


def _chercher(texte, motif, conversion, source):
    """Extracts a field by its pattern, or explains why it is missing.

    Args:
        texte: Normalised document text.
        motif: Regular expression with one or two capture groups.
        conversion: `'nombre'`, `'produit'` or `None` for raw text.
        source: Location in the document, cited in the reference dataset.

    Returns:
        dict: Extracted field or field in `A_CONFIRMER`.
    """
    trouve = re.search(motif, texte)
    if trouve is None:
        return _champ_absent(source, "motif absent de la couche texte")
    if conversion == "nombre":
        try:
            valeur = _nombre(trouve.group(1))
        except ValueError:
            return _champ_absent(source, "valeur non numérique : %r" % trouve.group(1))
    elif conversion == "produit":
        valeur = {"type": trouve.group(1), "fabricant": trouve.group(2)}
    else:
        valeur = trouve.group(1).strip()
    return {"valeur": valeur, "statut": RELEVE, "source": source}


def _proprietes_optiques(texte):
    """Extracts the whole-window table, blind retracted and deployed.

    The order of the two columns cannot be deduced from the rows: it comes
    from the header « Without shading With shading ». Without this header,
    nothing is extracted — swapping the columns would give a blind ten times
    too transparent, without the result becoming implausible.

    Args:
        texte: Normalised text from the example building documentation.

    Returns:
        dict: Normative blocks, each carrying its quantities.
    """
    en_tete = ORDRE_COLONNES.search(texte)
    if en_tete is None:
        return {
            "statut": A_CONFIRMER,
            "raison": (
                "l'en-tête « Without shading With shading » est absent "
                "du texte extrait ; l'ordre des deux colonnes n'est "
                "donc pas démontré et aucune propriété n'est relevée"
            ),
            "blocs": {},
        }

    blocs = {}
    for cle_bloc, debut, fin in BLOCS_OPTIQUES:
        borne_debut = re.search(debut, texte)
        # The end bound is searched AFTER the start bound, and not in the
        # whole document: « Layer d [mm] » appears twice, and the first
        # occurrence precedes « EN 410: ». Searching globally gave a segment
        # of negative length, hence an empty block, with no visible error.
        borne_fin = (
            re.compile(fin).search(texte, borne_debut.end())
            if borne_debut is not None
            else None
        )
        if borne_debut is None or borne_fin is None:
            blocs[cle_bloc] = {
                "statut": A_CONFIRMER,
                "raison": "bornes du bloc absentes de la couche texte",
                "grandeurs": {},
            }
            continue
        segment = texte[borne_debut.end() : borne_fin.start()]
        grandeurs = {}
        for cle, libelle, unite in GRANDEURS_OPTIQUES:
            trouve = re.search(libelle + r"\s*" + _NOMBRE + r"\s*" + _NOMBRE, segment)
            if trouve is None:
                continue
            grandeurs[cle] = {
                "unite": unite,
                "store_rentre": _nombre(trouve.group(1)),
                "store_deploye": _nombre(trouve.group(2)),
                "statut": RELEVE,
            }
        blocs[cle_bloc] = {
            "statut": RELEVE if grandeurs else A_CONFIRMER,
            "grandeurs": grandeurs,
        }
        if not grandeurs:
            blocs[cle_bloc]["raison"] = "aucune grandeur du tableau relevée dans ce bloc"
    return {
        "statut": RELEVE,
        "ordre_colonnes": "première colonne = store rentré, seconde = store "
        "déployé, d'après l'en-tête imprimé",
        "blocs": blocs,
    }


def _concordance_du_u(parametres, fenetre):
    """Identifies UNDER WHICH standard the U value from the specification is found.

    An earlier version of this producer reported a "divergence between sources":
    0.654 in the specification against 0.646 in the documentation. That was
    wrong, and the mistake was mine. The documentation describes the same window
    under two families of standards, and the U value is not the same — 0.646
    under EN ISO 52022-3 reference conditions, 0.654 under ISO 15099 winter
    conditions. The specification uses the second, to the last digit. Both
    documents agree; it was the comparison that targeted the wrong block.

    Keeping this as a check rather than removing it has a reason: the error had
    nearly been sent in a message to the author of these documents as a
    notification of a typo.

    Args:
        parametres: Parameters extracted from the Test 2 specification.
        fenetre: Optical blocks extracted from the documentation.

    Returns:
        dict: Standard under which the value agrees, or the discrepancy if it remains.
    """
    spec = parametres.get("vitrage", {}).get("u_vitrage_w_m2k", {})
    if spec.get("statut") != RELEVE:
        return {"statut": A_CONFIRMER, "raison": "U de la spécification non relevé"}
    attendu = spec["valeur"]
    trouves = []
    for cle_bloc, bloc in (fenetre.get("blocs") or {}).items():
        grandeur = (bloc.get("grandeurs") or {}).get("u_vitrage_w_m2k")
        if grandeur is None:
            continue
        trouves.append((cle_bloc, grandeur["store_rentre"]))
        if grandeur["store_rentre"] == attendu:
            return {
                "statut": RELEVE,
                "grandeur": "u_vitrage_w_m2k",
                "valeur": attendu,
                "norme_concordante": cle_bloc,
                "autres_valeurs_du_document": dict(trouves),
                "commentaire": (
                    "La spécification Test 2 reprend le U de ce bloc normatif. "
                    "La documentation en donne d'autres sous d'autres normes : "
                    "comparer au mauvais bloc fait passer une différence de "
                    "norme pour une contradiction entre documents."
                ),
            }
    return {
        "statut": A_CONFIRMER,
        "grandeur": "u_vitrage_w_m2k",
        "specification_test_2": attendu,
        "valeurs_du_document": dict(trouves),
        "raison": (
            "Le U de la spécification ne se retrouve dans aucun bloc normatif "
            "relevé. À vérifier avant d'en conclure quoi que ce soit : une "
            "norme manquante à l'extraction expliquerait l'écart mieux qu'une "
            "coquille dans un document officiel."
        ),
    }


def construire():
    """Assembles the reference dataset for the chain 1A to 1E.

    Returns:
        dict: Traced reference dataset, ready to be frozen to JSON.
    """
    sources = {}
    textes = {}
    for cle, relatif, role in SOURCES:
        chemin = os.path.join(_SPECS, relatif)
        textes[cle] = _texte_normalise(chemin)
        sources[cle] = {
            "fichier": "SIA_4010_geteilter_Link/" + relatif.replace("\\", "/"),
            "sha256": _empreinte(chemin),
            "role": role,
        }

    chaine = []
    for cas, motif, ajoute in CHAINE:
        releve = _chercher(
            textes["specification_test_1"], motif, None, "Diagnosefälle / Testfall 1E"
        )
        chaine.append(
            {
                "cas": cas,
                "definition_verbatim_de": releve["valeur"],
                "statut": releve["statut"],
                "source": releve["source"],
                "ajoute_au_precedent": ajoute,
                "raison": releve.get("raison"),
            }
        )

    # The SIA 2024 authority extract, if present. Its absence does not cause
    # production to fail: the affected fields come out as `A_CONFIRMER`,
    # like any value that was not found.
    chemin_sia_2024 = os.path.join(_RACINE, SOURCE_SIA_2024)
    extrait_sia_2024 = None
    if os.path.exists(chemin_sia_2024):
        with io.open(chemin_sia_2024, encoding="utf-8") as flux:
            extrait_sia_2024 = json.load(flux)
        sources["extrait_autorite_sia_2024"] = {
            "fichier": SOURCE_SIA_2024.replace("\\", "/"),
            "sha256": _empreinte(chemin_sia_2024),
            "role": (
                "Extrait d'autorité du 2026-08-10 pour la catégorie d'usage "
                "3.1. Donne le gain sensible des occupants en W/m² et les "
                "horaires, que la spécification ne reproduit pas."
            ),
            "categorie": extrait_sia_2024.get("use_category"),
        }

    parametres = {}
    for bloc, cle, motif, conversion, source in PARAMETRES_TEST_2:
        parametres.setdefault(bloc, {})[cle] = _chercher(
            textes["specification_test_2"], motif, conversion, source
        )
    for bloc, cle, motif, conversion, source in PARAMETRES_BATIMENT:
        parametres.setdefault(bloc, {})[cle] = _chercher(
            textes["documentation_batiment_exemple"], motif, conversion, source
        )
    for bloc, cle, chemin in CHAMPS_SIA_2024:
        localisation = "SIA 2024:2021 fiche 3.1, standard_values.%s" % (".".join(chemin))
        if extrait_sia_2024 is None:
            parametres.setdefault(bloc, {})[cle] = _champ_absent(
                localisation,
                "extrait d'autorité SIA 2024 absent du dépôt : %s"
                % SOURCE_SIA_2024.replace("\\", "/"),
            )
            continue
        noeud = extrait_sia_2024.get("standard_values", {})
        for partie in chemin:
            noeud = (noeud or {}).get(partie) if isinstance(noeud, dict) else None
        if noeud is None:
            parametres.setdefault(bloc, {})[cle] = _champ_absent(
                localisation, "champ absent de l'extrait d'autorité"
            )
        else:
            parametres.setdefault(bloc, {})[cle] = {
                "valeur": noeud,
                "statut": RELEVE,
                "source": localisation,
            }

    fenetre = _proprietes_optiques(textes["documentation_batiment_exemple"])
    return {
        "test": 1,
        "perimetre": "Cas diagnostiques 1A à 1D et cas 1E du Test 1",
        "statut": "FIGÉ — chaque champ relevé dans la couche texte de sa source",
        "pourquoi": (
            "Le cas 1E est le seul cas du Test 1 à porter un critère "
            "pass/fail, et il n'est pas générable sans cette chaîne. "
            "Ce référentiel ne rend pas 1E validable : il rend la question "
            "posable."
        ),
        "sources": sources,
        "chaine": chaine,
        "parametres": parametres,
        "fenetre_entiere": fenetre,
        "concordance_du_u_vitrage": _concordance_du_u(parametres, fenetre),
        "reserves": [
            "Les propriétés relevées sont celles de la FENÊTRE ENTIÈRE "
            "(EN ISO 52022-3 / EN 410), store rentré et déployé. La "
            "documentation donne aussi les propriétés couche par couche dans "
            "des figures ; elles ne sont PAS relevées ici.",
            "L'usage du maillon 1D renvoie à SIA 2024:2021. Seule la "
            "catégorie citée par la spécification est relevée ; les valeurs "
            "de la fiche restent à lier depuis l'extrait d'autorité.",
            "Aucun cas n'est enregistré et aucun générateur VE n'est écrit "
            "par ce producteur.",
        ],
    }


def bilan(reference):
    """Counts the fields that were extracted and those to confirm.

    Args:
        reference: Built reference dataset.

    Returns:
        tuple[int, int]: Number of extracted fields, number to confirm.
    """
    releves = [0]
    a_confirmer = [0]

    def visiter(noeud):
        if isinstance(noeud, dict):
            statut = noeud.get("statut")
            if statut == RELEVE:
                releves[0] += 1
            elif statut == A_CONFIRMER:
                a_confirmer[0] += 1
            for valeur in noeud.values():
                visiter(valeur)
        elif isinstance(noeud, list):
            for valeur in noeud:
                visiter(valeur)

    visiter(reference)
    return releves[0], a_confirmer[0]


def main(arguments=()):
    """Command-line entry point.

    Args:
        arguments: Arguments without the script name. `--ecrire` freezes the JSON.

    Returns:
        int: 0 if everything went well.
    """
    reference = construire()
    releves, a_confirmer = bilan(reference)

    print("Chaîne 1A → 1E : %d maillon(s)" % len(reference["chaine"]))
    for maillon in reference["chaine"]:
        print(
            "  %-3s %-28s %s"
            % (maillon["cas"], maillon["ajoute_au_precedent"], maillon["statut"])
        )
        if maillon["definition_verbatim_de"]:
            print("      « %s »" % maillon["definition_verbatim_de"])
    print()
    for bloc in sorted(reference["parametres"]):
        print("  %s" % bloc)
        for cle in sorted(reference["parametres"][bloc]):
            champ = reference["parametres"][bloc][cle]
            print("    %-26s %-12s %s" % (cle, champ["statut"], champ["valeur"]))
    print()
    fenetre = reference["fenetre_entiere"]
    print("  fenêtre entière : %s" % fenetre["statut"])
    for cle_bloc in sorted(fenetre["blocs"]):
        grandeurs = fenetre["blocs"][cle_bloc]["grandeurs"]
        print("    %-40s %d grandeur(s)" % (cle_bloc, len(grandeurs)))
    print()
    print("  %d champ(s) relevé(s), %d à confirmer" % (releves, a_confirmer))

    if "--ecrire" in arguments:
        sortie = os.path.join(_SORTIE, "test-1.diagnostics.ref.json")
        with io.open(sortie, "w", encoding="utf-8") as flux:
            flux.write(json.dumps(reference, ensure_ascii=False, indent=2))
            flux.write("\n")
        print("  écrit : %s" % sortie)
    else:
        print("  (ajouter --ecrire pour figer le JSON)")
    return 0


if __name__ == "__main__":
    sys.exit(main(tuple(sys.argv[1:])))
