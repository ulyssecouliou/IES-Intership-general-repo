# -*- coding: utf-8 -*-
u"""Frequency distribution criterion for SIA 4010 tests.

The specifications of these three tests state **two** criteria. The first --
the annual sum within the band -- is handled by `sia_bandes_engine`. The
second is this one:

    "Die Häufigkeitsverteilung muss im Streubereich der Referenzprogramme
      liegen."   (Spezifikation_Test2/3/5.pdf, section Testkriterien)

A written clarification from Prof. Gerhard Zweifel, received on 2026-08-10,
confirms that `Streubereich` means the **min/max envelope of the reference
programs, class by class**. The mean +/- max-deviation band is still computed
only for comparison with older audits; it no longer decides the verdict.
The authority also confirmed that class totals below 8 760 do not indicate
incomplete series: some hourly values fall outside the defined bounds.
They are counted separately and are never silently absorbed by the last class.

Pure Python: no `iesve` import, testable in continuous integration.
"""

from __future__ import print_function

import io
import json
import os

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
_DOSSIER_REFERENCES = os.path.join(_RACINE, 'refs', 'reference-data')

#: JSON references currently built. The workbooks of Tests 4 and 6
#: also contain classes and distributions; their exact scope as an
#: acceptance gate remains to be confirmed before adding them to this executable list.
TESTS_SUPPORTES = (2, 3, 5)

#: Criterion status. Weaker than `INFERE` from the annual sums: there, a
#: formula existed in the workbook and could be recovered. Here, there is
#: none.
STATUT_CRITERE = 'CONFIRME_AUTORITE_2026-08-10'

JUSTIFICATION_CRITERE = (
    u'Clarification écrite reçue le 2026-08-10 : enveloppe minimum/maximum '
    u'des programmes de référence pour chaque classe de fréquence.'
)

#: Both possible readings of the `Streubereich`, computed together.
LECTURE_ENVELOPPE = 'enveloppe_min_max'
LECTURE_BANDE = 'moyenne_plus_ecart_max'
LECTURES = (LECTURE_ENVELOPPE, LECTURE_BANDE)

VERDICT_NON_ETABLI = 'NON_ETABLI'
VERDICT_NON_EVALUABLE = 'NOT_CHECKABLE'
VERDICT_PASS = 'PASS'
VERDICT_FAIL = 'FAIL'

class ReferenceIntrouvable(IOError):
    u"""Raised when the distribution reference for a test is missing."""


def chemin_reference(numero_test):
    u"""Path of the distribution reference for a test.

    Args:
        numero_test: SIA test number.

    Returns:
        str: Absolute path.
    """
    return os.path.join(_DOSSIER_REFERENCES,
                        'test-%d.distributions.ref.json' % numero_test)


def charger_reference(numero_test, chemin=None):
    u"""Load the distribution reference for a test.

    Args:
        numero_test: SIA test number.
        chemin: Explicit path, otherwise the frozen location.

    Returns:
        dict: Reference data.

    Raises:
        ValueError: If the test has no distribution criterion.
        ReferenceIntrouvable: If the file is missing.
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
    u"""Distribute an hourly series into the workbook's classes.

    The bounds are UPPER bounds. Values exceeding the last one remain
    outside the displayed classes; use
    :func:`classer_avec_hors_classes` to obtain their audit count.

    Args:
        serie: Hourly values; non-numeric values are excluded.
        bornes: Upper bounds, in ascending order.

    Returns:
        list[int]: Class count, same length as `bornes`.

    Raises:
        ValueError: If bounds are empty or unordered -- in which case any
            classification would be arbitrary.
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
    u"""Classify values and audit those above the last bound.

    The 2026-08-10 authority response confirms that these values explain the
    displayed totals below 8 760. They are neither missing nor silently
    absorbed by the last class.
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
    u"""Counts of the reference programs for a class.

    Args:
        bloc: Distribution block.
        classe: Class count entry.

    Returns:
        list[int]: Counts, with unfilled columns excluded.
    """
    valeurs = []
    for contributeur in bloc['contributeurs']:
        valeur = classe['par_colonne'].get(contributeur['colonne'])
        if valeur is not None:
            valeurs.append(valeur)
    return valeurs


def bornes_des_lectures(effectifs):
    u"""Compute the two readings of the `Streubereich` for a class.

    Args:
        effectifs: Counts of the reference programs.

    Returns:
        dict: `{reading: (lower, upper)}`, empty if no counts.
    """
    if not effectifs:
        return {}
    moyenne = float(sum(effectifs)) / len(effectifs)
    ecart_max = max(abs(v - moyenne) for v in effectifs)
    return {
        # A count cannot be negative: the floor at zero is a
        # property of the quantity, not of the criterion.
        LECTURE_ENVELOPPE: (float(min(effectifs)), float(max(effectifs))),
        LECTURE_BANDE: (max(0.0, moyenne - ecart_max), moyenne + ecart_max),
    }


def evaluer_bloc(bloc, effectifs_candidats=None):
    u"""Compare a candidate distribution against those of the programs.

    Args:
        bloc: Distribution block from the reference data.
        effectifs_candidats: Per-class count produced by VE, or `None`.

    Returns:
        dict: Result, never `None`. The min/max envelope is binding.
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
                # Bounds INCLUSIVE, as for annual sums.
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
    u"""Evaluate all distributions for a test.

    Args:
        reference: Loaded reference data.
        candidat: `{(cas, grandeur): [counts per class]}`, or `None`.
            A missing key leaves the distribution NOT EVALUABLE -- never
            conformant, never failing.

    Returns:
        dict: Overall result.
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
    u"""Render the result in a human-readable console format.

    Args:
        resultat: Output of `evaluer`.

    Returns:
        str: Text table.
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
