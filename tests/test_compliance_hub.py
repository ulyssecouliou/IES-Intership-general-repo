"""Tests for the pure Swiss Compliance Hub registry and capability summary."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from swiss_sia.compliance_hub import (
    ACTIONS,
    action_map,
    build_capability_summary,
    build_project_snapshot,
    is_disposable_project,
)
from swiss_sia.compliance_hub_ui import _centred_geometry
from swiss_sia.reference_model.sia4010.case_registry import all_case_capabilities


class ComplianceHubTests(unittest.TestCase):
    """Verify truthful workflow registration without invoking Tk or VE."""

    def test_every_registered_launcher_exists(self) -> None:
        """The hub must never advertise a missing Run-button workflow."""
        repository = Path(__file__).resolve().parents[1]
        for action in ACTIONS:
            self.assertTrue((repository / action.launcher).is_file(), action.launcher)

    def test_mutating_actions_require_disposable_projects(self) -> None:
        """Every VE mutation entry must be protected by the disposable guard."""
        for action in ACTIONS:
            if action.mutates_ve:
                self.assertTrue(action.requires_disposable_project)
        self.assertFalse(action_map()["client_audit"].mutates_ve)

    def test_disposable_project_names_are_explicit(self) -> None:
        """Ordinary client paths must not satisfy the mutation guard."""
        self.assertTrue(is_disposable_project(r"C:\Models\CLIENT_TEST"))
        self.assertTrue(is_disposable_project(r"C:\Models\SIA4010_DISPOSABLE_01"))
        self.assertTrue(is_disposable_project(r"C:\Models\SIA4010_TEST1_600FF"))
        self.assertTrue(is_disposable_project(r"C:\Models\Test_640_Test1"))
        self.assertFalse(is_disposable_project(r"C:\Models\CLIENT_PROJECT"))

    def test_current_sia4010_summary_does_not_overclaim(self) -> None:
        """The UI status must match the explicit case capability registry."""
        summary = build_capability_summary(all_case_capabilities())
        # 34 since the registration of diagnostic cases 1A through 1D of
        # Test 1: 1E existed without the base its definition requires.
        self.assertEqual(summary["exact_cases"], 34)
        self.assertEqual(summary["guarded_mutation_cases"], 1)
        # 5 -> 9 on 2026-08-13: the four diagnostic cases 1A through 1D of
        # Test 1 go through the same qualification in a disposable project.
        self.assertEqual(summary["runtime_qualification_cases"], 9)
        # 28 -> 24: the four diagnostic cases have had a generator since
        # 2026-08-13. This counter is what the UI shows the client, and
        # it must neither over- nor under-count: 24 cases remain blocked,
        # all by a VE binding we have not written.
        self.assertEqual(summary["not_implemented_cases"], 24)

    def test_hub_geometry_is_centred_and_kept_on_screen(self) -> None:
        """Small displays must not place the hub outside the visible desktop."""

        self.assertEqual(_centred_geometry(940, 680, 1920, 1080), "940x680+490+200")
        self.assertEqual(_centred_geometry(940, 680, 800, 600), "720x500+40+50")

    def test_snapshot_reports_client_audit_without_inventing_a_verdict(self) -> None:
        """The client tile must expose warnings and recommend evidence review."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "CLIENT_TEST"
            diagnostics = root / "sia_compliance_artifacts" / "diagnostics"
            diagnostics.mkdir(parents=True)
            (root / "client.mdl").write_bytes(b"model")
            (diagnostics / "swiss_sia_remediation_probe_20260814.json").write_text(
                json.dumps({"status": "WARNING", "room_count": 4}),
                encoding="utf-8",
            )

            snapshot = build_project_snapshot(str(root))

        self.assertEqual(snapshot.project_kind, "Disposable validation project")
        self.assertEqual(snapshot.client_audit_status, "WARNING")
        self.assertEqual(snapshot.template_remediation_status, "NOT RUN")
        self.assertEqual(snapshot.result_status, "NOT RUN")
        self.assertIn("complete evidence", snapshot.recommended_action)

    def test_snapshot_distinguishes_recorded_results_from_acceptance(self) -> None:
        """A criterion-free APS evaluation is displayed verbatim, never as PASS."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "SIA4010_TEST1_600FF"
            results = root / "sia4010_artifacts" / "results"
            vista = root / "Vista"
            results.mkdir(parents=True)
            vista.mkdir()
            (root / "case.mdl").write_bytes(b"model")
            (vista / "case.aps").write_bytes(b"aps")
            (root / "sia_model_scenario.json").write_text(
                json.dumps({"selection": {"variant": "test_1", "case_id": "600FF"}}),
                encoding="utf-8",
            )
            (results / "case_evaluation.json").write_text(
                json.dumps(
                    {
                        "status": "REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION",
                        "required_output_scope_complete": True,
                    }
                ),
                encoding="utf-8",
            )

            snapshot = build_project_snapshot(str(root))

        self.assertEqual(snapshot.scenario, "test_1/600FF")
        self.assertEqual(snapshot.aps_files, 1)
        self.assertEqual(
            snapshot.result_status,
            "REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION",
        )
        self.assertTrue(snapshot.result_scope_complete)

    def test_snapshot_requires_audit_after_verified_template_remediation(self) -> None:
        """A write receipt never replaces the required post-mutation audit."""

        root = Path("C:/Models/CLIENT_TEST")
        # Exercise the artifact ordering contract through isolated method mocks;
        # no filesystem is required for this status rule.
        import swiss_sia.compliance_hub as module

        audit_path = type(
            "Artifact", (), {"stat": lambda self: type("S", (), {"st_mtime": 1})()}
        )()
        receipt_path = type(
            "Artifact", (), {"stat": lambda self: type("S", (), {"st_mtime": 2})()}
        )()
        paths = iter([audit_path, receipt_path, None])
        payloads = iter(
            [
                {"status": "WARNING"},
                {"status": "APPLIED_AND_READBACK_VERIFIED"},
                {},
                {},
                {},
            ]
        )
        with (
            patch.object(module, "_latest_file", side_effect=lambda *_args: next(paths)),
            patch.object(module, "_read_json", side_effect=lambda _path: next(payloads)),
            patch.object(Path, "glob", return_value=[]),
        ):
            snapshot = build_project_snapshot(str(root))

        self.assertIn("Rerun the post-remediation", snapshot.recommended_action)


if __name__ == "__main__":
    unittest.main()
