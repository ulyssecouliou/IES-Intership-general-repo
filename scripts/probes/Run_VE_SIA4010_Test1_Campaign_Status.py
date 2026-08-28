"""Read-only Test 1 ISO and diagnostic campaign navigator for VEScripts."""

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)


def run():
    """Report completed evidence and the next disposable Test 1 project."""

    from swiss_sia.reference_model.sia4010.evidence_registry import load_registry
    from swiss_sia.reference_model.sia4010.test1_campaign import (
        build_test1_campaign_status,
    )

    registry_path = (
        PROJECT_ROOT
        / "sia4010_evidence"
        / "autonomy"
        / "sia4010_case_evidence.json"
    )
    registry = load_registry(registry_path)
    report = build_test1_campaign_status(registry)
    report_path = registry_path.parent / "sia4010_test1_campaign_status.json"
    temporary = report_path.with_suffix(report_path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(report_path)

    print("SIA 4010 TEST 1 CAMPAIGN: {}".format(report["status"]))
    print(
        "ISO reference-result cases complete: {}/{} ({})".format(
            report["iso_reference_results_complete_count"],
            report["iso_case_count"],
            report["iso_status"],
        )
    )
    print(
        "Diagnostic hourly deliverables complete: {}/{} ({})".format(
            report["diagnostic_deliverables_complete_count"],
            report["diagnostic_case_count"],
            report["diagnostic_status"],
        )
    )
    print("Formal Test 1 gate: {}".format(report["formal_test1_status"]))
    for item in report["cases"]:
        print("- {}: {}".format(item["case_id"], item["stage"]))
    if report["next_case"] is not None:
        item = report["next_case"]
        print("NEXT CASE: {}".format(item["case_id"]))
        action = item["next_action"]
        if action["requires_fresh_project"]:
            if item["case_id"] == "1E":
                print("Create a separate copy of completed case 1D named: {}".format(
                    item["recommended_project_name"]
                ))
            else:
                print("Create a fresh saved VE project named: {}".format(
                    item["recommended_project_name"]
                ))
        elif action["project_path"]:
            print("Open existing VE project: {}".format(action["project_path"]))
        print("Run VEScript: {}".format(action["script"]))
        if action.get("follow_up_script"):
            print("Then run: {}".format(action["follow_up_script"]))
        print("Action: {}".format(action["instruction"]))
    print("Report: {}".format(report_path))
    print("No VE model, APS file or official source was changed.")
    return report_path


if __name__ == "__main__":
    run()
