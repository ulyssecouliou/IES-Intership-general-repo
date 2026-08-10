# -*- coding: utf-8 -*-
"""Validation-class selection, and a diagnosis of what is blocking it.

TWO READINGS OF ONE STATE, FOR TWO AUDIENCES.

The **client** picks the class they are aiming at and wants to know where they
stand: which tests it requires, which are cleared. Their report must contain
only what concerns that class -- a class 1A has no use for the quantities of
Test 5.

The **team** wants the precise list of what is missing, with the cause and the
action. `diagnose` produces it. It is deliberately harder than the client
report: it names unresolved bindings, criteria that are not established, and
inputs absent from the repository.

WHAT THIS MODULE WILL NEVER DO. Declare a class reached on anything other than
a simulation result. A class with no candidate is `NOT_EVALUATED`, never
`PASS` -- and that distinction is carried by a separate status, not by cautious
wording.

LANGUAGE. The diagnosis strings are English and stay English: `diagnose` feeds
the INTERNAL report, read by the team. The class descriptions do go through
`ui/i18n.py`, because they appear in the client's selector. Note what they are:
a RENDERING of the "applications" column of SIA 4010:2023 table 63, which is
published in German. They are not quotations, in either language, and they are
not lookup keys -- nothing matches on them.

Pure Python: no `tkinter`, no `iesve`. Testable with no display and no licence.
"""

from __future__ import print_function

import re

from ui import i18n
from ui import verdict_view as views

#: Validation classes, in the order of SIA 4010:2023, table 63 (p. 48).
CLASSES = ('1A', '1B', '2A', '2B', '3', '4A', '4B', '5')

#: i18n key holding each class description. Built rather than written out, so a
#: class added to `CLASSES` fails loudly in `i18n.translate` instead of showing
#: its bare identifier in the selector.
DESCRIPTION_KEY = dict(('%s' % name, 'class.%s' % name) for name in CLASSES)

STATUS_PASS = 'CONFORME'
STATUS_FAIL = 'NON_CONFORME'
STATUS_NOT_EVALUATED = 'NON_EVALUEE'

#: Blocking reasons, most blocking first. The order matters: the internal
#: report leads with what prevents everything else.
REASON_NO_SIMULATION = 'AUCUNE_SIMULATION'
REASON_UNRESOLVED_BINDINGS = 'LIAISONS_NON_RESOLUES'
REASON_CRITERION_NOT_ESTABLISHED = 'CRITERE_NON_ETABLI'
REASON_INPUT_MISSING = 'ENTREE_ABSENTE_DU_DEPOT'

REASON_ORDER = (REASON_NO_SIMULATION, REASON_UNRESOLVED_BINDINGS,
                REASON_CRITERION_NOT_ESTABLISHED, REASON_INPUT_MISSING)

#: The only criterion status that needs no confirmation from the SIA
#: subcommittee: the specification states the rule itself.
CRITERION_STATED_IN_SPEC = 'ENONCE_DANS_LA_SPEC'

#: Sort key for a blocker that names no test. High enough to land last inside
#: its reason group, without pretending to be a test number.
NO_TEST_SORT_KEY = 99


class UnknownClass(ValueError):
    """Raised when a requested class is not in table 63."""


def tests_for_class(name):
    """Tests a validation class requires.

    Args:
        name: Class identifier, `'1A'` through `'5'`.

    Returns:
        tuple[str]: Test identifiers, as table 63 names them.

    Raises:
        UnknownClass: If the class does not exist. Returning an empty tuple
            would read as "this class requires nothing", the opposite of the
            truth.
    """
    if name not in views.TESTS_PAR_CLASSE:
        raise UnknownClass(
            'class %r is not in table 63 of SIA 4010:2023. Classes: %s.'
            % (name, ', '.join(CLASSES)))
    return views.TESTS_PAR_CLASSE[name]


def description(name):
    """Readable description of a class, in the language in force.

    Args:
        name: Class identifier.

    Returns:
        str: Description, or the identifier itself for a class this module
        does not know. Returning the identifier is honest here -- it says
        "no description", where inventing one would put unverified wording in
        front of a client.
    """
    key = DESCRIPTION_KEY.get(name)
    if key is None:
        return name
    return i18n.translate(key)


