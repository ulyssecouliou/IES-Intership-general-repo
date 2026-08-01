"""Coverage proof for every SIA 4010 validation class and exact variant."""

import unittest
from pathlib import Path

from swiss_sia.reference_model.sia4010.case_manifest import Sia4010CaseManifest
from swiss_sia.reference_model.sia4010.coverage_audit import (
    build_all_classes_coverage_audit,
)


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "SIA_4010_geteilter_Link"
MANIFEST = ROOT / "config" / "sia4010_all_classes.json"


@unittest.skipUnless(BUNDLE.is_dir(), "official SIA 4010 package not present")
class Sia4010AllClassesCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = build_all_classes_coverage_audit(BUNDLE)

    def test_all_eight_classes_are_framework_covered(self):
        self.assertEqual(
            set(self.audit["classes"]),
            {"1A", "1B", "2A", "2B", "3", "4A", "4B", "5"},
        )
        self.assertTrue(
            all(
                row["framework_status"] == "PASS"
                for row in self.audit["classes"].values()
            )
        )

    def test_all_24_exact_variants_are_parsed_and_registered(self):
        summary = self.audit["summary"]
        self.assertEqual(summary["required_exact_variants"], 24)
        self.assertEqual(summary["parsed_exact_variants"], 24)
        self.assertEqual(summary["registered_scenarios"], 24)
        self.assertEqual(summary["registered_exact_cases"], 30)
        self.assertEqual(summary["preparation_ready_cases"], 30)
        self.assertEqual(summary["deterministic_geometry_artifact_cases"], 23)
        self.assertEqual(summary["runtime_qualification_cases"], 5)
        self.assertEqual(summary["runtime_discovery_cases"], 13)
        self.assertEqual(summary["source_bound_bundle_cases"], 13)
        self.assertEqual(summary["apachesim_qualification_cases"], 6)
        self.assertEqual(summary["qualified_aps_evaluation_cases"], 11)
        self.assertEqual(
            summary["qualified_aps_complete_evaluation_cases"], 11
        )
        self.assertEqual(
            summary["qualified_aps_partial_evaluation_cases"], 0
        )
        self.assertEqual(summary["missing_parser_variants"], [])
        self.assertEqual(summary["missing_scenarios"], [])

    def test_generator_coverage_is_reported_honestly(self):
        self.assertEqual(self.audit["summary"]["implemented_ve_cases"], 1)
        self.assertEqual(
            self.audit["classes"]["1A"]["ve_generator_status"], "PARTIAL"
        )
        self.assertEqual(
            self.audit["classes"]["5"]["ve_generator_status"], "NOT_IMPLEMENTED"
        )

    def test_full_manifest_is_fail_closed_for_every_class(self):
        manifest = Sia4010CaseManifest.load(MANIFEST)
        self.assertEqual(set(manifest.classes), set(self.audit["classes"]))
        for class_id in manifest.classes:
            with self.subTest(class_id=class_id):
                statuses = manifest.class_readiness(class_id)
                self.assertTrue(statuses)
                self.assertTrue(
                    all(
                        item.status == "BLOCKED_MISSING_INPUTS"
                        for item in statuses.values()
                    )
                )


if __name__ == "__main__":
    unittest.main()
