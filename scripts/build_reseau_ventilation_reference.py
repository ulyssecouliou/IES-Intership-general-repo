# -*- coding: utf-8 -*-
"""Freezes the ventilation network for SIA Tests 5 and 6, from their PDFs.

WHY AN EXTRACTOR, AND NOT A HAND-WRITTEN FILE. Project rule 2 makes the
published specification the sole truth. A retyped JSON proves nothing: it
asserts, with the authority of a reference dataset, what someone believed they
read. Here every value is FOUND in the PDF text layer by a named pattern, and
**what is not found is not filled in**: the field comes out as `null`, in
`A_CONFIRMER`, with the reason.

WHAT THE TEXT LAYER DOES NOT PROVIDE. Two families, and they carry values that
decide the result:

* **charts.** Sliding setpoints are drawn. Their data labels (« 12; 20 »)
  are in the text and are therefore extracted — but the STEPS beyond the
  labelled points are not. The fan characteristic curve has no label at all:
  it comes out empty.
* **variant tables.** Test 5 has four columns (5A to 5D) and often two merged
  cells. The split point is not in the text. Guessing would mean building two
  variants out of four incorrectly.

Usage:
    python scripts/build_reseau_ventilation_reference.py [--ecrire]
"""

from __future__ import print_function

import io
import json
import os
import re
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

_SPECS = os.path.join(_RACINE, "SIA_4010_geteilter_Link")
_SORTIE = os.path.join(_RACINE, "refs", "reference-data")

#: Possible statuses of a value. `RELEVE` means "found as-is in the text
#: layer". The other two say exactly why we cannot go further — they are NOT
#: polite variants of "ok".
RELEVE = "RELEVE"
SUR_GRAPHIQUE = "RELEVE_SUR_GRAPHIQUE"
A_CONFIRMER = "A_CONFIRMER"

#: Pattern for a chart data label: « abscissa; ordinate ».
_ETIQUETTE = re.compile(r"(-?\d+(?:\.\d+)?); ?(-?\d+(?:\.\d+)?)")

_NOMBRE = r"([\d\'’]+(?:\.\d+)?)"


def _nombre(texte):
    """Converts a number from the PDF, including thousand separators.

    Args:
        texte: Number as written in the PDF (« 1'040 »).

    Returns:
        float | int: Numeric value.
    """
    net = texte.replace("'", "").replace("’", "")
    valeur = float(net)
    return int(valeur) if valeur == int(valeur) else valeur


def _texte_du_pdf(numero_test):
    """Extracts the text layer from a specification PDF.

    Args:
        numero_test: 5 or 6.

    Returns:
        str: Concatenated text.

    Raises:
        IOError: If the PDF is missing.
    """
    chemin = os.path.join(
        _SPECS, "Test%d" % numero_test, "Spezifikation_Test%d.pdf" % numero_test
    )
    if not os.path.exists(chemin):
        raise IOError("spécification absente : %s" % chemin)
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader
    lecteur = PdfReader(chemin)
    return "\n".join((page.extract_text() or "") for page in lecteur.pages)


