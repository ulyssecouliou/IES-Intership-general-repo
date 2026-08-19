# -*- coding: utf-8 -*-
"""Tests of the PURE parts of `scripts/run_test1_dans_ve.py`.

This script is designed to run inside VE, so most of it is not testable
here. But two things are, and they are the ones that can mislead:

* the **solar check**, which decides whether the sky model is a confounding
  factor — a sign error or tolerance error would pass unnoticed;
* the **refusal to run outside VE**, which must be frank rather than silent.
"""

import os

import pytest

from scripts import run_test1_dans_ve as run


# --------------------------------------------------------------------------
# Solar check
# --------------------------------------------------------------------------

def test_reference_solaire_est_celle_du_fichier_iso():
    """1547.1 kWh/m2 = SV column of the public ISO 52016-1 climate file.

    If someone 'rounded' this constant, the check would lose its
    meaning: it must remain that of the frozen reference.
    """
    assert run.IRRADIATION_SUD_REFERENCE_KWH_M2 == 1547.1


def test_ecart_nul_declare_le_ciel_neutre():
    rapport = run.controler_solaire(run.IRRADIATION_SUD_REFERENCE_KWH_M2)
    assert rapport['ecart_kwh_m2'] == 0.0
    assert rapport['modele_de_ciel_neutre'] is True


def test_petit_ecart_reste_neutre():
    """0.83%: below the 1% tolerance."""
    assert run.controler_solaire(1560.0)['modele_de_ciel_neutre'] is True


def test_gros_ecart_declare_le_ciel_confondant():
    """-6.3%: any thermal discrepancy would first be explained by solar."""
    rapport = run.controler_solaire(1450.0)
    assert rapport['modele_de_ciel_neutre'] is False
    assert 'facteur confondant' in rapport['interpretation']


def test_le_signe_de_lecart_est_conserve():
    """A VE value lower than the reference gives a NEGATIVE deviation.

    Taking the absolute value too early would hide the direction of divergence.
    """
    assert run.controler_solaire(1400.0)['ecart_kwh_m2'] < 0
    assert run.controler_solaire(1700.0)['ecart_kwh_m2'] > 0


def test_la_tolerance_est_symetrique():
    marge = run.IRRADIATION_SUD_REFERENCE_KWH_M2 * run.TOLERANCE_SOLAIRE_RELATIVE
    for valeur in (run.IRRADIATION_SUD_REFERENCE_KWH_M2 - marge * 0.99,
                   run.IRRADIATION_SUD_REFERENCE_KWH_M2 + marge * 0.99):
        assert run.controler_solaire(valeur)['modele_de_ciel_neutre'] is True


# --------------------------------------------------------------------------
# Scope of cases
# --------------------------------------------------------------------------

def test_les_six_cas_drycold_sont_ceux_du_test_1():
    assert run.CAS_DRYCOLD == ('600', '640', '900', '940', '600FF', '900FF')


def test_les_cas_kloten_sont_exclus_et_1e_en_fait_partie():
    """1E is the only case carrying the pass/fail criterion: excluding it must
    be explicit, never an oversight."""
    assert '1E' in run.CAS_KLOTEN
    assert not set(run.CAS_DRYCOLD) & set(run.CAS_KLOTEN)


# --------------------------------------------------------------------------
# Execution safeguards
# --------------------------------------------------------------------------

def test_run_refuse_de_sexecuter_hors_ve():
    """Explicitly, with the reason — never a silently empty run."""
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
    """A preflight that crashes helps no one to diagnose."""
    assert run.preflight() in (True, False)


# --------------------------------------------------------------------------
# Mode selection — VEScripts has only a Run button, not a terminal
# --------------------------------------------------------------------------

def test_sans_argument_le_mode_depend_de_la_presence_de_ve():
    """That is the whole point: pressing Run must do the right thing."""
    attendu = 'sonde' if run._dans_ve() else 'preflight'
    assert run._mode_effectif(()) == attendu


