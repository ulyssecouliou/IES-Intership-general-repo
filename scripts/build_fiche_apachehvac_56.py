# -*- coding: utf-8 -*-
u"""Generates the ApacheHVAC data entry sheets for SIA tests 5 and 6.

SAME REASON AS FOR TEST 4. `HVACNetwork` exposes no creation method:
the network must be entered manually, once, in the ApacheHVAC editor.
Afterwards the `.asp` is versioned and reloaded via `load_network`.

WHAT IS DIFFERENT HERE. The Test 4 sheet is drawn from a Python module where
parameters had been captured one by one. These are drawn from
`refs/reference-data/test-{5,6}.reseau.json`, produced by an extractor that
reads the PDF — so **gaps in the specification bubble up to the sheet**,
named, at the top, instead of being silently filled in.

That is the key point: in Test 5, five parameters depend on the variant
(5A to 5D) and the PDF table has four columns for two cells. A sheet that
resolved them would build two wrong variants out of four, with nothing
flagging it before the final comparison.

Usage:
    python scripts/build_fiche_apachehvac_56.py [--ecrire]
"""

from __future__ import print_function

import io
import json
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

from scripts.build_reseau_ventilation_reference import (  # noqa: E402
    A_CONFIRMER, RELEVE, SUR_GRAPHIQUE)

_REFS = os.path.join(_RACINE, 'refs', 'reference-data')
_DOCS = os.path.join(_RACINE, 'docs')

TESTS = (5, 6)

#: Sections of the sheet, in airflow order, with the expected `iesve` class
#: at survey time. The class name is used to COMPARE the entered network against
#: this sheet after the fact, via `HVACNetwork.components` — it is not an
#: object name to enter.
BLOCS = [
    ('reseau', u'Réseau et conditions générales', None),
    ('ventilateurs', u'Ventilateurs', 'HVACFan'),
    ('recuperateur', u'Récupérateur de chaleur',
     'HVACAirToAirHeatEnthalpyExchanger'),
    ('batterie_chaude', u'Batterie chaude', 'HVACHeatingCoil'),
    ('batterie_froide', u'Batterie froide', 'HVACCoolingCoil'),
    ('humidificateur', u'Humidificateur', None),
]

#: What each sheet enables, and what it does not.
PORTEE = {
    5: (u'Quatre variantes (5A à 5D) : type de récupérateur, taux d\'échange, '
        u'part de pression constante et type d\'humidificateur en dépendent.',
        u'Test 5 — classes de validation 2B, 4A et 4B'),
    6: (u'Une seule configuration : récupération par boucle à eau glycolée '
        u'(« Kreislaufverbund »), ventilation à trois étages.',
        u'Test 6 — classes de validation 3, 4A et 4B'),
}


def charger(numero_test):
    u"""Loads the frozen network reference data.

    Args:
        numero_test: 5 or 6.

    Returns:
        dict: Reference data.

    Raises:
        IOError: If the reference data has not been frozen.
    """
    chemin = os.path.join(_REFS, 'test-%d.reseau.json' % numero_test)
    if not os.path.exists(chemin):
        raise IOError(
            u'référentiel absent : %s. Le produire par '
            u'`python scripts/build_reseau_ventilation_reference.py '
            u'--ecrire`.' % os.path.relpath(chemin, _RACINE))
    with io.open(chemin, encoding='utf-8') as flux:
        return json.load(flux)


def _valeur_lisible(champ):
    u"""Formats the value of a field.

    Args:
        champ: Entry from the reference data.

    Returns:
        str: Markdown cell. A field to be resolved NEVER shows a value:
        showing a dash would suggest zero, showing a value would suggest a
        confirmed reading.
    """
    if champ['statut'] == A_CONFIRMER:
        return u'**À TRANCHER**'
    valeur = champ['valeur']
    if isinstance(valeur, (list, tuple)):
        return u'**%s**' % u' – '.join(u'%s' % v for v in valeur)
    return u'**%s**' % valeur


