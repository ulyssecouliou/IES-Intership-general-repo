# -*- coding: utf-8 -*-
u"""Tests du contrôle de provenance des modules (`scripts/bootstrap_check.py`).

Le défaut visé est réel et daté du 2026-08-06 : VEScripts avait en cache un
paquet `scripts` provenant de l'ancien dépôt `SIA_Compliance_Scripts`. Pour la
sonde APS, l'import a levé — cas bénin. Pour la sonde du Test 1, le module
existe dans les deux dépôts : **l'import aurait réussi**, en chargeant du code
antérieur aux corrections d'énumérés, sans rien signaler.

C'est ce cas silencieux que ces tests verrouillent.
"""

import io
import os

import pytest

from scripts import bootstrap_check

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))
_LANCEURS = ('Run_VE_SIA4010_Sonde_APS.py', 'Run_VE_SIA4010_Sonde_Test1.py')


class FauxModule(object):
    """Module minimal, avec ou sans `__file__`."""

    def __init__(self, fichier=None):
        if fichier is not None:
            self.__file__ = fichier


# --------------------------------------------------------------------------
# Détection
# --------------------------------------------------------------------------

def test_un_module_du_bon_depot_ne_gene_pas():
    table = {'scripts.sonde_aps': FauxModule(
        os.path.join(_RACINE, 'scripts', 'sonde_aps.py'))}
    assert bootstrap_check.modules_outside_repository(_RACINE, table) == []


def test_le_cas_silencieux_est_detecte():
    """`run_test1_dans_ve` existe dans les DEUX depots : l'import reussit et
    charge la mauvaise version. Rien ne leve, rien ne previent."""
    intrus = os.path.join('C:', os.sep, 'ailleurs', 'SIA_Compliance_Scripts',
                          'scripts', 'run_test1_dans_ve.py')
    table = {'scripts.run_test1_dans_ve': FauxModule(intrus)}
    trouves = bootstrap_check.modules_outside_repository(_RACINE, table)
    assert [nom for nom, _ in trouves] == ['scripts.run_test1_dans_ve']


@pytest.mark.parametrize('paquet', bootstrap_check.PACKAGES)
def test_tous_les_paquets_du_projet_sont_surveilles(paquet):
    """Surveiller `scripts` seul laisserait passer un `ve_adapter` etranger,
    qui est justement celui qui produit les nombres."""
    table = {paquet: FauxModule(os.path.join('C:', os.sep, 'ailleurs',
                                             paquet, '__init__.py'))}
    assert len(bootstrap_check.modules_outside_repository(_RACINE, table)) == 1


def test_un_module_etranger_au_projet_est_ignore():
    """`numpy` ou `openpyxl` viennent d'ailleurs par construction."""
    table = {'numpy': FauxModule(os.path.join('C:', os.sep, 'py', 'numpy.py'))}
    assert bootstrap_check.modules_outside_repository(_RACINE, table) == []


def test_un_nom_qui_commence_pareil_nest_pas_du_projet():
    """`scriptsomething` n'est pas un sous-module de `scripts`."""
    table = {'scriptsomething': FauxModule(
        os.path.join('C:', os.sep, 'ailleurs', 'x.py'))}
    assert bootstrap_check.modules_outside_repository(_RACINE, table) == []


def test_un_module_sans_fichier_nest_pas_accuse():
    """Un paquet d'espace de noms n'a pas de `__file__` : rien a confronter,
    donc rien a reprocher. Accuser sans preuve ferait echouer des runs sains."""
    assert bootstrap_check.modules_outside_repository(_RACINE, {'scripts': FauxModule()}) == []


def test_la_comparaison_ignore_la_casse_du_chemin():
    """Windows : `C:\\Users` et `c:\\users` designent le meme dossier."""
    table = {'scripts.x': FauxModule(
        os.path.join(_RACINE.upper(), 'scripts', 'x.py'))}
    assert bootstrap_check.modules_outside_repository(_RACINE, table) == []


def test_un_depot_voisin_de_meme_prefixe_est_bien_un_intrus():
    """`...repo-ancien` commence par `...repo` : une comparaison de chaines
    sans separateur le prendrait pour le bon depot."""
    table = {'scripts.x': FauxModule(_RACINE + '-ancien' + os.sep + 'x.py')}
    assert len(bootstrap_check.modules_outside_repository(_RACINE, table)) == 1


