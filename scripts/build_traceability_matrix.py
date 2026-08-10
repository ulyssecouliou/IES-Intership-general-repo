# -*- coding: utf-8 -*-
u"""Génère les matrices de traçabilité des tests SIA à bandes (2 à 6).

POURQUOI ELLES SONT GÉNÉRÉES ET NON RÉDIGÉES. Une matrice de traçabilité est
un document de contrôle : elle affirme que telle clause est couverte par tel
code et tel test. Rédigée à la main, elle se périme au premier changement du
dépôt — et une matrice périmée est pire qu'absente, puisqu'elle affirme une
couverture qui n'existe plus.

Tout ce qui est vérifiable est donc LU : les grandeurs et les bandes viennent
des référentiels figés, l'état des liaisons vient de l'adaptateur, l'existence
des fichiers de test est contrôlée sur le disque. Le jugement normatif — ce
que la norme exige, ce qui reste à prouver — est écrit ici, en clair, et daté.

CE QUE CE SCRIPT NE FAIT PAS. Il ne signe rien. La règle 5 du projet demande
une signature `qa-auditor` indépendante, et un script qui se signerait
lui-même ne vaudrait rien.

Usage :
    python scripts/build_traceability_matrix.py [numero...] [--ecrire]
"""

from __future__ import print_function

import io
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

from engine import sia_bandes_engine as moteur_bandes          # noqa: E402
from engine import sia_distributions_engine as moteur_distrib  # noqa: E402
from ve_adapter import bandes_adapter as adaptateur            # noqa: E402

_SORTIE = os.path.join(_RACINE, 'traceability')

TESTS = (2, 3, 4, 5, 6)

#: Ancrage normatif de chaque test, relevé dans les documents officiels. Le
#: numéro de page renvoie au PDF cité ; l'énoncé des critères est repris de la
#: section « Testkriterien » de la spécification, quand elle existe.
ANCRAGE = {
    2: {
        'spec': 'SIA_4010_geteilter_Link/Test2/Spezifikation_Test2.pdf',
        'criteres_dans_la_spec': True,
        'batiment': u'Testraum « ASHRAE 140 » selon EN ISO 52016-1:2017, ch. 7',
        'climat': u'SIA 2028 DRY normal, Zürich Kloten',
        'objet': u'protection solaire — store toile (2A) et stores à lamelles '
                 u'avec régulations 1 à 3 de SIA 387/4:2017, tableau 9',
    },
    3: {
        'spec': 'SIA_4010_geteilter_Link/Test3/Spezifikation_Test3.pdf',
        'criteres_dans_la_spec': True,
        'batiment': u'Testraum « ASHRAE 140 » selon EN ISO 52016-1:2017, ch. 7',
        'climat': u'SIA 2028 DRY normal, Zürich Kloten',
        'objet': u'éclairage et régulation en fonction de la lumière du jour, '
                 u'12 cas (4 protections solaires × régulations)',
    },
    4: {
        'spec': 'SIA_4010_geteilter_Link/Test4/Spezifikation_Test4.pdf',
        'criteres_dans_la_spec': False,
        'batiment': u'Bâtiment exemple, local « Hörsaal », 165,8 m2, sans '
                    u'fenêtre, sur deux niveaux',
        'climat': u'SIA 2028 DRY normal, Zürich Kloten',
        'objet': u'climatisation monozone à débit variable, récupération à '
                 u'plaques sans échange d\'humidité (taux 0,75), régulation '
                 u'CO2',
    },
    5: {
        'spec': 'SIA_4010_geteilter_Link/Test5/Spezifikation_Test5.pdf',
        'criteres_dans_la_spec': True,
        'batiment': u'Bâtiment exemple',
        'climat': u'SIA 2028 DRY normal, Zürich Kloten',
        # « contact 5A-5C, vapeur 5D » était écrit ici. L'extraction du PDF
        # (build_reseau_ventilation_reference) montre que le tableau porte
        # QUATRE colonnes de variantes pour DEUX cellules fusionnées : le
        # point de partage n'est pas dans la couche texte. On décrit donc les
        # deux types sans leur affecter de variantes.
        'objet': u'ventilation mécanique : batteries chaude et froide, '
                 u'récupération rotative, humidification par contact ou par '
                 u'vapeur selon la variante (répartition 5A-5D à confirmer)',
    },
    6: {
        'spec': 'SIA_4010_geteilter_Link/Test6/Spezifikation_Test6.pdf',
        'criteres_dans_la_spec': False,
        'batiment': u'Bâtiment exemple',
        'climat': u'SIA 2028 DRY normal, Zürich Kloten',
        # « variantes de récupération de chaleur » était écrit ici. Le PDF
        # décrit UNE configuration — boucle à eau glycolée — et le référentiel
        # figé ne porte qu'un cas, « (ensemble) ». Annoncer des variantes
        # ferait chercher des cas qui n'existent pas.
        'objet': u'ventilation mécanique à trois étages, récupération par '
                 u'boucle à eau glycolée (« Kreislaufverbund »), configuration '
                 u'unique',
    },
}

