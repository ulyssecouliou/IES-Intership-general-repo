# -*- coding: utf-8 -*-
u"""Génère les fiches de saisie ApacheHVAC des tests SIA 5 et 6.

MÊME RAISON QUE POUR LE TEST 4. `HVACNetwork` n'expose aucune méthode de
création : le réseau se saisit à la main, une fois, dans l'éditeur
ApacheHVAC. Ensuite le `.asp` se versionne et se recharge par `load_network`.

CE QUI CHANGE ICI. La fiche du Test 4 est tirée d'un module Python où les
paramètres avaient été relevés un par un. Celles-ci sont tirées de
`refs/reference-data/test-{5,6}.reseau.json`, produits par un extracteur qui
lit le PDF — donc **les trous de la spécification remontent jusqu'à la
fiche**, nommés, en tête, au lieu d'être comblés en silence.

C'est le point important : sur le Test 5, cinq paramètres dépendent de la
variante (5A à 5D) et le tableau du PDF porte quatre colonnes pour deux
cellules. Une fiche qui trancherait ferait construire deux variantes fausses
sur quatre, sans que rien ne le signale avant la comparaison finale.

Usage :
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

#: Blocs de la fiche, dans l'ordre du flux d'air, avec la classe `iesve`
#: attendue au relevé. Le nom de classe sert à CONFRONTER le réseau saisi à
#: cette fiche après coup, par `HVACNetwork.components` — ce n'est pas un nom
#: d'objet à saisir.
BLOCS = [
    ('reseau', u'Réseau et conditions générales', None),
    ('ventilateurs', u'Ventilateurs', 'HVACFan'),
    ('recuperateur', u'Récupérateur de chaleur',
     'HVACAirToAirHeatEnthalpyExchanger'),
    ('batterie_chaude', u'Batterie chaude', 'HVACHeatingCoil'),
    ('batterie_froide', u'Batterie froide', 'HVACCoolingCoil'),
    ('humidificateur', u'Humidificateur', None),
]

#: Ce que chaque fiche sert à débloquer, et ce qu'elle ne débloque pas.
PORTEE = {
    5: (u'Quatre variantes (5A à 5D) : type de récupérateur, taux d\'échange, '
        u'part de pression constante et type d\'humidificateur en dépendent.',
        u'Test 5 — classes de validation 2B, 4A et 4B'),
    6: (u'Une seule configuration : récupération par boucle à eau glycolée '
        u'(« Kreislaufverbund »), ventilation à trois étages.',
        u'Test 6 — classes de validation 3, 4A et 4B'),
}


def charger(numero_test):
    u"""Charge le référentiel de réseau figé.

    Args:
        numero_test: 5 ou 6.

    Returns:
        dict: Référentiel.

    Raises:
        IOError: Si le référentiel n'a pas été figé.
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
    u"""Met en forme la valeur d'un champ.

    Args:
        champ: Entrée du référentiel.

    Returns:
        str: Cellule Markdown. Un champ à confirmer n'affiche JAMAIS de
        valeur : afficher un tiret laisserait croire à un zéro, afficher une
        valeur laisserait croire à un relevé.
    """
    if champ['statut'] == A_CONFIRMER:
        return u'**À TRANCHER**'
    valeur = champ['valeur']
    if isinstance(valeur, (list, tuple)):
        return u'**%s**' % u' – '.join(u'%s' % v for v in valeur)
    return u'**%s**' % valeur


def _tableau(bloc):
    u"""Lignes du tableau d'un bloc de composants.

    Args:
        bloc: Sous-dictionnaire du référentiel.

    Returns:
        list[str]: Lignes Markdown.
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
    u"""Lignes du tableau des consignes glissantes.

    Args:
        courbes: Bloc `courbes` du référentiel.

    Returns:
        list[str]: Lignes Markdown.
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
    u"""Rassemble tout ce que la spécification ne permet pas de trancher.

    Args:
        reference: Référentiel chargé.

    Returns:
        list[tuple]: `(chemin du champ, source, raison)`.
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
    u"""Rédige la fiche d'un test.

    Args:
        numero_test: 5 ou 6.

    Returns:
        str: Document Markdown.
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
    u"""Point d'entrée.

    Args:
        arguments: `--ecrire` pour écrire les fiches.

    Returns:
        int: 0 si les deux fiches ont pu être construites.
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
