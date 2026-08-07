# -*- coding: utf-8 -*-
"""Tests des parties PURES de `scripts/run_test1_dans_ve.py`.

Ce script est fait pour tourner dans VE, donc l'essentiel n'est pas testable
ici. Mais deux choses le sont, et ce sont celles qui peuvent tromper :

* le **contrôle solaire**, qui décide si le modèle de ciel est un facteur
  confondant — une erreur de signe ou de tolérance y passerait inaperçue ;
* le **refus de tourner hors VE**, qui doit être franc plutôt que silencieux.
"""

import os

import pytest

from scripts import run_test1_dans_ve as run


# --------------------------------------------------------------------------
# Contrôle solaire
# --------------------------------------------------------------------------

def test_reference_solaire_est_celle_du_fichier_iso():
    """1547,1 kWh/m2 = colonne SV du fichier climatique public d'ISO 52016-1.

    Si quelqu'un « arrondissait » cette constante, le contrôle perdrait son
    sens : elle doit rester celle du référentiel figé.
    """
    assert run.IRRADIATION_SUD_REFERENCE_KWH_M2 == 1547.1


def test_ecart_nul_declare_le_ciel_neutre():
    rapport = run.controler_solaire(run.IRRADIATION_SUD_REFERENCE_KWH_M2)
    assert rapport['ecart_kwh_m2'] == 0.0
    assert rapport['modele_de_ciel_neutre'] is True


def test_petit_ecart_reste_neutre():
    """0,83 % : sous la tolérance de 1 %."""
    assert run.controler_solaire(1560.0)['modele_de_ciel_neutre'] is True


def test_gros_ecart_declare_le_ciel_confondant():
    """−6,3 % : tout écart thermique s'expliquerait d'abord par le solaire."""
    rapport = run.controler_solaire(1450.0)
    assert rapport['modele_de_ciel_neutre'] is False
    assert 'facteur confondant' in rapport['interpretation']


def test_le_signe_de_lecart_est_conserve():
    """Une valeur VE plus faible que la référence donne un écart NÉGATIF.

    Une valeur absolue prise trop tôt masquerait le sens de la divergence.
    """
    assert run.controler_solaire(1400.0)['ecart_kwh_m2'] < 0
    assert run.controler_solaire(1700.0)['ecart_kwh_m2'] > 0


def test_la_tolerance_est_symetrique():
    marge = run.IRRADIATION_SUD_REFERENCE_KWH_M2 * run.TOLERANCE_SOLAIRE_RELATIVE
    for valeur in (run.IRRADIATION_SUD_REFERENCE_KWH_M2 - marge * 0.99,
                   run.IRRADIATION_SUD_REFERENCE_KWH_M2 + marge * 0.99):
        assert run.controler_solaire(valeur)['modele_de_ciel_neutre'] is True


# --------------------------------------------------------------------------
# Périmètre des cas
# --------------------------------------------------------------------------

def test_les_six_cas_drycold_sont_ceux_du_test_1():
    assert run.CAS_DRYCOLD == ('600', '640', '900', '940', '600FF', '900FF')


def test_les_cas_kloten_sont_exclus_et_1e_en_fait_partie():
    """1E est le seul cas porteur du critère pass/fail : l'exclure doit être
    explicite, jamais un oubli."""
    assert '1E' in run.CAS_KLOTEN
    assert not set(run.CAS_DRYCOLD) & set(run.CAS_KLOTEN)


# --------------------------------------------------------------------------
# Garde-fous d'exécution
# --------------------------------------------------------------------------

def test_run_refuse_de_sexecuter_hors_ve():
    """Franchement, avec le motif — jamais un run silencieusement vide."""
    if run._dans_ve():
        pytest.skip(u'session VEScripts : le refus ne s\'applique pas')
    with pytest.raises((RuntimeError, NotImplementedError), match='iesve|VE'):
        run.executer()


def test_la_sonde_hors_ve_ne_pretend_rien_avoir_appris():
    if run._dans_ve():
        pytest.skip(u'session VEScripts')
    rapport = run.sonder()
    assert rapport['dans_ve'] is False
    assert rapport['etapes'] == []


def test_le_preflight_ne_leve_jamais():
    """Un préflight qui plante n'aide personne à diagnostiquer."""
    assert run.preflight() in (True, False)


