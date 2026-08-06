# -*- coding: utf-8 -*-
u"""Tests des parties PURES de `scripts/sonde_aps.py`.

La sonde tourne dans VE, donc l'essentiel n'est pas testable ici. Le sont :

* la **recherche du `.aps`**, qui doit prendre le plus récent et ne pas
  parcourir un projet entier ;
* le **résumé de série**, qui ne doit ni recopier 8760 points ni lever sur une
  valeur exotique ;
* le **refus de tourner hors VE**, qui doit être franc et ne rien écrire.
"""

import io
import json
import os

import pytest

from scripts import sonde_aps as sonde


# --------------------------------------------------------------------------
# Recherche du fichier de résultats
# --------------------------------------------------------------------------

def _fabriquer(dossier, chemin_relatif, horodatage):
    """Crée un fichier vide et lui fixe une date de modification.

    Args:
        dossier: Racine.
        chemin_relatif: Chemin sous la racine.
        horodatage: Date de modification à imposer.

    Returns:
        str: Chemin absolu du fichier créé.
    """
    chemin = os.path.join(str(dossier), *chemin_relatif.split('/'))
    parent = os.path.dirname(chemin)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(chemin, 'w', encoding='utf-8') as flux:
        flux.write(u'')
    os.utime(chemin, (horodatage, horodatage))
    return chemin


def test_le_plus_recent_vient_en_premier(tmp_path):
    """Sur un projet où plusieurs cas ont tourné, c'est la dernière simulation
    qui intéresse — pas celle que l'ordre alphabétique met devant."""
    _fabriquer(tmp_path, 'vista/aaa.aps', 1000)
    recent = _fabriquer(tmp_path, 'vista/zzz.aps', 9000)
    assert sonde.trouver_aps(str(tmp_path))[0] == recent


def test_la_recherche_est_recursive(tmp_path):
    """L'arborescence d'un projet VE n'est pas supposée : on descend."""
    attendu = _fabriquer(tmp_path, 'vista/sous/cas.aps', 1000)
    assert attendu in sonde.trouver_aps(str(tmp_path))


def test_la_recherche_ne_descend_pas_indefiniment(tmp_path):
    """Un projet volumineux produirait un rapport illisible."""
    trop_loin = 'a/b/c/d/e/perdu.aps'
    _fabriquer(tmp_path, trop_loin, 1000)
    assert sonde.trouver_aps(str(tmp_path)) == []


def test_les_autres_extensions_sont_ignorees(tmp_path):
    _fabriquer(tmp_path, 'vista/modele.gbxml', 1000)
    assert sonde.trouver_aps(str(tmp_path)) == []


def test_lextension_est_insensible_a_la_casse(tmp_path):
    attendu = _fabriquer(tmp_path, 'CAS.APS', 1000)
    assert sonde.trouver_aps(str(tmp_path)) == [attendu]


@pytest.mark.parametrize('racine', [None, '', '/dossier/qui/nexiste/pas'])
def test_un_dossier_absent_ne_leve_pas(racine):
    """La sonde doit consigner l'absence, pas s'interrompre dessus."""
    assert sonde.trouver_aps(racine) == []


def test_le_nombre_de_fichiers_est_borne(tmp_path):
    for numero in range(sonde.LIMITE_FICHIERS + 15):
        _fabriquer(tmp_path, 'vista/cas%03d.aps' % numero, 1000 + numero)
    assert len(sonde.trouver_aps(str(tmp_path))) == sonde.LIMITE_FICHIERS


# --------------------------------------------------------------------------
# Résumé de série
# --------------------------------------------------------------------------

def test_une_serie_horaire_est_resumee_pas_recopiee():
    """8760 points par variable, sur des dizaines de variables : le rapport
    deviendrait illisible et masquerait ce qu'on y cherche."""
    resume = sonde._resume_serie([float(i) for i in range(8760)])
    assert resume['nb_points'] == 8760
    assert resume['minimum'] == 0.0
    assert resume['maximum'] == 8759.0
    assert len(resume['premieres_valeurs']) == 6


