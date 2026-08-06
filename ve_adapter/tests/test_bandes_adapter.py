# -*- coding: utf-8 -*-
"""Tests de l'adaptateur des tests a bandes (2 a 6), SANS VE.

Un double de `ResultsReader` remplace l'API : tout ce qui compte ici est
testable sans licence. Les tests visent surtout ce qu'une implementation
plausible mais fausse ferait -- deviner un nom de variable, replier une
agregation inconnue sur la somme, ou renvoyer un candidat vide qui se lirait
comme « rien ne passe ».
"""

import io
import os

import pytest

from engine import sia_bandes_engine as moteur
from ve_adapter import bandes_adapter as adaptateur


class FauxResultsReader(object):
    """Double minimal de `iesve.ResultsReader`.

    CALQUE SUR L'API REELLE, pas sur ce qu'on en supposait. La version
    precedente de ce double prenait un `niveau` en argument de
    `get_variables` et rendait des chaines : elle VALIDAIT l'erreur qu'elle
    aurait du signaler. VE, sur `ZOER_C1.aps` le 2026-08-06, refuse
    l'argument (`ArgumentError`) et rend des dictionnaires portant
    `aps_varname`, `display_name` et `model_level`.

    Attributes:
        series: `{(varname, niveau): serie}`.
        variables: Liste d'entrees, chacune un dict comme l'API en rend.
    """

    def __init__(self, series=None, variables=None):
        self.series = series or {}
        self.variables = list(variables or [])
        self.ferme = False

    def get_variables(self):
        # Aucun argument : c'est le contrat reel de l'API.
        return list(self.variables)

    def get_results(self, varname, niveau):
        cle = (varname, niveau)
        if cle not in self.series:
            raise KeyError(varname)
        return self.series[cle]

    def get_room_results(self, room_id, varname, niveau):
        return self.get_results(varname, niveau)

    def close(self):
        self.ferme = True


def _ref(numero):
    try:
        return moteur.charger_reference(numero)
    except IOError:
        pytest.skip(u'reference Test %d absente' % numero)


# --------------------------------------------------------------------------
# Garde-fou d'API
# --------------------------------------------------------------------------

def test_lapi_reelle_presente_toutes_les_methodes_employees():
    """Ecrit contre une VE 2025 introspectee, pas contre la documentation."""
    assert adaptateur.verifier_api() == dict(
        (m, True) for m in adaptateur.METHODES_REQUISES)


def test_une_methode_disparue_est_signalee():
    """Le cas s'est deja produit : `element_categories` etait cherche sur
    `VECdbProject` alors qu'il appartient au module `iesve`."""
    amputee = {'ResultsReader': {'members': ['close']}}
    with pytest.raises(adaptateur.ApiIncompatible, match='get_results'):
        adaptateur.verifier_api(amputee)


def test_une_surface_vide_est_signalee():
    with pytest.raises(adaptateur.ApiIncompatible):
        adaptateur.verifier_api({})


# --------------------------------------------------------------------------
# Liaisons : rien n'est devine
# --------------------------------------------------------------------------

@pytest.mark.parametrize('numero', adaptateur.TESTS_COUVERTS)
def test_les_liaisons_couvrent_exactement_les_grandeurs(numero):
    """Une espace de trop dans un libelle allemand rendrait la liaison
    introuvable une fois resolue. Les cles sont generees, pas retapees."""
    reference = _ref(numero)
    attendues = set(g['libelle_de'] for g in reference['grandeurs'])
    assert set(adaptateur.LIAISONS[numero]) == attendues


@pytest.mark.parametrize('numero', adaptateur.TESTS_COUVERTS)
def test_aucune_liaison_nest_resolue_par_defaut(numero):
    """Aucun `aps_varname` ne peut etre etabli hors d'un `.aps` reel."""
    assert adaptateur.liaisons_resolues(numero) == {}


def test_extraire_refuse_quand_rien_nest_resolu():
    """Retourner un candidat vide se lirait comme « rien ne passe », alors que
    rien n'a ete cherche."""
    with pytest.raises(adaptateur.LiaisonNonResolue, match='decouvrir_variables'):
        adaptateur.extraire_candidat(2, FauxResultsReader(), _ref(2))


def test_un_test_hors_perimetre_est_refuse():
    with pytest.raises(ValueError, match='hors de port'):
        adaptateur.extraire_candidat(7, FauxResultsReader(), {'grandeurs': []})


# --------------------------------------------------------------------------
# Agregation
# --------------------------------------------------------------------------

def test_somme_annuelle_convertit_les_watts_en_kwh():
    """8760 h a 1000 W valent 8760 kWh, pas 8 760 000."""
    assert adaptateur.agreger([1000.0] * 8760, 'somme_annuelle') == 8760.0


@pytest.mark.parametrize('methode,attendu', [
    ('moyenne', 2.0), ('maximum', 3.0), ('minimum', 1.0)])