@pytest.mark.parametrize("mode", ['preflight', 'sonde', 'evaluer', 'run'])
def test_un_argument_explicite_prime(mode):
    """Those who have a terminal keep control."""
    assert run._mode_effectif(('--' + mode,)) == mode


def test_la_constante_mode_prime_sur_la_detection(monkeypatch):
    """The only setting to change from VE, for lack of a command line."""
    monkeypatch.setattr(run, 'MODE', 'evaluer')
    assert run._mode_effectif(()) == 'evaluer'


def test_une_constante_mode_invalide_retombe_sur_la_detection(monkeypatch):
    """A typo must not render the script inert."""
    monkeypatch.setattr(run, 'MODE', 'sond')  # intentional typo
    assert run._mode_effectif(()) in ('sonde', 'preflight')


def test_largument_prime_meme_sur_la_constante(monkeypatch):
    monkeypatch.setattr(run, 'MODE', 'evaluer')
    assert run._mode_effectif(('--preflight',)) == 'preflight'


def test_main_sans_argument_ne_leve_pas():
    """From the Run button, an uncaught exception only displays a trace
    in the script window: the code must return an integer."""
    assert main_sans_effet_de_bord() in (0, 1)


def main_sans_effet_de_bord():
    """Calls `main` in preflight mode, which modifies nothing.

    Returns:
        int: Return code of `main`.
    """
    return run.main(('--preflight',))


def test_le_chemin_candidat_est_sous_outputs():
    """Never in refs/: it is not a frozen reference."""
    assert 'outputs' in run.CHEMIN_CANDIDAT.replace(os.sep, '/')
    assert 'refs' not in run.CHEMIN_CANDIDAT.replace(os.sep, '/')


# --------------------------------------------------------------------------
# Entry point of the construction database
# --------------------------------------------------------------------------

class FauxProjetCdb(object):
    """Stand-in for `VECdbProject`: neither a list, nor a dict, nor a string."""


def test_get_projects_rend_un_dict_pas_une_liste():
    """The defect found in probe v2.

    `projets[0]` on `{'project': [...], 'system': [...]}` returns the key
    'project', a string — and the report presented the methods of `list`
    as those of `VECdbProject`. Nothing had raised.
    """
    projet = FauxProjetCdb()
    renvoi = {'project': [projet], 'system': [], 'manufacturer': []}
    assert run._premier_projet_cdb(renvoi) is projet


def test_les_bibliotheques_fournies_ne_sont_pas_le_projet():
    """'system' and 'manufacturer' are libraries shipped with VE:
    introspecting them does not tell us about the open model."""
    systeme = FauxProjetCdb()
    assert run._premier_projet_cdb(
        {'project': [], 'system': [systeme]}) is None


def test_une_liste_imbriquee_est_refusee():
    """Sign that we took the wrong level again: better None than a
    wrong record."""
    assert run._premier_projet_cdb({'project': [['a', 'b']]}) is None


def test_une_chaine_est_refusee():
    """Exactly what `projets[0]` returned before the fix."""
    assert run._premier_projet_cdb(['project', 'system']) is None


def test_une_liste_de_projets_reste_acceptee():
    """If another VE version returned a list, the probe must continue
    to work."""
    projet = FauxProjetCdb()
    assert run._premier_projet_cdb([projet]) is projet


@pytest.mark.parametrize('vide', [None, {}, [], {'project': []}])
def test_labsence_de_projet_donne_none(vide):
    assert run._premier_projet_cdb(vide) is None


def test_echouer_leve_avec_le_motif():
    """A step absent from the report is lost information; a failed step
    says why."""
    with pytest.raises(RuntimeError, match='motif exact'):
        run._echouer('motif exact')


class FauxEnum(object):
    """Enum member in the manner of iesve.project_types.

    It displays as a string but is not one: this is exactly what caused
    the key lookup to fail.
    """

    def __init__(self, nom):
        self.name = nom

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'iesve.project_types.%s' % self.name


