# -*- coding: utf-8 -*-
"""Tests of the dispersion-band adapter (tests 2 to 6), WITHOUT VE.

A `ResultsReader` double replaces the API: everything that matters here is
testable without a licence. The tests target especially what a plausible but
wrong implementation would do -- guessing a variable name, falling back an
unknown aggregation to sum, or returning an empty candidate that would read
as "nothing passes".
"""

import io
import os

import pytest

from engine import sia_bandes_engine as moteur
from ve_adapter import bandes_adapter as adaptateur


class FauxResultsReader(object):
    """Minimal double of `iesve.ResultsReader`.

    MODELLED ON THE REAL API, not on what was assumed about it. The previous
    version of this double took a `niveau` argument to `get_variables` and
    returned strings: it was VALIDATING the error it should have flagged. VE,
    on `ZOER_C1.aps` on 2026-08-06, rejects the argument (`ArgumentError`)
    and returns dictionaries carrying `aps_varname`, `display_name` and
    `model_level`.

    Attributes:
        series: `{(varname, niveau): serie}`.
        variables: List of entries, each a dict as the API returns.
    """

    def __init__(self, series=None, variables=None):
        self.series = series or {}
        self.variables = list(variables or [])
        self.ferme = False

    def get_variables(self):
        # No argument: that is the real API contract.
        return list(self.variables)

    def get_results(self, varname, niveau):
        cle = (varname, niveau)
        if cle not in self.series:
            raise KeyError(varname)
        return self.series[cle]

    def get_room_results(self, room_id, varname, niveau):
        return self.get_results(varname, niveau)

    def close(self):
        self.ferme = True


def _ref(numero):
    try:
        return moteur.charger_reference(numero)
    except IOError:
        pytest.skip("reference Test %d absente" % numero)


# --------------------------------------------------------------------------
# API safeguard
# --------------------------------------------------------------------------


def test_lapi_reelle_presente_toutes_les_methodes_employees():
    """Written against an introspected VE 2025, not against the documentation."""
    assert adaptateur.verifier_api() == dict(
        (m, True) for m in adaptateur.METHODES_REQUISES
    )


def test_une_methode_disparue_est_signalee():
    """This has already happened: `element_categories` was sought on
    `VECdbProject` whereas it belongs to the `iesve` module."""
    amputee = {"ResultsReader": {"members": ["close"]}}
    with pytest.raises(adaptateur.ApiIncompatible, match="get_results"):
        adaptateur.verifier_api(amputee)


def test_une_surface_vide_est_signalee():
    with pytest.raises(adaptateur.ApiIncompatible):
        adaptateur.verifier_api({})


# --------------------------------------------------------------------------
# Bindings: nothing is guessed
# --------------------------------------------------------------------------


@pytest.mark.parametrize("numero", adaptateur.TESTS_COUVERTS)
def test_les_liaisons_couvrent_exactement_les_grandeurs(numero):
    """A stray space in a German label would make the binding unfindable
    once resolved. Keys are generated, not retyped."""
    reference = _ref(numero)
    attendues = set(g["libelle_de"] for g in reference["grandeurs"])
    assert set(adaptateur.LIAISONS[numero]) == attendues


@pytest.mark.parametrize("numero", adaptateur.TESTS_COUVERTS)
def test_aucune_liaison_nest_resolue_par_defaut(numero):
    """No `aps_varname` can be established outside a real `.aps` file."""
    assert adaptateur.liaisons_resolues(numero) == {}


def test_extraire_refuse_quand_rien_nest_resolu():
    """Returning an empty candidate would read as "nothing passes", whereas
    nothing was looked for."""
    with pytest.raises(adaptateur.LiaisonNonResolue, match="decouvrir_variables"):
        adaptateur.extraire_candidat(2, FauxResultsReader(), _ref(2))