#: Fields to extract, per test. Each entry is
#: `(bloc, clé, motif, conversion, source)`. The pattern is applied to the
#: full text; if it does not match, the field comes out as `A_CONFIRMER`.
CHAMPS = {
    5: [
        (
            "reseau",
            "debit_nominal_m3_h",
            r"Nennvolumenstrom\s*→?\s*" + _NOMBRE + r"\s*m3/h",
            _nombre,
            "Volumenstrom / Nennvolumenstrom",
        ),
        (
            "reseau",
            "debit_variable_min_pourcent",
            r"Variabel von bis\s*→?\s*" + _NOMBRE + r"\s*[–-]",
            _nombre,
            "Volumenstrom / Variabel von bis",
        ),
        (
            "reseau",
            "horaire_fonctionnement",
            r"Betriebszeit\s*(Werktags[^\n]*)",
            None,
            "Regelung / Betriebszeit",
        ),
        (
            "reseau",
            "perte_de_charge_soufflage_pa",
            r"Zuluft\s*→\s*" + _NOMBRE + r"\s*Pa",
            _nombre,
            "Nenn-Druckverlust / Zuluft",
        ),
        (
            "reseau",
            "perte_de_charge_reprise_pa",
            r"Abluft\s*→\s*" + _NOMBRE + r"\s*Pa",
            _nombre,
            "Nenn-Druckverlust / Abluft",
        ),
        (
            "reseau",
            "infiltration_m3_h_m2",
            r"Infiltration\s*" + _NOMBRE + r"\s*m3/\(h",
            _nombre,
            "Infiltration",
        ),
        (
            "reseau",
            "debit_par_personne_m3_h",
            _NOMBRE + r"\s*m3/h pro Person",
            _nombre,
            "Lüftung — « abweichend von SIA 2024:2021 »",
        ),
        (
            "reseau",
            "co2_exterieur_ppm",
            r"Aussenluftkonzentration:\s*" + _NOMBRE + r"\s*ppm",
            _nombre,
            "Sollwerte / CO2",
        ),
        (
            "reseau",
            "humidite_relative_min_pourcent",
            r"Rel\. Feuchte min\.\s*" + _NOMBRE + r"%",
            _nombre,
            "Sollwerte / Rel. Feuchte",
        ),
        (
            "ventilateurs",
            "puissance_soufflage_w",
            r"Zuluftventilator:\s*" + _NOMBRE + r"\s*W",
            _nombre,
            "Ventilatoren / Nennleistung",
        ),
        (
            "ventilateurs",
            "puissance_reprise_w",
            r"Abluftventilator:\s*" + _NOMBRE + r"\s*W",
            _nombre,
            "Ventilatoren / Nennleistung",
        ),
        (
            "ventilateurs",
            "vitesse_soufflage_min_1",
            r"Zuluftventilator:\s*" + _NOMBRE + r"\s*min-1",
            _nombre,
            "Ventilatoren / Drehzahl",
        ),
        (
            "ventilateurs",
            "vitesse_reprise_min_1",
            r"Abluftventilator:\s*" + _NOMBRE + r"\s*min-1",
            _nombre,
            "Ventilatoren / Drehzahl",
        ),
        (
            "recuperateur",
            "vitesse_nominale_min_1",
            r"Nominale Drehzahl\s*" + _NOMBRE + r"\s*min-1",
            _nombre,
            "Nominale Drehzahl",
        ),
        (
            "recuperateur",
            "puissance_entrainement_w",
            r"Nominale Antriebsleistung\s*" + _NOMBRE + r"\s*W",
            _nombre,
            "Nominale Antriebsleistung",
        ),
        (
            "recuperateur",
            "charge_partielle",
            r"Teillastverhalten\s*(Gemäss EN[^\n]*)",
            None,
            "Teillastverhalten",
        ),
        (
            "batterie_froide",
            "puissance_kw",
            r"Auslegungsleistung\s*" + _NOMBRE + r"\s*kW",
            _nombre,
            "Luftkühler / Auslegungsleistung",
            "Luftkühler",
        ),
        (
            "batterie_froide",
            "rendement_echange",
            r"wir-?\s*kungsgrad\s*" + _NOMBRE,
            _nombre,
            "Wärmeübertragungswirkungsgrad",
            "Luftkühler",
        ),
        (
            "batterie_froide",
            "facteur_bypass",
            r"Bypassfaktor\s*" + _NOMBRE,
            _nombre,
            "Bypassfaktor",
            "Luftkühler",
        ),
        (
            "batterie_froide",
            "air_entrant_c",
            r"Eintritts-Lufttemperatur\s*" + _NOMBRE + r"°C",
            _nombre,
            "Luftkühler / Eintritts-Lufttemperatur",
            "Luftkühler",
        ),
        (
            "batterie_froide",
            "air_entrant_g_kg",
            r"Feuchtegehalt\s*" + _NOMBRE + r"\s*g/kg",
            _nombre,
            "Feuchtegehalt",
            "Luftkühler",
        ),
        (
            "batterie_froide",
            "air_sortant_c",
            r"Austrittstemperatur\s*" + _NOMBRE + r"°C",
            _nombre,
            "Luftkühler / Austrittstemperatur",
            "Luftkühler",
        ),
        (
            "batterie_froide",
            "eau_glacee_entree_c",
            r"Kaltwasser-Eintrittstemperatur\s*" + _NOMBRE + r"\s*°C",
            _nombre,
            "Kaltwasser-Eintrittstemperatur",
            "Luftkühler",
        ),
        (
            "batterie_chaude",
            "puissance_kw",
            r"Auslegungsleistung\s*" + _NOMBRE + r"\s*kW",
            _nombre,
            "Lufterhitzer / Auslegungsleistung",
            "Lufterhitzer",
        ),
        (
            "batterie_chaude",
            "air_entrant_c",
            r"Eintritts-Lufttemperatur\s*\+?" + _NOMBRE + r"°C",
            _nombre,
            "Lufterhitzer / Eintritts-Lufttemperatur",
            "Lufterhitzer",
        ),
        (
            "batterie_chaude",
            "air_sortant_c",
            r"Austrittstemperatur\s*" + _NOMBRE + r"°C",
            _nombre,
            "Lufterhitzer / Austrittstemperatur",
            "Lufterhitzer",
        ),
        (
            "batterie_chaude",
            "eau_chaude_entree_c",
            r"Heizwasser-Eintrittstempera-?\s*tur\s*" + _NOMBRE + r"°C",
            _nombre,
            "Heizwasser-Eintrittstemperatur",
            "Lufterhitzer",
        ),
        (
            "humidificateur",
            "debit_eau_kg_h",
            r"strom Wasser\s*" + _NOMBRE + r"\s*kg/h",
            _nombre,
            "Nenn-Massenstrom Wasser",
        ),
        (
            "humidificateur",
            "energie_pompe_wh_m3",
            r"feuchters\s*" + _NOMBRE + r"\s*Wh/m3",
            _nombre,
            "Spez. Pumpenenergie des Befeuchters",
        ),
    ],
    6: [
        (
            "reseau",
            "debit_nominal_stufe3_m3_h",
            r"Stufe 3\s*" + _NOMBRE + r"\s*m3/h",
            _nombre,
            "Volumenstrom / Nennvolumenstrom Stufe 3",
        ),
        (
            "reseau",
            "debit_nominal_stufe2_m3_h",
            r"Stufe 2\s*" + _NOMBRE + r"\s*m3/h",
            _nombre,
            "Volumenstrom / Stufe 2",
        ),
        (
            "reseau",
            "debit_nominal_stufe1_m3_h",
            r"Stufe 1\s*" + _NOMBRE + r"\s*m3/h",
            _nombre,
            "Volumenstrom / Stufe 1",
        ),
        (
            "reseau",
            "horaire_fonctionnement",
            r"Betriebszeit\s*(Montag[^\n]*)",
            None,
            "Regelung / Betriebszeit",
        ),
        (
            "reseau",
            "perte_de_charge_soufflage_pa",
            r"Zuluft\s*→\s*" + _NOMBRE + r"\s*Pa",
            _nombre,
            "Nenn-Druckverlust / Zuluft",
        ),
        (
            "reseau",
            "perte_de_charge_reprise_pa",
            r"Abluft\s*→\s*" + _NOMBRE + r"\s*Pa",
            _nombre,
            "Nenn-Druckverlust / Abluft",
        ),
        (
            "reseau",
            "infiltration_m3_h_m2",
            r"Infiltration\s*" + _NOMBRE + r"\s*m3/\(h",
            _nombre,
            "Infiltration",
        ),
        (
            "reseau",
            "surface_nette_m2",
            r"Gemäss Dokumentation \(" + _NOMBRE + r"\s*m2\)",
            _nombre,
            "Räume / Nettofläche",
        ),
        (
            "ventilateurs",
            "puissance_soufflage_w",
            r"Zuluftventilator:\s*" + _NOMBRE + r"\s*W",
            _nombre,
            "Ventilatoren / Nennleistung",
        ),
        (
            "ventilateurs",
            "puissance_reprise_w",
            r"Abluftventilator:\s*" + _NOMBRE + r"\s*W",
            _nombre,
            "Ventilatoren / Nennleistung",
        ),
        (
            "ventilateurs",
            "vitesse_soufflage_min_1",
            r"Zuluftventilator:\s*" + _NOMBRE + r"\s*min-1",
            _nombre,
            "Ventilatoren / Drehzahl",
        ),
        (
            "ventilateurs",
            "vitesse_reprise_min_1",
            r"Abluftventilator:\s*" + _NOMBRE + r"\s*min-1",
            _nombre,
            "Ventilatoren / Drehzahl",
        ),
        (
            "recuperateur",
            "taux_temperature",
            r"Nominale Temperaturänderungszahl\s*" + _NOMBRE,
            _nombre,
            "Kreislaufverbund / Nominale Temperaturänderungszahl",
        ),
        (
            "recuperateur",
            "fluide",
            r"Transportmedium\s*([^\n]+)",
            None,
            "Transportmedium",
        ),
        (
            "recuperateur",
            "debit_pompe_l_h",
            r"Volumenstrom Pumpkreis\s*" + _NOMBRE + r"\s*l/h",
            _nombre,
            "Nominaler Volumenstrom Pumpkreis",
        ),
        (
            "recuperateur",
            "puissance_pompe_w",
            r"Pumpen-Antriebsleistung\s*" + _NOMBRE + r"\s*W",
            _nombre,
            "Nominale Pumpen-Antriebsleistung",
        ),
        (
            "recuperateur",
            "debit_pompe_min_pourcent",
            r"Minimaler Volumenstrom Pumpkreis\s*" + _NOMBRE + r"%",
            _nombre,
            "Minimaler Volumenstrom Pumpkreis",
        ),
        (
            "recuperateur",
            "protection_antigel",
            r"schutz\s*(Mit Pumpendrehzahl-Anpassung auf Fortlufttemperatur[^\n]*)",
            None,
            "Vereisungsschutz",
        ),
        (
            "batterie_froide",
            "puissance_kw",
            r"Auslegungsleistung\s*" + _NOMBRE + r"\s*kW",
            _nombre,
            "Luftkühler / Auslegungsleistung",
            "Luftkühler",
        ),
        (
            "batterie_froide",
            "rendement_echange",
            r"wir-?\s*kungsgrad\s*" + _NOMBRE,
            _nombre,
            "Wärmeübertragungswirkungsgrad",
            "Luftkühler",
        ),
        (
            "batterie_froide",
            "air_entrant_c",
            r"Eintritts-Lufttemperatur\s*" + _NOMBRE + r"°C",
            _nombre,
            "Luftkühler / Eintritts-Lufttemperatur",
            "Luftkühler",
        ),
        (
            "batterie_froide",
            "air_entrant_g_kg",
            r"Feuchtegehalt\s*" + _NOMBRE + r"\s*g/kg",
            _nombre,
            "Feuchtegehalt",
            "Luftkühler",
        ),
        (
            "batterie_froide",
            "air_sortant_c",
            r"Austrittstemperatur\s*" + _NOMBRE + r"°C",
            _nombre,
            "Luftkühler / Austrittstemperatur",
            "Luftkühler",
        ),
        (
            "batterie_froide",
            "eau_glacee_entree_c",
            r"Kaltwasser-Eintrittstemperatur\s*" + _NOMBRE + r"\s*°C",
            _nombre,
            "Kaltwasser-Eintrittstemperatur",
            "Luftkühler",
        ),
        (
            "batterie_chaude",
            "puissance_kw",
            r"Auslegungsleistung\s*" + _NOMBRE + r"\s*kW",
            _nombre,
            "Lufterhitzer / Auslegungsleistung",
            "Lufterhitzer",
        ),
        (
            "batterie_chaude",
            "air_entrant_c",
            r"Eintritts-Lufttemperatur\s*\+?" + _NOMBRE + r"°C",
            _nombre,
            "Lufterhitzer / Eintritts-Lufttemperatur",
            "Lufterhitzer",
        ),
        (
            "batterie_chaude",
            "air_sortant_c",
            r"Austrittstemperatur\s*" + _NOMBRE + r"°C",
            _nombre,
            "Lufterhitzer / Austrittstemperatur",
            "Lufterhitzer",
        ),
        (
            "batterie_chaude",
            "eau_chaude_entree_c",
            r"Heizwasser-Eintrittstemperatur\s*" + _NOMBRE + r"°C",
            _nombre,
            "Heizwasser-Eintrittstemperatur",
            "Lufterhitzer",
        ),
    ],
}

