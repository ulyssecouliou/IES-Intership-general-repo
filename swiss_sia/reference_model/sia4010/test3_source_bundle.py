"""Source-bound, pre-mutation generator contract for SIA 4010 Test 3."""

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple, Union

from ..exceptions import ConfigurationError
from .case_manifest import Sia4010CaseManifest
from .distribution_reference import DISTRIBUTION_CRITERIA
from .external_input_manifest import (
    EXTERNAL_INPUT_FILENAME,
    Sia4010ExternalInputManifest,
    external_input_readiness,
)
from .official_input_contract import Sia4010OfficialInputContract
from .preparation_bundle import prepare_case
from .test3_external_bindings import (
    SHADING_CONTROL_IDS,
    Test3ExternalBindings,
    load_test3_external_bindings,
)
from .workbook_loaders import parse_test3_reference_bands


TEST3_VARIANTS = tuple("test_3{}".format(letter) for letter in "ABCDEFGHIJKL")
GENERATOR_INPUT_SCHEMA_VERSION = "1.0"
GENERATOR_INPUT_FILENAME = "generator_input.json"
AUDIT_FILENAME = "source_binding_audit.json"
RUNTIME_BLOCKERS = (
    "SIA3874_CONTROL_AST_INTERPRETER_NOT_IMPLEMENTED",
    "VE_TEST3_SHADING_CONTROL_BINDING_NOT_QUALIFIED",
    "VE_TEST3_DAYLIGHT_SENSOR_BINDING_NOT_QUALIFIED",
    "VE_TEST3_LIGHTING_CONTROL_BINDING_NOT_QUALIFIED",
    "VE_TEST3_APS_BINDINGS_NOT_QUALIFIED",
)
MISSING_NATIVE_PROFILE_GRAPH_BLOCKER = (
    "SIA2024_NATIVE_VE_PROFILE_GRAPH_NOT_SUPPLIED"
)
AUTHORITY_MAPPING_BLOCKER = (
    "TEST3_3K_3L_AUTHORITY_DECISION_RUNTIME_MAPPING_NOT_IMPLEMENTED"
)


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest of one source-bound artifact."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write one source-binding JSON artifact atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