# --------------------------------------------------------------------------
# Diagnostic
# --------------------------------------------------------------------------

def test_le_message_nomme_le_fichier_fautif():
    """Sans le chemin, l'utilisateur ne peut rien faire du message."""
    intrus = [('scripts.x', 'C:\\ailleurs\\scripts\\x.py')]
    message = bootstrap_check.intrusion_message(_RACINE, intrus)
    assert 'C:\\ailleurs\\scripts\\x.py' in message
    assert 'scripts.x' in message


def test_le_message_donne_la_manoeuvre():
    """Un diagnostic sans issue n'aide personne : le cache ne se purge qu'en
    rouvrant VE."""
    message = bootstrap_check.intrusion_message(_RACINE, [('scripts.x', 'ailleurs')])
    assert 'Closing VE' in message


def test_le_message_dit_que_les_resultats_ne_valent_rien():
    message = bootstrap_check.intrusion_message(_RACINE, [('scripts.x', 'ailleurs')])
    assert 'trustworthy' in message


def test_pas_de_message_quand_tout_va_bien():
    assert bootstrap_check.intrusion_message(_RACINE, []) == u''


def test_check_refuse_de_laisser_tourner(monkeypatch, capsys):
    monkeypatch.setattr(bootstrap_check, 'modules_outside_repository',
                        lambda racine: [('scripts.x', 'ailleurs')])
    assert bootstrap_check.check(_RACINE) is False
    assert 'STOP' in capsys.readouterr().out


def test_check_laisse_passer_un_depot_sain():
    """Le depot courant est sain : le controle ne doit pas bloquer la CI."""
    assert bootstrap_check.check(_RACINE) is True


# --------------------------------------------------------------------------
# Les lanceurs appliquent bien la purge
# --------------------------------------------------------------------------

def _source(nom):
    with io.open(os.path.join(_RACINE, nom), encoding='utf-8') as flux:
        return flux.read()


@pytest.mark.parametrize('lanceur', _LANCEURS)
def test_le_lanceur_purge_avant_dimporter(lanceur):
    """La purge doit precéder le premier import du projet, sinon elle arrive
    trop tard : un module deja charge n'est jamais recharge."""
    source = _source(lanceur)
    purge = source.find('del sys.modules[')
    premier_import = source.find('from scripts import')
    assert purge > 0, lanceur
    assert purge < premier_import, lanceur


@pytest.mark.parametrize('lanceur', _LANCEURS)
def test_le_lanceur_met_sa_racine_en_tete(lanceur):
    """`if _RACINE not in sys.path` ne suffit pas : un autre depot deja present
    resterait devant."""
    source = _source(lanceur)
    assert 'sys.path.insert(0, _RACINE)' in source
    assert 'sys.path.remove(_RACINE)' in source


@pytest.mark.parametrize('lanceur', _LANCEURS)
def test_le_lanceur_controle_la_provenance(lanceur):
    source = _source(lanceur)
    assert 'bootstrap_check.check(_RACINE)' in source


@pytest.mark.parametrize('lanceur', _LANCEURS)
def test_le_lanceur_purge_les_memes_paquets_que_le_controle(lanceur):
    """Purger moins que ce qu'on surveille laisserait un intrus detecte mais
    jamais evince."""
    source = _source(lanceur)
    for paquet in bootstrap_check.PACKAGES:
        assert "'%s'" % paquet in source, (lanceur, paquet)


@pytest.mark.parametrize('lanceur', _LANCEURS)
def test_le_lanceur_nappelle_pas_sys_exit(lanceur):
    """SystemExit remonte comme une erreur dans la fenetre de script de VE,
    alors que tout s'est bien passe.

    On cherche l'APPEL, pas le mot : les deux lanceurs expliquent en
    commentaire pourquoi ils s'en abstiennent.
    """
    for numero, ligne in enumerate(_source(lanceur).splitlines(), 1):
        code = ligne.split('#')[0]
        assert 'sys.exit(' not in code, (lanceur, numero)