#: Charts to extract, per test: `(clé, titre dans le PDF, ordonnée)`. Points
#: come from DATA LABELS, the only part of a chart present in the text layer.
COURBES = {
    5: [
        ("temperature_soufflage", "Zulufttemperatur", "Zulufttemperatur"),
        ("temperature_eau_glacee", "Kaltwassertemperatur", "Kaltwassertemperatur"),
        ("temperature_eau_chaude", "Heizwassertemperatur", "Heizwassertemperatur"),
    ],
    6: [
        ("temperature_soufflage", "Zulufttemperatur", "Zulufttemperatur"),
        ("temperature_eau_glacee", "Kaltwassertemperatur", "Kaltwassertemperatur"),
        ("temperature_eau_chaude", "Heizwassertemperatur", "Heizwassertemperatur"),
    ],
}

#: Fields that the text layer CANNOT resolve, with the reason. They are
#: declared here rather than guessed: a reference dataset silent about its
#: gaps is more dangerous than an incomplete one.
TROUS = {
    5: [
        (
            "ventilateurs",
            "kennfeld",
            "Ventilatoren / Kennfeld",
            "Courbe caractéristique : graphique SANS étiquette de données. "
            "Aucun point n'en est extractible. Sans elle, la puissance des "
            "ventilateurs à charge partielle n'est pas reproductible — et "
            "c'est une des grandeurs à livrer.",
        ),
        (
            "ventilateurs",
            "part_pression_constante_pa",
            "Variante 5A 5B 5C 5D / Konstantdruckanteil (ZUL+ABL)",
            "Deux cellules (« 50+50 Pa », « 270+270 Pa ») pour QUATRE colonnes "
            "de variantes. Le point de partage n'est pas dans la couche texte.",
        ),
        (
            "recuperateur",
            "type_par_variante",
            "Variante 5A 5B 5C 5D / Typ",
            "Deux cellules (« Hygroskopisch », « Nicht hygroskopisch ») pour "
            "quatre colonnes.",
        ),
        (
            "recuperateur",
            "taux_temperature_par_variante",
            "Nominale Temperaturänderungszahl",
            "Deux cellules (0.67, 0.69) pour quatre colonnes.",
        ),
        (
            "recuperateur",
            "taux_humidite_par_variante",
            "Nominale Feuchteänderungszahl",
            "Deux cellules (0.42, 0.3) pour quatre colonnes.",
        ),
        (
            "humidificateur",
            "type_par_variante",
            "Luftbefeuchter / Variante 5A 5B 5C 5D / Typ",
            "Deux cellules (« Kontaktbefeuchter », « Dampf ») pour quatre "
            "colonnes. Le dépôt suppose ailleurs « contact 5A-5C, vapeur 5D » "
            "(build_traceability_matrix.ANCRAGE) : cette supposition n'est PAS "
            "confirmée par la couche texte et doit être tranchée.",
        ),
    ],
    6: [
        (
            "ventilateurs",
            "kennfeld",
            "Ventilatoren / Kennfeld",
            "Courbe caractéristique : graphique sans étiquette de données.",
        ),
        (
            "reseau",
            "debit_du_local_restaurant_m3_h",
            "Lüftung (p. 1) contre RLT-Anlage / Volumenstrom (p. 3)",
            "CONTRADICTION APPARENTE : la page 1 annonce « Zuluft 3'000 m3/h, "
            "Abluft 2'650 m3/h » et la section RLT un nominal de 6'150 m3/h "
            "en étage 3. Les deux ne se rapportent probablement pas au même "
            "périmètre (local seul / centrale desservant aussi la cuisine), "
            "mais la spécification ne le dit pas. Saisir l'un pour l'autre "
            "fausserait tout le bilan aéraulique.",
        ),
        (
            "reseau",
            "profil_stufenbetrieb",
            "Regelung / Stufenbetrieb",
            "Le profil horaire des trois étages est un GRAPHIQUE (débit relatif "
            "0 / 0.33 / 0.67 / 1.00 sur 24 h). Les paliers y sont lisibles mais "
            "pas les heures de bascule.",
        ),
    ],
}


