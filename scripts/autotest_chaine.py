# -*- coding: utf-8 -*-
u"""Auto-test de bout en bout : référence → moteur → verdict → vue.

CE QUE CE SCRIPT PROUVE, ET CE QU'IL NE PROUVE PAS.

Il resoumet à la chaîne les valeurs d'un **programme de référence** comme si
elles venaient de VE, et vérifie que la chaîne les déclare conformes. Cela
prouve que la **mécanique** est correcte : le référentiel se charge, le moteur
apparie les grandeurs et les cas, la bande se calcule, le verdict se compose,
la vue s'assemble.

Cela ne prouve **rien** sur IESVE. Un programme contributeur tombe dans sa
propre bande par construction — la bande vaut `moyenne ± max|programme −
moyenne|`, et l'écart maximal est par définition supérieur ou égal à celui de
chaque contributeur. Le succès est donc arithmétiquement garanti : c'est
précisément ce qui en fait un test de la plomberie, et pas un résultat de
validation.

    Une classe « fonctionnelle » au sens de ce script = la chaîne tourne.
    Une classe « validée » au sens de la SIA = IESVE a simulé les cas et ses
    résultats tombent dans les bandes. Aucune classe n'est validée à ce jour.

Le script échoue bruyamment si un contributeur ressort NON conforme : cela ne
peut venir que d'un défaut de la chaîne, jamais des données.

Usage :
    python scripts/autotest_chaine.py [numero...]
"""

from __future__ import print_function

import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

from engine import sia_bandes_engine as moteur_bandes          # noqa: E402
from engine import sia_distributions_engine as moteur_distrib  # noqa: E402
from engine import scatter_band                                # noqa: E402

TESTS = (2, 3, 4, 5, 6)


class ChaineDefaillante(RuntimeError):
    u"""Levée quand un contributeur ne ressort pas conforme.

    Arithmétiquement impossible si la chaîne est correcte : l'erreur est
    forcément dans le code, jamais dans les données de référence.
    """


def choisir_contributeur(reference):
    u"""Choisit la colonne présente dans le plus de cas.

    Args:
        reference: Référentiel des sommes annuelles.

    Returns:
        str | None: Lettre de colonne, ou `None` si le test n'en a aucune.
    """
    comptes = {}
    for grandeur in reference['grandeurs']:
        for cas in grandeur['cas']:
            for lettre in cas['contributeurs']:
                comptes[lettre] = comptes.get(lettre, 0) + 1
    if not comptes:
        return None
    return sorted(comptes.items(), key=lambda p: (-p[1], p[0]))[0][0]


def candidat_depuis_contributeur(reference, lettre):
    u"""Construit un candidat à partir des valeurs d'un programme.

    Args:
        reference: Référentiel des sommes annuelles.
        lettre: Colonne du programme à rejouer.

    Returns:
        dict: `{libellé grandeur: {nom de cas: valeur}}`.
    """
    candidat = {}
    for grandeur in reference['grandeurs']:
        par_cas = {}
        for cas in grandeur['cas']:
            if lettre not in cas['contributeurs']:
                continue
            entree = cas['par_colonne'].get(lettre) or {}
            if entree.get('valeur') is not None:
                par_cas[cas['cas']] = float(entree['valeur'])
        if par_cas:
            candidat[grandeur['libelle_de']] = par_cas
    return candidat


def verifier_bandes(numero_test):
    u"""Rejoue un programme de référence dans le moteur des sommes annuelles.

    Args:
        numero_test: Numéro du test SIA.

    Returns:
        dict: Compte rendu.

    Raises:
        ChaineDefaillante: Si un cas rejoué ressort non conforme.
    """
    reference = moteur_bandes.charger_reference(numero_test)
    lettre = choisir_contributeur(reference)
    if lettre is None:
        raise ChaineDefaillante(
            u'test %d : aucun contributeur dans le référentiel.' % numero_test)

    candidat = candidat_depuis_contributeur(reference, lettre)
    resultat = moteur_bandes.evaluer(reference, candidat)

    echecs = []
    evalues = 0
    for grandeur in resultat['grandeurs']:
        for ligne in grandeur['cas']:
            if ligne['candidat'] is None:
                continue
            evalues += 1
            if not scatter_band.is_passing(ligne['statut']):
                # `libelle`, pas `libelle_de` : le RESULTAT du moteur renomme
                # la cle du referentiel. Le chemin d echec n avait jamais ete
                # exerce, et son propre test l a demasque.
                echecs.append((grandeur['libelle'], ligne['cas'],
                               ligne['statut']))
    if echecs:
        raise ChaineDefaillante(
            u'test %d : %d cas rejoués sortent de leur propre bande, ce qui '
            u'est arithmétiquement impossible. Le défaut est dans la chaîne. '
            u'Premiers : %s' % (numero_test, len(echecs), echecs[:3]))

    return {
        'test': numero_test,
        'programme_rejoue': lettre,
        'classes_concernees': resultat['classes_concernees'],
        'nb_bandes': resultat['nb_bandes'],
        'nb_cas_rejoues': evalues,
        'nb_non_evaluables': resultat['nb_non_evaluables'],
        'critere': resultat['critere']['statut'],
        'verdict': resultat['verdict'],
    }


