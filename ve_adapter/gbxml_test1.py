# -*- coding: utf-8 -*-
u"""Writes the Test 1 trial cell as gbXML, for import into VE.

WHY THIS FILE. The `iesve` API exposes no geometry constructor:
no room, no body, no surface. The only path is `ImportGBXML.import_file`
(lowercase -- the documented casing `Import_file` does not exist, confirmed by
introspection on 2026-08-07). The geometry must therefore be described in a
file.

ALL DIMENSIONS COME FROM `geometrie_test1`, which itself holds them from
`config/iso52016_chapter7_confirmed_inputs.json` -- clause 7.2.2.2, Figure 2 and
Table 22, page 123 of BS EN ISO 52016-1:2017. None are entered here.

WHAT IS DELIBERATELY NOT WRITTEN. No **location**: no latitude, no
longitude, no postal code, no altitude. Test 1 is defined by its climate
file, not by a site, and inventing coordinates would produce a plausible model
whose solar would be wrong. The `CADModelAzimuth` field is however written
at 0: it is what fixes the SOUTH orientation of the front facade, and the
specification requires it.

COORDINATE FRAME. X towards east, Y towards north, Z upwards; front facade
faces south, so at Y = 0. Polylines turn **counter-clockwise seen from the
outside**, gbXML convention: a reversed winding would flip the normal and
corrupt the entire solar balance, without any surface area check detecting it.
That is why the tests also verify the winding, not only the area.

Pure Python: no `iesve`, no writing into VE. Testable in continuous integration.
"""

from __future__ import print_function

import io
import os
from xml.etree import ElementTree

from ve_adapter import geometrie_test1 as geometrie

#: gbXML namespace. Taken verbatim from the public schema.
NAMESPACE = 'http://www.gbxml.org/schema'

#: Schema version declared. Chosen for broad compatibility; adjust
#: if VE's importer complains -- the error message will say so.
VERSION_SCHEMA = '0.37'

#: Model azimuth. Zero places the front facade (Y = 0) to the SOUTH, as
#: required by the specification. This is not a location: it is an
#: orientation, and it is established.
AZIMUT_MODELE = 0.0

#: gbXML surface types, by face. `SlabOnGrade` for the floor is the
#: closest type to the ASHRAE 140 cell, whose floor is insulated
#: with an ideal insulator rather than on a ground slab -- TO VERIFY against
#: the actual behaviour of the importer.
TYPE_DE_SURFACE = {
    'front_wall': 'ExteriorWall',
    'back_wall': 'ExteriorWall',
    'left_wall': 'ExteriorWall',
    'right_wall': 'ExteriorWall',
    'floor': 'SlabOnGrade',
    'ceiling': 'Roof',
}

#: Stable identifiers. Freezing them allows each surface to be found in the
#: imported model, and its area to be compared against the source.
IDENTIFIANT_ESPACE = 'TEST1-CELL'
IDENTIFIANT_ZONE = 'TEST1-ZONE'
IDENTIFIANT_BATIMENT = 'TEST1-BUILDING'
IDENTIFIANT_CAMPUS = 'TEST1-CAMPUS'


class GbxmlIncoherent(ValueError):
    u"""Raised when the written geometry does not reproduce the source."""


def polylignes(cotes):
    u"""Polyline of each face, counter-clockwise seen from the outside.

    Args:
        cotes: `geometry` block from the source.

    Returns:
        dict: `{face: [(x, y, z), ...]}`.
    """
    largeur = cotes['width_m']
    profondeur = cotes['depth_m']
    hauteur = cotes['height_m']
    return {
        # SOUTH facade (front), exterior at -Y: seen from the south, east is on the right.
        'front_wall': [(0.0, 0.0, 0.0), (largeur, 0.0, 0.0),
                       (largeur, 0.0, hauteur), (0.0, 0.0, hauteur)],
        # NORTH facade, exterior at +Y: seen from the north, east moves to the left.
        'back_wall': [(largeur, profondeur, 0.0), (0.0, profondeur, 0.0),
                      (0.0, profondeur, hauteur), (largeur, profondeur, hauteur)],
        # WEST gable, exterior at -X.
        'left_wall': [(0.0, profondeur, 0.0), (0.0, 0.0, 0.0),
                      (0.0, 0.0, hauteur), (0.0, profondeur, hauteur)],
        # EAST gable, exterior at +X.
        'right_wall': [(largeur, 0.0, 0.0), (largeur, profondeur, 0.0),
                       (largeur, profondeur, hauteur), (largeur, 0.0, hauteur)],
        # Floor, exterior at -Z: counter-clockwise seen from BELOW.
        'floor': [(0.0, 0.0, 0.0), (0.0, profondeur, 0.0),
                  (largeur, profondeur, 0.0), (largeur, 0.0, 0.0)],
        # Roof, exterior at +Z: counter-clockwise seen from ABOVE.
        'ceiling': [(0.0, 0.0, hauteur), (largeur, 0.0, hauteur),
                    (largeur, profondeur, hauteur), (0.0, profondeur, hauteur)],
    }


