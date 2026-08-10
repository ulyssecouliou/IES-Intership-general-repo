# -*- coding: utf-8 -*-
u"""Tests de l'extraction du réseau de ventilation des tests SIA 5 et 6.

Ce que ces tests surveillent n'est PAS que l'extraction trouve beaucoup de
valeurs : c'est qu'elle **refuse** quand elle ne sait pas. Trois pièges ont
été rencontrés en écrivant l'extracteur, et tous trois produisaient une
valeur crédible :

* `Auslegungsleistung` et `Austrittstemperatur` apparaissent sur les deux
  batteries. Sans ancrage de section, la batterie chaude héritait des valeurs
  du refroidisseur — 8,6 kW au lieu de 3,5 kW ;
* « 20; 2018 » est une graduation d'axe collée à une valeur. Lire 2018 comme
  20 serait une invention ;
* les étiquettes d'un graphique voisin sans titre se rangeaient sous la
  température de soufflage du Test 6.

Aucun n'aurait fait échouer quoi que ce soit avant la comparaison finale.
"""

import pytest

from scripts import build_reseau_ventilation_reference as extracteur


@pytest.fixture(scope='module', params=[5, 6])
def reference(request):
    try:
        return extracteur.construire(request.param)
    except IOError:
        pytest.skip(u'spécification absente')


# --------------------------------------------------------------------------
# Rien n'est deviné
# --------------------------------------------------------------------------

def test_un_motif_introuvable_ne_rend_jamais_de_valeur():
    champ = extracteur._chercher(u'rien ici', r'introuvable (\d+)',
                                 extracteur._nombre, u'source')
    assert champ['valeur'] is None
    assert champ['statut'] == extracteur.A_CONFIRMER
    assert 'devinée' in champ['a_confirmer']


def test_une_section_absente_ne_rend_jamais_de_valeur():
    champ = extracteur._chercher(u'Auslegungsleistung 8.6 kW',
                                 r'Auslegungsleistung ([\d.]+)',
                                 extracteur._nombre, u'source',
                                 depuis=u'Lufterhitzer')
    assert champ['valeur'] is None
    assert champ['statut'] == extracteur.A_CONFIRMER


def test_lancrage_de_section_evite_de_lire_le_mauvais_appareil():
    u"""LE PIÈGE. Les deux batteries portent le même libellé ; la première du
    flux gagnerait, en silence."""
    texte = (u'Luftkühler Auslegungsleistung 8.6 kW\n'
             u'Lufterhitzer Auslegungsleistung 3.5 kW')
    motif = r'Auslegungsleistung\s*([\d.]+)\s*kW'
    froide = extracteur._chercher(texte, motif, extracteur._nombre, u'x',
                                  depuis=u'Luftkühler')
    chaude = extracteur._chercher(texte, motif, extracteur._nombre, u'x',
                                  depuis=u'Lufterhitzer')
    assert froide['valeur'] == 8.6
    assert chaude['valeur'] == 3.5


def test_les_separateurs_de_milliers_du_pdf_sont_lus():
    assert extracteur._nombre(u"1'040") == 1040
    assert extracteur._nombre(u'6150') == 6150
    assert extracteur._nombre(u'0.765') == 0.765


def test_un_entier_reste_un_entier():
    u"""`20.0 min-1` écrit dans un référentiel invite à croire à une mesure."""
    assert isinstance(extracteur._nombre(u'20'), int)


# --------------------------------------------------------------------------
# Les graphiques : refuser plutôt que réparer
# --------------------------------------------------------------------------

def test_une_ordonnee_hors_graduations_fait_echouer_la_courbe():
    u"""« 20; 2018 » : la graduation 18 est collée à la valeur 20. Corriger
    en 20 serait exactement l'invention que la règle 1 interdit."""
    texte = u'20; 2018\n18\n20\n40\n42\nHeizwassertemperatur'
    attribution = extracteur._attribuer_les_etiquettes(
        texte, [u'Heizwassertemperatur'])
    courbe = extracteur._courbe(texte, u'Heizwassertemperatur',
                                u'Heizwassertemperatur', attribution)
    assert courbe['points'] is None
    assert courbe['statut'] == extracteur.A_CONFIRMER
    assert 'collé' in courbe['a_confirmer']


