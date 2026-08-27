# -*- coding: utf-8 -*-
"""Tests of the PURE parts of `scripts/construire_test4_dans_ve.py`.

This script builds in VE, so most of it is not testable here. What is:

* the **parameters** must all come from the specification, and say so;
* the **construction** must refuse, and for the right reason — since
  2026-08-07 it is no longer 'unknown signatures' but 'ApacheSystems
  models efficiencies, not components';
* the script must never present itself as producing a validation case.
"""

import os

import pytest

from scripts import construire_test4_dans_ve as construction

# --------------------------------------------------------------------------
# The refusal to build without knowing
# --------------------------------------------------------------------------


def test_construire_refuse_parce_quapachesystems_ne_convient_pas():
    """THE central test, and its reason CHANGED on 2026-08-07.

    Signatures are now known. What blocks is no longer
    ignorance: it is that ApacheSystems models seasonal EFFICIENCIES,
    not components. Building anyway would produce a system that
    simulates, gives numbers, and does not represent the test."""
    with pytest.raises(construction.ConstructionRefusee, match="ne peut pas représenter"):
        construction.construire()


def test_le_refus_nomme_ce_qui_est_inexprimable():
    """A refusal without a way forward helps no one: it must say what to do."""
    with pytest.raises(construction.ConstructionRefusee) as capture:
        construction.construire()
    message = "%s" % capture.value
    assert "ApacheHVAC" in message
    assert "load_network" in message
    for exigence in construction.INEXPRIMABLE_EN_APACHESYSTEMS:
        assert exigence in message, exigence


def test_les_cles_des_setters_viennent_du_releve():
    """Recorded in the docstrings of a real VE, not assumed."""
    assert "SFP" in construction.CLES_DES_SETTERS["set_auxiliary_energy"]
    assert "SEER" in construction.CLES_DES_SETTERS["set_cooling"]
    assert "SCoP" in construction.CLES_DES_SETTERS["set_heating"]
    assert (
        "heat_recovery_efficiency" in construction.CLES_DES_SETTERS["set_ventilation_ncm"]
    )


def test_aucune_cle_nexprime_une_puissance_de_batterie():
    """`gen_size` sizes the GENERATOR, not the air-handling battery.
    The confusion would build a plausible and wrong system."""
    toutes = set()
    for cles in construction.CLES_DES_SETTERS.values():
        toutes.update(cles)
    for interdit in (
        "coil_size",
        "coil_capacity",
        "heating_coil",
        "cooling_coil",
        "bypass",
        "frost",
        "supply_setpoint",
    ):
        assert interdit not in toutes, interdit


def test_chaque_exigence_inexprimable_est_justifiee():
    for exigence, motif in construction.INEXPRIMABLE_EN_APACHESYSTEMS.items():
        assert len(motif) > 40, exigence


# --------------------------------------------------------------------------
# Parameters all come from the specification
# --------------------------------------------------------------------------


def test_chaque_parametre_cite_sa_source():
    """Rule 3: each value cites its origin. A parameter without a source
    ends up being taken for an implementation choice."""
    for cle, entree in construction.PARAMETRES.items():
        assert entree["source"], cle
        assert "Spezifikation_Test4.pdf" in entree["source"], cle


def test_aucun_parametre_nest_vide():
    for cle, entree in construction.PARAMETRES.items():
        assert entree["valeur"] is not None, cle


@pytest.mark.parametrize(
    "cle,attendu",
    [
        ("debit_nominal_m3_h", 1700.0),
        ("puissance_ventilateur_soufflage_w", 407.0),
        ("puissance_ventilateur_reprise_w", 331.0),
        ("recuperateur_taux", 0.75),
        ("batterie_froide_kw", 12.8),
        ("batterie_chaude_kw", 11.4),
        ("surface_nette_m2", 165.8),
        ("occupants", 55),
    ],
)
def test_les_valeurs_sont_celles_de_la_spec(cle, attendu):
    """Copied as-is: neither rounded, nor converted, nor filled in."""
    assert construction.PARAMETRES[cle]["valeur"] == attendu