def _chercher(texte, motif, conversion, source, depuis=None):
    """Searches for a field in the text layer.

    Args:
        texte: PDF text.
        motif: Regular expression with one capture group.
        conversion: Conversion function, or `None` for raw text.
        source: PDF section, for traceability.
        depuis: Section title from which to start searching. Without it,
            shared labels — `Auslegungsleistung`, `Austrittstemperatur` —
            match the first equipment encountered: the heating coil would
            silently inherit the cooler's values.

    Returns:
        dict: Value and status. `null` + `A_CONFIRMER` if the pattern does
        not match — never a default value.
    """
    if depuis is not None:
        debut = texte.find(depuis)
        if debut < 0:
            return {
                "valeur": None,
                "statut": A_CONFIRMER,
                "source": source,
                "a_confirmer": "Section « %s » introuvable dans le PDF." % depuis,
            }
        texte = texte[debut:]
    trouve = re.search(motif, texte)
    if trouve is None:
        return {
            "valeur": None,
            "statut": A_CONFIRMER,
            "source": source,
            "a_confirmer": "Motif introuvable dans la couche texte du "
            "PDF. La valeur n'a PAS été devinée.",
        }
    brut = trouve.group(1).strip()
    return {
        "valeur": conversion(brut) if conversion else brut,
        "statut": RELEVE,
        "source": source,
    }


