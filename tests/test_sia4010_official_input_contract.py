"""Validation of the source-traced Tests 2-7 input contract."""

import unittest
from pathlib import Path

from swiss_sia.reference_model.sia4010.official_input_contract import (
    Sia4010OfficialInputContract,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "sia4010_official_input_contract.json"


class Sia4010OfficialInputContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = Sia4010OfficialInputContract.load(CONTRACT)

    def test_every_base_test_2_to_7_is_source_traced(self):
        self.assertEqual(set(self.contract.tests), set("234567"))
        for test_id, item in self.contract.tests.items():
            with self.subTest(test_id=test_id):
                self.assertTrue(item.source)
                self.assertTrue(item.source_pages)
                self.assertTrue(item.confirmed_inputs)

    def test_unresolved_dependencies_are_never_erased(self):
        for test_id, item in self.contract.tests.items():
            with self.subTest(test_id=test_id):
                self.assertTrue(item.unresolved_dependencies)
                self.assertEqual(item.ve_generation_status, "NOT_IMPLEMENTED")

    def test_exact_variant_cardinality_matches_official_matrix(self):
        expected = {"2": 4, "3": 12, "4": 1, "5": 4, "6": 1, "7": 1}
        self.assertEqual(
            {
                test_id: len(item.variants)
                for test_id, item in self.contract.tests.items()
            },
            expected,
        )

    def test_critical_values_are_not_rounded_into_other_requirements(self):
        test2 = self.contract.test("2").confirmed_inputs
        self.assertEqual(test2["glazing_g_value"], 0.545)
        self.assertEqual(test2["external_shading_activation_w_m2"], 150.0)
        test7 = self.contract.test("7").confirmed_inputs
        self.assertEqual(test7["nominal_cooling_kw"], 55.9)
        self.assertEqual(test7["nominal_heating_kw"], 60.0)


if __name__ == "__main__":
    unittest.main()

