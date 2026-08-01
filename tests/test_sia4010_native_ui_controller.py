"""Headless tests for the native VEScripts Model Builder controller."""

import hashlib
import json
import shutil
import unittest
from pathlib import Path
from unittest import mock

import tkinter as tk

from swiss_sia.reference_model.sia4010.model_scenario import FEATURE_IDS
from swiss_sia.reference_model.sia4010.native_ui import (
    ModelBuilderController,
    NativeModelBuilderWindow,
)


ROOT = Path(__file__).resolve().parents[1]


class _FakeScreen:
    """Stand-in for a Tk master exposing only the screen dimensions."""

    def __init__(self, width, height, raises=False):
        """Record the reported screen size, or force a Tk failure."""
        self._width = width
        self._height = height
        self._raises = raises

    def winfo_screenwidth(self):
        """Return the reported screen width."""
        if self._raises:
            raise tk.TclError("no display")
        return self._width

    def winfo_screenheight(self):
        """Return the reported screen height."""
        if self._raises:
            raise tk.TclError("no display")
        return self._height


class CompactLayoutTests(unittest.TestCase):
    """The compact layout is presentation-only and driven by the screen size."""

    def test_short_or_narrow_screens_are_compact(self):
        detect = NativeModelBuilderWindow._detect_compact
        self.assertTrue(detect(_FakeScreen(1366, 768)))
        self.assertTrue(detect(_FakeScreen(1024, 1200)))

    def test_large_screens_use_the_roomy_layout(self):
        self.assertFalse(NativeModelBuilderWindow._detect_compact(_FakeScreen(1920, 1080)))

    def test_unavailable_display_falls_back_to_the_roomy_layout(self):
        self.assertFalse(
            NativeModelBuilderWindow._detect_compact(_FakeScreen(0, 0, raises=True))
        )

    def test_scaled_picks_the_metric_for_the_active_layout(self):
        window = NativeModelBuilderWindow.__new__(NativeModelBuilderWindow)
        window.compact = False
        self.assertEqual(window._scaled(18, 11), 18)
        window.compact = True
        self.assertEqual(window._scaled(18, 11), 11)


class QualificationReportGateTests(unittest.TestCase):
    """Mutation buttons require one untampered, semantically valid receipt."""

    def setUp(self):
        self.root = ROOT / ".codex_tmp" / "ui_qualification_report_gate"
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir(parents=True)

    def tearDown(self):
        if self.root.exists():
            shutil.rmtree(self.root)

    def _report(self, payload):
        report = self.root / "qualification.json"
        report.write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
        checksum = hashlib.sha256(report.read_bytes()).hexdigest()
        report.with_suffix(".json.sha256").write_text(
            "{}  {}\n".format(checksum, report.name),
            encoding="utf-8",
        )
        return report

    def test_valid_checksum_and_required_guardrail_authorize_next_stage(self):
        report = self._report(
            {
                "status": "PASS",
                "dynamic_equivalence_qualified": False,
            }
        )
        self.assertTrue(
            NativeModelBuilderWindow._qualification_report_is_valid(
                (report,),
                required_false_field="dynamic_equivalence_qualified",
            )
        )

    def test_tampered_or_ambiguous_reports_fail_closed(self):
        report = self._report(
            {
                "status": "PASS",
                "fixed_closed_storage_qualified": True,
            }
        )
        report.write_text("{}\n", encoding="utf-8")
        validate = NativeModelBuilderWindow._qualification_report_is_valid
        self.assertFalse(
            validate(
                (report,),
                required_true_field="fixed_closed_storage_qualified",
            )
        )
        self.assertFalse(validate((report, report)))