def test_les_cles_de_get_projects_sont_des_enums_pas_des_chaines():
    """Finding from 2026-08-07: get_projects() returns
    {iesve.project_types.project: [...]}. A table.get('project') fails
    silently and returns an empty list — which reads as 'no project'
    when there is one."""
    projet = FauxProjetCdb()
    renvoi = {FauxEnum('project'): [projet],
              FauxEnum('system'): [FauxProjetCdb()],
              FauxEnum('manufacturer'): [FauxProjetCdb()]}
    assert renvoi.get('project') is None      # the trap
    assert run._premier_projet_cdb(renvoi) is projet


def test_une_cle_chaine_reste_acceptee():
    """If a VE version indexed by strings, the probe must continue to work."""
    projet = FauxProjetCdb()
    assert run._premier_projet_cdb({'project': [projet]}) is projet


def test_les_bibliotheques_fournies_restent_ecartees_avec_des_enums():
    assert run._premier_projet_cdb({FauxEnum('system'): [FauxProjetCdb()]}) is None


def test_la_recherche_par_cle_textuelle_rend_une_liste_vide_si_absente():
    assert run._valeur_par_cle_textuelle({FauxEnum('system'): [1]}, 'project') == []


def test_la_sonde_passe_le_projet_pas_la_base():
    """VE responded 'VECdbDatabase object has no attribute
    create_construction': create_construction is carried by the PROJECT.
    Same error class as enums looked up on the wrong container."""
    import io as _io
    with _io.open(run.__file__.replace('.pyc', '.py'), encoding='utf-8') as f:
        source = f.read()
    assert 'creer_constructions_cas(projet_cdb' in source
    assert 'creer_constructions_cas(cdb' not in source


class FauxModuleIesve(object):
    """Minimal module carrying an enum."""

    class material_categories(object):
        other = 15


def test_le_membre_denum_est_resolu_sans_supposer():
    assert run._membre_enum(
        FauxModuleIesve, 'material_categories', 'other') == 15


def test_un_enum_absent_est_signale():
    """It is the API that changed: saying so is better than falling back to a
    default value, which would simulate without signalling anything."""
    with pytest.raises(RuntimeError, match='absent du module'):
        run._membre_enum(FauxModuleIesve, 'inexistant', 'other')


def test_un_membre_absent_est_signale():
    with pytest.raises(RuntimeError, match='absent de'):
        run._membre_enum(FauxModuleIesve, 'material_categories', 'opaque')


def test_la_sonde_releve_les_cles_acceptees_par_set_properties():
    """On 2026-08-07, set_properties responded 'could not convert string to
    float: plasterboard': `description` is not an accepted key. Trying others
    blindly would be the fifth guessing game; the probe reads get_properties()
    instead."""
    import io as _io
    with _io.open(run.__file__.replace('.pyc', '.py'), encoding='utf-8') as f:
        source = f.read()
    assert 'LES CLES ACCEPTEES' in source
    assert 'get_properties()' in source
    assert 'set_properties sans description' in source


# --------------------------------------------------------------------------
# Minimum mass accepted by VE
# --------------------------------------------------------------------------

def test_lechelle_commence_a_zero():
    """ISO 52016-1 gives 0 for the ideal insulator: it is the first value to
    try, not one to discard in advance."""
    assert run.ECHELLE_MINIMUM[0] == 0.0
    assert list(run.ECHELLE_MINIMUM) == sorted(run.ECHELLE_MINIMUM)


def test_lechelle_ne_descend_jamais_sous_zero():
    """ASHRAE 140 note (a): 'not < 0'."""
    assert all(v >= 0 for v in run.ECHELLE_MINIMUM)


def test_la_relecture_tolere_le_flottant_32_bits():
    assert run._proche(0.1599999964237213, 0.16)
    assert run._proche(0.0, 0.0)


