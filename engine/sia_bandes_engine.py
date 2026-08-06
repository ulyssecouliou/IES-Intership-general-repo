# -*- coding: utf-8 -*-
"""Generic SIA 4010 engine for references shaped as quantity -> case.

Tests 2 to 6 share one reference shape: a handful of quantities, each carrying
several cases, each case holding one band. Test 7's references are a flat list
instead, so it keeps `engine/test7_engine.py` -- normalising the two would mean
rewriting a module that is already frozen, tested and committed, for no gain.

REFERENCE SHAPE consumed here, produced by `scripts/build_sia_reference.py`:

    {"test": 2,
     "grandeurs": [{"libelle_de": ..., "unite": ...,
                    "cas": [{"cas": "Test 2 A", "contributeurs": [...],
                             "par_colonne": {...}, "moyenne": ..., ...}]}]}

CRITERION. Identical to every other SIA 4010 test: the candidate must fall
inside `mean +/- MAX(ABS(program - mean))` over the CONTRIBUTING programs,
bounds inclusive. It is marked INFERE, because only Test 1 states its criteria
in its own specification; everywhere else SIA 4010 clause 4.4 delegates the
comparison to the evaluation workbook, and confirmation by the sub-commission
remains outstanding (clause 4.6.2).

THE TRAP THIS ENGINE MUST NOT FALL INTO. In tests 2 and 3 the workbook columns
are program VARIANTS, not programs -- IDA_ICE appears three times, as
"Fe det Spec", "Fe det noSpec" and "Fe einf". The SIA keeps one variant per
program, and not the same one across programs. The contributing set therefore
differs from case to case, and is read from the frozen reference, never
inferred from position.

Pure Python, no dependencies, no `import iesve`: testable in CI without a VE
licence and runnable as-is inside VEScripts.
"""

import io
import json
import os

from engine import scatter_band


_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))

#: Tests dont les references ont cette forme. Les cinq classeurs presentent
#: pourtant trois dispositions differentes -- grandeur en bloc et cas en
#: ligne (2, 3), grandeur en ligne sans cas (4, 6), matrice grandeur x cas
#: (5) -- mais scripts/build_sia_reference.py les normalise a l extraction.
TESTS_SUPPORTES = (2, 3, 4, 5, 6)

TOLERANCE_DEFAUT = 1e-6

STATUT_CRITERE = 'INFERE'
JUSTIFICATION_CRITERE = (
    "La specification de ce test n'enonce aucun critere ; SIA 4010:2023 "
    "clause 4.4 delegue la comparaison au classeur d'evaluation, qui porte "
    "les bandes. A confirmer par la sous-commission (clause 4.6.2).")


def chemin_reference(numero_test):
    """Chemin du referentiel fige d'un test.

    Args:
        numero_test: Numero du test SIA.

    Returns:
        str: Chemin absolu du JSON.
    """
    return os.path.join(_RACINE, 'refs', 'reference-data',
                        'test-%d.ref.json' % numero_test)


def charger_reference(numero_test, chemin=None):
    """Charge les references figees d'un test.

    Args:
        numero_test: Numero du test SIA, 2 ou 3.
        chemin: Chemin explicite, sinon celui par defaut.

    Returns:
        dict: Le referentiel.

    Raises:
        ValueError: Si le test n'a pas cette forme de reference.
    """
    if numero_test not in TESTS_SUPPORTES:
        raise ValueError(
            'test %r hors de portee de ce moteur ; supportes : %s. Le Test 7 '
            'a sa propre forme de reference et son propre moteur.'
            % (numero_test, list(TESTS_SUPPORTES)))
    with io.open(chemin or chemin_reference(numero_test), encoding='utf-8') as f:
        return json.load(f)


def valeurs_contributrices(cas):
    """Valeurs des seuls programmes contributeurs d'un cas.

    Un programme absent du jeu est ECARTE, jamais mis a zero : le compter
    comme zero deplacerait la moyenne et donc la bande.

    Args:
        cas: Entree de cas du referentiel.

    Returns:
        list[float]: Valeurs, dans l'ordre du classeur.
    """
    par_colonne = cas['par_colonne']
    valeurs = []
    for lettre in cas['contributeurs']:
        entree = par_colonne.get(lettre)
        if entree is not None and entree.get('valeur') is not None:
            valeurs.append(float(entree['valeur']))
    return valeurs


def _cle(texte):
    return ('%s' % texte).strip().lower()


