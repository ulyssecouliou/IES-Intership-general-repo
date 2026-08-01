"""Source-bound generator contract for SIA 4010 Test 2A.

This module creates no VE objects.  It combines the supplied Test 2
specification values with three independently validated external bindings and
writes the exact, checksummed input contract that the future guarded VE
generator must consume.  Runtime mutation remains disabled until the dynamic
awning and SIA 2024 profile setters/read-backs are qualified in VE.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple, Union

from ..exceptions import ConfigurationError
from .case_manifest import Sia4010CaseManifest
from .external_input_manifest import (
    EXTERNAL_INPUT_FILENAME,
    Sia4010ExternalInputManifest,
    external_input_readiness,
)
from .normalized_external_inputs import load_test2a_external_bindings
from .official_input_contract import Sia4010OfficialInputContract
from .test2a_shading_control import (
    build_test2a_fabric_awning_control,
    build_test2a_optical_diagnostic_contract,
)
from .test2a_diagnostic_workbook import (
    load_test2a_diagnostic_workbook_binding,
)
from .qualified_aps import QualifiedApsBindings
from .test2a_diagnostic_aps import (
    build_test2a_2e1_aps_binding_contract,
)


GENERATOR_INPUT_SCHEMA_VERSION = "1.0"
GENERATOR_INPUT_FILENAME = "generator_input.json"
AUDIT_FILENAME = "source_binding_audit.json"
RUNTIME_BLOCKERS = (
    "VE_DYNAMIC_FABRIC_AWNING_BINDING_NOT_QUALIFIED",
    "VE_SIA2024_PROFILE_TYPE_BINDING_NOT_QUALIFIED",
    "VE_TEST2A_ASSET_BUNDLE_NOT_IMPLEMENTED",
)
MISSING_NATIVE_PROFILE_GRAPH_BLOCKER = (
    "SIA2024_NATIVE_VE_PROFILE_GRAPH_NOT_SUPPLIED"
)
QUALIFICATION_REPORT_SPECS = {
    "native_profiles": {
        "pattern": "sia2a_profiles_*.json",
        "required_true": ("mutation_performed",),
        "required_false": (
            "other_ve_objects_changed",
            "simulation_performed",
            "compliance_claim_allowed",
        ),
    },
    "shade_threshold_setters": {
        "pattern": "sia2a_external_shade_setter_*.json",
        "required_true": ("cdb_setter_qualified",),
        "required_false": (
            "dynamic_equivalence_qualified",
            "full_test2a_mutation_authorized",
            "compliance_claim_allowed",
        ),
    },
    "fixed_closed_optical_storage": {
        "pattern": "sia2a_2e1_optical_setter_*.json",
        "required_true": ("fixed_closed_storage_qualified",),
        "required_false": (
            "fixed_closed_optical_mapping_qualified",
            "diagnostic_candidate_generation_authorized",
            "compliance_claim_allowed",
        ),
    },
}

_OFFICIAL_TEST2_REQUIRED_KEYS = (
    "geometry_reference",
    "construction",
    "use_category",
    "infiltration_m3_h_m2",
    "heating_setpoint_c",
    "cooling_setpoint_c",
    "people_count",
    "area_m2_per_person",
    "activity_met",
    "equipment_gain_w_m2",
    "lighting_gain_w_m2",
    "lighting_installed_power_w_m2",
    "glazing_type",
    "glazing_g_value",
    "glazing_u_w_m2k",
    "glazing_visible_transmittance",
    "glazing_visible_reflectance",
    "external_shading_activation_w_m2",
    "variant_2A_shade",
    "variant_2A_combined_g_total",
    "variant_2A_direct_solar_transmittance",
    "variant_2A_outside_solar_reflectance",
    "variant_2A_inside_solar_reflectance",
    "variant_2A_visible_transmittance",
    "variant_2A_outside_visible_reflectance",
    "variant_2A_inside_visible_reflectance",
    "variant_2A_convection_factor",
    "variant_2A_thermal_radiation_factor",
    "variant_2A_ventilation_factor",
    "variant_2A_secondary_internal_heat_transfer_factor",
    "variant_2A_uv_transmittance",
    "variant_2A_reference_combined_g_total",
    "variant_2A_reference_u_w_m2k",
    "variant_2A_iso15099_winter_u_w_m2k",
    "variant_2A_peripheral_gap_m",
    "variant_2A_screen_layer_thickness_m",
)


def _sha256(path: Path) -> str:
    """Return the lowercase SHA-256 digest of one artifact."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write deterministic UTF-8 JSON atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _runtime_qualification_evidence(project: Path) -> Dict[str, Any]:
    """Return checksum- and guardrail-qualified disposable VE receipts."""

    diagnostics = project / "sia4010_artifacts" / "diagnostics"
    evidence: Dict[str, Any] = {}
    for key, specification in QUALIFICATION_REPORT_SPECS.items():
        reports = tuple(
            sorted(diagnostics.glob(str(specification["pattern"])))
        )
        if not reports:
            evidence[key] = {
                "status": "NOT_RUN",
                "qualified": False,
            }
            continue
        if len(reports) != 1:
            evidence[key] = {
                "status": "AMBIGUOUS_REPORT_SET",
                "qualified": False,
                "report_count": len(reports),
                "reports": [str(path) for path in reports],
            }
            continue
        report = reports[0]
        checksum_path = report.with_suffix(report.suffix + ".sha256")
        try:
            expected_sha = checksum_path.read_text(
                encoding="utf-8"
            ).split()[0]
            actual_sha = _sha256(report)
            payload = json.loads(report.read_text(encoding="utf-8"))
        except (IndexError, OSError, ValueError, TypeError) as exc:
            evidence[key] = {
                "status": "INVALID_REPORT",
                "qualified": False,
                "report": str(report),
                "error": "{}: {}".format(type(exc).__name__, exc),
            }
            continue
        scenario = payload.get("scenario", {})
        reported_project = payload.get("project", {}).get("path", "")
        true_fields = tuple(specification["required_true"])
        false_fields = tuple(specification["required_false"])
        guardrails_match = (
            payload.get("status") == "PASS"
            and scenario.get("variant") == "test_2A"
            and scenario.get("case_id") == "2A"
            and Path(str(reported_project)).resolve() == project.resolve()
            and all(payload.get(field) is True for field in true_fields)
            and all(payload.get(field) is False for field in false_fields)
        )
        checksum_matches = expected_sha == actual_sha
        qualified = checksum_matches and guardrails_match
        evidence[key] = {
            "status": "PASS" if qualified else "INVALID_REPORT",
            "qualified": qualified,
            "report": str(report),
            "sha256": actual_sha,
            "checksum_matches": checksum_matches,
            "guardrails_match": guardrails_match,
        }
    evidence["all_storage_boundaries_qualified"] = all(
        item.get("qualified") is True
        for item in evidence.values()
        if isinstance(item, dict)
    )
    return evidence


