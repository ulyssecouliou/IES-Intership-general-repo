"""Source-traced preparation artifacts for every SIA 4010 class and case.

Preparation is deliberately useful even before a VE generator exists: it
verifies the immutable official package, records the exact specification and
evaluation files, reports input and implementation blockers, and gives the UI
a deterministic next action.  It does not fabricate geometry or mutate VE.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from ...config import SIA4010_CLASS_TEST_MATRIX
from ..config_loader import load_configuration
from ..exceptions import ConfigurationError
from ..gbxml_writer import GbxmlWriter
from .case_manifest import Sia4010CaseManifest
from .case_registry import get_case_capability
from .case_geometry import (
    Sia4010CellGeometryGenerator,
    validate_cell_geometry,
)
from .external_input_manifest import (
    EXTERNAL_INPUT_FILENAME,
    Sia4010ExternalInputManifest,
    build_external_input_matrix,
    external_input_readiness,
)
from .ifc_space_extractor import AbstractBimIfcSpaceExtractor
from .model_scenario import TEST_CASES
from .official_input_contract import Sia4010OfficialInputContract
from .test_loader import BundleFile, OfficialTestBundle, Sia4010TestLoader

_OFFICIAL_IFC_SPACE_NUMBERS = {
    "4": ("101",),
    "5": ("100", "102", "200", "201", "202", "203", "204", "205"),
    "6": ("001", "002"),
}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Write a deterministic UTF-8 JSON artifact."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    """Return the lowercase SHA-256 digest of one local file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_files(
    bundle: OfficialTestBundle, test_id: str, roles: Tuple[str, ...]
) -> Tuple[BundleFile, ...]:
    """Return all verified official files required by one preparation record."""

    selected = tuple(
        item for item in bundle.files if test_id in item.test_ids and item.role in roles
    )
    available_roles = {item.role for item in selected}
    missing_roles = sorted(set(roles) - available_roles)
    if missing_roles:
        raise ConfigurationError(
            "Official Test {} bundle is missing required roles: {}".format(
                test_id, missing_roles
            )
        )
    return selected


@dataclass(frozen=True)
class CasePreparationReceipt:
    """Project-local preparation result for one exact official model case."""

    status: str
    target_class: str
    variant: str
    case_id: str
    audit_path: Path
    case_manifest_path: Path
    config_path: Path
    asset_manifest_path: Path
    mutation_supported: bool
    blockers: Tuple[str, ...]
    geometry_artifact_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe receipt."""

        payload = asdict(self)
        for key in (
            "audit_path",
            "case_manifest_path",
            "config_path",
            "asset_manifest_path",
            "geometry_artifact_path",
        ):
            payload[key] = str(payload[key]) if payload[key] is not None else None
        payload["blockers"] = list(self.blockers)
        return payload


@dataclass(frozen=True)
class ClassPreparationReceipt:
    """Project-local preparation index for one validation class."""

    status: str
    target_class: str
    audit_path: Path
    cases: Tuple[CasePreparationReceipt, ...]
    mutation_ready_cases: int
    blocked_cases: int

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe receipt."""

        return {
            "status": self.status,
            "target_class": self.target_class,
            "audit_path": str(self.audit_path),
            "mutation_ready_cases": self.mutation_ready_cases,
            "blocked_cases": self.blocked_cases,
            "cases": [item.to_dict() for item in self.cases],
        }


