"""VEScripts run-button audit for all eight SIA 4010 validation classes."""

import json
import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT in sys.path:
    sys.path.remove(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

# VE Scripts keeps imported Python modules alive between Run-button executions.
# Always reload the exact-variant routing from the current source files.
for module_name in tuple(sys.modules):
    if module_name == "swiss_sia" or module_name.startswith("swiss_sia."):
        del sys.modules[module_name]


def run():
    """Verify the official package and write the complete coverage report."""

    import iesve

    from swiss_sia.reference_model.sia4010.coverage_audit import (
        build_all_classes_coverage_audit,
    )

    project = iesve.VEProject.get_current_project()
    bundle_path = os.path.join(PROJECT_ROOT, "SIA_4010_geteilter_Link")
    report = build_all_classes_coverage_audit(bundle_path)
    output_dir = os.path.join(
        str(project.path), "sia4010_artifacts", "diagnostics"
    )
    os.makedirs(output_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(
        output_dir, "sia4010_all_classes_coverage_{}.json".format(stamp)
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)

    summary = report["summary"]
    print("SIA 4010 ALL-CLASSES COVERAGE: {}".format(report["status"]))
    print("Project: {}".format(getattr(project, "name", "")))
    print("Validation classes: {}".format(summary["validation_classes"]))
    print("Exact variants: {}/{}".format(
        summary["parsed_exact_variants"], summary["required_exact_variants"]
    ))
    print("Source-traced preparation cases: {}/{}".format(
        summary["preparation_ready_cases"], summary["registered_exact_cases"]
    ))
    print("Deterministic geometry artifacts: {}/{}".format(
        summary["deterministic_geometry_artifact_cases"],
        summary["registered_exact_cases"],
    ))
    print("VE runtime-qualification probes: {}/{}".format(
        summary["runtime_qualification_cases"],
        summary["registered_exact_cases"],
    ))
    print("Read-only runtime discovery cases: {}/{}".format(
        summary["runtime_discovery_cases"],
        summary["registered_exact_cases"],
    ))
    print("Conditional source-bound bundles: {}/{}".format(
        summary["source_bound_bundle_cases"],
        summary["registered_exact_cases"],
    ))
    print("Guarded ApacheSim qualification paths: {}/{}".format(
        summary["apachesim_qualification_cases"],
        summary["registered_exact_cases"],
    ))
    print("Qualified active APS evaluations: {}/{}".format(
        summary["qualified_aps_evaluation_cases"],
        summary["registered_exact_cases"],
    ))
    print("Implemented guarded VE cases: {}".format(
        summary["implemented_ve_cases"]
    ))
    print("Report: {}".format(output_path))
    print("No VE model, workbook or APS data was changed.")


if __name__ == "__main__":
    run()