# --------------------------------------------------------------------------
# Sélection du mode — VEScripts n'a qu'un bouton Run, pas de terminal
# --------------------------------------------------------------------------

def test_sans_argument_le_mode_depend_de_la_presence_de_ve():
    """C'est tout l'intérêt : appuyer sur Run doit faire la bonne chose."""
    attendu = 'sonde' if run._dans_ve() else 'preflight'
    assert run._mode_effectif(()) == attendu


@pytest.mark.parametrize("mode", ['preflight', 'sonde', 'evaluer', 'run'])
def test_un_argument_explicite_prime(mode):
    """Ceux qui ont un terminal gardent la main."""
    assert run._mode_effectif(('--' + mode,)) == mode


def test_la_constante_mode_prime_sur_la_detection(monkeypatch):
    """Le seul réglage à modifier depuis VE, faute de ligne de commande."""
    monkeypatch.setattr(run, 'MODE', 'evaluer')
    assert run._mode_effectif(()) == 'evaluer'


def test_une_constante_mode_invalide_retombe_sur_la_detection(monkeypatch):
    """Une faute de frappe ne doit pas rendre le script inerte."""
    monkeypatch.setattr(run, 'MODE', 'sond')  # faute volontaire
    assert run._mode_effectif(()) in ('sonde', 'preflight')


def test_largument_prime_meme_sur_la_constante(monkeypatch):
    monkeypatch.setattr(run, 'MODE', 'evaluer')
    assert run._mode_effectif(('--preflight',)) == 'preflight'


def test_main_sans_argument_ne_leve_pas():
    """Depuis le bouton Run, une exception non rattrapée n'affiche qu'une
    trace dans la fenêtre de script : le code doit rendre un entier."""
    assert main_sans_effet_de_bord() in (0, 1)


def main_sans_effet_de_bord():
    """Appelle `main` en mode préflight, qui ne modifie rien.

    Returns:
        int: Code de retour de `main`.
    """
    return run.main(('--preflight',))


def test_le_chemin_candidat_est_sous_outputs():
    """Jamais dans refs/ : ce n'est pas un référentiel figé."""
    assert 'outputs' in run.CHEMIN_CANDIDAT.replace(os.sep, '/')
    assert 'refs' not in run.CHEMIN_CANDIDAT.replace(os.sep, '/')


# --------------------------------------------------------------------------
# Porte d'entrée de la base de constructions
# --------------------------------------------------------------------------

class FauxProjetCdb(object):
    """Tient lieu de `VECdbProject` : ni liste, ni dict, ni chaîne."""


def test_get_projects_rend_un_dict_pas_une_liste():
    """Le défaut relevé dans la sonde v2.

    `projets[0]` sur `{'project': [...], 'system': [...]}` rend la clé
    « project », une chaîne — et le rapport a présenté les méthodes de `list`
    comme étant celles de `VECdbProject`. Rien n'avait levé.
    """
    projet = FauxProjetCdb()
    renvoi = {'project': [projet], 'system': [], 'manufacturer': []}
    assert run._premier_projet_cdb(renvoi) is projet


def test_les_bibliotheques_fournies_ne_sont_pas_le_projet():
    """« system » et « manufacturer » sont des bibliothèques livrées avec VE :
    les introspecter ne renseigne pas sur le modèle ouvert."""
    systeme = FauxProjetCdb()
    assert run._premier_projet_cdb(
        {'project': [], 'system': [systeme]}) is None


def test_une_liste_imbriquee_est_refusee():
    """Signe qu'on s'est encore trompé de niveau : mieux vaut None qu'un
    relevé faux."""
    assert run._premier_projet_cdb({'project': [['a', 'b']]}) is None


def test_une_chaine_est_refusee():
    """Exactement ce que renvoyait `projets[0]` avant la correction."""
    assert run._premier_projet_cdb(['project', 'system']) is None


def test_une_liste_de_projets_reste_acceptee():
    """Si une autre version de VE renvoyait une liste, la sonde doit continuer
    de fonctionner."""
    projet = FauxProjetCdb()
    assert run._premier_projet_cdb([projet]) is projet


@pytest.mark.parametrize('vide', [None, {}, [], {'project': []}])
def test_labsence_de_projet_donne_none(vide):
    assert run._premier_projet_cdb(vide) is None


