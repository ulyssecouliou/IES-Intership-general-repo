# -*- coding: utf-8 -*-
u"""Geometry of the Test 1 trial cell, in gbXML.

WHY A FILE, AND NOT API CALLS. The `iesve` API exposes **no geometry
constructor**: no room, no body, no surface. The only path is
`ImportGBXML.import_file`. The geometry must therefore be described in a file,
then imported.

THE POINT LEFT OPEN BY THE AUDIT IS SETTLED. `AUDIT.md` §D noted that the
documentation writes `Import_file` (capital I) where the external repository
called `import_file`, without either having ever seen the call execute.
Introspection of VE 2025 gives **`import_file`, in lowercase**: it is the
documentation that is wrong.

WHAT HAS CHANGED SINCE THE AUDIT REFUSAL. `AUDIT.md` refused to write a
gbXML "not verifiable against a real VE". It now is: once imported,
`VEModel.get_bodies()` and `VEBody.get_areas()` return the actual surfaces,
which can be compared against those from the source. This is the same
write -> read back -> verify loop that served for materials and layers, and
that exposed the 1 mm thicknesses.

ALL DIMENSIONS COME FROM THE SOURCE, none are entered here:
`config/iso52016_chapter7_confirmed_inputs.json`, clause 7.2.2.2, Figure 2 and
Table 22, page 123 of BS EN ISO 52016-1:2017.

Pure Python: no `iesve`, no writing into VE. Testable in continuous integration.
"""

from __future__ import print_function

import io
import json
import os

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))

CHEMIN_SOURCE = os.path.join(_RACINE, 'config',
                             'iso52016_chapter7_confirmed_inputs.json')

#: Surface comparison tolerance, in m². Dimensions are exact to the
#: centimetre; a larger discrepancy signals a construction error, not a
#: rounding issue.
TOLERANCE_SURFACE_M2 = 1e-6

#: Face names, as the source names them. Order follows the coordinate frame:
#: the front facade faces south, orientation imposed by the specification.
FACES = ('front_wall', 'back_wall', 'left_wall', 'right_wall',
         'floor', 'ceiling')


class GeometrieIndisponible(IOError):
    u"""Raised when the reference dimensions cannot be read."""


class GeometrieIncoherente(ValueError):
    u"""Raised when the computed areas do not reproduce the source."""


def charger_cotes(chemin=None):
    u"""Loads the cell dimensions from the frozen source.

    Args:
        chemin: Explicit path, otherwise the repository source.

    Returns:
        dict: `geometry` block from the source.

    Raises:
        GeometrieIndisponible: If the source is missing or does not carry the cell.
    """
    chemin = chemin or CHEMIN_SOURCE
    if not os.path.exists(chemin):
        raise GeometrieIndisponible(
            u'cotes de référence absentes : %s' % chemin)
    with io.open(chemin, encoding='utf-8') as flux:
        source = json.load(flux)
    geometrie = (source.get('hourly_test_cell') or {}).get('geometry')
    if not geometrie:
        raise GeometrieIndisponible(
            u'le fichier %s ne porte pas hourly_test_cell.geometry' % chemin)
    return geometrie


def surfaces_attendues(cotes):
    u"""Computes the opaque areas from the dimensions alone.

    They are RECOMPUTED and not copied: it is this recomputation, compared
    against the source values, that proves the dimensions are self-consistent.

    Args:
        cotes: `geometry` block.

    Returns:
        dict: `{face: area in m²}`, plus `windows`.
    """
    largeur = cotes['width_m']
    profondeur = cotes['depth_m']
    hauteur = cotes['height_m']
    fenetres = cotes['windows']
    aire_vitrage = (fenetres['count'] * fenetres['width_m']
                    * fenetres['height_m'])
    return {
        'front_wall': largeur * hauteur - aire_vitrage,
        'back_wall': largeur * hauteur,
        'left_wall': profondeur * hauteur,
        'right_wall': profondeur * hauteur,
        'floor': largeur * profondeur,
        'ceiling': largeur * profondeur,
        'windows': aire_vitrage,
    }


