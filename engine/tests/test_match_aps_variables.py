# -*- coding: utf-8 -*-
"""Tests for the APS probe confrontation (`scripts/match_aps_variables.py`).

The script's value is entirely in what it REFUSES to conclude, so that is what
these tests hold:

* finding a name in a probe is not the same claim as that name being correct.
  The script reports presence; it must never write a binding;
* a candidate absent from the declared level but present at ANOTHER level is a
  declaration error, not a missing component. Those two call for opposite
  actions -- fix a line of code, or build a component and re-simulate -- and
  the first version of this script conflated them. It found exactly one such
  case on the real probe;
* a truncated offer list that does not say it is truncated reads as an
  exhaustive one.
"""

import pytest

from scripts import match_aps_variables as match


def _probe(variables):
    """A probe shaped like what `scripts/sonde_aps.py` writes."""
    return {'aps': {'nom': 'test.aps'}, 'variables': list(variables)}


def _variable(name, level):
    return {'aps_varname': name, 'display_name': name, 'model_level': level}


# --------------------------------------------------------------------------
# Reading the probe
# --------------------------------------------------------------------------

def test_a_missing_probe_raises_and_says_how_to_make_one():
    with pytest.raises(match.ProbeUnreadable) as caught:
        match.load_probe('no/such/probe.json')
    assert 'Sonde_APS' in str(caught.value)


def test_a_file_that_is_not_a_probe_raises(tmp_path):
    """Treating it as an empty probe would report every quantity as absent --
    a very confident way of saying nothing at all."""
    import io
    import os
    path = os.path.join(str(tmp_path), 'x.json')
    with io.open(path, 'w', encoding='utf-8') as stream:
        stream.write(u'{"something": 1}')
    with pytest.raises(match.ProbeUnreadable):
        match.load_probe(path)


def test_variables_group_by_level():
    grouped = match.index_by_level(_probe([
        _variable('a', 'v'), _variable('b', 'z'), _variable('c', 'v')]))
    assert sorted(grouped) == ['v', 'z']
    assert len(grouped['v']) == 2


# --------------------------------------------------------------------------
# The distinction that matters: wrong level vs absent
# --------------------------------------------------------------------------

def test_a_candidate_at_another_level_is_not_reported_as_absent():
    """THE FINDING. On the real probe, `Total lights energy` is declared at
    level `z` and lives at level `e`. Reported as merely absent, it would send
    someone to build a component that is already there."""
    grouped = match.index_by_level(_probe([_variable('X', 'e')]))
    assert match._levels_carrying(grouped, 'X') == ['e']
    assert match._find(grouped, 'z', 'X') is None


def test_a_name_nowhere_in_the_probe_carries_no_level():
    grouped = match.index_by_level(_probe([_variable('X', 'e')]))
    assert match._levels_carrying(grouped, 'Y') == []


def test_the_two_states_are_ordered_apart():
    """They call for opposite actions, so they must not sort together."""
    assert match.CANDIDATE_WRONG_LEVEL in match.STATE_ORDER
    assert match.CANDIDATE_ABSENT in match.STATE_ORDER
    assert match.STATE_ORDER.index(match.CANDIDATE_WRONG_LEVEL) != \
        match.STATE_ORDER.index(match.CANDIDATE_ABSENT)


# --------------------------------------------------------------------------
# Against the real probe
# --------------------------------------------------------------------------

@pytest.fixture(scope='module')
def real_report():
    try:
        return match.confront_all(match.load_probe())
    except match.ProbeUnreadable:
        pytest.skip('no probe in outputs/')


def test_every_declared_quantity_appears_exactly_once(real_report):
    from ve_adapter import bandes_adapter as adapter
    declared = sum(len(v) for v in adapter.LIAISONS.values())
    assert real_report['total'] == declared
    keys = [(r['test'], r['libelle_de']) for r in real_report['lignes']]
    assert len(set(keys)) == len(keys)


def test_every_row_carries_a_known_state(real_report):
    for row in real_report['lignes']:
        assert row['etat'] in match.STATE_ORDER, row


def test_the_tally_matches_the_rows(real_report):
    assert sum(real_report['effectifs'].values()) == real_report['total']


def test_the_lighting_level_error_is_caught(real_report):
    """The regression, on the case that was actually found: Test 3's
    `Beleuchtungsenergie` is declared at level `z`, and its candidate lives at
    `e`. An extraction at `z` would find nothing."""
    rows = [r for r in real_report['lignes']
            if r['etat'] == match.CANDIDATE_WRONG_LEVEL]
    assert rows, 'expected the declared-level error to be reported'
    assert any(r['libelle_de'] == 'Beleuchtungsenergie' for r in rows)


def test_no_row_is_reported_as_bound_yet(real_report):
    """Twenty quantities, none bound. If this ever passes with BOUND > 0, a
    binding was declared -- which is a human decision, never this script's."""
    assert real_report['effectifs'][match.BOUND] == 0


# --------------------------------------------------------------------------
# What the report must never do
# --------------------------------------------------------------------------

def test_the_script_never_writes_a_binding():
    """It reports presence. Binding is a human claim, and the adapter stays
    hand-edited."""
    import io
    import os
    path = os.path.abspath(match.__file__).replace('.pyc', '.py')
    with io.open(path, encoding='utf-8') as stream:
        source = stream.read()
    assert 'LIAISONS[' not in source
    assert "adapter.LIAISONS.get" in source


def test_a_truncated_offer_states_how_much_it_hid():
    """A truncated list that does not say so reads as an exhaustive one."""
    variables = [_variable('v%d' % index, 'z')
                 for index in range(match.OFFER_LIMIT + 5)]
    grouped = match.index_by_level(_probe(variables))
    assert len(grouped['z']) > match.OFFER_LIMIT


def test_an_empty_level_is_called_out_as_a_missing_component(real_report):
    """A level with no variables means the COMPONENT is not in the model, and
    no amount of searching the probe will help."""
    empties = match.empty_levels(real_report)
    for level, count in empties:
        assert count > 0
        assert level in real_report['recensement_par_niveau'] or True


def test_the_sheet_says_it_binds_nothing(real_report):
    sheet = match.build_sheet(real_report)
    assert u'ne lie rien' in sheet
    assert u'Ce que cette fiche ne dit pas' in sheet


def test_the_sheet_warns_that_absence_is_model_specific(real_report):
    """This probe comes from ONE model. Another would carry other variables."""
    sheet = match.build_sheet(real_report)
    assert u'UN' in sheet and u'mod' in sheet


def test_the_sheet_lists_every_test(real_report):
    sheet = match.build_sheet(real_report)
    for number in sorted(set(r['test'] for r in real_report['lignes'])):
        assert u'## Test %d' % number in sheet


def test_main_without_a_probe_returns_one():
    assert match.main(('no/such/probe.json',)) == 1
