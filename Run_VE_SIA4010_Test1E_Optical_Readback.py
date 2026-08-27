"""Read the complete Test 1E external-shade optical state without mutation."""

import json
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))


def _purge_cached_reference_model_modules():
    for module_name in tuple(sys.modules):
        if module_name == "swiss_sia.reference_model" or module_name.startswith(
            "swiss_sia.reference_model."
        ):
            del sys.modules[module_name]


def run():
    """Print and retain every relevant optical field on the assigned CDB."""

    _purge_cached_reference_model_modules()
    import iesve  # type: ignore

    from swiss_sia.reference_model.sia4010.test1e_awning_qualification import (
        _live_targets,
    )
    from swiss_sia.reference_model.ve_api import IesVeGateway

    project = iesve.VEProject.get_current_project()
    project_path = Path(str(getattr(project, "path", "") or "")).resolve()
    gateway = IesVeGateway()
    targets = _live_targets(gateway)
    constructions = {}
    tokens = ("shade", "solar", "visible", "transmitt", "reflect", "glaz", "g_")
    for target in targets:
        identifier = str(target["construction_id"])
        properties = dict(target["construction"].get_properties())
        constructions[identifier] = {
            key: value
            for key, value in sorted(properties.items())
            if any(token in key.casefold() for token in tokens)
        }
    output = (
        project_path
        / "sia4010_artifacts"
        / "diagnostics"
        / "sia4010_test1e_optical_readback.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "OPTICAL_READBACK_RECORDED",
        "project_path": str(project_path),
        "opening_ids": [target["opening_id"] for target in targets],
        "constructions": constructions,
        "mutation_performed": False,
        "project_saved_by_script": False,
    }
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("SIA 4010 TEST 1E OPTICAL READBACK: OPTICAL_READBACK_RECORDED")
    print("Project: {}".format(project_path))
    for identifier, properties in constructions.items():
        print("Construction: {}".format(identifier))
        for key, value in properties.items():
            print("  {} = {!r}".format(key, value))
    print("Report: {}".format(output))
    print("No VE object was changed and the project was not saved by the script.")
    return output


if __name__ == "__main__":
    run()
