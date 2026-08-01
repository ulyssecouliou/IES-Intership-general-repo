"""Smoke tests for the standalone scenario-selection interface."""

import unittest

from Build_SIA_Model_Builder_Interface import build


class SiaModelBuilderInterfaceTests(unittest.TestCase):
    def test_builds_standalone_interface_with_embedded_catalog(self):
        path = build()
        html = path.read_text(encoding="utf-8")
        self.assertNotIn("__CATALOG_JSON__", html)
        self.assertIn("SIA4010_OFFICIAL", html)
        self.assertIn("official_feature_matrix", html)
        self.assertIn("sia_model_scenario.json", html)
        self.assertIn("Run_VE_SIA_Model_Builder.py", html)
        self.assertIn(
            'value="config/sia4010_all_classes.json"',
            html,
        )
        self.assertNotIn(
            'value="config/sia4010_classes_1a_1b.json"',
            html,
        )


if __name__ == "__main__":
    unittest.main()