#: Fichiers de code et de test attendus. Leur existence est CONTRÔLÉE : une
#: matrice qui citerait un fichier absent serait un faux témoignage.
CHAINE = {
    'moteur (somme annuelle)': 'engine/sia_bandes_engine.py',
    'moteur (distribution)': 'engine/sia_distributions_engine.py',
    'extraction des références': 'scripts/build_sia_reference.py',
    'extraction des distributions':
        'scripts/build_sia_distribution_reference.py',
    'adaptateur VE': 've_adapter/bandes_adapter.py',
    'tests du moteur (bandes)': 'engine/tests/test_sia_bandes_engine.py',
    'tests du moteur (distributions)':
        'engine/tests/test_distributions_engine.py',
    'tests des références figées': 'engine/tests/test_distributions_ref.py',
    'tests de l\'adaptateur': 've_adapter/tests/test_bandes_adapter.py',
}


def _existe(chemin_relatif):
    u"""Vrai si un fichier du dépôt existe.

    Args:
        chemin_relatif: Chemin relatif à la racine.

    Returns:
        bool: Présence sur le disque.
    """
    return os.path.exists(os.path.join(_RACINE, chemin_relatif))


def _etat_liaison(numero_test, libelle):
    u"""État d'une grandeur dans la chaîne d'extraction.

    Args:
        numero_test: Numéro du test SIA.
        libelle: Libellé allemand de la grandeur.

    Returns:
        str: Description, en une ligne de tableau.
    """
    liaison = adaptateur.LIAISONS.get(numero_test, {}).get(libelle, {})
    if liaison.get('aps_varname'):
        return u'**LIÉE** → `%s` (niveau `%s`)' % (liaison['aps_varname'],
                                                   liaison['niveau'])
    piste = adaptateur.candidats_a_confirmer(numero_test).get(libelle)
    if piste:
        nom = piste['aps_varname_candidat']
        if nom is None:
            return u'candidat impossible — %s' % piste['a_confirmer'][:90]
        return u'candidat `%s` (%s), à confirmer' % (nom,
                                                     piste['niveau_de_preuve'])
    if libelle in adaptateur.sans_candidat(numero_test):
        return u'cherché, **aucune variable ne correspond**'
    return u'**pas encore cherché**'


def _tableau_grandeurs(numero_test, reference):
    u"""Lignes du tableau grandeur → bande → extraction.

    Args:
        numero_test: Numéro du test SIA.
        reference: Référentiel des sommes annuelles.

    Returns:
        list[str]: Lignes Markdown.
    """
    lignes = [u'| Grandeur (libellé du classeur) | Unité | Cas | Chaîne VE |',
              u'|---|---|---|---|']
    for grandeur in reference['grandeurs']:
        libelle = grandeur['libelle_de']
        lignes.append(u'| `%s` | %s | %d | %s |'
                      % (libelle, grandeur.get('unite') or u'—',
                         len(grandeur['cas']),
                         _etat_liaison(numero_test, libelle)))
    return lignes