def test_un_test_hors_perimetre_est_refuse():
    with pytest.raises(ValueError, match="hors de port"):
        adaptateur.extraire_candidat(7, FauxResultsReader(), {"grandeurs": []})


# --------------------------------------------------------------------------
# Aggregation
# --------------------------------------------------------------------------


def test_somme_annuelle_convertit_les_watts_en_kwh():
    """8760 h at 1000 W equals 8760 kWh, not 8 760 000."""
    assert adaptateur.agreger([1000.0] * 8760, "somme_annuelle") == 8760.0


@pytest.mark.parametrize(
    "methode,attendu", [("moyenne", 2.0), ("maximum", 3.0), ("minimum", 1.0)]
)
def test_les_autres_agregations(methode, attendu):
    assert adaptateur.agreger([1.0, 2.0, 3.0], methode) == attendu


def test_une_methode_inconnue_est_refusee():
    """Never a silent fallback to sum: that would be a plausible and wrong
    number."""
    with pytest.raises(ValueError, match="inconnue"):
        adaptateur.agreger([1.0], "mediane")


def test_une_serie_vide_donne_none_pas_zero():
    """Zero is a measurement; absence is not."""
    assert adaptateur.agreger([], "somme_annuelle") is None
    assert adaptateur.agreger(None, "moyenne") is None


def test_les_trous_sont_ecartes_pas_comptes_comme_zero():
    assert adaptateur.agreger([1.0, None, 3.0], "moyenne") == 2.0


# --------------------------------------------------------------------------
# Extraction, once a binding is resolved
# --------------------------------------------------------------------------


def _resoudre(monkeypatch, numero, libelle, varname, niveau):
    """Resolves ONE binding, without touching the original module."""
    liaisons = dict(
        (cle, dict((k, dict(v)) for k, v in valeur.items()))
        for cle, valeur in adaptateur.LIAISONS.items()
    )
    liaisons[numero][libelle]["aps_varname"] = varname
    liaisons[numero][libelle]["niveau"] = niveau
    monkeypatch.setattr(adaptateur, "LIAISONS", liaisons)


def test_une_liaison_resolue_produit_un_candidat_exploitable(monkeypatch):
    reference = _ref(3)
    libelle = reference["grandeurs"][0]["libelle_de"]
    _resoudre(monkeypatch, 3, libelle, "LIGHT_POWER", adaptateur.NIVEAU_LOCAL)

    lecteur = FauxResultsReader(
        series={("LIGHT_POWER", adaptateur.NIVEAU_LOCAL): [1000.0] * 8760}
    )
    candidat = adaptateur.extraire_candidat(3, lecteur, reference)

    assert libelle in candidat
    # All cases share the same series in this double: all at 8760 kWh.
    assert set(candidat[libelle].values()) == {8760.0}
    # And the engine must be able to consume it.
    assert moteur.evaluer(reference, candidat)["nb_non_evaluables"] == 0


def test_une_serie_absente_ne_fabrique_pas_de_valeur(monkeypatch):
    reference = _ref(3)
    libelle = reference["grandeurs"][0]["libelle_de"]
    _resoudre(monkeypatch, 3, libelle, "INEXISTANT", adaptateur.NIVEAU_LOCAL)
    assert adaptateur.extraire_candidat(3, FauxResultsReader(), reference) == {}


def test_les_grandeurs_non_resolues_restent_absentes(monkeypatch):
    """They must not appear as zero: the engine treats them as
    NOT_CHECKABLE, which is the truth."""
    reference = _ref(2)
    libelle = reference["grandeurs"][0]["libelle_de"]
    _resoudre(monkeypatch, 2, libelle, "SOLAR", adaptateur.NIVEAU_LOCAL)

    lecteur = FauxResultsReader(
        series={("SOLAR", adaptateur.NIVEAU_LOCAL): [500.0] * 8760}
    )
    candidat = adaptateur.extraire_candidat(2, lecteur, reference)

    assert list(candidat) == [libelle]
    assert reference["grandeurs"][1]["libelle_de"] not in candidat
    assert moteur.evaluer(reference, candidat)["nb_non_evaluables"] > 0


