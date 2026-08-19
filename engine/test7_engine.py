# -*- coding: utf-8 -*-
"""SIA 4010 validation engine -- Test 7 (heat and cold generation, storage,
distribution and PV, driven by given load profiles).

Test 7 is the ONLY test required by validation class 5 (SIA 4010:2023,
table 63). It needs no building thermal model, no usage data and no glazing:
the load profiles are supplied by the SIA in `Lastverlaeufe_220607.xlsx`.

WHERE THE CRITERION COMES FROM -- and why it is marked as inferred.

`Spezifikation_Test7.pdf` states NO acceptance criterion. Searched for
`kriterium|kriterien|streubereich|abweichung|toleranz`: zero hits, unlike
Test 1 which spells its criteria out. SIA 4010:2023 defines no generic numeric
criterion either; its clause 4.4 delegates the comparison to the evaluation
workbook:

    "Pour chaque test, un fichier d'evaluation EXCEL est disponible [...] dans
     lequel les resultats peuvent etre transferes et qui genere la
     representation comparative des resultats avec les resultats de reference."

So the workbook IS the criterion. For Test 7 that delegation is backed by direct
material evidence rather than analogy -- the bands exist exactly where the
criterion must bite:

    rows 8-12, 14-18, 20  Testgroessen   -> L/M/N carry mean / upper / lower
    rows 21-26            Diagnosegroessen -> L/M/N EMPTY

The original workbook's conditional-formatting rule compared mean-to-upper
instead of lower-to-upper. Prof. Gerhard Zweifel confirmed the mistake and sent
a corrected workbook on 2026-08-10. Direct XML inspection verified that the
rule now uses lower-to-upper (``$N8`` to ``$M8``) over the same Testgroessen
range; its SHA-256 is pinned in the traceability record.

CONTRIBUTING SET. It varies per quantity -- GHJ, GHIJ, GHI across the eleven
bands. A program that did not deliver a quantity drops out and is never counted
as zero. The authoritative set is the one listed in the workbook's own
`MAX(ABS(...))` formula, frozen per quantity by
`scripts/build_test7_reference.py`.

WHAT THIS ENGINE CANNOT YET DECIDE. Quantity "PV-Ertrag" is a Testgroesse and
carries a band, so it is mandatory. Producing it requires solar irradiance on
the module plane, which no official source in our possession provides. Its
candidate value will therefore be absent and the engine returns NOT_CHECKABLE
for it -- never a pass by default. See
`traceability/classes-de-validation.spec.md`.

Pure Python, no dependencies, no `import iesve`: testable in CI without a VE
licence and runnable as-is inside VEScripts.
"""

import io
import json
import os

from engine import scatter_band


_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
CHEMIN_REFERENCE_DEFAUT = os.path.join(
    _RACINE, 'refs', 'reference-data', 'test-7.ref.json')

# SIA 4010:2023, tableau 63 -- classes that REQUIRE Test 7:
#   4A: tests 1, 2A, 3A to F, 4 to 7
#   4B: tests 1 to 7
#   5 : test 7 ONLY
# Class 5 is the only one for which Test 7 alone is sufficient; for 4A and 4B
# it is just one test among others. Omitting 4A/4B would understate the impact
# of a Test 7 failure in the navigator.
CLASSES_CONCERNEES = ('4A', '4B', '5')

# The only class for which Test 7 alone constitutes validation.
CLASSE_SATISFAITE_PAR_CE_SEUL_TEST = '5'

# Diagnosegroessen carry no band in the workbook: they are
# reported for information only and never enter the verdict.
GROUPE_AVEC_CRITERE = u'Testgr\xf6ssen'

TOLERANCE_DEFAUT = 1e-6

# IRRADIANCE LOCK -- added 2026-08-06 after independent audit.
#
# The audit established that no lock existed: supplying a value for
# `PV-Ertrag` was sufficient to obtain PASS and `classe_5_validee = True`. Yet
# computing PV requires irradiance on the module plane, which NO official
# source in our possession provides (cf.
# `traceability/classes-de-validation.spec.md`). The dangerous scenario is
# concrete: an adapter computing PV against a substitute climate --
# CH2018 2035, a neighbouring station -- would produce a plausible number
# that nothing would flag.
#
# The lock does not forbid the value: it requires the caller to DECLARE where
# their irradiance comes from. A hard block would be wrong the day we have
# the data; a mandatory declaration remains correct in both cases, and
# the declared source propagates into all reports.
GRANDEURS_EXIGEANT_IRRADIANCE = ('PV-Ertrag',)

MOTIF_VERROU_IRRADIANCE = (
    "Valeur refusee : le calcul de cette grandeur exige l'irradiance solaire "
    "sur le plan des modules, qu'aucune source officielle ne fournit a ce "
    "jour. Pour la soumettre malgre tout, passer `source_irradiance=` a "
    "`evaluer_test7()` en decrivant precisement l'origine de l'irradiance ; "
    "cette declaration sera reproduite dans tous les rapports.")

