# -*- coding: utf-8 -*-
u"""Tests de la géométrie de la cellule d'essai (`ve_adapter/geometrie_test1.py`).

Le danger visé est celui qui a coûté le plus cher cette semaine : une cote mal
lue produirait une cellule **plausible et fausse**, que la simulation ne
signalerait pas. C'est ce qui s'est passé avec les épaisseurs de couche à 1 mm,
sous une sonde verte.

Les surfaces sont donc RECALCULÉES depuis les cotes et confrontées à celles que
la source annonce — deux chemins, une seule vérité.
"""

import pytest

from ve_adapter import geometrie_test1 as geometrie


@pytest.fixture(scope='module')
def cotes():
    try:
        return geometrie.charger_cotes()
    except geometrie.GeometrieIndisponible:
        pytest.skip(u'cotes de référence absentes')


# --------------------------------------------------------------------------
# Les cotes se tiennent
# --------------------------------------------------------------------------

def test_les_surfaces_recalculees_reproduisent_la_source(cotes):
    """LE contrôle. Si une cote était mal lue, ce recalcul ne tomberait pas
    sur les surfaces annoncées."""
    releve = geometrie.controler_les_cotes(cotes)
    for face, (calculee, annoncee) in releve.items():
        assert abs(calculee - annoncee) < 1e-9, face


def test_la_facade_avant_deduit_le_vitrage(cotes):
    """8 x 2,7 = 21,6 moins 12 m² de vitrage = 9,6. Oublier la déduction
    donnerait une paroi opaque deux fois trop grande."""
    surfaces = geometrie.surfaces_attendues(cotes)
    assert surfaces['front_wall'] == pytest.approx(9.6)
    assert surfaces['back_wall'] == pytest.approx(21.6)
    assert surfaces['back_wall'] - surfaces['front_wall'] == pytest.approx(12.0)


def test_le_volume_est_coherent(cotes):
    assert cotes['volume_m3'] == pytest.approx(
        cotes['width_m'] * cotes['depth_m'] * cotes['height_m'])


def test_une_cote_falsifiee_est_detectee(cotes):
    """Le contrôle doit mordre, pas seulement exister."""
    faussees = dict(cotes)
    faussees['width_m'] = 9.0
    with pytest.raises(geometrie.GeometrieIncoherente, match='ne se tiennent'):
        geometrie.controler_les_cotes(faussees)


def test_un_volume_falsifie_est_detecte(cotes):
    faussees = dict(cotes)
    faussees['volume_m3'] = 130.0
    with pytest.raises(geometrie.GeometrieIncoherente, match='volume'):
        geometrie.controler_les_cotes(faussees)


# --------------------------------------------------------------------------
# Implantation des fenêtres
# --------------------------------------------------------------------------

def test_les_fenetres_remplissent_exactement_la_facade(cotes):
    """0,5 + 3 + 1 + 3 + 0,5 = 8,0 m. Si la somme ne tombait pas juste, les
    marges ou l'intervalle auraient été mal lus."""
    fenetres = geometrie.rectangles_des_fenetres(cotes)
    assert len(fenetres) == 2
    assert fenetres[0]['x_min'] == pytest.approx(0.5)
    assert fenetres[-1]['x_max'] == pytest.approx(cotes['width_m'] - 0.5)


def test_les_fenetres_sont_separees_par_lintervalle_annonce(cotes):
    fenetres = geometrie.rectangles_des_fenetres(cotes)
    ecart = fenetres[1]['x_min'] - fenetres[0]['x_max']
    assert ecart == pytest.approx(cotes['windows']['gap_m'])


def test_lallege_est_respectee(cotes):
    fenetre = geometrie.rectangles_des_fenetres(cotes)[0]
    assert fenetre['z_min'] == pytest.approx(cotes['windows']['sill_m'])
    assert fenetre['z_max'] - fenetre['z_min'] == pytest.approx(
        cotes['windows']['height_m'])


def test_les_surfaces_vitrees_totalisent_celle_de_la_source(cotes):
    total = sum(f['surface_m2']
                for f in geometrie.rectangles_des_fenetres(cotes))
    assert total == pytest.approx(cotes['windows']['total_area_m2'])


def test_une_implantation_impossible_est_refusee(cotes):
    """Marges trop larges : les fenêtres déborderaient du mur."""
    faussees = dict(cotes)
    faussees['windows'] = dict(cotes['windows'])
    faussees['windows']['side_margin_m'] = 2.0
    with pytest.raises(geometrie.GeometrieIncoherente, match='implantation'):
        geometrie.rectangles_des_fenetres(faussees)


# --------------------------------------------------------------------------
# Repère et orientation
# --------------------------------------------------------------------------

def test_la_facade_avant_est_au_sud(cotes):
    """L'orientation décide de tout le solaire : la spécification impose une
    façade sud, donc en Y = 0 dans ce repère."""
    sommets = geometrie.sommets_de_la_cellule(cotes)
    for nom, (_, y, _) in sommets.items():
        if nom.startswith('sud'):
            assert y == 0.0, nom
        else:
            assert y == cotes['depth_m'], nom


def test_les_huit_sommets_sont_produits(cotes):
    assert len(geometrie.sommets_de_la_cellule(cotes)) == 8


def test_la_hauteur_separe_le_bas_du_haut(cotes):
    sommets = geometrie.sommets_de_la_cellule(cotes)
    for nom, (_, _, z) in sommets.items():
        assert z == (cotes['height_m'] if nom.endswith('haut') else 0.0), nom


# --------------------------------------------------------------------------
# Provenance et pureté
# --------------------------------------------------------------------------

def test_aucune_cote_nest_ecrite_dans_le_module():
    """Toutes viennent de la source. Une cote saisie ici serait invérifiable,
    et se périmerait sans bruit."""
    import io
    import os
    chemin = os.path.abspath(geometrie.__file__).replace('.pyc', '.py')
    with io.open(chemin, encoding='utf-8') as flux:
        for numero, ligne in enumerate(flux, 1):
            code = ligne.split('#')[0]
            for cote in ('8.0', '6.0', '2.7', '48.0', '129.6', '21.6', '16.2'):
                assert cote not in code, (numero, cote, ligne.strip())


def test_une_source_absente_est_signalee(tmp_path):
    import os
    manquante = os.path.join(str(tmp_path), 'absente.json')
    with pytest.raises(geometrie.GeometrieIndisponible, match='absentes'):
        geometrie.charger_cotes(manquante)


def test_le_module_reste_pur():
    """Règle 4 : aucun import `iesve`, testable en CI."""
    import io
    import os
    chemin = os.path.abspath(geometrie.__file__).replace('.pyc', '.py')
    with io.open(chemin, encoding='utf-8') as flux:
        for numero, ligne in enumerate(flux, 1):
            nu = ligne.strip()
            assert not nu.startswith(('import iesve', 'from iesve')), numero


def test_le_resume_est_lisible(cotes):
    texte = geometrie.resumer(cotes)
    assert 'SUD' in texte
    assert 'front_wall' in texte
    assert 'concordent' in texte