def test_une_valeur_non_conservee_est_detectee():
    """If VE returns 0 at a floor value, the readback must see it."""
    assert not run._proche(10.0, 0.0)
    assert not run._proche(None, 0.0)


def test_le_releve_ne_conclut_pas_a_la_place_du_lecteur():
    """It records written/read pairs; reading them settles the question.
    Choosing in the script would freeze a value on a single item."""
    import io as _io
    with _io.open(run.__file__.replace('.pyc', '.py'), encoding='utf-8') as f:
        source = f.read()
    debut = source.index('def _echelle_de_minimum')
    corps = source[debut:debut + 1800]
    assert 'No conclusions are drawn here' in corps
    assert 'releves.append' in corps


# --------------------------------------------------------------------------
# Are the thicknesses really written?
# --------------------------------------------------------------------------

def test_la_sonde_relit_les_epaisseurs_des_couches():
    """`add_layer(material_id, False)` writes NO thickness, and
    the thickness does not exist at material level. A construction that creates
    itself without raising, with default thicknesses, would produce plausible
    and wrong U values — the failure mode this project must prevent."""
    import io as _io
    with _io.open(run.__file__.replace('.pyc', '.py'), encoding='utf-8') as f:
        source = f.read()
    assert 'epaisseurs REELLES' in source
    assert '_proprietes_des_couches' in source


def test_le_releve_des_couches_ne_leve_pas():
    """A probe that crashes reports nothing."""
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
# Cleanup: a probe must leave the model as it found it
# --------------------------------------------------------------------------

def test_les_materiaux_dessai_sont_supprimes():
    """Seven passes had left 76 materials in the user's project construction
    database: identifiers had gone from PYOP1 to PYOP76. A read-only probe
    must leave nothing behind."""
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
    """A material used by a construction cannot be deleted: this is
    normal, and it must be readable in the report."""
    class ProjetRecalcitrant(object):
        def delete_material(self, identifiant):
            raise RuntimeError('materiau utilise')

    bilan = run._supprimer_materiaux(ProjetRecalcitrant(), ['PYOP1'])
    assert bilan['supprimes'] == []
    assert 'materiau utilise' in bilan['echecs']['PYOP1']


def test_les_identifiants_vides_sont_ignores():
    """A material whose identifier could not be read must not cause
    the cleanup of the others to fail."""
    class Projet(object):
        def __init__(self):
            self.appels = 0

        def delete_material(self, identifiant):
            self.appels += 1

    projet = Projet()
    run._supprimer_materiaux(projet, [None, '', 'PYOP1'])
    assert projet.appels == 1


def test_le_menage_ne_touche_pas_aux_materiaux_des_constructions():
    """Those are legitimately used by the created walls."""
    import io as _io
    with _io.open(run.__file__.replace('.pyc', '.py'), encoding='utf-8') as f:
        source = f.read()
    assert 'CONSTRUCTION materials are not concerned' in source


# --------------------------------------------------------------------------
# Geometry: read before writing
# --------------------------------------------------------------------------

class FauxImporteur(object):
    @staticmethod
    def import_file(*args):
        """import_file(file_name, heal_geometry, cap_mode, cap_height)"""


class FauxModuleAvecImport(object):
    ImportGBXML = FauxImporteur


def test_les_deux_orthographes_dimport_sont_relevees():
    """The documentation writes `Import_file` (capital I), introspection
    gives `import_file`. It was wrong once: we record both rather than
    trusting it on the rest."""
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
    """Without this record, a 'successful' import would prove nothing: that
    is the trap of 1 mm thicknesses."""
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
    # FLAT LIST and FLATTENED keys: nesting placed the surfaces at the 4th
    # level, where `_serialisable` reduces them to a truncated repr. The
    # 2026-08-07 record came out unreadable for this single reason.
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
    """The 2026-08-07 defect: the surface dictionary was at the 4th nesting
    level, so reduced to `repr(...)[:400]`. A truncated record is useless —
    that is exactly what one came to find there."""
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
