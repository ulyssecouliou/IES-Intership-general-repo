"""Open the accelerated all-class SIA 4010 campaign dashboard in VE."""

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

for module_name in tuple(sys.modules):
    if module_name == "swiss_sia.reference_model" or module_name.startswith(
        "swiss_sia.reference_model."
    ):
        del sys.modules[module_name]


def run():
    """Rebuild the queue, print its next action and open the HTML dashboard."""

    from swiss_sia.reference_model.sia4010.validation_campaign import (
        write_validation_campaign,
    )

    payload = write_validation_campaign(PROJECT_ROOT)
    summary = payload["summary"]
    action = payload.get("next_action")
    print("SIA 4010 ACCELERATED VALIDATION CAMPAIGN")
    print(
        "Exact cases complete: {}/{}".format(
            summary["complete_exact_cases"], summary["exact_cases"]
        )
    )
    print(
        "Classes technically complete: {}/{}".format(
            summary["technically_complete_classes"],
            summary["validation_classes"],
        )
    )
    if action:
        print("NEXT CASE: {} ({})".format(action["case_key"], action["phase_id"]))
        print("NEXT ACTION: {}".format(action["action_code"]))
        print("RUN: {}".format(action["launcher"] or "manual evidence review"))
        print(action["instruction"])
    else:
        print("All technical case gates are complete; submit the evidence package.")
    report = Path(payload["artifacts"]["html"])
    print("Dashboard: {}".format(report))
    try:
        os.startfile(str(report))
    except (AttributeError, OSError):
        pass
    print("This dashboard does not grant SIA attestation.")
    return payload


if __name__ == "__main__":
    run()

