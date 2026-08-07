# -*- coding: utf-8 -*-
u"""Géométrie de la cellule d'essai du Test 1, en gbXML.

POURQUOI UN FICHIER, ET PAS DES APPELS D'API. L'API `iesve` n'expose **aucun
constructeur de géométrie** : ni pièce, ni corps, ni surface. La seule voie est
`ImportGBXML.import_file`. La géométrie doit donc être décrite dans un fichier,
puis importée.

LE POINT QUE L'AUDIT LAISSAIT OUVERT EST TRANCHÉ. `AUDIT.md` §D signalait que
la documentation écrit `Import_file` (I majuscule) là où le dépôt externe
appelait `import_file`, sans qu'aucun des deux n'ait jamais vu l'appel
s'exécuter. L'introspection de VE 2025 donne **`import_file`, en minuscule** :
c'est la documentation qui se trompe.

CE QUI A CHANGÉ DEPUIS LE REFUS DE L'AUDIT. `AUDIT.md` refusait d'écrire un
gbXML « non vérifiable contre une VE réelle ». Il l'est désormais : une fois
importé, `VEModel.get_bodies()` et `VEBody.get_areas()` rendent les surfaces
réelles, qu'on confronte à celles de la source. C'est la même boucle
écrire → relire → vérifier qui a servi aux matériaux et aux couches, et qui a
démasqué les épaisseurs à 1 mm.

TOUTES LES COTES VIENNENT DE LA SOURCE, aucune n'est saisie ici :
`config/iso52016_chapter7_confirmed_inputs.json`, clause 7.2.2.2, Figure 2 et
Table 22, page 123 de BS EN ISO 52016-1:2017.

Python pur : ni `iesve`, ni écriture dans VE. Testable en intégration continue.
"""

from __future__ import print_function

import io
import json
import os

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))

CHEMIN_SOURCE = os.path.join(_RACINE, 'config',
                             'iso52016_chapter7_confirmed_inputs.json')

#: Tolérance de comparaison des surfaces, en m². Les cotes sont exactes au
#: centimètre ; un écart supérieur signale une erreur de construction, pas un
#: arrondi.
TOLERANCE_SURFACE_M2 = 1e-6

#: Noms des faces, tels que la source les nomme. L'ordre est celui du repère :
#: la façade avant est au sud, orientation imposée par la spécification.
FACES = ('front_wall', 'back_wall', 'left_wall', 'right_wall',
         'floor', 'ceiling')


class GeometrieIndisponible(IOError):
    u"""Levée quand les cotes de référence ne sont pas lisibles."""


class GeometrieIncoherente(ValueError):
    u"""Levée quand les surfaces calculées ne reproduisent pas la source."""


def charger_cotes(chemin=None):
    u"""Charge les cotes de la cellule depuis la source figée.

    Args:
        chemin: Chemin explicite, sinon la source du dépôt.

    Returns:
        dict: Bloc `geometry` de la source.

    Raises:
        GeometrieIndisponible: Si la source manque ou ne porte pas la cellule.
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
    u"""Calcule les surfaces opaques depuis les seules cotes.

    Elles sont RECALCULÉES et non recopiées : c'est ce recalcul, confronté
    aux valeurs de la source, qui prouve que les cotes se tiennent.

    Args:
        cotes: Bloc `geometry`.

    Returns:
        dict: `{face: surface en m²}`, plus `windows`.
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
    u"""Confronte les surfaces recalculées à celles que la source annonce.

    Args:
        cotes: Bloc `geometry`.

    Returns:
        dict: `{face: (recalculee, annoncee)}` pour information.

    Raises:
        GeometrieIncoherente: Au moindre écart. Une cote mal lue produirait
            une cellule plausible et fausse — et la simulation qui suit ne le
            dirait pas.
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
    u"""Sommets du parallélépipède, en mètres.

    Repère : X vers l'est, Y vers le nord, Z vers le haut. La façade **avant
    est au sud**, donc en Y = 0 — c'est l'orientation qu'impose la
    spécification, et elle décide de tout le solaire.

    Args:
        cotes: Bloc `geometry`.

    Returns:
        dict: `{nom: (x, y, z)}` pour les huit sommets.
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
    u"""Rectangles des deux fenêtres, dans le plan de la façade sud.

    Disposition imposée par la source : marge latérale, puis fenêtre,
    intervalle, fenêtre, marge latérale. L'implantation est RECALCULÉE et
    contrôlée : si les marges et l'intervalle ne remplissent pas la largeur,
    c'est que la source a été mal lue.

    Args:
        cotes: Bloc `geometry`.

    Returns:
        list[dict]: Un rectangle par fenêtre, en coordonnées (x, z).

    Raises:
        GeometrieIncoherente: Si l'implantation ne remplit pas la façade.
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
    u"""Résumé lisible des cotes et de leur contrôle.

    Args:
        cotes: Bloc `geometry`, chargé depuis la source si absent.

    Returns:
        str: Texte.
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