# --------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------


def _variable(varname, niveau, display=None):
    """Entry from `get_variables()`, in the real API form."""
    return {
        "aps_varname": varname,
        "display_name": display or varname,
        "model_level": niveau,
        "units_type": "Power",
    }


_VARIABLES = [
    _variable("A", adaptateur.NIVEAU_LOCAL),
    _variable("B_SOLAR", adaptateur.NIVEAU_LOCAL, "Window solar gains"),
    _variable("C", adaptateur.NIVEAU_SYSTEME),
]


def test_la_decouverte_liste_tout_le_fichier_sans_filtre():
    lecteur = FauxResultsReader(variables=_VARIABLES)
    trouvees = adaptateur.decouvrir_variables(lecteur)
    assert [v["aps_varname"] for v in trouvees] == ["A", "B_SOLAR", "C"]


def test_le_niveau_se_lit_sur_la_variable_pas_sur_lappel():
    """`get_variables('z')` raises ArgumentError in VE: the level is carried
    by `model_level`, entry by entry. Filtering is done on our side."""
    lecteur = FauxResultsReader(variables=_VARIABLES)
    trouvees = adaptateur.decouvrir_variables(lecteur, adaptateur.NIVEAU_LOCAL)
    assert [v["aps_varname"] for v in trouvees] == ["A", "B_SOLAR"]


def test_la_decouverte_filtre_sans_tenir_compte_de_la_casse():
    lecteur = FauxResultsReader(variables=_VARIABLES)
    trouvees = adaptateur.decouvrir_variables(lecteur, adaptateur.NIVEAU_LOCAL, "solar")
    assert [v["aps_varname"] for v in trouvees] == ["B_SOLAR"]


def test_le_motif_cherche_aussi_dans_le_libelle_daffichage():
    """'Window solar gains' is the display_name; the aps_varname can be
    anything. Searching only in one would make discovery blind."""
    lecteur = FauxResultsReader(variables=_VARIABLES)
    trouvees = adaptateur.decouvrir_variables(lecteur, motif="window")
    assert [v["aps_varname"] for v in trouvees] == ["B_SOLAR"]


def test_la_cle_name_nexiste_pas_dans_lapi():
    """The old version filtered on `variable.get('name', ...)`. This field
    does not exist: the filter fell back to the whole dict, so it matched
    almost anything."""
    assert "name" not in adaptateur.CHAMPS_NOMMANTS
    lecteur = FauxResultsReader(variables=_VARIABLES)
    assert adaptateur.decouvrir_variables(lecteur, motif="units_type") == []


def test_letat_des_liaisons_nomme_ce_qui_manque():
    texte = adaptateur.etat_des_liaisons()
    assert "0/8" in texte and "0/6" in texte
    assert "decouvrir_variables" in texte


def test_pas_dimport_iesve_au_chargement():
    """Rule 4: the module must remain importable in CI, without a licence."""
    chemin = os.path.abspath(adaptateur.__file__).replace(".pyc", ".py")
    with io.open(chemin, encoding="utf-8") as flux:
        for numero, ligne in enumerate(flux, 1):
            nu = ligne.strip()
            assert not nu.startswith("import iesve"), numero
            assert not nu.startswith("from iesve"), numero


# --------------------------------------------------------------------------
# Probe candidates: leads, never bindings
# --------------------------------------------------------------------------

import json as _json  # noqa: E402

_RACINE = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir)
)
#: FROZEN, versioned catalogue. We do NOT read `outputs/sonde_aps.json`:
#: that directory is ignored by Git, so absent from a fresh clone -- these
#: tests would skip silently, giving the false impression that candidates
#: are verified when nothing controls them anymore.
_CATALOGUE = os.path.join(
    _RACINE, "refs", "reference-data", "iesve-aps-variables-ve2025.json"
)