def controler_les_cotes(cotes):
    u"""Compares the recomputed areas against those announced by the source.

    Args:
        cotes: `geometry` block.

    Returns:
        dict: `{face: (recomputed, announced)}` for information.

    Raises:
        GeometrieIncoherente: On any discrepancy. A mis-read dimension would
            produce a plausible and wrong cell -- and the simulation that
            follows would not say so.
    """
    calculees = surfaces_attendues(cotes)
    annoncees = dict(cotes['opaque_areas_m2'])
    annoncees['windows'] = cotes['windows']['total_area_m2']

    ecarts, releve = [], {}
    for face, valeur in calculees.items():
        attendue = annoncees.get(face)
        releve[face] = (valeur, attendue)
        if attendue is None:
            ecarts.append(u'%s : absente de la source' % face)
        elif abs(valeur - attendue) > TOLERANCE_SURFACE_M2:
            ecarts.append(u'%s : calculée %.4f, annoncée %.4f'
                          % (face, valeur, attendue))

    volume_calcule = (cotes['width_m'] * cotes['depth_m']
                      * cotes['height_m'])
    if abs(volume_calcule - cotes['volume_m3']) > TOLERANCE_SURFACE_M2:
        ecarts.append(u'volume : calculé %.4f, annoncé %.4f'
                      % (volume_calcule, cotes['volume_m3']))

    if ecarts:
        raise GeometrieIncoherente(
            u'les cotes ne se tiennent pas : %s' % u' ; '.join(ecarts))
    return releve


def sommets_de_la_cellule(cotes):
    u"""Vertices of the rectangular box, in metres.

    Coordinate frame: X towards east, Y towards north, Z upwards. The **front
    facade faces south**, so at Y = 0 -- this is the orientation imposed by the
    specification, and it determines the entire solar balance.

    Args:
        cotes: `geometry` block.

    Returns:
        dict: `{name: (x, y, z)}` for the eight vertices.
    """
    largeur = cotes['width_m']
    profondeur = cotes['depth_m']
    hauteur = cotes['height_m']
    return {
        'sud_ouest_bas': (0.0, 0.0, 0.0),
        'sud_est_bas': (largeur, 0.0, 0.0),
        'nord_est_bas': (largeur, profondeur, 0.0),
        'nord_ouest_bas': (0.0, profondeur, 0.0),
        'sud_ouest_haut': (0.0, 0.0, hauteur),
        'sud_est_haut': (largeur, 0.0, hauteur),
        'nord_est_haut': (largeur, profondeur, hauteur),
        'nord_ouest_haut': (0.0, profondeur, hauteur),
    }


def rectangles_des_fenetres(cotes):
    u"""Rectangles of the two windows, in the plane of the south facade.

    Layout imposed by the source: side margin, then window, gap, window, side
    margin. The placement is RECOMPUTED and checked: if the margins and gap do
    not fill the width, the source has been mis-read.

    Args:
        cotes: `geometry` block.

    Returns:
        list[dict]: One rectangle per window, in (x, z) coordinates.

    Raises:
        GeometrieIncoherente: If the placement does not fill the facade.
    """
    fenetres = cotes['windows']
    largeur_mur = cotes['width_m']
    marge = fenetres['side_margin_m']
    intervalle = fenetres['gap_m']
    largeur = fenetres['width_m']
    hauteur = fenetres['height_m']
    allege = fenetres['sill_m']

    occupe = 2 * marge + intervalle + fenetres['count'] * largeur
    if abs(occupe - largeur_mur) > TOLERANCE_SURFACE_M2:
        raise GeometrieIncoherente(
            u'implantation des fenêtres : %.3f m occupés pour un mur de '
            u'%.3f m. Marges, intervalle ou largeurs mal lus.'
            % (occupe, largeur_mur))

    rectangles = []
    x = marge
    for rang in range(fenetres['count']):
        rectangles.append({
            'rang': rang,
            'x_min': x,
            'x_max': x + largeur,
            'z_min': allege,
            'z_max': allege + hauteur,
            'surface_m2': largeur * hauteur,
        })
        x += largeur + intervalle
    return rectangles


def resumer(cotes=None):
    u"""Human-readable summary of the dimensions and their check.

    Args:
        cotes: `geometry` block, loaded from the source if absent.

    Returns:
        str: Text.
    """
    cotes = cotes or charger_cotes()
    releve = controler_les_cotes(cotes)
    lignes = [
        u'Cellule d essai du Test 1 — %.1f x %.1f x %.1f m'
        % (cotes['width_m'], cotes['depth_m'], cotes['height_m']),
        u'Facade avant au SUD ; %d fenetre(s) de %.1f x %.1f m'
        % (cotes['windows']['count'], cotes['windows']['width_m'],
           cotes['windows']['height_m']),
        u'',
        u'  %-14s %10s %10s' % (u'face', u'calculee', u'annoncee'),
    ]
    for face in FACES + ('windows',):
        calculee, annoncee = releve[face]
        lignes.append(u'  %-14s %10.3f %10.3f' % (face, calculee, annoncee))
    lignes.append(u'')
    lignes.append(u'Toutes les surfaces concordent avec la source.')
    return u'\n'.join(lignes)
