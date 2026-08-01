"""Evaluate the active qualified SIA 4010 case from its newest APS file."""

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

for module_name in tuple(sys.modules):
    if module_name == "swiss_sia.reference_model" or module_name.startswith(
        "swiss_sia.reference_model."
    ):
        del sys.modules[module_name]


def _room_id(room):
    """Return the ResultsReader identifier from one room-list entry."""

    if isinstance(room, dict):
        return room.get("id") or room.get("room_id")
    if isinstance(room, (list, tuple)) and len(room) >= 2:
        return room[1]
    return None


def run():
    """Compare one qualified active APS case without changing VE or APS data."""

    import iesve

    from swiss_sia.reference_model.sia4010.active_case_evaluation import (
        QUALIFIED_ACTIVE_CASES,
        evaluate_qualified_active_case,
    )
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.simulation_results import (
        list_aps_files,
        open_results_reader,
    )

    project = iesve.VEProject.get_current_project()
    project_path = Path(str(project.path))
    scenario_path = project_path / "sia_model_scenario.json"
    scenario = ModelScenario.load(scenario_path)
    pair = (scenario.variant, scenario.case_id)
    if pair not in QUALIFIED_ACTIVE_CASES:
        raise RuntimeError(
            "APS evaluation is not qualified for {}/{}. Supported active cases: "
            "{}".format(
                pair[0],
                pair[1],
                ", ".join(
                    "{}/{}".format(*item)
                    for item in sorted(QUALIFIED_ACTIVE_CASES)
                ),
            )
        )
    aps_files = list_aps_files(project)
    if not aps_files:
        raise RuntimeError(
            "No APS file was found in the active project's Vista folder."
        )
    vista = project_path / "Vista"
    aps_name = max(
        aps_files,
        key=lambda name: os.path.getmtime(str(vista / name)),
    )
    aps_path = vista / aps_name
    results_file = open_results_reader(aps_name)
    try:
        rooms = list(results_file.get_room_list() or [])
    except Exception as exc:
        raise RuntimeError(
            "Cannot read the APS room list: {}".format(exc)
        ) from exc
    room_ids = tuple(
        identifier
        for identifier in (_room_id(room) for room in rooms)
        if identifier is not None
    )
    if len(room_ids) != 1:
        raise RuntimeError(
            "Qualified Test 1/2 extraction requires exactly one APS room; "
            "found {}".format(len(room_ids))
        )
    output = (
        project_path
        / "sia4010_artifacts"
        / "results"
        / "SIA4010_{}_{}_evaluation.json".format(
            scenario.variant, scenario.case_id
        )
    )
    receipt = evaluate_qualified_active_case(
        variant=scenario.variant,
        case_id=scenario.case_id,
        results_file=results_file,
        room_id=room_ids[0],
        aps_path=aps_path,
        bundle_root=PROJECT_ROOT / "SIA_4010_geteilter_Link",
        bindings_path=(
            PROJECT_ROOT
            / "config"
            / "sia4010_aps_bindings_ve_runtime.json"
        ),
        output_path=output,
    )
    from swiss_sia.reference_model.sia4010.evidence_registry import (
        build_all_class_navigators,
        register_case_evaluation,
    )

    autonomy = PROJECT_ROOT / "sia4010_evidence" / "autonomy"
    registry = autonomy / "sia4010_case_evidence.json"
    register_case_evaluation(
        registry,
        receipt,
        project_path=project_path,
    )
    navigator = build_all_class_navigators(
        registry,
        PROJECT_ROOT / "SIA_4010_geteilter_Link",
        autonomy / "navigator",
    )
    print("SIA 4010 ACTIVE-CASE APS EVALUATION: {}".format(receipt.status))
    print("Project: {}".format(str(getattr(project, "name", "") or "")))
    print("Case: {}/{}".format(receipt.variant, receipt.case_id))
    print("Observed metrics: {}".format(receipt.observed_metric_count))
    print(
        "Acceptance criterion available: {}".format(
            receipt.acceptance_criterion_available
        )
    )
    print(
        "Required output scope complete: {}".format(
            receipt.required_output_scope_complete
        )
    )
    print(
        "Distribution criteria: {}".format(
            receipt.distribution_criterion_count
        )
    )
    print("Report: {}".format(output))
    print(
        "Eight-class navigator: {}".format(
            navigator["global_artifacts"]["html"]
        )
    )
    print("No VE model, APS file or official workbook was changed.")
    return receipt


if __name__ == "__main__":
    run()
