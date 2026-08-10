# -*- coding: utf-8 -*-
u"""Tests du générateur de matrices (`scripts/build_traceability_matrix.py`).

Une matrice de traçabilité est un document de CONTRÔLE : elle affirme qu'une
clause est couverte. Deux façons de la rendre nuisible, toutes deux vécues
dans ce dépôt :

* **écrire un chiffre au lieu de le compter.** La première version annonçait
  « un seul cas porte le critère pass/fail » — le moteur en rend trois. Le
  document affirmait donc, avec l'autorité d'un relevé, quelque chose de faux ;
* **écraser une rédaction.** La matrice du Test 7 est un audit indépendant de
  trois cents lignes, renvoyé non signé. Un générateur ne sait pas produire ce
  jugement ; l'écraser le détruit sans trace.

Ces deux dangers sont ce que ces tests surveillent.
"""

import io
import os

import pytest

from scripts import build_traceability_matrix as generateur


# --------------------------------------------------------------------------
# Ne jamais écraser une rédaction
# --------------------------------------------------------------------------

@pytest.fixture
def sortie(tmp_path, monkeypatch):
    monkeypatch.setattr(generateur, '_SORTIE', str(tmp_path))
    return str(tmp_path)


def _poser(dossier, nom, contenu):
    chemin = os.path.join(dossier, nom)
    with io.open(chemin, 'w', encoding='utf-8') as flux:
        flux.write(contenu)
    return chemin


def test_sans_fichier_existant_on_ecrit_a_la_place_attendue(sortie):
    chemin, redigee = generateur.chemin_de_sortie(1)
    assert chemin.endswith('test-1.matrix.md')
    assert redigee is False


def test_une_matrice_redigee_a_la_main_nest_pas_ecrasee(sortie):
    _poser(sortie, 'test-7.matrix.md', u'# Audit indépendant\n\nRENVOYÉE\n')
    chemin, redigee = generateur.chemin_de_sortie(7)
    assert redigee is True
    assert chemin.endswith('test-7.matrix.releve.md')


def test_le_releve_va_a_cote_sans_toucher_a_la_redaction(sortie):
    original = u'# Audit indépendant\n\nRENVOYÉE\n'
    ecrit = _poser(sortie, 'test-7.matrix.md', original)
    generateur.chemin_de_sortie(7)
    with io.open(ecrit, encoding='utf-8') as flux:
        assert flux.read() == original


@pytest.mark.parametrize('numero', [1, 2, 3, 4, 5, 6, 7])
def test_une_sortie_du_script_est_bien_reconnue_comme_sienne(sortie, numero):
    u"""LA RÉGRESSION VÉCUE. Le marqueur avait été pris dans la bannière
    d'en-tête — formulée différemment par `construire` et `construire_dedie`.
    Les tests 2 à 6 passaient donc pour des rédactions à la main, et leur
    matrice partait dans un fichier voisin à chaque exécution."""
    document = (generateur.construire_dedie(numero)
                if numero in generateur.TESTS_DEDIES
                else generateur.construire(numero))
    _poser(sortie, 'test-%d.matrix.md' % numero, document)
    chemin, redigee = generateur.chemin_de_sortie(numero)
    assert redigee is False, numero
    assert chemin.endswith('test-%d.matrix.md' % numero)


def test_le_marqueur_est_present_dans_les_deux_generateurs():
    u"""Contrôle direct de l'invariant dont dépend le test précédent."""
    assert generateur.MARQUE_GENEREE in generateur.construire(2)
    assert generateur.MARQUE_GENEREE in generateur.construire_dedie(1)
    assert generateur.MARQUE_GENEREE in generateur.construire_dedie(7)


# --------------------------------------------------------------------------
# Tests 1 et 7 : moteurs propres
# --------------------------------------------------------------------------

def test_les_tests_a_bandes_ne_passent_pas_par_le_generateur_dedie():
    u"""Leurs résultats n'ont pas la même forme : le forcer produirait une
    matrice qui parle de champs inexistants."""
    for numero in generateur.TESTS:
        with pytest.raises(ValueError):
            generateur.construire_dedie(numero)


def test_seuls_1_et_7_ont_un_moteur_dedie():
    assert generateur.TESTS_DEDIES == (1, 7)
    assert not set(generateur.TESTS) & set(generateur.TESTS_DEDIES)


def test_les_sept_tests_sont_couverts():
    couverts = set(generateur.TESTS) | set(generateur.TESTS_DEDIES)
    assert couverts == set(range(1, 8))


