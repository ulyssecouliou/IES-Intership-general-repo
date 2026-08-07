# -*- coding: utf-8 -*-
u"""Tests de la sélection de classe et du diagnostic (`ui/selection_classe.py`).

Deux dangers guettent ce module, et les tests visent surtout eux :

* qu'une classe **sans résultat** finisse par se lire comme conforme ;
* qu'un rapport client **filtré** laisse passer un test qui échoue, parce que
  le filtre l'aurait écarté.
"""

import pytest

from ui import selection_classe as sel


def _vue(test_id, couleur, critere=None):
    """Vue minimale, à la forme de `verdict_view`."""
    assemblee = {'test_id': test_id,
                 'verdict_global': {'couleur': couleur, 'texte': u'x',
                                    'article': u'y'}}
    if critere:
        assemblee['critere'] = {'statut': critere}
    return assemblee


# --------------------------------------------------------------------------
# Les classes viennent du tableau 63
# --------------------------------------------------------------------------

def test_les_huit_classes_sont_couvertes():
    assert set(sel.CLASSES) == set(sel.INTITULE_DES_CLASSES)
    assert len(sel.CLASSES) == 8


def test_la_classe_5_nexige_que_le_test_7():
    """SIA 4010:2023, tableau 63 : c'est la seule classe à un seul test."""
    assert sel.tests_de_la_classe('5') == ('7',)


def test_la_classe_4b_exige_les_sept_tests():
    assert len(sel.tests_de_la_classe('4B')) == 7


def test_une_classe_inconnue_leve_au_lieu_de_rendre_vide():
    """Un tuple vide se lirait comme « cette classe n'exige rien », le
    contraire de la vérité."""
    with pytest.raises(sel.ClasseInconnue, match='tableau 63'):
        sel.tests_de_la_classe('9Z')


def test_chaque_classe_a_un_intitule_lisible():
    for classe in sel.CLASSES:
        assert sel.intitule(classe) != classe


# --------------------------------------------------------------------------
# Le numéro de test se lit, ne se devine pas
# --------------------------------------------------------------------------

@pytest.mark.parametrize('identifiant,attendu', [
    ('1', 1), ('2A', 2), ('3A-F', 3), ('7', 7)])
def test_le_numero_est_extrait_du_prefixe(identifiant, attendu):
    """Le tableau 63 nomme certains tests par un sous-ensemble de cas ;
    le moteur raisonne par numéro."""
    assert sel._numero_du_test(identifiant) == attendu


def test_un_identifiant_sans_chiffre_ne_donne_pas_de_numero():
    assert sel._numero_du_test('') is None
    assert sel._numero_du_test('divers') is None


# --------------------------------------------------------------------------
# La sélection filtre sans perdre
# --------------------------------------------------------------------------

def test_la_selection_ne_garde_que_les_tests_exiges():
    """Une classe 1A n'a que faire des grandeurs du Test 5."""
    selection = sel.selectionner('1A', [_vue('1', 'vert'), _vue('5', 'vert')])
    assert [v['test_id'] for v in selection['vues']] == ['1']


def test_les_tests_exiges_mais_absents_sont_nommes():
    """Les taire ferait passer une classe incomplète pour évaluée."""
    selection = sel.selectionner('1A', [_vue('1', 'vert')])
    assert selection['numeros_absents'] == [2]


def test_la_selection_porte_lintitule_de_la_classe():
    assert sel.selectionner('2A', [])['intitule'] == sel.intitule('2A')
    assert 'froid' in sel.selectionner('2A', [])['intitule']


# --------------------------------------------------------------------------
# Le danger principal : une classe sans preuve
# --------------------------------------------------------------------------

def test_une_classe_sans_vue_nest_pas_conforme():
    """LE test central. Aucun résultat ne vaut jamais conformité."""
    assert sel.statut_de_la_classe(
        sel.selectionner('5', [])) == sel.STATUT_NON_EVALUEE


def test_un_test_manquant_empeche_la_conformite():
    selection = sel.selectionner('1A', [_vue('1', 'vert')])
    assert sel.statut_de_la_classe(selection) == sel.STATUT_NON_EVALUEE


def test_un_test_gris_empeche_la_conformite():
    """Un test non évalué ne vaut pas succès : c'est la règle qui empêche une
    preuve manquante de se lire comme un résultat."""
    selection = sel.selectionner('1A', [_vue('1', 'vert'), _vue('2A', 'gris')])
    assert sel.statut_de_la_classe(selection) == sel.STATUT_NON_EVALUEE


def test_un_seul_test_rouge_rend_la_classe_non_conforme():
    selection = sel.selectionner('1A', [_vue('1', 'vert'), _vue('2A', 'rouge')])
    assert sel.statut_de_la_classe(selection) == sel.STATUT_NON_CONFORME


