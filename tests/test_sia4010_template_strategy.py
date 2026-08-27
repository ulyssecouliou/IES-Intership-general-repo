"""Tests for the fail-closed SIA 4010 hybrid execution strategy."""

import unittest
from pathlib import Path
from unittest.mock import patch

from swiss_sia.reference_model.sia4010.template_strategy import (
    TemplateBinding,
    TemplateValidation,
    _is_transient_ve_file,
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
        self.assertTrue(self.requirements["1"].template_allowed)
        self.assertEqual(
            self.requirements["7"].strategy,
            "QUALIFIED_VE_TEMPLATE_REQUIRED",
        )
        for requirement in self.requirements.values():
            self.assertIn("required_output_scope_review", requirement.required_evidence)
            self.assertNotIn("qualified_aps", requirement.required_evidence)

    def test_template_signature_excludes_ve_temporary_save_model(self):
        self.assertTrue(_is_transient_ve_file(Path("TEST-tmpSave.mdl")))
        self.assertTrue(_is_transient_ve_file(Path("test-TMPSAVE.MDL")))
        self.assertFalse(_is_transient_ve_file(Path("TEST.mdl")))

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
            "BLOCKED_TEMPLATE_REQUIRED",
        )

    def test_unbound_complex_cases_are_blocked(self):
        plans = build_hybrid_case_plans(self.requirements, ())
        blocked = [item for item in plans if item.status == "BLOCKED_TEMPLATE_REQUIRED"]
        # 24: all cases outside the direct Test 1 route, including diagnostic 1E.
        #
        # The previous version expected 27 and placed 1A through 1D among them
        # "for lack of a bound template". That was the right count for the wrong
        # reason. Cases 600 through 1D keep their guarded direct route. Only 1E,
        # which has no exposed generator, may use an independently qualified
        # exact template.
        self.assertEqual(len(blocked), 24)
        self.assertTrue(self.requirements["1"].template_allowed)
        test1_bloques = {item.case_id for item in blocked if item.base_test_id == "1"}
        self.assertEqual(test1_bloques, {"1E"})
        # The positive control: the four follow direct runtime qualification,
        # while 1E fails closed until an exact template is bound.
        par_cas = {
            item.case_id: item.status for item in plans if item.base_test_id == "1"
        }
        for case_id in ("1A", "1B", "1C", "1D"):
            self.assertEqual(par_cas[case_id], "READY_FOR_REAL_VE_QUALIFICATION", case_id)
        self.assertEqual(par_cas["1E"], "BLOCKED_TEMPLATE_REQUIRED")

    @patch("swiss_sia.reference_model.sia4010.template_strategy.validate_binding")
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

    @patch("swiss_sia.reference_model.sia4010.template_strategy.validate_binding")
    def test_verified_exact_template_unblocks_diagnostic_1e(self, validate):
        validate.return_value = TemplateValidation(
            "QUALIFIED_TEMPLATE_VERIFIED", "T1E", (), "def456"
        )
        binding = TemplateBinding(
            template_id="T1E",
            project_path=Path("C:/qualified/test1e"),
            qualification_manifest=Path("C:/qualified/test1e-review.json"),
            covered_cases=("test_1/1E",),
            status="QUALIFIED",
        )
        plans = build_hybrid_case_plans(self.requirements, (binding,))
        plan = next(
            item for item in plans if (item.variant, item.case_id) == ("test_1", "1E")
        )
        self.assertEqual(plan.status, "READY_FROM_QUALIFIED_TEMPLATE")
        self.assertEqual(plan.route, "QUALIFIED_VE_TEMPLATE")

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