class NativeModelBuilderControllerTests(unittest.TestCase):
    def setUp(self):
        self.controller = ModelBuilderController()

    def test_class_filters_variants(self):
        self.assertEqual(
            self.controller.variants_for_class("1A"),
            ("test_1", "test_2A"),
        )
        self.assertEqual(
            self.controller.variants_for_class("1B"),
            ("test_1", "test_2B", "test_2C", "test_2D"),
        )

    def test_official_payload_locks_case_features(self):
        payload = self.controller.build_payload(
            "SIA4010_1A_600FF",
            "SIA4010_OFFICIAL",
            "1A",
            "test_1",
            "600FF",
            "PREPARE_ONLY",
            "config/sia4010_classes_1a_1b.json",
            "reference_model_config.json",
            "reference_model_assets.json",
            custom_features={feature_id: True for feature_id in FEATURE_IDS},
        )
        self.assertFalse(payload["features"]["ideal_heating"])
        self.assertFalse(payload["features"]["ideal_cooling"])
        self.assertFalse(payload["features"]["solar_protection"])

    def test_custom_payload_is_forced_to_prepare_only(self):
        payload = self.controller.build_payload(
            "CUSTOM",
            "CUSTOM_REFERENCE",
            "1A",
            "test_1",
            "600",
            "CREATE_IN_ACTIVE_VE_PROJECT",
            "config/sia4010_classes_1a_1b.json",
            "reference_model_config.json",
            "reference_model_assets.json",
            custom_features={"geometry": True},
        )
        self.assertEqual(payload["execution"]["mode"], "PREPARE_ONLY")
        self.assertTrue(payload["features"]["geometry"])
        self.assertFalse(payload["features"]["weather"])

    def test_create_capability_is_not_inferred_from_framework_coverage(self):
        self.assertTrue(self.controller.mutation_supported("test_1", "600"))
        self.assertFalse(self.controller.mutation_supported("test_1", "600FF"))
        self.assertFalse(self.controller.mutation_supported("test_3L", "3L"))
        self.assertFalse(self.controller.mutation_supported("test_7", "7"))

    def test_runtime_qualification_is_separate_from_verified_creation(self):
        self.assertTrue(
            self.controller.runtime_qualification_supported("test_1", "640")
        )
        self.assertTrue(
            self.controller.runtime_qualification_supported(
                "test_1", "600FF"
            )
        )
        for case_id in ("900", "940", "900FF"):
            with self.subTest(case_id=case_id):
                self.assertTrue(
                    self.controller.runtime_qualification_supported(
                        "test_1", case_id
                    )
                )
        self.assertFalse(
            self.controller.runtime_qualification_supported("test_1", "600")
        )
        self.assertFalse(
            self.controller.runtime_qualification_supported("test_3L", "3L")
        )

    def test_ready_test2a_external_bindings_route_to_source_bundle_only(self):
        readiness = mock.Mock(ready_for_binding=True)
        expected = object()
        project = Path("C:/saved-project")
        repository = Path("C:/repository")
        with mock.patch(
            "swiss_sia.reference_model.sia4010.native_ui."
            "external_input_readiness",
            return_value=readiness,
        ), mock.patch(
            "swiss_sia.reference_model.sia4010.native_ui."
            "build_test2a_source_bound_bundle",
            return_value=expected,
        ) as builder:
            receipt = self.controller.prepare_case_bundle(
                project,
                repository,
                "SIA4010_OFFICIAL",
                "1A",
                "test_2A",
                "2A",
            )
        self.assertIs(receipt, expected)
        builder.assert_called_once_with(project, repository)

    def test_ready_test3_external_bindings_route_to_exact_source_bundle(self):
        readiness = mock.Mock(ready_for_binding=True)
        expected = object()
        project = Path("C:/saved-project")
        repository = Path("C:/repository")
        with mock.patch(
            "swiss_sia.reference_model.sia4010.native_ui."
            "external_input_readiness",
            return_value=readiness,
        ), mock.patch(
            "swiss_sia.reference_model.sia4010.native_ui."
            "build_test3_source_bound_bundle",
            return_value=expected,
        ) as builder:
            receipt = self.controller.prepare_case_bundle(
                project,
                repository,
                "SIA4010_OFFICIAL",
                "2B",
                "test_3J",
                "3J",
            )
        self.assertIs(receipt, expected)
        builder.assert_called_once_with(
            project, repository, "2B", "test_3J", "3J"
        )

    def test_unready_test3_sources_keep_generic_preparation_fallback(self):
        readiness = mock.Mock(ready_for_binding=False)
        expected = object()
        with mock.patch(
            "swiss_sia.reference_model.sia4010.native_ui."
            "external_input_readiness",
            return_value=readiness,
        ), mock.patch(
            "swiss_sia.reference_model.sia4010.native_ui.prepare_case",
            return_value=expected,
        ) as preparation:
            receipt = self.controller.prepare_case_bundle(
                Path("C:/saved-project"),
                Path("C:/repository"),
                "SIA4010_OFFICIAL",
                "2B",
                "test_3J",
                "3J",
            )
        self.assertIs(receipt, expected)
        preparation.assert_called_once()

    def test_aps_evaluation_uses_only_qualified_result_variables(self):
        self.assertTrue(
            self.controller.aps_evaluation_supported("test_1", "1E")
        )
        self.assertTrue(
            self.controller.aps_evaluation_supported("test_2D", "2D")
        )
        self.assertTrue(
            self.controller.aps_evaluation_supported("test_1", "600")
        )
        self.assertTrue(
            self.controller.aps_evaluation_supported("test_1", "600FF")
        )
        self.assertFalse(
            self.controller.aps_evaluation_supported("test_3A", "3A")
        )

    def test_apachesim_qualification_is_exposed_only_for_generated_test1_cases(self):
        for case_id in ("600", "640", "600FF", "900", "940", "900FF"):
            with self.subTest(case_id=case_id):
                self.assertTrue(
                    self.controller.apachesim_qualification_supported(
                        "test_1", case_id
                    )
                )
        self.assertFalse(
            self.controller.apachesim_qualification_supported(
                "test_1", "1E"
            )
        )
        self.assertFalse(
            self.controller.apachesim_qualification_supported(
                "test_2A", "2A"
            )
        )

    def test_evidence_navigator_rebuild_uses_the_central_ledger(self):
        root = Path("C:/repository")
        expected = {"summary": {"validation_classes": 8}}
        with mock.patch.object(Path, "is_file", return_value=True), mock.patch(
            "swiss_sia.reference_model.sia4010.native_ui."
            "build_all_class_navigators",
            return_value=expected,
        ) as builder:
            actual = self.controller.rebuild_evidence_navigator(root)
        self.assertIs(actual, expected)
        builder.assert_called_once_with(
            root
            / "sia4010_evidence"
            / "autonomy"
            / "sia4010_case_evidence.json",
            root / "SIA_4010_geteilter_Link",
            root / "sia4010_evidence" / "autonomy" / "navigator",
        )

    def test_evidence_navigator_rebuild_fails_without_ledger(self):
        with mock.patch.object(Path, "is_file", return_value=False):
            with self.assertRaisesRegex(
                FileNotFoundError, "evidence ledger does not exist"
            ):
                self.controller.rebuild_evidence_navigator(
                    Path("C:/repository")
                )

    def test_external_input_manifest_is_created_once_and_never_overwritten(self):
        project = ROOT / ".codex_tmp" / "ui_external_input_manifest"
        if project.exists():
            shutil.rmtree(project)
        project.mkdir(parents=True)
        try:
            path, created = self.controller.ensure_external_input_manifest(
                project, ROOT
            )
            self.assertTrue(created)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "1.0")
            template_files = sorted(
                (
                    project / "sia4010_external_input_templates"
                ).glob("*.json")
            )
            self.assertEqual(len(template_files), 6)
            payload["operator_note"] = "preserve me"
            path.write_text(
                json.dumps(payload, indent=2) + "\n",
                encoding="utf-8",
            )

            same_path, created_again = (
                self.controller.ensure_external_input_manifest(project, ROOT)
            )
            self.assertEqual(same_path, path)
            self.assertFalse(created_again)
            preserved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(preserved["operator_note"], "preserve me")
        finally:
            if project.exists():
                shutil.rmtree(project)


if __name__ == "__main__":
    unittest.main()