#: Maximum distance, in characters, between a data label and the title of the
#: chart it belongs to. Beyond this, the label is an orphan: better to leave
#: it unattributed than to attribute it at random.
PORTEE_ETIQUETTE = 400

#: Maximum gap, in characters, between two labels of the SAME chart. Beyond
#: this, they come from different charts.
ECART_MEME_GRAPHIQUE = 60

#: Isolated number pattern, for reading axis tick marks.
_GRADUATION = re.compile(r"-?\d+(?:\.\d+)?")


def _attribuer_les_etiquettes(texte, titres):
    """Assigns each data label to the CLOSEST chart.

    A simple search "does the title appear within the next N characters" is
    not enough: two charts follow one another in the stream, and chilled-water
    points were also ending up under the hot-water chart. The closest chart
    wins.

    Args:
        texte: PDF text.
        titres: Titles of the charts to extract.

    Returns:
        dict: `{titre: [(couple, position, fin_du_graphique)]}`.
    """
    attribution = dict((titre, []) for titre in titres)
    for etiquette in _ETIQUETTE.finditer(texte):
        proche, distance = None, None
        for titre in titres:
            position = texte.find(titre, etiquette.end())
            if position < 0:
                continue
            ecart = position - etiquette.end()
            if distance is None or ecart < distance:
                proche, distance = titre, ecart
        if proche is None or distance > PORTEE_ETIQUETTE:
            continue
        attribution[proche].append(
            (
                etiquette.group(0),
                [_nombre(etiquette.group(1)), _nombre(etiquette.group(2))],
                etiquette.end(),
                etiquette.end() + distance,
            )
        )
    return attribution


