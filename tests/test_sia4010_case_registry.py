"""Capability-registry and autonomous class-preparation tests."""

import unittest
from pathlib import Path
from unittest import mock

from swiss_sia.reference_model.sia4010.case_registry import (
    all_case_capabilities,
    get_case_capability,
)
from swiss_sia.reference_model.sia4010.model_scenario import TEST_CASES
from swiss_sia.reference_model.sia4010.preparation_bundle import (
    CasePreparationReceipt,
    prepare_all_classes,
    prepare_case,
    prepare_class,
)

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "SIA_4010_geteilter_Link"


class Sia4010CaseRegistryTests(unittest.TestCase):
    """The registry separates framework coverage from VE mutation coverage."""

    def test_every_registered_case_has_one_capability_record(self):
        capabilities = all_case_capabilities()
        expected = sum(len(case_ids) for case_ids in TEST_CASES.values())
        self.assertEqual(len(capabilities), expected)
        self.assertEqual(
            len({(item.variant, item.case_id) for item in capabilities}),
            expected,
        )

    def test_only_verified_case600_mutation_is_enabled(self):
        enabled = [
            (item.variant, item.case_id)
            for item in all_case_capabilities()
            if item.mutation_supported
        ]
        self.assertEqual(enabled, [("test_1", "600")])

    def test_test1_variants_have_guarded_runtime_probes_only(self):
        probes = [
            (item.variant, item.case_id)
            for item in all_case_capabilities()
            if item.runtime_qualification_supported
        ]
        # The four diagnostic cases joined the list on 2026-08-13:
        # `test1_diagnostic_bundle` applies their frozen links, so they
        # go through the same qualification in a disposable project. They follow
        # the six ISO cases in registry order.
        self.assertEqual(
            probes,
            [
                ("test_1", "640"),
                ("test_1", "600FF"),
                ("test_1", "900"),
                ("test_1", "940"),
                ("test_1", "900FF"),
                ("test_1", "1A"),
                ("test_1", "1B"),
                ("test_1", "1C"),
                ("test_1", "1D"),
            ],
        )
        for case_id in ("640", "600FF", "900", "940", "900FF"):
            capability = get_case_capability("test_1", case_id)
            self.assertFalse(capability.mutation_supported)
            self.assertEqual(
                capability.blocker_code,
                "VE_RUNTIME_QUALIFICATION_REQUIRED",
            )
        self.assertEqual(
            get_case_capability("test_1", "900").generator_id,
            "test1_heavyweight_runtime_probe_v1",
        )

    def test_read_only_runtime_discovery_covers_test2a_test3_and_tests4_to7(self):
        discovery = [
            (item.variant, item.case_id)
            for item in all_case_capabilities()
            if item.runtime_discovery_supported
        ]
        self.assertEqual(len(discovery), 20)
        self.assertIn(("test_2A", "2A"), discovery)
        self.assertEqual(
            {case_id for variant, case_id in discovery if variant.startswith("test_3")},
            {"3{}".format(letter) for letter in "ABCDEFGHIJKL"},
        )
        self.assertFalse(get_case_capability("test_3A", "3A").mutation_supported)
        for variant, case_id in (
            ("test_4", "4"),
            ("test_5A", "5A"),
            ("test_5B", "5B"),
            ("test_5C", "5C"),
            ("test_5D", "5D"),
            ("test_6", "6"),
            ("test_7", "7"),
        ):
            capability = get_case_capability(variant, case_id)
            self.assertTrue(capability.runtime_discovery_supported)
            self.assertFalse(capability.mutation_supported)

    def test_source_bound_bundles_cover_test2a_and_all_test3_cases(self):
        source_bound = [
            (item.variant, item.case_id)
            for item in all_case_capabilities()
            if item.source_bound_bundle_supported
        ]
        self.assertEqual(len(source_bound), 13)
        self.assertIn(("test_2A", "2A"), source_bound)
        self.assertEqual(
            {
                case_id
                for variant, case_id in source_bound
                if variant.startswith("test_3")
            },
            {"3{}".format(letter) for letter in "ABCDEFGHIJKL"},
        )
        payload = get_case_capability("test_3A", "3A").to_dict()
        self.assertTrue(payload["source_bound_bundle_supported"])
        self.assertFalse(payload["mutation_supported"])

    def test_aps_load_evaluation_covers_conditioned_test1_cases_only(self):
        supported = [
            item.case_id
            for item in all_case_capabilities()
            if item.variant == "test_1" and item.aps_evaluation_supported
        ]
        # 1A through 1D evaluate an hourly deliverable, without criterion or
        # reference: they are therefore "supported" without being compared. The
        # scope says so, and the test below verifies it does not borrow case 600's.
        self.assertEqual(
            supported,
            [
                "600",
                "640",
                "600FF",
                "900",
                "940",
                "900FF",
                "1A",
                "1B",
                "1C",
                "1D",
                "1E",
            ],
        )
        for case_id in ("1A", "1B", "1C", "1D"):
            self.assertEqual(
                get_case_capability("test_1", case_id).aps_evaluation_scope,
                "HOURLY_DELIVERABLE_ONLY_NO_REFERENCE",
            )
        self.assertEqual(
            get_case_capability("test_1", "600").aps_evaluation_scope,
            "REFERENCE_OUTPUTS_IMPLEMENTED",
        )
        self.assertTrue(get_case_capability("test_1", "1E").aps_full_evaluation_supported)
        for case_id in ("600FF", "900FF"):
            self.assertTrue(
                get_case_capability("test_1", case_id).aps_full_evaluation_supported
            )

    def test_apachesim_qualification_is_limited_to_generated_test1_cases(self):
        supported = [
            item.case_id
            for item in all_case_capabilities()
            if item.apachesim_qualification_supported
        ]
        # The diagnostic cases need the annual ApacheSim like the others:
        # their deliverable IS the 8760-hour dataset. 1E stays out, its
        # generator does not exist.
        self.assertEqual(
            supported,
            [
                "600",
                "640",
                "600FF",
                "900",
                "940",
                "900FF",
                "1A",
                "1B",
                "1C",
                "1D",
            ],
        )
        self.assertFalse(
            get_case_capability("test_1", "1E").apachesim_qualification_supported
        )
        self.assertFalse(
            get_case_capability("test_2A", "2A").apachesim_qualification_supported
        )

    def test_qualified_template_simulation_closes_1e_and_test2_routes(self):
        supported = {
            (item.variant, item.case_id)
            for item in all_case_capabilities()
            if item.qualified_template_simulation_supported
        }
        self.assertEqual(
            supported,
            {
                ("test_1", "1E"),
                ("test_2A", "2A"),
                ("test_2B", "2B"),
                ("test_2C", "2C"),
                ("test_2D", "2D"),
            },
        )
        payload = get_case_capability("test_2A", "2A").to_dict()
        self.assertTrue(payload["qualified_template_simulation_supported"])
        self.assertFalse(payload["apachesim_qualification_supported"])

    def test_tests1_to3_can_prepare_geometry_without_enabling_mutation(self):
        for variant, case_id in (
            ("test_1", "600FF"),
            ("test_2A", "2A"),
            ("test_3L", "3L"),
        ):
            with self.subTest(variant=variant):
                capability = get_case_capability(variant, case_id)
                self.assertTrue(capability.geometry_artifact_supported)
                self.assertFalse(capability.mutation_supported)

    def test_unimplemented_cases_have_actionable_blockers(self):
        capability = get_case_capability("test_5C", "5C")
        self.assertFalse(capability.mutation_supported)
        self.assertEqual(
            capability.blocker_code,
            "VE_MULTIZONE_HVAC_BINDING_NOT_IMPLEMENTED",
        )
        self.assertTrue(capability.blocker_detail)


