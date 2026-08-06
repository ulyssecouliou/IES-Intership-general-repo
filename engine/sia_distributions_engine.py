# -*- coding: utf-8 -*-
u"""Second critère des tests SIA 2, 3 et 5 : la distribution de fréquence.

Les spécifications de ces trois tests énoncent **deux** critères. Le premier —
la somme annuelle dans la bande — est traité par `sia_bandes_engine`. Le
second est celui-ci :

    « Die Häufigkeitsverteilung muss im Streubereich der Referenzprogramme
      liegen. »   (Spezifikation_Test2/3/5.pdf, section Testkriterien)

CE QUE CE MODULE NE FAIT PAS, ET POURQUOI. Il ne rend **jamais** de verdict
conforme. Les feuilles « Verteilung » des classeurs officiels sont des
graphiques : elles tracent les courbes des programmes de référence et celle du
programme testé, et **aucune cellule ne calcule de bande**. Le classeur laisse
donc le jugement à l'œil.

Deux lectures du mot `Streubereich` restent défendables :

  * l'**enveloppe** min/max des programmes de référence, classe par classe ;
  * la bande **moyenne ± écart maximal**, qui est la formule que le même
    classeur applique aux sommes annuelles (établie et vérifiée 26/26 lors de
    l'audit du Test 1).

Les deux sont calculées et rapportées séparément. Trancher entre elles ici
reviendrait à inventer le critère — exactement ce que la règle 1 interdit. Le
verdict d'ensemble reste `NON_ETABLI` tant que la sous-commission SIA n'a pas
répondu, quelle que soit la qualité du candidat.

Python pur : aucun import `iesve`, testable en intégration continue.
"""

from __future__ import print_function

import io
import json
import os

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
_DOSSIER_REFERENCES = os.path.join(_RACINE, 'refs', 'reference-data')

#: Tests dont la spécification énonce le critère de distribution. Les tests 4
#: et 6 n'ont ni classes de fréquence ni feuille de distribution, et leurs
#: spécifications ne comportent aucune section « Testkriterien » : pour eux, la
#: somme annuelle est le seul critère. C'est un constat, pas une lacune.
TESTS_SUPPORTES = (2, 3, 5)

#: Statut du critère. Plus faible qu'`INFERE` des sommes annuelles : là, une
#: formule existait dans le classeur et se laissait retrouver. Ici, il n'y en a
#: aucune.
STATUT_CRITERE = 'NON_ETABLI'

JUSTIFICATION_CRITERE = (
    u'Les feuilles « Verteilung » sont des graphiques. Aucune cellule des '
    u'classeurs officiels ne définit la bande d\'une distribution : le '
    u'classeur laisse le jugement visuel. Ce module calcule les deux lectures '
    u'défendables et ne conclut pas.'
)

#: Lectures possibles du `Streubereich`, calculées toutes les deux.
LECTURE_ENVELOPPE = 'enveloppe_min_max'
LECTURE_BANDE = 'moyenne_plus_ecart_max'
LECTURES = (LECTURE_ENVELOPPE, LECTURE_BANDE)

VERDICT_NON_ETABLI = 'NON_ETABLI'
VERDICT_NON_EVALUABLE = 'NOT_CHECKABLE'

#: Sous ce nombre d'heures totalisées, un contributeur n'est pas comparable aux
#: autres : il ne couvre pas la même période. Le seuil est celui qu'emploie
#: l'extracteur pour lever une réserve.
SEUIL_CONTRIBUTEUR_PARTIEL = 8760 // 2


class ReferenceIntrouvable(IOError):
    u"""Levée quand le référentiel de distributions d'un test manque."""


def chemin_reference(numero_test):
    u"""Chemin du référentiel de distributions d'un test.

    Args:
        numero_test: Numéro du test SIA.

    Returns:
        str: Chemin absolu.
    """
    return os.path.join(_DOSSIER_REFERENCES,
                        'test-%d.distributions.ref.json' % numero_test)