def _tableau(bloc):
    u"""Table rows for a component section.

    Args:
        bloc: Sub-dictionary from the reference data.

    Returns:
        list[str]: Markdown rows.
    """
    lignes = [u'| Paramètre | Valeur | Source (section du PDF) |',
              u'|---|---|---|']
    for cle in sorted(bloc):
        champ = bloc[cle]
        if not isinstance(champ, dict) or 'statut' not in champ:
            continue
        lignes.append(u'| `%s` | %s | %s |'
                      % (cle, _valeur_lisible(champ), champ['source']))
    return lignes


def _tableau_courbes(courbes):
    u"""Table rows for the sliding setpoints.

    Args:
        courbes: `courbes` block from the reference data.

    Returns:
        list[str]: Markdown rows.
    """
    lignes = [u'| Consigne | Points (θ extérieure → consigne) | Lecture |',
              u'|---|---|---|']
    for cle in sorted(courbes):
        courbe = courbes[cle]
        if courbe['statut'] == A_CONFIRMER:
            lignes.append(u'| `%s` | **À TRANCHER** | relevé refusé |' % cle)
            continue
        points = u' ; '.join(u'%g °C → %g °C' % (x, y)
                             for x, y in courbe['points'])
        lignes.append(u'| `%s` | %s | étiquettes du graphique |' % (cle,
                                                                    points))
    return lignes


def _a_trancher(reference):
    u"""Collects everything the specification does not allow to resolve.

    Args:
        reference: Loaded reference data.

    Returns:
        list[tuple]: `(field path, source, reason)`.
    """
    trous = []
    for nom_bloc in sorted(reference):
        bloc = reference[nom_bloc]
        if nom_bloc.startswith('_') or not isinstance(bloc, dict):
            continue
        for cle in sorted(bloc):
            champ = bloc[cle]
            if not isinstance(champ, dict):
                continue
            if champ.get('statut') != A_CONFIRMER:
                continue
            trous.append((u'%s.%s' % (nom_bloc, cle),
                          champ.get('source') or u'—',
                          champ.get('a_confirmer') or u'—'))
    return trous


