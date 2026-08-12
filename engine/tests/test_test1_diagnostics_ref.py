# -*- coding: utf-8 -*-
u"""Contrôles du référentiel de la chaîne diagnostique 1A → 1E du Test 1.

Le cas 1E est le seul cas du Test 1 à porter un critère pass/fail. Sa
construction dépend d'une chaîne de quatre maillons, et chaque maillon ajoute un
paramètre normatif : climat, fenêtre, infiltration, usage. Une erreur silencieuse
dans ces valeurs produirait un verdict pass/fail crédible et faux, ce qui est
pire qu'un `NOT_CHECKABLE`.

Le contrôle qui compte le plus n'est pas qu'un champ existe, mais que les deux
colonnes du tableau optique ne soient pas interverties. Elles ne sont pas
nommées ligne par ligne : leur ordre vient d'un en-tête séparé. Un swap donnerait
un store laissant passer dix fois plus de soleil, et rien dans le fichier ne
paraîtrait anormal. On le vérifie donc par la physique, pas par la structure.
"""

import json
import os

import pytest


_RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
_REFERENCE = os.path.join(_RACINE, 'refs', 'reference-data',
                          'test-1.diagnostics.ref.json')

#: Maillons attendus, dans l'ordre de la spécification.
MAILLONS = ('1A', '1B', '1C', '1D', '1E')


@pytest.fixture(scope='module')
def reference():
    if not os.path.exists(_REFERENCE):
        pytest.skip(u'référentiel diagnostique absent')
    with open(_REFERENCE, encoding='utf-8') as flux:
        return json.load(flux)


def test_les_cinq_maillons_sont_presents_et_ordonnes(reference):
    assert [m['cas'] for m in reference['chaine']] == list(MAILLONS)


def test_chaque_maillon_porte_sa_definition_verbatim(reference):
    u"""Une paraphrase française serait une interprétation déguisée en donnée."""
    for maillon in reference['chaine']:
        assert maillon['statut'] == 'RELEVE', maillon
        assert maillon['definition_verbatim_de'], maillon


def test_la_chaine_est_bien_une_chaine(reference):
    u"""Chaque maillon cite le précédent : 1E → 1D → 1C → 1B → 1A → cas 600.

    Si un maillon cessait de citer son prédécesseur, la chaîne serait rompue et
    1E se construirait sur un modèle incomplet sans que rien ne le signale.
    """
    par_cas = {m['cas']: m['definition_verbatim_de'] for m in reference['chaine']}
    assert u'600' in par_cas['1A']
    assert u'1A' in par_cas['1B']
    assert u'1B' in par_cas['1C']
    assert u'1C' in par_cas['1D']
    assert u'1D' in par_cas['1E']


def test_le_cas_1e_ajoute_bien_le_store(reference):
    par_cas = {m['cas']: m['definition_verbatim_de'] for m in reference['chaine']}
    assert u'Stoffmarkise' in par_cas['1E']


def test_le_maillon_1a_impose_le_climat_de_kloten(reference):
    u"""Ce n'est PAS la météo DRYCOLD des six cas normatifs du Test 1."""
    par_cas = {m['cas']: m['definition_verbatim_de'] for m in reference['chaine']}
    assert u'Kloten' in par_cas['1A']


def test_lusage_est_la_categorie_3_1_de_sia_2024(reference):
    categorie = reference['parametres']['usage']['categorie_sia_2024']
    assert categorie['statut'] == 'RELEVE'
    assert categorie['valeur'].startswith(u'3.1')


def test_la_categorie_correspond_a_lextrait_dautorite_detenu():
    u"""Le maillon 1D est liable parce que nous détenons CETTE catégorie.

    La comparaison porte sur le numéro de catégorie, pas sur le libellé : la
    spécification écrit « 3.1 Einzel-Gruppenbüro » et l'extrait d'autorité
    « 3.1 Einzel-/Gruppenbüro ». Même catégorie, typographie différente selon le
    document ; exiger l'égalité des chaînes ferait échouer un test sur une
    barre oblique.
    """
    extrait = os.path.join(
        _RACINE, 'sia4010_evidence', 'source_audits',
        'sia2024_3_1_authority_20260810',
        'sia2024_office_3_1_standard_profiles.binding.json')
    if not os.path.exists(extrait):
        pytest.skip(u"extrait d'autorité SIA 2024 absent")
    with open(extrait, encoding='utf-8') as flux:
        binding = json.load(flux)
    assert u'3.1' in binding['use_category']


def test_les_parametres_chiffres_sont_releves(reference):
    parametres = reference['parametres']
    assert parametres['infiltration']['debit_m3_h_m2']['valeur'] == 0.15
    assert parametres['consignes']['chauffage_celsius']['valeur'] == 20
    assert parametres['consignes']['refroidissement_celsius']['valeur'] == 27
    assert parametres['store']['seuil_activation_w_m2']['valeur'] == 150