@pytest.fixture(scope="module")
def variables_relevees():
    """Variables as a real .aps file returned them, on 2026-08-06.

    Returns:
        dict: `{(aps_varname, model_level): entry}`. The same pair may
            carry several display_names: we keep the first, the catalogue
            order being deterministic.
    """
    if not os.path.exists(_CATALOGUE):
        pytest.skip("catalogue absent : scripts/freeze_aps_variables.py")
    with io.open(_CATALOGUE, encoding="utf-8") as flux:
        catalogue = _json.load(flux)
    par_cle = {}
    for variable in catalogue["variables"]:
        par_cle.setdefault(
            (variable.get("aps_varname"), variable.get("model_level")), variable
        )
    return par_cle


def test_le_catalogue_est_versionne():
    """If it fell back under outputs/, all tests in this section would skip
    without anyone noticing."""
    assert os.path.exists(_CATALOGUE), _CATALOGUE
    normalise = _CATALOGUE.replace(os.sep, "/")
    assert "/refs/reference-data/" in normalise


def test_le_catalogue_couvre_les_douze_niveaux(variables_relevees):
    niveaux = set(niveau for (_, niveau) in variables_relevees)
    assert niveaux == set(adaptateur.NIVEAUX_RELEVES)


def test_aucun_candidat_ne_resout_de_liaison():
    """The exact risk this separation exists to eliminate: 'Window solar
    gains' is a VE variable name. Re-using it without having compared its
    definition to the workbook would produce a plausible and wrong number.
    """
    for numero in adaptateur.TESTS_COUVERTS:
        assert adaptateur.liaisons_resolues(numero) == {}


def test_extraire_ignore_integralement_les_candidats():
    assert adaptateur.candidats_a_confirmer(2)
    with pytest.raises(adaptateur.LiaisonNonResolue):
        adaptateur.extraire_candidat(2, FauxResultsReader(), _ref(2))


# --- Names are compared against the probe, not retyped from memory --------


def test_chaque_candidat_existe_vraiment_dans_un_aps(variables_relevees):
    """A name retyped from memory is a wrong name."""
    for libelle, piste in adaptateur.CANDIDATS_PAR_GRANDEUR.items():
        nom = piste["aps_varname_candidat"]
        if nom is None:
            continue  # case "no unique variable", handled below
        assert (nom, piste["niveau"]) in variables_relevees, libelle


def test_le_libelle_et_lunite_du_candidat_sont_les_bons(variables_relevees):
    """The display_name is used to identify the quantity in the VE interface:
    if wrong, human verification goes down the wrong track."""
    for piste in adaptateur.CANDIDATS_PAR_GRANDEUR.values():
        if piste["aps_varname_candidat"] is None:
            continue
        releve = variables_relevees[(piste["aps_varname_candidat"], piste["niveau"])]
        assert piste["display_name"] == releve.get("display_name")
        assert piste["units_type"] == releve.get("units_type")


def test_les_deux_termes_de_la_somme_existent(variables_relevees):
    """'Warmeabfuhr Luftkuhler total' has no unique variable, but both
    terms of the sum must exist, otherwise the reservation is pointless."""
    for nom in ("Sys Mech vent cooling load", "Sys Mech vent dehum load"):
        assert (nom, adaptateur.NIVEAU_SYSTEME) in variables_relevees