#: A view's test identifier, as the engines emit it: `SIA-4010-Test-1`,
#: `Test 7`. The number follows the word "Test" -- it is NOT the leading digit
#: group, and "SIA-4010" contains digits that mean nothing here.
_VIEW_TEST_ID = re.compile(r'[Tt]est[^0-9]*([0-9]+)')


def _required_test_number(identifier):
    """SIA test number carried by a TABLE 63 identifier.

    Table 63 names some tests by a subset of cases -- "2A", "3A-F" -- where
    the engine reasons by number. The numeric prefix is therefore extracted,
    never guessed.

    Args:
        identifier: For example `'1'`, `'2A'`, `'3A-F'`.

    Returns:
        int | None: The number, or `None` if the identifier carries none.
    """
    digits = u''
    for character in u'%s' % identifier:
        if character.isdigit():
            digits += character
        else:
            break
    return int(digits) if digits else None


def _view_test_number(test_id):
    """SIA test number carried by a VIEW's identifier.

    THIS IS A DIFFERENT VOCABULARY FROM TABLE 63, and conflating the two was a
    real defect. Table 63 says `1`, `2A`; the views say `SIA-4010-Test-1` and
    `Test 7`. Reading the leading digits of a view identifier yields nothing --
    so `select` retained NOTHING, for every class, and reported every required
    test as absent. The dialog showed "0/2 tests present" with the results
    sitting right there, and the exports, which follow the selection, would
    have carried nothing. The old tests missed it because their synthetic
    identifiers happened to start with a digit.

    The last match wins: `SIA-4010-Test-1` must give 1, not 4010.

    Args:
        test_id: For example `'SIA-4010-Test-1'`, `'Test 7'`.

    Returns:
        int | None: The number, or `None` if none can be read. `None` is not
        swallowed -- see `select`, which lists such views rather than dropping
        them.
    """
    matches = _VIEW_TEST_ID.findall(u'%s' % test_id)
    return int(matches[-1]) if matches else None


def select(name, view_list=()):
    """Restrict a set of views to the tests a class requires.

    Args:
        name: Class identifier.
        view_list: Views assembled by `verdict_view`.

    Returns:
        dict: The selection, with the tests present and the ones missing.

    Raises:
        UnknownClass: If the class does not exist.
    """
    required = tests_for_class(name)
    required_numbers = set(
        number for number in
        (_required_test_number(test) for test in required)
        if number is not None)

    kept, present, unidentified = [], set(), []
    for view in view_list:
        number = _view_test_number(view.get('test_id') or '')
        if number is None:
            # NOT dropped. A view whose identifier carries no test number is
            # a defect somewhere upstream, and silently excluding it is how
            # the previous version hid exactly that.
            unidentified.append(view.get('test_id'))
            continue
        if number in required_numbers:
            kept.append(view)
            present.add(number)

    return {
        'classe': name,
        'intitule': description(name),
        'tests_exiges': list(required),
        'vues': kept,
        'numeros_presents': sorted(present),
        'numeros_absents': sorted(required_numbers - present),
        'test_id_non_identifies': unidentified,
    }


def class_status(selection):
    """Status of a class, from a selection.

    Args:
        selection: What `select` returns.

    Returns:
        str: `STATUS_PASS`, `STATUS_FAIL` or `STATUS_NOT_EVALUATED`.
    """
    if selection['numeros_absents'] or not selection['vues']:
        return STATUS_NOT_EVALUATED

    colours = set(view['verdict_global']['couleur']
                  for view in selection['vues'])
    if 'rouge' in colours:
        return STATUS_FAIL
    if 'gris' in colours:
        # A test that was not evaluated is not compliance. This is the rule
        # that stops a missing proof from reading as a success.
        return STATUS_NOT_EVALUATED
    return STATUS_PASS