def test_la_somme_permet_de_reconnaitre_une_unite_aberrante():
    """Une série en W sommée sur l'année donne un nombre mille fois trop
    grand : c'est ce qui le rend visible dans le rapport."""
    assert sonde._resume_serie([1000.0] * 8760)['somme'] == 8760000.0


def test_une_serie_vide_est_declaree_vide():
    assert sonde._resume_serie([])['nb_points'] == 0


def test_les_valeurs_non_numeriques_sont_ecartees():
    resume = sonde._resume_serie([1.0, None, 'x', 3.0])
    assert resume['nb_points'] == 2
    assert resume['maximum'] == 3.0


def test_un_objet_non_iterable_ne_leve_pas():
    """L'API peut renvoyer autre chose qu'une séquence : le `repr` renseigne
    mieux qu'une exception qui interromprait le relevé."""
    assert 'non_iterable' in sonde._resume_serie(object())


# --------------------------------------------------------------------------
# Aperçu d'un jeu de résultats
# --------------------------------------------------------------------------

def test_lapercu_resume_chaque_variable():
    apercu = sonde._apercu_resultats({'Fan power': [1.0, 2.0]})
    assert apercu['Fan power']['nb_points'] == 2


def test_une_forme_inattendue_est_rendue_telle_quelle():
    """Mieux vaut un `repr` exploitable qu'un résumé inventé."""
    assert sonde._apercu_resultats(['a', 'b']) == ['a', 'b']


# --------------------------------------------------------------------------
# Refus hors VE
# --------------------------------------------------------------------------

def test_hors_ve_la_sonde_nannonce_aucun_releve(monkeypatch):
    monkeypatch.setattr(sonde, '_dans_ve', lambda: False)
    rapport = sonde.sonder()
    assert rapport['dans_ve'] is False
    assert rapport['etapes'] == []


def test_hors_ve_aucun_rapport_nest_ecrit(monkeypatch, tmp_path):
    """Un fichier vide sur disque se lirait comme « la sonde a tourné et n'a
    rien trouvé », ce qui est faux : elle n'a rien pu chercher."""
    cible = os.path.join(str(tmp_path), 'sonde_aps.json')
    monkeypatch.setattr(sonde, 'CHEMIN_RAPPORT', cible)
    monkeypatch.setattr(sonde, '_dans_ve', lambda: False)
    sonde.sonder()
    assert not os.path.exists(cible)


def test_main_hors_ve_rend_un_entier(monkeypatch):
    """Depuis le bouton Run, une exception n'affiche qu'une trace."""
    monkeypatch.setattr(sonde, '_dans_ve', lambda: False)
    assert sonde.main(()) == 1


def test_labsence_daps_est_une_erreur_explicite():
    with pytest.raises(RuntimeError, match='ApacheSim'):
        sonde._sans_aps()


# --------------------------------------------------------------------------
# Cohérence avec ce que la sonde doit débloquer
# --------------------------------------------------------------------------

def test_les_trois_niveaux_de_ladaptateur_sont_interroges():
    """Interroger un seul niveau laisserait les tests 4 à 6 sans piste : leurs
    grandeurs désignent des organes de traitement d'air."""
    from ve_adapter import bandes_adapter as adaptateur
    interroges = set(niveau for niveau, _ in sonde.NIVEAUX)
    assert {adaptateur.NIVEAU_LOCAL, adaptateur.NIVEAU_SYSTEME,
            adaptateur.NIVEAU_METEO} <= interroges


def test_le_rapport_porte_son_avertissement(monkeypatch):
    monkeypatch.setattr(sonde, '_dans_ve', lambda: False)
    assert 'validation' in sonde.sonder()['avertissement']


def test_le_rapport_va_sous_outputs():
    """Jamais dans refs/ : ce n'est pas un référentiel figé."""
    normalise = sonde.CHEMIN_RAPPORT.replace(os.sep, '/')
    assert '/outputs/' in normalise
    assert '/refs/' not in normalise


def test_le_rapport_est_du_json_valide(monkeypatch, tmp_path):
    """Il sera relu par script : un rapport illisible ne débloque rien."""
    cible = os.path.join(str(tmp_path), 'sonde_aps.json')
    monkeypatch.setattr(sonde, 'CHEMIN_RAPPORT', cible)
    sonde._ecrire({'dans_ve': True, 'etapes': [{'nom': 'x', 'statut': 'OK'}]})
    with io.open(cible, encoding='utf-8') as flux:
        assert json.load(flux)['etapes'][0]['nom'] == 'x'