def test_les_deux_seuils_du_store_concordent(reference):
    u"""Le seuil est écrit dans deux documents ; ils doivent dire la même chose.

    La spécification Test 2 et la documentation du bâtiment exemple portent
    chacune ce seuil. Une divergence signalerait qu'on lit la mauvaise ligne
    dans l'un des deux.
    """
    store = reference['parametres']['store']
    assert (store['seuil_activation_w_m2']['valeur']
            == store['seuil_fermeture_w_m2']['valeur'])


def test_le_produit_du_store_est_releve_en_entier(reference):
    u"""Le type porte une espace ; un motif trop strict ne relevait que « Soltis »."""
    produit = reference['parametres']['store']['produit']
    assert produit['statut'] == 'RELEVE'
    assert produit['valeur']['type'] == u'Soltis 92-2048-Alu'
    assert produit['valeur']['fabricant'] == u'SergeFerrari'


def test_lordre_des_colonnes_optiques_est_demontre(reference):
    fenetre = reference['fenetre_entiere']
    assert fenetre['statut'] == 'RELEVE'
    assert u'store rentré' in fenetre['ordre_colonnes']


@pytest.mark.parametrize('bloc,attendu', [
    ('en_iso_52022_3_conditions_ete', 5),
    ('en_iso_52022_3_conditions_reference', 2),
    ('en_410', 7),
])
def test_chaque_bloc_optique_porte_ses_grandeurs(reference, bloc, attendu):
    u"""Effectifs figés : « EN 410 » sortait vide sur une borne mal cherchée.

    « Layer d [mm] » apparaît deux fois dans le document et la première
    occurrence précède « EN 410: ». Chercher la borne de fin globalement donnait
    un segment de longueur négative, donc un bloc vide, sans erreur visible.
    """
    grandeurs = reference['fenetre_entiere']['blocs'][bloc]['grandeurs']
    assert len(grandeurs) == attendu, sorted(grandeurs)


def test_le_store_deploye_reduit_la_transmission(reference):
    u"""Contrôle par la physique, seul garde-fou contre une interversion.

    Déployer un store ne peut pas augmenter la transmission solaire ni la
    transmission visible. Si les deux colonnes étaient interverties, ce test
    échouerait ; aucun contrôle de structure ne le ferait.
    """
    blocs = reference['fenetre_entiere']['blocs']
    transmissions = (
        blocs['en_iso_52022_3_conditions_ete']['grandeurs']['g_total'],
        blocs['en_iso_52022_3_conditions_reference']['grandeurs']['g_total'],
        blocs['en_410']['grandeurs']['transmission_solaire_directe_te'],
        blocs['en_410']['grandeurs']['transmission_visible_tv'],
        blocs['en_410']['grandeurs']['transmission_uv_tuv'],
    )
    for grandeur in transmissions:
        assert grandeur['store_deploye'] < grandeur['store_rentre'], grandeur


def test_le_store_deploye_augmente_la_reflexion_exterieure(reference):
    u"""L'autre moitié du même contrôle : un store réfléchit ce qu'il arrête."""
    en_410 = reference['fenetre_entiere']['blocs']['en_410']['grandeurs']
    for cle in ('reflexion_solaire_exterieure_re',
                'reflexion_visible_exterieure_rv'):
        grandeur = en_410[cle]
        assert grandeur['store_deploye'] > grandeur['store_rentre'], grandeur


def test_la_reflexion_visible_recoupe_la_specification_test_2(reference):
    u"""Recoupement inter-documents : la spec Test 2 cite « Reflexion v → 0.145 ».

    La valeur vient de la documentation du bâtiment exemple ; la retrouver dans
    la spécification confirme qu'on lit la bonne fenêtre.
    """
    en_410 = reference['fenetre_entiere']['blocs']['en_410']['grandeurs']
    assert en_410['reflexion_visible_exterieure_rv']['store_rentre'] == 0.145


def test_chaque_source_porte_son_empreinte(reference):
    assert len(reference['sources']) == 3
    for cle, source in reference['sources'].items():
        assert len(source['sha256']) == 64, cle
        assert source['fichier'].startswith('SIA_4010_geteilter_Link/'), cle
        assert source['role'], cle


def test_aucun_champ_ne_reste_a_confirmer_en_silence(reference):
    u"""Un `A_CONFIRMER` est admissible, mais il doit porter sa raison."""
    manquants = []

    def visiter(noeud, chemin=''):
        if isinstance(noeud, dict):
            if noeud.get('statut') == 'A_CONFIRMER' and not noeud.get('raison'):
                manquants.append(chemin)
            for cle, valeur in noeud.items():
                visiter(valeur, chemin + '.' + str(cle))
        elif isinstance(noeud, list):
            for indice, valeur in enumerate(noeud):
                visiter(valeur, chemin + '[%d]' % indice)

    visiter(reference)
    assert manquants == []


def test_le_referentiel_ne_revendique_aucune_validation(reference):
    u"""Figer la donnée ne rend pas 1E validable, et le fichier doit le dire."""
    assert u'posable' in reference['pourquoi']
    joint = u' '.join(reference['reserves'])
    assert u'Aucun cas' in joint
