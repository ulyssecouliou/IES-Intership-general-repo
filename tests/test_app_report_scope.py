"""Tests for report-scope resolution in app.main.

The client SIA 380/2-only report is the default; the full SIA 380/2 + SIA 4010
internal report is opt-in only. SIA 4010 validation classes qualify the
toolchain, not a client building, so they never appear unless explicitly asked.
"""

from __future__ import annotations

import os
import shutil
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from swiss_sia import app


class ResolveIncludeSia4010Tests(unittest.TestCase):
    """_resolve_include_sia4010 decides the report scope (client-only vs full)."""

    def _resolve(self, explicit, scope=None):
        """Resolve the scope with SIA_REPORT_SCOPE set to ``scope`` (or unset)."""
        env = {k: v for k, v in os.environ.items() if k != app.REPORT_SCOPE_ENV_VAR}
        if scope is not None:
            env[app.REPORT_SCOPE_ENV_VAR] = scope
        with mock.patch.dict(os.environ, env, clear=True):
            return app._resolve_include_sia4010(explicit)

    def test_explicit_true_forces_full_report_over_any_env(self):
        # The internal launcher passes True; it must win regardless of the env.
        self.assertTrue(self._resolve(True, scope="sia3802"))

    def test_explicit_false_forces_client_report_over_any_env(self):
        self.assertFalse(self._resolve(False, scope="full"))

    def test_default_is_the_client_380_2_only_report_when_env_is_unset(self):
        self.assertFalse(self._resolve(None))

    def test_internal_scope_tokens_select_the_full_report(self):
        for token in app._INTERNAL_FULL_SCOPE_TOKENS:
            self.assertTrue(self._resolve(None, scope=token), msg=token)

    def test_internal_scope_token_is_case_insensitive_and_stripped(self):
        self.assertTrue(self._resolve(None, scope="  BOTH  "))

    def test_unknown_or_client_scope_keeps_the_380_2_only_report(self):
        for token in ("", "sia3802", "client", "sia380", "garbage"):
            self.assertFalse(self._resolve(None, scope=token), msg=token)


class ModelViewerCaptureTests(unittest.TestCase):
    """The client UI can capture the active Mv2 view without manual files."""

    def test_documented_mv2_snapshot_is_saved_inside_the_project(self):
        project = (
            Path(__file__).resolve().parents[1]
            / ".codex_tmp"
            / "model_viewer_capture_api"
        )
        recorded = {}

        class FakeMv2:
            class mv2_viewmode:
                shaded = "SHADED"

            def take_snapshot(self, **options):
                recorded.update(options)
                output = Path(options["path"]) / (options["file_name"] + ".png")
                output.write_bytes(b"captured-model-viewer")

        try:
            with mock.patch.object(app, "iesve", SimpleNamespace(Mv2=FakeMv2)):
                output = app.capture_model_viewer_image(project)

            self.assertTrue(output.is_file())
            self.assertTrue(output.is_relative_to(project))
            self.assertEqual(recorded["view_mode"], "SHADED")
            self.assertFalse(recorded["components"])
        finally:
            shutil.rmtree(project, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
