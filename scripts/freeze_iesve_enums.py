# -*- coding: utf-8 -*-
u"""Fige les énumérés du module `iesve`, relevés dans une VE réellement ouverte.

POURQUOI CE FICHIER EXISTE. La documentation `refs/VEScripts-API-VE2023.pdf`
§6.1.32.4 liste bien les MEMBRES de ces énumérés, et le relevé les confirme un
par un. Ce qu'elle ne donne pas :

  * les **valeurs numériques** — aucune n'y figure ;
  * les **alias** — `struct_fram` (= 26, à côté de `struct_frame`) est absent
    de la documentation, et rien n'y indique que `ceiling` et `int_floor`
    partagent la valeur 1 ;
  * un **membre ajouté depuis** — `surface_tile` (= 37) n'existe pas en
    VE 2023 ;
  * le **conteneur réel**, sur lequel elle est contradictoire (voir ci-dessous).

La documentation vise VE 2023 et le relevé une VE 2025. Leur concordance a été
vérifiée membre par membre (`ve_adapter/tests/test_enums_iesve.py`) : à part
les deux noms ci-dessus, elles sont identiques et rien n'a disparu.

CE QUE LE RELEVÉ A PERMIS DE CORRIGER. La sonde du Test 1 échouait sur
« Enum 'iesve.<class 'iesve.VECdbProject'>.element_categories' introuvable ».
Deux erreurs cumulées, aucune imputable à la documentation :

  1. ces énumérés appartiennent au **module** `iesve`, pas à la classe
     `VECdbProject`. Le titre « 6.1.32.4 Enums Defined Here » les range sous
     `VECdbProject` et nous a induits en erreur — mais la prose de la même
     section écrit `'iesve.construction_class.none'`, c'est-à-dire le chemin
     module. L'indice était là ; il n'a pas été lu. Un titre de section n'est
     pas une preuve de conteneur d'exécution ;
  2. `material_categories` n'a **aucun** membre `opaque` — et la documentation
     ne l'a jamais prétendu : elle liste 20 familles de bibliothèque (`all`,
     `concretes`, `insulating`, `timber`…). `opaque` appartient à
     `construction_class`. Les deux énumérés avaient été confondus par
     inattention.

Usage :
    python scripts/freeze_iesve_enums.py [chemin_du_rapport] [--ecrire]

Le rapport est produit par `Run_VE_SIA4010_Sonde_Test1.py`, au bouton Run
depuis VE.
"""

from __future__ import print_function

import io
import json
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))

_SORTIE = os.path.join(_RACINE, 'refs', 'reference-data',
                       'iesve-enums-ve2025.json')

#: Rapports de sonde cherchés par défaut, dans l'ordre. Le second couvre le
#: dépôt d'origine, avant la consolidation du 2026-08-06.
RAPPORTS_PAR_DEFAUT = (
    os.path.join(_RACINE, 'outputs', 'sonde_test1_600.json'),
    os.path.join(os.path.expanduser('~'), 'Documents', 'SIA_Compliance_Scripts',
                 'outputs', 'sonde_test1_600.json'),
)

#: Énumérés que le projet utilise réellement. On ne fige pas les 149 : seuls
#: ceux dont dépend du code, pour que le fichier reste relisable.
ENUMS_RETENUS = (
    'element_categories',
    'construction_class',
    'material_categories',
    'AirExchange_type',
)

#: Membres hérités d'`int` par les IntEnum, à écarter du relevé.
BRUIT_INT = frozenset((
    'as_integer_ratio', 'bit_count', 'bit_length', 'ceiling_', 'conjugate',
    'denominator', 'から', 'from_bytes', 'imag', 'is_integer', 'name', 'names',
    'numerator', 'real', 'to_bytes', 'values',
))

RESERVES = [
    u'ceiling et int_floor partagent la valeur 1 ; struct_fram et '
    u'struct_frame partagent 26. Ce sont des alias de l\'API, pas une erreur '
    u'de relevé. La documentation ne mentionne ni struct_fram ni le partage '
    u'de valeur.',
    u'material_categories est un classement de BIBLIOTHÈQUE, sans effet sur '
    u'la simulation : les propriétés physiques sont portées ailleurs. Y '
    u'chercher « opaque » est une confusion avec construction_class.',
    u'Conteneur : ces énumérés sont sur le MODULE iesve. La documentation les '
    u'range sous « 6.1.32.4 Enums Defined Here » de VECdbProject, mais sa '
    u'propre prose écrit iesve.construction_class.none. Le relevé tranche en '
    u'faveur du module.',
    u'Concordance avec §6.1.32.4 (VE 2023), vérifiée membre par membre : '
    u'construction_class et material_categories sont identiques ; '
    u'element_categories compte deux noms de plus — struct_fram (alias non '
    u'documenté de struct_frame, même valeur 26) et surface_tile (= 37, '
    u'ajouté après VE 2023, à la suite de double_facade = 36). Aucun membre '
    u'documenté n\'a disparu. C\'est la seule dérive d\'API constatée.',
    u'Les VALEURS numériques ne figurent nulle part dans la documentation : '
    u'elles ne proviennent que de ce relevé.',
    u'Relevé sur une VE 2025. Une autre version peut différer : relancer la '
    u'sonde plutôt que de supposer.',
]


class RapportInexploitable(RuntimeError):
    u"""Levée quand le rapport de sonde ne contient pas les énumérés."""