def evaluer_cas(cas, valeur_candidate, tolerance=TOLERANCE_DEFAUT):
    """Verdict d'un cas : le candidat tombe-t-il dans la bande ?

    Args:
        cas: Entree de cas du referentiel.
        valeur_candidate: Valeur produite par VE, ou `None`.
        tolerance: Tolerance de comparaison.

    Returns:
        dict: Ligne de resultat, jamais `None`.
    """
    contributions = valeurs_contributrices(cas)
    statut = scatter_band.verdict(
        valeur_candidate, contributions,
        floor_at_zero=cas['plancher_a_zero'], tolerance=tolerance)

    ecart = None
    if valeur_candidate is not None and cas.get('moyenne') is not None:
        ecart = float(valeur_candidate) - cas['moyenne']

    return {
        'cas': cas['cas'],
        'ligne_classeur': cas['ligne_classeur'],
        'candidat': valeur_candidate,
        'moyenne': cas['moyenne'],
        'borne_basse': cas['borne_basse'],
        'borne_haute': cas['borne_haute'],
        'plancher_a_zero': cas['plancher_a_zero'],
        'contributeurs': cas['contributeurs'],
        'programmes': [cas['par_colonne'][l].get('programme')
                       for l in cas['contributeurs'] if l in cas['par_colonne']],
        'variantes': [cas['par_colonne'][l].get('variante')
                      for l in cas['contributeurs'] if l in cas['par_colonne']],
        'ecart_a_la_moyenne': ecart,
        'statut': statut,
        'conforme': (True if scatter_band.is_passing(statut)
                     else (False if statut == scatter_band.VERDICT_FAIL
                           else None)),
        'critere_statut': STATUT_CRITERE,
    }


def _index_candidat(candidat):
    """Indexe un candidat imbrique en {(grandeur, cas): valeur}.

    Args:
        candidat: `{libelle grandeur: {nom de cas: valeur}}`.

    Returns:
        dict: Index insensible a la casse et aux espaces de bord.
    """
    index = {}
    for grandeur, par_cas in (candidat or {}).items():
        if not isinstance(par_cas, dict):
            continue
        for nom_cas, valeur in par_cas.items():
            index[(_cle(grandeur), _cle(nom_cas))] = valeur
    return index


def evaluer(reference, candidat=None, tolerance=TOLERANCE_DEFAUT):
    """Evalue un test entier.

    Args:
        reference: Referentiel charge par `charger_reference`.
        candidat: `{libelle grandeur: {nom de cas: valeur}}`. Une grandeur ou
            un cas absent reste NOT_CHECKABLE -- jamais un succes par defaut.
        tolerance: Tolerance de comparaison.

    Returns:
        dict: Resultat complet, meme contrat que `test7_engine.evaluer_test7`.
    """
    index = _index_candidat(candidat)
    attendues = set()

    grandeurs = []
    for grandeur in reference['grandeurs']:
        libelle = grandeur['libelle_de']
        lignes = []
        for cas in grandeur['cas']:
            cle = (_cle(libelle), _cle(cas['cas']))
            attendues.add(cle)
            lignes.append(evaluer_cas(cas, index.get(cle), tolerance))
        grandeurs.append({
            'libelle': libelle,
            'unite': grandeur.get('unite'),
            'cas': lignes,
        })

    # Cles fournies mais appariees a rien : presque toujours une faute de
    # frappe cote adaptateur. N influence pas le verdict, mais doit s afficher.
    ignorees = sorted(
        '%s / %s' % (g, c)
        for (g, c) in _index_candidat(candidat)
        if (g, c) not in attendues)

    toutes = [ligne for g in grandeurs for ligne in g['cas']]
    echecs = [l for l in toutes if l['conforme'] is False]
    inconnues = [l for l in toutes if l['conforme'] is None]
    reserves = [l for l in toutes
                if l['statut'] == scatter_band.VERDICT_PASS_WITH_RESERVATION]

    if echecs:
        verdict = scatter_band.VERDICT_FAIL
    elif inconnues:
        verdict = scatter_band.VERDICT_NOT_CHECKABLE
    elif reserves:
        verdict = scatter_band.VERDICT_PASS_WITH_RESERVATION
    else:
        verdict = scatter_band.VERDICT_PASS

    return {
        'test': reference['test'],
        'classes_concernees': list(reference.get('classes_concernees', [])),
        'critere': {
            'statut': STATUT_CRITERE,
            'justification': JUSTIFICATION_CRITERE,
            'formule': reference['critere']['formule'],
        },
        'grandeurs': grandeurs,
        'nb_bandes': len(toutes),
        'nb_echecs': len(echecs),
        'nb_non_evaluables': len(inconnues),
        'nb_reserves': len(reserves),
        'cles_candidat_ignorees': ignorees,
        'verdict': verdict,
    }


def resumer(resultat):
    """Resume texte, une ligne par cas.

    Args:
        resultat: Sortie d'`evaluer`.

    Returns:
        str: Resume multi-lignes.
    """
    lignes = ['Test %s -- classes %s' % (resultat['test'],
                                         ', '.join(resultat['classes_concernees'])),
              'critere : %s (%s)' % (resultat['critere']['formule'],
                                     resultat['critere']['statut']),
              '']
    for grandeur in resultat['grandeurs']:
        lignes.append('%s [%s]' % (grandeur['libelle'], grandeur['unite']))
        for cas in grandeur['cas']:
            candidat = '--' if cas['candidat'] is None else '%.1f' % cas['candidat']
            lignes.append('  %-12s %10s  (%9.1f ... %9.1f)  %s'
                          % (cas['cas'], candidat, cas['borne_basse'],
                             cas['borne_haute'], cas['statut']))
        lignes.append('')
    lignes.append('verdict : %s  (%d echec(s), %d non evaluable(s))'
                  % (resultat['verdict'], resultat['nb_echecs'],
                     resultat['nb_non_evaluables']))
    for ignoree in resultat['cles_candidat_ignorees']:
        lignes.append('IGNOREE %s : ne correspond a aucune bande' % ignoree)
    return '\n'.join(lignes)
