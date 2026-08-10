# -*- coding: utf-8 -*-
u"""Tests du gbXML de la cellule d'essai (`ve_adapter/gbxml_test1.py`).

Le danger vise est celui qui a coûté le plus cher cette semaine : une
géométrie **plausible et fausse**, importée sans erreur, simulée sans
avertissement. Deux erreurs la produisent, et aucune ne se voit à l'œil :

* une **coordonnée fautive** — les aires ne tombent plus juste ;
* une **normale retournée** — les aires tombent juste, et tout le bilan
  solaire est faux. C'est la plus dangereuse des deux, et c'est pourquoi le
  sens des polylignes est testé au même titre que leur aire.
"""

from xml.etree import ElementTree

import pytest

from ve_adapter import gbxml_test1 as gbxml
from ve_adapter import geometrie_test1 as geometrie


@pytest.fixture(scope='module')
def cotes():
    try:
        return geometrie.charger_cotes()
    except geometrie.GeometrieIndisponible:
        pytest.skip(u'cotes de référence absentes')


# --------------------------------------------------------------------------
# Les aires, recalculées depuis la géométrie écrite
# --------------------------------------------------------------------------

def test_chaque_polyligne_reproduit_laire_de_la_source(cotes):
    """Ce contrôle ne relit pas les cotes : il MESURE la géométrie écrite.
    Une coordonnée fautive y apparaît, là où relire les cotes ne verrait
    rien."""
    for face, (mesuree, source) in gbxml.controler_les_polylignes(
            cotes).items():
        assert abs(mesuree - source) < 1e-9, face


def test_la_facade_avant_deduit_bien_son_vitrage(cotes):
    """Sa polyligne décrit le mur ENTIER — 21,6 m² — et l'aire opaque s'en
    déduit. Confondre les deux doublerait la paroi opaque."""
    entier = gbxml.aire(gbxml.polylignes(cotes)['front_wall'])
    assert entier == pytest.approx(cotes['width_m'] * cotes['height_m'])
    assert gbxml.controler_les_polylignes(cotes)['front_wall'][0] == \
        pytest.approx(cotes['opaque_areas_m2']['front_wall'])


def test_les_deux_fenetres_totalisent_laire_annoncee(cotes):
    total = sum(gbxml.aire(f['polyligne'])
                for f in gbxml.polylignes_des_fenetres(cotes))
    assert total == pytest.approx(cotes['windows']['total_area_m2'])


def test_une_cote_falsifiee_est_detectee(cotes):
    faussees = dict(cotes)
    faussees['width_m'] = 9.0
    with pytest.raises((gbxml.GbxmlIncoherent,
                        geometrie.GeometrieIncoherente)):
        gbxml.controler_les_polylignes(faussees)


# --------------------------------------------------------------------------
# Le sens des polylignes — l'erreur qui ne se voit pas
# --------------------------------------------------------------------------

@pytest.mark.parametrize('face,sens', [
    ('front_wall', (0.0, -1.0, 0.0)),
    ('back_wall', (0.0, 1.0, 0.0)),
    ('left_wall', (-1.0, 0.0, 0.0)),
    ('right_wall', (1.0, 0.0, 0.0)),
    ('floor', (0.0, 0.0, -1.0)),
    ('ceiling', (0.0, 0.0, 1.0)),
])
def test_chaque_normale_pointe_vers_lexterieur(cotes, face, sens):
    polyligne = gbxml.polylignes(cotes)[face]
    vecteur = gbxml.normale(polyligne)
    longueur = gbxml.aire(polyligne)
    unitaire = [composante / longueur for composante in vecteur]
    assert sum(a * b for a, b in zip(unitaire, sens)) == pytest.approx(1.0)


def test_une_normale_retournee_est_refusee(cotes, monkeypatch):
    """Les aires resteraient justes : seul le contrôle de sens l'attrape."""
    vraies = gbxml.polylignes(cotes)

    def retournee(_cotes):
        faussees = dict(vraies)
        faussees['front_wall'] = list(reversed(vraies['front_wall']))
        return faussees

    monkeypatch.setattr(gbxml, 'polylignes', retournee)
    with pytest.raises(gbxml.GbxmlIncoherent, match='interieur'):
        gbxml.controler_les_polylignes(cotes)


def test_la_normale_ne_depend_pas_du_sommet_de_depart(cotes):
    """La méthode de Newell doit être invariante par rotation des sommets ;
    un simple produit vectoriel de deux arêtes ne l'est pas."""
    polyligne = gbxml.polylignes(cotes)['ceiling']
    pivotee = polyligne[2:] + polyligne[:2]
    for attendu, obtenu in zip(gbxml.normale(polyligne),
                               gbxml.normale(pivotee)):
        assert attendu == pytest.approx(obtenu)


def test_les_fenetres_suivent_le_sens_de_leur_mur(cotes):
    """Une ouverture au sens inverse de son mur retournerait sa normale."""
    mur = gbxml.normale(gbxml.polylignes(cotes)['front_wall'])
    for fenetre in gbxml.polylignes_des_fenetres(cotes):
        vitre = gbxml.normale(fenetre['polyligne'])
        produit = sum(a * b for a, b in zip(mur, vitre))
        assert produit > 0, fenetre['rang']


