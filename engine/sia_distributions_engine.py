# -*- coding: utf-8 -*-
u"""Critère de distribution de fréquence des tests SIA 4010.

Les spécifications de ces trois tests énoncent **deux** critères. Le premier —
la somme annuelle dans la bande — est traité par `sia_bandes_engine`. Le
second est celui-ci :

    « Die Häufigkeitsverteilung muss im Streubereich der Referenzprogramme
      liegen. »   (Spezifikation_Test2/3/5.pdf, section Testkriterien)

Une clarification écrite de Prof. Gerhard Zweifel, reçue le 2026-08-10,
confirme que `Streubereich` signifie l'**enveloppe min/max des programmes de
référence, classe par classe**. La bande moyenne ± écart maximal reste calculée
uniquement pour la comparaison avec les anciens audits ; elle ne décide plus le
verdict. L'autorité a aussi confirmé que les totaux de classes inférieurs à
8 760 ne signalent pas des séries incomplètes : certaines valeurs horaires sont
hors des bornes définies. Elles sont comptées séparément et ne sont jamais
absorbées silencieusement par la dernière classe.

Python pur : aucun import `iesve`, testable en intégration continue.
"""

from __future__ import print_function

import io
import json
import os

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
_DOSSIER_REFERENCES = os.path.join(_RACINE, 'refs', 'reference-data')

#: Référentiels JSON actuellement construits. Les classeurs des Tests 4 et 6
#: contiennent eux aussi des classes et distributions ; leur portée exacte comme
#: gate d'acceptation reste à confirmer avant ajout à cette liste exécutable.
TESTS_SUPPORTES = (2, 3, 5)

#: Statut du critère. Plus faible qu'`INFERE` des sommes annuelles : là, une
#: formule existait dans le classeur et se laissait retrouver. Ici, il n'y en a
#: aucune.
STATUT_CRITERE = 'CONFIRME_AUTORITE_2026-08-10'

JUSTIFICATION_CRITERE = (
    u'Clarification écrite reçue le 2026-08-10 : enveloppe minimum/maximum '
    u'des programmes de référence pour chaque classe de fréquence.'
)

#: Lectures possibles du `Streubereich`, calculées toutes les deux.
LECTURE_ENVELOPPE = 'enveloppe_min_max'
LECTURE_BANDE = 'moyenne_plus_ecart_max'
LECTURES = (LECTURE_ENVELOPPE, LECTURE_BANDE)

VERDICT_NON_ETABLI = 'NON_ETABLI'
VERDICT_NON_EVALUABLE = 'NOT_CHECKABLE'
VERDICT_PASS = 'PASS'
VERDICT_FAIL = 'FAIL'

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
            u'avec référentiel exécutable : %s. Les classeurs des Tests 4 et 6 '
            u'ont des distributions, mais leur gate exact reste en revue.'
            % (numero_test, list(TESTS_SUPPORTES)))
    chemin = chemin or chemin_reference(numero_test)
    if not os.path.exists(chemin):
        raise ReferenceIntrouvable(
            u'référentiel absent : %s. Le produire avec '
            u'scripts/build_sia_distribution_reference.py' % chemin)
    with io.open(chemin, encoding='utf-8') as flux:
        return json.load(flux)


# Authority clarification 2026-08-10: the workbook's displayed classes do not
# include values above the last declared boundary. Such values are not missing
# hours; classer_avec_hors_classes reports them separately for audit.
def classer(serie, bornes):
    u"""Répartit une série horaire dans les classes du classeur.

    Les bornes sont des bornes SUPÉRIEURES. Les valeurs qui dépassent la
    dernière restent hors des classes affichées ; utiliser
    :func:`classer_avec_hors_classes` pour obtenir leur compte d'audit.

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
        place = None
        for rang, borne in enumerate(bornes):
            if valeur <= borne:
                place = rang
                break
        if place is not None:
            effectifs[place] += 1
    return effectifs


def classer_avec_hors_classes(serie, bornes):
    u"""Classe les valeurs et audite celles au-dessus de la derniere borne.

    La reponse d'autorite du 2026-08-10 confirme que ces valeurs expliquent les
    totaux affiches inferieurs a 8 760. Elles ne sont ni manquantes, ni absorbees
    silencieusement par la derniere classe.
    """
    effectifs = classer(serie, bornes)
    numeriques = [
        valeur for valeur in (serie or [])
        if isinstance(valeur, (int, float)) and not isinstance(valeur, bool)
    ]
    return {
        'effectifs': effectifs,
        'hors_classes_superieur': len(numeriques) - sum(effectifs),
        'total_numerique': len(numeriques),
    }


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
        dict: Résultat, jamais `None`. L'enveloppe min/max est contraignante.
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

    if effectifs_candidats is None or evaluables != len(classes):
        verdict = VERDICT_NON_EVALUABLE
    elif hors[LECTURE_ENVELOPPE]:
        verdict = VERDICT_FAIL
    else:
        verdict = VERDICT_PASS

    return {
        'cas': bloc['cas'],
        'grandeur': bloc['grandeur'],
        'unite': bloc['unite'],
        'colonne_bloc': bloc['colonne_bloc'],
        'nb_classes': len(classes),
        'nb_classes_evaluees': evaluables,
        'nb_hors_lecture': dict(hors),
        # Historical field retained for report compatibility. The authority
        # confirmed that short displayed totals are not partial source series.
        'contributeurs_partiels': [],
        'contributeurs_hors_classes': [
            {
                'colonne': c['colonne'],
                'heures_hors_classes': c.get(
                    'heures_hors_classes',
                    max(0, 8760 - c['total_heures']),
                ),
            }
            for c in bloc['contributeurs']
            if c.get('heures_hors_classes', max(0, 8760 - c['total_heures']))
        ],
        'total_candidat': (sum(effectifs_candidats)
                           if effectifs_candidats is not None else None),
        'classes': classes,
        'verdict': verdict,
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
    if any(r['verdict'] == VERDICT_FAIL for r in resultats):
        verdict_global = VERDICT_FAIL
    elif any(r['verdict'] == VERDICT_NON_EVALUABLE for r in resultats):
        verdict_global = VERDICT_NON_EVALUABLE
    else:
        verdict_global = VERDICT_PASS
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
        'verdict': verdict_global,
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
        u'Verdict : %s — critère min/max confirmé par clarification écrite.'
        % resultat['verdict'],
    ])
    return u'\n'.join(lignes)
