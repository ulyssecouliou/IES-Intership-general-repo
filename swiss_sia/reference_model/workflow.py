"""End-to-end reference-model generation workflow."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .asset_manifest import AssetManifest, load_asset_manifest
from .compliance_config import ParameterRegistry
from .domain import GeometryModel, ModelSnapshot
from .exceptions import ReferenceModelError
from .gbxml_writer import GbxmlWriter
from .geometry import ReferenceGeometryGenerator
from .logging_config import LOGGER_NAME, configure_logging
from .report_generator import ReportArtifacts, ReportGenerator
from .results import AuditEvent, ValidationResult, ValidationStatus, worst_status
from .validator import ReferenceModelValidator
from .ve_api import VeGateway
from .ve_asset_provisioner import ProvisioningReceipt


@dataclass(frozen=True)
class WorkflowOutcome:
    """Final status, evidence artifacts, and snapshot for one workflow run."""

    status: ValidationStatus
    message: str
    artifacts: ReportArtifacts
    validation_results: List[ValidationResult]
    snapshot: Optional[ModelSnapshot]


class ReferenceModelWorkflow:
    """Orchestrates preflight, VE mutation, verification and reporting."""

    def __init__(
        self,
        parameters: ParameterRegistry,
        gateway: VeGateway,
        validator: Optional[ReferenceModelValidator] = None,
        now: Optional[Callable[[], datetime]] = None,
        geometry_factory: Optional[Callable[[], GeometryModel]] = None,
        geometry_artifact_name: str = "swiss_reference_model.gbxml",
    ):
        """Initialize workflow services around one VE gateway instance."""

        self.parameters = parameters
        self.gateway = gateway
        self.validator = validator or ReferenceModelValidator()
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.geometry_factory = geometry_factory or (
            lambda: ReferenceGeometryGenerator(self.parameters).generate()
        )
        self.geometry_artifact_name = geometry_artifact_name
        self.output_folder = gateway.project_path / "reference_model_artifacts"
        self.reporter = ReportGenerator(self.output_folder / "reports")
        self.logger = configure_logging(self.output_folder / "logs")
        self.audit_events: List[AuditEvent] = []
        self.asset_manifest: Optional[AssetManifest] = None
        self.provisioning_receipt: Optional[ProvisioningReceipt] = None

    def _timestamp(self) -> str:
        """Return a timezone-aware UTC timestamp for audit evidence."""

        return self.now().astimezone(timezone.utc).isoformat()

    def _audit(
        self, stage: str, action: str, outcome: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Append one ordered event to the in-memory audit trail."""

        event = AuditEvent(
            sequence=len(self.audit_events) + 1,
            timestamp_utc=self._timestamp(),
            stage=stage,
            action=action,
            outcome=outcome,
            details=details or {},
        )
        self.audit_events.append(event)
        self.logger.info("%s | %s | %s", stage, action, outcome)

    def _write_report(
        self,
        validations: List[ValidationResult],
        geometry: Optional[GeometryModel],
        snapshot: Optional[ModelSnapshot],
        mode: str,
        gbxml_path: Optional[Path] = None,
    ) -> ReportArtifacts:
        """Write all report formats for the current workflow state."""

        return self.reporter.generate(
            run_metadata={
                "generated_at_utc": self._timestamp(),
                "project_name": self.gateway.project_name,
                "project_path": str(self.gateway.project_path),
                "mode": mode,
                "package": "swiss_sia.reference_model",
                "model_schema_version": self.parameters.value("model_schema_version"),
            },
            parameters=self.parameters,
            validations=validations,
            audit_events=self.audit_events,
            geometry=geometry,
            snapshot=snapshot,
            additional_data={
                "gbxml_path": str(gbxml_path) if gbxml_path else None,
                "native_room_creation_api_available": False,
                "geometry_creation_boundary": "generated gbXML imported through ImportGBXML",
                "asset_provisioning_mode": self.parameters.value(
                    "asset_provisioning_mode"
                ),
                "asset_manifest": self.asset_manifest.to_dict()
                if self.asset_manifest
                else None,
                "provisioning_receipt": self.provisioning_receipt.to_dict()
                if self.provisioning_receipt
                else None,
            },
        )

    def _load_create_mode_manifest(self) -> Optional[AssetManifest]:
        """Load the project-relative asset manifest when create mode is active."""

        if self.parameters.value("asset_provisioning_mode") != "create":
            return None
        configured_path = self.parameters.value("asset_manifest_file")
        if not configured_path:
            raise ReferenceModelError(
                "asset_manifest_file is required when asset_provisioning_mode='create'"
            )
        manifest_path = Path(str(configured_path))
        if not manifest_path.is_absolute():
            manifest_path = self.gateway.project_path / manifest_path
        return load_asset_manifest(manifest_path)

    def run(
        self, dry_run: bool = False, resume_after_import: bool = False
    ) -> WorkflowOutcome:
        """Execute fail-closed preflight, optional mutation, and reporting.

        ``resume_after_import`` is a controlled recovery path for a previous run
        that successfully imported the deterministic rooms but stopped before
        completing assignments.  It reuses and validates those rooms; it never
        imports the gbXML a second time.
        """

        if dry_run and resume_after_import:
            raise ValueError("dry_run and resume_after_import are mutually exclusive")

        validations: List[ValidationResult] = []
        geometry: Optional[GeometryModel] = None
        snapshot: Optional[ModelSnapshot] = None
        gbxml_path: Optional[Path] = None
        mode = (
            "DRY_RUN"
            if dry_run
            else "VE_RESUME_AFTER_IMPORT"
            if resume_after_import
            else "VE_MUTATION"
        )
        try:
            self.asset_manifest = self._load_create_mode_manifest()
            if self.asset_manifest:
                asset_results = self.validator.validate_asset_manifest(
                    self.asset_manifest
                )
                validations.extend(asset_results)
                self._audit(
                    "preflight",
                    "load and validate source-traced VE asset manifest",
                    worst_status(asset_results).value,
                    {
                        "path": self.asset_manifest.source_path,
                        "sha256": self.asset_manifest.source_checksum,
                    },
                )
            self._audit("preflight", "validate configuration", "STARTED")
            planned = (
                self.asset_manifest.planned_parameter_names
                if self.asset_manifest
                else None
            )
            validations.extend(
                self.validator.validate_configuration(self.parameters, planned)
            )
            self._audit(
                "preflight",
                "validate configuration",
                worst_status(validations).value,
            )

            geometry = self.geometry_factory()
            geometry_results = self.validator.validate_geometry(geometry, self.parameters)
            validations.extend(geometry_results)
            self._audit(
                "geometry",
                "generate and validate deterministic geometry",
                worst_status(geometry_results).value,
                {
                    "spaces": len(geometry.spaces),
                    "surfaces": len(geometry.surfaces),
                    "openings": len(geometry.openings),
                    "shades": len(geometry.shades),
                },
            )

            gbxml_path = GbxmlWriter(self.parameters).write(
                geometry,
                self.output_folder / "geometry" / self.geometry_artifact_name,
            )
            self._audit(
                "geometry",
                "write gbXML artifact",
                "PASS",
                {"path": str(gbxml_path)},
            )

            if worst_status(validations) == ValidationStatus.FAIL:
                self._audit(
                    "gate",
                    "pre-mutation validation gate",
                    "BLOCKED",
                    {"reason": "configuration or geometry failure"},
                )
                artifacts = self._write_report(
                    validations, geometry, snapshot, mode, gbxml_path
                )
                return WorkflowOutcome(
                    status=ValidationStatus.FAIL,
                    message="VE mutation blocked by fail-closed preflight; see report",
                    artifacts=artifacts,
                    validation_results=validations,
                    snapshot=None,
                )

            if dry_run:
                validations.append(
                    ValidationResult(
                        control_id="RUN-DRY-001",
                        category="Workflow",
                        status=ValidationStatus.WARNING,
                        message="Dry run completed; no VE model mutation or post-import validation was performed",
                    )
                )
                self._audit("workflow", "dry run", "WARNING")
                artifacts = self._write_report(
                    validations, geometry, snapshot, mode, gbxml_path
                )
                return WorkflowOutcome(
                    status=ValidationStatus.WARNING,
                    message="Dry run completed",
                    artifacts=artifacts,
                    validation_results=validations,
                    snapshot=None,
                )

            capabilities = self.gateway.check_capabilities()
            self._audit(
                "ve_api", "check required capabilities", "PASS", capabilities
            )
            expected_names = [space.name for space in geometry.spaces]
            if not resume_after_import:
                self.gateway.assert_no_existing_generated_rooms(expected_names)
                self._audit("ve_api", "check duplicate generated rooms", "PASS")

            if self.asset_manifest:
                self.provisioning_receipt = self.gateway.provision_assets(
                    self.asset_manifest
                )
                self.parameters = self.parameters.with_overrides(
                    self.provisioning_receipt.parameter_overrides
                )
                for index, warning in enumerate(
                    self.provisioning_receipt.compatibility_warnings, start=1
                ):
                    validations.append(
                        ValidationResult(
                            control_id="VE-COMPAT-{:03d}".format(index),
                            category="VE Runtime Compatibility",
                            status=ValidationStatus.WARNING,
                            message=str(warning.get("message", "VE compatibility warning")),
                            evidence=warning,
                        )
                    )
                refreshed_configuration = self.validator.validate_configuration(
                    self.parameters
                )
                configuration_ids = {
                    result.control_id
                    for result in validations
                    if result.control_id.startswith("CFG-")
                }
                validations = [
                    result
                    for result in validations
                    if result.control_id not in configuration_ids
                ]
                validations.extend(refreshed_configuration)
                if worst_status(refreshed_configuration) == ValidationStatus.FAIL:
                    raise ReferenceModelError(
                        "Provisioned asset identifiers did not close configuration gates"
                    )
                self._audit(
                    "ve_mutation",
                    "create and verify profiles, CDB assets and thermal template",
                    (
                        "WARNING"
                        if self.provisioning_receipt.compatibility_warnings
                        else "PASS"
                    ),
                    self.provisioning_receipt.to_dict(),
                )

            if resume_after_import:
                self._audit(
                    "ve_mutation",
                    "reuse previously imported generated geometry",
                    "PASS",
                    {"expected_rooms": expected_names},
                )
            else:
                self.gateway.import_geometry(gbxml_path)
                self._audit("ve_mutation", "import generated gbXML", "PASS")

            # Validate imported room creation before any further assignments.
            import_snapshot = self.gateway.snapshot(geometry, self.parameters)
            import_results = self.validator.validate_model_snapshot(
                import_snapshot, self.parameters, geometry
            )
            zone_results = [
                result
                for result in import_results
                if result.control_id in ("VE-ZONE-001", "VE-ZONE-002")
            ]
            validations.extend(zone_results)
            if worst_status(zone_results) == ValidationStatus.FAIL:
                raise ReferenceModelError(
                    "Imported room geometry failed immediate object validation"
                )
            self._audit("ve_validation", "validate imported rooms", "PASS")

            self.gateway.assign_constructions(geometry, self.parameters)
            self._audit(
                "ve_mutation", "assign and verify constructions/openings", "PASS"
            )
            self.gateway.rebuild_adjacencies()
            self._audit("ve_mutation", "rebuild adjacencies", "PASS")
            self.gateway.verify_construction_assignments(geometry, self.parameters)
            self._audit(
                "ve_validation",
                "verify constructions against finalized surface types",
                "PASS",
            )
            self.gateway.assign_thermal_template(geometry, self.parameters)
            runtime_warnings = self.gateway.consume_runtime_compatibility_warnings()
            for index, warning in enumerate(runtime_warnings, start=1):
                validations.append(
                    ValidationResult(
                        control_id="VE-RUNTIME-COMPAT-{:03d}".format(index),
                        category="VE Runtime Compatibility",
                        status=ValidationStatus.WARNING,
                        message=str(
                            warning.get(
                                "message", "VE runtime compatibility workaround"
                            )
                        ),
                        object_id=str(warning.get("room_id", "")) or None,
                        evidence=warning,
                    )
                )
            self._audit(
                "ve_mutation",
                "assign and verify thermal template",
                "WARNING" if runtime_warnings else "PASS",
                {"compatibility_warnings": runtime_warnings},
            )
            self.gateway.assign_hvac_if_configured(geometry, self.parameters)
            self._audit("ve_mutation", "assign HVAC if configured", "PASS")
            self.gateway.assign_weather(str(self.parameters.value("weather_file")))
            self._audit("ve_mutation", "assign and verify weather", "PASS")

            snapshot = self.gateway.snapshot(geometry, self.parameters)
            final_results = self.validator.validate_model_snapshot(
                snapshot, self.parameters, geometry
            )
            # Replace the preliminary zone controls with final controls.
            preliminary_ids = {result.control_id for result in zone_results}
            validations = [
                result
                for result in validations
                if result.control_id not in preliminary_ids
            ]
            validations.extend(final_results)
            final_status = worst_status(validations)
            self._audit(
                "ve_validation",
                "run full post-mutation validation",
                final_status.value,
            )
            artifacts = self._write_report(
                validations, geometry, snapshot, mode, gbxml_path
            )
            return WorkflowOutcome(
                status=final_status,
                message="Reference-model workflow completed with status {}".format(
                    final_status.value
                ),
                artifacts=artifacts,
                validation_results=validations,
                snapshot=snapshot,
            )
        except Exception as exc:
            self.logger.exception("Reference-model workflow failed")
            validations.append(
                ValidationResult(
                    control_id="RUN-ERR-001",
                    category="Workflow",
                    status=ValidationStatus.FAIL,
                    message="Controlled workflow failure: {}".format(exc),
                    evidence={"exception_type": type(exc).__name__},
                )
            )
            self._audit(
                "workflow",
                "handle failure and emit audit artifacts",
                "FAIL",
                {"exception_type": type(exc).__name__, "message": str(exc)},
            )
            artifacts = self._write_report(
                validations, geometry, snapshot, mode, gbxml_path
            )
            return WorkflowOutcome(
                status=ValidationStatus.FAIL,
                message=str(exc),
                artifacts=artifacts,
                validation_results=validations,
                snapshot=snapshot,
            )
