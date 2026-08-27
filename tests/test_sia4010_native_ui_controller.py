"""Headless tests for the native VEScripts Model Builder controller."""

import hashlib
import json
import shutil
import unittest
from pathlib import Path
from unittest import mock

import tkinter as tk

from swiss_sia.reference_model.sia4010.model_scenario import FEATURE_IDS
from swiss_sia.reference_model.sia4010.external_input_manifest import (
    external_input_readiness,
)
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
        self.assertFalse(
            NativeModelBuilderWindow._detect_compact(_FakeScreen(1920, 1080))
        )

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

    def test_test1_bundle_bootstraps_verified_repository_weather(self):
        """Copy controlled DRYCOLD inputs before Test 1 preflight."""

        project = ROOT / ".codex_tmp" / "ui_test1_weather_bootstrap"
        if project.exists():
            shutil.rmtree(project)
        project.mkdir(parents=True)
        try:
            receipt = self.controller.prepare_case_bundle(
                project,
                ROOT,
                "SIA4010_OFFICIAL",
                "1A",
                "test_1",
                "600",
            )
            weather = project / "DRYCOLD_IESVE.epw"
            verification = project / "DRYCOLD_IESVE_EPW_DERIVATION.json"
            self.assertTrue(weather.is_file())
            self.assertTrue(verification.is_file())
            self.assertEqual(receipt.weather_file, weather.resolve())
            audit = json.loads(receipt.audit_path.read_text(encoding="utf-8"))
            self.assertNotIn(
                "denver_drycold_weather_file",
                audit["evidence_summary"]["unresolved"],
            )
        finally:
            shutil.rmtree(project, ignore_errors=True)

    def test_test1_weather_migrates_only_audited_managed_transport(self):
        project = ROOT / ".codex_tmp" / "ui_test1_weather_migration"
        repository = project / "repository"
        source = repository / "references" / "standards" / "bestest"
        source.mkdir(parents=True, exist_ok=True)
        try:
            tmy = source / "DRYCOLD.TMY"
            tmy.write_text("controlled tmy", encoding="ascii")
            legacy_tmy_checksum = hashlib.sha256(
                b"controlled tmy with legacy line endings"
            ).hexdigest()
            (source / "DRYCOLD_TMY_ISO_SOURCE_VERIFICATION.json").write_text(
                json.dumps({"weather": {"sha256": legacy_tmy_checksum}}),
                encoding="utf-8",
            )
            new_weather = source / "DRYCOLD_IESVE.epw"
            new_weather.write_text("new sky boundary", encoding="ascii")
            new_audit = source / "DRYCOLD_IESVE_EPW_DERIVATION.json"
            new_audit.write_text("{}\n", encoding="utf-8")

            old_weather = project / "DRYCOLD_IESVE.epw"
            old_weather.write_text("old generated transport", encoding="ascii")
            old_audit = project / "DRYCOLD_IESVE_EPW_DERIVATION.json"
            old_audit.write_text(
                json.dumps(
                    {
                        "status": "PASS",
                        "weather": {
                            "format": "EPW",
                            "sha256": hashlib.sha256(
                                old_weather.read_bytes()
                            ).hexdigest(),
                        },
                        "source_tmy1": {
                            "format": "NOAA_TMY1_FIXED_WIDTH",
                            "sha256": legacy_tmy_checksum,
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = self.controller.ensure_test1_weather(project, repository)
            self.assertEqual(result, old_weather)
            self.assertEqual(
                old_weather.read_text(encoding="ascii"),
                "new sky boundary",
            )
            self.assertEqual(
                (project / "DRYCOLD_IESVE.pre_iso_sky_boundary.epw.bak").read_text(
                    encoding="ascii"
                ),
                "old generated transport",
            )
        finally:
            shutil.rmtree(project, ignore_errors=True)

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
        self.assertTrue(self.controller.runtime_qualification_supported("test_1", "640"))
        self.assertTrue(
            self.controller.runtime_qualification_supported("test_1", "600FF")
        )
        for case_id in ("900", "940", "900FF"):
            with self.subTest(case_id=case_id):
                self.assertTrue(
                    self.controller.runtime_qualification_supported("test_1", case_id)
                )
        self.assertFalse(self.controller.runtime_qualification_supported("test_1", "600"))
        self.assertFalse(self.controller.runtime_qualification_supported("test_3L", "3L"))

    def test_ready_test2a_external_bindings_route_to_source_bundle_only(self):
        readiness = mock.Mock(ready_for_binding=True)
        expected = object()
        project = Path("C:/saved-project")
        repository = Path("C:/repository")
        with (
            mock.patch(
                "swiss_sia.reference_model.sia4010.native_ui." "external_input_readiness",
                return_value=readiness,
            ),
            mock.patch(
                "swiss_sia.reference_model.sia4010.native_ui."
                "build_test2a_source_bound_bundle",
                return_value=expected,
            ) as builder,
        ):
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
        with (
            mock.patch(
                "swiss_sia.reference_model.sia4010.native_ui." "external_input_readiness",
                return_value=readiness,
            ),
            mock.patch(
                "swiss_sia.reference_model.sia4010.native_ui."
                "build_test3_source_bound_bundle",
                return_value=expected,
            ) as builder,
        ):
            receipt = self.controller.prepare_case_bundle(
                project,
                repository,
                "SIA4010_OFFICIAL",
                "2B",
                "test_3J",
                "3J",
            )
        self.assertIs(receipt, expected)
        builder.assert_called_once_with(project, repository, "2B", "test_3J", "3J")

    def test_unready_test3_sources_keep_generic_preparation_fallback(self):
        readiness = mock.Mock(ready_for_binding=False)
        expected = object()
        with (
            mock.patch(
                "swiss_sia.reference_model.sia4010.native_ui." "external_input_readiness",
                return_value=readiness,
            ),
            mock.patch(
                "swiss_sia.reference_model.sia4010.native_ui.prepare_case",
                return_value=expected,
            ) as preparation,
        ):
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
        self.assertTrue(self.controller.aps_evaluation_supported("test_1", "1E"))
        self.assertTrue(self.controller.aps_evaluation_supported("test_2D", "2D"))
        self.assertTrue(self.controller.aps_evaluation_supported("test_1", "600"))
        self.assertTrue(self.controller.aps_evaluation_supported("test_1", "600FF"))
        self.assertFalse(self.controller.aps_evaluation_supported("test_3A", "3A"))

    def test_apachesim_qualification_is_exposed_only_for_generated_test1_cases(self):
        for case_id in ("600", "640", "600FF", "900", "940", "900FF"):
            with self.subTest(case_id=case_id):
                self.assertTrue(
                    self.controller.apachesim_qualification_supported("test_1", case_id)
                )
        self.assertFalse(
            self.controller.apachesim_qualification_supported("test_1", "1E")
        )
        self.assertFalse(
            self.controller.apachesim_qualification_supported("test_2A", "2A")
        )

    def test_evidence_navigator_rebuild_uses_the_central_ledger(self):
        root = Path("C:/repository")
        expected = {"summary": {"validation_classes": 8}}
        with (
            mock.patch.object(Path, "is_file", return_value=True),
            mock.patch(
                "swiss_sia.reference_model.sia4010.native_ui."
                "build_all_class_navigators",
                return_value=expected,
            ) as builder,
        ):
            actual = self.controller.rebuild_evidence_navigator(root)
        self.assertIs(actual, expected)
        builder.assert_called_once_with(
            root / "sia4010_evidence" / "autonomy" / "sia4010_case_evidence.json",
            root / "SIA_4010_geteilter_Link",
            root / "sia4010_evidence" / "autonomy" / "navigator",
        )

    def test_evidence_navigator_rebuild_fails_without_ledger(self):
        with mock.patch.object(Path, "is_file", return_value=False):
            with self.assertRaisesRegex(
                FileNotFoundError, "evidence ledger does not exist"
            ):
                self.controller.rebuild_evidence_navigator(Path("C:/repository"))

    def test_prepared_manifest_is_opt_in_and_declares_whose_decisions(self):
        """The prepared manifest carries human decisions.

        It must therefore never be the default: a new project would inherit
        authorizations that no one in that project has made. This action is
        the explicit alternative, and it must make visible what it installs.
        """

        project = ROOT / ".codex_tmp" / "ui_prepared_manifest"
        if project.exists():
            shutil.rmtree(project)
        project.mkdir(parents=True)
        try:
            controller = self.controller
            (
                path,
                installed,
                authorizations,
            ) = controller.install_prepared_external_input_manifest(project, ROOT)
            self.assertTrue(installed)
            self.assertEqual(path.name, "sia4010_external_inputs.json")
            ids = sorted(item["input_id"] for item in authorizations)
            self.assertEqual(
                ids,
                [
                    "iso52016_2017_chapter7_test_cell",
                    "sia2024_office_3_1_standard_profiles",
                    "sia2028_dry_normal_zurich_kloten",
                    "sia_example_building_fabric_awning_detail",
                    "test6_stage_control_trace",
                    "test7_heat_pump_performance_tables",
                ],
            )
            # Each displayed basis comes from `license_reference`, the field the
            # strict reader rejects when empty. An empty basis here would mean
            # displaying a field that nothing guarantees.
            for item in authorizations:
                with self.subTest(input_id=item["input_id"]):
                    self.assertTrue(item["basis"])

            # Installing a repository-owned prepared manifest into a project
            # must not change the base directory of its evidence paths.
            readiness = external_input_readiness(project, "test_2A", "2A")
            self.assertEqual(readiness.status, "READY_FOR_BINDING")
            self.assertTrue(readiness.ready_for_binding)
            for evidence in readiness.evidence:
                with self.subTest(input_id=evidence.input_id):
                    self.assertTrue(Path(evidence.source_path).is_absolute())
                    self.assertTrue(Path(evidence.validation_report_path).is_absolute())

            # Never overwrite: a local authorization or edit does not belong to us.
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["operator_note"] = "preserve me"
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            _same, again, _auth = controller.install_prepared_external_input_manifest(
                project, ROOT
            )
            self.assertFalse(again)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8"))["operator_note"],
                "preserve me",
            )
        finally:
            if project.exists():
                shutil.rmtree(project)

    def test_prepared_manifest_install_refuses_a_missing_project(self):
        """Writing a proof contract outside a saved project makes no sense."""

        with self.assertRaises(FileNotFoundError):
            self.controller.install_prepared_external_input_manifest(
                ROOT / ".codex_tmp" / "does_not_exist_at_all", ROOT
            )

    def test_explicit_prepared_install_upgrades_only_pristine_empty_manifest(self):
        """An untouched empty template carries no local decision to lose."""

        project = ROOT / ".codex_tmp" / "ui_upgrade_empty_manifest"
        if project.exists():
            shutil.rmtree(project)
        project.mkdir(parents=True)
        try:
            empty_path, created = self.controller.ensure_external_input_manifest(
                project, ROOT
            )
            self.assertTrue(created)
            self.assertEqual(
                empty_path.read_bytes(),
                (ROOT / "config" / "sia4010_external_inputs.example.json").read_bytes(),
            )

            path, installed, authorizations = (
                self.controller.install_prepared_external_input_manifest(project, ROOT)
            )
            self.assertTrue(installed)
            self.assertEqual(path, empty_path)
            self.assertTrue(authorizations)
            readiness = external_input_readiness(project, "test_4", "4")
            self.assertIn("sia2028_dry_normal_zurich_kloten", readiness.ready_input_ids)
            self.assertIn(
                "sia2024_auditorium_target_profiles", readiness.blocked_input_ids
            )
            self.assertIn("test4_fan_curve_digitization", readiness.blocked_input_ids)
        finally:
            if project.exists():
                shutil.rmtree(project)

    def test_prepared_install_preserves_null_paths_and_repairs_old_none_sentinel(self):
        project = ROOT / ".codex_tmp" / "ui_prepared_null_paths"
        if project.exists():
            shutil.rmtree(project)
        project.mkdir(parents=True)
        try:
            path, installed, _authorizations = (
                self.controller.install_prepared_external_input_manifest(project, ROOT)
            )
            self.assertTrue(installed)
            payload = json.loads(path.read_text(encoding="utf-8"))
            record = payload["inputs"]["sia_authority_test7_pv_precedence"]
            self.assertIsNone(record["source_path"])
            self.assertIsNone(record["technical_validation"]["report_path"])

            sentinel = str((ROOT / "config" / "None").resolve())
            record["source_path"] = sentinel
            record["technical_validation"]["report_path"] = sentinel
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            _path, installed_again, _authorizations = (
                self.controller.install_prepared_external_input_manifest(project, ROOT)
            )
            self.assertFalse(installed_again)
            repaired = json.loads(path.read_text(encoding="utf-8"))["inputs"]
            repaired = repaired["sia_authority_test7_pv_precedence"]
            self.assertIsNone(repaired["source_path"])
            self.assertIsNone(repaired["technical_validation"]["report_path"])
        finally:
            if project.exists():
                shutil.rmtree(project)

    def test_prepared_install_refreshes_only_a_stale_validation_report_checksum(self):
        project = ROOT / ".codex_tmp" / "ui_prepared_checksum_refresh"
        if project.exists():
            shutil.rmtree(project)
        project.mkdir(parents=True)
        try:
            path, installed, _authorizations = (
                self.controller.install_prepared_external_input_manifest(project, ROOT)
            )
            self.assertTrue(installed)
            payload = json.loads(path.read_text(encoding="utf-8"))
            record = payload["inputs"]["sia2024_office_3_1_standard_profiles"]
            expected = record["technical_validation"]["report_sha256"]
            record["technical_validation"]["report_sha256"] = "0" * 64
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            _path, refreshed, _authorizations = (
                self.controller.install_prepared_external_input_manifest(project, ROOT)
            )

            self.assertTrue(refreshed)
            repaired = json.loads(path.read_text(encoding="utf-8"))
            repaired = repaired["inputs"]["sia2024_office_3_1_standard_profiles"]
            self.assertEqual(repaired["technical_validation"]["report_sha256"], expected)
        finally:
            if project.exists():
                shutil.rmtree(project)

    def test_external_input_manifest_is_created_once_and_never_overwritten(self):
        project = ROOT / ".codex_tmp" / "ui_external_input_manifest"
        if project.exists():
            shutil.rmtree(project)
        project.mkdir(parents=True)
        try:
            path, created = self.controller.ensure_external_input_manifest(project, ROOT)
            self.assertTrue(created)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "1.0")
            template_files = sorted(
                (project / "sia4010_external_input_templates").glob("*.json")
            )
            self.assertEqual(len(template_files), 6)
            payload["operator_note"] = "preserve me"
            path.write_text(
                json.dumps(payload, indent=2) + "\n",
                encoding="utf-8",
            )

            same_path, created_again = self.controller.ensure_external_input_manifest(
                project, ROOT
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