def test_deux_groupes_detiquettes_font_echouer_la_courbe():
    u"""Un graphique voisin sans titre propre se fait attribuer au suivant."""
    texte = (u'17.5; 25 19; 22' + u' ' * 120 + u'12; 20 20; 18'
             + u'\n15\n30\nZulufttemperatur')
    attribution = extracteur._attribuer_les_etiquettes(
        texte, [u'Zulufttemperatur'])
    courbe = extracteur._courbe(texte, u'Zulufttemperatur',
                                u'Zulufttemperatur', attribution)
    assert courbe['points'] is None
    assert len(courbe['groupes_candidats']) == 2


def test_les_groupes_candidats_sont_montres_et_non_arbitres():
    u"""Montrer les deux fait de la lecture du PDF une affaire de secondes ;
    en choisir un fait de l'erreur une affaire de semaines."""
    texte = (u'17.5; 25' + u' ' * 120 + u'12; 20 20; 18'
             + u'\n15\n30\nZulufttemperatur')
    attribution = extracteur._attribuer_les_etiquettes(
        texte, [u'Zulufttemperatur'])
    courbe = extracteur._courbe(texte, u'Zulufttemperatur', u'x', attribution)
    assert [17.5, 25] in courbe['groupes_candidats'][0]
    assert [12, 20] in courbe['groupes_candidats'][1]


def test_une_etiquette_va_au_graphique_le_plus_proche():
    u"""Le premier défaut : « le titre apparaît-il plus loin » rangeait les
    points de l'eau glacée aussi sous l'eau chaude."""
    texte = u'12; 18\nKaltwassertemperatur\n-10; 40\nHeizwassertemperatur'
    attribution = extracteur._attribuer_les_etiquettes(
        texte, [u'Kaltwassertemperatur', u'Heizwassertemperatur'])
    assert len(attribution[u'Kaltwassertemperatur']) == 1
    assert len(attribution[u'Heizwassertemperatur']) == 1


def test_une_etiquette_orpheline_nest_attribuee_a_personne():
    texte = u'12; 18' + u' ' * 900 + u'Kaltwassertemperatur'
    attribution = extracteur._attribuer_les_etiquettes(
        texte, [u'Kaltwassertemperatur'])
    assert attribution[u'Kaltwassertemperatur'] == []


# --------------------------------------------------------------------------
# Les référentiels produits
# --------------------------------------------------------------------------

def test_chaque_champ_porte_son_statut_et_sa_source(reference):
    for nom_bloc, bloc in sorted(reference.items()):
        if nom_bloc.startswith('_') or nom_bloc == 'courbes':
            continue
        if not isinstance(bloc, dict):
            continue
        for cle, champ in sorted(bloc.items()):
            assert 'statut' in champ, (nom_bloc, cle)
            assert champ.get('source'), (nom_bloc, cle)


def test_un_champ_a_confirmer_ne_porte_jamais_de_valeur(reference):
    u"""La règle centrale du dépôt : une absence n'est pas une mesure."""
    for nom_bloc, bloc in sorted(reference.items()):
        if nom_bloc.startswith('_') or not isinstance(bloc, dict):
            continue
        for cle, champ in sorted(bloc.items()):
            if not isinstance(champ, dict):
                continue
            if champ.get('statut') != extracteur.A_CONFIRMER:
                continue
            assert champ.get('valeur') is None, (nom_bloc, cle)
            assert champ.get('points') is None, (nom_bloc, cle)
            assert champ.get('a_confirmer'), (nom_bloc, cle)


def test_le_bilan_compte_les_trous(reference):
    u"""Un référentiel dont on ignore le nombre de trous invite à le croire
    complet."""
    bilan = reference['_bilan']
    assert bilan['effectifs'].get(extracteur.A_CONFIRMER, 0) == \
        len(bilan['a_confirmer'])
    assert bilan['a_confirmer'], u'aucun trou signalé : suspect'


