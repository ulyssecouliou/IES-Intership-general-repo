"""Tests for the multilingual Swiss VE Model Builder interface catalogue."""

import re
import unittest
from pathlib import Path

from Build_SIA_Model_Builder_Interface import build
from swiss_sia.reference_model.sia4010.ui_translations import (
    DEFAULT_LANGUAGE,
    LANGUAGE_LABELS,
    LANGUAGES,
    TRANSLATIONS,
    catalog_for,
    missing_translations,
    normalize_language,
    translate,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


class CatalogueCompletenessTests(unittest.TestCase):
    """Every supported language must be fully translated."""

    def test_supported_languages_cover_swiss_national_plus_english(self):
        self.assertEqual(set(LANGUAGES), {"en", "de", "fr", "it"})
        self.assertIn(DEFAULT_LANGUAGE, LANGUAGES)
        self.assertEqual(set(LANGUAGE_LABELS), set(LANGUAGES))

    def test_no_language_has_a_missing_or_blank_string(self):
        self.assertEqual(missing_translations(), {})

    def test_default_is_english_and_core_french_copy_has_accents(self):
        self.assertEqual(DEFAULT_LANGUAGE, "en")
        expected = {
            "client_ui_window_title": "Conformité",
            "client_ui_section_model": "Présentation",
            "client_ui_weather_detected": "météo",
            "client_ui_evidence_help": "éclairage",
            "client_ui_evidence_open": "Compléter",
        }
        for key, accented in expected.items():
            with self.subTest(key=key):
                self.assertIn(accented, translate(key, "fr"))

    def test_client_interface_has_no_known_ascii_french_regressions(self):
        forbidden = (
            "conformite",
            "evaluation",
            "modele",
            "meteo",
            "donnees",
            "telephone",
            "represente",
            "reponse",
            " a afficher",
            " a integrer",
            "ajoutee",
            " apres ",
            "selectionne",
        )
        rendered = " ".join(
            translate(key, "fr") for key in TRANSLATIONS if key.startswith("client_ui_")
        ).lower()
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, rendered)

    def test_every_key_is_present_in_every_language(self):
        for key, entry in TRANSLATIONS.items():
            with self.subTest(key=key):
                self.assertEqual(set(entry), set(LANGUAGES))

    def test_catalog_for_returns_all_keys(self):
        for code in LANGUAGES:
            with self.subTest(language=code):
                self.assertEqual(set(catalog_for(code)), set(TRANSLATIONS))

    def test_swiss_german_orthography_avoids_eszett(self):
        # Swiss German uses "ss"; an eszett would be wrong for a Swiss document.
        offenders = [key for key, entry in TRANSLATIONS.items() if "ß" in entry["de"]]
        self.assertEqual(offenders, [])

    def test_placeholders_are_preserved_across_languages(self):
        # A translated string must keep the exact {placeholders} its callers format.
        for key, entry in TRANSLATIONS.items():
            expected = set(re.findall(r"\{(\w+)\}", entry[DEFAULT_LANGUAGE]))
            for code in LANGUAGES:
                with self.subTest(key=key, language=code):
                    self.assertEqual(set(re.findall(r"\{(\w+)\}", entry[code])), expected)

    def test_standard_identifiers_stay_verbatim_in_every_language(self):
        # A normative designation must never be reshaped by grammar (German
        # compounding would turn "SIA 4010" into "SIA-4010-Fall").
        pattern = re.compile(r"SIA[‐-―\- ]\d")
        offenders = [
            "{}/{}".format(key, code)
            for key, entry in TRANSLATIONS.items()
            for code in LANGUAGES
            if pattern.search(entry[code])
        ]
        self.assertEqual(offenders, [])

    def test_official_option_names_the_standard(self):
        for code in LANGUAGES:
            with self.subTest(language=code):
                self.assertIn("SIA 4010", translate("option_official", code))

    def test_dynamic_domain_has_a_human_label_in_every_language(self):
        for code in LANGUAGES:
            with self.subTest(language=code):
                label = translate("domain_dynamic", code)
                self.assertNotEqual(label, "domain_dynamic")
                self.assertIn("SIA 180", label)


class LanguageResolutionTests(unittest.TestCase):
    def test_exact_codes_resolve(self):
        for code in LANGUAGES:
            self.assertEqual(normalize_language(code), code)

    def test_swiss_locales_resolve_to_their_base_language(self):
        self.assertEqual(normalize_language("de-CH"), "de")
        self.assertEqual(normalize_language("fr_CH"), "fr")
        self.assertEqual(normalize_language("it-CH"), "it")

    def test_unknown_or_empty_falls_back_to_the_default(self):
        for value in ("", None, "es", "zz-ZZ"):
            self.assertEqual(normalize_language(value), DEFAULT_LANGUAGE)

    def test_unknown_key_returns_the_key_rather_than_raising(self):
        self.assertEqual(translate("no_such_key", "de"), "no_such_key")


class EmbeddedInterfaceTests(unittest.TestCase):
    """The standalone HTML must ship every language and switch offline."""

    @classmethod
    def setUpClass(cls):
        """Build the interface once and read it back."""
        cls.html = build().read_text(encoding="utf-8")

    def test_no_placeholder_survives_the_build(self):
        self.assertNotIn("__CATALOG_JSON__", self.html)
        self.assertNotIn("__I18N_JSON__", self.html)

    def test_every_language_is_embedded(self):
        for code in LANGUAGES:
            with self.subTest(language=code):
                self.assertIn('"{}"'.format(code), self.html)
        # A representative string from each language proves the payload is real.
        self.assertIn("Vorbereiten und prüfen", self.html)
        self.assertIn("Préparer et contrôler", self.html)
        self.assertIn("Prepara e verifica", self.html)
        self.assertIn("Prepare and check", self.html)

    def test_language_switcher_is_present(self):
        self.assertIn('id="lang"', self.html)
        self.assertIn("applyLanguage", self.html)

    def test_machine_codes_stay_untranslated_in_the_markup(self):
        # The generated scenario must carry codes, never localized labels.
        self.assertIn('value="SIA4010_OFFICIAL"', self.html)
        self.assertIn('value="PREPARE_ONLY"', self.html)
        self.assertIn('value="CREATE_IN_ACTIVE_VE_PROJECT"', self.html)

    def test_document_structure_is_intact(self):
        self.assertTrue(self.html.lstrip().startswith("<!doctype html>"))
        self.assertEqual(self.html.count("<html"), 1)
        self.assertEqual(self.html.count("</html>"), 1)


class NativeWindowLanguageTests(unittest.TestCase):
    """The VEScripts window resolves and switches language without a display."""

    def _window(self, language=None):
        """Return an unconstructed window with only the language state set."""
        from swiss_sia.reference_model.sia4010.native_ui import (
            NativeModelBuilderWindow,
        )

        window = NativeModelBuilderWindow.__new__(NativeModelBuilderWindow)
        window.language = normalize_language(language or DEFAULT_LANGUAGE)
        return window

    def test_translation_helper_follows_the_active_language(self):
        for code in LANGUAGES:
            with self.subTest(language=code):
                window = self._window(code)
                self.assertEqual(window.t("btn_prepare"), translate("btn_prepare", code))

    def test_swiss_locale_is_accepted_by_the_window(self):
        self.assertEqual(self._window("de-CH").t("btn_close"), "Schliessen")

    def test_each_language_has_distinct_action_wording(self):
        wordings = {translate("btn_prepare", code) for code in LANGUAGES}
        self.assertEqual(len(wordings), len(LANGUAGES))


if __name__ == "__main__":
    unittest.main()
