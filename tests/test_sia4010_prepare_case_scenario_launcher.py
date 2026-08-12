"""The scenario-preparation launcher must agree with the probes it feeds.

``Run_VE_SIA4010_Prepare_Case_Scenario`` exists because the Test 3 and
Tests 4-7 runtime-capability probes refuse to run without a validated
``sia_model_scenario.json``, and the only scripted writers of that file were
hard-wired to Test 1.  A launcher that prepared a case the probe then rejected
would just move the failure one step later, so the case set and the variant
derivation are asserted against the probes' own contracts rather than restated
here.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "Run_VE_SIA4010_Prepare_Case_Scenario.py"


def _load_launcher():
    """Import the launcher by path: its name is not an importable package."""

    spec = importlib.util.spec_from_file_location(
        "run_ve_sia4010_prepare_case_scenario", LAUNCHER
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PrepareCaseScenarioLauncherTests(unittest.TestCase):

    def setUp(self) -> None:
        self.launcher = _load_launcher()

    def test_the_launcher_exists(self) -> None:
        self.assertTrue(LAUNCHER.is_file())

    def test_every_test3_variant_is_reachable(self) -> None:
        """Test 3 asserts case_id == variant[5:]; the launcher must match."""

        from swiss_sia.reference_model.sia4010.test3_runtime_capability import (
            TEST3_VARIANTS,
        )

        for variant in TEST3_VARIANTS:
            case_id = variant[5:]
            with self.subTest(case=case_id):
                self.assertEqual("test_{}".format(case_id), variant)
                self.assertIn(
                    case_id[0], self.launcher._PROBE_BY_BASE_TEST
                )

    def test_every_hvac_exact_case_is_reachable(self) -> None:
        """Tests 4-7 accept exactly ("test_<case>", "<case>") pairs."""

        from swiss_sia.reference_model.sia4010 import (
            hvac_plant_runtime_capability,
        )

        for variant, case_id in hvac_plant_runtime_capability.EXACT_CASES:
            with self.subTest(case=case_id):
                self.assertEqual("test_{}".format(case_id), variant)
                self.assertIn(
                    case_id[0], self.launcher._PROBE_BY_BASE_TEST
                )

    def test_each_reachable_case_has_a_requiring_class(self) -> None:
        """Preparation rejects a variant its class does not require."""

        from swiss_sia.reference_model.sia4010 import (
            hvac_plant_runtime_capability,
        )
        from swiss_sia.reference_model.sia4010.test3_runtime_capability import (
            TEST3_VARIANTS,
        )

        variants = list(TEST3_VARIANTS) + [
            variant
            for variant, _ in hvac_plant_runtime_capability.EXACT_CASES
        ]
        for variant in variants:
            with self.subTest(variant=variant):
                class_id = self.launcher._resolve_target_class(variant)
                self.assertTrue(class_id)

    def test_resolved_class_really_requires_the_variant(self) -> None:
        from swiss_sia.config import SIA4010_CLASS_TEST_MATRIX

        class_id = self.launcher._resolve_target_class("test_3A")
        self.assertIn("test_3A", SIA4010_CLASS_TEST_MATRIX[class_id])

    def test_an_unrelated_class_is_refused(self) -> None:
        self.launcher.TARGET_CLASS = "1A"
        try:
            with self.assertRaises(RuntimeError):
                self.launcher._resolve_target_class("test_7")
        finally:
            self.launcher.TARGET_CLASS = ""

    def test_the_default_case_is_probe_consumable(self) -> None:
        case_id = str(self.launcher.CASE).strip().upper()
        self.assertIn(case_id[0], self.launcher._PROBE_BY_BASE_TEST)

    def test_the_probe_targets_exist_on_disk(self) -> None:
        for name in set(self.launcher._PROBE_BY_BASE_TEST.values()):
            with self.subTest(probe=name):
                self.assertTrue((ROOT / name).is_file())

    def test_the_launcher_never_requests_a_mutating_mode(self) -> None:
        """Only PREPARE_ONLY may appear: this launcher must not mutate VE."""

        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn('"PREPARE_ONLY"', source)
        for mode in (
            "CREATE_IN_ACTIVE_VE_PROJECT",
            "QUALIFY_IN_ACTIVE_VE_PROJECT",
        ):
            with self.subTest(mode=mode):
                self.assertNotIn(mode, source)

    def test_the_replacement_gate_exists_and_blocks(self) -> None:
        """Assert the guard, not the switch position.

        ``CASE`` and ``ALLOW_SCENARIO_REPLACEMENT`` are operator settings that
        the documented procedure tells the operator to edit. An earlier version
        of this test asserted the flag currently reads ``False``, which meant
        following the launcher's own instructions turned the suite red. What
        must hold is that the flag is consulted and that the false branch
        refuses instead of overwriting.
        """

        self.assertIsInstance(
            self.launcher.ALLOW_SCENARIO_REPLACEMENT, bool
        )
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("not ALLOW_SCENARIO_REPLACEMENT", source)
        self.assertIn("BLOCKED", source)

    def test_a_receipt_carrying_the_paths_is_used_verbatim(self) -> None:
        class Receipt:
            case_manifest_path = ROOT / "config" / "sia4010_all_classes.json"
            config_path = ROOT / "config" / "reference_model_config.json"
            asset_manifest_path = ROOT / "config" / "reference_model_assets.json"

        resolved = self.launcher._resolve_scenario_files(Receipt())
        self.assertEqual(
            resolved,
            [
                str(Receipt.case_manifest_path),
                str(Receipt.config_path),
                str(Receipt.asset_manifest_path),
            ],
        )

    def test_a_receipt_without_the_paths_falls_back_instead_of_emitting_empty(
        self,
    ) -> None:
        """Test3SourceBundleReceipt carries none of the three.

        Reading them with a default of "" would write a scenario naming no
        files, and the failure would surface much later as a missing manifest.
        """

        from swiss_sia.reference_model.sia4010.test3_source_bundle import (
            Test3SourceBundleReceipt,
        )

        for attribute, _filename in self.launcher._REPOSITORY_SCENARIO_FILES:
            with self.subTest(attribute=attribute):
                self.assertNotIn(
                    attribute, Test3SourceBundleReceipt.__dataclass_fields__
                )

        class Bare:
            pass

        resolved = self.launcher._resolve_scenario_files(Bare())
        self.assertEqual(len(resolved), 3)
        for path in resolved:
            self.assertTrue(Path(path).is_file(), path)
            self.assertNotEqual(path, "")

    def test_a_missing_scenario_input_stops_the_run(self) -> None:
        class Wrong:
            case_manifest_path = ROOT / "no_such_manifest.json"

        with self.assertRaises(RuntimeError):
            self.launcher._resolve_scenario_files(Wrong())


if __name__ == "__main__":
    unittest.main()