@pytest.mark.parametrize('valeur', [3, 3.0, object(), ['/tmp'], {'p': '/tmp'}])
def test_un_chemin_de_projet_non_textuel_ne_leve_pas(valeur):
    """`VEProject.path` n'est pas garanti etre une chaine, et
    `os.path.isdir(3)` interpreterait un entier comme un descripteur de
    fichier — silencieusement, avec un resultat arbitraire."""
    assert sonde.trouver_aps(valeur) == []


# --------------------------------------------------------------------------
# Couverture du relevé, sans VE
# --------------------------------------------------------------------------

class FauxLecteur(object):
    """Double de `ResultsReader` qui note comment on l'appelle.

    Attributes:
        appels: Liste de `(methode, arguments)`, dans l'ordre.
    """

    results_per_day = 24
    first_day = 1
    last_day = 365
    year = 2026
    weather_file = 'DRYCOLD.fwt'
    hvac_file = ''

    def __init__(self):
        self.appels = []
        self.variables = []

    def get_variables(self):
        self.appels.append(('get_variables', ()))
        return list(self.variables)

    #: Ce que ZOER_C1.aps a reellement rendu le 2026-08-06. `get_process_
    #: variables` exige l'un de ces noms : sans argument il leve ArgumentError.
    PROCESSUS = ['Process Material flow', 'Process Product flow',
                 'Process Heat input', 'Process Heat output']

    def __getattr__(self, nom):
        def methode(*arguments):
            self.appels.append((nom, arguments))
            if nom == 'get_apache_systems':
                return ['SYS1']
            if nom == 'get_process_list':
                return list(self.PROCESSUS)
            return []
        return methode


def _relever_a_blanc():
    """Déroule `_relever` contre un double et rend les appels observés.

    Returns:
        tuple: `(appels, etapes)`.
    """
    lecteur = FauxLecteur()
    etapes = []

    def etape(nom, fonction):
        try:
            etapes.append((nom, 'OK', fonction()))
        except Exception as erreur:  # noqa: BLE001
            etapes.append((nom, 'ECHEC', erreur))
        return etapes[-1][2] if etapes[-1][1] == 'OK' else None

    sonde._relever(etape, lecteur)
    return lecteur.appels, etapes


def test_la_forme_sans_argument_est_celle_qui_repond():
    """Tranche par VE le 2026-08-06 sur ZOER_C1.aps : `get_variables()` rend
    la liste, `get_variables('z')` leve ArgumentError. Le double refuse
    l'argument comme VE le fait."""
    appels, _ = _relever_a_blanc()
    formes = [args for methode, args in appels if methode == 'get_variables']
    assert formes == [()]


def test_les_formes_a_argument_restent_tentees():
    """Si une autre version de VE les acceptait, le rapport le dirait — au
    lieu de laisser croire au contraire sur la foi d'un seul fichier."""
    _, etapes = _relever_a_blanc()
    tentees = [nom for nom, _, _ in etapes if nom.startswith('get_variables(')]
    for niveau in ('z', 'v', 'w'):
        assert any(repr(niveau) in nom for nom in tentees), niveau


def test_un_echec_sur_les_formes_a_argument_ne_perd_pas_la_liste():
    """C'est le cas reel : trois etapes en echec, et pourtant le releve
    complet doit etre dans le rapport."""
    lecteur = FauxLecteur()
    lecteur.variables = [{'aps_varname': 'A', 'model_level': 'z'}]
    rapport = {}

    def etape(nom, fonction):
        try:
            return fonction()
        except Exception:  # noqa: BLE001
            return None

    sonde._relever(etape, lecteur, rapport)
    assert rapport['variables'] == [{'aps_varname': 'A', 'model_level': 'z'}]


def test_les_portes_dentree_systeme_et_energie_sont_interrogees():
    """C'est ce que le probe preexistant n'interroge pas, et c'est la que
    vivent Lufterwarmer, Luftkuhler, WRG et Ventilatoren."""
    appels, _ = _relever_a_blanc()
    methodes = set(methode for methode, _ in appels)
    for attendue in ('get_apache_systems', 'get_energy_uses',
                     'get_energy_meters', 'get_energy_sources',
                     'get_units', 'get_process_variables'):
        assert attendue in methodes, attendue


