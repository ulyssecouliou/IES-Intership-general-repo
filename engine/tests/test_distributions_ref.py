# -*- coding: utf-8 -*-
u"""Tests des distributions de fréquence de référence — tests SIA 2, 3 et 5.

Le second critère des spécifications 2, 3 et 5 — « Die Häufigkeitsverteilung
muss im Streubereich der Referenzprogramme liegen » — n'avait jamais été
extrait. Ces tests gardent le référentiel qui le porte.

Ils visent surtout ce qu'une extraction plausible mais fausse produirait :
compter une colonne de zéros comme une mesure, rater la ligne de totaux, ou
inventer une bande que le classeur ne calcule nulle part.
"""

import io
import json
import os

import pytest

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))
_DOSSIER = os.path.join(_RACINE, 'refs', 'reference-data')

#: Tests dont les effectifs de distribution sont figés. Les tests 4, 6 et 7
#: ont rejoint la liste le 2026-08-12, quand la disposition de leur classeur a
#: été relevée. Tous les contrôles d'intégrité de ce fichier s'y appliquent.
TESTS = (2, 3, 4, 5, 6, 7)

#: Tests dont la spécification ne comporte AUCUNE section « Testkriterien ».
#: Vérifié le 2026-08-12 sur les trois PDF, après s'être assuré que leur texte
#: s'extrait bien : zéro occurrence de `Testkriterien`, `Streubereich`,
#: `Abweichung` ni `Häufigkeitsverteilung`.
#:
#: CE N'EST PAS « PAS DE DISTRIBUTION ». Leurs classeurs en portent, et la
#: confusion des deux est ce qui a fait affirmer le contraire à la SIA le
#: 2026-08-07. Ces trois tests ont des effectifs figés ; savoir si le critère
#: de distribution leur est opposable est une question ouverte auprès de la
#: sous-commission.
TESTS_SANS_TESTKRITERIEN = (4, 6, 7)


def _charger(numero):
    chemin = os.path.join(_DOSSIER, 'test-%d.distributions.ref.json' % numero)
    if not os.path.exists(chemin):
        pytest.skip(u'référentiel absent : '
                    u'scripts/build_sia_distribution_reference.py')
    with io.open(chemin, encoding='utf-8') as flux:
        return json.load(flux)


@pytest.fixture(scope='module', params=TESTS)
def reference(request):
    return _charger(request.param)


# --------------------------------------------------------------------------
# Le critère n'est pas inventé
# --------------------------------------------------------------------------

def test_le_critere_est_confirme_par_lautorite(reference):
    """Le classeur ne calcule pas la bande, mais la SIA a confirmé min/max."""
    assert reference['statut_critere'] == 'CONFIRME_AUTORITE_2026-08-10'
    assert 'GRAPHIQUES' in reference['pourquoi_non_calcule']
    assert 'min/max' in reference['pourquoi_non_calcule']


def test_le_critere_cite_sa_source(reference):
    """Règle de traçabilité : chaque contrôle cite son article."""
    assert 'Streubereich' in reference['critere']
    assert 'Spezifikation_Test' in reference['critere']


def test_aucune_bande_nest_publiee(reference):
    """Si une clé de bande apparaissait, quelqu'un l'aurait calculée sans
    fondement. Le référentiel ne doit porter que des effectifs."""
    texte = json.dumps(reference, ensure_ascii=False).lower()
    for interdit in ('"borne_inf', '"borne_sup_bande', '"moyenne"',
                     '"ecart_max"', '"bande"'):
        assert interdit not in texte, interdit


# --------------------------------------------------------------------------
# Les effectifs sont réconciliés avec le classeur
# --------------------------------------------------------------------------

def test_chaque_contributeur_totalise_ce_que_le_classeur_annonce(reference):
    """Le garde-fou principal. Il valide DEUX choses d'un coup : la lecture
    des effectifs, et la détection de la ligne de totaux — qui n'est pas
    étiquetée dans le Test 3."""
    for bloc in reference['distributions']:
        for contributeur in bloc['contributeurs']:
            lettre = contributeur['colonne']
            somme = sum(e['par_colonne'][lettre] or 0
                        for e in bloc['effectifs'])
            assert somme == contributeur['total_heures'], (
                reference['test'], bloc['colonne_bloc'], lettre)