def _trouver_rapport(chemin=None):
    u"""Localise un rapport de sonde exploitable.

    Args:
        chemin: Chemin explicite, sinon les emplacements par défaut.

    Returns:
        str: Chemin du rapport.

    Raises:
        RapportInexploitable: Si aucun rapport n'est trouvé.
    """
    candidats = (chemin,) if chemin else RAPPORTS_PAR_DEFAUT
    for candidat in candidats:
        if candidat and os.path.isfile(candidat):
            return candidat
    raise RapportInexploitable(
        u'aucun rapport de sonde trouvé. Lancer '
        u'Run_VE_SIA4010_Sonde_Test1.py depuis VE, puis relancer ce script. '
        u'Cherché : %s' % u', '.join(c for c in candidats if c))


def _enums_du_rapport(rapport):
    u"""Extrait la table des énumérés du rapport de sonde.

    Args:
        rapport: Contenu JSON du rapport.

    Returns:
        dict: `{nom d'enum: {membre: valeur}}`.

    Raises:
        RapportInexploitable: Si l'étape d'introspection est absente ou a
            échoué — auquel cas il n'y a rien à figer, et inventer les valeurs
            serait exactement ce que ce fichier existe pour éviter.
    """
    for etape in rapport.get('etapes', []):
        if etape.get('nom') == 'enums du module iesve':
            if etape.get('statut') != 'OK':
                raise RapportInexploitable(
                    u'l\'introspection des énumérés a échoué dans VE : %s'
                    % etape.get('erreur'))
            return etape.get('valeur') or {}
    raise RapportInexploitable(
        u'le rapport ne contient pas l\'étape « enums du module iesve ». '
        u'Il vient probablement d\'une sonde v1 : relancer la sonde actuelle.')


def _nettoyer(membres):
    u"""Retire le bruit hérité d'`int` et ne garde que les valeurs entières.

    Args:
        membres: `{nom: valeur}` tel que relevé.

    Returns:
        dict: Membres réels de l'énuméré, triés par valeur puis par nom.
    """
    retenus = dict(
        (nom, valeur) for nom, valeur in membres.items()
        if nom not in BRUIT_INT and isinstance(valeur, int)
        and not isinstance(valeur, bool))
    return dict(sorted(retenus.items(), key=lambda p: (p[1], p[0])))


def construire(chemin_rapport=None):
    u"""Construit la structure à figer depuis un rapport de sonde.

    Args:
        chemin_rapport: Chemin explicite du rapport.

    Returns:
        dict: Structure prête à écrire.

    Raises:
        RapportInexploitable: Si un énuméré attendu manque au relevé.
    """
    chemin = _trouver_rapport(chemin_rapport)
    with io.open(chemin, encoding='utf-8') as flux:
        rapport = json.load(flux)

    releves = _enums_du_rapport(rapport)
    manquants = [nom for nom in ENUMS_RETENUS if nom not in releves]
    if manquants:
        raise RapportInexploitable(
            u'énumérés absents du relevé : %s. L\'API a peut-être changé ; '
            u'ne pas les inventer.' % u', '.join(manquants))

    donnees = {
        u'grandeur': u'Énumérés du module iesve, relevés dans une VE ouverte',
        u'statut': u'FIGÉ — introspection runtime, pas une lecture de doc',
        u'source': {
            u'rapport': os.path.basename(chemin),
            u'methode': u'Run_VE_SIA4010_Sonde_Test1.py, étape '
                        u'« enums du module iesve »',
            u'nombre_enums_du_module': len(releves),
            u'pourquoi': u'§6.1.32.4 de VEScripts-API-VE2023.pdf liste les '
                         u'membres — que ce relevé confirme — mais ne donne '
                         u'aucune valeur numérique, omet les alias, et range '
                         u'ces énumérés sous VECdbProject alors qu\'ils sont '
                         u'sur le module iesve.',
            u'concordance_documentation': u'Vérifiée membre par membre contre '
                                          u'§6.1.32.4 (VE 2023) : identique, '
                                          u'sauf element_categories qui gagne '
                                          u'struct_fram (alias) et '
                                          u'surface_tile (ajout VE 2025). '
                                          u'Aucune disparition.',
        },
        u'reserves': RESERVES,
    }
    for nom in ENUMS_RETENUS:
        donnees[nom] = _nettoyer(releves[nom])
    return donnees


def main(arguments):
    u"""Point d'entrée en ligne de commande.

    Args:
        arguments: Arguments sans le nom du script.

    Returns:
        int: 0 si tout s'est bien passé.
    """
    chemins = [a for a in arguments if not a.startswith('--')]
    donnees = construire(chemins[0] if chemins else None)

    print(u'relevé : %s' % donnees[u'source'][u'rapport'])
    print(u'énumérés du module : %d, dont %d figés'
          % (donnees[u'source'][u'nombre_enums_du_module'], len(ENUMS_RETENUS)))
    for nom in ENUMS_RETENUS:
        membres = donnees[nom]
        apercu = u', '.join(u'%s=%d' % (k, v)
                            for k, v in list(membres.items())[:6])
        print(u'  %-22s %2d membres  %s…' % (nom, len(membres), apercu))

    if '--ecrire' in arguments:
        with io.open(_SORTIE, 'w', encoding='utf-8') as flux:
            flux.write(json.dumps(donnees, ensure_ascii=False, indent=2))
            flux.write(u'\n')
        print()
        print(u'écrit : %s' % os.path.relpath(_SORTIE, _RACINE))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
