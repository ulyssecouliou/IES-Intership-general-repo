# -*- coding: utf-8 -*-
"""Tests de `engine/test7_engine.py` — Test 7, classe de validation 5.

Deux familles, comme pour le Test 1 :

1. **Reproduction des références.** Les onze bandes du moteur doivent redonner
   exactement les colonnes `Mittelwert / Obere Grenze / Untere Grenze` du
   classeur officiel. Ce contrôle tourne aussi SANS le classeur, contre le JSON
   figé, pour rester exécutable en CI.

2. **Résistance à la mutation.** Chaque test échoue si une implémentation
   plausible mais fausse était écrite : programme non contributeur compté comme
   zéro, plancher à zéro appliqué par défaut, grandeur manquante comptée comme
   réussie, Diagnosegrössen entrant dans le verdict.
"""

import io
import json
import os

import pytest

from engine import scatter_band
from engine import test7_engine as moteur


_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))


@pytest.fixture(scope='module')
def reference():
    if not os.path.exists(moteur.CHEMIN_REFERENCE_DEFAUT):
        pytest.skip(u'référence Test 7 absente : %s'
                    % moteur.CHEMIN_REFERENCE_DEFAUT)
    return moteur.charger_reference()


# Provenance d'irradiance FICTIVE, uniquement pour les témoins positifs : elle
# lève le verrou du PV sans prétendre décrire une source réelle. Aucun test ne
# doit l'utiliser pour affirmer qu'une irradiance existe.
SOURCE_FICTIVE = u'source fictive de test -- ne décrit aucune donnée réelle'


@pytest.fixture(scope='module')
def candidat_parfait(reference):
    u"""Candidat fictif posé exactement sur la moyenne de chaque bande.

    Il DOIT passer : c'est le centre de la bande. Sert de témoin positif.
    """
    return dict((g['libelle_de'], g['moyenne']) for g in reference['grandeurs'])


# --------------------------------------------------------------------------
# 1. Reproduction des références
# --------------------------------------------------------------------------

def test_onze_grandeurs_a_bande(reference):
    """Le classeur porte 11 lignes à bande : 5 froid, 5 chaud, 1 PV."""
    assert len(reference['grandeurs']) == 11


def test_les_bandes_du_json_sont_coherentes_avec_leurs_contributeurs(reference):
    """Recalcul complet depuis les valeurs par programme.

    Si le JSON figé avait été édité à la main, ce test le verrait.
    """
    for g in reference['grandeurs']:
        contributions = moteur.valeurs_contributrices(g)
        bande = scatter_band.build_band(
            contributions, floor_at_zero=g['plancher_a_zero'])
        assert abs(bande.mean - g['moyenne']) < 1e-9, g['libelle_de']
        assert abs(bande.upper_bound - g['borne_haute']) < 1e-9, g['libelle_de']
        assert abs(bande.lower_bound - g['borne_basse']) < 1e-9, g['libelle_de']


def test_le_jeu_de_contributeurs_varie_reellement(reference):
    """GHJ, GHIJ, GHI — si tout était GHIJ, on aurait mal lu le classeur."""
    jeux = set(tuple(g['contributeurs']) for g in reference['grandeurs'])
    assert len(jeux) > 1, jeux
    assert ('G', 'H', 'J') in jeux
    assert ('G', 'H', 'I', 'J') in jeux


def test_le_plancher_a_zero_est_ponctuel_pas_general(reference):
    """Deux grandeurs seulement portent MAX(0,…) dans le classeur."""
    avec = [g['libelle_de'] for g in reference['grandeurs']
            if g['plancher_a_zero']]
    assert len(avec) == 2, avec
    for g in reference['grandeurs']:
        if g['plancher_a_zero']:
            assert g['borne_basse'] >= 0.0


