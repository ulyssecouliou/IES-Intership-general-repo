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

FRENCH = "fr"
ENGLISH = "en"

#: Languages this module can render. French leads because the tool is used
#: against Swiss standards, in French-speaking practice.
LANGUAGES = (FRENCH, ENGLISH)

DEFAULT_LANGUAGE = FRENCH

#: Every user-facing string, keyed by a dotted path. Adding a key means adding
#: BOTH languages -- `check_completeness` fails the build otherwise, so a
#: half-added label cannot reach a user.
STRINGS = {
    # -- Window and shell ---------------------------------------------------
    "app.title": ("Navigateur de validation SIA 4010", "SIA 4010 Validation Navigator"),
    "app.subtitle": (
        "Vérification des classes de validation pour IESVE",
        "Validation class checking for IESVE",
    ),
    "app.product": ("IES Virtual Environment", "IES Virtual Environment"),
    # -- Primary actions ---------------------------------------------------
    "action.run": ("Lancer la vérification", "Run check"),
    "action.close": ("Fermer", "Close"),
    "action.export_excel": ("Exporter vers Excel", "Export to Excel"),
    "action.export_pdf": ("Exporter en PDF", "Export to PDF"),
    "action.refresh": ("Actualiser", "Refresh"),
    "action.select_all": ("Tout sélectionner", "Select all"),
    "action.select_none": ("Tout désélectionner", "Clear selection"),
    "action.copy_details": ("Copier le détail", "Copy details"),
    # -- Verdicts. The most sensitive entries in this table. ----------------
    "verdict.pass": ("CONFORME", "PASS"),
    "verdict.fail": ("NON CONFORME", "FAIL"),
    "verdict.warning": ("RÉSERVE", "WARNING"),
    "verdict.not_checkable": ("NON VÉRIFIABLE", "NOT CHECKABLE"),
    "verdict.not_evaluated": ("NON ÉVALUÉ", "NOT EVALUATED"),
    "verdict.not_signed": ("NON SIGNÉ", "NOT SIGNED"),
    # -- What a verdict means. Shown next to it, never instead of it. -------
    "verdict.pass.help": (
        "La valeur simulée tombe dans la bande de référence. Ce n'est pas "
        "une validation SIA 4010 : celle-ci demande une signature "
        "indépendante.",
        "The simulated value falls inside the reference band. This is not "
        "SIA 4010 validation, which requires an independent signature.",
    ),
    "verdict.fail.help": (
        "La valeur simulée sort de la bande de référence.",
        "The simulated value falls outside the reference band.",
    ),
    "verdict.warning.help": (
        "Un contrôle a abouti, mais sous une réserve qui doit être levée.",
        "A check completed, but under a reservation that must be lifted.",
    ),
    "verdict.not_checkable.help": (
        "Une entrée indispensable manque. Ce n'est pas un échec : rien "
        "n'a pu être comparé.",
        "A required input is missing. This is not a failure: nothing could "
        "be compared.",
    ),
    "verdict.not_evaluated.help": (
        "Aucune simulation n'a produit de valeur candidate.",
        "No simulation has produced a candidate value.",
    ),
    # -- Column headings ---------------------------------------------------
    "column.test": ("Test", "Test"),
    "column.class": ("Classe", "Class"),
    "column.quantity": ("Grandeur", "Quantity"),
    "column.case": ("Cas", "Case"),
    "column.unit": ("Unité", "Unit"),
    "column.simulated": ("Simulé", "Simulated"),
    "column.reference": ("Référence", "Reference"),
    "column.band": ("Bande admissible", "Admissible band"),
    "column.verdict": ("Verdict", "Verdict"),
    "column.source": ("Source", "Source"),
    "column.status": ("État", "Status"),
    # -- Section headings --------------------------------------------------
    "section.classes": ("Classes de validation", "Validation classes"),
    "section.results": ("Résultats", "Results"),
    "section.evidence": ("Preuves", "Evidence"),
    "section.blocking": ("Ce qui bloque", "What is blocking"),
    "section.not_established": ("Ce qui n'est pas établi", "What is not established"),
    # -- Empty and error states. Never blank, always actionable. -----------
    "state.no_results": (
        "Aucun résultat. Lancez une simulation ApacheSim sur l'année "
        "complète, puis relancez la vérification.",
        "No results. Run ApacheSim over the full year, then run the check " "again.",
    ),
    "state.no_selection": (
        "Sélectionnez au moins une classe de validation.",
        "Select at least one validation class.",
    ),
    "state.missing_climate": (
        "Climat SIA 2028 DRY Zürich-Kloten absent. Sans lui, aucune "
        "simulation de ce test n'est un cas de validation SIA.",
        "SIA 2028 DRY Zürich-Kloten climate missing. Without it, no "
        "simulation of this test is an SIA validation case.",
    ),
    "state.outside_ve": (
        "Hors de VEScripts : les relevés du modèle ne sont pas disponibles.",
        "Outside VEScripts: model readings are unavailable.",
    ),
    # -- Standing reminders. They exist because these three get confused. --
    "note.pass_is_not_compliance": (
        "Un PASS technique n'est ni une conformité SIA 380/2 ni une "
        "validation SIA 4010.",
        "A technical PASS is neither SIA 380/2 compliance nor SIA 4010 " "validation.",
    ),
    "note.absence_is_not_zero": (
        "Une valeur absente n'est pas zéro.",
        "A missing value is not zero.",
    ),
    "note.generated_document": (
        "Document généré. Corriger la source, puis régénérer.",
        "Generated document. Fix the source, then regenerate.",
    ),
    # -- Validation classes ------------------------------------------------
    #
    # RESERVATION, AND IT MATTERS. These eight descriptions RENDER the
    # "applications" column of SIA 4010:2023 table 63 (p. 48), which is
    # published in German. They are not quotations, in either language, and
    # nothing matches on them -- they exist so the selector reads as something
    # other than eight bare identifiers. If the SIA publishes an official
    # French or English wording, replace these with it and say so here.
    "class.1A": (
        "Besoins de chaleur, bâtiment sans refroidissement",
        "Heating demand, building without cooling",
    ),
    "class.1B": ("Besoins de chaleur, tous bâtiments", "Heating demand, all buildings"),
    "class.2A": (
        "Besoins de chaleur et de froid, protection solaire simple",
        "Heating and cooling demand, simple solar shading",
    ),
    "class.2B": (
        "Besoins de chaleur et de froid, protection solaire et " "éclairage",
        "Heating and cooling demand, solar shading and lighting",
    ),
    "class.3": (
        "Installations de ventilation et de climatisation",
        "Ventilation and air-conditioning systems",
    ),
    "class.4A": (
        "Bâtiment complet, protection solaire simple",
        "Whole building, simple solar shading",
    ),
    "class.4B": ("Bâtiment complet, tous équipements", "Whole building, all systems"),
    "class.5": (
        "Besoins de chaleur et de froid pour profils existants",
        "Heating and cooling demand for existing profiles",
    ),
    # -- Language switch ---------------------------------------------------
    "language.label": ("Langue", "Language"),
    "language.fr": ("Français", "French"),
    "language.en": ("Anglais", "English"),
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
        raise UnknownLanguage("unknown language %r; known: %s" % (code, list(LANGUAGES)))
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
            "unknown language %r; known: %s" % (wanted, list(LANGUAGES))
        )
    if key not in STRINGS:
        raise MissingTranslation(
            "no string for %r. Add it to STRINGS in both languages." % key
        )
    entry = STRINGS[key]
    text = entry[LANGUAGES.index(wanted)]
    if not text:
        raise MissingTranslation(
            "string %r is empty in %r. Add it, do not leave it blank." % (key, wanted)
        )
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
            missing.append((key, "wrong arity: %d" % len(entry)))
            continue
        for index, code in enumerate(LANGUAGES):
            if not entry[index]:
                missing.append((key, code))
    return {"missing": missing, "checked": len(STRINGS)}


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
        "PASS": "verdict.pass",
        "FAIL": "verdict.fail",
        "WARNING": "verdict.warning",
        "NOT_CHECKABLE": "verdict.not_checkable",
        "NON_EVALUE": "verdict.not_evaluated",
        "NON_EVALUEE": "verdict.not_evaluated",
        "NOT_EVALUATED": "verdict.not_evaluated",
        "NON_ETABLI": "verdict.not_checkable",
        "NOT_ESTABLISHED": "verdict.not_checkable",
        "NON_SIGNE": "verdict.not_signed",
        "NOT_SIGNED": "verdict.not_signed",
        # Vocabulaire des STATUTS DE CLASSE (`ui/class_selection.py`), qui
        # nomme les memes trois etats autrement. Les laisser passer bruts
        # affichait « NON_EVALUEE » a l ecran -- un identifiant interne.
        "CONFORME": "verdict.pass",
        "NON_CONFORME": "verdict.fail",
        "NON_EVALUEE": "verdict.not_evaluated",
    }
    if verdict not in known:
        raise MissingTranslation(
            "unknown verdict %r. Add it to verdict_key rather than letting "
            "it render as something else." % verdict
        )
    return known[verdict]
