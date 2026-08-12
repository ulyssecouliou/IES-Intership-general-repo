# -*- coding: utf-8 -*-
u"""Extrait les distributions de fréquence de référence — tests SIA 2, 3 et 5.

POURQUOI CE FICHIER EXISTE. Les spécifications des tests 2, 3 et 5 énoncent
**deux** critères, pas un :

  1. « Jahressumme : Mittelwert +/- max. Abweichung der Referenzprogramme » —
     c'est la bande annuelle, déjà figée par `build_sia_reference.py` ;
  2. « Die Häufigkeitsverteilung muss im Streubereich der Referenzprogramme
     liegen » — la distribution horaire doit rester dans la dispersion des
     programmes de référence.

Le second n'avait jamais été extrait. Sans lui, un verdict « conforme » ne
porterait que sur la moitié des critères du test.

CE PARAGRAPHE AFFIRMAIT LE CONTRAIRE, ET IL ÉTAIT FAUX. Il disait que les
tests 4 et 6 n'ont ni feuille de classes ni feuille de distribution, « et
c'est un constat, pas un oubli ». C'était un oubli, et il tenait à une seule
lettre : leurs classeurs écrivent la feuille `Haeufigkeitskassen`, sans le
« l » de `Haeufigkeitsklassen` que portent les tests 2, 3 et 5. Une faute de
frappe dans les fichiers officiels, prise pour une absence.

CE QUI EST VÉRIFIÉ, le 2026-08-10, en ouvrant les classeurs :

  * `Resultaterfassung Test4.xlsx` et `Resultaterfassung_Test6.xlsx` portent
    tous deux une feuille `Haeufigkeitskassen` de 23 lignes, structurée comme
    celle du Test 2 : un index de classe, puis une borne par grandeur ;
  * leur `Zusammenfassung` porte une section
    « Stündliche Häufigkeitsverteilung » (Test 4 : ligne 19) suivie de blocs
    par grandeur — nom, unité et programmes, ligne `Klassen`, puis les
    effectifs de chaque programme de référence. C'est exactement la structure
    que ce script sait déjà lire.

La clarification de l'autorité du 2026-08-10
(`traceability/sia4010-authority-clarification-2026-08-10.json`, décision
`SIA4010-TEST4-6-DISTRIBUTION-PRESENCE`) dit la même chose.

Ces deux tests sont donc À PORTÉE et restent À FAIRE : leur disposition n'est
pas encore relevée dans `DISPOSITIONS`, et ce script ne devine jamais une
disposition — voir le commentaire de cette table. `TESTS_AVEC_DISTRIBUTION`
les exclut encore pour cette raison, et pour cette raison seulement.

CE QUE LE CLASSEUR NE FAIT PAS, ET QUE CE SCRIPT NE FERA DONC PAS NON PLUS.
Les feuilles « Verteilung » sont des **graphiques**, pas des tableaux : elles
tracent les 8 variantes de référence plus le programme testé, et **aucune
bande n'est calculée nulle part**. Le jugement est visuel dans le classeur
officiel. Ce script fige donc les EFFECTIFS par classe — des faits — et laisse
le critère explicitement non établi. Choisir une formule de bande ici
reviendrait à inventer le critère.

Usage :
    python scripts/build_sia_distribution_reference.py [numero...] [--ecrire]
"""

from __future__ import print_function

import io
import json
import os
import sys

import openpyxl
from openpyxl.utils import column_index_from_string, get_column_letter

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))

_DOSSIER_SIA = os.environ.get(
    'SIA_4010_DOSSIER', os.path.join(_RACINE, 'SIA_4010_geteilter_Link'))

_SORTIE = os.path.join(_RACINE, 'refs', 'reference-data')

