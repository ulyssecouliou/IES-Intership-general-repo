# -*- coding: utf-8 -*-
u"""Sélection d'une classe de validation, et diagnostic de ce qui la bloque.

DEUX LECTURES D'UN MÊME ÉTAT, POUR DEUX PUBLICS.

Le **client** choisit la classe qu'il vise et veut savoir où il en est : quels
tests elle exige, lesquels sont franchis. Son rapport ne doit contenir que ce
qui la concerne — une classe 1A n'a que faire des grandeurs du Test 5.

L'**équipe** veut la liste précise de ce qui manque, avec la cause et l'action.
`diagnostiquer()` la produit. Elle est délibérément plus dure que le rapport
client : elle nomme les liaisons non résolues, les critères non établis et les
entrées absentes du dépôt.

CE QUE CE MODULE NE FERA JAMAIS. Déclarer une classe atteinte sur autre chose
qu'un résultat de simulation. Une classe sans candidat est `NON_EVALUEE`,
jamais `CONFORME` — et la nuance est portée par un statut distinct, pas par une
formulation prudente.

Python pur : ni `tkinter`, ni `iesve`. Testable sans écran et sans licence.
"""

from __future__ import print_function

from ui import verdict_view as vue

#: Classes de validation, dans l'ordre de SIA 4010:2023, tableau 63 (p. 48).
CLASSES = ('1A', '1B', '2A', '2B', '3', '4A', '4B', '5')

#: Ce que chaque classe permet de faire, en clair. Repris de la colonne
#: « applications » du tableau 63.
INTITULE_DES_CLASSES = {
    '1A': u'Besoins de chaleur, bâtiment sans refroidissement',
    '1B': u'Besoins de chaleur, tous bâtiments',
    '2A': u'Besoins de chaleur et de froid, protection solaire simple',
    '2B': u'Besoins de chaleur et de froid, protection solaire et éclairage',
    '3': u'Installations de ventilation et de climatisation',
    '4A': u'Bâtiment complet, protection solaire simple',
    '4B': u'Bâtiment complet, tous équipements',
    '5': u'Besoins de chaleur et de froid pour profils existants',
}

STATUT_CONFORME = 'CONFORME'
STATUT_NON_CONFORME = 'NON_CONFORME'
STATUT_NON_EVALUEE = 'NON_EVALUEE'

#: Motifs de blocage, du plus bloquant au moins bloquant. L'ordre compte : le
#: rapport interne présente d'abord ce qui empêche tout le reste.
MOTIF_SANS_SIMULATION = 'AUCUNE_SIMULATION'
MOTIF_LIAISONS = 'LIAISONS_NON_RESOLUES'
MOTIF_CRITERE = 'CRITERE_NON_ETABLI'
MOTIF_ENTREE_ABSENTE = 'ENTREE_ABSENTE_DU_DEPOT'

ORDRE_DES_MOTIFS = (MOTIF_SANS_SIMULATION, MOTIF_LIAISONS, MOTIF_CRITERE,
                    MOTIF_ENTREE_ABSENTE)


class ClasseInconnue(ValueError):
    u"""Levée quand une classe demandée ne figure pas au tableau 63."""


def tests_de_la_classe(classe):
    u"""Tests exigés par une classe de validation.

    Args:
        classe: Identifiant de classe, `'1A'` à `'5'`.

    Returns:
        tuple[str]: Identifiants de tests, tels que les nomme le tableau 63.

    Raises:
        ClasseInconnue: Si la classe n'existe pas. Rendre un tuple vide se
            lirait comme « cette classe n'exige rien », ce qui est le contraire
            de la vérité.
    """
    if classe not in vue.TESTS_PAR_CLASSE:
        raise ClasseInconnue(
            u'classe %r inconnue du tableau 63 de SIA 4010:2023. '
            u'Classes : %s.' % (classe, u', '.join(CLASSES)))
    return vue.TESTS_PAR_CLASSE[classe]


def intitule(classe):
    u"""Intitulé lisible d'une classe.

    Args:
        classe: Identifiant de classe.

    Returns:
        str: Intitulé, ou l'identifiant si aucun n'est connu.
    """
    return INTITULE_DES_CLASSES.get(classe, classe)


def _numero_du_test(identifiant):
    u"""Numéro de test SIA porté par un identifiant du tableau 63.

    Le tableau nomme certains tests par un sous-ensemble de cas — « 2A »,
    « 3A-F » — là où le moteur raisonne par numéro. Le préfixe numérique est
    donc extrait, jamais deviné.

    Args:
        identifiant: Par exemple `'1'`, `'2A'`, `'3A-F'`.

    Returns:
        int | None: Numéro, ou `None` si l'identifiant n'en porte pas.
    """
    chiffres = u''
    for caractere in u'%s' % identifiant:
        if caractere.isdigit():
            chiffres += caractere
        else:
            break
    return int(chiffres) if chiffres else None


def selectionner(classe, vues=()):
    u"""Restreint un jeu de vues aux tests qu'exige une classe.

    Args:
        classe: Identifiant de classe.
        vues: Vues assemblées par `verdict_view`.

    Returns:
        dict: Sélection, avec les tests présents et ceux qui manquent.

    Raises:
        ClasseInconnue: Si la classe n'existe pas.
    """
    exiges = tests_de_la_classe(classe)
    numeros_exiges = set(
        n for n in (_numero_du_test(t) for t in exiges) if n is not None)

    retenues, presents = [], set()
    for une_vue in vues:
        numero = _numero_du_test(une_vue.get('test_id') or '')
        if numero in numeros_exiges:
            retenues.append(une_vue)
            presents.add(numero)

    return {
        'classe': classe,
        'intitule': intitule(classe),
        'tests_exiges': list(exiges),
        'vues': retenues,
        'numeros_presents': sorted(presents),
        'numeros_absents': sorted(numeros_exiges - presents),
    }