# --------------------------------------------------------------------------
# Orientation et localisation
# --------------------------------------------------------------------------

def test_la_facade_avant_est_bien_au_sud(cotes):
    """L'orientation décide de tout le solaire."""
    for _, y, _ in gbxml.polylignes(cotes)['front_wall']:
        assert y == 0.0


def test_aucune_localisation_nest_ecrite(cotes):
    """Ni latitude, ni longitude, ni altitude : le Test 1 se définit par son
    fichier climatique. Des coordonnées inventées donneraient un modèle
    plausible dont le solaire serait faux."""
    racine = gbxml.construire_arbre(cotes)
    texte = ElementTree.tostring(racine, encoding='unicode')
    for interdit in ('Latitude', 'Longitude', 'Elevation',
                     'ZipcodeOrPostalCode', 'StationId'):
        assert interdit not in texte, interdit


def test_lazimut_est_ecrit_car_il_est_etabli(cotes):
    """Contrairement à la localisation, l'orientation est imposée par la
    spécification : elle, on l'écrit."""
    racine = gbxml.construire_arbre(cotes)
    texte = ElementTree.tostring(racine, encoding='unicode')
    assert 'CADModelAzimuth' in texte


# --------------------------------------------------------------------------
# Structure du document
# --------------------------------------------------------------------------

def test_la_coque_fermee_porte_les_six_faces(cotes):
    racine = gbxml.construire_arbre(cotes)
    coque = racine.find('.//ClosedShell')
    assert coque is not None
    assert len(coque.findall('PolyLoop')) == 6


def test_les_six_surfaces_sont_typees(cotes):
    racine = gbxml.construire_arbre(cotes)
    surfaces = racine.findall('.//Surface')
    assert len(surfaces) == 6
    types = set(s.get('surfaceType') for s in surfaces)
    assert 'Roof' in types
    assert 'ExteriorWall' in types


def test_les_ouvertures_sont_sur_la_facade_avant_seulement(cotes):
    racine = gbxml.construire_arbre(cotes)
    for surface in racine.findall('.//Surface'):
        ouvertures = surface.findall('Opening')
        attendu = 2 if surface.get('id').endswith('FRONT_WALL') else 0
        assert len(ouvertures) == attendu, surface.get('id')


def test_le_volume_declare_est_celui_de_la_source(cotes):
    racine = gbxml.construire_arbre(cotes)
    volume = racine.find('.//Space/Volume')
    assert float(volume.text) == pytest.approx(cotes['volume_m3'])


def test_les_unites_sont_declarees_en_si(cotes):
    racine = gbxml.construire_arbre(cotes)
    assert racine.get('lengthUnit') == 'Meters'
    assert racine.get('useSIUnitsForResults') == 'true'


def test_chaque_sommet_a_trois_coordonnees(cotes):
    racine = gbxml.construire_arbre(cotes)
    for point in racine.findall('.//CartesianPoint'):
        assert len(point.findall('Coordinate')) == 3


# --------------------------------------------------------------------------
# Écriture
# --------------------------------------------------------------------------

def test_le_fichier_ecrit_se_relit(tmp_path):
    import os
    chemin = os.path.join(str(tmp_path), 'sous', 'cellule.xml')
    gbxml.ecrire(chemin)
    assert os.path.exists(chemin)
    racine = ElementTree.parse(chemin).getroot()
    assert racine.tag.endswith('gbXML')


def test_lecriture_refuse_une_geometrie_incoherente(tmp_path, monkeypatch):
    """Mieux vaut ne rien ecrire qu ecrire un fichier faux : il serait
    importe sans erreur."""
    import os
    monkeypatch.setattr(
        gbxml, 'controler_les_polylignes',
        lambda _cotes: (_ for _ in ()).throw(
            gbxml.GbxmlIncoherent('defaut simule')))
    with pytest.raises(gbxml.GbxmlIncoherent):
        gbxml.ecrire(os.path.join(str(tmp_path), 'x.xml'))
    assert not os.path.exists(os.path.join(str(tmp_path), 'x.xml'))


def test_le_module_reste_pur():
    """Règle 4 : aucun import `iesve`."""
    import io
    import os
    chemin = os.path.abspath(gbxml.__file__).replace('.pyc', '.py')
    with io.open(chemin, encoding='utf-8') as flux:
        for numero, ligne in enumerate(flux, 1):
            nu = ligne.strip()
            assert not nu.startswith(('import iesve', 'from iesve')), numero


def test_aucune_cote_nest_ecrite_en_dur():
    """Toutes viennent de `geometrie_test1`, qui les tient de la source."""
    import io
    import os
    chemin = os.path.abspath(gbxml.__file__).replace('.pyc', '.py')
    with io.open(chemin, encoding='utf-8') as flux:
        for numero, ligne in enumerate(flux, 1):
            code = ligne.split('#')[0]
            for cote in ('8.0', '6.0', '2.7', '48.0', '129.6', '21.6'):
                assert cote not in code, (numero, cote, ligne.strip())
