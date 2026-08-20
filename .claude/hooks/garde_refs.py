# -*- coding: utf-8 -*-
u"""Hook PreToolUse — protège les référentiels figés contre l'édition à la main.

POURQUOI. La règle 2 de `CLAUDE.md` pose que la vérité est constituée des
valeurs de référence publiées. Chaque fichier de `refs/reference-data/` est
produit par un script qui, en plus d'extraire, **recalcule et confronte** les
valeurs à leur source officielle. Éditer un tel fichier à la main romprait
silencieusement cette chaîne de preuve : le JSON resterait plausible et ne
serait plus vérifiable.

Ce hook rend l'erreur impossible plutôt que d'espérer qu'on y pense.

CE QU'IL BLOQUE : toute écriture directe sous `refs/`.
CE QU'IL LAISSE PASSER : tout le reste, y compris les scripts de `scripts/`
qui régénèrent ces fichiers — c'est la voie prévue.

Contrat : lit le JSON de l'appel sur stdin, sort en code 2 pour bloquer, avec
le motif sur stderr. Toute autre situation sort en 0 : un hook ne doit jamais
faire échouer une session par excès de zèle.
"""

from __future__ import print_function

import json
import os
import re
import sys

OUTILS_ECRITURE = ('Write', 'Edit', 'MultiEdit', 'NotebookEdit')

# Chemins protégés, relatifs à la racine du dépôt.
PROTEGES = (
    re.compile(r'(^|[\\/])refs[\\/]reference-data[\\/]'),
    re.compile(r'(^|[\\/])refs[\\/][^\\/]+\.(pdf|xls|xlsx)$', re.I),
)

REGENERATEURS = {
    'test-1.ref.json': 'scripts/build_cell_fingerprint.py (et la chaîne Test 1)',
    'test-1.cells.json': 'scripts/build_cell_fingerprint.py',
    'test-7.ref.json': 'scripts/build_test7_reference.py',
    'sia-2024-2021.tables.json': 'scripts/build_sia2024_sia180_refs.py',
    'sia-180-2014.comfort.json': 'scripts/build_sia2024_sia180_refs.py',
    'sia-387-4-2017.blinds.json': 'scripts/build_sia2024_sia180_refs.py',
    'sia-380-2-2022.figure1.json': 'scripts/extract_sia380_2_figure1.py',
    'sia-2028-kloten-temperature.json': 'scripts/extract_kloten_weather_from_sia.py',
    'sia-2028-kloten-temperature.csv': 'scripts/extract_kloten_weather_from_sia.py',
    'iso-52016-1-climat-drycold.json': 'scripts/freeze_iso_drycold_climate.py',
    'sn-en-14825-2018.cooling-seer.json': 'scripts/build_sn_en_14825_seer.py',
}


def main():
    try:
        charge = json.load(sys.stdin)
    except Exception:
        return 0  # entrée illisible : on ne bloque pas

    outil = charge.get('tool_name') or charge.get('toolName') or ''
    if outil not in OUTILS_ECRITURE:
        return 0

    entree = charge.get('tool_input') or charge.get('toolInput') or {}
    chemin = entree.get('file_path') or entree.get('notebook_path') or ''
    if not chemin:
        return 0

    normalise = chemin.replace('\\', '/')
    if not any(motif.search(normalise) for motif in PROTEGES):
        return 0

    nom = os.path.basename(normalise)
    script = REGENERATEURS.get(nom)

    message = [
        u'BLOQUÉ — %s est un référentiel FIGÉ.' % nom,
        u'',
        u"Ces fichiers ne s'éditent pas à la main : ils sont produits par un "
        u'script qui recalcule les valeurs et les confronte à la source '
        u'officielle SIA ou ISO. Une édition manuelle romprait la chaîne de '
        u'preuve exigée par la règle 2 de CLAUDE.md, sans que rien ne le '
        u'signale.',
        u'',
    ]
    if script:
        message.append(u'Voie prévue : modifier puis relancer %s' % script)
    else:
        message.append(u'Voie prévue : modifier le script de scripts/ qui '
                       u'produit ce fichier, puis le relancer.')
    message.append(u'')
    message.append(u"Si le référentiel est réellement faux, corrige "
                   u"l'EXTRACTEUR, pas sa sortie.")

    sys.stderr.write(u'\n'.join(message) + u'\n')
    return 2


if __name__ == '__main__':
    sys.exit(main())