STATUT_CRITERE = 'CLASSEUR_CORRIGE_VERIFIE_2026-08-10'
JUSTIFICATION_CRITERE = (
    "La specification du Test 7 ne definit aucun critere ; SIA 4010:2023 "
    "clause 4.4 delegue la comparaison au classeur d'evaluation, qui porte des "
    "bandes sur les seules Testgroessen. Le classeur corrige recu le "
    "2026-08-10 a ete controle par checksum et lecture XML : la mise en forme "
    "conditionnelle compare bien la borne basse a la borne haute. Cette "
    "evaluation logicielle ne remplace pas l'attestation de la sous-commission.")

# The active criterion comes from the corrected workbook (STATUT_CRITERE), verified by
# checksum and XML inspection, but NEVER confirmed by the SIA sub-commission
# (art. 4.6.2). While this flag remains False, a "validated class 5" from this
# engine is a SOFTWARE conformity, not an official validation. When the
# sub-commission confirms the criterion, setting this flag to True (and updating
# STATUT_CRITERE) is sufficient to lift the reservation in all reports.
CRITERE_ATTESTE_PAR_SOUS_COMMISSION = False


def charger_reference(chemin=None):
    """Load the frozen reference data for Test 7."""
    chemin = chemin or CHEMIN_REFERENCE_DEFAUT
    with io.open(chemin, encoding='utf-8') as flux:
        return json.load(flux)


def valeurs_contributrices(grandeur):
    """Values of the contributing programs only, in workbook order.

    A program absent from `contributeurs_noms` is EXCLUDED, not set to zero:
    counting it as zero would shift the mean and therefore the dispersion band.
    """
    par_programme = grandeur['par_programme']
    valeurs = []
    for nom in grandeur['contributeurs_noms']:
        valeur = par_programme.get(nom)
        if valeur is not None:
            valeurs.append(float(valeur))
    return valeurs


def exige_irradiance(grandeur):
    """Does this quantity require solar irradiance to be computed?"""
    return grandeur['libelle_de'].strip() in GRANDEURS_EXIGEANT_IRRADIANCE


def evaluer_grandeur(grandeur, valeur_candidate, tolerance=TOLERANCE_DEFAUT,
                     source_irradiance=None):
    """Verdict for a quantity: does the candidate fall inside the dispersion band?

    The `critere_statut` field retains the identity of the corrected source used
    and allows the report to distinguish software evaluation from the attestation
    issued by the sub-commission.

    `source_irradiance`: description of the irradiance origin, mandatory to
    submit a quantity from `GRANDEURS_EXIGEANT_IRRADIANCE`. Without it,
    the value is REFUSED and the quantity remains non-evaluable -- never a
    pass obtained on a silently substituted irradiance.
    """
    verrou = None
    if (valeur_candidate is not None and exige_irradiance(grandeur)
            and not source_irradiance):
        verrou = MOTIF_VERROU_IRRADIANCE
        valeur_candidate = None

    contributions = valeurs_contributrices(grandeur)
    statut = scatter_band.verdict(
        valeur_candidate, contributions,
        floor_at_zero=grandeur['plancher_a_zero'], tolerance=tolerance)

    ecart = None
    if valeur_candidate is not None and grandeur['moyenne'] is not None:
        ecart = float(valeur_candidate) - grandeur['moyenne']

    return {
        'libelle': grandeur['libelle_de'],
        'groupe': grandeur['groupe'],
        'unite': grandeur['unite'],
        'ligne_classeur': grandeur['ligne_classeur'],
        'candidat': valeur_candidate,
        'moyenne': grandeur['moyenne'],
        'borne_basse': grandeur['borne_basse'],
        'borne_haute': grandeur['borne_haute'],
        'plancher_a_zero': grandeur['plancher_a_zero'],
        'contributeurs': grandeur['contributeurs_noms'],
        'ecart_a_la_moyenne': ecart,
        'statut': statut,
        'conforme': (True if scatter_band.is_passing(statut)
                     else (False if statut == scatter_band.VERDICT_FAIL
                           else None)),
        # Criterion status recalled on EVERY row: `evaluer_grandeur` is
        # public and may be called without going through `evaluer_test7`.
        'critere_statut': STATUT_CRITERE,
        'exige_irradiance': exige_irradiance(grandeur),
        'source_irradiance': source_irradiance,
        # Non-`None` when a value was REFUSED due to missing declared origin:
        # the reason must surface to the user.
        'verrou': verrou,
    }


def _cle(libelle):
    return libelle.strip().lower()


