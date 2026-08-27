"""Machine-readable coverage audit for all SIA 4010 validation classes.

This audit distinguishes software coverage (official bundle parsing, exact
variant routing, class navigation and acceptance-criterion guards) from VE
model-generator coverage.  It never turns a framework capability into a
compliance claim.
"""

from pathlib import Path
from typing import Any, Dict, Union

from ...config import SIA4010_CLASS_TEST_MATRIX
from .distribution_reference import DISTRIBUTION_CRITERIA
from .case_registry import all_case_capabilities, get_case_capability
from .model_scenario import TEST_CASES
from .navigator import Sia4010ValidationNavigator
from .test_runner import Sia4010TestRunner

IMPLEMENTED_VE_CASES = frozenset(
    (item.variant, item.case_id)
    for item in all_case_capabilities()
    if item.mutation_supported
)


def build_all_classes_coverage_audit(
    bundle_path: Union[str, Path],
) -> Dict[str, Any]:
    """Inspect the official package and return exact class/variant coverage."""

    runner = Sia4010TestRunner()
    bundle = runner.loader.load_bundle(bundle_path)
    capabilities = all_case_capabilities()
    required_variants = tuple(
        dict.fromkeys(
            variant
            for variants in SIA4010_CLASS_TEST_MATRIX.values()
            for variant in variants
        )
    )
    parsed_variants = set()
    test_rows = []
    for test_id in "1234567":
        bands = runner.expected_bands(bundle_path, test_id)
        variants = sorted(
            {
                runner._variant_key(test_id, band.case_id)
                for band in bands
                if runner._variant_key(test_id, band.case_id)
            }
        )
        parsed_variants.update(variants)
        test_rows.append(
            {
                "test_id": test_id,
                "reference_band_count": len(bands),
                "exact_variants": variants,
                "distribution_required": test_id in DISTRIBUTION_CRITERIA,
                "distribution_criterion_registered": (test_id in DISTRIBUTION_CRITERIA),
                "status": "PASS" if bands and variants else "FAIL",
            }
        )

    variant_rows = []
    for variant in required_variants:
        cases = tuple(TEST_CASES.get(variant, ()))
        implemented = [
            case_id for case_id in cases if (variant, case_id) in IMPLEMENTED_VE_CASES
        ]
        if implemented and len(implemented) == len(cases):
            generator_status = "IMPLEMENTED"
        elif implemented:
            generator_status = "PARTIAL"
        else:
            generator_status = "NOT_IMPLEMENTED"
        variant_rows.append(
            {
                "variant": variant,
                "official_cases": list(cases),
                "official_band_parser": (
                    "PASS" if variant in parsed_variants else "FAIL"
                ),
                "scenario_registered": bool(cases),
                "ve_generator_status": generator_status,
                "implemented_ve_cases": implemented,
                "case_capabilities": [
                    get_case_capability(variant, case_id).to_dict() for case_id in cases
                ],
            }
        )

    missing_parser_variants = sorted(set(required_variants) - parsed_variants)
    missing_scenarios = sorted(set(required_variants) - set(TEST_CASES))
    classes = {
        class_id: {
            "required_variants": list(variants),
            "navigator_supported": (
                class_id in Sia4010ValidationNavigator.SUPPORTED_CLASSES
            ),
            "framework_status": (
                "PASS"
                if all(
                    variant in parsed_variants and variant in TEST_CASES
                    for variant in variants
                )
                else "FAIL"
            ),
            "ve_generator_status": (
                "IMPLEMENTED"
                if all(
                    (variant, case_id) in IMPLEMENTED_VE_CASES
                    for variant in variants
                    for case_id in TEST_CASES.get(variant, ())
                )
                else (
                    "PARTIAL"
                    if any(
                        (variant, case_id) in IMPLEMENTED_VE_CASES
                        for variant in variants
                        for case_id in TEST_CASES.get(variant, ())
                    )
                    else "NOT_IMPLEMENTED"
                )
            ),
        }
        for class_id, variants in SIA4010_CLASS_TEST_MATRIX.items()
    }
    framework_pass = (
        not missing_parser_variants
        and not missing_scenarios
        and all(row["navigator_supported"] for row in classes.values())
    )
    return {
        "schema_version": "1.0",
        "status": (
            "FRAMEWORK_COVERAGE_PASS" if framework_pass else "FRAMEWORK_COVERAGE_FAIL"
        ),
        "official_bundle": {
            "root": str(bundle.root),
            "manifest": str(bundle.manifest_path),
            "issued_by": bundle.issued_by,
            "verified": True,
        },
        "summary": {
            "validation_classes": len(SIA4010_CLASS_TEST_MATRIX),
            "required_exact_variants": len(required_variants),
            "parsed_exact_variants": len(parsed_variants),
            "registered_scenarios": len(TEST_CASES),
            "registered_exact_cases": len(capabilities),
            "preparation_ready_cases": sum(
                item.preparation_status == "PREPARATION_READY" for item in capabilities
            ),
            "deterministic_geometry_artifact_cases": sum(
                item.geometry_artifact_supported for item in capabilities
            ),
            "runtime_qualification_cases": sum(
                item.runtime_qualification_supported for item in capabilities
            ),
            "runtime_discovery_cases": sum(
                item.runtime_discovery_supported for item in capabilities
            ),
            "source_bound_bundle_cases": sum(
                item.source_bound_bundle_supported for item in capabilities
            ),
            "apachesim_qualification_cases": sum(
                item.apachesim_qualification_supported for item in capabilities
            ),
            "qualified_template_simulation_cases": sum(
                item.qualified_template_simulation_supported for item in capabilities
            ),
            "qualified_aps_evaluation_cases": sum(
                item.aps_evaluation_supported for item in capabilities
            ),
            "qualified_aps_complete_evaluation_cases": sum(
                item.aps_full_evaluation_supported for item in capabilities
            ),
            "qualified_aps_partial_evaluation_cases": sum(
                item.aps_evaluation_scope == "SENSIBLE_LOAD_RESULTS_ONLY"
                for item in capabilities
            ),
            "implemented_ve_cases": len(IMPLEMENTED_VE_CASES),
            "missing_parser_variants": missing_parser_variants,
            "missing_scenarios": missing_scenarios,
        },
        "tests": test_rows,
        "classes": classes,
        "variants": variant_rows,
        "claim_guardrail": (
            "Framework coverage is not SIA validation. Each required VE case "
            "must be generated, simulated, compared against every official "
            "annual/hourly criterion and submitted for the required attestation."
        ),
    }
