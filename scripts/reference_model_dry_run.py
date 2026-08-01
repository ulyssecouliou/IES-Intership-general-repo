"""Pure-Python preflight for geometry/config/report validation outside VE."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from swiss_sia.reference_model.asset_manifest import load_asset_manifest
from swiss_sia.reference_model.config_loader import load_configuration
from swiss_sia.reference_model.gbxml_writer import GbxmlWriter
from swiss_sia.reference_model.geometry import ReferenceGeometryGenerator
from swiss_sia.reference_model.report_generator import ReportGenerator
from swiss_sia.reference_model.results import (
    AuditEvent,
    ValidationResult,
    ValidationStatus,
    worst_status,
)
from swiss_sia.reference_model.validator import ReferenceModelValidator


def main(config_path=None):
    """Generate and validate pure-Python artifacts without mutating VE."""

    project_root = PROJECT_ROOT
    parameters = load_configuration(config_path)
    geometry = ReferenceGeometryGenerator(parameters).generate()
    validator = ReferenceModelValidator()
    manifest = None
    results = []
    if parameters.value("asset_provisioning_mode") == "create":
        configured_manifest = parameters.value("asset_manifest_file")
        try:
            if not configured_manifest:
                raise ValueError("asset_manifest_file is required in create mode")
            manifest_path = Path(str(configured_manifest))
            if not manifest_path.is_absolute():
                base_folder = (
                    Path(config_path).resolve().parent
                    if config_path is not None
                    else project_root
                )
                manifest_path = base_folder / manifest_path
            manifest = load_asset_manifest(manifest_path)
            results.extend(validator.validate_asset_manifest(manifest))
        except Exception as exc:
            results.append(
                ValidationResult(
                    control_id="ASSET-001",
                    category="VE asset provisioning",
                    status=ValidationStatus.FAIL,
                    message="Create-mode asset manifest is unavailable or invalid",
                    evidence={
                        "exception_type": type(exc).__name__,
                        "message": str(exc),
                    },
                )
            )
    planned = manifest.planned_parameter_names if manifest else None
    results.extend(validator.validate_configuration(parameters, planned))
    results.extend(validator.validate_geometry(geometry, parameters))
    output = project_root / "outputs" / "reference_model_dry_run"
    gbxml_path = GbxmlWriter(parameters).write(
        geometry, output / "geometry" / "swiss_reference_model.gbxml"
    )
    audit = [
        AuditEvent(
            sequence=1,
            timestamp_utc="",
            stage="dry_run",
            action="generate and validate pure-Python artifacts",
            outcome=worst_status(results).value,
            details={"gbxml_path": str(gbxml_path)},
        )
    ]
    artifacts = ReportGenerator(output / "reports").generate(
        run_metadata={"mode": "PURE_PYTHON_DRY_RUN", "project_root": str(project_root)},
        parameters=parameters,
        validations=results,
        audit_events=audit,
        geometry=geometry,
        additional_data={
            "gbxml_path": str(gbxml_path),
            "asset_provisioning_mode": parameters.value("asset_provisioning_mode"),
            "asset_manifest": manifest.to_dict() if manifest else None,
        },
    )
    print("Status: {}".format(worst_status(results).value))
    print("Report: {}".format(artifacts.report_json))
    return 1 if worst_status(results).value == "FAIL" else 0


if __name__ == "__main__":
    selected_config = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    raise SystemExit(main(selected_config))