#: Tests dont la disposition a été RELEVÉE dans `DISPOSITIONS`, et dont les
#: effectifs sont donc extractibles. Les tests 4, 6 et 7 ont rejoint cette
#: liste le 2026-08-12, quand leur disposition a été lue.
#:
#: EXTRACTIBLE N'EST PAS OPPOSABLE. Cette liste dit d'où l'on sait lire des
#: effectifs, pas où un critère de distribution s'applique. Les spécifications
#: des tests 4, 6 et 7 ne comportent aucune section « Testkriterien » — zéro
#: occurrence de `Testkriterien`, `Streubereich`, `Abweichung` ni
#: `Häufigkeitsverteilung`, vérifié le 2026-08-12 après s'être assuré que le
#: texte des trois PDF s'extrait bien. La question de savoir si le critère de
#: distribution leur est opposable est posée à la sous-commission et n'a pas
#: de réponse. Le moteur `sia_distributions_engine` garde donc sa propre
#: liste : figer un fait n'autorise pas à en tirer un verdict.
TESTS_AVEC_DISTRIBUTION = (2, 3, 4, 5, 6, 7)

#: Tests dont les classeurs portent des distributions, disposition relevée
#: ou non. Sert à distinguer « pas de distribution » de « pas encore
#: extraite » — la confusion des deux est ce qui a fait écrire pendant
#: des semaines que les tests 4 et 6 n'en avaient pas, et l'a fait écrire
#: à la SIA le 2026-08-07, qui l'a relevé.
TESTS_PORTANT_DES_DISTRIBUTIONS = (2, 3, 4, 5, 6, 7)

#: Heures d'une année. Le classeur totalise par colonne ; les écarts d'une ou
#: deux heures observés (8759, 8732) sont RÉELS et conservés tels quels.
HEURES_ANNEE = 8760

#: Disposition LUE sur chaque classeur, jamais supposée. Les trois diffèrent —
#: c'est en les croyant semblables qu'on s'est trompé quatre fois sur les
#: sommes annuelles.
#:
#:   ligne_cas        : ligne portant l'identifiant de cas, en tête de bloc
#:   ligne_grandeur   : ligne portant « grandeur, unité »
#:   ligne_unite      : ligne portant l'unité SEULE, quand le classeur ne la
#:                      met pas dans la cellule de grandeur. Absente pour les
#:                      tests 2, 3 et 5, où l'unité suit la virgule.
#:   ligne_programmes : ligne portant les noms de programmes
#:   ligne_classes    : ligne portant le mot « Klassen »
#:   colonne_index    : colonne d'index de classe commune à tous les blocs,
#:                      ou None si chaque bloc porte ses propres bornes
#:
#: TROIS FAMILLES DE DISPOSITION, relevées le 2026-08-12 :
#:
#:   tests 2, 3, 5 : « Grandeur, unité » dans UNE cellule, et une ligne de cas
#:                   portant un identifiant (« Alle », « Test 3 A »...) ;
#:   tests 4, 6    : grandeur et unité sur DEUX lignes, la ligne d'unité
#:                   portant aussi les noms de programmes. Aucun identifiant
#:                   de cas : ces tests n'ont qu'un cas ;
#:   test 7        : comme 4 et 6, mais la cellule de grandeur répète l'unité
#:                   après une virgule. Les deux sources sont lues et doivent
#:                   concorder — un désaccord fait refuser l'extraction.
DISPOSITIONS = {
    2: {
        'fichier': os.path.join('Test2', 'Resultaterfassung_Test2.xlsx'),
        'feuille': u'Zusammenfassung',
        'ligne_cas': 28,
        'ligne_grandeur': 29,
        'ligne_programmes': 30,
        'ligne_classes': 31,
        'colonne_index': None,
        'classes_sia': ['2A', '2B', '4A', '4B'],
    },
    3: {
        'fichier': os.path.join('Test3', 'Resultaterfassung_Test3.xlsx'),
        'feuille': u'Zusammenfassung',
        'ligne_cas': 30,
        'ligne_grandeur': 31,
        'ligne_programmes': 32,
        'ligne_classes': 33,
        'colonne_index': None,
        'classes_sia': ['2A', '2B', '4A', '4B'],
    },
    5: {
        'fichier': os.path.join('Test5', 'Resultaterfassung_Test5.xlsx'),
        'feuille': u'Zusammenfassung',
        'ligne_cas': 20,
        'ligne_grandeur': 21,
        'ligne_programmes': 22,
        'ligne_classes': 23,
        # Test 5 porte l'index de classe en colonne A, commune a tous les
        # blocs, et la borne dans la 1re colonne de chaque bloc.
        'colonne_index': 1,
        'classes_sia': ['3', '4A', '4B'],
    },
    # Relevés le 2026-08-12 en ouvrant les classeurs. La section porte le titre
    # « Stündliche Häufigkeitsverteilung » en colonne A : Test 4 ligne 19,
    # Test 6 ligne 22, Test 7 ligne 31. Aucune ligne de cas : ces trois tests
    # n'ont qu'un cas, et `_reserves` le dira au lieu de le déduire.
    4: {
        'fichier': os.path.join('Test4', 'Resultaterfassung Test4.xlsx'),
        'feuille': u'Zusammenfassung',
        'ligne_cas': 20,
        'ligne_grandeur': 21,
        'ligne_unite': 22,
        'ligne_programmes': 22,
        'ligne_classes': 23,
        'colonne_index': 1,
        'classes_sia': ['3', '4A', '4B'],
    },
    6: {
        'fichier': os.path.join('Test6', 'Resultaterfassung_Test6.xlsx'),
        'feuille': u'Zusammenfassung',
        'ligne_cas': 23,
        'ligne_grandeur': 24,
        'ligne_unite': 25,
        'ligne_programmes': 25,
        'ligne_classes': 26,
        'colonne_index': 1,
        'classes_sia': ['3', '4A', '4B'],
    },
    7: {
        'fichier': os.path.join('Test7', 'Resultaterfassung Test7.xlsx'),
        'feuille': u'Zusammenfassung',
        'ligne_cas': 31,
        'ligne_grandeur': 32,
        'ligne_unite': 33,
        'ligne_programmes': 33,
        'ligne_classes': 34,
        'colonne_index': 1,
        'classes_sia': ['4A', '4B', '5'],
    },
}