def test_le_recuperateur_est_sans_echange_dhumidite():
    """Decisive detail: a plate exchanger WITHOUT moisture exchange does
    not produce any latent recovery. Confusing it with an enthalpy wheel
    would change the result of 'Wärmezufuhr WRG latent'."""
    assert "SANS" in construction.PARAMETRES["recuperateur_type"]["valeur"]


# --------------------------------------------------------------------------
# This model is not a validation case
# --------------------------------------------------------------------------


def test_les_entrees_manquantes_sont_nommees():
    """Silencing them would make one believe that a result from this model means
    something in the SIA sense."""
    assert set(construction.MANQUANTS) == {"climat", "constructions", "usage"}
    for motif in construction.MANQUANTS.values():
        assert motif


def test_le_climat_manquant_est_celui_de_la_norme():
    assert "SIA 2028" in construction.MANQUANTS["climat"]
    assert "Kloten" in construction.MANQUANTS["climat"]


def test_le_module_annonce_quil_ne_valide_pas():
    doc = construction.__doc__
    assert "NOT VALIDATING" in doc or "must be presented as a SIA candidate" in doc


def test_le_rapport_va_sous_outputs():
    """Never in refs/: it is not a frozen reference."""
    normalise = construction.CHEMIN_RAPPORT.replace(os.sep, "/")
    assert "/outputs/" in normalise
    assert "/refs/" not in normalise


# --------------------------------------------------------------------------
# Recognition outside VE
# --------------------------------------------------------------------------


def test_hors_ve_rien_nest_releve(monkeypatch):
    monkeypatch.setattr(construction, "_dans_ve", lambda: False)
    rapport = construction.reconnaitre()
    assert rapport["dans_ve"] is False
    assert rapport["etapes"] == []


def test_le_rapport_porte_les_parametres_et_les_manques(monkeypatch):
    """The survey must be readable on its own: signatures on one side, what we
    want to apply to them on the other."""
    monkeypatch.setattr(construction, "_dans_ve", lambda: False)
    rapport = construction.reconnaitre()
    assert set(rapport["parametres_de_la_spec"]) == set(construction.PARAMETRES)
    assert rapport["manquants_pour_une_validation"] == construction.MANQUANTS
    assert "validation" in rapport["avertissement"]


def test_main_hors_ve_rend_un_entier(monkeypatch):
    monkeypatch.setattr(construction, "_dans_ve", lambda: False)
    assert construction.main(()) == 1


def test_main_avec_construire_refuse_proprement(monkeypatch):
    """Since the Run button, an exception only displays a trace."""
    monkeypatch.setattr(construction, "_dans_ve", lambda: False)
    assert construction.main(("--construire",)) == 1


# --------------------------------------------------------------------------
# The surveyed setters cover what we want to configure
# --------------------------------------------------------------------------


def test_les_setters_releves_existent_dans_lapi():
    """Written against the introspected surface, not against the documentation."""
    import io
    import json

    chemin = os.path.join(
        os.path.dirname(os.path.abspath(construction.__file__)),
        os.pardir,
        "ve_adapter",
        "ve_api_surface.json",
    )
    with io.open(os.path.abspath(chemin), encoding="utf-8") as flux:
        surface = json.load(flux)
    membres = set(surface["symbols"]["VEApacheSystem"]["members"])
    for nom in construction.SETTERS_A_RELEVER:
        assert nom in membres, nom
    for nom in construction.PROPRIETES_A_RELEVER:
        assert nom in membres, nom


def test_le_reseau_apachehvac_nest_pas_scriptable():
    """Measured finding on the API surface: HVACNetwork exposes no
    creation method. If a future version added one, this test must
    fail so we can take advantage."""
    import io
    import json

    chemin = os.path.join(
        os.path.dirname(os.path.abspath(construction.__file__)),
        os.pardir,
        "ve_adapter",
        "ve_api_surface.json",
    )
    with io.open(os.path.abspath(chemin), encoding="utf-8") as flux:
        surface = json.load(flux)
    membres = surface["symbols"]["HVACNetwork"]["members"]
    assert not [
        m for m in membres if m.startswith(("create_", "add_", "new_", "remove_"))
    ]
    # What EXISTS, and which opens the path to the manually built .asp.
    assert "load_network" in membres
    assert "path" in membres