def charger_reference(numero_test, chemin=None):
    u"""Charge le référentiel de distributions d'un test.

    Args:
        numero_test: Numéro du test SIA.
        chemin: Chemin explicite, sinon l'emplacement figé.

    Returns:
        dict: Référentiel.

    Raises:
        ValueError: Si le test n'a pas de critère de distribution.
        ReferenceIntrouvable: Si le fichier manque.
    """
    if numero_test not in TESTS_SUPPORTES:
        raise ValueError(
            u'le test %r n\'a pas de critère de distribution. Tests '
            u'concernés : %s. Les tests 4 et 6 n\'en ont pas : leurs '
            u'spécifications ne fixent aucun Testkriterium et leurs classeurs '
            u'n\'ont pas de classes de fréquence.'
            % (numero_test, list(TESTS_SUPPORTES)))
    chemin = chemin or chemin_reference(numero_test)
    if not os.path.exists(chemin):
        raise ReferenceIntrouvable(
            u'référentiel absent : %s. Le produire avec '
            u'scripts/build_sia_distribution_reference.py' % chemin)
    with io.open(chemin, encoding='utf-8') as flux:
        return json.load(flux)


def classer(serie, bornes):
    u"""Répartit une série horaire dans les classes du classeur.

    Les bornes sont des bornes SUPÉRIEURES, la dernière absorbant tout ce qui
    la dépasse — sans quoi des heures disparaîtraient du total, et le contrôle
    de réconciliation deviendrait impossible à interpréter.

    Args:
        serie: Valeurs horaires ; les non-numériques sont écartées.
        bornes: Bornes supérieures, croissantes.

    Returns:
        list[int]: Effectif par classe, de même longueur que `bornes`.

    Raises:
        ValueError: Si les bornes sont vides ou désordonnées — auquel cas tout
            classement serait arbitraire.
    """
    if not bornes:
        raise ValueError(u'aucune borne de classe fournie')
    if list(bornes) != sorted(bornes):
        raise ValueError(u'bornes non croissantes : %r' % (bornes,))

    effectifs = [0] * len(bornes)
    for valeur in (serie or []):
        if not isinstance(valeur, (int, float)) or isinstance(valeur, bool):
            continue
        place = len(bornes) - 1
        for rang, borne in enumerate(bornes):
            if valeur <= borne:
                place = rang
                break
        effectifs[place] += 1
    return effectifs


def _effectifs_contributeurs(bloc, classe):
    u"""Effectifs des programmes de référence pour une classe.

    Args:
        bloc: Bloc de distribution.
        classe: Entrée d'effectifs d'une classe.

    Returns:
        list[int]: Effectifs, les colonnes non renseignées écartées.
    """
    valeurs = []
    for contributeur in bloc['contributeurs']:
        valeur = classe['par_colonne'].get(contributeur['colonne'])
        if valeur is not None:
            valeurs.append(valeur)
    return valeurs


def bornes_des_lectures(effectifs):
    u"""Calcule les deux lectures du `Streubereich` pour une classe.

    Args:
        effectifs: Effectifs des programmes de référence.

    Returns:
        dict: `{lecture: (basse, haute)}`, vide si aucun effectif.
    """
    if not effectifs:
        return {}
    moyenne = float(sum(effectifs)) / len(effectifs)
    ecart_max = max(abs(v - moyenne) for v in effectifs)
    return {
        # Un effectif ne peut pas être négatif : le plancher à zéro est une
        # propriété de la grandeur, pas du critère.
        LECTURE_ENVELOPPE: (float(min(effectifs)), float(max(effectifs))),
        LECTURE_BANDE: (max(0.0, moyenne - ecart_max), moyenne + ecart_max),
    }