def test_les_autres_agregations(methode, attendu):
    assert adaptateur.agreger([1.0, 2.0, 3.0], methode) == attendu


def test_une_methode_inconnue_est_refusee():
    """Jamais de repli silencieux sur la somme : ce serait un nombre plausible
    et faux."""
    with pytest.raises(ValueError, match='inconnue'):
        adaptateur.agreger([1.0], 'mediane')


def test_une_serie_vide_donne_none_pas_zero():
    """Zero est une mesure ; l'absence n'en est pas une."""
    assert adaptateur.agreger([], 'somme_annuelle') is None
    assert adaptateur.agreger(None, 'moyenne') is None


def test_les_trous_sont_ecartes_pas_comptes_comme_zero():
    assert adaptateur.agreger([1.0, None, 3.0], 'moyenne') == 2.0


# --------------------------------------------------------------------------
# Extraction, une fois une liaison resolue
# --------------------------------------------------------------------------

def _resoudre(monkeypatch, numero, libelle, varname, niveau):
    """Resout UNE liaison, sans toucher au module d'origine."""
    liaisons = dict(
        (cle, dict((k, dict(v)) for k, v in valeur.items()))
        for cle, valeur in adaptateur.LIAISONS.items())
    liaisons[numero][libelle]['aps_varname'] = varname
    liaisons[numero][libelle]['niveau'] = niveau
    monkeypatch.setattr(adaptateur, 'LIAISONS', liaisons)


def test_une_liaison_resolue_produit_un_candidat_exploitable(monkeypatch):
    reference = _ref(3)
    libelle = reference['grandeurs'][0]['libelle_de']
    _resoudre(monkeypatch, 3, libelle, 'LIGHT_POWER', adaptateur.NIVEAU_LOCAL)

    lecteur = FauxResultsReader(
        series={('LIGHT_POWER', adaptateur.NIVEAU_LOCAL): [1000.0] * 8760})
    candidat = adaptateur.extraire_candidat(3, lecteur, reference)

    assert libelle in candidat
    # Tous les cas partagent la meme serie dans ce double : tous a 8760 kWh.
    assert set(candidat[libelle].values()) == {8760.0}
    # Et le moteur doit savoir le consommer.
    assert moteur.evaluer(reference, candidat)['nb_non_evaluables'] == 0


def test_une_serie_absente_ne_fabrique_pas_de_valeur(monkeypatch):
    reference = _ref(3)
    libelle = reference['grandeurs'][0]['libelle_de']
    _resoudre(monkeypatch, 3, libelle, 'INEXISTANT', adaptateur.NIVEAU_LOCAL)
    assert adaptateur.extraire_candidat(3, FauxResultsReader(), reference) == {}


def test_les_grandeurs_non_resolues_restent_absentes(monkeypatch):
    """Elles ne doivent pas apparaitre a zero : le moteur les traite en
    NOT_CHECKABLE, ce qui est la verite."""
    reference = _ref(2)
    libelle = reference['grandeurs'][0]['libelle_de']
    _resoudre(monkeypatch, 2, libelle, 'SOLAR', adaptateur.NIVEAU_LOCAL)

    lecteur = FauxResultsReader(
        series={('SOLAR', adaptateur.NIVEAU_LOCAL): [500.0] * 8760})
    candidat = adaptateur.extraire_candidat(2, lecteur, reference)

    assert list(candidat) == [libelle]
    assert reference['grandeurs'][1]['libelle_de'] not in candidat
    assert moteur.evaluer(reference, candidat)['nb_non_evaluables'] > 0


# --------------------------------------------------------------------------
# Decouverte
# --------------------------------------------------------------------------

def _variable(varname, niveau, display=None):
    """Entree de `get_variables()`, dans la forme reelle de l'API."""
    return {'aps_varname': varname, 'display_name': display or varname,
            'model_level': niveau, 'units_type': 'Power'}


_VARIABLES = [
    _variable('A', adaptateur.NIVEAU_LOCAL),
    _variable('B_SOLAR', adaptateur.NIVEAU_LOCAL, 'Window solar gains'),
    _variable('C', adaptateur.NIVEAU_SYSTEME),
]


def test_la_decouverte_liste_tout_le_fichier_sans_filtre():
    lecteur = FauxResultsReader(variables=_VARIABLES)
    trouvees = adaptateur.decouvrir_variables(lecteur)
    assert [v['aps_varname'] for v in trouvees] == ['A', 'B_SOLAR', 'C']


def test_le_niveau_se_lit_sur_la_variable_pas_sur_lappel():
    """`get_variables('z')` leve ArgumentError dans VE : le niveau est porte
    par `model_level`, entree par entree. Le filtrage est fait chez nous."""
    lecteur = FauxResultsReader(variables=_VARIABLES)
    trouvees = adaptateur.decouvrir_variables(lecteur, adaptateur.NIVEAU_LOCAL)
    assert [v['aps_varname'] for v in trouvees] == ['A', 'B_SOLAR']


