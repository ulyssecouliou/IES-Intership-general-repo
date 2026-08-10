# -*- coding: utf-8 -*-
"""User-facing strings for the SIA 4010 navigator, French by default.

WHY A TABLE AND NOT LITERALS IN THE WIDGETS. Two reasons, and the second is
the one that matters for this project.

The obvious one: the tool serves Swiss practice, so it speaks French, but the
rest of IES works in English. A literal in a widget makes that a rewrite.

The one that matters: **a verdict label is evidence.** "NON EVALUE" and
"CONFORME" are not decorations -- they are what a reader will quote back at
us. Keeping them in one table means they can be reviewed as a set, and it
means a label cannot quietly drift between the dialog, the Excel export and
the PDF, which is exactly how three documents come to disagree about the same
run.

A MISSING TRANSLATION IS LOUD. `translate` never falls back to the key, never
returns an empty string, and never silently picks the other language. It
raises. A dialog that shows `verdict.not_checkable` is ugly for ten seconds; a
dialog that shows nothing where a verdict belongs is a false report, and this
repository has already been bitten by eighteen green steps hiding a wrong
answer.

WHAT IS NOT TRANSLATED. German labels that serve as lookup keys against the
official SIA workbooks stay verbatim -- translating one breaks the match. They
never enter this table.
"""

from __future__ import print_function

FRENCH = 'fr'
ENGLISH = 'en'

#: Languages this module can render. French leads because the tool is used
#: against Swiss standards, in French-speaking practice.
LANGUAGES = (FRENCH, ENGLISH)

DEFAULT_LANGUAGE = FRENCH

#: Every user-facing string, keyed by a dotted path. Adding a key means adding
#: BOTH languages -- `check_completeness` fails the build otherwise, so a
#: half-added label cannot reach a user.
STRINGS = {
    # -- Window and shell ---------------------------------------------------
    'app.title': (u'Navigateur de validation SIA 4010',
                  u'SIA 4010 Validation Navigator'),
    'app.subtitle': (u'Vérification des classes de validation pour IESVE',
                     u'Validation class checking for IESVE'),
    'app.product': (u'IES Virtual Environment', u'IES Virtual Environment'),

    # -- Primary actions ---------------------------------------------------
    'action.run': (u'Lancer la vérification', u'Run check'),
    'action.close': (u'Fermer', u'Close'),
    'action.export_excel': (u'Exporter vers Excel', u'Export to Excel'),
    'action.export_pdf': (u'Exporter en PDF', u'Export to PDF'),
    'action.refresh': (u'Actualiser', u'Refresh'),
    'action.select_all': (u'Tout sélectionner', u'Select all'),
    'action.select_none': (u'Tout désélectionner', u'Clear selection'),
    'action.copy_details': (u'Copier le détail', u'Copy details'),

    # -- Verdicts. The most sensitive entries in this table. ----------------
    'verdict.pass': (u'CONFORME', u'PASS'),
    'verdict.fail': (u'NON CONFORME', u'FAIL'),
    'verdict.warning': (u'RÉSERVE', u'WARNING'),
    'verdict.not_checkable': (u'NON VÉRIFIABLE', u'NOT CHECKABLE'),
    'verdict.not_evaluated': (u'NON ÉVALUÉ', u'NOT EVALUATED'),
    'verdict.not_signed': (u'NON SIGNÉ', u'NOT SIGNED'),

    # -- What a verdict means. Shown next to it, never instead of it. -------
    'verdict.pass.help': (
        u'La valeur simulée tombe dans la bande de référence. Ce n\'est pas '
        u'une validation SIA 4010 : celle-ci demande une signature '
        u'indépendante.',
        u'The simulated value falls inside the reference band. This is not '
        u'SIA 4010 validation, which requires an independent signature.'),
    'verdict.fail.help': (
        u'La valeur simulée sort de la bande de référence.',
        u'The simulated value falls outside the reference band.'),
    'verdict.warning.help': (
        u'Un contrôle a abouti, mais sous une réserve qui doit être levée.',
        u'A check completed, but under a reservation that must be lifted.'),
    'verdict.not_checkable.help': (
        u'Une entrée indispensable manque. Ce n\'est pas un échec : rien '
        u'n\'a pu être comparé.',
        u'A required input is missing. This is not a failure: nothing could '
        u'be compared.'),
    'verdict.not_evaluated.help': (
        u'Aucune simulation n\'a produit de valeur candidate.',
        u'No simulation has produced a candidate value.'),

    # -- Column headings ---------------------------------------------------
    'column.test': (u'Test', u'Test'),
    'column.class': (u'Classe', u'Class'),
    'column.quantity': (u'Grandeur', u'Quantity'),
    'column.case': (u'Cas', u'Case'),
    'column.unit': (u'Unité', u'Unit'),
    'column.simulated': (u'Simulé', u'Simulated'),
    'column.reference': (u'Référence', u'Reference'),
    'column.band': (u'Bande admissible', u'Admissible band'),
    'column.verdict': (u'Verdict', u'Verdict'),
    'column.source': (u'Source', u'Source'),
    'column.status': (u'État', u'Status'),

    # -- Section headings --------------------------------------------------
    'section.classes': (u'Classes de validation', u'Validation classes'),
    'section.results': (u'Résultats', u'Results'),
    'section.evidence': (u'Preuves', u'Evidence'),
    'section.blocking': (u'Ce qui bloque', u'What is blocking'),
    'section.not_established': (u'Ce qui n\'est pas établi',
                                u'What is not established'),

    # -- Empty and error states. Never blank, always actionable. -----------
    'state.no_results': (
        u'Aucun résultat. Lancez une simulation ApacheSim sur l\'année '
        u'complète, puis relancez la vérification.',
        u'No results. Run ApacheSim over the full year, then run the check '
        u'again.'),
    'state.no_selection': (
        u'Sélectionnez au moins une classe de validation.',
        u'Select at least one validation class.'),
    'state.missing_climate': (
        u'Climat SIA 2028 DRY Zürich-Kloten absent. Sans lui, aucune '
        u'simulation de ce test n\'est un cas de validation SIA.',
        u'SIA 2028 DRY Zürich-Kloten climate missing. Without it, no '
        u'simulation of this test is an SIA validation case.'),
    'state.outside_ve': (
        u'Hors de VEScripts : les relevés du modèle ne sont pas disponibles.',
        u'Outside VEScripts: model readings are unavailable.'),

    # -- Standing reminders. They exist because these three get confused. --
    'note.pass_is_not_compliance': (
        u'Un PASS technique n\'est ni une conformité SIA 380/2 ni une '
        u'validation SIA 4010.',
        u'A technical PASS is neither SIA 380/2 compliance nor SIA 4010 '
        u'validation.'),
    'note.absence_is_not_zero': (
        u'Une valeur absente n\'est pas zéro.',
        u'A missing value is not zero.'),
    'note.generated_document': (
        u'Document généré. Corriger la source, puis régénérer.',
        u'Generated document. Fix the source, then regenerate.'),

    # -- Language switch ---------------------------------------------------
    'language.label': (u'Langue', u'Language'),
    'language.fr': (u'Français', u'French'),
    'language.en': (u'Anglais', u'English'),
}


