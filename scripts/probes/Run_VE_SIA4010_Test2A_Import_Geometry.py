"""Guarded gbXML import for the prepared SIA 4010 Test 2A cell.

Run this explicitly from the IESVE VEScripts editor in the saved disposable
Test 2A project.  Geometry import is a model mutation, so this launcher refuses
an unsaved project, a scenario other than test_2A/2A, or a project that already
contains bodies.  It imports the checksum-traced preparation artifact and then
reads the resulting areas and openings back from VE.

The script does not assign constructions, profiles, controls or weather, does
not run ApacheSim, and does not save the project.  Continue only when the final
status is ``GEOMETRY_IMPORTED_AND_READBACK_VERIFIED``.
"""

from __future__ import print_function

import hashlib
import io
import json
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

REPORT_DIRECTORY = Path("sia4010_artifacts") / "model_builder" / "test2a"
GEOMETRY_DIRECTORY = Path("sia4010_artifacts") / "model_builder" / "geometry"
GEOMETRY_FILENAME = "SIA4010_test_2A_2A.gbxml"
GEOMETRY_AUDIT_FILENAME = "SIA4010_test_2A_2A_geometry.json"
EXPECTED_STATUS = "GEOMETRY_IMPORTED_AND_READBACK_VERIFIED"


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_report(project_path, payload):
    directory = Path(project_path) / REPORT_DIRECTORY
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = directory / ("sia4010_test2a_geometry_import_{}.json".format(timestamp))
    with io.open(str(path), "w", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, indent=2))
        stream.write("\n")
    digest = _sha256(path)
    checksum = path.with_suffix(path.suffix + ".sha256")
    checksum.write_text("{}  {}\n".format(digest, path.name), encoding="ascii")
    return path


def _bodies(project):
    bodies = []
    for model in list(getattr(project, "models", None) or []):
        bodies.extend(list(model.get_bodies(False) or []))
    return bodies


def _opening_count(bodies):
    count = 0
    errors = []
    for body in bodies:
        try:
            surfaces = list(body.get_surfaces() or [])
        except Exception as exc:  # pragma: no cover - native VE boundary
            errors.append("{}: {}".format(type(exc).__name__, exc))
            continue
        for surface in surfaces:
            getter = getattr(surface, "get_openings", None)
            if not callable(getter):
                continue
            try:
                count += len(list(getter() or []))
            except Exception as exc:  # pragma: no cover - native VE boundary
                errors.append("{}: {}".format(type(exc).__name__, exc))
    return count, errors


def _load_geometry_contract(project_path):
    geometry_directory = Path(project_path) / GEOMETRY_DIRECTORY
    gbxml_path = geometry_directory / GEOMETRY_FILENAME
    audit_path = geometry_directory / GEOMETRY_AUDIT_FILENAME
    if not gbxml_path.is_file():
        raise RuntimeError("Prepared Test 2A gbXML is missing: {}".format(gbxml_path))
    if not audit_path.is_file():
        raise RuntimeError("Prepared geometry audit is missing: {}".format(audit_path))
    payload = json.loads(audit_path.read_text(encoding="utf-8"))
    if payload.get("variant") != "test_2A" or payload.get("case_id") != "2A":
        raise RuntimeError("Prepared geometry audit belongs to another case")
    validation = payload.get("geometry_validation", {})
    if validation.get("status") != "PASS" or not all(
        validation.get("checks", {}).values()
    ):
        raise RuntimeError("Prepared Test 2A geometry audit is not PASS")
    if Path(str(payload.get("gbxml_path", ""))).resolve() != gbxml_path.resolve():
        raise RuntimeError("Geometry audit does not identify the prepared gbXML")
    return gbxml_path, audit_path, payload


def _prior_import_receipt(project_path, gbxml_path):
    """Return proof that this launcher created the existing geometry.

    A failed strict read-back may still follow a successful import.  VEScripts
    then keeps the body in memory.  A second import would duplicate it, so a
    rerun is allowed to perform read-back only when a prior local receipt proves
    that the exact gbXML was accepted and yielded one body with two openings.
    """

    pattern = "sia4010_test2a_geometry_import_*.json"
    reports = sorted(
        (Path(project_path) / REPORT_DIRECTORY).glob(pattern),
        reverse=True,
    )
    expected_sha = _sha256(gbxml_path)
    for path in reports:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        prepared = payload.get("prepared_geometry", {})
        imported = payload.get("import_call", {})
        readback = payload.get("readback", {})
        if (
            prepared.get("gbxml_sha256") == expected_sha
            and imported.get("forme_retenue")
            and readback.get("body_count") == 1
            and readback.get("opening_count") == 2
        ):
            return {
                "path": str(path),
                "sha256": _sha256(path),
                "original_import_call": imported,
            }
    return None