def _courbe(texte, titre, ordonnee, attribution):
    """Extracts data labels from a sliding setpoint chart.

    A point whose ordinate falls outside the axis tick marks is not corrected:
    it causes the entire curve to FAIL. « 20; 2018 » comes from a tick mark
    concatenated with the value; guessing that 2018 meant 20 would be exactly
    the kind of invention that rule 1 forbids.

    Args:
        texte: PDF text.
        titre: Chart title.
        ordonnee: Y-axis label.
        attribution: What `_attribuer_les_etiquettes` returns.

    Returns:
        dict: Extracted points and reading reservations.
    """
    retenues, suspects = [], []
    for brut, couple, debut, fin in attribution.get(titre, []):
        graduations = [float(g) for g in _GRADUATION.findall(texte[debut:fin])]
        if graduations and not (min(graduations) <= couple[1] <= max(graduations)):
            suspects.append(
                "« %s » : ordonnée %s hors des graduations "
                "[%g ; %g] du graphique — l'extraction a "
                "probablement collé deux nombres."
                % (brut, couple[1], min(graduations), max(graduations))
            )
            continue
        retenues.append((brut, couple, debut))
    if suspects:
        return {
            "points": None,
            "statut": A_CONFIRMER,
            "ordonnee": ordonnee,
            "a_confirmer": " ".join(suspects),
        }

    # Labels from the same chart follow one another in the stream. A gap
    # reveals a NEIGHBOURING chart, captured because it has no title of its
    # own — as in Test 6, where three points from another setpoint were grouped
    # under the supply-air temperature. We do not choose: we refuse and display
    # the groups, so that reading the PDF takes ten seconds.
    groupes = []
    for brut, couple, debut in retenues:
        if groupes and debut - groupes[-1][-1][2] <= ECART_MEME_GRAPHIQUE:
            groupes[-1].append((brut, couple, debut))
        else:
            groupes.append([(brut, couple, debut)])
    if len(groupes) > 1:
        return {
            "points": None,
            "statut": A_CONFIRMER,
            "ordonnee": ordonnee,
            "groupes_candidats": [[c for _, c, _ in groupe] for groupe in groupes],
            "a_confirmer": "%d groupes d'étiquettes se disputent ce graphique : %s. Un "
            "graphique voisin sans titre propre a été capté. Lire le PDF "
            "et retenir le bon groupe."
            % (
                len(groupes),
                " / ".join("[%s]" % ", ".join(brut for brut, _, _ in g) for g in groupes),
            ),
        }
    points = []
    for _, couple, _ in retenues:
        if couple not in points:
            points.append(couple)
    if not points:
        return {
            "points": None,
            "statut": A_CONFIRMER,
            "ordonnee": ordonnee,
            "a_confirmer": "Aucune étiquette de données lisible pour ce " "graphique.",
        }
    return {
        "points": points,
        "statut": SUR_GRAPHIQUE,
        "abscisse": "Aussenlufttemperatur (°C)",
        "ordonnee": ordonnee,
        "reserve_de_lecture": "Points relevés sur les ÉTIQUETTES DE DONNÉES du graphique. Les "
        "PALIERS au-delà de ces points ne sont pas étiquetés : le tracé "
        "les suggère constants, la spécification ne l'écrit pas.",
    }