def _tableau_distributions(distributions):
    u"""Lignes du tableau des distributions.

    Args:
        distributions: Référentiel des distributions, ou `None`.

    Returns:
        list[str]: Lignes Markdown.
    """
    if distributions is None:
        return []
    lignes = [u'| Cas | Grandeur | Classes | Programmes de référence |',
              u'|---|---|---|---|']
    for bloc in distributions['distributions']:
        lignes.append(u'| %s | `%s` | %d | %d |'
                      % (bloc['cas'] or u'*(non nommé)*', bloc['grandeur'],
                         bloc['nb_classes'], len(bloc['contributeurs'])))
    return lignes


def _tableau_chaine():
    u"""Lignes du tableau de la chaîne logicielle, existence contrôlée.

    Returns:
        list[str]: Lignes Markdown.
    """
    lignes = [u'| Rôle | Fichier | Présent |', u'|---|---|---|']
    for role, chemin in sorted(CHAINE.items()):
        lignes.append(u'| %s | `%s` | %s |'
                      % (role, chemin, u'oui' if _existe(chemin) else u'**NON**'))
    return lignes


def construire(numero_test):
    u"""Construit la matrice d'un test.

    Args:
        numero_test: Numéro du test SIA.

    Returns:
        str: Document Markdown.

    Raises:
        ValueError: Si le test n'est pas un test à bandes.
    """
    if numero_test not in TESTS:
        raise ValueError(
            u'test %r hors périmètre. Ce script traite les tests à bandes %s. '
            u'Le Test 1 (ASHRAE 140) et le Test 7 (PV) ont leurs propres '
            u'moteurs et leurs propres matrices.' % (numero_test, list(TESTS)))

    reference = moteur_bandes.charger_reference(numero_test)
    try:
        distributions = moteur_distrib.charger_reference(numero_test)
    except (ValueError, moteur_distrib.ReferenceIntrouvable):
        distributions = None

    ancrage = ANCRAGE[numero_test]
    resolues = adaptateur.liaisons_resolues(numero_test)
    declarees = adaptateur.LIAISONS.get(numero_test, {})
    nb_bandes = sum(len(g['cas']) for g in reference['grandeurs'])

    lignes = []
    lignes.append(u'# Matrice de traçabilité — Test SIA 4010 n° %d'
                  % numero_test)
    lignes.append(u'')
    lignes.append(u'> ## Statut : **NON SIGNÉE**')
    lignes.append(u'>')
    lignes.append(u'> Motif bloquant : **%d liaison(s) sur %d** entre une '
                  u'grandeur du classeur et une variable de résultat VE. '
                  u'Aucune valeur candidate ne peut donc être produite, et '
                  u'aucune ligne de cette matrice ne porte de résultat '
                  u'reproduit.' % (len(resolues), len(declarees)))
    lignes.append(u'>')
    lignes.append(u'> Ce document est **généré** par '
                  u'`scripts/build_traceability_matrix.py` : les grandeurs, '
                  u'les bandes et l\'état des liaisons sont lus dans les '
                  u'référentiels figés et dans le code, jamais retapés. Une '
                  u'matrice rédigée à la main se périme au premier changement '
                  u'— et une matrice périmée affirme une couverture qui '
                  u'n\'existe plus.')
    lignes.append(u'>')
    lignes.append(u'> **Le script ne signe pas.** La règle 5 demande une '
                  u'signature `qa-auditor` indépendante.')
    lignes.append(u'')
    lignes.append(u'---')
    lignes.append(u'')

    lignes.append(u'## 1. Ancrage normatif')
    lignes.append(u'')
    lignes.append(u'| Élément | Valeur | Source |')
    lignes.append(u'|---|---|---|')
    lignes.append(u'| Classes de validation concernées | %s | SIA 4010:2023, '
                  u'tableau 63 (p. 48) |'
                  % u', '.join(reference.get('classes_concernees', [])))
    lignes.append(u'| Bâtiment / local | %s | %s |'
                  % (ancrage['batiment'], os.path.basename(ancrage['spec'])))
    lignes.append(u'| Climat | %s | idem |' % ancrage['climat'])
    lignes.append(u'| Objet du test | %s | idem |' % ancrage['objet'])
    lignes.append(u'| Classeur d\'évaluation | `%s` | SIA 4010:2023, §4.4 |'
                  % reference['source']['fichier'])
    lignes.append(u'')

    lignes.append(u'## 2. Critères')
    lignes.append(u'')
    if ancrage['criteres_dans_la_spec']:
        lignes.append(u'La spécification énonce **deux** critères, dans sa '
                      u'section *Testkriterien*.')
    else:
        lignes.append(u'La spécification ne comporte **aucune** section '
                      u'*Testkriterien* : SIA 4010:2023 §4.4 délègue au '
                      u'classeur d\'évaluation. Le classeur ne porte ni '
                      u'classes de fréquence ni feuille de distribution — la '
                      u'somme annuelle est donc le seul critère. C\'est un '
                      u'constat, pas une lacune.')
    lignes.append(u'')
    lignes.append(u'### 2.1 Somme annuelle')
    lignes.append(u'')
    lignes.append(u'- Formule appliquée : `%s`'
                  % reference['critere'].get('formule', u'—'))
    statut_annuel, justification_annuelle = moteur_bandes.critere_du_test(
        numero_test)
    lignes.append(u'- Statut du critère : **%s** — %s'
                  % (statut_annuel, justification_annuelle))
    lignes.append(u'- Bandes figées : **%d**' % nb_bandes)
    lignes.append(u'')
    lignes.append(u'### 2.2 Distribution de fréquence')
    lignes.append(u'')
    if distributions is None:
        lignes.append(u'**Sans objet pour ce test.** Le classeur ne porte ni '
                      u'feuille `Haeufigkeitsklassen` ni feuille '
                      u'`Verteilung`.')
    else:
        lignes.append(u'- Énoncé : %s' % distributions['critere'])
        lignes.append(u'- Statut du critère : **%s**'
                      % moteur_distrib.STATUT_CRITERE)
        lignes.append(u'- Motif : %s' % distributions['pourquoi_non_calcule'])
        lignes.append(u'- Distributions figées : **%d**, sur **%d** classes'
                      % (distributions['nb_distributions'],
                         distributions['distributions'][0]['nb_classes']))
        lignes.append(u'- Les deux lectures du `Streubereich` sont calculées '
                      u'(`%s`, `%s`) et **aucune n\'est retenue** : le moteur '
                      u'ne rend jamais de verdict conforme.'
                      % moteur_distrib.LECTURES)
    lignes.append(u'')

    lignes.append(u'## 3. Grandeurs, bandes et chaîne d\'extraction')
    lignes.append(u'')
    lignes.extend(_tableau_grandeurs(numero_test, reference))
    lignes.append(u'')

    if distributions is not None:
        lignes.append(u'## 4. Distributions de référence')
        lignes.append(u'')
        lignes.extend(_tableau_distributions(distributions))
        lignes.append(u'')
        for reserve in distributions.get('reserves', []):
            lignes.append(u'> %s' % reserve)
            lignes.append(u'>')
        lignes.append(u'')

    lignes.append(u'## %d. Chaîne logicielle' % (5 if distributions else 4))
    lignes.append(u'')
    lignes.extend(_tableau_chaine())
    lignes.append(u'')

    lignes.append(u'## %d. Ce qui n\'est PAS établi'
                  % (6 if distributions else 5))
    lignes.append(u'')
    lignes.extend(_ce_qui_manque(numero_test, distributions, resolues,
                                 declarees))
    lignes.append(u'')
    lignes.append(u'---')
    lignes.append(u'')
    lignes.append(u'## Signature')
    lignes.append(u'')
    lignes.append(u'| Rôle | Nom | Date | Verdict |')
    lignes.append(u'|---|---|---|---|')
    lignes.append(u'| Producteur | `build_traceability_matrix.py` (généré) | '
                  u'— | non applicable |')
    lignes.append(u'| Vérificateur indépendant | `qa-auditor` | — | '
                  u'**non signé** |')
    lignes.append(u'')
    return u'\n'.join(lignes) + u'\n'


