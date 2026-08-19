# -*- coding: utf-8 -*-
u"""Tests of the geometry import (`scripts/importer_geometrie_test1.py`).

This script is the only one in the repository that deliberately MODIFIES the
VE model. Two things must therefore hold:

* it must not trigger by accident — hence a separate launcher from the
  probe, and a warning in its report;
* the **surface confrontation** must bite. An import that does not raise proves
  nothing: the 1 mm layer thicknesses were created without any error and yielded
  an R forty-seven times too low.
"""

import io
import os

import pytest

from scripts import importer_geometrie_test1 as importateur
from ve_adapter import geometrie_test1 as geometrie


@pytest.fixture(scope='module')
def cotes():
    try:
        return geometrie.charger_cotes()
    except geometrie.GeometrieIndisponible:
        pytest.skip(u'cotes de référence absentes')


# --------------------------------------------------------------------------
# The expected totals, aggregated as VE returns them
# --------------------------------------------------------------------------

def test_les_murs_sont_agreges_comme_get_areas_les_rend(cotes):
    """`get_areas()` does not give one entry per face: it aggregates. Comparing
    face by face would compare what VE does not separate."""
    attendus = importateur.totaux_attendus(cotes)
    assert attendus['murs_exterieurs'] == pytest.approx(9.6 + 21.6 + 16.2 * 2)


def test_le_vitrage_est_compte_a_part_des_murs(cotes):
    """Confusing it with the opaque would double the wall."""
    attendus = importateur.totaux_attendus(cotes)
    assert attendus['vitrage_exterieur'] == pytest.approx(12.0)
    assert attendus['murs_exterieurs'] == pytest.approx(63.6)


def test_plancher_et_toiture_valent_la_surface_au_sol(cotes):
    attendus = importateur.totaux_attendus(cotes)
    assert attendus['plancher'] == pytest.approx(48.0)
    assert attendus['toiture'] == pytest.approx(48.0)


# --------------------------------------------------------------------------
# The confrontation — the only step that proves something
# --------------------------------------------------------------------------

def test_des_surfaces_identiques_concordent():
    attendus = {'plancher': 48.0}
    verdicts = importateur.comparer(attendus, {'plancher': 48.0})
    assert verdicts['plancher']['statut'] == 'CONCORDE'


def test_un_ecart_de_surface_est_declare_divergent():
    verdicts = importateur.comparer({'plancher': 48.0}, {'plancher': 47.0})
    assert verdicts['plancher']['statut'] == 'DIVERGE'
    assert 'cellule fausse' in verdicts['plancher']['note']


def test_le_flottant_32_bits_est_tolere():
    """VE stores in float32: an exact equality would fail on a correct import."""
    verdicts = importateur.comparer({'plancher': 48.0},
                                    {'plancher': 48.00000023841858})
    assert verdicts['plancher']['statut'] == 'CONCORDE'


def test_un_poste_absent_nest_jamais_lu_comme_zero():
    """This is the central rule of the repository: an absence is not a measurement."""
    verdicts = importateur.comparer({'toiture': 48.0}, {'toiture': None})
    assert verdicts['toiture']['statut'] == 'NON_RELEVE'
    assert verdicts['toiture']['releve_m2'] is None
    assert 'zero' in verdicts['toiture']['note']


def test_le_verdict_est_rendu_poste_par_poste():
    """A global boolean would hide WHICH item diverges."""
    verdicts = importateur.comparer(
        {'plancher': 48.0, 'toiture': 48.0},
        {'plancher': 48.0, 'toiture': 12.0})
    assert verdicts['plancher']['statut'] == 'CONCORDE'
    assert verdicts['toiture']['statut'] == 'DIVERGE'


def test_lecart_signe_est_conserve():
    """Too large and too small are not corrected the same way."""
    verdicts = importateur.comparer({'plancher': 48.0}, {'plancher': 50.0})
    assert verdicts['plancher']['ecart_m2'] > 0


# --------------------------------------------------------------------------
# Cumulation of read-back surfaces
# --------------------------------------------------------------------------

class CorpsFactice(object):
    """Stand-in for `VEBody`, returning the real keys of `get_areas()`."""

    def __init__(self, aires):
        self._aires = aires

    def get_areas(self):
        return dict(self._aires)


def test_les_surfaces_sont_cumulees_sur_tous_les_corps():
    corps = [CorpsFactice({'ext_wall_area': 30.0}),
             CorpsFactice({'ext_wall_area': 33.6})]
    assert importateur.totaux_releves(corps)['murs_exterieurs'] == \
        pytest.approx(63.6)


