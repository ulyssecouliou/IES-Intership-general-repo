# -*- coding: utf-8 -*-
u"""Écrit la cellule d'essai du Test 1 en gbXML, pour import dans VE.

POURQUOI CE FICHIER. L'API `iesve` n'expose aucun constructeur de géométrie :
ni pièce, ni corps, ni surface. La seule voie est `ImportGBXML.import_file`
(minuscule — la casse documentée `Import_file` n'existe pas, confirmé par
introspection le 2026-08-07). La géométrie doit donc être décrite dans un
fichier.

TOUTES LES COTES VIENNENT DE `geometrie_test1`, qui les tient lui-même de
`config/iso52016_chapter7_confirmed_inputs.json` — clause 7.2.2.2, Figure 2 et
Table 22, page 123 de BS EN ISO 52016-1:2017. Aucune n'est saisie ici.

CE QUI N'EST DÉLIBÉRÉMENT PAS ÉCRIT. Aucune **localisation** : ni latitude, ni
longitude, ni code postal, ni altitude. Le Test 1 se définit par son fichier
climatique, pas par un site, et inventer des coordonnées produirait un modèle
plausible dont le solaire serait faux. Le champ `CADModelAzimuth` est en
revanche écrit à 0 : c'est lui qui fixe l'orientation SUD de la façade avant,
et elle, la spécification l'impose.

REPÈRE. X vers l'est, Y vers le nord, Z vers le haut ; façade avant au sud,
donc en Y = 0. Les polylignes tournent dans le sens **anti-horaire vu de
l'extérieur**, convention gbXML : un sens inversé retournerait la normale et
fausserait tout le bilan solaire, sans qu'aucun contrôle de surface ne le voie.
C'est pourquoi les tests vérifient AUSSI le sens, pas seulement l'aire.

Python pur : ni `iesve`, ni écriture dans VE. Testable en intégration continue.
"""

from __future__ import print_function

import io
import os
from xml.etree import ElementTree

from ve_adapter import geometrie_test1 as geometrie

#: Espace de noms gbXML. Repris tel quel du schéma public.
NAMESPACE = 'http://www.gbxml.org/schema'

#: Version de schéma déclarée. Choisie pour sa large compatibilité ; à ajuster
#: si l'importeur de VE s'en plaint — le message d'erreur le dira.
VERSION_SCHEMA = '0.37'

#: Azimut du modèle. Zéro place la façade avant (Y = 0) au SUD, comme
#: l'impose la spécification. Ce n'est pas une localisation : c'est une
#: orientation, et elle est établie.
AZIMUT_MODELE = 0.0

#: Types de surface gbXML, par face. `SlabOnGrade` pour le plancher est le
#: type le plus proche de la cellule ASHRAE 140, dont le plancher est isolé
#: d'un isolant idéal plutôt que posé sur terre-plein — À VÉRIFIER contre le
#: comportement réel de l'importeur.
TYPE_DE_SURFACE = {
    'front_wall': 'ExteriorWall',
    'back_wall': 'ExteriorWall',
    'left_wall': 'ExteriorWall',
    'right_wall': 'ExteriorWall',
    'floor': 'SlabOnGrade',
    'ceiling': 'Roof',
}

#: Identifiants stables. Les figer permet de retrouver chaque surface dans le
#: modèle importé, et de confronter son aire à celle de la source.
IDENTIFIANT_ESPACE = 'TEST1-CELL'
IDENTIFIANT_ZONE = 'TEST1-ZONE'
IDENTIFIANT_BATIMENT = 'TEST1-BUILDING'
IDENTIFIANT_CAMPUS = 'TEST1-CAMPUS'


class GbxmlIncoherent(ValueError):
    u"""Levée quand la géométrie écrite ne reproduit pas la source."""


def polylignes(cotes):
    u"""Polyligne de chaque face, dans le sens anti-horaire vu de l'extérieur.

    Args:
        cotes: Bloc `geometry` de la source.

    Returns:
        dict: `{face: [(x, y, z), ...]}`.
    """
    largeur = cotes['width_m']
    profondeur = cotes['depth_m']
    hauteur = cotes['height_m']
    return {
        # Façade SUD (avant), extérieur en -Y : vu du sud, l'est est à droite.
        'front_wall': [(0.0, 0.0, 0.0), (largeur, 0.0, 0.0),
                       (largeur, 0.0, hauteur), (0.0, 0.0, hauteur)],
        # Façade NORD, extérieur en +Y : vu du nord, l'est passe à gauche.
        'back_wall': [(largeur, profondeur, 0.0), (0.0, profondeur, 0.0),
                      (0.0, profondeur, hauteur), (largeur, profondeur, hauteur)],
        # Pignon OUEST, extérieur en -X.
        'left_wall': [(0.0, profondeur, 0.0), (0.0, 0.0, 0.0),
                      (0.0, 0.0, hauteur), (0.0, profondeur, hauteur)],
        # Pignon EST, extérieur en +X.
        'right_wall': [(largeur, 0.0, 0.0), (largeur, profondeur, 0.0),
                       (largeur, profondeur, hauteur), (largeur, 0.0, hauteur)],
        # Plancher, extérieur en -Z : anti-horaire vu de DESSOUS.
        'floor': [(0.0, 0.0, 0.0), (0.0, profondeur, 0.0),
                  (largeur, profondeur, 0.0), (largeur, 0.0, 0.0)],
        # Toiture, extérieur en +Z : anti-horaire vu de DESSUS.
        'ceiling': [(0.0, 0.0, hauteur), (largeur, 0.0, hauteur),
                    (largeur, profondeur, hauteur), (0.0, profondeur, hauteur)],
    }