def _ce_qui_manque(numero_test, distributions, resolues, declarees):
    u"""Énumère ce qui empêche la signature.

    Args:
        numero_test: Numéro du test SIA.
        distributions: Référentiel des distributions, ou `None`.
        resolues: Liaisons résolues.
        declarees: Liaisons déclarées.

    Returns:
        list[str]: Lignes Markdown.
    """
    lignes = []
    lignes.append(u'1. **Aucune valeur candidate.** %d liaison(s) sur %d sont '
                  u'établies. Tant qu\'elles ne le sont pas, aucun cas ne peut '
                  u'être évalué et le moteur les traite en `NOT_CHECKABLE` — '
                  u'ce qui est la vérité, mais ne vaut pas conformité.'
                  % (len(resolues), len(declarees)))
    lignes.append(u'2. **Aucune simulation.** Le test n\'a jamais été construit '
                  u'ni simulé dans IESVE. Les bandes de référence sont '
                  u'vérifiées ; le comportement de VE face à elles ne l\'est '
                  u'pas.')
    if distributions is not None:
        lignes.append(u'3. **La bande des distributions n\'est pas définie.** '
                      u'Le classeur officiel ne la calcule nulle part. Deux '
                      u'lectures restent défendables et le choix appartient à '
                      u'la sous-commission SIA, pas à cet outil.')
    muettes = adaptateur.sans_candidat(numero_test)
    if muettes:
        lignes.append(u'%d. **%d grandeur(s) sans variable VE correspondante** '
                      u'sur le modèle sondé : %s. Un modèle doté d\'un réseau '
                      u'ApacheHVAC pourrait en exposer davantage — à vérifier '
                      u'avant de conclure.'
                      % (4 if distributions else 3, len(muettes),
                         u', '.join(u'`%s`' % m for m in sorted(muettes))))
    return lignes


