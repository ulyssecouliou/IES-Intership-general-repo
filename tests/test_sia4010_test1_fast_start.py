"""Tests for the folder-safe Test 1 Fast Start selector."""

import unittest
from pathlib import Path

from Run_VE_SIA4010_Test1_Fast_Start import (
    _execution_mode,
    _reload_launcher,
    _select_case,
)


class Test1FastStartTests(unittest.TestCase):
    def test_case_is_inferred_from_disposable_folder(self):
        for case_id in ("640", "600FF", "900", "940", "900FF"):
            path = Path("C:/Models/SIA4010_TEST1_{}_DISPOSABLE".format(case_id))
            self.assertEqual(_select_case(path), case_id)

    def test_free_float_is_not_shortened(self):
        self.assertEqual(
            _select_case(Path("C:/Models/SIA4010_TEST1_600FF_DISPOSABLE")),
            "600FF",
        )
        self.assertEqual(
            _select_case(Path("C:/Models/SIA4010_TEST1_900FF_DISPOSABLE")),
            "900FF",
        )

    def test_case_is_inferred_from_user_folder_order(self):
        self.assertEqual(
            _select_case(Path("C:/Models/Test_640_Test1")),
            "640",
        )

    def test_registered_execution_mode_is_selected_per_case(self):
        self.assertEqual(
            _execution_mode("600"),
            "CREATE_IN_ACTIVE_VE_PROJECT",
        )
        for case_id in ("640", "600FF", "900", "940", "900FF"):
            with self.subTest(case_id=case_id):
                self.assertEqual(
                    _execution_mode(case_id),
                    "QUALIFY_IN_ACTIVE_VE_PROJECT",
                )

    def test_reload_launcher_refreshes_a_cached_ve_launcher(self):
        module = _reload_launcher("Run_VE_SIA4010_Test1_Active_Case_One_Click")
        refreshed = _reload_launcher(module.__name__)
        self.assertEqual(refreshed.__name__, module.__name__)


if __name__ == "__main__":
    unittest.main()
