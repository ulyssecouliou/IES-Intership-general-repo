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
        'objet': u'ventilation mécanique : batteries chaude et froide, '
                 u'récupération, humidification (contact 5A-5C, vapeur 5D)',
    },
    6: {
        'spec': 'SIA_4010_geteilter_Link/Test6/Spezifikation_Test6.pdf',
        'criteres_dans_la_spec': False,
        'batiment': u'Bâtiment exemple',
        'climat': u'SIA 2028 DRY normal, Zürich Kloten',
        'objet': u'ventilation mécanique, variantes de récupération de chaleur',
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


def main(arguments):
    u"""Point d'entrée en ligne de commande.

    Args:
        arguments: Numéros de tests, et `--ecrire`.

    Returns:
        int: 0 si tout s'est bien passé.
    """
    demandes = [int(a) for a in arguments if a.isdigit()]
    for numero in (demandes or list(TESTS)):
        document = construire(numero)
        chemin = os.path.join(_SORTIE, 'test-%d.matrix.md' % numero)
        print(u'Test %d : %d lignes' % (numero, document.count(u'\n')))
        if '--ecrire' in arguments:
            with io.open(chemin, 'w', encoding='utf-8') as flux:
                flux.write(document)
            print(u'    écrit : %s' % os.path.relpath(chemin, _RACINE))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
