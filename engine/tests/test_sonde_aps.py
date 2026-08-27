# -*- coding: utf-8 -*-
"""Tests of the PURE parts of `scripts/sonde_aps.py`.

The probe runs inside VE, so most of it cannot be tested here. What can:

* **locating the `.aps`**, which must take the most recent one and not
  traverse an entire project;
* **the series summary**, which must neither copy 8760 points nor raise on an
  exotic value;
* **refusing to run outside VE**, which must be explicit and write nothing.
"""

import io
import json
import os

import pytest

from scripts import sonde_aps as sonde

# --------------------------------------------------------------------------
# Locating the results file
# --------------------------------------------------------------------------


def _fabriquer(dossier, chemin_relatif, horodatage):
    """Creates an empty file and sets its modification time.

    Args:
        dossier: Root directory.
        chemin_relatif: Path under the root.
        horodatage: Modification time to impose.

    Returns:
        str: Absolute path of the created file.
    """
    chemin = os.path.join(str(dossier), *chemin_relatif.split("/"))
    parent = os.path.dirname(chemin)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(chemin, "w", encoding="utf-8") as flux:
        flux.write("")
    os.utime(chemin, (horodatage, horodatage))
    return chemin


def test_le_plus_recent_vient_en_premier(tmp_path):
    """On a project where several cases have run, the last simulation
    is what matters — not the one alphabetical order puts first."""
    _fabriquer(tmp_path, "vista/aaa.aps", 1000)
    recent = _fabriquer(tmp_path, "vista/zzz.aps", 9000)
    assert sonde.trouver_aps(str(tmp_path))[0] == recent


def test_la_recherche_est_recursive(tmp_path):
    """The structure of a VE project is not assumed: we descend."""
    attendu = _fabriquer(tmp_path, "vista/sous/cas.aps", 1000)
    assert attendu in sonde.trouver_aps(str(tmp_path))


def test_la_recherche_ne_descend_pas_indefiniment(tmp_path):
    """A large project would produce an unreadable report."""
    trop_loin = "a/b/c/d/e/perdu.aps"
    _fabriquer(tmp_path, trop_loin, 1000)
    assert sonde.trouver_aps(str(tmp_path)) == []


def test_les_autres_extensions_sont_ignorees(tmp_path):
    _fabriquer(tmp_path, "vista/modele.gbxml", 1000)
    assert sonde.trouver_aps(str(tmp_path)) == []


def test_lextension_est_insensible_a_la_casse(tmp_path):
    attendu = _fabriquer(tmp_path, "CAS.APS", 1000)
    assert sonde.trouver_aps(str(tmp_path)) == [attendu]


@pytest.mark.parametrize("racine", [None, "", "/dossier/qui/nexiste/pas"])
def test_un_dossier_absent_ne_leve_pas(racine):
    """The probe must log the absence, not interrupt on it."""
    assert sonde.trouver_aps(racine) == []


def test_le_nombre_de_fichiers_est_borne(tmp_path):
    for numero in range(sonde.LIMITE_FICHIERS + 15):
        _fabriquer(tmp_path, "vista/cas%03d.aps" % numero, 1000 + numero)
    assert len(sonde.trouver_aps(str(tmp_path))) == sonde.LIMITE_FICHIERS


# --------------------------------------------------------------------------
# Series summary
# --------------------------------------------------------------------------


def test_une_serie_horaire_est_resumee_pas_recopiee():
    """8760 points per variable, across dozens of variables: the report
    would become unreadable and hide what one looks for."""
    resume = sonde._resume_serie([float(i) for i in range(8760)])
    assert resume["nb_points"] == 8760
    assert resume["minimum"] == 0.0
    assert resume["maximum"] == 8759.0
    assert len(resume["premieres_valeurs"]) == 6


def test_la_somme_permet_de_reconnaitre_une_unite_aberrante():
    """A series in W summed over the year gives a number a thousand times
    too large: that is what makes it visible in the report."""
    assert sonde._resume_serie([1000.0] * 8760)["somme"] == 8760000.0


