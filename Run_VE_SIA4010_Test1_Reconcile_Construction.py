"""Reconcile one exact stale construction in an official Test 1 project."""

import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _resolve(project_path, configured_path):
    candidate = Path(str(configured_path))
    return candidate if candidate.is_absolute() else project_path / candidate


def run(construction_key):
    """Update and verify one uniquely identified construction assembly."""

    try:
        import iesve
    except ImportError as exc:
        raise RuntimeError("Run this script from IESVE VEScripts") from exc
    for module_name in tuple(sys.modules):
        if module_name == "swiss_sia.reference_model" or module_name.startswith(
            "swiss_sia.reference_model."
        ):
            del sys.modules[module_name]
    from swiss_sia.reference_model.asset_manifest import load_asset_manifest
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.sia4010.scenario_preflight import (
        is_temporary_ve_project,
    )
    from swiss_sia.reference_model.ve_api import IesVeGateway

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("Open the backed-up disposable Test 1 project first")
    project_path = Path(str(project.path))
    if not project_path.is_dir() or is_temporary_ve_project(project_path):
        raise RuntimeError("The active Test 1 project must be saved")
    scenario = ModelScenario.load(project_path / "sia_model_scenario.json")
    if not scenario.is_official or scenario.variant != "test_1":
        raise RuntimeError("This repair is restricted to an official Test 1 case")
    manifest_path = _resolve(
        project_path, scenario.files.ve_asset_manifest_file
    )
    manifest = load_asset_manifest(manifest_path)
    valid_keys = {item.key for item in manifest.constructions}
    if construction_key not in valid_keys:
        raise RuntimeError(
            "Construction {!r} is not defined by this exact Test 1 manifest".format(
                construction_key
            )
        )
    safe_key = re.sub(r"[^A-Za-z0-9_.-]+", "_", construction_key)
    report_path = (
        project_path
        / "sia4010_artifacts"
        / "diagnostics"
        / "sia4010_test1_construction_repair_{}_{}.json".format(
            safe_key, datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        )
    )
    report = {
        "schema_version": "1.0",
        "status": "STARTED",
        "project_path": str(project_path),
        "scenario": {"variant": scenario.variant, "case_id": scenario.case_id},
        "construction_key": construction_key,
        "mutation_scope": "ONE_EXISTING_CDB_CONSTRUCTION_AND_ITS_LAYERS",
        "mutation_boundary_entered": False,
        "manifest": {"path": str(manifest_path), "sha256": _sha256(manifest_path)},
        "compliance_claim_allowed": False,
    }
    _write(report_path, report)
    try:
        gateway = IesVeGateway(iesve)
        reconcile = getattr(gateway, "reconcile_existing_construction", None)
        if not callable(reconcile):
            raise RuntimeError(
                "Reloaded IesVeGateway exposes no construction reconciliation"
            )
        report["mutation_boundary_entered"] = True
        report["status"] = "MUTATION_STARTED"
        _write(report_path, report)
        receipt = reconcile(manifest, construction_key)
        report.update({"status": "PASS", "receipt": receipt})
    except Exception as exc:
        report.update(
            {
                "status": "FAIL",
                "error": "{}: {}".format(type(exc).__name__, exc),
                "recovery_action": "Restore the project backup before retrying.",
            }
        )
        _write(report_path, report)
        raise
    _write(report_path, report)
    report_path.with_suffix(report_path.suffix + ".sha256").write_text(
        "{}  {}\n".format(_sha256(report_path), report_path.name),
        encoding="ascii",
    )
    print("SIA 4010 TEST 1 CONSTRUCTION RECONCILIATION: PASS")
    print("Case: test_1/{}".format(scenario.case_id))
    print("Construction: {} ({})".format(construction_key, receipt["construction_id"]))
    print("Status: {}".format(receipt["status"]))
    print("Report: {}".format(report_path))
    return report_path


if __name__ == "__main__":
    raise RuntimeError(
        "Use the Test 1 active-case one-click launcher so the exact failed "
        "construction key is derived from the guarded model audit."
    )
