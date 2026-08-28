"""Run-button launcher for SIA 4010 official test execution (Phase B).

Use this file from the IESVE Scripts window with the Run button.

It locates the official SIA 4010 bundle under ``sia4010_official_bundle/``,
generates its checksum manifest if needed, then evaluates every registered test
against its official reference band and writes a summary.

Until the VE/APS result bindings are confirmed in the runtime and candidate
results are supplied, every metric stays NOT_CHECKABLE (fail-closed). This
launcher never fabricates a result and reaching a band is never SIA validation.
"""

import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

BUNDLE_DIR_NAMES = ("SIA_4010_geteilter_Link", "sia4010_official_bundle")
SUMMARY_NAME = "SIA4010_test_execution_summary.json"


def _no_ve_result(binding, expected):
    """Placeholder VE/APS accessor.

    The real accessor reads ApacheSim/APS results inside the VE runtime and is
    qualified there (see docs/project/SIA4010_PHASE_B_VE_EXTRACTION_CONTRACT.md).
    Returning None keeps every metric fail-closed until that binding exists.
    """

    return None


def _prepare_bundle_root():
    """Return the bundle root with a manifest, generating one if needed."""

    from swiss_sia.reference_model.sia4010.test_loader import Sia4010TestLoader

    for directory in BUNDLE_DIR_NAMES:
        root = os.path.join(PROJECT_ROOT, directory)
        if not os.path.isdir(root):
            continue
        manifest = os.path.join(root, Sia4010TestLoader.MANIFEST_NAME)
        if not os.path.isfile(manifest):
            from swiss_sia.reference_model.sia4010.bundle_builder import write_manifest

            write_manifest(root)
        return root
    return None


if __name__ == "__main__":
    from swiss_sia.reference_model.sia4010.execution import run_all_tests
    from swiss_sia.reference_model.sia4010.observed_extraction import VeApsResolver

    bundle_root = _prepare_bundle_root()
    if bundle_root is None:
        print(
            "No official SIA 4010 bundle found. Place the official package under "
            "one of {} (test specifications, evaluation workbooks, example building) "
            "and run again.".format(", ".join(BUNDLE_DIR_NAMES))
        )
        sys.exit(0)

    # No confirmed VE/APS bindings yet -> resolver supplies nothing (fail-closed).
    resolver = VeApsResolver(accessor=_no_ve_result, bindings={})
    summary = run_all_tests(bundle_root, resolver)

    out_dir = os.path.join(PROJECT_ROOT, "sia4010_evidence")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, SUMMARY_NAME)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(summary.to_dict(), handle, indent=2, ensure_ascii=False)

    print("SIA 4010 test execution summary written to: {}".format(out_path))
    for test_id, status in sorted(summary.statuses.items()):
        print("  Test {}: {}".format(test_id, status))
    print(
        "Statuses stay NOT_CHECKABLE until VE/APS bindings are confirmed in the "
        "runtime and candidate results are supplied. This is not SIA validation; "
        "official class validation still requires SIA sub-commission attestation."
    )