#: Mot qui marque, sur `ligne_classes`, la première colonne d'un bloc.
MARQUEUR_BLOC = u'Klassen'

#: Libellé de la ligne de contrôle, sous les classes.
MARQUEUR_TOTAL = u'Total'


class ExtractionRefusee(RuntimeError):
    u"""Levée dès qu'une valeur ne peut pas être établie avec certitude."""


def _texte(feuille, ligne, colonne):
    u"""Valeur texte d'une cellule, nettoyée.

    Args:
        feuille: Feuille openpyxl.
        ligne: Numéro de ligne.
        colonne: Index de colonne.

    Returns:
        str | None: Texte nettoyé, ou `None` si la cellule n'en porte pas.
    """
    valeur = feuille.cell(ligne, colonne).value
    if isinstance(valeur, str) and valeur.strip():
        return valeur.strip()
    return None


def _entier(feuille, ligne, colonne):
    u"""Valeur entière d'une cellule, ou `None`.

    Args:
        feuille: Feuille openpyxl.
        ligne: Numéro de ligne.
        colonne: Index de colonne.

    Returns:
        int | None: Effectif, ou `None` si la cellule n'est pas numérique.
    """
    valeur = feuille.cell(ligne, colonne).value
    if isinstance(valeur, bool) or valeur is None:
        return None
    if isinstance(valeur, int):
        return valeur
    if isinstance(valeur, float) and valeur == int(valeur):
        return int(valeur)
    return None


def _colonnes_de_bloc(feuille, disposition):
    u"""Repère les colonnes qui ouvrent un bloc de distribution.

    Args:
        feuille: Feuille `Zusammenfassung`.
        disposition: Entrée de `DISPOSITIONS`.

    Returns:
        list[int]: Index des colonnes portant « Klassen », dans l'ordre.

    Raises:
        ExtractionRefusee: Si aucun bloc n'est trouvé — la disposition
            déclarée ne correspond alors pas au classeur, et poursuivre
            produirait un référentiel vide qui se lirait comme « pas de
            distribution ».
    """
    ligne = disposition['ligne_classes']
    blocs = [c for c in range(1, feuille.max_column + 1)
             if _texte(feuille, ligne, c) == MARQUEUR_BLOC]
    if not blocs:
        raise ExtractionRefusee(
            u'aucun bloc « %s » sur la ligne %d : la disposition déclarée ne '
            u'correspond pas au classeur.' % (MARQUEUR_BLOC, ligne))
    return blocs