def test_la_decouverte_filtre_sans_tenir_compte_de_la_casse():
    lecteur = FauxResultsReader(variables=_VARIABLES)
    trouvees = adaptateur.decouvrir_variables(
        lecteur, adaptateur.NIVEAU_LOCAL, 'solar')
    assert [v['aps_varname'] for v in trouvees] == ['B_SOLAR']


def test_le_motif_cherche_aussi_dans_le_libelle_daffichage():
    """« Window solar gains » est le display_name ; l'aps_varname peut etre
    tout autre. Ne chercher que dans l'un rendrait la decouverte aveugle."""
    lecteur = FauxResultsReader(variables=_VARIABLES)
    trouvees = adaptateur.decouvrir_variables(lecteur, motif='window')
    assert [v['aps_varname'] for v in trouvees] == ['B_SOLAR']


def test_la_cle_name_nexiste_pas_dans_lapi():
    """L'ancienne version filtrait sur `variable.get('name', ...)`. Ce champ
    n'existe pas : le filtre retombait sur le dict entier, donc matchait
    a peu pres n'importe quoi."""
    assert 'name' not in adaptateur.CHAMPS_NOMMANTS
    lecteur = FauxResultsReader(variables=_VARIABLES)
    assert adaptateur.decouvrir_variables(lecteur, motif='units_type') == []


def test_letat_des_liaisons_nomme_ce_qui_manque():
    texte = adaptateur.etat_des_liaisons()
    assert '0/8' in texte and '0/6' in texte
    assert 'decouvrir_variables' in texte


def test_pas_dimport_iesve_au_chargement():
    """Regle 4 : le module doit rester importable en CI, sans licence."""
    chemin = os.path.abspath(adaptateur.__file__).replace('.pyc', '.py')
    with io.open(chemin, encoding='utf-8') as flux:
        for numero, ligne in enumerate(flux, 1):
            nu = ligne.strip()
            assert not nu.startswith('import iesve'), numero
            assert not nu.startswith('from iesve'), numero


# --------------------------------------------------------------------------
# Candidats de sonde : des pistes, jamais des liaisons
# --------------------------------------------------------------------------

def test_un_candidat_ne_resout_aucune_liaison():
    """Le risque exact que cette separation existe pour ecarter : « Window
    solar gains » est un nom de variable VE releve pour le Test 1. Le reprendre
    tel quel pour le Test 2 produirait un nombre plausible et faux."""
    for numero in adaptateur.TESTS_COUVERTS:
        assert adaptateur.liaisons_resolues(numero) == {}


def test_extraire_ignore_integralement_les_candidats():
    """Meme la ou un candidat existe, l'extraction refuse de tourner."""
    assert adaptateur.candidats_a_confirmer(2)
    with pytest.raises(adaptateur.LiaisonNonResolue):
        adaptateur.extraire_candidat(2, FauxResultsReader(), _ref(2))


def test_les_candidats_portent_les_libelles_exacts_du_classeur():
    """Une cle qui ne correspond a aucune grandeur serait une piste morte."""
    for numero, pistes in adaptateur.CANDIDATS_RUNTIME.items():
        libelles = set(adaptateur.LIAISONS[numero])
        assert set(pistes) <= libelles, numero


def test_chaque_candidat_declare_sa_preuve_et_sa_reserve():
    """Une piste sans provenance ni reserve finit par etre prise pour un
    resultat."""
    for pistes in adaptateur.CANDIDATS_RUNTIME.values():
        for piste in pistes.values():
            assert piste['preuve']
            assert piste['niveau_de_preuve']
            assert piste['a_confirmer']


def test_le_candidat_solaire_est_marque_comme_allegation():
    """Le rapport de sonde d'origine est absent du depot : la trace ne peut pas
    etre rejouee. Le dire, plutot que de laisser croire a une confirmation."""
    piste = adaptateur.candidats_a_confirmer(2)[
        u'Jahresenergie solarer Wärmeeintrag']
    assert 'ALLEGATION' in piste['niveau_de_preuve']
    assert piste['aps_varname_candidat'] == u'Window solar gains'


def test_la_seconde_grandeur_du_test_2_na_pas_de_candidat():
    """La sonde marque `total_transmitted_solar_radiation` explicitement NON
    lie. Lui inventer une piste serait pire que de n'en avoir aucune."""
    assert u'Jahresenergie total transmittierte Solarstrahlung' not in \
        adaptateur.candidats_a_confirmer(2)


def test_letat_signale_le_candidat_sans_le_compter_comme_resolu():
    texte = adaptateur.etat_des_liaisons()
    assert '0/2' in texte
    assert 'candidat a confirmer' in texte
    assert 'Window solar gains' in texte


def test_les_tests_de_systeme_nont_aucun_candidat():
    """Lufterwarmer, Luftkuhler, WRG, Ventilateurs : la sonde n'a releve que du
    niveau local. Aucune piste, et c'est la verite."""
    for numero in (4, 5, 6):
        assert adaptateur.candidats_a_confirmer(numero) == {}