def test_le_rouge_prime_sur_le_gris():
    """Sinon un échec avéré serait présenté comme une simple absence."""
    selection = sel.selectionner(
        '1B', [_vue('1', 'rouge'), _vue('2', 'gris')])
    assert sel.statut_de_la_classe(selection) == sel.STATUT_NON_CONFORME


def test_tous_les_tests_verts_donnent_conforme():
    selection = sel.selectionner('1A', [_vue('1', 'vert'), _vue('2A', 'vert')])
    assert sel.statut_de_la_classe(selection) == sel.STATUT_CONFORME


# --------------------------------------------------------------------------
# Le diagnostic interne
# --------------------------------------------------------------------------

def test_le_diagnostic_nomme_chaque_test_sans_resultat():
    diagnostic = sel.diagnostiquer('1A')
    motifs = set(b['motif'] for b in diagnostic['blocages'])
    assert motifs == {sel.MOTIF_SANS_SIMULATION}
    assert len(diagnostic['blocages']) == 2


def test_le_diagnostic_signale_les_liaisons_non_resolues():
    diagnostic = sel.diagnostiquer('1A', etat_liaisons={2: (0, 2)})
    liaisons = [b for b in diagnostic['blocages']
                if b['motif'] == sel.MOTIF_LIAISONS]
    assert len(liaisons) == 1
    assert '0 liaison(s) sur 2' in liaisons[0]['constat']


def test_une_liaison_complete_ne_bloque_pas():
    diagnostic = sel.diagnostiquer('1A', etat_liaisons={2: (2, 2)})
    assert not [b for b in diagnostic['blocages']
                if b['motif'] == sel.MOTIF_LIAISONS]


def test_un_critere_non_enonce_est_signale():
    diagnostic = sel.diagnostiquer(
        '1A', vues=[_vue('1', 'vert', 'INFERE'),
                    _vue('2A', 'vert', 'ENONCE_DANS_LA_SPEC')])
    criteres = [b for b in diagnostic['blocages']
                if b['motif'] == sel.MOTIF_CRITERE]
    assert len(criteres) == 1
    assert 'INFERE' in criteres[0]['constat']


def test_les_entrees_absentes_sont_reportees():
    diagnostic = sel.diagnostiquer(
        '5', entrees_absentes={'climat': u'SIA 2028 non disponible'})
    absentes = [b for b in diagnostic['blocages']
                if b['motif'] == sel.MOTIF_ENTREE_ABSENTE]
    assert len(absentes) == 1
    assert 'SIA 2028' in absentes[0]['cause']


def test_chaque_blocage_porte_cause_et_action():
    """Un diagnostic qui nomme un symptôme sans action n'aide personne."""
    diagnostic = sel.diagnostiquer('4B', etat_liaisons={5: (0, 8)},
                                   entrees_absentes={'x': u'motif'})
    for blocage in diagnostic['blocages']:
        assert blocage['constat'] and blocage['cause'] and blocage['action']


def test_les_blocages_sont_ordonnes_du_plus_bloquant():
    """Le rapport doit présenter d'abord ce qui empêche tout le reste."""
    diagnostic = sel.diagnostiquer('4B', etat_liaisons={5: (0, 8)},
                                   entrees_absentes={'x': u'motif'})
    rangs = [sel.ORDRE_DES_MOTIFS.index(b['motif'])
             for b in diagnostic['blocages']]
    assert rangs == sorted(rangs)


def test_une_classe_sans_blocage_est_declaree_atteignable():
    diagnostic = sel.diagnostiquer('1A', vues=[_vue('1', 'vert'),
                                               _vue('2A', 'vert')])
    assert diagnostic['blocages'] == []
    assert diagnostic['atteignable_en_letat'] is True
    assert diagnostic['statut'] == sel.STATUT_CONFORME


def test_le_resume_dit_le_nombre_de_blocages():
    texte = sel.resumer_diagnostic(sel.diagnostiquer('1B'))
    assert 'blocage(s)' in texte
    assert 'AUCUNE_SIMULATION' in texte


def test_le_resume_dune_classe_saine_ne_ment_pas():
    diagnostic = sel.diagnostiquer('1A', vues=[_vue('1', 'vert'),
                                               _vue('2A', 'vert')])
    assert 'Aucun blocage' in sel.resumer_diagnostic(diagnostic)


# --------------------------------------------------------------------------
# Aucune dépendance à l'écran ni à VE
# --------------------------------------------------------------------------

def test_le_module_reste_pur():
    """Règle 4 : testable en CI, sans licence VE et sans affichage."""
    import io
    import os
    chemin = os.path.abspath(sel.__file__).replace('.pyc', '.py')
    with io.open(chemin, encoding='utf-8') as flux:
        for numero, ligne in enumerate(flux, 1):
            nu = ligne.strip()
            assert not nu.startswith(('import iesve', 'from iesve',
                                      'import tkinter', 'from tkinter')), numero