@dataclass(frozen=True)
class AllClassesPreparationReceipt:
    """Project-local preparation index for all eight validation classes."""

    status: str
    audit_path: Path
    classes: Tuple[ClassPreparationReceipt, ...]
    exact_case_occurrences: int
    unique_exact_cases: int
    geometry_artifact_occurrences: int
    unique_geometry_artifact_cases: int
    mutation_ready_occurrences: int
    blocked_occurrences: int

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe receipt."""

        return {
            "status": self.status,
            "audit_path": str(self.audit_path),
            "exact_case_occurrences": self.exact_case_occurrences,
            "unique_exact_cases": self.unique_exact_cases,
            "geometry_artifact_occurrences": self.geometry_artifact_occurrences,
            "unique_geometry_artifact_cases": self.unique_geometry_artifact_cases,
            "mutation_ready_occurrences": self.mutation_ready_occurrences,
            "blocked_occurrences": self.blocked_occurrences,
            "classes": [item.to_dict() for item in self.classes],
        }


def prepare_case(
    project_root: Union[str, Path],
    repository_root: Union[str, Path],
    target_class: str,
    variant: str,
    case_id: str,
    *,
    bundle_root: Optional[Union[str, Path]] = None,
    _verified_bundle: Optional[OfficialTestBundle] = None,
    _case_manifest: Optional[Sia4010CaseManifest] = None,
    _official_inputs: Optional[Sia4010OfficialInputContract] = None,
    _external_inputs: Optional[Sia4010ExternalInputManifest] = None,
    _ifc_extractor: Optional[AbstractBimIfcSpaceExtractor] = None,
) -> CasePreparationReceipt:
    """Verify and record one exact case without changing the VE model."""

    project = Path(project_root)
    repository = Path(repository_root)
    class_id = str(target_class).strip().upper()
    if class_id not in SIA4010_CLASS_TEST_MATRIX:
        raise ConfigurationError(
            "Unsupported SIA 4010 validation class: {}".format(target_class)
        )
    if variant not in SIA4010_CLASS_TEST_MATRIX[class_id]:
        raise ConfigurationError(
            "{} is not required by SIA 4010 class {}".format(variant, class_id)
        )
    capability = get_case_capability(variant, case_id)
    official_root = (
        Path(bundle_root)
        if bundle_root is not None
        else repository / "SIA_4010_geteilter_Link"
    )
    bundle = _verified_bundle or Sia4010TestLoader().load_bundle(official_root)
    sources = _source_files(
        bundle, capability.base_test_id, capability.required_source_roles
    )

    case_manifest_path = repository / "config" / "sia4010_all_classes.json"
    cell_geometry_manifest_path = repository / "config" / "sia4010_classes_1a_1b.json"
    config_path = repository / "config" / "reference_model_config.json"
    asset_path = repository / "config" / "reference_model_assets.json"
    manifest = _case_manifest or Sia4010CaseManifest.load(case_manifest_path)
    readiness = manifest.case_readiness(variant, case_id)
    delegated_inputs = external_input_readiness(
        project,
        variant,
        case_id,
        manifest=_external_inputs,
    )
    input_contract_path = repository / "config" / "sia4010_official_input_contract.json"
    official_inputs = _official_inputs
    if official_inputs is None and capability.base_test_id != "1":
        official_inputs = Sia4010OfficialInputContract.load(input_contract_path)
    extracted_input = (
        official_inputs.test(capability.base_test_id).to_dict()
        if official_inputs is not None and capability.base_test_id != "1"
        else None
    )
    official_ifc_spaces = None
    if capability.base_test_id in _OFFICIAL_IFC_SPACE_NUMBERS:
        ifc_sources = tuple(
            item for item in sources if item.role == "example_building_ifc"
        )
        if len(ifc_sources) != 1:
            raise ConfigurationError(
                "Official Test {} preparation expected exactly one IFC source, "
                "found {}".format(capability.base_test_id, len(ifc_sources))
            )
        extractor = _ifc_extractor or AbstractBimIfcSpaceExtractor(ifc_sources[0].path)
        if Path(extractor.path).resolve() != Path(ifc_sources[0].path).resolve():
            raise ConfigurationError(
                "Cached official IFC extractor does not match the verified "
                "source selected for Test {}".format(capability.base_test_id)
            )
        official_ifc_spaces = {
            number: record.to_dict()
            for number, record in extractor.extract(
                _OFFICIAL_IFC_SPACE_NUMBERS[capability.base_test_id]
            ).items()
        }
    blockers = list(readiness.missing_parameters)
    blockers.extend(
        "EXTERNAL_INPUT:{}".format(input_id)
        for input_id in delegated_inputs.blocked_input_ids
    )
    if not capability.mutation_supported:
        blockers.append(capability.blocker_code)

    scenario_id = "SIA4010_{}_{}".format(class_id, case_id)
    artifact_path = (
        project
        / "sia4010_artifacts"
        / "model_builder"
        / "{}_preparation.json".format(scenario_id)
    )
    status = (
        "READY_FOR_GUARDED_MUTATION"
        if (
            capability.mutation_supported
            and not readiness.missing_parameters
            and delegated_inputs.ready_for_binding
        )
        else "PREPARED_WITH_BLOCKERS"
    )
    geometry_artifact_path = None
    geometry_audit_path = None
    geometry_validation = None
    if capability.geometry_artifact_supported:
        geometry_manifest = Sia4010CaseManifest.load(cell_geometry_manifest_path)
        parameters = load_configuration(config_path)
        geometry = Sia4010CellGeometryGenerator(geometry_manifest).generate(
            identifier="SIA4010_{}_{}".format(
                capability.variant.upper(),
                capability.case_id.upper(),
            )
        )
        validation = validate_cell_geometry(geometry, geometry_manifest)
        if not validation.passed:
            raise ConfigurationError(
                "Source-qualified SIA 4010 cell geometry failed validation: "
                "{}".format(validation.checks)
            )
        shared_geometry_stem = "SIA4010_{}_{}".format(variant, case_id)
        shared_geometry_directory = artifact_path.parent / "geometry"
        geometry_artifact_path = shared_geometry_directory / (
            "{}.gbxml".format(shared_geometry_stem)
        )
        geometry_audit_path = shared_geometry_directory / (
            "{}_geometry.json".format(shared_geometry_stem)
        )
        GbxmlWriter(parameters).write(geometry, geometry_artifact_path)
        geometry_validation = {
            "status": validation.status,
            "checks": validation.checks,
        }
        _write_json(
            geometry_audit_path,
            {
                "schema_version": "1.0",
                "scenario_id": scenario_id,
                "variant": variant,
                "case_id": case_id,
                "geometry_validation": geometry_validation,
                "geometry": geometry.to_dict(),
                "gbxml_path": str(geometry_artifact_path),
                "geometry_input_manifest": {
                    "path": str(cell_geometry_manifest_path),
                    "sha256": _sha256(cell_geometry_manifest_path),
                },
                "claim_guardrail": (
                    "This is a deterministic geometry preparation artifact. "
                    "No VE construction, template, control or simulation "
                    "capability is implied."
                ),
            },
        )
    payload = {
        "schema_version": "1.0",
        "status": status,
        "scenario_id": scenario_id,
        "target_class": class_id,
        "variant": variant,
        "case_id": case_id,
        "official_bundle": {
            "root": str(bundle.root),
            "manifest": str(bundle.manifest_path),
            "manifest_sha256": _sha256(bundle.manifest_path),
            "issued_by": bundle.issued_by,
            "verified": True,
        },
        "source_files": [
            {
                "path": str(item.path),
                "role": item.role,
                "sha256": item.sha256,
                "test_ids": list(item.test_ids),
            }
            for item in sources
        ],
        "input_readiness": readiness.to_dict(),
        "external_input_readiness": delegated_inputs.to_dict(),
        "confirmed_specification_input": extracted_input,
        "confirmed_specification_input_contract": (
            str(input_contract_path) if extracted_input is not None else None
        ),
        "official_ifc_spaces": official_ifc_spaces,
        "geometry_source_status": (
            "DETERMINISTIC_GBXML_WRITTEN"
            if geometry_artifact_path is not None
            else (
                "EXTRACTED_FROM_VERIFIED_OFFICIAL_IFC"
                if official_ifc_spaces is not None
                else "NOT_APPLICABLE_TO_THIS_TEST"
            )
        ),
        "prepared_geometry": {
            "gbxml_path": (
                str(geometry_artifact_path)
                if geometry_artifact_path is not None
                else None
            ),
            "audit_path": (
                str(geometry_audit_path) if geometry_audit_path is not None else None
            ),
            "validation": geometry_validation,
        },
        "generator_capability": capability.to_dict(),
        "pipeline": {
            "official_sources": "PASS",
            "deterministic_geometry_artifact": (
                "READY"
                if capability.geometry_artifact_supported
                else (
                    "SOURCE_IFC_EXTRACTED"
                    if official_ifc_spaces is not None
                    else "BLOCKED"
                )
            ),
            "exact_input_binding": (
                "PASS" if not readiness.missing_parameters else "BLOCKED"
            ),
            "delegated_external_inputs": delegated_inputs.status,
            "ve_model_generation": (
                "READY" if capability.mutation_supported else "BLOCKED"
            ),
            "apache_simulation": "PENDING_MODEL",
            "aps_extraction": "PENDING_SIMULATION",
            "official_comparison": "READY_FOR_RESULTS",
            "class_attestation": "EXTERNAL_SIA_REVIEW_REQUIRED",
        },
        "blockers": [
            {
                "code": parameter_id,
                "detail": manifest.parameters[parameter_id]["description"],
                "source_required": manifest.parameters[parameter_id]["source"],
            }
            for parameter_id in readiness.missing_parameters
        ]
        + [
            {
                "code": "EXTERNAL_INPUT:{}".format(item.input_id),
                "detail": "{} Issues: {}".format(
                    item.description,
                    "; ".join(item.issues),
                ),
                "source_required": item.source_required,
            }
            for item in delegated_inputs.evidence
            if not item.ready_for_binding
        ]
        + (
            [
                {
                    "code": capability.blocker_code,
                    "detail": capability.blocker_detail,
                    "source_required": "",
                }
            ]
            if capability.blocker_code
            else []
        ),
        "claim_guardrail": (
            "This artifact proves source and workflow preparation only. It does "
            "not prove that a VE model exists, that APS results pass the official "
            "bands, or that SIA validation has been granted."
        ),
    }
    _write_json(artifact_path, payload)
    return CasePreparationReceipt(
        status=status,
        target_class=class_id,
        variant=variant,
        case_id=case_id,
        audit_path=artifact_path,
        case_manifest_path=case_manifest_path,
        config_path=config_path,
        asset_manifest_path=asset_path,
        mutation_supported=capability.mutation_supported,
        blockers=tuple(blockers),
        geometry_artifact_path=geometry_artifact_path,
    )


def prepare_class(
    project_root: Union[str, Path],
    repository_root: Union[str, Path],
    target_class: str,
    *,
    bundle_root: Optional[Union[str, Path]] = None,
    _verified_bundle: Optional[OfficialTestBundle] = None,
    _case_manifest: Optional[Sia4010CaseManifest] = None,
    _official_inputs: Optional[Sia4010OfficialInputContract] = None,
    _external_inputs: Optional[Sia4010ExternalInputManifest] = None,
    _ifc_extractor: Optional[AbstractBimIfcSpaceExtractor] = None,
) -> ClassPreparationReceipt:
    """Prepare every exact case required by one SIA 4010 validation class."""

    class_id = str(target_class).strip().upper()
    if class_id not in SIA4010_CLASS_TEST_MATRIX:
        raise ConfigurationError(
            "Unsupported SIA 4010 validation class: {}".format(target_class)
        )
    project = Path(project_root)
    repository = Path(repository_root)
    official_root = (
        Path(bundle_root)
        if bundle_root is not None
        else repository / "SIA_4010_geteilter_Link"
    )
    # The official bundle may contain large IFC/DWG/PDF files. Verify every
    # checksum once per class preparation, then reuse the immutable result for
    # each case instead of re-hashing the package dozens of times.
    verified_bundle = _verified_bundle or Sia4010TestLoader().load_bundle(official_root)
    case_manifest = _case_manifest or Sia4010CaseManifest.load(
        repository / "config" / "sia4010_all_classes.json"
    )
    official_inputs = _official_inputs or Sia4010OfficialInputContract.load(
        repository / "config" / "sia4010_official_input_contract.json"
    )
    external_inputs = _external_inputs
    external_input_path = project / EXTERNAL_INPUT_FILENAME
    if external_inputs is None and external_input_path.is_file():
        external_inputs = Sia4010ExternalInputManifest.load(external_input_path)
    class_variants = SIA4010_CLASS_TEST_MATRIX[class_id]
    requires_ifc = any(
        get_case_capability(variant, TEST_CASES[variant][0]).base_test_id
        in _OFFICIAL_IFC_SPACE_NUMBERS
        for variant in class_variants
    )
    ifc_extractor = _ifc_extractor
    if requires_ifc:
        ifc_sources = tuple(
            item for item in verified_bundle.files if item.role == "example_building_ifc"
        )
        unique_ifc_paths = tuple(dict.fromkeys(item.path for item in ifc_sources))
        if len(unique_ifc_paths) != 1:
            raise ConfigurationError(
                "Class {} preparation expected one shared official IFC, found "
                "{}".format(class_id, len(unique_ifc_paths))
            )
        if ifc_extractor is None:
            ifc_extractor = AbstractBimIfcSpaceExtractor(unique_ifc_paths[0])
        elif Path(ifc_extractor.path).resolve() != Path(unique_ifc_paths[0]).resolve():
            raise ConfigurationError(
                "Cached official IFC extractor does not match the verified "
                "class source"
            )
    receipts = tuple(
        prepare_case(
            project_root,
            repository_root,
            class_id,
            variant,
            case_id,
            bundle_root=bundle_root,
            _verified_bundle=verified_bundle,
            _case_manifest=case_manifest,
            _official_inputs=official_inputs,
            _external_inputs=external_inputs,
            _ifc_extractor=ifc_extractor,
        )
        for variant in class_variants
        for case_id in TEST_CASES[variant]
    )
    ready = sum(item.mutation_supported and not item.blockers for item in receipts)
    blocked = len(receipts) - ready
    audit_path = (
        project
        / "sia4010_artifacts"
        / "model_builder"
        / "SIA4010_{}_class_preparation.json".format(class_id)
    )
    payload = {
        "schema_version": "1.0",
        "status": (
            "READY_FOR_AUTONOMOUS_EXECUTION"
            if not blocked
            else "CLASS_PREPARED_WITH_BLOCKERS"
        ),
        "target_class": class_id,
        "required_variants": list(SIA4010_CLASS_TEST_MATRIX[class_id]),
        "exact_case_count": len(receipts),
        "mutation_ready_cases": ready,
        "blocked_cases": blocked,
        "execution_contract": {
            "project_isolation": "ONE_DISPOSABLE_VE_PROJECT_PER_EXACT_CASE",
            "automatic_ve_project_creation_supported": False,
            "reason": (
                "The verified VE Python contract mutates the active project; it "
                "does not expose a qualified API for creating and saving a new "
                "independent VE project for every queued case."
            ),
            "required_pipeline": [
                "prepare_source_traced_inputs",
                "create_or_open_disposable_ve_project",
                "run_guarded_case_generator",
                "run_apachesim_with_official_temporal_settings",
                "extract_qualified_aps_results",
                "compare_annual_official_bands",
                "compare_required_hourly_distributions",
                "write_class_navigator_report",
                "record_external_sia_attestation",
            ],
        },
        "execution_queue": [
            {
                "sequence": index,
                "variant": item.variant,
                "case_id": item.case_id,
                "preparation_artifact": str(item.audit_path),
                "state": (
                    "READY_FOR_ACTIVE_PROJECT_MUTATION"
                    if item.mutation_supported and not item.blockers
                    else "BLOCKED"
                ),
                "blockers": list(item.blockers),
                "next_action": (
                    "Open a saved disposable VE project and run the guarded "
                    "case generator."
                    if item.mutation_supported and not item.blockers
                    else "Resolve the recorded official-input and generator "
                    "implementation blockers."
                ),
            }
            for index, item in enumerate(receipts, start=1)
        ],
        "cases": [item.to_dict() for item in receipts],
        "next_action": (
            "Run each guarded model generator, ApacheSim, APS extraction and "
            "official comparison."
            if not blocked
            else "Resolve the per-case input and VE generator blockers recorded "
            "in the linked preparation artifacts."
        ),
        "claim_guardrail": (
            "Class preparation is not SIA validation and does not authorize a "
            "compliance claim."
        ),
    }
    _write_json(audit_path, payload)
    return ClassPreparationReceipt(
        status=payload["status"],
        target_class=class_id,
        audit_path=audit_path,
        cases=receipts,
        mutation_ready_cases=ready,
        blocked_cases=blocked,
    )


def prepare_all_classes(
    project_root: Union[str, Path],
    repository_root: Union[str, Path],
    *,
    bundle_root: Optional[Union[str, Path]] = None,
) -> AllClassesPreparationReceipt:
    """Prepare all eight classes with one official-bundle verification pass.

    Exact cases shared by several classes remain listed in each class contract
    because class qualification has separate evidence gates. The summary also
    reports the 30 unique variant/case combinations to avoid overstating model
    generator coverage.
    """

    project = Path(project_root)
    repository = Path(repository_root)
    official_root = (
        Path(bundle_root)
        if bundle_root is not None
        else repository / "SIA_4010_geteilter_Link"
    )
    verified_bundle = Sia4010TestLoader().load_bundle(official_root)
    case_manifest = Sia4010CaseManifest.load(
        repository / "config" / "sia4010_all_classes.json"
    )
    official_inputs = Sia4010OfficialInputContract.load(
        repository / "config" / "sia4010_official_input_contract.json"
    )
    external_input_path = project / EXTERNAL_INPUT_FILENAME
    external_inputs = (
        Sia4010ExternalInputManifest.load(external_input_path)
        if external_input_path.is_file()
        else None
    )
    external_input_matrix = build_external_input_matrix(
        project,
        manifest=external_inputs,
    )
    ifc_sources = tuple(
        item for item in verified_bundle.files if item.role == "example_building_ifc"
    )
    unique_ifc_paths = tuple(dict.fromkeys(item.path for item in ifc_sources))
    if len(unique_ifc_paths) != 1:
        raise ConfigurationError(
            "All-class preparation expected one shared official IFC, found "
            "{}".format(len(unique_ifc_paths))
        )
    ifc_extractor = AbstractBimIfcSpaceExtractor(unique_ifc_paths[0])
    classes = tuple(
        prepare_class(
            project,
            repository,
            class_id,
            bundle_root=bundle_root,
            _verified_bundle=verified_bundle,
            _case_manifest=case_manifest,
            _official_inputs=official_inputs,
            _external_inputs=external_inputs,
            _ifc_extractor=ifc_extractor,
        )
        for class_id in SIA4010_CLASS_TEST_MATRIX
    )
    occurrences = sum(len(item.cases) for item in classes)
    ready = sum(item.mutation_ready_cases for item in classes)
    blocked = sum(item.blocked_cases for item in classes)
    unique_cases = {
        (variant, case_id)
        for variant, case_ids in TEST_CASES.items()
        for case_id in case_ids
    }
    geometry_occurrences = sum(
        case.geometry_artifact_path is not None
        for class_receipt in classes
        for case in class_receipt.cases
    )
    unique_geometry_cases = {
        (case.variant, case.case_id)
        for class_receipt in classes
        for case in class_receipt.cases
        if case.geometry_artifact_path is not None
    }
    status = (
        "READY_FOR_AUTONOMOUS_EXECUTION"
        if not blocked
        else "ALL_CLASSES_PREPARED_WITH_BLOCKERS"
    )
    audit_path = (
        project
        / "sia4010_artifacts"
        / "model_builder"
        / "SIA4010_all_classes_preparation.json"
    )
    payload = {
        "schema_version": "1.0",
        "status": status,
        "validation_classes": list(SIA4010_CLASS_TEST_MATRIX),
        "validation_class_count": len(classes),
        "exact_case_occurrences": occurrences,
        "unique_exact_cases": len(unique_cases),
        "geometry_artifact_occurrences": geometry_occurrences,
        "unique_geometry_artifact_cases": len(unique_geometry_cases),
        "mutation_ready_occurrences": ready,
        "blocked_occurrences": blocked,
        "external_input_matrix": external_input_matrix,
        "classes": [item.to_dict() for item in classes],
        "claim_guardrail": (
            "All-class preparation verifies sources and creates execution "
            "contracts. It does not create unsupported VE models, run ApacheSim, "
            "or grant SIA validation."
        ),
    }
    _write_json(audit_path, payload)
    return AllClassesPreparationReceipt(
        status=status,
        audit_path=audit_path,
        classes=classes,
        exact_case_occurrences=occurrences,
        unique_exact_cases=len(unique_cases),
        geometry_artifact_occurrences=geometry_occurrences,
        unique_geometry_artifact_cases=len(unique_geometry_cases),
        mutation_ready_occurrences=ready,
        blocked_occurrences=blocked,
    )
