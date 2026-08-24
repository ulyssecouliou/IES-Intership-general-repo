"""Every key a client-facing report builds at runtime must resolve.

WHY THIS EXISTS. ``translate`` returns the key itself when a translation is
missing, deliberately, so a partly translated VEScripts window degrades to a
visible marker rather than crashing. That trade-off is right for an interface
and wrong for a PDF handed to a client: on 2026-08-12 a real report printed

    Outstanding evidence: reviewed project/reference comparison,
    outstanding_sia3802_domain_evidence, official SIA 4010 test results, ...

because ``compliance_report_pdf`` composes the key as
``"outstanding_" + item`` and one of the five items had no entry. A grep cannot
catch a key that is never written as a literal, so it is checked here instead.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from swiss_sia.reference_model.sia4010.ui_translations import (
    LANGUAGES,
    TRANSLATIONS,
    translate,
)


ROOT = Path(__file__).resolve().parents[1]

#: The vocabulary of ``ComplianceVerdict.outstanding``, read from its producer
#: rather than restated, so a new item cannot be added without this test
#: noticing.
VERDICT_SOURCE = ROOT / "swiss_sia" / "compliance_verdict.py"

DOMAIN_REASONS = (
    "domain_not_evaluated",
    "blocking_findings",
    "evidence_incomplete",
    "no_blocking_finding_with_limitations",
    "no_blocking_finding",
)


def _outstanding_items() -> list[str]:
    text = VERDICT_SOURCE.read_text(encoding="utf-8")
    return sorted(set(re.findall(r'outstanding\.append\(\s*"([a-z0-9_]+)"', text)))


class OutstandingKeyCoverageTests(unittest.TestCase):

    def test_the_producer_still_declares_its_items_the_expected_way(self) -> None:
        """Guard the guard: if the append pattern changes, this test is blind."""

        items = _outstanding_items()
        self.assertGreaterEqual(
            len(items), 5, msg="found only {}; has the pattern changed?".format(items)
        )

    def test_every_outstanding_item_has_a_translation(self) -> None:
        missing = [
            item
            for item in _outstanding_items()
            if "outstanding_" + item not in TRANSLATIONS
        ]
        self.assertEqual(
            missing,
            [],
            msg=(
                "these items would print their raw key in a client report: "
                "{}".format(missing)
            ),
        )

    def test_no_outstanding_key_resolves_to_itself_in_any_language(self) -> None:
        """The exact failure observed in the field, in all four languages."""

        for item in _outstanding_items():
            key = "outstanding_" + item
            for language in LANGUAGES:
                rendered = translate(key, language)
                self.assertNotEqual(
                    rendered,
                    key,
                    msg="{} unresolved in {}".format(key, language),
                )
                self.assertTrue(rendered.strip())

    def test_outstanding_translations_are_lower_case_fragments(self) -> None:
        """They are spliced into a sentence, so they must not be capitalised.

        The scope line reads "Outstanding evidence: a, b, c." A fragment
        starting with a capital would read as a new sentence.

        GERMAN IS EXEMPT, and not as a convenience: German capitalises every
        noun, so "Klassenbereitschaftsnachweis" mid-sentence is correct and
        lowercasing it would be a spelling error. The first version of this test
        failed on exactly that and was wrong to.
        """

        checked = tuple(code for code in LANGUAGES if code != "de")
        for item in _outstanding_items():
            for language in checked:
                rendered = translate("outstanding_" + item, language).lstrip()
                first = rendered[:1]
                if not first.isalpha():
                    continue
                # An acronym opening the fragment is not a sentence start.
                if rendered.split(" ", 1)[0].isupper():
                    continue
                self.assertFalse(
                    first.isupper(),
                    msg="{} in {} starts capitalised: {!r}".format(
                        item, language, rendered
                    ),
                )


class DomainReasonCoverageTests(unittest.TestCase):
    """Prevent an internal domain-reason token from reaching a client PDF."""

    def test_every_domain_reason_resolves_in_every_language(self) -> None:
        for reason in DOMAIN_REASONS:
            key = "report_domain_reason_" + reason
            self.assertIn(key, TRANSLATIONS)
            for language in LANGUAGES:
                rendered = translate(key, language)
                self.assertNotEqual(rendered, key)
                self.assertTrue(rendered.strip())


class ScopeSentenceTests(unittest.TestCase):
    """The sentence the fragments are spliced into must keep its placeholder."""

    def test_scope_outstanding_carries_the_items_placeholder(self) -> None:
        for language in LANGUAGES:
            rendered = translate("scope_outstanding", language)
            self.assertIn("{items}", rendered, msg="missing in {}".format(language))

    def test_the_two_scope_lines_resolve(self) -> None:
        for key in ("scope_line_1", "scope_line_2"):
            for language in LANGUAGES:
                self.assertNotEqual(translate(key, language), key)


if __name__ == "__main__":
    unittest.main()
