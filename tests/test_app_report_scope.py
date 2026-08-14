"""Tests for the client SIA 380/2-only report-scope resolution in app.main."""

from __future__ import annotations

import os
import unittest
from unittest import mock

from swiss_sia import app


class ResolveIncludeSia4010Tests(unittest.TestCase):
    """_resolve_include_sia4010 decides the report scope (full vs client-only)."""

    def _resolve(self, explicit, scope=None):
        """Resolve the scope with SIA_REPORT_SCOPE set to ``scope`` (or unset)."""
        env = {k: v for k, v in os.environ.items() if k != app.REPORT_SCOPE_ENV_VAR}
        if scope is not None:
            env[app.REPORT_SCOPE_ENV_VAR] = scope
        with mock.patch.dict(os.environ, env, clear=True):
            return app._resolve_include_sia4010(explicit)

    def test_explicit_true_forces_full_report_over_any_env(self):
        self.assertTrue(self._resolve(True, scope="sia3802"))

    def test_explicit_false_forces_client_report_over_any_env(self):
        # The dedicated launcher passes False; it must win regardless of the env.
        self.assertFalse(self._resolve(False, scope="full"))

    def test_default_is_the_full_report_when_env_is_unset(self):
        self.assertTrue(self._resolve(None))

    def test_client_scope_tokens_select_the_380_2_only_report(self):
        for token in app._CLIENT_ONLY_SCOPE_TOKENS:
            self.assertFalse(self._resolve(None, scope=token), msg=token)

    def test_scope_token_is_case_insensitive_and_stripped(self):
        self.assertFalse(self._resolve(None, scope="  SIA3802  "))

    def test_unknown_scope_keeps_the_full_report(self):
        for token in ("", "full", "sia380_2_and_4010", "garbage"):
            self.assertTrue(self._resolve(None, scope=token), msg=token)


if __name__ == "__main__":
    unittest.main()