def test_un_plancher_interieur_et_exterieur_sont_additionnes():
    """VE distinguishes `ext_floor_area` and `int_floor_area`; the cell has
    only one floor, but the aggregation must hold in both cases."""
    corps = [CorpsFactice({'ext_floor_area': 48.0, 'int_floor_area': 0.0})]
    assert importateur.totaux_releves(corps)['plancher'] == pytest.approx(48.0)


def test_un_corps_muet_ne_fait_pas_planter_le_cumul():
    class Muet(object):
        def get_areas(self):
            raise RuntimeError('indisponible')

    releve = importateur.totaux_releves([Muet(),
                                         CorpsFactice({'ext_wall_area': 1.0})])
    assert releve['murs_exterieurs'] == pytest.approx(1.0)


def test_sans_aucun_corps_tous_les_postes_restent_nuls_pas_zero():
    releve = importateur.totaux_releves([])
    for poste in importateur.CLES_DE_SURFACE:
        assert releve[poste] is None, poste


# --------------------------------------------------------------------------
# Call shapes for import_file
# --------------------------------------------------------------------------

def test_la_premiere_forme_qui_repond_est_retenue():
    """The signature is not introspectable: its docstring reduces to
    'cap_height'. We try, and record what works."""
    class Importeur(object):
        @staticmethod
        def import_file(chemin, *arguments):
            if len(arguments) != 0:
                raise TypeError('trop d arguments')
            return True

    resultat = importateur._essayer_import(Importeur, 'x.xml')
    assert resultat['forme_retenue'] == u'file_name seul'


def test_les_echecs_sont_tous_consignes():
    """Error messages name what the API expects: losing them
    would require redoing the trial."""
    class Importeur(object):
        @staticmethod
        def import_file(chemin, *arguments):
            raise TypeError('signature refusee')

    resultat = importateur._essayer_import(Importeur, 'x.xml')
    assert resultat['forme_retenue'] is None
    assert len(resultat['essais']) == len(importateur.FORMES_DAPPEL)
    assert all(e['statut'] == 'ECHEC' for e in resultat['essais'])


def test_les_formes_vont_du_plus_simple_au_plus_complet():
    """Trying the complete form first would risk passing with
    unwanted default values."""
    longueurs = [len(arguments) for _, arguments in importateur.FORMES_DAPPEL]
    assert longueurs == sorted(longueurs)
    assert longueurs[0] == 0


# --------------------------------------------------------------------------
# Safeguards
# --------------------------------------------------------------------------

def test_le_rapport_avertit_que_le_modele_est_modifie():
    """This is the only script in the repository that deliberately mutates the model."""
    rapport = importateur.importer()
    assert 'MODIFIE' in rapport['avertissement']
    assert 'JETABLE' in rapport['avertissement']


def test_hors_ve_le_gbxml_est_ecrit_mais_rien_nest_importe(monkeypatch):
    monkeypatch.setattr(importateur, '_dans_ve', lambda: False)
    rapport = importateur.importer()
    noms = [e['nom'] for e in rapport['etapes']]
    assert u'ecriture du gbXML' in noms
    assert not any('import_file' in nom for nom in noms)


def test_le_rapport_va_sous_outputs():
    normalise = importateur.CHEMIN_RAPPORT.replace(os.sep, '/')
    assert '/outputs/' in normalise
    assert '/refs/' not in normalise


def test_le_gbxml_est_ecrit_sous_outputs():
    normalise = importateur.CHEMIN_GBXML.replace(os.sep, '/')
    assert '/outputs/' in normalise


def test_main_hors_ve_rend_un_entier(monkeypatch):
    monkeypatch.setattr(importateur, '_dans_ve', lambda: False)
    assert importateur.main(()) == 0


def test_le_lanceur_avertit_avant_de_muter():
    chemin = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(importateur.__file__))),
        'Run_VE_SIA4010_Importer_Geometrie_Test1.py')
    if not os.path.exists(chemin):
        pytest.skip(u'lanceur absent')
    with io.open(chemin, encoding='utf-8') as flux:
        source = flux.read()
    # The launcher was moved to English; the preserved property is the same:
    # it must WARN before mutating, and name the throwaway project.
    assert 'MODIFIES the VE model' in source
    assert 'THROWAWAY' in source