def diagnose(name, view_list=(), binding_state=None, missing_inputs=None):
    """List what prevents a class from being reached.

    This is the INTERNAL report: it names causes, not only symptoms, and gives
    the action that lifts each one.

    Args:
        name: Class identifier.
        view_list: Assembled views.
        binding_state: `{test number: (resolved, declared)}`.
        missing_inputs: `{name: cause}` for inputs absent from the repository.

    Returns:
        dict: Diagnosis, ordered most blocking first.
    """
    selection = select(name, view_list)
    bindings = dict(binding_state or {})
    absent = dict(missing_inputs or {})
    blockers = []

    for number in selection['numeros_absents']:
        blockers.append({
            'motif': REASON_NO_SIMULATION,
            'test': number,
            'constat': 'Test %d produced no result.' % number,
            'cause': 'The case has never been built or simulated in IESVE.',
            'action': 'Build the model, run ApacheSim over the full year, '
                      'read the .aps back.',
        })

    for number in sorted(bindings):
        if number not in selection['numeros_presents'] \
                and number not in selection['numeros_absents']:
            continue
        resolved, declared = bindings[number]
        if resolved >= declared:
            continue
        blockers.append({
            'motif': REASON_UNRESOLVED_BINDINGS,
            'test': number,
            'constat': 'Test %d: %d binding(s) of %d between a workbook '
                       'quantity and a VE variable.'
                       % (number, resolved, declared),
            'cause': 'Variable names are not API symbols: they are read off a '
                     'real .aps.',
            'action': 'Run Run_VE_SIA4010_Sonde_APS.py on a model that carries '
                      'these components, then declare the names read.',
        })

    for view in selection['vues']:
        criterion = (view.get('critere') or {}).get('statut')
        if criterion and criterion != CRITERION_STATED_IN_SPEC:
            blockers.append({
                'motif': REASON_CRITERION_NOT_ESTABLISHED,
                'test': _view_test_number(view.get('test_id') or ''),
                'constat': '%s: criterion %s.' % (view.get('test_id'),
                                                  criterion),
                'cause': 'The rule applied is not written in the '
                         'specification; it is recovered from the workbook, or '
                         'not defined at all.',
                'action': 'Have the SIA subcommittee confirm it '
                          '(SIA 4010:2023, 4.6.2).',
            })

    for input_name in sorted(absent):
        blockers.append({
            'motif': REASON_INPUT_MISSING,
            'test': None,
            'constat': 'Input absent from the repository: %s.' % input_name,
            'cause': absent[input_name],
            'action': 'Obtain the official data before any result is presented '
                      'as an SIA candidate.',
        })

    blockers.sort(key=lambda blocker: (
        REASON_ORDER.index(blocker['motif']),
        blocker['test'] if blocker['test'] is not None else NO_TEST_SORT_KEY))
    return {
        'classe': name,
        'intitule': selection['intitule'],
        'statut': class_status(selection),
        'tests_exiges': selection['tests_exiges'],
        'nb_blocages': len(blockers),
        'blocages': blockers,
        'atteignable_en_letat': not blockers,
    }


def summarise_diagnosis(diagnosis):
    """Render the diagnosis for a console or an internal report.

    Args:
        diagnosis: What `diagnose` returns.

    Returns:
        str: The text.
    """
    lines = [
        'Class %s -- %s' % (diagnosis['classe'], diagnosis['intitule']),
        'Tests required: %s' % ', '.join(diagnosis['tests_exiges']),
        'Status: %s' % diagnosis['statut'],
        '',
    ]
    if not diagnosis['blocages']:
        lines.append('No blocker recorded.')
        return '\n'.join(lines)

    current_reason = None
    for blocker in diagnosis['blocages']:
        if blocker['motif'] != current_reason:
            current_reason = blocker['motif']
            lines.append('[%s]' % current_reason)
        lines.append('  %s' % blocker['constat'])
        lines.append('      cause  : %s' % blocker['cause'])
        lines.append('      action : %s' % blocker['action'])
    lines.append('')
    lines.append('%d blocker(s). The class is not reachable as things stand.'
                 % diagnosis['nb_blocages'])
    return '\n'.join(lines)
