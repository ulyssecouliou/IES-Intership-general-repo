# -*- coding: utf-8 -*-
"""Tests of the ventilation network extraction for SIA tests 5 and 6.

What these tests guard is NOT that the extraction finds many values: it is
that it **refuses** when it does not know. Three traps were encountered while
writing the extractor, and all three produced a plausible value:

* `Auslegungsleistung` and `Austrittstemperatur` appear on both coils.
  Without a section anchor, the heating coil inherited the chiller values
  — 8.6 kW instead of 3.5 kW;
* "20; 2018" is an axis graduation stuck to a value. Reading 2018 as
  20 would be an invention;
* labels from a neighbouring chart with no title were filed under the
  supply-air temperature of Test 6.

None would have caused a failure before the final comparison.
"""

import pytest

from scripts import build_reseau_ventilation_reference as extracteur


@pytest.fixture(scope="module", params=[5, 6])
def reference(request):
    try:
        return extracteur.construire(request.param)
    except IOError:
        pytest.skip("spécification absente")


# --------------------------------------------------------------------------
# Nothing is guessed
# --------------------------------------------------------------------------


def test_un_motif_introuvable_ne_rend_jamais_de_valeur():
    champ = extracteur._chercher(
        "rien ici", r"introuvable (\d+)", extracteur._nombre, "source"
    )
    assert champ["valeur"] is None
    assert champ["statut"] == extracteur.A_CONFIRMER
    assert "devinée" in champ["a_confirmer"]


def test_une_section_absente_ne_rend_jamais_de_valeur():
    champ = extracteur._chercher(
        "Auslegungsleistung 8.6 kW",
        r"Auslegungsleistung ([\d.]+)",
        extracteur._nombre,
        "source",
        depuis="Lufterhitzer",
    )
    assert champ["valeur"] is None
    assert champ["statut"] == extracteur.A_CONFIRMER


def test_lancrage_de_section_evite_de_lire_le_mauvais_appareil():
    """THE TRAP. Both coils carry the same label; the first in the flow
    would win, silently."""
    texte = (
        "Luftkühler Auslegungsleistung 8.6 kW\n" "Lufterhitzer Auslegungsleistung 3.5 kW"
    )
    motif = r"Auslegungsleistung\s*([\d.]+)\s*kW"
    froide = extracteur._chercher(
        texte, motif, extracteur._nombre, "x", depuis="Luftkühler"
    )
    chaude = extracteur._chercher(
        texte, motif, extracteur._nombre, "x", depuis="Lufterhitzer"
    )
    assert froide["valeur"] == 8.6
    assert chaude["valeur"] == 3.5


def test_les_separateurs_de_milliers_du_pdf_sont_lus():
    assert extracteur._nombre("1'040") == 1040
    assert extracteur._nombre("6150") == 6150
    assert extracteur._nombre("0.765") == 0.765


def test_un_entier_reste_un_entier():
    """`20.0 min-1` written in a reference invites belief in a measurement."""
    assert isinstance(extracteur._nombre("20"), int)


# --------------------------------------------------------------------------
# Charts: refuse rather than repair
# --------------------------------------------------------------------------


def test_une_ordonnee_hors_graduations_fait_echouer_la_courbe():
    """ "20; 2018": graduation 18 is stuck to value 20. Correcting to 20
    would be exactly the invention rule 1 forbids."""
    texte = "20; 2018\n18\n20\n40\n42\nHeizwassertemperatur"
    attribution = extracteur._attribuer_les_etiquettes(texte, ["Heizwassertemperatur"])
    courbe = extracteur._courbe(
        texte, "Heizwassertemperatur", "Heizwassertemperatur", attribution
    )
    assert courbe["points"] is None
    assert courbe["statut"] == extracteur.A_CONFIRMER
    assert "collé" in courbe["a_confirmer"]


def test_deux_groupes_detiquettes_font_echouer_la_courbe():
    """A neighbouring chart without its own title is attributed to the next one."""
    texte = "17.5; 25 19; 22" + " " * 120 + "12; 20 20; 18" + "\n15\n30\nZulufttemperatur"
    attribution = extracteur._attribuer_les_etiquettes(texte, ["Zulufttemperatur"])
    courbe = extracteur._courbe(
        texte, "Zulufttemperatur", "Zulufttemperatur", attribution
    )
    assert courbe["points"] is None
    assert len(courbe["groupes_candidats"]) == 2


def test_les_groupes_candidats_sont_montres_et_non_arbitres():
    """Showing both makes reading the PDF a matter of seconds;
    choosing one makes an error a matter of weeks."""
    texte = "17.5; 25" + " " * 120 + "12; 20 20; 18" + "\n15\n30\nZulufttemperatur"
    attribution = extracteur._attribuer_les_etiquettes(texte, ["Zulufttemperatur"])
    courbe = extracteur._courbe(texte, "Zulufttemperatur", "x", attribution)
    assert [17.5, 25] in courbe["groupes_candidats"][0]
    assert [12, 20] in courbe["groupes_candidats"][1]


def test_une_etiquette_va_au_graphique_le_plus_proche():
    """The first defect: "does the title appear further on" filed the
    chilled-water points under the hot-water chart too."""
    texte = "12; 18\nKaltwassertemperatur\n-10; 40\nHeizwassertemperatur"
    attribution = extracteur._attribuer_les_etiquettes(
        texte, ["Kaltwassertemperatur", "Heizwassertemperatur"]
    )
    assert len(attribution["Kaltwassertemperatur"]) == 1
    assert len(attribution["Heizwassertemperatur"]) == 1