def construire(numero_test):
    """Extracts the ventilation network for a test.

    Args:
        numero_test: 5 or 6.

    Returns:
        dict: Frozen reference dataset.

    Raises:
        ValueError: If the test has no ventilation network described here.
    """
    if numero_test not in CHAMPS:
        raise ValueError(
            "test %r sans réseau de ventilation décrit ici. "
            "Concernés : %s." % (numero_test, sorted(CHAMPS))
        )
    texte = _texte_du_pdf(numero_test)
    reference = {
        "_source": "SIA_4010_geteilter_Link/Test%d/Spezifikation_Test%d.pdf"
        % (numero_test, numero_test),
        "_producteur": "scripts/build_reseau_ventilation_reference.py",
        "_avertissement": "Ce fichier fige une LECTURE de la spécification, pas une "
        "validation. Rien n'y est calculé ni complété : un champ que la "
        "couche texte ne donne pas sort à `null`, en `A_CONFIRMER`.",
        "test": numero_test,
    }
    for entree in CHAMPS[numero_test]:
        bloc, cle, motif, conversion, source = entree[:5]
        depuis = entree[5] if len(entree) > 5 else None
        reference.setdefault(bloc, {})[cle] = _chercher(
            texte, motif, conversion, source, depuis
        )
    for bloc, cle, source, raison in TROUS[numero_test]:
        reference.setdefault(bloc, {})[cle] = {
            "valeur": None,
            "statut": A_CONFIRMER,
            "source": source,
            "a_confirmer": raison,
        }
    attribution = _attribuer_les_etiquettes(
        texte, [titre for _, titre, _ in COURBES[numero_test]]
    )
    reference["courbes"] = dict(
        (cle, _courbe(texte, titre, ordonnee, attribution))
        for cle, titre, ordonnee in COURBES[numero_test]
    )
    reference["_bilan"] = bilan(reference)
    return reference