@dataclass(frozen=True)
class Test2ASourceBundleReceipt:
    """Paths and honest readiness state of the Test 2A source contract."""

    status: str
    generator_input_path: Path
    generator_input_sha256: str
    audit_path: Path
    external_manifest_path: Path
    runtime_blockers: Tuple[str, ...]
    mutation_supported: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe receipt."""

        payload = asdict(self)
        for key in (
            "generator_input_path",
            "audit_path",
            "external_manifest_path",
        ):
            payload[key] = str(payload[key])
        payload["runtime_blockers"] = list(self.runtime_blockers)
        return payload


def _geometry_consistency_checks(
    manifest: Sia4010CaseManifest,
    iso_cell: Any,
) -> Dict[str, Dict[str, Any]]:
    """Compare the two official source paths for the Test 2 cell geometry."""

    expected = {
        "cell_width_m": iso_cell.width_m,
        "cell_depth_m": iso_cell.depth_m,
        "cell_height_m": iso_cell.height_m,
        "south_window_count": iso_cell.window_count,
        "south_window_width_m": iso_cell.window_width_m,
        "south_window_height_m": iso_cell.window_height_m,
        "south_window_sill_m": iso_cell.window_sill_m,
        "south_window_side_margin_m": iso_cell.window_side_margin_m,
        "south_window_gap_m": iso_cell.window_gap_m,
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
    failed = [key for key, value in checks.items() if value["status"] != "PASS"]
    if failed:
        raise ConfigurationError(
            "Test 2A source conflict between the supplied SIA specification "
            "geometry and normalized ISO input: {}".format(failed)
        )
    return checks


def _confirmed_test2_inputs(
    contract: Sia4010OfficialInputContract,
) -> Dict[str, Any]:
    """Return the exact supplied Test 2 fields needed by Case 2A."""

    test2 = contract.test("2")
    missing = [
        key
        for key in _OFFICIAL_TEST2_REQUIRED_KEYS
        if key not in test2.confirmed_inputs
        or test2.confirmed_inputs[key] is None
    ]
    if missing:
        raise ConfigurationError(
            "Official Test 2 contract is missing Case 2A inputs: {}".format(
                missing
            )
        )
    return {
        key: test2.confirmed_inputs[key]
        for key in _OFFICIAL_TEST2_REQUIRED_KEYS
    }


def build_test2a_source_bound_bundle(
    project_root: Union[str, Path],
    repository_root: Union[str, Path],
) -> Test2ASourceBundleReceipt:
    """Write the complete pre-mutation Test 2A generator input contract."""

    project = Path(project_root)
    repository = Path(repository_root)
    if not project.is_dir():
        raise ConfigurationError(
            "Test 2A source binding requires a saved project directory: "
            "{}".format(project)
        )
    external_manifest_path = project / EXTERNAL_INPUT_FILENAME
    if not external_manifest_path.is_file():
        raise ConfigurationError(
            "Test 2A requires project external-input manifest: {}".format(
                external_manifest_path
            )
        )
    external_manifest = Sia4010ExternalInputManifest.load(
        external_manifest_path
    )
    readiness = external_input_readiness(
        project,
        "test_2A",
        "2A",
        manifest=external_manifest,
    )
    bindings = load_test2a_external_bindings(readiness)
    profile_graph = bindings.office_profiles.ve_profile_graph
    qualification_evidence = _runtime_qualification_evidence(project)
    runtime_blockers = RUNTIME_BLOCKERS
    status = "SOURCE_BINDINGS_READY_VE_BINDING_REQUIRED"
    if profile_graph is None:
        runtime_blockers = runtime_blockers + (
            MISSING_NATIVE_PROFILE_GRAPH_BLOCKER,
        )
        status = "SOURCE_BINDINGS_READY_PROFILE_GRAPH_REQUIRED"
    elif qualification_evidence["all_storage_boundaries_qualified"]:
        status = "RUNTIME_STORAGE_QUALIFIED_MODEL_BINDING_REQUIRED"

    geometry_manifest_path = (
        repository / "config" / "sia4010_classes_1a_1b.json"
    )
    official_contract_path = (
        repository / "config" / "sia4010_official_input_contract.json"
    )
    geometry_manifest = Sia4010CaseManifest.load(geometry_manifest_path)
    official_contract = Sia4010OfficialInputContract.load(
        official_contract_path
    )
    geometry_checks = _geometry_consistency_checks(
        geometry_manifest, bindings.iso_cell
    )
    official_inputs = _confirmed_test2_inputs(official_contract)
    shading_control = build_test2a_fabric_awning_control(official_inputs)
    test2_workbook_path = (
        repository
        / "SIA_4010_geteilter_Link"
        / "Test2"
        / "Resultaterfassung_Test2.xlsx"
    )
    diagnostic_workbook_binding = (
        load_test2a_diagnostic_workbook_binding(test2_workbook_path)
    )
    optical_diagnostic = build_test2a_optical_diagnostic_contract(
        shading_control,
        diagnostic_workbook_binding.to_dict(),
    )
    aps_binding_path = (
        repository / "config" / "sia4010_aps_bindings_ve_runtime.json"
    )
    aps_bindings = QualifiedApsBindings.load(aps_binding_path)
    aps_diagnostic_binding = build_test2a_2e1_aps_binding_contract(
        aps_bindings,
        diagnostic_workbook_binding,
    )

    artifact_directory = (
        project / "sia4010_artifacts" / "model_builder" / "test2a"
    )
    generator_input_path = artifact_directory / GENERATOR_INPUT_FILENAME
    audit_path = artifact_directory / AUDIT_FILENAME
    generator_input = {
        "schema_version": GENERATOR_INPUT_SCHEMA_VERSION,
        "scenario_id": "SIA4010_TEST_2A_2A",
        "variant": "test_2A",
        "case_id": "2A",
        "geometry_and_lightweight_opaque_envelope": (
            bindings.iso_cell.to_dict()
        ),
        "weather": bindings.weather.to_dict(),
        "sia2024_office_profiles": bindings.office_profiles.to_dict(),
        "official_test2_parameters": official_inputs,
        "fabric_awning_control": shading_control.to_dict(),
        "fabric_awning_optical_diagnostic": optical_diagnostic.to_dict(),
        "fabric_awning_aps_diagnostic_binding": (
            aps_diagnostic_binding.to_dict()
        ),
        "source_contracts": {
            "external_manifest": {
                "path": str(external_manifest_path.resolve()),
                "sha256": _sha256(external_manifest_path),
            },
            "official_test2_contract": {
                "path": str(official_contract_path.resolve()),
                "sha256": _sha256(official_contract_path),
            },
            "geometry_manifest": {
                "path": str(geometry_manifest_path.resolve()),
                "sha256": _sha256(geometry_manifest_path),
            },
            "official_test2_result_workbook": {
                "path": str(test2_workbook_path.resolve()),
                "sha256": diagnostic_workbook_binding.workbook_sha256,
                "binding_status": diagnostic_workbook_binding.status,
            },
            "normalized_binding_sha256": dict(bindings.evidence_sha256),
        },
        "runtime_contract": {
            "mutation_supported": False,
            "blockers": list(runtime_blockers),
            "qualification_evidence": qualification_evidence,
            "sia2024_native_profile_graph": {
                "present": profile_graph is not None,
                "required_profile_types": (
                    list(profile_graph.required_profile_types)
                    if profile_graph is not None
                    else []
                ),
                "output_nodes": (
                    dict(profile_graph.outputs)
                    if profile_graph is not None
                    else {}
                ),
            },
            "fabric_awning": {
                "cdb_setter_plan_available": True,
                "cdb_setter_plan": shading_control.setter_plan,
                "cdb_setter_plan_scope": "CDB_STORAGE_AND_READBACK_ONLY",
                "dynamic_equivalence_qualified": (
                    shading_control.dynamic_equivalence_qualified
                ),
                "dynamic_equivalence_blockers": list(
                    shading_control.dynamic_equivalence_blockers
                ),
                "optical_diagnostic": optical_diagnostic.to_dict(),
                "aps_diagnostic_binding": aps_diagnostic_binding.to_dict(),
            },
            "required_readbacks": [
                "one imported thermal zone with exact geometry",
                "opaque constructions and ordered layers",
                "Test 2 glazing thermal and optical properties",
                "three SIA 2024 profiles and their calendar semantics",
                "people, equipment and lighting gains",
                "facade-area-specific infiltration",
                "external fabric awning optical state",
                "source threshold value 150 W/m2 stored in candidate VE fields",
                "authorized SIA 2028 weather identity",
            ],
        },
        "claim_guardrail": (
            "This is a source-complete generator input contract, not a VE "
            "model, simulation result, SIA comparison or attestation."
        ),
    }
    _write_json(generator_input_path, generator_input)
    generator_input_sha = _sha256(generator_input_path)
    audit = {
        "schema_version": "1.0",
        "status": status,
        "variant": "test_2A",
        "case_id": "2A",
        "generator_input": {
            "path": str(generator_input_path),
            "sha256": generator_input_sha,
        },
        "external_input_readiness": readiness.to_dict(),
        "geometry_consistency_checks": geometry_checks,
        "official_input_keys": list(official_inputs),
        "fabric_awning_control": shading_control.to_dict(),
        "fabric_awning_optical_diagnostic": optical_diagnostic.to_dict(),
        "fabric_awning_aps_diagnostic_binding": (
            aps_diagnostic_binding.to_dict()
        ),
        "runtime_qualification_evidence": qualification_evidence,
        "runtime_blockers": list(runtime_blockers),
        "mutation_supported": False,
        "next_action": (
            "Supply a source-traced native VE daily/weekly/yearly profile "
            "graph before runtime qualification."
            if profile_graph is None
            else (
                "Implement the guarded Test 2A model binding. Profile, shade "
                "threshold and direct-name fixed-closed optical storage are "
                "qualified, but dynamic shade semantics, complete 2E1 optics "
                "and APS equivalence remain blocked."
                if qualification_evidence[
                    "all_storage_boundaries_qualified"
                ]
                else "Run the guarded disposable-project profile, shade "
                "threshold and fixed-closed optical storage qualifications "
                "against this immutable generator input."
            )
        ),
        "claim_guardrail": generator_input["claim_guardrail"],
    }
    _write_json(audit_path, audit)
    return Test2ASourceBundleReceipt(
        status=audit["status"],
        generator_input_path=generator_input_path,
        generator_input_sha256=generator_input_sha,
        audit_path=audit_path,
        external_manifest_path=external_manifest_path,
        runtime_blockers=runtime_blockers,
    )