# ---------------------------------------------------------------------------
# Tests 1 et 7 — moteurs et formes de référence propres
# ---------------------------------------------------------------------------
#
# Ils ne passent pas par `sia_bandes_engine` et leurs résultats n'ont pas la
# même forme : le Test 1 rend `cas` indexé par « grandeur/cas » et ne porte ni
# `grandeurs` ni `critere` ; le Test 7 ajoute `source_irradiance` et
# `grandeurs_verrouillees`. Les forcer dans le gabarit des tests 2 à 6
# produirait des matrices qui parlent de champs inexistants.

TESTS_DEDIES = (1, 7)

ANCRAGE_DEDIE = {
    1: {
        'spec': 'SIA_4010_geteilter_Link/Test1/Spezifikation_Test1.pdf',
        'batiment': u'Testraum « ASHRAE 140 » selon EN ISO 52016-1:2017, ch. 7',
        'climat': u'ISO 52016-1 DRYCOLD pour les six cas principaux ; '
                  u'SIA 2028 DRY Zürich Kloten pour les cas diagnostiques',
        'objet': u'besoins de chaleur et de froid, températures opératives et '
                 u'charge de pointe horaire, sur la cellule d\'essai',
    },
    7: {
        'spec': 'SIA_4010_geteilter_Link/Test7/Spezifikation_Test7.pdf',
        'batiment': u'Bâtiment exemple',
        'climat': u'SIA 2028 DRY normal, Zürich Kloten',
        'objet': u'besoins de chaleur et de froid pour profils existants, '
                 u'production photovoltaïque comprise',
    },
}


