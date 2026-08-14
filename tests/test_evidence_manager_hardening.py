"""Defensive-robustness tests for the evidence-payload lookup helpers.

These helpers receive dynamic evidence payloads (for example
``external_mappings`` supplied to the checker, or ``sia3802_results`` result
dicts). A malformed payload must degrade to the existing "no accepted record"
state (``None``) instead of raising, and must never invent an acceptance.
"""

from __future__ import annotations

import unittest

from swiss_sia.evidence_manager import (
    find_accepted_global_comparison,
    find_accepted_mapping,
    find_accepted_project_metadata,
)


class FindAcceptedProjectMetadataHardeningTests(unittest.TestCase):
    """Guard project-metadata lookups against malformed result payloads."""

    def test_success_returns_matching_record(self) -> None:
        """A well-formed payload still returns the matching accepted record."""
        results = {"accepted_records": [{"project_id": "Demo_Project"}]}
        record = find_accepted_project_metadata(results, "Demo_Project")
        self.assertEqual(record, {"project_id": "Demo_Project"})

    def test_invalid_payload_is_not_a_dict(self) -> None:
        """A non-dict payload degrades to None instead of raising."""
        self.assertIsNone(find_accepted_project_metadata([1, 2], "Demo_Project"))

    def test_fallback_accepted_records_not_a_list(self) -> None:
        """A non-list ``accepted_records`` degrades to None instead of raising."""
        self.assertIsNone(
            find_accepted_project_metadata({"accepted_records": 5}, "Demo_Project")
        )


class FindAcceptedGlobalComparisonHardeningTests(unittest.TestCase):
    """Guard global-comparison lookups against malformed result payloads."""

    def test_success_returns_matching_record(self) -> None:
        """A well-formed payload still returns the matching accepted record."""
        results = {"accepted_records": [{"project_id": "Demo_Project"}]}
        record = find_accepted_global_comparison(results, "Demo_Project")
        self.assertEqual(record, {"project_id": "Demo_Project"})

    def test_invalid_payload_is_not_a_dict(self) -> None:
        """A non-dict payload degrades to None instead of raising."""
        self.assertIsNone(find_accepted_global_comparison([1], "Demo_Project"))

    def test_fallback_accepted_records_not_a_list(self) -> None:
        """A non-list ``accepted_records`` degrades to None instead of raising."""
        self.assertIsNone(
            find_accepted_global_comparison({"accepted_records": 5}, "Demo_Project")
        )


class FindAcceptedMappingHardeningTests(unittest.TestCase):
    """Guard external-standard mapping lookups against malformed payloads."""

    def test_success_returns_matching_record(self) -> None:
        """A well-formed payload still returns the matching accepted record."""
        results = {
            "accepted_records": [{"room_id": "R1", "sia2024_category": "office"}]
        }
        record = find_accepted_mapping(results, room_id="R1")
        self.assertEqual(record, {"room_id": "R1", "sia2024_category": "office"})

    def test_invalid_payload_is_not_a_dict(self) -> None:
        """A non-dict payload degrades to None instead of raising."""
        self.assertIsNone(find_accepted_mapping([1], room_id="R1"))

    def test_fallback_accepted_records_not_a_list(self) -> None:
        """A non-list ``accepted_records`` degrades to None instead of raising."""
        self.assertIsNone(
            find_accepted_mapping({"accepted_records": 5}, room_id="R1")
        )


if __name__ == "__main__":
    unittest.main()