def test_la_recuperation_sur_lair_neuf_nexpose_quune_temperature(variables_relevees):
    """Structural observation. There are two heat-recovery variables in Power
    at the same level -- 'Sys Process heat recovered' and 'Sys Process heat
    recovery heat pump' -- but they relate to PROCESSES, not to outdoor air.
    Confusing them would give a plausible and wrong number."""
    ventilation = variables_relevees[
        ("Sys Mech vent heat recovery temp", adaptateur.NIVEAU_SYSTEME)
    ]
    assert ventilation["units_type"] == "Temperature"
    for nom in ("Sys Process heat recovered", "Sys Process heat recovery heat pump"):
        assert (
            variables_relevees[(nom, adaptateur.NIVEAU_SYSTEME)]["units_type"] == "Power"
        )
    # If an outdoor-air heat recovery energy appeared, this test must fail
    # so that it gets bound.
    ventilation_wrg = sorted(
        nom
        for (nom, niveau) in variables_relevees
        if niveau == adaptateur.NIVEAU_SYSTEME
        and "mech vent" in (nom or "").lower()
        and "recovery" in (nom or "").lower()
    )
    assert ventilation_wrg == ["Sys Mech vent heat recovery temp"]


# --- Table consistency -----------------------------------------------------


def test_chaque_piste_declare_sa_preuve_et_sa_reserve():
    """A lead without provenance or reservation ends up being taken for a
    result."""
    for piste in adaptateur.CANDIDATS_PAR_GRANDEUR.values():
        assert piste["preuve"] and piste["niveau_de_preuve"]
        assert piste["a_confirmer"]


def test_toutes_les_grandeurs_citees_existent_dans_les_liaisons():
    """A key matching no quantity would be a dead lead."""
    connues = set()
    for grandeurs in adaptateur.LIAISONS.values():
        connues |= set(grandeurs)
    assert set(adaptateur.CANDIDATS_PAR_GRANDEUR) <= connues
    assert set(adaptateur.SANS_CANDIDAT) <= connues


def test_aucune_grandeur_nest_a_la_fois_pistee_et_muette():
    communes = set(adaptateur.CANDIDATS_PAR_GRANDEUR) & set(adaptateur.SANS_CANDIDAT)
    assert not communes, communes


def test_une_grandeur_partagee_porte_la_meme_piste_dans_tous_ses_tests():
    """'Warmezufuhr Lufterwarmer' appears in tests 4, 5 and 6. A table
    indexed by test would have let these three copies diverge."""
    pistes = [
        adaptateur.candidats_a_confirmer(n).get("Wärmezufuhr Lufterwärmer")
        for n in (4, 5, 6)
    ]
    assert all(p is not None for p in pistes)
    assert pistes[0] == pistes[1] == pistes[2]


def test_le_candidat_solaire_est_passe_dallegation_a_releve():
    """It was backed only by metadata whose trace was missing. The probe
    of 2026-08-06 found the variable in a real .aps file, independently."""
    piste = adaptateur.candidats_a_confirmer(2)["Jahresenergie solarer Wärmeeintrag"]
    assert piste["niveau_de_preuve"] == "RELEVE"
    assert piste["aps_varname_candidat"] == "Window solar gains"


def test_le_test_6_na_de_piste_que_par_grandeurs_partagees():
    """Its six quantities are heat-recovery items, fans, or the Luftkuhler
    sum. Only those shared with test 4 have a lead."""
    assert set(adaptateur.candidats_a_confirmer(6)) == {
        "Wärmezufuhr Lufterwärmer",
        "Wärmeabfuhr Luftkühler total",
    }


# --- Status display --------------------------------------------------------


def test_letat_distingue_les_trois_situations():
    """'not yet searched' and 'searched, nothing matches' must never read the
    same."""
    texte = adaptateur.etat_des_liaisons()
    assert "candidat a confirmer : Window solar gains" in texte
    assert "cherche, aucune variable ne correspond" in texte
    assert "pas de variable unique" in texte
    assert "None" not in texte


def test_letat_ne_compte_aucun_candidat_comme_resolu():
    texte = adaptateur.etat_des_liaisons()
    for numero, attendu in ((2, "0/2"), (3, "0/1"), (4, "0/3"), (5, "0/8"), (6, "0/6")):
        assert "Test %d : %s" % (numero, attendu) in texte


