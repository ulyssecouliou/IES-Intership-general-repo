# -*- coding: utf-8 -*-
"""Tests for validation-class selection (`ui/class_selection.py`).

The rule the whole module exists to hold: **a class is never reached on
anything but a simulation result.** Every shortcut around it looks reasonable
in isolation -- an unknown class returning an empty tuple, a grey test
counting as "not a failure", a class with no views defaulting to fine -- and
every one of them turns a missing proof into a success.

The second thing guarded here is the diagnosis: it must name the CAUSE and the
ACTION, not just the symptom. A blocker that says "test 5 produced no result"
and stops there sends the reader looking for the reason we already know.
"""

import io
import os

import pytest

from ui import class_selection as sel
from ui import i18n


@pytest.fixture(autouse=True)
def restore_language():
    before = i18n.language()
    yield
    i18n.set_language(before)


def _view(test_id, colour, criterion=None):
    """A minimal view, shaped like what `verdict_view` assembles."""
    built = {'test_id': test_id, 'verdict_global': {'couleur': colour}}
    if criterion is not None:
        built['critere'] = {'statut': criterion}
    return built


# --------------------------------------------------------------------------
# Table 63
# --------------------------------------------------------------------------

def test_the_eight_classes_are_covered():
    assert len(sel.CLASSES) == 8
    for name in sel.CLASSES:
        assert sel.tests_for_class(name)


def test_class_5_requires_only_test_7():
    assert sel.tests_for_class('5') == ('7',)


def test_class_4b_requires_all_seven_tests():
    numbers = set(sel._required_test_number(t)
                  for t in sel.tests_for_class('4B'))
    assert numbers == set(range(1, 8))


def test_an_unknown_class_raises_instead_of_returning_empty():
    """An empty tuple would read as "this class requires nothing", the
    opposite of the truth."""
    with pytest.raises(sel.UnknownClass) as caught:
        sel.tests_for_class('9Z')
    assert 'table 63' in str(caught.value)
    assert '1A' in str(caught.value)


def test_every_class_has_a_readable_description():
    for name in sel.CLASSES:
        text = sel.description(name)
        assert text != name
        assert len(text) > 10


def test_descriptions_follow_the_language_in_force():
    i18n.set_language(i18n.ENGLISH)
    assert sel.description('1A') == i18n.translate('class.1A', i18n.ENGLISH)
    i18n.set_language(i18n.FRENCH)
    assert sel.description('1A') == i18n.translate('class.1A', i18n.FRENCH)


def test_an_unknown_class_description_returns_the_identifier():
    """Honest: it says "no description". Inventing one would put unverified
    wording in front of a client."""
    assert sel.description('9Z') == '9Z'


def test_there_is_one_description_key_per_class():
    assert sorted(sel.DESCRIPTION_KEY) == sorted(sel.CLASSES)


# --------------------------------------------------------------------------
# Test numbers
# --------------------------------------------------------------------------

@pytest.mark.parametrize('identifier,expected', [
    ('1', 1), ('2A', 2), ('3A-F', 3), ('7', 7),
])
def test_a_table_63_number_is_taken_from_the_prefix(identifier, expected):
    """Table 63 names some tests by a subset of cases. The prefix is
    extracted, never guessed."""
    assert sel._required_test_number(identifier) == expected


def test_a_table_63_identifier_without_digits_yields_no_number():
    assert sel._required_test_number('') is None
    assert sel._required_test_number('abc') is None


@pytest.mark.parametrize('test_id,expected', [
    ('SIA-4010-Test-1', 1),
    ('Test 7', 7),
    ('Test 2A', 2),
    ('SIA-4010-Test-6', 6),
])
def test_a_view_number_is_read_after_the_word_test(test_id, expected):
    """THE DEFECT. A view identifier is a DIFFERENT vocabulary from table 63:
    the number follows the word "Test", it is not the leading digit group.
    Reading the prefix of 'SIA-4010-Test-1' gives nothing -- so selection
    retained NOTHING, for every class, and reported every required test as
    absent. The screen said "0/2 tests present" with the results sitting
    right there, and the exports follow the selection."""
    assert sel._view_test_number(test_id) == expected