def verifier_distributions(numero_test):
    u"""Rejoue un programme de référence dans le moteur des distributions.

    Args:
        numero_test: Numéro du test SIA.

    Returns:
        dict | None: Compte rendu, ou `None` si le test n'a pas ce critère.

    Raises:
        ChaineDefaillante: Si une classe rejouée sort de l'enveloppe.
    """
    if numero_test not in moteur_distrib.TESTS_SUPPORTES:
        return None
    try:
        reference = moteur_distrib.charger_reference(numero_test)
    except moteur_distrib.ReferenceIntrouvable:
        return None

    candidat, hors = {}, 0
    for bloc in reference['distributions']:
        if not bloc['contributeurs']:
            continue
        lettre = bloc['contributeurs'][0]['colonne']
        candidat[(bloc['cas'], bloc['grandeur'])] = [
            entree['par_colonne'][lettre] for entree in bloc['effectifs']]

    resultat = moteur_distrib.evaluer(reference, candidat)
    for bloc in resultat['distributions']:
        hors += bloc['nb_hors_lecture'].get(
            moteur_distrib.LECTURE_ENVELOPPE, 0)
    if hors:
        raise ChaineDefaillante(
            u'test %d : %d classes rejouées sortent de l\'enveloppe min/max '
            u'de leur propre jeu — impossible si la chaîne est correcte.'
            % (numero_test, hors))

    return {
        'test': numero_test,
        'nb_distributions': resultat['nb_distributions'],
        'nb_evaluees': resultat['nb_evaluees'],
        'critere': resultat['critere']['statut'],
        'verdict': resultat['verdict'],
    }


def verifier_vue(numero_test):
    u"""Assemble la vue du navigateur, pour vérifier qu'elle tient debout.

    Args:
        numero_test: Numéro du test SIA.

    Returns:
        dict: Compte rendu de la vue.
    """
    from ui import verdict_view as vue

    reference = moteur_bandes.charger_reference(numero_test)
    lettre = choisir_contributeur(reference)
    resultat = moteur_bandes.evaluer(
        reference, candidat_depuis_contributeur(reference, lettre))
    assemblee = vue.construire_vue_bandes(resultat)
    return {
        'test_id': assemblee.get('test_id'),
        'nb_lignes': len(assemblee.get('lignes', [])),
        'couleur': assemblee['verdict_global']['couleur'],
    }


def executer(tests=TESTS):
    u"""Déroule l'auto-test complet.

    Args:
        tests: Numéros de tests à contrôler.

    Returns:
        list[dict]: Un compte rendu par test.
    """
    comptes_rendus = []
    for numero in tests:
        rendu = {'bandes': verifier_bandes(numero),
                 'distributions': verifier_distributions(numero),
                 'vue': verifier_vue(numero)}
        comptes_rendus.append(rendu)
    return comptes_rendus


def main(arguments=()):
    u"""Point d'entrée en ligne de commande.

    Args:
        arguments: Numéros de tests.

    Returns:
        int: 0 si la chaîne tient, 1 sinon.
    """
    demandes = [int(a) for a in arguments if a.isdigit()]
    print(u'AUTO-TEST DE LA CHAINE — reference -> moteur -> verdict -> vue')
    print(u'Ne prouve PAS que IESVE passe les tests : aucune simulation n est')
    print(u'en jeu. Prouve que la mecanique tourne de bout en bout.')
    print()
    try:
        rendus = executer(demandes or TESTS)
    except ChaineDefaillante as erreur:
        print(u'CHAINE DEFAILLANTE : %s' % erreur)
        return 1

    classes = set()
    for rendu in rendus:
        bandes = rendu['bandes']
        classes.update(bandes['classes_concernees'])
        distributions = rendu['distributions']
        print(u'Test %d  programme rejoue %-3s  %2d/%2d cas  classes %s'
              % (bandes['test'], bandes['programme_rejoue'],
                 bandes['nb_cas_rejoues'], bandes['nb_bandes'],
                 u', '.join(bandes['classes_concernees'])))
        print(u'         critere somme annuelle : %s' % bandes['critere'])
        if distributions:
            print(u'         distributions : %d/%d evaluees, critere %s'
                  % (distributions['nb_evaluees'],
                     distributions['nb_distributions'],
                     distributions['critere']))
        else:
            print(u'         distributions : sans objet pour ce test')
        print(u'         vue : %d lignes' % rendu['vue']['nb_lignes'])
    print()
    print(u'Chaine verte sur %d tests, couvrant les classes %s.'
          % (len(rendus), u', '.join(sorted(classes))))
    print(u'AUCUNE de ces classes n est VALIDEE : il y faut une simulation')
    print(u'IESVE, et 0 liaison sur 20 est etablie a ce jour.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