def test_echouer_leve_avec_le_motif():
    """Une étape absente du rapport est une information perdue ; une étape en
    échec dit pourquoi."""
    with pytest.raises(RuntimeError, match='motif exact'):
        run._echouer('motif exact')


class FauxEnum(object):
    """Membre d enum a la maniere de iesve.project_types.

    Il s affiche comme une chaine mais n en est pas une : c est exactement ce
    qui a fait echouer la recherche par cle textuelle.
    """

    def __init__(self, nom):
        self.name = nom

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'iesve.project_types.%s' % self.name


def test_les_cles_de_get_projects_sont_des_enums_pas_des_chaines():
    """Releve du 2026-08-07 : get_projects() rend
    {iesve.project_types.project: [...]}. Un table.get('project') echoue
    en silence et rend une liste vide — ce qui se lit comme « aucun projet »
    alors qu il y en a un."""
    projet = FauxProjetCdb()
    renvoi = {FauxEnum('project'): [projet],
              FauxEnum('system'): [FauxProjetCdb()],
              FauxEnum('manufacturer'): [FauxProjetCdb()]}
    assert renvoi.get('project') is None      # le piege
    assert run._premier_projet_cdb(renvoi) is projet


def test_une_cle_chaine_reste_acceptee():
    """Si une version de VE indexait par chaines, la sonde doit continuer de
    fonctionner."""
    projet = FauxProjetCdb()
    assert run._premier_projet_cdb({'project': [projet]}) is projet


def test_les_bibliotheques_fournies_restent_ecartees_avec_des_enums():
    assert run._premier_projet_cdb({FauxEnum('system'): [FauxProjetCdb()]}) is None


def test_la_recherche_par_cle_textuelle_rend_une_liste_vide_si_absente():
    assert run._valeur_par_cle_textuelle({FauxEnum('system'): [1]}, 'project') == []


def test_la_sonde_passe_le_projet_pas_la_base():
    """VE repondait « 'VECdbDatabase' object has no attribute
    'create_construction' » : create_construction est porte par le PROJET.
    Meme classe d erreur que les enums cherches sur le mauvais conteneur."""
    import io as _io
    with _io.open(run.__file__.replace('.pyc', '.py'), encoding='utf-8') as f:
        source = f.read()
    assert 'creer_constructions_cas(projet_cdb' in source
    assert 'creer_constructions_cas(cdb' not in source


class FauxModuleIesve(object):
    """Module minimal portant un enum."""

    class material_categories(object):
        other = 15


def test_le_membre_denum_est_resolu_sans_supposer():
    assert run._membre_enum(
        FauxModuleIesve, 'material_categories', 'other') == 15


def test_un_enum_absent_est_signale():
    """C est l API qui a change : le dire vaut mieux que de retomber sur une
    valeur par defaut, qui simulerait sans rien signaler."""
    with pytest.raises(RuntimeError, match='absent du module'):
        run._membre_enum(FauxModuleIesve, 'inexistant', 'other')


def test_un_membre_absent_est_signale():
    with pytest.raises(RuntimeError, match='absent de'):
        run._membre_enum(FauxModuleIesve, 'material_categories', 'opaque')


def test_la_sonde_releve_les_cles_acceptees_par_set_properties():
    """Le 2026-08-07, set_properties a repondu « could not convert string to
    float: 'plasterboard' » : `description` n est pas une cle acceptee. En
    essayer d autres a l aveugle serait la cinquieme devinette ; la sonde
    releve get_properties() a la place."""
    import io as _io
    with _io.open(run.__file__.replace('.pyc', '.py'), encoding='utf-8') as f:
        source = f.read()
    assert 'LES CLES ACCEPTEES' in source
    assert 'get_properties()' in source
    assert 'set_properties sans description' in source


# --------------------------------------------------------------------------
# Minimum de masse accepte par VE
# --------------------------------------------------------------------------

def test_lechelle_commence_a_zero():
    """ISO 52016-1 donne 0 pour l isolant ideal : c est la premiere valeur a
    essayer, pas une que l on ecarte d avance."""
    assert run.ECHELLE_MINIMUM[0] == 0.0
    assert list(run.ECHELLE_MINIMUM) == sorted(run.ECHELLE_MINIMUM)


