# -*- coding: utf-8 -*-
u"""Contrôle de provenance des modules du projet, sous VEScripts.

LE PIÈGE. VEScripts garde le **même interpréteur** d'un clic sur Run au
suivant : `sys.modules` persiste. Un paquet `scripts` importé depuis un AUTRE
dépôt y reste en cache et masque celui-ci — même si `sys.path` a été corrigé
entre-temps, puisqu'un module déjà chargé n'est jamais rechargé.

C'est arrivé le 2026-08-06 :

    ImportError: cannot import name 'sonde_aps' from 'scripts'
    (C:\\Users\\ulysse.couliou\\Documents\\SIA_Compliance_Scripts\\scripts\\__init__.py)

Le fichier existait bien, mais dans le dépôt consolidé — pas dans celui que VE
avait en mémoire.

Le cas visible est le moins dangereux : il lève. Le cas dangereux est
silencieux — `ve_adapter` chargé depuis l'ancien dépôt tournerait sans rien
dire, avec un code antérieur aux corrections, et produirait des résultats
crédibles issus de la mauvaise source.

LA PURGE NE PEUT PAS VIVRE ICI. Elle doit s'exécuter *avant* le premier
`import scripts...`, donc dans le lanceur lui-même. Ce module apporte le
contrôle qui vient après, une fois les imports faits.
"""

from __future__ import print_function

import os
import sys

#: Paquets du projet. Un module chargé depuis un autre dépôt sous l'un de ces
#: noms est une erreur, pas une variante.
PAQUETS = ('scripts', 've_adapter', 'engine', 'ui', 'swiss_sia')


def prefixes_a_purger():
    u"""Préfixes de noms de modules qu'un lanceur doit purger.

    Returns:
        tuple[str]: Noms exacts et préfixes de sous-modules.
    """
    return PAQUETS + tuple(nom + '.' for nom in PAQUETS)


def modules_hors_depot(racine, modules=None):
    u"""Modules du projet chargés depuis un AUTRE dossier que `racine`.

    Args:
        racine: Racine du dépôt attendu.
        modules: Table de modules à examiner ; par défaut `sys.modules`.

    Returns:
        list[tuple[str, str]]: `(nom, fichier)`, triés. Vide si tout va bien.
    """
    table = sys.modules if modules is None else modules
    attendu = os.path.normcase(os.path.abspath(racine))
    intrus = []
    for nom, module in list(table.items()):
        if not _est_du_projet(nom):
            continue
        fichier = getattr(module, '__file__', None)
        if not fichier:
            # Paquet d'espace de noms : aucun fichier à confronter, donc rien
            # à reprocher. Ne pas le signaler faute de preuve.
            continue
        chemin = os.path.normcase(os.path.abspath(fichier))
        if not chemin.startswith(attendu + os.sep):
            intrus.append((nom, fichier))
    return sorted(intrus)


def _est_du_projet(nom):
    u"""Vrai si un nom de module appartient à un paquet du projet.

    Args:
        nom: Nom complet du module.

    Returns:
        bool: Vrai si le nom est un paquet du projet ou l'un de ses enfants.
    """
    return nom in PAQUETS or nom.startswith(tuple(p + '.' for p in PAQUETS))


def message_dintrusion(racine, intrus):
    u"""Rédige le diagnostic à afficher dans la console de VEScripts.

    Args:
        racine: Racine attendue.
        intrus: Ce que rend `modules_hors_depot`.

    Returns:
        str: Message prêt à afficher, vide s'il n'y a rien à dire.
    """
    if not intrus:
        return u''
    lignes = [
        u'ARRET : des modules du projet viennent d\'un autre depot.',
        u'',
        u'  attendu sous : %s' % racine,
    ]
    for nom, fichier in intrus:
        lignes.append(u'  %-28s <- %s' % (nom, fichier))
    lignes.extend([
        u'',
        u'VEScripts garde le meme interpreteur d\'un Run a l\'autre : un',
        u'module deja charge n\'est jamais recharge, meme si sys.path change.',
        u'Fermer VE et le rouvrir suffit a purger le cache.',
        u'',
        u'Tant que ce message apparait, aucun resultat n\'est fiable : le code',
        u'execute n\'est pas celui du depot.',
    ])
    return u'\n'.join(lignes)


def controler(racine):
    u"""Contrôle la provenance et affiche le diagnostic s'il y a lieu.

    Args:
        racine: Racine du dépôt attendu.

    Returns:
        bool: Vrai si tous les modules du projet viennent bien de `racine`.
    """
    intrus = modules_hors_depot(racine)
    if not intrus:
        return True
    print(message_dintrusion(racine, intrus))
    return False