def _bornes_du_bloc(feuille, disposition, colonne_bloc):
    u"""Lit les bornes de classe d'un bloc, et la ligne de contrôle.

    Args:
        feuille: Feuille `Zusammenfassung`.
        disposition: Entrée de `DISPOSITIONS`.
        colonne_bloc: Colonne portant « Klassen ».

    LA LIGNE DE CONTRÔLE N'EST PAS TOUJOURS ÉTIQUETÉE. Le Test 2 écrit
    « Total » en colonne A ; le Test 3 laisse la cellule vide et pose
    simplement les totaux sous la dernière classe. On la repère donc par
    position — la ligne qui suit la dernière classe — et la **vérification par
    la somme** (`_controler_totaux`) valide cette détection : si la ligne
    retenue n'est pas la bonne, les sommes ne tomberont pas juste et
    l'extraction sera refusée. Aucune détection n'est crue sur parole.

    Returns:
        tuple: `(lignes_de_classe, bornes, ligne_total)`.

    Raises:
        ExtractionRefusee: Si aucune classe n'est trouvée sous le bloc.
    """
    depart = disposition['ligne_classes'] + 1
    colonne_libelle = disposition.get('colonne_index') or colonne_bloc
    lignes, bornes = [], []
    ligne_total = None
    for ligne in range(depart, feuille.max_row + 1):
        if _texte(feuille, ligne, 1) == MARQUEUR_TOTAL:
            ligne_total = ligne
            break
        borne = _entier(feuille, ligne, colonne_bloc)
        if borne is None and _entier(feuille, ligne, colonne_libelle) is None:
            break
        lignes.append(ligne)
        bornes.append(borne)
    if not lignes:
        raise ExtractionRefusee(
            u'aucune classe sous le bloc %s : la disposition déclarée ne '
            u'correspond pas au classeur.' % get_column_letter(colonne_bloc))
    if ligne_total is None:
        ligne_total = lignes[-1] + 1
    return lignes, bornes, ligne_total


def _contributeurs(feuille, disposition, colonne_bloc, colonne_fin,
                   ligne_total):
    u"""Repère les colonnes de programmes ayant réellement soumis ce cas.

    LE PIÈGE. Une colonne peut être pleine de zéros parce que le programme
    n'a pas soumis ce cas, pas parce qu'il a compté zéro heure. La ligne
    « Total » tranche : elle vaut ~8760 pour un contributeur réel, 0 sinon.
    Compter les zéros comme des mesures fausserait toute la dispersion.

    Args:
        feuille: Feuille `Zusammenfassung`.
        disposition: Entrée de `DISPOSITIONS`.
        colonne_bloc: Colonne portant « Klassen ».
        colonne_fin: Première colonne du bloc suivant (exclue).
        ligne_total: Ligne de contrôle.

    Returns:
        list[dict]: Un descripteur par colonne contributrice.
    """
    ligne_programmes = disposition['ligne_programmes']
    retenus = []
    for colonne in range(colonne_bloc + 1, colonne_fin):
        total = _entier(feuille, ligne_total, colonne)
        if not total:
            continue
        retenus.append({
            'colonne': get_column_letter(colonne),
            'programme': _texte(feuille, ligne_programmes, colonne),
            # Backward-compatible name: this is the sum of the displayed
            # classes, not the size of the underlying annual source series.
            'total_heures': total,
            'heures_dans_classes': total,
            'heures_hors_classes': max(0, HEURES_ANNEE - total),
            'heures_source_attendues': HEURES_ANNEE,
        })
    return retenus


def _grandeur_et_unite(libelle):
    u"""Sépare « Grandeur, unité » en deux.

    Args:
        libelle: Texte de la ligne de grandeur.

    Returns:
        tuple[str, str | None]: Grandeur et unité, l'unité pouvant manquer.
    """
    if libelle and ',' in libelle:
        grandeur, unite = libelle.rsplit(',', 1)
        return grandeur.strip(), unite.strip()
    return (libelle or u'').strip(), None


