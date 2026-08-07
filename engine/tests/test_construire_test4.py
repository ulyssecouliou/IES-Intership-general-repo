# -*- coding: utf-8 -*-
u"""Tests des parties PURES de `scripts/construire_test4_dans_ve.py`.

Ce script construit dans VE, donc l'essentiel n'est pas testable ici. Le sont
les trois choses qui pourraient tromper :

* les **paramètres** doivent tous venir de la spécification, et le dire ;
* la **construction** doit refuser, et pour la bonne raison — depuis le
  2026-08-07 ce n'est plus « signatures inconnues » mais « ApacheSystems
  modélise des rendements, pas des composants » ;
* le script ne doit jamais se présenter comme produisant un cas de validation.
"""

import os

import pytest

from scripts import construire_test4_dans_ve as construction


# --------------------------------------------------------------------------
# Le refus de construire sans savoir
# --------------------------------------------------------------------------

def test_construire_refuse_parce_quapachesystems_ne_convient_pas():
    """LE test central, et sa raison a CHANGE le 2026-08-07.

    Les signatures sont desormais connues. Ce qui bloque n est plus
    l ignorance : c est qu ApacheSystems modelise des RENDEMENTS saisonniers,
    pas des composants. Construire quand meme produirait un systeme qui
    simule, qui donne des nombres, et qui ne represente pas le test."""
    with pytest.raises(construction.ConstructionRefusee,
                       match='ne peut pas représenter'):
        construction.construire()


def test_le_refus_nomme_ce_qui_est_inexprimable():
    """Un refus sans issue n aide personne : il doit dire quoi faire."""
    with pytest.raises(construction.ConstructionRefusee) as capture:
        construction.construire()
    message = u'%s' % capture.value
    assert 'ApacheHVAC' in message
    assert 'load_network' in message
    for exigence in construction.INEXPRIMABLE_EN_APACHESYSTEMS:
        assert exigence in message, exigence


def test_les_cles_des_setters_viennent_du_releve():
    """Relevees dans les docstrings d une VE reelle, pas supposees."""
    assert 'SFP' in construction.CLES_DES_SETTERS['set_auxiliary_energy']
    assert 'SEER' in construction.CLES_DES_SETTERS['set_cooling']
    assert 'SCoP' in construction.CLES_DES_SETTERS['set_heating']
    assert 'heat_recovery_efficiency' in construction.CLES_DES_SETTERS[
        'set_ventilation_ncm']


def test_aucune_cle_nexprime_une_puissance_de_batterie():
    """`gen_size` dimensionne le GENERATEUR, pas la batterie de traitement
    d air. La confusion ferait construire un systeme plausible et faux."""
    toutes = set()
    for cles in construction.CLES_DES_SETTERS.values():
        toutes.update(cles)
    for interdit in ('coil_size', 'coil_capacity', 'heating_coil',
                     'cooling_coil', 'bypass', 'frost', 'supply_setpoint'):
        assert interdit not in toutes, interdit


def test_chaque_exigence_inexprimable_est_justifiee():
    for exigence, motif in construction.INEXPRIMABLE_EN_APACHESYSTEMS.items():
        assert len(motif) > 40, exigence


# --------------------------------------------------------------------------
# Les paramètres viennent tous de la spécification
# --------------------------------------------------------------------------

def test_chaque_parametre_cite_sa_source():
    """Règle 3 : chaque valeur cite son origine. Un paramètre sans source
    finit par être pris pour un choix d'implémentation."""
    for cle, entree in construction.PARAMETRES.items():
        assert entree['source'], cle
        assert 'Spezifikation_Test4.pdf' in entree['source'], cle


def test_aucun_parametre_nest_vide():
    for cle, entree in construction.PARAMETRES.items():
        assert entree['valeur'] is not None, cle


@pytest.mark.parametrize('cle,attendu', [
    ('debit_nominal_m3_h', 1700.0),
    ('puissance_ventilateur_soufflage_w', 407.0),
    ('puissance_ventilateur_reprise_w', 331.0),
    ('recuperateur_taux', 0.75),
    ('batterie_froide_kw', 12.8),
    ('batterie_chaude_kw', 11.4),
    ('surface_nette_m2', 165.8),
    ('occupants', 55),
])
def test_les_valeurs_sont_celles_de_la_spec(cle, attendu):
    """Recopiées telles quelles : ni arrondies, ni converties, ni complétées."""
    assert construction.PARAMETRES[cle]['valeur'] == attendu