def polylignes_des_fenetres(cotes):
    u"""Polyligne de chaque fenêtre, dans le plan de la façade sud.

    Même sens que la façade qui les porte : une ouverture au sens inverse de
    son mur retournerait sa normale.

    Args:
        cotes: Bloc `geometry`.

    Returns:
        list[dict]: `{'rang', 'polyligne', 'surface_m2'}` par fenêtre.
    """
    fenetres = []
    for rectangle in geometrie.rectangles_des_fenetres(cotes):
        x1, x2 = rectangle['x_min'], rectangle['x_max']
        z1, z2 = rectangle['z_min'], rectangle['z_max']
        fenetres.append({
            'rang': rectangle['rang'],
            'polyligne': [(x1, 0.0, z1), (x2, 0.0, z1),
                          (x2, 0.0, z2), (x1, 0.0, z2)],
            'surface_m2': rectangle['surface_m2'],
        })
    return fenetres


def normale(polyligne):
    u"""Normale non normalisée d'un polygone, par la méthode de Newell.

    Robuste aux polygones non plans et indépendante du sommet de départ, ce
    qu'un simple produit vectoriel de deux arêtes n'est pas.

    Args:
        polyligne: Sommets `(x, y, z)`.

    Returns:
        tuple[float, float, float]: Vecteur normal.
    """
    nx = ny = nz = 0.0
    nombre = len(polyligne)
    for rang in range(nombre):
        x1, y1, z1 = polyligne[rang]
        x2, y2, z2 = polyligne[(rang + 1) % nombre]
        nx += (y1 - y2) * (z1 + z2)
        ny += (z1 - z2) * (x1 + x2)
        nz += (x1 - x2) * (y1 + y2)
    return (nx / 2.0, ny / 2.0, nz / 2.0)


def aire(polyligne):
    u"""Aire d'un polygone défini par ses sommets.

    Args:
        polyligne: Sommets `(x, y, z)`.

    Returns:
        float: Aire en m².
    """
    nx, ny, nz = normale(polyligne)
    return (nx * nx + ny * ny + nz * nz) ** 0.5


def controler_les_polylignes(cotes):
    u"""Recalcule chaque aire depuis sa polyligne et la confronte à la source.

    C'est le contrôle qui compte : il ne relit pas les cotes, il mesure la
    géométrie effectivement écrite. Une coordonnée fautive y apparaît, là où
    une simple relecture des cotes ne verrait rien.

    Args:
        cotes: Bloc `geometry`.

    Returns:
        dict: `{face: (aire_recalculee, aire_source)}`.

    Raises:
        GbxmlIncoherent: Au moindre écart, ou sur une normale mal orientée.
    """
    attendues = geometrie.surfaces_attendues(cotes)
    faces = polylignes(cotes)
    aire_vitrage = sum(f['surface_m2'] for f in polylignes_des_fenetres(cotes))

    ecarts, releve = [], {}
    for face, polyligne in faces.items():
        mesuree = aire(polyligne)
        # La façade avant porte les fenêtres : sa polyligne décrit le mur
        # ENTIER, l'aire opaque s'en déduit en retirant le vitrage.
        opaque = mesuree - aire_vitrage if face == 'front_wall' else mesuree
        attendue = attendues[face]
        releve[face] = (opaque, attendue)
        if abs(opaque - attendue) > geometrie.TOLERANCE_SURFACE_M2:
            ecarts.append(u'%s : polyligne %.4f m2, source %.4f m2'
                          % (face, opaque, attendue))

    for face, sens in (('front_wall', (0.0, -1.0, 0.0)),
                       ('back_wall', (0.0, 1.0, 0.0)),
                       ('left_wall', (-1.0, 0.0, 0.0)),
                       ('right_wall', (1.0, 0.0, 0.0)),
                       ('floor', (0.0, 0.0, -1.0)),
                       ('ceiling', (0.0, 0.0, 1.0))):
        vecteur = normale(faces[face])
        longueur = aire(faces[face]) or 1.0
        unitaire = tuple(composante / longueur for composante in vecteur)
        produit = sum(a * b for a, b in zip(unitaire, sens))
        if produit < 0.99:
            ecarts.append(
                u'%s : normale orientee vers l interieur (produit %.3f). Le '
                u'bilan solaire serait faux sans qu aucune aire ne le montre.'
                % (face, produit))

    if ecarts:
        raise GbxmlIncoherent(u'geometrie ecrite incoherente : %s'
                              % u' ; '.join(ecarts))
    return releve