def test_une_serie_vide_est_declaree_vide():
    assert sonde._resume_serie([])["nb_points"] == 0


def test_les_valeurs_non_numeriques_sont_ecartees():
    resume = sonde._resume_serie([1.0, None, "x", 3.0])
    assert resume["nb_points"] == 2
    assert resume["maximum"] == 3.0


def test_un_objet_non_iterable_ne_leve_pas():
    """The API may return something other than a sequence: `repr` informs
    better than an exception that would interrupt the read."""
    assert "non_iterable" in sonde._resume_serie(object())


# --------------------------------------------------------------------------
# Results set overview
# --------------------------------------------------------------------------


def test_lapercu_resume_chaque_variable():
    apercu = sonde._apercu_resultats({"Fan power": [1.0, 2.0]})
    assert apercu["Fan power"]["nb_points"] == 2


def test_une_forme_inattendue_est_rendue_telle_quelle():
    """Better a usable `repr` than an invented summary."""
    assert sonde._apercu_resultats(["a", "b"]) == ["a", "b"]


# --------------------------------------------------------------------------
# Refusal outside VE
# --------------------------------------------------------------------------


def test_hors_ve_la_sonde_nannonce_aucun_releve(monkeypatch):
    monkeypatch.setattr(sonde, "_dans_ve", lambda: False)
    rapport = sonde.sonder()
    assert rapport["dans_ve"] is False
    assert rapport["etapes"] == []


def test_hors_ve_aucun_rapport_nest_ecrit(monkeypatch, tmp_path):
    """An empty file on disk would read as 'the probe ran and found
    nothing', which is false: it could not search for anything."""
    cible = os.path.join(str(tmp_path), "sonde_aps.json")
    monkeypatch.setattr(sonde, "CHEMIN_RAPPORT", cible)
    monkeypatch.setattr(sonde, "_dans_ve", lambda: False)
    sonde.sonder()
    assert not os.path.exists(cible)


def test_main_hors_ve_rend_un_entier(monkeypatch):
    """From the Run button, an exception only shows a traceback."""
    monkeypatch.setattr(sonde, "_dans_ve", lambda: False)
    assert sonde.main(()) == 1


def test_labsence_daps_est_une_erreur_explicite():
    with pytest.raises(RuntimeError, match="ApacheSim"):
        sonde._sans_aps()


# --------------------------------------------------------------------------
# Consistency with what the probe must unblock
# --------------------------------------------------------------------------


def test_les_trois_niveaux_de_ladaptateur_sont_interroges():
    """Querying only one level would leave tests 4 to 6 without a lead: their
    quantities designate air-handling components."""
    from ve_adapter import bandes_adapter as adaptateur

    interroges = set(niveau for niveau, _ in sonde.NIVEAUX)
    assert {
        adaptateur.NIVEAU_LOCAL,
        adaptateur.NIVEAU_SYSTEME,
        adaptateur.NIVEAU_METEO,
    } <= interroges


def test_le_rapport_porte_son_avertissement(monkeypatch):
    monkeypatch.setattr(sonde, "_dans_ve", lambda: False)
    assert "validation" in sonde.sonder()["avertissement"]


def test_le_rapport_va_sous_outputs():
    """Never in refs/: that is not a frozen reference."""
    normalise = sonde.CHEMIN_RAPPORT.replace(os.sep, "/")
    assert "/outputs/" in normalise
    assert "/refs/" not in normalise


def test_le_rapport_est_du_json_valide(monkeypatch, tmp_path):
    """It will be re-read by a script: an unreadable report unblocks nothing."""
    cible = os.path.join(str(tmp_path), "sonde_aps.json")
    monkeypatch.setattr(sonde, "CHEMIN_RAPPORT", cible)
    sonde._ecrire({"dans_ve": True, "etapes": [{"nom": "x", "statut": "OK"}]})
    with io.open(cible, encoding="utf-8") as flux:
        assert json.load(flux)["etapes"][0]["nom"] == "x"


