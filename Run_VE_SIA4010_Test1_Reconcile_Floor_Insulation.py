"""Repair the stale ISO Test 1 ideal-floor material in the active VE project.

This recovery is restricted to an official Test 1 scenario and the exact
``xps_ground`` logical material in its source-traced manifest. It writes a
durable STARTED audit before changing the CDB material and verifies every
property after the setter. Run only on a backed-up disposable Test 1 project.
"""

import hashlib
import json
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


def _resolve_scenario_file(project_path, configured_path):
    """Resolve either an absolute or project-relative scenario file path."""

    candidate = Path(str(configured_path))
    return candidate if candidate.is_absolute() else project_path / candidate


def _safe_predispatch_failure(path):
    """Recognize the one historical cache failure that called no VE setter."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    error = str(payload.get("error", ""))
    return (
        payload.get("status") == "FAIL"
        and "AttributeError" in error
        and "reconcile_existing_material" in error
        and "receipt" not in payload
    )


def _safe_retryable_report(path):
    """Allow an idempotent retry after a completed or pre-dispatch attempt."""

    if _safe_predispatch_failure(path):
        return True
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return payload.get("status") == "PASS" and "receipt" in payload


def run():
    """Reconcile and verify only the official ideal-floor insulation material."""

    try:
        import iesve
    except ImportError as exc:
        raise RuntimeError("Run this script from IESVE VEScripts") from exc

    # VE keeps one Python interpreter alive between VEScripts runs. Reload the
    # repository package so the newly added guarded gateway boundary is visible.
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
    scenario_path = project_path / "sia_model_scenario.json"
    scenario = ModelScenario.load(scenario_path)
    if not scenario.is_official or scenario.variant != "test_1":
        raise RuntimeError("This repair is restricted to an official Test 1 scenario")
    manifest_path = _resolve_scenario_file(
        project_path, scenario.files.ve_asset_manifest_file
    )
    manifest = load_asset_manifest(manifest_path)
    reports = project_path / "sia4010_artifacts" / "diagnostics"
    prior = sorted(reports.glob("sia4010_test1_floor_insulation_repair_*.json"))
    unsafe_prior = [path for path in prior if not _safe_retryable_report(path)]
    if unsafe_prior:
        raise RuntimeError(
            "A floor-insulation repair was already attempted; inspect it before "
            "retrying: {}".format(unsafe_prior[-1])
        )
    report_path = reports / (
        "sia4010_test1_floor_insulation_repair_{}.json".format(
            datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        )
    )
    report = {
        "schema_version": "1.0",
        "status": "STARTED",
        "project_path": str(project_path),
        "scenario": {"variant": scenario.variant, "case_id": scenario.case_id},
        "material_key": "xps_ground",
        "mutation_scope": "ONE_EXISTING_CDB_MATERIAL",
        "mutation_boundary_entered": False,
        "manifest": {"path": str(manifest_path), "sha256": _sha256(manifest_path)},
        "compliance_claim_allowed": False,
        "safe_predispatch_retry_of": [str(path) for path in prior],
    }
    _write(report_path, report)
    try:
        gateway = IesVeGateway(iesve)
        reconcile = getattr(gateway, "reconcile_existing_material", None)
        if not callable(reconcile):
            raise RuntimeError(
                "Reloaded IesVeGateway still exposes no material reconciliation"
            )
        report["mutation_boundary_entered"] = True
        report["status"] = "MUTATION_STARTED"
        _write(report_path, report)
        receipt = reconcile(manifest, "xps_ground")
        report.update({"status": "PASS", "receipt": receipt})
    except Exception as exc:
        report.update(
            {
                "status": "FAIL",
                "error": "{}: {}".format(type(exc).__name__, exc),
                "recovery_action": "Restore the project backup before another attempt.",
            }
        )
        _write(report_path, report)
        raise
    _write(report_path, report)
    report_path.with_suffix(report_path.suffix + ".sha256").write_text(
        "{}  {}\n".format(_sha256(report_path), report_path.name),
        encoding="ascii",
    )
    print("SIA 4010 TEST 1 FLOOR-INSULATION RECONCILIATION: PASS")
    print("Case: test_1/{}".format(scenario.case_id))
    print("Status: {}".format(receipt["status"]))
    print("Material ID: {}".format(receipt["material_id"]))
    print("Report: {}".format(report_path))
    print("Save the VE project, then run the Test 1 active-case one-click script.")
    return report_path


if __name__ == "__main__":
    run()