def test_lechelle_ne_descend_jamais_sous_zero():
    """ASHRAE 140 note (a) : « pas < 0 »."""
    assert all(v >= 0 for v in run.ECHELLE_MINIMUM)


def test_la_relecture_tolere_le_flottant_32_bits():
    assert run._proche(0.1599999964237213, 0.16)
    assert run._proche(0.0, 0.0)


def test_une_valeur_non_conservee_est_detectee():
    """Si VE ramene 0 a une valeur plancher, la relecture doit le voir."""
    assert not run._proche(10.0, 0.0)
    assert not run._proche(None, 0.0)


def test_le_releve_ne_conclut_pas_a_la_place_du_lecteur():
    """Il consigne les couples ecrit/relu ; c est leur lecture qui tranche.
    Choisir dans le script figerait une valeur sur un seul poste."""
    import io as _io
    with _io.open(run.__file__.replace('.pyc', '.py'), encoding='utf-8') as f:
        source = f.read()
    debut = source.index('def _echelle_de_minimum')
    corps = source[debut:debut + 1800]
    assert 'Aucune conclusion' in corps
    assert 'releves.append' in corps


# --------------------------------------------------------------------------
# Les epaisseurs sont-elles reellement posees ?
# --------------------------------------------------------------------------

def test_la_sonde_relit_les_epaisseurs_des_couches():
    """`add_layer(materiau_id, False)` n ecrit AUCUNE epaisseur, et
    l epaisseur n existe pas au niveau materiau. Une construction qui se cree
    sans lever, avec des epaisseurs par defaut, produirait des U credibles et
    faux — le mode de defaillance que ce projet doit empecher."""
    import io as _io
    with _io.open(run.__file__.replace('.pyc', '.py'), encoding='utf-8') as f:
        source = f.read()
    assert 'epaisseurs REELLES' in source
    assert '_proprietes_des_couches' in source


def test_le_releve_des_couches_ne_leve_pas():
    """Une sonde qui plante ne rapporte rien."""
    class CoucheMuette(object):
        def get_properties(self):
            raise RuntimeError('indisponible')

    class Construction(object):
        def get_layers(self):
            return [CoucheMuette()]

    releve = run._proprietes_des_couches(Construction())
    assert len(releve) == 1
    assert 'RuntimeError' in releve[0]['proprietes']


def test_un_get_layers_casse_est_consigne():
    class ConstructionCassee(object):
        def get_layers(self):
            raise RuntimeError('pas de couches')

    assert 'get_layers_a_echoue' in run._proprietes_des_couches(
        ConstructionCassee())


def test_le_releve_rend_les_proprietes_de_chaque_couche():
    class Couche(object):
        def __init__(self, epaisseur):
            self._e = epaisseur

        def get_properties(self):
            return {'thickness': self._e}

    class Construction(object):
        def get_layers(self):
            return [Couche(0.012), Couche(0.066)]

    releve = run._proprietes_des_couches(Construction())
    assert [c['proprietes']['thickness'] for c in releve] == [0.012, 0.066]


# --------------------------------------------------------------------------
# Menage : une sonde doit rendre le modele tel qu elle l a trouve
# --------------------------------------------------------------------------

def test_les_materiaux_dessai_sont_supprimes():
    """Sept passages avaient laisse 76 materiaux dans la base de constructions
    du projet de l utilisateur : les identifiants sont passes de PYOP1 a
    PYOP76. Une sonde en lecture ne doit rien laisser derriere elle."""
    class ProjetCdb(object):
        def __init__(self):
            self.supprimes = []

        def delete_material(self, identifiant):
            self.supprimes.append(identifiant)

    projet = ProjetCdb()
    bilan = run._supprimer_materiaux(projet, ['PYOP1', 'PYOP2'])
    assert projet.supprimes == ['PYOP1', 'PYOP2']
    assert bilan['echecs'] == {}


def test_un_refus_de_suppression_est_consigne_pas_masque():
    """Un materiau utilise par une construction ne se supprime pas : c est
    normal, et ca doit se lire dans le rapport."""
    class ProjetRecalcitrant(object):
        def delete_material(self, identifiant):
            raise RuntimeError('materiau utilise')

    bilan = run._supprimer_materiaux(ProjetRecalcitrant(), ['PYOP1'])
    assert bilan['supprimes'] == []
    assert 'materiau utilise' in bilan['echecs']['PYOP1']