def statut_de_la_classe(selection):
    u"""Statut d'une classe, à partir d'une sélection.

    Args:
        selection: Ce que rend `selectionner`.

    Returns:
        str: `CONFORME`, `NON_CONFORME` ou `NON_EVALUEE`.
    """
    if selection['numeros_absents'] or not selection['vues']:
        return STATUT_NON_EVALUEE

    couleurs = set(v['verdict_global']['couleur'] for v in selection['vues'])
    if 'rouge' in couleurs:
        return STATUT_NON_CONFORME
    if 'gris' in couleurs:
        # Un test non evalue ne vaut pas conformite. C'est la regle qui
        # empeche une preuve manquante de se lire comme un succes.
        return STATUT_NON_EVALUEE
    return STATUT_CONFORME


def diagnostiquer(classe, vues=(), etat_liaisons=None, entrees_absentes=None):
    u"""Dresse la liste de ce qui empêche une classe d'être atteinte.

    C'est le rapport INTERNE : il nomme les causes, pas seulement les
    symptômes, et propose l'action qui lève chacune.

    Args:
        classe: Identifiant de classe.
        vues: Vues assemblées.
        etat_liaisons: `{numero de test: (resolues, declarees)}`.
        entrees_absentes: `{nom: motif}` des entrées manquant au dépôt.

    Returns:
        dict: Diagnostic ordonné, du plus bloquant au moins bloquant.
    """
    selection = selectionner(classe, vues)
    liaisons = dict(etat_liaisons or {})
    absentes = dict(entrees_absentes or {})
    blocages = []

    for numero in selection['numeros_absents']:
        blocages.append({
            'motif': MOTIF_SANS_SIMULATION,
            'test': numero,
            'constat': u'Le test %d n\'a produit aucun résultat.' % numero,
            'cause': u'Le cas n\'a jamais été construit ni simulé dans IESVE.',
            'action': u'Construire le modèle, lancer ApacheSim sur l\'année '
                      u'complète, relire le .aps.',
        })

    for numero in sorted(liaisons):
        if numero not in selection['numeros_presents'] \
                and numero not in selection['numeros_absents']:
            continue
        resolues, declarees = liaisons[numero]
        if resolues >= declarees:
            continue
        blocages.append({
            'motif': MOTIF_LIAISONS,
            'test': numero,
            'constat': u'Test %d : %d liaison(s) sur %d entre une grandeur du '
                       u'classeur et une variable VE.'
                       % (numero, resolues, declarees),
            'cause': u'Les noms de variables ne sont pas des symboles de '
                     u'l\'API : ils se relèvent sur un .aps réel.',
            'action': u'Lancer Run_VE_SIA4010_Sonde_APS.py sur un modèle qui '
                      u'porte ces organes, puis déclarer les noms relevés.',
        })

    for une_vue in selection['vues']:
        critere = (une_vue.get('critere') or {}).get('statut')
        if critere and critere not in ('ENONCE_DANS_LA_SPEC',):
            blocages.append({
                'motif': MOTIF_CRITERE,
                'test': _numero_du_test(une_vue.get('test_id') or ''),
                'constat': u'%s : critère %s.'
                           % (une_vue.get('test_id'), critere),
                'cause': u'La règle appliquée n\'est pas écrite dans la '
                         u'spécification ; elle est retrouvée dans le '
                         u'classeur, ou pas définie du tout.',
                'action': u'Faire confirmer par la sous-commission SIA '
                          u'(SIA 4010:2023, §4.6.2).',
            })

    for nom in sorted(absentes):
        blocages.append({
            'motif': MOTIF_ENTREE_ABSENTE,
            'test': None,
            'constat': u'Entrée absente du dépôt : %s.' % nom,
            'cause': absentes[nom],
            'action': u'Obtenir la donnée officielle avant tout résultat '
                      u'présenté comme un candidat SIA.',
        })

    blocages.sort(key=lambda b: (ORDRE_DES_MOTIFS.index(b['motif']),
                                 b['test'] if b['test'] is not None else 99))
    return {
        'classe': classe,
        'intitule': selection['intitule'],
        'statut': statut_de_la_classe(selection),
        'tests_exiges': selection['tests_exiges'],
        'nb_blocages': len(blocages),
        'blocages': blocages,
        'atteignable_en_letat': not blocages,
    }


def resumer_diagnostic(diagnostic):
    u"""Rend le diagnostic lisible en console ou en rapport interne.

    Args:
        diagnostic: Ce que rend `diagnostiquer`.

    Returns:
        str: Texte.
    """
    lignes = [
        u'Classe %s — %s' % (diagnostic['classe'], diagnostic['intitule']),
        u'Tests exiges : %s' % u', '.join(diagnostic['tests_exiges']),
        u'Statut : %s' % diagnostic['statut'],
        u'',
    ]
    if not diagnostic['blocages']:
        lignes.append(u'Aucun blocage recense.')
        return u'\n'.join(lignes)

    motif_courant = None
    for blocage in diagnostic['blocages']:
        if blocage['motif'] != motif_courant:
            motif_courant = blocage['motif']
            lignes.append(u'[%s]' % motif_courant)
        lignes.append(u'  %s' % blocage['constat'])
        lignes.append(u'      cause  : %s' % blocage['cause'])
        lignes.append(u'      action : %s' % blocage['action'])
    lignes.append(u'')
    lignes.append(u'%d blocage(s). La classe n est pas atteignable en l etat.'
                  % diagnostic['nb_blocages'])
    return u'\n'.join(lignes)