def test_les_niveaux_releves_depassent_les_trois_nommes():
    """Believing that z/v/w exhaust the levels caused missing lighting
    (level e) and incident solar (level s)."""
    for niveau in (adaptateur.NIVEAU_ENERGIE, adaptateur.NIVEAU_SURFACE):
        assert niveau in adaptateur.NIVEAUX_RELEVES
    assert len(adaptateur.NIVEAUX_RELEVES) == 12


# --------------------------------------------------------------------------
# Second criterion: the hourly series and label correspondence
# --------------------------------------------------------------------------

from engine import sia_distributions_engine as moteur_distributions  # noqa: E402


def _ref_distributions(numero):
    try:
        return moteur_distributions.charger_reference(numero)
    except moteur_distributions.ReferenceIntrouvable:
        pytest.skip("referentiel de distributions du Test %d absent" % numero)


@pytest.mark.parametrize("numero", moteur_distributions.TESTS_SUPPORTES)
def test_toute_grandeur_de_distribution_est_declaree(numero):
    """An undeclared quantity would raise `libelle_annuel`, which is the
    intended behaviour -- but better to know here than mid-extraction."""
    reference = _ref_distributions(numero)
    relevees = set(b["grandeur"] for b in reference["distributions"])
    declarees = set(adaptateur.CORRESPONDANCE_DISTRIBUTIONS[numero])
    assert relevees == declarees, (numero, relevees ^ declarees)


@pytest.mark.parametrize("numero", moteur_distributions.TESTS_SUPPORTES)
def test_toute_cible_annuelle_existe_dans_les_liaisons(numero):
    """A mis-spelt target would be unfindable once the binding is resolved --
    the same trap as the retyped German labels."""
    for cible in adaptateur.CORRESPONDANCE_DISTRIBUTIONS[numero].values():
        if cible is not None:
            assert cible in adaptateur.LIAISONS[numero], (numero, cible)


def test_les_diagnostics_sont_declares_comme_tels():
    """'Einstrahlung auf Fensterebene', 'Beleuchtungsstarke',
    'Zulufttemperatur': the workbook traces their distribution, but the
    specifications classify them under Diagnoseresultate. They are not
    criteria."""
    assert adaptateur.libelle_annuel(2, "Einstrahlung auf Fensterebene gesamt") is None
    assert adaptateur.libelle_annuel(3, "Beleuchtungsstärke") is None
    assert adaptateur.libelle_annuel(5, "Zulufttemperatur im Betrieb") is None


def test_une_grandeur_de_puissance_pointe_vers_son_energie_annuelle():
    """The two criteria do not name the quantities the same way: power (W)
    for the distribution, energy (kWh) for the annual sum. It is the same
    physical quantity at two stages."""
    assert adaptateur.libelle_annuel(3, "Beleuchtungsleistung") == "Beleuchtungsenergie"
    assert (
        adaptateur.libelle_annuel(5, "Leistung Lufterwärmer")
        == "Wärmezufuhr Lufterwärmer"
    )


def test_une_grandeur_inconnue_leve_au_lieu_de_rendre_none():
    """Returning `None` would confuse it with a diagnostic, and would make
    a criterion disappear silently."""
    with pytest.raises(KeyError, match="non déclarée"):
        adaptateur.libelle_annuel(3, "Grandeur inventee")


def test_deux_grandeurs_annuelles_nont_pas_de_distribution():
    """Befeuchtungsenergie and Hilfsenergie WRG: the workbook carries no
    distribution sheet for them. Their only criterion is the annual sum --
    an observation, not an oversight."""
    cibles = set(
        v for v in adaptateur.CORRESPONDANCE_DISTRIBUTIONS[5].values() if v is not None
    )
    for libelle in adaptateur.SANS_DISTRIBUTION[5]:
        assert libelle in adaptateur.LIAISONS[5]
        assert libelle not in cibles


