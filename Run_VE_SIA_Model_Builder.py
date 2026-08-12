"""Scenario-driven IESVE launcher for SIA 380/2 and SIA 4010 models.

Place ``sia_model_scenario.json`` in the active VE project folder.  The default
PREPARE_ONLY mode writes exact geometry and a preflight report without changing
the VE project.  VE mutation is allowed only when every official input is
resolved and the asset manifest is tagged for the exact selected case.
"""

import json
import re
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


def _safe_name(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("._") or "scenario"


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def run(resume_after_import=False):
    """Prepare, create, or safely resume the selected active-project model."""

    from swiss_sia.reference_model.config_loader import load_configuration
    from swiss_sia.reference_model.gbxml_writer import GbxmlWriter
    from swiss_sia.reference_model.geometry import ReferenceGeometryGenerator
    from swiss_sia.reference_model.sia4010.case_geometry import (
        Sia4010CellGeometryGenerator,
        validate_cell_geometry,
    )
    from swiss_sia.reference_model.sia4010.case_manifest import Sia4010CaseManifest
    from swiss_sia.reference_model.sia4010.case_registry import get_case_capability
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.sia4010.scenario_preflight import (
        evaluate_scenario,
        resolve_scenario_path,
    )
    from swiss_sia.reference_model.ve_api import IesVeGateway
    from swiss_sia.reference_model.workflow import ReferenceModelWorkflow

    gateway = IesVeGateway()
    scenario_path = gateway.project_path / "sia_model_scenario.json"
    scenario = ModelScenario.load(scenario_path)
    preflight = evaluate_scenario(
        scenario, gateway.project_path, PROJECT_ROOT
    )
    output = gateway.project_path / "sia4010_artifacts" / "model_builder"
    stem = _safe_name(scenario.scenario_id)
    preflight_path = output / "{}_preflight.json".format(stem)
    _write_json(preflight_path, preflight.to_dict())

    capability = (
        get_case_capability(scenario.variant, scenario.case_id)
        if scenario.is_official
        else None
    )
    if (
        scenario.is_official
        and capability is not None
        and not capability.mutation_supported
    ):
        runtime_qualification = (
            scenario.execution_mode == "QUALIFY_IN_ACTIVE_VE_PROJECT"
            and capability.runtime_qualification_supported
        )
        # Tests 2 and 3 use the same source-qualified test cell as Test 1.
        # PREPARE_ONLY may therefore write that geometry artifact, while all
        # controls, templates and VE mutation remain blocked. Other tests must
        # not receive a fabricated generic geometry.
        geometry_preparation_supported = (
            capability.geometry_artifact_supported
        )
        if (
            scenario.execution_mode == "PREPARE_ONLY"
            and not geometry_preparation_supported
        ):
            print("SIA MODEL BUILDER: PREPARED_WITH_BLOCKERS")
            print("Scenario: {}".format(scenario.scenario_id))
            print("Case: {}/{}".format(scenario.variant, scenario.case_id))
            print("Generator blocker: {}".format(capability.blocker_code))
            print("Preflight: {}".format(preflight_path))
            print("No geometry was fabricated and no VE model data was changed.")
            return preflight
        if (
            scenario.execution_mode != "PREPARE_ONLY"
            and not runtime_qualification
        ):
            raise RuntimeError(
                "Guarded VE mutation is not implemented for {}/{}: {} - {}".format(
                    scenario.variant,
                    scenario.case_id,
                    capability.blocker_code,
                    capability.blocker_detail,
                )
            )
    elif (
        scenario.execution_mode == "QUALIFY_IN_ACTIVE_VE_PROJECT"
        and (
            capability is None
            or not capability.runtime_qualification_supported
        )
    ):
        raise RuntimeError(
            "Runtime qualification mode is reserved for a registered "
            "unverified generator; use normal Create for this case."
        )

    manifest_path = resolve_scenario_path(
        scenario.files.case_manifest_file, gateway.project_path, PROJECT_ROOT
    )
    manifest = Sia4010CaseManifest.load(manifest_path)
    config_path = resolve_scenario_path(
        scenario.files.ve_config_file, gateway.project_path, PROJECT_ROOT
    )
    parameters = load_configuration(config_path if config_path.is_file() else None)
    if scenario.is_official:
        geometry_manifest = manifest
        if capability is not None and capability.geometry_artifact_supported:
            # The all-class manifest tracks unresolved class inputs. The
            # dimensioned common cell remains checksum-traced in the original
            # Test 1/2 manifest and is also prescribed by Test 3.
            geometry_manifest = Sia4010CaseManifest.load(
                PROJECT_ROOT / "config" / "sia4010_classes_1a_1b.json"
            )
        geometry = Sia4010CellGeometryGenerator(geometry_manifest).generate(
            identifier="SIA4010_{}_{}".format(
                _safe_name(scenario.variant).upper(),
                _safe_name(scenario.case_id).upper(),
            )
        )
        geometry_validation = validate_cell_geometry(
            geometry, geometry_manifest
        )
        if not geometry_validation.passed:
            raise RuntimeError(
                "SIA 4010 geometry validation failed: {}".format(
                    geometry_validation.checks
                )
            )
        geometry_checks = geometry_validation.checks
        geometry_status = geometry_validation.status
    else:
        geometry = ReferenceGeometryGenerator(parameters).generate()
        geometry_checks = {
            "custom_reference_geometry_generated": True,
            "official_sia4010_geometry_claim": False,
        }
        geometry_status = "PASS"
    gbxml_path = GbxmlWriter(parameters).write(
        geometry, output / "{}.gbxml".format(stem)
    )
    _write_json(
        output / "{}_geometry.json".format(stem),
        {
            "scenario": scenario.to_dict(),
            "geometry_validation": {
                "status": geometry_status,
                "checks": geometry_checks,
            },
            "geometry": geometry.to_dict(),
            "gbxml_path": str(gbxml_path),
        },
    )

    if scenario.execution_mode == "PREPARE_ONLY":
        prepared_status = (
            "PREPARED_GEOMETRY_WITH_BLOCKERS"
            if capability is not None and not capability.mutation_supported
            else "READY_FOR_REVIEW"
        )
        print("SIA MODEL BUILDER: {}".format(prepared_status))
        print("Scenario: {}".format(scenario.scenario_id))
        print("Case: {}/{}".format(scenario.variant, scenario.case_id))
        print("Geometry: {}".format(gbxml_path))
        print("Preflight: {}".format(preflight_path))
        print("No VE model data was changed.")
        return preflight

    if not preflight.allows_mutation:
        print("SIA MODEL BUILDER: BLOCKED")
        for blocker in preflight.blockers:
            print("- {}".format(blocker))
        print("Preflight: {}".format(preflight_path))
        print("No VE model data was changed.")
        return preflight

    if scenario.execution_mode == "QUALIFY_IN_ACTIVE_VE_PROJECT":
        print("SIA MODEL BUILDER: GUARDED RUNTIME QUALIFICATION")
        print(
            "This is an unverified generator probe in a disposable project; "
            "no compliance claim is permitted."
        )

    asset_path = resolve_scenario_path(
        scenario.files.ve_asset_manifest_file, gateway.project_path, PROJECT_ROOT
    )
    parameters = parameters.with_overrides(
        {
            "asset_provisioning_mode": {
                "value": "create",
                "source": "SIA model scenario",
                "source_locator": str(scenario_path),
            },
            "asset_manifest_file": {
                "value": str(asset_path),
                "source": "SIA model scenario",
                "source_locator": str(scenario_path),
            },
        }
    )
    workflow = ReferenceModelWorkflow(
        parameters,
        gateway,
        geometry_factory=lambda: geometry,
        geometry_artifact_name="{}.gbxml".format(stem),
    )
    outcome = workflow.run(
        dry_run=False,
        resume_after_import=bool(resume_after_import),
    )
    try:
        from swiss_sia.reference_model.sia4010.evidence_registry import (
            build_all_class_navigators,
            register_model_outcome,
        )

        autonomy = PROJECT_ROOT / "sia4010_evidence" / "autonomy"
        registry = autonomy / "sia4010_case_evidence.json"
        register_model_outcome(
            registry,
            scenario,
            workflow_status=outcome.status.value,
            report_path=outcome.artifacts.report_json,
            project_path=gateway.project_path,
        )
        build_all_class_navigators(
            registry,
            PROJECT_ROOT / "SIA_4010_geteilter_Link",
            autonomy / "navigator",
        )
    except Exception as registry_error:
        # The model report remains authoritative and has already been written.
        # Never hide a cross-project coordination failure, but do not relabel a
        # completed VE mutation as failed solely because the central ledger is
        # temporarily unavailable.
        print(
            "EVIDENCE REGISTRY WARNING: {}".format(registry_error)
        )
    print(outcome.message)
    print("Status: {}".format(outcome.status.value))
    print("Audit report: {}".format(outcome.artifacts.report_json))
    return outcome


if __name__ == "__main__":
    run()