def extraire(numero_test):
    u"""Extrait les distributions de référence d'un test.

    Args:
        numero_test: 2, 3 ou 5.

    Returns:
        dict: Structure prête à figer.

    Raises:
        ExtractionRefusee: Sur toute incohérence entre le relevé et les
            contrôles du classeur.
    """
    if numero_test not in DISPOSITIONS:
        raise ExtractionRefusee(
            u'test %r : aucune disposition relevée. Tests dont la disposition '
            u'est lue : %s. Ne jamais en ajouter un sans avoir ouvert son '
            u'classeur : une disposition supposée extrait au hasard.'
            % (numero_test, sorted(DISPOSITIONS)))

    disposition = DISPOSITIONS[numero_test]
    chemin = os.path.join(_DOSSIER_SIA, disposition['fichier'])
    if not os.path.isfile(chemin):
        raise ExtractionRefusee(u'classeur introuvable : %s' % chemin)

    classeur = openpyxl.load_workbook(chemin, data_only=True)
    feuille = classeur[disposition['feuille']]

    colonnes = _colonnes_de_bloc(feuille, disposition)
    distributions = []
    for rang, colonne_bloc in enumerate(colonnes):
        suivante = (colonnes[rang + 1] if rang + 1 < len(colonnes)
                    else feuille.max_column + 1)
        distributions.append(
            _extraire_bloc(feuille, disposition, colonne_bloc, suivante))

    return {
        u'test': numero_test,
        u'critere': u'Häufigkeitsverteilung : « muss im Streubereich der '
                    u'Referenzprogramme liegen » (Spezifikation_Test%d.pdf, '
                    u'Testkriterien)' % numero_test,
        u'statut_critere': u'CONFIRME_AUTORITE_2026-08-10',
        u'pourquoi_non_calcule':
            u'Les feuilles « Verteilung » sont des GRAPHIQUES : elles tracent '
            u'les variantes de référence et le programme testé, sans calculer '
            u'aucune bande. Aucune cellule du classeur ne définit le '
            u'Streubereich d\'une distribution. La clarification écrite du '
            u'2026-08-10 définit la règle : enveloppe min/max des programmes '
            u'de référence, classe par classe.',
        u'classes_concernees': disposition['classes_sia'],
        u'source': {
            u'fichier': disposition['fichier'],
            u'feuille': disposition['feuille'],
            u'lignes_de_structure': _lignes_de_structure(disposition),
        },
        u'nb_distributions': len(distributions),
        u'reserves': _reserves(distributions),
        u'distributions': distributions,
    }


def _lignes_de_structure(disposition):
    u"""Consigne les lignes réellement lues, pour que la source soit rejouable.

    `unite` n'apparaît que pour les dispositions qui en ont une : la clé
    absente signifie « l'unité suit la virgule dans la cellule de grandeur »,
    pas « on ne sait pas ».

    Args:
        disposition: Entrée de `DISPOSITIONS`.

    Returns:
        dict: Numéros de ligne, par rôle.
    """
    lignes = {
        u'cas': disposition['ligne_cas'],
        u'grandeur': disposition['ligne_grandeur'],
        u'programmes': disposition['ligne_programmes'],
        u'classes': disposition['ligne_classes'],
    }
    if disposition.get('ligne_unite') is not None:
        lignes[u'unite'] = disposition['ligne_unite']
    return lignes


