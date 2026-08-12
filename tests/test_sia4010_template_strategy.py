"""Tests for the fail-closed SIA 4010 hybrid execution strategy."""

import unittest
from pathlib import Path
from unittest.mock import patch

from swiss_sia.reference_model.sia4010.template_strategy import (
    TemplateBinding,
    TemplateRequirement,
    TemplateValidation,
    build_hybrid_case_plans,
    load_requirements,
)


ROOT = Path(__file__).resolve().parents[1]


class Sia4010TemplateStrategyTests(unittest.TestCase):
    def setUp(self):
        self.requirements = load_requirements(
            ROOT / "config" / "sia4010_template_requirements.json"
        )

    def test_requirements_cover_all_base_tests(self):
        self.assertEqual(set(self.requirements), set("1234567"))
        self.assertFalse(self.requirements["1"].template_allowed)
        self.assertEqual(
            self.requirements["7"].strategy,
            "QUALIFIED_VE_TEMPLATE_REQUIRED",
        )

    def test_direct_test1_cases_do_not_require_templates(self):
        plans = build_hybrid_case_plans(self.requirements, ())
        by_case = {(item.variant, item.case_id): item for item in plans}
        self.assertEqual(
            by_case[("test_1", "600")].status,
            "READY_FOR_GUARDED_MUTATION",
        )
        for case_id in ("640", "600FF", "900", "940", "900FF"):
            self.assertEqual(
                by_case[("test_1", case_id)].status,
                "READY_FOR_REAL_VE_QUALIFICATION",
            )
        self.assertEqual(
            by_case[("test_1", "1E")].status,
            "SOURCE_PREPARATION_ONLY",
        )

    def test_unbound_complex_cases_are_blocked(self):
        plans = build_hybrid_case_plans(self.requirements, ())
        blocked = [item for item in plans if item.status == "BLOCKED_TEMPLATE_REQUIRED"]
        self.assertEqual(len(blocked), 23)
        self.assertTrue(all(item.base_test_id in "234567" for item in blocked))

    @patch(
        "swiss_sia.reference_model.sia4010.template_strategy.validate_binding"
    )
    def test_verified_template_unblocks_only_covered_case(self, validate):
        validate.return_value = TemplateValidation(
            "QUALIFIED_TEMPLATE_VERIFIED",
            "T4",
            (),
            "abc123",
        )
        binding = TemplateBinding(
            template_id="T4",
            project_path=Path("C:/qualified/template"),
            qualification_manifest=Path("C:/qualified/review.json"),
            covered_cases=("test_4/4",),
            status="QUALIFIED",
        )
        plans = build_hybrid_case_plans(self.requirements, (binding,))
        by_case = {(item.variant, item.case_id): item for item in plans}
        self.assertEqual(
            by_case[("test_4", "4")].status,
            "READY_FROM_QUALIFIED_TEMPLATE",
        )
        self.assertEqual(
            by_case[("test_5A", "5A")].status,
            "BLOCKED_TEMPLATE_REQUIRED",
        )

    def test_required_evidence_is_specific_to_system_family(self):
        self.assertIn(
            "multizone_apachehvac_topology_review",
            self.requirements["5"].required_evidence,
        )
        self.assertIn(
            "pv_capacity_authority_resolution",
            self.requirements["7"].required_evidence,
        )


if __name__ == "__main__":
    unittest.main()