def test_la_couverture_annuelle_est_complete():
    """Every quantity in LIAISONS has either a distribution or an explicit
    declaration that it has none. Silence would read as an oversight."""
    for numero in moteur_distributions.TESTS_SUPPORTES:
        cibles = set(
            v
            for v in adaptateur.CORRESPONDANCE_DISTRIBUTIONS[numero].values()
            if v is not None
        )
        sans = set(adaptateur.SANS_DISTRIBUTION.get(numero, ()))
        assert set(adaptateur.LIAISONS[numero]) == cibles | sans, numero


# --- Reading the raw series -----------------------------------------------


def test_la_serie_est_rendue_brute_sans_agregation(monkeypatch):
    """The workbook wants the 8760 values and computes the sum and distribution
    itself. Delivering an aggregate satisfies only half the criteria."""
    libelle = "Beleuchtungsenergie"
    _resoudre(monkeypatch, 3, libelle, "LIGHT", adaptateur.NIVEAU_LOCAL)
    serie = [float(i) for i in range(8760)]
    lecteur = FauxResultsReader(series={("LIGHT", adaptateur.NIVEAU_LOCAL): serie})
    assert adaptateur.extraire_serie(3, lecteur, libelle) == serie


def test_une_liaison_non_resolue_refuse_la_serie():
    """Returning an empty series would read as 'the quantity equals zero'."""
    with pytest.raises(adaptateur.LiaisonNonResolue, match="non résolue"):
        adaptateur.extraire_serie(3, FauxResultsReader(), "Beleuchtungsenergie")


def test_une_grandeur_inconnue_du_test_est_refusee():
    with pytest.raises(adaptateur.LiaisonNonResolue, match="inconnue"):
        adaptateur.extraire_serie(3, FauxResultsReader(), "Inexistante")


def test_une_serie_absente_donne_none_pas_une_liste_vide(monkeypatch):
    _resoudre(monkeypatch, 3, "Beleuchtungsenergie", "ABSENT", adaptateur.NIVEAU_LOCAL)
    assert (
        adaptateur.extraire_serie(3, FauxResultsReader(), "Beleuchtungsenergie") is None
    )


def test_la_serie_brute_se_classe_avec_le_moteur(monkeypatch):
    """End to end: read the series from VE, classify it with the workbook
    bounds, compare against the reference programmes."""
    reference = _ref_distributions(3)
    bloc = reference["distributions"][0]
    bornes = [e["borne_superieure"] for e in bloc["effectifs"]]

    _resoudre(monkeypatch, 3, "Beleuchtungsenergie", "LIGHT", adaptateur.NIVEAU_LOCAL)
    serie = [0.0] * 8760
    lecteur = FauxResultsReader(series={("LIGHT", adaptateur.NIVEAU_LOCAL): serie})

    brute = adaptateur.extraire_serie(3, lecteur, "Beleuchtungsenergie")
    effectifs = moteur_distributions.classer(brute, bornes)
    assert sum(effectifs) == 8760

    resultat = moteur_distributions.evaluer(
        reference, {(bloc["cas"], bloc["grandeur"]): effectifs}
    )
    assert resultat["nb_evaluees"] == 1
    # Entire year in the first class: outside the envelope.
    assert (
        resultat["distributions"][0]["nb_hors_lecture"][
            moteur_distributions.LECTURE_ENVELOPPE
        ]
        > 0
    )
    # THIS TEST EXPECTED NON_ETABLI, and that was correct until 2026-08-10:
    # the reading of the word `Streubereich` was not settled, so no verdict
    # could be rendered. The written clarification from the authority
    # (traceability/sia4010-authority-clarification-2026-08-10.json, decision
    # SIA4010-DISTRIBUTION-BAND) retains the class-by-class min/max envelope.
    # The criterion is therefore established, and a series outside the
    # envelope is a FAIL -- which is precisely what was forbidden to say before.
    assert resultat["verdict"] == moteur_distributions.VERDICT_FAIL