def _reserves(distributions):
    u"""Rédige les réserves à partir des données extraites, pas de mémoire.

    Une réserve écrite à la main se périme dès que le classeur change. Celles-ci
    sont recalculées à chaque extraction : si le motif disparaît, la réserve
    disparaît avec lui.

    Args:
        distributions: Blocs extraits.

    Returns:
        list[str]: Réserves, éventuellement vide.
    """
    reserves = []

    sans_cas = [b['colonne_bloc'] for b in distributions if not b['cas']]
    if sans_cas:
        reserves.append(
            u'Bloc(s) %s : le classeur ne porte AUCUN identifiant de cas sur '
            u'la ligne prévue. La spécification range ces grandeurs sous un '
            u'cas précis, mais le classeur ne le dit pas : le champ reste nul '
            u'plutôt que d\'être comblé par déduction.'
            % u', '.join(sans_cas))

    conflits = [b['conflit_unite'] for b in distributions
                if b.get('conflit_unite')]
    for conflit in conflits:
        reserves.append(
            u'Bloc %s : le classeur écrit deux unités contradictoires pour la '
            u'même grandeur — « %s » dans la cellule de grandeur, « %s » sur la '
            u'ligne d\'unité %d. Les effectifs sont conservés car ils ne '
            u'dépendent pas de cette étiquette ; l\'unité reste nulle. Trancher '
            u'ici corrigerait un défaut du classeur officiel à la place de son '
            u'auteur. À signaler à la sous-commission.'
            % (conflit['colonne_bloc'], conflit['unite_cellule_grandeur'],
               conflit['unite_ligne_unite'], conflit['ligne_unite']))

    totaux = sorted(set(c['total_heures'] for b in distributions
                        for c in b['contributeurs']))
    hors_classes = [t for t in totaux if t < HEURES_ANNEE]
    if hors_classes:
        reserves.append(
            u'Totaux affichés dans les classes : %s. La SIA a confirmé le '
            u'2026-08-10 que les écarts à %d ne sont pas des heures manquantes : '
            u'les autres valeurs sont hors des bornes définies par les classes. '
            u'Elles sont conservées comme compte hors classes et ne sont pas '
            u'ajoutées à la dernière classe.'
            % (u', '.join(str(t) for t in totaux), HEURES_ANNEE))

    reserves.append(
        u'Les effectifs sont des FAITS relevés cellule par cellule et '
        u'réconciliés avec la ligne de totaux du classeur. La bande '
        u'd\'acceptation min/max par classe est confirmée par la réponse '
        u'écrite du 2026-08-10.')
    return reserves


def _extraire_bloc(feuille, disposition, colonne_bloc, colonne_fin):
    u"""Extrait un bloc de distribution.

    Args:
        feuille: Feuille `Zusammenfassung`.
        disposition: Entrée de `DISPOSITIONS`.
        colonne_bloc: Colonne portant « Klassen ».
        colonne_fin: Première colonne du bloc suivant (exclue).

    Returns:
        dict: Distribution d'un couple (cas, grandeur).

    Raises:
        ExtractionRefusee: Si la somme des effectifs d'un contributeur ne
            reproduit pas son total déclaré. C'est le garde-fou : il a déjà
            attrapé quatre hypothèses fausses sur les sommes annuelles.
    """
    lignes, bornes, ligne_total = _bornes_du_bloc(
        feuille, disposition, colonne_bloc)
    contributeurs = _contributeurs(
        feuille, disposition, colonne_bloc, colonne_fin, ligne_total)

    grandeur, unite = _grandeur_et_unite(
        _texte(feuille, disposition['ligne_grandeur'], colonne_bloc))
    ligne_unite = disposition.get('ligne_unite')
    conflit_unite = None
    if ligne_unite is not None:
        unite_propre = _texte(feuille, ligne_unite, colonne_bloc)
        if unite is None:
            # Tests 4 et 6 : la cellule de grandeur ne porte pas l'unité.
            unite = unite_propre
        elif unite_propre and unite_propre != unite:
            # Test 7, bloc W au 2026-08-12 : la cellule de grandeur annonce
            # « kW » et la ligne d'unité « °C ». Un seul bloc sur dix-sept.
            #
            # Les EFFECTIFS ne dépendent pas de cette étiquette : refuser le
            # bloc perdrait des faits pour un désaccord de métadonnée. Choisir
            # l'une des deux sources reviendrait à trancher un défaut du
            # classeur officiel à la place de son auteur. L'unité reste donc
            # nulle et le conflit remonte en réserve, nommé.
            conflit_unite = {
                'colonne_bloc': get_column_letter(colonne_bloc),
                'unite_cellule_grandeur': unite,
                'unite_ligne_unite': unite_propre,
                'ligne_unite': ligne_unite,
            }
            unite = None

    effectifs = []
    for rang, ligne in enumerate(lignes):
        par_colonne = {}
        for contributeur in contributeurs:
            colonne = column_index_from_string(contributeur['colonne'])
            par_colonne[contributeur['colonne']] = _entier(
                feuille, ligne, colonne)
        effectifs.append({
            'ligne_classeur': ligne,
            'borne_superieure': bornes[rang],
            'par_colonne': par_colonne,
        })

    _controler_totaux(contributeurs, effectifs, colonne_bloc)

    bloc = {
        'cas': _texte(feuille, disposition['ligne_cas'], colonne_bloc),
        'grandeur': grandeur,
        'unite': unite,
        'colonne_bloc': get_column_letter(colonne_bloc),
        'nb_classes': len(lignes),
        'ligne_total': ligne_total,
        'contributeurs': contributeurs,
        'effectifs': effectifs,
    }
    # Clé ajoutée seulement quand il y a un conflit : les référentiels des
    # tests 2, 3 et 5 restent ainsi identiques au bit près, aucun n'ayant de
    # ligne d'unité. Une preuve figée ne se réécrit pas pour une clé nulle.
    if conflit_unite is not None:
        bloc['conflit_unite'] = conflit_unite
    return bloc