def evaluer_bloc(bloc, effectifs_candidats=None):
    u"""Confronte une distribution candidate à celles des programmes.

    Args:
        bloc: Bloc de distribution du référentiel.
        effectifs_candidats: Effectif par classe produit par VE, ou `None`.

    Returns:
        dict: Résultat, jamais `None`. Le verdict reste `NON_ETABLI` même
            quand toutes les classes tombent dans les deux lectures : ce
            module ne tranche pas ce que la norme n'a pas tranché.
    """
    classes = []
    hors = dict((lecture, 0) for lecture in LECTURES)
    evaluables = 0

    for rang, entree in enumerate(bloc['effectifs']):
        contributions = _effectifs_contributeurs(bloc, entree)
        lectures = bornes_des_lectures(contributions)
        candidat = None
        if effectifs_candidats is not None and rang < len(effectifs_candidats):
            candidat = effectifs_candidats[rang]

        dedans = {}
        for lecture, (basse, haute) in lectures.items():
            if candidat is None:
                dedans[lecture] = None
            else:
                # Bornes INCLUSES, comme pour les sommes annuelles.
                dedans[lecture] = basse <= candidat <= haute
                if not dedans[lecture]:
                    hors[lecture] += 1
        if candidat is not None and lectures:
            evaluables += 1

        classes.append({
            'borne_superieure': entree['borne_superieure'],
            'ligne_classeur': entree['ligne_classeur'],
            'candidat': candidat,
            'contributions': contributions,
            'lectures': dict((nom, list(bornes))
                             for nom, bornes in lectures.items()),
            'dans_la_lecture': dedans,
        })

    return {
        'cas': bloc['cas'],
        'grandeur': bloc['grandeur'],
        'unite': bloc['unite'],
        'colonne_bloc': bloc['colonne_bloc'],
        'nb_classes': len(classes),
        'nb_classes_evaluees': evaluables,
        'nb_hors_lecture': dict(hors),
        'contributeurs_partiels': [
            c['colonne'] for c in bloc['contributeurs']
            if c['total_heures'] < SEUIL_CONTRIBUTEUR_PARTIEL],
        'total_candidat': (sum(effectifs_candidats)
                           if effectifs_candidats is not None else None),
        'classes': classes,
        'verdict': (VERDICT_NON_EVALUABLE if effectifs_candidats is None
                    else VERDICT_NON_ETABLI),
    }


def evaluer(reference, candidat=None):
    u"""Évalue toutes les distributions d'un test.

    Args:
        reference: Référentiel chargé.
        candidat: `{(cas, grandeur): [effectifs par classe]}`, ou `None`.
            Une clé absente laisse la distribution NON ÉVALUABLE — jamais
            conforme, jamais en échec.

    Returns:
        dict: Résultat d'ensemble.
    """
    index = dict(candidat or {})
    resultats, ignorees = [], []
    utilisees = set()

    for bloc in reference['distributions']:
        cle = (bloc['cas'], bloc['grandeur'])
        effectifs = index.get(cle)
        if effectifs is not None:
            utilisees.add(cle)
        resultats.append(evaluer_bloc(bloc, effectifs))

    for cle in index:
        if cle not in utilisees:
            ignorees.append(list(cle))

    evalues = [r for r in resultats if r['verdict'] != VERDICT_NON_EVALUABLE]
    return {
        'test': reference['test'],
        'classes_concernees': list(reference.get('classes_concernees', [])),
        'critere': {
            'statut': STATUT_CRITERE,
            'justification': JUSTIFICATION_CRITERE,
            'enonce': reference['critere'],
        },
        'nb_distributions': len(resultats),
        'nb_evaluees': len(evalues),
        'nb_non_evaluables': len(resultats) - len(evalues),
        'cles_candidat_ignorees': sorted(ignorees),
        'distributions': resultats,
        # Jamais PASS : la bande n'est pas etablie. Un outil qui conclurait ici
        # transformerait une preuve manquante en conformite.
        'verdict': VERDICT_NON_ETABLI,
    }


def resumer(resultat):
    u"""Rend le résultat lisible en console.

    Args:
        resultat: Ce que rend `evaluer`.

    Returns:
        str: Tableau texte.
    """
    lignes = [u'Test %d — distributions de fréquence' % resultat['test'],
              u'critère : %s' % resultat['critere']['statut'], u'']
    for bloc in resultat['distributions']:
        if bloc['verdict'] == VERDICT_NON_EVALUABLE:
            etat = u'non evaluable'
        else:
            etat = u', '.join(
                u'%s: %d/%d hors' % (lecture, bloc['nb_hors_lecture'][lecture],
                                     bloc['nb_classes_evaluees'])
                for lecture in LECTURES)
        lignes.append(u'  %-12s %-38s %s'
                      % (bloc['cas'] or u'(sans cas)',
                         (bloc['grandeur'] or u'')[:38], etat))
    lignes.extend([
        u'',
        u'%d/%d distributions evaluees.'
        % (resultat['nb_evaluees'], resultat['nb_distributions']),
        u'Verdict : %s — aucune bande n est definie par le classeur officiel.'
        % resultat['verdict'],
    ])
    return u'\n'.join(lignes)
