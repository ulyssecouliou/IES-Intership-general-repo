"""Regression tests for the persistent IESVE Python interpreter bootstrap."""

from pathlib import Path
import subprocess
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class VEReloadBootstrapTests(unittest.TestCase):
    """Ensure repeated VE Run clicks reload providers before consumers."""

    def test_app_reload_restores_stale_provider_apis(self):
        """Reload app successfully when VE cached older provider modules."""
        script = """
import importlib
import inspect
import swiss_sia.app as app
import swiss_sia.evidence_manager as evidence_manager
import swiss_sia.evidence_pack as evidence_pack
import swiss_sia.sia380_checker as sia380_checker

del evidence_pack.matches_active_project_scope

def stale_usage_mapping_api(project_root, evidence_dir_name="sia4010_evidence"):
    return {}

evidence_manager.scan_sia2024_usage_mappings = stale_usage_mapping_api
sia380_checker.scan_sia2024_usage_mappings = stale_usage_mapping_api
importlib.reload(app)

assert hasattr(evidence_pack, "matches_active_project_scope")
assert len(inspect.signature(evidence_manager.scan_sia2024_usage_mappings).parameters) == 3
assert (
    sia380_checker.scan_sia2024_usage_mappings
    is evidence_manager.scan_sia2024_usage_mappings
)
assert app.SIA4010Checker.__module__ == "swiss_sia.sia4010_checker"
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
