"""Tests for the qualified-template model and Test 2 execution shortcut."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from swiss_sia.reference_model.sia4010.evidence_registry import (
    register_model_outcome,
    register_template_case_simulation,
)
from swiss_sia.reference_model.sia4010.model_scenario import (
    ModelScenario,
    official_features,
)
from swiss_sia.reference_model.sia4010.template_apachesim import (
    TemplateApacheSimError,
    run_qualified_template_apachesim,
)
from swiss_sia.reference_model.sia4010.template_strategy import (
    TEMPLATE_BINDINGS_FILENAME,
    instantiate_qualified_case,
    load_requirements,
    project_signature,
    qualify_instantiated_template_model,
)


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _scenario_payload(
    variant="test_2A", case_id="2A", target_class="1A"
):
    return {
        "schema_version": "1.0",
        "scenario_id": "SIA4010_TEST2A_TEMPLATE",
        "profile": "SIA4010_OFFICIAL",
        "selection": {
            "target_class": target_class,
            "variant": variant,
            "case_id": case_id,
        },
        "features": official_features(variant, case_id),
        "files": {
            "case_manifest_file": "sia4010_case_manifest.json",
            "ve_config_file": "reference_model_config.json",
            "ve_asset_manifest_file": "reference_model_assets.json",
        },
        "execution": {"mode": "QUALIFY_IN_ACTIVE_VE_PROJECT"},
    }


def _qualified_disposable(
    tmp_path: Path,
    *,
    variant="test_2A",
    case_id="2A",
    target_class="1A",
    base_test_id="2",
) -> Path:
    source = tmp_path / "qualified_source"
    source.mkdir()
    (source / "case.mdl").write_text("qualified model", encoding="utf-8")
    (source / "Project Content.db").write_bytes(b"qualified database")
    (source / "sia_model_scenario.json").write_text(
        json.dumps(_scenario_payload(variant, case_id, target_class)),
        encoding="utf-8",
    )
    signature = project_signature(source)["template_signature_sha256"]
    requirements = load_requirements(
        ROOT / "config" / "sia4010_template_requirements.json"
    )
    qualification = tmp_path / "qualification.json"
    qualification.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "status": "QUALIFIED",
                "reviewer": "Independent reviewer",
                "reviewed_at": "2026-08-21T12:00:00Z",
                "ve_version": "2025",
                "evidence": list(requirements[base_test_id].required_evidence),
                "covered_cases": ["{}/{}".format(variant, case_id)],
                "template_signature_sha256": signature,
            }
        ),
        encoding="utf-8",
    )
    control = tmp_path / "control_project"
    control.mkdir()
    (control / TEMPLATE_BINDINGS_FILENAME).write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "bindings": [
                    {
                        "template_id": "TEST2A-EXACT",
                        "project_path": str(source),
                        "qualification_manifest": str(qualification),
                        "covered_cases": ["{}/{}".format(variant, case_id)],
                        "status": "QUALIFIED",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    destination = tmp_path / "disposable_projects"
    destination.mkdir()
    return instantiate_qualified_case(
        control,
        ROOT,
        variant,
        case_id,
        destination,
    ).disposable_project


class _Project:
    def __init__(self, path: Path):
        self.path = str(path)


class _ApacheSim:
    def __init__(self, project: Path, mismatch: bool = False):
        self.project = project
        self.options = {"simulation_timestep": 2, "preconditioning_days": 14}
        self.mismatch = mismatch

    def get_options(self):
        options = dict(self.options)
        if self.mismatch and "reporting_interval" in options:
            options["reporting_interval"] = 2
        return options

    def set_options(self, options):
        self.options.update(options)
        return True

    def run_simulation(self, queue_to_tasks=False):
        vista = self.project / "Vista"
        vista.mkdir(exist_ok=True)
        (vista / self.options["results_filename"]).write_bytes(b"test2 aps")
        return True


def test_exact_disposable_template_becomes_registered_model_evidence(tmp_path):
    project = _qualified_disposable(tmp_path)
    receipt = qualify_instantiated_template_model(project, ROOT)
    assert receipt.status == "QUALIFIED_TEMPLATE_MODEL_VERIFIED"
    registry = tmp_path / "registry.json"
    scenario = ModelScenario.load(project / "sia_model_scenario.json")
    payload = register_model_outcome(
        registry,
        scenario,
        workflow_status="PASS",
        report_path=receipt.report_path,
        project_path=project,
    )
    evidence = payload["cases"]["test_2A/2A"]["model_evidence"]
    assert evidence["status"] == "VERIFIED"
    assert evidence["artifact_sha256"] == _sha256(receipt.report_path)


def test_changed_disposable_template_is_rejected(tmp_path):
    project = _qualified_disposable(tmp_path)
    (project / "case.mdl").write_text("changed", encoding="utf-8")
    with pytest.raises(Exception, match="changed after the qualified copy"):
        qualify_instantiated_template_model(project, ROOT)


def test_test2_template_simulation_is_annual_hourly_and_registers(tmp_path):
    project = _qualified_disposable(tmp_path)
    model_receipt = qualify_instantiated_template_model(project, ROOT)
    registry = tmp_path / "registry.json"
    scenario = ModelScenario.load(project / "sia_model_scenario.json")
    register_model_outcome(
        registry,
        scenario,
        workflow_status="PASS",
        report_path=model_receipt.report_path,
        project_path=project,
    )
    sim = _ApacheSim(project)
    receipt = run_qualified_template_apachesim(
        project=_Project(project),
        apachesim_factory=lambda: sim,
        repository_root=ROOT,
        now=datetime(2026, 8, 21, 13, 14, 15, tzinfo=timezone.utc),
        file_wait_seconds=0,
    )
    assert receipt.requested_options == {
        "start_day": 1,
        "start_month": 1,
        "end_day": 31,
        "end_month": 12,
        "reporting_interval": 3,
        "results_filename": "SIA4010_test_2A_2A_20260821_131415.aps",
    }
    assert receipt.options_after["preconditioning_days"] == 14
    payload = register_template_case_simulation(
        registry, receipt, project_path=project
    )
    evidence = payload["cases"]["test_2A/2A"]["simulation_evidence"]
    assert evidence["model_evidence_link_status"] == "VERIFIED"
    assert evidence["verification_basis"] == "QUALIFIED_EXACT_TEMPLATE"


def test_test2_template_simulation_rejects_option_readback_mismatch(tmp_path):
    project = _qualified_disposable(tmp_path)
    qualify_instantiated_template_model(project, ROOT)
    with pytest.raises(TemplateApacheSimError, match="read-back mismatch"):
        run_qualified_template_apachesim(
            project=_Project(project),
            apachesim_factory=lambda: _ApacheSim(project, mismatch=True),
            repository_root=ROOT,
            now=datetime(2026, 8, 21, 13, 14, 15, tzinfo=timezone.utc),
            file_wait_seconds=0,
        )


def test_diagnostic_1e_uses_its_official_specification(tmp_path):
    project = _qualified_disposable(
        tmp_path,
        variant="test_1",
        case_id="1E",
        target_class="1A",
        base_test_id="1",
    )
    qualify_instantiated_template_model(project, ROOT)
    receipt = run_qualified_template_apachesim(
        project=_Project(project),
        apachesim_factory=lambda: _ApacheSim(project),
        repository_root=ROOT,
        now=datetime(2026, 8, 21, 14, 0, 0, tzinfo=timezone.utc),
        file_wait_seconds=0,
    )
    audit = json.loads(Path(receipt.audit_path).read_text(encoding="utf-8"))
    assert receipt.variant == "test_1"
    assert receipt.case_id == "1E"
    assert Path(receipt.source_path).name == "Spezifikation_Test1.pdf"
    assert "diagnostic 1E" in audit["source"]
