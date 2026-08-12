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

# SIA 4010:2023, tableau 63 -- les classes qui EXIGENT le Test 7 :
#   4A : tests 1, 2A, 3A a F, 4 a 7
#   4B : tests 1 a 7
#   5  : test 7 SEUL
# La classe 5 est la seule dont le Test 7 suffise ; pour 4A et 4B il n'est
# qu'un test parmi d'autres. Omettre 4A/4B ferait sous-estimer la portee d'un
# echec du Test 7 dans le navigateur.
CLASSES_CONCERNEES = ('4A', '4B', '5')

# La seule classe dont le Test 7 constitue a lui seul la validation.
CLASSE_SATISFAITE_PAR_CE_SEUL_TEST = '5'

# Les Diagnosegroessen ne portent aucune bande dans le classeur : elles sont
# rapportees pour information et n'entrent jamais dans le verdict.
GROUPE_AVEC_CRITERE = u'Testgr\xf6ssen'

TOLERANCE_DEFAUT = 1e-6

# VERROU D'IRRADIANCE -- ajoute le 2026-08-06 apres audit independant.
#
# L'audit a etabli qu'aucun verrou n'existait : fournir une valeur pour
# `PV-Ertrag` suffisait a obtenir PASS et `classe_5_validee = True`. Or le
# calcul du PV exige l'irradiance sur le plan des modules, qu'AUCUNE source
# officielle en notre possession ne fournit (cf.
# `traceability/classes-de-validation.spec.md`). Le scenario dangereux est
# concret : un adaptateur calculant le PV sur un climat de substitution --
# CH2018 2035, station voisine -- produirait un nombre plausible que rien ne
# signalerait.
#
# Le verrou n'interdit pas la valeur : il exige que l'appelant DECLARE d'ou
# vient son irradiance. Un blocage en dur serait faux le jour ou nous aurons
# la donnee ; une declaration obligatoire reste juste dans les deux cas, et
# la source declaree remonte dans tous les rapports.
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


def charger_reference(chemin=None):
    """Charge les references figees du Test 7."""
    chemin = chemin or CHEMIN_REFERENCE_DEFAUT
    with io.open(chemin, encoding='utf-8') as flux:
        return json.load(flux)


def valeurs_contributrices(grandeur):
    """Valeurs des seuls programmes contributeurs, dans l'ordre du classeur.

    Un programme absent de `contributeurs_noms` est ECARTE, pas mis a zero :
    le compter comme zero deplacerait la moyenne et donc la bande.
    """
    par_programme = grandeur['par_programme']
    valeurs = []
    for nom in grandeur['contributeurs_noms']:
        valeur = par_programme.get(nom)
        if valeur is not None:
            valeurs.append(float(valeur))
    return valeurs


def exige_irradiance(grandeur):
    """La grandeur exige-t-elle l'irradiance solaire pour etre calculee ?"""
    return grandeur['libelle_de'].strip() in GRANDEURS_EXIGEANT_IRRADIANCE


def evaluer_grandeur(grandeur, valeur_candidate, tolerance=TOLERANCE_DEFAUT,
                     source_irradiance=None):
    """Verdict d'une grandeur : le candidat tombe-t-il dans la bande ?

    Le champ `critere_statut` conserve l'identité de la source corrigée utilisée
    et permet au rapport de distinguer l'évaluation logicielle de l'attestation
    délivrée par la sous-commission.

    `source_irradiance` : description de l'origine de l'irradiance, obligatoire
    pour soumettre une grandeur de `GRANDEURS_EXIGEANT_IRRADIANCE`. Sans elle,
    la valeur est REFUSEE et la grandeur reste non evaluable -- jamais un
    succes obtenu sur une irradiance de substitution silencieuse.
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
        # Rappel du statut du critere sur CHAQUE ligne : `evaluer_grandeur` est
        # publique et peut etre appelee sans passer par `evaluer_test7`.
        'critere_statut': STATUT_CRITERE,
        'exige_irradiance': exige_irradiance(grandeur),
        'source_irradiance': source_irradiance,
        # Non `None` quand une valeur a ete REFUSEE faute de provenance
        # declaree : le motif doit remonter jusqu'a l'utilisateur.
        'verrou': verrou,
    }


def _cle(libelle):
    return libelle.strip().lower()


def evaluer_test7(reference, candidat=None, tolerance=TOLERANCE_DEFAUT,
                  source_irradiance=None):
    """Evalue le Test 7 complet, donc la classe de validation 5.

    `candidat` : dict {libelle de la grandeur: valeur annuelle}. Les libelles
    sont apparies sans tenir compte de la casse ni des espaces de bord. Une
    grandeur absente du candidat reste NOT_CHECKABLE -- jamais un succes par
    defaut.
    """
    candidat = candidat or {}
    index = dict((_cle(k), v) for k, v in candidat.items())

    # Clés du candidat qui ne correspondent à AUCUNE grandeur de référence.
    # Sans ce contrôle, une faute de frappe dans l'adaptateur serait
    # silencieusement ignorée et la grandeur apparaîtrait NOT_CHECKABLE sans
    # que rien n'indique pourquoi. Les clés préfixées par « _ » sont des
    # métadonnées assumées (`_provenance`) et ne sont pas signalées.
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
    # Repli : si l'etiquette de groupe du classeur changeait, mieux vaut juger
    # toutes les grandeurs a bande que de n'en juger aucune et annoncer un
    # succes vide.
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
        # Clés fournies par l'appelant et appariées à aucune grandeur : une
        # liste non vide signale presque toujours une faute de frappe côté
        # adaptateur. N'influence PAS le verdict, mais doit être affichée.
        'cles_candidat_ignorees': cles_ignorees,
        # Provenance de l'irradiance declaree par l'appelant, `None` si aucune.
        # Doit apparaitre dans tout rapport : c'est la seule trace de ce sur
        # quoi le PV a ete calcule.
        'source_irradiance': source_irradiance,
        'grandeurs_verrouillees': [r['libelle'] for r in resultats if r['verrou']],
        'grandeurs_soumises_au_critere': len(soumises),
        'nb_echecs': len(echecs),
        'nb_non_evaluables': len(inconnues),
        'nb_reserves': len(reserves),
        'verdict': verdict_global,
        # Vrai UNIQUEMENT pour la classe 5, seule classe que le Test 7 valide
        # a lui seul. Les classes 4A et 4B exigent d'autres tests en plus :
        # ce drapeau ne dit rien d'elles.
        'classe_5_validee': verdict_global in (
            scatter_band.VERDICT_PASS,
            scatter_band.VERDICT_PASS_WITH_RESERVATION),
        # Alias historique conservÃ© pour les consommateurs existants. Depuis
        # rÃ©ception du classeur corrigÃ©, il porte la mÃªme valeur que le drapeau
        # principal et ne signifie plus que le critÃ¨re est provisoire.
        'classe_5_provisoirement_conforme': verdict_global in (
            scatter_band.VERDICT_PASS,
            scatter_band.VERDICT_PASS_WITH_RESERVATION),
    }


def resumer(resultat):
    """Resume texte, une ligne par grandeur. Pour la console et les rapports."""
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