def run():
    try:
        import iesve  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Run this script from the IESVE VEScripts editor") from exc

    # VEScripts keeps one interpreter alive between Run-button presses.  Drop
    # only the helper corrected by this launcher so a failed first attempt does
    # not retain its stale integer cap-mode call.
    sys.modules.pop("scripts.importer_geometrie_test1", None)
    from scripts.importer_geometrie_test1 import (
        _essayer_import,
        comparer,
        totaux_attendus,
        totaux_releves,
    )
    from ve_adapter.geometrie_test1 import charger_cotes
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.sia4010.scenario_preflight import (
        is_temporary_ve_project,
    )

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("Open the saved disposable Test 2A project first")
    project_path = Path(str(getattr(project, "path", "") or ""))
    if not project_path.is_dir() or is_temporary_ve_project(project_path):
        raise RuntimeError("Save the disposable Test 2A project before importing")

    scenario_path = project_path / "sia_model_scenario.json"
    if not scenario_path.is_file():
        raise RuntimeError("Prepare test_2A/2A before importing geometry")
    scenario = ModelScenario.load(scenario_path)
    if (scenario.variant, scenario.case_id) != ("test_2A", "2A"):
        raise RuntimeError(
            "Active scenario is {}/{}; expected test_2A/2A".format(
                scenario.variant, scenario.case_id
            )
        )

    gbxml_path, audit_path, _audit = _load_geometry_contract(project_path)
    before = _bodies(project)
    prior_receipt = None
    if before:
        prior_receipt = _prior_import_receipt(project_path, gbxml_path)
        if prior_receipt is None:
            raise RuntimeError(
                "Refusing geometry import: the active project already contains {} "
                "body/bodies and no matching prior import receipt exists. Use "
                "a fresh disposable project.".format(len(before))
            )

    expected = totaux_attendus(charger_cotes())
    print("SIA 4010 TEST 2A GUARDED GEOMETRY IMPORT")
    print("Project: {}".format(project_path))
    print("gbXML: {}".format(gbxml_path))
    print("This operation imports geometry and does not save the project.")

    if prior_receipt is None:
        import_result = _essayer_import(
            iesve.ImportGBXML, str(gbxml_path), module_iesve=iesve
        )
        import_performed_this_run = bool(import_result.get("forme_retenue"))
    else:
        print("Matching prior import receipt found; read-back only, no re-import.")
        import_result = prior_receipt["original_import_call"]
        import_performed_this_run = False
    bodies = _bodies(project)
    measured = totaux_releves(bodies)
    comparisons = comparer(expected, measured)
    opening_count, opening_errors = _opening_count(bodies)
    areas_verified = bool(comparisons) and all(
        item.get("statut") == "CONCORDE" for item in comparisons.values()
    )
    verified = bool(import_result.get("forme_retenue")) and bool(bodies)
    verified = verified and areas_verified and opening_count == 2 and not opening_errors
    status = EXPECTED_STATUS if verified else "GEOMETRY_IMPORT_READBACK_FAILED"

    report = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "project": {
            "name": str(getattr(project, "name", "") or ""),
            "path": str(project_path),
        },
        "scenario": {"variant": scenario.variant, "case_id": scenario.case_id},
        "prepared_geometry": {
            "gbxml_path": str(gbxml_path),
            "gbxml_sha256": _sha256(gbxml_path),
            "audit_path": str(audit_path),
            "audit_sha256": _sha256(audit_path),
        },
        "import_call": import_result,
        "import_performed_this_run": import_performed_this_run,
        "prior_import_receipt": prior_receipt,
        "readback": {
            "body_count": len(bodies),
            "opening_count": opening_count,
            "opening_errors": opening_errors,
            "expected_areas_m2": expected,
            "measured_areas_m2": measured,
            "area_comparisons": comparisons,
        },
        "project_saved_by_script": False,
        "mutation_scope": "GEOMETRY_IMPORT_ONLY",
        "next_action": (
            "Save the project, then rerun the Test 2A runtime capability probe."
            if verified
            else "Discard this project and inspect the readback differences."
        ),
        "claim_guardrail": (
            "This receipt verifies only the imported common test-cell geometry. "
            "It does not qualify constructions, profiles, shading, simulation, "
            "SIA validation or compliance."
        ),
    }
    report_path = _write_report(project_path, report)
    print("TEST 2A GEOMETRY IMPORT: {}".format(status))
    print("Bodies: {}; openings: {}".format(len(bodies), opening_count))
    print("Project saved by script: NO")
    print("Report: {}".format(report_path))
    if not verified:
        raise RuntimeError("Imported geometry failed strict VE readback; see report")
    return report


if __name__ == "__main__":
    run()