def test_the_last_number_wins_over_the_standard_number():
    """'SIA-4010-Test-1' must give 1, not 4010."""
    assert sel._view_test_number('SIA-4010-Test-1') == 1


def test_real_view_identifiers_are_actually_selected():
    """The regression, stated on the shapes the engines really emit. The old
    tests used synthetic identifiers that happened to start with a digit,
    which is exactly why they missed this."""
    chosen = sel.select('4B', [_view('SIA-4010-Test-1', 'gris'),
                               _view('Test 7', 'gris')])
    assert chosen['numeros_presents'] == [1, 7]


def test_an_unreadable_identifier_is_listed_not_dropped():
    """Silently excluding it is how the previous version hid the defect."""
    chosen = sel.select('1A', [_view('no number here', 'gris')])
    assert chosen['test_id_non_identifies'] == ['no number here']


# --------------------------------------------------------------------------
# Selection
# --------------------------------------------------------------------------

def test_selection_keeps_only_the_required_tests():
    chosen = sel.select('5', [_view('SIA-4010-Test-1', 'vert'),
                              _view('Test 7', 'vert')])
    assert [v['test_id'] for v in chosen['vues']] == ['Test 7']


def test_required_but_absent_tests_are_named():
    """Naming them is what turns "incomplete" into an action."""
    chosen = sel.select('4B', [_view('Test 7', 'vert')])
    assert chosen['numeros_absents'] == [1, 2, 3, 4, 5, 6]


def test_the_selection_carries_the_class_description():
    chosen = sel.select('1A', [])
    assert chosen['intitule'] == sel.description('1A')


# --------------------------------------------------------------------------
# Status -- where a missing proof must not become a success
# --------------------------------------------------------------------------

def test_a_class_with_no_view_is_not_compliant():
    assert sel.class_status(sel.select('1A', [])) == \
        sel.STATUS_NOT_EVALUATED


def test_a_missing_test_prevents_compliance():
    chosen = sel.select('4B', [_view('Test 7', 'vert')])
    assert sel.class_status(chosen) == sel.STATUS_NOT_EVALUATED


def test_a_grey_test_prevents_compliance():
    """THE RULE. A test that was not evaluated is not compliance."""
    chosen = sel.select('5', [_view('Test 7', 'gris')])
    assert sel.class_status(chosen) == sel.STATUS_NOT_EVALUATED


def test_one_red_test_makes_the_class_non_compliant():
    chosen = sel.select('5', [_view('Test 7', 'rouge')])
    assert sel.class_status(chosen) == sel.STATUS_FAIL


def test_red_outranks_grey():
    """A class that is both incomplete and wrong is reported wrong: the
    failure is the actionable half."""
    chosen = sel.select('1B', [_view('SIA-4010-Test-1', 'rouge'),
                               _view('Test 2', 'gris')])
    assert sel.class_status(chosen) == sel.STATUS_FAIL


def test_all_green_gives_compliance():
    chosen = sel.select('5', [_view('Test 7', 'vert')])
    assert sel.class_status(chosen) == sel.STATUS_PASS


# --------------------------------------------------------------------------
# Diagnosis -- cause and action, not just symptom
# --------------------------------------------------------------------------

def test_every_test_without_a_result_is_named():
    found = sel.diagnose('4B', [_view('Test 7', 'gris')])
    numbers = [b['test'] for b in found['blocages']
               if b['motif'] == sel.REASON_NO_SIMULATION]
    assert numbers == [1, 2, 3, 4, 5, 6]