# --------------------------------------------------------------------------
# Le compte des porteuses est CALCULÉ
# --------------------------------------------------------------------------

def test_le_nombre_dentrees_porteuses_vient_du_moteur():
    u"""Le chiffre écrit à la main était faux : trois entrées portent le
    critère, sur le seul cas 1E."""
    from engine import test1_engine as moteur
    resultat = moteur.evaluer_test1(moteur.charger_reference())
    porteuses = [e for e in resultat['cas'].values()
                 if e.get('type_controle') == 'critere_pass_fail']
    document = generateur.construire_dedie(1)
    assert u'**%d entrée(s) sur %d portent le critère pass/fail**' % (
        len(porteuses), len(resultat['cas'])) in document


def test_aucun_nombre_de_cas_nest_ecrit_en_toutes_lettres():
    u"""« un seul cas », « les dix-huit autres » : ces formulations sont
    exactement celles qui se sont périmées."""
    chemin = os.path.abspath(generateur.__file__).replace('.pyc', '.py')
    with io.open(chemin, encoding='utf-8') as flux:
        source = flux.read()
    for interdit in (u'dix-huit autres', u'Un seul cas porte',
                     u'seul cas porteur du'):
        assert interdit not in source, interdit


def test_le_cas_porteur_est_lu_et_non_affirme():
    from engine import test1_engine as moteur
    resultat = moteur.evaluer_test1(moteur.charger_reference())
    porteurs = sorted(set(e.get('cas') for e in resultat['cas'].values()
                          if e.get('type_controle') == 'critere_pass_fail'))
    document = generateur.construire_dedie(1)
    assert u'repose entièrement sur le(s) cas **%s**' % u', '.join(porteurs) \
        in document


# --------------------------------------------------------------------------
# Ce que la matrice ne doit jamais dire
# --------------------------------------------------------------------------

@pytest.mark.parametrize('numero', [1, 7])
def test_aucune_matrice_ne_se_signe_elle_meme(numero):
    u"""Règle 5 : la signature est indépendante. Un script qui se signerait
    ne vaudrait rien."""
    document = generateur.construire_dedie(numero)
    assert u'**non signé**' in document
    assert u'NON SIGNÉE' in document


@pytest.mark.parametrize('numero', [1, 7])
def test_aucune_matrice_nannonce_une_validation(numero):
    document = generateur.construire_dedie(numero)
    for interdit in (u'validé', u'conforme', u'PASS'):
        assert interdit not in document, (numero, interdit)


def test_la_matrice_du_test_1_dit_combien_de_controles_restent_non_evalues():
    from engine import test1_engine as moteur
    verdict = moteur.evaluer_test1(
        moteur.charger_reference()).get('verdict_test1') or {}
    document = generateur.construire_dedie(1)
    assert u'%d contrôle(s) sur %d ne sont pas évalués' % (
        verdict.get('nb_periodes_non_evaluees', 0),
        verdict.get('nb_periodes_totales', 0)) in document


def test_la_matrice_du_test_7_nomme_sa_source_dirradiance():
    u"""Sans irradiance de Kloten, aucune grandeur du Test 7 n'est calculable.
    Le taire donnerait une matrice qui semble complète."""
    document = generateur.construire_dedie(7)
    assert u'Source d\'irradiance' in document


def test_les_classes_concernees_viennent_du_moteur():
    u"""SIA 4010:2023, tableau 63. Les retaper les périmerait."""
    from engine import test7_engine as moteur
    classes = moteur.evaluer_test7(
        moteur.charger_reference()).get('classes_concernees') or []
    document = generateur.construire_dedie(7)
    assert u', '.join(classes) in document


# --------------------------------------------------------------------------
# Chaîne logicielle : l'existence est contrôlée
# --------------------------------------------------------------------------

@pytest.mark.parametrize('numero', [1, 7])
def test_un_fichier_absent_est_signale_et_non_tu(numero):
    lignes = generateur._tableau_chaine_dediee(numero)
    assert any(u'| Rôle |' in ligne for ligne in lignes)
    for ligne in lignes[2:]:
        assert ligne.endswith(u'oui |') or ligne.endswith(u'**NON** |'), ligne


def test_la_chaine_du_test_1_cite_le_gbxml_et_limport():
    u"""Ce sont les deux maillons ajoutés cette semaine ; une matrice qui les
    ignorerait sous-déclarerait la couverture."""
    lignes = u'\n'.join(generateur._tableau_chaine_dediee(1))
    assert 've_adapter/gbxml_test1.py' in lignes
    assert 'scripts/importer_geometrie_test1.py' in lignes
