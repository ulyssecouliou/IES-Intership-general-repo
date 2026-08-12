"""Tests for the pure Swiss Compliance Hub registry and capability summary."""

from __future__ import annotations

import unittest
from pathlib import Path

from swiss_sia.compliance_hub import (
    ACTIONS,
    action_map,
    build_capability_summary,
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
        self.assertFalse(is_disposable_project(r"C:\Models\CLIENT_PROJECT"))

    def test_current_sia4010_summary_does_not_overclaim(self) -> None:
        """The UI status must match the explicit case capability registry."""
        summary = build_capability_summary(all_case_capabilities())
        # 34 depuis l'enregistrement des cas diagnostiques 1A a 1D du
        # Test 1 : 1E existait sans la base que sa definition exige.
        self.assertEqual(summary["exact_cases"], 34)
        self.assertEqual(summary["guarded_mutation_cases"], 1)
        self.assertEqual(summary["runtime_qualification_cases"], 5)
        # 28 : aucun generateur VE ne lie encore les quatre cas
        # diagnostiques du Test 1, donc ils comptent comme non implementes.
        self.assertEqual(summary["not_implemented_cases"], 28)

    def test_hub_geometry_is_centred_and_kept_on_screen(self) -> None:
        """Small displays must not place the hub outside the visible desktop."""

        self.assertEqual(_centred_geometry(940, 680, 1920, 1080), "940x680+490+200")
        self.assertEqual(_centred_geometry(940, 680, 800, 600), "720x500+40+50")


if __name__ == "__main__":
    unittest.main()