def bilan(reference):
    """Counts what has been extracted and what has not.

    A reference dataset where we do not know how many fields are empty invites
    us to believe it is complete.

    Args:
        reference: Built reference dataset.

    Returns:
        dict: Counts by status, and list of fields to confirm.
    """
    effectifs, a_confirmer = {}, []
    for nom_bloc, bloc in sorted(reference.items()):
        if nom_bloc.startswith("_") or not isinstance(bloc, dict):
            continue
        for cle, champ in sorted(bloc.items()):
            if not isinstance(champ, dict) or "statut" not in champ:
                continue
            statut = champ["statut"]
            effectifs[statut] = effectifs.get(statut, 0) + 1
            if statut == A_CONFIRMER:
                a_confirmer.append("%s.%s" % (nom_bloc, cle))
    return {"effectifs": effectifs, "a_confirmer": a_confirmer}


def main(arguments=()):
    """Entry point.

    Args:
        arguments: `--ecrire` to freeze the files.

    Returns:
        int: 0 if both tests could be extracted.
    """
    for numero in sorted(CHAMPS):
        try:
            reference = construire(numero)
        except IOError as erreur:
            print("Test %d : %s" % (numero, erreur))
            return 1
        compte = reference["_bilan"]["effectifs"]
        print(
            "Test %d : %d relevés, %d sur graphique, %d à confirmer"
            % (
                numero,
                compte.get(RELEVE, 0),
                compte.get(SUR_GRAPHIQUE, 0),
                compte.get(A_CONFIRMER, 0),
            )
        )
        for champ in reference["_bilan"]["a_confirmer"]:
            print("    à confirmer : %s" % champ)
        if "--ecrire" in arguments:
            chemin = os.path.join(_SORTIE, "test-%d.reseau.json" % numero)
            with io.open(chemin, "w", encoding="utf-8") as flux:
                flux.write(
                    json.dumps(reference, ensure_ascii=False, indent=2, sort_keys=True)
                )
            print("    écrit : %s" % os.path.relpath(chemin, _RACINE))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