def test_le_pv_porte_une_bande_donc_il_est_obligatoire(reference):
    """« PV-Ertrag » est une Testgrösse : sans irradiance, pas de classe 5."""
    pv = [g for g in reference['grandeurs'] if 'PV' in g['libelle_de']]
    assert len(pv) == 1
    assert pv[0]['groupe'] == moteur.GROUPE_AVEC_CRITERE
    assert pv[0]['borne_haute'] > pv[0]['borne_basse']


# --------------------------------------------------------------------------
# 2. Comportement du moteur
# --------------------------------------------------------------------------

def test_sans_candidat_rien_nest_conforme(reference):
    """État « avant première simulation VE » : aucun succès par défaut."""
    r = moteur.evaluer_test7(reference, None)
    assert r['verdict'] == scatter_band.VERDICT_NOT_CHECKABLE
    assert r['classe_5_validee'] is False
    assert all(g['conforme'] is None for g in r['grandeurs'])
    assert r['nb_echecs'] == 0


def test_candidat_au_centre_de_chaque_bande_passe(reference, candidat_parfait):
    """Témoin positif. La provenance de l'irradiance doit être déclarée :
    sans elle le PV est refusé, cf. la section « verrou » plus bas."""
    r = moteur.evaluer_test7(reference, candidat_parfait,
                             source_irradiance=SOURCE_FICTIVE)
    assert r['verdict'] == scatter_band.VERDICT_PASS
    assert r['classe_5_validee'] is True
    assert r['classe_5_provisoirement_conforme'] is True
    assert r['nb_echecs'] == 0
    assert r['nb_non_evaluables'] == 0


def test_une_seule_grandeur_manquante_suffit_a_bloquer(reference,
                                                       candidat_parfait):
    """Le cas réel : tout passe sauf le PV, faute d'irradiance.

    Le verdict doit être NOT_CHECKABLE, surtout pas PASS.
    """
    partiel = dict(candidat_parfait)
    pv = [k for k in partiel if 'PV' in k][0]
    del partiel[pv]

    r = moteur.evaluer_test7(reference, partiel)
    assert r['verdict'] == scatter_band.VERDICT_NOT_CHECKABLE
    assert r['classe_5_validee'] is False
    assert r['nb_non_evaluables'] == 1
    assert r['nb_echecs'] == 0
    ligne_pv = [g for g in r['grandeurs'] if g['libelle'] == pv][0]
    assert ligne_pv['statut'] == scatter_band.VERDICT_NOT_CHECKABLE
    assert ligne_pv['conforme'] is None


def test_une_valeur_hors_bande_fait_echouer(reference, candidat_parfait):
    faux = dict(candidat_parfait)
    cible = reference['grandeurs'][0]
    faux[cible['libelle_de']] = cible['borne_haute'] + 1000.0

    r = moteur.evaluer_test7(reference, faux)
    assert r['verdict'] == scatter_band.VERDICT_FAIL
    assert r['classe_5_validee'] is False
    assert r['nb_echecs'] == 1


def test_les_bornes_sont_inclusives(reference, candidat_parfait):
    """Le classeur ne définit aucune exclusion stricte."""
    for borne in ('borne_basse', 'borne_haute'):
        au_bord = dict(candidat_parfait)
        cible = reference['grandeurs'][1]
        au_bord[cible['libelle_de']] = cible[borne]
        r = moteur.evaluer_test7(reference, au_bord)
        assert r['nb_echecs'] == 0, borne


def test_un_echec_prime_sur_une_non_evaluable(reference, candidat_parfait):
    """Un FAIL ne doit pas être masqué par un NOT_CHECKABLE."""
    melange = dict(candidat_parfait)
    pv = [k for k in melange if 'PV' in k][0]
    del melange[pv]
    cible = reference['grandeurs'][0]
    melange[cible['libelle_de']] = cible['borne_haute'] + 1000.0

    r = moteur.evaluer_test7(reference, melange)
    assert r['verdict'] == scatter_band.VERDICT_FAIL


