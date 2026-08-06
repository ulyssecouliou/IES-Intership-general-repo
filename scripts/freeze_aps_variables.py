# -*- coding: utf-8 -*-
u"""Fige le catalogue de variables de résultats relevé dans une VE réelle.

POURQUOI CE FICHIER EXISTE. `outputs/` est ignoré par Git. Le rapport de sonde
`outputs/sonde_aps.json` est donc absent d'un clone neuf — et avec lui, la
preuve contre laquelle `ve_adapter/tests/test_bandes_adapter.py` confronte
chaque nom de variable candidat. Ces tests se seraient **ignorés en silence**,
laissant croire que les candidats étaient vérifiés alors que plus rien ne les
contrôlait.

CE QUE CE FICHIER EST, ET N'EST PAS. C'est un **catalogue de noms** : ce que
VE 2025 sait produire. Ce n'est ni une valeur de référence SIA, ni une liaison,
ni un résultat de simulation. Aucune série n'y figure.

Usage :
    python scripts/freeze_aps_variables.py [chemin_du_rapport] [--ecrire]

Le rapport est produit par `Run_VE_SIA4010_Sonde_APS.py`, au bouton Run depuis
VE, sur un projet dont une simulation a déjà tourné.
"""

from __future__ import print_function

import io
import json
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))

_SORTIE = os.path.join(_RACINE, 'refs', 'reference-data',
                       'iesve-aps-variables-ve2025.json')

RAPPORT_PAR_DEFAUT = os.path.join(_RACINE, 'outputs', 'sonde_aps.json')

#: Champs conservés. Tout ce qui sert à reconnaître une grandeur et à convertir
#: son unité, rien de plus.
CHAMPS = ('aps_varname', 'display_name', 'model_level', 'units_type')

RESERVES = [
    u'Catalogue de NOMS, pas de valeurs. Il dit ce que VE sait produire, pas '
    u'ce que vaut une grandeur.',
    u'Relevé sur UN modèle (ZOER_C1). Un modèle doté d\'un réseau ApacheHVAC '
    u'exposerait vraisemblablement d\'autres variables : l\'absence d\'un nom '
    u'ici ne prouve pas que VE ne sait pas le produire.',
    u'Plusieurs entrées partagent un même aps_varname avec des display_name '
    u'ou des units_type différents (ainsi « Ext surface incident solar flux », '
    u'en Radiation flux et en Heat flow). Le couple (aps_varname, '
    u'model_level) n\'est donc PAS une clé unique.',
    u'Les libellés marqués [obs] sont signalés obsolètes par VE elle-même.',
]


class RapportInexploitable(RuntimeError):
    u"""Levée quand le rapport de sonde ne porte pas le relevé complet."""


def _lire_rapport(chemin):
    u"""Charge un rapport de sonde APS.

    Args:
        chemin: Chemin explicite, ou `None` pour l'emplacement par défaut.

    Returns:
        dict: Contenu du rapport.

    Raises:
        RapportInexploitable: Si le fichier manque ou ne porte pas la clé
            `variables` — auquel cas il vient d'une sonde antérieure au relevé
            complet, et figer sa liste tronquée serait pire que ne rien figer.
    """
    chemin = chemin or RAPPORT_PAR_DEFAUT
    if not os.path.isfile(chemin):
        raise RapportInexploitable(
            u'rapport introuvable : %s. Lancer Run_VE_SIA4010_Sonde_APS.py '
            u'depuis VE, sur un projet dont une simulation a tourné.' % chemin)
    with io.open(chemin, encoding='utf-8') as flux:
        rapport = json.load(flux)
    if not rapport.get('variables'):
        raise RapportInexploitable(
            u'le rapport ne porte pas la clé « variables ». Il vient d\'une '
            u'sonde antérieure, dont le relevé était tronqué à 500 entrées : '
            u'le figer donnerait un catalogue incomplet qui se lirait comme '
            u'complet.')
    return rapport


def _normaliser(variables):
    u"""Réduit et ordonne les entrées relevées.

    Args:
        variables: Entrées du rapport.

    Returns:
        list[dict]: Entrées réduites aux champs utiles, triées par niveau puis
            par nom, doublons exacts écartés.
    """
    vues = set()
    retenues = []
    for variable in variables:
        if not isinstance(variable, dict):
            continue
        reduite = dict((champ, variable.get(champ)) for champ in CHAMPS)
        signature = tuple(reduite[champ] for champ in CHAMPS)
        if signature in vues:
            continue
        vues.add(signature)
        retenues.append(reduite)
    return sorted(retenues, key=lambda v: (u'%s' % v['model_level'],
                                           u'%s' % v['aps_varname'],
                                           u'%s' % v['display_name']))


def _compter_par_niveau(variables):
    u"""Compte les entrées par niveau de modèle.

    Args:
        variables: Entrées normalisées.

    Returns:
        dict: `{niveau: nombre}`, trié.
    """
    comptes = {}
    for variable in variables:
        niveau = u'%s' % variable['model_level']
        comptes[niveau] = comptes.get(niveau, 0) + 1
    return dict(sorted(comptes.items()))


def construire(chemin_rapport=None):
    u"""Construit la structure à figer.

    Args:
        chemin_rapport: Chemin explicite du rapport.

    Returns:
        dict: Structure prête à écrire.
    """
    rapport = _lire_rapport(chemin_rapport)
    brutes = rapport['variables']
    variables = _normaliser(brutes)
    return {
        u'grandeur': u'Catalogue des variables de résultats exposées par une '
                     u'VE 2025, relevé dans un .aps réel',
        u'statut': u'FIGÉ — introspection runtime, pas une lecture de doc',
        u'source': {
            u'rapport': os.path.basename(chemin_rapport or RAPPORT_PAR_DEFAUT),
            u'aps': (rapport.get('aps') or {}).get('nom'),
            u'methode': u'Run_VE_SIA4010_Sonde_APS.py, ResultsReader.'
                        u'get_variables() sans argument',
            u'pourquoi': u'outputs/ est ignoré par Git : sans ce fichier, les '
                         u'tests qui confrontent chaque nom candidat à la '
                         u'réalité s\'ignorent en silence sur un clone neuf.',
        },
        u'nombre': len(variables),
        u'nombre_brut': len(brutes),
        u'doublons_exacts_ecartes': len(brutes) - len(variables),
        u'par_niveau': _compter_par_niveau(variables),
        u'reserves': RESERVES,
        u'variables': variables,
    }


def main(arguments):
    u"""Point d'entrée en ligne de commande.

    Args:
        arguments: Arguments sans le nom du script.

    Returns:
        int: 0 si tout s'est bien passé.
    """
    chemins = [a for a in arguments if not a.startswith('--')]
    donnees = construire(chemins[0] if chemins else None)

    print(u'relevé  : %s (%s)' % (donnees[u'source'][u'rapport'],
                                  donnees[u'source'][u'aps']))
    print(u'variables : %d retenues sur %d relevées (%d doublons exacts '
          u'écartés)' % (donnees[u'nombre'], donnees[u'nombre_brut'],
                         donnees[u'doublons_exacts_ecartes']))
    print(u'par niveau : %s'
          % u', '.join(u'%s=%d' % couple
                       for couple in donnees[u'par_niveau'].items()))

    if '--ecrire' in arguments:
        with io.open(_SORTIE, 'w', encoding='utf-8') as flux:
            flux.write(json.dumps(donnees, ensure_ascii=False, indent=1))
            flux.write(u'\n')
        print()
        print(u'écrit : %s' % os.path.relpath(_SORTIE, _RACINE))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