def evaluer_test7(reference, candidat=None, tolerance=TOLERANCE_DEFAUT,
                  source_irradiance=None):
    """Evaluate the full Test 7, and therefore validation class 5.

    `candidat`: dict {quantity label: annual value}. Labels are matched
    case-insensitively, ignoring leading/trailing whitespace. A quantity
    absent from the candidate remains NOT_CHECKABLE -- never a pass by default.
    """
    candidat = candidat or {}
    index = dict((_cle(k), v) for k, v in candidat.items())

    # Candidate keys that do not match ANY reference quantity.
    # Without this check, a typo in the adapter would be
    # silently ignored and the quantity would appear NOT_CHECKABLE with
    # no indication as to why. Keys prefixed with "_" are assumed
    # metadata (`_provenance`) and are not flagged.
    attendues = set(_cle(g['libelle_de']) for g in reference['grandeurs'])
    cles_ignorees = sorted(
        k for k in candidat
        if not str(k).startswith('_') and _cle(k) not in attendues)

    resultats = []
    for grandeur in reference['grandeurs']:
        valeur = index.get(_cle(grandeur['libelle_de']))
        resultats.append(evaluer_grandeur(
            grandeur, valeur, tolerance, source_irradiance))

    soumises = [r for r in resultats if r['groupe'] == GROUPE_AVEC_CRITERE]
    # Fallback: if the workbook's group label changes, it is better to evaluate
    # all quantities with a band than to evaluate none and announce an
    # empty pass.
    if not soumises:
        soumises = resultats

    echecs = [r for r in soumises if r['conforme'] is False]
    inconnues = [r for r in soumises if r['conforme'] is None]
    reserves = [r for r in soumises
                if r['statut'] == scatter_band.VERDICT_PASS_WITH_RESERVATION]

    if echecs:
        verdict_global = scatter_band.VERDICT_FAIL
    elif inconnues:
        verdict_global = scatter_band.VERDICT_NOT_CHECKABLE
    elif reserves:
        verdict_global = scatter_band.VERDICT_PASS_WITH_RESERVATION
    else:
        verdict_global = scatter_band.VERDICT_PASS

    return {
        'test': 7,
        'classes_concernees': list(CLASSES_CONCERNEES),
        'critere': {
            'statut': STATUT_CRITERE,
            'justification': JUSTIFICATION_CRITERE,
            'formule': reference['critere']['formule'],
        },
        'grandeurs': resultats,
        # Keys supplied by the caller and matched to no quantity: a
        # non-empty list almost always signals a typo on the adapter side.
        # Does NOT affect the verdict, but must be displayed.
        'cles_candidat_ignorees': cles_ignorees,
        # Irradiance origin declared by the caller, `None` if none.
        # Must appear in every report: it is the sole record of what
        # the PV was computed against.
        'source_irradiance': source_irradiance,
        'grandeurs_verrouillees': [r['libelle'] for r in resultats if r['verrou']],
        'grandeurs_soumises_au_critere': len(soumises),
        'nb_echecs': len(echecs),
        'nb_non_evaluables': len(inconnues),
        'nb_reserves': len(reserves),
        'verdict': verdict_global,
        # True ONLY for class 5, the only class that Test 7 validates
        # on its own. Classes 4A and 4B require additional tests:
        # this flag says nothing about them.
        'classe_5_validee': verdict_global in (
            scatter_band.VERDICT_PASS,
            scatter_band.VERDICT_PASS_WITH_RESERVATION),
        # Historical alias kept for existing consumers. Since
        # receipt of the corrected workbook, it carries the same value as the
        # main flag and no longer implies the criterion is provisional.
        'classe_5_provisoirement_conforme': verdict_global in (
            scatter_band.VERDICT_PASS,
            scatter_band.VERDICT_PASS_WITH_RESERVATION),
        # Honesty safeguard: even a full PASS remains a software conformity
        # until the sub-commission confirms the criterion (art. 4.6.2).
        # A consumer that reads only `classe_5_validee` must not be able to
        # present it as an official validation.
        'attestation_sous_commission_requise': (
            not CRITERE_ATTESTE_PAR_SOUS_COMMISSION),
    }


def resumer(resultat):
    """Text summary, one line per quantity. For the console and reports."""
    lignes = ['Test 7 -- classe de validation 5',
              'critere : %s (%s)' % (resultat['critere']['formule'],
                                     resultat['critere']['statut']),
              '']
    gabarit = '%-46s %12s %12s %12s  %s'
    lignes.append(gabarit % ('grandeur', 'candidat', 'bas', 'haut', 'statut'))
    lignes.append('-' * 104)
    for r in resultat['grandeurs']:
        candidat = ('--' if r['candidat'] is None
                    else '%.1f' % r['candidat'])
        lignes.append(gabarit % (
            r['libelle'][:46], candidat, '%.1f' % r['borne_basse'],
            '%.1f' % r['borne_haute'], r['statut']))
    lignes.append('')
    lignes.append('verdict : %s  (%d echec(s), %d non evaluable(s), %d reserve(s))'
                  % (resultat['verdict'], resultat['nb_echecs'],
                     resultat['nb_non_evaluables'], resultat['nb_reserves']))
    if resultat.get('source_irradiance'):
        lignes.append('irradiance declaree : %s' % resultat['source_irradiance'])
    for verrouillee in resultat.get('grandeurs_verrouillees') or []:
        lignes.append('VERROU  %s : %s' % (verrouillee, MOTIF_VERROU_IRRADIANCE))
    for ignoree in resultat.get('cles_candidat_ignorees') or []:
        lignes.append('IGNOREE %s : ne correspond a aucune grandeur de reference'
                      % ignoree)
    return '\n'.join(lignes)