@unittest.skipUnless(BUNDLE.is_dir(), "official SIA 4010 package not present")
class Sia4010PreparationBundleTests(unittest.TestCase):
    """Preparation remains source-traced and fail-closed without VE."""

    def test_unimplemented_case_writes_verified_preparation_artifact(self):
        with mock.patch(
            "swiss_sia.reference_model.sia4010.preparation_bundle._write_json"
        ) as write_json:
            receipt = prepare_case(ROOT, ROOT, "3", "test_5A", "5A")
            self.assertEqual(receipt.status, "PREPARED_WITH_BLOCKERS")
            self.assertFalse(receipt.mutation_supported)
            payload = write_json.call_args.args[1]
            self.assertTrue(payload["official_bundle"]["verified"])
            self.assertEqual(payload["pipeline"]["ve_model_generation"], "BLOCKED")
            self.assertEqual(
                payload["pipeline"]["delegated_external_inputs"],
                "MISSING_MANIFEST",
            )
            self.assertEqual(
                payload["generator_capability"]["generation_status"],
                "NOT_IMPLEMENTED",
            )
            self.assertEqual(payload["confirmed_specification_input"]["test_id"], "5")
            self.assertTrue(payload["confirmed_specification_input"]["confirmed_inputs"])
            self.assertEqual(
                payload["geometry_source_status"],
                "EXTRACTED_FROM_VERIFIED_OFFICIAL_IFC",
            )
            self.assertEqual(
                set(payload["official_ifc_spaces"]),
                {"100", "102", "200", "201", "202", "203", "204", "205"},
            )
            self.assertTrue(payload["source_files"])
            self.assertFalse(payload["external_input_readiness"]["ready_for_binding"])
            self.assertTrue(
                any(
                    item["code"].startswith("EXTERNAL_INPUT:")
                    for item in payload["blockers"]
                )
            )
            self.assertFalse(
                any(
                    item["role"] == "reference_report" for item in payload["source_files"]
                )
            )

    def test_whole_class_preparation_lists_every_exact_case(self):
        def fake_prepare(
            project_root, repository_root, target_class, variant, case_id, **kwargs
        ):
            return CasePreparationReceipt(
                status="PREPARED_WITH_BLOCKERS",
                target_class=target_class,
                variant=variant,
                case_id=case_id,
                audit_path=ROOT / "{}.json".format(case_id),
                case_manifest_path=ROOT / "config" / "sia4010_all_classes.json",
                config_path=ROOT / "config" / "reference_model_config.json",
                asset_manifest_path=ROOT / "config" / "reference_model_assets.json",
                mutation_supported=False,
                blockers=("UNRESOLVED",),
            )

        with (
            mock.patch(
                "swiss_sia.reference_model.sia4010.preparation_bundle.prepare_case",
                side_effect=fake_prepare,
            ),
            mock.patch(
                "swiss_sia.reference_model.sia4010.preparation_bundle._write_json"
            ) as write_json,
        ):
            # Note the homonym: "1A" here is a validation CLASS,
            # not the diagnostic case 1A of Test 1. Class 1A requires
            # `test_1` and `test_2A`.
            receipt = prepare_class(ROOT, ROOT, "1A")
            self.assertEqual(receipt.target_class, "1A")
            # 12 not 8: `test_1` now carries 11 cases instead of 7,
            # since the registration of diagnostic cases 1A through 1D, plus
            # the single case of `test_2A`.
            self.assertEqual(len(receipt.cases), 12)
            self.assertGreater(receipt.blocked_cases, 0)
            payload = write_json.call_args.args[1]
            self.assertEqual(payload["exact_case_count"], 12)
            self.assertEqual(payload["status"], "CLASS_PREPARED_WITH_BLOCKERS")
            self.assertEqual(len(payload["execution_queue"]), 12)
            self.assertEqual(
                payload["execution_contract"]["project_isolation"],
                "ONE_DISPOSABLE_VE_PROJECT_PER_EXACT_CASE",
            )

    def test_all_classes_preparation_uses_one_verified_source_index(self):
        with (
            mock.patch(
                "swiss_sia.reference_model.sia4010.preparation_bundle._write_json"
            ) as write_json,
            mock.patch(
                "swiss_sia.reference_model.sia4010.preparation_bundle.GbxmlWriter.write",
                side_effect=lambda model, path: Path(path),
            ),
        ):
            receipt = prepare_all_classes(ROOT, ROOT)
        self.assertEqual(len(receipt.classes), 8)
        # 34 since the registration of diagnostic cases 1A through 1D of
        # Test 1. The number of classes remains 8: these are cases, not
        # variants, and the class matrix is unchanged.
        self.assertEqual(receipt.unique_exact_cases, 34)
        # 27: same ISO 52016 chapter 7 cell for the four diagnostic
        # cases, which all derive from case 600.
        self.assertEqual(receipt.unique_geometry_artifact_cases, 27)
        geometry_paths = {
            item.geometry_artifact_path
            for class_receipt in receipt.classes
            for item in class_receipt.cases
            if item.geometry_artifact_path is not None
        }
        # 27 not 23: the four diagnostic cases of Test 1 share the
        # ISO 52016 chapter 7 cell of case 600 from which they derive.
        self.assertEqual(len(geometry_paths), 27)
        self.assertGreater(receipt.exact_case_occurrences, 30)
        self.assertGreater(receipt.blocked_occurrences, 0)
        self.assertEqual(
            receipt.status,
            "ALL_CLASSES_PREPARED_WITH_BLOCKERS",
        )
        payload = write_json.call_args.args[1]
        self.assertEqual(payload["external_input_matrix"]["exact_case_count"], 34)
        self.assertEqual(payload["external_input_matrix"]["catalog_input_count"], 17)


if __name__ == "__main__":
    unittest.main()