def test_le_cadre_temporel_est_releve():
    """Sans pas de temps ni annee, une somme annuelle n'a pas de sens."""
    _, etapes = _relever_a_blanc()
    noms = set(nom for nom, _, _ in etapes)
    assert 'results_per_day' in noms and 'weather_file' in noms


class LecteurAmpute(FauxLecteur):
    """Double dont une porte d'entree est indisponible.

    Le `__getattr__` doit etre defini sur la CLASSE : pose sur une instance, il
    n'est jamais consulte, et le test passerait a vide.
    """

    def __getattr__(self, nom):
        if nom == 'get_energy_uses':
            def indisponible(*_):
                raise RuntimeError('methode absente de cette version')
            return indisponible
        return FauxLecteur.__getattr__(self, nom)


def test_une_methode_qui_leve_ninterrompt_pas_le_releve():
    """Une porte d'entree absente est une information ; perdre les suivantes
    serait une perte seche."""
    lecteur = LecteurAmpute()
    etapes = []

    def etape(nom, fonction):
        try:
            fonction()
            etapes.append((nom, 'OK'))
        except Exception:  # noqa: BLE001
            etapes.append((nom, 'ECHEC'))
        return None

    sonde._relever(etape, lecteur)
    statuts = dict(etapes)
    # Le double doit vraiment avoir echoue, sinon le test ne prouve rien.
    assert statuts['get_energy_uses'] == 'ECHEC'
    # Et le releve doit avoir continue au-dela.
    assert statuts['get_units'] == 'OK'
    assert statuts['get_process_list'] == 'OK'


def test_get_process_variables_est_appele_avec_un_processus():
    """Sans argument il leve ArgumentError. La liste des processus vient de
    `get_process_list`, constate sur ZOER_C1.aps le 2026-08-06."""
    appels, _ = _relever_a_blanc()
    passes = [args for methode, args in appels
              if methode == 'get_process_variables']
    assert passes, 'get_process_variables jamais appele'
    assert all(len(args) == 1 for args in passes)
    assert ('Process Heat input',) in passes


def test_la_liste_complete_des_variables_echappe_au_plafond():
    """Le releve du 2026-08-06 a ete tronque a 500 entrees par le plafond des
    etapes, et AUCUNE variable de niveau « z » n'y a survecu : un garde-fou
    de lisibilite avait coupe exactement ce que la sonde existe pour
    rapporter."""
    lecteur = FauxLecteur()
    nombreuses = [{'aps_varname': 'V%04d' % i, 'display_name': 'v',
                   'model_level': 'z' if i % 2 else 'e'}
                  for i in range(sonde.LIMITE_ELEMENTS_ETAPE + 250)]
    lecteur.variables = nombreuses
    rapport = {}

    def etape(nom, fonction):
        try:
            return fonction()
        except Exception:  # noqa: BLE001
            return None

    sonde._relever(etape, lecteur, rapport)
    assert len(rapport['variables']) == len(nombreuses)
    assert rapport['variables_par_niveau']['z'] > 0
    assert rapport['variables_par_niveau']['e'] > 0


def test_une_variable_est_reduite_a_ce_qui_sert():
    reduite = sonde._variable_lisible({
        'aps_varname': 'Window solar gains', 'display_name': 'Solar gain',
        'model_level': 'z', 'units_type': 'Power', 'inutile': 1})
    assert reduite['aps_varname'] == 'Window solar gains'
    assert 'inutile' not in reduite


def test_une_variable_de_forme_inattendue_est_signalee_pas_perdue():
    assert 'forme_inattendue' in sonde._variable_lisible('juste une chaine')


def test_les_comptes_par_niveau_sont_lisibles_en_console():
    comptes = sonde._compter_par_niveau([
        {'model_level': 'z'}, {'model_level': 'z'}, {'model_level': 'e'}])
    assert comptes == {'e': 1, 'z': 2}
    assert sonde._en_clair(comptes) == 'e=1, z=2'
