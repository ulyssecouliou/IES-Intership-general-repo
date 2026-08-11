# -*- coding: utf-8 -*-
"""Checks that the onboarding manual still describes this repository.

A manual is a claim about the code, exactly like a traceability matrix, and it
rots the same way: someone renames a module, and the one document a newcomer
reads first sends them to a file that is not there. Ten minutes of doubting the
documentation is worse than no documentation, because they then doubt all of
it.

So the checkable parts are checked. Every path the manual names must exist,
every module it tells you to run must import, and the statements it makes about
the current standing -- eight classes not evaluated, twenty bindings unresolved
-- are re-derived here rather than trusted.

WHAT IS NOT CHECKED, and cannot be: the judgement. Whether the reasons given
are the right reasons is for a reader to weigh.
"""

import io
import os
import re

import pytest

_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir,
                 os.pardir))
MANUAL = os.path.join(_ROOT, 'docs', 'MANUEL-DE-REPRISE.md')

#: Paths named in prose that are directories, or that the manual deliberately
#: cites as absent. Listing them here is cheaper than teaching the regex to
#: understand context.
NOT_FILES = {'refs/reference-data/*.json', 'traceability/test-N.matrix.md',
             'docs/FICHE-APACHEHVAC-TEST{4,5,6}.md'}


@pytest.fixture(scope='module')
def manual():
    if not os.path.exists(MANUAL):
        pytest.skip('manual absent')
    with io.open(MANUAL, encoding='utf-8') as stream:
        return stream.read()


def _cited_paths(text):
    """Every repository path the manual names inside backticks."""
    found = set()
    for match in re.finditer(r'`([A-Za-z0-9_./\-]+\.(?:py|md|json|epw))`',
                             text):
        path = match.group(1)
        if path not in NOT_FILES and '/' in path or path.startswith('Run_VE'):
            found.add(path)
    return sorted(found)


# --------------------------------------------------------------------------
# Every path it names must be there
# --------------------------------------------------------------------------

def test_every_file_the_manual_names_exists(manual):
    """The failure this prevents: a newcomer's first command hits a path that
    was renamed, and they stop trusting the whole document."""
    missing = [path for path in _cited_paths(manual)
               if not os.path.exists(os.path.join(_ROOT, path))
               and path not in NOT_FILES]
    # The manual cites DRYCOLD_IESVE.epw to warn against it; it need not be
    # present for the warning to be worth making.
    missing = [path for path in missing if not path.endswith('.epw')]
    assert missing == [], missing


def test_the_launchers_it_lists_are_real(manual):
    for name in re.findall(r'`(Run_VE_SIA4010_[A-Za-z0-9_]+\.py)`', manual):
        assert os.path.exists(os.path.join(_ROOT, name)), name


@pytest.mark.parametrize('module', [
    'scripts.build_traceability_matrix',
    'scripts.match_aps_variables',
    'scripts.build_reseau_ventilation_reference',
    'scripts.bootstrap_check',
    'ui.i18n',
    'ui.theme',
    'ui.class_selection',
])
def test_every_module_it_tells_you_to_run_imports(module):
    __import__(module)


def test_the_i18n_key_it_quotes_exists(manual):
    """It promises the interface carries the standing reminder. If the key
    were renamed, the promise would be empty."""
    from ui import i18n
    assert 'note.pass_is_not_compliance' in manual
    assert i18n.translate('note.pass_is_not_compliance', i18n.FRENCH)


# --------------------------------------------------------------------------
# The standing it reports, re-derived rather than trusted
# --------------------------------------------------------------------------

def test_the_eight_classes_are_still_unevaluated(manual):
    """The manual's headline claim. If a class ever becomes evaluated this
    test fails, and the manual must be rewritten -- which is the point."""
    from engine import test1_engine as engine
    from ui import class_selection as selection
    from ui import verdict_view as views
    try:
        views_built = [views.construire_vue_test1(
            engine.evaluer_test1(engine.charger_reference()))]
    except Exception:  # noqa: BLE001 -- a missing reference is a skip
        pytest.skip('Test 1 reference not available')
    statuses = set(selection.diagnose(name, views_built)['statut']
                   for name in selection.CLASSES)
    assert statuses == {selection.STATUS_NOT_EVALUATED}
    assert u'Les huit classes sont `NON_EVALUEE`' in manual


def test_the_binding_count_it_quotes_is_right(manual):
    from ve_adapter import bandes_adapter as adapter
    declared = sum(len(v) for v in adapter.LIAISONS.values())
    resolved = sum(1 for test in adapter.LIAISONS.values()
                   for binding in test.values()
                   if binding.get('aps_varname'))
    assert declared == 20, declared
    assert resolved == 0, resolved
    assert u'20 noms de variables APS' in manual
    assert u'0/20' in manual or u'0 sur 20' in manual


def test_the_wall_resistance_it_quotes_is_the_measured_one(manual):
    """1.7893 against 1.789 is the repository's one established VE-to-standard
    agreement. A manual that rounded it would be quoting itself."""
    assert u'1,7893' in manual
    assert u'1,789' in manual


# --------------------------------------------------------------------------
# The distinctions it exists to protect
# --------------------------------------------------------------------------

def test_it_separates_the_two_workstreams(manual):
    """Confusing SIA 4010 with SIA 380/2 is the costliest mistake available
    here, so the manual leads with it."""
    tete = manual[:4000]
    assert 'SIA 4010' in tete and 'SIA 380/2' in tete
    assert u'logiciel' in tete and u'bâtiment client' in tete


def test_it_states_that_a_pass_is_not_a_validation(manual):
    assert u'PASS technique' in manual
    assert u'signature indépendante' in manual


def test_it_refuses_to_call_drycold_a_swiss_climate(manual):
    """A standing instruction from the owner, and an easy thing to lose."""
    assert 'DRYCOLD' in manual
    assert u'pas** un climat suisse approuvé' in manual


def test_it_says_what_the_repository_does_not_prove(manual):
    """The section that makes the rest usable."""
    assert u'ne prouve pas' in manual
    assert u'aucune classe n\'est validée' in manual


def test_it_names_who_can_lift_each_blocker(manual):
    """"Blocked" without an owner is a status; with one it is a request."""
    for owner in (u'la SIA', u'Johan', u'une personne dans VE'):
        assert owner in manual, owner


# --------------------------------------------------------------------------
# Freshness
# --------------------------------------------------------------------------

def test_it_carries_a_date(manual):
    assert re.search(r'20\d\d-\d\d-\d\d', manual)


def test_it_does_not_reference_modules_that_were_renamed(manual):
    """These four were renamed during the English conversion. A manual is the
    likeliest place for an old name to survive."""
    for gone in ('design_ies', 'theme_ies', 'selection_classe',
                 'export_excel_com', 'scripts/amorcage'):
        assert gone not in manual, gone
