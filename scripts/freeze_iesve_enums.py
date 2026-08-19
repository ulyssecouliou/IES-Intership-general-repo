# -*- coding: utf-8 -*-
u"""Freezes the `iesve` module enumerated types, read from a real open VE instance.

WHY THIS FILE EXISTS. The documentation `refs/VEScripts-API-VE2023.pdf`
§6.1.32.4 does list the MEMBERS of these enums, and the reading confirms them
one by one. What it does not give:

  * the **numeric values** — none appear;
  * the **aliases** — `struct_fram` (= 26, alongside `struct_frame`) is absent
    from the documentation, and nothing indicates that `ceiling` and `int_floor`
    share the value 1;
  * a **member added since** — `surface_tile` (= 37) does not exist in VE 2023;
  * the **actual container**, on which it is contradictory (see below).

The documentation targets VE 2023 and the reading a VE 2025. Their agreement
was verified member by member (`ve_adapter/tests/test_enums_iesve.py`): apart
from the two names above, they are identical and nothing has disappeared.

WHAT THE READING ALLOWED TO CORRECT. The Test 1 probe was failing with
"Enum 'iesve.<class 'iesve.VECdbProject'>.element_categories' not found".
Two cumulated errors, neither attributable to the documentation:

  1. these enums belong to the **module** `iesve`, not to the class
     `VECdbProject`. The heading "6.1.32.4 Enums Defined Here" places them under
     `VECdbProject` and misled us — but the prose of the same section writes
     `'iesve.construction_class.none'`, i.e. the module path. The clue was there;
     it was not read. A section heading is not proof of a runtime container;
  2. `material_categories` has **no** member `opaque` — and the documentation
     never claimed it did: it lists 20 library families (`all`, `concretes`,
     `insulating`, `timber`...). `opaque` belongs to `construction_class`. The
     two enums had been confused through inattention.

Usage:
    python scripts/freeze_iesve_enums.py [chemin_du_rapport] [--ecrire]

The report is produced by `Run_VE_SIA4010_Sonde_Test1.py`, via the Run button
from VE.
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

#: Probe reports searched by default, in order. The second covers the original
#: repository, before the 2026-08-06 consolidation.
RAPPORTS_PAR_DEFAUT = (
    os.path.join(_RACINE, 'outputs', 'sonde_test1_600.json'),
    os.path.join(os.path.expanduser('~'), 'Documents', 'SIA_Compliance_Scripts',
                 'outputs', 'sonde_test1_600.json'),
)

#: Enums the project actually uses. Not all 149 are frozen: only those that
#: code depends on, so the file remains readable.
ENUMS_RETENUS = (
    'element_categories',
    'construction_class',
    'material_categories',
    'AirExchange_type',
)

#: Members inherited from `int` by IntEnums, to exclude from the reading.
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
    u"""Raised when the probe report does not contain the enumerated types."""


def _trouver_rapport(chemin=None):
    u"""Locates a usable probe report.

    Args:
        chemin: Explicit path, otherwise the default locations.

    Returns:
        str: Report path.

    Raises:
        RapportInexploitable: If no report is found.
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
    u"""Extracts the enum table from the probe report.

    Args:
        rapport: JSON content of the report.

    Returns:
        dict: `{enum name: {member: value}}`.

    Raises:
        RapportInexploitable: If the introspection step is absent or failed —
            in which case there is nothing to freeze, and inventing the values
            would be exactly what this file exists to prevent.
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
    u"""Removes `int`-inherited noise and keeps only integer values.

    Args:
        membres: `{name: value}` as read.

    Returns:
        dict: Actual enum members, sorted by value then name.
    """
    retenus = dict(
        (nom, valeur) for nom, valeur in membres.items()
        if nom not in BRUIT_INT and isinstance(valeur, int)
        and not isinstance(valeur, bool))
    return dict(sorted(retenus.items(), key=lambda p: (p[1], p[0])))


def construire(chemin_rapport=None):
    u"""Builds the structure to freeze from a probe report.

    Args:
        chemin_rapport: Explicit report path.

    Returns:
        dict: Structure ready to write.

    Raises:
        RapportInexploitable: If an expected enum is missing from the reading.
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
    u"""Command-line entry point.

    Args:
        arguments: Arguments without the script name.

    Returns:
        int: 0 if everything went well.
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
