"""Qualified active-case APS extraction and comparison tests."""

import unittest
from pathlib import Path

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.active_case_evaluation import (
    REFERENCE_ONLY_RESULTS_RECORDED,
    evaluate_qualified_active_case,
)


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "SIA_4010_geteilter_Link"
BINDINGS = ROOT / "config" / "sia4010_aps_bindings_ve_runtime.json"


class _HourlyResults:
    """Minimal ResultsReader double matching the qualified runtime metadata."""

    results_per_day = 24

    def __init__(self):
        self.values = {
            "Room units heating load": [1000.0] * 8760,
            "Room units cooling load": [500.0] * 8760,
            "Window solar gains": [200.0] * 8760,
            "Room air temperature": [20.0] * 8760,
            "Comfort temperature": [22.0] * 8760,
        }

    def get_variables(self):
        variables = {
            "Room units heating load": (
                "Heating plant sensible load",
                "power",
            ),
            "Room units cooling load": (
                "Cooling plant sensible load",
                "power",
            ),
            "Window solar gains": ("Solar gain", "power"),
            "Room air temperature": ("Air temperature", "temperature"),
            "Comfort temperature": (
                "Dry resultant temperature",
                "temperature",
            ),
        }
        return [
            {
                "aps_varname": name,
                "display_name": metadata[0],
                "model_level": "z",
                "units_type": metadata[1],
            }
            for name, metadata in variables.items()
        ]

    @staticmethod
    def get_units():
        return {
            "power": {
                "units_metric": {
                    "display_name": "kW",
                    "divisor": 1000.0,
                    "offset": 0.0,
                }
            },
            "temperature": {
                "units_metric": {
                    "display_name": "°C",
                    "divisor": 1.0,
                    "offset": 0.0,
                }
            },
        }

    def get_room_results(self, room_id, aps_var, vista_var, level):
        return self.values[aps_var]


@unittest.skipUnless(BUNDLE.is_dir(), "official SIA 4010 package not present")
class ActiveCaseEvaluationTests(unittest.TestCase):
    def test_test2_evaluates_only_the_selected_exact_variant(self):
        receipt = evaluate_qualified_active_case(
            variant="test_2A",
            case_id="2A",
            results_file=_HourlyResults(),
            room_id="R1",
            aps_path=Path(__file__),
            bundle_root=BUNDLE,
            bindings_path=BINDINGS,
        )
        self.assertEqual(receipt.variant, "test_2A")
        self.assertEqual(receipt.observed_metric_count, 1)
        self.assertEqual(receipt.distribution_criterion_count, 1)
        self.assertEqual(
            receipt.status,
            receipt.evaluation.variant_statuses["test_2A"],
        )

    def test_test1_case1e_extracts_the_complete_official_metric_set(self):
        receipt = evaluate_qualified_active_case(
            variant="test_1",
            case_id="1E",
            results_file=_HourlyResults(),
            room_id="R1",
            aps_path=Path(__file__),
            bundle_root=BUNDLE,
            bindings_path=BINDINGS,
        )
        self.assertEqual(receipt.test_id, "1")
        self.assertEqual(receipt.observed_metric_count, 28)
        self.assertEqual(receipt.distribution_criterion_count, 0)
        self.assertTrue(receipt.acceptance_criterion_available)
        self.assertTrue(receipt.required_output_scope_complete)

    def test_test1_case600_records_results_without_false_verdict(self):
        receipt = evaluate_qualified_active_case(
            variant="test_1",
            case_id="600",
            results_file=_HourlyResults(),
            room_id="R1",
            aps_path=Path(__file__),
            bundle_root=BUNDLE,
            bindings_path=BINDINGS,
        )
        self.assertEqual(receipt.observed_metric_count, 88)
        self.assertEqual(receipt.status, REFERENCE_ONLY_RESULTS_RECORDED)
        self.assertFalse(receipt.acceptance_criterion_available)
        self.assertTrue(receipt.required_output_scope_complete)
        self.assertEqual(receipt.evaluation.comparisons, ())
        self.assertEqual(
            receipt.evaluation.band_status,
            "NO_ACCEPTANCE_CRITERION",
        )

    def test_unqualified_test_family_is_rejected_before_reading_aps(self):
        with self.assertRaises(ConfigurationError):
            evaluate_qualified_active_case(
                variant="test_3A",
                case_id="3A",
                results_file=_HourlyResults(),
                room_id="R1",
                aps_path=Path("missing.aps"),
                bundle_root=BUNDLE,
                bindings_path=BINDINGS,
            )

    def test_test1_free_float_temperature_results_are_recorded(self):
        receipt = evaluate_qualified_active_case(
            variant="test_1",
            case_id="600FF",
            results_file=_HourlyResults(),
            room_id="R1",
            aps_path=Path(__file__),
            bundle_root=BUNDLE,
            bindings_path=BINDINGS,
        )
        self.assertEqual(receipt.observed_metric_count, 39)
        self.assertEqual(receipt.status, REFERENCE_ONLY_RESULTS_RECORDED)
        self.assertFalse(receipt.acceptance_criterion_available)
        self.assertTrue(receipt.required_output_scope_complete)


if __name__ == "__main__":
    unittest.main()
