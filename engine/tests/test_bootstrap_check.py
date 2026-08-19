# -*- coding: utf-8 -*-
u"""Tests of the module provenance check (`scripts/bootstrap_check.py`).

The targeted defect is real and dated 2026-08-06: VEScripts had cached a
`scripts` package from the older `SIA_Compliance_Scripts` repository. For the
APS probe, the import raised — a benign case. For the Test 1 probe, the module
exists in both repositories: **the import would have succeeded**, loading code
predating the enum fixes, without signalling anything.

It is this silent case that these tests lock down.
"""

import io
import os

import pytest

from scripts import bootstrap_check

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))
_LANCEURS = ('Run_VE_SIA4010_Sonde_APS.py', 'Run_VE_SIA4010_Sonde_Test1.py')


class FauxModule(object):
    """Minimal module, with or without `__file__`."""

    def __init__(self, fichier=None):
        if fichier is not None:
            self.__file__ = fichier


# --------------------------------------------------------------------------
# Detection
# --------------------------------------------------------------------------

def test_un_module_du_bon_depot_ne_gene_pas():
    table = {'scripts.sonde_aps': FauxModule(
        os.path.join(_RACINE, 'scripts', 'sonde_aps.py'))}
    assert bootstrap_check.modules_outside_repository(_RACINE, table) == []


def test_le_cas_silencieux_est_detecte():
    """`run_test1_dans_ve` exists in BOTH repositories: the import succeeds and
    loads the wrong version. Nothing raises, nothing warns."""
    intrus = os.path.join('C:', os.sep, 'ailleurs', 'SIA_Compliance_Scripts',
                          'scripts', 'run_test1_dans_ve.py')
    table = {'scripts.run_test1_dans_ve': FauxModule(intrus)}
    trouves = bootstrap_check.modules_outside_repository(_RACINE, table)
    assert [nom for nom, _ in trouves] == ['scripts.run_test1_dans_ve']


@pytest.mark.parametrize('paquet', bootstrap_check.PACKAGES)
def test_tous_les_paquets_du_projet_sont_surveilles(paquet):
    """Watching `scripts` alone would let a foreign `ve_adapter` through,
    which is exactly the one that produces the numbers."""
    table = {paquet: FauxModule(os.path.join('C:', os.sep, 'ailleurs',
                                             paquet, '__init__.py'))}
    assert len(bootstrap_check.modules_outside_repository(_RACINE, table)) == 1


def test_un_module_etranger_au_projet_est_ignore():
    """`numpy` or `openpyxl` come from elsewhere by construction."""
    table = {'numpy': FauxModule(os.path.join('C:', os.sep, 'py', 'numpy.py'))}
    assert bootstrap_check.modules_outside_repository(_RACINE, table) == []


def test_un_nom_qui_commence_pareil_nest_pas_du_projet():
    """`scriptsomething` is not a sub-module of `scripts`."""
    table = {'scriptsomething': FauxModule(
        os.path.join('C:', os.sep, 'ailleurs', 'x.py'))}
    assert bootstrap_check.modules_outside_repository(_RACINE, table) == []


def test_un_module_sans_fichier_nest_pas_accuse():
    """A namespace package has no `__file__`: nothing to compare,
    so nothing to reproach. Accusing without evidence would fail healthy runs."""
    assert bootstrap_check.modules_outside_repository(_RACINE, {'scripts': FauxModule()}) == []


def test_la_comparaison_ignore_la_casse_du_chemin():
    """Windows: `C:\\Users` and `c:\\users` designate the same folder."""
    table = {'scripts.x': FauxModule(
        os.path.join(_RACINE.upper(), 'scripts', 'x.py'))}
    assert bootstrap_check.modules_outside_repository(_RACINE, table) == []


def test_un_depot_voisin_de_meme_prefixe_est_bien_un_intrus():
    """`...repo-ancien` starts with `...repo`: a string comparison without a
    separator would take it for the right repository."""
    table = {'scripts.x': FauxModule(_RACINE + '-ancien' + os.sep + 'x.py')}
    assert len(bootstrap_check.modules_outside_repository(_RACINE, table)) == 1


# --------------------------------------------------------------------------
# Diagnostic
# --------------------------------------------------------------------------

def test_le_message_nomme_le_fichier_fautif():
    """Without the path, the user cannot act on the message."""
    intrus = [('scripts.x', 'C:\\ailleurs\\scripts\\x.py')]
    message = bootstrap_check.intrusion_message(_RACINE, intrus)
    assert 'C:\\ailleurs\\scripts\\x.py' in message
    assert 'scripts.x' in message


def test_le_message_donne_la_manoeuvre():
    """A diagnosis without a remedy helps no one: the cache can only be
    cleared by reopening VE."""
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
    """The current repository is healthy: the check must not block CI."""
    assert bootstrap_check.check(_RACINE) is True


# --------------------------------------------------------------------------
# Launchers apply the purge
# --------------------------------------------------------------------------

def _source(nom):
    with io.open(os.path.join(_RACINE, nom), encoding='utf-8') as flux:
        return flux.read()


@pytest.mark.parametrize('lanceur', _LANCEURS)
def test_le_lanceur_purge_avant_dimporter(lanceur):
    """The purge must precede the first project import, otherwise it arrives
    too late: an already-loaded module is never reloaded."""
    source = _source(lanceur)
    purge = source.find('del sys.modules[')
    premier_import = source.find('from scripts import')
    assert purge > 0, lanceur
    assert purge < premier_import, lanceur


@pytest.mark.parametrize('lanceur', _LANCEURS)
def test_le_lanceur_met_sa_racine_en_tete(lanceur):
    """`if _RACINE not in sys.path` is not enough: another repository already
    present would stay ahead."""
    source = _source(lanceur)
    assert 'sys.path.insert(0, _RACINE)' in source
    assert 'sys.path.remove(_RACINE)' in source


@pytest.mark.parametrize('lanceur', _LANCEURS)
def test_le_lanceur_controle_la_provenance(lanceur):
    source = _source(lanceur)
    assert 'bootstrap_check.check(_RACINE)' in source


@pytest.mark.parametrize('lanceur', _LANCEURS)
def test_le_lanceur_purge_les_memes_paquets_que_le_controle(lanceur):
    """Purging fewer packages than those being watched would leave a detected
    intruder that is never evicted."""
    source = _source(lanceur)
    for paquet in bootstrap_check.PACKAGES:
        assert "'%s'" % paquet in source, (lanceur, paquet)


@pytest.mark.parametrize('lanceur', _LANCEURS)
def test_le_lanceur_nappelle_pas_sys_exit(lanceur):
    """SystemExit surfaces as an error in the VE script window,
    even when everything went well.

    We check for the CALL, not the word: both launchers explain in a
    comment why they refrain from it.
    """
    for numero, ligne in enumerate(_source(lanceur).splitlines(), 1):
        code = ligne.split('#')[0]
        assert 'sys.exit(' not in code, (lanceur, numero)
