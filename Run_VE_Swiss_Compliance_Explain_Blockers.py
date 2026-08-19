"""
Explain what blocks a COMPLIANT SIA 380/2 verdict for the latest analysed model.

Run this file from the IESVE Scripts window with the Run button AFTER running
Run_VE_Swiss_Compliance.py. It finds the most recent
reports/*_compliance_criteria.json and prints, in plain text:

  - the overall status and the criteria tally;
  - every criterion that is NOT_CHECKABLE / PARTIAL / NOT_OK, with the exact
    reason (runtime_evidence);
  - the decisive global-comparison gate status;
  - the reference-project blockers.

No VE model needs to be open: it only reads the last report. Copy the printed
block back to share it.
"""

import glob
import json
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_REPORTS = os.path.join(PROJECT_ROOT, "reports")
_ATTENTION = {"NOT_CHECKABLE", "PARTIAL", "NOT_OK", "NEEDS_REVIEWER_EVIDENCE"}


def _latest_manifest():
    pattern = os.path.join(_REPORTS, "*_compliance_criteria.json")
    matches = glob.glob(pattern)
    if not matches:
        return None
    return max(matches, key=os.path.getmtime)


def main():
    path = _latest_manifest()
    if not path:
        print("No *_compliance_criteria.json found in {}.".format(_REPORTS))
        print("Run Run_VE_Swiss_Compliance.py first.")
        return

    with open(path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    evaluation = manifest.get("evaluation", {})
    print("=" * 78)
    print("COMPLIANCE EXPLAINER -", os.path.basename(path))
    print("=" * 78)
    print("Overall SIA 380/2 :", evaluation.get("overall_sia3802_status"),
          "(", evaluation.get("overall_sia3802_reason"), ")")
    print("Rooms analysed    :", evaluation.get("rooms_analysed"))
    print("Criteria tally    :", evaluation.get("criteria_status_tally"))
    print("Decisive gate     :", manifest.get("decisive_gate", {}).get("runtime_status"))
    print("   ->", manifest.get("decisive_gate", {}).get("runtime_evidence"))

    print("\n--- REFERENCE-PROJECT BLOCKERS ({}) ---".format(
        evaluation.get("reference_project_status") or "unknown"))
    blockers = evaluation.get("reference_project_blockers", [])
    if blockers:
        for blocker in blockers:
            print("  -", blocker)
    else:
        print("  (none)")

    print("\n--- CRITERIA NEEDING ACTION ---")
    for criterion in manifest.get("criteria", []):
        status = criterion.get("runtime_status", "")
        if status in _ATTENTION:
            print("  [{}] {}".format(status.ljust(24), criterion.get("id")))
            print("        source     :", criterion.get("data_source"))
            print("        capability :", criterion.get("ve_capability"))
            print("        evidence   :", criterion.get("runtime_evidence"))

    print("\n--- WHAT VE CANNOT PRODUCE (structural) ---")
    for criterion in manifest.get("criteria", []):
        if criterion.get("runtime_status") == "NOT_AVAILABLE_IN_VE":
            print("  -", criterion.get("id"), "::", criterion.get("ve_capability_note"))
    print("=" * 78)


if __name__ == "__main__":
    main()
