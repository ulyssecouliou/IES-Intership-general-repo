# -*- coding: utf-8 -*-
u"""Fige la consigne de température du Test 4, lue sur le graphique de la spec.

POURQUOI CE FICHIER EXISTE. Dans `Spezifikation_Test4.pdf`, la ligne
« Sollwerte / Raumlufttemperatur » est **vide dans la couche texte**. La
consigne n'y est pas écrite : elle est dessinée, dans une image occupant le
rectangle (307, 74)–(581, 182) de la page 2.

Conséquence pratique : toute extraction automatique du PDF — la nôtre y
comprise, jusqu'au 2026-08-07 — conclut que le Test 4 n'a pas de consigne de
température. C'est faux, et ce serait une erreur silencieuse : un modèle
construit sans elle tournerait, produirait des nombres, et serait faux.

CE QUE LE GRAPHIQUE MONTRE. Une consigne GLISSANTE, fonction de la moyenne
mobile 48 h de la température extérieure — pas une valeur fixe. Quatre points
d'inflexion sont **annotés en clair sur le tracé** (« 12;23 », « 17;25 »,
« 19;22 », « 23.5;23.5 ») : ce sont des étiquettes du graphique, pas une
lecture de pixels au jugé.

CE QUI RESTE À VÉRIFIER. L'attribution des deux courbes — bleue au
refroidissement, rouge au chauffage — est déduite de leur position relative
(la consigne de chauffage est la plus basse) et non d'une légende : le
graphique n'en porte pas. Le recoupement est cohérent, la bande morte passant
de 1,0 K à 1,5 K, mais il reste une déduction.

Usage :
    python scripts/freeze_test4_consignes.py [--ecrire]
"""

from __future__ import print_function

import io
import json
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))

_SORTIE = os.path.join(_RACINE, 'refs', 'reference-data',
                       'test-4.consignes.json')

_SPEC = os.path.join('SIA_4010_geteilter_Link', 'Test4',
                     'Spezifikation_Test4.pdf')

#: Rectangle de l'image porteuse, page 2 (index 1). Consigné pour que le
#: relevé puisse être refait à l'identique.
_RECTANGLE_IMAGE = {'page': 2, 'x0': 307.35, 'y0': 74.55,
                    'x1': 581.10, 'y1': 182.55}

#: Points d'inflexion, tels qu'ANNOTÉS sur le tracé. Chaque couple est
#: `(moyenne mobile 48 h de la température extérieure, consigne)`, en °C.
#: Hors de ces bornes, les deux courbes sont horizontales.
CONSIGNES = {
    u'chauffage': {
        u'couleur_du_trace': u'rouge (la plus basse)',
        u'points': [[19.0, 22.0], [23.5, 23.5]],
        u'etiquettes_lues': [u'19;22', u'23.5;23.5'],
    },
    u'refroidissement': {
        u'couleur_du_trace': u'bleu (la plus haute)',
        u'points': [[12.0, 23.0], [17.0, 25.0]],
        u'etiquettes_lues': [u'12;23', u'17;25'],
    },
}

RESERVES = [
    u'La consigne est ABSENTE de la couche texte du PDF : elle n\'existe que '
    u'sous forme d\'image. Une extraction textuelle conclut à tort qu\'il n\'y '
    u'a pas de consigne.',
    u'L\'attribution chauffage/refroidissement est DÉDUITE de la position '
    u'relative des courbes, faute de légende sur le graphique. Cohérente (la '
    u'bande morte passe de 1,0 K à 1,5 K) mais non certifiée.',
    u'Les quatre points viennent des étiquettes portées sur le tracé, pas '
    u'd\'une lecture de pixels. Entre deux points, l\'interpolation linéaire '
    u'est supposée d\'après l\'allure du tracé.',
    u'Hors des bornes, les deux courbes sont horizontales — palier bas avant '
    u'le premier point, palier haut après le second.',
]


def consigne(role, moyenne_48h):
    u"""Consigne de température pour une moyenne extérieure donnée.

    Args:
        role: `'chauffage'` ou `'refroidissement'`.
        moyenne_48h: Moyenne mobile 48 h de la température extérieure, en °C.

    Returns:
        float: Consigne en °C.

    Raises:
        KeyError: Si le rôle est inconnu.
    """
    points = CONSIGNES[role][u'points']
    (x1, y1), (x2, y2) = points[0], points[1]
    if moyenne_48h <= x1:
        return y1
    if moyenne_48h >= x2:
        return y2
    return y1 + (y2 - y1) * (moyenne_48h - x1) / (x2 - x1)


def construire():
    u"""Structure à figer.

    Returns:
        dict: Référentiel prêt à écrire.
    """
    return {
        u'grandeur': u'Consigne de température de l\'air du local — Test SIA '
                     u'4010 n° 4 (Hörsaal)',
        u'statut': u'FIGÉ — lu sur le graphique de la spécification',
        u'type': u'consigne glissante sur la moyenne mobile 48 h de la '
                 u'température extérieure',
        u'unite': u'°C',
        u'source': {
            u'fichier': _SPEC,
            u'emplacement': u'ligne « Sollwerte / Raumlufttemperatur »',
            u'image': _RECTANGLE_IMAGE,
            u'pourquoi': u'La cellule est VIDE dans la couche texte du PDF. '
                         u'La consigne n\'existe que sous forme d\'image.',
        },
        u'abscisse': u'Gleitender 48-h Mittelwert Aussenlufttemperatur, °C',
        u'consignes': CONSIGNES,
        u'reserves': RESERVES,
    }


def main(arguments):
    u"""Point d'entrée en ligne de commande.

    Args:
        arguments: Arguments sans le nom du script.

    Returns:
        int: 0 si tout s'est bien passé.
    """
    donnees = construire()
    for role in sorted(donnees[u'consignes']):
        points = donnees[u'consignes'][role][u'points']
        print(u'%-16s %s  (paliers hors bornes)'
              % (role, u' -> '.join(u'%.1f °C ext = %.1f °C' % tuple(p)
                                    for p in points)))
    print()
    for exterieure in (-10.0, 12.0, 15.0, 19.0, 21.0, 30.0):
        print(u'  ext %6.1f °C : chauffage %.2f  refroidissement %.2f'
              % (exterieure, consigne('chauffage', exterieure),
                 consigne('refroidissement', exterieure)))
    if '--ecrire' in arguments:
        with io.open(_SORTIE, 'w', encoding='utf-8') as flux:
            flux.write(json.dumps(donnees, ensure_ascii=False, indent=1))
            flux.write(u'\n')
        print()
        print(u'écrit : %s' % os.path.relpath(_SORTIE, _RACINE))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