def test_les_diagnosegroessen_nentrent_pas_dans_le_verdict(reference):
    """Elles ne portent aucune bande dans le classeur : elles sont exclues."""
    r = moteur.evaluer_test7(reference, None)
    assert r['grandeurs_soumises_au_critere'] == len(
        [g for g in reference['grandeurs']
         if g['groupe'] == moteur.GROUPE_AVEC_CRITERE])


def test_le_classeur_corrige_est_annonce_comme_verifie(reference):
    """Le résultat identifie la source corrigée désormais active."""
    r = moteur.evaluer_test7(reference, None)
    assert r['critere']['statut'] == 'CLASSEUR_CORRIGE_VERIFIE_2026-08-10'
    assert '4.4' in r['critere']['justification']
    assert '2026-08-10' in r['critere']['justification']


def test_appariement_insensible_a_la_casse_et_aux_espaces(reference):
    brut = dict((g['libelle_de'].upper() + '  ', g['moyenne'])
                for g in reference['grandeurs'])
    r = moteur.evaluer_test7(reference, brut, source_irradiance=SOURCE_FICTIVE)
    assert r['nb_non_evaluables'] == 0
    assert r['cles_candidat_ignorees'] == []


def test_un_programme_non_contributeur_nest_pas_compte_comme_zero(reference):
    """Mutation classique : remplacer None par 0.0 écraserait la moyenne."""
    for g in reference['grandeurs']:
        contributions = moteur.valeurs_contributrices(g)
        assert len(contributions) == len(g['contributeurs_noms'])
        assert all(v is not None for v in contributions)
        if len(g['contributeurs_noms']) < 4:
            avec_zero = contributions + [0.0]
            faussee = sum(avec_zero) / len(avec_zero)
            assert abs(faussee - g['moyenne']) > 1e-6, g['libelle_de']


def test_une_cle_candidate_non_appariee_est_signalee(reference,
                                                      candidat_parfait):
    """Une faute de frappe dans l'adaptateur ne doit pas passer inaperçue.

    Sans ce signalement, la grandeur visée apparaîtrait NOT_CHECKABLE sans que
    rien n'indique qu'une valeur avait pourtant été fournie sous un autre nom.
    """
    avec_faute = dict(candidat_parfait)
    cible = reference['grandeurs'][0]['libelle_de']
    avec_faute['Zugefuehrte elektrische Enrgie Kaeltemaschine'] = avec_faute.pop(cible)

    r = moteur.evaluer_test7(reference, avec_faute)
    assert 'Zugefuehrte elektrische Enrgie Kaeltemaschine' in r['cles_candidat_ignorees']
    # et la grandeur visée est bien restée non évaluable
    ligne = [g for g in r['grandeurs'] if g['libelle'] == cible][0]
    assert ligne['statut'] == scatter_band.VERDICT_NOT_CHECKABLE


def test_les_metadonnees_prefixees_ne_sont_pas_signalees(reference,
                                                          candidat_parfait):
    """`_provenance` est un bloc assumé des fixtures, pas une erreur."""
    avec_meta = dict(candidat_parfait)
    avec_meta['_provenance'] = {'source': u'fixture de développement'}
    r = moteur.evaluer_test7(reference, avec_meta)
    assert r['cles_candidat_ignorees'] == []


def test_un_candidat_propre_ne_signale_rien(reference, candidat_parfait):
    r = moteur.evaluer_test7(reference, candidat_parfait)
    assert r['cles_candidat_ignorees'] == []


# --------------------------------------------------------------------------
# 3. Verrou d'irradiance — le scénario que l'audit a montré ouvert
# --------------------------------------------------------------------------