def test_les_identifiants_vides_sont_ignores():
    """Un materiau dont l identifiant n a pas pu etre lu ne doit pas faire
    echouer le menage des autres."""
    class Projet(object):
        def __init__(self):
            self.appels = 0

        def delete_material(self, identifiant):
            self.appels += 1

    projet = Projet()
    run._supprimer_materiaux(projet, [None, '', 'PYOP1'])
    assert projet.appels == 1


def test_le_menage_ne_touche_pas_aux_materiaux_des_constructions():
    """Ceux-la sont legitimement utilises par les parois creees."""
    import io as _io
    with _io.open(run.__file__.replace('.pyc', '.py'), encoding='utf-8') as f:
        source = f.read()
    assert 'Ceux' in source and 'constructions n en font pas partie' in source


# --------------------------------------------------------------------------
# Geometrie : relever avant d ecrire
# --------------------------------------------------------------------------

class FauxImporteur(object):
    @staticmethod
    def import_file(*args):
        """import_file(file_name, heal_geometry, cap_mode, cap_height)"""


class FauxModuleAvecImport(object):
    ImportGBXML = FauxImporteur


def test_les_deux_orthographes_dimport_sont_relevees():
    """La documentation ecrit `Import_file` (I majuscule), l introspection
    donne `import_file`. Elle s est deja trompee une fois : on releve les deux
    plutot que de la croire sur le reste."""
    releve = run._signature_dimport(FauxModuleAvecImport)
    assert 'import_file' in releve
    assert 'Import_file' in releve
    assert releve['Import_file'] == 'absent'
    assert 'file_name' in releve['import_file']['doc']


def test_un_importeur_absent_est_signale():
    class SansImport(object):
        pass

    assert 'absent du module' in run._signature_dimport(SansImport)['ImportGBXML']


def test_les_corps_du_modele_sont_releves_avec_leurs_surfaces():
    """Sans ce releve, un import « reussi » ne prouverait rien : c est le
    piege des epaisseurs a 1 mm."""
    class Corps(object):
        id = 'B1'
        name = 'cellule'
        type = 'room'

        def get_areas(self):
            return {'floor': 48.0}

        def get_room_data(self):
            return {'volume': 129.6}

    class Modele(object):
        model_type = 'real'

        def get_bodies(self, _selection):
            return [Corps()]

    class Projet(object):
        models = [Modele()]

    releve = run._corps_du_modele(Projet())
    assert releve[0]['nb_corps'] == 1
    # LISTE PLATE et cles APLATIES : imbriquer portait les surfaces au 4e
    # niveau, ou `_serialisable` les reduit a un repr tronque. Le releve du
    # 2026-08-07 est ressorti illisible pour cette seule raison.
    assert releve[1]['get_areas.floor'] == 48.0
    assert releve[1]['get_room_data.volume'] == 129.6


def test_un_modele_vide_est_signale():
    class Projet(object):
        models = []

    assert run._corps_du_modele(Projet()) == {'aucun_modele': True}


def test_un_get_bodies_casse_ne_fait_pas_planter():
    class Modele(object):
        model_type = 'real'

        def get_bodies(self, _selection):
            raise RuntimeError('indisponible')

    class Projet(object):
        models = [Modele()]

    assert 'get_bodies_a_echoue' in run._corps_du_modele(Projet())[0]


def test_les_surfaces_ne_sont_pas_tronquees_par_la_profondeur():
    """Le defaut du 2026-08-07 : le dictionnaire des surfaces etait au 4e
    niveau d imbrication, donc reduit a `repr(...)[:400]`. Un releve tronque
    ne sert a rien — c est justement ce qu on venait y chercher."""
    class Corps(object):
        id = 'B1'
        name = 'x'
        type = 'room'

        def get_areas(self):
            return dict(('cle_%02d' % i, float(i)) for i in range(30))

        def get_room_data(self):
            return {}

    class Modele(object):
        model_type = 'real'

        def get_bodies(self, _selection):
            return [Corps()]

    class Projet(object):
        models = [Modele()]

    detail = run._corps_du_modele(Projet())[1]
    assert detail['get_areas.cle_29'] == 29.0