def _tableau_cas_test1(resultat):
    u"""Lignes du tableau des cas du Test 1.

    La colonne qui compte est `type_controle` : seule une minorité d'entrées
    porte le critère pass/fail, les autres sont informatives. Une matrice qui
    les présenterait à égalité laisserait croire que toutes décident du
    verdict. Leur nombre est COMPTÉ, jamais écrit : la première rédaction
    annonçait « un seul cas » là où le moteur en rend trois.

    Args:
        resultat: Ce que rend `evaluer_test1`.

    Returns:
        list[str]: Lignes Markdown.
    """
    lignes = [u'| Grandeur | Cas | Nature du contrôle | Périodes | Évaluées |',
              u'|---|---|---|---|---|']
    for cle in sorted(resultat['cas']):
        entree = resultat['cas'][cle]
        periodes = entree.get('periodes') or {}
        evaluees = sum(1 for p in periodes.values()
                       if p.get('valeur_candidate') is not None)
        nature = entree.get('type_controle') or u'—'
        marque = u'**critère pass/fail**' if nature == 'critere_pass_fail' \
            else u'informatif'
        lignes.append(u'| `%s` | %s | %s (`%s`) | %d | %d |'
                      % (entree.get('grandeur'), entree.get('cas'), marque,
                         nature, len(periodes), evaluees))
    return lignes


def _tableau_grandeurs_test7(resultat):
    u"""Lignes du tableau des grandeurs du Test 7.

    Args:
        resultat: Ce que rend `evaluer_test7`.

    Returns:
        list[str]: Lignes Markdown.
    """
    lignes = [u'| Grandeur | Unité | Statut | Candidat |', u'|---|---|---|---|']
    for grandeur in resultat.get('grandeurs') or []:
        lignes.append(u'| `%s` | %s | %s | %s |'
                      % (grandeur.get('libelle') or grandeur.get('libelle_de'),
                         grandeur.get('unite') or u'—',
                         grandeur.get('statut') or u'—',
                         u'—' if grandeur.get('candidat') is None
                         else grandeur.get('candidat')))
    return lignes


