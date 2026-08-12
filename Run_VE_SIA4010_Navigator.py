"""Run-button launcher for all eight SIA 4010 validation classes."""

import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT in sys.path:
    sys.path.remove(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

# VE Scripts persists imports between runs. Always reload the current
# eight-class navigator and exact-variant matrix from disk.
for module_name in tuple(sys.modules):
    if module_name == "swiss_sia" or module_name.startswith("swiss_sia."):
        del sys.modules[module_name]

BUNDLE_CANDIDATES = ("SIA_4010_geteilter_Link", "sia4010_official_bundle")
CASE_MANIFEST = os.path.join(
    PROJECT_ROOT, "config", "sia4010_all_classes.json"
)
EXECUTION_SUMMARY = os.path.join(
    PROJECT_ROOT, "sia4010_evidence", "SIA4010_test_execution_summary.json"
)
OUTPUT_DIRECTORY = os.path.join(PROJECT_ROOT, "sia4010_evidence", "navigator")
EVIDENCE_REGISTRY = os.path.join(
    PROJECT_ROOT,
    "sia4010_evidence",
    "autonomy",
    "sia4010_case_evidence.json",
)


def _verified_bundle():
    """Return whether one local official bundle passes checksum verification."""

    from swiss_sia.reference_model.sia4010.test_loader import Sia4010TestLoader

    loader = Sia4010TestLoader()
    for directory in BUNDLE_CANDIDATES:
        root = os.path.join(PROJECT_ROOT, directory)
        if os.path.isdir(root):
            try:
                bundle = loader.load_bundle(root)
                return True, str(bundle.manifest_path)
            except Exception as exc:
                return False, "{}: {}".format(root, exc)
    return False, "No official SIA 4010 bundle found"


def _execution_state():
    """Load the latest execution summary, if one exists."""

    if not os.path.isfile(EXECUTION_SUMMARY):
        return {}, {}
    with open(EXECUTION_SUMMARY, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    results = payload.get("test_results_map", {}) or {}
    locators = {}
    for variant, result in results.items():
        status = str((result or {}).get("status") or "").upper()
        if status in {"OFFICIAL_RESULTS_RECORDED", "FAILED", "FAIL"}:
            locators[variant] = EXECUTION_SUMMARY
    return results, locators


def run():
    """Build Navigator HTML/JSON artifacts for every validation class."""

    if os.path.isfile(EVIDENCE_REGISTRY):
        from swiss_sia.reference_model.sia4010.evidence_registry import (
            build_all_class_navigators,
        )

        payload = build_all_class_navigators(
            EVIDENCE_REGISTRY,
            os.path.join(PROJECT_ROOT, "SIA_4010_geteilter_Link"),
            os.path.join(
                PROJECT_ROOT, "sia4010_evidence", "autonomy", "navigator"
            ),
        )
        print("SIA 4010 AUTONOMOUS EVIDENCE NAVIGATOR")
        print(
            "Validation classes: {}".format(
                payload["summary"]["validation_classes"]
            )
        )
        print(
            "Ready for official review: {}".format(
                payload["summary"]["ready_for_official_review"]
            )
        )
        print(
            "Checksum-valid model cases: {}/{}".format(
                payload["summary"]["checksum_valid_model_cases"],
                payload["summary"]["exact_cases"],
            )
        )
        print(
            "Checksum-valid ApacheSim cases: {}/{}".format(
                payload["summary"]["checksum_valid_apachesim_cases"],
                payload["summary"]["exact_cases"],
            )
        )
        print(
            "Simulation-linked APS evaluations: {}".format(
                payload["summary"]["simulation_linked_aps_evaluations"]
            )
        )
        print("Official test evidence gates:")
        for test_id, evidence in sorted(payload["tests"].items()):
            print(
                "  Test {}: {} | model {}/{} | simulation {}/{} | "
                "APS result {}/{}".format(
                    test_id,
                    evidence["status"],
                    evidence["checksum_valid_model_cases"],
                    evidence["exact_cases"],
                    evidence["checksum_valid_simulation_cases"],
                    evidence["exact_cases"],
                    evidence["simulation_linked_result_cases"],
                    evidence["exact_cases"],
                )
            )
        print(
            "Report: {}".format(
                payload["global_artifacts"]["html"]
            )
        )
        print(
            "Only checksum-valid evidence satisfies a gate; no SIA "
            "attestation is inferred."
        )
        return payload

    from swiss_sia.reference_model.sia4010.case_manifest import (
        Sia4010CaseManifest,
    )
    from swiss_sia.reference_model.sia4010.navigator import (
        Sia4010ValidationNavigator,
    )
    from swiss_sia.reference_model.sia4010.navigator_report import (
        write_navigator_artifacts,
    )

    bundle_verified, bundle_note = _verified_bundle()
    manifest = Sia4010CaseManifest.load(CASE_MANIFEST)
    test_results, result_locators = _execution_state()
    print("SIA 4010 NAVIGATOR")
    print("Official bundle: {}".format(
        "VERIFIED" if bundle_verified else "BLOCKED"
    ))
    print("Bundle evidence: {}".format(bundle_note))

    for class_id in ("1A", "1B", "2A", "2B", "3", "4A", "4B", "5"):
        evaluation = Sia4010ValidationNavigator.evaluate(
            class_id,
            bundle_verified=bundle_verified,
            model_case_statuses=manifest.navigator_model_statuses(class_id),
            candidate_result_locators=result_locators,
            test_results_map=test_results,
        )
        paths = write_navigator_artifacts(evaluation, OUTPUT_DIRECTORY)
        print(
            "Class {}: {} | HTML: {}".format(
                class_id, evaluation.overall_status, paths["html"]
            )
        )

    print(
        "The navigator is fail-closed and does not grant official SIA validation."
    )


if __name__ == "__main__":
    run()
