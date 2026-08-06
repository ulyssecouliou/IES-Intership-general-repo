# -*- coding: utf-8 -*-
"""Tests de `ve_adapter/test7_adapter.py` -- Test SIA 4010 n° 7, classe 5.

Même esprit que `test_test1_adapter.py` :

1. **Confrontation aux valeurs normatives figées** (`Spezifikation_Test7.pdf`,
   lu intégralement) -- les constantes codées en dur ne dérivent pas.
2. **Concordance verbatim des 11 libellés allemands** avec
   `refs/reference-data/test-7.ref.json` -- une faute de frappe romprait
   silencieusement l'appariement fait par `engine/test7_engine.py`.
3. **Résistance à la mutation** sur la lecture/agrégation horaire (mêmes
   pièges qu'au Test 1 : décalage de curseur, décimation au lieu de
   moyenne, pas de simulation non entier).
4. **Refus explicites** : `PV-Ertrag` ne doit jamais pouvoir entrer dans un
   plan d'extraction ; une grandeur absente du plan reste absente du
   candidat (jamais 0, jamais None fabriqué) ; une unité qui ne concorde
   pas avec ce que le fichier `.aps` déclare doit bloquer l'extraction.
5. **Bout en bout sans VE** : la fixture, une fois passée dans
   `engine.test7_engine.evaluer_test7`, doit produire exactement le
   comportement réel attendu (PV manquant -> NOT_CHECKABLE, jamais PASS).

Aucun `iesve` n'est requis : import paresseux (`_iesve()`), et tout ce qui
est testé ici est du calcul pur ou du dialogue avec un double.
"""

import calendar
import importlib.util
import io
import json
import os
import sys

import pytest

_ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)

from engine import test7_engine as moteur  # noqa: E402
from engine import scatter_band  # noqa: E402