@dataclass(frozen=True)
class Test3SourceBundleReceipt:
    """Paths and conservative readiness state for one exact Test 3 case."""

    status: str
    target_class: str
    variant: str
    case_id: str
    generator_input_path: Path
    generator_input_sha256: str
    audit_path: Path
    external_manifest_path: Path
    preparation_audit_path: Path
    runtime_blockers: Tuple[str, ...]
    mutation_supported: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the source bundle receipt with portable path values."""

        payload = asdict(self)
        for key in (
            "generator_input_path",
            "audit_path",
            "external_manifest_path",
            "preparation_audit_path",
        ):
            payload[key] = str(payload[key])
        payload["runtime_blockers"] = list(self.runtime_blockers)
        return payload


def _geometry_consistency_checks(
    manifest: Sia4010CaseManifest,
    bindings: Test3ExternalBindings,
) -> Dict[str, Dict[str, Any]]:
    """Verify identical geometry values across specification and normalized inputs."""

    expected = {
        "cell_width_m": bindings.common.iso_cell.width_m,
        "cell_depth_m": bindings.common.iso_cell.depth_m,
        "cell_height_m": bindings.common.iso_cell.height_m,
        "south_window_count": bindings.common.iso_cell.window_count,
        "south_window_width_m": bindings.common.iso_cell.window_width_m,
        "south_window_height_m": bindings.common.iso_cell.window_height_m,
        "south_window_sill_m": bindings.common.iso_cell.window_sill_m,
        "south_window_side_margin_m": (
            bindings.common.iso_cell.window_side_margin_m
        ),
        "south_window_gap_m": bindings.common.iso_cell.window_gap_m,
    }
    checks = {}
    for parameter_id, normalized_value in expected.items():
        specification_value = manifest.value(parameter_id)
        matches = (
            int(specification_value) == int(normalized_value)
            if parameter_id == "south_window_count"
            else abs(float(specification_value) - float(normalized_value))
            <= 1.0e-9
        )
        checks[parameter_id] = {
            "status": "PASS" if matches else "FAIL",
            "specification_value": specification_value,
            "normalized_iso_value": normalized_value,
        }
    failed = [
        key for key, result in checks.items() if result["status"] != "PASS"
    ]
    if failed:
        raise ConfigurationError(
            "Test 3 source conflict between SIA geometry and normalized ISO "
            "input: {}".format(failed)
        )
    return checks


def _selected_annual_band(
    workbook_path: Path,
    case_id: str,
) -> Dict[str, Any]:
    """Select exactly one official annual reference band for the case."""

    expected_label = "Test 3 {}".format(case_id[-1])
    matches = [
        item
        for item in parse_test3_reference_bands(
            workbook_path,
            source_checksum=_sha256(workbook_path),
        )
        if item.case_id == expected_label
    ]
    if len(matches) != 1:
        raise ConfigurationError(
            "Expected exactly one official annual band for {}, found {}".format(
                case_id, len(matches)
            )
        )
    return matches[0].to_dict()


def _distribution_contract() -> Dict[str, Any]:
    """Build the official Test 3 hourly distribution comparison contract."""

    contract = DISTRIBUTION_CRITERIA["3"]
    return {
        "case_ids": list(contract["case_ids"]),
        "quantities": [
            {
                "header_label": item.header_label,
                "legend_key": item.legend_key,
            }
            for item in contract["quantities"]
        ],
        "data_prefix": str(contract["data_prefix"]),
        "candidate_sheet": str(contract["candidate_sheet"]),
        "criterion": (
            "Candidate hourly whole-room lighting-power frequency "
            "distribution must remain within the official reference-program "
            "scatter band."
        ),
    }


def build_test3_source_bound_bundle(
    project_root: Union[str, Path],
    repository_root: Union[str, Path],
    target_class: str,
    variant: str,
    case_id: str,
) -> Test3SourceBundleReceipt:
    """Write a complete Test 3 source contract without touching VE."""

    project = Path(project_root)
    repository = Path(repository_root)
    if not project.is_dir():
        raise ConfigurationError(
            "Test 3 source binding requires a saved project directory: "
            "{}".format(project)
        )
    if variant not in TEST3_VARIANTS or case_id != variant[5:]:
        raise ConfigurationError(
            "Test 3 source binding requires one exact test_3A-test_3L pair"
        )
    external_manifest_path = project / EXTERNAL_INPUT_FILENAME
    if not external_manifest_path.is_file():
        raise ConfigurationError(
            "Test 3 requires project external-input manifest: {}".format(
                external_manifest_path
            )
        )
    external_manifest = Sia4010ExternalInputManifest.load(
        external_manifest_path
    )
    readiness = external_input_readiness(
        project,
        variant,
        case_id,
        manifest=external_manifest,
    )
    bindings = load_test3_external_bindings(readiness)
    preparation = prepare_case(
        project,
        repository,
        target_class,
        variant,
        case_id,
        _external_inputs=external_manifest,
    )
    if preparation.geometry_artifact_path is None:
        raise ConfigurationError(
            "Test 3 preparation did not produce deterministic geometry"
        )

    geometry_manifest_path = (
        repository / "config" / "sia4010_classes_1a_1b.json"
    )
    geometry_manifest = Sia4010CaseManifest.load(geometry_manifest_path)
    geometry_checks = _geometry_consistency_checks(
        geometry_manifest, bindings
    )
    official_contract_path = (
        repository / "config" / "sia4010_official_input_contract.json"
    )
    official_contract = Sia4010OfficialInputContract.load(
        official_contract_path
    )
    test3 = official_contract.test("3")
    official_matrix = dict(
        official_contract.payload["tests"]["3"]["variant_matrix"]
    )
    if set(official_matrix) != {
        "3{}".format(letter) for letter in "ABCDEFGHIJKL"
    }:
        raise ConfigurationError("Official Test 3 variant matrix is incomplete")
    selected_pair = tuple(official_matrix[case_id])
    if len(selected_pair) != 2:
        raise ConfigurationError(
            "Official Test 3 pair must contain shade and lighting controls"
        )
    shade_id, lighting_id = selected_pair
    shading_control = (
        bindings.controls.control(shade_id).to_dict()
        if shade_id in SHADING_CONTROL_IDS
        else None
    )
    try:
        lighting_control = bindings.controls.control(lighting_id).to_dict()
    except KeyError as exc:
        raise ConfigurationError(
            "Official Test 3 matrix references unavailable lighting control "
            "{}".format(lighting_id)
        ) from exc

    result_workbook = (
        repository
        / "SIA_4010_geteilter_Link"
        / "Test3"
        / "Resultaterfassung_Test3.xlsx"
    )
    if not result_workbook.is_file():
        raise ConfigurationError(
            "Official Test 3 result workbook is missing: {}".format(
                result_workbook
            )
        )
    annual_band = _selected_annual_band(result_workbook, case_id)
    profile_graph = bindings.common.office_profiles.ve_profile_graph
    blockers = list(RUNTIME_BLOCKERS)
    if profile_graph is None:
        blockers.append(MISSING_NATIVE_PROFILE_GRAPH_BLOCKER)
    if case_id in {"3K", "3L"}:
        if bindings.authority_decision is None:
            raise ConfigurationError(
                "Test 3K/3L requires a source-bound authority decision"
            )
        blockers.append(AUTHORITY_MAPPING_BLOCKER)
    elif shading_control is None:
        raise ConfigurationError(
            "Official Test 3 matrix references unavailable shading control "
            "{}".format(shade_id)
        )
    status = "SOURCE_BOUND_RUNTIME_QUALIFICATION_REQUIRED"
    if profile_graph is None:
        status = "SOURCE_BOUND_PROFILE_GRAPH_REQUIRED"

    artifact_directory = (
        project
        / "sia4010_artifacts"
        / "model_builder"
        / "test3"
        / case_id
    )
    generator_input_path = artifact_directory / GENERATOR_INPUT_FILENAME
    audit_path = artifact_directory / AUDIT_FILENAME
    generator_input = {
        "schema_version": GENERATOR_INPUT_SCHEMA_VERSION,
        "scenario_id": "SIA4010_{}_{}".format(
            str(target_class).upper(), case_id
        ),
        "target_class": str(target_class).upper(),
        "variant": variant,
        "case_id": case_id,
        "geometry_and_lightweight_opaque_envelope": (
            bindings.common.iso_cell.to_dict()
        ),
        "weather": bindings.common.weather.to_dict(),
        "sia2024_office_profiles": (
            bindings.common.office_profiles.to_dict()
        ),
        "official_test3_parameters": dict(test3.confirmed_inputs),
        "official_variant_matrix": official_matrix,
        "selected_control_pair": {
            "shade_control_id": shade_id,
            "lighting_control_id": lighting_id,
            "shading_control": shading_control,
            "lighting_control": lighting_control,
            "authority_decision": (
                bindings.authority_decision.to_dict()
                if bindings.authority_decision is not None
                else None
            ),
        },
        "sia3874_controls": bindings.controls.to_dict(),
        "shading_device": bindings.shading_device.to_dict(),
        "official_evaluation_contract": {
            "required_results": list(
                official_contract.payload["tests"]["3"]["required_results"]
            ),
            "mandatory_criteria": list(
                official_contract.payload["tests"]["3"][
                    "mandatory_criteria"
                ]
            ),
            "annual_reference_band": annual_band,
            "hourly_distribution": _distribution_contract(),
        },
        "source_contracts": {
            "external_manifest": {
                "path": str(external_manifest_path.resolve()),
                "sha256": _sha256(external_manifest_path),
            },
            "official_test3_contract": {
                "path": str(official_contract_path.resolve()),
                "sha256": _sha256(official_contract_path),
            },
            "geometry_manifest": {
                "path": str(geometry_manifest_path.resolve()),
                "sha256": _sha256(geometry_manifest_path),
            },
            "official_test3_result_workbook": {
                "path": str(result_workbook.resolve()),
                "sha256": _sha256(result_workbook),
            },
            "prepared_geometry": {
                "path": str(preparation.geometry_artifact_path.resolve()),
                "sha256": _sha256(preparation.geometry_artifact_path),
            },
            "normalized_binding_sha256": dict(bindings.evidence_sha256),
        },
        "runtime_contract": {
            "mutation_supported": False,
            "mutation_performed": False,
            "simulation_performed": False,
            "compliance_claim_allowed": False,
            "blockers": blockers,
            "required_readbacks": [
                "exact imported ISO test cell geometry",
                "source-bound opaque and glazed constructions",
                "source-bound shading-device optical states",
                "source-bound Table 9 shading control",
                "source-bound Table 10 lighting control",
                "daylight sensor coordinates and workplane semantics",
                "whole-room hourly lighting power in kW",
                "authorized SIA 2028 weather identity",
            ],
        },
        "claim_guardrail": (
            "This artifact is a source-bound pre-mutation contract. It is not "
            "a VE model, simulation result, SIA comparison or attestation."
        ),
    }
    _write_json(generator_input_path, generator_input)
    generator_sha = _sha256(generator_input_path)
    audit = {
        "schema_version": "1.0",
        "status": status,
        "target_class": str(target_class).upper(),
        "variant": variant,
        "case_id": case_id,
        "generator_input": {
            "path": str(generator_input_path),
            "sha256": generator_sha,
        },
        "preparation_audit": str(preparation.audit_path),
        "external_input_readiness": readiness.to_dict(),
        "geometry_consistency_checks": geometry_checks,
        "selected_control_pair": {
            "shade_control_id": shade_id,
            "lighting_control_id": lighting_id,
        },
        "runtime_blockers": blockers,
        "mutation_supported": False,
        "mutation_performed": False,
        "simulation_performed": False,
        "compliance_claim_allowed": False,
        "claim_guardrail": generator_input["claim_guardrail"],
    }
    _write_json(audit_path, audit)
    return Test3SourceBundleReceipt(
        status=status,
        target_class=str(target_class).upper(),
        variant=variant,
        case_id=case_id,
        generator_input_path=generator_input_path,
        generator_input_sha256=generator_sha,
        audit_path=audit_path,
        external_manifest_path=external_manifest_path,
        preparation_audit_path=preparation.audit_path,
        runtime_blockers=tuple(blockers),
    )