def construire(numero_test):
    u"""Writes the data entry sheet for one test.

    Args:
        numero_test: 5 or 6.

    Returns:
        str: Markdown document.
    """
    reference = charger(numero_test)
    portee, classes = PORTEE[numero_test]
    trous = _a_trancher(reference)
    compte = reference['_bilan']['effectifs']

    lignes = [
        u'# Fiche de saisie — réseau ApacheHVAC du Test SIA 4010 n° %d'
        % numero_test,
        u'',
        u'> **Document généré** par `scripts/build_fiche_apachehvac_56.py`, '
        u'depuis `refs/reference-data/test-%d.reseau.json` — lui-même extrait '
        u'de `%s`. Ne rien corriger ici : corriger l\'extracteur et '
        u'régénérer.' % (numero_test, reference['_source']),
        u'',
        u'> **%d paramètres relevés, %d lus sur un graphique, %d À TRANCHER '
        u'avant toute saisie.**' % (compte.get(RELEVE, 0),
                                    compte.get(SUR_GRAPHIQUE, 0),
                                    compte.get(A_CONFIRMER, 0)),
        u'',
        u'- Portée : %s' % portee,
        u'- Classes visées : %s' % classes,
        u'',
        u'## Pourquoi cette saisie est manuelle',
        u'',
        u'`HVACNetwork` n\'expose que `components`, `systems`, `controllers`, '
        u'`get_component_by_id`, `load_network` et `path` — **aucune méthode '
        u'de création**. Le réseau ne peut pas être construit par script. Une '
        u'fois saisi, le `.asp` se versionne et se recharge par '
        u'`load_network` ; tout le reste redevient scriptable.',
        u'',
        u'---',
        u'',
    ]

    if trous:
        lignes.extend([
            u'## ⚠ À trancher AVANT de saisir quoi que ce soit',
            u'',
            u'Ces %d points ne sont pas dans la couche texte du PDF. Les '
            u'combler au jugé produirait un réseau plausible et faux — le '
            u'genre d\'erreur qui ne se voit qu\'à la comparaison finale, '
            u'après une simulation annuelle.' % len(trous),
            u'',
            u'| Champ | Où regarder dans le PDF | Pourquoi il manque |',
            u'|---|---|---|',
        ])
        for chemin, source, raison in trous:
            lignes.append(u'| `%s` | %s | %s |' % (chemin, source, raison))
        lignes.append(u'')
        lignes.append(u'---')
        lignes.append(u'')

    lignes.append(u'## Composants')
    lignes.append(u'')
    for nom_bloc, titre, classe in BLOCS:
        bloc = reference.get(nom_bloc)
        if not bloc:
            continue
        lignes.append(u'### %s' % titre)
        lignes.append(u'')
        if classe:
            lignes.append(u'*Classe `iesve` attendue au relevé : `%s`*'
                          % classe)
            lignes.append(u'')
        lignes.extend(_tableau(bloc))
        lignes.append(u'')

    lignes.append(u'## Consignes glissantes')
    lignes.append(u'')
    lignes.append(u'Elles sont **dessinées** dans la spécification. Les points '
                  u'ci-dessous viennent des étiquettes de données du '
                  u'graphique. **Les paliers au-delà de ces points ne sont pas '
                  u'étiquetés** : le tracé les suggère constants, la '
                  u'spécification ne l\'écrit pas.')
    lignes.append(u'')
    lignes.extend(_tableau_courbes(reference['courbes']))
    lignes.append(u'')

    lignes.extend([
        u'## Après la saisie',
        u'',
        u'1. Enregistrer le réseau ; noter le chemin du `.asp` et le '
        u'versionner.',
        u'2. Lancer ApacheSim sur **l\'année complète** — un `.aps` partiel '
        u'rend toute somme annuelle inexploitable.',
        u'3. Lancer `Run_VE_SIA4010_Sonde_APS.py` et renvoyer '
        u'`outputs/sonde_aps.json`.',
        u'4. Le relevé donnera les noms de variables des batteries, du '
        u'récupérateur, des ventilateurs et de l\'humidificateur — les '
        u'liaisons encore manquantes du Test %d.' % numero_test,
        u'',
        u'## Ce que cette fiche ne dit pas',
        u'',
        u'- Elle ne déclare rien conforme. Elle décrit une SAISIE ; le verdict '
        u'vient de la comparaison aux valeurs de référence publiées.',
        u'- Les charges internes et l\'occupation renvoient à SIA 2024:2021, '
        u'absent du dépôt sous forme exploitable.',
        u'- Le climat SIA 2028 DRY Zürich-Kloten reste absent : sans lui, '
        u'aucune simulation de ce test n\'est un cas de validation SIA.',
        u'',
    ])
    return u'\n'.join(lignes) + u'\n'


def main(arguments=()):
    u"""Entry point.

    Args:
        arguments: `--ecrire` to write the sheets.

    Returns:
        int: 0 if both sheets were built successfully.
    """
    for numero in TESTS:
        try:
            document = construire(numero)
        except IOError as erreur:
            print(u'Test %d : %s' % (numero, erreur))
            return 1
        trous = len(_a_trancher(charger(numero)))
        print(u'Test %d : %d lignes, %d point(s) à trancher'
              % (numero, document.count(u'\n'), trous))
        if '--ecrire' in arguments:
            chemin = os.path.join(_DOCS,
                                  'FICHE-APACHEHVAC-TEST%d.md' % numero)
            with io.open(chemin, 'w', encoding='utf-8') as flux:
                flux.write(document)
            print(u'    écrit : %s' % os.path.relpath(chemin, _RACINE))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