def polylignes_des_fenetres(cotes):
    u"""Polyline of each window, in the plane of the south facade.

    Same winding as the wall that carries them: an opening wound in the
    opposite direction to its wall would flip its normal.

    Args:
        cotes: `geometry` block.

    Returns:
        list[dict]: `{'rang', 'polyligne', 'surface_m2'}` per window.
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
    u"""Unnormalised normal of a polygon, using Newell's method.

    Robust to non-planar polygons and independent of the starting vertex,
    which a simple cross-product of two edges is not.

    Args:
        polyligne: Vertices `(x, y, z)`.

    Returns:
        tuple[float, float, float]: Normal vector.
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
    u"""Area of a polygon defined by its vertices.

    Args:
        polyligne: Vertices `(x, y, z)`.

    Returns:
        float: Area in m².
    """
    nx, ny, nz = normale(polyligne)
    return (nx * nx + ny * ny + nz * nz) ** 0.5


def controler_les_polylignes(cotes):
    u"""Recomputes each area from its polyline and compares it to the source.

    This is the check that counts: it does not re-read the dimensions, it
    measures the geometry actually written. A faulty coordinate shows up here,
    whereas simply re-reading the dimensions would see nothing.

    Args:
        cotes: `geometry` block.

    Returns:
        dict: `{face: (recomputed_area, source_area)}`.

    Raises:
        GbxmlIncoherent: On any discrepancy, or on a wrongly oriented normal.
    """
    attendues = geometrie.surfaces_attendues(cotes)
    faces = polylignes(cotes)
    aire_vitrage = sum(f['surface_m2'] for f in polylignes_des_fenetres(cotes))

    ecarts, releve = [], {}
    for face, polyligne in faces.items():
        mesuree = aire(polyligne)
        # The front facade carries the windows: its polyline describes the
        # ENTIRE wall, the opaque area is derived by subtracting glazing.
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
    u"""Adds a `CartesianPoint` to an element.

    Args:
        parent: Host element.
        sommet: `(x, y, z)`.
    """
    point = ElementTree.SubElement(parent, 'CartesianPoint')
    for valeur in sommet:
        ElementTree.SubElement(point, 'Coordinate').text = '%.6f' % valeur


def _polyloop(parent, polyligne):
    u"""Adds a `PolyLoop` to an element.

    Args:
        parent: Host element.
        polyligne: Vertices.
    """
    boucle = ElementTree.SubElement(parent, 'PolyLoop')
    for sommet in polyligne:
        _point(boucle, sommet)


def construire_arbre(cotes=None):
    u"""Builds the gbXML tree of the cell.

    Args:
        cotes: `geometry` block; loaded from the source if absent.

    Returns:
        xml.etree.ElementTree.Element: Root `gbXML` element.

    Raises:
        GbxmlIncoherent: If the written geometry does not reproduce the source.
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
    # NO location is written: no latitude, no longitude, no altitude.
    # Test 1 is defined by its climate file. Only the name is set,
    # and it says what the cell is.
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
    u"""Writes the gbXML to disk.

    Args:
        chemin: File to write.
        cotes: `geometry` block; loaded from the source if absent.

    Returns:
        str: Path written.
    """
    racine = construire_arbre(cotes)
    dossier = os.path.dirname(chemin)
    if dossier and not os.path.isdir(dossier):
        os.makedirs(dossier)
    arbre = ElementTree.ElementTree(racine)
    with io.open(chemin, 'wb') as flux:
        arbre.write(flux, encoding='utf-8', xml_declaration=True)
    return chemin