def test_les_variantes_du_test_5_ne_sont_pas_arbitrees():
    u"""Cinq paramètres dépendent de la variante et le PDF porte quatre
    colonnes pour deux cellules. Trancher construirait deux variantes fausses
    sur quatre."""
    try:
        reference = extracteur.construire(5)
    except IOError:
        pytest.skip(u'spécification absente')
    for bloc, cle in (('recuperateur', 'type_par_variante'),
                      ('recuperateur', 'taux_temperature_par_variante'),
                      ('recuperateur', 'taux_humidite_par_variante'),
                      ('humidificateur', 'type_par_variante'),
                      ('ventilateurs', 'part_pression_constante_pa')):
        champ = reference[bloc][cle]
        assert champ['statut'] == extracteur.A_CONFIRMER, (bloc, cle)
        assert 'colonnes' in champ['a_confirmer'], (bloc, cle)


def test_la_contradiction_de_debit_du_test_6_est_signalee():
    u"""La page 1 annonce 3'000 m3/h et la section RLT 6'150. Les confondre
    fausserait tout le bilan aéraulique."""
    try:
        reference = extracteur.construire(6)
    except IOError:
        pytest.skip(u'spécification absente')
    champ = reference['reseau']['debit_du_local_restaurant_m3_h']
    assert champ['statut'] == extracteur.A_CONFIRMER
    assert 'CONTRADICTION' in champ['a_confirmer']


def test_les_batteries_ne_partagent_pas_leurs_valeurs():
    try:
        reference = extracteur.construire(5)
    except IOError:
        pytest.skip(u'spécification absente')
    froide = reference['batterie_froide']
    chaude = reference['batterie_chaude']
    assert froide['puissance_kw']['valeur'] != chaude['puissance_kw']['valeur']
    assert froide['air_entrant_c']['valeur'] != \
        chaude['air_entrant_c']['valeur']


# --------------------------------------------------------------------------
# Les fiches de saisie
# --------------------------------------------------------------------------

@pytest.mark.parametrize('numero', [5, 6])
def test_la_fiche_met_les_trous_en_tete(numero):
    from scripts import build_fiche_apachehvac_56 as fiche
    try:
        document = fiche.construire(numero)
    except IOError:
        pytest.skip(u'référentiel non figé')
    position_trous = document.find(u'À trancher AVANT')
    position_composants = document.find(u'## Composants')
    assert 0 < position_trous < position_composants


@pytest.mark.parametrize('numero', [5, 6])
def test_un_champ_a_trancher_naffiche_aucune_valeur(numero):
    u"""Afficher un tiret laisserait croire à un zéro ; afficher une valeur
    laisserait croire à un relevé."""
    from scripts import build_fiche_apachehvac_56 as fiche
    champ = {'statut': extracteur.A_CONFIRMER, 'valeur': None,
             'source': u'x', 'a_confirmer': u'y'}
    assert fiche._valeur_lisible(champ) == u'**À TRANCHER**'


@pytest.mark.parametrize('numero', [5, 6])
def test_la_fiche_ne_declare_rien_conforme(numero):
    from scripts import build_fiche_apachehvac_56 as fiche
    try:
        document = fiche.construire(numero)
    except IOError:
        pytest.skip(u'référentiel non figé')
    for interdit in (u'validé', u'PASS'):
        assert interdit not in document, (numero, interdit)


@pytest.mark.parametrize('numero', [5, 6])
def test_la_fiche_rappelle_que_le_climat_manque(numero):
    u"""Sans le climat SIA 2028 Kloten, une simulation de ce test n'est pas un
    cas de validation SIA — le taire ferait croire l'inverse."""
    from scripts import build_fiche_apachehvac_56 as fiche
    try:
        document = fiche.construire(numero)
    except IOError:
        pytest.skip(u'référentiel non figé')
    assert u'SIA 2028' in document
    assert u'Kloten' in document