class MissingTranslation(KeyError):
    """Raised when a key has no entry, or no entry in the asked language.

    It is an error rather than a fallback on purpose: see the module note.
    """


class UnknownLanguage(ValueError):
    """Raised for a language this module cannot render."""


_current = DEFAULT_LANGUAGE


def language():
    """Return the language in force.

    Returns:
        str: `FRENCH` or `ENGLISH`.
    """
    return _current


def set_language(code):
    """Switch the language for every later lookup.

    Args:
        code: `FRENCH` or `ENGLISH`.

    Returns:
        str: The language now in force.

    Raises:
        UnknownLanguage: For anything else. Falling back to the default here
            would show a French dialog to someone who asked for English and
            report success.
    """
    global _current
    if code not in LANGUAGES:
        raise UnknownLanguage(
            'unknown language %r; known: %s' % (code, list(LANGUAGES)))
    _current = code
    return _current


def translate(key, code=None):
    """Return one user-facing string.

    Args:
        key: Dotted key from `STRINGS`.
        code: Language, or `None` for the one in force.

    Returns:
        str: The string.

    Raises:
        MissingTranslation: If the key is unknown or its entry is empty. No
            fallback to the key, to the other language, or to an empty
            string -- a blank where a verdict belongs is a false report.
        UnknownLanguage: For an unknown language code.
    """
    wanted = _current if code is None else code
    if wanted not in LANGUAGES:
        raise UnknownLanguage(
            'unknown language %r; known: %s' % (wanted, list(LANGUAGES)))
    if key not in STRINGS:
        raise MissingTranslation(
            'no string for %r. Add it to STRINGS in both languages.' % key)
    entry = STRINGS[key]
    text = entry[LANGUAGES.index(wanted)]
    if not text:
        raise MissingTranslation(
            'string %r is empty in %r. Add it, do not leave it blank.'
            % (key, wanted))
    return text


#: Short alias. Used heavily in layout code, where the noise of a long name
#: buries the structure it is meant to make readable.
t = translate


def check_completeness():
    """Report keys that are not translated in every language.

    Called by the test suite. A label added in one language only would show
    up blank -- or raise -- for the other half of the users.

    Returns:
        dict: `{'missing': [(key, language)], 'checked': int}`.
    """
    missing = []
    for key in sorted(STRINGS):
        entry = STRINGS[key]
        if len(entry) != len(LANGUAGES):
            missing.append((key, 'wrong arity: %d' % len(entry)))
            continue
        for index, code in enumerate(LANGUAGES):
            if not entry[index]:
                missing.append((key, code))
    return {'missing': missing, 'checked': len(STRINGS)}


def verdict_key(verdict):
    """Map an engine verdict to its string key.

    The engines speak a fixed vocabulary -- `PASS`, `FAIL`, `WARNING`,
    `NOT_CHECKABLE`, `NON_EVALUE`, `NON_ETABLI`. Mapping it here keeps the
    dialog, the Excel export and the PDF from each inventing their own
    wording for the same state.

    Args:
        verdict: Verdict string as an engine produces it.

    Returns:
        str: Key into `STRINGS`.

    Raises:
        MissingTranslation: For a verdict this module does not know. Silently
            showing "NON EVALUE" for an unrecognised verdict would hide a
            state we have not thought about.
    """
    known = {
        'PASS': 'verdict.pass',
        'FAIL': 'verdict.fail',
        'WARNING': 'verdict.warning',
        'NOT_CHECKABLE': 'verdict.not_checkable',
        'NON_EVALUE': 'verdict.not_evaluated',
        'NON_EVALUEE': 'verdict.not_evaluated',
        'NOT_EVALUATED': 'verdict.not_evaluated',
        'NON_ETABLI': 'verdict.not_checkable',
        'NOT_ESTABLISHED': 'verdict.not_checkable',
        'NON_SIGNE': 'verdict.not_signed',
        'NOT_SIGNED': 'verdict.not_signed',
    }
    if verdict not in known:
        raise MissingTranslation(
            'unknown verdict %r. Add it to verdict_key rather than letting '
            'it render as something else.' % verdict)
    return known[verdict]
