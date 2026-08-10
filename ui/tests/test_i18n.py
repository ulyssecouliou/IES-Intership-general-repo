# -*- coding: utf-8 -*-
"""Tests for the user-facing string table (`ui/i18n.py`).

A verdict label is evidence, not decoration. "NON EVALUE" is what a reader
will quote back at us, and three documents produced from the same run -- the
dialog, the Excel export, the PDF -- must not word it three ways.

So what these tests guard is mostly refusal:

* a missing key RAISES. It does not fall back to the key, to the other
  language, or to an empty string. A dialog showing `verdict.pass` is ugly for
  ten seconds; a dialog showing nothing where a verdict belongs is a false
  report, and this repository has already lost a week to eighteen green steps
  hiding a wrong answer;
* an unknown verdict RAISES rather than rendering as the nearest known one.
  Silently showing "NON EVALUE" for a state we have not thought about hides
  exactly the thing worth seeing.
"""

import pytest

from ui import i18n


@pytest.fixture(autouse=True)
def restore_language():
    """The language is module state; a test that switched it must not leak."""
    before = i18n.language()
    yield
    i18n.set_language(before)


# --------------------------------------------------------------------------
# Completeness
# --------------------------------------------------------------------------

def test_every_key_exists_in_both_languages():
    """A label added in one language only shows up blank -- or raises -- for
    half the users."""
    report = i18n.check_completeness()
    assert report['missing'] == [], report['missing']
    assert report['checked'] > 0


def test_french_is_the_default():
    """The tool serves Swiss practice. English exists, it does not lead."""
    assert i18n.DEFAULT_LANGUAGE == i18n.FRENCH
    assert i18n.LANGUAGES[0] == i18n.FRENCH


def test_no_string_is_identical_across_languages_by_accident():
    """A few legitimately match: a product name, and three words that are
    spelled the same in French and English. Anything else is a translation
    someone forgot to write, and it would ship looking finished."""
    allowed = {'app.product',     # proper noun
               'column.source',   # same word in both
               'column.test',     # same word in both
               'column.verdict'}  # same word in both
    for key in sorted(i18n.STRINGS):
        fr, en = i18n.STRINGS[key]
        if fr == en:
            assert key in allowed, key


# --------------------------------------------------------------------------
# Refusal, not fallback
# --------------------------------------------------------------------------

def test_an_unknown_key_raises():
    """THE RULE. A blank where a verdict belongs is a false report."""
    with pytest.raises(i18n.MissingTranslation):
        i18n.translate('no.such.key')


def test_an_unknown_key_names_the_fix():
    """An error message that does not say what to do costs a round trip."""
    try:
        i18n.translate('no.such.key')
    except i18n.MissingTranslation as error:
        assert 'STRINGS' in str(error)
        assert 'both languages' in str(error)


def test_an_unknown_language_raises_rather_than_falling_back():
    """Falling back would show a French dialog to someone who asked for
    English, and report success."""
    with pytest.raises(i18n.UnknownLanguage):
        i18n.set_language('de')
    with pytest.raises(i18n.UnknownLanguage):
        i18n.translate('verdict.pass', 'de')


def test_an_empty_string_is_treated_as_missing(monkeypatch):
    patched = dict(i18n.STRINGS)
    patched['test.empty'] = (u'', u'something')
    monkeypatch.setattr(i18n, 'STRINGS', patched)
    with pytest.raises(i18n.MissingTranslation):
        i18n.translate('test.empty', i18n.FRENCH)


def test_check_completeness_catches_an_empty_entry(monkeypatch):
    patched = dict(i18n.STRINGS)
    patched['test.empty'] = (u'présent', u'')
    monkeypatch.setattr(i18n, 'STRINGS', patched)
    manquants = i18n.check_completeness()['missing']
    assert ('test.empty', i18n.ENGLISH) in manquants


# --------------------------------------------------------------------------
# Switching
# --------------------------------------------------------------------------

def test_switching_changes_what_comes_back():
    i18n.set_language(i18n.FRENCH)
    assert i18n.translate('verdict.pass') == u'CONFORME'
    i18n.set_language(i18n.ENGLISH)
    assert i18n.translate('verdict.pass') == u'PASS'


def test_an_explicit_language_wins_over_the_one_in_force():
    i18n.set_language(i18n.FRENCH)
    assert i18n.translate('verdict.fail', i18n.ENGLISH) == u'FAIL'
    assert i18n.language() == i18n.FRENCH


def test_the_short_alias_is_the_same_function():
    assert i18n.t is i18n.translate


# --------------------------------------------------------------------------
# Verdicts
# --------------------------------------------------------------------------

@pytest.mark.parametrize('verdict,expected', [
    ('PASS', 'verdict.pass'),
    ('FAIL', 'verdict.fail'),
    ('WARNING', 'verdict.warning'),
    ('NOT_CHECKABLE', 'verdict.not_checkable'),
    ('NON_EVALUE', 'verdict.not_evaluated'),
    ('NON_ETABLI', 'verdict.not_checkable'),
])
def test_engine_verdicts_map_to_a_key(verdict, expected):
    assert i18n.verdict_key(verdict) == expected


def test_an_unknown_verdict_raises_rather_than_rendering_as_another():
    """Showing "NON EVALUE" for a state nobody has thought about hides
    exactly the thing worth seeing."""
    with pytest.raises(i18n.MissingTranslation):
        i18n.verdict_key('SOMETHING_NEW')


def test_every_verdict_key_resolves_in_both_languages():
    for verdict in ('PASS', 'FAIL', 'WARNING', 'NOT_CHECKABLE',
                    'NON_EVALUE', 'NON_ETABLI', 'NON_SIGNE'):
        key = i18n.verdict_key(verdict)
        for code in i18n.LANGUAGES:
            assert i18n.translate(key, code)


def test_pass_and_fail_never_render_the_same():
    for code in i18n.LANGUAGES:
        assert i18n.translate('verdict.pass', code) != \
            i18n.translate('verdict.fail', code)


def test_not_checkable_is_worded_apart_from_fail():
    """Nothing was compared, so nothing failed. The wording has to say so."""
    for code in i18n.LANGUAGES:
        assert i18n.translate('verdict.not_checkable', code) != \
            i18n.translate('verdict.fail', code)


def test_the_pass_help_refuses_to_claim_sia_validation():
    """A technical PASS is neither SIA 380/2 compliance nor SIA 4010
    validation. The help text is where that gets confused."""
    for code in i18n.LANGUAGES:
        aide = i18n.translate('verdict.pass.help', code)
        assert ('4010' in aide)
        assert ('signature' in aide.lower())


def test_the_standing_reminders_exist_in_both_languages():
    """They exist because these three states get confused in reports."""
    for key in ('note.pass_is_not_compliance', 'note.absence_is_not_zero'):
        for code in i18n.LANGUAGES:
            assert i18n.translate(key, code)


# --------------------------------------------------------------------------
# What must never enter the table
# --------------------------------------------------------------------------

def test_no_german_lookup_key_is_translated():
    """German labels that key against the official SIA workbooks must stay
    verbatim -- translating one breaks the match. They never enter here."""
    suspects = ('Zulufttemperatur', 'Wärmerückgewinnung', 'Auslegungsleistung',
                'Zugeführte', 'Nennvolumenstrom')
    for key in sorted(i18n.STRINGS):
        for fr, en in [i18n.STRINGS[key]]:
            for suspect in suspects:
                assert suspect not in fr, (key, suspect)
                assert suspect not in en, (key, suspect)