@pytest.mark.parametrize("valeur", [3, 3.0, object(), ["/tmp"], {"p": "/tmp"}])
def test_un_chemin_de_projet_non_textuel_ne_leve_pas(valeur):
    """`VEProject.path` is not guaranteed to be a string, and
    `os.path.isdir(3)` would interpret an integer as a file descriptor
    — silently, with an arbitrary result."""
    assert sonde.trouver_aps(valeur) == []


# --------------------------------------------------------------------------
# Read coverage, without VE
# --------------------------------------------------------------------------


class FauxLecteur(object):
    """Stand-in for `ResultsReader` that records how it is called.

    Attributes:
        appels: List of `(method, arguments)`, in order.
    """

    results_per_day = 24
    first_day = 1
    last_day = 365
    year = 2026
    weather_file = "DRYCOLD.fwt"
    hvac_file = ""

    def __init__(self):
        self.appels = []
        self.variables = []

    def get_variables(self):
        self.appels.append(("get_variables", ()))
        return list(self.variables)

    #: What ZOER_C1.aps actually returned on 2026-08-06. `get_process_
    #: variables` requires one of these names: without an argument it raises ArgumentError.
    PROCESSUS = [
        "Process Material flow",
        "Process Product flow",
        "Process Heat input",
        "Process Heat output",
    ]

    def __getattr__(self, nom):
        def methode(*arguments):
            self.appels.append((nom, arguments))
            if nom == "get_apache_systems":
                return ["SYS1"]
            if nom == "get_process_list":
                return list(self.PROCESSUS)
            return []

        return methode


def _relever_a_blanc():
    """Runs `_relever` against a stand-in and returns the observed calls.

    Returns:
        tuple: `(appels, etapes)`.
    """
    lecteur = FauxLecteur()
    etapes = []

    def etape(nom, fonction):
        try:
            etapes.append((nom, "OK", fonction()))
        except Exception as erreur:  # noqa: BLE001
            etapes.append((nom, "ECHEC", erreur))
        return etapes[-1][2] if etapes[-1][1] == "OK" else None

    sonde._relever(etape, lecteur)
    return lecteur.appels, etapes


def test_la_forme_sans_argument_est_celle_qui_repond():
    """Slice by VE on 2026-08-06 on ZOER_C1.aps: `get_variables()` returns
    the list, `get_variables('z')` raises ArgumentError. The stand-in refuses
    the argument as VE does."""
    appels, _ = _relever_a_blanc()
    formes = [args for methode, args in appels if methode == "get_variables"]
    assert formes == [()]


def test_les_formes_a_argument_restent_tentees():
    """If another version of VE accepted them, the report would say so —
    rather than leaving the opposite impression based on a single file."""
    _, etapes = _relever_a_blanc()
    tentees = [nom for nom, _, _ in etapes if nom.startswith("get_variables(")]
    for niveau in ("z", "v", "w"):
        assert any(repr(niveau) in nom for nom in tentees), niveau


def test_un_echec_sur_les_formes_a_argument_ne_perd_pas_la_liste():
    """That is the real case: three steps failing, yet the complete read
    must be in the report."""
    lecteur = FauxLecteur()
    lecteur.variables = [{"aps_varname": "A", "model_level": "z"}]
    rapport = {}

    def etape(nom, fonction):
        try:
            return fonction()
        except Exception:  # noqa: BLE001
            return None

    sonde._relever(etape, lecteur, rapport)
    assert rapport["variables"] == [{"aps_varname": "A", "model_level": "z"}]


def test_les_portes_dentree_systeme_et_energie_sont_interrogees():
    """That is what the pre-existing probe does not query, and that is where
    Lufterwarmer, Luftkuhler, WRG and Ventilatoren live."""
    appels, _ = _relever_a_blanc()
    methodes = set(methode for methode, _ in appels)
    for attendue in (
        "get_apache_systems",
        "get_energy_uses",
        "get_energy_meters",
        "get_energy_sources",
        "get_units",
        "get_process_variables",
    ):
        assert attendue in methodes, attendue


