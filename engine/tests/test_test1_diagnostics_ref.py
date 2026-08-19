# -*- coding: utf-8 -*-
u"""Checks of the reference data for the diagnostic chain 1A → 1E of Test 1.

Case 1E is the only case of Test 1 that carries a pass/fail criterion. Its
construction depends on a chain of four links, and each link adds a normative
parameter: climate, window, infiltration, use. A silent error in these values
would produce a plausible and wrong pass/fail verdict, which is worse than a
`NOT_CHECKABLE`.

The check that matters most is not that a field exists, but that the two
columns of the optical table have not been swapped. They are not labelled
row by row: their order comes from a separate header. A swap would give a
blind that lets ten times more sunlight through, and nothing in the file
would look unusual. We therefore check by physics, not by structure.
"""

import json
import os

import pytest


_RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
_REFERENCE = os.path.join(_RACINE, 'refs', 'reference-data',
                          'test-1.diagnostics.ref.json')

#: Expected links, in the order of the specification.
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
    u"""A French paraphrase would be an interpretation disguised as data."""
    for maillon in reference['chaine']:
        assert maillon['statut'] == 'RELEVE', maillon
        assert maillon['definition_verbatim_de'], maillon


def test_la_chaine_est_bien_une_chaine(reference):
    u"""Each link cites the previous one: 1E → 1D → 1C → 1B → 1A → case 600.

    If a link stopped citing its predecessor, the chain would be broken and
    1E would be built on an incomplete model with no signal.
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
    u"""This is NOT the DRYCOLD weather of the six normative cases of Test 1."""
    par_cas = {m['cas']: m['definition_verbatim_de'] for m in reference['chaine']}
    assert u'Kloten' in par_cas['1A']


def test_lusage_est_la_categorie_3_1_de_sia_2024(reference):
    categorie = reference['parametres']['usage']['categorie_sia_2024']
    assert categorie['statut'] == 'RELEVE'
    assert categorie['valeur'].startswith(u'3.1')


def test_la_categorie_correspond_a_lextrait_dautorite_detenu():
    u"""Link 1D is traceable because we hold THIS category.

    The comparison is on the category number, not the label: the specification
    writes "3.1 Einzel-Gruppenbüro" and the authority extract "3.1 Einzel-/
    Gruppenbüro". Same category, different typography across documents; requiring
    string equality would fail a test on a slash.
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
    u"""The threshold is written in two documents; they must say the same thing.

    The Test 2 specification and the example-building documentation each carry
    this threshold. A divergence would indicate that one reads the wrong row in
    one of them.
    """
    store = reference['parametres']['store']
    assert (store['seuil_activation_w_m2']['valeur']
            == store['seuil_fermeture_w_m2']['valeur'])


def test_le_produit_du_store_est_releve_en_entier(reference):
    u"""The type contains a space; too strict a pattern extracted only "Soltis"."""
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
    u"""Frozen counts: "EN 410" came out empty with a badly searched boundary.

    "Layer d [mm]" appears twice in the document and the first occurrence
    precedes "EN 410:". Searching the end boundary globally gave a negative-length
    segment, hence an empty block, with no visible error.
    """
    grandeurs = reference['fenetre_entiere']['blocs'][bloc]['grandeurs']
    assert len(grandeurs) == attendu, sorted(grandeurs)