def construire_dedie(numero_test):
    u"""Construit la matrice d'un test à moteur propre (1 ou 7).

    Args:
        numero_test: 1 ou 7.

    Returns:
        str: Document Markdown.

    Raises:
        ValueError: Si le test n'a pas de moteur dédié.
    """
    if numero_test not in TESTS_DEDIES:
        raise ValueError(
            u'test %r sans moteur dédié. Concernés : %s. Les tests 2 à 6 '
            u'passent par `construire`.' % (numero_test, list(TESTS_DEDIES)))

    ancrage = ANCRAGE_DEDIE[numero_test]
    if numero_test == 1:
        from engine import test1_engine as moteur
        resultat = moteur.evaluer_test1(moteur.charger_reference())
        classes = resultat.get('classes_concernees') or []
        verdict = resultat.get('verdict_test1') or {}
        total = verdict.get('nb_periodes_totales', 0)
        non_evaluees = verdict.get('nb_periodes_non_evaluees', 0)
        statut_critere = u'ÉNONCÉ DANS LA SPEC'
        justification = (
            u'Le Test 1 est le seul dont la spécification énonce ses propres '
            u'critères ; ils ne sont pas inférés du classeur.')
    else:
        from engine import test7_engine as moteur
        resultat = moteur.evaluer_test7(moteur.charger_reference())
        classes = resultat.get('classes_concernees') or []
        total = len(resultat.get('grandeurs') or [])
        non_evaluees = resultat.get('nb_non_evaluables', 0)
        critere = resultat.get('critere') or {}
        statut_critere = critere.get('statut') or u'—'
        justification = critere.get('justification') or u''

    lignes = [
        u'# Matrice de traçabilité — Test SIA 4010 n° %d' % numero_test,
        u'',
        u'> ## Statut : **NON SIGNÉE**',
        u'>',
        u'> **%d contrôle(s) sur %d ne sont pas évalués** : aucune simulation '
        u'IESVE n\'a produit de valeur candidate. Aucune ligne de cette '
        u'matrice ne porte donc de résultat reproduit.' % (non_evaluees, total),
        u'>',
        u'> Document **généré** par `scripts/build_traceability_matrix.py` : '
        u'les grandeurs, les cas et leur état sont lus dans le moteur et dans '
        u'les référentiels figés, jamais retapés. Le script **ne signe pas** — '
        u'la règle 5 demande une vérification indépendante.',
        u'',
        u'---',
        u'',
        u'## 1. Ancrage normatif',
        u'',
        u'| Élément | Valeur | Source |',
        u'|---|---|---|',
        u'| Classes de validation concernées | %s | SIA 4010:2023, tableau 63 '
        u'(p. 48) |' % u', '.join(classes),
        u'| Bâtiment / local | %s | %s |'
        % (ancrage['batiment'], os.path.basename(ancrage['spec'])),
        u'| Climat | %s | idem |' % ancrage['climat'],
        u'| Objet du test | %s | idem |' % ancrage['objet'],
        u'',
        u'## 2. Critère',
        u'',
        u'- Statut : **%s**' % statut_critere,
        u'- %s' % justification,
        u'',
    ]

    if numero_test == 1:
        lignes.append(u'## 3. Cas et nature du contrôle')
        lignes.append(u'')
        # Ce compte était ÉCRIT à la main — et faux : le moteur rend trois
        # entrées porteuses, pas une. On le calcule, comme tout le reste.
        porteuses = [entree for entree in resultat['cas'].values()
                     if entree.get('type_controle') == 'critere_pass_fail']
        cas_porteurs = sorted(set(e.get('cas') for e in porteuses))
        lignes.append(
            u'**%d entrée(s) sur %d portent le critère pass/fail**, sur le(s) '
            u'cas %s. Les autres sont informatives : les présenter à égalité '
            u'laisserait croire qu\'elles décident du verdict.'
            % (len(porteuses), len(resultat['cas']),
               u', '.join(cas_porteurs) or u'—'))
        lignes.append(u'')
        lignes.extend(_tableau_cas_test1(resultat))
    else:
        lignes.append(u'## 3. Grandeurs')
        lignes.append(u'')
        lignes.extend(_tableau_grandeurs_test7(resultat))
        verrouillees = resultat.get('grandeurs_verrouillees') or []
        if verrouillees:
            lignes.append(u'')
            lignes.append(u'**Grandeurs verrouillées** : %s. Leur calcul exige '
                          u'une entrée absente du dépôt.'
                          % u', '.join(u'`%s`' % g for g in verrouillees))
        lignes.append(u'')
        lignes.append(u'- Source d\'irradiance : `%s`'
                      % (resultat.get('source_irradiance') or u'AUCUNE'))

    lignes.extend([
        u'',
        u'## 4. Chaîne logicielle',
        u'',
    ])
    lignes.extend(_tableau_chaine_dediee(numero_test))
    lignes.extend([
        u'',
        u'## 5. Ce qui n\'est PAS établi',
        u'',
        u'1. **Aucune valeur candidate.** %d contrôle(s) sur %d restent non '
        u'évalués faute de simulation.' % (non_evaluees, total),
        u'2. **Aucune simulation.** Le test n\'a jamais été construit ni '
        u'simulé dans IESVE.',
    ])
    if numero_test == 1:
        # Quel cas porte le critère est LU dans le moteur : l'écrire ferait
        # de la matrice une affirmation, non un relevé.
        lignes.append(
            u'3. **Les cas diagnostiques 1A à 1E sont hors de portée** : ils '
            u'exigent le climat de Zürich-Kloten, absent du dépôt. Or le '
            u'critère pass/fail repose entièrement sur le(s) cas **%s** — '
            u'sans eux, aucun verdict formel du Test 1 n\'est possible.'
            % (u', '.join(cas_porteurs) or u'aucun'))
    else:
        lignes.append(
            u'3. **La divergence de mise en forme conditionnelle** du classeur '
            u'du Test 7 (`[moyenne ; borne haute]` au lieu de '
            u'`[borne basse ; borne haute]`, seul des six classeurs) est '
            u'posée à la sous-commission et reste sans réponse.')
    lignes.extend([
        u'',
        u'---',
        u'',
        u'## Signature',
        u'',
        u'| Rôle | Nom | Date | Verdict |',
        u'|---|---|---|---|',
        u'| Producteur | `build_traceability_matrix.py` (généré) | — | non '
        u'applicable |',
        u'| Vérificateur indépendant | `qa-auditor` | — | **non signé** |',
        u'',
    ])
    return u'\n'.join(lignes) + u'\n'