def test_le_recuperateur_est_sans_echange_dhumidite():
    """Détail décisif : un échangeur à plaques SANS échange d'humidité ne
    produit aucune récupération latente. Le confondre avec un roue
    enthalpique changerait le résultat de « Wärmezufuhr WRG latent »."""
    assert 'SANS' in construction.PARAMETRES['recuperateur_type']['valeur']


# --------------------------------------------------------------------------
# Ce modèle n'est pas un cas de validation
# --------------------------------------------------------------------------

def test_les_entrees_manquantes_sont_nommees():
    """Les taire laisserait croire qu'un résultat issu de ce modèle vaut
    quelque chose au sens SIA."""
    assert set(construction.MANQUANTS) == {'climat', 'constructions', 'usage'}
    for motif in construction.MANQUANTS.values():
        assert motif


def test_le_climat_manquant_est_celui_de_la_norme():
    assert 'SIA 2028' in construction.MANQUANTS['climat']
    assert 'Kloten' in construction.MANQUANTS['climat']


def test_le_module_annonce_quil_ne_valide_pas():
    doc = construction.__doc__
    assert 'PAS VALIDER' in doc or 'ne doit être présenté' in doc


def test_le_rapport_va_sous_outputs():
    """Jamais dans refs/ : ce n'est pas un référentiel figé."""
    normalise = construction.CHEMIN_RAPPORT.replace(os.sep, '/')
    assert '/outputs/' in normalise
    assert '/refs/' not in normalise


# --------------------------------------------------------------------------
# Reconnaissance hors VE
# --------------------------------------------------------------------------

def test_hors_ve_rien_nest_releve(monkeypatch):
    monkeypatch.setattr(construction, '_dans_ve', lambda: False)
    rapport = construction.reconnaitre()
    assert rapport['dans_ve'] is False
    assert rapport['etapes'] == []


def test_le_rapport_porte_les_parametres_et_les_manques(monkeypatch):
    """Le relevé doit être lisible seul : les signatures d'un côté, ce qu'on
    veut leur appliquer de l'autre."""
    monkeypatch.setattr(construction, '_dans_ve', lambda: False)
    rapport = construction.reconnaitre()
    assert set(rapport['parametres_de_la_spec']) == set(construction.PARAMETRES)
    assert rapport['manquants_pour_une_validation'] == construction.MANQUANTS
    assert 'validation' in rapport['avertissement']


def test_main_hors_ve_rend_un_entier(monkeypatch):
    monkeypatch.setattr(construction, '_dans_ve', lambda: False)
    assert construction.main(()) == 1


def test_main_avec_construire_refuse_proprement(monkeypatch):
    """Depuis le bouton Run, une exception n'affiche qu'une trace."""
    monkeypatch.setattr(construction, '_dans_ve', lambda: False)
    assert construction.main(('--construire',)) == 1


# --------------------------------------------------------------------------
# Les setters relevés couvrent ce qu'on veut configurer
# --------------------------------------------------------------------------

def test_les_setters_releves_existent_dans_lapi():
    """Écrit contre la surface introspectée, pas contre la documentation."""
    import io
    import json
    chemin = os.path.join(
        os.path.dirname(os.path.abspath(construction.__file__)),
        os.pardir, 've_adapter', 've_api_surface.json')
    with io.open(os.path.abspath(chemin), encoding='utf-8') as flux:
        surface = json.load(flux)
    membres = set(surface['symbols']['VEApacheSystem']['members'])
    for nom in construction.SETTERS_A_RELEVER:
        assert nom in membres, nom
    for nom in construction.PROPRIETES_A_RELEVER:
        assert nom in membres, nom


def test_le_reseau_apachehvac_nest_pas_scriptable():
    """Constat mesuré sur la surface d'API : HVACNetwork n'expose aucune
    methode de creation. Si une version future en ajoutait une, ce test doit
    echouer pour qu'on en profite."""
    import io
    import json
    chemin = os.path.join(
        os.path.dirname(os.path.abspath(construction.__file__)),
        os.pardir, 've_adapter', 've_api_surface.json')
    with io.open(os.path.abspath(chemin), encoding='utf-8') as flux:
        surface = json.load(flux)
    membres = surface['symbols']['HVACNetwork']['members']
    assert not [m for m in membres
                if m.startswith(('create_', 'add_', 'new_', 'remove_'))]
    # Ce qui EXISTE, et qui ouvre la voie du .asp construit a la main.
    assert 'load_network' in membres
    assert 'path' in membres