def test_le_cadre_temporel_est_releve():
    """Without a time step or a year, an annual sum has no meaning."""
    _, etapes = _relever_a_blanc()
    noms = set(nom for nom, _, _ in etapes)
    assert "results_per_day" in noms and "weather_file" in noms


class LecteurAmpute(FauxLecteur):
    """Stand-in with one entry point unavailable.

    `__getattr__` must be defined on the CLASS: set on an instance, it
    is never consulted, and the test would pass vacuously.
    """

    def __getattr__(self, nom):
        if nom == "get_energy_uses":

            def indisponible(*_):
                raise RuntimeError("methode absente de cette version")

            return indisponible
        return FauxLecteur.__getattr__(self, nom)


def test_une_methode_qui_leve_ninterrompt_pas_le_releve():
    """A missing entry point is information; losing the subsequent ones
    would be a net loss."""
    lecteur = LecteurAmpute()
    etapes = []

    def etape(nom, fonction):
        try:
            fonction()
            etapes.append((nom, "OK"))
        except Exception:  # noqa: BLE001
            etapes.append((nom, "ECHEC"))
        return None

    sonde._relever(etape, lecteur)
    statuts = dict(etapes)
    # The stand-in must have genuinely failed, otherwise the test proves nothing.
    assert statuts["get_energy_uses"] == "ECHEC"
    # And the read must have continued beyond it.
    assert statuts["get_units"] == "OK"
    assert statuts["get_process_list"] == "OK"


def test_get_process_variables_est_appele_avec_un_processus():
    """Without an argument it raises ArgumentError. The list of processes comes
    from `get_process_list`, observed on ZOER_C1.aps on 2026-08-06."""
    appels, _ = _relever_a_blanc()
    passes = [args for methode, args in appels if methode == "get_process_variables"]
    assert passes, "get_process_variables jamais appele"
    assert all(len(args) == 1 for args in passes)
    assert ("Process Heat input",) in passes


def test_la_liste_complete_des_variables_echappe_au_plafond():
    """The 2026-08-06 read was truncated to 500 entries by the step ceiling,
    and NO level-'z' variable survived: a readability safeguard had cut
    exactly what the probe exists to report."""
    lecteur = FauxLecteur()
    nombreuses = [
        {
            "aps_varname": "V%04d" % i,
            "display_name": "v",
            "model_level": "z" if i % 2 else "e",
        }
        for i in range(sonde.LIMITE_ELEMENTS_ETAPE + 250)
    ]
    lecteur.variables = nombreuses
    rapport = {}

    def etape(nom, fonction):
        try:
            return fonction()
        except Exception:  # noqa: BLE001
            return None

    sonde._relever(etape, lecteur, rapport)
    assert len(rapport["variables"]) == len(nombreuses)
    assert rapport["variables_par_niveau"]["z"] > 0
    assert rapport["variables_par_niveau"]["e"] > 0


def test_une_variable_est_reduite_a_ce_qui_sert():
    reduite = sonde._variable_lisible(
        {
            "aps_varname": "Window solar gains",
            "display_name": "Solar gain",
            "model_level": "z",
            "units_type": "Power",
            "inutile": 1,
        }
    )
    assert reduite["aps_varname"] == "Window solar gains"
    assert "inutile" not in reduite


def test_une_variable_de_forme_inattendue_est_signalee_pas_perdue():
    assert "forme_inattendue" in sonde._variable_lisible("juste une chaine")


def test_les_comptes_par_niveau_sont_lisibles_en_console():
    comptes = sonde._compter_par_niveau(
        [{"model_level": "z"}, {"model_level": "z"}, {"model_level": "e"}]
    )
    assert comptes == {"e": 1, "z": 2}
    assert sonde._en_clair(comptes) == "e=1, z=2"