def test_unresolved_bindings_are_reported():
    found = sel.diagnose('5', [_view('Test 7', 'gris')],
                         binding_state={7: (0, 11)})
    reported = [b for b in found['blocages']
                if b['motif'] == sel.REASON_UNRESOLVED_BINDINGS]
    assert len(reported) == 1
    assert '0 binding(s) of 11' in reported[0]['constat']


def test_a_complete_binding_does_not_block():
    found = sel.diagnose('5', [_view('Test 7', 'vert')],
                         binding_state={7: (11, 11)})
    assert not [b for b in found['blocages']
                if b['motif'] == sel.REASON_UNRESOLVED_BINDINGS]


def test_a_criterion_not_stated_in_the_spec_is_reported():
    found = sel.diagnose('5', [_view('Test 7', 'vert', criterion='INFERE')])
    reported = [b for b in found['blocages']
                if b['motif'] == sel.REASON_CRITERION_NOT_ESTABLISHED]
    assert len(reported) == 1
    assert 'subcommittee' in reported[0]['action']


def test_a_criterion_stated_in_the_spec_does_not_block():
    found = sel.diagnose(
        '5', [_view('Test 7', 'vert', criterion=sel.CRITERION_STATED_IN_SPEC)])
    assert not [b for b in found['blocages']
                if b['motif'] == sel.REASON_CRITERION_NOT_ESTABLISHED]


def test_missing_inputs_are_reported():
    found = sel.diagnose('5', [_view('Test 7', 'vert')],
                         missing_inputs={'Kloten irradiance': 'not published'})
    reported = [b for b in found['blocages']
                if b['motif'] == sel.REASON_INPUT_MISSING]
    assert len(reported) == 1
    assert 'Kloten' in reported[0]['constat']


def test_every_blocker_carries_a_cause_and_an_action():
    """A blocker that names only the symptom sends the reader looking for a
    reason we already know."""
    found = sel.diagnose('4B', [], binding_state={1: (0, 3)},
                         missing_inputs={'x': 'y'})
    assert found['blocages']
    for blocker in found['blocages']:
        assert blocker['cause'].strip()
        assert blocker['action'].strip()


def test_blockers_are_ordered_most_blocking_first():
    """The internal report leads with what prevents everything else."""
    found = sel.diagnose('4B', [_view('Test 7', 'gris')],
                         binding_state={7: (0, 11)},
                         missing_inputs={'x': 'y'})
    reasons = [sel.REASON_ORDER.index(b['motif']) for b in found['blocages']]
    assert reasons == sorted(reasons)


def test_a_class_with_no_blocker_is_declared_reachable():
    found = sel.diagnose('5', [_view('Test 7', 'vert')])
    assert found['blocages'] == []
    assert found['atteignable_en_letat'] is True


def test_the_summary_states_the_number_of_blockers():
    found = sel.diagnose('4B', [])
    text = sel.summarise_diagnosis(found)
    assert '%d blocker(s)' % found['nb_blocages'] in text


def test_the_summary_of_a_clean_class_does_not_invent_blockers():
    found = sel.diagnose('5', [_view('Test 7', 'vert')])
    text = sel.summarise_diagnosis(found)
    assert 'No blocker recorded.' in text
    assert 'not reachable' not in text


def test_the_summary_names_the_class_and_its_status():
    found = sel.diagnose('5', [_view('Test 7', 'gris')])
    text = sel.summarise_diagnosis(found)
    assert 'Class 5' in text
    assert found['statut'] in text


# --------------------------------------------------------------------------
# Purity
# --------------------------------------------------------------------------

def test_the_module_stays_pure():
    """Rule 4: no `iesve`, and no `tkinter` either -- this must be testable
    with no display and no licence."""
    path = os.path.abspath(sel.__file__).replace('.pyc', '.py')
    with io.open(path, encoding='utf-8') as stream:
        for number, line in enumerate(stream, 1):
            stripped = line.strip()
            assert not stripped.startswith(
                ('import iesve', 'from iesve', 'import tkinter',
                 'from tkinter')), number