def test_aucune_colonne_de_zeros_nest_retenue(reference):
    """Une colonne pleine de zéros signale un programme qui n'a PAS soumis ce
    cas, pas un programme ayant compté zéro heure. La compter comme une mesure
    fausserait toute la dispersion."""
    for bloc in reference['distributions']:
        for contributeur in bloc['contributeurs']:
            assert contributeur['total_heures'] > 0


def test_les_effectifs_ne_sont_jamais_negatifs(reference):
    for bloc in reference['distributions']:
        for effectif in bloc['effectifs']:
            for valeur in effectif['par_colonne'].values():
                assert valeur is None or valeur >= 0


def test_tous_les_blocs_ont_le_meme_nombre_de_classes(reference):
    """Les classes viennent d'une feuille commune : un bloc qui en aurait un
    nombre différent signalerait une lecture décalée."""
    nombres = set(bloc['nb_classes'] for bloc in reference['distributions'])
    assert len(nombres) == 1, nombres


#: Borne « sans limite haute », écrite ±9999 par le classeur : `9999` pour une
#: grandeur positive, `-9999` pour une grandeur négative comme une puissance
#: évacuée.
#:
#: CE N'EST PAS UNE CLASSE VIDE. Un test l'a supposé le 2026-08-12 et les
#: données l'ont démenti : la première classe ±9999 d'un bloc capte les heures
#: qui dépassent la dernière borne réelle — 3, 6 ou 7 heures selon les blocs
#: des tests 4, 5 et 7. Les ±9999 qui la suivent sont, eux, à zéro. La
#: garantie sur les effectifs reste la réconciliation avec la ligne de totaux
#: du classeur, pas une hypothèse sur cette borne.
BORNE_SANS_LIMITE_HAUTE = 9999


def test_les_bornes_sont_monotones(reference):
    """Des bornes désordonnées signaleraient une colonne mal repérée.

    MONOTONES, PAS CROISSANTES. Ce test exigeait des bornes croissantes, ce
    qui n'est vrai que d'une grandeur positive. Le Test 6 porte
    « Leistung Wärmeabfuhr WRG », une puissance ÉVACUÉE donc négative, dont
    les classes descendent : 100, -1000, -2000 ... -10000. Exiger la
    croissance rejetait une lecture correcte d'un classeur correct.

    Les bornes ±9999 sont écartées du contrôle : elles signifient « sans
    limite haute » et rompraient la monotonie sans rien signaler. Elles
    portent de vrais effectifs — voir `BORNE_SANS_LIMITE_HAUTE`.
    """
    for bloc in reference['distributions']:
        bornes = [e['borne_superieure'] for e in bloc['effectifs']
                  if e['borne_superieure'] is not None
                  and abs(e['borne_superieure']) != BORNE_SANS_LIMITE_HAUTE]
        assert bornes == sorted(bornes) or bornes == sorted(bornes,
                                                            reverse=True), (
            u'bloc %s : bornes ni croissantes ni décroissantes : %s'
            % (bloc['colonne_bloc'], bornes))


# --------------------------------------------------------------------------
# Ce que le relevé dit de lui-même
# --------------------------------------------------------------------------

def test_les_heures_hors_classes_sont_explicites(reference):
    """Un total affiché court signifie hors classes, pas série incomplète."""
    totaux = set(c['total_heures'] for bloc in reference['distributions']
                 for c in bloc['contributeurs'])
    if any(t < 8760 for t in totaux):
        texte = u' '.join(reference['reserves'])
        assert u'8760' in texte
        assert u'heures manquantes' in texte
        for bloc in reference['distributions']:
            for contributeur in bloc['contributeurs']:
                assert contributeur['heures_dans_classes'] == contributeur['total_heures']
                assert (
                    contributeur['heures_dans_classes']
                    + contributeur['heures_hors_classes']
                    == contributeur['heures_source_attendues']
                )