def _tableau_chaine_dediee(numero_test):
    u"""Chaîne logicielle d'un test à moteur propre, existence contrôlée.

    Args:
        numero_test: 1 ou 7.

    Returns:
        list[str]: Lignes Markdown.
    """
    fichiers = {
        u'moteur': 'engine/test%d_engine.py' % numero_test,
        u'référence figée': 'refs/reference-data/test-%d.ref.json' % numero_test,
        u'vue du navigateur': 'ui/verdict_view.py',
    }
    if numero_test == 1:
        fichiers[u'adaptateur VE'] = 've_adapter/test1_adapter.py'
        fichiers[u'géométrie'] = 've_adapter/geometrie_test1.py'
        fichiers[u'gbXML'] = 've_adapter/gbxml_test1.py'
        fichiers[u'import + confrontation'] = (
            'scripts/importer_geometrie_test1.py')

    lignes = [u'| Rôle | Fichier | Présent |', u'|---|---|---|']
    for role, chemin in sorted(fichiers.items()):
        lignes.append(u'| %s | `%s` | %s |'
                      % (role, chemin, u'oui' if _existe(chemin) else u'**NON**'))
    return lignes


#: Marque qui reconnaît nos propres sorties — et donc ce qu'il est permis
#: d'écraser. C'est la LIGNE DE SIGNATURE, seule chaîne écrite à l'identique
#: par `construire` et par `construire_dedie` : la bannière d'en-tête, elle,
#: est formulée différemment dans les deux, et un marqueur pris là prenait les
#: tests 2 à 6 pour des rédactions à la main.
MARQUE_GENEREE = u'| Producteur | `build_traceability_matrix.py` (généré) |'


def chemin_de_sortie(numero_test):
    u"""Où écrire la matrice d'un test, sans jamais écraser une rédaction.

    Le Test 7 porte une matrice RÉDIGÉE à la main : trois cents lignes d'audit
    indépendant, renvoyées non signées. Un générateur ne sait pas produire ce
    jugement, et l'écraser le détruirait sans trace. La règle est donc
    générale : **si le fichier attendu n'a pas été écrit par ce script**, le
    relevé va dans un fichier voisin et la rédaction reste intacte.

    Args:
        numero_test: Numéro du test SIA.

    Returns:
        tuple: `(chemin, une_redaction_existe)`.
    """
    attendu = os.path.join(_SORTIE, 'test-%d.matrix.md' % numero_test)
    if not os.path.exists(attendu):
        return attendu, False
    with io.open(attendu, encoding='utf-8') as flux:
        deja_generee = MARQUE_GENEREE in flux.read()
    if deja_generee:
        return attendu, False
    voisin = os.path.join(_SORTIE, 'test-%d.matrix.releve.md' % numero_test)
    return voisin, True


def main(arguments):
    u"""Point d'entrée en ligne de commande.

    Args:
        arguments: Numéros de tests, et `--ecrire`.

    Returns:
        int: 0 si tout s'est bien passé.
    """
    demandes = [int(a) for a in arguments if a.isdigit()]
    for numero in (demandes or (list(TESTS) + list(TESTS_DEDIES))):
        # Les tests 1 et 7 ont leurs propres moteurs et formes de référence :
        # les forcer dans le gabarit des tests à bandes produirait des
        # matrices qui parlent de champs inexistants.
        document = (construire_dedie(numero) if numero in TESTS_DEDIES
                    else construire(numero))
        chemin, redigee = chemin_de_sortie(numero)
        print(u'Test %d : %d lignes' % (numero, document.count(u'\n')))
        if redigee:
            print(u'    matrice RÉDIGÉE présente : elle est conservée. '
                  u'Le relevé va à côté.')
        if '--ecrire' in arguments:
            with io.open(chemin, 'w', encoding='utf-8') as flux:
                flux.write(document)
            print(u'    écrit : %s' % os.path.relpath(chemin, _RACINE))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