def test_le_store_deploye_reduit_la_transmission(reference):
    u"""Physics check, the only safeguard against a column swap.

    Deploying a blind cannot increase solar transmittance or visible
    transmittance. If the two columns were swapped, this test would fail;
    no structural check would.
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
    u"""The other half of the same check: a blind reflects what it blocks."""
    en_410 = reference['fenetre_entiere']['blocs']['en_410']['grandeurs']
    for cle in ('reflexion_solaire_exterieure_re',
                'reflexion_visible_exterieure_rv'):
        grandeur = en_410[cle]
        assert grandeur['store_deploye'] > grandeur['store_rentre'], grandeur


def test_la_reflexion_visible_recoupe_la_specification_test_2(reference):
    u"""Cross-document corroboration: Test 2 spec cites "Reflexion v → 0.145".

    The value comes from the example-building documentation; finding it in
    the specification confirms that one reads the correct window.
    """
    en_410 = reference['fenetre_entiere']['blocs']['en_410']['grandeurs']
    assert en_410['reflexion_visible_exterieure_rv']['store_rentre'] == 0.145


def test_le_vitrage_du_maillon_1b_est_chiffre_par_la_specification(reference):
    u"""The specification resolves what the documentation leaves open.

    The example-building documentation gives two total g values, under summer
    and reference conditions. The specification retains one value, and it is
    that value which defines the test case: choosing oneself would mean deciding
    a normative datum.
    """
    vitrage = reference['parametres']['vitrage']
    assert vitrage['type']['valeur'] == u'SGG Planitherm XN_4/14/4/14/4'
    assert vitrage['g_total']['valeur'] == 0.545
    assert vitrage['u_vitrage_w_m2k']['valeur'] == 0.654
    assert vitrage['transmission_visible']['valeur'] == 0.742
    assert vitrage['reflexion_visible']['valeur'] == 0.145


def test_les_symboles_grecs_ne_font_pas_echouer_le_releve(reference):
    u"""Extraction trap: "τv" and "ρv" come out in the private-use area.

    The text layer renders these symbols as glyphs from the Symbol font,
    not as Unicode Greek characters. A pattern written with the real τ would
    never match and the field would come out as `A_CONFIRMER`, suggesting that
    the specification does not give the value.
    """
    vitrage = reference['parametres']['vitrage']
    assert vitrage['transmission_visible']['statut'] == 'RELEVE'
    assert vitrage['reflexion_visible']['statut'] == 'RELEVE'


def test_le_g_et_la_transmission_concordent_entre_les_deux_sources(reference):
    u"""Cross-corroboration: the two documents must say the same thing."""
    spec = reference['parametres']['vitrage']
    blocs = reference['fenetre_entiere']['blocs']
    ete = blocs['en_iso_52022_3_conditions_ete']['grandeurs']['g_total']
    en_410 = blocs['en_410']['grandeurs']['transmission_visible_tv']
    assert spec['g_total']['valeur'] == ete['store_rentre']
    assert spec['transmission_visible']['valeur'] == en_410['store_rentre']


def test_le_u_de_la_specification_concorde_avec_une_norme_du_document(reference):
    u"""There is NO divergence between the two official documents.

    An earlier version of this reference announced one: 0.654 in the
    specification against 0.646 in the documentation. The error was mine.
    The documentation describes the same window under two families of standards
    and the U value differs — 0.646 under EN ISO 52022-3 reference conditions,
    0.654 under ISO 15099 winter conditions. The specification takes the second,
    to the unit.

    This test exists because this false discrepancy almost went into a letter
    to the author of these documents.
    """
    concordance = reference['concordance_du_u_vitrage']
    assert concordance['statut'] == 'RELEVE', concordance
    assert concordance['norme_concordante'] == 'iso_15099_conditions_hiver'
    assert concordance['valeur'] == 0.654
    autres = concordance['autres_valeurs_du_document']
    assert autres['en_iso_52022_3_conditions_reference'] == 0.646


def test_le_u_differe_selon_la_norme_dans_le_meme_document(reference):
    u"""The fact that explains the false discrepancy, locked explicitly."""
    blocs = reference['fenetre_entiere']['blocs']
    reference_52022 = blocs['en_iso_52022_3_conditions_reference']['grandeurs']
    hiver_15099 = blocs['iso_15099_conditions_hiver']['grandeurs']
    assert (reference_52022['u_vitrage_w_m2k']['store_rentre']
            != hiver_15099['u_vitrage_w_m2k']['store_rentre'])


def test_le_store_deploye_ameliore_le_u(reference):
    u"""An extra layer in front of the glazing cannot degrade its U value."""
    hiver = reference['fenetre_entiere']['blocs'][
        'iso_15099_conditions_hiver']['grandeurs']['u_vitrage_w_m2k']
    assert hiver['store_deploye'] < hiver['store_rentre'], hiver


def test_les_apports_du_maillon_1d_sont_chiffres(reference):
    u"""Only the SCHEDULES refer to SIA 2024; the power levels are written."""
    apports = reference['parametres']['apports']
    assert apports['appareils_w_m2']['valeur'] == 11
    assert apports['eclairage_w_m2']['valeur'] == 12.5
    assert apports['eclairage_puissance_installee_w_m2']['valeur'] == 12.5
    assert apports['personnes_activite_met']['valeur'] == 1.2
    assert apports['personnes_m2_par_personne']['valeur'] == 14


def test_le_nombre_doccupants_est_coherent_avec_la_surface(reference):
    u"""3.43 persons for 48 m² at 14 m²/person: arithmetic check.

    The specification gives both figures separately. If they did not
    cross-check, one of them would be misread.
    """
    usage = reference['parametres']['usage']['personnes_par_piece']['valeur']
    par_personne = reference['parametres']['apports'][
        'personnes_m2_par_personne']['valeur']
    assert abs(usage * par_personne - 48.0) < 0.1, (usage, par_personne)


def test_chaque_source_porte_son_empreinte(reference):
    u"""Four sources: three official PDFs and the SIA 2024 authority extract.

    The latter does not come from the shared link — the specification refers to
    SIA 2024:2021 without reproducing the data sheet — hence the different path.
    """
    assert len(reference['sources']) == 4
    for cle, source in reference['sources'].items():
        assert len(source['sha256']) == 64, cle
        assert source['role'], cle
        attendu = ('sia4010_evidence/' if cle == 'extrait_autorite_sia_2024'
                   else 'SIA_4010_geteilter_Link/')
        assert source['fichier'].startswith(attendu), cle


def test_le_gain_sensible_des_occupants_est_releve(reference):
    u"""It makes any met → watts conversion unnecessary.

    I had blocked link 1D by asserting that a body-surface area convention was
    needed. That was true of the specification and false as a conclusion: the
    SIA 2024 data sheet gives the sensible gain in W/m².
    """
    apports = reference['parametres']['apports']
    assert apports['personnes_gain_sensible_w_m2']['valeur'] == 4.9
    assert apports['personnes_simultaneite_annuelle']['valeur'] == 0.8


def test_lextrait_dautorite_porte_la_bonne_categorie(reference):
    source = reference['sources']['extrait_autorite_sia_2024']
    assert '3.1' in source['categorie']


def test_aucun_champ_ne_reste_a_confirmer_en_silence(reference):
    u"""An `A_CONFIRMER` is admissible, but it must carry its reason."""
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
    u"""Freezing the data does not make 1E validatable, and the file must say so."""
    assert u'posable' in reference['pourquoi']
    joint = u' '.join(reference['reserves'])
    assert u'Aucun cas' in joint
