"""Regression tests for the SIA 380/2 compliance-score weighting.

These guard against two prior defects: the compliance-score weight table
drifting away from the categories the SIA 380/2 checker actually emits, and a
SIA 4010 ("simulation") term leaking into the SIA 380/2 compliance score.
"""

import unittest

from swiss_sia.config import CATEGORY_WEIGHTS
from swiss_sia.health_score import HealthScoreCalculator

SCORED_CATEGORIES = {"envelope", "openings", "ventilation", "gains", "hvac"}


class ComplianceScoreWeightingTests(unittest.TestCase):
    def test_weight_keys_match_scored_sia3802_categories(self):
        """The weight table must cover exactly the emitted SIA 380/2 categories."""

        self.assertEqual(set(CATEGORY_WEIGHTS), SCORED_CATEGORIES)
        self.assertNotIn("simulation", CATEGORY_WEIGHTS)
        self.assertNotIn("energy", CATEGORY_WEIGHTS)

    def test_gains_category_contributes_to_compliance_score(self):
        """A failing internal-gains domain must lower the compliance score."""

        def score(gains_value):
            results = {category: {"score": 100.0} for category in SCORED_CATEGORIES}
            results["gains"] = {"score": gains_value}
            return HealthScoreCalculator()._calculate_sia3802_score(results)

        self.assertGreater(score(100.0), score(0.0))

    def test_full_pass_normalizes_to_one_hundred(self):
        """All-category pass must normalize to 100 over the weight sum."""

        results = {category: {"score": 100.0} for category in SCORED_CATEGORIES}
        self.assertAlmostEqual(
            HealthScoreCalculator()._calculate_sia3802_score(results), 100.0
        )


if __name__ == "__main__":
    unittest.main()