def _controler_totaux(contributeurs, effectifs, colonne_bloc):
    u"""Confronte la somme des effectifs au total déclaré par le classeur.

    Args:
        contributeurs: Descripteurs de colonnes.
        effectifs: Effectifs par classe.
        colonne_bloc: Colonne du bloc, pour le message.

    Raises:
        ExtractionRefusee: Sur le moindre écart. Un effectif mal lu donnerait
            une distribution plausible et fausse.
    """
    for contributeur in contributeurs:
        lettre = contributeur['colonne']
        somme = sum(e['par_colonne'][lettre] or 0 for e in effectifs)
        if somme != contributeur['total_heures']:
            raise ExtractionRefusee(
                u'bloc %s, colonne %s : somme des classes = %d, total déclaré '
                u'par le classeur = %d. Écart de %d.'
                % (get_column_letter(colonne_bloc), lettre, somme,
                   contributeur['total_heures'],
                   somme - contributeur['total_heures']))


def _chemin_sortie(numero_test):
    u"""Chemin du référentiel figé d'un test.

    Args:
        numero_test: Numéro du test SIA.

    Returns:
        str: Chemin absolu.
    """
    return os.path.join(_SORTIE, 'test-%d.distributions.ref.json' % numero_test)


def main(arguments):
    u"""Point d'entrée en ligne de commande.

    Args:
        arguments: Numéros de tests, et `--ecrire`.

    Returns:
        int: 0 si tout s'est bien passé, 1 sinon.
    """
    demandes = [int(a) for a in arguments if a.isdigit()]
    tests = demandes or list(TESTS_AVEC_DISTRIBUTION)
    code = 0
    for numero in tests:
        try:
            donnees = extraire(numero)
        except ExtractionRefusee as erreur:
            print(u'Test %d : REFUSE — %s' % (numero, erreur))
            code = 1
            continue
        heures = set()
        for bloc in donnees['distributions']:
            for contributeur in bloc['contributeurs']:
                heures.add(contributeur['total_heures'])
        print(u'Test %d : %d distributions, %d classes, totaux horaires %s'
              % (numero, donnees['nb_distributions'],
                 donnees['distributions'][0]['nb_classes'] if
                 donnees['distributions'] else 0,
                 sorted(heures)))
        for bloc in donnees['distributions'][:4]:
            print(u'    %-12s %-42s %d contributeur(s)'
                  % (bloc['cas'], (bloc['grandeur'] or u'')[:42],
                     len(bloc['contributeurs'])))
        if len(donnees['distributions']) > 4:
            print(u'    ... et %d autres'
                  % (len(donnees['distributions']) - 4))
        if '--ecrire' in arguments:
            chemin = _chemin_sortie(numero)
            with io.open(chemin, 'w', encoding='utf-8') as flux:
                flux.write(json.dumps(donnees, ensure_ascii=False, indent=1))
                flux.write(u'\n')
            print(u'    écrit : %s' % os.path.relpath(chemin, _RACINE))
        print()
    return code


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