def test_une_valeur_de_pv_sans_provenance_declaree_est_refusee(
        reference, candidat_parfait):
    """Le scénario dangereux : un PV calculé sur un climat de substitution.

    Avant ce verrou, fournir la valeur suffisait à obtenir PASS et
    `classe_5_validee = True`.
    """
    r = moteur.evaluer_test7(reference, candidat_parfait)  # PV fourni, sans source
    assert r['verdict'] == scatter_band.VERDICT_NOT_CHECKABLE
    assert r['classe_5_validee'] is False
    assert r['grandeurs_verrouillees'] == ['PV-Ertrag']

    pv = [g for g in r['grandeurs'] if g['libelle'] == 'PV-Ertrag'][0]
    assert pv['statut'] == scatter_band.VERDICT_NOT_CHECKABLE
    assert pv['candidat'] is None       # la valeur est ÉCARTÉE, pas conservée
    assert pv['verrou'] == moteur.MOTIF_VERROU_IRRADIANCE


def test_le_verrou_ne_touche_que_le_pv(reference, candidat_parfait):
    r = moteur.evaluer_test7(reference, candidat_parfait)
    autres = [g for g in r['grandeurs'] if g['libelle'] != 'PV-Ertrag']
    assert all(g['verrou'] is None for g in autres)
    assert all(g['conforme'] is True for g in autres)


def test_une_provenance_declaree_leve_le_verrou(reference, candidat_parfait):
    """Le verrou exige une déclaration, il n'interdit pas la valeur.

    Un blocage en dur serait faux le jour où nous aurons l'irradiance.
    """
    source = u'SIA 2028 DRY normal, Kloten, colonnes verticales — hypothétique'
    r = moteur.evaluer_test7(reference, candidat_parfait,
                             source_irradiance=source)
    assert r['verdict'] == scatter_band.VERDICT_PASS
    assert r['classe_5_validee'] is True
    assert r['classe_5_provisoirement_conforme'] is True
    assert r['grandeurs_verrouillees'] == []
    assert r['source_irradiance'] == source


def test_la_provenance_declaree_remonte_sur_la_ligne_pv(reference,
                                                         candidat_parfait):
    """Sans ça, la déclaration serait perdue au moment d'écrire le rapport."""
    source = u'irradiance mesurée, station X'
    r = moteur.evaluer_test7(reference, candidat_parfait,
                             source_irradiance=source)
    pv = [g for g in r['grandeurs'] if g['libelle'] == 'PV-Ertrag'][0]
    assert pv['source_irradiance'] == source
    assert pv['exige_irradiance'] is True


def test_le_resume_affiche_le_verrou(reference, candidat_parfait):
    texte = moteur.resumer(moteur.evaluer_test7(reference, candidat_parfait))
    assert 'VERROU' in texte
    assert 'PV-Ertrag' in texte


def test_chaque_ligne_porte_le_statut_du_classeur_corrige(reference,
                                                          candidat_parfait):
    """`evaluer_grandeur` est publique : le marqueur ne doit pas dépendre
    d'un passage par `evaluer_test7`."""
    grandeur = reference['grandeurs'][0]
    ligne = moteur.evaluer_grandeur(grandeur, grandeur['moyenne'])
    assert ligne['critere_statut'] == 'CLASSEUR_CORRIGE_VERIFIE_2026-08-10'


def test_la_liste_des_grandeurs_a_irradiance_correspond_a_la_reference(reference):
    """Si le libellé du classeur changeait, le verrou deviendrait inopérant
    en silence. Ce test le ferait voir."""
    libelles = set(g['libelle_de'].strip() for g in reference['grandeurs'])
    for nom in moteur.GRANDEURS_EXIGEANT_IRRADIANCE:
        assert nom in libelles, nom


def test_resume_mentionne_chaque_grandeur(reference, candidat_parfait):
    texte = moteur.resumer(moteur.evaluer_test7(reference, candidat_parfait))
    for g in reference['grandeurs']:
        assert g['libelle_de'][:40] in texte


def test_no_iesve_import():
    """Règle 4 de CLAUDE.md : engine/ est du Python pur."""
    chemin = os.path.join(_RACINE, 'engine', 'test7_engine.py')
    with io.open(chemin, encoding='utf-8') as f:
        for numero, ligne in enumerate(f, 1):
            nu = ligne.strip()
            assert not nu.startswith('import iesve'), numero
            assert not nu.startswith('from iesve'), numero