def _charger_adaptateur():
    """Charge le module par chemin : `ve_adapter/` n'est pas un paquet."""
    chemin = os.path.join(RACINE, 've_adapter', 'test7_adapter.py')
    spec = importlib.util.spec_from_file_location('test7_adapter_sous_test', chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adaptateur = _charger_adaptateur()

HEURES_PAR_AN = 365 * 24


@pytest.fixture(scope='module')
def reference():
    chemin = os.path.join(RACINE, 'refs', 'reference-data', 'test-7.ref.json')
    if not os.path.exists(chemin):
        pytest.skip(u'référence Test 7 absente : %s' % chemin)
    with io.open(chemin, encoding='utf-8') as flux:
        return json.load(flux)


# ==========================================================================
# 1. Confrontation aux valeurs normatives figées -- Spezifikation_Test7.pdf
# ==========================================================================

def test_annee_de_simulation_est_2022_pas_2011():
    """Spezifikation_Test7.pdf p.1 : « 1.1.2022 bis 31.12.2022 ».

    Différent du Test 1 (2011) -- une confusion entre les deux modules
    romprait silencieusement l'agrégation mensuelle/annuelle (aucune des
    deux années n'est bissextile, donc l'erreur ne se verrait pas sur la
    seule longueur de la série).
    """
    assert adaptateur.ANNEE_SIMULATION == 2022
    assert not calendar.isleap(adaptateur.ANNEE_SIMULATION)
    assert adaptateur.HEURES_PAR_AN == HEURES_PAR_AN


def test_climaveneta_puissances_nominales():
    """Spezifikation_Test7.pdf p.2 : « Nennleistung Kälte: 55.9 kW »,
    « Nennleistung Wärme: 60.0 kW »."""
    pac = adaptateur.CLIMAVENETA_NX_W_Y_H_0182
    assert pac['puissance_nominale_froid_kw'] == 55.9
    assert pac['puissance_nominale_chaud_kw'] == 60.0


def test_distribution_froid_et_chaud_conformes_a_la_spec():
    """Spezifikation_Test7.pdf p.1 : pertes 5 %, auxiliaire 2 %, dont 50 %
    récupéré/reporté sur l'autre circuit -- pour le froid ET le chaud."""
    froid = adaptateur.DISTRIBUTION_FROID
    chaud = adaptateur.DISTRIBUTION_CHAUD
    assert froid['pertes_pct_de_la_chaleur_absorbee'] == 5.0
    assert froid['auxiliaire_pct_de_la_chaleur_absorbee'] == 2.0
    assert froid['auxiliaire_recupere_comme_charge_thermique_pct'] == 50.0
    assert chaud['pertes_pct_de_la_chaleur_delivree'] == 5.0
    assert chaud['auxiliaire_pct_de_la_chaleur_delivree'] == 2.0
    assert chaud['auxiliaire_recupere_dans_circuit_chauffage_pct'] == 50.0


def test_stockage_deux_ballons_de_2000_litres():
    """Spezifikation_Test7.pdf p.1 : « Volumen 2'000 l » pour les DEUX
    ballons (froid et chaud)."""
    assert adaptateur.STOCKAGE_FROID_LITRES == 2000
    assert adaptateur.STOCKAGE_CHAUD_LITRES == 2000


def test_appareils_sur_air_exterieur_conformes_a_la_spec():
    """Spezifikation_Test7.pdf p.4 : refroidisseur sec 70 kW, échangeur air
    extérieur 76 kW, ventilateur 0.045 kW/kW."""
    assert adaptateur.AEROREFROIDISSEUR_SEC_KW == 70.0
    assert adaptateur.ECHANGEUR_AIR_EXTERIEUR_KW == 76.0
    assert adaptateur.VENTILATEUR_PUISSANCE_SPECIFIQUE_KW_PAR_KW == 0.045


def test_circuit_glycol_conforme_a_la_spec_et_garde_sa_reserve():
    """Spezifikation_Test7.pdf p.4 : 19'000 kg/h, spread 4 K, ΔT air-fluide
    4 K à pleine charge, 50 % de la chaleur de pompe utile, pertes 5 %.

    Le « ? » du taux de glycol est VERBATIM dans la source SIA elle-même
    (« Wasser-Glykol-Gemisch 30%? ») -- ce test s'assure que personne ne le
    retire silencieusement en "nettoyant" la constante, ce qui masquerait
    une incertitude qui n'est pas de notre fait.
    """
    circuit = adaptateur.CIRCUIT_GLYCOL
    assert circuit['massflow_kg_par_h'] == 19000.0
    assert circuit['spread_k'] == 4.0
    assert circuit['delta_t_air_fluide_pleine_charge_k'] == 4.0
    assert circuit['pompe_puissance_utile_dans_circuit_pct'] == 50.0
    assert circuit['pertes_pct'] == 5.0
    assert '30%' in circuit['fluide']
    assert '?' in circuit['fluide'], (
        "la réserve de la source SIA elle-même doit rester visible, "
        "pas être silencieusement résolue par ce module")


def test_bivalence_chaudiere_gaz_rendement_09():
    """Spezifikation_Test7.pdf p.4 : « Wärmeträger: Gas; Wirkungsgrad 0.9 »."""
    assert adaptateur.BIVALENCE['vecteur_energetique'] == 'gaz'
    assert adaptateur.BIVALENCE['rendement'] == 0.9


def test_pv_systeme_nombre_de_modules_et_puissances_declarees():
    """Spezifikation_Test7.pdf p.4 : toit 18x7+6x4=150 modules, 45 kWc,
    10°, est/ouest ; façade sud 13x4=52 modules, 15.6 kWc."""
    pv = adaptateur.PV_SYSTEME
    assert pv['toit_modules'] == 18 * 7 + 6 * 4 == 150
    assert pv['toit_kwp_declare'] == 45.0
    assert pv['toit_inclinaison_deg'] == 10.0
    assert pv['toit_orientation'] == 'est/ouest'
    assert pv['facade_modules'] == 13 * 4 == 52
    assert pv['facade_kwp_declare'] == 15.6
    assert pv['onduleur_rendement'] == 0.97


def test_reserve_puissance_pv_documentee_et_non_masquee():
    """150 x 310 W = 46.5 kWc et 52 x 310 W = 16.12 kWc NE concordent PAS
    avec les 45 / 15.6 kWc déclarés par la source -- alors que 300 W/module
    concorde exactement des deux côtés. Ce test vérifie que
    `verifier_coherence_puissance_pv()` DÉTECTE et REND VISIBLE cet écart,
    plutôt que de le corriger silencieusement (on ne sait pas laquelle des
    deux lectures est la bonne sans relire la page 4 du PDF source).

    Aucune incidence fonctionnelle : `PV-Ertrag` n'est jamais calculé par ce
    module quelle que soit l'issue de ce contrôle.
    """
    rapport = adaptateur.verifier_coherence_puissance_pv()
    assert rapport['toit_coherent_a_310w'] is False
    assert rapport['toit_coherent_a_300w'] is True
    assert rapport['facade_coherent_a_310w'] is False
    assert rapport['facade_coherent_a_300w'] is True


# ==========================================================================
# 2. Concordance verbatim avec test-7.ref.json
# ==========================================================================

def test_onze_grandeurs_dont_pv_ertrag(reference):
    assert len(adaptateur.GRANDEURS_TEST7) == 11
    libelles = set(g['libelle_de'] for g in adaptateur.GRANDEURS_TEST7)
    assert adaptateur.LIBELLE_PV_ERTRAG in libelles
    assert adaptateur.LIBELLE_PV_ERTRAG == u'PV-Ertrag'


def test_libelles_concordent_verbatim_avec_la_reference_figee(reference):
    """Si un libellé diffère d'un seul caractère (accent, espace), la
    grandeur correspondante deviendrait silencieusement NOT_CHECKABLE côté
    moteur -- ce test l'attraperait avant que ça n'arrive en pratique.
    """
    libelles_reference = set(g['libelle_de'] for g in reference['grandeurs'])
    libelles_module = set(g['libelle_de'] for g in adaptateur.GRANDEURS_TEST7)
    assert libelles_module == libelles_reference


def test_seul_pv_ertrag_est_exclu_du_jeu_verifiable(reference):
    verifiables = adaptateur._LIBELLES_VERIFIABLES_SANS_IRRADIANCE
    assert adaptateur.LIBELLE_PV_ERTRAG not in verifiables
    assert len(verifiables) == 10


# ==========================================================================
# 3. Température extérieure de Kloten -- source figée, résistance mutation
# ==========================================================================

def test_temperature_kloten_8760_heures_contigues():
    serie = adaptateur.charger_temperature_exterieure_kloten()
    assert len(serie) == HEURES_PAR_AN
    assert all(isinstance(v, float) for v in serie)


def test_temperature_kloten_concorde_avec_les_agregats_figes():
    """Contrôle croisé contre `sia-2028-kloten-temperature.json` (mêmes
    agrégats déjà calculés et figés par `reference-data-engineer`) :
    min -13.0167, max 34.1, moyenne 9.4692 °C."""
    serie = adaptateur.charger_temperature_exterieure_kloten()
    assert abs(min(serie) - (-13.0167)) < 1e-3
    assert abs(max(serie) - 34.1) < 1e-3
    assert abs(sum(serie) / len(serie) - 9.4692) < 1e-3


def test_temperature_kloten_refuse_un_fichier_tronque(tmp_path):
    chemin = tmp_path / 'kloten_tronque.csv'
    chemin.write_text(
        'heure,theta_e_air_c,moyenne_glissante_48h_c\n'
        + '\n'.join('%d,%f,%f' % (h, 0.0, 0.0) for h in range(1, 100)),
        encoding='utf-8')
    with pytest.raises(ValueError):
        adaptateur.charger_temperature_exterieure_kloten(str(chemin))


def test_temperature_kloten_refuse_des_heures_non_contigues(tmp_path):
    """Mutation plausible : un export trié par valeur au lieu de par heure."""
    lignes = ['heure,theta_e_air_c,moyenne_glissante_48h_c']
    heures = list(range(1, HEURES_PAR_AN + 1))
    heures[0], heures[1] = heures[1], heures[0]  # une seule permutation suffit
    for h in heures:
        lignes.append('%d,%f,%f' % (h, 0.0, 0.0))
    chemin = tmp_path / 'kloten_permute.csv'
    chemin.write_text('\n'.join(lignes), encoding='utf-8')
    with pytest.raises(ValueError):
        adaptateur.charger_temperature_exterieure_kloten(str(chemin))


def test_verification_temperature_simulee_identique_est_coherente():
    reference_serie = adaptateur.charger_temperature_exterieure_kloten()
    rapport = adaptateur.verifier_temperature_exterieure_simulee(
        list(reference_serie), reference_serie)
    assert rapport['coherent'] is True
    assert rapport['ecart_max_c'] == 0.0
    assert rapport['nb_heures'] == HEURES_PAR_AN


def test_verification_temperature_simulee_detecte_un_decalage():
    """Mutation réaliste : la VE simule avec un fichier météo décalé d'1 h ;
    le contrôle doit le voir, pas le laisser passer en silence."""
    reference_serie = adaptateur.charger_temperature_exterieure_kloten()
    decalee = reference_serie[1:] + reference_serie[:1]
    rapport = adaptateur.verifier_temperature_exterieure_simulee(
        decalee, reference_serie, tolerance_c=0.01)
    assert rapport['coherent'] is False
    assert rapport['ecart_max_c'] > 0.01


def test_verification_temperature_simulee_refuse_longueur_differente():
    reference_serie = adaptateur.charger_temperature_exterieure_kloten()
    with pytest.raises(ValueError):
        adaptateur.verifier_temperature_exterieure_simulee(
            reference_serie[:100], reference_serie)


# ==========================================================================
# 4. Lecture des séries de composants HVAC -- avec un double du ResultsReader
# ==========================================================================

class FauxResultsReader(object):
    """Double minimal de `iesve.ResultsReader` (§6.1.14), étendu au niveau
    `h` (HVAC component) par rapport à celui de `test_test1_adapter.py`."""

    def __init__(self, variables=None, unites=None, serie=None, results_per_day=24):
        self._variables = variables if variables is not None else []
        self._unites = unites if unites is not None else {}
        self._serie = serie if serie is not None else []
        self.results_per_day = results_per_day
        self.appels = []

    def get_variables(self):
        return self._variables

    def get_units(self):
        return self._unites

    def get_hvac_component_results(self, component_id, component_type, var_name,
                                    *args, **kwargs):
        self.appels.append((component_id, component_type, var_name))
        return list(self._serie)


def _plan_valide(aps_varname='Var HVAC test', unite='kW'):
    return {
        'component_id': 'COMPOSANT-1',
        'component_type': 'TYPE-RESOLU-PAR-APPELANT',
        'aps_varname': aps_varname,
        'unite_attendue': unite,
    }


def _lecteur_avec_variable(aps_varname='Var HVAC test', units_type='Power',
                            display_name='kW', serie=None, niveau='h'):
    return FauxResultsReader(
        variables=[{'aps_varname': aps_varname, 'model_level': niveau,
                    'units_type': units_type}],
        unites={units_type: {'units_metric': {'display_name': display_name}}},
        serie=serie or [0.0] * HEURES_PAR_AN)


def test_unite_declaree_est_lue_via_get_variables_et_get_units():
    lecteur = _lecteur_avec_variable(display_name='kW')
    unite = adaptateur._valeur_unite_declaree(lecteur, 'Var HVAC test', 'h')
    assert unite == 'kW'


def test_unite_declaree_leve_si_variable_absente():
    lecteur = FauxResultsReader(variables=[])
    with pytest.raises(RuntimeError):
        adaptateur._valeur_unite_declaree(lecteur, 'Var inconnue', 'h')


def test_unite_declaree_exige_le_bon_niveau_de_modele():
    """Même nom de variable, mauvais niveau : ne doit jamais être confondue
    avec une variable de zone ou de système homonyme."""
    lecteur = _lecteur_avec_variable(niveau='z')
    with pytest.raises(RuntimeError):
        adaptateur._valeur_unite_declaree(lecteur, 'Var HVAC test', 'h')


def test_serie_horaire_composant_passe_telle_quelle_a_pas_horaire():
    serie = [float(i % 7) for i in range(HEURES_PAR_AN)]
    lecteur = FauxResultsReader(serie=serie)
    horaire = adaptateur._serie_horaire_composant(
        lecteur, 'C1', 'TYPE', 'Var', 24)
    assert horaire == serie
    assert lecteur.appels == [('C1', 'TYPE', 'Var')]


def test_serie_horaire_composant_semi_horaire_est_moyennee():
    """Même défaut métrologique documenté pour le Test 1 : un pas de 30 min
    doit MOYENNER, jamais décimer."""
    serie = []
    for heure in range(HEURES_PAR_AN):
        serie.extend([float(heure), float(heure) + 2.0])  # moyenne = heure+1
    lecteur = FauxResultsReader(serie=serie)
    horaire = adaptateur._serie_horaire_composant(lecteur, 'C1', 'TYPE', 'Var', 48)
    assert len(horaire) == HEURES_PAR_AN
    assert abs(horaire[0] - 1.0) < 1e-12
    assert abs(horaire[-1] - (HEURES_PAR_AN - 1 + 1.0)) < 1e-12


def test_serie_horaire_composant_refuse_pas_non_entier():
    lecteur = FauxResultsReader(serie=[1.0] * (HEURES_PAR_AN * 3))
    for par_jour in (36, 10, 0):
        with pytest.raises(RuntimeError):
            adaptateur._serie_horaire_composant(lecteur, 'C1', 'TYPE', 'Var', par_jour)


def test_serie_horaire_composant_refuse_longueur_invalide():
    lecteur = FauxResultsReader(serie=[1.0] * (HEURES_PAR_AN - 24))
    with pytest.raises(RuntimeError):
        adaptateur._serie_horaire_composant(lecteur, 'C1', 'TYPE', 'Var', 24)


def test_energie_annuelle_kwh_somme_la_serie_horaire():
    serie = [1.0] * HEURES_PAR_AN
    assert abs(adaptateur._energie_annuelle_kwh(serie) - HEURES_PAR_AN) < 1e-9


def test_energie_annuelle_kwh_distingue_somme_de_moyenne():
    """Mutation classique : moyenner au lieu de sommer donne un nombre
    plausible (même ordre de grandeur qu'une puissance) mais faux."""
    serie = [float(i) for i in range(HEURES_PAR_AN)]
    somme = adaptateur._energie_annuelle_kwh(serie)
    moyenne = sum(serie) / len(serie)
    assert abs(somme - sum(serie)) < 1e-9
    assert abs(somme - moyenne) > 1.0  # très largement différent


def test_energie_annuelle_kwh_refuse_longueur_invalide():
    with pytest.raises(ValueError):
        adaptateur._energie_annuelle_kwh([1.0] * 100)


# ==========================================================================
# 5. Refus explicites de l'extraction par grandeur
# ==========================================================================

def test_pv_ertrag_ne_peut_jamais_entrer_dans_un_plan_dextraction():
    lecteur = _lecteur_avec_variable()
    with pytest.raises(ValueError) as erreur:
        adaptateur.extraire_grandeur_test7(
            lecteur, adaptateur.LIBELLE_PV_ERTRAG, _plan_valide())
    assert 'PV-Ertrag' in str(erreur.value) or 'irradiance' in str(erreur.value).lower()


def test_grandeur_inconnue_leve_key_error():
    lecteur = _lecteur_avec_variable()
    with pytest.raises(KeyError):
        adaptateur.extraire_grandeur_test7(
            lecteur, u'Grandeur qui n existe pas', _plan_valide())


def test_plan_incomplet_leve_key_error():
    lecteur = _lecteur_avec_variable()
    libelle = adaptateur.GRANDEURS_TEST7[0]['libelle_de']
    plan_troue = dict(_plan_valide())
    del plan_troue['aps_varname']
    with pytest.raises(KeyError):
        adaptateur.extraire_grandeur_test7(lecteur, libelle, plan_troue)


def test_unite_incoherente_bloque_lextraction():
    """Le plan attend 'kW' mais le fichier .aps déclare 'kWh' pour cette
    variable -- refus plutôt qu'une lecture silencieusement fausse."""
    lecteur = _lecteur_avec_variable(display_name='kWh')
    libelle = adaptateur.GRANDEURS_TEST7[0]['libelle_de']
    with pytest.raises(RuntimeError):
        adaptateur.extraire_grandeur_test7(
            lecteur, libelle, _plan_valide(unite='kW'))


def test_extraction_reussie_dune_grandeur():
    libelle = adaptateur.GRANDEURS_TEST7[0]['libelle_de']
    serie = [2.0] * HEURES_PAR_AN
    lecteur = _lecteur_avec_variable(serie=serie)
    valeur = adaptateur.extraire_grandeur_test7(lecteur, libelle, _plan_valide())
    assert abs(valeur - 2.0 * HEURES_PAR_AN) < 1e-9
    assert lecteur.appels == [('COMPOSANT-1', 'TYPE-RESOLU-PAR-APPELANT', 'Var HVAC test')]


def test_grandeur_absente_du_plan_reste_absente_du_candidat():
    """Jamais 0.0, jamais None fabriqué : la clé n'existe simplement pas."""
    libelle_present = adaptateur.GRANDEURS_TEST7[0]['libelle_de']
    lecteur = _lecteur_avec_variable(serie=[1.0] * HEURES_PAR_AN)
    plan = {libelle_present: _plan_valide()}
    candidat = adaptateur.extraire_candidat_test7_depuis_fichier(lecteur, plan)
    assert libelle_present in candidat
    autre_libelle = adaptateur.GRANDEURS_TEST7[1]['libelle_de']
    assert autre_libelle not in candidat
    assert adaptateur.LIBELLE_PV_ERTRAG not in candidat


def test_candidat_porte_une_provenance_signalant_labsence_de_pv():
    libelle = adaptateur.GRANDEURS_TEST7[0]['libelle_de']
    lecteur = _lecteur_avec_variable(serie=[1.0] * HEURES_PAR_AN)
    candidat = adaptateur.extraire_candidat_test7_depuis_fichier(
        lecteur, {libelle: _plan_valide()})
    assert candidat['_provenance']['pv_ertrag_disponible'] is False
    assert candidat['_provenance']['annee_simulation'] == 2022


def test_plan_extraction_avec_pv_ertrag_leve_avant_toute_lecture():
    lecteur = _lecteur_avec_variable()
    libelle = adaptateur.GRANDEURS_TEST7[0]['libelle_de']
    plan = {libelle: _plan_valide(), adaptateur.LIBELLE_PV_ERTRAG: _plan_valide()}
    with pytest.raises(ValueError):
        adaptateur.extraire_candidat_test7_depuis_fichier(lecteur, plan)


# ==========================================================================
# 6. Découverte (lecture seule, jamais invoquée automatiquement)
# ==========================================================================

def test_decouverte_filtre_par_niveau_et_par_jeton():
    lecteur = FauxResultsReader(variables=[
        {'aps_varname': 'Heat pump electrical power', 'display_name':
         'Heat pump electrical power', 'model_level': 'h'},
        {'aps_varname': 'Room air temperature', 'display_name':
         'Room air temperature', 'model_level': 'z'},
    ])
    trouves = adaptateur.decouvrir_variables_hvac(
        lecteur, jetons_requis=('heat', 'pump'), niveaux=('h',))
    assert len(trouves) == 1
    assert trouves[0]['aps_varname'] == 'Heat pump electrical power'


def test_decouverte_ne_leve_jamais_de_verdict():
    """Cette fonction n'est qu'une aide manuelle : elle ne doit jamais être
    appelée par le chemin d'extraction de confiance."""
    import inspect
    source_extraction = inspect.getsource(adaptateur.extraire_candidat_test7_depuis_fichier)
    source_extraction += inspect.getsource(adaptateur.extraire_grandeur_test7)
    assert 'decouvrir_variables_hvac' not in source_extraction


# ==========================================================================
# 7. Aucun chemin de code vers PV / VERenewables / EnergyUse -- refus
#    délibéré, pas une lacune API (docstring de module, point 5).
# ==========================================================================

def test_aucun_appel_reel_vers_les_symboles_pv_non_verifies():
    """Les symboles cités en PROSE (pour expliquer le refus) ne doivent
    jamais apparaître comme un appel exécutable dans le code."""
    chemin = os.path.join(RACINE, 've_adapter', 'test7_adapter.py')
    with io.open(chemin, encoding='utf-8') as f:
        source = f.read()
    motifs_interdits = (
        'get_pv_data(', 'get_pv_data_by_id(', 'get_chp_data(', 'get_wind_data(',
        '.prm_elec_gen_pv', 'VERenewables()', 'results_file.get_energy_results(',
        'results_file.get_energy_results_ex(',
    )
    for motif in motifs_interdits:
        assert motif not in source, (
            u"appel interdit trouvé : {0!r} -- PV-Ertrag ne doit jamais "
            u"être calculé par ce module".format(motif))


# ==========================================================================
# 8. Bout en bout avec le moteur -- sans VE
# ==========================================================================

def test_fixture_se_charge_et_ne_contient_jamais_pv_ertrag():
    fixture = adaptateur.charger_fixture_test7()
    assert adaptateur.LIBELLE_PV_ERTRAG not in fixture
    for libelle in adaptateur._LIBELLES_VERIFIABLES_SANS_IRRADIANCE:
        assert libelle in fixture
        assert isinstance(fixture[libelle], float)


def test_fixture_passee_dans_le_moteur_est_not_checkable_a_cause_du_pv(reference):
    """C'est le scénario réel : tout est simulé sauf le PV, faute
    d'irradiance. Le verdict global ne doit JAMAIS être PASS."""
    fixture = adaptateur.charger_fixture_test7()
    resultat = moteur.evaluer_test7(reference, fixture)
    assert resultat['verdict'] == scatter_band.VERDICT_NOT_CHECKABLE
    assert resultat['classe_5_validee'] is False
    assert resultat['nb_non_evaluables'] == 1
    assert resultat['nb_echecs'] == 0

    ligne_pv = [g for g in resultat['grandeurs']
                if g['libelle'] == adaptateur.LIBELLE_PV_ERTRAG][0]
    assert ligne_pv['conforme'] is None
    assert ligne_pv['statut'] == scatter_band.VERDICT_NOT_CHECKABLE


def test_fixture_est_dans_la_bande_pour_les_dix_grandeurs_verifiables(reference):
    """Les dix grandeurs simulées (fixture = moyenne +1 %) doivent tomber
    dans la bande recalculée -- sinon la fixture ne servirait à rien pour
    développer l'UI en régime "tout va bien"."""
    fixture = adaptateur.charger_fixture_test7()
    resultat = moteur.evaluer_test7(reference, fixture)
    for g in resultat['grandeurs']:
        if g['libelle'] == adaptateur.LIBELLE_PV_ERTRAG:
            continue
        assert g['conforme'] is True, (g['libelle'], g['statut'])


def test_no_iesve_import_au_niveau_module():
    """Même garde-fou que pour `test1_adapter.py` : `iesve` ne doit être
    importé qu'à la demande, à l'INTÉRIEUR de `_iesve()` (donc indenté),
    jamais au niveau module (donc en colonne 0)."""
    chemin = os.path.join(RACINE, 've_adapter', 'test7_adapter.py')
    with io.open(chemin, encoding='utf-8') as f:
        for numero, ligne in enumerate(f, 1):
            if ligne.startswith('import iesve') or ligne.startswith('from iesve'):
                pytest.fail(
                    u'import iesve non paresseux (colonne 0) ligne %d'
                    % numero)