def _point(parent, sommet):
    u"""Ajoute un `CartesianPoint` à un élément.

    Args:
        parent: Élément d'accueil.
        sommet: `(x, y, z)`.
    """
    point = ElementTree.SubElement(parent, 'CartesianPoint')
    for valeur in sommet:
        ElementTree.SubElement(point, 'Coordinate').text = '%.6f' % valeur


def _polyloop(parent, polyligne):
    u"""Ajoute une `PolyLoop` à un élément.

    Args:
        parent: Élément d'accueil.
        polyligne: Sommets.
    """
    boucle = ElementTree.SubElement(parent, 'PolyLoop')
    for sommet in polyligne:
        _point(boucle, sommet)


def construire_arbre(cotes=None):
    u"""Construit l'arbre gbXML de la cellule.

    Args:
        cotes: Bloc `geometry` ; chargé depuis la source si absent.

    Returns:
        xml.etree.ElementTree.Element: Racine `gbXML`.

    Raises:
        GbxmlIncoherent: Si la géométrie écrite ne reproduit pas la source.
    """
    cotes = cotes or geometrie.charger_cotes()
    controler_les_polylignes(cotes)

    faces = polylignes(cotes)
    fenetres = polylignes_des_fenetres(cotes)

    racine = ElementTree.Element('gbXML', {
        'xmlns': NAMESPACE,
        'temperatureUnit': 'C',
        'lengthUnit': 'Meters',
        'areaUnit': 'SquareMeters',
        'volumeUnit': 'CubicMeters',
        'useSIUnitsForResults': 'true',
        'version': VERSION_SCHEMA,
    })

    campus = ElementTree.SubElement(racine, 'Campus',
                                    {'id': IDENTIFIANT_CAMPUS})
    # AUCUNE localisation n est ecrite : ni latitude, ni longitude, ni
    # altitude. Le Test 1 se definit par son fichier climatique. Seul le nom
    # est pose, et il dit ce que la cellule est.
    lieu = ElementTree.SubElement(campus, 'Location')
    ElementTree.SubElement(lieu, 'Name').text = (
        'EN ISO 52016-1 clause 7.2.2 test cell — location intentionally '
        'unset; the climate is defined by the weather file')
    ElementTree.SubElement(lieu, 'CADModelAzimuth').text = '%.1f' % AZIMUT_MODELE

    batiment = ElementTree.SubElement(
        campus, 'Building',
        {'id': IDENTIFIANT_BATIMENT, 'buildingType': 'Unknown'})
    ElementTree.SubElement(batiment, 'Area').text = '%.4f' % (
        cotes['width_m'] * cotes['depth_m'])

    espace = ElementTree.SubElement(
        batiment, 'Space',
        {'id': IDENTIFIANT_ESPACE, 'zoneIdRef': IDENTIFIANT_ZONE})
    ElementTree.SubElement(espace, 'Name').text = IDENTIFIANT_ESPACE
    ElementTree.SubElement(espace, 'Area').text = '%.4f' % (
        cotes['width_m'] * cotes['depth_m'])
    ElementTree.SubElement(espace, 'Volume').text = '%.4f' % cotes['volume_m3']

    coque = ElementTree.SubElement(espace, 'ShellGeometry',
                                   {'id': IDENTIFIANT_ESPACE + '-SHELL'})
    fermee = ElementTree.SubElement(coque, 'ClosedShell')
    for face in geometrie.FACES:
        _polyloop(fermee, faces[face])

    for face in geometrie.FACES:
        surface = ElementTree.SubElement(campus, 'Surface', {
            'id': '%s-%s' % (IDENTIFIANT_ESPACE, face.upper()),
            'surfaceType': TYPE_DE_SURFACE[face],
        })
        ElementTree.SubElement(surface, 'Name').text = face
        ElementTree.SubElement(surface, 'AdjacentSpaceId',
                               {'spaceIdRef': IDENTIFIANT_ESPACE})
        plan = ElementTree.SubElement(surface, 'PlanarGeometry')
        _polyloop(plan, faces[face])

        if face != 'front_wall':
            continue
        for fenetre in fenetres:
            ouverture = ElementTree.SubElement(surface, 'Opening', {
                'id': '%s-WINDOW-%d' % (IDENTIFIANT_ESPACE, fenetre['rang']),
                'openingType': 'FixedWindow',
            })
            ElementTree.SubElement(ouverture, 'Name').text = (
                'window_%d' % fenetre['rang'])
            plan_ouverture = ElementTree.SubElement(ouverture,
                                                    'PlanarGeometry')
            _polyloop(plan_ouverture, fenetre['polyligne'])

    return racine


def ecrire(chemin, cotes=None):
    u"""Écrit le gbXML sur disque.

    Args:
        chemin: Fichier à écrire.
        cotes: Bloc `geometry` ; chargé depuis la source si absent.

    Returns:
        str: Chemin écrit.
    """
    racine = construire_arbre(cotes)
    dossier = os.path.dirname(chemin)
    if dossier and not os.path.isdir(dossier):
        os.makedirs(dossier)
    arbre = ElementTree.ElementTree(racine)
    with io.open(chemin, 'wb') as flux:
        arbre.write(flux, encoding='utf-8', xml_declaration=True)
    return chemin
