"""Release gates for the multilingual project-evidence editor."""

import unittest

from swiss_sia.project_evidence import FAMILIES
from swiss_sia.project_evidence_translations import (
    FIELD_TEXT,
    family_help,
    family_title,
    field_label,
    missing_translations,
    text,
)
from swiss_sia.reference_model.sia4010.ui_translations import LANGUAGES


class ProjectEvidenceTranslationTests(unittest.TestCase):
    def test_every_visible_entry_exists_in_all_four_languages(self) -> None:
        self.assertEqual(set(LANGUAGES), {"en", "de", "fr", "it"})
        self.assertEqual(missing_translations(), ())
        fields = {field for family in FAMILIES for field in family.fields}
        self.assertEqual(set(FIELD_TEXT), fields)

    def test_every_language_renders_human_copy(self) -> None:
        for language in LANGUAGES:
            with self.subTest(language=language):
                self.assertTrue(text("save", language))
                self.assertTrue(family_title("project_metadata", language))
                self.assertTrue(family_help("project_metadata", language))
                self.assertTrue(field_label("weather_file", language))

    def test_english_is_reviewed_default_and_french_keeps_accents(self) -> None:
        self.assertEqual(text("save"), "Save active tab")
        self.assertEqual(field_label("weather_file"), "Weather file")
        self.assertEqual(text("save", "fr"), "Enregistrer l’onglet actif")
        self.assertEqual(field_label("weather_file", "fr"), "Fichier météo")
        self.assertIn("traçables", text("intro", "fr"))
        self.assertIn("complète", text("intro", "fr"))


if __name__ == "__main__":
    unittest.main()