def test_une_etiquette_orpheline_nest_attribuee_a_personne():
    texte = "12; 18" + " " * 900 + "Kaltwassertemperatur"
    attribution = extracteur._attribuer_les_etiquettes(texte, ["Kaltwassertemperatur"])
    assert attribution["Kaltwassertemperatur"] == []


# --------------------------------------------------------------------------
# Produced reference data
# --------------------------------------------------------------------------


def test_chaque_champ_porte_son_statut_et_sa_source(reference):
    for nom_bloc, bloc in sorted(reference.items()):
        if nom_bloc.startswith("_") or nom_bloc == "courbes":
            continue
        if not isinstance(bloc, dict):
            continue
        for cle, champ in sorted(bloc.items()):
            assert "statut" in champ, (nom_bloc, cle)
            assert champ.get("source"), (nom_bloc, cle)


def test_un_champ_a_confirmer_ne_porte_jamais_de_valeur(reference):
    """The central rule of the repository: an absence is not a measurement."""
    for nom_bloc, bloc in sorted(reference.items()):
        if nom_bloc.startswith("_") or not isinstance(bloc, dict):
            continue
        for cle, champ in sorted(bloc.items()):
            if not isinstance(champ, dict):
                continue
            if champ.get("statut") != extracteur.A_CONFIRMER:
                continue
            assert champ.get("valeur") is None, (nom_bloc, cle)
            assert champ.get("points") is None, (nom_bloc, cle)
            assert champ.get("a_confirmer"), (nom_bloc, cle)


def test_le_bilan_compte_les_trous(reference):
    """A reference where the number of gaps is unknown invites belief that
    it is complete."""
    bilan = reference["_bilan"]
    assert bilan["effectifs"].get(extracteur.A_CONFIRMER, 0) == len(bilan["a_confirmer"])
    assert bilan["a_confirmer"], "aucun trou signalé : suspect"


def test_les_variantes_du_test_5_ne_sont_pas_arbitrees():
    """Five parameters depend on the variant and the PDF carries four
    columns for two cells. Choosing would build two wrong variants out of four."""
    try:
        reference = extracteur.construire(5)
    except IOError:
        pytest.skip("spécification absente")
    for bloc, cle in (
        ("recuperateur", "type_par_variante"),
        ("recuperateur", "taux_temperature_par_variante"),
        ("recuperateur", "taux_humidite_par_variante"),
        ("humidificateur", "type_par_variante"),
        ("ventilateurs", "part_pression_constante_pa"),
    ):
        champ = reference[bloc][cle]
        assert champ["statut"] == extracteur.A_CONFIRMER, (bloc, cle)
        assert "colonnes" in champ["a_confirmer"], (bloc, cle)


def test_la_contradiction_de_debit_du_test_6_est_signalee():
    """Page 1 announces 3'000 m3/h and the RLT section 6'150. Confusing them
    would falsify the entire air-flow balance."""
    try:
        reference = extracteur.construire(6)
    except IOError:
        pytest.skip("spécification absente")
    champ = reference["reseau"]["debit_du_local_restaurant_m3_h"]
    assert champ["statut"] == extracteur.A_CONFIRMER
    assert "CONTRADICTION" in champ["a_confirmer"]


def test_les_batteries_ne_partagent_pas_leurs_valeurs():
    try:
        reference = extracteur.construire(5)
    except IOError:
        pytest.skip("spécification absente")
    froide = reference["batterie_froide"]
    chaude = reference["batterie_chaude"]
    assert froide["puissance_kw"]["valeur"] != chaude["puissance_kw"]["valeur"]
    assert froide["air_entrant_c"]["valeur"] != chaude["air_entrant_c"]["valeur"]


# --------------------------------------------------------------------------
# Entry forms
# --------------------------------------------------------------------------


@pytest.mark.parametrize("numero", [5, 6])
def test_la_fiche_met_les_trous_en_tete(numero):
    from scripts import build_fiche_apachehvac_56 as fiche

    try:
        document = fiche.construire(numero)
    except IOError:
        pytest.skip("référentiel non figé")
    position_trous = document.find("À trancher AVANT")
    position_composants = document.find("## Composants")
    assert 0 < position_trous < position_composants


@pytest.mark.parametrize("numero", [5, 6])
def test_un_champ_a_trancher_naffiche_aucune_valeur(numero):
    """Displaying a dash would suggest a zero; displaying a value would
    suggest a measurement."""
    from scripts import build_fiche_apachehvac_56 as fiche

    champ = {
        "statut": extracteur.A_CONFIRMER,
        "valeur": None,
        "source": "x",
        "a_confirmer": "y",
    }
    assert fiche._valeur_lisible(champ) == "**À TRANCHER**"


@pytest.mark.parametrize("numero", [5, 6])
def test_la_fiche_ne_declare_rien_conforme(numero):
    from scripts import build_fiche_apachehvac_56 as fiche

    try:
        document = fiche.construire(numero)
    except IOError:
        pytest.skip("référentiel non figé")
    for interdit in ("validé", "PASS"):
        assert interdit not in document, (numero, interdit)


@pytest.mark.parametrize("numero", [5, 6])
def test_la_fiche_rappelle_que_le_climat_manque(numero):
    """Without the SIA 2028 Kloten climate, a simulation of this test is not
    a SIA validation case — hiding this would suggest the opposite."""
    from scripts import build_fiche_apachehvac_56 as fiche

    try:
        document = fiche.construire(numero)
    except IOError:
        pytest.skip("référentiel non figé")
    assert "SIA 2028" in document
    assert "Kloten" in document