def test_un_bloc_sans_cas_est_signale(reference):
    """Le Test 5 porte un bloc que le classeur ne rattache à aucun cas. Le
    champ reste nul, et la réserve le dit."""
    sans_cas = [b for b in reference['distributions'] if not b['cas']]
    if sans_cas:
        assert any('identifiant de cas' in r for r in reference['reserves'])


def test_les_reserves_rappellent_la_bande_confirmee(reference):
    assert any('min/max' in r for r in reference['reserves'])


def test_chaque_bloc_nomme_sa_grandeur(reference):
    for bloc in reference['distributions']:
        assert bloc['grandeur'], bloc['colonne_bloc']


def test_la_source_est_tracable(reference):
    source = reference['source']
    assert source['fichier'].endswith('.xlsx')
    assert source['feuille']
    lignes = source['lignes_de_structure']
    assert {'cas', 'grandeur', 'programmes', 'classes'} <= set(lignes)
    # `unite` n'est présent que pour les dispositions dont le classeur met
    # l'unité sur sa propre ligne (tests 4, 6, 7). Son absence signifie
    # « l'unité suit la virgule », pas « on ne sait pas ».
    assert set(lignes) <= {
        'cas', 'grandeur', 'programmes', 'classes', 'unite'}
    assert all(isinstance(v, int) and v > 0 for v in lignes.values())


# --------------------------------------------------------------------------
# Portée
# --------------------------------------------------------------------------

@pytest.mark.parametrize('numero', TESTS_SANS_TESTKRITERIEN)
def test_les_tests_sans_testkriterien_ont_bien_des_effectifs(numero):
    """L'inverse de ce que ce fichier affirmait avant le 2026-08-12.

    Ces trois tests n'énoncent aucun critère dans leur spécification, et
    leurs classeurs tabulent pourtant des distributions horaires. Figer les
    effectifs ne dit rien de leur opposabilité ; ne pas les figer disait,
    à tort, qu'ils n'existaient pas.
    """
    chemin = os.path.join(_DOSSIER,
                          'test-%d.distributions.ref.json' % numero)
    assert os.path.exists(chemin), (
        u'produire avec scripts/build_sia_distribution_reference.py %d '
        u'--ecrire' % numero)


def test_lextracteur_refuse_un_test_sans_disposition_relevee():
    """Le refus porte sur la disposition non lue, jamais sur une absence
    supposée de distribution."""
    from scripts import build_sia_distribution_reference as extracteur
    with pytest.raises(extracteur.ExtractionRefusee,
                       match='aucune disposition relev'):
        extracteur.extraire(1)


def test_le_moteur_ne_gate_pas_ce_qui_est_seulement_extractible():
    """Un fait figé n'autorise pas un verdict.

    L'extracteur sait lire six tests ; le moteur n'en évalue que trois, ceux
    dont la spécification énonce le critère. Aligner l'un sur l'autre sans
    réponse de la sous-commission transformerait une donnée en critère.
    """
    from engine import sia_distributions_engine as moteur
    from scripts import build_sia_distribution_reference as extracteur
    assert set(moteur.TESTS_SUPPORTES) == {2, 3, 5}
    assert set(TESTS_SANS_TESTKRITERIEN).isdisjoint(moteur.TESTS_SUPPORTES)
    assert set(moteur.TESTS_SUPPORTES).issubset(
        extracteur.TESTS_AVEC_DISTRIBUTION)


@pytest.mark.parametrize('numero,attendu',
                         [(2, 22), (3, 16), (4, 11), (5, 16), (6, 10), (7, 17)])
def test_le_nombre_de_distributions_est_fige(numero, attendu):
    """54 distributions au total. Si le compte changeait, ce serait soit un
    classeur différent, soit une lecture décalée — les deux méritent un
    échec."""
    assert _charger(numero)['nb_distributions'] == attendu
